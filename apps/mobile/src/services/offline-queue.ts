import AsyncStorage from "@react-native-async-storage/async-storage";
import * as FileSystem from "expo-file-system";
import type { OfflineQueueItemStatus } from "@ilm/contracts";

export interface OfflineQueueItem {
  id: string;
  classId: string;
  studentId: string;
  assignmentId?: string;
  persistedPhotoUri: string; // In stored items: permanent DocumentDirectory path. When passed as input to addToOfflineQueue: the source URI to copy from (may be a temp/cache URI — the function handles the copy internally).
  originalUri: string;
  capturedAt: string; // ISO 8601 UTC
  width: number;
  height: number;
  status: OfflineQueueItemStatus;
  attemptCount: number;
  failedAt?: string; // ISO 8601 UTC of last failure
}

const QUEUE_STORAGE_KEY = "offline_photo_queue";

function getOfflinePhotosDir(): string {
  return `${FileSystem.documentDirectory}offline-photos/`;
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

/**
 * Add a photo to the persistent offline queue.
 * Copies the photo from item.persistedPhotoUri (temp URI) to DocumentDirectory
 * and stores the queue item with the permanent path.
 */
export async function addToOfflineQueue(
  item: Omit<OfflineQueueItem, "id" | "status" | "attemptCount">,
): Promise<OfflineQueueItem> {
  const id = generateId();
  const offlinePhotosDir = getOfflinePhotosDir();
  const destPath = `${offlinePhotosDir}${id}.jpg`;

  // Ensure directory exists
  const dirInfo = await FileSystem.getInfoAsync(offlinePhotosDir);
  if (!dirInfo.exists) {
    await FileSystem.makeDirectoryAsync(offlinePhotosDir, { intermediates: true });
  }

  // Copy photo from the source URI (item.persistedPhotoUri, may be a temp/cache URI) to the
  // permanent DocumentDirectory path. The returned queue item's persistedPhotoUri is destPath.
  await FileSystem.copyAsync({ from: item.persistedPhotoUri, to: destPath });

  const queueItem: OfflineQueueItem = {
    ...item,
    id,
    persistedPhotoUri: destPath,
    status: "pending",
    attemptCount: 0,
  };

  const existing = await getOfflineQueue();
  existing.push(queueItem);
  await AsyncStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(existing));

  return queueItem;
}

export async function getOfflineQueue(): Promise<OfflineQueueItem[]> {
  const raw = await AsyncStorage.getItem(QUEUE_STORAGE_KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as OfflineQueueItem[];
  } catch {
    return [];
  }
}

export async function updateQueueItem(
  id: string,
  updates: Partial<OfflineQueueItem>,
): Promise<void> {
  const queue = await getOfflineQueue();
  const idx = queue.findIndex((item) => item.id === id);
  if (idx === -1) return;
  queue[idx] = { ...queue[idx], ...updates };
  await AsyncStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(queue));
}

export async function removeFromOfflineQueue(id: string): Promise<void> {
  const queue = await getOfflineQueue();
  const item = queue.find((q) => q.id === id);
  if (item) {
    try {
      await FileSystem.deleteAsync(item.persistedPhotoUri, { idempotent: true });
    } catch {
      // Ignore file deletion errors — storage cleanup is best-effort
    }
  }
  const updated = queue.filter((q) => q.id !== id);
  await AsyncStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(updated));
}

export async function clearOfflineQueue(): Promise<void> {
  const queue = await getOfflineQueue();
  for (const item of queue) {
    try {
      await FileSystem.deleteAsync(item.persistedPhotoUri, { idempotent: true });
    } catch {
      // Ignore
    }
  }
  await AsyncStorage.removeItem(QUEUE_STORAGE_KEY);
}

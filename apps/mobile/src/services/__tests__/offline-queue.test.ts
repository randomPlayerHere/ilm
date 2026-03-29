// Mock native modules before any imports
jest.mock("@react-native-async-storage/async-storage", () => ({
  __esModule: true,
  default: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
  },
}));

jest.mock("expo-file-system", () => ({
  documentDirectory: "file:///mock-documents/",
  getInfoAsync: jest.fn(),
  makeDirectoryAsync: jest.fn(),
  copyAsync: jest.fn(),
  deleteAsync: jest.fn(),
}));

jest.mock("@ilm/contracts", () => ({}));

import AsyncStorage from "@react-native-async-storage/async-storage";
import * as FileSystem from "expo-file-system";
import {
  addToOfflineQueue,
  getOfflineQueue,
  updateQueueItem,
  removeFromOfflineQueue,
  clearOfflineQueue,
  type OfflineQueueItem,
} from "../offline-queue";

const mockAsyncStorage = AsyncStorage as jest.Mocked<typeof AsyncStorage>;
const mockFileSystem = FileSystem as jest.Mocked<typeof FileSystem>;

const FAKE_ITEM_INPUT: Omit<OfflineQueueItem, "id" | "status" | "attemptCount"> = {
  classId: "cls_1",
  studentId: "stu_1",
  persistedPhotoUri: "file:///tmp/compressed.jpg",
  originalUri: "file:///tmp/original.jpg",
  capturedAt: "2026-03-28T10:00:00.000Z",
  width: 800,
  height: 600,
};

function makeStoredItem(overrides: Partial<OfflineQueueItem> = {}): OfflineQueueItem {
  return {
    id: "test-id-123",
    classId: "cls_1",
    studentId: "stu_1",
    persistedPhotoUri: "file:///mock-documents/offline-photos/test-id-123.jpg",
    originalUri: "file:///tmp/original.jpg",
    capturedAt: "2026-03-28T10:00:00.000Z",
    width: 800,
    height: 600,
    status: "pending",
    attemptCount: 0,
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  // Default: AsyncStorage starts empty
  mockAsyncStorage.getItem.mockResolvedValue(null);
  mockAsyncStorage.setItem.mockResolvedValue();
  mockAsyncStorage.removeItem.mockResolvedValue();
  // Default: directory does NOT exist → will be created
  (mockFileSystem.getInfoAsync as jest.Mock).mockResolvedValue({ exists: false });
  (mockFileSystem.makeDirectoryAsync as jest.Mock).mockResolvedValue(undefined);
  (mockFileSystem.copyAsync as jest.Mock).mockResolvedValue(undefined);
  (mockFileSystem.deleteAsync as jest.Mock).mockResolvedValue(undefined);
});

describe("addToOfflineQueue", () => {
  it("copies photo from temp URI to DocumentDirectory", async () => {
    await addToOfflineQueue(FAKE_ITEM_INPUT);
    expect(mockFileSystem.copyAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        from: "file:///tmp/compressed.jpg",
        to: expect.stringContaining("offline-photos/"),
      }),
    );
  });

  it("creates offline-photos directory when it does not exist", async () => {
    (mockFileSystem.getInfoAsync as jest.Mock).mockResolvedValue({ exists: false });
    await addToOfflineQueue(FAKE_ITEM_INPUT);
    expect(mockFileSystem.makeDirectoryAsync).toHaveBeenCalledWith(
      expect.stringContaining("offline-photos"),
      { intermediates: true },
    );
  });

  it("skips makeDirectoryAsync when directory already exists", async () => {
    (mockFileSystem.getInfoAsync as jest.Mock).mockResolvedValue({ exists: true });
    await addToOfflineQueue(FAKE_ITEM_INPUT);
    expect(mockFileSystem.makeDirectoryAsync).not.toHaveBeenCalled();
  });

  it("saves item to AsyncStorage with generated id and status=pending", async () => {
    const item = await addToOfflineQueue(FAKE_ITEM_INPUT);
    expect(item.id).toBeTruthy();
    expect(item.status).toBe("pending");
    expect(item.attemptCount).toBe(0);
    expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
      "offline_photo_queue",
      expect.stringContaining(item.id),
    );
  });

  it("persistedPhotoUri in returned item points to DocumentDirectory, not temp URI", async () => {
    const item = await addToOfflineQueue(FAKE_ITEM_INPUT);
    expect(item.persistedPhotoUri).toContain("offline-photos/");
    expect(item.persistedPhotoUri).not.toBe("file:///tmp/compressed.jpg");
  });

  it("appends to existing queue items", async () => {
    const existingItem = makeStoredItem();
    mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify([existingItem]));

    await addToOfflineQueue(FAKE_ITEM_INPUT);

    const setItemCall = mockAsyncStorage.setItem.mock.calls[0];
    const savedQueue: OfflineQueueItem[] = JSON.parse(setItemCall[1] as string);
    expect(savedQueue).toHaveLength(2);
    expect(savedQueue[0].id).toBe(existingItem.id);
  });
});

describe("getOfflineQueue", () => {
  it("returns empty array when storage is empty", async () => {
    mockAsyncStorage.getItem.mockResolvedValue(null);
    const result = await getOfflineQueue();
    expect(result).toEqual([]);
  });

  it("returns parsed items in storage order", async () => {
    const items = [makeStoredItem({ id: "a" }), makeStoredItem({ id: "b" })];
    mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(items));
    const result = await getOfflineQueue();
    expect(result).toHaveLength(2);
    expect(result[0].id).toBe("a");
    expect(result[1].id).toBe("b");
  });

  it("returns empty array on corrupt JSON", async () => {
    mockAsyncStorage.getItem.mockResolvedValue("not-valid-json{{{");
    const result = await getOfflineQueue();
    expect(result).toEqual([]);
  });
});

describe("updateQueueItem", () => {
  it("merges updates into the matching item", async () => {
    const item = makeStoredItem({ id: "item-1", status: "pending", attemptCount: 0 });
    mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify([item]));

    await updateQueueItem("item-1", { status: "failed", attemptCount: 1 });

    const setItemCall = mockAsyncStorage.setItem.mock.calls[0];
    const savedQueue: OfflineQueueItem[] = JSON.parse(setItemCall[1] as string);
    expect(savedQueue[0].status).toBe("failed");
    expect(savedQueue[0].attemptCount).toBe(1);
    // Other fields preserved
    expect(savedQueue[0].classId).toBe("cls_1");
  });

  it("does nothing when id is not found", async () => {
    const item = makeStoredItem({ id: "item-1" });
    mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify([item]));

    await updateQueueItem("nonexistent-id", { status: "failed" });

    // Implementation returns early without writing when id is not found
    expect(mockAsyncStorage.setItem).not.toHaveBeenCalled();
  });
});

describe("removeFromOfflineQueue", () => {
  it("removes the item from storage", async () => {
    const items = [makeStoredItem({ id: "item-1" }), makeStoredItem({ id: "item-2" })];
    mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(items));

    await removeFromOfflineQueue("item-1");

    const setItemCall = mockAsyncStorage.setItem.mock.calls[0];
    const savedQueue: OfflineQueueItem[] = JSON.parse(setItemCall[1] as string);
    expect(savedQueue).toHaveLength(1);
    expect(savedQueue[0].id).toBe("item-2");
  });

  it("deletes the persisted photo file for the removed item", async () => {
    const item = makeStoredItem({ id: "item-1", persistedPhotoUri: "file:///mock-documents/offline-photos/item-1.jpg" });
    mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify([item]));

    await removeFromOfflineQueue("item-1");

    expect(mockFileSystem.deleteAsync).toHaveBeenCalledWith(
      "file:///mock-documents/offline-photos/item-1.jpg",
      { idempotent: true },
    );
  });

  it("does not throw when item id is not found", async () => {
    mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify([]));
    await expect(removeFromOfflineQueue("nonexistent")).resolves.not.toThrow();
  });
});

describe("clearOfflineQueue", () => {
  it("removes all items from storage", async () => {
    const items = [makeStoredItem({ id: "a" }), makeStoredItem({ id: "b" })];
    mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(items));

    await clearOfflineQueue();

    expect(mockAsyncStorage.removeItem).toHaveBeenCalledWith("offline_photo_queue");
  });

  it("deletes all photo files", async () => {
    const items = [
      makeStoredItem({ id: "a", persistedPhotoUri: "file:///mock-documents/offline-photos/a.jpg" }),
      makeStoredItem({ id: "b", persistedPhotoUri: "file:///mock-documents/offline-photos/b.jpg" }),
    ];
    mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(items));

    await clearOfflineQueue();

    expect(mockFileSystem.deleteAsync).toHaveBeenCalledTimes(2);
    expect(mockFileSystem.deleteAsync).toHaveBeenCalledWith(
      "file:///mock-documents/offline-photos/a.jpg",
      { idempotent: true },
    );
    expect(mockFileSystem.deleteAsync).toHaveBeenCalledWith(
      "file:///mock-documents/offline-photos/b.jpg",
      { idempotent: true },
    );
  });

  it("works on an empty queue without errors", async () => {
    mockAsyncStorage.getItem.mockResolvedValue(null);
    await expect(clearOfflineQueue()).resolves.not.toThrow();
  });
});

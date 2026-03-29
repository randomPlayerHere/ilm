import { useCallback, useEffect, useRef, useState } from "react";
import NetInfo from "@react-native-community/netinfo";
import { getAuthData } from "../../../services/token-storage";
import {
  getOfflineQueue,
  updateQueueItem,
  removeFromOfflineQueue,
  type OfflineQueueItem,
} from "../../../services/offline-queue";
import {
  createAssignment,
  uploadArtifact,
  submitGradingJob,
} from "../../../services/grading-service";
import { emitQueueJobComplete } from "../../../services/queue-events";

export interface OfflineQueueProcessorState {
  pendingCount: number;
  processingItemId: string | null;
  queueItems: OfflineQueueItem[];
  retryItem: (id: string) => void;
}

export function useOfflineQueueProcessor(): OfflineQueueProcessorState {
  const [pendingCount, setPendingCount] = useState(0);
  const [processingItemId, setProcessingItemId] = useState<string | null>(null);
  const [queueItems, setQueueItems] = useState<OfflineQueueItem[]>([]);

  const isMountedRef = useRef(true);
  const isProcessingRef = useRef(false);

  const refreshQueueState = useCallback(async () => {
    const queue = await getOfflineQueue();
    if (!isMountedRef.current) return;
    setQueueItems(queue);
    setPendingCount(queue.filter((item) => item.status === "pending").length);
  }, []);

  const processQueue = useCallback(async () => {
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;

    try {
      const authData = await getAuthData();
      if (!authData || !isMountedRef.current) return;
      const token = authData.token;

      const queue = await getOfflineQueue();
      // Process items that are pending or failed with remaining attempts, sorted FIFO
      const processable = queue
        .filter(
          (item) =>
            item.status === "pending" ||
            (item.status === "failed" && item.attemptCount < 3),
        )
        .sort((a, b) => a.capturedAt.localeCompare(b.capturedAt));

      for (const item of processable) {
        if (!isMountedRef.current) break;

        await updateQueueItem(item.id, { status: "uploading" });
        if (isMountedRef.current) setProcessingItemId(item.id);
        await refreshQueueState();

        try {
          const title = `Assignment ${new Date(item.capturedAt).toLocaleDateString()}`;
          const assignment_id =
            item.assignmentId ??
            (await createAssignment(item.classId, title, token)).assignment_id;

          const { artifact_id } = await uploadArtifact(
            assignment_id,
            item.studentId,
            item.persistedPhotoUri,
            token,
          );

          const gradingJob = await submitGradingJob(assignment_id, artifact_id, token);

          await removeFromOfflineQueue(item.id);
          emitQueueJobComplete(assignment_id, gradingJob.job_id);
        } catch {
          const newAttemptCount = item.attemptCount + 1;
          await updateQueueItem(item.id, {
            status: "failed",
            attemptCount: newAttemptCount,
            failedAt: new Date().toISOString(),
          });

          // Exponential backoff before next item if still under retry limit
          if (newAttemptCount < 3) {
            const delay = Math.pow(2, newAttemptCount) * 1000;
            await new Promise((resolve) => setTimeout(resolve, delay));
          }
        }

        if (isMountedRef.current) setProcessingItemId(null);
      }
    } finally {
      isProcessingRef.current = false;
      if (isMountedRef.current) await refreshQueueState();
    }
  }, [refreshQueueState]);

  const retryItem = useCallback(
    async (id: string) => {
      await updateQueueItem(id, { status: "pending", attemptCount: 0 });
      await refreshQueueState();
      await processQueue();
    },
    [refreshQueueState, processQueue],
  );

  useEffect(() => {
    isMountedRef.current = true;

    // Load initial queue state
    refreshQueueState();

    // Subscribe to connectivity — process queue when connection is restored
    const unsubscribe = NetInfo.addEventListener((state) => {
      if (state.isConnected) {
        processQueue();
      }
    });

    return () => {
      isMountedRef.current = false;
      unsubscribe();
    };
  }, [refreshQueueState, processQueue]);

  return { pendingCount, processingItemId, queueItems, retryItem };
}

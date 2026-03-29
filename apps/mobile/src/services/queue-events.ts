type QueueJobCompleteListener = (assignmentId: string, jobId: string) => void;

const listeners = new Set<QueueJobCompleteListener>();

export function onQueueJobComplete(listener: QueueJobCompleteListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function emitQueueJobComplete(assignmentId: string, jobId: string): void {
  listeners.forEach((listener) => listener(assignmentId, jobId));
}

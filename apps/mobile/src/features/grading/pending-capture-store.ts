export interface PendingCapture {
  compressedUri: string;
  originalUri: string;
  capturedAt: string; // ISO 8601 UTC
  width: number;
  height: number;
}

let _pendingCapture: PendingCapture | null = null;

export function setPendingCapture(capture: PendingCapture): void {
  _pendingCapture = capture;
}

export function getPendingCapture(): PendingCapture | null {
  return _pendingCapture;
}

export function clearPendingCapture(): void {
  _pendingCapture = null;
}

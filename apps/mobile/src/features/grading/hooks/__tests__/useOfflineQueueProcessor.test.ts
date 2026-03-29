import type { NetInfoState } from "@react-native-community/netinfo";

// Capture NetInfo listener so tests can simulate connectivity changes
let capturedNetInfoListener: ((state: NetInfoState) => void) | null = null;
const mockNetInfoUnsubscribe = jest.fn();

jest.mock("@react-native-community/netinfo", () => ({
  __esModule: true,
  default: {
    addEventListener: jest.fn((listener: (state: NetInfoState) => void) => {
      capturedNetInfoListener = listener;
      return mockNetInfoUnsubscribe;
    }),
  },
}));

jest.mock("../../../../services/offline-queue", () => ({
  getOfflineQueue: jest.fn(),
  updateQueueItem: jest.fn(),
  removeFromOfflineQueue: jest.fn(),
}));

jest.mock("../../../../services/grading-service", () => ({
  createAssignment: jest.fn(),
  uploadArtifact: jest.fn(),
  submitGradingJob: jest.fn(),
}));

jest.mock("../../../../services/token-storage", () => ({
  getAuthData: jest.fn(),
}));

jest.mock("../../../../services/queue-events", () => ({
  emitQueueJobComplete: jest.fn(),
}));

import { act, renderHook } from "@testing-library/react-native";
import { useOfflineQueueProcessor } from "../useOfflineQueueProcessor";
import * as offlineQueue from "../../../../services/offline-queue";
import * as gradingService from "../../../../services/grading-service";
import * as tokenStorage from "../../../../services/token-storage";
import * as queueEvents from "../../../../services/queue-events";
import type { OfflineQueueItem } from "../../../../services/offline-queue";

const mockGetOfflineQueue = offlineQueue.getOfflineQueue as jest.MockedFunction<typeof offlineQueue.getOfflineQueue>;
const mockUpdateQueueItem = offlineQueue.updateQueueItem as jest.MockedFunction<typeof offlineQueue.updateQueueItem>;
const mockRemoveFromOfflineQueue = offlineQueue.removeFromOfflineQueue as jest.MockedFunction<typeof offlineQueue.removeFromOfflineQueue>;
const mockCreateAssignment = gradingService.createAssignment as jest.MockedFunction<typeof gradingService.createAssignment>;
const mockUploadArtifact = gradingService.uploadArtifact as jest.MockedFunction<typeof gradingService.uploadArtifact>;
const mockSubmitGradingJob = gradingService.submitGradingJob as jest.MockedFunction<typeof gradingService.submitGradingJob>;
const mockGetAuthData = tokenStorage.getAuthData as jest.MockedFunction<typeof tokenStorage.getAuthData>;
const mockEmitQueueJobComplete = queueEvents.emitQueueJobComplete as jest.MockedFunction<typeof queueEvents.emitQueueJobComplete>;

const FAKE_AUTH = { token: "fake-token", role: "teacher", homePath: "/", email: "t@t.com" };

function makeQueueItem(overrides: Partial<OfflineQueueItem> = {}): OfflineQueueItem {
  return {
    id: "item-1",
    classId: "cls_1",
    studentId: "stu_1",
    persistedPhotoUri: "file:///docs/offline-photos/item-1.jpg",
    originalUri: "file:///tmp/orig.jpg",
    capturedAt: "2026-03-28T10:00:00.000Z",
    width: 800,
    height: 600,
    status: "pending",
    attemptCount: 0,
    ...overrides,
  };
}

function makeNetInfoState(isConnected: boolean): NetInfoState {
  return { isConnected, isInternetReachable: isConnected, type: "wifi", details: null } as unknown as NetInfoState;
}

beforeEach(() => {
  jest.clearAllMocks();
  capturedNetInfoListener = null;
  mockGetAuthData.mockResolvedValue(FAKE_AUTH);
  mockGetOfflineQueue.mockResolvedValue([]);
  mockUpdateQueueItem.mockResolvedValue();
  mockRemoveFromOfflineQueue.mockResolvedValue();
  mockCreateAssignment.mockResolvedValue({ assignment_id: "asgn_1" });
  mockUploadArtifact.mockResolvedValue({ artifact_id: "art_1" });
  mockSubmitGradingJob.mockResolvedValue({
    job_id: "job_1", artifact_id: "art_1", assignment_id: "asgn_1",
    status: "pending", attempt_count: 0, submitted_at: "", completed_at: null,
    failure_code: null, failure_reason: null, rubric_criteria: [],
  });
});

describe("useOfflineQueueProcessor", () => {
  it("exposes pendingCount=0 and empty queueItems on mount with empty queue", async () => {
    const { result } = renderHook(() => useOfflineQueueProcessor());
    await act(async () => { await Promise.resolve(); });
    expect(result.current.pendingCount).toBe(0);
    expect(result.current.queueItems).toEqual([]);
  });

  it("reflects pending items from queue on mount", async () => {
    const items = [makeQueueItem({ status: "pending" }), makeQueueItem({ id: "item-2", status: "pending" })];
    mockGetOfflineQueue.mockResolvedValue(items);

    const { result } = renderHook(() => useOfflineQueueProcessor());
    await act(async () => { await Promise.resolve(); });

    expect(result.current.pendingCount).toBe(2);
    expect(result.current.queueItems).toHaveLength(2);
  });

  it("does not process queue when connectivity fires as disconnected", async () => {
    mockGetOfflineQueue.mockResolvedValue([makeQueueItem()]);
    renderHook(() => useOfflineQueueProcessor());

    await act(async () => {
      capturedNetInfoListener?.(makeNetInfoState(false));
      await Promise.resolve();
    });

    expect(mockCreateAssignment).not.toHaveBeenCalled();
    expect(mockUploadArtifact).not.toHaveBeenCalled();
  });

  it("processes pending items in FIFO order when connectivity is restored", async () => {
    const items = [
      makeQueueItem({ id: "item-1", capturedAt: "2026-03-28T10:00:00.000Z", status: "pending" }),
      makeQueueItem({ id: "item-2", capturedAt: "2026-03-28T10:01:00.000Z", status: "pending" }),
    ];
    mockGetOfflineQueue.mockResolvedValue(items);

    renderHook(() => useOfflineQueueProcessor());

    await act(async () => {
      capturedNetInfoListener?.(makeNetInfoState(true));
      // Flush all async ops
      for (let i = 0; i < 10; i++) await Promise.resolve();
    });

    const updateCalls = mockUpdateQueueItem.mock.calls;
    const uploadingUpdates = updateCalls.filter((c) => (c[1] as Partial<OfflineQueueItem>).status === "uploading");
    expect(uploadingUpdates[0][0]).toBe("item-1"); // item-1 processed first (earlier capturedAt)
    expect(uploadingUpdates[1][0]).toBe("item-2");
  });

  it("emits queueJobComplete after successful upload and job submission", async () => {
    mockGetOfflineQueue.mockResolvedValue([makeQueueItem()]);

    renderHook(() => useOfflineQueueProcessor());

    await act(async () => {
      capturedNetInfoListener?.(makeNetInfoState(true));
      for (let i = 0; i < 10; i++) await Promise.resolve();
    });

    expect(mockEmitQueueJobComplete).toHaveBeenCalledWith("asgn_1", "job_1");
  });

  it("removes item from queue after successful upload", async () => {
    mockGetOfflineQueue.mockResolvedValue([makeQueueItem({ id: "item-1" })]);

    renderHook(() => useOfflineQueueProcessor());

    await act(async () => {
      capturedNetInfoListener?.(makeNetInfoState(true));
      for (let i = 0; i < 10; i++) await Promise.resolve();
    });

    expect(mockRemoveFromOfflineQueue).toHaveBeenCalledWith("item-1");
  });

  it("increments attemptCount and sets status=failed on upload error", async () => {
    mockGetOfflineQueue.mockResolvedValue([makeQueueItem({ id: "item-1", attemptCount: 0 })]);
    mockUploadArtifact.mockRejectedValue(new Error("Network error"));

    renderHook(() => useOfflineQueueProcessor());

    await act(async () => {
      capturedNetInfoListener?.(makeNetInfoState(true));
      for (let i = 0; i < 15; i++) await Promise.resolve();
    });

    const failedUpdate = mockUpdateQueueItem.mock.calls.find(
      (c) => (c[1] as Partial<OfflineQueueItem>).status === "failed",
    );
    expect(failedUpdate).toBeDefined();
    expect((failedUpdate![1] as Partial<OfflineQueueItem>).attemptCount).toBe(1);
  });

  it("does not process item with attemptCount >= 3 (permanently failed)", async () => {
    mockGetOfflineQueue.mockResolvedValue([makeQueueItem({ status: "failed", attemptCount: 3 })]);

    renderHook(() => useOfflineQueueProcessor());

    await act(async () => {
      capturedNetInfoListener?.(makeNetInfoState(true));
      for (let i = 0; i < 10; i++) await Promise.resolve();
    });

    expect(mockUploadArtifact).not.toHaveBeenCalled();
  });

  it("unsubscribes from NetInfo on unmount", () => {
    const { unmount } = renderHook(() => useOfflineQueueProcessor());
    unmount();
    expect(mockNetInfoUnsubscribe).toHaveBeenCalled();
  });

  it("pendingCount reflects only items with status=pending", async () => {
    const items = [
      makeQueueItem({ id: "a", status: "pending" }),
      makeQueueItem({ id: "b", status: "failed", attemptCount: 3 }),
      makeQueueItem({ id: "c", status: "uploading" }),
    ];
    mockGetOfflineQueue.mockResolvedValue(items);

    const { result } = renderHook(() => useOfflineQueueProcessor());
    await act(async () => { await Promise.resolve(); });

    expect(result.current.pendingCount).toBe(1);
  });

  it("retryItem resets item to pending and triggers processing", async () => {
    const failedItem = makeQueueItem({ id: "item-1", status: "failed", attemptCount: 3 });
    mockGetOfflineQueue.mockResolvedValue([failedItem]);

    const { result } = renderHook(() => useOfflineQueueProcessor());
    await act(async () => { await Promise.resolve(); });

    // Re-mock the queue to return the reset item after updateQueueItem is called
    mockGetOfflineQueue.mockResolvedValue([makeQueueItem({ id: "item-1", status: "pending", attemptCount: 0 })]);

    await act(async () => {
      result.current.retryItem("item-1");
      for (let i = 0; i < 10; i++) await Promise.resolve();
    });

    expect(mockUpdateQueueItem).toHaveBeenCalledWith("item-1", { status: "pending", attemptCount: 0 });
  });
});

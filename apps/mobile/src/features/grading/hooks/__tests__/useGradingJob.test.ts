import { act, renderHook } from "@testing-library/react-native";
import { useGradingJob } from "../useGradingJob";

// Mock grading-service module functions
jest.mock("../../../../services/grading-service", () => ({
  createAssignment: jest.fn(),
  uploadArtifact: jest.fn(), // kept for offline queue processor (not used in online path since 5.9)
  getPresignedUploadUrl: jest.fn(),
  uploadToPresignedUrl: jest.fn(),
  registerArtifact: jest.fn(),
  submitGradingJob: jest.fn(),
  getGradingJob: jest.fn(),
}));

// Mock pending-capture-store — pre-seed a fake PendingCapture
jest.mock("../../pending-capture-store", () => ({
  getPendingCapture: jest.fn(),
  clearPendingCapture: jest.fn(),
}));

// Mock token-storage — return fake auth data
jest.mock("../../../../services/token-storage", () => ({
  getAuthData: jest.fn(),
}));

// Mock offline-queue — capture calls
jest.mock("../../../../services/offline-queue", () => ({
  addToOfflineQueue: jest.fn(),
}));

// Mock NetInfo — default online, tests override as needed
jest.mock("@react-native-community/netinfo", () => ({
  __esModule: true,
  default: {
    fetch: jest.fn(),
    addEventListener: jest.fn(() => jest.fn()),
  },
}));

import * as gradingService from "../../../../services/grading-service";
import * as pendingCaptureStore from "../../pending-capture-store";
import * as tokenStorage from "../../../../services/token-storage";
import * as offlineQueueModule from "../../../../services/offline-queue";
import NetInfo from "@react-native-community/netinfo";

const mockCreateAssignment = gradingService.createAssignment as jest.MockedFunction<typeof gradingService.createAssignment>;
const mockGetPresignedUploadUrl = gradingService.getPresignedUploadUrl as jest.MockedFunction<typeof gradingService.getPresignedUploadUrl>;
const mockUploadToPresignedUrl = gradingService.uploadToPresignedUrl as jest.MockedFunction<typeof gradingService.uploadToPresignedUrl>;
const mockRegisterArtifact = gradingService.registerArtifact as jest.MockedFunction<typeof gradingService.registerArtifact>;
const mockUploadArtifact = gradingService.uploadArtifact as jest.MockedFunction<typeof gradingService.uploadArtifact>;
const mockSubmitGradingJob = gradingService.submitGradingJob as jest.MockedFunction<typeof gradingService.submitGradingJob>;
const mockGetGradingJob = gradingService.getGradingJob as jest.MockedFunction<typeof gradingService.getGradingJob>;
const mockGetPendingCapture = pendingCaptureStore.getPendingCapture as jest.MockedFunction<typeof pendingCaptureStore.getPendingCapture>;
const mockClearPendingCapture = pendingCaptureStore.clearPendingCapture as jest.MockedFunction<typeof pendingCaptureStore.clearPendingCapture>;
const mockGetAuthData = tokenStorage.getAuthData as jest.MockedFunction<typeof tokenStorage.getAuthData>;
const mockAddToOfflineQueue = offlineQueueModule.addToOfflineQueue as jest.MockedFunction<typeof offlineQueueModule.addToOfflineQueue>;
const mockNetInfoFetch = NetInfo.fetch as jest.MockedFunction<typeof NetInfo.fetch>;

const FAKE_AUTH = { token: "fake-token", role: "teacher", homePath: "/", email: "test@test.com" };
const FAKE_CAPTURE = { compressedUri: "file://test.jpg", originalUri: "file://orig.jpg", capturedAt: "2026-03-26T00:00:00Z", width: 800, height: 600 };
const FAKE_JOB_RESPONSE = { job_id: "job_1", artifact_id: "art_1", assignment_id: "asgn_1", status: "pending" as const, attempt_count: 0, submitted_at: "", completed_at: null, failure_code: null as null, failure_reason: null as null, rubric_criteria: [] as { criterion: string; description: string | null }[] };
const FAKE_COMPLETED_JOB = {
  ...FAKE_JOB_RESPONSE,
  status: "completed" as const,
  completed_at: "2026-03-26T00:00:01Z",
  result: {
    proposed_score: "85/100",
    rubric_mapping: {},
    draft_feedback: "Good work",
    generated_at: "2026-03-26T00:00:01Z",
    confidence_level: "high" as const,
    confidence_score: 0.95,
    confidence_reason: null,
    practice_recommendations: [],
  },
  is_approved: false,
};
const FAKE_FAILED_JOB = { ...FAKE_JOB_RESPONSE, status: "failed" as const, completed_at: "2026-03-26T00:00:01Z", result: null, is_approved: false, failure_code: 'MODEL_ERROR' as const, failure_reason: 'AI grading did not complete — please try again.' };

const ONLINE_NET_STATE = { isConnected: true, isInternetReachable: true, type: "wifi", details: null };
const OFFLINE_NET_STATE = { isConnected: false, isInternetReachable: false, type: "none", details: null };

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
  mockGetAuthData.mockResolvedValue(FAKE_AUTH);
  mockGetPendingCapture.mockReturnValue(FAKE_CAPTURE);
  mockCreateAssignment.mockResolvedValue({ assignment_id: "asgn_1" });
  // Story 5.9: 3-step upload flow in online path
  mockGetPresignedUploadUrl.mockResolvedValue({ url: "https://s3.example.com/presigned", key: "orgs/org/cls/stu/asgn/uuid.jpg" });
  mockUploadToPresignedUrl.mockResolvedValue(undefined);
  mockRegisterArtifact.mockResolvedValue({ artifact_id: "art_1" });
  mockSubmitGradingJob.mockResolvedValue(FAKE_JOB_RESPONSE);
  // Default: online
  mockNetInfoFetch.mockResolvedValue(ONLINE_NET_STATE as any);
  mockAddToOfflineQueue.mockResolvedValue({
    id: "queue-item-1",
    classId: "cls_1",
    studentId: "stu_1",
    persistedPhotoUri: "file:///docs/offline-photos/queue-item-1.jpg",
    originalUri: "file://orig.jpg",
    capturedAt: "2026-03-26T00:00:00Z",
    width: 800,
    height: 600,
    status: "pending",
    attemptCount: 0,
  });
});

afterEach(() => {
  jest.useRealTimers();
});

// Suppress React's "not wrapped in act()" warnings for this suite.
const originalConsoleError = console.error.bind(console);
beforeAll(() => {
  jest.spyOn(console, "error").mockImplementation((...args: unknown[]) => {
    if (typeof args[0] === "string" && args[0].includes("not wrapped in act")) return;
    originalConsoleError(...args);
  });
});
afterAll(() => (console.error as jest.MockedFunction<typeof console.error>).mockRestore());

// Flush all async state updates from useGradingJob's run() function (online path).
// run() chains 7 sequential awaits (Story 5.9 pre-signed URL flow):
//   getAuthData → NetInfo.fetch → createAssignment →
//   getPresignedUploadUrl → uploadToPresignedUrl → registerArtifact → submitGradingJob
const flushRun = async () => {
  await act(async () => { await Promise.resolve(); }); // tick 1: getAuthData
  await act(async () => { await Promise.resolve(); }); // tick 2: NetInfo.fetch → setState("uploading")
  await act(async () => { await Promise.resolve(); }); // tick 3: createAssignment
  await act(async () => { await Promise.resolve(); }); // tick 4: getPresignedUploadUrl
  await act(async () => { await Promise.resolve(); }); // tick 5: uploadToPresignedUrl
  await act(async () => { await Promise.resolve(); }); // tick 6: registerArtifact
  await act(async () => { await Promise.resolve(); }); // tick 7: submitGradingJob → setState("processing")
  await act(async () => { await Promise.resolve(); }); // tick 8: safety margin
};

// Flush for offline path: getAuthData → NetInfo.fetch → addToOfflineQueue
const flushOfflineRun = async () => {
  await act(async () => { await Promise.resolve(); }); // tick 1: getAuthData
  await act(async () => { await Promise.resolve(); }); // tick 2: NetInfo.fetch (offline)
  await act(async () => { await Promise.resolve(); }); // tick 3: addToOfflineQueue → setState("queued-offline")
  await act(async () => { await Promise.resolve(); }); // tick 4: safety margin
};

describe("useGradingJob — online path (no regression)", () => {
  it("photoUri in returned state equals pendingCapture.compressedUri", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    expect(result.current.photoUri).toBeNull();
    await flushRun();
    expect(result.current.photoUri).toBe("file://test.jpg");
  });

  it("transitions uploading → processing → completed", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));

    await flushRun();
    expect(result.current.status).toBe("processing");

    await act(async () => { jest.advanceTimersByTime(2000); });
    expect(result.current.status).toBe("completed");
    expect(result.current.result).toEqual(FAKE_COMPLETED_JOB);
  });

  it("sets failed state with error message when job fails", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_FAILED_JOB);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushRun();
    await act(async () => { jest.advanceTimersByTime(2000); });
    expect(result.current.status).toBe("failed");
    expect(result.current.error).toBeTruthy();
  });

  it("clears pending capture after successful upload and job submission", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushRun();
    expect(mockClearPendingCapture).toHaveBeenCalledTimes(1);
  });

  it("sets failed with session-expired message when getAuthData returns null", async () => {
    mockGetAuthData.mockResolvedValue(null);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushRun();
    expect(result.current.status).toBe("failed");
    expect(result.current.error).toBe("Session expired — please sign in again");
  });

  it("calls clearTimeout on unmount", async () => {
    const clearTimeoutSpy = jest.spyOn(global, "clearTimeout");
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    const { unmount } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushRun();
    unmount();
    expect(clearTimeoutSpy).toHaveBeenCalled();
    clearTimeoutSpy.mockRestore();
  });

  it("sets failed with timed-out message after 30 poll attempts", async () => {
    mockGetGradingJob.mockResolvedValue({
      ...FAKE_JOB_RESPONSE,
      status: "pending" as const,
      result: null,
      is_approved: false,
    });
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushRun();
    for (let i = 0; i <= 30; i++) {
      await act(async () => { jest.advanceTimersByTime(2000); });
    }
    expect(result.current.status).toBe("failed");
    expect(result.current.error).toBe("Request timed out");
  });

  it("retrying=false in initial state", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    expect(result.current.retrying).toBe(false);
  });

  it("retrying=true when poll response has status='processing' and attempt_count=2", async () => {
    const processingJob = { ...FAKE_JOB_RESPONSE, status: "processing" as const, result: null, is_approved: false, attempt_count: 2 };
    mockGetGradingJob.mockResolvedValueOnce(processingJob).mockResolvedValue(FAKE_COMPLETED_JOB);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushRun();
    await act(async () => { jest.advanceTimersByTime(2000); });
    expect(result.current.retrying).toBe(true);
  });

  it("retrying=false when poll response has status='processing' and attempt_count=1", async () => {
    const processingJob = { ...FAKE_JOB_RESPONSE, status: "processing" as const, result: null, is_approved: false, attempt_count: 1 };
    mockGetGradingJob.mockResolvedValueOnce(processingJob).mockResolvedValue(FAKE_COMPLETED_JOB);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushRun();
    await act(async () => { jest.advanceTimersByTime(2000); });
    expect(result.current.retrying).toBe(false);
  });

  it("when assignmentId is provided, createAssignment is NOT called", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    renderHook(() => useGradingJob("cls_1", "stu_1", "existing_asgn"));
    await flushRun();
    expect(mockCreateAssignment).not.toHaveBeenCalled();
    // Story 5.9: online path uses getPresignedUploadUrl → uploadToPresignedUrl → registerArtifact
    expect(mockGetPresignedUploadUrl).toHaveBeenCalledWith(
      "cls_1", "stu_1", "existing_asgn", "assignment.jpg", "fake-token",
    );
  });

  it("queueItemId is null in online happy path", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushRun();
    expect(result.current.queueItemId).toBeNull();
  });

  it("calls getPresignedUploadUrl → uploadToPresignedUrl → registerArtifact in order", async () => {
    const callOrder: string[] = [];
    mockGetPresignedUploadUrl.mockImplementation(async () => {
      callOrder.push("getPresignedUploadUrl");
      return { url: "https://s3.example.com/presigned", key: "orgs/org/cls/stu/asgn/uuid.jpg" };
    });
    mockUploadToPresignedUrl.mockImplementation(async () => { callOrder.push("uploadToPresignedUrl"); });
    mockRegisterArtifact.mockImplementation(async () => {
      callOrder.push("registerArtifact");
      return { artifact_id: "art_1" };
    });
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushRun();
    expect(callOrder).toEqual(["getPresignedUploadUrl", "uploadToPresignedUrl", "registerArtifact"]);
  });

  it("uploadArtifact is NOT called in online path (replaced by pre-signed URL flow)", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushRun();
    expect(mockUploadArtifact).not.toHaveBeenCalled();
  });
});

describe("useGradingJob — offline path", () => {
  beforeEach(() => {
    mockNetInfoFetch.mockResolvedValue(OFFLINE_NET_STATE as any);
  });

  it("sets status=queued-offline when device is offline", async () => {
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushOfflineRun();
    expect(result.current.status).toBe("queued-offline");
  });

  it("calls addToOfflineQueue with pending capture data when offline", async () => {
    renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushOfflineRun();
    expect(mockAddToOfflineQueue).toHaveBeenCalledWith(
      expect.objectContaining({
        classId: "cls_1",
        studentId: "stu_1",
        persistedPhotoUri: "file://test.jpg",
        originalUri: "file://orig.jpg",
        capturedAt: "2026-03-26T00:00:00Z",
        width: 800,
        height: 600,
      }),
    );
  });

  it("calls clearPendingCapture after queuing (photo persisted)", async () => {
    renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushOfflineRun();
    expect(mockClearPendingCapture).toHaveBeenCalledTimes(1);
  });

  it("stores queueItemId from addToOfflineQueue result", async () => {
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushOfflineRun();
    expect(result.current.queueItemId).toBe("queue-item-1");
  });

  it("does NOT call pre-signed URL upload or submit when offline", async () => {
    renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushOfflineRun();
    expect(mockGetPresignedUploadUrl).not.toHaveBeenCalled();
    expect(mockUploadToPresignedUrl).not.toHaveBeenCalled();
    expect(mockRegisterArtifact).not.toHaveBeenCalled();
    expect(mockSubmitGradingJob).not.toHaveBeenCalled();
  });

  it("photoUri is set even when queued offline", async () => {
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushOfflineRun();
    expect(result.current.photoUri).toBe("file://test.jpg");
  });

  it("sets status=failed if addToOfflineQueue throws", async () => {
    mockAddToOfflineQueue.mockRejectedValue(new Error("Storage error"));
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await flushOfflineRun();
    expect(result.current.status).toBe("failed");
    expect(result.current.error).toContain("Storage error");
  });

  it("passes assignmentId to addToOfflineQueue when provided", async () => {
    renderHook(() => useGradingJob("cls_1", "stu_1", "existing_asgn"));
    await flushOfflineRun();
    expect(mockAddToOfflineQueue).toHaveBeenCalledWith(
      expect.objectContaining({ assignmentId: "existing_asgn" }),
    );
  });
});

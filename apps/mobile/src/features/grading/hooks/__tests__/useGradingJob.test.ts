import { act, renderHook } from "@testing-library/react-native";
import { useGradingJob } from "../useGradingJob";

// Mock grading-service module functions
jest.mock("../../../../services/grading-service", () => ({
  createAssignment: jest.fn(),
  uploadArtifact: jest.fn(),
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

import * as gradingService from "../../../../services/grading-service";
import * as pendingCaptureStore from "../../pending-capture-store";
import * as tokenStorage from "../../../../services/token-storage";

const mockCreateAssignment = gradingService.createAssignment as jest.MockedFunction<typeof gradingService.createAssignment>;
const mockUploadArtifact = gradingService.uploadArtifact as jest.MockedFunction<typeof gradingService.uploadArtifact>;
const mockSubmitGradingJob = gradingService.submitGradingJob as jest.MockedFunction<typeof gradingService.submitGradingJob>;
const mockGetGradingJob = gradingService.getGradingJob as jest.MockedFunction<typeof gradingService.getGradingJob>;
const mockGetPendingCapture = pendingCaptureStore.getPendingCapture as jest.MockedFunction<typeof pendingCaptureStore.getPendingCapture>;
const mockClearPendingCapture = pendingCaptureStore.clearPendingCapture as jest.MockedFunction<typeof pendingCaptureStore.clearPendingCapture>;
const mockGetAuthData = tokenStorage.getAuthData as jest.MockedFunction<typeof tokenStorage.getAuthData>;

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

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
  mockGetAuthData.mockResolvedValue(FAKE_AUTH);
  mockGetPendingCapture.mockReturnValue(FAKE_CAPTURE);
  mockCreateAssignment.mockResolvedValue({ assignment_id: "asgn_1" });
  mockUploadArtifact.mockResolvedValue({ artifact_id: "art_1" });
  mockSubmitGradingJob.mockResolvedValue(FAKE_JOB_RESPONSE);
});

afterEach(() => {
  jest.useRealTimers();
});

describe("useGradingJob", () => {
  it("photoUri in returned state equals pendingCapture.compressedUri", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    // Initial state — photoUri is null before async flow runs
    expect(result.current.photoUri).toBeNull();
    // After auth + capture load + upload
    await act(async () => {});
    expect(result.current.photoUri).toBe("file://test.jpg");
  });

  it("transitions uploading → processing → completed", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));

    // After upload + job submission completes, status is 'processing'
    await act(async () => {});
    expect(result.current.status).toBe("processing");

    // Advance timer to trigger first poll
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });
    expect(result.current.status).toBe("completed");
    expect(result.current.result).toEqual(FAKE_COMPLETED_JOB);
  });

  it("sets failed state with error message when job fails", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_FAILED_JOB);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));

    await act(async () => {});
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    expect(result.current.status).toBe("failed");
    expect(result.current.error).toBeTruthy();
  });

  it("clears pending capture after successful upload and job submission", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    renderHook(() => useGradingJob("cls_1", "stu_1"));
    await act(async () => {});
    expect(mockClearPendingCapture).toHaveBeenCalledTimes(1);
  });

  it("sets failed with session-expired message when getAuthData returns null", async () => {
    mockGetAuthData.mockResolvedValue(null);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await act(async () => {});
    expect(result.current.status).toBe("failed");
    expect(result.current.error).toBe("Session expired — please sign in again");
  });

  it("calls clearTimeout on unmount", async () => {
    const clearTimeoutSpy = jest.spyOn(global, "clearTimeout");
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    const { unmount } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await act(async () => {});
    unmount();
    expect(clearTimeoutSpy).toHaveBeenCalled();
    clearTimeoutSpy.mockRestore();
  });

  it("sets failed with timed-out message after 30 poll attempts", async () => {
    // Always return pending status so polling never stops
    mockGetGradingJob.mockResolvedValue({
      ...FAKE_JOB_RESPONSE,
      status: "pending" as const,
      result: null,
      is_approved: false,
    });
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await act(async () => {});

    // Advance through 31 poll intervals (> 30 max attempts)
    for (let i = 0; i <= 30; i++) {
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });
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
    await act(async () => {});
    await act(async () => { jest.advanceTimersByTime(2000); });
    expect(result.current.retrying).toBe(true);
  });

  it("retrying=false (stays false) when poll response has status='processing' and attempt_count=1", async () => {
    const processingJob = { ...FAKE_JOB_RESPONSE, status: "processing" as const, result: null, is_approved: false, attempt_count: 1 };
    mockGetGradingJob.mockResolvedValueOnce(processingJob).mockResolvedValue(FAKE_COMPLETED_JOB);
    const { result } = renderHook(() => useGradingJob("cls_1", "stu_1"));
    await act(async () => {});
    await act(async () => { jest.advanceTimersByTime(2000); });
    expect(result.current.retrying).toBe(false);
  });

  it("when assignmentId is provided, createAssignment is NOT called and the provided value is used", async () => {
    mockGetGradingJob.mockResolvedValue(FAKE_COMPLETED_JOB);
    renderHook(() => useGradingJob("cls_1", "stu_1", "existing_asgn"));
    await act(async () => {});
    expect(mockCreateAssignment).not.toHaveBeenCalled();
    expect(mockUploadArtifact).toHaveBeenCalledWith("existing_asgn", "stu_1", expect.any(String), expect.any(String));
  });
});

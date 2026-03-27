import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react-native";
import type { GradingJobWithResultResponse } from "@ilm/contracts";
import GradingScreen from "../grading";

const mockBack = jest.fn();
const mockReplace = jest.fn();
let mockParams: {
  classId?: string;
  studentId?: string;
  batchIndex?: string;
  batchTotal?: string;
  assignmentId?: string;
} = {};

const mockUseGradingJob = jest.fn();
const mockUseGradingReview = jest.fn();
const mockUseGradeApproval = jest.fn();
const mockGradingCard = jest.fn((_: unknown) => null);

jest.mock("expo-router", () => ({
  useRouter: () => ({ back: mockBack, replace: mockReplace }),
  useLocalSearchParams: () => mockParams,
}));

jest.mock("expo-haptics", () => ({
  notificationAsync: jest.fn(),
  NotificationFeedbackType: { Success: "success" },
}));

jest.mock("../../../src/features/grading/hooks/useGradingJob", () => ({
  useGradingJob: (...args: unknown[]) => mockUseGradingJob(...args),
}));

jest.mock("../../../src/features/grading/hooks/useGradingReview", () => ({
  useGradingReview: (...args: unknown[]) => mockUseGradingReview(...args),
}));

jest.mock("../../../src/features/grading/hooks/useGradeApproval", () => ({
  useGradeApproval: (...args: unknown[]) => mockUseGradeApproval(...args),
}));

jest.mock("../../../src/features/grading/components/GradingCard", () => ({
  GradingCard: (props: unknown) => {
    mockGradingCard(props);
    return null;
  },
}));

const mockUseManualGrading = jest.fn();
jest.mock("../../../src/features/grading/hooks/useManualGrading", () => ({
  useManualGrading: (...args: unknown[]) => mockUseManualGrading(...args),
}));

const makeApprovalControls = (overrides = {}) => ({
  approve: jest.fn(),
  isApproving: false,
  isApproved: false,
  approvalError: null,
  ...overrides,
});

const COMPLETED_RESULT: GradingJobWithResultResponse = {
  job_id: "job_1",
  artifact_id: "artifact_1",
  assignment_id: "assignment_1",
  status: "completed",
  attempt_count: 1,
  submitted_at: "2026-03-27T00:00:00Z",
  completed_at: "2026-03-27T00:00:01Z",
  is_approved: false,
  failure_code: null,
  failure_reason: null,
  rubric_criteria: [],
  result: {
    proposed_score: "85/100",
    draft_feedback: "Good work.",
    confidence_level: "high",
    confidence_score: 0.9,
    confidence_reason: null,
    rubric_mapping: { clarity: "good" },
    generated_at: "2026-03-27T00:00:01Z",
    practice_recommendations: [],
  },
};

const FAILED_RESULT: GradingJobWithResultResponse = {
  ...COMPLETED_RESULT,
  job_id: "job_failed",
  status: "failed",
  result: null,
  failure_code: "MODEL_ERROR",
  failure_reason: "AI grading did not complete",
  rubric_criteria: [],
};

describe("grading screen", () => {
  beforeEach(() => {
    mockParams = {};
    mockBack.mockReset();
    mockReplace.mockReset();
    mockUseGradingJob.mockReset();
    mockUseGradingReview.mockReset();
    mockUseGradeApproval.mockReset();
    mockUseGradeApproval.mockReturnValue(null);
    mockGradingCard.mockReset();
    mockUseManualGrading.mockReset();
    mockUseManualGrading.mockReturnValue(null);
  });

  it("uses missing-param failure state and does not enable review controls", () => {
    mockUseGradingJob.mockReturnValue({
      status: "idle",
      result: null,
      error: null,
      photoUri: null,
    });
    mockUseGradingReview.mockReturnValue(null);

    render(<GradingScreen />);

    expect(mockUseGradingJob).toHaveBeenCalledWith("", "", undefined);
    expect(mockUseGradingReview).toHaveBeenCalledWith(null);

    expect(mockGradingCard).toHaveBeenCalled();
    const gradingCardProps = mockGradingCard.mock.calls[mockGradingCard.mock.calls.length - 1]?.[0] as unknown as {
      status: string;
      error: string;
      reviewControls: unknown;
    };

    expect(gradingCardProps.status).toBe("failed");
    expect(gradingCardProps.error).toContain("Missing assignment context");
    expect(gradingCardProps.reviewControls).toBeNull();
  });

  it("enables review controls only when grading is completed with result", () => {
    const completedResult: GradingJobWithResultResponse = {
      job_id: "job_1",
      artifact_id: "artifact_1",
      assignment_id: "assignment_1",
      status: "completed",
      attempt_count: 1,
      submitted_at: "2026-03-27T00:00:00Z",
      completed_at: "2026-03-27T00:00:01Z",
      is_approved: false,
      failure_code: null,
      failure_reason: null,
      rubric_criteria: [],
      result: {
        proposed_score: "85/100",
        draft_feedback: "Good work.",
        confidence_level: "high",
        confidence_score: 0.9,
        confidence_reason: null,
        rubric_mapping: {
          clarity: "good",
        },
        generated_at: "2026-03-27T00:00:01Z",
        practice_recommendations: [],
      },
    };

    const reviewControls = {
      scoreValue: 85,
      scoreInputText: "85",
      displayScore: "85/100",
      feedbackValue: "Good work.",
      increment: jest.fn(),
      decrement: jest.fn(),
      setScore: jest.fn(),
      setFeedback: jest.fn(),
      undoFeedback: jest.fn(),
    };

    mockParams = { classId: "class-1", studentId: "student-1" };
    mockUseGradingJob.mockReturnValue({
      status: "completed",
      result: completedResult,
      error: null,
      photoUri: "file://assignment.jpg",
    });
    mockUseGradingReview.mockReturnValue(reviewControls);

    render(<GradingScreen />);

    expect(mockUseGradingReview).toHaveBeenCalledWith(completedResult);

    expect(mockGradingCard).toHaveBeenCalled();
    const gradingCardProps = mockGradingCard.mock.calls[mockGradingCard.mock.calls.length - 1]?.[0] as unknown as {
      status: string;
      reviewControls: unknown;
    };

    expect(gradingCardProps.status).toBe("completed");
    expect(gradingCardProps.reviewControls).toBe(reviewControls);
  });

  it("does not enable review controls outside completed status", () => {
    mockParams = { classId: "class-1", studentId: "student-1" };
    mockUseGradingJob.mockReturnValue({
      status: "processing",
      result: null,
      error: null,
      photoUri: null,
    });
    mockUseGradingReview.mockReturnValue(null);

    render(<GradingScreen />);

    expect(mockUseGradingReview).toHaveBeenCalledWith(null);

    expect(mockGradingCard).toHaveBeenCalled();
    const gradingCardProps = mockGradingCard.mock.calls[mockGradingCard.mock.calls.length - 1]?.[0] as unknown as {
      status: string;
      reviewControls: unknown;
    };

    expect(gradingCardProps.status).toBe("processing");
    expect(gradingCardProps.reviewControls).toBeNull();
  });

  it("passes approvalControls to GradingCard from useGradeApproval return value", () => {
    mockParams = { classId: "class-1", studentId: "student-1" };
    mockUseGradingJob.mockReturnValue({
      status: "completed",
      result: COMPLETED_RESULT,
      error: null,
      photoUri: null,
    });
    mockUseGradingReview.mockReturnValue(null);
    const approvalControls = makeApprovalControls();
    mockUseGradeApproval.mockReturnValue(approvalControls);

    render(<GradingScreen />);

    const props = mockGradingCard.mock.calls[mockGradingCard.mock.calls.length - 1]?.[0] as any;
    expect(props.approvalControls).toBe(approvalControls);
  });

  it("shows celebration view when isApproved=true and batchIndex >= batchTotal", () => {
    mockParams = { classId: "class-1", studentId: "student-1", batchIndex: "3", batchTotal: "3" };
    mockUseGradingJob.mockReturnValue({
      status: "completed",
      result: COMPLETED_RESULT,
      error: null,
      photoUri: null,
    });
    mockUseGradingReview.mockReturnValue({ scoreValue: 85 } as any);
    mockUseGradeApproval.mockReturnValue(makeApprovalControls({ isApproved: true }));

    render(<GradingScreen />);

    expect(screen.getByText(/All caught up/)).toBeTruthy();
  });

  it("does not show celebration when batchIndex < batchTotal — calls router.back() instead", () => {
    jest.useFakeTimers();
    mockParams = { classId: "class-1", studentId: "student-1", batchIndex: "2", batchTotal: "3" };
    mockUseGradingJob.mockReturnValue({
      status: "completed",
      result: COMPLETED_RESULT,
      error: null,
      photoUri: null,
    });
    mockUseGradingReview.mockReturnValue({ scoreValue: 85 } as any);
    mockUseGradeApproval.mockReturnValue(makeApprovalControls({ isApproved: true }));

    render(<GradingScreen />);

    expect(screen.queryByText(/All caught up/)).toBeNull();

    act(() => { jest.advanceTimersByTime(600); });
    expect(mockBack).toHaveBeenCalled();

    jest.useRealTimers();
  });

  it("does not show celebration when batchTotal is absent", () => {
    jest.useFakeTimers();
    mockParams = { classId: "class-1", studentId: "student-1" };
    mockUseGradingJob.mockReturnValue({
      status: "completed",
      result: COMPLETED_RESULT,
      error: null,
      photoUri: null,
    });
    mockUseGradingReview.mockReturnValue({ scoreValue: 85 } as any);
    mockUseGradeApproval.mockReturnValue(makeApprovalControls({ isApproved: true }));

    render(<GradingScreen />);

    expect(screen.queryByText(/All caught up/)).toBeNull();

    act(() => { jest.advanceTimersByTime(600); });
    expect(mockBack).toHaveBeenCalled();

    jest.useRealTimers();
  });

  it("Done button in celebration calls router.back()", () => {
    mockParams = { classId: "class-1", studentId: "student-1", batchIndex: "3", batchTotal: "3" };
    mockUseGradingJob.mockReturnValue({
      status: "completed",
      result: COMPLETED_RESULT,
      error: null,
      photoUri: null,
    });
    mockUseGradingReview.mockReturnValue({ scoreValue: 85 } as any);
    mockUseGradeApproval.mockReturnValue(makeApprovalControls({ isApproved: true }));

    render(<GradingScreen />);

    fireEvent.press(screen.getByRole("button", { name: /Done/i }));
    expect(mockBack).toHaveBeenCalled();
  });

  it("assignmentId URL param forwarded to useGradingJob as third arg", () => {
    mockParams = { classId: "class-1", studentId: "student-1", assignmentId: "asgn_existing" };
    mockUseGradingJob.mockReturnValue({ status: "processing", result: null, error: null, photoUri: null, retrying: false });
    mockUseGradingReview.mockReturnValue(null);

    render(<GradingScreen />);

    expect(mockUseGradingJob).toHaveBeenCalledWith("class-1", "student-1", "asgn_existing");
  });

  it("when status='failed' and result is not null → useManualGrading called with result", () => {
    mockParams = { classId: "class-1", studentId: "student-1" };
    mockUseGradingJob.mockReturnValue({ status: "failed", result: FAILED_RESULT, error: "AI failed", photoUri: null, retrying: false });
    mockUseGradingReview.mockReturnValue(null);

    render(<GradingScreen />);

    expect(mockUseManualGrading).toHaveBeenCalledWith(FAILED_RESULT);
  });

  it("when status='processing' → useManualGrading called with null", () => {
    mockParams = { classId: "class-1", studentId: "student-1" };
    mockUseGradingJob.mockReturnValue({ status: "processing", result: null, error: null, photoUri: null, retrying: false });
    mockUseGradingReview.mockReturnValue(null);

    render(<GradingScreen />);

    expect(mockUseManualGrading).toHaveBeenCalledWith(null);
  });

  it("processingHint='Still processing...' passed to GradingCard when retrying=true", () => {
    mockParams = { classId: "class-1", studentId: "student-1" };
    mockUseGradingJob.mockReturnValue({ status: "processing", result: null, error: null, photoUri: null, retrying: true });
    mockUseGradingReview.mockReturnValue(null);

    render(<GradingScreen />);

    const props = mockGradingCard.mock.calls[mockGradingCard.mock.calls.length - 1]?.[0] as any;
    expect(props.processingHint).toBe("Still processing...");
  });

  it("processingHint=null passed when status='processing' and not retrying", () => {
    mockParams = { classId: "class-1", studentId: "student-1" };
    mockUseGradingJob.mockReturnValue({ status: "processing", result: null, error: null, photoUri: null, retrying: false });
    mockUseGradingReview.mockReturnValue(null);

    render(<GradingScreen />);

    const props = mockGradingCard.mock.calls[mockGradingCard.mock.calls.length - 1]?.[0] as any;
    expect(props.processingHint).toBeNull();
  });

  it("onRetakePhoto is defined in GradingCard props when status='failed' and !isManualGrading", () => {
    mockParams = { classId: "class-1", studentId: "student-1" };
    mockUseGradingJob.mockReturnValue({ status: "failed", result: FAILED_RESULT, error: "AI failed", photoUri: null, retrying: false });
    mockUseGradingReview.mockReturnValue(null);

    render(<GradingScreen />);

    const props = mockGradingCard.mock.calls[mockGradingCard.mock.calls.length - 1]?.[0] as any;
    expect(props.onRetakePhoto).toBeDefined();
  });

  it("onGradeManually is defined in GradingCard props when status='failed' and !isManualGrading", () => {
    mockParams = { classId: "class-1", studentId: "student-1" };
    mockUseGradingJob.mockReturnValue({ status: "failed", result: FAILED_RESULT, error: "AI failed", photoUri: null, retrying: false });
    mockUseGradingReview.mockReturnValue(null);

    render(<GradingScreen />);

    const props = mockGradingCard.mock.calls[mockGradingCard.mock.calls.length - 1]?.[0] as any;
    expect(props.onGradeManually).toBeDefined();
  });

  it("after onGradeManually() is called, manualGradingControls becomes hook return value", () => {
    mockParams = { classId: "class-1", studentId: "student-1" };
    const mockControls = { scoreValue: 0, isSubmitted: false, submit: jest.fn() };
    mockUseManualGrading.mockReturnValue(mockControls);
    mockUseGradingJob.mockReturnValue({ status: "failed", result: FAILED_RESULT, error: "AI failed", photoUri: null, retrying: false });
    mockUseGradingReview.mockReturnValue(null);

    render(<GradingScreen />);

    // Initially manualGradingControls is null (isManualGrading=false)
    const propsBeforeManual = mockGradingCard.mock.calls[mockGradingCard.mock.calls.length - 1]?.[0] as any;
    expect(propsBeforeManual.manualGradingControls).toBeNull();

    // Call onGradeManually
    act(() => { propsBeforeManual.onGradeManually(); });

    const propsAfterManual = mockGradingCard.mock.calls[mockGradingCard.mock.calls.length - 1]?.[0] as any;
    expect(propsAfterManual.manualGradingControls).toBe(mockControls);
  });

  it("after onRetakePhoto() is called, router.replace called with camera pathname + context", () => {
    mockParams = { classId: "class-1", studentId: "student-1" };
    mockUseGradingJob.mockReturnValue({ status: "failed", result: FAILED_RESULT, error: "AI failed", photoUri: null, retrying: false });
    mockUseGradingReview.mockReturnValue(null);

    render(<GradingScreen />);

    const props = mockGradingCard.mock.calls[mockGradingCard.mock.calls.length - 1]?.[0] as any;
    act(() => { props.onRetakePhoto(); });

    expect(mockReplace).toHaveBeenCalledWith({
      pathname: "/(teacher)/camera",
      params: { classId: "class-1", studentId: "student-1", assignmentId: FAILED_RESULT.assignment_id },
    });
  });
});

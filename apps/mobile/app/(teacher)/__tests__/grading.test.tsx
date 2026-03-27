import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react-native";
import type { GradingJobWithResultResponse } from "@ilm/contracts";
import GradingScreen from "../grading";

const mockBack = jest.fn();
let mockParams: {
  classId?: string;
  studentId?: string;
  batchIndex?: string;
  batchTotal?: string;
} = {};

const mockUseGradingJob = jest.fn();
const mockUseGradingReview = jest.fn();
const mockUseGradeApproval = jest.fn();
const mockGradingCard = jest.fn((_: unknown) => null);

jest.mock("expo-router", () => ({
  useRouter: () => ({ back: mockBack }),
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

describe("grading screen", () => {
  beforeEach(() => {
    mockParams = {};
    mockBack.mockReset();
    mockUseGradingJob.mockReset();
    mockUseGradingReview.mockReset();
    mockUseGradeApproval.mockReset();
    mockUseGradeApproval.mockReturnValue(null);
    mockGradingCard.mockReset();
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

    expect(mockUseGradingJob).toHaveBeenCalledWith("", "");
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
});

import { act, renderHook } from "@testing-library/react-native";
import { useGradeApproval } from "../useGradeApproval";
import type { GradingJobWithResultResponse } from "@ilm/contracts";
import type { GradingReviewControls } from "../useGradingReview";
import type { PracticeRecommendationsControls } from "../usePracticeRecommendations";

jest.mock('../../../../services/grading-service', () => ({ approveGradingJob: jest.fn() }));
jest.mock('../../../../services/token-storage', () => ({ getAuthData: jest.fn() }));

import { approveGradingJob } from '../../../../services/grading-service';
import { getAuthData } from '../../../../services/token-storage';

const mockApproveGradingJob = approveGradingJob as jest.MockedFunction<typeof approveGradingJob>;
const mockGetAuthData = getAuthData as jest.MockedFunction<typeof getAuthData>;

const makeResult = (overrides: Partial<GradingJobWithResultResponse> = {}): GradingJobWithResultResponse => ({
  job_id: 'job_1',
  artifact_id: 'art_1',
  assignment_id: 'asgn_1',
  status: 'completed',
  attempt_count: 1,
  submitted_at: '2026-03-26T00:00:00Z',
  completed_at: '2026-03-26T00:00:01Z',
  is_approved: false,
  failure_code: null,
  failure_reason: null,
  rubric_criteria: [],
  result: {
    proposed_score: '85/100',
    draft_feedback: 'Good work.',
    confidence_level: 'high',
    confidence_score: 0.9,
    confidence_reason: null,
    rubric_mapping: {},
    generated_at: '2026-03-26T00:00:01Z',
    practice_recommendations: [],
  },
  ...overrides,
});

const makeReviewControls = (overrides: Partial<GradingReviewControls> = {}): GradingReviewControls => ({
  scoreValue: 85,
  scoreInputText: '85',
  displayScore: '85/100',
  feedbackValue: 'Good work.',
  increment: jest.fn(),
  decrement: jest.fn(),
  setScore: jest.fn(),
  setFeedback: jest.fn(),
  undoFeedback: jest.fn(),
  ...overrides,
});

describe("useGradeApproval", () => {
  beforeEach(() => {
    mockApproveGradingJob.mockReset();
    mockGetAuthData.mockReset();
  });

  it("returns null when result is null", () => {
    const { result } = renderHook(() => useGradeApproval(null, null));
    expect(result.current).toBeNull();
  });

  it("initializes isApproved=true when result.is_approved=true", () => {
    const { result } = renderHook(() =>
      useGradeApproval(makeResult({ is_approved: true }), makeReviewControls()),
    );
    expect(result.current?.isApproved).toBe(true);
  });

  it("initializes isApproved=false when result.is_approved=false", () => {
    const { result } = renderHook(() =>
      useGradeApproval(makeResult({ is_approved: false }), makeReviewControls()),
    );
    expect(result.current?.isApproved).toBe(false);
  });

  it("returns null when result is null — approve() is not available to callers", () => {
    const { result } = renderHook(() => useGradeApproval(null, null));
    // Hook returns null so approve() is inaccessible; verify no API call leaked through
    expect(result.current).toBeNull();
    expect(mockApproveGradingJob).not.toHaveBeenCalled();
  });

  it("approve() sets isApproved=true optimistically and isApproving=true before API resolves", async () => {
    let resolveApprove!: () => void;
    const pendingPromise = new Promise<void>((resolve) => {
      resolveApprove = resolve;
    });
    mockGetAuthData.mockResolvedValue({ token: 'tok_1', role: 'teacher', homePath: '/', email: 'test@test.com' });
    mockApproveGradingJob.mockReturnValue(pendingPromise as any);

    const { result } = renderHook(() =>
      useGradeApproval(makeResult(), makeReviewControls()),
    );

    act(() => {
      result.current!.approve();
    });

    // Optimistic update fires synchronously
    expect(result.current?.isApproved).toBe(true);
    expect(result.current?.isApproving).toBe(true);

    // After resolve, isApproving clears
    await act(async () => {
      resolveApprove();
    });
    expect(result.current?.isApproving).toBe(false);
    expect(result.current?.isApproved).toBe(true);
  });

  it("calls approveGradingJob with correct arguments (no practice recs — sends empty array)", async () => {
    const approvalResponse = {
      job_id: 'job_1',
      approved_score: '85',
      approved_feedback: 'Good work.',
      approver_user_id: 'user_1',
      approved_at: '2026-03-27T00:00:00Z',
      version: 1,
      practice_recommendations: [],
    };
    mockGetAuthData.mockResolvedValue({ token: 'tok_1', role: 'teacher', homePath: '/', email: 'test@test.com' });
    mockApproveGradingJob.mockResolvedValue(approvalResponse);

    const { result } = renderHook(() =>
      useGradeApproval(makeResult({ assignment_id: 'asgn_1', job_id: 'job_1' }), makeReviewControls({ scoreValue: 85, feedbackValue: 'Good work.' })),
    );

    await act(async () => {
      result.current!.approve();
    });

    expect(mockApproveGradingJob).toHaveBeenCalledWith('asgn_1', 'job_1', '85', 'Good work.', 'tok_1', []);
  });

  it("passes practice recommendations to approveGradingJob when provided", async () => {
    const approvalResponse = {
      job_id: 'job_1',
      approved_score: '85',
      approved_feedback: 'Good work.',
      approver_user_id: 'user_1',
      approved_at: '2026-03-27T00:00:00Z',
      version: 1,
      practice_recommendations: ['Practice A'],
    };
    mockGetAuthData.mockResolvedValue({ token: 'tok_1', role: 'teacher', homePath: '/', email: 'test@test.com' });
    mockApproveGradingJob.mockResolvedValue(approvalResponse);

    const mockPracticeControls: PracticeRecommendationsControls = {
      recommendations: ['Practice A'],
      originalRecommendations: ['Practice A'],
      modifiedIndices: new Set(),
      editRecommendation: jest.fn(),
      resetRecommendation: jest.fn(),
    };

    const { result } = renderHook(() =>
      useGradeApproval(
        makeResult({ assignment_id: 'asgn_1', job_id: 'job_1' }),
        makeReviewControls({ scoreValue: 85, feedbackValue: 'Good work.' }),
        mockPracticeControls,
      ),
    );

    await act(async () => {
      result.current!.approve();
    });

    expect(mockApproveGradingJob).toHaveBeenCalledWith('asgn_1', 'job_1', '85', 'Good work.', 'tok_1', ['Practice A']);
  });

  it("passes empty array when practiceRecommendationsControls is null", async () => {
    const approvalResponse = {
      job_id: 'job_1',
      approved_score: '85',
      approved_feedback: 'Good work.',
      approver_user_id: 'user_1',
      approved_at: '2026-03-27T00:00:00Z',
      version: 1,
      practice_recommendations: [],
    };
    mockGetAuthData.mockResolvedValue({ token: 'tok_1', role: 'teacher', homePath: '/', email: 'test@test.com' });
    mockApproveGradingJob.mockResolvedValue(approvalResponse);

    const { result } = renderHook(() =>
      useGradeApproval(
        makeResult({ assignment_id: 'asgn_1', job_id: 'job_1' }),
        makeReviewControls({ scoreValue: 85, feedbackValue: 'Good work.' }),
        null,
      ),
    );

    await act(async () => {
      result.current!.approve();
    });

    expect(mockApproveGradingJob).toHaveBeenCalledWith('asgn_1', 'job_1', '85', 'Good work.', 'tok_1', []);
  });

  it("sends edited recommendations when practiceRecommendationsControls updates before approve", async () => {
    // Regression: approve() was capturing a stale closure because practiceRecommendationsControls
    // was missing from the useCallback dependency array.
    const approvalResponse = {
      job_id: 'job_1',
      approved_score: '85',
      approved_feedback: 'Good work.',
      approver_user_id: 'user_1',
      approved_at: '2026-03-27T00:00:00Z',
      version: 1,
      practice_recommendations: ['Edited rec'],
    };
    mockGetAuthData.mockResolvedValue({ token: 'tok_1', role: 'teacher', homePath: '/', email: 'test@test.com' });
    mockApproveGradingJob.mockResolvedValue(approvalResponse);

    const initialControls: PracticeRecommendationsControls = {
      recommendations: ['Original rec'],
      originalRecommendations: ['Original rec'],
      modifiedIndices: new Set(),
      editRecommendation: jest.fn(),
      resetRecommendation: jest.fn(),
    };
    const updatedControls: PracticeRecommendationsControls = {
      recommendations: ['Edited rec'],
      originalRecommendations: ['Original rec'],
      modifiedIndices: new Set([0]),
      editRecommendation: jest.fn(),
      resetRecommendation: jest.fn(),
    };

    const { result, rerender } = renderHook(
      ({ p }: { p: PracticeRecommendationsControls }) =>
        useGradeApproval(
          makeResult({ assignment_id: 'asgn_1', job_id: 'job_1' }),
          makeReviewControls({ scoreValue: 85, feedbackValue: 'Good work.' }),
          p,
        ),
      { initialProps: { p: initialControls } },
    );

    // Simulate teacher editing a recommendation before tapping Approve
    rerender({ p: updatedControls });

    await act(async () => {
      result.current!.approve();
    });

    // Must send the edited value, not the original stale closure value
    expect(mockApproveGradingJob).toHaveBeenCalledWith('asgn_1', 'job_1', '85', 'Good work.', 'tok_1', ['Edited rec']);
  });

  it("on API rejection, rolls back — isApproved=false, approvalError set", async () => {
    mockGetAuthData.mockResolvedValue({ token: 'tok_1', role: 'teacher', homePath: '/', email: 'test@test.com' });
    mockApproveGradingJob.mockRejectedValue(new Error('Server error'));

    const { result } = renderHook(() =>
      useGradeApproval(makeResult(), makeReviewControls()),
    );

    await act(async () => {
      result.current!.approve();
    });

    expect(result.current?.isApproved).toBe(false);
    expect(result.current?.approvalError).toBe('Server error');
  });

  it("resets isApproved, approvalState, and approvalError when result job_id changes", async () => {
    mockGetAuthData.mockResolvedValue({ token: 'tok_1', role: 'teacher', homePath: '/', email: 'test@test.com' });
    mockApproveGradingJob.mockRejectedValue(new Error('Server error'));

    const { result, rerender } = renderHook(
      ({ r }: { r: ReturnType<typeof makeResult> }) => useGradeApproval(r, makeReviewControls()),
      { initialProps: { r: makeResult({ job_id: 'job_1' }) } },
    );

    // Drive the hook into an error state on job_1
    await act(async () => { result.current!.approve(); });
    expect(result.current?.approvalError).toBe('Server error');
    expect(result.current?.isApproved).toBe(false);

    // Swap to a new job — state must reset
    rerender({ r: makeResult({ job_id: 'job_2', is_approved: false }) });
    expect(result.current?.isApproved).toBe(false);
    expect(result.current?.approvalError).toBeNull();
  });

  it("when getAuthData() returns null, sets approvalError and does NOT call approveGradingJob", async () => {
    mockGetAuthData.mockResolvedValue(null);

    const { result } = renderHook(() =>
      useGradeApproval(makeResult(), makeReviewControls()),
    );

    await act(async () => {
      result.current!.approve();
    });

    expect(mockApproveGradingJob).not.toHaveBeenCalled();
    expect(result.current?.approvalError).toBe('Session expired — please sign in again');
    expect(result.current?.isApproved).toBe(false);
  });
});

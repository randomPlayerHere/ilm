import { act, renderHook } from "@testing-library/react-native";
import { useManualGrading } from "../useManualGrading";
import type { GradingJobWithResultResponse } from "@ilm/contracts";

jest.mock("../../../../services/grading-service", () => ({ submitManualGrade: jest.fn() }));
jest.mock("../../../../services/token-storage", () => ({ getAuthData: jest.fn() }));

import { submitManualGrade } from "../../../../services/grading-service";
import { getAuthData } from "../../../../services/token-storage";

const mockSubmitManualGrade = submitManualGrade as jest.MockedFunction<typeof submitManualGrade>;
const mockGetAuthData = getAuthData as jest.MockedFunction<typeof getAuthData>;

const makeResult = (overrides: Partial<GradingJobWithResultResponse> = {}): GradingJobWithResultResponse => ({
  job_id: "job_1",
  assignment_id: "asgn_1",
  artifact_id: "art_1",
  status: "failed",
  attempt_count: 2,
  submitted_at: "2026-03-27T00:00:00Z",
  completed_at: "2026-03-27T00:00:01Z",
  result: null,
  is_approved: false,
  failure_code: "IMAGE_BLURRY",
  failure_reason: "Handwriting unclear",
  rubric_criteria: [{ criterion: "Clarity", description: "Clear reasoning" }],
  ...overrides,
});

describe("useManualGrading", () => {
  beforeEach(() => {
    mockSubmitManualGrade.mockReset();
    mockGetAuthData.mockReset();
  });

  it("returns null when result is null", () => {
    const { result } = renderHook(() => useManualGrading(null));
    expect(result.current).toBeNull();
  });

  it("initializes scoreValue=0, feedbackValue='', submitState='idle'", () => {
    const { result } = renderHook(() => useManualGrading(makeResult()));
    expect(result.current?.scoreValue).toBe(0);
    expect(result.current?.feedbackValue).toBe("");
    expect(result.current?.submitState).toBe("idle");
  });

  it("rubricCriteria comes from result.rubric_criteria", () => {
    const { result } = renderHook(() =>
      useManualGrading(makeResult({ rubric_criteria: [{ criterion: "Clarity", description: "Clear reasoning" }] })),
    );
    expect(result.current?.rubricCriteria).toEqual([{ criterion: "Clarity", description: "Clear reasoning" }]);
  });

  it("increment() clamps to 100", () => {
    const { result } = renderHook(() => useManualGrading(makeResult()));
    act(() => { result.current?.setScore("100"); });
    act(() => { result.current?.increment(); });
    expect(result.current?.scoreValue).toBe(100);
  });

  it("decrement() clamps to 0", () => {
    const { result } = renderHook(() => useManualGrading(makeResult()));
    act(() => { result.current?.decrement(); });
    expect(result.current?.scoreValue).toBe(0);
  });

  it("setScore('85') sets scoreValue=85 and scoreInputText='85'", () => {
    const { result } = renderHook(() => useManualGrading(makeResult()));
    act(() => { result.current?.setScore("85"); });
    expect(result.current?.scoreValue).toBe(85);
    expect(result.current?.scoreInputText).toBe("85");
  });

  it("setScore('') keeps previous scoreValue unchanged (ignores NaN)", () => {
    const { result } = renderHook(() => useManualGrading(makeResult()));
    act(() => { result.current?.setScore("85"); });
    act(() => { result.current?.setScore(""); });
    expect(result.current?.scoreValue).toBe(85);
  });

  it("submit() sets isSubmitting=true before API resolves", async () => {
    let resolveSubmit!: () => void;
    const pendingPromise = new Promise<any>((resolve) => { resolveSubmit = resolve; });
    mockGetAuthData.mockResolvedValue({ token: "tok_1", role: "teacher", homePath: "/", email: "test@test.com" });
    mockSubmitManualGrade.mockReturnValue(pendingPromise);

    const { result } = renderHook(() => useManualGrading(makeResult()));

    act(() => { result.current?.submit(); });

    // After the sync call but before getAuthData resolves, submitState is loading
    // We need to wait for getAuthData but not for submitManualGrade
    await act(async () => { await Promise.resolve(); }); // flush getAuthData
    // At this point getAuthData resolved, submitManualGrade is still pending
    expect(result.current?.isSubmitting).toBe(true);

    await act(async () => { resolveSubmit({ job_id: "job_1", score: "0", feedback: "", grader_user_id: "u1", graded_at: "" }); });
  });

  it("calls submitManualGrade with result.assignment_id, result.job_id, String(scoreValue), feedbackValue, token", async () => {
    mockGetAuthData.mockResolvedValue({ token: "tok_1", role: "teacher", homePath: "/", email: "test@test.com" });
    mockSubmitManualGrade.mockResolvedValue({ job_id: "job_1", score: "0", feedback: "", grader_user_id: "u1", graded_at: "" });

    const { result } = renderHook(() => useManualGrading(makeResult()));
    act(() => { result.current?.setScore("75"); });
    act(() => { result.current?.setFeedback("Well done."); });

    await act(async () => { result.current?.submit(); });

    expect(mockSubmitManualGrade).toHaveBeenCalledWith("asgn_1", "job_1", "75", "Well done.", "tok_1");
  });

  it("on success → isSubmitted=true, submitState='submitted'", async () => {
    mockGetAuthData.mockResolvedValue({ token: "tok_1", role: "teacher", homePath: "/", email: "test@test.com" });
    mockSubmitManualGrade.mockResolvedValue({ job_id: "job_1", score: "0", feedback: "", grader_user_id: "u1", graded_at: "" });

    const { result } = renderHook(() => useManualGrading(makeResult()));
    await act(async () => { result.current?.submit(); });

    expect(result.current?.isSubmitted).toBe(true);
    expect(result.current?.submitState).toBe("submitted");
  });

  it("on API rejection → submitState='error', submitError set to error message", async () => {
    mockGetAuthData.mockResolvedValue({ token: "tok_1", role: "teacher", homePath: "/", email: "test@test.com" });
    mockSubmitManualGrade.mockRejectedValue(new Error("Server error"));

    const { result } = renderHook(() => useManualGrading(makeResult()));
    await act(async () => { result.current?.submit(); });

    expect(result.current?.submitState).toBe("error");
    expect(result.current?.submitError).toBe("Server error");
  });

  it("when getAuthData() returns null → submitError = 'Session expired — please sign in again', submitManualGrade NOT called", async () => {
    mockGetAuthData.mockResolvedValue(null);

    const { result } = renderHook(() => useManualGrading(makeResult()));
    await act(async () => { result.current?.submit(); });

    expect(mockSubmitManualGrade).not.toHaveBeenCalled();
    expect(result.current?.submitError).toBe("Session expired — please sign in again");
  });

  it("submit() no-op when submitState === 'submitted'", async () => {
    mockGetAuthData.mockResolvedValue({ token: "tok_1", role: "teacher", homePath: "/", email: "test@test.com" });
    mockSubmitManualGrade.mockResolvedValue({ job_id: "job_1", score: "0", feedback: "", grader_user_id: "u1", graded_at: "" });

    const { result } = renderHook(() => useManualGrading(makeResult()));
    await act(async () => { result.current?.submit(); });
    expect(result.current?.submitState).toBe("submitted");

    mockSubmitManualGrade.mockReset();
    await act(async () => { result.current?.submit(); });
    expect(mockSubmitManualGrade).not.toHaveBeenCalled();
  });

  it("submit() no-op when submitState === 'loading'", async () => {
    let resolveSubmit!: () => void;
    const pendingPromise = new Promise<any>((resolve) => { resolveSubmit = resolve; });
    mockGetAuthData.mockResolvedValue({ token: "tok_1", role: "teacher", homePath: "/", email: "test@test.com" });
    mockSubmitManualGrade.mockReturnValue(pendingPromise);

    const { result } = renderHook(() => useManualGrading(makeResult()));
    act(() => { result.current?.submit(); });
    await act(async () => { await Promise.resolve(); }); // flush getAuthData

    // Now in loading state — call submit again
    await act(async () => { result.current?.submit(); });
    // Only one call should have been made
    expect(mockSubmitManualGrade).toHaveBeenCalledTimes(1);

    await act(async () => { resolveSubmit({ job_id: "job_1", score: "0", feedback: "", grader_user_id: "u1", graded_at: "" }); });
  });
});

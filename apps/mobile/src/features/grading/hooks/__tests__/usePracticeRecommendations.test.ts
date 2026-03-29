import { act, renderHook } from "@testing-library/react-native";
import { usePracticeRecommendations } from "../usePracticeRecommendations";
import type { GradingJobWithResultResponse } from "@ilm/contracts";

const makeResult = (recs: string[] = ["Practice A", "Practice B"]): GradingJobWithResultResponse => ({
  job_id: "job_1",
  artifact_id: "art_1",
  assignment_id: "asgn_1",
  status: "completed",
  attempt_count: 1,
  submitted_at: "2026-03-28T00:00:00Z",
  completed_at: "2026-03-28T00:00:01Z",
  is_approved: false,
  failure_code: null,
  failure_reason: null,
  rubric_criteria: [],
  result: {
    proposed_score: "85",
    rubric_mapping: {},
    draft_feedback: "Good work",
    generated_at: "2026-03-28T00:00:01Z",
    confidence_level: "high",
    confidence_score: 0.9,
    confidence_reason: null,
    practice_recommendations: recs,
  },
});

describe("usePracticeRecommendations", () => {
  it("returns null when result is null", () => {
    const { result } = renderHook(() => usePracticeRecommendations(null));
    expect(result.current).toBeNull();
  });

  it("returns null when result.result is null", () => {
    const noResult: GradingJobWithResultResponse = {
      ...makeResult(),
      result: null,
    };
    const { result } = renderHook(() => usePracticeRecommendations(noResult));
    expect(result.current).toBeNull();
  });

  it("returns null when practice_recommendations is empty", () => {
    const { result } = renderHook(() => usePracticeRecommendations(makeResult([])));
    expect(result.current).toBeNull();
  });

  it("initializes recommendations from result.result.practice_recommendations", () => {
    const { result } = renderHook(() =>
      usePracticeRecommendations(makeResult(["Practice A", "Practice B"])),
    );
    expect(result.current?.recommendations).toEqual(["Practice A", "Practice B"]);
  });

  it("limits to max 3 recommendations even if AI returns more", () => {
    const { result } = renderHook(() =>
      usePracticeRecommendations(makeResult(["A", "B", "C", "D", "E"])),
    );
    expect(result.current?.recommendations).toHaveLength(3);
    expect(result.current?.recommendations).toEqual(["A", "B", "C"]);
  });

  it("starts with empty modifiedIndices", () => {
    const { result } = renderHook(() => usePracticeRecommendations(makeResult()));
    expect(result.current?.modifiedIndices.size).toBe(0);
  });

  it("editRecommendation updates recommendations[0] and adds 0 to modifiedIndices", () => {
    const { result } = renderHook(() => usePracticeRecommendations(makeResult()));
    act(() => {
      result.current!.editRecommendation(0, "New text");
    });
    expect(result.current?.recommendations[0]).toBe("New text");
    expect(result.current?.modifiedIndices.has(0)).toBe(true);
  });

  it("editRecommendation with original text removes index from modifiedIndices", () => {
    const { result } = renderHook(() =>
      usePracticeRecommendations(makeResult(["Practice A", "Practice B"])),
    );
    // First edit to something different
    act(() => {
      result.current!.editRecommendation(0, "Modified");
    });
    expect(result.current?.modifiedIndices.has(0)).toBe(true);

    // Then edit back to original
    act(() => {
      result.current!.editRecommendation(0, "Practice A");
    });
    expect(result.current?.modifiedIndices.has(0)).toBe(false);
  });

  it("resetRecommendation restores original text and removes index from modifiedIndices", () => {
    const { result } = renderHook(() =>
      usePracticeRecommendations(makeResult(["Practice A", "Practice B"])),
    );
    act(() => {
      result.current!.editRecommendation(0, "Modified");
    });
    expect(result.current?.recommendations[0]).toBe("Modified");
    expect(result.current?.modifiedIndices.has(0)).toBe(true);

    act(() => {
      result.current!.resetRecommendation(0);
    });
    expect(result.current?.recommendations[0]).toBe("Practice A");
    expect(result.current?.modifiedIndices.has(0)).toBe(false);
  });

  it("modifying index 1 does not affect index 0 modification state", () => {
    const { result } = renderHook(() =>
      usePracticeRecommendations(makeResult(["Practice A", "Practice B"])),
    );
    act(() => {
      result.current!.editRecommendation(1, "Modified B");
    });
    expect(result.current?.modifiedIndices.has(0)).toBe(false);
    expect(result.current?.modifiedIndices.has(1)).toBe(true);
  });

  it("re-initializes state when result.job_id changes", () => {
    const { result, rerender } = renderHook(
      ({ r }: { r: GradingJobWithResultResponse }) => usePracticeRecommendations(r),
      { initialProps: { r: makeResult(["Practice A"]) } },
    );
    // Edit first
    act(() => {
      result.current!.editRecommendation(0, "Modified");
    });
    expect(result.current?.modifiedIndices.has(0)).toBe(true);

    // Switch to new job
    const newResult: GradingJobWithResultResponse = {
      ...makeResult(["New Practice"]),
      job_id: "job_2",
    };
    rerender({ r: newResult });

    expect(result.current?.recommendations).toEqual(["New Practice"]);
    expect(result.current?.modifiedIndices.size).toBe(0);
  });

  it("originalRecommendations never changes after edits", () => {
    const { result } = renderHook(() =>
      usePracticeRecommendations(makeResult(["Practice A", "Practice B"])),
    );
    act(() => {
      result.current!.editRecommendation(0, "Modified");
      result.current!.editRecommendation(1, "Also modified");
    });
    expect(result.current?.originalRecommendations).toEqual(["Practice A", "Practice B"]);
  });
});

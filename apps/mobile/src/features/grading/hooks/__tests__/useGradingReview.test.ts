import { act, renderHook } from "@testing-library/react-native";
import { useGradingReview } from "../useGradingReview";
import type { GradingJobWithResultResponse } from "@ilm/contracts";

const makeResult = (
  proposed_score: string,
  draft_feedback: string,
  confidence_level: "high" | "medium" | "low" = "high",
): GradingJobWithResultResponse => ({
  job_id: "job_1",
  artifact_id: "art_1",
  assignment_id: "asgn_1",
  status: "completed",
  attempt_count: 1,
  submitted_at: "2026-03-26T00:00:00Z",
  completed_at: "2026-03-26T00:00:01Z",
  is_approved: false,
  result: {
    proposed_score,
    draft_feedback,
    confidence_level,
    confidence_score: 0.9,
    confidence_reason: null,
    rubric_mapping: { Clarity: "Excellent" },
    generated_at: "2026-03-26T00:00:01Z",
    practice_recommendations: [],
  },
});

describe("useGradingReview", () => {
  describe("initialization", () => {
    it("returns null when result is null", () => {
      const { result } = renderHook(() => useGradingReview(null));
      expect(result.current).toBeNull();
    });

    it("initializes scoreValue from proposed_score (integer part)", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("85/100", "Good work.")));
      expect(result.current?.scoreValue).toBe(85);
    });

    it("initializes scoreInputText from proposed_score integer", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("72/100", "Good work.")));
      expect(result.current?.scoreInputText).toBe("72");
    });

    it("initializes displayScore in NN/100 format", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("90/100", "Good work.")));
      expect(result.current?.displayScore).toBe("90/100");
    });

    it("initializes feedbackValue from draft_feedback", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("80/100", "Keep it up!")));
      expect(result.current?.feedbackValue).toBe("Keep it up!");
    });

    it("clamps proposed_score above 100 to 100", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("150/100", "Good.")));
      expect(result.current?.scoreValue).toBe(100);
    });

    it("clamps negative proposed_score to 0", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("-5/100", "Good.")));
      expect(result.current?.scoreValue).toBe(0);
    });

    it("handles plain integer proposed_score without /100", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("75", "Good.")));
      expect(result.current?.scoreValue).toBe(75);
    });
  });

  describe("score controls", () => {
    it("increment increases scoreValue by 1", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("85/100", "Good.")));
      act(() => result.current!.increment());
      expect(result.current?.scoreValue).toBe(86);
      expect(result.current?.scoreInputText).toBe("86");
      expect(result.current?.displayScore).toBe("86/100");
    });

    it("decrement decreases scoreValue by 1", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("85/100", "Good.")));
      act(() => result.current!.decrement());
      expect(result.current?.scoreValue).toBe(84);
      expect(result.current?.scoreInputText).toBe("84");
      expect(result.current?.displayScore).toBe("84/100");
    });

    it("increment does not exceed 100", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("100/100", "Good.")));
      act(() => result.current!.increment());
      expect(result.current?.scoreValue).toBe(100);
    });

    it("decrement does not go below 0", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("0/100", "Good.")));
      act(() => result.current!.decrement());
      expect(result.current?.scoreValue).toBe(0);
    });

    it("setScore updates scoreValue and scoreInputText for valid integer string", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("85/100", "Good.")));
      act(() => result.current!.setScore("60"));
      expect(result.current?.scoreValue).toBe(60);
      expect(result.current?.scoreInputText).toBe("60");
    });

    it("setScore clamps value above 100 to 100", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("85/100", "Good.")));
      act(() => result.current!.setScore("150"));
      expect(result.current?.scoreValue).toBe(100);
    });

    it("setScore clamps negative value to 0", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("85/100", "Good.")));
      act(() => result.current!.setScore("-10"));
      expect(result.current?.scoreValue).toBe(0);
    });

    it("setScore with empty string keeps scoreValue unchanged but updates scoreInputText", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("85/100", "Good.")));
      act(() => result.current!.setScore(""));
      expect(result.current?.scoreValue).toBe(85);
      expect(result.current?.scoreInputText).toBe("");
    });

    it("setScore with non-numeric string keeps scoreValue unchanged", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("85/100", "Good.")));
      act(() => result.current!.setScore("abc"));
      expect(result.current?.scoreValue).toBe(85);
    });
  });

  describe("feedback controls", () => {
    it("setFeedback updates feedbackValue", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("85/100", "Original.")));
      act(() => result.current!.setFeedback("Edited feedback."));
      expect(result.current?.feedbackValue).toBe("Edited feedback.");
    });

    it("undoFeedback restores original AI draft_feedback", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("85/100", "Original AI draft.")));
      act(() => result.current!.setFeedback("Edited feedback."));
      expect(result.current?.feedbackValue).toBe("Edited feedback.");
      act(() => result.current!.undoFeedback());
      expect(result.current?.feedbackValue).toBe("Original AI draft.");
    });

    it("undoFeedback after multiple edits always restores to original AI draft", () => {
      const { result } = renderHook(() => useGradingReview(makeResult("85/100", "AI original.")));
      act(() => result.current!.setFeedback("Edit 1"));
      act(() => result.current!.setFeedback("Edit 2"));
      act(() => result.current!.undoFeedback());
      expect(result.current?.feedbackValue).toBe("AI original.");
    });
  });

  describe("result transitions", () => {
    it("returns null initially and initializes when result arrives", () => {
      let resultProp: GradingJobWithResultResponse | null = null;
      const { result, rerender } = renderHook(() => useGradingReview(resultProp));
      expect(result.current).toBeNull();

      resultProp = makeResult("78/100", "Nice work.");
      rerender({});

      expect(result.current?.scoreValue).toBe(78);
      expect(result.current?.feedbackValue).toBe("Nice work.");
    });
  });
});

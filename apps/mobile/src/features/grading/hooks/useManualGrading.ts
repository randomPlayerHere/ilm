import { useCallback, useEffect, useRef, useState } from "react";
import type { GradingJobWithResultResponse } from "@ilm/contracts";
import { getAuthData } from "../../../services/token-storage";
import { submitManualGrade } from "../../../services/grading-service";

export interface ManualGradingControls {
  scoreValue: number;
  scoreInputText: string;
  feedbackValue: string;
  submitState: "idle" | "loading" | "submitted" | "error";
  submitError: string | null;
  isSubmitting: boolean;
  isSubmitted: boolean;
  rubricCriteria: { criterion: string; description: string | null }[];
  setScore: (raw: string) => void;
  setFeedback: (text: string) => void;
  increment: () => void;
  decrement: () => void;
  submit: () => void;
}

export function useManualGrading(
  result: GradingJobWithResultResponse | null,
): ManualGradingControls | null {
  const [scoreValue, setScoreValue] = useState(0);
  const [scoreInputText, setScoreInputText] = useState("0");
  const [feedbackValue, setFeedbackValue] = useState("");
  const [submitState, setSubmitState] = useState<"idle" | "loading" | "submitted" | "error">("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const isMountedRef = useRef(true);
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const setScore = useCallback((raw: string) => {
    const parsed = parseInt(raw, 10);
    if (isNaN(parsed)) return;
    const clamped = Math.min(100, Math.max(0, parsed));
    setScoreValue(clamped);
    setScoreInputText(String(clamped));
  }, []);

  const setFeedback = useCallback((text: string) => {
    setFeedbackValue(text);
  }, []);

  const increment = useCallback(() => {
    setScoreValue((v) => {
      const next = Math.min(100, v + 1);
      setScoreInputText(String(next));
      return next;
    });
  }, []);

  const decrement = useCallback(() => {
    setScoreValue((v) => {
      const next = Math.max(0, v - 1);
      setScoreInputText(String(next));
      return next;
    });
  }, []);

  const submit = useCallback(async () => {
    if (!result) return;
    if (submitState === "loading" || submitState === "submitted") return;

    setSubmitState("loading");
    setSubmitError(null);

    const authData = await getAuthData();
    if (!isMountedRef.current) return;

    if (authData === null) {
      setSubmitError("Session expired — please sign in again");
      setSubmitState("error");
      return;
    }

    try {
      await submitManualGrade(
        result.assignment_id,
        result.job_id,
        String(scoreValue),
        feedbackValue,
        authData.token,
      );
      if (!isMountedRef.current) return;
      setSubmitState("submitted");
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      const message = err instanceof Error ? err.message : "Grade submission failed";
      setSubmitState("error");
      setSubmitError(message);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result, submitState, scoreValue, feedbackValue]);

  if (result === null) return null;

  return {
    scoreValue,
    scoreInputText,
    feedbackValue,
    submitState,
    submitError,
    isSubmitting: submitState === "loading",
    isSubmitted: submitState === "submitted",
    rubricCriteria: result.rubric_criteria,
    setScore,
    setFeedback,
    increment,
    decrement,
    submit,
  };
}

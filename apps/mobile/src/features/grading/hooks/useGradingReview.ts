import { useCallback, useEffect, useRef, useState } from "react";
import type { GradingJobWithResultResponse } from "@ilm/contracts";

export interface GradingReviewControls {
  scoreValue: number;
  scoreInputText: string;
  displayScore: string;
  feedbackValue: string;
  increment: () => void;
  decrement: () => void;
  setScore: (raw: string) => void;
  setFeedback: (text: string) => void;
  undoFeedback: () => void;
}

function parseProposedScore(proposed: string): number {
  const num = parseInt(proposed.split("/")[0] ?? proposed, 10);
  if (isNaN(num)) return 0;
  return Math.min(100, Math.max(0, num));
}

/**
 * Local review-state hook for the grading review card.
 * Initializes from the completed grading result and exposes score/feedback
 * editing controls. Returns null when no result is available yet.
 */
export function useGradingReview(
  result: GradingJobWithResultResponse | null,
): GradingReviewControls | null {
  const aiResult = result?.result ?? null;
  const initializedRef = useRef(false);
  const originalFeedbackRef = useRef<string>("");

  const [scoreValue, setScoreValue] = useState<number>(0);
  const [scoreInputText, setScoreInputText] = useState<string>("0");
  const [feedbackValue, setFeedbackValue] = useState<string>("");

  // Initialize state once when result first arrives
  useEffect(() => {
    if (aiResult && !initializedRef.current) {
      initializedRef.current = true;
      const parsed = parseProposedScore(aiResult.proposed_score);
      setScoreValue(parsed);
      setScoreInputText(String(parsed));
      setFeedbackValue(aiResult.draft_feedback);
      originalFeedbackRef.current = aiResult.draft_feedback;
    }
  }, [aiResult]);

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

  const setScore = useCallback((raw: string) => {
    setScoreInputText(raw);
    if (raw === "") return;
    const parsed = parseInt(raw, 10);
    if (isNaN(parsed)) return;
    setScoreValue(Math.min(100, Math.max(0, parsed)));
  }, []);

  const setFeedback = useCallback((text: string) => {
    setFeedbackValue(text);
  }, []);

  const undoFeedback = useCallback(() => {
    setFeedbackValue(originalFeedbackRef.current);
  }, []);

  if (!aiResult) return null;

  return {
    scoreValue,
    scoreInputText,
    displayScore: `${scoreValue}/100`,
    feedbackValue,
    increment,
    decrement,
    setScore,
    setFeedback,
    undoFeedback,
  };
}

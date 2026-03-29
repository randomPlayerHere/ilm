import { useCallback, useEffect, useRef, useState } from "react";
import type { GradingJobWithResultResponse } from "@ilm/contracts";

export interface PracticeRecommendationsControls {
  recommendations: string[];
  originalRecommendations: string[];
  modifiedIndices: Set<number>;
  editRecommendation: (index: number, text: string) => void;
  resetRecommendation: (index: number) => void;
}

export function usePracticeRecommendations(
  result: GradingJobWithResultResponse | null,
): PracticeRecommendationsControls | null {
  const aiResult = result?.result ?? null;
  const initializedRefKeyRef = useRef<string | null>(null);
  const originalRecommendationsRef = useRef<string[]>([]);

  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [modifiedIndices, setModifiedIndices] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!result || !aiResult) {
      initializedRefKeyRef.current = null;
      return;
    }

    const initKey = `${result.job_id}:${aiResult.generated_at}`;
    if (initializedRefKeyRef.current === initKey) {
      return;
    }

    initializedRefKeyRef.current = initKey;
    const sliced = aiResult.practice_recommendations.slice(0, 3);
    originalRecommendationsRef.current = sliced;
    setRecommendations(sliced);
    setModifiedIndices(new Set());
  }, [result]);

  const editRecommendation = useCallback(
    (index: number, text: string) => {
      setRecommendations((prev) => {
        const next = [...prev];
        next[index] = text;
        return next;
      });
      setModifiedIndices((prev) => {
        const next = new Set(prev);
        if (text === originalRecommendationsRef.current[index]) {
          next.delete(index);
        } else {
          next.add(index);
        }
        return next;
      });
    },
    [],
  );

  const resetRecommendation = useCallback(
    (index: number) => {
      const original = originalRecommendationsRef.current[index] ?? "";
      setRecommendations((prev) => {
        const next = [...prev];
        next[index] = original;
        return next;
      });
      setModifiedIndices((prev) => {
        const next = new Set(prev);
        next.delete(index);
        return next;
      });
    },
    [],
  );

  // Guard against null result AND against the brief first-render window before the
  // initialization effect fires (recommendations state starts as []).
  if (!aiResult || recommendations.length === 0) {
    return null;
  }

  return {
    recommendations,
    originalRecommendations: originalRecommendationsRef.current,
    modifiedIndices,
    editRecommendation,
    resetRecommendation,
  };
}

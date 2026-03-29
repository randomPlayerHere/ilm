import { useCallback, useEffect, useRef, useState } from "react";
import type { GradingJobWithResultResponse } from "@ilm/contracts";
import { getAuthData } from "../../../services/token-storage";
import { approveGradingJob } from "../../../services/grading-service";
import type { GradingReviewControls } from "./useGradingReview";
import type { PracticeRecommendationsControls } from "./usePracticeRecommendations";

export interface GradeApprovalControls {
  approve: () => void;
  isApproving: boolean;
  isApproved: boolean;
  approvalError: string | null;
}

type ApprovalState = "idle" | "loading" | "approved" | "error";

export function useGradeApproval(
  result: GradingJobWithResultResponse | null,
  reviewControls: GradingReviewControls | null,
  practiceRecommendationsControls?: PracticeRecommendationsControls | null,
): GradeApprovalControls | null {
  const [approvalState, setApprovalState] = useState<ApprovalState>("idle");
  const [isApproved, setIsApproved] = useState<boolean>(result?.is_approved ?? false);
  const [approvalError, setApprovalError] = useState<string | null>(null);

  const isMountedRef = useRef(true);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Re-initialize isApproved when result changes
  useEffect(() => {
    setIsApproved(result?.is_approved ?? false);
    setApprovalState("idle");
    setApprovalError(null);
  }, [result?.job_id, result?.is_approved]);

  const approve = useCallback(async () => {
    if (result === null || reviewControls === null) return;

    // Set loading for isApproving; set isApproved optimistically for UI
    setApprovalState("loading");
    setIsApproved(true);
    setApprovalError(null);

    const authData = await getAuthData();
    if (!isMountedRef.current) return;

    if (authData === null) {
      setApprovalState("error");
      setIsApproved(false);
      setApprovalError("Session expired — please sign in again");
      return;
    }

    try {
      await approveGradingJob(
        result.assignment_id,
        result.job_id,
        String(reviewControls.scoreValue),
        reviewControls.feedbackValue,
        authData.token,
        practiceRecommendationsControls?.recommendations ?? [],
      );
      if (!isMountedRef.current) return;
      setApprovalState("approved");
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      const message = err instanceof Error ? err.message : "Approval failed";
      setApprovalState("error");
      setIsApproved(false);
      setApprovalError(message);
    }
  }, [result, reviewControls, practiceRecommendationsControls]);

  if (result === null) return null;

  return {
    approve,
    isApproving: approvalState === "loading",
    isApproved,
    approvalError,
  };
}

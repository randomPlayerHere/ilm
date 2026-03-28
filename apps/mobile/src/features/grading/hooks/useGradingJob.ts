import { useCallback, useEffect, useRef, useState } from "react";
import type { GradingJobWithResultResponse } from "@ilm/contracts";
import { ApiError } from "../../../services/api-client";
import { getAuthData } from "../../../services/token-storage";
import { clearPendingCapture, getPendingCapture } from "../pending-capture-store";
import {
  createAssignment,
  getGradingJob,
  submitGradingJob,
  uploadArtifact,
} from "../../../services/grading-service";

export type GradingJobStatus = "idle" | "uploading" | "processing" | "completed" | "failed";

export interface GradingJobState {
  status: GradingJobStatus;
  result: GradingJobWithResultResponse | null;
  error: string | null;
  photoUri: string | null;
  retrying: boolean;
}

export function useGradingJob(classId: string, studentId: string, assignmentId?: string): GradingJobState {
  const [state, setState] = useState<GradingJobState>({
    status: "idle",
    result: null,
    error: null,
    photoUri: null,
    retrying: false,
  });

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);
  const isMountedRef = useRef(true);

  const scheduleNextPoll = useCallback(
    (assignmentId: string, jobId: string, token: string) => {
      timerRef.current = setTimeout(async () => {
        if (!isMountedRef.current) return;
        attemptRef.current += 1;
        if (attemptRef.current > 30) {
          setState((s) => ({ ...s, status: "failed", error: "Request timed out" }));
          return;
        }
        try {
          const job = await getGradingJob(assignmentId, jobId, token);
          if (!isMountedRef.current) return;
          if (job.status === "completed" || job.status === "failed") {
            setState((s) => ({
              ...s,
              status: job.status as "completed" | "failed",
              result: job,
              retrying: false,
              error: job.status === "failed"
                ? (job.failure_reason ?? "AI grading did not complete — please try again.")
                : null,
            }));
          } else {
            if (job.attempt_count > 1) {
              setState((s) => ({ ...s, retrying: true }));
            }
            scheduleNextPoll(assignmentId, jobId, token);
          }
        } catch (err: unknown) {
          if (!isMountedRef.current) return;
          attemptRef.current += 1;
          if (attemptRef.current > 30) {
            setState((s) => ({ ...s, status: "failed", error: "Request timed out" }));
            return;
          }
          // 4xx errors are fatal — retrying with the same credentials won't recover
          if (err instanceof ApiError && err.status >= 400 && err.status < 500) {
            setState((s) => ({ ...s, status: "failed", error: err.message }));
            return;
          }
          scheduleNextPoll(assignmentId, jobId, token);
        }
      }, 2000);
    },
    [],
  );

  useEffect(() => {
    isMountedRef.current = true;

    async function run() {
      // 1. Get auth token
      const authData = await getAuthData();
      if (!authData) {
        setState({
          status: "failed",
          result: null,
          error: "Session expired — please sign in again",
          photoUri: null,
        });
        return;
      }
      const token = authData.token;

      // 2. Read pending capture
      const pendingCapture = getPendingCapture();
      if (!pendingCapture) {
        setState({
          status: "failed",
          result: null,
          error: "No photo available for grading",
          photoUri: null,
        });
        return;
      }
      const photoUri = pendingCapture.compressedUri;

      // Set initial state with photoUri
      setState({ status: "uploading", result: null, error: null, photoUri, retrying: false });

      try {
        // 3. Create assignment (skip if assignmentId provided — retake flow reuses existing)
        const title = `Assignment ${new Date().toLocaleDateString()}`;
        const assignment_id = assignmentId ?? (await createAssignment(classId, title, token)).assignment_id;
        if (!isMountedRef.current) return;

        // 4. Upload artifact
        const { artifact_id } = await uploadArtifact(assignment_id, studentId, photoUri, token);
        if (!isMountedRef.current) return;

        // 5. Submit grading job
        const gradingJob = await submitGradingJob(assignment_id, artifact_id, token);
        if (!isMountedRef.current) return;

        // 6. Clear pending capture after successful upload and job submission
        clearPendingCapture();

        // 7. Start polling
        setState((s) => ({ ...s, status: "processing" }));
        scheduleNextPoll(assignment_id, gradingJob.job_id, token);
      } catch (err: unknown) {
        if (!isMountedRef.current) return;
        const message = err instanceof Error ? err.message : "An unexpected error occurred";
        setState((s) => ({ ...s, status: "failed", error: message }));
      }
    }

    run();

    return () => {
      isMountedRef.current = false;
      if (timerRef.current !== null) clearTimeout(timerRef.current);
    };
  }, [classId, studentId, assignmentId, scheduleNextPoll]);

  return state;
}

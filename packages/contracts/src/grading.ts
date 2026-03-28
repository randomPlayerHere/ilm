// Grading domain contract types
// Generated from OpenAPI 3.1 — Story 5.1

export interface AIGradingResultResponse {
  proposed_score: string;
  rubric_mapping: Record<string, string>;
  draft_feedback: string;
  generated_at: string;
  confidence_level: "high" | "medium" | "low";
  confidence_score: number;           // 0.0 – 1.0
  confidence_reason: string | null;   // present for non-high confidence
  practice_recommendations: string[];
}

export interface GradingJobResponse {
  job_id: string;
  artifact_id: string;
  assignment_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  attempt_count: number;
  submitted_at: string;
  completed_at: string | null;
}

export interface GradingJobWithResultResponse extends GradingJobResponse {
  result: AIGradingResultResponse | null;
  is_approved: boolean;
}

export interface GradeApprovalResponse {
  job_id: string;
  approved_score: string;
  approved_feedback: string;
  approver_user_id: string;
  approved_at: string;
  version: number;
}

export type AIConfidenceLevel = "high" | "medium" | "low";

export type AIGradingErrorCode =
  | "IMAGE_BLURRY"
  | "IMAGE_UNREADABLE"
  | "MODEL_TIMEOUT"
  | "MODEL_ERROR"
  | "RATE_LIMITED";

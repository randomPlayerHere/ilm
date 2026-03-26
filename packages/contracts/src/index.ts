/**
 * @ilm/contracts — Shared TypeScript types generated from OpenAPI specs.
 * Types will be added as API contracts are formalized.
 */

/** API response envelope */
export interface ApiResponse<T> {
  data: T;
  meta?: Record<string, unknown>;
}

/** API error envelope */
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string;
  };
}

/** Auth contracts */
export type { UserRole, LoginRequest, LoginResponse, GoogleLoginRequest } from "./auth";

/** Onboarding contracts */
export type {
  ClassCreateRequest,
  ClassResponse,
  ClassListResponse,
  StudentCreateRequest,
  StudentResponse,
  RosterResponse,
  CsvImportRowResult,
  CsvImportResponse,
  InviteLinkResponse,
  InviteLinkResolveResponse,
  JoinCodeRequest,
  JoinCodeResponse,
  GuardianStudentLinkResponse,
  LinkedChildResponse,
  LinkedChildrenResponse,
} from "./onboarding";

/** Grading contracts */
export type {
  AIGradingResultResponse,
  GradingJobResponse,
  GradingJobWithResultResponse,
  GradeApprovalResponse,
  AIConfidenceLevel,
  AIGradingErrorCode,
} from "./grading";

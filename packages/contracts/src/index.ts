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

/** User roles */
export type UserRole = "admin" | "principal" | "teacher" | "parent" | "student";

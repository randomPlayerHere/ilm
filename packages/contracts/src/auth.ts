/** User roles — defined here to avoid circular dependency with index.ts */
export type UserRole = "admin" | "principal" | "teacher" | "parent" | "student";

/** Request body for POST /auth/login */
export interface LoginRequest {
  email: string;
  password: string;
}

/** Request body for POST /auth/google */
export interface GoogleLoginRequest {
  id_token: string;
}

/** Response from POST /auth/login */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  role: UserRole;
  org_id: string;
  home_path: string;
}

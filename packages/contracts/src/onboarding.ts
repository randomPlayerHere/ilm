/** POST /onboarding/classes request body */
export interface ClassCreateRequest {
  name: string;
  subject: string;
}

/** Class resource */
export interface ClassResponse {
  class_id: string;
  org_id: string;
  teacher_user_id: string;
  name: string;
  subject: string;
  join_code: string;
  student_count: number;
  created_at: string;
}

export interface ClassListResponse {
  classes: ClassResponse[];
}

/** POST /onboarding/classes/{classId}/students request body */
export interface StudentCreateRequest {
  name: string;
  grade_level: string;
}

export interface StudentResponse {
  student_id: string;
  name: string;
  grade_level: string;
  org_id: string;
  created_at: string;
}

export interface RosterResponse {
  class_id: string;
  students: StudentResponse[];
}

export interface CsvImportRowResult {
  row: number;
  success: boolean;
  student_name: string | null;
  error: string | null;
}

export interface CsvImportResponse {
  total_rows: number;
  successful: number;
  failed: number;
  results: CsvImportRowResult[];
}

export interface InviteLinkResponse {
  invite_id: string;
  token: string;
  url: string;         // "ilm://invite/{token}"
  student_id: string;
  expires_at: string;
}

export interface InviteLinkResolveResponse {
  valid: boolean;
  reason: string | null;    // "already_used" | "expired" | null
  student_name: string | null;
  class_name: string | null;
  subject: string | null;
}

export interface JoinCodeRequest {
  join_code: string;
}

export interface JoinCodeResponse {
  class_id: string;
  class_name: string;
  subject: string;
}

export interface GuardianStudentLinkResponse {
  link_id: string;
  student_id: string;
  student_name: string;
}

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

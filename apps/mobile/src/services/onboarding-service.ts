import type {
  ClassCreateRequest,
  ClassListResponse,
  ClassResponse,
  CsvImportResponse,
  JoinCodeRequest,
  JoinCodeResponse,
  RosterResponse,
  StudentCreateRequest,
  StudentResponse,
} from "@ilm/contracts";
import { API_BASE_URL, ApiError, apiRequest } from "./api-client";

export class ClassNotFoundError extends Error {
  name = "ClassNotFoundError" as const;
}

export class ClassAccessError extends Error {
  name = "ClassAccessError" as const;
}

export async function createClass(
  token: string,
  data: ClassCreateRequest,
): Promise<ClassResponse> {
  try {
    return await apiRequest<ClassResponse>("/onboarding/classes", {
      method: "POST",
      body: data,
      token,
    });
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 403:
          throw new ClassAccessError("You don't have permission to manage this class.");
        case 404:
          throw new ClassNotFoundError("Class not found.");
      }
    }
    throw error;
  }
}

export async function listClasses(token: string): Promise<ClassListResponse> {
  return apiRequest<ClassListResponse>("/onboarding/classes", { token });
}

export async function getRoster(token: string, classId: string): Promise<RosterResponse> {
  try {
    return await apiRequest<RosterResponse>(`/onboarding/classes/${classId}/roster`, { token });
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 403:
          throw new ClassAccessError("You don't have permission to view this class.");
        case 404:
          throw new ClassNotFoundError("Class not found.");
      }
    }
    throw error;
  }
}

export async function addStudent(
  token: string,
  classId: string,
  data: StudentCreateRequest,
): Promise<StudentResponse> {
  try {
    return await apiRequest<StudentResponse>(`/onboarding/classes/${classId}/students`, {
      method: "POST",
      body: data,
      token,
    });
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 403:
          throw new ClassAccessError("You don't have permission to manage this class.");
        case 404:
          throw new ClassNotFoundError("Class not found.");
      }
    }
    throw error;
  }
}

export async function removeStudent(
  token: string,
  classId: string,
  studentId: string,
): Promise<void> {
  try {
    await apiRequest(`/onboarding/classes/${classId}/students/${studentId}`, {
      method: "DELETE",
      token,
    });
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 403:
          throw new ClassAccessError("You don't have permission to manage this class.");
        case 404:
          throw new ClassNotFoundError("Class or student not found.");
      }
    }
    throw error;
  }
}

export class InvalidJoinCodeError extends Error {
  name = "InvalidJoinCodeError" as const;
}

export class AlreadyEnrolledError extends Error {
  name = "AlreadyEnrolledError" as const;
}

export async function joinClassByCode(
  token: string,
  joinCode: string,
): Promise<JoinCodeResponse> {
  const body: JoinCodeRequest = { join_code: joinCode.toUpperCase().trim() };
  try {
    return await apiRequest<JoinCodeResponse>("/onboarding/join", {
      method: "POST",
      body,
      token,
    });
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 404:
          throw new InvalidJoinCodeError("Invalid or expired join code.");
        case 409:
          throw new AlreadyEnrolledError("You are already enrolled in this class.");
      }
    }
    throw error;
  }
}

export async function importStudentsCsv(
  token: string,
  classId: string,
  fileUri: string,
  fileName: string,
): Promise<CsvImportResponse> {
  const formData = new FormData();
  formData.append("file", {
    uri: fileUri,
    name: fileName,
    type: "text/csv",
  } as unknown as Blob);

  const response = await fetch(
    `${API_BASE_URL}/onboarding/classes/${classId}/students/import`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    },
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), err.detail ?? "Import failed", response.status);
  }
  return response.json() as Promise<CsvImportResponse>;
}

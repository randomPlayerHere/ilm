import type {
  GradeApprovalResponse,
  GradingJobResponse,
  GradingJobWithResultResponse,
  ManualGradeResponse,
} from "@ilm/contracts";
import { API_BASE_URL, ApiError } from "./api-client";

export async function createAssignment(
  classId: string,
  title: string,
  token: string,
): Promise<{ assignment_id: string }> {
  const response = await fetch(`${API_BASE_URL}/grading/assignments`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ class_id: classId, title }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "Create assignment failed", response.status);
  }
  return response.json();
}

export async function uploadArtifact(
  assignmentId: string,
  studentId: string,
  compressedUri: string,
  token: string,
): Promise<{ artifact_id: string }> {
  const formData = new FormData();
  formData.append("student_id", studentId);
  formData.append("file", {
    uri: compressedUri,
    type: "image/jpeg",
    name: "assignment.jpg",
  } as any); // React Native FormData accepts {uri, type, name} objects

  const response = await fetch(
    `${API_BASE_URL}/grading/assignments/${assignmentId}/artifacts`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        // Do NOT set Content-Type — let fetch set multipart boundary automatically
      },
      body: formData,
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "Upload failed", response.status);
  }
  return response.json();
}

export async function submitGradingJob(
  assignmentId: string,
  artifactId: string,
  token: string,
): Promise<GradingJobResponse> {
  const response = await fetch(
    `${API_BASE_URL}/grading/assignments/${assignmentId}/grading-jobs`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ artifact_id: artifactId }),
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "Submit grading job failed", response.status);
  }
  return response.json();
}

export async function approveGradingJob(
  assignmentId: string,
  jobId: string,
  approvedScore: string,
  approvedFeedback: string,
  token: string,
): Promise<GradeApprovalResponse> {
  const response = await fetch(
    `${API_BASE_URL}/grading/assignments/${assignmentId}/grading-jobs/${jobId}/approve`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ approved_score: approvedScore, approved_feedback: approvedFeedback }),
    },
  );
  if (response.status === 409) {
    try { response.body?.cancel(); } catch { /* ignore — body drain is best-effort */ }
    return {} as GradeApprovalResponse;
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "Approve grading job failed", response.status);
  }
  return response.json();
}

export async function submitManualGrade(
  assignmentId: string,
  jobId: string,
  score: string,
  feedback: string,
  token: string,
): Promise<ManualGradeResponse> {
  const response = await fetch(
    `${API_BASE_URL}/grading/assignments/${assignmentId}/grading-jobs/${jobId}/manual-grade`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ score, feedback }),
    },
  );
  if (response.status === 409) {
    try { response.body?.cancel(); } catch { /* ignore — body drain is best-effort */ }
    return {} as ManualGradeResponse;
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "Submit manual grade failed", response.status);
  }
  return response.json();
}

export async function getGradingJob(
  assignmentId: string,
  jobId: string,
  token: string,
): Promise<GradingJobWithResultResponse> {
  const response = await fetch(
    `${API_BASE_URL}/grading/assignments/${assignmentId}/grading-jobs/${jobId}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "Get grading job failed", response.status);
  }
  return response.json();
}

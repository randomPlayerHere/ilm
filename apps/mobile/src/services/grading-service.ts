import type {
  ArtifactDownloadUrlResponse,
  ArtifactRegisterRequest,
  AssignmentListResponse,
  GradeApprovalResponse,
  GradingJobResponse,
  GradingJobWithResultResponse,
  ManualGradeRequest,
  ManualGradeResponse,
} from "@ilm/contracts";

interface ArtifactSummary {
  artifact_id: string;
  file_name: string;
  media_type: string;
  created_at: string;
}
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
  practiceRecommendations: string[] = [],
): Promise<GradeApprovalResponse> {
  const response = await fetch(
    `${API_BASE_URL}/grading/assignments/${assignmentId}/grading-jobs/${jobId}/approve`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ approved_score: approvedScore, approved_feedback: approvedFeedback, practice_recommendations: practiceRecommendations }),
    },
  );
  if (response.status === 409) {
    try { response.body?.cancel(); } catch { /* ignore — body drain is best-effort */ }
    return { job_id: '', approved_score: '', approved_feedback: '', approver_user_id: '', approved_at: '', version: 0, practice_recommendations: [] };
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
      body: JSON.stringify({ score, feedback } satisfies ManualGradeRequest),
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

export async function getPresignedUploadUrl(
  classId: string,
  studentId: string,
  assignmentId: string,
  filename: string,
  token: string,
): Promise<{ url: string; key: string }> {
  const response = await fetch(`${API_BASE_URL}/v1/storage/presigned-url`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      filename,
      class_id: classId,
      student_id: studentId,
      assignment_id: assignmentId,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "Failed to get upload URL", response.status);
  }
  return response.json();
}

export async function uploadToPresignedUrl(
  presignedUrl: string,
  localUri: string,
): Promise<void> {
  // Fetch the local file as a blob then PUT it directly to S3/MinIO.
  // No Authorization header — pre-signed URLs are already authorized.
  const fileResponse = await fetch(localUri);
  if (!fileResponse.ok) {
    throw new Error("Failed to read local photo file for upload");
  }
  const blob = await fileResponse.blob();
  const uploadResponse = await fetch(presignedUrl, {
    method: "PUT",
    headers: { "Content-Type": "image/jpeg" },
    body: blob,
  });
  if (!uploadResponse.ok) {
    throw new Error(`S3 upload failed with status ${uploadResponse.status}`);
  }
}

export async function registerArtifact(
  assignmentId: string,
  storageKey: string,
  studentId: string,
  fileName: string,
  mediaType: string,
  token: string,
): Promise<{ artifact_id: string }> {
  const body: ArtifactRegisterRequest = {
    student_id: studentId,
    storage_key: storageKey,
    file_name: fileName,
    media_type: mediaType,
  };
  const response = await fetch(
    `${API_BASE_URL}/grading/assignments/${assignmentId}/artifacts/register`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) {
    const responseBody = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), responseBody.detail ?? "Register artifact failed", response.status);
  }
  return response.json();
}

export async function listAssignments(
  classId: string,
  token: string,
): Promise<AssignmentListResponse> {
  const response = await fetch(
    `${API_BASE_URL}/grading/assignments?class_id=${encodeURIComponent(classId)}`,
    {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "List assignments failed", response.status);
  }
  return response.json();
}

export async function listArtifacts(
  assignmentId: string,
  token: string,
): Promise<ArtifactSummary[]> {
  const response = await fetch(
    `${API_BASE_URL}/grading/assignments/${assignmentId}/artifacts`,
    {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "List artifacts failed", response.status);
  }
  const data = await response.json();
  return data.artifacts as ArtifactSummary[];
}

export async function getArtifactGradingJob(
  assignmentId: string,
  artifactId: string,
  token: string,
): Promise<GradingJobWithResultResponse | null> {
  const response = await fetch(
    `${API_BASE_URL}/grading/assignments/${assignmentId}/artifacts/${artifactId}/grading-job`,
    {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (response.status === 404) return null;
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "Get artifact grading job failed", response.status);
  }
  return response.json();
}

export async function getGradeApproval(
  assignmentId: string,
  jobId: string,
  token: string,
): Promise<GradeApprovalResponse | null> {
  const response = await fetch(
    `${API_BASE_URL}/grading/assignments/${assignmentId}/grading-jobs/${jobId}/approval`,
    {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (response.status === 403) return null; // not yet approved
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "Get grade approval failed", response.status);
  }
  return response.json();
}

export async function getArtifactDownloadUrl(
  assignmentId: string,
  artifactId: string,
  token: string,
): Promise<ArtifactDownloadUrlResponse> {
  const response = await fetch(
    `${API_BASE_URL}/grading/assignments/${assignmentId}/artifacts/${artifactId}/download-url`,
    {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(String(response.status), body.detail ?? "Get download URL failed", response.status);
  }
  return response.json();
}

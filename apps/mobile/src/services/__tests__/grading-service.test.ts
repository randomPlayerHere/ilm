import {
  createAssignment,
  getGradingJob,
  submitGradingJob,
  uploadArtifact,
} from "../grading-service";
import { ApiError } from "../api-client";

// Mock fetch globally — React Native test env has no fetch polyfill
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock expo-constants so API_BASE_URL resolves in test env
jest.mock("expo-constants", () => ({
  default: { expoConfig: { extra: { apiBaseUrl: "http://localhost:8000" } } },
}));

const TOKEN = "fake-token";

function mockOkResponse(body: unknown) {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve(body),
  } as Response);
}

function mockErrorResponse(status: number, detail: string) {
  mockFetch.mockResolvedValueOnce({
    ok: false,
    status,
    json: () => Promise.resolve({ detail }),
  } as unknown as Response);
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe("createAssignment", () => {
  it("sends correct JSON body and returns assignment_id", async () => {
    mockOkResponse({ assignment_id: "asgn_1" });
    const result = await createAssignment("cls_1", "Test Assignment", TOKEN);
    expect(result).toEqual({ assignment_id: "asgn_1" });
    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/grading/assignments",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ class_id: "cls_1", title: "Test Assignment" }),
      }),
    );
  });

  it("throws ApiError on non-2xx response", async () => {
    mockErrorResponse(403, "Forbidden");
    await expect(createAssignment("cls_1", "Test", TOKEN)).rejects.toBeInstanceOf(ApiError);
  });
});

describe("uploadArtifact", () => {
  it("sends FormData with student_id field and file blob", async () => {
    // Spy on FormData.prototype.append to track what was appended
    const appendSpy = jest.spyOn(FormData.prototype, "append");
    mockOkResponse({ artifact_id: "art_1" });

    const result = await uploadArtifact("asgn_1", "stu_demo_1", "file://test.jpg", TOKEN);
    expect(result).toEqual({ artifact_id: "art_1" });

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe("http://localhost:8000/grading/assignments/asgn_1/artifacts");
    expect(opts.method).toBe("POST");
    // Content-Type must NOT be set (let fetch set multipart boundary)
    expect(opts.headers?.["Content-Type"]).toBeUndefined();
    expect(opts.headers?.["Authorization"]).toBe(`Bearer ${TOKEN}`);
    // Body is FormData
    expect(opts.body).toBeInstanceOf(FormData);

    // student_id field was appended
    expect(appendSpy).toHaveBeenCalledWith("student_id", "stu_demo_1");
    appendSpy.mockRestore();
  });

  it("FormData includes file field with uri, type, name", async () => {
    const appendSpy = jest.spyOn(FormData.prototype, "append");
    mockOkResponse({ artifact_id: "art_1" });

    await uploadArtifact("asgn_1", "stu_1", "file://photo.jpg", TOKEN);

    expect(appendSpy).toHaveBeenCalledWith(
      "file",
      expect.objectContaining({ uri: "file://photo.jpg", type: "image/jpeg", name: "assignment.jpg" }),
    );
    appendSpy.mockRestore();
  });

  it("throws ApiError on non-2xx response", async () => {
    mockErrorResponse(400, "Upload failed");
    await expect(uploadArtifact("asgn_1", "stu_1", "file://test.jpg", TOKEN)).rejects.toBeInstanceOf(ApiError);
  });
});

describe("submitGradingJob", () => {
  it("sends correct JSON body with artifact_id", async () => {
    const mockJob = {
      job_id: "job_1",
      artifact_id: "art_1",
      assignment_id: "asgn_1",
      status: "pending",
      attempt_count: 0,
      submitted_at: "",
      completed_at: null,
    };
    mockOkResponse(mockJob);
    const result = await submitGradingJob("asgn_1", "art_1", TOKEN);
    expect(result).toEqual(mockJob);
    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/grading/assignments/asgn_1/grading-jobs",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ artifact_id: "art_1" }),
      }),
    );
  });

  it("throws ApiError on non-2xx response", async () => {
    mockErrorResponse(422, "Unprocessable");
    await expect(submitGradingJob("asgn_1", "art_1", TOKEN)).rejects.toBeInstanceOf(ApiError);
  });
});

describe("getGradingJob", () => {
  it("hits correct GET URL", async () => {
    const mockJob = {
      job_id: "job_1",
      artifact_id: "art_1",
      assignment_id: "asgn_1",
      status: "completed",
      attempt_count: 1,
      submitted_at: "",
      completed_at: "",
      result: null,
      is_approved: false,
    };
    mockOkResponse(mockJob);
    const result = await getGradingJob("asgn_1", "job_1", TOKEN);
    expect(result).toEqual(mockJob);
    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/grading/assignments/asgn_1/grading-jobs/job_1",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("throws ApiError on non-2xx response", async () => {
    mockErrorResponse(404, "Not found");
    await expect(getGradingJob("asgn_1", "job_1", TOKEN)).rejects.toBeInstanceOf(ApiError);
  });
});

// --- Story 5.9 tests ---

import {
  getArtifactDownloadUrl,
  getArtifactGradingJob,
  getGradeApproval,
  getPresignedUploadUrl,
  listAssignments,
  listArtifacts,
  registerArtifact,
  uploadToPresignedUrl,
} from "../grading-service";

describe("getPresignedUploadUrl", () => {
  it("posts to presigned-url with scoped params and returns url + key", async () => {
    mockOkResponse({ url: "http://minio:9000/bucket/orgs/org1/cls1/stu1/asgn1/uuid.jpg?sig=abc", key: "orgs/org1/cls1/stu1/asgn1/uuid.jpg" });
    const result = await getPresignedUploadUrl("cls1", "stu1", "asgn1", "assignment.jpg", TOKEN);
    expect(result.url).toContain("minio");
    expect(result.key).toBe("orgs/org1/cls1/stu1/asgn1/uuid.jpg");
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe("http://localhost:8000/v1/storage/presigned-url");
    expect(opts.method).toBe("POST");
    const body = JSON.parse(opts.body);
    expect(body).toEqual({ filename: "assignment.jpg", class_id: "cls1", student_id: "stu1", assignment_id: "asgn1" });
  });

  it("throws ApiError on non-2xx response", async () => {
    mockErrorResponse(403, "Forbidden");
    await expect(getPresignedUploadUrl("cls1", "stu1", "asgn1", "photo.jpg", TOKEN)).rejects.toBeInstanceOf(ApiError);
  });
});

describe("uploadToPresignedUrl", () => {
  it("GETs the local file then PUTs to presigned URL without Authorization header", async () => {
    // First fetch: read local file
    mockFetch.mockResolvedValueOnce({ ok: true, blob: () => Promise.resolve(new Blob(["data"])) } as unknown as Response);
    // Second fetch: PUT to S3
    mockFetch.mockResolvedValueOnce({ ok: true } as Response);

    await uploadToPresignedUrl("http://minio:9000/bucket/key?sig=abc", "file://local/photo.jpg");

    const [localUrl] = mockFetch.mock.calls[0];
    expect(localUrl).toBe("file://local/photo.jpg");

    const [s3Url, s3Opts] = mockFetch.mock.calls[1];
    expect(s3Url).toBe("http://minio:9000/bucket/key?sig=abc");
    expect(s3Opts.method).toBe("PUT");
    expect(s3Opts.headers?.["Content-Type"]).toBe("image/jpeg");
    expect(s3Opts.headers?.["Authorization"]).toBeUndefined();
  });

  it("throws when local file read fails", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 } as Response);
    await expect(uploadToPresignedUrl("http://s3/key", "file://missing.jpg")).rejects.toThrow("Failed to read local photo file for upload");
  });

  it("throws when S3 PUT fails", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, blob: () => Promise.resolve(new Blob()) } as unknown as Response);
    mockFetch.mockResolvedValueOnce({ ok: false, status: 403 } as Response);
    await expect(uploadToPresignedUrl("http://s3/key", "file://photo.jpg")).rejects.toThrow("S3 upload failed");
  });
});

describe("registerArtifact", () => {
  it("posts storage_key and returns artifact_id", async () => {
    mockOkResponse({ artifact_id: "artf_1", assignment_id: "asgn_1", student_id: "stu_1", class_id: "cls_1", org_id: "org_1", teacher_user_id: "usr_1", file_name: "assignment.jpg", media_type: "image/jpeg", created_at: "" });
    const result = await registerArtifact("asgn_1", "orgs/org1/cls1/stu1/asgn1/uuid.jpg", "stu_1", "assignment.jpg", "image/jpeg", TOKEN);
    expect(result.artifact_id).toBe("artf_1");
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe("http://localhost:8000/grading/assignments/asgn_1/artifacts/register");
    expect(opts.method).toBe("POST");
    const body = JSON.parse(opts.body);
    expect(body.storage_key).toBe("orgs/org1/cls1/stu1/asgn1/uuid.jpg");
    expect(body.student_id).toBe("stu_1");
  });

  it("throws ApiError on non-2xx response", async () => {
    mockErrorResponse(403, "Forbidden");
    await expect(registerArtifact("asgn_1", "orgs/org1/k.jpg", "stu_1", "f.jpg", "image/jpeg", TOKEN)).rejects.toBeInstanceOf(ApiError);
  });
});

describe("listAssignments", () => {
  it("hits GET /grading/assignments?class_id= and returns assignments array", async () => {
    const mockData = { assignments: [{ assignment_id: "asgn_1", class_id: "cls_1", title: "Quiz 1", created_at: "", artifact_count: 2 }] };
    mockOkResponse(mockData);
    const result = await listAssignments("cls_1", TOKEN);
    expect(result.assignments).toHaveLength(1);
    expect(result.assignments[0].assignment_id).toBe("asgn_1");
    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("/grading/assignments?class_id=cls_1");
  });

  it("throws ApiError on non-2xx response", async () => {
    mockErrorResponse(403, "Forbidden");
    await expect(listAssignments("cls_1", TOKEN)).rejects.toBeInstanceOf(ApiError);
  });
});

describe("getArtifactDownloadUrl", () => {
  it("hits GET download-url endpoint and returns url", async () => {
    mockOkResponse({ url: "http://minio:9000/bucket/key?sig=xyz" });
    const result = await getArtifactDownloadUrl("asgn_1", "artf_1", TOKEN);
    expect(result.url).toContain("minio");
    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe("http://localhost:8000/grading/assignments/asgn_1/artifacts/artf_1/download-url");
  });

  it("throws ApiError on non-2xx response", async () => {
    mockErrorResponse(403, "Forbidden");
    await expect(getArtifactDownloadUrl("asgn_1", "artf_1", TOKEN)).rejects.toBeInstanceOf(ApiError);
  });
});

describe("listArtifacts", () => {
  it("returns artifact summaries for an assignment", async () => {
    mockOkResponse({ artifacts: [{ artifact_id: "artf_1", file_name: "photo.jpg", media_type: "image/jpeg", created_at: "" }] });
    const result = await listArtifacts("asgn_1", TOKEN);
    expect(result).toHaveLength(1);
    expect(result[0].artifact_id).toBe("artf_1");
    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe("http://localhost:8000/grading/assignments/asgn_1/artifacts");
  });

  it("throws ApiError on non-2xx response", async () => {
    mockErrorResponse(403, "Forbidden");
    await expect(listArtifacts("asgn_1", TOKEN)).rejects.toBeInstanceOf(ApiError);
  });
});

describe("getArtifactGradingJob", () => {
  it("returns grading job when found", async () => {
    const mockJob = { job_id: "job_1", artifact_id: "artf_1", assignment_id: "asgn_1", status: "completed", attempt_count: 1, submitted_at: "", completed_at: "", result: null, is_approved: false };
    mockOkResponse(mockJob);
    const result = await getArtifactGradingJob("asgn_1", "artf_1", TOKEN);
    expect(result?.job_id).toBe("job_1");
  });

  it("returns null on 404 (artifact not yet submitted for grading)", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404, json: () => Promise.resolve({}) } as unknown as Response);
    const result = await getArtifactGradingJob("asgn_1", "artf_1", TOKEN);
    expect(result).toBeNull();
  });

  it("throws ApiError on other errors", async () => {
    mockErrorResponse(403, "Forbidden");
    await expect(getArtifactGradingJob("asgn_1", "artf_1", TOKEN)).rejects.toBeInstanceOf(ApiError);
  });
});

describe("getGradeApproval", () => {
  it("returns approval when found", async () => {
    mockOkResponse({ job_id: "job_1", approved_score: "90/100", approved_feedback: "Good work", approver_user_id: "usr_1", approved_at: "", version: 1, practice_recommendations: [] });
    const result = await getGradeApproval("asgn_1", "job_1", TOKEN);
    expect(result?.approved_score).toBe("90/100");
  });

  it("returns null on 403 (not yet approved)", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 403, json: () => Promise.resolve({}) } as unknown as Response);
    const result = await getGradeApproval("asgn_1", "job_1", TOKEN);
    expect(result).toBeNull();
  });

  it("throws ApiError on 500 errors", async () => {
    mockErrorResponse(500, "Server error");
    await expect(getGradeApproval("asgn_1", "job_1", TOKEN)).rejects.toBeInstanceOf(ApiError);
  });
});

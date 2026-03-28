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

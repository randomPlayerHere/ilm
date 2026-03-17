from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class AssignmentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    class_id: Annotated[str, StringConstraints(min_length=3, max_length=64)]
    title: Annotated[str, StringConstraints(min_length=3, max_length=200)]


class AssignmentResponse(BaseModel):
    assignment_id: str
    class_id: str
    org_id: str
    teacher_user_id: str
    title: str
    created_at: str


class ArtifactResponse(BaseModel):
    artifact_id: str
    assignment_id: str
    student_id: str
    class_id: str
    org_id: str
    teacher_user_id: str
    file_name: str
    media_type: str
    # Stub S3 key (e.g. "s3://stub/artf_1"). Story 2.4 must replace this with a
    # presigned URL accessor and never expose raw bucket paths in production responses.
    storage_key: str
    created_at: str


class ArtifactListResponse(BaseModel):
    artifacts: list[ArtifactResponse]


class GradingJobSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: Annotated[str, StringConstraints(min_length=3, max_length=64)]


class GradingJobResponse(BaseModel):
    job_id: str
    artifact_id: str
    assignment_id: str
    status: str
    attempt_count: int
    submitted_at: str
    completed_at: str | None


class GradingResultResponse(BaseModel):
    proposed_score: str
    rubric_mapping: dict[str, str]
    draft_feedback: str
    generated_at: str


class GradingJobWithResultResponse(BaseModel):
    job_id: str
    artifact_id: str
    assignment_id: str
    status: str
    attempt_count: int
    submitted_at: str
    completed_at: str | None
    result: GradingResultResponse | None

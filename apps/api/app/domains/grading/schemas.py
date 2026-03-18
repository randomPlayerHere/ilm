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
    is_approved: bool


class GradeApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved_score: Annotated[str, StringConstraints(min_length=1, max_length=50)]
    approved_feedback: Annotated[str, StringConstraints(min_length=1, max_length=2000)]


class GradeApprovalResponse(BaseModel):
    job_id: str
    approved_score: str
    approved_feedback: str
    approver_user_id: str
    approved_at: str
    version: int


class GradeVersionResponse(BaseModel):
    job_id: str
    version: int
    approved_score: str
    approved_feedback: str
    editor_user_id: str
    edited_at: str
    is_approved: bool


class GradeVersionListResponse(BaseModel):
    versions: list[GradeVersionResponse]


class RecommendationTopicItem(BaseModel):
    topic: str
    suggestion: str
    weakness_signal: str


class RecommendationTopicItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    suggestion: Annotated[str, StringConstraints(min_length=1, max_length=1000)]


class RecommendationJobResponse(BaseModel):
    rec_job_id: str
    job_id: str
    assignment_id: str
    student_id: str
    status: str
    attempt_count: int
    submitted_at: str
    completed_at: str | None


class RecommendationResultResponse(BaseModel):
    rec_job_id: str
    topics: list[RecommendationTopicItem]
    generated_at: str


class RecommendationJobWithResultResponse(BaseModel):
    rec_job_id: str
    job_id: str
    assignment_id: str
    student_id: str
    status: str
    attempt_count: int
    submitted_at: str
    completed_at: str | None
    result: RecommendationResultResponse | None
    is_confirmed: bool


class ConfirmRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topics: list[RecommendationTopicItemRequest]


class ConfirmedRecommendationResponse(BaseModel):
    rec_job_id: str
    job_id: str
    student_id: str
    topics: list[RecommendationTopicItem]
    confirmed_by: str
    confirmed_at: str

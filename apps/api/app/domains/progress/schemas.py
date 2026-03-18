from __future__ import annotations

from pydantic import BaseModel


class ApprovedGradeResponse(BaseModel):
    job_id: str
    artifact_id: str
    assignment_id: str
    assignment_title: str
    student_id: str
    approved_score: str
    approved_feedback: str
    approved_at: str
    approver_user_id: str
    version: int


class ApprovedGradeListResponse(BaseModel):
    grades: list[ApprovedGradeResponse]


class ConfirmedRecommendationResponse(BaseModel):
    rec_job_id: str
    job_id: str
    student_id: str
    topics: list[dict[str, str]]
    confirmed_by: str
    confirmed_at: str


class ConfirmedRecommendationListResponse(BaseModel):
    recommendations: list[ConfirmedRecommendationResponse]

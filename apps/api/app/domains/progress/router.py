from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.domains.auth.dependencies import ActorContext, require_authenticated_actor
from app.domains.grading.repository import InMemoryGradingRepository
from app.domains.progress.schemas import (
    ApprovedGradeListResponse,
    ApprovedGradeResponse,
    ConfirmedRecommendationListResponse,
    ConfirmedRecommendationResponse,
    TopicInsightListResponse,
    TopicInsightResponse,
)
from app.domains.students.repository import InMemoryStudentsRepository

router = APIRouter(prefix="/progress", tags=["progress"])

_grading_repo = InMemoryGradingRepository()
_students_repo = InMemoryStudentsRepository()


def reset_progress_state_for_tests() -> None:
    InMemoryGradingRepository.reset_state()
    InMemoryStudentsRepository.reset_state()


def _require_parent_or_student(
    actor: ActorContext,
    student_id: str,
    students_repo: InMemoryStudentsRepository,
    grading_repo: InMemoryGradingRepository,
) -> None:
    if actor.role == "student":
        if actor.user_id != student_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        # Org isolation: verify student context is in actor.org_id
        student_ctx = grading_repo.get_student_context(student_id)
        if student_ctx is None or student_ctx.org_id != actor.org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    elif actor.role == "parent":
        links = students_repo.get_links_for_guardian(actor.user_id, actor.org_id)
        if not any(link.student_id == student_id for link in links):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        # Org isolation: verify student is in actor's org (defense-in-depth)
        student_ctx = grading_repo.get_student_context(student_id)
        if student_ctx is None or student_ctx.org_id != actor.org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get(
    "/students/{student_id}/grades",
    response_model=ApprovedGradeListResponse,
)
async def get_student_grades(
    student_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> ApprovedGradeListResponse:
    _require_parent_or_student(actor, student_id, _students_repo, _grading_repo)
    records = _grading_repo.list_approved_grades_for_student(student_id, actor.org_id)
    grades = [
        ApprovedGradeResponse(
            job_id=r.job_id,
            artifact_id=r.artifact_id,
            assignment_id=r.assignment_id,
            assignment_title=r.assignment_title,
            student_id=r.student_id,
            approved_score=r.approved_score,
            approved_feedback=r.approved_feedback,
            approved_at=r.approved_at,
            approver_user_id=r.approver_user_id,
            version=r.version,
            practice_recommendations=r.practice_recommendations,
        )
        for r in records
    ]
    return ApprovedGradeListResponse(grades=grades)


@router.get(
    "/students/{student_id}/recommendations",
    response_model=ConfirmedRecommendationListResponse,
)
async def get_student_recommendations(
    student_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> ConfirmedRecommendationListResponse:
    _require_parent_or_student(actor, student_id, _students_repo, _grading_repo)
    records = _grading_repo.list_confirmed_recommendations_for_student(student_id, actor.org_id)
    recommendations = [
        ConfirmedRecommendationResponse(
            rec_job_id=r.rec_job_id,
            job_id=r.job_id,
            student_id=r.student_id,
            topics=r.topics,
            confirmed_by=r.confirmed_by,
            confirmed_at=r.confirmed_at,
        )
        for r in records
    ]
    return ConfirmedRecommendationListResponse(recommendations=recommendations)


@router.get(
    "/students/{student_id}/topic-insights",
    response_model=TopicInsightListResponse,
)
async def get_student_topic_insights(
    student_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> TopicInsightListResponse:
    _require_parent_or_student(actor, student_id, _students_repo, _grading_repo)
    insights, has_sufficient_data = _grading_repo.list_topic_insights_for_student(
        student_id, actor.org_id
    )
    return TopicInsightListResponse(
        topic_insights=[
            TopicInsightResponse(
                topic=i.topic,
                status=i.status,
                weakness_signal=i.weakness_signal,
                guidance=i.guidance,
                rec_job_id=i.rec_job_id,
                confirmed_at=i.confirmed_at,
            )
            for i in insights
        ],
        has_sufficient_data=has_sufficient_data,
    )

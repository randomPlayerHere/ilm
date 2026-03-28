from __future__ import annotations

import logging
import os

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.domains.auth.dependencies import ActorContext, require_authenticated_actor
from app.domains.grading.ai_provider import (
    AIGradingProvider,
    MockAIGradingProvider,
    NonMockAIGradingProvider,
)
from app.domains.grading.repository import InMemoryGradingRepository
from app.domains.grading.schemas import (
    ArtifactListResponse,
    ArtifactResponse,
    AssignmentCreateRequest,
    AssignmentResponse,
    ConfirmRecommendationRequest,
    ConfirmedRecommendationResponse,
    GradeApprovalRequest,
    GradeApprovalResponse,
    GradeVersionListResponse,
    GradeVersionResponse,
    GradingJobResponse,
    GradingJobSubmitRequest,
    GradingJobWithResultResponse,
    GradingResultResponse,
    RecommendationJobResponse,
    RecommendationJobWithResultResponse,
    RecommendationResultResponse,
    RecommendationTopicItem,
)
from app.domains.grading.service import (
    Artifact,
    ArtifactFormatError,
    Assignment,
    ConfirmedRecommendation,
    GradeApproval,
    GradeVersion,
    GradingAccessError,
    GradingJob,
    GradingJobWithResult,
    GradingService,
    GradingStateError,
    RecommendationJob,
    RecommendationJobWithResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/grading", tags=["grading"])


def _make_ai_provider() -> AIGradingProvider:
    # AI_MOCK_MODE defaults to "true" for local development
    mock_mode = os.environ.get("AI_MOCK_MODE", "true").lower()
    if mock_mode == "true":
        return MockAIGradingProvider()
    return NonMockAIGradingProvider()


_grading_service = GradingService(
    repository=InMemoryGradingRepository(),
    ai_provider=_make_ai_provider(),
)


async def get_grading_service() -> GradingService:
    return _grading_service


def reset_grading_state_for_tests() -> None:
    InMemoryGradingRepository.reset_state()
    MockAIGradingProvider.reset()  # prevents mock scenario state from bleeding across tests


def _require_teacher(actor: ActorContext) -> None:
    if actor.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _to_assignment_response(assignment: Assignment) -> AssignmentResponse:
    return AssignmentResponse(
        assignment_id=assignment.assignment_id,
        class_id=assignment.class_id,
        org_id=assignment.org_id,
        teacher_user_id=assignment.teacher_user_id,
        title=assignment.title,
        created_at=assignment.created_at,
    )


def _to_artifact_response(artifact: Artifact) -> ArtifactResponse:
    return ArtifactResponse(
        artifact_id=artifact.artifact_id,
        assignment_id=artifact.assignment_id,
        student_id=artifact.student_id,
        class_id=artifact.class_id,
        org_id=artifact.org_id,
        teacher_user_id=artifact.teacher_user_id,
        file_name=artifact.file_name,
        media_type=artifact.media_type,
        storage_key=artifact.storage_key,
        created_at=artifact.created_at,
    )


@router.post(
    "/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment(
    payload: AssignmentCreateRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> AssignmentResponse:
    _require_teacher(actor)
    try:
        assignment = service.create_assignment(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            class_id=payload.class_id,
            title=payload.title,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return _to_assignment_response(assignment)


@router.post(
    "/assignments/{assignment_id}/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_artifact(
    assignment_id: str,
    student_id: str = Form(...),
    file: UploadFile = File(...),
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> ArtifactResponse:
    _require_teacher(actor)
    try:
        artifact = service.create_artifact(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
            student_id=student_id,
            file_name=file.filename or "upload",
            media_type=file.content_type or "application/octet-stream",
        )
    except ArtifactFormatError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    finally:
        await file.close()
    return _to_artifact_response(artifact)


@router.get(
    "/assignments/{assignment_id}/artifacts/{artifact_id}",
    response_model=ArtifactResponse,
)
async def get_artifact(
    assignment_id: str,
    artifact_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> ArtifactResponse:
    _require_teacher(actor)
    try:
        artifact = service.get_artifact(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
            artifact_id=artifact_id,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return _to_artifact_response(artifact)


@router.get(
    "/assignments/{assignment_id}/artifacts",
    response_model=ArtifactListResponse,
)
async def list_artifacts(
    assignment_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> ArtifactListResponse:
    _require_teacher(actor)
    try:
        artifacts = service.list_artifacts(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return ArtifactListResponse(artifacts=[_to_artifact_response(a) for a in artifacts])


# --- Grading job helpers ---


def _to_grading_job_response(job: GradingJob) -> GradingJobResponse:
    return GradingJobResponse(
        job_id=job.job_id,
        artifact_id=job.artifact_id,
        assignment_id=job.assignment_id,
        status=job.status,
        attempt_count=job.attempt_count,
        submitted_at=job.submitted_at,
        completed_at=job.completed_at,
    )


def _to_grading_job_with_result_response(
    job_with_result: GradingJobWithResult,
) -> GradingJobWithResultResponse:
    result_response = None
    if job_with_result.result is not None:
        r = job_with_result.result
        result_response = GradingResultResponse(
            proposed_score=r.proposed_score,
            rubric_mapping=r.rubric_mapping,
            draft_feedback=r.draft_feedback,
            generated_at=r.generated_at,
            confidence_level=r.confidence_level,
            confidence_score=r.confidence_score,
            confidence_reason=r.confidence_reason,
            practice_recommendations=r.practice_recommendations,
        )
    return GradingJobWithResultResponse(
        job_id=job_with_result.job_id,
        artifact_id=job_with_result.artifact_id,
        assignment_id=job_with_result.assignment_id,
        status=job_with_result.status,
        attempt_count=job_with_result.attempt_count,
        submitted_at=job_with_result.submitted_at,
        completed_at=job_with_result.completed_at,
        result=result_response,
        is_approved=job_with_result.is_approved,
    )


def _to_grade_approval_response(approval: GradeApproval) -> GradeApprovalResponse:
    return GradeApprovalResponse(
        job_id=approval.job_id,
        approved_score=approval.approved_score,
        approved_feedback=approval.approved_feedback,
        approver_user_id=approval.approver_user_id,
        approved_at=approval.approved_at,
        version=approval.version,
    )


def _to_grade_version_response(v: GradeVersion) -> GradeVersionResponse:
    return GradeVersionResponse(
        job_id=v.job_id,
        version=v.version,
        approved_score=v.approved_score,
        approved_feedback=v.approved_feedback,
        editor_user_id=v.editor_user_id,
        edited_at=v.edited_at,
        is_approved=v.is_approved,
    )


def _process_grading_job_task(job_id: str, service: GradingService) -> None:
    """Background task: run stub AI grading for the given job. Errors are swallowed."""
    try:
        service.process_grading_job(job_id)
    except Exception:  # noqa: BLE001
        logger.exception("Background grading job failed for job_id=%s", job_id)


# --- Grading job endpoints ---


@router.post(
    "/assignments/{assignment_id}/grading-jobs",
    response_model=GradingJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_grading_job(
    assignment_id: str,
    payload: GradingJobSubmitRequest,
    background_tasks: BackgroundTasks,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> GradingJobResponse:
    _require_teacher(actor)
    try:
        job = service.submit_grading_job(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
            artifact_id=payload.artifact_id,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    if job.status == "pending" and job.attempt_count == 0:
        background_tasks.add_task(
            _process_grading_job_task, job_id=job.job_id, service=service
        )
    return _to_grading_job_response(job)


@router.get(
    "/assignments/{assignment_id}/grading-jobs/{job_id}",
    response_model=GradingJobWithResultResponse,
)
async def get_grading_job(
    assignment_id: str,
    job_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> GradingJobWithResultResponse:
    _require_teacher(actor)
    try:
        job_with_result = service.get_grading_job_status(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
            job_id=job_id,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return _to_grading_job_with_result_response(job_with_result)


@router.post(
    "/assignments/{assignment_id}/grading-jobs/{job_id}/approve",
    response_model=GradeApprovalResponse,
    status_code=status.HTTP_200_OK,
)
async def approve_grading_job(
    assignment_id: str,
    job_id: str,
    payload: GradeApprovalRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> GradeApprovalResponse:
    _require_teacher(actor)
    try:
        approval = service.approve_grading_job(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
            job_id=job_id,
            approved_score=payload.approved_score,
            approved_feedback=payload.approved_feedback,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except GradingStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return _to_grade_approval_response(approval)


@router.get(
    "/assignments/{assignment_id}/grading-jobs/{job_id}/approval",
    response_model=GradeApprovalResponse,
)
async def get_grade_approval(
    assignment_id: str,
    job_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> GradeApprovalResponse:
    _require_teacher(actor)
    try:
        approval = service.get_grade_approval(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
            job_id=job_id,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return _to_grade_approval_response(approval)


@router.get(
    "/assignments/{assignment_id}/grading-jobs/{job_id}/versions",
    response_model=GradeVersionListResponse,
)
async def list_grade_versions(
    assignment_id: str,
    job_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> GradeVersionListResponse:
    _require_teacher(actor)
    try:
        versions = service.list_grade_versions(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
            job_id=job_id,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return GradeVersionListResponse(
        versions=[_to_grade_version_response(v) for v in versions]
    )


# --- Recommendation job helpers ---


def _to_recommendation_job_response(
    job: RecommendationJob,
) -> RecommendationJobResponse:
    return RecommendationJobResponse(
        rec_job_id=job.rec_job_id,
        job_id=job.job_id,
        assignment_id=job.assignment_id,
        student_id=job.student_id,
        status=job.status,
        attempt_count=job.attempt_count,
        submitted_at=job.submitted_at,
        completed_at=job.completed_at,
    )


def _to_recommendation_job_with_result_response(
    job_with_result: RecommendationJobWithResult,
) -> RecommendationJobWithResultResponse:
    result_response = None
    if job_with_result.result is not None:
        r = job_with_result.result
        result_response = RecommendationResultResponse(
            rec_job_id=r.rec_job_id,
            topics=[
                RecommendationTopicItem(
                    topic=t["topic"],
                    suggestion=t["suggestion"],
                    weakness_signal=t["weakness_signal"],
                )
                for t in r.topics
            ],
            generated_at=r.generated_at,
        )
    return RecommendationJobWithResultResponse(
        rec_job_id=job_with_result.rec_job_id,
        job_id=job_with_result.job_id,
        assignment_id=job_with_result.assignment_id,
        student_id=job_with_result.student_id,
        status=job_with_result.status,
        attempt_count=job_with_result.attempt_count,
        submitted_at=job_with_result.submitted_at,
        completed_at=job_with_result.completed_at,
        result=result_response,
        is_confirmed=job_with_result.is_confirmed,
    )


def _to_confirmed_recommendation_response(
    confirmed: ConfirmedRecommendation,
) -> ConfirmedRecommendationResponse:
    return ConfirmedRecommendationResponse(
        rec_job_id=confirmed.rec_job_id,
        job_id=confirmed.job_id,
        student_id=confirmed.student_id,
        topics=[
            RecommendationTopicItem(
                topic=t["topic"],
                suggestion=t["suggestion"],
                weakness_signal=t["weakness_signal"],
            )
            for t in confirmed.topics
        ],
        confirmed_by=confirmed.confirmed_by,
        confirmed_at=confirmed.confirmed_at,
    )


def _process_recommendation_job_task(rec_job_id: str, service: GradingService) -> None:
    """Background task: run stub recommendation generation. Errors are swallowed."""
    try:
        service.process_recommendation_job(rec_job_id)
    except Exception:  # noqa: BLE001
        logger.exception(
            "Background recommendation job failed for rec_job_id=%s", rec_job_id
        )


# --- Recommendation job endpoints ---


@router.post(
    "/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs",
    response_model=RecommendationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_recommendation_job(
    assignment_id: str,
    job_id: str,
    background_tasks: BackgroundTasks,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> RecommendationJobResponse:
    _require_teacher(actor)
    try:
        rec_job = service.submit_recommendation_job(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
            job_id=job_id,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except GradingStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    if rec_job.status == "pending" and rec_job.attempt_count == 0:
        background_tasks.add_task(
            _process_recommendation_job_task,
            rec_job_id=rec_job.rec_job_id,
            service=service,
        )
    return _to_recommendation_job_response(rec_job)


@router.get(
    "/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}",
    response_model=RecommendationJobWithResultResponse,
)
async def get_recommendation_job(
    assignment_id: str,
    job_id: str,
    rec_job_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> RecommendationJobWithResultResponse:
    _require_teacher(actor)
    try:
        job_with_result = service.get_recommendation_job_status(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
            job_id=job_id,
            rec_job_id=rec_job_id,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return _to_recommendation_job_with_result_response(job_with_result)


@router.post(
    "/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}/confirm",
    response_model=ConfirmedRecommendationResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_recommendations(
    assignment_id: str,
    job_id: str,
    rec_job_id: str,
    payload: ConfirmRecommendationRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> ConfirmedRecommendationResponse:
    _require_teacher(actor)
    topics = [{"topic": t.topic, "suggestion": t.suggestion} for t in payload.topics]
    try:
        confirmed = service.confirm_recommendations(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
            job_id=job_id,
            rec_job_id=rec_job_id,
            topics=topics,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except GradingStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return _to_confirmed_recommendation_response(confirmed)


@router.get(
    "/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}/confirm",
    response_model=ConfirmedRecommendationResponse,
)
async def get_confirmed_recommendations(
    assignment_id: str,
    job_id: str,
    rec_job_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: GradingService = Depends(get_grading_service),
) -> ConfirmedRecommendationResponse:
    _require_teacher(actor)
    try:
        confirmed = service.get_confirmed_recommendation(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            assignment_id=assignment_id,
            job_id=job_id,
            rec_job_id=rec_job_id,
        )
    except GradingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return _to_confirmed_recommendation_response(confirmed)

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status

from app.domains.auth.dependencies import ActorContext, require_authenticated_actor
from app.domains.grading.repository import InMemoryGradingRepository
from app.domains.grading.schemas import (
    ArtifactListResponse,
    ArtifactResponse,
    AssignmentCreateRequest,
    AssignmentResponse,
    GradingJobResponse,
    GradingJobSubmitRequest,
    GradingJobWithResultResponse,
    GradingResultResponse,
)
from app.domains.grading.service import (
    Artifact,
    ArtifactFormatError,
    Assignment,
    GradingAccessError,
    GradingJob,
    GradingJobWithResult,
    GradingService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/grading", tags=["grading"])

_grading_service = GradingService(repository=InMemoryGradingRepository())


async def get_grading_service() -> GradingService:
    return _grading_service


def reset_grading_state_for_tests() -> None:
    InMemoryGradingRepository.reset_state()


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


@router.post("/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
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


def _to_grading_job_with_result_response(job_with_result: GradingJobWithResult) -> GradingJobWithResultResponse:
    result_response = None
    if job_with_result.result is not None:
        r = job_with_result.result
        result_response = GradingResultResponse(
            proposed_score=r.proposed_score,
            rubric_mapping=r.rubric_mapping,
            draft_feedback=r.draft_feedback,
            generated_at=r.generated_at,
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    background_tasks.add_task(_process_grading_job_task, job_id=job.job_id, service=service)
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _to_grading_job_with_result_response(job_with_result)

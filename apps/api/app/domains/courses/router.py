from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.domains.auth.dependencies import ActorContext, require_authenticated_actor
from app.domains.courses.repository import InMemoryCoursesRepository
from app.domains.courses.schemas import (
    LessonDraftEditRequest,
    LessonDraftGenerateRequest,
    LessonDraftListResponse,
    LessonDraftRevisionListResponse,
    LessonDraftRevisionResponse,
    LessonDraftResponse,
    StudentVariantCreateRequest,
)
from app.domains.courses.service import (
    CourseDraft,
    CourseDraftRevision,
    CourseDraftGenerationAccessError,
    CourseDraftGenerationProviderUnavailableError,
    CourseDraftNotFoundError,
    CoursesService,
)

router = APIRouter(prefix="/courses", tags=["courses"])

_courses_service = CoursesService(repository=InMemoryCoursesRepository())


async def get_courses_service() -> CoursesService:
    return _courses_service


def reset_courses_state_for_tests() -> None:
    InMemoryCoursesRepository.reset_state()


def _require_teacher(actor: ActorContext) -> None:
    if actor.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _to_response(draft: CourseDraft) -> LessonDraftResponse:
    return LessonDraftResponse(
        draft_id=draft.draft_id,
        org_id=draft.org_id,
        teacher_user_id=draft.teacher_user_id,
        class_id=draft.class_id,
        unit_title=draft.unit_title,
        prompt=draft.prompt,
        generated_outline=draft.generated_outline,
        suggested_assessments=draft.suggested_assessments,
        revision=draft.revision,
        base_draft_id=draft.base_draft_id,
        student_id=draft.student_id,
        objectives=draft.objectives,
        pacing_notes=draft.pacing_notes,
        assessments=draft.assessments,
        status=draft.status,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


def _to_revision_response(revision: CourseDraftRevision) -> LessonDraftRevisionResponse:
    return LessonDraftRevisionResponse(
        revision=revision.revision,
        objectives=revision.objectives,
        pacing_notes=revision.pacing_notes,
        assessments=revision.assessments,
        updated_by_user_id=revision.updated_by_user_id,
        updated_at=revision.updated_at,
    )


@router.post("/drafts/generate", response_model=LessonDraftResponse, status_code=status.HTTP_201_CREATED)
async def generate_lesson_draft(
    payload: LessonDraftGenerateRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: CoursesService = Depends(get_courses_service),
) -> LessonDraftResponse:
    _require_teacher(actor)
    try:
        created = service.generate_draft(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            class_id=payload.class_id,
            prompt=payload.prompt,
            unit_title=payload.unit_title,
        )
    except CourseDraftGenerationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except CourseDraftGenerationProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return _to_response(created)


@router.get("/drafts/{draft_id}", response_model=LessonDraftResponse)
async def get_lesson_draft(
    draft_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: CoursesService = Depends(get_courses_service),
) -> LessonDraftResponse:
    _require_teacher(actor)
    try:
        draft = service.get_draft(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            draft_id=draft_id,
        )
    except CourseDraftNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CourseDraftGenerationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _to_response(draft)


@router.get("/drafts", response_model=LessonDraftListResponse)
async def list_lesson_drafts(
    actor: ActorContext = Depends(require_authenticated_actor),
    service: CoursesService = Depends(get_courses_service),
) -> LessonDraftListResponse:
    _require_teacher(actor)
    drafts = service.list_drafts_for_teacher(actor_user_id=actor.user_id, actor_org_id=actor.org_id)
    return LessonDraftListResponse(drafts=[_to_response(draft) for draft in drafts])


@router.put("/drafts/{draft_id}", response_model=LessonDraftResponse)
async def edit_lesson_draft(
    draft_id: str,
    payload: LessonDraftEditRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: CoursesService = Depends(get_courses_service),
) -> LessonDraftResponse:
    _require_teacher(actor)
    try:
        draft = service.edit_draft(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            draft_id=draft_id,
            objectives=payload.objectives,
            pacing_notes=payload.pacing_notes,
            assessments=payload.assessments,
        )
    except CourseDraftGenerationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _to_response(draft)


@router.get("/drafts/{draft_id}/revisions", response_model=LessonDraftRevisionListResponse)
async def list_lesson_draft_revisions(
    draft_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: CoursesService = Depends(get_courses_service),
) -> LessonDraftRevisionListResponse:
    _require_teacher(actor)
    try:
        revisions = service.list_revisions(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            draft_id=draft_id,
        )
    except CourseDraftGenerationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return LessonDraftRevisionListResponse(revisions=[_to_revision_response(revision) for revision in revisions])


@router.post("/drafts/{draft_id}/student-variants", response_model=LessonDraftResponse, status_code=status.HTTP_201_CREATED)
async def create_student_variant(
    draft_id: str,
    payload: StudentVariantCreateRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: CoursesService = Depends(get_courses_service),
) -> LessonDraftResponse:
    _require_teacher(actor)
    try:
        created = service.create_student_variant(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            draft_id=draft_id,
            student_id=payload.student_id,
            objectives=payload.objectives,
            pacing_notes=payload.pacing_notes,
            assessments=payload.assessments,
        )
    except CourseDraftGenerationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _to_response(created)

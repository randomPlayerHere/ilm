from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.domains.auth.dependencies import ActorContext, require_authenticated_actor
from app.domains.courses.repository import InMemoryCoursesRepository
from app.domains.courses.schemas import LessonDraftGenerateRequest, LessonDraftListResponse, LessonDraftResponse
from app.domains.courses.service import (
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
    return LessonDraftResponse(
        draft_id=created.draft_id,
        org_id=created.org_id,
        teacher_user_id=created.teacher_user_id,
        class_id=created.class_id,
        unit_title=created.unit_title,
        prompt=created.prompt,
        generated_outline=created.generated_outline,
        suggested_assessments=created.suggested_assessments,
        status=created.status,
        created_at=created.created_at,
        updated_at=created.updated_at,
    )


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
    return LessonDraftResponse(
        draft_id=draft.draft_id,
        org_id=draft.org_id,
        teacher_user_id=draft.teacher_user_id,
        class_id=draft.class_id,
        unit_title=draft.unit_title,
        prompt=draft.prompt,
        generated_outline=draft.generated_outline,
        suggested_assessments=draft.suggested_assessments,
        status=draft.status,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


@router.get("/drafts", response_model=LessonDraftListResponse)
async def list_lesson_drafts(
    actor: ActorContext = Depends(require_authenticated_actor),
    service: CoursesService = Depends(get_courses_service),
) -> LessonDraftListResponse:
    _require_teacher(actor)
    drafts = service.list_drafts_for_teacher(actor_user_id=actor.user_id, actor_org_id=actor.org_id)
    return LessonDraftListResponse(
        drafts=[
            LessonDraftResponse(
                draft_id=draft.draft_id,
                org_id=draft.org_id,
                teacher_user_id=draft.teacher_user_id,
                class_id=draft.class_id,
                unit_title=draft.unit_title,
                prompt=draft.prompt,
                generated_outline=draft.generated_outline,
                suggested_assessments=draft.suggested_assessments,
                status=draft.status,
                created_at=draft.created_at,
                updated_at=draft.updated_at,
            )
            for draft in drafts
        ]
    )

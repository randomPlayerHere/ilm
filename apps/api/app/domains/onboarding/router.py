from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.domains.auth.dependencies import ActorContext, require_authenticated_actor
from app.domains.onboarding.repository import InMemoryOnboardingRepository
from app.domains.onboarding.schemas import (
    ClassCreateRequest,
    ClassListResponse,
    ClassResponse,
    CsvImportResponse,
    RosterResponse,
    StudentCreateRequest,
    StudentResponse,
)
from app.domains.onboarding.service import (
    ClassAccessError,
    ClassNotFoundError,
    OnboardingService,
    StudentNotEnrolledError,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

_onboarding_service = OnboardingService(repository=InMemoryOnboardingRepository())


async def get_onboarding_service() -> OnboardingService:
    return _onboarding_service


def reset_onboarding_state_for_tests() -> None:
    InMemoryOnboardingRepository.reset_state()


def _require_teacher(actor: ActorContext) -> None:
    if actor.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    payload: ClassCreateRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> ClassResponse:
    _require_teacher(actor)
    return service.create_class(
        actor_user_id=actor.user_id,
        actor_org_id=actor.org_id,
        name=payload.name,
        subject=payload.subject,
    )


@router.get("/classes", response_model=ClassListResponse)
async def list_classes(
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> ClassListResponse:
    _require_teacher(actor)
    classes = service.list_classes(actor_user_id=actor.user_id, actor_org_id=actor.org_id)
    return ClassListResponse(classes=classes)


@router.get("/classes/{class_id}/roster", response_model=RosterResponse)
async def get_class_roster(
    class_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> RosterResponse:
    _require_teacher(actor)
    try:
        return service.get_roster(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            class_id=class_id,
        )
    except ClassNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ClassAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/classes/{class_id}/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def add_student(
    class_id: str,
    payload: StudentCreateRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> StudentResponse:
    _require_teacher(actor)
    try:
        return service.add_student(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            class_id=class_id,
            name=payload.name,
            grade_level=payload.grade_level,
        )
    except ClassNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ClassAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.delete("/classes/{class_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_student(
    class_id: str,
    student_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> None:
    _require_teacher(actor)
    try:
        service.remove_student(
            actor_user_id=actor.user_id,
            class_id=class_id,
            student_id=student_id,
        )
    except ClassNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ClassAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except StudentNotEnrolledError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/classes/{class_id}/students/import", response_model=CsvImportResponse)
async def import_students_csv(
    class_id: str,
    file: UploadFile = File(...),
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> CsvImportResponse:
    _require_teacher(actor)
    try:
        content = await file.read()
        text = content.decode("utf-8-sig")  # strips BOM from Excel-exported CSVs
        return service.import_students_csv(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            class_id=class_id,
            csv_text=text,
        )
    except ClassNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ClassAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

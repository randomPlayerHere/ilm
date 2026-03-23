from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.domains.auth.dependencies import ActorContext, require_authenticated_actor
from app.domains.onboarding.repository import InMemoryOnboardingRepository
from app.domains.onboarding.schemas import (
    ClassCreateRequest,
    ClassListResponse,
    ClassResponse,
    CsvImportResponse,
    GuardianStudentLinkResponse,
    InviteLinkResolveResponse,
    InviteLinkResponse,
    JoinCodeRequest,
    JoinCodeResponse,
    LinkedChildrenResponse,
    RosterResponse,
    StudentCreateRequest,
    StudentResponse,
)
from app.domains.onboarding.service import (
    AlreadyEnrolledError,
    AlreadyLinkedError,
    ClassAccessError,
    ClassNotFoundError,
    InvalidJoinCodeError,
    InviteLinkInvalidError,
    InviteLinkNotFoundError,
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


def _require_parent(actor: ActorContext) -> None:
    if actor.role != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Parent access required")


def _require_student(actor: ActorContext) -> None:
    if actor.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access required")


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
            actor_org_id=actor.org_id,
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


@router.post(
    "/classes/{class_id}/students/{student_id}/invite-link",
    response_model=InviteLinkResponse,
)
async def generate_invite_link(
    class_id: str,
    student_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> InviteLinkResponse:
    _require_teacher(actor)
    try:
        return service.generate_invite_link(
            actor_user_id=actor.user_id,
            actor_org_id=actor.org_id,
            class_id=class_id,
            student_id=student_id,
        )
    except ClassNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ClassAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except StudentNotEnrolledError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/invite/{token}", response_model=InviteLinkResolveResponse)
async def resolve_invite_link(
    token: str,
    service: OnboardingService = Depends(get_onboarding_service),
) -> InviteLinkResolveResponse:
    # No actor context — this endpoint is unauthenticated
    try:
        return service.resolve_invite_link(token)
    except InviteLinkNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/invite/{token}/accept", response_model=GuardianStudentLinkResponse)
async def accept_invite_link(
    token: str,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> GuardianStudentLinkResponse:
    _require_parent(actor)
    try:
        return service.accept_invite_link(
            parent_user_id=actor.user_id,
            parent_org_id=actor.org_id,
            token=token,
        )
    except InviteLinkInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except AlreadyLinkedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/parent/children", response_model=LinkedChildrenResponse)
async def get_linked_children(
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> LinkedChildrenResponse:
    _require_parent(actor)
    children = service.get_linked_children(
        parent_user_id=actor.user_id,
        org_id=actor.org_id,
    )
    return LinkedChildrenResponse(children=children)


@router.post("/join", response_model=JoinCodeResponse)
async def join_class_by_code(
    payload: JoinCodeRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
    service: OnboardingService = Depends(get_onboarding_service),
) -> JoinCodeResponse:
    _require_student(actor)
    try:
        return service.join_by_code(
            student_user_id=actor.user_id,
            org_id=actor.org_id,
            join_code=payload.join_code,
        )
    except InvalidJoinCodeError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AlreadyEnrolledError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

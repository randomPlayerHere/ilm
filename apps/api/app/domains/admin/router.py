from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.domains.admin.schemas import (
    AssignUserMembershipRequest,
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    InviteUserRequest,
    InviteUserResponse,
    OrganizationCreateRequest,
    OrganizationResponse,
    ProtectedOrganizationSummaryResponse,
    SafetyControlsResponse,
    SafetyControlsUpsertRequest,
    UpdateUserRoleRequest,
    UpdateUserRoleResponse,
    UserLifecycleResponse,
)
from app.domains.admin.service import (
    AdminService,
    DuplicateOrganizationError,
    InvalidLifecycleTransitionError,
    InvitationError,
    OrganizationNotFoundError,
    SafetyControlsAccessError,
    SafetyControlsValidationError,
    UserLifecycleError,
    UserNotFoundError,
)
from app.domains.auth.dependencies import ActorContext, require_authenticated_actor
from app.domains.auth.repository import InMemoryAuthRepository

router = APIRouter(prefix="/admin", tags=["admin"])

_admin_service = AdminService(repository=InMemoryAuthRepository())


async def get_admin_service() -> AdminService:
    return _admin_service


def reset_admin_state_for_tests() -> None:
    InMemoryAuthRepository.reset_state()


async def require_admin_actor(
    actor: ActorContext = Depends(require_authenticated_actor),
) -> ActorContext:
    if actor.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permission required")
    return actor


async def require_authorized_org_actor(
    org_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> ActorContext:
    if actor.role not in {"admin", "principal"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if actor.org_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return actor


async def require_safety_controls_reader(
    org_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> ActorContext:
    if actor.role not in {"admin", "principal", "teacher"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if actor.org_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return actor


@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreateRequest,
    actor: ActorContext = Depends(require_admin_actor),
    service: AdminService = Depends(get_admin_service),
) -> OrganizationResponse:
    try:
        org = service.create_organization(name=payload.name, slug=payload.slug, actor_id=actor.user_id)
    except DuplicateOrganizationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return OrganizationResponse(org_id=org.org_id, name=org.name, slug=org.slug)


@router.post("/users/invite", response_model=InviteUserResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    payload: InviteUserRequest,
    actor: ActorContext = Depends(require_admin_actor),
    service: AdminService = Depends(get_admin_service),
) -> InviteUserResponse:
    try:
        invited = service.invite_user(
            email=payload.email,
            role=payload.role,
            org_id=payload.org_id,
            actor_id=actor.user_id,
            expires_in_seconds=payload.expires_in_seconds,
        )
    except OrganizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UserLifecycleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return InviteUserResponse(
        user_id=invited.user_id,
        email=invited.email,
        role=invited.role,
        status=invited.status,
        org_id=invited.org_id,
        invitation_token=invited.invitation_token,
        expires_at=invited.expires_at,
    )


@router.post("/users/{user_id}/role", response_model=UpdateUserRoleResponse)
async def update_user_role(
    user_id: str,
    payload: UpdateUserRoleRequest,
    actor: ActorContext = Depends(require_admin_actor),
    service: AdminService = Depends(get_admin_service),
) -> UpdateUserRoleResponse:
    try:
        updated = service.update_user_role(
            user_id=user_id,
            role=payload.role,
            actor_id=actor.user_id,
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UserLifecycleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UpdateUserRoleResponse(user_id=updated.user_id, role=updated.role, org_id=updated.org_id)


@router.post("/users/{user_id}/membership", response_model=UserLifecycleResponse)
async def assign_user_membership(
    user_id: str,
    payload: AssignUserMembershipRequest,
    actor: ActorContext = Depends(require_admin_actor),
    service: AdminService = Depends(get_admin_service),
) -> UserLifecycleResponse:
    try:
        updated = service.assign_user_membership(
            user_id=user_id,
            org_id=payload.org_id,
            actor_id=actor.user_id,
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OrganizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return UserLifecycleResponse(user_id=updated.user_id, status=updated.status, org_id=updated.org_id)


@router.post("/users/{user_id}/activate", response_model=UserLifecycleResponse)
async def activate_user(
    user_id: str,
    actor: ActorContext = Depends(require_admin_actor),
    service: AdminService = Depends(get_admin_service),
) -> UserLifecycleResponse:
    try:
        updated = service.activate_user(user_id=user_id, actor_id=actor.user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidLifecycleTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UserLifecycleResponse(user_id=updated.user_id, status=updated.status, org_id=updated.org_id)


@router.post("/users/{user_id}/deactivate", response_model=UserLifecycleResponse)
async def deactivate_user(
    user_id: str,
    actor: ActorContext = Depends(require_admin_actor),
    service: AdminService = Depends(get_admin_service),
) -> UserLifecycleResponse:
    try:
        updated = service.deactivate_user(user_id=user_id, actor_id=actor.user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidLifecycleTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UserLifecycleResponse(user_id=updated.user_id, status=updated.status, org_id=updated.org_id)


@router.post("/invitations/accept", response_model=InvitationAcceptResponse)
async def accept_invitation(
    payload: InvitationAcceptRequest,
    service: AdminService = Depends(get_admin_service),
) -> InvitationAcceptResponse:
    try:
        updated = service.accept_invitation(
            invitation_token=payload.invitation_token,
            org_id=payload.org_id,
        )
    except InvitationError as exc:
        detail = str(exc)
        if "not valid for this organization" in detail:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc

    return InvitationAcceptResponse(user_id=updated.user_id, status=updated.status, org_id=updated.org_id)


@router.get("/protected/organizations/{org_id}/summary", response_model=ProtectedOrganizationSummaryResponse)
async def get_protected_organization_summary(
    org_id: str,
    actor: ActorContext = Depends(require_authorized_org_actor),
    service: AdminService = Depends(get_admin_service),
) -> ProtectedOrganizationSummaryResponse:
    try:
        summary = service.get_protected_org_summary(org_id=org_id)
    except OrganizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProtectedOrganizationSummaryResponse(
        org_id=summary.org_id,
        organization_name=summary.organization_name,
        message=summary.message,
    )


@router.put("/organizations/{org_id}/safety-controls", response_model=SafetyControlsResponse)
async def upsert_safety_controls(
    org_id: str,
    payload: SafetyControlsUpsertRequest,
    actor: ActorContext = Depends(require_admin_actor),
    service: AdminService = Depends(get_admin_service),
) -> SafetyControlsResponse:
    try:
        updated = service.update_safety_controls(
            org_id=org_id,
            moderation_mode=payload.moderation_mode,
            blocked_categories=payload.blocked_categories,
            age_safety_level=payload.age_safety_level,
            max_response_tone=payload.max_response_tone,
            actor_id=actor.user_id,
            actor_org_id=actor.org_id,
        )
    except SafetyControlsAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except SafetyControlsValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OrganizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SafetyControlsResponse(
        org_id=updated.org_id,
        version=updated.version,
        moderation_mode=updated.moderation_mode,
        blocked_categories=updated.blocked_categories,
        age_safety_level=updated.age_safety_level,
        max_response_tone=updated.max_response_tone,
        updated_by=updated.updated_by,
        updated_at=updated.updated_at,
    )


@router.get("/organizations/{org_id}/safety-controls", response_model=SafetyControlsResponse)
async def get_safety_controls(
    org_id: str,
    actor: ActorContext = Depends(require_safety_controls_reader),
    service: AdminService = Depends(get_admin_service),
) -> SafetyControlsResponse:
    try:
        controls = service.get_safety_controls(org_id=org_id, actor_org_id=actor.org_id)
    except SafetyControlsAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except OrganizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SafetyControlsResponse(
        org_id=controls.org_id,
        version=controls.version,
        moderation_mode=controls.moderation_mode,
        blocked_categories=controls.blocked_categories,
        age_safety_level=controls.age_safety_level,
        max_response_tone=controls.max_response_tone,
        updated_by=controls.updated_by,
        updated_at=controls.updated_at,
    )

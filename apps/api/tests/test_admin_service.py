from __future__ import annotations

import pytest

from app.domains.admin.service import (
    AdminService,
    DuplicateOrganizationError,
    InvitationError,
    OrganizationNotFoundError,
    SafetyControlsValidationError,
    UserLifecycleError,
)
from app.domains.auth.repository import InMemoryAuthRepository


def setup_function():
    InMemoryAuthRepository.reset_state()


def test_create_organization_duplicate_slug_raises_conflict_error():
    service = AdminService(repository=InMemoryAuthRepository())

    service.create_organization(name="Alpha", slug="alpha", actor_id="usr_admin_1")
    with pytest.raises(DuplicateOrganizationError):
        service.create_organization(name="Alpha Two", slug="alpha", actor_id="usr_admin_1")


def test_invite_unknown_org_raises_not_found():
    service = AdminService(repository=InMemoryAuthRepository())

    with pytest.raises(OrganizationNotFoundError):
        service.invite_user(
            email="invitee@example.com",
            role="teacher",
            org_id="org_missing",
            actor_id="usr_admin_1",
            expires_in_seconds=3600,
        )


def test_deactivate_then_activate_user_lifecycle():
    service = AdminService(repository=InMemoryAuthRepository())

    deactivated = service.deactivate_user(user_id="usr_teacher_1", actor_id="usr_admin_1")
    assert deactivated.status == "deactivated"

    activated = service.activate_user(user_id="usr_teacher_1", actor_id="usr_admin_1")
    assert activated.status == "active"


def test_invalid_transition_raises_error():
    service = AdminService(repository=InMemoryAuthRepository())

    with pytest.raises(UserLifecycleError):
        service.activate_user(user_id="usr_teacher_1", actor_id="usr_admin_1")


def test_accept_invitation_wrong_org_is_denied():
    service = AdminService(repository=InMemoryAuthRepository())
    org = service.create_organization(name="Gamma", slug="gamma", actor_id="usr_admin_1")
    invite = service.invite_user(
        email="pending@example.com",
        role="teacher",
        org_id=org.org_id,
        actor_id="usr_admin_1",
        expires_in_seconds=3600,
    )

    with pytest.raises(InvitationError):
        service.accept_invitation(invitation_token=invite.invitation_token, org_id="org_wrong")


def test_update_role_and_membership_persist_for_user():
    service = AdminService(repository=InMemoryAuthRepository())

    role_updated = service.update_user_role(
        user_id="usr_teacher_1",
        role="principal",
        actor_id="usr_admin_1",
    )
    assert role_updated.role == "principal"

    org = service.create_organization(name="Delta", slug="delta", actor_id="usr_admin_1")
    membership_updated = service.assign_user_membership(
        user_id="usr_teacher_1",
        org_id=org.org_id,
        actor_id="usr_admin_1",
    )
    assert membership_updated.org_id == org.org_id


def test_update_role_rejects_unsupported_role():
    service = AdminService(repository=InMemoryAuthRepository())
    with pytest.raises(UserLifecycleError):
        service.update_user_role(
            user_id="usr_teacher_1",
            role="superuser",
            actor_id="usr_admin_1",
        )


def test_update_and_get_safety_controls_versions_and_normalization():
    service = AdminService(repository=InMemoryAuthRepository())

    first = service.update_safety_controls(
        org_id="org_demo_1",
        moderation_mode="balanced",
        blocked_categories=[" violence ", "self-harm", "violence"],
        age_safety_level="standard",
        max_response_tone="neutral",
        actor_id="usr_admin_1",
        actor_org_id="org_demo_1",
    )
    assert first.version == 1
    assert first.blocked_categories == ["self-harm", "violence"]

    second = service.update_safety_controls(
        org_id="org_demo_1",
        moderation_mode="strict",
        blocked_categories=["hate"],
        age_safety_level="enhanced",
        max_response_tone="supportive",
        actor_id="usr_admin_1",
        actor_org_id="org_demo_1",
    )
    assert second.version == 2

    latest = service.get_safety_controls(org_id="org_demo_1", actor_org_id="org_demo_1")
    assert latest.version == 2
    assert latest.moderation_mode == "strict"
    assert latest.blocked_categories == ["hate"]


def test_update_safety_controls_rejects_invalid_or_noop_payloads():
    service = AdminService(repository=InMemoryAuthRepository())

    with pytest.raises(SafetyControlsValidationError):
        service.update_safety_controls(
            org_id="org_demo_1",
            moderation_mode="invalid",
            blocked_categories=["violence"],
            age_safety_level="standard",
            max_response_tone="neutral",
            actor_id="usr_admin_1",
            actor_org_id="org_demo_1",
        )

    created = service.update_safety_controls(
        org_id="org_demo_1",
        moderation_mode="balanced",
        blocked_categories=["violence"],
        age_safety_level="standard",
        max_response_tone="neutral",
        actor_id="usr_admin_1",
        actor_org_id="org_demo_1",
    )
    assert created.version == 1

    with pytest.raises(SafetyControlsValidationError):
        service.update_safety_controls(
            org_id="org_demo_1",
            moderation_mode="balanced",
            blocked_categories=["violence"],
            age_safety_level="standard",
            max_response_tone="neutral",
            actor_id="usr_admin_1",
            actor_org_id="org_demo_1",
        )

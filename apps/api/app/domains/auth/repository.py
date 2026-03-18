from __future__ import annotations

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Protocol

from app.core.security import hash_password
from app.domains.auth.models import (
    AuditEventRecord,
    InvitationRecord,
    OrganizationRecord,
    SafetyControlsRecord,
    UserRecord,
)


class AuthRepository(Protocol):
    def get_by_email(self, normalized_email: str) -> UserRecord | None:
        ...

    def get_by_user_id(self, user_id: str) -> UserRecord | None:
        ...

    def get_by_google_sub(self, google_sub: str) -> UserRecord | None:
        ...

    def link_google_sub(self, user_id: str, google_sub: str) -> None:
        ...

    def update_user_role(self, user_id: str, role: str, actor_id: str) -> UserRecord:
        ...

    def assign_user_membership(self, user_id: str, org_id: str, actor_id: str) -> UserRecord:
        ...

    def update_safety_controls(
        self,
        org_id: str,
        moderation_mode: str,
        blocked_categories: list[str],
        age_safety_level: str,
        max_response_tone: str,
        actor_id: str,
    ) -> SafetyControlsRecord:
        ...

    def get_latest_safety_controls(self, org_id: str) -> SafetyControlsRecord | None:
        ...


class InMemoryAuthRepository:
    _users: dict[str, UserRecord] = {}
    _orgs: dict[str, OrganizationRecord] = {}
    _invitations: dict[str, InvitationRecord] = {}
    _safety_controls: dict[str, list[SafetyControlsRecord]] = {}
    _audit_events: list[AuditEventRecord] = []
    _org_seq: int = 2
    _user_seq: int = 3
    _event_seq: int = 0
    _seeded: bool = False

    def __init__(self) -> None:
        self._ensure_seed_data()

    @classmethod
    def _ensure_seed_data(cls) -> None:
        if cls._seeded:
            return
        cls._seeded = True
        cls._users = {
            "admin@example.com": UserRecord(
                user_id="usr_admin_1",
                org_id="org_demo_1",
                email="admin@example.com",
                password_hash=hash_password("correct-horse-battery-staple"),
                role="admin",
                status="active",
            ),
            "teacher@example.com": UserRecord(
                user_id="usr_teacher_1",
                org_id="org_demo_1",
                email="teacher@example.com",
                password_hash=hash_password("correct-horse-battery-staple"),
                role="teacher",
                status="active",
                google_sub="google-sub-teacher-1",
            ),
            "inactive.teacher@example.com": UserRecord(
                user_id="usr_teacher_2",
                org_id="org_demo_1",
                email="inactive.teacher@example.com",
                password_hash=hash_password("correct-horse-battery-staple"),
                role="teacher",
                status="inactive",
            ),
            "parent@example.com": UserRecord(
                user_id="usr_parent_1",
                org_id="org_demo_1",
                email="parent@example.com",
                password_hash=hash_password("correct-horse-battery-staple"),
                role="parent",
                status="active",
            ),
            "student@example.com": UserRecord(
                user_id="usr_student_1",
                org_id="org_demo_1",
                email="student@example.com",
                password_hash=hash_password("correct-horse-battery-staple"),
                role="student",
                status="active",
            ),
        }
        cls._orgs = {
            "org_demo_1": OrganizationRecord(
                org_id="org_demo_1",
                name="Demo Organization",
                slug="demo-organization",
                created_at=datetime.now(UTC).isoformat(),
            )
        }
        cls._invitations = {}
        cls._safety_controls = {}
        cls._audit_events = []
        cls._org_seq = 2
        cls._user_seq = 3
        cls._event_seq = 0

    @classmethod
    def reset_state(cls) -> None:
        cls._seeded = False
        cls._ensure_seed_data()

    def get_by_email(self, normalized_email: str) -> UserRecord | None:
        return self.__class__._users.get(normalized_email)

    def get_by_user_id(self, user_id: str) -> UserRecord | None:
        for user in self.__class__._users.values():
            if user.user_id == user_id:
                return user
        return None

    def get_by_google_sub(self, google_sub: str) -> UserRecord | None:
        for user in self.__class__._users.values():
            if user.google_sub == google_sub:
                return user
        return None

    def link_google_sub(self, user_id: str, google_sub: str) -> None:
        for email, user in self.__class__._users.items():
            if user.user_id != user_id:
                continue
            if user.google_sub is not None and user.google_sub != google_sub:
                raise ValueError("Google subject is already linked to this user")
            self.__class__._users[email] = UserRecord(
                user_id=user.user_id,
                org_id=user.org_id,
                email=user.email,
                password_hash=user.password_hash,
                role=user.role,
                status=user.status,
                google_sub=google_sub,
            )
            return

    def create_organization(self, name: str, slug: str, actor_id: str) -> OrganizationRecord:
        normalized_slug = slug.strip().lower()
        for org in self.__class__._orgs.values():
            if org.slug == normalized_slug:
                raise ValueError("Organization slug already exists")
        org_id = f"org_{self.__class__._org_seq}"
        self.__class__._org_seq += 1
        org = OrganizationRecord(
            org_id=org_id,
            name=name.strip(),
            slug=normalized_slug,
            created_at=datetime.now(UTC).isoformat(),
        )
        self.__class__._orgs[org_id] = org
        self._record_audit(
            actor_id=actor_id,
            org_id=org_id,
            action="organization.created",
            target_id=org_id,
        )
        return org

    def get_organization(self, org_id: str) -> OrganizationRecord | None:
        return self.__class__._orgs.get(org_id)

    def invite_user(
        self,
        email: str,
        role: str,
        org_id: str,
        actor_id: str,
        expires_in_seconds: int,
    ) -> InvitationRecord:
        if org_id not in self.__class__._orgs:
            raise KeyError("Organization not found")
        normalized_email = email.strip().lower()
        user = self.__class__._users.get(normalized_email)
        if user is None:
            user_id = f"usr_{self.__class__._user_seq}"
            self.__class__._user_seq += 1
            user = UserRecord(
                user_id=user_id,
                org_id="",
                email=normalized_email,
                password_hash=hash_password(token_urlsafe(12)),
                role=role,
                status="invited",
                google_sub=None,
            )
        else:
            user = UserRecord(
                user_id=user.user_id,
                org_id=user.org_id,
                email=user.email,
                password_hash=user.password_hash,
                role=role,
                status="invited",
                google_sub=user.google_sub,
            )
        self.__class__._users[normalized_email] = user

        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in_seconds)
        invitation = InvitationRecord(
            invitation_token=token_urlsafe(24),
            user_id=user.user_id,
            email=normalized_email,
            role=role,
            org_id=org_id,
            expires_at=expires_at.isoformat(),
        )
        self.__class__._invitations[invitation.invitation_token] = invitation
        self._record_audit(
            actor_id=actor_id,
            org_id=org_id,
            action="user.invited",
            target_id=user.user_id,
        )
        return invitation

    def set_user_status(self, user_id: str, status: str, actor_id: str) -> UserRecord:
        found: tuple[str, UserRecord] | None = None
        for email, user in self.__class__._users.items():
            if user.user_id == user_id:
                found = (email, user)
                break
        if found is None:
            raise KeyError("User not found")
        email, user = found
        if user.status == status:
            raise ValueError(f"User already {status}")
        updated = UserRecord(
            user_id=user.user_id,
            org_id=user.org_id,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
            status=status,
            google_sub=user.google_sub,
        )
        self.__class__._users[email] = updated
        self._record_audit(
            actor_id=actor_id,
            org_id=updated.org_id or "org_unassigned",
            action=f"user.{status}",
            target_id=updated.user_id,
        )
        return updated

    def accept_invitation(self, invitation_token: str, org_id: str) -> UserRecord:
        invitation = self.__class__._invitations.get(invitation_token)
        if invitation is None:
            raise KeyError("Invalid invitation token")
        if invitation.used_at is not None:
            raise ValueError("Invitation token already used")
        if invitation.org_id != org_id:
            raise PermissionError("Invitation token is not valid for this organization")
        if datetime.now(UTC) >= datetime.fromisoformat(invitation.expires_at):
            raise ValueError("Invitation token has expired")

        user = self.get_by_email(invitation.email)
        if user is None:
            raise KeyError("Invited user not found")
        updated = UserRecord(
            user_id=user.user_id,
            org_id=org_id,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
            status="active",
            google_sub=user.google_sub,
        )
        self.__class__._users[invitation.email] = updated
        self.__class__._invitations[invitation_token] = InvitationRecord(
            invitation_token=invitation.invitation_token,
            user_id=invitation.user_id,
            email=invitation.email,
            role=invitation.role,
            org_id=invitation.org_id,
            expires_at=invitation.expires_at,
            used_at=datetime.now(UTC).isoformat(),
        )
        self._record_audit(
            actor_id=updated.user_id,
            org_id=org_id,
            action="invitation.accepted",
            target_id=updated.user_id,
        )
        return updated

    def update_user_role(self, user_id: str, role: str, actor_id: str) -> UserRecord:
        found = self.get_by_user_id(user_id)
        if found is None:
            raise KeyError("User not found")
        updated = UserRecord(
            user_id=found.user_id,
            org_id=found.org_id,
            email=found.email,
            password_hash=found.password_hash,
            role=role,
            status=found.status,
            google_sub=found.google_sub,
        )
        self.__class__._users[found.email] = updated
        self._record_audit(
            actor_id=actor_id,
            org_id=updated.org_id or "org_unassigned",
            action="user.role.updated",
            target_id=updated.user_id,
        )
        return updated

    def assign_user_membership(self, user_id: str, org_id: str, actor_id: str) -> UserRecord:
        found = self.get_by_user_id(user_id)
        if found is None:
            raise KeyError("User not found")
        if org_id not in self.__class__._orgs:
            raise KeyError("Organization not found")
        updated = UserRecord(
            user_id=found.user_id,
            org_id=org_id,
            email=found.email,
            password_hash=found.password_hash,
            role=found.role,
            status=found.status,
            google_sub=found.google_sub,
        )
        self.__class__._users[found.email] = updated
        self._record_audit(
            actor_id=actor_id,
            org_id=org_id,
            action="user.membership.assigned",
            target_id=updated.user_id,
        )
        return updated

    def update_safety_controls(
        self,
        org_id: str,
        moderation_mode: str,
        blocked_categories: list[str],
        age_safety_level: str,
        max_response_tone: str,
        actor_id: str,
    ) -> SafetyControlsRecord:
        if org_id not in self.__class__._orgs:
            raise KeyError("Organization not found")
        latest = self.get_latest_safety_controls(org_id)
        next_version = 1 if latest is None else latest.version + 1
        record = SafetyControlsRecord(
            org_id=org_id,
            version=next_version,
            moderation_mode=moderation_mode,
            blocked_categories=tuple(blocked_categories),
            age_safety_level=age_safety_level,
            max_response_tone=max_response_tone,
            updated_by=actor_id,
            updated_at=datetime.now(UTC).isoformat(),
        )
        history = self.__class__._safety_controls.setdefault(org_id, [])
        history.append(record)
        self._record_audit(
            actor_id=actor_id,
            org_id=org_id,
            action="org.safety_controls.updated",
            target_id=org_id,
        )
        return record

    def get_latest_safety_controls(self, org_id: str) -> SafetyControlsRecord | None:
        history = self.__class__._safety_controls.get(org_id, [])
        if not history:
            return None
        return history[-1]

    def _record_audit(self, actor_id: str, org_id: str, action: str, target_id: str) -> AuditEventRecord:
        self.__class__._event_seq += 1
        event = AuditEventRecord(
            event_id=f"audit_{self.__class__._event_seq}",
            actor_id=actor_id,
            org_id=org_id,
            action=action,
            target_id=target_id,
            occurred_at=datetime.now(UTC).isoformat(),
        )
        self.__class__._audit_events.append(event)
        return event

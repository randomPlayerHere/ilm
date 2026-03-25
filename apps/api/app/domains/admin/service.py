from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.roles import is_supported_role
from app.domains.auth.models import (
    InvitationRecord,
    OrganizationRecord,
    SafetyControlsRecord,
    UserRecord,
)
from app.domains.auth.repository import InMemoryAuthRepository
from app.domains.onboarding.repository import InMemoryOnboardingRepository


class DuplicateOrganizationError(Exception):
    pass


class OrganizationNotFoundError(Exception):
    pass


class UserLifecycleError(Exception):
    pass


class UserNotFoundError(UserLifecycleError):
    pass


class InvalidLifecycleTransitionError(UserLifecycleError):
    pass


class InvitationError(Exception):
    pass


class SafetyControlsValidationError(Exception):
    pass


class SafetyControlsAccessError(Exception):
    pass


@dataclass(frozen=True)
class OrganizationCreated:
    org_id: str
    name: str
    slug: str


@dataclass(frozen=True)
class InviteCreated:
    user_id: str
    email: str
    role: str
    status: str
    org_id: str
    invitation_token: str
    expires_at: str


@dataclass(frozen=True)
class UserLifecycleUpdated:
    user_id: str
    status: str
    org_id: str


@dataclass(frozen=True)
class UserRoleUpdated:
    user_id: str
    role: str
    org_id: str


@dataclass(frozen=True)
class ProtectedOrganizationSummary:
    org_id: str
    organization_name: str
    message: str


@dataclass(frozen=True)
class SafetyControlsConfigured:
    org_id: str
    version: int
    moderation_mode: str
    blocked_categories: list[str]
    age_safety_level: str
    max_response_tone: str
    updated_by: str
    updated_at: str


class StudentNotFoundForConsentError(Exception):
    pass


class ConsentAlreadyConfirmedError(Exception):
    pass


@dataclass(frozen=True)
class ConsentConfirmed:
    student_id: str
    org_id: str
    consent_status: str  # "confirmed"
    confirmed_by: str  # admin user_id
    confirmed_at: str  # ISO 8601 UTC


@dataclass(frozen=True)
class StudentConsentSummary:
    student_id: str
    name: str
    grade_level: str
    consent_status: str  # "pending" | "confirmed" | "not_required"
    org_id: str


@dataclass(frozen=True)
class StudentConsentRecord:
    student_id: str
    org_id: str
    consent_status: str
    confirmed_by: str | None
    confirmed_at: str | None


class AdminService:
    _SUPPORTED_MODERATION_MODES = {"balanced", "strict"}
    _SUPPORTED_AGE_SAFETY_LEVELS = {"standard", "enhanced"}
    _SUPPORTED_RESPONSE_TONES = {"neutral", "supportive", "strict"}

    def __init__(
        self,
        repository: InMemoryAuthRepository,
        onboarding_repository: InMemoryOnboardingRepository,
    ) -> None:
        self._repository = repository
        self._onboarding_repository = onboarding_repository

    def create_organization(
        self, name: str, slug: str, actor_id: str
    ) -> OrganizationCreated:
        try:
            org: OrganizationRecord = self._repository.create_organization(
                name=name, slug=slug, actor_id=actor_id
            )
        except ValueError as exc:
            raise DuplicateOrganizationError(str(exc)) from exc
        return OrganizationCreated(org_id=org.org_id, name=org.name, slug=org.slug)

    def invite_user(
        self,
        email: str,
        role: str,
        org_id: str,
        actor_id: str,
        expires_in_seconds: int,
    ) -> InviteCreated:
        if not is_supported_role(role):
            raise UserLifecycleError("Unsupported role")
        try:
            invitation: InvitationRecord = self._repository.invite_user(
                email=email,
                role=role,
                org_id=org_id,
                actor_id=actor_id,
                expires_in_seconds=expires_in_seconds,
            )
        except KeyError as exc:
            raise OrganizationNotFoundError(str(exc)) from exc

        user = self._repository.get_by_email(email.strip().lower())
        if user is None:
            raise UserLifecycleError("Invited user creation failed")

        return InviteCreated(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            status=user.status,
            org_id=invitation.org_id,
            invitation_token=invitation.invitation_token,
            expires_at=invitation.expires_at,
        )

    def activate_user(self, user_id: str, actor_id: str) -> UserLifecycleUpdated:
        return self._set_user_status(
            user_id=user_id, status="active", actor_id=actor_id
        )

    def deactivate_user(self, user_id: str, actor_id: str) -> UserLifecycleUpdated:
        return self._set_user_status(
            user_id=user_id, status="deactivated", actor_id=actor_id
        )

    def accept_invitation(
        self, invitation_token: str, org_id: str
    ) -> UserLifecycleUpdated:
        try:
            user: UserRecord = self._repository.accept_invitation(
                invitation_token=invitation_token, org_id=org_id
            )
        except KeyError as exc:
            raise InvitationError(str(exc)) from exc
        except PermissionError as exc:
            raise InvitationError(str(exc)) from exc
        except ValueError as exc:
            raise InvitationError(str(exc)) from exc
        return UserLifecycleUpdated(
            user_id=user.user_id, status=user.status, org_id=user.org_id
        )

    def update_user_role(
        self, user_id: str, role: str, actor_id: str
    ) -> UserRoleUpdated:
        if not is_supported_role(role):
            raise UserLifecycleError("Unsupported role")
        try:
            updated = self._repository.update_user_role(
                user_id=user_id,
                role=role,
                actor_id=actor_id,
            )
        except KeyError as exc:
            raise UserNotFoundError(str(exc)) from exc
        return UserRoleUpdated(
            user_id=updated.user_id, role=updated.role, org_id=updated.org_id
        )

    def assign_user_membership(
        self, user_id: str, org_id: str, actor_id: str
    ) -> UserLifecycleUpdated:
        try:
            updated = self._repository.assign_user_membership(
                user_id=user_id,
                org_id=org_id,
                actor_id=actor_id,
            )
        except KeyError as exc:
            msg = str(exc)
            if "Organization not found" in msg:
                raise OrganizationNotFoundError(msg) from exc
            raise UserNotFoundError(msg) from exc
        return UserLifecycleUpdated(
            user_id=updated.user_id, status=updated.status, org_id=updated.org_id
        )

    def get_protected_org_summary(self, org_id: str) -> ProtectedOrganizationSummary:
        org = self._repository.get_organization(org_id)
        if org is None:
            raise OrganizationNotFoundError("Organization not found")
        return ProtectedOrganizationSummary(
            org_id=org.org_id,
            organization_name=org.name,
            message="Protected organization summary",
        )

    def update_safety_controls(
        self,
        org_id: str,
        moderation_mode: str,
        blocked_categories: list[str],
        age_safety_level: str,
        max_response_tone: str,
        actor_id: str,
        actor_org_id: str,
    ) -> SafetyControlsConfigured:
        if actor_org_id != org_id:
            raise SafetyControlsAccessError("Forbidden")
        normalized_categories = self._normalize_categories(blocked_categories)
        if moderation_mode not in self._SUPPORTED_MODERATION_MODES:
            raise SafetyControlsValidationError("Unsupported moderation_mode")
        if age_safety_level not in self._SUPPORTED_AGE_SAFETY_LEVELS:
            raise SafetyControlsValidationError("Unsupported age_safety_level")
        if max_response_tone not in self._SUPPORTED_RESPONSE_TONES:
            raise SafetyControlsValidationError("Unsupported max_response_tone")
        existing = self._repository.get_latest_safety_controls(org_id)
        if existing is not None and self._is_noop(
            existing=existing,
            moderation_mode=moderation_mode,
            blocked_categories=normalized_categories,
            age_safety_level=age_safety_level,
            max_response_tone=max_response_tone,
        ):
            raise SafetyControlsValidationError(
                "No changes detected in safety controls"
            )
        try:
            updated = self._repository.update_safety_controls(
                org_id=org_id,
                moderation_mode=moderation_mode,
                blocked_categories=normalized_categories,
                age_safety_level=age_safety_level,
                max_response_tone=max_response_tone,
                actor_id=actor_id,
            )
        except KeyError as exc:
            raise OrganizationNotFoundError(str(exc)) from exc
        return self._as_safety_controls_configured(updated)

    def get_safety_controls(
        self, org_id: str, actor_org_id: str
    ) -> SafetyControlsConfigured:
        if actor_org_id != org_id:
            raise SafetyControlsAccessError("Forbidden")
        existing = self._repository.get_latest_safety_controls(org_id)
        if existing is None:
            raise OrganizationNotFoundError("Safety controls not found")
        return self._as_safety_controls_configured(existing)

    def confirm_consent(
        self,
        student_id: str,
        admin_user_id: str,
        org_id: str,
    ) -> ConsentConfirmed:
        student = self._onboarding_repository.get_student(student_id)
        if student is None:
            raise StudentNotFoundForConsentError(f"Student not found: {student_id}")
        if student.org_id != org_id:
            raise StudentNotFoundForConsentError(
                "Student does not belong to this organization"
            )
        if student.consent_status in {"confirmed", "not_required"}:
            raise ConsentAlreadyConfirmedError(
                "Consent not required or already confirmed for this student"
            )
        confirmed_at = datetime.now(UTC).isoformat()
        updated = self._onboarding_repository.confirm_student_consent(
            student_id=student_id,
            confirmed_by=admin_user_id,
            confirmed_at=confirmed_at,
        )
        assert updated.consent_confirmed_by is not None
        assert updated.consent_confirmed_at is not None
        return ConsentConfirmed(
            student_id=updated.student_id,
            org_id=updated.org_id,
            consent_status=updated.consent_status,
            confirmed_by=updated.consent_confirmed_by,
            confirmed_at=updated.consent_confirmed_at,
        )

    def list_students_pending_consent(self, org_id: str) -> list[StudentConsentSummary]:
        students = self._onboarding_repository.list_students_for_org(org_id)
        return [
            StudentConsentSummary(
                student_id=s.student_id,
                name=s.name,
                grade_level=s.grade_level,
                consent_status=s.consent_status,
                org_id=s.org_id,
            )
            for s in students
            if s.consent_status == "pending"
        ]

    def get_student_consent_record(
        self,
        student_id: str,
        org_id: str,
    ) -> StudentConsentRecord:
        student = self._onboarding_repository.get_student(student_id)
        if student is None:
            raise StudentNotFoundForConsentError(f"Student not found: {student_id}")
        if student.org_id != org_id:
            raise StudentNotFoundForConsentError(
                "Student does not belong to this organization"
            )
        return StudentConsentRecord(
            student_id=student.student_id,
            org_id=student.org_id,
            consent_status=student.consent_status,
            confirmed_by=student.consent_confirmed_by,
            confirmed_at=student.consent_confirmed_at,
        )

    def _set_user_status(
        self, user_id: str, status: str, actor_id: str
    ) -> UserLifecycleUpdated:
        try:
            user = self._repository.set_user_status(
                user_id=user_id, status=status, actor_id=actor_id
            )
        except KeyError as exc:
            raise UserNotFoundError(str(exc)) from exc
        except ValueError as exc:
            raise InvalidLifecycleTransitionError(str(exc)) from exc
        return UserLifecycleUpdated(
            user_id=user.user_id, status=user.status, org_id=user.org_id
        )

    def _normalize_categories(self, blocked_categories: list[str]) -> list[str]:
        cleaned = [
            category.strip().lower()
            for category in blocked_categories
            if category.strip()
        ]
        if not cleaned:
            raise SafetyControlsValidationError(
                "blocked_categories must contain at least one value"
            )
        return sorted(set(cleaned))

    def _is_noop(
        self,
        existing: SafetyControlsRecord,
        moderation_mode: str,
        blocked_categories: list[str],
        age_safety_level: str,
        max_response_tone: str,
    ) -> bool:
        return (
            existing.moderation_mode == moderation_mode
            and list(existing.blocked_categories) == blocked_categories
            and existing.age_safety_level == age_safety_level
            and existing.max_response_tone == max_response_tone
        )

    def _as_safety_controls_configured(
        self, record: SafetyControlsRecord
    ) -> SafetyControlsConfigured:
        return SafetyControlsConfigured(
            org_id=record.org_id,
            version=record.version,
            moderation_mode=record.moderation_mode,
            blocked_categories=list(record.blocked_categories),
            age_safety_level=record.age_safety_level,
            max_response_tone=record.max_response_tone,
            updated_by=record.updated_by,
            updated_at=record.updated_at,
        )

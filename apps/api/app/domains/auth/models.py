from dataclasses import dataclass


@dataclass(frozen=True)
class UserRecord:
    user_id: str
    org_id: str
    email: str
    password_hash: str
    role: str
    status: str
    google_sub: str | None = None


@dataclass(frozen=True)
class OrganizationRecord:
    org_id: str
    name: str
    slug: str
    created_at: str


@dataclass(frozen=True)
class InvitationRecord:
    invitation_token: str
    user_id: str
    email: str
    role: str
    org_id: str
    expires_at: str
    used_at: str | None = None


@dataclass(frozen=True)
class AuditEventRecord:
    event_id: str
    actor_id: str
    org_id: str
    action: str
    target_id: str
    occurred_at: str


@dataclass(frozen=True)
class SafetyControlsRecord:
    org_id: str
    version: int
    moderation_mode: str
    blocked_categories: tuple[str, ...]
    age_safety_level: str
    max_response_tone: str
    updated_by: str
    updated_at: str

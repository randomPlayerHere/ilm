from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class OrganizationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    slug: Annotated[
        str, StringConstraints(min_length=3, max_length=120, pattern=r"^[a-z0-9-]+$")
    ]


class OrganizationResponse(BaseModel):
    org_id: str
    name: str
    slug: str
    membership_assignment_available: bool = True


class InviteUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Annotated[
        str,
        StringConstraints(
            min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        ),
    ]
    role: Annotated[str, StringConstraints(min_length=3, max_length=32)]
    org_id: Annotated[str, StringConstraints(min_length=4, max_length=64)]
    expires_in_seconds: int = Field(default=86_400, ge=0, le=604_800)


class InviteUserResponse(BaseModel):
    user_id: str
    email: str
    role: str
    status: str
    org_id: str
    invitation_token: str
    expires_at: str


class UserLifecycleResponse(BaseModel):
    user_id: str
    status: str
    org_id: str


class InvitationAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invitation_token: str = Field(min_length=16, max_length=256)
    org_id: str = Field(min_length=4, max_length=64)


class InvitationAcceptResponse(BaseModel):
    user_id: str
    status: str
    org_id: str


class UpdateUserRoleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Annotated[str, StringConstraints(min_length=3, max_length=32)]


class UpdateUserRoleResponse(BaseModel):
    user_id: str
    role: str
    org_id: str


class AssignUserMembershipRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    org_id: Annotated[str, StringConstraints(min_length=4, max_length=64)]


class ProtectedOrganizationSummaryResponse(BaseModel):
    org_id: str
    organization_name: str
    message: str


class SafetyControlsUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    moderation_mode: Annotated[str, StringConstraints(min_length=4, max_length=32)]
    blocked_categories: list[
        Annotated[str, StringConstraints(min_length=2, max_length=64)]
    ] = Field(min_length=1, max_length=20)
    age_safety_level: Annotated[str, StringConstraints(min_length=4, max_length=32)]
    max_response_tone: Annotated[str, StringConstraints(min_length=4, max_length=32)]


class SafetyControlsResponse(BaseModel):
    org_id: str
    version: int
    moderation_mode: str
    blocked_categories: list[str]
    age_safety_level: str
    max_response_tone: str
    updated_by: str
    updated_at: str


class ConsentConfirmResponse(BaseModel):
    student_id: str
    org_id: str
    consent_status: str
    confirmed_by: str
    confirmed_at: str


class StudentConsentSummaryResponse(BaseModel):
    student_id: str
    name: str
    grade_level: str
    consent_status: str
    org_id: str


class PendingConsentListResponse(BaseModel):
    students: list[StudentConsentSummaryResponse]


class StudentConsentRecordResponse(BaseModel):
    student_id: str
    org_id: str
    consent_status: str
    confirmed_by: str | None
    confirmed_at: str | None

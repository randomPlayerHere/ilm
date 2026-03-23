from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InviteLinkRecord:
    invite_id: str        # e.g., "inv_1"
    org_id: str
    class_id: str
    student_id: str       # StudentRecord.student_id (NOT a user account)
    token: str            # URL-safe random token
    generated_by: str     # teacher user_id
    expires_at: str       # ISO 8601 UTC — 72 hours from creation
    used_at: str | None   # ISO 8601 UTC when accepted, None if unused
    created_at: str


@dataclass(frozen=True)
class GuardianStudentLinkRecord:
    link_id: str          # e.g., "gsl_1"
    parent_user_id: str   # usr_* from auth domain (the parent's auth user)
    student_id: str       # StudentRecord.student_id from onboarding domain
    org_id: str
    linked_via: str       # "invite_link" | "manual"
    invite_id: str | None # InviteLinkRecord.invite_id, None if manual
    created_at: str


@dataclass(frozen=True)
class ClassRecord:
    class_id: str        # e.g., "cls_1"
    org_id: str
    teacher_user_id: str
    name: str            # e.g., "Math Period 3"
    subject: str         # e.g., "Mathematics"
    join_code: str       # e.g., "A3BX9K" — 6-char uppercase alphanumeric
    created_at: str      # ISO 8601 UTC


@dataclass(frozen=True)
class StudentRecord:
    student_id: str      # e.g., "stu_1"
    org_id: str
    name: str            # full name, e.g., "Jane Smith"
    grade_level: str     # e.g., "Grade 5", "Year 7", "10th Grade", "Grade K"
    created_at: str
    consent_status: str = "not_required"   # "not_required" | "pending" | "confirmed"
    consent_confirmed_by: str | None = None
    consent_confirmed_at: str | None = None


@dataclass(frozen=True)
class EnrollmentRecord:
    enrollment_id: str   # e.g., "enr_1"
    class_id: str
    student_id: str
    org_id: str
    enrolled_by: str     # teacher user_id
    created_at: str

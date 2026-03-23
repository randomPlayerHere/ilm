from __future__ import annotations

import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.domains.onboarding.models import (
    ClassRecord,
    EnrollmentRecord,
    GuardianStudentLinkRecord,
    InviteLinkRecord,
    StudentRecord,
)


def _generate_join_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


def _generate_invite_token() -> str:
    return secrets.token_urlsafe(18)  # 24-char URL-safe string


class OnboardingRepository(Protocol):
    def create_class(self, org_id: str, teacher_user_id: str, name: str, subject: str) -> ClassRecord: ...
    def get_class(self, class_id: str) -> ClassRecord | None: ...
    def list_classes_for_teacher(self, teacher_user_id: str, org_id: str) -> list[ClassRecord]: ...
    def get_or_create_student(self, org_id: str, name: str, grade_level: str) -> StudentRecord: ...
    def get_student(self, student_id: str) -> StudentRecord | None: ...
    def enroll_student(self, class_id: str, student_id: str, org_id: str, enrolled_by: str) -> EnrollmentRecord: ...
    def unenroll_student(self, class_id: str, student_id: str) -> None: ...
    def list_enrollments_for_class(self, class_id: str) -> list[EnrollmentRecord]: ...
    def is_enrolled(self, class_id: str, student_id: str) -> bool: ...
    def create_invite_link(self, org_id: str, class_id: str, student_id: str, generated_by: str) -> InviteLinkRecord: ...
    def get_invite_link(self, token: str) -> InviteLinkRecord | None: ...
    def get_active_invite_link_for_student(self, class_id: str, student_id: str) -> InviteLinkRecord | None: ...
    def accept_invite_link(self, token: str, parent_user_id: str, org_id: str) -> GuardianStudentLinkRecord: ...
    def get_guardian_links_for_parent(self, parent_user_id: str) -> list[GuardianStudentLinkRecord]: ...
    def is_parent_linked_to_student(self, parent_user_id: str, student_id: str) -> bool: ...
    def find_class_by_join_code(self, join_code: str, org_id: str) -> ClassRecord | None: ...
    def join_class_by_code(self, join_code: str, student_user_id: str, org_id: str) -> EnrollmentRecord: ...


class InMemoryOnboardingRepository:
    _classes: dict[str, ClassRecord] = {}
    _students: dict[str, StudentRecord] = {}
    _enrollments: dict[str, EnrollmentRecord] = {}
    _invite_links: dict[str, InviteLinkRecord] = {}      # key: token
    _guardian_links: list[GuardianStudentLinkRecord] = []
    _class_seq: int = 2
    _student_seq: int = 1
    _enrollment_seq: int = 1
    _invite_seq: int = 0
    _guardian_link_seq: int = 0
    _seeded: bool = False

    def __init__(self) -> None:
        self._ensure_seed_data()

    @classmethod
    def _ensure_seed_data(cls) -> None:
        if cls._seeded:
            return
        cls._seeded = True
        seed_class = ClassRecord(
            class_id="cls_1",
            org_id="org_demo_1",
            teacher_user_id="usr_teacher_1",
            name="Math Period 3",
            subject="Mathematics",
            join_code="A3BX9K",
            created_at="2026-03-01T08:00:00Z",
        )
        cls._classes = {"cls_1": seed_class}
        cls._students = {}
        cls._enrollments = {}
        cls._class_seq = 2
        cls._student_seq = 1
        cls._enrollment_seq = 1
        # Seed invite link for stu_1 / cls_1
        seed_invite = InviteLinkRecord(
            invite_id="inv_1",
            org_id="org_demo_1",
            class_id="cls_1",
            student_id="stu_1",
            token="inv_demo_abc123",
            generated_by="usr_teacher_1",
            expires_at=(datetime.now(UTC) + timedelta(hours=72)).isoformat(),
            used_at=None,
            created_at="2026-03-22T08:00:00Z",
        )
        cls._invite_links = {"inv_demo_abc123": seed_invite}
        cls._guardian_links = []
        cls._invite_seq = 1
        cls._guardian_link_seq = 0

    @classmethod
    def reset_state(cls) -> None:
        cls._seeded = False
        cls._ensure_seed_data()

    def create_class(self, org_id: str, teacher_user_id: str, name: str, subject: str) -> ClassRecord:
        class_id = f"cls_{self.__class__._class_seq}"
        self.__class__._class_seq += 1
        record = ClassRecord(
            class_id=class_id,
            org_id=org_id,
            teacher_user_id=teacher_user_id,
            name=name,
            subject=subject,
            join_code=_generate_join_code(),
            created_at=datetime.now(UTC).isoformat(),
        )
        self.__class__._classes[class_id] = record
        return record

    def get_class(self, class_id: str) -> ClassRecord | None:
        return self.__class__._classes.get(class_id)

    def list_classes_for_teacher(self, teacher_user_id: str, org_id: str) -> list[ClassRecord]:
        return [
            c for c in self.__class__._classes.values()
            if c.teacher_user_id == teacher_user_id and c.org_id == org_id
        ]

    def get_or_create_student(self, org_id: str, name: str, grade_level: str) -> StudentRecord:
        # Reuse student if same name+grade already exists in org (idempotent CSV imports)
        for student in self.__class__._students.values():
            if student.org_id == org_id and student.name == name and student.grade_level == grade_level:
                return student
        student_id = f"stu_{self.__class__._student_seq}"
        self.__class__._student_seq += 1
        record = StudentRecord(
            student_id=student_id,
            org_id=org_id,
            name=name,
            grade_level=grade_level,
            created_at=datetime.now(UTC).isoformat(),
        )
        self.__class__._students[student_id] = record
        return record

    def get_student(self, student_id: str) -> StudentRecord | None:
        return self.__class__._students.get(student_id)

    def enroll_student(self, class_id: str, student_id: str, org_id: str, enrolled_by: str) -> EnrollmentRecord:
        # Idempotent: if already enrolled, return existing
        for enr in self.__class__._enrollments.values():
            if enr.class_id == class_id and enr.student_id == student_id:
                return enr
        enrollment_id = f"enr_{self.__class__._enrollment_seq}"
        self.__class__._enrollment_seq += 1
        record = EnrollmentRecord(
            enrollment_id=enrollment_id,
            class_id=class_id,
            student_id=student_id,
            org_id=org_id,
            enrolled_by=enrolled_by,
            created_at=datetime.now(UTC).isoformat(),
        )
        self.__class__._enrollments[enrollment_id] = record
        return record

    def unenroll_student(self, class_id: str, student_id: str) -> None:
        to_remove = [
            eid for eid, enr in self.__class__._enrollments.items()
            if enr.class_id == class_id and enr.student_id == student_id
        ]
        for eid in to_remove:
            del self.__class__._enrollments[eid]

    def list_enrollments_for_class(self, class_id: str) -> list[EnrollmentRecord]:
        return [enr for enr in self.__class__._enrollments.values() if enr.class_id == class_id]

    def is_enrolled(self, class_id: str, student_id: str) -> bool:
        return any(
            enr.class_id == class_id and enr.student_id == student_id
            for enr in self.__class__._enrollments.values()
        )

    def create_invite_link(self, org_id: str, class_id: str, student_id: str, generated_by: str) -> InviteLinkRecord:
        self.__class__._invite_seq += 1
        invite_id = f"inv_{self.__class__._invite_seq}"
        token = _generate_invite_token()
        record = InviteLinkRecord(
            invite_id=invite_id,
            org_id=org_id,
            class_id=class_id,
            student_id=student_id,
            token=token,
            generated_by=generated_by,
            expires_at=(datetime.now(UTC) + timedelta(hours=72)).isoformat(),
            used_at=None,
            created_at=datetime.now(UTC).isoformat(),
        )
        self.__class__._invite_links[token] = record
        return record

    def get_invite_link(self, token: str) -> InviteLinkRecord | None:
        return self.__class__._invite_links.get(token)

    def get_active_invite_link_for_student(self, class_id: str, student_id: str) -> InviteLinkRecord | None:
        now = datetime.now(UTC).isoformat()
        for link in self.__class__._invite_links.values():
            if (
                link.class_id == class_id
                and link.student_id == student_id
                and link.used_at is None
                and link.expires_at > now
            ):
                return link
        return None

    def accept_invite_link(self, token: str, parent_user_id: str, org_id: str) -> GuardianStudentLinkRecord:
        invite = self.__class__._invite_links[token]
        # Mark invite as used (replace frozen dataclass)
        updated_invite = InviteLinkRecord(
            invite_id=invite.invite_id,
            org_id=invite.org_id,
            class_id=invite.class_id,
            student_id=invite.student_id,
            token=invite.token,
            generated_by=invite.generated_by,
            expires_at=invite.expires_at,
            used_at=datetime.now(UTC).isoformat(),
            created_at=invite.created_at,
        )
        self.__class__._invite_links[token] = updated_invite
        # Create guardian link
        self.__class__._guardian_link_seq += 1
        link_id = f"gsl_{self.__class__._guardian_link_seq}"
        guardian_link = GuardianStudentLinkRecord(
            link_id=link_id,
            parent_user_id=parent_user_id,
            student_id=invite.student_id,
            org_id=org_id,
            linked_via="invite_link",
            invite_id=invite.invite_id,
            created_at=datetime.now(UTC).isoformat(),
        )
        self.__class__._guardian_links.append(guardian_link)
        return guardian_link

    def get_guardian_links_for_parent(self, parent_user_id: str) -> list[GuardianStudentLinkRecord]:
        return [lnk for lnk in self.__class__._guardian_links if lnk.parent_user_id == parent_user_id]

    def is_parent_linked_to_student(self, parent_user_id: str, student_id: str) -> bool:
        return any(
            lnk.parent_user_id == parent_user_id and lnk.student_id == student_id
            for lnk in self.__class__._guardian_links
        )

    def find_class_by_join_code(self, join_code: str, org_id: str) -> ClassRecord | None:
        for cls in self.__class__._classes.values():
            if cls.join_code == join_code and cls.org_id == org_id:
                return cls
        return None

    def join_class_by_code(self, join_code: str, student_user_id: str, org_id: str) -> EnrollmentRecord:
        cls = self.find_class_by_join_code(join_code, org_id)
        if cls is None:
            raise KeyError(f"No class found for join_code '{join_code}' in org '{org_id}'")
        # Use auth user id directly for auth-user-linked enrollment
        student_id = student_user_id
        enrollment_id = f"enr_{self.__class__._enrollment_seq}"
        self.__class__._enrollment_seq += 1
        record = EnrollmentRecord(
            enrollment_id=enrollment_id,
            class_id=cls.class_id,
            student_id=student_id,
            org_id=org_id,
            enrolled_by=student_user_id,
            created_at=datetime.now(UTC).isoformat(),
        )
        self.__class__._enrollments[enrollment_id] = record
        return record

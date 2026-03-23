from __future__ import annotations

import secrets
import string
from datetime import UTC, datetime
from typing import Protocol

from app.domains.onboarding.models import ClassRecord, EnrollmentRecord, StudentRecord


def _generate_join_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


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


class InMemoryOnboardingRepository:
    _classes: dict[str, ClassRecord] = {}
    _students: dict[str, StudentRecord] = {}
    _enrollments: dict[str, EnrollmentRecord] = {}
    _class_seq: int = 2
    _student_seq: int = 1
    _enrollment_seq: int = 1
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

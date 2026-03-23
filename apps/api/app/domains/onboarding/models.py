from __future__ import annotations

from dataclasses import dataclass


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
    grade_level: str     # e.g., "Grade 5", "Year 7", "10th Grade"
    created_at: str


@dataclass(frozen=True)
class EnrollmentRecord:
    enrollment_id: str   # e.g., "enr_1"
    class_id: str
    student_id: str
    org_id: str
    enrolled_by: str     # teacher user_id
    created_at: str

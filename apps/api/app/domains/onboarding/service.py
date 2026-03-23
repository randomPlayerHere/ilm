from __future__ import annotations

import csv
import io

from app.domains.onboarding.models import ClassRecord, StudentRecord
from app.domains.onboarding.repository import OnboardingRepository
from app.domains.onboarding.schemas import (
    ClassResponse,
    CsvImportResponse,
    CsvImportRowResult,
    RosterResponse,
    StudentResponse,
)

_MAX_CSV_ROWS = 200


class ClassNotFoundError(Exception):
    pass


class ClassAccessError(Exception):
    pass


class StudentNotFoundError(Exception):
    pass


class StudentNotEnrolledError(Exception):
    pass


class OnboardingService:
    def __init__(self, repository: OnboardingRepository) -> None:
        self._repo = repository

    def _class_to_response(self, cls: ClassRecord) -> ClassResponse:
        enrollments = self._repo.list_enrollments_for_class(cls.class_id)
        return ClassResponse(
            class_id=cls.class_id,
            org_id=cls.org_id,
            teacher_user_id=cls.teacher_user_id,
            name=cls.name,
            subject=cls.subject,
            join_code=cls.join_code,
            student_count=len(enrollments),
            created_at=cls.created_at,
        )

    def _student_to_response(self, student: StudentRecord) -> StudentResponse:
        return StudentResponse(
            student_id=student.student_id,
            name=student.name,
            grade_level=student.grade_level,
            org_id=student.org_id,
            created_at=student.created_at,
        )

    def _get_owned_class(self, class_id: str, actor_user_id: str) -> ClassRecord:
        cls = self._repo.get_class(class_id)
        if cls is None:
            raise ClassNotFoundError(f"Class '{class_id}' not found.")
        if cls.teacher_user_id != actor_user_id:
            raise ClassAccessError("You do not have permission to manage this class.")
        return cls

    def create_class(self, actor_user_id: str, actor_org_id: str, name: str, subject: str) -> ClassResponse:
        cls = self._repo.create_class(
            org_id=actor_org_id,
            teacher_user_id=actor_user_id,
            name=name,
            subject=subject,
        )
        return self._class_to_response(cls)

    def list_classes(self, actor_user_id: str, actor_org_id: str) -> list[ClassResponse]:
        classes = self._repo.list_classes_for_teacher(
            teacher_user_id=actor_user_id,
            org_id=actor_org_id,
        )
        return [self._class_to_response(cls) for cls in classes]

    def get_roster(self, actor_user_id: str, actor_org_id: str, class_id: str) -> RosterResponse:
        self._get_owned_class(class_id, actor_user_id)
        enrollments = self._repo.list_enrollments_for_class(class_id)
        students = []
        for enr in enrollments:
            student = self._repo.get_student(enr.student_id)
            if student is not None:
                students.append(self._student_to_response(student))
        return RosterResponse(class_id=class_id, students=students)

    def add_student(
        self,
        actor_user_id: str,
        actor_org_id: str,
        class_id: str,
        name: str,
        grade_level: str,
    ) -> StudentResponse:
        self._get_owned_class(class_id, actor_user_id)
        student = self._repo.get_or_create_student(
            org_id=actor_org_id,
            name=name,
            grade_level=grade_level,
        )
        self._repo.enroll_student(
            class_id=class_id,
            student_id=student.student_id,
            org_id=actor_org_id,
            enrolled_by=actor_user_id,
        )
        return self._student_to_response(student)

    def remove_student(
        self,
        actor_user_id: str,
        class_id: str,
        student_id: str,
    ) -> None:
        self._get_owned_class(class_id, actor_user_id)
        if not self._repo.is_enrolled(class_id, student_id):
            raise StudentNotEnrolledError(f"Student '{student_id}' is not enrolled in class '{class_id}'.")
        self._repo.unenroll_student(class_id, student_id)

    def import_students_csv(
        self,
        actor_user_id: str,
        actor_org_id: str,
        class_id: str,
        csv_text: str,
    ) -> CsvImportResponse:
        self._get_owned_class(class_id, actor_user_id)

        reader = csv.DictReader(io.StringIO(csv_text))

        # Normalise headers for case-insensitive match
        if reader.fieldnames is None:
            return CsvImportResponse(total_rows=0, successful=0, failed=0, results=[])

        normalised_headers = {h.strip().lower(): h for h in reader.fieldnames if h}
        if "name" not in normalised_headers or "grade_level" not in normalised_headers:
            return CsvImportResponse(
                total_rows=0,
                successful=0,
                failed=1,
                results=[
                    CsvImportRowResult(
                        row=0,
                        success=False,
                        student_name=None,
                        error="CSV must have 'name' and 'grade_level' columns",
                    )
                ],
            )

        name_col = normalised_headers["name"]
        grade_col = normalised_headers["grade_level"]

        rows = list(reader)
        if len(rows) > _MAX_CSV_ROWS:
            return CsvImportResponse(
                total_rows=len(rows),
                successful=0,
                failed=len(rows),
                results=[
                    CsvImportRowResult(
                        row=0,
                        success=False,
                        student_name=None,
                        error=f"Too many rows: {len(rows)} (maximum {_MAX_CSV_ROWS})",
                    )
                ],
            )

        results: list[CsvImportRowResult] = []
        successful = 0
        failed = 0

        for row_num, row in enumerate(rows, start=1):
            raw_name = (row.get(name_col) or "").strip()
            raw_grade = (row.get(grade_col) or "").strip()

            error: str | None = None
            if not raw_name:
                error = "Missing name"
            elif len(raw_name) > 200:
                error = "Name too long (max 200 characters)"
            elif not raw_grade:
                error = "Missing grade_level"
            elif len(raw_grade) > 50:
                error = "grade_level too long (max 50 characters)"

            if error:
                failed += 1
                results.append(CsvImportRowResult(row=row_num, success=False, student_name=raw_name or None, error=error))
                continue

            student = self._repo.get_or_create_student(
                org_id=actor_org_id,
                name=raw_name,
                grade_level=raw_grade,
            )
            self._repo.enroll_student(
                class_id=class_id,
                student_id=student.student_id,
                org_id=actor_org_id,
                enrolled_by=actor_user_id,
            )
            successful += 1
            results.append(CsvImportRowResult(row=row_num, success=True, student_name=raw_name, error=None))

        return CsvImportResponse(
            total_rows=len(rows),
            successful=successful,
            failed=failed,
            results=results,
        )

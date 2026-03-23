from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from app.domains.onboarding.models import ClassRecord, StudentRecord
from app.domains.onboarding.repository import OnboardingRepository
from app.domains.onboarding.schemas import (
    ClassResponse,
    CsvImportResponse,
    CsvImportRowResult,
    GuardianStudentLinkResponse,
    InviteLinkResolveResponse,
    InviteLinkResponse,
    JoinCodeResponse,
    LinkedChildResponse,
    RosterResponse,
    StudentResponse,
)

_MAX_CSV_ROWS = 200
INVITE_URL_SCHEME = "ilm://invite/"


class ClassNotFoundError(Exception):
    pass


class ClassAccessError(Exception):
    pass


class StudentNotFoundError(Exception):
    pass


class StudentNotEnrolledError(Exception):
    pass


class InviteLinkNotFoundError(Exception):
    pass


class InviteLinkInvalidError(Exception):
    pass


class AlreadyLinkedError(Exception):
    pass


class InvalidJoinCodeError(Exception):
    pass


class AlreadyEnrolledError(Exception):
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

    def _get_owned_class(
        self, class_id: str, actor_user_id: str, actor_org_id: str
    ) -> ClassRecord:
        cls = self._repo.get_class(class_id)
        if cls is None:
            raise ClassNotFoundError(f"Class '{class_id}' not found.")
        if cls.teacher_user_id != actor_user_id or cls.org_id != actor_org_id:
            raise ClassAccessError("You do not have permission to manage this class.")
        return cls

    def create_class(
        self, actor_user_id: str, actor_org_id: str, name: str, subject: str
    ) -> ClassResponse:
        cls = self._repo.create_class(
            org_id=actor_org_id,
            teacher_user_id=actor_user_id,
            name=name,
            subject=subject,
        )
        return self._class_to_response(cls)

    def list_classes(
        self, actor_user_id: str, actor_org_id: str
    ) -> list[ClassResponse]:
        classes = self._repo.list_classes_for_teacher(
            teacher_user_id=actor_user_id,
            org_id=actor_org_id,
        )
        return [self._class_to_response(cls) for cls in classes]

    def get_roster(
        self, actor_user_id: str, actor_org_id: str, class_id: str
    ) -> RosterResponse:
        self._get_owned_class(class_id, actor_user_id, actor_org_id)
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
        self._get_owned_class(class_id, actor_user_id, actor_org_id)
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
        actor_org_id: str,
        class_id: str,
        student_id: str,
    ) -> None:
        self._get_owned_class(class_id, actor_user_id, actor_org_id)
        if not self._repo.is_enrolled(class_id, student_id):
            raise StudentNotEnrolledError(
                f"Student '{student_id}' is not enrolled in class '{class_id}'."
            )
        self._repo.unenroll_student(class_id, student_id)

    def import_students_csv(
        self,
        actor_user_id: str,
        actor_org_id: str,
        class_id: str,
        csv_text: str,
    ) -> CsvImportResponse:
        self._get_owned_class(class_id, actor_user_id, actor_org_id)

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
                results.append(
                    CsvImportRowResult(
                        row=row_num,
                        success=False,
                        student_name=raw_name or None,
                        error=error,
                    )
                )
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
            results.append(
                CsvImportRowResult(
                    row=row_num, success=True, student_name=raw_name, error=None
                )
            )

        return CsvImportResponse(
            total_rows=len(rows),
            successful=successful,
            failed=failed,
            results=results,
        )

    def generate_invite_link(
        self,
        actor_user_id: str,
        actor_org_id: str,
        class_id: str,
        student_id: str,
    ) -> InviteLinkResponse:
        self._get_owned_class(class_id, actor_user_id, actor_org_id)
        if not self._repo.is_enrolled(class_id, student_id):
            raise StudentNotEnrolledError(
                f"Student '{student_id}' is not enrolled in class '{class_id}'."
            )
        # Idempotent: return existing active invite if one exists
        existing = self._repo.get_active_invite_link_for_student(class_id, student_id)
        if existing is not None:
            return InviteLinkResponse(
                invite_id=existing.invite_id,
                token=existing.token,
                url=f"{INVITE_URL_SCHEME}{existing.token}",
                student_id=existing.student_id,
                expires_at=existing.expires_at,
            )
        invite = self._repo.create_invite_link(
            org_id=actor_org_id,
            class_id=class_id,
            student_id=student_id,
            generated_by=actor_user_id,
        )
        return InviteLinkResponse(
            invite_id=invite.invite_id,
            token=invite.token,
            url=f"{INVITE_URL_SCHEME}{invite.token}",
            student_id=invite.student_id,
            expires_at=invite.expires_at,
        )

    def resolve_invite_link(self, token: str) -> InviteLinkResolveResponse:
        invite = self._repo.get_invite_link(token)
        if invite is None:
            raise InviteLinkNotFoundError(f"Invite link '{token}' not found.")
        now = datetime.now(UTC).isoformat()
        if invite.used_at is not None:
            return InviteLinkResolveResponse(
                valid=False,
                reason="already_used",
                student_name=None,
                class_name=None,
                subject=None,
            )
        if invite.expires_at < now:
            return InviteLinkResolveResponse(
                valid=False,
                reason="expired",
                student_name=None,
                class_name=None,
                subject=None,
            )
        student = self._repo.get_student(invite.student_id)
        cls = self._repo.get_class(invite.class_id)
        return InviteLinkResolveResponse(
            valid=True,
            reason=None,
            student_name=student.name if student else None,
            class_name=cls.name if cls else None,
            subject=cls.subject if cls else None,
        )

    def accept_invite_link(
        self,
        parent_user_id: str,
        parent_org_id: str,
        token: str,
    ) -> GuardianStudentLinkResponse:
        invite = self._repo.get_invite_link(token)
        if invite is None:
            raise InviteLinkInvalidError("Invite link not found or invalid.")
        if invite.org_id != parent_org_id:
            raise InviteLinkInvalidError(
                "Invite link is not valid for this organization."
            )
        now = datetime.now(UTC).isoformat()
        if invite.used_at is not None or invite.expires_at < now:
            raise InviteLinkInvalidError("Invite link is no longer valid.")
        if self._repo.is_parent_linked_to_student(parent_user_id, invite.student_id):
            raise AlreadyLinkedError("Already linked to this student.")
        guardian_link = self._repo.accept_invite_link(
            token=token,
            parent_user_id=parent_user_id,
            org_id=invite.org_id,
        )
        student = self._repo.get_student(invite.student_id)
        return GuardianStudentLinkResponse(
            link_id=guardian_link.link_id,
            student_id=guardian_link.student_id,
            student_name=student.name if student else "",
        )

    def get_linked_children(
        self,
        parent_user_id: str,
        org_id: str,
    ) -> list[LinkedChildResponse]:
        # get_guardian_links_for_parent returns ALL links for this parent (no org filter in repo)
        all_links = self._repo.get_guardian_links_for_parent(parent_user_id)
        # Must filter by org_id here — repo method does not do it
        links = [lnk for lnk in all_links if lnk.org_id == org_id]

        result = []
        for link in links:
            student = self._repo.get_student(link.student_id)
            if not student:
                continue
            # Find class via student's enrollment(s)
            enrollments = self._repo.get_enrollments_for_student(link.student_id)
            class_record = None
            if enrollments:
                class_record = self._repo.get_class(enrollments[0].class_id)
            result.append(
                LinkedChildResponse(
                    link_id=link.link_id,
                    student_id=link.student_id,
                    student_name=student.name,
                    class_name=class_record.name if class_record else None,
                    subject=class_record.subject if class_record else None,
                    consent_status=student.consent_status,
                )
            )
        return result

    def join_by_code(
        self,
        student_user_id: str,
        org_id: str,
        join_code: str,
    ) -> JoinCodeResponse:
        cls = self._repo.find_class_by_join_code(join_code.upper(), org_id)
        if cls is None:
            raise InvalidJoinCodeError(f"Invalid or expired join code '{join_code}'.")
        # Use auth user id directly for auth-user-linked students
        student_id = student_user_id
        if self._repo.is_enrolled(cls.class_id, student_id):
            raise AlreadyEnrolledError("Already enrolled in this class.")
        self._repo.join_class_by_code(
            join_code=join_code.upper(),
            student_user_id=student_user_id,
            org_id=org_id,
        )
        return JoinCodeResponse(
            class_id=cls.class_id,
            class_name=cls.name,
            subject=cls.subject,
        )

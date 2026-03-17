from __future__ import annotations

from dataclasses import dataclass

from app.domains.courses.repository import (
    InMemoryCoursesRepository,
    LessonDraftRecord,
    LessonDraftRevisionRecord,
)


class CourseDraftGenerationAccessError(Exception):
    pass


class CourseDraftGenerationProviderUnavailableError(Exception):
    pass


class CourseDraftNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class CourseDraft:
    draft_id: str
    org_id: str
    teacher_user_id: str
    class_id: str
    unit_title: str
    prompt: str
    generated_outline: list[str]
    suggested_assessments: list[str]
    revision: int
    base_draft_id: str | None
    student_id: str | None
    objectives: list[str]
    pacing_notes: str
    assessments: list[str]
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CourseDraftRevision:
    revision: int
    objectives: list[str]
    pacing_notes: str
    assessments: list[str]
    updated_by_user_id: str
    updated_at: str


class StubLessonDraftGenerator:
    def generate(self, unit_title: str, prompt: str, grade_level: str, subject: str) -> tuple[list[str], list[str]]:
        if "[simulate-provider-unavailable]" in prompt:
            raise CourseDraftGenerationProviderUnavailableError("Generation provider unavailable. Please retry.")
        outline = [
            f"Warm-up: Review prior {subject.lower()} concepts for grade {grade_level}",
            f"Core instruction: {unit_title}",
            f"Guided practice: Small-group problem solving",
            "Exit ticket: Quick mastery check",
        ]
        assessments = [
            "Formative quiz (5 questions)",
            "Short written reflection on strategy use",
        ]
        return outline, assessments


class CoursesService:
    def __init__(
        self,
        repository: InMemoryCoursesRepository,
        generator: StubLessonDraftGenerator | None = None,
    ) -> None:
        self._repository = repository
        self._generator = generator or StubLessonDraftGenerator()

    def generate_draft(
        self,
        actor_user_id: str,
        actor_org_id: str,
        class_id: str,
        prompt: str,
        unit_title: str,
    ) -> CourseDraft:
        class_context = self._repository.get_class_context(class_id)
        if class_context is None:
            raise CourseDraftGenerationAccessError("Forbidden")
        if class_context.org_id != actor_org_id:
            raise CourseDraftGenerationAccessError("Forbidden")
        if class_context.teacher_user_id != actor_user_id:
            raise CourseDraftGenerationAccessError("Forbidden")

        outline, assessments = self._generator.generate(
            unit_title=unit_title,
            prompt=prompt,
            grade_level=class_context.grade_level,
            subject=class_context.subject,
        )
        created = self._repository.create_lesson_draft(
            org_id=actor_org_id,
            teacher_user_id=actor_user_id,
            class_id=class_id,
            unit_title=unit_title,
            prompt=prompt,
            generated_outline=outline,
            suggested_assessments=assessments,
        )
        return self._to_course_draft(created)

    def get_draft(self, actor_user_id: str, actor_org_id: str, draft_id: str) -> CourseDraft:
        draft = self._repository.get_lesson_draft(draft_id)
        if draft is None:
            raise CourseDraftNotFoundError("Draft not found")
        if draft.org_id != actor_org_id or draft.teacher_user_id != actor_user_id:
            raise CourseDraftGenerationAccessError("Forbidden")
        return self._to_course_draft(draft)

    def list_drafts_for_teacher(self, actor_user_id: str, actor_org_id: str) -> list[CourseDraft]:
        drafts = self._repository.list_lesson_drafts_for_teacher(
            org_id=actor_org_id,
            teacher_user_id=actor_user_id,
        )
        return [self._to_course_draft(draft) for draft in drafts]

    def edit_draft(
        self,
        actor_user_id: str,
        actor_org_id: str,
        draft_id: str,
        objectives: list[str],
        pacing_notes: str,
        assessments: list[str],
    ) -> CourseDraft:
        draft = self._repository.get_lesson_draft(draft_id)
        if draft is None:
            raise CourseDraftGenerationAccessError("Forbidden")
        if draft.org_id != actor_org_id or draft.teacher_user_id != actor_user_id:
            raise CourseDraftGenerationAccessError("Forbidden")

        updated = self._repository.update_lesson_draft(
            draft_id=draft_id,
            updated_by_user_id=actor_user_id,
            objectives=objectives,
            pacing_notes=pacing_notes,
            assessments=assessments,
        )
        if updated is None:
            raise CourseDraftGenerationAccessError("Forbidden")
        return self._to_course_draft(updated)

    def create_student_variant(
        self,
        actor_user_id: str,
        actor_org_id: str,
        draft_id: str,
        student_id: str,
        objectives: list[str] | None,
        pacing_notes: str | None,
        assessments: list[str] | None,
    ) -> CourseDraft:
        base = self._repository.get_lesson_draft(draft_id)
        if base is None:
            raise CourseDraftGenerationAccessError("Forbidden")
        if base.org_id != actor_org_id or base.teacher_user_id != actor_user_id:
            raise CourseDraftGenerationAccessError("Forbidden")
        if base.student_id is not None:
            raise CourseDraftGenerationAccessError("Forbidden")

        student = self._repository.get_student_context(student_id)
        if student is None:
            raise CourseDraftGenerationAccessError("Forbidden")
        if student.org_id != actor_org_id or student.teacher_user_id != actor_user_id:
            raise CourseDraftGenerationAccessError("Forbidden")
        if student.class_id != base.class_id:
            raise CourseDraftGenerationAccessError("Forbidden")

        created = self._repository.create_student_variant(
            base_draft_id=draft_id,
            student_id=student_id,
            actor_user_id=actor_user_id,
            objectives=objectives if objectives is not None else list(base.objectives),
            pacing_notes=pacing_notes if pacing_notes is not None else base.pacing_notes,
            assessments=assessments if assessments is not None else list(base.assessments),
        )
        if created is None:
            raise CourseDraftGenerationAccessError("Forbidden")
        return self._to_course_draft(created)

    def list_revisions(self, actor_user_id: str, actor_org_id: str, draft_id: str) -> list[CourseDraftRevision]:
        draft = self._repository.get_lesson_draft(draft_id)
        if draft is None:
            raise CourseDraftGenerationAccessError("Forbidden")
        if draft.org_id != actor_org_id or draft.teacher_user_id != actor_user_id:
            raise CourseDraftGenerationAccessError("Forbidden")
        revisions = self._repository.list_draft_revisions(draft_id)
        return [self._to_course_draft_revision(revision) for revision in revisions]

    def _to_course_draft(self, draft: LessonDraftRecord) -> CourseDraft:
        return CourseDraft(
            draft_id=draft.draft_id,
            org_id=draft.org_id,
            teacher_user_id=draft.teacher_user_id,
            class_id=draft.class_id,
            unit_title=draft.unit_title,
            prompt=draft.prompt,
            generated_outline=list(draft.generated_outline),
            suggested_assessments=list(draft.suggested_assessments),
            revision=draft.revision,
            base_draft_id=draft.base_draft_id,
            student_id=draft.student_id,
            objectives=list(draft.objectives),
            pacing_notes=draft.pacing_notes,
            assessments=list(draft.assessments),
            status=draft.status,
            created_at=draft.created_at,
            updated_at=draft.updated_at,
        )

    def _to_course_draft_revision(self, revision: LessonDraftRevisionRecord) -> CourseDraftRevision:
        return CourseDraftRevision(
            revision=revision.revision,
            objectives=list(revision.objectives),
            pacing_notes=revision.pacing_notes,
            assessments=list(revision.assessments),
            updated_by_user_id=revision.updated_by_user_id,
            updated_at=revision.updated_at,
        )

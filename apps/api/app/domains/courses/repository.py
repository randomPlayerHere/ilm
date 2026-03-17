from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True)
class ClassContextRecord:
    class_id: str
    org_id: str
    teacher_user_id: str
    title: str
    grade_level: str
    subject: str


@dataclass(frozen=True)
class StudentContextRecord:
    student_id: str
    org_id: str
    teacher_user_id: str
    class_id: str


@dataclass(frozen=True)
class LessonDraftRevisionRecord:
    draft_id: str
    revision: int
    objectives: tuple[str, ...]
    pacing_notes: str
    assessments: tuple[str, ...]
    updated_by_user_id: str
    updated_at: str


@dataclass(frozen=True)
class LessonDraftRecord:
    draft_id: str
    org_id: str
    teacher_user_id: str
    class_id: str
    unit_title: str
    prompt: str
    generated_outline: tuple[str, ...]
    suggested_assessments: tuple[str, ...]
    revision: int
    base_draft_id: str | None
    student_id: str | None
    objectives: tuple[str, ...]
    pacing_notes: str
    assessments: tuple[str, ...]
    status: str
    created_at: str
    updated_at: str


class CoursesRepository(Protocol):
    def get_class_context(self, class_id: str) -> ClassContextRecord | None:
        ...

    def get_student_context(self, student_id: str) -> StudentContextRecord | None:
        ...

    def create_lesson_draft(
        self,
        org_id: str,
        teacher_user_id: str,
        class_id: str,
        unit_title: str,
        prompt: str,
        generated_outline: list[str],
        suggested_assessments: list[str],
    ) -> LessonDraftRecord:
        ...

    def get_lesson_draft(self, draft_id: str) -> LessonDraftRecord | None:
        ...

    def update_lesson_draft(
        self,
        draft_id: str,
        updated_by_user_id: str,
        objectives: list[str],
        pacing_notes: str,
        assessments: list[str],
    ) -> LessonDraftRecord | None:
        ...

    def create_student_variant(
        self,
        base_draft_id: str,
        student_id: str,
        actor_user_id: str,
        objectives: list[str],
        pacing_notes: str,
        assessments: list[str],
    ) -> LessonDraftRecord | None:
        ...

    def list_draft_revisions(self, draft_id: str) -> list[LessonDraftRevisionRecord]:
        ...

    def list_lesson_drafts_for_teacher(self, org_id: str, teacher_user_id: str) -> list[LessonDraftRecord]:
        ...


class InMemoryCoursesRepository:
    _classes: dict[str, ClassContextRecord] = {}
    _students: dict[str, StudentContextRecord] = {}
    _drafts: dict[str, LessonDraftRecord] = {}
    _revisions: dict[str, list[LessonDraftRevisionRecord]] = {}
    _draft_seq: int = 0
    _seeded: bool = False

    def __init__(self) -> None:
        self._ensure_seed_data()

    @classmethod
    def _ensure_seed_data(cls) -> None:
        if cls._seeded:
            return
        cls._seeded = True
        cls._classes = {
            "cls_demo_math_1": ClassContextRecord(
                class_id="cls_demo_math_1",
                org_id="org_demo_1",
                teacher_user_id="usr_teacher_1",
                title="Grade 6 Mathematics",
                grade_level="6",
                subject="Mathematics",
            ),
            "cls_other_org_1": ClassContextRecord(
                class_id="cls_other_org_1",
                org_id="org_other_1",
                teacher_user_id="usr_teacher_9",
                title="Grade 7 Science",
                grade_level="7",
                subject="Science",
            ),
        }
        cls._students = {
            "stu_demo_1": StudentContextRecord(
                student_id="stu_demo_1",
                org_id="org_demo_1",
                teacher_user_id="usr_teacher_1",
                class_id="cls_demo_math_1",
            ),
            "stu_other_org_1": StudentContextRecord(
                student_id="stu_other_org_1",
                org_id="org_other_1",
                teacher_user_id="usr_teacher_9",
                class_id="cls_other_org_1",
            ),
        }
        cls._drafts = {}
        cls._revisions = {}
        cls._draft_seq = 0

    @classmethod
    def reset_state(cls) -> None:
        cls._seeded = False
        cls._ensure_seed_data()

    def get_class_context(self, class_id: str) -> ClassContextRecord | None:
        return self.__class__._classes.get(class_id)

    def get_student_context(self, student_id: str) -> StudentContextRecord | None:
        return self.__class__._students.get(student_id)

    def create_lesson_draft(
        self,
        org_id: str,
        teacher_user_id: str,
        class_id: str,
        unit_title: str,
        prompt: str,
        generated_outline: list[str],
        suggested_assessments: list[str],
    ) -> LessonDraftRecord:
        self.__class__._draft_seq += 1
        draft_id = f"draft_{self.__class__._draft_seq}"
        now = datetime.now(UTC).isoformat()
        record = LessonDraftRecord(
            draft_id=draft_id,
            org_id=org_id,
            teacher_user_id=teacher_user_id,
            class_id=class_id,
            unit_title=unit_title,
            prompt=prompt,
            generated_outline=tuple(generated_outline),
            suggested_assessments=tuple(suggested_assessments),
            revision=1,
            base_draft_id=None,
            student_id=None,
            objectives=tuple(generated_outline),
            pacing_notes="Teacher-editable pacing notes",
            assessments=tuple(suggested_assessments),
            status="draft",
            created_at=now,
            updated_at=now,
        )
        self.__class__._drafts[draft_id] = record
        self.__class__._revisions[draft_id] = [
            LessonDraftRevisionRecord(
                draft_id=draft_id,
                revision=1,
                objectives=record.objectives,
                pacing_notes=record.pacing_notes,
                assessments=record.assessments,
                updated_by_user_id=teacher_user_id,
                updated_at=now,
            )
        ]
        return record

    def get_lesson_draft(self, draft_id: str) -> LessonDraftRecord | None:
        return self.__class__._drafts.get(draft_id)

    def update_lesson_draft(
        self,
        draft_id: str,
        updated_by_user_id: str,
        objectives: list[str],
        pacing_notes: str,
        assessments: list[str],
    ) -> LessonDraftRecord | None:
        existing = self.__class__._drafts.get(draft_id)
        if existing is None:
            return None
        now = datetime.now(UTC).isoformat()
        updated = LessonDraftRecord(
            draft_id=existing.draft_id,
            org_id=existing.org_id,
            teacher_user_id=existing.teacher_user_id,
            class_id=existing.class_id,
            unit_title=existing.unit_title,
            prompt=existing.prompt,
            generated_outline=existing.generated_outline,
            suggested_assessments=existing.suggested_assessments,
            revision=existing.revision + 1,
            base_draft_id=existing.base_draft_id,
            student_id=existing.student_id,
            objectives=tuple(objectives),
            pacing_notes=pacing_notes,
            assessments=tuple(assessments),
            status="draft",
            created_at=existing.created_at,
            updated_at=now,
        )
        self.__class__._drafts[draft_id] = updated
        history = self.__class__._revisions.setdefault(draft_id, [])
        history.append(
            LessonDraftRevisionRecord(
                draft_id=draft_id,
                revision=updated.revision,
                objectives=updated.objectives,
                pacing_notes=updated.pacing_notes,
                assessments=updated.assessments,
                updated_by_user_id=updated_by_user_id,
                updated_at=now,
            )
        )
        return updated

    def create_student_variant(
        self,
        base_draft_id: str,
        student_id: str,
        actor_user_id: str,
        objectives: list[str],
        pacing_notes: str,
        assessments: list[str],
    ) -> LessonDraftRecord | None:
        base = self.__class__._drafts.get(base_draft_id)
        if base is None:
            return None
        self.__class__._draft_seq += 1
        draft_id = f"draft_{self.__class__._draft_seq}"
        now = datetime.now(UTC).isoformat()
        variant = LessonDraftRecord(
            draft_id=draft_id,
            org_id=base.org_id,
            teacher_user_id=base.teacher_user_id,
            class_id=base.class_id,
            unit_title=base.unit_title,
            prompt=base.prompt,
            generated_outline=base.generated_outline,
            suggested_assessments=base.suggested_assessments,
            revision=1,
            base_draft_id=base_draft_id,
            student_id=student_id,
            objectives=tuple(objectives),
            pacing_notes=pacing_notes,
            assessments=tuple(assessments),
            status="draft",
            created_at=now,
            updated_at=now,
        )
        self.__class__._drafts[draft_id] = variant
        self.__class__._revisions[draft_id] = [
            LessonDraftRevisionRecord(
                draft_id=draft_id,
                revision=1,
                objectives=variant.objectives,
                pacing_notes=variant.pacing_notes,
                assessments=variant.assessments,
                updated_by_user_id=actor_user_id,
                updated_at=now,
            )
        ]
        return variant

    def list_draft_revisions(self, draft_id: str) -> list[LessonDraftRevisionRecord]:
        return list(self.__class__._revisions.get(draft_id, []))

    def list_lesson_drafts_for_teacher(self, org_id: str, teacher_user_id: str) -> list[LessonDraftRecord]:
        drafts = [
            draft
            for draft in self.__class__._drafts.values()
            if draft.org_id == org_id and draft.teacher_user_id == teacher_user_id
        ]
        drafts.sort(key=lambda draft: draft.created_at)
        return drafts

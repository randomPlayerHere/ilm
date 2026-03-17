from __future__ import annotations

import pytest

from app.domains.courses.service import (
    CourseDraftGenerationAccessError,
    CoursesService,
    CourseDraftGenerationProviderUnavailableError,
)
from app.domains.courses.repository import (
    ClassContextRecord,
    InMemoryCoursesRepository,
    StudentContextRecord,
)


def setup_function() -> None:
    InMemoryCoursesRepository.reset_state()


def test_generate_draft_persists_teacher_owned_draft_state() -> None:
    service = CoursesService(repository=InMemoryCoursesRepository())

    created = service.generate_draft(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        class_id="cls_demo_math_1",
        prompt="Create a multiplication lesson",
        unit_title="Multiplication Foundations",
    )

    assert created.status == "draft"
    assert created.org_id == "org_demo_1"
    assert created.teacher_user_id == "usr_teacher_1"
    assert created.class_id == "cls_demo_math_1"

    fetched = service.get_draft(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        draft_id=created.draft_id,
    )
    assert fetched.draft_id == created.draft_id


def test_generate_draft_rejects_cross_tenant_class_access() -> None:
    service = CoursesService(repository=InMemoryCoursesRepository())

    with pytest.raises(CourseDraftGenerationAccessError):
        service.generate_draft(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            class_id="cls_other_org_1",
            prompt="Create lesson",
            unit_title="Unit",
        )


def test_generation_provider_failure_is_retryable_and_no_record_written() -> None:
    service = CoursesService(repository=InMemoryCoursesRepository())

    with pytest.raises(CourseDraftGenerationProviderUnavailableError):
        service.generate_draft(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            class_id="cls_demo_math_1",
            prompt="[simulate-provider-unavailable]",
            unit_title="Unit",
        )

    assert service.list_drafts_for_teacher(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
    ) == []


def test_edit_draft_tracks_revision_and_keeps_draft_state() -> None:
    service = CoursesService(repository=InMemoryCoursesRepository())
    created = service.generate_draft(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        class_id="cls_demo_math_1",
        prompt="Create a multiplication lesson",
        unit_title="Multiplication Foundations",
    )

    edited = service.edit_draft(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        draft_id=created.draft_id,
        objectives=["Master multiplication facts", "Apply area models"],
        pacing_notes="2x 40-minute sessions",
        assessments=["Exit ticket", "Quick quiz"],
    )

    assert edited.status == "draft"
    assert edited.revision == 2
    assert edited.objectives == ["Master multiplication facts", "Apply area models"]
    assert edited.pacing_notes == "2x 40-minute sessions"
    assert edited.assessments == ["Exit ticket", "Quick quiz"]
    assert len(service.list_revisions(actor_user_id="usr_teacher_1", actor_org_id="org_demo_1", draft_id=created.draft_id)) == 2


def test_create_student_variant_links_base_and_keeps_records_distinct() -> None:
    service = CoursesService(repository=InMemoryCoursesRepository())
    base = service.generate_draft(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        class_id="cls_demo_math_1",
        prompt="Create a multiplication lesson",
        unit_title="Multiplication Foundations",
    )
    edited_base = service.edit_draft(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        draft_id=base.draft_id,
        objectives=["Base objective"],
        pacing_notes="base pace",
        assessments=["Base assessment"],
    )
    assert edited_base.objectives == ["Base objective"]

    variant = service.create_student_variant(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        draft_id=base.draft_id,
        student_id="stu_demo_1",
        objectives=["Variant objective"],
        pacing_notes="1:1 session",
        assessments=["Oral check"],
    )

    assert variant.base_draft_id == base.draft_id
    assert variant.student_id == "stu_demo_1"
    assert variant.objectives == ["Variant objective"]
    assert variant.status == "draft"

    reloaded_base = service.get_draft(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        draft_id=base.draft_id,
    )
    assert reloaded_base.objectives == ["Base objective"]


def test_create_student_variant_rejects_variant_of_variant() -> None:
    service = CoursesService(repository=InMemoryCoursesRepository())
    base = service.generate_draft(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        class_id="cls_demo_math_1",
        prompt="Create a multiplication lesson",
        unit_title="Multiplication Foundations",
    )
    first_variant = service.create_student_variant(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        draft_id=base.draft_id,
        student_id="stu_demo_1",
        objectives=None,
        pacing_notes=None,
        assessments=None,
    )
    assert first_variant.base_draft_id == base.draft_id

    with pytest.raises(CourseDraftGenerationAccessError):
        service.create_student_variant(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            draft_id=first_variant.draft_id,
            student_id="stu_demo_1",
            objectives=None,
            pacing_notes=None,
            assessments=None,
        )


def test_list_drafts_for_teacher_includes_student_variants() -> None:
    service = CoursesService(repository=InMemoryCoursesRepository())
    base = service.generate_draft(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        class_id="cls_demo_math_1",
        prompt="Create a multiplication lesson",
        unit_title="Multiplication Foundations",
    )
    service.create_student_variant(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        draft_id=base.draft_id,
        student_id="stu_demo_1",
        objectives=None,
        pacing_notes=None,
        assessments=None,
    )

    all_drafts = service.list_drafts_for_teacher(actor_user_id="usr_teacher_1", actor_org_id="org_demo_1")
    assert len(all_drafts) == 2
    generic = [d for d in all_drafts if d.student_id is None]
    variants = [d for d in all_drafts if d.student_id is not None]
    assert len(generic) == 1
    assert len(variants) == 1
    assert variants[0].base_draft_id == base.draft_id


def test_create_student_variant_rejects_student_from_other_class_context() -> None:
    repository = InMemoryCoursesRepository()
    repository.__class__._classes["cls_demo_science_2"] = ClassContextRecord(
        class_id="cls_demo_science_2",
        org_id="org_demo_1",
        teacher_user_id="usr_teacher_1",
        title="Grade 6 Science",
        grade_level="6",
        subject="Science",
    )
    repository.__class__._students["stu_demo_science_2"] = StudentContextRecord(
        student_id="stu_demo_science_2",
        org_id="org_demo_1",
        teacher_user_id="usr_teacher_1",
        class_id="cls_demo_science_2",
    )
    service = CoursesService(repository=repository)
    base = service.generate_draft(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        class_id="cls_demo_math_1",
        prompt="Create a multiplication lesson",
        unit_title="Multiplication Foundations",
    )

    with pytest.raises(CourseDraftGenerationAccessError):
        service.create_student_variant(
            actor_user_id="usr_teacher_1",
            actor_org_id="org_demo_1",
            draft_id=base.draft_id,
            student_id="stu_demo_science_2",
            objectives=["Variant objective"],
            pacing_notes="1:1 session",
            assessments=["Oral check"],
        )

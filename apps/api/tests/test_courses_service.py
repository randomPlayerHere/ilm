from __future__ import annotations

import pytest

from app.domains.courses.service import (
    CourseDraftGenerationAccessError,
    CoursesService,
    CourseDraftGenerationProviderUnavailableError,
)
from app.domains.courses.repository import InMemoryCoursesRepository


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

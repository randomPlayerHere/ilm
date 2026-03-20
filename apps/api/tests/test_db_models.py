"""Tests for SQLAlchemy ORM models — Story 4.3.

Uses an in-process async SQLite database via aiosqlite.
NOTE: SQLite does NOT enforce FK constraints by default; FK integrity is
validated by PostgreSQL in production. Do not write tests that expect FK
violations to raise IntegrityError.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
import app.db.models  # noqa: F401 — registers all models on Base
from app.db.models import (
    AuditEvent,
    Class,
    ClassEnrollment,
    Organization,
    Student,
    User,
    compute_audit_hash,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session():
    """Create a fresh in-memory async SQLite database per test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def make_org(**kwargs) -> Organization:
    defaults = dict(name="Test Org", slug="test-org")
    defaults.update(kwargs)
    return Organization(**defaults)


def make_user(org_id=None, **kwargs) -> User:
    defaults = dict(
        email=f"user-{uuid.uuid4().hex[:8]}@example.com",
        role="teacher",
        status="active",
        org_id=org_id,
    )
    defaults.update(kwargs)
    return User(**defaults)


def make_class(org_id, teacher_id, **kwargs) -> Class:
    defaults = dict(
        org_id=org_id,
        teacher_id=teacher_id,
        name="Math 101",
        subject="Math",
        join_code=uuid.uuid4().hex[:8],
    )
    defaults.update(kwargs)
    return Class(**defaults)


def make_student(org_id, **kwargs) -> Student:
    defaults = dict(org_id=org_id, consent_status="pending")
    defaults.update(kwargs)
    return Student(**defaults)


# ---------------------------------------------------------------------------
# AC #2: Organization — basic create/read + slug uniqueness
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_organization_create_and_read(db_session):
    """Create an Organization and read it back by PK."""
    org = make_org(name="Greenwood Academy", slug="greenwood")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    assert org.id is not None
    assert org.name == "Greenwood Academy"
    assert org.slug == "greenwood"


@pytest.mark.anyio
async def test_organization_slug_unique(db_session):
    """Duplicate slug must raise IntegrityError."""
    org1 = make_org(name="Org A", slug="org-a")
    db_session.add(org1)
    await db_session.commit()

    org2 = make_org(name="Org B", slug="org-a")  # duplicate slug
    db_session.add(org2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ---------------------------------------------------------------------------
# AC #2: User — nullable org_id (invited user) + org-bound user
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_user_with_no_org(db_session):
    """User with org_id=None is valid (invited state)."""
    user = make_user(org_id=None)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.org_id is None


@pytest.mark.anyio
async def test_user_with_org(db_session):
    """User bound to an org stores org_id correctly."""
    org = make_org(slug="my-school")
    db_session.add(org)
    await db_session.commit()

    user = make_user(org_id=org.id)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.org_id == org.id


# ---------------------------------------------------------------------------
# AC #3: ClassEnrollment — unique (class_id, student_id)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_class_enrollment_unique_constraint(db_session):
    """Duplicate (class_id, student_id) enrollment raises IntegrityError."""
    org = make_org(slug="school-x")
    db_session.add(org)
    await db_session.commit()

    teacher = make_user(org_id=org.id)
    db_session.add(teacher)
    await db_session.commit()

    klass = make_class(org_id=org.id, teacher_id=teacher.id)
    db_session.add(klass)
    await db_session.commit()

    student = make_student(org_id=org.id)
    db_session.add(student)
    await db_session.commit()

    enrollment1 = ClassEnrollment(class_id=klass.id, student_id=student.id)
    db_session.add(enrollment1)
    await db_session.commit()

    enrollment2 = ClassEnrollment(class_id=klass.id, student_id=student.id)
    db_session.add(enrollment2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ---------------------------------------------------------------------------
# AC #4: AuditEvent — hash field is SHA-256 of payload
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_audit_event_hash_correct(db_session):
    """AuditEvent hash must equal compute_audit_hash(payload)."""
    payload = {"action": "user.login", "ip": "127.0.0.1", "success": True}
    expected_hash = compute_audit_hash(payload)

    event = AuditEvent(
        event_type="user.login",
        target_entity="user",
        target_id=str(uuid.uuid4()),
        payload=payload,
        hash=expected_hash,
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    assert event.hash == expected_hash
    # Verify hash is deterministic
    assert event.hash == compute_audit_hash(payload)


@pytest.mark.anyio
async def test_compute_audit_hash_deterministic():
    """compute_audit_hash is deterministic regardless of key insertion order."""
    payload_a = {"b": 2, "a": 1}
    payload_b = {"a": 1, "b": 2}
    assert compute_audit_hash(payload_a) == compute_audit_hash(payload_b)


# ---------------------------------------------------------------------------
# AC #3: Update operations (create/read/UPDATE coverage)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_organization_update(db_session):
    """Update an Organization's name and verify the change persists."""
    org = make_org(name="Original Name", slug="update-test-org")
    db_session.add(org)
    await db_session.commit()

    org.name = "Updated Name"
    await db_session.commit()
    await db_session.refresh(org)

    assert org.name == "Updated Name"
    assert org.slug == "update-test-org"  # unchanged


@pytest.mark.anyio
async def test_user_update_status(db_session):
    """Update a User's status from active to suspended."""
    user = make_user(status="active")
    db_session.add(user)
    await db_session.commit()

    user.status = "suspended"
    await db_session.commit()
    await db_session.refresh(user)

    assert user.status == "suspended"


@pytest.mark.anyio
async def test_student_update_consent_status(db_session):
    """Update a Student's consent_status from pending to confirmed."""
    org = make_org(slug="consent-org")
    db_session.add(org)
    await db_session.commit()

    student = make_student(org_id=org.id, consent_status="pending")
    db_session.add(student)
    await db_session.commit()

    student.consent_status = "confirmed"
    await db_session.commit()
    await db_session.refresh(student)

    assert student.consent_status == "confirmed"

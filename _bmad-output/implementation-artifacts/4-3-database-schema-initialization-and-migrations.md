# Story 4.3: Database Schema Initialization and Migrations

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want all core database tables created via versioned Alembic migrations,
so that application code can persist and query data from the first story onward.

## Acceptance Criteria

1. **Core tables created by Alembic migration:**
   - Running `alembic upgrade head` against a fresh PostgreSQL instance creates all tables: `organizations`, `users`, `user_org_memberships`, `classes`, `students`, `class_enrollments`, `parent_student_links`, `consent_records`, `audit_events`
   - All tables with tenant-scoped data include an `org_id` column with a foreign key to `organizations`
   - Row-level org isolation is enforceable via query filters (no RLS required in MVP, but `org_id` filter is the pattern)

2. **SQLAlchemy ORM models map correctly to tables:**
   - All SQLAlchemy models use SQLAlchemy 2.0 declarative style: `DeclarativeBase`, `Mapped[]`, `mapped_column()`
   - Models are importable from `app/db/models.py` (single module for Story 4.3 scope)
   - All models registered on the shared `Base` from `app/db/base.py`

3. **CRUD operations work in automated tests:**
   - Test suite verifies basic create/read/update for: `organizations`, `users`, `classes`, `students`, `class_enrollments`
   - Tests use an in-process SQLite or a real async PostgreSQL database (asyncpg-compatible test DB)
   - Zero regressions: all existing ~294 API tests continue to pass

4. **audit_events table is append-only:**
   - Schema includes: `event_type`, `actor_id`, `target_entity`, `target_id`, `org_id`, `timestamp`, `payload` (JSONB), `hash` (tamper-evidence SHA-256 of payload)
   - Application role (the DB user used by the API) has INSERT only — no UPDATE or DELETE on `audit_events`
   - The migration grants and revokes appropriate permissions for the app user

5. **Incremental migration support:**
   - A second migration (`0003_*`) can be generated on top of the core schema and applied via `alembic upgrade head` without error
   - `alembic downgrade -1` rolls back the most recent migration without error

6. **Existing in-memory repositories are NOT broken:**
   - Existing `InMemoryAuthRepository` and all other in-memory repos are left intact
   - Adding SQLAlchemy models is purely additive — no existing service or domain code is modified
   - All 294+ existing tests pass with zero regressions

## Tasks / Subtasks

- [ ] Task 1: Create `app/db/models.py` with all core SQLAlchemy ORM models (AC: #1, #2)
  - [ ] Import `Base` from `app.db.base` (already defined with `DeclarativeBase`)
  - [ ] Define `Organization` model: `id` (UUID PK), `name` (str), `slug` (str, unique), `settings` (JSON, nullable), `created_at` (datetime, server_default)
  - [ ] Define `User` model: `id` (UUID PK), `org_id` (UUID FK → organizations.id), `email` (str, unique), `password_hash` (str, nullable), `google_id` (str, nullable, unique), `role` (str), `status` (str), `created_at` (datetime, server_default)
  - [ ] Define `UserOrgMembership` model: `id` (UUID PK), `user_id` (UUID FK → users.id), `org_id` (UUID FK → organizations.id), `role` (str), `status` (str), `created_at` (datetime, server_default) — unique on (user_id, org_id)
  - [ ] Define `Class` model (table name `classes`): `id` (UUID PK), `org_id` (UUID FK → organizations.id), `teacher_id` (UUID FK → users.id), `name` (str), `subject` (str), `state_standard` (str, nullable), `join_code` (str, unique), `created_at` (datetime, server_default)
  - [ ] Define `Student` model: `id` (UUID PK), `org_id` (UUID FK → organizations.id), `grade_level` (str, nullable), `profile` (JSON, nullable), `consent_status` (str, default `pending`), `consent_confirmed_by` (UUID FK → users.id, nullable), `consent_confirmed_at` (datetime, nullable), `created_at` (datetime, server_default)
  - [ ] Define `ClassEnrollment` model (table name `class_enrollments`): `id` (UUID PK), `class_id` (UUID FK → classes.id), `student_id` (UUID FK → students.id), `enrolled_at` (datetime, server_default) — unique on (class_id, student_id)
  - [ ] Define `ParentStudentLink` model (table name `parent_student_links`): `id` (UUID PK), `parent_user_id` (UUID FK → users.id), `student_id` (UUID FK → students.id), `linked_via` (str, nullable), `created_at` (datetime, server_default) — unique on (parent_user_id, student_id)
  - [ ] Define `ConsentRecord` model (table name `consent_records`): `id` (UUID PK), `student_id` (UUID FK → students.id), `org_id` (UUID FK → organizations.id), `confirmed_by` (UUID FK → users.id), `status` (str), `confirmed_at` (datetime), `created_at` (datetime, server_default)
  - [ ] Define `AuditEvent` model (table name `audit_events`): `id` (UUID PK), `org_id` (UUID FK → organizations.id, nullable — system events may have no org), `actor_id` (UUID FK → users.id, nullable), `event_type` (str), `target_entity` (str), `target_id` (str), `payload` (JSON), `hash` (str — SHA-256 of serialized payload), `timestamp` (datetime, server_default = NOW, index=True)
  - [ ] Add DB-level indexes per architecture naming: `idx_users_org_id`, `idx_users_email`, `idx_classes_org_id`, `idx_students_org_id`, `idx_class_enrollments_class_id`, `idx_class_enrollments_student_id`, `idx_audit_events_org_id`, `idx_audit_events_actor_id`, `idx_audit_events_timestamp`

- [ ] Task 2: Generate Alembic migration `0002_core_schema.py` (AC: #1, #4, #5)
  - [ ] Run `alembic revision --autogenerate -m "core_schema"` from `apps/api/` — Alembic reads from `Base.metadata` (must import all models in `env.py`)
  - [ ] Update `apps/api/alembic/env.py` to import `app.db.models` so all models are registered before autogenerate runs: add `import app.db.models  # noqa: F401` after Base import
  - [ ] Review generated migration for correctness — verify all 9 tables, correct FK references, indexes
  - [ ] Add `audit_events` permission statements at end of `upgrade()`:
    ```python
    op.execute("REVOKE UPDATE, DELETE ON audit_events FROM ilm_app")
    op.execute("GRANT INSERT, SELECT ON audit_events TO ilm_app")
    ```
  - [ ] Add corresponding `downgrade()` logic to reverse permission changes
  - [ ] Verify `alembic upgrade head` runs cleanly against local PostgreSQL (`docker compose up -d postgres && alembic upgrade head`)
  - [ ] Verify `alembic downgrade -1` rolls back cleanly

- [ ] Task 3: Write tests for core model CRUD operations (AC: #3)
  - [ ] Create `apps/api/tests/test_db_models.py`
  - [ ] Use `pytest-anyio` (or existing `pytest` + `asyncio`) with an async SQLite fixture: `create_async_engine("sqlite+aiosqlite:///:memory:")`, `await conn.run_sync(Base.metadata.create_all)`
  - [ ] Add `aiosqlite` to `[dev]` dependencies in `pyproject.toml` (test-only)
  - [ ] Test: create Organization, read back by PK — verify slug uniqueness constraint raises on duplicate
  - [ ] Test: create User with org_id FK — verify FK constraint enforced
  - [ ] Test: create Class + Student + ClassEnrollment — verify unique constraint on (class_id, student_id)
  - [ ] Test: create AuditEvent — verify `hash` field is populated (application-layer SHA-256 of `payload` JSON)
  - [ ] All new tests use `pytest.mark.anyio` (or equivalent) for async test execution

- [ ] Task 4: Verify zero regressions (AC: #6)
  - [ ] Run full test suite: `cd apps/api && python -m pytest tests/ -v`
  - [ ] Confirm all ~294 existing tests pass — zero regressions allowed
  - [ ] New test file adds ≥ 5 tests covering the models
  - [ ] Confirm `app/db/models.py` import does not conflict with existing `app/domains/auth/models.py` (different module paths — no naming clash)

## Dev Notes

### Critical: In-Memory Repositories Stay Intact

The existing `InMemoryAuthRepository` and all other in-memory repositories (`InMemoryAuthRepository`, courses `repository.py`, grading `repository.py`, students `repository.py`, notifications `repository.py`) **must not be touched**. Story 4.3 is purely additive:
- Creates new `app/db/models.py` module (SQLAlchemy ORM)
- Generates Alembic migration `0002_core_schema.py`
- Adds model-level tests

**Do NOT wire SQLAlchemy models to existing services or routers in this story.** The in-memory repos remain the live path — SQLAlchemy-backed repos come in future stories.

### Current Alembic Setup (from Story 4.2)

The scaffold is already complete. Story 4.3 only adds migration `0002`:

```
apps/api/
├── alembic.ini                     # Already configured (points to apps/api/alembic/)
├── alembic/
│   ├── env.py                      # Already configured with async bridge pattern
│   ├── script.py.mako              # Alembic template
│   └── versions/
│       ├── 0001_initial.py         # Baseline no-op migration (already exists)
│       └── 0002_core_schema.py     # THIS STORY creates this file
└── app/
    └── db/
        ├── base.py                 # Base = DeclarativeBase() + async engine (exists)
        ├── session.py              # AsyncSession FastAPI dependency (exists)
        └── models.py               # NEW: all ORM models go here
```

### SQLAlchemy 2.0 Model Pattern

Use strict 2.0 declarative style throughout — **not** legacy `Column(Integer, ...)` style:

```python
# app/db/models.py  — pattern to follow
from __future__ import annotations
import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

**SQLite compatibility for tests:** Use `JSON` (not `JSONB`) when targeting SQLite in tests, or configure `render_as_batch=True` in the test engine. The production migration uses `JSONB` for PostgreSQL. For the test fixture, use `JSON` fallback or mock the column type.

**Recommended approach for test SQLite compatibility:** define a type alias at top of `models.py`:

```python
from sqlalchemy import JSON
# Use JSON for portability; PostgreSQL will still store as JSONB via alembic migration explicitly
```

Or override in test fixtures — pick one approach and be consistent.

### audit_events Hash Field

The `hash` column is a SHA-256 of the serialized `payload` JSON. It is computed at the **application layer** before INSERT — the DB stores the hash but does not compute it. Implementation for reference:

```python
import hashlib, json

def compute_audit_hash(payload: dict) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()
```

Tests should verify this hash is present on AuditEvent records.

### DB User / Role for Permissions

The local `.env.example` uses `ilm_app` as the application DB user (set `POSTGRES_USER=ilm_app` in docker-compose). If the current `docker-compose.yml` uses a different user, **check `.env.example` before writing the GRANT/REVOKE statements** — the DB user name must match exactly.

From Story 4.2: `DATABASE_URL=postgresql+asyncpg://ilm:ilm@postgres:5432/ilm` — so the application user is `ilm`. Use `ilm` in `GRANT/REVOKE` statements:

```python
op.execute("REVOKE UPDATE, DELETE ON audit_events FROM ilm")
op.execute("GRANT INSERT, SELECT ON audit_events TO ilm")
```

If the database user does not yet have a restricted permission set, this is a no-op operationally but establishes the intent in the migration for future enforcement.

### Architecture Domain Model — Story 4.3 Scope

Story 4.3 creates the **bootstrap tables** only. Subsequent stories add more tables as needed:

| Table | Story | Notes |
|---|---|---|
| `organizations` | **4.3** | Tenant root |
| `users` | **4.3** | Auth + identity |
| `user_org_memberships` | **4.3** | Role + org binding |
| `classes` | **4.3** | Teacher's classes |
| `students` | **4.3** | Student records (with consent_status) |
| `class_enrollments` | **4.3** | Student ↔ Class link |
| `parent_student_links` | **4.3** | Parent ↔ Student link |
| `consent_records` | **4.3** | COPPA consent audit trail |
| `audit_events` | **4.3** | Append-only audit log |
| `invite_links` | 4.8 | Invite link flow |
| `courses`, `assignments`, `submissions` | Epic 5/6 | Grading pipeline |
| `grades`, `grade_versions` | Epic 5 | Immutable grade ledger |
| `messages`, `threads` | Epic 8 | Messaging |
| `notifications`, `notification_preferences`, `device_tokens` | Epic 8 | Push / notifications |

**Do NOT create courses, assignments, submissions, grades, or messaging tables in this story.**

### Naming Conventions (MANDATORY — from Architecture doc)

- Tables: `snake_case` plural — `organizations`, `users`, `class_enrollments`, `parent_student_links`, `audit_events`
- Columns: `snake_case` — `org_id`, `created_at`, `consent_confirmed_at`
- PK: always `id`; FK always `<entity>_id`
- Indexes: `idx_<table>_<column>` — e.g., `idx_users_org_id`, `idx_audit_events_timestamp`
- Unique constraints: `uq_<table>_<columns>` — e.g., `uq_class_enrollments_class_student`

### Test Async Setup

The project uses `pytest` + `httpx` for API tests. For model-level async tests, use `pytest-anyio` or `anyio` + `asyncio` mode. Check if `anyio` is already a transitive dependency — if so, use `pytest.mark.anyio`. If not, add `pytest-anyio` to dev dependencies.

Async SQLite test fixture pattern:

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.base import Base
import app.db.models  # noqa: F401 — ensures all models registered on Base

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()
```

### Project Structure Notes

New files this story creates:

```
apps/api/
├── alembic/versions/0002_core_schema.py     # NEW: core schema migration
└── app/
    └── db/
        └── models.py                         # NEW: all SQLAlchemy ORM models
apps/api/tests/
└── test_db_models.py                         # NEW: model CRUD tests
```

Modified files:

```
apps/api/alembic/env.py         # Add: import app.db.models (model registration for autogenerate)
apps/api/pyproject.toml         # Add: aiosqlite to [dev] dependencies (for SQLite test fixture)
apps/api/uv.lock                # Regenerated after pyproject.toml change
```

**No other files should be modified.** In particular:
- Do NOT modify `app/domains/auth/models.py` (in-memory dataclasses — separate from SQLAlchemy models)
- Do NOT modify any existing domain service, router, or repository
- Do NOT modify `app/db/base.py` or `app/db/session.py`
- Do NOT modify `app/core/settings.py`

### Alembic env.py — Model Registration

After autogenerate, verify `apps/api/alembic/env.py` includes the models import. The existing `env.py` from Story 4.2 uses the async bridge pattern. Add the models import near the top:

```python
from app.db.base import Base
import app.db.models  # noqa: F401 — registers all models on Base.metadata for autogenerate

target_metadata = Base.metadata
```

This must be in place **before** running `alembic revision --autogenerate`.

### Technology Versions (from Story 4.2 established baseline)

- **SQLAlchemy:** `>=2.0,<3.0` (already installed). Use `Mapped[]` + `mapped_column()` — 2.0 declarative style only.
- **Alembic:** `>=1.13,<2.0` (already installed). `alembic revision --autogenerate -m "core_schema"` generates `0002_core_schema.py` with revision id auto-assigned.
- **asyncpg:** `>=0.30.0,<0.32.0` (already installed). Production migration uses `postgresql+asyncpg://` connection string.
- **aiosqlite:** Add `aiosqlite>=0.20,<0.21` to `[project.optional-dependencies.dev]` in `pyproject.toml` — for test-only async SQLite support. Run `uv lock` after adding (or `pip install aiosqlite` locally for test verification).

### UUID Strategy

Use Python `uuid.uuid4()` as the default for all PKs. In PostgreSQL, store as `UUID` type. In the test SQLite fixture, UUID is stored as `CHAR(32)` — this is handled transparently by SQLAlchemy when `UUID(as_uuid=True)` is specified.

Alternative: use `String(36)` for cross-DB compatibility in models, but UUID type is preferred for PostgreSQL production use.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.3] — Story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/architecture.md#Core Domain Model (MVP)] — Full domain model field specs
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture] — SQLAlchemy, Alembic, PostgreSQL patterns
- [Source: _bmad-output/planning-artifacts/architecture.md#Naming Patterns (Database)] — Table/column/index naming rules
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security] — COPPA consent gate, audit log requirements
- [Source: _bmad-output/implementation-artifacts/4-2-local-infrastructure-with-docker-compose.md#Dev Notes] — Alembic setup, SQLAlchemy version guidance, DB user (`ilm`), existing repo patterns to preserve

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (claude-sonnet-4-6)

### Debug Log References

### Completion Notes List

### File List

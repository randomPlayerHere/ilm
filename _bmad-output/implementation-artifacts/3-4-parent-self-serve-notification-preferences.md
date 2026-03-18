# Story 3.4: Parent Self-Serve Notification Preferences

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a parent,
I want to configure update preferences by event type and cadence,
so that I stay informed without alert fatigue.

## Acceptance Criteria

1. **Given** a parent opens notification settings **When** they select event types and cadence (instant/daily/weekly/off) **Then** preferences are saved successfully **And** applied within the required propagation window (i.e., persisted immediately and readable by subsequent requests).

2. **Given** preferences are updated **When** new eligible events occur **Then** delivery follows the latest saved preferences (i.e., the stored preferences reflect the most recent PUT at time of retrieval).

3. **Given** a parent has no saved preferences **When** they GET their notification preferences **Then** the response returns a well-formed preferences list (default cadence: "off" for all event types, or empty list — confirm which with the epics AC intent; see Dev Notes).

4. **Given** an invalid cadence value (not one of: instant/daily/weekly/off) **When** a PUT is submitted **Then** the API returns 422 Unprocessable Entity.

5. **Given** any non-parent role (student, teacher, admin, principal) **When** they access notification preference endpoints **Then** the response is 403 Forbidden.

6. **Given** an unauthenticated request **When** notification preference endpoints are accessed **Then** the response is 401 Unauthorized.

7. **Given** a parent in org A **When** they access notification preferences **Then** only their own org-scoped preferences are visible (org isolation enforced).

## Tasks / Subtasks

- [x] Task 1: Create `notifications` domain (AC: 1, 2, 3)
  - [x] Create `apps/api/app/domains/notifications/__init__.py` (empty)
  - [x] Create `apps/api/app/domains/notifications/repository.py` with `NotificationPreferenceRecord` dataclass and `InMemoryNotificationPreferencesRepository`
  - [x] Create `apps/api/app/domains/notifications/schemas.py` with `NotificationPreferenceItem`, `NotificationPreferencesResponse`, `NotificationPreferencesUpdateRequest`
  - [x] Create `apps/api/app/domains/notifications/router.py` with `GET /notifications/preferences` and `PUT /notifications/preferences`

- [x] Task 2: Register notifications router in main.py (AC: 1, 2)
  - [x] Import and include `notifications_router` in `apps/api/app/main.py`
  - [x] Update `apps/api/README.md` Story Scope section to list new endpoints

- [x] Task 3: Write tests (AC: 1–7)
  - [x] Create `apps/api/tests/test_notifications_api.py`
  - [x] Test 1: Parent can GET default preferences (200, well-formed response)
  - [x] Test 2: Parent can PUT preferences for a single event type (200, saved)
  - [x] Test 3: GET returns updated preferences after PUT
  - [x] Test 4: Student role → 403
  - [x] Test 5: Teacher role → 403
  - [x] Test 6: Unauthenticated → 401
  - [x] Test 7: Invalid cadence → 422
  - [x] Test 8: Org isolation — preferences are user+org scoped
  - [x] Test 9: Multiple event types configured independently (PUT grade_approved:weekly + recommendation_confirmed:daily → GET returns both)
  - [x] Test 10: NFR-001 performance — p95 latency ≤ 700ms for GET and PUT

## Dev Notes

### Scope Boundary — This Story vs. Epic 4

**This story creates preference persistence only.** No notification delivery, no email/push/SMS dispatch, no background worker. The delivery engine is Epic 4 (stories 4.3 and 4.4). The "propagation window" AC means preferences must be persisted (immediately in-memory) so Epic 4's delivery engine can read them when events occur.

Do NOT implement:
- Notification fanout or delivery queue integration
- Email/push channel connectors
- Background notification workers
- `notifications(id, user_id, type, status, sent_at)` delivery ledger (that's Epic 4)

### New `notifications` Domain Structure

Create **four new files**, following the exact structure established in `progress/` and `grading/` domains:

```
apps/api/app/domains/notifications/
├── __init__.py          # empty
├── repository.py        # in-memory store + dataclass
├── schemas.py           # Pydantic request/response models
└── router.py            # FastAPI router, endpoints, role guard
```

Architecture explicitly plans for this domain at:
[Source: _bmad-output/implementation-artifacts/architecture.md#domains-folder-structure, line 529]

### `NotificationPreferenceRecord` Dataclass

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class NotificationPreferenceRecord:
    user_id: str
    org_id: str
    event_type: str   # "grade_approved" | "recommendation_confirmed" | "topic_insight_new"
    cadence: str      # "instant" | "daily" | "weekly" | "off"
    updated_at: str   # ISO 8601 UTC, e.g. "2026-03-19T10:00:00+00:00"
```

Use `frozen=True` consistent with all other record dataclasses in the codebase (e.g., `TopicInsightRecord`, `ConfirmedRecommendationRecord`).

### Defined Event Types (MVP)

Three event types for MVP, matching the progress domain outputs already built:

| event_type | Meaning |
|---|---|
| `grade_approved` | A teacher-approved grade for a linked student |
| `recommendation_confirmed` | A confirmed learning recommendation for a linked student |
| `topic_insight_new` | A new topic weakness insight for a linked student |

These map to the outputs from the progress domain stories 3.1–3.3. The delivery engine (Epic 4) will use these keys to route events.

### `InMemoryNotificationPreferencesRepository`

Pattern: class-level `dict` state — same as `InMemoryGradingRepository`, `InMemoryStudentsRepository`, etc.

```python
VALID_CADENCES = frozenset({"instant", "daily", "weekly", "off"})
VALID_EVENT_TYPES = frozenset({"grade_approved", "recommendation_confirmed", "topic_insight_new"})

class InMemoryNotificationPreferencesRepository:
    # Key: (user_id, org_id, event_type) → NotificationPreferenceRecord
    _preferences: ClassVar[dict[tuple[str, str, str], NotificationPreferenceRecord]] = {}

    def get_preferences_for_user(
        self, user_id: str, org_id: str
    ) -> list[NotificationPreferenceRecord]:
        """Return all preferences for user+org, sorted by event_type for stable output."""
        return sorted(
            [p for p in self.__class__._preferences.values()
             if p.user_id == user_id and p.org_id == org_id],
            key=lambda p: p.event_type,
        )

    def upsert_preference(
        self, user_id: str, org_id: str, event_type: str, cadence: str, updated_at: str
    ) -> NotificationPreferenceRecord:
        """Create or replace a preference record. Returns the new record."""
        record = NotificationPreferenceRecord(
            user_id=user_id, org_id=org_id,
            event_type=event_type, cadence=cadence, updated_at=updated_at,
        )
        self.__class__._preferences[(user_id, org_id, event_type)] = record
        return record

def reset_notifications_state_for_tests() -> None:
    InMemoryNotificationPreferencesRepository._preferences.clear()
```

### Schemas

```python
from pydantic import BaseModel, field_validator
from typing import Literal

VALID_CADENCES = {"instant", "daily", "weekly", "off"}

class NotificationPreferenceItem(BaseModel):
    event_type: str
    cadence: str
    updated_at: str

class NotificationPreferencesResponse(BaseModel):
    preferences: list[NotificationPreferenceItem]

class NotificationPreferenceUpdateItem(BaseModel):
    event_type: str
    cadence: str

    @field_validator("cadence")
    @classmethod
    def validate_cadence(cls, v: str) -> str:
        if v not in VALID_CADENCES:
            raise ValueError(f"cadence must be one of: {sorted(VALID_CADENCES)}")
        return v

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        from app.domains.notifications.repository import VALID_EVENT_TYPES
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"event_type must be one of: {sorted(VALID_EVENT_TYPES)}")
        return v

class NotificationPreferencesUpdateRequest(BaseModel):
    preferences: list[NotificationPreferenceUpdateItem]
```

**Note on 422 validation:** Pydantic `field_validator` raising `ValueError` automatically produces a FastAPI 422 response — no extra error handling needed in the router.

### Router Pattern

```python
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.domains.auth.dependencies import ActorContext, require_authenticated_actor
from app.domains.notifications.repository import InMemoryNotificationPreferencesRepository
from app.domains.notifications.schemas import (
    NotificationPreferencesResponse,
    NotificationPreferenceItem,
    NotificationPreferencesUpdateRequest,
)
from fastapi import HTTPException

router = APIRouter(prefix="/notifications", tags=["notifications"])
_prefs_repo = InMemoryNotificationPreferencesRepository()

def _require_parent(actor: ActorContext) -> None:
    """Guard: only parent role may manage notification preferences."""
    if actor.role != "parent":
        raise HTTPException(status_code=403, detail="Forbidden")

@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    actor: ActorContext = Depends(require_authenticated_actor),
) -> NotificationPreferencesResponse:
    _require_parent(actor)
    records = _prefs_repo.get_preferences_for_user(actor.user_id, actor.org_id)
    return NotificationPreferencesResponse(
        preferences=[
            NotificationPreferenceItem(
                event_type=r.event_type,
                cadence=r.cadence,
                updated_at=r.updated_at,
            )
            for r in records
        ]
    )

@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    body: NotificationPreferencesUpdateRequest,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> NotificationPreferencesResponse:
    _require_parent(actor)
    now = datetime.now(tz=timezone.utc).isoformat()
    for item in body.preferences:
        _prefs_repo.upsert_preference(
            user_id=actor.user_id,
            org_id=actor.org_id,
            event_type=item.event_type,
            cadence=item.cadence,
            updated_at=now,
        )
    records = _prefs_repo.get_preferences_for_user(actor.user_id, actor.org_id)
    return NotificationPreferencesResponse(
        preferences=[
            NotificationPreferenceItem(
                event_type=r.event_type,
                cadence=r.cadence,
                updated_at=r.updated_at,
            )
            for r in records
        ]
    )
```

**Why `_require_parent` not `_require_parent_or_student`:** Notification preferences are parent-only. Students do not configure delivery cadences in the MVP. This mirrors the PRD which specifies self-serve notification settings for parents.
[Source: _bmad-output/planning-artifacts/prd.md#Parent Success Criteria]

### main.py Registration

Add exactly two lines to `apps/api/app/main.py`:

```python
from app.domains.notifications.router import router as notifications_router
# ... (alongside existing router imports)

app.include_router(notifications_router)
# ... (after existing include_router calls)
```

### Test File: `apps/api/tests/test_notifications_api.py`

**Test setup pattern** — follow `test_progress_api.py` exactly:

```python
import asyncio
import httpx
import pytest
from app.main import app
from app.domains.auth.repository import InMemoryAuthRepository
from app.domains.notifications.repository import (
    InMemoryNotificationPreferencesRepository,
    reset_notifications_state_for_tests,
)

# ── Token helpers ─────────────────────────────────────────────────────────────
def _parent_token(user_id="usr_parent_1", org_id="org_demo_1") -> str:
    from app.core.security import create_access_token
    return create_access_token({"sub": user_id, "role": "parent", "org_id": org_id})

def _parent_headers(**kwargs) -> dict:
    return {"Authorization": f"Bearer {_parent_token(**kwargs)}"}

def _student_headers() -> dict:
    from app.core.security import create_access_token
    token = create_access_token({"sub": "usr_student_1", "role": "student", "org_id": "org_demo_1"})
    return {"Authorization": f"Bearer {token}"}

def _teacher_headers() -> dict:
    from app.core.security import create_access_token
    token = create_access_token({"sub": "usr_teacher_1", "role": "teacher", "org_id": "org_demo_1"})
    return {"Authorization": f"Bearer {token}"}

# ── State reset helper ────────────────────────────────────────────────────────
def reset_state() -> None:
    reset_notifications_state_for_tests()
    InMemoryAuthRepository._users.clear()
    InMemoryAuthRepository._users["usr_parent_1"] = ...  # same pattern as test_progress_api.py
    # Activate usr_parent_1 as parent in org_demo_1
    # Activate usr_student_1 as student in org_demo_1
    # Activate usr_teacher_1 as teacher in org_demo_1
```

**Note:** Look at how `reset_auth_state_for_tests()` works in `test_progress_api.py` and replicate the same user seeding for `usr_parent_1`, `usr_student_1`, `usr_teacher_1`. Do NOT modify the shared auth reset function — create an inline helper in the new test file.

**Individual tests:**

```python
# Test 1 — GET default preferences (empty, well-formed)
def test_get_preferences_returns_empty_for_new_parent() -> None:
    reset_state()
    r = asyncio.run(_get("/notifications/preferences", _parent_headers()))
    assert r.status_code == 200
    assert r.json() == {"preferences": []}

# Test 2 — PUT saves a single preference
def test_put_preference_saves_successfully() -> None:
    reset_state()
    body = {"preferences": [{"event_type": "grade_approved", "cadence": "daily"}]}
    r = asyncio.run(_put("/notifications/preferences", _parent_headers(), body))
    assert r.status_code == 200
    prefs = r.json()["preferences"]
    assert len(prefs) == 1
    assert prefs[0]["event_type"] == "grade_approved"
    assert prefs[0]["cadence"] == "daily"
    assert "updated_at" in prefs[0]

# Test 3 — GET after PUT returns updated preferences
def test_get_returns_updated_preferences_after_put() -> None:
    reset_state()
    body = {"preferences": [{"event_type": "grade_approved", "cadence": "weekly"}]}
    asyncio.run(_put("/notifications/preferences", _parent_headers(), body))
    r = asyncio.run(_get("/notifications/preferences", _parent_headers()))
    assert r.status_code == 200
    prefs = r.json()["preferences"]
    assert any(p["event_type"] == "grade_approved" and p["cadence"] == "weekly" for p in prefs)

# Test 4 — student role → 403
def test_student_cannot_access_notification_preferences() -> None:
    reset_state()
    r = asyncio.run(_get("/notifications/preferences", _student_headers()))
    assert r.status_code == 403

# Test 5 — teacher role → 403
def test_teacher_cannot_access_notification_preferences() -> None:
    reset_state()
    r = asyncio.run(_get("/notifications/preferences", _teacher_headers()))
    assert r.status_code == 403

# Test 6 — unauthenticated → 401
def test_unauthenticated_get_returns_401() -> None:
    reset_state()
    r = asyncio.run(_get("/notifications/preferences", {}))
    assert r.status_code == 401

# Test 7 — invalid cadence → 422
def test_invalid_cadence_returns_422() -> None:
    reset_state()
    body = {"preferences": [{"event_type": "grade_approved", "cadence": "quarterly"}]}
    r = asyncio.run(_put("/notifications/preferences", _parent_headers(), body))
    assert r.status_code == 422

# Test 8 — org isolation: parent from org_other_1 has separate preferences
def test_preferences_are_org_scoped() -> None:
    reset_state()
    body = {"preferences": [{"event_type": "grade_approved", "cadence": "daily"}]}
    asyncio.run(_put("/notifications/preferences", _parent_headers(org_id="org_demo_1"), body))
    r_other = asyncio.run(_get("/notifications/preferences", _parent_headers(org_id="org_other_1")))
    assert r_other.status_code == 200
    prefs = r_other.json()["preferences"]
    assert not any(p["event_type"] == "grade_approved" and p["cadence"] == "daily" for p in prefs)

# Test 9 — multiple event types configured independently
def test_multiple_event_types_configured_independently() -> None:
    reset_state()
    body = {"preferences": [
        {"event_type": "grade_approved", "cadence": "weekly"},
        {"event_type": "recommendation_confirmed", "cadence": "daily"},
    ]}
    asyncio.run(_put("/notifications/preferences", _parent_headers(), body))
    r = asyncio.run(_get("/notifications/preferences", _parent_headers()))
    prefs = r.json()["preferences"]
    assert len(prefs) == 2
    cadence_map = {p["event_type"]: p["cadence"] for p in prefs}
    assert cadence_map["grade_approved"] == "weekly"
    assert cadence_map["recommendation_confirmed"] == "daily"

# Test 10 — NFR-001: p95 ≤ 700ms
def test_nfr_001_get_preferences_performance() -> None:
    reset_state()
    import time
    latencies = []
    for _ in range(20):
        start = time.perf_counter()
        asyncio.run(_get("/notifications/preferences", _parent_headers()))
        latencies.append((time.perf_counter() - start) * 1000)
    latencies.sort()
    p95 = latencies[int(0.95 * len(latencies))]
    assert p95 < 700, f"p95 latency {p95:.1f}ms exceeds 700ms"
```

**ASGI test client helpers** (add at top of test file, same pattern as `test_progress_api.py`):

```python
async def _async_get(path: str, headers: dict) -> httpx.Response:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path, headers=headers)

async def _async_put(path: str, headers: dict, body: dict) -> httpx.Response:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.put(path, headers=headers, json=body)

def _get(path: str, headers: dict) -> httpx.Response:
    return asyncio.run(_async_get(path, headers))  # type: ignore[return-value]

def _put(path: str, headers: dict, body: dict) -> httpx.Response:
    return asyncio.run(_async_put(path, headers, body))  # type: ignore[return-value]
```

### Previous Story Intelligence (3-3 → 3-4)

**From Story 3.3 — learnings applicable here:**
- Use `frozen=True` on all dataclasses (all existing records use it; don't break the pattern).
- Use `datetime.fromisoformat()` for any timestamp comparisons (not string comparison).
- All test HTTP calls use `asyncio.run()` + `httpx.AsyncClient(transport=httpx.ASGITransport(app=app))`. Do NOT use `httpx.Client(app=app, ...)` — it was corrected in 3.3 to use async.
- Class-level `_state` dicts — always add a `reset_*_for_tests()` function so tests can call it.
- "Domain Boundary Rule": router must import only from its own domain's repository + `auth.dependencies`. Do NOT import from `grading`, `progress`, `students` etc.
- 248 tests currently passing — ensure all pass after this story.

**File list from Story 3.3 (do not modify these unless required):**
- `apps/api/app/domains/grading/repository.py` (do not touch)
- `apps/api/app/domains/progress/schemas.py` (do not touch)
- `apps/api/app/domains/progress/router.py` (do not touch)
- `apps/api/tests/test_progress_api.py` (do not touch)

### Git Intelligence

Recent commits confirm:
- b643adb: story 3.2 completed — grades with trend, 240 tests passing
- 0288230: added Authz and Tenet Safety Rules — README updated with auth rules
- 30a8b10: epic 2 completed — recommendation pipeline complete, guardian-student linkage

Pattern observed: each story is a clean, additive commit. No regressions. Follow the same: new files first, main.py second, tests last.

### Project Structure Notes

**Alignment with architecture:**
- Architecture specifies `domains/notifications/` as a planned domain [Source: architecture.md#domains-structure]
- Architecture specifies `/notifications/*` as a planned API boundary [Source: architecture.md#api-boundaries]
- Architecture specifies `notification_jobs.py` worker (future, Epic 4) [Source: architecture.md#workers]
- This story creates the domain skeleton; Epic 4 adds the worker and delivery ledger

**No conflicts or variances detected.** The `notifications` domain is new — no existing code to break.

**Files to create (new):**
- `apps/api/app/domains/notifications/__init__.py`
- `apps/api/app/domains/notifications/repository.py`
- `apps/api/app/domains/notifications/schemas.py`
- `apps/api/app/domains/notifications/router.py`
- `apps/api/tests/test_notifications_api.py`

**Files to modify (existing):**
- `apps/api/app/main.py` — add import + `include_router(notifications_router)`
- `apps/api/README.md` — add 2 endpoints to Story Scope section
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — update `3-4-...` to `ready-for-dev` (already done by create-story workflow)

### Regression Risk

- `require_authenticated_actor` is unchanged — no JWT changes
- All existing 248 tests in `test_progress_api.py`, `test_grading_api.py`, etc. must remain green
- `main.py` change is purely additive (one import + one `include_router`)
- No shared state with existing repos (new class-level dict in notifications repo only)

### References

- Story 3.4 AC and user story: [Source: _bmad-output/implementation-artifacts/epics.md#Epic-3-Story-3.4]
- FR-029 (notification cadence configuration): [Source: _bmad-output/planning-artifacts/srs.md#FR-029]
- DR-005 (preferences per user per channel and cadence): [Source: _bmad-output/planning-artifacts/srs.md#DR-005]
- NFR-001 (API p95 ≤ 700ms): [Source: _bmad-output/planning-artifacts/srs.md#NFR-001]
- Architecture notifications domain plan: [Source: _bmad-output/implementation-artifacts/architecture.md#domains-folder-structure]
- Architecture notifications API boundary: [Source: _bmad-output/implementation-artifacts/architecture.md#api-boundaries, line 78]
- Architecture risk mitigation (notification overload): [Source: _bmad-output/implementation-artifacts/architecture.md#risks, line 117]
- Story 3.3 dev notes (test patterns, frozen dataclasses, asyncio+httpx pattern): [Source: _bmad-output/implementation-artifacts/3-3-strength-weakness-indicators-and-next-step-guidance.md#Dev-Notes]
- Domain Boundary Rule: [Source: apps/api/README.md#Domain-Boundary-Rule]
- `require_authenticated_actor`: [Source: apps/api/app/domains/auth/dependencies.py]
- `InMemoryGradingRepository` (class-level state pattern to follow): [Source: apps/api/app/domains/grading/repository.py]
- UX notification settings context: [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Information-Architecture]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Created `notifications` domain: `__init__.py` (empty), `repository.py` (`NotificationPreferenceRecord` frozen dataclass, `InMemoryNotificationPreferencesRepository` with class-level dict keyed by `(user_id, org_id, event_type)`, `reset_notifications_state_for_tests()`), `schemas.py` (Pydantic models with `field_validator` for cadence + event_type giving automatic 422), `router.py` (`_require_parent` guard, `GET /notifications/preferences`, `PUT /notifications/preferences` using `datetime.now(UTC).isoformat()` for `updated_at`)
- Registered `notifications_router` in `main.py` (additive only — one import, one `include_router`)
- Updated `README.md` Story Scope with `GET /notifications/preferences` and `PUT /notifications/preferences`
- Created `tests/test_notifications_api.py` with 15 tests: empty default GET (AC3), PUT saves (AC1), GET after PUT (AC2), student/teacher 403 (AC5 ×3), unauthenticated 401 (AC6 ×2), invalid cadence 422 (AC4), invalid event_type 422 (AC4), org isolation repo-layer (AC7), multiple event types (AC1), upsert semantics (AC2), NFR-001 p95 GET and PUT
- Full suite: 263/263 passed (248 prior + 15 new); zero regressions
- Code review fixes applied (2026-03-19): added 5 tests (admin GET/PUT 403, principal GET/PUT 403, user-scoped isolation within org); refactored NFR tests to single-session with warm-up matching established test_progress_api.py pattern; 20/20 notification tests passing

### File List

- `apps/api/app/domains/notifications/__init__.py` — new, empty domain marker
- `apps/api/app/domains/notifications/repository.py` — new; `NotificationPreferenceRecord`, `InMemoryNotificationPreferencesRepository`, `reset_notifications_state_for_tests`, `VALID_CADENCES`, `VALID_EVENT_TYPES`
- `apps/api/app/domains/notifications/schemas.py` — new; `NotificationPreferenceItem`, `NotificationPreferencesResponse`, `NotificationPreferenceUpdateItem` (with validators), `NotificationPreferencesUpdateRequest`
- `apps/api/app/domains/notifications/router.py` — new; `_require_parent` guard, `GET /notifications/preferences`, `PUT /notifications/preferences`
- `apps/api/app/main.py` — modified; added `notifications_router` import and `include_router` call
- `apps/api/README.md` — modified; added 2 notification endpoints to Story Scope
- `apps/api/tests/test_notifications_api.py` — new; 20 tests covering all ACs (including admin/principal role 403s, user-scoped isolation) and NFR-001
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — modified; `3-4-parent-self-serve-notification-preferences` → `review`

## Change Log

- Story created (2026-03-19)
- Implementation complete (2026-03-19): created `notifications` domain (repository, schemas, router), registered in main.py, updated README, added 15 tests; 263/263 passing
- Code review (2026-03-19): Fixed H2 (added admin/principal 403 tests for AC5), M1 (user-scoped isolation test for AC7), M2 (NFR tests refactored to single-session with warm-up). 20 notification tests passing

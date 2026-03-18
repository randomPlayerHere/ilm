---
title: 'Guardian-Student Linkage and Parent/Student Role Foundation'
slug: 'guardian-student-linkage-parent-student-roles'
created: '2026-03-18'
status: 'Completed'
stepsCompleted: [1, 2, 3, 4]
tech_stack:
  - FastAPI
  - Python dataclasses (in-memory phase)
  - Pydantic v2 (request/response schemas)
  - pytest + httpx.ASGITransport
  - python-jose (JWT via app.core.security)
files_to_modify:
  - apps/api/app/main.py
  - apps/api/app/domains/auth/repository.py
files_to_create:
  - apps/api/app/domains/students/__init__.py
  - apps/api/app/domains/students/models.py
  - apps/api/app/domains/students/repository.py
  - apps/api/app/domains/students/schemas.py
  - apps/api/app/domains/students/router.py
  - apps/api/tests/test_students_api.py
code_patterns:
  - frozen dataclass records
  - InMemory class-level state with _seeded guard
  - _require_teacher(actor) helper in router
  - actor org-scoping on all mutations
test_patterns:
  - httpx.ASGITransport + asyncio.run(scenario())
  - setup_function resets all repo state
  - mismatched-role JWT for 403 tests
---

# Tech-Spec: Guardian-Student Linkage and Parent/Student Role Foundation

**Created:** 2026-03-18

## Overview

### Problem Statement

Epic 3 (Parent and Student Progress Transparency) cannot begin because two foundational prerequisites are missing: (1) no `parent` or `student` users exist in the system — the `InMemoryAuthRepository` only seeds `admin` and `teacher` accounts — and (2) there is no `GuardianStudentLink` data model or repository, meaning the system has no way to associate a guardian to the students they are authorized to view. Story 3.1 will produce HIGH code review findings if implemented without this design in place.

### Solution

Introduce a dedicated `students` domain (modular, not a patch) that owns the `GuardianStudentLink` record type and its repository. Add parent and student seed users to `InMemoryAuthRepository`. Expose teacher-gated endpoints for creating and managing guardian-student links. This gives Epic 3 a clean, non-temporary foundation: progress endpoints call `students_repo.get_links_for_guardian(actor.user_id, actor.org_id)` to validate parent access with org isolation enforced at the repo contract level — no JWT changes needed.

### Scope

**In Scope:**

- New `students` domain: `__init__.py`, `models.py`, `repository.py`, `schemas.py`, `router.py`
- `GuardianStudentLink` frozen dataclass: `link_id`, `guardian_id`, `student_id`, `org_id`, `linked_by`, `created_at`
- `StudentsRepository` Protocol + `InMemoryStudentsRepository` with full CRUD
- Pydantic schemas in dedicated `schemas.py`: `GuardianStudentLinkCreateRequest`, `GuardianStudentLinkResponse`, `GuardianStudentLinkListResponse`
- 3 teacher-gated endpoints under `/students/{student_id}/guardian-links`
- Seed data: parent and student users added to `InMemoryAuthRepository`
- Students router registered in `main.py`
- 16 tests covering all happy paths and every error path

**Out of Scope:**

- Parent/student progress endpoints (Story 3.1+)
- Frontend/mobile UI changes
- Notification infrastructure (Story 3.4)
- JWT token changes or `ActorContext` field additions
- `StudentProfile` record (students are UserRecords with role="student")
- COPPA/FERPA disclosure workflows (Epic 6)
- Service layer (router calls repo directly — simple CRUD, no state machine)

## Context for Development

### Codebase Patterns

- **Role gating**: Each router defines a local `_require_teacher(actor)` helper that raises HTTP 403 if `actor.role != "teacher"`. Applied on every protected route before business logic. Follow this exact pattern — see `apps/api/app/domains/grading/router.py` lines 60-63.
- **InMemory repository**: Class-level `_seeded: bool` + `@classmethod _ensure_seed_data()` prevents double-seeding. `@classmethod reset_state()` clears and re-seeds for tests. All state in class-level dicts. See `apps/api/app/domains/auth/repository.py` lines 51-115.
- **Auth dependency**: Every protected endpoint uses `actor: ActorContext = Depends(require_authenticated_actor)`. Import from `app.domains.auth.dependencies`. Never import from `auth` domain beyond this.
- **ID format**: Sequential string IDs with prefix — `link_1`, `link_2`. Class-level `_link_seq: int = 1`.
- **Router prefix**: `APIRouter(prefix="/students", tags=["students"])`.
- **Router registration**: `app.include_router(students_router)` in `apps/api/app/main.py`.
- **Test: mismatched role → 403**: Create a token with `role="parent"` for `usr_teacher_1` (stored as teacher) — `require_authenticated_actor` fails the role cross-check → 403. See `tests/test_grading_api.py` lines 18-21.
- **Test: setup_function**: Resets all repo state + clears `app.dependency_overrides` before each test function.
- **No service layer**: Students domain uses repo directly from router. Simple CRUD — no state machine justifying a service layer.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `apps/api/app/domains/auth/models.py` | Frozen dataclass pattern to replicate for `GuardianStudentLink` |
| `apps/api/app/domains/auth/repository.py` | InMemory pattern: class-level state, seed guard, `reset_state` |
| `apps/api/app/domains/auth/dependencies.py` | `ActorContext`, `require_authenticated_actor` — Depends on every route |
| `apps/api/app/core/roles.py` | Confirms `"parent"` and `"student"` already in `ROLE_HOME_PATHS` |
| `apps/api/app/core/security.py` | `create_access_token(subject, org_id, role)` — used in test helpers |
| `apps/api/app/domains/grading/router.py` | `_require_teacher` helper + endpoint structure to follow exactly |
| `apps/api/app/main.py` | Where to add `app.include_router(students_router)` |
| `apps/api/tests/test_grading_api.py` | Test harness: `httpx.ASGITransport`, `asyncio.run`, `setup_function` |

### Technical Decisions

- **`students` domain (not `auth` domain)**: `auth` owns identity; `students` owns educational relationships. Clean boundary for Epics 3–7.
- **Teacher-created links**: Admin creates user accounts via the existing invite flow. Teachers create the `parent ↔ student` link record — they know the class roster.
- **Service-layer lookup at request time (no JWT changes)**: Epic 3+ progress endpoints will call `students_repo.get_links_for_guardian(actor.user_id)`. No token refresh complexity needed.
- **Duplicate link prevention**: `create_link` raises `ValueError` if `(guardian_id, student_id, org_id)` triple already exists. The uniqueness key includes `org_id` to prevent cross-tenant false conflicts. Router maps to 409 Conflict.
- **Org-scoped links**: `org_id` on every link comes from `actor.org_id`. GET uses repo-level org filter. DELETE returns 404 for both not-found and cross-org cases — 403 would confirm cross-org link existence (information disclosure).
- **`linked_by` field**: Stores teacher's `user_id` for auditability — no separate audit event needed.

## Implementation Plan

### Tasks

- [x] Task 1: Add parent and student seed users to auth repository
  - File: `apps/api/app/domains/auth/repository.py`
  - Action: In `_ensure_seed_data()`, add two entries to `cls._users`:
    - Key `"parent@example.com"`: `UserRecord(user_id="usr_parent_1", org_id="org_demo_1", email="parent@example.com", password_hash=hash_password("correct-horse-battery-staple"), role="parent", status="active")`
    - Key `"student@example.com"`: `UserRecord(user_id="usr_student_1", org_id="org_demo_1", email="student@example.com", password_hash=hash_password("correct-horse-battery-staple"), role="student", status="active")`
  - Notes: Do **NOT** change `_user_seq`. `usr_parent_1` and `usr_student_1` are hardcoded IDs — they are not generated by the sequence counter. The sequence stays at `3` (next `invite_user` produces `usr_3`, which does not collide with `usr_parent_1` or `usr_student_1`). No changes to `_user_seq` in any location. No existing auth tests are affected.

- [x] Task 2: Create `apps/api/app/domains/students/__init__.py`
  - File: `apps/api/app/domains/students/__init__.py`
  - Action: Create empty file
  - Notes: Consistent with all other domain `__init__.py` files — no content.

- [x] Task 3: Create `apps/api/app/domains/students/models.py`
  - File: `apps/api/app/domains/students/models.py`
  - Action: Define one frozen dataclass:
    ```python
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class GuardianStudentLink:
        link_id: str
        guardian_id: str
        student_id: str
        org_id: str
        linked_by: str
        created_at: str
    ```
  - Notes: `guardian_id` and `student_id` are `user_id` strings from `UserRecord`. No foreign-key enforcement in-memory phase.

- [x] Task 4: Create `apps/api/app/domains/students/repository.py`
  - File: `apps/api/app/domains/students/repository.py`
  - Action: Define `StudentsRepository` Protocol and `InMemoryStudentsRepository`:

    **Protocol methods:**
    - `create_link(guardian_id: str, student_id: str, org_id: str, linked_by: str) -> GuardianStudentLink`
    - `get_links_for_guardian(guardian_id: str, org_id: str) -> list[GuardianStudentLink]`
    - `get_links_for_student(student_id: str, org_id: str) -> list[GuardianStudentLink]`
    - `get_link_by_id(link_id: str) -> GuardianStudentLink | None`
    - `delete_link(link_id: str) -> None`
    - Note: `org_id` is required on both lookup methods — this enforces tenant isolation at the contract level so Epic 3 callers cannot accidentally return cross-org links

    **InMemoryStudentsRepository:**
    - Class-level state: `_links: dict[str, GuardianStudentLink] = {}`, `_link_seq: int = 1`, `_seeded: bool = False`
    - `__init__`: call `self._ensure_seed_data()` — follow the auth repo pattern exactly (see `auth/repository.py` line 63)
    - `_ensure_seed_data()`: guard with `if cls._seeded: return`; then set `cls._seeded = True`, `cls._links = {}` — do NOT set `_link_seq` here (the guard prevents it running after first call, making it a no-op on resets)
    - `reset_state()`: sets `cls._seeded = False`, `cls._link_seq = 1`, `cls._links = {}`, then calls `cls._ensure_seed_data()` — `_link_seq` is reset here, not in `_ensure_seed_data()`
    - `create_link`: check for existing `(guardian_id, student_id, org_id)` triple → raise `ValueError("Guardian-student link already exists")` if found; create `link_id = f"link_{cls._link_seq}"`, increment `_link_seq`, store and return — uniqueness key includes `org_id` to prevent cross-tenant false conflicts
    - `get_links_for_guardian`: `[l for l in cls._links.values() if l.guardian_id == guardian_id and l.org_id == org_id]`
    - `get_links_for_student`: `[l for l in cls._links.values() if l.student_id == student_id and l.org_id == org_id]`
    - `get_link_by_id`: `return cls._links.get(link_id)`
    - `delete_link`: raise `KeyError("Link not found")` if absent; otherwise `del cls._links[link_id]`

  - Notes: Import `datetime` from stdlib for `created_at = datetime.now(UTC).isoformat()`. Import `UTC` from `datetime`.

- [x] Task 5: Create `apps/api/app/domains/students/schemas.py`
  - File: `apps/api/app/domains/students/schemas.py`
  - Action: Define Pydantic schemas (separate file, consistent with grading domain pattern — see `grading/schemas.py`):
    - `GuardianStudentLinkCreateRequest(BaseModel)`: `guardian_id: str = Field(..., min_length=1)` — `min_length=1` rejects empty string
    - `GuardianStudentLinkResponse(BaseModel)`: `link_id: str`, `guardian_id: str`, `student_id: str`, `org_id: str`, `linked_by: str`, `created_at: str`
    - `GuardianStudentLinkListResponse(BaseModel)`: `links: list[GuardianStudentLinkResponse]`
  - Notes: Import `Field` from `pydantic`. Router imports these from `app.domains.students.schemas`.

- [x] Task 6: Create `apps/api/app/domains/students/router.py`
  - File: `apps/api/app/domains/students/router.py`
  - Action: Define router, helper, and 3 endpoints — import schemas from `app.domains.students.schemas`:

    **Router setup:**
    ```python
    from app.domains.students.schemas import (
        GuardianStudentLinkCreateRequest,
        GuardianStudentLinkListResponse,
        GuardianStudentLinkResponse,
    )

    router = APIRouter(prefix="/students", tags=["students"])
    _repo = InMemoryStudentsRepository()

    def reset_students_state_for_tests() -> None:
        InMemoryStudentsRepository.reset_state()

    def _require_teacher(actor: ActorContext) -> None:
        if actor.role != "teacher":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    def _to_link_response(link: GuardianStudentLink) -> GuardianStudentLinkResponse:
        return GuardianStudentLinkResponse(
            link_id=link.link_id, guardian_id=link.guardian_id,
            student_id=link.student_id, org_id=link.org_id,
            linked_by=link.linked_by, created_at=link.created_at,
        )
    ```

    **Endpoint 1 — POST `/students/{student_id}/guardian-links`** → 201:
    - `_require_teacher(actor)`
    - Call `_repo.create_link(guardian_id=payload.guardian_id, student_id=student_id, org_id=actor.org_id, linked_by=actor.user_id)`
    - Catch `ValueError` → raise `HTTPException(409, detail="Guardian-student link already exists")`
    - Return `_to_link_response(link)`

    **Endpoint 2 — GET `/students/{student_id}/guardian-links`** → 200:
    - `_require_teacher(actor)`
    - `links = _repo.get_links_for_student(student_id=student_id, org_id=actor.org_id)` — org_id enforced at repo level
    - Return `GuardianStudentLinkListResponse(links=[_to_link_response(l) for l in links])`

    **Endpoint 3 — DELETE `/students/{student_id}/guardian-links/{link_id}`** → 204:
    - `_require_teacher(actor)`
    - `link = _repo.get_link_by_id(link_id)` → if `None`: raise `HTTPException(404, "Link not found")`
    - If `link.org_id != actor.org_id`: raise `HTTPException(404, "Link not found")` — return 404 (not 403) to avoid confirming cross-org link existence (information disclosure prevention)
    - If `link.student_id != student_id`: raise `HTTPException(404, "Link not found")`
    - Call `_repo.delete_link(link_id)`
    - Return `Response(status_code=status.HTTP_204_NO_CONTENT)`

  - Notes: Import `Response` from `fastapi`. Declare DELETE decorator with `response_model=None, status_code=204` to prevent FastAPI OpenAPI schema generation issues. Do NOT import from `courses` or `grading` domains.

- [x] Task 7: Register students router in main.py
  - File: `apps/api/app/main.py`
  - Action: Add import `from app.domains.students.router import router as students_router` and call `app.include_router(students_router)`
  - Notes: Place import alongside the other domain router imports. Place `include_router` call after the existing four routers.

- [x] Task 8: Write test file
  - File: `apps/api/tests/test_students_api.py`
  - Action: Implement 16 tests using `httpx.ASGITransport` + `asyncio.run(scenario())` harness:

    **Helpers:**
    ```python
    def _teacher_headers() -> dict[str, str]:
        token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="teacher")
        return {"Authorization": f"Bearer {token}"}

    def _non_teacher_headers() -> dict[str, str]:
        # usr_teacher_1 stored as role="teacher" — mismatched token role → 403
        token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="parent")
        return {"Authorization": f"Bearer {token}"}

    def _parent_headers() -> dict[str, str]:
        token, _ = create_access_token(subject="usr_parent_1", org_id="org_demo_1", role="parent")
        return {"Authorization": f"Bearer {token}"}

    def setup_function() -> None:
        reset_auth_state_for_tests()
        reset_students_state_for_tests()
        app.dependency_overrides.clear()
    ```

    **Tests:**
    1. `test_create_guardian_link_teacher_success` — POST → 201, assert `link_id` starts with `"link_"`, assert `guardian_id`, `student_id`, `org_id == "org_demo_1"`, `linked_by == "usr_teacher_1"`, `created_at` present
    2. `test_create_guardian_link_duplicate_conflict` — POST same `(guardian_id, student_id)` twice → second returns 409
    3. `test_create_guardian_link_unauthenticated` — no token → 401
    4. `test_create_guardian_link_non_teacher_forbidden` — `_non_teacher_headers()` → 403
    5. `test_list_guardian_links_teacher_success` — create 1 link, GET `/students/{student_id}/guardian-links` → 200, `links` list has 1 item with correct fields
    6. `test_list_guardian_links_empty` — GET with no links created → 200, `links == []`
    7. `test_list_guardian_links_unauthenticated` — 401
    8. `test_list_guardian_links_non_teacher_forbidden` — 403
    9. `test_delete_guardian_link_teacher_success` — create link, DELETE by `link_id` → 204, subsequent GET returns empty list
    10. `test_delete_guardian_link_not_found` — DELETE unknown `link_id` → 404
    11. `test_delete_guardian_link_unauthenticated` — 401
    12. `test_delete_guardian_link_non_teacher_forbidden` — 403
    13. `test_get_links_for_guardian_repo_direct` — POST to `/students/usr_student_1/guardian-links` with `{"guardian_id": "usr_parent_1"}` using `_teacher_headers()`; then call `InMemoryStudentsRepository().get_links_for_guardian("usr_parent_1", "org_demo_1")` directly; assert the list contains one record with `guardian_id="usr_parent_1"` and `student_id="usr_student_1"` (covers AC 9)
    14. `test_parent_calling_teacher_endpoint_forbidden` — use `_parent_headers()` (valid `usr_parent_1` JWT, role=parent, passes `require_authenticated_actor`) to POST to `/students/usr_student_1/guardian-links` → assert 403; this tests `_require_teacher` directly, not the mismatched-role trick (covers AC 4 via genuine RBAC check)
    15. `test_delete_student_mismatch_returns_404` — create a link for `usr_student_1`, then DELETE using the correct `link_id` but wrong student path `/students/usr_admin_1/guardian-links/{link_id}` → assert 404 (covers the student_id mismatch branch)
    16. `test_list_guardian_links_org_isolation` — create a link as `org_demo_1` teacher; then call `InMemoryStudentsRepository().get_links_for_student("usr_student_1", "org_demo_2")` directly and assert it returns `[]`; add inline comment: `# NOTE: org isolation validated at repo layer; HTTP cross-org test not possible with single-org seed — add org_demo_2 seed in a future story if needed`

  - Notes: Import `reset_students_state_for_tests` from `app.domains.students.router`. Use `"usr_parent_1"` and `"usr_student_1"` as fixture IDs (they exist in seed data after Task 1). For test 16, because the in-memory auth repo only has one org, the cross-org isolation is validated at the repo layer directly rather than via HTTP — document this explicitly in a test comment.

### Acceptance Criteria

- [x] AC 1: Given an authenticated teacher, when they POST to `/students/usr_student_1/guardian-links` with `{"guardian_id": "usr_parent_1"}`, then the system returns 201 with a response containing `link_id`, `guardian_id="usr_parent_1"`, `student_id="usr_student_1"`, `org_id="org_demo_1"`, `linked_by="usr_teacher_1"`, and `created_at`.

- [x] AC 2: Given a teacher POSTs the same `(guardian_id, student_id)` pair a second time, when the duplicate check runs in `create_link`, then the system returns 409 Conflict and no duplicate record is created.

- [x] AC 3: Given a request with no Authorization header, when any `/students/` endpoint is called, then the system returns 401 Unauthorized.

- [x] AC 4: Given a JWT token carrying a non-teacher role (e.g. `role="parent"`) for a user stored as `role="teacher"`, when any `/students/` endpoint is called, then the system returns 403 Forbidden.

- [x] AC 5: Given a teacher creates one guardian-student link, when they GET `/students/{student_id}/guardian-links`, then the response is 200 with `links` containing exactly that one record with all fields correct and `org_id` matching the teacher's org.

- [x] AC 6: Given no links have been created, when a teacher GETs `/students/{student_id}/guardian-links`, then the system returns 200 with `links: []`.

- [x] AC 7: Given a teacher creates a link and captures the `link_id`, when they DELETE `/students/{student_id}/guardian-links/{link_id}`, then the system returns 204 and a subsequent GET returns an empty `links` list.

- [x] AC 8: Given a DELETE request for a `link_id` that does not exist, when the lookup returns None, then the system returns 404 Not Found.

- [x] AC 9: Given a link exists for `guardian_id="usr_parent_1"` in `org_id="org_demo_1"`, when `InMemoryStudentsRepository().get_links_for_guardian("usr_parent_1", "org_demo_1")` is called directly, then it returns a list containing the matching `GuardianStudentLink` record — confirming the method Epic 3 progress endpoints will depend on works correctly with org isolation enforced.

- [x] AC 10: Given `"parent@example.com"` and `"student@example.com"` users exist in seed data, when `require_authenticated_actor` validates a JWT for `usr_parent_1` with `role="parent"`, then the actor is resolved successfully with `role="parent"` and `org_id="org_demo_1"`.

## Additional Context

### Dependencies

- `apps/api/app/domains/auth/dependencies.py` — `require_authenticated_actor`, `ActorContext` (runtime dependency for all endpoints)
- `apps/api/app/domains/auth/repository.py` — extended with parent/student seed users (Task 1 must complete before test helpers work)
- `apps/api/app/core/security.py` — `create_access_token` used in test helpers only
- No external libraries — all in stdlib + existing FastAPI/Pydantic stack

### Testing Strategy

- **Harness**: `httpx.ASGITransport(app=app)` + `asyncio.run(scenario())` — identical to Epic 2 pattern. No timing complexity.
- **State isolation**: `setup_function()` resets both `InMemoryAuthRepository` and `InMemoryStudentsRepository` before each test. No test-order dependencies.
- **403 coverage**: Uses mismatched-role JWT trick for `_non_teacher_headers()` — no separate non-teacher user needed.
- **`get_links_for_guardian` coverage**: AC 9 + test 13 test via direct repo call with org isolation enforced. Test 14 validates genuine RBAC via `_parent_headers()`. Test 15 covers `student_id` mismatch path. Test 16 validates repo-level cross-org isolation directly.
- **Task order matters for tests**: Task 1 (seed users) must be done before running tests that use `_parent_headers()` or `usr_parent_1` as a fixture ID.
- **DoD gate**: All 16 tests must pass with `pytest -x` before this story is marked complete. Zero failures accepted.

### Notes

- **`_user_seq` — no change needed**: `usr_parent_1` and `usr_student_1` are hardcoded IDs, not sequential. `_user_seq` stays at `3`. No existing auth tests are affected.
- **Risk — domain boundary**: The `students` router must never import from `app.domains.courses` or `app.domains.grading`. If Epic 3 needs data from grading, the progress endpoint (in a future `progress` domain or `students` domain) calls both repos — it does not import across domains.
- **Future**: When the database phase arrives, `GuardianStudentLink` maps cleanly to a `guardian_student_links` table with `(guardian_id, student_id)` unique constraint and `org_id` FK. The Protocol abstraction makes the swap non-breaking.
- **Retro action item source**: "Guardian-student linkage quick spec — must complete before `/bmad-bmm-create-story` for Story 3.1" (epic-2-retro-2026-03-18.md, Critical Path item 1).

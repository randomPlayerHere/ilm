# Story 2.3: Capture and Store Assignment Artifacts

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want to capture or upload assignment artifacts,
so that submissions are available for grading.

## Acceptance Criteria

1. Given an assignment and enrolled student, when the teacher captures or uploads an artifact, then the file is stored and retrievable, and metadata links it to assignment, student, class, and organization.
2. Given an unsupported artifact format, when upload validation runs, then the system rejects the upload, and returns actionable validation feedback.

## Tasks / Subtasks

- [x] Create `app/domains/grading/` domain module with repository, service, schemas, router (AC: 1, 2)
  - [x] Define `AssignmentRecord`, `ArtifactRecord` dataclasses and `InMemoryGradingRepository` with class-level state and `reset_state()`
  - [x] Seed `InMemoryGradingRepository` with same class/student fixtures as courses (`cls_demo_math_1`, `stu_demo_1`, `org_demo_1`, `usr_teacher_1`) plus `cls_demo_science_1`/`stu_science_1` for class-boundary tests
  - [x] Implement `create_assignment`, `create_artifact`, `get_artifact`, `list_artifacts_for_assignment` repository methods

- [x] Implement grading service with access control and file validation (AC: 1, 2)
  - [x] `create_assignment`: verify class exists + org/teacher ownership (fail-closed 403 on unknown/cross-tenant class)
  - [x] `create_artifact`: verify assignment ownership + student enrollment + class-boundary check (`student.class_id == assignment.class_id`); validate mime_type against allowlist; store artifact with stub storage key `s3://stub/{artifact_id}`
  - [x] `get_artifact`: owner-scoped retrieval; fail-closed 403 on unknown/cross-tenant
  - [x] `list_artifacts_for_assignment`: return all artifacts for a teacher-owned assignment

- [x] Add grading router and register in `app/main.py` (AC: 1, 2)
  - [x] `POST /grading/assignments` — create assignment (teacher-gated, class-scoped)
  - [x] `POST /grading/assignments/{assignment_id}/artifacts` — upload artifact via multipart `UploadFile`
  - [x] `GET /grading/assignments/{assignment_id}/artifacts/{artifact_id}` — retrieve artifact metadata
  - [x] `GET /grading/assignments/{assignment_id}/artifacts` — list artifacts for assignment
  - [x] Include router in `app/main.py` alongside auth, admin, courses routers

- [x] Add tests for artifact capture, retrieval, format validation, and authorization (AC: 1, 2)
  - [x] Unit tests (`test_grading_service.py`): assignment creation success, artifact creation success (jpeg/png/pdf/webp), mime-type rejection, class-boundary enforcement, cross-tenant fail-closed
  - [x] API tests (`test_grading_api.py`): upload success path (JPEG, PNG, PDF, WebP), unsupported format rejection (422), unauthenticated (401), non-teacher (403), cross-tenant (403), artifact retrieval success and fail-closed
  - [x] Full regression: `cd apps/api && uv run --extra dev pytest -q` passes (113 tests)

- [x] Update docs and handoff notes (AC: 1)
  - [x] Update `apps/api/README.md` with grading endpoints and artifact storage notes
  - [x] Update `apps/api/pyproject.toml` `[tool.ilm]` story to `"2.3"` with grading domain notes
  - [x] Document stub S3 pattern and downstream expectations for Story 2.4 grading job integration

## Dev Notes

- Story 2.3 introduces a new `grading` domain (`app/domains/grading/`) that is the entry point for the full AI grading workflow (Stories 2.3–2.6).
- Real S3 upload is out of scope; use stub in-memory storage with `storage_key = f"s3://stub/{artifact_id}"`. This key is the handle Story 2.4 will use when submitting AI grading jobs.
- No `assignment` concept currently existed in the codebase — this story creates it as the container linking class, teacher, and student artifacts.
- Student class-boundary check (`student.class_id == assignment.class_id`) is a hard requirement; learned from Story 2.2 review finding [HIGH] that missed a similar check.
- `python-multipart>=0.0.9,<1.0.0` was added as a required dependency for FastAPI multipart form support.

### Technical Requirements

- Implement in `apps/api` FastAPI domain modules under `app/domains/grading/`.
- Follow the same layered pattern: thin router → service (business logic) → repository (storage).
- Preserve tenant isolation and teacher role-based checks using `app.domains.auth.dependencies.require_authenticated_actor`.
- Fail-closed (403) on any unknown or cross-tenant reference to avoid resource enumeration.
- Multipart file upload using FastAPI's `UploadFile` — no JSON body for artifact upload endpoint.
- Supported MIME types (allowlist): `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `application/pdf`.
- Reject all other MIME types with `HTTP 422` and an actionable error message listing supported types.

### Architecture Compliance

- `/grading` is an explicit module boundary per architecture requirements.
- Grading domain does NOT import from `app/domains/courses/` — domain boundary maintained.
- Route layer: thin, delegates all logic to service. Service: all business rules and access control. Repository: all persistence and state.

### Library / Framework Requirements

- `python-multipart>=0.0.9,<1.0.0` added as required dependency for multipart form upload support.
- FastAPI `UploadFile` + `File(...)` + `Form(...)` used for multipart artifact upload.
- Pydantic v2 with `extra="forbid"` on request schemas.
- FastAPI range `>=0.115.0,<1.0.0` (unchanged).

### File Structure Requirements

New files created:
- `apps/api/app/domains/grading/__init__.py`
- `apps/api/app/domains/grading/repository.py`
- `apps/api/app/domains/grading/service.py`
- `apps/api/app/domains/grading/schemas.py`
- `apps/api/app/domains/grading/router.py`
- `apps/api/tests/test_grading_service.py`
- `apps/api/tests/test_grading_api.py`

Modified files:
- `apps/api/app/main.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`

### Testing Requirements

- AC-mapped tests for artifact upload success (JPEG, PNG, PDF, WebP).
- Tests verifying unsupported format returns 422 with descriptive error.
- Tests verifying metadata linking (assignment_id, student_id, class_id, org_id).
- Authorization regression: unauthenticated (401), non-teacher (403), cross-tenant (403) for all write and read endpoints.
- Class-boundary test: student from different class cannot have artifact created against that assignment.
- Artifact retrieval success and fail-closed (403 on unknown/cross-tenant).

### Previous Story Intelligence

- Story 2.1 established fail-closed semantics for class lookup.
- Story 2.2 code review found [HIGH]: missing class-boundary check — applied identically here.
- Story 2.2 code review found [HIGH]: missing unauthenticated/non-teacher denial tests — all new endpoints have explicit 401 and 403 tests.

### References

- [Source: _bmad-output/implementation-artifacts/epics.md#Story 2.3: Capture and Store Assignment Artifacts]
- [Source: _bmad-output/planning-artifacts/prd.md#Teacher Instruction and Assessment Workflow (FR13, FR41)]
- [Source: _bmad-output/implementation-artifacts/2-2-edit-and-save-generic-and-student-specific-plans.md#Review Findings]
- [Source: apps/api/app/domains/courses/repository.py] — seed data fixture IDs
- [Source: apps/api/app/domains/courses/router.py] — _require_teacher pattern
- [Source: apps/api/app/domains/auth/dependencies.py] — ActorContext, require_authenticated_actor
- [Source: https://fastapi.tiangolo.com/tutorial/request-files/]

## Story Completion Status

- Story implemented from scratch (new grading domain).
- 42 new tests added (20 service, 22 API): all pass.
- Full regression: 113 tests passing (71 pre-existing + 42 new), 0 failures.
- `python-multipart` added as required dependency.
- Status set to `review`.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Implementation Plan

- Created `app/domains/grading/` domain with repository → service → router layered architecture.
- Wrote failing tests first (test_grading_service.py, test_grading_api.py), then implemented to make them pass.
- Added `python-multipart` dependency required for FastAPI multipart form support.
- Replaced deprecated `status.HTTP_422_UNPROCESSABLE_ENTITY` with literal `422` to avoid FastAPI deprecation warning.

### Debug Log References

- New tests (red): `uv run --extra dev pytest -q tests/test_grading_service.py tests/test_grading_api.py` (ERROR — modules not yet created)
- Dependency added: `python-multipart==0.0.22` installed via `uv sync --extra dev`
- New tests (green): `uv run --extra dev pytest -q tests/test_grading_service.py tests/test_grading_api.py` (42 passed)
- Full regression: `uv run --extra dev pytest -q` (113 passed)

### Completion Notes List

- Created `app/domains/grading/` as a new domain module — first new domain since Epic 1.
- `InMemoryGradingRepository` uses same class-level state pattern as courses with `reset_state()` for test isolation. Seeded with `cls_demo_math_1`, `cls_demo_science_1`, `cls_other_org_1` and corresponding students.
- `GradingService.create_artifact` validates MIME type before access checks, raising `ArtifactFormatError` (422) for unsupported types and `GradingAccessError` (403) for auth/ownership failures.
- Class-boundary enforcement: `student.class_id != assignment.class_id` → 403. `stu_science_1` in `cls_demo_science_1` is rejected for artifacts on `cls_demo_math_1` assignments.
- Storage key pattern `s3://stub/{artifact_id}` is the hook Story 2.4 will use when submitting async AI grading jobs.
- `python-multipart>=0.0.9,<1.0.0` added to `pyproject.toml` dependencies — required for `Form(...)` and `File(...)` in FastAPI.
- Router registered in `app/main.py` alongside existing auth, admin, courses routers.

### File List

- _bmad-output/implementation-artifacts/2-3-capture-and-store-assignment-artifacts.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- apps/api/app/main.py
- apps/api/app/domains/grading/__init__.py
- apps/api/app/domains/grading/repository.py
- apps/api/app/domains/grading/service.py
- apps/api/app/domains/grading/schemas.py
- apps/api/app/domains/grading/router.py
- apps/api/README.md
- apps/api/pyproject.toml
- apps/api/uv.lock
- apps/api/tests/test_grading_service.py
- apps/api/tests/test_grading_api.py

### Senior Developer Review (AI)

- Reviewer: elephant
- Date: 2026-03-17
- Outcome: **Approved**

#### Findings Fixed (6)

- [HIGH] MIME type validated before assignment ownership — reordered so ownership check (403) always runs first; bad MIME type on unowned assignment no longer returns 422 (`apps/api/app/domains/grading/service.py`).
- [HIGH] Unused imports `ClassContextRecord`, `StudentContextRecord` in test file — removed (`apps/api/tests/test_grading_service.py`).
- [HIGH] Missing service-level cross-tenant test for `list_artifacts` — added `test_list_artifacts_fails_for_cross_tenant_assignment` (`apps/api/tests/test_grading_service.py`).
- [MEDIUM] `UploadFile` never closed — added `await file.close()` in `finally` block (`apps/api/app/domains/grading/router.py`).
- [MEDIUM] `image/gif` in allowlist with no test coverage — added `test_create_artifact_success_gif` (service) and `test_upload_artifact_gif_success` (API).
- [MEDIUM] `storage_key` exposes raw stub path — added presigned-URL warning comment for Story 2.4 (`apps/api/app/domains/grading/schemas.py`).

#### Acknowledged / Not Fixed

- [LOW] `python-multipart` lower bound tightened from `>=0.0.9` to `>=0.0.18`.
- [LOW] No `GradingRepository` Protocol defined — acknowledged as consistent with existing `courses` domain pattern; both use concrete type annotation on the service.

#### Test Counts

- Before: 113 passed
- After: 116 passed (3 new tests: gif service, gif API, list_artifacts cross-tenant)

### Change Log

- 2026-03-17: Implemented Story 2.3 grading domain with assignment creation and multipart artifact capture. Added 42 new tests (20 service, 22 API). Added python-multipart dependency. 113 tests passing total. Status set to review.
- 2026-03-17: Code review completed (elephant). 3 HIGH + 3 MEDIUM issues fixed; 2 LOW addressed/acknowledged. 116 tests passing. Story approved → done.

# Story 2.4: Submit and Process Async AI Grading Jobs

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want AI-assisted grading jobs to process asynchronously,
so that grading suggestions are produced reliably at scale.

## Acceptance Criteria

1. **Given** a valid submission artifact exists for an assignment
   **When** the teacher submits a grading job request for that artifact
   **Then** the system enqueues the grading job and returns a job record (job_id, status: "pending") within performance targets (NFR4: 95% acknowledge within 3 seconds)
   **And** the artifact's `storage_key` (e.g. `s3://stub/{artifact_id}`) is used as the input reference.

2. **Given** the grading job has completed processing
   **When** the teacher polls or opens grading review for that job
   **Then** the response includes the job status "completed"
   **And** contains a `result` block with `proposed_score`, `rubric_mapping` (criteria → rating), and `draft_feedback`.

3. **Given** a transient processing failure occurs during AI grading
   **When** the retry policy is applied
   **Then** the job is retried idempotently (attempt_count increments, same job_id reused)
   **And** no duplicate grade records are created for the same artifact.

4. **Given** the teacher submits a duplicate grading job request for an artifact that already has a job
   **When** the submission is evaluated
   **Then** the existing job record is returned rather than creating a new one (idempotency gate).

5. **Given** an unauthenticated request or a non-teacher actor
   **When** any grading job endpoint is called
   **Then** the response is 401 (unauthenticated) or 403 (non-teacher) respectively.

6. **Given** a request to a grading job on an unknown or cross-tenant assignment
   **When** authorization is evaluated
   **Then** the request fails closed with 403 and no job data is revealed.

## Tasks / Subtasks

- [x] Extend `app/domains/grading/repository.py` with grading job and result records (AC: 1, 2, 3, 4)
  - [x] Define `GradingJobRecord` dataclass: `job_id`, `artifact_id`, `assignment_id`, `org_id`, `teacher_user_id`, `status` (pending/processing/completed/failed), `attempt_count`, `submitted_at`, `completed_at`
  - [x] Define `GradingResultRecord` dataclass: `job_id`, `proposed_score`, `rubric_mapping` (dict), `draft_feedback`, `generated_at`
  - [x] Add class-level state to `InMemoryGradingRepository`: `_grading_jobs: dict[str, GradingJobRecord]`, `_grading_results: dict[str, GradingResultRecord]`, `_job_seq: int`, `_artifact_job_index: dict[str, str]` (artifact_id → job_id for idempotency)
  - [x] Reset `_grading_jobs`, `_grading_results`, `_job_seq`, `_artifact_job_index` in `reset_state()` and `_ensure_seed_data()`
  - [x] Implement `create_grading_job(artifact_id, assignment_id, org_id, teacher_user_id)` → `GradingJobRecord` with generated `job_id` (`"gjob_{seq}"`), status `"pending"`, `attempt_count=0`, `submitted_at=now`; index `artifact_id → job_id`
  - [x] Implement `get_grading_job_by_id(job_id)` → `GradingJobRecord | None`
  - [x] Implement `get_grading_job_for_artifact(artifact_id)` → `GradingJobRecord | None` (via `_artifact_job_index`)
  - [x] Implement `update_grading_job(job_id, status, attempt_count, completed_at)` → `GradingJobRecord` (replace record in `_grading_jobs`)
  - [x] Implement `save_grading_result(job_id, proposed_score, rubric_mapping, draft_feedback)` → `GradingResultRecord` with `generated_at=now`
  - [x] Implement `get_grading_result(job_id)` → `GradingResultRecord | None`

- [x] Extend `app/domains/grading/service.py` with grading job logic (AC: 1, 2, 3, 4, 6)
  - [x] Add service-level dataclasses `GradingJob` and `GradingResult` and `GradingJobWithResult` (mirrors of repository records, service layer objects)
  - [x] Implement `submit_grading_job(actor_user_id, actor_org_id, assignment_id, artifact_id)` → `GradingJob`
    - Verify artifact ownership (artifact exists, same org, same teacher, assignment matches) — fail-closed 403 on any mismatch
    - Idempotency check: if `get_grading_job_for_artifact(artifact_id)` is not None, return existing job (no new record)
    - Create new job via `create_grading_job(…)` with status "pending"
    - Return `GradingJob` from record
  - [x] Implement `process_grading_job(job_id)` → None (internal; called by background task or test helper)
    - Load job record; skip if already "completed" or "failed" (idempotency guard)
    - Set status → "processing", increment `attempt_count`
    - Run stub AI grading: generate fixed/deterministic result (see stub spec below)
    - On success: `save_grading_result(…)` + update job status → "completed" with `completed_at=now`
    - On simulated transient error (if attempt_count < 3, raise a test-injectable exception): update status → "failed" without saving result; caller should re-enqueue
  - [x] Implement `get_grading_job_status(actor_user_id, actor_org_id, assignment_id, job_id)` → `GradingJobWithResult`
    - Verify job exists and belongs to actor's org/teacher — fail-closed 403
    - Verify job's assignment_id matches path param — fail-closed 403
    - Load result if status is "completed"
    - Return `GradingJobWithResult`
  - [x] **Stub AI grading output spec**: `proposed_score = "85/100"`, `rubric_mapping = {"content_accuracy": "meets_expectations", "presentation": "exceeds_expectations", "completeness": "meets_expectations"}`, `draft_feedback = "Good work overall. Content is accurate and presentation is strong. Review completeness of answers on section 3."`

- [x] Add new schemas to `app/domains/grading/schemas.py` (AC: 1, 2)
  - [x] `GradingJobSubmitRequest`: `artifact_id` (str, min_length=3, max_length=64), `model_config = ConfigDict(extra="forbid")`
  - [x] `GradingJobResponse`: `job_id`, `artifact_id`, `assignment_id`, `status`, `attempt_count`, `submitted_at`, `completed_at` (str | None)
  - [x] `GradingResultResponse`: `proposed_score`, `rubric_mapping` (dict[str, str]), `draft_feedback`, `generated_at`
  - [x] `GradingJobWithResultResponse`: all fields of `GradingJobResponse` + `result: GradingResultResponse | None`

- [x] Add new router endpoints to `app/domains/grading/router.py` (AC: 1, 2, 5, 6)
  - [x] `POST /grading/assignments/{assignment_id}/grading-jobs` — submit grading job
    - Auth: `require_authenticated_actor`, `_require_teacher`
    - Body: `GradingJobSubmitRequest` (contains `artifact_id`)
    - On `GradingAccessError` → 403
    - Trigger background processing via `BackgroundTasks.add_task(process_grading_job_task, job_id=job.job_id, service=service)`
    - Return 202 `GradingJobResponse`
  - [x] `GET /grading/assignments/{assignment_id}/grading-jobs/{job_id}` — poll job status
    - Auth: `require_authenticated_actor`, `_require_teacher`
    - On `GradingAccessError` → 403
    - Return 200 `GradingJobWithResultResponse`
  - [x] Add `process_grading_job_task(job_id, service)` helper (sync or async) called by BackgroundTasks; calls `service.process_grading_job(job_id)` with error swallowing (log, don't propagate — background task failures must not crash the app)

- [x] Add tests for grading job submission, status polling, idempotency, and authorization (AC: 1–6)
  - [x] **Service tests** (`tests/test_grading_service.py`):
    - `test_submit_grading_job_success`: job created, status "pending", job_id pattern `"gjob_"`
    - `test_submit_grading_job_idempotent`: second submit for same artifact returns same job_id
    - `test_submit_grading_job_unknown_artifact_forbidden`: 403 via GradingAccessError
    - `test_submit_grading_job_cross_tenant_forbidden`: artifact in different org raises GradingAccessError
    - `test_process_grading_job_success`: after processing, status "completed", result has proposed_score/rubric_mapping/draft_feedback
    - `test_process_grading_job_idempotent_when_already_completed`: second call to process_grading_job is no-op
    - `test_get_grading_job_status_success_pending`: returns job with status "pending" and result=None
    - `test_get_grading_job_status_success_completed`: after processing, result populated
    - `test_get_grading_job_status_unknown_job_forbidden`: GradingAccessError on unknown job_id
    - `test_get_grading_job_status_cross_tenant_forbidden`: job in different org raises GradingAccessError
  - [x] **API tests** (`tests/test_grading_api.py`):
    - `test_submit_grading_job_success`: POST returns 202, body has job_id/status/artifact_id/assignment_id
    - `test_submit_grading_job_idempotent`: two POSTs for same artifact return same job_id
    - `test_submit_grading_job_unauthenticated`: 401
    - `test_submit_grading_job_non_teacher_forbidden`: 403
    - `test_submit_grading_job_unknown_artifact_forbidden`: 403
    - `test_get_grading_job_pending`: GET returns 200 with status "pending", result=null
    - `test_get_grading_job_completed`: after background processing settles, GET returns status "completed" with result block
    - `test_get_grading_job_unauthenticated`: 401
    - `test_get_grading_job_non_teacher_forbidden`: 403
    - `test_get_grading_job_unknown_job_forbidden`: 403
  - [x] Full regression: `cd apps/api && uv run --extra dev pytest -q` — 137 passed (116 pre-existing + 21 new)

- [x] Update docs and metadata (AC: 1)
  - [x] Update `apps/api/README.md` with grading job endpoints
  - [x] Update `apps/api/pyproject.toml` `[tool.ilm]` story to `"2.4"` with async grading job notes

## Dev Notes

### Core Design Decision: In-Memory Async Simulation

This story introduces the async grading job concept using **FastAPI BackgroundTasks** as the async dispatch mechanism — no external queue (SQS/Celery) is introduced in this in-memory phase. The pattern is:
1. `POST` endpoint accepts job, stores it as `"pending"`, enqueues `BackgroundTasks.add_task(…)` — returns 202 immediately
2. Background task runs `service.process_grading_job(job_id)` — transitions job to `"completed"` and saves stub AI result
3. `GET` endpoint polls job status — returns result when ready

**Why BackgroundTasks instead of a real queue:** Consistent with the in-memory stub pattern established in 2.3 (`s3://stub/`). Real SQS/Celery integration is post-MVP infrastructure work; the job data model and API contract are production-ready and will not need to change when the queue is swapped in.

### Idempotency Implementation

- `_artifact_job_index: dict[str, str]` maps `artifact_id → job_id` in the repository.
- `submit_grading_job` checks this index before creating a new job. If found, returns existing job.
- `process_grading_job` checks `job.status in {"completed", "failed"}` before processing — no-op if already done.
- These two guards together ensure zero duplicate grade records regardless of retry or resubmission.

### Stub AI Grading Output

All processed jobs will produce this deterministic result (needed for reliable test assertions):
```python
proposed_score = "85/100"
rubric_mapping = {
    "content_accuracy": "meets_expectations",
    "presentation": "exceeds_expectations",
    "completeness": "meets_expectations",
}
draft_feedback = (
    "Good work overall. Content is accurate and presentation is strong. "
    "Review completeness of answers on section 3."
)
```

### BackgroundTask Timing in Tests

FastAPI `BackgroundTasks` execute **after the response is sent** within the same process. In tests using `httpx.AsyncClient` + `ASGITransport`, background tasks run synchronously within the same `asyncio.run()` call before the test asserts on the response. This means the `test_get_grading_job_completed` test can reliably:
1. `POST` submit → returns 202 (background task queued)
2. After `asyncio.run()` returns, background task has already run → `GET` immediately returns status "completed"

No `sleep` or polling loop needed.

### Technical Requirements

- Extend the existing `grading` domain (`app/domains/grading/`) — do NOT create new modules or touch other domains.
- Follow the same layered pattern: thin router → service (business logic) → repository (storage).
- All new endpoints must use `require_authenticated_actor` + `_require_teacher` gate.
- Fail-closed (403) on any unknown or cross-tenant reference — job_id, artifact_id, assignment_id must all pass ownership checks.
- New endpoints:
  - `POST /grading/assignments/{assignment_id}/grading-jobs` → 202 `GradingJobResponse`
  - `GET /grading/assignments/{assignment_id}/grading-jobs/{job_id}` → 200 `GradingJobWithResultResponse`
- Use `status.HTTP_202_ACCEPTED` for job submission (not 201 — not fully created yet).
- The artifact's `storage_key` field (e.g. `s3://stub/artf_1`) is the notional input to the AI grading process — reference it in the service for completeness, even though the stub ignores it.

### Architecture Compliance

- `/grading` is the only module boundary touched in this story.
- Grading domain does NOT import from `app/domains/courses/` or any other domain.
- Route layer: thin, delegates all logic to service + BackgroundTasks.
- Service: all business rules, idempotency, and stub AI logic.
- Repository: all state storage and index management.
- `GradingJobRecord` and `GradingResultRecord` are added to the existing `repository.py` — not new files.

### Library / Framework Requirements

- **FastAPI `BackgroundTasks`**: inject as `background_tasks: BackgroundTasks` parameter in the submit endpoint. Import from `fastapi`.
- **Pydantic v2** with `extra="forbid"` on all new request schemas.
- **FastAPI range `>=0.115.0,<1.0.0`** (unchanged).
- **No new runtime dependencies** needed — all capabilities are already in the installed FastAPI version.

### File Structure Requirements

**Modified files only** (no new files needed):
- `apps/api/app/domains/grading/repository.py` — add `GradingJobRecord`, `GradingResultRecord`, new repository methods, state fields
- `apps/api/app/domains/grading/service.py` — add `GradingJob`, `GradingResult`, `GradingJobWithResult` dataclasses, new service methods
- `apps/api/app/domains/grading/schemas.py` — add `GradingJobSubmitRequest`, `GradingJobResponse`, `GradingResultResponse`, `GradingJobWithResultResponse`
- `apps/api/app/domains/grading/router.py` — add submit and poll endpoints, `process_grading_job_task` helper
- `apps/api/tests/test_grading_service.py` — add service-level tests for job submission, processing, idempotency
- `apps/api/tests/test_grading_api.py` — add API-level tests for submit, poll, idempotency, auth
- `apps/api/README.md` — document new grading job endpoints
- `apps/api/pyproject.toml` — update `[tool.ilm]` story marker

**Do NOT modify:**
- `apps/api/app/main.py` — grading router already registered; no changes needed
- `apps/api/app/domains/auth/` — no auth changes required
- Any other domain

### Testing Requirements

- **Auth regression** (all new endpoints): unauthenticated → 401, non-teacher → 403, cross-tenant → 403.
- **Idempotency test**: submit same artifact_id twice → same job_id returned, only one job record exists.
- **Processing idempotency**: calling `process_grading_job` twice on a completed job is a no-op (no duplicate result records).
- **Result shape**: completed job result must have `proposed_score`, `rubric_mapping` (dict with at least 1 key), `draft_feedback` (non-empty string).
- **Pending state**: freshly submitted job has `status="pending"` and `result=null` on GET.
- **Unknown job fail-closed**: GET with unknown `job_id` → 403.
- **setup_function** already resets grading state via `reset_grading_state_for_tests()` — ensure new state (`_grading_jobs`, `_grading_results`, `_job_seq`, `_artifact_job_index`) is also reset in `reset_state()`.

### Previous Story Intelligence

- **Story 2.3 established patterns** (MUST follow exactly):
  - `InMemoryGradingRepository` uses class-level state dicts with `_seeded` guard — add new state dicts (`_grading_jobs`, `_grading_results`, `_job_seq`, `_artifact_job_index`) to the same class-level pattern.
  - `reset_state()` calls `_ensure_seed_data()` which resets everything — add new state fields there too.
  - Sequence IDs use `_*_seq` pattern (e.g., `_assignment_seq`, `_artifact_seq`) → new: `_job_seq` generating `"gjob_{n}"`.
  - Fail-closed 403 for unknown/cross-tenant always via `GradingAccessError("Forbidden")`.

- **Code review findings from Story 2.3** (apply to Story 2.4):
  - [HIGH] Ownership check MUST run before payload/content validation — if actor doesn't own the artifact, they get 403 regardless of other errors.
  - [HIGH] All new endpoints need explicit `401` and `403` tests (unauthenticated AND non-teacher).
  - [MEDIUM] `UploadFile` was closed with `finally` block in router — Story 2.4 does not use UploadFile, but apply similar defensive hygiene to any resources opened in the background task.

- **Story 2.3 noted explicitly** (`storage_key` comment in schemas.py): "Story 2.4 must replace this with a presigned-URL accessor and never expose raw bucket paths in production responses." — Story 2.4 reads `storage_key` as input to the AI job but does NOT need to change `ArtifactResponse.storage_key` yet; that is a production concern for real S3 integration.

- **Test helper pattern**: tests use `asyncio.run(scenario())` with inner `async def scenario()` and `httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")`. Keep this pattern exactly.

- **Token helper pattern**: `_teacher_headers()` creates token for `sub="usr_teacher_1", org_id="org_demo_1", role="teacher"`. Re-use `_create_assignment` helper already defined in test file to create prerequisite assignment, and add `_upload_artifact` helper for artifact prerequisite.

### References

- [Source: _bmad-output/implementation-artifacts/epics.md#Story 2.4: Submit and Process Async AI Grading Jobs]
- [Source: _bmad-output/planning-artifacts/prd.md#FR42, NFR4, NFR5, NFR15]
- [Source: _bmad-output/implementation-artifacts/2-3-capture-and-store-assignment-artifacts.md#Dev Agent Record]
- [Source: apps/api/app/domains/grading/repository.py] — class-level state pattern
- [Source: apps/api/app/domains/grading/service.py] — GradingAccessError pattern, ownership check ordering
- [Source: apps/api/app/domains/grading/router.py] — _require_teacher, BackgroundTasks injection pattern
- [Source: apps/api/app/domains/grading/schemas.py] — Pydantic v2 schema pattern with ConfigDict(extra="forbid")
- [Source: apps/api/tests/test_grading_api.py] — asyncio.run/httpx.AsyncClient test pattern

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Implementation Plan

- Extended `InMemoryGradingRepository` with `GradingJobRecord`, `GradingResultRecord`, `_grading_jobs`, `_grading_results`, `_artifact_job_index` class-level state and all required CRUD methods. `reset_state()` and `_ensure_seed_data()` both clear new state.
- Added `GradingJob`, `GradingResult`, `GradingJobWithResult` service-layer dataclasses. Implemented `submit_grading_job` (ownership check → idempotency gate → create), `process_grading_job` (idempotency guard → processing → save stub result → completed), and `get_grading_job_status` (ownership check → load result if completed).
- Added `GradingJobSubmitRequest`, `GradingJobResponse`, `GradingResultResponse`, `GradingJobWithResultResponse` Pydantic v2 schemas with `extra="forbid"` on request schema.
- Added `POST /grading/assignments/{id}/grading-jobs` (202) and `GET /grading/assignments/{id}/grading-jobs/{job_id}` (200) endpoints. Background task (`_process_grading_job_task`) swallows errors to prevent background failures from crashing the app.
- All new endpoints gated with `_require_teacher` + `require_authenticated_actor`; fail-closed 403 on all unknown/cross-tenant references.
- 21 new tests: 11 service-level (job submission, processing, idempotency, polling, auth) + 10 API-level. Full regression: 137 passed.

### Debug Log References

- New service tests (red): `uv run --extra dev pytest -q tests/test_grading_service.py` — ERRORS (modules not yet extended)
- New API tests (red): `uv run --extra dev pytest -q tests/test_grading_api.py` — ERRORS (endpoints not yet added)
- Implementation complete (green): `uv run --extra dev pytest -q` — 137 passed

### Completion Notes List

- `GradingJobRecord.completed_at` is `str | None` (frozen dataclass); `update_grading_job` replaces the immutable record in the dict to simulate mutation.
- Ownership check in `submit_grading_job` verifies: artifact exists, same org, same teacher, AND `artifact.assignment_id == assignment_id` path param — fail-closed 403 on any mismatch.
- `process_grading_job` idempotency guard (`status in {"completed", "failed"}`) prevents duplicate result records on retry or double-invocation.
- In `httpx.ASGITransport` tests, `BackgroundTasks` run synchronously within the same `asyncio.run()` call, so `test_get_grading_job_completed` reliably asserts `status == "completed"` immediately after the submit POST.
- `pytest` import added to `test_grading_service.py` for `pytest.raises` usage in new tests.
- No new dependencies required — `BackgroundTasks` ships with FastAPI.

### File List

- _bmad-output/implementation-artifacts/2-4-submit-and-process-async-ai-grading-jobs.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- apps/api/app/domains/grading/repository.py
- apps/api/app/domains/grading/service.py
- apps/api/app/domains/grading/schemas.py
- apps/api/app/domains/grading/router.py
- apps/api/tests/test_grading_service.py
- apps/api/tests/test_grading_api.py
- apps/api/README.md
- apps/api/pyproject.toml

### Change Log

- 2026-03-17: Implemented Story 2.4 async AI grading job submission and polling. Added GradingJobRecord/GradingResultRecord to repository, GradingJob/GradingResult/GradingJobWithResult service dataclasses, 4 new Pydantic schemas, 2 new endpoints (POST 202, GET 200), BackgroundTasks processing. 21 new tests added. 137 tests passing total. Status set to review.

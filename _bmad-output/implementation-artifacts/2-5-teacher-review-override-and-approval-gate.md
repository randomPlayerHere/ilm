# Story 2.5: Teacher Review, Override, and Approval Gate

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want to review or override AI grading outputs and explicitly approve results,
So that final grading authority remains with me and approved grades are gated from parent/student visibility until I confirm them.

## Acceptance Criteria

1. **Given** a completed AI grading job exists for a submission
   **When** the teacher submits an approval (with optional score/feedback overrides)
   **Then** the approved values are stored with `approver_user_id` and `approved_at` timestamp
   **And** a `GradeVersion` record is created capturing the approved state (version=1 for first approval)
   **And** the response includes `job_id`, `approved_score`, `approved_feedback`, `approver_user_id`, `approved_at`, `version`.

2. **Given** a teacher has already approved a grading job and re-submits an approval with different values
   **When** the re-approval is processed
   **Then** the `GradeApprovalRecord` is updated with the new values and `version` is incremented
   **And** a new `GradeVersion` record is appended (prior versions are preserved, not overwritten)
   **And** the response reflects the latest version.

3. **Given** a grading job that has NOT yet reached `status == "completed"`
   **When** the teacher attempts to approve it
   **Then** the request fails with `409 Conflict` (cannot approve an unfinished job).

4. **Given** a grading job with at least one approval
   **When** the teacher requests the version history
   **Then** the response returns all `GradeVersion` records for that job, ordered by `version` ascending
   **And** each version includes `version`, `approved_score`, `approved_feedback`, `editor_user_id`, `edited_at`, `is_approved`.

5. **Given** a grading job that has been approved
   **When** `GET /grading/assignments/{id}/grading-jobs/{job_id}` is called
   **Then** the response includes `is_approved: true`
   **And** `GET /grading/assignments/{id}/grading-jobs/{job_id}/approval` returns the current approval record.

6. **Given** a grading job that has NOT been approved
   **When** `GET /grading/assignments/{id}/grading-jobs/{job_id}/approval` is called
   **Then** the response is `403 Forbidden` (approval not yet exists; fail-closed to prevent enumeration)
   **And** `GET /grading/assignments/{id}/grading-jobs/{job_id}` returns `is_approved: false`.

7. **Given** an unauthenticated request or a non-teacher actor
   **When** any approval endpoint is called
   **Then** the response is `401` (unauthenticated) or `403` (non-teacher) respectively.

8. **Given** a request referencing a job on an unknown or cross-tenant assignment
   **When** authorization is evaluated
   **Then** the request fails closed with `403` and no approval data is revealed.

## Tasks / Subtasks

- [x] Extend `app/domains/grading/repository.py` with grade approval and version records (AC: 1, 2, 4, 5, 6)
  - [x] Define `GradeApprovalRecord` dataclass (frozen=True): `job_id`, `approved_score`, `approved_feedback`, `approver_user_id`, `approved_at`, `version` (int)
  - [x] Define `GradeVersionRecord` dataclass (frozen=True): `job_id`, `version` (int), `approved_score`, `approved_feedback`, `editor_user_id`, `edited_at`, `is_approved` (bool)
  - [x] Add class-level state to `InMemoryGradingRepository`: `_grade_approvals: dict[str, GradeApprovalRecord]` (keyed by job_id), `_grade_versions: dict[str, list[GradeVersionRecord]]` (keyed by job_id), `_approval_seq: int`
  - [x] Reset `_grade_approvals`, `_grade_versions`, `_approval_seq` in `reset_state()` AND `_ensure_seed_data()`
  - [x] Implement `upsert_grade_approval(job_id, approved_score, approved_feedback, approver_user_id, version)` → `GradeApprovalRecord` (replace existing record for same job_id)
  - [x] Implement `get_grade_approval(job_id)` → `GradeApprovalRecord | None`
  - [x] Implement `append_grade_version(job_id, version, approved_score, approved_feedback, editor_user_id, is_approved)` → `GradeVersionRecord` (append to list; create list if first entry)
  - [x] Implement `list_grade_versions(job_id)` → `list[GradeVersionRecord]` sorted by `version` ascending

- [x] Extend `app/domains/grading/service.py` with approval logic (AC: 1, 2, 3, 4, 5, 6, 8)
  - [x] Add `GradingStateError(Exception)` — raised when job is in wrong state for the operation (maps to 409)
  - [x] Add `GradeApproval` service dataclass (frozen=True): `job_id`, `approved_score`, `approved_feedback`, `approver_user_id`, `approved_at`, `version`
  - [x] Add `GradeVersion` service dataclass (frozen=True): `job_id`, `version`, `approved_score`, `approved_feedback`, `editor_user_id`, `edited_at`, `is_approved`
  - [x] Update `GradingJobWithResult` dataclass: add `is_approved: bool` field (default False)
  - [x] Implement `approve_grading_job(actor_user_id, actor_org_id, assignment_id, job_id, approved_score, approved_feedback)` → `GradeApproval`
    - Verify job exists and is owned by actor (same org, same teacher, same assignment_id) — fail-closed 403 via `GradingAccessError`
    - Verify `job.status == "completed"` — if not, raise `GradingStateError("Job must be completed before approval")`
    - Get existing approval (if any) → `new_version = existing.version + 1`; else `new_version = 1`
    - Call `repository.append_grade_version(job_id, new_version, approved_score, approved_feedback, actor_user_id, is_approved=True)`
    - Call `repository.upsert_grade_approval(job_id, approved_score, approved_feedback, actor_user_id, new_version)` with `approved_at = now`
    - Return `GradeApproval` from record
  - [x] Implement `get_grade_approval(actor_user_id, actor_org_id, assignment_id, job_id)` → `GradeApproval`
    - Verify job ownership — fail-closed 403
    - Load approval record; if None → raise `GradingAccessError("Forbidden")` (fail-closed, no 404)
    - Return `GradeApproval`
  - [x] Implement `list_grade_versions(actor_user_id, actor_org_id, assignment_id, job_id)` → `list[GradeVersion]`
    - Verify job ownership — fail-closed 403
    - Return sorted version list
  - [x] Update `get_grading_job_status` to populate `is_approved = repository.get_grade_approval(job_id) is not None`

- [x] Add new schemas to `app/domains/grading/schemas.py` (AC: 1, 2, 4, 5)
  - [x] `GradeApprovalRequest`: `approved_score` (str, min_length=1, max_length=50), `approved_feedback` (str, min_length=1, max_length=2000), `model_config = ConfigDict(extra="forbid")`
  - [x] `GradeApprovalResponse`: `job_id`, `approved_score`, `approved_feedback`, `approver_user_id`, `approved_at`, `version` (int)
  - [x] `GradeVersionResponse`: `job_id`, `version` (int), `approved_score`, `approved_feedback`, `editor_user_id`, `edited_at`, `is_approved` (bool)
  - [x] `GradeVersionListResponse`: `versions: list[GradeVersionResponse]`
  - [x] Update `GradingJobWithResultResponse`: add `is_approved: bool` field

- [x] Add new router endpoints to `app/domains/grading/router.py` (AC: 1–8)
  - [x] Import `GradingStateError` from service; import new schemas
  - [x] Add `_to_grade_approval_response(approval: GradeApproval) -> GradeApprovalResponse` helper
  - [x] Add `_to_grade_version_response(v: GradeVersion) -> GradeVersionResponse` helper
  - [x] Update `_to_grading_job_with_result_response` to include `is_approved` field
  - [x] `POST /grading/assignments/{assignment_id}/grading-jobs/{job_id}/approve` → 200 `GradeApprovalResponse`
    - Auth: `require_authenticated_actor`, `_require_teacher`
    - Body: `GradeApprovalRequest`
    - On `GradingAccessError` → 403
    - On `GradingStateError` → 409
    - Return 200 `GradeApprovalResponse`
  - [x] `GET /grading/assignments/{assignment_id}/grading-jobs/{job_id}/approval` → 200 `GradeApprovalResponse`
    - Auth: `require_authenticated_actor`, `_require_teacher`
    - On `GradingAccessError` → 403
    - Return 200 `GradeApprovalResponse`
  - [x] `GET /grading/assignments/{assignment_id}/grading-jobs/{job_id}/versions` → 200 `GradeVersionListResponse`
    - Auth: `require_authenticated_actor`, `_require_teacher`
    - On `GradingAccessError` → 403
    - Return 200 `GradeVersionListResponse`

- [x] Add tests for approval, version history, visibility gate, and authorization (AC: 1–8)
  - [x] **Service tests** (`tests/test_grading_service.py`):
    - `test_approve_grading_job_success`: approved_score/feedback stored, version=1, approver_user_id set, approved_at non-empty
    - `test_approve_grading_job_override_score`: teacher sets different score than AI's proposed_score; stored correctly
    - `test_approve_grading_job_reapproval_increments_version`: second approve call → version=2, prior version preserved in list_grade_versions
    - `test_approve_grading_job_fails_if_not_completed`: job status "pending" → raises `GradingStateError`
    - `test_approve_grading_job_cross_tenant_forbidden`: different org → raises `GradingAccessError`
    - `test_approve_grading_job_unknown_job_forbidden`: unknown job_id → raises `GradingAccessError`
    - `test_get_grade_approval_success`: returns correct approval after approve call
    - `test_get_grade_approval_unapproved_returns_forbidden`: no approval yet → `GradingAccessError`
    - `test_list_grade_versions_after_two_approvals`: two approve calls → two versions in ascending order
    - `test_get_grading_job_status_is_approved_false_before_approval`: `is_approved == False` when not yet approved
    - `test_get_grading_job_status_is_approved_true_after_approval`: `is_approved == True` after approve call
  - [x] **API tests** (`tests/test_grading_api.py`):
    - `test_approve_grading_job_success`: POST 200, body has approved_score, approved_feedback, approver_user_id, approved_at, version=1
    - `test_approve_grading_job_reapproval_increments_version`: second POST 200, version=2
    - `test_approve_grading_job_unauthenticated`: 401
    - `test_approve_grading_job_non_teacher_forbidden`: 403
    - `test_approve_grading_job_not_completed_conflict`: approve a job that was never processed → 409
    - `test_get_grade_approval_success`: GET 200 after approval
    - `test_get_grade_approval_unapproved_forbidden`: GET 403 when no approval exists
    - `test_list_grade_versions_success`: GET 200, `versions` list non-empty after approval
    - `test_get_grading_job_with_result_includes_is_approved_field`: GET job response includes `is_approved` bool

- [x] Update docs and metadata
  - [x] Update `apps/api/README.md` with new approval endpoints
  - [x] Update `apps/api/pyproject.toml` `[tool.ilm]` story to `"2.5"` with approval gate notes

## Dev Notes

### Core Design Decision: Approval as Immutable Ledger

Per architecture mandate: *"Grade publication rule: immutable approval ledger; no parent/student visibility pre-approval."*

The approval flow in this story:
1. Teacher calls `POST .../approve` with optional overrides of AI's `proposed_score`/`draft_feedback`
2. System stores a `GradeApprovalRecord` (latest approved state, upserted per job_id)
3. Each approval also appends a `GradeVersionRecord` (immutable history — never deleted or overwritten)
4. The `is_approved` flag on `GradingJobWithResult` drives the visibility gate for downstream Epic 3 endpoints

**Why upsert for `GradeApprovalRecord`?** The approval record represents current authoritative state (what parent/student would see). Re-approvals update this. Version history is in the separate `_grade_versions` list.

**Why fail-closed 403 on `GET .../approval` when unapproved?** Consistent with the fail-closed pattern established in 2.3/2.4. Returning 404 leaks information about job existence to callers who shouldn't have it. Since all approval endpoints are teacher-only, this simplifies the implementation — any missing record → 403.

### `is_approved` Field on `GradingJobWithResultResponse`

Story 2.4 added `GradingJobWithResultResponse` without `is_approved`. This story adds it. The field must be added to:
1. `GradingJobWithResult` service dataclass — add `is_approved: bool` (default value `False`)
2. `GradingJobWithResultResponse` Pydantic schema — add `is_approved: bool`
3. `get_grading_job_status` service method — populate `is_approved = repository.get_grade_approval(job_id) is not None`
4. `_to_grading_job_with_result_response` router helper — pass through `is_approved`

**Test impact**: existing `test_get_grading_job_completed` test will now receive `is_approved: false` in the response body — this is fine; assertions on `status == "completed"` and `result` fields are unaffected. No test breakage expected.

### `GradingStateError` → HTTP 409

New exception for state-transition violations:
```python
class GradingStateError(Exception):
    pass
```
Router maps it: `except GradingStateError as exc: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc`

### Approval Data Model (In-Memory)

```python
@dataclass(frozen=True)
class GradeApprovalRecord:
    job_id: str
    approved_score: str
    approved_feedback: str
    approver_user_id: str
    approved_at: str       # ISO 8601
    version: int           # 1-based; increments on re-approval

@dataclass(frozen=True)
class GradeVersionRecord:
    job_id: str
    version: int
    approved_score: str
    approved_feedback: str
    editor_user_id: str
    edited_at: str         # ISO 8601
    is_approved: bool      # always True in current flow (only approved edits create versions)
```

Class-level state in `InMemoryGradingRepository`:
```python
_grade_approvals: dict[str, GradeApprovalRecord] = {}   # job_id → latest approval
_grade_versions: dict[str, list[GradeVersionRecord]] = {}  # job_id → ordered list of versions
_approval_seq: int = 0  # reserved for future use; not needed for current ID scheme
```

Reset in both `reset_state()` → `_ensure_seed_data()`:
```python
cls._grade_approvals = {}
cls._grade_versions = {}
cls._approval_seq = 0
```

### `approve_grading_job` Implementation Pattern

```python
def approve_grading_job(self, actor_user_id, actor_org_id, assignment_id, job_id,
                         approved_score, approved_feedback) -> GradeApproval:
    job = self._repository.get_grading_job_by_id(job_id)
    if job is None:
        raise GradingAccessError("Forbidden")
    if job.org_id != actor_org_id or job.teacher_user_id != actor_user_id:
        raise GradingAccessError("Forbidden")
    if job.assignment_id != assignment_id:
        raise GradingAccessError("Forbidden")
    if job.status != "completed":
        raise GradingStateError("Job must be completed before approval")

    existing = self._repository.get_grade_approval(job_id)
    new_version = (existing.version + 1) if existing is not None else 1
    now = datetime.now(UTC).isoformat()

    self._repository.append_grade_version(
        job_id, new_version, approved_score, approved_feedback, actor_user_id, is_approved=True
    )
    record = self._repository.upsert_grade_approval(
        job_id, approved_score, approved_feedback, actor_user_id, new_version, approved_at=now
    )
    return self._to_grade_approval(record)
```

### Visibility Gate (Forward Compatibility Note for Epic 3)

This story establishes `is_approved` on `GradingJobWithResult`. Epic 3 parent/student progress endpoints will:
1. Fetch grade data via internal service calls
2. Check `is_approved` — if False, omit grade/feedback from parent/student response (AC2 of this story)

This story does NOT add parent/student endpoints — that is Epic 3 scope. But the gate mechanism (`is_approved` field + `get_grade_approval` repository method) must be production-ready in this story.

### Architecture Compliance

- Only `app/domains/grading/` is touched — no other domain imports
- All new service dataclasses go in `service.py`; all new repository records in `repository.py`
- No new files needed — same pattern as 2.4
- `GradeApprovalRecord` and `GradeVersionRecord` follow `frozen=True` dataclass pattern (same as `GradingJobRecord`)
- `upsert_grade_approval` replaces the dict entry by key — `frozen` record is replaced, not mutated
- `append_grade_version` creates list if not present: `cls._grade_versions.setdefault(job_id, []).append(record)`

### Technical Requirements

- All new endpoints: `require_authenticated_actor` + `_require_teacher`
- Fail-closed 403 on: unknown job, cross-tenant job, unapproved job (for GET approval)
- 409 Conflict on: approve attempt when job.status != "completed"
- `approved_score` and `approved_feedback` are free-form strings — teacher can set any value
  - Validation: min_length=1 (non-empty), approved_score max_length=50, approved_feedback max_length=2000
- `approved_at` uses `datetime.now(UTC).isoformat()` — same pattern as `submitted_at`, `completed_at`

### Library / Framework Requirements

- No new dependencies — everything uses existing FastAPI + Pydantic v2
- `status.HTTP_409_CONFLICT` is available in `fastapi.status` (no import change)
- `ConfigDict(extra="forbid")` on `GradeApprovalRequest` — same pattern as all request schemas

### File Structure Requirements

**Modified files only** (no new files):
- `apps/api/app/domains/grading/repository.py` — add `GradeApprovalRecord`, `GradeVersionRecord`, state fields, 4 new repository methods
- `apps/api/app/domains/grading/service.py` — add `GradingStateError`, `GradeApproval`, `GradeVersion` dataclasses; update `GradingJobWithResult`; add 3 service methods; update `get_grading_job_status`
- `apps/api/app/domains/grading/schemas.py` — add `GradeApprovalRequest`, `GradeApprovalResponse`, `GradeVersionResponse`, `GradeVersionListResponse`; update `GradingJobWithResultResponse`
- `apps/api/app/domains/grading/router.py` — import `GradingStateError` + new schemas; add 2 helpers; add 3 endpoints; update `_to_grading_job_with_result_response`
- `apps/api/tests/test_grading_service.py` — add 11 service tests in new `# --- Approval gate ---` section
- `apps/api/tests/test_grading_api.py` — add 9 API tests in new `# --- Approval endpoints ---` section
- `apps/api/README.md` — add 3 new endpoints to the list
- `apps/api/pyproject.toml` — update `[tool.ilm]` story to `"2.5"`

**Do NOT modify:**
- `apps/api/app/main.py` — grading router already registered
- `apps/api/app/domains/auth/` — no auth changes
- Any other domain

### Testing Requirements

- **Auth regression** on ALL new endpoints: unauthenticated → 401, non-teacher → 403
- **State-gate test**: attempt approval on a job with `status != "completed"` → 409
- **Version history**: two approve calls → two version records, correct ordering
- **Override test**: `approved_score` different from AI's `proposed_score="85/100"` → custom value persisted
- **`is_approved` on job response**: False before approval, True after
- **Re-use `setup_function`** in service tests (already resets `InMemoryGradingRepository.reset_state()`); clear `GradingService._fail_on_job_ids` as already done in `setup_function`
- **API test helper pattern**: re-use `_create_assignment`, `_upload_artifact`; add `_submit_and_process_job(client, assignment_id, artifact_id)` helper that: submits job → waits for background task to complete → returns job_id ready for approval

### `_submit_and_process_job` API Test Helper

```python
async def _submit_and_process_job(client, assignment_id: str, artifact_id: str) -> str:
    """Submit a grading job and wait for background processing; return job_id."""
    resp = await client.post(
        f"/grading/assignments/{assignment_id}/grading-jobs",
        headers=_teacher_headers(),
        json={"artifact_id": artifact_id},
    )
    assert resp.status_code == 202
    # BackgroundTasks run synchronously in ASGITransport — job is already completed
    return resp.json()["job_id"]
```

### Previous Story Intelligence

- **Story 2.4 established patterns** (MUST follow exactly):
  - `InMemoryGradingRepository` class-level state with `_seeded` guard — extend by adding `_grade_approvals`, `_grade_versions` to same class body
  - `reset_state()` → calls `_ensure_seed_data()` which resets EVERYTHING — must add new fields there
  - `frozen=True` dataclass records replaced by key reassignment (not mutated)
  - `GradingService._fail_on_job_ids` is a class-level set for test injection — new state follows same placement in the class body
  - Background task returns synchronously in `httpx.ASGITransport` tests — so after `POST .../grading-jobs`, job is already "completed" → safe to call `POST .../approve` immediately in the same `asyncio.run()` block

- **Code review findings from Story 2.4** (apply to Story 2.5):
  - [H2] Only enqueue background task on newly created jobs (status == "pending" AND attempt_count == 0) — no impact on 2.5 but understand the pattern
  - [H3] `GradingService._fail_on_job_ids` error injection is now available — don't need it for 2.5 but don't remove it
  - [M3] `update_grading_job` now has a guard — `upsert_grade_approval` should similarly use `.get()` + explicit error if needed

- **Test file state after 2.4 code review fixes**: `test_grading_service.py` now imports `GradingProcessError` and `test_get_grading_job_pending` was renamed to `test_get_grading_job_returns_200`. The `setup_function` now calls `GradingService._fail_on_job_ids.clear()`. All of this is already in the file — do not revert.

### References

- [Source: _bmad-output/implementation-artifacts/epics.md#Story 2.5: Teacher Review, Override, and Approval Gate]
- [Source: _bmad-output/planning-artifacts/prd.md#FR15, FR16, FR17, FR35, NFR10, NFR14]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Grade publication rule, Data model, Grading pipeline]
- [Source: _bmad-output/implementation-artifacts/2-4-submit-and-process-async-ai-grading-jobs.md#Dev Notes, Dev Agent Record]
- [Source: apps/api/app/domains/grading/repository.py] — class-level state + frozen dataclass replace pattern
- [Source: apps/api/app/domains/grading/service.py] — GradingAccessError pattern, ownership check ordering
- [Source: apps/api/app/domains/grading/router.py] — _require_teacher, 409 pattern
- [Source: apps/api/tests/test_grading_api.py] — asyncio.run/httpx.AsyncClient test helper pattern

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation proceeded without blocking issues.

### Completion Notes List

- All 8 ACs implemented across 4 layers (repository → service → schemas → router).
- `GradeApprovalRecord` is upserted per job_id (latest authoritative state); `GradeVersionRecord` list is append-only immutable history — satisfies both re-approval override and prior-version auditability.
- `is_approved` field threads through `GradingJobWithResult` service dataclass → `GradingJobWithResultResponse` schema → `_to_grading_job_with_result_response` helper — existing tests unaffected (field defaults to `false`).
- `GradingStateError` → HTTP 409 for approve-on-non-completed; `GradingAccessError` → HTTP 403 for all fail-closed cases including unapproved GET.
- In ASGITransport tests background tasks run synchronously, so `POST .../grading-jobs` immediately yields a completed job ready for approval in the same `asyncio.run()` block. For the 409 test, a pending job is injected directly via `_grading_service._repository.create_grading_job()` to bypass background processing.
- 46 service tests + 9 new API approval tests added during dev; 6 additional tests added during code review (H1, M2, M3 fixes).
- No new files created — all changes confined to `apps/api/app/domains/grading/` and test files.

### File List

- `apps/api/app/domains/grading/repository.py` — added `GradeApprovalRecord`, `GradeVersionRecord` dataclasses; class-level state `_grade_approvals`, `_grade_versions`, `_approval_seq`; 4 new repository methods; reset in `reset_state()`/`_ensure_seed_data()`
- `apps/api/app/domains/grading/service.py` — added `GradingStateError`, `GradeApproval`, `GradeVersion` dataclasses; `is_approved` on `GradingJobWithResult`; 3 new service methods (`approve_grading_job`, `get_grade_approval`, `list_grade_versions`); updated `get_grading_job_status`; private helpers `_to_grade_approval`, `_to_grade_version`
- `apps/api/app/domains/grading/schemas.py` — added `GradeApprovalRequest`, `GradeApprovalResponse`, `GradeVersionResponse`, `GradeVersionListResponse`; added `is_approved: bool` to `GradingJobWithResultResponse`
- `apps/api/app/domains/grading/router.py` — added imports; helpers `_to_grade_approval_response`, `_to_grade_version_response`; 3 new endpoints (POST approve, GET approval, GET versions); updated `_to_grading_job_with_result_response`
- `apps/api/tests/test_grading_service.py` — added 11 service tests in `# --- Approval gate ---` section; updated imports; removed duplicate `_create_demo_artifact` (H1 code review fix); added `test_get_grade_approval_cross_tenant_forbidden`, `test_list_grade_versions_cross_tenant_forbidden` (M3 code review fix)
- `apps/api/tests/test_grading_api.py` — added 9 API tests in `# --- Approval endpoints ---` section; added `_submit_and_process_job` async helper; added 4 auth tests for GET /approval and GET /versions (M2 code review fix)
- `apps/api/README.md` — added 3 new endpoints to Story Scope list
- `apps/api/pyproject.toml` — updated `[tool.ilm]` story to `"2.5"` with approval gate notes
- `.gitignore` — added Python `__pycache__`/`.pyc` entries (code review H1 fix from 2.4)

### Change Log

- **repository.py**: Added `GradeApprovalRecord` + `GradeVersionRecord` frozen dataclasses; added `_grade_approvals`, `_grade_versions`, `_approval_seq` class-level state; implemented `upsert_grade_approval`, `get_grade_approval`, `append_grade_version`, `list_grade_versions`; reset new state in `reset_state()`/`_ensure_seed_data()`; fixed `update_grading_job` to use `.get()` + explicit `KeyError` (code review M3)
- **service.py**: Added `GradingStateError`; added `GradeApproval`, `GradeVersion` dataclasses; added `is_approved: bool = False` to `GradingJobWithResult`; implemented `approve_grading_job`, `get_grade_approval`, `list_grade_versions`; updated `get_grading_job_status` to populate `is_approved`; added `GradingProcessError` + `_fail_on_job_ids` error injection (code review H3)
- **schemas.py**: Added 4 new Pydantic models; added `is_approved: bool` to `GradingJobWithResultResponse`
- **router.py**: Added 3 endpoints; added 2 response helpers; updated job response helper; added background-task idempotency guard (code review H2)
- **test_grading_service.py**: Added 11 approval gate tests; updated `setup_function` to clear `_fail_on_job_ids`
- **test_grading_api.py**: Added 9 approval endpoint tests; fixed misleading test name (code review M2); added mismatch test (code review M4)

# Story 2.6: Generate Weakness-Based Practice Recommendations

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a teacher,
I want targeted practice recommendations based on weak areas identified in AI grading,
So that students receive timely intervention guidance linked to their specific performance gaps.

## Acceptance Criteria

1. **Given** an approved grading job exists for a student submission
   **When** the teacher submits a recommendation-generation request (`POST .../recommendation-jobs`)
   **Then** the system returns `202 Accepted` with a `rec_job_id`
   **And** processes the job asynchronously (BackgroundTasks) producing topic-linked practice suggestions
   **And** the request is idempotent — a second POST for the same grading job returns the existing `rec_job_id`.

2. **Given** a recommendation job has completed processing
   **When** the teacher polls `GET .../recommendation-jobs/{rec_job_id}`
   **Then** the response includes `status: "completed"` and a `result` block
   **And** `result.topics` is a list of items each with `topic`, `suggestion`, and `weakness_signal`
   **And** topics are derived from rubric dimensions that did not achieve "exceeds_expectations".

3. **Given** a grading job that has NOT been teacher-approved (via story 2.5)
   **When** the teacher attempts to generate recommendations
   **Then** the request fails with `409 Conflict` (`GradingStateError`: "Grading job must be approved before generating recommendations").

4. **Given** a completed recommendation job exists
   **When** the teacher confirms (with optional topic edits) via `POST .../recommendation-jobs/{rec_job_id}/confirm`
   **Then** the confirmed recommendations are stored with `confirmed_by` (actor user_id), `confirmed_at` (ISO 8601), and `student_id` linkage
   **And** the response reflects the final confirmed state
   **And** re-confirming (calling confirm again) upserts and replaces the prior confirmation.

5. **Given** a recommendation job has been confirmed
   **When** `GET .../recommendation-jobs/{rec_job_id}` is called
   **Then** the response includes `is_confirmed: true`
   **And** `GET .../recommendation-jobs/{rec_job_id}/confirm` returns the confirmed recommendation record.

6. **Given** a recommendation job that has NOT been confirmed
   **When** `GET .../recommendation-jobs/{rec_job_id}` is polled
   **Then** `is_confirmed: false` is returned.

7. **Given** an unauthenticated request or a non-teacher actor
   **When** any recommendation endpoint is called
   **Then** the response is `401` (unauthenticated) or `403` (non-teacher) respectively.

8. **Given** a request referencing an unknown or cross-tenant grading job
   **When** authorization is evaluated
   **Then** the request fails closed with `403` and no recommendation data is revealed.

## Tasks / Subtasks

- [x] Extend `app/domains/grading/repository.py` with recommendation records and state (AC: 1, 2, 4, 5, 6)
  - [x] Define `RecommendationJobRecord` dataclass (frozen=True): `rec_job_id`, `job_id`, `assignment_id`, `org_id`, `teacher_user_id`, `student_id`, `status` (str: pending|processing|completed|failed), `attempt_count` (int), `submitted_at`, `completed_at: str | None`
  - [x] Define `RecommendationResultRecord` dataclass (frozen=True): `rec_job_id`, `job_id`, `student_id`, `topics: list[dict[str, str]]` (each: `{"topic": str, "suggestion": str, "weakness_signal": str}`), `generated_at`
  - [x] Define `ConfirmedRecommendationRecord` dataclass (frozen=True): `rec_job_id`, `job_id`, `student_id`, `topics: list[dict[str, str]]`, `confirmed_by`, `confirmed_at`
  - [x] Add class-level state to `InMemoryGradingRepository`: `_recommendation_jobs: dict[str, RecommendationJobRecord]`, `_recommendation_results: dict[str, RecommendationResultRecord]`, `_confirmed_recommendations: dict[str, ConfirmedRecommendationRecord]`, `_job_rec_index: dict[str, str]` (job_id → rec_job_id), `_rec_job_seq: int`
  - [x] Reset all 5 new state fields in `reset_state()` → `_ensure_seed_data()`
  - [x] Implement `create_recommendation_job(job_id, assignment_id, org_id, teacher_user_id, student_id)` → `RecommendationJobRecord`
  - [x] Implement `get_recommendation_job_by_id(rec_job_id)` → `RecommendationJobRecord | None`
  - [x] Implement `get_recommendation_job_for_grading_job(job_id)` → `RecommendationJobRecord | None` (idempotency index lookup)
  - [x] Implement `update_recommendation_job(rec_job_id, status, attempt_count, completed_at)` → `RecommendationJobRecord`
  - [x] Implement `save_recommendation_result(rec_job_id, job_id, student_id, topics)` → `RecommendationResultRecord`
  - [x] Implement `get_recommendation_result(rec_job_id)` → `RecommendationResultRecord | None`
  - [x] Implement `upsert_confirmed_recommendation(rec_job_id, job_id, student_id, topics, confirmed_by, confirmed_at)` → `ConfirmedRecommendationRecord`
  - [x] Implement `get_confirmed_recommendation(rec_job_id)` → `ConfirmedRecommendationRecord | None`

- [x] Extend `app/domains/grading/service.py` with recommendation logic (AC: 1–8)
  - [x] Add `RecommendationJob` service dataclass (frozen=True): `rec_job_id`, `job_id`, `assignment_id`, `student_id`, `status`, `attempt_count`, `submitted_at`, `completed_at: str | None`
  - [x] Add `RecommendationResult` service dataclass (frozen=True): `rec_job_id`, `job_id`, `student_id`, `topics: list[dict[str, str]]`, `generated_at`
  - [x] Add `RecommendationJobWithResult` service dataclass (frozen=True): `rec_job_id`, `job_id`, `assignment_id`, `student_id`, `status`, `attempt_count`, `submitted_at`, `completed_at: str | None`, `result: RecommendationResult | None`, `is_confirmed: bool = False`
  - [x] Add `ConfirmedRecommendation` service dataclass (frozen=True): `rec_job_id`, `job_id`, `student_id`, `topics: list[dict[str, str]]`, `confirmed_by`, `confirmed_at`
  - [x] Add module-level constants: `STRONG_RATINGS = frozenset({"exceeds_expectations"})` and `_RECOMMENDATION_SUGGESTIONS: dict[str, str]` (deterministic stub suggestions keyed by rubric dimension name)
  - [x] Implement `submit_recommendation_job(actor_user_id, actor_org_id, assignment_id, job_id)` → `RecommendationJob`
    - Verify grading job existence + ownership (org_id, teacher_user_id, assignment_id) — fail-closed 403 via `GradingAccessError`
    - Check `repository.get_grade_approval(job_id) is not None` — raise `GradingStateError("Grading job must be approved before generating recommendations")` if not approved
    - Idempotency: `repository.get_recommendation_job_for_grading_job(job_id)` — if exists return `_to_recommendation_job(existing)`
    - Get artifact via `repository.get_artifact(job.artifact_id)` to extract `student_id`
    - Call `repository.create_recommendation_job(...)` and return `_to_recommendation_job(record)`
  - [x] Implement `process_recommendation_job(rec_job_id)` → `None` (background task target)
    - No-op if `rec_job.status in {"completed", "failed"}` (idempotency guard)
    - Update status → "processing"
    - Get grading result via `repository.get_grading_result(rec_job.job_id)` for rubric_mapping
    - Extract weakness topics: dimensions where `rating not in STRONG_RATINGS`
    - `repository.save_recommendation_result(rec_job_id, job_id, student_id, topics)`
    - Update status → "completed"
  - [x] Implement `get_recommendation_job_status(actor_user_id, actor_org_id, assignment_id, job_id, rec_job_id)` → `RecommendationJobWithResult`
    - Verify grading job ownership — fail-closed 403
    - Verify rec_job exists and `rec_job.job_id == job_id` — fail-closed 403 if not
    - Populate `result` from `repository.get_recommendation_result(rec_job_id)` if status=="completed"
    - Populate `is_confirmed = repository.get_confirmed_recommendation(rec_job_id) is not None`
  - [x] Implement `confirm_recommendations(actor_user_id, actor_org_id, assignment_id, job_id, rec_job_id, topics)` → `ConfirmedRecommendation`
    - Verify grading job ownership — fail-closed 403
    - Verify rec_job exists + `rec_job.job_id == job_id` — fail-closed 403
    - Verify `rec_job.status == "completed"` — raise `GradingStateError("Recommendation job must be completed before confirming")` if not
    - `repository.upsert_confirmed_recommendation(...)` with `confirmed_at = datetime.now(UTC).isoformat()`
    - Return `_to_confirmed_recommendation(record)`
  - [x] Add private helpers: `_to_recommendation_job()`, `_to_recommendation_result()`, `_to_recommendation_job_with_result()`, `_to_confirmed_recommendation()`

- [x] Add new schemas to `app/domains/grading/schemas.py` (AC: 1, 2, 4, 5)
  - [x] `RecommendationTopicItem`: `topic: str`, `suggestion: str`, `weakness_signal: str`
  - [x] `RecommendationTopicItemRequest`: `model_config = ConfigDict(extra="forbid")`, `topic: Annotated[str, StringConstraints(min_length=1, max_length=100)]`, `suggestion: Annotated[str, StringConstraints(min_length=1, max_length=1000)]`
  - [x] `RecommendationJobResponse`: `rec_job_id`, `job_id`, `assignment_id`, `student_id`, `status`, `attempt_count`, `submitted_at`, `completed_at: str | None`
  - [x] `RecommendationResultResponse`: `rec_job_id`, `topics: list[RecommendationTopicItem]`, `generated_at`
  - [x] `RecommendationJobWithResultResponse`: `rec_job_id`, `job_id`, `assignment_id`, `student_id`, `status`, `attempt_count`, `submitted_at`, `completed_at: str | None`, `result: RecommendationResultResponse | None`, `is_confirmed: bool`
  - [x] `ConfirmRecommendationRequest`: `model_config = ConfigDict(extra="forbid")`, `topics: list[RecommendationTopicItemRequest]`
  - [x] `ConfirmedRecommendationResponse`: `rec_job_id`, `job_id`, `student_id`, `topics: list[RecommendationTopicItem]`, `confirmed_by`, `confirmed_at`

- [x] Add new router endpoints to `app/domains/grading/router.py` (AC: 1–8)
  - [x] Import new service dataclasses and schemas
  - [x] Add `_to_recommendation_job_response(job: RecommendationJob) -> RecommendationJobResponse` helper
  - [x] Add `_to_recommendation_job_with_result_response(job_with_result: RecommendationJobWithResult) -> RecommendationJobWithResultResponse` helper
  - [x] Add `_to_confirmed_recommendation_response(confirmed: ConfirmedRecommendation) -> ConfirmedRecommendationResponse` helper
  - [x] Add `_process_recommendation_job_task(rec_job_id, service)` background task helper (same swallow-exception pattern as `_process_grading_job_task`)
  - [x] `POST /grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs` → `202 RecommendationJobResponse`
    - Auth: `require_authenticated_actor`, `_require_teacher`
    - `GradingAccessError` → 403; `GradingStateError` → 409
    - Guard: only enqueue background task when `job.status == "pending" and job.attempt_count == 0` (idempotency)
  - [x] `GET /grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}` → `200 RecommendationJobWithResultResponse`
    - Auth: `require_authenticated_actor`, `_require_teacher`
    - `GradingAccessError` → 403
  - [x] `POST /grading/assignments/{assignment_id}/grading-jobs/{job_id}/recommendation-jobs/{rec_job_id}/confirm` → `200 ConfirmedRecommendationResponse`
    - Auth: `require_authenticated_actor`, `_require_teacher`
    - Body: `ConfirmRecommendationRequest`
    - `GradingAccessError` → 403; `GradingStateError` → 409

- [x] Add tests (AC: 1–8)
  - [x] **Service tests** (`tests/test_grading_service.py`) — add `# --- Recommendation jobs ---` section:
    - `test_submit_recommendation_job_success`: rec_job created, status="pending", student_id populated from artifact
    - `test_submit_recommendation_job_requires_approved_job`: un-approved job raises `GradingStateError`
    - `test_submit_recommendation_job_idempotent`: second call returns same rec_job_id
    - `test_submit_recommendation_job_cross_tenant_forbidden`: raises `GradingAccessError`
    - `test_submit_recommendation_job_unknown_job_forbidden`: unknown job_id raises `GradingAccessError`
    - `test_process_recommendation_job_generates_topics`: topics non-empty after processing; each has topic/suggestion/weakness_signal
    - `test_process_recommendation_job_idempotent_when_completed`: second call is no-op (attempt_count unchanged)
    - `test_get_recommendation_job_status_pending`: status="pending", result=None before processing
    - `test_get_recommendation_job_status_completed`: status="completed", result non-None after processing
    - `test_get_recommendation_job_is_confirmed_false_before_confirm`: `is_confirmed == False`
    - `test_confirm_recommendations_success`: confirmed_by set, confirmed_at non-empty; `is_confirmed == True` on subsequent GET
    - `test_confirm_recommendations_requires_completed_status`: raises `GradingStateError` if rec_job not completed
    - `test_confirm_recommendations_upserts_on_reconfirm`: second confirm with different topics upserts correctly
    - `test_confirm_recommendations_cross_tenant_forbidden`: raises `GradingAccessError`
  - [x] **API tests** (`tests/test_grading_api.py`) — add `# --- Recommendation endpoints ---` section:
    - `test_submit_recommendation_job_success`: POST 202, body has rec_job_id/job_id/student_id/status="pending"
    - `test_submit_recommendation_job_unauthenticated`: 401
    - `test_submit_recommendation_job_non_teacher_forbidden`: 403
    - `test_submit_recommendation_job_not_approved_conflict`: 409 when job not approved
    - `test_submit_recommendation_job_idempotent`: same rec_job_id on second POST
    - `test_get_recommendation_job_completed`: status="completed", result.topics non-empty
    - `test_get_recommendation_job_is_confirmed_field`: `is_confirmed: false` before confirm, `is_confirmed: true` after
    - `test_confirm_recommendations_success`: 200, confirmed_by=="usr_teacher_1", topics list present
    - `test_confirm_recommendations_not_completed_conflict`: 409 when rec_job not yet processed

- [x] Update docs and metadata
  - [x] Update `apps/api/README.md` with 3 new endpoints
  - [x] Update `apps/api/pyproject.toml` `[tool.ilm]` story to `"2.6"` with recommendation notes

## Dev Notes

### Core Design: Recommendation Pipeline as Second-Stage Async Job

Story 2.6 is the second async job type in the grading domain, following the identical pattern established in story 2.4. The design is intentionally parallel:

| Concern | Grading Job (2.4) | Recommendation Job (2.6) |
|---|---|---|
| Submit endpoint | `POST .../grading-jobs` | `POST .../recommendation-jobs` |
| Idempotency index | `_artifact_job_index` (artifact_id → job_id) | `_job_rec_index` (job_id → rec_job_id) |
| Background task | `_process_grading_job_task` | `_process_recommendation_job_task` |
| Status lifecycle | pending→processing→completed→failed | pending→processing→completed→failed |
| Poll endpoint | `GET .../grading-jobs/{job_id}` | `GET .../recommendation-jobs/{rec_job_id}` |
| Post-process action | Teacher approves (story 2.5) | Teacher confirms |

**Key difference:** Recommendation jobs have a mandatory prerequisite — the parent grading job must be approved (`GradeApprovalRecord` exists). This enforces the immutable ledger gate: no recommendations without teacher-approved grades.

### Approval Gate Integration

The prerequisite check in `submit_recommendation_job`:

```python
if self._repository.get_grade_approval(job_id) is None:
    raise GradingStateError("Grading job must be approved before generating recommendations")
```

This reuses the `GradingStateError` class added in story 2.5 (already imported in router). No new exception class needed.

### Weakness Signal Extraction

The stub AI recommendation logic in `process_recommendation_job` extracts topics from `GradingResultRecord.rubric_mapping`:

```python
# Module-level in service.py
STRONG_RATINGS = frozenset({"exceeds_expectations"})
_RECOMMENDATION_SUGGESTIONS: dict[str, str] = {
    "content_accuracy": (
        "Review foundational concepts in the relevant chapter and complete the "
        "practice exercises before the next assessment."
    ),
    "completeness": (
        "Ensure all rubric sections are fully addressed. Re-read the assignment "
        "prompt and check each criterion before submitting."
    ),
    "presentation": (
        "Practice structuring responses with a clear opening, supporting details, "
        "and a summary conclusion."
    ),
}

def _extract_weakness_topics(rubric_mapping: dict[str, str]) -> list[dict[str, str]]:
    """Return practice topics for any dimension that did not exceed expectations."""
    topics = []
    for dimension, rating in rubric_mapping.items():
        if rating not in STRONG_RATINGS:
            topics.append({
                "topic": dimension.replace("_", " ").title(),
                "suggestion": _RECOMMENDATION_SUGGESTIONS.get(
                    dimension,
                    f"Additional practice on {dimension.replace('_', ' ')} is recommended.",
                ),
                "weakness_signal": rating,
            })
    return topics
```

With the seed grading rubric (`content_accuracy: meets_expectations, presentation: exceeds_expectations, completeness: meets_expectations`), this produces **2 topics** (content_accuracy + completeness) for reliable test assertions.

### `student_id` Sourcing

The `student_id` must be extracted from the artifact at recommendation job submission time, **not** from the grading job record (which doesn't store `student_id`). Flow:

```python
# In submit_recommendation_job:
job = self._repository.get_grading_job_by_id(job_id)
# ... ownership checks ...
artifact = self._repository.get_artifact(job.artifact_id)
# artifact.student_id is the student linkage for downstream Epic 3
record = self._repository.create_recommendation_job(
    ...,
    student_id=artifact.student_id,
)
```

`get_artifact()` always succeeds here because the grading job was created from a valid artifact — no need for an extra access check on the artifact.

### `is_confirmed` Visibility Gate (Forward Compatibility for Epic 3)

The `is_confirmed` field on `RecommendationJobWithResult` mirrors the `is_approved` pattern from story 2.5:
- `is_confirmed = repository.get_confirmed_recommendation(rec_job_id) is not None`
- Epic 3 parent/student progress endpoints will check `is_confirmed` before surfacing recommendations — unconfirmed recommendations remain hidden from students/parents
- This story does NOT implement Epic 3 endpoints, only the gate mechanism

### Confirm as Upsert

`confirm_recommendations` upserts using `upsert_confirmed_recommendation`:
- First call: creates `ConfirmedRecommendationRecord`
- Subsequent call with different topics: replaces the record (same frozen dataclass replace-not-mutate pattern as `upsert_grade_approval`)
- No version history for confirmations (simpler than approval — teacher can change their mind freely)

### `RecommendationJobRecord` → `student_id` vs Lookup

`student_id` is denormalized onto `RecommendationJobRecord` and `RecommendationResultRecord` and `ConfirmedRecommendationRecord`. This is intentional for Epic 3 — when a parent/student queries for recommendations, the lookup key is `student_id`, not `job_id`. Storing it denormalized avoids a join through the grading job → artifact chain in downstream reads.

### Data Model

```python
@dataclass(frozen=True)
class RecommendationJobRecord:
    rec_job_id: str
    job_id: str
    assignment_id: str
    org_id: str
    teacher_user_id: str
    student_id: str        # denormalized from artifact at submit time
    status: str            # pending | processing | completed | failed
    attempt_count: int
    submitted_at: str
    completed_at: str | None

@dataclass(frozen=True)
class RecommendationResultRecord:
    rec_job_id: str
    job_id: str
    student_id: str
    topics: list[dict[str, str]]  # [{"topic": str, "suggestion": str, "weakness_signal": str}]
    generated_at: str

@dataclass(frozen=True)
class ConfirmedRecommendationRecord:
    rec_job_id: str
    job_id: str
    student_id: str
    topics: list[dict[str, str]]  # possibly edited by teacher at confirm time
    confirmed_by: str
    confirmed_at: str
```

Class-level state additions:
```python
_recommendation_jobs: dict[str, RecommendationJobRecord] = {}       # rec_job_id → record
_recommendation_results: dict[str, RecommendationResultRecord] = {} # rec_job_id → result
_confirmed_recommendations: dict[str, ConfirmedRecommendationRecord] = {} # rec_job_id → confirmed
_job_rec_index: dict[str, str] = {}  # job_id → rec_job_id (idempotency)
_rec_job_seq: int = 0
```

Reset all 5 fields in `_ensure_seed_data()`.

### Background Task Idempotency Guard (Inherited from 2.4 H2 Fix)

The router must apply the same guard as `submit_grading_job`:

```python
if rec_job.status == "pending" and rec_job.attempt_count == 0:
    background_tasks.add_task(_process_recommendation_job_task, ...)
```

On idempotent re-submit (existing completed rec job returned), `status == "completed"` so the guard prevents re-enqueue.

### `update_recommendation_job` — Use `.get()` Pattern (Inherited from 2.4 M3 Fix)

```python
def update_recommendation_job(self, rec_job_id: str, ...) -> RecommendationJobRecord:
    existing = self.__class__._recommendation_jobs.get(rec_job_id)
    if existing is None:
        raise KeyError(f"Recommendation job not found: {rec_job_id}")
    # ... replace-not-mutate
```

### Test Helper Pattern

Add `_submit_and_approve_job` helper to service tests (builds on `_submit_and_process`):

```python
def _submit_approve_and_get_job_id(service, assignment_id, artifact_id):
    job_id = _submit_and_process(service, assignment_id, artifact_id)
    service.approve_grading_job(
        actor_user_id="usr_teacher_1",
        actor_org_id="org_demo_1",
        assignment_id=assignment_id,
        job_id=job_id,
        approved_score="85/100",
        approved_feedback="Good.",
    )
    return job_id
```

For API tests, add `_submit_approve_and_get_job_id_api` async helper:

```python
async def _submit_approve_and_get_job_id(client, assignment_id, artifact_id):
    job_id = await _submit_and_process_job(client, assignment_id, artifact_id)
    await client.post(
        f"/grading/assignments/{assignment_id}/grading-jobs/{job_id}/approve",
        headers=_teacher_headers(),
        json={"approved_score": "85/100", "approved_feedback": "Good."},
    )
    return job_id
```

For the `test_submit_recommendation_job_not_approved_conflict` API test: since BackgroundTasks run synchronously in ASGITransport tests (making job immediately "completed"), the test cannot use a normally submitted job that lacks approval. Use `_grading_service._repository.create_grading_job(...)` to inject a completed job without approval (same pattern as `test_approve_grading_job_not_completed_conflict` in 2.5, but inverted — here we need a completed-but-unapproved job):

```python
# In test_submit_recommendation_job_not_approved_conflict:
# Create completed job via repo, skip background processing (use update_grading_job to set status=completed)
# Then attempt POST recommendation-jobs → expect 409
```

### Architecture Compliance

- Only `app/domains/grading/` is modified — no other domain imports
- All new service dataclasses go in `service.py` after `ConfirmedRecommendation`
- All new repository records go in `repository.py` after `ConfirmedRecommendationRecord`
- No new files created — strictly additive to existing files
- All 3 new endpoints require `require_authenticated_actor` + `_require_teacher`
- `GradingStateError` and `GradingAccessError` are reused (no new exception classes)
- `frozen=True` on all new dataclasses; `list[dict]` field allowed in frozen dataclass (Python permits mutable fields in frozen dataclasses — they follow the replace-not-mutate convention by design)

### Technical Requirements

- `ConfirmRecommendationRequest.topics` list can be empty (teacher may confirm with 0 topics — i.e., "no recommendations needed")
- `topics` item validation: `min_length=1` on both `topic` and `suggestion` strings; max_length: topic=100, suggestion=1000
- `weakness_signal` is NOT in the confirm request — it's system-generated metadata; teacher edits only `topic` and `suggestion` in the confirm payload
- `confirmed_at` uses `datetime.now(UTC).isoformat()` — same pattern as `approved_at` in 2.5
- `rec_job_id` naming: `f"rec_{self.__class__._rec_job_seq}"` (e.g., `rec_1`, `rec_2`)

### Library / Framework Requirements

- No new dependencies — FastAPI + Pydantic v2 + `datetime.now(UTC)` (same as all prior stories)
- `status.HTTP_202_ACCEPTED` already imported in `router.py`
- `status.HTTP_409_CONFLICT` already imported in `router.py` (from 2.5)

### File Structure Requirements

**Modified files only** (no new files):
- `apps/api/app/domains/grading/repository.py` — 3 new records, 5 new state fields, 8 new repository methods
- `apps/api/app/domains/grading/service.py` — 4 new dataclasses, 2 new constants, 4 new service methods, 4 private helpers
- `apps/api/app/domains/grading/schemas.py` — 7 new Pydantic models
- `apps/api/app/domains/grading/router.py` — 3 new response helpers, 1 background task helper, 3 new endpoints
- `apps/api/tests/test_grading_service.py` — 14 new service tests in `# --- Recommendation jobs ---` section
- `apps/api/tests/test_grading_api.py` — 9 new API tests in `# --- Recommendation endpoints ---` section
- `apps/api/README.md` — 3 new endpoints in Story Scope
- `apps/api/pyproject.toml` — update `[tool.ilm]` to story 2.6

**Do NOT modify:**
- `apps/api/app/main.py` — grading router already registered
- `apps/api/app/domains/auth/` — no auth changes
- Any other domain

### Testing Requirements

- **Auth regression** on ALL 3 new endpoints: unauthenticated → 401, non-teacher → 403
- **Approval gate test**: POST recommendation-jobs on unapproved job → 409 (use direct repo injection to create completed-but-unapproved job)
- **Idempotency test**: two POSTs for same grading job → same rec_job_id (both service and API level)
- **Topic content test**: after processing, assert `len(result.topics) >= 1` and each topic has non-empty `topic`, `suggestion`, `weakness_signal`
- **Confirm cycle**: approve → submit rec → poll until completed → confirm → GET shows `is_confirmed: true`
- **Reconfirm upsert**: second confirm with different topics replaces prior confirmation
- **Cross-tenant**: all service methods must have cross-tenant test
- **Re-use `setup_function`** which already calls `InMemoryGradingRepository.reset_state()` and `GradingService._fail_on_job_ids.clear()`

### Previous Story Intelligence

- **2.5 approval gate** is the prerequisite — `get_grade_approval(job_id) is not None` is the check. Reuse `GradingStateError` for the 409 path (same exception class, different message).
- **2.5 `is_approved` pattern** is the template for `is_confirmed` — same boolean default False, same populate-from-repo-lookup pattern in the "with result" method.
- **2.4 background task idempotency guard** (`if job.status == "pending" and job.attempt_count == 0`) must be applied to the new recommendation job submit endpoint.
- **2.4 M3 fix** — `update_recommendation_job` must use `.get()` with explicit `KeyError`, not `dict[key]`.
- **2.4 H2 pattern** — `_process_recommendation_job_task` swallows all exceptions via `except Exception: logger.exception(...)` (same as `_process_grading_job_task`).
- **Test file `_create_demo_artifact` helper** is already defined at line 441 of `test_grading_service.py` — do NOT define it again (H1 code review fix from 2.5 review).
- **ASGITransport background tasks run synchronously** — after `POST .../recommendation-jobs`, the rec job is already "completed" in tests; approve first, then submit recommendation, then immediately confirm in the same `asyncio.run()` block.

### Git Intelligence

Recent commits show the grading domain has been extended in-place across stories 2.3→2.4→2.5. The pattern is strictly additive: new frozen dataclasses → new repository methods → new service methods → new schemas → new router endpoints. No architectural drift detected.

### References

- [Source: _bmad-output/implementation-artifacts/epics.md#Story 2.6: Generate Weakness-Based Practice Recommendations]
- [Source: _bmad-output/planning-artifacts/prd.md#FR18, FR21, FR23, FR26, FR42, NFR4, NFR5, NFR15]
- [Source: _bmad-output/implementation-artifacts/architecture.md#Grade publication rule, Async job architecture, Implementation Patterns]
- [Source: _bmad-output/implementation-artifacts/2-5-teacher-review-override-and-approval-gate.md#Dev Notes, Dev Agent Record]
- [Source: apps/api/app/domains/grading/repository.py] — frozen dataclass + class-level state + replace-not-mutate patterns
- [Source: apps/api/app/domains/grading/service.py] — GradingStateError, GradingAccessError, ownership check ordering
- [Source: apps/api/app/domains/grading/router.py] — _require_teacher, background task guard, 409/403 patterns
- [Source: apps/api/tests/test_grading_api.py] — asyncio.run/httpx.AsyncClient test helper pattern, _submit_and_process_job helper

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No debug issues encountered. One test assertion fix: `test_submit_recommendation_job_success` initially asserted `status == "completed"` after POST 202, but the response body reflects pre-background-task state (same as grading jobs) — corrected to `status == "pending"`.

### Completion Notes List

- Implemented full recommendation pipeline as second-stage async job pattern, parallel to 2.4 grading job design
- `RecommendationJobRecord`, `RecommendationResultRecord`, `ConfirmedRecommendationRecord` added as frozen dataclasses in repository.py; all 5 new state fields reset in `_ensure_seed_data()`
- 8 new repository methods added following `.get()` + KeyError pattern (2.4 M3 fix) for `update_recommendation_job`
- Approval gate enforced in `submit_recommendation_job`: `get_grade_approval(job_id) is None` → `GradingStateError` (409)
- Idempotency index `_job_rec_index` (job_id → rec_job_id) returns existing rec job on duplicate submit
- `student_id` sourced from artifact at submit time (artifact.student_id) — denormalized to all 3 new record types
- `_extract_weakness_topics` module-level function produces 2 topics from seed rubric (content_accuracy + completeness, both `meets_expectations`)
- `is_confirmed` flag mirrors 2.5 `is_approved` pattern as Epic 3 visibility gate
- `confirm_recommendations` upserts via `upsert_confirmed_recommendation` (no version history — teacher can freely change)
- Background task idempotency guard: `if rec_job.status == "pending" and rec_job.attempt_count == 0`
- 7 new Pydantic schemas; `ConfirmRecommendationRequest.topics` uses `RecommendationTopicItemRequest` (no `weakness_signal` — system-generated only)
- `_to_confirmed_recommendation_response` uses `t.get("weakness_signal", "")` to handle confirm payloads lacking that field
- 14 service tests + 9 API tests; all 189 tests passing (166 existing + 23 new)

### File List

- apps/api/app/domains/grading/repository.py
- apps/api/app/domains/grading/service.py
- apps/api/app/domains/grading/schemas.py
- apps/api/app/domains/grading/router.py
- apps/api/tests/test_grading_service.py
- apps/api/tests/test_grading_api.py
- apps/api/README.md
- apps/api/pyproject.toml
- .gitignore
- _bmad-output/implementation-artifacts/2-4-submit-and-process-async-ai-grading-jobs.md

### Change Log

- 2026-03-18: Story 2.6 implemented — weakness-based practice recommendation pipeline. Added 3 new frozen dataclasses (RecommendationJobRecord, RecommendationResultRecord, ConfirmedRecommendationRecord), 8 repository methods, 4 service methods + 4 helpers + module-level constants (STRONG_RATINGS, _RECOMMENDATION_SUGGESTIONS, _extract_weakness_topics), 7 Pydantic schemas, 3 router endpoints (POST submit 202, GET poll, POST confirm 200), 23 new tests. 189 total passing.
- 2026-03-18: Code review fixes applied — added missing `GET .../recommendation-jobs/{rec_job_id}/confirm` endpoint and service path, hardened recommendation submit to fail closed if grading job artifact linkage is missing, normalized confirmed recommendation topics to always retain `weakness_signal`, expanded service/API tests for confirmed recommendation retrieval and weakness-signal preservation, and updated API README endpoint list.

### Senior Developer Review (AI)

- Outcome: Changes Requested → Fixed automatically.
- High issue fixed: Missing AC endpoint `GET .../recommendation-jobs/{rec_job_id}/confirm` is now implemented and tested.
- High issue fixed: Recommendation submission now fails closed (`403`) when grading job artifact linkage is missing instead of creating a record with empty `student_id`.
- Medium issue fixed: Confirmed recommendation topics now persist a `weakness_signal` value so response payloads are not lossy.
- Medium issue noted: Repository has additional unrelated modified files and staged `__pycache__` artifacts that were not introduced by this story implementation.

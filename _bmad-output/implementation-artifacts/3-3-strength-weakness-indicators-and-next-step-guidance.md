# Story 3.3: Strength/Weakness Indicators and Next-Step Guidance

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a guardian or student,
I want clear strengths and weakness indicators with next steps,
so that I can focus effort effectively.

## Acceptance Criteria

1. **Topic insights endpoint:** `GET /progress/students/{student_id}/topic-insights` is accessible to authenticated parents and students with the same access control as the existing progress endpoints (`_require_parent_or_student`). Teachers and unauthenticated requests are rejected.

2. **Weakness indicators with guidance:** Each response entry includes `topic`, `status` (set to `"weakness"` for topics derived from confirmed recommendations), `weakness_signal`, and `guidance` (the recommendation suggestion text). The response is scoped to the student's org.

3. **De-duplication by topic:** If the same topic appears across multiple confirmed recommendations, only the entry from the most recent recommendation (by `confirmed_at` descending) is included in the response. Stale duplicates are omitted.

4. **Sufficient-data gate:** The response includes `has_sufficient_data: true` when at least one approved grade exists for the student in their org; `false` otherwise. When `false`, the `topic_insights` list must be empty — the system avoids presenting indicators without a performance basis.

5. **Access control unchanged:** All existing auth/authz rules from Stories 3.1–3.2 (`_require_parent_or_student`, org isolation, role exclusion, 401/403/404 responses) remain fully intact. No changes to existing endpoints.

6. **Performance target compliance:** The topic-insights endpoint must respond within NFR-001 threshold (p95 ≤ 700 ms for student read endpoints). In-memory aggregation ensures this; no async work or external calls.

## Tasks / Subtasks

- [x] Task 1: Add `TopicInsightRecord` dataclass and `list_topic_insights_for_student` to repository (AC: 2, 3, 4)
  - [x] In `apps/api/app/domains/grading/repository.py`, add `TopicInsightRecord(frozen=True)` dataclass after `ConfirmedRecommendationRecord` with fields: `topic: str`, `status: str` (value `"weakness"`), `weakness_signal: str`, `guidance: str`, `rec_job_id: str`, `confirmed_at: str`
  - [x] Add `list_topic_insights_for_student(self, student_id: str, org_id: str) -> tuple[list[TopicInsightRecord], bool]` method to `InMemoryGradingRepository`:
    - Step 1: Check if at least one approved grade exists for student+org → set `has_sufficient_data`
    - Step 2: If `has_sufficient_data` is False, return `([], False)` immediately
    - Step 3: Collect all confirmed recommendations for student+org using existing `list_confirmed_recommendations_for_student` pattern (filter by student_id + rec_job org isolation)
    - Step 4: Flatten recommendation topics, keeping only the latest `confirmed_at` entry per topic (de-duplicate by topic name, sort by confirmed_at descending, keep first per topic)
    - Step 5: Return `([TopicInsightRecord(...)], True)` for each de-duplicated topic entry

- [x] Task 2: Add `TopicInsightResponse` and `TopicInsightListResponse` schemas (AC: 2, 4)
  - [x] In `apps/api/app/domains/progress/schemas.py`, add `TopicInsightResponse(BaseModel)` with fields: `topic: str`, `status: str`, `weakness_signal: str`, `guidance: str`, `rec_job_id: str`, `confirmed_at: str`
  - [x] Add `TopicInsightListResponse(BaseModel)` with fields: `topic_insights: list[TopicInsightResponse]`, `has_sufficient_data: bool`

- [x] Task 3: Add `GET /progress/students/{student_id}/topic-insights` endpoint (AC: 1, 2, 3, 4, 5)
  - [x] In `apps/api/app/domains/progress/router.py`, add import for `TopicInsightResponse`, `TopicInsightListResponse`
  - [x] Add endpoint `get_student_topic_insights(student_id, actor)` following the same pattern as `get_student_grades`:
    - Call `_require_parent_or_student(actor, student_id, _students_repo, _grading_repo)` first
    - Call `_grading_repo.list_topic_insights_for_student(student_id, actor.org_id)`
    - Map `TopicInsightRecord` → `TopicInsightResponse`
    - Return `TopicInsightListResponse(topic_insights=..., has_sufficient_data=...)`

- [x] Task 4: Write tests in `apps/api/tests/test_progress_api.py` (AC: 1, 2, 3, 4, 5, 6)
  - [x] Test 24: Endpoint returns weakness topic with guidance when confirmed recommendation exists and approved grade exists (`has_sufficient_data: true`, topic entry present)
  - [x] Test 25: `has_sufficient_data: false` and empty `topic_insights` when repo is empty (no grades, no recommendations) — call only `reset_progress_state_for_tests()` + `reset_auth_state_for_tests()` + `_create_guardian_link()`, no data setup; the gate fires on missing grades
  - [x] Test 26: De-duplication — two recommendations with the same topic; only the more recent `confirmed_at` entry is returned
  - [x] Test 27: Access control — teacher JWT → 403; unauthenticated → 401; wrong student (student role, wrong user_id) → 403
  - [x] Test 28: Org isolation — parent in org_demo_1 cannot access student in org_other_1 → 404
  - [x] Test 29: Empty `topic_insights` list (not null) when no confirmed recommendations exist but approved grades do exist (`has_sufficient_data: true`, `topic_insights: []`)
  - [x] Verify existing 240 tests still pass (no regressions) — 246/246 passed (240 prior + 6 new)

## Dev Notes

### Context from Previous Stories

Story 3.1 built `_require_parent_or_student`, org isolation, and the two `/progress/` endpoints. Story 3.2 enriched grade responses with `assignment_title` and chronological ordering. Story 2.6 built the confirmed recommendations pipeline. **Do not re-implement or modify any of those — they are complete and green.**

### Data Sources and Derivation Logic

The existing `ConfirmedRecommendationRecord` already carries everything needed for weakness indicators:

```python
@dataclass(frozen=True)
class ConfirmedRecommendationRecord:
    rec_job_id: str
    job_id: str
    student_id: str
    topics: list[dict[str, str]]  # [{"topic": str, "suggestion": str, "weakness_signal": str}]
    confirmed_by: str
    confirmed_at: str
```

Each `topics` entry is a weakness — `weakness_signal` is the symptom label, `suggestion` is the guidance text. This is the only data source needed; no new domain fields are required.

**There is no "strength" concept yet in the data model** — the confirmed recommendations are exclusively weakness-driven. `status: "weakness"` is the only status value in this story. Clients interpreting "no indicators for a topic" as a strength signal is acceptable at the UI layer; the API is correct to omit absent topics.

### New `TopicInsightRecord` Dataclass

```python
@dataclass(frozen=True)
class TopicInsightRecord:
    topic: str
    status: str              # always "weakness" in MVP
    weakness_signal: str
    guidance: str            # from topics[].suggestion
    rec_job_id: str          # for client deep-linking
    confirmed_at: str        # ISO 8601; used for de-duplication ordering
```

Add this **after** `ConfirmedRecommendationRecord` at approximately line 120.

### `list_topic_insights_for_student` Implementation Pattern

```python
def list_topic_insights_for_student(
    self, student_id: str, org_id: str
) -> tuple[list[TopicInsightRecord], bool]:
    # Sufficient-data gate: any approved grade for this student+org?
    has_grade = any(
        self.__class__._artifact_job_index.get(a.artifact_id) is not None
        and self.__class__._grade_approvals.get(
            self.__class__._artifact_job_index[a.artifact_id]
        ) is not None
        for a in self.__class__._artifacts.values()
        if a.student_id == student_id and a.org_id == org_id
    )
    if not has_grade:
        return [], False

    # Reuse existing org-isolation logic — do NOT duplicate it inline
    recs = self.list_confirmed_recommendations_for_student(student_id, org_id)

    # Flatten topics; keep latest confirmed_at per topic (de-duplicate)
    # Use datetime.fromisoformat() to avoid mixed-offset string misordering (per Story 3.2 lesson)
    # Secondary key rec_job_id ensures stable sort when timestamps are equal
    recs_sorted = sorted(recs, key=lambda r: (datetime.fromisoformat(r.confirmed_at), r.rec_job_id), reverse=True)
    seen_topics: set[str] = set()
    insights: list[TopicInsightRecord] = []
    for rec in recs_sorted:
        for entry in rec.topics:
            topic = entry.get("topic", "")
            if topic in seen_topics:
                continue
            seen_topics.add(topic)
            insights.append(TopicInsightRecord(
                topic=topic,
                status="weakness",
                weakness_signal=entry.get("weakness_signal", ""),
                guidance=entry.get("suggestion", ""),
                rec_job_id=rec.rec_job_id,
                confirmed_at=rec.confirmed_at,
            ))
    return insights, True
```

### Router Endpoint Pattern

Follows the exact structure of `get_student_grades`:

```python
@router.get(
    "/students/{student_id}/topic-insights",
    response_model=TopicInsightListResponse,
)
async def get_student_topic_insights(
    student_id: str,
    actor: ActorContext = Depends(require_authenticated_actor),
) -> TopicInsightListResponse:
    _require_parent_or_student(actor, student_id, _students_repo, _grading_repo)
    insights, has_sufficient_data = _grading_repo.list_topic_insights_for_student(
        student_id, actor.org_id
    )
    return TopicInsightListResponse(
        topic_insights=[
            TopicInsightResponse(
                topic=i.topic,
                status=i.status,
                weakness_signal=i.weakness_signal,
                guidance=i.guidance,
                rec_job_id=i.rec_job_id,
                confirmed_at=i.confirmed_at,
            )
            for i in insights
        ],
        has_sufficient_data=has_sufficient_data,
    )
```

### Test Patterns

**Test helper setup for topic-insights tests:**
- Use existing `_create_confirmed_recommendation_pipeline()` to set up the full data chain (it calls `_create_approved_grade_pipeline` internally → creates grade AND recommendation)
- Use existing `_create_guardian_link()` to set up parent access — it uses `asyncio.run()` internally, call it synchronously with no `await`
- Each test must call `reset_progress_state_for_tests()` and `reset_auth_state_for_tests()` for isolation

**Test 24 — happy path:**
```python
def test_topic_insights_returns_weakness_with_guidance() -> None:
    reset_progress_state_for_tests()
    reset_auth_state_for_tests()
    _create_confirmed_recommendation_pipeline()
    _create_guardian_link()
    with httpx.Client(app=app, base_url="http://test") as client:
        r = client.get(
            "/progress/students/usr_student_1/topic-insights",
            headers=_parent_headers(),
        )
    assert r.status_code == 200
    body = r.json()
    assert body["has_sufficient_data"] is True
    assert len(body["topic_insights"]) == 1
    insight = body["topic_insights"][0]
    assert insight["topic"] == "Algebra"
    assert insight["status"] == "weakness"
    assert insight["weakness_signal"] == "low score"
    assert insight["guidance"] == "Practice more"
    assert "rec_job_id" in insight
    assert "confirmed_at" in insight

    # Also verify student role can access own topic-insights
    with httpx.Client(app=app, base_url="http://test") as client:
        r = client.get(
            "/progress/students/usr_student_1/topic-insights",
            headers=_student_headers(),
        )
    assert r.status_code == 200
    assert r.json()["has_sufficient_data"] is True
```

**Test 25 — insufficient data (empty repo):**
```python
def test_topic_insights_insufficient_data_when_no_grades() -> None:
    reset_progress_state_for_tests()
    reset_auth_state_for_tests()
    _create_guardian_link()  # auth only — no grades, no recs

    with httpx.Client(app=app, base_url="http://test") as client:
        r = client.get(
            "/progress/students/usr_student_1/topic-insights",
            headers=_parent_headers(),
        )
    assert r.status_code == 200
    body = r.json()
    assert body["has_sufficient_data"] is False
    assert body["topic_insights"] == []
```
Note: Do NOT use `_create_confirmed_recommendation_pipeline` here — it internally calls `_create_approved_grade_pipeline`, which creates a grade and defeats the test.

**Test 26 — de-duplication:**
```python
def test_topic_insights_deduplication_keeps_latest_rec() -> None:
    reset_progress_state_for_tests()
    reset_auth_state_for_tests()
    repo = InMemoryGradingRepository()

    # Two distinct approved grade pipelines → two distinct job_ids
    job_id_1, _, assignment_id_1 = _create_approved_grade_pipeline()
    job_id_2, _, assignment_id_2 = _create_approved_grade_pipeline()

    # Rec 1: older confirmed_at — same topic "Algebra"
    rec_job_1 = repo.create_recommendation_job(
        job_id=job_id_1, assignment_id=assignment_id_1,
        org_id="org_demo_1", teacher_user_id="usr_teacher_1", student_id="usr_student_1",
    )
    repo.upsert_confirmed_recommendation(
        rec_job_id=rec_job_1.rec_job_id, job_id=job_id_1, student_id="usr_student_1",
        topics=[{"topic": "Algebra", "suggestion": "Old guidance", "weakness_signal": "old signal"}],
        confirmed_by="usr_teacher_1", confirmed_at="2024-01-01T00:00:00+00:00",
    )

    # Rec 2: newer confirmed_at — same topic "Algebra"
    rec_job_2 = repo.create_recommendation_job(
        job_id=job_id_2, assignment_id=assignment_id_2,
        org_id="org_demo_1", teacher_user_id="usr_teacher_1", student_id="usr_student_1",
    )
    repo.upsert_confirmed_recommendation(
        rec_job_id=rec_job_2.rec_job_id, job_id=job_id_2, student_id="usr_student_1",
        topics=[{"topic": "Algebra", "suggestion": "New guidance", "weakness_signal": "new signal"}],
        confirmed_by="usr_teacher_1", confirmed_at="2024-02-01T00:00:00+00:00",
    )

    _create_guardian_link()
    with httpx.Client(app=app, base_url="http://test") as client:
        r = client.get(
            "/progress/students/usr_student_1/topic-insights",
            headers=_parent_headers(),
        )
    assert r.status_code == 200
    body = r.json()
    assert len(body["topic_insights"]) == 1                              # deduplicated
    assert body["topic_insights"][0]["guidance"] == "New guidance"       # newer rec wins
    assert body["topic_insights"][0]["confirmed_at"] == "2024-02-01T00:00:00+00:00"
```

**Test 27 — access control:**
```python
# teacher → 403
# unauthenticated → 401
# wrong student (usr_teacher_1 with student role) → 403
```

**Test 28 — org isolation:**
```python
# parent in org_demo_1 requests student in org_other_1 → 404
```

**Test 29 — empty but sufficient:**
```python
# Create approved grade pipeline only (no recommendation)
# Verify has_sufficient_data: true, topic_insights: []
```

### Domain Boundary Rule

The `progress` router **must not import from** `app.domains.grading.service`, `app.domains.grading.router`, or `app.domains.students.router`. Only allowed imports:
- `InMemoryGradingRepository` from `app.domains.grading.repository`
- `InMemoryStudentsRepository` from `app.domains.students.repository`
- `ActorContext`, `require_authenticated_actor` from `app.domains.auth.dependencies`

[Source: apps/api/README.md#Domain-Boundary-Rule]

### Project Structure Notes

**Files to modify (no new files):**
- `apps/api/app/domains/grading/repository.py` — add `TopicInsightRecord` dataclass; add `list_topic_insights_for_student` method
- `apps/api/app/domains/progress/schemas.py` — add `TopicInsightResponse`, `TopicInsightListResponse`
- `apps/api/app/domains/progress/router.py` — add import of new schema types; add `get_student_topic_insights` endpoint
- `apps/api/tests/test_progress_api.py` — add tests 24–29

**No changes needed to:**
- `_require_parent_or_student` — use as-is
- `reset_progress_state_for_tests` — use as-is
- Existing endpoints or schemas

### Regression Risk

- `ConfirmedRecommendationRecord` is `frozen=True` — this story does NOT modify it; `TopicInsightRecord` is a new dataclass
- `list_confirmed_recommendations_for_student` already exists and is used by the recommendations endpoint — do NOT modify it; `list_topic_insights_for_student` is additive
- Class-level state shared across repo instances — `reset_progress_state_for_tests()` already resets all relevant dicts; no new dicts are added

### Performance Note (NFR-001)

Topic insights endpoint performs O(R×T) work where R = confirmed recommendations and T = topics per rec. In-memory with in-process ASGI — well within 700 ms p95 threshold. No async ops, external I/O, or caching needed.

### References

- Story 3.3 ACs and user story: [Source: _bmad-output/implementation-artifacts/epics.md#Story-3.3]
- FR23 (strength/weakness indicators by subject/topic): [Source: _bmad-output/planning-artifacts/prd.md#FR23]
- FR-023 (parent dashboard cards for growth and risk): [Source: _bmad-output/planning-artifacts/srs.md#FR-023]
- NFR-001 (API p95 ≤ 700ms for student read endpoints): [Source: _bmad-output/planning-artifacts/srs.md#NFR-001]
- `ConfirmedRecommendationRecord` definition: [Source: apps/api/app/domains/grading/repository.py:112]
- `list_confirmed_recommendations_for_student`: [Source: apps/api/app/domains/grading/repository.py:567]
- `_require_parent_or_student` guard: [Source: apps/api/app/domains/progress/router.py:26]
- `_create_confirmed_recommendation_pipeline` test helper: [Source: apps/api/tests/test_progress_api.py:91]
- `_create_approved_grade_pipeline` test helper: [Source: apps/api/tests/test_progress_api.py:49]
- Domain Boundary Rule: [Source: apps/api/README.md#Domain-Boundary-Rule]
- Story 3.1 (access control foundation): [Source: _bmad-output/implementation-artifacts/3-1-linked-guardian-and-student-progress-access.md]
- Story 3.2 (grade enrichment + sort, 240 tests): [Source: _bmad-output/implementation-artifacts/3-2-outcome-explanations-and-trend-visualization.md]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Added `TopicInsightRecord(frozen=True)` dataclass to `grading/repository.py` after `ConfirmedRecommendationRecord`
- Added `list_topic_insights_for_student(student_id, org_id) -> tuple[list[TopicInsightRecord], bool]` to `InMemoryGradingRepository`: sufficient-data gate checks `_grade_approvals`, then delegates to `list_confirmed_recommendations_for_student` (DRY), de-duplicates topics via newest-first `datetime.fromisoformat(confirmed_at)` sort with `rec_job_id` secondary key
- Added `TopicInsightResponse` and `TopicInsightListResponse` Pydantic models to `progress/schemas.py`
- Added `GET /progress/students/{student_id}/topic-insights` endpoint to `progress/router.py` using `_require_parent_or_student` guard (unchanged)
- Added tests 24–29 to `test_progress_api.py` covering: happy path (parent + student roles), insufficient-data gate, de-duplication, access control (teacher/unauth/wrong user), org isolation, empty-but-sufficient state
- Fixed test HTTP client pattern: all new tests use `asyncio.run()` + `httpx.AsyncClient(transport=httpx.ASGITransport(app=app))` consistent with existing test suite
- Full suite: 246/246 passed (240 prior + 6 new); zero regressions

### File List

- `apps/api/app/domains/grading/repository.py` — added `TopicInsightRecord` dataclass; added `list_topic_insights_for_student` method; code review fixes: walrus operator in sufficient-data gate (M3), empty topic skip guard (M1)
- `apps/api/app/domains/progress/schemas.py` — added `TopicInsightResponse`, `TopicInsightListResponse`
- `apps/api/app/domains/progress/router.py` — imported new schema types; added `get_student_topic_insights` endpoint
- `apps/api/tests/test_progress_api.py` — added tests 24–29 (`test_topic_insights_*`); code review additions: Test 30 (NFR-001 performance, AC6), Test 31 (repo-layer org isolation, AC5); code review fix: Test 28 now uses cross-org guardian link to exercise defense-in-depth org check (M1)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — sprint status synced: 3-3-strength-weakness-indicators-and-next-step-guidance → done

## Change Log

- Story created (2026-03-18)
- Implementation complete (2026-03-18): added `TopicInsightRecord`, `list_topic_insights_for_student`, `TopicInsightResponse`/`TopicInsightListResponse` schemas, `GET /progress/students/{student_id}/topic-insights` endpoint, and tests 24–29; 246/246 passing
- Code review complete (2026-03-19): fixed empty topic skip guard (M1), walrus operator in sufficient-data gate (M3), added Test 30 (AC6 NFR-001 performance for topic-insights), added Test 31 (AC5 repo-layer org isolation for topic-insights); 248/248 passing
- Code review pass 2 (2026-03-19): fixed Test 28 org isolation — now creates cross-org guardian link so defense-in-depth check at router.py:46-48 is exercised (was testing "no link" → 404, now tests "cross-org link" → 404); documented sprint-status.yaml in File List

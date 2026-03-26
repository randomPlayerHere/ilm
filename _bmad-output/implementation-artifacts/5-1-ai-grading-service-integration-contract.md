# Story 5.1: AI Grading Service Integration Contract

Status: done

## Story

As a developer,
I want the AI grading service contract defined with endpoints, error codes, confidence scoring, and mock endpoints,
so that all grading stories can develop against a stable, testable interface.

## Acceptance Criteria

**AC1 — Contract defines input/output schema**
Given the AI grading service needs to be integrated
When the service contract is defined
Then it specifies:
- Input schema: `image_url` (str), `rubric_context` (dict[str, str]), `standards_profile` (str | None)
- Output schema: `suggested_score` (str), `feedback_text` (str), `rubric_breakdown` (dict[str, str]), `confidence_level` (str: "high"|"medium"|"low"), `confidence_score` (float 0-1), `confidence_reason` (str | None), `practice_recommendations` (list[str])
- Error schema: `error_code` (str), `reason` (str), `retryable` (bool)

**AC2 — Confidence levels defined**
Given the contract defines confidence levels
When the AI returns a result
Then confidence is one of: `"high"` (green), `"medium"` (amber), `"low"` (red)
And `confidence_score` is a float 0-1
And `confidence_reason` is a human-readable string present for non-high confidence results

**AC3 — Error codes defined**
Given the contract defines error codes
When the AI fails to process an image
Then specific error codes are returned: `IMAGE_BLURRY`, `IMAGE_UNREADABLE`, `MODEL_TIMEOUT`, `MODEL_ERROR`, `RATE_LIMITED`
And each code includes a `retryable` boolean and a `reason` string

**AC4 — Retry behavior with exponential backoff**
Given the contract defines retry behavior
When a retryable error occurs
Then the system retries up to 2 times with exponential backoff (2s, 4s)
And after 2 failures, the job is marked as `"failed"` and routed to DLQ (status update in-memory)

**AC5 — Mock mode via environment variable**
Given development needs to proceed before the AI model is production-ready
When `AI_MOCK_MODE=true` is set in the environment
Then the mock provider returns realistic grading responses with configurable confidence levels and error scenarios
And mock mode is the default for local development

**AC6 — GradingResult includes confidence fields**
Given a grading job completes
When the result is returned from `GET /grading/assignments/{assignment_id}/jobs/{job_id}`
Then `GradingJobWithResultResponse.result` includes `confidence_level`, `confidence_score`, and `confidence_reason`
And `GradingResultResponse` in `packages/contracts/src/grading.ts` reflects these fields

## Tasks / Subtasks

- [x] Task 1: Create AI grading provider module (AC: #1, #2, #3)
  - [x] 1.1 Create `apps/api/app/domains/grading/ai_provider.py` with `AIGradingRequest`, `AIGradingResponse`, `AIGradingError` dataclasses — see Dev Notes for exact schema
  - [x] 1.2 Add `AI_ERROR_CODES` dict mapping code → `(retryable: bool, default_reason: str)` — see Dev Notes for all 5 codes
  - [x] 1.3 Define `AIGradingProvider` Protocol with `grade(request: AIGradingRequest) -> AIGradingResponse` — raises `AIGradingError` on failure
  - [x] 1.4 Implement `MockAIGradingProvider` with class-level `_scenario` state (default: `"success_high"`) — see Dev Notes for all scenarios

- [x] Task 2: Extend GradingResultRecord and GradingResult with confidence fields (AC: #2, #6)
  - [x] 2.1 Add `confidence_level: str = "high"`, `confidence_score: float = 0.9`, `confidence_reason: str | None = None` to `GradingResultRecord` in `apps/api/app/domains/grading/repository.py` — fields with defaults MUST come after fields without defaults
  - [x] 2.2 Update `save_grading_result()` in `InMemoryGradingRepository` to accept optional `confidence_level`, `confidence_score`, `confidence_reason` params — see Dev Notes for signature
  - [x] 2.3 Add `confidence_level: str = "high"`, `confidence_score: float = 0.9`, `confidence_reason: str | None = None` to `GradingResult` dataclass in `apps/api/app/domains/grading/service.py`
  - [x] 2.4 Update `_to_grading_result()` in `GradingService` to pass confidence fields from record to domain object

- [x] Task 3: Update GradingService to use AI provider with retry logic (AC: #4, #5)
  - [x] 3.1 Add `ai_provider: AIGradingProvider` parameter to `GradingService.__init__()` — see Dev Notes for exact signature and import
  - [x] 3.2 Replace the hardcoded stub in `process_grading_job()` with AI provider call + retry loop — see Dev Notes for exact implementation with injectable `_sleep` for test compatibility
  - [x] 3.3 On `AIGradingError` with `retryable=False` or after 2 retries: update job to `"failed"` status — use existing `update_grading_job()` pattern
  - [x] 3.4 Remove `GradingService._fail_on_job_ids` class variable AND the `GradingProcessError` exception class — failure injection now handled via `MockAIGradingProvider._scenario`; `GradingProcessError` is no longer raised by `process_grading_job()`

- [x] Task 4: Update router and environment config (AC: #5)
  - [x] 4.1 Update `_grading_service` singleton in `apps/api/app/domains/grading/router.py` to instantiate correct provider based on `AI_MOCK_MODE` env var — see Dev Notes for exact pattern; also update `reset_grading_state_for_tests()` to call `MockAIGradingProvider.reset()` to prevent mock state bleeding across API tests
  - [x] 4.2 Add `AI_MOCK_MODE=true` to `.env.local` (and `.env.example` if it exists) — the api/worker services use `env_file: .env.local` with NO existing `environment:` block in docker-compose.yml; adding to `.env.local` is the correct approach — see Dev Notes for placement
  - [x] 4.3 The project uses `apps/api/app/core/settings.py` (NOT `config.py`) with a plain `@dataclass` — do NOT modify settings.py; reading `AI_MOCK_MODE` directly from `os.environ` in the router (already shown in Task 4.1) is the correct approach for this story

- [x] Task 5: Update schemas and TypeScript contracts (AC: #6)
  - [x] 5.1 Add `confidence_level: str`, `confidence_score: float`, `confidence_reason: str | None` to `GradingResultResponse` in `apps/api/app/domains/grading/schemas.py`
  - [x] 5.2 Create `packages/contracts/src/grading.ts` — does NOT currently exist — with `GradingResultResponse` interface including confidence fields — see Dev Notes for full interface
  - [x] 5.3 Add named type export to `packages/contracts/src/index.ts` matching the file's existing `export type { ... }` pattern — see Dev Notes for exact export block
  - [x] 5.4 Update `_to_grading_job_with_result_response()` in `apps/api/app/domains/grading/router.py` to pass the three new confidence fields to `GradingResultResponse` — **REQUIRED**: `confidence_level` and `confidence_score` have no defaults in Pydantic and will cause a runtime validation error if omitted — see Dev Notes for exact change

- [x] Task 6: Update tests (AC: all)
  - [x] 6.1 Update `apps/api/tests/test_grading_service.py` — replace ALL `_fail_on_job_ids` usage with `MockAIGradingProvider` scenario injection; also replace the two `with pytest.raises(GradingProcessError):` test blocks (lines ~715 and ~740) with `assert status.status == "failed"` assertions — `GradingProcessError` is removed in Task 3.4 and must not appear in tests — see Dev Notes for test patterns
  - [x] 6.2 Update `apps/api/tests/test_grading_api.py` — assert `confidence_level`, `confidence_score`, `confidence_reason` present in grading result responses
  - [x] 6.3 Add tests for retry behavior: `"fail_then_succeed"` scenario verifies job completes after one retry; `"fail_permanent"` verifies job marked `"failed"` after exhausting retries
  - [x] 6.4 Add test for `IMAGE_BLURRY` non-retryable code: job → failed immediately (no retries)
  - [x] 6.5 Run `pnpm typecheck` — zero TypeScript errors required
  - [x] 6.6 Run `python -m pytest apps/api/tests/ -v` — all tests must pass (previous count: 351)

## Dev Notes

### Overview

Story 5.1 defines the **AI grading service interface** that all subsequent Epic 5 stories depend on. It replaces the hardcoded stub in `process_grading_job()` with a proper provider protocol + mock implementation.

**Scope boundary**: This story is **backend only** — no mobile UI changes. It:
- Adds the `ai_provider.py` module with the contract definition
- Extends `GradingResult` with confidence fields
- Upgrades `process_grading_job()` from stub to provider-backed with retry
- Creates `packages/contracts/src/grading.ts` (new file — does not exist yet)

**Critical context**: The `grading` domain already has significant implementation from Epics 2–3 (assignments, artifacts, grading jobs, grade approvals, grade versions, recommendations). DO NOT touch or rewrite these — Story 5.1 is **additive only**. The stub is being upgraded, not removed.

---

### Task 1 Detail: AI Provider Module (`ai_provider.py`)

Create `apps/api/app/domains/grading/ai_provider.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

# ─── Error codes ────────────────────────────────────────────────────────────
# Maps error code → (retryable, default_reason)
AI_ERROR_CODES: dict[str, tuple[bool, str]] = {
    "IMAGE_BLURRY":       (False, "Image quality is too low for analysis"),
    "IMAGE_UNREADABLE":   (False, "Image content could not be parsed"),
    "MODEL_TIMEOUT":      (True,  "AI model timed out — will retry"),
    "MODEL_ERROR":        (True,  "AI model returned an unexpected error — will retry"),
    "RATE_LIMITED":       (True,  "AI provider rate limit reached — will retry"),
}


class AIGradingError(Exception):
    """Raised by AIGradingProvider.grade() on failure."""
    def __init__(self, error_code: str, reason: str | None = None) -> None:
        entry = AI_ERROR_CODES.get(error_code)
        if entry is None:
            raise ValueError(f"Unknown AI error code: {error_code!r}")
        self.error_code = error_code
        self.retryable: bool = entry[0]
        self.reason: str = reason or entry[1]
        super().__init__(self.reason)


@dataclass(frozen=True)
class AIGradingRequest:
    image_url: str
    rubric_context: dict[str, str]
    standards_profile: str | None = None


@dataclass(frozen=True)
class AIGradingResponse:
    suggested_score: str
    feedback_text: str
    rubric_breakdown: dict[str, str]
    confidence_level: str          # "high" | "medium" | "low"
    confidence_score: float        # 0.0 – 1.0
    practice_recommendations: list[str]
    confidence_reason: str | None = None   # present for non-high confidence


class AIGradingProvider(Protocol):
    """Contract that all AI grading provider implementations must satisfy."""
    def grade(self, request: AIGradingRequest) -> AIGradingResponse:
        """Grade an assignment image.

        Returns AIGradingResponse on success.
        Raises AIGradingError on failure (with retryable flag set appropriately).
        """
        ...


# ─── Mock implementation ─────────────────────────────────────────────────────

_MOCK_SCENARIOS: dict[str, AIGradingResponse | str] = {
    # str values are error_codes; AIGradingResponse values are successes
    "success_high": AIGradingResponse(
        suggested_score="85/100",
        feedback_text=(
            "Good work overall. Content is accurate and presentation is strong. "
            "Review completeness of answers on section 3."
        ),
        rubric_breakdown={
            "content_accuracy": "meets_expectations",
            "presentation": "exceeds_expectations",
            "completeness": "meets_expectations",
        },
        confidence_level="high",
        confidence_score=0.92,
        practice_recommendations=[
            "Review section 3 for completeness gaps.",
        ],
        confidence_reason=None,
    ),
    "success_medium": AIGradingResponse(
        suggested_score="72/100",
        feedback_text=(
            "Decent attempt. Some sections are unclear — the handwriting in the lower half "
            "made analysis less certain."
        ),
        rubric_breakdown={
            "content_accuracy": "approaching_expectations",
            "presentation": "meets_expectations",
            "completeness": "approaching_expectations",
        },
        confidence_level="medium",
        confidence_score=0.61,
        practice_recommendations=[
            "Practice content accuracy on foundational concepts.",
            "Ensure all rubric sections are fully addressed.",
        ],
        confidence_reason="Handwriting in bottom section was partially unclear",
    ),
    "success_low": AIGradingResponse(
        suggested_score="60/100",
        feedback_text="AI analysis has low confidence — please review manually.",
        rubric_breakdown={
            "content_accuracy": "below_expectations",
            "presentation": "approaching_expectations",
            "completeness": "below_expectations",
        },
        confidence_level="low",
        confidence_score=0.31,
        practice_recommendations=[
            "Review foundational concepts in the relevant chapter.",
            "Ensure all rubric sections are fully addressed.",
            "Practice structuring responses with clear opening and conclusion.",
        ],
        confidence_reason="Image quality and handwriting clarity were insufficient for reliable analysis",
    ),
    # Error scenarios — string values are AI_ERROR_CODES
    "fail_image_blurry":    "IMAGE_BLURRY",
    "fail_image_unreadable":"IMAGE_UNREADABLE",
    "fail_model_error":     "MODEL_ERROR",
    "fail_model_timeout":   "MODEL_TIMEOUT",
    "fail_rate_limited":    "RATE_LIMITED",
}


class MockAIGradingProvider:
    """Deterministic mock for development and testing.

    Control via class-level _scenario:
        MockAIGradingProvider.set_scenario("success_medium")
        MockAIGradingProvider.set_scenario("fail_model_error")

    For retry testing use "fail_then_succeed":
        - First N calls raise MODEL_ERROR (retryable=True)
        - Subsequent calls return success_high
    """
    _scenario: str = "success_high"
    _fail_count: int = 0          # for "fail_then_succeed": number of initial failures
    _call_tracker: dict[str, int] = {}  # job_id → call count

    @classmethod
    def set_scenario(cls, scenario: str, fail_count: int = 1) -> None:
        cls._scenario = scenario
        cls._fail_count = fail_count
        cls._call_tracker = {}

    @classmethod
    def reset(cls) -> None:
        cls._scenario = "success_high"
        cls._fail_count = 0
        cls._call_tracker = {}

    def grade(self, request: AIGradingRequest) -> AIGradingResponse:
        scenario = self.__class__._scenario

        if scenario == "fail_then_succeed":
            call_key = request.image_url
            count = self.__class__._call_tracker.get(call_key, 0) + 1
            self.__class__._call_tracker[call_key] = count
            if count <= self.__class__._fail_count:
                raise AIGradingError("MODEL_ERROR")
            return _MOCK_SCENARIOS["success_high"]  # type: ignore[return-value]

        result = _MOCK_SCENARIOS.get(scenario)
        if result is None:
            raise ValueError(f"Unknown mock scenario: {scenario!r}")
        if isinstance(result, str):
            raise AIGradingError(result)
        return result
```

---

### Task 2 Detail: Extend GradingResultRecord and GradingResult

#### Step 2.1 — `GradingResultRecord` (`repository.py`)

Fields with defaults MUST come after fields without defaults in frozen dataclasses:

```python
@dataclass(frozen=True)
class GradingResultRecord:
    job_id: str
    proposed_score: str
    rubric_mapping: dict[str, str]
    draft_feedback: str
    generated_at: str
    # Confidence fields (added Story 5.1) — defaults for backward compatibility
    confidence_level: str = "high"          # "high" | "medium" | "low"
    confidence_score: float = 0.9           # 0.0 – 1.0
    confidence_reason: str | None = None
```

#### Step 2.2 — Update `save_grading_result()` (`repository.py`)

Find the existing `save_grading_result()` method and add the three new optional parameters:

```python
def save_grading_result(
    self,
    job_id: str,
    proposed_score: str,
    rubric_mapping: dict[str, str],
    draft_feedback: str,
    confidence_level: str = "high",
    confidence_score: float = 0.9,
    confidence_reason: str | None = None,
) -> GradingResultRecord:
    now = datetime.now(UTC).isoformat()
    record = GradingResultRecord(
        job_id=job_id,
        proposed_score=proposed_score,
        rubric_mapping=rubric_mapping,
        draft_feedback=draft_feedback,
        generated_at=now,
        confidence_level=confidence_level,
        confidence_score=confidence_score,
        confidence_reason=confidence_reason,
    )
    self.__class__._grading_results[job_id] = record
    return record
```

#### Step 2.3 & 2.4 — `GradingResult` and `_to_grading_result()` (`service.py`)

Add confidence fields with defaults to `GradingResult` (it lives at the bottom of `service.py`):

```python
@dataclass(frozen=True)
class GradingResult:
    job_id: str
    proposed_score: str
    rubric_mapping: dict[str, str]
    draft_feedback: str
    generated_at: str
    confidence_level: str = "high"
    confidence_score: float = 0.9
    confidence_reason: str | None = None
```

Update `_to_grading_result()` to pass confidence fields:

```python
def _to_grading_result(self, record: GradingResultRecord) -> GradingResult:
    return GradingResult(
        job_id=record.job_id,
        proposed_score=record.proposed_score,
        rubric_mapping=record.rubric_mapping,
        draft_feedback=record.draft_feedback,
        generated_at=record.generated_at,
        confidence_level=record.confidence_level,
        confidence_score=record.confidence_score,
        confidence_reason=record.confidence_reason,
    )
```

---

### Task 3 Detail: Update GradingService (`service.py`)

#### Step 3.1 — Add `ai_provider` to `GradingService.__init__()`

```python
from app.domains.grading.ai_provider import AIGradingProvider, AIGradingError, AIGradingRequest

class GradingService:
    # REMOVE: _fail_on_job_ids class variable — test injection now via MockAIGradingProvider

    def __init__(
        self,
        repository: InMemoryGradingRepository,
        ai_provider: AIGradingProvider,
    ) -> None:
        self._repository = repository
        self._ai_provider = ai_provider
```

#### Step 3.2 — Replace `process_grading_job()` stub with provider + retry

Replace the entire `process_grading_job()` method body. The `_sleep` parameter is injectable for tests to avoid actual delays:

```python
import time as _time_module  # top of file (after existing imports)

def process_grading_job(
    self,
    job_id: str,
    _sleep: Callable[[float], None] | None = None,
) -> None:
    """Run AI grading for job. Called by background task after job submission.

    Retries up to 2 times with exponential backoff (2s, 4s) on retryable errors.
    Non-retryable errors mark the job failed immediately.
    _sleep is injectable for tests to skip actual delays.
    """
    if _sleep is None:
        _sleep = _time_module.sleep

    job = self._repository.get_grading_job_by_id(job_id)
    if job is None:
        return
    # Idempotency guard: no-op if already completed or failed
    if job.status in {"completed", "failed"}:
        return

    artifact = self._repository.get_artifact(job.artifact_id)
    # Build request — use stub URL since real S3 upload happens in Story 5.9
    image_url = artifact.storage_key if artifact else f"stub://{job.artifact_id}"
    request = AIGradingRequest(
        image_url=image_url,
        rubric_context={"content_accuracy": "str", "presentation": "str", "completeness": "str"},
        standards_profile=None,
    )

    backoff_delays = [2.0, 4.0]
    max_attempts = len(backoff_delays) + 1  # 3 total: initial + 2 retries

    for attempt in range(max_attempts):
        self._repository.update_grading_job(
            job_id=job_id,
            status="processing",
            attempt_count=attempt + 1,
        )
        try:
            response = self._ai_provider.grade(request)
            break  # success — exit retry loop
        except AIGradingError as exc:
            is_last_attempt = attempt == max_attempts - 1
            if not exc.retryable or is_last_attempt:
                self._repository.update_grading_job(
                    job_id=job_id,
                    status="failed",
                    attempt_count=attempt + 1,
                )
                return  # job failed — caller checks status
            # Retryable error — wait and retry
            _sleep(backoff_delays[attempt])
    else:
        # for...else: this block runs only if the loop completed WITHOUT a `break`
        # (i.e., all attempts exhausted without a successful response)
        self._repository.update_grading_job(job_id=job_id, status="failed", attempt_count=max_attempts)
        return

    # Save result from successful AI response
    self._repository.save_grading_result(
        job_id=job_id,
        proposed_score=response.suggested_score,
        rubric_mapping=response.rubric_breakdown,
        draft_feedback=response.feedback_text,
        confidence_level=response.confidence_level,
        confidence_score=response.confidence_score,
        confidence_reason=response.confidence_reason,
    )

    now = datetime.now(UTC).isoformat()
    self._repository.update_grading_job(
        job_id=job_id,
        status="completed",
        attempt_count=attempt + 1,
        completed_at=now,
    )
```

> **Import**: Add `from collections.abc import Callable` to service.py imports (already available in Python 3.12+).

---

### Task 4 Detail: Router and Environment Config

#### Step 4.1 — Update `_grading_service` singleton (`router.py`)

```python
import os

from app.domains.grading.ai_provider import MockAIGradingProvider

def _make_ai_provider() -> MockAIGradingProvider:
    # AI_MOCK_MODE defaults to "true" for local development
    mock_mode = os.environ.get("AI_MOCK_MODE", "true").lower()
    if mock_mode == "true":
        return MockAIGradingProvider()
    # Future: return RealAIGradingProvider() when cloud credentials available
    return MockAIGradingProvider()

_grading_service = GradingService(
    repository=InMemoryGradingRepository(),
    ai_provider=_make_ai_provider(),
)
```

Also update `reset_grading_state_for_tests()` to reset mock state, preventing contamination in API-layer tests (`test_grading_api.py` calls this in `setup_function`):

```python
def reset_grading_state_for_tests() -> None:
    InMemoryGradingRepository.reset_state()
    MockAIGradingProvider.reset()  # ADD — prevents mock scenario state from bleeding across tests
```

#### Step 4.2 — Environment config

The `api` and `worker` services in `docker-compose.yml` use `env_file: .env.local` and have **no existing `environment:` block**. Add `AI_MOCK_MODE=true` to `.env.local` (the correct approach — consistent with how all other env vars are set):

```dotenv
# .env.local — add after NOTIFICATION_PROVIDER line
AI_MOCK_MODE=true
```

Also add the key to `.env.example` if that file exists, so other developers know the variable exists:

```dotenv
AI_MOCK_MODE=true
```

#### Step 4.3 — Core config

The project uses `apps/api/app/core/settings.py` (not `config.py`) with a plain `@dataclass(frozen=True)` — **do NOT modify it**. Reading `AI_MOCK_MODE` directly from `os.environ` in the router (as shown in Step 4.1 above) is correct and complete for this story.

---

### Task 5 Detail: Schemas and TypeScript Contracts

#### Step 5.1 — Update `GradingResultResponse` (`schemas.py`)

```python
class GradingResultResponse(BaseModel):
    proposed_score: str
    rubric_mapping: dict[str, str]
    draft_feedback: str
    generated_at: str
    confidence_level: str               # "high" | "medium" | "low"
    confidence_score: float             # 0.0 – 1.0
    confidence_reason: str | None       # present for non-high confidence
```

#### Step 5.2 — Create `packages/contracts/src/grading.ts` (NEW FILE — does NOT exist yet)

```typescript
// Grading domain contract types
// Generated from OpenAPI 3.1 — Story 5.1

export interface AIGradingResultResponse {
  proposed_score: string;
  rubric_mapping: Record<string, string>;
  draft_feedback: string;
  generated_at: string;
  confidence_level: "high" | "medium" | "low";
  confidence_score: number;           // 0.0 – 1.0
  confidence_reason: string | null;   // present for non-high confidence
}

export interface GradingJobResponse {
  job_id: string;
  artifact_id: string;
  assignment_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  attempt_count: number;
  submitted_at: string;
  completed_at: string | null;
}

export interface GradingJobWithResultResponse extends GradingJobResponse {
  result: AIGradingResultResponse | null;
  is_approved: boolean;
}

export interface GradeApprovalResponse {
  job_id: string;
  approved_score: string;
  approved_feedback: string;
  approver_user_id: string;
  approved_at: string;
  version: number;
}

export type AIConfidenceLevel = "high" | "medium" | "low";

export type AIGradingErrorCode =
  | "IMAGE_BLURRY"
  | "IMAGE_UNREADABLE"
  | "MODEL_TIMEOUT"
  | "MODEL_ERROR"
  | "RATE_LIMITED";
```

#### Step 5.3 — Update `packages/contracts/src/index.ts`

The file uses named `export type { ... }` syntax — match that pattern (do NOT use `export *`):

```typescript
/** Grading contracts */
export type {
  AIGradingResultResponse,
  GradingJobResponse,
  GradingJobWithResultResponse,
  GradeApprovalResponse,
  AIConfidenceLevel,
  AIGradingErrorCode,
} from "./grading";
```

#### Step 5.4 — Update `_to_grading_job_with_result_response()` in `router.py`

Find this function (currently around line 200) and add the three confidence fields to the `GradingResultResponse` constructor. `confidence_level` and `confidence_score` have no defaults in the Pydantic model — omitting them causes a **runtime validation error**:

```python
result_response = GradingResultResponse(
    proposed_score=r.proposed_score,
    rubric_mapping=r.rubric_mapping,
    draft_feedback=r.draft_feedback,
    generated_at=r.generated_at,
    confidence_level=r.confidence_level,    # ADD
    confidence_score=r.confidence_score,    # ADD
    confidence_reason=r.confidence_reason,  # ADD
)
```

---

### Task 6 Detail: Tests

#### Step 6.1 — Update `test_grading_service.py`

Remove the import of `GradingProcessError` from the top of the file — it is deleted in Task 3.4 and must not appear anywhere in tests.

Replace all `GradingService._fail_on_job_ids` usage with `MockAIGradingProvider` scenario injection:

**Before (old pattern)**:
```python
GradingService._fail_on_job_ids.add(job.job_id)
# ... later ...
with pytest.raises(GradingProcessError):
    service.process_grading_job(job.job_id)
```

**After (new pattern)**:
```python
from app.domains.grading.ai_provider import MockAIGradingProvider

def _make_service() -> GradingService:
    return GradingService(
        repository=InMemoryGradingRepository(),
        ai_provider=MockAIGradingProvider(),
    )

# Replace pytest.raises(GradingProcessError) blocks with:
MockAIGradingProvider.set_scenario("fail_model_error")
service.process_grading_job(job.job_id, _sleep=lambda _: None)
status = service.get_grading_job_status(...)
assert status.status == "failed"
```

There are **two** existing tests with `with pytest.raises(GradingProcessError):` (around lines 715 and 740). Both must be rewritten — they tested that `process_grading_job` raises; the new contract is that it marks the job `"failed"` and returns, never raises.

> **Critical**: Each test should use `MockAIGradingProvider.reset()` in setup. Do NOT share a global service between tests when testing failure scenarios.

Add `setup_function` reset:
```python
def setup_function():
    InMemoryGradingRepository.reset_state()
    MockAIGradingProvider.reset()
```

#### Step 6.2 — Update `test_grading_api.py`

Find test that asserts on grading result content and add confidence field assertions:

```python
# After grading job completes, assert confidence fields present
result_body = response.json()
result = result_body.get("result")
assert result is not None
assert result["confidence_level"] in ("high", "medium", "low")
assert isinstance(result["confidence_score"], float)
assert 0.0 <= result["confidence_score"] <= 1.0
assert "confidence_reason" in result  # may be None for high confidence
```

#### Step 6.3 — Retry behavior tests (`test_grading_service.py`)

**Test: `test_process_grading_job_retries_on_model_error`** — verifies retry path

```python
def test_process_grading_job_retries_on_model_error():
    MockAIGradingProvider.set_scenario("fail_then_succeed", fail_count=1)
    service = _make_service()
    # ... create assignment, artifact, submit job (setup)
    # Process with no-op sleep to avoid test delays
    service.process_grading_job(job.job_id, _sleep=lambda _: None)
    # Job should complete after 1 retry
    status = service.get_grading_job_status(
        actor_user_id=..., actor_org_id=..., assignment_id=..., job_id=job.job_id
    )
    assert status.status == "completed"
    assert status.attempt_count == 2  # initial + 1 retry
    assert status.result is not None
    assert status.result.confidence_level == "high"
```

**Test: `test_process_grading_job_fails_after_max_retries`** — verifies exhaustion path

```python
def test_process_grading_job_fails_after_max_retries():
    MockAIGradingProvider.set_scenario("fail_model_error")  # always fails
    service = _make_service()
    # ... setup
    service.process_grading_job(job.job_id, _sleep=lambda _: None)
    status = service.get_grading_job_status(...)
    assert status.status == "failed"
    assert status.attempt_count == 3  # all 3 attempts exhausted
    assert status.result is None
```

**Test: `test_process_grading_job_fails_immediately_on_non_retryable_error`** — IMAGE_BLURRY

```python
def test_process_grading_job_fails_immediately_on_non_retryable_error():
    MockAIGradingProvider.set_scenario("fail_image_blurry")
    service = _make_service()
    # ... setup
    service.process_grading_job(job.job_id, _sleep=lambda _: None)
    status = service.get_grading_job_status(...)
    assert status.status == "failed"
    assert status.attempt_count == 1  # no retries — IMAGE_BLURRY is not retryable
```

**Test: `test_process_grading_job_result_includes_confidence`**

```python
def test_process_grading_job_result_includes_confidence():
    MockAIGradingProvider.set_scenario("success_medium")
    service = _make_service()
    # ... setup and process
    service.process_grading_job(job.job_id, _sleep=lambda _: None)
    status = service.get_grading_job_status(...)
    assert status.result.confidence_level == "medium"
    assert 0.5 <= status.result.confidence_score <= 0.7
    assert status.result.confidence_reason is not None  # medium always has reason
```

---

### Repository Access Rules (Unchanged)

- `GradingService` only uses repository methods — never direct class-level `_dicts`
- `GradingService` only uses `ai_provider.grade()` — never direct AI SDK calls
- Mock state is class-level (`MockAIGradingProvider._scenario`) — injectable via class methods

---

### What NOT To Implement

- **Real AI provider integration** (Claude / GPT-4 Vision API) — this is a mock contract story only
- **Mobile camera UI** — Epic 5 Story 5.2
- **Photo upload/S3 integration** — Epic 5 Story 5.9 (pre-signed URL is stub `storage_key` until 5.9)
- **Push notifications for grading completion** — Epic 5 Story 5.3
- **GradingCard UI component** — Epic 5 Story 5.4
- **Offline queue** — Epic 5 Story 5.8
- **Batch progress indicator** — Epic 5 Story 5.3
- **Practice recommendations in GradingCard** — Epic 5 Story 5.7 (recommendations exist but display is Epic 5.7)
- **SQS integration** — mock BackgroundTasks pattern is retained for MVP

---

### File Structure Impact

Files to **create**:
- `apps/api/app/domains/grading/ai_provider.py` (new module — core deliverable)
- `packages/contracts/src/grading.ts` (new contract file — does not exist yet)

Files to **modify**:
- `apps/api/app/domains/grading/repository.py` (add confidence fields to `GradingResultRecord`; update `save_grading_result()`)
- `apps/api/app/domains/grading/service.py` (add confidence fields to `GradingResult`; update `_to_grading_result()`, `__init__()`, `process_grading_job()`; remove `_fail_on_job_ids` class variable AND `GradingProcessError` exception class; add `Callable` import)
- `apps/api/app/domains/grading/schemas.py` (add confidence fields to `GradingResultResponse`)
- `apps/api/app/domains/grading/router.py` (update singleton with AI provider; add `AI_MOCK_MODE` env var logic; add `os` import; update `_to_grading_job_with_result_response()` to pass confidence fields; update `reset_grading_state_for_tests()` to call `MockAIGradingProvider.reset()`)
- `packages/contracts/src/index.ts` (add `export * from "./grading"`)
- `docker-compose.yml` (add `AI_MOCK_MODE=true` to api/worker env)
- `apps/api/tests/test_grading_service.py` (replace `_fail_on_job_ids` pattern; add retry/confidence tests; add `setup_function` with `MockAIGradingProvider.reset()`)
- `apps/api/tests/test_grading_api.py` (add confidence field assertions to result assertions)

### Project Structure Notes

- New `ai_provider.py` lives in `apps/api/app/domains/grading/` (same domain module) — NOT in `app/core/` or `app/workers/`
- `MockAIGradingProvider` class-level state: safe to use across router/tests; call `MockAIGradingProvider.reset()` in `setup_function()`
- The `_sleep` injection pattern mirrors Python standard library testing conventions — no new testing deps needed
- `packages/contracts/src/grading.ts` must be created (file does not exist); `index.ts` uses `export *` pattern already established for `auth` and `onboarding`
- Previous stub output (`"85/100"`, `"meets_expectations"` etc.) becomes the `"success_high"` scenario — behavior is unchanged for existing tests unless scenario is explicitly changed

### References

- Epic 5 / Story 5.1 requirements: [Source: `_bmad-output/planning-artifacts/epics.md` #Story 5.1]
- Architecture — AI grading: [Source: `_bmad-output/planning-artifacts/architecture.md` #Stack Decisions] (`Multimodal vision models (Claude / GPT-4 Vision) — no OCR pipeline`)
- Architecture — async job architecture: [Source: `_bmad-output/planning-artifacts/architecture.md` #Core Architectural Decisions] (`SQS-driven worker service with idempotency keys, separate from API service`)
- Architecture — retry patterns: [Source: `_bmad-output/planning-artifacts/architecture.md` #API & Communication Patterns] (`idempotency keys, retry policies with exponential backoff, dead-letter queues`)
- Architecture — NFR4/NFR5: [Source: `_bmad-output/planning-artifacts/architecture.md` #Performance] (`AI grading ack ≤3s; 90% results within 60s`)
- Architecture — FR18b: [Source: `_bmad-output/planning-artifacts/epics.md` #Requirements] (`retries up to 2 times before manual fallback`)
- Existing `GradingService` stub: [Source: `apps/api/app/domains/grading/service.py:240`]
- Existing `GradingResultRecord`: [Source: `apps/api/app/domains/grading/repository.py:59`]
- `save_grading_result()` current signature: [Source: `apps/api/app/domains/grading/repository.py`]
- Previous story learnings (4.10): [Source: `_bmad-output/implementation-artifacts/4-10-coppa-consent-confirmation-gate.md`]
- Frozen dataclass field ordering rule (fields with defaults after fields without): [Source: `_bmad-output/implementation-artifacts/4-10-coppa-consent-confirmation-gate.md` #Step 1.1]
- `dataclasses.replace()` pattern for frozen records: [Source: `_bmad-output/implementation-artifacts/4-10-coppa-consent-confirmation-gate.md` #Step 2.2]
- `packages/contracts/src/index.ts` export pattern: [Source: `packages/contracts/src/index.ts`]
- `InMemoryGradingRepository.reset_state()`: [Source: `apps/api/app/domains/grading/router.py:57`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No blockers encountered. IDE diagnostics showed F401/F821 lint warnings that were stale (the imports are used in `process_grading_job`); confirmed correct by verifying file contents. All E501 line-length warnings are pre-existing in the codebase — not introduced by this story.

### Completion Notes List

- Created `ai_provider.py` with full contract: `AIGradingError`, `AIGradingRequest`, `AIGradingResponse`, `AIGradingProvider` Protocol, `MockAIGradingProvider` with 8 scenarios (3 success + 5 error + fail_then_succeed).
- Extended `GradingResultRecord` and `GradingResult` with `confidence_level/score/reason` fields (defaults maintain backward compatibility).
- Replaced hardcoded stub in `process_grading_job()` with AI provider call + 3-attempt retry loop (2s/4s backoff). Injectable `_sleep` avoids real delays in tests.
- Removed `GradingProcessError` exception class and `_fail_on_job_ids` class variable — failure injection now via `MockAIGradingProvider.set_scenario()`.
- Router updated with `_make_ai_provider()` factory, `AI_MOCK_MODE` env var support, and `MockAIGradingProvider.reset()` in test reset helper.
- `GradingResultResponse` in schemas.py now includes confidence fields (no defaults — required by Pydantic).
- Created `packages/contracts/src/grading.ts` with 6 exported TypeScript types.
- Tests: 354 passed (up from 351), 3 new tests added for retry behavior, max-retry exhaustion, and confidence fields. TypeScript typecheck: 0 errors.

### File List

- `apps/api/app/domains/grading/ai_provider.py` (created)
- `apps/api/app/domains/grading/repository.py` (modified — confidence fields on GradingResultRecord, save_grading_result signature)
- `apps/api/app/domains/grading/service.py` (modified — removed GradingProcessError/_fail_on_job_ids, added ai_provider param, replaced process_grading_job stub with retry loop, confidence fields on GradingResult)
- `apps/api/app/domains/grading/schemas.py` (modified — confidence fields on GradingResultResponse)
- `apps/api/app/domains/grading/router.py` (modified — _make_ai_provider factory, AI_MOCK_MODE, confidence fields in _to_grading_job_with_result_response, MockAIGradingProvider.reset in test helper)
- `packages/contracts/src/grading.ts` (created)
- `packages/contracts/src/index.ts` (modified — grading type exports)
- `.env.local` (modified — AI_MOCK_MODE=true)
- `.env.example` (modified — AI_MOCK_MODE=true)
- `apps/api/tests/test_grading_service.py` (modified — removed GradingProcessError import/_fail_on_job_ids, updated _make_service, rewrote 2 tests, added 3 new tests)
- `apps/api/tests/test_grading_api.py` (modified — confidence field assertions)

### Senior Developer Review (AI)

- Outcome: **Approved after fixes**
- High findings fixed:
    - Added missing `practice_recommendations` to grading result surface (repository, domain object, API schema/mapper, TypeScript contract).
    - Implemented explicit in-memory DLQ routing on terminal grading failures (`route_grading_job_to_dlq`), while preserving `failed` terminal job status.
    - Made `AI_MOCK_MODE` materially switch provider behavior via `NonMockAIGradingProvider` when disabled.
- Medium findings fixed:
    - Added test coverage for env-based provider switching and DLQ routing.
    - Removed unused import in AI provider module.

### Change Log

- 2026-03-26: Senior AI code review fixes applied (AC1 contract completeness, AC4 DLQ routing semantics, AI_MOCK_MODE behavior split), tests extended, story promoted to `done`.

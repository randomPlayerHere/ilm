from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

# ─── Error codes ────────────────────────────────────────────────────────────
# Maps error code → (retryable, default_reason)
AI_ERROR_CODES: dict[str, tuple[bool, str]] = {
    "IMAGE_BLURRY": (False, "Image quality is too low for analysis"),
    "IMAGE_UNREADABLE": (False, "Image content could not be parsed"),
    "MODEL_TIMEOUT": (True, "AI model timed out — will retry"),
    "MODEL_ERROR": (True, "AI model returned an unexpected error — will retry"),
    "RATE_LIMITED": (True, "AI provider rate limit reached — will retry"),
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
    confidence_level: str  # "high" | "medium" | "low"
    confidence_score: float  # 0.0 – 1.0
    practice_recommendations: list[str]
    confidence_reason: str | None = None  # present for non-high confidence


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
    "fail_image_blurry": "IMAGE_BLURRY",
    "fail_image_unreadable": "IMAGE_UNREADABLE",
    "fail_model_error": "MODEL_ERROR",
    "fail_model_timeout": "MODEL_TIMEOUT",
    "fail_rate_limited": "RATE_LIMITED",
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
    _fail_count: int = 0  # for "fail_then_succeed": number of initial failures
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


class NonMockAIGradingProvider:
    """Placeholder provider used when AI_MOCK_MODE is disabled.

    Story 5.1 intentionally does not implement real vendor integration yet.
    This provider keeps behavior explicit and distinct from mock mode.
    """

    def grade(self, request: AIGradingRequest) -> AIGradingResponse:  # noqa: ARG002
        raise AIGradingError(
            "MODEL_ERROR",
            "Real AI provider is not configured for this environment.",
        )

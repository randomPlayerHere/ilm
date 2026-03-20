"""Tests for async job processing abstraction."""
from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from app.core.jobs import BackgroundTasksJobProvider, SQSJobProvider


class TestBackgroundTasksJobProvider:
    def test_dispatch_calls_task_fn(self) -> None:
        provider = BackgroundTasksJobProvider()
        called_with: list[tuple] = []

        def my_task(a: int, b: str) -> None:
            called_with.append((a, b))

        provider.dispatch(my_task, 42, "hello")
        assert called_with == [(42, "hello")]

    def test_dispatch_returns_correlation_id(self) -> None:
        provider = BackgroundTasksJobProvider()
        cid = provider.dispatch(lambda: None)
        assert isinstance(cid, str)
        assert len(cid) > 0

    def test_dispatch_accepts_explicit_correlation_id(self) -> None:
        provider = BackgroundTasksJobProvider()
        cid = provider.dispatch(lambda: None, correlation_id="test-cid-123")
        assert cid == "test-cid-123"

    def test_dispatch_logs_completion(self, caplog: pytest.LogCaptureFixture) -> None:
        provider = BackgroundTasksJobProvider()

        def noop() -> None:
            pass

        with caplog.at_level(logging.INFO, logger="app.core.jobs"):
            provider.dispatch(noop, correlation_id="cid-abc")

        messages = [r.message for r in caplog.records]
        assert any("cid-abc" in m for m in messages)

    def test_dispatch_with_background_tasks_enqueues_task(self) -> None:
        provider = BackgroundTasksJobProvider()
        mock_bg = MagicMock()
        executed: list[int] = []

        def my_task(value: int) -> None:
            executed.append(value)

        provider.dispatch_with_background_tasks(mock_bg, my_task, 99)
        mock_bg.add_task.assert_called_once()


class TestSQSJobProviderIsStub:
    def test_dispatch_raises_not_implemented(self) -> None:
        provider = SQSJobProvider()
        with pytest.raises(NotImplementedError):
            provider.dispatch(lambda: None)

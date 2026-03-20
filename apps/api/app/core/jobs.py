from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from app.core.settings import settings

logger = logging.getLogger(__name__)


class JobProvider(ABC):
    """Queue-agnostic job dispatch interface.

    Swap implementations via JOB_PROVIDER config.
    Local dev  → BackgroundTasksJobProvider (FastAPI BackgroundTasks).
    Future SQS → SQSJobProvider.
    """

    @abstractmethod
    def dispatch(
        self,
        task_fn: Callable[..., Any],
        *args: Any,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Dispatch a job. Returns a correlation_id for tracing."""
        ...


class BackgroundTasksJobProvider(JobProvider):
    """Local dev provider using FastAPI BackgroundTasks.

    Because FastAPI BackgroundTasks requires access to the request context,
    callers must pass the `background_tasks` instance when dispatching.
    Use `dispatch_with_background_tasks()` instead of `dispatch()` for
    in-request usage.
    """

    def dispatch(
        self,
        task_fn: Callable[..., Any],
        *args: Any,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        cid = correlation_id or str(uuid.uuid4())
        logger.info("[JOB:dispatch] correlation_id=%s fn=%s", cid, task_fn.__name__)
        task_fn(*args, **kwargs)
        logger.info("[JOB:complete] correlation_id=%s fn=%s", cid, task_fn.__name__)
        return cid

    def dispatch_with_background_tasks(
        self,
        background_tasks: Any,
        task_fn: Callable[..., Any],
        *args: Any,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Enqueue task_fn into FastAPI BackgroundTasks with correlation logging."""
        cid = correlation_id or str(uuid.uuid4())
        logger.info("[JOB:enqueue] correlation_id=%s fn=%s", cid, task_fn.__name__)

        def _wrapper(*a: Any, **kw: Any) -> None:
            logger.info("[JOB:start] correlation_id=%s fn=%s", cid, task_fn.__name__)
            try:
                task_fn(*a, **kw)
                logger.info("[JOB:complete] correlation_id=%s fn=%s", cid, task_fn.__name__)
            except Exception:
                logger.exception("[JOB:failed] correlation_id=%s fn=%s", cid, task_fn.__name__)

        background_tasks.add_task(_wrapper, *args, **kwargs)
        return cid


class SQSJobProvider(JobProvider):
    """Future AWS SQS provider — swap in via JOB_PROVIDER=sqs."""

    def dispatch(
        self,
        task_fn: Callable[..., Any],
        *args: Any,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        raise NotImplementedError("SQS provider not yet implemented")


def _build_job_provider() -> JobProvider:
    provider = settings.job_provider
    if provider == "sqs":
        return SQSJobProvider()
    return BackgroundTasksJobProvider()


job_service: JobProvider = _build_job_provider()

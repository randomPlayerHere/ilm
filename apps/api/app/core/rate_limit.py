from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from time import monotonic


@dataclass
class InMemoryLoginRateLimiter:
    max_attempts: int = 5
    window_seconds: int = 300
    _attempts: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def _prune(self, key: str, now: float) -> None:
        queue = self._attempts[key]
        cutoff = now - self.window_seconds
        while queue and queue[0] < cutoff:
            queue.popleft()
        if not queue:
            self._attempts.pop(key, None)

    def _normalize_key(self, key: str) -> str:
        return key.strip().lower()

    def is_limited(self, key: str) -> bool:
        normalized = self._normalize_key(key)
        now = monotonic()
        self._prune(normalized, now)
        return len(self._attempts.get(normalized, ())) >= self.max_attempts

    def record_failure(self, key: str) -> None:
        normalized = self._normalize_key(key)
        now = monotonic()
        self._prune(normalized, now)
        self._attempts[normalized].append(now)

    def record_success(self, key: str) -> None:
        normalized = self._normalize_key(key)
        self._attempts.pop(normalized, None)

    def clear(self) -> None:
        self._attempts.clear()


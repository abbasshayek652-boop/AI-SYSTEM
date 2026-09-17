from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def with_retry(operation: Callable[[], T], *, attempts: int = 3, base_delay: float = 0.25) -> T:
    """Retry transient adapter operations with a small bounded backoff."""
    attempts = max(1, min(attempts, 5))
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == attempts - 1:
                raise
            time.sleep(base_delay * (2**attempt))
    assert last_error is not None
    raise last_error

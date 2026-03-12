"""Async retry decorator using tenacity with exponential back-off."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import structlog
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = structlog.get_logger(__name__)


def _before_sleep(retry_state: RetryCallState) -> None:
    """Log each retry attempt."""
    exc = retry_state.outcome and retry_state.outcome.exception()
    log.warning(
        "retrying",
        fn=getattr(retry_state.fn, "__qualname__", str(retry_state.fn)),
        attempt=retry_state.attempt_number,
        error=str(exc) if exc else None,
    )


def async_retry(
    *,
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[..., Any]:
    """Return a tenacity ``retry`` decorator pre-configured for async use.

    Parameters
    ----------
    max_attempts:
        Total number of attempts before giving up.
    min_wait:
        Minimum back-off delay in seconds.
    max_wait:
        Maximum back-off delay in seconds.
    retry_on:
        Exception types that should trigger a retry.
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retry_on),
        before_sleep=_before_sleep,
        reraise=True,
    )

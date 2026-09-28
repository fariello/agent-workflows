"""Unified policy and helper for code-only contention waits.

One shared policy across the codebase:
- Poll every 0.1s by default (tight common-case response for sub-second holds)
- Report progress every 60s to stderr naming what is awaited and who holds it
- Timeout after 1800s (30 minutes)
"""

from __future__ import annotations

import sys
import time
from typing import Any, Callable, NamedTuple, Optional

POLL_SECONDS: float = 0.1
REPORT_SECONDS: float = 60.0
TIMEOUT_SECONDS: float = 1800.0


class WaitResult(NamedTuple):
    ok: bool
    value: Any
    waited: float
    attempts: int
    detail: str


def _default_report(message: str) -> None:
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def _format_holder(
    holder: Optional[Callable[[], Optional[str]]],
) -> tuple[str, Optional[str]]:
    if holder is None:
        return "", None
    try:
        h = holder()
    except Exception:
        h = None
    if h is not None and str(h).strip():
        return f" held by {h}", str(h)
    return "", None


def wait_until(
    try_once: Callable[[], tuple[bool, Any]],
    *,
    what: str,
    holder: Optional[Callable[[], Optional[str]]] = None,
    timeout: float = TIMEOUT_SECONDS,
    poll: float = POLL_SECONDS,
    report_every: float = REPORT_SECONDS,
    report: Optional[Callable[[str], None]] = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
) -> WaitResult:
    """Bounded wait helper with periodic progress reporting and injectable clock."""
    _say = report if report is not None else _default_report
    start = now()
    timeout_val = float(timeout)
    poll_val = float(poll)
    report_every_val = float(report_every)

    attempts = 1
    done, value = try_once()
    if done:
        waited = max(0.0, now() - start)
        return WaitResult(
            ok=True, value=value, waited=waited, attempts=attempts, detail=""
        )

    next_report_due = report_every_val

    while True:
        waited = max(0.0, now() - start)
        if timeout_val is not None and waited >= timeout_val:
            break

        sleep(poll_val)
        waited = max(0.0, now() - start)

        if timeout_val is not None and waited >= timeout_val:
            break

        if report_every_val > 0 and waited >= next_report_due:
            held_str, _ = _format_holder(holder)
            line = f"still waiting for {what}{held_str} ({int(waited)}s of {int(timeout_val)}s)"
            _say(line)
            while next_report_due <= waited:
                next_report_due += report_every_val

        attempts += 1
        done, value = try_once()
        if done:
            return WaitResult(
                ok=True, value=value, waited=waited, attempts=attempts, detail=""
            )

    held_str, _ = _format_holder(holder)
    detail = f"timed out waiting for {what}{held_str} after {int(waited)}s (bound {int(timeout_val)}s)"
    return WaitResult(
        ok=False, value=None, waited=waited, attempts=attempts, detail=detail
    )

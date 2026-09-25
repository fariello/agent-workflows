"""Nested-`aw` refusal text capture and the agy probe argv (run-20260925T174509Z-636951 defects).

D2: `driver_finalize` / `driver_begin` recorded `(stderr or stdout)`, so an advisory stderr notice
from `checkout_pin` displaced the real refusal, which `aw` prints on STDOUT. `nested_aw_message`
keeps both streams and drops only that notice.

D3: the orchestrator coverage probe passed agy `--print-timeout 180`; agy parses a Go duration and
rejects a unitless value by printing its usage, so every agy run recorded `could-not-ask` with the
detail `update  Update CLI` (the last usage line) and warned past the gate.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

from agent_workflows import checkout_pin, runner_shared

NOTICE = (
    "aw: invoked in checkout /x/lane but imported agent_workflows from /x; "
    "re-running with /x/lane's package (set AW_NO_REEXEC=1 to disable)"
)
REFUSAL = (
    "error: AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes"
)


def test_refusal_on_stdout_survives_notice_on_stderr() -> None:
    msg = runner_shared.nested_aw_message(REFUSAL + "\n", NOTICE + "\n")
    assert msg == REFUSAL


def test_both_streams_kept_stderr_first() -> None:
    assert runner_shared.nested_aw_message("out", "err") == "err\nout"


def test_notice_alone_is_kept_rather_than_empty() -> None:
    assert runner_shared.nested_aw_message("", NOTICE) == NOTICE


def test_empty_streams() -> None:
    assert runner_shared.nested_aw_message(None, None) == ""


def test_notice_does_not_break_stale_receipt_retry_classification() -> None:
    from agent_workflows import ipd_lifecycle

    stale = f"{runner_shared.RETRYABLE_STALE_RECEIPT_SUMMARY}\n  {ipd_lifecycle.FINDING_RECEIPT_STALE}"
    assert runner_shared.finalize_refusal_is_retryable(stale)
    with_notice = runner_shared.nested_aw_message(stale, NOTICE)
    assert runner_shared.finalize_refusal_is_retryable(with_notice)


def test_notice_prefix_matches_checkout_pin_source() -> None:
    src = inspect.getsource(checkout_pin.check_and_reexec)
    literals = re.findall(r'f"(aw: invoked in checkout )\{', src)
    assert (
        literals
    ), "checkout_pin notice wording changed; update _CHECKOUT_PIN_NOTICE_PREFIX"
    assert all(lit == runner_shared._CHECKOUT_PIN_NOTICE_PREFIX for lit in literals)


def test_agy_probe_print_timeout_carries_a_duration_unit() -> None:
    argv = runner_shared.probe_argv(
        {"options": {"agy": "agy"}}, host="agy", prompt="p", repo=str(Path.cwd())
    )
    value = argv[argv.index("--print-timeout") + 1]
    assert re.fullmatch(r"\d+(ns|us|ms|s|m|h)", value), value

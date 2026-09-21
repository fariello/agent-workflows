"""Tests for formatted exit summary table and runner signal/exit handling."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_workflows.render_stream import (
    Palette,
    StreamTracker,
    _strip_ansi,
    format_duration,
    render_run_summary_table,
)
from agent_workflows import oc_runipd
from agent_workflows import agy_runipd


def test_format_duration() -> None:
    assert format_duration(None) == "0s"
    assert format_duration(-5) == "0s"
    assert format_duration(0) == "0s"
    assert format_duration(12) == "12s"
    assert format_duration(59) == "59s"
    assert format_duration(60) == "1m 00s"
    assert format_duration(84) == "1m 24s"
    assert format_duration(3600) == "1h 00m 00s"
    assert format_duration(3725) == "1h 02m 05s"
    assert format_duration(86400) == "1d 0h 00m 00s"
    assert format_duration(86400 + 3 * 3600 + 7 * 60 + 56) == "1d 3h 07m 56s"


def test_render_run_summary_table_borders_and_alignment() -> None:
    sample_state = {
        "run_id": "run-20260830T185011Z-2301181",
        "repo": "/tmp/test-repo",
        "created_at": "2026-08-30T18:50:11+00:00",
        "updated_at": "2026-08-30T18:54:23+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "jb6vys",
                "setid": "sessrot",
                "action": "execute",
                "status": "executed",
                "verification_status": "pass",
                "attempts": [
                    {
                        "number": 1,
                        "started_at": "2026-08-30T18:50:12+00:00",
                        "ended_at": "2026-08-30T18:51:36+00:00",
                        "cost": 4.12,
                        "tokens": {
                            "total": 3200000,
                            "input": 45200,
                            "output": 32100,
                            "cache": 3100000,
                        },
                        "session_id": "ses_01",
                    }
                ],
            },
            {
                "position": 2,
                "id6": "bmh754",
                "setid": "detrun",
                "action": "review",
                "status": "reviewed",
                "verification_status": None,
                "attempts": [
                    {
                        "number": 1,
                        "started_at": "2026-08-30T18:51:37+00:00",
                        "ended_at": "2026-08-30T18:52:10+00:00",
                        "cost": 1.50,
                        "tokens": {
                            "total": 1800000,
                            "input": 22000,
                            "output": 15200,
                            "cache": 1700000,
                        },
                        "session_id": "ses_02",
                    }
                ],
            },
            {
                "position": 3,
                "id6": "a54m79",
                "setid": "detrun",
                "action": "execute",
                "status": "interrupted",
                "verification_status": None,
                "attempts": [
                    {
                        "number": 1,
                        "started_at": "2026-08-30T18:52:11+00:00",
                        "ended_at": "2026-08-30T18:52:21+00:00",
                        "cost": 0.85,
                        "tokens": {
                            "total": 1200000,
                            "input": 18000,
                            "output": 12000,
                            "cache": 1150000,
                        },
                        "session_id": "ses_03",
                    }
                ],
            },
            {
                "position": 4,
                "id6": "kaygwo",
                "setid": "detrun",
                "action": "execute",
                "status": "queued",
                "verification_status": None,
                "attempts": [],
            },
        ],
    }

    output = render_run_summary_table(sample_state, pal=Palette(False))
    lines = output.splitlines()

    border_lines = [
        lines[0],
        lines[4],
        lines[6],
        lines[11],
        lines[13],
    ]
    border_lens = [len(b) for b in border_lines]
    assert len(set(border_lens)) == 1, f"Border lengths differ: {border_lens}"
    table_width = border_lens[0]

    for idx, line in enumerate(lines[:14]):
        clean_line = _strip_ansi(line)
        assert (
            len(clean_line) == table_width
        ), f"Line {idx} width {len(clean_line)} != {table_width}"

    assert "AW RUN SUMMARY: run-20260830T185011Z-2301181" in output
    assert "jb6vys" in output
    assert "bmh754" in output
    assert "a54m79" in output
    assert "kaygwo" in output
    assert ".12" in output
    assert ".50" in output
    assert ".47" in output


def test_render_run_summary_table_ascii_borders() -> None:
    sample_state = {
        "run_id": "run-ascii-test",
        "queue": [
            {
                "position": 1,
                "id6": "item01",
                "setid": "set1",
                "action": "execute",
                "status": "executed",
                "verification_status": "pass",
                "attempts": [],
            }
        ],
    }
    output = render_run_summary_table(
        sample_state, use_unicode=False, pal=Palette(False)
    )
    lines = output.splitlines()
    assert lines[0].startswith("+")
    assert lines[0].endswith("+")
    assert "|" in lines[1]


def test_render_run_summary_table_diagnostics() -> None:
    sample_state = {
        "run_id": "run-diag-test",
        "queue": [
            {
                "position": 1,
                "id6": "dep001",
                "setid": "myset",
                "action": "execute",
                "status": "dependency-blocked",
                "unsatisfied_dependencies": ["base01"],
                "unsatisfied_dependency_reasons": {"base01": "spec approval required"},
            },
            {
                "position": 2,
                "id6": "err002",
                "setid": "myset",
                "action": "execute",
                "status": "failed-safely",
                "driver_error": "merge conflict in tests/test_main.py",
            },
            {
                "position": 3,
                "id6": "int003",
                "setid": "myset",
                "action": "execute",
                "status": "interrupted",
                "interrupt_reason": "stall_timeout",
            },
        ],
    }
    output = render_run_summary_table(sample_state, pal=Palette(False))
    assert "Diagnostics / Blocked Items:" in output
    assert "• dep001: dependency-blocked (base01 (spec approval required))" in output
    assert "• err002: failed-safely (merge conflict in tests/test_main.py)" in output
    assert "• int003: interrupted (stall_timeout)" in output


def test_render_run_summary_table_tracker_override() -> None:
    sample_state = {
        "run_id": "run-track-test",
        "queue": [
            {
                "position": 1,
                "id6": "item01",
                "setid": "myset",
                "action": "execute",
                "status": "executed",
                "attempts": [
                    {
                        "started_at": "2026-08-30T10:00:00+00:00",
                        "ended_at": "2026-08-30T10:01:00+00:00",
                        "cost": 1.0,
                        "tokens": {
                            "total": 1000,
                            "input": 500,
                            "output": 500,
                            "cache": 0,
                        },
                    }
                ],
            }
        ],
    }
    tracker = StreamTracker()
    tracker.cost = 5.50
    tracker.input_tokens = 20000
    tracker.output_tokens = 10000
    tracker.cache_tokens = 50000

    output = render_run_summary_table(sample_state, tracker=tracker, pal=Palette(False))
    assert ".50" in output
    assert "80k" in output


def test_oc_runipd_print_status_renders_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "test_run"
    run_dir.mkdir()
    state = {
        "run_id": "run-test-oc-status",
        "repo": str(tmp_path),
        "created_at": "2026-08-30T10:00:00+00:00",
        "updated_at": "2026-08-30T10:05:00+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "test01",
                "setid": "set1",
                "action": "execute",
                "status": "executed",
                "verification_status": "pass",
                "attempts": [],
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    oc_runipd.print_status(run_dir)
    val = buf.getvalue()

    assert "AW RUN SUMMARY: run-test-oc-status" in val
    assert "test01" in val


def test_agy_runipd_print_status_renders_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "test_run_agy"
    run_dir.mkdir()
    state = {
        "run_id": "run-test-agy-status",
        "repo": str(tmp_path),
        "created_at": "2026-08-30T10:00:00+00:00",
        "updated_at": "2026-08-30T10:05:00+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "agy001",
                "setid": "agyset",
                "action": "review",
                "status": "reviewed",
                "verification_status": None,
                "attempts": [],
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    agy_runipd.print_status(run_dir)
    val = buf.getvalue()

    assert "AW RUN SUMMARY: run-test-agy-status" in val
    assert "agy001" in val


def test_oc_runipd_main_sigterm_and_sigint_handling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "test_run_sig"
    run_dir.mkdir()
    state = {
        "run_id": "run-sig-test",
        "repo": str(tmp_path),
        "created_at": "2026-08-30T10:00:00+00:00",
        "updated_at": "2026-08-30T10:01:00+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "sig001",
                "setid": "sigset",
                "action": "execute",
                "status": "interrupted",
                "attempts": [],
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    # Test SIGTERM exit 143
    buf = io.StringIO()
    err_buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    monkeypatch.setattr("sys.stderr", err_buf)

    with patch.object(
        oc_runipd, "run_queue", side_effect=KeyboardInterrupt("Terminated by SIGTERM")
    ), patch.object(oc_runipd, "locked_run"):
        rc = oc_runipd.main(["resume", "--repo", str(tmp_path), str(run_dir)])
        assert rc == 143
        val = buf.getvalue()
        assert "AW RUN SUMMARY: run-sig-test" in val
        assert "TERMINATED (SIGTERM)" in val

    # Test SIGINT exit 130
    buf = io.StringIO()
    err_buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    monkeypatch.setattr("sys.stderr", err_buf)

    with patch.object(
        oc_runipd, "run_queue", side_effect=KeyboardInterrupt("Ctrl-C")
    ), patch.object(oc_runipd, "locked_run"):
        rc = oc_runipd.main(["resume", "--repo", str(tmp_path), str(run_dir)])
        assert rc == 130
        val = buf.getvalue()
        assert "AW RUN SUMMARY: run-sig-test" in val
        assert "INTERRUPTED (SIGINT / Ctrl-C)" in val


def test_agy_runipd_main_sigterm_and_sigint_handling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = tmp_path / "test_run_agy_sig"
    run_dir.mkdir()
    state = {
        "run_id": "run-agy-sig-test",
        "repo": str(tmp_path),
        "created_at": "2026-08-30T10:00:00+00:00",
        "updated_at": "2026-08-30T10:01:00+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "agysig",
                "setid": "sigset",
                "action": "execute",
                "status": "interrupted",
                "attempts": [],
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    # Test SIGTERM exit 143
    buf = io.StringIO()
    err_buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    monkeypatch.setattr("sys.stderr", err_buf)

    with patch.object(
        agy_runipd, "run_queue", side_effect=KeyboardInterrupt("Terminated by SIGTERM")
    ), patch.object(agy_runipd, "locked_run"):
        rc = agy_runipd.main(["resume", "--repo", str(tmp_path), str(run_dir)])
        assert rc == 143
        val = buf.getvalue()
        assert "AW RUN SUMMARY: run-agy-sig-test" in val
        assert "TERMINATED (SIGTERM)" in val

    # Test SIGINT exit 130
    buf = io.StringIO()
    err_buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    monkeypatch.setattr("sys.stderr", err_buf)

    with patch.object(
        agy_runipd, "run_queue", side_effect=KeyboardInterrupt("Ctrl-C")
    ), patch.object(agy_runipd, "locked_run"):
        rc = agy_runipd.main(["resume", "--repo", str(tmp_path), str(run_dir)])
        assert rc == 130
        val = buf.getvalue()
        assert "AW RUN SUMMARY: run-agy-sig-test" in val
        assert "INTERRUPTED (SIGINT / Ctrl-C)" in val


def test_resume_statusbar_starts_from_resume_time(tmp_path: Path) -> None:
    """Verify resume invocation sets _invocation_start_mono so statusbar does not count old time."""
    import time

    # Created 10 hours ago
    created_at = "2026-08-30T00:00:00+00:00"
    state = {
        "run_id": "run-resume-time-test",
        "repo": str(tmp_path),
        "created_at": created_at,
        "updated_at": "2026-08-30T00:05:00+00:00",
        "queue": [
            {
                "position": 1,
                "id6": "item01",
                "setid": "testset",
                "action": "execute",
                "status": "queued",
                "attempts": [],
            }
        ],
    }
    run_dir = tmp_path / "run-resume-time-test"
    run_dir.mkdir(parents=True)
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    t_before = time.monotonic()
    # In run_queue, state["_invocation_start_mono"] is populated with current monotonic time
    captured_state = {}
    with patch.object(oc_runipd, "execute_item") as mock_exec:

        def fake_exec(r_dir, st, item, *args, **kwargs):
            captured_state["_invocation_start_mono"] = st.get("_invocation_start_mono")
            st["queue"][0]["status"] = "executed"
            (r_dir / "state.json").write_text(json.dumps(st), encoding="utf-8")

        mock_exec.side_effect = fake_exec
        rc = oc_runipd.run_queue(run_dir, retry_incomplete=False)
        assert rc == 0
        assert captured_state.get("_invocation_start_mono") is not None
        assert captured_state["_invocation_start_mono"] >= t_before


# ======================================================================================
# ys1dor: A RUN WHOSE WORK NEVER LANDED IS REPORTED AS `STRANDED`, IN RED, FROM THE RUN'S
# OWN RECORD.
#
# THE MEASURED DEFECT, from `run-20260908T140845Z-2489897`: a single-item run whose entire
# product was stranded printed `Outcome: COMPLETED   Spend: $32.83` at
# `Progress: 1/1 [##########] 100% (1 substantially-complete)` while NOTHING had been
# integrated; the work sat on `aw/lane/03ie04_attempt2` and the maintainer found it only by
# auditing `git worktree list` by hand. Eleven lanes were stranded that way on one unrelated
# red test, and plan `03ie04` was paid for twice ($16.59, then $32.83).
#
# THE MECHANISM WAS A MISSING QUESTION, not a wrong answer: the outcome was derived purely
# from per-item STATUS, and `substantially-complete` sits inside the success tuple, so a
# stranded run and a landed one were indistinguishable to it. The verdict, its reason and the
# recovery route were all recorded at the time and NO report read any of them.
#
# THE RULE THESE TESTS PIN, which is the whole reason this plan superseded `xtklpd`: the
# verdict comes from the run's OWN RECORD and never from the filesystem. `xtklpd` derived it
# from a filesystem audit, and its review measured the consequence - re-rendering a run that
# had since been recovered by hand reported `COMPLETED` again, so the summary silently
# REWROTE HISTORY.
# ======================================================================================

STRANDED_FIXTURE = (
    Path(__file__).parent / "fixtures" / "run_summary" / "stranded-run-state.json"
)


def _outcome_line(state: dict, *, color: bool = False) -> str:
    """The rendered `Outcome:` line, with ANSI intact when `color` is set."""
    rendered = render_run_summary_table(state, pal=Palette(color))
    for line in rendered.splitlines():
        if "Outcome:" in line:
            return line
    raise AssertionError("no Outcome line was rendered")


def _item(**overrides: object) -> dict:
    """One queue entry in the shape a real run persists (the measured item's field set)."""
    item: dict = {
        "position": 1,
        "id6": "03ie04",
        "setid": "depreview",
        "action": "execute",
        "status": "substantially-complete",
        "verification_status": "-",
        "attempts": [{"number": 1}],
    }
    item.update(overrides)
    return item


def _state(*items: dict, **extra: object) -> dict:
    state: dict = {"run_id": "run-ys1dor-test", "queue": list(items)}
    state.update(extra)
    return state


def _stranded_item(**overrides: object) -> dict:
    """The measured stranded shape: a SUCCESS-TUPLE status with a REFUSING signal."""
    base: dict = {
        "integration_signal": "suite-failed",
        "preserved_branch": "aw/lane/03ie04_attempt2",
        "preserved_worktree": "/home/user/repo/.aw/worktrees/03ie04_attempt2",
        "attempts": [
            {
                "number": 1,
                "integration_signal": "suite-failed",
                "integration_detail": (
                    "no verifier ran (validation off) and the driver-run suite did not "
                    "pass: suite FAILED with exit 1 in /home/user/repo (no summary "
                    "line parsed)"
                ),
            }
        ],
    }
    base.update(overrides)
    return _item(**base)


def test_a_stranded_run_is_not_reported_completed() -> None:
    """THE FALSIFIABLE CORE: the measured shape must not read as success.

    This is the case NOTHING else catches. The item kept a SUCCESS-TUPLE status
    (`substantially-complete`, which is legitimate and load-bearing: `reconcile_disposition`
    downgrades a claimed `executed` to it as an anti-fabrication guard) while its own
    `integration_signal` recorded that integration was REFUSED.
    """
    outcome = _strip_ansi(_outcome_line(_state(_stranded_item())))
    assert "COMPLETED" not in outcome, (
        "a run whose own record says integration was REFUSED must not report COMPLETED; "
        f"got {outcome!r}"
    )
    assert "STRANDED" in outcome


def test_a_landed_run_still_reports_completed_in_green() -> None:
    """The honest success case is untouched, including its color."""
    item = _item(status="executed", integration_signal="driver-run-suite")
    line = _outcome_line(_state(item), color=True)
    assert "COMPLETED" in _strip_ansi(line)
    assert "\033[32mCOMPLETED" in line, f"a landed run must stay GREEN; got {line!r}"


def test_a_review_only_run_with_no_integration_signal_key_reports_completed() -> None:
    """THE MOST LIKELY FALSE POSITIVE: absent must not read as refusing.

    A review-only run integrates nothing by design, so its item carries NO
    `integration_signal` key at all. Keying on falsiness rather than on PRESENCE would report
    every review run as stranded.
    """
    item = _item(action="review", status="reviewed")
    assert "integration_signal" not in item
    assert "COMPLETED" in _strip_ansi(_outcome_line(_state(item)))


def test_an_explicitly_empty_signal_is_treated_as_absent_not_as_a_refusal() -> None:
    """A present-but-empty value carries no verdict; inventing one would be a false alarm."""
    for empty in ("", None):
        item = _item(status="executed", integration_signal=empty)
        assert "COMPLETED" in _strip_ansi(
            _outcome_line(_state(item))
        ), f"integration_signal={empty!r} must behave as absent"


def test_a_partially_stranded_run_reports_stranded() -> None:
    """OQ-02, resolved as STRANDED: a partial strand is still a strand.

    A run where one item landed and one did not is a run with unintegrated work sitting in a
    lane, which is the fact an operator must act on. This precedence matches the `FAILED`
    branch's established shape in this same function (it fires on `any(...)`, not on all), and
    the recovery section names WHICH items are affected so the body still distinguishes
    "everything" from "one of two".
    """
    landed = _item(
        position=1, id6="aaaaaa", status="executed", integration_signal="verifier"
    )
    stranded = _stranded_item(position=2, id6="bbbbbb")
    outcome = _strip_ansi(_outcome_line(_state(landed, stranded)))
    assert "STRANDED" in outcome
    assert "COMPLETED" not in outcome


def test_an_unknown_future_signal_reads_as_a_refusal_not_as_success() -> None:
    """THE PROPERTY THE DESIGN EXISTS TO GUARANTEE, and why EARNED is the enumerated set.

    The renderer tests for the two EARNED values and treats every other non-empty signal as a
    refusal, so a signal added later fails SAFE by construction. Enumerating the three REFUSAL
    reasons instead would make each new signal read as landed until somebody remembered to
    extend the list - the same miss class as the `integration-blocked` allowlist that once
    rendered nothing at all.
    """
    item = _stranded_item(integration_signal="some-refusal-invented-in-2027")
    assert "STRANDED" in _strip_ansi(_outcome_line(_state(item)))


def test_an_integration_blocked_status_still_reports_failed() -> None:
    """THE REGRESSION THIS CHANGE COULD HAVE SHIPPED, so it gets its own test.

    The outcome block ALREADY had a `FAILED` branch firing on `("failed-safely",
    "integration-blocked", "merge-conflict")`, and an `integration-blocked` item ALSO carries a
    refusing `integration_signal`. An implementation that tested the signal BEFORE the status
    would have RELABELLED that existing outcome to `STRANDED`: a regression dressed as the
    feature. The landing question is therefore asked LAST, inside the success branch only.
    """
    item = _stranded_item(status="integration-blocked")
    outcome = _strip_ansi(_outcome_line(_state(item)))
    assert (
        "FAILED" in outcome
    ), f"expected the pre-existing FAILED word; got {outcome!r}"
    assert "STRANDED" not in outcome


def test_an_exit_reason_still_short_circuits_the_whole_outcome_block() -> None:
    """The `exit_reason` passthrough is the FIRST branch and must keep winning.

    A stranded run that ALSO exited on a signal keeps the exit wording: that is what the
    operator pressed Ctrl-C about, and hijacking it would hide the interruption.
    """
    line = _strip_ansi(
        render_run_summary_table(
            _state(_stranded_item()),
            pal=Palette(False),
            exit_reason="INTERRUPTED (SIGINT / Ctrl-C)",
        ).splitlines()[2]
    )
    assert "INTERRUPTED (SIGINT / Ctrl-C)" in line
    assert "STRANDED" not in line


def test_a_refusal_released_by_the_agents_answer_is_not_stranded() -> None:
    """gatewire-01's rung, which the measured incident predates and which must not false-alarm.

    When an agent adjudicates a failing suite and its answer RELEASES the gate, the run
    integrates and the item reaches `executed`, yet `integration_signal` KEEPS its refusing
    value because it records what the SUITE said. Only `integration_released_by_answer` records
    the override, so ignoring it would report a LANDED run as stranded.
    """
    item = _stranded_item(
        status="executed",
        integration_released_by_answer="not-mine",
    )
    assert "COMPLETED" in _strip_ansi(_outcome_line(_state(item)))


def test_the_stranded_outcome_is_rendered_in_red_with_an_explicit_branch() -> None:
    """E-02: proven by the RAW escape sequence, not by a claim.

    The color selection is a set of SUBSTRING tests whose else-branch is CYAN, so an unhandled
    word looks deliberate while being wrong. `STRANDED` contains no `FAIL`, no `INTERRUPT` and
    no `STOP`, so without a branch of its own it would render cyan rather than red.
    """
    line = _outcome_line(_state(_stranded_item()), color=True)
    assert "\033[31mSTRANDED\033[0m" in line, f"expected RED STRANDED; got {line!r}"
    assert (
        "\033[36mSTRANDED" not in line
    ), "STRANDED must not fall through to the cyan else-branch"

    import inspect

    src = inspect.getsource(render_run_summary_table)
    assert "outcome_str == STRANDED_OUTCOME" in src, (
        "the color selection must carry an EXPLICIT branch for the new word rather than "
        "relying on a substring coincidence"
    )


def test_the_stranded_word_is_distinct_from_every_pre_existing_outcome() -> None:
    """It must not be a synonym a reader skims past, nor a rename of an existing outcome."""
    from agent_workflows import render_stream

    assert render_stream.STRANDED_OUTCOME not in (
        "COMPLETED",
        "PARTIAL",
        "BLOCKED",
        "FAILED",
        "INTERRUPTED",
        "QUEUED",
    )
    # And no pre-existing condition produces it: the only assignment is the new branch.
    import inspect

    src = inspect.getsource(render_run_summary_table)
    assert src.count("outcome_str = STRANDED_OUTCOME") == 1


def test_the_recovery_section_names_the_branch_and_the_reason_and_the_next_step() -> (
    None
):
    """E-03: an alarm an operator cannot ACT on trains them to ignore it."""
    rendered = _strip_ansi(
        render_run_summary_table(_state(_stranded_item()), pal=Palette(False))
    )
    assert "STRANDED WORK - NOT IN YOUR PROJECT:" in rendered
    assert "aw/lane/03ie04_attempt2" in rendered, "the preserved branch must be named"
    assert "suite-failed" in rendered, "the refusal reason must be named"
    assert (
        "git log HEAD..aw/lane/03ie04_attempt2" in rendered
    ), "state the concrete next step"
    assert "Do NOT delete the branch" in rendered


def test_the_recovery_section_prints_NO_absolute_path() -> None:
    """THE ONE WAY THIS CHANGE COULD DO REAL HARM, measured rather than supposed.

    `preserved_worktree` is an absolute path under the maintainer's home directory, and
    `integration_detail`'s recorded text embeds the repository's absolute path too. The
    end-of-run summary is the most-copied output in the product (an operator pastes it into an
    issue, a chat, or a plan's `Observed evidence`), so a leak here is a leak everywhere.
    """
    rendered = _strip_ansi(
        render_run_summary_table(_state(_stranded_item()), pal=Palette(False))
    )
    assert (
        "/home/" not in rendered
    ), f"an absolute home path reached the render:\n{rendered}"
    assert "/home/user/repo/.aw/worktrees" not in rendered
    assert (
        "preserved_worktree" not in rendered
    ), "the worktree field must not be printed at all"
    # The useful part of the reason SURVIVES the redaction rather than the line being dropped.
    assert "the driver-run suite did not pass" in rendered


def test_the_reason_detail_is_read_from_the_ATTEMPT_and_absence_is_tolerated() -> None:
    """F-10: `integration_detail` is on the ATTEMPT, not the item.

    Measured on the real record: the item's keys include `integration_signal`,
    `preserved_branch` and `preserved_worktree` but NO `integration_detail`; both drivers write
    it onto `attempt`. An item with no attempts (or a record frozen by an older driver) must
    still render rather than raise.
    """
    from agent_workflows import render_stream

    with_attempt = _stranded_item()
    assert "integration_detail" not in with_attempt
    assert render_stream.integration_refusal_detail(with_attempt)

    no_attempts = _stranded_item(attempts=[])
    assert render_stream.integration_refusal_detail(no_attempts) is None
    rendered = _strip_ansi(
        render_run_summary_table(_state(no_attempts), pal=Palette(False))
    )
    assert (
        "STRANDED WORK" in rendered
    ), "an item with no attempts must still be reported"
    assert "aw/lane/03ie04_attempt2" in rendered


def test_an_item_with_no_preserved_branch_still_gets_an_actionable_line() -> None:
    """A refusal recorded without a branch is still a strand, and still needs a next step."""
    item = _stranded_item()
    item.pop("preserved_branch")
    rendered = _strip_ansi(render_run_summary_table(_state(item), pal=Palette(False)))
    assert "STRANDED" in rendered
    assert "no branch recorded" in rendered
    assert "aw attention" in rendered


def test_the_item_table_gains_NO_column() -> None:
    """E-03 adds a SECTION, never a table column: the column contract is unchanged.

    Compared by COLUMN SET rather than byte width, because the table already auto-sizes each
    column to its widest cell, so `substantially-complete` legitimately makes the `Status`
    column wider than `executed` does at HEAD too. The contract this pins is WHICH columns
    exist and in what order; the byte-identity of a like-for-like render is demonstrated
    against pre-change code in the plan's V-03 evidence.
    """
    landed = _item(status="executed", integration_signal="driver-run-suite")
    stranded = _stranded_item()
    expected = [
        "Run",
        "Pos",
        "ID6",
        "Set",
        "Action",
        "Status",
        "Verify",
        "Duration",
        "Spend",
        "Tok tot",
        "Tok in",
        "Tok out",
        "Tok cache",
    ]
    for state in (_state(landed), _state(stranded)):
        header = render_run_summary_table(state, pal=Palette(False)).splitlines()[5]
        cells = [c.strip() for c in header.strip("│").split("│")]
        assert cells == expected, f"the table's column contract changed: {cells}"

    # The stranded render differs from the clean one ONLY by appended lines: every line of the
    # box itself is unchanged in COUNT, so nothing was inserted into the table.
    clean = render_run_summary_table(_state(landed), pal=Palette(False)).splitlines()
    strand = render_run_summary_table(_state(stranded), pal=Palette(False)).splitlines()
    assert len(strand) > len(clean), "the stranded render must append a section"
    assert len([ln for ln in clean if ln.startswith("│")]) == len(
        [ln for ln in strand if ln.startswith("│")]
    ), "a row or banner line was added to the box itself"


def test_the_earned_signal_constants_match_the_runners_definitions() -> None:
    """The renderer MIRRORS two producer constants; this is what stops the copy going stale.

    `render_stream` is a LEAF: it imports no first-party module, and `runner_shared` imports
    FROM it at module level, so reading `INTEGRATION_EARNED_BY_*` from its home would be a
    circular import. The copy is therefore deliberate, and cross-checked here instead.
    """
    from agent_workflows import render_stream
    from agent_workflows import runner_shared

    assert render_stream.INTEGRATION_EARNED_SIGNALS == frozenset(
        {
            runner_shared.INTEGRATION_EARNED_BY_VERIFIER,
            runner_shared.INTEGRATION_EARNED_BY_SUITE,
        }
    ), (
        "the renderer's mirrored EARNED signals drifted from the producer's; update "
        "INTEGRATION_EARNED_SIGNALS (and note that an unknown value reads as a REFUSAL)"
    )
    # And the runners' REFUSAL values are all on the refusal side, by construction rather than
    # by enumeration.
    for refused in (
        runner_shared.INTEGRATION_REFUSED_VERIFIER_DECLINED,
        runner_shared.INTEGRATION_REFUSED_SUITE_FAILED,
        runner_shared.INTEGRATION_REFUSED_NO_SIGNAL,
    ):
        assert render_stream.integration_was_refused(
            {"integration_signal": refused}
        ), f"{refused!r} must read as a refusal"


def test_the_stranded_word_is_the_same_one_the_cross_tree_view_uses() -> None:
    """One condition, one vocabulary: `aw attention` and the run summary must not diverge."""
    from agent_workflows import render_stream
    from agent_workflows import runner_shared

    assert render_stream.STRANDED_OUTCOME == runner_shared.LANE_STRANDED


def test_the_landing_question_reads_NO_filesystem() -> None:
    """E-01/E-05: the verdict must be derivable from `state.json` ALONE.

    This is the property that makes a run summary a statement about what THAT RUN DID. The
    rejected design derived it from a filesystem audit, and re-rendering a since-recovered run
    reported `COMPLETED` again: the summary silently rewrote history.
    """
    import ast
    import inspect
    import textwrap

    from agent_workflows import render_stream

    for fn in (
        render_stream.integration_was_refused,
        render_stream.integration_refusal_detail,
        render_stream.format_stranded_work_section,
    ):
        tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
        names = {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        } | {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        for forbidden in (
            "Path",
            "exists",
            "is_file",
            "is_dir",
            "iterdir",
            "glob",
            "rglob",
            "read_text",
            "open",
            "listdir",
            "subprocess",
        ):
            assert forbidden not in names, (
                f"{fn.__name__} reads the filesystem ({forbidden!r}); the landing verdict must "
                f"come from the run's own record, or re-rendering an old run will rewrite history"
            )


def test_render_stream_still_imports_no_first_party_module() -> None:
    """No import cycle was introduced: this module stays a stdlib-only LEAF.

    Both runners and `runner_shared` import FROM it, so a first-party import here would invert
    the dependency. That is why the EARNED constants are mirrored rather than imported.
    """
    import ast
    from pathlib import Path as _Path

    from agent_workflows import render_stream

    tree = ast.parse(_Path(render_stream.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"relative import added: {ast.dump(node)}"
            assert not (node.module or "").startswith(
                "agent_workflows"
            ), f"first-party import added: {node.module}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(
                    "agent_workflows"
                ), f"first-party import added: {alias.name}"


def test_the_recovered_run_fixture_STILL_reports_stranded() -> None:
    """E-05: THE SHARPEST TEST OF THE DIFFERENCE between this design and the rejected one.

    `run-20260908T140845Z-2489897` (plan `03ie04`) was stranded, and has SINCE been recovered
    by hand: `03ie04` now sits in `.aw/records/plans/executed/`. A filesystem-derived summary
    therefore reports it CLEAN today - measured on `xtklpd`'s approach, which is why that plan
    was superseded rather than revised. Because the verdict here comes from the run's own
    durable record, re-rendering it says STRANDED forever, which is what a historical report
    must do.

    ASSERTED AGAINST A COMMITTED REDACTED FIXTURE, not the live record: `.aw/records/runs/` is
    GITIGNORED, so a test bound to it would fail in every other checkout and in every clean
    worktree.
    """
    state = json.loads(STRANDED_FIXTURE.read_text(encoding="utf-8"))
    rendered = render_run_summary_table(state, pal=Palette(False))
    plain = _strip_ansi(rendered)
    assert "STRANDED" in plain
    assert "COMPLETED" not in plain
    # The status that misled the outcome is still shown honestly in the table.
    assert "substantially-complete" in plain
    # The recovery route is present and leaks nothing.
    assert "aw/lane/03ie04_attempt2" in plain
    assert "/home/" not in plain, f"the fixture's absolute paths leaked:\n{plain}"


def test_the_committed_fixture_is_tracked_and_not_gitignored() -> None:
    """Guards the F-13 trap: a fixture under a gitignored path would pass only here."""
    import subprocess

    assert STRANDED_FIXTURE.is_file()
    rc = subprocess.run(
        ["git", "check-ignore", "-q", str(STRANDED_FIXTURE)],
        capture_output=True,
    ).returncode
    assert rc != 0, (
        "the stranded fixture is GITIGNORED, so this suite would pass only in this checkout; "
        "commit it somewhere tracked"
    )

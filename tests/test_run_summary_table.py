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

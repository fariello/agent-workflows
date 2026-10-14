"""Tests for aw runs empty-state machine records under --agent and --json.

Plan t76qdk / Backlog l5dq92:
Ensure aw runs --agent and aw runs list --agent emit an aw.agent/v1 summary record
in empty repositories or when filters exclude all runs, while --json output remains
the bare {"runs": []} payload.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tempfile

import pytest

from agent_workflows import agent_schema, cli


SPELLINGS = [
    ["runs"],
    ["runs", "list"],
]


def _run_viewer(
    root: Path, spelling: list[str], argv: list[str]
) -> tuple[str, str, int]:
    """Invoke runs command through the real CLI entry point."""
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main([*spelling, "--dir", str(root), *argv])
    except SystemExit as exc:
        rc = int(exc.code or 0)
    return out.getvalue(), err.getvalue(), rc


@pytest.mark.parametrize("spelling", SPELLINGS, ids=lambda s: " ".join(s))
def test_case_a_empty_repo_agent_summary(spelling: list[str]) -> None:
    """Case (a): --agent prints one valid summary record at exit 0 with clean outcome and zero counts."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        out, err, rc = _run_viewer(root, spelling, ["--agent"])
        assert rc == 0, f"Expected rc 0, got {rc}. stderr: {err}"
        lines = [line for line in out.splitlines() if line.strip()]
        assert len(lines) == 1, f"Expected exactly one non-blank line, got: {lines}"
        record = json.loads(lines[0])
        errors = agent_schema.validate_agent_record(record)
        assert errors == [], f"Validation errors: {errors}"
        assert record.get("kind") == "summary"
        assert record.get("outcome") == "clean"
        assert record.get("total") == 0
        assert record.get("emitted") == 0
        assert record.get("omitted") == 0
        assert record.get("complete") is True
        assert record.get("next") is None
        assert record.get("filters") == {}
        assert record.get("exit") == rc == 0


@pytest.mark.parametrize("spelling", SPELLINGS, ids=lambda s: " ".join(s))
def test_case_b_empty_repo_agent_with_filter(spelling: list[str]) -> None:
    """Case (b): --agent with filters carries filters dict, next broadening query, and exit parity."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        out, err, rc = _run_viewer(
            root, spelling, ["--agent", "--status", "nosuchstatus"]
        )
        assert rc == 0, f"Expected rc 0, got {rc}. stderr: {err}"
        lines = [line for line in out.splitlines() if line.strip()]
        assert len(lines) == 1, f"Expected exactly one non-blank line, got: {lines}"
        record = json.loads(lines[0])
        errors = agent_schema.validate_agent_record(record)
        assert errors == [], f"Validation errors: {errors}"
        assert record.get("kind") == "summary"
        assert record.get("outcome") == "clean"
        assert record.get("total") == 0
        assert record.get("emitted") == 0
        assert record.get("omitted") == 0
        assert record.get("complete") is True
        assert record.get("filters") == {"status": "nosuchstatus"}
        assert record.get("next") == "aw runs"
        assert record.get("exit") == rc == 0


@pytest.mark.parametrize("spelling", SPELLINGS, ids=lambda s: " ".join(s))
def test_case_c_empty_repo_json_unchanged(spelling: list[str]) -> None:
    """Case (c): --json output parses to exactly {'runs': []}."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        out, err, rc = _run_viewer(root, spelling, ["--json"])
        assert rc == 0, f"Expected rc 0, got {rc}. stderr: {err}"
        data = json.loads(out)
        assert data == {"runs": []}


def test_case_d_spellings_produce_byte_identical_agent_output() -> None:
    """Case (d): both spellings produce byte-identical --agent output."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        out_bare, err_bare, rc_bare = _run_viewer(root, ["runs"], ["--agent"])
        out_list, err_list, rc_list = _run_viewer(root, ["runs", "list"], ["--agent"])
        assert rc_bare == 0
        assert rc_list == 0
        assert out_bare == out_list
        # Ensure the byte-identical output is the valid summary record, not pre-fix bare dict
        record = json.loads(out_bare.strip())
        assert record.get("kind") == "summary"
        assert agent_schema.validate_agent_record(record) == []

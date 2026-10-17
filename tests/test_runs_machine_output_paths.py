"""Behavioral tests for `aw runs` machine output and repo-relative ledger paths (IPD lpvcln).

`aw runs decisions` / `aw runs questions` must emit ONE parseable JSON object under `--agent` and
`--json` (backlog hbok5d, F-07), and `aw runs evidence` / `verify-ledger` / `show` plus the shared
not-a-ledger refusal must report the ledger as a repo-relative path in every mode (F-08), so the
machine surface is parseable and sanitizer-clean. Every case drives the real CLI in a subprocess
against an isolated `tmp_path` repo and asserts on stdout, parsed JSON, and exit codes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_workflows import set_records
from tests.conformance_matrix import (
    LEDGER_FIXTURE_RUN_ID,
    run_cli,
    seed_ledger_fixture,
)

PROJECTIONS = {
    "decisions": (set_records.DECISIONS_FILE, "_No autonomous decisions recorded._"),
    "questions": (set_records.OPEN_QUESTIONS_FILE, "_No unresolved questions._"),
}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return seed_ledger_fixture(tmp_path)


def _parse_machine(stdout: str, mode: str) -> dict:
    text = stdout.strip()
    if mode == "--agent":
        lines = [ln for ln in text.splitlines() if ln.strip()]
        assert len(lines) == 1, f"--agent must emit one compact line, got {stdout!r}"
    data = json.loads(text)
    assert isinstance(data, dict), f"machine stdout is not a JSON object: {stdout!r}"
    return data


def _assert_relative(value: str, root: Path) -> None:
    assert value, "path must be non-empty"
    assert not Path(value).is_absolute(), f"path is absolute: {value!r}"
    assert str(root.resolve()) not in value


# ---- (a) projection leaves: empty projection under --json / --agent -------------------------------


@pytest.mark.parametrize("mode", ["--json", "--agent"])
@pytest.mark.parametrize("kind", sorted(PROJECTIONS))
def test_projection_machine_output_parses_empty(
    repo: Path, kind: str, mode: str
) -> None:
    _, marker = PROJECTIONS[kind]
    res = run_cli(["runs", kind, LEDGER_FIXTURE_RUN_ID, "--dir", str(repo), mode])
    assert res.returncode == 1, res.stdout + res.stderr
    data = _parse_machine(res.stdout, mode)
    assert data["ok"] is True
    assert data["projection"] == kind
    assert data["run_id"] == LEDGER_FIXTURE_RUN_ID
    assert data["empty"] is True
    assert data["entry_ids"] == []
    assert marker in data["content"]
    assert data["exit_code"] == res.returncode == 1
    _assert_relative(data["path"], repo)


# ---- (b) a non-empty decisions projection -------------------------------------------------------


def test_decisions_machine_output_lists_entry_ids(repo: Path) -> None:
    proj = set_records.run_artifacts_dir(repo, "exec-set", LEDGER_FIXTURE_RUN_ID)
    (proj / set_records.DECISIONS_FILE).write_text(
        set_records.render_decisions(
            [
                {
                    "kind": "autonomous_decision",
                    "decision_id": "D-01",
                    "selected_option": "A",
                    "confidence": "high",
                    "reversible": True,
                    "consultation_preferred": True,
                }
            ]
        ),
        encoding="utf-8",
    )
    res = run_cli(
        ["runs", "decisions", LEDGER_FIXTURE_RUN_ID, "--dir", str(repo), "--json"]
    )
    assert res.returncode == 0, res.stdout + res.stderr
    data = _parse_machine(res.stdout, "--json")
    assert data["empty"] is False
    assert data["entry_ids"] == ["D-01"]
    assert data["exit_code"] == 0


# ---- (c) a missing projection -------------------------------------------------------------------


@pytest.mark.parametrize("kind", sorted(PROJECTIONS))
def test_projection_missing_machine_error(repo: Path, kind: str) -> None:
    res = run_cli(["runs", kind, "run-0000000000", "--dir", str(repo), "--json"])
    assert res.returncode == 2, res.stdout + res.stderr
    data = _parse_machine(res.stdout, "--json")
    assert data["ok"] is False
    assert data["exit_code"] == 2
    assert data["projection"] == kind
    _assert_relative(data["path"], repo)
    assert str(repo.resolve()) not in data["error"]


def test_projection_missing_human_line_is_relative(repo: Path) -> None:
    res = run_cli(["runs", "decisions", "run-0000000000", "--dir", str(repo)])
    assert res.returncode == 2
    assert "no decisions projection found for this run" in res.stdout
    assert str(repo.resolve()) not in res.stdout


# ---- (d) human output of a present projection is the file verbatim ------------------------------


@pytest.mark.parametrize("kind", sorted(PROJECTIONS))
def test_projection_human_output_is_file_text(repo: Path, kind: str) -> None:
    filename, _ = PROJECTIONS[kind]
    proj = set_records.run_artifacts_dir(repo, "exec-set", LEDGER_FIXTURE_RUN_ID)
    expected = (proj / filename).read_text(encoding="utf-8")
    res = run_cli(["runs", kind, LEDGER_FIXTURE_RUN_ID, "--dir", str(repo)])
    assert res.returncode == 1
    assert res.stdout == expected


# ---- (e) runs evidence machine ledger key -------------------------------------------------------


@pytest.mark.parametrize("mode", ["--json", "--agent"])
def test_evidence_machine_ledger_is_relative(repo: Path, mode: str) -> None:
    res = run_cli(["runs", "evidence", LEDGER_FIXTURE_RUN_ID, "--dir", str(repo), mode])
    data = _parse_machine(res.stdout, mode)
    _assert_relative(data["ledger"], repo)
    assert data["ledger"].endswith("ledger.jsonl")


# ---- (f) runs evidence / verify-ledger human output ---------------------------------------------


def test_evidence_human_has_no_absolute_root(repo: Path) -> None:
    res = run_cli(["runs", "evidence", LEDGER_FIXTURE_RUN_ID, "--dir", str(repo)])
    assert "Evidence for " in res.stdout
    assert str(repo.resolve()) not in res.stdout


def test_verify_ledger_human_has_relative_ledger_line(repo: Path) -> None:
    res = run_cli(["runs", "verify-ledger", LEDGER_FIXTURE_RUN_ID, "--dir", str(repo)])
    assert str(repo.resolve()) not in res.stdout
    ledger_lines = [ln for ln in res.stdout.splitlines() if ln.startswith("Ledger: ")]
    assert len(ledger_lines) == 1, res.stdout
    assert ledger_lines[0].endswith("ledger.jsonl")
    _assert_relative(ledger_lines[0][len("Ledger: ") :], repo)


# ---- (g) runs show human output -----------------------------------------------------------------


def test_show_human_has_relative_ledger_line(repo: Path) -> None:
    res = run_cli(["runs", "show", LEDGER_FIXTURE_RUN_ID, "--dir", str(repo)])
    assert str(repo.resolve()) not in res.stdout
    ledger_lines = [ln for ln in res.stdout.splitlines() if ln.startswith("Ledger: ")]
    assert len(ledger_lines) == 1, res.stdout
    assert ledger_lines[0].endswith("records)")
    assert "ledger.jsonl (" in ledger_lines[0]


# ---- (h) not-a-ledger refusal machine path ------------------------------------------------------


def test_not_a_ledger_machine_path_is_relative(repo: Path) -> None:
    foreign = repo / ".aw" / "records" / "runs" / "run-feedfeed00" / "events.jsonl"
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_text(
        json.dumps({"at": "2026-10-16T00:00:00Z", "event": "run_start"}) + "\n",
        encoding="utf-8",
    )
    res = run_cli(["runs", "show", str(foreign), "--dir", str(repo), "--json"])
    assert res.returncode == 7, res.stdout + res.stderr
    data = _parse_machine(res.stdout, "--json")
    assert data["not_a_ledger"] is True
    assert data["corrupted"] is False
    _assert_relative(data["path"], repo)
    assert data["path"].endswith("events.jsonl")

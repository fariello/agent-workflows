"""Behavioral tests asserting the shape of wide-exit refusals across aw run / aw runs leaves.

Pins the protocol boundary decided in IPD u1ujw9 (backlog p7bvku):
- Under --agent, exit 1 (EXIT_INCOMPLETE) refusals are emitted as aw.agent/v1 result records
  with outcome "fail" and exit 1 (retaining legacy ok/error/exit_code keys and honoring --fields).
- Refusals with wider exit codes 3 to 7 stay bare JSON under --agent because aw.agent/v1
  cannot carry them without renumbering or breaking exit parity / the {0, 1, 2} bound.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from agent_workflows import agent_schema, runner_shared, run_ledger_store
from tests.support import run_cli


SAMPLE_WORKFLOW = {
    "id": "wf-test-wide-exit",
    "steps": [
        {"id": "S-01", "action": "step 1", "depends_on": [], "satisfies": ["R-01"]},
        {
            "id": "S-02",
            "action": "step 2",
            "depends_on": ["S-01"],
            "satisfies": ["R-02"],
        },
    ],
    "requirements": [
        {"id": "R-01", "description": "requirement 1"},
        {"id": "R-02", "description": "requirement 2"},
    ],
}


def _create_scratch_repo(path: Path) -> Path:
    (path / ".aw" / "records").mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init"],
        cwd=str(path),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return path


def _init_run(repo: Path, run_id: str = "run-0123456789abcdef") -> tuple[str, Path]:
    wf_file = repo / "workflow.json"
    wf_file.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")
    res = run_cli(
        "run",
        "init",
        "--workflow",
        str(wf_file),
        "--run-id",
        run_id,
        cwd=repo,
    )
    assert res.returncode == 0, f"run init failed: {res.stdout}\n{res.stderr}"
    ledger_path = (
        runner_shared.state_root(repo) / run_id / run_ledger_store.LEDGER_FILENAME
    )
    assert ledger_path.is_file()
    return run_id, wf_file


def test_finalize_incomplete_refusal_agent_record(tmp_path: Path) -> None:
    """(a) run finalize <run-id> --agent on freshly initialized run asserts exit 1 result record."""
    repo = _create_scratch_repo(tmp_path / "repo")
    run_id, _ = _init_run(repo)

    res = run_cli("run", "finalize", run_id, "--agent", cwd=repo)
    rc = res.returncode
    assert rc == 1

    lines = [line for line in res.stdout.strip().splitlines() if line.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])

    assert agent_schema.validate_agent_record(rec) == []
    assert rec["kind"] == "result"
    assert rec["cmd"] == "run finalize"
    assert rec["exit"] == rc == rec["exit_code"] == 1
    assert rec["outcome"] == "fail"
    assert rec["ok"] is False
    assert isinstance(rec["reasons"], list)
    assert len(rec["reasons"]) > 0
    assert rec["next"] == f"aw runs status {run_id}"


def test_finalize_incomplete_refusal_agent_fields_projection(tmp_path: Path) -> None:
    """(b) run finalize <run-id> --agent --fields cmd asserts exit 1 valid projected record."""
    repo = _create_scratch_repo(tmp_path / "repo")
    run_id, _ = _init_run(repo)

    res = run_cli("run", "finalize", run_id, "--agent", "--fields", "cmd", cwd=repo)
    rc = res.returncode
    assert rc == 1

    lines = [line for line in res.stdout.strip().splitlines() if line.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])

    assert agent_schema.validate_agent_record(rec) == []
    assert set(rec) <= agent_schema._PRESERVED_FIELDS | {"cmd"}


def test_finalize_incomplete_refusal_json_mode(tmp_path: Path) -> None:
    """(c) run finalize <run-id> --json asserts bare payload key set and no schema key."""
    repo = _create_scratch_repo(tmp_path / "repo")
    run_id, _ = _init_run(repo)

    res = run_cli("run", "finalize", run_id, "--json", cwd=repo)
    rc = res.returncode
    assert rc == 1

    payload = json.loads(res.stdout)
    assert "schema" not in payload
    assert set(payload.keys()) == {"ok", "error", "exit_code", "reasons", "predicates"}


@pytest.mark.parametrize(
    "code,case_id",
    [
        (3, "exit_3_blocked_dependency"),
        (5, "exit_5_corrupted_header"),
        (6, "exit_6_duplicate_init"),
        (7, "exit_7_not_a_ledger"),
    ],
)
def test_wider_code_refusal_stays_bare_under_agent(
    tmp_path: Path, code: int, case_id: str
) -> None:
    """(d) Wider refusal codes 3, 5, 6, 7 stay bare JSON under --agent without schema key."""
    repo = _create_scratch_repo(tmp_path / case_id)
    run_id, wf_file = _init_run(repo)

    if code == 3:
        res = run_cli("run", "start", run_id, "--step", "S-02", "--agent", cwd=repo)
    elif code == 5:
        ledger_path = (
            runner_shared.state_root(repo) / run_id / run_ledger_store.LEDGER_FILENAME
        )
        lines = ledger_path.read_text(encoding="utf-8").splitlines()
        hdr = json.loads(lines[0])
        hdr["run_id"] = "invalid_id!"
        lines[0] = json.dumps(hdr)
        ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        res = run_cli("runs", "status", run_id, "--agent", cwd=repo)
    elif code == 6:
        res = run_cli(
            "run",
            "init",
            "--workflow",
            str(wf_file),
            "--run-id",
            run_id,
            "--agent",
            cwd=repo,
        )
    elif code == 7:
        foreign = repo / "foreign.jsonl"
        foreign.write_text(json.dumps({"x": 1}) + "\n", encoding="utf-8")
        res = run_cli("runs", "status", str(foreign), "--agent", cwd=repo)
    else:
        raise ValueError(f"Unexpected exit code {code}")

    rc = res.returncode
    assert rc == code

    lines = [line for line in res.stdout.strip().splitlines() if line.strip()]
    assert len(lines) >= 1
    payload = json.loads(lines[-1])

    assert "schema" not in payload
    assert payload["ok"] is False
    assert payload["exit_code"] == rc

"""Tests for aw run init (IPD v47z9u, Set runledger).

Asserts run ledger initialization: creating a new ledger under the runs root,
writing exactly one kind: "run" header record, refusing duplicates and invalid
invocations without leaving partial state, and follow-on sequence with run
start/record and runs status/verify-ledger.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

from agent_workflows import (
    agent_schema,
    run_ledger_schema,
    run_ledger_store,
    runner_shared,
)
from tests.support import run_cli


SAMPLE_WORKFLOW = {
    "id": "wf-test-01",
    "steps": [{"id": "S-01", "action": "run tests", "depends_on": [], "satisfies": []}],
    "requirements": [{"id": "R-01", "description": "basic requirement"}],
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


def _extract_run_id(output: str) -> str:
    m = re.search(r"run-[0-9a-f]{8,}", output)
    assert m is not None, f"Could not find run-id in output: {output!r}"
    return m.group(0)


def test_case_a_init_creates_valid_ledger_record(tmp_path: Path) -> None:
    """Case (a): init creates exactly one record at state_root(repo)/<id>/ledger.jsonl,
    validate_records accepts it, its run_id equals the printed id, and its
    workflow_digest equals run_ledger_store.compute_record_hash of the workflow.
    """
    repo = _create_scratch_repo(tmp_path / "repo")
    wf_file = repo / "workflow.json"
    wf_file.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")

    res = run_cli("run", "init", "--workflow", str(wf_file), cwd=repo)
    assert res.returncode == 0, f"res failed: stdout={res.stdout}, stderr={res.stderr}"

    run_id = _extract_run_id(res.stdout)
    ledger_path = (
        runner_shared.state_root(repo) / run_id / run_ledger_store.LEDGER_FILENAME
    )
    assert ledger_path.is_file(), f"Ledger file not found at {ledger_path}"

    records = run_ledger_store.RunLedgerStore(ledger_path).read_records(verify=True)
    assert len(records) == 1, f"Expected 1 record, got {len(records)}"

    val_res = run_ledger_schema.validate_records(records)
    assert val_res.ok, f"validate_records failed: {val_res.findings}"

    rec = records[0]
    assert rec["kind"] == "run"
    assert rec["run_id"] == run_id
    expected_wf_digest = run_ledger_store.compute_record_hash(SAMPLE_WORKFLOW)
    assert rec["workflow_digest"] == expected_wf_digest


def test_case_b_follow_on_sequence(tmp_path: Path) -> None:
    """Case (b): the follow-on sequence: aw run start <id> --step S-01 --workflow wf.json exit 0,
    aw run record <id> --step S-01 --state performed --workflow wf.json exit 0,
    aw runs status <id> --workflow wf.json output contains S-01: performed (exit 1, run still incomplete),
    and aw runs verify-ledger <id> output contains Hash Chain: CLEAN (exit 1, completion UNSATISFIED
    with 'no frozen requirements defined').
    """
    repo = _create_scratch_repo(tmp_path / "repo")
    wf_file = repo / "workflow.json"
    wf_file.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")

    res_init = run_cli("run", "init", "--workflow", str(wf_file), cwd=repo)
    assert res_init.returncode == 0, f"init failed: {res_init.stderr}"
    run_id = _extract_run_id(res_init.stdout)

    res_start = run_cli(
        "run", "start", run_id, "--step", "S-01", "--workflow", str(wf_file), cwd=repo
    )
    assert (
        res_start.returncode == 0
    ), f"start failed: {res_start.stdout} {res_start.stderr}"

    res_record = run_cli(
        "run",
        "record",
        run_id,
        "--step",
        "S-01",
        "--state",
        "performed",
        "--workflow",
        str(wf_file),
        cwd=repo,
    )
    assert (
        res_record.returncode == 0
    ), f"record failed: {res_record.stdout} {res_record.stderr}"

    res_status = run_cli("runs", "status", run_id, "--workflow", str(wf_file), cwd=repo)
    assert res_status.returncode == 1, f"status exit: {res_status.returncode}"
    assert "S-01: performed" in res_status.stdout

    res_verify = run_cli("runs", "verify-ledger", run_id, cwd=repo)
    assert res_verify.returncode == 1, f"verify-ledger exit: {res_verify.returncode}"
    assert "Hash Chain: CLEAN" in res_verify.stdout
    assert "no frozen requirements defined" in res_verify.stdout


def test_case_c_second_init_existing_id_refusal(tmp_path: Path) -> None:
    """Case (c): a second init with the same --run-id exits 6 and leaves the ledger byte-identical."""
    repo = _create_scratch_repo(tmp_path / "repo")
    wf_file = repo / "workflow.json"
    wf_file.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")
    run_id = "run-0123456789abcdef"

    res1 = run_cli(
        "run", "init", "--run-id", run_id, "--workflow", str(wf_file), cwd=repo
    )
    assert res1.returncode == 0, f"res1 failed: {res1.stderr}"

    ledger_path = (
        runner_shared.state_root(repo) / run_id / run_ledger_store.LEDGER_FILENAME
    )
    assert ledger_path.is_file()
    ledger_bytes = ledger_path.read_bytes()

    res2 = run_cli(
        "run", "init", "--run-id", run_id, "--workflow", str(wf_file), cwd=repo
    )
    assert (
        res2.returncode == 6
    ), f"res2 expected exit 6, got {res2.returncode}: {res2.stdout} {res2.stderr}"
    assert ledger_path.read_bytes() == ledger_bytes


def test_case_d_refusals_leave_filesystem_unchanged(tmp_path: Path) -> None:
    """Case (d): malformed --run-id (including ../x), missing workflow, invalid JSON,
    and a JSON array each exit 2 and leave state_root(repo) with no new entry.
    """
    repo = _create_scratch_repo(tmp_path / "repo")
    state_dir = runner_shared.state_root(repo)

    def _state_entries() -> list[str]:
        if not state_dir.exists():
            return []
        return sorted(p.name for p in state_dir.iterdir())

    initial_entries = _state_entries()

    # Valid workflow file
    wf_valid = repo / "workflow.json"
    wf_valid.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")

    # 1. Malformed run ids
    for bad_id in ("../x", "run-short", "invalid-id", "run-XYZ12345"):
        res = run_cli(
            "run", "init", "--run-id", bad_id, "--workflow", str(wf_valid), cwd=repo
        )
        assert res.returncode == 2, f"bad_id {bad_id!r} returned {res.returncode}"
        assert _state_entries() == initial_entries

    # 2. Missing workflow file
    res = run_cli("run", "init", "--workflow", str(repo / "nonexistent.json"), cwd=repo)
    assert res.returncode == 2, f"missing workflow returned {res.returncode}"
    assert _state_entries() == initial_entries

    # 3. Invalid JSON
    wf_invalid = repo / "invalid.json"
    wf_invalid.write_text("{broken json", encoding="utf-8")
    res = run_cli("run", "init", "--workflow", str(wf_invalid), cwd=repo)
    assert res.returncode == 2, f"invalid JSON returned {res.returncode}"
    assert _state_entries() == initial_entries

    # 4. JSON array
    wf_array = repo / "array.json"
    wf_array.write_text("[1, 2, 3]", encoding="utf-8")
    res = run_cli("run", "init", "--workflow", str(wf_array), cwd=repo)
    assert res.returncode == 2, f"JSON array returned {res.returncode}"
    assert _state_entries() == initial_entries


def test_case_e_default_id_generation(tmp_path: Path) -> None:
    """Case (e): the default id matches ^run-[0-9a-f]{16}$ and two default inits produce distinct ids."""
    repo = _create_scratch_repo(tmp_path / "repo")
    wf_file = repo / "workflow.json"
    wf_file.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")

    res1 = run_cli("run", "init", "--workflow", str(wf_file), cwd=repo)
    assert res1.returncode == 0
    id1 = _extract_run_id(res1.stdout)
    assert re.match(r"^run-[0-9a-f]{16}$", id1), f"id1 {id1!r} did not match pattern"

    res2 = run_cli("run", "init", "--workflow", str(wf_file), cwd=repo)
    assert res2.returncode == 0
    id2 = _extract_run_id(res2.stdout)
    assert re.match(r"^run-[0-9a-f]{16}$", id2), f"id2 {id2!r} did not match pattern"

    assert id1 != id2, f"Generated identical IDs: {id1}"


def test_case_f_machine_modes_agent_and_json(tmp_path: Path) -> None:
    """Case (f): --agent emits exactly one line that agent_schema.validate_agent_record accepts,
    naming the id and a repo-relative ledger path, and --json emits one parseable object with the same id.
    """
    repo = _create_scratch_repo(tmp_path / "repo")
    wf_file = repo / "workflow.json"
    wf_file.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")

    # 1. Test --agent
    res_agent = run_cli("run", "init", "--workflow", str(wf_file), "--agent", cwd=repo)
    assert res_agent.returncode == 0, f"agent mode failed: {res_agent.stderr}"
    lines = [ln.strip() for ln in res_agent.stdout.splitlines() if ln.strip()]
    assert (
        len(lines) == 1
    ), f"Expected 1 line in agent output, got {len(lines)}: {lines}"

    agent_rec = json.loads(lines[0])
    errors = agent_schema.validate_agent_record(agent_rec)
    assert errors == [], f"Agent record validation errors: {errors}"
    assert agent_rec["schema"] == "aw.agent/v1"
    assert agent_rec["kind"] == "result"
    assert agent_rec["cmd"] == "run init"
    assert agent_rec["exit"] == 0
    assert agent_rec["outcome"] == "ok"
    assert agent_rec["verified"] is True
    assert agent_rec["complete"] is True
    assert re.match(r"^run-[0-9a-f]{16}$", agent_rec["run_id"])
    assert not Path(
        agent_rec["ledger"]
    ).is_absolute(), f"Ledger path leaked absolute: {agent_rec['ledger']}"
    assert agent_rec["ledger"].endswith("ledger.jsonl")

    # 2. Test --json
    res_json = run_cli("run", "init", "--workflow", str(wf_file), "--json", cwd=repo)
    assert res_json.returncode == 0, f"json mode failed: {res_json.stderr}"
    json_obj = json.loads(res_json.stdout)
    assert re.match(r"^run-[0-9a-f]{16}$", json_obj["run_id"])
    assert json_obj["cmd"] == "run init"
    assert json_obj["exit"] == 0
    assert not Path(json_obj["ledger"]).is_absolute()
    assert json_obj["ledger"].endswith("ledger.jsonl")


def test_case_g_dir_flag_from_different_cwd(tmp_path: Path) -> None:
    """Case (g): --dir <scratch> run from a different cwd writes under the --dir repo."""
    repo = _create_scratch_repo(tmp_path / "repo")
    other_cwd = tmp_path / "other"
    other_cwd.mkdir()

    wf_file = repo / "workflow.json"
    wf_file.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")

    res = run_cli(
        "run", "init", "--workflow", str(wf_file), "--dir", str(repo), cwd=other_cwd
    )
    assert res.returncode == 0, f"dir flag failed: {res.stdout} {res.stderr}"

    run_id = _extract_run_id(res.stdout)
    ledger_path = (
        runner_shared.state_root(repo) / run_id / run_ledger_store.LEDGER_FILENAME
    )
    assert ledger_path.is_file(), f"Ledger not created in repo: {ledger_path}"

    # Verify other_cwd has no .aw created
    assert not (other_cwd / ".aw").exists()

"""Behavioral tests asserting exit code and machine payload for run-ledger readers on corrupt and missing ledgers.

Validates IPD fuuw94 (backlog z63xoh):
- aw runs show|evidence|verify-ledger return EXIT_CORRUPTED_LEDGER (5) on corrupted ledger
- aw runs status|next|resume control cases return EXIT_CORRUPTED_LEDGER (5)
- aw runs show returns EXIT_INVALID_INVOCATION (2) on missing ledger
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pytest

from agent_workflows import run_cli
from agent_workflows import run_ledger_schema as schema
from agent_workflows import run_ledger_store as store


def _build_broken_ledger_fixture(
    dir_path: Path,
) -> Tuple[Path, bool, bool, Optional[store.ChainBreak]]:
    """Build a real two-record ledger and tamper prev_hash to break the hash chain.

    Derives roles and record fields from module symbols per IPD fuuw94 E-05.
    Returns (ledger_path, clean_before, clean_after, break_info).
    """
    ledger_path = dir_path / "corrupted_run.ledger.jsonl"
    ledger_store = store.RunLedgerStore(ledger_path)

    actor = "coordinator" if "coordinator" in schema.ROLES else sorted(schema.ROLES)[0]
    schema_version = schema.LEDGER_SCHEMA_VERSION
    run_id = "run-0123456789abcdef"

    # Seq 0: kind="run"
    run_fields = {
        name: ("0" * 64 if "digest" in name else "0" * 40 if name == "head" else "repo")
        for name, _ in schema._KIND_FIELDS["run"]
    }
    r0 = {
        "schema_version": schema_version,
        "kind": "run",
        "run_id": run_id,
        "actor": actor,
        "parent": "",
        **run_fields,
    }
    ledger_store.append(r0)

    # Seq 1: kind="step_attempt"
    step_fields = {
        name: ("S-01" if name == "step" else "performed" if name == "state" else 1)
        for name, _ in schema._KIND_FIELDS["step_attempt"]
    }
    r1 = {
        "schema_version": schema_version,
        "kind": "step_attempt",
        "run_id": run_id,
        "actor": actor,
        "parent": "",
        **step_fields,
    }
    ledger_store.append(r1)

    clean_before = ledger_store.verify_chain(raise_on_error=False).clean

    # Tamper prev_hash in seq 1
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    rec1 = json.loads(lines[1])
    rec1["prev_hash"] = "0" * 64
    lines[1] = json.dumps(rec1, sort_keys=True, separators=(",", ":"))
    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    chain_ver = ledger_store.verify_chain(raise_on_error=False)
    clean_after = chain_ver.clean
    break_info = chain_ver.break_info

    return ledger_path, clean_before, clean_after, break_info


@pytest.fixture
def corrupted_ledger(
    tmp_path: Path,
) -> Tuple[Path, bool, bool, Optional[store.ChainBreak]]:
    return _build_broken_ledger_fixture(tmp_path)


def test_fixture_integrity(
    corrupted_ledger: Tuple[Path, bool, bool, Optional[store.ChainBreak]],
) -> None:
    """Verify fixture is clean before tamper and broken after, with a real ChainBreak."""
    _, clean_before, clean_after, break_info = corrupted_ledger
    assert clean_before is True, "Fixture must be clean before tamper"
    assert clean_after is False, "Fixture must be broken after tamper"
    assert break_info is not None, "Break info must be present"
    assert break_info.seq == 1
    assert break_info.reason == "prev_hash mismatch"


CORRUPTION_CASES = [
    (
        "show",
        run_cli.EXIT_CORRUPTED_LEDGER,
        {
            "ok": False,
            "corrupted": True,
            "exit_code": run_cli.EXIT_CORRUPTED_LEDGER,
        },
    ),
    (
        "evidence",
        run_cli.EXIT_CORRUPTED_LEDGER,
        {
            "ok": False,
            "corrupted": True,
            "exit_code": run_cli.EXIT_CORRUPTED_LEDGER,
        },
    ),
    (
        "verify-ledger",
        run_cli.EXIT_CORRUPTED_LEDGER,
        {
            "ok": False,
            "chain_clean": False,
            "exit_code": run_cli.EXIT_CORRUPTED_LEDGER,
        },
    ),
    (
        "status",
        run_cli.EXIT_CORRUPTED_LEDGER,
        {
            "ok": False,
            "exit_code": run_cli.EXIT_CORRUPTED_LEDGER,
        },
    ),
    (
        "next",
        run_cli.EXIT_CORRUPTED_LEDGER,
        {
            "ok": False,
            "exit_code": run_cli.EXIT_CORRUPTED_LEDGER,
        },
    ),
    (
        "resume",
        run_cli.EXIT_CORRUPTED_LEDGER,
        {
            "ok": False,
            "exit_code": run_cli.EXIT_CORRUPTED_LEDGER,
        },
    ),
]


@pytest.mark.parametrize(
    "verb,expected_exit,expected_payload_subset",
    CORRUPTION_CASES,
    ids=[c[0] for c in CORRUPTION_CASES],
)
def test_corrupted_ledger_readers(
    corrupted_ledger: Tuple[Path, bool, bool, Optional[store.ChainBreak]],
    verb: str,
    expected_exit: int,
    expected_payload_subset: Dict[str, Any],
) -> None:
    """Drive all six corruption-reporting readers and assert exit code and payload keys."""
    ledger_path, _, _, _ = corrupted_ledger
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "runs",
            verb,
            str(ledger_path),
            "--agent",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == expected_exit, (
        f"Verb 'aw runs {verb}' exited {res.returncode}, expected {expected_exit}. "
        f"Stdout: {res.stdout!r}, Stderr: {res.stderr!r}"
    )

    payload = json.loads(res.stdout)
    for key, expected_value in expected_payload_subset.items():
        assert payload.get(key) == expected_value, (
            f"Verb 'aw runs {verb}' payload key {key!r} was {payload.get(key)!r}, "
            f"expected {expected_value!r}. Full payload: {payload}"
        )


def test_missing_ledger_reports_invalid_invocation(tmp_path: Path) -> None:
    """Assert missing ledger exits EXIT_INVALID_INVOCATION (2) and is distinguishable from corruption."""
    nonexistent = tmp_path / "nonexistent.ledger.jsonl"
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "runs",
            "show",
            str(nonexistent),
            "--agent",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == run_cli.EXIT_INVALID_INVOCATION
    payload = json.loads(res.stdout)
    assert payload.get("ok") is False
    assert payload.get("exit_code") == run_cli.EXIT_INVALID_INVOCATION

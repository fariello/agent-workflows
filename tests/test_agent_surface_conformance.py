"""Behavioral conformance sweep for CLI machine surfaces (aw.agent/v1).

Validates IPD f36de0 (backlog kjr5ol):
- Every declared read/check/bare leaf that declares agent_record_kind="result"
  must emit a schema-valid terminal record with exit code parity under --agent.
- Driven via subprocess; no static inspection of production source code (P16).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional

import pytest

from agent_workflows import cli
from agent_workflows.agent_schema import validate_agent_record
from agent_workflows.command_surface import (
    discover_parser_leaves,
    get_all_declarations,
)
from tests.conformance_matrix import (
    EXEMPTION_REGISTRY,
    RUNNABLE_ARGV,
    run_cli,
    semantic_facts_from_agent,
)


def compute_conformance_universe() -> List[str]:
    """Compute candidate leaves minus the justified exemption registry."""
    parser = cli._build_parser()
    leaves = discover_parser_leaves(parser)
    decls = {d.command: d for d in get_all_declarations()}

    candidates = {
        leaf
        for leaf in leaves
        if decls.get(leaf)
        and decls[leaf].command_class in ("read", "check", "bare")
        and decls[leaf].agent_record_kind == "result"
    }
    universe = sorted(candidates - set(EXEMPTION_REGISTRY.keys()))
    return universe


UNIVERSE = compute_conformance_universe()


@pytest.fixture(scope="session")
def scoped_repo_dir(tmp_path_factory) -> Path:
    """A minimal initialized git repo with a minimal .aw folder.

    Used by expensive whole-tree inspection commands (doctor, check) so their
    conformance check verifies the emit contract without spending tens of seconds
    traversing this repository's full records tree.
    """
    temp_dir = tmp_path_factory.mktemp("scoped_aw_project")
    subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
    (temp_dir / ".aw").mkdir()
    return temp_dir


@pytest.mark.parametrize("leaf", UNIVERSE)
def test_agent_surface_conformance(leaf: str, scoped_repo_dir: Path) -> None:
    """Assert leaf emits non-empty stdout, a valid terminal record, and exit parity."""
    extra_argv = RUNNABLE_ARGV.get(leaf, [])
    full_argv = leaf.split() + extra_argv + ["--agent"]

    # Scope expensive tree-walking leaves to a minimal test project (E-06)
    cwd: Optional[Path] = scoped_repo_dir if leaf in ("doctor", "check") else None

    res = run_cli(full_argv, cwd=cwd)

    # 1. Non-empty stdout
    assert res.stdout.strip(), (
        f"Leaf {leaf!r} emitted EMPTY stdout under --agent!\n"
        f"Argv: {full_argv}\n"
        f"Exit code: {res.returncode}\n"
        f"Stderr: {res.stderr[:500]}"
    )

    # 2. Terminal result/summary/error record present
    facts = semantic_facts_from_agent(res.stdout)
    assert facts, (
        f"Leaf {leaf!r} emitted no terminal result/summary/error record in JSONL!\n"
        f"Argv: {full_argv}\n"
        f"Exit code: {res.returncode}\n"
        f"Stdout: {res.stdout[:500]}\n"
        f"Stderr: {res.stderr[:500]}"
    )

    # Find the last terminal record for schema validation
    terminal_recs = []
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            if isinstance(r, dict) and r.get("kind") in ("result", "summary", "error"):
                terminal_recs.append(r)
        except Exception:
            continue

    assert terminal_recs, (
        f"Leaf {leaf!r}: failed to parse terminal record from JSONL stdout.\n"
        f"Argv: {full_argv}\n"
        f"Stdout: {res.stdout[:500]}"
    )
    last_rec = terminal_recs[-1]

    # 3. validate_agent_record returns []
    val_errors = validate_agent_record(last_rec)
    assert not val_errors, (
        f"Leaf {leaf!r}: record failed schema validation: {val_errors}\n"
        f"Record: {last_rec}\n"
        f"Argv: {full_argv}"
    )

    # 4. Exit code parity: record['exit'] == process exit code
    assert last_rec.get("exit") == res.returncode, (
        f"Leaf {leaf!r}: record exit ({last_rec.get('exit')}) does not match "
        f"process returncode ({res.returncode})\n"
        f"Record: {last_rec}\n"
        f"Argv: {full_argv}"
    )


def test_attention_non_project_cwd(tmp_path: Path) -> None:
    """Pin the kjr5ol defect: attention outside an AW project must emit cannot-run record (E-04)."""
    # Bare git repo with no .aw directory
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

    # Machine path: attention --agent
    res = run_cli(["attention", "--agent"], cwd=tmp_path)
    assert (
        res.stdout.strip()
    ), "attention --agent in non-project dir emitted EMPTY stdout!"
    assert res.returncode == 2, f"Expected returncode 2, got {res.returncode}"

    # Verify JSONL lines: exactly one record
    lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1, f"Expected exactly 1 line, got {len(lines)}: {lines}"
    rec = json.loads(lines[0])

    assert rec.get("kind") in ("result", "error"), f"Unexpected kind: {rec.get('kind')}"
    assert (
        rec.get("outcome") == "cannot-run"
    ), f"Unexpected outcome: {rec.get('outcome')}"
    assert rec.get("exit") == 2, f"Unexpected exit in record: {rec.get('exit')}"
    assert (
        validate_agent_record(rec) == []
    ), f"Validation errors: {validate_agent_record(rec)}"

    # Ensure temp path and /home/ are NOT leaked in stdout
    assert str(tmp_path) not in res.stdout, f"Temp path leaked in stdout: {res.stdout}"
    assert "/home/" not in res.stdout, f"/home/ path leaked in stdout: {res.stdout}"

    # Human path: attention without flags
    # Human exit 3 was retired to 2 by backlog c6vs7y (IPD rwvzqm).
    res_human = run_cli(["attention"], cwd=tmp_path)
    assert (
        res_human.returncode == 2
    ), f"Expected human returncode 2, got {res_human.returncode}"
    assert (
        res_human.stdout == ""
    ), f"Expected empty stdout for human path, got: {res_human.stdout}"
    assert res_human.stderr.strip() != "", "Expected prose on stderr for human path"

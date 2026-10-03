"""Behavioral tests pinning that the no-AW-project condition answers exit 2 across all surfaces.

IPD rwvzqm (exit3three-01):
Pins cross-surface agreement between the human CLI surface and the machine (--agent)
surface for all six spellings ('next', 'att', 'todo', 'attention', 'ipd', 'ipd board')
when invoked outside any AW project, in both a git repository and a non-git directory.

Makes command_surface.CommandDeclaration.exit_contract load-bearing for 'next' and 'ipd board':
the observed runtime exit code must be a member of decl.exit_contract, and 3 must not be
in decl.exit_contract.

Scope note:
This test scopes declaration subset enforcement strictly to 'next' (and its aliases 'att',
'todo', 'attention') and 'ipd board'. Eight other declarations legitimately admit codes outside
0/1/2 (ipd execute-set, run start, runs next, run record, runs resume, run cancel, runs status,
run finalize), which belong to a separate run-execution exit vocabulary (spec 25kzda) where exit 3
indicates required human input. A tree-wide subset assertion would fail across all eight.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agent_workflows.agent_schema import validate_agent_record
from agent_workflows.command_surface import get_declaration

REPO_ROOT = Path(__file__).resolve().parent.parent

SPELLINGS = [
    ("next",),
    ("att",),
    ("todo",),
    ("attention",),
    ("ipd",),
    ("ipd", "board"),
]


def _run_cli(args: tuple[str, ...], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["NO_COLOR"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "agent_workflows", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.mark.parametrize("spelling", SPELLINGS, ids=lambda sp: "-".join(sp))
@pytest.mark.parametrize("is_git", [True, False], ids=["git", "nongit"])
def test_no_project_cross_surface_exit_and_payload(
    spelling: tuple[str, ...], is_git: bool, tmp_path: Path
) -> None:
    """Pin cross-surface agreement (exit 2) and pipe-safety for no-project condition."""
    target_dir = tmp_path / ("git_dir" if is_git else "nongit_dir")
    target_dir.mkdir(parents=True, exist_ok=True)
    if is_git:
        subprocess.run(["git", "init", "-q"], cwd=target_dir, check=True)

    # 1. Drive human surface
    human_res = _run_cli(spelling, cwd=target_dir)

    # 2. Drive agent surface
    agent_res = _run_cli((*spelling, "--agent"), cwd=target_dir)

    # Cross-surface agreement: derived equality rather than only hardcoded numbers
    assert human_res.returncode == agent_res.returncode, (
        f"Surface disagreement for {spelling}: human returned {human_res.returncode}, "
        f"--agent returned {agent_res.returncode}"
    )

    # Invariant: both surfaces must exit 2 (cannot-run)
    assert (
        human_res.returncode == 2
    ), f"Human surface for {spelling} expected exit 2, got {human_res.returncode}"
    assert (
        agent_res.returncode == 2
    ), f"Agent surface for {spelling} expected exit 2, got {agent_res.returncode}"

    # Pipe-safety on human surface: stdout must be strictly empty, stderr carries guidance
    assert (
        human_res.stdout == ""
    ), f"Human surface for {spelling} must leave stdout empty"
    assert (
        "no AW project found" in human_res.stderr
    ), f"Human surface stderr missing guidance: {human_res.stderr}"

    # Agent envelope validation
    assert (
        agent_res.stdout.strip()
    ), f"Agent surface for {spelling} emitted empty stdout"
    lines = [ln.strip() for ln in agent_res.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1, f"Expected 1 JSONL record, got {len(lines)}"
    rec = json.loads(lines[0])

    assert rec.get("schema") == "aw.agent/v1"
    assert rec.get("outcome") == "cannot-run"
    assert rec.get("exit") == 2
    assert (
        validate_agent_record(rec) == []
    ), f"Agent record validation failed: {validate_agent_record(rec)}"

    # Sanitization: ensure temporary directory path and /home/ are NOT leaked in stdout
    assert (
        str(target_dir) not in agent_res.stdout
    ), f"Directory path leaked in stdout: {agent_res.stdout}"
    assert (
        "/home/" not in agent_res.stdout
    ), f"/home/ leaked in stdout: {agent_res.stdout}"

    # Install offer: git repo carries 'aw install .', non-git carries null
    if is_git:
        assert (
            rec.get("next") == "aw install ."
        ), f"Expected next='aw install .' in git repo, got {rec.get('next')}"
    else:
        assert (
            rec.get("next") is None
        ), f"Expected next=None in non-git directory, got {rec.get('next')}"

    # E-05 declaration membership check:
    decl_name = " ".join(spelling)
    decl = get_declaration(decl_name)
    if decl is not None:
        assert (
            human_res.returncode in decl.exit_contract
        ), f"Observed exit {human_res.returncode} not in {decl_name} exit_contract {decl.exit_contract}"
        assert (
            agent_res.returncode in decl.exit_contract
        ), f"Observed exit {agent_res.returncode} not in {decl_name} exit_contract {decl.exit_contract}"
    else:
        # Bare 'ipd' has no declaration at all (parser group leaf without standalone command)
        assert decl_name == "ipd", f"Unexpected undeclared command: {decl_name}"


def test_no_project_exit_declarations_conform() -> None:
    """Make exit_contract load-bearing for 'next' and 'ipd board' and verify 3 is excluded.

    Following the precedent in tests/test_run_cli_declarations.py, this test verifies:
    1. get_declaration retrieves the normative CommandDeclaration for each command.
    2. 'next' and its registered aliases ('att', 'todo', 'attention') as well as 'ipd board'
       declare exit_contract as a subset of (0, 1, 2) (the published three-state classification).
    3. Exit code 3 is explicitly absent from decl.exit_contract for all of them.
    4. Bare 'ipd' has no declaration (returns None), which is explicitly recorded and checked.

    Scope note:
    This subset check is deliberately scoped to these two commands and their aliases.
    Eight other declarations legitimately admit codes outside 0/1/2 (ipd execute-set,
    run start, runs next, run record, runs resume, run cancel, runs status, run finalize),
    which belong to a separate run-execution exit vocabulary (spec 25kzda) where exit 3
    indicates required human input. A tree-wide subset assertion would fail across all eight.
    """
    declared_targets = ["next", "att", "todo", "attention", "ipd board"]

    for name in declared_targets:
        decl = get_declaration(name)
        assert decl is not None, f"Expected declaration for {name}"
        # Assert exit_contract is subset of (0, 1, 2)
        assert set(decl.exit_contract).issubset(
            {0, 1, 2}
        ), f"{name} exit_contract {decl.exit_contract} is not a subset of (0, 1, 2)"
        # Assert 3 is absent from exit_contract
        assert (
            3 not in decl.exit_contract
        ), f"Exit 3 must not be in {name} exit_contract {decl.exit_contract}"

    # Bare 'ipd' is undeclared in command inventory
    assert get_declaration("ipd") is None, "Expected get_declaration('ipd') to be None"

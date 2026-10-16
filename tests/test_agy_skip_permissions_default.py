"""Behavioral coverage that the Antigravity driver's skip-permissions option defaults to True.

Restores the behavioral guard deleted in 19313eed (spec R4.1c). Asserts:
1. The parser defaults dangerously_skip_permissions to True, and only --no-dangerously-skip-permissions yields False.
2. The real run_agy_turn argv defaults to including --dangerously-skip-permissions (for absent key and True, omitted for False).
3. The real initialize_run freezes dangerously_skip_permissions as True under an isolated config home, and False with the opt-out flag.
4. The real runner_shared.probe_argv coverage probe defaults to including --dangerously-skip-permissions (absent key and True, omitted for False).
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, runner_shared


class TestParserDefault:
    """Task group 1 (E-01): Parser default and flag behavior for dangerously_skip_permissions."""

    def test_parser_default_is_true(self) -> None:
        parser = agy_runipd.build_parser()
        args = parser.parse_args(["start", "someid"])
        assert args.dangerously_skip_permissions is True, (
            "R4.1c forbids flipping the default without its own decision: "
            "dangerously_skip_permissions must default to True"
        )

    def test_parser_opt_out_is_false(self) -> None:
        parser = agy_runipd.build_parser()
        args = parser.parse_args(
            ["start", "someid", "--no-dangerously-skip-permissions"]
        )
        assert args.dangerously_skip_permissions is False

    def test_parser_explicit_flags_are_true(self) -> None:
        parser = agy_runipd.build_parser()
        for flag in ("--dangerously-skip-permissions", "--dangerous"):
            args = parser.parse_args(["start", "someid", flag])
            assert (
                args.dangerously_skip_permissions is True
            ), f"Flag {flag} must yield dangerously_skip_permissions is True"


def _setup_launcher_run_dir(
    tmp_path: Path,
) -> tuple[dict[str, Any], Path, dict[str, Any], Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    run_dir = tmp_path / "run"
    (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    plan_path = repo / "plan.ipd.md"
    plan_path.write_text("# Plan\n", encoding="utf-8")
    prompt_path = run_dir / "prompt.md"
    prompt_path.write_text("prompt content", encoding="utf-8")
    state = {"run_id": "run-test", "repo": str(repo), "options": {}}
    item = {"id6": "wir001", "position": 1, "setid": "testset", "action": "execute"}
    return state, run_dir, item, plan_path, prompt_path


def _run_turn_and_capture_agy_argv(tmp_dir: Path, options: dict[str, Any]) -> list[str]:
    state, run_dir, item, _, prompt_path = _setup_launcher_run_dir(tmp_dir)
    state["options"] = dict(options)
    state["options"]["agy"] = sys.executable

    captured_argvs: list[list[str]] = []

    class FakeProc:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            cmd = args[0] if args else kwargs.get("args")
            captured_argvs.append(list(cmd) if cmd is not None else [])
            self.pid = 12345
            self.stdout = io.StringIO("")
            self.returncode = 0

        def poll(self) -> int:
            return 0

        def wait(self, timeout: float | None = None) -> int:
            return 0

        def communicate(self, *args: Any, **kwargs: Any) -> tuple[str, str]:
            return "", ""

    with mock.patch("subprocess.Popen", side_effect=FakeProc):
        agy_runipd.run_agy_turn(
            state,
            run_dir,
            item,
            prompt_path,
            1,
            session_id=None,
            use_continue=False,
            work_dir=None,
        )

    resolved_bin = agy_runipd.resolve_agy(sys.executable)
    agy_calls = [cmd for cmd in captured_argvs if cmd and cmd[0] == resolved_bin]
    assert len(agy_calls) == 1, (
        f"Expected exactly 1 agy launch argv whose argv[0] == {resolved_bin!r}, "
        f"found {len(agy_calls)} out of {len(captured_argvs)} calls: {captured_argvs}"
    )
    return agy_calls[0]


class TestAgyTurnArgvDefault:
    """Task group 2 (E-02): Captured argv in run_agy_turn carries the default."""

    def test_run_agy_turn_argv_defaults_to_skip_permissions(
        self, tmp_path: Path
    ) -> None:
        argv = _run_turn_and_capture_agy_argv(tmp_path / "omitted", {})
        assert "--dangerously-skip-permissions" in argv

    def test_run_agy_turn_argv_with_skip_permissions_true(self, tmp_path: Path) -> None:
        argv = _run_turn_and_capture_agy_argv(
            tmp_path / "true", {"dangerously_skip_permissions": True}
        )
        assert "--dangerously-skip-permissions" in argv

    def test_run_agy_turn_argv_with_skip_permissions_false(
        self, tmp_path: Path
    ) -> None:
        argv = _run_turn_and_capture_agy_argv(
            tmp_path / "false", {"dangerously_skip_permissions": False}
        )
        assert "--dangerously-skip-permissions" not in argv


PLAN_FIXTURE = """# IPD: test fixture

- Date: 2026-10-14
- Kind: child
- Concern: fixture
- Scope: fixture
- Scope-Paths: README.md
- Status: approved
- Set: fixture
- Order: 1
- Highest E allocated: 01
- Author: test
- Priority: low
- Work-Kind: chore
- Id: {id6}
- Approval: 2026-10-14, fixture
- Readiness: go-pending-approval

## Workflow history
- 2026-10-14 reviewed (test): APPROVE; no blocking findings.

## Goal
Fixture.

## Detailed Implementation Checklist (TODO)
### Task group 1: work
- [ ] E-01 Step 1
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
None.

## Findings
None.

## Proposed changes (ordered, validatable)
None.

## Deferred / out of scope (with reason)
None.

## Scope check
None.

## Required tests / validation
None.

## Spec / documentation sync
None.

## Open questions
None.

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: done
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""


def _make_temp_repo(root: Path, id6: str = "fix001") -> Path:
    repo = root / "repo"
    repo.mkdir(parents=True)
    for cmd in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "test@example.invalid"],
        ["git", "config", "user.name", "Test"],
    ):
        subprocess.run(cmd, cwd=repo, check=True)
    (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    (pending / f"20261014-fixture-01-{id6}-test.ipd.md").write_text(
        PLAN_FIXTURE.format(id6=id6), encoding="utf-8"
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return repo


def _frozen_options_for_args(
    extra_args: list[str], tmp_path: Path, id6: str = "fix001"
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as home:
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": home}, clear=False):
            repo = _make_temp_repo(tmp_path / f"repo_{id6}", id6=id6)
            args = agy_runipd.build_parser().parse_args(
                ["start", id6, "--repo", str(repo), *extra_args]
            )
            args.prepare_only = True
            run_dir = agy_runipd.initialize_run(args)
            return runner_shared.load_state(run_dir)["options"]


class TestRunInitializationFrozenOption:
    """Task group 2 (E-03): Default survives run initialization into frozen options."""

    def test_initialize_run_freezes_default_true(self, tmp_path: Path) -> None:
        options = _frozen_options_for_args([], tmp_path, id6="fix001")
        assert options["dangerously_skip_permissions"] is True

    def test_initialize_run_freezes_opt_out_false(self, tmp_path: Path) -> None:
        options = _frozen_options_for_args(
            ["--no-dangerously-skip-permissions"], tmp_path, id6="fix002"
        )
        assert options["dangerously_skip_permissions"] is False


class TestCoverageProbeArgvDefault:
    """Task group 2 (E-05): Coverage-probe launch site defaults on."""

    def test_probe_argv_defaults_to_skip_permissions(self, tmp_path: Path) -> None:
        argv = runner_shared.probe_argv(
            {"options": {"agy": "agy"}}, host="agy", prompt="p", repo=str(tmp_path)
        )
        assert "--dangerously-skip-permissions" in argv

    def test_probe_argv_with_skip_permissions_true(self, tmp_path: Path) -> None:
        argv = runner_shared.probe_argv(
            {"options": {"agy": "agy", "dangerously_skip_permissions": True}},
            host="agy",
            prompt="p",
            repo=str(tmp_path),
        )
        assert "--dangerously-skip-permissions" in argv

    def test_probe_argv_with_skip_permissions_false(self, tmp_path: Path) -> None:
        argv = runner_shared.probe_argv(
            {"options": {"agy": "agy", "dangerously_skip_permissions": False}},
            host="agy",
            prompt="p",
            repo=str(tmp_path),
        )
        assert "--dangerously-skip-permissions" not in argv

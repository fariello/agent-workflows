"""End-to-end integration tests proving a run that changes its own linter retires its orchestrator.

Covers Set runfresh, IPD hohlc6 (Order 05):
Validates spec 25kzda 5.3b and 4.1:
- A run whose child modifies the linter schema in agent_workflows/ipd_schema.py and updates
  the orchestrator front matter with a newly recognized field restarts between items on new code.
- Resuming into the updated codebase allows the orchestrator's retirement to lint conforming
  and succeed.
- Disabling the restart via AW_NO_DRIVER_RESTART=1 leaves the driver running on stale in-memory code,
  causing orchestrator retirement to be refused with IPD-M103 unknown field and ending fail-depend.
- Process identity and nested-call pinning are re-established across os.execv.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

import pytest

from tests.support import REPO_ROOT, make_fake_executable

pytestmark = pytest.mark.slow

_PROBE_FIELD = "Runfresh-Probe"

_ORCHESTRATOR_TEMPLATE = """# IPD: Test Orchestrator {orch_id6}

- Date: 2026-10-06
- Kind: orchestrator
- Id: {orch_id6}
- Set: {setid}
- Order: 0
- Status: approved
- Approval: 2026-10-06, recorded via aw ipd set: status set to approved
- Priority: high
- Work-Kind: bug
- Author: test
- Highest E allocated: 01
- Concern: Test orchestrator concern.
- Scope: Test orchestrator scope.
- Scope-Paths: tests/test_runfresh_end_to_end.py
- Item-Dependencies: none

## Workflow history
- 2026-10-06 approved (test): status set to approved
- 2026-10-06 created (test): created

## Goal
Test orchestrator goal.

## Detailed Implementation Checklist (TODO)
Execution-state rule: mark performed only after doing it.
### Task group 1: orchestrate
- [ ] E-01 CONFIRM {child_id6} REACHED executed
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
|---|---|---|---|---|
| 01 | {child_id6} | pending | .aw/records/plans/pending/20261006-{setid}-01-{child_id6}-child.ipd.md | none |

## Completion criteria (the whole Set is done only when)
- {child_id6} reached executed

## Cross-IPD validation
- None.

## Deferred / out of scope (with reason)
- None.

## Scope check
- None.

## Required tests / validation
- None.

## Spec / documentation sync
- None.

## Open questions
- None.

## Validation and cross-check (verify before reporting the Set complete)
Validation-state rule: inspect evidence.
- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- None.
"""

_CHILD_TEMPLATE = """# IPD: Test Child Plan {child_id6}

- Date: 2026-10-06
- Kind: child
- Concern: Test child {child_id6} concern.
- Scope: Test child {child_id6} scope.
- Scope-Paths: agent_workflows/ipd_schema.py
- Status: approved
- Approval: 2026-10-06, recorded via aw ipd set: status set to approved
- Set: {setid}
- Order: 1
- Highest E allocated: 01
- Author: test
- Priority: high
- Work-Kind: bug
- Id: {child_id6}
- Item-Dependencies: none

## Workflow history
- 2026-10-06 approved (test): status set to approved
- 2026-10-06 created (test): created

## Goal
Test child {child_id6} goal.

## Detailed Implementation Checklist (TODO)
Execution-state rule: mark performed only after doing it.
### Task group 1: work
- [ ] E-01 Work item
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
- None.

## Findings
- None.

## Proposed changes (ordered, validatable)
1. E-01 do work.

## Deferred / out of scope (with reason)
- None.

## Scope check
- None.

## Required tests / validation
- None.

## Spec / documentation sync
- None.

## Open questions
- None.

## Validation and cross-check (verify before reporting done)
Validation-state rule: inspect evidence.
- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- None.
"""

_FAKE_HOST_SCRIPT = r"""#!/usr/bin/env python3
import json
import os
import pathlib
import re
import subprocess
import sys

args = sys.argv[1:]
if "--" in args:
    prompt = args[args.index("--") + 1]
    is_oc = True
elif "-p" in args:
    prompt = args[args.index("-p") + 1]
    is_oc = False
else:
    prompt = ""
    is_oc = True

if "--conversation" in args:
    session = args[args.index("--conversation") + 1]
elif "--session" in args:
    session = args[args.index("--session") + 1]
else:
    session = "fake_session_rf"

if is_oc:
    sys.stdout.write(json.dumps({"type": "step_start", "part": {}, "sessionID": session}) + "\n")
    sys.stdout.write(json.dumps({"type": "tool_use", "part": {"type": "tool", "tool": "bash", "state": {"status": "completed"}}, "sessionID": session}) + "\n")
    sys.stdout.flush()
else:
    sys.stdout.write(json.dumps({"event": "init", "conversation_id": session, "init": {"model": "antigravity"}}) + "\n")
    sys.stdout.write(json.dumps({"type": "step_update", "step_update": {"state": "DONE", "step_type": "tool", "tool_info": {"name": "bash"}}}) + "\n")
    sys.stdout.flush()

id6_m = re.search(r"Assigned IPD: (\S+)", prompt)
id6 = id6_m.group(1) if id6_m else ""

plan_m = re.search(r"Plan file at launch: (\S+)", prompt)
plan_rel = plan_m.group(1).strip() if plan_m else ""

outcome_m = re.search(r"Required JSON outcome: (\S+)", prompt)
outcome_rel = outcome_m.group(1).strip() if outcome_m else ""

repo = pathlib.Path.cwd()

# (a) add "Runfresh-Probe" to META_RECOGNIZED in <fixture>/agent_workflows/ipd_schema.py
schema_path = repo / "agent_workflows" / "ipd_schema.py"
schema_text = schema_path.read_text(encoding="utf-8")
if '"Runfresh-Probe"' not in schema_text:
    schema_text = schema_text.replace(
        "META_COVERAGE_CHECKED,\n",
        "META_COVERAGE_CHECKED,\n        \"Runfresh-Probe\",\n",
    )
    schema_path.write_text(schema_text, encoding="utf-8")

# (b) insert - Runfresh-Probe: x into the orchestrator's front matter
pending_dir = repo / ".aw" / "records" / "plans" / "pending"
for p in pending_dir.glob("*.ipd.md"):
    text = p.read_text(encoding="utf-8")
    if "- Kind: orchestrator" in text and "- Runfresh-Probe:" not in text:
        text = text.replace("- Status: approved\n", "- Status: approved\n- Runfresh-Probe: x\n")
        p.write_text(text, encoding="utf-8")

# (c) move the child plan to executed/ with - Status: executed
if plan_rel:
    src = repo / plan_rel
    dst = repo / plan_rel.replace("/pending/", "/executed/")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_file():
        child_text = src.read_text(encoding="utf-8")
        child_text = child_text.replace("- Status: approved\n", "- Status: executed\n")
        child_text = re.sub(r"(?m)^- Approval:.*\n?", "", child_text)
        child_text = child_text.replace(
            "## Workflow history\n",
            "## Workflow history\n- 2026-10-06 executed (tester): executed\n",
        )
        dst.write_text(child_text, encoding="utf-8")
        src.unlink()

# (d) git add -A && git commit in the fixture
subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
st = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True)
if st.stdout.strip():
    subprocess.run(["git", "commit", "-qm", "child turn executed"], cwd=repo, check=True)


# (e) write the Required JSON outcome: file with disposition: executed
if outcome_rel:
    out_file = repo / outcome_rel
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps({
        "schema_version": 1,
        "id6": id6,
        "disposition": "executed",
        "pushed": False,
    }), encoding="utf-8")

if is_oc:
    sys.stdout.write(json.dumps({"type": "text", "part": {"text": "done"}, "sessionID": session}) + "\n")
    sys.stdout.flush()
else:
    sys.stdout.write(json.dumps({"event": "result", "result": {"status": "SUCCESS"}}) + "\n")
    sys.stdout.flush()

sys.exit(0)
"""

_NESTED_PIN_SCRIPT = r"""#!/usr/bin/env python3
import os
import sys
from pathlib import Path

phase = sys.argv[1]
events_path = Path(sys.argv[2])
fixture_root = Path(sys.argv[3])

from agent_workflows import runner_shared

if phase == "phase1":
    runner_shared.assert_child_tool_identity(events_path, cwd=fixture_root)
    os.execv(sys.executable, [sys.executable, __file__, "phase2", str(events_path), str(fixture_root)])
elif phase == "phase2":
    runner_shared.assert_child_tool_identity(events_path, cwd=fixture_root)
    sys.exit(0)
else:
    sys.exit(1)
"""


def make_runfresh_fixture(
    root: Path,
    *,
    setid: str = "rfset1",
    orch_id6: str = "orc001",
    child_id6: str = "chd001",
    mutate_restart_decision: bool = False,
) -> tuple[Path, Path, Path, Path]:
    """Create a temporary git repository toolkit checkout holding a runfresh Set."""
    fixture = root.resolve()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=fixture, check=True)
    subprocess.run(
        ["git", "config", "user.email", "tester@example.com"], cwd=fixture, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=fixture, check=True)
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=fixture, check=True
    )

    (fixture / ".gitignore").write_text(
        ".aw/records/runs/\n.aw/state/\n.aw/worktrees/\n__pycache__/\n*.pyc\n",
        encoding="utf-8",
    )

    shutil.copytree(
        REPO_ROOT / "agent_workflows",
        fixture / "agent_workflows",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    if (
        mutate_restart_decision
        or os.environ.get("RUNFRESH_MUTATE_RESTART_DECISION") == "1"
    ):
        rs_path = fixture / "agent_workflows" / "runner_shared.py"
        rs_text = rs_path.read_text(encoding="utf-8")
        rs_text = rs_text.replace(
            "def restart_decision(",
            'def restart_decision(*_args, **_kwargs):\n    return "none"\n\ndef _orig_restart_decision(',
        )
        rs_path.write_text(rs_text, encoding="utf-8")

    pending_dir = fixture / ".aw" / "records" / "plans" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    (fixture / ".aw" / "records" / "plans" / "executed").mkdir(
        parents=True, exist_ok=True
    )

    orch_path = pending_dir / f"20261006-{setid}-00-{orch_id6}-orchestrator.ipd.md"
    orch_path.write_text(
        _ORCHESTRATOR_TEMPLATE.format(
            setid=setid,
            orch_id6=orch_id6,
            child_id6=child_id6,
        ),
        encoding="utf-8",
    )

    child_path = pending_dir / f"20261006-{setid}-01-{child_id6}-child.ipd.md"
    child_path.write_text(
        _CHILD_TEMPLATE.format(
            setid=setid,
            child_id6=child_id6,
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["PYTHONPATH"] = str(fixture)
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from agent_workflows import coverage_record; "
            "coverage_record.write(sys.argv[1], verdict=coverage_record.COVERAGE_PASS, commit=False)",
            str(orch_path),
        ],
        cwd=fixture,
        env=env,
        check=True,
    )

    fake_host = make_fake_executable(fixture / "fake_agent", _FAKE_HOST_SCRIPT)

    subprocess.run(["git", "add", "-A"], cwd=fixture, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "initial fixture commit"], cwd=fixture, check=True
    )

    return fixture, fake_host, orch_path, child_path


def _clean_driver_env(
    fixture_root: Path, *, disable_restart: bool = False
) -> dict[str, str]:
    """Build environment for driving the driver as a subprocess pinned to the fixture."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(fixture_root)
    env.pop("AW_NO_REEXEC", None)
    env.pop("AW_REEXEC_FROM", None)
    env.pop("AW_EXECUTION_ROLE", None)
    env.pop("AW_PINNED_CHILD", None)
    env.pop("AW_PIN_KEEP_ROOT", None)
    if disable_restart:
        env["AW_NO_DRIVER_RESTART"] = "1"
    else:
        env.pop("AW_NO_DRIVER_RESTART", None)
    return env


def _find_single_run_dir(fixture_root: Path) -> Path:
    """Locate the single run directory created under .aw/records/runs/."""
    runs_dir = fixture_root / ".aw" / "records" / "runs"
    subdirs = [
        p for p in runs_dir.iterdir() if p.is_dir() and p.name.startswith("run-")
    ]
    assert len(subdirs) == 1, f"Expected 1 run dir, found: {subdirs}"
    return subdirs[0]


class RunfreshEndToEndTests(unittest.TestCase):
    """Integration suite proving restart behavior and linter drift resolution."""

    def test_e01_pre_run_linter_drift(self) -> None:
        """Validate Task group 1: pre-run lint reproduces the 2026-10-06 unknown field failure."""
        with tempfile.TemporaryDirectory() as td:
            fixture_root, _fake_host, orch_path, _child_path = make_runfresh_fixture(
                Path(td)
            )

            # Make a scratch copy of the orchestrator under executed/ with Runfresh-Probe added
            executed_dir = fixture_root / ".aw" / "records" / "plans" / "executed"
            scratch_orch = executed_dir / orch_path.name
            orch_text = orch_path.read_text(encoding="utf-8")
            orch_text = orch_text.replace(
                "- Status: approved\n", f"- Status: executed\n- {_PROBE_FIELD}: x\n"
            )
            orch_text = re.sub(r"(?m)^- Approval:.*\n?", "", orch_text)
            orch_text = orch_text.replace(
                "## Workflow history\n",
                "## Workflow history\n- 2026-10-06 executed (tester): executed\n",
            )
            scratch_orch.write_text(orch_text, encoding="utf-8")

            env = _clean_driver_env(fixture_root)

            # Pre-run lint with ORIGINAL package -> reports IPD-M103 unknown field
            lint_orig = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "ipd",
                    "lint",
                    "--phase",
                    "post-transition",
                    str(scratch_orch),
                ],
                cwd=fixture_root,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(
                lint_orig.returncode,
                0,
                f"Expected lint failure with original package:\n{lint_orig.stdout}\n{lint_orig.stderr}",
            )
            combined_orig = lint_orig.stdout + lint_orig.stderr
            self.assertIn("IPD-M103", combined_orig)
            self.assertIn(f"{_PROBE_FIELD}: unknown field", combined_orig)

            # Edit the package in the fixture to recognize the field (Step a)
            schema_path = fixture_root / "agent_workflows" / "ipd_schema.py"
            schema_text = schema_path.read_text(encoding="utf-8")
            schema_text = schema_text.replace(
                "META_COVERAGE_CHECKED,\n",
                f'META_COVERAGE_CHECKED,\n        "{_PROBE_FIELD}",\n',
            )
            schema_path.write_text(schema_text, encoding="utf-8")

            # Pre-run lint with EDITED package -> reports no IPD-M103 finding
            lint_edited = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "ipd",
                    "lint",
                    "--phase",
                    "post-transition",
                    str(scratch_orch),
                ],
                cwd=fixture_root,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                lint_edited.returncode,
                0,
                f"Expected conforming lint with edited package:\n{lint_edited.stdout}\n{lint_edited.stderr}",
            )
            self.assertNotIn("IPD-M103", lint_edited.stdout + lint_edited.stderr)

    def _drive_host_run(
        self,
        host: str,
        *,
        disable_restart: bool = False,
    ) -> tuple[
        subprocess.CompletedProcess[str],
        Path,
        dict[str, Any],
        list[dict[str, Any]],
        str,
        str,
    ]:
        """Execute a full driver run for host in a fresh temporary repository."""
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        setid = f"rf{host}"
        orch_id6 = "orcoc1" if host == "oc" else "oragy1"
        child_id6 = "chdoc1" if host == "oc" else "chagy1"

        fixture_root, fake_host, _orch_path, _child_path = make_runfresh_fixture(
            Path(td.name),
            setid=setid,
            orch_id6=orch_id6,
            child_id6=child_id6,
        )

        host_flag = "--opencode" if host == "oc" else "--agy"
        cmd = [
            sys.executable,
            "-m",
            "agent_workflows",
            host,
            "run",
            "start",
            setid,
            "--no-isolate-worktree",
            "--no-self-finalize",
            "--no-validate",
            host_flag,
            str(fake_host),
        ]
        env = _clean_driver_env(fixture_root, disable_restart=disable_restart)
        proc = subprocess.run(
            cmd, cwd=fixture_root, env=env, capture_output=True, text=True
        )
        if not (fixture_root / ".aw" / "records" / "runs").is_dir():
            raise AssertionError(
                f"Driver failed early (returncode={proc.returncode}):\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            )

        run_dir = _find_single_run_dir(fixture_root)
        state_file = run_dir / "state.json"
        state = (
            json.loads(state_file.read_text(encoding="utf-8"))
            if state_file.is_file()
            else {}
        )
        events_file = run_dir / "events.jsonl"
        events: list[dict[str, Any]] = []
        if events_file.is_file():
            events = [
                json.loads(line)
                for line in events_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        return proc, fixture_root, state, events, orch_id6, child_id6

    def _get_prepare_only_options(self, host: str, fake_host: Path) -> dict[str, Any]:
        """Obtain state['options'] from a --prepare-only start of an identical fixture."""
        with tempfile.TemporaryDirectory() as td:
            setid = f"rf{host}"
            orch_id6 = "orcoc1" if host == "oc" else "oragy1"
            child_id6 = "chdoc1" if host == "oc" else "chagy1"
            fixture_root, _unused_fake, _orch, _chd = make_runfresh_fixture(
                Path(td),
                setid=setid,
                orch_id6=orch_id6,
                child_id6=child_id6,
            )
            host_flag = "--opencode" if host == "oc" else "--agy"
            cmd = [
                sys.executable,
                "-m",
                "agent_workflows",
                host,
                "run",
                "start",
                setid,
                "--no-isolate-worktree",
                "--no-self-finalize",
                "--no-validate",
                "--prepare-only",
                host_flag,
                str(fake_host),
            ]
            env = _clean_driver_env(fixture_root)
            proc = subprocess.run(
                cmd, cwd=fixture_root, env=env, capture_output=True, text=True
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"prepare-only failed:\n{proc.stdout}\n{proc.stderr}",
            )
            run_dir = _find_single_run_dir(fixture_root)
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            return state.get("options", {})

    def _verify_restart_enabled(self, host: str) -> None:
        """Run and assert restart-enabled case for the given host (E-02)."""
        proc, fixture_root, state, events, orch_id6, child_id6 = self._drive_host_run(
            host, disable_restart=False
        )
        fake_host = fixture_root / "fake_agent"
        expected_options = self._get_prepare_only_options(host, fake_host)
        self.assertEqual(
            proc.returncode,
            0,
            f"Driver run failed for {host} (restart enabled):\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )

        # 1. Exactly one driver-restarted event
        restarted_events = [e for e in events if e.get("event") == "driver-restarted"]
        self.assertEqual(
            len(restarted_events),
            1,
            f"Expected exactly 1 driver-restarted event for {host}, got {len(restarted_events)}",
        )
        restarted = restarted_events[0]
        self.assertEqual(restarted.get("previous_id6"), child_id6)
        self.assertIn(
            "agent_workflows/ipd_schema.py", restarted.get("changed_files", [])
        )

        # 2. state['driver']['loaded_code'] has two entries with different fingerprints
        loaded_code = state.get("driver", {}).get("loaded_code", [])
        self.assertEqual(
            len(loaded_code),
            2,
            f"Expected 2 loaded_code entries, got {len(loaded_code)}",
        )
        self.assertNotEqual(
            loaded_code[0].get("fingerprint"), loaded_code[1].get("fingerprint")
        )

        # 3. Orchestrator file under executed/ with - Status: executed
        executed_plans = list(
            (fixture_root / ".aw" / "records" / "plans" / "executed").glob(
                f"*-{orch_id6}-*.ipd.md"
            )
        )
        self.assertEqual(
            len(executed_plans),
            1,
            f"Expected orchestrator in executed/, found: {executed_plans}",
        )
        orch_executed_text = executed_plans[0].read_text(encoding="utf-8")
        self.assertIn("- Status: executed", orch_executed_text)

        # 4. No refusal on orchestrator item
        orch_item = next(
            (it for it in state.get("queue", []) if it.get("id6") == orch_id6), None
        )
        self.assertIsNotNone(orch_item, "Orchestrator item not found in queue")
        assert orch_item is not None
        self.assertEqual(orch_item.get("status"), "executed")
        self.assertIsNone(
            orch_item.get("refusal"),
            f"Unexpected refusal on orchestrator: {orch_item.get('refusal')}",
        )

        # 5. stdout of resumed process shows 'Restarts: 1'
        self.assertIn("Restarts: 1", proc.stdout)

        # 6. Child item executed with exactly one attempt
        child_item = next(
            (it for it in state.get("queue", []) if it.get("id6") == child_id6), None
        )
        self.assertIsNotNone(child_item, "Child item not found in queue")
        assert child_item is not None
        self.assertEqual(child_item.get("status"), "executed")
        self.assertEqual(len(child_item.get("attempts", [])), 1)

        # 7. state['options'] equals state['options'] from --prepare-only
        self.assertEqual(state.get("options"), expected_options)

        # 8. state['set_sessions'] maps setid to child attempt's session id
        setid = f"rf{host}"
        child_session = child_item["attempts"][0].get("session_id") or child_item[
            "attempts"
        ][0].get("session")
        self.assertEqual(state.get("set_sessions", {}).get(setid), child_session)

    def _verify_restart_disabled(self, host: str) -> None:
        """Run and assert restart-disabled case (AW_NO_DRIVER_RESTART=1) for the given host (E-02)."""
        _proc, _fixture_root, state, events, orch_id6, _child_id6 = (
            self._drive_host_run(host, disable_restart=True)
        )

        # 1. No driver-restarted event
        restarted_events = [e for e in events if e.get("event") == "driver-restarted"]
        self.assertEqual(
            len(restarted_events),
            0,
            f"Expected 0 driver-restarted events when restart is disabled, got {len(restarted_events)}",
        )

        # 2. Orchestrator ends fail-depend with refusal.code == 'finalize-refused'
        orch_item = next(
            (it for it in state.get("queue", []) if it.get("id6") == orch_id6), None
        )
        self.assertIsNotNone(orch_item, "Orchestrator item not found in queue")
        assert orch_item is not None
        self.assertEqual(orch_item.get("status"), "fail-depend")
        refusal = orch_item.get("refusal") or {}
        self.assertEqual(refusal.get("code"), "finalize-refused")
        reason = refusal.get("reason", "")
        self.assertIn("IPD-M103", reason)
        self.assertIn(_PROBE_FIELD, reason)

    def test_e02_oc_restart_enabled(self) -> None:
        """E-02 oc host: restart enabled retires orchestrator cleanly on reloaded schema."""
        self._verify_restart_enabled("oc")

    def test_e02_oc_restart_disabled(self) -> None:
        """E-02 oc host: restart disabled (AW_NO_DRIVER_RESTART=1) refuses orchestrator retirement."""
        self._verify_restart_disabled("oc")

    def test_e02_agy_restart_enabled(self) -> None:
        """E-02 agy host: restart enabled retires orchestrator cleanly on reloaded schema."""
        self._verify_restart_enabled("agy")

    def test_e02_agy_restart_disabled(self) -> None:
        """E-02 agy host: restart disabled (AW_NO_DRIVER_RESTART=1) refuses orchestrator retirement."""
        self._verify_restart_disabled("agy")

    def test_e05_nested_call_pin_reestablished_after_exec(self) -> None:
        """E-05: nested-call pin re-established after a restart via os.execv."""
        with tempfile.TemporaryDirectory() as td:
            fixture_root, _fake_host, _orch, _child = make_runfresh_fixture(Path(td))
            script_path = make_fake_executable(
                fixture_root / "nested_pin_script.py", _NESTED_PIN_SCRIPT
            )
            events_path = fixture_root / "events.jsonl"

            env = _clean_driver_env(fixture_root)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "phase1",
                    str(events_path),
                    str(fixture_root),
                ],
                cwd=fixture_root,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"Nested pin script failed:\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
            )

            self.assertTrue(events_path.is_file(), "events.jsonl not written")
            events = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            verified = [e for e in events if e.get("event") == "tool-identity-verified"]
            self.assertEqual(
                len(verified),
                2,
                f"Expected 2 tool-identity-verified events, got {len(verified)}",
            )

            expected_module = os.path.realpath(
                str(fixture_root / "agent_workflows" / "__init__.py")
            )
            for idx, ev in enumerate(verified, start=1):
                self.assertEqual(
                    ev.get("expected_module"),
                    expected_module,
                    f"Event {idx} expected_module mismatch",
                )
                self.assertEqual(
                    ev.get("child_module"),
                    expected_module,
                    f"Event {idx} child_module mismatch",
                )
                self.assertEqual(
                    ev.get("child_module"),
                    ev.get("expected_module"),
                    f"Event {idx} child_module does not equal expected_module",
                )

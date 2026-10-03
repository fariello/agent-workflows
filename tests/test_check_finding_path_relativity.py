"""Behavioral tests verifying that check-engine finding fields are repo-relative.

Pins:
- Lifecycle placement conflict does not crash --agent with ValueError when repo is under $HOME.
- Composite location, detail, and recovery fields do not leak home paths or absolute root.
- System layout missing finding does not leak home paths or absolute root in recovery.
- IPD lint diagnostics do not leak home paths or absolute root in recovery.
- Collision findings (id6 and setid) do not leak home paths or absolute root in detail.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from agent_workflows.agent_schema import (
    _HOME_PATH_RE,
    validate_agent_record,
)


class CheckFindingPathRelativityTests(unittest.TestCase):
    """Verify repo-relativity of finding fields across --agent and --json surfaces."""

    def _create_fixture_repo(self) -> str:
        # Fixture root is derived from os.path.expanduser at runtime
        home_dir = os.path.expanduser("~")
        fixture_dir = tempfile.mkdtemp(dir=home_dir, prefix="aw_rel_test_")
        subprocess.run(
            ["git", "init"], cwd=fixture_dir, check=True, capture_output=True
        )
        return fixture_dir

    def _assert_no_leaks(self, obj: Any, resolved_root: str, path: str = "") -> None:
        """Walk json payload asserting zero home-path matches and no resolved root substring."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                current_path = f"{path}.{k}" if path else k
                if current_path == "data.repo_root":
                    continue  # data.repo_root is a deliberate absolute fact, out of scope
                self._assert_no_leaks(v, resolved_root, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._assert_no_leaks(item, resolved_root, f"{path}[{i}]")
        elif isinstance(obj, str):
            self.assertIsNone(
                _HOME_PATH_RE.search(obj),
                f"Home path leak detected at {path}: {obj}",
            )
            self.assertNotIn(
                resolved_root,
                obj,
                f"Resolved fixture root substring detected at {path}: {obj}",
            )

    def test_lifecycle_placement_conflict_no_crash_and_no_leak(self) -> None:
        """Lifecycle placement conflict on --agent must not crash and on --json must not leak."""
        fixture_dir = self._create_fixture_repo()
        try:
            resolved_root = str(Path(fixture_dir).resolve())
            pending = os.path.join(fixture_dir, ".aw/records/plans/pending")
            executed = os.path.join(fixture_dir, ".aw/records/plans/executed")
            os.makedirs(pending, exist_ok=True)
            os.makedirs(executed, exist_ok=True)

            plan_text = (
                "# IPD: Placement Test\n"
                "- Date: 2026-10-01\n"
                "- Kind: primary\n"
                "- Scope: IN: test. OUT: none.\n"
                "- Scope-Paths: none\n"
                "- Item-Dependencies: none\n"
                "- Readiness: ready\n"
                "- Status: pending\n"
                "- Work-Kind: feature\n"
                "- Priority: low\n"
                "- From-Backlog: none\n"
                "- Blocks-Release: none\n"
                "- Set: testset\n"
                "- Order: 1\n"
                "- Highest E allocated: 01\n"
                "- Author: test\n"
                "- Id: pln001\n"
                "- Approval: none\n\n"
                "## Detailed Implementation Checklist (TODO)\n"
                "- [ ] E-01 Item\n"
                "  - Execution state: pending\n"
            )
            p1 = os.path.join(pending, "20261001-testset-01-pln001-test.ipd.md")
            p2 = os.path.join(executed, "20261001-testset-01-pln001-test.ipd.md")
            with open(p1, "w", encoding="utf-8") as f:
                f.write(plan_text)
            with open(p2, "w", encoding="utf-8") as f:
                f.write(plan_text.replace("- Status: pending", "- Status: executed"))

            # --agent surface: must exit 1 (not crash), emit 1 valid record, no ValueError on stderr
            proc_agent = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "check",
                    "all",
                    "--agent",
                    "--dir",
                    fixture_dir,
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                proc_agent.returncode,
                1,
                f"Expected exit 1, got {proc_agent.returncode}: {proc_agent.stderr}",
            )
            self.assertNotIn(
                "ValueError", proc_agent.stderr, "stderr must not contain ValueError"
            )
            self.assertNotIn(
                "Traceback", proc_agent.stderr, "stderr must not contain Traceback"
            )
            lines = [
                line.strip() for line in proc_agent.stdout.splitlines() if line.strip()
            ]
            self.assertEqual(
                len(lines), 1, f"Must emit exactly one record, got: {proc_agent.stdout}"
            )
            rec = json.loads(lines[0])
            self.assertEqual(rec.get("schema"), "aw.agent/v1")
            self.assertEqual(validate_agent_record(rec), [])
            self._assert_no_leaks(rec, resolved_root)

            # --json surface: no home path leak and no resolved root substring
            proc_json = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "check",
                    "all",
                    "--json",
                    "--dir",
                    fixture_dir,
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                proc_json.returncode,
                1,
                f"Expected exit 1, got {proc_json.returncode}: {proc_json.stderr}",
            )
            data = json.loads(proc_json.stdout)
            self._assert_no_leaks(data, resolved_root)
        finally:
            shutil.rmtree(fixture_dir, ignore_errors=True)

    def test_uninstalled_layout_recovery_no_leak(self) -> None:
        """Uninstalled layout missing recovery must not interpolate absolute root."""
        fixture_dir = self._create_fixture_repo()
        try:
            resolved_root = str(Path(fixture_dir).resolve())
            sys_dir = os.path.join(fixture_dir, ".aw/system")
            os.makedirs(sys_dir, exist_ok=True)
            with open(os.path.join(sys_dir, "VERSION"), "w", encoding="utf-8") as f:
                f.write("0.1.0\n")

            proc_json = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "check",
                    "all",
                    "--json",
                    "--dir",
                    fixture_dir,
                ],
                capture_output=True,
                text=True,
            )
            data = json.loads(proc_json.stdout)
            findings = [
                f
                for f in data.get("data", {}).get("policy_findings", [])
                if f.get("rule") == "check.system-layout-missing"
            ]
            self.assertGreaterEqual(
                len(findings), 1, "Must emit check.system-layout-missing"
            )
            self._assert_no_leaks(data, resolved_root)
        finally:
            shutil.rmtree(fixture_dir, ignore_errors=True)

    def test_ipd_lint_diagnostic_recovery_no_leak(self) -> None:
        """IPD lint diagnostics must emit repo-relative recovery paths."""
        fixture_dir = self._create_fixture_repo()
        try:
            resolved_root = str(Path(fixture_dir).resolve())
            pending = os.path.join(fixture_dir, ".aw/records/plans/pending")
            executed = os.path.join(fixture_dir, ".aw/records/plans/executed")
            os.makedirs(pending, exist_ok=True)
            os.makedirs(executed, exist_ok=True)

            # Site 1: pending plan failing lint (missing Scope, etc.)
            broken_pending = (
                "# IPD: Broken Pending\n"
                "- Date: 2026-10-01\n"
                "- Kind: primary\n"
                "- Status: pending\n"
                "- Set: setaaa (First Descriptive)\n"
                "- Order: 1\n"
                "- Id: pln001\n"
            )
            with open(
                os.path.join(pending, "20261001-setaaa-01-pln001-broken.ipd.md"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(broken_pending)

            # Site 2: terminal plan whose date >= cutover date but status disagrees with path
            mismatched_executed = (
                "# IPD: Executed Status Mismatch\n"
                "- Date: 2026-10-01\n"
                "- Kind: primary\n"
                "- Scope: IN: test. OUT: none.\n"
                "- Scope-Paths: none\n"
                "- Item-Dependencies: none\n"
                "- Readiness: ready\n"
                "- Status: approved\n"
                "- Work-Kind: feature\n"
                "- Priority: low\n"
                "- From-Backlog: none\n"
                "- Blocks-Release: none\n"
                "- Set: setaaa (First Descriptive)\n"
                "- Order: 2\n"
                "- Highest E allocated: 01\n"
                "- Author: test\n"
                "- Id: pln002\n"
                "- Approval: none\n\n"
                "## Detailed Implementation Checklist (TODO)\n"
                "- [ ] E-01 Item\n"
                "  - Execution state: pending\n"
            )
            with open(
                os.path.join(executed, "20261001-setaaa-02-pln002-two.ipd.md"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(mismatched_executed)

            proc_json = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "check",
                    "all",
                    "--json",
                    "--dir",
                    fixture_dir,
                ],
                capture_output=True,
                text=True,
            )
            data = json.loads(proc_json.stdout)
            lint_findings = [
                f
                for f in data.get("data", {}).get("policy_findings", [])
                if f.get("rule") == "check.ipd-lint-diagnostic"
            ]
            self.assertGreaterEqual(
                len(lint_findings), 2, "Must emit lint findings for both sites"
            )
            self._assert_no_leaks(data, resolved_root)
        finally:
            shutil.rmtree(fixture_dir, ignore_errors=True)

    def test_id6_and_setid_collision_detail_no_leak(self) -> None:
        """Collision detail strings must emit repo-relative paths for secondary paths."""
        fixture_dir = self._create_fixture_repo()
        try:
            resolved_root = str(Path(fixture_dir).resolve())
            pending = os.path.join(fixture_dir, ".aw/records/plans/pending")
            os.makedirs(pending, exist_ok=True)

            plan1 = (
                "# IPD: Plan One\n"
                "- Date: 2026-10-01\n"
                "- Kind: primary\n"
                "- Scope: IN: test. OUT: none.\n"
                "- Scope-Paths: none\n"
                "- Item-Dependencies: none\n"
                "- Readiness: ready\n"
                "- Status: pending\n"
                "- Work-Kind: feature\n"
                "- Priority: low\n"
                "- From-Backlog: none\n"
                "- Blocks-Release: none\n"
                "- Set: setaaa (First Descriptive)\n"
                "- Order: 1\n"
                "- Highest E allocated: 01\n"
                "- Author: test\n"
                "- Id: dup001\n"
                "- Approval: none\n\n"
                "## Detailed Implementation Checklist (TODO)\n"
                "- [ ] E-01 Item\n"
                "  - Execution state: pending\n"
            )
            plan2 = (
                "# IPD: Plan Two\n"
                "- Date: 2026-10-01\n"
                "- Kind: primary\n"
                "- Scope: IN: test. OUT: none.\n"
                "- Scope-Paths: none\n"
                "- Item-Dependencies: none\n"
                "- Readiness: ready\n"
                "- Status: pending\n"
                "- Work-Kind: feature\n"
                "- Priority: low\n"
                "- From-Backlog: none\n"
                "- Blocks-Release: none\n"
                "- Set: setaaa (Second Descriptive)\n"
                "- Order: 2\n"
                "- Highest E allocated: 01\n"
                "- Author: test\n"
                "- Id: dup001\n"
                "- Approval: none\n\n"
                "## Detailed Implementation Checklist (TODO)\n"
                "- [ ] E-01 Item\n"
                "  - Execution state: pending\n"
            )
            with open(
                os.path.join(pending, "20261001-setaaa-01-dup001-one.ipd.md"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(plan1)
            with open(
                os.path.join(pending, "20261001-setaaa-02-dup001-two.ipd.md"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(plan2)

            proc_json = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "check",
                    "all",
                    "--json",
                    "--dir",
                    fixture_dir,
                ],
                capture_output=True,
                text=True,
            )
            data = json.loads(proc_json.stdout)
            id6_coll = [
                f
                for f in data.get("data", {}).get("policy_findings", [])
                if f.get("rule") == "check.id6-collision"
            ]
            setid_coll = [
                f
                for f in data.get("data", {}).get("policy_findings", [])
                if f.get("rule") == "check.setid-collision"
            ]
            self.assertGreaterEqual(len(id6_coll), 1, "Must emit check.id6-collision")
            self.assertGreaterEqual(
                len(setid_coll), 1, "Must emit check.setid-collision"
            )
            self._assert_no_leaks(data, resolved_root)
        finally:
            shutil.rmtree(fixture_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

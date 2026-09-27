"""Behavioral tests for commit trailer attribution at finalize (Set trailread, 199u11).

Verifies:
1. OWN TRAILER DEMANDS: a commit carrying AW-Item with the plan's id6 requires a scope-reason
   even when it touches no declared path.
2. UNTRAILERED FALLS BACK: an untrailered out-of-scope commit falls back to commit cohesion
   (excused when it touches no declared path).
3. FOREIGN FALLS BACK: a commit carrying a foreign AW-Item falls back to cohesion and increments
   the foreign commit counter.
4. NO FALSE UNKNOWN->FOREIGN: when no commit touches declared territory (anchored=False), an
   untrailered out-of-scope commit is still fail-closed demanded.
5. _commit_run_ownership correctly classifies real commits as owned, foreign, or unknown.
6. END TO END WITH ORDER 1: aw commit stamps trailers that finalize reads back.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle as LC
from tests import support


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _completed_plan_text(
    *,
    plan_id: str = "abc123",
    scope_paths: str = "agent_workflows/demo.py, tests/test_demo.py",
) -> str:
    t = support.ready_plan_text(plan_id=plan_id, scope_paths=scope_paths)
    t = t.replace("- [ ] E-01 ", "- [x] E-01 ", 1).replace(
        "  - Execution state: pending", "  - Execution state: performed", 1
    )
    t = (
        t.replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
        .replace(
            "  - Observed evidence:\n", "  - Observed evidence: done, verified.\n", 1
        )
        .replace("  - Result: pending", "  - Result: pass", 1)
    )
    return t


def _write_plan(
    root: Path, text: str, name: str = "20260824-demo-01-abc123-demo.ipd.md"
) -> Path:
    d = root / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(text, encoding="utf-8")
    return p


class FinalizeTrailerAttributionTests(unittest.TestCase):
    """Behavioral tests verifying finalize attribution with AW-Item commit trailers."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()
        self.plan = _write_plan(self.root, _completed_plan_text())
        (self.root / "agent_workflows" / "demo.py").write_text("x\n", encoding="utf-8")
        (self.root / "tests" / "test_demo.py").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.root, check=True)
        res = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_case_1_own_trailer_demands(self) -> None:
        """Case (1): a commit trailered AW-Item: abc123 demands a scope reason."""
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        (self.root / "tests" / "test_demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py", "tests/test_demo.py"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        (self.root / "other.py").write_text("oos\n", encoding="utf-8")
        subprocess.run(["git", "add", "other.py"], cwd=self.root, check=True)
        msg = "oos\n\nAW-Run: run-20260926T000000Z-1\nAW-Item: abc123"
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=self.root, check=True)

        exit_code, message, evidence, findings = LC.finalize_precheck(
            self.root, self.plan
        )
        scope_audit = evidence.get("scope_audit", {})
        self.assertIn("other.py", scope_audit.get("out_of_scope_paths", []))
        self.assertNotIn("other.py", scope_audit.get("disregarded_unowned_paths", []))

        # Finalize without a reason for other.py refuses
        refused = LC.finalize(self.root, self.plan, "opencode/test", "done", apply=True)
        self.assertNotEqual(refused.exit_code, LC.EXIT_OK)

        # Finalize with a reason for other.py succeeds
        ok = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "done",
            apply=True,
            scope_reasons={"other.py": "legitimate out-of-scope work"},
        )
        self.assertEqual(ok.exit_code, LC.EXIT_OK, ok.message)

    def test_case_2_untrailered_falls_back(self) -> None:
        """Case (2): an untrailered commit falls back to cohesion (excused when disjoint)."""
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        (self.root / "other.py").write_text("oos\n", encoding="utf-8")
        subprocess.run(["git", "add", "other.py"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "oos"], cwd=self.root, check=True)

        exit_code, message, evidence, findings = LC.finalize_precheck(
            self.root, self.plan
        )
        scope_audit = evidence.get("scope_audit", {})
        self.assertNotIn("other.py", scope_audit.get("out_of_scope_paths", []))
        self.assertIn("other.py", scope_audit.get("disregarded_unowned_paths", []))
        self.assertEqual(evidence.get("attribution_source"), "commit-cohesion")

    def test_case_3_foreign_falls_back(self) -> None:
        """Case (3): a foreign-trailered commit falls back to cohesion and records count."""
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        (self.root / "other.py").write_text("oos\n", encoding="utf-8")
        subprocess.run(["git", "add", "other.py"], cwd=self.root, check=True)
        msg = "oos\n\nAW-Run: run-20260926T000000Z-1\nAW-Item: zzz999"
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=self.root, check=True)

        exit_code, message, evidence, findings = LC.finalize_precheck(
            self.root, self.plan
        )
        scope_audit = evidence.get("scope_audit", {})
        self.assertNotIn("other.py", scope_audit.get("out_of_scope_paths", []))
        self.assertIn("other.py", scope_audit.get("disregarded_unowned_paths", []))
        trailer_attr = evidence.get("trailer_attribution", {})
        self.assertEqual(trailer_attr.get("foreign_commits"), 1)

    def test_case_4_no_false_unknown_to_foreign(self) -> None:
        """Case (4): when no commit is anchored, an untrailered commit is still demanded."""
        # Note: no in-scope commit is made here
        (self.root / "other.py").write_text("oos\n", encoding="utf-8")
        subprocess.run(["git", "add", "other.py"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "oos"], cwd=self.root, check=True)

        exit_code, message, evidence, findings = LC.finalize_precheck(
            self.root, self.plan
        )
        scope_audit = evidence.get("scope_audit", {})
        self.assertIn("other.py", scope_audit.get("out_of_scope_paths", []))

    def test_case_5_commit_run_ownership(self) -> None:
        """Case (5): _commit_run_ownership correctly classifies commits on disk."""
        (self.root / "f1.txt").write_text("1\n")
        subprocess.run(["git", "add", "f1.txt"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "c1\n\nAW-Item: abc123"],
            cwd=self.root,
            check=True,
        )
        sha_owned = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()

        (self.root / "f2.txt").write_text("2\n")
        subprocess.run(["git", "add", "f2.txt"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "c2\n\nAW-Item: zzz999"],
            cwd=self.root,
            check=True,
        )
        sha_foreign = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()

        (self.root / "f3.txt").write_text("3\n")
        subprocess.run(["git", "add", "f3.txt"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "c3"], cwd=self.root, check=True)
        sha_unknown = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()

        (self.root / "f4.txt").write_text("4\n")
        subprocess.run(["git", "add", "f4.txt"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "c4\n\nAW-Run: run-20260926T000000Z-1"],
            cwd=self.root,
            check=True,
        )
        sha_run_only = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()

        self.assertEqual(
            LC._commit_run_ownership(self.root, sha_owned, "abc123"), "owned"
        )
        self.assertEqual(
            LC._commit_run_ownership(self.root, sha_owned, "zzz999"), "foreign"
        )
        self.assertEqual(
            LC._commit_run_ownership(self.root, sha_foreign, "abc123"), "foreign"
        )
        self.assertEqual(
            LC._commit_run_ownership(self.root, sha_unknown, "abc123"), "unknown"
        )
        self.assertEqual(
            LC._commit_run_ownership(self.root, sha_run_only, "abc123"), "unknown"
        )

    def test_case_6_end_to_end_with_order_1(self) -> None:
        """Case (6): Order 1 aw commit creates trailers that finalize reads back."""
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        (self.root / "other.py").write_text("oos\n", encoding="utf-8")
        env = dict(os.environ)
        env["AW_RUN_ID"] = "run-20260926T000000Z-1"
        env["AW_ITEM_ID6"] = "abc123"

        sub_res = subprocess.run(
            [
                "python3",
                "-m",
                "agent_workflows",
                "commit",
                "--no-plan",
                "-m",
                "oos",
                "--",
                "other.py",
            ],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            sub_res.returncode,
            0,
            f"aw commit failed:\n{sub_res.stderr}\n{sub_res.stdout}",
        )

        # Assert BOTH trailers were stamped on the produced commit before precheck
        run_tr = subprocess.check_output(
            ["git", "log", "-1", "--format=%(trailers:key=AW-Run,valueonly)"],
            cwd=self.root,
            text=True,
        ).strip()
        item_tr = subprocess.check_output(
            ["git", "log", "-1", "--format=%(trailers:key=AW-Item,valueonly)"],
            cwd=self.root,
            text=True,
        ).strip()
        self.assertEqual(run_tr, "run-20260926T000000Z-1")
        self.assertEqual(item_tr, "abc123")

        exit_code, message, evidence, findings = LC.finalize_precheck(
            self.root, self.plan
        )
        scope_audit = evidence.get("scope_audit", {})
        self.assertIn("other.py", scope_audit.get("out_of_scope_paths", []))
        self.assertNotIn("other.py", scope_audit.get("disregarded_unowned_paths", []))

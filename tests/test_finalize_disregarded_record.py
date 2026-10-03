"""Behavioral tests for recording disregarded out-of-scope paths in permanent finalize records (IPD 1dcl10, Set s9z85a).

Verifies the seven E-05 requirements:
(a) test_a_recorded: F-02 escaping shape records out-of-scope path in executed plan history
(b) test_b_lifecycle_commit: same path is in the lifecycle commit message
(c) test_c_clean_is_silent: finalize with clean delta writes neither reconciliation nor disregarded note
(d) test_d_foreign_is_not_claimed: foreign-trailered out-of-scope path is NOT named in the plan's history
(e) test_e_verdict_unchanged: exit codes and out_of_scope_paths for (a), (c), (d) match shipped behavior
(f) test_f_overlap_is_recorded: path touched by foreign commit and untrailered commit is recorded (F-13)
(g) test_g_volume_is_capped: 12 untrailered commits cap at 5 named paths, states total 12, audit has all 12 (F-06)
"""

from __future__ import annotations

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
    scope_paths: str = "agent_workflows/demo.py",
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


class FinalizeDisregardedRecordTests(unittest.TestCase):
    """Behavioral tests asserting the disregarded out-of-scope paths record and gate invariance."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        self.plan = _write_plan(self.root, _completed_plan_text())
        (self.root / "agent_workflows" / "demo.py").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.root, check=True)
        res = LC.begin(
            self.root, self.plan, "opencode/test", timestamp="2026-10-01T00:00:00Z"
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _get_executed_plan_content(self) -> str:
        executed_dir = self.root / ".aw" / "records" / "plans" / "executed"
        matches = list(executed_dir.glob("*abc123*.ipd.md"))
        self.assertTrue(matches, f"No executed plan found in {executed_dir}")
        return matches[0].read_text(encoding="utf-8")

    def _get_head_commit_message(self) -> str:
        rc, out, _err = LC._git(self.root, ["log", "-1", "--format=%B"])
        self.assertEqual(rc, 0)
        return out

    def test_a_recorded(self) -> None:
        """Case (a): F-02 escaping shape records out-of-scope path in executed plan history."""
        # 1. In-scope commit
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        # 2. Solo untrailered out-of-scope commit
        (self.root / "other.py").write_text("oos\n", encoding="utf-8")
        subprocess.run(["git", "add", "other.py"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "oos untrailered"], cwd=self.root, check=True
        )

        # 3. Finalize succeeds with exit 0
        res = LC.finalize(
            self.root, self.plan, "opencode/test", "execute demo", apply=True, env={}
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        # 4. Executed plan's text names other.py and attribution source
        content = self._get_executed_plan_content()
        self.assertIn("other.py", content)
        self.assertIn("commit-cohesion", content)

    def test_b_lifecycle_commit(self) -> None:
        """Case (b): The same path and attribution source appear in the lifecycle commit message."""
        # Setup identical to (a)
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        (self.root / "other.py").write_text("oos\n", encoding="utf-8")
        subprocess.run(["git", "add", "other.py"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "oos untrailered"], cwd=self.root, check=True
        )

        res = LC.finalize(
            self.root, self.plan, "opencode/test", "execute demo", apply=True, env={}
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        # Lifecycle commit message carries other.py and attribution_source
        commit_msg = self._get_head_commit_message()
        self.assertIn("other.py", commit_msg)
        self.assertIn("commit-cohesion", commit_msg)

    def test_c_clean_is_silent(self) -> None:
        """Case (c): A finalize with clean delta writes neither reconciliation nor disregarded note."""
        # In-scope commit only
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        res = LC.finalize(
            self.root, self.plan, "opencode/test", "execute demo", apply=True, env={}
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        content = self._get_executed_plan_content()
        self.assertNotIn("Scope reconciliation", content)
        self.assertNotIn("Scope attribution", content)
        self.assertNotIn("DISREGARDED", content)

        commit_msg = self._get_head_commit_message()
        self.assertNotIn("Scope reconciliation", commit_msg)
        self.assertNotIn("Scope attribution", commit_msg)

    def test_d_foreign_is_not_claimed(self) -> None:
        """Case (d): A path disregarded due to foreign AW-Item is NOT named in this plan's record."""
        # 1. In-scope commit
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        # 2. Foreign-trailered out-of-scope commit
        (self.root / "foreign.py").write_text("foreign\n", encoding="utf-8")
        subprocess.run(["git", "add", "foreign.py"], cwd=self.root, check=True)
        msg = "foreign\n\nAW-Run: run-foreign\nAW-Item: zzz999"
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=self.root, check=True)

        # Precheck verifies key classification
        exit_code, message, evidence, findings = LC.finalize_precheck(
            self.root, self.plan
        )
        scope_audit = evidence.get("scope_audit", {})
        self.assertIn(
            "foreign.py", scope_audit.get("disregarded_foreign_owned_paths", [])
        )
        self.assertNotIn(
            "foreign.py", scope_audit.get("disregarded_no_evidence_paths", [])
        )
        self.assertIn("foreign.py", scope_audit.get("disregarded_unowned_paths", []))

        res = LC.finalize(
            self.root, self.plan, "opencode/test", "execute demo", apply=True, env={}
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        content = self._get_executed_plan_content()
        self.assertNotIn("foreign.py", content)
        self.assertNotIn("Scope attribution", content)

        commit_msg = self._get_head_commit_message()
        self.assertNotIn("foreign.py", commit_msg)
        self.assertNotIn("Scope attribution", commit_msg)

    def test_e_verdict_unchanged(self) -> None:
        """Case (e): Finalize exit code and out_of_scope_paths equal shipped behavior for (a), (c), (d)."""
        # --- (a) shape: in-scope + untrailered out-of-scope ---
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        (self.root / "other.py").write_text("oos\n", encoding="utf-8")
        subprocess.run(["git", "add", "other.py"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "oos untrailered"], cwd=self.root, check=True
        )

        exit_code_a, msg_a, evidence_a, _ = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(exit_code_a, LC.EXIT_OK)
        self.assertEqual(
            evidence_a.get("scope_audit", {}).get("out_of_scope_paths"), []
        )
        self.assertIn(
            "other.py",
            evidence_a.get("scope_audit", {}).get("disregarded_unowned_paths", []),
        )
        preview_a = LC.finalize(
            self.root, self.plan, "opencode/test", "execute demo", apply=False, env={}
        )
        self.assertEqual(preview_a.exit_code, LC.EXIT_OK)

        # Also verify uncommitted working-tree change lands in no-evidence disregarded set (V-02d)
        (self.root / "uncommitted.py").write_text("dirty\n", encoding="utf-8")
        exit_code_u, _, evidence_u, _ = LC.finalize_precheck(self.root, self.plan)
        audit_u = evidence_u.get("scope_audit", {})
        self.assertIn(
            "uncommitted.py", audit_u.get("disregarded_no_evidence_paths", [])
        )
        self.assertNotIn(
            "uncommitted.py", audit_u.get("disregarded_foreign_owned_paths", [])
        )
        self.assertIn("uncommitted.py", audit_u.get("disregarded_unowned_paths", []))
        (self.root / "uncommitted.py").unlink()

        # Reset repo to base for (c) and (d) checks
        subprocess.run(["git", "reset", "--hard", "HEAD~2"], cwd=self.root, check=True)

        # --- (c) shape: clean delta (in-scope only) ---
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        exit_code_c, _, evidence_c, _ = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(exit_code_c, LC.EXIT_OK)
        self.assertEqual(
            evidence_c.get("scope_audit", {}).get("out_of_scope_paths"), []
        )
        self.assertEqual(
            evidence_c.get("scope_audit", {}).get("disregarded_unowned_paths"), []
        )
        preview_c = LC.finalize(
            self.root, self.plan, "opencode/test", "execute demo", apply=False, env={}
        )
        self.assertEqual(preview_c.exit_code, LC.EXIT_OK)

        # Reset repo for (d)
        subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=self.root, check=True)

        # --- (d) shape: foreign-trailered out-of-scope ---
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        (self.root / "foreign.py").write_text("foreign\n", encoding="utf-8")
        subprocess.run(["git", "add", "foreign.py"], cwd=self.root, check=True)
        msg_foreign = "foreign\n\nAW-Run: run-foreign\nAW-Item: zzz999"
        subprocess.run(
            ["git", "commit", "-q", "-m", msg_foreign], cwd=self.root, check=True
        )

        exit_code_d, _, evidence_d, _ = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(exit_code_d, LC.EXIT_OK)
        self.assertEqual(
            evidence_d.get("scope_audit", {}).get("out_of_scope_paths"), []
        )
        self.assertIn(
            "foreign.py",
            evidence_d.get("scope_audit", {}).get("disregarded_unowned_paths", []),
        )
        preview_d = LC.finalize(
            self.root, self.plan, "opencode/test", "execute demo", apply=False, env={}
        )
        self.assertEqual(preview_d.exit_code, LC.EXIT_OK)

    def test_f_overlap_is_recorded(self) -> None:
        """Case (f): F-13 overlap regression test - path written by foreign commit AND untrailered commit is recorded."""
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        # 1. Foreign-trailered commit touches shared.py
        (self.root / "shared.py").write_text("v1\n", encoding="utf-8")
        subprocess.run(["git", "add", "shared.py"], cwd=self.root, check=True)
        msg = "foreign commit touching shared\n\nAW-Run: run-foreign\nAW-Item: zzz999"
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=self.root, check=True)

        # 2. Untrailered commit touches the SAME shared.py again
        (self.root / "shared.py").write_text("v2\n", encoding="utf-8")
        subprocess.run(["git", "add", "shared.py"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "untrailered commit touching shared"],
            cwd=self.root,
            check=True,
        )

        # Precheck verifies overlap: shared.py is in BOTH sets
        exit_code, message, evidence, findings = LC.finalize_precheck(
            self.root, self.plan
        )
        scope_audit = evidence.get("scope_audit", {})
        self.assertIn(
            "shared.py", scope_audit.get("disregarded_foreign_owned_paths", [])
        )
        self.assertIn("shared.py", scope_audit.get("disregarded_no_evidence_paths", []))
        self.assertIn("shared.py", scope_audit.get("disregarded_unowned_paths", []))

        res = LC.finalize(
            self.root, self.plan, "opencode/test", "execute demo", apply=True, env={}
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        content = self._get_executed_plan_content()
        self.assertIn("shared.py", content)

        commit_msg = self._get_head_commit_message()
        self.assertIn("shared.py", commit_msg)

    def test_g_volume_is_capped(self) -> None:
        """Case (g): F-06 volume regression test - 12 untrailered commits cap at 5 named paths, total 12 stated."""
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "agent_workflows/demo.py"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "in-scope"], cwd=self.root, check=True
        )

        # Twelve untrailered co-worker commits
        for i in range(1, 13):
            path = self.root / f"coworker_{i:02d}.py"
            path.write_text(f"cw {i}\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", f"coworker_{i:02d}.py"], cwd=self.root, check=True
            )
            subprocess.run(
                ["git", "commit", "-q", "-m", f"coworker {i}"],
                cwd=self.root,
                check=True,
            )

        exit_code, message, evidence, findings = LC.finalize_precheck(
            self.root, self.plan
        )
        scope_audit = evidence.get("scope_audit", {})
        no_evidence_paths = scope_audit.get("disregarded_no_evidence_paths", [])
        self.assertEqual(len(no_evidence_paths), 12)

        res = LC.finalize(
            self.root, self.plan, "opencode/test", "execute demo", apply=True, env={}
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        content = self._get_executed_plan_content()
        # Behavioral cap assertions:
        # 1. Total 12 is stated
        self.assertIn("12", content)
        # 2. Residual count is stated (12 - 5 = 7 more)
        self.assertIn("7 more", content)
        # 3. Exactly 5 paths are named in the rendered text
        named_count = sum(1 for i in range(1, 13) if f"coworker_{i:02d}.py" in content)
        self.assertEqual(named_count, 5)

        commit_msg = self._get_head_commit_message()
        self.assertIn("12", commit_msg)
        self.assertIn("7 more", commit_msg)
        commit_named_count = sum(
            1 for i in range(1, 13) if f"coworker_{i:02d}.py" in commit_msg
        )
        self.assertEqual(commit_named_count, 5)

"""Behavioral tests for recording empty declared-scope deltas in finalize (IPD a8e2l8, Set emptyscope).

Verifies the six behaviours required by E-04:
(a) test_a_recorded: execution modifying neither declared path records empty declared delta and declared count in plan
(b) test_b_lifecycle_commit: same statement appears in the lifecycle commit message
(c) test_c_partial_work_is_silent: execution committing one of two declared paths writes no empty delta note
(d) test_d_grandfathered_is_silent: plan with no concrete Scope-Paths writes no empty delta note
(e) test_e_verdict_unchanged: exit codes, out_of_scope_paths and in_scope_unmodified match shipped behaviour for (a), (c), (d)
(f) test_f_volume_cap: plan declaring 7+ paths all unmodified caps at 5 named paths, states total count and residual
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle as LC
from tests import support
from tests.test_ipd_lifecycle_cli import (
    _commit_all,
    _completed_plan_text,
    _init_git,
    _write_plan,
)


class FinalizeEmptyDeclaredScopeTests(unittest.TestCase):
    """Behavioral tests asserting empty declared-scope delta recording and gate invariance."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir(parents=True, exist_ok=True)
        (self.root / "tests").mkdir(parents=True, exist_ok=True)
        (self.root / "agent_workflows" / "demo.py").write_text(
            "orig\n", encoding="utf-8"
        )
        (self.root / "tests" / "test_demo.py").write_text("orig\n", encoding="utf-8")
        self.plan = _write_plan(
            self.root,
            _completed_plan_text(
                plan_id="abc123",
                scope_paths="agent_workflows/demo.py, tests/test_demo.py",
            ),
            "20260824-demo-01-abc123-demo.ipd.md",
        )
        _commit_all(self.root, "init")
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
        """Case (a): Execution modifying neither declared path records empty delta and path count in plan."""
        exit_code, _msg, evidence, _ = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(exit_code, LC.EXIT_OK)
        audit = evidence.get("scope_audit", {})
        self.assertTrue(audit.get("all_declared_unmodified"))
        self.assertEqual(audit.get("out_of_scope_paths"), [])
        self.assertEqual(
            audit.get("in_scope_unmodified"),
            ["agent_workflows/demo.py", "tests/test_demo.py"],
        )

        acks = {
            p: "declared-but-unmodified (auto-acknowledged by aw oc run)"
            for p in audit.get("in_scope_unmodified", [])
        }
        res = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "exec demo",
            apply=True,
            scope_acks=acks,
            env={},
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        content = self._get_executed_plan_content()
        self.assertIn("no declared Scope-Paths were modified", content)
        self.assertIn("2 declared path(s)", content)
        self.assertIn("agent_workflows/demo.py", content)
        self.assertIn("tests/test_demo.py", content)

    def test_b_lifecycle_commit(self) -> None:
        """Case (b): The same statement appears in the lifecycle commit message."""
        exit_code, _msg, evidence, _ = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(exit_code, LC.EXIT_OK)
        audit = evidence.get("scope_audit", {})
        acks = {
            p: "declared-but-unmodified (auto-acknowledged by aw oc run)"
            for p in audit.get("in_scope_unmodified", [])
        }
        res = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "exec demo",
            apply=True,
            scope_acks=acks,
            env={},
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        commit_msg = self._get_head_commit_message()
        self.assertIn("no declared Scope-Paths were modified", commit_msg)
        self.assertIn("2 declared path(s)", commit_msg)
        self.assertIn("agent_workflows/demo.py", commit_msg)
        self.assertIn("tests/test_demo.py", commit_msg)

    def test_c_partial_work_is_silent(self) -> None:
        """Case (c): Execution committing one of two declared paths gets NO new note while reconciliation note remains."""
        (self.root / "agent_workflows" / "demo.py").write_text(
            "mod\n", encoding="utf-8"
        )
        _commit_all(self.root, "commit demo.py")

        exit_code, _msg, evidence, _ = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(exit_code, LC.EXIT_OK)
        audit = evidence.get("scope_audit", {})
        self.assertFalse(audit.get("all_declared_unmodified"))
        self.assertEqual(audit.get("out_of_scope_paths"), [])
        self.assertEqual(audit.get("in_scope_unmodified"), ["tests/test_demo.py"])

        acks = {
            "tests/test_demo.py": "declared-but-unmodified (auto-acknowledged by aw oc run)"
        }
        res = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "exec partial",
            apply=True,
            scope_acks=acks,
            env={},
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        content = self._get_executed_plan_content()
        self.assertIn(
            "in-scope-unmodified tests/test_demo.py: declared-but-unmodified", content
        )
        self.assertNotIn("no declared Scope-Paths were modified", content)
        self.assertNotIn("Scope delta", content)

        commit_msg = self._get_head_commit_message()
        self.assertIn(
            "in-scope-unmodified tests/test_demo.py: declared-but-unmodified",
            commit_msg,
        )
        self.assertNotIn("no declared Scope-Paths were modified", commit_msg)
        self.assertNotIn("Scope delta", commit_msg)

    def test_d_grandfathered_is_silent(self) -> None:
        """Case (d): A grandfathered plan with no declared fence gets no new note, pinning E-01's guard."""
        gf_plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id="gf1234", scope_paths="grandfathered"),
            "20260824-demo-02-gf1234-gf.ipd.md",
        )
        _commit_all(self.root, "add gf plan")
        res_begin = LC.begin(
            self.root, gf_plan, "opencode/test", timestamp="2026-10-01T00:00:00Z"
        )
        self.assertEqual(res_begin.exit_code, LC.EXIT_OK)

        exit_code, _msg, evidence, _ = LC.finalize_precheck(self.root, gf_plan)
        self.assertEqual(exit_code, LC.EXIT_OK)
        audit = evidence.get("scope_audit", {})
        self.assertTrue(audit.get("grandfathered"))
        self.assertFalse(audit.get("all_declared_unmodified"))
        self.assertEqual(audit.get("out_of_scope_paths"), [])
        self.assertEqual(audit.get("in_scope_unmodified"), [])

        res = LC.finalize(
            self.root, gf_plan, "opencode/test", "exec gf", apply=True, env={}
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        executed_gf = (
            self.root / ".aw" / "records" / "plans" / "executed" / gf_plan.name
        ).read_text(encoding="utf-8")
        self.assertNotIn("no declared Scope-Paths were modified", executed_gf)
        self.assertNotIn("Scope delta", executed_gf)

        commit_msg = self._get_head_commit_message()
        self.assertNotIn("no declared Scope-Paths were modified", commit_msg)
        self.assertNotIn("Scope delta", commit_msg)

    def test_e_verdict_unchanged(self) -> None:
        """Case (e): Finalize exit code, out_of_scope_paths, and in_scope_unmodified match shipped behavior for (a), (c), (d)."""
        # Shape (a): all unmodified
        code_a, _, ev_a, _ = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(code_a, LC.EXIT_OK)
        audit_a = ev_a.get("scope_audit", {})
        self.assertEqual(audit_a.get("out_of_scope_paths"), [])
        self.assertEqual(
            audit_a.get("in_scope_unmodified"),
            ["agent_workflows/demo.py", "tests/test_demo.py"],
        )
        preview_a = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "exec a",
            apply=False,
            scope_acks={
                p: "not-needed" for p in audit_a.get("in_scope_unmodified", [])
            },
            env={},
        )
        self.assertEqual(preview_a.exit_code, LC.EXIT_OK)

        # Shape (c): partial work
        (self.root / "agent_workflows" / "demo.py").write_text(
            "mod\n", encoding="utf-8"
        )
        _commit_all(self.root, "commit demo.py")
        code_c, _, ev_c, _ = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(code_c, LC.EXIT_OK)
        audit_c = ev_c.get("scope_audit", {})
        self.assertEqual(audit_c.get("out_of_scope_paths"), [])
        self.assertEqual(audit_c.get("in_scope_unmodified"), ["tests/test_demo.py"])
        preview_c = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "exec c",
            apply=False,
            scope_acks={"tests/test_demo.py": "not-needed"},
            env={},
        )
        self.assertEqual(preview_c.exit_code, LC.EXIT_OK)

        # Shape (d): grandfathered
        gf_plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id="gf5678", scope_paths="grandfathered"),
            "20260824-demo-03-gf5678-gf.ipd.md",
        )
        _commit_all(self.root, "add gf plan")
        res_begin = LC.begin(
            self.root, gf_plan, "opencode/test", timestamp="2026-10-01T00:00:00Z"
        )
        self.assertEqual(res_begin.exit_code, LC.EXIT_OK)
        code_d, _, ev_d, _ = LC.finalize_precheck(self.root, gf_plan)
        self.assertEqual(code_d, LC.EXIT_OK)
        audit_d = ev_d.get("scope_audit", {})
        self.assertEqual(audit_d.get("out_of_scope_paths"), [])
        self.assertEqual(audit_d.get("in_scope_unmodified"), [])
        preview_d = LC.finalize(
            self.root, gf_plan, "opencode/test", "exec d", apply=False, env={}
        )
        self.assertEqual(preview_d.exit_code, LC.EXIT_OK)

    def test_f_volume_cap(self) -> None:
        """Case (f): Plan declaring 7+ paths all unmodified caps at 5 named paths, states total and residual."""
        paths = [f"agent_workflows/file_{i:02d}.py" for i in range(1, 9)]
        for p in paths:
            (self.root / p).write_text(f"# {p}\n", encoding="utf-8")
        scope_str = ", ".join(paths)
        vol_plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id="vol123", scope_paths=scope_str),
            "20260824-demo-04-vol123-vol.ipd.md",
        )
        _commit_all(self.root, "add vol files and plan")
        res_begin = LC.begin(
            self.root, vol_plan, "opencode/test", timestamp="2026-10-01T00:00:00Z"
        )
        self.assertEqual(res_begin.exit_code, LC.EXIT_OK)

        exit_code, _msg, evidence, _ = LC.finalize_precheck(self.root, vol_plan)
        self.assertEqual(exit_code, LC.EXIT_OK)
        audit = evidence.get("scope_audit", {})
        self.assertTrue(audit.get("all_declared_unmodified"))
        self.assertEqual(len(audit.get("in_scope_unmodified", [])), 8)

        acks = {p: "not-needed" for p in paths}
        res = LC.finalize(
            self.root,
            vol_plan,
            "opencode/test",
            "exec vol",
            apply=True,
            scope_acks=acks,
            env={},
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

        executed_vol = (
            self.root / ".aw" / "records" / "plans" / "executed" / vol_plan.name
        ).read_text(encoding="utf-8")

        # Behavioral cap assertions on plan history line:
        hist_line = next(
            line for line in executed_vol.splitlines() if "Scope delta" in line
        )
        delta_note = support.final_section(
            hist_line, "[Scope delta", next_marker="\n", anchored=False
        )
        self.assertIn("8 declared path(s)", delta_note)
        self.assertIn("3 more", delta_note)
        named_in_note = sum(1 for p in paths if p in delta_note)
        self.assertEqual(named_in_note, 5)

        # Behavioral cap assertions on lifecycle commit message:
        commit_msg = self._get_head_commit_message()
        self.assertIn("8 declared path(s)", commit_msg)
        self.assertIn("3 more", commit_msg)
        commit_note_line = next(
            line for line in commit_msg.splitlines() if "Scope delta" in line
        )
        commit_delta_note = support.final_section(
            commit_note_line, "[Scope delta", next_marker="\n", anchored=False
        )
        named_in_commit = sum(1 for p in paths if p in commit_delta_note)
        self.assertEqual(named_in_commit, 5)

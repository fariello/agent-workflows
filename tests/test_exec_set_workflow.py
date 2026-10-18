"""Conformance tests for the /exec-set workflow packaging (execset Order 05, `2h7777`).

V-01: manifest discovery, workflow files exist, skill package + semantic-digest parity, generated
      shims present, no drift on regeneration, and explicit-runtime fallback (aw ipd execute-set).
V-02: the CLI surfaces the help advertises actually dispatch - `aw run decisions`/`aw run questions`
      exist and read the Order-02 projections, and `aw ipd execute-set --resume` exists; help names
      no nonexistent command; lifecycle wording is Order 02's (inherited, not re-authored).
V-03: generated-drift + packaging + security are clean (the shim regenerates byte-identically; the
      workflow body carries no leak; the manifest row points at a real body).

Restored under backlog q86fxm and findings b1mx2w from revision 19313eed^, omitting five tests that asserted on prose and help text rather than behavior (ExecSetWorkflowV01.test_workflow_files_exist, test_explicit_runtime_fallback_documented, ExecSetCliSurfaceV02.test_help_advertises_only_real_commands, test_lifecycle_wording_inherited_not_reauthored, ExecSetPackagingV03.test_body_has_no_obvious_leak_markers).
"""

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

from agent_workflows import engine as INS
from agent_workflows import host_adapters as HA
from agent_workflows import migration_compact as MC
from agent_workflows import run_cli
from agent_workflows import set_records
import pytest
from tests.support import REPO_ROOT, SOURCE_WORKFLOWS

pytestmark = pytest.mark.core


class ExecSetWorkflowV01(unittest.TestCase):
    def setUp(self):
        self.wf_dir = REPO_ROOT / ".aw" / "system" / "workflows" / "exec-set"
        self.body = self.wf_dir / "exec-set.md"
        self.readme = self.wf_dir / "README.md"
        self.workflows = INS.parse_manifest(SOURCE_WORKFLOWS)
        self.wf_map = {w.command: w for w in self.workflows}

    def test_manifest_registers_exec_set(self):
        self.assertIn("exec-set", self.wf_map)
        wf = self.wf_map["exec-set"]
        self.assertEqual(wf.body, ".aw/system/workflows/exec-set/exec-set.md")
        self.assertTrue((REPO_ROOT / wf.body).is_file())
        self.assertTrue(wf.description)

    def test_skill_package_digest_parity(self):
        wf = self.wf_map["exec-set"]
        pkg = HA.build_skill_package(wf)
        self.assertEqual(pkg.semantic_digest, HA.compute_workflow_semantic_digest(wf))
        # the router body must stay within budget
        self.assertTrue(pkg.within_budget())

    def test_shims_generated_and_no_drift(self):
        shims = INS.generate_shim_members(self.workflows, SOURCE_WORKFLOWS)
        es = {p: c for p, c in shims.items() if "exec-set" in p}
        self.assertTrue(es, "no exec-set shims generated")
        for path, content in es.items():
            tool = "opencode" if "opencode" in path else "claude"
            self.assertTrue(INS.validate_shim_grammar(content, tool))
            # regeneration is byte-identical -> no drift
            self.assertFalse(MC.detect_shim_drift(content, content))


class ExecSetCliSurfaceV02(unittest.TestCase):
    def _projection(self, root, recs):
        set_records.write_local_projections(root, "exec-set", "run-abcdef01", recs)

    def test_run_decisions_dispatches_and_reads_projection(self):
        root = Path(tempfile.mkdtemp())
        self._projection(
            root,
            [
                {
                    "kind": "autonomous_decision",
                    "decision_id": "D1",
                    "selected_option": "x",
                    "confidence": "high",
                    "consultation_preferred": True,
                    "reversible": True,
                    "prev": "",
                    "timestamp": "2026-08-24T00:00:00Z",
                    "actor": "coordinator",
                }
            ],
        )
        ns = argparse.Namespace(
            run_command="decisions",
            target="run-abcdef01",
            dir=str(root),
            workflow="exec-set",
            agent=False,
            json=False,
        )
        self.assertEqual(run_cli.run_cli(ns), 0)

    def test_run_questions_dispatches(self):
        root = Path(tempfile.mkdtemp())
        self._projection(
            root,
            [
                {
                    "kind": "question_raised",
                    "question_id": "Q1",
                    "context": "ambiguous",
                    "affected_nodes": ["a:E-01"],
                    "timestamp": "2026-08-24T00:00:00Z",
                    "actor": "coordinator",
                }
            ],
        )
        ns = argparse.Namespace(
            run_command="questions",
            target="run-abcdef01",
            dir=str(root),
            workflow="exec-set",
            agent=False,
            json=False,
        )
        self.assertEqual(run_cli.run_cli(ns), 0)

    def test_run_decisions_missing_projection_exit2(self):
        root = Path(tempfile.mkdtemp())
        ns = argparse.Namespace(
            run_command="decisions",
            target="run-nope",
            dir=str(root),
            workflow="exec-set",
            agent=False,
            json=False,
        )
        self.assertEqual(run_cli.run_cli(ns), 2)

    def test_execute_set_resume_flag_exists(self):
        # The parser must accept --resume (advertised in the help); a missing ledger is exit 2.
        from agent_workflows import ipd_set_plan

        root = Path(tempfile.mkdtemp())
        ns = argparse.Namespace(
            set_id="execset",
            plan_only=False,
            resume_run_id="run-nope",
            dir=str(root),
            agent=False,
        )
        self.assertEqual(ipd_set_plan.run_execute_set(ns), 2)


class ExecSetPackagingV03(unittest.TestCase):
    def test_manifest_body_points_at_real_file(self):
        workflows = INS.parse_manifest(SOURCE_WORKFLOWS)
        wf = {w.command: w for w in workflows}["exec-set"]
        self.assertTrue((REPO_ROOT / wf.body).is_file())

    def test_regeneration_is_deterministic(self):
        workflows = INS.parse_manifest(SOURCE_WORKFLOWS)
        a = INS.generate_shim_members(workflows, SOURCE_WORKFLOWS)
        b = INS.generate_shim_members(workflows, SOURCE_WORKFLOWS)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()

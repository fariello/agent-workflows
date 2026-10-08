"""Tests for recording refusal findings at orchestrator retirement (plan vvqr34)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import coverage_record
from agent_workflows import ipd_lifecycle as LC
from agent_workflows import render_stream as rs_render
from agent_workflows import runner_shared as rs
from tests import support
from tests.test_orchestrator_retirement import _init_git_repo, _write_conforming_plan


class FinalizeRefusalFindingsTests(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        LC.clear_checkout_control_root_cache()
        self.addCleanup(LC.clear_checkout_control_root_cache)
        _init_git_repo(self.root)

    def test_orchestrator_retirement_refusal_findings_recorded(self) -> None:
        """Case (a): an unknown front-matter field causes retirement lint refusal with IPD-M103 recorded."""
        _write_conforming_plan(
            self.root,
            "executed",
            plan_id="chi001",
            set_id="set001",
            order=1,
            status="executed",
            kind="child",
        )
        orch_path = _write_conforming_plan(
            self.root,
            "pending",
            plan_id="orc001",
            set_id="set001",
            order=0,
            status="approved",
            kind="orchestrator",
        )
        coverage_record.write(
            orch_path, verdict=coverage_record.COVERAGE_PASS, commit=False
        )

        text = orch_path.read_text(encoding="utf-8")
        self.assertIn("- Concern: TODO.\n", text)
        text = text.replace(
            "- Concern: TODO.\n",
            "- Concern: TODO.\n- Bogus-Field: x\n",
        )
        orch_path.write_text(text, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "init set"], cwd=self.root, check=True)

        run_dir = rs.state_root(self.root) / "run-20261006T120000Z-111111"
        run_dir.mkdir(parents=True, exist_ok=True)
        item = {
            "position": 1,
            "id6": "orc001",
            "setid": "set001",
            "action": "orchestrate",
            "kind": "orchestrator",
            "status": "queued",
            "dependencies": [],
            "attempts": [],
        }
        state = {
            "repo": str(self.root),
            "run_id": "run-20261006T120000Z-111111",
            "queue": [item],
        }

        decision = rs.dispatch_orchestrator_item(
            self.root,
            run_dir,
            state,
            item,
            actor="tester",
            terminal_states={"failed-safely", "fail-depend"},
            success_states={"executed"},
        )

        self.assertEqual(decision.outcome, rs.ORCH_DISPATCH_TERMINATE)
        self.assertEqual(decision.reason, rs.ORCH_REASON_FINALIZE_REFUSED)

        ref = rs_render.refusal_of_item(item)
        self.assertIsNotNone(ref)
        self.assertIn("IPD-M103", ref.reason)
        self.assertIn("Bogus-Field", ref.reason)

        self.assertIn("IPD-M103", item["orchestrator_refusal_detail"])
        self.assertIn("Bogus-Field", item["orchestrator_refusal_detail"])

        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        deferred = [e for e in events if e.get("event") == "orchestrator-deferred"]
        self.assertEqual(len(deferred), 1)
        self.assertIn("IPD-M103", deferred[0]["detail"])
        self.assertIn("Bogus-Field", deferred[0]["detail"])

        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        env = dict(os.environ)
        env["AW_NO_REEXEC"] = "1"
        env["AW_NONINTERACTIVE"] = "1"
        env.pop("AW_EXECUTION_ROLE", None)

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "runs",
                "--dir",
                str(self.root),
                "--no-color",
            ],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, f"runs failed: {proc.stderr}")
        self.assertIn("IPD-M103", proc.stdout)
        self.assertIn("Bogus-Field", proc.stdout)

        proc_json = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "runs",
                "--dir",
                str(self.root),
                "--json",
            ],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc_json.returncode, 0, f"runs --json failed: {proc_json.stderr}"
        )
        self.assertIn("IPD-M103", proc_json.stdout)
        self.assertIn("Bogus-Field", proc_json.stdout)

        summary_table = rs_render.render_run_summary_table(state)
        self.assertIn("IPD-M103", summary_table)
        self.assertIn("Bogus-Field", summary_table)

    def test_no_findings_preserves_old_detail(self) -> None:
        """Case (b): empty findings preserves unchanged old refusal detail."""
        _write_conforming_plan(
            self.root,
            "executed",
            plan_id="chi002",
            set_id="set002",
            order=1,
            status="executed",
            kind="child",
        )
        orch_path = _write_conforming_plan(
            self.root,
            "pending",
            plan_id="orc002",
            set_id="set002",
            order=0,
            status="approved",
            kind="orchestrator",
        )
        coverage_record.write(
            orch_path, verdict=coverage_record.COVERAGE_PASS, commit=False
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init set002"], cwd=self.root, check=True
        )

        class _ResultDouble:
            exit_code = 1
            message = "some transition error"
            findings = ()

        run_dir = rs.state_root(self.root) / "run-nofindings"
        run_dir.mkdir(parents=True, exist_ok=True)
        item = {
            "position": 1,
            "id6": "orc002",
            "setid": "set002",
            "action": "orchestrate",
            "kind": "orchestrator",
            "status": "queued",
            "dependencies": [],
            "attempts": [],
        }
        state = {
            "repo": str(self.root),
            "run_id": "run-nofindings",
            "queue": [item],
        }
        with unittest.mock.patch.object(
            LC, "retire_orchestrator", return_value=_ResultDouble()
        ):
            decision = rs.dispatch_orchestrator_item(
                self.root,
                run_dir,
                state,
                item,
                actor="tester",
                terminal_states={"failed-safely", "fail-depend"},
                success_states={"executed"},
            )
        self.assertEqual(
            decision.detail, "retirement transition refused: some transition error"
        )

        class _ResultNoAttr:
            exit_code = 1
            message = "no findings attribute"

        with unittest.mock.patch.object(
            LC, "retire_orchestrator", return_value=_ResultNoAttr()
        ):
            decision2 = rs.dispatch_orchestrator_item(
                self.root,
                run_dir,
                state,
                item,
                actor="tester",
                terminal_states={"failed-safely", "fail-depend"},
                success_states={"executed"},
            )
        self.assertEqual(
            decision2.detail, "retirement transition refused: no findings attribute"
        )

    def test_refusal_findings_text_cap(self) -> None:
        """Case (c): calling refusal_findings_text with 25 findings caps at 20 and counts remainder."""
        findings = [f"CODE{i:02d} message {i}" for i in range(25)]
        text = rs.refusal_findings_text(findings, cap=20)
        self.assertTrue(text.startswith("findings (25): "))
        for i in range(20):
            self.assertIn(f"CODE{i:02d} message {i}", text)
        for i in range(20, 25):
            self.assertNotIn(f"CODE{i:02d} message {i}", text)
        self.assertIn("; ... and 5 more", text)

        self.assertEqual(rs.refusal_findings_text(()), "")
        self.assertEqual(rs.refusal_findings_text(None), "")
        self.assertEqual(rs.refusal_findings_text([]), "")

    def test_child_finalize_prints_findings_exactly_once(self) -> None:
        """Case (d): aw ipd finalize on a child plan prints each IPD-S404 finding line exactly once."""
        with tempfile.TemporaryDirectory() as td:
            repo_dir = Path(td)
            _init_git_repo(repo_dir)

            (repo_dir / "target.py").write_text("# target\n", encoding="utf-8")
            subprocess.run(["git", "add", "target.py"], cwd=repo_dir, check=True)
            subprocess.run(
                ["git", "commit", "-m", "initial commit"], cwd=repo_dir, check=True
            )

            child_path = _write_conforming_plan(
                repo_dir,
                "pending",
                plan_id="chi003",
                set_id="set003",
                order=1,
                status="approved",
                kind="child",
            )
            content = child_path.read_text(encoding="utf-8")
            content = content.replace(
                "- Scope-Paths: grandfathered", "- Scope-Paths: target.py"
            )
            child_path.write_text(content, encoding="utf-8")

            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
            subprocess.run(
                ["git", "commit", "-m", "add child plan"], cwd=repo_dir, check=True
            )

            env = dict(os.environ)
            env["AW_NO_REEXEC"] = "1"
            env["AW_NONINTERACTIVE"] = "1"
            env.pop("AW_EXECUTION_ROLE", None)

            begin_res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "ipd",
                    "begin",
                    child_path.name,
                    "--actor",
                    "tester",
                ],
                cwd=repo_dir,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                begin_res.returncode,
                f"begin failed: {begin_res.stdout} {begin_res.stderr}",
            )

            finalize_res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "ipd",
                    "finalize",
                    child_path.name,
                    "--actor",
                    "tester",
                    "--message",
                    "test finalize",
                    "--apply",
                ],
                cwd=repo_dir,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(
                0,
                finalize_res.returncode,
                "finalize should refuse on pending E items",
            )
            s404_lines = [
                line.strip()
                for line in finalize_res.stdout.splitlines()
                if "IPD-S404" in line
            ]
            self.assertGreater(
                len(s404_lines), 0, "must have at least one IPD-S404 finding"
            )
            for line in s404_lines:
                self.assertEqual(
                    finalize_res.stdout.count(line),
                    1,
                    f"finding line {line!r} must appear exactly once in stdout",
                )

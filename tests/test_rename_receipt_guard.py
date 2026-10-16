"""Outcome tests: rename/group citation rewrites skip in-flight plans (IPD 69pxm5).

A citing plan holding a begin receipt has its Scope-Paths and E/V action blocks frozen, so a
rename/regroup must not rewrite citations inside it. Every test drives the real CLI (`cli.main`)
against a scratch git repo under the system temp dir and asserts only on exit codes, printed
output, machine records and file bytes (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import agent_schema, cli, ipd_lifecycle

SPEC = "20260701-grp-01-s11111-my-spec.spec.md"
TARGET_PLAN = "20260701-p33333-01-p33333-tgt.ipd.md"
RESEARCH = "20260701-seta-01-r44444-topic.reference-research.md"
IN_FLIGHT = "20260701-x-01-p22222-x.ipd.md"
SIBLING = "20260701-y-01-p55555-y.ipd.md"
SKIP_MARK = "--- SKIPPED citation rewrite in .aw/records/plans/pending/" + IN_FLIGHT


def _plan_text(id6: str, cite: str, *, in_action_only: bool = False) -> str:
    head = f"# IPD: {id6}\n\n- Date: 2026-07-01\n- Id: {id6}\n- Status: approved\n- Set: x\n- Order: 1\n"
    if in_action_only:
        head += "- Scope-Paths: agent_workflows/x.py\n"
    else:
        head += f"- Scope-Paths: {cite}\n"
    return (
        head
        + "\n## Detailed Implementation Checklist (TODO)\n\n"
        + f"- [ ] E-01 Update the behavior described by {cite}.\n"
        + "  - Execution state: pending\n"
    )


class _GuardCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_rename_guard_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "t@e.com"],
            ["git", "config", "user.name", "T"],
        ):
            subprocess.run(cmd, cwd=self.tmp, check=True)
        cfg = self.tmp / ".aw" / "config"
        cfg.mkdir(parents=True)
        (cfg / "project.json").write_text(
            '{"cutovers": {"spec_id6": "2026-06-01"}}', encoding="utf-8"
        )
        self.specs = self.tmp / ".aw" / "records" / "specs"
        self.plans = self.tmp / ".aw" / "records" / "plans" / "pending"
        self.research = self.tmp / ".aw" / "records" / "research"
        for d in (self.specs, self.plans, self.research):
            d.mkdir(parents=True)
        (self.specs / SPEC).write_text(
            "# Spec: My\n\n- Date: 2026-07-01\n- Id: s11111\n- Set: grp\n- Status: draft\n",
            encoding="utf-8",
        )
        (self.plans / TARGET_PLAN).write_text(
            "# IPD: tgt\n\n- Date: 2026-07-01\n- Id: p33333\n- Status: draft\n- Set: p33333\n- Order: 1\n",
            encoding="utf-8",
        )
        (self.research / RESEARCH).write_text(
            "# Research: topic\n\n- Date: 2026-07-01\n- Id: r44444\n- Set: seta\n",
            encoding="utf-8",
        )

    def _cite(self, cite: str, *, in_action_only: bool = False, receipt: bool = True):
        self.in_flight = self.plans / IN_FLIGHT
        self.in_flight.write_text(
            _plan_text("p22222", cite, in_action_only=in_action_only), encoding="utf-8"
        )
        self.sibling = self.plans / SIBLING
        self.sibling.write_text(_plan_text("p55555", cite), encoding="utf-8")
        self.test_file = self.tmp / "tests" / "test_cites.py"
        self.test_file.parent.mkdir(exist_ok=True)
        self.test_file.write_text(f"# see {cite}\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.tmp, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp, check=True)
        if receipt:
            rp = ipd_lifecycle.receipt_path_for(self.tmp, "p22222")
            rp.parent.mkdir(parents=True, exist_ok=True)
            rp.write_text("{}", encoding="utf-8")
        self.before = {
            p: p.read_bytes() for p in (self.in_flight, self.sibling, self.test_file)
        }

    def _run(self, argv):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            try:
                rc = cli.main(argv + ["--dir", str(self.tmp)])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue()

    def _changed(self, path: Path) -> bool:
        return path.read_bytes() != self.before[path]

    def _assert_guarded(self, rc: int, out: str, new_name: str):
        self.assertEqual(rc, 0, out)
        self.assertFalse(self._changed(self.in_flight), out)
        self.assertTrue(self._changed(self.sibling), out)
        self.assertIn(new_name, self.sibling.read_text(encoding="utf-8"))
        self.assertIn(SKIP_MARK, out)


class TestRenameReceiptGuard(_GuardCase):
    def test_a_group_specs_skips_in_flight_plan(self):
        self._cite(SPEC)
        rc, out = self._run(
            [
                "group",
                "specs",
                "s11111",
                "--set",
                "newgrp",
                "--rename",
                "--apply",
                "--no-commit",
            ]
        )
        self._assert_guarded(rc, out, "20260701-newgrp-01-s11111-my-spec.spec.md")

    def test_b_rename_plans_skips_in_flight_plan(self):
        self._cite(TARGET_PLAN)
        rc, out = self._run(
            ["rename", "plans", "p33333", "--slug", "zz", "--apply", "--no-commit"]
        )
        self._assert_guarded(rc, out, "20260701-p33333-01-p33333-zz.ipd.md")

    def test_c_rename_research_skips_in_flight_plan(self):
        self._cite(f".aw/records/research/{RESEARCH}")
        rc, out = self._run(
            ["rename", "research", "r44444", "--slug", "zz", "--apply", "--no-commit"]
        )
        self._assert_guarded(
            rc, out, "20260701-seta-01-r44444-zz.reference-research.md"
        )

    def test_d_citation_in_action_block_is_also_left_unchanged(self):
        self._cite(SPEC, in_action_only=True)
        rc, out = self._run(
            [
                "group",
                "specs",
                "s11111",
                "--set",
                "newgrp",
                "--rename",
                "--apply",
                "--no-commit",
            ]
        )
        self._assert_guarded(rc, out, "20260701-newgrp-01-s11111-my-spec.spec.md")
        self.assertIn(SPEC, self.in_flight.read_text(encoding="utf-8"))

    def test_e_non_plan_citing_file_still_rewritten(self):
        self._cite(SPEC)
        rc, out = self._run(
            [
                "group",
                "specs",
                "s11111",
                "--set",
                "newgrp",
                "--rename",
                "--apply",
                "--no-commit",
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertFalse(self._changed(self.in_flight))
        self.assertIn(
            "20260701-newgrp-01-s11111-my-spec.spec.md",
            self.test_file.read_text(encoding="utf-8"),
        )

    def test_f_preview_reports_skip_and_no_would_rewrite_for_in_flight(self):
        self._cite(SPEC)
        rc, out = self._run(["group", "specs", "s11111", "--set", "newgrp", "--rename"])
        self.assertEqual(rc, 0, out)
        self.assertIn(SKIP_MARK, out)
        would = [ln for ln in out.splitlines() if "would rewrite" in ln]
        self.assertTrue(any(SIBLING in ln for ln in would), out)
        self.assertFalse(any(IN_FLIGHT in ln for ln in would), out)
        for p in self.before:
            self.assertFalse(self._changed(p))

    def test_g_no_receipt_means_plan_is_rewritten(self):
        self._cite(SPEC, receipt=False)
        rc, out = self._run(
            [
                "group",
                "specs",
                "s11111",
                "--set",
                "newgrp",
                "--rename",
                "--apply",
                "--no-commit",
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertTrue(self._changed(self.in_flight), out)
        self.assertNotIn("SKIPPED", out)

    def test_h_machine_output_carries_skip_note(self):
        self._cite(SPEC)
        rc, out = self._run(
            ["group", "specs", "s11111", "--set", "newgrp", "--rename", "--agent"]
        )
        self.assertEqual(rc, 0, out)
        lines = [ln for ln in out.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1, out)
        rec = json.loads(lines[0])
        agent_schema.assert_valid_agent_record(rec)
        self.assertIn("notes", rec["evidence"])

        rc, out = self._run(
            ["group", "specs", "s11111", "--set", "newgrp", "--rename", "--json"]
        )
        self.assertEqual(rc, 0, out)
        data = json.loads(out)
        self.assertTrue(any(SKIP_MARK in n for n in data["data"]["notes"]), data)

    def test_i_rename_plans_refuses_in_flight_target(self):
        self._cite(SPEC)
        rc, out = self._run(
            ["rename", "plans", "p22222", "--slug", "renamed", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 2, out)
        self.assertIn("cannot rename or regroup in-flight plan p22222", out)
        self.assertIn("live begin receipt present", out)
        self.assertTrue(self.in_flight.exists())
        self.assertFalse(self._changed(self.in_flight))
        self.assertFalse((self.plans / "20260701-x-01-p22222-renamed.ipd.md").exists())

    def test_j_preview_rename_plans_refuses_in_flight_target(self):
        self._cite(SPEC)
        rc, out = self._run(["rename", "plans", "p22222", "--slug", "renamed"])
        self.assertEqual(rc, 2, out)
        self.assertIn("cannot rename or regroup in-flight plan p22222", out)
        self.assertIn("live begin receipt present", out)
        self.assertNotIn("--- would rename", out)
        self.assertTrue(self.in_flight.exists())
        self.assertFalse(self._changed(self.in_flight))

    def test_k_group_plans_refuses_in_flight_target(self):
        self._cite(SPEC)
        # With --rename
        rc, out = self._run(
            [
                "group",
                "plans",
                "p22222",
                "--set",
                "newset",
                "--rename",
                "--apply",
                "--no-commit",
            ]
        )
        self.assertEqual(rc, 2, out)
        self.assertIn("cannot rename or regroup in-flight plan p22222", out)
        self.assertIn("live begin receipt present", out)
        self.assertTrue(self.in_flight.exists())
        self.assertFalse(self._changed(self.in_flight))

        # Metadata-only (without --rename)
        rc, out = self._run(
            [
                "group",
                "plans",
                "p22222",
                "--set",
                "newset",
                "--apply",
                "--no-commit",
            ]
        )
        self.assertEqual(rc, 2, out)
        self.assertIn("cannot rename or regroup in-flight plan p22222", out)
        self.assertIn("live begin receipt present", out)
        self.assertTrue(self.in_flight.exists())
        self.assertFalse(self._changed(self.in_flight))

    def test_l_batch_group_atomicity_refuses_when_one_target_is_in_flight(self):
        self._cite(SPEC)
        # Sibling (p55555) is not in flight; p22222 is in flight. Neither should be modified.
        rc, out = self._run(
            [
                "group",
                "plans",
                "p55555",
                "p22222",
                "--set",
                "newset",
                "--rename",
                "--apply",
                "--no-commit",
            ]
        )
        self.assertEqual(rc, 2, out)
        self.assertIn("cannot rename or regroup in-flight plan p22222", out)
        self.assertTrue(self.sibling.exists())
        self.assertFalse(self._changed(self.sibling))
        self.assertTrue(self.in_flight.exists())
        self.assertFalse(self._changed(self.in_flight))

    def test_m_machine_output_refuses_in_flight_target(self):
        self._cite(SPEC)
        rc, out = self._run(
            [
                "rename",
                "plans",
                "p22222",
                "--slug",
                "renamed",
                "--apply",
                "--no-commit",
                "--agent",
            ]
        )
        self.assertEqual(rc, 2, out)
        lines = [ln for ln in out.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1, out)
        rec = json.loads(lines[0])
        agent_schema.assert_valid_agent_record(rec)
        self.assertEqual(rec["kind"], "error")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertIs(rec["applied"], False)
        self.assertTrue(
            any(d.get("rule") == "in-flight-plan" for d in rec.get("diagnostics", [])),
            rec,
        )

        rc, out = self._run(
            [
                "rename",
                "plans",
                "p22222",
                "--slug",
                "renamed",
                "--apply",
                "--no-commit",
                "--json",
            ]
        )
        self.assertEqual(rc, 2, out)
        doc = json.loads(out)
        self.assertEqual(doc["status"], "cannot-run")
        self.assertEqual(doc["exit_code"], 2)
        self.assertTrue(
            any(
                d.get("rule") == "in-flight-plan" and d.get("severity") == "error"
                for d in doc.get("diagnostics", [])
            ),
            doc,
        )

    def test_n_recovery_after_receipt_removal(self):
        self._cite(SPEC)
        rp = ipd_lifecycle.receipt_path_for(self.tmp, "p22222")
        self.assertTrue(rp.exists())
        rp.unlink()

        rc, out = self._run(
            ["rename", "plans", "p22222", "--slug", "renamed", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, out)
        renamed_file = self.plans / "20260701-x-01-p22222-renamed.ipd.md"
        self.assertTrue(renamed_file.exists())
        self.assertFalse(self.in_flight.exists())

        rc, out = self._run(
            [
                "group",
                "plans",
                "p22222",
                "--set",
                "newset",
                "--rename",
                "--apply",
                "--no-commit",
            ]
        )
        self.assertEqual(rc, 0, out)
        regrouped_file = self.plans / "20260701-newset-01-p22222-renamed.ipd.md"
        self.assertTrue(regrouped_file.exists())
        self.assertFalse(renamed_file.exists())


if __name__ == "__main__":
    unittest.main()

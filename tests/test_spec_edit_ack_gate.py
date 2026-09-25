#!/usr/bin/env python3

"""Regression suite for the spec-edit acknowledgement gate (specpause-01, `1g4i1t`).

Validates:
(a) Unattended run without flag refuses declaring plans and records refusal in state and events.
(b) Unattended run with --ack-spec-edits proceeds and records the justification.
(c) Interactive TTY prompt lists declaring id6 and spec paths, and 'y' proceeds.
(d) Interactive TTY prompt default is No (empty or None refuses).
(e) Queue with no declared spec edits never prompts or refuses.
(f) Flag registration on both hosts (oc_runipd and agy_runipd) requiring an argument.
(g) Gate is wired once in initialize_run_core before any announcement call.
(h) An unreadable declaring plan refuses rather than silently proceeding.
"""

from __future__ import annotations

import contextlib
import inspect
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

from agent_workflows import agy_runipd, oc_runipd, render_stream, runner_shared


class SpecEditAckGateTests(unittest.TestCase):
    """Tests for enforce_spec_edit_ack_gate and policy flag wiring."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        (self.repo / ".git").mkdir(parents=True, exist_ok=True)
        (self.repo / ".aw" / "records" / "plans" / "pending").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_run_setup(
        self,
        *,
        id6: str = "tst001",
        setid: str = "testset",
        scope_paths: str = "x.spec.md, src/foo.py",
    ) -> tuple[Path, dict]:
        plan_filename = f"20260924-{setid}-01-{id6}-test-plan.ipd.md"
        plan_rel = f".aw/records/plans/pending/{plan_filename}"
        plan_path = self.repo / plan_rel
        plan_content = f"""# IPD: Test plan for spec ack gate

- Date: 2026-09-24
- Kind: child
- Concern: test.
- Scope: test.
- Scope-Paths: {scope_paths}
- Item-Dependencies: none
- Status: approved
- Set: {setid}
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Goal
Test.

## Detailed Implementation Checklist (TODO)
- [ ] E-01 Do test
  - Execution state: pending
"""
        plan_path.write_text(plan_content, encoding="utf-8")

        run_id = "run-20260925T000000Z-111111"
        run_dir = self.repo / ".aw" / "records" / "runs" / run_id
        for sub in ("sessions", "outcomes", "prompts"):
            (run_dir / sub).mkdir(parents=True, exist_ok=True)

        state = {
            "schema_version": 1,
            "run_id": run_id,
            "queue": [
                {
                    "position": 1,
                    "id6": id6,
                    "setid": setid,
                    "configured_file": plan_rel,
                    "status": "pending",
                    "action": "execute",
                    "attempts": [],
                }
            ],
            "options": {},
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return run_dir, state

    def dummy_write_report(self, run_dir: Path, state: dict) -> None:
        pass

    def test_unattended_without_flag_REFUSES_and_records_it(self) -> None:
        """Case (a): unattended, no flag -> proceed is False, refusal recorded."""
        run_dir, state = self.make_run_setup()
        gate_fn = getattr(runner_shared, "enforce_spec_edit_ack_gate")
        decision = gate_fn(
            run_dir,
            state,
            repo=self.repo,
            interactive=False,
            write_report_fn=self.dummy_write_report,
            acknowledgement=None,
        )
        self.assertFalse(decision.proceed)
        item = state["queue"][0]
        refusal = render_stream.refusal_of_item(item)
        self.assertIsNotNone(refusal)
        self.assertEqual(refusal.code, "spec-edit-unacknowledged")

        # Verify state.json on disk carries refusal
        disk_state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        disk_refusal = render_stream.refusal_of_item(disk_state["queue"][0])
        self.assertIsNotNone(disk_refusal)
        self.assertEqual(disk_refusal.code, "spec-edit-unacknowledged")

        # Verify events.jsonl
        events_path = run_dir / "events.jsonl"
        self.assertTrue(events_path.exists())
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        ack_events = [e for e in events if e.get("event") == "spec-edit-ack-gate"]
        self.assertEqual(len(ack_events), 1)
        self.assertFalse(ack_events[0]["proceed"])

    def test_unattended_WITH_flag_proceeds_and_records_the_justification(self) -> None:
        """Case (b): unattended with --ack-spec-edits -> proceed is True, justification recorded."""
        run_dir, state = self.make_run_setup()
        gate_fn = getattr(runner_shared, "enforce_spec_edit_ack_gate")
        justification = "reviewed the 2.5c amendment"
        decision = gate_fn(
            run_dir,
            state,
            repo=self.repo,
            interactive=False,
            write_report_fn=self.dummy_write_report,
            acknowledgement=justification,
        )
        self.assertTrue(decision.proceed)
        self.assertEqual(state["options"]["ack_spec_edits"], justification)

        events_path = run_dir / "events.jsonl"
        self.assertTrue(events_path.exists())
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        ack_events = [e for e in events if e.get("event") == "spec-edit-ack-gate"]
        self.assertEqual(len(ack_events), 1)
        self.assertTrue(ack_events[0]["proceed"])
        self.assertEqual(ack_events[0]["override"], "flag")
        self.assertEqual(ack_events[0]["justification"], justification)

    def test_tty_prompt_lists_specs_and_y_proceeds(self) -> None:
        """Case (c): interactive TTY prompt lists plan id6 and spec paths; 'y' proceeds."""
        run_dir, state = self.make_run_setup()
        questions: list[str] = []

        def stub_prompt(q: str) -> str:
            questions.append(q)
            return "y"

        gate_fn = getattr(runner_shared, "enforce_spec_edit_ack_gate")
        decision = gate_fn(
            run_dir,
            state,
            repo=self.repo,
            interactive=True,
            write_report_fn=self.dummy_write_report,
            prompt=stub_prompt,
        )
        self.assertTrue(decision.proceed)
        self.assertEqual(len(questions), 1)
        self.assertIn("tst001", questions[0])
        self.assertIn("x.spec.md", questions[0])
        self.assertEqual(
            state["options"]["ack_spec_edits"], "interactive confirmation: y"
        )

        events_path = run_dir / "events.jsonl"
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        ack_events = [e for e in events if e.get("event") == "spec-edit-ack-gate"]
        self.assertEqual(len(ack_events), 1)
        self.assertTrue(ack_events[0]["proceed"])
        self.assertEqual(ack_events[0]["override"], "interactive")

    def test_tty_prompt_default_is_NO(self) -> None:
        """Case (d): empty or None from prompt refuses."""
        gate_fn = getattr(runner_shared, "enforce_spec_edit_ack_gate")
        for stub_val in ("", None, "n", "no"):
            run_dir, state = self.make_run_setup()
            decision = gate_fn(
                run_dir,
                state,
                repo=self.repo,
                interactive=True,
                write_report_fn=self.dummy_write_report,
                prompt=lambda _q, val=stub_val: val,
            )
            self.assertFalse(decision.proceed)
            item = state["queue"][0]
            refusal = render_stream.refusal_of_item(item)
            self.assertIsNotNone(refusal)
            self.assertEqual(refusal.code, "spec-edit-unacknowledged")

    def test_no_declared_spec_edit_never_prompts(self) -> None:
        """Case (e): queue without spec edits proceeds without prompting."""
        run_dir, state = self.make_run_setup(
            scope_paths="src/foo.py, tests/test_foo.py"
        )

        def fail_prompt(_q: str) -> str:
            raise AssertionError(
                "Prompt should not be called when no spec edit is declared"
            )

        gate_fn = getattr(runner_shared, "enforce_spec_edit_ack_gate")
        decision = gate_fn(
            run_dir,
            state,
            repo=self.repo,
            interactive=True,
            write_report_fn=self.dummy_write_report,
            prompt=fail_prompt,
        )
        self.assertTrue(decision.proceed)
        self.assertEqual(decision.impacts, ())
        item = state["queue"][0]
        self.assertIsNone(render_stream.refusal_of_item(item))

        events_path = run_dir / "events.jsonl"
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        ack_events = [e for e in events if e.get("event") == "spec-edit-ack-gate"]
        self.assertEqual(len(ack_events), 1)
        self.assertTrue(ack_events[0]["proceed"])
        self.assertEqual(ack_events[0]["declared"], [])

    def test_flag_on_both_hosts(self) -> None:
        """Case (f): --ack-spec-edits on both hosts requires a value and freezes into options."""
        for host_mod in (oc_runipd, agy_runipd):
            parser = host_mod.build_parser()
            # Bare flag raises SystemExit
            with self.assertRaises(SystemExit) as cm:
                with io.StringIO() as f, contextlib.redirect_stderr(f):
                    parser.parse_args(["start", "sel", "--ack-spec-edits"])
            self.assertNotEqual(cm.exception.code, 0)

            # Flag with value parses and freezes
            args = parser.parse_args(
                ["start", "sel", "--ack-spec-edits", "valid justification"]
            )
            frozen = runner_shared.freeze_run_policy_flags(args)
            self.assertEqual(frozen["ack_spec_edits"], "valid justification")

    def test_gate_is_wired_once_before_announcement(self) -> None:
        """Case (g): initialize_run_core calls enforce_spec_edit_ack_gate exactly once, ahead of announcements."""
        # Check symbol exists
        _ = getattr(runner_shared, "enforce_spec_edit_ack_gate")
        src = inspect.getsource(runner_shared.initialize_run_core)
        self.assertEqual(
            src.count("enforce_spec_edit_ack_gate("),
            1,
            "enforce_spec_edit_ack_gate( must appear exactly once in initialize_run_core",
        )
        call_pos = src.find("enforce_spec_edit_ack_gate(")
        announce_positions = [
            m.start() for m in re.finditer(r"announce_run_order_fn\(", src)
        ]
        self.assertGreaterEqual(len(announce_positions), 1)
        for pos in announce_positions:
            self.assertLess(
                call_pos,
                pos,
                "enforce_spec_edit_ack_gate( must precede every announce_run_order_fn(",
            )

    def test_an_unreadable_declaring_plan_REFUSES_rather_than_proceeding(self) -> None:
        """Case (h): unreadable/absent plan file refuses rather than proceeding on empty impacts."""
        run_dir, state = self.make_run_setup(scope_paths="x.spec.md")
        plan_path = (
            self.repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260924-testset-01-tst001-test-plan.ipd.md"
        )
        plan_path.unlink()

        gate_fn = getattr(runner_shared, "enforce_spec_edit_ack_gate")
        decision = gate_fn(
            run_dir,
            state,
            repo=self.repo,
            interactive=False,
            write_report_fn=self.dummy_write_report,
        )
        self.assertFalse(decision.proceed)
        item = state["queue"][0]
        refusal = render_stream.refusal_of_item(item)
        self.assertIsNotNone(refusal)
        self.assertEqual(refusal.code, "spec-edit-unacknowledged")
        self.assertIn("tst001", decision.message)


if __name__ == "__main__":
    unittest.main()

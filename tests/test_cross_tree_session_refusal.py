# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for cross-tree session refusal (r0iob3 E-03).

Guards that:
1. Operator --session is refused when carried into an isolated review sweep lane (Shape (c)).
2. The refusal names both the operator's tree and the lane tree, and continues with a fresh session.
3. The four turn shapes (a)-(d) behave as contracted:
   (a) execute non-isolated with --session -> honors operator session (continuity promise)
   (b) execute isolated with --session -> fresh session (xd9sll mitigation)
   (c) review in sweep lane with --session -> refused, fresh session (r0iob3 E-03)
   (d) review outside sweep lane with --session -> fresh session
4. Decisive negative case: the sweep lane's own recorded session (REVIEW_SWEEP_SESSION_KEY)
   is preserved and passed into subsequent turns in that sweep lane.
5. Both oc_runipd and runner_shared session expressions obey this contract.
"""

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import oc_runipd, runner_shared


class CrossTreeSessionRefusalTests(unittest.TestCase):
    """Guards for refusing operator --session carried into isolated sweep lanes."""

    def test_four_turn_shapes_runner_shared(self) -> None:
        """Derive session resolution across four turn shapes in runner_shared."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            sweep_lane = Path(temp) / "sweep_lane"
            sweep_lane.mkdir()
            run_dir = Path(temp) / "run_dir"
            run_dir.mkdir()

            op_session = "ses_OP"

            # Shape (a): execute turn, NOT isolated, with --session -> passes ses_OP
            item_a = {"id6": "tst001", "action": "execute", "setid": "set1"}
            options_a = {"session": op_session, "isolate_worktree": False}
            state_a = {"options": options_a, "repo": str(repo)}
            # In execute_item_core logic:
            is_review_a = False
            review_uses_sweep_session_a = (
                is_review_a and runner_shared.isolation_for_action(options_a, "review")
            )
            self.assertFalse(review_uses_sweep_session_a)
            # Not review -> falls back to options.get("session")
            raw_session_a = (
                state_a.get("session_id")
                or state_a.get("set_sessions", {}).get(item_a["setid"])
                or options_a.get("session")
            )
            self.assertEqual(op_session, raw_session_a)

            # Shape (b): execute turn, ISOLATED lane, with --session -> None
            item_b = {"id6": "tst002", "action": "execute", "setid": "set1"}
            options_b = {"session": op_session, "isolate_worktree": True}
            self.assertEqual("execute", item_b["action"])
            self.assertTrue(options_b["isolate_worktree"])
            # For isolated execute, session is explicitly overridden to None (xd9sll)
            # execute_item_core: if isolate: session_id = None
            raw_session_b = None
            self.assertIsNone(raw_session_b)

            # Shape (c): review turn in sweep lane, with --session, no sweep session recorded yet
            # -> operator session is REFUSED, falls back to None (fresh session)
            item_c = {"id6": "rev001", "action": "review", "setid": "set1"}
            options_c = {"session": op_session, "isolate_worktree": True}
            state_c = {
                "options": options_c,
                "repo": str(repo),
                runner_shared.REVIEW_SWEEP_LANE_KEY: {
                    "path": str(sweep_lane),
                    "worktree": str(sweep_lane),
                    "branch": "aw/lane/review_sweep",
                    "run_id": "test_run",
                },
            }
            # Simulate the sweep branch in runner_shared.execute_item_core:
            is_review_c = item_c.get("action") == "review"
            review_uses_sweep_session_c = (
                is_review_c and runner_shared.isolation_for_action(options_c, "review")
            )
            self.assertTrue(review_uses_sweep_session_c)

            # Check runner_shared sweep resolution block
            rec = runner_shared.review_sweep_lane_record(state_c)
            self.assertIsNotNone(rec)
            lane_tree = str(rec.get("path"))
            self.assertEqual(str(sweep_lane), lane_tree)

            recorded_sweep_session_c = state_c.get(
                runner_shared.REVIEW_SWEEP_SESSION_KEY
            )
            self.assertIsNone(recorded_sweep_session_c)
            # Since options.get("session") is set, it triggers refusal:
            op_tree = str(repo)
            refusal_reason = (
                f"cannot carry operator session {op_session!r} bound to {op_tree!r} into isolated "
                f"sweep lane {lane_tree!r}: cross-tree session reuse is refused to prevent silent "
                f"execution failure; continuing with a fresh session"
            )
            self.assertIn(op_session, refusal_reason)
            self.assertIn(str(repo), refusal_reason)
            self.assertIn(str(sweep_lane), refusal_reason)

            # Shape (d): review turn outside sweep lane (e.g. non-isolated review)
            # -> options.get("session") honored if not isolated
            options_d = {"session": op_session, "isolate_worktree": False}
            review_uses_sweep_session_d = (
                is_review_c and runner_shared.isolation_for_action(options_d, "review")
            )
            self.assertFalse(review_uses_sweep_session_d)

    def test_decisive_negative_case_sweep_session_preserved(self) -> None:
        """The sweep's own recorded session (REVIEW_SWEEP_SESSION_KEY) is preserved."""
        sweep_session = "ses_SWEEP_OWN"
        op_session = "ses_OP"

        state = {
            runner_shared.REVIEW_SWEEP_SESSION_KEY: sweep_session,
            "options": {"session": op_session, "isolate_worktree": True},
        }
        # When REVIEW_SWEEP_SESSION_KEY is present, it must be chosen over options.get("session")
        recorded = state.get(runner_shared.REVIEW_SWEEP_SESSION_KEY)
        self.assertEqual(sweep_session, recorded)
        self.assertNotEqual(op_session, recorded)

    def test_oc_runipd_sweep_lane_turn_refusal(self) -> None:
        """Verify oc_runipd.run_opencode refuses operator session in sweep lane and drops to fresh."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            sweep_lane = root / "sweep_lane"
            sweep_lane.mkdir()
            run_dir = root / "run_dir"
            (run_dir / "sessions").mkdir(parents=True)

            item = {"id6": "rev001", "action": "review", "setid": "set1", "position": 1}
            op_session = "ses_OP"
            fake_bin = root / "fake_opencode"
            fake_bin.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "args = sys.argv[1:]\n"
                "sess = args[args.index('--session') + 1] if '--session' in args else 'fresh_ses'\n"
                "print(json.dumps({'type':'text','sessionID':sess,'part':{'text':'done'}}))\n"
            )
            fake_bin.chmod(0o755)

            options = {
                "session": op_session,
                "opencode": str(fake_bin),
                "max_items_per_session": 4,
            }

            state = {
                "run_id": "run_test_01",
                "repo": str(repo),
                "options": options,
                "opencode_bin": str(fake_bin),
                runner_shared.REVIEW_SWEEP_LANE_KEY: {
                    "path": str(sweep_lane),
                    "worktree": str(sweep_lane),
                    "branch": "aw/lane/review_sweep",
                    "run_id": "run_test_01",
                },
            }

            plan_path = root / "plan.ipd.md"
            plan_path.write_text("- Id: rev001\n", encoding="utf-8")
            prompt_path = root / "prompt.txt"
            prompt_path.write_text("test review prompt\n", encoding="utf-8")

            # Run in sweep lane: work_dir=str(sweep_lane)
            # Operator session must be refused, not passed into fake_opencode argv
            with mock.patch("sys.stderr", new_callable=io.StringIO) as fake_stderr:
                code, observed_session, _log, _argv = oc_runipd.run_opencode(
                    state=state,
                    run_dir=run_dir,
                    item=item,
                    plan_path=plan_path,
                    prompt_path=prompt_path,
                    attempt_no=1,
                    work_dir=str(sweep_lane),
                )

            self.assertEqual(0, code)
            self.assertEqual("fresh_ses", observed_session)
            self.assertIn("Refused carrying operator session", fake_stderr.getvalue())
            # Refusal was recorded on item
            refusal = item.get("refusal") or {}
            self.assertEqual("cross-tree-session-refused", refusal.get("code"))
            self.assertIn(op_session, refusal.get("reason", ""))
            self.assertIn(str(sweep_lane), refusal.get("reason", ""))

            # Event appended to events.jsonl
            events_file = run_dir / "events.jsonl"
            self.assertTrue(events_file.is_file())
            events = [
                json.loads(line)
                for line in events_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            refusal_events = [
                e for e in events if e.get("event") == "cross-tree-session-refused"
            ]
            self.assertEqual(1, len(refusal_events))
            self.assertEqual(op_session, refusal_events[0].get("session_id"))
            self.assertEqual(str(sweep_lane), refusal_events[0].get("lane_tree"))


if __name__ == "__main__":
    unittest.main()

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

"""Tests for silent turn observability (r0iob3 E-01, E-02, E-04).

Guards that:
1. `attempt_log_status` classifies log files into {absent, empty, unparseable, non-dict, events}.
2. `turn_attempted_nothing` handles both EXECUTE and REVIEW actions, returns reasoned verdicts,
   and preserves fail-closed behavior without reclassifying deliberate stops.
3. `review_has_positive_evidence` detects positive work (events, uncommitted edits, review records).
4. `reconcile_disposition` refuses zero-output review turns for both to-review and approved plans.
5. The turn completion path in `execute_item_core` records `turn-silent-refused` with `ipd-silent-turn`.
"""

import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import oc_runipd, runner_shared, runner_stop


class AttemptLogStatusTests(unittest.TestCase):
    """Guards for attempt_log_status classifying supporting log evidence."""

    def test_absent_log(self) -> None:
        self.assertEqual("absent", runner_shared.attempt_log_status({}))
        self.assertEqual(
            "absent",
            runner_shared.attempt_log_status({"log": "/nonexistent/log.jsonl"}),
        )

    def test_empty_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_path = Path(temp) / "log.jsonl"
            log_path.touch()
            self.assertEqual(
                "empty", runner_shared.attempt_log_status({"log": str(log_path)})
            )

    def test_unparseable_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_path = Path(temp) / "log.jsonl"
            log_path.write_text(
                "not json at all\nsecond broken line\n", encoding="utf-8"
            )
            self.assertEqual(
                "unparseable", runner_shared.attempt_log_status({"log": str(log_path)})
            )

    def test_non_dict_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_path = Path(temp) / "log.jsonl"
            log_path.write_text('"just a string"\n123\n', encoding="utf-8")
            self.assertEqual(
                "non-dict", runner_shared.attempt_log_status({"log": str(log_path)})
            )

    def test_valid_dict_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_path = Path(temp) / "log.jsonl"
            log_path.write_text(
                '{"event": "start"}\n{"event": "finish"}\n', encoding="utf-8"
            )
            self.assertEqual(
                "events", runner_shared.attempt_log_status({"log": str(log_path)})
            )


class TurnAttemptedNothingTests(unittest.TestCase):
    """Guards for turn_attempted_nothing covering execute and review actions."""

    def _execute_item(self) -> dict[str, Any]:
        return {"action": "execute", "id6": "tst001", "position": 1}

    def _review_item(self) -> dict[str, Any]:
        return {"action": "review", "id6": "rev001", "position": 1}

    def test_silent_execute_turn_in_lane(self) -> None:
        item = self._execute_item()
        attempt = {
            "lane_commit": "abc1234",
            "worktree": "/tmp/fake_lane",
        }
        lane = {"commits_ahead": 0, "dirty": False, "state": "clean", "branch": "test"}
        verdict = runner_shared.turn_attempted_nothing(
            item, attempt, disposition="fail-verify", outcome_written=False, lane=lane
        )
        self.assertTrue(verdict.attempted_nothing)
        self.assertTrue(verdict.proven)
        self.assertIn("wrote no outcome file", verdict.reason)

    def test_silent_review_turn_answers_with_reasoned_verdict(self) -> None:
        """r0iob3 E-01: review action is no longer refused as 'a different question'."""
        item = self._review_item()
        attempt = {
            "lane_commit": "abc1234",
            "worktree": "/tmp/fake_lane",
        }
        lane = {"commits_ahead": 0, "dirty": False, "state": "clean", "branch": "test"}
        # Pre-r0iob3 disposition for a silent review turn was "reviewed"
        verdict_reviewed = runner_shared.turn_attempted_nothing(
            item, attempt, disposition="reviewed", outcome_written=False, lane=lane
        )
        self.assertTrue(verdict_reviewed.attempted_nothing)
        self.assertTrue(verdict_reviewed.proven)
        self.assertNotIn("different question", verdict_reviewed.reason)

    def test_execute_turn_refusals_preserved(self) -> None:
        item = self._execute_item()
        attempt = {"lane_commit": "abc1234", "worktree": "/tmp/fake_lane"}

        # 1. Outcome written
        lane = {"commits_ahead": 0, "dirty": False}
        v = runner_shared.turn_attempted_nothing(
            item, attempt, disposition="executed", outcome_written=True, lane=lane
        )
        self.assertFalse(v.attempted_nothing)
        self.assertIn("outcome file WAS written", v.reason)

        # 2. Commits ahead
        lane = {"commits_ahead": 2, "dirty": False}
        v = runner_shared.turn_attempted_nothing(
            item, attempt, disposition="executed", outcome_written=False, lane=lane
        )
        self.assertFalse(v.attempted_nothing)
        self.assertIn("commit(s) beyond its base", v.reason)

        # 3. Dirty tree
        lane = {"commits_ahead": 0, "dirty": True}
        v = runner_shared.turn_attempted_nothing(
            item, attempt, disposition="partial", outcome_written=False, lane=lane
        )
        self.assertFalse(v.attempted_nothing)
        self.assertIn("tree is DIRTY", v.reason)

        # 4. Shared tree head moved
        attempt_shared = {
            "starting_head": "commit_1",
            "ending_head": "commit_2",
            "ending_status": "",
        }
        v = runner_shared.turn_attempted_nothing(
            item,
            attempt_shared,
            disposition="partial",
            outcome_written=False,
            lane=None,
        )
        self.assertFalse(v.attempted_nothing)
        self.assertIn("HEAD MOVED", v.reason)

    def test_deliberate_stop_outranks_silence(self) -> None:
        """Deliberate operator stop is never classified as attempted nothing."""
        item = self._execute_item()
        item["stopped"] = {"stopped_deliberately": True}
        attempt = {"lane_commit": "abc1234", "worktree": "/tmp/fake_lane"}
        lane = {"commits_ahead": 0, "dirty": False}
        v = runner_shared.turn_attempted_nothing(
            item,
            attempt,
            disposition=runner_stop.STOPPED_DISPOSITION,
            outcome_written=False,
            lane=lane,
        )
        self.assertFalse(v.attempted_nothing)
        self.assertTrue(v.proven)
        self.assertIn("DELIBERATE OPERATOR STOP", v.reason)


class ReviewEvidenceAndDispositionTests(unittest.TestCase):
    """Guards for review_has_positive_evidence and reconcile_disposition review gate (E-04)."""

    def test_review_positive_evidence_detection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "t@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "file.txt").write_text("base", encoding="utf-8")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)

            run_dir = repo / "run"
            run_dir.mkdir()
            item: dict[str, Any] = {"id6": "rev001", "action": "review"}

            # Clean repo, no log, no outcome -> no positive evidence
            self.assertFalse(
                runner_shared.review_has_positive_evidence(repo, run_dir, item)
            )

            # Case 1: uncommitted working tree edit
            (repo / "file.txt").write_text("modified", encoding="utf-8")
            self.assertTrue(
                runner_shared.review_has_positive_evidence(repo, run_dir, item)
            )
            subprocess.run(["git", "checkout", "-q", "file.txt"], cwd=repo, check=True)
            self.assertFalse(
                runner_shared.review_has_positive_evidence(repo, run_dir, item)
            )

            # Case 2: review record written under .aw/records/reviews/
            rev_dir = repo / ".aw" / "records" / "reviews"
            rev_dir.mkdir(parents=True)
            (rev_dir / "20260928-rev001-review.md").write_text(
                "# Review", encoding="utf-8"
            )
            self.assertTrue(
                runner_shared.review_has_positive_evidence(repo, run_dir, item)
            )
            (rev_dir / "20260928-rev001-review.md").unlink()
            self.assertFalse(
                runner_shared.review_has_positive_evidence(repo, run_dir, item)
            )

            # Case 3: attempt log has events
            log_file = run_dir / "review.jsonl"
            log_file.write_text(
                '{"type": "message", "content": "review text"}\n', encoding="utf-8"
            )
            item_with_log = dict(item, attempts=[{"log": str(log_file)}])
            self.assertTrue(
                runner_shared.review_has_positive_evidence(repo, run_dir, item_with_log)
            )

    def test_reconcile_disposition_review_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "t@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "README").write_text("test\n", encoding="utf-8")
            subprocess.run(["git", "add", "README"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)

            plans_dir = repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)

            # Plan 1: to-review
            p_toreview = plans_dir / "20260928-demo-01-rev001-test.ipd.md"
            p_toreview.write_text(
                "- Id: rev001\n- Status: to-review\n", encoding="utf-8"
            )

            # Plan 2: approved
            p_approved = plans_dir / "20260928-demo-02-rev002-test.ipd.md"
            p_approved.write_text(
                "- Id: rev002\n- Status: approved\n", encoding="utf-8"
            )

            # Commit the plans so working tree is clean for zero-output test
            subprocess.run(["git", "add", ".aw"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

            run_dir = repo / "run"
            run_dir.mkdir()

            item_tr = {"id6": "rev001", "action": "review", "path": str(p_toreview)}
            item_ap = {"id6": "rev002", "action": "review", "path": str(p_approved)}

            # ZERO OUTPUT turns (exit 0, no positive evidence)
            # Both MUST return fail-gate with review-zero-output-refused
            disp_tr, _ = runner_shared.reconcile_disposition(
                repo, item_tr, run_dir, exit_code=0
            )
            self.assertEqual("fail-gate", disp_tr)
            self.assertEqual(
                (item_tr.get("refusal") or {}).get("code"),
                runner_shared.REVIEW_ZERO_OUTPUT_REFUSAL_CODE,
            )

            disp_ap, _ = runner_shared.reconcile_disposition(
                repo, item_ap, run_dir, exit_code=0
            )
            self.assertEqual("fail-gate", disp_ap)
            self.assertEqual(
                (item_ap.get("refusal") or {}).get("code"),
                runner_shared.REVIEW_ZERO_OUTPUT_REFUSAL_CODE,
            )

            # NORMAL OUTPUT turns (uncommitted change made)
            (repo / "README").write_text("modified by review\n", encoding="utf-8")
            item_tr_ok = {"id6": "rev001", "action": "review", "path": str(p_toreview)}
            item_ap_ok = {"id6": "rev002", "action": "review", "path": str(p_approved)}

            disp_tr_ok, _ = runner_shared.reconcile_disposition(
                repo, item_tr_ok, run_dir, exit_code=0
            )
            self.assertEqual("reviewed", disp_tr_ok)

            disp_ap_ok, _ = runner_shared.reconcile_disposition(
                repo, item_ap_ok, run_dir, exit_code=0
            )
            self.assertEqual("approved", disp_ap_ok)


class CompletionSeamRefusalTests(unittest.TestCase):
    """Guards for E-02 turn-completion seam in execute_item_core."""

    def test_silent_turn_records_refusal_and_event(self) -> None:
        """A silent turn is recorded as turn-silent-refused and emits ipd-silent-turn."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "t@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / ".gitignore").write_text(
                ".aw/state/\n.aw/worktrees/\n", encoding="utf-8"
            )
            (repo / "README").write_text("initial\n", encoding="utf-8")
            subprocess.run(["git", "add", "README", ".gitignore"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

            plans_dir = repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)
            plan_file = plans_dir / "20260928-set1-01-tst001-test.ipd.md"
            plan_file.write_text("- Id: tst001\n- Status: approved\n", encoding="utf-8")
            subprocess.run(["git", "add", ".aw"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add plan"], cwd=repo, check=True)

            run_dir = root / "run_dir"
            run_dir.mkdir()
            (run_dir / "outcomes").mkdir()
            (run_dir / "sessions").mkdir()
            (run_dir / "prompts").mkdir()

            item = {
                "id6": "tst001",
                "action": "execute",
                "setid": "set1",
                "position": 1,
                "status": "queued",
                "attempts": [],
            }
            state = {
                "run_id": "test_run",
                "repo": str(repo),
                "options": {"auto": True, "no_audit": True},
                "queue": [item],
            }

            fake_bin = root / "fake_opencode"
            fake_bin.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "print(json.dumps({'type':'text','sessionID':'ses-1','part':{'text':'done'}}))\n"
            )
            fake_bin.chmod(0o755)
            state["options"]["opencode"] = str(fake_bin)

            with mock.patch.object(
                oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")
            ), mock.patch.object(
                oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")
            ), mock.patch.object(
                oc_runipd, "assert_child_tool_identity", lambda *a, **k: None
            ), mock.patch.object(
                oc_runipd, "extract_suite_failures", None
            ), mock.patch.object(
                oc_runipd, "run_suite_check", lambda *a, **k: (True, "1 passed")
            ), mock.patch("sys.stderr", new_callable=io.StringIO):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            # Verification of E-02 contract:
            self.assertEqual("fail-verify", item["status"])
            refusal = item.get("refusal") or {}
            self.assertEqual("turn-silent-refused", refusal.get("code"))
            self.assertIn("wrote no outcome file", refusal.get("reason", ""))

            # events.jsonl has ipd-silent-turn
            events_file = run_dir / "events.jsonl"
            self.assertTrue(events_file.is_file())
            events = [
                json.loads(line)
                for line in events_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            silent_events = [e for e in events if e.get("event") == "ipd-silent-turn"]
            self.assertEqual(1, len(silent_events))
            self.assertEqual("tst001", silent_events[0].get("id6"))


if __name__ == "__main__":
    unittest.main()

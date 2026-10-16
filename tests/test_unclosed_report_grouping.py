"""Tests for unclosed backlog items classification, grouped reporting, and ledger recording (lr6lnm)."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from agent_workflows import runner_shared


class TestUnclosedReportGrouping(unittest.TestCase):
    """Behavioral tests for classify_unclosed, render_unclosed_report, and record_unclosed_backlog_items."""

    def test_classification_and_grouped_rendering_all_causes(self) -> None:
        """Cover each cause, assert group headings, ordering, pairs, next commands, and no 'never evaluated'."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            events_path = run_dir / "events.jsonl"
            # Write deliberate-stop event for pla001
            stop_event = {
                "at": "2026-10-12T23:59:06Z",
                "event": "deliberate-stop",
                "deliberate": True,
                "not_started": ["pla001"],
            }
            events_path.write_text(json.dumps(stop_event) + "\n", encoding="utf-8")

            queue = [
                # 1. not-started (stopped)
                {
                    "id6": "pla001",
                    "from_backlog": "itm001",
                    "status": "queued",
                },
                # 2. not-started (ended before reaching)
                {
                    "id6": "pla002",
                    "from_backlog": "itm002",
                    "status": "queued",
                },
                # 3. review-only
                {
                    "id6": "pla003",
                    "from_backlog": "itm003",
                    "status": "reviewed",
                },
                # 4. plan-failed (interrupted)
                {
                    "id6": "pla004",
                    "from_backlog": "itm004",
                    "status": "interrupted",
                },
                # 5. plan-failed (fail-gate)
                {
                    "id6": "pla005",
                    "from_backlog": "itm005",
                    "status": "fail-gate",
                },
                # 6. waiting-on-carriers (backlog_close closed=False with carrier reason)
                {
                    "id6": "pla006",
                    "from_backlog": "itm006",
                    "status": "executed",
                    "backlog_close": {
                        "item": "itm006",
                        "closed": False,
                        "reason": "IPD carrier(s) not executed: .aw/records/plans/pending/20261012-set-01-car001-slug.ipd.md",
                    },
                },
                # 7. close-refused (backlog_close closed=False with other reason)
                {
                    "id6": "pla007",
                    "from_backlog": "itm007",
                    "status": "executed",
                    "backlog_close": {
                        "item": "itm007",
                        "closed": False,
                        "reason": "close evaluation failed: disk read error",
                    },
                },
                # 8. unknown status
                {
                    "id6": "pla008",
                    "from_backlog": "itm008",
                    "status": "unknown-mystery-state",
                },
                # 9. already closed item (should not be included)
                {
                    "id6": "pla009",
                    "from_backlog": "itm009",
                    "status": "executed",
                    "backlog_close": {
                        "item": "itm009",
                        "closed": True,
                        "reason": "every carrier executed",
                    },
                },
            ]

            state = {
                "run_id": "run-20261012T233651Z-4004596",
                "queue": queue,
                "host_capabilities": {"host": "antigravity"},
            }

            classified = runner_shared.classify_unclosed(state, run_dir=run_dir)
            self.assertEqual(len(classified), 8)

            by_item = {it.item_id6: it for it in classified}

            # 1. stopped not-started
            self.assertEqual(by_item["itm001"].cause, "not-started")
            self.assertFalse(by_item["itm001"].needs_action)
            self.assertEqual(
                by_item["itm001"].detail, "the run was stopped before this plan ran"
            )

            # 2. unreached not-started
            self.assertEqual(by_item["itm002"].cause, "not-started")
            self.assertFalse(by_item["itm002"].needs_action)
            self.assertEqual(
                by_item["itm002"].detail, "the run ended before reaching this plan"
            )

            # 3. review-only
            self.assertEqual(by_item["itm003"].cause, "review-only")
            self.assertFalse(by_item["itm003"].needs_action)

            # 4. plan-failed (interrupted)
            self.assertEqual(by_item["itm004"].cause, "plan-failed")
            self.assertTrue(by_item["itm004"].needs_action)
            self.assertEqual(by_item["itm004"].detail, "interrupted")

            # 5. plan-failed (fail-gate)
            self.assertEqual(by_item["itm005"].cause, "plan-failed")
            self.assertTrue(by_item["itm005"].needs_action)
            self.assertEqual(by_item["itm005"].detail, "fail-gate")

            # 6. waiting-on-carriers
            self.assertEqual(by_item["itm006"].cause, "waiting-on-carriers")
            self.assertFalse(by_item["itm006"].needs_action)
            self.assertEqual(by_item["itm006"].detail, "car001")

            # 7. close-refused
            self.assertEqual(by_item["itm007"].cause, "close-refused")
            self.assertTrue(by_item["itm007"].needs_action)
            self.assertEqual(
                by_item["itm007"].detail, "close evaluation failed: disk read error"
            )

            # 8. unknown
            self.assertEqual(by_item["itm008"].cause, "unknown")
            self.assertTrue(by_item["itm008"].needs_action)
            self.assertEqual(by_item["itm008"].detail, "unknown-mystery-state")

            # Render report
            report = runner_shared.render_unclosed_report(state, run_dir=run_dir)

            # Heading and count
            self.assertIn("--- Backlog items still open (8) ---", report)

            # Wording must not use "never evaluated"
            self.assertNotIn("never evaluated", report)

            # Group ordering: needs-action groups ordered first
            pos_failed = report.find("Plan failed")
            pos_refused = report.find("Close refused")
            pos_unknown = report.find("Unknown")
            pos_waiting = report.find("Waiting on carriers")
            pos_not_started = report.find("Not started")
            pos_review = report.find("Review only")

            self.assertTrue(0 <= pos_failed < pos_refused < pos_unknown)
            self.assertTrue(pos_unknown < pos_waiting < pos_not_started < pos_review)

            # item <- plan pairs present
            self.assertIn("itm001 <- pla001", report)
            self.assertIn("itm006 <- pla006", report)
            self.assertIn("itm007 <- pla007", report)

            # Details present for detail groups
            self.assertIn("waiting on car001", report)
            self.assertIn("close evaluation failed: disk read error", report)
            self.assertIn("unknown-mystery-state", report)

            # Resume command present for stopped run
            self.assertIn(
                "Continue: aw agy run resume run-20261012T233651Z-4004596", report
            )
            # Investigate command for failed plans
            self.assertIn("Investigate: aw runs run-20261012T233651Z-4004596", report)

            # Test record_unclosed_backlog_items writes extended ledger event
            runner_shared.record_unclosed_backlog_items(run_dir, state)
            lines = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            unclosed_events = [
                e for e in lines if e.get("event") == "backlog-items-left-open"
            ]
            self.assertEqual(len(unclosed_events), 1)
            event_items = unclosed_events[0]["items"]
            self.assertEqual(len(event_items), 8)

            for item_rec in event_items:
                self.assertIn("item", item_rec)
                self.assertIn("reason", item_rec)
                self.assertIn("cause", item_rec)
                self.assertIn("plan", item_rec)
                self.assertIn("needs_action", item_rec)

            rec_map = {r["item"]: r for r in event_items}
            self.assertEqual(rec_map["itm001"]["cause"], "not-started")
            self.assertEqual(rec_map["itm001"]["plan"], "pla001")
            self.assertFalse(rec_map["itm001"]["needs_action"])

            self.assertEqual(rec_map["itm004"]["cause"], "plan-failed")
            self.assertEqual(rec_map["itm004"]["plan"], "pla004")
            self.assertTrue(rec_map["itm004"]["needs_action"])

            self.assertEqual(rec_map["itm006"]["cause"], "waiting-on-carriers")
            self.assertFalse(rec_map["itm006"]["needs_action"])

    def test_resume_command_only_for_stopped_run_group(self) -> None:
        """A run with queued items but no deliberate stop does not render resume command."""
        state = {
            "run_id": "run-test-no-stop",
            "queue": [
                {
                    "id6": "pla010",
                    "from_backlog": "itm010",
                    "status": "queued",
                }
            ],
            "host_capabilities": {"host": "opencode"},
        }
        report = runner_shared.render_unclosed_report(state)
        self.assertIn("Not started (1):", report)
        self.assertIn("the run ended before reaching these plans", report)
        self.assertNotIn("resume", report)
        self.assertNotIn("never evaluated", report)

    def test_empty_report_when_all_closed(self) -> None:
        """When every item is closed, render_unclosed_report returns empty string."""
        state = {
            "run_id": "run-test-all-closed",
            "queue": [
                {
                    "id6": "pla020",
                    "from_backlog": "itm020",
                    "status": "executed",
                    "backlog_close": {"closed": True, "reason": "closed"},
                }
            ],
        }
        self.assertEqual(runner_shared.render_unclosed_report(state), "")
        self.assertEqual(runner_shared.classify_unclosed(state), [])
        self.assertEqual(runner_shared.unclosed_backlog_items(state), [])

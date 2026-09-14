"""Tests for agent_workflows.record_history (awhistory Order 01): the global history.jsonl store."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from agent_workflows import record_history as rh


class RecordHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_append_and_read(self) -> None:
        rh.append(
            self.root,
            id6="aaa111",
            tree="plans",
            workflow="ipd",
            actor="a",
            message="m1",
            date="20260101",
        )
        rh.append(
            self.root,
            id6="aaa111",
            tree="plans",
            workflow="ipd",
            actor="a",
            message="m2",
            date="20260102",
        )
        rh.append(
            self.root,
            id6="bbb222",
            tree="specs",
            workflow="spec",
            actor="b",
            message="s1",
            date="20260103",
        )
        forr = rh.read_for(self.root, "aaa111")
        self.assertEqual([r["message"] for r in forr], ["m1", "m2"])
        self.assertEqual(len(rh.read_all(self.root)), 3)

    def test_missing_file_returns_empty(self) -> None:
        self.assertEqual(rh.read_for(self.root, "aaa111"), [])
        self.assertEqual(rh.read_all(self.root), [])

    def test_malformed_line_skipped(self) -> None:
        p = rh.history_path(self.root)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            'this is not json\n{"id6":"aaa111","date":"20260101","tree":"plans","workflow":"ipd","actor":"a","message":"ok"}\n',
            encoding="utf-8",
        )
        recs = rh.read_all(self.root)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["message"], "ok")

    def test_bad_id6_raises(self) -> None:
        with self.assertRaises(ValueError):
            rh.append(
                self.root,
                id6="TOOLONG",
                tree="plans",
                workflow="ipd",
                actor="a",
                message="m",
            )

    def test_date_defaults_today(self) -> None:
        rh.append(
            self.root,
            id6="aaa111",
            tree="plans",
            workflow="ipd",
            actor="a",
            message="m",
        )
        self.assertEqual(
            rh.read_all(self.root)[0]["date"], date.today().strftime("%Y%m%d")
        )

    def test_managed_by_directive(self) -> None:
        self.assertIn("Managed-by: aw", rh.MANAGED_BY_DIRECTIVE)


class ParenthesizedActorInTheInlineTailParser(unittest.TestCase):
    """Plan fn2l1u E-08b / V-08: `_TAIL_RE`'s actor capture is LAZY.

    This is not cosmetic. `_TAIL_RE` feeds `ipd_lifecycle._plan_status_events`, so with the old
    `[^)]*` bound a plan whose newest record was a parenthesized `executed` line was read as still
    being in its PREVIOUS status (measured: `approved` rather than `executed`), and
    `check_engine.check_lifecycle_transitions` consumes the same events.
    """

    def test_a_parenthesized_actor_parses_with_the_full_actor(self) -> None:
        line = "- 2026-08-30 executed (opencode (its_direct/some-model)): did the work"
        date_s, workflow, actor, message = rh._parse_record_line(line)
        self.assertEqual(date_s, "2026-08-30")
        self.assertEqual(workflow, "executed")
        self.assertEqual(actor, "opencode (its_direct/some-model)")
        self.assertEqual(message, "did the work")

    def test_the_slash_form_is_unchanged(self) -> None:
        line = "- 2026-08-30 executed (opencode/its_direct/some-model): did the work"
        _d, workflow, actor, message = rh._parse_record_line(line)
        self.assertEqual(
            (workflow, actor, message),
            ("executed", "opencode/its_direct/some-model", "did the work"),
        )

    def test_a_message_containing_close_paren_colon_is_not_truncated(self) -> None:
        """Lazy, not greedy; a greedy capture would take `opencode/model): fixed foo(bar` as actor."""
        line = "- 2026-09-08 executed (opencode/model): fixed foo(bar): baz"
        _d, workflow, actor, message = rh._parse_record_line(line)
        self.assertEqual(
            (workflow, actor, message),
            ("executed", "opencode/model", "fixed foo(bar): baz"),
        )

    def test_derive_plan_status_reads_a_parenthesized_terminal_line(self) -> None:
        """The measured consequence of the old bound: the derived status lagged by one transition."""
        from agent_workflows import ipd_lifecycle as life

        text = (
            "# IPD: x\n\n- Id: aaa111\n- Status: executed\n\n## Workflow history\n"
            "- 2026-08-30 executed (opencode (its_direct/some-model)): did the work\n"
            "- 2026-08-01 approved (aw set): ok\n"
        )
        self.assertEqual(life.derive_plan_status(text), "executed")

    def test_a_multi_word_middle_is_still_NOT_parsed(self) -> None:
        """Deliberately out of scope (fn2l1u Deferred): the workflow token stays `\\S+`.

        150 tracked records carry a multi-word middle. Widening THAT means deciding what the workflow
        token IS, which is a grammar change rather than a bound widening, and it reaches no gate. This
        test pins the boundary so the omission is visible rather than looking like an oversight.
        """
        line = "- 2026-07-26 fleshed to a design spec from research (actor): msg"
        _d, workflow, actor, _m = rh._parse_record_line(line)
        self.assertEqual((workflow, actor), ("", ""))


if __name__ == "__main__":
    unittest.main()

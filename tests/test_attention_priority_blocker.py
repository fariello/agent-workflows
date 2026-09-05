"""Tests for awdoctorfix Order 01: the attention board's priority + release-blocker columns + legend.
render_board is pure over a list of Items, so these build Items in code (no disk fixture)."""

from __future__ import annotations

import json
import re
import unittest

from agent_workflows import attention
from agent_workflows import term as T


def _strip(s):
    return re.sub(r"\033\[[0-9;]*m", "", s)


def _item(path, *, priority=None, blocks_release=None, lha="2026-05-01"):
    return attention.Item(
        "aaa111",
        path,
        "backlog",
        "open",
        "ready",
        None,
        lha,
        priority=priority,
        blocks_release=blocks_release,
    )


class AttentionPriorityBlockerTests(unittest.TestCase):
    def _colored(self, items):
        return _strip(
            attention.render_board(items, [], show_all=True, term=T.Term(color=True))
        )

    def _plain(self, items):
        return attention.render_board(
            items, [], show_all=True, term=T.Term(color=False)
        )

    def test_priority_bracket_rendered(self):
        out = self._colored(
            [_item(".aw/records/backlog/open/a.backlog.md", priority="high")]
        )
        self.assertIn("high", out)
        raw = attention.render_board(
            [_item(".aw/records/backlog/open/a.backlog.md", priority="high")],
            [],
            show_all=True,
            term=T.Term(color=True),
        )
        self.assertIn("\033[1;38;5;196mhigh", raw)

    def test_release_blocker_marker(self):
        item = _item(".aw/records/backlog/open/a.backlog.md", blocks_release="next")
        out = self._colored([item])
        # the Blocking column renders the resolved release version or 'next'
        self.assertRegex(out, r"open\s+backlog\s+(?:2\.0\.0|next)\s+-\s+-\s+0\s+0\s+a")

        raw = attention.render_board([item], [], show_all=True, term=T.Term(color=True))
        # blocking release version is styled in red (256-color code 196, bold)
        self.assertIn("\033[1;38;5;196m", raw)

        out_noblock = self._colored([_item(".aw/records/backlog/open/a.backlog.md")])
        self.assertRegex(out_noblock, r"open\s+backlog\s+-\s+-\s+-\s+0\s+0\s+a")

    def test_table_header_present_colored(self):
        out = self._colored([_item(".aw/records/backlog/open/a.backlog.md")])
        self.assertIn(
            "Status    Type    Blocking Priority Readiness  OQs  RQs  Artifact Set / ID",
            out,
        )

    def test_plain_board_unchanged(self):
        out = self._plain(
            [
                _item(
                    ".aw/records/backlog/open/a.backlog.md",
                    priority="high",
                    blocks_release="next",
                )
            ]
        )
        self.assertNotIn("legend:", out)
        self.assertNotIn("[high]", out)
        self.assertNotIn("[blocking]", out)
        self.assertIn("- [backlog] .aw/records/backlog/open/a.backlog.md (open)", out)

    def test_schema_version_and_json_keys(self):
        # Bumped to 3 when items gained readiness + oqs + rqs (was 2: priority + blocks_release).
        self.assertEqual(attention.SCHEMA_VERSION, 3)
        obj = json.loads(
            attention.render_json(
                [_item(".aw/records/backlog/open/a.backlog.md", priority="low")], []
            )
        )
        it = obj["items"][0]
        self.assertEqual(it["priority"], "low")
        self.assertIn("blocks_release", it)


class PlanReleaseBlockerSurfacingTests(unittest.TestCase):
    """IPD 7mw7m5 E-02: a plan carrying Blocks-Release surfaces in the release-blocker set AND its
    Item.blocks_release is populated by the plans reader (display parity with specs/backlog)."""

    def _mk_plan(self, root, br_value):
        import pathlib

        pdir = pathlib.Path(root) / ".aw" / "records" / "plans" / "pending"
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "20260101-demo-01-pl0001-x.ipd.md").write_text(
            "# IPD: pl0001\n\n- Date: 2026-08-22\n- Kind: child\n- Status: draft\n"
            f"- Set: demo\n- Order: 1\n- Id: pl0001\n- Blocks-Release: {br_value}\n\n"
            "## Workflow history\n- 2026-08-22 draft (t): x.\n\n## Goal\nx\n",
            encoding="utf-8",
        )

    def test_plans_reader_populates_blocks_release_and_surfaces(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._mk_plan(root, "next")
            items, _drift = attention.scan(root)
            plan_items = [it for it in items if it.tree == "plans"]
            self.assertEqual(len(plan_items), 1)
            # E-02: the plans reader now populates blocks_release (was None before).
            self.assertEqual(plan_items[0].blocks_release, "next")
            # set membership: the plan appears in the release-blocker set.
            blockers = attention.release_blockers(items, root)
            self.assertTrue(
                any(it.tree == "plans" and it.id == "pl0001" for it in blockers),
                "release-blocking plan must appear in release_blockers",
            )

    def test_plan_release_blocker_renders_blocking_markers(self):
        # Display parity: an Item with blocks_release set renders in the Blocking column
        it = attention.Item(
            "pl0001",
            ".aw/records/plans/pending/20260101-demo-01-pl0001-x.ipd.md",
            "plans",
            "draft",
            "ready",
            None,
            "2026-05-01",
            blocks_release="next",
        )
        out = _strip(
            attention.render_board([it], [], show_all=True, term=T.Term(color=True))
        )
        self.assertRegex(
            out,
            r"draft\s+plan\s+(?:2\.0\.0|next)\s+-\s+-\s+0\s+0\s+20260101-demo-01-pl0001",
        )


class RetiredPlanIsNotAReleaseBlockerTests(unittest.TestCase):
    """A RETIRED artifact keeps its `Blocks-Release` field on purpose (the field records what the
    artifact was for, and erasing it would falsify the record), but it must NOT be counted as an
    outstanding release blocker: nobody is going to do it. `release_blockers` previously skipped only
    the DONE class, so a plan retired to `superseded/` kept appearing in the release-blocker list."""

    def _mk_plan(self, root, disposition, status):
        import pathlib

        pdir = pathlib.Path(root) / ".aw" / "records" / "plans" / disposition
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "20260101-demo-01-pl0002-x.ipd.md").write_text(
            "# IPD: pl0002\n\n- Date: 2026-08-22\n- Kind: child\n"
            f"- Status: {status}\n"
            "- Set: demo\n- Order: 1\n- Id: pl0002\n- Blocks-Release: next\n\n"
            "## Workflow history\n- 2026-08-22 draft (t): x.\n\n## Goal\nx\n",
            encoding="utf-8",
        )

    def _blockers(self, disposition, status):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._mk_plan(root, disposition, status)
            items, _drift = attention.scan(root)
            return (
                [it.id for it in attention.release_blockers(items, root)],
                [it.attention_class for it in items if it.tree == "plans"],
            )

    def test_superseded_plan_is_not_an_outstanding_release_blocker(self):
        # The regression: a split/retired plan keeps Blocks-Release but cannot gate a release.
        blockers, classes = self._blockers("superseded", "superseded")
        self.assertEqual(classes, ["parked"], "superseded must map to the parked class")
        self.assertNotIn(
            "pl0002",
            blockers,
            "a superseded plan must NOT be counted as an outstanding release blocker",
        )

    def test_pending_plan_is_still_an_outstanding_release_blocker(self):
        # The guard against over-filtering: a live plan must still be counted.
        blockers, _classes = self._blockers("pending", "approved")
        self.assertIn(
            "pl0002",
            blockers,
            "a live pending plan carrying Blocks-Release must still be counted",
        )


class ReadinessReaderTests(unittest.TestCase):
    """The `- Readiness:` reader must be the schema's closed-enum reader, not a `(\\S+)` scan.

    THE REGRESSION THIS PINS: each of attention's four readers used to run its own
    `^-[ \\t]*Readiness:[ \\t]*(\\S+)` scan, which stops at the first space. The workflow documents
    multi-word spellings (`GO - PENDING HUMAN APPROVAL`), so such a value was folded to a bare `go`
    -- it then RENDERED as `go` and, worse, MATCHED `aw att --readiness go`, reporting a plan that
    still needs human approval as cleanly ready. Out-of-vocabulary input must fail closed to None.
    """

    def test_enum_values_round_trip(self):
        for value in ("go", "go-pending-approval", "no-go"):
            self.assertEqual(attention.read_readiness(f"- Readiness: {value}"), value)

    def test_value_matching_is_case_insensitive(self):
        self.assertEqual(
            attention.read_readiness("- Readiness: GO-PENDING-APPROVAL"),
            "go-pending-approval",
        )

    def test_multiword_spelling_is_not_truncated_to_go(self):
        for value in ("GO - PENDING HUMAN APPROVAL", "go (pending human approval)"):
            self.assertIsNone(
                attention.read_readiness(f"- Readiness: {value}"),
                f"{value!r} must fail closed, never collapse to a bare 'go'",
            )

    def test_absent_and_out_of_vocab_are_both_none(self):
        self.assertIsNone(attention.read_readiness("- Status: to-review\n"))
        self.assertIsNone(attention.read_readiness("- Readiness: banana"))
        # CONDITIONAL-GO is in no documented IPD vocabulary; it must not read as a value.
        self.assertIsNone(attention.read_readiness("- Readiness: CONDITIONAL-GO"))

    def test_agrees_with_the_schema_authority(self):
        from agent_workflows import ipd_schema

        for value in ("go", "no-go", "GO - PENDING HUMAN APPROVAL", "banana", ""):
            text = f"- Readiness: {value}\n"
            self.assertEqual(
                attention.read_readiness(text),
                ipd_schema.read_readiness(text),
                f"attention must not fork the schema reader on {value!r}",
            )


class GateRefRenderingTests(unittest.TestCase):
    """The gate suffix must honor `--long`, and the header fold must actually replace it.

    TWO REGRESSIONS THIS PINS, both display-only:
      1. The gate ref ignored `--long`, so a row showing a 30-char compact identity carried a
         110-char repo-relative path for its gate -- the one column the flag did not govern.
      2. The blocked-section fold hoisted a shared ref into the header but never suppressed the
         per-row suffix, so folding ADDED a line instead of removing the repetition.
    """

    def _colored(self, items):
        return _strip(
            attention.render_board(items, [], show_all=True, term=T.Term(color=True))
        )

    def _gated(self, ref, *, n=1, kind="artifact"):
        return [
            attention.Item(
                f"aaa11{i}",
                f".aw/records/backlog/blocked/2026090{i}-set-01-aaa11{i}-x.backlog.md",
                "backlog",
                "blocked",
                "blocked",
                {"kind": kind, "ref": ref},
                "2026-09-01",
            )
            for i in range(n)
        ]

    _DEEP = ".aw/records/plans/pending/20260903-runflags-01-uyeko5-wire-the-spec.ipd.md"

    def test_deep_path_ref_is_compacted_by_default(self):
        out = self._colored(self._gated(self._DEEP))
        self.assertIn("[gate artifact: 20260903-runflags-01-uyeko5]", out)
        self.assertNotIn(
            self._DEEP, out, "the raw deep path must not appear by default"
        )

    def test_long_restores_the_full_ref(self):
        out = _strip(
            attention.render_board(
                self._gated(self._DEEP),
                [],
                show_all=True,
                term=T.Term(color=True),
                long=True,
            )
        )
        self.assertIn(f"[gate artifact: {self._DEEP}]", out)

    def test_non_path_ref_is_never_compacted(self):
        # `TODO.md` has no directory separator: a stem would render a bare `TODO`, naming no file.
        out = self._colored(self._gated("TODO.md"))
        self.assertIn("[gate artifact: TODO.md]", out)

    def test_typed_non_path_refs_survive_verbatim(self):
        for kind, ref in (("issue", "GH-1234"), ("date", "2026-12-01")):
            out = self._colored(self._gated(ref, kind=kind))
            self.assertIn(f"[gate {kind}: {ref}]", out)

    def test_shared_ref_folds_into_header_and_leaves_rows(self):
        out = self._colored(self._gated("TODO.md", n=2))
        self.assertIn("TODO.md", out, "the shared ref must be stated once")
        self.assertNotIn(
            "[gate artifact:",
            out,
            "a folded ref must be REMOVED from every row, not merely echoed in the header",
        )

    def test_distinct_refs_are_not_folded_and_stay_on_rows(self):
        items = self._gated("TODO.md") + self._gated(self._DEEP)
        out = self._colored(items)
        self.assertIn("[gate artifact: TODO.md]", out)
        self.assertIn("[gate artifact: 20260903-runflags-01-uyeko5]", out)

    def test_mixed_gated_and_ungated_group_is_not_folded(self):
        # Hoisting into a header covering ungated rows would attribute a gate to items lacking one.
        items = self._gated("TODO.md") + [
            _item(".aw/records/backlog/open/plain.backlog.md")
        ]
        out = self._colored(items)
        self.assertIn("[gate artifact: TODO.md]", out)

    def test_uncolored_machine_form_keeps_the_full_ref(self):
        # The uncolored view is the stable agent/grep shape; compaction must not reach it.
        out = attention.render_board(
            self._gated(self._DEEP), [], show_all=True, term=T.Term(color=False)
        )
        self.assertIn(f"[gate artifact: {self._DEEP}]", out)


class QuestionCountJsonTests(unittest.TestCase):
    """oqs/rqs/readiness must be in `--format json`, not TTY-only, so agents and --check see them."""

    def test_json_carries_the_new_columns(self):
        item = attention.Item(
            "aaa111",
            ".aw/records/plans/pending/p.ipd.md",
            "plans",
            "to-review",
            "ready",
            None,
            "2026-05-01",
            readiness="go-pending-approval",
            oqs=2,
            rqs=1,
        )
        it = json.loads(attention.render_json([item], []))["items"][0]
        self.assertEqual(it["readiness"], "go-pending-approval")
        self.assertEqual(it["oqs"], 2)
        self.assertEqual(it["rqs"], 1)

    def test_deferred_question_counts_as_unresolved(self):
        # Matches plan_readiness.has_unresolved_blocking_question: "Status is not resolved".
        text = "## Open questions\n\n### OQ-01: q\n\n- Status: deferred\n"
        self.assertEqual(attention.count_question_stats(text), (1, 0))

    def test_missing_status_counts_as_unresolved(self):
        text = "## Open questions\n\n### OQ-01: q\n\n- Owner: maintainer\n"
        self.assertEqual(attention.count_question_stats(text), (1, 0))

    def test_resolved_question_counts_as_rq(self):
        text = "## Open questions\n\n### OQ-01: q\n\n- Status: resolved\n"
        self.assertEqual(attention.count_question_stats(text), (0, 1))


if __name__ == "__main__":
    unittest.main()

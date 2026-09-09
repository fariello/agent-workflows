#!/usr/bin/env python3
"""The askme gate: an UNRESOLVED BLOCKING open question is refused at EVERY checkpoint.

WHAT THIS FILE PROVES, and why the gate needed to exist at all. `ipd_lint` already refused a
`Blocking: yes` / `Status: open` question, but ONLY at the `pre-execution` checkpoint. Measured
2026-09-08 at HEAD: plan `xipfy1` carried exactly that state and a DEFAULT `aw ipd lint` reported
`conforming`, so an agent could author a plan, hand it over, and report completion with its
load-bearing question never put to the human. The gate closes that window; `/askme` is the workflow
that answers the question properly.

THE SCOPE IS A MAINTAINER RULING, NOT A CONVENIENCE, and the numbers are why. Measured across the 103
pending plans at the time: 66 carried at least one NON-blocking open question (the normal, healthy
state of a plan in progress: a noted minor choice with a stated lean), while only 14 carried a blocking
one. Firing on all 66 would have declared the repository's ordinary working state broken and, in a
shared checkout, would have forced an agent to edit other agents' in-flight plans to get its own commit
through. So the gate fires on `Blocking: yes` ONLY. Widening it is a maintainer decision.

THE FOUR PROPERTIES, each of which can fail independently:
  1. FIRES AT EVERY CHECKPOINT, not just `pre-execution`, which is the whole point.
  2. FIRES ONLY ON `Blocking: yes` + `Status: open`, so a non-blocking open question and a resolved
     blocking question both stay clean.
  3. DOES NOT DOUBLE-REPORT alongside the structural grammar error, so a malformed question yields one
     actionable diagnostic rather than two.
  4. NAMES THE REMEDY, because a refusal that does not say what to do just relocates the confusion.
"""

from __future__ import annotations

import unittest

from agent_workflows import ipd_lint
from agent_workflows import ipd_schema as S

_GATE_TEXT = "BLOCKING question is still"


def _oq(
    blocking: str, status: str, *, owner: str = "maintainer", rationale: str = ""
) -> str:
    lines = [
        "### OQ-01: should the runs root move out of the repository?",
        "",
        f"- Blocking: {blocking}",
        f"- Status: {status}",
        f"- Owner: {owner}",
        f"- Resolution or deferral rationale: {rationale}",
    ]
    return "\n".join(lines) + "\n"


def _gate_hits(oq_block: str) -> list[str]:
    """Diagnostics contributed by the askme gate for one `## Open questions` block."""
    parsed = ipd_lint.parse(
        "# IPD: probe\n\n## Open questions\n\n" + oq_block,
    )
    return [
        d.message
        for d in ipd_lint.check_open_questions(parsed)
        if _GATE_TEXT in d.message
    ]


def _other_hits(oq_block: str) -> list[str]:
    parsed = ipd_lint.parse("# IPD: probe\n\n## Open questions\n\n" + oq_block)
    return [
        d.message
        for d in ipd_lint.check_open_questions(parsed)
        if _GATE_TEXT not in d.message
    ]


class FiringConditionTests(unittest.TestCase):
    def test_blocking_open_is_refused(self):
        hits = _gate_hits(_oq("yes", "open"))
        self.assertEqual(len(hits), 1, hits)

    def test_blocking_resolved_is_clean(self):
        """The ONLY way to clear the gate honestly: answer it and record the answer."""
        self.assertEqual(
            _gate_hits(
                _oq("yes", "resolved", rationale="maintainer chose X on 2026-09-08")
            ),
            [],
        )

    def test_non_blocking_open_is_clean(self):
        """The 66-plan case. A plan in progress may carry an open non-blocking question."""
        self.assertEqual(_gate_hits(_oq("no", "open", owner="none")), [])

    def test_non_blocking_deferred_is_clean(self):
        self.assertEqual(
            _gate_hits(_oq("no", "deferred", rationale="waits on the release")),
            [],
        )

    def test_remedy_is_named_in_the_message(self):
        """A refusal must say what to DO, or it just relocates the confusion."""
        (msg,) = _gate_hits(_oq("yes", "open"))
        self.assertIn("/askme", msg)
        self.assertIn("Status: resolved", msg)
        self.assertIn("Blocking: no", msg)

    def test_question_id_is_named(self):
        (msg,) = _gate_hits(_oq("yes", "open"))
        self.assertIn("OQ-01", msg)


class EveryCheckpointTests(unittest.TestCase):
    """Property 1: the gate is checkpoint-INDEPENDENT, which is the reason it was added.

    `check_open_questions` is called unconditionally by `lint_text`, unlike `check_checkpoint`, so the
    proof is that a full lint at each checkpoint (and with none at all) is non-conforming.
    """

    PLAN = "# IPD: probe\n\n## Open questions\n\n" + _oq("yes", "open")

    def test_default_lint_is_not_conforming(self):
        """The measured hole: a DEFAULT lint used to report `conforming` for this exact state."""
        res = ipd_lint.lint_text(self.PLAN, directory="pending")
        self.assertTrue(any(_GATE_TEXT in d.message for d in res.diagnostics))

    def test_every_named_checkpoint_reports_it(self):
        for checkpoint in S.CHECKPOINTS:
            with self.subTest(checkpoint=checkpoint):
                res = ipd_lint.lint_text(
                    self.PLAN, checkpoint=checkpoint, directory="pending"
                )
                self.assertTrue(
                    any(_GATE_TEXT in d.message for d in res.diagnostics),
                    f"gate did not fire at checkpoint {checkpoint!r}",
                )


class NoDoubleReportTests(unittest.TestCase):
    """Property 3: a malformed question yields ONE actionable diagnostic, not two.

    A `Blocking: yes` + `Status: deferred` question is already a grammar error ("a blocking question
    may not be deferred"). The gate must not pile on: the author needs one instruction, and the
    structural error is the more specific one.
    """

    def test_grammar_error_is_reported_without_the_gate(self):
        block = _oq("yes", "deferred", rationale="waits")
        self.assertEqual(_gate_hits(block), [])
        self.assertEqual(len(_other_hits(block)), 1, _other_hits(block))

    def test_unparseable_blocking_value_does_not_also_fire_the_gate(self):
        block = _oq("maybe", "open")
        self.assertEqual(_gate_hits(block), [])
        self.assertTrue(_other_hits(block))


class RealCorpusTests(unittest.TestCase):
    """The gate must not fire on a plan that legitimately has nothing open."""

    def test_no_open_questions_section_is_clean(self):
        parsed = ipd_lint.parse("# IPD: probe\n\n## Goal\n\nnothing.\n")
        self.assertEqual(
            [
                d
                for d in ipd_lint.check_open_questions(parsed)
                if _GATE_TEXT in d.message
            ],
            [],
        )

    def test_the_scaffolded_default_is_clean(self):
        """`aw ipd scaffold` writes `Blocking: no` / `Status: open`; a fresh plan must lint clean."""
        self.assertEqual(
            _gate_hits(_oq("no", "open", owner="none", rationale="TODO.")),
            [],
        )


if __name__ == "__main__":
    unittest.main()

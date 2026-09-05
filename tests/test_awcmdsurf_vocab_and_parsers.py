"""Tests for awcmdsurf Order 01: the TYPE-noun vocabulary, TYPE_BACKENDS routing, exit-code helper,
and the six new noun-verb parsers."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import artifact_types as at
from agent_workflows import cli


class VocabTests(unittest.TestCase):
    def test_normalize(self) -> None:
        self.assertEqual(at.normalize_type("plan"), "plans")
        self.assertEqual(at.normalize_type("specs"), "specs")
        self.assertEqual(at.normalize_type("all"), "all")
        self.assertEqual(at.normalize_type("other"), "other")
        self.assertEqual(at.normalize_type("misc"), "other")

    def test_normalize_unknown_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            at.normalize_type("bogus")
        self.assertIn("valid types", str(ctx.exception))

    def test_expand(self) -> None:
        self.assertEqual(
            at.expand_types("all", supported=("plans", "specs")), ["plans", "specs"]
        )
        self.assertEqual(at.expand_types("plan", supported=("plans",)), ["plans"])
        with self.assertRaises(ValueError):
            at.expand_types("comms", supported=("plans",))


class DerivedVocabularyTests(unittest.TestCase):
    """The vocabulary is DERIVED from `layout.py` (spec `kw5y2s`, Set `wslayout` Order 02, `zvk796`).

    These pin the two properties the consolidation had to hold: it may not NARROW the live tuple,
    and the one widening it does make (`reviews`) is deliberate rather than accidental.
    """

    def test_derivation_does_not_narrow_the_pre_consolidation_vocabulary(self) -> None:
        # NON-NEGOTIABLE (plan-review PR-001): dropping `roadmaps` would break
        # `run_rename_roadmaps` / `run_group_roadmaps` and orphan the on-disk roadmap records, so
        # every pre-consolidation type and alias must survive the move to the layout model.
        for t in (
            "plans",
            "specs",
            "prompts",
            "research",
            "backlog",
            "walkthroughs",
            "roadmaps",
            "comms",
            "releases",
            "other",
        ):
            self.assertIn(t, at.ARTIFACT_TYPES)
        for alias, target in (
            ("plan", "plans"),
            ("spec", "specs"),
            ("prompt", "prompts"),
            ("walkthrough", "walkthroughs"),
            ("roadmap", "roadmaps"),
            ("comm", "comms"),
            ("research", "research"),
            ("backlog", "backlog"),
            ("release", "releases"),
            ("other", "other"),
            ("others", "other"),
            ("misc", "other"),
        ):
            self.assertEqual(at.normalize_type(alias), target)

    def test_reviews_is_now_an_accepted_type_noun(self) -> None:
        # THE ONE DELIBERATE WIDENING (maintainer UNION ruling, spec Section 3.2). `reviews` was
        # already a `record_producers.RecordClass` member while absent from `ARTIFACT_TYPES`, so the
        # derivation RECONCILES two live vocabularies. Before Order 02, `aw check reviews` exited 2
        # with "unknown artifact type 'reviews'".
        self.assertIn("reviews", at.ARTIFACT_TYPES)
        self.assertTrue(at.is_type_token("reviews"))
        self.assertEqual(at.normalize_type("reviews"), "reviews")
        self.assertEqual(at.normalize_type("review"), "reviews")

    def test_reviews_has_no_backend_and_no_status_lifecycle(self) -> None:
        # Accepting the NOUN must not make it a mutable work item: a review record has no status to
        # set, so it stays out of `TYPE_BACKENDS` and out of `selectors.KNOWN_PRIMARY_TYPES`.
        from agent_workflows import selectors

        self.assertNotIn("reviews", at.TYPE_BACKENDS)
        self.assertNotIn("reviews", selectors.KNOWN_PRIMARY_TYPES)
        self.assertIn("reviews", selectors.NON_PRIMARY_RECORD_DIRS)

    def test_records_root_alias_is_still_not_a_type_noun(self) -> None:
        # `records` is a legitimate `RecordClass` member but has never been a CLI type noun;
        # accepting it would silently widen the command surface.
        self.assertNotIn("records", at.ARTIFACT_TYPES)
        self.assertFalse(at.is_type_token("records"))
        with self.assertRaises(ValueError):
            at.normalize_type("records")

    def test_all_expansion_token_survives_the_derivation(self) -> None:
        # Every `aw <verb> all` invocation depends on this passing through unchanged.
        self.assertEqual(at.normalize_type("all"), "all")
        self.assertTrue(at.is_type_token("all"))
        self.assertNotIn("all", at.ARTIFACT_TYPES)

    def test_falsy_tokens_are_not_type_tokens(self) -> None:
        for token in (None, "", "   "):
            self.assertFalse(at.is_type_token(token))


class BackendMapTests(unittest.TestCase):
    def test_lookup(self) -> None:
        self.assertEqual(at.TYPE_BACKENDS["plans"]["rename"], "plans_refs.run_mv")
        self.assertIsNone(at.backend_name("specs", "index"))

    def test_no_eager_import(self) -> None:
        # importing artifact_types must not import the backend modules.
        import importlib

        importlib.reload(at)
        # after reload, the backend modules should still not be forced in (they may be present from
        # elsewhere, so just assert artifact_types itself declares strings, not callables).
        self.assertIsInstance(at.TYPE_BACKENDS["plans"]["index"], str)


class ExitCodeTests(unittest.TestCase):
    def test_codes(self) -> None:
        from agent_workflows.artifact_core import Drift

        self.assertEqual(at.exit_code_for([]), 0)
        self.assertEqual(at.exit_code_for([Drift("l", "r", "d")]), 1)
        self.assertEqual(at.EXIT_CANNOT_RUN, 2)


class ParserTests(unittest.TestCase):
    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def test_help_parses_for_all_six(self) -> None:
        for v in ("check", "find", "search", "index", "rename", "group"):
            rc, out, err = self._run([v, "--help"])
            self.assertEqual(rc, 0, f"{v} --help rc={rc}")

    def test_unknown_type_errors(self) -> None:
        rc, out, err = self._run(["check", "bogus"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()

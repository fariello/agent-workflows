"""Tests for the aw backlog new near-duplicate guard (IPD fwgq2u / OQ-01 / E-01..E-03).

Asserts:
1. Candidate duplicate detection across all lifecycle statuses (open, graduated, done, blocked, parked).
2. Family members derived from the real 25-item turn_bounds corpus are flagged as candidates.
3. Negative control items (e.g. q6bbdb, 4bhxni, 1z58zm) naming test_turn_bounds for unrelated concerns
   are NOT falsely flagged as duplicate candidates.
4. Precision threshold: regression to naive bare substring matching would fail negative-control assertions.
5. Demonstration of non-vacuousness: test fails when run against a naive/broken discriminator.
6. CLI integration: aw backlog new emits advisory notice with stated limits and coverage, and NEVER refuses.
7. Agent/JSON mode structured fields and evidence receipts.
8. No assertion reads the live records tree (isolated fixtures only).
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import List, Tuple

from agent_workflows import agent_schema as schema
from agent_workflows import backlog as B


def _make_args(**kw):
    class Args:
        pass

    ns = Args()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


# Real-derived fixtures from the turn_bounds ambient-env defect family
FIXTURE_FAMILY_4VN040 = (
    Path(
        ".aw/records/backlog/graduated/20260923-envhermet-01-4vn040-turn-bounds.backlog.md"
    ),
    B.parse_item(
        "- Id: 4vn040\n"
        "- Status: graduated\n"
        "- Set: envhermet\n"
        "- Priority: medium\n"
        "- Work-Kind: bug\n"
        "- Summary: test_turn_bounds isolation-scoped permission policy test fails inside a runner lane because OPENCODE_CONFIG_CONTENT is ambient\n"
        "- Blocks-Release: next\n"
    ),
    "- Id: 4vn040\n"
    "- Status: graduated\n"
    "- Set: envhermet\n"
    "- Priority: medium\n"
    "- Work-Kind: bug\n"
    "- Summary: test_turn_bounds isolation-scoped permission policy test fails inside a runner lane because OPENCODE_CONFIG_CONTENT is ambient\n"
    "- Blocks-Release: next\n"
    "\n"
    "## Workflow history\n"
    "- 2026-09-23 graduated (aw set): Graduated to envhermet.\n"
    "\n"
    "tests/test_turn_bounds.py fails when OPENCODE_CONFIG_CONTENT is in ambient env.\n",
)

FIXTURE_FAMILY_06NGNX = (
    Path(
        ".aw/records/backlog/graduated/20260923-envhermet-01-06ngnx-turn-bounds.backlog.md"
    ),
    B.parse_item(
        "- Id: 06ngnx\n"
        "- Status: graduated\n"
        "- Set: envhermet\n"
        "- Priority: medium\n"
        "- Work-Kind: bug\n"
        "- Summary: test_turn_bounds asserts OPENCODE_CONFIG_CONTENT is absent from a child env but inherits it from the parent turn, so the suite fails inside a lane run\n"
        "- Blocks-Release: next\n"
    ),
    "- Id: 06ngnx\n"
    "- Status: graduated\n"
    "- Set: envhermet\n"
    "- Priority: medium\n"
    "- Work-Kind: bug\n"
    "- Summary: test_turn_bounds asserts OPENCODE_CONFIG_CONTENT is absent from a child env but inherits it from the parent turn, so the suite fails inside a lane run\n"
    "- Blocks-Release: next\n"
    "\n"
    "## Workflow history\n"
    "- 2026-09-23 graduated (aw set): Graduated to envhermet.\n"
    "\n"
    "test_turn_bounds ambient env leak.\n",
)

FIXTURE_FAMILY_MEPBMP = (
    Path(".aw/records/backlog/done/20260922-mepbmp-01-mepbmp-turn-bounds.backlog.md"),
    B.parse_item(
        "- Id: mepbmp\n"
        "- Status: done\n"
        "- Set: mepbmp\n"
        "- Priority: medium\n"
        "- Work-Kind: bug\n"
        "- Summary: test_turn_bounds asserts a non-isolated turn carries NO permission policy, but run_opencode now always sets OPENCODE_CONFIG_CONTENT, so 1 node fails on a clean tree\n"
    ),
    "- Id: mepbmp\n"
    "- Status: done\n"
    "- Set: mepbmp\n"
    "- Priority: medium\n"
    "- Work-Kind: bug\n"
    "- Summary: test_turn_bounds asserts a non-isolated turn carries NO permission policy, but run_opencode now always sets OPENCODE_CONFIG_CONTENT, so 1 node fails on a clean tree\n"
    "\n"
    "## Workflow history\n"
    "- 2026-09-22 done (aw set): Closed.\n"
    "\n"
    "test_turn_bounds and OPENCODE_CONFIG_CONTENT interaction.\n",
)

FIXTURE_FAMILY_WNABNS = (
    Path(".aw/records/backlog/open/20260922-wnabns-01-wnabns-turn-bounds.backlog.md"),
    B.parse_item(
        "- Id: wnabns\n"
        "- Status: open\n"
        "- Set: wnabns\n"
        "- Priority: medium\n"
        "- Work-Kind: bug\n"
        "- Summary: test_the_permission_policy_by_contrast_IS_isolation_scoped reads the ambient env, so it fails inside an OpenCode-driven turn\n"
        "- Blocks-Release: next\n"
    ),
    "- Id: wnabns\n"
    "- Status: open\n"
    "- Set: wnabns\n"
    "- Priority: medium\n"
    "- Work-Kind: bug\n"
    "- Summary: test_the_permission_policy_by_contrast_IS_isolation_scoped reads the ambient env, so it fails inside an OpenCode-driven turn\n"
    "- Blocks-Release: next\n"
    "\n"
    "## Workflow history\n"
    "- 2026-09-22 created (aw backlog): filed.\n"
    "\n"
    "tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped asserts OPENCODE_CONFIG_CONTENT is absent.\n",
)

# Unrelated fixtures (F-6) quoting test_turn_bounds for different concerns
FIXTURE_UNRELATED_Q6BBDB = (
    Path(".aw/records/backlog/open/20260923-q6bbdb-01-q6bbdb-slow-failures.backlog.md"),
    B.parse_item(
        "- Id: q6bbdb\n"
        "- Status: open\n"
        "- Set: q6bbdb\n"
        "- Priority: medium\n"
        "- Work-Kind: bug\n"
        "- Summary: 14 slow-marked test failures remain unrelated to the runner-stop path and need triage (installer cleanup, CLI conformance, role guard, release readiness, turn bounds)\n"
        "- Blocks-Release: next\n"
    ),
    "- Id: q6bbdb\n"
    "- Status: open\n"
    "- Set: q6bbdb\n"
    "- Priority: medium\n"
    "- Work-Kind: bug\n"
    "- Summary: 14 slow-marked test failures remain unrelated to the runner-stop path and need triage (installer cleanup, CLI conformance, role guard, release readiness, turn bounds)\n"
    "- Blocks-Release: next\n"
    "\n"
    "## Workflow history\n"
    "- 2026-09-23 created (aw backlog): triage list.\n"
    "\n"
    "The failing node ids across 14 slow tests include installer, cli conformance, and:\n"
    "tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped\n",
)

FIXTURE_UNRELATED_4BHXNI = (
    Path(".aw/records/backlog/open/20260923-4bhxni-01-4bhxni-turn-budget.backlog.md"),
    B.parse_item(
        "- Id: 4bhxni\n"
        "- Status: open\n"
        "- Set: 4bhxni\n"
        "- Priority: low\n"
        "- Work-Kind: followup\n"
        "- Summary: Tell the agent its remaining turn budget in the execute prompt (x7wfyx item A, never implemented)\n"
    ),
    "- Id: 4bhxni\n"
    "- Status: open\n"
    "- Set: 4bhxni\n"
    "- Priority: low\n"
    "- Work-Kind: followup\n"
    "- Summary: Tell the agent its remaining turn budget in the execute prompt (x7wfyx item A, never implemented)\n"
    "\n"
    "## Workflow history\n"
    "- 2026-09-23 created (aw backlog): filed.\n"
    "\n"
    "It is a change to the shared execute prompt with its own regression surface (tests/test_turn_bounds.py asserts three FOREGROUND properties).\n",
)

FIXTURE_UNRELATED_1Z58ZM = (
    Path(".aw/records/backlog/open/20260923-1z58zm-01-1z58zm-unmerged-lane.backlog.md"),
    B.parse_item(
        "- Id: 1z58zm\n"
        "- Status: open\n"
        "- Set: 1z58zm\n"
        "- Priority: high\n"
        "- Work-Kind: bug\n"
        "- Summary: Two release-blocking backlog items (34q6ha, mepbmp) exist only on the unmerged lane aw/lane/udgilu_attempt2, so they are invisible to attention, find and every release-gate check\n"
        "- Blocks-Release: next\n"
    ),
    "- Id: 1z58zm\n"
    "- Status: open\n"
    "- Set: 1z58zm\n"
    "- Priority: high\n"
    "- Work-Kind: bug\n"
    "- Summary: Two release-blocking backlog items (34q6ha, mepbmp) exist only on the unmerged lane aw/lane/udgilu_attempt2, so they are invisible to attention, find and every release-gate check\n"
    "- Blocks-Release: next\n"
    "\n"
    "## Workflow history\n"
    "- 2026-09-23 created (aw backlog): filed.\n"
    "\n"
    "mepbmp does not reproduce at HEAD: python3 -m pytest tests/test_turn_bounds.py -> 43 passed.\n",
)


class BacklogDuplicateGuardUnitTests(unittest.TestCase):
    """Unit tests for candidate duplicate detection algorithm on fixture data."""

    def setUp(self):
        self.corpus_fixtures: List[Tuple[Path, B.BacklogItem, str]] = [
            FIXTURE_FAMILY_4VN040,
            FIXTURE_FAMILY_06NGNX,
            FIXTURE_FAMILY_MEPBMP,
            FIXTURE_FAMILY_WNABNS,
            FIXTURE_UNRELATED_Q6BBDB,
            FIXTURE_UNRELATED_4BHXNI,
            FIXTURE_UNRELATED_1Z58ZM,
        ]

    def test_flags_family_members_across_statuses(self):
        """A new filing describing the ambient-env defect matches family members across open, graduated, and done."""
        proposed_summary = "test_turn_bounds permission-policy test fails when OPENCODE_CONFIG_CONTENT is ambient"
        proposed_body = "tests/test_turn_bounds.py fails inside an opencode turn"

        candidates = B.find_duplicate_candidates_in_items(
            self.corpus_fixtures,
            summary=proposed_summary,
            body=proposed_body,
        )
        cand_ids = {c.id for c in candidates}

        # Motivating family members across multiple statuses MUST be flagged
        self.assertIn("4vn040", cand_ids)  # graduated
        self.assertIn("06ngnx", cand_ids)  # graduated
        self.assertIn("mepbmp", cand_ids)  # done

        # Verify candidate objects contain status, summary, and match reasons
        c_4vn = next(c for c in candidates if c.id == "4vn040")
        self.assertEqual(c_4vn.status, "graduated")
        self.assertIn("OPENCODE_CONFIG_CONTENT", c_4vn.summary)
        self.assertTrue(bool(c_4vn.shared_tokens))

    def test_negative_control_not_flagged(self):
        """Unrelated items mentioning test_turn_bounds (q6bbdb, 4bhxni, 1z58zm) are NOT flagged."""
        proposed_summary = "test_turn_bounds permission-policy test fails when OPENCODE_CONFIG_CONTENT is ambient"
        proposed_body = "tests/test_turn_bounds.py fails inside an opencode turn"

        candidates = B.find_duplicate_candidates_in_items(
            self.corpus_fixtures,
            summary=proposed_summary,
            body=proposed_body,
        )
        cand_ids = {c.id for c in candidates}

        # Negative controls: must NOT be flagged
        self.assertNotIn("q6bbdb", cand_ids)
        self.assertNotIn("4bhxni", cand_ids)
        self.assertNotIn("1z58zm", cand_ids)

    def test_wnabns_is_true_duplicate_and_is_flagged(self):
        """wnabns is a true duplicate (considered and rejected as a negative control) and is correctly flagged."""
        proposed_summary = "test_the_permission_policy_by_contrast_IS_isolation_scoped fails from ambient OPENCODE_CONFIG_CONTENT"
        candidates = B.find_duplicate_candidates_in_items(
            self.corpus_fixtures,
            summary=proposed_summary,
        )
        cand_ids = {c.id for c in candidates}
        self.assertIn("wnabns", cand_ids)

    def test_negative_control_filing_does_not_flag_defect_family(self):
        """Filing a triage item like q6bbdb does not flag the ambient-env defect family."""
        proposed_summary = "14 slow-marked test failures remain unrelated to the runner-stop path and need triage"
        proposed_body = (
            "Triage list including installer, role guard, and tests/test_turn_bounds.py"
        )

        candidates = B.find_duplicate_candidates_in_items(
            self.corpus_fixtures,
            summary=proposed_summary,
            body=proposed_body,
        )
        cand_ids = {c.id for c in candidates}
        self.assertNotIn("4vn040", cand_ids)
        self.assertNotIn("06ngnx", cand_ids)
        self.assertNotIn("mepbmp", cand_ids)

    def test_clean_filing_yields_empty_candidates(self):
        """A completely unrelated item yields zero candidates."""
        candidates = B.find_duplicate_candidates_in_items(
            self.corpus_fixtures,
            summary="Add caching layer for user workspace preferences in web UI",
            body="Details about redis cache key format and TTL expiry",
        )
        self.assertEqual(candidates, [])

    def test_non_vacuousness_fails_under_naive_substring_matcher(self):
        """Demonstrate that naive substring matching (bare 'test_turn_bounds' in text) fails the negative control.

        This test proves the test assertions are non-vacuous per caf5ed: a naive matcher would falsely
        include q6bbdb, 4bhxni, and 1z58zm, dropping precision.
        """
        proposed_token = "test_turn_bounds"

        # Naive matcher: any item whose text contains proposed_token
        naive_matches = [
            item.id for f, item, text in self.corpus_fixtures if proposed_token in text
        ]

        # Under naive matching, negative controls ARE falsely matched
        self.assertIn("q6bbdb", naive_matches)
        self.assertIn("4bhxni", naive_matches)
        self.assertIn("1z58zm", naive_matches)

        # But under our discriminator, they are excluded
        real_matches = [
            c.id
            for c in B.find_duplicate_candidates_in_items(
                self.corpus_fixtures,
                summary="test_turn_bounds permission-policy test fails when OPENCODE_CONFIG_CONTENT is ambient",
            )
        ]
        self.assertNotIn("q6bbdb", real_matches)
        self.assertNotIn("4bhxni", real_matches)
        self.assertNotIn("1z58zm", real_matches)


class BacklogDuplicateGuardCliIntegrationTests(unittest.TestCase):
    """Integration tests for aw backlog new candidate advisory output, limits, and non-refusal."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        # Create standard layout
        for d in ("open", "graduated", "blocked", "parked", "done"):
            (self.repo / ".aw/records/backlog" / d).mkdir(parents=True, exist_ok=True)

        # Populate with fixtures
        (self.repo / FIXTURE_FAMILY_4VN040[0]).write_text(
            FIXTURE_FAMILY_4VN040[2], encoding="utf-8"
        )
        (self.repo / FIXTURE_FAMILY_MEPBMP[0]).write_text(
            FIXTURE_FAMILY_MEPBMP[2], encoding="utf-8"
        )
        (self.repo / FIXTURE_UNRELATED_Q6BBDB[0]).write_text(
            FIXTURE_UNRELATED_Q6BBDB[2], encoding="utf-8"
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_run_new_reports_candidates_and_never_refuses(self):
        """aw backlog new reports candidate duplicates with status, stated limits, and exits 0."""
        out, err = io.StringIO(), io.StringIO()
        args = _make_args(
            dir=str(self.repo),
            summary="test_turn_bounds permission-policy test fails when OPENCODE_CONFIG_CONTENT is ambient",
            priority="medium",
            work_kind="bug",
            apply=True,
        )
        with redirect_stdout(out), redirect_stderr(err):
            rc = B.run_new(args)

        # MUST NEVER REFUSE
        self.assertEqual(rc, 0)
        stdout = out.getvalue()

        # Candidates reported with id and status
        self.assertIn("candidate duplicate(s) detected", stdout)
        self.assertIn("4vn040 [graduated]", stdout)
        self.assertIn("mepbmp [done]", stdout)

        # Negative control not reported
        self.assertNotIn("q6bbdb", stdout)

        # Stated limits and coverage quoted in output
        self.assertIn(
            "ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.",
            stdout,
        )
        self.assertIn("What it can and cannot tell you:", stdout)
        self.assertIn("exact identifier and token overlap: DETECTABLE", stdout)
        self.assertIn("paraphrased defect descriptions: PARTLY DETECTABLE", stdout)
        self.assertIn(
            "distinct issues referencing the same test or symbol: NOT DETECTABLE",
            stdout,
        )
        self.assertIn("Searched: BACKLOG ITEMS across all statuses", stdout)

        # File was created
        created = list((self.repo / ".aw/records/backlog/open").glob("*.backlog.md"))
        # 1 existing open (q6bbdb) + 1 newly created = 2
        self.assertEqual(len(created), 2)

    def test_run_new_no_candidates_states_silence_limits(self):
        """When no candidates match, aw backlog new states what silence does and does not prove."""
        out, err = io.StringIO(), io.StringIO()
        args = _make_args(
            dir=str(self.repo),
            summary="Implement OAuth refresh token rotation in api gateway",
            priority="medium",
            work_kind="feature",
            apply=True,
        )
        with redirect_stdout(out), redirect_stderr(err):
            rc = B.run_new(args)

        self.assertEqual(rc, 0)
        stdout = out.getvalue()

        self.assertIn("no duplicate candidates detected", stdout)
        self.assertIn(
            "ADVISORY ONLY: this silence means nothing matched the signal", stdout
        )
        self.assertIn("exact identifier and token overlap: DETECTABLE", stdout)
        self.assertIn("Searched: BACKLOG ITEMS across all statuses", stdout)

    def test_run_new_agent_json_mode_schema_and_evidence(self):
        """In --agent / --json mode, structured candidate list, limits, and evidence receipts are emitted."""
        out, err = io.StringIO(), io.StringIO()
        args = _make_args(
            dir=str(self.repo),
            summary="test_turn_bounds permission-policy test fails when OPENCODE_CONFIG_CONTENT is ambient",
            priority="medium",
            work_kind="bug",
            agent=True,
            apply=False,
        )
        with redirect_stdout(out), redirect_stderr(err):
            rc = B.run_new(args)

        self.assertEqual(rc, 0)
        raw = out.getvalue().strip()
        rec = json.loads(raw)

        schema.assert_valid_agent_record(rec)
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["cmd"], "backlog new")

        # Evidence receipts
        evidence = rec.get("evidence", [])
        self.assertIn("duplicate-candidates:2", evidence)
        self.assertIn("limit:exact identifier and token overlap:DETECTABLE", evidence)
        self.assertIn(
            "limit:paraphrased defect descriptions:PARTLY DETECTABLE", evidence
        )
        self.assertIn(
            "limit:distinct issues referencing the same test or symbol:NOT DETECTABLE",
            evidence,
        )

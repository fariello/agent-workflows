"""Behavioral contract tests for aw find --limit bounding on human and --paths surfaces.

IPD i00j2o (no88yi):
Make aw find --limit bound the human row listing and the --paths listing,
and say how many rows were omitted with a runnable continuation.
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import cli

EXPECTED_PLANS_PATHS = (
    ".aw/records/plans/pending/20260927-setalpha-01-pln001-plan-one.ipd.md\n"
    ".aw/records/plans/pending/20260927-setalpha-02-pln002-plan-two.ipd.md\n"
    ".aw/records/plans/executed/20260927-setbeta-01-pln003-plan-three.ipd.md\n"
)

EXPECTED_PLANS_HUMAN = (
    "◕  pending       pln001  setalpha        .aw/records/plans/pending/20260927-setalpha-01-pln001-plan-one.ipd.md\n"
    "◕  pending       pln002  setalpha        .aw/records/plans/pending/20260927-setalpha-02-pln002-plan-two.ipd.md\n"
    "✓  executed      pln003  setbeta         .aw/records/plans/executed/20260927-setbeta-01-pln003-plan-three.ipd.md\n"
)


class TestFindHumanLimit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_find_human_limit_")
        self.repo_root = Path(self.temp_dir)

        # 1. Three plans across two dispositions (pending, executed)
        plans_pending = self.repo_root / ".aw" / "records" / "plans" / "pending"
        plans_executed = self.repo_root / ".aw" / "records" / "plans" / "executed"
        plans_pending.mkdir(parents=True, exist_ok=True)
        plans_executed.mkdir(parents=True, exist_ok=True)

        self.plan_1 = plans_pending / "20260927-setalpha-01-pln001-plan-one.ipd.md"
        self.plan_1.write_text(
            "# IPD: Plan One\n\n- Id: pln001\n- Status: approved\n- Set: setalpha\n",
            encoding="utf-8",
        )
        self.plan_2 = plans_pending / "20260927-setalpha-02-pln002-plan-two.ipd.md"
        self.plan_2.write_text(
            "# IPD: Plan Two\n\n- Id: pln002\n- Status: draft\n- Set: setalpha\n",
            encoding="utf-8",
        )
        self.plan_3 = plans_executed / "20260927-setbeta-01-pln003-plan-three.ipd.md"
        self.plan_3.write_text(
            "# IPD: Plan Three\n\n- Id: pln003\n- Status: executed\n- Set: setbeta\n",
            encoding="utf-8",
        )

        # 2. One spec in to-review
        specs_to_review = self.repo_root / ".aw" / "records" / "specs" / "to-review"
        specs_to_review.mkdir(parents=True, exist_ok=True)
        self.spec_1 = specs_to_review / "20260927-setalpha-01-spc001-spec-one.spec.md"
        self.spec_1.write_text(
            "# Spec: Spec One\n\n- Id: spc001\n- Status: to-review\n- Set: setalpha\n",
            encoding="utf-8",
        )

        # 3. One backlog item in open
        bkl_open = self.repo_root / ".aw" / "records" / "backlog" / "open"
        bkl_open.mkdir(parents=True, exist_ok=True)
        self.bkl_1 = bkl_open / "20260927-setbeta-01-bkl001-item-one.backlog.md"
        self.bkl_1.write_text(
            "- Id: bkl001\n- Status: open\n- Set: setbeta\n- Work-Kind: bug\n- Priority: high\n\n## Summary\nBacklog One\n",
            encoding="utf-8",
        )

        # 4. Cross-type id6 collision fixture (col001 claimed by both spec and backlog)
        self.coll_spec = (
            specs_to_review / "20260927-setalpha-01-col001-coll-spec.spec.md"
        )
        self.coll_spec.write_text(
            "# Spec: Coll Spec\n\n- Id: col001\n- Status: to-review\n- Set: setalpha\n",
            encoding="utf-8",
        )
        self.coll_bkl = bkl_open / "20260927-setalpha-01-col001-coll-bkl.backlog.md"
        self.coll_bkl.write_text(
            "- Id: col001\n- Status: open\n- Set: setalpha\n- Work-Kind: bug\n- Priority: low\n\n## Summary\nColl Backlog\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_find(self, extra_args: list[str]) -> tuple[int, str, str]:
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with patch("sys.stdout", buf_out), patch("sys.stderr", buf_err):
            rc = cli.main(["find", *extra_args, "--dir", str(self.repo_root)])
        return rc, buf_out.getvalue(), buf_err.getvalue()

    def test_01_human_row_limit_bounding_and_notice(self):
        """E-01(1): find plans --no-color --limit 2 prints exactly the first 2 rows of
        unbounded output, followed by an omitted-rows notice stating 2 shown of 3 total
        and Next line whose command is 'aw find plans --limit 3'.
        """
        rc, out, err = self.run_find(["plans", "--no-color", "--limit", "2"])
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

        unbounded_lines = EXPECTED_PLANS_HUMAN.splitlines()
        out_lines = out.splitlines()

        # Must print exactly the first 2 rows
        self.assertGreaterEqual(len(out_lines), 2)
        self.assertEqual(out_lines[:2], unbounded_lines[:2])

        # Followed by blank line, omitted-rows notice, and Next continuation
        self.assertEqual(
            len(out_lines),
            5,
            f"Expected 5 output lines, got {len(out_lines)}: {out_lines}",
        )
        self.assertEqual(out_lines[2], "")
        self.assertIn("showing 2 of 3 matches (1 omitted)", out_lines[3])
        self.assertIn("Next  aw find plans --limit 3", out_lines[4])
        self.assertIn("(list every match)", out_lines[4])

    def test_02_limit_at_or_above_count_byte_identical(self):
        """E-01(2): With --limit at or above row count, output is byte-identical to unbounded
        run and carries no notice.
        """
        for lim in ("3", "4", "99"):
            rc, out, err = self.run_find(["plans", "--no-color", "--limit", lim])
            self.assertEqual(rc, 0)
            self.assertEqual(err, "")
            self.assertEqual(out, EXPECTED_PLANS_HUMAN)

    def test_03_paths_limit_bounding_and_notice_on_stderr(self):
        """E-01(3): find plans --paths --limit 2 prints exactly the first 2 lines of
        find plans --paths on stdout and nothing else there, with omitted notice on stderr.
        """
        rc, out, err = self.run_find(["plans", "--paths", "--limit", "2"])
        self.assertEqual(rc, 0)

        unbounded_paths = EXPECTED_PLANS_PATHS.splitlines()
        out_paths = out.splitlines()
        self.assertEqual(out_paths, unbounded_paths[:2])

        # Notice is on stderr
        err_lines = err.splitlines()
        self.assertGreaterEqual(len(err_lines), 2)
        self.assertIn("showing 2 of 3 matches (1 omitted)", err_lines[0])
        self.assertTrue(
            any(
                "aw find plans" in line and "--limit 3" in line and "--paths" in line
                for line in err_lines
            )
        )

    def test_04_paths_limit_at_or_above_count_byte_identical(self):
        """E-01(4): --paths --limit at or above count leaves stdout byte-identical to
        unbounded --paths and stderr empty.
        """
        for lim in ("3", "5", "100"):
            rc, out, err = self.run_find(["plans", "--paths", "--limit", lim])
            self.assertEqual(rc, 0)
            self.assertEqual(err, "")
            self.assertEqual(out, EXPECTED_PLANS_PATHS)

    def test_05_paths_limit_matches_agent_items(self):
        """E-01(5): The paths printed under --limit 2 equal the path fields of the 2
        item records find plans --agent --limit 2 emits.
        """
        rc_paths, out_paths, _ = self.run_find(["plans", "--paths", "--limit", "2"])
        self.assertEqual(rc_paths, 0)
        paths = [line.strip() for line in out_paths.splitlines() if line.strip()]

        rc_agent, out_agent, _ = self.run_find(["plans", "--agent", "--limit", "2"])
        self.assertEqual(rc_agent, 0)
        agent_lines = [line.strip() for line in out_agent.splitlines() if line.strip()]
        agent_items = [
            json.loads(line)
            for line in agent_lines
            if json.loads(line).get("kind") == "item"
        ]
        agent_paths = [it["path"] for it in agent_items]

        self.assertEqual(len(paths), 2)
        self.assertEqual(paths, agent_paths)

    def test_06_selector_filtered_limit_and_continuation(self):
        """E-01(6): A selector plus --limit (find plans setalpha --limit 1) bounds the
        filtered rows and its Next command carries the selector.
        """
        rc, out, err = self.run_find(
            ["plans", "setalpha", "--no-color", "--limit", "1"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

        out_lines = out.splitlines()
        self.assertGreaterEqual(len(out_lines), 4)
        self.assertIn("pln001", out_lines[0])
        self.assertEqual(out_lines[1], "")
        self.assertIn("showing 1 of 2 matches (1 omitted)", out_lines[2])
        self.assertIn("Next  aw find plans setalpha --limit 2", out_lines[3])

    def test_07_exit_code_zero_for_bounded_queries(self):
        """E-01(7): Exit code is 0 in every bounded case."""
        cases = [
            ["plans", "--no-color", "--limit", "1"],
            ["plans", "--paths", "--limit", "1"],
            ["plans", "setalpha", "--no-color", "--limit", "1"],
            ["all", "--no-color", "--limit", "2"],
        ]
        for c in cases:
            rc, _, _ = self.run_find(c)
            self.assertEqual(rc, 0, f"Expected exit code 0 for query {c}, got {rc}")

    def test_08_invariance_unflagged_and_json(self):
        """E-01(8): Unflagged human output, unflagged --paths, and --json with and without
        --limit are captured and asserted unchanged.
        """
        rc_h, out_h, err_h = self.run_find(["plans", "--no-color"])
        self.assertEqual(rc_h, 0)
        self.assertEqual(err_h, "")
        self.assertEqual(out_h, EXPECTED_PLANS_HUMAN)

        rc_p, out_p, err_p = self.run_find(["plans", "--paths"])
        self.assertEqual(rc_p, 0)
        self.assertEqual(err_p, "")
        self.assertEqual(out_p, EXPECTED_PLANS_PATHS)

        # --json without limit
        rc_j1, out_j1, err_j1 = self.run_find(["plans", "--json"])
        self.assertEqual(rc_j1, 0)
        self.assertEqual(err_j1, "")
        doc1 = json.loads(out_j1)
        self.assertEqual(doc1.get("status"), "clean")
        self.assertEqual(len(doc1.get("data", {}).get("matches", [])), 3)

        # --json with --limit remains unbounded full dictionary
        rc_j2, out_j2, err_j2 = self.run_find(["plans", "--json", "--limit", "1"])
        self.assertEqual(rc_j2, 0)
        self.assertEqual(err_j2, "")
        doc2 = json.loads(out_j2)
        self.assertEqual(doc2.get("status"), "clean")
        self.assertEqual(len(doc2.get("data", {}).get("matches", [])), 3)

    def test_09_collisions_not_bounded(self):
        """E-01(9): Over the col001 spec-plus-backlog collision pair, find all col001
        --no-color --limit 1 prints exactly 1 row, then the omitted notice and Next line,
        then the find.id6-collision warning naming BOTH claimant paths, in that order.
        """
        rc, out, err = self.run_find(["all", "col001", "--no-color", "--limit", "1"])
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

        out_lines = out.splitlines()
        # Row 0: first match
        self.assertIn("col001", out_lines[0])
        # Row 1: blank line
        self.assertEqual(out_lines[1], "")
        # Row 2: omitted notice
        self.assertIn("showing 1 of 2 matches (1 omitted)", out_lines[2])
        # Row 3: Next line
        self.assertIn("Next  aw find all col001 --limit 2", out_lines[3])

        # Followed by collision warning naming both claimant paths
        full_text = "\n".join(out_lines[4:])
        self.assertIn("is claimed as its OWN identity", full_text)
        self.assertIn(
            "specs/to-review/20260927-setalpha-01-col001-coll-spec.spec.md", full_text
        )
        self.assertIn(
            "backlog/open/20260927-setalpha-01-col001-coll-bkl.backlog.md", full_text
        )

    def test_10_brace_and_space_selectors_human_surface(self):
        """E-01(10): With plans containing {x} and has space, find plans '{x}' 'has space'
        --no-color --limit 1 prints a Next line containing '{x}' and 'has space' and NOT {{x}}.
        """
        p_dir = self.repo_root / ".aw" / "records" / "plans" / "pending"
        (
            p_dir / "20260927-setalpha-04-pln004-special-{x}-has space-one.ipd.md"
        ).write_text(
            "- Id: pln004\n- Status: draft\n- Set: setalpha\n", encoding="utf-8"
        )
        (
            p_dir / "20260927-setalpha-05-pln005-special-{x}-has space-two.ipd.md"
        ).write_text(
            "- Id: pln005\n- Status: draft\n- Set: setalpha\n", encoding="utf-8"
        )

        rc, out, err = self.run_find(
            ["plans", "{x}", "has space", "--no-color", "--limit", "1"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

        next_lines = [line for line in out.splitlines() if line.startswith("Next")]
        self.assertEqual(len(next_lines), 1, f"Expected 1 Next line in output: {out}")
        next_cmd = next_lines[0]
        self.assertIn("'{x}'", next_cmd)
        self.assertIn("'has space'", next_cmd)
        self.assertNotIn("{{x}}", next_cmd)

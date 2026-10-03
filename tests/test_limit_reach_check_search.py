"""Behavioral tests for --limit token-control and search hit payload on aw check and aw search.

IPD 2zvxhx (limitreach-01).

Drives a fixture repository through `cli.main` with `--dir <fixture>`, asserting:
- Agent assertion (1): check with no --limit carries every fixture finding, while --limit bounds diagnostics.
- Agent assertion (2): check with --limit N emits N diagnostics with total, emitted, omitted, and next continuation.
- Agent assertion (3): validate_agent_record returns [] for bounded check record.
- Agent assertion (4): exit code and outcome are unchanged by bound, while complete flips to False when truncated.
- Agent assertion (5): findings still reports true total, not the emitted count.
- Agent assertion (6): search with no --limit reports hit count equal to --json hits over the same fixture.
- Agent assertion (7): search with --limit N emits N hits with total/emitted/omitted, complete: false, outcome: partial.
- Agent assertion (8): every emitted search record carries matches and validates cleanly under validate_agent_record.
- Agent assertion (9): search zero-match case keeps its current exit code and includes empty matches payload.
- Surface invariance: human output and --json output are invariant across check and search.
- Non-positive limit refusal (E-05): --limit 0 and --limit -1 exit 2 with cannot-run on both verbs.

GUIDING_PRINCIPLES P16 compliance: zero code-pinning tests; no inspection of production source code;
every assertion obtains its facts from cli.main exit codes and rendered stdout/stderr streams.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Dict, Tuple

from agent_workflows import agent_schema, cli
from tests.test_check_engine_release_gate import _create_minimal_repo


class FixtureRepoBase(unittest.TestCase):
    """Hermetic fixture repository with a known number of check findings and search hits."""

    FIXTURE_FINDINGS_COUNT = 5
    FIXTURE_SEARCH_HITS_COUNT = 5
    SEARCH_QUERY = "SEARCH_HIT_TOKEN"

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = _create_minimal_repo(Path(self.tmp.name))

        # Seed exactly 5 live ungated bug items under backlog/open.
        # These produce:
        # - exactly 5 findings under `aw check release-gates` (rule: check.live-bug-ungated)
        # - exactly 5 hits under `aw search backlog SEARCH_HIT_TOKEN`
        self.backlog_open = self.repo / ".aw" / "records" / "backlog" / "open"
        for i in range(self.FIXTURE_FINDINGS_COUNT):
            item_file = (
                self.backlog_open
                / f"20261001-bkl00{i}-01-bkl00{i}-defect-{i}.backlog.md"
            )
            item_file.write_text(
                f"- Id: bkl00{i}\n"
                f"- Status: open\n"
                f"- Set: bkl00{i}\n"
                f"- Priority: medium\n"
                f"- Work-Kind: bug\n"
                f"- Summary: Live ungated bug {i} {self.SEARCH_QUERY}\n",
                encoding="utf-8",
            )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _run_cli(self, *args: str) -> Tuple[int, str, str]:
        """Run cli.main with given arguments pointing to the fixture repo, capturing stdout and stderr."""
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        argv = list(args) + ["--dir", str(self.repo)]
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = cli.main(argv)
        return rc, out_buf.getvalue(), err_buf.getvalue()

    def _run_agent(self, *args: str) -> Dict[str, Any]:
        """Run command under --agent and return parsed first JSONL record."""
        rc, out, err = self._run_cli(*args, "--agent")
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertTrue(
            lines, f"Expected agent JSONL output, got empty stdout. stderr: {err}"
        )
        return json.loads(lines[0])

    def _run_agent_with_rc(self, *args: str) -> Tuple[int, Dict[str, Any]]:
        """Run command under --agent and return process exit code and parsed first JSONL record."""
        rc, out, err = self._run_cli(*args, "--agent")
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertTrue(
            lines, f"Expected agent JSONL output, got empty stdout. stderr: {err}"
        )
        return rc, json.loads(lines[0])

    def _run_json(self, *args: str) -> Dict[str, Any]:
        """Run command under --json and return parsed JSON result."""
        rc, out, err = self._run_cli(*args, "--json")
        self.assertTrue(
            out.strip(), f"Expected JSON output, got empty stdout. stderr: {err}"
        )
        return json.loads(out)


class TestAgentAssertions(FixtureRepoBase):
    """The nine agent assertions specified in E-01 / V-01."""

    def test_01_check_unbounded_carries_every_finding_and_limit_bounds(self) -> None:
        """(1) with no --limit, the result record carries every fixture finding (5 diagnostics);
        with --limit N, diagnostics are bounded to N.
        """
        rec_unbounded = self._run_agent("check", "release-gates")
        self.assertEqual(
            len(rec_unbounded.get("diagnostics", [])), self.FIXTURE_FINDINGS_COUNT
        )
        self.assertEqual(rec_unbounded.get("findings"), self.FIXTURE_FINDINGS_COUNT)

        rec_bounded = self._run_agent("check", "release-gates", "--limit", "2")
        self.assertEqual(len(rec_bounded.get("diagnostics", [])), 2)

    def test_02_check_limit_bounds_diagnostics_and_counts(self) -> None:
        """(2) with --limit N below the fixture's finding count, exactly N diagnostics are present,
        emitted == N, omitted == total - N, total equals the fixture's finding count, and next is a runnable continuation.
        """
        rec = self._run_agent("check", "release-gates", "--limit", "2")
        self.assertEqual(len(rec.get("diagnostics", [])), 2)
        self.assertEqual(rec.get("emitted"), 2)
        self.assertEqual(rec.get("omitted"), 3)
        self.assertEqual(rec.get("total"), self.FIXTURE_FINDINGS_COUNT)
        self.assertIn("next", rec)
        self.assertTrue(rec["next"] and "aw check release-gates" in rec["next"])

    def test_03_check_bounded_record_schema_and_counts_valid(self) -> None:
        """(3) agent_schema.validate_agent_record returns [] for the bounded record carrying total/emitted/omitted."""
        rec = self._run_agent("check", "release-gates", "--limit", "2")
        self.assertIn("omitted", rec)
        self.assertEqual(rec.get("omitted"), 3)
        errs = agent_schema.validate_agent_record(rec)
        self.assertEqual(errs, [])

    def test_04_check_limit_exit_outcome_unchanged_and_complete_false(self) -> None:
        """(4) the exit code and outcome are UNCHANGED by the bound, and complete flips to false when truncated."""
        rec_unbounded = self._run_agent("check", "release-gates")
        rec_bounded = self._run_agent("check", "release-gates", "--limit", "2")

        self.assertEqual(rec_bounded.get("exit"), rec_unbounded.get("exit"))
        self.assertEqual(rec_bounded.get("outcome"), rec_unbounded.get("outcome"))
        self.assertIs(rec_unbounded.get("complete"), True)
        self.assertIs(rec_bounded.get("complete"), False)

    def test_05_check_limit_findings_reports_true_total(self) -> None:
        """(5) findings still reports the TRUE total (5), not the emitted count (2)."""
        rec = self._run_agent("check", "release-gates", "--limit", "2")
        self.assertEqual(rec.get("findings"), self.FIXTURE_FINDINGS_COUNT)
        self.assertEqual(len(rec.get("diagnostics", [])), 2)
        self.assertNotEqual(rec.get("findings"), len(rec.get("diagnostics", [])))

    def test_06_search_unbounded_hit_count_equals_json(self) -> None:
        """(6) with no --limit, the --agent record's reported hit count equals what --json reports on the same query."""
        rec_agent = self._run_agent("search", "backlog", self.SEARCH_QUERY)
        rec_json = self._run_json("search", "backlog", self.SEARCH_QUERY)

        self.assertEqual(rec_json["data"]["hits"], self.FIXTURE_SEARCH_HITS_COUNT)
        self.assertEqual(rec_agent.get("findings"), rec_json["data"]["hits"])

    def test_07_search_limit_bounds_hits_and_outcome_partial(self) -> None:
        """(7) with --limit N, exactly N hits are emitted with total/emitted/omitted, a next,
        complete: false and outcome: partial; with --limit at or above hit count, record is complete: true.
        """
        rec_bounded = self._run_agent(
            "search", "backlog", self.SEARCH_QUERY, "--limit", "2"
        )
        self.assertEqual(rec_bounded.get("outcome"), "partial")
        self.assertIs(rec_bounded.get("complete"), False)
        self.assertEqual(rec_bounded.get("emitted"), 2)
        self.assertEqual(rec_bounded.get("omitted"), 3)
        self.assertEqual(rec_bounded.get("total"), self.FIXTURE_SEARCH_HITS_COUNT)
        self.assertEqual(len(rec_bounded.get("matches", [])), 2)

        rec_above = self._run_agent(
            "search", "backlog", self.SEARCH_QUERY, "--limit", "10"
        )
        self.assertEqual(rec_above.get("outcome"), "clean")
        self.assertIs(rec_above.get("complete"), True)

    def test_08_search_records_carry_matches_and_validate(self) -> None:
        """(8) every emitted search record carries matches and validates cleanly under agent_schema.validate_agent_record."""
        rec_agent = self._run_agent("search", "backlog", self.SEARCH_QUERY)
        self.assertIn("matches", rec_agent)
        self.assertEqual(
            len(rec_agent.get("matches", [])), self.FIXTURE_SEARCH_HITS_COUNT
        )
        self.assertEqual(agent_schema.validate_agent_record(rec_agent), [])

        rec_bounded = self._run_agent(
            "search", "backlog", self.SEARCH_QUERY, "--limit", "2"
        )
        self.assertIn("matches", rec_bounded)
        self.assertEqual(len(rec_bounded.get("matches", [])), 2)
        self.assertEqual(agent_schema.validate_agent_record(rec_bounded), [])

    def test_09_search_zero_match_exit_code_and_matches_payload(self) -> None:
        """(9) the zero-match case keeps its current exit code (1) and carries empty matches payload."""
        rc_unbounded, rec_unbounded = self._run_agent_with_rc(
            "search", "backlog", "NONEXISTENT_KEYWORD"
        )
        rc_bounded, rec_bounded = self._run_agent_with_rc(
            "search", "backlog", "NONEXISTENT_KEYWORD", "--limit", "2"
        )

        self.assertEqual(rc_unbounded, 1)
        self.assertEqual(rc_bounded, 1)
        self.assertEqual(rec_unbounded.get("exit"), 1)
        self.assertEqual(rec_bounded.get("exit"), 1)
        self.assertIn("matches", rec_unbounded)
        self.assertEqual(rec_unbounded.get("matches"), [])
        self.assertIn("matches", rec_bounded)
        self.assertEqual(rec_bounded.get("matches"), [])


class TestSurfaceInvariance(FixtureRepoBase):
    """The unchanged human and --json surfaces remain invariant across the change."""

    def test_check_human_output_invariant(self) -> None:
        """Human output for check release-gates reports findings and release-gate counts."""
        rc, out, err = self._run_cli("check", "release-gates", "--no-color")
        self.assertEqual(rc, 1)
        self.assertIn("FINDINGS  5 finding(s) detected across 6 release-gates", out)
        self.assertIn("check.live-bug-ungated", out)
        self.assertIn("errors  5   warnings  0   info  0", out)

    def test_check_json_output_invariant(self) -> None:
        """JSON output for check release-gates retains exit_code, status, diagnostics, and findings."""
        data = self._run_json("check", "release-gates")
        self.assertEqual(data.get("exit_code"), 1)
        self.assertEqual(data.get("status"), "findings")
        self.assertEqual(len(data.get("diagnostics", [])), self.FIXTURE_FINDINGS_COUNT)
        self.assertEqual(
            len(data.get("data", {}).get("policy_findings", [])),
            self.FIXTURE_FINDINGS_COUNT,
        )

    def test_search_human_output_invariant(self) -> None:
        """Human output for search reports matching files and lines."""
        rc, out, err = self._run_cli(
            "search", "backlog", self.SEARCH_QUERY, "--no-color"
        )
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        # 5 file headers + 5 matching line entries = 10 lines
        self.assertEqual(len(lines), 10)
        for i in range(self.FIXTURE_SEARCH_HITS_COUNT):
            self.assertTrue(any(f"bkl00{i}" in line for line in lines))

    def test_search_json_output_invariant(self) -> None:
        """JSON output for search retains hits, matches, files, and filters."""
        data = self._run_json("search", "backlog", self.SEARCH_QUERY)
        self.assertEqual(data.get("exit_code"), 0)
        self.assertEqual(data.get("status"), "clean")
        payload = data.get("data", {})
        self.assertEqual(payload.get("hits"), self.FIXTURE_SEARCH_HITS_COUNT)
        self.assertEqual(
            len(payload.get("matches", [])), self.FIXTURE_SEARCH_HITS_COUNT
        )
        self.assertEqual(len(payload.get("files", [])), self.FIXTURE_SEARCH_HITS_COUNT)
        self.assertEqual(payload.get("filters", {}).get("pattern"), self.SEARCH_QUERY)


class TestNonPositiveLimitRefusal(FixtureRepoBase):
    """E-05: Non-positive --limit is refused at exit 2 with a cannot-run record on both verbs."""

    def test_10_check_nonpositive_limit_refused(self) -> None:
        """aw check --limit 0 and --limit -1 exit 2 with cannot-run on check."""
        for lim in ("0", "-1"):
            rc, rec = self._run_agent_with_rc("check", "release-gates", "--limit", lim)
            self.assertEqual(
                rc, 2, f"Expected exit 2 for check --limit {lim}, got {rc}"
            )
            self.assertEqual(rec.get("exit"), 2)
            self.assertEqual(rec.get("outcome"), "cannot-run")
            self.assertEqual(agent_schema.validate_agent_record(rec), [])

    def test_11_search_nonpositive_limit_refused(self) -> None:
        """aw search --limit 0 and --limit -1 exit 2 with cannot-run on search."""
        for lim in ("0", "-1"):
            rc, rec = self._run_agent_with_rc(
                "search", "backlog", self.SEARCH_QUERY, "--limit", lim
            )
            self.assertEqual(
                rc, 2, f"Expected exit 2 for search --limit {lim}, got {rc}"
            )
            self.assertEqual(rec.get("exit"), 2)
            self.assertEqual(rec.get("outcome"), "cannot-run")
            self.assertEqual(agent_schema.validate_agent_record(rec), [])

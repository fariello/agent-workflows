"""Behavioral unit tests for tools/dead_status_token_scan.py.

This test exercises the dead-status-token scanner against synthesized fixture inputs
and an isolated throwaway directory constructed under tempfile / tmp_path.
Per E-02, P16, and project conventions:
- References NEITHER the real trim commit shas NOR the live tree.
- Carries NO livecorpus marker.
- Reads nothing under .aw/records/.
- Asserts both classifier directions (flags dead tokens, clears paired/exempt/out-of-domain).
- Asserts all eight required fixture shapes (a through h).
"""

from __future__ import annotations

import pathlib
import tempfile
import unittest

from tools.dead_status_token_scan import (
    get_domain,
    scan_paths,
    scan_source,
)


class DeadStatusTokenScanBehavioralTests(unittest.TestCase):
    """Behavioral tests driving scan_source on synthesized fixtures."""

    def test_fixture_a_bare_legacy_failed_safely_flags(self) -> None:
        """Case (a): A chain comparing only 'failed-safely' FLAGS."""
        source = """
def check_item(status: str) -> str:
    if status == "failed-safely":
        return "failed"
    return "ok"
"""
        records = scan_source(source, filename="fixture_a.py")
        flagged = [r for r in records if not r.is_exempt]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0].tokens, ["failed-safely"])
        self.assertEqual(
            flagged[0].missing,
            [{"token": "failed-safely", "canonical": "fail-gate"}],
        )

    def test_fixture_b_paired_fail_gate_does_not_flag(self) -> None:
        """Case (b): The same chain with 'fail-gate' added to ANY arm does NOT flag."""
        source = """
def check_item(status: str) -> str:
    if status in ("failed-safely", "fail-gate"):
        return "failed"
    return "ok"
"""
        records = scan_source(source, filename="fixture_b.py")
        flagged = [r for r in records if not r.is_exempt]
        self.assertEqual(len(flagged), 0)

    def test_fixture_c_function_canonicalizer_does_not_flag(self) -> None:
        """Case (c): The same chain inside a function that also calls canonical_terminal_status does NOT flag."""
        source = """
def check_item(status: str) -> str:
    st = canonical_terminal_status(status)
    if status == "failed-safely":
        return "failed"
    return "ok"
"""
        records = scan_source(source, filename="fixture_c.py")
        flagged = [r for r in records if not r.is_exempt]
        self.assertEqual(len(flagged), 0)
        exempt = [r for r in records if r.is_exempt]
        self.assertEqual(len(exempt), 1)
        self.assertIn("canonicalizer", str(exempt[0].exemption_reason))

    def test_fixture_d_ambiguous_tokens_blocked_and_partial_do_not_flag(
        self,
    ) -> None:
        """Case (d): A chain comparing 'blocked' or 'partial' does NOT flag at all."""
        source = """
def check_gate(status: str) -> str:
    if status == "blocked":
        return "wait"
    elif status == "partial":
        return "partial"
    return "proceed"
"""
        records = scan_source(source, filename="fixture_d.py")
        flagged = [r for r in records if not r.is_exempt]
        self.assertEqual(len(flagged), 0)
        self.assertEqual(len(records), 0)

    def test_fixture_e_canonical_twin_in_different_arm_does_not_flag(
        self,
    ) -> None:
        """Case (e): A chain whose canonical token appears in a DIFFERENT arm of the same chain does not flag."""
        source = """
def check_item(status: str) -> str:
    if status == "failed-safely":
        return "legacy_fail"
    elif status == "fail-gate":
        return "canonical_fail"
    return "ok"
"""
        records = scan_source(source, filename="fixture_e.py")
        flagged = [r for r in records if not r.is_exempt]
        self.assertEqual(len(flagged), 0)

    def test_fixture_f_bare_equality_comparison_flags(self) -> None:
        """Case (f): A bare == comparison against an in-domain token FLAGS."""
        source = """
def check_merge(status: str) -> str:
    if status == "merge-conflict":
        return "conflict"
    return "clean"
"""
        records = scan_source(source, filename="fixture_f.py")
        flagged = [r for r in records if not r.is_exempt]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0].tokens, ["merge-conflict"])
        self.assertEqual(
            flagged[0].missing,
            [{"token": "merge-conflict", "canonical": "fail-merge"}],
        )

    def test_fixture_g_well_formed_exemption_marker_does_not_flag(self) -> None:
        """Case (g): A chain carrying a well-formed exemption marker aw: dead-status-token-exempt <id6> <why> does NOT flag."""
        source = """
def evaluate_outcome(status: str) -> str:
    # aw: dead-status-token-exempt qvfd4l Raw token must be inspected before canonicalizing
    if status in ("substantially-complete", "partial"):
        return "partial"
    return "other"
"""
        records = scan_source(source, filename="fixture_g.py")
        flagged = [r for r in records if not r.is_exempt]
        self.assertEqual(len(flagged), 0)
        exempt = [r for r in records if r.is_exempt]
        self.assertEqual(len(exempt), 1)
        self.assertIn("marker (qvfd4l)", str(exempt[0].exemption_reason))

    def test_fixture_h_uncited_marker_still_flags(self) -> None:
        """Case (h): A chain carrying a marker with NO <id6> citation STILL FLAGS."""
        source = """
def evaluate_outcome(status: str) -> str:
    # aw: dead-status-token-exempt Raw token must be inspected without citation
    if status in ("substantially-complete", "partial"):
        return "partial"
    return "other"
"""
        records = scan_source(source, filename="fixture_h.py")
        flagged = [r for r in records if not r.is_exempt]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0].tokens, ["substantially-complete"])
        self.assertEqual(
            flagged[0].missing,
            [{"token": "substantially-complete", "canonical": "fail-gate"}],
        )


class DeadStatusTokenScanFilesystemTests(unittest.TestCase):
    """Behavioral filesystem tests using temporary files and directories."""

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.temp_dir = pathlib.Path(self._td.name)

    def test_scan_paths_on_temporary_directory(self) -> None:
        """Verify scan_paths correctly classifies clean and dead files on disk."""
        clean_file = self.temp_dir / "clean.py"
        clean_file.write_text(
            """
def clean_check(st: str) -> str:
    if st in ("fail-gate", "failed-safely"):
        return "fail"
    return "ok"
""",
            encoding="utf-8",
        )

        dead_file = self.temp_dir / "dead.py"
        dead_file.write_text(
            """
def dead_check(st: str) -> str:
    if st == "not-attempted":
        return "skipped"
    return "ran"
""",
            encoding="utf-8",
        )

        summary = scan_paths([self.temp_dir], repo_root=self.temp_dir)
        self.assertEqual(summary.total_flagged, 1)
        self.assertEqual(summary.flagged[0].function, "dead_check")
        self.assertEqual(
            summary.flagged[0].missing,
            [{"token": "not-attempted", "canonical": "not-run"}],
        )

    def test_domain_computation_and_dynamic_derivation(self) -> None:
        """Verify the domain computation excludes ambiguous tokens and grows dynamically."""
        domain = get_domain()
        self.assertEqual(len(domain), 8)
        self.assertNotIn("blocked", domain)
        self.assertNotIn("partial", domain)
        for expected in [
            "substantially-complete",
            "failed-safely",
            "dependency-blocked",
            "integration-blocked",
            "merge-conflict",
            "merge-needs-human",
            "merge-refused",
            "not-attempted",
        ]:
            self.assertIn(expected, domain)

        # Dynamic growth when alias table is extended
        mock_aliases = {"new-legacy": "new-canon", "blocked": "fail-gate"}
        mock_domain = get_domain(mock_aliases)
        self.assertEqual(mock_domain, frozenset({"new-legacy"}))

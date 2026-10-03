"""Tests for IPD x4vf9p: release sentinel succession and attribution.

Pins by outcome:
(a) resolve_release_outcome distinguishes resolved, absent, and ambiguous states.
(b) resolve_release preserves exact wrapper contract across all three states.
(c) check_release_gates on zero-planned tree emits exactly one sentinel finding and suppresses per-record.
(d) check_release_gates on two-planned tree emits exactly one ambiguous finding.
(e) non-next unresolvable values still report check.blocks-release-dangling in all three states.
(f) aw set shipped refuses on the last planned release and leaves file byte-identical.
(g) aw set shipped succeeds when a successor planned release exists.
(h) override flag permits write, records justification in history, and refuses empty/whitespace values.
(i) aw check release-gates --agent exits nonzero in both absent and ambiguous states.
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import check_engine, releases

_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
_ENV = {**os.environ, "PYTHONPATH": _REPO_ROOT}


def _create_fixture_repo(root: Path, planned_count: int = 1) -> Path:
    """Create a minimal fixture repository with a controlled number of planned releases."""
    for p in (
        root / ".aw" / "records" / "releases",
        root / ".aw" / "records" / "backlog" / "open",
        root / ".aw" / "records" / "plans" / "pending",
        root / ".aw" / "records" / "specs" / "approved",
    ):
        p.mkdir(parents=True, exist_ok=True)

    if planned_count >= 1:
        rel1 = (
            root
            / ".aw"
            / "records"
            / "releases"
            / "20260901-rel001-01-rel001-v1.release.md"
        )
        rel1.write_text(
            "# Release: 1.0.0\n\n"
            "- Id: rel001\n"
            "- Status: planned\n"
            "- Version: 1.0.0\n"
            "- Summary: First release\n\n"
            "## Workflow history\n\n"
            "- 2026-09-01 created (aw releases): First release\n",
            encoding="utf-8",
        )
    if planned_count >= 2:
        rel2 = (
            root
            / ".aw"
            / "records"
            / "releases"
            / "20260902-rel002-01-rel002-v2.release.md"
        )
        rel2.write_text(
            "# Release: 2.0.0\n\n"
            "- Id: rel002\n"
            "- Status: planned\n"
            "- Version: 2.0.0\n"
            "- Summary: Second release\n\n"
            "## Workflow history\n\n"
            "- 2026-09-02 created (aw releases): Second release\n",
            encoding="utf-8",
        )
    return root


class TestReleaseSentinelSuccession(unittest.TestCase):
    """Pin the sentinel succession and root-cause attribution outcomes."""

    def test_sentinel_outcomes_three_states(self) -> None:
        """Case (a): resolve_release_outcome distinguishes resolved, absent, and ambiguous states."""
        with TemporaryDirectory() as tmp:
            # 1 planned release -> resolved
            repo1 = _create_fixture_repo(Path(tmp) / "r1", planned_count=1)
            res1 = releases.resolve_release_outcome(repo1, "next")
            self.assertEqual(res1.outcome, releases.SENTINEL_RESOLVED)
            self.assertEqual(len(res1.paths), 1)

            # 0 planned releases -> absent
            repo0 = _create_fixture_repo(Path(tmp) / "r0", planned_count=0)
            res0 = releases.resolve_release_outcome(repo0, "next")
            self.assertEqual(res0.outcome, releases.SENTINEL_ABSENT)
            self.assertEqual(len(res0.paths), 0)

            # 2 planned releases -> ambiguous
            repo2 = _create_fixture_repo(Path(tmp) / "r2", planned_count=2)
            res2 = releases.resolve_release_outcome(repo2, "next")
            self.assertEqual(res2.outcome, releases.SENTINEL_AMBIGUOUS)
            self.assertEqual(len(res2.paths), 2)

    def test_resolve_release_wrapper_parity_three_states(self) -> None:
        """Case (b): resolve_release wrapper returns path, None, None across the three states."""
        with TemporaryDirectory() as tmp:
            repo1 = _create_fixture_repo(Path(tmp) / "r1", planned_count=1)
            p1 = releases.resolve_release(repo1, "next")
            self.assertIsNotNone(p1)
            self.assertEqual(p1.name, "20260901-rel001-01-rel001-v1.release.md")

            repo0 = _create_fixture_repo(Path(tmp) / "r0", planned_count=0)
            p0 = releases.resolve_release(repo0, "next")
            self.assertIsNone(p0)

            repo2 = _create_fixture_repo(Path(tmp) / "r2", planned_count=2)
            p2 = releases.resolve_release(repo2, "next")
            self.assertIsNone(p2)

    def test_check_release_gates_zero_planned_single_finding(self) -> None:
        """Case (c): check_release_gates on zero-planned tree emits exactly one sentinel finding and suppresses per-record."""
        with TemporaryDirectory() as tmp:
            repo = _create_fixture_repo(Path(tmp), planned_count=0)
            # Add three gated records across backlog, specs, and plans
            (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-item01-01-item01-b1.backlog.md"
            ).write_text(
                "- Id: item01\n- Status: open\n- Blocks-Release: next\n- Set: item01\n- Priority: medium\n- Work-Kind: feature\n",
                encoding="utf-8",
            )
            (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "approved"
                / "20260920-spec01-01-spec01-s1.spec.md"
            ).write_text(
                "- Id: spec01\n- Status: approved\n- Blocks-Release: next\n- Set: spec01\n",
                encoding="utf-8",
            )
            (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260920-plan01-01-plan01-p1.ipd.md"
            ).write_text(
                "# IPD: Plan 1\n\n- Id: plan01\n- Status: approved\n- Blocks-Release: next\n- Set: plan01\n- Scope: S\n",
                encoding="utf-8",
            )

            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertEqual(len(findings), 1)
            self.assertEqual(rules, ["check.release-sentinel-absent"])
            self.assertIn("releases", findings[0].location)

    def test_check_release_gates_two_planned_ambiguous_finding(self) -> None:
        """Case (d): check_release_gates on two-planned tree emits exactly one ambiguous finding."""
        with TemporaryDirectory() as tmp:
            repo = _create_fixture_repo(Path(tmp), planned_count=2)
            # Add multiple next-valued records
            (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-item01-01-item01-b1.backlog.md"
            ).write_text(
                "- Id: item01\n- Status: open\n- Blocks-Release: next\n- Set: item01\n- Priority: medium\n- Work-Kind: feature\n",
                encoding="utf-8",
            )
            (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260920-plan01-01-plan01-p1.ipd.md"
            ).write_text(
                "# IPD: Plan 1\n\n- Id: plan01\n- Status: approved\n- Blocks-Release: next\n- Set: plan01\n- Scope: S\n",
                encoding="utf-8",
            )

            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertEqual(len(findings), 1)
            self.assertEqual(rules, ["check.release-sentinel-ambiguous"])
            self.assertIn("20260901-rel001-01-rel001-v1.release.md", findings[0].detail)
            self.assertIn("20260902-rel002-01-rel002-v2.release.md", findings[0].detail)

    def test_non_next_unresolvable_reports_dangling_all_three_states(self) -> None:
        """Case (e): non-next unresolvable value still reports check.blocks-release-dangling in all three states."""
        with TemporaryDirectory() as tmp:
            for count in (0, 1, 2):
                repo = _create_fixture_repo(
                    Path(tmp) / f"r{count}", planned_count=count
                )
                # Next-gated record
                (
                    repo
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / "20260920-item01-01-item01-b1.backlog.md"
                ).write_text(
                    "- Id: item01\n- Status: open\n- Blocks-Release: next\n- Set: item01\n- Priority: medium\n- Work-Kind: feature\n",
                    encoding="utf-8",
                )
                # Planted unresolvable non-next record
                (
                    repo
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / "20260920-item02-01-item02-b2.backlog.md"
                ).write_text(
                    "- Id: item02\n- Status: open\n- Blocks-Release: nonexist\n- Set: item02\n- Priority: medium\n- Work-Kind: feature\n",
                    encoding="utf-8",
                )

                findings = check_engine.check_release_gates(repo)
                rules = [d.rule for d in findings]
                self.assertIn("check.blocks-release-dangling", rules)
                # For count 0: 1 sentinel absent + 1 dangling = 2 findings
                # For count 1: 0 sentinel + 1 dangling = 1 finding
                # For count 2: 1 sentinel ambiguous + 1 dangling = 2 findings
                expected_count = 2 if count in (0, 2) else 1
                self.assertEqual(len(findings), expected_count)

    def test_set_shipped_refuses_last_planned_preserves_bytes(self) -> None:
        """Case (f): aw set shipped refuses on the last planned release and leaves file byte-identical."""
        with TemporaryDirectory() as tmp:
            repo = _create_fixture_repo(Path(tmp), planned_count=1)
            # Add records that would dangle
            (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-item01-01-item01-b1.backlog.md"
            ).write_text(
                "- Id: item01\n- Status: open\n- Blocks-Release: next\n- Set: item01\n- Priority: medium\n- Work-Kind: feature\n",
                encoding="utf-8",
            )
            rel_file = (
                repo
                / ".aw"
                / "records"
                / "releases"
                / "20260901-rel001-01-rel001-v1.release.md"
            )
            orig_bytes = rel_file.read_bytes()

            res = subprocess.run(
                [sys.executable, "-m", "agent_workflows", "set", "shipped", "rel001"],
                cwd=str(repo),
                env=_ENV,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(res.returncode, 0)
            combined_output = res.stdout + res.stderr
            self.assertIn("aw releases new", combined_output)
            self.assertIn("1 record", combined_output)
            self.assertEqual(rel_file.read_bytes(), orig_bytes)
            self.assertIn("- Status: planned", rel_file.read_text(encoding="utf-8"))

    def test_set_shipped_succeeds_when_successor_exists(self) -> None:
        """Case (g): aw set shipped succeeds when a successor planned release exists."""
        with TemporaryDirectory() as tmp:
            repo = _create_fixture_repo(Path(tmp), planned_count=2)
            rel1 = (
                repo
                / ".aw"
                / "records"
                / "releases"
                / "20260901-rel001-01-rel001-v1.release.md"
            )
            rel2 = (
                repo
                / ".aw"
                / "records"
                / "releases"
                / "20260902-rel002-01-rel002-v2.release.md"
            )

            res = subprocess.run(
                [sys.executable, "-m", "agent_workflows", "set", "shipped", "rel001"],
                cwd=str(repo),
                env=_ENV,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("- Status: shipped", rel1.read_text(encoding="utf-8"))
            self.assertIn("- Status: planned", rel2.read_text(encoding="utf-8"))

    def test_override_flag_permits_write_records_history_refuses_empty(self) -> None:
        """Case (h): override flag permits write, records justification in history, and refuses empty/whitespace."""
        with TemporaryDirectory() as tmp:
            repo = _create_fixture_repo(Path(tmp), planned_count=1)
            (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-item01-01-item01-b1.backlog.md"
            ).write_text(
                "- Id: item01\n- Status: open\n- Blocks-Release: next\n- Set: item01\n- Priority: medium\n- Work-Kind: feature\n",
                encoding="utf-8",
            )
            rel_file = (
                repo
                / ".aw"
                / "records"
                / "releases"
                / "20260901-rel001-01-rel001-v1.release.md"
            )
            orig_bytes = rel_file.read_bytes()

            # Empty override fails
            res_empty = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "set",
                    "shipped",
                    "rel001",
                    "--allow-unresolvable-release-sentinel",
                    "",
                ],
                cwd=str(repo),
                env=_ENV,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(res_empty.returncode, 0)
            self.assertEqual(rel_file.read_bytes(), orig_bytes)

            # Whitespace override fails
            res_space = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "set",
                    "shipped",
                    "rel001",
                    "--allow-unresolvable-release-sentinel",
                    "   ",
                ],
                cwd=str(repo),
                env=_ENV,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(res_space.returncode, 0)
            self.assertEqual(rel_file.read_bytes(), orig_bytes)

            # Valid justification succeeds and records justification in history
            justification = "shipping 1.0.0; successor record lands in the same change"
            res_valid = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "set",
                    "shipped",
                    "rel001",
                    "--allow-unresolvable-release-sentinel",
                    justification,
                ],
                cwd=str(repo),
                env=_ENV,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_valid.returncode, 0)
            txt = rel_file.read_text(encoding="utf-8")
            self.assertIn("- Status: shipped", txt)
            self.assertIn(justification, txt)

    def test_check_release_gates_agent_cli_exits_nonzero_in_bad_states(self) -> None:
        """Case (i): aw check release-gates --agent exits nonzero in both absent and ambiguous states."""
        with TemporaryDirectory() as tmp:
            # Absent state
            repo0 = _create_fixture_repo(Path(tmp) / "r0", planned_count=0)
            (
                repo0
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-item01-01-item01-b1.backlog.md"
            ).write_text(
                "- Id: item01\n- Status: open\n- Blocks-Release: next\n- Set: item01\n- Priority: medium\n- Work-Kind: feature\n",
                encoding="utf-8",
            )
            res0 = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "check",
                    "release-gates",
                    "--agent",
                ],
                cwd=str(repo0),
                env=_ENV,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(res0.returncode, 0)
            self.assertIn("check.release-sentinel-absent", res0.stdout)

            # Ambiguous state
            repo2 = _create_fixture_repo(Path(tmp) / "r2", planned_count=2)
            (
                repo2
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-item01-01-item01-b1.backlog.md"
            ).write_text(
                "- Id: item01\n- Status: open\n- Blocks-Release: next\n- Set: item01\n- Priority: medium\n- Work-Kind: feature\n",
                encoding="utf-8",
            )
            res2 = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "check",
                    "release-gates",
                    "--agent",
                ],
                cwd=str(repo2),
                env=_ENV,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(res2.returncode, 0)
            self.assertIn("check.release-sentinel-ambiguous", res2.stdout)


if __name__ == "__main__":
    unittest.main()

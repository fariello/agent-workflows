"""Tests for gateci 2vw35i: release-gate rule family reachability and CLI check target.

Verifies:
1. Every member of the release-gate rule family is reachable from `check_release_gates` and
   the `aw check release-gates` CLI surface:
   - `check.live-bug-ungated`
   - `check.from-backlog-gate-mismatch`
   - `check.blocking-item-closed-without-gate`
   - `check.blocks-release-dangling`
   - `check.from-backlog-dangling`
2. Polarity: fires on synthetic violations, clean on synthetic valid fixtures.
3. Handoff exemption: a live bug whose From-Backlog carrier holds the gate is NOT flagged.
4. Parity: rule set reachable from `check_release_gates` equals the full sweep's gate family rules.
5. Pre-commit aggregator composition: `check_commit_invariants` still composes only its 3 commit-scoped rules.
6. CLI target and alias routing (`release-gates`, `release-gate`).
"""

from __future__ import annotations

import argparse
import inspect
import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import artifact_core as _core
from agent_workflows import check_engine
from agent_workflows import cli
from agent_workflows.term import Term


def _create_minimal_repo(root: Path) -> Path:
    """Create a minimal conformant repository structure."""
    for p in (
        root / ".aw" / "records" / "releases",
        root / ".aw" / "records" / "backlog" / "open",
        root / ".aw" / "records" / "backlog" / "done",
        root / ".aw" / "records" / "plans" / "pending",
        root / ".aw" / "records" / "plans" / "executed",
        root / ".aw" / "records" / "specs" / "approved",
    ):
        p.mkdir(parents=True, exist_ok=True)
    # create a planned release
    rel_file = (
        root
        / ".aw"
        / "records"
        / "releases"
        / "20260901-rel001-01-rel001-v1.release.md"
    )
    rel_file.write_text(
        "# Release: 1.0.0\n\n"
        "- Id: rel001\n"
        "- Status: planned\n"
        "- Version: 1.0.0\n"
        "- Summary: Test release\n",
        encoding="utf-8",
    )
    return root


class TestCheckEngineReleaseGate(unittest.TestCase):
    """Synthetic tests for release-gate family reachability and behavior."""

    def test_clean_fixture_produces_zero_findings(self) -> None:
        """A clean fixture produces zero findings from check_release_gates."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            findings = check_engine.check_release_gates(repo)
            self.assertEqual(findings, [])
            self.assertEqual(_core.drift_exit_code(findings), 0)

    def test_rule_live_bug_ungated_reachable(self) -> None:
        """check.live-bug-ungated is reported by check_release_gates on a live ungated bug."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug001-01-bug001-test-defect.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug001\n"
                "- Status: open\n"
                "- Set: bug001\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Live ungated bug\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertIn("check.live-bug-ungated", rules)
            self.assertEqual(_core.drift_exit_code(findings), 1)

    def test_live_bug_with_gate_is_clean(self) -> None:
        """A live bug carrying a valid Blocks-Release is clean."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug001-01-bug001-test-defect.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug001\n"
                "- Status: open\n"
                "- Blocks-Release: next\n"
                "- Set: bug001\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Live gated bug\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            self.assertEqual(findings, [])

    def test_live_ungated_security_item_clean_with_no_config(self) -> None:
        """A live ungated security item is clean when no config overrides the default."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            sec_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-sec001-01-sec001-sec-defect.backlog.md"
            )
            sec_file.write_text(
                "- Id: sec001\n"
                "- Status: open\n"
                "- Set: sec001\n"
                "- Priority: medium\n"
                "- Work-Kind: security\n"
                "- Summary: Live ungated security item\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            self.assertEqual(findings, [])

    def test_live_ungated_security_item_flagged_when_configured(self) -> None:
        """A live ungated security item is flagged when release_gate_work_kinds includes security."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            conf_dir = repo / ".aw" / "config"
            conf_dir.mkdir(parents=True, exist_ok=True)
            (conf_dir / "project.json").write_text(
                json.dumps({"release_gate_work_kinds": {"kinds": ["bug", "security"]}}),
                encoding="utf-8",
            )
            sec_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-sec001-01-sec001-sec-defect.backlog.md"
            )
            sec_file.write_text(
                "- Id: sec001\n"
                "- Status: open\n"
                "- Set: sec001\n"
                "- Priority: medium\n"
                "- Work-Kind: security\n"
                "- Summary: Live ungated security item\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertIn("check.live-bug-ungated", rules)

    def test_live_ungated_bug_clean_when_configured_empty(self) -> None:
        """A live ungated bug is clean when release_gate_work_kinds is configured as []."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            conf_dir = repo / ".aw" / "config"
            conf_dir.mkdir(parents=True, exist_ok=True)
            (conf_dir / "project.json").write_text(
                json.dumps({"release_gate_work_kinds": []}),
                encoding="utf-8",
            )
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug001-01-bug001-test-defect.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug001\n"
                "- Status: open\n"
                "- Set: bug001\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Live ungated bug\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            self.assertEqual(findings, [])

    def test_handoff_exemption(self) -> None:
        """A live bug with no gate whose From-Backlog plan carries the gate is NOT flagged."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug001-01-bug001-test-defect.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug001\n"
                "- Status: open\n"
                "- Set: bug001\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Live handed-off bug\n",
                encoding="utf-8",
            )
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260920-plan01-01-plan01-fix-bug.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Fix bug\n\n"
                "- Id: plan01\n"
                "- Status: approved\n"
                "- From-Backlog: bug001\n"
                "- Blocks-Release: next\n"
                "- Set: plan01\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            self.assertEqual(findings, [])

    def test_rule_from_backlog_gate_mismatch_reachable(self) -> None:
        """check.from-backlog-gate-mismatch is reported when carrier gate disagrees with item gate."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            # create another release record
            (
                repo
                / ".aw"
                / "records"
                / "releases"
                / "20260902-rel002-01-rel002-v2.release.md"
            ).write_text(
                "- Id: rel002\n- Status: planned\n- Version: 2.0.0\n- Summary: R2\n",
                encoding="utf-8",
            )
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug001-01-bug001-test-defect.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug001\n"
                "- Status: open\n"
                "- Blocks-Release: rel001\n"
                "- Set: bug001\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Gated bug\n",
                encoding="utf-8",
            )
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260920-plan01-01-plan01-fix-bug.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Fix bug\n\n"
                "- Id: plan01\n"
                "- Status: approved\n"
                "- From-Backlog: bug001\n"
                "- Blocks-Release: rel002\n"
                "- Set: plan01\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertIn("check.from-backlog-gate-mismatch", rules)

    def test_rule_blocks_release_dangling_reachable(self) -> None:
        """check.blocks-release-dangling is reported when Blocks-Release resolves to nothing."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug001-01-bug001-test-defect.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug001\n"
                "- Status: open\n"
                "- Blocks-Release: nonexist\n"
                "- Set: bug001\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Dangling release gate\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertIn("check.blocks-release-dangling", rules)

    def test_rule_from_backlog_dangling_reachable(self) -> None:
        """check.from-backlog-dangling is reported when From-Backlog resolves to nonexistent item."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260920-plan01-01-plan01-fix-bug.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Fix bug\n\n"
                "- Id: plan01\n"
                "- Status: approved\n"
                "- From-Backlog: noitem\n"
                "- Blocks-Release: next\n"
                "- Set: plan01\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertIn("check.from-backlog-dangling", rules)

    def test_rule_blocking_item_closed_without_gate_reachable(self) -> None:
        """check.blocking-item-closed-without-gate is reported on a staged done item with gate and no handoff."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.name", "Test"], check=True
            )
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "test@test.com"],
                check=True,
            )
            done_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260920-item01-01-item01-done-bug.backlog.md"
            )
            done_file.write_text(
                "- Id: item01\n"
                "- Status: done\n"
                "- Blocks-Release: next\n"
                "- Set: item01\n"
                "- Priority: medium\n"
                "- Work-Kind: feature\n"
                "- Summary: Closed without gate handoff\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(repo), "add", "--", ".aw"], check=True)
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertIn("check.blocking-item-closed-without-gate", rules)

    def test_whole_family_rules_constant(self) -> None:
        """RELEASE_GATE_RULES lists all 5 release-gate family rules."""
        expected = {
            "check.live-bug-ungated",
            "check.blocking-item-closed-without-gate",
            "check.from-backlog-gate-mismatch",
            "check.blocks-release-dangling",
            "check.from-backlog-dangling",
        }
        self.assertEqual(set(check_engine.RELEASE_GATE_RULES), expected)

    def test_check_commit_invariants_composition_intact(self) -> None:
        """check_commit_invariants still composes exactly its 3 commit-scoped functions."""
        source = inspect.getsource(check_engine.check_commit_invariants)
        self.assertIn("check_status_untooled", source)
        self.assertIn("check_release_gate_consistency", source)
        self.assertIn("check_scope_drift", source)
        self.assertNotIn("check_live_bug_gate", source)
        self.assertNotIn("check_release_gates", source)

    def test_full_sweep_includes_check_release_gates(self) -> None:
        """The full sweep (check_types(['all'])) includes all findings from check_release_gates."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug001-01-bug001-test-defect.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug001\n"
                "- Status: open\n"
                "- Set: bug001\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Live ungated bug\n",
                encoding="utf-8",
            )
            gate_findings = check_engine.check_release_gates(repo)
            sweep_findings = check_engine.check_types(repo, ["all"])
            gate_rules = {
                d.rule
                for d in gate_findings
                if d.rule in check_engine.RELEASE_GATE_RULES
            }
            sweep_gate_rules = {
                d.rule
                for d in sweep_findings
                if d.rule in check_engine.RELEASE_GATE_RULES
            }
            self.assertEqual(gate_rules, sweep_gate_rules)
            self.assertIn("check.live-bug-ungated", sweep_gate_rules)

    def test_cli_check_release_gates_runner(self) -> None:
        """CLI invocation `aw check release-gates` executes properly and reports findings."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            # Add an ungated bug
            (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug001-01-bug001-test-defect.backlog.md"
            ).write_text(
                "- Id: bug001\n"
                "- Status: open\n"
                "- Set: bug001\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Live ungated bug\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                command="check",
                type="release-gates",
                dir=str(repo),
                all=False,
                agent=True,
                json=False,
                selector=[],
                strict_setid_length=False,
            )
            term = Term(color=False)
            rc = cli._run_check(args, term)
            self.assertEqual(rc, 1)

            # Test singular alias
            args_singular = argparse.Namespace(
                command="check",
                type="release-gate",
                dir=str(repo),
                all=False,
                agent=True,
                json=False,
                selector=[],
                strict_setid_length=False,
            )
            rc_singular = cli._run_check(args_singular, term)
            self.assertEqual(rc_singular, 1)

    def test_cli_check_release_gates_clean(self) -> None:
        """CLI invocation `aw check release-gates` returns 0 on clean repository."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            args = argparse.Namespace(
                command="check",
                type="release-gates",
                dir=str(repo),
                all=False,
                agent=True,
                json=False,
                selector=[],
                strict_setid_length=False,
            )
            term = Term(color=False)
            rc = cli._run_check(args, term)
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()

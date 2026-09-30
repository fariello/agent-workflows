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
import json
from unittest import mock
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import artifact_core as _core
from agent_workflows import check_engine
from agent_workflows import cli
from agent_workflows import ipd_schema
from agent_workflows import releases
from agent_workflows import runner_shared
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

    def test_rule_blocking_item_closed_pending_plan_yields_finding(self) -> None:
        """closescope 2a6phj E-06: a staged done gated item whose only carrier is a PENDING plan yields check.blocking-item-closed-without-gate."""
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
                "- From-Backlog: item01\n"
                "- Blocks-Release: next\n"
                "- Set: plan01\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
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
                "- Summary: Closed with pending carrier\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(repo), "add", "--", ".aw"], check=True)
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertIn("check.blocking-item-closed-without-gate", rules)

    def test_rule_blocking_item_closed_executed_plan_clean(self) -> None:
        """closescope 2a6phj E-06: a staged done gated item whose carrier is an EXECUTED plan yields NO finding."""
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
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20260920-plan01-01-plan01-fix-bug.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Fix bug\n\n"
                "- Id: plan01\n"
                "- Status: executed\n"
                "- From-Backlog: item01\n"
                "- Blocks-Release: next\n"
                "- Set: plan01\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
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
                "- Summary: Closed with executed carrier\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(repo), "add", "--", ".aw"], check=True)
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertNotIn("check.blocking-item-closed-without-gate", rules)

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

    def test_check_commit_invariants_composition(self) -> None:
        """check_commit_invariants composes status-untooled, release-gate consistency, and scope-drift."""
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
            # 1. Staged hand-edited plan status change -> triggers check.status-untooled
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260920-p01-01-p01-test.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Test\n\n- Id: p01\n- Status: approved\n- Set: p01\n",
                encoding="utf-8",
            )
            # 2. Staged done gated item with pending carrier -> triggers check.blocking-item-closed-without-gate
            done_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260920-item01-01-item01-done.backlog.md"
            )
            done_file.write_text(
                "- Id: item01\n- Status: done\n- Blocks-Release: next\n- Set: item01\n- Priority: medium\n- Work-Kind: feature\n- Summary: Done\n",
                encoding="utf-8",
            )
            # 3. An open bug with blocks-release that triggers check.live-bug-ungated in full check_release_gates,
            # but must NOT appear in check_commit_invariants aggregate
            open_bug = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug01-01-bug01-bug.backlog.md"
            )
            open_bug.write_text(
                "- Id: bug01\n- Status: open\n- Blocks-Release: next\n- Set: bug01\n- Priority: high\n- Work-Kind: bug\n- Summary: Bug\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(repo), "add", "--", ".aw"], check=True)

            sentinel_drift = _core.Drift(
                "lane/foo.py", "check.scope-drift", "scope drift detail"
            )
            with mock.patch(
                "agent_workflows.check_engine.check_scope_drift",
                return_value=[sentinel_drift],
            ):
                findings = check_engine.check_commit_invariants(repo)

            rules = {d.rule for d in findings}
            self.assertIn("check.status-untooled", rules)
            self.assertIn("check.blocking-item-closed-without-gate", rules)
            self.assertIn("check.scope-drift", rules)
            self.assertNotIn("check.live-bug-ungated", rules)

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

    def test_gate_mismatch_not_reported_when_next_and_id6_resolve_to_same_release(
        self,
    ) -> None:
        """(a) Item 'next' and From-Backlog plan with resolved release id6 produce no gate mismatch."""
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
                "- Blocks-Release: rel001\n"
                "- Set: plan01\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertNotIn("check.from-backlog-gate-mismatch", rules)

    def test_evaluate_blocking_close_legitimate_when_next_and_id6_resolve_to_same_release(
        self,
    ) -> None:
        """(b) evaluate_blocking_close is legitimate with path HANDOFF when gates resolve identically."""
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
                "- Summary: Gated bug\n",
                encoding="utf-8",
            )
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20260920-plan01-01-plan01-fix-bug.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Fix bug\n\n"
                "- Id: plan01\n"
                "- Status: executed\n"
                "- From-Backlog: bug001\n"
                "- Blocks-Release: rel001\n"
                "- Set: plan01\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
            )
            verdict = check_engine.evaluate_blocking_close(repo, bug_file, "done")
            self.assertTrue(verdict.legitimate)
            self.assertEqual(verdict.path, "HANDOFF")
            self.assertEqual(verdict.severity, "ok")

    def test_gate_mismatch_reported_for_genuinely_different_release(
        self,
    ) -> None:
        """(c) Gate mismatch is reported when carrier names a genuinely different release."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            # Create a second planned release
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

            verdict = check_engine.evaluate_blocking_close(repo, bug_file, "done")
            self.assertFalse(verdict.legitimate)
            self.assertEqual(verdict.severity, "error")
            self.assertIsNone(verdict.path)

    def test_gate_mismatch_unresolvable_next_falls_back_to_string_mismatch(
        self,
    ) -> None:
        """(d) When 'next' cannot be resolved (multiple planned releases), fallback treats it as mismatch."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            # Create a second planned release so 'next' fails to resolve (ambiguous)
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
                "- Blocks-Release: next\n"
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
                "- Blocks-Release: rel001\n"
                "- Set: plan01\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertIn("check.from-backlog-gate-mismatch", rules)
            self.assertIn("check.blocks-release-dangling", rules)

            verdict = check_engine.evaluate_blocking_close(repo, bug_file, "done")
            self.assertFalse(verdict.legitimate)
            self.assertEqual(verdict.severity, "error")
            self.assertIsNone(verdict.path)

    def test_release_gate_warnings_orphaned_live_blocker_remedy(self) -> None:
        """closescope 2a6phj E-05: orphaned-live-blocker warning names graduated for pending plan and --status done for executed plan."""
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
                "- Summary: Gated bug\n",
                encoding="utf-8",
            )
            pending_plan = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260920-plan01-01-plan01-fix-bug.ipd.md"
            )
            pending_plan.write_text(
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
            # 1. With pending plan: warning remedies using graduated
            warns = check_engine.release_gate_warnings(repo)
            self.assertEqual(len(warns), 1)
            self.assertEqual(warns[0].rule, "check.orphaned-live-blocker")
            self.assertIn("--status graduated", warns[0].detail)
            self.assertNotIn("set done", warns[0].detail)

            # Move plan to executed
            pending_plan.unlink()
            exec_plan = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20260920-plan01-01-plan01-fix-bug.ipd.md"
            )
            exec_plan.write_text(
                "# IPD: Fix bug\n\n"
                "- Id: plan01\n"
                "- Status: executed\n"
                "- From-Backlog: bug001\n"
                "- Blocks-Release: next\n"
                "- Set: plan01\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
            )
            # 2. With executed plan: warning remedies using --status done
            warns2 = check_engine.release_gate_warnings(repo)
            self.assertEqual(len(warns2), 1)
            self.assertEqual(warns2[0].rule, "check.orphaned-live-blocker")
            self.assertIn("aw backlog set bug001 --status done", warns2[0].detail)
            self.assertNotIn("set done bug001", warns2[0].detail)

    def test_from_backlog_sentinels_treated_as_absent(self) -> None:
        """E-05: -, none, unresolved on From-Backlog are treated as absent across all readers."""
        for sentinel in ("-", "none", "unresolved"):
            with self.subTest(sentinel=sentinel):
                with TemporaryDirectory() as tmp:
                    repo = _create_minimal_repo(Path(tmp))
                    plan_text = (
                        f"# IPD: Test\n\n"
                        f"- Id: pln001\n"
                        f"- Status: approved\n"
                        f"- From-Backlog: {sentinel}\n"
                        f"- Set: pln001\n"
                        f"- Scope: Fix\n"
                        f"- Scope-Paths: foo.py\n"
                    )
                    plan_file = (
                        repo
                        / ".aw"
                        / "records"
                        / "plans"
                        / "pending"
                        / "20260901-pln001-01-pln001-test.ipd.md"
                    )
                    plan_file.write_text(plan_text, encoding="utf-8")

                    # 1. 0 check.from-backlog-dangling from check_release_gates(repo)
                    findings = check_engine.check_release_gates(repo)
                    dangling = [
                        d for d in findings if d.rule == "check.from-backlog-dangling"
                    ]
                    self.assertEqual(dangling, [])

                    # 2. find_from_backlog_artifacts returns empty
                    artifacts = check_engine.find_from_backlog_artifacts(repo, sentinel)
                    self.assertEqual(artifacts, [])

                    # 3. _from_backlog_carrier_index has no key for the sentinel
                    c_idx = check_engine._from_backlog_carrier_index(repo)
                    self.assertNotIn(sentinel, c_idx)

                    # 4. build_graduation_reverse_index has no ('backlog', sentinel) key
                    r_idx = check_engine.build_graduation_reverse_index(repo)
                    self.assertNotIn(("backlog", sentinel), r_idx)

                    # 5. runner_shared._read_from_backlog returns None
                    self.assertIsNone(runner_shared._read_from_backlog(plan_text))

    def test_from_spec_sentinels_treated_as_absent(self) -> None:
        """E-05: -, none, unresolved on From-Spec yield 0 check.from-spec-dangling."""
        for sentinel in ("-", "none", "unresolved"):
            with self.subTest(sentinel=sentinel):
                with TemporaryDirectory() as tmp:
                    repo = _create_minimal_repo(Path(tmp))
                    # Spec with - Id: so known-id set is non-empty
                    spec_file = (
                        repo
                        / ".aw"
                        / "records"
                        / "specs"
                        / "approved"
                        / "20260901-spc001-01-spc001-v1.spec.md"
                    )
                    spec_file.write_text(
                        "# Spec\n\n- Id: spc001\n- Status: approved\n",
                        encoding="utf-8",
                    )
                    plan_file = (
                        repo
                        / ".aw"
                        / "records"
                        / "plans"
                        / "pending"
                        / "20260901-pln001-01-pln001-test.ipd.md"
                    )
                    plan_file.write_text(
                        f"# IPD: Test\n\n"
                        f"- Id: pln001\n"
                        f"- Status: approved\n"
                        f"- From-Spec: {sentinel}\n"
                        f"- Set: pln001\n"
                        f"- Scope: Fix\n"
                        f"- Scope-Paths: foo.py\n",
                        encoding="utf-8",
                    )
                    findings = check_engine.check_from_spec_dangling(repo)
                    dangling = [
                        d for d in findings if d.rule == "check.from-spec-dangling"
                    ]
                    self.assertEqual(dangling, [])

    def test_unknown_id6_still_flags_dangling(self) -> None:
        """E-05 negative cases: a real-shaped but unknown id6 (zz9zz9) yields exactly 1 dangling finding for both From-Backlog and From-Spec."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            # Negative case 1: From-Backlog: zz9zz9
            plan_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260901-pln001-01-pln001-test.ipd.md"
            )
            plan_file.write_text(
                "# IPD: Test\n\n"
                "- Id: pln001\n"
                "- Status: approved\n"
                "- From-Backlog: zz9zz9\n"
                "- Set: pln001\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            dangling = [d for d in findings if d.rule == "check.from-backlog-dangling"]
            self.assertEqual(len(dangling), 1)

            # Negative case 2: From-Spec: zz9zz9
            spec_file = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "approved"
                / "20260901-spc001-01-spc001-v1.spec.md"
            )
            spec_file.write_text(
                "# Spec\n\n- Id: spc001\n- Status: approved\n",
                encoding="utf-8",
            )
            plan_file2 = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260901-pln002-01-pln002-test.ipd.md"
            )
            plan_file2.write_text(
                "# IPD: Test\n\n"
                "- Id: pln002\n"
                "- Status: approved\n"
                "- From-Spec: zz9zz9\n"
                "- Set: pln002\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
            )
            spec_findings = check_engine.check_from_spec_dangling(repo)
            spec_dangling = [
                d for d in spec_findings if d.rule == "check.from-spec-dangling"
            ]
            self.assertEqual(len(spec_dangling), 1)

    def test_regression_guard_all_readers_honor_schema_sentinels(self) -> None:
        """E-06: Behavioral regression guard ensuring all six public readers treat every member

        of ipd_schema.SOURCE_LINK_ABSENT_SENTINELS as absent.
        """
        for sentinel in ipd_schema.SOURCE_LINK_ABSENT_SENTINELS:
            with TemporaryDirectory() as tmp:
                repo = _create_minimal_repo(Path(tmp))
                # Valid spec so check_from_spec_dangling doesn't short-circuit
                spec_file = (
                    repo
                    / ".aw"
                    / "records"
                    / "specs"
                    / "approved"
                    / "20260901-spc001-01-spc001-v1.spec.md"
                )
                spec_file.write_text(
                    "# Spec\n\n- Id: spc001\n- Status: approved\n",
                    encoding="utf-8",
                )
                plan_bkl_text = (
                    f"# IPD: Test\n\n"
                    f"- Id: plnbkl\n"
                    f"- Status: approved\n"
                    f"- From-Backlog: {sentinel}\n"
                    f"- Set: plnbkl\n"
                    f"- Scope: Fix\n"
                    f"- Scope-Paths: foo.py\n"
                )
                plan_bkl_file = (
                    repo
                    / ".aw"
                    / "records"
                    / "plans"
                    / "pending"
                    / "20260901-plnbkl-01-plnbkl-test.ipd.md"
                )
                plan_bkl_file.write_text(plan_bkl_text, encoding="utf-8")

                plan_spc_file = (
                    repo
                    / ".aw"
                    / "records"
                    / "plans"
                    / "pending"
                    / "20260901-plnspc-01-plnspc-test.ipd.md"
                )
                plan_spc_file.write_text(
                    f"# IPD: Test\n\n"
                    f"- Id: plnspc\n"
                    f"- Status: approved\n"
                    f"- From-Spec: {sentinel}\n"
                    f"- Set: plnspc\n"
                    f"- Scope: Fix\n"
                    f"- Scope-Paths: foo.py\n",
                    encoding="utf-8",
                )

                # 1. runner_shared._read_from_backlog
                with self.subTest(
                    reader="runner_shared._read_from_backlog", sentinel=sentinel
                ):
                    res = runner_shared._read_from_backlog(plan_bkl_text)
                    self.assertIsNone(
                        res,
                        f"runner_shared._read_from_backlog did not treat sentinel {sentinel!r} as absent, got {res!r}",
                    )

                # 2. check_engine.find_from_backlog_artifacts
                with self.subTest(
                    reader="check_engine.find_from_backlog_artifacts", sentinel=sentinel
                ):
                    arts = check_engine.find_from_backlog_artifacts(repo, sentinel)
                    self.assertEqual(
                        arts,
                        [],
                        f"check_engine.find_from_backlog_artifacts did not treat sentinel {sentinel!r} as absent",
                    )

                # 3. check_engine._from_backlog_carrier_index
                with self.subTest(
                    reader="check_engine._from_backlog_carrier_index", sentinel=sentinel
                ):
                    c_idx = check_engine._from_backlog_carrier_index(repo)
                    self.assertNotIn(
                        sentinel,
                        c_idx,
                        f"check_engine._from_backlog_carrier_index indexed sentinel {sentinel!r}",
                    )

                # 4. check_engine.build_graduation_reverse_index
                with self.subTest(
                    reader="check_engine.build_graduation_reverse_index",
                    sentinel=sentinel,
                ):
                    r_idx = check_engine.build_graduation_reverse_index(repo)
                    self.assertNotIn(
                        ("backlog", sentinel),
                        r_idx,
                        f"check_engine.build_graduation_reverse_index indexed ('backlog', {sentinel!r})",
                    )
                    self.assertNotIn(
                        ("spec", sentinel),
                        r_idx,
                        f"check_engine.build_graduation_reverse_index indexed ('spec', {sentinel!r})",
                    )

                # 5. releases.check_from_backlog
                with self.subTest(
                    reader="releases.check_from_backlog", sentinel=sentinel
                ):
                    bkl_drift = [
                        d
                        for d in releases.check_from_backlog(repo)
                        if d.rule == "check.from-backlog-dangling"
                        and d.location == str(plan_bkl_file)
                    ]
                    self.assertEqual(
                        bkl_drift,
                        [],
                        f"releases.check_from_backlog reported dangling finding for sentinel {sentinel!r}",
                    )

                # 6. check_engine.check_from_spec_dangling
                with self.subTest(
                    reader="check_engine.check_from_spec_dangling", sentinel=sentinel
                ):
                    spc_drift = [
                        d
                        for d in check_engine.check_from_spec_dangling(repo)
                        if d.rule == "check.from-spec-dangling"
                        and d.location == str(plan_spc_file)
                    ]
                    self.assertEqual(
                        spc_drift,
                        [],
                        f"check_engine.check_from_spec_dangling reported dangling finding for sentinel {sentinel!r}",
                    )

    def test_valid_release_exempt_pair_yields_zero_findings(self) -> None:
        """A valid exempt pair on a live bug item yields zero check.live-bug-ungated and zero check.blocks-release-dangling findings."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug002-01-bug002-exempt-bug.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug002\n"
                "- Status: open\n"
                "- Set: bug002\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Live exempt bug\n"
                "- Release-Exempt-Kind: decision\n"
                "- Release-Exempt-Ref: D42\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertNotIn("check.live-bug-ungated", rules)
            self.assertNotIn("check.blocks-release-dangling", rules)

    def test_malformed_release_exempt_pair_does_not_silence_rule(self) -> None:
        """A malformed exempt pair does NOT silence check.live-bug-ungated."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug003-01-bug003-bad-exempt-bug.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug003\n"
                "- Status: open\n"
                "- Set: bug003\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Live bad exempt bug\n"
                "- Release-Exempt-Kind: decision\n"
                "- Release-Exempt-Ref: garbage\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertIn("check.live-bug-ungated", rules)

    def test_blocks_release_dash_marker_still_produces_dangling_finding(self) -> None:
        """The literal '- Blocks-Release: -' marker STILL produces check.blocks-release-dangling (pinned non-change)."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug004-01-bug004-dash-bug.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug004\n"
                "- Status: open\n"
                "- Set: bug004\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Live dash bug\n"
                "- Blocks-Release: -\n",
                encoding="utf-8",
            )
            findings = check_engine.check_release_gates(repo)
            rules = [d.rule for d in findings]
            self.assertIn("check.blocks-release-dangling", rules)


if __name__ == "__main__":
    unittest.main()

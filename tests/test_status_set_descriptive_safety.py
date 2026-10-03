"""Tests for Section 8.8 output-safety enforcement at the shared cross-tree setter.

IPD 4gwgo3 pins:
1. CROSS-TREE INJECTION CLOSURE (E-04): unsafe descriptive values (embedded newlines,
   carriage returns, control characters) across five guarded flags (--message, --actor,
   --gate-ref, --gate-summary, --blocks-release) are refused at positional set dispatch
   with exit 2, leaving the target artifact byte-identical by sha256. For --message,
   covers all five trees served (plans, specs, backlog, releases, prompts).
2. SHIPPED DIVERGENCE (E-04 / PR-205): the --status spelling retains its shipped refusal
   wording ('aw backlog set: --message must not contain embedded newlines') while the
   positional spelling emits the cross-tree setter refusal ('aw set: ...').
3. ATTESTATION FORGERY AND ESCALATION (E-05): composite injection that would forge
   readiness and review attestation is refused; pre-fix string assertions verify the
   vulnerability predicate behavior; plans-tree release gate escalation asymmetry is pinned.
4. LENGTH ASYMMETRY AND BOUNDARIES (E-06): 1200-char single-line --message is accepted,
   301-char --gate-summary is refused; boundary at exactly 300 accepted vs 301 refused;
   late control characters in --message (> 300 chars) are refused.
5. NON-REGRESSIONS (E-06): already-validated flags (--graduated-to, --release-exempt-ref)
   retain shipped refusals; actor_refusal empty and parenthesis checks and apply_status_change
   backstop raise survive; in-repo callers (work_cmd.run_finish and item-dependencies wrapper)
   succeed, with the wrapper newly refusing forwarded newline messages (PR-203); conforming
   transitions across all five trees succeed.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention_contract as ac
from agent_workflows import cli, ipd_schema, plan_readiness, releases, status_set


class StatusSetDescriptiveSafetyTestBase(unittest.TestCase):
    """Fixture repository layout and artifact generation helpers."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="aw_test_status_safety_")
        self.repo = Path(self.tmp)

        # Standard layout for all five trees
        (self.repo / ".aw" / "records" / "plans" / "pending").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "plans" / "executed").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "specs" / "draft").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "specs" / "to-review").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "specs" / "approved").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "backlog" / "open").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "backlog" / "blocked").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "backlog" / "parked").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "backlog" / "done").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "releases" / "planned").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "releases" / "shipped").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "prompts" / "pending").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / ".aw" / "records" / "prompts" / "executed").mkdir(
            parents=True, exist_ok=True
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def file_sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def call_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = cli.main(list(args))
        return rc, out.getvalue(), err.getvalue()

    def create_plan(
        self,
        filename: str,
        id6: str,
        set_id: str = "s1",
        status: str = "draft",
        disposition: str = "pending",
    ) -> Path:
        p = self.repo / ".aw" / "records" / "plans" / disposition / filename
        p.parent.mkdir(parents=True, exist_ok=True)
        content = f"""# IPD: Test Plan {id6}

- Date: 2026-10-01
- Kind: child
- Status: {status}
- Work-Kind: chore
- Priority: medium
- Set: {set_id}
- Order: 1
- Id: {id6}

## Workflow history
- 2026-10-01 {status} (aw set): initial draft.

## Goal
Test plan goal.
"""
        p.write_text(content, encoding="utf-8")
        return p

    def create_spec(
        self,
        filename: str,
        id6: str,
        set_id: str = "s1",
        status: str = "draft",
    ) -> Path:
        p = self.repo / ".aw" / "records" / "specs" / status / filename
        p.parent.mkdir(parents=True, exist_ok=True)
        content = f"""# Spec: Test Spec {id6}

- Date: 2026-10-01
- Status: {status}
- Set: {set_id}
- Id: {id6}

## Workflow history
- 2026-10-01 {status} (aw set): initial spec.

## Goal
Test spec goal.
"""
        p.write_text(content, encoding="utf-8")
        return p

    def create_backlog(
        self,
        filename: str,
        id6: str,
        set_id: str = "s1",
        status: str = "open",
    ) -> Path:
        p = self.repo / ".aw" / "records" / "backlog" / status / filename
        p.parent.mkdir(parents=True, exist_ok=True)
        content = f"""# Backlog Item {id6}

- Id: {id6}
- Status: {status}
- Set: {set_id}
- Priority: medium
- Kind: chore
- Summary: Test backlog item

## Workflow history
- 2026-10-01 {status} (aw set): created.
"""
        p.write_text(content, encoding="utf-8")
        return p

    def create_release(
        self,
        filename: str,
        id6: str,
        status: str = "planned",
        version: str = "1.0.0",
        disposition: str = "planned",
    ) -> Path:
        p = self.repo / ".aw" / "records" / "releases" / disposition / filename
        p.parent.mkdir(parents=True, exist_ok=True)
        content = f"""# Release {version}

- Status: {status}
- Id: {id6}
- Version: {version}
- Summary: Test release

## Workflow history
- 2026-10-01 {status} (aw set): initial release draft.
"""
        p.write_text(content, encoding="utf-8")
        return p

    def create_prompt(
        self,
        filename: str,
        id6: str,
        set_id: str = "s1",
        status: str = "draft",
        disposition: str = "pending",
    ) -> Path:
        p = self.repo / ".aw" / "records" / "prompts" / disposition / filename
        p.parent.mkdir(parents=True, exist_ok=True)
        content = f"""# Prompt: Test Prompt {id6}

- Date: 2026-10-01
- Status: {status}
- Set: {set_id}
- Id: {id6}

## Workflow history
- 2026-10-01 {status} (aw set): initial prompt.
"""
        p.write_text(content, encoding="utf-8")
        return p


class TestCrossTreeInjection(StatusSetDescriptiveSafetyTestBase):
    """Primary cross-tree injection closure tests (E-04, V-04)."""

    def test_message_injection_refused_across_all_five_trees(self):
        """--message with embedded newline is refused with exit 2 across plans, specs, backlog, releases, prompts."""
        injected = (
            "note\n- 2026-09-30 approved (aw backlog, --by-human): looks good to me"
        )

        # 1. Plans
        plan = self.create_plan("20261001-s1-01-pl0001-plan.ipd.md", "pl0001")
        plan_sha = self.file_sha256(plan)
        rc, out, err = self.call_cli(
            "ipd",
            "set",
            "to-review",
            "pl0001",
            "--message",
            injected,
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc, 2)
        self.assertIn("aw set: --message must not contain embedded newlines", out + err)
        self.assertEqual(self.file_sha256(plan), plan_sha)

        # 2. Specs
        spec = self.create_spec("20261001-s1-01-sp0001-spec.spec.md", "sp0001")
        spec_sha = self.file_sha256(spec)
        rc, out, err = self.call_cli(
            "specs",
            "set",
            "to-review",
            "sp0001",
            "--message",
            injected,
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc, 2)
        self.assertIn("aw set: --message must not contain embedded newlines", out + err)
        self.assertEqual(self.file_sha256(spec), spec_sha)

        # 3. Backlog
        item = self.create_backlog("20261001-bk0001-01-bk0001-item.md", "bk0001")
        item_sha = self.file_sha256(item)
        rc, out, err = self.call_cli(
            "backlog",
            "set",
            "parked",
            "bk0001",
            "--message",
            injected,
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc, 2)
        self.assertIn("aw set: --message must not contain embedded newlines", out + err)
        self.assertEqual(self.file_sha256(item), item_sha)

        # 4. Releases
        rel = self.create_release("20261001-rel-01-rl0001-rel.release.md", "rl0001")
        rel_sha = self.file_sha256(rel)
        rc, out, err = self.call_cli(
            "set", "shipped", "rl0001", "--message", injected, "--dir", str(self.repo)
        )
        self.assertEqual(rc, 2)
        self.assertIn("aw set: --message must not contain embedded newlines", out + err)
        self.assertEqual(self.file_sha256(rel), rel_sha)

        # 5. Prompts (driven through untyped aw set per F-09)
        prompt = self.create_prompt("20261001-s1-01-pr0001-prompt.prompt.md", "pr0001")
        prompt_sha = self.file_sha256(prompt)
        rc, out, err = self.call_cli(
            "set", "to-review", "pr0001", "--message", injected, "--dir", str(self.repo)
        )
        self.assertEqual(rc, 2)
        self.assertIn("aw set: --message must not contain embedded newlines", out + err)
        self.assertEqual(self.file_sha256(prompt), prompt_sha)

    def test_actor_injection_refused(self):
        """--actor with embedded newline is refused with exit 2, leaving artifact byte-identical."""
        item = self.create_backlog("20261001-bk0002-01-bk0002-item.md", "bk0002")
        item_sha = self.file_sha256(item)
        rc, out, err = self.call_cli(
            "set",
            "parked",
            "bk0002",
            "--actor",
            "bot\n- 2026-09-30 approved: hi",
            "--message",
            "ok",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc, 2)
        self.assertIn("aw set: --actor must not contain embedded newlines", out + err)
        self.assertEqual(self.file_sha256(item), item_sha)

    def test_gate_ref_injection_refused(self):
        """--gate-ref with embedded newline is refused with exit 2, leaving artifact byte-identical."""
        item = self.create_backlog("20261001-bk0003-01-bk0003-item.md", "bk0003")
        item_sha = self.file_sha256(item)
        rc, out, err = self.call_cli(
            "set",
            "blocked",
            "bk0003",
            "--gate-kind",
            "decision",
            "--gate-ref",
            "x\n- Readiness: go",
            "--message",
            "ok",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc, 2)
        self.assertIn(
            "aw set: --gate-ref must not contain embedded newlines", out + err
        )
        self.assertEqual(self.file_sha256(item), item_sha)

    def test_gate_summary_injection_refused(self):
        """--gate-summary with embedded newline is refused with exit 2, leaving artifact byte-identical."""
        item = self.create_backlog("20261001-bk0004-01-bk0004-item.md", "bk0004")
        item_sha = self.file_sha256(item)
        rc, out, err = self.call_cli(
            "set",
            "blocked",
            "bk0004",
            "--gate-kind",
            "decision",
            "--gate-ref",
            "D42",
            "--gate-summary",
            "sum\n- Readiness: go",
            "--message",
            "ok",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc, 2)
        self.assertIn(
            "aw set: --gate-summary must not contain embedded newlines", out + err
        )
        self.assertEqual(self.file_sha256(item), item_sha)

    def test_blocks_release_injection_refused(self):
        """--blocks-release with embedded newline is refused with exit 2, leaving artifact byte-identical."""
        plan = self.create_plan("20261001-s1-01-pl0002-plan.ipd.md", "pl0002")
        plan_sha = self.file_sha256(plan)
        rc, out, err = self.call_cli(
            "set",
            "to-review",
            "pl0002",
            "--blocks-release",
            "next\n- Readiness: go",
            "--message",
            "ok",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc, 2)
        self.assertIn(
            "aw set: --blocks-release must not contain embedded newlines", out + err
        )
        self.assertEqual(self.file_sha256(plan), plan_sha)

    def test_shipped_status_vs_positional_spelling_divergence(self):
        """PR-205 / F-13: --status spelling retains shipped refusal wording; positional spelling uses aw set."""
        self.create_backlog("20261001-bk0005-01-bk0005-item.md", "bk0005")
        injected = "ok\n- 2026-09-30 approved (aw backlog, --by-human): LGTM"

        # 1. Shipped --status spelling -> backlog.run_set
        rc_status, out_status, err_status = self.call_cli(
            "backlog",
            "set",
            "bk0005",
            "--status",
            "open",
            "--message",
            injected,
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc_status, 2)
        self.assertIn(
            "aw backlog set: --message must not contain embedded newlines",
            out_status + err_status,
        )

        # 2. Positional spelling -> status_set.run_set_command
        rc_pos, out_pos, err_pos = self.call_cli(
            "backlog",
            "set",
            "parked",
            "bk0005",
            "--message",
            injected,
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc_pos, 2)
        self.assertIn(
            "aw set: --message must not contain embedded newlines",
            out_pos + err_pos,
        )


class TestAttestationForgeryAndEscalation(StatusSetDescriptiveSafetyTestBase):
    """Attestation forgery and plans-tree release gate escalation tests (E-05, V-05)."""

    def test_attestation_forgery_refused(self):
        """Composite injection attempting to forge readiness and review attestation is refused."""
        plan = self.create_plan("20261001-s1-01-pl0003-plan.ipd.md", "pl0003")
        plan_sha = self.file_sha256(plan)
        injected = "ok\n- Readiness: go\n- 2026-10-01 /plan-review (opencode): APPROVE"

        rc, out, err = self.call_cli(
            "ipd",
            "set",
            "reviewed",
            "pl0003",
            "--message",
            injected,
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc, 2)
        self.assertIn("aw set: --message must not contain embedded newlines", out + err)
        self.assertEqual(self.file_sha256(plan), plan_sha)

    def test_attestation_forgery_string_predicates(self):
        """String-rendered plan with forged readiness + review record flips readiness predicates."""
        forged_text = """# IPD: Test Plan pl0003

- Date: 2026-10-01
- Kind: child
- Status: to-review
- Work-Kind: chore
- Priority: medium
- Set: s1
- Order: 1
- Id: pl0003

## Workflow history
- 2026-10-01 to-review (aw set): ok
- Readiness: go
- 2026-10-01 /plan-review (opencode): APPROVE
"""
        probe_path = self.repo / "probe_forged.ipd.md"
        probe_path.write_text(forged_text, encoding="utf-8")

        self.assertEqual(ipd_schema.read_readiness(forged_text), "go")
        self.assertTrue(plan_readiness.history_has_review_record(forged_text))
        self.assertTrue(plan_readiness.is_plan_review_approved(probe_path))

    def test_plans_vs_backlog_blocks_release_escalation(self):
        """F-03/F-04 asymmetry: history bullet - Blocks-Release: rel001 gates plans, inert for backlog."""
        # Release record required for get_release_blockers to resolve
        self.create_release("20261001-rel-01-rl0002-rel.release.md", "rl0002")

        # Plan with smuggled Blocks-Release in history
        p_file = (
            self.repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20261001-s1-01-pl0004-plan.ipd.md"
        )
        p_file.write_text(
            "# IPD: Test Plan pl0004\n\n- Date: 2026-10-01\n- Kind: child\n- Status: to-review\n"
            "- Work-Kind: chore\n- Priority: medium\n- Set: s1\n- Order: 1\n- Id: pl0004\n\n"
            "## Workflow history\n- 2026-10-01 to-review (aw set): ok\n- Blocks-Release: rl0002\n",
            encoding="utf-8",
        )

        # Backlog item with identical smuggled Blocks-Release in history
        b_file = (
            self.repo
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20261001-bk0006-01-bk0006-item.md"
        )
        b_file.write_text(
            "# Backlog Item bk0006\n\n- Id: bk0006\n- Status: open\n- Set: s1\n"
            "- Priority: medium\n- Kind: chore\n- Summary: Test\n\n"
            "## Workflow history\n- 2026-10-01 open (aw set): ok\n- Blocks-Release: rl0002\n",
            encoding="utf-8",
        )

        blockers = releases.get_release_blockers(self.repo, "rl0002")
        blocker_ids = [b["id"] for b in blockers]
        self.assertIn("pl0004", blocker_ids)
        self.assertNotIn("bk0006", blocker_ids)


class TestLengthAsymmetryAndNonRegressions(StatusSetDescriptiveSafetyTestBase):
    """Length asymmetry, boundary checks, and non-regressions (E-06, V-06)."""

    def test_length_asymmetry_and_late_control_characters(self):
        """1200-char --message accepted; 301-char --gate-summary refused; late control chars refused."""
        item1 = self.create_backlog("20261001-bk0007-01-bk0007-item.md", "bk0007")
        long_message = "m" * 1200
        rc1, _out1, _err1 = self.call_cli(
            "set",
            "parked",
            "bk0007",
            "--message",
            long_message,
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc1, 0)
        # Target moved to parked/
        moved = self.repo / ".aw" / "records" / "backlog" / "parked" / item1.name
        self.assertTrue(moved.exists())
        self.assertIn(long_message, moved.read_text(encoding="utf-8"))

        self.create_backlog("20261001-bk0008-01-bk0008-item.md", "bk0008")
        rc2, out2, err2 = self.call_cli(
            "set",
            "blocked",
            "bk0008",
            "--gate-kind",
            "decision",
            "--gate-ref",
            "D42",
            "--gate-summary",
            "s" * 301,
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc2, 2)
        self.assertIn(
            "aw set: --gate-summary exceeds maximum length of 300 characters (301 > 300)",
            out2 + err2,
        )

        # Late control character past 300 characters in --message
        self.create_backlog("20261001-bk0009-01-bk0009-item.md", "bk0009")
        rc3, out3, err3 = self.call_cli(
            "set",
            "parked",
            "bk0009",
            "--message",
            "a" * 500 + "\x07" + "b",
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc3, 2)
        self.assertIn(
            "aw set: --message must not contain control characters", out3 + err3
        )

    def test_boundary_gate_summary_length(self):
        """Boundary: --gate-summary at exactly 300 chars is accepted; 301 chars is refused."""
        item1 = self.create_backlog("20261001-bk0010-01-bk0010-item.md", "bk0010")
        rc1, _out1, _err1 = self.call_cli(
            "set",
            "blocked",
            "bk0010",
            "--gate-kind",
            "decision",
            "--gate-ref",
            "D42",
            "--gate-summary",
            "s" * 300,
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc1, 0)
        moved = self.repo / ".aw" / "records" / "backlog" / "blocked" / item1.name
        self.assertTrue(moved.exists())
        self.assertIn(f"- Gate-Summary: {'s' * 300}", moved.read_text(encoding="utf-8"))

        self.create_backlog("20261001-bk0011-01-bk0011-item.md", "bk0011")
        rc2, out2, err2 = self.call_cli(
            "set",
            "blocked",
            "bk0011",
            "--gate-kind",
            "decision",
            "--gate-ref",
            "D42",
            "--gate-summary",
            "s" * 301,
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc2, 2)
        self.assertIn("301 > 300", out2 + err2)

    def test_non_regression_already_validated_flags(self):
        """Existing refusals on --graduated-to and --release-exempt-ref are unchanged."""
        self.create_backlog("20261001-bk0012-01-bk0012-item.md", "bk0012")

        # --graduated-to shape refusal
        rc1, out1, err1 = self.call_cli(
            "set",
            "graduated",
            "bk0012",
            "--graduated-to",
            "x\n- Readiness: go",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc1, 2)
        self.assertIn(
            "aw set: --graduated-to takes lowercase-kebab setids", out1 + err1
        )

        # --release-exempt-ref kind refusal
        rc2, out2, err2 = self.call_cli(
            "set",
            "parked",
            "bk0012",
            "--release-exempt-kind",
            "decision",
            "--release-exempt-ref",
            "r1\n- Readiness: go",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc2, 2)
        self.assertIn(
            "aw set: --release-exempt-ref is invalid for kind 'decision'", out2 + err2
        )

    def test_non_regression_actor_refusals_and_backstop(self):
        """actor_refusal's empty and parenthesis checks remain unchanged, and apply_status_change raises."""
        self.assertEqual(ac.actor_refusal(""), "a non-empty actor is required.")
        self.assertIn("contains a parenthesis", ac.actor_refusal("bot(foo)") or "")

        item = self.create_backlog("20261001-bk0013-01-bk0013-item.md", "bk0013")
        rec = status_set.read_artifact_record(item, self.repo)
        self.assertIsNotNone(rec)
        ns = argparse.Namespace(actor="bot(foo)", message="m")
        with self.assertRaises(ValueError) as ctx:
            status_set.apply_status_change(rec, "parked", self.repo, ns)
        self.assertIn("contains a parenthesis", str(ctx.exception))

    def test_in_repo_callers_and_deps_wrapper(self):
        """In-repo callers still work: simulated run_finish succeeds, item-deps wrapper succeeds and refuses newlines."""
        self.create_plan(
            "20261001-s1-01-pl0005-plan.ipd.md", "pl0005", status="to-review"
        )

        # Simulated work_cmd.run_finish Namespace
        finish_ns = argparse.Namespace(
            dir=str(self.repo),
            message="aw finish: evidence-bound transition",
            yes=True,
        )
        rc = status_set.run_set_command(
            ["reviewed", "pl0005"],
            scoped_type="plans",
            repo_root=self.repo,
            args=finish_ns,
        )
        self.assertEqual(rc, 0)

        # --item-dependencies wrapper: default message succeeds
        rc_deps_default, _out_dd, _err_dd = self.call_cli(
            "ipd",
            "dependencies",
            "set",
            "pl0005",
            "none",
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc_deps_default, 0)

        # --item-dependencies wrapper: user-supplied newline message is newly REFUSED (PR-203)
        rc_deps_newline, out_dn, err_dn = self.call_cli(
            "ipd",
            "dependencies",
            "set",
            "pl0005",
            "none",
            "--message",
            "custom\n- Readiness: go",
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc_deps_newline, 2)
        self.assertIn(
            "aw set: --message must not contain embedded newlines", out_dn + err_dn
        )

    def test_conforming_transitions_across_five_trees(self):
        """Conforming transitions on plans, specs, backlog, releases, and prompts all succeed with history written."""
        # 1. Plan
        self.create_plan("20261001-s1-01-pl0006-plan.ipd.md", "pl0006", status="draft")
        rc1, _, _ = self.call_cli(
            "ipd",
            "set",
            "to-review",
            "pl0006",
            "--message",
            "conforming plan note",
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc1, 0)
        p1 = next(iter(self.repo.rglob("*pl0006*.ipd.md")))
        self.assertIn("conforming plan note", p1.read_text(encoding="utf-8"))

        # 2. Spec
        self.create_spec("20261001-s1-01-sp0002-spec.spec.md", "sp0002", status="draft")
        rc2, _, _ = self.call_cli(
            "specs",
            "set",
            "to-review",
            "sp0002",
            "--message",
            "conforming spec note",
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc2, 0)
        p2 = next(iter(self.repo.rglob("*sp0002*.spec.md")))
        self.assertIn("conforming spec note", p2.read_text(encoding="utf-8"))

        # 3. Backlog
        self.create_backlog(
            "20261001-bk0014-01-bk0014-item.md", "bk0014", status="open"
        )
        rc3, _, _ = self.call_cli(
            "backlog",
            "set",
            "parked",
            "bk0014",
            "--message",
            "conforming backlog note",
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc3, 0)
        p3 = next(iter(self.repo.rglob("*bk0014*.md")))
        self.assertIn("conforming backlog note", p3.read_text(encoding="utf-8"))

        # 4. Release
        self.create_release(
            "20261001-rel-01-rl0003-rel.release.md", "rl0003", status="planned"
        )
        rc4, _, _ = self.call_cli(
            "set",
            "shipped",
            "rl0003",
            "--message",
            "conforming release note",
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc4, 0)
        p4 = next(iter(self.repo.rglob("*rl0003*.release.md")))
        self.assertIn("conforming release note", p4.read_text(encoding="utf-8"))

        # 5. Prompt
        self.create_prompt(
            "20261001-s1-01-pr0002-prompt.prompt.md", "pr0002", status="pending"
        )
        rc5, _, _ = self.call_cli(
            "set",
            "executed",
            "pr0002",
            "--message",
            "conforming prompt note",
            "--yes",
            "--dir",
            str(self.repo),
        )
        self.assertEqual(rc5, 0)
        p5 = next(iter(self.repo.rglob("*pr0002*.prompt.md")))
        self.assertIn("conforming prompt note", p5.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

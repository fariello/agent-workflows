"""Tests for orchestrator review readiness (spec 25kzda 2.5d) and aw ipd coverage.

Validates:
E-01: review_readiness() four conditions, finding codes, and remedy constants.
E-02: human and agent renderings, deterministic findings, no absolute paths.
E-03: aw ipd coverage CLI verb, probe invocation, caching, and exits.
E-04: IPD-S408 and IPD-M112 in ipd_lint.py.
E-05: test coverage across conditions, fixtures, parity, and model-free linters.
E-06: check.orchestrator-not-review-ready in check_engine.py.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import check_engine, coverage_record, ipd_lint
from agent_workflows import orchestrator_readiness as readiness
from agent_workflows import runner_shared as rs
from tests.test_ipd_lint import _conforming_child, _executed_child


def _init_repo(tmp_dir: Path) -> Path:
    repo = tmp_dir.resolve()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "plans" / "executed").mkdir(parents=True, exist_ok=True)
    return repo


def _make_orchestrator(
    repo: Path,
    *,
    id6: str = "orc001",
    setid: str = "tstset",
    status: str = "to-review",
    child_rows: list[tuple[str, str, str]] | None = None,
    checklist_item: str = "- [ ] E-01 CONFIRM chd001 REACHED executed\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending",
    omit_child_table: bool = False,
) -> Path:
    pending_dir = repo / ".aw" / "records" / "plans" / "pending"
    orch_path = pending_dir / f"20261004-{setid}-00-{id6}-test.ipd.md"

    if child_rows is None:
        child_rows = [
            (
                "01",
                "chd001",
                f".aw/records/plans/pending/20261004-{setid}-01-chd001-test.ipd.md",
            )
        ]

    lines = [
        f"# IPD: Orchestrator {id6}",
        "",
        "- Date: 2026-10-04",
        "- Kind: orchestrator",
        f"- Id: {id6}",
        f"- Set: {setid}",
        "- Order: 0",
        f"- Status: {status}",
        "- Priority: medium",
        "- Work-Kind: chore",
        "- Author: test",
        "- Highest E allocated: 01",
        "- Concern: test concern.",
        "- Scope: test scope.",
        "- Scope-Paths: none",
        "- Item-Dependencies: none",
    ]
    if status == "approved":
        lines.append("- Approval: 2026-10-04, test approved")
    lines.extend(
        [
            "",
            "## Workflow history",
            "",
            f"- 2026-10-04 {status} (test): created.",
            "",
            "## Goal",
            "",
            "Test orchestrator goal.",
            "",
            "## Detailed Implementation Checklist (TODO)",
            "",
            checklist_item,
            "",
        ]
    )
    if not omit_child_table:
        lines.extend(
            [
                "## Child IPDs, sequence, and dependencies",
                "",
                "| Order | Id | Status | Plan | Depends on |",
                "|---|---|---|---|---|",
            ]
        )
        for ord_tok, c_id6, c_path in child_rows:
            lines.append(f"| {ord_tok} | {c_id6} | pending | {c_path} | none |")
        lines.append("")

    lines.extend(
        [
            "## Completion criteria (the whole Set is done only when)",
            "",
            "- None.",
            "",
            "## Cross-IPD validation",
            "",
            "- None.",
            "",
            "## Deferred / out of scope (with reason)",
            "",
            "- None.",
            "",
            "## Scope check",
            "",
            "- None.",
            "",
            "## Required tests / validation",
            "",
            "- None.",
            "",
            "## Open questions",
            "",
            "- None.",
            "",
            "## Validation and cross-check (verify before reporting the Set complete)",
            "",
            "- [ ] V-01 validates E-01",
            "  - Required evidence: check.",
            "  - Observed evidence:",
            "  - Result: pending",
            "",
            "## Approval and execution gate",
            "",
            "- None.",
            "",
        ]
    )
    orch_path.write_text("\n".join(lines), encoding="utf-8")
    return orch_path


def _make_child(
    repo: Path,
    *,
    id6: str = "chd001",
    setid: str = "tstset",
    order: int = 1,
    status: str = "to-review",
    in_executed: bool = False,
    broken_lint: bool = False,
) -> Path:
    bucket = "executed" if in_executed else "pending"
    p_dir = repo / ".aw" / "records" / "plans" / bucket
    p_dir.mkdir(parents=True, exist_ok=True)
    child_path = p_dir / f"20261004-{setid}-{order:02d}-{id6}-test.ipd.md"

    if in_executed or status == "executed":
        text = (
            _executed_child()
            .replace("- Set: x", f"- Set: {setid}")
            .replace("- Order: 1", f"- Order: {order}")
            .replace("- Id: abc123", f"- Id: {id6}")
        )
    else:
        text = (
            _conforming_child()
            .replace("- Set: x", f"- Set: {setid}")
            .replace("- Order: 1", f"- Order: {order}")
            .replace("- Id: abc123", f"- Id: {id6}")
            .replace("- Status: to-review", f"- Status: {status}")
        )
    if broken_lint:
        # Break required heading
        text = text.replace("## Goal", "## Broken")

    child_path.write_text(text, encoding="utf-8")
    return child_path


class TestOrchestratorReadinessConditions(unittest.TestCase):
    """Test conditions 1-4 of orchestrator review readiness (spec 25kzda 2.5d)."""

    def test_condition_1_child_table_unusable(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo, omit_child_table=True)
            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_TABLE_UNUSABLE, codes)
            f = next(f for f in res.findings if f.code == readiness.CODE_TABLE_UNUSABLE)
            self.assertEqual(f.remedy, readiness.REMEDY_TABLE_UNUSABLE)
            self.assertEqual(f.subject, "orc001")

    def test_condition_1_child_unauthored(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            # chd001 is NOT created on disk
            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_CHILD_UNAUTHORED, codes)
            f = next(
                f for f in res.findings if f.code == readiness.CODE_CHILD_UNAUTHORED
            )
            self.assertEqual(f.remedy, readiness.REMEDY_CHILD_UNAUTHORED)
            self.assertEqual(f.subject, "01")

    def test_condition_1_child_open_ended(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(
                repo,
                child_rows=[("03+", "unres", ".aw/records/plans/pending/none.ipd.md")],
            )
            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_CHILD_OPEN_ENDED, codes)
            f = next(
                f for f in res.findings if f.code == readiness.CODE_CHILD_OPEN_ENDED
            )
            self.assertEqual(f.remedy, readiness.REMEDY_CHILD_OPEN_ENDED)
            self.assertEqual(f.subject, "03+")

    def test_condition_2_child_status_draft(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            _make_child(repo, id6="chd001", status="draft")
            coverage_record.write(orch, "pass", model="fixture", tool="test")
            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_CHILD_STATUS, codes)
            f = next(f for f in res.findings if f.code == readiness.CODE_CHILD_STATUS)
            self.assertEqual(f.remedy, readiness.REMEDY_CHILD_STATUS)
            self.assertEqual(f.subject, "chd001")

    def test_condition_2_child_fails_lint(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            _make_child(repo, id6="chd001", status="to-review", broken_lint=True)
            coverage_record.write(orch, "pass", model="fixture", tool="test")
            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_CHILD_LINT, codes)
            f = next(f for f in res.findings if f.code == readiness.CODE_CHILD_LINT)
            self.assertEqual(f.remedy, readiness.REMEDY_CHILD_LINT)
            self.assertEqual(f.subject, "chd001")

    def test_condition_2_executed_child_under_executed_dir_is_ready(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(
                repo,
                child_rows=[
                    (
                        "01",
                        "chd001",
                        ".aw/records/plans/executed/20261004-tstset-01-chd001-test.ipd.md",
                    )
                ],
            )
            _make_child(repo, id6="chd001", status="executed", in_executed=True)
            coverage_record.write(orch, "pass", model="fixture", tool="test")
            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertTrue(res.ready, [f.detail for f in res.findings])
            self.assertEqual(res.findings, ())

    def test_condition_3_checklist_row_nonconforming(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(
                repo,
                checklist_item="- [ ] E-01 Untyped prose item without confirm\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending",
            )
            _make_child(repo, id6="chd001", status="to-review")
            coverage_record.write(orch, "pass", model="fixture", tool="test")
            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_ROW_NONCONFORMING, codes)
            f = next(
                f for f in res.findings if f.code == readiness.CODE_ROW_NONCONFORMING
            )
            self.assertEqual(f.remedy, readiness.REMEDY_ROW_NONCONFORMING)

    def test_condition_4_coverage_record_absent(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            _make_child(repo, id6="chd001", status="to-review")
            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_COVERAGE_ABSENT, codes)
            f = next(
                f for f in res.findings if f.code == readiness.CODE_COVERAGE_ABSENT
            )
            self.assertEqual(f.remedy, readiness.REMEDY_COVERAGE_RECORD)
            self.assertEqual(f.subject, "orc001")

    def test_condition_4_coverage_record_stale(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            _make_child(repo, id6="chd001", status="to-review")
            coverage_record.write(orch, "pass", model="fixture", tool="test")
            # Modify orchestrator text after record write (stale fingerprint)
            text = orch.read_text(encoding="utf-8")
            text = text.replace(
                "Test orchestrator goal.", "Modified goal that changes fingerprint."
            )
            orch.write_text(text, encoding="utf-8")

            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_COVERAGE_STALE, codes)
            f = next(f for f in res.findings if f.code == readiness.CODE_COVERAGE_STALE)
            self.assertEqual(f.remedy, readiness.REMEDY_COVERAGE_RECORD)

    def test_condition_4_coverage_fail_with_two_quotes(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            _make_child(repo, id6="chd001", status="to-review")
            quotes = ("uncovered obligation one", "uncovered obligation two")
            coverage_record.write(
                orch, "fail", quotes=quotes, model="fixture", tool="test"
            )

            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            fail_findings = [
                f for f in res.findings if f.code == readiness.CODE_COVERAGE_FAIL
            ]
            self.assertEqual(len(fail_findings), 2)
            self.assertIn("obligation one", fail_findings[0].detail)
            self.assertIn("obligation two", fail_findings[1].detail)
            for f in fail_findings:
                self.assertEqual(f.remedy, readiness.REMEDY_COVERAGE_FAIL)

    def test_condition_4_could_not_ask(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            _make_child(repo, id6="chd001", status="to-review")

            def failing_asker(*args, **kwargs):
                return (rs.PROBE_ANSWER_COULD_NOT_ASK, "fake-model")

            res = readiness.review_readiness(repo, orch, ask=True, asker=failing_asker)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_COVERAGE_COULD_NOT_ASK, codes)
            f = next(
                f
                for f in res.findings
                if f.code == readiness.CODE_COVERAGE_COULD_NOT_ASK
            )
            self.assertEqual(f.remedy, readiness.REMEDY_COVERAGE_COULD_NOT_ASK)

    def test_ready_orchestrator(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            _make_child(repo, id6="chd001", status="to-review")
            coverage_record.write(orch, "pass", model="fixture", tool="test")

            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertTrue(res.ready)
            self.assertEqual(res.findings, ())
            self.assertTrue(res.cached)
            self.assertEqual(res.calls, 0)


class TestIpdM112LintCases(unittest.TestCase):
    """Test IPD-M112 lint rule for hand-written / malformed coverage records."""

    def test_m112_missing_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            coverage_record.write(orch, "pass", model="fixture", tool="test")
            # Strip Coverage-Fingerprint field
            text = orch.read_text(encoding="utf-8")
            lines = [
                line
                for line in text.splitlines()
                if not line.startswith("- Coverage-Fingerprint:")
            ]
            orch.write_text("\n".join(lines), encoding="utf-8")

            res = ipd_lint.lint_file(orch, checkpoint="author")
            diag_codes = [d.code for d in res.diagnostics]
            self.assertIn(ipd_lint.C_COVERAGE_RECORD, diag_codes)
            diag = next(
                d for d in res.diagnostics if d.code == ipd_lint.C_COVERAGE_RECORD
            )
            self.assertIn("aw ipd coverage", diag.message)

    def test_m112_fail_without_findings_section(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            coverage_record.write(
                orch, "fail", quotes=("some quote",), model="fixture", tool="test"
            )
            # Remove ## Coverage findings section
            text = orch.read_text(encoding="utf-8")
            lines = [
                line
                for line in text.splitlines()
                if not line.startswith("## Coverage findings")
                and not line.startswith('- "some quote"')
            ]
            orch.write_text("\n".join(lines), encoding="utf-8")

            res = ipd_lint.lint_file(orch, checkpoint="author")
            diag_codes = [d.code for d in res.diagnostics]
            self.assertIn(ipd_lint.C_COVERAGE_RECORD, diag_codes)

    def test_m112_no_matching_history_line(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            coverage_record.write(orch, "pass", model="fixture", tool="test")
            # Remove the workflow history line
            text = orch.read_text(encoding="utf-8")
            lines = [line for line in text.splitlines() if "coverage pass" not in line]
            orch.write_text("\n".join(lines), encoding="utf-8")

            res = ipd_lint.lint_file(orch, checkpoint="author")
            diag_codes = [d.code for d in res.diagnostics]
            self.assertIn(ipd_lint.C_COVERAGE_RECORD, diag_codes)


class TestIpdCoverageCommand(unittest.TestCase):
    """Test aw ipd coverage CLI invocation, caching, and exits."""

    def test_ipd_coverage_agent_bare_repo_no_args(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            cmd = [
                "python3",
                "-m",
                "agent_workflows",
                "ipd",
                "coverage",
                "--agent",
                "--dir",
                str(repo),
            ]
            env = dict(os.environ)
            proc = subprocess.run(
                cmd, capture_output=True, text=True, env=env, check=False
            )
            self.assertEqual(
                proc.returncode,
                2,
                f"Expected exit 2, got {proc.returncode}: {proc.stderr}",
            )
            payload = json.loads(proc.stdout)
            self.assertEqual(payload.get("schema"), "aw.agent/v1")
            self.assertEqual(payload.get("cmd"), "ipd coverage")
            self.assertEqual(payload.get("exit"), 2)
            self.assertEqual(payload.get("outcome"), "cannot-run")

    def test_ipd_coverage_second_invocation_caching(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            _make_child(repo, id6="chd001", status="to-review")

            calls = 0

            def fake_asker(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
                nonlocal calls
                calls += 1
                return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model")

            res1 = readiness.review_readiness(
                repo, orch, ask=True, asker=fake_asker, suppress_commit=True
            )
            self.assertTrue(res1.ready)
            self.assertFalse(res1.cached)
            self.assertEqual(res1.calls, 1)
            self.assertEqual(calls, 1)

            # Record was written to plan
            text_after = orch.read_text(encoding="utf-8")
            self.assertIn("- Coverage: pass", text_after)
            self.assertIn("- Coverage-Fingerprint:", text_after)
            self.assertIn("coverage pass", text_after)

            # Second invocation on unchanged plan reads from plan and spends 0 calls
            res2 = readiness.review_readiness(
                repo, orch, ask=True, asker=fake_asker, suppress_commit=True
            )
            self.assertTrue(res2.ready)
            self.assertTrue(res2.cached)
            self.assertEqual(res2.calls, 0)
            self.assertEqual(calls, 1, "Second invocation must make zero probe calls")


class TestConsumerParityAndModelFreeLinters(unittest.TestCase):
    """Test parity across lint, check, and coverage, and assert linters never call model."""

    def test_parity_across_lint_check_and_coverage(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            # Create orchestrator with open-ended child row (Condition 1 finding)
            orch = _make_orchestrator(
                repo,
                child_rows=[("03+", "unres", ".aw/records/plans/pending/none.ipd.md")],
            )
            # Pre-write valid coverage record so coverage verb reads it instead of asking
            coverage_record.write(orch, "pass", model="fixture", tool="test")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

            env = dict(os.environ)
            env["PYTHONPATH"] = str(Path.cwd())

            # 1. aw ipd lint --phase review-finalize
            lint_cmd = [
                "python3",
                "-m",
                "agent_workflows",
                "ipd",
                "lint",
                str(orch),
                "--phase",
                "review-finalize",
            ]
            lint_proc = subprocess.run(
                lint_cmd, cwd=repo, capture_output=True, text=True, env=env, check=False
            )
            self.assertNotEqual(lint_proc.returncode, 0)
            combined_lint = lint_proc.stdout + lint_proc.stderr
            self.assertIn(readiness.CODE_CHILD_OPEN_ENDED, combined_lint)

            # 2. aw check plans --agent
            check_cmd = [
                "python3",
                "-m",
                "agent_workflows",
                "check",
                "plans",
                "--agent",
                "--dir",
                str(repo),
            ]
            check_proc = subprocess.run(
                check_cmd,
                cwd=repo,
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertNotEqual(check_proc.returncode, 0)
            check_payload = json.loads(check_proc.stdout)
            check_rules = [
                d.get("rule", "") for d in check_payload.get("diagnostics", [])
            ]
            self.assertIn("check.orchestrator-not-review-ready", check_rules)

            # Check human output for the remedy
            check_human_cmd = [
                "python3",
                "-m",
                "agent_workflows",
                "check",
                "plans",
                "--dir",
                str(repo),
            ]
            check_human_proc = subprocess.run(
                check_human_cmd,
                cwd=repo,
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertIn(
                "author the missing child and its row", check_human_proc.stdout
            )

            # 3. aw ipd coverage --agent
            cov_cmd = [
                "python3",
                "-m",
                "agent_workflows",
                "ipd",
                "coverage",
                str(orch),
                "--agent",
                "--no-commit",
            ]
            cov_proc = subprocess.run(
                cov_cmd, cwd=repo, capture_output=True, text=True, env=env, check=False
            )
            self.assertEqual(cov_proc.returncode, 1)
            cov_payload = json.loads(cov_proc.stdout)
            cov_findings = cov_payload.get("data", {}).get("finding_codes", []) or [
                f.get("code")
                for item in cov_payload.get("data", {}).get("orchestrators", [])
                for f in item.get("findings", [])
            ]
            self.assertIn(readiness.CODE_CHILD_OPEN_ENDED, cov_findings)

    def test_lint_and_check_never_call_model(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo)
            _make_child(repo, id6="chd001", status="to-review")

            def explode_if_called(*args, **kwargs):
                raise AssertionError("Model probe was called unexpectedly!")

            with mock.patch.object(rs, "ask_orchestrator_probe", explode_if_called):
                # Lint at review-finalize on orchestrator without coverage record
                res_lint = ipd_lint.lint_file(orch, checkpoint="review-finalize")
                self.assertFalse(res_lint.passing)

                # Check on orchestrator without coverage record
                findings = check_engine.check_orchestrator_not_review_ready(repo, orch)
                self.assertTrue(len(findings) > 0)


class TestOrchestratorReadinessRefusalStylingAndFormatting(unittest.TestCase):
    """Pin items 1-4 of E-05 (plan juu1rj)."""

    def test_render_human_target_status_approved(self):
        f = readiness.Finding(
            code=readiness.CODE_CHILD_STATUS,
            subject="62pkkg",
            detail="child 62pkkg has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)",
            remedy="bring the child to `to-review` with `aw ipd set to-review 62pkkg`",
        )
        r = readiness.ReviewReadiness(
            applies=True,
            ready=False,
            findings=(f,),
            id6="itamry",
            setid="setfoo",
        )
        rendered = readiness.render_human(r, target_status="approved")
        self.assertTrue(
            rendered.startswith(
                "Refusing to set approved for orchestrator itamry (set setfoo):"
            )
        )
        self.assertIn("62pkkg", rendered)
        self.assertIn(
            "An orchestrator may not advance while a child in its Set is not ready",
            rendered,
        )

    def test_render_human_byte_identical_default_and_to_review(self):
        f = readiness.Finding(
            code=readiness.CODE_CHILD_STATUS,
            subject="62pkkg",
            detail="child 62pkkg has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)",
            remedy="bring the child to `to-review` with `aw ipd set to-review 62pkkg`",
        )
        r = readiness.ReviewReadiness(
            applies=True,
            ready=False,
            findings=(f,),
            id6="itamry",
            setid="setfoo",
        )
        default_out = readiness.render_human(r)
        to_review_out = readiness.render_human(r, target_status="to-review")
        self.assertEqual(default_out, to_review_out)
        self.assertTrue(
            default_out.startswith("Orchestrator itamry is not ready for review:")
        )
        expected_lines = [
            "Orchestrator itamry is not ready for review:",
            "  - [child-status-not-ready] 62pkkg: child 62pkkg has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)",
            "    Remedy: bring the child to `to-review` with `aw ipd set to-review 62pkkg`",
        ]
        self.assertEqual(default_out, "\n".join(expected_lines))

    def test_child_lint_question_extraction_and_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            c_path = ".aw/records/plans/pending/20261004-tstset-01-chd001-test.ipd.md"
            orch = _make_orchestrator(
                repo,
                id6="orc001",
                setid="tstset",
                child_rows=[("01", "chd001", c_path)],
            )
            child = _make_child(
                repo, id6="chd001", setid="tstset", order=1, status="to-review"
            )
            child_text = child.read_text(encoding="utf-8")
            child_text = child_text.replace(
                "### OQ-01: a question\n\n- Blocking: no",
                "### OQ-06: Which admitted forms does TRACE treat as mandatory?\n\n- Blocking: yes",
            )
            child.write_text(child_text, encoding="utf-8")

            res = readiness.review_readiness(repo, orch, ask=False)
            clf = [f for f in res.findings if f.code == readiness.CODE_CHILD_LINT]
            self.assertEqual(len(clf), 1)
            self.assertEqual(
                clf[0].questions,
                (("OQ-06", "Which admitted forms does TRACE treat as mandatory?"),),
            )
            rendered = readiness.render_human(res)
            self.assertIn(
                "OQ-06: Which admitted forms does TRACE treat as mandatory?", rendered
            )

            # Fallback when questions is empty
            f_fallback = readiness.Finding(
                code=readiness.CODE_CHILD_LINT,
                subject="chd001",
                detail="child chd001 fails author lint: IPD-Q501 unmatched",
                remedy="fix the child's named lint finding",
                questions=(),
            )
            r_fallback = readiness.ReviewReadiness(
                applies=True,
                ready=False,
                findings=(f_fallback,),
                id6="orc001",
                setid="tstset",
            )
            rendered_fb = readiness.render_human(r_fallback)
            self.assertIn(
                "child chd001 fails author lint: IPD-Q501 unmatched", rendered_fb
            )

    def test_term_styling_lifecycle_and_plain_escapes(self):
        from agent_workflows.term import Term, resolve_lifecycle

        f = readiness.Finding(
            code=readiness.CODE_CHILD_STATUS,
            subject="62pkkg",
            detail="child 62pkkg has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)",
            remedy="bring the child to `to-review` with `aw ipd set to-review 62pkkg`",
        )
        r = readiness.ReviewReadiness(
            applies=True,
            ready=False,
            findings=(f,),
            id6="itamry",
            setid="setfoo",
        )

        # Plain text with term=None
        plain_out = readiness.render_human(r, target_status="approved", term=None)
        self.assertNotIn("\x1b", plain_out)

        # Plain text with Term(color=False)
        nocolor_term = Term(color=False)
        nocolor_out = readiness.render_human(
            r, target_status="approved", term=nocolor_term
        )
        self.assertNotIn("\x1b", nocolor_out)

        # Styled with Term(color=True)
        color_term = Term(color=True)
        color_out = readiness.render_human(r, target_status="approved", term=color_term)
        self.assertIn("\x1b", color_out)

        # Target status styled via Term.style_lifecycle_text
        expected_target_styled = color_term.style_lifecycle_text(
            "approved", resolve_lifecycle("plans", "approved")
        )
        self.assertIn(expected_target_styled, color_out)

        # Child id6 formatted via Term.format_lifecycle_compact
        expected_child_compact = color_term.format_lifecycle_compact(
            "62pkkg", resolve_lifecycle("plans", "draft"), word=True
        )
        self.assertIn(expected_child_compact, color_out)

        # Setid styled with bold only
        expected_setid = color_term.colorize("setfoo", "bold")
        self.assertIn(expected_setid, color_out)


if __name__ == "__main__":
    unittest.main()

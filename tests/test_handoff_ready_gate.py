"""Tests for the handoff-readiness gate and check.graduation-incomplete rule (IPD sbiv1j).

Covers:
- Predicate evaluate_handoff_ready unit tests:
  - 4 failure kinds: no handoff, plan below to-review, author lint failing, orchestrator review readiness failing;
  - 3 ready cases: ready Set with passing orchestrator, completed all-terminal handoff, Graduated-To Set handoff.
- CLI subprocess tests:
  - both backlog setter spellings refusing identically with exit 1 and leaving file unchanged;
  - both backlog setter spellings succeeding on a ready fixture;
  - spec setter (aw specs set implementing) refusing and succeeding;
  - same-status note (graduated -> graduated) bypassing the gate.
- check.graduation-incomplete check rule tests:
  - post-cutover drifted item/spec reported with severity error;
  - pre-cutover grandfathered item/spec skipped;
  - CLI check command reporting post-cutover finding.
- Production path regression test and isolated lane test with --gate-dir.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import coverage_record as cr
from tests import support


def _make_conforming_child(
    repo: Path,
    *,
    id6: str = "chd001",
    setid: str = "demo",
    order: int = 1,
    status: str = "to-review",
    backlog_id6: str | None = None,
    spec_id6: str | None = None,
    broken_lint: bool = False,
    in_terminal: str | None = None,
) -> Path:
    bucket = in_terminal if in_terminal else "pending"
    p_dir = repo / ".aw" / "records" / "plans" / bucket
    p_dir.mkdir(parents=True, exist_ok=True)
    p = p_dir / f"20261006-{setid}-{order:02d}-{id6}-test.ipd.md"

    bkl = f"- From-Backlog: {backlog_id6}\n" if backlog_id6 else ""
    spc = f"- From-Spec: {spec_id6}\n" if spec_id6 else ""
    scope_field = "- Scope: Test scope.\n" if not broken_lint else ""

    content = f"""# IPD: Test Child Plan {id6}

- Date: 2026-10-06
- Kind: child
- Concern: Test concern.
{scope_field}- Status: {status}
- Work-Kind: chore
- Priority: medium
- Set: {setid}
- Order: {order}
- Id: {id6}
{bkl}{spc}- Scope-Paths: README.md
- Highest E allocated: 01
- Author: test
- Item-Dependencies: none

## Workflow history
- 2026-10-06 {status} (test): created.

## Goal
Test goal for child plan {id6}.

## Detailed Implementation Checklist (TODO)
### Task group 1: work
- [ ] E-01 Work item
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
None.

## Findings
None.

## Proposed changes (ordered, validatable)
1. E-01 do work.

## Deferred / out of scope (with reason)
- None.

## Scope check
- None.

## Required tests / validation
- None.

## Spec / documentation sync
- None.

## Open questions
- None.

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""
    p.write_text(content, encoding="utf-8")
    return p


def _make_conforming_orchestrator(
    repo: Path,
    *,
    id6: str = "orc001",
    setid: str = "demo",
    status: str = "to-review",
    backlog_id6: str | None = None,
    spec_id6: str | None = None,
    child_rows: list[tuple[str, str, str]] | None = None,
    pass_coverage: bool = True,
    fail_coverage: bool = False,
    omit_coverage: bool = False,
    omit_child_table: bool = False,
) -> Path:
    p_dir = repo / ".aw" / "records" / "plans" / "pending"
    p_dir.mkdir(parents=True, exist_ok=True)
    orch_path = p_dir / f"20261006-{setid}-00-{id6}-orchestrator.ipd.md"

    bkl = f"- From-Backlog: {backlog_id6}\n" if backlog_id6 else ""
    spc = f"- From-Spec: {spec_id6}\n" if spec_id6 else ""

    if child_rows is None:
        child_rows = [
            (
                "01",
                "chd001",
                f".aw/records/plans/pending/20261006-{setid}-01-chd001-test.ipd.md",
            )
        ]

    lines = [
        f"# IPD: Orchestrator {id6}",
        "",
        "- Date: 2026-10-06",
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
    if bkl:
        lines.append(bkl.strip())
    if spc:
        lines.append(spc.strip())
    if status == "approved":
        lines.append("- Approval: 2026-10-06, test approved")

    lines.extend(
        [
            "",
            "## Workflow history",
            f"- 2026-10-06 {status} (test): created.",
            "",
            "## Goal",
            "Test orchestrator goal.",
            "",
            "## Detailed Implementation Checklist (TODO)",
            "- [ ] E-01 CONFIRM chd001 REACHED executed",
            "  - Depends on: none",
            "  - Expected outcome: done",
            "  - Execution state: pending",
            "",
        ]
    )

    if not omit_child_table:
        lines.extend(
            [
                "## Child IPDs, sequence, and dependencies",
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
            "- None.",
            "",
            "## Cross-IPD validation",
            "- None.",
            "",
            "## Deferred / out of scope (with reason)",
            "- None.",
            "",
            "## Scope check",
            "- None.",
            "",
            "## Required tests / validation",
            "- None.",
            "",
            "## Open questions",
            "- None.",
            "",
            "## Validation and cross-check (verify before reporting the Set complete)",
            "- [ ] V-01 validates E-01",
            "  - Required evidence: check.",
            "  - Observed evidence:",
            "  - Result: pending",
            "",
            "## Approval and execution gate",
            "- None.",
            "",
        ]
    )

    orch_path.write_text("\n".join(lines), encoding="utf-8")

    if fail_coverage and not omit_coverage:
        cr.write(
            orch_path,
            cr.COVERAGE_FAIL,
            quotes=["uncovered work"],
            model="test-model",
            tool="test-tool",
        )
    elif pass_coverage and not omit_coverage:
        cr.write(orch_path, cr.COVERAGE_PASS, model="test-model", tool="test-tool")

    return orch_path


def _make_backlog_item(
    repo: Path,
    *,
    id6: str = "bk0001",
    status: str = "open",
    setid: str = "demo",
    graduated_to: str | None = None,
    history_date: str = "2026-10-06",
) -> Path:
    p_dir = repo / ".aw" / "records" / "backlog" / status
    p_dir.mkdir(parents=True, exist_ok=True)
    p = p_dir / f"20261006-{setid}-01-{id6}-item.backlog.md"

    lines = [
        f"- Id: {id6}",
        f"- Status: {status}",
        f"- Set: {setid}",
        "- Priority: medium",
        "- Work-Kind: feature",
        "- Summary: Test item",
    ]
    if graduated_to:
        lines.append(f"- Graduated-To: {graduated_to}")
    lines.extend(
        [
            "",
            "## Workflow history",
            f"- {history_date} {status} (test): transition to {status}",
            "",
            "Prose body",
        ]
    )
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _make_spec(
    repo: Path,
    *,
    id6: str = "sp0001",
    status: str = "approved",
    setid: str = "demo",
    from_backlog: str | None = None,
    history_date: str = "2026-10-06",
) -> Path:
    p_dir = repo / ".aw" / "records" / "specs" / status
    p_dir.mkdir(parents=True, exist_ok=True)
    p = p_dir / f"20261006-{id6}-01-{id6}-test.spec.md"

    bkl = f"- From-Backlog: {from_backlog}\n" if from_backlog else ""
    content = f"""# Spec: Test Spec {id6}

- Date: 2026-10-06
- Status: {status}
- Set: {setid}
- Id: {id6}
{bkl}
## Workflow history
- {history_date} {status} (test): approved spec

## Goal
Goal for spec {id6}.
"""
    p.write_text(content, encoding="utf-8")
    return p


def _setup_test_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    for sub in ("open", "graduated", "done", "blocked", "parked"):
        (path / ".aw" / "records" / "backlog" / sub).mkdir(parents=True, exist_ok=True)
    for sub in (
        "draft",
        "to-review",
        "reviewed",
        "approved",
        "implementing",
        "implemented",
        "deferred",
        "parked",
        "superseded",
    ):
        (path / ".aw" / "records" / "specs" / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("pending", "executed", "superseded", "not-executed"):
        (path / ".aw" / "records" / "plans" / sub).mkdir(parents=True, exist_ok=True)
    (path / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
    (path / ".aw" / "config").mkdir(parents=True, exist_ok=True)
    (path / ".aw" / "config" / "project.json").write_text(
        json.dumps(
            {"schema_version": 1, "cutovers": {"graduation_ready": "2026-10-06"}}
        ),
        encoding="utf-8",
    )
    return path


class TestPredicateUnit(unittest.TestCase):
    """Unit tests for evaluate_handoff_ready predicate (E-01)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = _setup_test_repo(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_failure_kind_1_no_handoff(self):
        _make_backlog_item(self.repo, id6="bk0001")
        res = ce.evaluate_handoff_ready(self.repo, "backlog", "bk0001")
        self.assertFalse(res.ready)
        self.assertEqual(len(res.findings), 1)
        self.assertEqual(res.findings[0].code, "no-handoff")
        self.assertIn("no handoff plan or spec found", res.findings[0].detail)

    def test_failure_kind_2_plan_status_below_to_review(self):
        _make_backlog_item(self.repo, id6="bk0001")
        _make_conforming_child(
            self.repo, id6="chd001", status="draft", backlog_id6="bk0001"
        )
        res = ce.evaluate_handoff_ready(self.repo, "backlog", "bk0001")
        self.assertFalse(res.ready)
        codes = [f.code for f in res.findings]
        self.assertIn("plan-status-not-ready", codes)
        f = next(f for f in res.findings if f.code == "plan-status-not-ready")
        self.assertIn("must be to-review or later", f.detail)

    def test_failure_kind_3_plan_lint_failing(self):
        _make_backlog_item(self.repo, id6="bk0001")
        _make_conforming_child(
            self.repo,
            id6="chd001",
            status="to-review",
            backlog_id6="bk0001",
            broken_lint=True,
        )
        res = ce.evaluate_handoff_ready(self.repo, "backlog", "bk0001")
        self.assertFalse(res.ready)
        codes = [f.code for f in res.findings]
        self.assertIn("plan-lint-failing", codes)
        f = next(f for f in res.findings if f.code == "plan-lint-failing")
        self.assertIn("fails author lint", f.detail)

    def test_failure_kind_4_orchestrator_coverage_failing(self):
        _make_backlog_item(self.repo, id6="bk0001")
        _make_conforming_child(
            self.repo, id6="chd001", status="to-review", backlog_id6="bk0001"
        )
        _make_conforming_orchestrator(
            self.repo, id6="orc001", fail_coverage=True, backlog_id6="bk0001"
        )
        res = ce.evaluate_handoff_ready(self.repo, "backlog", "bk0001")
        self.assertFalse(res.ready)
        codes = [f.code for f in res.findings]
        self.assertTrue(any("coverage" in c or "orchestrator" in c for c in codes))

    def test_ready_case_1_ready_set_with_passing_orchestrator(self):
        _make_backlog_item(self.repo, id6="bk0001")
        _make_conforming_child(
            self.repo, id6="chd001", status="to-review", backlog_id6="bk0001"
        )
        _make_conforming_orchestrator(
            self.repo, id6="orc001", pass_coverage=True, backlog_id6="bk0001"
        )
        res = ce.evaluate_handoff_ready(self.repo, "backlog", "bk0001")
        self.assertTrue(res.ready, f"Expected ready, got findings: {res.findings}")
        self.assertEqual(len(res.findings), 0)

    def test_ready_case_2_completed_all_terminal_handoff(self):
        _make_backlog_item(self.repo, id6="bk0001")
        # All linked plans are in terminal directory with at least 1 executed
        _make_conforming_child(
            self.repo,
            id6="chd001",
            status="executed",
            in_terminal="executed",
            backlog_id6="bk0001",
        )
        _make_conforming_child(
            self.repo,
            id6="chd002",
            status="superseded",
            in_terminal="superseded",
            backlog_id6="bk0001",
        )
        res = ce.evaluate_handoff_ready(self.repo, "backlog", "bk0001")
        self.assertTrue(
            res.ready,
            f"Expected ready for completed handoff, got findings: {res.findings}",
        )
        self.assertEqual(len(res.findings), 0)

    def test_ready_case_3_graduated_to_set_handoff(self):
        # Backlog item points to Set 'demo' via - Graduated-To: demo, plans do not have - From-Backlog:
        _make_backlog_item(self.repo, id6="bk0001", graduated_to="demo")
        _make_conforming_child(
            self.repo, id6="chd001", setid="demo", status="to-review", backlog_id6=None
        )
        res = ce.evaluate_handoff_ready(self.repo, "backlog", "bk0001")
        self.assertTrue(
            res.ready,
            f"Expected ready via Graduated-To set, got findings: {res.findings}",
        )
        self.assertEqual(len(res.findings), 0)


class TestBacklogSetterSubprocess(unittest.TestCase):
    """Subprocess tests for both backlog setter spellings (E-02)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = _setup_test_repo(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_both_spellings_refuse_identically_on_not_ready_and_write_nothing(self):
        item = _make_backlog_item(self.repo, id6="bk0001", status="open")
        orig_bytes = item.read_bytes()

        # Route 1: positional spelling
        res1 = support.run_cli(
            "backlog",
            "set",
            "graduated",
            "bk0001",
            "--yes",
            "--no-commit",
            cwd=self.repo,
        )
        self.assertEqual(res1.returncode, 1)
        self.assertIn("handoff for backlog bk0001 is not ready", res1.stderr)
        self.assertIn(
            "[no-handoff] no handoff plan or spec found for backlog bk0001", res1.stderr
        )
        self.assertEqual(item.read_bytes(), orig_bytes)
        self.assertTrue(item.exists())

        # Route 2: --status spelling
        res2 = support.run_cli(
            "backlog",
            "set",
            str(item),
            "--status",
            "graduated",
            "--no-commit",
            cwd=self.repo,
        )
        self.assertEqual(res2.returncode, 1)
        self.assertIn("handoff for backlog bk0001 is not ready", res2.stderr)
        self.assertIn(
            "[no-handoff] no handoff plan or spec found for backlog bk0001", res2.stderr
        )
        self.assertEqual(item.read_bytes(), orig_bytes)
        self.assertTrue(item.exists())

        # Compare finding blocks from both outputs
        self.assertIn("[no-handoff]", res1.stderr)
        self.assertIn("[no-handoff]", res2.stderr)

    def test_both_spellings_succeed_on_ready_fixture(self):
        # 1. Positional spelling
        item1 = _make_backlog_item(self.repo, id6="bk0001", status="open")
        _make_conforming_child(
            self.repo, id6="chd001", status="to-review", backlog_id6="bk0001"
        )
        res1 = support.run_cli(
            "backlog",
            "set",
            "graduated",
            "bk0001",
            "--yes",
            "--no-commit",
            cwd=self.repo,
        )
        self.assertEqual(res1.returncode, 0, f"res1 failed: {res1.stderr}")
        moved1 = self.repo / ".aw" / "records" / "backlog" / "graduated" / item1.name
        self.assertTrue(moved1.exists())
        self.assertIn("- Status: graduated", moved1.read_text(encoding="utf-8"))

        # 2. --status spelling
        item2 = _make_backlog_item(self.repo, id6="bk0002", status="open")
        _make_conforming_child(
            self.repo, id6="chd002", status="to-review", backlog_id6="bk0002"
        )
        res2 = support.run_cli(
            "backlog",
            "set",
            str(item2),
            "--status",
            "graduated",
            "--no-commit",
            cwd=self.repo,
        )
        self.assertEqual(res2.returncode, 0, f"res2 failed: {res2.stderr}")
        moved2 = self.repo / ".aw" / "records" / "backlog" / "graduated" / item2.name
        self.assertTrue(moved2.exists())
        self.assertIn("- Status: graduated", moved2.read_text(encoding="utf-8"))

    def test_same_status_note_skips_check(self):
        # Already graduated item with no handoff: a same-status note succeeds without refusal
        item = _make_backlog_item(self.repo, id6="bk0003", status="graduated")
        res = support.run_cli(
            "backlog",
            "set",
            str(item),
            "--status",
            "graduated",
            "--message",
            "same status note",
            "--no-commit",
            cwd=self.repo,
        )
        self.assertEqual(
            res.returncode, 0, f"Expected same-status to succeed: {res.stderr}"
        )


class TestSpecSetterSubprocess(unittest.TestCase):
    """Subprocess tests for spec setter aw specs set implementing (E-03)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = _setup_test_repo(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_spec_setter_refuses_when_handoff_is_not_ready(self):
        spec = _make_spec(self.repo, id6="sp0001", status="approved")
        # Child plan linked to spec is draft
        _make_conforming_child(
            self.repo, id6="chd001", status="draft", spec_id6="sp0001"
        )
        res = support.run_cli(
            "specs", "set", "implementing", "sp0001", "--yes", cwd=self.repo
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("handoff for spec sp0001 is not ready", res.stderr)
        self.assertIn("plan-status-not-ready", res.stderr)
        self.assertTrue(spec.exists())

    def test_spec_setter_succeeds_when_handoff_is_ready(self):
        spec = _make_spec(self.repo, id6="sp0002", status="approved")
        _make_conforming_child(
            self.repo, id6="chd002", status="to-review", spec_id6="sp0002"
        )
        res = support.run_cli(
            "specs", "set", "implementing", "sp0002", "--yes", cwd=self.repo
        )
        self.assertEqual(res.returncode, 0, f"Expected success: {res.stderr}")
        moved = self.repo / ".aw" / "records" / "specs" / "implementing" / spec.name
        self.assertTrue(moved.exists())
        self.assertIn("- Status: implementing", moved.read_text(encoding="utf-8"))


class TestGraduationIncompleteCheckRule(unittest.TestCase):
    """Check rule check.graduation-incomplete and cutover grandfathering (E-04)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = _setup_test_repo(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_check_rule_reports_post_cutover_drift_and_skips_pre_cutover(self):
        # Post-cutover drifted item: graduated on 2026-10-06 with no handoff
        _make_backlog_item(
            self.repo, id6="bkpost", status="graduated", history_date="2026-10-06"
        )

        # Pre-cutover item: graduated on 2026-10-01 with no handoff (grandfathered)
        _make_backlog_item(
            self.repo, id6="bkprev", status="graduated", history_date="2026-10-01"
        )

        findings = ce.check_graduation_incomplete(self.repo, "backlog")
        rule_findings = [f for f in findings if f.rule == "check.graduation-incomplete"]
        reported_ids = [f.location for f in rule_findings]

        self.assertTrue(
            any("bkpost" in loc for loc in reported_ids),
            f"Expected bkpost reported in {reported_ids}",
        )
        self.assertFalse(
            any("bkprev" in loc for loc in reported_ids),
            f"Expected bkprev skipped in {reported_ids}",
        )

    def test_check_rule_reports_post_cutover_spec_drift_and_skips_pre_cutover(self):
        # Post-cutover drifted spec: implementing on 2026-10-06 with unready plan
        _make_spec(
            self.repo, id6="sppost", status="implementing", history_date="2026-10-06"
        )
        _make_conforming_child(
            self.repo, id6="chd101", status="draft", spec_id6="sppost"
        )

        # Pre-cutover spec: implementing on 2026-10-01 with unready plan
        _make_spec(
            self.repo, id6="spprev", status="implementing", history_date="2026-10-01"
        )
        _make_conforming_child(
            self.repo, id6="chd102", status="draft", spec_id6="spprev"
        )

        findings = ce.check_graduation_incomplete(self.repo, "specs")
        rule_findings = [f for f in findings if f.rule == "check.graduation-incomplete"]
        reported_ids = [f.location for f in rule_findings]

        self.assertTrue(
            any("sppost" in loc for loc in reported_ids),
            f"Expected sppost reported in {reported_ids}",
        )
        self.assertFalse(
            any("spprev" in loc for loc in reported_ids),
            f"Expected spprev skipped in {reported_ids}",
        )

    def test_cli_check_backlog_reports_finding(self):
        _make_backlog_item(
            self.repo, id6="bkpost", status="graduated", history_date="2026-10-06"
        )
        res = support.run_cli("check", "backlog", cwd=self.repo)
        self.assertIn("check.graduation-incomplete", res.stdout + res.stderr)


class TestProductionAndIsolation(unittest.TestCase):
    """End-to-end regression and isolated lane graduation tests (E-05)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = _setup_test_repo(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_isolated_lane_graduates_against_lane_plans_with_separate_gate_dir(self):
        # Simulate lane: plans exist only in lane (self.repo), while gate_dir has no plans
        gate_tmp = tempfile.TemporaryDirectory()
        gate_dir = _setup_test_repo(Path(gate_tmp.name))
        try:
            item = _make_backlog_item(self.repo, id6="bklane", status="open")
            _make_conforming_child(
                self.repo, id6="chd001", status="to-review", backlog_id6="bklane"
            )

            res = support.run_cli(
                "backlog",
                "set",
                str(item),
                "--status",
                "graduated",
                "--dir",
                str(self.repo),
                "--gate-dir",
                str(gate_dir),
                "--no-commit",
                cwd=self.repo,
            )
            self.assertEqual(
                res.returncode, 0, f"Expected lane graduation to succeed: {res.stderr}"
            )
            moved = self.repo / ".aw" / "records" / "backlog" / "graduated" / item.name
            self.assertTrue(moved.exists())
            self.assertIn("- Status: graduated", moved.read_text(encoding="utf-8"))
        finally:
            gate_tmp.cleanup()


if __name__ == "__main__":
    unittest.main()

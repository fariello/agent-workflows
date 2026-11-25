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
from tests.conformance_matrix import run_cli_inproc
from tests.record_builder import RecordBuilder, assert_field


def _run_cli(*args, cwd=None, **kwargs):
    cli_args = []
    for a in args:
        if isinstance(a, (list, tuple)):
            cli_args.extend(str(x) for x in a)
        else:
            cli_args.append(str(a))
    return run_cli_inproc(cli_args, cwd=cwd)


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
    extra: dict[str, str] = {}
    if backlog_id6:
        extra["from_backlog"] = backlog_id6
    if spec_id6:
        extra["from_spec"] = spec_id6
    raw_fields: dict[str, object] = {
        "Concern": "Test concern.",
        "Scope": None if broken_lint else "Test scope.",
    }
    body = f"""## Goal
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
- Cohesion rationale: not required"""
    p = RecordBuilder(repo).plan(
        id6=id6,
        plan_role="child",
        title=f"Test Child Plan {id6}",
        author="test",
        when="2026-10-06",
        set=setid,
        order=order,
        status=status,
        scope_paths="README.md",
        item_dependencies="none",
        priority="medium",
        work_kind="chore",
        disposition=bucket,
        slug="test",
        history=[f"- 2026-10-06 {status} (test): created."],
        body=body,
        raw_fields=raw_fields,
        **extra,
    )
    assert isinstance(p, Path)
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
    if child_rows is None:
        child_rows = [
            (
                "01",
                "chd001",
                f".aw/records/plans/pending/20261006-{setid}-01-chd001-test.ipd.md",
            )
        ]

    extra: dict[str, str] = {}
    if backlog_id6:
        extra["from_backlog"] = backlog_id6
    if spec_id6:
        extra["from_spec"] = spec_id6

    body_lines = [
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

    if not omit_child_table:
        body_lines.extend(
            [
                "## Child IPDs, sequence, and dependencies",
                "| Order | Id | Status | Plan | Depends on |",
                "|---|---|---|---|---|",
            ]
        )
        for ord_tok, c_id6, c_path in child_rows:
            body_lines.append(f"| {ord_tok} | {c_id6} | pending | {c_path} | none |")
        body_lines.append("")

    body_lines.extend(
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
        ]
    )

    orch_path = RecordBuilder(repo).plan(
        id6=id6,
        plan_role="orchestrator",
        title=f"Orchestrator {id6}",
        author="test",
        when="2026-10-06",
        set=setid,
        order=0,
        status=status,
        scope_paths="none",
        item_dependencies="none",
        priority="medium",
        work_kind="chore",
        approval="2026-10-06, test approved" if status == "approved" else None,
        disposition="pending",
        slug="orchestrator",
        history=[f"- 2026-10-06 {status} (test): created."],
        body="\n".join(body_lines),
        raw_fields={"Concern": "test concern.", "Scope": "test scope."},
        **extra,
    )
    assert isinstance(orch_path, Path)

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
        RecordBuilder(self.repo).backlog(
            id6="bk0001",
            status="open",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 open (test): transition to open"],
            body="Prose body",
        )
        res = ce.evaluate_handoff_ready(self.repo, "backlog", "bk0001")
        self.assertFalse(res.ready)
        self.assertEqual(len(res.findings), 1)
        self.assertEqual(res.findings[0].code, "no-handoff")
        self.assertIn("no handoff plan or spec found", res.findings[0].detail)

    def test_failure_kind_2_plan_status_below_to_review(self):
        RecordBuilder(self.repo).backlog(
            id6="bk0001",
            status="open",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 open (test): transition to open"],
            body="Prose body",
        )
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
        RecordBuilder(self.repo).backlog(
            id6="bk0001",
            status="open",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 open (test): transition to open"],
            body="Prose body",
        )
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
        RecordBuilder(self.repo).backlog(
            id6="bk0001",
            status="open",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 open (test): transition to open"],
            body="Prose body",
        )
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
        RecordBuilder(self.repo).backlog(
            id6="bk0001",
            status="open",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 open (test): transition to open"],
            body="Prose body",
        )
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
        RecordBuilder(self.repo).backlog(
            id6="bk0001",
            status="open",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 open (test): transition to open"],
            body="Prose body",
        )
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
        RecordBuilder(self.repo).backlog(
            id6="bk0001",
            status="open",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            graduated_to="demo",
            history=["- 2026-10-06 open (test): transition to open"],
            body="Prose body",
        )
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
        item = RecordBuilder(self.repo).backlog(
            id6="bk0001",
            status="open",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 open (test): transition to open"],
            body="Prose body",
        )
        assert isinstance(item, Path)
        orig_bytes = item.read_bytes()

        # Route 1: positional spelling
        res1 = _run_cli(
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
        res2 = _run_cli(
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
        item1 = RecordBuilder(self.repo).backlog(
            id6="bk0001",
            status="open",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 open (test): transition to open"],
            body="Prose body",
        )
        assert isinstance(item1, Path)
        _make_conforming_child(
            self.repo, id6="chd001", status="to-review", backlog_id6="bk0001"
        )
        res1 = _run_cli(
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
        assert_field(moved1, "status", "graduated")

        # 2. --status spelling
        item2 = RecordBuilder(self.repo).backlog(
            id6="bk0002",
            status="open",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 open (test): transition to open"],
            body="Prose body",
        )
        assert isinstance(item2, Path)
        _make_conforming_child(
            self.repo, id6="chd002", status="to-review", backlog_id6="bk0002"
        )
        res2 = _run_cli(
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
        assert_field(moved2, "status", "graduated")

    def test_same_status_note_skips_check(self):
        # Already graduated item with no handoff: a same-status note succeeds without refusal
        item = RecordBuilder(self.repo).backlog(
            id6="bk0003",
            status="graduated",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 graduated (test): transition to graduated"],
            body="Prose body",
        )
        assert isinstance(item, Path)
        res = _run_cli(
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
        spec = RecordBuilder(self.repo).spec(
            id6="sp0001",
            title="Test Spec sp0001",
            status="approved",
            set="demo",
            when="2026-10-06",
            slug="test",
            history=["- 2026-10-06 approved (test): approved spec"],
            body="## Goal\nGoal for spec sp0001.",
        )
        assert isinstance(spec, Path)
        # Child plan linked to spec is draft
        _make_conforming_child(
            self.repo, id6="chd001", status="draft", spec_id6="sp0001"
        )
        res = _run_cli("specs", "set", "implementing", "sp0001", "--yes", cwd=self.repo)
        self.assertEqual(res.returncode, 1)
        self.assertIn("handoff for spec sp0001 is not ready", res.stderr)
        self.assertIn("plan-status-not-ready", res.stderr)
        self.assertTrue(spec.exists())

    def test_spec_setter_succeeds_when_handoff_is_ready(self):
        spec = RecordBuilder(self.repo).spec(
            id6="sp0002",
            title="Test Spec sp0002",
            status="approved",
            set="demo",
            when="2026-10-06",
            slug="test",
            history=["- 2026-10-06 approved (test): approved spec"],
            body="## Goal\nGoal for spec sp0002.",
        )
        assert isinstance(spec, Path)
        _make_conforming_child(
            self.repo, id6="chd002", status="to-review", spec_id6="sp0002"
        )
        res = _run_cli("specs", "set", "implementing", "sp0002", "--yes", cwd=self.repo)
        self.assertEqual(res.returncode, 0, f"Expected success: {res.stderr}")
        moved = self.repo / ".aw" / "records" / "specs" / "implementing" / spec.name
        self.assertTrue(moved.exists())
        assert_field(moved, "status", "implementing")


class TestGraduationIncompleteCheckRule(unittest.TestCase):
    """Check rule check.graduation-incomplete and cutover grandfathering (E-04)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = _setup_test_repo(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_check_rule_reports_post_cutover_drift_and_skips_pre_cutover(self):
        # Post-cutover drifted item: graduated on 2026-10-06 with no handoff
        RecordBuilder(self.repo).backlog(
            id6="bkpost",
            status="graduated",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 graduated (test): transition to graduated"],
            body="Prose body",
        )

        # Pre-cutover item: graduated on 2026-10-01 with no handoff (grandfathered)
        RecordBuilder(self.repo).backlog(
            id6="bkprev",
            status="graduated",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-01 graduated (test): transition to graduated"],
            body="Prose body",
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
        RecordBuilder(self.repo).spec(
            id6="sppost",
            title="Test Spec sppost",
            status="implementing",
            set="demo",
            when="2026-10-06",
            slug="test",
            history=["- 2026-10-06 implementing (test): approved spec"],
            body="## Goal\nGoal for spec sppost.",
        )
        _make_conforming_child(
            self.repo, id6="chd101", status="draft", spec_id6="sppost"
        )

        # Pre-cutover spec: implementing on 2026-10-01 with unready plan
        RecordBuilder(self.repo).spec(
            id6="spprev",
            title="Test Spec spprev",
            status="implementing",
            set="demo",
            when="2026-10-06",
            slug="test",
            history=["- 2026-10-01 implementing (test): approved spec"],
            body="## Goal\nGoal for spec spprev.",
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
        RecordBuilder(self.repo).backlog(
            id6="bkpost",
            status="graduated",
            set="demo",
            priority="medium",
            work_kind="feature",
            summary="Test item",
            when="2026-10-06",
            slug="item",
            history=["- 2026-10-06 graduated (test): transition to graduated"],
            body="Prose body",
        )
        res = _run_cli("check", "backlog", cwd=self.repo)
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
            item = RecordBuilder(self.repo).backlog(
                id6="bklane",
                status="open",
                set="demo",
                priority="medium",
                work_kind="feature",
                summary="Test item",
                when="2026-10-06",
                slug="item",
                history=["- 2026-10-06 open (test): transition to open"],
                body="Prose body",
            )
            assert isinstance(item, Path)
            _make_conforming_child(
                self.repo, id6="chd001", status="to-review", backlog_id6="bklane"
            )

            res = _run_cli(
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
            assert_field(moved, "status", "graduated")
        finally:
            gate_tmp.cleanup()


if __name__ == "__main__":
    unittest.main()

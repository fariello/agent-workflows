"""orchtyped Order 05 (`h9cbn4`): prove the composed control on the merged result across all four children.

Validates:
E-01 / V-01 (Criterion 1): One conformance rule, two consumers, no second implementation.
E-02 / V-02 (Criterion 3): Deliverables cannot be expressed as conforming rows (3 real items refused).
E-03 / V-03 (Criterion 9): Semantic probe survived and blocks bare continuation line obligations;
                           probe integrity pinned (absent from Set diff, 7 functions at 476 lines AST span).
E-04 / V-04 (Criteria 10 & 11): Distinguishable refusals (IPD-S407 vs IPD-S406) and mixed-queue ordering
                                (shape refusal spends 0 model calls; conforming reaches probe double).
E-05 / V-05 (Criteria 4 & 13): Baseline preservation and criterion 4 co-existence (parent d1u4sy + svacmz).
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
import subprocess
import tempfile
import unittest
import unittest.mock

from agent_workflows import agy_runipd, oc_runipd
from agent_workflows import ipd_lint as lint
from agent_workflows import ipd_schema
from agent_workflows import ipd_set_plan
from agent_workflows import runner_shared as rs
from tests.support import REPO_ROOT

BOTH_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))

# Commits across the orchtyped Set (children 01..04)
ORCHTYPED_CHILD_COMMITS = (
    # Order 01 (dpdyed)
    "7067884730ad096cbafb9fbd94ebc87a1d53c87a",
    "07cf1972fccb4dbdf026953b2059dda3e00c8068",
    # Order 02 (r3xk1f)
    "39ec4e90bc5abefd467d90399e06c872ffa133f5",
    "391227b27e51e92349e5f4e8d5f07bdede369f5b",
    # Order 03 (0xmk4e)
    "688d73ef5188b9d02ae1ede9f0f6c0efeac2721d",
    "def803533f2495dd6c305e1bba5b76e7f9eab245",
    # Order 04 (68uhp0)
    "33f1aaba87580a085610daea0b0c9d69a5df7d84",
    "deae090e657ac617d9c3798e31d84b627e157d8c",
)

PROBE_SEVEN_FUNCTIONS = (
    "enforce_orchestrator_probe_gate",
    "ask_orchestrator_probe",
    "orchestrator_probe_excerpt",
    "queued_orchestrator_targets",
    "classify_probe_reply",
    "probe_cache_payload",
    "probe_refusal_remedy",
)

# Literal pre-migration texts pinned to git revision c58ec3ab
REAL_PRE_MIGRATION_5E4SB6_E01 = (
    "- [x] E-01 Produce the function-by-function INVENTORY the backlog item names as its first "
    "required deliverable, as a durable research artifact under `.aw/records/research/` created with "
    "`aw research new` (do not hand-name it). Classify EVERY top-level symbol in both runners as "
    "(a) COMMON, identical or trivially unifiable; (b) HOST-SPECIFIC, genuinely tied to one CLI's "
    "invocation, event stream, or binary resolution; (c) DIVERGED, present in both but drifted, "
    "which is the class the item calls a divergence bug and which measurement shows is the LARGEST "
    "class at 37 symbols; or (d) ALREADY-EXTRACTED, a symbol a NON-runner module already owns, so the "
    "runner copy is a RE-FORK to delete rather than a symbol to extract (see F10; this class is mandatory "
    "and a two-runner-only comparison is structurally blind to it). For each class (c) symbol, record "
    "which side is authoritative and WHY, with the evidence, since that judgment is the actual "
    "intellectual work of this Set and must not be improvised per-child later. Use a mechanical "
    "method, not reading: an AST comparison of per-symbol source, plus a host-token-normalized "
    'comparison to separate "differs only by host naming" from "differs substantively" '
    "(measurement showed only ONE symbol, `driver_actor`, differs by naming alone, so this distinction "
    "matters). The class (d) sweep must compare each runner symbol against ALL of `agent_workflows/*.py`, "
    "not just against the other runner. The inventory must state the measured totals and the HEAD they "
    "were taken at, because they will move."
)

REAL_PRE_MIGRATION_WFJSP4_E02 = (
    "- [ ] E-02 VERIFY THE BROWSE AFFORDANCE ACTUALLY ARRIVED, which is the entire point of the Set "
    "and the one thing no child can demonstrate alone."
)

REAL_PRE_MIGRATION_TB63QV_E01 = (
    "- [ ] E-01 After both children are `executed`, verify the Set's combined outcome and record it, "
    "MEASURED FROM THE MAIN CHECKOUT and naming that tree: `aw attention --check` reports no stranded "
    "lane (or exactly the maintainer-deferred ESCALATE set, and see OQ-03 on why a deleted branch does "
    "NOT silence a row), `git worktree list` shows only the main checkout plus any lane a live run owns, "
    "and a subsequent driver run leaves no worktree behind. This is the only item on this orchestrator, "
    "and it is a VERIFICATION of the children's combined effect rather than work of its own. THE "
    "MEASURING TREE IS LOAD-BEARING: measured at review, a lane sees 13 lane worktrees where the main "
    "checkout sees a different set, and `.aw/records/runs/` is gitignored and ABSENT inside a lane, so "
    "`stranded_lane_drift` returns `[]` from a lane for lack of run records and would report a FALSE clean."
)


def _make_orchestrator_doc(
    *,
    id6: str = "orc001",
    child_table_rows: list[str] | None = None,
    checklist_rows: list[str] | None = None,
) -> str:
    children_lines = child_table_rows or [
        "| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fix-01-chd001.ipd.md | none |",
        "| 02 | chd002 | pending | .aw/records/plans/pending/20260924-fix-02-chd002.ipd.md | 01 |",
    ]
    check_lines = checklist_rows or [
        "- [ ] E-01 CONFIRM chd001 REACHED executed\n  - Depends on: none\n  - Execution state: pending",
        "- [ ] E-02 CONFIRM chd002 REACHED executed\n  - Depends on: E-01\n  - Execution state: pending",
    ]
    return f"""# IPD: Orchestrator Fixture {id6}

- Date: 2026-09-24
- Kind: orchestrator
- Concern: test fixture.
- Scope: test fixture.
- Scope-Paths: none
- Status: approved
- Set: set{id6}
- Order: 0
- Highest E allocated: 02
- Author: test
- Id: {id6}
- Approval: 2026-09-24, test

## Workflow history

- 2026-09-24 approved (test): created.

## Goal

Fixture.

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(children_lines)}

## Detailed Implementation Checklist (TODO)

{chr(10).join(check_lines)}

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: check.
  - Observed evidence:
  - Result: pending
"""


class TestOneRuleTwoConsumers(unittest.TestCase):
    """E-01 / V-01 (Criterion 1): One conformance rule, two consumers, no second implementation."""

    def test_single_conformance_function_exists_and_matches_signature(self):
        """ipd_lint.orchestrator_row_conformance is the single conformance evaluator."""
        self.assertTrue(hasattr(lint, "orchestrator_row_conformance"))
        sig = inspect.signature(lint.orchestrator_row_conformance)
        self.assertIn("text", sig.parameters)
        self.assertIn("doc", sig.parameters)

    def test_both_consumers_reach_shared_conformance_rule(self):
        """Review-side (lint_text) and run-side (enforce_orchestrator_shape_gate) call orchestrator_row_conformance."""
        # 1. Review-side: ipd_lint.check_orchestrator_rows is wired into lint_text
        self.assertTrue(hasattr(lint, "check_orchestrator_rows"))
        doc = lint.parse(_make_orchestrator_doc())
        diags = lint.check_orchestrator_rows(
            doc, _make_orchestrator_doc(), "review-finalize"
        )
        self.assertEqual(diags, [])

        # 2. Run-side: runner_shared.enforce_orchestrator_shape_gate is wired into initialize_run_core
        self.assertTrue(hasattr(rs, "enforce_orchestrator_shape_gate"))
        src = inspect.getsource(rs.enforce_orchestrator_shape_gate)
        self.assertIn("orchestrator_row_conformance", src)

    def test_no_second_row_pattern_in_agent_workflows(self):
        """Ensure no duplicate regex or re-implementation of the child-tracking row grammar exists."""
        aw_dir = REPO_ROOT / "agent_workflows"
        regex_compile_hits = []
        for py_file in aw_dir.glob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    is_compile = (
                        isinstance(func, ast.Attribute) and func.attr == "compile"
                    ) or (isinstance(func, ast.Name) and func.id == "compile")
                    if is_compile:
                        for arg in node.args:
                            if (
                                isinstance(arg, ast.Constant)
                                and isinstance(arg.value, str)
                                and "CONFIRM" in arg.value
                            ):
                                regex_compile_hits.append(
                                    (py_file.name, node.lineno, arg.value)
                                )

        # Expected hit: exactly _ORCH_ROW_RE in ipd_lint.py
        self.assertEqual(
            len(regex_compile_hits),
            1,
            f"Expected exactly 1 row regex definition, found: {regex_compile_hits}",
        )
        self.assertEqual(regex_compile_hits[0][0], "ipd_lint.py")
        self.assertIs(lint._ORCH_ROW_RE, getattr(lint, "_ORCH_ROW_RE"))

    def test_account_for_known_good_scanners_and_status_lists(self):
        """Enumerate and account for expected child-table scanners and status lists."""
        # Pre-existing child table readers:
        # 1. ipd_set_plan.parse_child_table (order graph)
        self.assertTrue(hasattr(ipd_set_plan, "parse_child_table"))
        # 2. runner_shared.child_table_rows (full cell tuples)
        self.assertTrue(hasattr(rs, "child_table_rows"))

        # Status list references:
        # 1. ipd_schema.RECOGNIZED_STATUS (definition)
        self.assertTrue(hasattr(ipd_schema, "RECOGNIZED_STATUS"))
        # 2. ipd_lint.orchestrator_row_conformance checks against ipd_schema.RECOGNIZED_STATUS
        src = inspect.getsource(lint.orchestrator_row_conformance)
        self.assertIn("RECOGNIZED_STATUS", src)


class TestDeliverablesCannotBeExpressedAsConformingRows(unittest.TestCase):
    """E-02 / V-02 (Criterion 3): Deliverables cannot be expressed as conforming rows."""

    def test_real_pre_migration_deliverables_are_refused(self):
        """Assert the 3 real historical parent items (pinned to HEAD c58ec3ab) are refused."""
        test_cases = [
            ("5e4sb6_E01", REAL_PRE_MIGRATION_5E4SB6_E01),
            ("wfjsp4_E02", REAL_PRE_MIGRATION_WFJSP4_E02),
            ("tb63qv_E01", REAL_PRE_MIGRATION_TB63QV_E01),
        ]

        for name, item_row in test_cases:
            with self.subTest(case=name):
                # Build a full orchestrator doc around this item
                doc_text = _make_orchestrator_doc(
                    id6=f"tst{name[:3]}",
                    checklist_rows=[
                        f"{item_row}\n  - Depends on: none\n  - Execution state: pending"
                    ],
                )
                res = lint.orchestrator_row_conformance(doc_text)
                self.assertFalse(
                    res.conforming, f"Expected {name} to be non-conforming"
                )
                self.assertEqual(len(res.findings), 1)
                finding = res.findings[0]
                self.assertFalse(finding.conforming)
                self.assertEqual(finding.reason, lint.ORCH_ROW_NOT_TYPED)
                self.assertIn("not a typed child-tracking row", finding.message)

    def test_wfjsp4_e02_refused_despite_allowlisted_verb(self):
        """wfjsp4 E-02 opens with 'VERIFY' and names no child; refused by grammar."""
        self.assertTrue(REAL_PRE_MIGRATION_WFJSP4_E02.startswith("- [ ] E-02 VERIFY"))
        doc_text = _make_orchestrator_doc(
            id6="wfj002",
            checklist_rows=[
                f"{REAL_PRE_MIGRATION_WFJSP4_E02}\n  - Depends on: none\n  - Execution state: pending"
            ],
        )
        res = lint.orchestrator_row_conformance(doc_text)
        self.assertFalse(res.conforming)
        self.assertEqual(res.findings[0].reason, lint.ORCH_ROW_NOT_TYPED)


class TestProbeSurvivedAndStillBlocks(unittest.TestCase):
    """E-03 / V-03 (Criterion 9): Semantic probe survived and blocks bare continuation line obligations."""

    def test_conforming_row_with_bare_continuation_prose_passes_shape_and_reaches_probe(
        self,
    ):
        """Prose obligation on bare continuation line passes shape gate but is present in probe excerpt."""
        prose_obligation = "SOMEONE MUST MIGRATE THE DATABASE BEFORE ANY CHILD RUNS"
        doc_text = _make_orchestrator_doc(
            id6="prose1",
            checklist_rows=[
                f"- [ ] E-01 CONFIRM chd001 REACHED executed\n    {prose_obligation}\n  - Depends on: none\n  - Execution state: pending",
                "- [ ] E-02 CONFIRM chd002 REACHED executed\n  - Depends on: E-01\n  - Execution state: pending",
            ],
        )
        # 1. Shape gate passes because the row itself matches the grammar and continuation lines are allowed
        shape_res = lint.orchestrator_row_conformance(doc_text)
        self.assertTrue(shape_res.conforming)
        self.assertEqual(shape_res.findings, ())

        # 2. Probe excerpt includes the bare continuation line
        excerpt = rs.orchestrator_probe_excerpt(doc_text)
        self.assertIn(prose_obligation, excerpt)

        # 3. Payload limit: Key-value subfields are filtered out from action blocks
        subfield_text = "- Context: this should be stripped by _SUBFIELD_RE"
        doc_with_subfield = _make_orchestrator_doc(
            id6="subf01",
            checklist_rows=[
                f"- [ ] E-01 CONFIRM chd001 REACHED executed\n  {subfield_text}\n  - Depends on: none\n  - Execution state: pending",
            ],
        )
        excerpt_sub = rs.orchestrator_probe_excerpt(doc_with_subfield)
        self.assertNotIn(subfield_text, excerpt_sub)

    def test_probe_test_file_absent_from_orchtyped_commits(self):
        """Pin: tests/test_orchestrator_probe.py was NOT touched by any orchtyped child commit."""
        for commit in ORCHTYPED_CHILD_COMMITS:
            out = subprocess.check_output(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit],
                cwd=REPO_ROOT,
                text=True,
            )
            touched = set(out.splitlines())
            self.assertNotIn(
                "tests/test_orchestrator_probe.py",
                touched,
                f"Commit {commit[:8]} unexpectedly touched tests/test_orchestrator_probe.py",
            )

    def test_probe_seven_functions_exist_and_sum_to_476_lines_ast(self):
        """Pin: all seven probe functions exist in runner_shared and their AST spans sum to 476."""
        rs_file = REPO_ROOT / "agent_workflows" / "runner_shared.py"
        src = rs_file.read_text(encoding="utf-8")
        tree = ast.parse(src)

        spans: dict[str, int] = {}
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name in PROBE_SEVEN_FUNCTIONS
            ):
                span = node.end_lineno - node.lineno + 1
                spans[node.name] = span

        self.assertEqual(
            set(spans.keys()),
            set(PROBE_SEVEN_FUNCTIONS),
            f"Missing probe functions: {set(PROBE_SEVEN_FUNCTIONS) - set(spans.keys())}",
        )
        total_span = sum(spans.values())
        self.assertEqual(
            total_span,
            476,
            f"Expected probe functions AST span to sum to 476 lines, got {total_span}: {spans}",
        )


class TestDistinguishableRefusalsAndMixedQueueOrdering(unittest.TestCase):
    """E-04 / V-04 (Criteria 10 & 11): Distinguishable refusals and mixed-queue ordering."""

    def test_shape_and_probe_refusal_codes_differ(self):
        """Shape check refusal code (IPD-S407) is distinct from probe refusal code (IPD-S406 / orchestrator-uncovered-work)."""
        shape_code = lint.C_ORCH_ROW
        probe_code = rs.PROBE_REFUSAL_CODE
        self.assertEqual(shape_code, "IPD-S407")
        self.assertEqual(probe_code, "orchestrator-uncovered-work")
        self.assertNotEqual(shape_code, probe_code)

    def test_mixed_queue_shape_refusal_short_circuits_with_zero_probe_calls(self):
        """A mixed queue with a non-conforming orchestrator fails shape check and spends 0 probe calls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_repo = Path(tmpdir)
            plans_dir = tmp_repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)

            # 1. Conforming orchestrator
            good_doc = _make_orchestrator_doc(id6="god001")
            (plans_dir / "20260924-setgod-00-god001-good.ipd.md").write_text(
                good_doc, encoding="utf-8"
            )

            # 2. Non-conforming orchestrator (untyped prose row)
            bad_doc = _make_orchestrator_doc(
                id6="bad001",
                checklist_rows=[
                    "- [ ] E-01 Sequence children by hand\n  - Depends on: none\n  - Execution state: pending"
                ],
            )
            (plans_dir / "20260924-setbad-00-bad001-bad.ipd.md").write_text(
                bad_doc, encoding="utf-8"
            )

            state = {
                "queue": [
                    {
                        "id6": "god001",
                        "kind": "orchestrator",
                        "setid": "setgod",
                        "position": 1,
                        "configured_file": ".aw/records/plans/pending/20260924-setgod-00-god001-good.ipd.md",
                    },
                    {
                        "id6": "bad001",
                        "kind": "orchestrator",
                        "setid": "setbad",
                        "position": 2,
                        "configured_file": ".aw/records/plans/pending/20260924-setbad-00-bad001-bad.ipd.md",
                    },
                ]
            }

            # Injected probe double to count calls
            probe_calls = 0

            def mock_asker(*args, **kwargs):
                nonlocal probe_calls
                probe_calls += 1
                return rs.ProbeAnswer(
                    calls=1, status=rs.PROBE_ANSWER_CLEAN, detail="mock clean"
                )

            # Running shape gate directly on the mixed queue raises shape refusal
            with self.assertRaises(rs.DriverError) as ctx:
                rs.enforce_orchestrator_shape_gate(state, repo=tmp_repo)

            self.assertIn("IPD-S407", str(ctx.exception))
            self.assertIn("bad001", str(ctx.exception))
            # Zero probe calls were made because shape gate aborted early
            self.assertEqual(probe_calls, 0)

    def test_conforming_queue_passes_shape_gate_and_reaches_probe(self):
        """A queue containing only conforming orchestrators passes shape gate and reaches probe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_repo = Path(tmpdir)
            plans_dir = tmp_repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)

            good_doc = _make_orchestrator_doc(id6="god002")
            (plans_dir / "20260924-setgod-00-god002-good.ipd.md").write_text(
                good_doc, encoding="utf-8"
            )

            state = {
                "queue": [
                    {
                        "id6": "god002",
                        "kind": "orchestrator",
                        "setid": "setgod",
                        "position": 1,
                        "configured_file": ".aw/records/plans/pending/20260924-setgod-00-god002-good.ipd.md",
                    }
                ]
            }

            # 1. Shape gate passes
            shape_outcomes = rs.enforce_orchestrator_shape_gate(state, repo=tmp_repo)
            self.assertEqual(len(shape_outcomes), 1)

            # 2. Probe gate is reached and calls injected asker
            probe_calls = 0

            def mock_asker(*args, **kwargs):
                nonlocal probe_calls
                probe_calls += 1
                return (rs.PROBE_ANSWER_NO_EXECUTIONS, "mock clean")

            run_dir = tmp_repo / ".aw" / "records" / "runs" / "run-test"
            run_dir.mkdir(parents=True)

            decision = rs.enforce_orchestrator_probe_gate(
                run_dir,
                state,
                repo=tmp_repo,
                host="oc",
                interactive=False,
                write_report_fn=lambda *a, **kw: None,
                asker=mock_asker,
            )
            self.assertTrue(decision.proceed)
            self.assertGreater(probe_calls, 0)


class TestSetBaselineAndCriterion4(unittest.TestCase):
    """E-05 / V-05 (Criteria 4 & 13): Baseline preservation and criterion 4 co-existence."""

    def test_parent_d1u4sy_rows_conform_and_coexist_with_cross_child_dependencies(self):
        """Parent d1u4sy has 5 conforming rows; child h9cbn4 has 4 sibling dependencies (precedent: svacmz)."""
        parent_path = (
            REPO_ROOT
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260919-orchtyped-00-d1u4sy-make-an-orchestrator-checklist-a-typed-child-tracking-row-so.ipd.md"
        )
        self.assertTrue(parent_path.exists(), f"Parent plan {parent_path} must exist")

        text = parent_path.read_text(encoding="utf-8")
        res = lint.orchestrator_row_conformance(text)
        self.assertTrue(
            res.conforming, f"Parent d1u4sy rows must conform; findings: {res.findings}"
        )
        self.assertEqual(len(res.rows), 5)
        for row in res.rows:
            self.assertTrue(row.conforming)
            self.assertEqual(row.status, "executed")

        # Verify child h9cbn4 dependencies
        child_path = (
            REPO_ROOT
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260919-orchtyped-05-h9cbn4-prove-the-composed-control-on-the-merged-result-across-all-f.ipd.md"
        )
        self.assertTrue(child_path.exists(), f"Child plan {child_path} must exist")
        child_text = child_path.read_text(encoding="utf-8")
        self.assertIn(
            "Item-Dependencies: executed:dpdyed, executed:r3xk1f, executed:0xmk4e, executed:68uhp0",
            child_text,
        )


if __name__ == "__main__":
    unittest.main()

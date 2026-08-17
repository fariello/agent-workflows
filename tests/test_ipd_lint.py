"""Tests for the deterministic IPD linter (Set ipd-structure, Order 02).

Covers the spec Section 16 acceptance cases: parser exclusions, both heading orders, metadata
invariants, watermark + dependency grammar, state combinations, checkpoints (incl. pre/post-
transition), OQ + size boundaries, legacy + quarantine dispositions, repository aggregation,
process-exit vs disposition semantics, --agent output, and dash-only-in-prose. Stdlib unittest.
"""

from __future__ import annotations

import argparse
import io
import re
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import ipd_lint as L
from agent_workflows import ipd_schema as S
from tests.support import CONFORMING_ORCHESTRATOR, REPO_ROOT, SOURCE_PLANS, SOURCE_DOCS

from tests.support import SOURCE_WORKFLOWS as _SWF

CHILD_TEMPLATE = _SWF / "assess" / "templates" / "ipd.md"
SPEC = SOURCE_DOCS / "specs" / "20260802-1904-01-ipd-structure-and-linting.spec.md"


# A minimal conforming CHILD IPD (author phase), built programmatically so tests can mutate it.
def _conforming_child() -> str:
    return """# IPD: sample (Set x, Order 1)

- Date: 2026-08-03
- Kind: child
- Concern: sample.
- Scope: sample.
- Status: to-review
- Set: x
- Order: 1
- Highest E allocated: 01
- Author: tester
- Id: abc123

## Workflow history

- 2026-08-03 to-review (tester): created.

## Goal

Sample goal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark performed only after doing it.

### Task group 1: t

- [ ] E-01 do a thing.
  - Depends on: none
  - Expected outcome: the thing exists.
  - Execution state: pending

## Project conventions discovered (Step 0)

- x

## Findings

- x

## Proposed changes (ordered, validatable)

- x

## Deferred / out of scope (with reason)

- x

## Scope check

- x

## Required tests / validation

- x

## Spec / documentation sync

- x

## Open questions

### OQ-01: a question

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: n/a

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence separately.

- [ ] V-01 validates E-01
  - Required evidence: the thing is present at path X.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Gate prose.
"""


def _executed_child(include_executed_history: bool = True) -> str:
    history = "- 2026-08-03 to-review (tester): created.\n"
    if include_executed_history:
        history += "- 2026-08-04 executed (tester): executed.\n"
    return (
        _conforming_child()
        .replace("- Status: to-review", "- Status: executed")
        .replace(
            "## Workflow history\n\n- 2026-08-03 to-review (tester): created.",
            f"## Workflow history\n\n{history.rstrip()}",
        )
        .replace(
            "- [ ] E-01 do a thing.\n  - Depends on: none\n  - Expected outcome: the thing exists.\n  - Execution state: pending",
            "- [x] E-01 do a thing.\n  - Depends on: none\n  - Expected outcome: the thing exists.\n  - Execution state: performed",
        )
        .replace(
            "- [ ] V-01 validates E-01\n  - Required evidence: the thing is present at path X.\n  - Observed evidence:\n  - Result: pending",
            "- [x] V-01 validates E-01\n  - Required evidence: the thing is present at path X.\n  - Observed evidence: verified at path X.\n  - Result: pass",
        )
    )


class ParserExclusionTests(unittest.TestCase):
    def test_fenced_example_not_parsed_as_structure(self):
        # The spec file contains fenced ## Goal / ## Detailed... examples; they must NOT be counted.
        doc = L.parse(SPEC.read_text(encoding="utf-8"))
        titles = [h.title for h in doc.h2]
        # The spec's OWN H2 are numbered ("1. Purpose ...") so the fenced "## Goal" example must
        # not appear as a real H2 heading.
        self.assertNotIn("Goal", titles)
        self.assertNotIn("Detailed Implementation Checklist (TODO)", titles)

    def test_yaml_front_matter_ignored(self):
        text = (
            "---\ntitle: x\n## Goal\n---\n# IPD: x\n\n- Kind: child\n\n## Goal\n\ny\n"
        )
        doc = L.parse(text)
        self.assertEqual([h.title for h in doc.h2], ["Goal"])


class ConformingTests(unittest.TestCase):
    def test_minimal_child_conforms_at_author(self):
        res = L.lint_text(_conforming_child(), checkpoint="author", directory="pending")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )
        self.assertTrue(res.passing)

    def test_conforming_orchestrator_fixture_conforms(self):
        p = CONFORMING_ORCHESTRATOR
        res = L.lint_file(p, checkpoint="author")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.render(str(p)) for d in res.diagnostics],
        )


class HeadingTests(unittest.TestCase):
    def test_missing_heading_flagged(self):
        text = _conforming_child().replace("## Scope check\n\n- x\n\n", "")
        res = L.lint_text(text, directory="pending")
        self.assertTrue(any(d.code == L.C_HEADING_MISSING for d in res.diagnostics))

    def test_execution_not_after_goal_flagged(self):
        # Move the execution checklist section far down by swapping Goal/Findings-region text.
        text = _conforming_child().replace(
            "## Goal\n\nSample goal.\n\n## Detailed Implementation Checklist (TODO)",
            "## Goal\n\nSample goal.\n\n## Findings\n\n- x\n\n## Detailed Implementation Checklist (TODO)",
        )
        res = L.lint_text(text, directory="pending")
        self.assertTrue(
            any(
                d.code in (L.C_EXEC_PLACEMENT, L.C_HEADING_ORDER, L.C_HEADING_DUP)
                for d in res.diagnostics
            )
        )

    def test_duplicate_heading_flagged(self):
        text = _conforming_child() + "\n## Goal\n\ndup\n"
        res = L.lint_text(text, directory="pending")
        self.assertTrue(any(d.code == L.C_HEADING_DUP for d in res.diagnostics))


class MetadataLintTests(unittest.TestCase):
    def test_unknown_field_flagged(self):
        text = _conforming_child().replace(
            "- Author: tester", "- Author: tester\n- Bogus: y"
        )
        res = L.lint_text(text, directory="pending")
        self.assertTrue(any(d.code == L.C_META_UNKNOWN for d in res.diagnostics))

    def test_orchestrator_order_nonzero_flagged(self):
        text = _conforming_child().replace("- Kind: child", "- Kind: orchestrator")
        # orchestrator with Order 1 is illegal; also headings won't match, but metadata error must appear.
        res = L.lint_text(text, directory="pending")
        self.assertTrue(any(d.message.startswith("Order") for d in res.diagnostics))

    def test_auto_approved_accepted_in_metadata(self):
        text = _conforming_child().replace(
            "- Status: to-review", "- Status: auto-approved"
        )
        res = L.lint_text(text, checkpoint="author", directory="pending")
        self.assertFalse(
            any(
                d.code in (L.C_META_FIELD, L.C_META_MISSING) and "Approval" in d.message
                for d in res.diagnostics
            )
        )

    def test_watermark_below_present_id_flagged(self):
        text = _conforming_child().replace(
            "- Highest E allocated: 01", "- Highest E allocated: 00"
        )
        res = L.lint_text(text, directory="pending")
        self.assertTrue(any(d.code == L.C_WATERMARK for d in res.diagnostics))


class IdBijectionTests(unittest.TestCase):
    def test_orphan_validation_flagged(self):
        text = _conforming_child().replace(
            "- [ ] V-01 validates E-01",
            "- [ ] V-01 validates E-01\n  - Required evidence: r\n  - Observed evidence:\n  - Result: pending\n- [ ] V-02 validates E-02",
        )
        res = L.lint_text(text, directory="pending")
        self.assertTrue(any(d.code == L.C_BIJECTION for d in res.diagnostics))

    def test_more_than_99_ids_ok(self):
        self.assertEqual(S.suffix_of("E-100"), 100)
        self.assertTrue(S.E_ID_STRICT.match("E-100"))

    def test_dependency_cycle_flagged(self):
        block = (
            "- [ ] E-01 a.\n  - Depends on: E-02\n  - Expected outcome: o.\n  - Execution state: pending\n"
            "- [ ] E-02 b.\n  - Depends on: E-01\n  - Expected outcome: o.\n  - Execution state: pending\n"
        )
        text = (
            _conforming_child()
            .replace(
                "- [ ] E-01 do a thing.\n  - Depends on: none\n  - Expected outcome: the thing exists.\n  - Execution state: pending\n",
                block,
            )
            .replace(
                "- [ ] V-01 validates E-01\n  - Required evidence: the thing is present at path X.\n  - Observed evidence:\n  - Result: pending",
                "- [ ] V-01 validates E-01\n  - Required evidence: r.\n  - Observed evidence:\n  - Result: pending\n"
                "- [ ] V-02 validates E-02\n  - Required evidence: r.\n  - Observed evidence:\n  - Result: pending",
            )
        )
        res = L.lint_text(text, directory="pending")
        self.assertTrue(
            any(d.code == L.C_DEPENDS and "cycle" in d.message for d in res.diagnostics)
        )


class StateMachineTests(unittest.TestCase):
    def test_checked_but_pending_execution_flagged(self):
        text = _conforming_child().replace(
            "- [ ] E-01 do a thing.", "- [x] E-01 do a thing."
        )
        res = L.lint_text(text, directory="pending")
        self.assertTrue(any(d.code == L.C_EXEC_STATE for d in res.diagnostics))

    def test_pass_without_evidence_flagged(self):
        text = _conforming_child().replace(
            "  - Observed evidence:\n  - Result: pending",
            "  - Observed evidence:\n  - Result: pass",
        )
        res = L.lint_text(text, directory="pending")
        self.assertTrue(
            any(d.code in (L.C_VALID_STATE, L.C_CROSS_STATE) for d in res.diagnostics)
        )

    def test_pre_transition_rejects_non_pass(self):
        # A pending plan at pre-transition: every E must be performed and V pass; here all pending.
        text = _conforming_child()
        res = L.lint_text(text, checkpoint="pre-transition", directory="pending")
        self.assertTrue(any(d.code == L.C_CHECKPOINT for d in res.diagnostics))


class CheckpointTests(unittest.TestCase):
    def test_pre_execution_blocking_question_rejected(self):
        text = (
            _conforming_child()
            .replace(
                "- Blocking: no\n- Status: open\n- Owner: none\n- Resolution or deferral rationale: n/a",
                "- Blocking: yes\n- Status: open\n- Owner: someone\n- Resolution or deferral rationale:",
            )
            .replace("- Status: to-review", "- Status: approved")
            .replace(
                "- Author: tester",
                "- Approval: approved by x 2026-08-03\n- Author: tester",
            )
        )
        res = L.lint_text(text, checkpoint="pre-execution", directory="pending")
        self.assertTrue(
            any(
                d.code == L.C_CHECKPOINT and "blocking" in d.message.lower()
                for d in res.diagnostics
            )
        )

    def test_pre_execution_status_incompatible(self):
        # to-review is not ready-to-execute -> checkpoint incompatible.
        res = L.lint_text(
            _conforming_child(), checkpoint="pre-execution", directory="pending"
        )
        self.assertTrue(any(d.code == L.C_CHECKPOINT for d in res.diagnostics))


class PostTransitionExecutedHistoryTests(unittest.TestCase):
    def test_post_transition_executed_with_history_passes(self):
        text = _executed_child(include_executed_history=True)
        res = L.lint_text(text, checkpoint="post-transition", directory="executed")
        self.assertEqual(res.disposition, S.DISPOSITION_CONFORMING)
        self.assertEqual(res.diagnostics, [])
        self.assertTrue(res.passing)

    def test_post_transition_executed_without_history_fails_s405(self):
        text = _executed_child(include_executed_history=False)
        res = L.lint_text(text, checkpoint="post-transition", directory="executed")
        self.assertEqual(res.disposition, S.DISPOSITION_ERROR)
        self.assertFalse(res.passing)
        codes = [d.code for d in res.diagnostics]
        self.assertIn(L.C_EXEC_HISTORY, codes)
        s405_diags = [d for d in res.diagnostics if d.code == L.C_EXEC_HISTORY]
        self.assertEqual(len(s405_diags), 1)
        self.assertIn(
            "must carry an 'executed' ## Workflow history entry", s405_diags[0].message
        )

    def test_legacy_grandfathered_terminal_plan_unaffected_under_default_evaluation(
        self,
    ):
        # Even without executed history, default evaluation on terminal dir returns legacy, not error
        text = _executed_child(include_executed_history=False)
        res = L.lint_text(text, checkpoint="author", directory="executed")
        self.assertEqual(res.disposition, S.DISPOSITION_LEGACY)
        self.assertEqual(res.diagnostics, [])

    def test_real_executed_plan_at_post_transition(self):
        # Verify against real executed plans in repo
        real_executed = sorted((SOURCE_PLANS / "executed").glob("*.md"))
        self.assertTrue(len(real_executed) > 0)
        # Select the latest conforming executed plan
        sample_plan = real_executed[-1]
        res = L.lint_file(sample_plan, checkpoint="post-transition")
        self.assertNotIn(L.C_EXEC_HISTORY, [d.code for d in res.diagnostics])


class OpenQuestionAndSizeTests(unittest.TestCase):
    def test_blocking_deferred_flagged(self):
        text = _conforming_child().replace(
            "- Blocking: no\n- Status: open",
            "- Blocking: yes\n- Status: deferred",
        )
        res = L.lint_text(text, directory="pending")
        self.assertTrue(any(d.code == L.C_OQ for d in res.diagnostics))

    def test_bad_size_assessment_flagged(self):
        text = _conforming_child().replace(
            "- Size assessment: standard", "- Size assessment: bogus"
        )
        res = L.lint_text(text, directory="pending")
        self.assertTrue(any(d.code == L.C_SIZE for d in res.diagnostics))


class DispositionTests(unittest.TestCase):
    def test_grandfathered_terminal_is_legacy(self):
        res = L.lint_text(_conforming_child(), directory="executed")
        self.assertEqual(res.disposition, S.DISPOSITION_LEGACY)
        self.assertFalse(res.passing)

    def test_quarantined_reported_not_passing(self):
        text = _conforming_child().replace(
            "- Author: tester",
            "- Quarantine: re-author later\n- Quarantine owner: maintainer\n- Quarantine follow-up: after the Set\n- Author: tester",
        )
        res = L.lint_text(text, directory="pending")
        self.assertEqual(res.disposition, S.DISPOSITION_QUARANTINED)
        self.assertFalse(res.passing)

    def test_conforming_is_the_only_pass(self):
        self.assertTrue(L.LintResult(S.DISPOSITION_CONFORMING, []).passing)
        self.assertFalse(L.LintResult(S.DISPOSITION_LEGACY, []).passing)
        self.assertFalse(L.LintResult(S.DISPOSITION_QUARANTINED, []).passing)
        self.assertFalse(L.LintResult(S.DISPOSITION_ERROR, []).passing)


class DashTests(unittest.TestCase):
    def test_dashes_no_longer_flagged_in_ipds(self):
        # The no-em/en-dash convention is a USER-FACING prose rule only
        # (GUIDING_PRINCIPLES P13). IPDs are internal/AI-facing artifacts, so the
        # linter must NOT flag em/en dashes and an IPD containing them still lints
        # conforming. The rule code IPD-D701 was retired.
        self.assertFalse(hasattr(L, "C_DASH"))
        prose = _conforming_child().replace(
            "Sample goal.", "Sample goal \u2014 with an em dash \u2013 and an en dash."
        )
        res = L.lint_text(prose, directory="pending")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            f"dashes should not affect linting; got {res.diagnostics}",
        )
        self.assertFalse(any("dash" in d.message.lower() for d in res.diagnostics))


class DiagnosticShapeTests(unittest.TestCase):
    def test_diagnostic_renders_with_code_and_location(self):
        d = L.Diagnostic(84, 1, L.C_ID_GRAMMAR, "duplicate execution id E-04")
        self.assertEqual(
            d.render("p.md"), "p.md:84:1 IPD-I301 duplicate execution id E-04"
        )


class ExitCodeTests(unittest.TestCase):
    def _run(self, **kw) -> int:
        ns = argparse.Namespace(
            phase="author", all=False, legacy=False, agent=False, path=None
        )
        for k, v in kw.items():
            setattr(ns, k, v)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = L.run_lint(ns)
        return rc

    def test_exit0_conforming(self):
        p = CONFORMING_ORCHESTRATOR
        self.assertEqual(self._run(path=str(p)), 0)

    def test_exit2_missing_file(self):
        self.assertEqual(self._run(path=str(REPO_ROOT / "does-not-exist.md")), 2)

    def test_exit2_unknown_phase(self):
        self.assertEqual(self._run(path="x.md", phase="bogus"), 2)

    def test_all_exits_1_when_errors_present(self):
        # Build a throwaway repo with one structurally-erroneous IPD; --all must exit 1.
        import tempfile

        root = Path(tempfile.mkdtemp())
        pend = root / ".agents" / "plans" / "pending"
        pend.mkdir(parents=True)
        (pend / "bad.md").write_text(
            "# IPD: bad\n\n- Kind: child\n\n## Goal\n\nno checklist here\n"
        )
        self.assertEqual(self._run(all=True, path=str(root)), 1)

    def test_all_exits_0_when_no_errors(self):
        # A repo whose only plan conforms -> --all exits 0.
        import tempfile
        from agent_workflows import ipd_authoring as A

        root = Path(tempfile.mkdtemp())
        pend = root / ".agents" / "plans" / "pending"
        pend.mkdir(parents=True)
        (pend / "ok.md").write_text(
            A.build_skeleton(
                kind="child",
                title="ok (Set x, Order 1)",
                author="t",
                when="2026-08-03",
                set_name="x",
                order=1,
            )
        )
        self.assertEqual(self._run(all=True, path=str(root)), 0)


class AgentOutputTests(unittest.TestCase):
    def test_agent_output_is_tab_separated_no_prose(self):
        p = CONFORMING_ORCHESTRATOR
        ns = argparse.Namespace(
            phase="author", all=False, legacy=False, agent=True, path=str(p)
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            L.run_lint(ns)
        out = buf.getvalue().strip()
        self.assertIn("\t", out)
        self.assertIn("DISPOSITION", out)


class NoDependencyTests(unittest.TestCase):
    def test_lint_module_is_stdlib_only(self):
        src = (REPO_ROOT / "agent_workflows" / "ipd_lint.py").read_text(
            encoding="utf-8"
        )
        for line in src.splitlines():
            m = re.match(r"^(?:from|import)\s+([a-zA-Z0-9_.]+)", line.strip())
            if not m:
                continue
            top = m.group(1).split(".")[0]
            self.assertIn(
                top,
                {
                    "__future__",
                    "argparse",
                    "re",
                    "pathlib",
                    "typing",
                    "agent_workflows",
                },
                "unexpected import: " + line,
            )


if __name__ == "__main__":
    unittest.main()

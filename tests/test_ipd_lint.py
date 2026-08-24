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
from tests.support import CONFORMING_ORCHESTRATOR, REPO_ROOT, SOURCE_DOCS, SOURCE_PLANS
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

    # --- ipdgates Order wezhxg: post-transition attribution lint (IPD-S406) ---
    def _executed_with(self, actor: str, msg: str, scope_paths: str) -> str:
        """An executed child whose newest history entry is `executed (<actor>): <msg>` and which
        declares a real (post-cutoff) or `grandfathered` (pre-cutoff) Scope-Paths."""
        text = _executed_child(include_executed_history=False)
        text = text.replace(
            "- Scope: sample.", f"- Scope: sample.\n- Scope-Paths: {scope_paths}", 1
        )
        # Insert the newest executed entry right after the Workflow history heading.
        text = text.replace(
            "## Workflow history\n\n- 2026-08-03 to-review (tester): created.",
            f"## Workflow history\n\n- 2026-08-05 executed ({actor}): {msg}\n"
            "- 2026-08-03 to-review (tester): created.",
            1,
        )
        return text

    def test_attribution_rejects_generic_actor_post_cutoff(self):
        text = self._executed_with(
            "aw set", "status set to executed", "agent_workflows/x.py"
        )
        res = L.lint_text(text, checkpoint="post-transition", directory="executed")
        self.assertIn(L.C_EXEC_ATTRIBUTION, [d.code for d in res.diagnostics])

    def test_attribution_rejects_empty_summary_post_cutoff(self):
        text = self._executed_with("opencode/model", "", "agent_workflows/x.py")
        res = L.lint_text(text, checkpoint="post-transition", directory="executed")
        self.assertIn(L.C_EXEC_ATTRIBUTION, [d.code for d in res.diagnostics])

    def test_attribution_accepts_real_actor_and_summary_post_cutoff(self):
        text = self._executed_with(
            "opencode/its_direct/pt3", "did the work", "agent_workflows/x.py"
        )
        res = L.lint_text(text, checkpoint="post-transition", directory="executed")
        self.assertNotIn(L.C_EXEC_ATTRIBUTION, [d.code for d in res.diagnostics])

    def test_attribution_does_not_reject_bare_tool_or_human_names(self):
        # Only the `aw set` machine default is generic; do NOT balloon to bare names.
        for actor in ("Antigravity", "maintainer", "codex/gpt-5"):
            text = self._executed_with(actor, "did it", "agent_workflows/x.py")
            res = L.lint_text(text, checkpoint="post-transition", directory="executed")
            self.assertNotIn(
                L.C_EXEC_ATTRIBUTION, [d.code for d in res.diagnostics], actor
            )

    def test_attribution_grandfathers_precutoff_generic_actor(self):
        # A grandfathered plan (Scope-Paths: grandfathered) with the legacy `aw set` actor is NOT
        # failed - forward-only, keyed on Order 02's cutoff marker.
        text = self._executed_with("aw set", "status set to executed", "grandfathered")
        res = L.lint_text(text, checkpoint="post-transition", directory="executed")
        self.assertNotIn(L.C_EXEC_ATTRIBUTION, [d.code for d in res.diagnostics])

    def test_attribution_grandfathers_when_no_scope_paths(self):
        # No Scope-Paths field at all (the existing executed tree) is also pre-cutoff.
        text = _executed_child(include_executed_history=False).replace(
            "## Workflow history\n\n- 2026-08-03 to-review (tester): created.",
            "## Workflow history\n\n- 2026-08-05 executed (aw set): status set to executed\n"
            "- 2026-08-03 to-review (tester): created.",
            1,
        )
        res = L.lint_text(text, checkpoint="post-transition", directory="executed")
        self.assertNotIn(L.C_EXEC_ATTRIBUTION, [d.code for d in res.diagnostics])

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
        # Use a grammar-conformant filename: aw ipd lint now name-checks plans (IPD-N001, awcheck-03).
        (pend / "20260803-x-01-aaa111-ok.ipd.md").write_text(
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
    def test_agent_output_is_agent_v1_jsonl_no_prose(self):
        import json

        p = CONFORMING_ORCHESTRATOR
        ns = argparse.Namespace(
            phase="author", all=False, legacy=False, agent=True, path=str(p)
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            L.run_lint(ns)
        out = buf.getvalue().strip()
        rec = json.loads(out)
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "ipd lint")
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)


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


class NameConformityTests(unittest.TestCase):
    """awcheck Order 03: aw ipd lint flags a nonconformant plan FILENAME (IPD-N001), respecting
    --legacy and the terminal-dir short-circuit."""

    def _res(self, disposition):
        # a minimal conforming result stand-in (no structural diagnostics)
        return L.LintResult(disposition=disposition, diagnostics=[])

    def test_bad_name_flagged(self):
        diags, disp = L._with_name_check(
            self._res(S.DISPOSITION_CONFORMING),
            Path(".aw/records/plans/pending/not-a-grammar.md"),
            legacy=False,
        )
        self.assertTrue(any(d.code == "IPD-N001" for d in diags))
        self.assertEqual(disp, S.DISPOSITION_ERROR)

    def test_good_name_unaffected(self):
        diags, disp = L._with_name_check(
            self._res(S.DISPOSITION_CONFORMING),
            Path(".aw/records/plans/pending/20260101-demo-01-aaa111-ok.ipd.md"),
            legacy=False,
        )
        self.assertFalse(any(d.code == "IPD-N001" for d in diags))
        self.assertEqual(disp, S.DISPOSITION_CONFORMING)

    def test_legacy_suppresses_recognized_legacy_name(self):
        diags, disp = L._with_name_check(
            self._res(S.DISPOSITION_CONFORMING),
            Path(".aw/records/plans/pending/2026-01-01-old-hyphenated.md"),
            legacy=True,
        )
        self.assertFalse(any(d.code == "IPD-N001" for d in diags))

    def test_non_plan_path_exempt(self):
        # a fixture / arbitrary path (no plans/ segment) is not name-checked.
        diags, disp = L._with_name_check(
            self._res(S.DISPOSITION_CONFORMING),
            Path("tests/fixtures/not-a-grammar.md"),
            legacy=False,
        )
        self.assertFalse(any(d.code == "IPD-N001" for d in diags))
        self.assertEqual(disp, S.DISPOSITION_CONFORMING)

    def test_terminal_shortcircuit_not_flagged(self):
        diags, disp = L._with_name_check(
            self._res(S.DISPOSITION_LEGACY),
            Path(".aw/records/plans/executed/bad-name.md"),
            legacy=False,
        )
        self.assertFalse(any(d.code == "IPD-N001" for d in diags))
        self.assertEqual(disp, S.DISPOSITION_LEGACY)


class DensityAdvisoryLintTests(unittest.TestCase):
    """Order 07: Per-E-item density heuristic surfacing in linter (spec Section 8.1)."""

    def _dense_child(self) -> str:
        # A conforming child IPD with a multi-concern E-item
        doc = _conforming_child()
        # Replace E-01 action with a multi-concern action
        return doc.replace(
            "- [ ] E-01 do a thing.",
            "- [ ] E-01 add an append-only tamper-evident ledger AND crash recovery AND a 12-class evidence validator",
        )

    def test_multi_concern_item_emits_advisory_without_error(self):
        text = self._dense_child()
        res = L.lint_text(text, checkpoint="author", directory="pending")
        # Conformance is NOT failed
        self.assertEqual(res.disposition, S.DISPOSITION_CONFORMING)
        self.assertTrue(res.passing)
        self.assertEqual(len(res.diagnostics), 0)
        # Advisory channel captures the finding
        self.assertEqual(len(res.advisories), 1)
        adv = res.advisories[0]
        self.assertEqual(adv.code, "IPD-Z602")
        self.assertEqual(adv.code, L.C_SIZE_DENSITY)
        self.assertIn("E-01", adv.message)
        self.assertIn("multi-concern", adv.message)
        self.assertGreater(adv.line, 0)

    def test_single_concern_plan_has_no_advisories(self):
        text = _conforming_child()
        res = L.lint_text(text, checkpoint="author", directory="pending")
        self.assertEqual(res.disposition, S.DISPOSITION_CONFORMING)
        self.assertTrue(res.passing)
        self.assertEqual(len(res.diagnostics), 0)
        self.assertEqual(len(res.advisories), 0)

    def test_advisory_does_not_gate_checkpoints(self):
        # A plan with an advisory passes pre-execution checkpoint if states/fields are valid
        text = self._dense_child().replace("Status: to-review", "Status: approved")
        text = text.replace(
            "- 2026-08-03 to-review (tester): created.",
            "- 2026-08-03 approved (tester): approved.",
        )
        # add approval field
        text = text.replace(
            "- Author: tester", "- Author: tester\n- Approval: tester 2026-08-03"
        )
        # Order oorry1: a ready-to-execute plan now needs a Scope-Paths value; declare a real
        # allowlist so this test isolates the DENSITY advisory (Z602) it is actually about.
        text = text.replace(
            "- Scope: sample.",
            "- Scope: sample.\n- Scope-Paths: agent_workflows/foo.py",
        )
        res = L.lint_text(text, checkpoint="pre-execution", directory="pending")
        self.assertEqual(res.disposition, S.DISPOSITION_CONFORMING)
        self.assertTrue(res.passing)
        self.assertEqual(len(res.diagnostics), 0)
        self.assertEqual(len(res.advisories), 1)

    def test_cli_agent_output_emits_advisory_record_with_clean_outcome(self):
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            plan_file = Path(td) / "20260822-test-01-abc123-dense.ipd.md"
            plan_file.write_text(self._dense_child(), encoding="utf-8")

            ns = argparse.Namespace(
                phase="author", all=False, legacy=False, agent=True, path=str(plan_file)
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = L.run_lint(ns)

            self.assertEqual(rc, 0)
            rec = json.loads(buf.getvalue().strip())
            self.assertEqual(rec["schema"], "aw.agent/v1")
            self.assertEqual(rec["cmd"], "ipd lint")
            self.assertEqual(rec["outcome"], "clean")
            self.assertEqual(rec["exit"], 0)
            self.assertEqual(rec["findings"], 1)
            self.assertTrue(
                any(d["rule"] == "IPD-Z602" for d in rec.get("diagnostics", []))
            )

    def test_cli_human_output_emits_advisory_line(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            plan_file = Path(td) / "20260822-test-01-abc123-dense.ipd.md"
            plan_file.write_text(self._dense_child(), encoding="utf-8")

            ns = argparse.Namespace(
                phase="author",
                all=False,
                legacy=False,
                agent=False,
                no_color=True,
                path=str(plan_file),
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = L.run_lint(ns)

            self.assertEqual(rc, 0)
            out = buf.getvalue()
            self.assertIn("advisory:", out)
            self.assertIn("IPD-Z602", out)
            self.assertIn("disposition: conforming", out)


def _with_scope_paths(text: str, value) -> str:
    """Return ``text`` with a Scope-Paths metadata line set to ``value`` (or removed if None)."""
    out = []
    for ln in text.splitlines():
        if ln.startswith("- Scope-Paths:"):
            continue  # drop any existing one first
        out.append(ln)
        if value is not None and ln.startswith("- Scope:"):
            out.append("- Scope-Paths: " + value)
    return "\n".join(out) + "\n"


def _approved(text: str) -> str:
    """Make a fixture ready-to-execute: Status approved + the required Approval field.

    Only the METADATA-block Status (before the first H2) is changed, so an OQ's own
    `- Status: open` line later in the document is left intact.
    """
    out = []
    in_meta = True
    for ln in text.splitlines():
        if ln.startswith("## "):
            in_meta = False
        if in_meta and ln.startswith("- Status:"):
            out.append("- Status: approved")
            continue
        out.append(ln)
        if in_meta and ln.startswith("- Author:"):
            out.append("- Approval: 2026-08-24, human: approved")
    return "\n".join(out) + "\n"


class ScopePathsCheckpointTests(unittest.TestCase):
    """Order oorry1: conditional Scope-Paths enforcement in the checkpoint layer.

    A fieldless plan is BLOCKED at the ready-to-execute gate; a `grandfathered`-marked plan is
    advisory-only (non-blocking); a real allowlist is grammar-validated; the `author` phase and
    terminal (grandfathered) records are unaffected.
    """

    def _scope_diags(self, res):
        return [d for d in res.diagnostics if d.code == L.C_SCOPE_PATHS]

    def _scope_advisories(self, res):
        return [d for d in res.advisories if d.code == L.C_SCOPE_PATHS]

    def test_author_phase_does_not_require_scope_paths(self):
        text = _with_scope_paths(_conforming_child(), None)  # no field at all
        res = L.lint_text(text, checkpoint="author", directory="pending")
        self.assertEqual(self._scope_diags(res), [])
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

    def test_pre_execution_fieldless_is_blocked(self):
        text = _approved(_with_scope_paths(_conforming_child(), None))
        res = L.lint_text(text, checkpoint="pre-execution", directory="pending")
        self.assertTrue(
            self._scope_diags(res), "fieldless plan must be blocked at pre-execution"
        )
        self.assertEqual(res.disposition, S.DISPOSITION_ERROR)

    def test_approved_status_fieldless_is_blocked_even_off_gate(self):
        # The requirement also fires by STATUS, so an approved plan cannot slip past a
        # non-pre-execution checkpoint without the field.
        text = _approved(_with_scope_paths(_conforming_child(), None))
        res = L.lint_text(text, checkpoint="review-finalize", directory="pending")
        self.assertTrue(self._scope_diags(res))

    def test_grandfathered_marker_is_advisory_not_blocking(self):
        text = _approved(_with_scope_paths(_conforming_child(), "grandfathered"))
        res = L.lint_text(text, checkpoint="pre-execution", directory="pending")
        self.assertEqual(self._scope_diags(res), [], "grandfathered must not block")
        self.assertTrue(
            self._scope_advisories(res), "grandfathered should emit an advisory"
        )
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

    def test_real_allowlist_is_grammar_validated(self):
        good = _approved(
            _with_scope_paths(
                _conforming_child(), "agent_workflows/foo.py, tests/test_foo.py"
            )
        )
        res = L.lint_text(good, checkpoint="pre-execution", directory="pending")
        self.assertEqual(
            self._scope_diags(res), [], [d.message for d in res.diagnostics]
        )
        self.assertEqual(res.disposition, S.DISPOSITION_CONFORMING)

        bad = _approved(_with_scope_paths(_conforming_child(), "/etc/passwd"))
        res_bad = L.lint_text(bad, checkpoint="pre-execution", directory="pending")
        self.assertTrue(self._scope_diags(res_bad), "malformed allowlist must block")
        self.assertEqual(res_bad.disposition, S.DISPOSITION_ERROR)

    def test_terminal_grandfathered_record_is_unaffected(self):
        # A terminal-dir plan with NO Scope-Paths short-circuits to legacy (never blocked),
        # proving the non-retroactivity guarantee for grandfathered terminal records.
        text = _with_scope_paths(_executed_child(), None)
        res = L.lint_text(text, checkpoint="pre-execution", directory="executed")
        self.assertEqual(res.disposition, S.DISPOSITION_LEGACY)
        self.assertEqual(self._scope_diags(res), [])

    def test_enforcement_lives_in_checkpoint_layer_not_metadata(self):
        # A fieldless plan produces NO metadata error (check_metadata), only a checkpoint-layer
        # diagnostic at the gate (check_scope_paths).
        fieldless = _with_scope_paths(_conforming_child(), None)
        doc = L.parse(fieldless)
        meta_diags = L.check_metadata(doc, "pending")
        self.assertEqual(
            [d for d in meta_diags if d.code == L.C_SCOPE_PATHS],
            [],
            "Scope-Paths must NOT be enforced in check_metadata",
        )
        approved_doc = L.parse(_approved(fieldless))
        block, _adv = L.check_scope_paths(approved_doc, "pre-execution", "pending")
        self.assertTrue(block, "check_scope_paths must enforce the field at the gate")


if __name__ == "__main__":
    unittest.main()

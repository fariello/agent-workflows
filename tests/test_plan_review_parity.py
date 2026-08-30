"""Parity + registration tests for the review workflows and the new ipd-lifecycle path (Order 05).

Ensures the single-file `plan-review` and the long-form `plan-review-long` carry the SAME structural
linter contract (same checkpoints, disposition, fail-closed exit codes, deterministic-vs-semantic
boundary), that required long-form dependencies exist, and that `ipd-lifecycle` is registered and
shimmed consistently. Stdlib unittest.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.support import REPO_ROOT

from tests.support import SOURCE_WORKFLOWS as WF

PLAN_REVIEW = WF / "plan-review" / "plan-review.md"
PRL_DIR = WF / "plan-review-long"
PRL_01 = PRL_DIR / "01-discover-and-snapshot.md"
PRL_03 = PRL_DIR / "03-resolve-and-finalize.md"
RUBRIC = PRL_DIR / "review-rubric.md"
PRL_02 = PRL_DIR / "02-review-and-revise.md"
ASSESS = WF / "assess" / "assess.md"
CHILD_TEMPLATE = WF / "assess" / "templates" / "ipd.md"
ORCH_TEMPLATE = WF / "assess" / "templates" / "orchestrator-ipd.md"
REPORT_TEMPLATE = PRL_DIR / "report-template.md"
LIFECYCLE = WF / "ipd-lifecycle" / "ipd-lifecycle.md"
LIFECYCLE_README = WF / "ipd-lifecycle" / "README.md"
INDEX = WF / "index.md"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class ReviewPreflightParityTests(unittest.TestCase):
    def test_author_preflight_in_both_variants(self):
        cmd = "aw ipd lint --phase author"
        self.assertIn(
            cmd, _read(PLAN_REVIEW), "single-file plan-review missing author preflight"
        )
        self.assertIn(cmd, _read(PRL_01), "long-form step 01 missing author preflight")

    def test_review_finalize_preflight_in_both_variants(self):
        cmd = "aw ipd lint --phase review-finalize"
        self.assertIn(
            cmd,
            _read(PLAN_REVIEW),
            "single-file plan-review missing review-finalize preflight",
        )
        self.assertIn(
            cmd, _read(PRL_03), "long-form step 03 missing review-finalize preflight"
        )

    def test_both_variants_state_conforming_gate_and_failclosed(self):
        for path in (PLAN_REVIEW, PRL_01, PRL_03, RUBRIC):
            t = _read(path)
            if "aw ipd lint" not in t:
                continue
            tl = t.lower()
            self.assertIn(
                "conforming",
                tl,
                "{0} must require a conforming disposition".format(path.name),
            )
            self.assertIn(
                "exit `1`", tl, "{0} must state exit-1 handling".format(path.name)
            )
            self.assertIn(
                "exit `2`", tl, "{0} must state exit-2 handling".format(path.name)
            )

    def test_deterministic_vs_semantic_boundary_stated(self):
        for path in (PLAN_REVIEW, RUBRIC):
            t = _read(path).lower()
            self.assertIn("structure", t)
            self.assertIn("semantic", t)

    def test_invoke_not_paraphrase(self):
        # The workflows must INVOKE the linter, not restate its checks.
        self.assertIn("do not paraphrase", _read(PLAN_REVIEW).lower())


class LongFormDependencyTests(unittest.TestCase):
    def test_required_long_form_files_exist(self):
        for p in (PRL_01, PRL_03, RUBRIC, REPORT_TEMPLATE):
            self.assertTrue(
                p.is_file(), "missing required long-form dependency: {0}".format(p)
            )

    def test_report_template_referenced(self):
        # 03-resolve-and-finalize references the report template; the dependency must be present.
        self.assertTrue(REPORT_TEMPLATE.is_file())


class IpdLifecycleRegistrationTests(unittest.TestCase):
    def test_lifecycle_files_exist(self):
        self.assertTrue(LIFECYCLE.is_file())
        self.assertTrue(LIFECYCLE_README.is_file())

    def test_lifecycle_registered_in_index(self):
        t = _read(INDEX)
        self.assertIn("| ipd-lifecycle |", t)
        # Post-.aw/-migration the shipped bundle is under .aw/system/workflows/ (IPD awretrofit
        # Order 02); the index invocation column must reference the real installed path.
        self.assertIn(".aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md", t)

    def test_lifecycle_shims_exist_both_hosts(self):
        for host in (".opencode", ".claude"):
            shim = REPO_ROOT / host / "commands" / "ipd-lifecycle.md"
            self.assertTrue(shim.is_file(), "missing {0} shim".format(host))
            # Shims reference the installed bundle path; post-migration that is .aw/system/workflows/
            # (regenerated in Order 10). Legacy .agents/workflows/ no longer appears.
            self.assertIn(
                ".aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md", _read(shim)
            )

    def test_lifecycle_names_all_three_checkpoints(self):
        t = _read(LIFECYCLE)
        for phase in ("pre-execution", "pre-transition", "post-transition"):
            self.assertIn("aw ipd lint --phase {0}".format(phase), t)

    def test_lifecycle_states_failclosed_and_recovery(self):
        t = _read(LIFECYCLE)
        tl = t.lower()
        self.assertIn("exit `1`", tl)
        self.assertIn("exit `2`", tl)
        self.assertIn("hard stop", tl)
        # transition is a post-gate transaction, not a checklist item
        self.assertIn("POST-gate", t) if "POST-gate" in t else self.assertIn(
            "post-gate", t.lower()
        )
        # pre/post-commit recovery language present
        self.assertIn("BEFORE the lifecycle commit", t)
        self.assertIn("AFTER the lifecycle commit", t)


class DriftGuardTests(unittest.TestCase):
    def test_deliberate_desync_would_fail(self):
        # Sanity: the parity assertions are content-based, so removing the preflight line from a
        # copy is detectable. We assert the marker exists in the real file (the inverse of drift).
        self.assertIn("aw ipd lint --phase author", _read(PRL_01))


class RightSizingRubricParityTests(unittest.TestCase):
    def test_right_sizing_rubric_in_plan_review_and_rubric(self):
        for path in (PLAN_REVIEW, RUBRIC):
            t = _read(path)
            # Conceptual density vs count lint
            self.assertIn(
                "conceptual density",
                t.lower(),
                f"{path.name} must mention conceptual density",
            )
            self.assertIn(
                "one concern",
                t.lower(),
                f"{path.name} must require one concern per E-item",
            )
            self.assertIn(
                "one focused pass",
                t.lower(),
                f"{path.name} must require execution in one focused pass",
            )

            # Diagnostic questions (a), (b), (c), (d)
            self.assertIn(
                "multiple distinct deliverables",
                t,
                f"{path.name} missing diagnostic (a) distinct deliverables",
            )
            self.assertIn(
                "multiple independent test-surfaces",
                t,
                f"{path.name} missing diagnostic (b) test surfaces",
            )
            self.assertIn(
                "independent passes",
                t,
                f"{path.name} missing diagnostic (c) independent passes",
            )
            self.assertIn(
                "lose focus", t, f"{path.name} missing diagnostic (d) model focus"
            )

            # Split recommendation and count lint insufficiency
            self.assertIn("split", t.lower(), f"{path.name} must recommend splitting")
            self.assertIn(
                "passing count-based size lint does not clear",
                t.lower(),
                f"{path.name} must state count lint does not clear right-sizing",
            )

    def test_maintainer_signal_rule_in_both_variants(self):
        for path in (PLAN_REVIEW, PRL_02, RUBRIC):
            t = _read(path).lower()
            self.assertIn(
                "maintainer", t, f"{path.name} must reference maintainer sizing signals"
            )
            self.assertIn(
                "finding", t, f"{path.name} must treat sizing questions as a finding"
            )
            self.assertIn(
                "decomposition",
                t,
                f"{path.name} must recommend investigating by decomposition",
            )

    def test_authoring_guidance_in_assess_and_templates(self):
        t_assess = _read(ASSESS).lower()
        self.assertIn(
            "each e-item\n   must address one concern and be executable in one focused pass",
            t_assess,
            "assess.md must require each E-item to address one concern and be executable in one focused pass",
        )
        self.assertIn(
            "split when an e-item names\n   multiple distinct deliverables",
            t_assess,
            "assess.md must guide splitting multi-deliverable E-items",
        )
        self.assertIn(
            "passing count-based size lint measures count, not conceptual density",
            t_assess,
            "assess.md must distinguish count from conceptual density",
        )

        for path in (CHILD_TEMPLATE, ORCH_TEMPLATE):
            t = _read(path)
            self.assertIn(
                "Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.",
                t,
                f"{path.name} must include the right-sizing rule in the execution checklist intro",
            )


class ReviewFindingsEmitAndEscalateParityTests(unittest.TestCase):
    """revgate Order 02 (plqjt7 E-04/E-05): both variants must emit the typed review record AND
    escalate an unfixed gating finding.

    These assertions live HERE, in the file that already owns single-file-vs-long parity for this
    exact pair, rather than in `tests/test_review_findings_gate.py`: a second parity harness would be
    the drift the repo's single-source rule forbids.

    The long variant is asserted on the STEP FILES (`02-review-and-revise.md`,
    `03-resolve-and-finalize.md`), NOT on the `plan-review-long.md` orchestrator. That is deliberate:
    the orchestrator only lists the steps and contains neither a findings-recording nor a finalize
    section, so a parity check pointed at it would pass while long-variant reviewers received no
    instruction at all.
    """

    def test_findings_record_emission_in_both_variants(self):
        # PRL_02 is the long variant's counterpart to plan-review.md's "Record findings" step.
        for path in (PLAN_REVIEW, PRL_02):
            t = _read(path)
            self.assertIn(
                ".aw/records/reviews/",
                t,
                f"{path.name} must instruct the reviewer to write the typed review record",
            )
            self.assertIn(
                ".review.md",
                t,
                f"{path.name} must name the .review.md artifact",
            )
            low = t.lower()
            self.assertIn(
                "## round",
                low,
                f"{path.name} must instruct appending a new Round for a re-review",
            )
            self.assertIn(
                "current",
                low,
                f"{path.name} must state that only the current round is read",
            )

    def test_escalation_requirement_in_both_variants(self):
        # PRL_03 is the long variant's counterpart to plan-review.md's finalize step.
        for path in (PLAN_REVIEW, PRL_03):
            t = _read(path)
            self.assertIn(
                "- Blocking: yes",
                t,
                f"{path.name} must require the escalation carry `- Blocking: yes`",
            )
            self.assertIn(
                "- Finding: <ID>",
                t,
                f"{path.name} must require the escalation name the finding id",
            )
            self.assertIn(
                "check.review-finding-unescalated",
                t,
                f"{path.name} must name the enforcing rule",
            )
            self.assertIn(
                "review_findings_gate",
                t,
                f"{path.name} must point at the configurable gate threshold",
            )
            self.assertIn(
                "pre-execution",
                t,
                f"{path.name} must state the escalated question is caught at pre-execution",
            )

    def test_escalation_reconciled_with_reporting_only_severity(self):
        """The added wording must reconcile itself with "Severity is for reporting only".

        Both variants carry that rule, so an escalation instruction that did not address it would read
        as a direct contradiction to the next reviewer.
        """
        for path in (PLAN_REVIEW, PRL_03):
            t = _read(path)
            self.assertIn(
                "Severity is for reporting only",
                t,
                f"{path.name} must quote the reporting-only rule it reconciles with",
            )
            self.assertIn(
                "Fix Bar",
                t,
                f"{path.name} must state the Fix Bar alone decides whether to fix",
            )

    def test_fix_bar_and_classification_not_weakened(self):
        """The pre-existing Fix Bar and severity/decision classification must survive intact."""
        pr = _read(PLAN_REVIEW)
        self.assertIn(
            "Fix every finding unless overall Remediation Risk is Medium-High or High.",
            pr,
            "plan-review.md must retain the Fix Bar",
        )
        self.assertIn(
            "Effort, time, cost, and tokens are never valid deferral reasons.",
            pr,
            "plan-review.md must retain the invalid-deferral-reasons rule",
        )
        for path in (PLAN_REVIEW, PRL_02):
            t = _read(path)
            self.assertIn(
                "`BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`",
                t,
                f"{path.name} must retain the severity vocabulary",
            )
            self.assertIn(
                "`FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`",
                t,
                f"{path.name} must retain the decision vocabulary",
            )


if __name__ == "__main__":
    unittest.main()

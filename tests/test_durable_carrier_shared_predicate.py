"""Behavioral tests asserting lint_file and check_durable_carrier share evaluate_durable_carrier.

Plan 55kl2u (backlog 8owahv): restore behavioral coverage lost when tests/test_durable_capture.py
was deleted in 19313eed.

Assures:
- test_one_predicate_backs_both_surfaces: a sentinel substituted for check_engine.evaluate_durable_carrier
  surfaces verbatim on both lint_file --phase pre-transition and check_durable_carrier, and unpatched
  both report the rule with a non-marker detail.
- test_only_lint_file_reaches_the_evaluator: a wraps= spy on the evaluator sees exactly one call
  from lint_file at pre-transition, zero from lint_file at every other ipd_schema.CHECKPOINTS member,
  and zero from lint_text / check_checkpoint at every checkpoint.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import artifact_core as core
from agent_workflows import check_engine as ce
from agent_workflows import ipd_lint
from agent_workflows import ipd_schema as S
from tests import support
from tests.record_builder import RecordBuilder

RULE = "check.ipd-uncarried-obligation"

_CUT = ce.CARRIER_CUTOVER_DATE
_POST_DATE = f"{_CUT[:4]}-{_CUT[4:6]}-{_CUT[6:]}"


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="aw_carrier_pred_"))
    for lane in ("pending", "executed"):
        (d / ".aw" / "records" / "plans" / lane).mkdir(parents=True)
    for status in ("open",):
        (d / ".aw" / "records" / "backlog" / status).mkdir(parents=True)
    return d


def _plan(
    repo: Path,
    *,
    id6: str = "subj01",
    lane: str = "pending",
    date: str = _POST_DATE,
    status: str = "approved",
    deferred_rows: str | None = None,
    open_questions: str = "",
    performed: bool = True,
) -> Path:
    """The SUBJECT plan. performed=True makes its E/V rows satisfy the pre-transition E/V checkpoint."""
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / lane
        / f"{_CUT}-durable-01-{id6}-subject-fixture.ipd.md"
    )
    if deferred_rows is None:
        deferred_rows = "- AN UNCARRIED DEFECT: nothing tracks this.\n"
    exec_state = "performed" if performed else "pending"
    valid_state = "pass" if performed else "pending"
    body = RecordBuilder().plan(
        title=f"durable-carrier subject {id6}",
        when=date,
        plan_role="child",
        scope_paths="x.py",
        item_dependencies="none",
        status=status,
        set="durable",
        order=1,
        highest_e_allocated="01",
        id6=id6,
        history=[f"- {date} draft (t): created."],
        open_questions=open_questions,
        body=f"## Goal\n\ng\n\n## Detailed Implementation Checklist (TODO)\n\n### Task group 1: do the thing\n\n- [x] E-01 DO THE THING.\n  - Depends on: none\n  - Expected outcome: the thing is done\n  - Execution state: {exec_state}\n\n## Project conventions discovered (Step 0)\n\n- none\n\n## Findings\n\n| Id | Severity | Area | What | Evidence |\n|---|---|---|---|---|\n| F-1 | LOW | x | y | z |\n\n## Proposed changes (ordered, validatable)\n\n1. do the thing\n\n## Deferred / out of scope (with reason)\n\n{deferred_rows}\n\n## Scope check\n\n- Over-scope: none\n- Under-scope: none\n\n## Required tests / validation\n\nthe suite\n\n## Spec / documentation sync\n\nnone\n\n## Validation and cross-check (verify before reporting done)\n\n- [x] V-01 validates E-01\n  - Required evidence: paste it\n  - Observed evidence: pasted output here\n  - Result: {valid_state}\n\n## Approval and execution gate\n\n- Size assessment: standard\n- Cohesion rationale: not required",
        text_only=True,
    )
    p.write_text(body, encoding="utf-8")
    return p


class DurableCarrierSharedPredicateTests(unittest.TestCase):
    """Behavioral tests asserting evaluate_durable_carrier is the single shared evaluator."""

    def setUp(self):
        support.declare_execution_role(self)
        self.repo = _mkrepo()
        self.plan = _plan(self.repo)

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def test_one_predicate_backs_both_surfaces(self):
        """A sentinel substituted for evaluate_durable_carrier surfaces verbatim on both consumers.

        Proves that check_engine.check_durable_carrier and ipd_lint.lint_file (--phase pre-transition)
        delegate to the one shared evaluator, rather than maintaining independent implementations.
        """
        marker = "SENTINEL-ONLY-THE-SHARED-EVALUATOR-CAN-PRODUCE-THIS"

        def sentinel(_repo_root, *, plan_path, plan_text, **_kwargs):
            return [core.Drift(str(plan_path), RULE, marker, severity="error")]

        with mock.patch.object(ce, "evaluate_durable_carrier", sentinel):
            lint = ipd_lint.lint_file(self.plan, checkpoint="pre-transition")
            sweep = ce.check_durable_carrier(self.repo)

        self.assertEqual(
            [d.message for d in lint.diagnostics if d.code == RULE],
            [marker],
            "`aw ipd lint --phase pre-transition` did not surface the shared evaluator's sentinel verdict",
        )
        self.assertEqual(
            [d.detail for d in sweep if d.rule == RULE],
            [marker],
            "`aw check` did not surface the shared evaluator's sentinel verdict",
        )

        # Non-vacuity sub-assertion: UNPATCHED, both surfaces report the rule on the same fixture
        # with a detail that is NOT the marker.
        unpatched_lint = ipd_lint.lint_file(self.plan, checkpoint="pre-transition")
        unpatched_sweep = ce.check_durable_carrier(self.repo)

        unpatched_lint_messages = [
            d.message for d in unpatched_lint.diagnostics if d.code == RULE
        ]
        unpatched_sweep_details = [d.detail for d in unpatched_sweep if d.rule == RULE]

        self.assertEqual(len(unpatched_lint_messages), 1)
        self.assertNotEqual(unpatched_lint_messages[0], marker)
        self.assertTrue(
            unpatched_lint_messages[0].startswith(
                "1 obligation(s) name no durable carrier"
            )
        )

        self.assertEqual(len(unpatched_sweep_details), 1)
        self.assertNotEqual(unpatched_sweep_details[0], marker)
        self.assertTrue(
            unpatched_sweep_details[0].startswith(
                "1 obligation(s) name no durable carrier"
            )
        )

    def test_only_lint_file_reaches_the_evaluator(self):
        """A wraps= spy sees exactly one call from lint_file at pre-transition, zero elsewhere.

        Asserts:
        - lint_file at pre-transition reaches the evaluator exactly once and reports the rule.
        - lint_text and check_checkpoint reach the evaluator 0 times across all checkpoints (pure).
        - lint_file at every checkpoint other than pre-transition reaches the evaluator 0 times.
        """
        plan = self.plan
        text = plan.read_text(encoding="utf-8")
        doc = ipd_lint.parse(text)

        # 1. lint_file at pre-transition calls it exactly once and reports the rule
        with mock.patch.object(
            ce, "evaluate_durable_carrier", wraps=ce.evaluate_durable_carrier
        ) as spy:
            res = ipd_lint.lint_file(plan, checkpoint="pre-transition")
        self.assertEqual(
            spy.call_count,
            1,
            f"`lint_file` reached the shared evaluator {spy.call_count} times; it must reach it exactly once.",
        )
        self.assertEqual(
            [d.code for d in res.diagnostics if d.code == RULE],
            [RULE],
            "the fixture must report check.ipd-uncarried-obligation at pre-transition",
        )

        # 2. Pure surfaces lint_text and check_checkpoint reach it 0 times for every checkpoint
        for label, drive in (
            (
                "lint_text",
                lambda cp: ipd_lint.lint_text(text, checkpoint=cp, directory="pending"),
            ),
            (
                "check_checkpoint",
                lambda cp: ipd_lint.check_checkpoint(doc, cp, "pending"),
            ),
        ):
            with mock.patch.object(
                ce, "evaluate_durable_carrier", wraps=ce.evaluate_durable_carrier
            ) as spy:
                for cp in S.CHECKPOINTS:
                    drive(cp)
            self.assertEqual(
                spy.call_count,
                0,
                f"`{label}` reached the repo-aware evaluator {spy.call_count} times across {len(S.CHECKPOINTS)} checkpoints.",
            )

        # 3. lint_file at every checkpoint where the rule does not apply calls it 0 times
        for cp in S.CHECKPOINTS:
            if cp in ("pre-transition", "review-finalize"):
                continue
            with mock.patch.object(
                ce, "evaluate_durable_carrier", wraps=ce.evaluate_durable_carrier
            ) as spy:
                ipd_lint.lint_file(plan, checkpoint=cp)
            self.assertEqual(
                spy.call_count,
                0,
                f"`lint_file` at checkpoint {cp!r} reached the evaluator {spy.call_count} times; expected 0.",
            )

    def test_review_finalize_reports_what_the_review_merge_gate_refuses(self):
        """pay4hs: the reviewer's check and the review-lane merge gate must agree.

        Before the fix `aw ipd lint --phase review-finalize` reported this plan clean while
        `runner_shared.check_review_lane_artifacts` refused it, so the review was wasted.
        """
        from agent_workflows import runner_shared as rs

        res = ipd_lint.lint_file(self.plan, checkpoint="review-finalize")
        self.assertIn(RULE, [d.code for d in res.diagnostics])
        self.assertNotEqual(res.disposition, S.DISPOSITION_CONFORMING)

        # The gate's carrier half, isolated: with the gate's own author-lint half stubbed to pass
        # (this fixture lacks unrelated metadata), the gate refuses for exactly the carrier rule.
        rel = str(self.plan.relative_to(self.repo)).replace("\\", "/")
        handle = mock.Mock(path=str(self.repo), branch="")
        passing = ipd_lint.LintResult(S.DISPOSITION_CONFORMING, [], [])
        with mock.patch.object(ipd_lint, "lint_text", return_value=passing):
            ok, reason = rs.check_review_lane_artifacts(self.repo, handle, [rel])
        self.assertFalse(ok)
        self.assertIn(RULE, reason)

        # Drafting is still free: `author` does not demand a carrier.
        author = ipd_lint.lint_file(self.plan, checkpoint="author")
        self.assertNotIn(RULE, [d.code for d in author.diagnostics])

    def test_none_deferred_sentinel_bullets_are_not_uncarried_obligations(self):
        """`- None.` / `- N/A.` sentinel bullets in `## Deferred / out of scope` are not obligations."""
        sentinel_bullets = [
            "- None.",
            "- None. This child completes the final testing and verification.",
            "- **None.** All requirements are covered in this plan.",
            "- N/A. Final wrap-up child.",
            "- Nothing deferred.",
        ]
        for bullet in sentinel_bullets:
            text = (
                "# Plan\n\n"
                "- Id: abc123\n"
                "- Date: 2026-11-27\n"
                "- Status: to-review\n\n"
                f"## {S.H_DEFERRED}\n\n"
                f"{bullet}\n"
            )
            drifts = ce.evaluate_durable_carrier(
                self.repo,
                plan_path=self.plan,
                plan_text=text,
                open_questions=[],
            )
            self.assertEqual(
                drifts,
                [],
                f"sentinel bullet {bullet!r} should not trigger {RULE}, got {drifts}",
            )

        # Non-sentinel bullets starting with "None of..." or real deferred work MUST still trigger.
        real_bullets = [
            "- None of the Windows smoke tests were converted yet.",
            "- Defer packaging to a follow-up.",
        ]
        for bullet in real_bullets:
            text = (
                "# Plan\n\n"
                "- Id: abc123\n"
                "- Date: 2026-11-27\n"
                "- Status: to-review\n\n"
                f"## {S.H_DEFERRED}\n\n"
                f"{bullet}\n"
            )
            drifts = ce.evaluate_durable_carrier(
                self.repo,
                plan_path=self.plan,
                plan_text=text,
                open_questions=[],
            )
            self.assertTrue(
                any(d.rule == RULE for d in drifts),
                f"real deferred bullet {bullet!r} must trigger {RULE}, got {drifts}",
            )


if __name__ == "__main__":
    unittest.main()

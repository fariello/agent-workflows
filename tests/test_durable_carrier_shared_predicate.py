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
    body = (
        f"# IPD: durable-carrier subject {id6}\n\n"
        f"- Date: {date}\n- Kind: child\n- Scope-Paths: x.py\n"
        f"- Item-Dependencies: none\n- Status: {status}\n- Set: durable\n- Order: 1\n"
        f"- Highest E allocated: 01\n- Id: {id6}\n\n"
        f"## Workflow history\n- {date} draft (t): created.\n\n"
        f"## Goal\n\ng\n\n"
        f"## Detailed Implementation Checklist (TODO)\n\n"
        f"### Task group 1: do the thing\n\n"
        f"- [x] E-01 DO THE THING.\n"
        f"  - Depends on: none\n"
        f"  - Expected outcome: the thing is done\n"
        f"  - Execution state: {exec_state}\n\n"
        f"## Project conventions discovered (Step 0)\n\n- none\n\n"
        f"## Findings\n\n| Id | Severity | Area | What | Evidence |\n|---|---|---|---|---|\n"
        f"| F-1 | LOW | x | y | z |\n\n"
        f"## Proposed changes (ordered, validatable)\n\n1. do the thing\n\n"
        f"## Deferred / out of scope (with reason)\n\n{deferred_rows}\n"
        f"## Scope check\n\n- Over-scope: none\n- Under-scope: none\n\n"
        f"## Required tests / validation\n\nthe suite\n\n"
        f"## Spec / documentation sync\n\nnone\n\n"
        f"## Open questions\n\n{open_questions}\n"
        f"## Validation and cross-check (verify before reporting done)\n\n"
        f"- [x] V-01 validates E-01\n"
        f"  - Required evidence: paste it\n"
        f"  - Observed evidence: pasted output here\n"
        f"  - Result: {valid_state}\n\n"
        f"## Approval and execution gate\n\n- Size assessment: standard\n"
        f"- Cohesion rationale: not required\n"
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

        # 3. lint_file at every checkpoint other than pre-transition calls it 0 times
        for cp in S.CHECKPOINTS:
            if cp == "pre-transition":
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


if __name__ == "__main__":
    unittest.main()

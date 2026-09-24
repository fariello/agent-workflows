"""Tests for Priority and Work-Kind enforcement at the ready-to-execute gate (planprio lkexaw).

Covers:
1. Ready-to-execute gate refusal (missing Priority / Work-Kind at pre-execution or on approved status).
2. Reserved sentinel grandfather exemption (advisory-satisfied at ready-to-execute gate).
3. Terminal exemption (legacy short-circuit at 4 non-post-transition phases).
4. Scaffold emission (build_skeleton writes unresolved sentinels after Status).
5. Enum-rule admission (check_plan_priority and check_plan_work_kind accept grandfathered, flag TODO).
6. Setter position stability (ipd set preserves field position after Status).
7. Authoring placeholder resolution (authoring_placeholders_resolved returns False on unresolved).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import cli
from agent_workflows import ipd_authoring as auth
from agent_workflows import ipd_lint as lint
from agent_workflows import ipd_schema as schema


def _build_test_plan(
    *,
    status: str = "draft",
    priority: str | None = None,
    work_kind: str | None = None,
    scope_paths: str = "agent_workflows/foo.py",
    plan_id: str = "tst001",
    approval: str | None = None,
) -> str:
    lines = [
        f"# IPD: Test Plan {plan_id}",
        "",
        "- Date: 2026-09-24",
        "- Kind: child",
        "- Concern: Test concern.",
        "- Scope: Test scope.",
        f"- Scope-Paths: {scope_paths}",
        "- Item-Dependencies: none",
        f"- Status: {status}",
    ]
    if approval:
        lines.append(f"- Approval: {approval}")
    if work_kind is not None:
        lines.append(f"- Work-Kind: {work_kind}")
    if priority is not None:
        lines.append(f"- Priority: {priority}")
    lines.extend(
        [
            "- Set: testset",
            "- Order: 1",
            "- Highest E allocated: 01",
            "- Author: test-author",
            f"- Id: {plan_id}",
            "",
            "## Workflow history",
            "- 2026-09-24 draft (test-author): created.",
            "",
            "## Goal",
            "Test goal.",
            "",
            "## Detailed Implementation Checklist (TODO)",
            "- [ ] E-01 Test action.",
            "  - Depends on: none",
            "  - Expected outcome: done",
            "  - Execution state: pending",
            "",
            "## Project conventions discovered (Step 0)",
            "- Convention 1.",
            "",
            "## Findings",
            "| Id | Severity | Finding |",
            "|---|---|---|",
            "| F-1 | LOW | Test finding. |",
            "",
            "## Proposed changes (ordered, validatable)",
            "1. Test change.",
            "",
            "## Deferred / out of scope (with reason)",
            "- None.",
            "",
            "## Scope check",
            "- Over-scope: none.",
            "",
            "## Required tests / validation",
            "tests/test_foo.py",
            "",
            "## Spec / documentation sync",
            "None.",
            "",
            "## Open questions",
            "### OQ-01: None.",
            "- Blocking: no",
            "- Status: resolved",
            "- Owner: author",
            "- Resolution or deferral rationale: done.",
            "",
            "## Validation and cross-check (verify before reporting done)",
            "- [ ] V-01 validates E-01",
            "  - Required evidence: done",
            "  - Observed evidence:",
            "  - Result: pending",
            "",
            "## Approval and execution gate",
            "- Size assessment: standard",
            "- Cohesion rationale: not required",
            "",
        ]
    )
    return "\n".join(lines)


class ReadyToExecuteGateTests(unittest.TestCase):
    def test_missing_priority_or_work_kind_refused_at_pre_execution(self) -> None:
        """A plan missing Priority or Work-Kind is refused at pre-execution."""
        text_no_prio = _build_test_plan(work_kind="feature")
        res_prio = lint.lint_text(
            text_no_prio, checkpoint="pre-execution", directory="pending"
        )
        self.assertEqual(res_prio.disposition, schema.DISPOSITION_ERROR)
        codes = [d.code for d in res_prio.diagnostics]
        self.assertIn(lint.C_PRIORITY, codes)
        self.assertNotIn(lint.C_WORK_KIND, codes)

        text_no_wk = _build_test_plan(priority="medium")
        res_wk = lint.lint_text(
            text_no_wk, checkpoint="pre-execution", directory="pending"
        )
        self.assertEqual(res_wk.disposition, schema.DISPOSITION_ERROR)
        codes = [d.code for d in res_wk.diagnostics]
        self.assertIn(lint.C_WORK_KIND, codes)
        self.assertNotIn(lint.C_PRIORITY, codes)

        text_neither = _build_test_plan()
        res_both = lint.lint_text(
            text_neither, checkpoint="pre-execution", directory="pending"
        )
        self.assertEqual(res_both.disposition, schema.DISPOSITION_ERROR)
        codes = [d.code for d in res_both.diagnostics]
        self.assertIn(lint.C_PRIORITY, codes)
        self.assertIn(lint.C_WORK_KIND, codes)

    def test_unresolved_sentinel_refused_at_pre_execution(self) -> None:
        """A plan with 'unresolved' sentinel is refused at pre-execution."""
        text = _build_test_plan(priority="unresolved", work_kind="unresolved")
        res = lint.lint_text(text, checkpoint="pre-execution", directory="pending")
        self.assertEqual(res.disposition, schema.DISPOSITION_ERROR)
        codes = [d.code for d in res.diagnostics]
        self.assertIn(lint.C_PRIORITY, codes)
        self.assertIn(lint.C_WORK_KIND, codes)

    def test_approved_plan_missing_fields_refused_at_author_phase(self) -> None:
        """The gate fires on status in READY_TO_EXECUTE even at the author checkpoint."""
        text = _build_test_plan(
            status="approved",
            approval="2026-09-24, human approval",
        )
        res = lint.lint_text(text, checkpoint="author", directory="pending")
        self.assertEqual(res.disposition, schema.DISPOSITION_ERROR)
        codes = [d.code for d in res.diagnostics]
        self.assertIn(lint.C_PRIORITY, codes)
        self.assertIn(lint.C_WORK_KIND, codes)

    def test_draft_or_reviewed_plan_missing_fields_passes_at_author_phase(self) -> None:
        """Draft/to-review/reviewed plans missing the fields lint clean at author phase."""
        for st in ("draft", "to-review", "reviewed"):
            text = _build_test_plan(status=st)
            res = lint.lint_text(text, checkpoint="author", directory="pending")
            codes = [d.code for d in res.diagnostics]
            self.assertNotIn(lint.C_PRIORITY, codes)
            self.assertNotIn(lint.C_WORK_KIND, codes)

    def test_grandfathered_sentinel_advisory_satisfied(self) -> None:
        """A plan carrying 'grandfathered' in both fields passes with advisories."""
        text = _build_test_plan(
            priority="grandfathered",
            work_kind="grandfathered",
            status="approved",
            approval="2026-09-24, human approval",
        )
        res = lint.lint_text(text, checkpoint="pre-execution", directory="pending")
        self.assertEqual(res.disposition, schema.DISPOSITION_CONFORMING)
        adv_codes = [d.code for d in res.advisories]
        self.assertIn(lint.C_PRIORITY, adv_codes)
        self.assertIn(lint.C_WORK_KIND, adv_codes)

    def test_valid_vocab_values_pass_silently(self) -> None:
        """A plan with valid vocabulary values passes with 0 diagnostics."""
        text = _build_test_plan(
            priority="high",
            work_kind="feature",
            status="approved",
            approval="2026-09-24, human approval",
        )
        res = lint.lint_text(text, checkpoint="pre-execution", directory="pending")
        self.assertEqual(res.disposition, schema.DISPOSITION_CONFORMING)
        codes = [d.code for d in res.diagnostics]
        self.assertNotIn(lint.C_PRIORITY, codes)
        self.assertNotIn(lint.C_WORK_KIND, codes)


class TerminalExemptionTests(unittest.TestCase):
    def test_terminal_plan_missing_fields_clean_at_four_phases(self) -> None:
        """An executed plan missing both fields produces NO diagnostics at 4 non-post-transition phases."""
        text = _build_test_plan(status="executed")
        for phase in ("author", "review-finalize", "pre-execution", "pre-transition"):
            res = lint.lint_text(text, checkpoint=phase, directory="executed")
            self.assertEqual(res.disposition, schema.DISPOSITION_LEGACY)
            self.assertEqual(
                len(res.diagnostics), 0, f"Failed at {phase}: {res.diagnostics}"
            )


class ScaffoldEmissionTests(unittest.TestCase):
    def test_scaffold_emits_unresolved_sentinels_after_status(self) -> None:
        """build_skeleton writes - Priority: unresolved and - Work-Kind: unresolved after Status."""
        skeleton = auth.build_skeleton(
            kind="child",
            title="Test Scaffold",
            author="test-author",
            when="2026-09-24",
            set_name="myset",
            order=1,
            plan_id="tmp123",
        )
        lines = skeleton.splitlines()
        status_idx = lines.index("- Status: draft")
        self.assertEqual(lines[status_idx + 1], "- Work-Kind: unresolved")
        self.assertEqual(lines[status_idx + 2], "- Priority: unresolved")

    def test_placeholder_property(self) -> None:
        """authoring_placeholders_resolved returns False when unresolved sentinel is present."""
        skeleton = auth.build_skeleton(
            kind="child",
            title="Test Scaffold",
            author="test-author",
            when="2026-09-24",
            set_name="myset",
            order=1,
            plan_id="tmp123",
        )
        self.assertFalse(auth.authoring_placeholders_resolved(skeleton))

        # Replace all placeholders except Priority
        prio_unresolved = _build_test_plan(priority="unresolved", work_kind="bug")
        self.assertFalse(auth.authoring_placeholders_resolved(prio_unresolved))

        # Replace all placeholders except Work-Kind
        wk_unresolved = _build_test_plan(priority="low", work_kind="unresolved")
        self.assertFalse(auth.authoring_placeholders_resolved(wk_unresolved))


class EnumRuleAdmissionTests(unittest.TestCase):
    def test_check_plan_priority_and_work_kind_admit_sentinel(self) -> None:
        """check_plan_priority and check_plan_work_kind admit 'grandfathered', reject 'TODO'."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plans_dir = root / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)

            # 1. Scratch plan with grandfathered sentinel -> 0 findings from both
            p_grand = plans_dir / "20260924-testset-01-tst001-grandfathered.ipd.md"
            p_grand.write_text(
                _build_test_plan(
                    priority="grandfathered",
                    work_kind="grandfathered",
                    plan_id="tst001",
                ),
                encoding="utf-8",
            )

            # 2. Scratch plan with TODO -> 1 finding from each
            p_todo = plans_dir / "20260924-testset-02-tst002-todo.ipd.md"
            p_todo.write_text(
                _build_test_plan(priority="TODO", work_kind="TODO", plan_id="tst002"),
                encoding="utf-8",
            )

            # 3. Scratch plan with unresolved sentinel -> 0 findings from both
            p_unresolved = plans_dir / "20260924-testset-03-tst003-unresolved.ipd.md"
            p_unresolved.write_text(
                _build_test_plan(
                    priority="unresolved", work_kind="unresolved", plan_id="tst003"
                ),
                encoding="utf-8",
            )

            # 4. Scratch plan with valid vocab -> 0 findings from both
            p_valid = plans_dir / "20260924-testset-04-tst004-valid.ipd.md"
            p_valid.write_text(
                _build_test_plan(
                    priority="medium", work_kind="feature", plan_id="tst004"
                ),
                encoding="utf-8",
            )

            prio_drift = ce.check_plan_priority(root, include_untracked=True)
            wk_drift = ce.check_plan_work_kind(root, include_untracked=True)

            prio_bad = [d for d in prio_drift if d.rule == "check.priority-invalid"]
            wk_bad = [d for d in wk_drift if d.rule == "check.work-kind-invalid"]

            self.assertEqual(
                len(prio_bad), 1, [(d.location, d.detail) for d in prio_bad]
            )
            self.assertIn("tst002", prio_bad[0].location)

            self.assertEqual(len(wk_bad), 1, [(d.location, d.detail) for d in wk_bad])
            self.assertIn("tst002", wk_bad[0].location)


class SetterPositionStabilityTests(unittest.TestCase):
    def test_setter_leaves_fields_adjacent_after_status(self) -> None:
        """aw ipd set --priority high --work-kind bug preserves position after - Status:."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plans_dir = root / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)
            p = plans_dir / "20260924-testset-01-tst001-test.ipd.md"
            p.write_text(
                auth.build_skeleton(
                    kind="child",
                    title="Test Plan",
                    author="test-author",
                    when="2026-09-24",
                    set_name="testset",
                    order=1,
                    plan_id="tst001",
                ),
                encoding="utf-8",
            )
            rc = cli.main(
                [
                    "ipd",
                    "set",
                    "draft",
                    "tst001",
                    "--priority",
                    "high",
                    "--work-kind",
                    "bug",
                    "--yes",
                    "--dir",
                    str(root),
                    "-m",
                    "update triage",
                ]
            )
            self.assertEqual(rc, 0)
            lines = p.read_text(encoding="utf-8").splitlines()
            status_idx = lines.index("- Status: draft")
            self.assertEqual(lines[status_idx + 1], "- Work-Kind: bug")
            self.assertEqual(lines[status_idx + 2], "- Priority: high")


if __name__ == "__main__":
    unittest.main()

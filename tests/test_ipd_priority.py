"""Tests for xprio Order 01 (1b45el): recognized-but-optional Priority on IPDs.

Covers E-01 (schema RECOGNIZES `Priority`; `aw ipd set --priority` writes/persists/clears via the
hoisted status-branch-independent write), E-02 (`aw check` validates the enum against the shared
`backlog.PRIORITIES`, silent on a valid/absent value), and E-03 (`attention._plans_record` populates
`Item.priority` from the plan's `- Priority:` line; absent = None; the shared sort key is unchanged).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    attention,
    backlog,
    check_engine as ce,
    cli,
    ipd_schema,
)


_PLAN = """\
# IPD: Prio demo

- Date: 2026-08-28
- Kind: child
- Concern: demo.
- Scope: demo.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: approved
{priority_line}- Set: demo
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: {id6}
- Approval: 2026-08-28, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-28 approved (aw set): status set to approved
- 2026-08-28 draft (test): created.

## Goal
demo.

## Detailed Implementation Checklist (TODO)

### Task group 1: demo
- [x] E-01 Do it.
  - Depends on: none
  - Expected outcome: done.
  - Execution state: performed

## Project conventions discovered (Step 0)
- x.

## Findings
x.

## Proposed changes (ordered, validatable)
1. x.

## Deferred / out of scope (with reason)
none.

## Scope check
- Over-scope: none.
- Under-scope: none.

## Required tests / validation
x.

## Spec / documentation sync
N/A.

## Open questions

### OQ-01: none?
- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: none.

## Validation and cross-check (verify before reporting done)
- [x] V-01 validates E-01
  - Required evidence: x.
  - Observed evidence: x.
  - Result: pass

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""


def _write_plan(root: Path, id6: str, priority: str | None) -> Path:
    plans = root / ".aw" / "records" / "plans" / "pending"
    plans.mkdir(parents=True, exist_ok=True)
    line = f"- Priority: {priority}\n" if priority is not None else ""
    p = plans / f"20260828-demo-01-{id6}-x.ipd.md"
    p.write_text(_PLAN.format(priority_line=line, id6=id6), encoding="utf-8")
    return p


class PrioritySchemaTests(unittest.TestCase):
    def test_priority_is_recognized_not_required(self) -> None:
        # E-01: schema RECOGNIZES Priority (suppresses IPD-M103 unknown-field) but does NOT require it.
        self.assertIn(ipd_schema.META_PRIORITY, ipd_schema.META_RECOGNIZED)
        self.assertEqual(ipd_schema.META_PRIORITY, "Priority")
        self.assertNotIn(ipd_schema.META_PRIORITY, ipd_schema.META_REQUIRED)

    def test_schema_does_not_enum_validate_priority(self) -> None:
        # Per the documented convention, validate_metadata does NOT enum-check Priority (that is
        # aw check's job); a recognized-but-bogus value must not raise an unknown-field error here.
        text = _PLAN.format(priority_line="- Priority: bogus\n", id6="sch001")
        from agent_workflows import ipd_lint

        doc = ipd_lint.parse(text)
        diags = ipd_schema.validate_metadata(doc.meta_fields)
        codes = [getattr(d, "code", "") for d in diags]
        # No unknown-field (M103) error for the recognized Priority field.
        self.assertNotIn("IPD-M103", codes)


class PrioritySetterTests(unittest.TestCase):
    def test_set_writes_persists_on_noop_and_clears(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = _write_plan(root, "set001", None)
            # set medium (via the real `aw ipd set` CLI surface)
            rc = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "set001",
                    "--priority",
                    "medium",
                    "--dir",
                    str(root),
                    "-m",
                    "set prio",
                ]
            )
            self.assertEqual(rc, 0)
            self.assertIn("- Priority: medium", p.read_text(encoding="utf-8"))
            # same-status no-op re-run WITHOUT --priority -> line persists
            cli.main(
                ["ipd", "set", "approved", "set001", "--dir", str(root), "-m", "noop"]
            )
            self.assertIn("- Priority: medium", p.read_text(encoding="utf-8"))
            # clear with '-'
            cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "set001",
                    "--priority",
                    "-",
                    "--dir",
                    str(root),
                    "-m",
                    "clear",
                ]
            )
            self.assertNotIn("- Priority:", p.read_text(encoding="utf-8"))


class PriorityCheckTests(unittest.TestCase):
    def test_check_flags_out_of_vocab_only(self) -> None:
        # E-02: aw check flags an out-of-vocab Priority; silent for a valid value and for absent.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_plan(root, "chkbad", "bogus")
            _write_plan(root, "chkgud", "high")
            _write_plan(root, "chknon", None)
            drift = ce.check_plan_priority(root, include_untracked=True)
            bad = [d for d in drift if d.rule == "check.priority-invalid"]
            self.assertEqual(len(bad), 1, [(d.location, d.detail) for d in drift])
            self.assertIn("chkbad", bad[0].location)
            self.assertIn("bogus", bad[0].detail)

    def test_check_uses_shared_backlog_vocab_not_forked(self) -> None:
        # The enum consumed is the shared backlog.PRIORITIES (import), never a forked literal.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Every member of the shared vocab must pass silently.
            for i, val in enumerate(sorted(backlog.PRIORITIES)):
                _write_plan(root, f"shr00{i}", val)
            drift = ce.check_plan_priority(root, include_untracked=True)
            self.assertEqual(
                [d for d in drift if d.rule == "check.priority-invalid"], []
            )

    def test_check_content_plans_surfaces_priority_invalid(self) -> None:
        # Wired into the plans-type content path (reached by aw check plans / all).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_plan(root, "ctbad0", "urgent")
            drift = ce.check_content(root, "plans", include_untracked=True)
            self.assertIn("check.priority-invalid", [d.rule for d in drift])


class PriorityAttentionTests(unittest.TestCase):
    def test_plans_record_populates_priority(self) -> None:
        # E-03: _plans_record reads `- Priority:` into Item.priority; absent -> None.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p_hi = _write_plan(root, "att001", "high")
            item_hi, _ = attention._plans_record(
                str(p_hi.relative_to(root)), p_hi, p_hi.read_text(encoding="utf-8")
            )
            self.assertIsNotNone(item_hi)
            self.assertEqual(item_hi.priority, "high")

            p_none = _write_plan(root, "att002", None)
            item_none, _ = attention._plans_record(
                str(p_none.relative_to(root)),
                p_none,
                p_none.read_text(encoding="utf-8"),
            )
            self.assertIsNotNone(item_none)
            self.assertIsNone(item_none.priority)


if __name__ == "__main__":
    unittest.main()

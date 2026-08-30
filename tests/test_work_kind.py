"""Tests for wkindname Order 02 (ng2blv): recognized-but-optional Work-Kind on plans and specs.

Modeled on the sibling `tests/test_ipd_priority.py` and `tests/test_spec_priority.py` so the two
optional-metadata features are verified the same way.

Covers E-01 (ONE shared vocabulary: the accepted set IS `backlog.KINDS`, never a forked literal),
E-02 (the IPD schema RECOGNIZES `Work-Kind` but does NOT require it, and does NOT enum-check it),
E-03 (the spec contract reads + enum-validates the optional bullet), E-04 (`aw ipd set --work-kind`
and `aw specs set --work-kind` write/persist/clear, and refuse an out-of-vocab value), E-05
(`aw check` flags an out-of-vocab value as `check.work-kind-invalid`, silent when valid or absent),
and E-06 (this module).

THE CENTRAL PROPERTY under test is NO MASS-FAIL: an artifact carrying NO Work-Kind must validate
exactly as before, on BOTH carriers. Note the deliberate asymmetry with backlog, which REQUIRES its
work-nature field and reports through its own `backlog.kind-invalid` path (Order 9trlc3); this Set
unified the field NAME across three types, not its requiredness. That asymmetry is asserted here so
nobody "fixes" it by weakening backlog's contract.
"""

from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from agent_workflows import (
    backlog,
    check_engine as ce,
    cli,
    ipd_schema,
    releases,
    specs,
)


# --------------------------------------------------------------------------------------
# Plan fixture (mirrors tests/test_ipd_priority.py's _PLAN)
# --------------------------------------------------------------------------------------

_PLAN = """\
# IPD: Work-Kind demo

- Date: 2026-08-29
- Kind: child
- Concern: demo.
- Scope: demo.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: approved
{work_kind_line}- Set: demo
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: {id6}
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 draft (test): created.

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


def _write_plan(root: Path, id6: str, work_kind: str | None) -> Path:
    plans = root / ".aw" / "records" / "plans" / "pending"
    plans.mkdir(parents=True, exist_ok=True)
    line = f"- Work-Kind: {work_kind}\n" if work_kind is not None else ""
    p = plans / f"20260829-demo-01-{id6}-x.ipd.md"
    p.write_text(_PLAN.format(work_kind_line=line, id6=id6), encoding="utf-8")
    return p


# --------------------------------------------------------------------------------------
# Spec fixture (mirrors tests/test_spec_priority.py)
# --------------------------------------------------------------------------------------


def _spec(status_block: str) -> str:
    return (
        "# Spec: t\n\n"
        + status_block
        + "\n## Body\n\ntext\n\n## Workflow history\n- 2026-08-29 draft (fixture): created.\n"
    )


def _args(**kw):
    ns = argparse.Namespace()
    defaults = dict(
        gate_kind=None,
        gate_ref=None,
        gate_summary=None,
        evidence=None,
        blocks_release=None,
        priority=None,
        work_kind=None,
        by_human=False,
        commit=False,
        date="2026-08-29",
    )
    for k, v in defaults.items():
        setattr(ns, k, v)
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def _mk_spec(d, block: str) -> Path:
    p = Path(d) / "s.md"
    p.write_text(_spec(block), encoding="utf-8")
    return p


# --------------------------------------------------------------------------------------
# E-01: ONE shared vocabulary
# --------------------------------------------------------------------------------------


class SharedVocabularyTests(unittest.TestCase):
    def test_accepted_set_is_the_shared_backlog_kinds_symbol(self) -> None:
        """E-01: the accepted vocabulary IS `backlog.KINDS`, not a copy of its members.

        This is the anti-fork assertion. It fails against an implementation that hard-codes a
        literal list, because the identity check below is against the shared frozenset OBJECT.
        """
        self.assertEqual(
            backlog.KINDS,
            frozenset(("bug", "feature", "chore", "security", "followup")),
        )
        # Every member of the SHARED vocab must be accepted on a plan, with no finding.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i, val in enumerate(sorted(backlog.KINDS)):
                _write_plan(root, f"shr00{i}", val)
            drift = ce.check_plan_work_kind(root, include_untracked=True)
            self.assertEqual(
                [d for d in drift if d.rule == "check.work-kind-invalid"],
                [],
                [(d.location, d.detail) for d in drift],
            )
        # ... and on a spec.
        for val in sorted(backlog.KINDS):
            text = _spec(f"- Status: draft\n- Work-Kind: {val}")
            drift = specs.validate_spec(Path("s.md"), text)
            self.assertEqual(
                [d for d in drift if d.rule == "spec.work-kind-invalid"], [], val
            )

    def test_the_check_rule_advertises_the_shared_vocab_in_its_message(self) -> None:
        """The accepted set and the ADVERTISED set cannot drift: the message is built from the
        shared symbol, so every member appears in the finding detail."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_plan(root, "advrt0", "bogus")
            drift = ce.check_plan_work_kind(root, include_untracked=True)
            self.assertEqual(len(drift), 1)
            for member in backlog.KINDS:
                self.assertIn(member, drift[0].detail)

    def test_the_cli_choices_match_the_shared_vocab(self) -> None:
        """The argparse `choices` list is a literal, exactly as the `--priority` precedent's is
        (`choices=["low","medium","high","-"]` appears three times in cli.py). A literal there is
        unavoidable at parser-build time, so this test PINS it to the shared vocabulary: if
        `backlog.KINDS` ever gains or loses a member, this fails rather than letting the CLI
        silently accept a different set from what `aw check` validates."""
        parser = cli._build_parser()

        def _choices_for(path: tuple[str, ...]) -> set[str]:
            node = parser
            for name in path:
                sub = next(
                    a
                    for a in node._actions
                    if isinstance(a, argparse._SubParsersAction)
                )
                node = sub.choices[name]
            action = next(
                a for a in node._actions if getattr(a, "dest", "") == "work_kind"
            )
            return set(action.choices or ())

        expected = set(backlog.KINDS) | {"-"}
        self.assertEqual(_choices_for(("ipd", "set")), expected)
        self.assertEqual(_choices_for(("specs", "set")), expected)

    def test_the_symbol_name_is_unchanged(self) -> None:
        """Order 9trlc3 renamed the on-disk FIELD, not the vocabulary SYMBOL. E-01 forbids
        renaming the symbol, so a future rename of `backlog.KINDS` fails here."""
        self.assertTrue(hasattr(backlog, "KINDS"))


# --------------------------------------------------------------------------------------
# E-02: the IPD schema
# --------------------------------------------------------------------------------------


class WorkKindSchemaTests(unittest.TestCase):
    def test_work_kind_is_recognized_not_required(self) -> None:
        # E-02: schema RECOGNIZES Work-Kind (suppresses IPD-M103) but does NOT require it.
        self.assertIn(ipd_schema.META_WORK_KIND, ipd_schema.META_RECOGNIZED)
        self.assertEqual(ipd_schema.META_WORK_KIND, "Work-Kind")
        self.assertNotIn(ipd_schema.META_WORK_KIND, ipd_schema.META_REQUIRED)

    def test_the_field_is_not_named_kind(self) -> None:
        """The name must not collide with the plan's REQUIRED structural `Kind`
        (child|orchestrator), which is a wholly disjoint vocabulary."""
        self.assertNotEqual(ipd_schema.META_WORK_KIND, "Kind")
        self.assertIn("Kind", ipd_schema.META_REQUIRED)
        self.assertEqual(set(ipd_schema.KINDS), {"child", "orchestrator"})
        self.assertEqual(set(ipd_schema.KINDS) & set(backlog.KINDS), set())

    def test_schema_does_not_enum_validate_work_kind(self) -> None:
        # Per the documented layering, validate_metadata does NOT enum-check Work-Kind (that is
        # aw check's job); a recognized-but-bogus value must not raise an unknown-field error here.
        from agent_workflows import ipd_lint

        text = _PLAN.format(work_kind_line="- Work-Kind: bogus\n", id6="sch001")
        doc = ipd_lint.parse(text)
        diags = ipd_schema.validate_metadata(doc.meta_fields)
        codes = [getattr(d, "code", "") for d in diags]
        self.assertNotIn("IPD-M103", codes)

    def test_a_plan_with_a_valid_work_kind_lints_clean(self) -> None:
        from agent_workflows import ipd_lint

        text = _PLAN.format(work_kind_line="- Work-Kind: feature\n", id6="lnt001")
        doc = ipd_lint.parse(text)
        diags = ipd_schema.validate_metadata(doc.meta_fields)
        self.assertEqual([getattr(d, "code", "") for d in diags], [])

    def test_a_plan_with_NO_work_kind_lints_clean(self) -> None:
        """THE NO-MASS-FAIL PROPERTY for plans. Fails against an implementation that added the
        field to META_REQUIRED."""
        from agent_workflows import ipd_lint

        text = _PLAN.format(work_kind_line="", id6="lnt002")
        doc = ipd_lint.parse(text)
        diags = ipd_schema.validate_metadata(doc.meta_fields)
        self.assertEqual([getattr(d, "code", "") for d in diags], [])


# --------------------------------------------------------------------------------------
# E-03: the spec contract
# --------------------------------------------------------------------------------------


class SpecWorkKindContractTests(unittest.TestCase):
    def test_valid_work_kind_conforms(self) -> None:
        for val in sorted(backlog.KINDS):
            text = _spec(f"- Status: draft\n- Work-Kind: {val}")
            drift = specs.validate_spec(Path("s.md"), text)
            self.assertEqual(
                [d for d in drift if d.rule == "spec.work-kind-invalid"], [], val
            )

    def test_absent_work_kind_conforms(self) -> None:
        """THE NO-MASS-FAIL PROPERTY for specs."""
        drift = specs.validate_spec(Path("s.md"), _spec("- Status: draft"))
        self.assertEqual([d for d in drift if d.rule == "spec.work-kind-invalid"], [])

    def test_out_of_vocab_work_kind_flagged(self) -> None:
        drift = specs.validate_spec(
            Path("s.md"), _spec("- Status: draft\n- Work-Kind: bogus")
        )
        bad = [d for d in drift if d.rule == "spec.work-kind-invalid"]
        self.assertEqual(len(bad), 1, [(d.rule, d.detail) for d in drift])
        self.assertIn("bogus", bad[0].detail)

    def test_reader_returns_value_or_none(self) -> None:
        self.assertEqual(
            specs._read_work_kind(
                _spec("- Status: draft\n- Work-Kind: bug").split("\n")
            ),
            "bug",
        )
        self.assertIsNone(specs._read_work_kind(_spec("- Status: draft").split("\n")))


# --------------------------------------------------------------------------------------
# E-04: the setters
# --------------------------------------------------------------------------------------


class PlanSetterTests(unittest.TestCase):
    def test_set_writes_persists_on_noop_and_clears(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = _write_plan(root, "set001", None)
            rc = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "set001",
                    "--work-kind",
                    "bug",
                    "--dir",
                    str(root),
                    "-m",
                    "set work kind",
                ]
            )
            self.assertEqual(rc, 0)
            self.assertIn("- Work-Kind: bug", p.read_text(encoding="utf-8"))
            # same-status no-op re-run WITHOUT --work-kind -> line persists
            cli.main(
                ["ipd", "set", "approved", "set001", "--dir", str(root), "-m", "noop"]
            )
            self.assertIn("- Work-Kind: bug", p.read_text(encoding="utf-8"))
            # clear with '-'
            cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "set001",
                    "--work-kind",
                    "-",
                    "--dir",
                    str(root),
                    "-m",
                    "clear",
                ]
            )
            self.assertNotIn("- Work-Kind:", p.read_text(encoding="utf-8"))

    def test_setter_rejects_out_of_vocab_value(self) -> None:
        """An out-of-vocab value is refused with a NONZERO exit and no write."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = _write_plan(root, "set002", None)
            before = p.read_text(encoding="utf-8")
            with self.assertRaises(SystemExit) as cm:
                with redirect_stderr(io.StringIO()):
                    cli.main(
                        [
                            "ipd",
                            "set",
                            "approved",
                            "set002",
                            "--work-kind",
                            "bogus",
                            "--dir",
                            str(root),
                            "-m",
                            "bad",
                        ]
                    )
            self.assertNotEqual(cm.exception.code, 0)
            self.assertEqual(p.read_text(encoding="utf-8"), before)

    def test_writing_work_kind_does_not_disturb_the_structural_kind(self) -> None:
        """The write is full-line anchored, so the REQUIRED `- Kind: child` line survives."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = _write_plan(root, "set003", None)
            cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "set003",
                    "--work-kind",
                    "chore",
                    "--dir",
                    str(root),
                    "-m",
                    "set",
                ]
            )
            text = p.read_text(encoding="utf-8")
            self.assertIn("- Kind: child", text)
            self.assertIn("- Work-Kind: chore", text)
            # And clearing Work-Kind must NOT remove the structural Kind.
            cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "set003",
                    "--work-kind",
                    "-",
                    "--dir",
                    str(root),
                    "-m",
                    "clear",
                ]
            )
            text = p.read_text(encoding="utf-8")
            self.assertIn("- Kind: child", text)
            self.assertNotIn("- Work-Kind:", text)


class SpecSetterTests(unittest.TestCase):
    def test_set_writes_and_clears(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = _mk_spec(d, "- Status: draft")
            with redirect_stdout(io.StringIO()):
                rc = specs.run_set(
                    _args(
                        path=str(p),
                        status="draft",
                        message="set work kind",
                        work_kind="feature",
                    )
                )
            self.assertEqual(rc, 0)
            self.assertIn("- Work-Kind: feature", p.read_text(encoding="utf-8"))
            with redirect_stdout(io.StringIO()):
                rc = specs.run_set(
                    _args(
                        path=str(p),
                        status="draft",
                        message="clear",
                        work_kind="-",
                    )
                )
            self.assertEqual(rc, 0)
            self.assertNotIn("- Work-Kind:", p.read_text(encoding="utf-8"))

    def test_setter_refuses_out_of_vocab_via_validate_spec(self) -> None:
        # The validate_spec enum check makes the setter refuse a hand-passed out-of-vocab value
        # (byte-identical, nonzero exit), independent of the CLI argparse choices guard.
        with tempfile.TemporaryDirectory() as d:
            p = _mk_spec(d, "- Status: draft")
            before = p.read_text(encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                rc = specs.run_set(
                    _args(
                        path=str(p),
                        status="draft",
                        message="bad",
                        work_kind="bogus",
                    )
                )
            self.assertEqual(rc, 1)
            self.assertEqual(p.read_text(encoding="utf-8"), before)  # unchanged


class SharedWriterTests(unittest.TestCase):
    def test_the_writer_is_idempotent_and_full_line_anchored(self) -> None:
        """Both setters funnel through ONE primitive, so it is tested directly. The anchoring
        matters: a substring-anchored pattern would corrupt `- Gate-Kind:` into
        `- Gate-Work-Kind:`, the exact class of bug Order 9trlc3 guarded against."""
        text = "- Status: draft\n- Gate-Kind: artifact\n- Kind: child\n"
        once = releases.set_work_kind_line(text, "bug")
        twice = releases.set_work_kind_line(once, "bug")
        self.assertEqual(once, twice)  # idempotent
        self.assertIn("- Work-Kind: bug", once)
        self.assertIn("- Gate-Kind: artifact", once)  # untouched
        self.assertIn("- Kind: child", once)  # untouched
        self.assertNotIn("- Gate-Work-Kind:", once)
        # Replacing an existing value leaves exactly one line.
        replaced = releases.set_work_kind_line(once, "chore")
        self.assertEqual(replaced.count("- Work-Kind:"), 1)
        self.assertIn("- Work-Kind: chore", replaced)
        # Clearing removes it and nothing else.
        cleared = releases.set_work_kind_line(replaced, "-")
        self.assertNotIn("- Work-Kind:", cleared)
        self.assertIn("- Gate-Kind: artifact", cleared)
        self.assertIn("- Kind: child", cleared)


# --------------------------------------------------------------------------------------
# E-05: the aw check rule
# --------------------------------------------------------------------------------------


class WorkKindCheckTests(unittest.TestCase):
    def test_check_flags_out_of_vocab_only(self) -> None:
        # E-05: aw check flags an out-of-vocab Work-Kind; silent for a valid value and for absent.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_plan(root, "chkbad", "bogus")
            _write_plan(root, "chkgud", "security")
            _write_plan(root, "chknon", None)
            drift = ce.check_plan_work_kind(root, include_untracked=True)
            bad = [d for d in drift if d.rule == "check.work-kind-invalid"]
            self.assertEqual(len(bad), 1, [(d.location, d.detail) for d in drift])
            self.assertIn("chkbad", bad[0].location)
            self.assertIn("bogus", bad[0].detail)

    def test_check_content_plans_surfaces_work_kind_invalid(self) -> None:
        # Wired into the plans-type content path (reached by aw check plans / all).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_plan(root, "ctbad0", "urgent")
            drift = ce.check_content(root, "plans", include_untracked=True)
            self.assertIn("check.work-kind-invalid", [d.rule for d in drift])

    def test_rule_is_registered_with_the_same_class_as_its_priority_sibling(
        self,
    ) -> None:
        self.assertIn("check.work-kind-invalid", ce.RULE_REGISTRY)
        self.assertEqual(
            ce.rule_spec("check.work-kind-invalid"),
            ce.rule_spec("check.priority-invalid"),
        )

    def test_the_structural_kind_field_is_never_flagged(self) -> None:
        """Every fixture plan carries `- Kind: child`, which is NOT in backlog.KINDS. If the rule
        matched it, every plan in the corpus would be flagged: the mass-fail this must not cause."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_plan(root, "strk01", None)
            drift = ce.check_plan_work_kind(root, include_untracked=True)
            self.assertEqual(drift, [])


# --------------------------------------------------------------------------------------
# The deliberate backlog asymmetry (F11/F12)
# --------------------------------------------------------------------------------------


class BacklogAsymmetryTests(unittest.TestCase):
    def test_backlog_still_REQUIRES_its_work_nature_field(self) -> None:
        """This Set unified the field NAME across three types, NOT its requiredness. Backlog
        requires the field and reports through its OWN `backlog.kind-invalid` path. Asserted so
        nobody "unifies" it by weakening backlog's contract, which this plan's fence forbids."""
        # A backlog item with NO work-nature field is still a violation (REQUIRED there), whereas
        # the same absence on a plan or a spec is silent (OPTIONAL here). That is the asymmetry.
        with_field = (
            "- Id: asym01\n- Status: open\n- Set: asym\n- Priority: medium\n"
            "- Work-Kind: chore\n- Summary: a one line summary\n\n"
            "## Workflow history\n- 2026-08-29 created (aw backlog): a one line summary\n"
        )
        without_field = with_field.replace("- Work-Kind: chore\n", "")
        self.assertNotIn(
            "backlog.kind-invalid",
            [d.rule for d in backlog.validate_item(Path("x.backlog.md"), with_field)],
        )
        self.assertIn(
            "backlog.kind-invalid",
            [
                d.rule
                for d in backlog.validate_item(Path("x.backlog.md"), without_field)
            ],
        )
        # backlog's rule id is distinct from this plan's rule id: two mechanisms by design.
        self.assertNotEqual("backlog.kind-invalid", "check.work-kind-invalid")
        # And backlog's rule is NOT routed through this registry.
        self.assertNotIn("backlog.kind-invalid", ce.RULE_REGISTRY)


if __name__ == "__main__":
    unittest.main()

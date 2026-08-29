"""Tests for bklgrad Order 01 (v58bvy) E-06/E-07: a SPEC as a release-gate carrier.

Before this change `check_engine.find_from_backlog_plans` scanned plan IPDs ONLY, so a spec carrying
`- From-Backlog: <id6>` plus the SAME `- Blocks-Release:` was invisible to the HANDOFF route and its
backlog item could never legitimately close. A spec preserves the gate exactly as well as a plan, so
both are now accepted, and the `aw check` consistency rule covers specs too (else the checker and the
setter diverge).

The regression guard `test_plan_handoff_verdict_unchanged` matters: extending the scan must not alter
any existing plan-based verdict.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import check_engine

ITEM = """- Id: {id6}
- Status: open
- Blocks-Release: {gate}
- Set: tst
- Priority: high
- Kind: feature
- Summary: A gated test item.

## Workflow history
- 2026-08-29 created (test): A gated test item.
"""

SPEC = """# Spec: A test spec

- Date: 2026-08-29
- Status: approved
- Id: {id6}
- From-Backlog: {backlog_id6}
{gate}- Scope: Testing.

## Workflow history
- 2026-08-29 created (test): Testing.
"""

PLAN = """# IPD: A test plan

- Date: 2026-08-29
- Kind: child
- Concern: Testing.
- Scope: Testing.
- Scope-Paths: x
- Item-Dependencies: none
- From-Backlog: {backlog_id6}
{gate}- Status: to-review
- Set: tst
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-08-29 created (test): Testing.
"""


def _item(root: Path, id6: str, gate: str = "next") -> Path:
    d = root / ".aw" / "records" / "backlog" / "open"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260829-tst-01-{id6}-a-gated-test-item.backlog.md"
    p.write_text(ITEM.format(id6=id6, gate=gate), encoding="utf-8")
    return p


def _spec(root: Path, id6: str, backlog_id6: str, gate: str | None = "next") -> Path:
    d = root / ".aw" / "records" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260829-{id6}-01-{id6}-a-test-spec.spec.md"
    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    p.write_text(
        SPEC.format(id6=id6, backlog_id6=backlog_id6, gate=gate_line), encoding="utf-8"
    )
    return p


def _plan(root: Path, id6: str, backlog_id6: str, gate: str | None = "next") -> Path:
    d = root / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260829-tst-01-{id6}-a-test-plan.ipd.md"
    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    p.write_text(
        PLAN.format(id6=id6, backlog_id6=backlog_id6, gate=gate_line), encoding="utf-8"
    )
    return p


class SpecFinderTests(unittest.TestCase):
    def test_find_from_backlog_specs_finds_the_spec(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "aaa111")
            _spec(root, "sss111", "aaa111")
            hits = check_engine.find_from_backlog_specs(root, "aaa111")
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0][1], "next")

    def test_artifacts_finder_unions_plans_and_specs(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "bbb222")
            _plan(root, "ppp222", "bbb222")
            _spec(root, "sss222", "bbb222")
            self.assertEqual(
                len(check_engine.find_from_backlog_artifacts(root, "bbb222")), 2
            )

    def test_plans_finder_still_ignores_specs(self):
        """The plan-only function must keep its exact previous behavior."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "ccc333")
            _spec(root, "sss333", "ccc333")
            self.assertEqual(check_engine.find_from_backlog_plans(root, "ccc333"), [])


class SpecHandoffVerdictTests(unittest.TestCase):
    def test_spec_only_handoff_is_legitimate(self):
        """The core fix: a spec-first graduation is now closable."""
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _item(root, "ddd444")
            _spec(root, "sss444", "ddd444")
            v = check_engine.evaluate_blocking_close(root, p, "done")
            self.assertTrue(v.legitimate, v.reason)
            self.assertEqual(v.severity, "ok")
            self.assertIn("handed off", v.reason)

    def test_spec_with_mismatched_gate_still_fails_closed(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _item(root, "eee555", gate="next")
            _spec(root, "sss555", "eee555", gate="v9z9z9")
            v = check_engine.evaluate_blocking_close(root, p, "done")
            self.assertFalse(v.legitimate, "a mismatched gate must not satisfy HANDOFF")
            self.assertEqual(v.severity, "error")

    def test_spec_with_no_gate_still_fails_closed(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _item(root, "fff666")
            _spec(root, "sss666", "fff666", gate=None)
            v = check_engine.evaluate_blocking_close(root, p, "done")
            self.assertFalse(v.legitimate)

    def test_plan_handoff_verdict_unchanged(self):
        """REGRESSION GUARD: plan-based HANDOFF must behave exactly as before."""
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _item(root, "ggg777")
            _plan(root, "ppp777", "ggg777")
            v = check_engine.evaluate_blocking_close(root, p, "done")
            self.assertTrue(v.legitimate, v.reason)
            self.assertEqual(v.severity, "ok")

    def test_no_carrier_at_all_fails_closed(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _item(root, "hhh888")
            v = check_engine.evaluate_blocking_close(root, p, "done")
            self.assertFalse(v.legitimate)
            self.assertEqual(v.severity, "error")


class SpecGateMismatchRuleTests(unittest.TestCase):
    """E-07: the consistency rule must cover specs, not just plans."""

    def test_spec_gate_mismatch_is_flagged(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "iii999", gate="next")
            _spec(root, "sss999", "iii999", gate="v9z9z9")
            drift = check_engine.check_release_gate_consistency(root)
            rules = [d.rule for d in drift]
            self.assertIn("check.from-backlog-gate-mismatch", rules)

    def test_matching_spec_gate_is_not_flagged(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "jjj000", gate="next")
            _spec(root, "ssj000", "jjj000", gate="next")
            drift = check_engine.check_release_gate_consistency(root)
            self.assertEqual([d.rule for d in drift], [])

    def test_plan_gate_mismatch_still_flagged(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "kkk111", gate="next")
            _plan(root, "ppk111", "kkk111", gate="v9z9z9")
            drift = check_engine.check_release_gate_consistency(root)
            self.assertIn("check.from-backlog-gate-mismatch", [d.rule for d in drift])

    def test_mismatch_detail_names_the_artifact_kind(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "lll222", gate="next")
            _spec(root, "ssl222", "lll222", gate="v9z9z9")
            drift = check_engine.check_release_gate_consistency(root)
            hits = [d for d in drift if d.rule == "check.from-backlog-gate-mismatch"]
            self.assertTrue(hits)
            self.assertIn("spec", hits[0].detail)


class LiveRepoTests(unittest.TestCase):
    """The real motivating case: spec c4gd2h carries the gate for kjzlgw."""

    def test_c4gd2h_is_recognized_as_a_carrier_for_kjzlgw(self):
        repo = Path(__file__).resolve().parents[1]
        specs = check_engine.find_from_backlog_specs(repo, "kjzlgw")
        names = [p.name for p, _ in specs]
        self.assertTrue(
            any("c4gd2h" in n for n in names),
            f"expected c4gd2h among {names}",
        )
        self.assertTrue(all(gate == "next" for _p, gate in specs))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

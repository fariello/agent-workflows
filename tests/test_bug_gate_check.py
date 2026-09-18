"""Tests for nobugship rgaasb: `check.live-bug-ungated` plus the `from-backlog-gate-mismatch` narrowing.

TWO SHIPPED BEHAVIORS ARE PINNED HERE AND THEY ARE DELIBERATELY IN ONE FILE, because the second
exists only to make the first landable:

1. `check.live-bug-ungated` (NEW): a LIVE (`open`/`blocked`/`graduated`) `Work-Kind: bug` backlog item
   carrying no `- Blocks-Release:` is a finding. The enforcement half of the maintainer's standing
   rule "we don't ship known bugs" (written in AGENTS.md by sibling `zqs0px`, defaulted at creation by
   sibling `di08i9`).

2. `check.from-backlog-gate-mismatch` NARROWED to a LIVE carrier (parent `qmgn12` OQ-03, maintainer
   ruling 2026-09-12). Backfilling every live bug's gate would otherwise newly flag every carrier
   plan, including plans in `executed/` that AGENTS.md forbids editing in place. The ruling restates
   the rule as the one-way obligation it already implements and skips a terminal carrier.

THE ZERO-FINDING DIRECTION IS ASSERTED EXPLICITLY (`test_gated_carrier_under_ungated_item_is_clean`)
and that is the durable half of the ruling. A gated carrier under an UNGATED item is currently
unreachable BY CONSTRUCTION (the `item_gate` map is populated only for a gated item), so nothing today
would notice if a refactor made the rule symmetric. Without this test the reframing is undefended.

Every test builds its OWN temp repo; none reads the live checkout.
"""

from __future__ import annotations

import inspect
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional

from agent_workflows import check_engine

ITEM = """- Id: {id6}
- Status: {status}
- Set: tst
- Priority: medium
- Work-Kind: {work_kind}
- Summary: A test item.
{gate}
## Workflow history
- 2026-09-18 created (test): A test item.
"""

PLAN = """# IPD: A test plan

- Date: 2026-09-18
- Kind: child
- Concern: Testing.
- Scope: Testing.
- Scope-Paths: x
- Item-Dependencies: none
- From-Backlog: {backlog_id6}
{gate}- Status: {status}
- Set: tst
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-18 created (test): Testing.
"""

SPEC = """# Spec: A test spec

- Date: 2026-09-18
- Status: approved
- Id: {id6}
- From-Backlog: {backlog_id6}
{gate}- Scope: Testing.

## Workflow history
- 2026-09-18 created (test): Testing.
"""


def _item(
    root: Path,
    id6: str,
    *,
    status: str = "open",
    work_kind: str = "bug",
    gate: Optional[str] = None,
) -> Path:
    """A backlog item in the status directory matching its `- Status:` (as the real tree does)."""
    d = root / ".aw" / "records" / "backlog" / status
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260918-tst-01-{id6}-a-test-item.backlog.md"
    p.write_text(
        ITEM.format(
            id6=id6,
            status=status,
            work_kind=work_kind,
            gate=(f"- Blocks-Release: {gate}\n" if gate else ""),
        ),
        encoding="utf-8",
    )
    return p


def _plan(
    root: Path,
    id6: str,
    backlog_id6: str,
    *,
    gate: Optional[str] = None,
    disposition: str = "pending",
    status: str = "to-review",
) -> Path:
    d = root / ".aw" / "records" / "plans" / disposition
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260918-tst-01-{id6}-a-test-plan.ipd.md"
    p.write_text(
        PLAN.format(
            id6=id6,
            backlog_id6=backlog_id6,
            status=status,
            gate=(f"- Blocks-Release: {gate}\n" if gate else ""),
        ),
        encoding="utf-8",
    )
    return p


def _spec(
    root: Path, id6: str, backlog_id6: str, *, gate: Optional[str] = None
) -> Path:
    d = root / ".aw" / "records" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260918-{id6}-01-{id6}-a-test-spec.spec.md"
    p.write_text(
        SPEC.format(
            id6=id6,
            backlog_id6=backlog_id6,
            gate=(f"- Blocks-Release: {gate}\n" if gate else ""),
        ),
        encoding="utf-8",
    )
    return p


def _rules(drift) -> List[str]:
    return [d.rule for d in drift]


RULE = "check.live-bug-ungated"
MISMATCH = "check.from-backlog-gate-mismatch"


class LiveBugGateBehaviorTests(unittest.TestCase):
    """E-03's six behavioral cases for the new rule."""

    def test_live_gateless_bug_is_flagged(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "aaa111", status="open", work_kind="bug", gate=None)
            drift = check_engine.check_live_bug_gate(root)
            self.assertEqual(_rules(drift), [RULE])

    def test_gated_bug_is_clean(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "aaa222", status="open", work_kind="bug", gate="next")
            self.assertEqual(check_engine.check_live_bug_gate(root), [])

    def test_done_gateless_bug_is_clean(self):
        """A closed bug shipped or did not; asserting a gate now would rewrite history."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "aaa333", status="done", work_kind="bug", gate=None)
            self.assertEqual(check_engine.check_live_bug_gate(root), [])

    def test_parked_gateless_bug_is_clean(self):
        """A parked maybe is uncommitted work the attention view hides."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "aaa444", status="parked", work_kind="bug", gate=None)
            self.assertEqual(check_engine.check_live_bug_gate(root), [])

    def test_non_bug_gateless_item_is_clean(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            for kind in ("feature", "chore", "followup", "security"):
                _item(root, f"bb{kind[:4]}", status="open", work_kind=kind, gate=None)
            self.assertEqual(check_engine.check_live_bug_gate(root), [])

    def test_graduated_gateless_bug_with_gated_carrier_is_clean(self):
        """HANDOFF: the gate lives on the From-Backlog carrier, which AGENTS.md accepts."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "aaa555", status="graduated", work_kind="bug", gate=None)
            _plan(root, "ppp555", "aaa555", gate="next")
            self.assertEqual(check_engine.check_live_bug_gate(root), [])


class LiveBugGateEdgeTests(unittest.TestCase):
    """The distinctions the six cases above do not by themselves pin."""

    def test_blocked_is_a_live_status_and_is_flagged(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "ccc111", status="blocked", work_kind="bug", gate=None)
            self.assertEqual(_rules(check_engine.check_live_bug_gate(root)), [RULE])

    def test_graduated_gateless_bug_with_UNGATED_carrier_is_still_flagged(self):
        """A carrier that dropped the gate does not satisfy the rule; that is the leak itself."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "ccc222", status="graduated", work_kind="bug", gate=None)
            _plan(root, "ppp222", "ccc222", gate=None)
            self.assertEqual(_rules(check_engine.check_live_bug_gate(root)), [RULE])

    def test_a_spec_is_an_equally_valid_carrier(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "ccc333", status="graduated", work_kind="bug", gate=None)
            _spec(root, "sss333", "ccc333", gate="next")
            self.assertEqual(check_engine.check_live_bug_gate(root), [])

    def test_open_item_with_gated_carrier_is_also_exempt(self):
        """The discriminator is the CARRIER's gate, not the item's status: measured on the real tree,
        two `open` items have carriers, so keying the exemption on `graduated` would treat identical
        evidence differently."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "ccc444", status="open", work_kind="bug", gate=None)
            _plan(root, "ppp444", "ccc444", gate="next")
            self.assertEqual(check_engine.check_live_bug_gate(root), [])

    def test_legacy_kind_spelling_is_honored(self):
        """`parse_item`'s dual-read window means a legacy `- Kind: bug` item is still caught."""
        with TemporaryDirectory() as td:
            root = Path(td)
            d = root / ".aw" / "records" / "backlog" / "open"
            d.mkdir(parents=True, exist_ok=True)
            (d / "20260918-tst-01-ccc555-legacy.backlog.md").write_text(
                "- Id: ccc555\n- Status: open\n- Priority: medium\n- Kind: bug\n"
                "- Summary: A legacy-spelled item.\n",
                encoding="utf-8",
            )
            self.assertEqual(_rules(check_engine.check_live_bug_gate(root)), [RULE])

    def test_finding_cites_the_written_rule_and_teaches_the_fix(self):
        """The fix must live in the STRUCTURED `recovery` field, not in `detail`: `recovery` is what
        the human renderer prints as the Fix line and what the machine record carries. A fix written
        into `detail` is invisible where a reader looks for it (driven: the generic "inspect ...
        frontmatter" fallback was printed instead)."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "ccc666", status="graduated", work_kind="bug", gate=None)
            (hit,) = check_engine.check_live_bug_gate(root)
            self.assertIn("Every live bug gates the next release", hit.detail)
            self.assertIn(
                "aw backlog set graduated ccc666 --blocks-release next", hit.recovery
            )
            self.assertEqual(hit.severity, "error")
            self.assertIn("no Blocks-Release", hit.observed)
            self.assertIn("Blocks-Release", hit.required)


class LiveBugGateReuseTests(unittest.TestCase):
    """E-03's reuse assertions, REPLACING the plan's original anti-fork assertion.

    The plan asked for proof that the predicate consumes `evaluate_blocking_close`. It does not and
    cannot (see `test_evaluate_blocking_close_cannot_answer_the_open_direction`), so asserting that
    would pin the wrong design in place. These assert the reuse that actually matters: the handoff
    definition has ONE owner, and the metadata regexes were not duplicated.
    """

    def test_predicate_consumes_the_shared_carrier_index(self):
        src = inspect.getsource(check_engine.check_live_bug_gate)
        self.assertIn("_from_backlog_carrier_index", src)

    def test_both_consumers_use_the_one_carrier_index(self):
        """The mismatch rule and the new rule must not each own a walk of the plans/specs trees."""
        for fn in (
            check_engine.check_live_bug_gate,
            check_engine.check_release_gate_consistency,
        ):
            with self.subTest(fn=fn.__name__):
                self.assertIn("_from_backlog_carrier_index", inspect.getsource(fn))

    def test_the_carrier_index_is_the_only_place_the_walk_is_written(self):
        """Neither consumer may re-derive the carrier set with its own iterator loop."""
        for fn in (
            check_engine.check_live_bug_gate,
            check_engine.check_release_gate_consistency,
        ):
            with self.subTest(fn=fn.__name__):
                src = inspect.getsource(fn)
                self.assertNotIn("_iter_plan_ipds", src)
                self.assertNotIn("_iter_spec_records", src)

    def test_no_second_copy_of_the_blocks_release_regex(self):
        """The module must own exactly ONE compiled `- Blocks-Release:` metadata pattern."""
        src = Path(check_engine.__file__).read_text(encoding="utf-8")
        self.assertEqual(src.count('r"(?m)^- Blocks-Release:'), 1)

    def test_predicate_does_not_fork_the_live_status_vocabulary(self):
        """LIVE is derived from the shared backlog vocabularies, not a fourth hardcoded list."""
        src = inspect.getsource(check_engine.check_live_bug_gate)
        self.assertIn("_backlog.STATUSES", src)
        self.assertIn("_GATE_DEFAULT_SKIP_STATUSES", src)
        self.assertIn("GATE_DEFAULT_KINDS", src)

    def test_the_live_set_agrees_with_the_creation_default(self):
        """The statuses this rule REQUIRES a gate on must be exactly the ones child 02's creation
        default APPLIES a gate to, or the checker and the setter teach different rules."""
        from agent_workflows import backlog

        live = backlog.STATUSES - backlog._GATE_DEFAULT_SKIP_STATUSES
        self.assertEqual(live, {"open", "blocked", "graduated"})

    def test_evaluate_blocking_close_cannot_answer_the_open_direction(self):
        """The NON-USE proof. Every branch of that predicate keys on the gate being PRESENT, so on an
        ungated item it returns legitimate/ok whichever transition is asked about."""
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _item(root, "ddd111", status="open", work_kind="bug", gate=None)
            done = check_engine.evaluate_blocking_close(root, p, "done")
            self.assertTrue(done.legitimate)
            self.assertEqual(done.severity, "ok")
            self.assertEqual(done.reason, "no release gate to preserve")
            other = check_engine.evaluate_blocking_close(root, p, "open")
            self.assertTrue(other.legitimate)
            self.assertEqual(other.severity, "ok")
            self.assertEqual(other.reason, "unchecked transition")


class LiveBugGateRegistrationTests(unittest.TestCase):
    """E-02: the rule must be REGISTERED, or it silently falls back to `_DEFAULT_RULESPEC` with an
    empty invariant and the I-07 trace is lost."""

    def test_registered_at_error_under_I07(self):
        spec = check_engine.RULE_REGISTRY[RULE]
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec.invariant, "I-07")

    def test_registered_as_a_deterministic_repository_invariant(self):
        spec = check_engine.RULE_REGISTRY[RULE]
        self.assertEqual(spec.assurance, check_engine.ASSURANCE_REPOSITORY)
        self.assertEqual(spec.determinism, check_engine.DET_DETERMINISTIC)

    def test_shares_its_invariant_with_the_rest_of_the_I07_family(self):
        for sibling in (
            "check.blocking-item-closed-without-gate",
            MISMATCH,
            "check.blocks-release-dangling",
            "check.from-backlog-dangling",
        ):
            with self.subTest(sibling=sibling):
                self.assertEqual(
                    check_engine.RULE_REGISTRY[sibling].invariant,
                    check_engine.RULE_REGISTRY[RULE].invariant,
                )


class LiveBugGateSeamTests(unittest.TestCase):
    """THE SEAM TEST. Review measured that calling a predicate directly passes while the shipped
    command reports nothing, which is precisely how an unwired rule ships green. So drive
    `check_types`, not the predicate."""

    def test_full_sweep_reports_the_rule(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "eee111", status="open", work_kind="bug", gate=None)
            self.assertIn(RULE, _rules(check_engine.check_types(root, ["all"])))

    def test_backlog_type_scope_does_NOT_report_it(self):
        """A STATED cost, asserted so it is a decision rather than a surprise: the whole I-07 family
        rides the once-per-full-sweep seam, so `aw check backlog` is blind to it. If a later change
        wires the family into the backlog content path, this test SHOULD fail and be updated."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "eee222", status="open", work_kind="bug", gate=None)
            self.assertNotIn(RULE, _rules(check_engine.check_types(root, ["backlog"])))

    def test_whole_tree_rule_is_absent_from_the_precommit_aggregator(self):
        """It must NOT reach `check_commit_invariants`: every rule there is commit- or receipt-scoped,
        and a whole-tree rule in a pre-commit gate would refuse a commit because ANOTHER party's item
        elsewhere in the tree is ungated."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "eee333", status="open", work_kind="bug", gate=None)
            self.assertNotIn(RULE, _rules(check_engine.check_commit_invariants(root)))

    def test_clean_tree_is_silent(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "eee444", status="open", work_kind="bug", gate="next")
            self.assertNotIn(RULE, _rules(check_engine.check_types(root, ["all"])))


class MismatchNarrowingTests(unittest.TestCase):
    """The OQ-03 ruling: `check.from-backlog-gate-mismatch` fires only for a LIVE carrier.

    Each assertion here FAILS against pre-change code, which is the point: a narrowing that passes
    before and after proves nothing.
    """

    def test_live_pending_carrier_still_flagged(self):
        """The direction that must KEEP firing: a live plan that dropped its item's gate."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "fff111", status="graduated", work_kind="bug", gate="next")
            _plan(root, "ppf111", "fff111", gate=None, disposition="pending")
            drift = check_engine.check_release_gate_consistency(root)
            self.assertEqual(_rules(drift), [MISMATCH])

    def test_executed_carrier_is_skipped(self):
        """FAILS against pre-change code, which flagged it and demanded an edit AGENTS.md forbids."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "fff222", status="graduated", work_kind="bug", gate="next")
            _plan(
                root,
                "ppf222",
                "fff222",
                gate=None,
                disposition="executed",
                status="executed",
            )
            self.assertEqual(check_engine.check_release_gate_consistency(root), [])

    def test_superseded_and_not_executed_carriers_are_skipped(self):
        """The ruled rationale ("work is DONE, no future release to gate") holds for every terminal
        disposition, which is why the shipped `is_retired` predicate is used rather than the narrower
        `_EXECUTED_SEGMENT` literal."""
        for disposition, status in (
            ("superseded", "superseded"),
            ("not-executed", "not-executed"),
        ):
            with self.subTest(disposition=disposition):
                with TemporaryDirectory() as td:
                    root = Path(td)
                    _item(
                        root, "fff333", status="graduated", work_kind="bug", gate="next"
                    )
                    _plan(
                        root,
                        "ppf333",
                        "fff333",
                        gate=None,
                        disposition=disposition,
                        status=status,
                    )
                    self.assertEqual(
                        check_engine.check_release_gate_consistency(root), []
                    )

    def test_gated_carrier_under_ungated_item_is_clean(self):
        """THE ZERO-FINDING DIRECTION, and the durable half of the ruling.

        The maintainer's pivot question was "why would we care if a plan is blocking but the backlog
        is not?" The answer is that we would not: a plan can discover DURING execution that it gates a
        release for reasons its originating item never knew, and forbidding that would punish the plan
        for being better informed than its own provenance. What the rule protects is the opposite and
        narrower thing, a DROPPED handoff.

        This is currently unreachable BY CONSTRUCTION (the `item_gate` map is populated only for a
        GATED item), so without this assertion nothing would notice if a refactor made the rule
        symmetric again.
        """
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "fff444", status="graduated", work_kind="bug", gate=None)
            _plan(root, "ppf444", "fff444", gate="next", disposition="pending")
            self.assertEqual(
                [
                    d
                    for d in check_engine.check_release_gate_consistency(root)
                    if d.rule == MISMATCH
                ],
                [],
            )

    def test_matching_gates_are_clean(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "fff555", status="graduated", work_kind="bug", gate="next")
            _plan(root, "ppf555", "fff555", gate="next")
            self.assertEqual(check_engine.check_release_gate_consistency(root), [])

    def test_live_spec_carrier_still_flagged(self):
        """The spec side of the scan must survive the narrowing (bklgrad v58bvy E-07)."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "fff666", status="graduated", work_kind="bug", gate="next")
            _spec(root, "ssf666", "fff666", gate="v9z9z9")
            drift = check_engine.check_release_gate_consistency(root)
            self.assertEqual(_rules(drift), [MISMATCH])
            self.assertIn("spec", drift[0].detail)

    def test_narrowing_uses_the_shipped_terminal_predicate(self):
        """Not a fresh path test, per the ruling."""
        src = inspect.getsource(check_engine.check_release_gate_consistency)
        self.assertIn("is_retired(", src)

    def test_dangling_from_backlog_is_still_another_rules_job(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _plan(root, "ppf777", "zzzzzz", gate="next")
            self.assertEqual(check_engine.check_release_gate_consistency(root), [])


class BackfillEndStateTests(unittest.TestCase):
    """The two rules must be exercised TOGETHER on ONE tree state, which is the cross-check the
    parent Set requires: satisfying the new rule on a graduated item is what VIOLATED the old one."""

    def test_backfilling_an_item_with_a_terminal_carrier_reaches_zero(self):
        """The case that blocked the Set. Gating the item used to flag its `executed/` carrier, which
        had no tooled remedy; with the narrowing, both rules are clean on the same tree."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "ggg111", status="graduated", work_kind="bug", gate="next")
            _plan(
                root,
                "ppg111",
                "ggg111",
                gate=None,
                disposition="executed",
                status="executed",
            )
            drift = check_engine.check_types(root, ["all"])
            for rule in (RULE, MISMATCH):
                with self.subTest(rule=rule):
                    self.assertNotIn(rule, _rules(drift))

    def test_backfilling_an_item_with_a_live_carrier_needs_the_carrier_co_updated(self):
        """The other half: a LIVE carrier is NOT skipped, so the backfill genuinely has to co-update
        it. Asserted so the remedy is not mistaken for unnecessary."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "ggg222", status="graduated", work_kind="bug", gate="next")
            carrier = _plan(root, "ppg222", "ggg222", gate=None, disposition="pending")
            before = _rules(check_engine.check_types(root, ["all"]))
            self.assertIn(MISMATCH, before)
            self.assertNotIn(RULE, before)
            carrier.write_text(
                carrier.read_text(encoding="utf-8").replace(
                    "- Status: to-review", "- Blocks-Release: next\n- Status: to-review"
                ),
                encoding="utf-8",
            )
            after = _rules(check_engine.check_types(root, ["all"]))
            self.assertNotIn(MISMATCH, after)
            self.assertNotIn(RULE, after)


if __name__ == "__main__":
    unittest.main()

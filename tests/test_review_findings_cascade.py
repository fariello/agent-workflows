"""Tests for revgate Order 03 (7nkcgp): a findings-blocked plan does not release its dependents.

Order 02 (`plqjt7`) made an unescalated gating finding REPORTABLE. This Order makes it BLOCKING for
anything that depends on the plan: an `executed:` edge is no longer satisfied by file location alone.

Covers:
* V-01 - the block itself, on BOTH resolution paths in `dependency_status` (the out-of-queue
  `bucket == "executed"` path AND the in-queue `EXECUTION_SUCCESS_STATES` path), plus proof the
  dependent is `dependency-blocked` and starts NO session, and that resolving the finding un-blocks it.
* V-02 - both host drivers decide IDENTICALLY through ONE shared predicate that lives in a NON-runner
  module, with no runner-to-runner import.
* V-03 - `aw check`'s evaluator reports the condition under a NEW, accurately-named, REGISTERED rule id
  (reuse of the identity verdicts `dangling`/`ambiguous` was evaluated and rejected).
* V-04 - the `dependency-blocked` event payload and the run report name the ROOT CAUSE (finding id +
  severity) and the exact recovery command, additively (the flat `dependencies` list keeps its shape).
* V-05 - transitive cascade (A -> B -> C), the threshold matrix, `off` disabling, and recovery via the
  REAL `--retry-incomplete` flag (a BARE resume does NOT re-queue, so a bare-resume recovery test would
  pass vacuously and enshrine a false claim).
* V-06 - cross-surface non-evasion: the SAME fixture is refused by every authority surface.
* V-07 - the `/exec-set` Set compiler treats a findings-blocked child as a gate and blocks its
  transitive descendants, reusing the EXISTING `_propagate_blocked` cascade, while leaving an
  independent sibling runnable.
* V-08 - the ACTUAL recovery behavior: still blocked after a bare resume, re-queued with
  `--retry-incomplete`, and the runner's re-queue default is UNCHANGED.

EVERY fixture is an ISOLATED tmp repo. No assertion reads this repository's live `.aw/records/runs/`,
live plans, or live `.aw/config/project.json`: asserting against live state is a known defect class
here (pending plan `i79rgh`, Order testinvoke-02), and a threshold assertion that read the live config
would be order-dependent and would break the moment a maintainer set the key.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd as agy
from agent_workflows import check_engine as ce
from agent_workflows import ipd_set_plan as sp
from agent_workflows import oc_runipd as oc
from agent_workflows import review_findings as rf

DEP_RULE = "check.ipd-dependency-findings-blocked"

#: The two host drivers, exercised through the SAME assertions so neither can drift.
DRIVERS = (("oc", oc), ("agy", agy))


# --------------------------------------------------------------------------------------
# Isolated fixture builders
# --------------------------------------------------------------------------------------


def _src(mod) -> str:
    """Read a module's own source (used to assert structural properties, never behavior)."""
    return Path(str(mod.__file__)).read_text(encoding="utf-8")


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="aw_revgate03_"))
    for lane in ("pending", "executed", "superseded", "not-executed", "reusable"):
        (d / ".aw" / "records" / "plans" / lane).mkdir(parents=True)
    (d / ".aw" / "records" / "reviews").mkdir(parents=True)
    (d / ".aw" / "config").mkdir(parents=True)
    return d


def _set_threshold(repo: Path, value: str | None) -> None:
    """Write (or remove) `review_findings_gate` in the FIXTURE's project.json (never the live one)."""
    pj = repo / ".aw" / "config" / "project.json"
    if value is None:
        if pj.exists():
            pj.unlink()
        return
    pj.write_text(
        json.dumps({"review_findings_gate": {"block_at": value}}), encoding="utf-8"
    )


def _plan(
    repo: Path,
    id6: str,
    *,
    lane: str = "executed",
    status: str = "executed",
    order: int = 1,
    deps: str = "none",
    set_id: str = "demo",
) -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / lane
        / f"20260829-{set_id}-{order:02d}-{id6}-cascade-fixture.ipd.md"
    )
    p.write_text(
        f"# IPD: cascade fixture {id6}\n\n"
        f"- Date: 2026-08-29\n- Kind: child\n- Scope-Paths: x.py\n"
        f"- Item-Dependencies: {deps}\n- Status: {status}\n- Set: {set_id}\n"
        f"- Order: {order}\n- Id: {id6}\n\n"
        f"## Workflow history\n- 2026-08-29 draft (t): created.\n\n"
        f"## Goal\ng\n\n"
        f"## Detailed Implementation Checklist (TODO)\n\n"
        f"- [ ] E-01 do the thing\n  - Depends on: none\n"
        f"  - Expected outcome: done\n  - Execution state: pending\n\n"
        f"## Validation and cross-check (verify before reporting done)\n\n"
        f"- [ ] V-01 validates E-01\n  - Required evidence: paste it\n"
        f"  - Observed evidence:\n  - Result: pending\n",
        encoding="utf-8",
    )
    return p


def _finding(
    fid: str = "F-1", severity: str = "high", decision: str = "open"
) -> rf.Finding:
    return rf.Finding(
        fid,
        severity,
        "IN-SCOPE",
        "rubric",
        "x.py:1",
        "the finding text",
        "Overall:Low",
        decision,
        "the resolution",
    )


def _review(repo: Path, id6: str, *, rounds=None) -> Path:
    if rounds is None:
        rounds = [rf.Round(1, (_finding(),), ())]
    return rf.write_review(
        repo
        / ".aw"
        / "records"
        / "reviews"
        / f"20260829-demo-01-{id6}-cascade.review.md",
        plan_id=id6,
        reviewed_at="2026-08-29",
        reviewer="test",
        verdict="REVIEWED - OPEN QUESTIONS",
        rounds=rounds,
    )


def _state(repo: Path, queue: list[dict]) -> dict:
    return {"repo": str(repo), "run_id": "run-test", "queue": queue}


def _item(
    id6: str, deps: list[str], *, status: str = "queued", position: int = 1
) -> dict:
    return {
        "id6": id6,
        "position": position,
        "setid": "demo",
        "status": status,
        "action": "execute",
        "dependencies": deps,
    }


class _RepoCase(unittest.TestCase):
    def setUp(self):
        self.repo = _mkrepo()

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)


# --------------------------------------------------------------------------------------
# V-01 / V-02: the block itself, on both resolution paths, in both drivers
# --------------------------------------------------------------------------------------


class BlockingTests(_RepoCase):
    def test_out_of_queue_executed_dep_with_gating_finding_is_unsatisfied(self):
        """The `bucket == 'executed'` path: location alone must no longer satisfy the edge."""
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(self.repo, "depaaa")
        state = _state(self.repo, [_item("itemaa", ["depaaa"])])
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                satisfied, missing = drv.dependency_status(state["queue"][0], state)
                self.assertFalse(satisfied)
                self.assertEqual(missing, ["depaaa"])

    def test_in_queue_successful_dep_with_gating_finding_is_unsatisfied(self):
        """The `EXECUTION_SUCCESS_STATES` path: the gate must not be evadable by being in-queue.

        Without this second call site the gate would depend on whether the target happens to be part
        of the same run, which is exactly the kind of path-dependent hole this Set exists to remove.
        """
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(self.repo, "depaaa")
        state = _state(
            self.repo,
            [
                _item("depaaa", [], status="executed", position=1),
                _item("itemaa", ["depaaa"], position=2),
            ],
        )
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                satisfied, missing = drv.dependency_status(state["queue"][1], state)
                self.assertFalse(satisfied)
                self.assertEqual(missing, ["depaaa"])

    def test_clean_executed_dep_is_satisfied(self):
        """Control: with NO review artifact at all, the pre-Order-03 behavior is unchanged."""
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        state = _state(self.repo, [_item("itemaa", ["depaaa"])])
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                satisfied, missing = drv.dependency_status(state["queue"][0], state)
                self.assertTrue(satisfied)
                self.assertEqual(missing, [])

    def test_resolved_finding_unblocks_the_dependent(self):
        """Same fixture, finding marked `fixed`: the dependent becomes runnable again."""
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(
            self.repo,
            "depaaa",
            rounds=[rf.Round(1, (_finding(decision="fixed"),), ())],
        )
        state = _state(self.repo, [_item("itemaa", ["depaaa"])])
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                satisfied, _missing = drv.dependency_status(state["queue"][0], state)
                self.assertTrue(satisfied)

    def test_later_round_fix_does_not_block(self):
        """Current-round semantics: a HIGH raised in round 1 and fixed in round 2 must not block."""
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(
            self.repo,
            "depaaa",
            rounds=[
                rf.Round(1, (_finding(decision="open"),), ()),
                rf.Round(2, (_finding(decision="fixed"),), ()),
            ],
        )
        state = _state(self.repo, [_item("itemaa", ["depaaa"])])
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                self.assertTrue(drv.dependency_status(state["queue"][0], state)[0])

    def test_malformed_review_blocks_rather_than_being_silently_skipped(self):
        """A present-but-unparseable artifact is an ERROR, not an absence; skipping it is the hole."""
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        (
            self.repo
            / ".aw"
            / "records"
            / "reviews"
            / "20260829-demo-01-depaaa-cascade.review.md"
        ).write_text(
            "# Review\n\n- Plan-Id: depaaa\n\n## Round 1\n\n| # | Severity |\n|---|---|\n| F-1 |\n",
            encoding="utf-8",
        )
        state = _state(self.repo, [_item("itemaa", ["depaaa"])])
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                self.assertFalse(drv.dependency_status(state["queue"][0], state)[0])

    def test_review_action_item_is_not_findings_gated(self):
        """Only an `executed:` edge asserts completed-and-verified work, so only it is gated."""
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(self.repo, "depaaa")
        item = _item("itemaa", ["depaaa"])
        item["action"] = "review"
        state = _state(self.repo, [item])
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                self.assertTrue(drv.dependency_status(state["queue"][0], state)[0])


class SharedPredicateTests(_RepoCase):
    def test_predicate_is_defined_once_in_a_non_runner_module(self):
        """One definition, in `review_findings`, consumed by both hosts and by check_engine."""
        self.assertEqual(
            rf.plan_gating_blocks.__module__, "agent_workflows.review_findings"
        )
        # Both driver wrappers exist and are thin delegates (no severity logic of their own).
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                self.assertTrue(hasattr(drv, "_findings_block_reason"))
                src = _src(drv)
                self.assertIn("plan_gating_blocks", src)
                # The severity comparison must NOT be reimplemented in a runner.
                self.assertNotIn("_SEVERITY_RANK", src)

    def test_no_runner_to_runner_import(self):
        """A runner-to-runner import would be a new coupling colliding with the rununify extraction."""
        oc_src = _src(oc)
        agy_src = _src(agy)
        self.assertNotIn("import agy_runipd", oc_src)
        self.assertNotIn("import oc_runipd", agy_src)

    def test_both_drivers_agree_on_the_same_fixture(self):
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(self.repo, "depaaa")
        state = _state(self.repo, [_item("itemaa", ["depaaa"])])
        results = {
            name: drv.dependency_status(state["queue"][0], state)
            for name, drv in DRIVERS
        }
        self.assertEqual(results["oc"], results["agy"])
        self.assertEqual(results["oc"], (False, ["depaaa"]))


# --------------------------------------------------------------------------------------
# V-05: thresholds, `off`, and the transitive cascade
# --------------------------------------------------------------------------------------


class ThresholdTests(_RepoCase):
    def _blocked_at(self, threshold: str | None, severity: str) -> bool:
        _set_threshold(self.repo, threshold)
        _plan(self.repo, "depaaa")
        _review(
            self.repo,
            "depaaa",
            rounds=[rf.Round(1, (_finding(severity=severity),), ())],
        )
        state = _state(self.repo, [_item("itemaa", ["depaaa"])])
        satisfied, _ = oc.dependency_status(state["queue"][0], state)
        return not satisfied

    def test_medium_does_not_block_at_high(self):
        self.assertFalse(self._blocked_at("high", "medium"))

    def test_medium_blocks_at_medium(self):
        self.assertTrue(self._blocked_at("medium", "medium"))

    def test_high_blocks_at_high(self):
        self.assertTrue(self._blocked_at("high", "high"))

    def test_blocker_blocks_at_high(self):
        self.assertTrue(self._blocked_at("high", "blocker"))

    def test_high_does_not_block_at_blocker(self):
        self.assertFalse(self._blocked_at("blocker", "high"))

    def test_off_disables_blocking_entirely(self):
        self.assertFalse(self._blocked_at("off", "blocker"))

    def test_both_drivers_share_the_threshold_matrix(self):
        """The matrix must be host-independent, or the gate is evadable by switching host."""
        _set_threshold(self.repo, "medium")
        _plan(self.repo, "depaaa")
        _review(
            self.repo,
            "depaaa",
            rounds=[rf.Round(1, (_finding(severity="medium"),), ())],
        )
        state = _state(self.repo, [_item("itemaa", ["depaaa"])])
        self.assertEqual(
            oc.dependency_status(state["queue"][0], state),
            agy.dependency_status(state["queue"][0], state),
        )


class TransitiveCascadeTests(_RepoCase):
    def test_transitive_dependent_is_also_blocked(self):
        """A -> B -> C with the finding on A: C must wait too (the maintainer's stated rule).

        C is blocked INDIRECTLY: A blocks B, B is therefore not in a success state, and B's
        unsatisfied status blocks C. The chain is what makes "everything depending on a failed item
        waits" true rather than only its immediate dependents.
        """
        _set_threshold(self.repo, "high")
        _plan(self.repo, "aaa111")
        _review(self.repo, "aaa111")
        state = _state(
            self.repo,
            [
                _item("aaa111", [], status="executed", position=1),
                _item("bbb222", ["aaa111"], position=2),
                _item("ccc333", ["bbb222"], position=3),
            ],
        )
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                # B: blocked directly by A's finding.
                sat_b, miss_b = drv.dependency_status(state["queue"][1], state)
                self.assertFalse(sat_b)
                self.assertEqual(miss_b, ["aaa111"])
                # C: blocked because B is not in a success state.
                sat_c, miss_c = drv.dependency_status(state["queue"][2], state)
                self.assertFalse(sat_c)
                self.assertEqual(miss_c, ["bbb222"])

    def test_independent_satisfiable_item_is_still_selected(self):
        """The TRUE property, not the draft's false 'independent items still proceed'.

        The runner's selection loop is ALL-OR-NOTHING at its terminal step: when NOTHING is
        satisfiable it blocks every queued item and BREAKS out of the run. So independent progress is
        a property of SELECTION (a satisfiable item is still chosen while a blocked chain waits), not
        of the block being item-local. That all-or-nothing terminal case is PRE-EXISTING runner
        behavior which this plan does NOT change.
        """
        _set_threshold(self.repo, "high")
        _plan(self.repo, "aaa111")
        _review(self.repo, "aaa111")
        state = _state(
            self.repo,
            [
                _item("aaa111", [], status="executed", position=1),
                _item("bbb222", ["aaa111"], position=2),
                _item("indep1", [], position=3),
            ],
        )
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                queued = [i for i in state["queue"] if i["status"] == "queued"]
                chosen = [
                    i["id6"] for i in queued if drv.dependency_status(i, state)[0]
                ]
                self.assertEqual(chosen, ["indep1"])


# --------------------------------------------------------------------------------------
# V-04 / V-08: the block names its cause and its exact recovery command
# --------------------------------------------------------------------------------------


class BlockLegibilityTests(_RepoCase):
    def test_reason_map_names_the_finding_id_and_severity(self):
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(self.repo, "depaaa")
        state = _state(self.repo, [_item("itemaa", ["depaaa"])])
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                sat, missing, reasons = drv.dependency_status_detailed(
                    state["queue"][0], state
                )
                self.assertFalse(sat)
                self.assertEqual(missing, ["depaaa"])
                why = reasons["depaaa"]
                self.assertIn("F-1", why)
                self.assertIn("high", why)
                # A message that says only "dependency not satisfied" is the failure mode being fixed.
                self.assertNotEqual(why.strip(), "dependency not satisfied")

    def test_flat_dependency_list_shape_is_unchanged(self):
        """E-04 is ADDITIVE: existing consumers of the flat list[str] must be untouched."""
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(self.repo, "depaaa")
        state = _state(self.repo, [_item("itemaa", ["depaaa"])])
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                _sat, missing = drv.dependency_status(state["queue"][0], state)
                self.assertIsInstance(missing, list)
                self.assertTrue(all(isinstance(x, str) for x in missing))

    def test_recovery_hint_names_the_actual_flag(self):
        """A block whose exit is undocumented is a usability failure; recovery needs an EXPLICIT flag."""
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                hint = drv.DEPENDENCY_BLOCK_RECOVERY_HINT
                self.assertIn("--retry-incomplete", hint)
                self.assertIn("bare", hint.lower())

    def test_report_section_names_cause_and_recovery(self):
        """The reason must reach the run report an operator reads, not only events.jsonl."""
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                run_dir = Path(tempfile.mkdtemp(prefix=f"aw_rep_{name}_"))
                try:
                    state = {
                        "run_id": "run-x",
                        "repo": str(self.repo),
                        "created_at": "t",
                        "updated_at": "t",
                        "selectors": [],
                        "set_sessions": {},
                        "queue": [
                            {
                                "id6": "itemaa",
                                "position": 1,
                                "setid": "demo",
                                "action": "execute",
                                "status": "dependency-blocked",
                                "attempts": [],
                                "unsatisfied_dependencies": ["depaaa"],
                                "unsatisfied_dependency_reasons": {
                                    "depaaa": "depaaa: review finding F-1 is high/open and unresolved"
                                },
                                "dependency_block_recovery": drv.DEPENDENCY_BLOCK_RECOVERY_HINT,
                            }
                        ],
                    }
                    drv.write_report(run_dir, state)
                    text = (run_dir / "execution-report.md").read_text(encoding="utf-8")
                    self.assertIn("Dependency blocks (why)", text)
                    self.assertIn("F-1", text)
                    self.assertIn("--retry-incomplete", text)
                finally:
                    shutil.rmtree(run_dir, ignore_errors=True)


class RecoverySemanticsTests(unittest.TestCase):
    """V-08: the ACTUAL re-queue behavior, which is NOT automatic and was falsely claimed in the draft."""

    def test_dependency_blocked_is_in_the_retry_set_but_only_under_the_flag(self):
        """Proves the flag is load-bearing by reading the runner source, not by asserting a wish."""
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                src = _src(drv)
                self.assertIn("if retry_incomplete:", src)
                # `start` must still pass False, i.e. the default is UNCHANGED by this plan.
                self.assertIn("retry_incomplete=False", src)

    def test_retry_incomplete_flag_exists_on_resume(self):
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                src = _src(drv)
                self.assertIn("--retry-incomplete", src)


# --------------------------------------------------------------------------------------
# V-03: the shared `aw check` evaluator
# --------------------------------------------------------------------------------------


class CheckEngineRuleTests(_RepoCase):
    def test_rule_id_is_registered_and_not_the_conservative_default(self):
        spec = ce.rule_spec(DEP_RULE)
        self.assertIn(DEP_RULE, ce.RULE_REGISTRY)
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec.determinism, ce.DET_DETERMINISTIC)

    def test_identity_verdicts_were_not_overloaded(self):
        """`dangling`/`ambiguous` are IDENTITY verdicts; reusing them here would be a false statement.

        Asserted structurally: the new rule id is distinct from both, so a findings-blocked target is
        never reported as "no artifact has that id6" or "several artifacts do".
        """
        self.assertNotEqual(DEP_RULE, "check.ipd-dependency-dangling")
        self.assertNotEqual(DEP_RULE, "check.ipd-dependency-ambiguous")

    def test_executed_edge_to_findings_blocked_plan_is_reported(self):
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(self.repo, "depaaa")
        dependent = _plan(
            self.repo,
            "itemaa",
            lane="pending",
            status="approved",
            order=2,
            deps="executed:depaaa",
        )
        drift = ce.evaluate_ipd_dependencies(self.repo, phase="pre-execution")
        hits = [d for d in drift if d.rule == DEP_RULE]
        self.assertEqual(len(hits), 1, [(d.rule, d.detail) for d in drift])
        self.assertEqual(hits[0].location, str(dependent))
        self.assertIn("F-1", hits[0].detail)
        self.assertIn("high", hits[0].detail)

    def test_clean_target_is_silent(self):
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _plan(
            self.repo,
            "itemaa",
            lane="pending",
            status="approved",
            order=2,
            deps="executed:depaaa",
        )
        drift = ce.evaluate_ipd_dependencies(self.repo, phase="pre-execution")
        self.assertEqual([d for d in drift if d.rule == DEP_RULE], [])

    def test_resolved_finding_is_silent(self):
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(
            self.repo, "depaaa", rounds=[rf.Round(1, (_finding(decision="fixed"),), ())]
        )
        _plan(
            self.repo,
            "itemaa",
            lane="pending",
            status="approved",
            order=2,
            deps="executed:depaaa",
        )
        drift = ce.evaluate_ipd_dependencies(self.repo, phase="pre-execution")
        self.assertEqual([d for d in drift if d.rule == DEP_RULE], [])

    def test_threshold_off_disables_the_rule(self):
        _set_threshold(self.repo, "off")
        _plan(self.repo, "depaaa")
        _review(self.repo, "depaaa")
        _plan(
            self.repo,
            "itemaa",
            lane="pending",
            status="approved",
            order=2,
            deps="executed:depaaa",
        )
        drift = ce.evaluate_ipd_dependencies(self.repo, phase="pre-execution")
        self.assertEqual([d for d in drift if d.rule == DEP_RULE], [])

    def test_exists_edge_is_not_findings_gated(self):
        """Only `executed:` asserts completed-and-verified work; `exists:` stays structural."""
        _set_threshold(self.repo, "high")
        _plan(self.repo, "depaaa")
        _review(self.repo, "depaaa")
        _plan(
            self.repo,
            "itemaa",
            lane="pending",
            status="approved",
            order=2,
            deps="exists:ipd:depaaa",
        )
        drift = ce.evaluate_ipd_dependencies(self.repo, phase="pre-execution")
        self.assertEqual([d for d in drift if d.rule == DEP_RULE], [])


# --------------------------------------------------------------------------------------
# V-07: the `/exec-set` Set compiler (the THIRD authority surface)
# --------------------------------------------------------------------------------------


class SetCompilerGateTests(_RepoCase):
    def _set_fixture(self) -> Path:
        """Set `demo`: orchestrator + A(1) -> B(2) -> C(3), plus independent sibling D(4)."""
        plans = self.repo / ".aw" / "records" / "plans"
        orch = plans / "pending" / "20260829-demo-00-orch01-orchestrator.ipd.md"
        orch.write_text(
            "# IPD: orchestrator\n\n"
            "- Date: 2026-08-29\n- Kind: orchestrator\n- Scope-Paths: x.py\n"
            "- Item-Dependencies: none\n- Status: approved\n- Set: demo\n- Order: 0\n"
            "- Id: orch01\n\n## Workflow history\n- 2026-08-29 draft (t): created.\n\n"
            "## Goal\ng\n",
            encoding="utf-8",
        )
        for id6, order in (("aaa111", 1), ("bbb222", 2), ("ccc333", 3), ("ddd444", 4)):
            _plan(
                self.repo,
                id6,
                lane="pending",
                status="approved",
                order=order,
                set_id="demo",
            )
        return plans

    def test_findings_blocked_child_becomes_a_gate_and_blocks_descendants(self):
        _set_threshold(self.repo, "high")
        plans = self._set_fixture()
        _review(self.repo, "aaa111")  # finding on the FIRST child
        inv = sp.resolve_set(plans, "demo")
        self.assertIn("aaa111", inv.deferred_gates)
        # The serial-inference cascade blocks every descendant of the gate.
        self.assertIn("aaa111", inv.blocked_children)
        self.assertIn("bbb222", inv.blocked_children)
        self.assertIn("ccc333", inv.blocked_children)
        # And the reason is legible rather than an unexplained id.
        self.assertIn("F-1", inv.gate_reasons["aaa111"])

    def test_clean_set_has_no_findings_gate(self):
        _set_threshold(self.repo, "high")
        plans = self._set_fixture()
        inv = sp.resolve_set(plans, "demo")
        self.assertEqual(inv.deferred_gates, ())
        self.assertEqual(inv.blocked_children, ())

    def test_independent_sibling_is_not_blocked_with_an_explicit_orchestrator_table(
        self,
    ):
        """A non-descendant sibling stays RUNNABLE: this gate blocks descendants, not the whole Set.

        Requires the REAL orchestrator child-table (heading `## Child IPDs, sequence, and dependencies`,
        four columns `| Order | File | Purpose | Depends on |`), because with the legacy fallback every
        child is serially chained to the previous one, so EVERY later sibling is a descendant of the
        gate and "independent sibling" is not expressible. Asserted explicitly rather than skipped,
        since descendant-only blocking is the property that keeps this gate from being a Set-wide halt.
        """
        _set_threshold(self.repo, "high")
        plans = self._set_fixture()
        orch = plans / "pending" / "20260829-demo-00-orch01-orchestrator.ipd.md"
        orch.write_text(
            orch.read_text(encoding="utf-8")
            + "\n## Child IPDs, sequence, and dependencies\n\n"
            "| Order | File | Purpose | Depends on |\n|---|---|---|---|\n"
            "| 1 | a.ipd.md | a | none |\n"
            "| 2 | b.ipd.md | b | 1 |\n"
            "| 3 | c.ipd.md | c | 2 |\n"
            "| 4 | d.ipd.md | d | none |\n",
            encoding="utf-8",
        )
        _review(self.repo, "aaa111")
        inv = sp.resolve_set(plans, "demo")
        self.assertEqual(inv.cross_edges_source, "orchestrator-table")
        self.assertEqual(inv.deferred_gates, ("aaa111",))
        # The gate and its transitive descendants block...
        self.assertIn("aaa111", inv.blocked_children)
        self.assertIn("bbb222", inv.blocked_children)
        self.assertIn("ccc333", inv.blocked_children)
        # ...but the INDEPENDENT sibling does not.
        self.assertNotIn("ddd444", inv.blocked_children)

    def test_reuses_the_existing_propagate_blocked_cascade(self):
        """One transitive rule in this module, not a second hand-written cascade."""
        src = _src(sp)
        self.assertEqual(src.count("def _propagate_blocked"), 1)
        self.assertIn("_propagate_blocked(child_ids, cross_edges, gates)", src)

    def test_manifest_carries_the_gate_reason(self):
        _set_threshold(self.repo, "high")
        plans = self._set_fixture()
        _review(self.repo, "aaa111")
        inv = sp.resolve_set(plans, "demo")
        manifest = sp.compile_manifest(inv, plans, base_head="deadbeef")
        self.assertIn("aaa111", manifest.deferred_gates)
        self.assertIn(
            "F-1", json.loads(sp.emit_manifest_json(manifest))["gate_reasons"]["aaa111"]
        )
        self.assertIn("F-1", sp.render_plan_only_human(manifest))


# --------------------------------------------------------------------------------------
# V-06: cross-surface non-evasion. ONE fixture, EVERY authority surface.
# --------------------------------------------------------------------------------------


class CrossSurfaceNonEvasionTests(_RepoCase):
    """A gate proven on three of four surfaces is a gate with an undocumented bypass.

    This enumerates every surface that grants execution authority and asserts each REFUSES the same
    fixture, so a future contributor who adds a fifth surface has a single place that fails.
    """

    # A NOTE ON WHY SURFACE 4 NEEDS ITS OWN CHILD STATUS, discovered while writing this test and
    # recorded because it is a vacuity trap, not a detail. The runner/`aw check` surfaces only reach
    # the findings check for a target that is ALREADY `executed` (that is what an `executed:` edge
    # asserts). But the Set compiler's `RUNNABLE_STATUSES` is `{approved, auto-approved}`, so an
    # `executed` child is ALREADY a gate for a PRE-EXISTING reason that has nothing to do with
    # findings. Asserting "the executed child is in blocked_children" would therefore pass with this
    # plan's code REVERTED - a vacuous assertion. Surface 4 is consequently exercised on an `approved`
    # child, where the ONLY possible gate cause is the finding, and the assertion additionally checks
    # `gate_reasons` names the FINDING rather than the status.

    def test_every_authority_surface_refuses_the_same_finding(self):
        _set_threshold(self.repo, "high")
        plans = self.repo / ".aw" / "records" / "plans"
        _plan(self.repo, "aaa111")  # executed/ target carrying the finding
        _review(self.repo, "aaa111")
        _plan(
            self.repo,
            "bbb222",
            lane="pending",
            status="approved",
            order=2,
            deps="executed:aaa111",
        )

        verdicts: dict[str, bool] = {}

        # Surface 1 + 2: both host runners' dependency_status.
        state = _state(self.repo, [_item("bbb222", ["aaa111"])])
        for name, drv in DRIVERS:
            satisfied, _ = drv.dependency_status(state["queue"][0], state)
            verdicts[f"{name}_runipd.dependency_status"] = not satisfied

        # Surface 3: the shared `aw check` evaluator.
        drift = ce.evaluate_ipd_dependencies(self.repo, phase="pre-execution")
        verdicts["check_engine.evaluate_ipd_dependencies"] = any(
            d.rule == DEP_RULE for d in drift
        )

        # Surface 4: the `/exec-set` Set compiler (E-07 branch (a): CLOSED, not scoped out). Uses a
        # SEPARATE Set whose gated child is `approved`, so the finding is the only possible cause.
        inv = sp.resolve_set(plans, "other")  # built below in _other_set
        verdicts["ipd_set_plan.blocked_children"] = (
            "eee555" in inv.blocked_children
            and "fff666" in inv.blocked_children
            and "F-1" in inv.gate_reasons.get("eee555", "")
        )

        self.assertEqual(
            verdicts,
            {
                "oc_runipd.dependency_status": True,
                "agy_runipd.dependency_status": True,
                "check_engine.evaluate_ipd_dependencies": True,
                "ipd_set_plan.blocked_children": True,
            },
        )

    def setUp(self):
        super().setUp()
        self._other_set()

    def _other_set(self) -> None:
        """Set `other`: approved children E(1) -> F(2), with the finding on E.

        `approved` is deliberate: it is IN `RUNNABLE_STATUSES`, so this child is a gate ONLY if the
        findings cause fires. That is what makes the surface-4 assertion non-vacuous.
        """
        _set_threshold(self.repo, "high")
        for id6, order in (("eee555", 1), ("fff666", 2)):
            _plan(
                self.repo,
                id6,
                lane="pending",
                status="approved",
                order=order,
                set_id="other",
            )
        _review(self.repo, "eee555")

    def test_surface_4_assertion_is_not_vacuous(self):
        """Proves the surface-4 child would NOT be a gate but for the finding.

        Without this control, `test_every_authority_surface_refuses_the_same_finding` could pass for
        the pre-existing unapproved-status reason and silently stop testing this plan's change.
        """
        plans = self.repo / ".aw" / "records" / "plans"
        # Same Set, same statuses, but the finding is FIXED -> no gate at all.
        _review(
            self.repo, "eee555", rounds=[rf.Round(1, (_finding(decision="fixed"),), ())]
        )
        inv = sp.resolve_set(plans, "other")
        self.assertEqual(inv.deferred_gates, ())
        self.assertEqual(inv.blocked_children, ())

    def test_all_surfaces_agree_when_the_finding_is_resolved(self):
        """The converse: no surface blocks spuriously once the finding is `fixed`."""
        _set_threshold(self.repo, "high")
        plans = self.repo / ".aw" / "records" / "plans"
        _plan(self.repo, "aaa111")
        _review(
            self.repo, "aaa111", rounds=[rf.Round(1, (_finding(decision="fixed"),), ())]
        )
        _plan(
            self.repo,
            "bbb222",
            lane="pending",
            status="approved",
            order=2,
            deps="executed:aaa111",
        )
        state = _state(self.repo, [_item("bbb222", ["aaa111"])])
        for name, drv in DRIVERS:
            with self.subTest(driver=name):
                self.assertTrue(drv.dependency_status(state["queue"][0], state)[0])
        drift = ce.evaluate_ipd_dependencies(self.repo, phase="pre-execution")
        self.assertEqual([d for d in drift if d.rule == DEP_RULE], [])
        # Set `other` (approved children): resolving the finding removes the gate entirely. Set `demo`
        # is NOT asserted here, because its `executed` child is a gate for the pre-existing
        # status reason regardless of findings (see the note above).
        _review(
            self.repo, "eee555", rounds=[rf.Round(1, (_finding(decision="fixed"),), ())]
        )
        inv_other = sp.resolve_set(plans, "other")
        self.assertEqual(inv_other.blocked_children, ())


if __name__ == "__main__":
    unittest.main()

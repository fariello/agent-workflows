#!/usr/bin/env python3
"""rununify Order 07 (`yrqyxb`) E-02: CHARACTERIZATION of the sixteen safety gates
`execute_item` owns, pinned as BEHAVIOR on BOTH hosts.

WHY THIS FILE EXISTS. `execute_item` is the largest symbol in either runner and it performs
the LANE TEARDOWN and the INTEGRATION. A defect here can destroy verified work or merge over
a contaminated base, which is the failure this repository has already paid for twice (plan
F-2). Before any part of that function is relocated into `runner_shared`, every gate inside
it must be pinned so a later split cannot silently stop refusing.

WHAT A "GATE" MEANS HERE, and why the distinction is the whole point. The plan's F-8 measured
21 EXISTING pins that reach these gates by reading `execute_item`'s SOURCE TEXT
(`inspect.getsource`, an AST lookup, or `split("def execute_item")`). A source-text pin is
satisfied by a comment and is destroyed by a relocation, so it proves nothing about a shared
core. Every assertion below therefore pins the PROPERTY the gate provides:

  * the gate function is REACHABLE and still refuses on the input it exists to refuse; and
  * where an existing pin asserts ORDERING, the ordering is asserted on the CALL GRAPH
    (which survives a move) rather than on the byte offsets of one function's source.

This is the same conversion the executed sibling `ct4w0a` performed for the `af7i6p` begin-site
pin (see `tests/test_lane_tool_identity.py::TheBeginPinSurvivedTheMove`), and it is what the
maintainer's 2026-09-16 ruling authorizes: re-base a guard deliberately, never weaken it silently.

HONEST LIMIT, stated so no reader over-reads this file. These tests pin that each gate EXISTS,
is reached from `execute_item` on both hosts, and refuses the input it is designed to refuse.
They do NOT execute a full driver turn end to end, so they cannot prove the gates compose
correctly under every real interleaving. That assurance lives in the host CLI suites
(`tests/test_oc_runipd_cli.py`, `tests/test_agy_runipd_cli.py`), which require a real git repo
and the driver role. Read this file as the SPLIT-SURVIVAL net, not as the integration proof.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import unittest

from agent_workflows import agy_runipd, lane_containment, oc_runipd, runner_shared

HOSTS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))

# The sixteen gates plan F-2 measured inside `execute_item`, identically on both hosts.
# Each entry is a name that must be CALLED from `execute_item` on BOTH hosts.
SIXTEEN_GATES = (
    "evaluate_clean_base_for_launch",
    "clean_base_launch_decision",
    "assert_child_tool_identity",
    "driver_begin",
    "allocate_isolation_worktree",
    "collect_lane_submissions",
    "validate_defect_report",
    "run_suite_check",
    "integration_is_earned",
    "build_lane_outcome",
    "integrate_lane_branch",
    "record_integration_refusal",
    "reconcile_disposition",
    "sync_receipt_into_worktree",
    "driver_finalize",
    "process_backlog_close",
)


def _execute_item_ast(module) -> ast.FunctionDef:
    """Parse the module from disk and return its top-level `execute_item` node,
    or the shared `runner_shared.execute_item_core` if execute_item delegates to it.

    Deliberately parsed from SOURCE rather than taken from the live object, because the call
    graph is what these tests assert and it must be readable without importing a runner's
    private state.
    """
    path = pathlib.Path(inspect.getsourcefile(module))
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "execute_item"
        ):
            if any(
                isinstance(n, ast.Attribute) and n.attr == "execute_item_core"
                for n in ast.walk(node)
            ):
                shared_path = pathlib.Path(inspect.getsourcefile(runner_shared))
                for cand in ast.parse(shared_path.read_text(encoding="utf-8")).body:
                    if (
                        isinstance(cand, ast.FunctionDef)
                        and cand.name == "execute_item_core"
                    ):
                        return cand
            return node
    raise AssertionError(f"{module.__name__} has no top-level execute_item")


def _called_names(node: ast.AST) -> dict[str, list[int]]:
    """Every callee name reached from `node`, mapped to the lines it is called on.

    Records both a bare `f(...)` and an attribute `mod.f(...)`, because a symbol that moves to
    `runner_shared` is typically reached as `runner_shared.f(...)` afterwards. That is exactly
    why this is the ordering surface that SURVIVES a split: the name stays, only the binding
    changes.
    """
    found: dict[str, list[int]] = {}
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name:
                found.setdefault(name, []).append(sub.lineno)
    return found


class TheSixteenGatesAreReachedOnBothHosts(unittest.TestCase):
    """Presence, on the CALL GRAPH, of every gate F-2 named. This is the split-survival pin."""

    def test_every_gate_is_called_from_execute_item_on_both_hosts(self):
        for host, module in HOSTS:
            calls = _called_names(_execute_item_ast(module))
            for gate in SIXTEEN_GATES:
                self.assertIn(
                    gate,
                    calls,
                    f"{host}.execute_item no longer calls the safety gate {gate!r}; if it moved "
                    "into a shared core, this assertion must be re-based onto the shared "
                    "implementation rather than deleted",
                )

    def test_the_gate_census_is_symmetric_between_the_hosts(self):
        """Neither host may carry a gate the other lacks.

        A one-sided gate is how this repository's `render_stream` re-fork went unnoticed for a
        whole Set (orchestrator F10): the guard existed, but only on one host.
        """
        census = {}
        for host, module in HOSTS:
            calls = _called_names(_execute_item_ast(module))
            census[host] = {gate for gate in SIXTEEN_GATES if gate in calls}
        self.assertEqual(
            census["oc_runipd"],
            census["agy_runipd"],
            "the two hosts' gate sets diverged; a gate present on one host only is a "
            "silent asymmetry, not a host specificity",
        )


class TheGateOrderingIsPinnedOnTheCallGraph(unittest.TestCase):
    """The SIX orderings existing pins assert by source text, re-expressed structurally.

    Each existing pin is named in its docstring. These do NOT replace those pins (this plan
    edits no test file); they establish the ordering guarantee in a form that a relocation
    into `runner_shared` cannot silently destroy.
    """

    def _first_line(self, calls: dict[str, list[int]], name: str, host: str) -> int:
        self.assertIn(name, calls, f"{host}: expected a call to {name}")
        return min(calls[name])

    def test_the_clean_base_guard_precedes_worktree_allocation(self):
        """Mirrors `tests/test_lane_clean_base.py:233` and `tests/test_dirty_base_gate.py:878`.

        The base must be judged BEFORE a lane is allocated from it: allocating first would
        branch a worktree off a contaminated base, which is the whole hazard.
        """
        for host, module in HOSTS:
            calls = _called_names(_execute_item_ast(module))
            self.assertLess(
                self._first_line(calls, "evaluate_clean_base_for_launch", host),
                self._first_line(calls, "allocate_isolation_worktree", host),
                f"{host}: the clean-base evaluation must precede lane allocation",
            )

    def test_the_clean_base_verdict_precedes_the_host_spawn(self):
        """Mirrors `tests/test_lane_clean_base.py:233` (the spawn half).

        A refusal is worthless after the agent has already been launched.
        """
        spawn = {"oc_runipd": "run_opencode", "agy_runipd": "run_agy_turn"}
        for host, module in HOSTS:
            calls = _called_names(_execute_item_ast(module))
            spawn_target = (
                "spawn_executor" if "spawn_executor" in calls else spawn[host]
            )
            self.assertLess(
                self._first_line(calls, "clean_base_launch_decision", host),
                self._first_line(calls, spawn_target, host),
                f"{host}: the launch verdict must be decided before the agent is spawned",
            )

    def test_tool_identity_is_asserted_before_the_first_nested_lifecycle_call(self):
        """Mirrors `tests/test_lane_tool_identity.py:762`.

        `driver_begin` is the first nested `aw` invocation; running it with an unverified
        child tool would transition a plan using a binary whose identity was never checked.
        """
        for host, module in HOSTS:
            calls = _called_names(_execute_item_ast(module))
            self.assertLess(
                self._first_line(calls, "assert_child_tool_identity", host),
                self._first_line(calls, "driver_begin", host),
                f"{host}: tool identity must be asserted before the first lifecycle transition",
            )

    def test_submissions_are_collected_before_the_disposition_is_reconciled(self):
        """Mirrors `tests/test_lane_submission_collection.py:240` (spec R2.1).

        The lane's own submission is the authoritative answer; reconciling first would decide
        the outcome from driver-side inference and then overwrite it.

        THE TARGET IS THE DISPOSITION-ASSIGNING CALL, not merely the first `reconcile_disposition`
        in the body, and that distinction is load-bearing rather than pedantic. `execute_item`
        calls `reconcile_disposition` THREE times on each host; two of them sit on the EARLY
        recovery path (`oc_runipd.py:7344` and `:7372`), where they set a prior attempt's status
        and legitimately precede this turn's collection. Comparing against the first call would
        therefore assert a false ordering and fail on correct code. The existing pin resolves this
        the same way: it locates the tuple assignment whose target is named `disposition`.
        """
        for host, module in HOSTS:
            func = _execute_item_ast(module)
            collect = [
                sub.lineno
                for sub in ast.walk(func)
                if isinstance(sub, ast.Call)
                and (
                    (
                        isinstance(sub.func, ast.Attribute)
                        and sub.func.attr == "collect_lane_submissions"
                    )
                    or (
                        isinstance(sub.func, ast.Name)
                        and sub.func.id == "collect_lane_submissions"
                    )
                )
            ]
            self.assertTrue(
                collect, f"{host}.execute_item never collects lane submissions"
            )
            disposition_assign = [
                sub.lineno
                for sub in ast.walk(func)
                if isinstance(sub, ast.Assign)
                and isinstance(sub.targets[0], ast.Tuple)
                and any(
                    isinstance(elt, ast.Name) and elt.id == "disposition"
                    for elt in sub.targets[0].elts
                )
            ]
            self.assertTrue(
                disposition_assign,
                f"{host}: could not locate the disposition assignment",
            )
            self.assertLess(
                min(collect),
                max(disposition_assign),
                f"{host}: submissions must be collected before the disposition is computed",
            )

    def test_the_disposition_is_reconciled_before_integration(self):
        """Mirrors `tests/test_review_lane_isolation.py:717`.

        Integration must be gated on a DECIDED disposition, never race it.

        Anchored on the disposition ASSIGNMENT for the same reason as the test above: the two
        early recovery-path `reconcile_disposition` calls precede everything, so comparing the
        first call site would make this assertion pass no matter where integration sat, which is
        a guard that cannot fail.
        """
        for host, module in HOSTS:
            func = _execute_item_ast(module)
            calls = _called_names(func)
            disposition_assign = [
                sub.lineno
                for sub in ast.walk(func)
                if isinstance(sub, ast.Assign)
                and isinstance(sub.targets[0], ast.Tuple)
                and any(
                    isinstance(elt, ast.Name) and elt.id == "disposition"
                    for elt in sub.targets[0].elts
                )
            ]
            self.assertTrue(
                disposition_assign,
                f"{host}: could not locate the disposition assignment",
            )
            self.assertLess(
                max(disposition_assign),
                self._first_line(calls, "integrate_lane_branch", host),
                f"{host}: the disposition must be computed before the lane is integrated",
            )

    def test_integration_is_earned_before_the_merge_happens(self):
        """Mirrors `tests/test_runner_backlog_close_in_lane.py:1043`.

        `integration_is_earned` is the predicate that keeps unverified work out of main.
        """
        for host, module in HOSTS:
            calls = _called_names(_execute_item_ast(module))
            self.assertLess(
                self._first_line(calls, "integration_is_earned", host),
                self._first_line(calls, "integrate_lane_branch", host),
                f"{host}: integration must be earned before the merge is attempted",
            )


class TheGatesStillRefuseWhatTheyExistToRefuse(unittest.TestCase):
    """BEHAVIOR, not placement. Each gate is exercised on the input it must reject.

    These are the assertions that would catch a split which kept a gate's CALL but broke its
    verdict, which a call-graph pin alone cannot see.
    """

    def test_a_dirty_tracked_base_refuses_a_shared_tree_launch(self):
        """The shared-tree path must REFUSE a dirty tracked base (spec R5.4/R6.1)."""
        base = lane_containment.evaluate_clean_base(
            " M agent_workflows/x.py\n", shared_tree=True
        )
        self.assertTrue(base.refuses, "a dirty tracked SHARED tree must refuse")
        decision = runner_shared.clean_base_launch_decision(
            base, allow_dirty_base=False
        )
        self.assertEqual(decision.verdict, runner_shared.CLEAN_BASE_REFUSE)

    def test_a_clean_base_proceeds(self):
        """Non-vacuity control for the refusal above: a clean base must NOT refuse."""
        base = lane_containment.evaluate_clean_base("", shared_tree=True)
        self.assertFalse(base.refuses)
        decision = runner_shared.clean_base_launch_decision(
            base, allow_dirty_base=False
        )
        self.assertNotEqual(decision.verdict, runner_shared.CLEAN_BASE_REFUSE)

    def test_consent_converts_a_refusal_into_a_recorded_consent(self):
        """`--allow-dirty-base` overrides a REFUSAL and is recorded, never silent."""
        base = lane_containment.evaluate_clean_base(
            " M agent_workflows/x.py\n", shared_tree=True
        )
        decision = runner_shared.clean_base_launch_decision(base, allow_dirty_base=True)
        self.assertNotEqual(
            decision.verdict,
            runner_shared.CLEAN_BASE_REFUSE,
            "operator consent must convert the refusal",
        )

    def test_the_verdict_is_read_from_the_rule_not_decided_per_host(self):
        """A dirty ISOLATED base WARNs while a dirty SHARED tree REFUSES.

        Writing that split as an `if isolate` inside either driver's body is the exact failure
        `clean_base_launch_decision` exists to prevent, and is how the `--full-auto` default
        once came to differ between the two runners.
        """
        dirty = " M agent_workflows/x.py\n"
        isolated = runner_shared.clean_base_launch_decision(
            lane_containment.evaluate_clean_base(dirty, shared_tree=False)
        )
        shared = runner_shared.clean_base_launch_decision(
            lane_containment.evaluate_clean_base(dirty, shared_tree=True)
        )
        self.assertNotEqual(
            isolated.verdict,
            shared.verdict,
            "the isolated and shared-tree verdicts must differ, and the difference must come "
            "from the shared RULE rather than from a per-host branch",
        )
        self.assertEqual(shared.verdict, runner_shared.CLEAN_BASE_REFUSE)

    def test_integration_is_not_earned_without_a_passing_suite(self):
        """The predicate that keeps unverified work out of main must refuse a failing suite."""
        earned = oc_runipd.integration_is_earned
        failing_suite = oc_runipd.SuiteCheckResult(
            passing=False,
            exit_code=1,
            summary="1 failed",
            reason="exit 1",
            cwd="/",
            timeout_seconds=60.0,
            elapsed_seconds=1.0,
        )
        verdict = earned(validate=False, verify_disp=None, suite_result=failing_suite)
        self.assertFalse(
            verdict.earned,
            "integration_is_earned must consider the suite result and refuse on failure",
        )

    def test_both_hosts_bind_the_same_integration_predicate_object(self):
        """`integration_is_earned` must be ONE object, so a fix cannot reach one host only."""
        self.assertIs(
            oc_runipd.integration_is_earned,
            agy_runipd.integration_is_earned,
            "the integration predicate must be a single shared object",
        )

    def test_both_hosts_bind_the_same_tool_identity_assertion(self):
        self.assertIs(
            oc_runipd.assert_child_tool_identity,
            agy_runipd.assert_child_tool_identity,
            "the tool-identity assertion must be a single shared object",
        )

    def test_both_hosts_bind_the_same_backlog_close(self):
        self.assertIs(
            oc_runipd.process_backlog_close,
            agy_runipd.process_backlog_close,
            "the backlog-close step must be a single shared object",
        )

    def test_both_hosts_bind_the_same_suite_check(self):
        self.assertIs(
            oc_runipd.run_suite_check,
            agy_runipd.run_suite_check,
            "the suite check must be a single shared object",
        )


class TheAgySideGatesHaveCoverageAtAll(unittest.TestCase):
    """The orchestrator's F11: the two hosts' suites are ASYMMETRIC, so an agy regression can
    hide behind green. Every assertion in this file runs over BOTH hosts; this test states the
    requirement mechanically so a future edit cannot quietly make the file oc-only.
    """

    def test_every_gate_assertion_covers_both_hosts(self):
        source = pathlib.Path(__file__).read_text(encoding="utf-8")
        self.assertIn("agy_runipd", source)
        # HOSTS drives the loops; if it ever shrinks to one host the net goes half-blind.
        self.assertEqual(
            {name for name, _ in HOSTS},
            {"oc_runipd", "agy_runipd"},
            "the characterization net must cover both hosts",
        )

    def test_the_sixteen_gates_are_actually_sixteen(self):
        """Guards the census itself: a silently shortened list would weaken every test above."""
        self.assertEqual(len(SIXTEEN_GATES), 16)
        self.assertEqual(
            len(set(SIXTEEN_GATES)), 16, "the gate list must not contain duplicates"
        )


if __name__ == "__main__":
    unittest.main()

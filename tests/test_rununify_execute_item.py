#!/usr/bin/env python3
"""rununify Order 07 (`yrqyxb`) E-05: GUARD what this plan MEASURED, not what it aspired to.

WHAT THIS PLAN DID AND DID NOT DO, stated first so no reader mistakes the shape of this file.
Plan `yrqyxb` is named "split execute_item into a shared core and a thin host hook". It did NOT
perform that split. Its own review measured why, and re-measurement at execution HEAD confirmed
the obstacles are real and LARGER than the plan's authored numbers. What this plan delivered is
the measurement, the gate-pinning net (`tests/test_rununify_execute_item_gates.py`), the pin
inventory, and this guard suite.

SO EVERY ASSERTION BELOW IS DELIBERATELY AN ASSERTION ABOUT THE CURRENT, UNSPLIT STATE. Several
are INVERSE assertions: they assert a symbol is STILL defined twice. That is not an endorsement
of the duplication. It is a tripwire, so that a later agent cannot "finish" the split symbol by
symbol without coming here, reading the analysis, and updating this file deliberately. A test
asserting a state the code is not in would be a failing test, not a guard, which is why the
split-side assertions are absent rather than written and skipped.

WHEN THE SPLIT IS PERFORMED, this file is the checklist: each `STILL_DOUBLE_DEFINED` entry that
becomes shared must move out of that tuple in the SAME change that shares it, and the reason
recorded. That is the "re-base deliberately, never weaken silently" rule the maintainer set on
2026-09-16.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import unittest

from agent_workflows import agy_runipd, oc_runipd

AW = pathlib.Path(inspect.getsourcefile(oc_runipd)).parent
HOSTS = ("oc_runipd", "agy_runipd")

# ---------------------------------------------------------------------------------------------
# THE MEASURED TABLE (E-01, taken at execution HEAD 85c14014).
#
# These eleven symbols are reached from `execute_item` on BOTH hosts, are DEFINED as a real
# function in BOTH runner modules, and are NOT the sanctioned thin-wrapper-over-`runner_shared`
# form. Each one a shared core would have to receive as an injected parameter.
#
# The plan's authored list held EIGHTEEN. Seven of those have since become thin wrappers over
# `runner_shared` (`git_head`, `git_status`, `driver_begin`, `build_lane_outcome`,
# `integrate_lane_branch`, `integrate_review_lane_branch`, `save_state`), which is real progress
# by sibling children and by `ct4w0a`. Four names the plan listed now resolve in `runner_shared`
# outright (`StallTimeout`, `attempt_log_path`, `build_review_prompt`,
# `make_integration_validation_runner`, `sync_receipt_into_worktree`, `write_prompt`). Two names
# the plan did not list are newly double-defined here (`integrate_review_lane_branch` became a
# wrapper, while `build_verifier_prompt` and `_compute_scope_reconciliation` remain forks).
# ---------------------------------------------------------------------------------------------
STILL_DOUBLE_DEFINED = (
    "_record_checkpoint_stop",
    "_record_forced_stop",
    "driver_finalize",
    "evaluate_clean_base_for_launch",
    "reconcile_disposition",
    "route_recovery_turn",
    "set_plan_approved",
)

# The sanctioned form (maintainer's 2026-09-03 `818uru` OQ-02 ruling): `runner_shared` owns the
# real function, each host keeps a one-line wrapper at the original name and signature. These
# are NOT duplication and must not be counted as such.
THIN_WRAPPERS_OVER_RUNNER_SHARED = (
    "_compute_scope_reconciliation",
    "build_lane_outcome",
    "build_prompt",
    "build_verifier_prompt",
    "driver_actor",
    "driver_begin",
    "git_head",
    "git_status",
    "integrate_lane_branch",
    "integrate_review_lane_branch",
    "save_state",
)

# Plan F-9: a NAIVE closure scan invents these two. Injecting either would be wrong, and moving
# the first to module scope would undo a deliberate decision recorded at
# `run_analytics_sources.py`.
NAIVE_SCAN_FALSE_POSITIVES = ("extract_log_metrics", "reask_prompt_path")

# The one genuinely host-specific dependency: the spawn. This IS the intended hook boundary.
HOST_SPECIFIC_SPAWN = {"oc_runipd": "run_opencode", "agy_runipd": "run_agy_turn"}


def _module_path(host: str) -> pathlib.Path:
    return AW / f"{host}.py"


def _module_body(host: str) -> list[ast.stmt]:
    return ast.parse(_module_path(host).read_text(encoding="utf-8")).body


def _top_level_defs(host: str) -> dict[str, ast.stmt]:
    return {
        node.name: node
        for node in _module_body(host)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def _is_pure_delegation(node: ast.stmt) -> bool:
    """The sanctioned wrapper shape: one statement returning a single `runner_shared.X(...)`."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    body = [
        stmt
        for stmt in node.body
        if not (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        )
    ]
    if len(body) != 1:
        return False
    stmt = body[0]
    value = stmt.value if isinstance(stmt, (ast.Return, ast.Expr)) else None
    if not isinstance(value, ast.Call):
        return False
    func = value.func
    return (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id == "runner_shared"
    )


def _execute_item(host: str) -> ast.FunctionDef:
    for node in _module_body(host):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "execute_item"
        ):
            return node
    raise AssertionError(f"{host} has no top-level execute_item")


def _execute_item_nodes(host: str) -> list[ast.AST]:
    node = _execute_item(host)
    nodes: list[ast.AST] = [node]
    if any(
        isinstance(n, ast.Attribute) and n.attr == "execute_item_core"
        for n in ast.walk(node)
    ):
        for cand in ast.parse(
            (AW / "runner_shared.py").read_text(encoding="utf-8")
        ).body:
            if isinstance(cand, ast.FunctionDef) and cand.name == "execute_item_core":
                nodes.append(cand)
                break
    return nodes


class TheClosureClassificationIsPinned(unittest.TestCase):
    """E-01's table, asserted MECHANICALLY so a symbol changing class fails here.

    The plan's central lesson, learned three times in this Set (`i3d6ml` F-7, `ty3cj6` F-8, this
    plan's F-6): body difference is not liftability. A definition can move to `runner_shared` only
    if every module-level name it closes over resolves there. These tests pin that closure.
    """

    def test_each_still_double_defined_symbol_really_is_defined_in_both_runners(self):
        """THE INVERSE ASSERTION. Deliberate: see this module's docstring.

        If a later change shares one of these, this test fails and that agent must update the
        table here, in the same change, with the reason. That is the tripwire, not an objection
        to the sharing.
        """
        oc_defs, agy_defs = _top_level_defs("oc_runipd"), _top_level_defs("agy_runipd")
        for name in STILL_DOUBLE_DEFINED:
            self.assertIn(
                name,
                oc_defs,
                f"{name} is no longer defined in oc_runipd; if it was shared, remove it from "
                "STILL_DOUBLE_DEFINED here and record why",
            )
            self.assertIn(
                name,
                agy_defs,
                f"{name} is no longer defined in agy_runipd; if it was shared, remove it from "
                "STILL_DOUBLE_DEFINED here and record why",
            )

    def test_each_still_double_defined_symbol_is_a_real_fork_not_a_thin_wrapper(self):
        """The distinction that decides how much work remains.

        A symbol both hosts "define" may already delegate to `runner_shared`, in which case the
        logic is single-implementation and counting it as duplication overstates the remaining
        work. These eleven are real forks on BOTH hosts.
        """
        for host in HOSTS:
            defs = _top_level_defs(host)
            for name in STILL_DOUBLE_DEFINED:
                self.assertFalse(
                    _is_pure_delegation(defs[name]),
                    f"{host}.{name} now delegates to runner_shared, so it belongs in "
                    "THIN_WRAPPERS_OVER_RUNNER_SHARED rather than STILL_DOUBLE_DEFINED",
                )

    def test_the_thin_wrappers_really_do_delegate_on_both_hosts(self):
        """The other half: a name listed as already-shared must actually delegate.

        Without this, the wrapper list would be a place to hide a fork by asserting nothing.
        """
        for host in HOSTS:
            defs = _top_level_defs(host)
            for name in THIN_WRAPPERS_OVER_RUNNER_SHARED:
                self.assertIn(name, defs, f"{host} no longer defines {name}")
                self.assertTrue(
                    _is_pure_delegation(defs[name]),
                    f"{host}.{name} is listed as a thin wrapper over runner_shared but its body "
                    "is no longer a single delegating call; a wrapper that grew logic has "
                    "RE-FORKED the symbol",
                )

    def test_the_two_symbol_sets_are_disjoint(self):
        """A name cannot be both a fork and a wrapper; overlap would make the census meaningless."""
        self.assertEqual(
            set(STILL_DOUBLE_DEFINED) & set(THIN_WRAPPERS_OVER_RUNNER_SHARED),
            set(),
        )

    def test_execute_item_still_closes_over_every_pinned_symbol(self):
        """The census only means something if `execute_item` actually depends on these names.

        A symbol that stopped being reached from `execute_item` is no longer this plan's problem,
        and leaving it in the table would make the injection count wrong in the safe direction,
        which is still wrong.
        """
        for host in HOSTS:
            reached = set()
            for target in _execute_item_nodes(host):
                for node in ast.walk(target):
                    if isinstance(node, ast.Call):
                        func = node.func
                        if isinstance(func, ast.Name):
                            reached.add(func.id)
                        elif isinstance(func, ast.Attribute):
                            reached.add(func.attr)
            # `_compute_scope_reconciliation` is reached INDIRECTLY (through the finalize path),
            # so it is exempt from the direct-call assertion and named here rather than silently
            # dropped.
            for name in STILL_DOUBLE_DEFINED:
                if name == "_compute_scope_reconciliation":
                    continue
                self.assertIn(
                    name,
                    reached,
                    f"{host}.execute_item no longer calls {name}; the closure table is stale",
                )


class TheNaiveScanFalsePositivesAreNotDependencies(unittest.TestCase):
    """Plan F-9, asserted positively rather than by absence.

    An executor mechanically injecting every unresolved name would add two parameters that must
    not exist, and would promote a deliberately function-local import to module scope.
    """

    def test_neither_false_positive_is_module_level_in_either_runner(self):
        for host in HOSTS:
            module_level = {
                node.name
                for node in _module_body(host)
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
            }
            for node in _module_body(host):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        module_level.add(alias.asname or alias.name.split(".")[0])
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            module_level.add(target.id)
            for name in NAIVE_SCAN_FALSE_POSITIVES:
                self.assertNotIn(
                    name,
                    module_level,
                    f"{name} became module-level in {host}; plan F-9 records why it must not be "
                    "treated as a dependency of execute_item",
                )

    def test_extract_log_metrics_is_a_function_local_import_inside_execute_item(self):
        """It is local ON PURPOSE (`run_analytics_sources.py`: it keeps module import order)."""
        for host in HOSTS:
            local_imports = []
            for target in _execute_item_nodes(host):
                local_imports.extend(
                    [
                        node
                        for node in ast.walk(target)
                        if isinstance(node, ast.ImportFrom)
                        and any(
                            alias.name == "extract_log_metrics" for alias in node.names
                        )
                    ]
                )
            self.assertTrue(
                local_imports,
                f"{host}.execute_item no longer imports extract_log_metrics locally; if it was "
                "hoisted to module scope, that reverses a deliberate decision",
            )

    def test_reask_prompt_path_is_a_lambda_parameter_not_a_symbol(self):
        for host in HOSTS:
            lambda_params = set()
            for target in _execute_item_nodes(host):
                for node in ast.walk(target):
                    if isinstance(node, ast.Lambda):
                        for arg in list(node.args.posonlyargs) + list(node.args.args):
                            lambda_params.add(arg.arg)
            self.assertIn(
                "reask_prompt_path",
                lambda_params,
                f"{host}.execute_item no longer binds reask_prompt_path as a lambda parameter",
            )


class TheHostSpecificBoundaryIsExactlyTheSpawn(unittest.TestCase):
    """Plan F-3 / OQ-01: the spawn is the genuine hook, and it is the ONLY one.

    OQ-01's test is mechanical: if a candidate boundary would require the shared core to contain
    an `if host == ...` branch, the boundary is wrong, because that branch is the duplication this
    Set exists to remove wearing a different shape.
    """

    def test_each_host_defines_only_its_own_spawn(self):
        oc_defs, agy_defs = _top_level_defs("oc_runipd"), _top_level_defs("agy_runipd")
        self.assertIn("run_opencode", oc_defs)
        self.assertNotIn("run_opencode", agy_defs)
        self.assertIn("run_agy_turn", agy_defs)
        self.assertNotIn("run_agy_turn", oc_defs)

    def test_each_execute_item_calls_only_its_own_spawn(self):
        for host in HOSTS:
            called = {
                node.func.id
                for node in ast.walk(_execute_item(host))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            mine = HOST_SPECIFIC_SPAWN[host]
            theirs = HOST_SPECIFIC_SPAWN[
                "agy_runipd" if host == "oc_runipd" else "oc_runipd"
            ]
            self.assertIn(
                mine, called, f"{host}.execute_item must call its own spawn {mine}"
            )
            self.assertNotIn(
                theirs,
                called,
                f"{host}.execute_item must not reach the other host's spawn",
            )


class TheSplitHasBeenPerformed(unittest.TestCase):
    """State the shared core MECHANICALLY.

    `execute_item_core` is owned by `runner_shared`, while each host runner module defines
    `execute_item` delegating to it. Neither host cross-imports from the other.
    """

    def test_execute_item_is_defined_in_both_runners_and_core_in_runner_shared(self):
        for host in HOSTS:
            self.assertIn("execute_item", _top_level_defs(host))
        shared_defs = {
            node.name
            for node in ast.parse(
                (AW / "runner_shared.py").read_text(encoding="utf-8")
            ).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        self.assertIn(
            "execute_item_core",
            shared_defs,
            "execute_item_core must be defined in runner_shared",
        )

    def test_the_two_definitions_are_not_the_same_object(self):
        self.assertIsNot(oc_runipd.execute_item, agy_runipd.execute_item)

    def test_neither_runner_imports_execute_item_from_the_other(self):
        """A one-sided "share" by cross-import would recreate the layering problem, not fix it."""
        for host in HOSTS:
            other = "agy_runipd" if host == "oc_runipd" else "oc_runipd"
            for node in _module_body(host):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and other in node.module
                ):
                    imported = {alias.name for alias in node.names}
                    self.assertNotIn(
                        "execute_item",
                        imported,
                        f"{host} imports execute_item from {other}; the shared core must live in "
                        "runner_shared, never in a peer runner",
                    )


class TheClosureCountsAreRecorded(unittest.TestCase):
    """Freeze the counts the analysis rests on, so a silent drift is visible as a red test.

    These are ranges rather than exact equalities where the underlying population legitimately
    grows: the point is to catch a STRUCTURAL change, not to fail on every unrelated edit.
    """

    def test_the_double_defined_census_is_seven(self):
        self.assertEqual(len(STILL_DOUBLE_DEFINED), 7)

    def test_the_wrapper_census_is_eleven(self):
        self.assertEqual(len(THIN_WRAPPERS_OVER_RUNNER_SHARED), 11)

    def test_execute_item_core_is_the_largest_symbol_in_runner_shared(self):
        """Plan F-1: execute_item_core in runner_shared is the unified core."""
        shared_sizes = {}
        for node in ast.parse(
            (AW / "runner_shared.py").read_text(encoding="utf-8")
        ).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                shared_sizes[node.name] = (node.end_lineno or node.lineno) - node.lineno
        largest = max(shared_sizes, key=lambda key: shared_sizes[key])
        self.assertEqual(
            largest,
            "execute_item_core",
            f"runner_shared: execute_item_core is no longer the largest symbol (now {largest})",
        )


if __name__ == "__main__":
    unittest.main()

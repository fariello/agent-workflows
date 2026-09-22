#!/usr/bin/env python3
"""rununify Order 08 (`ty3cj6`) E-05: GUARD what this plan MEASURED and REPAIRED.

WHAT THIS PLAN DID AND DID NOT DO, stated first so no reader mistakes the shape of this file.
Plan `ty3cj6` is named "split run_queue into a shared core and a thin host hook". It did NOT
perform that split. Its own 2026-09-16 review measured why, and re-measurement at execution HEAD
reproduced every number: `run_queue` is a DISPATCH LOOP whose body barely differs between hosts
(12 differing code lines out of ~233, only 2 carrying a host token) while it closes over ELEVEN
symbols that are still defined twice, one of which is pinned PERMANENTLY unmovable. So the split
is a relocation taking a dozen injected dependencies, not the small move the line count suggests.

WHAT IT DELIVERED: the closure measurement (E-01), a behavioral characterization net on both hosts
(E-02, since folded into THIS file by `7ebc2964`), a two-line repair of the ONE real
defect the measurement exposed (E-03), the split analysis the sequencing decision needs (E-04), and
this guard suite.

SO SOME ASSERTIONS BELOW ARE DELIBERATELY INVERSE: they assert a symbol is STILL defined twice.
That is not an endorsement of the duplication. It is a tripwire, so a later agent cannot "finish"
the split symbol by symbol without coming here, reading the analysis, and updating this file
deliberately. A test asserting a state the code is not in would be a failing test, not a guard,
which is why the split-side assertions are ABSENT rather than written and skipped.

WHEN THE SPLIT IS PERFORMED, this file is the checklist: each `STILL_DOUBLE_DEFINED` entry that
becomes shared moves out of that tuple in the SAME change that shares it, with the reason recorded.
That is the "re-base deliberately, never weaken silently" rule the maintainer set on 2026-09-16.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import contextlib
import io
import json
import tempfile
import unittest
from unittest.mock import patch

from agent_workflows import agy_runipd, oc_runipd, runner_shared

AW = pathlib.Path(str(inspect.getsourcefile(oc_runipd))).parent
HOSTS = ("oc_runipd", "agy_runipd")
MODULES = {"oc_runipd": oc_runipd, "agy_runipd": agy_runipd}

# ==================================================================================================
# THE MEASURED CLOSURE TABLE (E-01, taken at execution HEAD 24932638 with the committed scanner).
#
# METHOD, because the number only means something with the method attached: parse each host's
# `run_queue` with full scope tracking (parameters, assignments, walrus, `for`/`with`/`except`
# targets, comprehension and lambda scopes, nested defs, function-local imports, `global`) and keep
# the free names that resolve at MODULE level. A definition can move to `runner_shared` only if
# every one of those resolves there.
#
# THE MEASUREMENT REPRODUCED THE PLAN'S NUMBERS EXACTLY: 41 free module-level names, 11 still
# double-defined. Unlike sibling `yrqyxb`, whose count IMPROVED from 18 to 11 under re-measurement,
# nothing here moved between authoring and execution.
# ==================================================================================================

# A REAL FORK: defined as an independent function in BOTH runner modules. Each one a shared core
# would have to receive as an injected parameter, and injecting a symbol is the opposite of sharing
# it, which is the whole reason this plan did not perform the split.
# RE-BASED BY hostdedup Order 01 (`li44r9`) E-04, in the SAME change that lifted the symbols, per the
# maintainer's 2026-09-16 "re-base deliberately, never weaken silently" rule. THREE entries MOVED to
# `THIN_WRAPPERS_OVER_RUNNER_SHARED` below rather than being deleted, so each is still asserted, now as
# a wrapper that must really delegate:
#   `_observe_between_turn_stop`, `_record_deliberate_stop`, `requeue_interrupted`.
#
# `disable_lane_prompt` DELIBERATELY STAYS, and it is the one symbol of that plan's tranche that was NOT
# lifted. `PERMANENTLY_UNMOVABLE` below states the reason and `tests/test_runner_shared.py
# ::UnmovableSymbolTests` enforces it: it mutates `_LANE_PROMPT_DISABLED` through `global` while each
# host's DIVERGED `_lane_reclaim_prompt` reads its own copy, so a shared definition would silently break
# prompt suppression on a repeated interrupt in an unattended run. Re-measured at that plan's execution
# HEAD, `_lane_reclaim_prompt` is still divergent, so the premise still holds.
#
# `_integrate_stranded_lanes` also stays: it became byte-identical after that plan was authored, so it
# was never reviewed under it and is left for Order 02 rather than lifted unreviewed.
STILL_DOUBLE_DEFINED = (
    # ADDED 2026-09-18 by `runnoop` Order 01 (`zz5yxq`), and it is a TABLE REPAIR, not this plan's
    # doing. `run_queue` on BOTH hosts calls `_integrate_stranded_lanes` and each host defines its own
    # (measured: `oc._integrate_stranded_lanes is agy._integrate_stranded_lanes` -> False,
    # `__module__` `agent_workflows.oc_runipd` vs `agent_workflows.agy_runipd`), so it has always
    # belonged in this class. It was simply never classified: measured at the PRE-CHANGE baseline, it
    # was already `reached but not in table`, which the membership test below cannot see because that
    # test only fails in the other direction (a LISTED name that stopped being reached). It is added
    # here because this plan's removal of `SUCCESS_STATES` moved the census total, and paying for that
    # by lowering `CLOSURE_TOTAL` would have hidden a real fork instead of recording it.
    "_integrate_stranded_lanes",
    "disable_lane_prompt",
    "execute_item",
    "reclaim_lanes_on_interrupt",
    # `reconcile_interrupted` IS DELIBERATELY NO LONGER HERE. It was SHARED by runrecon-02 (`fduoj4`)
    # E-01 and each host now keeps the sanctioned one-line wrapper, so it moved to
    # THIN_WRAPPERS_OVER_RUNNER_SHARED below. That is the "re-base deliberately, never weaken silently"
    # rule this file's header sets, performed in the SAME change that shared the symbol.
    #
    # WHY IT HAD TO BE SHARED, recorded so the reclassification is not read as tidying: the two copies
    # had DIVERGED in one code line (oc `item["configured_file"]`, agy `.get(..., "")`), so on an item
    # missing that key oc raised `KeyError` past an `except DriverError` that does not catch it and
    # abandoned the whole crashed queue before `save_state`, while agy reconciled it. `run_viewer`'s
    # `repair_run` also called the OC copy for every run whatever host wrote it. One behavior, three
    # callers, two implementations.
    # `requeue_interrupted` LEFT FOR THE SAME REASON, under hostdedup Order 01 (`li44r9`) E-04,
    # which lifted it with `_observe_between_turn_stop` and `_record_deliberate_stop`. BOTH
    # removals land in this merge: `fduoj4` shared one symbol and `li44r9` shared three, and the
    # two sets are DISJOINT, so these are independent reclassifications and not competing edits.
    "retry_deferred_integrations",
)

# PINNED UNMOVABLE, PERMANENTLY, by `tests/test_runner_shared.py::UnmovableSymbolTests`. It mutates
# `_LANE_PROMPT_DISABLED` through `global` while each host's DIVERGED `_lane_reclaim_prompt` reads
# its own copy, so lifting it silently breaks prompt suppression on a repeated interrupt in an
# unattended run. `run_queue` CALLS it, so a shared core must take it as a parameter FOREVER rather
# than until some later child moves it. Sibling `i3d6ml` measured the same trap from the other side:
# `_lane_reclaim_prompt` cannot be lifted either, for the same shared-global reason.
PERMANENTLY_UNMOVABLE = ("disable_lane_prompt",)

# Already resolving in `runner_shared` today: these move with the loop for free.
RESOLVES_IN_RUNNER_SHARED = (
    "DriverError",
    "append_jsonl",
    "dispatch_orchestrator_item",
    "load_state",
    "print_lane_interrupt_report",
    "should_color",
    "utc_now",
)

# ALREADY ONE OBJECT, reached by both hosts (agy imports it from oc, or both import a third
# module). NOT duplication: these need RELOCATION to `runner_shared`, not de-duplication, and
# counting them as forks would overstate the remaining work. This is the distinction sibling
# `yrqyxb` established for the thin-wrapper class, applied to the import class.
ALREADY_ONE_OBJECT = (
    "Palette",
    "Path",
    "StreamTracker",
    "ToolIdentityError",
    "cascade_dependency_blocked",
    "contextlib",
    "dependency_status",
    "dependency_status_detailed",
    "emit_shutdown_report",
    "queue_sort_key",
    "register_signal_report",
    "render_run_summary_table",
    "report_run_spec_edits",
    "runner_shared",
    "runner_stop",
    "sys",
    "time",
    "update_execution_order",
)

# The sanctioned wrapper form (maintainer's 2026-09-03 `818uru` OQ-02 ruling): `runner_shared` owns
# the real function and each host keeps a one-line wrapper at the original name and signature.
#: RECLASSIFIED 2026-09-17 by sibling `tx6q0h`, which gave the two runners ONE `HostLabels`
#: descriptor and lifted the eight host-label symbols into `runner_shared`. Each name moved here
#: from STILL_DOUBLE_DEFINED because it is now the SANCTIONED WRAPPER FORM (the maintainer's
#: 2026-09-03 `818uru` OQ-02 ruling): `runner_shared` owns the real function and each host keeps a
#: one-line wrapper at the original name and signature, binding its own labels. Verified at
#: integration by the assertions in this file, which report the delegation themselves. Counting
#: them as forks would OVERSTATE the remaining work, which is exactly what this table exists to
#: prevent.
#: `reconcile_interrupted` JOINED THIS CLASS 2026-09-22 under runrecon-02 (`fduoj4`) E-01, moved out of
#: STILL_DOUBLE_DEFINED in the same change that shared it, per this file's re-base rule. `runner_shared`
#: owns the body; each host keeps a one-line wrapper at the original name and signature, injecting its
#: own `save_state`, because `save_state` in turn needs the class (c) DIVERGED `write_report` and a
#: shared body choosing one host's report renderer would silently give the other host the wrong format.
#: `run_viewer.repair_run` was re-pointed at the shared definition too, so all three callers now reach
#: ONE implementation. The delegation is proven per name by the fork-vs-wrapper test in this file.
THIN_WRAPPERS_OVER_RUNNER_SHARED = (
    # hostdedup Order 01 (`li44r9`) E-04: the three names MOVED here from `STILL_DOUBLE_DEFINED` above
    # in the same change that lifted them. See the note on that tuple.
    "_observe_between_turn_stop",
    "_record_deliberate_stop",
    "driver_actor",
    "reconcile_interrupted",
    "render_continuation_hint",
    "requeue_interrupted",
    "save_state",
    "write_report",
)

# Module constants defined twice with EQUAL values: they can be lifted with the loop.
#
# RE-MEASURED 2026-09-18 by `runnoop` Order 01 (`zz5yxq`): `SUCCESS_STATES` was REMOVED from this
# tuple because `run_queue` NO LONGER REACHES IT. This table's stated contract is that it "describes
# what the FUNCTION reaches", and the load-bearing test below fails when a listed name stops being
# reached, so leaving it here would make the table assert something false.
#
# WHY IT STOPPED BEING REACHED, so a reader can tell a real regression from this: the exit-code site
# used to pass the bare `SUCCESS_STATES` to `runner_stop.deliberate_stop_exit_code`, which applies ONE
# container to the WHOLE queue and therefore could not judge an item against the bar its own `action`
# earns. A `reviewed`-but-unapproved EXECUTE item is never dispatched, and that bar counted it as a
# success, so an approval-blocked queue exited 0 having done nothing (backlog `em0z50`). The site now
# calls `runner_shared.exit_code_statuses(...)`, which makes the per-item decision in SHARED code, so
# the name the function closes over is `runner_shared` (already classified in ALREADY_ONE_OBJECT) and
# no longer the constant.
#
# NOT A WEAKENING, AND THE COUNTS CONFIRM IT: `EXECUTION_SUCCESS_STATES` and `TERMINAL_STATES` are
# still reached and still pinned, `CLOSURE_TOTAL` is unchanged at 41 (measured), and the split
# analysis this table feeds is unaffected, because a name that moved INTO `runner_shared` is one
# fewer symbol a shared core would have to be injected with, not one more.
EQUAL_CONSTANTS = ("EXECUTION_SUCCESS_STATES", "TERMINAL_STATES")

# Defined twice with values that DIFFER BY HOST, by design: a hook input. Lifting it unchanged
# would print the wrong recovery command on one host.
DIVERGENT_CONSTANTS = ("DEPENDENCY_BLOCK_RECOVERY_HINT",)

CLOSURE_TOTAL = 41

# The five sites at which each host must refresh the shutdown reporter's published state. E-03's
# repair brought agy from THREE to FIVE, site for site with oc.
REGISTER_SIGNAL_REPORT_SITES = 5

# The one genuinely host-specific string in this function (F-6).
DRIVER_LABELS = {"oc_runipd": "opencode", "agy_runipd": "antigravity"}


# ------------------------------------------------------------------------------- AST helpers


def module_body(name: str) -> list[ast.stmt]:
    return ast.parse((AW / f"{name}.py").read_text(encoding="utf-8")).body


def top_level_defs(name: str) -> dict[str, ast.stmt]:
    return {
        node.name: node
        for node in module_body(name)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def module_index(name: str) -> dict[str, dict]:
    """Every module-level binding, and what binds it."""
    out: dict[str, dict] = {}
    for node in module_body(name):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = {"kind": "def", "node": node}
        elif isinstance(node, ast.ClassDef):
            out[node.name] = {"kind": "class", "node": node}
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    out[tgt.id] = {"kind": "assign", "value": node.value}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out[node.target.id] = {"kind": "assign", "value": node.value}
        elif isinstance(node, ast.Import):
            for alias in node.names:
                out[alias.asname or alias.name.split(".")[0]] = {
                    "kind": "import",
                    "module": alias.name,
                }
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                out[alias.asname or alias.name] = {
                    "kind": "importfrom",
                    "module": node.module or "",
                }
        elif isinstance(node, (ast.If, ast.Try)):
            for sub in ast.walk(node):
                if isinstance(sub, ast.ImportFrom):
                    for alias in sub.names:
                        out.setdefault(
                            alias.asname or alias.name,
                            {"kind": "importfrom", "module": sub.module or ""},
                        )
                elif isinstance(sub, ast.Import):
                    for alias in sub.names:
                        out.setdefault(
                            alias.asname or alias.name.split(".")[0],
                            {"kind": "import", "module": alias.name},
                        )
    return out


def run_queue_node(name: str) -> ast.FunctionDef:
    for node in module_body(name):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "run_queue"
        ):
            assert isinstance(node, ast.FunctionDef)
            return node
    raise AssertionError(f"{name} has no top-level run_queue")


def is_pure_delegation(node: ast.stmt) -> bool:
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
    fn = value.func
    return (
        isinstance(fn, ast.Attribute)
        and isinstance(fn.value, ast.Name)
        and fn.value.id == "runner_shared"
    )


def free_module_level_names(host: str) -> set[str]:
    """The closure, re-derived here so the table cannot drift from the code that produced it.

    A DELIBERATELY SIMPLER SCANNER than the committed evidence script: it collects every `Name`
    load in the function and intersects with the module index, then subtracts names bound anywhere
    in the body. Simpler is acceptable HERE because the assertions below are membership checks in
    that direction (every pinned name must still be reached), not an exact census, and the exact
    census lives in the evidence scanner. The one property that must hold is no FALSE NEGATIVE: a
    pinned name that stopped being reached must fail, and it does.
    """
    node = run_queue_node(host)
    loads = {
        n.id
        for n in ast.walk(node)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    }
    bound = {
        n.id
        for n in ast.walk(node)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
    }
    bound |= {a.arg for a in node.args.args + node.args.kwonlyargs}
    for sub in ast.walk(node):
        if isinstance(sub, (ast.Import, ast.ImportFrom)):
            for alias in sub.names:
                bound.add(alias.asname or alias.name.split(".")[0])
    index = module_index(host)
    return {name for name in loads - bound if name in index}


# ==================================================================================================
# The closure classification, asserted MECHANICALLY so a symbol changing class fails.
# ==================================================================================================


class TheClosureClassificationIsPinned(unittest.TestCase):
    """E-01's table, asserted rather than described, in the direction that catches silent drift."""

    def test_every_still_double_defined_symbol_really_is_defined_in_both_runners(self):
        for host in HOSTS:
            defs = top_level_defs(host)
            for name in STILL_DOUBLE_DEFINED:
                with self.subTest(host=host, symbol=name):
                    self.assertIn(
                        name,
                        defs,
                        f"{name} is no longer defined in {host}. If it was SHARED, that is "
                        "progress: remove it from STILL_DOUBLE_DEFINED in the SAME change and "
                        "record why, per the maintainer's re-base-deliberately rule",
                    )

    def test_every_still_double_defined_symbol_is_a_REAL_fork_not_a_thin_wrapper(self):
        """The distinction sibling `yrqyxb` established, applied here.

        A thin wrapper over `runner_shared` is syntactically a `def` in both modules, so a naive
        scan calls it duplication. Counting it as a fork would OVERSTATE the remaining work, which
        is the same category error as measuring body difference and inferring liftability, with the
        sign reversed.
        """
        for host in HOSTS:
            defs = top_level_defs(host)
            for name in STILL_DOUBLE_DEFINED:
                with self.subTest(host=host, symbol=name):
                    self.assertFalse(
                        is_pure_delegation(defs[name]),
                        f"{host}.{name} now DELEGATES to runner_shared, so it is the sanctioned "
                        "wrapper form rather than a fork: move it to "
                        "THIN_WRAPPERS_OVER_RUNNER_SHARED",
                    )

    def test_the_thin_wrappers_really_do_delegate_on_both_hosts(self):
        """The INVERSE of the test above. Without it, the wrapper list would be a place to hide a
        re-fork by asserting nothing about it."""
        for host in HOSTS:
            defs = top_level_defs(host)
            for name in THIN_WRAPPERS_OVER_RUNNER_SHARED:
                with self.subTest(host=host, symbol=name):
                    self.assertIn(name, defs, f"{host} lost its {name} wrapper")
                    self.assertTrue(
                        is_pure_delegation(defs[name]),
                        f"{host}.{name} is no longer a pure delegation to runner_shared; the "
                        "818uru OQ-02 wrapper ruling has been undone and the symbol RE-FORKED",
                    )

    def test_the_shared_resolving_names_really_do_resolve_in_runner_shared(self):
        shared_defs = set(top_level_defs("runner_shared"))
        for name in RESOLVES_IN_RUNNER_SHARED:
            with self.subTest(symbol=name):
                self.assertIn(
                    name,
                    shared_defs,
                    f"{name} no longer resolves in runner_shared, so the closure got WORSE and "
                    "the split got harder",
                )

    def test_the_already_one_object_names_really_are_one_object(self):
        """Object identity, not a name match: agy must reach the SAME object, not a copy."""
        skip = {"Path", "sys", "time", "contextlib", "runner_shared", "runner_stop"}
        for name in ALREADY_ONE_OBJECT:
            if name in skip:
                continue  # stdlib or a module alias; identity is trivially true
            with self.subTest(symbol=name):
                self.assertIs(
                    getattr(oc_runipd, name),
                    getattr(agy_runipd, name),
                    f"{name} is no longer ONE object across the two hosts; it has been re-forked",
                )

    def test_the_module_aliases_are_the_same_module_on_both_hosts(self):
        for name in ("runner_shared", "runner_stop"):
            with self.subTest(symbol=name):
                self.assertIs(getattr(oc_runipd, name), getattr(agy_runipd, name))

    def test_the_equal_constants_are_still_equal_across_hosts(self):
        for name in EQUAL_CONSTANTS:
            with self.subTest(symbol=name):
                self.assertEqual(
                    set(getattr(oc_runipd, name)),
                    set(getattr(agy_runipd, name)),
                    f"{name} used to be EQUAL on both hosts and now differs, so it can no longer "
                    "be lifted with the loop: it has become a hook input",
                )

    def test_the_divergent_constant_still_differs_by_host(self):
        """The INVERSE assertion for F-12. If these ever become equal the constant can be lifted,
        and this test is where that is noticed rather than assumed."""
        for name in DIVERGENT_CONSTANTS:
            with self.subTest(symbol=name):
                self.assertNotEqual(
                    getattr(oc_runipd, name),
                    getattr(agy_runipd, name),
                    f"{name} is now EQUAL on both hosts. That is a real simplification: move it "
                    "to EQUAL_CONSTANTS and say so",
                )

    def test_the_classes_are_disjoint(self):
        """A name in two classes means the table contradicts itself and no assertion above is safe."""
        groups = {
            "still-double-defined": set(STILL_DOUBLE_DEFINED),
            "resolves-in-runner-shared": set(RESOLVES_IN_RUNNER_SHARED),
            "already-one-object": set(ALREADY_ONE_OBJECT),
            "thin-wrapper": set(THIN_WRAPPERS_OVER_RUNNER_SHARED),
            "equal-constant": set(EQUAL_CONSTANTS),
            "divergent-constant": set(DIVERGENT_CONSTANTS),
        }
        names = list(groups)
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                with self.subTest(pair=(left, right)):
                    self.assertEqual(groups[left] & groups[right], set())

    def test_run_queue_still_closes_over_every_pinned_symbol(self):
        """The load-bearing direction: the table describes what the FUNCTION reaches.

        If a name stops being reached, the table is stale and every count computed from it is
        wrong, INCLUDING the injection count the split analysis rests on.
        """
        classified = (
            set(STILL_DOUBLE_DEFINED)
            | set(RESOLVES_IN_RUNNER_SHARED)
            | set(ALREADY_ONE_OBJECT)
            | set(THIN_WRAPPERS_OVER_RUNNER_SHARED)
            | set(EQUAL_CONSTANTS)
            | set(DIVERGENT_CONSTANTS)
        )
        for host in HOSTS:
            reached = free_module_level_names(host)
            missing = sorted(classified - reached)
            with self.subTest(host=host):
                self.assertEqual(
                    missing,
                    [],
                    f"{host}.run_queue no longer closes over {missing}; E-01's table is stale and "
                    "must be re-measured with the committed scanner before it is trusted",
                )

    def test_the_census_totals_are_what_the_plan_measured(self):
        # RE-MEASURED 2026-09-17 after sibling `tx6q0h` lifted the eight host-label symbols behind
        # one `HostLabels` descriptor: the named forks became the sanctioned one-line-wrapper form,
        # so they moved to THIN_WRAPPERS_OVER_RUNNER_SHARED. Re-measured from the tables above rather
        # than edited to fit, and each reclassification is proven individually by the fork-vs-wrapper
        # test in this class, which reports the delegation itself.
        #
        # 8 -> 9, RE-MEASURED 2026-09-18 by `runnoop` Order 01 (`zz5yxq`): `_integrate_stranded_lanes`
        # was added to `STILL_DOUBLE_DEFINED`. It is a REAL, PRE-EXISTING fork that the table never
        # classified (both hosts define their own; measured NOT the same object), not new work by that
        # plan. This number is DERIVED from the tuple above, so it is re-measured here rather than the
        # tuple being trimmed to preserve the old figure, which would have hidden the fork. The
        # fork-vs-wrapper test in this class proves the classification for every name listed,
        # including this one.
        #
        # 9 -> 5, RE-MEASURED IN THIS MERGE rather than taken from either side. main said 8
        # (runrecon-02 `fduoj4` E-01 shared `reconcile_interrupted`); the lane said 6 (hostdedup
        # Order 01 `li44r9` E-04 shared `_observe_between_turn_stop`, `_record_deliberate_stop` and
        # `requeue_interrupted`). The two sets are DISJOINT, so the census loses all four names and
        # EITHER side's number alone would have been wrong. `CLOSURE_TOTAL` is UNCHANGED at 41: no
        # name stopped being reached, each changed CLASS, which is what the two totals separate.
        self.assertEqual(
            len(STILL_DOUBLE_DEFINED)
            + len(RESOLVES_IN_RUNNER_SHARED)
            + len(ALREADY_ONE_OBJECT)
            + len(THIN_WRAPPERS_OVER_RUNNER_SHARED)
            + len(EQUAL_CONSTANTS)
            + len(DIVERGENT_CONSTANTS),
            CLOSURE_TOTAL,
            "the six classes must partition the 41 measured names exactly; a total that does not "
            "reach 41 means a name was dropped from the table rather than reclassified",
        )


# ==================================================================================================
# The permanently unmovable symbol: the INVERSE assertion.
# ==================================================================================================


class ThePinnedSymbolStayedPinned(unittest.TestCase):
    """`disable_lane_prompt` can NEVER resolve in `runner_shared` while the pin stands.

    ASSERTED IN THE INVERSE DIRECTION deliberately, so a later agent cannot "complete" the split by
    moving a symbol the maintainer's own guard pinned. If lifting it ever becomes correct, the
    change must edit BOTH this file and `UnmovableSymbolTests`, which is the point: two deliberate
    edits, not one silent one.
    """

    def test_it_is_still_defined_in_both_runners(self):
        for host in HOSTS:
            for name in PERMANENTLY_UNMOVABLE:
                with self.subTest(host=host, symbol=name):
                    self.assertIn(name, top_level_defs(host))

    def test_runner_shared_still_does_not_define_it(self):
        shared_defs = top_level_defs("runner_shared")
        for name in PERMANENTLY_UNMOVABLE:
            with self.subTest(symbol=name):
                self.assertNotIn(
                    name,
                    shared_defs,
                    f"{name} was lifted into runner_shared. `UnmovableSymbolTests` pins it in both "
                    "runners BECAUSE it mutates a module global that each host's own diverged "
                    "`_lane_reclaim_prompt` reads, so lifting it silently breaks prompt "
                    "suppression on a repeated interrupt in an unattended run",
                )

    def test_the_two_definitions_are_not_the_same_object(self):
        for name in PERMANENTLY_UNMOVABLE:
            with self.subTest(symbol=name):
                self.assertIsNot(getattr(oc_runipd, name), getattr(agy_runipd, name))

    def test_run_queue_still_calls_it_which_is_why_the_injection_is_permanent(self):
        """The reason the pin MATTERS to this plan, asserted rather than argued.

        If `run_queue` did not call it, the pin would be irrelevant to the split. It does, so any
        shared core must take it as a parameter forever.
        """
        for host in HOSTS:
            with self.subTest(host=host):
                node = run_queue_node(host)
                called = {
                    call.func.id
                    for call in ast.walk(node)
                    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                }
                self.assertIn(
                    "disable_lane_prompt",
                    called,
                    f"{host}.run_queue no longer calls disable_lane_prompt. If the call moved, the "
                    "permanent-injection argument in this plan's E-04 analysis no longer applies "
                    "and the analysis must be re-done rather than assumed",
                )


# ==================================================================================================
# E-03's repair, guarded so the sites cannot be lost again.
# ==================================================================================================


class TheSignalReportRefreshSitesArePinned(unittest.TestCase):
    """E-03: agy went from THREE `register_signal_report` sites to FIVE, matching oc site for site.

    THE COUNT IS PINNED RATHER THAN THE BEHAVIOR HERE ON PURPOSE, and the behavior is pinned
    separately by `TheExitCodeReflectsTheRealOutcome` in THIS file (it lived in a companion
    `..._characterization.py` until `7ebc2964` folded that file in here). Both are wanted: the
    behavioral test proves the reporter sees post-reload state, and this one names the SITES, so a
    future edit that deletes one is attributed to the deletion rather than debugged from a
    behavioral symptom.
    """

    def sites(self, host: str) -> list[int]:
        node = run_queue_node(host)
        return sorted(
            call.lineno
            for call in ast.walk(node)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "register_signal_report"
        )

    def test_both_hosts_refresh_at_five_sites(self):
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertEqual(
                    len(self.sites(host)),
                    REGISTER_SIGNAL_REPORT_SITES,
                    f"{host}.run_queue has {len(self.sites(host))} register_signal_report sites, "
                    f"expected {REGISTER_SIGNAL_REPORT_SITES}. oc_runipd.py's own comment states "
                    "the invariant: the reporter is refreshed after EACH state reload so it never "
                    "runs off a stale snapshot",
                )

    def test_the_two_hosts_have_the_SAME_number_of_sites(self):
        """The asymmetry E-03 repaired, asserted directly: a host with fewer refreshes has a
        staleness window the other does not."""
        self.assertEqual(
            len(self.sites("oc_runipd")),
            len(self.sites("agy_runipd")),
            "the hosts disagree on how many times the shutdown reporter is refreshed; the host "
            "with fewer reports from a pre-reload snapshot in exactly that many windows",
        )

    def test_every_ladder_reload_is_followed_by_a_refresh_on_both_hosts(self):
        """THE PROPERTY behind the count: a reload that CONTINUES THE LOOP must refresh.

        WHY THIS IS SCOPED TO THE LADDER RATHER THAN TO EVERY RELOAD, measured rather than assumed.
        `run_queue` reloads `state` at ten places per host, and a blanket "every reload must
        refresh" rule is WRONG: four of oc's ten sit on paths that immediately `break` out of the
        loop or hand `state` straight to an interrupt handler, and each of those reaches the
        end-of-run refresh (`register_signal_report` just before `emit_shutdown_report`) before any
        report can be rendered. Asserting the blanket rule reported those four as defects on
        CORRECT code, which would have made this guard a source of false alarms rather than a pin.

        The load-bearing case is the one E-03 repaired: a reload after which the loop KEEPS GOING,
        so an arbitrarily long window opens in which a signal can arrive against a dead snapshot.
        Both integration-ladder reloads are of that kind, and rungs 2/3 can block for minutes.

        So this test asserts the property for the reloads guarded by a
        `deferred_integration_items` test, which is exactly the ladder, and does so for BOTH hosts.
        """
        for host in HOSTS:
            with self.subTest(host=host):
                node = run_queue_node(host)
                ladder_blocks = [
                    sub
                    for sub in ast.walk(node)
                    if isinstance(sub, ast.If)
                    and "deferred_integration_items" in ast.unparse(sub.test)
                ]
                self.assertTrue(
                    ladder_blocks,
                    f"{host}.run_queue no longer guards a block on deferred_integration_items; the "
                    "integration ladder has moved and this guard must be re-based on its new shape",
                )
                checked = 0
                unrefreshed: list[int] = []
                for block in ladder_blocks:
                    body = block.body
                    for index, stmt in enumerate(body):
                        if not self._is_state_reload(stmt):
                            continue
                        checked += 1
                        if not any(self._is_refresh(s) for s in body[index + 1 :]):
                            unrefreshed.append(stmt.lineno)
                self.assertGreaterEqual(
                    checked,
                    2,
                    f"{host}: expected both ladder rungs to reload state; found {checked}. A "
                    "guard that checks fewer reloads than exist proves less than it claims",
                )
                self.assertEqual(
                    unrefreshed,
                    [],
                    f"{host}.run_queue rebinds `state` at line(s) {unrefreshed} inside the "
                    "integration ladder and then CONTINUES THE LOOP without refreshing the "
                    "shutdown reporter. A signal arriving in that window reports a PRE-reload "
                    "snapshot: the item shows as still deferred after it has integrated. That is "
                    "exactly the defect rununify ty3cj6 E-03 repaired on agy",
                )

    def test_the_exit_path_reloads_are_covered_by_the_end_of_run_refresh(self):
        """The other half of the scoping decision above, asserted so it is not merely asserted.

        The reloads this guard deliberately does NOT require an inline refresh for are the ones on
        break/interrupt paths. Their safety rests on a refresh existing AFTER the loop, so that is
        pinned here: if the end-of-run refresh were removed, those paths WOULD become stale and the
        scoping argument above would collapse.
        """
        for host in HOSTS:
            with self.subTest(host=host):
                node = run_queue_node(host)
                loop_end = max(
                    (stmt.end_lineno or stmt.lineno)
                    for stmt in node.body
                    if isinstance(stmt, ast.While)
                )
                after_loop = [
                    call.lineno
                    for call in ast.walk(node)
                    if isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name)
                    and call.func.id == "register_signal_report"
                    and call.lineno > loop_end
                ]
                self.assertTrue(
                    after_loop,
                    f"{host}.run_queue has no register_signal_report AFTER the dispatch loop. The "
                    "break/interrupt reload paths rely on it, so removing it strands them on a "
                    "stale snapshot",
                )

    # -- helpers ---------------------------------------------------------------------------------
    def _statement_blocks(self, node: ast.AST):
        """Every statement LIST in the subtree, so ordering comparisons stay within one block.

        Comparing line numbers across sibling branches would be wrong: a refresh on one branch does
        not cover a reload on another.
        """
        for sub in ast.walk(node):
            for field in ("body", "orelse", "finalbody"):
                block = getattr(sub, field, None)
                if isinstance(block, list) and block and isinstance(block[0], ast.stmt):
                    yield block

    def _is_state_reload(self, stmt: ast.stmt) -> bool:
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            return False
        target = stmt.targets[0]
        if not (isinstance(target, ast.Name) and target.id == "state"):
            return False
        return (
            isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Name)
            and stmt.value.func.id == "load_state"
        )

    def _is_refresh(self, stmt: ast.stmt) -> bool:
        return (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Name)
            and stmt.value.func.id == "register_signal_report"
        )

    def test_the_refresh_is_one_shared_function_not_two(self):
        """A per-host copy would drift, and F-2's retraction rests on this identity holding."""
        self.assertIs(
            oc_runipd.register_signal_report, agy_runipd.register_signal_report
        )

    def test_the_repair_added_no_save_state_call_site(self):
        """F-11: the wrapper-ruling census counts `save_state` sites per runner and pins them.

        E-03 adds `register_signal_report` calls only, so both counts must be UNCHANGED. Asserted
        here as well as in `WrapperTests` because it is this plan's obligation to show it did not
        disturb that census.
        """
        for host in HOSTS:
            with self.subTest(host=host):
                node = run_queue_node(host)
                count = sum(
                    1
                    for call in ast.walk(node)
                    if isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name)
                    and call.func.id == "save_state"
                )
                self.assertEqual(
                    count,
                    13,
                    f"{host}.run_queue's save_state call count moved from 13 to {count}; "
                    "WrapperTests::test_no_call_site_was_rewritten pins the per-runner total and "
                    "a change here moves it",
                )


# ==================================================================================================
# The host-specific boundary, and the source-reading pins the split must re-base.
HOST_PAIRS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))


class RunQueueCase(unittest.TestCase):
    """Drive a host's real `run_queue` over a synthetic queue, with the agent turn stubbed."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.turns: list[str] = []

    # ---- fixtures --------------------------------------------------------------------------
    def item(
        self,
        id6: str,
        *,
        setid: str = "synth",
        action: str = "execute",
        status: str = "queued",
        deps: tuple[str, ...] = (),
        position: int = 1,
        kind: str = "child",
        **extra,
    ) -> dict:
        entry = {
            "position": position,
            "id6": id6,
            "setid": setid,
            "action": action,
            "kind": kind,
            "status": status,
            "dependencies": list(deps),
            "attempts": [],
        }
        entry.update(extra)
        return entry

    def make_run(
        self, queue: list[dict], *, run_id: str = "run-char", options=None
    ) -> pathlib.Path:
        run_dir = self.root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "repo": str(self.root),
            "created_at": "2026-09-17T00:00:00+00:00",
            "updated_at": "2026-09-17T00:00:00+00:00",
            "selectors": ["synthetic"],
            "options": dict(options or {}),
            "set_sessions": {},
            "queue": queue,
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return run_dir

    # ---- driving ---------------------------------------------------------------------------
    def drive(
        self,
        module,
        run_dir: pathlib.Path,
        *,
        retry_incomplete: bool = False,
        on_turn=None,
        budget: int = 40,
        **kwargs,
    ):
        """Run the loop with `execute_item` stubbed. FAILS LOUDLY on a spin rather than hanging."""
        seen = {"n": 0}

        def fake_exec(rd, st, it, *a, **kw):
            seen["n"] += 1
            if seen["n"] > budget:
                raise AssertionError(
                    f"SPIN: {seen['n']} dispatches without the run terminating; the loop is not "
                    "converging on a terminal state for every item"
                )
            self.turns.append(str(it.get("id6")))
            if on_turn is not None:
                on_turn(it)
            else:
                it["status"] = "executed"
                # AND FINALIZE IT ON DISK, because since 2026-09-19 an `executed:` edge is answered
                # from the plan's DIRECTORY and not from its in-run status (the in-queue shortcut was
                # deleted after it released a dependent against work that was never integrated). A
                # stub that only sets the in-memory status models a run in which finalize never
                # happened, so a dependent would correctly refuse and this harness would stop being
                # able to test dispatch ORDER at all. Writing the plan into `executed/` is what a real
                # verified turn does, so it is the faithful stub.
                self._finalize_on_disk(str(it.get("id6")))
            module.save_state(rd, st)

        buf = io.StringIO()
        with patch.object(module, "execute_item", side_effect=fake_exec):
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                rc = module.run_queue(
                    run_dir, retry_incomplete=retry_incomplete, **kwargs
                )
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        return rc, state, buf.getvalue()

    # ---- reading ---------------------------------------------------------------------------
    def _finalize_on_disk(self, id6: str) -> None:
        """Write ``id6``'s plan into `executed/`, as a real verified turn's finalize would."""
        executed = self.root / ".aw" / "records" / "plans" / "executed"
        executed.mkdir(parents=True, exist_ok=True)
        (executed / f"20260919-synth-01-{id6}-stub.ipd.md").write_text(
            f"# IPD: stub\n\n- Id: {id6}\n- Status: executed\n", encoding="utf-8"
        )

    def statuses(self, state: dict) -> dict[str, str]:
        return {it["id6"]: it["status"] for it in state["queue"]}

    def events(self, run_dir: pathlib.Path) -> list[dict]:
        path = run_dir / "events.jsonl"
        if not path.exists():
            return []
        return [
            json.loads(ln)
            for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]

    # ---- the signal-report ledger -----------------------------------------------------------
    def published(self, module=None) -> dict | None:
        """Read the ledger `register_signal_report` writes.

        There is exactly ONE ledger: `_SIGNAL_REPORT_STATE` is defined in `oc_runipd` and agy
        reaches the SAME dict because it imports `register_signal_report` from oc
        (`agy_runipd.py:408`), so `oc.register_signal_report is agy.register_signal_report`. That is
        why this reads oc's module global for BOTH hosts rather than each host's own: agy has no
        `_SIGNAL_REPORT_STATE` attribute of its own, and asserting against a per-host copy would be
        asserting against something that does not exist.
        """
        del module  # one shared ledger; the parameter is kept for call-site symmetry
        return oc_runipd._SIGNAL_REPORT_STATE.get("state")

    def clear_published(self) -> None:
        """The ledger is a PROCESS global, so a prior test's run would otherwise leak into this one.

        This matters for correctness, not tidiness: without it, a staleness assertion could be
        satisfied by an EARLIER test's state object and the guard would not fail on broken code.
        """
        oc_runipd._SIGNAL_REPORT_STATE.clear()


class TheLoopDispatchesEveryRunnableItem(RunQueueCase):
    """The baseline behavior: an independent queue drains, on both hosts, in dependency order."""

    def test_an_independent_queue_drains_completely(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        self.item("aaa111", position=1),
                        self.item("bbb222", position=2),
                        self.item("ccc333", position=3),
                    ],
                    run_id=f"drain-{label}",
                )
                rc, state, _ = self.drive(module, run_dir)
                self.assertEqual(rc, 0, f"{label}: a fully drained queue must exit 0")
                self.assertEqual(
                    self.statuses(state),
                    {"aaa111": "executed", "bbb222": "executed", "ccc333": "executed"},
                )
                self.assertEqual(sorted(self.turns), ["aaa111", "bbb222", "ccc333"])

    def test_a_dependency_is_dispatched_before_its_dependent(self):
        """Declared edges are authoritative; this is the property `queue_sort_key` exists for."""
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        # The DEPENDENT is listed first, so position order alone would get it wrong.
                        self.item("dep222", position=1, deps=("executed:pre111",)),
                        self.item("pre111", position=2),
                    ],
                    run_id=f"order-{label}",
                )
                rc, state, _ = self.drive(module, run_dir)
                self.assertEqual(rc, 0)
                self.assertEqual(
                    self.statuses(state), {"pre111": "executed", "dep222": "executed"}
                )
                self.assertEqual(
                    self.turns,
                    ["pre111", "dep222"],
                    f"{label}: the dependency must be dispatched FIRST regardless of position",
                )


class AnUnsatisfiableDependencyBlocksRatherThanStalls(RunQueueCase):
    """The cascade, and the recovery hint attached to it. F-12: the hint DIFFERS per host."""

    def test_a_dependent_of_a_failed_item_is_marked_dependency_blocked(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        self.item("fail11", position=1),
                        self.item("dep222", position=2, deps=("executed:fail11",)),
                    ],
                    run_id=f"cascade-{label}",
                )

                def on_turn(item):
                    item["status"] = (
                        "failed-safely" if item["id6"] == "fail11" else "executed"
                    )

                rc, state, _ = self.drive(module, run_dir, on_turn=on_turn)
                statuses = self.statuses(state)
                self.assertEqual(statuses["fail11"], "failed-safely")
                self.assertEqual(
                    statuses["dep222"],
                    "dependency-blocked",
                    f"{label}: a dependent of a non-success terminal item must be blocked, "
                    "not left queued (which would stall the queue)",
                )
                self.assertEqual(
                    self.turns,
                    ["fail11"],
                    f"{label}: the blocked item must NOT spend an agent turn",
                )
                self.assertNotEqual(
                    rc, 0, f"{label}: a run leaving blocked work must not exit 0"
                )

    def test_the_blocked_item_carries_its_host_s_own_recovery_hint(self):
        """F-12: `DEPENDENCY_BLOCK_RECOVERY_HINT` is host-divergent BY DESIGN.

        A split that lifted this constant unchanged would print the wrong recovery command on one
        host, so the divergence is pinned here as behavior: the hint that lands in state must name
        THIS host's own resume verb.
        """
        expected = {
            "oc_runipd": "aw oc runipd resume",
            "agy_runipd": "aw agy runipd resume",
        }
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [self.item("dep222", position=1, deps=("executed:absent",))],
                    run_id=f"hint-{label}",
                )
                _, state, _ = self.drive(module, run_dir)
                entry = state["queue"][0]
                self.assertEqual(entry["status"], "dependency-blocked")
                self.assertIn(
                    expected[label],
                    entry["dependency_block_recovery"],
                    f"{label}: the recovery hint must name this host's OWN resume verb",
                )
                self.assertNotIn(
                    expected["agy_runipd" if label == "oc_runipd" else "oc_runipd"],
                    entry["dependency_block_recovery"],
                    f"{label}: the hint must not name the OTHER host's verb",
                )

    def test_an_unsatisfied_dependency_records_both_the_flat_list_and_the_reasons(self):
        """The additive companion key, whose shape existing consumers depend on."""
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [self.item("dep222", position=1, deps=("executed:absent",))],
                    run_id=f"reasons-{label}",
                )
                _, state, _ = self.drive(module, run_dir)
                entry = state["queue"][0]
                self.assertIsInstance(entry["unsatisfied_dependencies"], list)
                self.assertTrue(
                    all(isinstance(x, str) for x in entry["unsatisfied_dependencies"]),
                    f"{label}: the flat list must stay list[str] for existing consumers",
                )
                self.assertIn("unsatisfied_dependency_reasons", entry)


class TheDrainArmLabelsOnlyWhatIsPermanentlyBlocked(RunQueueCase):
    """depblock 01 (`akzy45`) E-02/E-05: the drain arm through the REAL loop, on BOTH hosts.

    WHY THIS CLASS IS HERE AND NOT ONLY BESIDE THE PREDICATE. The classification itself is unit-tested
    in `tests/test_runner_item_dependencies.py`, but each host owns its OWN `run_queue` and therefore its
    own copy of the labelling loop, so a correct predicate wired into only one host would leave that
    file green while the other host kept over-labelling. These cases drive the real loop, so they fail if
    the wiring is missing on either side.

    THE ARM USED TO LABEL EVERY REMAINING QUEUED ITEM AND BREAK, which is two defects: an item whose
    prerequisite merely had not finished yet was given a TERMINAL status (recoverable only with
    `--retry-incomplete`), and a single unsatisfiable node could end a run holding other work.

    NOTE THE SPIN DETECTOR IS LOAD-BEARING FOR EVERY CASE HERE. `drive` fails after `budget` dispatches
    rather than hanging, so "leave it queued instead of labelling it" cannot pass by looping forever:
    the wrong fix (re-testing a prerequisite nothing can advance) shows up as a SPIN failure, which is
    exactly the regression `kxkc04`'s prescription ran into and which `dispatch_orchestrator_item`
    records.
    """

    def test_a_dependent_of_an_INTERRUPTED_prerequisite_is_left_queued_not_blocked(
        self,
    ):
        """The transient case. `interrupted` is NOT terminal, so a terminal label would over-claim.

        THE HARM IS CONCRETE AND ASYMMETRIC, which is why this is worth a behavior test: a bare `resume`
        re-queues an `interrupted` item with NO flag (`requeue_interrupted` selects on exactly that
        status), while a `dependency-blocked` item needs `--retry-incomplete`. So labelling the
        dependent terminally took a recovery that was free and made it require a specific flag the
        operator has to know about.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        self.item("pre111", position=1),
                        self.item("dep222", position=2, deps=("executed:pre111",)),
                    ],
                    run_id=f"transient-{label}",
                )

                def on_turn(item):
                    # The prerequisite ends NON-terminally, which is what a stall or an interrupt
                    # leaves behind. Deliberately NOT finalized on disk.
                    item["status"] = "interrupted"

                rc, state, out = self.drive(module, run_dir, on_turn=on_turn)
                statuses = self.statuses(state)
                self.assertEqual(statuses["pre111"], "interrupted")
                self.assertEqual(
                    statuses["dep222"],
                    "queued",
                    f"{label}: THE FIX. Its prerequisite is non-terminal, so the dependent must be "
                    "left `queued` for the next invocation rather than given a TERMINAL "
                    "`dependency-blocked` that only `--retry-incomplete` can undo",
                )
                self.assertEqual(
                    self.turns,
                    ["pre111"],
                    f"{label}: the waiting item must not spend an agent turn",
                )
                self.assertNotEqual(
                    rc,
                    0,
                    f"{label}: leaving a wait outstanding must NOT exit 0 (OQ-03: exit AND report, "
                    "never a silent clean finish over unfinished work)",
                )
                entry = next(it for it in state["queue"] if it["id6"] == "dep222")
                record = entry.get(runner_shared.TRANSIENT_DEPENDENCY_WAIT_KEY)
                self.assertIsNotNone(
                    record,
                    f"{label}: an item the arm DECLINES to label must still carry its reason and "
                    "recovery route. The terminal path attaches the hint inside the labelling loop, "
                    "so without this record the item exits with no explanation at all - less "
                    "informative than the dead end it replaced",
                )
                self.assertEqual(
                    record["unsatisfied_dependencies"], ["executed:pre111"]
                )
                self.assertNotIn(
                    "unsatisfied_dependencies",
                    entry,
                    f"{label}: the TOP-LEVEL key must stay absent, or a still-`queued` item renders "
                    "as `dependency_not_met` in the disposition summary (a fabricated disposition)",
                )
                self.assertIn(
                    "dependency-wait-transient",
                    [e.get("event") for e in self.events(run_dir)],
                    f"{label}: the verdict must reach events.jsonl",
                )

    def test_a_dependent_of_a_DEAD_prerequisite_is_still_labelled_terminally(self):
        """The anti-over-suppression guard, driven through the loop.

        Kept in the SAME class as the case above so the pair cannot be read apart: they differ ONLY in
        whether the prerequisite's status is terminal, and they must reach OPPOSITE dispositions. If
        both go `queued`, the narrowing was over-applied and the runner now waits on work that can
        never happen.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        self.item("pre111", position=1),
                        self.item("dep222", position=2, deps=("executed:pre111",)),
                    ],
                    run_id=f"permanent-{label}",
                )

                def on_turn(item):
                    item["status"] = "failed-safely"

                _rc, state, _ = self.drive(module, run_dir, on_turn=on_turn)
                entry = next(it for it in state["queue"] if it["id6"] == "dep222")
                self.assertEqual(
                    entry["status"],
                    "dependency-blocked",
                    f"{label}: a genuinely dead prerequisite must STILL block its dependents",
                )
                self.assertEqual(
                    entry["unsatisfied_dependencies"],
                    ["executed:pre111 (target failed-safely)"],
                    f"{label}: and it is labelled by the CASCADE, whose token carries the reason "
                    "INLINE and which writes no separate recovery hint. Asserted in this exact shape "
                    "because it proves WHICH writer acted: the cascade runs first in the loop, so a "
                    "dead prerequisite never reaches the drain arm at all. An earlier draft of this "
                    "test wrongly demanded `dependency_block_recovery` here; that key belongs to the "
                    "DRAIN path, and the divergence between the two writers' shapes is pre-existing "
                    "and is documented at `run_selection_policy.derive_item_disposition`",
                )
                self.assertNotIn(
                    runner_shared.TRANSIENT_DEPENDENCY_WAIT_KEY,
                    entry,
                    f"{label}: a permanently blocked item must NOT also be recorded as waiting",
                )

    def test_a_CYCLE_still_terminates_the_run_rather_than_waiting_forever(self):
        """A permanent-drain guard. Every member of a cycle looks non-terminal.

        Without the cycle test in the classification this case would read as a recoverable wait, and the
        run would end claiming the operator can resume into something that can never resolve.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        self.item("aaa111", position=1, deps=("executed:bbb222",)),
                        self.item("bbb222", position=2, deps=("executed:aaa111",)),
                    ],
                    run_id=f"cycle-{label}",
                )
                rc, state, _ = self.drive(module, run_dir)
                self.assertEqual(
                    self.statuses(state),
                    {"aaa111": "dependency-blocked", "bbb222": "dependency-blocked"},
                    f"{label}: both members of a cycle must receive the TERMINAL label",
                )
                self.assertEqual(
                    self.turns, [], f"{label}: a cycle must spend no agent turn"
                )
                self.assertNotEqual(rc, 0)

    def test_a_DANGLING_EXTERNAL_edge_still_terminates_the_run(self):
        """The second permanent-drain guard: a target this run cannot advance at all.

        There is no `--with-dependencies` closure inside a frozen run, so waiting is unbounded by
        construction and the terminal label is the truthful answer.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [self.item("dep222", position=1, deps=("executed:absent",))],
                    run_id=f"dangling-{label}",
                )
                rc, state, _ = self.drive(module, run_dir)
                entry = state["queue"][0]
                self.assertEqual(
                    entry["status"],
                    "dependency-blocked",
                    f"{label}: an unsatisfiable external edge stays TERMINAL",
                )
                self.assertNotIn(runner_shared.TRANSIENT_DEPENDENCY_WAIT_KEY, entry)
                self.assertNotEqual(rc, 0)

    def test_the_drain_no_longer_labels_an_INDEPENDENT_item_it_never_judged(self):
        """The ALL-OR-NOTHING half (the plan's Part 2), which the measured incident did NOT exercise.

        The arm looped over EVERY remaining queued item and labelled it, so a run could end with items
        marked `dependency-blocked` that had no unmet dependency at all. Here `solo33` declares NOTHING
        and is only queued behind a transiently-waiting item; it must not inherit a terminal label.

        NOTE WHAT IS AND IS NOT CLAIMED: `solo33` is independent, so the loop DISPATCHES it before the
        drain is ever reached. That is the point - the run makes all the forward progress it can - and it
        is why this asserts `executed` rather than `queued`.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        self.item("pre111", position=1),
                        self.item("dep222", position=2, deps=("executed:pre111",)),
                        self.item("solo33", position=3),
                    ],
                    run_id=f"allornothing-{label}",
                )

                def on_turn(item):
                    if item["id6"] == "pre111":
                        item["status"] = "interrupted"
                    else:
                        item["status"] = "executed"
                        self._finalize_on_disk(str(item["id6"]))

                _rc, state, _ = self.drive(module, run_dir, on_turn=on_turn)
                statuses = self.statuses(state)
                self.assertEqual(
                    statuses["solo33"],
                    "executed",
                    f"{label}: an INDEPENDENT item must be dispatched, not swept into a "
                    "dependency-blocked label by a drain it was never judged by",
                )
                self.assertEqual(
                    statuses["dep222"],
                    "queued",
                    f"{label}: and the genuinely waiting item is left queued",
                )

    def test_both_hosts_reach_IDENTICAL_dispositions_on_the_same_fixture(self):
        """E-04's cross-host claim as BEHAVIOR, not only as object identity.

        Object identity proves both hosts hold the same predicate; it does NOT prove both hosts CALL
        it. `pgq326` E-07 measured exactly that gap: agy shared the orchestrator DECIDER while lacking
        the branch that acted on it, and every identity assertion still passed. So the dispositions
        themselves are compared across hosts here.
        """
        fixtures = {
            "transient": (("pre111", ()), ("dep222", ("executed:pre111",))),
            "cycle": (
                ("aaa111", ("executed:bbb222",)),
                ("bbb222", ("executed:aaa111",)),
            ),
            "dangling": (("dep222", ("executed:absent",)),),
        }
        for name, rows in fixtures.items():
            observed = {}
            for label, module in HOST_PAIRS:
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        self.item(id6, position=i, deps=deps)
                        for i, (id6, deps) in enumerate(rows, start=1)
                    ],
                    run_id=f"parity-{name}-{label}",
                )

                def on_turn(item):
                    item["status"] = "interrupted"

                _rc, state, _ = self.drive(module, run_dir, on_turn=on_turn)
                observed[label] = self.statuses(state)
            self.assertEqual(
                observed["oc_runipd"],
                observed["agy_runipd"],
                f"fixture {name!r}: the two hosts disposed of the SAME queue differently, so one of "
                "them is not routing its drain arm through the shared classification",
            )


class TheRetryIncompleteFlagRequeuesTheStatesItDeclares(RunQueueCase):
    """`--retry-incomplete`'s status set, as behavior. F-3: oc requires the argument, agy defaults it."""

    REQUEUED = (
        "interrupted",
        "substantially-complete",
        "partial",
        "failed-safely",
        "blocked",
        "dependency-blocked",
        "merge-needs-human",
        "merge-refused",
        "merge-retry",
    )

    def test_every_declared_non_terminal_state_is_requeued_and_dispatched(self):
        for label, module in HOST_PAIRS:
            for status in self.REQUEUED:
                with self.subTest(host=label, status=status):
                    self.turns.clear()
                    run_dir = self.make_run(
                        [self.item("rty111", position=1, status=status)],
                        run_id=f"retry-{label}-{status}",
                    )
                    rc, state, _ = self.drive(module, run_dir, retry_incomplete=True)
                    self.assertEqual(
                        self.statuses(state)["rty111"],
                        "executed",
                        f"{label}: --retry-incomplete must re-queue a {status!r} item",
                    )
                    self.assertEqual(self.turns, ["rty111"])
                    self.assertEqual(rc, 0)

    def test_a_requeued_item_is_dispatched_in_recovery_mode(self):
        """`recovery=True` is what tells the turn it is a retry rather than a first attempt.

        The flag reaches the turn as the KEYWORD, not as the item key: the loop `pop`s
        `recovery_next` off the item and passes `recovery=` (`oc_runipd.py:8870`). Asserting on the
        item key would therefore always see `None` and the test would be vacuous.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                seen: list[object] = []

                def fake_exec(rd, st, it, *a, **kw):
                    seen.append(kw.get("recovery"))
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("rty111", position=1, status="partial")],
                    run_id=f"recovery-{label}",
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=fake_exec):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=True)
                self.assertEqual(
                    seen,
                    [True],
                    f"{label}: a re-queued item must be dispatched with recovery=True",
                )

    def test_a_first_attempt_is_not_dispatched_in_recovery_mode(self):
        """The inverse, so the assertion above cannot pass on a hardcoded True."""
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                seen: list[object] = []

                def fake_exec(rd, st, it, *a, **kw):
                    seen.append(kw.get("recovery"))
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("fst111", position=1)], run_id=f"firstattempt-{label}"
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=fake_exec):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)
                self.assertEqual(
                    seen,
                    [False],
                    f"{label}: a first attempt must not claim recovery mode",
                )

    def test_without_the_flag_an_incomplete_item_is_left_alone(self):
        """The inverse: the flag is the ONLY thing that re-queues these, so absence must be inert."""
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [self.item("rty111", position=1, status="partial")],
                    run_id=f"noretry-{label}",
                )
                _, state, _ = self.drive(module, run_dir, retry_incomplete=False)
                self.assertEqual(self.statuses(state)["rty111"], "partial")
                self.assertEqual(
                    self.turns,
                    [],
                    f"{label}: without the flag nothing may be re-dispatched",
                )

    def test_an_indeterminate_item_is_refused_even_under_the_flag(self):
        """runstop `m0z0ti` R19: a force-interrupted item's outcome was never established, so a
        broader retry flag is NOT permission to re-run it. This is the SECOND route into the requeue
        and it must agree with the first."""
        from agent_workflows import runner_stop

        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                item = self.item("ind111", position=1, status="interrupted")
                run_dir = self.make_run([item], run_id=f"indet-{label}")
                with patch.object(runner_stop, "is_indeterminate", return_value=True):
                    _, state, _ = self.drive(module, run_dir, retry_incomplete=True)
                self.assertEqual(
                    self.statuses(state)["ind111"],
                    "interrupted",
                    f"{label}: an indeterminate item must NOT be re-queued by --retry-incomplete",
                )
                self.assertEqual(self.turns, [])


class TheDisplayOptionsAreFrozenOnceAndTogether(RunQueueCase):
    """The `output_mode`/`verbosity` re-choice, and its ONE `save_state`.

    The shared persist is deliberate (`WrapperTests::test_no_call_site_was_rewritten` counts
    `save_state` sites per runner), so this pins the OBSERVABLE half: both land, and `None` means
    "operator did not pass the flag" and must leave a frozen value alone.
    """

    def test_both_display_options_are_persisted_when_supplied(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                run_dir = self.make_run([], run_id=f"display-{label}")
                self.drive(module, run_dir, output_mode="plain", verbosity=2)
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(state["options"]["output_mode"], "plain")
                self.assertEqual(state["options"]["verbosity"], 2)

    def test_none_leaves_a_frozen_value_untouched(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                run_dir = self.make_run(
                    [],
                    run_id=f"frozen-{label}",
                    options={"output_mode": "json", "verbosity": 3},
                )
                self.drive(module, run_dir, output_mode=None, verbosity=None)
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(state["options"]["output_mode"], "json")
                self.assertEqual(state["options"]["verbosity"], 3)

    def test_verbosity_is_coerced_to_int(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                run_dir = self.make_run([], run_id=f"coerce-{label}")
                self.drive(module, run_dir, verbosity=True)
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertIsInstance(state["options"]["verbosity"], int)


class TheSignalReporterSeesPostReloadState(RunQueueCase):
    """F-9, THE DEFECT THIS PLAN REPAIRS, pinned as behavior on BOTH hosts.

    `run_queue` publishes its live `state` for the shutdown reporter through
    `register_signal_report`. `state` is REBOUND by every `load_state` inside the loop, so the
    published reference is stale until it is refreshed. `oc_runipd.py`'s own comment states the
    invariant: "`register_signal_report` is called again after each state reload so the report never
    runs off a stale snapshot".

    Measured at plan-execution HEAD, oc called it FIVE times inside the loop and agy THREE: agy
    omitted the refresh after BOTH integration-ladder reloads. So on `aw agy run`, a signal arriving
    there reported PRE-reload item states.

    THE TEST IS BEHAVIORAL, not a call count: it asserts that the object the reporter would read is
    the SAME object the loop is currently working with, at every point the loop reloads state. That
    property is what the call sites exist to produce, and it survives a relocation.
    """

    def test_the_published_state_is_the_live_object_at_the_end_of_the_run(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                self.clear_published()
                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"pub-{label}"
                )
                _, state, _ = self.drive(module, run_dir)
                published = self.published(module)
                assert isinstance(published, dict), f"{label}: nothing was published"
                self.assertEqual(
                    {it["id6"]: it["status"] for it in published["queue"]},
                    {"aaa111": "executed"},
                    f"{label}: the reporter must see the FINAL statuses, not a pre-turn snapshot",
                )

    def test_the_published_state_is_refreshed_after_every_reload_in_the_loop(self):
        """The invariant, asserted at each reload rather than only at the end.

        `load_state` is wrapped so that immediately AFTER the loop takes a fresh state object, the
        published reference is compared. A refresh that the host omits shows up as the published
        object being a DIFFERENT dict from the one the loop just loaded, which is exactly the
        staleness F-9 describes. Only reloads that happen while a report could fire are checked, so
        the pre-loop initial load is excluded by construction (it is followed immediately by the
        first registration).
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                self.clear_published()
                run_dir = self.make_run(
                    [self.item("aaa111", position=1), self.item("bbb222", position=2)],
                    run_id=f"refresh-{label}",
                )
                real_load = module.load_state
                stale: list[int] = []
                loads = {"n": 0}

                def tracking_load(rd, *a, **kw):
                    loaded = real_load(rd, *a, **kw)
                    loads["n"] += 1
                    return loaded

                def fake_exec(rd, st, it, *a, **kw):
                    self.turns.append(str(it.get("id6")))
                    it["status"] = "executed"
                    module.save_state(rd, st)
                    # At the moment a turn ends, the reporter must be able to see THIS item's status.
                    pub = self.published(module)
                    if not isinstance(pub, dict):
                        stale.append(-1)
                        return
                    seen = {e["id6"]: e["status"] for e in pub["queue"]}
                    if seen.get(str(it.get("id6"))) is None:
                        stale.append(len(self.turns))

                buf = io.StringIO()
                with patch.object(module, "load_state", side_effect=tracking_load):
                    with patch.object(module, "execute_item", side_effect=fake_exec):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            module.run_queue(run_dir, retry_incomplete=False)

                self.assertGreater(
                    loads["n"], 2, f"{label}: the loop must reload state per iteration"
                )
                self.assertEqual(
                    stale,
                    [],
                    f"{label}: the reporter saw a snapshot missing an item the loop had already "
                    "processed; register_signal_report was not refreshed after a reload",
                )

    def test_the_reporter_is_published_before_the_first_turn_runs(self):
        """An interrupt at any point must report from real state, including before turn one."""
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                self.clear_published()
                observed: list[object] = []

                def fake_exec(rd, st, it, *a, **kw):
                    observed.append(self.published(module))
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"prepub-{label}"
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=fake_exec):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)
                self.assertTrue(observed, f"{label}: the turn never ran")
                self.assertIsInstance(
                    observed[0],
                    dict,
                    f"{label}: state must be published BEFORE the first turn starts",
                )


class TheIntegrationLadderIsReachedFromTheLoop(RunQueueCase):
    """The two F-9 branches, which were BOTH uncovered on agy and both missing the refresh.

    RUNG 1 fires at the top of the loop for any deferred item. RUNGS 2/3 fire when `runnable is
    None`, which covers both the last-item case and the all-deferred case.
    """

    def test_rung_one_reattempts_a_deferred_integration_at_the_top_of_the_loop(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                calls: list[dict] = []

                def retry(rd, st, *a, **kw):
                    calls.append(dict(kw))
                    for entry in st["queue"]:
                        if entry["status"] == "merge-retry":
                            entry["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [
                        self.item("def111", position=1, status="merge-retry"),
                        self.item("aaa222", position=2),
                    ],
                    run_id=f"rung1-{label}",
                )
                with patch.object(
                    module, "retry_deferred_integrations", side_effect=retry
                ):
                    rc, state, _ = self.drive(module, run_dir)
                self.assertTrue(
                    calls, f"{label}: rung 1 never fired for a deferred item"
                )
                self.assertEqual(
                    calls[0].get("poll"),
                    None,
                    f"{label}: rung 1 must be the FREE re-attempt (no poll)",
                )
                self.assertEqual(self.statuses(state)["def111"], "executed")
                self.assertEqual(rc, 0)

    def test_rungs_two_and_three_fire_when_nothing_else_is_runnable(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                polled: list[dict] = []

                def retry(rd, st, *a, **kw):
                    polled.append(dict(kw))
                    if kw.get("poll"):
                        for entry in st["queue"]:
                            if entry["status"] == "merge-retry":
                                entry["status"] = "executed"
                        module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("def111", position=1, status="merge-retry")],
                    run_id=f"rung23-{label}",
                )
                with patch.object(
                    module, "retry_deferred_integrations", side_effect=retry
                ):
                    rc, state, _ = self.drive(module, run_dir)
                self.assertTrue(
                    any(kw.get("poll") for kw in polled),
                    f"{label}: rungs 2/3 must fire once `runnable is None`",
                )
                self.assertTrue(
                    any(kw.get("ask") for kw in polled),
                    f"{label}: rung 3 passes ask=True unconditionally (the SHARED ladder resolves "
                    "the interactive predicate itself, so an unattended run cannot stop on it)",
                )
                self.assertEqual(self.statuses(state)["def111"], "executed")

    def test_the_reporter_sees_post_ladder_state_at_both_reload_points(self):
        """F-9 STATED AS THE PROPERTY IT IS ABOUT, at the ladder reloads, on both hosts.

        Each ladder rung mutates state, saves it, and RELOADS it, rebinding `state`. If the host
        omits the refresh, the published object is the pre-ladder dict and a signal arriving there
        reports the item as still deferred after it has actually integrated.

        THE ASSERTION IS OBJECT IDENTITY, and the first version of this test was VACUOUS without it,
        which is worth recording. Comparing published STATUSES passes on the broken host too,
        because a test stub mutates the very dict the loop is holding, so the pre-reload snapshot
        and the live object are the same object and agree by construction. What actually
        distinguishes a refreshed host from a stale one is whether the dict the reporter would read
        IS the dict the loop is now working with. Measured at this HEAD that probe returns True on
        oc and False on agy, so it FAILS on the defect and passes after the repair, which is the
        whole requirement for a guard.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                self.clear_published()
                identity: list[bool] = []

                def retry(rd, st, *a, **kw):
                    for entry in st["queue"]:
                        if entry["status"] == "merge-retry":
                            entry["status"] = "executed"
                    module.save_state(rd, st)
                    return []

                def fake_exec(rd, st, it, *a, **kw):
                    # `st` is the object the loop is holding RIGHT NOW, after the ladder's reload.
                    identity.append(self.published() is st)
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [
                        self.item("def111", position=1, status="merge-retry"),
                        # A second runnable item is what keeps the loop alive past rung 1, so the
                        # probe fires AFTER the ladder reload rather than at the summary.
                        self.item("aaa222", position=2),
                    ],
                    run_id=f"ladderpub-{label}",
                )
                buf = io.StringIO()
                with patch.object(
                    module, "retry_deferred_integrations", side_effect=retry
                ):
                    with patch.object(module, "execute_item", side_effect=fake_exec):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            module.run_queue(run_dir, retry_incomplete=False)

                self.assertTrue(identity, f"{label}: no turn ran after the ladder")
                self.assertTrue(
                    all(identity),
                    f"{label}: after the integration ladder reloaded state, the object the "
                    "shutdown reporter would read is NOT the object the loop is working with, so "
                    "a signal arriving here reports a PRE-reload snapshot. oc calls "
                    "register_signal_report after each reload for exactly this reason "
                    "(oc_runipd.py:8645 states the invariant); the missing calls are agy's.",
                )

    def test_the_published_snapshot_matches_the_live_statuses_after_the_ladder(self):
        """The operator-visible consequence of the identity property above.

        Kept as a SEPARATE test with a deliberately different instrument: this one lets the ladder
        write through `save_state` and then compares the reporter's view of a LATER item against
        the live one. On a stale host the reporter reports the second item as still `queued` after
        it has executed.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                self.clear_published()
                snapshots: list[dict] = []

                def retry(rd, st, *a, **kw):
                    for entry in st["queue"]:
                        if entry["status"] == "merge-retry":
                            entry["status"] = "executed"
                    module.save_state(rd, st)
                    return []

                def fake_exec(rd, st, it, *a, **kw):
                    it["status"] = "executed"
                    module.save_state(rd, st)
                    pub = self.published()
                    if isinstance(pub, dict):
                        snapshots.append({e["id6"]: e["status"] for e in pub["queue"]})

                run_dir = self.make_run(
                    [
                        self.item("def111", position=1, status="merge-retry"),
                        self.item("aaa222", position=2),
                    ],
                    run_id=f"laddersnap-{label}",
                )
                buf = io.StringIO()
                with patch.object(
                    module, "retry_deferred_integrations", side_effect=retry
                ):
                    with patch.object(module, "execute_item", side_effect=fake_exec):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            module.run_queue(run_dir, retry_incomplete=False)

                self.assertTrue(snapshots, f"{label}: no turn ran after the ladder")
                self.assertEqual(
                    snapshots[-1].get("aaa222"),
                    "executed",
                    f"{label}: the reporter reports an item as unfinished AFTER its turn "
                    "completed, because the published reference predates the ladder's reload",
                )


class AnOrchestratorSpendsNoAgentTurn(RunQueueCase):
    """The `orchestrate` short-circuit, on both hosts, as behavior rather than as an AST shape.

    `tests/test_orchestrator_retirement.py:3575` asserts agy's BRANCH exists by parsing its AST.
    This asserts the consequence: an orchestrate item reaches `dispatch_orchestrator_item` and
    never reaches `execute_item`.
    """

    def test_an_orchestrate_item_never_reaches_execute_item(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                dispatched: list[str] = []

                # The real call is positional `(repo, run_dir, state, item, ...)`, so the item is
                # the FOURTH argument. Getting this wrong silently mis-binds `state` and the
                # failure surfaces far from the cause, which is why it is spelled out.
                def dispatch(repo, rd, st, it, *a, **kw):
                    dispatched.append(str(it.get("id6")))
                    it["status"] = "executed"
                    module.save_state(rd, st)
                    return True

                run_dir = self.make_run(
                    [
                        self.item(
                            "orc111",
                            position=1,
                            action="orchestrate",
                            kind="orchestrator",
                        )
                    ],
                    run_id=f"orch-{label}",
                )
                with patch.object(
                    module, "dispatch_orchestrator_item", side_effect=dispatch
                ):
                    rc, state, _ = self.drive(module, run_dir)
                self.assertEqual(
                    dispatched,
                    ["orc111"],
                    f"{label}: the orchestrator must reach the SHARED dispatcher",
                )
                self.assertEqual(
                    self.turns,
                    [],
                    f"{label}: an orchestrator must spend NO agent turn (that is the whole point "
                    "of the branch)",
                )
                self.assertEqual(rc, 0)

    def test_the_dispatcher_receives_both_state_sets_from_its_host(self):
        """The two EQUAL constants are passed here, and they are NOT interchangeable.

        `terminal_states=TERMINAL_STATES` and `success_states=EXECUTION_SUCCESS_STATES`. A split
        that swapped them would compile and would change which children count as done, so the
        binding is pinned at the call rather than left to a source substring.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                seen: list[dict] = []

                def dispatch(repo, rd, st, it, *a, **kw):
                    seen.append(dict(kw))
                    it["status"] = "executed"
                    module.save_state(rd, st)
                    return True

                run_dir = self.make_run(
                    [
                        self.item(
                            "orc222",
                            position=1,
                            action="orchestrate",
                            kind="orchestrator",
                        )
                    ],
                    run_id=f"orchargs-{label}",
                )
                with patch.object(
                    module, "dispatch_orchestrator_item", side_effect=dispatch
                ):
                    self.drive(module, run_dir)
                self.assertTrue(seen, f"{label}: the dispatcher was never called")
                self.assertEqual(
                    set(seen[0]["terminal_states"]), set(module.TERMINAL_STATES)
                )
                self.assertEqual(
                    set(seen[0]["success_states"]), set(module.EXECUTION_SUCCESS_STATES)
                )
                self.assertNotEqual(
                    set(seen[0]["success_states"]),
                    set(seen[0]["terminal_states"]),
                    f"{label}: the two sets must not be the same object or the swap is undetectable",
                )


class TheRunSummaryNamesItsOwnDriver(RunQueueCase):
    """F-6: `driver_label` is the ONE genuine host string in this function.

    Asserted as OUTPUT rather than as a source literal, so a split that bound the wrong label
    fails here even though `inspect.getsource` of a thin caller would contain neither string.
    """

    def test_the_summary_table_is_rendered_with_this_host_s_label(self):
        expected = {"oc_runipd": "opencode", "agy_runipd": "antigravity"}
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                seen: list[str] = []
                real = module.render_run_summary_table

                def capture(*a, **kw):
                    seen.append(str(kw.get("driver_label")))
                    return real(*a, **kw)

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"label-{label}"
                )
                with patch.object(
                    module, "render_run_summary_table", side_effect=capture
                ):
                    self.drive(module, run_dir)
                self.assertEqual(
                    seen,
                    [expected[label]],
                    f"{label}: the run summary must be labelled with THIS driver's name",
                )


class TheContinuationHintNamesItsOwnHost(RunQueueCase):
    """F-7: the STYLE resolves to oc, but `render_continuation_hint` itself is host-divergent.

    So the hint is a hook input in substance. Pinned as printed OUTPUT.
    """

    def test_the_printed_hint_names_this_host(self):
        expected = {"oc_runipd": "OpenCode", "agy_runipd": "Antigravity"}
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"hint2-{label}"
                )
                _, _, out = self.drive(module, run_dir)
                self.assertIn(
                    expected[label],
                    out,
                    f"{label}: the continuation hint must name THIS host's session continuity",
                )


class ToolIdentityIsRunFatalNotItemLocal(RunQueueCase):
    """The ordering `tests/test_lane_tool_identity.py:733` pins by SOURCE OFFSET, as behavior.

    `ToolIdentityError` subclasses `DriverError`. If the item-local `except DriverError` caught it
    first, the abort would be recorded as ONE item `failed-safely` while the remaining items kept
    running under the same wrong control plane. The INTENDED observable property is: the run
    ABORTS and the later items are NOT dispatched.

    READ `ADocumentedDefectInTheToolIdentityHandler` BELOW BEFORE TRUSTING THAT SENTENCE. Measured
    at this plan's execution HEAD, the intended property DOES NOT HOLD on either host: the handler
    swallows the exception. This class therefore pins only the half that does hold (the clause is
    reached at all, and a PLAIN `DriverError` stays item-local, which is what makes the ordering
    assertion non-vacuous), and the broken half is pinned separately and named as a defect.
    """

    def test_the_dedicated_clause_is_reached_rather_than_the_item_local_one(self):
        """The half that DOES hold: the identity error is not recorded as one item `failed-safely`.

        A plain `DriverError` marks the item `failed-safely` (see the test below). If the
        item-local clause were catching `ToolIdentityError` too, the item would carry that status.
        It does not, which proves the dedicated earlier clause is the one that runs.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()

                def boom(rd, st, it, *a, **kw):
                    self.turns.append(str(it.get("id6")))
                    it["status"] = "running"
                    module.save_state(rd, st)
                    raise module.ToolIdentityError("tool-identity mismatch (synthetic)")

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"identity-{label}"
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=boom):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        with self.assertRaises(module.ToolIdentityError):
                            module.run_queue(run_dir, retry_incomplete=False)
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertNotEqual(
                    self.statuses(state)["aaa111"],
                    "failed-safely",
                    f"{label}: a ToolIdentityError recorded as `failed-safely` means the "
                    "item-local DriverError clause caught it and the run-fatal abort was "
                    "silently downgraded (af7i6p OQ-02)",
                )

    def test_a_plain_driver_error_is_item_local(self):
        """The inverse, which is what makes the test above meaningful: an ordinary DriverError must
        NOT abort the run, or the ordering assertion would be vacuous."""
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()

                def boom(rd, st, it, *a, **kw):
                    self.turns.append(str(it.get("id6")))
                    if it["id6"] == "aaa111":
                        raise module.DriverError("synthetic item-local failure")
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("aaa111", position=1), self.item("bbb222", position=2)],
                    run_id=f"driverr-{label}",
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=boom):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)
                self.assertEqual(
                    self.turns,
                    ["aaa111", "bbb222"],
                    f"{label}: an item-local DriverError must not stop the queue",
                )
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(
                    self.statuses(state)["aaa111"],
                    "failed-safely",
                    f"{label}: an item-local DriverError is recorded as failed-safely; this is "
                    "the status the ToolIdentityError test above proves is NOT used",
                )


class ToolIdentityHandlerRepairedAndRunFatal(RunQueueCase):
    """Pins the restored run-fatal behavior of ToolIdentityError on both hosts (hp9rot E-04 / BUG-02)."""

    def test_the_handler_raises_and_aborts_queue_execution(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()

                def boom(rd, st, it, *a, **kw):
                    self.turns.append(str(it.get("id6")))
                    it["status"] = "running"
                    module.save_state(rd, st)
                    raise module.ToolIdentityError("tool-identity mismatch (synthetic)")

                run_dir = self.make_run(
                    [self.item("aaa111", position=1), self.item("bbb222", position=2)],
                    run_id=f"identdefect-{label}",
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=boom):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        with self.assertRaises(module.ToolIdentityError):
                            module.run_queue(run_dir, retry_incomplete=False)
                self.assertEqual(
                    self.turns,
                    ["aaa111"],
                    f"{label}: ToolIdentityError must abort immediately; second item must not run",
                )

    def test_the_source_contains_the_raise_statement(self):
        import ast
        import inspect

        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                src = inspect.getsource(module.run_queue)
                self.assertIn("except ToolIdentityError", src)
                self.assertLess(
                    src.index("except ToolIdentityError"),
                    src.index("except DriverError"),
                )
                handler = None
                for node in ast.walk(ast.parse(src.lstrip())):
                    if (
                        isinstance(node, ast.ExceptHandler)
                        and node.type is not None
                        and "ToolIdentityError" in ast.unparse(node.type)
                    ):
                        handler = node
                        break
                assert (
                    handler is not None
                ), f"{label}: no ToolIdentityError handler found"
                self.assertTrue(
                    any(isinstance(n, ast.Raise) for n in ast.walk(handler)),
                    f"{label}: the  must be present in except ToolIdentityError",
                )


class TheBetweenItemStopCheckpointPrecedesSelection(RunQueueCase):
    """What `tests/test_runner_stop.py:607` pins by string offset, as behavior.

    The observable property: the poll happens BEFORE the next item is chosen, so a stop request
    written between two turns prevents the next dispatch rather than arriving too late.
    """

    def test_a_stop_request_between_turns_prevents_the_next_dispatch(self):
        from agent_workflows import runner_stop

        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        self.item("aaa111", position=1),
                        self.item("bbb222", position=2, setid="other"),
                    ],
                    run_id=f"stop-{label}",
                )
                # Level 2 = stop after the current set. The second item is in ANOTHER set, so the
                # wind-down must refuse to start it and leave it `queued` (spec R22: no fabricated
                # disposition).
                polls = {"n": 0}
                real_poll = runner_stop.poll_stop

                def poll(rd, *a, **kw):
                    polls["n"] += 1
                    if polls["n"] == 1:
                        return real_poll(rd, *a, **kw)
                    return 2

                with patch.object(runner_stop, "poll_stop", side_effect=poll):
                    _, state, _ = self.drive(module, run_dir)
                statuses = self.statuses(state)
                self.assertEqual(statuses["aaa111"], "executed")
                self.assertEqual(
                    statuses["bbb222"],
                    "queued",
                    f"{label}: an out-of-boundary item must be left `queued`, never relabelled",
                )
                self.assertNotIn(
                    "bbb222",
                    self.turns,
                    f"{label}: the between-item poll must precede selection, or the stop arrives "
                    "after the dispatch it was meant to prevent",
                )


class TheStreamTrackerIsWiredThroughToTheTurn(RunQueueCase):
    """What both host CLI pins assert as three source substrings, as behavior.

    `tests/test_oc_runipd_cli.py:233` and `tests/test_agy_runipd_cli.py:1569` require the literal
    `"tracker = StreamTracker()"` and the exact `execute_item(...)` call string. The property is
    that a tracker instance is CREATED by the loop and REACHES the turn, which survives a split.
    """

    def test_a_stream_tracker_instance_reaches_execute_item(self):
        from agent_workflows.render_stream import StreamTracker

        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                seen: list[object] = []

                def fake_exec(rd, st, it, *a, **kw):
                    seen.append(kw.get("tracker"))
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"tracker-{label}"
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=fake_exec):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)
                self.assertTrue(seen, f"{label}: the turn never ran")
                self.assertIsInstance(
                    seen[0],
                    StreamTracker,
                    f"{label}: the loop must create a StreamTracker and pass it to the turn",
                )

    def test_the_same_tracker_instance_is_reused_across_items(self):
        """One tracker per RUN, not per item: the summary table aggregates over the whole run."""
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                seen: list[object] = []

                def fake_exec(rd, st, it, *a, **kw):
                    seen.append(kw.get("tracker"))
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("aaa111", position=1), self.item("bbb222", position=2)],
                    run_id=f"tracker2-{label}",
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=fake_exec):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)
                self.assertEqual(len(seen), 2)
                self.assertIs(
                    seen[0], seen[1], f"{label}: one tracker per run, not per item"
                )


class TheExitCodeReflectsTheRealOutcome(RunQueueCase):
    """The loop's return value, per state, on both hosts."""

    def test_a_fully_executed_queue_exits_zero(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"rc0-{label}"
                )
                rc, _, _ = self.drive(module, run_dir)
                self.assertEqual(rc, 0)

    def test_a_queue_with_a_non_success_terminal_item_exits_nonzero(self):
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()

                def on_turn(item):
                    item["status"] = "failed-safely"

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"rc1-{label}"
                )
                rc, _, _ = self.drive(module, run_dir, on_turn=on_turn)
                self.assertNotEqual(
                    rc, 0, f"{label}: a failed item must not be reported as a clean run"
                )

    def test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES(self):
        """The two EQUAL-valued constants are NOT interchangeable, and the loop uses each for a
        different job. Worth pinning because a split that passed the wrong one would be invisible:
        both are module constants with identical values across hosts, so no host-token diff shows it.

        `SUCCESS_STATES` = {reviewed, approved, executed} decides the EXIT CODE.
        `EXECUTION_SUCCESS_STATES` = {executed, substantially-complete} is handed to the
        orchestrator dispatcher to decide whether a CHILD counts as done.

        So `substantially-complete` is an execution success for retirement purposes and still exits
        NONZERO, which is the behavior asserted here.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.assertEqual(
                    set(module.SUCCESS_STATES), {"reviewed", "approved", "executed"}
                )
                self.assertEqual(
                    set(module.EXECUTION_SUCCESS_STATES),
                    {"executed", "substantially-complete"},
                )
                self.turns.clear()

                def on_turn(item):
                    item["status"] = "substantially-complete"

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"rcsub-{label}"
                )
                rc, _, _ = self.drive(module, run_dir, on_turn=on_turn)
                self.assertNotEqual(
                    rc,
                    0,
                    f"{label}: the exit code is computed from SUCCESS_STATES, which does NOT "
                    "contain substantially-complete; a 0 here means the wrong constant was used",
                )


class AnApprovalBlockedQueueIsNotASilentSuccess(RunQueueCase):
    """`runnoop` Order 01 (`zz5yxq`) E-05: the MEASURED incident, and the control a naive fix breaks.

    THE INCIDENT (backlog `em0z50`, 2026-08-29). `aw oc run wtiso` was launched with all 8 `wtiso`
    plans at `- Status: reviewed`. It printed the run id, the state dir, and "No OpenCode session was
    captured for this run.", then EXITED 0. `aw runs <id>` showed `8 steps: 8 reviewed`,
    `action=execute`, `Attempts: 0` on every row, an empty `outcomes/`, and a single `run-created`
    event. The operator believed 8 plans were queued. The cause was that one status carried two
    contradictory meanings: `action_for('child','reviewed')` -> `'execute'` (a ROUTING decision, "run
    this") while `'reviewed' in SUCCESS_STATES` -> True (a COMPLETION decision, "this succeeded"), and
    the queue builder froze such an item as queue status `reviewed` rather than `queued`, so it was
    never dispatched AND was counted as a success.

    THE CONTROL IS THE LOAD-BEARING HALF OF THIS CLASS, not a courtesy. The tempting one-line fix is
    to remove `reviewed` from `SUCCESS_STATES`, and that is WRONG: `cascade_dependency_blocked`'s
    in-tree docstring records run `run-20260904T042705Z-1025943`, a 6-item all-`review` run of the
    `wslayout` Set that reviewed Orders 00 and 01 and then killed Orders 02-05 the instant Order 01
    reached `reviewed`, because that site hardcoded the execution bar. A review pass legitimately
    SUCCEEDS at `reviewed`. A suite covering only the execute case would pass over a re-broken
    review-mode Set run, so both cases are asserted here, on both hosts.
    """

    def test_a_reviewed_EXECUTE_item_is_not_counted_as_a_success(self):
        """The incident itself: an item the loop never dispatches must not produce exit 0."""
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()
                # `status="reviewed"` is what the REAL queue builder freezes for a `reviewed`-but-
                # unapproved plan (`runner_shared.initial_queue_status`: `reviewed` is absent from
                # `NON_TERMINAL_QUEUE_STATUSES`, so the entry is born NOT `queued`), paired with
                # `action="execute"` from `action_for`. Asserted against those two real functions
                # below, so this fixture cannot drift from what the builder actually writes.
                self.assertEqual(module.action_for("child", "reviewed"), "execute")
                self.assertEqual(
                    module.runner_shared.initial_queue_status("reviewed"), "reviewed"
                )
                run_dir = self.make_run(
                    [
                        self.item(
                            "aaa111", position=1, action="execute", status="reviewed"
                        ),
                        self.item(
                            "bbb222", position=2, action="execute", status="reviewed"
                        ),
                    ],
                    run_id=f"needsapproval-{label}",
                )
                rc, state, _ = self.drive(module, run_dir)
                self.assertEqual(
                    self.turns,
                    [],
                    f"{label}: neither item is dispatchable, so no turn may run; if one did, the "
                    "admission tuple changed and this test is measuring the wrong thing",
                )
                self.assertNotEqual(
                    rc,
                    0,
                    f"{label}: a queue of `reviewed`-but-unapproved EXECUTE items did NO WORK, so "
                    "exit 0 would report a silent success (backlog em0z50)",
                )
                self.assertEqual(
                    rc,
                    1,
                    f"{label}: zz5yxq OQ-02 resolved to 1 from this site. Spec 25kzda 5.6's exit 3 "
                    "for `needs_input` is reachable only by wiring the drivers to "
                    "`run_evidence.aggregate_run_exit`, which they do not call today.",
                )
                self.assertEqual(
                    self.statuses(state),
                    {"aaa111": "reviewed", "bbb222": "reviewed"},
                    f"{label}: no status may be REWRITTEN to produce the nonzero exit (spec R22); "
                    "the bar changed, the record did not",
                )

    def test_a_reviewed_REVIEW_item_is_still_a_success(self):
        """The control. A review pass ending `reviewed` is a COMPLETED review and must still exit 0.

        This is the case the docstring on `cascade_dependency_blocked` records as having been broken
        once by exactly the shape of fix this plan makes (run `run-20260904T042705Z-1025943`).
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                self.turns.clear()

                def on_turn(item):
                    item["status"] = "reviewed"

                run_dir = self.make_run(
                    [
                        self.item("aaa111", position=1, action="review"),
                        self.item("bbb222", position=2, action="review"),
                    ],
                    run_id=f"reviewmode-{label}",
                )
                rc, state, _ = self.drive(module, run_dir, on_turn=on_turn)
                self.assertEqual(
                    sorted(self.turns),
                    ["aaa111", "bbb222"],
                    f"{label}: both review items must actually be dispatched",
                )
                self.assertEqual(
                    rc,
                    0,
                    f"{label}: a completed REVIEW run must still exit 0. A nonzero here means the "
                    "execute-action fix was applied to the review action too, which is the "
                    "regression that made a review-mode Set run impossible to complete "
                    "(run-20260904T042705Z-1025943)",
                )
                self.assertEqual(
                    self.statuses(state), {"aaa111": "reviewed", "bbb222": "reviewed"}
                )

    def test_a_review_run_that_reached_reviewed_and_an_execute_one_get_OPPOSITE_verdicts(
        self,
    ):
        """The two halves stated as ONE assertion, so the distinction cannot be lost by editing one.

        Identical statuses, different actions, opposite verdicts. Driven through the SHARED predicate
        rather than the loop, because this is a claim about the bar itself.
        """
        for label, module in HOST_PAIRS:
            with self.subTest(host=label):
                bar = module.item_reached_success
                self.assertFalse(bar({"action": "execute", "status": "reviewed"}))
                self.assertTrue(bar({"action": "review", "status": "reviewed"}))
                # And the unambiguous cases still behave: a real execution success, and a failure.
                self.assertTrue(bar({"action": "execute", "status": "executed"}))
                self.assertFalse(bar({"action": "review", "status": "failed-safely"}))
                # THE NARROWING IS EXACTLY ONE STATUS FOR EXACTLY ONE ACTION. `substantially-complete`
                # must STILL be a non-success for reporting, on BOTH actions: the sibling test
                # `test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES` pins that as a
                # deliberate contract, and it is what rules out reusing the DEPENDENCY bar
                # (`EXECUTION_SUCCESS_STATES`, which contains it) for this question.
                self.assertFalse(
                    bar({"action": "execute", "status": "substantially-complete"})
                )
                self.assertEqual(
                    set(module.runner_shared.EXECUTE_REPORTING_SUCCESS_STATES),
                    {"executed", "approved"},
                    f"{label}: the execute reporting bar must be SUCCESS_STATES minus `reviewed` "
                    "and nothing else",
                )


if __name__ == "__main__":
    unittest.main()

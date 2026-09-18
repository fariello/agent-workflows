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
(`tests/test_rununify_run_queue_characterization.py`, E-02), a two-line repair of the ONE real
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
import unittest

from agent_workflows import agy_runipd, oc_runipd

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
STILL_DOUBLE_DEFINED = (
    "_observe_between_turn_stop",
    "_record_deliberate_stop",
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
    "reconcile_interrupted",
    "requeue_interrupted",
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
THIN_WRAPPERS_OVER_RUNNER_SHARED = (
    "driver_actor",
    "render_continuation_hint",
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
        self.assertEqual(len(STILL_DOUBLE_DEFINED), 9)
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
    separately in `tests/test_rununify_run_queue_characterization.py`. Both are wanted: the
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
# The split HAS NOT been performed. Recorded state, not an oversight.
# ==================================================================================================


class TheSplitHasNotBeenPerformed(unittest.TestCase):
    """Asserted MECHANICALLY so the omission is a guarded state a later reader must engage with.

    Read this plan's E-04 analysis before changing anything here.
    """

    def test_run_queue_is_defined_in_both_runners_and_not_in_runner_shared(self):
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertIn("run_queue", top_level_defs(host))
        self.assertNotIn(
            "run_queue",
            top_level_defs("runner_shared"),
            "runner_shared now defines run_queue, so the split HAS happened. Update this file "
            "deliberately: re-base the ten source-reading pins E-04 enumerates, move each shared "
            "symbol out of STILL_DOUBLE_DEFINED, and record what each re-based pin now asserts",
        )

    def test_the_two_definitions_are_not_the_same_object(self):
        self.assertIsNot(oc_runipd.run_queue, agy_runipd.run_queue)

    def test_neither_runner_imports_run_queue_from_the_other(self):
        """A runner-to-runner import would be the WRONG way to de-duplicate: it makes one host
        depend on the other's module rather than on the shared library, which is what
        `runner_shared`'s own no-runner-import rule exists to prevent."""
        for host in HOSTS:
            other = "agy_runipd" if host == "oc_runipd" else "oc_runipd"
            with self.subTest(host=host):
                imported = {
                    alias.asname or alias.name
                    for node in module_body(host)
                    if isinstance(node, ast.ImportFrom) and other in (node.module or "")
                    for alias in node.names
                }
                self.assertNotIn("run_queue", imported)


# ==================================================================================================
# The host-specific boundary, and the source-reading pins the split must re-base.
# ==================================================================================================


class TheHostSpecificBoundaryIsExactlyWhatWasMeasured(unittest.TestCase):
    """F-6/F-7/F-12: the three genuine host inputs, and nothing else."""

    def test_each_host_binds_its_own_driver_label(self):
        for host in HOSTS:
            with self.subTest(host=host):
                node = run_queue_node(host)
                labels = {
                    kw.value.value
                    for call in ast.walk(node)
                    if isinstance(call, ast.Call)
                    for kw in call.keywords
                    if kw.arg == "driver_label"
                    and isinstance(kw.value, ast.Constant)
                    and isinstance(kw.value.value, str)
                }
                self.assertEqual(
                    labels,
                    {DRIVER_LABELS[host]},
                    f"{host}.run_queue must label the run summary {DRIVER_LABELS[host]!r}",
                )

    def test_the_recovery_hint_names_this_host_s_own_resume_verb(self):
        expected = {
            "oc_runipd": "aw oc runipd resume",
            "agy_runipd": "aw agy runipd resume",
        }
        for host, module in MODULES.items():
            with self.subTest(host=host):
                self.assertIn(expected[host], module.DEPENDENCY_BLOCK_RECOVERY_HINT)

    def test_the_continuation_hint_renderer_is_still_host_divergent(self):
        """F-7: the STYLE of the print resolves to oc, but the RENDERER differs per host, so this
        line is a hook input in substance. Pinned so the claim stays checkable."""
        self.assertIsNot(
            oc_runipd.render_continuation_hint, agy_runipd.render_continuation_hint
        )


class TheSourceReadingPinsAreInventoried(unittest.TestCase):
    """E-04(c): the pins a split must re-base, asserted to still EXIST.

    WHY ASSERT THEIR EXISTENCE. E-04's analysis says a thin caller breaks these. That claim is only
    checkable while they are there; if one is quietly deleted, the analysis silently becomes wrong
    and the split looks cheaper than it is. So this test is the analysis's own tripwire.

    THE PINS ARE NOT ENDORSED. Each reads SOURCE TEXT, which a comment can satisfy and a
    relocation destroys. `tests/test_rununify_run_queue_characterization.py` re-expresses the
    load-bearing ones as behavior, which is the technique the maintainer's 2026-09-16 ruling
    authorizes for re-basing them.
    """

    # file -> the substring each pin requires of `run_queue`'s source.
    PINS = {
        "tests/test_runner_backlog_close.py": (
            "emit_shutdown_report()",
            "register_signal_report(",
        ),
        "tests/test_oc_runipd_cli.py": (
            "tracker = StreamTracker()",
            "render_run_summary_table(",
        ),
        "tests/test_agy_runipd_cli.py": (
            "tracker = StreamTracker()",
            "render_run_summary_table(",
        ),
        "tests/test_lane_tool_identity.py": (
            "except ToolIdentityError",
            "except DriverError",
        ),
        "tests/test_runner_stop.py": ("runner_stop.poll_stop(run_dir)",),
        "tests/test_runner_shared.py": (
            '"integration-deferred"',
            "retry_deferred_integrations",
            "deferred_integration_items",
            "runnable is None",
            "poll=True",
        ),
    }

    def test_every_substring_the_existing_pins_require_is_present_on_both_hosts(self):
        for host, module in MODULES.items():
            src = inspect.getsource(module.run_queue)
            for path, needles in self.PINS.items():
                for needle in needles:
                    with self.subTest(host=host, pin=path, needle=needle):
                        self.assertIn(
                            needle,
                            src,
                            f"{path} asserts {needle!r} appears in {host}.run_queue's SOURCE. It "
                            "does not. Either the split happened (re-base that pin) or the "
                            "substring changed (update both deliberately)",
                        )

    def test_the_ordering_pin_still_holds_on_both_hosts(self):
        """`tests/test_lane_tool_identity.py:733` requires the ToolIdentityError clause to precede
        the item-local DriverError one. Reproduced here because it is one of the two pins whose
        GUARANTEE (not just its text) must survive any relocation."""
        for host, module in MODULES.items():
            with self.subTest(host=host):
                src = inspect.getsource(module.run_queue)
                self.assertLess(
                    src.index("except ToolIdentityError"),
                    src.index("except DriverError"),
                    f"{host}: the run-fatal clause must come FIRST or the abort is downgraded to "
                    "one item failed-safely while the rest run under the wrong control plane",
                )

    def test_the_agy_orchestrate_branch_ast_shape_still_holds(self):
        """`tests/test_orchestrator_retirement.py:3575` parses agy's OWN `run_queue` AST and
        requires an `If` mentioning `orchestrate` containing a `Continue`."""
        node = run_queue_node("agy_runipd")
        branches = [
            sub
            for sub in ast.walk(node)
            if isinstance(sub, ast.If) and "orchestrate" in ast.unparse(sub.test)
        ]
        self.assertTrue(
            branches,
            "agy_runipd.run_queue has no branch reading the orchestrate action",
        )
        self.assertTrue(
            any(isinstance(n, ast.Continue) for b in branches for n in ast.walk(b)),
            "the orchestrate branch must short-circuit, or the item falls through to execute_item "
            "and spends an agent turn on a plan no agent should author against",
        )


# ==================================================================================================
# The measured shape of the divergence, so the "12 differing lines" claim stays checkable.
# ==================================================================================================


class TheMeasuredDivergenceIsSmallButTheClosureIsNot(unittest.TestCase):
    """The two numbers whose CONFLATION this plan's review caught, pinned side by side.

    Keeping them in one place is the point: 12 differing code lines is the reason the split LOOKS
    cheap, and 11 double-defined dependencies is the reason it is not. A future reader who sees only
    the first number repeats the error that made both this plan and sibling `i3d6ml` NO-GO.
    """

    def code_lines(self, host: str) -> list[str]:
        src = (AW / f"{host}.py").read_text(encoding="utf-8").splitlines()
        node = run_queue_node(host)
        body = src[node.lineno - 1 : node.end_lineno]
        return [
            ln.rstrip() for ln in body if ln.strip() and not ln.strip().startswith("#")
        ]

    def test_the_bodies_still_barely_differ(self):
        import difflib

        oc, agy = self.code_lines("oc_runipd"), self.code_lines("agy_runipd")
        diff = [
            ln
            for ln in difflib.unified_diff(oc, agy, lineterm="", n=0)
            if ln[:1] in "+-" and not ln.startswith(("+++", "---"))
        ]
        # A RANGE, not an exact figure: E-03 deliberately added two lines plus comments to agy, and
        # a future legitimate edit will move it again. What must NOT change silently is the ORDER of
        # magnitude, because the whole argument is "the bodies agree, the closure does not".
        self.assertLess(
            len(diff),
            40,
            f"the two run_queue bodies now differ by {len(diff)} code lines, far more than the 12 "
            "measured at 2026-09-17. Real DRIFT has appeared: measure it before assuming the "
            "split analysis still applies",
        )

    def test_the_closure_is_the_binding_constraint_not_the_body_difference(self):
        """Stated as an assertion so the conclusion is checkable, not just prose: there are more
        still-forked dependencies than there are host-token lines."""
        host_token_lines = 0
        for host in HOSTS:
            for line in self.code_lines(host):
                if "opencode" in line or "antigravity" in line:
                    host_token_lines += 1
        self.assertGreater(
            len(STILL_DOUBLE_DEFINED),
            host_token_lines,
            "if the host-token line count ever exceeds the fork count, the shape of this problem "
            "has changed and the split analysis must be re-derived",
        )


if __name__ == "__main__":
    unittest.main()

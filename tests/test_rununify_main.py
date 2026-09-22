#!/usr/bin/env python3
"""rununify Order 11 (`3dki3o`) E-05/E-06: GUARD what plan `3dki3o` measured about `main`.

TWO DIFFERENT ACTORS ARE GUARDED AGAINST HERE, which is why the file has two halves.

E-05 GUARDS AGAINST THE CODE DRIFTING. `main` closes over 31 module-level names (27 when this file was
written; every change since is annotated and dated in :data:`EXPECTED_CLOSURE`), and the plan's
decision about whether it can be split at all rests on HOW MANY of them are still defined twice.
:class:`TheClosureClassification` re-derives that classification from the AST at import time and
asserts it against :data:`EXPECTED_CLOSURE`, a NAMED TABLE. A symbol that silently changes class
fails here, which is the point: the split's cost is a function of this table, so the table moving
without anybody noticing is how a stale plan gets executed.

E-06 GUARDS AGAINST A LATER AGENT CLEARING THE OBSTACLES. This is a different threat from drift. The
four source pins inventoried in :data:`SOURCE_PINS` are what a split of `main` would break, LOUDLY,
and the cheapest way to make a split "pass" is to delete them. :class:`TheSourcePinsAreStillPresent`
asserts each is still there, and :class:`TheSplitHasNotBeenPerformed` asserts `main` is still defined
in both runners. So a unilateral relocation cannot land quietly; it has to come back through this
file and say what it did.

WHAT THIS FILE DELIBERATELY DOES NOT ASSERT. It contains no assertion about a shared `main` core in
`runner_shared`. Per E-05, a test asserting a state the code is not in is a failing test rather than
a guard. When the split lands, the classes below are the place to re-base, and the maintainer's
2026-09-16 ruling governs how: re-base a guard deliberately and record what it now asserts; never
weaken one silently.

THE ONE MEASUREMENT THAT MOVED SINCE THE PLAN WAS WRITTEN, recorded here because it is load-bearing
rather than cosmetic. The plan's Goal table lists `EmptyStatusSelection` as STILL DEFINED TWICE and
its F-7 calls a shared-core `except` arm on it a BLOCKER, having proven by construction that
hardcoding one host's class returns 2 where spec `25kzda` 2.4a property 3 requires 0. Sibling
`i3d6ml` (commit `d26c1061`) has since lifted the class into `runner_shared`, so both hosts now
resolve the SAME object and that blocker is structurally gone. The class count therefore reads
9/2/5/8/3 at this HEAD where the plan measured 8/2/5/9/3. The behavioral half of the contract is
pinned in `TheEmptySweepExitCodeContract`, below in THIS file, which also
fails if the class is ever re-forked.
"""

from __future__ import annotations

import ast
import contextlib
import functools
import inspect
import io
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests.support import REPO_ROOT

HOSTS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))

ERROR_PREFIX = {"oc_runipd": "runipd:", "agy_runipd": "runagy:"}

# ==========================================================================================
# THE NAMED TABLE. Every closure assertion below is driven from here, so there is exactly one
# place to update when a symbol legitimately changes class, and updating it is a visible edit.
# ==========================================================================================

#: The five closure classes, in the order plan `3dki3o`'s Goal table states them, with what each
#: means for a split. The CONSEQUENCE column is the reason the classification is worth guarding:
#: classes 1 and 3 are free, class 2 needs the ruled wrapper form, and classes 4 and 5 are the cost.
CLOSURE_CLASSES = {
    "shared-same-object": "resolves in runner_shared and is the SAME object: moves for free",
    "shared-host-wrapper": "name in runner_shared but the host object DIFFERS (a per-host "
    "wrapper): must be injected, or the host label is lost",
    "one-object-agy-imports-oc": "already ONE object, agy imports it from oc: needs RELOCATION to "
    "runner_shared, not de-duplication",
    "still-defined-twice": "STILL DEFINED TWICE: each is an injected parameter, and injecting it "
    "is the opposite of sharing it",
    "oc-only": "no agy counterpart exists: host hook, permanently",
}

#: The 31 module-level free names of `oc_runipd.main`, each mapped to its class (27 when this table was
#: first written; see the dated per-row notes below for each addition and why it was not a re-fork).
#:
#: MEASURED AT HEAD `761edad3`, 2026-09-17, by the same AST method the assertions below use, and it
#: is re-derived rather than trusted: :meth:`TheClosureClassification.test_every_name_is_in_the_table`
#: fails if the code's closure and this table disagree in EITHER direction.
#:
#: `EmptyStatusSelection` is classed `shared-same-object` here and was `still-defined-twice` in the
#: plan. That is the one class change, and it is a REAL improvement rather than a correction: sibling
#: `i3d6ml` lifted the class, which dissolved plan `3dki3o`'s F-7 blocker. See the module docstring.
EXPECTED_CLOSURE = {
    # class 1: resolves in runner_shared, same object (9)
    "DriverError": "shared-same-object",
    "EmptyStatusSelection": "shared-same-object",
    "Palette": "shared-same-object",
    "json": "shared-same-object",
    "load_state": "shared-same-object",
    "render_run_summary_table": "shared-same-object",
    "resolve_run_dir": "shared-same-object",
    "should_color": "shared-same-object",
    "sys": "shared-same-object",
    # class 2: shared NAME, per-host wrapper object (2)
    "print_status": "shared-host-wrapper",
    "save_state": "shared-host-wrapper",
    # class 3: one object, agy imports it from oc (6)
    "emit_shutdown_report": "one-object-agy-imports-oc",
    "install_exit_signal_handler": "one-object-agy-imports-oc",
    "render_runs_pointer": "one-object-agy-imports-oc",
    "report_run_spec_edits": "one-object-agy-imports-oc",
    "runner_shared": "one-object-agy-imports-oc",
    # ADDED 2026-09-21 by stopdisc-01 (`wqq8ua`): `main`'s interrupt/SIGTERM handler now prints the
    # graceful-stop hint, so `main` REFERENCES the `runner_stop` module it previously did not. NOTHING
    # WAS FORKED OR MOVED, and that distinction is the whole reason this row is a legitimate update
    # rather than the drift this table exists to catch: `runner_stop` was ALREADY bound on both hosts
    # before this change (verified at the pre-change HEAD), and both hosts already resolved the SAME
    # module object. What grew is the set of names `main` closes over, not the number of definitions.
    "runner_stop": "one-object-agy-imports-oc",
    # class 4: STILL DEFINED TWICE, i.e. the injection cost of a split (9)
    "build_parser": "still-defined-twice",
    # ADDED 2026-09-21 by stopdisc-01 (`wqq8ua`): `main` now calls `_detect_driver_command()` to render
    # the graceful-stop hint in this host's own command vocabulary (`aw oc run` / `aw agy run`), so the
    # name entered `main`'s closure. IT IS NOT A NEW FORK: both hosts have carried their own one-line
    # `_detect_driver_command` since rununify 04 (`tx6q0h`) lifted the host labels, and the two were
    # ALREADY distinct objects at the pre-change HEAD (verified). It is classed `still-defined-twice`
    # for the same reason `print_status` is a wrapper: each host binds its OWN `HostLabels`
    # (`OC_HOST_LABELS` vs `AGY_HOST_LABELS`), which is exactly the per-host datum that must not be
    # lost, and the DECISION it wraps is the single shared `runner_shared.detect_driver_command`.
    "_detect_driver_command": "still-defined-twice",
    # ADDED 2026-09-17 by integpath-04 (`rl67b0`): the `integrate` verb's per-host handler, the exact
    # twin of `handle_stop_command` beside it and forked for the same reason. Each host binds its OWN
    # `integrate_lane_branch` wrapper (so the merge subject on MAIN names the right driver) and its own
    # `run_suite_check`, which `runner_shared` may not import; the DECISION is the single shared
    # `runner_shared.reintegrate_lane`, so the fork is the wiring and not the logic.
    "handle_integrate_command": "still-defined-twice",
    # ADDED 2026-09-20 by reverify-01 (`mp289j`): the `audit` verb's per-host handler. ITS FORK IS
    # ASYMMETRIC AND THAT IS THE DESIGN rather than a cost to pay down later: the OpenCode half
    # launches the turn (it must bind THIS host's `run_opencode` and `resolve_launch_pair`, which
    # `runner_shared` may not import), and the Antigravity half is a REFUSAL naming the oc spelling,
    # because wiring a second launch path is out of that plan's fence. The two decisions that are not
    # host-specific are shared: `runner_shared.plan_audit_target` (which plan is auditable, and what it
    # can be diffed against) and `runner_shared.build_verifier_prompt(..., audit=True)` (the prompt).
    "handle_audit_command": "still-defined-twice",
    # RECLASSIFIED 2026-09-22 by hostdedup Order 01 (`li44r9`) E-04/E-07: `handle_stop_command`,
    # `install_stop_triggers` and `locked_run` were BYTE-IDENTICAL in both drivers and now have ONE
    # definition each in `runner_shared`, with each host keeping a one-line wrapper. So all three move
    # from `still-defined-twice` to `shared-host-wrapper`, exactly as `render_continuation_hint` and
    # `write_report` did under `tx6q0h`, and the fork count falls by the same three: the histogram below
    # still partitions the same population, which is what makes this a reclassification and not a
    # deletion.
    #
    # THE FIRST TWO KEEP A WRAPPER RATHER THAN BECOMING ONE OBJECT because each binds its OWN
    # `HostLabels`: both bodies previously called the host's `_detect_driver_command`, and the
    # operator-facing driver command they record must name the host that actually ran. `locked_run` keeps
    # one for the ordinary reason a wrapper exists here (the name stays resolvable in the module every
    # source-inspection pin looks at).
    "handle_stop_command": "shared-host-wrapper",
    "initialize_run": "still-defined-twice",
    "install_stop_triggers": "shared-host-wrapper",
    "locked_run": "shared-host-wrapper",
    # RECLASSIFIED 2026-09-17 by sibling `tx6q0h`: lifted behind the `HostLabels` descriptor, so
    # each host now keeps a one-line wrapper over the single `runner_shared` definition.
    "render_continuation_hint": "shared-host-wrapper",
    "run_queue": "still-defined-twice",
    "write_report": "shared-host-wrapper",  # same reclassification as above (`tx6q0h`)
    # class 5: oc-only, no agy counterpart (3)
    "ProfileClauseError": "oc-only",
    "extract_profile_clause": "oc-only",
    "print_launch_identity": "oc-only",
}

#: The class histogram the table above implies. Asserted separately from the per-name mapping so a
#: failure says WHICH WAY the cost moved, not merely that something changed.
EXPECTED_CLASS_COUNTS = {
    "shared-same-object": 9,
    # RE-MEASURED 2026-09-17: 4, up from 2. `render_continuation_hint` and `write_report` moved from
    # `still-defined-twice` when sibling `tx6q0h` lifted them behind the `HostLabels` descriptor; the
    # fork count falls by the same two, so the histogram still partitions the same population.
    # RE-MEASURED 2026-09-22 by hostdedup Order 01 (`li44r9`): 7, up from 4. `handle_stop_command`,
    # `install_stop_triggers` and `locked_run` moved here from `still-defined-twice` when that plan
    # lifted them into `runner_shared`; the fork count below falls by the same three, so the histogram
    # still partitions the same population. A RISE IN THIS CLASS CANNOT BE A RE-FORK by construction:
    # the class MEANS "one shared definition behind a per-host wrapper", and the per-name assertions in
    # this file prove each wrapper really delegates.
    "shared-host-wrapper": 7,
    # RE-MEASURED 2026-09-21: 6, up from 5. stopdisc-01 (`wqq8ua`) made `main` reference the
    # `runner_stop` module when printing the graceful-stop hint on the interrupt path. A rise in THIS
    # class is not a re-fork by construction: the class MEANS "already one object", so a name can only
    # enter it by being a single shared object both hosts see, which `runner_stop` already was.
    "one-object-agy-imports-oc": 6,
    # RE-MEASURED 2026-09-17: 7, up from 6. integpath-04 (`rl67b0`) added `handle_integrate_command`
    # per host. A RISE is normally a re-fork and therefore a defect, so the reason is stated: this is a
    # NEW verb whose per-host half binds host-specific values only (the `integrate_lane_branch` wrapper
    # carrying the merge subject's label, and `run_suite_check`, which `runner_shared` may not import),
    # while the decision lives once in `runner_shared.reintegrate_lane`. Nothing previously shared was
    # forked.
    # RE-MEASURED 2026-09-20: 8, up from 7. reverify-01 (`mp289j`) added `handle_audit_command` per
    # host, for the same shape of reason and with the same test applied: nothing PREVIOUSLY SHARED was
    # forked. Both of the new verb's host-neutral decisions were placed in `runner_shared` from the
    # start (`plan_audit_target`, and the `audit` mode of the ONE `build_verifier_prompt`), so what is
    # duplicated is the host binding alone, and on one host that binding is a refusal.
    # RE-MEASURED 2026-09-21: 9, up from 8. stopdisc-01 (`wqq8ua`) made `main` call
    # `_detect_driver_command()` so the graceful-stop hint names THIS host's command. NOTHING WAS
    # FORKED: that wrapper has existed on both hosts since `tx6q0h` lifted the host labels, and the two
    # were ALREADY distinct objects at the pre-change HEAD (verified before the edit). The rise measures
    # what `main` now REFERENCES, not a new duplicate, which is the distinction that makes this a
    # legitimate table update rather than the drift this table exists to catch.
    # RE-MEASURED 2026-09-22 by hostdedup Order 01 (`li44r9`): 6, DOWN from 9, which is the direction
    # this number is supposed to move. The three that left are named in the `shared-host-wrapper` note
    # above. A FALL is only legitimate when the names went somewhere and are still asserted there, which
    # is why the count of the receiving class rose by exactly three in the same change.
    "still-defined-twice": 6,
    "oc-only": 3,
}

#: The four test files whose `mock.patch.object(<host>, "<name>")` seams patch a name `main`
#: resolves at MODULE level, with the count measured at this HEAD. A shared core in `runner_shared`
#: resolves its OWN globals, so it would observe none of them.
#:
#: THIS IS THE OBSTACLE WHOSE FAILURE MODE IS SILENT, which is why it is counted rather than merely
#: described: a broken source pin fails at its assertion, but a LOST patch seam makes the test
#: exercise the REAL `run_queue`, `locked_run` and `initialize_run` against a temp repo, where it may
#: still pass while asserting nothing it claims to.
PATCH_SEAM_FILES = {
    # RE-MEASURED 2026-09-21: 18, up from 12. stopdisc-01 (`wqq8ua`) added
    # `MainInterruptNamesTheGracefulStopVerbTests`, whose `_stderr_for` helper drives the REAL `main`
    # to its `KeyboardInterrupt` handler through the same SIX seams the sibling
    # `RunnerMainOutputOnInterruptTests` already used (`run_queue`, `emit_shutdown_report`,
    # `resolve_run_dir`, `load_state`, `locked_run`, `install_stop_triggers`).
    #
    # A RISE HERE IS NOT AUTOMATICALLY GOOD OR BAD, which is why it is annotated rather than bumped:
    # what this counter protects is that each seam still TAKES EFFECT, since a seam that silently stops
    # applying leaves its test green while exercising the real `run_queue`. These six are declared once
    # in a helper rather than repeated per test, so they are six seams serving four tests.
    "tests/test_interrupt_menu.py": 18,
    "tests/test_run_summary_table.py": 8,
    "tests/test_oc_runipd.py": 4,
    "tests/test_oc_runipd_cli.py": 2,
}

#: Total seams across those four files. 26 when plan `3dki3o` F-9 first reported it; 32 since
#: stopdisc-01 (`wqq8ua`) added the six-seam interrupt-message harness annotated above.
EXPECTED_SEAM_TOTAL = 32


# ==========================================================================================
# The measurement, re-derived. Shared by both halves of the file.
# ==========================================================================================


def module_level_free_names(mod, funcname: str) -> set[str]:
    """Every name `funcname` reads that resolves in `mod`'s module globals.

    Deliberately AST-based rather than `__code__.co_names`: `co_names` also reports attribute names
    and cannot distinguish a genuine global read from a local rebind, which would inflate the
    closure and make the table below unfalsifiable.
    """
    fn = next(
        node
        for node in ast.parse(inspect.getsource(mod)).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == funcname
    )
    bound = {a.arg for a in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs}
    if fn.args.vararg:
        bound.add(fn.args.vararg.arg)
    if fn.args.kwarg:
        bound.add(fn.args.kwarg.arg)
    loaded: list[str] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                bound.add(node.id)
            else:
                loaded.append(node.id)
        elif (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node is not fn
        ):
            bound.add(node.name)
        elif isinstance(node, ast.alias):
            bound.add((node.asname or node.name).split(".")[0])
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
    globals_ = vars(mod)
    return {n for n in loaded if n not in bound and n in globals_}


def classify(name: str) -> str:
    """Put one closure name in exactly one of :data:`CLOSURE_CLASSES`.

    The order of the checks IS the definition, so it is written to match the Goal table's order:
    identity with `runner_shared` first (the free case), then a shared name whose object differs
    (the wrapper case), then absence from agy (the oc-only case), then identity across the two hosts
    (the relocate case), leaving genuine double definition last.
    """
    host_obj = getattr(oc_runipd, name)
    in_shared = hasattr(runner_shared, name)
    if in_shared and getattr(runner_shared, name) is host_obj:
        return "shared-same-object"
    if in_shared:
        return "shared-host-wrapper"
    if not hasattr(agy_runipd, name):
        return "oc-only"
    if getattr(agy_runipd, name) is host_obj:
        return "one-object-agy-imports-oc"
    return "still-defined-twice"


def measured_closure() -> dict[str, str]:
    return {n: classify(n) for n in module_level_free_names(oc_runipd, "main")}


# ==========================================================================================
# E-05: the code must not drift out from under the plan's measurement
# ==========================================================================================


class TheClosureClassification(unittest.TestCase):
    """`main`'s closure, re-derived at import and asserted against :data:`EXPECTED_CLOSURE`."""

    def test_every_name_is_in_the_table_and_the_table_has_no_extras(self):
        """Bidirectional, so neither a NEW closure name nor a stale table entry can hide."""
        measured = measured_closure()
        self.assertEqual(
            sorted(measured),
            sorted(EXPECTED_CLOSURE),
            "main's closure and EXPECTED_CLOSURE disagree; update the table DELIBERATELY and say "
            "in the commit which symbol moved and why",
        )

    def test_the_closure_size_matches_the_table(self):
        """The measured closure and the table must agree on SIZE as well as on membership.

        THE NUMBER IS NO LONGER IN THE TEST NAME, deliberately. It read `..._is_still_28_names` and went
        stale twice in four days (27 -> 28 when `rl67b0` added `handle_integrate_command`, 28 -> 29 when
        `mp289j` added `handle_audit_command`), leaving a method whose name asserted one number while its
        body asserted another. The table is the single place the count lives; this asserts the code has
        not drifted from it.
        """

        self.assertEqual(len(measured_closure()), len(EXPECTED_CLOSURE))
        # 29 -> 31 on 2026-09-21 (stopdisc-01, `wqq8ua`): `main`'s interrupt handler now prints the
        # graceful-stop hint, which references `runner_stop` and calls `_detect_driver_command()`. Both
        # names already existed on BOTH hosts; the closure grew by what `main` references, not by any
        # new definition. See the two annotated rows in `EXPECTED_CLOSURE`.
        self.assertEqual(len(EXPECTED_CLOSURE), 31)

    def test_each_name_is_still_in_its_expected_class(self):
        for name, expected in sorted(EXPECTED_CLOSURE.items()):
            with self.subTest(name=name):
                self.assertEqual(
                    classify(name),
                    expected,
                    f"{name} changed closure class; a split's cost is a function of this "
                    f"classification, so the plan that reads it is now stale",
                )

    def test_the_class_histogram_is_unchanged(self):
        measured = measured_closure()
        counts = {cls: 0 for cls in CLOSURE_CLASSES}
        for cls in measured.values():
            counts[cls] += 1
        self.assertEqual(counts, EXPECTED_CLASS_COUNTS)

    def test_every_class_named_in_the_table_is_a_declared_class(self):
        """Guards the table against a typo silently creating a sixth class nobody asserts."""
        for name, cls in EXPECTED_CLOSURE.items():
            with self.subTest(name=name):
                self.assertIn(cls, CLOSURE_CLASSES)

    def test_the_still_double_defined_count_is_stated_not_implied(self):
        """The number that decides the split's injection cost, asserted on its own.

        SEVEN, down from the nine plan `3dki3o` measured. A DROP here is progress and is recorded with
        the sibling that caused it; a RISE means something was re-forked UNLESS the rise is a genuinely
        new per-host verb, which is stated when it happens.

          * 9 -> 8: `EmptyStatusSelection` moved to `runner_shared` (sibling `i3d6ml`).
          * 8 -> 6: `render_continuation_hint` and `write_report` became one-line per-host wrappers
            over single `runner_shared` definitions when sibling `tx6q0h` lifted the eight host-label
            symbols behind its `HostLabels` descriptor (integrated 2026-09-17). They are now classed
            `shared-host-wrapper`, so the histogram above partitions the same population.
          * 6 -> 7: integpath-04 (`rl67b0`) added `handle_integrate_command`, the `integrate` verb's
            per-host handler and the exact twin of `handle_stop_command`. NOT a re-fork: nothing that
            was shared became forked. The per-host half binds only host-specific values (this host's
            `integrate_lane_branch` wrapper, which carries the merge subject's `aw oc run`/`aw agy run`
            label onto MAIN, and this host's `run_suite_check`, which `runner_shared` is forbidden by
            test from importing), and the decision itself is the one shared
            `runner_shared.reintegrate_lane`.
          * 7 -> 8: reverify-01 (`mp289j`) added `handle_audit_command`, the `audit` verb's per-host
            handler. NOT a re-fork, by the same test: nothing that was shared became forked, and BOTH of
            the new verb's host-neutral decisions were placed in `runner_shared` from the start
            (`plan_audit_target`, and the `audit` MODE of the one `build_verifier_prompt` rather than a
            second composer). What is duplicated is the host binding, and on the Antigravity host that
            binding is a refusal naming the OpenCode spelling.
          * 8 -> 9: stopdisc-01 (`wqq8ua`) made `main` call `_detect_driver_command()` so the new
            graceful-stop hint names THIS host's command vocabulary. NOT a re-fork, and this case is
            weaker still than the two above: those ADDED a per-host handler, whereas this added NO
            definition at all. The wrapper has existed on both hosts since `tx6q0h`, and the two were
            already distinct objects before the change (verified at the pre-change HEAD); only `main`'s
            reference to it is new. A rise driven purely by a new REFERENCE is the one kind this
            counter cannot distinguish from a fork on its own, which is why it is annotated rather
            than merely incremented.
        """
        measured = measured_closure()
        twice = sorted(n for n, c in measured.items() if c == "still-defined-twice")
        self.assertEqual(
            len(twice), EXPECTED_CLASS_COUNTS["still-defined-twice"], twice
        )
        self.assertNotIn(
            "EmptyStatusSelection",
            twice,
            "EmptyStatusSelection was re-forked into two per-host classes; that revives plan "
            "3dki3o's F-7 hazard, where a shared `except` arm returns 2 instead of 0",
        )

    def test_agys_own_closure_is_smaller_and_that_is_the_capability_gap(self):
        """agy reads 26 module-level names against oc's 29; the 3 missing are oc's profile grammar.

        Pinned because it is the measurement that answers "how much of `main` is even shareable":
        the difference is a CAPABILITY agy has no subsystem for, not drift to reconcile.

        RE-MEASURED 2026-09-17 (24/27 -> 25/28): integpath-04 (`rl67b0`) added
        `handle_integrate_command` to BOTH hosts, so both counts rose by one and the GAP - which is what
        this test is actually about - is unchanged at exactly oc's three profile-grammar symbols.

        RE-MEASURED 2026-09-20 (25/28 -> 26/29): reverify-01 (`mp289j`) added `handle_audit_command` to
        BOTH hosts, so both counts rose by one again and THE GAP IS STILL EXACTLY THE THREE
        PROFILE-GRAMMAR SYMBOLS. That the verb is IMPLEMENTED on oc only does not widen the gap, which
        is worth stating because one might expect it to: the agy half is a real, declared handler that
        refuses, so the NAME exists on both hosts and only its body differs.
        """
        agy_names = module_level_free_names(agy_runipd, "main")
        oc_names = module_level_free_names(oc_runipd, "main")
        # RE-MEASURED 2026-09-21 (26/29 -> 28/31): stopdisc-01 (`wqq8ua`) made BOTH hosts' `main` print
        # the graceful-stop hint on the interrupt path, so both closures gained the same two names
        # (`runner_stop` and `_detect_driver_command`) and THE GAP IS STILL EXACTLY THE THREE
        # PROFILE-GRAMMAR SYMBOLS. That symmetry is the point of re-measuring it here: a change that
        # widened the gap would mean one host got a surface the other did not, which is the divergence
        # this file guards, and an operator-facing surface added to one driver only is precisely the
        # defect the repository's shared-runner work exists to prevent.
        self.assertEqual(len(agy_names), 28)
        self.assertEqual(len(oc_names), 31)
        self.assertEqual(
            sorted(oc_names - agy_names),
            ["ProfileClauseError", "extract_profile_clause", "print_launch_identity"],
        )


class MainCase(unittest.TestCase):
    """Drive a host's real `main` in-process and capture what an operator would see."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    # ---- fixtures ------------------------------------------------------------------------
    PLAN = """# IPD: characterization probe

- Date: 2026-09-17
- Kind: child
- Status: {status}
- Set: mainchar
- Order: 01
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-17 reviewed (test): APPROVE; no blocking findings.
"""

    def make_repo(
        self, *, id6: str = "mch001", status: str = "approved"
    ) -> pathlib.Path:
        """A minimal git repo with one plan, enough for `initialize_run` to resolve a selector.

        The directory name carries a counter because every test here builds one repo PER HOST, and a
        shared name would collide on the second `subTest` rather than isolating the two hosts.
        """
        self._repo_seq = getattr(self, "_repo_seq", 0) + 1
        repo = self.root / f"repo-{self._repo_seq:02d}-{id6}-{status}"
        repo.mkdir(parents=True)
        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=repo, check=True)
        (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        (pending / f"20260917-mainchar-01-{id6}-probe.ipd.md").write_text(
            self.PLAN.format(id6=id6, status=status), encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo

    def call_main(self, mod, argv: list[str]) -> tuple[int, str, str]:
        """Return `(rc, stdout, stderr)` from a real in-process `main`."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = mod.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def prepared_run(
        self, mod, repo: pathlib.Path, id6: str = "mch001"
    ) -> pathlib.Path:
        """`start --prepare-only`, which creates the run dir and returns 0 without launching."""
        rc, out, err = self.call_main(
            mod, ["start", id6, "--repo", str(repo), "--prepare-only"]
        )
        self.assertEqual(rc, 0, f"prepare failed: {err or out}")
        runs = repo / ".aw" / "records" / "runs"
        dirs = sorted(p for p in runs.iterdir() if p.is_dir())
        self.assertEqual(len(dirs), 1, dirs)
        return dirs[0]


class TheFiveExitCodes(MainCase):
    """`main` owns the process exit status, so each code it can return is pinned on BOTH hosts.

    Spec `25kzda` 5.6 records that "the drivers themselves return only `0`/`2`/`130`/`143` today",
    citing `oc_runipd.main`. The fifth distinct RETURN is also 0, from `parser.print_help()` when no
    subcommand resolves; it is pinned separately because it is a different branch reaching the same
    code, and a split that lost it would turn a bare invocation into a crash.
    """

    def test_exit_0_a_prepare_only_start_completes(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                rc, out, err = self.call_main(
                    mod, ["start", "mch001", "--repo", str(repo), "--prepare-only"]
                )
                self.assertEqual(rc, 0, err)
                self.assertIn("Run ID:", out)
                self.assertIn("State directory:", out)

    def test_exit_0_no_subcommand_prints_help_rather_than_failing(self):
        """`main` returns 0 after `print_help()`; it must not raise and must not exit 2.

        REACHED THROUGH A NAMESPACE WHOSE `command` IS UNSET, which is the only way in: the shim
        rewrites a bare selector to `start`, so no command line reaches this branch on the shipped
        parser. It is pinned anyway because `main` still contains the branch, a caller constructing
        its own namespace can reach it, and the alternative to returning 0 here is an
        `AttributeError` on `args.command` further down.
        """
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                parser = mod.build_parser()
                ns = parser.parse_args(["status", "run-x", "--repo", str(self.root)])
                ns.command = None
                with patch.object(
                    mod, "build_parser", return_value=parser
                ), patch.object(parser, "parse_args", return_value=ns):
                    rc, out, err = self.call_main(mod, ["status", "run-x"])
                self.assertEqual(rc, 0, err)
                self.assertIn("usage", out.lower())

    def test_exit_2_an_unresolvable_selector_is_translated_not_raised(self):
        """A `DriverError` becomes the host-prefixed stderr line plus exit 2, never a traceback."""
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                rc, out, err = self.call_main(
                    mod, ["start", "nosuch", "--repo", str(repo), "--prepare-only"]
                )
                self.assertEqual(rc, 2, out)
                self.assertTrue(
                    err.startswith(ERROR_PREFIX[name]),
                    f"{name}: expected the {ERROR_PREFIX[name]!r} prefix, got {err!r}",
                )

    def test_exit_130_sigint_funnels_through_keyboardinterrupt(self):
        """CPython raises `KeyboardInterrupt` for SIGINT; `main` must translate it to 130."""
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                with patch.object(
                    mod, "run_queue", side_effect=KeyboardInterrupt("Ctrl-C")
                ), patch.object(mod, "install_stop_triggers"):
                    rc, out, err = self.call_main(
                        mod, ["resume", run_dir.name, "--repo", str(repo)]
                    )
                self.assertEqual(rc, 130, err)
                self.assertIn("Interrupted", err)
                self.assertIn("durable run state was preserved", err)

    def test_exit_143_sigterm_is_marked_by_the_message_not_a_second_handler(self):
        """The SIGTERM handler raises `KeyboardInterrupt("...SIGTERM...")`; the MESSAGE selects 143.

        This is the mechanism, and it is easy to break by accident: both signals arrive at the SAME
        `except KeyboardInterrupt` arm, and the only thing distinguishing them is `"SIGTERM" in
        str(exc)`. A split that reconstructed the exception, or normalized its message, would return
        130 for a SIGTERM and the operator would misread a clean termination as an interrupt.
        """
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                with patch.object(
                    mod,
                    "run_queue",
                    side_effect=KeyboardInterrupt("Terminated by SIGTERM"),
                ), patch.object(mod, "install_stop_triggers"):
                    rc, out, err = self.call_main(
                        mod, ["resume", run_dir.name, "--repo", str(repo)]
                    )
                self.assertEqual(rc, 143, err)
                self.assertIn("Terminated by SIGTERM", err)

    def test_the_just_terminate_message_replaces_the_preserved_state_sentence(self):
        """The `just-terminate-no-cleanup` escape prints a DIFFERENT sentence, still exiting 130."""
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                with patch.object(
                    mod,
                    "run_queue",
                    side_effect=KeyboardInterrupt("just-terminate-no-cleanup"),
                ), patch.object(mod, "install_stop_triggers"):
                    rc, _out, err = self.call_main(
                        mod, ["resume", run_dir.name, "--repo", str(repo)]
                    )
                self.assertEqual(rc, 130, err)
                self.assertIn("Terminated without clean up", err)
                self.assertNotIn("durable run state was preserved", err)


class TheImplicitStartShim(MainCase):
    """A first token that is not a subcommand gets `start` prepended; the exceptions are pinned.

    The shim's set is required to stay an INLINE LITERAL in each host's own source: two tests in
    `tests/test_runner_stop_triggers.py` regex `subcommands = \\{(.*?)\\}` out of BOTH files and
    require the sets to be identical, and each runner carries a KEEP-THIS-INLINE comment recording
    that hoisting it to a module constant makes the guard silently unmatchable. This class pins the
    BEHAVIOR that guard protects, so the property survives even if the guard's form changes.
    """

    def test_a_bare_selector_is_treated_as_start(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                rc, out, err = self.call_main(
                    mod, ["mch001", "--repo", str(repo), "--prepare-only"]
                )
                self.assertEqual(rc, 0, err)
                self.assertIn("Run ID:", out)

    def test_a_bare_stop_is_NOT_rewritten_into_start_stop(self):
        """THE CASE THE SHIM'S SET EXISTS FOR, asserted as behavior on both hosts.

        If `stop` were missing from the set, this invocation would become
        `start stop <run-id>`, i.e. it would LAUNCH a run whose selector is the literal `stop`. So
        the discriminator is not the exit code but the absence of any run: a rewritten `stop` builds
        a run directory, and a correctly routed one never does.
        """
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                rc, out, err = self.call_main(
                    mod,
                    [
                        "stop",
                        "run-20260917T000000Z-0001",
                        "--repo",
                        str(repo),
                        "--now",
                    ],
                )
                self.assertNotEqual(
                    rc, 0, "a stop naming no live run must not report success"
                )
                self.assertFalse(
                    (repo / ".aw" / "records" / "runs").exists(),
                    f"{name}: `stop` was rewritten to `start stop`, which launched a run",
                )
                self.assertNotIn("Run ID:", out)

    def test_each_real_subcommand_routes_without_a_rewrite(self):
        """`status`/`report`/`resume`/`stop`/`start` are all in the set on both hosts."""
        for name, mod in HOSTS:
            for verb in ("start", "resume", "status", "report", "stop"):
                with self.subTest(driver=name, verb=verb):
                    parser = mod.build_parser()
                    # A parse that RESOLVES the verb proves the verb is a real subcommand, which is
                    # the precondition for the shim leaving it alone.
                    self.assertIn(verb, parser.format_help())


class TheFourExceptArmsInOrder(MainCase):
    """The `except` ladder is `KeyboardInterrupt`, `EmptyStatusSelection`, `DriverError`, `Exception`.

    ORDER IS LOAD-BEARING, not stylistic. `EmptyStatusSelection` is a SUBCLASS of `DriverError`, so
    if the generic arm came first the empty-review sweep would exit 2 instead of 0 and violate spec
    `25kzda` 2.4a property 3. Each arm is proven reachable BY BEHAVIOR here rather than by reading
    the source, so the property survives a relocation of the body.
    """

    def test_the_generic_exception_arm_reraises_after_reporting(self):
        """An unexpected error must print the host-prefixed line AND re-raise, never return 0.

        Swallowing it would be the worst outcome: a crashed run reported as a clean exit.
        """
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                out, err = io.StringIO(), io.StringIO()
                with patch.object(
                    mod, "run_queue", side_effect=ZeroDivisionError("boom")
                ), patch.object(mod, "install_stop_triggers"):
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(
                        err
                    ):
                        with self.assertRaises(ZeroDivisionError):
                            mod.main(["resume", run_dir.name, "--repo", str(repo)])
                self.assertIn(
                    f"{ERROR_PREFIX[name]} unexpected failure:", err.getvalue()
                )

    def test_a_driver_error_from_the_queue_returns_2_and_is_not_reraised(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                with patch.object(
                    mod,
                    "run_queue",
                    side_effect=runner_shared.DriverError("queue said no"),
                ), patch.object(mod, "install_stop_triggers"):
                    rc, _out, err = self.call_main(
                        mod, ["resume", run_dir.name, "--repo", str(repo)]
                    )
                self.assertEqual(rc, 2)
                self.assertIn("queue said no", err)

    def test_the_empty_status_arm_precedes_the_driver_error_arm(self):
        """Proven BY BEHAVIOR: raise `EmptyStatusSelection` and require 0, not 2.

        Because the class is a `DriverError` subclass, getting 0 here is only possible if its arm is
        ordered FIRST. That makes this a behavioral test of an ordering property, which is what the
        maintainer's 2026-09-16 ruling asks for where a source pin would otherwise be used.
        """
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                with patch.object(
                    mod,
                    "run_queue",
                    side_effect=runner_shared.EmptyStatusSelection("empty"),
                ), patch.object(mod, "install_stop_triggers"):
                    rc, out, err = self.call_main(
                        mod, ["resume", run_dir.name, "--repo", str(repo)]
                    )
                self.assertEqual(
                    rc,
                    0,
                    f"{name}: EmptyStatusSelection fell through to the DriverError arm "
                    f"(stderr={err!r})",
                )
                self.assertIn("Nothing awaiting review", out)


class TheJsonStatusBranch(MainCase):
    """`status --json` must emit parseable JSON and SUPPRESS the human pointer sentence.

    One existing pin (`tests/test_runner_backlog_close.py:923`) asserts this by walking the AST of
    `main`'s source for an `if` whose body contains `json.dumps` and not `render_runs_pointer`. This
    asserts the same contract as OUTPUT, which is both stronger (a comment cannot satisfy it) and
    survives the body moving.
    """

    def test_json_status_is_parseable_and_carries_no_pointer_line(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                rc, out, err = self.call_main(
                    mod, ["status", run_dir.name, "--repo", str(repo), "--json"]
                )
                self.assertEqual(rc, 0, err)
                parsed = json.loads(out)  # fails loudly if a human line leaked in
                self.assertIn("queue", parsed)
                self.assertNotIn("Run `aw runs", out)

    def test_plain_status_DOES_carry_the_pointer_line(self):
        """The inverse half: without `--json` the pointer is expected, so the suppression above is
        a real branch rather than a line nobody prints."""
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                rc, out, err = self.call_main(
                    mod, ["status", run_dir.name, "--repo", str(repo)]
                )
                self.assertEqual(rc, 0, err)
                self.assertIn("Run `aw runs", out)


class TheReportBranch(MainCase):
    """`report` writes the file and prints its path, on both hosts."""

    def test_report_writes_the_execution_report_and_prints_the_path(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                rc, out, err = self.call_main(
                    mod, ["report", run_dir.name, "--repo", str(repo)]
                )
                self.assertEqual(rc, 0, err)
                report = run_dir / "execution-report.md"
                self.assertTrue(report.is_file(), f"{name}: no report written")
                self.assertIn(str(report), out)


class TheResumeFreezeContract(MainCase):
    """Resume REFUSES a frozen flag and APPLIES a passed policy flag, on both hosts.

    A source pin (`tests/test_run_flag_surface.py:837`) requires `main`'s source to mention
    `refuse_frozen_flags_on_resume` and `apply_run_policy_flags_on_resume`. These two tests assert
    what those calls DO, so the contract is pinned to behavior as well as to text.
    """

    def test_retry_budget_is_refused_on_resume(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                rc, _out, err = self.call_main(
                    mod,
                    [
                        "resume",
                        run_dir.name,
                        "--repo",
                        str(repo),
                        "--retry-budget",
                        "9",
                    ],
                )
                self.assertEqual(rc, 2, "a frozen flag must be refused, not applied")
                self.assertIn("retry-budget", err.replace("_", "-"))

    def test_a_passed_policy_flag_is_applied_to_the_frozen_state(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                before = runner_shared.load_state(run_dir)["options"].get("unattended")
                with patch.object(mod, "run_queue", return_value=0), patch.object(
                    mod, "install_stop_triggers"
                ):
                    rc, _out, err = self.call_main(
                        mod,
                        ["resume", run_dir.name, "--repo", str(repo), "--unattended"],
                    )
                self.assertEqual(rc, 0, err)
                after = runner_shared.load_state(run_dir)["options"].get("unattended")
                self.assertTrue(
                    after, f"{name}: --unattended was not applied on resume"
                )
                self.assertNotEqual(before, after)


class OcOnlyProfileGrammar(MainCase):
    """The `as <profile>` clause is OC-ONLY, and its absence on agy is pinned as a fact.

    This is the measurement that decides how much of `main` can be shared at all: 19 of the 46
    differing AST-normalized lines are this grammar, and agy has NO profile subsystem to support it.
    Pinning it here means a later split cannot quietly grow the clause onto agy (a FEATURE the
    parent Set forbids a child from adding) or quietly drop it from oc.
    """

    def test_oc_refuses_a_profile_named_on_a_non_start_command(self):
        repo = self.make_repo(id6="mch001")
        run_dir = self.prepared_run(oc_runipd, repo)
        parser = oc_runipd.build_parser()
        ns = parser.parse_args(["resume", run_dir.name, "--repo", str(repo)])
        setattr(ns, "profile", "gem")
        with patch.object(oc_runipd, "build_parser", return_value=parser), patch.object(
            parser, "parse_args", return_value=ns
        ):
            rc, _out, err = self.call_main(
                oc_runipd, ["resume", run_dir.name, "--repo", str(repo)]
            )
        self.assertEqual(rc, 2)
        self.assertIn("cannot be named on", err)
        self.assertIn("frozen when the run is created", err)

    def test_agy_has_no_profile_clause_extractor_at_all(self):
        """Not a style difference: the whole subsystem is absent, so there is nothing to unify."""
        self.assertTrue(hasattr(oc_runipd, "extract_profile_clause"))
        self.assertFalse(hasattr(agy_runipd, "extract_profile_clause"))
        self.assertTrue(hasattr(oc_runipd, "ProfileClauseError"))
        self.assertFalse(hasattr(agy_runipd, "ProfileClauseError"))

    def test_oc_refuses_verify_with_on_resume_and_agy_never_offered_it(self):
        repo = self.make_repo(id6="mch001")
        run_dir = self.prepared_run(oc_runipd, repo)
        rc, _out, err = self.call_main(
            oc_runipd,
            ["resume", run_dir.name, "--repo", str(repo), "--verify-with", "opus"],
        )
        self.assertEqual(rc, 2)
        self.assertIn("cannot be changed on resume", err)
        self.assertNotIn("--verify-with", agy_runipd.build_parser().format_help())


class AgyOnlyResumeFlag(MainCase):
    """`--agy-executable` is agy's own resume-time state write, with no oc counterpart."""

    def test_agy_executable_is_written_to_the_frozen_options_on_resume(self):
        repo = self.make_repo(id6="mch001")
        run_dir = self.prepared_run(agy_runipd, repo)
        with patch.object(agy_runipd, "run_queue", return_value=0), patch.object(
            agy_runipd, "install_stop_triggers"
        ):
            rc, _out, err = self.call_main(
                agy_runipd,
                [
                    "resume",
                    run_dir.name,
                    "--repo",
                    str(repo),
                    "--agy-executable",
                    "/usr/bin/true",
                ],
            )
        self.assertEqual(rc, 0, err)
        state = runner_shared.load_state(run_dir)
        self.assertEqual(state["options"]["agy_executable"], "/usr/bin/true")
        self.assertNotIn("--agy-executable", oc_runipd.build_parser().format_help())


class OcOnlyLaunchIdentity(MainCase):
    """`print_launch_identity` runs on oc's `--prepare-only` and `status`; agy has no such symbol."""

    def test_oc_prints_the_launch_identity_and_agy_has_none_to_print(self):
        self.assertTrue(hasattr(oc_runipd, "print_launch_identity"))
        self.assertFalse(hasattr(agy_runipd, "print_launch_identity"))
        repo = self.make_repo(id6="mch001")
        with patch.object(oc_runipd, "print_launch_identity") as spy:
            rc, _out, err = self.call_main(
                oc_runipd, ["start", "mch001", "--repo", str(repo), "--prepare-only"]
            )
        self.assertEqual(rc, 0, err)
        self.assertEqual(
            spy.call_count,
            1,
            "oc's --prepare-only must report what it will launch with",
        )


# ==========================================================================================
# E-03: THE EXIT-CODE CONTRACT PLAN `3dki3o` F-7 SHOWS IS SILENTLY BREAKABLE
# ==========================================================================================


class TheEmptySweepExitCodeContract(unittest.TestCase):
    """E-03: an empty review sweep exits 0, and the class that makes that possible is ONE object.

    THE HAZARD, as plan `3dki3o` F-7 proved by construction at review time: if the two hosts define
    SEPARATE `EmptyStatusSelection` classes (siblings under the shared `DriverError`, neither a
    subclass of the other), then a SHARED core writing `except EmptyStatusSelection` resolves ONE of
    them, and the other host's instance falls through to `except DriverError` and returns 2 where
    spec `25kzda` 2.4a property 3 requires 0. Its failure mode is what makes it worth a test of its
    own: nothing crashes, the run simply reports failure on a healthy repository.

    WHAT CHANGED SINCE THE PLAN WAS WRITTEN, and it is the good news: sibling `i3d6ml` (commit
    `d26c1061`) lifted `EmptyStatusSelection` into `runner_shared`, so at this HEAD both hosts
    resolve the SAME class and the hazard is structurally gone. The plan's own Goal table lists the
    symbol as "STILL DEFINED TWICE"; that is now stale, which
    `tests/test_rununify_main.py` records as a class change.

    So this class pins BOTH halves: the behavior (0, the plain sentence, no run directory) and the
    structural precondition (one class, shared, a `DriverError` subclass). A future re-fork into two
    per-host classes fails HERE, loudly, instead of turning exit 0 into exit 2 in production.
    """

    PLAN_TO_REVIEW = """# IPD: nothing to review

- Date: 2026-09-17
- Kind: child
- Status: executed
- Set: emptysweep
- Order: 01
- Highest E allocated: 01
- Author: test
- Id: esw001

## Workflow history
- 2026-09-17 executed (test): done.
"""

    def make_repo_with_nothing_to_review(self, root: pathlib.Path) -> pathlib.Path:
        repo = root / "repo"
        repo.mkdir(parents=True)
        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=repo, check=True)
        (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
        executed = repo / ".aw" / "records" / "plans" / "executed"
        executed.mkdir(parents=True)
        (executed / "20260917-emptysweep-01-esw001-done.ipd.md").write_text(
            self.PLAN_TO_REVIEW, encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo

    def test_an_empty_review_sweep_exits_zero_on_both_hosts(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo_with_nothing_to_review(pathlib.Path(td))
                    out, err = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(
                        err
                    ):
                        rc = mod.main(
                            [
                                "start",
                                "reviews",
                                "--repo",
                                str(repo),
                                "--prepare-only",
                            ]
                        )
                    self.assertEqual(
                        rc,
                        0,
                        f"{name}: an empty review sweep is the HEALTHY state and must exit 0 "
                        f"(spec 25kzda 2.4a property 3); stderr={err.getvalue()!r}",
                    )
                    self.assertIn("Nothing awaiting review", out.getvalue())
                    self.assertFalse(
                        (repo / ".aw" / "records" / "runs").exists(),
                        f"{name}: an empty sweep must create no run directory",
                    )

    def test_empty_status_selection_is_ONE_shared_class_not_two_per_host(self):
        """THE STRUCTURAL HALF, which no other test in the repository asserts.

        If this fails because the classes were re-forked, the empty-sweep behavior above is one
        careless `except` away from returning 2 in a shared core. See F-7.
        """
        self.assertIs(
            oc_runipd.EmptyStatusSelection,
            agy_runipd.EmptyStatusSelection,
            "the two hosts' EmptyStatusSelection must be the SAME object; two sibling classes "
            "let a shared `except` arm miss one host and return 2 instead of 0 (F-7)",
        )
        self.assertIs(
            oc_runipd.EmptyStatusSelection,
            runner_shared.EmptyStatusSelection,
            "the shared class must be the one `runner_shared` owns, so a shared core's `except` "
            "arm resolves the same object both hosts raise",
        )

    def test_the_shared_class_is_still_a_driver_error_subclass(self):
        """The subclass relation is WHY the arm ordering matters; losing it changes the ladder."""
        self.assertTrue(
            issubclass(runner_shared.EmptyStatusSelection, runner_shared.DriverError)
        )
        self.assertIsNot(runner_shared.EmptyStatusSelection, runner_shared.DriverError)

    def test_a_plain_driver_error_still_exits_2_so_the_zero_is_not_blanket(self):
        """NON-VACUITY of the contract above: only the EMPTY sweep gets 0, not every failure."""
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo_with_nothing_to_review(pathlib.Path(td))
                    out, err = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(
                        err
                    ):
                        rc = mod.main(
                            ["start", "zzzzzz", "--repo", str(repo), "--prepare-only"]
                        )
                    self.assertEqual(rc, 2, out.getvalue())
                    self.assertNotIn("Nothing awaiting review", out.getvalue())


class ThePatchSeamPopulation(unittest.TestCase):
    """The patch seams plan `3dki3o` F-9 measured (26 then, 32 now), asserted so their loss cannot be
    silent. :data:`PATCH_SEAM_FILES` is the authority for the per-file counts and carries a dated note
    for every change.

    WHY COUNT THEM AT ALL, when a split has not happened: because this is the obstacle that does NOT
    announce itself. A source pin fails at its assertion. A seam that stops taking effect leaves the
    test GREEN while it silently exercises the real `run_queue`, `locked_run` and `initialize_run`.
    Counting them here converts "we think 26 tests still mean what they say" into an assertion.
    """

    @classmethod
    @functools.lru_cache(maxsize=1)
    def _cached_seams(cls) -> list[tuple[str, int, str]]:
        closure = module_level_free_names(oc_runipd, "main") | module_level_free_names(
            agy_runipd, "main"
        )
        direct = {"oc_runipd", "agy_runipd"}
        indirect = {"driver", "module", "mod", "runner", "host", "_MODULES"}
        found: list[tuple[str, int, str]] = []
        for path in sorted(pathlib.Path(REPO_ROOT, "tests").glob("*.py")):
            text = path.read_text(encoding="utf-8")
            if "patch.object" not in text and "setattr" not in text:
                continue
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or len(node.args) < 2:
                    continue
                func = ast.unparse(node.func)
                if not func.endswith(("patch.object", "setattr")):
                    continue
                target = ast.unparse(node.args[0])
                base = target.split(".")[-1].split("[")[0]
                if base not in direct and base not in indirect:
                    continue
                try:
                    symbol = ast.literal_eval(node.args[1])
                except (ValueError, SyntaxError):
                    continue
                if not isinstance(symbol, str) or symbol not in closure:
                    continue
                found.append((f"tests/{path.name}", node.lineno, symbol))
        return found

    def seams(self) -> list[tuple[str, int, str]]:
        """Every `patch.object`/`setattr` on a host module naming a `main`-closure symbol.

        Both spellings of the target are counted: the DIRECT `patch.object(oc_runipd, ...)` and the
        INDIRECT `patch.object(module, ...)` used inside a both-hosts loop. Counting only the direct
        form undercounts by 18 of 28, which is how a scan can report a reassuring number and be
        wrong.
        """
        return self._cached_seams()

    def test_the_four_named_files_still_hold_their_measured_seam_counts(self):
        counts: dict[str, int] = {}
        for rel, _line, _symbol in self.seams():
            counts[rel] = counts.get(rel, 0) + 1
        for rel, expected in sorted(PATCH_SEAM_FILES.items()):
            with self.subTest(path=rel):
                self.assertEqual(
                    counts.get(rel, 0),
                    expected,
                    f"{rel}'s patch-seam count moved; a seam that no longer takes effect leaves "
                    f"its test green while exercising real code (F-9)",
                )

    def test_the_total_across_those_files_matches_the_table(self):
        """THE NUMBER IS NOT IN THE TEST NAME, for the reason its sibling
        `test_the_closure_size_matches_the_table` records: a hardcoded count in a method name goes
        stale and leaves a test asserting one number while its name claims another. This method read
        `..._is_still_26` and its message said "expected 26" while `EXPECTED_SEAM_TOTAL` was the real
        authority; renamed by stopdisc-01 (`wqq8ua`) when the total legitimately moved to 32."""
        total = sum(
            1 for rel, _line, _symbol in self.seams() if rel in PATCH_SEAM_FILES
        )
        self.assertEqual(
            total,
            EXPECTED_SEAM_TOTAL,
            f"expected {EXPECTED_SEAM_TOTAL}, measured {total}",
        )

    def test_every_seam_still_names_a_symbol_main_actually_reads(self):
        """Non-vacuity of the count: a seam on an unrelated name would inflate it harmlessly."""
        closure = module_level_free_names(oc_runipd, "main") | module_level_free_names(
            agy_runipd, "main"
        )
        for rel, line, symbol in self.seams():
            with self.subTest(site=f"{rel}:{line}"):
                self.assertIn(symbol, closure)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

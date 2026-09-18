#!/usr/bin/env python3
"""rununify Order 11 (`3dki3o`) E-05/E-06: GUARD what plan `3dki3o` measured about `main`.

TWO DIFFERENT ACTORS ARE GUARDED AGAINST HERE, which is why the file has two halves.

E-05 GUARDS AGAINST THE CODE DRIFTING. `main` closes over 27 module-level names, and the plan's
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
pinned in `tests/test_rununify_main_characterization.py::TheEmptySweepExitCodeContract`, which also
fails if the class is ever re-forked.
"""

from __future__ import annotations

import ast
import functools
import inspect
import pathlib
import unittest

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests.support import REPO_ROOT

HOSTS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))

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

#: The 27 module-level free names of `oc_runipd.main`, each mapped to its class.
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
    # class 3: one object, agy imports it from oc (5)
    "emit_shutdown_report": "one-object-agy-imports-oc",
    "install_exit_signal_handler": "one-object-agy-imports-oc",
    "render_runs_pointer": "one-object-agy-imports-oc",
    "report_run_spec_edits": "one-object-agy-imports-oc",
    "runner_shared": "one-object-agy-imports-oc",
    # class 4: STILL DEFINED TWICE, i.e. the injection cost of a split (8)
    "build_parser": "still-defined-twice",
    # ADDED 2026-09-17 by integpath-04 (`rl67b0`): the `integrate` verb's per-host handler, the exact
    # twin of `handle_stop_command` beside it and forked for the same reason. Each host binds its OWN
    # `integrate_lane_branch` wrapper (so the merge subject on MAIN names the right driver) and its own
    # `run_suite_check`, which `runner_shared` may not import; the DECISION is the single shared
    # `runner_shared.reintegrate_lane`, so the fork is the wiring and not the logic.
    "handle_integrate_command": "still-defined-twice",
    "handle_stop_command": "still-defined-twice",
    "initialize_run": "still-defined-twice",
    "install_stop_triggers": "still-defined-twice",
    "locked_run": "still-defined-twice",
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
    "shared-host-wrapper": 4,
    "one-object-agy-imports-oc": 5,
    # RE-MEASURED 2026-09-17: 7, up from 6. integpath-04 (`rl67b0`) added `handle_integrate_command`
    # per host. A RISE is normally a re-fork and therefore a defect, so the reason is stated: this is a
    # NEW verb whose per-host half binds host-specific values only (the `integrate_lane_branch` wrapper
    # carrying the merge subject's label, and `run_suite_check`, which `runner_shared` may not import),
    # while the decision lives once in `runner_shared.reintegrate_lane`. Nothing previously shared was
    # forked.
    "still-defined-twice": 7,
    "oc-only": 3,
}

#: THE FOUR SOURCE PINS that read `inspect.getsource(<host>.main)`, each with the substring or AST
#: shape it requires. A thin caller delegating to a shared core satisfies NONE of them, which is
#: precisely why they are inventoried: a split must re-base each one deliberately.
#:
#: The `line` is recorded for a human's benefit and is NOT asserted (line numbers move for unrelated
#: reasons, and a guard that fails on an unrelated edit above it teaches people to edit the guard).
#: What IS asserted is that the file still contains the pin and its required text.
SOURCE_PINS = (
    {
        "path": "tests/test_runner_backlog_close.py",
        "line": 923,
        "test": "test_json_output_suppresses_the_pointer",
        "requires": ("json.dumps", "render_runs_pointer"),
        "shape": "walks the AST of main's source for the `--json` branch and asserts that branch "
        "contains `json.dumps` and does NOT contain `render_runs_pointer`",
        "behavioral_twin": "tests/test_rununify_main_characterization.py::TheJsonStatusBranch",
    },
    {
        "path": "tests/test_runner_backlog_close.py",
        "line": 1073,
        "test": "test_the_sigterm_funnel_is_wired_in_both_drivers_main",
        "requires": ("install_exit_signal_handler()", "143"),
        "shape": "asserts main's source contains the literal `install_exit_signal_handler()` and "
        "the literal `143`",
        "behavioral_twin": "tests/test_rununify_main_characterization.py::TheFiveExitCodes"
        "::test_exit_143_sigterm_is_marked_by_the_message_not_a_second_handler",
    },
    {
        "path": "tests/test_runner_backlog_close.py",
        "line": 1089,
        "test": "test_both_drivers_report_from_their_keyboardinterrupt_funnel",
        "requires": ("KeyboardInterrupt", "emit_shutdown_report"),
        "shape": "requires an `except` handler naming `KeyboardInterrupt` whose body contains "
        "`emit_shutdown_report`",
        "behavioral_twin": "tests/test_rununify_main_characterization.py::TheFiveExitCodes"
        "::test_exit_130_sigint_funnels_through_keyboardinterrupt",
    },
    {
        "path": "tests/test_run_flag_surface.py",
        "line": 837,
        "test": "test_both_runners_refuse_and_apply_on_resume",
        "requires": (
            "refuse_frozen_flags_on_resume",
            "apply_run_policy_flags_on_resume",
        ),
        "shape": "asserts main's source contains both helper names, on BOTH hosts",
        "behavioral_twin": "tests/test_rununify_main_characterization.py"
        "::TheResumeFreezeContract",
    },
)

#: The four test files whose `mock.patch.object(<host>, "<name>")` seams patch a name `main`
#: resolves at MODULE level, with the count measured at this HEAD. A shared core in `runner_shared`
#: resolves its OWN globals, so it would observe none of them.
#:
#: THIS IS THE OBSTACLE WHOSE FAILURE MODE IS SILENT, which is why it is counted rather than merely
#: described: a broken source pin fails at its assertion, but a LOST patch seam makes the test
#: exercise the REAL `run_queue`, `locked_run` and `initialize_run` against a temp repo, where it may
#: still pass while asserting nothing it claims to.
PATCH_SEAM_FILES = {
    "tests/test_interrupt_menu.py": 12,
    "tests/test_run_summary_table.py": 8,
    "tests/test_oc_runipd.py": 4,
    "tests/test_oc_runipd_cli.py": 2,
}

#: Total seams across those four files, i.e. the number plan `3dki3o` F-9 reported.
EXPECTED_SEAM_TOTAL = 26


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

    def test_the_closure_is_still_28_names(self):
        # 28, up from 27: integpath-04 (`rl67b0`) added `handle_integrate_command`, the `integrate`
        # verb's per-host handler, to `main`'s closure. The table above records its class and why.
        self.assertEqual(len(measured_closure()), 28)
        self.assertEqual(len(EXPECTED_CLOSURE), 28)

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
        """
        measured = measured_closure()
        twice = sorted(n for n, c in measured.items() if c == "still-defined-twice")
        self.assertEqual(len(twice), 7, twice)
        self.assertNotIn(
            "EmptyStatusSelection",
            twice,
            "EmptyStatusSelection was re-forked into two per-host classes; that revives plan "
            "3dki3o's F-7 hazard, where a shared `except` arm returns 2 instead of 0",
        )

    def test_agys_own_closure_is_smaller_and_that_is_the_capability_gap(self):
        """agy reads 25 module-level names against oc's 28; the 3 missing are oc's profile grammar.

        Pinned because it is the measurement that answers "how much of `main` is even shareable":
        the difference is a CAPABILITY agy has no subsystem for, not drift to reconcile.

        RE-MEASURED 2026-09-17 (24/27 -> 25/28): integpath-04 (`rl67b0`) added
        `handle_integrate_command` to BOTH hosts, so both counts rose by one and the GAP - which is what
        this test is actually about - is unchanged at exactly oc's three profile-grammar symbols.
        """
        agy_names = module_level_free_names(agy_runipd, "main")
        oc_names = module_level_free_names(oc_runipd, "main")
        self.assertEqual(len(agy_names), 25)
        self.assertEqual(len(oc_names), 28)
        self.assertEqual(
            sorted(oc_names - agy_names),
            ["ProfileClauseError", "extract_profile_clause", "print_launch_identity"],
        )


class TheMeasuredDivergence(unittest.TestCase):
    """The line-level numbers plan `3dki3o` F-1 rests on, re-derived so a claim cannot go stale.

    These are ASSERTED rather than merely recorded because F-1's conclusion (that `main` is the most
    CAPABILITY-divergent of the five, not the least) is what re-scoped the plan. If the two bodies
    converge or diverge materially, the conclusion needs re-examining, and this is where that
    surfaces.
    """

    def normalized(self, mod, name: str) -> list[str]:
        fn = next(
            node
            for node in ast.parse(inspect.getsource(mod)).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == name
        )
        return [line for line in ast.unparse(fn).splitlines() if line.strip()]

    def test_the_two_bodies_are_still_the_measured_sizes(self):
        # RE-MEASURED 2026-09-17 by integpath-04 (`rl67b0`), which added the `integrate` dispatch arm
        # (plus its comment) to BOTH bodies: raw 297 -> 309 on oc and 205 -> 215 on agy, normalized
        # 133 -> 135 and 111 -> 113. Both bodies grew by the SAME two normalized lines, which is why
        # F-1's conclusion is untouched: the divergence did not move, both hosts gained the same verb.
        self.assertEqual(len(inspect.getsourcelines(oc_runipd.main)[0]), 309)
        self.assertEqual(len(inspect.getsourcelines(agy_runipd.main)[0]), 215)
        self.assertEqual(len(self.normalized(oc_runipd, "main")), 135)
        self.assertEqual(len(self.normalized(agy_runipd, "main")), 113)

    def test_the_similarity_is_still_about_0_81(self):
        import difflib

        ratio = difflib.SequenceMatcher(
            None,
            self.normalized(oc_runipd, "main"),
            self.normalized(agy_runipd, "main"),
        ).ratio()
        # 0.8145 after integpath-04 (`rl67b0`), from 0.8115: both bodies gained the same two lines, so
        # the similarity moved slightly UP. F-1's conclusion (that `main` is the most
        # capability-divergent of the five) is unaffected by a change in this direction.
        self.assertAlmostEqual(ratio, 0.8145, places=3)


# ==========================================================================================
# E-06: a later agent must not clear the obstacles to make a split pass
# ==========================================================================================


class TheSourcePinsAreStillPresent(unittest.TestCase):
    """THE FIRST INVERSE ASSERTION. Deleting a pin is the cheapest way to fake a clean split.

    The maintainer's 2026-09-16 ruling is the standard these enforce: a source-reading guard is
    something to RE-BASE deliberately (move it onto the shared implementation, record what it now
    asserts, prove it still catches the regression it was installed for), and WEAKENING one silently
    stays forbidden. Deletion is the extreme form of weakening, so it fails here.

    Each pin's behavioral twin is named in :data:`SOURCE_PINS`. Where a behavioral assertion can
    replace a source-text one without losing coverage the ruling says to prefer it, and the twins
    are what make that trade available rather than hypothetical.
    """

    def read(self, rel: str) -> str:
        path = pathlib.Path(REPO_ROOT) / rel
        self.assertTrue(
            path.is_file(), f"{rel} is gone; a pinned guard cannot be deleted"
        )
        return path.read_text(encoding="utf-8")

    def test_each_pin_file_still_reads_mains_source(self):
        for pin in SOURCE_PINS:
            with self.subTest(pin=pin["test"]):
                text = self.read(pin["path"])
                self.assertIn(
                    "inspect.getsource",
                    text,
                    f"{pin['path']} no longer inspects any source; pin {pin['test']} is gone",
                )
                self.assertRegex(
                    text,
                    r"inspect\.getsource\([^)]*\.main\)",
                    f"{pin['path']} no longer reads `main`'s source; pin {pin['test']} was "
                    f"removed rather than re-based",
                )

    def test_each_pin_test_still_exists_by_name(self):
        for pin in SOURCE_PINS:
            with self.subTest(pin=pin["test"]):
                self.assertIn(
                    f"def {pin['test']}",
                    self.read(pin["path"]),
                    f"{pin['test']} was deleted from {pin['path']}",
                )

    def test_each_pin_still_requires_its_substrings(self):
        for pin in SOURCE_PINS:
            text = self.read(pin["path"])
            for needle in pin["requires"]:
                with self.subTest(pin=pin["test"], requires=needle):
                    self.assertIn(
                        needle,
                        text,
                        f"{pin['test']} no longer requires {needle!r}; that is a WEAKENING, "
                        f"which the 2026-09-16 ruling forbids doing silently",
                    )

    #: This plan's own two files are excluded from the pin census, and the reason is not
    #: convenience. Neither contains a pin: this file merely QUOTES the pattern (in the census regex
    #: and in :data:`SOURCE_PINS`' prose) and the characterization file only names it in a docstring
    #: explaining why it adds none. Counting a guard's description of a pin as a pin would make the
    #: census self-referential, so it would rise every time the documentation improved.
    CENSUS_EXCLUDES = frozenset(
        {"test_rununify_main.py", "test_rununify_main_characterization.py"}
    )

    def test_the_pin_population_is_still_exactly_four(self):
        """A pin ADDED is as interesting as one removed: E-02 was forbidden from adding a fifth.

        The count is over real `inspect.getsource(<mod>.main)` CALLS, found by regex over the whole
        test tree, so a pin moved to a new file is still counted and a mention in prose is not.
        """
        import re

        found: list[str] = []
        for path in sorted(pathlib.Path(REPO_ROOT, "tests").glob("*.py")):
            if path.name in self.CENSUS_EXCLUDES:
                continue
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"inspect\.getsource\([^)]*\.main\)", text):
                line = text[: match.start()].count("\n") + 1
                found.append(f"{path.name}:{line}")
        self.assertEqual(
            len(found),
            4,
            f"the `getsource(main)` pin population changed: {found}. Four is the measured "
            f"baseline; a FIFTH hands the next refactor another obstacle, and FEWER means one "
            f"was deleted instead of re-based.",
        )


class TheSplitHasNotBeenPerformed(unittest.TestCase):
    """THE SECOND INVERSE ASSERTION. `main` is still per-host, and that is the current state.

    THE REASON IT IS STILL PER-HOST IS AUTHORITY, NOT DIFFICULTY, and the distinction matters for
    whoever re-bases this class. Plan `3dki3o`'s OQ-03 is `resolved`: the maintainer ruled on
    2026-09-16 that the Set's objective is 100% de-duplication, so the split IS wanted. What this
    plan was approved with, after its 2026-09-16 review, is a scope that changes NO product code:
    E-01 measures, E-02/E-03 pin behavior, E-04 writes the analysis, E-05/E-06 guard. Performing the
    relocation would exceed that scope and would move a symbol whose eight still-double-defined
    dependencies (see :data:`EXPECTED_CLOSURE`) are owned by sibling plans.

    SO THIS CLASS IS A CHECKPOINT, NOT A VETO. When the split lands, re-base these assertions onto
    the shared implementation in the same change, and say so. What must not happen is the split
    landing while this file still claims it did not.
    """

    def test_both_runners_still_define_main_themselves(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                self.assertEqual(
                    mod.main.__module__,
                    f"agent_workflows.{name}",
                    f"{name}.main is no longer defined in {name}; if the split landed, re-base "
                    f"this guard in the same change (OQ-03, maintainer ruling 2026-09-16)",
                )

    def test_the_two_mains_are_not_the_same_object(self):
        self.assertIsNot(
            oc_runipd.main,
            agy_runipd.main,
            "the two `main`s collapsed into one object; that is the split, and it must arrive "
            "with this file re-based rather than silently",
        )

    def test_runner_shared_does_not_define_main(self):
        self.assertFalse(
            hasattr(runner_shared, "main"),
            "runner_shared grew a `main`; the shared core arrived without re-basing this guard",
        )

    def test_neither_host_delegates_to_its_peer(self):
        """`runner_shared` is the only legal home for shared logic; host-to-host is forbidden.

        `tests/test_runner_shared.py` owns the AST-based no-runner-import rule for `runner_shared`
        itself. This is the narrower `main`-specific half: agy legitimately imports FIVE of main's
        closure names from oc today, so the general no-import claim is false here and must not be
        cited; what is asserted is only that neither `main` IS the other's.
        """
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                peer = agy_runipd if mod is oc_runipd else oc_runipd
                self.assertIsNot(mod.main, peer.main)


class ThePatchSeamPopulation(unittest.TestCase):
    """The 26 seams plan `3dki3o` F-9 measured, asserted so their loss cannot be silent.

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

    def test_the_total_across_those_files_is_still_26(self):
        total = sum(
            1 for rel, _line, _symbol in self.seams() if rel in PATCH_SEAM_FILES
        )
        self.assertEqual(total, EXPECTED_SEAM_TOTAL, f"expected 26, measured {total}")

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

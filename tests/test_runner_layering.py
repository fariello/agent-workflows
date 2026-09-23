#!/usr/bin/env python3
"""THE oc-to-agy IMPORT LAYER: its classification, and the guard that freezes it.

`runnerlayer` Order 01 (`9kmbr0`). Backlog `cnwy8g`.

WHY THIS FILE EXISTS. `agy_runipd` imports names FROM `agent_workflows.oc_runipd`, so one HOST
DRIVER is a library for the other and the two are not peers. The set is also ACCRETING: the
backlog item measured 40 on 2026-09-03, the plan was authored at 47 on 2026-09-08, its review
measured 48 on 2026-09-09, and this execution measured 56 on 2026-09-22. Nothing in the suite
noticed any of that, because the one adjacent guard asks "do both runners hold the SAME OBJECT
for these named symbols?" (`tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests`)
and an imported symbol trivially passes that question. A 57th name would have been found by the
next audit, not by a test. This module ends that: the set is FROZEN below, and the freeze is
derived from a per-name CLASSIFICATION so a new name cannot be waved through without a verdict.

WHAT THIS MODULE DOES NOT DO. It MOVES NOTHING. `9kmbr0` is deliberately a classify-and-freeze
plan; the re-homing is `runnerlayer` Order 02 (`1f7xno`). So a name appearing here says only
"agy imports this from oc today, and here is what we judged it to be".

--------------------------------------------------------------------------------------------
THE CRITERION (E-01), stated ONCE, before any verdict, so the verdicts can be re-derived
--------------------------------------------------------------------------------------------

A name is OPENCODE-SPECIFIC if and only if its BODY references an opencode-only concept,
meaning the `opencode` binary, its CLI flags, its session format, or its JSON stream shape.
EVERYTHING ELSE IS HOST-NEUTRAL.

JUDGE THE BODY, NOT THE NAME. Three names in this set sound host-specific and are documented
as neutral. `pinned_child_env` and `pinned_module_argv` pin a NESTED `aw` invocation, and the
in-tree comment above agy's import of them records that BOTH drivers must stay symmetric and
that "a second copy is exactly how the previous inert half-pin came to differ from what it
looked like it did". `announce_run_order` prints through the shared `render_stream` formatter
and holds no opencode concept at all.

JUDGE CODE, NOT PROSE. A comment or docstring mentioning `aw oc run` is NOT a body reference
to an opencode concept. This distinction decides real cases in this very set rather than being
hypothetical: measured at execution by stripping comments AND docstrings from all 56
definitions, exactly ONE retains an `oc` token in executable code (`process_backlog_close`,
see its row), while `queue_sort_key`, `run_order_rationale`, `render_runs_pointer` and
`dependency_status_detailed` carry one in PROSE ONLY and are neutral. A grep would have
misclassified four names.

A HOST LABEL IS A PARAMETER, NOT AN OPENCODE CONCEPT. `process_backlog_close` hardcodes the
string `closed by aw oc run: ...` into a commit message while agy calls that same shared
function, so an antigravity-driven run already writes a false provenance today. That is a REAL
LIVE DEFECT, recorded in the row and filed to the backlog, and it is NOT a reason to call the
function opencode-specific: the fix is to inject the label, which is what `runner_shared`
already does for `integrate_lane_branch` (see `HOST_LABELS` in `tests/test_runner_shared.py`).

WHAT THE CRITERION DOES NOT DECIDE, kept as a SEPARATE axis rather than smuggled into a
verdict. "Is this host-neutral?" and "can it move, and where to?" are different questions. A
name can be plainly neutral while its move is blocked (a live Set is editing that surface) or
its destination contested (`render_stream` may own a wording function rather than
`runner_shared`). Collapsing those into an `unsettled` VERDICT would report the criterion as
having failed when it did not. So each row carries `move_note`, and `MOVE_UNSETTLED` below
lists the names whose MOVE Order 02 must resolve or defer. An `unsettled` verdict is reserved
for a name the criterion itself genuinely cannot settle; there are none today, and that is
reported as a measurement rather than as tidiness.

--------------------------------------------------------------------------------------------
WHAT THE CLASSIFICATION FOUND (E-02), stated plainly because the result is one-sided
--------------------------------------------------------------------------------------------

ALL 56 NAMES ARE HOST-NEUTRAL. Zero opencode-specific, zero unsettled. That is a surprising
enough result to state rather than bury: it predicts that Order 02's RESIDUAL oc-to-agy import
set is EMPTY, i.e. this coupling should go to zero rather than shrink to a core of genuinely
opencode-owned names. If Order 02 finds a residual it cannot move, that is a finding against
this classification and should be reported as one.

THE REAL WORK ORDER 02 FACES IS NOT VERDICTS, IT IS CLOSURE. A neutral function whose body
closes over an oc-PRIVATE module-level name cannot move alone: the private name must move, be
injected, or be shared too. Each row therefore records `closes_over`, measured by AST at this
execution, which is the sizing information a mover actually needs and which no count conveys.

--------------------------------------------------------------------------------------------
THE THREE BINDING TIERS, because they have materially different move costs
--------------------------------------------------------------------------------------------

`pure-reexport`      module-level, spelled `as <same-name>`, and the bound name is never used
                     in agy's own body. These are the ones `ruff` DELETES: the backlog item
                     records it removing six of them on a first commit attempt, caught only by
                     the cross-driver symmetry test. The `as <same-name>` form is load-bearing.
`module-level`       module-level and CONSUMED in agy's body, so a move must keep the binding
                     reachable at the call sites.
`lazy-wrapper`       imported INSIDE a delegating function body. This tier is invisible to an
                     identity audit: measured, `agy.<name> is oc.<name>` is FALSE for all of
                     them, because agy exposes its own wrapper. It is also invisible to a
                     guard written over `tree.body`, which is why the guard below walks the
                     WHOLE tree (see `oc_to_agy_imports`).
"""

from __future__ import annotations

import ast
import pathlib
import unittest
from typing import NamedTuple

from agent_workflows import agy_runipd, oc_runipd

NEUTRAL = "host-neutral"
OPENCODE_SPECIFIC = "opencode-specific"
UNSETTLED = "unsettled"

#: Binding tiers, in the order a mover should think about them.
PURE_REEXPORT = "pure-reexport"
MODULE_LEVEL = "module-level"
LAZY_WRAPPER = "lazy-wrapper"


class Name(NamedTuple):
    """One name `agy_runipd` imports from `oc_runipd`, and what we judged it to be.

    `verdict` answers the CRITERION only. `move_note` carries everything the criterion does
    not decide (a contested destination, a live Set editing the same surface, a co-located
    private dependency, a defect found while reading the body), so the two axes stay separate.
    `closes_over` is the oc-PRIVATE module-level names the body references, measured by AST:
    it is empty for a name that can move on its own and non-empty for one that cannot.
    """

    name: str
    group: str
    verdict: str
    tier: str
    reason: str
    closes_over: tuple[str, ...] = ()
    move_note: str = ""


# =============================================================================================
# THE CLASSIFICATION (E-02). Grouped by CONCERN, because the argument lives in the groups and a
# flat list of 56 is unreviewable. Every row's `tier` and `closes_over` were measured by AST at
# execution; every `verdict` applies the criterion in the docstring to the definition's BODY.
#
# THIS TABLE IS ALSO THE FROZEN SET (E-03). The guard below derives what it pins FROM these
# rows, deliberately, so a new import cannot be admitted without a verdict and a reason. Do not
# add a bare name to a separate pin list; there is no separate pin list.
# =============================================================================================
CLASSIFICATION: tuple[Name, ...] = (
    # --- dependency graph evaluation (13) ----------------------------------------------------
    # The largest group and the least ambiguous: this is the shared rule set that decides which
    # queued plan may run, and both hosts must answer it identically. `dependency_status_detailed`
    # is the cautionary tale of the whole Set: agy carried its own BROKEN copy for months because
    # the symmetry guard's name list omitted it.
    Name(
        "edge_satisfied",
        "dependency-graph",
        NEUTRAL,
        MODULE_LEVEL,
        "decides whether one typed dependency edge is satisfied; pure record/state logic",
    ),
    Name(
        "dependency_status",
        "dependency-graph",
        NEUTRAL,
        MODULE_LEVEL,
        "aggregates edge verdicts for one plan; no host concept in the body",
    ),
    Name(
        "dependency_status_detailed",
        "dependency-graph",
        NEUTRAL,
        MODULE_LEVEL,
        "the `_detailed` sibling adding a root-cause map; mentions `aw oc run` in PROSE only",
        closes_over=("EXECUTION_SUCCESS_STATES", "TERMINAL_STATES"),
        move_note=(
            "the name whose ABSENCE from `_SHARED_NAMES` let the symmetry guard pass over "
            "agy's real broken copy for months (`03ie04` E-04 added it)"
        ),
    ),
    Name(
        "dependency_reasons",
        "dependency-graph",
        NEUTRAL,
        PURE_REEXPORT,
        "renders why an edge is unsatisfied; reporting text, no gating decision",
    ),
    Name(
        "cascade_dependency_blocked",
        "dependency-graph",
        NEUTRAL,
        MODULE_LEVEL,
        "propagates dependency-blocked over reverse edges to a fixed point",
        closes_over=("EXECUTION_SUCCESS_STATES", "SUCCESS_STATES", "TERMINAL_STATES"),
    ),
    Name(
        "preflight_dependency_findings",
        "dependency-graph",
        NEUTRAL,
        PURE_REEXPORT,
        "runs the SHARED evaluator over selected plans; already a thin call into `check_engine`",
        closes_over=("_consuming_actions_for",),
    ),
    Name(
        "enforce_dependency_preflight",
        "dependency-graph",
        NEUTRAL,
        LAZY_WRAPPER,
        "raises `DriverError` on an invalid selected graph; `DriverError` is ALREADY shared",
        move_note=(
            "the behavioral defect the backlog item filed (two DriverError classes) was fixed "
            "by `818uru`, so this is now a pure layering move"
        ),
    ),
    Name(
        "DEPENDENCY_FATAL_RULES",
        "dependency-graph",
        NEUTRAL,
        PURE_REEXPORT,
        "a frozenset of check-rule ids; data, and not host data",
    ),
    Name(
        "_artifact_owners",
        "dependency-graph",
        NEUTRAL,
        PURE_REEXPORT,
        "looks owners up in the shared identity index; body is a `check_engine` call",
    ),
    # --- backlog closing (11) ----------------------------------------------------------------
    # The rule set deciding whether a run may close a backlog item. Its in-tree comment already
    # states the intent this Set is finishing: every rule "lives ONCE in `oc_runipd` and this
    # module binds the SAME objects", which is the right instinct wired to the wrong module.
    Name(
        "close_backlog_item",
        "backlog-closing",
        NEUTRAL,
        PURE_REEXPORT,
        "closes an item through the lifecycle-owned setter, never by editing the file",
        closes_over=("run_checked",),
        move_note="`run_checked` is already a `runner_shared` symbol each host wraps (injection precedent)",
    ),
    Name(
        "commit_backlog_close",
        "backlog-closing",
        NEUTRAL,
        PURE_REEXPORT,
        "path-scoped-commits the moved item file via the shared tooled commit path",
        closes_over=("run_checked",),
    ),
    Name(
        "process_backlog_close",
        "backlog-closing",
        NEUTRAL,
        MODULE_LEVEL,
        "orchestrates the close after a plan reaches executed; the ONE body with an `oc` token in CODE",
        closes_over=("collect_lane_earned_paths",),
        move_note=(
            "LIVE DEFECT: its commit message hardcodes `closed by aw oc run:` while agy calls this "
            "same function, so agy-driven runs record a false provenance today. A host LABEL is a "
            "parameter, not an opencode concept, so the verdict stays neutral; filed as a bug, NOT "
            "fixed by `9kmbr0`, which moves and changes nothing"
        ),
    ),
    # --- run ordering (4) ---------------------------------------------------------------------
    # --- recovery routing (3) -----------------------------------------------------------------
    # All three are the lazy-wrapper tier, which is the tier an identity audit cannot see.
    Name(
        "classify_recovery_disposition",
        "recovery-routing",
        NEUTRAL,
        LAZY_WRAPPER,
        "routes a recovery turn from git FACTS via `worktree_lease`; no host concept",
        closes_over=(
            "DISPOSITION_FRESH_EXECUTION",
            "DISPOSITION_UNDETERMINED",
            "DISPOSITION_VERIFY_AND_CONTINUE",
            "RecoveryDisposition",
            "_lane_commit_subjects",
        ),
        move_note="cannot move alone: the `RecoveryDisposition` record and three DISPOSITION_* constants must move with it",
    ),
    Name(
        "route_recovery_turn",
        "recovery-routing",
        NEUTRAL,
        LAZY_WRAPPER,
        "records the routing verdict durably and dispatches; writes run state and events",
        closes_over=(
            "DISPOSITION_FRESH_EXECUTION",
            "DISPOSITION_UNDETERMINED",
            "RecoveryDisposition",
            "save_state",
        ),
    ),
    Name(
        "build_verify_and_continue_notice",
        "recovery-routing",
        NEUTRAL,
        LAZY_WRAPPER,
        "builds the prompt block telling a resumed turn to verify prior work; prompt text, host-agnostic",
        closes_over=("RecoveryDisposition",),
        move_note=(
            "DESTINATION CONTESTED: a wording function may belong to `render_stream` rather than "
            "`runner_shared`; Order 02 must settle it (see MOVE_UNSETTLED)"
        ),
    ),
    # --- shutdown reporting (4) ---------------------------------------------------------------
    # --- suite checking (5) -------------------------------------------------------------------
    Name(
        "run_suite_check",
        "suite-checking",
        NEUTRAL,
        MODULE_LEVEL,
        "runs the repository suite in the PRIMARY checkout and reads the result; runs pytest, not opencode",
        closes_over=("SUITE_CHECK_TIMEOUT_SECONDS",),
        move_note=(
            "MOVE MAY COLLIDE: three `integpath` plans are still pending and two declare both "
            "drivers in Scope-Paths (`rl67b0`'s F-15 discusses this name directly). Neutral by the "
            "criterion; sequencing is Order 02's problem (see MOVE_UNSETTLED)"
        ),
    ),
    Name(
        "SuiteCheckResult",
        "suite-checking",
        NEUTRAL,
        PURE_REEXPORT,
        "the record of what the driver observed running the suite; a data class",
        move_note="same `integpath` collision risk as `run_suite_check` (see MOVE_UNSETTLED)",
    ),
    Name(
        "SUITE_CHECK_ARGV",
        "suite-checking",
        NEUTRAL,
        PURE_REEXPORT,
        "the argv of the repository suite, `(python, -m, pytest)`; nothing to do with a host driver",
    ),
    Name(
        "parse_suite_summary",
        "suite-checking",
        NEUTRAL,
        PURE_REEXPORT,
        "extracts the suite COUNT LINE; exists because `runner_shared` may not import a host driver",
        closes_over=("_SUITE_SUMMARY_RE",),
        move_note=(
            "ALREADY HALF-SHARED, and the reason is this very layering: it was created as an "
            "injectable reader so `runner_shared` could parse the count line WITHOUT importing a "
            "runner. Re-homing it removes the need for the injection"
        ),
    ),
    Name(
        "extract_suite_failures",
        "suite-checking",
        NEUTRAL,
        PURE_REEXPORT,
        "pulls FAILED/ERROR node ids out of suite output; regex over pytest text",
        closes_over=("SUITE_FAILURE_LINE_LIMIT", "_SUITE_FAILURE_LINE_RE"),
    ),
    # --- earned integration (3) ---------------------------------------------------------------
    Name(
        "integration_is_earned",
        "earned-integration",
        NEUTRAL,
        PURE_REEXPORT,
        "decides whether a completed turn earned automatic integration; verifier/suite logic",
        closes_over=(
            "INTEGRATION_EARNED_BY_SUITE",
            "INTEGRATION_EARNED_BY_VERIFIER",
            "INTEGRATION_REFUSED_NO_SIGNAL",
            "INTEGRATION_REFUSED_SUITE_FAILED",
            "INTEGRATION_REFUSED_VERIFIER_DECLINED",
            "IntegrationVerdict",
        ),
        move_note=(
            "MOVE MAY COLLIDE with the pending `integpath` Set, and it also cannot move without "
            "its verdict record and five reason constants (see MOVE_UNSETTLED)"
        ),
    ),
    Name(
        "collect_earned_paths",
        "earned-integration",
        NEUTRAL,
        PURE_REEXPORT,
        "diffs an attempt's head range to list the paths it produced; a git diff",
        closes_over=("run_checked",),
        move_note="same `integpath` collision risk (see MOVE_UNSETTLED)",
    ),
    # --- declared spec-edit visibility (1 of an original 9) -----------------------------------
    # THE GROUP THAT ALREADY MOVED, and the clearest evidence of both the accretion and the fix.
    # All nine arrived in the thirteen days between Order 01's review and its execution; EIGHT were
    # re-homed into `runner_shared` by Order 02 (`1f7xno`) as the first batch, which is why their
    # rows are gone. That is the SANCTIONED SHRINK the frozen-set comment below describes, not
    # tampering.
    #
    # `record_item_spec_edits` IS THE ONE THAT STAYED, and the reason is a live defect rather than a
    # scruple: `runner_shared` ALREADY carries its own copy of this name whose body DIVERGES from
    # oc's (measured by docstring-stripped AST), and the two write DIFFERENT keys
    # (`spec_edits_reconciliation` versus `spec_edits`) in different record shapes. So re-homing it
    # would be a RECONCILIATION of two behaviors, not a pure move, and `1f7xno` is a pure-move plan.
    # Filed as backlog `tm5vnx`; do not "finish the group" by lifting this row without resolving it.
    Name(
        "record_item_spec_edits",
        "spec-edit-visibility",
        NEUTRAL,
        PURE_REEXPORT,
        "stores one item's reconciliation on its queue entry; takes `reconcile` as a PARAMETER",
        move_note=(
            "DEFERRED BY `1f7xno`: `runner_shared` already holds a DIVERGED copy writing a "
            "different key in a different shape (backlog `tm5vnx`), so the move is a "
            "reconciliation. "
            "ALREADY BUILT FOR SHARING: its docstring records that `_compute_scope_reconciliation` "
            "is forked per driver and is therefore INJECTED, 'the same explicit-injection form "
            "`runner_shared` uses'. The fork itself is out of this Set's scope"
        ),
    ),
    # --- nested-`aw` tool identity (4) --------------------------------------------------------
    # The group whose neutrality is load-bearing rather than incidental: agy imports these
    # BECAUSE a second copy already diverged once. See the in-tree comment above the import.
    Name(
        "pinned_child_env",
        "tool-identity",
        NEUTRAL,
        MODULE_LEVEL,
        "pins a nested `aw` child's PYTHONPATH to the runner's own package root; about `aw`, not opencode",
        closes_over=("runner_package_root",),
        move_note="the plan's worked example: sounds host-specific, is documented as requiring symmetry",
    ),
    Name(
        "pinned_module_argv",
        "tool-identity",
        NEUTRAL,
        MODULE_LEVEL,
        "builds argv invoking the runner's OWN `agent_workflows` CLI; the suppressing half of the pin",
        closes_over=("_AW_PIN_BOOTSTRAP",),
    ),
    Name(
        "assert_child_tool_identity",
        "tool-identity",
        NEUTRAL,
        PURE_REEXPORT,
        "verifies a pinned child resolves this package to the runner's own copy; fails closed",
        closes_over=("_AW_PIN_PROBE", "_TOOL_IDENTITY_VERIFIED"),
        move_note=(
            "memoized through a module-level `_TOOL_IDENTITY_VERIFIED`, so a move must not leave "
            "two caches; also counted by the ttywedge launcher-symmetry guard, which asserts the "
            "hosts expose an EQUAL number of nested-`aw` launchers"
        ),
    ),
    Name(
        "ToolIdentityError",
        "tool-identity",
        NEUTRAL,
        MODULE_LEVEL,
        "the run-fatal identity mismatch exception; nothing in it is about opencode",
        move_note=(
            "MOVE SHAPE IS AN EXCEPTION BINDING, not a function relocation: both hosts' `except` "
            "clauses bind it, and its sibling `StallTimeout` is DELIBERATELY defined in both "
            "drivers with an in-tree note saying so. Order 02 needs it in its callee map"
        ),
    ),
)

#: Names whose VERDICT is settled but whose MOVE Order 02 must resolve or defer, with the axis
#: named. Kept separate from the verdict so neither question is answered by the other. This is
#: the list the plan's OQ-01 asked for, expressed on the axis the question actually lives on.
MOVE_UNSETTLED: tuple[str, ...] = (
    # Destination contested: `render_stream` may own a wording function rather than `runner_shared`.
    #
    # `render_runs_pointer` LEFT THIS LIST BY MOVING, resolved rather than dropped (runnerlayer
    # Order 02 `1f7xno`). This list means "names whose MOVE Order 02 must resolve or defer", so a
    # moved name has had its move RESOLVED and an entry naming a row that no longer exists is what
    # `test_the_classification_is_internally_consistent` correctly refuses. It went to
    # `runner_shared` and not to `render_stream` because it could not be split from the closure it
    # belongs to: `emit_shutdown_report` prints it, and that reporter shares the
    # `_SIGNAL_REPORT_STATE` registry with `register_signal_report`, so the whole shutdown graph had
    # to land in one module or the two hosts would have kept separate signal registries.
    "build_verify_and_continue_notice",
    # Sequencing: the `integpath` Set was editing this surface when Order 01 classified these names.
    #
    # RE-MEASURED AT EXECUTION AND THE HEDGE IS STALE: all three plans Order 01 named (`51vw4y`,
    # `rl67b0`, `3v7wo6`) are in `.aw/records/plans/executed/`, so the collision it was avoiding has
    # resolved itself. Order 01's own text predicted exactly this and told Order 02 to "re-measure
    # rather than inherit either claim". `collect_earned_paths` and `run_earned_paths` therefore
    # moved, and they were not optional in any case: the backlog-closing closure REACHES them, so
    # deferring them would have blocked eleven other names.
    "run_suite_check",
    "SuiteCheckResult",
    "integration_is_earned",
)

#: Verdicts the criterion genuinely could not settle. EMPTY, and that is a MEASUREMENT: every
#: body was read, exactly one contained an `oc` token in executable code, and that one is a host
#: LABEL (a parameter) rather than an opencode concept. An empty list here is not an unapplied
#: criterion; `test_the_classification_is_internally_consistent` proves every row carries a
#: verdict from the enum and a non-empty reason.
UNSETTLED_VERDICTS: tuple[str, ...] = ()

# =============================================================================================
# THE FROZEN SET. DERIVED from the classification above, deliberately: there is no second list
# to keep in step, and admitting a name REQUIRES classifying it.
#
# SHRINKING THIS SET IS EXPECTED AND CORRECT. `runnerlayer` Order 02 (`1f7xno`) re-homes these
# names one batch at a time and updates this table in the SAME commit as each move, so a row
# disappearing alongside a move in `runner_shared` is the plan working. GROWING it is the
# regression this module exists to catch. And if this guard goes RED, the fix is NEVER to delete
# it or to trim the table to match: read the failure message, which names the symbol and states
# the two legitimate options.
# =============================================================================================
FROZEN_OC_TO_AGY_IMPORTS: frozenset[str] = frozenset(row.name for row in CLASSIFICATION)


def module_source(module) -> str:
    return pathlib.Path(str(module.__file__)).read_text(encoding="utf-8")


def oc_to_agy_imports(
    source: str, *, module_suffix: str = "oc_runipd"
) -> list[ast.alias]:
    """Every `from ...<module_suffix> import` ALIAS in ``source``, anywhere in the tree.

    WALKS THE WHOLE TREE, NOT `tree.body`, AND THAT IS THE POINT. Measured at this execution,
    4 of the 56 imports are NESTED inside delegating wrapper functions, so a guard iterating
    `tree.body` under-reports by four and freezes a set that is short by exactly the tier no
    other check can see (`agy.<name> is oc.<name>` is FALSE for all four, because agy exposes
    its own wrapper, so an identity-based audit is blind to them too).

    AST AND NOT GREP: a substring search counts a mention inside a comment or docstring and
    cannot distinguish an `as <same-name>` re-export from a use.
    """
    aliases: list[ast.alias] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith(
            module_suffix
        ):
            aliases.extend(node.names)
    return aliases


def imported_names(source: str, *, module_suffix: str = "oc_runipd") -> frozenset[str]:
    """The ORIGINAL names imported, keyed on `alias.name` and NEVER on `asname or name`.

    Measured at this execution: the 56 aliases carry only 54 distinct BOUND names, because
    three lazy wrappers bind their import to the same local `_shared`. A set keyed on the bound
    name therefore COLLAPSES those three into one entry and reports no change when one of them
    is added or removed, which is precisely the silent accretion this guard exists to stop.
    """
    return frozenset(
        alias.name for alias in oc_to_agy_imports(source, module_suffix=module_suffix)
    )


class ClassificationIntegrityTests(unittest.TestCase):
    """The classification must be a usable artifact, not a list of names with adjectives."""

    def test_the_classification_is_internally_consistent(self):
        problems = []
        seen: dict[str, str] = {}
        for row in CLASSIFICATION:
            if row.name in seen:
                problems.append(
                    f"  {row.name}: listed twice (groups {seen[row.name]!r} and {row.group!r})"
                )
            seen[row.name] = row.group
            if row.verdict not in (NEUTRAL, OPENCODE_SPECIFIC, UNSETTLED):
                problems.append(
                    f"  {row.name}: verdict {row.verdict!r} is not one of the three"
                )
            if row.tier not in (PURE_REEXPORT, MODULE_LEVEL, LAZY_WRAPPER):
                problems.append(
                    f"  {row.name}: tier {row.tier!r} is not one of the three"
                )
            if not row.reason.strip():
                problems.append(
                    f"  {row.name}: no reason. A verdict without a reason cannot be reviewed"
                )
            if row.verdict == UNSETTLED and row.name not in UNSETTLED_VERDICTS:
                problems.append(
                    f"  {row.name}: verdict is unsettled but it is missing from UNSETTLED_VERDICTS"
                )
        for name in UNSETTLED_VERDICTS:
            if name not in seen:
                problems.append(f"  {name}: in UNSETTLED_VERDICTS but not classified")
        for name in MOVE_UNSETTLED:
            if name not in seen:
                problems.append(f"  {name}: in MOVE_UNSETTLED but not classified")
            elif not dict((r.name, r) for r in CLASSIFICATION)[name].move_note.strip():
                problems.append(
                    f"  {name}: in MOVE_UNSETTLED with no move_note saying WHY"
                )
        self.assertEqual(
            problems,
            [],
            f"{len(problems)} classification rows are unusable. This table is the input "
            "`runnerlayer` Order 02 moves against, so a row missing a verdict, a tier or a reason "
            "would have that name moved on a guess.\n" + "\n".join(problems),
        )

    def test_every_frozen_name_is_a_REAL_DEFINITION_in_oc_runipd(self):
        """No pass-through tier: each name must be oc's OWN definition, not something oc imports.

        WHY THIS IS A TEST AND NOT A NOTE. It is zero today (measured), and zero is what makes
        Order 02's sizing "N definition moves" rather than "N minus some cheap re-points". If it
        ever becomes nonzero the right response is to re-point agy at the REAL owner rather than
        to move anything, so the two situations need opposite fixes and must be distinguishable.
        """
        tree = ast.parse(module_source(oc_runipd))
        defined: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined.add(node.name)
            elif isinstance(node, ast.Assign):
                defined.update(t.id for t in node.targets if isinstance(t, ast.Name))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                defined.add(node.target.id)
        passthrough = sorted(FROZEN_OC_TO_AGY_IMPORTS - defined)
        self.assertEqual(
            passthrough,
            [],
            "these names are imported from `oc_runipd` but NOT defined there, so `oc_runipd` is "
            "merely relaying someone else's symbol and agy is coupled to a driver for no reason. "
            "FIX: re-point agy at the module that actually owns each name; do NOT move anything.\n  "
            + "\n  ".join(passthrough),
        )

    def test_every_lazy_wrapper_row_really_is_a_NESTED_import(self):
        """The one tier claim worth gating, because it is the tier a naive guard cannot see.

        The `pure-reexport` versus `module-level` split is recorded but deliberately NOT gated:
        it turns on whether agy's body happens to reference the bound name, which changes for
        ordinary reasons that are not regressions, and a gate that fails on legitimate churn
        gets deleted. Nesting is different: it is an explicit authoring choice, it is what makes
        a name invisible to both `tree.body` and an identity check, and it does not drift.
        """
        source = module_source(agy_runipd)
        tree = ast.parse(source)
        nested_names: set[str] = set()

        def walk(node: ast.AST, inside: bool) -> None:
            for child in ast.iter_child_nodes(node):
                if (
                    inside
                    and isinstance(child, ast.ImportFrom)
                    and (child.module or "").endswith("oc_runipd")
                ):
                    nested_names.update(alias.name for alias in child.names)
                walk(
                    child,
                    inside
                    or isinstance(
                        child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                    ),
                )

        walk(tree, False)
        declared = {row.name for row in CLASSIFICATION if row.tier == LAZY_WRAPPER}
        self.assertEqual(
            (sorted(declared - nested_names), sorted(nested_names - declared)),
            ([], []),
            "the classification's `lazy-wrapper` rows must be exactly the imports nested inside a "
            "function body. First list: declared lazy but imported at module level. Second: "
            "imported inside a body but not declared lazy, which means the table under-reports the "
            "tier that no identity check can see.",
        )


class FrozenImportSetTests(unittest.TestCase):
    """The set is pinned by NAME, so churn cannot hide behind a stable count."""

    def test_the_oc_to_agy_import_set_is_exactly_the_frozen_set(self):
        """Adding a name must fail HERE, not be found by an audit weeks later.

        A COUNT WOULD NOT DO. Measured history: 40 names on 2026-09-03, 47 on 2026-09-08, 48 on
        2026-09-09, 56 on 2026-09-22, with names LEAVING in the same window as others arrived
        (four of the review-time 48 left for `runner_shared`/`selectors` while twelve arrived).
        A count guard passes straight through a one-out-one-in change.
        """
        live = imported_names(module_source(agy_runipd))
        added = sorted(live - FROZEN_OC_TO_AGY_IMPORTS)
        removed = sorted(FROZEN_OC_TO_AGY_IMPORTS - live)
        if not added and not removed:
            return
        lines = []
        if added:
            lines.append(
                "ADDED (agy now imports these from oc and the table does not classify them): "
                + ", ".join(added)
            )
        if removed:
            lines.append(
                "REMOVED (the table classifies these but agy no longer imports them): "
                + ", ".join(removed)
            )
        self.fail(
            "the oc-to-agy import surface changed, and this guard exists because nothing else in "
            "the suite notices that.\n  "
            + "\n  ".join(lines)
            + "\n\nWHAT TO DO, depending on which way it moved:\n"
            "  * You ADDED a name. If it is HOST-NEUTRAL (its body references no opencode-only "
            "concept: not the `opencode` binary, its CLI flags, its session format, or its JSON "
            "stream shape), it does NOT belong in a host driver at all. Put the definition in "
            "`agent_workflows/runner_shared.py` and have BOTH drivers import it from there; then "
            "this guard needs no edit. If it is genuinely OPENCODE-SPECIFIC, add a `Name(...)` row "
            "to CLASSIFICATION in this file with verdict `OPENCODE_SPECIFIC` and a reason saying "
            "which opencode concept its body references. Either way the name gets a verdict.\n"
            "  * You REMOVED a name by re-homing it (this is `runnerlayer` Order 02's whole job): "
            "delete its row from CLASSIFICATION in the SAME commit as the move, so the suite is "
            "never red between commits.\n"
            "  * DO NOT delete or weaken this guard, and do not trim the table to whatever the "
            "code now says. That converts a caught regression into an uncaught one, and a blanket "
            "`as <same-name>` re-export is exactly what `ruff` silently deleted six of once "
            "already."
        )

    def test_the_agy_to_oc_direction_is_ZERO(self):
        """Pin the reverse direction at zero, because a nonzero value would be an import CYCLE.

        Cheap here and otherwise nobody's job. NOTE what this does NOT duplicate: the existing
        substring claim in `tests/test_review_findings_cascade.py` ("oc_runipd does not import
        the other runner" as a `"import agy_runipd"` needle) is a spelling check inside a
        data-row test about a different subject, and `agy`'s own symbol-level
        `from agent_workflows.oc_runipd import` form is chosen deliberately so that needle stays
        meaningful. This is an AST measurement of the coupling itself. Do not weaken either.
        """
        reverse = sorted(
            imported_names(module_source(oc_runipd), module_suffix="agy_runipd")
        )
        self.assertEqual(
            reverse,
            [],
            "`oc_runipd` now imports from `agy_runipd`, which closes an import CYCLE between the "
            "two host drivers: the coupling has been zero in this direction throughout, and the "
            "fix is to put the shared name in `agent_workflows/runner_shared.py` rather than to "
            "reach across.\n  " + "\n  ".join(reverse),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

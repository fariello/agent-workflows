#!/usr/bin/env python3
"""The MOVE HARNESS for `runner_shared` (rununify Order 02, `818uru`).

WHAT THIS FILE PROVES, and why the claim needs a mechanical proof at all. Plan `818uru` moves 32 of
34 symbols that were defined TWICE, once per host runner, with AST-identical bodies, into one shared
module. Its central claim is that this is a PURE MOVE: no body changed, so no behavior changed. That
claim cannot be discharged by reading 34 diffs, and it cannot be discharged by the driver suites
either - the suites were fully green for months while `DriverError` was two DISTINCT classes needing
a hand-written translation wrapper. So the proof is mechanical and lives here.

THE THREE INDEPENDENT ASSERTIONS, none of which implies another:

  1. FINGERPRINT EQUALITY. `tests/fixtures/runner_shared_premove_fingerprints.json` holds the
     PRE-MOVE `ast.dump(ast.parse(ast.unparse(node)))` of all 34 symbols from BOTH runners, captured
     at HEAD `1ecc5891`. Each moved body must still fingerprint IDENTICALLY. This is what makes "pure
     move" falsifiable: edit one moved line and this fails.
  2. OBJECT IDENTITY. Both runners must resolve each moved name to the SAME object. Fingerprint
     equality alone would pass while a runner kept its own copy that merely looks the same, which is
     precisely the state this plan exists to end.
  3. NO RE-DEFINITION. Neither runner may still contain a top-level `def`/`class` of a moved symbol.
     Identity alone would pass while a stale duplicate sat in the file shadowed by a later import,
     which is a trap rather than a fix.

THE FINGERPRINT RULE SPLITS, and the exemption is ENUMERATED rather than implicit, because quietly
exempting the riskiest symbols is how a harness becomes decorative:

  * 27 symbols have NO outside dependency and are held to STRICT fingerprint equality.
  * 5 symbols gained ONE keyword-only parameter by design (`INJECTED`, below), so their post-move
    fingerprint CANNOT equal the pre-move capture - a body that gained a parameter is not
    byte-identical, and claiming otherwise about exactly the five highest-risk symbols would be a
    false claim. They are held to fingerprint equality MODULO the injection (proven by re-deriving
    the pre-move signature from the post-move one and THEN comparing bodies) plus a behavior test
    through each runner's wrapper.
  * 2 symbols did not move at all (`UNMOVABLE`, below) and this file pins WHY, so a later reader who
    counts 32 and expects 34 finds the reason instead of "finishing the job" and reintroducing a bug.
"""

from __future__ import annotations

import contextlib
import io
import json
import pathlib
import tempfile
import unittest
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared

BOTH = ("oc_runipd", "agy_runipd")
_MODULES = {
    "oc_runipd": oc_runipd,
    "agy_runipd": agy_runipd,
    "runner_shared": runner_shared,
}

# The 5 symbols that take an injected dependency, mapped to the keyword-only parameter each gained.
# THE MAINTAINER RULED THE THIN RUNNER-LOCAL WRAPPER over uniform parameter injection, for two
# measured reasons: uniform injection would have rewritten ~86 call sites in the two
# highest-contention files in the repo, and it would have broken assertion (1) above on exactly these
# five symbols. So `runner_shared` owns the parameterized function and each runner keeps a one-line
# wrapper at the ORIGINAL name and signature. `test_no_call_site_was_rewritten` is the measurement
# that keeps that promise honest.
# THE COUNT IS 8, NOT THE PLAN'S 5, and the three additions are recorded here rather than absorbed
# silently. `git_head`/`git_status`/`git_common_dir` call `run_checked`, which is in the SAME seam and
# which gained a parameter, so a naive lift raises `TypeError: missing 1 required keyword-only
# argument`. The plan's analysis looked for calls OUT of the moved set and could not see an
# intra-seam dependency on a symbol whose own signature changed. See decision 05-818uru-D4.
INJECTED: dict[str, str] = {
    "run_checked": "env_builder",
    "save_state": "write_report",
    "discover_plans": "parse_plan_file",
    "validate_manifest": "parse_dependency_token",
    "print_status": "driver_label",
    "git_head": "run_checked",
    "git_status": "run_checked",
    "git_common_dir": "run_checked",
}

# integpath-02 (`6sb3yu`): the lane->main integration seam, extracted LATER than the 34 above and
# therefore held to a DIFFERENT standard, stated here so the split is deliberate rather than an
# exemption. `INJECTED` above is pinned against `runner_shared_premove_fingerprints.json`, a capture
# of the PRE-MOVE source at HEAD `1ecc5891`; these three symbols do not appear in that fixture
# because they did not exist in it, so they have no pre-move fingerprint to match and adding them to
# `INJECTED` would make the fixture-backed tests raise `KeyError` rather than prove anything.
# `LaneIntegrationExtractionTests` is what replaces the fingerprint for them: it asserts the same
# three properties (no re-definition, object identity or a delegating wrapper, and no runner import)
# plus the host-label binding that a fingerprint could not express.
LANE_INTEGRATION_MOVED = (
    "dirty_tree_overlap",
    "build_lane_outcome",
    "integrate_lane_branch",
)

# stalemerge-01 (`87apfx`) E-05: the refusal CAUSE and conflict SHAPE machinery, pinned as a SEPARATE
# list rather than appended to `LANE_INTEGRATION_MOVED`, and the reason is a scope decision worth stating
# because appending was TRIED FIRST AND REVERTED.
#
# `LANE_INTEGRATION_MOVED` drives `test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners`, which
# demands that each host module carry the ATTRIBUTE. Satisfying it therefore requires adding ten
# `as <same-name>` re-exports to BOTH `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`,
# neither of which `87apfx` declares in its `Scope-Paths`, and the plan's Scope check explicitly forbids
# widening into undeclared host files without reporting first. Measured: the append made all nine tests
# in that class pass, at the cost of 36 added lines in each undeclared host module.
#
# THE PROPERTY E-05 ACTUALLY REQUIRES IS SINGLE-DEFINITION, NOT ATTRIBUTE IDENTITY. These symbols are
# reached from INSIDE `integrate_lane_branch`, which is itself shared, so a host cannot use a different
# implementation without first defining one - and that is exactly what
# `test_neither_runner_carries_its_own_copy_of_the_ladder` (extended below) and
# `test_the_cause_and_shape_machinery_has_EXACTLY_ONE_definition` forbid. Attribute identity would be a
# stronger claim about a weaker property: it proves each host can NAME the symbol, which no caller needs.
INTEGRATION_CAUSE_SHARED = (
    "tag_integration_cause",
    "read_integration_cause",
    "integration_cause_for_gate_status",
    "terminal_refusal_verdict",
    "classify_conflict_hunk_shape",
    "classify_conflict_shape_from_stages",
    "peer_commit_for_conflict",
    "build_conflict_resolver_detail",
    "format_conflict_resolver_facts",
    "conflict_resolver_remedy",
)

# Which of the three keep a runner-local WRAPPER (because they need a host-specific value) and which
# is bound by plain re-export. `dirty_tree_overlap` needs nothing from its host, so it is the SAME
# OBJECT in both runners; the other two are not, and asserting identity for them would be wrong.
LANE_INTEGRATION_WRAPPED = ("build_lane_outcome", "integrate_lane_branch")

# The host label each runner MUST bind into `integrate_lane_branch`. This value lands in a merge
# commit subject on MAIN, so it records WHICH driver integrated a lane; the shared function gives it
# no default precisely so a mis-binding cannot be silent.
HOST_LABELS = {"oc_runipd": "aw oc run", "agy_runipd": "aw agy run"}

# Symbols that MOVED into `runner_shared` while CALLING `run_checked`, mapped to how many calls each
# body makes. Two independent tests read this ONE table: the call-site census subtracts the total
# (those calls relocated, they were not rewritten), and the injection test asserts this is exactly
# the set of shared functions that call `run_checked` at all. Driving both from one place is what
# stops the two from disagreeing after the next extraction.
RELOCATED_RUN_CHECKED_CALLERS: dict[str, int] = {
    "git_head": 1,
    "git_status": 1,
    "git_common_dir": 1,
    # integpath-02 (`6sb3yu`): `git rev-parse`, `git diff --name-only`, `git diff`.
    "build_lane_outcome": 3,
    # hostdedup Order 01 (`li44r9`): `set_plan_approved` was BYTE-IDENTICAL in both runners and moved
    # here whole. Its body makes TWO `run_checked` calls -- the pinned `python -m agent_workflows` form
    # and the console-script `aw` fallback -- so each runner's census legitimately drops by two.
    #
    # THIS IS A RELOCATION AND NOT A REWRITE, which is the distinction this whole table exists to
    # record: no surviving call site in either runner was edited, and each host's remaining wrapper
    # passes `run_checked` as a NAME (`run_checked_fn=run_checked`), which is an INJECTION rather than a
    # call and therefore adds nothing back to the count. The shared body spells the calls
    # `run_checked_fn(...)` because this module may not import a runner; that is the same mechanism
    # `driver_begin` next door already uses.
    "set_plan_approved": 2,
    # runnerlayer Order 02 (`1f7xno`), backlog `cnwy8g`: the backlog-close and earned-paths trio, the
    # LAST group of `run_checked` callers `oc_runipd` still owned. ONE call each, counted by walking the
    # three bodies rather than estimated: `collect_earned_paths` diffs the attempt's head range,
    # `close_backlog_item` invokes the pinned nested `aw backlog set --status done`, and
    # `commit_backlog_close` reaches the tooled commit path once.
    #
    # THE SUBTRACTION IS ASYMMETRIC HERE, WHICH IS WHY THE COUNT IS STATED PER HOST BELOW RATHER THAN
    # IN THIS TABLE. Every other row subtracts from BOTH runners because both DEFINED the moved
    # function. These three were defined only in `oc_runipd`; `agy_runipd` IMPORTED them, so agy's
    # pre-move `run_checked` census never counted them (measured: 0 at the pre-move HEAD) and
    # subtracting from agy would drive its expectation negative. See
    # `REHOMED_BACKLOG_CLOSE_CALL_SITES` and its use in the census test.
    #
    # WHY THEY HAD TO BE INJECTED AT ALL rather than lifted plainly: the shared `run_checked` takes a
    # host-specific `env_builder`, so a shared body cannot resolve one. Measured when the lift was first
    # attempted without the injection: `TypeError: run_checked() missing 1 required keyword-only
    # argument: 'env_builder'` on ten tests in `tests/test_runner_backlog_close.py`.
    "collect_earned_paths": 1,
    "close_backlog_item": 1,
    "commit_backlog_close": 1,
}

#: The three rows above, subtracted from `oc_runipd` ONLY. They were oc-owned and agy-imported, so agy
#: never had these call sites to lose; a symmetric subtraction would make agy's expected census
#: negative, which is how this was caught (`0 != -5`).
REHOMED_BACKLOG_CLOSE_CALL_SITES: dict[tuple[str, str], int] = {
    ("oc_runipd", "run_checked"): 3,
}

# Shared `run_checked` callers that were BORN HERE rather than relocated from a runner, mapped the
# same way. THE DISTINCTION IS LOAD-BEARING AND IS WHY THIS IS A SECOND TABLE, not a fifth entry
# above: the census test SUBTRACTS the relocated total from each runner's pre-move count, because
# those calls left the runners. A natively-shared function never had a call site in either runner, so
# subtracting it would under-count the census by one per host and mask a genuinely rewritten call.
# The injection test, in contrast, must see BOTH tables, since every shared caller of `run_checked`
# has to take it as a keyword-only parameter regardless of how it got here.
#
# dirtygates-03 (`9iq461`): `collect_lane_earned_paths` makes ONE call (`git diff --name-only` over
# the lane branch's `base..branch` range). It is defined in this module from the start precisely so
# BOTH hosts reach it here instead of one importing it from the other (backlog `cnwy8g`).
# runconcur-01 (`vddpml`): `_resolved_main_tip` makes ONE call (`git rev-parse HEAD`), and it exists so
# that `main`'s tip is read INSIDE the repository integration lock rather than before acquiring it (a tip
# read while waiting is exactly the stale read that plan exists to stop). Natively shared: it was never a
# call site in either runner, and both hosts reach it through the one shared serializer.
#
# IT TAKES `run_checked` AS AN INJECTED PARAMETER rather than reaching `_run_git` directly, for the
# reason this table's own message states: rewriting a `run_checked` caller onto `_run_git` would be a
# BEHAVIOR CHANGE. It falls back to `_run_git` only when no runner injected one (the out-of-band verb
# path, which has no host `run_checked` to pass), and the tip is a RECORD rather than a gate either way.
NATIVE_SHARED_RUN_CHECKED_CALLERS: dict[str, int] = {
    "collect_lane_earned_paths": 1,
    "_resolved_main_tip": 1,
}

#: Every shared function that calls `run_checked`, however it arrived. The injection test reads this.
ALL_SHARED_RUN_CHECKED_CALLERS: dict[str, int] = {
    **RELOCATED_RUN_CHECKED_CALLERS,
    **NATIVE_SHARED_RUN_CHECKED_CALLERS,
}

# The 2 symbols that could NOT move, with the reason pinned in `UnmovableSymbolTests`.
UNMOVABLE = ("disable_lane_prompt",)

# `print_status` was never AST-identical across the runners: the two bodies differed ONLY by the
# literal host name. It is therefore compared against the OC pre-move capture with the host token
# normalized, and its rendered output is proven byte-identical for BOTH hosts separately.
HOST_NAMING_ONLY = ("print_status",)

# Symbols that GAINED A DOCSTRING since the pre-move capture, and nothing else. ENUMERATED, in the
# same spirit as `INJECTED` above, because an unenumerated exemption is how this harness would become
# decorative (depreview 03ie04 E-05).
#
# WHY THE EXEMPTION IS LEGITIMATE HERE. This file's claim is that a moved body still BEHAVES as it
# did. A docstring is an unobservable string constant, so it cannot change behavior, but it DOES
# change `ast.dump`. Holding a moved symbol to byte-identical AST forever would mean a moved symbol
# can never be DOCUMENTED, which penalizes precisely the improvement the repository wants: measured,
# `plan_bucket` had NO docstring at all, and the absence of its stated contract is what let
# `oc_runipd.edge_satisfied` ask it a question it structurally cannot answer (readiness), producing
# the defect 03ie04 fixes.
#
# THE EXEMPTION IS NARROW AND PROVEN BY SUBTRACTION, not asserted: `_without_docstring` removes ONLY
# the leading string expression and the remaining tokens must match the pre-move capture EXACTLY, so
# any edit to an executable statement in one of these bodies still FAILS. Every symbol NOT listed
# here is still held to STRICT equality including its docstring. Keep this list SHORT, and add a name
# only together with the reason the new documentation was needed.
DOCUMENTED_SINCE_MOVE = ("plan_bucket",)

# Symbols that ALREADY HAD a docstring in the pre-move capture and whose docstring TEXT was later
# REVISED, with no executable change. ENUMERATED separately from `DOCUMENTED_SINCE_MOVE`, and the
# separation is LOAD-BEARING rather than stylistic.
#
# WHY IT CANNOT BE THE SAME LIST, measured rather than reasoned about (IPD `2iye0e` E-04). The
# `DOCUMENTED_SINCE_MOVE` route subtracts the docstring from the CURRENT body ONLY and then demands
# equality with the capture VERBATIM, which is exactly right for a symbol that GAINED a docstring,
# because the capture has none to subtract (`plan_bucket`'s captured body provably starts with no
# docstring `Expr`). `describe_lane`'s captured body DOES start with one, so subtracting only from the
# current side compares a body WITHOUT a docstring against a capture WITH one, which can never match.
# Adding this name to `DOCUMENTED_SINCE_MOVE` was tried first and FAILED precisely there
# (`test_every_clean_symbol_is_a_STRICT_fingerprint_match`), so this list subtracts the docstring from
# BOTH SIDES.
#
# WHY THE EXEMPTION IS LEGITIMATE HERE. `describe_lane`'s docstring named plan `2c122z` as the live
# OWNER of `aw doctor --lanes` and `aw recover`. That plan was RETIRED UNLANDED 2026-09-02, so the
# sentence sent a reader to a plan that will never run; the verbs themselves still do not exist, so
# only the ownership claim was wrong. Correcting a false citation is a documentation improvement, and
# the alternative is the one this harness explicitly rejects elsewhere: re-baselining the recorded
# pre-move capture, which would destroy the falsifiability the fixture exists for.
#
# THE EXEMPTION IS NARROW AND PROVEN BY SUBTRACTION, not asserted. Every remaining token on both
# sides must match EXACTLY, so an edit to any executable statement still FAILS, which
# `test_a_redocumented_symbol_is_still_held_to_its_executable_body` proves by mutation. Keep this list
# SHORT, and add a name only together with the reason the documentation had to change.
REDOCUMENTED_SINCE_MOVE = ("describe_lane",)

# Symbols whose implementations have been SUPERSEDED by design in subsequent approved IPDs, and whose
# post-move bodies deliberately no longer match the pre-move capture. ENUMERATED, in the same spirit
# as `INJECTED` and `DOCUMENTED_SINCE_MOVE`.
#
# WHY THE EXEMPTION IS LEGITIMATE HERE. `state_root` moved in rununify Order 02 (`818uru`) with the
# hardcoded repo-backed literal `.aw/records/runs`. IPD `xbwq8n` (`runanalytics` Order 01) identified
# this hardcoded literal as a defect because the runs root is relocatable via `records_backend`
# (repository, companion, home). E-01 replaced the hardcoded literal with dynamic resolution through
# `project_context.resolve_project_context`.
#
# Holding `state_root` to byte-identical AST of the pre-move literal would freeze the defect in place.
# The superseded symbol is tested rigorously in its own dedicated test suite (`CanonicalRunsRootTests`)
# covering relocated backends, pure side-effect-free guarantees, and AST checks.
#
# `_run_git` GAINED AN OPTIONAL `timeout` (IPD `zexed1` E-02), and the exemption is recorded here rather
# than absorbed. WHY IT IS LEGITIMATE: the pre-move body passes NO timeout, so a `git` that wedges hangs
# its caller forever. That was harmless while every caller was a driver running unattended, and is not
# harmless now that `artifact_audit.build_finalize_evidence_index` reads history for `aw runs`, an
# INTERACTIVE read-only view. THE DEFAULT IS `None`, which is byte-for-byte today's behavior, so no
# existing caller changed; holding the symbol to its pre-move AST would instead mean the shared git
# helper can never grow a timeout, i.e. it would freeze the defect exactly as it would have for
# `state_root`. The added capability has its OWN dedicated coverage in
# `tests/test_artifact_audit.py::EvidenceIndexTests` (`test_it_passes_an_explicit_timeout` asserts the
# value actually reaches the subprocess, `test_a_timeout_is_unknown_not_a_pass` asserts a timeout
# classifies as unprovable rather than as a pass).
#
# `should_color` BECAME A DELEGATION to `term.should_color` (IPD `z8ddk0` E-02), and the exemption is
# recorded here rather than absorbed. WHY IT IS LEGITIMATE: the pre-move body was one of THREE
# independent implementations of the color capability decision that DISAGREED with each other,
# measured by execution 2026-09-19. This one ignored `TERM` entirely, so `TERM=dumb aw oc run` emitted
# color while `TERM=dumb aw attention` did not, and it read both variables by TRUTHINESS, so
# `FORCE_COLOR=0` - the value that plainly means "do not force" - FORCED COLOR ON, even into a pipe.
# Spec `uonrjg` R9.3a.2 requires the depth resolver above this decision have EXACTLY ONE definition,
# which is unsatisfiable while the decision beneath it has three.
#
# So holding this symbol to its pre-move AST would freeze TWO defects in place and block the spec
# requirement, exactly as it would have for `state_root`. THE `def` DELIBERATELY REMAINS, as a single
# delegating statement, because three shipped guards assert `runner_shared` DEFINES this symbol
# (`test_runner_refork_guard.py`'s `Owned("should_color", "runner_shared", BOTH)` row,
# `test_rununify_run_queue.py`'s `RESOLVES_IN_RUNNER_SHARED`, and `test_exactly_one_definition_package_wide`
# below); an import fails all three. A delegation cannot fingerprint as the body it replaces, which is
# why no shape of this change can satisfy the STRICT match and why the exemption is the only honest
# route. The unified decision has its OWN dedicated coverage in `tests/test_term.py`
# (`ShouldColorGridTests` pins all 16 `NO_COLOR` x `FORCE_COLOR` cells against both a TTY and a pipe
# plus the four `TERM` values; `OneOriginatingDefinitionTests` forbids a fourth implementation), and
# the delegation itself is pinned by `SharedColorDecisionTests` in this file.
# `describe_unresolved_plan_selector` GAINED THE ID-LESS-SPEC EXPLANATION (graduate-02 `iuxtjy` E-02),
# and the exemption is recorded here rather than absorbed. WHY IT IS LEGITIMATE: the pre-move body ends
# every non-plan branch with the bare sentence "'<sel>' is a <type>, not an IPD plan.", which is exactly
# right for eight of the nine types and MISLEADING for a spec that declares no `- Id:`. Measured at
# execution time, 19 of 36 spec records carry no `- Id:`, so this is the MAJORITY case, and the two
# surfaces disagree about it by design: the shared `selectors` layer RESOLVES such a file by stem (so
# `aw find` shows it) while `runner_shared.discover_specs` deliberately SKIPS it (without an id6 it
# cannot be named by a selector, cannot carry a review record, and cannot be attested). An operator
# therefore sees a file one tool finds and the runner declines, told only "not a plan", which reads as a
# bug in a deliberate skip. The added branch states the asymmetry and names the conversion verb
# (`aw rename specs <path> --to-id6`); it mints NOTHING, because a durable records write belongs to the
# `aw specs` verbs that own the tree and never to a dispatch path.
#
# Holding this symbol to its pre-move AST would mean the runner can never explain a refusal it is
# uniquely placed to explain, which is the same freeze-the-defect trap recorded above for `state_root`
# and `should_color`. Every OTHER branch of the function is byte-unchanged, and the new one has its own
# dedicated coverage in `tests/test_graduation_dispatch.py::RefusalContentTests`
# (`test_a_spec_with_no_Id_refuses_with_an_explanation_and_the_conversion_verb` asserts the message and
# the verb; `test_a_spec_that_HAS_an_Id_reached_by_stem_does_not_get_the_id_less_note` is the
# load-bearing negative proving the branch keys on the ACTUAL absence of `- Id:` rather than on the
# selector spelling, so it cannot assert something false about a conformant spec).
SUPERSEDED_SINCE_MOVE = (
    "state_root",
    "_run_git",
    "should_color",
    "describe_unresolved_plan_selector",
)


class WrapperTests(unittest.TestCase):
    """The wrapped symbols: original signature kept, callable at original name."""

    def test_each_runner_keeps_a_wrapper_at_the_original_name(self):
        for name in sorted(INJECTED):
            for runner in BOTH:
                with self.subTest(symbol=name, runner=runner):
                    self.assertIsNotNone(
                        getattr(_MODULES[runner], name, None),
                        f"{runner}.{name} must stay callable at its original name",
                    )


class CrossHostSuccessBarEqualityTests(unittest.TestCase):
    """`runnoop` Order 01 (`zz5yxq`) E-04: the two success bars may not diverge between the hosts.

    WHAT IS ALREADY SHARED AND WHAT IS NOT, measured rather than assumed, because the answer changed
    under this plan and the plan's own text is stale on it. `SUCCESS_STATES` was relocated into
    `runner_shared` by `rununify` Order 04 (`tx6q0h`) and both hosts now re-export the SAME object
    (`oc.SUCCESS_STATES is agy.SUCCESS_STATES` -> True), which is why the identity assertion below is
    available for it at all; `tests/test_rununify_host_descriptor.py::RELOCATED_CONSTANTS` pins that
    relocation from the other direction. `EXECUTION_SUCCESS_STATES` did NOT move: each host still
    declares its own set literal, so the two are EQUAL BUT NOT IDENTICAL, and an equality assertion is
    the strongest true statement available for it.

    WHY THE WEAKER ASSERTION IS STILL WORTH MAKING. A one-sided edit to a duplicated constant is
    SILENT: both are module-level set literals with identical values, so no host-token diff, no import
    error and no type check would show it, and the consequence is that a later fix to the bar reaches
    one driver only. This class is the tripwire. Unifying the objects is `rununify`'s extraction and
    `cnwy8g`'s layering correction, deliberately NOT done here; pinning the equality is the cheap
    durable guard that keeps the gap harmless until then.
    """

    def test_cross_host_success_bar_constants_and_tokens(self):
        from agent_workflows import run_evidence, run_gates

        self.assertIs(oc_runipd.SUCCESS_STATES, runner_shared.SUCCESS_STATES)
        self.assertIs(agy_runipd.SUCCESS_STATES, runner_shared.SUCCESS_STATES)
        self.assertIs(
            oc_runipd.EXECUTION_SUCCESS_STATES, runner_shared.EXECUTION_SUCCESS_STATES
        )
        self.assertIs(
            agy_runipd.EXECUTION_SUCCESS_STATES, runner_shared.EXECUTION_SUCCESS_STATES
        )
        self.assertEqual(
            runner_shared.EXECUTION_SUCCESS_STATES,
            {"executed", "substantially-complete"},
        )
        for name in (
            "success_states_for_action",
            "item_reached_success",
            "item_needs_approval",
            "exit_code_statuses",
        ):
            with self.subTest(symbol=name):
                shared = getattr(runner_shared, name)
                self.assertIs(getattr(oc_runipd, name), shared)
                self.assertIs(getattr(agy_runipd, name), shared)

        self.assertEqual(
            runner_shared.NEEDS_INPUT_TOKEN, run_gates.GATE_STATUS_NEEDS_INPUT
        )
        self.assertEqual(
            runner_shared.NEEDS_INPUT_TOKEN, run_evidence.AGGREGATE_NEEDS_INPUT
        )
        self.assertEqual(runner_shared.NEEDS_INPUT_KEY, runner_shared.NEEDS_INPUT_TOKEN)
        self.assertEqual(oc_runipd.NEEDS_INPUT_TOKEN, runner_shared.NEEDS_INPUT_TOKEN)
        self.assertEqual(agy_runipd.NEEDS_INPUT_TOKEN, runner_shared.NEEDS_INPUT_TOKEN)


class DriverErrorUnificationTests(unittest.TestCase):
    """`DriverError` unification and exception hierarchy across runners."""

    def test_both_runners_share_the_one_class_and_stall_timeout_hierarchy(self):
        self.assertIs(oc_runipd.DriverError, agy_runipd.DriverError)
        self.assertIs(oc_runipd.DriverError, runner_shared.DriverError)

        for name in ("StallTimeout", "EmptyStatusSelection"):
            with self.subTest(symbol=name):
                shared_cls = getattr(runner_shared, name)
                self.assertIs(getattr(oc_runipd, name), shared_cls)
                self.assertIs(getattr(agy_runipd, name), shared_cls)
                self.assertTrue(issubclass(shared_cls, runner_shared.DriverError))

        # Stall timeout caught by DriverError across runners
        for runner in BOTH:
            with self.subTest(runner=runner):
                with self.assertRaises(runner_shared.DriverError):
                    raise _MODULES[runner].StallTimeout("stalled")

        # DriverError raised from oc caught by agy
        caught = False
        try:
            raise oc_runipd.DriverError("raised from the opencode side")
        except agy_runipd.DriverError:
            caught = True
        self.assertTrue(caught)

    def test_oc_ToolIdentityError_still_subclasses_it(self):
        self.assertTrue(
            issubclass(oc_runipd.ToolIdentityError, runner_shared.DriverError)
        )


class BehaviorThroughWrapperTests(unittest.TestCase):
    """The behavior half the injected symbols' fingerprint exemption is backed by."""

    def test_run_checked_behavior_and_errors(self):
        import sys

        out = oc_runipd.run_checked([sys.executable, "-c", "print('ok-oc')"])
        self.assertEqual(out, "ok-oc")
        out = agy_runipd.run_checked([sys.executable, "-c", "print('ok-agy')"])
        self.assertEqual(out, "ok-agy")

        for runner in BOTH:
            with self.subTest(runner=runner):
                with self.assertRaises(runner_shared.DriverError):
                    _MODULES[runner].run_checked(
                        [sys.executable, "-c", "import sys; sys.exit(3)"]
                    )
                out_pin = _MODULES[runner].run_checked(
                    [
                        sys.executable,
                        "-c",
                        "import os; print(os.environ.get('AW_PIN_KEEP_ROOT', 'MISSING'))",
                    ]
                )
                self.assertNotEqual(out_pin, "MISSING")
                self.assertEqual(out_pin, oc_runipd.runner_package_root())

    def test_save_state_writes_state_and_calls_each_runners_own_write_report(self):
        import tempfile

        for runner in BOTH:
            with self.subTest(runner=runner):
                module = _MODULES[runner]
                with tempfile.TemporaryDirectory() as tmp:
                    run_dir = pathlib.Path(tmp)
                    state = {"run_id": "run-x", "queue": [], "repo": tmp}
                    module.save_state(run_dir, state)
                    self.assertTrue((run_dir / "state.json").is_file())
                    written = json.loads((run_dir / "state.json").read_text())
                    self.assertEqual(written["run_id"], "run-x")
                    self.assertIn("updated_at", written)
                    self.assertTrue(
                        (run_dir / "execution-report.md").is_file(),
                        "the injected `write_report` did not run",
                    )

    def test_validate_manifest_accepts_valid_and_rejects_invalid(self):
        valid = {
            "schema_version": 1,
            "plans": {
                "aaaaaa": {"file": "a.ipd.md", "set": "s1", "dependencies": []},
            },
            "sets": {"s1": {"order": ["aaaaaa"]}},
        }
        bad_dep = {
            "schema_version": 1,
            "plans": {
                "aaaaaa": {
                    "file": "a.ipd.md",
                    "set": "s1",
                    "dependencies": ["!!not a token!!"],
                }
            },
            "sets": {"s1": {"order": ["aaaaaa"]}},
        }
        for runner in BOTH:
            with self.subTest(runner=runner):
                _MODULES[runner].validate_manifest(valid)
                with self.assertRaises(runner_shared.DriverError):
                    _MODULES[runner].validate_manifest(bad_dep)
                with self.assertRaises(runner_shared.DriverError):
                    _MODULES[runner].validate_manifest({"schema_version": 999})


class DiscoverPlansRecordTypeTests(unittest.TestCase):
    """The record types are now the SAME, deliberately."""

    def _repo(self, tmp: pathlib.Path) -> pathlib.Path:
        plans = tmp / ".aw" / "records" / "plans" / "pending"
        plans.mkdir(parents=True)
        (plans / "20260101-setaaa-01-aaaaaa-a-plan.ipd.md").write_text(
            "# IPD: a plan\n\n- Id: aaaaaa\n- Status: approved\n- Set: setaaa\n"
            "- Order: 1\n- Kind: child\n",
            encoding="utf-8",
        )
        return tmp

    def test_both_runners_discover_plans_yields_shared_record_with_kind(self):
        import tempfile

        self.assertIs(oc_runipd.PlanRecord, agy_runipd.PlanRecord)
        self.assertIs(oc_runipd.PlanRecord, runner_shared.PlanRecord)
        self.assertIn("kind", runner_shared.PlanRecord._fields)

        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(pathlib.Path(tmp))
            for runner in BOTH:
                with self.subTest(runner=runner):
                    found = _MODULES[runner].discover_plans(repo)
                    self.assertIn("aaaaaa", found)
                    record = found["aaaaaa"]
                    self.assertIs(type(record), runner_shared.PlanRecord)
                    self.assertEqual(record.kind, "child")


class PrintStatusRenderingTests(unittest.TestCase):
    """`print_status` is the one host-naming-only symbol: prove BOTH hosts render as before."""

    def _run_dir(self, tmp: str) -> pathlib.Path:
        run_dir = pathlib.Path(tmp)
        (run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "run-20260101T000000Z-1",
                    "repo": tmp,
                    "queue": [],
                    "options": {},
                }
            ),
            encoding="utf-8",
        )
        return run_dir

    def test_each_host_renders_its_own_label_and_names_itself(self):
        import contextlib as _ctx
        import io
        import tempfile

        rendered = {}
        for runner, label in (("oc_runipd", "opencode"), ("agy_runipd", "antigravity")):
            with tempfile.TemporaryDirectory() as tmp:
                run_dir = self._run_dir(tmp)
                buf = io.StringIO()
                with _ctx.redirect_stdout(buf):
                    _MODULES[runner].print_status(run_dir)
                rendered[runner] = buf.getvalue()
                buf2 = io.StringIO()
                with _ctx.redirect_stdout(buf2):
                    runner_shared.print_status(run_dir, driver_label=label)
                self.assertEqual(
                    rendered[runner],
                    buf2.getvalue(),
                    f"{runner}.print_status diverged from the shared definition",
                )
        self.assertIn("opencode", rendered["oc_runipd"])
        self.assertNotIn("antigravity", rendered["oc_runipd"])
        self.assertIn("antigravity", rendered["agy_runipd"])
        self.assertNotIn("opencode", rendered["agy_runipd"])
        self.assertNotEqual(rendered["oc_runipd"], rendered["agy_runipd"])


class LaneIntegrationBehaviorTests(unittest.TestCase):
    """integpath-02 (`6sb3yu`) E-05: the extraction's claim is "NOTHING CHANGED", proven on BOTH hosts
    against REAL GIT rather than mocks.

    WHY REAL REPOSITORIES AND WHY BOTH HOSTS. The two driver suites are ASYMMETRIC (the agy side has
    far fewer tests), so an agy-only regression can leave both suites green - which is exactly how the
    50 diverged symbols in this package got that way. Each case below therefore runs through EACH
    RUNNER'S OWN wrapper, so the host-specific bindings (`run_checked`, `host_label`) are exercised
    and not bypassed by calling the shared function directly.

    The four cases are the four behaviors the extraction had to preserve: a clean integration and its
    per-host merge subject, the dirty-overlap refusal, the rename endpoints, and the conflict abort.
    """

    def _repo(self, tmp: pathlib.Path) -> pathlib.Path:
        """A throwaway repo with one commit on `main` and a lane branch off it."""
        import subprocess

        repo = tmp / "repo"
        repo.mkdir()
        run = lambda *a: subprocess.run(  # noqa: E731 - terse local helper
            list(a), cwd=repo, check=True, capture_output=True, text=True
        )
        run("git", "init", "-q", "-b", "main")
        run("git", "config", "user.email", "test@example.invalid")
        run("git", "config", "user.name", "Test")
        run("git", "config", "commit.gpgsign", "false")
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        run("git", "add", "base.txt")
        run("git", "commit", "-qm", "base")
        return repo

    def _git(self, repo: pathlib.Path, *args: str) -> str:
        import subprocess

        return subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True
        ).stdout.strip()

    def _lane(self, repo: pathlib.Path, id6: str, *, path: str, body: str):
        """Commit ``body`` at ``path`` on a lane branch and return a handle for it."""
        from agent_workflows import worktree_lease

        base = self._git(repo, "rev-parse", "HEAD")
        branch = f"aw/lane/{id6}"
        self._git(repo, "branch", branch)
        wt = repo.parent / f"wt-{id6}"
        self._git(repo, "worktree", "add", "-q", str(wt), branch)
        target = wt / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        self._git(wt, "add", path)
        self._git(wt, "commit", "-qm", f"lane {id6}: write {path}")
        return worktree_lease.WorktreeHandle(
            lane_id=id6, path=wt, branch=branch, base_commit=base
        )

    def _passing_runner(self):
        return lambda _diff, _files: True

    def _renaming_lane(self, repo: pathlib.Path, id6: str, *, orig: str, dest: str):
        """A lane that RENAMES ``orig`` -> ``dest``, plus a handle for it.

        dirtygates-02 (`metc8b`): this shape is what makes git's local-changes refusal REACHABLE while
        the pre-merge `dirty_tree_overlap` guard is retained, so it is not an exotic case - it is the
        shape of every plan moving `pending/` -> `executed/`. `build_lane_outcome` derives
        `changed_files` from `git diff --name-only`, which applies RENAME DETECTION and reports only
        ``dest``; the merge must nonetheless DELETE ``orig`` in main, so dirt on ``orig`` passes the
        guard (it is not in the incoming set) and git then refuses.

        ``orig`` must already exist and be committed on main. The body is long enough that git scores
        the pair as a rename rather than an add+delete.
        """
        from agent_workflows import worktree_lease

        base = self._git(repo, "rev-parse", "HEAD")
        branch = f"aw/lane/{id6}"
        self._git(repo, "branch", branch)
        wt = repo.parent / f"wt-{id6}"
        self._git(repo, "worktree", "add", "-q", str(wt), branch)
        self._git(wt, "mv", orig, dest)
        self._git(wt, "commit", "-qm", f"lane {id6}: rename {orig} -> {dest}")
        return worktree_lease.WorktreeHandle(
            lane_id=id6, path=wt, branch=branch, base_commit=base
        )

    def _renamable_body(self) -> str:
        """Content long enough for git's rename detection to score a move as R100."""
        return "".join(f"line {i}\n" for i in range(40))

    def _git_trace(self, repo: pathlib.Path):
        """Record every `git` argv `runner_shared` runs, so a test can assert what was NOT run.

        `merge --abort` on a refusal that never started a merge exits 128 and its result is discarded,
        so its absence CANNOT be observed from the repository state afterwards. The passing criterion
        is that the call is not made, which requires seeing the calls.
        """
        calls: list[list[str]] = []
        real = runner_shared._run_git

        def traced(r, args, **kwargs):
            calls.append(list(args))
            return real(r, args, **kwargs)

        return calls, mock.patch.object(runner_shared, "_run_git", traced)

    def test_a_clean_lane_still_integrates_and_carries_ITS_OWN_host_label(self):
        """The clean path, plus the ONE value E-02 parameterized and so the one most likely miswired.

        A wrong label is invisible until someone audits main's log, which is why it is asserted
        POSITIVELY (this host's label present) AND NEGATIVELY (the other host's label absent).
        """
        import tempfile

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(pathlib.Path(tmp))
                handle = self._lane(repo, "aaa111", path="src/x.py", body="lane\n")
                # Advance main so the `--ff-only` attempt fails and the CONTROLLED `--no-ff` merge
                # (the only place the host label appears) is the path actually taken.
                (repo / "other.txt").write_text("moved on\n", encoding="utf-8")
                self._git(repo, "add", "other.txt")
                self._git(repo, "commit", "-qm", "main advances")

                integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                    repo, handle, "aaa111", self._passing_runner()
                )

                self.assertTrue(integrated, reason)
                self.assertEqual(kind, "integrated")
                subject = self._git(repo, "log", "-1", "--pretty=%s")
                self.assertEqual(
                    subject,
                    f"integrate({HOST_LABELS[runner]}): merge verified lane aaa111 to main",
                )
                other = next(v for k, v in HOST_LABELS.items() if k != runner)
                self.assertNotIn(other, subject)
                # The lane's file really is on main now.
                self.assertEqual(
                    (repo / "src" / "x.py").read_text(encoding="utf-8"), "lane\n"
                )

    def test_a_dirty_overlapping_path_still_refuses_with_main_untouched(self):
        import tempfile

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(pathlib.Path(tmp))
                handle = self._lane(repo, "bbb222", path="src/x.py", body="lane\n")
                head_before = self._git(repo, "rev-parse", "HEAD")
                # Un-owned dirt in MAIN on the very path the lane changed.
                (repo / "src").mkdir(parents=True, exist_ok=True)
                (repo / "src" / "x.py").write_text("un-owned dirt\n", encoding="utf-8")

                integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                    repo, handle, "bbb222", self._passing_runner()
                )

                self.assertFalse(integrated)
                self.assertEqual(kind, "merge-retry")
                self.assertIn("src/x.py", reason)
                # Main untouched: HEAD unmoved, the un-owned edit NOT clobbered, lane preserved.
                self.assertEqual(self._git(repo, "rev-parse", "HEAD"), head_before)
                self.assertEqual(
                    (repo / "src" / "x.py").read_text(encoding="utf-8"),
                    "un-owned dirt\n",
                )
                self.assertIn(
                    handle.branch,
                    self._git(repo, "branch", "--format=%(refname:short)"),
                )

    def test_a_rename_still_makes_BOTH_endpoints_count_as_dirty(self):
        """Load-bearing for this Set: a rename is how a plan moves into `executed/`.

        Dropping either endpoint would silently NARROW the refusal and let an integration proceed over
        a path it should have refused, so the origin is asserted as well as the destination.
        """
        import tempfile

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(pathlib.Path(tmp))
                (repo / "orig.txt").write_text("content\n", encoding="utf-8")
                self._git(repo, "add", "orig.txt")
                self._git(repo, "commit", "-qm", "add orig")
                self._git(repo, "mv", "orig.txt", "dest.txt")
                porcelain = self._git(repo, "status", "--short")
                self.assertIn("->", porcelain, porcelain)

                overlap = _MODULES[runner].dirty_tree_overlap
                self.assertEqual(overlap(repo, ["dest.txt"]), ["dest.txt"])
                self.assertEqual(overlap(repo, ["orig.txt"]), ["orig.txt"])
                self.assertEqual(
                    overlap(repo, ["orig.txt", "dest.txt"]), ["dest.txt", "orig.txt"]
                )
                # Disjoint dirt is still ignored, and no incoming files is never blocked.
                self.assertEqual(overlap(repo, ["unrelated.txt"]), [])
                self.assertEqual(overlap(repo, []), [])

    def test_a_real_conflict_still_aborts_leaving_main_clean(self):
        import tempfile

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(pathlib.Path(tmp))
                handle = self._lane(repo, "ccc333", path="clash.txt", body="lane\n")
                # Main COMMITS a conflicting change to the same path: the gate is diff-based and
                # passes, so the real `git merge` is what conflicts.
                (repo / "clash.txt").write_text("main\n", encoding="utf-8")
                self._git(repo, "add", "clash.txt")
                self._git(repo, "commit", "-qm", "main writes clash.txt")
                head_before = self._git(repo, "rev-parse", "HEAD")

                integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                    repo, handle, "ccc333", self._passing_runner()
                )

                self.assertFalse(integrated, reason)
                self.assertEqual(kind, "merge-refused")
                # Main is CLEAN: HEAD unmoved, no partial merge, no markers in the file.
                self.assertEqual(self._git(repo, "rev-parse", "HEAD"), head_before)
                self.assertEqual(self._git(repo, "status", "--short"), "")
                self.assertNotIn(
                    "<<<<<<<", (repo / "clash.txt").read_text(encoding="utf-8")
                )
                # No in-progress merge left behind: `MERGE_HEAD` exists only mid-merge, so its absence
                # is what proves the abort ran rather than the merge merely having failed.
                git_dir = pathlib.Path(
                    self._git(repo, "rev-parse", "--absolute-git-dir")
                )
                self.assertFalse((git_dir / "MERGE_HEAD").exists())
                # The lane branch survives for a human/serial resolution.
                self.assertIn(
                    handle.branch,
                    self._git(repo, "branch", "--format=%(refname:short)"),
                )

    def _refusal_repo(self, tmp: pathlib.Path, id6: str):
        """Main + a lane whose merge git will REFUSE TO START because main holds local changes.

        Built as the rename shape, which is what reaches this branch past the retained pre-merge
        overlap guard: the lane renames `moved.txt` -> `dest.txt`, and main has an uncommitted edit to
        `moved.txt`, which the merge must delete. Returns `(repo, handle, head_before, dirty_before)`.

        THE PRE-MERGE GUARD MUST STAY SILENT HERE OR THIS FIXTURE PROVES NOTHING, and what keeps it
        silent CHANGED with mergedirty-01 (`fujm0y`). It used to be rename detection: the guard was
        asked about the LANE's `changed_files`, which reports only `dest.txt`, so dirt on the rename
        ORIGIN was outside the question. `fujm0y` widened the input to the paths the MERGE would write
        (`['dest.txt', 'moved.txt']`, measured), which is precisely that plan's purpose, so the guard
        now DOES see `moved.txt` and refuses FIRST - retiring this fixture's original mechanism.

        SO THE PREDICTION IS FORCED TO **UNKNOWN**, which is the fixture's honest replacement rather
        than a contrivance to keep a test alive. `merge_write_set` returns None when it cannot know the
        write set - a git older than 2.38, which lacks `--write-tree`, or a `merge-tree` that exits
        non-zero - and `integrate_lane_branch` then falls back to the lane's `changed_files`, i.e. to
        the pre-`fujm0y` input. That fallback is a SHIPPED code path, so this arm is exactly what
        protects an older-git operator, and a test proving it is load-bearing rather than decorative.

        AND THE ARM IS REACHABLE ON A MODERN GIT TOO, which is why `fujm0y` did not delete it: the
        guard reads `git status` at one instant and the merge runs at a later one, and this is a SHARED
        CHECKOUT where a co-worker may dirty a path in between. No prediction can close that window.
        The invariant is therefore unchanged by the widening: git remains the authority on its own
        preconditions, and our prediction is only ever an EARLIER, more accurate refusal.

        WHAT WAS TRIED AND REJECTED, recorded so it is not retried. Hiding the edit from porcelain with
        `git update-index --assume-unchanged` also silences the guard, but git then CLOBBERED the
        un-owned edit during the merge attempt (measured: `moved.txt` came back without the local
        line), because `--assume-unchanged` is a promise to git that the file has not changed. That
        would have made the fixture assert "main is left exactly as found" while main was in fact
        modified, so it was the wrong mechanism, not merely an awkward one.
        """
        repo = self._repo(tmp)
        body = self._renamable_body()
        (repo / "moved.txt").write_text(body, encoding="utf-8")
        self._git(repo, "add", "moved.txt")
        self._git(repo, "commit", "-qm", "add moved.txt")
        handle = self._renaming_lane(repo, id6, orig="moved.txt", dest="dest.txt")
        lane_changed = self._git(
            repo, "diff", "--name-only", f"{handle.base_commit}..{handle.branch}"
        ).split()
        self.assertEqual(lane_changed, ["dest.txt"])
        dirty_before = body + "un-owned local edit\n"
        (repo / "moved.txt").write_text(dirty_before, encoding="utf-8")
        # The widened prediction DOES name the rename origin, which is `fujm0y` working: asserted here
        # so this fixture records WHY it must force the unknown path rather than looking like an
        # oversight to a later reader.
        self.assertEqual(
            sorted(runner_shared.merge_write_set(repo, handle.branch) or []),
            ["dest.txt", "moved.txt"],
        )
        self.assertEqual(
            runner_shared.dirty_tree_overlap(repo, lane_changed),
            [],
            "the retained guard must PASS on the FALLBACK input, or this test is not reaching git's "
            "own refusal",
        )
        return repo, handle, self._git(repo, "rev-parse", "HEAD"), dirty_before

    def _unknown_write_set(self):
        """Force `merge_write_set` to UNKNOWN, i.e. the older-git / non-zero-`merge-tree` fallback.

        Patched at the SHARED symbol because that is where the single implementation lives, so both
        hosts' wrappers reach the patched version and neither can drift past it.
        """
        return mock.patch.object(
            runner_shared, "merge_write_set", lambda _repo, _branch: None
        )

    def test_a_local_changes_refusal_is_integration_blocked_NOT_a_merge_conflict(self):
        """dirtygates-02 (`metc8b`) E-02: git refusing to START a merge is not a content conflict.

        MEASURED WITNESS: lanes `bzz5e6` and `f6idxs` (2026-09-13) each finalized verified work and
        were recorded `merge-conflict` carrying git's own "Your local changes ..." text. That kind is
        TERMINAL on its first attempt (`classify_integration_refusal`), so the misclassification is
        what converted a self-clearing condition into permanent in-run loss.

        BOTH ROUTES to the refusal are covered, because they differ in how the `--ff-only` attempt
        fails and only the structural discriminator classifies both: with main ADVANCED it fails as
        diverged, and with main NOT advanced it is ITSELF refused with the same text and execution
        falls through to the `--no-ff` attempt. A branch nested under a "main advanced" assumption
        would pass the first and fail the second.
        """
        import tempfile

        for runner in BOTH:
            for advanced in (True, False):
                with (
                    self.subTest(runner=runner, main_advanced=advanced),
                    tempfile.TemporaryDirectory() as tmp,
                ):
                    repo, handle, _base, dirty_before = self._refusal_repo(
                        pathlib.Path(tmp), "ddd444"
                    )
                    if advanced:
                        (repo / "other.txt").write_text("moved on\n", encoding="utf-8")
                        self._git(repo, "add", "other.txt")
                        self._git(repo, "commit", "-qm", "main advances")
                    head_before = self._git(repo, "rev-parse", "HEAD")

                    with self._unknown_write_set():
                        integrated, reason, kind = _MODULES[
                            runner
                        ].integrate_lane_branch(
                            repo, handle, "ddd444", self._passing_runner()
                        )

                    self.assertFalse(integrated, reason)
                    self.assertEqual(
                        kind,
                        "merge-retry",
                        f"a refusal to START a merge is the TRANSIENT arm, not a conflict: {reason}",
                    )
                    # Git's OWN words, naming the offending file, carried verbatim.
                    self.assertIn("Your local changes", reason)
                    self.assertIn("moved.txt", reason)
                    # And NOT the conflict helper's hard-coded phrase, which is the reported defect.
                    self.assertNotIn("merge-back conflict", reason)
                    # Main is exactly as found and the lane is intact (E-03).
                    self.assertEqual(self._git(repo, "rev-parse", "HEAD"), head_before)
                    self.assertEqual(
                        (repo / "moved.txt").read_text(encoding="utf-8"), dirty_before
                    )
                    self.assertIn(
                        handle.branch,
                        self._git(repo, "branch", "--format=%(refname:short)"),
                    )

    def test_the_two_failure_classes_are_told_apart_STRUCTURALLY_not_by_message_text(
        self,
    ):
        """The discriminator is `MERGE_HEAD`, so it cannot break under a localized or newer git.

        Asserted at the level that matters: the two conditions are driven through
        `integrate_lane_branch` under a git whose MESSAGES ARE NOT ENGLISH (`LC_ALL`/`LANGUAGE` forced
        to a non-English locale), and each must still land on its own kind. A text-keyed
        implementation passes a same-locale test and misclassifies silently here.
        """
        import os
        import tempfile

        # `merge_in_progress` itself: absent before any merge, present mid-conflict, absent after abort.
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(pathlib.Path(tmp))
            handle = self._lane(repo, "eee555", path="clash.txt", body="lane\n")
            self.assertFalse(runner_shared.merge_in_progress(repo))
            (repo / "clash.txt").write_text("main\n", encoding="utf-8")
            self._git(repo, "add", "clash.txt")
            self._git(repo, "commit", "-qm", "main writes clash.txt")
            import subprocess

            subprocess.run(
                ["git", "merge", "--no-ff", "--no-edit", "-m", "x", handle.branch],
                cwd=repo,
                capture_output=True,
                text=True,
            )
            self.assertTrue(
                runner_shared.merge_in_progress(repo),
                "a real conflict STARTS the merge, so MERGE_HEAD must exist",
            )
            self.assertEqual(runner_shared.conflicted_paths(repo), ["clash.txt"])
            self._git(repo, "merge", "--abort")
            self.assertFalse(runner_shared.merge_in_progress(repo))

        # Now both classes end-to-end under a NON-ENGLISH git locale.
        forced = {
            "LC_ALL": "C.UTF-8",
            "LANG": "C.UTF-8",
            "LANGUAGE": "de_DE:de",
            "GIT_TEST_GETTEXT_POISON": "1",
        }
        with mock.patch.dict(os.environ, forced):
            with tempfile.TemporaryDirectory() as tmp:
                repo, handle, _h, _d = self._refusal_repo(pathlib.Path(tmp), "fff666")
                # mergedirty-01 (`fujm0y`): the write set is forced UNKNOWN so this case still reaches
                # GIT's refusal and therefore still exercises the STRUCTURAL discriminator. Without it
                # the widened pre-merge guard refuses first, and the test would pass for a reason that
                # has nothing to do with git's message language - a hollow pass, not a green one.
                with self._unknown_write_set():
                    _integrated, _reason, kind = runner_shared.integrate_lane_branch(
                        repo,
                        handle,
                        "fff666",
                        self._passing_runner(),
                        host_label="aw oc run",
                        run_checked=oc_runipd.run_checked,
                        # dirtygates-05 (`ajxr5d`) E-03: the EXECUTE kind, stated explicitly. These cases are
                        # about the merge failure classes, which are shared by both kinds, so `execute` keeps
                        # them asserting exactly what they asserted before (the revalidation gate still runs).
                        action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
                    )
                self.assertEqual(
                    kind,
                    "merge-retry",
                    "classification must not depend on git's message language",
                )
                self.assertIn(
                    "Your local changes",
                    _reason,
                    "this case must land on GIT's refusal, not on the pre-merge prediction",
                )
            with tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(pathlib.Path(tmp))
                handle = self._lane(repo, "ggg777", path="clash.txt", body="lane\n")
                (repo / "clash.txt").write_text("main\n", encoding="utf-8")
                self._git(repo, "add", "clash.txt")
                self._git(repo, "commit", "-qm", "main writes clash.txt")
                _integrated, _reason, kind = runner_shared.integrate_lane_branch(
                    repo,
                    handle,
                    "ggg777",
                    self._passing_runner(),
                    host_label="aw oc run",
                    run_checked=oc_runipd.run_checked,
                    # dirtygates-05 (`ajxr5d`) E-03: the EXECUTE kind, stated explicitly. These cases are
                    # about the merge failure classes, which are shared by both kinds, so `execute` keeps
                    # them asserting exactly what they asserted before (the revalidation gate still runs).
                    action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
                )
                self.assertEqual(
                    kind,
                    "merge-refused",
                    "a real conflict must stay the TERMINAL kind in any locale",
                )

    def test_merge_abort_is_issued_for_a_conflict_and_NOT_for_a_refusal(self):
        """F-6: with no `MERGE_HEAD`, `git merge --abort` exits 128 and is pointless.

        Its result was discarded, so its absence is invisible in the repository afterwards; the argv
        trace is what makes "the call is not made" observable rather than merely tolerated.
        """
        import tempfile

        # (a) the local-changes refusal: NO abort.
        with tempfile.TemporaryDirectory() as tmp:
            repo, handle, _h, _d = self._refusal_repo(pathlib.Path(tmp), "hhh888")
            calls, patcher = self._git_trace(repo)
            # mergedirty-01 (`fujm0y`): UNKNOWN write set, so the merge is really ATTEMPTED and there is
            # really something whose abort could be wrongly issued. With the widened guard refusing
            # first, no merge would run at all and "no abort was issued" would be trivially true.
            with patcher, self._unknown_write_set():
                _i, _r, kind = runner_shared.integrate_lane_branch(
                    repo,
                    handle,
                    "hhh888",
                    self._passing_runner(),
                    host_label="aw oc run",
                    run_checked=oc_runipd.run_checked,
                    # dirtygates-05 (`ajxr5d`) E-03: the EXECUTE kind, stated explicitly. These cases are
                    # about the merge failure classes, which are shared by both kinds, so `execute` keeps
                    # them asserting exactly what they asserted before (the revalidation gate still runs).
                    action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
                )
            self.assertEqual(kind, "merge-retry")
            self.assertIn(
                ["merge", "--no-ff", "--no-edit", "-m", mock.ANY, handle.branch],
                calls,
                "the merge must actually be attempted, or the abort assertion below is vacuous",
            )
            self.assertNotIn(
                ["merge", "--abort"],
                calls,
                f"no merge was started, so nothing must be aborted; ran {calls}",
            )

        # (b) the genuine content conflict: abort IS issued, and main is left clean by it.
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(pathlib.Path(tmp))
            handle = self._lane(repo, "iii999", path="clash.txt", body="lane\n")
            (repo / "clash.txt").write_text("main\n", encoding="utf-8")
            self._git(repo, "add", "clash.txt")
            self._git(repo, "commit", "-qm", "main writes clash.txt")
            calls, patcher = self._git_trace(repo)
            with patcher:
                _i, reason, kind = runner_shared.integrate_lane_branch(
                    repo,
                    handle,
                    "iii999",
                    self._passing_runner(),
                    host_label="aw oc run",
                    run_checked=oc_runipd.run_checked,
                    # dirtygates-05 (`ajxr5d`) E-03: the EXECUTE kind, stated explicitly. These cases are
                    # about the merge failure classes, which are shared by both kinds, so `execute` keeps
                    # them asserting exactly what they asserted before (the revalidation gate still runs).
                    action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
                )
            self.assertEqual(kind, "merge-refused")
            self.assertIn(["merge", "--abort"], calls)
            # The `mergemsg` contract: the conflicted path is named, from the conflict's STDOUT.
            self.assertIn("clash.txt", reason)
            self.assertIn("merge-back conflict", reason)
            self.assertNotIn("Not possible to fast-forward", reason)
            # E-03: no partial merge survives, and the lane is preserved.
            self.assertEqual(self._git(repo, "status", "--short"), "")
            self.assertFalse(runner_shared.merge_in_progress(repo))
            self.assertIn(
                handle.branch, self._git(repo, "branch", "--format=%(refname:short)")
            )

    def test_the_local_changes_refusal_arm_is_DEFERRABLE_by_the_ladder(self):
        """Why the reclassification is not a cosmetic relabel.

        `classify_integration_refusal` defers ONLY `integration-blocked`; `merge-conflict` is terminal
        on its first attempt. So the kind this branch returns decides whether verified work gets
        another attempt or is lost for the run.
        """
        self.assertTrue(runner_shared.classify_integration_refusal("merge-retry"))
        self.assertFalse(runner_shared.classify_integration_refusal("merge-refused"))
        first = runner_shared.decide_integration_deferral(
            integ_kind="merge-retry", attempts_used=1, limit=10
        )
        self.assertTrue(first.deferred)
        self.assertEqual(first.status, "merge-retry")
        conflict = runner_shared.decide_integration_deferral(
            integ_kind="merge-refused", attempts_used=1, limit=10
        )
        self.assertFalse(conflict.deferred)
        self.assertEqual(conflict.status, "merge-refused")

    def test_an_UNMEASURED_gate_refusal_is_DEFERRABLE_and_not_a_merge_conflict(self):
        """`l2mzxn`: "the gate could not measure" is not "the suite failed", and must not be terminal.

        THE MEASURED INCIDENT (run `run-20260921T105933Z-1994623`, 2026-09-21). Three items completed
        successful agent turns and were refused `merge-conflict` because the revalidation runner could not
        resolve their lane endpoints. No conflict existed (`git merge-tree --write-tree` exited 0 for all
        three) and the merged tree was green (`7991 passed`), yet the recorded reason read "Full test
        suite / revalidation failed ... (per-lane-green + combined-red)" - asserting a suite run that was
        never invoked. Because `merge-conflict` is terminal on its FIRST attempt, all three verified lanes
        were also excluded from the deferral ladder and stranded for the rest of the run.

        TWO SEPARATE PROPERTIES, both asserted: the KIND is deferrable, and the reclassification happens
        from the fact the runner RECORDED rather than from a guess at the refusal text.
        """
        self.assertTrue(
            runner_shared.classify_integration_refusal("merge-unchecked"),
            "an unmeasured-gate refusal must be deferrable: unlike a real conflict, a re-attempt CAN "
            "succeed once the harness fault clears, and terminality here strands verified work",
        )
        first = runner_shared.decide_integration_deferral(
            integ_kind="merge-unchecked", attempts_used=1, limit=10
        )
        self.assertTrue(first.deferred)
        self.assertEqual(first.status, "merge-retry")
        self.assertIn(
            "could not MEASURE",
            first.reason,
            "the deferral verdict must name the harness fault; the dirty-overlap wording would tell "
            "an operator to wait for dirt to clear when nothing is dirty",
        )
        self.assertNotIn("dirty paths", first.reason)

        # BOUNDED: a harness fault that never clears still ends terminal rather than spinning forever.
        exhausted = runner_shared.decide_integration_deferral(
            integ_kind="merge-unchecked", attempts_used=11, limit=10
        )
        self.assertFalse(exhausted.deferred)
        self.assertEqual(exhausted.status, "merge-needs-human")
        self.assertIn("could not MEASURE", exhausted.reason)

    def test_the_refusal_site_RECLASSIFIES_only_an_unmeasured_revalidation(self):
        """The reclassification must key on the RECORD, so a real failure stays terminal.

        This is the discrimination that makes the new kind safe: `integrate_lane_branch` returns
        `merge-conflict` for ANY non-passing gate result, so the refusal site is where the harness fault
        is told apart from the code fault. Getting this wrong in the permissive direction would defer
        genuine conflicts and burn the budget; getting it wrong in the strict direction restores the
        `l2mzxn` defect. All four cases are therefore pinned together.
        """

        def _refuse(item, kind="merge-refused"):
            with tempfile.TemporaryDirectory() as d:
                state = {"options": {}, "queue": [item]}
                decision = runner_shared.record_integration_refusal(
                    run_dir=pathlib.Path(d),
                    state=state,
                    item=item,
                    attempt={},
                    integ_kind=kind,
                    integ_reason="integration gate did not pass (integration_failed_combined_red)",
                    branch="aw/lane/zzzzzz",
                    save_state=lambda *_a, **_k: None,
                    append_jsonl=lambda *_a, **_k: None,
                )
            return decision, item["integration_ladder"]["kind"]

        # 1. UNMEASURED -> reclassified and deferred.
        decision, kind = _refuse(
            {
                "id6": "aaa",
                "post_merge_revalidation": {
                    "passed": False,
                    "measured": False,
                    "reason": "the lane's base/head could not be resolved from run state",
                },
            }
        )
        self.assertEqual(kind, "merge-unchecked")
        self.assertTrue(decision.deferred)
        self.assertEqual(decision.status, "merge-retry")

        # 2. MEASURED RED -> a real combined-red verdict about the code stays terminal.
        decision, kind = _refuse(
            {
                "id6": "bbb",
                "post_merge_revalidation": {
                    "passed": False,
                    "measured": True,
                    "reason": "3 failed",
                },
            }
        )
        self.assertEqual(
            kind,
            "merge-refused",
            "a suite that RAN and failed is a verdict about the work; deferring it would spin the "
            "ladder against a failure repetition cannot fix",
        )
        self.assertFalse(decision.deferred)

        # 3. NO RECORD AT ALL -> fail closed. A caller that recorded nothing has made no claim, and a
        #    real merge conflict never reaches the revalidation runner, so this is the conflict path.
        decision, kind = _refuse({"id6": "ccc"})
        self.assertEqual(kind, "merge-refused")
        self.assertFalse(decision.deferred)

        # 4. A PASSING record is never reinterpreted (the refusal came from elsewhere in the gate).
        decision, kind = _refuse(
            {
                "id6": "ddd",
                "post_merge_revalidation": {"passed": True, "measured": True},
            }
        )
        self.assertEqual(kind, "merge-refused")
        self.assertFalse(decision.deferred)

    def test_the_terminal_verdict_NAMES_the_condition_instead_of_listing_four(self):
        """`l2mzxn`: the sentence a human reads must not be a menu of four possible causes.

        The old verdict read "repetition cannot fix a conflict, stale base, combined-red revalidation,
        or scope violation", leaving the reader to guess which fired - and in the measured incident it
        named none of them correctly, because the real cause was a harness fault absent from the list.
        A refusal an operator cannot explain is indistinguishable from a bug, which is why this is
        asserted rather than left to review.
        """
        verdict = runner_shared.decide_integration_deferral(
            integ_kind="merge-refused", attempts_used=1, limit=10
        ).reason
        self.assertNotIn(
            "stale base",
            verdict,
            "the verdict must not enumerate causes it cannot distinguish",
        )
        self.assertNotIn("scope violation", verdict)
        self.assertIn("terminal on its first attempt", verdict)
        self.assertIn(
            "integration_deferral",
            verdict,
            "having stopped guessing, the verdict must point at the field that carries the gate's "
            "actual status, or the specific cause becomes unfindable",
        )

    def test_an_unmeasured_revalidation_is_RECORDED_as_not_measured(self):
        """The flag the reclassification reads must actually be written by the refusing paths.

        Without this the two halves could pass independently while the wiring between them is broken:
        `revalidation_was_unmeasured` is the ONLY reader, and a runner that never writes `measured: false`
        would silently restore `merge-conflict` for every harness fault.
        """
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            run_dir = root / "run"
            run_dir.mkdir()
            # No suite checker injected: one of the four harness paths, and the cheapest to reach.
            item: dict = {"id6": "xx1111"}
            self.assertFalse(
                runner_shared.make_integration_validation_runner(
                    {"options": {"validate": False}}, run_dir, item
                )("d", ())
            )
            record = item["post_merge_revalidation"]
            self.assertIs(record["measured"], False)
            self.assertTrue(runner_shared.revalidation_was_unmeasured(item))

        # And the predicate is fail-closed on the shapes that are NOT harness faults.
        self.assertFalse(
            runner_shared.revalidation_was_unmeasured({"id6": "no-record"}),
            "an absent record makes no claim and must not be reinterpreted as a harness fault",
        )
        self.assertFalse(
            runner_shared.revalidation_was_unmeasured(
                {"post_merge_revalidation": {"passed": False, "measured": True}}
            )
        )
        self.assertFalse(
            runner_shared.revalidation_was_unmeasured(
                {"post_merge_revalidation": {"passed": True, "measured": False}}
            ),
            "a PASSING record is not a refusal, whatever its measured flag says",
        )

    def test_the_kind_vocabulary_is_UNCHANGED_by_the_extraction(self):
        """The `kind` values are a CONTRACT read by callers and by run state."""
        self.assertFalse(
            runner_shared.classify_integration_refusal(
                runner_shared.INTEGRATION_REDERIVED
            ),
            "merge-rederived is a SUCCESS kind; the deferral ladder must never claim it",
        )
        self.assertTrue(
            runner_shared.classify_integration_refusal(
                runner_shared.INTEGRATION_REFUSAL_TRANSIENT
            )
        )
        self.assertTrue(
            runner_shared.classify_integration_refusal(
                runner_shared.INTEGRATION_REFUSAL_UNMEASURED
            )
        )
        self.assertFalse(
            runner_shared.classify_integration_refusal(
                runner_shared.INTEGRATION_REFUSAL_CONFLICT
            )
        )


class CanonicalRunsRootTests(unittest.TestCase):
    """Canonical run-root and analytics namespace tests (runanalytics Order 01, `xbwq8n`).

    Validates E-01 / V-01:
      1. `state_root` resolves through project-context authority for repository, companion, and home.
      2. Side-effect-free analytics constants and helpers derive from `state_root`.
      3. `path_is_within_analytics` handles canonical, nested, symlinked, relative (`..`), and legacy roots,
         and rejects sibling paths starting with 'analytics'.
      4. Resolution creates NO directories on disk (pure).
      5. `state_root` AST contains no hardcoded `.aw/records/runs` literal.
    """

    def test_state_root_resolves_through_project_context_repository_backend(self):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "preset": "private-target",
                        "records_backend": "repository",
                    }
                ),
                encoding="utf-8",
            )
            resolved = runner_shared.state_root(repo)
            self.assertEqual(resolved, (repo / ".aw" / "records" / "runs").resolve())

    def test_state_root_resolves_through_project_context_companion_backend(self):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "preset": "public-target-private-companion",
                        "records_backend": "companion",
                    }
                ),
                encoding="utf-8",
            )
            resolved = runner_shared.state_root(repo)
            expected = (
                pathlib.Path(f"{repo.resolve()}.aw") / "records" / "runs"
            ).resolve()
            self.assertEqual(resolved, expected)

    def test_state_root_resolves_through_project_context_home_backend(self):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "project_id": "test-proj-home-42",
                        "records_backend": "home",
                    }
                ),
                encoding="utf-8",
            )
            resolved = runner_shared.state_root(repo)
            from agent_workflows.project_context import resolve_project_context

            ctx = resolve_project_context(target_repo=str(repo))
            expected = pathlib.Path(ctx.logical_roots["records"]).resolve() / "runs"
            self.assertEqual(resolved, expected)
            self.assertIn("test-proj-home-42", str(resolved))

    def test_analytics_subpaths_derive_from_state_root(self):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"schema_version": 2, "records_backend": "repository"}),
                encoding="utf-8",
            )
            s_root = runner_shared.state_root(repo)
            self.assertEqual(runner_shared.analytics_root(repo), s_root / "analytics")
            self.assertEqual(
                runner_shared.analytics_cache_dir(repo), s_root / "analytics" / "cache"
            )
            self.assertEqual(
                runner_shared.analytics_snapshots_dir(repo),
                s_root / "analytics" / "snapshots",
            )
            self.assertEqual(
                runner_shared.analytics_exports_dir(repo),
                s_root / "analytics" / "exports",
            )

    def test_path_is_within_analytics_canonical_and_nested(self):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"schema_version": 2, "records_backend": "repository"}),
                encoding="utf-8",
            )
            self.assertTrue(
                runner_shared.path_is_within_analytics(
                    runner_shared.analytics_root(repo), repo
                )
            )
            self.assertTrue(
                runner_shared.path_is_within_analytics(
                    runner_shared.analytics_cache_dir(repo), repo
                )
            )
            self.assertTrue(
                runner_shared.path_is_within_analytics(
                    runner_shared.analytics_snapshots_dir(repo)
                    / "run-20260101T000000Z-1",
                    repo,
                )
            )
            self.assertTrue(
                runner_shared.path_is_within_analytics(
                    runner_shared.analytics_exports_dir(repo) / "summary.json",
                    repo,
                )
            )
            # A real run directory is NOT within analytics
            self.assertFalse(
                runner_shared.path_is_within_analytics(
                    runner_shared.state_root(repo) / "run-20260101T000000Z-1",
                    repo,
                )
            )

    def test_path_is_within_analytics_symlink_and_relative(self):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"schema_version": 2, "records_backend": "repository"}),
                encoding="utf-8",
            )
            snap_dir = (
                runner_shared.analytics_snapshots_dir(repo) / "run-20260101T000000Z-1"
            )
            snap_dir.mkdir(parents=True)

            # Symlink outside pointing inside analytics
            outside_link = repo / "symlink_to_snapshot"
            outside_link.symlink_to(snap_dir)
            self.assertTrue(runner_shared.path_is_within_analytics(outside_link, repo))

            # Relative path with .. resolving inside analytics
            rel_inside = (
                runner_shared.state_root(repo)
                / "run-20260101T000000Z-1"
                / ".."
                / "analytics"
                / "cache"
            )
            self.assertTrue(runner_shared.path_is_within_analytics(rel_inside, repo))

            # Relative path starting with analytics/ but escaping via ..
            rel_outside = (
                runner_shared.analytics_root(repo) / ".." / "run-20260101T000000Z-1"
            )
            self.assertFalse(runner_shared.path_is_within_analytics(rel_outside, repo))

    def test_path_is_within_analytics_rejects_sibling_starting_with_analytics(self):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"schema_version": 2, "records_backend": "repository"}),
                encoding="utf-8",
            )
            s_root = runner_shared.state_root(repo)
            self.assertFalse(
                runner_shared.path_is_within_analytics(
                    s_root / "analytics_backup", repo
                )
            )
            self.assertFalse(
                runner_shared.path_is_within_analytics(
                    s_root / "analytics-backup", repo
                )
            )
            self.assertFalse(
                runner_shared.path_is_within_analytics(s_root / "analytics.json", repo)
            )
            self.assertFalse(
                runner_shared.path_is_within_analytics(
                    s_root / "analytics-extra" / "run-1", repo
                )
            )

    def test_path_is_within_analytics_legacy_roots(self):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td)
            # Legacy .aw/runs/analytics
            self.assertTrue(
                runner_shared.path_is_within_analytics(
                    repo / ".aw" / "runs" / "analytics" / "cache", repo
                )
            )
            # Legacy .agents/runs/analytics
            self.assertTrue(
                runner_shared.path_is_within_analytics(
                    repo / ".agents" / "runs" / "analytics" / "snapshots" / "run-1",
                    repo,
                )
            )
            # Legacy non-analytics runs
            self.assertFalse(
                runner_shared.path_is_within_analytics(
                    repo / ".aw" / "runs" / "run-1", repo
                )
            )
            self.assertFalse(
                runner_shared.path_is_within_analytics(
                    repo / ".agents" / "runs" / "run-1", repo
                )
            )

    def test_state_root_and_analytics_resolution_is_pure_and_creates_no_directories(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:
            repo = pathlib.Path(td) / "empty_repo"
            repo.mkdir()
            # Do NOT create any subdirectories
            _ = runner_shared.state_root(repo)
            _ = runner_shared.analytics_root(repo)
            _ = runner_shared.analytics_cache_dir(repo)
            _ = runner_shared.analytics_snapshots_dir(repo)
            _ = runner_shared.analytics_exports_dir(repo)
            _ = runner_shared.path_is_within_analytics(
                repo / ".aw" / "records" / "runs" / "analytics" / "test", repo
            )
            # Assert no directory was created
            self.assertFalse((repo / ".aw").exists())
            self.assertFalse(runner_shared.state_root(repo).exists())
            self.assertFalse(runner_shared.analytics_root(repo).exists())



class SharedVerificationResolutionTests(unittest.TestCase):
    """`hostdefault-02` (`ybkmzp`) E-01: the ONE host-neutral verification resolution."""

    def store(self, td: str, document: dict | None) -> None:
        path = pathlib.Path(td) / "agent-workflows" / "runner-profiles.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if document is not None:
            path.write_text(json.dumps(document), encoding="utf-8")

    def resolve(self, document, *, runner, profile=None, validate=None):
        import os
        from unittest import mock

        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": td}, clear=False):
                self.store(td, document)
                return runner_shared.resolve_verification_decision(
                    runner=runner, profile=profile, validate=validate
                )

    def test_shared_verification_decision_resolution(self):
        decision = self.resolve(None, runner="oc", validate=True)
        self.assertEqual(decision._fields, ("validate", "provenance"))
        self.assertNotIn("no_verify", decision._fields)
        self.assertIsInstance(decision.validate, bool)
        self.assertIsInstance(decision.provenance, str)

        doc = {"schema_version": 2, "defaults": {"validate": True}}
        said_nothing = self.resolve(doc, runner="oc", validate=None)
        self.assertIs(said_nothing.validate, True)
        self.assertEqual(said_nothing.provenance, "defaults")

        said_no = self.resolve(doc, runner="oc", validate=False)
        self.assertIs(said_no.validate, False)
        self.assertEqual(said_no.provenance, "explicit")

        said_yes = self.resolve(
            {"schema_version": 2, "defaults": {"validate": False}},
            runner="oc",
            validate=True,
        )
        self.assertIs(said_yes.validate, True)
        self.assertEqual(said_yes.provenance, "explicit")

        # Malformed store raises DriverError
        with self.assertRaises(runner_shared.DriverError) as ctx:
            self.resolve(
                {"schema_version": 2, "defaults": {"validate": "yes"}}, runner="oc"
            )
        self.assertIn("runner profile", str(ctx.exception))


class VerificationPolarityTests(unittest.TestCase):
    """`hostdefault-02` (`ybkmzp`) E-06: THE SAFETY-CRITICAL MATRIX, at the FROZEN-STATE level.

    The two hosts' frozen keys are OPPOSITE IN POLARITY: `oc_runipd` freezes `validate` and gates on
    it, `agy_runipd` freezes `no_verify` and gates on `not no_verify`. So a wiring change that looks
    correct can silently DISABLE verification on antigravity: a resolved `True` (verify) written
    un-negated into `no_verify` means the verifier does not run, with no error anywhere.

    A test that checks one host, or one direction, cannot detect that. All FOUR cells are asserted
    here, and they are read out of the run's real frozen `state.json` rather than off the resolver,
    because the resolver was already correct before this plan and the defect was entirely in what
    consumed it.
    """

    PLAN = """# IPD: polarity probe

- Date: 2026-09-13
- Kind: child
- Concern: fixture
- Scope: fixture
- Scope-Paths: README.md
- Status: approved
- Set: polarity
- Order: 1
- Highest E allocated: 01
- Id: {id6}
- Approval: 2026-09-13, fixture

## Workflow history
- 2026-09-13 reviewed (test): APPROVE; no blocking findings.
"""

    def make_repo(self, root: pathlib.Path, id6: str = "pol001"):
        import subprocess

        repo = root / "repo"
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
        (pending / f"20260913-polarity-01-{id6}-probe.ipd.md").write_text(
            self.PLAN.format(id6=id6), encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo

    def frozen_options(self, runner: str, argv: list, document: dict | None) -> dict:
        """Drive the REAL `initialize_run` with `--prepare-only` against an ISOLATED store."""

        import os
        from unittest import mock

        module = _MODULES[runner]
        with tempfile.TemporaryDirectory() as home:
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": home}, clear=False):
                if document is not None:
                    store = pathlib.Path(home) / "agent-workflows"
                    store.mkdir(parents=True, exist_ok=True)
                    (store / "runner-profiles.json").write_text(
                        json.dumps(document), encoding="utf-8"
                    )
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo(pathlib.Path(td))
                    args = module.build_parser().parse_args(
                        ["start", "pol001", "--repo", str(repo), *argv]
                    )
                    args.prepare_only = True
                    run_dir = module.initialize_run(args)
                    return runner_shared.load_state(run_dir)["options"]

    def test_verification_polarity_matrix_and_agreement(self):
        """resolved verify -> oc `validate=True` AND agy `no_verify=False`, and the converse."""

        verify_on = {"schema_version": 2, "defaults": {"validate": True}}
        verify_off = {"schema_version": 2, "defaults": {"validate": False}}

        oc_on = self.frozen_options("oc_runipd", [], verify_on)
        self.assertIs(oc_on["validate"], True, "cell 1: oc, resolved verify")
        self.assertIs(oc_on["no_audit"], False, "oc's derived key must agree")

        agy_on = self.frozen_options("agy_runipd", [], verify_on)
        self.assertIs(agy_on["no_verify"], False, "cell 2: agy, resolved verify")

        oc_off = self.frozen_options("oc_runipd", [], verify_off)
        self.assertIs(oc_off["validate"], False, "cell 3: oc, resolved do-not-verify")
        self.assertIs(oc_off["no_audit"], True, "oc's derived key must agree")

        agy_off = self.frozen_options("agy_runipd", [], verify_off)
        self.assertIs(agy_off["no_verify"], True, "cell 4: agy, resolved do-not-verify")

        # Floor with empty store
        oc = self.frozen_options("oc_runipd", [], None)
        self.assertIs(oc["validate"], False)
        self.assertIs(oc["no_audit"], True)
        agy = self.frozen_options("agy_runipd", [], None)
        self.assertIs(agy["no_verify"], False)
        self.assertNotIn("validate", agy)

        # Cross-host agreement
        for document in (None, verify_on, verify_off):
            with self.subTest(document=document):
                o = self.frozen_options("oc_runipd", [], document)
                a = self.frozen_options("agy_runipd", [], document)
                if document is None:
                    self.assertIs(o["validate"], False)
                    self.assertIs(not a["no_verify"], True)
                else:
                    self.assertIs(o["validate"], not a["no_verify"])


class VerificationChainFrozenStateTests(unittest.TestCase):
    """The four tiers pinned at the frozen-state level."""

    def frozen(self, runner: str, argv: list, document: dict | None) -> dict:
        return VerificationPolarityTests.frozen_options(
            VerificationPolarityTests(
                "test_verification_polarity_matrix_and_agreement"
            ),
            runner,
            argv,
            document,
        )

    def verifies(self, runner: str, options: dict) -> bool:
        """Each host's frozen key read in ITS OWN polarity, so one table covers both."""

        if runner == "oc_runipd":
            self.assertIs(
                options["no_audit"],
                not options["validate"],
                "oc's two frozen keys must never disagree",
            )
            return bool(options["validate"])
        return not bool(options["no_verify"])

    def test_verification_tiers_1_through_4_precedence(self):
        oc_store = {
            "schema_version": 2,
            "profiles": {"p": {"runner": "oc", "model": "v/m", "validate": False}},
            "defaults": {"profiles": {"oc": "p"}},
        }
        self.assertTrue(
            self.verifies(
                "oc_runipd", self.frozen("oc_runipd", ["--validate"], oc_store)
            )
        )
        agy_store = {
            "schema_version": 2,
            "profiles": {"p": {"runner": "agy", "model": "v/m", "validate": True}},
            "defaults": {"profiles": {"agy": "p"}},
        }
        self.assertFalse(
            self.verifies(
                "agy_runipd", self.frozen("agy_runipd", ["--no-validate"], agy_store)
            )
        )
        self.assertFalse(
            self.verifies(
                "agy_runipd", self.frozen("agy_runipd", ["--no-verify"], agy_store)
            )
        )

        # Tier 2: profile beats defaults
        for runner, host in (("oc_runipd", "oc"), ("agy_runipd", "agy")):
            with self.subTest(runner=runner):
                store = {
                    "schema_version": 2,
                    "profiles": {
                        "p": {"runner": host, "model": "v/m", "validate": True}
                    },
                    "defaults": {"profiles": {host: "p"}, "validate": False},
                }
                self.assertTrue(self.verifies(runner, self.frozen(runner, [], store)))

        # Tier 3: defaults beat host row
        self.assertTrue(
            self.verifies(
                "oc_runipd",
                self.frozen(
                    "oc_runipd",
                    [],
                    {"schema_version": 2, "defaults": {"validate": True}},
                ),
            )
        )
        self.assertFalse(
            self.verifies(
                "agy_runipd",
                self.frozen(
                    "agy_runipd",
                    [],
                    {"schema_version": 2, "defaults": {"validate": False}},
                ),
            )
        )

        # Tier 4: absence yields host row
        self.assertFalse(self.verifies("oc_runipd", self.frozen("oc_runipd", [], None)))
        self.assertTrue(
            self.verifies("agy_runipd", self.frozen("agy_runipd", [], None))
        )

    def test_verification_tristate_and_provenance_recording(self):
        for runner, host, row_default in (
            ("oc_runipd", "oc", False),
            ("agy_runipd", "agy", True),
        ):
            with self.subTest(runner=runner):
                omitted = {
                    "schema_version": 2,
                    "profiles": {"p": {"runner": host, "model": "v/m"}},
                    "defaults": {"profiles": {host: "p"}},
                }
                self.assertIs(
                    self.verifies(runner, self.frozen(runner, [], omitted)), row_default
                )
                present_false = {
                    "schema_version": 2,
                    "profiles": {
                        "p": {"runner": host, "model": "v/m", "validate": False}
                    },
                    "defaults": {"profiles": {host: "p"}},
                }
                self.assertFalse(
                    self.verifies(runner, self.frozen(runner, [], present_false))
                )

        explicit = self.frozen("oc_runipd", ["--validate"], None)["launch_profile"]
        self.assertIs(explicit["validate"], True)
        self.assertEqual(explicit["provenance"]["validate"], "explicit")
        configured = self.frozen(
            "oc_runipd", [], {"schema_version": 2, "defaults": {"validate": True}}
        )["launch_profile"]
        self.assertIs(configured["validate"], True)
        self.assertEqual(configured["provenance"]["validate"], "defaults")
        self.assertNotIn("launch_profile", self.frozen("agy_runipd", [], None))


class AgyVerificationFlagSurfaceTests(unittest.TestCase):
    """`hostdefault-02` (`ybkmzp`) E-02: the tri-state spelling, and the two silent-bypass traps."""

    def parse(self, argv: list):
        return agy_runipd.build_parser().parse_args(
            ["start", "demo", "--repo", ".", *argv]
        )

    def test_tristate_parsing_options_and_distinct_flags(self):
        import argparse as _argparse

        cases = {
            (): (None, False),
            ("--validate",): (True, False),
            ("--no-validate",): (False, False),
            ("--no-verify",): (None, True),
            ("--no-audit",): (None, True),
        }
        for argv, (validate, no_verify) in cases.items():
            with self.subTest(argv=argv):
                args = self.parse(list(argv))
                self.assertIs(args.validate, validate)
                self.assertIs(getattr(args, "no_verify", "<gone>"), no_verify)

        parser = agy_runipd.build_parser()
        self.assertIsNotNone(parser)
        start = None
        for action in parser._actions:
            if isinstance(action, _argparse._SubParsersAction):
                start = action.choices.get("start")
        assert start is not None
        options = {opt for a in start._actions for opt in a.option_strings}
        for expected in ("--validate", "--no-validate", "--no-verify", "--no-audit"):
            self.assertIn(expected, options)

        # distinct flags check
        good = _argparse.ArgumentParser()
        good.add_argument(
            "--no-verify", "--no-audit", dest="no_verify", action="store_true"
        )
        good.add_argument(
            "--validate",
            dest="validate",
            action=_argparse.BooleanOptionalAction,
            default=None,
        )
        agy_runipd.assert_verification_flags_are_distinct(good)

        stolen = _argparse.ArgumentParser(conflict_handler="resolve")
        stolen.add_argument(
            "--no-verify", "--no-audit", dest="no_verify", action="store_true"
        )
        stolen.add_argument(
            "--validate",
            "--verify",
            "--audit",
            dest="validate",
            action=_argparse.BooleanOptionalAction,
            default=None,
        )
        with self.assertRaises(runner_shared.DriverError) as ctx:
            agy_runipd.assert_verification_flags_are_distinct(stolen)
        self.assertIn("--no-verify", str(ctx.exception))

    def test_contradictory_flag_refusal_and_partial_namespace(self):
        import argparse as _argparse
        import os
        from unittest import mock

        args = self.parse(["--no-verify", "--validate"])
        self.assertIs(args.validate, True)
        self.assertIs(args.no_verify, True)
        with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
            agy_runipd.verification_flag_tristate(args)
        self.assertIn("contradict", str(ctx.exception))

        agreeing = self.parse(["--no-verify", "--no-validate"])
        self.assertIs(agy_runipd.verification_flag_tristate(agreeing), False)
        self.assertIsNone(
            agy_runipd.verification_flag_tristate(_argparse.Namespace(validate=None))
        )

        probe = VerificationPolarityTests(
            "test_verification_polarity_matrix_and_agreement"
        )
        with tempfile.TemporaryDirectory() as home:
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": home}, clear=False):
                with tempfile.TemporaryDirectory() as td:
                    repo = probe.make_repo(pathlib.Path(td))
                    args = agy_runipd.build_parser().parse_args(
                        [
                            "start",
                            "pol001",
                            "--repo",
                            str(repo),
                            "--no-verify",
                            "--validate",
                        ]
                    )
                    args.prepare_only = True
                    with self.assertRaises(runner_shared.RunFlagRefusal):
                        agy_runipd.initialize_run(args)
                    runs = repo / ".aw" / "records" / "runs"
                    self.assertEqual(
                        list(runs.glob("run-*")) if runs.exists() else [],
                        [],
                    )


class IntegrationDeferralLadderTests(unittest.TestCase):
    """integpath-03 (`51vw4y`) E-06: EVERY rung transition, pinned deterministically.

    WHAT THIS CLASS EXISTS TO PREVENT, stated because a green suite already coexisted with the defect
    once. `integration_deferred` has appeared in both runners as a DIAGNOSTIC REASON STRING since
    `driverfin-03` while the status still went terminal, so grepping the name proved nothing about
    whether a deferral was ever re-attempted. The assertions below therefore drive the DECISION and the
    STATUS, never the presence of a string.

    NOTHING HERE DEPENDS ON A REAL CONCURRENT WRITER OR ON WALL-CLOCK SLEEPING. `decide_integration_deferral`
    is pure; the poll takes injected `sleep`/`overlap`/`activity_age` callables; the ask takes an
    injected prompt. So time and dirt are controlled inputs, which is what makes these tests fast and
    non-flaky rather than "usually passing".
    """

    def decide(self, **kw):
        base: dict = {
            "integ_kind": runner_shared.INTEGRATION_REFUSAL_TRANSIENT,
            "attempts_used": 1,
            "limit": 10,
        }
        base.update(kw)
        return runner_shared.decide_integration_deferral(**base)

    # ---- rung 1: defer, re-attempt, and the budget ------------------------------------------------

    def test_decide_integration_deferral_semantics_and_limits(self):
        decision = self.decide()
        self.assertTrue(decision.deferred)
        self.assertEqual(decision.status, runner_shared.INTEGRATION_DEFERRED_STATUS)
        for module in (oc_runipd, agy_runipd):
            self.assertNotIn(decision.status, module.TERMINAL_STATES)

        for attempt in range(1, 4):
            self.assertTrue(self.decide(attempts_used=attempt, limit=3).deferred)
        exhausted = self.decide(attempts_used=4, limit=3)
        self.assertFalse(exhausted.deferred)
        self.assertEqual(exhausted.status, runner_shared.INTEGRATION_BLOCKED_STATUS)
        self.assertIn("budget exhausted", exhausted.reason)
        for module in (oc_runipd, agy_runipd):
            self.assertIn(exhausted.status, module.TERMINAL_STATES)

        # Zero limit
        self.assertFalse(self.decide(attempts_used=1, limit=0).deferred)

        # Override choices and policy
        self.assertEqual(
            runner_shared.resolve_on_integration_blocked(None),
            runner_shared.ON_INTEGRATION_BLOCKED_DEFER,
        )
        for good in runner_shared.ON_INTEGRATION_BLOCKED_CHOICES:
            self.assertEqual(runner_shared.resolve_on_integration_blocked(good), good)
        with self.assertRaises(runner_shared.RunFlagRefusal):
            runner_shared.resolve_on_integration_blocked("sometimes")

        block_decision = self.decide(policy=runner_shared.ON_INTEGRATION_BLOCKED_BLOCK)
        self.assertFalse(block_decision.deferred)
        self.assertEqual(
            block_decision.status, runner_shared.INTEGRATION_BLOCKED_STATUS
        )

        # Unrecognized kind fails closed
        self.assertFalse(runner_shared.classify_integration_refusal("something-new"))
        self.assertFalse(self.decide(integ_kind="something-new").deferred)

    def test_merge_conflict_terminal_and_budget_independence(self):
        decision = self.decide(
            integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT, attempts_used=1
        )
        self.assertFalse(decision.deferred)
        self.assertEqual(decision.status, "merge-refused")
        self.assertIn("terminal on its first attempt", decision.reason)
        self.assertFalse(
            runner_shared.classify_integration_refusal(
                runner_shared.INTEGRATION_REFUSAL_CONFLICT
            )
        )
        self.assertFalse(
            self.decide(
                integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT,
                attempts_used=1,
                limit=1000,
            ).deferred
        )

        from agent_workflows import run_recovery

        self.assertEqual(run_recovery.DEFAULT_RETRY_LIMIT, 2)
        self.assertEqual(runner_shared.DEFAULT_INTEGRATION_RETRY_LIMIT, 10)
        self.assertEqual(runner_shared.resolve_integration_retry_limit(None), 10)
        self.assertEqual(runner_shared.resolve_integration_retry_limit(7), 7)
        self.assertEqual(runner_shared.resolve_integration_retry_limit(25), 25)
        with self.assertRaises(runner_shared.RunFlagRefusal):
            runner_shared.resolve_integration_retry_limit(-1)

        self.assertEqual(runner_shared.resolve_retry_budget(0), 0)
        self.assertEqual(runner_shared.resolve_integration_retry_limit(9), 9)
        self.assertTrue(self.decide(attempts_used=3, limit=9).deferred)

    # ---- the 2026-09-21 rename, and its back-compatibility guarantee (`l2mzxn`) ------------------

    def test_the_status_vocabulary_and_legacy_aliases(self):
        self.assertEqual(runner_shared.INTEGRATION_DEFERRED_STATUS, "merge-retry")
        self.assertEqual(runner_shared.INTEGRATION_BLOCKED_STATUS, "merge-needs-human")
        self.assertEqual(runner_shared.INTEGRATION_REFUSAL_CONFLICT, "merge-refused")
        self.assertEqual(
            runner_shared.INTEGRATION_REFUSAL_UNMEASURED, "merge-unchecked"
        )
        self.assertEqual(
            runner_shared.INTEGRATION_REFUSAL_TRANSIENT,
            runner_shared.INTEGRATION_DEFERRED_STATUS,
        )
        expected_aliases = {
            "integration-deferred": "merge-retry",
            "integration-blocked": "merge-needs-human",
            "merge-conflict": "merge-refused",
            "integration-unmeasured": "merge-unchecked",
        }
        self.assertEqual(
            runner_shared.LEGACY_INTEGRATION_STATUS_ALIASES, expected_aliases
        )
        for legacy, canonical in expected_aliases.items():
            self.assertEqual(
                runner_shared.canonical_integration_status(legacy), canonical
            )
            self.assertEqual(
                runner_shared.canonical_integration_status(canonical), canonical
            )

        for untouched in (
            "executed",
            "queued",
            "dependency-blocked",
            "interrupted",
            "",
        ):
            self.assertEqual(
                runner_shared.canonical_integration_status(untouched), untouched
            )
        self.assertEqual(runner_shared.canonical_integration_status(None), "")
        self.assertEqual(runner_shared.canonical_integration_status(17), "")

        for spelling in (
            "merge-needs-human",
            "merge-refused",
            "integration-blocked",
            "merge-conflict",
        ):
            self.assertIn(spelling, runner_shared.REINTEGRATABLE_STATUSES)
        for spelling in ("merge-retry", "merge-unchecked", "integration-deferred"):
            self.assertNotIn(spelling, runner_shared.REINTEGRATABLE_STATUSES)

        for terminal in (
            "merge-needs-human",
            "merge-refused",
            "integration-blocked",
            "merge-conflict",
        ):
            self.assertIn(terminal, runner_shared.TERMINAL_STATES)
        for non_terminal in ("merge-retry", "merge-unchecked", "integration-deferred"):
            self.assertNotIn(non_terminal, runner_shared.TERMINAL_STATES)

        from agent_workflows import lifecycle_style

        for (
            legacy,
            canonical,
        ) in runner_shared.LEGACY_INTEGRATION_STATUS_ALIASES.items():
            legacy_stage = lifecycle_style.resolve(
                lifecycle_style.FAMILY_RUNNER_ITEM, legacy
            ).stage
            canonical_stage = lifecycle_style.resolve(
                lifecycle_style.FAMILY_RUNNER_ITEM, canonical
            ).stage
            self.assertEqual(legacy_stage, canonical_stage)
            self.assertNotEqual(legacy_stage, lifecycle_style.UNKNOWN)

    # ---- rung 2: BOTH bounds, asserted SEPARATELY -------------------------------------------------

    def poll(self, *, dirty, ages, poll_limit=10, staleness=3600.0):
        slept: list = []
        seq_dirty = list(dirty)
        seq_ages = list(ages)

        def _overlap(_repo, _files):
            return seq_dirty.pop(0) if seq_dirty else []

        def _age(_repo):
            return seq_ages.pop(0) if seq_ages else 0.0

        outcome = runner_shared.poll_for_integration_window(
            pathlib.Path("/nonexistent"),
            ("src/x.py",),
            poll_limit=poll_limit,
            interval=0.0,
            staleness_limit=staleness,
            sleep=slept.append,
            overlap=_overlap,
            activity_age=_age,
        )
        return outcome, slept

    def test_poll_ladder_bounds_and_dirt_clearing(self):
        # Bound I: poll count
        outcome, slept = self.poll(
            dirty=[["src/x.py"]] * 40, ages=[60.0] * 40, poll_limit=3
        )
        self.assertFalse(outcome.cleared)
        self.assertEqual(outcome.bound, runner_shared.POLL_BOUND_COUNT)
        self.assertEqual(outcome.polls, 3)
        self.assertEqual(len(slept), 3)

        # Bound II: stale main
        outcome_stale, slept_stale = self.poll(
            dirty=[["src/x.py"]] * 40, ages=[4 * 3600.0] * 40, poll_limit=25
        )
        self.assertFalse(outcome_stale.cleared)
        self.assertEqual(outcome_stale.bound, runner_shared.POLL_BOUND_STALE)
        self.assertEqual(outcome_stale.polls, 0)
        self.assertEqual(slept_stale, [])

        # Dirt clears
        outcome_clear, slept_clear = self.poll(
            dirty=[["src/x.py"], ["src/x.py"], []], ages=[10.0] * 5
        )
        self.assertTrue(outcome_clear.cleared)
        self.assertEqual(outcome_clear.bound, runner_shared.POLL_BOUND_CLEARED)
        self.assertEqual(outcome_clear.polls, 2)
        self.assertEqual(len(slept_clear), 2)

        # Unmeasurable main
        outcome_unmeas, slept_unmeas = self.poll(dirty=[["x"]] * 5, ages=[None] * 5)
        self.assertEqual(outcome_unmeas.bound, runner_shared.POLL_BOUND_STALE)
        self.assertEqual(slept_unmeas, [])

    def test_main_last_activity_is_the_NEWER_of_head_time_and_dirty_mtime(self):
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            repo.mkdir()
            for cmd in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "t@example.invalid"],
                ["git", "config", "user.name", "T"],
            ):
                subprocess.run(cmd, cwd=repo, check=True)
            (repo / "a.txt").write_text("a\n", encoding="utf-8")
            subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

            committed_age = runner_shared.main_last_activity_age(repo)
            self.assertIsNotNone(committed_age)
            assert committed_age is not None
            self.assertLess(committed_age, 120.0)

            (repo / "b.txt").write_text("dirty\n", encoding="utf-8")
            age = runner_shared.main_last_activity_age(
                repo, now=__import__("time").time()
            )
            self.assertIsNotNone(age)
            assert age is not None
            self.assertLess(age, 120.0)

    # ---- rung 3: the ask, which must never hang ---------------------------------------------------

    def test_interactive_ask_behavior_and_prompt_predicate(self):
        import argparse

        # Unattended suppresses ask
        unattended_out = runner_shared.ask_operator_about_integration(
            "aaa111",
            "dirty overlap",
            interactive=False,
            prompt=lambda *a, **k: self.fail("must not prompt"),
        )
        self.assertFalse(unattended_out.asked)
        self.assertFalse(unattended_out.retry)

        # Timeout falls through to terminal
        timeout_out = runner_shared.ask_operator_about_integration(
            "aaa111", "dirty overlap", interactive=True, prompt=lambda *a, **k: None
        )
        self.assertTrue(timeout_out.asked)
        self.assertFalse(timeout_out.retry)

        # Affirmative and refusal
        yes = runner_shared.ask_operator_about_integration(
            "aaa111", "r", interactive=True, prompt=lambda *a, **k: "y\n"
        )
        self.assertTrue(yes.retry)
        for answer in ("n\n", "\n", "later\n"):
            self.assertFalse(
                runner_shared.ask_operator_about_integration(
                    "aaa111", "r", interactive=True, prompt=lambda *a, **k: answer
                ).retry
            )

        class _TTY:
            def isatty(self):
                return True

        self.assertFalse(
            runner_shared.is_interactive_run(
                argparse.Namespace(unattended=True, full_auto=False), stream=_TTY()
            )
        )
        with mock.patch.object(runner_shared.sys, "stdin", _TTY()):
            self.assertTrue(
                runner_shared.is_interactive_run(
                    argparse.Namespace(unattended=False, full_auto=False), stream=_TTY()
                )
            )

    # ---- OQ-03: resolution, dependencies, and cascade ---------------------------------------------

    def test_exhausted_deferrals_resolution(self):
        events: list = []
        saved: list = []
        state = {
            "queue": [
                {
                    "id6": "aaa111",
                    "setid": "s",
                    "status": runner_shared.INTEGRATION_DEFERRED_STATUS,
                    "preserved_branch": "aw/lane/aaa111",
                    "integration_deferral": "dirty overlap on src/x.py",
                    "attempts": [{}],
                }
            ]
        }
        resolved = runner_shared.resolve_exhausted_deferrals(
            pathlib.Path("/nonexistent"),
            state,
            save_state=lambda *a, **k: saved.append(a),
            append_jsonl=lambda _p, e: events.append(e),
        )
        self.assertEqual(resolved, ["aaa111"])
        item = state["queue"][0]
        self.assertEqual(item["status"], runner_shared.INTEGRATION_BLOCKED_STATUS)
        self.assertEqual(item["preserved_branch"], "aw/lane/aaa111")
        self.assertEqual(events[0]["event"], "ipd-integration-blocked")
        self.assertTrue(saved)

        # Nothing resolved when no item is deferred
        state_executed = {"queue": [{"id6": "aaa111", "status": "executed"}]}
        self.assertEqual(
            runner_shared.resolve_exhausted_deferrals(
                pathlib.Path("/nonexistent"),
                state_executed,
                save_state=lambda *a, **k: self.fail("must not persist"),
                append_jsonl=lambda *a, **k: self.fail("must not emit"),
            ),
            [],
        )

    def test_deferred_item_dependency_cascade_and_reconcile(self):
        state = {
            "repo": ".",
            "queue": [
                {
                    "id6": "aaa111",
                    "status": runner_shared.INTEGRATION_DEFERRED_STATUS,
                    "setid": "s",
                    "action": "execute",
                    "position": 1,
                    "dependencies": [],
                },
                {
                    "id6": "bbb222",
                    "status": "queued",
                    "setid": "s",
                    "action": "execute",
                    "position": 2,
                    "dependencies": ["executed:aaa111"],
                },
            ],
        }
        for module in (oc_runipd, agy_runipd):
            satisfied, unsatisfied = module.dependency_status(state["queue"][1], state)
            self.assertFalse(satisfied)
            self.assertEqual(unsatisfied, ["executed:aaa111"])

            self.assertEqual(module.cascade_dependency_blocked(state), [])
            self.assertEqual(state["queue"][1]["status"], "queued")

        # Terminal non-success prerequisite still cascades
        state["queue"][0]["status"] = "merge-needs-human"
        self.assertTrue(oc_runipd.cascade_dependency_blocked(state))
        self.assertEqual(state["queue"][1]["status"], "dependency-blocked")

        # Reconcile disposition passes deferral through
        for module in (oc_runipd, agy_runipd):
            with tempfile.TemporaryDirectory() as td:
                run_dir = pathlib.Path(td) / "run"
                (run_dir / "outcomes").mkdir(parents=True)
                item = {
                    "id6": "aaa111",
                    "position": 1,
                    "configured_file": "",
                    "action": "execute",
                    "status": runner_shared.INTEGRATION_DEFERRED_STATUS,
                }
                disposition, _outcome = module.reconcile_disposition(
                    pathlib.Path(td), item, run_dir, 0
                )
                self.assertEqual(disposition, runner_shared.INTEGRATION_DEFERRED_STATUS)

        from agent_workflows import runner_shutdown

        self.assertIn(
            runner_shared.INTEGRATION_DEFERRED_STATUS,
            runner_shutdown.KNOWN_ITEM_STATUSES,
        )

    # ---- dispatch loop & retry incomplete --------------------------------------------------------

    @staticmethod
    def _dispatch_repo(root: pathlib.Path) -> pathlib.Path:
        import subprocess

        repo = root / "repo"
        repo.mkdir(parents=True)
        for cmd in (
            ["git", "init", "-q", "-b", "main"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=repo, check=True)
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo

    @classmethod
    def _dispatch_run(
        cls, root: pathlib.Path, repo: pathlib.Path, statuses: tuple[str, ...]
    ) -> pathlib.Path:
        run_dir = root / "run-dispatch"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "state.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "run_id": "run-dispatch",
                    "repo": str(repo),
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                    "selectors": ["s"],
                    "options": {},
                    "set_sessions": {},
                    "queue": [
                        {
                            "position": index + 1,
                            "id6": "aaa{0}".format(111 * (index + 1)),
                            "setid": "s",
                            "action": "execute",
                            "kind": "child",
                            "status": status,
                            "dependencies": [],
                            "attempts": [{}],
                            "configured_file": "",
                        }
                        for index, status in enumerate(statuses)
                    ],
                }
            ),
            encoding="utf-8",
        )
        return run_dir

    def test_retry_incomplete_and_dispatch_reaches_ladder(self):
        for module in (oc_runipd, agy_runipd):
            turns: list = []

            def _fake_execute(
                run_dir, state, item, *_a, _log=turns, _host=module, **_k
            ):
                _log.append((item.get("id6"), item.get("requeue_from_status")))
                item["status"] = "executed"
                _host.save_state(run_dir, state)

            with tempfile.TemporaryDirectory() as td:
                root = pathlib.Path(td)
                repo = self._dispatch_repo(root)
                run_dir = self._dispatch_run(
                    root, repo, (runner_shared.INTEGRATION_DEFERRED_STATUS,)
                )
                with (
                    mock.patch.object(module, "execute_item", _fake_execute),
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    module.run_queue(run_dir, retry_incomplete=True)
                final = runner_shared.load_state(run_dir)["queue"][0]
                self.assertEqual(len(turns), 1)
                self.assertEqual(turns[0][1], runner_shared.INTEGRATION_DEFERRED_STATUS)
                self.assertEqual(final["status"], "executed")


# --------------------------------------------------------------------------------------------------
# lanestrand-01 (`pr5b0t`) E-07: the stranded-lane predicate, proven in BOTH directions
# --------------------------------------------------------------------------------------------------


def _git(repo: pathlib.Path, *args: str) -> str:
    import subprocess

    proc = subprocess.run(
        ["git", *args], cwd=str(repo), text=True, capture_output=True, check=True
    )
    return proc.stdout.strip()


def _make_lane_fixture_repo(root: pathlib.Path) -> pathlib.Path:
    """A throwaway repo on `main` with one commit. FIXTURES ONLY: never a real lane.

    The plan's execution contract is explicit that this repository holds dozens of live `aw/lane/*`
    branches and several in-repo lane worktrees, and that a test touching one could destroy the very
    unintegrated work this predicate exists to protect.
    """
    import subprocess

    repo = root / "repo"
    repo.mkdir(parents=True)
    for cmd in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "config", "user.email", "test@example.invalid"],
        ["git", "config", "user.name", "Test"],
    ):
        subprocess.run(cmd, cwd=repo, check=True)
    (repo / "f.txt").write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    return repo


def _add_lane(
    repo: pathlib.Path, lane_dir: pathlib.Path, lane_id: str, *, commit: bool = True
) -> dict:
    """Create a lane THE WAY THE RUNNER CREATES ONE: `git worktree add -b aw/lane/<id> <path> <base>`.

    THE CONSTRUCTION IS LOAD-BEARING AND NOT INTERCHANGEABLE WITH `git branch`. `inspect_lane` reads
    the lane's own base from the branch CREATION REFLOG entry (`worktree_lease._lane_base_sha`), so a
    fixture built with a bare `git branch <name> <other-branch-name>` writes a different creation entry
    and can make `commits_ahead` read 0 for the wrong reason: the test would then pass while the
    predicate stayed broken. `allocate_worktree` uses `worktree add -b`, so this matches it.
    """
    import subprocess

    base = _git(repo, "rev-parse", "HEAD")
    branch = "aw/lane/{0}".format(lane_id)
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", branch, str(lane_dir), base],
        cwd=repo,
        check=True,
    )
    if commit:
        (lane_dir / "{0}.txt".format(lane_id)).write_text("work\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=lane_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "lane work"], cwd=lane_dir, check=True)
    return {
        "worktree": str(lane_dir),
        "branch": branch,
        "lane_id": lane_id,
        "base_commit": base,
        "disposition": "created",
        "id6": lane_id,
        "status": "substantially-complete",
    }


def _state_for(repo: pathlib.Path, lanes: list, run_id: str = "run-fixture") -> dict:
    """A minimal run `state.json` shaped like the real one: the `preserved_*` fields on each item."""
    queue = []
    for lane in lanes:
        queue.append(
            {
                "id6": lane["id6"],
                "position": len(queue) + 1,
                "status": lane.get("status", "substantially-complete"),
                "preserved_worktree": lane["worktree"],
                "preserved_branch": lane["branch"],
                "preserved_lane_id": lane["lane_id"],
                "preserved_base": lane["base_commit"],
                "preserved_disposition": lane["disposition"],
                "preserved_reason": "the run ended without integrating this lane",
                "integration_signal": lane.get("integration_signal", "suite-failed"),
                "attempts": [
                    {
                        "worktree": lane["worktree"],
                        "worktree_branch": lane["branch"],
                        "worktree_lane_id": lane["lane_id"],
                        "worktree_base": lane["base_commit"],
                        "integration_detail": "gate refused in {0}".format(repo),
                    }
                ],
            }
        )
    return {"run_id": run_id, "repo": str(repo), "queue": queue}


class StrandedLanePredicateTests(unittest.TestCase):
    """Both directions of the predicate. A false positive here destroys the alarm's value."""

    def test_classify_lane_integration_states(self):
        from agent_workflows import worktree_lease

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)

            # Unmerged work is stranded
            lane = _add_lane(repo, root / "lane01", "lane01")
            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(rec["lane_state"], runner_shared.LANE_STRANDED)
            self.assertIs(rec["landed"], False)
            self.assertTrue(rec["needs_attention"])
            self.assertEqual(rec["commits_ahead"], 1)

            # Empty lane
            lane_empty = _add_lane(
                repo, root / "lane_empty", "lane_empty", commit=False
            )
            rec_empty = runner_shared.classify_lane_integration(
                repo, lane_empty, target="main"
            )
            self.assertEqual(rec_empty["lane_state"], runner_shared.LANE_EMPTY_OF_WORK)
            self.assertFalse(rec_empty["needs_attention"])

            # Owned by live process
            with mock.patch.object(
                worktree_lease, "lane_owned_by_other_live_process", return_value=True
            ):
                rec_live = runner_shared.classify_lane_integration(
                    repo, lane, target="main"
                )
            self.assertEqual(rec_live["lane_state"], runner_shared.LANE_LIVE)
            self.assertFalse(rec_live["needs_attention"])

            # Ghost branch is empty
            ghost = dict(
                lane, branch="aw/lane/ghost99", lane_id="ghost99", id6="ghost99"
            )
            self.assertIsNone(
                runner_shared.lane_work_has_landed(repo, ghost["branch"], target="main")
            )
            self.assertEqual(
                runner_shared.classify_lane_integration(repo, ghost, target="main")[
                    "lane_state"
                ],
                runner_shared.LANE_EMPTY_OF_WORK,
            )

            # Unresolvable target is unknown
            rec_unk = runner_shared.classify_lane_integration(
                repo, lane, target="refs/heads/no-such-target"
            )
            self.assertEqual(rec_unk["lane_state"], runner_shared.LANE_UNKNOWN)
            self.assertTrue(rec_unk["needs_attention"])

    def test_a_MERGED_lane_is_NOT_stranded_and_holds_work_alone_would_get_it_WRONG(
        self,
    ):
        import subprocess

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")

            before = runner_shared.describe_lane(repo, lane)
            before_landed = runner_shared.lane_work_has_landed(
                repo, lane["branch"], target="main"
            )
            subprocess.run(
                [
                    "git",
                    "merge",
                    "--no-ff",
                    "--no-edit",
                    "-m",
                    "integrate lane01",
                    lane["branch"],
                ],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            after = runner_shared.describe_lane(repo, lane)
            after_landed = runner_shared.lane_work_has_landed(
                repo, lane["branch"], target="main"
            )

            self.assertTrue(before["holds_work"])
            self.assertTrue(after["holds_work"])
            self.assertIs(before_landed, False)
            self.assertIs(after_landed, True)

            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(rec["lane_state"], runner_shared.LANE_LANDED)
            self.assertFalse(rec["needs_attention"])

    def test_records_and_worktree_display(self):
        import subprocess

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            state = _state_for(repo, [lane])

            stranded = runner_shared.stranded_lane_records(repo, [state], target="main")
            self.assertEqual(len(stranded), 1)
            self.assertEqual(stranded[0]["branch"], "aw/lane/lane01")

            subprocess.run(
                [
                    "git",
                    "merge",
                    "--no-ff",
                    "--no-edit",
                    "-m",
                    "integrate",
                    lane["branch"],
                ],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            self.assertEqual(
                runner_shared.stranded_lane_records(repo, [state], target="main"), []
            )

            inside = repo / ".aw" / "worktrees" / "lane01"
            inside.mkdir(parents=True)
            self.assertEqual(
                runner_shared.lane_worktree_display(repo, str(inside)),
                ".aw/worktrees/lane01",
            )
            self.assertIsNone(runner_shared.lane_worktree_display(repo, None))

    def test_attention_stranded_lane_drift_delegates_to_shared_records(self):
        from agent_workflows import attention

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            _advance_main(repo)
            run_dir = runner_shared.state_root(repo) / "run-fixture"
            run_dir.mkdir(parents=True)
            (run_dir / "state.json").write_text(
                json.dumps(_state_for(repo, [lane])), encoding="utf-8"
            )

            real = attention.stranded_lane_drift(repo)
            self.assertEqual([rec.location for rec in real], [lane["branch"]])

            sentinel_branch = "aw/lane/SENTINEL-not-a-real-lane"
            with mock.patch.object(
                runner_shared,
                "stranded_lane_records",
                lambda *a, **k: [
                    {
                        "branch": sentinel_branch,
                        "lane_state": runner_shared.LANE_STRANDED,
                        "id6": "sent01",
                        "commits_ahead": 7,
                        "dirty": False,
                    }
                ],
            ):
                observed = [rec.location for rec in attention.stranded_lane_drift(repo)]
            self.assertEqual(observed, [sentinel_branch])


# ==================================================================================================
# stranrep-01 (`0ta5vg`): THE CONTENT-LANDED READING, ONE ROW PER LANE, AND NO PHANTOM WORKTREE
# ==================================================================================================


def _advance_main(repo: pathlib.Path, name: str = "independent") -> None:
    """Put an INDEPENDENT commit on main, which is what makes a cherry-pick produce a DIFFERENT sha.

    LOAD-BEARING, NOT DECORATION. Cherry-picking a lane commit onto an UNADVANCED main reproduces the
    IDENTICAL sha, which makes the lane an ancestor and proves nothing about the content reading: the
    ancestry reading would already have answered True. Advancing main first is what creates the shape
    this reading exists for.
    """
    import subprocess

    (repo / "{0}.txt".format(name)).write_text("main moves\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "main: {0}".format(name)], cwd=repo, check=True
    )


def _cherry_pick_onto_main(repo: pathlib.Path, rev: str) -> None:
    import subprocess

    subprocess.run(
        ["git", "cherry-pick", "-x", rev], cwd=repo, check=True, capture_output=True
    )


class SupersededLaneTests(unittest.TestCase):
    """A lane whose PLAN went terminal is SUPERSEDED, not STRANDED, and must not fail the gate.

    THE MEASURED DEFECT, 2026-09-22. Thirteen lanes reported `STRANDED`; TEN held nothing recoverable,
    because a LATER attempt redid the work and landed it, leaving the first lane a husk. Neither
    existing reading can see that: ancestry says no (the lane's commits are not ancestors of the
    target) and patch id says no (the second attempt wrote different bytes), and `git cherry` agreed,
    reporting every commit absent upstream even where the feature was demonstrably live and tested.
    The board therefore sat at `VIEW INVALID` on work that HAD landed, which is the failure mode that
    teaches an operator to stop reading the gate and so lets the NEXT real stranding through.

    A NOTE ON THE EVIDENCE, because I got it wrong first. While triaging I "proved" supersession by
    comparing symbol sets between the lane and the target, and that reasoning is INVALID: a second
    attempt legitimately restructures names, so a symbol present in the lane and absent from the
    target proves nothing at all. The signal these tests pin is the LIFECYCLE RECORD (the plan reached
    a terminal directory), which is a durable git-visible fact rather than an inference about code.
    """

    def _plan(self, repo: pathlib.Path, id6: str, bucket: str) -> None:
        """Write a minimal plan for ``id6`` into ``bucket`` and commit it."""
        d = repo / ".aw" / "records" / "plans" / bucket
        d.mkdir(parents=True, exist_ok=True)
        (d / "20260101-set-01-{0}-slug.ipd.md".format(id6)).write_text(
            "# IPD: probe\n\n- Id: {0}\n- Status: executed\n".format(id6),
            encoding="utf-8",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "plan {0} in {1}".format(id6, bucket))

    def test_a_lane_whose_plan_is_EXECUTED_is_superseded_not_stranded(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            self._plan(repo, "aaa111", "executed")
            lane = _add_lane(repo, root / "lane01", "lane01")
            lane["id6"] = "aaa111"
            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(
                rec["lane_state"],
                runner_shared.LANE_SUPERSEDED,
                "a lane whose plan reached a terminal directory holds nothing at risk; calling it "
                "STRANDED is what held the board invalid on ten landed lanes",
            )
            self.assertIs(
                rec["landed"],
                False,
                "`landed` describes THIS branch and must stay False: its own commits really did not "
                "reach the target. Overwriting it would be a false claim about the branch",
            )
            self.assertTrue(
                rec["needs_attention"],
                "it must still be REPORTED: the lane exists, holds commits and occupies a worktree, "
                "so an operator should see it and prune it",
            )

    def test_a_lane_whose_plan_is_still_PENDING_stays_stranded(self):
        """The direction that must NOT move: real unlanded work keeps its alarm."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            self._plan(repo, "bbb222", "pending")
            lane = _add_lane(repo, root / "lane01", "lane01")
            lane["id6"] = "bbb222"
            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(rec["lane_state"], runner_shared.LANE_STRANDED)
            self.assertIs(rec["landed"], False)

    def test_an_UNRESOLVABLE_plan_stays_stranded_fail_closed(self):
        """The fail-closed arm: an unreadable record must never buy a lane an exemption."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            lane["id6"] = "nosuch"  # no plan file anywhere
            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(
                rec["lane_state"],
                runner_shared.LANE_STRANDED,
                "an unresolvable plan is an UNANSWERED question, not a terminal one; downgrading here "
                "would let an unreadable record silence a real stranding",
            )

    def test_the_predicate_is_three_valued(self):
        """`lane_plan_is_terminal` must distinguish no/yes/unknown, since the caller keys on `is True`."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            self._plan(repo, "ccc333", "executed")
            self._plan(repo, "ddd444", "pending")
            self.assertIs(
                runner_shared.lane_plan_is_terminal(repo, {"id6": "ccc333"}), True
            )
            self.assertIs(
                runner_shared.lane_plan_is_terminal(repo, {"id6": "ddd444"}), False
            )
            self.assertIsNone(
                runner_shared.lane_plan_is_terminal(repo, {"id6": "missin"})
            )
            self.assertIsNone(
                runner_shared.lane_plan_is_terminal(repo, {}),
                "no id6 at all is UNKNOWN, never False",
            )

    def test_superseded_is_reported_but_does_NOT_fail_the_gate(self):
        """The severity split is the whole point: report it, do not red the board for it."""
        from agent_workflows import artifact_core as core
        from agent_workflows import attention

        self.assertEqual(
            attention.lane_drift_severity(runner_shared.LANE_SUPERSEDED), "info"
        )
        self.assertEqual(
            attention.lane_drift_severity(runner_shared.LANE_STRANDED), "error"
        )
        self.assertEqual(
            attention.lane_drift_severity(runner_shared.LANE_UNKNOWN),
            "error",
            "an unanswerable landing question is not evidence the work landed",
        )
        # And the exit convention must actually exempt it, or the split is cosmetic.
        self.assertEqual(
            core.drift_exit_code(
                [core.Drift("l", attention.LANE_SUPERSEDED_RULE, "d", severity="info")]
            ),
            0,
        )
        self.assertEqual(
            core.drift_exit_code(
                [core.Drift("l", attention.LANE_STRANDED_RULE, "d", severity="error")]
            ),
            1,
        )

    def test_superseded_gets_its_OWN_rule_id(self):
        """A consumer keying on the stranded rule must not start matching lanes with nothing at risk."""
        from agent_workflows import attention

        self.assertNotEqual(
            attention.LANE_SUPERSEDED_RULE, attention.LANE_STRANDED_RULE
        )
        self.assertEqual(attention.LANE_SUPERSEDED_RULE, "attention.lane-superseded")


class ContentLandedReadingTests(unittest.TestCase):
    """E-01/E-02: patch-id landing, its two parse guards, and the DIRTY lane that must never be silenced.

    EVERY CASE BUILDS ITS OWN TEMPORARY GIT REPOSITORY and passes an explicit repo path. Backlog `no0j8g`
    records four tests that read the developer's own repository and so had live-state-dependent results;
    and this repository holds dozens of real `aw/lane/*` branches whose unintegrated work is exactly what
    this predicate protects.
    """

    def test_a_CHERRY_PICKED_lane_is_landed_by_CONTENT_though_not_by_ancestry(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            lane_tip = _git(root / "lane01", "rev-parse", "HEAD")

            # Main advances INDEPENDENTLY first, so the cherry-pick cannot reproduce the same sha.
            _advance_main(repo)
            _cherry_pick_onto_main(repo, lane_tip)

            # The two readings DISAGREE, which is the whole point of carrying both.
            self.assertIs(
                runner_shared.lane_work_has_landed(repo, lane["branch"], target="main"),
                False,
            )
            self.assertIs(
                runner_shared.lane_work_landed_by_content(
                    repo, lane["branch"], target="main"
                ),
                True,
            )

    def test_a_genuinely_ABSENT_commit_reads_False(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            _advance_main(repo)
            self.assertIs(
                runner_shared.lane_work_landed_by_content(
                    repo, lane["branch"], target="main"
                ),
                False,
            )

    def test_the_PARTIAL_case_reads_False_because_one_commit_is_still_absent(self):
        """A mixed `-`/`+` output must NOT read as landed: the lane still holds work main lacks."""
        import subprocess

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane_dir = root / "lane01"
            lane = _add_lane(repo, lane_dir, "lane01")
            first_tip = _git(lane_dir, "rev-parse", "HEAD")
            (lane_dir / "second.txt").write_text("more\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=lane_dir, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "lane work 2"], cwd=lane_dir, check=True
            )

            _advance_main(repo)
            _cherry_pick_onto_main(repo, first_tip)  # only the FIRST of two

            out = _git(repo, "cherry", "main", lane["branch"])
            self.assertTrue(any(ln.startswith("-") for ln in out.splitlines()))
            self.assertTrue(any(ln.startswith("+") for ln in out.splitlines()))
            self.assertIs(
                runner_shared.lane_work_landed_by_content(
                    repo, lane["branch"], target="main"
                ),
                False,
            )

    def test_EMPTY_output_reads_False_and_NEVER_vacuously_landed(self):
        """Guard (a). `git cherry` exits 0 with no lines, and "every line begins `-`" is vacuously true."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01", commit=False)

            out = _git(repo, "cherry", "main", lane["branch"])
            self.assertEqual(out.strip(), "")
            self.assertIs(
                runner_shared.lane_work_landed_by_content(
                    repo, lane["branch"], target="main"
                ),
                False,
            )

    def test_an_UNRESOLVABLE_ref_reads_None_and_never_False(self):
        """Guard (b). A question we cannot answer must stay UNKNOWN, never read as either answer."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            self.assertIsNone(
                runner_shared.lane_work_landed_by_content(
                    repo, "aw/lane/no-such-branch", target="main"
                )
            )
            self.assertIsNone(
                runner_shared.lane_work_landed_by_content(
                    repo, lane["branch"], target="refs/heads/no-such-target"
                )
            )
            self.assertIsNone(
                runner_shared.lane_work_landed_by_content(repo, "", target="main")
            )

    def test_a_cherry_picked_CLEAN_lane_classifies_LANDED_by_content(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            lane_tip = _git(root / "lane01", "rev-parse", "HEAD")
            _advance_main(repo)
            _cherry_pick_onto_main(repo, lane_tip)

            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(rec["lane_state"], runner_shared.LANE_LANDED)
            self.assertFalse(rec["needs_attention"])
            self.assertFalse(rec["dirty"])
            self.assertEqual(rec["landed_by"], "content")
            self.assertIs(rec["landed"], True)

    def test_a_cherry_picked_DIRTY_lane_STAYS_REPORTABLE_so_uncommitted_work_is_not_lost(
        self,
    ):
        """THE DATA-LOSS GUARD, and the most important case in this class.

        `holds_work` is `commits_ahead > 0 OR dirty`, so a lane whose commits ALL landed by patch id but
        whose tree still holds uncommitted changes reaches the landing question. Patch ids describe
        COMMITS only, so the content reading says nothing about those files. The ancestry-only reading
        ACCIDENTALLY protected them; silencing this lane would remove that protection and lose the file.
        """
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            lane_dir = root / "lane01"
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, lane_dir, "lane01")
            lane_tip = _git(lane_dir, "rev-parse", "HEAD")
            _advance_main(repo)
            _cherry_pick_onto_main(repo, lane_tip)

            # The precious file: uncommitted, and invisible to any patch-id reading.
            (lane_dir / "precious_uncommitted.txt").write_text(
                "not committed anywhere\n", encoding="utf-8"
            )

            # The commits DID land by content...
            self.assertIs(
                runner_shared.lane_work_landed_by_content(
                    repo, lane["branch"], target="main"
                ),
                True,
            )
            # ...and the lane is STILL REPORTED, because its tree is dirty.
            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertTrue(rec["dirty"])
            self.assertTrue(rec["needs_attention"])
            self.assertEqual(rec["lane_state"], runner_shared.LANE_STRANDED)
            self.assertIsNone(rec["landed_by"])
            self.assertTrue((lane_dir / "precious_uncommitted.txt").is_file())

    def test_a_genuinely_unmerged_lane_still_classifies_STRANDED(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            _advance_main(repo)
            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(rec["lane_state"], runner_shared.LANE_STRANDED)
            self.assertTrue(rec["needs_attention"])
            self.assertIsNone(rec["landed_by"])

    def test_an_UNANSWERABLE_content_reading_does_NOT_rescue_a_negative_ancestry(self):
        """FAIL-CLOSED DIRECTION. A false LANDED hides real loss; a false STRANDED only costs a row."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            _advance_main(repo)

            def _unanswerable(*_a: Any, **_k: Any) -> Any:
                return None

            with mock.patch.object(
                runner_shared, "lane_work_landed_by_content", _unanswerable
            ):
                rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertTrue(rec["needs_attention"])
            self.assertEqual(rec["lane_state"], runner_shared.LANE_STRANDED)
            self.assertIsNone(rec["landed_by"])

    # A SOURCE-TEXT PIN WAS DELETED HERE, NOT REPLACED, because a behavioral sibling in this class
    # ALREADY PROVES THE SAME PROPERTY AND PROVES IT BETTER.
    #
    # `test_the_content_reading_is_gated_on_NOT_DIRTY_in_the_source` read
    # `inspect.getsource(classify_lane_integration)` and asserted the literal
    # `'if not described.get("dirty")'` appeared. That is a change-detector three times over: the
    # twenty-line comment block directly above that gate spells the condition out in prose (it exists
    # to stop a later reader deleting the guard), so the pin was satisfiable by the comment with the
    # gate gone; it asserts one SPELLING, so rewriting the same condition as
    # `if described.get("dirty") is not True` fails a test about behavior; and it says nothing about
    # what the gate DOES.
    #
    # `test_a_cherry_picked_DIRTY_lane_STAYS_REPORTABLE_so_uncommitted_work_is_not_lost` above drives
    # the real predicate over a real repository where the lane's commits ALL landed by patch id while
    # its tree still holds an uncommitted file, and asserts the lane is still reported. MEASURED by
    # mutation while removing this pin: deleting the `if not described.get("dirty")` gate from
    # `runner_shared.classify_lane_integration` makes that sibling FAIL with
    # `AssertionError: False is not true` on `rec["needs_attention"]`. So the removal is caught, and it
    # is caught by the consequence (an uncommitted file silently dropped from the report) rather than by
    # a spelling.

    def test_an_ancestor_landed_lane_records_landed_by_ancestor(self):
        import subprocess

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            subprocess.run(
                [
                    "git",
                    "merge",
                    "--no-ff",
                    "--no-edit",
                    "-m",
                    "integrate lane01",
                    lane["branch"],
                ],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(rec["lane_state"], runner_shared.LANE_LANDED)
            self.assertEqual(rec["landed_by"], "ancestor")


class OneRowPerLaneTests(unittest.TestCase):
    """E-04: one lane is one row across runs, WITHOUT losing the within-run collapse or the evidence."""

    def test_a_lane_named_by_THREE_runs_yields_ONE_row_carrying_the_run_count(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            states = [
                _state_for(repo, [lane], run_id="run-20260101T000000Z-1"),
                _state_for(repo, [lane], run_id="run-20260202T000000Z-2"),
                _state_for(repo, [lane], run_id="run-20260303T000000Z-3"),
            ]
            recs = runner_shared.stranded_lane_records(repo, states, target="main")
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["branch"], "aw/lane/lane01")
            self.assertEqual(recs[0]["run_count"], 3)
            # The NEWEST run is the one an operator opens first.
            self.assertEqual(recs[0]["run_id"], "run-20260303T000000Z-3")
            self.assertEqual(len(recs[0]["run_ids"]), 3)

    def test_the_WITHIN_RUN_collapse_SURVIVES_one_lane_named_twice_in_one_run(self):
        """The stage-1 key was CORRECT for its own duplicate and must not be lost to the stage-2 fix.

        One run naming a lane by BOTH an attempt and the item-level `preserved_*` fields must still yield
        exactly ONE record, which is what the original `(run_id, branch, worktree)` key delivered.
        """
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            state = _state_for(repo, [lane], run_id="run-solo")
            recs = runner_shared.stranded_lane_records(repo, [state], target="main")
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["run_count"], 1)
            self.assertEqual(recs[0]["run_id"], "run-solo")

    def test_TWO_DISTINCT_lanes_are_NOT_collapsed_into_one_row(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane_a = _add_lane(repo, root / "lane01", "lane01")
            lane_b = _add_lane(repo, root / "lane02", "lane02")
            state = _state_for(repo, [lane_a, lane_b], run_id="run-both")
            recs = runner_shared.stranded_lane_records(repo, [state], target="main")
            self.assertEqual(len(recs), 2)
            self.assertEqual(
                sorted(r["branch"] for r in recs),
                ["aw/lane/lane01", "aw/lane/lane02"],
            )

    def test_the_retained_row_is_the_MOST_INFORMATIVE_one(self):
        """An `integration_signal` names WHY the lane did not integrate, so it must survive the collapse."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            bare = _state_for(repo, [lane], run_id="run-20260101T000000Z-1")
            for item in bare["queue"]:
                item["integration_signal"] = None
                for attempt in item["attempts"]:
                    attempt["integration_signal"] = None
            rich = _state_for(repo, [lane], run_id="run-20260202T000000Z-2")

            recs = runner_shared.stranded_lane_records(
                repo, [bare, rich], target="main"
            )
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["integration_signal"], "suite-failed")
            self.assertEqual(recs[0]["run_count"], 2)


class LaneWorktreeDisplayExistenceTests(unittest.TestCase):
    """E-05: a row must not assert a directory that is gone, and must still name one that is there."""

    def test_an_ABSENT_worktree_is_OMITTED(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            gone = repo / ".aw" / "worktrees" / "reclaimed"
            self.assertFalse(gone.exists())
            self.assertIsNone(runner_shared.lane_worktree_display(repo, str(gone)))

    def test_an_EXISTING_worktree_still_renders_REPOSITORY_RELATIVE(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            live = repo / ".aw" / "worktrees" / "alive"
            live.mkdir(parents=True)
            self.assertEqual(
                runner_shared.lane_worktree_display(repo, str(live)),
                ".aw/worktrees/alive",
            )

    def test_the_guard_protects_the_SUCCESS_return_not_only_the_reconstruction(self):
        """The intuitive suspect was the except branch, and it was the WRONG one.

        `Path.resolve()` does not require the path to exist, so `relative_to(root)` SUCCEEDS for a
        long-gone directory and the value is returned by the NORMAL path. Measured over the live record
        set: every record carrying a worktree took the success path and none took the except branch.

        A SOURCE-TEXT PIN WAS REMOVED FROM THIS TEST. Its last line read
        `inspect.getsource(runner_shared.lane_worktree_display)` and asserted the literal
        `"if not _exists(resolved):"` appeared. That was residue: the function's own DOCSTRING devotes
        a paragraph to why the guard sits on the success return rather than on the reconstruction, so
        the pin was satisfied by that prose with the guard deleted; and it pinned one spelling, so
        hoisting the check into a helper or inverting it would fail a test about behavior.

        THE BEHAVIORAL ASSERTIONS THAT REMAIN ARE STRICTLY STRONGER AND ARE WHAT CATCHES THE REMOVAL.
        MEASURED by mutation: deleting `if not _exists(resolved): return None` from
        `runner_shared.lane_worktree_display` makes this test fail with
        `AssertionError: '.aw/worktrees/reclaimed' is not None`. The third case below is what makes the
        claim specifically about the SUCCESS return rather than about omission in general: its parent
        directory is NOT named `worktrees`, so the reconstruction branch could not have produced a
        value for it even if it ran, which means only a guard on the normal path can omit it.
        """
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            gone = repo / ".aw" / "worktrees" / "reclaimed"
            # The success path really is the one taken: `relative_to` does not raise for an absent path,
            # so control never reaches the `except` branch for this input.
            self.assertEqual(
                gone.resolve().relative_to(repo.resolve()).as_posix(),
                ".aw/worktrees/reclaimed",
            )
            self.assertIsNone(runner_shared.lane_worktree_display(repo, str(gone)))

            # THE DISCRIMINATING CASE: absent, INSIDE the repository, and its parent is not
            # `worktrees`, so the reconstruction branch is structurally incapable of returning it.
            # Omitting it can only be the success return's own guard.
            not_a_lane_shape = repo / ".aw" / "someplace" / "reclaimed"
            self.assertEqual(
                not_a_lane_shape.resolve().relative_to(repo.resolve()).as_posix(),
                ".aw/someplace/reclaimed",
                "fixture check: this path must still take the success path, or the assertion below "
                "would prove something about the except branch instead",
            )

            # AND THE POSITIVE CONTROL, so the two assertions above cannot be satisfied by a function
            # that omits everything: the same shape, existing, still renders.
            not_a_lane_shape.mkdir(parents=True)
            self.assertEqual(
                runner_shared.lane_worktree_display(repo, str(not_a_lane_shape)),
                ".aw/someplace/reclaimed",
            )

    def test_an_absent_worktree_OUTSIDE_the_repository_is_still_omitted(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            self.assertIsNone(
                runner_shared.lane_worktree_display(
                    repo, str(root / "elsewhere" / "worktrees" / "ghost")
                )
            )

    def test_NO_surface_ever_renders_an_ABSOLUTE_path(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            live = repo / ".aw" / "worktrees" / "alive"
            live.mkdir(parents=True)
            for candidate in (
                str(live),
                str(repo / ".aw" / "worktrees" / "gone"),
                str(root / "outside"),
                "",
                None,
            ):
                got = runner_shared.lane_worktree_display(repo, candidate)
                if got is not None:
                    self.assertFalse(pathlib.Path(got).is_absolute(), got)


# ==================================================================================================
# integpath-04 (`rl67b0`): THE RE-INTEGRATION VERB AND THE RESUME PASS
# ==================================================================================================


class _SuiteResult:
    """A stand-in for `oc_runipd.SuiteCheckResult`, carrying only what the shared code reads.

    Deliberately NOT the real NamedTuple: `runner_shared` may not import either driver, and a test that
    imported one to build this would quietly assert a coupling the module forbids. The shared code reads
    `.passing` and `.reason`, so those are what a stand-in must have.
    """

    def __init__(self, passing: bool, reason: str = "suite (fake)") -> None:
        self.passing = passing
        self.reason = reason


def _passing_suite(*_a: Any, **_k: Any) -> _SuiteResult:
    return _SuiteResult(True, "suite passed (fake)")


def _failing_suite(*_a: Any, **_k: Any) -> _SuiteResult:
    return _SuiteResult(False, "suite FAILED with exit 1 (fake)")


def _write_run_state(
    repo: pathlib.Path, state: dict, run_id: str = "run-fixture"
) -> pathlib.Path:
    """Persist `state` as a real run record, because the verb's INDEX is the run records on disk."""
    import json as _json

    run_dir = runner_shared.state_root(repo) / run_id
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    state = dict(state)
    state.setdefault("run_id", run_id)
    (run_dir / "state.json").write_text(
        _json.dumps(state, indent=2, sort_keys=True), encoding="utf-8"
    )
    return run_dir


def _finalize_plan_on_lane(
    repo: pathlib.Path, lane_dir: pathlib.Path, id6: str
) -> None:
    """Move this id6's plan from `pending/` to `executed/` ON THE LANE, and commit it there.

    This is what "a finalized lane" MEANS to the verb, and the fixture must produce it truthfully: an
    unfinalized lane is one of the five refusals, so a fixture that skipped this step would make every
    positive case refuse for the wrong reason.
    """
    import subprocess

    name = "20260906-demo-01-{0}-demo.ipd.md".format(id6)
    src = lane_dir / ".aw" / "records" / "plans" / "pending" / name
    dst = lane_dir / ".aw" / "records" / "plans" / "executed" / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "mv", str(src.relative_to(lane_dir)), str(dst.relative_to(lane_dir))],
        cwd=lane_dir,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-qm", "lifecycle({0}): finalize -> executed".format(id6)],
        cwd=lane_dir,
        check=True,
    )


def _repo_with_pending_plan(root: pathlib.Path, id6: str) -> pathlib.Path:
    """A throwaway repo holding one pending plan for `id6`. FIXTURES ONLY, never a real lane."""
    import subprocess

    repo = root / "repo"
    repo.mkdir(parents=True)
    for cmd in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "config", "user.email", "test@example.invalid"],
        ["git", "config", "user.name", "Test"],
    ):
        subprocess.run(cmd, cwd=repo, check=True)
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    (pending / "20260906-demo-01-{0}-demo.ipd.md".format(id6)).write_text(
        "# IPD: demo\n\n- Id: {0}\n- Status: approved\n".format(id6), encoding="utf-8"
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return repo


def _add_pending_plan(repo: pathlib.Path, id6: str) -> None:
    """Add an additional pending plan to an existing fixture repo."""
    import subprocess

    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True, exist_ok=True)
    (pending / "20260906-demo-01-{0}-demo.ipd.md".format(id6)).write_text(
        "# IPD: demo\n\n- Id: {0}\n- Status: approved\n".format(id6), encoding="utf-8"
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "add plan {0}".format(id6)], cwd=repo, check=True
    )


def _verified_lane(
    repo: pathlib.Path,
    root: pathlib.Path,
    id6: str,
    *,
    branch_suffix: str = "",
    finalize: bool = True,
    commit: bool = True,
) -> dict:
    """A lane in the shape the driver leaves behind after a verified-but-unintegrated turn.

    `branch_suffix` produces the ATTEMPT-SCOPED shape (`aw/lane/<id6>_attempt2`), which is the `mm6wuz`
    case and the one a name reconstructed from the id6 would silently miss.
    """
    import subprocess

    lane_id = "{0}{1}".format(id6, branch_suffix)
    branch = "aw/lane/{0}".format(lane_id)
    lane_dir = root / "lane-{0}".format(lane_id)
    base = _git(repo, "rev-parse", "HEAD")
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", branch, str(lane_dir), base],
        cwd=repo,
        check=True,
    )
    if commit:
        (lane_dir / "src").mkdir(parents=True, exist_ok=True)
        (lane_dir / "src" / "{0}.txt".format(id6)).write_text(
            "lane work\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=lane_dir, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "{0}: lane work".format(id6)],
            cwd=lane_dir,
            check=True,
        )
        if finalize:
            _finalize_plan_on_lane(repo, lane_dir, id6)
    return {
        "id6": id6,
        "lane_id": lane_id,
        "branch": branch,
        "worktree": str(lane_dir),
        "base_commit": base,
    }


def _stranded_item(lane: dict, status: str = "merge-needs-human") -> dict:
    return {
        "id6": lane["id6"],
        "position": 1,
        "setid": "demo",
        "status": status,
        "configured_file": ".aw/records/plans/pending/20260906-demo-01-{0}-demo.ipd.md".format(
            lane["id6"]
        ),
        "preserved_lane_id": lane["lane_id"],
        "preserved_branch": lane["branch"],
        "preserved_base": lane["base_commit"],
        "preserved_worktree": lane["worktree"],
        "attempts": [{"number": 1, "disposition": status}],
    }


class ReintegrationVerbTests(unittest.TestCase):
    """E-05: the verb's cases, on the SHARED implementation both hosts and both spellings call.

    WHY THE CASES LIVE HERE rather than being written twice per host: `reintegrate_lane` IS the
    implementation, and each host's `handle_integrate_command` binds only its own
    `integrate_lane_branch` wrapper and its own suite check. The host-specific halves (the merge
    subject's label, the argv routing, the shim registration) are asserted in each host's own suite;
    duplicating the decision cases there would be the drift this Set exists to end.
    """

    def _integrate(self, repo, handle, id6, validation_runner):
        """The oc host's wrapper, called exactly as `handle_integrate_command` calls it."""
        return oc_runipd.integrate_lane_branch(repo, handle, id6, validation_runner)

    def test_a_verified_finalized_lane_integrates_with_no_agent_turn(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0001")
            lane = _verified_lane(repo, root, "aa0001")
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})
            before = _git(repo, "rev-parse", "HEAD")

            outcome = runner_shared.reintegrate_lane(
                repo,
                "aa0001",
                integrate=self._integrate,
                suite_check=_passing_suite,
            )

            self.assertTrue(outcome.integrated, outcome.reason)
            self.assertEqual(outcome.code, runner_shared.REINTEGRATE_OK)
            self.assertNotEqual(_git(repo, "rev-parse", "HEAD"), before)
            # The lane's work and the finalize are BOTH on main now.
            self.assertTrue((repo / "src" / "aa0001.txt").is_file())
            self.assertTrue(
                (
                    repo
                    / ".aw"
                    / "records"
                    / "plans"
                    / "executed"
                    / "20260906-demo-01-aa0001-demo.ipd.md"
                ).is_file()
            )
            # And the suite REALLY RAN, through the injected checker, as part of the gate.
            self.assertIsNotNone(outcome.suite)
            self.assertTrue(outcome.suite.passing)

    def test_the_gate_RAN_and_COULD_HAVE_REFUSED(self):
        """THE safety-critical assertion: "the gate was invoked" is NOT sufficient on its own.

        The shipped `make_integration_validation_runner` returns a constant True, so a single-lane gate
        call passes UNCONDITIONALLY; an implementation that merely routed through the gate would look
        verified while verifying nothing. So this asserts BOTH halves: the gate was called (spy), AND a
        failing suite makes it REFUSE with main untouched.
        """
        from agent_workflows import orchestrate_isolation

        calls = []
        real_gate = orchestrate_isolation.execute_merge_and_revalidate_gate

        def spy_gate(*a, **k):
            calls.append(k)
            return real_gate(*a, **k)

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0002")
            lane = _verified_lane(repo, root, "aa0002")
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})
            before = _git(repo, "rev-parse", "HEAD")

            with mock.patch.object(
                orchestrate_isolation, "execute_merge_and_revalidate_gate", spy_gate
            ):
                outcome = runner_shared.reintegrate_lane(
                    repo,
                    "aa0002",
                    integrate=self._integrate,
                    suite_check=_failing_suite,
                )

            self.assertEqual(len(calls), 1, "the attempt must route through the gate")
            # THE BASE PASSED IS THE LANE'S OWN DECLARED BASE, never main's current head: the
            # stale-base check is a caller-consistency assertion, and passing main's head refuses every
            # recovered lane while rebuilding the outcome to satisfy it revalidates a diff that REVERTS
            # main.
            self.assertEqual(calls[0]["integration_base_commit"], lane["base_commit"])
            self.assertFalse(outcome.integrated)
            self.assertEqual(outcome.code, runner_shared.REINTEGRATE_GATE_REFUSED)
            self.assertIn("combined_red", outcome.reason.replace("-", "_"))
            self.assertIn("suite FAILED", outcome.reason)
            # MAIN IS UNTOUCHED and the lane is preserved.
            self.assertEqual(_git(repo, "rev-parse", "HEAD"), before)
            self.assertFalse((repo / "src" / "aa0002.txt").exists())
            self.assertEqual(
                _git(repo, "rev-parse", "--verify", lane["branch"]),
                _git(repo, "rev-parse", lane["branch"]),
            )

    def test_the_validation_runner_is_NOT_the_shipped_constant_true_one(self):
        """The runner the verb supplies must be able to say NO, and it must be the verb's OWN runner.

        THE PREMISE OF THIS TEST CHANGED AT integearn-03 (`daexj1`) E-03, and the assertion was updated
        rather than deleted because what it PROTECTS is unchanged. It used to read
        `assertTrue(shipped(...))`, pinning that the shared factory returned a constant True, and used
        that fact to argue the verb must not call it. The factory no longer returns a constant: it now
        materializes the merge result and runs the suite there, and with NO `suite_check` injected (the
        three-argument call below) it FAILS CLOSED and returns False.

        So the old assertion is now false, and asserting it would be asserting the inert gate this
        repository spent a plan removing. What still matters, and is asserted instead, is the property
        the test exists for: the shared factory must never be a source of unconditional YES, and
        `reintegrate_lane` must supply its OWN suite-backed runner rather than reaching for the factory.
        """
        # THE MODE IS STATED EXPLICITLY, exactly as a real run's frozen state states it
        # (`oc_runipd.py:3477-3478` writes `validate` and `no_audit`; `agy_runipd.py:2190` writes
        # `no_verify`). It matters here: revalidation is the SUITE-EARNED mode's step, and an options
        # mapping carrying none of those keys resolves to the VERIFIER mode, whose trust signal is the
        # verifier's verdict rather than a suite. This case is about the suite-earned mode.
        shipped = runner_shared.make_integration_validation_runner(
            {"options": {"validate": False}}, pathlib.Path("."), {}
        )
        self.assertFalse(
            shipped("any diff", ("any", "files")),
            "with no suite checker injected the shared runner must FAIL CLOSED; a True here would be "
            "a way to land an unvalidated lane on main while reporting a green gate",
        )

    def test_reintegrate_lane_empty_dirty_and_missing_branch_refusals(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0003")
            lane = _verified_lane(repo, root, "aa0003")
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})
            import subprocess

            # 1. Missing branch refuses
            subprocess.run(
                ["git", "worktree", "remove", "--force", lane["worktree"]],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ["git", "branch", "-qD", lane["branch"]], cwd=repo, check=True
            )
            outcome = runner_shared.reintegrate_lane(
                repo, "aa0003", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome.integrated)
            self.assertEqual(outcome.code, runner_shared.REINTEGRATE_LANE_ABSENT)

            # 2. Empty lane holding no commits refuses
            lane_empty = _verified_lane(repo, root, "aa0004", commit=False)
            _write_run_state(
                repo, {"repo": str(repo), "queue": [_stranded_item(lane_empty)]}
            )
            outcome_empty = runner_shared.reintegrate_lane(
                repo, "aa0004", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome_empty.integrated)
            self.assertEqual(outcome_empty.code, runner_shared.REINTEGRATE_LANE_EMPTY)

            # 3. Dirty lane with zero commits refuses
            lane_dirty = _verified_lane(repo, root, "aa0005", commit=False)
            (pathlib.Path(lane_dirty["worktree"]) / "dirt.txt").write_text(
                "uncommitted\n", encoding="utf-8"
            )
            _write_run_state(
                repo, {"repo": str(repo), "queue": [_stranded_item(lane_dirty)]}
            )
            outcome_dirty = runner_shared.reintegrate_lane(
                repo, "aa0005", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome_dirty.integrated)
            self.assertEqual(outcome_dirty.code, runner_shared.REINTEGRATE_LANE_EMPTY)

            # 4. Plan not finalized refuses
            lane_not_fin = _verified_lane(repo, root, "aa0006", finalize=False)
            _write_run_state(
                repo, {"repo": str(repo), "queue": [_stranded_item(lane_not_fin)]}
            )
            outcome_not_fin = runner_shared.reintegrate_lane(
                repo, "aa0006", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome_not_fin.integrated)
            self.assertEqual(
                outcome_not_fin.code, runner_shared.REINTEGRATE_PLAN_NOT_FINALIZED
            )

    def test_reintegrate_lane_ownership_ambiguity_and_error_refusals(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0007")
            lane = _verified_lane(repo, root, "aa0007")
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})

            from agent_workflows import worktree_lease

            worktree_lease.write_lane_owner(
                repo,
                lane["lane_id"],
                branch=lane["branch"],
                worktree=lane["worktree"],
                base_commit=lane["base_commit"],
                disposition="created",
            )
            outcome_live = runner_shared.reintegrate_lane(
                repo, "aa0007", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome_live.integrated)
            self.assertEqual(outcome_live.code, runner_shared.REINTEGRATE_LANE_LIVE)

            # Two recorded lanes with no run id -> ambiguous refusal
            _add_pending_plan(repo, "aa0009")
            first = _verified_lane(repo, root, "aa0009")
            second = _verified_lane(repo, root, "aa0009", branch_suffix="_attempt2")
            _write_run_state(
                repo,
                {"repo": str(repo), "queue": [_stranded_item(first)]},
                run_id="run-one",
            )
            _write_run_state(
                repo,
                {"repo": str(repo), "queue": [_stranded_item(second)]},
                run_id="run-two",
            )
            outcome_ambig = runner_shared.reintegrate_lane(
                repo, "aa0009", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome_ambig.integrated)
            self.assertEqual(
                outcome_ambig.code, runner_shared.REINTEGRATE_AMBIGUOUS_LANE
            )
            self.assertEqual(len(outcome_ambig.candidates), 2)

            # Explicit run_id resolves it
            named = runner_shared.reintegrate_lane(
                repo,
                "aa0009",
                integrate=self._integrate,
                suite_check=_passing_suite,
                run_id="run-two",
            )
            self.assertTrue(named.integrated)
            self.assertEqual(named.candidate.branch, "aw/lane/aa0009_attempt2")

            # No run record naming a lane
            _add_pending_plan(repo, "aa0010")
            _verified_lane(repo, root, "aa0010")
            outcome_no_rec = runner_shared.reintegrate_lane(
                repo, "aa0010", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome_no_rec.integrated)
            self.assertEqual(
                outcome_no_rec.code, runner_shared.REINTEGRATE_NO_LANE_RECORD
            )

            # Exception from integrate callable is a refusal, not a raise
            _add_pending_plan(repo, "aa0011")
            lane11 = _verified_lane(repo, root, "aa0011")
            _write_run_state(
                repo, {"repo": str(repo), "queue": [_stranded_item(lane11)]}
            )

            def boom(*_a, **_k):
                raise RuntimeError("git exploded")

            outcome_err = runner_shared.reintegrate_lane(
                repo, "aa0011", integrate=boom, suite_check=_passing_suite
            )
            self.assertFalse(outcome_err.integrated)
            self.assertEqual(outcome_err.code, runner_shared.REINTEGRATE_ERROR)
            self.assertIn("git exploded", outcome_err.reason)

    def test_a_merge_conflict_item_is_ALSO_re_attemptable(self):
        """OQ-01: both statuses, because main has moved and only the gate can say if it still conflicts.

        AND BOTH VOCABULARIES (`l2mzxn`). The pre-rename spellings are part of this contract rather than
        leftovers: this verb exists to rescue a lane stranded by an EARLIER run, which is exactly the run
        most likely to have written `integration-blocked` / `merge-conflict`. Dropping them would make
        every already-stranded lane in the repository's history unrecoverable by the one verb built to
        recover it, so the rename would have destroyed data while looking cosmetic.
        """
        self.assertEqual(
            set(runner_shared.REINTEGRATABLE_STATUSES),
            {
                "merge-needs-human",
                "merge-refused",
                "integration-blocked",
                "merge-conflict",
            },
        )
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0012")
            lane = _verified_lane(repo, root, "aa0012")
            state = {
                "repo": str(repo),
                "run_id": "run-fixture",
                "queue": [_stranded_item(lane, status="merge-refused")],
            }
            _write_run_state(repo, state)
            self.assertEqual(
                [
                    c.id6
                    for _item, c, _prior in runner_shared.stranded_integration_candidates(
                        repo, state
                    )
                ],
                ["aa0012"],
            )


class ResumeIntegrationPassTests(unittest.TestCase):
    """E-06: the automatic pass, where the EXPENSIVE failure lives.

    THE TWO ABSENCES ARE THE FIX and are asserted directly: zero agent turns and zero new lanes. A test
    asserting only that the item ended integrated would pass identically had the resume paid $39 for a
    turn to get there, which is the measured bug.
    """

    def _integrate(self, repo, handle, id6, validation_runner):
        return oc_runipd.integrate_lane_branch(repo, handle, id6, validation_runner)

    def _pass(self, repo, run_dir, state, *, suite=_passing_suite, integrate=None):
        lines: list[str] = []
        records = runner_shared.integrate_stranded_lanes(
            repo=repo,
            run_dir=run_dir,
            state=state,
            integrate=integrate or self._integrate,
            suite_check=suite,
            save_state=lambda rd, st: (rd / "state.json").write_text(
                __import__("json").dumps(st, indent=2, sort_keys=True), encoding="utf-8"
            ),
            append_jsonl=runner_shared.append_jsonl,
            process_backlog_close=None,
            report=lines.append,
        )
        return records, lines

    def test_a_stranded_lane_is_MERGED_and_the_item_reaches_executed(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "bb0001")
            lane = _verified_lane(repo, root, "bb0001")
            item = _stranded_item(lane)
            state = {"repo": str(repo), "run_id": "run-fixture", "queue": [item]}
            run_dir = _write_run_state(repo, state)

            records, lines = self._pass(repo, run_dir, state)

            self.assertEqual([r["outcome"] for r in records], ["integrated"])
            self.assertEqual(item["status"], "executed")
            self.assertTrue((repo / "src" / "bb0001.txt").is_file())
            # THE SAME RECORDS THE IN-RUN SUCCESS PATH WRITES.
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("ipd-finalized", events)
            self.assertIn('"reintegrated": true', events)
            # `last_plan_path` RE-RESOLVED: the plan now lives in executed/ on main.
            self.assertIn("executed", item["last_plan_path"])
            self.assertTrue(any("NO agent turn" in line for line in lines))

    def test_ZERO_new_lanes_are_allocated(self):
        """The second absence: no `_attempt2`. That branch IS the orphaning `mm6wuz` measured."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "bb0002")
            lane = _verified_lane(repo, root, "bb0002")
            state = {
                "repo": str(repo),
                "run_id": "run-fixture",
                "queue": [_stranded_item(lane)],
            }
            run_dir = _write_run_state(repo, state)

            self._pass(repo, run_dir, state)

            branches = _git(repo, "branch", "--list", "aw/lane/bb0002*")
            self.assertNotIn("_attempt2", branches)

    def test_the_flag_ALREADY_rewrote_the_status_and_the_pass_still_selects_it(self):
        """The ordering fact E-03 turns on, asserted as the shape the code must survive.

        `--retry-incomplete` runs BEFORE the pass may legally sit, so by then `status` is `queued` and
        `recovery_next` is True. A pass selecting on `status in {integration-blocked, merge-conflict}`
        would see nothing here, which is exactly the case the fix exists for; selection is therefore on
        durable lane facts plus the recorded prior disposition.
        """
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "bb0003")
            lane = _verified_lane(repo, root, "bb0003")
            item = _stranded_item(lane)
            # Exactly what the requeue leaves behind.
            item["requeue_from_status"] = "merge-needs-human"
            item["status"] = "queued"
            item["recovery_next"] = True
            state = {"repo": str(repo), "run_id": "run-fixture", "queue": [item]}
            run_dir = _write_run_state(repo, state)

            records, _lines = self._pass(repo, run_dir, state)

            self.assertEqual([r["outcome"] for r in records], ["integrated"])
            self.assertEqual(item["status"], "executed")
            # AND THE FLIP IS UNDONE, or the loop would pay for a turn to redo what just landed.
            self.assertNotIn("recovery_next", item)

    def test_a_REFUSED_attempt_holds_the_item_back_with_an_explicit_reason(self):
        """E-04: refused means NOT re-dispatched, restored to its terminal status, and REPORTED."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "bb0004")
            lane = _verified_lane(repo, root, "bb0004")
            item = _stranded_item(lane)
            item["requeue_from_status"] = "merge-needs-human"
            item["status"] = "queued"
            item["recovery_next"] = True
            state = {"repo": str(repo), "run_id": "run-fixture", "queue": [item]}
            run_dir = _write_run_state(repo, state)
            before = _git(repo, "rev-parse", "HEAD")

            records, lines = self._pass(repo, run_dir, state, suite=_failing_suite)

            self.assertEqual([r["outcome"] for r in records], ["held-back"])
            self.assertEqual(item["status"], "merge-needs-human")
            self.assertNotIn("recovery_next", item)
            self.assertEqual(_git(repo, "rev-parse", "HEAD"), before)
            # The lane is STILL THERE: it is the preserved evidence, never reclaimed to clear the way.
            self.assertTrue(
                _git(repo, "branch", "--list", lane["branch"])
                .strip()
                .endswith(lane["branch"])
            )
            self.assertNotIn("_attempt2", _git(repo, "branch", "--list", "aw/lane/*"))
            joined = "\n".join(lines)
            self.assertIn("was NOT re-dispatched", joined)
            self.assertIn("bb0004", joined)
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("ipd-reintegration-refused", events)

    def test_an_exception_does_not_abort_the_pass(self):
        """A resume that died because one lane could not merge would be worse than doing nothing."""

        def boom(*_a, **_k):
            raise RuntimeError("git exploded")

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "bb0005")
            lane = _verified_lane(repo, root, "bb0005")
            item = _stranded_item(lane)
            state = {"repo": str(repo), "run_id": "run-fixture", "queue": [item]}
            run_dir = _write_run_state(repo, state)

            records, _lines = self._pass(repo, run_dir, state, integrate=boom)

            self.assertEqual([r["outcome"] for r in records], ["held-back"])
            self.assertEqual(records[0]["code"], runner_shared.REINTEGRATE_ERROR)
            self.assertEqual(item["status"], "merge-needs-human")

    def test_items_that_genuinely_need_a_turn_are_NOT_captured(self):
        """E-04 narrows the flag's reach; it does not redefine it.

        Two negatives in one place, because both are ways the narrowing could go too far: a `partial`
        item is not in the re-integratable statuses at all, and a snapshot-only `interrupted` item whose
        lane holds a commit but no finalize is the case `txc9l1` routes to a verify-and-continue turn.
        """
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "bb0006")
            snapshot = _verified_lane(repo, root, "bb0006", finalize=False)
            partial_item = {
                "id6": "bb0007",
                "status": "partial",
                "preserved_branch": snapshot["branch"],
                "preserved_lane_id": snapshot["lane_id"],
                "preserved_base": snapshot["base_commit"],
            }
            interrupted = _stranded_item(snapshot, status="interrupted")
            state = {
                "repo": str(repo),
                "run_id": "run-fixture",
                "queue": [partial_item, interrupted],
            }
            run_dir = _write_run_state(repo, state)

            self.assertEqual(
                runner_shared.stranded_integration_candidates(repo, state), []
            )
            records, _lines = self._pass(repo, run_dir, state)
            self.assertEqual(records, [])
            self.assertEqual(partial_item["status"], "partial")
            self.assertEqual(interrupted["status"], "interrupted")


class MeasuredIncidentsAreSurvivedTests(unittest.TestCase):
    """E-07: this repository's OWN two incidents, reproduced synthetically and shown survived.

    Both are HISTORICAL (their branches are deleted and their plans are in `executed/`, recovered by
    hand), so the conditions are rebuilt in throwaway repositories rather than probed for. Each case is
    run on BOTH hosts, because the host binding is the one thing the shared implementation cannot
    supply, and a fix proven on one host only is how the two drivers diverged before.
    """

    HOSTS = ("oc", "agy")

    def _integrate_for(self, host: str):
        module = oc_runipd if host == "oc" else agy_runipd
        return lambda repo, handle, id6, runner: module.integrate_lane_branch(
            repo, handle, id6, runner
        )

    def test_the_FOUR_LANE_incident_is_recovered_by_the_verb_with_no_agent_turn(self):
        """`run-20260905T050043Z-639569`: four items verified, finalized, refused on transient dirt.

        All four merged clean against main afterwards, and recovering them took a full session of hand
        merges. Here each is recovered by ONE verb call, and the launcher is not involved at all.
        """
        for host in self.HOSTS:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as d:
                root = pathlib.Path(d)
                repo = _repo_with_pending_plan(root, "ff0001")
                # Four plans, four lanes, exactly the shape the run left behind.
                pending = repo / ".aw" / "records" / "plans" / "pending"
                ids = ["ff0001", "ff0002", "ff0003", "ff0004"]
                for id6 in ids[1:]:
                    (
                        pending / "20260906-demo-01-{0}-demo.ipd.md".format(id6)
                    ).write_text(
                        "# IPD: demo\n\n- Id: {0}\n- Status: approved\n".format(id6),
                        encoding="utf-8",
                    )
                import subprocess

                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "four pending plans"], cwd=repo, check=True
                )
                lanes = [_verified_lane(repo, root, id6) for id6 in ids]
                _write_run_state(
                    repo,
                    {
                        "repo": str(repo),
                        "queue": [_stranded_item(lane) for lane in lanes],
                    },
                )

                for id6 in ids:
                    outcome = runner_shared.reintegrate_lane(
                        repo,
                        id6,
                        integrate=self._integrate_for(host),
                        suite_check=_passing_suite,
                    )
                    self.assertTrue(
                        outcome.integrated, "{0}: {1}".format(id6, outcome.reason)
                    )

                for id6 in ids:
                    self.assertTrue(
                        (repo / "src" / "{0}.txt".format(id6)).is_file(), id6
                    )
                    self.assertTrue(
                        (
                            repo
                            / ".aw"
                            / "records"
                            / "plans"
                            / "executed"
                            / "20260906-demo-01-{0}-demo.ipd.md".format(id6)
                        ).is_file(),
                        id6,
                    )
                # NO lane was orphaned into a second attempt by any of the four recoveries.
                self.assertNotIn(
                    "_attempt", _git(repo, "branch", "--list", "aw/lane/*")
                )

    def test_the_THREE_LANE_incident_stops_accumulating_lanes_on_resume(self):
        """`mm6wuz`: a verified lane that accumulated `_attempt2` and `_attempt3` across resumes.

        $39.42 of verified work was recovered by hand from the third lane. The fix is asserted as the
        CONTRAST: before it, a resume of such an item re-dispatched it and `allocate_worktree` scoped a
        SECOND lane; here the resume integrates the FIRST lane and allocates none.
        """
        import json as _json
        import subprocess

        for host in self.HOSTS:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as d:
                root = pathlib.Path(d)
                repo = _repo_with_pending_plan(root, "mm0001")
                lane = _verified_lane(repo, root, "mm0001")
                item = _stranded_item(lane)
                # The `--retry-incomplete` shape, which is how `mm6wuz` was resumed.
                item["requeue_from_status"] = "merge-needs-human"
                item["status"] = "queued"
                item["recovery_next"] = True
                state = {"repo": str(repo), "run_id": "run-fixture", "queue": [item]}
                run_dir = _write_run_state(repo, state)

                # PRE-FIX BEHAVIOR, measured here rather than asserted from memory: dispatching such an
                # item attempt-scopes a SECOND lane and leaves the first untouched.
                from agent_workflows import worktree_lease

                handle = worktree_lease.allocate_worktree(repo, "mm0001")
                self.assertEqual(handle.branch, "aw/lane/mm0001_attempt2")
                self.assertEqual(handle.displaced_from, "aw/lane/mm0001")
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(handle.path)],
                    cwd=repo,
                    check=True,
                )
                subprocess.run(
                    ["git", "branch", "-qD", handle.branch], cwd=repo, check=True
                )

                records = runner_shared.integrate_stranded_lanes(
                    repo=repo,
                    run_dir=run_dir,
                    state=state,
                    integrate=self._integrate_for(host),
                    suite_check=_passing_suite,
                    save_state=lambda rd, st: (rd / "state.json").write_text(
                        _json.dumps(st, indent=2, sort_keys=True), encoding="utf-8"
                    ),
                    append_jsonl=runner_shared.append_jsonl,
                    process_backlog_close=None,
                )

                self.assertEqual([r["outcome"] for r in records], ["integrated"])
                self.assertEqual(item["status"], "executed")
                # THE FIRST lane's work is on main, and NO second lane exists.
                self.assertTrue((repo / "src" / "mm0001.txt").is_file())
                self.assertNotIn(
                    "_attempt", _git(repo, "branch", "--list", "aw/lane/mm0001*")
                )


class PathSelectorKindTests(unittest.TestCase):
    """Regression test for preserving kind in expand_selectors (hp9rot E-10 / BUG-15)."""

    def test_path_selector_kind(self):
        """E-10: Path selector to orchestrator IPD retains kind: orchestrator in manifest."""
        with tempfile.TemporaryDirectory() as temp:
            repo = pathlib.Path(temp)
            plan_dir = repo / ".aw/records/plans/pending"
            plan_dir.mkdir(parents=True, exist_ok=True)
            plan_file = plan_dir / "20260908-orch-01-abc123-orchestrator.ipd.md"
            plan_file.write_text(
                "# IPD: orchestrator\n\n- Date: 2026-09-08\n- Kind: orchestrator\n- Status: approved\n- Set: orch\n- Order: 1\n- Id: abc123\n\n## Goal\nOrchestrate.\n",
                encoding="utf-8",
            )
            for name, mod in (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd)):
                with self.subTest(driver=name):
                    manifest: dict[str, Any] = {"plans": {}, "sets": {}}
                    queue_ids = mod.expand_selectors(
                        manifest, [str(plan_file)], repo=repo
                    )
                    self.assertEqual(queue_ids, ["abc123"])
                    self.assertEqual(
                        manifest["plans"]["abc123"].get("kind"),
                        "orchestrator",
                        f"{name} must retain kind: orchestrator",
                    )


class SharedColorDecisionTests(unittest.TestCase):
    """`should_color` is a sanctioned DELEGATION to `term.should_color` (IPD `z8ddk0` E-02).

    WHY THESE ASSERTIONS AND NOT A FINGERPRINT. This symbol is enumerated in
    `SUPERSEDED_SINCE_MOVE` above, which exempts it from the byte-identical pre-move capture
    (a delegation cannot fingerprint as the body it replaces). That exemption removes the
    only coverage the harness gave it, so this class is the replacement: it pins the SHAPE
    (one delegating statement, so the `def` is a binding and not a second body) and the
    BEHAVIOR CHANGE that motivated the supersession.
    """

    class _TTYStream:
        def isatty(self) -> bool:
            return True

    class _PipeStream:
        def isatty(self) -> bool:
            return False

    def setUp(self):
        import os

        self._saved = {
            k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")
        }

    def tearDown(self):
        import os

        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _set_env(self, **values: str | None) -> None:
        import os

        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_should_color_behavior(self):
        from agent_workflows import term

        self._set_env(NO_COLOR=None, FORCE_COLOR=None, TERM="xterm-256color")
        for stream in (self._TTYStream(), self._PipeStream()):
            self.assertEqual(
                runner_shared.should_color(stream),
                term.should_color(stream),
            )

        # TERM=dumb
        self._set_env(NO_COLOR=None, FORCE_COLOR=None, TERM="dumb")
        self.assertFalse(runner_shared.should_color(self._TTYStream()))

        # FORCE_COLOR=0
        self._set_env(NO_COLOR=None, FORCE_COLOR="0", TERM="xterm-256color")
        self.assertFalse(runner_shared.should_color(self._PipeStream()))
        self.assertTrue(runner_shared.should_color(self._TTYStream()))


class GateAnswerVocabularyTests(unittest.TestCase):
    """The closed vocabulary an agent answers a refused integration with."""

    def test_valid_answers_and_dispositions(self):
        # not-mine with reason integrates
        v = runner_shared.validate_gate_answer(
            {"answer": "not-mine", "reason": "fails in records/"}
        )
        self.assertTrue(v.usable and v.integrates and not v.earns_recheck)

        # fixed earns recheck
        v = runner_shared.validate_gate_answer(
            {"answer": "fixed", "reason": "repaired"}
        )
        self.assertTrue(v.usable and v.earns_recheck and not v.integrates)

        # mine refuses
        v = runner_shared.validate_gate_answer("mine")
        self.assertTrue(v.usable and not v.integrates and not v.earns_recheck)

        # needs-human refuses and awaits decision
        v = runner_shared.validate_gate_answer(
            {"answer": "needs-human", "reason": "maintainer call"}
        )
        self.assertTrue(v.usable and v.refuses and v.awaits_human_decision)

        # check exhaustiveness
        for token in runner_shared.GATE_ANSWERS:
            reason = (
                "because" if token in runner_shared.GATE_ANSWERS_NEEDING_REASON else ""
            )
            res = runner_shared.validate_gate_answer(
                {"answer": token, "reason": reason}
            )
            self.assertTrue(res.usable)
            self.assertEqual(
                sum(1 for d in [res.integrates, res.earns_recheck, res.refuses] if d), 1
            )

    def test_invalid_answers_and_reasons_fail_closed(self):
        # missing reason
        self.assertFalse(
            runner_shared.validate_gate_answer({"answer": "needs-human"}).usable
        )
        self.assertFalse(
            runner_shared.validate_gate_answer({"answer": "not-mine"}).usable
        )
        # unrecognized token
        self.assertFalse(
            runner_shared.validate_gate_answer(
                {"answer": "unknown", "reason": "x"}
            ).usable
        )
        # malformed types
        for raw in (None, "", {}, 42, [], {"answer": ""}):
            self.assertFalse(runner_shared.validate_gate_answer(raw).usable)

    def test_shape_coercion_and_exception_safety(self):
        for raw in ("NOT MINE", "not_mine", "  Not-Mine  "):
            v = runner_shared.validate_gate_answer({"answer": raw, "reason": "x"})
            self.assertEqual(v.answer, runner_shared.GATE_ANSWER_NOT_MINE)

        # exception safety
        class Hostile:
            def __str__(self):
                raise RuntimeError("boom")

        self.assertFalse(runner_shared.validate_gate_answer(Hostile()).usable)


if __name__ == "__main__":
    unittest.main()

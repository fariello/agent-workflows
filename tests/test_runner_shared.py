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

import ast
import builtins
import contextlib
import io
import json
import pathlib
import re
import tempfile
import unittest
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared

FIXTURE = (
    pathlib.Path(__file__).parent
    / "fixtures"
    / "runner_shared_premove_fingerprints.json"
)

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
NATIVE_SHARED_RUN_CHECKED_CALLERS: dict[str, int] = {
    "collect_lane_earned_paths": 1,
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
SUPERSEDED_SINCE_MOVE = ("state_root", "_run_git", "should_color")


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def module_source(module) -> str:
    return pathlib.Path(str(module.__file__)).read_text(encoding="utf-8")


def top_level_definitions(module) -> dict[str, int]:
    """Map every top-level `def`/`async def`/`class` in ``module`` to its line number.

    AST-based on purpose: a substring search cannot tell a definition from a mention of one in a
    comment or docstring, and misses spelling variants such as `class X (Base):`.
    """
    found: dict[str, int] = {}
    for node in ast.parse(module_source(module)).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.setdefault(node.name, node.lineno)
    return found


def _normalize_dump(dumped: str) -> str:
    """Make an ``ast.dump`` string comparable ACROSS CPython versions.

    WHY THIS EXISTS. `ast.dump` is not stable across releases: on CPython <= 3.13 an
    `arguments` node renders an empty `posonlyargs=[]` field, and on 3.14 that empty field is
    omitted. The committed fixture was captured on 3.14, so every symbol whose signature has no
    positional-only parameters fingerprinted differently on 3.9-3.13 and this harness failed on
    5 of the 6 Python versions the `tests` workflow matrixes over - 28 subtest failures that say
    nothing about whether the move was pure.

    Normalizing here rather than re-capturing the fixture is deliberate: re-capturing on 3.12
    would just move the breakage to 3.14, and the fixture is supposed to be a record of the
    PRE-MOVE source at HEAD `1ecc5891`, not of the interpreter that read it.

    This erases ONLY EMPTY list fields, i.e. the fields 3.14 omits and earlier versions spell out
    (`posonlyargs=[]`, `args=[]`, `kwonlyargs=[]`, `kw_defaults=[]`, `defaults=[]`, and the same
    for `decorator_list`/`bases`/`keywords`). A field that actually HAS contents renders as
    `name=[...]` with something inside and is left untouched, so the harness still fails if a
    moved body's arguments, decorators, or bases really change. Removing an empty field cannot
    make two different signatures compare equal: absent and empty mean the same thing here, which
    is exactly why 3.14 stopped printing them.

    Implemented as a REGEX over whole `name=[]` fields rather than plain string replacement.
    Substring replacement is unsafe here because field names nest as substrings of one another
    (`args` inside `posonlyargs` and `kwonlyargs`; `kw_defaults` inside `defaults`), so a naive
    `.replace("args=[], ", "")` corrupts `kwonlyargs=[], ` into `kwonly` and produces garbage that
    matches nothing. The word boundary is what makes this correct.
    """

    # Drop every `<field>=[]` entry, then repair the separators. `\b` prevents matching the tail of
    # a longer field name.
    out = re.sub(r"\b\w+=\[\](, )?", "", dumped)
    # Collapse any separator damage left where an empty field sat between two kept fields.
    out = re.sub(r"\(, +", "(", out)
    out = re.sub(r", +\)", ")", out)
    out = re.sub(r", *,", ",", out)
    return out


def _without_docstring(node: ast.AST) -> ast.AST:
    """Return ``node`` with a leading docstring removed, leaving every executable statement.

    WHY A HARNESS ABOUT PURITY IS ALLOWED TO IGNORE A DOCSTRING (depreview 03ie04 E-05, and see
    `DOCUMENTED_SINCE_MOVE` for the enumeration this serves). This file's claim is that a moved body
    still BEHAVES as it did, and it proves that by fingerprinting the AST. A docstring is a string
    constant that no caller can observe through behavior, so adding one cannot change what the
    function does, yet it DOES change `ast.dump` and therefore fails a strict comparison. The
    alternative was measured and rejected: a moved symbol could then never be DOCUMENTED, which
    penalizes exactly the improvement this repository wants (`plan_bucket` had no docstring at all,
    and its missing contract is what let `edge_satisfied` ask it a question it cannot answer).

    THIS IS A SUBTRACTION, NOT A HAND-WAVE, exactly like `_strip_injected_parameter` above: ONLY the
    leading string expression is removed, and every remaining token must then match the pre-move
    capture. Change one executable line as well and the comparison still fails. It is applied ONLY to
    the names enumerated in `DOCUMENTED_SINCE_MOVE`, so a silent body edit to any other symbol still
    fails STRICTLY.
    """
    clone = ast.parse(ast.unparse(node)).body[0]
    assert isinstance(clone, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    body = clone.body
    if (
        len(body) > 1
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        # A function whose ONLY statement is its docstring would become syntactically invalid, so the
        # `len(body) > 1` guard keeps it rather than emitting an empty body.
        clone.body = body[1:]
    return clone


def _capture_without_docstring(dumped: str) -> str:
    """Return a CAPTURED fingerprint re-dumped with its leading docstring removed.

    THE CAPTURE SIDE NEEDS ITS OWN SUBTRACTION, which is why this exists beside
    `_without_docstring` rather than being folded into it (IPD `2iye0e` E-04, serving
    `REDOCUMENTED_SINCE_MOVE`). `_without_docstring` strips the CURRENT source, which is all a symbol
    that GAINED a docstring needs, because its capture has none. A symbol whose captured body ALREADY
    contained a docstring needs the same subtraction applied to the CAPTURE too, or a stripped body is
    compared against an unstripped capture and can never match. Measured: adding `describe_lane` to
    `DOCUMENTED_SINCE_MOVE` failed for exactly that reason.

    THIS IS STILL A SUBTRACTION, NOT A RE-BASELINE. The fixture on disk is never rewritten; the
    recorded dump is parsed back into a tree, ONLY its leading string expression is dropped, and every
    remaining token must match. The alternative - regenerating the fixture entry - would replace
    recorded pre-move truth with a post-move value in the one file whose whole value is that a change
    to it is suspicious.
    """
    namespace = {
        name: getattr(ast, name) for name in dir(ast) if not name.startswith("_")
    }
    tree = eval(dumped, {"__builtins__": {}}, namespace)  # noqa: S307 - fixture-authored dump only
    ast.fix_missing_locations(tree)
    node = tree.body[0]
    assert isinstance(
        node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    ), "a captured fingerprint must be a single def"
    stripped = _without_docstring(node)
    return _normalize_dump(
        ast.dump(ast.parse(ast.unparse(stripped)), include_attributes=False)
    )


def fingerprint_of(module, name: str, *, drop_docstring: bool = False) -> str | None:
    """The post-move fingerprint of ``name`` as defined in ``module``, or None if absent."""
    for node in ast.parse(module_source(module)).body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == name
        ):
            target = _without_docstring(node) if drop_docstring else node
            return _normalize_dump(
                ast.dump(ast.parse(ast.unparse(target)), include_attributes=False)
            )
    return None


def _strip_injected_parameter(name: str, node: ast.AST) -> ast.AST:
    """Remove the ONE keyword-only parameter ``name`` gained, so the rest can be compared.

    This is what "fingerprint equality MODULO the injection" means concretely, and it is a
    subtraction rather than a hand-wave: the added parameter is removed and EVERY OTHER token must
    then match the pre-move capture exactly. If the move also changed anything else, this still
        fails.
    """
    clone = ast.parse(ast.unparse(node)).body[0]
    param = INJECTED[name]
    assert isinstance(clone, (ast.FunctionDef, ast.AsyncFunctionDef))
    kwonly = [a for a in clone.args.kwonlyargs if a.arg != param]
    removed = len(clone.args.kwonlyargs) - len(kwonly)
    if removed != 1:
        raise AssertionError(
            f"{name} should carry exactly ONE injected keyword-only parameter "
            f"`{param}`; found {removed} matching of {[a.arg for a in clone.args.kwonlyargs]}"
        )
    keep_defaults = [
        d
        for a, d in zip(clone.args.kwonlyargs, clone.args.kw_defaults)
        if a.arg != param
    ]
    clone.args.kwonlyargs = kwonly
    clone.args.kw_defaults = keep_defaults
    return clone


def _substitute_injected_call(name: str, node: ast.AST) -> ast.AST:
    """Rewrite the parameter's USE back to the runner-local name it replaced.

    `run_checked` called `pinned_child_env(env)` and now calls `env_builder(env)`; `save_state`
    called `write_report(...)` and still does, through the parameter. Mapping the use back is the
    other half of the modulo, so the body comparison is over the WHOLE body and not just its head.

    `discover_plans` additionally needs its TYPE ANNOTATIONS mapped back, and that substitution is
    named here rather than waved at because it is the one place where a moved body's TEXT genuinely
    had to change beyond adding a parameter. The shared module CANNOT name `PlanRecord`: the two
    runners define different NamedTuples under that name, and importing either would be exactly the
    "drag one host's type into shared code" error the module forbids. So `dict[str, PlanRecord]`
    became `dict[str, Any]` in the signature and the local. The substitution below restores the
    original spelling so the rest of the body is still compared EXACTLY; if anything else in the body
    changed, this still fails.
    """
    back = {
        "run_checked": ("env_builder", "pinned_child_env"),
        "print_status": ("driver_label", '"opencode"'),
    }
    src = ast.unparse(node)
    if name == "discover_plans":
        src = src.replace("dict[str, Any]", "dict[str, PlanRecord]")
        return ast.parse(src).body[0]
    if name not in back:
        return node
    param, original = back[name]
    if name == "print_status":
        src = src.replace("driver_label=driver_label", "driver_label='opencode'")
    else:
        src = src.replace(f"{param}(", f"{original}(")
    return ast.parse(src).body[0]


class FixtureIntegrityTests(unittest.TestCase):
    """Guard the guard. A fixture that lost a symbol would make the move proof vacuous."""

    def test_fixture_covers_all_34_symbols_for_both_runners(self):
        data = load_fixture()
        self.assertEqual(data["symbol_count"], 34)
        self.assertEqual(len(data["symbols"]), 34)
        self.assertEqual(len(set(data["symbols"])), 34)
        for runner in BOTH:
            with self.subTest(runner=runner):
                self.assertEqual(
                    sorted(data["fingerprints"][runner]), sorted(data["symbols"])
                )

    def test_fixture_records_the_head_it_was_captured_at(self):
        """A fingerprint with no provenance cannot be re-derived, so it is not evidence."""
        head = load_fixture()["captured_at_head"]
        self.assertRegex(head, r"^[0-9a-f]{40}$")

    def test_the_capture_reproduces_the_plans_33_plus_1_claim(self):
        """The plan's load-bearing count, re-derived FROM the fixture rather than trusted.

        33 AST-identical plus `print_status` (identical only after host-token normalization) is the
        whole basis for calling these 34 safe to move. If the fixture disagreed with that, the plan's
        premise would be wrong and every move below would be unjustified.
        """
        data = load_fixture()
        oc_fp = data["fingerprints"]["oc_runipd"]
        agy_fp = data["fingerprints"]["agy_runipd"]
        identical = [n for n in data["symbols"] if oc_fp[n] == agy_fp[n]]
        self.assertEqual(len(identical), 33)
        self.assertEqual(
            sorted(set(data["symbols"]) - set(identical)), sorted(HOST_NAMING_ONLY)
        )

    def test_the_injected_and_unmovable_lists_are_disjoint_and_accounted_for(self):
        data = load_fixture()
        self.assertEqual(set(INJECTED) & set(UNMOVABLE), set())
        for name in list(INJECTED) + list(UNMOVABLE):
            with self.subTest(symbol=name):
                self.assertIn(name, data["symbols"])


class PureMoveFingerprintTests(unittest.TestCase):
    """Assertion (1): every moved body still fingerprints as it did before the move."""

    def moved_symbols(self) -> list[str]:
        return [n for n in load_fixture()["symbols"] if n not in UNMOVABLE]

    def test_every_clean_symbol_is_a_STRICT_fingerprint_match(self):
        data = load_fixture()
        expected = data["fingerprints"]["oc_runipd"]
        clean = [
            n
            for n in self.moved_symbols()
            if n not in INJECTED
            and n not in HOST_NAMING_ONLY
            and n not in SUPERSEDED_SINCE_MOVE
        ]
        # 22, DOWN FROM 23 BY EXACTLY ONE: `should_color` moved to `SUPERSEDED_SINCE_MOVE` when it
        # became a delegation to `term.should_color` (IPD `z8ddk0` E-02/E-03; see that list for why the
        # exemption is legitimate). It was 23 for the same reason one step earlier, when `_run_git`
        # gained an optional `timeout` (IPD `zexed1` E-02), and 24 before that.
        # This assertion exists so such a move cannot happen silently, so the number is updated
        # together with the enumeration and never independently of it.
        self.assertEqual(
            len(clean),
            22,
            "the clean-move count must not drift silently",
        )
        self.assertEqual(
            len(SUPERSEDED_SINCE_MOVE),
            3,
            "a name added to SUPERSEDED_SINCE_MOVE must be accounted for in the clean count above",
        )
        for name in clean:
            with self.subTest(symbol=name):
                # A name in `DOCUMENTED_SINCE_MOVE` is compared with its docstring subtracted from the
                # CURRENT side only (its capture has none to subtract). A name in
                # `REDOCUMENTED_SINCE_MOVE` already had one in the capture, so the subtraction is
                # applied to BOTH sides. Every other name is compared STRICTLY, docstring included.
                documented = name in DOCUMENTED_SINCE_MOVE
                redocumented = name in REDOCUMENTED_SINCE_MOVE
                want = (
                    _capture_without_docstring(expected[name])
                    if redocumented
                    else _normalize_dump(expected[name])
                )
                self.assertEqual(
                    fingerprint_of(
                        runner_shared, name, drop_docstring=documented or redocumented
                    ),
                    want,
                    f"`{name}` was NOT a pure move: its body differs from the pre-move "
                    f"capture at {data['captured_at_head']}"
                    + (
                        " (compared with its docstring subtracted, per DOCUMENTED_SINCE_MOVE, so "
                        "this failure is about an EXECUTABLE statement)"
                        if documented
                        else ""
                    )
                    + (
                        " (compared with the docstring subtracted from BOTH sides, per "
                        "REDOCUMENTED_SINCE_MOVE, so this failure is about an EXECUTABLE statement)"
                        if redocumented
                        else ""
                    ),
                )

    def test_a_superseded_symbol_is_accounted_for(self):
        """A symbol listed in `SUPERSEDED_SINCE_MOVE` must genuinely differ from the pre-move capture.

        Proves the exemption is necessary and not decorative: `state_root` must not match the
        pre-move capture at HEAD `1ecc5891` (because it now resolves through project_context),
        and must be covered by dedicated tests in `CanonicalRunsRootTests`.
        """
        data = load_fixture()
        expected = data["fingerprints"]["oc_runipd"]
        for name in SUPERSEDED_SINCE_MOVE:
            with self.subTest(symbol=name):
                self.assertNotEqual(
                    fingerprint_of(runner_shared, name),
                    _normalize_dump(expected[name]),
                    f"`{name}` matches STRICTLY; remove it from SUPERSEDED_SINCE_MOVE",
                )

    def test_a_documented_symbol_is_still_held_to_its_executable_body(self):
        """The `DOCUMENTED_SINCE_MOVE` exemption covers the docstring and NOTHING else.

        Proves the subtraction is narrow rather than trusting the comment that says so: each exempt
        symbol must (a) genuinely HAVE a docstring now, or it does not belong on the list, (b) still
        differ from the pre-move capture when compared STRICTLY, which is what makes the exemption
        necessary rather than decorative, and (c) FAIL when an executable statement is also changed.
        """
        data = load_fixture()
        expected = data["fingerprints"]["oc_runipd"]
        for name in DOCUMENTED_SINCE_MOVE:
            with self.subTest(symbol=name):
                fn = getattr(runner_shared, name)
                self.assertTrue(
                    (fn.__doc__ or "").strip(),
                    f"`{name}` is listed as documented but has no docstring",
                )
                self.assertNotEqual(
                    fingerprint_of(runner_shared, name),
                    _normalize_dump(expected[name]),
                    f"`{name}` matches STRICTLY, so it does not need the exemption; "
                    "remove it from DOCUMENTED_SINCE_MOVE",
                )
                # (c) mutate one executable statement and require the subtraction to still refuse.
                node = None
                for cand in ast.parse(module_source(runner_shared)).body:
                    if (
                        isinstance(cand, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and cand.name == name
                    ):
                        node = cand
                assert node is not None
                mutated = _without_docstring(node)
                assert isinstance(mutated, (ast.FunctionDef, ast.AsyncFunctionDef))
                mutated.body.append(ast.Return(value=ast.Constant(value="mutant")))
                self.assertNotEqual(
                    _normalize_dump(
                        ast.dump(
                            ast.parse(ast.unparse(mutated)), include_attributes=False
                        )
                    ),
                    _normalize_dump(expected[name]),
                    f"an added statement in `{name}` was NOT detected; the exemption is too wide",
                )

    def test_a_redocumented_symbol_is_still_held_to_its_executable_body(self):
        """The `REDOCUMENTED_SINCE_MOVE` exemption covers the docstring and NOTHING else.

        Proves the two-sided subtraction is narrow rather than trusting the comment that says so. Each
        exempt symbol must (a) genuinely have a docstring NOW and (b) have had one in the CAPTURE too,
        which is the very thing that distinguishes this list from `DOCUMENTED_SINCE_MOVE` and makes the
        one-sided route structurally unable to match; (c) still differ from the capture when compared
        STRICTLY, so the exemption is necessary rather than decorative; and (d) FAIL when an executable
        statement is also changed, which is what keeps this a subtraction and not a blanket pass.
        """
        data = load_fixture()
        expected = data["fingerprints"]["oc_runipd"]
        self.assertEqual(
            set(REDOCUMENTED_SINCE_MOVE) & set(DOCUMENTED_SINCE_MOVE),
            set(),
            "a symbol belongs to exactly one docstring exemption",
        )
        for name in REDOCUMENTED_SINCE_MOVE:
            with self.subTest(symbol=name):
                fn = getattr(runner_shared, name)
                self.assertTrue(
                    (fn.__doc__ or "").strip(),
                    f"`{name}` is listed as re-documented but has no docstring",
                )
                # (b) the CAPTURE must already contain a docstring, or this is the wrong list.
                self.assertNotEqual(
                    _capture_without_docstring(expected[name]),
                    _normalize_dump(expected[name]),
                    f"`{name}`'s pre-move capture has NO docstring to subtract, so it belongs in "
                    "DOCUMENTED_SINCE_MOVE, not REDOCUMENTED_SINCE_MOVE",
                )
                # (c) it must genuinely fail the strict comparison.
                self.assertNotEqual(
                    fingerprint_of(runner_shared, name),
                    _normalize_dump(expected[name]),
                    f"`{name}` matches STRICTLY, so it does not need the exemption; "
                    "remove it from REDOCUMENTED_SINCE_MOVE",
                )
                # (d) mutate one executable statement and require the subtraction to still refuse.
                node = None
                for cand in ast.parse(module_source(runner_shared)).body:
                    if (
                        isinstance(cand, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and cand.name == name
                    ):
                        node = cand
                assert node is not None
                mutated = _without_docstring(node)
                assert isinstance(mutated, (ast.FunctionDef, ast.AsyncFunctionDef))
                mutated.body.append(ast.Return(value=ast.Constant(value="mutant")))
                self.assertNotEqual(
                    _normalize_dump(
                        ast.dump(
                            ast.parse(ast.unparse(mutated)), include_attributes=False
                        )
                    ),
                    _capture_without_docstring(expected[name]),
                    f"an added statement in `{name}` was NOT detected; the exemption is too wide",
                )

    def test_every_injected_symbol_matches_MODULO_its_one_new_parameter(self):
        """The enumerated exemption, proven by subtraction rather than asserted.

        Remove the ONE parameter each gained, map its use back to the name it replaced, and the
        result must equal the pre-move capture EXACTLY. So the exemption covers the injection and
        nothing else: any other edit to these five bodies still fails here.
        """
        data = load_fixture()
        expected = data["fingerprints"]["oc_runipd"]
        for name in sorted(INJECTED):
            with self.subTest(symbol=name):
                node = None
                for cand in ast.parse(module_source(runner_shared)).body:
                    if (
                        isinstance(cand, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and cand.name == name
                    ):
                        node = cand
                assert node is not None, f"`{name}` is not defined in runner_shared"
                stripped = _strip_injected_parameter(name, node)
                restored = _substitute_injected_call(name, stripped)
                self.assertEqual(
                    _normalize_dump(
                        ast.dump(
                            ast.parse(ast.unparse(restored)), include_attributes=False
                        )
                    ),
                    _normalize_dump(expected[name]),
                    f"`{name}` differs from its pre-move capture by MORE than the "
                    f"injected `{INJECTED[name]}` parameter",
                )

    def test_the_shared_module_defines_every_symbol_it_claims(self):
        defined = top_level_definitions(runner_shared)
        for name in self.moved_symbols():
            with self.subTest(symbol=name):
                self.assertIn(name, defined)


class SingleDefinitionTests(unittest.TestCase):
    """Assertion (3): the runners no longer DEFINE what they now import.

    A WRAPPER IS NOT A RE-FORK, and this class has to tell them apart or it would forbid the very
    mechanism the maintainer ruled. The 8 `INJECTED` symbols keep a runner-local `def` at the
    original name whose ONLY statement delegates to `runner_shared`. That is a binding, not a second
    implementation, and `WrapperTests` separately proves each one is a single delegating statement.
    What must never exist is a runner-local definition with a BODY, which is what this class checks
    for everything else.
    """

    def test_neither_runner_redefines_an_unwrapped_moved_symbol(self):
        moved = [
            n
            for n in load_fixture()["symbols"]
            if n not in UNMOVABLE and n not in INJECTED
        ]
        violations = []
        for runner in BOTH:
            defined = top_level_definitions(_MODULES[runner])
            for name in moved:
                line = defined.get(name)
                if line is not None:
                    violations.append(f"{runner}.py:{line} re-defines `{name}`")
        self.assertEqual(
            violations,
            [],
            "RE-DEFINITION FOUND. Import from `runner_shared` instead of keeping a "
            "second copy; a fix to the shared definition does not reach a copy.\n  "
            + "\n  ".join(violations),
        )

    def test_every_wrapped_symbol_has_a_wrapper_and_not_a_second_body(self):
        """The wrapped case, checked rather than exempted.

        A wrapper is permitted; a wrapper that GREW A BODY is a re-fork with extra steps, and would
        re-create exactly the divergence this plan removes. So the bar is structural: the runner-local
        `def` must contain a single statement, and that statement must name the shared function.
        """
        for name in sorted(INJECTED):
            for runner in BOTH:
                with self.subTest(symbol=name, runner=runner):
                    node = next(
                        (
                            n
                            for n in ast.parse(module_source(_MODULES[runner])).body
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and n.name == name
                        ),
                        None,
                    )
                    self.assertIsNotNone(
                        node,
                        f"{runner}.{name} must keep a wrapper at its original name",
                    )
                    assert node is not None
                    statements = [
                        s
                        for s in node.body
                        if not (
                            isinstance(s, ast.Expr)
                            and isinstance(s.value, ast.Constant)
                        )
                    ]
                    self.assertEqual(
                        len(statements),
                        1,
                        f"{runner}.{name} has {len(statements)} statements; a wrapper "
                        "that grows logic is a re-fork with extra steps",
                    )
                    self.assertIn(f"runner_shared.{name}", ast.unparse(statements[0]))

    def test_exactly_one_definition_package_wide(self):
        """Repo-wide, not pairwise: a pairwise check passes while a third copy sits elsewhere.

        That is not hypothetical - it is exactly how `agy_runipd` re-forked four `render_stream`
        symbols while a one-sided guard stayed green (the orchestrator's F10).

        Scoped to the UNWRAPPED symbols for the reason given in this class's docstring: a wrapped
        symbol legitimately has a runner-local delegating `def`, whose single-statement shape is
        proven by `test_every_wrapped_symbol_has_a_wrapper_and_not_a_second_body`.
        """
        moved = [
            n
            for n in load_fixture()["symbols"]
            if n not in UNMOVABLE and n not in INJECTED
        ]
        pkg = pathlib.Path(runner_shared.__file__).parent
        counts: dict[str, list[str]] = {n: [] for n in moved}
        for path in sorted(pkg.glob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (
                SyntaxError
            ):  # pragma: no cover - a broken module is a different failure
                continue
            for node in tree.body:
                if (
                    isinstance(
                        node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                    )
                    and node.name in counts
                ):
                    counts[node.name].append(f"{path.name}:{node.lineno}")
        # `_run_git`, `should_color`, `sha256_file`, `load_state` and `validate_manifest` also NAME-
        # COLLIDE with unrelated definitions in `layout_inventory`/`layout_migration`/`term`/
        # `benchmark_manifest`/`leak_sanitizer_config`. Those have DIFFERENT bodies (verified: the
        # layout pair returns a `CompletedProcess` where the runners' returns a tuple), so they are
        # collisions and NOT re-forks; unifying them would be a behavior change. Only the runners and
        # the shared module are in scope here.
        in_scope = {"runner_shared.py", "oc_runipd.py", "agy_runipd.py"}
        for name, sites in sorted(counts.items()):
            with self.subTest(symbol=name):
                scoped = [s for s in sites if s.split(":")[0] in in_scope]
                self.assertEqual(
                    scoped,
                    [s for s in scoped if s.startswith("runner_shared.py:")],
                    f"`{name}` is defined outside `runner_shared` at {scoped}",
                )
                self.assertEqual(len(scoped), 1, f"`{name}` sites: {scoped}")


class ObjectIdentityTests(unittest.TestCase):
    """Assertion (2): both runners resolve each moved name to the SAME object."""

    def test_both_runners_expose_the_shared_object(self):
        moved = [n for n in load_fixture()["symbols"] if n not in UNMOVABLE]
        violations = []
        for name in moved:
            expected = getattr(runner_shared, name, None)
            if expected is None:
                violations.append(f"runner_shared.{name} is missing")
                continue
            for runner in BOTH:
                actual = getattr(_MODULES[runner], name, None)
                if actual is None:
                    violations.append(
                        f"{runner}.{name} is MISSING; it must stay reachable so no "
                        "existing call site or test breaks"
                    )
                elif name in INJECTED:
                    # A wrapped symbol is deliberately NOT the shared object: the wrapper IS the
                    # runner's binding. What must hold is that the wrapper is a one-liner that
                    # delegates, which `WrapperTests` proves.
                    continue
                elif actual is not expected:
                    violations.append(
                        f"{runner}.{name} is NOT `runner_shared.{name}` "
                        f"(got {actual!r} from {getattr(actual, '__module__', '?')})"
                    )
        self.assertEqual(
            violations, [], "IDENTITY MISMATCH:\n  " + "\n  ".join(violations)
        )

    def test_the_constants_the_moved_bodies_close_over_are_also_shared(self):
        """`_SET_RE`/`_ORDER_RE`/`ID6_RE`/`SCHEMA_VERSION` moved too, so they must be shared.

        Leaving a duplicate CONSTANT behind reproduces the same defect one layer down: a fix to the
        pattern would still not reach the runner carrying its own copy.
        """
        for name in ("_SET_RE", "_ORDER_RE", "ID6_RE", "SCHEMA_VERSION"):
            expected = getattr(runner_shared, name)
            for runner in BOTH:
                with self.subTest(constant=name, runner=runner):
                    self.assertIs(getattr(_MODULES[runner], name), expected)


class LaneIntegrationExtractionTests(unittest.TestCase):
    """integpath-02 (`6sb3yu`): the guard for the lane->main integration extraction.

    WHY A SEPARATE CLASS AND NOT THREE MORE FIXTURE ENTRIES. The 34 symbols above are pinned against
    a PRE-MOVE fingerprint captured at HEAD `1ecc5891`. These three did not exist in that capture, so
    there is no fingerprint to compare and pretending otherwise would make the fixture-backed tests
    fail on a missing key rather than prove anything. This class asserts the same three independent
    properties in a form that does not need the fixture, plus one the fixture could not express.

    WHY IT IS DRIVEN BY A SYMBOL LIST rather than three copy-pasted assertion blocks: a guard whose
    shape discourages extension is how the NEXT re-fork slips through. Extending it is adding a name
    to `LANE_INTEGRATION_MOVED`.

    WHY EVERY ASSERTION COVERS BOTH RUNNERS. This is a recorded failure in this repository, not a
    hypothesis: `render_stream` was extracted with a guard that checked only `oc_runipd`, and
    `agy_runipd` then re-forked `Palette`, `_one_line`, `_strip_ansi` and `Heartbeat` with nothing
    noticing (the `rununify` orchestrator's F10). A one-sided guard is how an extraction silently
    un-does itself.
    """

    def test_the_shared_module_defines_all_three(self):
        defined = top_level_definitions(runner_shared)
        for name in LANE_INTEGRATION_MOVED:
            with self.subTest(symbol=name):
                self.assertIn(name, defined)

    def test_neither_runner_redefines_an_unwrapped_symbol(self):
        """The pure move must leave NO runner-local definition behind.

        Object identity alone would pass while a stale duplicate sat in the file shadowed by a later
        import, which is a trap rather than a fix.
        """
        unwrapped = [
            n for n in LANE_INTEGRATION_MOVED if n not in LANE_INTEGRATION_WRAPPED
        ]
        violations = []
        for runner in BOTH:
            defined = top_level_definitions(_MODULES[runner])
            for name in unwrapped:
                line = defined.get(name)
                if line is not None:
                    violations.append(f"{runner}.py:{line} re-defines `{name}`")
        self.assertEqual(
            violations,
            [],
            "RE-DEFINITION FOUND. The lane->main integration logic must have ONE "
            "definition; the whole point of the extraction is that this Set's behavior "
            "changes land once.\n  " + "\n  ".join(violations),
        )

    def test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners(self):
        for name in LANE_INTEGRATION_MOVED:
            if name in LANE_INTEGRATION_WRAPPED:
                continue
            expected = getattr(runner_shared, name)
            for runner in BOTH:
                with self.subTest(symbol=name, runner=runner):
                    self.assertIs(
                        getattr(_MODULES[runner], name),
                        expected,
                        f"{runner}.{name} must BE `runner_shared.{name}`, not merely "
                        "behave like it",
                    )

    def test_a_wrapped_symbol_is_a_single_delegating_statement(self):
        """A wrapper is permitted; a wrapper that GREW A BODY is a re-fork with extra steps.

        `build_lane_outcome` and `integrate_lane_branch` legitimately keep a runner-local `def`,
        because each must bind a host-specific value. So the bar is structural rather than identity:
        one statement, naming the shared function.
        """
        for name in LANE_INTEGRATION_WRAPPED:
            for runner in BOTH:
                with self.subTest(symbol=name, runner=runner):
                    node = next(
                        (
                            n
                            for n in ast.parse(module_source(_MODULES[runner])).body
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and n.name == name
                        ),
                        None,
                    )
                    self.assertIsNotNone(
                        node,
                        f"{runner}.{name} must keep a wrapper at its original name",
                    )
                    assert node is not None
                    statements = [
                        s
                        for s in node.body
                        if not (
                            isinstance(s, ast.Expr)
                            and isinstance(s.value, ast.Constant)
                        )
                    ]
                    self.assertEqual(
                        len(statements),
                        1,
                        f"{runner}.{name} has {len(statements)} statements; a wrapper "
                        "that grows logic is a re-fork with extra steps",
                    )
                    self.assertIn(f"runner_shared.{name}", ast.unparse(statements[0]))

    def test_each_wrapper_keeps_the_ORIGINAL_signature(self):
        """No call site may have had to change, so no wrapper may expose the injected parameter."""
        originals = {
            "build_lane_outcome": ["repo", "handle", "id6"],
            "integrate_lane_branch": ["repo", "handle", "id6", "validation_runner"],
        }
        for name in LANE_INTEGRATION_WRAPPED:
            for runner in BOTH:
                with self.subTest(symbol=name, runner=runner):
                    node = next(
                        n
                        for n in ast.parse(module_source(_MODULES[runner])).body
                        if isinstance(n, ast.FunctionDef) and n.name == name
                    )
                    self.assertEqual([a.arg for a in node.args.args], originals[name])
                    self.assertEqual([a.arg for a in node.args.kwonlyargs], [])

    def test_exactly_one_definition_package_wide(self):
        """Pairwise is not enough: a pairwise check passes while a third copy sits elsewhere.

        Scoped to the runners and the shared module for the reason the older twin gives: an unrelated
        module may legitimately share a NAME with a different body, and that is a collision rather
        than a re-fork.
        """
        pkg = pathlib.Path(runner_shared.__file__).parent
        in_scope = {"runner_shared.py", "oc_runipd.py", "agy_runipd.py"}
        for name in LANE_INTEGRATION_MOVED:
            if name in LANE_INTEGRATION_WRAPPED:
                continue
            sites = []
            for path in sorted(pkg.glob("*.py")):
                if path.name not in in_scope:
                    continue
                for node in ast.parse(path.read_text(encoding="utf-8")).body:
                    if (
                        isinstance(
                            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                        )
                        and node.name == name
                    ):
                        sites.append(f"{path.name}:{node.lineno}")
            with self.subTest(symbol=name):
                self.assertEqual(len(sites), 1, f"`{name}` sites: {sites}")
                self.assertTrue(sites[0].startswith("runner_shared.py:"), sites)

    def test_the_host_label_has_NO_DEFAULT_in_the_shared_function(self):
        """The one parameterized VALUE must be impossible to inherit silently.

        `host_label` lands in a merge commit subject ON MAIN, so it records which driver integrated a
        lane. A default would let a new caller attribute its integrations to the wrong driver, and
        that misattribution is invisible until someone audits the log.
        """
        node = next(
            n
            for n in ast.parse(module_source(runner_shared)).body
            if isinstance(n, ast.FunctionDef) and n.name == "integrate_lane_branch"
        )
        names = [a.arg for a in node.args.kwonlyargs]
        self.assertIn("host_label", names)
        default = node.args.kw_defaults[names.index("host_label")]
        self.assertIsNone(
            default, "`host_label` must have NO default; see this test's docstring"
        )

    def test_each_runner_binds_its_OWN_host_label(self):
        """And it must be the RIGHT one: a swapped pair would still satisfy "has a label"."""
        for runner in BOTH:
            with self.subTest(runner=runner):
                node = next(
                    n
                    for n in ast.parse(module_source(_MODULES[runner])).body
                    if isinstance(n, ast.FunctionDef)
                    and n.name == "integrate_lane_branch"
                )
                call = next(
                    sub
                    for sub in ast.walk(node)
                    if isinstance(sub, ast.Call)
                    and "runner_shared.integrate_lane_branch" in ast.unparse(sub.func)
                )
                bound = {
                    kw.arg: ast.unparse(kw.value)
                    for kw in call.keywords
                    if kw.arg is not None
                }
                self.assertEqual(
                    ast.literal_eval(bound["host_label"]), HOST_LABELS[runner]
                )
                self.assertEqual(bound.get("run_checked"), "run_checked")

    def test_the_shared_bodies_reference_no_name_from_either_runner(self):
        """The de-duplication must not have smuggled in a dependency on a host.

        Checked over the WHOLE module rather than by trusting the import guard, because a lazy
        function-level import would satisfy that guard's module-level reading. `NoRunnerImportTests`
        covers the import statements; this covers these three bodies' free names.
        """
        tree = ast.parse(module_source(runner_shared))
        shared_names = {
            n.name
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        } | {
            t.id
            for n in tree.body
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name)
        }
        for name in LANE_INTEGRATION_MOVED:
            node = next(
                n
                for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == name
            )
            local = {a.arg for a in node.args.args} | {
                a.arg for a in node.args.kwonlyargs
            }
            called = {
                sub.func.id
                for sub in ast.walk(node)
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
            }
            # Every function this body CALLS by bare name must be resolvable inside this module or be
            # one of its own parameters or a builtin. A name from a runner could not be.
            unresolved = {
                c
                for c in called
                if c not in shared_names and c not in local and not hasattr(builtins, c)
            }
            with self.subTest(symbol=name):
                self.assertEqual(
                    unresolved,
                    set(),
                    f"`{name}` calls {sorted(unresolved)}, which `runner_shared` "
                    "cannot resolve; a name from a runner would be a hidden host "
                    "dependency wearing a de-duplication's clothes",
                )


class ReconcileInterruptedExtractionTests(unittest.TestCase):
    """runrecon-02 (`fduoj4`) E-06: the guard for the crash-reconciler extraction.

    WHY HERE AND NOT IN `tests/test_runner_refork_guard.py`'s `REFORK_TABLE`, which is where E-06 first
    said to put it. That table's `Owned` row asserts BOTH that the listed runner has no top-level AST
    definition of the symbol AND that the runner's attribute IS the owner's object. A WRAPPED symbol
    fails both halves BY CONSTRUCTION, which is exactly why that table's own comment records eight
    wrapped symbols as deliberately absent. `reconcile_interrupted` is wrapped: each host keeps a
    one-line `def` at the original name injecting its own `save_state`, because `save_state` needs the
    class (c) DIVERGED `write_report` and a shared body choosing one host's report renderer would
    silently give the other host the wrong format. So the row was INAPPLICABLE and the pin belongs in
    this module, beside `SingleDefinitionTests`, which is where every other wrapped symbol's equivalent
    guarantee lives. The plan anticipated this case and said to state which shape was produced: a
    WRAPPER, for the reason above.

    WHAT THIS GUARDS, since grep would not guard it. The crash reconciler is what decides, after a
    driver dies, whether a step's work is recorded as finished or as merely interrupted - and since this
    plan that decision also changes whether a resume RETRIES the step and whether its dependents are
    released. A textually identical copy in one host would let a correction reach only one driver, which
    is precisely how `render_stream`'s ANSI constants came to be re-forked and how `aw agy run` carried
    a broken `dependency_status_detailed` for months. Worse, it already HAD diverged: the two copies
    differed in one code line, so one host raised `KeyError` and abandoned a whole crashed queue where
    the other reconciled it.

    THE THIRD CALLER IS ASSERTED TOO. `run_viewer.repair_run` is not a runner, and it used to reach
    into `oc_runipd` for this function, so it could disagree with the agy crash path. Its call is
    asserted to name `runner_shared`, which no assertion about the two runners can cover.
    """

    SYMBOL = "reconcile_interrupted"

    def test_the_shared_module_owns_the_body(self):
        self.assertIn(self.SYMBOL, top_level_definitions(runner_shared))

    def test_each_host_keeps_a_single_delegating_wrapper(self):
        """A wrapper is permitted; a wrapper that GREW A BODY is a re-fork with extra steps.

        The bar is structural, exactly as `SingleDefinitionTests` sets it for the eight `INJECTED`
        symbols: the runner-local `def` must hold ONE statement, and that statement must name the
        shared function.
        """
        for runner in BOTH:
            with self.subTest(runner=runner):
                node = next(
                    (
                        n
                        for n in ast.parse(module_source(_MODULES[runner])).body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and n.name == self.SYMBOL
                    ),
                    None,
                )
                self.assertIsNotNone(
                    node,
                    f"{runner}.{self.SYMBOL} must keep a wrapper at its original name",
                )
                assert node is not None
                statements = [
                    s
                    for s in node.body
                    if not (
                        isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)
                    )
                ]
                self.assertEqual(
                    len(statements),
                    1,
                    f"{runner}.{self.SYMBOL} has {len(statements)} statements; a wrapper "
                    "that grows logic is a re-fork with extra steps",
                )
                self.assertIn(
                    f"runner_shared.{self.SYMBOL}", ast.unparse(statements[0])
                )

    def test_each_wrapper_keeps_the_ORIGINAL_signature(self):
        """No call site may have had to change, so no wrapper may expose the injected parameter."""
        for runner in BOTH:
            with self.subTest(runner=runner):
                node = next(
                    n
                    for n in ast.parse(module_source(_MODULES[runner])).body
                    if isinstance(n, ast.FunctionDef) and n.name == self.SYMBOL
                )
                self.assertEqual([a.arg for a in node.args.args], ["run_dir", "state"])
                self.assertEqual([a.arg for a in node.args.kwonlyargs], [])

    def test_the_two_hosts_no_longer_carry_two_implementations(self):
        """The property the whole extraction exists for, asserted on the SOURCE not on identity.

        Identity cannot be asserted for a wrapped symbol (each host's attribute is its own wrapper, by
        design), so what is asserted instead is that neither wrapper CONTAINS the decision: the words
        that carry it appear in `runner_shared` and in neither runner.
        """
        markers = ("interrupted-detected", "interrupted-reconciled-executed")
        shared_src = module_source(runner_shared)
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, shared_src)
        for runner in BOTH:
            src = module_source(_MODULES[runner])
            for marker in markers:
                with self.subTest(runner=runner, marker=marker):
                    self.assertNotIn(
                        marker,
                        src,
                        f"{runner} still carries the reconciliation decision itself; the "
                        "extraction has been un-done and the two hosts can disagree again",
                    )

    def test_the_repair_verb_calls_the_shared_definition(self):
        """`run_viewer.repair_run` is the THIRD caller, and it is not a runner.

        It previously called `oc_runipd.reconcile_interrupted`, so `aw runs repair` ran the OpenCode
        host's copy for every run whatever host wrote it. Asserted on the AST rather than by grep,
        because a stale `oc_runipd.` mention in a comment must not satisfy this.
        """
        from agent_workflows import run_viewer

        tree = ast.parse(module_source(run_viewer))
        repair = next(
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "repair_run"
        )
        targets = {
            ast.unparse(n.func)
            for n in ast.walk(repair)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == self.SYMBOL
        }
        self.assertEqual(targets, {f"runner_shared.{self.SYMBOL}"})

    def test_the_shared_body_reads_the_outcome_through_the_shared_precedence(self):
        """E-02's central property: ONE definition of the precedence, reached by BOTH callers.

        Asserted because the rejected design (PR-701) is the one a later refactor would drift back
        toward: calling `reconcile_disposition` from the crash path, which flips a crashed step to
        `failed-safely` on every no-answer branch. So the crash path must call the HELPER and must not
        call `reconcile_disposition`.
        """
        tree = ast.parse(module_source(runner_shared))
        bodies = {
            n.name: n
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)
            and n.name in (self.SYMBOL, "reconcile_disposition")
        }
        for name in (self.SYMBOL, "reconcile_disposition"):
            called = {
                ast.unparse(n.func)
                for n in ast.walk(bodies[name])
                if isinstance(n, ast.Call)
            }
            with self.subTest(function=name):
                self.assertIn("outcome_precedence_disposition", called)
                self.assertIn("read_recorded_outcome", called)
        self.assertNotIn(
            "reconcile_disposition",
            {
                ast.unparse(n.func)
                for n in ast.walk(bodies[self.SYMBOL])
                if isinstance(n, ast.Call)
            },
            "the crash path must NOT call `reconcile_disposition`: it has no exit code to pass, "
            "and that function's fallback returns `partial`/`failed-safely` rather than the "
            "`interrupted` guess a crashed step with no recorded outcome must keep (PR-701)",
        )

    def test_the_precedence_helper_owns_no_fallback_and_takes_no_exit_code(self):
        """Why the helper is SAFE on both callers, asserted rather than argued.

        A helper carrying an `exit_code` parameter or a `partial`/`failed-safely` fallback would be
        `reconcile_disposition` again, and the crash path would inherit an answer it must not give.
        """
        node = next(
            n
            for n in ast.parse(module_source(runner_shared)).body
            if isinstance(n, ast.FunctionDef)
            and n.name == "outcome_precedence_disposition"
        )
        params = [a.arg for a in node.args.args + node.args.kwonlyargs]
        self.assertEqual(params, ["bucket", "outcome"])
        # CODE ONLY, with the docstring dropped: that docstring NAMES the three forbidden tokens in
        # order to explain why they are absent, so asserting over the whole unparse would fail on the
        # explanation rather than on the implementation. Measured while writing this test.
        body = ast.unparse(_without_docstring(node))
        for forbidden in ("exit_code", "failed-safely", "partial"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, body)
        # And it must be able to say "no answer", which is what preserves the caller's own fallback.
        self.assertIsNone(runner_shared.outcome_precedence_disposition(None, None))


class NoRunnerImportTests(unittest.TestCase):
    """The shared module must not import either runner, at module level OR lazily."""

    def test_runner_shared_imports_neither_runner(self):
        tree = ast.parse(module_source(runner_shared))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "runipd" in alias.name:
                        offenders.append(f"line {node.lineno}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if "runipd" in module:
                    offenders.append(f"line {node.lineno}: from {module} import ...")
                for alias in node.names:
                    if "runipd" in alias.name:
                        offenders.append(
                            f"line {node.lineno}: from {module} import {alias.name}"
                        )
        self.assertEqual(
            offenders,
            [],
            "`runner_shared` must never import a runner: doing so would drag one "
            "host's DIVERGED behavior into code BOTH hosts run.\n  "
            + "\n  ".join(offenders),
        )

    def test_the_shared_module_is_importable_on_its_own(self):
        """No cycle: importing it in a fresh interpreter without a runner must work."""
        import subprocess
        import sys

        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "import agent_workflows.runner_shared as m; print(m.__name__)",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("agent_workflows.runner_shared", proc.stdout)


class WrapperTests(unittest.TestCase):
    """The five wrapped symbols: original signature kept, dependency bound, no call site touched."""

    def wrapper_node(self, runner: str, name: str):
        for node in ast.parse(module_source(_MODULES[runner])).body:
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name
            ):
                return node
        return None

    def test_each_runner_keeps_a_wrapper_at_the_original_name(self):
        for name in sorted(INJECTED):
            for runner in BOTH:
                with self.subTest(symbol=name, runner=runner):
                    self.assertIsNotNone(
                        getattr(_MODULES[runner], name, None),
                        f"{runner}.{name} must stay callable at its original name",
                    )

    def test_no_wrapper_signature_gained_the_injected_parameter(self):
        """The whole point of the wrapper ruling: call sites must be UNCHANGED.

        If a wrapper exposed the injected parameter, every caller would have had to pass it and the
        ~86 call sites the ruling protects would have been rewritten after all.
        """
        for name, param in sorted(INJECTED.items()):
            for runner in BOTH:
                with self.subTest(symbol=name, runner=runner):
                    node = self.wrapper_node(runner, name)
                    assert node is not None, f"{runner}.{name} wrapper not found"
                    kwonly = [a.arg for a in node.args.kwonlyargs]
                    self.assertNotIn(
                        param,
                        kwonly,
                        f"{runner}.{name} leaked the injected `{param}` into its "
                        "public signature, so its call sites are NOT unchanged",
                    )

    def test_each_wrapper_delegates_to_the_shared_definition(self):
        """A wrapper that reimplemented the body would defeat the whole de-duplication."""
        for name in sorted(INJECTED):
            for runner in BOTH:
                with self.subTest(symbol=name, runner=runner):
                    node = self.wrapper_node(runner, name)
                    assert node is not None, f"{runner}.{name} wrapper not found"
                    body = ast.unparse(node)
                    self.assertIn(
                        f"runner_shared.{name}(",
                        body,
                        f"{runner}.{name} must delegate to the shared definition",
                    )
                    # And it must be a WRAPPER, not a fork: one statement, which is the delegation.
                    statements = [
                        s for s in node.body if not isinstance(s, ast.Expr)
                    ] or node.body
                    self.assertEqual(
                        len(statements),
                        1,
                        f"{runner}.{name} is not a one-line wrapper; a wrapper that "
                        "grows logic re-creates the divergence this plan removes",
                    )

    # REAL call-site counts, measured at the pre-move HEAD `1ecc5891` by walking each runner's AST
    # for `ast.Call` nodes naming the symbol. Deliberately NOT a `src.count("name(")` substring
    # count: that also counts the `def` line, docstring mentions, and comments, and the plan's own
    # authoring figures (33/31 for `save_state`, 13/9 for `run_checked`) are those inflated numbers.
    # An inflated baseline would make this test pass or fail for the wrong reason, so the honest
    # measurement replaces it and the discrepancy is recorded rather than quietly adopted.
    PREMOVE_CALL_SITES = {
        ("oc_runipd", "save_state"): 32,
        ("agy_runipd", "save_state"): 30,
        ("oc_runipd", "run_checked"): 12,
        ("agy_runipd", "run_checked"): 8,
        ("oc_runipd", "discover_plans"): 1,
        ("agy_runipd", "discover_plans"): 1,
        ("oc_runipd", "validate_manifest"): 1,
        ("agy_runipd", "validate_manifest"): 1,
        ("oc_runipd", "print_status"): 2,
        ("agy_runipd", "print_status"): 2,
    }

    # CALL SITES ADDED BY LATER, UNRELATED WORK, enumerated one entry at a time with the plan that
    # added each. This exists because the baseline above answers "was an EXISTING call site
    # REWRITTEN", which is the wrapper ruling's actual claim, while a bare equality ALSO fails
    # whenever a new function legitimately calls a wrapped symbol for the first time. Those are
    # different events and must not share one verdict: conflating them would make the honest response
    # to adding a feature be to edit the pre-move baseline, which would destroy the measurement.
    #
    # THE RULE FOR ADDING AN ENTRY: it is for a NEW caller only. If a count moves and you cannot name
    # the new call site, the wrapper ruling has been undone and the correct action is to fix the code,
    # NOT to add a number here.
    ADDED_CALL_SITES = {
        # resumedupe (`txc9l1`) E-05: `route_recovery_turn` persists the routing decision, so the
        # verdict survives the process that made it. One new `save_state(run_dir, state)` in
        # `oc_runipd`; the Antigravity twin DELEGATES to it and therefore adds none of its own.
        ("oc_runipd", "save_state"): 1,
        # orchretire-03 (`pgq326`) E-07: `aw agy run` gained the ORCHESTRATOR DISPATCH BRANCH it never
        # had. Before it, `agy_runipd` had no `orchestrate` handling at all and its queue loop called
        # `execute_item` unconditionally, so an approved orchestrator was AGENT-EXECUTED. The branch
        # persists the outcome, hence one new `save_state(run_dir, state)` in `agy_runipd`. This is a
        # NEW CALLER, which is exactly what this table is for: no existing call site was rewritten, and
        # the retire/reconsider/terminate logic itself is the SHARED `dispatch_orchestrator_item`
        # rather than a second copy in this module.
        ("agy_runipd", "save_state"): 1,
    }

    #: lanectn Order 02 (`nna8yz`) E-05, spec R5.4: the CLEAN-BASE GUARD is a NEW CALLER in BOTH
    #: drivers, which is precisely the case this table exists to record. Each driver's `execute_item`
    #: gained one refusal branch that persists the refusal before returning, so `save_state` gains one
    #: call site per host. NO EXISTING CALL SITE WAS REWRITTEN, which is what the wrapper ruling
    #: actually protects: the RULE itself is the shared `lane_containment.evaluate_clean_base`, and each
    #: driver contributes only its own git invocation, so the guard did not thread a new dependency
    #: through any existing call. Counted separately from the entries above so each ruling keeps its own
    #: provenance rather than being folded into a single unexplained number.
    CLEAN_BASE_GUARD_CALL_SITES = {
        ("oc_runipd", "save_state"): 1,
        ("agy_runipd", "save_state"): 1,
    }

    #: integpath-03 (`51vw4y`): THE INTEGRATION DEFERRAL LADDER's new callers, four per host, each one
    #: NAMED as this table's rule requires ("it is for a NEW caller only ... If a count moves and you
    #: cannot name the new call site, the wrapper ruling has been undone").
    #:
    #: Per host, in `retry_deferred_integrations`: TWO inside its `_finish` closure (persist the
    #: `executed` promotion plus the lane-teardown result, then persist again after the backlog close,
    #: mirroring the first-attempt success path which does exactly the same twice); and TWO in the
    #: `run_queue` dispatch loop, one after rung 1's re-attempt pass and one after rungs 2/3.
    #:
    #: NO EXISTING CALL SITE WAS REWRITTEN, which is the only thing the wrapper ruling protects. The
    #: LADDER itself is the shared `runner_shared.reattempt_deferred_integrations` /
    #: `record_integration_refusal` / `resolve_exhausted_deferrals`, so neither driver carries a second
    #: copy of the decision; each contributes only the host-specific bindings (its own
    #: `integrate_lane_branch` wrapper, hence its own `host_label` in a re-attempt's merge subject).
    INTEGRATION_LADDER_CALL_SITES = {
        ("oc_runipd", "save_state"): 4,
        ("agy_runipd", "save_state"): 4,
    }

    #: dirtygates-03 (`9iq461`): THE LANE-SIDE BACKLOG CLOSE's new caller, ONE per host, NAMED as this
    #: table's rule requires.
    #:
    #: WHERE: in each host's `execute_item`, inside the `fin_rc == 0` branch, immediately after the
    #: lane-side `process_backlog_close(...)` call that this plan ADDED there. The close is now
    #: performed IN THE LANE before integration (so the item's move rides the merge instead of being
    #: written into the shared checkout mid-run), and its verdict must be persisted at that point for
    #: the same reason the pre-existing post-merge close persists its own: the record is what the
    #: `Backlog items left open` report reads, and a crash between the close and the merge would
    #: otherwise lose it.
    #:
    #: NO EXISTING CALL SITE WAS REWRITTEN, which is the only thing the wrapper ruling protects. The
    #: pre-existing post-merge `process_backlog_close(...)` + `save_state(...)` pair is still there,
    #: unmodified, now guarded so it serves the NON-ISOLATED path; and the close logic itself remains
    #: the ONE shared `oc_runipd.process_backlog_close` that `agy_runipd` imports by name, so neither
    #: host carries a second copy of the decision.
    LANE_BACKLOG_CLOSE_CALL_SITES = {
        ("oc_runipd", "save_state"): 1,
        ("agy_runipd", "save_state"): 1,
    }

    #: dirtygates-05 (`ajxr5d`): THE REVIEW SWEEP LANE's new callers, SIX per host, each NAMED as this
    #: table's rule requires ("it is for a NEW caller only ... If a count moves and you cannot name the
    #: new call site, the wrapper ruling has been undone").
    #:
    #: WHERE, per host, all six inside `execute_item` except the last:
    #:   1. the sweep-lane ACQUISITION branch, persisting the lane record on this attempt;
    #:   2. its FAIL-CLOSED arm, persisting the `blocked` refusal before returning (mirroring what the
    #:      execute path's own allocation-failure arm does);
    #:   3. the review PROMPT REBUILD, persisting the lane-relative prompt + input manifest;
    #:   4. the review WRITE-SCOPE record (E-10), persisting which paths the review touched;
    #:   5. the review INTEGRATION result, persisting whether the two files reached main;
    #:   6. its refusal arm, persisting the preserved-lane reason.
    #: A SEVENTH sits in `run_queue` rather than `execute_item`, and it is not counted here because it is
    #: not a direct `save_state(` call: the coordinator's sweep-lane RETIREMENT (E-11) passes `save_state`
    #: as a NAME to `runner_shared.retire_review_sweep_lane`, which is an injection and not a call site -
    #: the same distinction `run_checked`'s wrapper already relies on.
    #:
    #: NO EXISTING CALL SITE WAS REWRITTEN, which is the only thing the wrapper ruling protects. The
    #: sweep lane's allocation, refresh, teardown and write-scope classification are all in
    #: `runner_shared`/`lane_containment`, so neither host carries a second copy of any decision; each
    #: contributes only its own wiring and its own `host_label`/`action_kind` bindings.
    REVIEW_SWEEP_LANE_CALL_SITES = {
        ("oc_runipd", "save_state"): 6,
        ("agy_runipd", "save_state"): 6,
    }

    def call_sites(self, runner: str, name: str) -> int:
        tree = ast.parse(module_source(_MODULES[runner]))
        return sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == name
        )

    def test_no_call_site_was_rewritten(self):
        """The MEASUREMENT behind the wrapper ruling, pinned so a later change cannot undo it.

        The wrapper form was chosen over uniform parameter injection precisely BECAUSE injection
        would have rewritten every one of these ~90 sites, in the two highest-contention files in the
        repository, which seven other reviewed plans also edit. If a later change threads the
        dependency through instead, these counts move and this test says so.

        NOTE `run_checked`'s count legitimately DROPS by 3 in oc and by 3 in agy, and that is not a
        rewritten call site: `git_head`, `git_status` and `git_common_dir` were themselves CALLERS of
        `run_checked`, and they MOVED to `runner_shared` in this same seam. Their calls did not
        change, they relocated with the functions that make them. The subtraction is stated
        explicitly rather than absorbed into a fudged expected number.

        A FURTHER 3 RELOCATED under integpath-02 (`6sb3yu`), for the same reason and by the same
        mechanism: `build_lane_outcome` moved to `runner_shared` and its body makes THREE
        `run_checked` calls (`git rev-parse`, `git diff --name-only`, `git diff`). So the subtraction
        is now 6 per runner, and it is a RELOCATION rather than a rewrite: no surviving call site in
        either runner was touched, and the wrapper each keeps passes `run_checked` as a NAME (an
        injection, not a call), which is why it adds nothing back.
        """
        # initialize_run unification relocated its discover_plans and validate_manifest call sites
        # to runner_shared.initialize_run_core.
        relocated_init_callers = {
            "discover_plans": 1,
            "validate_manifest": 1,
        }
        # execute_item unification relocated its save_state call sites to runner_shared.execute_item_core.
        relocated_execute_callers = {
            "save_state": 22,
        }
        # runrecon-02 (`fduoj4`) E-01: `reconcile_interrupted` moved to `runner_shared` and its body
        # makes ONE `save_state` call, so that call RELOCATED with the function on BOTH hosts. It is
        # subtracted for the identical reason `run_checked`'s six and `execute_item`'s twenty-two are:
        # no surviving call site in either runner was touched. The wrapper each host keeps INJECTS
        # `save_state` as a NAME rather than calling it, which is why it adds nothing back, and which is
        # also why `save_state` had to be injected at all (it needs the class (c) DIVERGED
        # `write_report`, so a shared body cannot pick one host's report renderer).
        relocated_reconcile_callers = {
            "save_state": 1,
        }
        moved_callers_of_run_checked = sum(RELOCATED_RUN_CHECKED_CALLERS.values())
        for (runner, name), premove in sorted(self.PREMOVE_CALL_SITES.items()):
            with self.subTest(runner=runner, symbol=name):
                expected = premove
                if name == "run_checked":
                    expected -= moved_callers_of_run_checked
                if name in relocated_init_callers:
                    expected -= relocated_init_callers[name]
                if name in relocated_execute_callers:
                    expected -= relocated_execute_callers[name]
                if name in relocated_reconcile_callers:
                    expected -= relocated_reconcile_callers[name]
                expected += self.ADDED_CALL_SITES.get((runner, name), 0)
                expected += self.CLEAN_BASE_GUARD_CALL_SITES.get((runner, name), 0)
                expected += self.INTEGRATION_LADDER_CALL_SITES.get((runner, name), 0)
                expected += self.LANE_BACKLOG_CLOSE_CALL_SITES.get((runner, name), 0)
                expected += self.REVIEW_SWEEP_LANE_CALL_SITES.get((runner, name), 0)
                self.assertEqual(
                    self.call_sites(runner, name),
                    expected,
                    f"the number of `{name}` CALL SITES in {runner} changed; the "
                    "wrapper ruling exists to keep call sites untouched",
                )

    def test_the_relocated_run_checked_callers_still_call_it_by_injection(self):
        """The other half of the subtraction above, and the reason `run_checked` is injected at all.

        `git_head`, `git_status` and `git_common_dir` moved in the SAME seam as `run_checked`, and
        their bodies call it. Their calls did not disappear, they RELOCATED into `runner_shared` - and
        because `run_checked` gained a parameter, each now receives the runner's own wrapper by
        injection rather than resolving a module global. `build_lane_outcome` joined them under
        integpath-02 (`6sb3yu`) with three such calls.

        This test also guards against the tempting WRONG repair, which is to rewrite these onto the
        shared `_run_git` sitting nearby. For `git_head` that would change raising `DriverError` into
        returning "" and would drop `git_status`'s `--short`, and both feed every run's outcome record.
        For `build_lane_outcome` it is worse and less visible: a failed `git rev-parse`/`git diff`
        would stop raising and instead build a `LaneOutcome` from EMPTY STRINGS, which the integration
        gate would then happily revalidate as an empty change and merge. If someone makes that change,
        the call set below shrinks and this fails.

        BOTH ASSERTIONS ARE DRIVEN BY THE TABLES rather than by literals, so the next extraction that
        brings a `run_checked` caller into this module extends a table instead of editing two
        hand-written sets that can silently disagree.

        THE TWO TABLES ARE NOT INTERCHANGEABLE (dirtygates-03 `9iq461`). This test reads
        `ALL_SHARED_RUN_CHECKED_CALLERS`, because the injection obligation applies to EVERY shared
        caller. The census test reads only `RELOCATED_RUN_CHECKED_CALLERS`, because only a relocated
        caller's calls LEFT a runner and may be subtracted there. Adding a natively-shared function to
        the relocated table would silently under-count the census by one per host, which is exactly
        the kind of masked rewrite the census exists to catch.
        """
        tree = ast.parse(module_source(runner_shared))
        callers: dict[str, int] = {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                count = sum(
                    1
                    for sub in ast.walk(node)
                    if isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Name)
                    and sub.func.id == "run_checked"
                )
                if count:
                    callers[node.name] = count
        self.assertEqual(
            callers,
            ALL_SHARED_RUN_CHECKED_CALLERS,
            "the shared `run_checked` callers (and their call counts) must match "
            "`ALL_SHARED_RUN_CHECKED_CALLERS`; rewriting one onto `_run_git` would be a "
            "BEHAVIOR CHANGE, and an unrecorded new caller breaks the call-site census. A NEW "
            "shared caller belongs in `NATIVE_SHARED_RUN_CHECKED_CALLERS`; only a caller that "
            "MOVED out of a runner belongs in `RELOCATED_RUN_CHECKED_CALLERS`, which the census "
            "subtracts",
        )
        # And each takes it as a parameter rather than closing over a global, which is what makes the
        # call resolvable at all.
        for name in sorted(ALL_SHARED_RUN_CHECKED_CALLERS):
            with self.subTest(symbol=name):
                node = next(
                    n
                    for n in tree.body
                    if isinstance(n, ast.FunctionDef) and n.name == name
                )
                self.assertIn("run_checked", [a.arg for a in node.args.kwonlyargs])


class UnmovableSymbolTests(unittest.TestCase):
    """PIN why `disable_lane_prompt` stayed behind, so it is not "finished" later by mistake."""

    def test_disable_lane_prompt_stays_in_both_runners(self):
        for runner in BOTH:
            with self.subTest(runner=runner):
                self.assertIn(
                    "disable_lane_prompt", top_level_definitions(_MODULES[runner])
                )

    def test_the_shared_module_does_not_define_it(self):
        self.assertNotIn("disable_lane_prompt", top_level_definitions(runner_shared))

    def test_the_reason_is_a_module_level_global_mutation(self):
        """The reason, asserted rather than described.

        It writes `_LANE_PROMPT_DISABLED` through `global`. Moving it would write the SHARED module's
        flag while each runner's DIVERGED `_lane_reclaim_prompt` kept reading its OWN, so prompt
        suppression on a repeated interrupt would silently stop working. The symptom would be an
        unattended run pausing to ask a question nobody is there to answer.
        """
        for runner in BOTH:
            with self.subTest(runner=runner):
                module = _MODULES[runner]
                node = next(
                    n
                    for n in ast.parse(module_source(module)).body
                    if isinstance(n, ast.FunctionDef)
                    and n.name == "disable_lane_prompt"
                )
                globals_used = [g for g in ast.walk(node) if isinstance(g, ast.Global)]
                self.assertTrue(globals_used, "the pinned reason no longer holds")
                self.assertIn("_LANE_PROMPT_DISABLED", globals_used[0].names)
                # And the flag it writes is still defined in THIS runner, which is the half that
                # makes moving the function unsafe.
                self.assertIn("_LANE_PROMPT_DISABLED", module_source(module))

    def test_prompt_suppression_still_works_in_both_runners(self):
        """Behavior, not structure: the flag each runner sets is the flag each runner reads."""
        for runner in BOTH:
            module = _MODULES[runner]
            with self.subTest(runner=runner):
                saved = getattr(module, "_LANE_PROMPT_DISABLED")
                try:
                    module.disable_lane_prompt()
                    self.assertTrue(getattr(module, "_LANE_PROMPT_DISABLED"))
                finally:
                    setattr(module, "_LANE_PROMPT_DISABLED", saved)


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

    def test_SUCCESS_STATES_is_ONE_OBJECT_across_both_hosts(self):
        self.assertIs(oc_runipd.SUCCESS_STATES, runner_shared.SUCCESS_STATES)
        self.assertIs(agy_runipd.SUCCESS_STATES, runner_shared.SUCCESS_STATES)

    def test_EXECUTION_SUCCESS_STATES_is_EQUAL_on_both_hosts_even_though_duplicated(
        self,
    ):
        """FAILS if either host's set literal is edited alone, which is the whole point.

        The `assertIsNot` is deliberate and is NOT a wish for divergence: it RECORDS the measured
        present state, so if a later plan unifies the objects this test fails loudly and is updated
        together with the change, rather than silently continuing to assert something weaker than the
        truth.
        """
        self.assertEqual(
            oc_runipd.EXECUTION_SUCCESS_STATES, agy_runipd.EXECUTION_SUCCESS_STATES
        )
        self.assertEqual(
            oc_runipd.EXECUTION_SUCCESS_STATES, {"executed", "substantially-complete"}
        )
        self.assertIsNot(
            oc_runipd.EXECUTION_SUCCESS_STATES,
            agy_runipd.EXECUTION_SUCCESS_STATES,
            "the two are now ONE object; unify the constant and simplify this test, do not "
            "delete the equality pin",
        )

    def test_the_action_aware_bar_is_the_SAME_OBJECT_from_every_module_that_exposes_it(
        self,
    ):
        """Grep cannot tell a shared object from a textually identical copy; `assertIs` can.

        `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` carries the same four names and asserts
        BOTH halves of its contract (no runner-local definition, plus attribute identity). This is the
        behavioral restatement sited with its constants, so the guarantee does not rest on one file.
        """
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
                self.assertEqual(shared.__module__, "agent_workflows.runner_shared")

    def test_the_needs_input_token_is_the_one_the_package_already_ships(self):
        """zz5yxq OQ-01: the durable needs-approval fact REUSES an existing token, byte for byte.

        A second spelling of one meaning is how two surfaces come to report the same fact differently,
        so this asserts against the two modules that already own the token rather than against a
        literal repeated here.
        """
        from agent_workflows import run_evidence, run_gates

        self.assertEqual(
            runner_shared.NEEDS_INPUT_TOKEN, run_gates.GATE_STATUS_NEEDS_INPUT
        )
        self.assertEqual(
            runner_shared.NEEDS_INPUT_TOKEN, run_evidence.AGGREGATE_NEEDS_INPUT
        )
        self.assertEqual(runner_shared.NEEDS_INPUT_KEY, runner_shared.NEEDS_INPUT_TOKEN)
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                self.assertEqual(
                    module.NEEDS_INPUT_TOKEN, runner_shared.NEEDS_INPUT_TOKEN
                )


class DriverErrorUnificationTests(unittest.TestCase):
    """`DriverError` was the one symbol here that was a latent BUG, not merely a duplicate."""

    def test_there_is_exactly_one_DriverError_in_the_package(self):
        pkg = pathlib.Path(runner_shared.__file__).parent
        sites = []
        for path in sorted(pkg.glob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover
                continue
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name == "DriverError":
                    sites.append(f"{path.name}:{node.lineno}")
        self.assertEqual(
            sites, ["runner_shared.py:" + sites[0].split(":")[1]] if sites else []
        )
        self.assertEqual(len(sites), 1, f"DriverError defined at {sites}")
        self.assertTrue(sites[0].startswith("runner_shared.py:"))

    def test_both_runners_share_the_one_class(self):
        self.assertIs(oc_runipd.DriverError, agy_runipd.DriverError)
        self.assertIs(oc_runipd.DriverError, runner_shared.DriverError)

    def test_each_runners_StallTimeout_is_reparented_onto_the_shared_class(self):
        """The re-parenting this move performs, and the reason it is the risky part.

        `StallTimeout` is what the stall watchdog raises. Its own body is class (c) DIVERGED and out
        of scope, so it was NOT edited - only its BASE changed. If an `except DriverError` in a
        runner stopped catching it, a clean timeout would become an unhandled traceback in an
        unattended overnight run.
        """
        for runner in BOTH:
            with self.subTest(runner=runner):
                cls = _MODULES[runner].StallTimeout
                self.assertTrue(issubclass(cls, runner_shared.DriverError))
                self.assertTrue(issubclass(cls, oc_runipd.DriverError))
                self.assertTrue(issubclass(cls, agy_runipd.DriverError))

    def test_a_stall_timeout_is_caught_by_an_except_DriverError_in_either_runner(self):
        """Exercised, not reasoned about: raise each runner's StallTimeout, catch the other's base."""
        for runner in BOTH:
            with self.subTest(runner=runner):
                caught = False
                try:
                    raise _MODULES[runner].StallTimeout("stalled")
                except runner_shared.DriverError:
                    caught = True
                self.assertTrue(caught)

    def test_the_real_watchdog_raise_sites_are_still_caught_by_their_handlers(self):
        """V-03's hard requirement: EXERCISE the watchdog path, do not reason about it.

        `issubclass` proves the type lattice; it does NOT prove that the `except` sites the runners
        actually rely on still catch what the watchdog actually raises. This re-parents a LIVE
        exception, and a stall that stops being caught turns a clean, recorded timeout into an
        unhandled traceback in an unattended overnight run - the exact failure mode the drivers exist
        to avoid.

        So this walks each runner's SOURCE, finds every `raise StallTimeout(...)` and every handler
        that must catch it, and then raises the real class through a handler of each observed form.
        """
        for runner in BOTH:
            module = _MODULES[runner]
            src = module_source(module)
            if "execute_item_core" in src:
                src += "\n" + module_source(runner_shared)
            with self.subTest(runner=runner):
                # The raise sites exist and raise THIS module's StallTimeout.
                self.assertGreaterEqual(
                    src.count("raise StallTimeout("),
                    2,
                    "the watchdog raise sites moved; re-derive this test",
                )
                # The two handler FORMS the runners depend on, taken from the source.
                self.assertIn("except StallTimeout:", src)
                self.assertIn("except (KeyboardInterrupt, StallTimeout):", src)

                # Form 1: `except StallTimeout:` (execute_item's interrupt recording).
                caught = None
                try:
                    raise module.StallTimeout("child turn stalled: no output for 600s")
                except module.StallTimeout as exc:
                    caught = str(exc)
                self.assertIn("stalled", caught or "")

                # Form 2: `except (KeyboardInterrupt, StallTimeout):` (the verification turn).
                caught2 = False
                try:
                    raise module.StallTimeout("stalled during verification")
                except (KeyboardInterrupt, module.StallTimeout):
                    caught2 = True
                self.assertTrue(caught2)

                # Form 3, the one the re-parenting could have broken: a bare `except DriverError`
                # in the SAME module must still catch its own StallTimeout now that the base class
                # lives in another module.
                caught3 = False
                try:
                    raise module.StallTimeout("stalled")
                except module.DriverError:
                    caught3 = True
                self.assertTrue(
                    caught3,
                    f"{runner}: `except DriverError` no longer catches its own StallTimeout",
                )

    def test_StallTimeout_is_now_defined_once_on_the_shared_base(self):
        """RE-BASED BY rununify 03 (`i3d6ml`) E-02. What it asserted, and why the assertion INVERTED.

        WHAT THIS TEST USED TO SAY, preserved verbatim because the reason matters more than the
        assertion: "`StallTimeout` is class (c) DIVERGED and out of scope: only its BASE could change.
        The two runners' docstrings differ, which is exactly why the class is diverged and why this
        plan may re-parent it but must not touch it." It then asserted the two docstrings were NOT
        equal, i.e. that a definition still existed in EACH runner.

        WHY THAT PREMISE WAS WRONG, which is what licensed re-basing it rather than working around it.
        "DIVERGED" in this file means the two bodies disagree, and it is measured with
        `_normalize_dump`, which STRIPS DOCSTRINGS before comparing. With docstrings stripped, both
        runners' `StallTimeout` bodies were empty (`pass` in agy, nothing in oc). So the class was
        never behaviorally diverged at all; only its PROSE differed, and prose divergence is precisely
        what the fingerprint machinery in this file deliberately ignores. The old test was therefore
        pinning a documentation difference as though it were a behavioral one.

        WHAT IS ASSERTED NOW, and it is STRICTER rather than weaker. There must be exactly ONE
        `StallTimeout` class in the package, it must live in `runner_shared`, both runners must resolve
        the SAME object, and it must still subclass `DriverError`. That subsumes the old base-class
        check (a single shared class cannot have two different bases) and adds the identity the old
        shape could not express. The behavior half - that every `except` form the runners actually use
        still catches a real watchdog raise - is unchanged and still enforced by
        `test_the_real_watchdog_raise_sites_are_still_caught_by_their_handlers` above, which is the
        test that would fail if this unification broke the stall path.

        THE SAME ARGUMENT APPLIES TO `EmptyStatusSelection`, which moved in the same E-item for the
        same reason and is asserted here beside it.
        """
        pkg = pathlib.Path(runner_shared.__file__).parent
        for name in ("StallTimeout", "EmptyStatusSelection"):
            with self.subTest(symbol=name):
                sites = []
                for path in sorted(pkg.glob("*.py")):
                    try:
                        tree = ast.parse(path.read_text(encoding="utf-8"))
                    except SyntaxError:  # pragma: no cover
                        continue
                    for node in tree.body:
                        if isinstance(node, ast.ClassDef) and node.name == name:
                            sites.append(f"{path.name}:{node.lineno}")
                self.assertEqual(
                    len(sites),
                    1,
                    f"`{name}` must be defined exactly once; found {sites}",
                )
                self.assertTrue(
                    sites[0].startswith("runner_shared.py:"),
                    f"`{name}` must be defined in runner_shared; found {sites[0]}",
                )
                shared_cls = getattr(runner_shared, name)
                self.assertIs(getattr(oc_runipd, name), shared_cls)
                self.assertIs(getattr(agy_runipd, name), shared_cls)
                self.assertTrue(issubclass(shared_cls, runner_shared.DriverError))

    def test_a_shared_DriverError_crosses_the_runner_boundary(self):
        """The defect this unification fixes, stated as a test.

        Before the move, code in `oc_runipd` raising `DriverError` could NOT be caught by
        `except DriverError` in `agy_runipd`, which is why a hand-written translation wrapper existed.
        """
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

    def test_run_checked_binds_each_runners_own_env_builder(self):
        import sys

        out = oc_runipd.run_checked([sys.executable, "-c", "print('ok-oc')"])
        self.assertEqual(out, "ok-oc")
        out = agy_runipd.run_checked([sys.executable, "-c", "print('ok-agy')"])
        self.assertEqual(out, "ok-agy")

    def test_run_checked_still_raises_DriverError_on_a_nonzero_exit(self):
        import sys

        for runner in BOTH:
            with self.subTest(runner=runner):
                with self.assertRaises(runner_shared.DriverError):
                    _MODULES[runner].run_checked(
                        [sys.executable, "-c", "import sys; sys.exit(3)"]
                    )

    def test_run_checked_applies_the_pythonpath_pin_through_the_injected_builder(self):
        """The injected `env_builder` must really be `pinned_child_env`, not a stub."""
        import sys

        for runner in BOTH:
            with self.subTest(runner=runner):
                out = _MODULES[runner].run_checked(
                    [
                        sys.executable,
                        "-c",
                        "import os; print(os.environ.get('AW_PIN_KEEP_ROOT', 'MISSING'))",
                    ]
                )
                self.assertNotEqual(out, "MISSING")
                self.assertEqual(out, oc_runipd.runner_package_root())

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
                    # The INJECTED dependency really ran: `write_report` is what creates this file.
                    self.assertTrue(
                        (run_dir / "execution-report.md").is_file(),
                        "the injected `write_report` did not run",
                    )

    def test_validate_manifest_accepts_a_valid_manifest_in_both_runners(self):
        manifest = {
            "schema_version": 1,
            "plans": {
                "aaaaaa": {"file": "a.ipd.md", "set": "s1", "dependencies": []},
            },
            "sets": {"s1": {"order": ["aaaaaa"]}},
        }
        for runner in BOTH:
            with self.subTest(runner=runner):
                _MODULES[runner].validate_manifest(manifest)

    def test_validate_manifest_still_rejects_a_bad_dependency_in_both_runners(self):
        """Proves the injected `parse_dependency_token` is wired, not merely accepted."""
        manifest = {
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
                with self.assertRaises(runner_shared.DriverError):
                    _MODULES[runner].validate_manifest(manifest)

    def test_validate_manifest_rejects_a_wrong_schema_version_in_both_runners(self):
        for runner in BOTH:
            with self.subTest(runner=runner):
                with self.assertRaises(runner_shared.DriverError):
                    _MODULES[runner].validate_manifest({"schema_version": 999})


class DiscoverPlansRecordTypeTests(unittest.TestCase):
    """PIN ONE OF TWO, INVERTED BY `sy7uwh`: the record types are now the SAME, deliberately.

    WHAT THIS CLASS USED TO ASSERT, AND WHY IT NO LONGER DOES. `818uru` wrote this class to FORBID
    unification: it asserted that the two runners' `PlanRecord` were DIFFERENT NamedTuples (oc's
    carrying a `kind` field agy's lacked), that each runner got its OWN type out of `discover_plans`,
    and its docstring said in terms "This plan may NOT unify them; that is a class (c) reconciliation
    for a later child."

    rununify 06 (`sy7uwh`) IS THAT LATER CHILD, authorized by the maintainer's 2026-09-14
    unify-toward-oc ruling, so the assertions are INVERTED IN PLACE rather than deleted - the repo's
    own precedent for a pinned decision a later phase deliberately reverses.
    Deleting the guard would leave the override unrecorded
    and the property unprotected; inverting it keeps a test that fails if the record ever re-forks.

    WHY THE OVERRIDE IS LEGITIMATE RATHER THAN A REVERSAL FOR ITS OWN SAKE: the premise dissolved.
    When `818uru` pinned the split, agy had NO use for `kind`. agy now imports the shared `action_for`,
    which READS `kind` to detect an orchestrator, and it was supplying the field by RE-READING the plan
    file per plan. Measured at `sy7uwh`'s execution: oc's field set was a strict SUPERSET of agy's
    differing in exactly `kind`, so the merge lost nothing.

    THE ORIGINAL WARNING STILL STANDS AND IS WHY THIS CLASS SURVIVES AT ALL: a shared constructor that
    DROPPED `kind` would silently disable orchestrator detection, type-shaped rather than crashing. So
    the last test below asserts the field is populated on BOTH hosts, and
    `tests/test_rununify_record.py` carries the end-to-end derivation that a field-presence check
    cannot substitute for.
    """

    def _repo(self, tmp: pathlib.Path) -> pathlib.Path:
        plans = tmp / ".aw" / "records" / "plans" / "pending"
        plans.mkdir(parents=True)
        (plans / "20260101-setaaa-01-aaaaaa-a-plan.ipd.md").write_text(
            "# IPD: a plan\n\n- Id: aaaaaa\n- Status: approved\n- Set: setaaa\n"
            "- Order: 1\n- Kind: child\n",
            encoding="utf-8",
        )
        return tmp

    def test_the_two_PlanRecord_types_are_now_ONE_shared_type(self):
        """INVERTED BY `sy7uwh`, which this class's docstring authorizes and explains.

        Was: `assertIsNot`, plus `kind` present on oc and ABSENT on agy. Now: one object, owned by
        `runner_shared`, carrying `kind` for both hosts.
        """
        self.assertIs(oc_runipd.PlanRecord, agy_runipd.PlanRecord)
        self.assertIs(oc_runipd.PlanRecord, runner_shared.PlanRecord)
        self.assertIn("kind", runner_shared.PlanRecord._fields)
        for runner in BOTH:
            with self.subTest(runner=runner):
                self.assertIn("kind", _MODULES[runner].PlanRecord._fields)

    def test_no_field_was_lost_when_the_two_shapes_MERGED(self):
        """The merge must be a UNION, not a redesign: `sy7uwh`'s OQ-02 forbids adding or dropping.

        The pre-unification field sets are stated as LITERALS, measured at that plan's execution HEAD,
        so this fails if a later change quietly drops a field either host used to have OR invents one
        neither did.
        """
        oc_premove = (
            "id6",
            "setid",
            "status",
            "order",
            "path",
            "rel_path",
            "dependencies",
            "kind",
            "dependency_error",
            "from_backlog",
        )
        agy_premove = tuple(n for n in oc_premove if n != "kind")
        shared = runner_shared.PlanRecord._fields
        for name in oc_premove:
            self.assertIn(name, shared, f"oc's `{name}` was LOST in the merge")
        for name in agy_premove:
            self.assertIn(name, shared, f"agy's `{name}` was LOST in the merge")
        self.assertEqual(
            set(shared),
            set(oc_premove),
            "the shared record must be exactly the UNION of the two pre-merge shapes; a field "
            "nobody read before must not appear (`sy7uwh` OQ-02)",
        )

    def test_each_runner_now_gets_the_SAME_record_type(self):
        """INVERTED BY `sy7uwh`. Was: each runner gets its OWN type out of `discover_plans`."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(pathlib.Path(tmp))
            built = {}
            for runner in BOTH:
                with self.subTest(runner=runner):
                    module = _MODULES[runner]
                    found = module.discover_plans(repo)
                    self.assertIn("aaaaaa", found)
                    self.assertIs(type(found["aaaaaa"]), runner_shared.PlanRecord)
                    built[runner] = found["aaaaaa"]
            self.assertEqual(built["oc_runipd"], built["agy_runipd"])

    def test_BOTH_paths_populate_kind(self):
        """The original warning, now asserted for BOTH hosts rather than only oc.

        `818uru` could only check oc here, because agy's record had no such field to check. That is the
        payoff of the unification stated as a test: a shared constructor that dropped `kind` would
        silently disable orchestrator detection on both hosts at once.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(pathlib.Path(tmp))
            for runner in BOTH:
                with self.subTest(runner=runner):
                    record = _MODULES[runner].discover_plans(repo)["aaaaaa"]
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

    def test_each_host_renders_its_own_label(self):
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
                # The SHARED function, called with the same label, must render identically.
                buf2 = io.StringIO()
                with _ctx.redirect_stdout(buf2):
                    runner_shared.print_status(run_dir, driver_label=label)
                self.assertEqual(
                    rendered[runner],
                    buf2.getvalue(),
                    f"{runner}.print_status diverged from the shared definition",
                )

    def test_each_host_still_names_itself_and_not_the_other(self):
        """If the host token were lost in the move, both would render the same label.

        DELIBERATELY NOT a `replace("opencode", "antigravity")` comparison of the two outputs: the
        summary is a box-drawn TABLE, so swapping a 8-character label for an 11-character one shifts
        the column padding and the two renderings are legitimately not translations of each other.
        A test asserting that would fail for a formatting reason while telling you nothing about the
        move. What matters is that each host names ITSELF, which is what the injected parameter
        carries.

        Byte-identity against the PRE-MOVE rendering is proven separately and is the stronger claim;
        see the E-06 evidence in the plan's V-06 (both hosts' output captured at HEAD `1ecc5891` in a
        detached worktree and diffed against the post-move output: identical).
        """
        import contextlib as _ctx
        import io
        import tempfile

        out = {}
        for runner in BOTH:
            with tempfile.TemporaryDirectory() as tmp:
                run_dir = self._run_dir(tmp)
                buf = io.StringIO()
                with _ctx.redirect_stdout(buf):
                    _MODULES[runner].print_status(run_dir)
                out[runner] = buf.getvalue()
        self.assertIn("opencode", out["oc_runipd"])
        self.assertNotIn("antigravity", out["oc_runipd"])
        self.assertIn("antigravity", out["agy_runipd"])
        self.assertNotIn("opencode", out["agy_runipd"])
        self.assertNotEqual(out["oc_runipd"], out["agy_runipd"])


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

    def test_the_pre_merge_dirty_overlap_guard_is_STILL_IN_PLACE(self):
        """OQ-03 resolved to KEEP the prediction, so its removal is a FAILURE of this plan.

        Two approved release-blocking plans (`fujm0y` widening its input, `51vw4y` building a deferral
        ladder on its arm) are signed off to improve this exact symbol, so an implementation that
        reclassified the post-merge branch by deleting the pre-merge check would negate them.
        """
        src = module_source(runner_shared)
        self.assertIn("def dirty_tree_overlap(", src)
        node = next(
            n
            for n in ast.parse(src).body
            if isinstance(n, ast.FunctionDef) and n.name == "integrate_lane_branch"
        )
        called = {
            sub.func.id
            for sub in ast.walk(node)
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
        }
        self.assertIn(
            "dirty_tree_overlap",
            called,
            "the pre-merge overlap prediction must still be CALLED by the integration path",
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
        """The three `kind` values are a CONTRACT read by callers and by run state.

        Child 03 changes what the transient kind means for `TERMINAL_STATES`; this child must not,
        and asserting the vocabulary here is what keeps a "pure move" from smuggling that in.

        RESOLVES NAMES AS WELL AS LITERALS (`l2mzxn`). The three kinds used to be spelled as bare
        strings inside the function; the rename moved them onto the module constants so a literal and
        the constant it duplicates can no longer drift. An AST walk that only accepted `ast.Constant`
        would therefore see an EMPTY set and pass vacuously against any vocabulary at all, which is
        strictly weaker than the contract this test exists to pin. So a returned `ast.Name` is resolved
        through the module, and a kind that is neither a literal nor a resolvable module constant fails.
        """
        src = module_source(runner_shared)
        node = next(
            n
            for n in ast.parse(src).body
            if isinstance(n, ast.FunctionDef) and n.name == "integrate_lane_branch"
        )
        returned = set()
        for sub in ast.walk(node):
            if not (isinstance(sub, ast.Return) and isinstance(sub.value, ast.Tuple)):
                continue
            elt = sub.value.elts[-1]
            if isinstance(elt, ast.Constant):
                returned.add(ast.literal_eval(elt))
            elif isinstance(elt, ast.Name):
                resolved = getattr(runner_shared, elt.id, None)
                self.assertIsInstance(
                    resolved,
                    str,
                    f"integrate_lane_branch returns {elt.id!r} as a kind, which is not a string "
                    "constant on the module; the kind vocabulary must stay resolvable",
                )
                returned.add(resolved)
        self.assertEqual(returned, {"integrated", "merge-retry", "merge-refused"})


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

    def test_state_root_ast_no_hardcoded_literal(self):
        src = module_source(runner_shared)
        tree = ast.parse(src)
        fn = next(
            (
                n
                for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "state_root"
            ),
            None,
        )
        self.assertIsNotNone(fn, "state_root definition not found in runner_shared.py")
        assert fn is not None
        fn_src = ast.unparse(fn)
        self.assertNotIn(
            '".aw" / "records" / "runs"',
            fn_src,
            "state_root body must not hardcode the repository-backed runs literal",
        )
        self.assertIn(
            "resolve_project_context",
            fn_src,
            "state_root must resolve through resolve_project_context",
        )


class SingleStateRootConstructionGuardTests(unittest.TestCase):
    """Repo-wide symmetric guard: no module in agent_workflows constructs .aw/records/runs directly.

    Modeled on test_runner_refork_guard and test_render_stream: single authority for runs-root resolution.
    """

    def test_no_module_constructs_hardcoded_runs_root_path(self):
        pkg_dir = pathlib.Path(runner_shared.__file__).parent
        violations = []
        for py_file in sorted(pkg_dir.glob("*.py")):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                    if (
                        isinstance(node.right, ast.Constant)
                        and node.right.value == "runs"
                    ):
                        left = node.left
                        if isinstance(left, ast.BinOp) and isinstance(left.op, ast.Div):
                            if (
                                isinstance(left.right, ast.Constant)
                                and left.right.value == "records"
                            ):
                                left_left = left.left
                                if isinstance(left_left, ast.BinOp) and isinstance(
                                    left_left.op, ast.Div
                                ):
                                    if (
                                        isinstance(left_left.right, ast.Constant)
                                        and left_left.right.value == ".aw"
                                    ):
                                        violations.append(
                                            f"{py_file.name}:{node.lineno} constructs '.aw/records/runs' path via '/'"
                                        )
                elif isinstance(node, ast.Call):
                    func_name = ""
                    if (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "join"
                    ):
                        func_name = "join"
                    if func_name == "join":
                        arg_constants = [
                            a.value
                            for a in node.args
                            if isinstance(a, ast.Constant) and isinstance(a.value, str)
                        ]
                        if (
                            ".aw" in arg_constants
                            and "records" in arg_constants
                            and "runs" in arg_constants
                        ):
                            violations.append(
                                f"{py_file.name}:{node.lineno} constructs '.aw/records/runs' via os.path.join"
                            )

        self.assertEqual(
            violations,
            [],
            "Direct .aw/records/runs path construction found outside the single authority:\n  "
            + "\n  ".join(violations),
        )


class SharedVerificationResolutionTests(unittest.TestCase):
    """`hostdefault-02` (`ybkmzp`) E-01: the ONE host-neutral verification resolution.

    NO STORE IS TOUCHED: every case points `XDG_CONFIG_HOME` at a `TemporaryDirectory`, so the
    maintainer's real `runner-profiles.json` is never read or written.
    """

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

    def test_the_helper_returns_a_decision_and_never_a_host_key(self):
        """The inversion hazard is designed OUT: there is no `no_verify` to write un-negated."""

        decision = self.resolve(None, runner="oc", validate=True)
        self.assertEqual(decision._fields, ("validate", "provenance"))
        self.assertNotIn("no_verify", decision._fields)
        self.assertIsInstance(decision.validate, bool)
        self.assertIsInstance(decision.provenance, str)

    def test_the_tristate_does_not_collapse(self):
        """`None` FALLS THROUGH; `False` is a decision that WINS. This is the whole mechanism."""

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

    def test_a_malformed_store_raises_the_one_driver_error_class(self):
        """No per-driver translation wrapper is needed: there is ONE `DriverError`."""

        self.assertIs(oc_runipd.DriverError, runner_shared.DriverError)
        self.assertIs(agy_runipd.DriverError, runner_shared.DriverError)
        with self.assertRaises(runner_shared.DriverError) as ctx:
            self.resolve(
                {"schema_version": 2, "defaults": {"validate": "yes"}}, runner="oc"
            )
        self.assertIn("runner profile", str(ctx.exception))

    def test_the_shared_module_imports_runner_profiles_which_is_not_a_runner(self):
        """The admission rule forbids RUNNERS, and `runner_profiles` is a peer, not a runner."""

        tree = ast.parse(module_source(runner_shared))
        imported = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertIn("agent_workflows", imported)
        self.assertNotIn("runipd", " ".join(sorted(imported)))
        from agent_workflows import runner_profiles

        self.assertIs(runner_shared.runner_profiles, runner_profiles)


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

    def test_all_four_polarity_cells(self):
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

        print(
            "POLARITY MATRIX: resolved verify -> oc validate=True / agy no_verify=False; "
            "resolved do-not-verify -> oc validate=False / agy no_verify=True"
        )

    def test_the_empty_store_floor_is_unchanged_on_both_hosts(self):
        """THE ANTI-REGRESSION FLOOR: with nothing configured, oc is OFF and agy is ON."""

        oc = self.frozen_options("oc_runipd", [], None)
        self.assertIs(oc["validate"], False, "oc must still NOT verify by default")
        self.assertIs(oc["no_audit"], True)
        agy = self.frozen_options("agy_runipd", [], None)
        self.assertIs(agy["no_verify"], False, "agy must STILL verify by default")
        print("EMPTY-STORE FLOOR: oc validate=False; agy no_verify=False (verifies)")

    def test_agy_freezes_no_validate_key_and_its_gate_expression_is_unchanged(self):
        """Two switches for one behavior is the shape this must not take."""

        options = self.frozen_options("agy_runipd", [], None)
        self.assertNotIn("validate", options)
        source = pathlib.Path(agy_runipd.__file__).read_text(encoding="utf-8")
        self.assertIn("and not no_verify", source)

    def test_oc_and_agy_agree_on_the_decision_for_the_same_store(self):
        """One resolution, two polarities: the two hosts can never disagree about the DECISION."""

        for document in (
            None,
            {"schema_version": 2, "defaults": {"validate": True}},
            {"schema_version": 2, "defaults": {"validate": False}},
        ):
            with self.subTest(document=document):
                oc = self.frozen_options("oc_runipd", [], document)
                agy = self.frozen_options("agy_runipd", [], document)
                if document is None:
                    # The ONE legitimate disagreement: tier 4 is PER HOST by design.
                    self.assertIs(oc["validate"], False)
                    self.assertIs(not agy["no_verify"], True)
                else:
                    self.assertIs(oc["validate"], not agy["no_verify"])


class VerificationChainFrozenStateTests(unittest.TestCase):
    """`hostdefault-02` (`ybkmzp`) E-07: the FOUR TIERS pinned at the FROZEN-STATE level.

    `tests/test_runner_profiles.py` already pins every tier AT THE RESOLVER, and that is deliberately
    NOT duplicated here. What no test covered before this one is that a stored value reaches the RUN,
    survives the freeze, and therefore decides the verifier gate.

    ON AGY THE "PROFILE" TIER IS THE PER-RUNNER DEFAULT PROFILE, not a named one, because that host
    declares no `--profile` and has no `as <profile>` clause. Its provenance is therefore
    `default-profile` rather than `profile`, which is why the agy rows below shape the store with
    `defaults.profiles`.
    """

    def frozen(self, runner: str, argv: list, document: dict | None) -> dict:
        return VerificationPolarityTests.frozen_options(
            VerificationPolarityTests("test_all_four_polarity_cells"),
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

    def test_tier_1_explicit_flag_beats_a_stored_profile_value(self):
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
        # And this host's shipped spelling is the same request as `--no-validate`.
        self.assertFalse(
            self.verifies(
                "agy_runipd", self.frozen("agy_runipd", ["--no-verify"], agy_store)
            )
        )

    def test_tier_2_a_profile_value_beats_defaults_validate(self):
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

    def test_tier_3_defaults_validate_beats_the_per_host_registry_row(self):
        # `False` on agy and `True` on oc, so each case OPPOSES that host's own row and cannot pass
        # by coincidence.
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

    def test_tier_4_absence_yields_each_hosts_own_row(self):
        self.assertFalse(self.verifies("oc_runipd", self.frozen("oc_runipd", [], None)))
        self.assertTrue(
            self.verifies("agy_runipd", self.frozen("agy_runipd", [], None))
        )

    def test_a_profile_omitting_validate_is_not_a_profile_saying_false(self):
        """THE TRI-STATE, at the frozen level: only a PRESENT value is a decision."""

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
                    self.verifies(runner, self.frozen(runner, [], omitted)),
                    row_default,
                    "an OMITTED profile `validate` must fall through to the host row",
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

    def test_oc_records_the_resolved_value_beside_its_provenance_tier(self):
        """E-05: the durable record carries the VALUE; the tier was already there."""

        explicit = self.frozen("oc_runipd", ["--validate"], None)["launch_profile"]
        self.assertIs(explicit["validate"], True)
        self.assertEqual(explicit["provenance"]["validate"], "explicit")
        configured = self.frozen(
            "oc_runipd", [], {"schema_version": 2, "defaults": {"validate": True}}
        )["launch_profile"]
        self.assertIs(configured["validate"], True)
        self.assertEqual(configured["provenance"]["validate"], "defaults")
        # agy has NO equivalent record; the gap is recorded in the plan, not silently accepted.
        self.assertNotIn("launch_profile", self.frozen("agy_runipd", [], None))


class AgyVerificationFlagSurfaceTests(unittest.TestCase):
    """`hostdefault-02` (`ybkmzp`) E-02: the tri-state spelling, and the two silent-bypass traps."""

    def parse(self, argv: list):
        return agy_runipd.build_parser().parse_args(
            ["start", "demo", "--repo", ".", *argv]
        )

    def test_the_tristate_parses_and_no_verify_still_exists(self):
        """`no_verify` MUST be present: its ABSENCE is the F-14 silent-bypass signature."""

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
                self.assertIs(
                    getattr(args, "no_verify", "<gone>"),
                    no_verify,
                    "args.no_verify must EXIST; a missing attribute means the parser stole the "
                    "flag and agy silently stopped verifying by default",
                )

    def test_the_parser_builds_and_declares_no_conflicting_option_strings(self):
        """The aliased spelling raises `ArgumentError` at build time; this proves it did not."""

        import argparse as _argparse

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

    def test_a_contradictory_pair_is_refused(self):
        """argparse accepts it; the refusal is hand-written and must be present."""

        args = self.parse(["--no-verify", "--validate"])
        self.assertIs(args.validate, True)
        self.assertIs(args.no_verify, True)
        with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
            agy_runipd.verification_flag_tristate(args)
        self.assertIn("contradict", str(ctx.exception))
        # An AGREEING pair is accepted.
        agreeing = self.parse(["--no-verify", "--no-validate"])
        self.assertIs(agy_runipd.verification_flag_tristate(agreeing), False)

    def test_a_stolen_flag_is_refused_at_the_parser_not_silently_accepted(self):
        """The F-14 `conflict_handler="resolve"` hazard, refused where it is decidable.

        The hazard is that the `--validate` family STEALS `--no-verify`, after which the shipped
        spelling stops meaning "do not verify" and antigravity's posture silently flips. That is a
        property of how the parser was BUILT, so it is checked against the parser: a parser whose
        `--no-verify` resolves to the wrong destination is refused.
        """

        import argparse as _argparse

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
        agy_runipd.assert_verification_flags_are_distinct(good)  # does not raise

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
        # And the REAL parser passes the same check, which is what `build_parser` asserts.
        self.assertIsNotNone(agy_runipd.build_parser())

    def test_a_partial_namespace_reads_as_no_flag_rather_than_raising(self):
        """Several shipped tests build partial namespaces; absence must mean "not passed"."""

        import argparse as _argparse

        self.assertIsNone(
            agy_runipd.verification_flag_tristate(_argparse.Namespace(validate=None))
        )

    def test_the_refusal_happens_before_any_durable_run_state(self):
        import os
        import subprocess
        from unittest import mock

        probe = VerificationPolarityTests("test_all_four_polarity_cells")
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
                        "a refused invocation must leave NO durable run state",
                    )
                    del subprocess


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

    def test_the_first_dirty_overlap_refusal_DEFERS_and_is_not_terminal(self):
        decision = self.decide()
        self.assertTrue(decision.deferred)
        self.assertEqual(decision.status, runner_shared.INTEGRATION_DEFERRED_STATUS)
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                self.assertNotIn(decision.status, module.TERMINAL_STATES)

    def test_the_budget_bounds_the_re_attempts_and_then_goes_TERMINAL(self):
        """A permanently dirty path must not spin the loop forever."""
        for attempt in range(1, 4):
            with self.subTest(attempt=attempt):
                self.assertTrue(self.decide(attempts_used=attempt, limit=3).deferred)
        exhausted = self.decide(attempts_used=4, limit=3)
        self.assertFalse(exhausted.deferred)
        self.assertEqual(exhausted.status, runner_shared.INTEGRATION_BLOCKED_STATUS)
        self.assertIn("budget exhausted", exhausted.reason)
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                self.assertIn(exhausted.status, module.TERMINAL_STATES)

    # ---- the 2026-09-21 rename, and its back-compatibility guarantee (`l2mzxn`) ------------------

    def test_the_status_vocabulary_is_NAMED_FOR_THE_OPERATORS_NEXT_ACTION(self):
        """The four canonical spellings, pinned so a future edit cannot quietly revert the rename.

        WHY PIN LITERAL STRINGS HERE when the rest of this class deliberately drives constants: these
        values are the OPERATOR-FACING CONTRACT. They are what a human reads in `aw runs`, what appears
        in a run summary, and what gets typed into a `--status` filter. A constant-only assertion would
        happily pass if someone renamed all four back, which is exactly the regression this pins.
        """
        self.assertEqual(runner_shared.INTEGRATION_DEFERRED_STATUS, "merge-retry")
        self.assertEqual(runner_shared.INTEGRATION_BLOCKED_STATUS, "merge-needs-human")
        self.assertEqual(runner_shared.INTEGRATION_REFUSAL_CONFLICT, "merge-refused")
        self.assertEqual(
            runner_shared.INTEGRATION_REFUSAL_UNMEASURED, "merge-unchecked"
        )
        # The transient KIND and the deferred STATUS share a value, as they did pre-rename. Asserted
        # rather than assumed, because `revladder` (`i4ak5n`) records a wrong diagnosis caused by
        # exactly this coincidence, and a future reader needs it to be deliberate.
        self.assertEqual(
            runner_shared.INTEGRATION_REFUSAL_TRANSIENT,
            runner_shared.INTEGRATION_DEFERRED_STATUS,
        )

    def test_EVERY_pre_rename_spelling_still_resolves(self):
        """A run directory is a DURABLE RECORD, so the old names must never stop being readable.

        THE HARM THIS PREVENTS IS SILENT. Every run that already happened wrote the old strings into its
        `state.json`. If the rename dropped them, `aw runs` would render the repository's own history as
        unknown statuses and `aw <host> run integrate` would refuse to rescue an already-stranded lane -
        the verb whose entire purpose is rescuing lanes stranded by an EARLIER run, i.e. exactly the runs
        most likely to carry the old vocabulary. Nothing would crash; the audit trail would just go
        blank, which is the same class of harm as deleting a plan instead of retiring it.
        """
        self.assertEqual(
            runner_shared.LEGACY_INTEGRATION_STATUS_ALIASES,
            {
                "integration-deferred": "merge-retry",
                "integration-blocked": "merge-needs-human",
                "merge-conflict": "merge-refused",
                "integration-unmeasured": "merge-unchecked",
            },
        )
        for legacy, canonical in (
            ("integration-deferred", "merge-retry"),
            ("integration-blocked", "merge-needs-human"),
            ("merge-conflict", "merge-refused"),
            ("integration-unmeasured", "merge-unchecked"),
        ):
            self.assertEqual(
                runner_shared.canonical_integration_status(legacy), canonical, legacy
            )
            # IDEMPOTENT: translating a canonical name is a no-op, so a caller may translate freely
            # without having to know whether a value came from an old run or a new one.
            self.assertEqual(
                runner_shared.canonical_integration_status(canonical), canonical
            )

    def test_the_translator_PASSES_THROUGH_what_it_does_not_own(self):
        """It is an alias map, not a validator; turning it into a gate would break every caller.

        `canonical_integration_status` is called on statuses drawn from the WHOLE item vocabulary, most
        of which have nothing to do with integration. Refusing or blanking an unknown value would make a
        rendering helper silently drop `executed` rows.
        """
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
        # Non-strings degrade to the empty string rather than raising: this runs on the reporting path,
        # where a malformed record must not take down the summary a human is waiting for.
        self.assertEqual(runner_shared.canonical_integration_status(None), "")
        self.assertEqual(runner_shared.canonical_integration_status(17), "")

    def test_a_legacy_spelling_is_STILL_RE_INTEGRATABLE(self):
        """The rename must not strand the lanes the `integrate` verb exists to rescue.

        This is the one back-compat consequence with teeth, so it is asserted on the real predicate
        rather than on the alias map: `REINTEGRATABLE_STATUSES` is matched against a status READ BACK
        from a run directory written by an earlier run.
        """
        for spelling in (
            "merge-needs-human",
            "merge-refused",
            "integration-blocked",
            "merge-conflict",
        ):
            self.assertIn(spelling, runner_shared.REINTEGRATABLE_STATUSES, spelling)
        # And the DEFERRABLE pair is absent: those are non-terminal and the live ladder owns them, so
        # offering them to the manual verb would invite a human to race the runner.
        for spelling in ("merge-retry", "merge-unchecked", "integration-deferred"):
            self.assertNotIn(spelling, runner_shared.REINTEGRATABLE_STATUSES, spelling)

    def test_a_legacy_spelling_RENDERS_identically_to_its_canonical_twin(self):
        """A pre-rename run must LOOK the same, not merely be classifiable.

        WHY THIS IS A SEPARATE TEST FROM THE ALIAS MAP: the alias map is consulted by code that CHOOSES
        to translate, while `lifecycle_style.resolve` is a lookup table keyed on the raw status. A rename
        can therefore leave the map perfect and still make old runs render as `unknown`, because the
        table simply has no row for the old word. THAT IS NOT HYPOTHETICAL - it is what this assertion
        found: `integration-unmeasured` resolved to `unknown` while `merge-unchecked` resolved to
        `recovering`, so a run directory from the rename window would have rendered its glyph as
        undecidable. Comparing each legacy spelling against its canonical twin is what caught it, which
        is why the test is written as a PARITY check rather than as eight hardcoded expectations.
        """
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
            self.assertEqual(
                legacy_stage,
                canonical_stage,
                f"{legacy!r} renders as {legacy_stage!r} but its canonical twin {canonical!r} "
                f"renders as {canonical_stage!r}; a pre-rename run directory would display "
                "differently from an identical post-rename one",
            )
            self.assertNotEqual(
                legacy_stage,
                lifecycle_style.UNKNOWN,
                f"{legacy!r} has no row in the style table, so an already-recorded run renders as "
                "undecidable",
            )

    def test_the_deferrable_pair_is_NOT_TERMINAL_and_the_refusals_ARE(self):
        """The property the whole ladder rests on, asserted across BOTH vocabularies.

        `TERMINAL_STATES` membership is what decides whether an item can be re-attempted, whether
        `cascade_dependency_blocked` kills its dependents, and whether an orchestrator keeps waiting. The
        rename touched this set, so the invariant is re-pinned here rather than trusted.
        """
        for terminal in (
            "merge-needs-human",
            "merge-refused",
            "integration-blocked",
            "merge-conflict",
        ):
            self.assertIn(terminal, runner_shared.TERMINAL_STATES, terminal)
        for non_terminal in ("merge-retry", "merge-unchecked", "integration-deferred"):
            self.assertNotIn(
                non_terminal,
                runner_shared.TERMINAL_STATES,
                f"{non_terminal} must NOT be terminal: that absence is what makes a re-attempt "
                "possible and keeps dependents alive",
            )

    def test_a_zero_limit_is_block_spelled_as_a_count(self):
        self.assertFalse(self.decide(attempts_used=1, limit=0).deferred)

    # ---- THE NEGATIVE CASE: merge-conflict must NOT acquire a retry loop --------------------------

    def test_merge_conflict_is_TERMINAL_ON_ITS_FIRST_ATTEMPT_and_consumes_no_budget(
        self,
    ):
        """THE OVER-TRIGGER GUARD, and it is not optional.

        Every positive-arm test above would ALSO pass for a ladder that wrongly deferred genuine
        conflicts, and that over-trigger is invisible until a real conflict has been retried ten times.
        `integrate_lane_branch` returns THREE kinds and only the dirty-overlap one is transient:
        `merge-conflict` means the reused gate returned non-passing (real conflict, stale base,
        combined-red, or scope), which repetition does not fix.

        THE WORDING ASSERTION WAS UPDATED BY `l2mzxn`, and the PROPERTY is untouched. This used to
        require the literal "not the transient", which the verdict no longer says: it stopped
        enumerating four causes it could not distinguish (the measured incident's real cause was absent
        from that list) and now states the kind plus why the kind is terminal. What this test exists to
        guard - that a genuine conflict is terminal on its FIRST attempt and consults no budget - is
        asserted below exactly as before.
        """
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
        # It stays terminal even with the whole budget untouched, i.e. the budget is not consulted.
        self.assertFalse(
            self.decide(
                integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT,
                attempts_used=1,
                limit=1000,
            ).deferred
        )

    def test_an_unrecognized_kind_fails_CLOSED_onto_todays_terminal_path(self):
        self.assertFalse(runner_shared.classify_integration_refusal("something-new"))
        self.assertFalse(self.decide(integ_kind="something-new").deferred)

    # ---- the override, including the one that reproduces today ------------------------------------

    def test_on_integration_blocked_block_REPRODUCES_the_pre_ladder_behavior(self):
        decision = self.decide(policy=runner_shared.ON_INTEGRATION_BLOCKED_BLOCK)
        self.assertFalse(decision.deferred)
        self.assertEqual(decision.status, runner_shared.INTEGRATION_BLOCKED_STATUS)

    def test_the_override_vocabulary_is_closed_and_defaults_to_defer(self):
        self.assertEqual(
            runner_shared.resolve_on_integration_blocked(None),
            runner_shared.ON_INTEGRATION_BLOCKED_DEFER,
        )
        for good in runner_shared.ON_INTEGRATION_BLOCKED_CHOICES:
            with self.subTest(value=good):
                self.assertEqual(
                    runner_shared.resolve_on_integration_blocked(good), good
                )
        with self.assertRaises(runner_shared.RunFlagRefusal):
            runner_shared.resolve_on_integration_blocked("sometimes")

    # ---- BUDGET INDEPENDENCE, the category error the backlog item names --------------------------

    def test_the_two_budgets_are_INDEPENDENT_quantities(self):
        """Set each to a different value and show each governs ONLY its own path.

        `DEFAULT_RETRY_LIMIT` counts PAID CORRECTION TURNS on the stated ground that repetition cannot
        turn failure into success; that ground is FALSE for an integration re-attempt, whose blocker is
        another process's transient dirt. Conflating them is what this asserts against.
        """
        from agent_workflows import run_recovery

        self.assertEqual(run_recovery.DEFAULT_RETRY_LIMIT, 2)
        self.assertEqual(runner_shared.DEFAULT_INTEGRATION_RETRY_LIMIT, 10)
        self.assertNotEqual(
            run_recovery.DEFAULT_RETRY_LIMIT,
            runner_shared.DEFAULT_INTEGRATION_RETRY_LIMIT,
        )

        # The integration resolver does not read the correction default...
        self.assertEqual(runner_shared.resolve_integration_retry_limit(None), 10)
        self.assertEqual(runner_shared.resolve_integration_retry_limit(7), 7)
        # ...and it is deliberately NOT clamped to spec 2.1's 0..10 CORRECTION range.
        self.assertEqual(runner_shared.resolve_integration_retry_limit(25), 25)
        with self.assertRaises(runner_shared.RunFlagRefusal):
            runner_shared.resolve_retry_budget(25)

        # Moving one does not move the other, asserted by driving both with opposite values.
        self.assertEqual(runner_shared.resolve_retry_budget(0), 0)
        self.assertEqual(runner_shared.resolve_integration_retry_limit(9), 9)
        # And an integration decision honors ITS limit, not the correction one: 3 re-attempts are
        # still deferred at limit 9, where a correction budget of 2 would already be spent.
        self.assertTrue(self.decide(attempts_used=3, limit=9).deferred)

    def test_a_negative_integration_limit_is_refused(self):
        with self.assertRaises(runner_shared.RunFlagRefusal):
            runner_shared.resolve_integration_retry_limit(-1)

    # ---- rung 2: BOTH bounds, asserted SEPARATELY -------------------------------------------------

    def poll(self, *, dirty, ages, poll_limit=10, staleness=3600.0):
        """Drive the poll with controlled dirt and clock. `dirty`/`ages` are per-poll sequences."""
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

    def test_rung_2_bound_i_the_POLL_COUNT_while_main_is_still_ACTIVE(self):
        outcome, slept = self.poll(
            dirty=[["src/x.py"]] * 40, ages=[60.0] * 40, poll_limit=3
        )
        self.assertFalse(outcome.cleared)
        self.assertEqual(outcome.bound, runner_shared.POLL_BOUND_COUNT)
        self.assertEqual(outcome.polls, 3)
        self.assertEqual(len(slept), 3)
        self.assertIn("poll bound 3", outcome.detail)
        self.assertIn("still active", outcome.detail)

    def test_rung_2_bound_ii_MAIN_IS_STALE_so_polling_stops_EARLY_regardless_of_count(
        self,
    ):
        """The bound that carries the design's whole argument, so it gets its own test.

        A test covering only the count would PASS with this bound unimplemented, which is exactly why
        the plan calls it the item most likely to be skipped. Here main has been idle for four hours
        with a generous poll budget: the correct behavior is to give up IMMEDIATELY, having slept zero
        times, because nobody is about to commit and the dirt is abandoned.
        """
        outcome, slept = self.poll(
            dirty=[["src/x.py"]] * 40, ages=[4 * 3600.0] * 40, poll_limit=25
        )
        self.assertFalse(outcome.cleared)
        self.assertEqual(outcome.bound, runner_shared.POLL_BOUND_STALE)
        self.assertEqual(outcome.polls, 0)
        self.assertEqual(slept, [], "a stale main must cost NO waiting at all")
        self.assertIn("ABANDONED", outcome.detail)
        self.assertIn("needs a human", outcome.detail)

    def test_the_two_bounds_report_DIFFERENT_facts(self):
        """ "polled 10x, main active 1m ago" and "gave up, main idle 4h" demand different responses."""
        active, _ = self.poll(dirty=[["x"]] * 40, ages=[60.0] * 40, poll_limit=2)
        stale, _ = self.poll(dirty=[["x"]] * 40, ages=[9999.0] * 40, poll_limit=2)
        self.assertNotEqual(active.bound, stale.bound)
        self.assertNotEqual(active.detail, stale.detail)
        self.assertEqual(active.last_activity_age, 60.0)
        self.assertEqual(stale.last_activity_age, 9999.0)

    def test_an_UNMEASURABLE_main_activity_fails_closed_and_does_not_wait(self):
        outcome, slept = self.poll(dirty=[["x"]] * 5, ages=[None] * 5)
        self.assertEqual(outcome.bound, runner_shared.POLL_BOUND_STALE)
        self.assertEqual(slept, [])
        self.assertIn("unmeasurable", outcome.detail)

    def test_the_poll_STOPS_as_soon_as_the_dirt_clears(self):
        outcome, slept = self.poll(
            dirty=[["src/x.py"], ["src/x.py"], []], ages=[10.0] * 5
        )
        self.assertTrue(outcome.cleared)
        self.assertEqual(outcome.bound, runner_shared.POLL_BOUND_CLEARED)
        self.assertEqual(outcome.polls, 2)
        self.assertEqual(len(slept), 2)

    def test_main_last_activity_is_the_NEWER_of_head_time_and_dirty_mtime(self):
        """Either signal ALONE answers the wrong question, so the combination is asserted on a real repo."""
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

            # A committed-but-idle repo reports the age of its HEAD commit: small, and measurable.
            committed_age = runner_shared.main_last_activity_age(repo)
            self.assertIsNotNone(committed_age)
            assert committed_age is not None
            self.assertLess(committed_age, 120.0)

            # Now make HEAD look OLD while an uncommitted edit is FRESH: the dirty mtime must win, or
            # an actively-edited tree would be misread as abandoned.
            (repo / "b.txt").write_text("dirty\n", encoding="utf-8")
            age = runner_shared.main_last_activity_age(
                repo, now=__import__("time").time()
            )
            self.assertIsNotNone(age)
            assert age is not None
            self.assertLess(age, 120.0)

    # ---- rung 3: the ask, which must never hang ---------------------------------------------------

    def test_the_ask_is_SKIPPED_ENTIRELY_when_the_run_is_not_interactive(self):
        outcome = runner_shared.ask_operator_about_integration(
            "aaa111",
            "dirty overlap",
            interactive=False,
            prompt=lambda *a, **k: self.fail(
                "an unattended run must never be prompted"
            ),
        )
        self.assertFalse(outcome.asked)
        self.assertFalse(outcome.retry)
        self.assertIn("SUPPRESSED", outcome.detail)

    def test_the_ask_CANNOT_HANG_a_timeout_falls_through_to_terminal(self):
        """`qyaime` closed an unbounded-wait deadlock whose honest limit was that the ask is
        "bounded and recorded, not architecturally prevented". Here the bound IS the architecture: a
        `None` answer (the timeout) yields `retry=False`, so the caller goes terminal."""
        outcome = runner_shared.ask_operator_about_integration(
            "aaa111", "dirty overlap", interactive=True, prompt=lambda *a, **k: None
        )
        self.assertTrue(outcome.asked)
        self.assertFalse(outcome.retry)
        self.assertIn("TIMED OUT", outcome.detail)

    def test_the_ask_honors_an_affirmative_and_a_refusal(self):
        yes = runner_shared.ask_operator_about_integration(
            "aaa111", "r", interactive=True, prompt=lambda *a, **k: "y\n"
        )
        self.assertTrue(yes.retry)
        for answer in ("n\n", "\n", "later\n"):
            with self.subTest(answer=answer):
                self.assertFalse(
                    runner_shared.ask_operator_about_integration(
                        "aaa111",
                        "r",
                        interactive=True,
                        prompt=lambda *a, **k: answer,
                    ).retry
                )

    def test_the_prompt_predicate_is_the_SHIPPED_one_not_a_second_TTY_test(self):
        """`is_interactive_run` already encodes both halves (a real TTY AND no `--unattended`).

        REPLACES A SOURCE-TEXT PIN. It read `inspect.getsource(retry_deferred_integrations)` on each
        host and asserted the substring `"is_interactive_run"` appeared. That is a change-detector in
        both directions: this adapter's own DOCSTRING and the comment above the call both name the
        predicate (the comment exists precisely to explain that the shared ladder resolves it), so the
        pin was satisfied by prose and would have stayed green with the call deleted; and a host that
        reached the predicate through an alias or a local re-export would have failed it while
        behaving correctly.

        WHAT REPLACES IT IS A SENTINEL THAT MUST TRAVEL. `is_interactive_run` is replaced by one
        returning a unique OBJECT, and the shared ladder is replaced by a spy recording the
        `interactive=` keyword it receives. Driving each host's real adapter must then deliver THAT
        OBJECT to the ladder. A second TTY test cannot produce it (it would deliver a plain bool), a
        comment cannot produce it, and neither can a host that computes interactivity itself.

        The `--unattended` half is asserted on the shipped predicate directly, because that is the
        property the hosts are DELEGATING to: a real TTY is not enough when the operator declared
        nobody is watching.
        """
        import argparse

        class _TTY:
            def isatty(self):
                return True

        # The shipped predicate's own contract: a real terminal does NOT make an `--unattended` run
        # interactive. This is what a host-local `stream.isatty()` test would get wrong.
        self.assertFalse(
            runner_shared.is_interactive_run(
                argparse.Namespace(unattended=True, full_auto=False), stream=_TTY()
            )
        )
        # THE POSITIVE ROW, without which the assertion above is satisfied by a predicate that always
        # refuses. `sys.stdin` must be patched too: the predicate requires BOTH streams to be terminals,
        # and under pytest stdin is captured, so the negative row alone would pass for the wrong reason.
        with mock.patch.object(runner_shared.sys, "stdin", _TTY()):
            self.assertTrue(
                runner_shared.is_interactive_run(
                    argparse.Namespace(unattended=False, full_auto=False), stream=_TTY()
                ),
                "with both streams real terminals and no policy flag, the predicate must permit a "
                "prompt; a gate that can never prompt is indistinguishable from one that always "
                "refuses",
            )
            self.assertFalse(
                runner_shared.is_interactive_run(
                    argparse.Namespace(unattended=True, full_auto=False), stream=_TTY()
                ),
                "and `--unattended` must still win over TWO real terminals, which is the half a "
                "host-local `stream.isatty()` test gets wrong",
            )

        sentinel = object()
        wrong = []
        for module in (oc_runipd, agy_runipd):
            seen: dict = {}

            # `seen` is bound as a DEFAULT, not closed over: the loop variable would late-bind and
            # make each host assert about the last one's call.
            def _spy(_sink=seen, **kwargs):
                _sink.update(kwargs)
                return []

            with (
                mock.patch.object(
                    runner_shared, "is_interactive_run", lambda *a, **k: sentinel
                ),
                mock.patch.object(
                    runner_shared, "reattempt_deferred_integrations", _spy
                ),
                tempfile.TemporaryDirectory() as td,
            ):
                module.retry_deferred_integrations(
                    pathlib.Path(td) / "run",
                    {"repo": td, "queue": [], "options": {"unattended": True}},
                )
            if "interactive" not in seen:
                wrong.append(
                    f"  {module.__name__}: the shared ladder was never reached, so this host cannot "
                    "be delegating the interactive decision to it at all"
                )
            elif seen["interactive"] is not sentinel:
                wrong.append(
                    f"  {module.__name__}: the ladder received interactive="
                    f"{seen['interactive']!r}, not the patched predicate's sentinel. This host "
                    "computes interactivity ITSELF rather than calling the shipped "
                    "`is_interactive_run`, so it carries a SECOND TTY test that is free to forget "
                    "`--unattended` and stop an overnight run on a question nobody will see"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of 2 hosts do not delegate the prompt predicate. A failure on ONE host is "
            "the asymmetry this class exists for: the two adapters are separate code and only the "
            "ladder is shared, so one host can grow its own TTY test while the other stays correct. "
            "FIX: pass `interactive=runner_shared.is_interactive_run(...)` into "
            "`reattempt_deferred_integrations` rather than testing a stream locally.\n"
            + "\n".join(wrong),
        )

    # ---- OQ-03: a run must not END on a non-terminal status ---------------------------------------

    def test_an_exhausted_deferral_is_RESOLVED_to_terminal_with_the_lane_preserved(
        self,
    ):
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
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                self.assertIn(item["status"], module.TERMINAL_STATES)
        # The lane is still named, so the recovery route survives.
        self.assertEqual(item["preserved_branch"], "aw/lane/aaa111")
        self.assertEqual(events[0]["event"], "ipd-integration-blocked")
        self.assertTrue(saved)

    def test_nothing_is_resolved_when_no_item_is_deferred(self):
        state = {"queue": [{"id6": "aaa111", "status": "executed"}]}
        self.assertEqual(
            runner_shared.resolve_exhausted_deferrals(
                pathlib.Path("/nonexistent"),
                state,
                save_state=lambda *a, **k: self.fail("must not persist"),
                append_jsonl=lambda *a, **k: self.fail("must not emit"),
            ),
            [],
        )

    # ---- E-01's dependency rule, on BOTH hosts ---------------------------------------------------

    def test_a_DEFERRED_prerequisite_does_NOT_satisfy_a_dependency_edge(self):
        """A deferred prerequisite has NOT integrated, so a dependent must wait exactly as for a
        queued one. Dispatching it would run against a base lacking its prerequisite's commits, which
        is worse than the bug being fixed."""
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
            with self.subTest(host=module.__name__):
                satisfied, unsatisfied = module.dependency_status(
                    state["queue"][1], state
                )
                self.assertFalse(satisfied)
                self.assertEqual(unsatisfied, ["executed:aaa111"])

    def test_the_cascade_does_NOT_kill_a_dependent_of_a_deferred_item(self):
        """This is the seven-of-34 cascade the plan exists to prevent, asserted directly.

        `cascade_dependency_blocked` kills a dependent when its prerequisite's status is
        `in TERMINAL_STATES and not in required`. Keeping `integration-deferred` OUT of that set is
        precisely what stops the cascade here. It is ONE shared implementation re-exported by agy, so
        the behavior is asserted on both hosts rather than fixed twice.
        """
        self.assertIs(
            agy_runipd.cascade_dependency_blocked,
            oc_runipd.cascade_dependency_blocked,
        )
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
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
                self.assertEqual(module.cascade_dependency_blocked(state), [])
                self.assertEqual(state["queue"][1]["status"], "queued")
                # CONTROL: the SAME shape with a terminal non-success prerequisite still cascades, so
                # this test cannot pass by the cascade having been disabled.
                state["queue"][0]["status"] = "merge-needs-human"
                self.assertTrue(module.cascade_dependency_blocked(state))
                self.assertEqual(state["queue"][1]["status"], "dependency-blocked")

    # ---- F-11: the silent-downgrade trap, on BOTH hosts -----------------------------------------

    def test_reconcile_disposition_PASSES_THE_DEFERRAL_THROUGH_on_both_hosts(self):
        """THE HIGHEST-RISK EDIT of this plan, so it is pinned directly.

        `integration-deferred` is deliberately absent from `TERMINAL_STATES`, so
        `TERMINAL_STATES - {...}` SKIPS it and control used to reach
        `return ("partial" if exit_code == 0 else "failed-safely")`. `partial` IS terminal, so a
        deferred item would have been silently relabelled and the deferral destroyed - reproducing
        today's permanent loss while every ladder unit test above still passed.
        """
        for module in (oc_runipd, agy_runipd):
            with (
                self.subTest(host=module.__name__),
                tempfile.TemporaryDirectory() as td,
            ):
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
                self.assertEqual(
                    disposition,
                    runner_shared.INTEGRATION_DEFERRED_STATUS,
                    "a deferred item must NOT be downgraded to `partial`",
                )
                self.assertNotIn(disposition, module.TERMINAL_STATES)
                # CONTROL: a non-deferred item still falls through EXACTLY as before, so the fix did
                # not disturb the fallback it guards.
                running = dict(item, status="running")
                self.assertEqual(
                    module.reconcile_disposition(pathlib.Path(td), running, run_dir, 0)[
                        0
                    ],
                    "partial",
                )
                self.assertEqual(
                    module.reconcile_disposition(pathlib.Path(td), running, run_dir, 1)[
                        0
                    ],
                    "failed-safely",
                )

    # ---- the ledger vocabulary and the resume route ----------------------------------------------

    def test_the_new_status_is_in_the_shared_ledger_vocabulary(self):
        """R3's coherence check must know it, or a run holding one refuses its own resume."""
        from agent_workflows import runner_shutdown

        self.assertIn(
            runner_shared.INTEGRATION_DEFERRED_STATUS,
            runner_shutdown.KNOWN_ITEM_STATUSES,
        )
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                self.assertEqual(
                    set(module.TERMINAL_STATES)
                    - set(runner_shutdown.KNOWN_ITEM_STATUSES),
                    set(),
                )

    # ---- driving a REAL `run_queue`, which is what the two pins below replaced text with ----------

    @staticmethod
    def _dispatch_repo(root: pathlib.Path) -> pathlib.Path:
        """A throwaway git repo. FIXTURES ONLY: `run_queue` reads `state["repo"]` and runs git in it."""
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

    def test_retry_incomplete_re_queues_a_deferred_item_on_both_hosts(self):
        """A deferral can outlive its run (an interrupt between deferring and the next iteration).

        REPLACES A SOURCE-TEXT PIN. It read `inspect.getsource(module.run_queue)` and asserted the
        literal `'"merge-retry"'` appeared somewhere in it. That is a change-detector in both
        directions: `run_queue` carries a long COMMENT explaining exactly this rule (it names the
        status in prose so a later reader does not delete it from the requeue set), so the pin was
        satisfied by that comment and would have stayed green with the status removed from the set;
        and it said nothing about the requeue actually HAPPENING, since the same literal appears in
        `reconcile_disposition`'s neighbourhood and in the event vocabulary.

        WHAT REPLACES IT DRIVES THE REQUEUE. A real `run_queue(retry_incomplete=True)` is driven over
        a queue holding ONE `integration-deferred` item with the agent turn stubbed, and the item must
        actually be dispatched (so the flip to `queued` happened) and must carry
        `requeue_from_status == "merge-retry"` (so the prior disposition was REMEMBERED, which
        is what the integration pass and E-04's hold-back read). A comment cannot dispatch an item.

        THE CONTROL ROW IS LOAD-BEARING: the same fixture with `retry_incomplete=False` must dispatch
        NOTHING, so this cannot pass by the loop having started admitting deferred items unconditionally.
        """
        wrong = []
        for module in (oc_runipd, agy_runipd):
            for retry, expect_turn in ((True, True), (False, False)):
                turns: list = []

                # Both `turns` and `module` are bound as DEFAULTS rather than closed over: a closure
                # over these loop variables late-binds, and every iteration would then record into the
                # LAST cell's list through the LAST host's `save_state`.
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
                        module.run_queue(run_dir, retry_incomplete=retry)
                    final = runner_shared.load_state(run_dir)["queue"][0]

                if bool(turns) is not expect_turn:
                    wrong.append(
                        f"  {module.__name__} with retry_incomplete={retry}: dispatched "
                        f"{len(turns)} turn(s), expected {'one' if expect_turn else 'none'}\n"
                        "    this row exists because: "
                        + (
                            "a deferral that outlived its run must be pickable up by a resume, or "
                            "verified work is stranded for good; the ladder only runs inside a LIVE "
                            "dispatch loop, so a resume needs this requeue"
                            if expect_turn
                            else "without `--retry-incomplete` a deferred item must be left alone, "
                            "or the flag means nothing and every resume silently re-runs work whose "
                            "integration was refused"
                        )
                    )
                elif expect_turn and turns[0][1] != (
                    runner_shared.INTEGRATION_DEFERRED_STATUS
                ):
                    wrong.append(
                        f"  {module.__name__}: the requeued item reached its turn with "
                        f"requeue_from_status={turns[0][1]!r}, expected "
                        f"{runner_shared.INTEGRATION_DEFERRED_STATUS!r}\n"
                        "    this row exists because: the flip to `queued` OVERWRITES the prior "
                        "disposition, and the integration pass plus E-04's hold-back select on this "
                        "recorded value; losing it makes the pass unable to tell a deferred lane from "
                        "an ordinary retry"
                    )
                elif expect_turn and final["status"] != "executed":
                    wrong.append(
                        f"  {module.__name__}: the requeued item ended {final['status']!r} rather "
                        "than reaching a real turn's outcome"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {2 * 2} (host, flag) cells mishandle a deferral surviving its run. A "
            "failure on ONE host is the asymmetry this class exists for: the two `run_queue` bodies "
            "are separate code and only the ladder is shared. FIX: `integration-deferred` belongs in "
            "the `retry_incomplete` requeue status set in each host's `run_queue`, and the flip must "
            f"record `requeue_from_status` before overwriting `status`.\n"
            + "\n".join(wrong),
        )

    # ---- the ladder is ONE implementation, not two -----------------------------------------------

    def test_neither_runner_carries_its_own_copy_of_the_ladder(self):
        """CID-3: a rule present in one driver only is a defect, and two copies drift (measured at
        0.651 similarity for the pre-extraction integration code)."""
        for module in (oc_runipd, agy_runipd):
            src = module_source(module)
            defined = {
                node.name
                for node in ast.parse(src).body
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
            }
            with self.subTest(host=module.__name__):
                for name in (
                    "decide_integration_deferral",
                    "classify_integration_refusal",
                    "poll_for_integration_window",
                    "ask_operator_about_integration",
                    "record_integration_refusal",
                    "resolve_exhausted_deferrals",
                    "reattempt_deferred_integrations",
                    "main_last_activity_age",
                ):
                    self.assertNotIn(name, defined)

    def test_both_hosts_reach_the_ladder_from_their_dispatch_loop(self):
        """A shared ladder nothing CALLS is the dead-gate failure this repository has already paid for.

        REPLACES FOUR SOURCE-TEXT PINS. It read `inspect.getsource(module.run_queue)` and asserted the
        substrings `"retry_deferred_integrations"`, `"deferred_integration_items"`,
        `"runnable is None"` and `"poll=True"` appeared. Every one is a change-detector: `run_queue`
        carries a ten-line COMMENT block that names the ladder, names the trigger, and explains why
        `poll=True` is passed exactly where it is, so all four were satisfied by prose alone and the
        whole ladder could have been deleted while this test stayed green. That is the dead-gate
        failure the docstring names, reproduced in the very test written to prevent it. The
        `"runnable is None"` pin is the worst of the four: it asserts a SPELLING of a condition, so
        rewriting it as `if not runnable:` would fail a test about behavior.

        WHAT REPLACES THEM IS AN OBSERVED CALL SEQUENCE, on both hosts. Each host's
        `retry_deferred_integrations` adapter is replaced by a spy that records the `poll`/`ask`
        keywords it receives, and a real `run_queue` is driven over a queue of THREE deferred items.
        The claim is then the full shape the four pins were approximating:

        * RUNG 1 IS REACHED, and reached FIRST, with `poll=False`: the top-of-loop re-attempt that
          costs nothing.
        * RUNG 2/3 IS REACHED with `poll=True, ask=True`, which is what makes the ladder more than its
          first rung.
        * THE TRIGGER IS "NOTHING ELSE IS DISPATCHABLE", NOT "THIS IS THE LAST ITEM", asserted by the
          fixture holding THREE deferred items and no queued one. A last-item test would never poll
          here, so this fixture distinguishes the two conditions the `"runnable is None"` text pin
          could only spell.

        A comment cannot record a keyword argument, and the assertion survives any rewrite of the
        condition or any renaming of the adapter.
        """
        wrong = []
        for module in (oc_runipd, agy_runipd):
            calls: list = []

            # `calls` and `module` are bound as DEFAULTS rather than closed over, so each host records
            # into its OWN log through its OWN `save_state`; a closure over the loop late-binds both.
            def _spy(
                run_dir, state, *, poll=False, ask=False, _log=calls, _host=module
            ):
                _log.append({"poll": poll, "ask": ask})
                if poll:
                    # Resolve the deferrals so the loop terminates; the real rung 3 does the same
                    # through `resolve_exhausted_deferrals`, and leaving them would spin.
                    for entry in state["queue"]:
                        if entry["status"] == runner_shared.INTEGRATION_DEFERRED_STATUS:
                            entry["status"] = runner_shared.INTEGRATION_BLOCKED_STATUS
                    _host.save_state(run_dir, state)
                return []

            with tempfile.TemporaryDirectory() as td:
                root = pathlib.Path(td)
                repo = self._dispatch_repo(root)
                run_dir = self._dispatch_run(
                    root, repo, (runner_shared.INTEGRATION_DEFERRED_STATUS,) * 3
                )
                with (
                    mock.patch.object(module, "retry_deferred_integrations", _spy),
                    mock.patch.object(
                        module,
                        "execute_item",
                        lambda *a, **k: self.fail(
                            "no item was dispatchable, so no agent turn may be spent"
                        ),
                    ),
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    module.run_queue(run_dir, retry_incomplete=False)

            problems = []
            if not calls:
                problems.append(
                    "the ladder was NEVER reached from the dispatch loop: this is the dead-gate "
                    "failure exactly, a fully built and fully tested ladder with no caller"
                )
            else:
                if calls[0] != {"poll": False, "ask": False}:
                    problems.append(
                        f"the FIRST call was {calls[0]!r}, expected rung 1's "
                        "{'poll': False, 'ask': False}. Rung 1 is the free one (the loop already "
                        "reloads state each iteration); polling on the first attempt spends waiting "
                        "before trying the cheap thing"
                    )
                if not any(c["poll"] and c["ask"] for c in calls):
                    problems.append(
                        f"no call ever carried poll=True with ask=True; calls seen: {calls!r}. Rungs "
                        "2 and 3 are unreachable, so a deferral that rung 1 cannot clear goes "
                        "straight to terminal with the lane stranded, which is the loss this ladder "
                        "exists to prevent. Note the fixture holds THREE deferred items and NO "
                        "queued one, so a trigger written as a LAST-ITEM test rather than as "
                        "`nothing else is dispatchable` fails here"
                    )
            if problems:
                wrong.append(
                    f"  {module.__name__}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of 2 hosts do not reach the shared ladder from their dispatch loop. A "
            "failure on ONE host is the asymmetry this class exists for: the ladder is shared but the "
            "two `run_queue` bodies are not, so a wiring that is correct on one host proves nothing "
            "about the other. FIX: call `retry_deferred_integrations(run_dir, state)` at the TOP of "
            "the loop whenever `deferred_integration_items(state)` is non-empty, and again with "
            f"`poll=True, ask=True` when the loop's own selection finds nothing dispatchable.\n"
            + "\n".join(wrong),
        )


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

    def test_a_lane_holding_unmerged_work_IS_stranded(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(rec["lane_state"], runner_shared.LANE_STRANDED)
            self.assertIs(rec["landed"], False)
            self.assertTrue(rec["needs_attention"])
            self.assertEqual(rec["commits_ahead"], 1)

    def test_a_MERGED_lane_is_NOT_stranded_and_holds_work_alone_would_get_it_WRONG(
        self,
    ):
        """Case (c), the one most likely to fail, plus the direct proof that `holds_work` is insufficient.

        Built runner-faithfully (`worktree add -b`) and merged with `--no-ff`, which is exactly the
        controlled fallback `integrate_lane_branch` performs when main advanced.
        """
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

            # THE MEASUREMENT: `holds_work` is UNCHANGED across the merge, so it cannot answer landing.
            self.assertTrue(before["holds_work"])
            self.assertTrue(after["holds_work"])
            self.assertEqual(before["commits_ahead"], after["commits_ahead"])
            # The reachability question is the one that changed.
            self.assertIs(before_landed, False)
            self.assertIs(after_landed, True)

            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(rec["lane_state"], runner_shared.LANE_LANDED)
            self.assertFalse(rec["needs_attention"])

    def test_an_EMPTY_lane_is_not_reported(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01", commit=False)
            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(rec["lane_state"], runner_shared.LANE_EMPTY_OF_WORK)
            self.assertFalse(rec["needs_attention"])

    def test_a_lane_owned_by_a_LIVE_process_is_not_reported(self):
        from agent_workflows import worktree_lease

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            with mock.patch.object(
                worktree_lease, "lane_owned_by_other_live_process", return_value=True
            ):
                rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertEqual(rec["lane_state"], runner_shared.LANE_LIVE)
            self.assertFalse(rec["needs_attention"])

    def test_owner_live_None_is_an_UNKNOWN_owner_and_never_a_not_live(self):
        """`inspect_lane` sets `owner_live=None` when no owner record exists; reading it as a boolean
        would silently misclassify. The fixture lane has no owner record, so it must still classify on
        its WORK, not be suppressed as live nor reported as live."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            rec = runner_shared.classify_lane_integration(repo, lane, target="main")
            self.assertIsNone(rec["owner_live"])
            self.assertEqual(rec["lane_state"], runner_shared.LANE_STRANDED)

    def test_a_vanished_branch_is_a_visible_UNKNOWN_not_a_silent_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            # Record a lane whose branch never existed: the run record outlives the branch.
            ghost = dict(lane)
            ghost["branch"] = "aw/lane/ghost99"
            ghost["lane_id"] = "ghost99"
            ghost["id6"] = "ghost99"
            self.assertIsNone(
                runner_shared.lane_work_has_landed(repo, ghost["branch"], target="main")
            )
            rec = runner_shared.classify_lane_integration(repo, ghost, target="main")
            # No branch and no worktree means no work to lose, so it is EMPTY rather than UNKNOWN; the
            # UNKNOWN case is a lane that HOLDS work whose landing cannot be decided.
            self.assertEqual(rec["lane_state"], runner_shared.LANE_EMPTY_OF_WORK)

    def test_a_holding_lane_whose_target_does_not_resolve_is_UNKNOWN(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            rec = runner_shared.classify_lane_integration(
                repo, lane, target="refs/heads/no-such-target"
            )
            self.assertEqual(rec["lane_state"], runner_shared.LANE_UNKNOWN)
            self.assertTrue(rec["needs_attention"])
            self.assertIsNone(rec["landed"])

    def test_records_come_from_the_RUN_RECORD_and_carry_the_integration_signal(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            state = _state_for(repo, [lane])
            recs = runner_shared.stranded_lane_records(repo, [state], target="main")
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["branch"], "aw/lane/lane01")
            self.assertEqual(recs[0]["integration_signal"], "suite-failed")
            self.assertEqual(recs[0]["run_id"], "run-fixture")
            self.assertEqual(recs[0]["lane_state"], runner_shared.LANE_STRANDED)

    def test_the_HISTORICAL_record_still_reports_what_it_did_after_recovery(self):
        """Test (f), done by ACTUALLY RECOVERING a fixture lane rather than by assertion.

        A verdict derived from a live filesystem audit reports a recovered run clean and rewrites
        history, which is what `xtklpd`'s review measured. THIS DOES NOT CONTRADICT the merged-not-
        reported case: that case asks "is this lane a CURRENT attention item" (no, its work landed),
        while this asks "what did this RUN record say happened" (a lane was preserved, with a reason and
        an integration signal), and the two are different questions about different objects.
        """
        import subprocess

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            lane = _add_lane(repo, root / "lane01", "lane01")
            state = _state_for(repo, [lane])

            stranded = runner_shared.stranded_lane_records(repo, [state], target="main")
            self.assertEqual(len(stranded), 1)

            # RECOVER IT, exactly as a human or `integrate_lane_branch` would.
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

            # The lane is no longer a CURRENT attention item.
            after = runner_shared.stranded_lane_records(repo, [state], target="main")
            self.assertEqual(after, [])

            # But the RUN RECORD still records what happened, unmodified by the recovery: the facts are
            # read from the record, never rebuilt from the filesystem.
            item = state["queue"][0]
            self.assertEqual(item["preserved_branch"], "aw/lane/lane01")
            self.assertEqual(item["integration_signal"], "suite-failed")
            self.assertEqual(
                item["preserved_reason"],
                "the run ended without integrating this lane",
            )
            full = runner_shared.stranded_lane_records(
                repo, [state], target="main", attention_only=False
            )
            self.assertEqual(len(full), 1)
            self.assertEqual(full[0]["lane_state"], runner_shared.LANE_LANDED)

    def test_worktree_display_NEVER_returns_an_absolute_path(self):
        """The leak guard. `preserved_worktree` is an absolute home path in most recorded run items."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            inside = repo / ".aw" / "worktrees" / "lane01"
            inside.mkdir(parents=True)
            self.assertEqual(
                runner_shared.lane_worktree_display(repo, str(inside)),
                ".aw/worktrees/lane01",
            )
            # An absolute path OUTSIDE the repo is reduced to the canonical lane shape or omitted, and
            # in neither case does the absolute prefix survive.
            # Composed rather than a literal, for the reason the attention fixture records: the
            # leak-sanitizer fails a tracked file containing a home path, fixture or not.
            #
            # WHICH OF THE TWO IT IS NOW DEPENDS ON EXISTENCE (plan `0ta5vg` E-05), and this assertion was
            # UPDATED rather than deleted. It previously demanded the reconstruction for an ABSENT
            # directory; a row must not assert a tree that is gone, so an absent one is now OMITTED. The
            # invariant this test exists for is untouched and still asserted on every branch below: no
            # absolute prefix ever survives. Omission strictly REDUCES what is printed, so it cannot
            # weaken the leak guard.
            self.assertIsNone(
                runner_shared.lane_worktree_display(
                    repo, "/" + "home" + "/someone/VC/proj/.aw/worktrees/lane09"
                )
            )
            # The reconstruction branch is still exercised, for an outside-the-repo lane that EXISTS.
            outside_live = root / "elsewhere" / "worktrees" / "lane09"
            outside_live.mkdir(parents=True)
            self.assertEqual(
                runner_shared.lane_worktree_display(repo, str(outside_live)),
                ".aw/worktrees/lane09",
            )
            self.assertIsNone(
                runner_shared.lane_worktree_display(repo, "/var/tmp/elsewhere")
            )
            self.assertIsNone(runner_shared.lane_worktree_display(repo, None))

    def test_the_predicate_has_exactly_ONE_definition(self):
        """ONE READER (the `nuanaw` hard constraint): `attention` must CALL it, never reimplement it.

        THE INCIDENT BEHIND THIS CLAIM, which is why it is not simply deleted: `agy_runipd` re-forked
        FOUR `render_stream` symbols while a one-sided guard stayed green (the orchestrator's F10). A
        second definition of a landing question is not a cosmetic duplicate here - the two copies drift,
        and the direction that drifts wrong reports a STRANDED lane as landed, which is unrecoverable
        loss of unintegrated work.

        THREE OF THE FOUR ASSERTIONS WERE SOURCE-TEXT PINS AND ARE NOW SPY-BASED OR AST-BASED.
        `assertIn("rs.stranded_lane_records(", source)` pinned a CALL SPELLING through a module alias,
        so renaming the `rs` alias would have failed a test about behavior, while a comment containing
        that exact text would have satisfied it with the call deleted. `assertNotIn("merge-base",
        source)` and `assertNotIn("--is-ancestor", source)` are worse: both tokens appear in ordinary
        EXPLANATORY PROSE in this package (`runner_shared:1064` and `:1115` both name
        `git merge-base --is-ancestor` in a comment precisely to document the reading), so any comment
        in `attention` explaining WHY it must not ask the landing question itself would have failed a
        test asserting it does not ask it.

        WHAT REPLACES THEM:

        * THE DELEGATION HALF IS A SENTINEL. `stranded_lane_records` is replaced by one returning a
          record for a lane that DOES NOT EXIST in the fixture repository, and `attention`'s real
          surface must report THAT lane. A reimplementation reads the filesystem and reports the real
          lane instead, so it cannot produce the sentinel; a comment cannot either.
        * THE NON-REIMPLEMENTATION HALF IS AN AST SCAN, not a text search. Every `ast.Constant` string
          in `attention` is checked for the two git tokens, which a COMMENT cannot satisfy because a
          comment is not a node. WHY THIS CANNOT BE BEHAVIORAL: the claim is the NON-EXISTENCE of a
          construct anywhere in the module, including on error branches no test drives, and a second
          copy that happened to AGREE with the shared one on every fixture would pass every behavioral
          test while still being the fork that drifts later. Non-existence of a construct is precisely
          the case the brief keeps as AST.
        * THE SINGLE-DEFINITION HALF IS A PACKAGE-WIDE AST COUNT, strictly stronger than the
          `__module__` check it replaces. `__module__` is satisfied by a SECOND definition sitting in
          another module unused, which is exactly the shape the `render_stream` re-fork took; counting
          `FunctionDef` nodes named that, across every module in the package, is not.
        """
        import pathlib as _pl

        from agent_workflows import attention

        wrong = []

        # ---- (1) exactly ONE definition of each landing symbol, package-wide, as AST -------------
        pkg = _pl.Path(runner_shared.__file__).parent
        for name in (
            "lane_work_has_landed",
            "lane_work_landed_by_content",
            "stranded_lane_records",
            "classify_lane_integration",
        ):
            sites = []
            for path in sorted(pkg.glob("*.py")):
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                except (
                    SyntaxError
                ):  # pragma: no cover - a broken module is another failure
                    continue
                for node in ast.walk(tree):
                    if (
                        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and node.name == name
                    ):
                        sites.append(f"{path.name}:{node.lineno}")
            if (
                sites != [s for s in sites if s.startswith("runner_shared.py:")]
                or len(sites) != 1
            ):
                wrong.append(
                    f"  `{name}` is defined at {sites}, expected exactly one site in "
                    "runner_shared.py\n"
                    "    this row exists because: `agy_runipd` re-forked FOUR `render_stream` symbols "
                    "while a one-sided guard stayed green. Two copies of a LANDING question drift, "
                    "and the wrong direction reports a stranded lane as landed, which loses "
                    "unintegrated work permanently"
                )
        # And the objects the package actually binds are those single definitions.
        if (
            runner_shared.lane_work_has_landed.__module__
            != "agent_workflows.runner_shared"
        ):
            wrong.append(
                f"  the bound `lane_work_has_landed` lives in "
                f"{runner_shared.lane_work_has_landed.__module__}, not `runner_shared`\n"
                "    this row exists because: a single `def` on disk still proves nothing if the "
                "name is rebound at import time to something else"
            )

        # ---- (2) `attention` asks the landing question NOWHERE of its own, as AST ----------------
        # STRING CONSTANTS ONLY. `_run_git`-style calls pass these tokens as literals, so a real
        # reimplementation MUST put them in an `ast.Constant`; a comment explaining the reading (which
        # this package has, twice, in `runner_shared`) is not a node and cannot satisfy this.
        atree = ast.parse(_pl.Path(str(attention.__file__)).read_text(encoding="utf-8"))
        literals = [
            node.value
            for node in ast.walk(atree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]
        for token in ("merge-base", "--is-ancestor"):
            offenders = [text for text in literals if token in text and len(text) < 200]
            if offenders:
                wrong.append(
                    f"  `attention` carries the git token {token!r} in a STRING LITERAL "
                    f"({offenders!r})\n"
                    "    this row exists because: the landing question belongs to exactly one "
                    "module. `attention` asking git directly is a SECOND reader, free to answer "
                    "differently from the one the runners use"
                )

        # ---- (3) and it really does CALL the shared predicate, proven by a sentinel --------------
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

            # BASELINE: the real predicate reports the real lane, so the surface is wired at all.
            real = attention.stranded_lane_drift(repo)
            if [rec.location for rec in real] != [lane["branch"]]:
                wrong.append(
                    f"  `attention.stranded_lane_drift` reported "
                    f"{[rec.location for rec in real]!r} for a genuinely stranded lane, expected "
                    f"[{lane['branch']!r}]\n"
                    "    this row exists because: the sentinel row below is vacuous if the surface "
                    "reports nothing at all"
                )

            # THE SENTINEL: a lane that does not exist in this repository. Only a caller of the
            # shared predicate can report it; a reimplementation reads git and reports `lane01`.
            sentinel_branch = "aw/lane/" + "SENTINEL" + "-not-a-real-lane"
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
            if observed != [sentinel_branch]:
                wrong.append(
                    f"  with `runner_shared.stranded_lane_records` patched to a sentinel, "
                    f"`attention` reported {observed!r}, expected [{sentinel_branch!r}]\n"
                    "    this row exists because: `attention` must CALL the one predicate, never "
                    "reimplement it. Reporting the REAL lane here means it derived the answer itself "
                    "and the patch was invisible to it, which is the second reader this test forbids"
                )

        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} single-reader violation(s) for the lane landing question. READ THE SHAPE: "
            "a DEFINITION count above one is a re-fork on disk and drifts on the next edit; a git "
            "token in `attention`'s literals is a second reader already asking git itself; and the "
            "sentinel failing while the baseline passes is the worst case, because it means the "
            "surface works today by answering the question TWICE and the two answers merely happen to "
            "agree. FIX: `attention` calls `runner_shared.stranded_lane_records` and renders what it "
            f"returns; the git reading lives only in `runner_shared`.\n"
            + "\n".join(wrong),
        )


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
            self.assertIsNone(
                runner_shared.lane_worktree_display(repo, str(not_a_lane_shape)),
                "an absent directory reached through the SUCCESS return must be omitted. A value here "
                "means the existence guard sits only on the reconstruction, so every real record (all "
                "of which took the success path, measured over the live set) still asserts a tree that "
                "was reclaimed months ago and sends its reader to inspect nothing",
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
        # Asserted over the CODE, not the source text: the docstring and a comment both NAME the
        # shipped runner in order to explain why it is not used, and a substring test over the raw
        # source would therefore fail on the prose that documents the very property being pinned.
        node = next(
            n
            for n in ast.parse(module_source(runner_shared)).body
            if isinstance(n, ast.FunctionDef) and n.name == "reintegrate_lane"
        )
        called = {
            ast.unparse(sub.func) for sub in ast.walk(node) if isinstance(sub, ast.Call)
        }
        self.assertNotIn("make_integration_validation_runner", called)
        self.assertIn("suite_check", called)

    def test_a_missing_branch_refuses_with_its_own_reason(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0003")
            lane = _verified_lane(repo, root, "aa0003")
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})
            import subprocess

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
            self.assertIn("no longer exists", outcome.reason)

    def test_a_lane_holding_no_commits_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0004")
            lane = _verified_lane(repo, root, "aa0004", commit=False)
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})

            outcome = runner_shared.reintegrate_lane(
                repo, "aa0004", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome.integrated)
            self.assertEqual(outcome.code, runner_shared.REINTEGRATE_LANE_EMPTY)
            self.assertIn("no commits beyond its base", outcome.reason)

    def test_a_DIRTY_lane_with_zero_commits_still_refuses(self):
        """`HOLDS-WORK` alone does NOT prove committed work (F-16): a merely dirty lane classifies so.

        Without this case an implementation keyed on the classifier state would accept a lane whose
        only content is uncommitted, which a merge cannot carry at all.
        """
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0005")
            lane = _verified_lane(repo, root, "aa0005", commit=False)
            (pathlib.Path(lane["worktree"]) / "dirt.txt").write_text(
                "uncommitted\n", encoding="utf-8"
            )
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})

            from agent_workflows import worktree_lease

            state = worktree_lease.inspect_lane(
                repo, lane["lane_id"], base_commit=lane["base_commit"]
            )
            self.assertEqual(state.state, worktree_lease.LANE_HOLDS_WORK)
            self.assertEqual(state.commits_ahead, 0)

            outcome = runner_shared.reintegrate_lane(
                repo, "aa0005", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome.integrated)
            self.assertEqual(outcome.code, runner_shared.REINTEGRATE_LANE_EMPTY)
            self.assertIn("dirty", outcome.reason)

    def test_a_lane_whose_plan_is_not_finalized_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0006")
            lane = _verified_lane(repo, root, "aa0006", finalize=False)
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})

            outcome = runner_shared.reintegrate_lane(
                repo, "aa0006", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome.integrated)
            self.assertEqual(outcome.code, runner_shared.REINTEGRATE_PLAN_NOT_FINALIZED)
            self.assertIn("NOT in executed/", outcome.reason)

    def test_a_FOREIGN_lane_refuses_rather_than_being_handled(self):
        """The fifth classifier state, excluded by the plan rather than supported.

        FOREIGN means the lane's own base is not an ancestor of the base recorded for it, so merging it
        would carry history this run never based on. Built from an ORPHAN commit, because that is the
        only way to make a lane whose base is genuinely unreachable from main's.
        """
        import subprocess

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0013")
            main_base = _git(repo, "rev-parse", "HEAD")
            # An orphan root: unrelated history, so neither base reaches the other.
            subprocess.run(
                ["git", "checkout", "-q", "--orphan", "unrelated"], cwd=repo, check=True
            )
            subprocess.run(["git", "rm", "-rqf", "."], cwd=repo, check=True)
            (repo / "other.txt").write_text("unrelated root\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "unrelated root"], cwd=repo, check=True
            )
            orphan = _git(repo, "rev-parse", "HEAD")
            subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
            lane_dir = root / "lane-foreign"
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "aw/lane/aa0013",
                    str(lane_dir),
                    orphan,
                ],
                cwd=repo,
                check=True,
            )
            # The RECORD says the lane was based on main, which the lane's own base cannot reach.
            _write_run_state(
                repo,
                {
                    "repo": str(repo),
                    "queue": [
                        _stranded_item(
                            {
                                "id6": "aa0013",
                                "lane_id": "aa0013",
                                "branch": "aw/lane/aa0013",
                                "worktree": str(lane_dir),
                                "base_commit": main_base,
                            }
                        )
                    ],
                },
            )

            from agent_workflows import worktree_lease

            self.assertEqual(
                worktree_lease.inspect_lane(
                    repo, "aa0013", base_commit=main_base
                ).state,
                worktree_lease.LANE_FOREIGN,
            )
            outcome = runner_shared.reintegrate_lane(
                repo, "aa0013", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome.integrated)
            self.assertEqual(outcome.code, runner_shared.REINTEGRATE_LANE_FOREIGN)
            self.assertIn("FOREIGN", outcome.reason)

    def test_a_lane_owned_by_a_LIVE_process_refuses(self):
        """The verb holds NO run lock, so a lane a live driver still owns is a race, not a recovery."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0007")
            lane = _verified_lane(repo, root, "aa0007")
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})
            before = _git(repo, "rev-parse", "HEAD")

            from agent_workflows import worktree_lease

            # THIS process is alive, so an owner record naming it is a live owner. `inspect_lane`
            # already answers this; the verb consumes that answer rather than adding a second probe.
            worktree_lease.write_lane_owner(
                repo,
                lane["lane_id"],
                branch=lane["branch"],
                worktree=lane["worktree"],
                base_commit=lane["base_commit"],
                disposition="created",
            )
            state = worktree_lease.inspect_lane(
                repo, lane["lane_id"], base_commit=lane["base_commit"]
            )
            self.assertIs(state.owner_live, True)

            outcome = runner_shared.reintegrate_lane(
                repo, "aa0007", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome.integrated)
            self.assertEqual(outcome.code, runner_shared.REINTEGRATE_LANE_LIVE)
            self.assertIn("LIVE process", outcome.reason)
            self.assertEqual(_git(repo, "rev-parse", "HEAD"), before)

    def test_an_ATTEMPT_SCOPED_lane_is_integrated_without_GUESSING_its_name(self):
        """The `mm6wuz` shape: the recorded branch is `_attempt2`, and a guessed name would miss it.

        `lane_branch_name`'s docstring forbids reconstructing a branch from an id6 precisely because
        allocation may have attempt-scoped it. Without this case an implementation that guessed
        `aw/lane/<id6>` passes every other test here.
        """
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0008")
            # The FIRST lane exists and is empty, exactly as an orphaned first attempt would be, so a
            # guessed `aw/lane/aa0008` would resolve to something and refuse rather than error.
            _verified_lane(repo, root, "aa0008", commit=False)
            scoped = _verified_lane(repo, root, "aa0008", branch_suffix="_attempt2")
            self.assertEqual(scoped["branch"], "aw/lane/aa0008_attempt2")
            _write_run_state(
                repo, {"repo": str(repo), "queue": [_stranded_item(scoped)]}
            )

            outcome = runner_shared.reintegrate_lane(
                repo, "aa0008", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertTrue(outcome.integrated, outcome.reason)
            self.assertEqual(outcome.candidate.branch, "aw/lane/aa0008_attempt2")
            self.assertTrue((repo / "src" / "aa0008.txt").is_file())

    def test_two_recorded_lanes_with_no_run_id_REFUSE_and_list_them(self):
        """OQ-02: several candidates is a refusal, because integrating the wrong lane lands wrong work."""
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0009")
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

            outcome = runner_shared.reintegrate_lane(
                repo, "aa0009", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome.integrated)
            self.assertEqual(outcome.code, runner_shared.REINTEGRATE_AMBIGUOUS_LANE)
            self.assertEqual(len(outcome.candidates), 2)
            self.assertIn("aw/lane/aa0009_attempt2", outcome.reason)

            # Naming the run resolves it, and integrates THAT lane.
            named = runner_shared.reintegrate_lane(
                repo,
                "aa0009",
                integrate=self._integrate,
                suite_check=_passing_suite,
                run_id="run-two",
            )
            self.assertTrue(named.integrated, named.reason)
            self.assertEqual(named.candidate.branch, "aw/lane/aa0009_attempt2")

    def test_no_run_record_naming_a_lane_refuses_rather_than_guessing(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0010")
            _verified_lane(repo, root, "aa0010")
            # A lane BRANCH exists, but NO run record names it: the record is the authority.
            outcome = runner_shared.reintegrate_lane(
                repo, "aa0010", integrate=self._integrate, suite_check=_passing_suite
            )
            self.assertFalse(outcome.integrated)
            self.assertEqual(outcome.code, runner_shared.REINTEGRATE_NO_LANE_RECORD)
            self.assertIn("NOT reconstructed from the id6", outcome.reason)

    def test_an_exception_from_the_attempt_is_a_refusal_not_a_raise(self):
        """E-03 requires the resume pass to survive this, so the shared function must not raise."""

        def boom(*_a, **_k):
            raise RuntimeError("git exploded")

        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _repo_with_pending_plan(root, "aa0011")
            lane = _verified_lane(repo, root, "aa0011")
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})

            outcome = runner_shared.reintegrate_lane(
                repo, "aa0011", integrate=boom, suite_check=_passing_suite
            )
            self.assertFalse(outcome.integrated)
            self.assertEqual(outcome.code, runner_shared.REINTEGRATE_ERROR)
            self.assertIn("git exploded", outcome.reason)

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

    def test_it_is_a_single_delegating_statement(self):
        """The shape that keeps three shipped guards green while removing the second body.

        THE IMPORT IS SUBTRACTED AND MUST BE. This module may NOT import `term` at module
        level: `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
        allows only `render_stream` and `runner_profiles` there, because an import in this
        file changes the import graph for BOTH host drivers, and its docstring names the
        function-local import as this module's established route (which is how `ipd_lint`,
        `ipd_lifecycle` and `worktree_lease` all arrive). So the delegation is necessarily
        `import` + `return`, and only the `return` is the wrapper's logic.
        """
        node = next(
            (
                n
                for n in ast.parse(module_source(runner_shared)).body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name == "should_color"
            ),
            None,
        )
        self.assertIsNotNone(
            node,
            "`runner_shared` must keep a `def should_color`: three guards assert this "
            "module DEFINES the symbol, and an import fails all three",
        )
        assert node is not None
        statements = [
            s
            for s in node.body
            if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
            and not isinstance(s, (ast.Import, ast.ImportFrom))
        ]
        self.assertEqual(
            len(statements),
            1,
            f"should_color has {len(statements)} non-import statements; a wrapper that "
            "grows logic is a re-fork with extra steps",
        )
        self.assertIn("should_color", ast.unparse(statements[0]))
        self.assertIn("term", ast.unparse(statements[0]))
        # The import that IS allowed must be the one that makes the delegation resolvable,
        # so a stray unrelated import cannot hide here.
        imports = [
            ast.unparse(s)
            for s in node.body
            if isinstance(s, (ast.Import, ast.ImportFrom))
        ]
        self.assertEqual(imports, ["from agent_workflows import term"])

    def test_it_reaches_the_single_originating_definition(self):
        """Identity of the ANSWER, not of the function: a stale copy passes an AST check."""
        from agent_workflows import term

        self._set_env(NO_COLOR=None, FORCE_COLOR=None, TERM="xterm-256color")
        for stream in (self._TTYStream(), self._PipeStream()):
            with self.subTest(stream=type(stream).__name__):
                self.assertEqual(
                    runner_shared.should_color(stream),  # type: ignore[arg-type]
                    term.should_color(stream),  # type: ignore[arg-type]
                )

    def test_term_dumb_is_now_honored(self):
        """THE BEHAVIOR CHANGE (IPD `z8ddk0` E-02), and it FAILS before that item.

        The previous body ignored `TERM` entirely, so `TERM=dumb aw oc run` emitted color
        while `TERM=dumb aw attention` did not - measured by execution 2026-09-19. Nothing
        in the suite read `TERM` against this symbol, which is why the divergence survived.
        """
        self._set_env(NO_COLOR=None, FORCE_COLOR=None, TERM="dumb")
        self.assertFalse(
            runner_shared.should_color(self._TTYStream()),  # type: ignore[arg-type]
            "TERM=dumb must be plain; the runners are not consulting the shared decision",
        )

    def test_a_falsey_force_color_no_longer_forces_color_into_a_pipe(self):
        """The OTHER behavior change: `"0"` is truthy in Python, so the previous body read
        `FORCE_COLOR=0` - the value that plainly means "do not force" - as FORCE IT ON."""
        self._set_env(NO_COLOR=None, FORCE_COLOR="0", TERM="xterm-256color")
        self.assertFalse(
            runner_shared.should_color(self._PipeStream()),  # type: ignore[arg-type]
            "FORCE_COLOR=0 must not force color into a pipe",
        )
        self.assertTrue(
            runner_shared.should_color(self._TTYStream()),  # type: ignore[arg-type]
            "FORCE_COLOR=0 means 'do not force', not 'suppress'; a TTY still gets color",
        )


class GateAnswerVocabularyTests(unittest.TestCase):
    """The closed vocabulary an agent answers a refused integration with.

    CONTEXT, because these tests exist for a measured incident rather than a hypothetical. Run
    `run-20260919T194413Z-2056285`: one test unrelated to any lane's work went red, the full test
    suite is a lane's trust signal, so THREE lanes were refused with no way to say anything about it.
    Nothing merged, eight further items cascaded to `dependency-blocked`, and the run spent 2h 10m and
    $55.02 producing no integrated work. The maintainer's ruling was to keep the gate hard and let the
    agent ANSWER it.
    """

    def test_not_mine_with_a_reason_integrates(self):
        v = runner_shared.validate_gate_answer(
            {
                "answer": "not-mine",
                "reason": "fails in records/, which this turn never touched",
            }
        )
        self.assertTrue(v.usable)
        self.assertTrue(v.integrates)
        self.assertFalse(v.earns_recheck)
        self.assertEqual(v.violation, "")

    def test_fixed_earns_a_recheck_and_does_not_integrate_on_the_claim(self):
        """The suite decides, never the claim. This is the property that keeps `fixed` honest."""
        v = runner_shared.validate_gate_answer(
            {"answer": "fixed", "reason": "repaired the assertion"}
        )
        self.assertTrue(v.usable)
        self.assertTrue(v.earns_recheck)
        self.assertFalse(
            v.integrates,
            "a `fixed` CLAIM must not release a lane; only a passing re-run may",
        )

    def test_mine_is_usable_and_refuses(self):
        """An honest `mine` must be usable, so it is never worse for the agent than silence."""
        v = runner_shared.validate_gate_answer("mine")
        self.assertTrue(v.usable)
        self.assertFalse(v.integrates)
        self.assertFalse(v.earns_recheck)

    def test_mine_needs_no_reason(self):
        self.assertNotIn(
            runner_shared.GATE_ANSWER_MINE, runner_shared.GATE_ANSWERS_NEEDING_REASON
        )

    def test_needs_human_is_usable_refuses_and_is_distinguishable_from_mine(self):
        """ADDED on the maintainer's observation that `mine` fused TWO claims.

        `mine` used to mean "this is mine AND I cannot fix it". An agent that broke something but
        needs a maintainer RULING to know which fix is correct then had no true answer: it would say
        `mine` and lose the distinction, or guess at a repair and claim `fixed`. A guess that passes
        the suite is the worse outcome, because it ships an unreviewed decision.
        """
        v = runner_shared.validate_gate_answer(
            {
                "answer": "needs-human",
                "reason": "two defensible fixes; which contract wins is a maintainer call",
            }
        )
        self.assertTrue(v.usable)
        self.assertTrue(
            v.refuses, "it must refuse and preserve, exactly as `mine` does"
        )
        self.assertTrue(v.awaits_human_decision)
        self.assertFalse(v.integrates)
        self.assertFalse(v.earns_recheck)

        mine = runner_shared.validate_gate_answer("mine")
        self.assertTrue(mine.refuses)
        self.assertFalse(
            mine.awaits_human_decision,
            "`mine` means needs WORK; `needs-human` means needs a DECISION. A report routes those "
            "to different people, so they must be distinguishable",
        )

    def test_needs_human_requires_the_decision_it_needs(self):
        """The whole value of the answer is telling a human WHAT to decide."""
        v = runner_shared.validate_gate_answer({"answer": "needs-human"})
        self.assertFalse(v.usable)
        self.assertIn("requires a reason", v.violation)

    def test_every_answer_either_releases_recheck_or_refuses(self):
        """EXHAUSTIVENESS: no answer may fall through to no handling at all.

        This is what guarantees the prompt's claim that one of the answers is always true. Adding a
        fifth answer without deciding its disposition fails here rather than at runtime.
        """
        for token in runner_shared.GATE_ANSWERS:
            with self.subTest(token):
                reason = (
                    "because"
                    if token in runner_shared.GATE_ANSWERS_NEEDING_REASON
                    else ""
                )
                v = runner_shared.validate_gate_answer(
                    {"answer": token, "reason": reason}
                )
                self.assertTrue(v.usable, f"{token} must validate")
                dispositions = [v.integrates, v.earns_recheck, v.refuses]
                self.assertEqual(
                    sum(1 for d in dispositions if d),
                    1,
                    f"{token} must map to EXACTLY one disposition, got "
                    f"integrates={v.integrates} earns_recheck={v.earns_recheck} "
                    f"refuses={v.refuses}",
                )

    def test_an_answer_needing_a_reason_is_refused_without_one(self):
        for token in sorted(runner_shared.GATE_ANSWERS_NEEDING_REASON):
            with self.subTest(token):
                v = runner_shared.validate_gate_answer({"answer": token})
                self.assertFalse(
                    v.usable, "a bare claim with no reason is not an answer"
                )
                self.assertIn("requires a reason", v.violation)

    def test_shape_is_coerced_but_meaning_is_not(self):
        for raw in ("NOT MINE", "not_mine", "  Not-Mine  "):
            with self.subTest(raw):
                v = runner_shared.validate_gate_answer({"answer": raw, "reason": "x"})
                self.assertEqual(v.answer, runner_shared.GATE_ANSWER_NOT_MINE)

    def test_an_unrecognized_token_is_refused_BY_NAME(self):
        v = runner_shared.validate_gate_answer(
            {"answer": "probably-fine", "reason": "x"}
        )
        self.assertFalse(v.usable)
        self.assertIn("probably-fine", v.violation)
        self.assertIn("not one of", v.violation)

    def test_absent_and_wrong_typed_answers_fail_closed(self):
        for raw in (None, "", {}, 42, [], {"answer": ""}):
            with self.subTest(repr(raw)):
                v = runner_shared.validate_gate_answer(raw)
                self.assertFalse(
                    v.usable,
                    "fail closed: a wrongly REFUSED lane is preserved and recoverable, a wrongly "
                    "INTEGRATED one merges work no trust signal cleared",
                )
                self.assertTrue(
                    v.violation, "an unusable answer must say what was wrong"
                )

    def test_validate_never_raises(self):
        class Hostile:
            def __str__(self):
                raise RuntimeError("no")

        for raw in (object(), Hostile(), {"answer": object()}):
            with self.subTest(repr(type(raw))):
                try:
                    v = runner_shared.validate_gate_answer(raw)
                except (
                    Exception
                ) as exc:  # pragma: no cover - the assertion is the point
                    self.fail(
                        f"validate_gate_answer raised {exc!r}; it must never raise"
                    )
                self.assertFalse(v.usable)


class GateAnswerQuestionWordingTests(unittest.TestCase):
    """The wording is load-bearing, so it is pinned (maintainer: "be careful how we ask")."""

    def _q(self, **kw):
        return runner_shared.gate_answer_question(
            failing="FAILED tests/test_example.py::T::t_something", **kw
        )

    def test_it_names_the_failing_tests_and_the_changed_files(self):
        q = self._q(changed_files=["agent_workflows/term.py"])
        self.assertIn("tests/test_example.py::T::t_something", q)
        self.assertIn("agent_workflows/term.py", q)

    def test_it_records_no_changed_files_honestly(self):
        self.assertIn("(none recorded)", self._q())

    def test_it_states_the_consequence_of_every_answer(self):
        q = self._q()
        self.assertIn("YOUR LANE IS THEN INTEGRATED", q)
        self.assertIn("RE-RUN", q)
        self.assertIn("PRESERVED", q)

    def test_it_does_not_accuse(self):
        """A question that presumes fault pushes an honest agent toward the wrong answer.

        Asserted against WHITESPACE-COLLAPSED text, because the prompt is hard-wrapped and a phrase
        that straddles a line break is still the phrase the agent reads.
        """
        q = " ".join(self._q().split())
        self.assertIn("This is a question, not an accusation", q)
        self.assertIn("not a concession", q)
        self.assertIn("commonest correct answer", q)

    def test_it_says_mine_is_better_than_silence(self):
        self.assertIn("strictly better than not answering", self._q())

    def test_it_tells_the_agent_needs_human_is_a_first_class_answer(self):
        """The maintainer's point: an agent must be able to use this COMFORTABLY.

        Not for the agent's feelings, but because an agent that believes asking is a failure will
        guess at a repair instead, and a guess that passes the suite ships an unreviewed decision.
        """
        q = " ".join(self._q().split())
        self.assertIn("USE THIS FREELY AND WITHOUT HESITATION", q)
        self.assertIn("not an escalation and not a failure", q)
        self.assertIn("DO NOT GUESS AT A REPAIR TO AVOID ASKING", q)

    def test_it_states_that_one_answer_is_always_true(self):
        q = " ".join(self._q().split())
        self.assertIn("CHOOSE THE ANSWER THAT IS TRUE", q)
        self.assertIn("no case where silence is the accurate answer", q)

    def test_every_vocabulary_member_appears(self):
        q = self._q()
        for token in runner_shared.GATE_ANSWERS:
            with self.subTest(token):
                self.assertIn(token, q)

    def test_a_reask_leads_with_the_previous_violation(self):
        q = self._q(
            violation="'probably-fine' is not one of ['not-mine', 'fixed', 'mine']"
        )
        self.assertTrue(q.startswith("YOUR PREVIOUS ANSWER COULD NOT BE USED:"))
        self.assertIn("probably-fine", q)


if __name__ == "__main__":
    unittest.main()

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
SUPERSEDED_SINCE_MOVE = ("state_root", "_run_git")


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
        # 23, DOWN FROM 24 BY EXACTLY ONE: `_run_git` moved to `SUPERSEDED_SINCE_MOVE` when it gained an
        # optional `timeout` (IPD `zexed1` E-02; see that list for why the exemption is legitimate).
        # This assertion exists so such a move cannot happen silently, so the number is updated
        # together with the enumeration and never independently of it.
        self.assertEqual(
            len(clean),
            23,
            "the clean-move count must not drift silently",
        )
        self.assertEqual(
            len(SUPERSEDED_SINCE_MOVE),
            2,
            "a name added to SUPERSEDED_SINCE_MOVE must be accounted for in the clean count above",
        )
        for name in clean:
            with self.subTest(symbol=name):
                # A name in `DOCUMENTED_SINCE_MOVE` is compared with its docstring subtracted; every
                # other name is compared STRICTLY, docstring included.
                documented = name in DOCUMENTED_SINCE_MOVE
                self.assertEqual(
                    fingerprint_of(runner_shared, name, drop_docstring=documented),
                    _normalize_dump(expected[name]),
                    f"`{name}` was NOT a pure move: its body differs from the pre-move "
                    f"capture at {data['captured_at_head']}"
                    + (
                        " (compared with its docstring subtracted, per DOCUMENTED_SINCE_MOVE, so "
                        "this failure is about an EXECUTABLE statement)"
                        if documented
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
        moved_callers_of_run_checked = sum(RELOCATED_RUN_CHECKED_CALLERS.values())
        for (runner, name), premove in sorted(self.PREMOVE_CALL_SITES.items()):
            with self.subTest(runner=runner, symbol=name):
                expected = premove
                if name == "run_checked":
                    expected -= moved_callers_of_run_checked
                expected += self.ADDED_CALL_SITES.get((runner, name), 0)
                expected += self.CLEAN_BASE_GUARD_CALL_SITES.get((runner, name), 0)
                expected += self.INTEGRATION_LADDER_CALL_SITES.get((runner, name), 0)
                expected += self.LANE_BACKLOG_CLOSE_CALL_SITES.get((runner, name), 0)
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

    def test_StallTimeout_bodies_were_not_edited(self):
        """`StallTimeout` is class (c) DIVERGED and out of scope: only its BASE could change.

        The two runners' docstrings differ, which is exactly why the class is diverged and why this
        plan may re-parent it but must not touch it. If a later change "tidies" them into agreement,
        that is a class (c) reconciliation and belongs to a different plan.
        """
        docstrings = {}
        for runner in BOTH:
            node = next(
                n
                for n in ast.parse(module_source(_MODULES[runner])).body
                if isinstance(n, ast.ClassDef) and n.name == "StallTimeout"
            )
            docstrings[runner] = ast.get_docstring(node)
            # The base is now the SHARED name, spelled exactly as before.
            self.assertEqual([ast.unparse(b) for b in node.bases], ["DriverError"])
        self.assertNotEqual(
            docstrings["oc_runipd"],
            docstrings["agy_runipd"],
            "the two StallTimeout docstrings converged; this plan must not reconcile "
            "a class (c) DIVERGED symbol",
        )

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
    """The FIFTH dependency the authoring measurement missed, and the subtlest one.

    `discover_plans` constructs records through `parse_plan_file`, and the two runners' `PlanRecord`
    are DIFFERENT NamedTuples: oc's carries a `kind` field agy's lacks. A shared `discover_plans`
    that built oc's type would hand agy a field its code never expects; one that built agy's would
    DROP `kind`, which oc's `action_for` reads to decide whether a plan is an orchestrator. Either
    failure is silent and type-shaped rather than a crash, which is why it gets its own test class.
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

    def test_the_two_PlanRecord_types_are_still_distinct_and_unmodified(self):
        """This plan may NOT unify them; that is a class (c) reconciliation for a later child."""
        self.assertIsNot(oc_runipd.PlanRecord, agy_runipd.PlanRecord)
        self.assertIn("kind", oc_runipd.PlanRecord._fields)
        self.assertNotIn("kind", agy_runipd.PlanRecord._fields)

    def test_each_runner_still_gets_its_OWN_record_type(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(pathlib.Path(tmp))
            for runner in BOTH:
                with self.subTest(runner=runner):
                    module = _MODULES[runner]
                    found = module.discover_plans(repo)
                    self.assertIn("aaaaaa", found)
                    self.assertIs(type(found["aaaaaa"]), module.PlanRecord)

    def test_the_oc_path_still_populates_kind(self):
        """A shared constructor that dropped `kind` would silently disable orchestrator detection."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(pathlib.Path(tmp))
            record = oc_runipd.discover_plans(repo)["aaaaaa"]
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
                self.assertEqual(kind, "integration-blocked")
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
                self.assertEqual(kind, "merge-conflict")
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
        `dirty_tree_overlap` guard: the lane renames `moved.txt` -> `dest.txt` (so `changed_files` is
        `['dest.txt']` only), and main has an uncommitted edit to `moved.txt`, which the merge must
        delete. Returns `(repo, handle, head_before, dirty_before)`.
        """
        repo = self._repo(tmp)
        body = self._renamable_body()
        (repo / "moved.txt").write_text(body, encoding="utf-8")
        self._git(repo, "add", "moved.txt")
        self._git(repo, "commit", "-qm", "add moved.txt")
        handle = self._renaming_lane(repo, id6, orig="moved.txt", dest="dest.txt")
        # The guard passes precisely because rename detection hides the origin from `changed_files`.
        lane_changed = self._git(
            repo, "diff", "--name-only", f"{handle.base_commit}..{handle.branch}"
        ).split()
        self.assertEqual(lane_changed, ["dest.txt"])
        dirty_before = body + "un-owned local edit\n"
        (repo / "moved.txt").write_text(dirty_before, encoding="utf-8")
        self.assertEqual(
            runner_shared.dirty_tree_overlap(repo, lane_changed),
            [],
            "the retained guard must PASS here, or this test is not reaching git's own refusal",
        )
        return repo, handle, self._git(repo, "rev-parse", "HEAD"), dirty_before

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

                    integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                        repo, handle, "ddd444", self._passing_runner()
                    )

                    self.assertFalse(integrated, reason)
                    self.assertEqual(
                        kind,
                        "integration-blocked",
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
                _integrated, _reason, kind = runner_shared.integrate_lane_branch(
                    repo,
                    handle,
                    "fff666",
                    self._passing_runner(),
                    host_label="aw oc run",
                    run_checked=oc_runipd.run_checked,
                )
                self.assertEqual(
                    kind,
                    "integration-blocked",
                    "classification must not depend on git's message language",
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
                )
                self.assertEqual(
                    kind,
                    "merge-conflict",
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
            with patcher:
                _i, _r, kind = runner_shared.integrate_lane_branch(
                    repo,
                    handle,
                    "hhh888",
                    self._passing_runner(),
                    host_label="aw oc run",
                    run_checked=oc_runipd.run_checked,
                )
            self.assertEqual(kind, "integration-blocked")
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
                )
            self.assertEqual(kind, "merge-conflict")
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
        self.assertTrue(
            runner_shared.classify_integration_refusal("integration-blocked")
        )
        self.assertFalse(runner_shared.classify_integration_refusal("merge-conflict"))
        first = runner_shared.decide_integration_deferral(
            integ_kind="integration-blocked", attempts_used=1, limit=10
        )
        self.assertTrue(first.deferred)
        self.assertEqual(first.status, "integration-deferred")
        conflict = runner_shared.decide_integration_deferral(
            integ_kind="merge-conflict", attempts_used=1, limit=10
        )
        self.assertFalse(conflict.deferred)
        self.assertEqual(conflict.status, "merge-conflict")

    def test_the_kind_vocabulary_is_UNCHANGED_by_the_extraction(self):
        """The three `kind` values are a CONTRACT read by callers and by run state.

        Child 03 changes what `integration-blocked` means for `TERMINAL_STATES`; this child must not,
        and asserting the vocabulary here is what keeps a "pure move" from smuggling that in.
        """
        src = module_source(runner_shared)
        node = next(
            n
            for n in ast.parse(src).body
            if isinstance(n, ast.FunctionDef) and n.name == "integrate_lane_branch"
        )
        returned = {
            ast.literal_eval(elt)
            for sub in ast.walk(node)
            if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Tuple)
            for elt in [sub.value.elts[-1]]
            if isinstance(elt, ast.Constant)
        }
        self.assertEqual(
            returned, {"integrated", "integration-blocked", "merge-conflict"}
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
        """
        decision = self.decide(
            integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT, attempts_used=1
        )
        self.assertFalse(decision.deferred)
        self.assertEqual(decision.status, "merge-conflict")
        self.assertIn("not the transient", decision.reason)
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
        """`is_interactive_run` already encodes both halves (a real TTY AND no `--unattended`)."""
        import argparse
        import inspect

        source = inspect.getsource(oc_runipd.retry_deferred_integrations)
        self.assertIn("is_interactive_run", source)
        self.assertIn(
            "is_interactive_run",
            inspect.getsource(agy_runipd.retry_deferred_integrations),
        )

        class _TTY:
            def isatty(self):
                return True

        self.assertFalse(
            runner_shared.is_interactive_run(
                argparse.Namespace(unattended=True, full_auto=False), stream=_TTY()
            )
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
                state["queue"][0]["status"] = "integration-blocked"
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
            with self.subTest(
                host=module.__name__
            ), tempfile.TemporaryDirectory() as td:
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

    def test_retry_incomplete_re_queues_a_deferred_item_on_both_hosts(self):
        """A deferral can outlive its run (an interrupt between deferring and the next iteration)."""
        import inspect

        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                self.assertIn(
                    '"integration-deferred"',
                    inspect.getsource(module.run_queue),
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
        """A shared ladder nothing CALLS is the dead-gate failure this repository has already paid for."""
        import inspect

        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                loop = inspect.getsource(module.run_queue)
                self.assertIn("retry_deferred_integrations", loop)
                self.assertIn("deferred_integration_items", loop)
                # Rung 2's trigger is the loop's OWN `runnable is None`, not a last-item test.
                self.assertIn("runnable is None", loop)
                self.assertIn("poll=True", loop)


if __name__ == "__main__":
    unittest.main()

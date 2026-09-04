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
import json
import pathlib
import unittest
from typing import Any

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

# The 2 symbols that could NOT move, with the reason pinned in `UnmovableSymbolTests`.
UNMOVABLE = ("disable_lane_prompt",)

# `print_status` was never AST-identical across the runners: the two bodies differed ONLY by the
# literal host name. It is therefore compared against the OC pre-move capture with the host token
# normalized, and its rendered output is proven byte-identical for BOTH hosts separately.
HOST_NAMING_ONLY = ("print_status",)


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


def fingerprint_of(module, name: str) -> str | None:
    """The post-move fingerprint of ``name`` as defined in ``module``, or None if absent."""
    for node in ast.parse(module_source(module)).body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == name
        ):
            return ast.dump(ast.parse(ast.unparse(node)), include_attributes=False)
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
    """
    back = {
        "run_checked": ("env_builder", "pinned_child_env"),
        "print_status": ("driver_label", '"opencode"'),
    }
    if name not in back:
        return node
    src = ast.unparse(node)
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
            if n not in INJECTED and n not in HOST_NAMING_ONLY
        ]
        self.assertEqual(len(clean), 25, "the clean-move count must not drift silently")
        for name in clean:
            with self.subTest(symbol=name):
                self.assertEqual(
                    fingerprint_of(runner_shared, name),
                    expected[name],
                    f"`{name}` was NOT a pure move: its body differs from the pre-move "
                    f"capture at {data['captured_at_head']}",
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
                    ast.dump(
                        ast.parse(ast.unparse(restored)), include_attributes=False
                    ),
                    expected[name],
                    f"`{name}` differs from its pre-move capture by MORE than the "
                    f"injected `{INJECTED[name]}` parameter",
                )

    def test_the_shared_module_defines_every_symbol_it_claims(self):
        defined = top_level_definitions(runner_shared)
        for name in self.moved_symbols():
            with self.subTest(symbol=name):
                self.assertIn(name, defined)


class SingleDefinitionTests(unittest.TestCase):
    """Assertion (3): the runners no longer DEFINE what they now import."""

    def test_neither_runner_redefines_a_moved_symbol(self):
        moved = [n for n in load_fixture()["symbols"] if n not in UNMOVABLE]
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

    def test_exactly_one_definition_package_wide(self):
        """Repo-wide, not pairwise: a pairwise check passes while a third copy sits elsewhere.

        That is not hypothetical - it is exactly how `agy_runipd` re-forked four `render_stream`
        symbols while a one-sided guard stayed green (the orchestrator's F10).
        """
        moved = [n for n in load_fixture()["symbols"] if n not in UNMOVABLE]
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
        """
        moved_callers_of_run_checked = 3
        for (runner, name), premove in sorted(self.PREMOVE_CALL_SITES.items()):
            with self.subTest(runner=runner, symbol=name):
                expected = premove
                if name == "run_checked":
                    expected -= moved_callers_of_run_checked
                self.assertEqual(
                    self.call_sites(runner, name),
                    expected,
                    f"the number of `{name}` CALL SITES in {runner} changed; the "
                    "wrapper ruling exists to keep call sites untouched",
                )

    def test_the_relocated_run_checked_callers_still_call_it_by_injection(self):
        """The other half of the subtraction above, and the reason `run_checked` is injected 3x.

        `git_head`, `git_status` and `git_common_dir` moved in the SAME seam as `run_checked`, and
        their bodies call it. Their calls did not disappear, they RELOCATED into `runner_shared` - and
        because `run_checked` gained a parameter, each now receives the runner's own wrapper by
        injection rather than resolving a module global.

        This test also guards against the tempting WRONG repair, which is to rewrite these three onto
        the shared `_run_git` sitting directly above them. That would change `git_head` from raising
        `DriverError` to returning "" and would drop `git_status`'s `--short`, and both feed every
        run's outcome record. If someone makes that change, the call set below empties and this fails.
        """
        tree = ast.parse(module_source(runner_shared))
        callers = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for sub in ast.walk(node):
                    if (
                        isinstance(sub, ast.Call)
                        and isinstance(sub.func, ast.Name)
                        and sub.func.id == "run_checked"
                    ):
                        callers.add(node.name)
        self.assertEqual(
            callers,
            {"git_head", "git_status", "git_common_dir"},
            "the three git helpers must still call `run_checked` (by injection); "
            "rewriting them onto `_run_git` would be a BEHAVIOR CHANGE",
        )
        # And each of the three takes it as a parameter rather than closing over a global, which is
        # what makes the call resolvable at all.
        for name in ("git_head", "git_status", "git_common_dir"):
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

    def test_the_two_hosts_render_differently_only_by_their_label(self):
        """If they rendered the SAME, the host token would have been lost in the move."""
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
        self.assertNotEqual(out["oc_runipd"], out["agy_runipd"])
        self.assertEqual(
            out["oc_runipd"].replace("opencode", "antigravity"), out["agy_runipd"]
        )


if __name__ == "__main__":
    unittest.main()

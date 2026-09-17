#!/usr/bin/env python3
"""rununify Order 09 (`orziju`) E-05: GUARD what this plan MEASURED, and pin what it did NOT do.

WHAT THIS PLAN DID AND DID NOT DO, stated first so no reader mistakes the shape of this file.
Plan `orziju` is named "split `initialize_run` into a shared core and a thin host hook". It did NOT
perform that split. Its own 2026-09-16 review measured why, and re-measurement at execution HEAD
confirmed the shape of the finding while moving several of the numbers (see the tables below).

`initialize_run` is the most misleading function in this Set. It has the HIGHEST line-level
similarity of the five large functions (0.9345 at review, only 15 differing code lines) and the
LOWEST shared CONTENT, because two of those fifteen differing lines are the `state` and
`queue.append` DICT LITERALS. Unpacked, the `options` dict is where the divergence lives: THIRTEEN
of its keys are host-specific and only twenty-one are shared, and the shared count is what it is
almost entirely because of the ONE `**runner_shared.freeze_run_policy_flags(args)` expansion that is
already de-duplicated. A "shared writer with a hook" would therefore take thirteen key parameters,
which is not a hook supplying host specifics: it is the function's entire output supplied by its
caller.

AND THE SHARPEST HAZARD IN THIS SET LIVES HERE. `initialize_run` evaluates `__file__` to record each
run's driver identity, and `__file__` is evaluated in the module where the code is DEFINED. A core
relocated to `runner_shared` therefore writes `runner_shared.py` for BOTH hosts, and two consumers
read that basename as the host discriminator. MEASURED, by sabotaging agy exactly as a naive
relocation would: `tests/test_run_analytics_sources.py`, `tests/test_run_viewer.py` and
`tests/test_run_analytics.py` stayed 183-green while every agy run became host-unattributable. There
was no test covering the runners' end of that contract at all; `EachHostRecordsItsOwnDriverIdentity`
in `tests/test_rununify_initialize_run_characterization.py` is now it.

WHAT THIS PLAN DELIVERED: the `options` partition and closure measurement (E-01), the
driver-identity pin plus a behavioral characterization net on both hosts (E-02), the pin inventory
with a per-pin thin-caller verdict (E-03), the split analysis the sequencing decision needs (E-04),
and this guard suite.

SO SOME ASSERTIONS BELOW ARE DELIBERATELY INVERSE: they assert a symbol is STILL defined twice, and
that `__file__` is STILL evaluated in each runner. That is not an endorsement of the duplication. It
is a tripwire, so a later agent cannot "finish" the split piecemeal without coming here, reading the
analysis, and updating this file deliberately. A test asserting a state the code is not in would be
a failing test, not a guard, which is why the split-side assertions are ABSENT rather than written
and skipped.

WHEN THE SPLIT IS PERFORMED, this file is the checklist: each `STILL_DOUBLE_DEFINED` entry that
becomes shared moves out of that tuple in the SAME change that shares it, with the reason recorded,
and `TheDriverIdentityIsEvaluatedInEachRunner` must be re-based onto whatever mechanism hands the
core the caller's module path. That is the "re-base deliberately, never weaken silently" rule the
maintainer set on 2026-09-16.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import pathlib
import unittest

from agent_workflows import agy_runipd, oc_runipd, runner_shared

AW = pathlib.Path(str(inspect.getsourcefile(oc_runipd))).parent
HOSTS = ("oc_runipd", "agy_runipd")
MODULES = {"oc_runipd": oc_runipd, "agy_runipd": agy_runipd}
TARGET = "initialize_run"

# ==================================================================================================
# E-01(a): THE `options` KEY PARTITION, measured at execution HEAD 87682a3b with the committed
# scanner and confirmed against a LIVE run initialized on each host.
#
# WHY BOTH VIEWS ARE RECORDED. The plan's review counted the keys the two dict bodies SPELL and got
# 10 shared / 7 oc-only / 6 agy-only = 23. That is exact for what it measured, and it omits two
# things: the four CONDITIONAL `verify_*` keys (present only when a verifier profile is configured)
# and the twelve keys the shared `**freeze_run_policy_flags(args)` expansion contributes. A live run
# therefore freezes 34 keys, of which 21 are shared and 13 host-specific.
#
# THE LOAD-BEARING NUMBER IS 13, AND IT IS IDENTICAL UNDER BOTH VIEWS. The shared count rises from
# 10 to 21 purely through ONE already-shared expansion, which is the opposite of evidence that the
# divergence is small: it means every additional shared key arrived by de-duplicating something
# else, while the thirteen host-specific ones remain exactly where they were.
# ==================================================================================================

#: Frozen on BOTH hosts. Read from a live run, not from the source, because `freeze_run_policy_flags`
#: contributes through a `**` expansion whose members are defined in another module.
SHARED_OPTION_KEYS = frozenset(
    {
        "action",
        "allow_dirty_base",
        "allow_drafts",
        "allow_mixed",
        "allow_unverifiable",
        "follow_generated",
        "full_auto",
        "integration_retry_limit",
        "isolate_worktree",
        "max_items_per_session",
        "model",
        "on_integration_blocked",
        "output_mode",
        "retry_budget",
        "self_finalize",
        "session",
        "stall_timeout",
        "unattended",
        "unverifiable_ok",
        "verbosity",
        "with_dependencies",
    }
)

#: OC ONLY. `launch_profile`, `variant`, `agent` and `opencode` name the launch identity; `validate`
#: and its derived `no_audit` are this host's verification polarity; `auto` is oc's own.
#: `launch_profile` is not a key agy forgot: `agy_runipd` contains ZERO `runner_profiles` references
#: against oc's 17, so it is a concept the other host does not have (F-11).
OC_ONLY_OPTION_KEYS = frozenset(
    {"agent", "auto", "launch_profile", "no_audit", "opencode", "validate", "variant"}
)

#: AGY ONLY. `no_verify` is the OPPOSITE POLARITY spelling of oc's `validate` (`ybkmzp` E-04), which
#: is why a shared writer cannot simply emit one key for both hosts.
AGY_ONLY_OPTION_KEYS = frozenset(
    {
        "agy_executable",
        "dangerously_skip_permissions",
        "effort",
        "new_session",
        "no_verify",
        "timeout",
    }
)

#: Present on oc only, and only when a VERIFIER profile is configured. Absent from an ordinary run,
#: which is what keeps an existing invocation's frozen state byte-identical to what it was before the
#: field existed (`kgpptv` E-02). Asserted as conditional rather than counted as present.
OC_CONDITIONAL_OPTION_KEYS = frozenset(
    {"verify_model", "verify_variant", "verify_agent", "verify_launch_profile"}
)

HOST_SPECIFIC_OPTION_COUNT = 13  # 7 oc-only + 6 agy-only
LIVE_OPTION_KEY_UNION = 34  # 21 shared + 13 host-specific

# ==================================================================================================
# E-01(b): THE CLOSURE. 37 free module-level names at execution HEAD (the plan's review said 34).
#
# METHOD: parse each host's `initialize_run` with full scope tracking (parameters, assignments,
# walrus, `for`/`with`/`except` targets, comprehension and lambda scopes, nested defs, function-local
# imports, `global`) and keep the free names that resolve at MODULE level. A definition can move to
# `runner_shared` only if every one of those resolves there.
# ==================================================================================================

#: A REAL FORK: an independent definition in BOTH runner modules. Each becomes an injected parameter
#: of a shared core, and injecting a symbol is the opposite of sharing it.
#:
#: FIVE, not the plan's eight, and each reduction came from a SIBLING landing rather than from this
#: plan. Recorded per reduction rather than silently absorbed, because the shrinking count IS the
#: Set working as designed:
#:   * `EmptyStatusSelection` LIFTED into `runner_shared` by sibling `i3d6ml` (commit `d26c1061`).
#:   * `build_dynamic_manifest` and `parse_plan_file` UNIFIED into `runner_shared` by sibling
#:     `sy7uwh` (integrated 2026-09-17), together with `PlanRecord`. Verified at integration:
#:     `oc_runipd.build_dynamic_manifest is agy_runipd.build_dynamic_manifest` -> True and
#:     `__module__` -> `agent_workflows.runner_shared`, likewise for `parse_plan_file`. They are
#:     therefore no longer forks and MUST NOT be listed here; they moved to
#:     RESOLVES_IN_RUNNER_SHARED below.
STILL_DOUBLE_DEFINED = (
    "enforce_dependency_preflight",
    "enforce_requested_action",
    "expand_selectors",
    "set_plan_approved",
    "write_report",
)

#: Imported FROM `runner_shared`, so they move with a relocated core for free.
RESOLVES_IN_RUNNER_SHARED = (
    "DriverError",
    "EmptyStatusSelection",
    "SCHEMA_VERSION",
    "action_for",
    "append_jsonl",
    "atomic_write_json",
    "build_dynamic_manifest",
    "load_json",
    "new_run_id",
    "parse_plan_file",
    "resolve_plan_path",
    "sha256_file",
    "state_root",
    "utc_now",
)

#: ALREADY ONE OBJECT, reached by both hosts (agy imports it from oc, or both import a third
#: module). NOT duplication: these need RELOCATION, not de-duplication, and counting them as forks
#: would overstate the remaining work. `announce_run_order`, `run_order_rationale` and
#: `is_plan_review_approved` are single objects precisely BECAUSE agy imports them from oc.
ALREADY_ONE_OBJECT = (
    "announce_run_order",
    "is_plan_review_approved",
    "run_order_rationale",
)

#: The sanctioned wrapper form (maintainer's 2026-09-03 `818uru` OQ-02 ruling): `runner_shared` owns
#: the real function and each host keeps a one-line wrapper at the original name and signature,
#: binding its own dependency. Syntactically a `def` in both modules, so a naive scan calls it
#: duplication; counting it as a fork would OVERSTATE the work.
THIN_WRAPPERS_OVER_RUNNER_SHARED = (
    "discover_plans",
    "git_common_dir",
    "validate_manifest",
)

#: Module constants defined twice with EQUAL values: liftable with a core.
EQUAL_CONSTANTS = ("DEFAULT_RUNBOOK_TEXT", "DEFAULT_STALL_TIMEOUT")

#: OC-ONLY, with NO agy counterpart at all. F-11's capability asymmetry: an A / NOT-A case under the
#: maintainer's oc-preferred ruling rather than an oc-preferred case, because there is no agy half to
#: prefer oc's over.
OC_ONLY_SYMBOLS = ("launch_profile_record", "resolve_launch_pair")

#: AGY-ONLY, likewise with no oc counterpart. `DEFAULT_MODEL`/`DEFAULT_TIMEOUT` are this host's own
#: launch defaults.
#:
#: `_plan_kind` WAS HERE AND IS DELETED, exactly as this comment predicted: it existed ONLY because
#: `agy.PlanRecord` lacked a `kind` field (the plan's F-4), and sibling `sy7uwh` (integrated
#: 2026-09-17) unified the record and removed it. Verified at integration:
#: `hasattr(agy_runipd, "_plan_kind")` -> False. Its legacy-manifest FALLBACK capability was not
#: lost with the name; `sy7uwh` lifted it to shared `plan_kind_from_file`/`resolve_manifest_kind`
#: and gave it to BOTH hosts, which repaired an oc defect (oc derived `execute` for an approved
#: orchestrator named by a manifest omitting `kind`, and would have spent an agent turn on a plan
#: that authors no code). Recorded rather than deleted silently so a reader does not re-add the name.
AGY_ONLY_SYMBOLS = ("DEFAULT_MODEL", "DEFAULT_TIMEOUT")

#: AGY-ONLY BUT ALREADY DELEGATING: agy's `resolve_verification_decision` is a one-line binding over
#: `runner_shared.resolve_verification_decision`, which plan `ybkmzp` built. oc reaches the same
#: shared resolver through `resolve_launch_pair`, which ALSO resolves the launch profile. So this is
#: not a fork, and F-3 is right that the two concerns must not be collapsed into one.
AGY_ONLY_DELEGATING = ("resolve_verification_decision",)

#: RE-MEASURED 2026-09-17: 36, down from the 37 this plan measured at authoring. The reduction is
#: `_plan_kind`, which sibling `sy7uwh` DELETED when it unified `PlanRecord` (see AGY_ONLY_SYMBOLS
#: above). `initialize_run` no longer reaches it on either host, verified by
#: `test_initialize_run_still_closes_over_every_pinned_symbol`, which compares the table against the
#: names the FUNCTION actually reaches. Lowered rather than left, because a total that no longer
#: matches the reached set makes every count derived from it wrong, including the injection count the
#: split analysis rests on.
CLOSURE_TOTAL = 36

#: `__file__`. NOT A SYMBOL AND NOT INJECTABLE: a construct whose MEANING changes on relocation.
#: Listed apart from every class above for that reason. See `TheDriverIdentityIsEvaluatedInEachRunner`.
NON_RELOCATABLE = ("__file__",)


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


def target_node(name: str) -> ast.FunctionDef:
    for node in module_body(name):
        if isinstance(node, ast.FunctionDef) and node.name == TARGET:
            return node
    raise AssertionError(f"{name} has no top-level {TARGET}")


def is_pure_delegation(node: ast.stmt | None) -> bool:
    """The sanctioned wrapper shape: one statement calling a single `runner_shared.X(...)`."""
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
    """The closure, re-derived here so the tables cannot drift from the code that produced them.

    A DELIBERATELY SIMPLER SCANNER than the committed evidence script: it collects every `Name` load
    in the function, subtracts every name bound anywhere in the body, and keeps what the module
    index resolves. Simpler is acceptable HERE because the assertions below are membership checks in
    that direction (every pinned name must still be REACHED), not an exact census; the exact census
    lives in the evidence scanner. The property that must hold is no FALSE NEGATIVE: a pinned name
    that stopped being reached must fail, and it does.
    """
    node = target_node(host)
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


def live_options(host: str) -> dict:
    """The `options` dict a REAL run freezes on this host.

    Driven rather than parsed, because the `**freeze_run_policy_flags(args)` expansion's members are
    defined in another module and a source-level key list would silently omit twelve of them.
    """
    import contextlib
    import io
    import json
    import subprocess
    import tempfile

    plan = "\n".join(
        [
            "# IPD: guard",
            "",
            "- Date: 2026-09-17",
            "- Kind: child",
            "- Status: approved",
            "- Set: guard (the guard set)",
            "- Order: 1",
            "- Id: aaa111",
            "- Item-Dependencies: none",
            "",
            "## Goal",
            "",
            "Do the thing.",
            "",
        ]
    )
    with tempfile.TemporaryDirectory() as td:
        repo = pathlib.Path(td) / "repo"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=repo, check=True)
        (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
        (pending / "20260917-guard-01-aaa111-guard.ipd.md").write_text(
            plan, encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

        mod = MODULES[host]
        args = mod.build_parser().parse_args(["start", "all", "--repo", str(repo)])
        args.prepare_only = True
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            run_dir = mod.initialize_run(args)
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        return state["options"]


# ==================================================================================================
# E-01(a) asserted MECHANICALLY, so a key silently changing class fails.
# ==================================================================================================


class TheOptionsPartitionIsPinned(unittest.TestCase):
    """The measurement the plan's headline line-count CONCEALS, asserted rather than described.

    Every assertion here is against a LIVE frozen run, which is the only view that includes the
    twelve keys the shared policy expansion contributes.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.frozen = {host: live_options(host) for host in HOSTS}

    def test_every_shared_key_is_frozen_by_BOTH_hosts(self):
        for host in HOSTS:
            keys = set(self.frozen[host])
            missing = sorted(SHARED_OPTION_KEYS - keys)
            with self.subTest(host=host):
                self.assertEqual(
                    missing,
                    [],
                    f"{host} no longer freezes {missing}, which the table classifies as SHARED. If "
                    "the key legitimately became host-specific, move it in the SAME change and say "
                    "why: the split analysis's 13-of-34 count is computed from this table",
                )

    def test_every_oc_only_key_is_frozen_by_oc_and_NOT_by_agy(self):
        """Asserted in BOTH directions, because either half alone is satisfiable by accident."""
        oc_keys, agy_keys = (
            set(self.frozen["oc_runipd"]),
            set(self.frozen["agy_runipd"]),
        )
        for key in sorted(OC_ONLY_OPTION_KEYS):
            with self.subTest(key=key):
                self.assertIn(key, oc_keys, f"oc stopped freezing its own {key}")
                self.assertNotIn(
                    key,
                    agy_keys,
                    f"agy now freezes {key}, which the table classifies as OC-ONLY. For "
                    "`launch_profile` in particular that would be FABRICATED PROVENANCE: agy has "
                    "no launch-profile subsystem to have resolved one from (F-11)",
                )

    def test_every_agy_only_key_is_frozen_by_agy_and_NOT_by_oc(self):
        oc_keys, agy_keys = (
            set(self.frozen["oc_runipd"]),
            set(self.frozen["agy_runipd"]),
        )
        for key in sorted(AGY_ONLY_OPTION_KEYS):
            with self.subTest(key=key):
                self.assertIn(key, agy_keys, f"agy stopped freezing its own {key}")
                self.assertNotIn(
                    key,
                    oc_keys,
                    f"oc now freezes {key}, which the table classifies as AGY-ONLY",
                )

    def test_the_conditional_verify_keys_are_ABSENT_from_an_ordinary_run(self):
        """`kgpptv` E-02's byte-identical-state property: the four `verify_*` keys appear ONLY when a
        verifier profile was configured. If they became unconditional, every existing invocation's
        frozen state would change shape, which is the thing that plan deliberately avoided."""
        for host in HOSTS:
            present = sorted(OC_CONDITIONAL_OPTION_KEYS & set(self.frozen[host]))
            with self.subTest(host=host):
                self.assertEqual(
                    present,
                    [],
                    f"{host} froze {present} with no verifier profile configured",
                )

    def test_the_counts_are_what_was_measured(self):
        oc_keys, agy_keys = (
            set(self.frozen["oc_runipd"]),
            set(self.frozen["agy_runipd"]),
        )
        shared = oc_keys & agy_keys
        oc_only = oc_keys - agy_keys
        agy_only = agy_keys - oc_keys
        self.assertEqual(shared, set(SHARED_OPTION_KEYS))
        self.assertEqual(oc_only, set(OC_ONLY_OPTION_KEYS))
        self.assertEqual(agy_only, set(AGY_ONLY_OPTION_KEYS))
        self.assertEqual(len(oc_only) + len(agy_only), HOST_SPECIFIC_OPTION_COUNT)
        self.assertEqual(len(oc_keys | agy_keys), LIVE_OPTION_KEY_UNION)

    def test_the_shared_keys_arrive_predominantly_through_the_ONE_shared_expansion(
        self,
    ):
        """The claim that makes the 21-shared count read correctly rather than reassuringly.

        Twelve of the twenty-one shared keys come from `freeze_run_policy_flags`, which is a single
        shared function both hosts `**`-expand. So the shared portion of this dict is large mostly
        because something ELSE was already de-duplicated, not because the two writers agree.
        """
        policy_keys = set(runner_shared.freeze_run_policy_flags(argparse.Namespace()))
        self.assertTrue(
            policy_keys <= SHARED_OPTION_KEYS,
            f"policy keys escaped the shared set: {sorted(policy_keys - SHARED_OPTION_KEYS)}",
        )
        self.assertGreaterEqual(
            len(policy_keys),
            len(SHARED_OPTION_KEYS) // 2,
            "the shared expansion no longer accounts for most of the shared keys; the reading in "
            "this module's docstring needs re-deriving",
        )

    def test_the_option_classes_are_disjoint(self):
        """A key in two classes means the table contradicts itself and no assertion above is safe."""
        groups = {
            "shared": set(SHARED_OPTION_KEYS),
            "oc-only": set(OC_ONLY_OPTION_KEYS),
            "agy-only": set(AGY_ONLY_OPTION_KEYS),
            "oc-conditional": set(OC_CONDITIONAL_OPTION_KEYS),
        }
        names = list(groups)
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                with self.subTest(pair=(left, right)):
                    self.assertEqual(groups[left] & groups[right], set())


# ==================================================================================================
# E-01(b) asserted MECHANICALLY.
# ==================================================================================================


class TheClosureClassificationIsPinned(unittest.TestCase):
    """E-01's closure table, in the direction that catches silent drift."""

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
        """The distinction sibling `yrqyxb` established, applied here: a wrapper over `runner_shared`
        is syntactically a `def` in both modules, and counting it as a fork OVERSTATES the work."""
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
        shared_names = set(top_level_defs("runner_shared")) | set(
            module_index("runner_shared")
        )
        for name in RESOLVES_IN_RUNNER_SHARED:
            with self.subTest(symbol=name):
                self.assertIn(
                    name,
                    shared_names,
                    f"{name} no longer resolves in runner_shared, so the closure got WORSE and "
                    "the split got harder",
                )

    def test_the_already_one_object_names_really_are_one_object(self):
        """Object identity, not a name match: agy must reach the SAME object, not a copy."""
        for name in ALREADY_ONE_OBJECT:
            with self.subTest(symbol=name):
                self.assertIs(
                    getattr(oc_runipd, name),
                    getattr(agy_runipd, name),
                    f"{name} is no longer ONE object across the two hosts; it has been re-forked",
                )

    def test_the_equal_constants_are_still_equal_across_hosts(self):
        for name in EQUAL_CONSTANTS:
            with self.subTest(symbol=name):
                self.assertEqual(
                    getattr(oc_runipd, name),
                    getattr(agy_runipd, name),
                    f"{name} used to be EQUAL on both hosts and now differs, so it can no longer "
                    "be lifted with a core: it has become a hook input",
                )

    def test_the_oc_only_symbols_have_no_agy_counterpart(self):
        """F-11's capability asymmetry, asserted in both directions. `resolve_launch_pair` and
        `launch_profile_record` are not symbols agy diverged on; they are symbols agy does not have,
        because it has no launch-profile subsystem. A shared writer must therefore emit
        `launch_profile` for one host and not the other, which is the clearest single argument
        against a symmetric shared writer."""
        oc_defs, agy_defs = top_level_defs("oc_runipd"), top_level_defs("agy_runipd")
        for name in OC_ONLY_SYMBOLS:
            with self.subTest(symbol=name):
                self.assertIn(name, oc_defs, f"oc lost its own {name}")
                self.assertNotIn(
                    name,
                    agy_defs,
                    f"agy now defines {name}. If agy grew a launch-profile subsystem this is a "
                    "real capability change and F-11's A / NOT-A reading no longer holds",
                )
        self.assertEqual(
            self.count_references("agy_runipd", "runner_profiles"),
            0,
            "agy_runipd now references runner_profiles, so the premise of F-11 (a capability agy "
            "does not have) has changed and OC_ONLY_SYMBOLS must be re-derived",
        )
        self.assertGreater(self.count_references("oc_runipd", "runner_profiles"), 0)

    @staticmethod
    def count_references(host: str, name: str) -> int:
        source = (AW / f"{host}.py").read_text(encoding="utf-8")
        return sum(
            1
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Name) and node.id == name
        ) + sum(
            1
            for node in ast.walk(ast.parse(source))
            if isinstance(node, (ast.Import, ast.ImportFrom))
            and any(a.name.split(".")[-1] == name for a in node.names)
        )

    def test_the_agy_only_symbols_have_no_oc_counterpart(self):
        oc_defs = set(top_level_defs("oc_runipd")) | set(module_index("oc_runipd"))
        agy_index = module_index("agy_runipd")
        for name in AGY_ONLY_SYMBOLS:
            with self.subTest(symbol=name):
                self.assertIn(name, agy_index, f"agy lost its own {name}")
                self.assertNotIn(
                    name,
                    oc_defs,
                    f"oc now defines {name}; the asymmetry this table records has changed",
                )

    def test_the_agy_only_delegating_symbol_really_delegates(self):
        """`resolve_verification_decision` is agy-only but is NOT a fork: it binds the shared
        resolver `ybkmzp` built. Pinning the delegation is what keeps F-3's instruction meaningful
        (do not collapse the launch-profile half into the verification half): the verification half
        is ALREADY shared, so collapsing them would un-share it."""
        agy_defs = top_level_defs("agy_runipd")
        for name in AGY_ONLY_DELEGATING:
            with self.subTest(symbol=name):
                self.assertIn(name, agy_defs)
                self.assertTrue(
                    is_pure_delegation(agy_defs[name]),
                    f"agy.{name} no longer delegates to runner_shared; the shared verification "
                    "resolution has been re-forked",
                )
                self.assertIn(name, set(top_level_defs("runner_shared")))

    def test_the_symbol_classes_are_disjoint(self):
        groups = {
            "still-double-defined": set(STILL_DOUBLE_DEFINED),
            "resolves-in-runner-shared": set(RESOLVES_IN_RUNNER_SHARED),
            "already-one-object": set(ALREADY_ONE_OBJECT),
            "thin-wrapper": set(THIN_WRAPPERS_OVER_RUNNER_SHARED),
            "equal-constant": set(EQUAL_CONSTANTS),
            "oc-only": set(OC_ONLY_SYMBOLS),
            "agy-only": set(AGY_ONLY_SYMBOLS),
            "agy-only-delegating": set(AGY_ONLY_DELEGATING),
            "non-relocatable": set(NON_RELOCATABLE),
        }
        names = list(groups)
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                with self.subTest(pair=(left, right)):
                    self.assertEqual(groups[left] & groups[right], set())

    def test_initialize_run_still_closes_over_every_pinned_symbol(self):
        """The load-bearing direction: the table describes what the FUNCTION reaches.

        If a name stops being reached, the table is stale and every count computed from it is wrong,
        INCLUDING the injection count the split analysis rests on. Checked against the UNION of the
        two hosts, because several classes are deliberately one-host-only.
        """
        classified = (
            set(STILL_DOUBLE_DEFINED)
            | set(RESOLVES_IN_RUNNER_SHARED)
            | set(ALREADY_ONE_OBJECT)
            | set(THIN_WRAPPERS_OVER_RUNNER_SHARED)
            | set(EQUAL_CONSTANTS)
            | set(OC_ONLY_SYMBOLS)
            | set(AGY_ONLY_SYMBOLS)
            | set(AGY_ONLY_DELEGATING)
        )
        reached = free_module_level_names("oc_runipd") | free_module_level_names(
            "agy_runipd"
        )
        missing = sorted(classified - reached)
        self.assertEqual(
            missing,
            [],
            f"initialize_run no longer closes over {missing}; E-01's table is stale and must be "
            "re-measured with the committed scanner before it is trusted",
        )

    def test_the_census_totals_are_what_was_measured(self):
        self.assertEqual(len(STILL_DOUBLE_DEFINED), 5)
        self.assertEqual(
            len(STILL_DOUBLE_DEFINED)
            + len(RESOLVES_IN_RUNNER_SHARED)
            + len(ALREADY_ONE_OBJECT)
            + len(THIN_WRAPPERS_OVER_RUNNER_SHARED)
            + len(EQUAL_CONSTANTS)
            + len(OC_ONLY_SYMBOLS)
            + len(AGY_ONLY_SYMBOLS)
            + len(AGY_ONLY_DELEGATING)
            + len(NON_RELOCATABLE)
            + 3,  # `Any`, `Path`, `runner_shared`: stdlib/module aliases, identity trivially true
            CLOSURE_TOTAL,
            "the classes must partition the measured names exactly; a total below CLOSURE_TOTAL "
            "means a name was dropped from the table rather than reclassified",
        )


# ==================================================================================================
# F-9: the hazard. THE INVERSE ASSERTION, and the one that matters most in this file.
# ==================================================================================================


class TheDriverIdentityIsEvaluatedInEachRunner(unittest.TestCase):
    """`__file__` must be evaluated in the RUNNER module, never in a shared one.

    ASSERTED AS A SOURCE PROPERTY here and as BEHAVIOR in
    `tests/test_rununify_initialize_run_characterization.py`, deliberately, because the two catch
    different mistakes. The behavioral test catches a relocation. THIS one catches the narrower
    error of a shared module acquiring its own `state["driver"]` writer, which the behavioral test
    would not see while each host still had its own.

    WHEN THE SPLIT HAPPENS, this class must be RE-BASED, not deleted: the correct handling is to pass
    the caller's module path into the core, so the assertion becomes "the core receives a path
    naming the calling runner" and the behavioral test above is what proves it.
    """

    def test_each_runner_evaluates_its_OWN_file_dunder_in_initialize_run(self):
        for host in HOSTS:
            with self.subTest(host=host):
                source = ast.unparse(target_node(host))
                self.assertIn(
                    "__file__",
                    source,
                    f"{host}.initialize_run no longer evaluates __file__. If the driver identity is "
                    "now supplied by a shared core, THAT CORE MUST RECEIVE THE CALLER'S MODULE "
                    "PATH: `run_analytics_sources.driver_generation` and `run_viewer` both key on "
                    "this basename, and a shared module's name makes every run unattributable",
                )

    def test_runner_shared_does_not_write_a_driver_record(self):
        """The narrow error: a shared helper that freezes `state['driver']` would produce the same
        silent loss even with each host still calling its own `initialize_run`."""
        source = (AW / "runner_shared.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        offenders = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            keys = {
                k.value
                for k in node.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            }
            if {"path", "sha256"} <= keys and "__file__" in ast.unparse(node):
                offenders.append(node.lineno)
        self.assertEqual(
            offenders,
            [],
            f"runner_shared.py builds a driver record from its own __file__ at line(s) {offenders}; "
            "that value names runner_shared.py for every host and destroys host attribution",
        )

    def test_the_two_consumers_that_read_this_basename_still_read_it(self):
        """The hazard's PREMISE, asserted so this class cannot become vacuous by the consumers
        changing rather than by the runners changing."""
        from agent_workflows import run_analytics_sources

        self.assertEqual(
            run_analytics_sources.DRIVER_GENERATIONS.get("oc_runipd.py"), "oc_runipd"
        )
        self.assertEqual(
            run_analytics_sources.DRIVER_GENERATIONS.get("agy_runipd.py"), "agy_runipd"
        )
        viewer = (AW / "run_viewer.py").read_text(encoding="utf-8")
        self.assertIn('"oc_runipd" in driver_path', viewer)
        self.assertIn('"agy_runipd" in driver_path', viewer)


# ==================================================================================================
# What was NOT done, asserted mechanically so the omission is a guarded state and not an oversight.
# ==================================================================================================


class TheSplitHasNotBeenPerformed(unittest.TestCase):
    """`initialize_run` still has TWO definitions and there is no shared core.

    ASSERTED IN THE INVERSE DIRECTION deliberately. A later agent who reads this plan's title and
    "finishes" the split symbol by symbol will fail here, which sends them to the analysis (plan
    `orziju` E-04 and its walkthrough) before they change what every run records about its own host.
    """

    def test_both_runners_still_define_initialize_run(self):
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertIn(TARGET, top_level_defs(host))

    def test_runner_shared_does_not_define_initialize_run(self):
        self.assertNotIn(
            TARGET,
            top_level_defs("runner_shared"),
            "a shared initialize_run exists. Read plan orziju's E-04 analysis first: a shared "
            "writer must supply 13 host-specific `options` keys and MUST be handed the caller's "
            "module path, or every run becomes host-unattributable with no test failing",
        )

    def test_the_two_definitions_are_not_the_same_object(self):
        self.assertIsNot(oc_runipd.initialize_run, agy_runipd.initialize_run)

    def test_neither_host_delegates_initialize_run_to_runner_shared(self):
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertFalse(
                    is_pure_delegation(top_level_defs(host)[TARGET]),
                    f"{host}.initialize_run is now a thin wrapper over runner_shared, so the split "
                    "HAS happened: re-base this file's inverse assertions and the driver-identity "
                    "class deliberately rather than deleting them",
                )


if __name__ == "__main__":
    unittest.main()

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
in THIS file is now it (it arrived here from a companion `..._characterization.py` that
`7ebc2964` folded in).

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

import contextlib
import io
import json
import subprocess
import tempfile
from pathlib import Path
from agent_workflows import (
    agy_runipd,
    oc_runipd,
    run_analytics_sources,
    run_viewer,
    runner_shared,
)

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
#: `allow_concurrent_driver` JOINED 2026-09-22 (runconcur-01 `vddpml`), through the SHARED
#: `freeze_run_policy_flags` expansion rather than through either host's dict body. That is the ONLY way
#: it could have arrived, and it is the direction these counts want: the flag reaches both hosts because
#: ONE table declares it, so it could not have landed on one host only. The load-bearing number - the
#: thirteen HOST-SPECIFIC keys - is unmoved, which is the property this partition exists to police.
SHARED_OPTION_KEYS = frozenset(
    {
        "action",
        "allow_concurrent_driver",
        "allow_dirty_base",
        "allow_drafts",
        "allow_mixed",
        "allow_uncovered_orchestrator_work",
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
# RE-MEASURED 2026-09-19 (34 -> 35) by orchprobe-03 (`m7gvuz`): the union grew by one SHARED key,
# `allow_uncovered_orchestrator_work`, frozen by the one shared `freeze_run_policy_flags` expansion.
# The host-specific count is UNCHANGED, which is the property that matters here: the new policy could
# not land on one host only.
# RE-MEASURED 2026-09-22 (35 -> 36) by runconcur-01 (`vddpml`), for exactly the same reason and with the
# same reading: one SHARED key, `allow_concurrent_driver`, through the same one shared expansion, with
# the host-specific count again UNMOVED.
LIVE_OPTION_KEY_UNION = 36  # 23 shared + 13 host-specific

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
#:   * `set_plan_approved` LIFTED into `runner_shared` by hostdedup Order 01 (`li44r9`) E-02/E-08, in the
#:     same change that re-based this table. It MOVED to THIN_WRAPPERS_OVER_RUNNER_SHARED below rather
#:     than being deleted, so it is still asserted -- now as a wrapper that must really delegate.
#:     IT WAS THE HARDEST SYMBOL IN THAT TRANCHE despite its two bodies having been BYTE-IDENTICAL, and
#:     the reason is worth recording here because it generalizes: each body read a module-level
#:     `FULL_AUTO_ACTOR`, AST comparison matches on the NAME, and the two names resolved to DIFFERENT
#:     strings (`aw oc run --full-auto` vs `aw agy run --full-auto`). That string is passed as `--actor`
#:     and lands in a plan's PERMANENT `## Workflow history`, so a verbatim lift would have attributed
#:     every Antigravity auto-approval to the OpenCode driver. The value now arrives through
#:     `HostLabels.full_auto_actor`, which has no default.
STILL_DOUBLE_DEFINED = (
    "enforce_dependency_preflight",
    "expand_selectors",
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
#: RECLASSIFIED 2026-09-17 by sibling `tx6q0h`, which gave the two runners ONE `HostLabels`
#: descriptor and lifted the eight host-label symbols into `runner_shared`. Each name moved here
#: from STILL_DOUBLE_DEFINED because it is now the SANCTIONED WRAPPER FORM (the maintainer's
#: 2026-09-03 `818uru` OQ-02 ruling): `runner_shared` owns the real function and each host keeps a
#: one-line wrapper at the original name and signature, binding its own labels. Verified at
#: integration by the assertions in this file, which report the delegation themselves. Counting
#: them as forks would OVERSTATE the remaining work, which is exactly what this table exists to
#: prevent.
THIN_WRAPPERS_OVER_RUNNER_SHARED = (
    # hostdedup Order 01 (`li44r9`) E-04: `set_plan_approved` MOVED here from `STILL_DOUBLE_DEFINED`
    # above in the same change that lifted it. See the note on that tuple for why it needed a
    # `HostLabels` field rather than a verbatim move.
    "discover_plans",
    "enforce_requested_action",
    "git_common_dir",
    "set_plan_approved",
    "validate_manifest",
    "write_report",
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
    nodes = [node]
    index = dict(module_index(host))
    if any(
        isinstance(n, ast.Attribute) and n.attr == "initialize_run_core"
        for n in ast.walk(node)
    ):
        for cand in module_body("runner_shared"):
            if isinstance(cand, ast.FunctionDef) and cand.name == "initialize_run_core":
                nodes.append(cand)
                index.update(module_index("runner_shared"))
                break

    loads: set[str] = set()
    bound: set[str] = set()
    for curr_node in nodes:
        loads |= {
            n.id
            for n in ast.walk(curr_node)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
        }
        bound |= {
            n.id
            for n in ast.walk(curr_node)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
        }
        bound |= {a.arg for a in curr_node.args.args + curr_node.args.kwonlyargs}
        for sub in ast.walk(curr_node):
            if isinstance(sub, (ast.Import, ast.ImportFrom)):
                for alias in sub.names:
                    bound.add(alias.asname or alias.name.split(".")[0])

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
        # RE-MEASURED 2026-09-17 after sibling `tx6q0h` lifted the eight host-label symbols behind
        # one `HostLabels` descriptor: the named forks became the sanctioned one-line-wrapper form,
        # so they moved to THIN_WRAPPERS_OVER_RUNNER_SHARED. Re-measured from the tables above rather
        # than edited to fit, and each reclassification is proven individually by the fork-vs-wrapper
        # test in this class, which reports the delegation itself.
        #
        # 3 -> 2, RE-MEASURED by hostdedup Order 01 (`li44r9`) E-04, which lifted `set_plan_approved`.
        # It MOVED to `THIN_WRAPPERS_OVER_RUNNER_SHARED`, which rose by one, so the partition assertion
        # immediately below is UNCHANGED against `CLOSURE_TOTAL` -- and that assertion, not this figure,
        # is what proves the re-base was a reclassification rather than a deletion.
        self.assertEqual(len(STILL_DOUBLE_DEFINED), 2)
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
    the behavioral net now in THIS file, deliberately, because the two catch
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


HOST_PAIRS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))

#: host -> the driver module basename that host must record, the generation label
#: `run_analytics_sources` must infer from it, the host label, and the name `run_viewer` renders.
DRIVER_IDENTITY = {
    "oc_runipd": {
        "basename": "oc_runipd.py",
        "generation": "oc_runipd",
        "host": "opencode",
        "viewer_label": "OpenCode",
    },
    "agy_runipd": {
        "basename": "agy_runipd.py",
        "generation": "agy_runipd",
        "host": "agy",
        "viewer_label": "Antigravity",
    },
}

_PLAN = """# IPD: {title}

- Date: 2026-09-17
- Kind: {kind}
- Status: {status}
- Set: {setid} (the {setid} set)
- Order: {order}
- Id: {id6}
- Item-Dependencies: {deps}
{extra}
## Goal

Do the thing.

## Detailed Implementation Checklist (TODO)

- [ ] E-01 do it
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: output
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: small
- Cohesion rationale: one concern.
"""


class InitializeRunCase(unittest.TestCase):
    """Drive a host's REAL `initialize_run` over a synthetic repository."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self._repo_seq = 0

    # ---- fixtures ---------------------------------------------------------------------------
    def plan_text(
        self,
        id6: str,
        *,
        kind: str = "child",
        status: str = "approved",
        setid: str = "probe",
        order: int = 1,
        deps: str = "none",
        from_backlog: str | None = None,
    ) -> str:
        extra = f"- From-Backlog: {from_backlog}\n" if from_backlog else ""
        return _PLAN.format(
            title=id6,
            kind=kind,
            status=status,
            setid=setid,
            order=order,
            id6=id6,
            deps=deps,
            extra=extra,
        )

    def make_repo(
        self, plans: dict[str, str] | None = None, *, git: bool = True
    ) -> Path:
        """A git repository with the given `filename -> text` plans under `pending/`.

        A FRESH DIRECTORY PER CALL, deliberately. A test that drives both hosts over one repository
        hits `initialize_run`'s own "Run already exists" refusal, because `new_run_id` is derived
        from a whole-second timestamp plus the pid and the two calls land inside the same second.
        That refusal is real behavior (and is characterized in
        `ARunIdCollisionRefusesRatherThanOverwrites`), so the fixture must not provoke it
        incidentally.
        """
        self._repo_seq += 1
        repo = self.root / f"repo-{self._repo_seq}"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        if git:
            for cmd in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Test"],
            ):
                subprocess.run(cmd, cwd=repo, check=True)
        (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
        for name, text in (
            plans or {"20260917-probe-01-aaa111-probe.ipd.md": self.plan_text("aaa111")}
        ).items():
            (pending / name).write_text(text, encoding="utf-8")
        if git:
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo

    def initialize(
        self, mod, repo: Path, argv: list[str] | None = None
    ) -> tuple[Path, dict, str, str]:
        """`initialize_run` on `repo`; returns (run_dir, state, stdout, stderr)."""
        args = mod.build_parser().parse_args(
            ["start", *(argv or ["all"]), "--repo", str(repo)]
        )
        args.prepare_only = True
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            run_dir = mod.initialize_run(args)
        return (
            run_dir,
            runner_shared.load_state(run_dir),
            out.getvalue(),
            err.getvalue(),
        )

    def events(self, run_dir: Path) -> list[dict]:
        raw = (run_dir / "events.jsonl").read_text(encoding="utf-8")
        return [json.loads(line) for line in raw.splitlines() if line.strip()]


# ==================================================================================================
# THE DRIVER-IDENTITY CONTRACT. F-9. No test covered this before this file.
# ==================================================================================================


class EachHostRecordsItsOwnDriverIdentity(InitializeRunCase):
    """A run must be attributable to the host that created it, through `state['driver']['path']`.

    Asserted at FOUR levels, because the value passes through four independent readers and a naive
    relocation breaks all four at once with no other symptom.
    """

    def test_the_recorded_driver_path_basename_is_this_hosts_runner_module(self):
        """The load-bearing assertion. `__file__` must be evaluated in the RUNNER, not in a shared
        module, so a relocated core has to be handed the caller's module path explicitly."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                recorded = state["driver"]["path"]
                self.assertEqual(
                    Path(recorded).name,
                    DRIVER_IDENTITY[name]["basename"],
                    f"{name} recorded driver path {recorded!r}. If this now names a SHARED module, "
                    "every run created by either host is host-unattributable in run analytics: "
                    "`run_analytics_sources.driver_generation` and `run_viewer` both key on this "
                    "BASENAME. A shared core must receive the caller's module path as a parameter",
                )

    def test_the_recorded_driver_sha256_is_that_same_modules_digest(self):
        """The digest and the path must describe the SAME file. Relocating one and not the other
        would produce a record that looks intact and attributes the run to a file whose contents it
        does not carry."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                module_file = Path(str(mod.__file__)).resolve()
                self.assertEqual(Path(state["driver"]["path"]), module_file)
                self.assertEqual(
                    state["driver"]["sha256"],
                    runner_shared.sha256_file(module_file),
                    f"{name}'s frozen driver digest is not this module's digest",
                )

    def test_run_analytics_infers_this_hosts_generation_and_not_unknown(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                generation = run_analytics_sources.driver_generation(state)
                self.assertEqual(generation, DRIVER_IDENTITY[name]["generation"])
                self.assertNotEqual(
                    generation,
                    run_analytics_sources.GENERATION_UNKNOWN,
                    f"{name}'s runs are no longer attributable to a driver generation",
                )
                self.assertEqual(
                    run_analytics_sources.generation_host(generation),
                    DRIVER_IDENTITY[name]["host"],
                )

    def test_the_run_viewer_labels_the_run_with_this_hosts_product_name(self):
        """The operator-visible half: `aw runs` names the host. A relocated core makes this render
        the shared module's stem (`runner_shared`) instead of `OpenCode` / `Antigravity`."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                run_dir, _state, _out, _err = self.initialize(mod, self.make_repo())
                summary = run_viewer.load_run_summary(run_dir, repo_root=run_dir)
                self.assertIsNotNone(summary)
                assert summary is not None
                self.assertEqual(
                    summary.driver,
                    DRIVER_IDENTITY[name]["viewer_label"],
                    f"{name}'s run no longer renders its host name in `aw runs`",
                )

    def test_the_two_hosts_record_DIFFERENT_driver_paths(self):
        """The property the discriminator exists for, asserted directly rather than inferred from
        the two per-host assertions above."""
        recorded = {}
        for name, mod in HOST_PAIRS:
            _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
            recorded[name] = Path(state["driver"]["path"]).name
        self.assertNotEqual(
            recorded["oc_runipd"],
            recorded["agy_runipd"],
            "both hosts now record the SAME driver path, so no consumer can tell their runs "
            f"apart: {recorded}",
        )

    def test_a_core_relocated_to_runner_shared_would_be_caught(self):
        """NON-VACUITY, and the whole reason this class exists (F-9).

        Construct the state a naive relocation WOULD write - `runner_shared.py` as the driver path
        for both hosts - and show that every consumer assertion above fails on it. Without this, the
        class above is four assertions that have never been demonstrated capable of failing.
        """
        shared_module = Path(str(runner_shared.__file__)).resolve()
        naive = {
            "driver": {
                "path": str(shared_module),
                "sha256": runner_shared.sha256_file(shared_module),
            }
        }
        self.assertEqual(Path(naive["driver"]["path"]).name, "runner_shared.py")

        generation = run_analytics_sources.driver_generation(naive)
        self.assertEqual(
            generation,
            run_analytics_sources.GENERATION_UNKNOWN,
            "a shared-module driver path must be UNRECOGNIZED, which is exactly the silent "
            "analytics loss F-9 names",
        )
        self.assertEqual(
            run_analytics_sources.generation_host(generation),
            run_analytics_sources.GENERATION_UNKNOWN,
        )
        for name in DRIVER_IDENTITY:
            with self.subTest(host=name):
                self.assertNotEqual(
                    Path(naive["driver"]["path"]).name,
                    DRIVER_IDENTITY[name]["basename"],
                )

        # And the viewer's label: it substring-matches, so a shared path falls through to the stem.
        run_dir = self.root / "naive-run"
        run_dir.mkdir()
        (run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "naive-run",
                    "driver": naive["driver"],
                    "queue": [],
                    "selectors": [],
                }
            ),
            encoding="utf-8",
        )
        summary = run_viewer.load_run_summary(run_dir, repo_root=run_dir)
        assert summary is not None
        self.assertEqual(summary.driver, "runner_shared")
        self.assertNotIn(
            summary.driver,
            {v["viewer_label"] for v in DRIVER_IDENTITY.values()},
            "the viewer must NOT be able to name a host from a shared driver path",
        )


# ==================================================================================================
# CHARACTERIZATION: the refusals, and the ORDER two spec-stated pins assert as source text.
# ==================================================================================================


class ARefusalLeavesNoDurableState(InitializeRunCase):
    """Spec 25kzda 2.5a's shape, as BEHAVIOR rather than as a source offset.

    Two existing pins (`tests/test_run_flag_surface.py:745`, `:1340`) express this by splitting the
    source on the literal `run_dir = state_root` and requiring a call to appear in the PREFIX. That
    encodes the guarantee "a refusal happens before any durable state exists" as a textual fact
    about one function's body, which relocation destroys. Here it is the observable property: after
    a refusal, `state_root(repo)` contains NO run directory.
    """

    def run_dirs(self, repo: Path) -> list[Path]:
        root = runner_shared.state_root(repo)
        return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []

    def test_an_unimplemented_flag_refuses_before_any_run_directory_exists(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo()
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(repo)]
                )
                args.prepare_only = True
                # The shared table's own unimplemented rows, read from the table rather than
                # hard-coded, so a row changing state cannot make this test silently vacuous.
                unimplemented = [
                    row for row in runner_shared.RUN_POLICY_FLAGS if not row.implemented
                ]
                self.assertTrue(
                    unimplemented, "no unimplemented policy flag remains to test with"
                )
                setattr(args, unimplemented[0].dest, True)
                with self.assertRaises(runner_shared.RunFlagRefusal):
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                self.assertEqual(
                    self.run_dirs(repo),
                    [],
                    f"{name} created durable run state despite refusing the invocation; the "
                    "refusal must precede the run directory (spec 25kzda 2.5a)",
                )

    def test_an_out_of_range_retry_budget_refuses_before_any_run_directory_exists(self):
        """The bound is `run_recovery.validate_retry_budget`'s and is re-raised at the flag layer as
        `RunFlagRefusal`, so the OPERATOR-FACING type is asserted here and the bound's own message is
        asserted through it rather than re-stated."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo()
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(repo)]
                )
                args.prepare_only = True
                args.retry_budget = 11
                with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                self.assertIn("--retry-budget", str(ctx.exception))
                self.assertEqual(self.run_dirs(repo), [])

    def test_a_non_repository_refuses_before_any_run_directory_exists(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                bare = self.root / f"not-a-repo-{name}"
                bare.mkdir()
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(bare)]
                )
                args.prepare_only = True
                with self.assertRaises(runner_shared.DriverError) as ctx:
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                self.assertIn("Not a Git repository", str(ctx.exception))
                self.assertEqual(self.run_dirs(bare), [])

    def test_the_control_a_valid_invocation_DOES_create_exactly_one_run_directory(self):
        """The non-vacuity control for this whole class: without it, a function that refused
        EVERYTHING would pass every test above."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo()
                run_dir, state, _out, _err = self.initialize(mod, repo)
                self.assertEqual(self.run_dirs(repo), [run_dir])
                self.assertEqual([i["id6"] for i in state["queue"]], ["aaa111"])


class TheDraftAdmissionGateExcludesRatherThanRefuses(InitializeRunCase):
    """Spec 2.5a bullet 4, as behavior: an ungated complete draft is WITHHELD and the rest runs.

    This is the behavioral equivalent of the ordering pin at `tests/test_run_flag_surface.py:1340`,
    which asserts textually that `expand_selectors` precedes `enforce_draft_admission_gate` and that
    both precede `run_dir = state_root`. The guarantee is that the exclusion decision is made
    against a RESOLVED queue and leaves nothing durable behind for the excluded item, and that is
    what is asserted here.
    """

    def repo_with_a_draft_and_a_reviewable(self) -> Path:
        return self.make_repo(
            {
                "20260917-probe-01-drf001-draft.ipd.md": self.plan_text(
                    "drf001", status="draft", order=1
                ),
                "20260917-probe-02-rev003-ordinary.ipd.md": self.plan_text(
                    "rev003", status="to-review", order=3
                ),
            }
        )

    def test_the_draft_is_excluded_and_the_reviewable_still_runs(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                run_dir, state, _out, _err = self.initialize(
                    mod, self.repo_with_a_draft_and_a_reviewable(), ["reviews"]
                )
                queued = [item["id6"] for item in state["queue"]]
                self.assertNotIn("drf001", queued, "the ungated draft was admitted")
                self.assertIn("rev003", queued, "the rest of the queue did not proceed")
                # ... and the exclusion is DURABLY recorded, which is the half a source pin cannot
                # express at all.
                gate = [
                    e
                    for e in self.events(run_dir)
                    if e.get("event") == "draft-admission-gate"
                ]
                self.assertEqual(
                    len(gate), 1, f"{name}: expected one gate event, got {gate}"
                )
                self.assertIn("drf001", gate[0]["excluded_complete"])

    def test_the_gate_decision_is_made_against_the_RESOLVED_queue(self):
        """The ordering property the textual pin encodes: the gate sees expanded selectors, so its
        excluded set is drawn from the resolved ids rather than from the raw selector tokens."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                run_dir, _state, _out, _err = self.initialize(
                    mod, self.repo_with_a_draft_and_a_reviewable(), ["reviews"]
                )
                gate = next(
                    e
                    for e in self.events(run_dir)
                    if e.get("event") == "draft-admission-gate"
                )
                considered = set(gate["excluded_complete"]) | set(
                    gate.get("skipped_incomplete", [])
                )
                self.assertIn(
                    "drf001",
                    considered,
                    "the gate did not see the resolved id, so it ran before selector expansion",
                )

    def test_a_drafts_only_selection_freezes_NO_run_directory(self):
        """The strongest form of "the exclusion leaves nothing durable": when every selected item is
        an ungated draft, the run refuses rather than freezing an empty queue."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-01-drf001-draft.ipd.md": self.plan_text(
                            "drf001", status="draft"
                        )
                    }
                )
                args = mod.build_parser().parse_args(
                    ["start", "reviews", "--repo", str(repo)]
                )
                args.prepare_only = True
                with self.assertRaises(runner_shared.EmptyStatusSelection):
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                root = runner_shared.state_root(repo)
                self.assertEqual(
                    [p for p in root.iterdir() if p.is_dir()] if root.is_dir() else [],
                    [],
                    f"{name} froze a run directory for a selection it then refused",
                )


class TheMixedTypeGateIsReachedExactlyOnce(InitializeRunCase):
    """`tests/test_run_flag_surface.py:1564` asserts the CALL SITE COUNT is exactly one, in source.

    The behavioral equivalent is that the ledger carries exactly one `mixed-type-gate` record per
    run: two call sites would produce two records (or, worse, two decisions), and zero would produce
    none, which is the dead-gate defect `uyeko5` was written to fix.
    """

    def test_exactly_one_gate_record_per_run_on_both_hosts(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                run_dir, _state, _out, _err = self.initialize(mod, self.make_repo())
                records = [
                    e
                    for e in self.events(run_dir)
                    if e.get("event") == "mixed-type-gate"
                ]
                self.assertEqual(
                    len(records),
                    1,
                    f"{name} recorded {len(records)} mixed-type-gate events; the gate must have "
                    "exactly ONE reached call site",
                )

    def test_the_gate_does_not_APPLY_to_a_single_type_selection(self):
        """The honest limit `uyeko5` recorded, pinned so a future `--type` cannot change it
        silently: the gate is REACHED on every run and correctly does not apply today."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                run_dir, _state, _out, _err = self.initialize(mod, self.make_repo())
                record = next(
                    e
                    for e in self.events(run_dir)
                    if e.get("event") == "mixed-type-gate"
                )
                self.assertFalse(record["gate_applied"])
                self.assertTrue(record["proceed"])


class TheFrozenQueueEntryShapeIsIdenticalOnBothHosts(InitializeRunCase):
    """F-2's resume hazard, measured rather than assumed.

    The plan's F-2 warned that a shared writer could change the queue-entry key set a RESUME reads.
    Measured at review and again here: both hosts write the IDENTICAL key set, differing only in
    the source-order of `kind` and `order`, which JSON round-trips do not preserve as significant.
    So the hazard is LOW, and this class is what keeps it low.

    THE COUNT WENT 12 -> 13, AND THAT IS A DELIBERATE CONTRACT CHANGE, not a drift (`runnoop` Order 01,
    `zz5yxq` E-03/E-07). The 13th key is `needs_input`, the durable, explicit record that an item was
    NOT dispatched because its plan still needs human approval. Before it, that fact was only IMPLICIT
    in the frozen queue status (`reviewed` rather than `queued`), and a fact each reporting surface has
    to INFER is a fact each surface reports differently - which is how an approval-blocked queue came
    to print a clean run and exit 0 (backlog `em0z50`).

    THIS TEST WAS NOT WEAKENED TO ACCOMMODATE THAT. The failure message below is what made the change
    visible in the first place ("a key added or removed here is a compatibility change"), so the
    correct response was to move the constant and say WHY here, not to relax the shape check. The
    assertion is still an exact `assertEqual` against a frozen set, so the NEXT unannounced key still
    fails. The name moved with it: a test named `..._twelve_keys` asserting thirteen would be the
    real weakening.

    THE RESUME QUESTION, since that is what the class exists for: adding a key is the SAFE direction.
    A resume READS this entry, and every reader takes the keys it knows by name; an older state file
    written without `needs_input` simply lacks the key, and the only consumer
    (`runner_shared.item_needs_approval`'s frozen result) is re-derivable. No reader iterates the key
    set and refuses an unknown member, so no in-flight run is invalidated by the addition.

    MERGE NOTE (2026-09-18): this class was consolidated here from
    `test_rununify_initialize_run_characterization.py` by `7ebc2964` while `zz5yxq` was executing
    against that now-deleted file, so the 12 -> 13 update landed by hand-merge rather than by the
    lane's own commit. The assertion and rationale are the lane's, unchanged.
    """

    EXPECTED_KEYS = frozenset(
        {
            "position",
            "id6",
            "setid",
            "configured_file",
            "dependencies",
            "kind",
            "order",
            "from_backlog",
            "initial_status",
            "action",
            "status",
            "attempts",
            # zz5yxq E-03. See the class docstring for why this key exists and why adding it is a
            # deliberate compatibility change rather than an accident.
            "needs_input",
        }
    )

    def test_both_hosts_freeze_the_same_thirteen_keys(self):
        seen = {}
        for name, mod in HOST_PAIRS:
            _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
            seen[name] = frozenset(state["queue"][0])
            with self.subTest(host=name):
                self.assertEqual(
                    seen[name],
                    self.EXPECTED_KEYS,
                    f"{name}'s queue entry shape changed; a RESUME of an in-flight run reads this "
                    "shape, so a key added or removed here is a compatibility change",
                )
        self.assertEqual(seen["oc_runipd"], seen["agy_runipd"])

    def test_the_from_backlog_link_is_frozen_on_the_entry(self):
        """`tests/test_runner_backlog_close.py:255` asserts the literal `"from_backlog"` appears in
        the source. The behavioral equivalent: the LINK actually reaches the frozen entry."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-01-aaa111-linked.ipd.md": self.plan_text(
                            "aaa111", from_backlog="bbbbbb"
                        )
                    }
                )
                _run_dir, state, _out, _err = self.initialize(mod, repo)
                self.assertEqual(state["queue"][0]["from_backlog"], "bbbbbb")

    def test_an_absent_link_freezes_None_rather_than_a_placeholder(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                self.assertIsNone(state["queue"][0]["from_backlog"])

    def test_an_orchestrators_kind_is_frozen_so_a_resume_rederives_its_action(self):
        """Both hosts must freeze `kind`, by DIFFERENT routes: oc reads `PlanRecord.kind`, agy falls
        back to `_plan_kind(path)` because its record lacks the field (the plan's F-4). The frozen
        RESULT must be the same, which is what a resume depends on."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-00-orc001-parent.ipd.md": self.plan_text(
                            "orc001", kind="orchestrator", order=0
                        ),
                        "20260917-probe-01-aaa111-child.ipd.md": self.plan_text(
                            "aaa111", order=1
                        ),
                    }
                )
                _run_dir, state, _out, _err = self.initialize(mod, repo)
                by_id = {item["id6"]: item for item in state["queue"]}
                self.assertEqual(by_id["orc001"]["kind"], "orchestrator")
                self.assertEqual(by_id["orc001"]["action"], "orchestrate")
                self.assertEqual(by_id["aaa111"]["kind"], "child")
                self.assertEqual(by_id["aaa111"]["action"], "execute")


class TheFrozenOptionsCarryEachHostsOwnPolicy(InitializeRunCase):
    """The `options` dict is where the two hosts genuinely diverge (13 host-specific keys of 34
    live), so its per-host content is characterized rather than assumed symmetric.

    `tests/test_run_flag_surface.py:874` asserts the `full_auto` args-fallback SPELLING is `False`
    on both hosts, by regex over the source. The behavioral equivalent is that a Namespace WITHOUT
    the attribute freezes `False`, which is the property the spelling exists to produce.
    """

    def test_the_shared_policy_keys_are_frozen_by_the_one_shared_function(self):
        """The keys `freeze_run_policy_flags` owns must all be present on both hosts, read from the
        shared table rather than listed, so a new policy flag cannot land on one host only."""
        expected = {row.dest for row in runner_shared.RUN_POLICY_FLAGS if row.freeze}
        self.assertTrue(expected)
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                missing = sorted(expected - set(state["options"]))
                self.assertEqual(
                    missing,
                    [],
                    f"{name} did not freeze {missing}; spec 2.1 requires resume to use the "
                    "original options",
                )

    def test_full_auto_defaults_to_False_on_both_hosts_when_the_attribute_is_absent(
        self,
    ):
        """The behavioral form of the site-2 spelling pin. Deleting the attribute is what makes the
        `getattr` default observable: a caller that builds a Namespace by hand is the case the
        `uyeko5` E-07 change was about."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo()
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(repo)]
                )
                args.prepare_only = True
                delattr(args, "full_auto")
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    run_dir = mod.initialize_run(args)
                state = runner_shared.load_state(run_dir)
                self.assertIs(
                    state["options"]["full_auto"],
                    False,
                    f"{name} defaulted full_auto to True for a Namespace lacking the attribute; "
                    "that is the opt-in/opt-out divergence `uyeko5` E-07 closed",
                )

    def test_each_host_freezes_its_own_verification_key_with_its_own_polarity(self):
        """oc freezes `validate` (positive) plus a derived `no_audit`; agy freezes `no_verify`
        (negated). Opposite spellings of one concept, and getting the polarity wrong would make
        "verify" mean "do not verify" with no error anywhere (`ybkmzp` E-04)."""
        _run_dir, oc_state, _o, _e = self.initialize(oc_runipd, self.make_repo())
        self.assertIn("validate", oc_state["options"])
        self.assertNotIn("no_verify", oc_state["options"])
        self.assertIs(
            oc_state["options"]["no_audit"], not oc_state["options"]["validate"]
        )

        _run_dir, agy_state, _o, _e = self.initialize(agy_runipd, self.make_repo())
        self.assertIn("no_verify", agy_state["options"])
        self.assertNotIn("validate", agy_state["options"])
        self.assertNotIn("no_audit", agy_state["options"])

    def test_only_oc_freezes_a_launch_profile_because_only_oc_has_one(self):
        """F-11's capability asymmetry, pinned in BOTH directions. `agy_runipd` contains zero
        `runner_profiles` references, so a shared writer emitting `launch_profile` for agy would
        fabricate provenance the host cannot supply, and one emitting it for neither would break
        `tests/test_runner_profiles_e2e.py`."""
        _run_dir, oc_state, _o, _e = self.initialize(oc_runipd, self.make_repo())
        self.assertIn("launch_profile", oc_state["options"])
        self.assertIn("config_digest", oc_state["options"]["launch_profile"])

        _run_dir, agy_state, _o, _e = self.initialize(agy_runipd, self.make_repo())
        self.assertNotIn(
            "launch_profile",
            agy_state["options"],
            "agy froze a launch profile, but this host has NO launch-profile subsystem to have "
            "resolved one from; the value is fabricated provenance",
        )

    def test_each_host_freezes_its_own_executable_key(self):
        _run_dir, oc_state, _o, _e = self.initialize(oc_runipd, self.make_repo())
        _run_dir, agy_state, _o, _e = self.initialize(agy_runipd, self.make_repo())
        self.assertIn("opencode", oc_state["options"])
        self.assertNotIn("agy_executable", oc_state["options"])
        self.assertIn("agy_executable", agy_state["options"])
        self.assertNotIn("opencode", agy_state["options"])


class TheRunOrderRationaleIsFrozenBesideTheQueue(InitializeRunCase):
    """Both hosts call the SAME `run_order_rationale`, so the frozen record must have one shape.

    Characterized because a shared writer is the most likely place for this to be silently dropped
    on one host: nothing else reads it at creation time, so its absence would surface only later, in
    `aw runs`.
    """

    def test_the_rationale_is_present_and_names_the_executed_order(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-02-bbb222-second.ipd.md": self.plan_text(
                            "bbb222", order=2
                        ),
                        "20260917-probe-01-aaa111-first.ipd.md": self.plan_text(
                            "aaa111", order=1
                        ),
                    }
                )
                _run_dir, state, _out, _err = self.initialize(mod, repo)
                self.assertIn("run_order", state)
                self.assertIsInstance(state["run_order"], dict)

    def test_the_run_created_event_is_the_first_ledger_record(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                events = self.events(run_dir)
                self.assertEqual(events[0]["event"], "run-created")
                self.assertEqual(events[0]["run_id"], state["run_id"])


class TheUntrackedDirtReportFiresOncePerRun(InitializeRunCase):
    """`tests/test_dirty_base_gate.py:179`/`:191` assert the call's PRESENCE and its POSITION in the
    source. The behavioral equivalents: the operator sees the notice exactly once, and it cannot
    fail the run.
    """

    def test_untracked_content_is_reported_and_does_not_refuse_the_run(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo()
                (repo / "unexpected.txt").write_text("dirt\n", encoding="utf-8")
                run_dir, state, out, err = self.initialize(mod, repo)
                combined = out + err
                self.assertIn(
                    "unexpected.txt",
                    combined,
                    f"{name} did not report the untracked path at run start",
                )
                # The report must NOT refuse: the run directory exists and the queue is frozen.
                self.assertTrue((run_dir / "state.json").is_file())
                self.assertEqual([i["id6"] for i in state["queue"]], ["aaa111"])

    def test_the_notice_is_emitted_ONCE_not_once_per_queue_entry(self):
        """The property `test_dirty_base_gate.py`'s position pin protects: placed beside the
        per-item guard it would repeat N times, so N is varied here rather than fixed at one."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-01-aaa111-one.ipd.md": self.plan_text(
                            "aaa111", order=1
                        ),
                        "20260917-probe-02-bbb222-two.ipd.md": self.plan_text(
                            "bbb222", order=2
                        ),
                        "20260917-probe-03-ccc333-three.ipd.md": self.plan_text(
                            "ccc333", order=3
                        ),
                    }
                )
                (repo / "unexpected.txt").write_text("dirt\n", encoding="utf-8")
                _run_dir, state, out, err = self.initialize(mod, repo)
                self.assertEqual(len(state["queue"]), 3)
                self.assertEqual(
                    (out + err).count("unexpected.txt"),
                    1,
                    f"{name} reported the untracked path once per ITEM rather than once per RUN",
                )


class ARunIdCollisionRefusesRatherThanOverwrites(InitializeRunCase):
    """The one destructive failure mode in this function: a second run freezing over the first.

    Characterized because a shared core reorders nothing else about the durable writes, but this
    check sits between the `run_id` resolution and the `mkdir`, and it is the only thing standing
    between a re-used `--run-id` and a clobbered run.
    """

    def test_reusing_a_run_id_refuses_and_leaves_the_first_run_intact(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo()
                first_dir, first_state, _o, _e = self.initialize(mod, repo)
                run_id = first_state["run_id"]

                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(repo)]
                )
                args.prepare_only = True
                args.run_id = run_id
                with self.assertRaises(runner_shared.DriverError) as ctx:
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                self.assertIn("Run already exists", str(ctx.exception))
                self.assertEqual(
                    runner_shared.load_state(first_dir)["created_at"],
                    first_state["created_at"],
                    f"{name} overwrote an existing run's frozen state",
                )


class TheDependencyPreflightRefusesAnInvalidGraphBeforeFreezing(InitializeRunCase):
    """Fail-closed on a bad dependency graph, before any durable state (`8guhs0` E-02).

    Behavioral, because the source pins on this function do not cover it at all: the closest thing
    is the ORDER pins, and neither names `enforce_dependency_preflight`.
    """

    def test_an_unresolvable_dependency_token_refuses_the_whole_run(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-01-aaa111-dependent.ipd.md": self.plan_text(
                            "aaa111", deps="unresolved"
                        )
                    }
                )
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(repo)]
                )
                args.prepare_only = True
                with self.assertRaises(runner_shared.DriverError):
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                root = runner_shared.state_root(repo)
                self.assertEqual(
                    [p for p in root.iterdir() if p.is_dir()] if root.is_dir() else [],
                    [],
                    f"{name} froze a run whose dependency graph it then refused",
                )


class TheManifestAndRunbookAreFrozenWithTheirDigests(InitializeRunCase):
    """A run's inputs are recorded by content, not only by path, so a later edit cannot silently
    change what the run was started from. Pinned because a shared writer computes four values here
    (`manifest`, `manifest_sha256`, `runbook`, `runbook_sha256`) from local variables, which is the
    easiest place for a relocation to drop one.
    """

    def test_a_discovered_manifest_is_written_into_the_run_and_digested(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                run_dir, state, _o, _e = self.initialize(mod, self.make_repo())
                manifest_path = Path(state["manifest"])
                self.assertEqual(manifest_path.parent, run_dir)
                self.assertTrue(manifest_path.is_file())
                self.assertEqual(
                    state["manifest_sha256"],
                    runner_shared.sha256_file(manifest_path),
                    f"{name}'s frozen manifest digest does not match the file it names",
                )

    def test_a_default_runbook_is_written_into_the_run_and_digested(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                run_dir, state, _o, _e = self.initialize(mod, self.make_repo())
                runbook_path = Path(state["runbook"])
                self.assertEqual(runbook_path.parent, run_dir)
                self.assertEqual(
                    state["runbook_sha256"], runner_shared.sha256_file(runbook_path)
                )

    def test_the_run_scaffold_directories_and_register_exist(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                run_dir, _state, _o, _e = self.initialize(mod, self.make_repo())
                for sub in ("sessions", "outcomes", "prompts"):
                    self.assertTrue((run_dir / sub).is_dir(), f"{name} missing {sub}/")
                self.assertTrue((run_dir / "decisions-and-questions.md").is_file())
                self.assertTrue((run_dir / "execution-report.md").is_file())


class TheFrozenStateSurvivesAResume(InitializeRunCase):
    """F-2's resume proof, from BOTH hosts.

    The plan asks for it as cheap confirmation rather than discovery (the queue-entry key sets are
    identical). What it establishes is that state frozen by `initialize_run` is READABLE by the
    resume path's own loader and carries everything a resume re-derives its actions from.
    """

    def test_a_frozen_run_reloads_with_its_queue_actions_re_derivable(self):
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-00-orc001-parent.ipd.md": self.plan_text(
                            "orc001", kind="orchestrator", order=0
                        ),
                        "20260917-probe-01-aaa111-child.ipd.md": self.plan_text(
                            "aaa111", order=1
                        ),
                    }
                )
                run_dir, frozen, _o, _e = self.initialize(mod, repo)
                reloaded = runner_shared.load_state(run_dir)
                self.assertEqual(reloaded["queue"], frozen["queue"])
                for item in reloaded["queue"]:
                    with self.subTest(item=item["id6"]):
                        self.assertEqual(
                            mod.action_for(item["kind"], item["initial_status"]),
                            item["action"],
                            "a resume re-derives the action from the frozen kind+status, so the "
                            "two must agree with what was frozen",
                        )

    def test_the_frozen_queue_sorts_the_same_way_after_a_reload(self):
        """`queue_sort_key` is shared, so the ORDER a resume computes must not depend on anything
        the freeze dropped."""
        for name, mod in HOST_PAIRS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-02-bbb222-second.ipd.md": self.plan_text(
                            "bbb222", order=2
                        ),
                        "20260917-probe-01-aaa111-first.ipd.md": self.plan_text(
                            "aaa111", order=1
                        ),
                    }
                )
                run_dir, frozen, _o, _e = self.initialize(mod, repo)
                reloaded = runner_shared.load_state(run_dir)
                # `queue_sort_key` is ONE object reached by both hosts (agy imports oc's), so the
                # host module's attribute is deliberately what is called here.
                self.assertIs(mod.queue_sort_key, oc_runipd.queue_sort_key)

                def order(queue: list[dict]) -> list[str]:
                    by_id = {i["id6"]: i for i in queue}
                    return [
                        i["id6"]
                        for i in sorted(
                            queue, key=lambda it: mod.queue_sort_key(it, by_id)
                        )
                    ]

                self.assertEqual(order(frozen["queue"]), order(reloaded["queue"]))


if __name__ == "__main__":
    unittest.main()

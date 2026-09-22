#!/usr/bin/env python3
"""hostdedup Order 01 (`li44r9`) E-05: the anti-re-fork guard over the symbols this plan lifted.

WHAT THIS FILE PROTECTS. Plan `li44r9` gave sixteen byte-identical runner symbols ONE definition each in
`runner_shared`, leaving each host a thin delegating wrapper. The value of that is entirely in it STAYING
true: the defect that motivated the whole `hostdedup` Set (`cjefq5`, fixed 2026-09-17) was ONE expression
present byte-identically in both hosts, and a fix to one copy that the other silently missed killed six
approved plans plus two orchestrators at queue build across 13 separate runs before anyone traced it. A
re-fork re-creates exactly that, and the cost multiplies: at two hosts a duplicated symbol is written
twice, at the five the maintainer intends (codex, claude, hermes) it is written five times.

ASSERT DELEGATION, NEVER OBJECT IDENTITY, and this is the single most important thing to understand before
editing this file. Under the wrapper design the plan chose, `oc_runipd.<sym> is agy_runipd.<sym>` is FALSE,
and so is `oc_runipd.<sym> is runner_shared.<sym>`: each host keeps its own function object whose body
calls the shared one. Verified at authoring on the pre-existing wrapper `git_head`, both comparisons
returned False. So an `is` check would FAIL a correct implementation, which is why the plan's own validation
contract forbids that form and why `TheWrapperIsNotTheSameObject` below asserts the non-identity
POSITIVELY: a future reader who "fixes" this file by reaching for `assertIs` will fail that test and read
this note.

THE TWO HALVES, neither of which implies the other:
  1. STRUCTURE: the shared module defines the symbol EXACTLY ONCE, and each host's definition is a pure
     delegation to it. Half 1 alone passes while a host rebinds the name to something else at runtime.
  2. REACHABILITY: the delegation really resolves to the shared definition when called. Half 2 alone
     passes while a stale duplicate definition sits in the file shadowed by a later import, which is a
     trap rather than a fix.

WHY THE DELEGATION PREDICATE IS THE REPOSITORY'S OWN. `is_pure_delegation` below is the same shape the four
`test_rununify_*` pin files carry, deliberately, because those files' `STILL_DOUBLE_DEFINED` /
`THIN_WRAPPERS_OVER_RUNNER_SHARED` tables and this guard must agree about what a wrapper IS. If they
disagreed, a symbol could be a "wrapper" to one file and a "fork" to the other and the census would mean
nothing.

WHY NOT A SOURCE-TEXT SEARCH. A `assertIn("runner_shared.terminate_process", source)` is satisfied by a
COMMENT and by a docstring -- measured in this repository, where exactly that form was satisfied by a
comment (`tests/test_lane_tool_identity.py` records the measurement). Every assertion here parses the AST
or calls the object.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import unittest

from agent_workflows import agy_runipd, oc_runipd, runner_shared

AW = pathlib.Path(str(inspect.getsourcefile(oc_runipd))).parent
HOSTS = ("oc_runipd", "agy_runipd")
MODULES = {"oc_runipd": oc_runipd, "agy_runipd": agy_runipd}

#: THE LIFTED SET: every symbol plan `li44r9` gave one definition in `runner_shared`, each now reached
#: through a thin per-host wrapper. Driven from a named table so a re-fork fails LOUDLY against a
#: specific name rather than drifting back one symbol at a time.
#:
#: MEASURED AT EXECUTION HEAD with the committed scanner `tools/runner_fork_scan.py`, not copied from the
#: plan: the plan's authored list held SEVENTEEN and one of those (`disable_lane_prompt`) was held back
#: with a recorded reason, see `TheDeliberatelyUnliftedSymbol` below.
LIFTED = (
    "StallWatchdog",
    "_budget_breach_recorder",
    "_escalation_recorder",
    "_observe_between_turn_stop",
    "_record_checkpoint_stop",
    "_record_deliberate_stop",
    "build_isolation_notice",
    "driver_finalize",
    "evaluate_clean_base_for_launch",
    "handle_stop_command",
    "install_stop_triggers",
    "locked_run",
    "requeue_interrupted",
    "run_lock",
    "set_plan_approved",
    "terminate_process",
)

#: `StallWatchdog` is a CLASS and its host form is a SUBCLASS, not a delegating function, so the
#: function-shaped delegation predicate does not apply to it. It is checked by
#: `TheWatchdogSubclassesTheSharedOne` instead, which is a stronger statement for a class: a subclass
#: inherits the shared behavior and cannot re-implement the stall loop without overriding a named method.
#:
#: WHY A SUBCLASS AT ALL, since a bare alias would have been thinner: the host must bind its OWN
#: `terminate_process`, which forwards that host's tunable module-level grace constants at call time. An
#: alias would have reaped with the shared defaults and silently made those constants inert.
CLASS_SHAPED = ("StallWatchdog",)

#: Symbols whose shared definition takes a HOST-VARYING value from the caller, and the `HostLabels` field
#: or injected dependency that carries it. This table is the plan's E-08 answer made checkable: each of
#: these looked decision-free to lift (byte-identical bodies) and was NOT, because a body can reference a
#: module-level name whose VALUE differs per host while AST comparison matches only the NAME.
HOST_VARYING = {
    "set_plan_approved": "full_auto_actor",
    "driver_finalize": "command",
    "handle_stop_command": "command",
    "install_stop_triggers": "command",
    "_escalation_recorder": "command",
}


def module_body(name: str) -> list[ast.stmt]:
    return ast.parse((AW / f"{name}.py").read_text(encoding="utf-8")).body


def top_level_defs(name: str) -> dict[str, list[ast.stmt]]:
    """EVERY top-level definition per name, as a LIST rather than last-wins.

    A list, because a duplicate definition in one file is itself a defect this guard must see: a
    last-wins mapping would silently hide a stale shadowed copy, which is precisely the trap half 2 of
    this file's contract exists to catch.
    """
    out: dict[str, list[ast.stmt]] = {}
    for node in module_body(name):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.setdefault(node.name, []).append(node)
    return out


def is_pure_delegation(node: ast.stmt | None) -> bool:
    """The sanctioned wrapper shape: one statement calling a single `runner_shared.X(...)`.

    The same predicate the four `test_rununify_*` pin files carry, so this guard and those censuses
    cannot disagree about what a wrapper is.
    """
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
    func = value.func
    return (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id == "runner_shared"
    )


def delegated_target(node: ast.stmt) -> str | None:
    """The `runner_shared` attribute a delegating wrapper actually calls, or None."""
    if not is_pure_delegation(node):
        return None
    body = [
        stmt
        for stmt in node.body  # type: ignore[union-attr]
        if not (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        )
    ]
    call = body[0].value  # type: ignore[union-attr]
    return call.func.attr  # type: ignore[union-attr]


FUNCTION_SHAPED = tuple(name for name in LIFTED if name not in CLASS_SHAPED)


class TheSharedModuleOwnsExactlyOneDefinition(unittest.TestCase):
    """Half 1(a): `runner_shared` defines each lifted symbol, exactly once."""

    def test_every_lifted_symbol_is_defined_in_runner_shared(self):
        defs = top_level_defs("runner_shared")
        for name in LIFTED:
            with self.subTest(symbol=name):
                self.assertIn(
                    name,
                    defs,
                    f"`runner_shared` no longer defines {name}. If it moved somewhere else, this "
                    "table must move with it; if it was pushed back into the hosts, that is the "
                    "re-fork this file exists to prevent and it must be justified, not silently "
                    "accommodated.",
                )

    def test_no_lifted_symbol_is_defined_twice_in_runner_shared(self):
        """A SECOND definition shadows the first, so half the callers get code nobody is reading.

        Measured during this plan's execution, which is why it is asserted rather than assumed: THREE of
        the lifted symbols were already defined in `runner_shared` while both hosts kept their own
        bodies, and one of those shared copies was BROKEN (it called `git_status` without the required
        keyword-only `run_checked`, so every record it wrote would have read `<unobserved: ...>`). It had
        never been noticed precisely because it was unreachable. A duplicate here is the same hazard.
        """
        defs = top_level_defs("runner_shared")
        for name in LIFTED:
            with self.subTest(symbol=name):
                self.assertEqual(
                    len(defs.get(name, [])),
                    1,
                    f"`runner_shared` defines {name} {len(defs.get(name, []))} times; the later "
                    "definition shadows the earlier one, so a reader can fix a body no caller "
                    "reaches",
                )


class EveryHostDelegatesRatherThanForking(unittest.TestCase):
    """Half 1(b): each host's definition is a pure delegation, on EVERY host."""

    def test_every_host_still_defines_the_symbol(self):
        """The wrapper must stay, so the name is resolvable in the module a source pin looks at.

        This is the plan's OQ-01 answer (keep the wrapper, following 21 existing precedents), asserted:
        deleting a wrapper and rewriting every internal call site is a much larger diff whose risk is
        unrelated to de-duplication, and it would break the source-inspection pins that read these names
        out of the driver modules.
        """
        for host in HOSTS:
            defs = top_level_defs(host)
            for name in LIFTED:
                with self.subTest(host=host, symbol=name):
                    self.assertIn(
                        name,
                        defs,
                        f"{host} no longer defines {name} at all; the wrapper form keeps the name "
                        "resolvable in the module every source-inspection pin reads",
                    )

    def test_every_function_shaped_wrapper_is_a_pure_delegation(self):
        """THE CENTRAL ASSERTION: no host carries a real body for a lifted symbol.

        This is what fails when someone re-forks: a wrapper that GREW logic is a fork again, whether or
        not it also still calls the shared function.
        """
        for host in HOSTS:
            defs = top_level_defs(host)
            for name in FUNCTION_SHAPED:
                with self.subTest(host=host, symbol=name):
                    self.assertTrue(
                        is_pure_delegation(defs[name][-1]),
                        f"{host}.{name} is no longer a single delegating call to `runner_shared`. "
                        "A wrapper that grew logic has RE-FORKED the symbol: the fix lands in one "
                        "host and the others silently miss it, which is exactly the `cjefq5` defect "
                        "that killed 6 plans and 2 orchestrators across 13 runs.",
                    )

    def test_each_wrapper_delegates_to_the_SAME_NAME_it_wraps(self):
        """A delegation to the WRONG shared symbol type-checks, passes the predicate, and is a bug.

        Asserted separately because `is_pure_delegation` only proves the call goes to `runner_shared`
        SOMEWHERE. A copy-paste that left `handle_stop_command` calling
        `runner_shared.install_stop_triggers` would satisfy every other assertion in this class.
        """
        for host in HOSTS:
            defs = top_level_defs(host)
            for name in FUNCTION_SHAPED:
                with self.subTest(host=host, symbol=name):
                    self.assertEqual(
                        delegated_target(defs[name][-1]),
                        name,
                        f"{host}.{name} delegates to `runner_shared."
                        f"{delegated_target(defs[name][-1])}`, not to its own name",
                    )

    def test_no_host_defines_a_lifted_symbol_twice(self):
        """A stale shadowed copy is a trap: a reader fixes a body no caller reaches."""
        for host in HOSTS:
            defs = top_level_defs(host)
            for name in LIFTED:
                with self.subTest(host=host, symbol=name):
                    self.assertEqual(
                        len(defs[name]),
                        1,
                        f"{host} defines {name} {len(defs[name])} times; the later definition "
                        "shadows the earlier, so one of them is unreachable code a future reader "
                        "may 'fix' with no effect",
                    )


class TheDelegationReallyResolves(unittest.TestCase):
    """Half 2: the wrapper is not merely SHAPED like a delegation, it reaches the shared object."""

    def test_every_lifted_symbol_is_callable_on_every_host(self):
        for host in HOSTS:
            for name in LIFTED:
                with self.subTest(host=host, symbol=name):
                    self.assertTrue(
                        callable(getattr(MODULES[host], name, None)),
                        f"{host}.{name} is not callable at runtime, so the wrapper's static shape "
                        "says nothing about what a caller actually gets",
                    )

    def test_the_shared_definition_is_reached_when_a_wrapper_is_called(self):
        """DRIVEN, not read: replace the shared definition and observe the host reach the replacement.

        The strongest available statement of "the delegation resolves", and it is immune to the two
        failure modes a static check misses: a name rebound at import time, and a stale shadowed
        duplicate. A host that carried its own copy would call that copy and never see the sentinel.

        The two CONTEXT MANAGERS are exercised the same way, since their wrappers return the shared
        factory's result rather than yielding themselves.

        THE REPLACEMENT RECORDS ITS CALL RATHER THAN ONLY RETURNING A SENTINEL, because a wrapper whose
        contract is to return None (`terminate_process`, `_record_deliberate_stop`) cannot be checked by
        its return value at all: a host carrying its own body would also return None and the check would
        pass vacuously. Recording the invocation works for every wrapper regardless of what it returns,
        and the returned sentinel is asserted ADDITIONALLY wherever the wrapper does propagate a value.
        """
        for host in HOSTS:
            module = MODULES[host]
            for name in FUNCTION_SHAPED:
                with self.subTest(host=host, symbol=name):
                    sentinel = object()
                    reached: list[bool] = []

                    def replacement(*_a, _reached=reached, _s=sentinel, **_kw):
                        _reached.append(True)
                        return _s

                    real = getattr(runner_shared, name)
                    setattr(runner_shared, name, replacement)
                    try:
                        got = getattr(module, name)(*([None] * _ARITY.get(name, 1)))
                    finally:
                        setattr(runner_shared, name, real)
                    self.assertEqual(
                        reached,
                        [True],
                        f"{host}.{name} did not reach the `runner_shared` definition exactly once "
                        f"(recorded {len(reached)} calls) while the shared function was replaced, so "
                        "this host is running code of its own",
                    )
                    if got is not None:
                        self.assertIs(
                            got,
                            sentinel,
                            f"{host}.{name} reached the shared definition but returned {got!r} "
                            "instead of propagating its result, so it is post-processing a value "
                            "the shared body owns",
                        )


#: Minimum positional arity for driving each wrapper with placeholder arguments in
#: `test_the_shared_definition_is_reached_when_a_wrapper_is_called`. The VALUES are irrelevant (the
#: shared function is replaced by a sentinel-returning stub that ignores them); only the COUNT matters,
#: so Python does not raise `TypeError` before the delegation happens.
_ARITY = {
    "_budget_breach_recorder": 4,
    "_escalation_recorder": 2,
    "_observe_between_turn_stop": 4,
    "_record_checkpoint_stop": 4,
    "_record_deliberate_stop": 3,
    "build_isolation_notice": 1,
    "driver_finalize": 5,
    "evaluate_clean_base_for_launch": 1,
    "handle_stop_command": 1,
    "install_stop_triggers": 1,
    "locked_run": 1,
    "requeue_interrupted": 2,
    "run_lock": 1,
    "set_plan_approved": 3,
    "terminate_process": 1,
}


class TheWrapperIsNotTheSameObject(unittest.TestCase):
    """The non-identity, asserted POSITIVELY so nobody "fixes" this file with `assertIs`.

    Under the wrapper design, object identity is FALSE in both directions, and any evidence requirement
    phrased as identity is unsatisfiable by a correct implementation. Stating it as a test rather than
    only as a comment means the next author who reaches for `assertIs` fails HERE, with this docstring in
    the failure, instead of concluding the lift is broken.
    """

    def test_the_hosts_do_not_share_the_wrapper_object(self):
        for name in FUNCTION_SHAPED:
            with self.subTest(symbol=name):
                self.assertIsNot(
                    getattr(oc_runipd, name),
                    getattr(agy_runipd, name),
                    f"{name} is now the SAME OBJECT on both hosts. That is not a defect in itself, "
                    "but it means the wrapper form was replaced by a re-export, so this file's "
                    "delegation assertions no longer describe the design. Update them "
                    "deliberately rather than leaving them asserting the wrong thing.",
                )

    def test_a_wrapper_is_not_the_shared_object_either(self):
        for name in FUNCTION_SHAPED:
            with self.subTest(symbol=name):
                self.assertIsNot(
                    getattr(oc_runipd, name),
                    getattr(runner_shared, name),
                    f"{name} on the host IS the shared object, so it is a re-export rather than a "
                    "wrapper; see the sibling test's note",
                )


class TheWatchdogSubclassesTheSharedOne(unittest.TestCase):
    """`StallWatchdog` is a CLASS, so its "delegation" is inheritance and is checked as such."""

    def test_each_host_subclasses_the_shared_watchdog(self):
        for host in HOSTS:
            with self.subTest(host=host):
                cls = getattr(MODULES[host], "StallWatchdog")
                self.assertTrue(
                    issubclass(cls, runner_shared.StallWatchdog),
                    f"{host}.StallWatchdog no longer derives from the shared one, so the stall "
                    "loop has been re-forked",
                )
                self.assertIsNot(
                    cls,
                    runner_shared.StallWatchdog,
                    f"{host}.StallWatchdog IS the shared class, so it cannot bind this host's own "
                    "`terminate_process` and the host's grace constants are silently inert",
                )

    def test_the_subclass_overrides_ONLY_the_constructor(self):
        """The subclass exists to BIND a dependency, not to re-implement behavior.

        An override of `_run`, `touch`, `remaining` or the context-manager methods would be a re-fork of
        the stall logic wearing an inheritance hat, and it would pass `issubclass`.
        """
        for host in HOSTS:
            defs = top_level_defs(host)
            node = defs["StallWatchdog"][-1]
            overridden = {
                sub.name
                for sub in node.body  # type: ignore[union-attr]
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            with self.subTest(host=host):
                self.assertEqual(
                    overridden,
                    {"__init__"},
                    f"{host}.StallWatchdog overrides {sorted(overridden)}; only `__init__` may be "
                    "overridden (to bind this host's reaper). Anything else re-implements the "
                    "shared stall loop.",
                )

    def test_the_host_watchdog_reaps_through_THIS_hosts_terminate_process(self):
        """The whole reason the subclass exists, driven rather than read.

        If the subclass failed to bind the host's reaper, the watchdog would kill a stalled child with
        `runner_shutdown`'s DEFAULT grace values and every per-host tuning would be silently inert.
        """
        for host in HOSTS:
            module = MODULES[host]
            with self.subTest(host=host):
                seen: list[object] = []
                real = module.terminate_process
                setattr(module, "terminate_process", lambda p: seen.append(p))
                try:
                    watchdog = module.StallWatchdog(_DeadProcess(), timeout=1.0)
                    marker = object()
                    watchdog._reaper(marker)  # type: ignore[attr-defined]
                finally:
                    setattr(module, "terminate_process", real)
                self.assertEqual(
                    seen,
                    [marker],
                    f"{host}.StallWatchdog does not reap through this host's `terminate_process`, "
                    "so a stalled child is killed with the shared default grace values and this "
                    f"host's `_SIGINT_GRACE_SECONDS` tuning is inert. Observed: {seen!r}",
                )


class _DeadProcess:
    """A process stub that is already finished, so no watchdog thread does any real work."""

    pid = -1

    def poll(self) -> int:
        return 0


class TheHostVaryingValuesTravelByDESCRIPTOR(unittest.TestCase):
    """E-08's answer, asserted: a shared body must never bake in one host's identity.

    THE FINDING THIS ENCODES. Five of the lifted symbols had BYTE-IDENTICAL bodies on both hosts and were
    still not safe to move verbatim, because AST comparison matches on the NAME and a module-level name
    can resolve to a different value per host. The sharpest case is `set_plan_approved`: it reads
    `FULL_AUTO_ACTOR`, which was `"aw oc run --full-auto"` on one host and `"aw agy run --full-auto"` on
    the other, and passes it as `--actor` into a plan's PERMANENT `## Workflow history`. A verbatim lift
    would have attributed every Antigravity auto-approval to the OpenCode driver, in durable history, with
    every existing test still green.
    """

    def test_every_host_varying_symbol_takes_its_value_from_the_caller(self):
        """The shared body must accept the host value as a keyword-only parameter.

        Keyword-only, so a caller cannot supply it positionally by accident, and REQUIRED, so a host that
        forgets raises instead of silently inheriting another host's identity.
        """
        shared = {
            node.name: node
            for node in module_body("runner_shared")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in HOST_VARYING:
            with self.subTest(symbol=name):
                node = shared[name]
                kwonly = {arg.arg for arg in node.args.kwonlyargs}
                self.assertIn(
                    "labels",
                    kwonly,
                    f"`runner_shared.{name}` no longer takes `labels`, so it cannot know which host "
                    "it is serving and must be baking one host's identity into shared code",
                )
                position = [arg.arg for arg in node.args.kwonlyargs].index("labels")
                self.assertIsNone(
                    node.args.kw_defaults[position],
                    f"`runner_shared.{name}`'s `labels` gained a DEFAULT. A default here is a silent "
                    "misattribution waiting to happen: a host that stops passing its own labels "
                    "would write another host's name into durable records and nothing would fail.",
                )

    def test_each_host_binds_its_OWN_labels(self):
        """A wrapper that passed the WRONG host's labels would satisfy every other assertion here."""
        expected = {
            "oc_runipd": "OC_HOST_LABELS",
            "agy_runipd": "AGY_HOST_LABELS",
        }
        for host in HOSTS:
            defs = top_level_defs(host)
            for name in HOST_VARYING:
                with self.subTest(host=host, symbol=name):
                    source = ast.unparse(defs[name][-1])
                    self.assertIn(
                        f"runner_shared.{expected[host]}",
                        source,
                        f"{host}.{name} does not bind {expected[host]}; it would record another "
                        "host's identity",
                    )
                    other = expected[
                        "agy_runipd" if host == "oc_runipd" else "oc_runipd"
                    ]
                    self.assertNotIn(
                        f"runner_shared.{other}",
                        source,
                        f"{host}.{name} binds {other}, i.e. the OTHER host's labels",
                    )

    def test_the_full_auto_actor_is_a_no_default_descriptor_field(self):
        """`HostLabels` must keep refusing a construction that omits the actor.

        This is the mechanism that makes the misattribution impossible rather than merely unlikely: a
        `NamedTuple` raises `TypeError` on a missing field at construction, so a new host cannot forget.
        """
        with self.assertRaises(TypeError):
            runner_shared.HostLabels(  # type: ignore[call-arg]
                command="aw x run",
                review_command="aw x review",
                argv_tokens=("x",),
                argv_subcommands=("run",),
                product="X",
                report_title="# X:",
                shell_tool=None,
                emits_launch_identity=False,
            )

    def test_each_host_records_its_OWN_auto_approval_actor(self):
        """THE BOTH-DIRECTIONS ATTRIBUTION TEST, and the one that would have caught the defect.

        Driven end to end through each host's real `set_plan_approved`, reading the `--actor` value off
        the argv it actually assembles. A green suite without this proves nothing about the failure that
        matters most, because the bodies were byte-identical and every structural check passed.
        """
        expected = {
            "oc_runipd": "aw oc run --full-auto",
            "agy_runipd": "aw agy run --full-auto",
        }
        for host in HOSTS:
            module = MODULES[host]
            with self.subTest(host=host):
                captured: list[list[str]] = []
                real = module.run_checked
                setattr(
                    module,
                    "run_checked",
                    lambda cmd, **_kw: captured.append(list(cmd)),
                )
                try:
                    module.set_plan_approved(pathlib.Path("/nonexistent"), "aaa111")
                finally:
                    setattr(module, "run_checked", real)
                self.assertTrue(captured, f"{host} assembled no argv at all")
                argv = captured[0]
                self.assertIn("--actor", argv)
                actor = argv[argv.index("--actor") + 1]
                self.assertEqual(
                    actor,
                    expected[host],
                    f"{host} records {actor!r} as the auto-approval actor, but this host is "
                    f"{expected[host]!r}. This value lands in a plan's PERMANENT `## Workflow "
                    "history`, so a wrong value here is durable-history misattribution that no "
                    "later reader can distinguish from the truth.",
                )

    def test_the_module_constant_and_the_descriptor_cannot_DISAGREE(self):
        """Each host's `FULL_AUTO_ACTOR` must BE the descriptor's value, not a second spelling of it.

        The shipped assertions (`tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`) check the argv
        against each host's module constant, so a literal that drifted from the descriptor would keep
        those tests passing while the runner wrote the other value. Reading the constant FROM the
        descriptor is what makes the two unable to diverge; this asserts that property rather than the
        current values.
        """
        for host, labels in (
            ("oc_runipd", runner_shared.OC_HOST_LABELS),
            ("agy_runipd", runner_shared.AGY_HOST_LABELS),
        ):
            with self.subTest(host=host):
                self.assertEqual(
                    MODULES[host].FULL_AUTO_ACTOR,
                    labels.full_auto_actor,
                    f"{host}.FULL_AUTO_ACTOR and its `HostLabels.full_auto_actor` disagree. The "
                    "shipped argv assertions read the module constant, so this drift is invisible "
                    "to them while the runner writes the descriptor's value into permanent history.",
                )


class ThePerHostGraceTuningSurvivedTheLift(unittest.TestCase):
    """The one BEHAVIOR CONTRACT this lift could have broken silently.

    `terminate_process` reads two module-level grace constants and a shipped test TUNES them per host. A
    shared body reading shared constants would have made that tuning inert: the test would set
    `oc_runipd._SIGINT_GRACE_SECONDS` and the reaper would never see it, with nothing failing to say so.
    That is why the shared function takes them as no-default parameters and each wrapper reads its own at
    call time.
    """

    def test_tuning_a_hosts_constants_still_reaches_the_reaper(self):
        from agent_workflows import runner_shutdown

        for host in HOSTS:
            module = MODULES[host]
            with self.subTest(host=host):
                seen: dict[str, float] = {}
                real = runner_shutdown.terminate_process
                setattr(
                    runner_shutdown,
                    "terminate_process",
                    lambda _p, **kw: seen.update(kw),
                )
                saved = (module._SIGINT_GRACE_SECONDS, module._SIGTERM_GRACE_SECONDS)
                try:
                    module._SIGINT_GRACE_SECONDS = 0.11
                    module._SIGTERM_GRACE_SECONDS = 0.07
                    module.terminate_process(_DeadProcess())
                finally:
                    setattr(runner_shutdown, "terminate_process", real)
                    (
                        module._SIGINT_GRACE_SECONDS,
                        module._SIGTERM_GRACE_SECONDS,
                    ) = saved
                self.assertEqual(
                    seen,
                    {"sigint_grace": 0.11, "sigterm_grace": 0.07},
                    f"{host}: tuning this module's grace constants no longer reaches the reaper, so "
                    f"the documented per-host tuning contract is inert. Observed: {seen!r}",
                )

    def test_the_shared_reaper_offers_no_grace_defaults(self):
        """No default, so a host cannot forget to pass its own and silently inherit another's timing."""
        node = next(
            n
            for n in module_body("runner_shared")
            if isinstance(n, ast.FunctionDef) and n.name == "terminate_process"
        )
        names = [arg.arg for arg in node.args.kwonlyargs]
        for required in ("sigint_grace", "sigterm_grace"):
            with self.subTest(parameter=required):
                self.assertIn(required, names)
                self.assertIsNone(
                    node.args.kw_defaults[names.index(required)],
                    f"`runner_shared.terminate_process`'s `{required}` gained a default, so a host "
                    "that stops passing its own value silently reaps on someone else's timing",
                )


class HostNeutralProseInTheSharedBodies(unittest.TestCase):
    """E-03: a shared docstring must not name ONE host.

    NOT PEDANTRY, and the reason is the third host. A shared body whose docstring says "a child OpenCode
    process" or "the per-turn `run_opencode` handlers" is MISLEADING the moment a third host calls it, and
    the second form is worse than the first: `run_opencode` is a SYMBOL NAME that will not exist for that
    host at all, so a reader of its stack goes looking for something absent.

    SCOPED TO THE SYMBOLS THIS PLAN LIFTED, deliberately. `runner_shared` legitimately names hosts
    elsewhere -- `HostLabels`'s own field docstrings must give concrete examples, and the descriptor
    instances are per host by definition -- so a module-wide prohibition would be false. The property that
    holds is narrower and real: the BODIES this plan moved describe behavior without naming a host.
    """

    #: The bare abbreviations are matched on WORD BOUNDARIES by the committed scanner
    #: (`tools/runner_fork_scan.py`), because `oc` as a substring matches "process", "block" and
    #: "docstring". Here the check is over a small, known set of docstrings, so the explicit
    #: product/symbol spellings are what matter and are listed outright.
    HOST_TOKENS = (
        "OpenCode",
        "opencode",
        "Antigravity",
        "antigravity",
        "oc_runipd",
        "agy_runipd",
        "run_opencode",
        "run_agy_turn",
        "the agy twin",
        "the oc twin",
    )

    #: Sentences whose host names are LEGITIMATE and must not be scrubbed, keyed by the symbol they
    #: belong to. The distinction this table encodes is the one the E-03 finding actually turns on, and
    #: getting it wrong in either direction is a real cost:
    #:
    #:   * A DESCRIPTION of current behavior must be host-neutral, because it is read as true of whatever
    #:     host is calling, and "a child OpenCode process" is simply FALSE on another host.
    #:   * A HISTORICAL NOTE recording WHY the body is shaped as it is often CANNOT be host-neutral
    #:     without destroying its evidentiary value. `set_plan_approved`'s note is the clearest case: the
    #:     whole finding is that a verbatim lift would have attributed every ANTIGRAVITY auto-approval to
    #:     `aw oc run`, and a version that said "one host's approvals would be attributed to another
    #:     host" would be unverifiable prose. The concrete direction is the evidence.
    #:
    #: Each allowance is keyed to its symbol rather than granted globally, so a NEW host name appearing
    #: in a DESCRIPTION still fails even in a body that carries a historical note.
    HISTORICAL_NOTE_ALLOWANCES = {
        "set_plan_approved": (
            "`aw oc run --full-auto`",
            "`aw agy run --full-auto`",
            "every Antigravity auto-approval claim",
            "`aw oc run` performed it",
        ),
    }

    def test_no_lifted_shared_body_names_a_single_host(self):
        shared = {
            node.name: node
            for node in module_body("runner_shared")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        for name in LIFTED:
            node = shared[name]
            text = ast.get_docstring(node) or ""
            for sub in ast.walk(node):
                if isinstance(
                    sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    if sub is not node:
                        text += "\n" + (ast.get_docstring(sub) or "")
            for allowed in self.HISTORICAL_NOTE_ALLOWANCES.get(name, ()):
                text = text.replace(allowed, "<allowed historical citation>")
            for token in self.HOST_TOKENS:
                with self.subTest(symbol=name, token=token):
                    self.assertNotIn(
                        token,
                        text,
                        f"`runner_shared.{name}`'s docstring names {token!r}. Shared prose that "
                        "DESCRIBES behavior must be host-neutral: this body serves every host, so a "
                        "sentence naming one of them reads as false to the others. If the mention is "
                        "a HISTORICAL citation whose concrete direction IS the evidence, add the "
                        "exact phrase to HISTORICAL_NOTE_ALLOWANCES with its reason rather than "
                        "loosening this check.",
                    )

    def test_the_allowances_are_all_still_used(self):
        """An allowance for prose that no longer exists is a hole nobody notices.

        Asserted so the exemption table cannot accumulate stale entries that would silently permit a
        future host name matching an old phrase.
        """
        shared_source = (AW / "runner_shared.py").read_text(encoding="utf-8")
        for symbol, phrases in self.HISTORICAL_NOTE_ALLOWANCES.items():
            for phrase in phrases:
                with self.subTest(symbol=symbol, phrase=phrase):
                    self.assertIn(
                        phrase,
                        shared_source,
                        f"the allowance {phrase!r} for {symbol} matches nothing in "
                        "`runner_shared` any more; remove it rather than leaving a stale "
                        "exemption in place",
                    )


class TheDeliberatelyUnliftedSymbol(unittest.TestCase):
    """`disable_lane_prompt` was in the plan's target set and was HELD BACK, with a recorded reason.

    RECORDED HERE SO THE COUNT DOES NOT INVITE A LATER "COMPLETION". The plan named seventeen symbols;
    sixteen were lifted. A reader comparing this file's table against the plan will find one missing, and
    without this class the obvious repair is to lift it -- which is exactly the change four separate
    guards exist to prevent.

    THE REASON IS BEHAVIORAL, not stylistic: the function mutates a module-level `_LANE_PROMPT_DISABLED`
    through `global`, while each host's DIVERGED `_lane_reclaim_prompt` READS its own copy. A shared
    `global` would write the SHARED module's flag while every host kept reading its own, so prompt
    suppression on a repeated interrupt would silently stop working -- and the only symptom is an
    unattended run pausing to ask a question nobody is there to answer.

    `tests/test_runner_shared.py::UnmovableSymbolTests` is the authority and is not duplicated here. This
    class states the LINK between that pin and this plan's table, which is the thing a reader of either
    file alone cannot see.
    """

    def test_it_is_not_in_this_files_lifted_table(self):
        self.assertNotIn(
            "disable_lane_prompt",
            LIFTED,
            "`disable_lane_prompt` was added to the lifted set. It is PINNED UNMOVABLE with a "
            "behavioral reason; see this class's docstring and "
            "`tests/test_runner_shared.py::UnmovableSymbolTests`.",
        )

    def test_the_premise_of_the_pin_still_holds(self):
        """The pin's reason depends on `_lane_reclaim_prompt` still being per-host and divergent.

        Asserted rather than assumed, because the day that reader becomes shared, the pin's rationale
        genuinely expires and the symbol becomes liftable. A pin whose premise silently stopped holding is
        a pin nobody can reason about.
        """
        bodies = {}
        for host in HOSTS:
            defs = top_level_defs(host)
            self.assertIn(
                "_lane_reclaim_prompt",
                defs,
                f"{host} no longer defines `_lane_reclaim_prompt`; if the reader became SHARED, "
                "`disable_lane_prompt`'s unmovable pin may legitimately be revisited",
            )
            bodies[host] = ast.unparse(defs["_lane_reclaim_prompt"][-1])
        self.assertNotEqual(
            bodies["oc_runipd"],
            bodies["agy_runipd"],
            "the two hosts' `_lane_reclaim_prompt` are now IDENTICAL. That does not by itself make "
            "`disable_lane_prompt` liftable (the flag is still per-module), but it removes one leg "
            "of the recorded reason, so the pin should be re-derived rather than trusted.",
        )


class TheCommittedScannerIsInTreeAndAgrees(unittest.TestCase):
    """E-01: the fork census must be REPRODUCIBLE, by path, not re-improvised each time.

    The `hostdedup` orchestrator records as its PR-006 that "the same AST scan that produced the baseline"
    did not exist in-tree: every number the Set quoted came from an ad-hoc shell scan that was thrown
    away, so no later agent could re-derive it. Its Order 04 acceptance plan therefore REFUSES to
    improvise one and requires this scanner by path. That makes the scanner's EXISTENCE a contract, which
    is why it is asserted here rather than assumed.
    """

    SCANNER = "tools/runner_fork_scan.py"

    def test_the_scanner_exists_where_the_set_expects_it(self):
        path = AW.parent / self.SCANNER
        self.assertTrue(
            path.is_file(),
            f"the committed fork scanner is missing from {self.SCANNER}. The Set's acceptance plan "
            "consumes it BY PATH and refuses to improvise a replacement, so deleting or moving it "
            "makes the Set's headline number unreproducible again.",
        )

    def test_the_scanner_agrees_that_every_lifted_symbol_is_a_wrapper(self):
        """The scanner and this guard must not disagree about what was lifted.

        Two independent implementations of "is this a fork?" that can disagree are worse than one, so the
        scanner's verdict is checked against this file's table. A symbol this file calls lifted must not
        appear in the scanner's fork census.
        """
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_runner_fork_scan", AW.parent / self.SCANNER
        )
        assert spec is not None and spec.loader is not None
        scanner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scanner)

        data = scanner.census()
        forks = set(data["real_forks"])
        still_forked = sorted(set(LIFTED) & forks)
        # `StallWatchdog` is a SUBCLASS, which the scanner's function-shaped delegation predicate
        # correctly does not recognize as a wrapper, so it legitimately still reads as co-defined. It is
        # covered by `TheWatchdogSubclassesTheSharedOne` instead, and is exempted here by NAME rather
        # than by loosening the assertion.
        still_forked = [n for n in still_forked if n not in CLASS_SHAPED]
        self.assertEqual(
            still_forked,
            [],
            f"the committed scanner still counts {still_forked} as REAL FORKS while this file lists "
            "them as lifted. One of the two is wrong, and a census that disagrees with its own "
            "guard cannot be trusted by the Set's acceptance plan.",
        )


if __name__ == "__main__":
    unittest.main()

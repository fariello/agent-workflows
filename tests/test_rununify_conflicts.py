"""rununify 05 (`ct4w0a`): the TWO symbols where the two host runners genuinely DISAGREED.

Sixteen of this Set's shared symbols were duplicates that agreed. These two did not, and that is why
they were separated out: unifying them required DECIDING which behavior is correct, and a decision
nobody can see is a decision nobody can defend later. This file is where each decision is pinned.

WHAT IS ASSERTED, and why a bare "both hosts resolve the same object" would be worth very little here:

  1. ONE DEFINITION, reached identically from both hosts, with no module in the package re-forking it.
     Necessary, and nowhere near sufficient: a unified reader that lost one host's wire format would
     satisfy it perfectly while silently disabling that host's session resume.

  2. EVERY CAPABILITY EITHER HOST HAD, still present. `extract_session_id` must resolve an id for all
     four keys and both nesting shapes, and must still PREFER a `ses_`-prefixed value.

  3. THE FIRST-EVER COVERAGE FOR ANTIGRAVITY'S WIRE FORMAT. Measured while this plan was reviewed:
     `conversation_id` appeared in NO test in the repository, and `extract_session_id` was exercised
     only through two oc-shaped cases. So the central hazard -- that adopting oc's reader outright
     leaves agy unable to find its own session id -- was simultaneously TRUE and INVISIBLE. Every
     `AgyWireFormatTests` case below is additionally shown to FAIL against oc's pre-union reader
     (reconstructed here from its shipped body), which is what makes it a test of the CAPABILITY
     rather than a test that the union merely exists.

  4. THE PRECEDENCE DECISION, pinned as a decision. The two readers disagreed about return DISCIPLINE
     as well as about keys, so no union could preserve both answers; see `PrecedenceTests`.

  5. NON-VACUITY CONTROLS. Each capability is removed from a REPLICA of the shared body and the
     corresponding assertion is shown to fail. A capability test that would pass against a reader
     lacking the capability is decoration.

WHY A REPLICA RATHER THAN MONKEYPATCHING THE REAL FUNCTION: the controls must not mutate shared state
that another test in a parallel worker could observe. Each control below re-implements ONE deliberately
crippled variant locally and runs it over the same fixture, so the sabotage is inspectable and cannot
leak. The replicas are held to the real body by `ControlFidelityTests`, so a control cannot drift into
proving something about a strawman.
"""

from __future__ import annotations

import ast
import inspect
import json
import pathlib
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path

from agent_workflows import agy_runipd, oc_runipd, runner_shared

BOTH = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))
_PKG = pathlib.Path(runner_shared.__file__).parent

# Written in two pieces so this file never contains a literal that looks like a real session id.
_SES = "ses" + "_"


def _log(*events: object) -> Path:
    """Write a JSONL session log in a temp dir and return its path (caller owns the dir)."""
    temp = tempfile.mkdtemp()
    path = Path(temp) / "session.jsonl"
    path.write_text(
        "\n".join(json.dumps(e) for e in events) + "\n",
        encoding="utf-8",
    )
    return path


# ---- the pre-union oc reader, reconstructed for the "does this test the capability?" control -------
#
# THE POINT OF KEEPING THIS. A test asserting the shared reader finds `conversation_id` proves the
# union works, but not that it was ever at RISK. Running the SAME fixture through oc's pre-union body
# and showing it returns None is what demonstrates the capability would really have been lost, which is
# the claim (F-1) that justified excepting this symbol from the Set's oc-preferred ruling.
_OC_PRE_UNION_KEYS = ("sessionID", "sessionId", "session_id")


def _oc_pre_union_reader(log_path: Path) -> str | None:
    """oc's `extract_session_id` as it stood at 1171f7b2: three flat keys, no nesting, no dict guard."""
    if not log_path.exists():
        return None
    fallback: str | None = None
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            for key in _OC_PRE_UNION_KEYS:
                value = event.get(key)
                if not isinstance(value, str) or not value.strip():
                    continue
                if value.startswith(_SES):
                    return value
                if fallback is None:
                    fallback = value
    return fallback


class OneDefinitionTests(unittest.TestCase):
    """Property 1: one definition, reached identically, with no re-fork anywhere in the package."""

    SHARED = ("extract_session_id", "begin_baseline_env", "_SESSION_ID_KEYS")

    def test_both_hosts_resolve_the_same_object(self):
        for name in self.SHARED:
            with self.subTest(symbol=name):
                shared = getattr(runner_shared, name)
                for host_name, host in BOTH:
                    self.assertIs(
                        getattr(host, name),
                        shared,
                        f"{host_name}.{name} is a DIFFERENT object from the shared one",
                    )

    def test_the_defining_module_is_runner_shared(self):
        for name in ("extract_session_id", "begin_baseline_env"):
            with self.subTest(symbol=name):
                self.assertEqual(
                    getattr(runner_shared, name).__module__,
                    "agent_workflows.runner_shared",
                )

    def test_no_module_in_the_package_re_forks_either_symbol(self):
        """Checked REPO-WIDE by AST: a pairwise oc-vs-agy check passes while a third module copies."""
        for name in ("extract_session_id", "begin_baseline_env"):
            offenders = []
            for path in sorted(_PKG.rglob("*.py")):
                if path.name == "runner_shared.py":
                    continue
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                except SyntaxError:  # pragma: no cover
                    continue
                for node in tree.body:
                    if (
                        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and node.name == name
                    ):
                        offenders.append(f"{path.name}:{node.lineno}")
            with self.subTest(symbol=name):
                self.assertEqual(
                    offenders,
                    [],
                    f"{name} is re-defined outside runner_shared: {offenders}",
                )

    def test_the_session_key_list_is_ONE_tuple_with_all_four_keys(self):
        """It was defined TWICE with DIFFERENT contents (oc 3 keys, agy 4), which is how it forked."""
        self.assertEqual(
            runner_shared._SESSION_ID_KEYS,
            ("sessionID", "sessionId", "session_id", "conversation_id"),
        )
        sources = {}
        for host_name, host in BOTH:
            tree = ast.parse(inspect.getsource(host))
            sources[host_name] = [
                node.lineno
                for node in tree.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(t, ast.Name) and t.id == "_SESSION_ID_KEYS"
                    for t in node.targets
                )
            ]
        self.assertEqual(
            sources,
            {"oc_runipd": [], "agy_runipd": []},
            "neither host may keep its own `_SESSION_ID_KEYS`; a second constant is how the next "
            f"reader re-forks the disagreement: {sources}",
        )

    def test_driver_begin_has_exactly_one_launcher_body(self):
        """The hosts keep WRAPPERS (their pin helpers cannot move); the BODY must exist once.

        A wrapper is not a re-fork -- it is the de-duplicated form the maintainer ruled for an injected
        dependency (`818uru` OQ-02) -- so what is asserted is that no host body launches a subprocess.
        """
        for host_name, host in BOTH:
            with self.subTest(host=host_name):
                src = inspect.getsource(host.driver_begin)
                self.assertNotIn(
                    "subprocess.run",
                    src,
                    f"{host_name}.driver_begin must DELEGATE, not hold a second launcher body",
                )
                self.assertIn("runner_shared.driver_begin", src)
        self.assertIs(
            oc_runipd.runner_shared.driver_begin,
            agy_runipd.runner_shared.driver_begin,
            "both hosts must reach the SAME shared launcher",
        )

    def test_each_wrapper_keeps_the_original_signature(self):
        """No call site in either driver may have needed rewriting."""
        for host_name, host in BOTH:
            with self.subTest(host=host_name):
                sig = inspect.signature(host.driver_begin)
                self.assertEqual(
                    list(sig.parameters),
                    ["repo", "id6", "actor", "isolated"],
                    f"{host_name}.driver_begin's public signature changed",
                )
                isolated = sig.parameters["isolated"]
                self.assertEqual(isolated.kind, inspect.Parameter.KEYWORD_ONLY)
                self.assertIs(isolated.default, False)
                # The injected dependencies must NOT leak into the host-facing signature.
                self.assertNotIn("env_builder", sig.parameters)
                self.assertNotIn("argv_builder", sig.parameters)


class UnionCoversEveryKeyAndNestingTests(unittest.TestCase):
    """Property 2: an id is found for EVERY key and EVERY nesting shape in the union.

    INCLUDING THE THREE KEYS AND THE `init` NESTING THAT ZERO REAL LOGS CONTAIN. They are retained
    deliberately (narrowing a wire-format reader on 627 logs is absence-of-evidence reasoning, and the
    same tuple is read live by `oc_runipd._event_session_id`), and a retained branch with no test is
    exactly how a branch rots. So each is exercised here.
    """

    def test_every_flat_key_resolves(self):
        for key in runner_shared._SESSION_ID_KEYS:
            with self.subTest(key=key, nesting="flat"):
                log = _log({"type": "text", key: "id-for-" + key})
                self.assertEqual(runner_shared.extract_session_id(log), "id-for-" + key)

    def test_every_key_resolves_inside_every_nesting(self):
        for nest in runner_shared._SESSION_ID_NESTS:
            for key in runner_shared._SESSION_ID_KEYS:
                with self.subTest(key=key, nesting=nest):
                    log = _log({"type": "x", nest: {key: "nested-" + key}})
                    self.assertEqual(
                        runner_shared.extract_session_id(log), "nested-" + key
                    )

    def test_the_ses_prefix_preference_still_holds(self):
        """oc's preference: a `ses_` value wins over a non-prefixed one even when it comes LATER."""
        real = _SES + "realsession1"
        log = _log({"sessionID": "raw-provider-id"}, {"sessionID": real})
        self.assertEqual(runner_shared.extract_session_id(log), real)

    def test_a_non_dict_event_is_skipped_rather_than_raising(self):
        """agy's guard, kept. oc's reader had none and would raise on a list-shaped JSONL line."""
        log = _log(["not", "a", "dict"], 42, "a string", {"sessionID": _SES + "after"})
        self.assertEqual(runner_shared.extract_session_id(log), _SES + "after")

    def test_an_unparseable_line_is_skipped(self):
        temp = tempfile.mkdtemp()
        log = Path(temp) / "s.jsonl"
        log.write_text(
            "{not json at all\n" + json.dumps({"sessionID": _SES + "ok"}) + "\n",
            encoding="utf-8",
        )
        self.assertEqual(runner_shared.extract_session_id(log), _SES + "ok")

    def test_a_missing_log_and_an_idless_log_both_return_None(self):
        self.assertIsNone(
            runner_shared.extract_session_id(Path(tempfile.mkdtemp()) / "absent.jsonl")
        )
        self.assertIsNone(runner_shared.extract_session_id(_log({"type": "text"})))

    def test_a_blank_or_non_string_value_is_not_accepted_as_an_id(self):
        log = _log(
            {"sessionID": ""},
            {"sessionID": "   "},
            {"sessionID": 12345},
            {"sessionID": None},
            {"conversation_id": "real-conv-id"},
        )
        self.assertEqual(runner_shared.extract_session_id(log), "real-conv-id")


class AgyWireFormatTests(unittest.TestCase):
    """Property 3: THE FIRST-EVER COVERAGE for Antigravity's session wire format.

    Measured at this plan's review: `conversation_id` appeared in NO test file in the repository, and
    `extract_session_id` was exercised only by two oc-shaped cases in `tests/test_oc_runipd.py`. That
    is why "adopt oc's reader" would have disabled agy's session resume SILENTLY: nothing anywhere
    would have gone red. Each test here therefore does two things -- asserts the shared reader finds
    the id, and asserts oc's PRE-UNION reader does NOT -- so it tests the capability rather than the
    union's existence.

    WHAT LOSING THIS WOULD COST, since it explains why a `None` here is not cosmetic: with no observed
    session id, `aw agy run` cannot resume a session, and the `b7xarm` one-shot defect-report re-ask
    REFUSES to fire, so a real defect report would be dropped rather than re-requested.
    """

    def test_flat_conversation_id_resolves_and_oc_alone_would_have_missed_it(self):
        log = _log({"type": "result", "conversation_id": "conv-flat-1"})
        self.assertEqual(runner_shared.extract_session_id(log), "conv-flat-1")
        self.assertIsNone(
            _oc_pre_union_reader(log),
            "if oc's pre-union reader finds this, the F-1 capability claim is wrong and this test "
            "proves nothing about the union",
        )

    def test_conversation_id_nested_under_result_resolves(self):
        """The shape actually observed in the real corpus: both flat AND under `result`."""
        log = _log({"type": "result", "result": {"conversation_id": "conv-nested-1"}})
        self.assertEqual(runner_shared.extract_session_id(log), "conv-nested-1")
        self.assertIsNone(_oc_pre_union_reader(log))

    def test_conversation_id_nested_under_init_resolves(self):
        """UNOBSERVED in 627 real logs and retained deliberately; tested so it cannot rot."""
        log = _log({"type": "init", "init": {"conversation_id": "conv-init-1"}})
        self.assertEqual(runner_shared.extract_session_id(log), "conv-init-1")
        self.assertIsNone(_oc_pre_union_reader(log))

    def test_a_realistic_agy_log_resolves_end_to_end(self):
        """Not a single hand-built event: a multi-event log of the shape agy really writes."""
        log = _log(
            {"type": "system", "subtype": "init"},
            {"type": "assistant", "message": {"content": "working"}},
            {"type": "result", "result": {"conversation_id": "conv-realistic-9"}},
        )
        self.assertEqual(runner_shared.extract_session_id(log), "conv-realistic-9")
        self.assertIsNone(_oc_pre_union_reader(log))

    def test_oc_wire_format_still_resolves_too(self):
        """The other direction: the union must not have traded oc's format for agy's."""
        log = _log({"type": "step-start", "sessionID": _SES + "ocshape1"})
        self.assertEqual(runner_shared.extract_session_id(log), _SES + "ocshape1")
        self.assertEqual(_oc_pre_union_reader(log), _SES + "ocshape1")


class PrecedenceTests(unittest.TestCase):
    """Property 4: THE PRECEDENCE DECISION, recorded as a decision (decision `06-ct4w0a-D1`).

    The two readers disagreed about RETURN DISCIPLINE, not only about keys: agy returned the FIRST
    non-empty hit immediately, while oc scanned the WHOLE file and kept a non-`ses_` value only as a
    fallback. NO UNION CAN PRESERVE BOTH ANSWERS, so on the one shape where they differ -- an
    unprefixed id EARLY and a `ses_` id LATER in the same log -- somebody's answer had to change.

    THE DECISION IS OC'S DISCIPLINE, for three stated reasons: oc's preference is a SHIPPED TESTED
    CONTRACT (`tests/test_oc_runipd.py::test_extract_session_id_prefers_ses_prefixed_over_nonprefixed`)
    while nothing pinned agy's ordering anywhere; the standing maintainer ruling prefers oc absent a
    significant behavioral difference; and the affected shape needs an OpenCode-style `ses_` id to
    appear in a log that also carries an Antigravity `conversation_id`, which occurred in 0 of the 627
    logs censused. This test exists so that answer is a recorded decision rather than an emergent
    property a later reader discovers from a surprising run.
    """

    def _mixed_log(self) -> Path:
        return _log(
            {"type": "result", "conversation_id": "conv-EARLY"},
            {"type": "step", "sessionID": _SES + "LATER"},
        )

    def test_the_union_returns_the_ses_prefixed_value_not_the_earlier_conversation_id(
        self,
    ):
        self.assertEqual(
            runner_shared.extract_session_id(self._mixed_log()),
            _SES + "LATER",
            "the recorded decision is oc's discipline: scan the whole log and prefer `ses_`",
        )

    def test_this_is_the_answer_agys_pre_union_reader_did_NOT_give(self):
        """The change is disclosed rather than asserted away: agy returned `conv-EARLY` here.

        Reconstructs agy's pre-union first-hit discipline over the same fixture, so the behavior
        change this plan makes is visible in the suite rather than only in a plan's prose.
        """

        def agy_pre_union(log_path: Path) -> str | None:
            with log_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        continue
                    for key in runner_shared._SESSION_ID_KEYS:
                        value = event.get(key)
                        if isinstance(value, str) and value.strip():
                            return value  # FIRST hit, immediately
            return None

        log = self._mixed_log()
        self.assertEqual(agy_pre_union(log), "conv-EARLY")
        self.assertEqual(runner_shared.extract_session_id(log), _SES + "LATER")

    def test_a_log_with_no_prefixed_value_still_returns_the_first_it_saw(self):
        """The fallback is FIRST-seen, so the change is confined to the mixed case."""
        log = _log(
            {"conversation_id": "conv-first"},
            {"sessionID": "raw-second"},
        )
        self.assertEqual(runner_shared.extract_session_id(log), "conv-first")

    def test_the_dead_fallback_variable_agy_carried_is_gone(self):
        """agy's body initialized `fallback`, returned it, and could never reach it non-None.

        Here `fallback` is LIVE (it IS oc's discipline), which is exactly why the dead twin had to go:
        a reader comparing the two would otherwise credit agy with a discipline it did not have.
        """
        src = inspect.getsource(runner_shared.extract_session_id)
        self.assertIn("fallback", src, "the shared reader's fallback is load-bearing")
        for host_name, host in BOTH:
            with self.subTest(host=host_name):
                mod_src = inspect.getsource(host)
                self.assertNotIn(
                    "def extract_session_id",
                    mod_src,
                    f"{host_name} must hold no second body to carry a dead local in",
                )


class BeginBaselineTests(unittest.TestCase):
    """`driver_begin` emits the isolated declaration if and only if `isolated=True`, on BOTH hosts."""

    def test_the_overlay_is_exactly_the_declaration_or_nothing(self):
        self.assertEqual(
            runner_shared.begin_baseline_env(True), {"AW_ISOLATED_BASELINE": "1"}
        )
        self.assertEqual(runner_shared.begin_baseline_env(False), {})

    def test_the_child_env_carries_the_declaration_only_when_isolated(self):
        """Built exactly as the shared launcher builds it, for each host's bound env builder."""
        for host_name, host in BOTH:
            for isolated in (True, False):
                with self.subTest(host=host_name, isolated=isolated):
                    env = {
                        **host.pinned_child_env(),
                        **runner_shared.begin_baseline_env(isolated),
                    }
                    if isolated:
                        self.assertEqual(env.get("AW_ISOLATED_BASELINE"), "1")
                    else:
                        self.assertNotIn(
                            "AW_ISOLATED_BASELINE",
                            env,
                            "a non-isolated turn must send NOTHING (not '0'), which is what keeps "
                            "that path byte-identical to its pre-change behavior",
                        )

    def test_the_non_isolated_child_env_is_byte_identical_to_the_bare_pin(self):
        """E-05's property, asserted permanently rather than only in the plan's evidence.

        Every existing test exercises the NON-isolated path, so a silent change there would be
        invisible. The key count is asserted too, or an empty-dict bug would pass this vacuously.
        """
        for host_name, host in BOTH:
            with self.subTest(host=host_name):
                bare = host.pinned_child_env()
                with_overlay = {**bare, **runner_shared.begin_baseline_env(False)}
                self.assertEqual(with_overlay, bare)
                self.assertGreater(len(bare), 1, "the pinned env must not be empty")

    def test_agys_call_site_passes_the_truthful_isolate_value(self):
        """agy must declare what is TRUE, not default to `isolated=True` to match oc's call shape."""
        src = inspect.getsource(agy_runipd.execute_item)
        self.assertIn("if isolate:", src)
        self.assertIn(
            'driver_begin(repo, item["id6"], actor, isolated=True)',
            src,
            "the isolated branch must declare the lane baseline",
        )
        self.assertIn(
            'driver_begin(repo, item["id6"], actor)',
            src,
            "the non-isolated branch must keep the exact pre-existing three-argument call shape",
        )
        # The value must come from the run's own isolation flag, not a literal.
        self.assertIn(
            'isolate = state.get("options", {}).get("isolate_worktree", True)', src
        )

    def test_begin_still_runs_before_the_lane_is_allocated_on_both_hosts(self):
        """Fail-closed ordering (authority BEFORE side effects) must survive the unification.

        This is why the isolated baseline is a frozen base COMMIT rather than a path: at begin time the
        lane does not exist yet. Previously asserted for oc only.
        """
        for host_name, host in BOTH:
            with self.subTest(host=host_name):
                src = inspect.getsource(host)
                self.assertLess(
                    src.index("begin_rc, begin_msg = driver_begin("),
                    src.index("allocate_isolation_worktree("),
                    f"{host_name}: begin must still run before the lane is allocated",
                )


class NonVacuityControlTests(unittest.TestCase):
    """Property 5: remove each capability from a REPLICA and show the matching assertion FAILS.

    A capability test that would also pass against a reader LACKING the capability proves nothing. Each
    control below is a deliberately crippled variant of the shared body, run over the same fixtures.
    `ControlFidelityTests` holds the replicas to the real body, so a control cannot drift into testing
    a strawman that stopped resembling the code.
    """

    @staticmethod
    def _reader(
        keys: tuple[str, ...],
        nests: tuple[str, ...],
        *,
        prefer_ses: bool,
    ) -> Callable[[Path], str | None]:
        def read(log_path: Path) -> str | None:
            if not log_path.exists():
                return None
            fallback: str | None = None
            with log_path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(event, dict):
                        continue
                    scopes = [event]
                    for nest in nests:
                        nested = event.get(nest)
                        if isinstance(nested, dict):
                            scopes.append(nested)
                    for scope in scopes:
                        for key in keys:
                            value = scope.get(key)
                            if not isinstance(value, str) or not value.strip():
                                continue
                            if prefer_ses and value.startswith(_SES):
                                return value
                            if not prefer_ses:
                                return value
                            if fallback is None:
                                fallback = value
            return fallback

        return read

    def test_control_a_dropping_conversation_id_breaks_the_agy_shape(self):
        """Control (a): without `conversation_id`, an agy-shaped log FAILS to resolve."""
        crippled = self._reader(
            ("sessionID", "sessionId", "session_id"),
            runner_shared._SESSION_ID_NESTS,
            prefer_ses=True,
        )
        log = _log({"type": "result", "conversation_id": "conv-flat-1"})
        self.assertIsNone(crippled(log), "the control must really be crippled")
        # RESTORED: the real reader still resolves it.
        self.assertEqual(runner_shared.extract_session_id(log), "conv-flat-1")

    def test_control_b_dropping_the_ses_preference_breaks_the_mixed_case(self):
        """Control (b): first-hit discipline returns the WRONG value on the mixed log."""
        crippled = self._reader(
            runner_shared._SESSION_ID_KEYS,
            runner_shared._SESSION_ID_NESTS,
            prefer_ses=False,
        )
        log = _log({"sessionID": "raw-provider-id"}, {"sessionID": _SES + "real1"})
        self.assertEqual(crippled(log), "raw-provider-id")
        self.assertEqual(
            runner_shared.extract_session_id(log),
            _SES + "real1",
            "the real reader must prefer the prefixed value",
        )

    def test_control_c_dropping_the_result_nesting_breaks_the_nested_shape(self):
        """Control (c): without the `result` nesting, agy's real observed shape FAILS."""
        crippled = self._reader(
            runner_shared._SESSION_ID_KEYS, ("init",), prefer_ses=True
        )
        log = _log({"type": "result", "result": {"conversation_id": "conv-nested-1"}})
        self.assertIsNone(crippled(log))
        self.assertEqual(runner_shared.extract_session_id(log), "conv-nested-1")

    def test_control_d_dropping_the_init_nesting_breaks_the_retained_shape(self):
        """The `init` path is UNOBSERVED and retained on purpose, so its control is worth having."""
        crippled = self._reader(
            runner_shared._SESSION_ID_KEYS, ("result",), prefer_ses=True
        )
        log = _log({"type": "init", "init": {"conversation_id": "conv-init-1"}})
        self.assertIsNone(crippled(log))
        self.assertEqual(runner_shared.extract_session_id(log), "conv-init-1")


class ControlFidelityTests(unittest.TestCase):
    """Guard the controls: a replica that stopped resembling the real body proves nothing.

    The controls above re-implement the shared reader in order to cripple it. That is only legitimate
    while the replica matches the real thing on the UNCRIPPLED inputs, so this class asserts the
    full-capability replica agrees with the real function across every shape the suite uses.
    """

    def test_the_uncrippled_replica_agrees_with_the_real_reader(self):
        replica = NonVacuityControlTests._reader(
            runner_shared._SESSION_ID_KEYS,
            runner_shared._SESSION_ID_NESTS,
            prefer_ses=True,
        )
        fixtures = [
            _log({"sessionID": _SES + "a"}),
            _log({"conversation_id": "conv-b"}),
            _log({"result": {"conversation_id": "conv-c"}}),
            _log({"init": {"session_id": "sn-d"}}),
            _log({"sessionID": "raw-e"}, {"sessionID": _SES + "f"}),
            _log({"conversation_id": "conv-early"}, {"sessionID": _SES + "late"}),
            _log({"type": "text"}),
        ]
        for log in fixtures:
            with self.subTest(log=log.parent.name):
                self.assertEqual(
                    replica(log),
                    runner_shared.extract_session_id(log),
                    "the control replica has drifted from the real body; the controls above are no "
                    "longer evidence about the real reader",
                )

    def test_the_pre_union_oc_replica_matches_the_shipped_body_it_reconstructs(self):
        """The oc replica used by `AgyWireFormatTests` must behave like the real pre-union oc reader.

        Verified against the SHIPPED body at the execution HEAD rather than against memory: if that
        commit is unreachable (a shallow clone) this skips, because the claim is historical.
        """
        import subprocess as sp

        head = "1171f7b22da8065390f190458070a0ad842c2376"
        repo_root = Path(__file__).resolve().parents[1]
        proc = sp.run(
            ["git", "show", f"{head}:agent_workflows/oc_runipd.py"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,  # a missing commit is handled by the skip below, not by an exception
            stdin=sp.DEVNULL,
        )
        if proc.returncode != 0:
            self.skipTest(f"execution HEAD {head[:8]} not reachable in this clone")
        # `exec` on TWO hand-picked AST nodes (one assignment, one function def) taken from a FIXED
        # commit's `oc_runipd.py`, into a private namespace. Deliberate and narrow: the point is to run
        # the SHIPPED pre-union body rather than a hand-copy of it, because a hand-copy is exactly what
        # `_oc_pre_union_reader` already is and this test exists to verify THAT copy is faithful. Nothing
        # here reads untrusted input: the source comes from this repository's own git object store at a
        # pinned SHA. `# noqa: S102` is scoped to the two exec lines below, not to the file.
        namespace: dict[str, object] = {"json": json, "Path": Path}
        tree = ast.parse(proc.stdout)
        wanted = {"extract_session_id"}
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "_SESSION_ID_KEYS"
                for t in node.targets
            ):
                exec(compile(ast.Module([node], []), "<pre>", "exec"), namespace)  # noqa: S102
            if isinstance(node, ast.FunctionDef) and node.name in wanted:
                exec(compile(ast.Module([node], []), "<pre>", "exec"), namespace)  # noqa: S102
        real_pre_union = namespace.get("extract_session_id")
        if not callable(
            real_pre_union
        ):  # pragma: no cover - a load failure, not an assertion
            self.fail("could not load the pre-union oc reader from git history")
        self.assertEqual(
            namespace.get("_SESSION_ID_KEYS"),
            _OC_PRE_UNION_KEYS,
            "this file's reconstruction of oc's pre-union key list is wrong",
        )
        for log in (
            _log({"conversation_id": "conv-x"}),
            _log({"result": {"conversation_id": "conv-y"}}),
            _log({"sessionID": _SES + "z"}),
            _log({"sessionID": "raw"}, {"sessionID": _SES + "w"}),
        ):
            with self.subTest(log=log.parent.name):
                self.assertEqual(
                    _oc_pre_union_reader(log),
                    real_pre_union(log),
                    "the reconstructed oc reader disagrees with the body it claims to reconstruct",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

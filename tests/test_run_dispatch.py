"""Host-neutral `aw run as <profile>` / `aw run ipd <selector>` dispatch (runprofile-04, `ygzq71`).

WHAT THIS FILE FALSIFIES, in the plan's own terms:

* E-01/V-01 - the parser grew EXACTLY the two fixed entries `as` and `ipd`, no dynamic profile
  command or subcommand exists, and every pre-existing `aw run` / `aw runs` leaf still selects the
  handler it selected before.
* E-02/V-02 - the adapter registry derives the runner from the PROFILE for a named dispatch and from
  `default_runner` for an unqualified one, delegates to `oc_runipd.main` IN-PROCESS (no subprocess,
  no shell, no reconstructed prompt), returns the host's exit code unchanged, and REFUSES - before
  any host invocation - on an unknown profile, an absent default, a malformed store, or a runner
  with no adapter.
* E-03/V-03 - exact argv parity: `aw run as gem X` reaches `oc_runipd.main` with the same argv as
  `aw oc run as gem X`, `aw run ipd X` with the same argv as `aw oc run X`, and an explicit
  `--model`/`--variant`/`--agent` survives exactly ONCE.
* E-04/V-04 - the adversarial namespace matrix: profiles named `status`/`report`/`run`/`show`/
  `evidence`/`future-command` cannot shadow a command, and every prohibited spelling (`aw gem`,
  `aw gemrun`, `aw rungem`, `aw run gem`, `aw run-gem`, `aw run:gem`) does not exist.

METHOD, and why it is not a subprocess suite: every test drives the REAL `cli.main` in-process with
`oc_runipd.main` PATCHED, so an assertion is about the argv the router actually forwards rather than
about a message. `XDG_CONFIG_HOME` is redirected to a temp dir in `setUp`, so no test reads or writes
the developer's own `runner-profiles.json`, and every model identifier here is SYNTHETIC.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock

from agent_workflows import cli, run_dispatch, runner_profiles

#: Synthetic models only. A real provider/model identifier here would put the maintainer's
#: institutional topology into a tracked file, which is exactly what `runner_profiles` keeps the
#: store user-local to avoid.
GEM_MODEL = "synthetic/gemini-test"
SONNET_MODEL = "synthetic/sonnet-test"


def _cli(*argv: str) -> Tuple[int, str]:
    """Invoke the real CLI in-process, capturing stdout+stderr. Returns (rc, combined output)."""

    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(list(argv))
    except SystemExit as exc:  # argparse usage errors exit rather than return
        rc = int(exc.code or 0)
    return rc, out.getvalue() + err.getvalue()


class _ProfileStoreFixture(unittest.TestCase):
    """A temp XDG config home holding one synthetic profile store."""

    #: The store this fixture writes. Deliberately includes COMMAND-LIKE profile names, because the
    #: whole collision claim is that a name is only ever read after the literal `as` and therefore
    #: cannot shadow a real leaf. A store that contained only innocuous names would not test that.
    STORE: Dict[str, Any] = {
        "schema_version": 1,
        "default_runner": "oc",
        "defaults": {"profiles": {"oc": "gem"}},
        "profiles": {
            "gem": {"runner": "oc", "model": GEM_MODEL, "variant": "high"},
            "sonnet": {"runner": "oc", "model": SONNET_MODEL, "variant": "medium"},
            "status": {"runner": "oc", "model": SONNET_MODEL},
            "report": {"runner": "oc", "model": SONNET_MODEL},
            "run": {"runner": "oc", "model": SONNET_MODEL},
            "show": {"runner": "oc", "model": SONNET_MODEL},
            "evidence": {"runner": "oc", "model": SONNET_MODEL},
            "future-command": {"runner": "oc", "model": SONNET_MODEL},
        },
    }

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.xdg = Path(self._tmp.name) / "cfg"
        self._env = mock.patch.dict(
            os.environ, {"XDG_CONFIG_HOME": str(self.xdg), "NO_COLOR": "1"}
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        self.store_path = runner_profiles.store_path()
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.write_store(self.STORE)

    def write_store(self, document: Any) -> None:
        """Write the store BYTES directly (so a MALFORMED document can be written too)."""

        text = document if isinstance(document, str) else json.dumps(document, indent=2)
        self.store_path.write_text(text, encoding="utf-8")

    def remove_store(self) -> None:
        self.store_path.unlink(missing_ok=True)


class _HostSpyFixture(_ProfileStoreFixture):
    """Adds a spy over `oc_runipd.main`, so a test asserts the FORWARDED ARGV, not a message."""

    def setUp(self) -> None:
        super().setUp()
        self.calls: List[List[str]] = []

    def spy(self, returncode: int = 0):
        """Patch `oc_runipd.main` to record argv and return `returncode` without running."""

        def _fake_main(argv: Optional[List[str]] = None) -> int:
            self.calls.append(list(argv or []))
            return returncode

        return mock.patch("agent_workflows.oc_runipd.main", side_effect=_fake_main)

    def forwarded(self, *argv: str, returncode: int = 0) -> Tuple[int, List[List[str]]]:
        """Run `aw <argv>` with the host spied; return (rc, the argv lists it received)."""

        self.calls = []
        with self.spy(returncode=returncode):
            rc, _out = _cli(*argv)
        return rc, list(self.calls)


# ==================================================================================================
# E-01 / V-01: the parser grew EXACTLY two fixed entries
# ==================================================================================================


class FixedGrammarRegistrationTests(unittest.TestCase):
    """V-01: only `as` and `ipd` were added; no dynamic profile command exists."""

    #: The four ledger WRITE leaves `aw run` owned before this plan (`0soncw` E-03), which must all
    #: still be present and still route to the ledger.
    LEDGER_WRITERS = ("start", "record", "cancel", "finalize")

    def _run_choices(self) -> Dict[str, Any]:
        import argparse

        parser = cli._build_parser()
        top = next(
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        )
        run_parser = top.choices["run"]
        run_sub = next(
            a for a in run_parser._actions if isinstance(a, argparse._SubParsersAction)
        )
        return dict(run_sub.choices)

    def test_run_family_is_exactly_the_writers_plus_the_two_fixed_routes(self) -> None:
        self.assertEqual(
            set(self._run_choices()),
            set(self.LEDGER_WRITERS) | {"as", "ipd"},
            "the `aw run` surface changed; only the fixed `as`/`ipd` routes may be added",
        )

    def test_no_profile_name_became_a_command_or_subcommand(self) -> None:
        """The store is never consulted to BUILD the parser, so no name can become a command."""

        import argparse

        parser = cli._build_parser()
        top = next(
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        )
        for forbidden in ("gem", "sonnet", "gemrun", "rungem", "run-gem", "run:gem"):
            self.assertNotIn(
                forbidden, top.choices, f"`aw {forbidden}` must not be a command"
            )
            self.assertNotIn(
                forbidden,
                self._run_choices(),
                f"`aw run {forbidden}` must not be a subcommand",
            )

    def test_the_two_routes_declare_no_flags_of_their_own(self) -> None:
        """They capture REMAINDER, so the HOST parser owns every flag (`oc runipd`'s mechanism)."""

        import argparse

        for token in ("as", "ipd"):
            route = self._run_choices()[token]
            flags = [opt for action in route._actions for opt in action.option_strings]
            self.assertEqual(
                flags,
                [],
                f"`aw run {token}` must declare no flags of its own, got {flags}",
            )
            remainder = [a for a in route._actions if a.nargs == argparse.REMAINDER]
            self.assertEqual(
                len(remainder),
                1,
                f"`aw run {token}` must capture exactly one REMAINDER",
            )

    def test_route_table_is_the_single_source_of_the_two_tokens(self) -> None:
        """`cli` registers from `run_dispatch.ROUTES`, so a third spelling cannot be half-added."""

        self.assertEqual(set(run_dispatch.ROUTES), {"as", "ipd"})
        self.assertEqual(run_dispatch.AS_TOKEN, "as")
        self.assertEqual(run_dispatch.IPD_TOKEN, "ipd")

    def test_both_routes_are_declared_in_the_command_surface_inventory(self) -> None:
        """A new parser leaf must carry a contract declaration (the repo-wide CI gate)."""

        from agent_workflows.command_surface import get_declaration

        for leaf in ("run as", "run ipd"):
            decl = get_declaration(leaf)
            self.assertIsNotNone(decl, f"{leaf} carries no CommandDeclaration")
            assert decl is not None  # narrow for type-checkers
            # A dispatch route LAUNCHES a run, which commits and writes durable state, so it is a
            # mutation exactly as `oc runipd` is - not a read.
            self.assertEqual(decl.command_class, "mutation")
            self.assertIn(2, decl.exit_contract, "a refusal must be a declared exit")


class ProfileParsedAsDataNotGrammarTests(_HostSpyFixture):
    """V-01: `aw run as status X` names the PROFILE `status`; `aw runs status X` is the leaf."""

    def test_as_status_is_a_profile_and_runs_status_is_the_leaf(self) -> None:
        rc, calls = self.forwarded("run", "as", "status", "SEL")
        self.assertEqual(rc, 0)
        self.assertEqual(
            calls,
            [["as", "status", "SEL"]],
            "`aw run as status SEL` must forward `status` as the PROFILE NAME",
        )

        # The real `status` VIEWER leaf lives on the reading noun (`0soncw` E-03) and must not have
        # been touched: it reaches its ledger handler, never the host runner.
        self.calls = []
        with self.spy():
            rc_leaf, out_leaf = _cli("runs", "status", "no-such-run-id")
        self.assertEqual(
            self.calls, [], "`aw runs status` must not reach the host runner"
        )
        self.assertNotEqual(rc_leaf, 0, out_leaf)

    def test_every_command_like_profile_name_is_reachable_after_as(self) -> None:
        for name in ("status", "report", "run", "show", "evidence", "future-command"):
            with self.subTest(profile=name):
                rc, calls = self.forwarded("run", "as", name, "SEL")
                self.assertEqual(rc, 0)
                self.assertEqual(calls, [["as", name, "SEL"]])


# ==================================================================================================
# E-02 / V-02: the adapter registry, runner derivation, and fail-closed refusals
# ==================================================================================================


class AdapterRegistryTests(_ProfileStoreFixture):
    """V-02: runner derivation and the registry seam, tested at the function level."""

    def test_named_dispatch_derives_the_runner_from_the_profile(self) -> None:
        self.assertEqual(run_dispatch.resolve_named_runner("gem"), "oc")

    def test_default_dispatch_uses_the_configured_default_runner(self) -> None:
        self.assertEqual(run_dispatch.resolve_default_runner(), "oc")

    def test_only_oc_is_registered_in_version_1(self) -> None:
        self.assertEqual(run_dispatch.registered_runners(), ["oc"])

    def test_the_registry_matches_the_shared_schema_runner_registry(self) -> None:
        """Every adapter must name a runner the SCHEMA accepts; no adapter may invent a host."""

        for name in run_dispatch.RUNNER_ADAPTERS:
            self.assertIn(name, runner_profiles.RUNNER_REGISTRY)

    def test_the_opencode_adapter_delegates_to_oc_runipd_main(self) -> None:
        """No subprocess, no shell, no rebuilt prompt: the driver's own parser is called directly."""

        with mock.patch("agent_workflows.oc_runipd.main", return_value=7) as m:
            rc = run_dispatch.RUNNER_ADAPTERS["oc"](["as", "gem", "SEL"])
        self.assertEqual(rc, 7, "the host's exit code must be returned unchanged")
        m.assert_called_once_with(["as", "gem", "SEL"])

    def test_the_adapter_uses_no_subprocess_or_shell(self) -> None:
        """Structural proof, so a later 'simplification' to a shell call fails this file.

        Asserted over the module's CODE, not its raw text: the docstring legitimately mentions
        "subprocess" while PROMISING not to use one, and a naive substring scan over the source
        would fail on that promise (measured). Walking the AST for real Import/Attribute/keyword
        nodes tests the behavior the promise is about.
        """

        import ast
        import inspect

        tree = ast.parse(inspect.getsource(run_dispatch))
        imported: set[str] = set()
        attributes: set[str] = set()
        shell_true = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
            elif isinstance(node, ast.Name):
                attributes.add(node.id)
            elif isinstance(node, ast.keyword) and node.arg == "shell":
                shell_true = True

        for banned in ("subprocess", "os", "shlex", "pty"):
            self.assertNotIn(
                banned, imported, f"run_dispatch must not import {banned!r}"
            )
        for banned in ("system", "Popen", "run", "spawn", "execv", "fork"):
            self.assertNotIn(
                banned, attributes, f"run_dispatch must not reference {banned!r}"
            )
        self.assertFalse(shell_true, "run_dispatch must pass no `shell=` keyword")

    def test_alias_runner_name_is_canonicalized_not_rejected(self) -> None:
        """`opencode` is an ALIAS of `oc` in the shared schema, so it must resolve, not refuse."""

        self.assertIs(
            run_dispatch.adapter_for("opencode"), run_dispatch.RUNNER_ADAPTERS["oc"]
        )

    def test_an_unknown_runner_refuses_and_names_the_registered_ones(self) -> None:
        with self.assertRaises(run_dispatch.RunDispatchError) as ctx:
            run_dispatch.adapter_for("no-such-host")
        self.assertIn("oc", str(ctx.exception))

    def test_a_registered_but_unimplemented_runner_is_a_distinct_refusal(self) -> None:
        """'known runner, no adapter' must not be reported as 'not a runner': different fixes.

        Uses a FICTIONAL host rather than the real `agy` row: `hostdefault-01` registered `agy` in
        the schema, so patching that key would SHADOW shipped data instead of adding a hypothetical
        host, and this test's job is the hypothetical case that recurs at every future host. The
        real `agy` refusal is covered separately (both dispatch routes, in the e2e suite).
        """

        spec = runner_profiles.RunnerSpec(
            name="futurehost",
            aliases=(),
            supports_variant=True,
            supports_agent=False,
            validate_default=False,
        )
        with mock.patch.dict(
            runner_profiles.RUNNER_REGISTRY, {"futurehost": spec}, clear=False
        ):
            with self.assertRaises(run_dispatch.RunDispatchError) as ctx:
                run_dispatch.adapter_for("futurehost")
        message = str(ctx.exception)
        self.assertIn("no dispatch adapter", message)
        self.assertNotIn("is not a registered runner", message)


class FailClosedRefusalTests(_HostSpyFixture):
    """V-02: every misconfiguration refuses with exit 2 and NEVER invokes a host."""

    def _refuses(self, *argv: str) -> str:
        self.calls = []
        with self.spy():
            rc, out = _cli(*argv)
        self.assertEqual(rc, run_dispatch.EXIT_CANNOT_RUN, out)
        self.assertEqual(
            self.calls, [], f"`aw {' '.join(argv)}` invoked the host before refusing"
        )
        return out

    def test_unknown_profile_refuses_and_names_the_creation_command(self) -> None:
        out = self._refuses("run", "as", "nope", "SEL")
        self.assertIn("no runner profile named 'nope'", out)
        self.assertIn("aw oc profile add nope", out)

    def test_absent_default_runner_refuses_rather_than_guessing_a_host(self) -> None:
        store = json.loads(json.dumps(self.STORE))
        store.pop("default_runner")
        self.write_store(store)
        out = self._refuses("run", "ipd", "SEL")
        self.assertIn("default_runner", out)
        self.assertIn("does not guess", out)

    def test_absent_store_refuses_for_both_routes(self) -> None:
        self.remove_store()
        self._refuses("run", "as", "gem", "SEL")
        self._refuses("run", "ipd", "SEL")

    def test_malformed_store_refuses_instead_of_degrading_to_empty(self) -> None:
        """Degrading to empty would silently launch the HOST DEFAULT model (runner_profiles' rule)."""

        self.write_store("{ this is not json")
        self._refuses("run", "as", "gem", "SEL")
        self._refuses("run", "ipd", "SEL")

    def test_unsupported_schema_version_refuses(self) -> None:
        store = json.loads(json.dumps(self.STORE))
        store["schema_version"] = 99
        self.write_store(store)
        self._refuses("run", "ipd", "SEL")

    def test_a_profile_whose_runner_has_no_adapter_refuses(self) -> None:
        # A FICTIONAL host, for the reason given on the adapter-registry twin of this test: the
        # real `agy` row now ships, so patching that key would shadow real data rather than
        # simulate the next host. What this pins is that a profile naming a schema-valid host with
        # no adapter refuses fail-closed WITHOUT launching any driver, whichever host that is.
        spec = runner_profiles.RunnerSpec(
            name="futurehost",
            aliases=(),
            supports_variant=True,
            supports_agent=False,
            validate_default=False,
        )
        store = json.loads(json.dumps(self.STORE))
        store["profiles"]["future"] = {"runner": "futurehost", "model": SONNET_MODEL}
        with mock.patch.dict(
            runner_profiles.RUNNER_REGISTRY, {"futurehost": spec}, clear=False
        ):
            self.write_store(store)
            out = self._refuses("run", "as", "future", "SEL")
        self.assertIn("no dispatch adapter", out)

    def test_the_real_agy_row_refuses_on_both_routes_without_launching(self) -> None:
        """`hostdefault-01` E-04: the registered-but-unimplemented refusal for the REAL second row.

        Registering `agy` in the schema made two new store states WRITABLE that no adapter can
        launch: a profile whose `runner` is `agy`, and `default_runner: agy` (which the UNQUALIFIED
        `aw run ipd` route reaches with no profile named at all). Both must refuse fail-closed,
        because the whole point of the row is to record that host's verification posture, NOT to
        make `aw run` reach it. No `mock.patch.dict` here: this is shipped data.
        """

        store = json.loads(json.dumps(self.STORE))
        store["profiles"]["gg"] = {"runner": "agy", "model": SONNET_MODEL}
        store["default_runner"] = "agy"
        self.write_store(store)
        for argv in (("run", "as", "gg", "SEL"), ("run", "ipd", "SEL")):
            with self.subTest(route=" ".join(argv)):
                out = self._refuses(*argv)
                self.assertIn("no dispatch adapter", out)
                self.assertIn("'agy'", out)
                self.assertIn("oc", out)

    def test_as_without_a_profile_name_refuses(self) -> None:
        out = self._refuses("run", "as")
        self.assertIn("requires a profile name", out)

    def test_as_followed_by_an_option_refuses_rather_than_treating_it_as_a_name(
        self,
    ) -> None:
        """`aw run as --model X SEL` has no profile; consuming `--model` as one would be silent."""

        out = self._refuses("run", "as", "--model", GEM_MODEL, "SEL")
        self.assertIn("requires a profile name", out)

    def test_route_help_is_answerable_without_any_configuration(self) -> None:
        """`--help` must never fail closed just because `default_runner` is unset."""

        self.remove_store()
        for argv in (("run", "as", "--help"), ("run", "ipd", "--help")):
            with self.subTest(argv=argv):
                self.calls = []
                with self.spy():
                    rc, out = _cli(*argv)
                self.assertEqual(rc, 0, out)
                self.assertEqual(self.calls, [], "route help must not invoke a host")
                self.assertIn("aw run as <profile>", out)


# ==================================================================================================
# E-03 / V-03: exact argv parity with the host-specific spelling
# ==================================================================================================


class HostParityTests(_HostSpyFixture):
    """V-03: the generic route adds NO behavioral layer beyond runner/profile selection."""

    def test_named_route_argv_equals_the_host_specific_spelling(self) -> None:
        _rc_a, generic = self.forwarded("run", "as", "gem", "SEL")
        _rc_b, host = self.forwarded("oc", "run", "as", "gem", "SEL")
        self.assertEqual(generic, host, "`aw run as gem SEL` != `aw oc run as gem SEL`")
        self.assertEqual(generic, [["as", "gem", "SEL"]])

    def test_named_route_parity_holds_for_the_long_host_spelling_too(self) -> None:
        _rc_a, generic = self.forwarded("run", "as", "gem", "SEL")
        _rc_b, host = self.forwarded("opencode", "runipd", "as", "gem", "SEL")
        self.assertEqual(generic, host)

    def test_default_route_argv_equals_the_unqualified_host_spelling(self) -> None:
        _rc_a, generic = self.forwarded("run", "ipd", "SEL")
        _rc_b, host = self.forwarded("oc", "run", "SEL")
        self.assertEqual(generic, host, "`aw run ipd SEL` != `aw oc run SEL`")
        self.assertEqual(generic, [["SEL"]])

    def test_default_route_forwards_no_as_clause(self) -> None:
        """The HOST applies its per-runner default profile; the router must not inject one."""

        _rc, calls = self.forwarded("run", "ipd", "SEL")
        self.assertNotIn(
            "as", calls[0], "the default route must not synthesize an `as` clause"
        )

    def test_explicit_overrides_survive_exactly_once(self) -> None:
        for flag, value in (
            ("--model", SONNET_MODEL),
            ("--variant", "low"),
            ("--agent", "build"),
        ):
            with self.subTest(flag=flag):
                _rc, calls = self.forwarded("run", "as", "gem", "SEL", flag, value)
                self.assertEqual(len(calls), 1)
                argv = calls[0]
                self.assertEqual(
                    argv.count(flag), 1, f"{flag} appears {argv.count(flag)} times"
                )
                self.assertEqual(argv.count(value), 1)
                self.assertEqual(argv, ["as", "gem", "SEL", flag, value])

    def test_all_three_overrides_together_survive_exactly_once(self) -> None:
        _rc, calls = self.forwarded(
            "run",
            "as",
            "gem",
            "SEL",
            "--model",
            SONNET_MODEL,
            "--variant",
            "low",
            "--agent",
            "build",
        )
        _rc2, host = self.forwarded(
            "oc",
            "run",
            "as",
            "gem",
            "SEL",
            "--model",
            SONNET_MODEL,
            "--variant",
            "low",
            "--agent",
            "build",
        )
        self.assertEqual(calls, host)
        for token in ("--model", "--variant", "--agent", SONNET_MODEL, "low", "build"):
            self.assertEqual(calls[0].count(token), 1, f"{token} duplicated")

    def test_a_leading_option_is_forwarded_not_rejected(self) -> None:
        """REMAINDER cannot capture a LEADING option, so flag POSITION must not matter."""

        _rc_a, leading = self.forwarded("run", "ipd", "--prepare-only", "SEL")
        _rc_b, trailing = self.forwarded("run", "ipd", "SEL", "--prepare-only")
        self.assertEqual(leading, [["--prepare-only", "SEL"]])
        self.assertEqual(trailing, [["SEL", "--prepare-only"]])
        _rc_c, host = self.forwarded("oc", "run", "--prepare-only", "SEL")
        self.assertEqual(leading, host)

    def test_the_host_exit_code_is_returned_unchanged(self) -> None:
        for code in (0, 1, 2, 3, 130):
            with self.subTest(code=code):
                rc, _calls = self.forwarded("run", "as", "gem", "SEL", returncode=code)
                self.assertEqual(rc, code)
                rc_default, _c = self.forwarded("run", "ipd", "SEL", returncode=code)
                self.assertEqual(rc_default, code)

    def test_host_help_after_a_profile_is_the_hosts_not_the_routes(self) -> None:
        """`aw run as gem --help` must reach the DRIVER, byte-identical to the host spelling."""

        _rc_a, generic = self.forwarded("run", "as", "gem", "--help")
        _rc_b, host = self.forwarded("oc", "run", "as", "gem", "--help")
        self.assertEqual(generic, host)
        self.assertEqual(generic, [["as", "gem", "--help"]])

    def test_the_double_dash_escape_reaches_the_host_intact(self) -> None:
        """`--` is the driver's literal-selector escape; the router must not consume it."""

        _rc, calls = self.forwarded("run", "ipd", "--", "as")
        self.assertEqual(calls, [["--", "as"]])

    def test_both_entry_paths_produce_identical_argv(self) -> None:
        """The pre-parse interception and the parsed-namespace branch must not diverge."""

        self.calls = []
        with self.spy():
            rc_pre = cli._dispatch(["run", "as", "gem", "SEL"])
        pre = list(self.calls)

        parser = cli._build_parser()
        args = parser.parse_args(["run", "as", "gem", "SEL"])
        self.calls = []
        with self.spy():
            rc_ns = run_dispatch.dispatch(args.run_command, list(args.dispatch_args))
        namespace = list(self.calls)

        self.assertEqual(rc_pre, rc_ns)
        self.assertEqual(pre, namespace)


# ==================================================================================================
# E-04 / V-04: the adversarial namespace matrix
# ==================================================================================================


class LedgerRoutingUnchangedTests(_HostSpyFixture):
    """V-04: every pre-existing run-family leaf still selects its ORIGINAL handler."""

    #: The post-`0soncw` split, which is the CURRENT truth this plan must preserve: `aw run` WRITES,
    #: `aw runs` READS. The plan text predates that split and names `status`/`show`/`evidence`/
    #: `verify-ledger` under `aw run`; they are asserted under their real noun here, and their
    #: REJECTION under `aw run` is asserted separately below.
    WRITERS = ("start", "record", "cancel", "finalize")
    VIEWERS = (
        "show",
        "status",
        "list",
        "next",
        "resume",
        "decisions",
        "questions",
        "evidence",
        "verify-ledger",
    )

    def test_no_ledger_leaf_reaches_the_host_runner(self) -> None:
        for leaf in self.WRITERS:
            with self.subTest(noun="run", leaf=leaf):
                self.calls = []
                with self.spy():
                    _cli("run", leaf, "no-such-target")
                self.assertEqual(
                    self.calls, [], f"`aw run {leaf}` reached the host runner"
                )
        for leaf in self.VIEWERS:
            with self.subTest(noun="runs", leaf=leaf):
                self.calls = []
                with self.spy():
                    _cli("runs", leaf, "no-such-target")
                self.assertEqual(
                    self.calls, [], f"`aw runs {leaf}` reached the host runner"
                )

    def test_writer_leaves_still_select_the_ledger_dispatcher(self) -> None:
        """Proven by WHERE the call lands, not by an exit code: `run_cli.run_cli` must be entered."""

        for leaf in self.WRITERS:
            with self.subTest(leaf=leaf):
                with mock.patch("agent_workflows.run_cli.run_cli", return_value=0) as m:
                    rc, out = _cli("run", leaf, "no-such-target")
                self.assertEqual(rc, 0, out)
                m.assert_called_once()
                self.assertEqual(
                    getattr(m.call_args[0][0], "run_command"),
                    leaf,
                    f"`aw run {leaf}` did not reach the ledger dispatcher as {leaf!r}",
                )

    def test_viewer_leaves_still_select_the_ledger_dispatcher(self) -> None:
        for leaf in self.VIEWERS:
            if leaf == "list":
                continue  # `list` is the VIEWER table, routed to run_viewer (0soncw E-04)
            with self.subTest(leaf=leaf):
                with mock.patch("agent_workflows.run_cli.run_cli", return_value=0) as m:
                    rc, out = _cli("runs", leaf, "no-such-target")
                self.assertEqual(rc, 0, out)
                m.assert_called_once()

    def test_bare_run_still_shows_family_help_not_a_dispatch(self) -> None:
        self.calls = []
        with self.spy():
            rc, out = _cli("run")
        self.assertEqual(self.calls, [])
        self.assertIn("start", out)
        self.assertIn("finalize", out)

    def test_the_moved_viewer_leaves_are_still_rejected_under_aw_run(self) -> None:
        """`0soncw`'s rejection must survive: `as`/`ipd` must not resurrect them by accident."""

        for leaf in ("show", "status", "evidence", "verify-ledger"):
            with self.subTest(leaf=leaf):
                self.calls = []
                with self.spy():
                    rc, out = _cli("run", leaf, "no-such-target")
                self.assertNotEqual(rc, 0, out)
                self.assertIn("invalid choice", out)
                self.assertEqual(self.calls, [])


class ProhibitedSpellingTests(_HostSpyFixture):
    """V-04: terseness must not be bought with command namespace or unknown-token inference."""

    #: Every spelling the plan's findings table PROHIBITS. Each must fail, and none may reach a host.
    #:
    #: `("status",)` is deliberately ABSENT even though a profile of that name exists in the fixture:
    #: `aw status` is a REAL command that must keep succeeding, so demanding failure here would be
    #: wrong. The claim about it is different in kind - the profile must not CAPTURE it - and is
    #: asserted by `test_aw_status_is_still_the_real_status_command` below.
    PROHIBITED: Tuple[Tuple[str, ...], ...] = (
        ("gem",),  # aw gem
        ("gemrun",),  # aw gemrun
        ("rungem",),  # aw rungem
        ("run-gem",),  # aw run-gem
        ("run:gem",),  # aw run:gem
        ("run", "gem"),  # aw run gem (bare unknown token under the run noun)
        ("run", "gem", "SEL"),
        (
            "run",
            "with",
            "gem",
            "SEL",
        ),  # alternate spellings are excluded; `as` is canonical
        ("run", "using", "gem", "SEL"),
        ("run", "w", "gem", "SEL"),
    )

    def test_every_prohibited_spelling_fails_and_invokes_no_host(self) -> None:
        for argv in self.PROHIBITED:
            with self.subTest(argv=" ".join(argv)):
                self.calls = []
                with self.spy():
                    rc, out = _cli(*argv)
                self.assertNotEqual(
                    rc, 0, f"`aw {' '.join(argv)}` must not succeed: {out}"
                )
                self.assertEqual(
                    self.calls,
                    [],
                    f"`aw {' '.join(argv)}` reached the host runner",
                )

    def test_aw_status_is_still_the_real_status_command(self) -> None:
        """A profile named `status` must not have shadowed the top-level verb."""

        self.calls = []
        with self.spy():
            rc, out = _cli("status")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.calls, [], "`aw status` reached the host runner")

    def test_a_future_run_subcommand_name_is_not_reinterpreted_as_a_selector(
        self,
    ) -> None:
        """Bare `aw run <unknown>` must REFUSE, so adding a future verb breaks nothing silently."""

        self.calls = []
        with self.spy():
            rc, out = _cli("run", "future-command")
        self.assertNotEqual(rc, 0)
        self.assertIn("invalid choice", out)
        self.assertEqual(self.calls, [])


class SelectorAmbiguityTests(_HostSpyFixture):
    """V-04: a token that LOOKS like a profile is still a selector when no `as` precedes it."""

    def test_gem_under_run_ipd_stays_a_selector(self) -> None:
        _rc, calls = self.forwarded("run", "ipd", "gem")
        self.assertEqual(
            calls,
            [["gem"]],
            "`aw run ipd gem` must forward `gem` as a SELECTOR, never as a profile",
        )
        self.assertNotIn("as", calls[0])

    def test_gem_under_run_ipd_equals_the_host_spelling_with_the_same_selector(
        self,
    ) -> None:
        _rc_a, generic = self.forwarded("run", "ipd", "gem")
        _rc_b, host = self.forwarded("oc", "run", "gem")
        self.assertEqual(generic, host)

    def test_a_profile_named_as_is_impossible_by_schema(self) -> None:
        """`as` is a RESERVED name in the shared schema, so the grammar cannot be made ambiguous."""

        self.assertIn("as", runner_profiles.RESERVED_PROFILE_NAMES)
        with self.assertRaises(runner_profiles.RunnerProfileError):
            runner_profiles.validate_profile_name("as")

    def test_a_second_as_clause_is_refused_by_the_host_not_silently_accepted(
        self,
    ) -> None:
        """The router forwards; the DRIVER owns the misplaced-clause refusal (`3cm15q` E-01)."""

        rc, out = _cli("run", "as", "gem", "SEL", "as", "sonnet")
        self.assertEqual(rc, 2, out)
        self.assertIn("as", out)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

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

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: invoke one argv with
the host spied, then assert the exit code plus either the forwarded argv or the absence of any host
call. The class boundaries used to track WHICH CLAIM the plan's V-item made, which is a property of
the plan and not of the subject, so a store misconfiguration and a prohibited spelling - both of
which must exit 2 without launching anything - sat in different classes asserting the same thing two
different ways.

EXIT CODES ARE A COLUMN IN EVERY TABLE, and that is deliberate: `run_dispatch.EXIT_CANNOT_RUN` (2) is
consumed by machines, it is what `command_surface` declares as this route's refusal exit, and the
realistic failure is not one refusal breaking but a shared helper mapping a whole family of
conditions onto a different class. A table reports that as one failure naming every row whose class
moved; N tests report it as N red lines each saying `2 != 0`.

MODES ARE COLUMNS, NOT CLASSES. The ROUTE (`as` versus `ipd`), the HOST SPELLING being compared
against (`aw oc run` versus `aw opencode runipd`), the store STATE, the NOUN (`aw run` writes,
`aw runs` reads) and the host's own RETURN CODE are all columns. In every case the property worth
asserting is that the SAME claim holds across the mode, which no single-mode test can state.

HUMAN PROSE IS PINNED ONLY AS THE ONE IDENTIFYING PHRASE a user or an agent greps for (`no runner
profile named 'nope'`, `no dispatch adapter`, `requires a profile name`, `invalid choice`). Whole
sentences of refusal or help text are NOT asserted: they are not load-bearing, and pinning them
would make a reworded message a test failure.

Tests that are NOT rows carry a one-line docstring saying why they stay separate. The recurring
reasons: the claim is `assertRaises` over a typed exception rather than an exit code; the assertion
is STRUCTURAL (an AST walk over the module, a registry subset property); the setup is materially
different (the two entry paths called directly, the REAL driver invoked unspied).
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


#: A schema-valid host with NO dispatch adapter, used by the refusal table's `futurehost` rows. A
#: FICTIONAL host rather than the real `agy` row: `hostdefault-01` registered `agy` in the schema, so
#: patching that key would SHADOW shipped data instead of adding a hypothetical host. The real `agy`
#: refusal gets its own rows, with no patching at all.
FUTURE_SPEC = runner_profiles.RunnerSpec(
    name="futurehost",
    aliases=(),
    supports_variant=True,
    supports_agent=False,
    validate_default=False,
)


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

    def invoke(
        self, *argv: str, returncode: int = 0
    ) -> Tuple[int, str, List[List[str]]]:
        """Like `forwarded`, but also returns the combined output for needle checks."""

        self.calls = []
        with self.spy(returncode=returncode):
            rc, out = _cli(*argv)
        return rc, out, list(self.calls)


# ==================================================================================================
# E-01 / V-01: the parser grew EXACTLY two fixed entries
# ==================================================================================================


def _run_choices() -> Dict[str, Any]:
    """The `aw run` subparser's choice map, read from the REAL parser."""

    import argparse

    parser = cli._build_parser()
    top = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    run_parser = top.choices["run"]
    run_sub = next(
        a for a in run_parser._actions if isinstance(a, argparse._SubParsersAction)
    )
    return dict(run_sub.choices)


def _top_choices() -> Dict[str, Any]:
    """The top-level command choice map, read from the REAL parser."""

    import argparse

    parser = cli._build_parser()
    top = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    return dict(top.choices)


class FixedGrammarRegistrationTests(unittest.TestCase):
    """V-01: only `as` and `ipd` were added; no dynamic profile command exists.

    THREE TABLES replace five tests, each table grouping by the SUBJECT rather than by which
    assertion helper the old test reached for: the exact TOKEN SET (asserted at both layers that can
    disagree), the names that must NOT be grammar, and the per-route properties of the two leaves
    that were added.
    """

    #: The four ledger WRITE leaves `aw run` owned before this plan (`0soncw` E-03), which must all
    #: still be present and still route to the ledger.
    LEDGER_WRITERS = ("start", "record", "cancel", "finalize")

    #: (layer, why this row exists) - the two independent places the token set is declared. The
    #: EXPECTED set is identical for both rows by construction, which is the whole point.
    TOKEN_LAYERS = (
        (
            "the argparse subparser choices under `aw run`",
            "the OBSERVABLE surface: this is the set a user's shell completion and an agent's "
            "`--help` scrape actually see, so a leaf added here is a public grammar change even if "
            "no module constant moved",
        ),
        (
            "run_dispatch.ROUTES, the table `cli` registers from",
            "the SINGLE SOURCE: `cli` registers from this mapping, so a third spelling cannot be "
            "half-added. Both rows failing together means a route was added properly and is simply "
            "unwanted; only the FIRST failing means `cli` grew a leaf that bypasses the table, "
            "which is how a route ends up with no adapter behind it",
        ),
    )

    def test_the_route_token_set_is_exactly_as_and_ipd_at_every_layer(self) -> None:
        expected_run_family = set(self.LEDGER_WRITERS) | {"as", "ipd"}
        actual = {
            "the argparse subparser choices under `aw run`": set(_run_choices()),
            "run_dispatch.ROUTES, the table `cli` registers from": set(
                run_dispatch.ROUTES
            )
            | set(self.LEDGER_WRITERS),
        }
        wrong = []
        for layer, why in self.TOKEN_LAYERS:
            got = actual[layer]
            if got != expected_run_family:
                wrong.append(
                    f"  {layer}:\n"
                    f"    - unexpected token(s): {sorted(got - expected_run_family)!r}\n"
                    f"    - missing token(s):    {sorted(expected_run_family - got)!r}\n"
                    f"    this row exists because: {why}"
                )
        # The two token CONSTANTS are the spellings both layers above are built from, so a rename
        # there would make both rows pass against the wrong words.
        for name, constant, expected_token in (
            ("AS_TOKEN", run_dispatch.AS_TOKEN, "as"),
            ("IPD_TOKEN", run_dispatch.IPD_TOKEN, "ipd"),
        ):
            if constant != expected_token:
                wrong.append(
                    f"  run_dispatch.{name}:\n"
                    f"    - expected {expected_token!r}, got {constant!r}\n"
                    "    this row exists because: the constants are the spellings both layers are "
                    "built from, so renaming one silently renames the user-facing grammar while "
                    "every set comparison above still agrees with itself"
                )
        self.assertEqual(
            wrong,
            [],
            f"the `aw run` token set is wrong at {len(wrong)} of {len(self.TOKEN_LAYERS) + 2} "
            "declaration points. `as` and `ipd` are FIXED grammar and the four writers are "
            "`0soncw`'s surface, so ALL ROWS FAILING TOGETHER means a leaf was added or removed "
            "deliberately and this table is the record that says so; ONE row failing means the "
            "layers DISAGREE, which is the dangerous case: a parser leaf with no entry in `ROUTES` "
            "has no adapter behind it, and an entry in `ROUTES` with no parser leaf is unreachable. "
            "FIX: change the expectation here only together with the plan that widens the grammar, "
            f"never to make a stray leaf green.\n" + "\n".join(wrong),
        )

    #: (name, why this row exists) - names that must exist NOWHERE in the grammar, at either level.
    #: The store is never consulted to BUILD the parser, which is what makes this true for every
    #: profile name and not merely for these.
    FORBIDDEN_NAMES = (
        (
            "gem",
            "a PROFILE NAME present in the fixture store. If the parser were built from the store, "
            "this is the name that would appear, so it is the direct probe of the claim",
        ),
        (
            "sonnet",
            "a second stored profile, so the row above cannot pass by `gem` being special-cased",
        ),
        (
            "gemrun",
            "the concatenated spelling: terseness must not be bought by minting a command per host",
        ),
        (
            "rungem",
            "the reversed concatenation, which is the other half of the same temptation",
        ),
        (
            "run-gem",
            "the hyphenated spelling, which would read as a command rather than as data",
        ),
        (
            "run:gem",
            "the colon spelling. A separator character is still a NAME to argparse, so this is not "
            "excluded automatically by the ones above",
        ),
    )

    def test_no_name_that_must_not_be_grammar_became_grammar(self) -> None:
        top, run_sub = _top_choices(), _run_choices()
        wrong = []
        for name, why in self.FORBIDDEN_NAMES:
            problems = []
            if name in top:
                problems.append(f"`aw {name}` exists as a TOP-LEVEL command")
            if name in run_sub:
                problems.append(f"`aw run {name}` exists as a SUBCOMMAND")
            if problems:
                wrong.append(
                    f"  {name!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.FORBIDDEN_NAMES)} forbidden names became grammar. The store "
            "is never read to BUILD the parser, so a profile name CANNOT become a command; several "
            "rows failing together means the parser started consulting the store (or a profile "
            "loop now registers leaves), which makes the command namespace depend on a user-local "
            "file and lets a stored name shadow a future real command. FIX: registration must come "
            f"from `run_dispatch.ROUTES` alone, never from `runner_profiles`.\n"
            + "\n".join(wrong),
        )

    #: (token, the `command_surface` leaf name, why this row exists) - the per-route properties of
    #: the two leaves that WERE added. Four claims per row, accumulated: no flags of its own, exactly
    #: one REMAINDER, a CommandDeclaration exists, and that declaration says `mutation` with 2 among
    #: its exits.
    ROUTES = (
        (
            "as",
            "run as",
            "the NAMED route. It reads one positional (the profile) and must still own no flags, "
            "because the profile name is data and every flag belongs to the host parser",
        ),
        (
            "ipd",
            "run ipd",
            "the UNQUALIFIED route. It has no positional of its own at all, so if REMAINDER capture "
            "regressed here the first selector token would be eaten as an argparse error instead of "
            "being forwarded",
        ),
    )

    def test_each_added_route_owns_no_flags_and_declares_its_contract(self) -> None:
        import argparse

        from agent_workflows.command_surface import get_declaration

        choices = _run_choices()
        wrong = []
        for token, leaf, why in self.ROUTES:
            problems = []
            route = choices.get(token)
            if route is None:
                problems.append(f"`aw run {token}` is not registered at all")
            else:
                flags = [
                    opt for action in route._actions for opt in action.option_strings
                ]
                if flags:
                    problems.append(
                        f"declares flags of its own {flags!r}; the HOST parser must own every flag"
                    )
                remainder = [a for a in route._actions if a.nargs == argparse.REMAINDER]
                if len(remainder) != 1:
                    problems.append(
                        f"captures {len(remainder)} REMAINDER action(s), expected exactly 1"
                    )
            decl = get_declaration(leaf)
            if decl is None:
                problems.append(f"{leaf!r} carries no CommandDeclaration")
            else:
                # A dispatch route LAUNCHES a run, which commits and writes durable state, so it is
                # a mutation exactly as `oc runipd` is - not a read.
                if decl.command_class != "mutation":
                    problems.append(
                        f"declared command_class is {decl.command_class!r}, expected 'mutation'"
                    )
                if run_dispatch.EXIT_CANNOT_RUN not in decl.exit_contract:
                    problems.append(
                        f"exit_contract {tuple(decl.exit_contract)!r} omits "
                        f"{run_dispatch.EXIT_CANNOT_RUN} (EXIT_CANNOT_RUN); a refusal must be a "
                        "DECLARED exit"
                    )
            if problems:
                wrong.append(
                    f"  `aw run {token}`:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.ROUTES)} dispatch routes are wrongly declared. BOTH rows "
            "failing on the same problem means the shared registration helper changed, since the "
            "two leaves are built by one loop; ONE row failing means the two routes drifted apart, "
            "which is how `ipd` ends up parsing flags `as` forwards. FIX: a missing "
            "CommandDeclaration also fails the repo-wide CI gate, and an exit_contract omitting "
            f"{run_dispatch.EXIT_CANNOT_RUN} makes every fail-closed refusal an UNDECLARED exit "
            f"that machines cannot anticipate.\n" + "\n".join(wrong),
        )


# ==================================================================================================
# E-02 / V-02: the adapter registry, runner derivation, and fail-closed refusals
# ==================================================================================================


class AdapterRegistryTests(_ProfileStoreFixture):
    """V-02: runner derivation and the registry seam, tested at the function level.

    ONE table replaces four tests. Each asked ONE derivation or lookup function for ONE answer with
    the fixture store in place, and differed only in which function and which expected value. The
    table beats the four because these functions are the whole of the selection policy - which host
    a dispatch reaches - and the realistic failure is the derivation ORDER changing (a named
    dispatch falling back to `default_runner`, or an alias stopping resolving) rather than one
    function breaking alone. Four tests report that as four unrelated red lines; the table reports
    which answers moved, together.

    The `assertRaises` refusals and the two STRUCTURAL guards below are deliberately NOT rows: an
    exception's TYPE and an AST walk are different kinds of claim, and folding them in would mean
    every row carrying an unused `expect_raises` column.
    """

    #: (case, a zero-arg probe returning the answer, the expected answer, why this row exists)
    #:
    #: Probes are callables rather than a name+args pair because the four functions have four
    #: different signatures; a uniform table would have had to invent a dispatch layer of its own.
    DERIVATIONS = (
        (
            "resolve_named_runner('gem') for a profile whose runner is oc",
            lambda: run_dispatch.resolve_named_runner("gem"),
            "oc",
            "A NAMED dispatch derives the host from the PROFILE, never from `default_runner`. If "
            "this ever read the default, `aw run as <profile>` would silently launch a host the "
            "profile does not name, which is the one thing naming a profile is for",
        ),
        (
            "resolve_default_runner() with default_runner: oc configured",
            lambda: run_dispatch.resolve_default_runner(),
            "oc",
            "the UNQUALIFIED route derives the host from `default_runner` alone. The mirror of the "
            "row above: together they state that the two routes read DIFFERENT fields, which is "
            "what one test per function cannot say",
        ),
        (
            "registered_runners() in version 1",
            lambda: run_dispatch.registered_runners(),
            ["oc"],
            "the adapter set is a CLOSED, ORDERED list this build can actually launch, and it is "
            "printed verbatim in the no-adapter refusal. `agy` is in the schema REGISTRY but "
            "deliberately absent here, so a row appearing means a host became launchable without "
            "its verification posture being recorded",
        ),
        (
            "adapter_for('oc'), the canonical name",
            lambda: (
                run_dispatch.adapter_for("oc") is run_dispatch.RUNNER_ADAPTERS["oc"]
            ),
            True,
            "the lookup returns the registry's OWN object rather than a wrapper, so the delegation "
            "test's `assert_called_once_with` is about the function dispatch actually uses",
        ),
        (
            "adapter_for('opencode'), the schema ALIAS",
            lambda: (
                run_dispatch.adapter_for("opencode")
                is run_dispatch.RUNNER_ADAPTERS["oc"]
            ),
            True,
            "`opencode` is an ALIAS of `oc` in the shared schema, so it must CANONICALIZE, not "
            "refuse. A store written by an older aw (or by hand) can legitimately carry the long "
            "spelling, and refusing it would make a valid store unrunnable",
        ),
    )

    def test_every_derivation_and_lookup_answers_correctly(self) -> None:
        wrong = []
        for case, probe, expected, why in self.DERIVATIONS:
            try:
                got: Any = probe()
            except Exception as exc:  # a derivation must ANSWER here, not refuse
                wrong.append(
                    f"  {case}:\n    - raised {type(exc).__name__}: {exc}\n"
                    f"    this row exists because: {why}"
                )
                continue
            if got != expected:
                wrong.append(
                    f"  {case}:\n    - expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"runner derivation gave the wrong answer for {len(wrong)} of "
            f"{len(self.DERIVATIONS)} lookups. These functions decide WHICH HOST a dispatch "
            "launches, so read the grouping: both `resolve_*` rows failing means the derivation "
            "order collapsed (one field is now read for both routes, so a named profile can be "
            "overridden by the default or vice versa); an `adapter_for` row failing alone means "
            "canonicalization moved, and the alias row is the one that breaks stores written by an "
            "older aw. FIX: if `registered_runners()` grew an entry, do not edit this row to match "
            "- a host becomes launchable only together with the plan that records its verification "
            f"posture.\n" + "\n".join(wrong),
        )

    def test_the_registry_matches_the_shared_schema_runner_registry(self) -> None:
        """Kept separate: a SUBSET property over two sets, not a per-row answer.

        The table asks named functions for named values. This asks whether one whole set is
        contained in another, which has no row shape: the claim is about every future adapter as
        well as today's, so enumerating rows would defeat it.
        """
        for name in run_dispatch.RUNNER_ADAPTERS:
            self.assertIn(name, runner_profiles.RUNNER_REGISTRY)

    def test_the_opencode_adapter_delegates_to_oc_runipd_main(self) -> None:
        """Kept separate: materially different setup (a patched collaborator) and a CALL assertion.

        No subprocess, no shell, no rebuilt prompt: the driver's own parser is called directly. The
        claim is about HOW the adapter was called (`assert_called_once_with`), which no table row
        expressing an expected VALUE can make.
        """

        with mock.patch("agent_workflows.oc_runipd.main", return_value=7) as m:
            rc = run_dispatch.RUNNER_ADAPTERS["oc"](["as", "gem", "SEL"])
        self.assertEqual(rc, 7, "the host's exit code must be returned unchanged")
        m.assert_called_once_with(["as", "gem", "SEL"])

    def test_the_adapter_uses_no_subprocess_or_shell(self) -> None:
        """Kept separate: STRUCTURAL proof over the module's AST, so a 'simplification' to a shell
        call fails this file.

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

    def test_an_unknown_runner_refuses_and_names_the_registered_ones(self) -> None:
        """Kept separate: an `assertRaises` over a typed exception, not an exit code."""

        with self.assertRaises(run_dispatch.RunDispatchError) as ctx:
            run_dispatch.adapter_for("no-such-host")
        self.assertIn("oc", str(ctx.exception))

    def test_a_registered_but_unimplemented_runner_is_a_distinct_refusal(self) -> None:
        """Kept separate: an `assertRaises`, and the claim is that two refusals differ in WORDING.

        'known runner, no adapter' must not be reported as 'not a runner': different fixes. Uses a
        FICTIONAL host rather than the real `agy` row, for the reason recorded on `FUTURE_SPEC`; the
        real `agy` refusal is covered by the refusal table's two `agy` rows.
        """

        with mock.patch.dict(
            runner_profiles.RUNNER_REGISTRY, {"futurehost": FUTURE_SPEC}, clear=False
        ):
            with self.assertRaises(run_dispatch.RunDispatchError) as ctx:
                run_dispatch.adapter_for("futurehost")
        message = str(ctx.exception)
        self.assertIn("no dispatch adapter", message)
        self.assertNotIn("is not a registered runner", message)


class FailClosedRefusalTests(_HostSpyFixture):
    """V-02: every misconfiguration refuses with exit 2 and NEVER invokes a host.

    ONE table replaces twelve tests. Every one of them put the store into one bad STATE, ran one
    argv, and asserted exit 2 plus an empty spy plus (sometimes) one message needle. Only the STATE,
    the ARGV and the needle differed.

    Why the table beats the twelve. THE EXIT CODE IS THE CONTRACT: `EXIT_CANNOT_RUN` (2) is what
    `command_surface` declares for both routes and what a wrapper script branches on, and the
    realistic failure is not one refusal breaking but the shared load-and-resolve path mapping a
    whole family of store conditions onto a different class - or worse, onto SUCCESS. Twelve tests
    report that as twelve red lines each saying `2 != 0`; the table reports one failure naming every
    state whose verdict moved, which is the shape of the real problem. It also makes the bad-store
    states browsable as the SET they are, so the next person adding a validation can see what is
    already refused.

    THE EMPTY-SPY CHECK IS THE LOAD-BEARING HALF, and it is asserted on every row including the
    positive ones. A refusal that exits 2 AFTER launching a host session has already spent money and
    already mutated a repository, so "refused" and "refused before invoking anything" are different
    guarantees and only the second one is worth having.

    THE POSITIVE ROWS ARE IN THE SAME TABLE deliberately: `--help` on both routes must answer 0 with
    NO configuration at all. Without them, a router that refused every invocation unconditionally
    would satisfy all twelve negative rows. Their failure message says so.
    """

    #: (case, store state, argv, expected exit code, needles that MUST appear, why this row exists)
    #:
    #: `state` is one of "base" (the fixture store), "no-default" (the same store with
    #: `default_runner` removed), "absent" (no store file at all), "malformed" (bytes that are not
    #: JSON), "bad-schema" (an unsupported `schema_version`), "futurehost" (a profile naming a
    #: schema-valid host with no adapter, with the schema patched) or "agy" (SHIPPED data: a profile
    #: whose runner is `agy` AND `default_runner: agy`, with nothing patched).
    #:
    #: Needles are the ONE identifying phrase a user or an agent greps for. Whole sentences are not
    #: pinned: they are not load-bearing, and pinning them would make a reworded refusal a failure.
    REFUSALS = (
        (
            "a profile name that is not in the store",
            "base",
            ("run", "as", "nope", "SEL"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("no runner profile named 'nope'", "aw oc profile add nope"),
            "the commonest operator error, and the refusal must be ACTIONABLE: it names the missing "
            "profile AND the command that creates it, so the fix needs no documentation lookup",
        ),
        (
            "no default_runner configured, on the UNQUALIFIED route",
            "no-default",
            ("run", "ipd", "SEL"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("default_runner", "does not guess"),
            "the unqualified route has NO other source for the host, and guessing one would launch "
            "a model the operator never chose. `does not guess` is asserted because that promise is "
            "the whole reason this path refuses rather than defaulting",
        ),
        (
            "no store file at all, on the NAMED route",
            "absent",
            ("run", "as", "gem", "SEL"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("no runner profile named 'gem'",),
            "ROUTE COLUMN, first half: an absent store must refuse on the route that names a "
            "profile, where the missing thing is the PROFILE",
        ),
        (
            "no store file at all, on the UNQUALIFIED route",
            "absent",
            ("run", "ipd", "SEL"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("default_runner",),
            "ROUTE COLUMN, second half: the SAME state refuses on the other route too, but for a "
            "different missing thing (the default). One route refusing while the other launched a "
            "host default is exactly the asymmetry a single-route test cannot see",
        ),
        (
            "a store that is not valid JSON, on the NAMED route",
            "malformed",
            ("run", "as", "gem", "SEL"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("not valid JSON",),
            "DEGRADING TO EMPTY WOULD BE WORSE THAN REFUSING: an empty store means no profile and "
            "no default, so the host would launch with ITS OWN default model while the operator "
            "believes their configured profile is in force (runner_profiles' documented rule)",
        ),
        (
            "a store that is not valid JSON, on the UNQUALIFIED route",
            "malformed",
            ("run", "ipd", "SEL"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("not valid JSON",),
            "the same state on the other route, because the unqualified route is where a "
            "silently-empty store does the most damage: there is no profile name to fail on, so an "
            "empty store reads as 'no default configured' at best and as the host default at worst",
        ),
        (
            "an unsupported schema_version",
            "bad-schema",
            ("run", "ipd", "SEL"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("schema_version",),
            "a FUTURE store shape must refuse rather than be read with today's assumptions. The "
            "fix is to upgrade aw, which is only discoverable if the version is named",
        ),
        (
            "a profile naming a schema-valid host with no adapter",
            "futurehost",
            ("run", "as", "future", "SEL"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("no dispatch adapter",),
            "THE HYPOTHETICAL THAT RECURS AT EVERY FUTURE HOST, on a FICTIONAL host so the real "
            "`agy` row is not shadowed: a store can name a host the schema accepts but this build "
            "cannot launch, and that must refuse fail-closed rather than fall back to `oc`",
        ),
        (
            "SHIPPED DATA: a profile whose runner is agy",
            "agy",
            ("run", "as", "gg", "SEL"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("no dispatch adapter", "'agy'", "oc"),
            "`hostdefault-01` E-04, with NO patching: registering `agy` in the schema made this "
            "store state WRITABLE. The refusal must name the unlaunchable host AND the hosts that "
            "are launchable, because the whole point of the row is to record that host's "
            "verification posture, NOT to make `aw run` reach it",
        ),
        (
            "SHIPPED DATA: default_runner is agy, on the UNQUALIFIED route",
            "agy",
            ("run", "ipd", "SEL"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("no dispatch adapter", "'agy'", "oc"),
            "the second state `agy`'s registration made writable, and the more dangerous one: this "
            "route names NO profile, so nothing in the invocation hints that an unlaunchable host "
            "was selected. A fallback to `oc` here would look exactly like success",
        ),
        (
            "`as` with no profile name after it",
            "base",
            ("run", "as"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("requires a profile name",),
            "the profile is read POSITIONALLY, so an absent name must refuse rather than fall "
            "through to the default runner - which would launch a host the operator did not choose "
            "while their command line said they were choosing one",
        ),
        (
            "`as` followed immediately by an OPTION",
            "base",
            ("run", "as", "--model", SONNET_MODEL, "SEL"),
            run_dispatch.EXIT_CANNOT_RUN,
            ("requires a profile name",),
            "consuming `--model` AS the profile name would be silent and catastrophic: the lookup "
            "would fail on a profile named `--model`, or worse succeed against a store someone "
            "created one in. Exercised with a real flag spelling for that reason",
        ),
        (
            "POSITIVE: `--help` on the named route with NO store at all",
            "absent",
            ("run", "as", "--help"),
            0,
            ("aw run as <profile>",),
            "THE POSITIVE ROW: `--help` must never fail closed just because the store is missing, "
            "because reading the help is exactly what an operator does BEFORE configuring anything. "
            "Every refusal row above is vacuous while this is broken, since a router that refused "
            "everything would satisfy all of them",
        ),
        (
            "POSITIVE: `--help` on the unqualified route with NO store at all",
            "absent",
            ("run", "ipd", "--help"),
            0,
            ("aw run as <profile>",),
            "THE SECOND POSITIVE ROW, and not a duplicate: this route's help is reachable only "
            "through the branch that would otherwise resolve `default_runner`, so help answering "
            "here proves the help check happens BEFORE resolution rather than after it",
        ),
    )

    def _apply_state(self, state: str):
        """Put the store into one `REFUSALS` state; return a context manager to enter for the row."""

        import contextlib

        if state == "base":
            self.write_store(self.STORE)
            return contextlib.nullcontext()
        if state == "absent":
            self.remove_store()
            return contextlib.nullcontext()
        if state == "malformed":
            self.write_store("{ this is not json")
            return contextlib.nullcontext()
        store = json.loads(json.dumps(self.STORE))
        if state == "no-default":
            store.pop("default_runner")
        elif state == "bad-schema":
            store["schema_version"] = 99
        elif state == "futurehost":
            store["profiles"]["future"] = {
                "runner": "futurehost",
                "model": SONNET_MODEL,
            }
            self.write_store(store)
            return mock.patch.dict(
                runner_profiles.RUNNER_REGISTRY,
                {"futurehost": FUTURE_SPEC},
                clear=False,
            )
        elif state == "agy":
            store["profiles"]["gg"] = {"runner": "agy", "model": SONNET_MODEL}
            store["default_runner"] = "agy"
        else:  # pragma: no cover - a typo in the table, not a product defect
            raise AssertionError(f"unknown store state {state!r}")
        self.write_store(store)
        return contextlib.nullcontext()

    def test_every_misconfiguration_refuses_before_invoking_any_host(self) -> None:
        wrong = []
        positive_rows_broken = 0
        launched_anyway = 0
        for case, state, argv, expected_rc, needles, why in self.REFUSALS:
            with self._apply_state(state):
                rc, out, calls = self.invoke(*argv)
            problems = []
            if rc != expected_rc:
                problems.append(f"exit code expected {expected_rc}, got {rc}")
                if expected_rc == 0:
                    positive_rows_broken += 1
            if calls:
                launched_anyway += 1
                problems.append(
                    f"INVOKED THE HOST before deciding, with argv {calls!r}. A refusal that "
                    "launches first has already spent money and already touched a repository"
                )
            for needle in needles:
                if needle not in out:
                    problems.append(
                        f"output is missing the identifying phrase {needle!r}; got {out[:300]!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case}\n    argv: aw {' '.join(argv)}  (store state: {state})\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        extra = ""
        if launched_anyway:
            extra += (
                f" {launched_anyway} row(s) LAUNCHED A HOST before refusing, which is the severe "
                "failure here and must be fixed before any wording problem."
            )
        if positive_rows_broken:
            extra += (
                f" {positive_rows_broken} POSITIVE row(s) are among the failures, and while either "
                "is broken every refusal row is VACUOUS: a router that refused every invocation "
                "would satisfy all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"the dispatch router gave the wrong verdict for {len(wrong)} of {len(self.REFUSALS)} "
            f"store states.{extra} EXIT {run_dispatch.EXIT_CANNOT_RUN} (EXIT_CANNOT_RUN) IS A "
            "DECLARED CONTRACT that wrapper scripts branch on, so read the grouping before editing "
            "a row: every row of one STATE failing together means that validation stopped firing; "
            "rows of DIFFERENT states failing together means the shared load-and-resolve path "
            "changed the class it maps a bad store onto. FIX: a row that now exits 0 is the worst "
            "case, because it means a misconfigured store LAUNCHED something - check the spy line "
            f"in the failure before anything else.\n" + "\n".join(wrong),
        )


# ==================================================================================================
# E-03 / V-03: exact argv parity with the host-specific spelling
# ==================================================================================================


class HostParityTests(_HostSpyFixture):
    """V-03: the generic route adds NO behavioral layer beyond runner/profile selection.

    ONE table replaces twelve tests (ten here plus two from the old `SelectorAmbiguityTests`). Every
    one of them ran one generic invocation with the host spied, sometimes ran a host-specific
    invocation too, and compared argv lists. Only the ARGV and the comparison target differed.

    Why the table beats the twelve. The claim is a single PROPERTY - the router forwards its
    remainder unchanged and adds nothing - and the realistic failure is the forwarding path gaining
    a normalization step, which breaks MANY rows at once in a recognizable pattern (every row with a
    flag, or every row on one route). Twelve tests report that as twelve list comparisons; the table
    reports which invocations diverged and whether they share a route or a flag.

    THE HOST SPELLING IS A COLUMN, not a separate test per comparison. `aw oc run ...` and
    `aw opencode runipd ...` are two spellings of the same host entry point, and rows that name one
    assert PARITY (the generic and the specific spelling produce byte-identical argv) on top of the
    exact expected argv, which is what stops both sides drifting together.

    THE HOST'S RETURN CODE IS A COLUMN TOO, and every row carries one. The router must return the
    host's exit code UNCHANGED - a machine consuming `aw run` cannot tell a failed run from a failed
    dispatch otherwise - so instead of one test looping over codes, rows spread 0/1/2/3/130 across
    both routes and assert the code came back. Note 2 is deliberately among them: the host's own 2
    must be indistinguishable in VALUE from the router's refusal 2, which is why the refusal table
    asserts an EMPTY SPY rather than merely an exit code.
    """

    #: (case, generic argv, the host-specific argv to compare against or None, the exact expected
    #: forwarded argv, the code the spied host returns, why this row exists)
    PARITY = (
        (
            "the named route",
            ("run", "as", "gem", "SEL"),
            ("oc", "run", "as", "gem", "SEL"),
            ["as", "gem", "SEL"],
            0,
            "THE BASELINE: `aw run as gem SEL` must reach the driver with the same argv as "
            "`aw oc run as gem SEL`, which is what makes the generic route a SPELLING rather than a "
            "second implementation",
        ),
        (
            "the named route against the LONG host spelling",
            ("run", "as", "gem", "SEL"),
            ("opencode", "runipd", "as", "gem", "SEL"),
            ["as", "gem", "SEL"],
            1,
            "HOST-SPELLING COLUMN: `aw opencode runipd` is the same entry point under its long "
            "name, so parity must hold against it too. If it did not, the two host spellings would "
            "themselves have diverged and the row above would be comparing two equally wrong argvs",
        ),
        (
            "the unqualified route",
            ("run", "ipd", "SEL"),
            ("oc", "run", "SEL"),
            ["SEL"],
            0,
            "the unqualified route maps onto the host's UNQUALIFIED spelling, and the expected argv "
            "is the load-bearing half: it contains NO `as` clause, so the HOST applies its "
            "per-runner default profile rather than the router injecting one it guessed",
        ),
        (
            "an explicit --model override",
            ("run", "as", "gem", "SEL", "--model", SONNET_MODEL),
            ("oc", "run", "as", "gem", "SEL", "--model", SONNET_MODEL),
            ["as", "gem", "SEL", "--model", SONNET_MODEL],
            0,
            "an override must survive EXACTLY ONCE. Duplicating it is not cosmetic: argparse's "
            "last-wins would still launch, so a doubled flag is silent, and a doubled flag with "
            "different values launches the WRONG MODEL",
        ),
        (
            "an explicit --variant override",
            ("run", "as", "gem", "SEL", "--variant", "low"),
            ("oc", "run", "as", "gem", "SEL", "--variant", "low"),
            ["as", "gem", "SEL", "--variant", "low"],
            0,
            "the fixture profile ALREADY sets `variant: high`, so this row is the probe that the "
            "router forwards the operator's value verbatim instead of merging it with the stored "
            "profile field",
        ),
        (
            "an explicit --agent override",
            ("run", "as", "gem", "SEL", "--agent", "build"),
            ("oc", "run", "as", "gem", "SEL", "--agent", "build"),
            ["as", "gem", "SEL", "--agent", "build"],
            2,
            "the third override, and it carries return code 2 on purpose: the HOST's own 2 must "
            "come back as 2, indistinguishable in value from the router's refusal 2. That is why "
            "the refusal table asserts an EMPTY SPY and not merely a code",
        ),
        (
            "all three overrides together",
            (
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
            ),
            (
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
            ),
            [
                "as",
                "gem",
                "SEL",
                "--model",
                SONNET_MODEL,
                "--variant",
                "low",
                "--agent",
                "build",
            ],
            3,
            "NOT redundant with the three single-override rows: a forwarding bug that duplicates "
            "only when several flags are present (a per-flag append loop, say) passes each of them "
            "and fails here. ORDER is pinned too, since the host's last-wins makes order load-"
            "bearing when two flags could conflict",
        ),
        (
            "a LEADING option before the selector",
            ("run", "ipd", "--prepare-only", "SEL"),
            ("oc", "run", "--prepare-only", "SEL"),
            ["--prepare-only", "SEL"],
            0,
            "argparse REMAINDER cannot capture a LEADING option, so this is the row that proves "
            "the router intercepts before argparse gets the chance to reject it. Flag POSITION must "
            "not matter",
        ),
        (
            "a TRAILING option after the selector",
            ("run", "ipd", "SEL", "--prepare-only"),
            None,
            ["SEL", "--prepare-only"],
            0,
            "the other half of the position claim, and it pins ORDER: the two rows expect "
            "DIFFERENT argv (leading versus trailing), so a router that sorted or normalized "
            "argument order would pass one and fail the other rather than passing both",
        ),
        (
            "the `--` literal-selector escape",
            ("run", "ipd", "--", "as"),
            None,
            ["--", "as"],
            0,
            "`--` is the driver's escape for a selector that LOOKS like a keyword, and the token "
            "after it here is `as` itself. The router must consume neither: eating the `--` would "
            "turn a literal selector into a misplaced `as` clause",
        ),
        (
            "host help after a profile name",
            ("run", "as", "gem", "--help"),
            ("oc", "run", "as", "gem", "--help"),
            ["as", "gem", "--help"],
            0,
            "`--help` AFTER a profile is the HOST's help, not the route's, so it must reach the "
            "driver byte-identically. Contrast the refusal table's two `--help` rows, where the "
            "flag comes BEFORE any profile and the ROUTE answers: the two must not be confused",
        ),
        (
            "a token that looks like a profile, used as a selector",
            ("run", "ipd", "gem"),
            ("oc", "run", "gem"),
            ["gem"],
            0,
            "`gem` IS a profile in the fixture store, and under `ipd` it must still be forwarded "
            "as a SELECTOR with no `as` clause synthesized. Inferring a profile from an unknown "
            "token is the ambiguity the fixed `as` grammar exists to prevent",
        ),
        (
            "the unqualified route with an unusual host exit code",
            ("run", "ipd", "SEL"),
            None,
            ["SEL"],
            130,
            "130 is SIGINT, the code an operator's Ctrl-C produces inside the host. Clamping or "
            "remapping it would make an interrupted run indistinguishable from a clean one, and "
            "this row sits on the UNQUALIFIED route so the passthrough is proven on both",
        ),
    )

    def test_every_invocation_forwards_exactly_and_returns_the_hosts_code(self) -> None:
        wrong = []
        for case, argv, host_argv, expected, returncode, why in self.PARITY:
            rc, calls = self.forwarded(*argv, returncode=returncode)
            problems = []
            if calls != [expected]:
                problems.append(f"forwarded {calls!r}, expected {[expected]!r}")
            if rc != returncode:
                problems.append(
                    f"the host returned {returncode} but `aw` returned {rc}; the host's exit code "
                    "must pass through UNCHANGED"
                )
            if host_argv is not None:
                _rc_host, host_calls = self.forwarded(*host_argv, returncode=returncode)
                if host_calls != calls:
                    problems.append(
                        f"PARITY BROKEN: `aw {' '.join(argv)}` forwarded {calls!r} but "
                        f"`aw {' '.join(host_argv)}` forwarded {host_calls!r}"
                    )
            # A duplicated token is the specific defect the override rows exist for, and it is
            # worth naming rather than leaving the reader to diff two long lists.
            if calls:
                dupes = sorted(
                    {t for t in calls[0] if calls[0].count(t) > expected.count(t)}
                )
                if dupes:
                    problems.append(
                        f"these tokens appear MORE often than expected: {dupes!r} (a duplicated "
                        "flag is silent under argparse last-wins, and with different values it "
                        "launches the wrong thing)"
                    )
            if problems:
                wrong.append(
                    f"  {case}\n    argv: aw {' '.join(argv)}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the router failed to forward {len(wrong)} of {len(self.PARITY)} invocations "
            "unchanged. The property is that the generic route adds NO behavioral layer, so read "
            "the grouping: every row carrying a FLAG failing means the forwarding path gained a "
            "normalization or re-emission step; every row on ONE ROUTE failing means the two routes "
            "diverged; a PARITY-BROKEN line means the generic spelling and the host spelling now "
            "disagree, which is the one failure that no amount of editing the expected argv can "
            "honestly fix. FIX: if an exit-code line is failing, the router is now interpreting the "
            "host's result, which makes `aw run` unusable in a script - a host failure and a "
            f"dispatch refusal would become indistinguishable.\n" + "\n".join(wrong),
        )

    def test_both_entry_paths_produce_identical_argv(self) -> None:
        """Kept separate: materially different setup, calling the two seams DIRECTLY.

        Every table row drives `cli.main`, which takes the pre-parse interception path. This one
        calls `cli._dispatch` and `run_dispatch.dispatch` (from a parsed namespace) by hand and
        compares them, because the claim is that TWO INTERNAL ENTRY POINTS agree - which no
        invocation through the front door can distinguish.
        """

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

    def test_a_profile_named_as_is_impossible_by_schema(self) -> None:
        """Kept separate: an `assertRaises` plus a RESERVED-SET membership claim, not a dispatch.

        `as` is a reserved name in the shared schema, so the grammar cannot be made ambiguous at
        the source: no store can contain a profile whose name collides with the keyword.
        """

        self.assertIn("as", runner_profiles.RESERVED_PROFILE_NAMES)
        with self.assertRaises(runner_profiles.RunnerProfileError):
            runner_profiles.validate_profile_name("as")

    def test_a_second_as_clause_is_refused_by_the_host_not_silently_accepted(
        self,
    ) -> None:
        """Kept separate: the only test here that invokes the REAL driver, unspied.

        Every table row patches `oc_runipd.main`, so no row can observe what the DRIVER does with
        what it receives. The router forwards a misplaced second `as` clause verbatim (measured:
        with the host spied it arrives as `['as', 'gem', 'SEL', 'as', 'sonnet']`); the refusal is
        the driver's own (`3cm15q` E-01), so proving it requires letting the driver run.
        """

        rc, out = _cli("run", "as", "gem", "SEL", "as", "sonnet")
        self.assertEqual(rc, 2, out)
        self.assertIn("as", out)


# ==================================================================================================
# E-04 / V-04: the adversarial namespace matrix
# ==================================================================================================


class NamespaceRoutingTests(_HostSpyFixture):
    """V-01 + V-04: every token under `aw run`/`aw runs` selects the handler it selected before.

    TWO tables replace ten tests spread over three classes (`ProfileParsedAsDataNotGrammarTests`,
    `LedgerRoutingUnchangedTests`, `ProhibitedSpellingTests`). Every one of them ran one argv with
    the host spied and asserted which handler it reached - the ledger dispatcher, the host runner, an
    argparse rejection, or family help. The class boundaries tracked which V-item the plan filed the
    claim under, not what the claim was about.

    Why the tables beat the ten. The subject is ONE namespace, and the danger is a token MOVING
    between handlers: a profile name capturing a command, a viewer leaf resurrected under the
    writing noun, an unknown token inferred as a selector. Ten tests can each say one token is fine;
    the tables say the whole namespace is partitioned as intended, and a failure that hits several
    tokens at once reads as "the partition moved" rather than as several coincidences.

    THE NOUN IS A COLUMN (`aw run` WRITES, `aw runs` READS, per the `0soncw` split), and it is the
    load-bearing one: the same leaf name must reach the ledger under one noun and be REJECTED under
    the other, which is a claim no single-noun test can make.

    POSITIVE AND NEGATIVE LIVE IN THE SAME TABLE deliberately. `aw status` must still exit 0 and
    every writer leaf must still reach `run_cli.run_cli`, because a CLI that rejected every token
    would satisfy every prohibited-spelling row while being useless. Their failure messages say so.
    """

    #: (noun, leaf, expected handler, expected `run_command` or None, why this row exists)
    #:
    #: `handler` is one of:
    #:   "ledger"   -> reaches `run_cli.run_cli`, and (for writers) as the named `run_command`
    #:   "viewer"   -> does NOT reach `run_cli`; the viewer table owns it (`0soncw` E-04)
    #:   "rejected" -> argparse refuses with `invalid choice`, nonzero, no handler entered
    #: No row may EVER reach the host runner, which is asserted for every row rather than as a
    #: column, because it is the one claim that is unconditional.
    LEAVES = (
        (
            "run",
            "start",
            "ledger",
            "start",
            "the four WRITE leaves are `0soncw`'s surface and must still reach the ledger "
            "dispatcher AS THEMSELVES. Asserted by WHERE the call lands and under WHICH name, not "
            "by an exit code: a wrong-but-nonzero exit would look identical to a correct refusal",
        ),
        (
            "run",
            "record",
            "ledger",
            "record",
            "the append leaf. `record` is also a word a future dispatch verb might want, so its "
            "continued routing is the probe that adding `as`/`ipd` did not shuffle the writers",
        ),
        (
            "run",
            "cancel",
            "ledger",
            "cancel",
            "a TERMINAL write. Misrouting this one would mean an operator's abort silently reached "
            "something else",
        ),
        (
            "run",
            "finalize",
            "ledger",
            "finalize",
            "the leaf that declares a run DONE, so it is the one whose misrouting would be worst "
            "and the one most likely to be shadowed by a future `run` verb",
        ),
        (
            "runs",
            "show",
            "ledger",
            None,
            "a READ leaf under the reading noun. `run_command` is None for viewers because the "
            "reading noun does not carry that attribute (measured), which is itself the evidence "
            "that the two nouns are genuinely separate parsers",
        ),
        (
            "runs",
            "status",
            "ledger",
            None,
            "THE COLLISION ROW: `status` is ALSO a profile name in the fixture store AND a "
            "top-level command. Under `aw runs` it must still be the viewer leaf, which together "
            "with the `run as status` parity row states that one word is three different things in "
            "three positions and none of them captures another",
        ),
        (
            "runs",
            "next",
            "ledger",
            None,
            "the leaf an unattended driver POLLS, so its routing is load-bearing for automation "
            "rather than for humans",
        ),
        (
            "runs",
            "resume",
            "ledger",
            None,
            "the recovery entry point; reaching a dispatch route instead would start a NEW run "
            "where the operator asked to continue an old one",
        ),
        (
            "runs",
            "decisions",
            "ledger",
            None,
            "a read-only projection, included so the viewer family is covered as a family and not "
            "only at its famous members",
        ),
        (
            "runs",
            "questions",
            "ledger",
            None,
            "the second such projection, for the same reason",
        ),
        (
            "runs",
            "evidence",
            "ledger",
            None,
            "the evidence reader, which is ALSO a profile name in the fixture store: another "
            "command-like name that must not have been captured",
        ),
        (
            "runs",
            "verify-ledger",
            "ledger",
            None,
            "the integrity verb, whose HYPHEN makes it the probe that a hyphenated leaf is not "
            "parsed as a flag or split into tokens",
        ),
        (
            "runs",
            "list",
            "viewer",
            None,
            "THE ONE VIEWER EXCEPTION: `list` is routed to `run_viewer`, not `run_cli` (`0soncw` "
            "E-04). Stated as its own handler value rather than skipped, because a `continue` in a "
            "loop records nothing while this row records WHY",
        ),
        (
            "run",
            "show",
            "rejected",
            None,
            "`0soncw` MOVED the viewers to the reading noun, and that rejection must SURVIVE: "
            "adding `as`/`ipd` must not resurrect a viewer under the writing noun by accident",
        ),
        (
            "run",
            "status",
            "rejected",
            None,
            "the same claim for the name that is simultaneously a profile, a viewer leaf and a "
            "top-level command - the single most over-loaded word in this namespace",
        ),
        (
            "run",
            "evidence",
            "rejected",
            None,
            "a third moved viewer, so the claim reads as a family property rather than as two "
            "special cases",
        ),
        (
            "run",
            "verify-ledger",
            "rejected",
            None,
            "the fourth, and the hyphenated one: a rejection that depended on the name being a "
            "single word would pass the three above and fail here",
        ),
    )

    def test_every_leaf_still_selects_its_original_handler(self) -> None:
        wrong = []
        ledger_rows_broken = 0
        for noun, leaf, handler, expected_command, why in self.LEAVES:
            self.calls = []
            with self.spy():
                with mock.patch("agent_workflows.run_cli.run_cli", return_value=0) as m:
                    rc, out = _cli(noun, leaf, "no-such-target")
            problems = []
            if self.calls:
                problems.append(
                    f"REACHED THE HOST RUNNER with argv {self.calls!r}; a ledger leaf must never "
                    "launch a host session"
                )
            if handler == "ledger":
                if m.call_count != 1:
                    ledger_rows_broken += 1
                    problems.append(
                        f"did not reach `run_cli.run_cli` (call count {m.call_count}); rc={rc}, "
                        f"output {out[:200]!r}"
                    )
                elif expected_command is not None:
                    got = getattr(m.call_args[0][0], "run_command", "<absent>")
                    if got != expected_command:
                        problems.append(
                            f"reached the ledger dispatcher as run_command={got!r}, expected "
                            f"{expected_command!r}"
                        )
            elif handler == "viewer":
                if m.call_count:
                    problems.append(
                        "reached `run_cli.run_cli`, but this leaf belongs to the VIEWER table "
                        "(`run_viewer`), so routing it here means the viewer split regressed"
                    )
            else:
                if rc == 0:
                    problems.append(
                        f"succeeded (rc 0); it must be refused. Output {out[:200]!r}"
                    )
                if "invalid choice" not in out:
                    problems.append(
                        "the refusal does not say `invalid choice`, which is the phrase that tells "
                        f"an operator the leaf moved rather than failed; got {out[:200]!r}"
                    )
                if m.call_count:
                    problems.append(
                        "entered the ledger dispatcher despite being rejected at the parser"
                    )
            if problems:
                wrong.append(
                    f"  aw {noun} {leaf}  (expected handler: {handler})\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        extra = ""
        if ledger_rows_broken:
            extra = (
                f" {ledger_rows_broken} row(s) that must REACH the ledger did not, and while any of "
                "those is broken the `rejected` rows are vacuous: a parser that refused every leaf "
                "would satisfy all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.LEAVES)} run-family leaves changed handler.{extra} The "
            "NOUN column is the thing to read first: every `aw run` row failing means the writing "
            "parser changed, every `aw runs` row failing means the reading one did, and a leaf "
            "flipping between `ledger` and `rejected` means the `0soncw` split moved - which "
            "silently changes which commands exist. FIX: a row reaching the HOST RUNNER is the "
            "severe case and comes first, because it means a ledger verb now launches a model "
            f"session.\n" + "\n".join(wrong),
        )

    #: (case, argv, expected exit code, invalid-choice expected, why this row exists)
    #:
    #: Every row additionally requires that NO host was invoked, which is the unconditional half of
    #: the claim. `invalid choice` is argparse's own phrase and is the one identifying needle
    #: asserted; the rest of the usage block is not pinned.
    SPELLINGS = (
        (
            "`aw gem`, a bare profile name as a command",
            ("gem",),
            2,
            True,
            "the whole temptation this grammar refuses: minting a top-level command per host would "
            "make the command namespace depend on a user-local file, so a stored profile could "
            "shadow a real future command",
        ),
        (
            "`aw gemrun`",
            ("gemrun",),
            2,
            True,
            "the concatenated spelling, which a helpful alias generator would produce",
        ),
        (
            "`aw rungem`",
            ("rungem",),
            2,
            True,
            "the reverse concatenation, so neither word order is quietly available",
        ),
        (
            "`aw run-gem`",
            ("run-gem",),
            2,
            True,
            "the hyphenated spelling: reads like a command, is actually data",
        ),
        (
            "`aw run:gem`",
            ("run:gem",),
            2,
            True,
            "the colon spelling. A separator is still just a NAME to argparse, so excluding the "
            "hyphen form does not exclude this one",
        ),
        (
            "`aw run gem`, a bare unknown token under the run noun",
            ("run", "gem"),
            2,
            True,
            "THE INFERENCE ROW: an unknown token under `run` must be REFUSED, never guessed at. "
            "Inferring a profile here is what would make a future `aw run <verb>` addition a "
            "silent behavior change for anyone with a profile of that name",
        ),
        (
            "`aw run gem SEL`, unknown token plus a selector",
            ("run", "gem", "SEL"),
            2,
            True,
            "the same inference with a trailing argument, which is the shape that LOOKS most like a "
            "legitimate invocation and so is most likely to be accepted by a lenient parser",
        ),
        (
            "`aw run with gem SEL`",
            ("run", "with", "gem", "SEL"),
            2,
            True,
            "ALTERNATE KEYWORDS ARE EXCLUDED: `as` is the one canonical spelling. Accepting "
            "synonyms would mean the grammar had several entry points to keep in agreement",
        ),
        (
            "`aw run using gem SEL`",
            ("run", "using", "gem", "SEL"),
            2,
            True,
            "a second plausible synonym, so the exclusion reads as a rule rather than as one "
            "rejected word",
        ),
        (
            "`aw run w gem SEL`",
            ("run", "w", "gem", "SEL"),
            2,
            True,
            "the abbreviated synonym, which is exactly what a terseness-minded patch would add",
        ),
        (
            "`aw run future-command`, a name a future verb might take",
            ("run", "future-command"),
            2,
            True,
            "a profile of THIS NAME exists in the fixture store, so the row proves an unknown "
            "subcommand is refused rather than reinterpreted as a selector - which is what makes "
            "adding a real verb later a safe, visible change",
        ),
        (
            "POSITIVE: `aw status`, a real top-level command",
            ("status",),
            0,
            False,
            "THE POSITIVE ROW, and the one that makes the rest non-vacuous: a profile named "
            "`status` sits in the fixture store, and `aw status` must STILL exit 0. Demanding "
            "failure here would be wrong, and a CLI that refused everything would satisfy every "
            "row above",
        ),
    )

    def test_no_prohibited_spelling_exists_and_real_commands_still_work(self) -> None:
        wrong = []
        positive_rows_broken = 0
        for case, argv, expected_rc, expect_invalid, why in self.SPELLINGS:
            self.calls = []
            with self.spy():
                rc, out = _cli(*argv)
            problems = []
            if rc != expected_rc:
                problems.append(f"exit code expected {expected_rc}, got {rc}")
                if expected_rc == 0:
                    positive_rows_broken += 1
            if self.calls:
                problems.append(
                    f"REACHED THE HOST RUNNER with argv {self.calls!r}; no prohibited spelling may "
                    "launch anything"
                )
            has_invalid = "invalid choice" in out
            if expect_invalid and not has_invalid:
                problems.append(
                    "argparse did not say `invalid choice`, so this spelling is being handled "
                    f"somewhere rather than refused as unknown; got {out[:200]!r}"
                )
            if not expect_invalid and has_invalid:
                problems.append(
                    "argparse said `invalid choice` for a REAL command; the token was captured or "
                    "removed from the parser"
                )
            if problems:
                wrong.append(
                    f"  {case}\n    argv: aw {' '.join(argv)}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        extra = ""
        if positive_rows_broken:
            extra = (
                " THE POSITIVE ROW IS AMONG THE FAILURES, and while it is broken every prohibited "
                "row here is VACUOUS: a CLI that rejected every token would satisfy all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SPELLINGS)} namespace spellings behaved wrongly.{extra} "
            "Terseness must not be bought with command namespace or unknown-token inference, so "
            "read the grouping: several ROOT spellings (`aw gem`, `aw gemrun`) becoming valid means "
            "commands are being generated from the profile store; the `aw run <token>` rows "
            "becoming valid means unknown tokens are now INFERRED, which turns every future verb "
            "addition into a silent behavior change for anyone holding a same-named profile. FIX: "
            "a row that reached the HOST RUNNER is the severe case, because an accidental spelling "
            f"then spends money.\n" + "\n".join(wrong),
        )

    #: (profile name, why this row exists) - names that are ALSO commands, leaves or reserved-looking
    #: words, each of which must be readable as a PROFILE in the one position where a profile is
    #: read. This is the mirror of `SPELLINGS`: that table says these names are not grammar anywhere
    #: else, and this one says they ARE data right after `as`.
    COMMAND_LIKE_PROFILES = (
        (
            "status",
            "the most over-loaded word here: a top-level command, a `aw runs` viewer leaf AND a "
            "profile. All three must coexist, and this row is the third of the three",
        ),
        (
            "report",
            "a command-shaped name that is not currently a leaf, so it covers the case of a profile "
            "colliding with a verb someone may add later",
        ),
        (
            "run",
            "the NOUN ITSELF as a profile name. If the profile position were parsed with any "
            "grammar awareness at all, this is the name that would break it",
        ),
        (
            "show",
            "a moved viewer leaf (rejected under `aw run`, live under `aw runs`) reused as a "
            "profile, so the row spans both halves of the `0soncw` split",
        ),
        (
            "evidence",
            "a second moved viewer, so the claim reads as a family property",
        ),
        (
            "future-command",
            "a name NO command has yet. It is refused as a subcommand (`SPELLINGS`) and accepted as "
            "a profile here, which together is the promise that adding that verb later breaks "
            "neither behavior",
        ),
    )

    def test_every_command_like_name_is_a_profile_in_the_profile_position(self) -> None:
        wrong = []
        for name, why in self.COMMAND_LIKE_PROFILES:
            rc, calls = self.forwarded("run", "as", name, "SEL")
            problems = []
            if rc != 0:
                problems.append(f"exit code expected 0, got {rc}")
            if calls != [["as", name, "SEL"]]:
                problems.append(
                    f"forwarded {calls!r}, expected {[['as', name, 'SEL']]!r}; the name must reach "
                    "the driver as the PROFILE NAME, unchanged"
                )
            if problems:
                wrong.append(
                    f"  profile {name!r} after `as`\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.COMMAND_LIKE_PROFILES)} command-like profile names were not "
            "readable in the profile position. THE COLLISION CLAIM IS EXACTLY THIS: a profile name "
            "is read ONLY from the slot immediately after the literal `as`, so no name can shadow a "
            "command AND no command name is forbidden as a profile. ALL ROWS FAILING TOGETHER means "
            "the profile slot stopped being a plain positional and grew grammar awareness (a "
            "reserved-word check, or a lookup against the command table); ONE row failing names the "
            "word that acquired special handling. FIX: this table is the mirror of `SPELLINGS`; the "
            "two must stay in agreement, since weakening either one is what lets a stored profile "
            f"name and a command collide.\n" + "\n".join(wrong),
        )

    def test_the_real_runs_status_leaf_still_refuses_an_unknown_run(self) -> None:
        """Kept separate: the only routing test that lets the REAL ledger handler run.

        Every `LEAVES` row patches `run_cli.run_cli`, so a row can prove WHERE a call landed but
        never that the handler behind it still works. This one runs `aw runs status` unpatched
        against a run id that does not exist, so the viewer leaf is observed END TO END: it must
        refuse (nonzero) and must not have reached the host runner. Without it, `run_cli` could have
        been replaced by a stub returning 0 and the whole `LEAVES` table would still pass.
        """

        self.calls = []
        with self.spy():
            rc, out = _cli("runs", "status", "no-such-run-id")
        self.assertEqual(
            self.calls, [], "`aw runs status` must not reach the host runner"
        )
        self.assertNotEqual(rc, 0, out)

    def test_bare_run_shows_family_help_rather_than_dispatching(self) -> None:
        """Kept separate: the assertion is over HELP TEXT content, not a handler or an exit code.

        Every `LEAVES` row names a leaf and asks which handler it reached. `aw run` with no leaf at
        all reaches none of them: argparse prints the family's own help, so the only observable is
        that the help lists the writer leaves. A handler column cannot express that.
        """

        self.calls = []
        with self.spy():
            rc, out = _cli("run")
        self.assertEqual(self.calls, [], "bare `aw run` must not invoke a host")
        self.assertNotEqual(rc, 0, out)
        for leaf in ("start", "finalize"):
            self.assertIn(leaf, out, f"the family help must still list {leaf!r}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

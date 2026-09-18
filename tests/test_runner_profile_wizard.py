"""Tests for runprofile Order 02 (`p0l1to`) E-01/E-02/E-04: model discovery and the wizard.

THE MATRIX THIS SUITE IS REQUIRED TO FAIL ON (plan E-05 / V-01 / V-02 / V-04). Each bullet is a
plausible implementation that would pass a happy-path-only suite:

  * green-washed discovery - a missing/timed-out/failing/garbage-emitting `opencode models` must
                             produce an UNAVAILABLE catalog with a NAMED reason, never a
                             successful EMPTY list, and never a refusal to create the profile.
  * a non-read-only probe  - the argv must be exactly `[opencode, models]` with `shell=False` and a
                             bounded timeout, and must NEVER carry `--refresh` or any write flag.
  * an unusable catalog    - hundreds of models must stay selectable through substring filtering
                             and bounded paging.
  * an unreachable model   - exact manual entry must ALWAYS be available, including after total
                             discovery failure, or a private model can never be configured.
  * an overclaimed variant - the menu must label variants provider-specific, must store "provider
                             default" as NO variant, and must accept an exact custom value.
  * a write after decline  - cancel / empty / EOF / interrupt / declined-save / exhausted-retries
                             must leave the config ABSENT or BYTE-IDENTICAL, proven by comparing
                             bytes rather than by inspecting code.
  * an assumed default     - the save, default-profile, and default-runner questions must be
                             SEPARATE and each default NO, and declining one must preserve its
                             previous value.
  * a leaked credential    - no captured output may contain a sentinel secret.

MODEL IDENTIFIERS HERE ARE SYNTHETIC, matching `tests/test_runner_profiles.py` and the
orchestrator's requirement (`3m0urk`): one real identifier is institution-specific and a tracked
test is public.

Stdlib `unittest` only. No test spawns a process, touches the network, or reads the developer's
own configuration: the subprocess boundary and the store are injected.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import List, Optional, Sequence

from agent_workflows import oc_models as OM
from agent_workflows import runner_profile_wizard as W
from agent_workflows import runner_profiles as RP

# Synthetic equivalents of the three requested profiles (see module docstring).
_FLASH = "example-vendor/flash-3.7"
_INHOUSE = "example-gw/inhouse/pt3-sonnet-5-1m-us"
_SOL = "example-openai/gpt-sol-5.6"

# A sentinel that MUST never appear in wizard output. Shaped like a real key so a naive dump of a
# config or an environment would be caught.
SENTINEL_SECRET = "sk-sentinel-must-never-be-printed-9999"


class _FakeProc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _RecordingRunner:
    """A `subprocess.run` stand-in that records its call and returns a scripted result."""

    def __init__(self, result=None, raises: Optional[BaseException] = None):
        self.result = result if result is not None else _FakeProc()
        self.raises = raises
        self.calls: List[dict] = []

    def __call__(self, argv, **kwargs):
        self.calls.append({"argv": list(argv), "kwargs": dict(kwargs)})
        if self.raises is not None:
            raise self.raises
        return self.result


class _Script:
    """A scripted TTY: `ask` pops the next answer, `emit` records every output line.

    An exhausted script raises ``EOFError``, which is exactly what a real ``input()`` does at end
    of input, so a wizard that asks one question too many is caught as a cancel rather than
    hanging or silently reusing an answer.
    """

    def __init__(self, answers: Sequence[str], interrupt_at: Optional[int] = None):
        self.answers = list(answers)
        self.prompts: List[str] = []
        self.lines: List[str] = []
        self.interrupt_at = interrupt_at
        self._asked = 0

    def ask(self, prompt: str) -> str:
        self.prompts.append(prompt)
        self._asked += 1
        if self.interrupt_at is not None and self._asked == self.interrupt_at:
            raise KeyboardInterrupt
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)

    def emit(self, line: str) -> None:
        self.lines.append(line)

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


class _Store:
    """An injected store: counts writes so "wrote exactly once" and "never wrote" are assertable."""

    def __init__(
        self, cfg: Optional[RP.ProfileConfig] = None, error: Optional[Exception] = None
    ):
        self.cfg = cfg if cfg is not None else RP.empty_config()
        self.error = error
        self.writes: List[RP.ProfileConfig] = []

    def load(self) -> RP.ProfileConfig:
        if (
            isinstance(self.error, (RP.ProfileSchemaError, RP.ProfileStoreError))
            and not self.writes
        ):
            # Only a LOAD error when explicitly configured as such by the test.
            pass
        return self.cfg

    def save(self, cfg: RP.ProfileConfig):
        if self.error is not None:
            raise self.error
        self.writes.append(cfg)
        self.cfg = cfg
        return Path("/injected/runner-profiles.json")


def _io(
    script: _Script,
    catalog: Optional[OM.ModelCatalog] = None,
    store: Optional[_Store] = None,
    with_writer: bool = True,
) -> W.WizardIO:
    store = store if store is not None else _Store()
    cat = (
        catalog
        if catalog is not None
        else OM.ModelCatalog(models=(_FLASH,), source=OM.CATALOG_SOURCE_CLI)
    )
    return W.WizardIO(
        ask=script.ask,
        emit=script.emit,
        discover=lambda: cat,
        load=store.load,
        save=store.save if with_writer else None,
    )


# ==================================================================================================
# E-01 / V-01: the read-only catalog probe
# ==================================================================================================


class CatalogArgvTests(unittest.TestCase):
    """NOT MERGED: five structurally different claims about the probe, not five data rows.

    These look like a cluster and are not one. `test_argv_is_exactly_the_read_only_probe` compares a
    LIST; the forbidden-flag test iterates a module constant and makes a NEGATIVE claim about argv;
    the smuggled-flag test uses `assertRaises`; the shell/timeout test inspects the recorded KWARGS
    rather than argv at all; and the default-timeout test asserts a numeric RANGE on a constant with
    no subprocess involved. A table over these would need a column per test and a branch per row,
    which is worse than the five.
    """

    def test_argv_is_exactly_the_read_only_probe(self):
        self.assertEqual(OM.catalog_argv(), ["opencode", "models"])
        self.assertEqual(OM.catalog_argv("/opt/oc"), ["/opt/oc", "models"])

    def test_no_refresh_or_write_flag_is_ever_issued(self):
        """The NEGATIVE assertion V-01 requires: discovery must not refresh or write."""
        runner = _RecordingRunner(_FakeProc(0, f"{_FLASH}\n"))
        OM.discover_models(runner=runner)
        argv = runner.calls[0]["argv"]
        for forbidden in OM.FORBIDDEN_CATALOG_FLAGS:
            self.assertNotIn(forbidden, argv)
        self.assertNotIn("--refresh", argv)
        self.assertEqual(argv, ["opencode", "models"])

    def test_argv_builder_refuses_a_smuggled_forbidden_flag(self):
        """Kept separate: an assertRaises test."""
        with self.assertRaises(ValueError):
            OM.catalog_argv("--refresh")

    def test_shell_is_false_and_the_timeout_is_bounded(self):
        runner = _RecordingRunner(_FakeProc(0, f"{_FLASH}\n"))
        OM.discover_models(runner=runner, timeout=7.5)
        kwargs = runner.calls[0]["kwargs"]
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["timeout"], 7.5)
        self.assertIs(kwargs["capture_output"], True)
        self.assertIs(kwargs["text"], True)
        self.assertIs(kwargs["check"], False)

    def test_default_timeout_is_finite(self):
        """Kept separate: asserts a RANGE on a module constant, with no probe and no subprocess."""
        self.assertGreater(OM.CATALOG_TIMEOUT, 0)
        self.assertLess(OM.CATALOG_TIMEOUT, 120)


class CatalogParsingTests(unittest.TestCase):
    """NOT MERGED: four different claims about parsing, only two of which share a shape.

    The two `parse_models_output` tests could be rows, but each is already a single call whose input
    is a multi-line fixture the assertion is inseparable from: the noise test's value is the SHAPE of
    the raw block (banners, ANSI, bullets, trailing words) and the dedupe test's is the ORDER of a
    repeated sequence. The other two are not rows at all: one asserts an `assertIs` identity between
    two modules' regexes, and one tests `strip_ansi`, a different function.
    """

    def test_ansi_and_noise_are_normalized_and_only_exact_records_survive(self):
        raw = (
            "\x1b[1mScanning providers...\x1b[0m\n"
            "\n"
            f"\x1b[32m{_FLASH}\x1b[0m\n"
            f"  {_INHOUSE}  \n"
            "* a bullet line\n"
            "not-a-model\n"
            "provider/model with trailing words\n"
            f"{_SOL}\n"
        )
        self.assertEqual(OM.parse_models_output(raw), (_FLASH, _INHOUSE, _SOL))

    def test_dedupe_is_deterministic_and_first_seen(self):
        raw = f"{_SOL}\n{_FLASH}\n{_SOL}\n{_FLASH}\n{_INHOUSE}\n"
        self.assertEqual(OM.parse_models_output(raw), (_SOL, _FLASH, _INHOUSE))

    def test_the_accepted_grammar_is_the_profile_schemas_own(self):
        """Kept separate: an `assertIs` IDENTITY claim between two modules, not a value row.

        A discovered model must be storable, so the two grammars must be ONE grammar rather than two
        that happen to agree today.
        """
        self.assertIs(OM._model_re(), RP.MODEL_RE)
        for model in OM.parse_models_output(f"{_FLASH}\n{_INHOUSE}\n{_SOL}\n"):
            self.assertEqual(RP.validate_model(model), model)

    def test_strip_ansi_removes_csi_and_osc(self):
        """Kept separate: tests `strip_ansi`, a different function from the parser above."""
        self.assertEqual(OM.strip_ansi("\x1b[31mred\x1b[0m"), "red")
        self.assertEqual(OM.strip_ansi("\x1b]0;title\x07x"), "x")


class CatalogDiagnosticTests(unittest.TestCase):
    """Every way discovery can fail produces an UNAVAILABLE catalog with its OWN named reason.

    ONE table replaces six tests of identical shape: script the injected subprocess boundary to fail
    one way, assert `available` is False and `reason` equals one constant.

    Why the table beats the six. The reasons are a CLOSED SET the wizard shows a user verbatim
    (`_report_catalog` prints "Model discovery is unavailable (<reason>)"), and the failure this
    guards is GREEN-WASHING: a discovery path that swallowed one failure class into another, or into
    a successful empty list, would still satisfy five of six tests individually while telling a user
    the wrong thing about their machine. Six tests report a collapse as scattered red lines; the
    table reports which reasons moved, and a mutation that maps several classes onto one reason shows
    up as several rows naming the SAME wrong value, which is what identifies the cause.

    THE POSITIVE ROW IS IN THE SAME TABLE deliberately, and the failure message says why: every
    negative row is satisfied by a `discover_models` that returned an unavailable catalog
    unconditionally, so the row where the probe SUCCEEDS is the only thing making them evidence.
    """

    #: (case, the scripted subprocess outcome, expected reason or None for "must SUCCEED",
    #: why this row exists)
    #:
    #: A row's second element is either a `_FakeProc` (the probe ran and returned) or an exception
    #: instance (the probe could not run at all).
    DIAGNOSTICS = (
        (
            "the opencode binary is not on PATH",
            FileNotFoundError(),
            OM.CATALOG_MISSING_BINARY,
            "the most common real failure. It must be NAMED, so the wizard can tell the user their "
            "binary is missing rather than that they own no models",
        ),
        (
            "the probe is denied permission to execute",
            PermissionError(),
            OM.CATALOG_MISSING_BINARY,
            "an OSError that is NOT FileNotFoundError must degrade to the same unreachable-binary "
            "reason rather than escaping as a crash. A traceback out of discovery would abort the "
            "wizard entirely, which is the 'refusal to create the profile' the plan forbids",
        ),
        (
            "the probe exceeds its bounded timeout",
            subprocess.TimeoutExpired(cmd=["opencode", "models"], timeout=1),
            OM.CATALOG_TIMED_OUT,
            "a HANG is its own diagnosis, distinct from a missing binary: the binary exists and is "
            "not answering, which is what the bounded timeout exists to convert into a verdict",
        ),
        (
            "the probe exits nonzero",
            _FakeProc(3, "boom"),
            OM.CATALOG_NONZERO_EXIT,
            "the tool RAN and REFUSED. Distinct from unparseable output, because the exit code is a "
            "deliberate signal while unparseable stdout is not",
        ),
        (
            "the probe exits zero but emits only banners and noise",
            _FakeProc(0, "Loading...\nnope\n"),
            OM.CATALOG_UNPARSEABLE,
            "A ZERO EXIT IS NOT SUCCESS. Output that parses to no exact provider/model record is "
            "unparseable, never a successful empty list, or the wizard would report a healthy "
            "catalog of nothing and the user would think they own no models",
        ),
        (
            "the probe exits zero with completely empty output",
            _FakeProc(0, ""),
            OM.CATALOG_NO_MODELS,
            "NO OUTPUT is separated from UNPARSEABLE OUTPUT on purpose: they point a user at "
            "different problems (nothing configured, versus a version whose format changed)",
        ),
        (
            "the probe succeeds and lists two models",
            _FakeProc(0, f"{_FLASH}\n{_SOL}\n"),
            None,
            "POSITIVE: the catalog is AVAILABLE, carries both ids, is sourced from the CLI, and its "
            "reason is EMPTY. Without this row a `discover_models` that always reported "
            "unavailability would satisfy every row above",
        ),
    )

    def test_every_discovery_failure_reports_its_own_named_reason(self):
        wrong = []
        by_reason = {}
        for case, outcome, expected, why in self.DIAGNOSTICS:
            runner = (
                _RecordingRunner(raises=outcome)
                if isinstance(outcome, BaseException)
                else _RecordingRunner(outcome)
            )
            cat = OM.discover_models(allow_config_fallback=False, runner=runner)
            problems = []
            if expected is None:
                if not cat.available:
                    problems.append(
                        f"the catalog must be AVAILABLE, but it is not (reason={cat.reason!r})"
                    )
                if cat.models != (_FLASH, _SOL):
                    problems.append(
                        f"expected models {(_FLASH, _SOL)!r}, got {cat.models!r}"
                    )
                if cat.source != OM.CATALOG_SOURCE_CLI:
                    problems.append(
                        f"expected source {OM.CATALOG_SOURCE_CLI!r}, got {cat.source!r}"
                    )
                if cat.reason:
                    problems.append(
                        f"a SUCCESSFUL probe must carry NO reason, but it carries {cat.reason!r}"
                    )
            else:
                if cat.available:
                    problems.append(
                        "the catalog reports itself AVAILABLE after a failure, which is the "
                        f"green-washing this table exists to catch (models={cat.models!r})"
                    )
                if cat.models != ():
                    problems.append(
                        f"a failed probe must yield no models, got {cat.models!r}"
                    )
                if cat.reason != expected:
                    by_reason[cat.reason] = by_reason.get(cat.reason, 0) + 1
                    problems.append(f"reason expected {expected!r}, got {cat.reason!r}")
            if problems:
                wrong.append(
                    f"  {case}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        collapsed = [
            f"{reason!r} ({count} rows)"
            for reason, count in sorted(by_reason.items(), key=lambda kv: str(kv[0]))
            if count > 1
        ]
        self.assertEqual(
            wrong,
            [],
            f"oc_models.discover_models diagnosed {len(wrong)} of {len(self.DIAGNOSTICS)} outcomes "
            "wrongly. The reasons are a CLOSED SET shown to the user verbatim by the wizard's "
            "`_report_catalog`, so read the grouping. "
            + (
                f"SEVERAL ROWS COLLAPSED ONTO THE SAME REASON: {', '.join(collapsed)}. That is a "
                "merge of distinct failure classes, not several independent bugs, and it points a "
                "user at the wrong problem on their own machine. "
                if collapsed
                else ""
            )
            + "FIX: a row reporting `available` TRUE after a failure is the worst case and comes "
            "first, because that is green-washed discovery: the wizard would tell the user their "
            "catalog is fine. If the POSITIVE row is the one failing, every negative row above is "
            "vacuous, since a discovery path that reported failure unconditionally satisfies all of "
            "them. A wrong reason with `available` correctly False is the mild case: the refusal "
            "works and only the explanation is wrong.\n" + "\n".join(wrong),
        )

    def test_a_successful_empty_catalog_is_unrepresentable(self):
        """Kept separate: a STRUCTURAL claim about the type, not an outcome of calling discovery.

        `available` is a derived property rather than a stored field, so "the probe succeeded and
        found zero models" cannot be CONSTRUCTED at all. The table above can only assert what
        `discover_models` returns; this asserts that the green-washed state is unreachable even by a
        caller building a catalog by hand.
        """
        self.assertFalse(
            OM.ModelCatalog(models=(), source=OM.CATALOG_SOURCE_CLI).available,
            "a catalog with no models must never report itself available, however it was built",
        )

    def test_every_diagnostic_reason_is_distinct(self):
        """Kept separate: asserts the CONSTANTS are six distinct strings, before any call is made.

        This is the precondition of the table above rather than a row in it: if two of these
        constants were ever given the same value, the table's rows would tie VACUOUSLY and its
        collapse detection would report nothing.
        """
        reasons = {
            OM.CATALOG_MISSING_BINARY,
            OM.CATALOG_TIMED_OUT,
            OM.CATALOG_NONZERO_EXIT,
            OM.CATALOG_UNPARSEABLE,
            OM.CATALOG_NO_MODELS,
            OM.CATALOG_NO_CONFIG,
        }
        self.assertEqual(
            len(reasons),
            6,
            f"the six diagnostic reasons must be six DISTINCT strings, got {sorted(reasons)}",
        )


class CatalogConfigFallbackTests(unittest.TestCase):
    """The no-secret fallback: statically declared ids, and NEVER a credential."""

    def _config_text(self) -> str:
        return json.dumps(
            {
                "provider": {
                    "example-vendor": {
                        "npm": "@ai-sdk/openai-compatible",
                        "options": {
                            "baseURL": "https://gw.example/v1",
                            "apiKey": SENTINEL_SECRET,
                        },
                        "models": {"flash-3.7": {"name": "Flash"}},
                    },
                    "example-openai": {"models": {"gpt-sol-5.6": {}}},
                }
            }
        )

    def test_only_provider_model_keys_are_read_and_no_secret_escapes(self):
        """Kept separate: calls `models_from_config` on an ALREADY-PARSED dict, no file involved.

        The `CONFIG_STATES` table goes through `catalog_from_config`, which resolves and reads a path.
        This pins the pure extraction step underneath it, which is where the credential boundary
        actually lives.
        """
        parsed = json.loads(self._config_text())
        models = OM.models_from_config(parsed)
        self.assertEqual(models, (_FLASH, _SOL))
        self.assertNotIn(SENTINEL_SECRET, "".join(models))

    def test_fallback_supplies_ids_and_still_reports_why_the_cli_failed(self):
        """Kept separate: asserts the COMPOSITION of two failures, which no single-state row can.

        The claim is that a config fallback carries the CLI's own failure reason forward: the catalog
        is available, sourced from the config, AND still reports `executable-not-found`. That is a
        property of discovery combining two sources, not of either one, so it needs both a failing
        runner and a valid config in the same call. DEGRADED IS NEVER SILENT.
        """
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "opencode.json"
            cfg.write_text(self._config_text(), encoding="utf-8")
            cat = OM.discover_models(
                runner=_RecordingRunner(raises=FileNotFoundError()),
                env={"OPENCODE_CONFIG": str(cfg)},
            )
        self.assertTrue(cat.available)
        self.assertEqual(cat.source, OM.CATALOG_SOURCE_CONFIG)
        # DEGRADED IS NEVER SILENT: the CLI reason survives into the fallback catalog.
        self.assertEqual(cat.reason, OM.CATALOG_MISSING_BINARY)
        self.assertEqual(cat.models, (_FLASH, _SOL))

    #: (case, the config file state, expected models, expected reason, why this row exists)
    #:
    #: The state is "absent" (write no file at all), "valid" (this class's own `_config_text`, which
    #: deliberately carries a sentinel credential) or a literal string to write verbatim.
    CONFIG_STATES = (
        (
            "no config file exists at the configured path",
            "absent",
            (),
            OM.CATALOG_NO_CONFIG,
            "an ABSENT config is its own reason, not unparseable and not an exception. The wizard "
            "shows this string to the user, and 'you have no config' and 'your config is broken' "
            "send them to different places",
        ),
        (
            "the config is not valid JSON",
            "{not json",
            (),
            OM.CATALOG_UNPARSEABLE,
            "a `.jsonc` or hand-damaged config must NOT raise. This path only ever ADDS ids to a "
            "catalog that already has a CLI diagnostic, so an exception here would turn a degraded "
            "discovery into a dead wizard",
        ),
        (
            "the config declares two providers with one model each",
            "valid",
            (_FLASH, _SOL),
            "",
            "POSITIVE: real ids are extracted and the reason is EMPTY. Without this row a fallback "
            "that returned nothing unconditionally would satisfy both rows above",
        ),
    )

    def test_every_config_state_yields_its_ids_and_its_reason(self):
        """One table over the config fallback's outcomes, replacing two tests and folding in a positive.

        Each of the two wrote (or omitted) a config file, called `catalog_from_config`, and asserted
        an empty tuple plus one reason constant. Only the FILE STATE differed.

        Why the table beats the two: this is one function deciding between three answers, and the
        interesting property is that it NEVER RAISES for any of them, because it is the degraded path
        a failed CLI probe falls back to. Asserting the three side by side is what makes "no config",
        "broken config" and "usable config" visibly distinct rather than three shades of empty.
        """
        wrong = []
        for case, state, expected_models, expected_reason, why in self.CONFIG_STATES:
            with tempfile.TemporaryDirectory() as d:
                cfg = Path(d) / "opencode.json"
                if state == "valid":
                    cfg.write_text(self._config_text(), encoding="utf-8")
                elif state != "absent":
                    cfg.write_text(state, encoding="utf-8")
                try:
                    models, reason = OM.catalog_from_config(
                        env={"OPENCODE_CONFIG": str(cfg)}
                    )
                except Exception as exc:  # pragma: no cover - the point of the row
                    wrong.append(
                        f"  {case}: RAISED {exc!r} instead of returning a reason. This path is the "
                        "degraded fallback, so an exception aborts the wizard\n"
                        f"    this row exists because: {why}"
                    )
                    continue
            problems = []
            if models != expected_models:
                problems.append(f"expected models {expected_models!r}, got {models!r}")
            if reason != expected_reason:
                problems.append(f"expected reason {expected_reason!r}, got {reason!r}")
            if SENTINEL_SECRET in "".join(models):
                problems.append(
                    "A CREDENTIAL LEAKED INTO THE MODEL IDS. The config carries a sentinel apiKey "
                    "and it reached the caller"
                )
            if problems:
                wrong.append(
                    f"  {case}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"oc_models.catalog_from_config mishandled {len(wrong)} of {len(self.CONFIG_STATES)} "
            "config states. One function answers all three, so several rows failing together means "
            "its branching changed rather than three bugs. FIX: a LEAKED SENTINEL is the only "
            "catastrophic outcome here and comes first, since it means the extractor walked past "
            "the model keys into a provider's options block. If the POSITIVE row is failing, the "
            "fallback supplies no ids at all and a user whose `opencode` binary is missing can no "
            "longer see any model. A row that RAISED rather than returning is worse than a wrong "
            f"reason: the degraded path must always answer.\n" + "\n".join(wrong),
        )

    def test_config_fallback_never_resolves_an_api_key(self):
        """`resolve_api_key` reads key FILES; the catalog path must never call it.

        Asserted against the CODE, with comments and docstrings stripped: a prose mention of
        `apiKey` explaining what is deliberately NOT read is exactly the documentation this
        boundary should carry, so matching raw source text would forbid the comment rather than
        the behavior. AST-based, so the check cannot be satisfied by rewording either.
        """
        import ast
        import inspect

        for fn in (OM.models_from_config, OM.catalog_from_config, OM.discover_models):
            tree = ast.parse(inspect.getsource(fn).lstrip())
            called = {
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            } | {
                node.func.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            }
            self.assertNotIn(
                "resolve_api_key", called, f"{fn.__name__} resolves a credential"
            )
            literals = {
                node.value
                for node in ast.walk(tree)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
            }
            # Docstrings are Constants too, so exclude the one that IS the docstring.
            literals.discard(ast.get_docstring(tree) or "")
            func_node = tree.body[0]
            if isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                literals.discard(ast.get_docstring(func_node) or "")
            for secret_key in ("apiKey", "options", "headers", "Authorization"):
                self.assertNotIn(
                    secret_key, literals, f"{fn.__name__} reads {secret_key!r}"
                )


# ==================================================================================================
# E-02 / V-02: filtering, paging, manual entry, variants, preview, cancellation
# ==================================================================================================


def _many_models(count: int = 200) -> tuple:
    return tuple(f"vendor{index % 4}/model-{index:03d}" for index in range(count))


class FilterAndPageTests(unittest.TestCase):
    """Every answer script through `select_model` reaches its model and says what it did.

    ONE table replaces ten tests of identical shape: build a catalog, feed a scripted answer
    sequence, assert the chosen model and one substring of what the user was shown. Only the CATALOG
    and the ANSWERS differed.

    Why the table beats the ten. `select_model` is a SINGLE LOOP whose state is (filter, page), and
    every one of these behaviors is that loop's response to one token: a number picks, `/text`
    filters, `m` escapes to manual entry, `n`/`p` page, garbage retries. Ten tests assert ten
    responses in isolation and can express no relationship between them, yet the realistic bug is in
    the SHARED index arithmetic: the absolute-numbering row and the filtered-numbering row disagree
    about what "entry 1" means on purpose, and only adjacent rows make that contrast visible. A
    regression in the offset calculation moves several rows at once, which the table reports as one
    failure showing the same wrong arithmetic repeated.

    DISCOVERY STATE IS A COLUMN, not a second table. `ManualEntryTests` was merged in for exactly
    that reason: whether the catalog is populated or dead changes only whether `select_model` enters
    the loop at all, and the plan's requirement is that exact manual entry stays reachable in BOTH
    cases. Splitting them let the working-catalog `m` row and the dead-catalog row drift apart even
    though they are two halves of one guarantee.

    WHY EACH ROW PINS ITS SHOWN SUBSTRING and not whole sentences of the menu: the page counter, the
    filter header and the boundary notice are the one identifying phrase each a user greps for. The
    rest of the menu prose is not load-bearing and is deliberately not asserted.
    """

    #: (case, the catalog's models or "dead" for a failed discovery, scripted answers, expected
    #: chosen model, substrings the user must have been shown, why this row exists)
    SELECTIONS = (
        (
            "picking entry 1 from a 200-model catalog",
            200,
            ("1",),
            "vendor0/model-000",
            ("page 1/10",),
            "an UNUSABLE CATALOG is the failure mode: 200 models must be PAGED, never dumped. The "
            "page counter proves the paging exists at all, and "
            "`test_a_page_shows_exactly_PAGE_SIZE_entries` pins the window size itself",
        ),
        (
            "paging forward then picking entry 21",
            200,
            ("n", "21"),
            "vendor0/model-020",
            ("page 2/10",),
            "NUMBERING IS ABSOLUTE ACROSS PAGES, not per-page: entry 21 is the first item of page "
            "2, i.e. catalog index 20. A per-page scheme would have returned index 0, and the user "
            "would silently configure a different model from the one they typed the number of",
        ),
        (
            "pressing p on the first page",
            200,
            ("p", "1"),
            "vendor0/model-000",
            ("Already on the first page.",),
            "paging backward is BOUNDED, not wrapped: it says so and stays put. Wrapping to the "
            "last page would make entry 1 mean something different from what is on screen",
        ),
        (
            "filtering 200 models down to the 100 matching 'model-1'",
            200,
            ("/model-1", "1"),
            "vendor0/model-100",
            ("Models (100 matching 'model-1')",),
            "SUBSTRING AND CATALOG-ORDER PRESERVING, and the deliberate contrast with the absolute "
            "row above: `model-1` matches model-100..199, so numbering RESTARTS at 1 within the "
            "FILTERED list and entry 1 is model-100, not the first item of the full catalog. The "
            "count in the header is asserted because it is what tells the user the filter worked",
        ),
        (
            "a filter that matches nothing, then picking from the restored list",
            30,
            ("/nothing-matches", "1"),
            "vendor0/model-000",
            ("No model matches",),
            "a dead-end filter is REPORTED AND RECOVERABLE: the filter is cleared so the next "
            "answer sees the whole catalog again. A loop that kept an empty filter would strand the "
            "user with no models and no way back",
        ),
        (
            "an out-of-range number, then garbage, then a valid pick",
            (_FLASH, _SOL),
            ("99", "banana", "2"),
            _SOL,
            ("out of range", "Unrecognized input"),
            "TWO DISTINCT COMPLAINTS for two distinct mistakes, and the loop survives both to accept "
            "a valid answer. One generic error for everything would leave a user guessing whether "
            "their number was too big or their input unrecognized",
        ),
        (
            "escaping to manual entry from a WORKING catalog",
            (_FLASH,),
            ("m", _INHOUSE),
            _INHOUSE,
            (),
            "THE UNREACHABLE-MODEL CASE: a private or brand-new model may be absent from a catalog "
            "that is otherwise fine, so `m` must escape to exact entry even when there is a list to "
            "pick from",
        ),
        (
            "typing an exact model when discovery is DEAD",
            "dead",
            (_INHOUSE,),
            _INHOUSE,
            (),
            "DISCOVERY-STATE COLUMN, and the other half of the guarantee above: with no catalog at "
            "all, `select_model` goes STRAIGHT to manual entry with no menu, so a user whose "
            "`opencode` binary is missing can still configure a profile. A wizard that refused here "
            "would be unable to configure a private model at all",
        ),
        (
            "two invalid manual ids, then a valid one, with discovery dead",
            "dead",
            ("no-slash", "bad;model/x", _SOL),
            _SOL,
            ("expected an exact 'provider/model' identifier",),
            "the manual path validates through the SCHEMA'S OWN grammar and shows the schema's own "
            "message, so a stored id is always launchable. Both a missing slash and an illegal "
            "character are refused, and the loop still accepts the third answer",
        ),
    )

    def test_every_answer_script_selects_its_model_and_says_what_it_did(self):
        wrong = []
        for case, models, answers, expected, shown, why in self.SELECTIONS:
            catalog = self._catalog(models)
            script = _Script(list(answers))
            io = _io(script, catalog)
            problems = []
            try:
                chosen = W.select_model(io, catalog)
            except W.WizardCancelled as exc:
                problems.append(
                    f"CANCELLED ({exc}) instead of selecting a model, so the loop rejected an "
                    "answer script it must accept"
                )
                chosen = None
            except EOFError:
                problems.append(
                    "ran out of scripted answers, which means it asked MORE questions than this "
                    "row supplies: the loop is consuming an extra turn somewhere"
                )
                chosen = None
            if chosen is not None and chosen != expected:
                problems.append(f"chose {chosen!r}, expected {expected!r}")
            missing = [needle for needle in shown if needle not in script.text]
            if missing:
                problems.append(
                    f"the user was never shown {missing!r}; what was shown was "
                    f"{script.text[-400:]!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (answers={list(answers)!r})\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"select_model mishandled {len(wrong)} of {len(self.SELECTIONS)} answer scripts. One "
            "loop over one (filter, page) state answers all of them, so read the grouping. Several "
            "rows choosing the WRONG MODEL together is the shared index arithmetic, not several "
            "bugs: compare the absolute-numbering row (entry 21 -> index 20) against the filtered "
            "row (entry 1 -> model-100), which disagree about what entry 1 means ON PURPOSE. FIX: a "
            "row that CHOSE THE WRONG MODEL is far worse than a missing substring, because the user "
            "silently gets a different model from the one they numbered, and the preview will show "
            "the wrong id as if it were their choice. A row that CANCELLED means the loop now "
            "refuses a legal answer. If the two manual-entry rows fail while the menu rows pass, "
            "exact entry has become unreachable and a private model can no longer be configured at "
            f"all, which is the plan's unreachable-model requirement regressing.\n"
            + "\n".join(wrong),
        )

    @staticmethod
    def _catalog(models) -> OM.ModelCatalog:
        """Build the row's catalog: a count of synthetic ids, an explicit tuple, or a dead one."""
        if models == "dead":
            return OM.ModelCatalog(
                source=OM.CATALOG_SOURCE_NONE, reason=OM.CATALOG_MISSING_BINARY
            )
        ids = _many_models(models) if isinstance(models, int) else models
        return OM.ModelCatalog(models=ids, source=OM.CATALOG_SOURCE_CLI)

    def test_a_page_shows_exactly_PAGE_SIZE_entries(self):
        """Kept separate: COUNTS the emitted lines, rather than matching a substring of them.

        The table's paging rows prove the counter says `page 1/10`; this proves the window actually
        holds `PAGE_SIZE` entries. A renderer that printed the right counter above all 200 models
        would satisfy every table row while dumping exactly what the paging exists to prevent.
        """
        catalog = OM.ModelCatalog(
            models=_many_models(200), source=OM.CATALOG_SOURCE_CLI
        )
        script = _Script(["1"])
        W.select_model(_io(script, catalog), catalog)
        listed = [line for line in script.lines if line.strip().startswith("[")]
        self.assertEqual(
            len(listed),
            W.PAGE_SIZE,
            f"a page must show exactly PAGE_SIZE ({W.PAGE_SIZE}) entries; {len(listed)} were "
            "printed, so a 200-model catalog is being dumped rather than paged",
        )

    def test_filter_models_is_case_insensitive_substring_and_order_preserving(self):
        """Kept separate: a PURE function over a list, with no wizard loop, no script, no IO.

        `select_model`'s filter rows go through the whole interactive loop; this pins
        `filter_models` itself, including the two cases the loop can never show (an empty needle
        returning everything, and a needle matching nothing returning an empty tuple rather than
        the input).
        """
        models = (_FLASH, _INHOUSE, _SOL)
        self.assertEqual(W.filter_models(models, "FLASH"), (_FLASH,))
        self.assertEqual(W.filter_models(models, "example"), models)
        self.assertEqual(W.filter_models(models, "zzz"), ())
        self.assertEqual(W.filter_models(models, ""), models)

    def test_the_dead_catalog_report_names_the_reason_it_failed(self):
        """Kept separate: asserts over `_report_catalog`, a DIFFERENT function from `select_model`.

        DEGRADED IS NEVER SILENT: when discovery failed, the reason must reach the user's screen.
        The table's dead-catalog rows prove selection still works; this proves the user is told why
        there is no list, which is the green-washing half of the requirement.
        """
        catalog = OM.ModelCatalog(
            source=OM.CATALOG_SOURCE_NONE, reason=OM.CATALOG_MISSING_BINARY
        )
        script = _Script([])
        W._report_catalog(_io(script, catalog), catalog)
        self.assertIn(
            OM.CATALOG_MISSING_BINARY,
            script.text,
            "a failed discovery must NAME its reason on screen rather than presenting an empty "
            f"catalog as normal; the user saw {script.text!r}",
        )


class ManualEntryTests(unittest.TestCase):
    def test_manual_entry_gives_up_after_a_bounded_number_of_attempts(self):
        """Kept out of the selection table: an assertRaises test, and about TERMINATION not choice.

        Every row of `FilterAndPageTests.SELECTIONS` ends in a chosen model. This one asserts the
        opposite, that a script of nothing but invalid answers RAISES rather than looping forever,
        which is a claim about the retry bound rather than about which model comes back.
        """
        catalog = OM.ModelCatalog(
            source=OM.CATALOG_SOURCE_NONE, reason=OM.CATALOG_NO_MODELS
        )
        script = _Script(["bad"] * (W.MAX_ATTEMPTS + 2))
        with self.assertRaises(W.WizardCancelled):
            W.select_model(_io(script, catalog), catalog)


#: The menu position of "enter an exact custom variant", derived rather than hard-coded so adding a
#: common variant cannot silently change which option the tables below are choosing.
_CUSTOM_VARIANT_CHOICE = str(len(W.COMMON_VARIANTS) + 2)


class VariantTests(unittest.TestCase):
    """Every variant answer produces the field the profile stores, or NO field at all.

    ONE table replaces six tests: feed an answer sequence to `select_variant` and assert the returned
    variant plus, sometimes, one substring of the menu.

    Why the table beats the six. THE CRITICAL DISTINCTION IS BETWEEN `None` AND A STRING, and it is
    only legible when both sit in one table. "Provider default" must store NO VARIANT rather than a
    guessed word like `medium`, because the stored field becomes a literal `--variant` flag on a real
    launch: writing a guess there would send a flag the user never chose to a provider that may
    reject it. Six tests assert six returns separately; the table shows the `None` rows and the
    string rows against each other, so a regression that made the default store `"medium"` reads as
    the contract violation it is rather than as one odd test.

    THE COMMON VARIANTS ARE ROWS, NOT A LOOP, on purpose: the old test looped `COMMON_VARIANTS` with
    `enumerate(..., start=2)`, which re-derived the menu offset from the same constant it was
    checking, so an off-by-one in the menu numbering would have moved the expectation with it. The
    rows below name their menu number LITERALLY, which is what a user actually types.
    """

    #: (case, scripted answers, expected variant (None means NO variant stored), substrings the
    #: user must have been shown, why this row exists)
    VARIANTS = (
        (
            "choosing the explicit provider-default option",
            ("1",),
            None,
            ("Provider default (store no variant)",),
            "OPTION 1 STORES NOTHING. This is the row the whole table exists around: an "
            "overclaimed variant would put a flag on every launch that the user never chose, and "
            "the only honest representation of 'whatever this model does by default' is no field",
        ),
        (
            "pressing Enter at the variant question",
            ("",),
            None,
            (),
            "EMPTY INPUT TAKES OPTION 1, so the cheapest possible answer is also the safest one. "
            "The prompt renders as `Variant [1]:`, and this is what makes that bracket true",
        ),
        (
            "choosing menu entry 2",
            ("2",),
            "low",
            (),
            "the first common variant. Its menu number is written LITERALLY rather than derived "
            "from COMMON_VARIANTS, so a renumbered menu fails instead of moving the expectation",
        ),
        ("choosing menu entry 3", ("3",), "medium", "the second common variant"),
        ("choosing menu entry 4", ("4",), "high", "the third common variant"),
        (
            "choosing menu entry 5",
            ("5",),
            "max",
            "the LAST common variant, so the boundary between the listed words and the custom "
            "option is covered on both sides",
        ),
        (
            "choosing the custom option and typing an exact value",
            (_CUSTOM_VARIANT_CHOICE, "ultra-2"),
            "ultra-2",
            (),
            "AN UNLISTED VARIANT MUST BE ACCEPTABLE, preserved VERBATIM. The menu's words are not "
            "exhaustive (OpenCode calls the flag provider-specific), so a wizard that only offered "
            "its own four words could not configure a provider using any other",
        ),
        (
            "typing an invalid custom value, then a valid one",
            (_CUSTOM_VARIANT_CHOICE, "bad value!", "high"),
            "high",
            ("invalid variant",),
            "the custom value is validated by the SCHEMA'S OWN validator and its message is shown, "
            "so a stored variant is always one the profile schema would accept. The loop then "
            "survives to take the next answer rather than cancelling",
        ),
    )

    def test_every_variant_answer_stores_the_field_it_should(self):
        wrong = []
        none_rows = sum(1 for row in self.VARIANTS if row[2] is None)
        for row in self.VARIANTS:
            # Rows with nothing to assert about the menu omit the substrings column entirely.
            if len(row) == 4:
                case, answers, expected, why = row
                shown = ()
            else:
                case, answers, expected, shown, why = row
            script = _Script(list(answers))
            problems = []
            try:
                got = W.select_variant(_io(script), _FLASH)
            except W.WizardCancelled as exc:
                problems.append(f"CANCELLED ({exc}) instead of answering")
                got = "<cancelled>"
            if got != expected and got != "<cancelled>":
                if expected is None:
                    problems.append(
                        f"expected NO variant (None) but it stored {got!r}. A stored variant "
                        "becomes a literal --variant flag on every launch, so this is an "
                        "overclaimed variant, not a cosmetic difference"
                    )
                elif got is None:
                    problems.append(
                        f"expected {expected!r} but it stored NOTHING, so the user's explicit "
                        "choice was silently dropped and the provider default will be used"
                    )
                else:
                    problems.append(f"expected {expected!r}, got {got!r}")
            missing = [needle for needle in shown if needle not in script.text]
            if missing:
                problems.append(f"the user was never shown {missing!r}")
            if problems:
                wrong.append(
                    f"  {case} (answers={list(answers)!r})\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"select_variant stored the wrong field for {len(wrong)} of {len(self.VARIANTS)} answer "
            f"scripts ({none_rows} of the rows expect NO variant at all). One menu and one parse "
            "answer all of them, so read the grouping. Every NUMBERED row failing together means "
            "the menu was renumbered, and the numbers in this table are what a user types. FIX: "
            "check the None-versus-string direction FIRST. A row expecting None that now stores a "
            "word is an OVERCLAIMED VARIANT, which puts a flag the user never chose onto every "
            "launch of that profile and may be rejected outright by their provider. A row expecting "
            "a word that now stores None is the mirror: the user's explicit choice was discarded in "
            f"silence.\n" + "\n".join(wrong),
        )

    def test_the_menu_does_not_overclaim_what_a_variant_means(self):
        """Kept separate: asserts about the MENU'S HONESTY, a claim no return value can carry.

        The table's rows all assert what comes BACK from a given answer. This asserts what the user
        is TOLD before answering, namely that variants are provider-specific and that a provider may
        accept none of the listed words. A menu presenting the four words as universally valid would
        satisfy every table row while misleading the user about what they are choosing.
        """
        script = _Script(["1"])
        W.select_variant(_io(script), _FLASH)
        for phrase in ("provider-specific", "a provider may accept none of these"):
            self.assertIn(
                phrase,
                script.text,
                f"the variant menu must say {phrase!r} rather than presenting its four words as "
                "universally accepted",
            )

    def test_the_field_validator_routes_through_the_public_schema_api(self):
        """Kept separate: includes an assertRaises, and tests the validator directly rather than a flow.

        `validate_optional_field` is the seam the wizard shares with the profile schema, and this
        pins both directions (a valid variant and agent pass through unchanged; an invalid agent
        raises the SCHEMA'S OWN error type). The raising half cannot be a row in a table whose every
        row returns a value.
        """
        self.assertEqual(W.validate_optional_field("variant", "high", _FLASH), "high")
        self.assertEqual(W.validate_optional_field("agent", "build", _FLASH), "build")
        with self.assertRaises(RP.ProfileSchemaError):
            W.validate_optional_field("agent", "not a token", _FLASH)


class PreviewTests(unittest.TestCase):
    """The preview shows the EXACT profile and the EXACT launch it expands to.

    ONE table replaces four tests: build a profile, render it, assert some substrings are present
    and (in one case) that a flag is ABSENT.

    Why the table beats the four. The preview's only job is to be EXACT, and the way a preview goes
    wrong is not by omitting a line but by SHOWING A FIELD THE PROFILE DOES NOT HAVE. The
    `forbidden` column is therefore load-bearing rather than decorative: the row where a profile
    stores no variant asserts that `--variant` appears NOWHERE in the block, which is the one thing a
    presence-only check can never catch. Four tests put the positive and negative halves of that
    claim in different methods; the table puts the fully-specified profile and the bare one side by
    side, where a preview that invented a default variant fails visibly against both.

    ARGV AND RENDERED TEXT ARE A CHECK-MODE COLUMN, not two tables: `opencode_argv_fields` and
    `preview_lines` are the same claim at two levels (the flag list, and the block a user reads), and
    the argv rows pin the EXACT LIST because flag ORDER mirrors `oc_runipd.run_opencode`. Pinning the
    list rather than substrings is what makes the preview the real expansion rather than a
    plausible-looking one.
    """

    #: (case, the profile, check mode, expectation, substrings that must be ABSENT, why)
    #:
    #: Check mode is "argv" (the expectation is the EXACT flag list `opencode_argv_fields` returns)
    #: or "lines" (the expectation is a tuple of substrings the rendered block must contain).
    PREVIEWS = (
        (
            "a fully specified profile expands to every flag in the runner's order",
            RP.LaunchProfile(runner="oc", model=_FLASH, variant="high", agent="build"),
            "argv",
            ["--model", _FLASH, "--variant", "high", "--agent", "build"],
            (),
            "the ORDER mirrors `oc_runipd.run_opencode` (--model, then --variant, then --agent), so "
            "the preview is the REAL expansion. The whole list is pinned, not sampled: a reordered "
            "or duplicated flag is exactly what a substring check would miss",
        ),
        (
            "a model-only profile emits no other flag at all",
            RP.LaunchProfile(runner="oc", model=_FLASH),
            "argv",
            ["--model", _FLASH],
            (),
            "AN ABSENT FIELD PRINTS NOTHING, which is what the runner does: pass no argument and "
            "let the host use its own default. An empty `--variant ''` would be a flag the user "
            "never chose",
        ),
        (
            "a profile with a variant but no agent renders both fields and the launch line",
            RP.LaunchProfile(runner="oc", model=_INHOUSE, variant="max"),
            "lines",
            (
                f"model:   {_INHOUSE}",
                "variant: max",
                "agent:   (none)",
                f"opencode run --model {_INHOUSE} --variant max",
            ),
            (),
            "the block shows the STORED FIELDS and the EQUIVALENT LAUNCH together, so a user can see "
            "both what is written to disk and what it will do. An unset field reads `(none)` rather "
            "than being omitted, so the user knows the wizard asked and they declined",
        ),
        (
            "a profile with no variant says so and emits no variant flag",
            RP.LaunchProfile(runner="oc", model=_FLASH),
            "lines",
            ("variant: (provider default)",),
            ("--variant",),
            "THE NEGATIVE HALF, and the reason this is one table: `(provider default)` must be shown "
            "AS SUCH rather than as a guessed word, and `--variant` must appear NOWHERE in the "
            "block. A preview that invented a default would satisfy every presence check above",
        ),
    )

    def test_every_profile_previews_its_exact_fields_and_launch(self):
        wrong = []
        for case, profile, mode, expectation, forbidden, why in self.PREVIEWS:
            problems = []
            if mode == "argv":
                got = W.opencode_argv_fields(profile)
                if got != expectation:
                    problems.append(f"expected argv {expectation!r}, got {got!r}")
                haystack = " ".join(got)
            else:
                assert mode == "lines", f"unknown check mode {mode!r}"
                haystack = "\n".join(W.preview_lines("sonnet", profile))
                missing = [needle for needle in expectation if needle not in haystack]
                if missing:
                    problems.append(
                        f"the block is missing {missing!r}; it rendered as {haystack!r}"
                    )
            leaked = [needle for needle in forbidden if needle in haystack]
            if leaked:
                problems.append(
                    f"LEAKED {leaked!r}: the preview is showing a field this profile does not "
                    f"store, so it is overclaiming. Rendered: {haystack!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the preview is wrong for {len(wrong)} of {len(self.PREVIEWS)} profiles. One argv "
            "builder feeds both the flag list and the launch line in the rendered block, so an argv "
            "row and a lines row failing together is that builder rather than the renderer. FIX: a "
            "LEAKED substring is the serious failure. `--variant` appearing for a profile that "
            "stores no variant means the preview is promising the user a flag their launch will not "
            "carry (or worse, that their profile will now silently carry), which defeats the entire "
            "point of showing an exact preview before asking them to save. A reordered argv list is "
            "the subtler one: it still contains every flag, so only the exact-list comparison "
            f"catches it, and the preview would stop matching the real launch.\n"
            + "\n".join(wrong),
        )


class ProfileNameTests(unittest.TestCase):
    """The name question enforces the SCHEMA'S grammar and the no-clobber rule, and retries.

    ONE table replaces three tests: seed a config, feed a name sequence, assert the accepted name and
    one substring of the complaint.

    Why the table beats the three. All three exercise the same retry loop, and the decisive column is
    `replace`: the SAME answer (`gem`, against a config that already has `gem`) must be REFUSED
    without it and ACCEPTED with it. Splitting those into separate methods hides that they are one
    rule read two ways, and it is the rule that matters here, because overwriting a profile the user
    forgot about is how a run silently moves onto a different, possibly far more expensive, model.
    """

    #: (case, the existing profile names to seed, answers, replace flag, expected accepted name,
    #: the complaint substring the user must have seen, why this row exists)
    NAMES = (
        (
            "an invalid name then a reserved word then a good one",
            (),
            ("Bad Name", "as", "gem"),
            False,
            "gem",
            "reserved",
            "the grammar is the SCHEMA'S OWN, not a local copy, so a name the wizard accepts is "
            "always a name the store accepts. Both an illegal spelling and a RESERVED word are "
            "refused, and the loop survives to take the third answer rather than cancelling",
        ),
        (
            "reusing an existing name WITHOUT replace",
            ("gem",),
            ("gem", "sol"),
            False,
            "sol",
            "already exists",
            "THE NO-CLOBBER RULE, matching `runner_profiles.add_profile`: overwriting `gem` because "
            "the user forgot it existed is how a run ends up on an unintended, possibly far more "
            "expensive model. The complaint must name the collision so the user can choose",
        ),
        (
            "reusing an existing name WITH replace",
            ("gem",),
            ("gem",),
            True,
            "gem",
            None,
            "THE REPLACE COLUMN, and why this is one table: the identical answer against the "
            "identical config must be ACCEPTED here. Without this row the rule above could be "
            "implemented as 'always refuse an existing name', which would break `--replace` "
            "entirely while still passing",
        ),
    )

    def test_every_name_answer_is_accepted_or_refused_by_the_rule(self):
        wrong = []
        for case, existing, answers, replace, expected, complaint, why in self.NAMES:
            cfg = RP.empty_config()
            for name in existing:
                cfg = RP.add_profile(
                    cfg, name, RP.LaunchProfile(runner="oc", model=_FLASH)
                )
            script = _Script(list(answers))
            problems = []
            try:
                got = W.ask_profile_name(_io(script), cfg, replace=replace)
            except W.WizardCancelled as exc:
                problems.append(f"CANCELLED ({exc}) instead of accepting a name")
                got = None
            if got is not None and got != expected:
                problems.append(f"accepted {got!r}, expected {expected!r}")
            if complaint is not None and complaint not in script.text:
                problems.append(
                    f"the user was never told {complaint!r}; they saw {script.text!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (answers={list(answers)!r}, replace={replace})\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"ask_profile_name mishandled {len(wrong)} of {len(self.NAMES)} answer scripts. One "
            "retry loop and one no-clobber check answer all of them. FIX: read the two `gem` rows "
            "TOGETHER, since they differ only in `replace`. If the without-replace row now ACCEPTS "
            "`gem`, the no-clobber rule is gone and the wizard will silently overwrite a profile the "
            "user forgot about, moving their runs onto a different model. If the WITH-replace row "
            "now refuses, `--replace` is broken and an existing profile can never be updated. Both "
            f"passing while the grammar row fails is the mild case: only validation moved.\n"
            + "\n".join(wrong),
        )


class YesNoTests(unittest.TestCase):
    """The yes/no primitive: every answer shape, and the two that must CANCEL rather than answer.

    ONE table replaces three tests plus the prompt-rendering one. The decisive design point is that
    the outcome column is a CHECK MODE rather than a bool: `True`, `False` and CANCEL are three
    outcomes, and collapsing the cancel rows into "returns False" would destroy the exact property
    that matters. An unattended pipe hitting EOF must not silently accept; it must raise, so no
    change is ever made on behalf of a user who was never there.
    """

    #: (case, scripted answers, rendered default, expected outcome, why this row exists)
    #:
    #: The expected outcome is True, False, or the string "cancel" for "must raise WizardCancelled".
    ANSWERS = (
        (
            "pressing Enter with a NO default",
            ("",),
            False,
            False,
            "EMPTY INPUT TAKES THE RENDERED DEFAULT. Paired with the row below, this is what makes "
            "the default a real setting rather than a hard-coded answer",
        ),
        (
            "pressing Enter with a YES default",
            ("",),
            True,
            True,
            "the same input with the opposite default must give the opposite answer. Without this "
            "row a function that always returned False would satisfy the row above",
        ),
        (
            "answering y",
            ("y",),
            False,
            True,
            "an explicit yes OVERRIDES a no default, which is the whole point of asking",
        ),
        (
            "answering the long form yes",
            ("yes",),
            False,
            True,
            "`yes` is accepted as well as `y`, because a user typing the word out is not making a "
            "mistake",
        ),
        (
            "answering n against a YES default",
            ("n",),
            True,
            False,
            "an explicit no OVERRIDES a yes default. This is the row that protects every "
            "default-YES question in the wizard: the user can always decline",
        ),
        (
            "answering the long form no",
            ("no",),
            True,
            False,
            "`no` as well as `n`, for the same reason as `yes`",
        ),
        (
            "an uppercase Y",
            ("Y",),
            False,
            True,
            "the answer is CASE-INSENSITIVE; a user holding shift has not cancelled",
        ),
        (
            "end of input",
            (),
            False,
            "cancel",
            "EOF IS A CANCEL, NOT A SILENT ANSWER, and this is the most important row here. An "
            "unattended pipe reaching end of input must raise rather than return, so no change is "
            "ever made on behalf of a user who was not there to make it. It must hold whichever way "
            "the default points, which is why the outcome is CANCEL rather than `False`",
        ),
        (
            "a quit word",
            ("q",),
            False,
            "cancel",
            "`q` cancels from ANY question, so a user who changes their mind mid-interview has an "
            "exit that is not an answer",
        ),
    )

    def test_every_answer_shape_resolves_or_cancels(self):
        wrong = []
        for case, answers, default, expected, why in self.ANSWERS:
            script = _Script(list(answers))
            try:
                got = W.ask_yes_no(_io(script), "Q?", default=default)
            except W.WizardCancelled:
                got = "cancel"
            if got != expected:
                detail = (
                    f"expected it to CANCEL, but it returned {got!r}. That is an answer given on "
                    "behalf of a user who never gave one"
                    if expected == "cancel"
                    else (
                        f"expected {expected!r}, got {got!r}"
                        if got != "cancel"
                        else f"expected {expected!r}, but it CANCELLED"
                    )
                )
                wrong.append(
                    f"  {case} (answers={list(answers)!r}, default={default})\n"
                    f"    - {detail}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"ask_yes_no mishandled {len(wrong)} of {len(self.ANSWERS)} answer shapes. FIX: a CANCEL "
            "row that now RETURNS is the dangerous direction and comes first. EOF or a quit word "
            "resolving to a bool means an unattended pipe, or a user who typed `q`, can be taken as "
            "having answered a save question, and every byte-identical guarantee in this suite rests "
            "on that not happening. Rows sharing a DEFAULT failing together means the default is "
            "being ignored; rows sharing an ANSWER WORD failing together means the parse changed.\n"
            + "\n".join(wrong),
        )

    def test_the_rendered_default_is_explicit_in_the_prompt(self):
        """Kept separate: asserts about the PROMPT TEXT, not about the value returned.

        Every table row above asserts what an answer resolves TO. This asserts that the user can SEE
        which answer Enter will give, before giving it. A function that honored its default perfectly
        while rendering a bare `Q?` would satisfy the whole table and still leave the user guessing.
        """
        script = _Script([""])
        W.ask_yes_no(_io(script), "Q?", default=False)
        self.assertTrue(
            any("[y/N]" in prompt for prompt in script.prompts),
            f"a NO default must render as [y/N] so Enter's meaning is visible; got {script.prompts}",
        )


# ==================================================================================================
# The full interview (E-02) and the default questions (E-04)
# ==================================================================================================

# One complete happy-path answer script: name, model pick, provider-default variant, no agent, save
_SAVE_ANSWERS = ["gem", "1", "1", "", "y"]


class InterviewTests(unittest.TestCase):
    """A whole interview round-trips its answers into the exact profile the store receives.

    ONE table replaces three tests: run the full interview with an answer script and assert the
    profile that reached the injected store. Only the SCRIPT, the CATALOG and the PRESEEDED NAME
    differed.

    Why the table beats the three. These are END-TO-END rows, and what they are really asserting is
    that no answer is LOST OR SUBSTITUTED between the question and the stored field. That property is
    only visible when the rows disagree: the discovered row stores `None` for variant and agent while
    the manual row stores real strings for both, so a wizard that dropped the optional fields (or one
    that invented values for them) fails exactly one of the two rather than both. Three separate
    tests could not express that contrast, and the previous framing hid it, since the row that stored
    two `None`s read as a weaker version of the row that stored two strings rather than as its
    deliberate opposite.

    THE DISCOVERY STATE AND THE PRESEEDED NAME ARE COLUMNS, because both change only HOW MANY
    QUESTIONS are asked, not what is stored. Each row's answer script is exactly as long as the
    questions it expects, so a wizard that asked one question too many hits EOF and cancels, which
    the loop reports rather than silently reusing an answer.
    """

    #: (case, the catalog or "dead", preseeded name or None, scripted answers, expected
    #: (name, model, variant, agent) as stored, why this row exists)
    ROUND_TRIPS = (
        (
            "a discovered model with no variant and no agent",
            None,
            None,
            _SAVE_ANSWERS + ["n", "n"],
            ("gem", _FLASH, None, None),
            "THE ALL-DEFAULTS PATH, and the deliberate opposite of the row below: picking entry 1 "
            "from the catalog, taking the provider default variant, and pressing Enter at the agent "
            "question must store the model and NOTHING ELSE. Two stored `None`s are the assertion, "
            "not an absence of one: a wizard that substituted a guessed variant would fail here and "
            "pass the next row",
        ),
        (
            "a manually typed model with a custom variant and an agent, discovery dead",
            "dead",
            None,
            [
                "sonnet",
                _INHOUSE,
                _CUSTOM_VARIANT_CHOICE,
                "ultra",
                "build",
                "y",
                "n",
                "n",
            ],
            ("sonnet", _INHOUSE, "ultra", "build"),
            "EVERY OPTIONAL FIELD POPULATED, through the hardest route: discovery is dead, so the "
            "model is typed exactly, the variant is a custom value not on the menu, and an agent is "
            "bound. All three must survive into the stored profile VERBATIM, since each becomes a "
            "literal flag on a real launch",
        ),
        (
            "a preseeded name skips the name question",
            None,
            "sol",
            ["1", "1", "", "y", "n", "n"],
            ("sol", _FLASH, None, None),
            "THE PRESEEDED-NAME COLUMN: a caller supplying the name must not be asked for it. The "
            "script is one answer SHORTER than the first row's, so if the question were asked anyway "
            "the interview would run out of input and cancel, which is what proves the skip",
        ),
    )

    def test_every_interview_stores_exactly_the_profile_its_answers_describe(self):
        wrong = []
        for case, catalog, preseed, answers, expected, why in self.ROUND_TRIPS:
            cat = (
                OM.ModelCatalog(
                    source=OM.CATALOG_SOURCE_NONE, reason=OM.CATALOG_MISSING_BINARY
                )
                if catalog == "dead"
                else catalog
            )
            store = _Store()
            script = _Script(list(answers))
            result = W.run_wizard(_io(script, catalog=cat, store=store), preseed)
            problems = []
            if not result.saved:
                problems.append(
                    f"the interview did not save (reason={result.reason!r}). A reason of "
                    "`cancelled` means it asked MORE questions than this row answers, so an extra "
                    "question was introduced somewhere"
                )
            elif len(store.writes) != 1:
                problems.append(f"expected exactly ONE write, got {len(store.writes)}")
            else:
                written = store.writes[0]
                name = expected[0]
                if result.name != name:
                    problems.append(
                        f"the result names the profile {result.name!r}, expected {name!r}"
                    )
                if name not in written.profiles:
                    problems.append(
                        f"the written config has no profile {name!r}; it has "
                        f"{sorted(written.profiles)}"
                    )
                else:
                    saved = written.profiles[name]
                    got = (saved.model, saved.variant, saved.agent)
                    if got != expected[1:]:
                        problems.append(
                            f"stored (model, variant, agent) expected {expected[1:]!r}, got {got!r}"
                        )
            if preseed is not None and any(
                "Profile name" in prompt for prompt in script.prompts
            ):
                problems.append(
                    "the name question was asked even though the caller preseeded the name"
                )
            if problems:
                wrong.append(
                    f"  {case}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.ROUND_TRIPS)} interviews stored a profile that does not "
            "match the answers given. These are END-TO-END rows, so a failure here can come from any "
            "question in the chain, and the per-question tables above are where to look next "
            "(`select_model`, `select_variant`, `ask_profile_name`). FIX: compare the two rows that "
            "DISAGREE about the optional fields. If the all-defaults row now stores a variant or an "
            "agent, the wizard is inventing values the user declined, and every launch of that "
            "profile will carry a flag they never chose. If the fully populated row stores `None` "
            "for one of them, an explicit answer is being dropped between the question and the "
            "store. A row that CANCELLED rather than saving means the question count changed: each "
            f"script is exactly as long as the questions its row expects.\n"
            + "\n".join(wrong),
        )

    def test_the_preview_precedes_the_save_question(self):
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        W.run_wizard(_io(script, store=_Store()))
        preview_index = next(
            i
            for i, line in enumerate(script.lines)
            if "Equivalent OpenCode launch:" in line
        )
        save_prompt_index = next(
            i for i, prompt in enumerate(script.prompts) if "Save profile" in prompt
        )
        self.assertGreater(len(script.lines), preview_index)
        self.assertGreaterEqual(save_prompt_index, 4)

    def test_an_existing_preseeded_name_refuses_without_replace_and_writes_nothing(
        self,
    ):
        """Kept separate: the interview REFUSES BEFORE ASKING ANYTHING, so it has no answer script.

        Every `ROUND_TRIPS` row answers questions and ends in a stored profile. This one supplies an
        EMPTY script deliberately: a preseeded name that already exists must be refused up front,
        with no questions asked at all, which is what the empty script proves. Folding it in would
        mean a row whose expected profile is nothing and whose answers are nothing.
        """
        cfg = RP.add_profile(
            RP.empty_config(), "gem", RP.LaunchProfile(runner="oc", model=_SOL)
        )
        store = _Store(cfg)
        result = W.run_wizard(_io(_Script([]), store=store), "gem")
        self.assertFalse(result.saved)
        self.assertEqual(result.reason, "exists")
        self.assertEqual(store.writes, [], "a refused name must not reach the writer")


class SaveOutcomeTests(unittest.TestCase):
    """Every way the interview can END: what it reports, and whether it wrote ANYTHING.

    ONE table replaces nine tests across two classes. Each of the nine ran `run_wizard` with one
    answer script and asserted `saved`, a `reason`, and whether the injected store was called. Only
    the SCRIPT and the expected verdict differed.

    Why the table beats the nine, and why the two classes had to merge. THE SAFETY PROPERTY IS A
    PARTITION, not nine independent facts: exactly one path writes, and every other path must leave
    the store untouched. `SaveQuestionDefaultsToYesTests` held the one WRITING row while
    `NonSaveWritesNothingTests` held the non-writing ones, so the polarity flip of 2026-09-12 (the
    save question now defaults YES) had to be argued across two classes, each carrying a docstring
    explaining what the other did. With the rows adjacent, the claim is checkable in one place: the
    Enter row SAVES, and the explicit-`n`, quit, EOF and interrupt rows do not, which is precisely
    what makes a default-YES question safe rather than reckless.

    THE WRITE COUNT IS ASSERTED ON EVERY ROW, not just the saving one. `writes` is a list on the
    injected store, so "wrote exactly once" and "never wrote" are the same assertion with a different
    number, and a second write would be caught even on a row that legitimately saves. That matters
    because the defaults are supposed to land in the SAME atomic write as the profile.

    REASON CODES ARE LOAD-BEARING and are asserted EXACTLY: callers in `cli.py` branch on them, so
    `declined` degrading into `cancelled` would make a user who answered `n` look like a user who
    walked away.
    """

    #: (case, scripted answers, interrupt_at, expected saved, expected reason, expected write count,
    #: expected cancelled, why this row exists)
    OUTCOMES = (
        (
            "the full happy path with an explicit y",
            _SAVE_ANSWERS + ["n", "n"],
            None,
            True,
            "",
            1,
            False,
            "POSITIVE, and the anchor of the whole table: a completed interview writes EXACTLY ONCE "
            "and reports no reason. Every non-writing row below is vacuous against a wizard that "
            "never writes at all",
        ),
        (
            "pressing Enter at the save question",
            ["gem", "1", "1", "", ""] + ["n", "n"],
            None,
            True,
            "",
            1,
            False,
            "THE SAVE QUESTION DEFAULTS YES (maintainer request 2026-09-12): by this point the user "
            "has picked a model, a variant and an agent and seen a preview, so Enter completes the "
            "thing they were doing. This row is what the four cancel rows below make safe",
        ),
        (
            "answering n at the save question",
            ["gem", "1", "1", "", "n"],
            None,
            False,
            "declined",
            0,
            False,
            "DECLINING MUST BE EXPLICIT now that the default is YES, and it is NOT a cancellation: "
            "`cancelled` stays False because the user completed the interview and chose no. A caller "
            "branching on the reason must be able to tell 'decided against' from 'walked away'",
        ),
        (
            "typing a quit word at the save question",
            ["gem", "1", "1", "", "q"],
            None,
            False,
            "cancelled",
            0,
            True,
            "a quit word at the LAST question still writes nothing, so a user who changes their mind "
            "after seeing the preview is obeyed",
        ),
        (
            "running out of input before the save question",
            ["gem", "1"],
            None,
            False,
            "cancelled",
            0,
            True,
            "EOF IS A CANCEL, which is the row that makes the default-YES save question safe in an "
            "unattended pipe: a script that pipes two answers and stops must not have a profile "
            "written on its behalf by a default it never saw",
        ),
        (
            "a keyboard interrupt part way through",
            _SAVE_ANSWERS,
            2,
            False,
            "cancelled",
            0,
            True,
            "Ctrl-C mid-interview is caught and turned into a clean cancel with no write, rather "
            "than escaping as a traceback that leaves the user unsure what was saved",
        ),
        (
            "an unreadable existing config",
            [],
            None,
            False,
            "unreadable-config",
            0,
            False,
            "A BROKEN CONFIG IS REPORTED, NEVER TREATED AS EMPTY. Silently starting from an empty "
            "config would let the single write DESTROY every profile in a file that merely failed to "
            "parse, which is the most destructive outcome available to this code",
        ),
    )

    def test_every_ending_reports_itself_and_writes_only_when_it_should(self):
        wrong = []
        wrote = 0
        for (
            case,
            answers,
            interrupt_at,
            expect_saved,
            expect_reason,
            expect_writes,
            expect_cancelled,
            why,
        ) in self.OUTCOMES:
            store = _Store()
            script = _Script(list(answers), interrupt_at=interrupt_at)
            if expect_reason == "unreadable-config":

                def _bad_load():
                    raise RP.ProfileSchemaError(
                        "runner-profiles.json is not valid JSON"
                    )

                io = W.WizardIO(
                    ask=script.ask,
                    emit=script.emit,
                    discover=lambda: OM.ModelCatalog(
                        models=(_FLASH,), source=OM.CATALOG_SOURCE_CLI
                    ),
                    load=_bad_load,
                    save=store.save,
                )
            else:
                io = _io(script, store=store)
            result = W.run_wizard(io)
            wrote += len(store.writes)
            problems = []
            if result.saved is not expect_saved:
                problems.append(f"`saved` expected {expect_saved}, got {result.saved}")
            if result.reason != expect_reason:
                problems.append(
                    f"`reason` expected {expect_reason!r}, got {result.reason!r}. Callers in "
                    "cli.py branch on this code, so it is not cosmetic"
                )
            if len(store.writes) != expect_writes:
                problems.append(
                    f"the writer was called {len(store.writes)} time(s), expected {expect_writes}"
                    + (
                        ". A PATH THAT MUST NOT WRITE WROTE ANYWAY"
                        if expect_writes == 0
                        else ""
                    )
                )
            if result.cancelled is not expect_cancelled:
                problems.append(
                    f"`cancelled` expected {expect_cancelled}, got {result.cancelled}"
                )
            if problems:
                wrong.append(
                    f"  {case}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"run_wizard mishandled {len(wrong)} of {len(self.OUTCOMES)} endings; the writer was "
            f"called {wrote} time(s) across the whole table, and exactly 2 of "
            f"{len(self.OUTCOMES)} rows may legitimately write. FIX: AN UNEXPECTED WRITE IS THE "
            "SERIOUS FAILURE and comes first, whatever else is red, because it means the wizard "
            "changed a user's stored configuration on a path where they declined, cancelled, or "
            "were never present. The EOF row is the one to read if the save question's default was "
            "just changed: a default-YES save question is only safe because EOF cancels instead of "
            "accepting it. If the two SAVING rows fail while the rest pass, the wizard has stopped "
            "writing entirely and every non-writing row above is passing vacuously. A wrong REASON "
            "with the right write count is the mild case: the effect is correct and only the code a "
            f"caller branches on moved.\n" + "\n".join(wrong),
        )

    def test_the_save_prompt_renders_the_yes_default(self):
        """Kept separate: asserts about the PROMPT TEXT, not about the outcome of answering.

        The table proves Enter SAVES. This proves the user could SEE that it would, which is a
        different claim: a wizard honoring a YES default while rendering `[y/N]` would satisfy every
        table row while actively misleading the person pressing Enter.
        """
        script = _Script(["gem", "1", "1", "", ""] + ["n", "n"])
        W.run_wizard(_io(script, store=_Store()))
        save_prompts = [p for p in script.prompts if "Save profile" in p]
        self.assertTrue(save_prompts, f"no save prompt was rendered: {script.prompts}")
        self.assertIn(
            "[Y/n]",
            save_prompts[0],
            "the save question defaults YES, so it must RENDER as [Y/n]; showing [y/N] while "
            f"treating Enter as yes would mislead the user. Got {save_prompts[0]!r}",
        )

    def test_a_write_failure_is_reported_and_not_claimed_as_saved(self):
        """Kept separate: needs a FAILING store, materially different setup from every table row.

        Every row above uses a healthy injected store and asks what the wizard DECIDED. This asks
        what happens when the decision was to save and the write then FAILED: the result must report
        `write-failed` and carry the underlying message, and must NOT claim `saved`. A table row
        cannot express it without giving every other row an unused error column.
        """
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        store = _Store(error=RP.ProfileStoreError("disk on fire"))
        result = W.run_wizard(_io(script, store=store))
        self.assertFalse(
            result.saved, "a failed write must never be reported as a successful save"
        )
        self.assertEqual(result.reason, "write-failed")
        self.assertIn(
            "disk on fire",
            "\n".join(result.messages),
            "the underlying store error must reach the user, or they cannot tell a full disk from a "
            "permission problem",
        )

    def test_no_writer_means_no_write_is_even_possible(self):
        """Kept separate: the store has NO `save` callable at all, a different WizardIO shape.

        This is the structural guarantee behind the table's non-writing rows: with `save=None` the
        wizard reports `no-writer` rather than crashing or pretending. Folding it in would mean a
        column that is `None` for every other row.
        """
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        result = W.run_wizard(_io(script, store=_Store(), with_writer=False))
        self.assertFalse(result.saved)
        self.assertEqual(result.reason, "no-writer")


class DefaultQuestionTests(unittest.TestCase):
    """E-04 / V-04: two SEPARATE default questions, each with its own polarity, in ONE atomic write.

    ONE table replaces eight tests. Each seeded a config, ran the full interview with a pair of
    answers to the two default questions, and asserted some mix of the returned flags, the WRITTEN
    config's defaults, and which prompts were rendered. Only the PRIOR CONFIG and the ANSWERS
    differed.

    Why the table beats the eight, and this is the strongest case in the file. The behavior is a
    MATRIX of two independent axes (does a default profile already exist; does a default runner
    already exist) against the answers, and the questions are deliberately ASYMMETRIC: the profile
    question defaults YES only when NO default exists yet, while the runner question always defaults
    NO. Eight separate tests state eight points of that matrix with no way to see it IS a matrix, and
    the asymmetry then reads as an inconsistency somebody should tidy up. Tabulated, the prior-state
    column makes it legible: adopting a FIRST default displaces nothing, so Enter may accept it,
    whereas making OpenCode the default IPD runner changes host-neutral dispatch (`ygzq71`) for
    unrelated work, so it stays opt-in.

    THE PROMPT POLARITY IS A COLUMN, not a separate table, because it is the same decision observed
    from the other side. A row asserts BOTH that Enter produced a given outcome AND that the prompt
    told the user it would. Those must agree, and the only way a mismatch is caught is by asserting
    them together: a question rendering `[y/N]` while treating Enter as yes is a wizard that changes
    a user's default without their consent.

    SKIPPING IS AN EXPECTED OUTCOME, NOT AN ABSENCE. Two rows expect a question NOT to be asked (the
    runner is already OpenCode; the profile is already the default), which is why the expected-prompt
    column distinguishes "asked with this polarity" from "must not be asked at all". A question with
    one real answer is noise, and the ANSWER COUNT is what proves it was skipped: a row supplying one
    answer for two questions would hit EOF and cancel if the wizard asked both.
    """

    #: (case, prior config, answers AFTER the save question, expected (made_default_profile,
    #: made_default_runner), expected written (default_profile_for("oc"), default_runner),
    #: expected prompts as a dict of question fragment -> "[Y/n]", "[y/N]" or None for
    #: "must NOT be asked", why this row exists)
    #:
    #: Prior config is "empty", "default-profile-old" (a different profile is already the default),
    #: "default-profile-gem" (the profile being written is ALREADY the default),
    #: "default-profile-sol" or "default-runner-oc".
    MATRIX = (
        (
            "both questions declined explicitly, from an empty config",
            "empty",
            ["n", "n"],
            (False, False),
            (None, None),
            {
                "default OpenCode profile?": "[Y/n]",
                "default IPD runner?": "[y/N]",
            },
            "TWO SEPARATE QUESTIONS, and NEITHER is implied by saving: the first profile a user "
            "creates does NOT silently become their default. Both are rendered, so a user who wants "
            "neither is asked about both rather than having one inferred",
        ),
        (
            "both questions answered with Enter, from an empty config",
            "empty",
            ["", ""],
            (True, False),
            ("gem", None),
            {
                "default OpenCode profile?": "[Y/n]",
                "default IPD runner?": "[y/N]",
            },
            "THE ASYMMETRY, and the row this table exists for (maintainer request 2026-09-12): the "
            "SAME empty answer ACCEPTS the first default profile and DECLINES the default runner, "
            "because adopting a first profile default displaces nothing while changing the default "
            "IPD runner affects host-neutral dispatch (`ygzq71`) for unrelated work. The two "
            "polarities are asserted beside the two outcomes so they cannot drift apart",
        ),
        (
            "both questions accepted explicitly, from an empty config",
            "empty",
            ["y", "y"],
            (True, True),
            ("gem", "oc"),
            {},
            "ONE ATOMIC WRITE: accepting both defaults must land in the SAME write as the profile, "
            "never a second one. The table asserts the write COUNT on every row, so a follow-up "
            "write would fail here. A crash between two writes could otherwise leave a default "
            "pointing at a profile that was never stored",
        ),
        (
            "Enter at the profile question when a DIFFERENT profile is already the default",
            "default-profile-old",
            ["", ""],
            (False, False),
            ("old", None),
            {"default OpenCode profile?": "[y/N]"},
            "THE GUARD ON THE 2026-09-12 CHANGE, which the maintainer scoped as 'IFF no default "
            "exists yet'. With a default already set the question REVERTS to default NO, so Enter "
            "cannot displace it. Silently moving a user's default could move every run onto a "
            "different and possibly costlier model, the same surprise `add_profile`'s no-clobber "
            "rule exists to prevent. Note the polarity column: the SAME question renders [Y/n] in "
            "the row above and [y/N] here, which is the whole mechanism",
        ),
        (
            "declining the profile default preserves the previous one",
            "default-profile-sol",
            ["n", "n"],
            (False, False),
            ("sol", None),
            {},
            "DECLINING IS NOT CLEARING: an explicit `n` leaves the existing default exactly as it "
            "was rather than unsetting it. A wizard that wrote None on a decline would silently "
            "remove a setting the user never mentioned",
        ),
        (
            "the runner question is SKIPPED when OpenCode is already the default runner",
            "default-runner-oc",
            ["n"],
            (False, False),
            (None, "oc"),
            {
                "default OpenCode profile?": "[Y/n]",
                "default IPD runner?": None,
            },
            "A QUESTION WITH ONE REAL ANSWER IS NOT ASKED, and the existing value survives. The "
            "profile question IS still asked because this profile is not the default yet, which is "
            "what makes this a skip of one question rather than of the pair. ONLY ONE ANSWER IS "
            "SUPPLIED: if the wizard asked both, it would hit EOF and cancel, so the answer count "
            "is itself the proof that the question was skipped",
        ),
        (
            "the profile question is SKIPPED when this profile is ALREADY the default",
            "default-profile-gem",
            ["n"],
            (False, False),
            ("gem", None),
            {
                "default OpenCode profile?": None,
                "default IPD runner?": "[y/N]",
            },
            "the mirror of the row above, on the OTHER axis: replacing `gem` when `gem` is already "
            "the default cannot change anything, so the question is skipped and the default is kept. "
            "Again only one answer is supplied, so asking would cancel the run",
        ),
    )

    def test_every_prior_state_and_answer_pair_lands_its_defaults(self):
        wrong = []
        for (
            case,
            prior,
            answers,
            expect_flags,
            expect_written,
            expect_prompts,
            why,
        ) in self.MATRIX:
            cfg, name, replace = self._prior(prior)
            store = _Store(cfg)
            # A pre-existing default named `gem` means the wizard is REPLACING that profile, so the
            # name is preseeded and the name question does not appear in the script.
            script = _Script(
                (["1", "1", "", "y"] if name else _SAVE_ANSWERS) + list(answers)
            )
            result = W.run_wizard(_io(script, store=store), name, replace=replace)
            problems = []
            if not result.saved:
                problems.append(
                    f"the interview did not SAVE (reason={result.reason!r}), so nothing below can "
                    "be judged. If the reason is `cancelled`, the wizard asked MORE questions than "
                    "this row supplies, which usually means a question that should be skipped was "
                    "asked"
                )
            else:
                if len(store.writes) != 1:
                    problems.append(
                        f"expected exactly ONE atomic write, got {len(store.writes)}. The defaults "
                        "must land in the same write as the profile"
                    )
                got_flags = (result.made_default_profile, result.made_default_runner)
                if got_flags != expect_flags:
                    problems.append(
                        f"(made_default_profile, made_default_runner) expected {expect_flags!r}, "
                        f"got {got_flags!r}"
                    )
                written = store.writes[0]
                got_written = (
                    written.default_profile_for("oc"),
                    written.default_runner,
                )
                if got_written != expect_written:
                    problems.append(
                        f"the WRITTEN config's (default profile, default runner) expected "
                        f"{expect_written!r}, got {got_written!r}. This is the durable effect, not "
                        "the report of it"
                    )
            for fragment, polarity in expect_prompts.items():
                rendered = [p for p in script.prompts if fragment in p]
                if polarity is None:
                    if rendered:
                        problems.append(
                            f"the question {fragment!r} must NOT be asked at all (it has one real "
                            f"answer), but it was rendered as {rendered!r}"
                        )
                elif not rendered:
                    problems.append(
                        f"the question {fragment!r} was never asked; the prompts were "
                        f"{script.prompts!r}"
                    )
                elif not any(polarity in p for p in rendered):
                    problems.append(
                        f"the question {fragment!r} must render {polarity} so the user can SEE what "
                        f"Enter will do; it rendered as {rendered!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (prior={prior}, answers={list(answers)!r})\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the default questions mishandled {len(wrong)} of {len(self.MATRIX)} prior-state and "
            "answer combinations. This is ONE matrix over two axes (a default profile already "
            "exists; a default runner already exists), so read the grouping rather than the rows. "
            "FIX: check the PROMPT POLARITY against the OUTCOME first, since a mismatch between "
            "them is the dangerous failure: a question that renders [y/N] while treating Enter as "
            "yes changes a user's default without their consent. The two Enter-from-empty and "
            "Enter-with-existing-default rows are the pair that encodes the maintainer's 'IFF no "
            "default exists yet' scoping, and if they now agree with each other, that scoping is "
            "gone and pressing Enter can displace a default the user chose earlier. A row reporting "
            "it did not SAVE at all, with reason `cancelled`, almost always means a question that "
            "should have been SKIPPED was asked: the row deliberately supplies too few answers, so "
            "an extra question exhausts the script. If the ONE ATOMIC WRITE count is wrong, a crash "
            "between the two writes could leave a default pointing at a profile that was never "
            "stored.\n" + "\n".join(wrong),
        )

    @staticmethod
    def _prior(prior: str):
        """Return (prior config, preseeded name or None, replace flag) for one `MATRIX` row."""
        cfg = RP.empty_config()
        if prior == "empty":
            return cfg, None, False
        if prior == "default-runner-oc":
            return RP.set_default_runner(cfg, "oc"), None, False
        existing = {
            "default-profile-old": ("old", _FLASH),
            "default-profile-sol": ("sol", _SOL),
            "default-profile-gem": ("gem", _SOL),
        }[prior]
        cfg = RP.add_profile(
            cfg, existing[0], RP.LaunchProfile(runner="oc", model=existing[1])
        )
        cfg = RP.set_default_profile(cfg, existing[0])
        # Only the `gem` case collides with the name the interview writes, so only it replaces.
        if existing[0] == "gem":
            return cfg, "gem", True
        return cfg, None, False

    def test_exactly_two_default_questions_are_asked_not_one_combined_one(self):
        """Kept separate: COUNTS the default-ish prompts, which no per-question row can do.

        The table asserts that each named question is asked with its own polarity. This asserts
        there are exactly TWO such questions and no more, so the pair cannot be merged into one
        combined "make this your default profile and runner?" question. A combined question would
        force a user who wants one and not the other to accept both, and it would satisfy every
        table row that only looks for its own fragment.
        """
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        W.run_wizard(_io(script, store=_Store()))
        asked = [p for p in script.prompts if "default" in p.lower() and "?" in p]
        self.assertEqual(
            len(asked),
            2,
            f"exactly two SEPARATE default questions must be asked, got {len(asked)}: {asked}",
        )

    def test_declining_the_profile_default_names_the_one_being_kept(self):
        """Kept separate: asserts about what was DISPLAYED to the user, not about what was written.

        The table's row for this case proves the previous default SURVIVES in the written config.
        This proves the user was TOLD which profile is keeping the role, so a decline is an informed
        one rather than a silent no-op.
        """
        cfg = RP.set_default_profile(
            RP.add_profile(
                RP.empty_config(), "sol", RP.LaunchProfile(runner="oc", model=_SOL)
            ),
            "sol",
        )
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        W.run_wizard(_io(script, store=_Store(cfg)))
        self.assertIn(
            "sol",
            script.text,
            "the user must be shown WHICH profile currently holds the default, or a decline is an "
            "uninformed one",
        )

    def test_an_already_default_profile_says_so_rather_than_asking(self):
        """Kept separate: asserts the EXPLANATION accompanying a skipped question.

        The table's row proves the question is not asked. This proves the wizard SAYS WHY instead of
        silently omitting it, which is the difference between a considered skip and a question that
        got lost.
        """
        cfg = RP.set_default_profile(
            RP.add_profile(
                RP.empty_config(), "gem", RP.LaunchProfile(runner="oc", model=_SOL)
            ),
            "gem",
        )
        script = _Script(["1", "1", "", "y", "n"])
        result = W.run_wizard(_io(script, store=_Store(cfg)), "gem", replace=True)
        self.assertTrue(result.saved)
        self.assertIn("already your default OpenCode profile", script.text)

    def test_ask_defaults_false_suppresses_both_questions(self):
        """Kept separate: a CALLER-side flag that removes both questions, not a matrix cell.

        Every `MATRIX` row answers the default questions. This one asserts a caller can suppress
        them entirely (`ask_defaults=False`, used by a fully specified noninteractive `add`), which
        is a claim about the parameter rather than about any prior state, and it needs a script with
        no default answers at all.
        """
        script = _Script(_SAVE_ANSWERS)
        store = _Store()
        result = W.run_wizard(_io(script, store=store), ask_defaults=False)
        self.assertTrue(result.saved)
        self.assertFalse(
            any("default" in p.lower() for p in script.prompts),
            f"ask_defaults=False must ask NEITHER question; got {script.prompts}",
        )
        self.assertIsNone(store.writes[0].default_profile_for("oc"))


class SessionLoopTests(unittest.TestCase):
    """The "Configure another profile?" loop belongs to an EXPLICIT session caller only.

    NOT MERGED: four claims about the LOOP rather than about one round's answers. Each counts a
    different thing across a different number of interviews: that `run_wizard` never renders the
    question at all, that `run_session` renders it and stops on no, that two full interviews produce
    two results and two writes with both profiles present, and that a cancel in the first round ends
    the session. A table would need a variable number of interviews per row plus a different
    accumulator each time, which is the "materially different setup" exclusion.
    """

    def test_the_loop_is_opt_in_and_run_wizard_never_loops(self):
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        W.run_wizard(_io(script, store=_Store()))
        self.assertFalse(any("another profile" in p.lower() for p in script.prompts))

    def test_the_session_asks_between_rounds_and_stops_on_no(self):
        script = _Script(_SAVE_ANSWERS + ["n", "n", "n"])
        results = W.run_session(_io(script, store=_Store()))
        self.assertEqual(len(results), 1)
        self.assertTrue(any("another profile" in p.lower() for p in script.prompts))

    def test_the_session_can_configure_two_profiles(self):
        script = _Script(
            ["gem", "1", "1", "", "y", "n", "n"]
            + ["y"]
            + ["sol", "1", "1", "", "y", "n", "n"]
            + ["n"]
        )
        store = _Store()
        results = W.run_session(_io(script, store=store))
        self.assertEqual([r.name for r in results], ["gem", "sol"])
        self.assertEqual(len(store.writes), 2)
        self.assertEqual(sorted(store.writes[-1].profiles), ["gem", "sol"])

    def test_the_session_stops_on_cancel(self):
        """Kept separate: the session must not re-ask after a cancel, a claim about the loop's exit."""
        results = W.run_session(_io(_Script(["q"]), store=_Store()))
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].cancelled)


class ByteIdenticalConfigTests(unittest.TestCase):
    """V-02 / V-04: a declined or failed flow leaves the REAL file's bytes untouched."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "runner-profiles.json"
        cfg = RP.add_profile(
            RP.empty_config(), "sol", RP.LaunchProfile(runner="oc", model=_SOL)
        )
        RP.save(cfg, self.path)
        self.before = self.path.read_bytes()

    def _io_on_disk(self, script: _Script) -> W.WizardIO:
        return W.WizardIO(
            ask=script.ask,
            emit=script.emit,
            discover=lambda: OM.ModelCatalog(
                models=(_FLASH,), source=OM.CATALOG_SOURCE_CLI
            ),
            load=lambda: RP.load(self.path),
            save=lambda cfg: RP.save(cfg, self.path),
        )

    #: (case, scripted answers, interrupt_at, why this row exists)
    #:
    #: Every row asserts the SAME thing about the SAME real file, which is the point: the four
    #: non-save endings are interchangeable from the file's perspective, and that is the property.
    NON_SAVE_ENDINGS = (
        (
            "the save question is declined",
            ["gem", "1", "1", "", "n"],
            None,
            "a completed interview the user says no to. This is the one ending that reaches the "
            "writer's DOORSTEP, having built a complete profile, so it is the likeliest to write by "
            "accident",
        ),
        (
            "a quit word is typed mid-interview",
            ["gem", "q"],
            None,
            "cancelling part way leaves a HALF-BUILT profile in memory, which must never be "
            "flushed. This row stops at the model question, so the profile is genuinely incomplete",
        ),
        (
            "input runs out before any question is answered",
            [],
            None,
            "an unattended pipe with NOTHING to say must not cause a write, which is what makes "
            "every default-YES question in this wizard safe to ship",
        ),
        (
            "a keyboard interrupt arrives at the third question",
            _SAVE_ANSWERS,
            3,
            "Ctrl-C is asynchronous and lands at an arbitrary point, so the file must be untouched "
            "even when the interrupt arrives LATE, with most of the profile already assembled",
        ),
    )

    def test_no_non_save_ending_changes_one_byte_of_the_real_file(self):
        """One table over the four non-save endings, replacing four tests.

        Each of the four ran one answer script against a REAL file on disk and compared its bytes to
        a snapshot. The scripts differed; the assertion was identical.

        Why the table beats the four. The claim is not four facts, it is ONE INVARIANT quantified
        over every way the interview can end without saving, and a table states it as such: the
        failure message can say "2 of 4 endings modified the file", which is the shape of the real
        problem, whereas four tests report two unrelated red lines. The four are also deliberately
        spread along the interview, from before the first answer to the last question, so a write
        introduced at any point has a row that reaches it.

        WHY BYTES AND NOT A MOCK. `NonSaveWritesNothingTests` already proves the injected writer is
        never CALLED. This class proves the FILE is unchanged, which is a strictly stronger claim over
        the real `RP.save`: it would catch a write that happened through some path other than the
        injected `save` callable, and it is the only assertion here that a reader can check without
        trusting the test's own injection.
        """
        wrong = []
        for case, answers, interrupt_at, why in self.NON_SAVE_ENDINGS:
            # Restore the snapshot first, so one leaking row cannot mask or cause another's failure.
            self.path.write_bytes(self.before)
            script = _Script(list(answers), interrupt_at=interrupt_at)
            result = W.run_wizard(self._io_on_disk(script))
            after = self.path.read_bytes()
            problems = []
            if result.saved:
                problems.append(
                    f"the wizard reported SAVED (reason={result.reason!r}) on a path that must not "
                    "save at all"
                )
            if after != self.before:
                problems.append(
                    f"THE FILE CHANGED: {len(self.before)} bytes became {len(after)}. Before: "
                    f"{self.before[:200]!r}\n      After:  {after[:200]!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (answers={list(answers)!r}"
                    + (
                        f", interrupt at question {interrupt_at}"
                        if interrupt_at
                        else ""
                    )
                    + ")\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.NON_SAVE_ENDINGS)} non-save endings modified a real "
            "configuration file. V-02 / V-04 is a SINGLE INVARIANT over every way the interview can "
            "end without saving, so several rows failing together means the write moved to a place "
            "all of them reach (most likely out of the save branch and into the interview itself) "
            "rather than several independent bugs. FIX: this is the most serious failure class in "
            "this suite, because the file belongs to the USER: it holds profiles they configured "
            "earlier, and a stray write can silently replace or drop them. The declined row is the "
            "one to read first, since it is the only ending that assembles a complete profile and "
            "then must throw it away. If the EOF row is failing, an unattended pipe can rewrite a "
            "developer's configuration, and no default-YES question in this wizard is safe. Note "
            "this assertion is over the REAL file rather than a mock, so unlike "
            f"`SaveOutcomeTests` it also catches a write that bypassed the injected writer.\n"
            + "\n".join(wrong),
        )

    def test_declining_the_defaults_still_changes_only_the_profiles_block(self):
        result = W.run_wizard(self._io_on_disk(_Script(_SAVE_ANSWERS + ["n", "n"])))
        self.assertTrue(result.saved)
        after = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(sorted(after["profiles"]), ["gem", "sol"])
        self.assertNotIn("defaults", after)
        self.assertNotIn("default_runner", after)

    def test_an_absent_config_stays_absent_after_a_decline(self):
        missing = Path(self._tmp.name) / "absent.json"
        script = _Script(["gem", "1", "1", "", "n"])
        io = W.WizardIO(
            ask=script.ask,
            emit=script.emit,
            discover=lambda: OM.ModelCatalog(
                models=(_FLASH,), source=OM.CATALOG_SOURCE_CLI
            ),
            load=lambda: RP.load(missing),
            save=lambda cfg: RP.save(cfg, missing),
        )
        result = W.run_wizard(io)
        self.assertFalse(result.saved)
        self.assertFalse(missing.exists())


class NoCredentialLeakTests(unittest.TestCase):
    def test_no_wizard_output_contains_a_sentinel_credential(self):
        """Kept separate: asserts over a HAYSTACK of three collected channels, not one value.

        The claim spans everything the wizard emitted, every prompt it rendered, and every message it
        returned, checked against a sentinel planted in the environment. It is a whole-run property
        rather than a per-input mapping, so there is no row to vary.
        """
        script = _Script(_SAVE_ANSWERS + ["y", "y"])
        os.environ["AW_TEST_FAKE_SECRET"] = SENTINEL_SECRET
        self.addCleanup(os.environ.pop, "AW_TEST_FAKE_SECRET", None)
        result = W.run_wizard(_io(script, store=_Store()))
        self.assertTrue(result.saved)
        haystack = script.text + "\n".join(script.prompts) + "\n".join(result.messages)
        self.assertNotIn(SENTINEL_SECRET, haystack)
        self.assertNotIn("apiKey", haystack)

    #: (forbidden token, the capability it would grant, why this row exists)
    #:
    #: Each row was one of three tests that read the wizard's source and looped its own short list of
    #: tokens, reporting only the FIRST hit and stopping. Nine tokens now report together.
    FORBIDDEN_SOURCE_TOKENS = (
        (
            "shell=True",
            "shell interpretation",
            "a shell would make any interpolated value (a model id, a variant, a profile name the "
            "user typed) executable, turning a text field into command injection",
        ),
        (
            "os.system",
            "shell interpretation",
            "the same hazard by a different route, and one that is easy to reach for when adding a "
            "single innocuous-looking command",
        ),
        (
            "eval(",
            "evaluating text as code",
            "every string here is USER INPUT from a prompt; evaluating any of it is arbitrary code "
            "execution",
        ),
        (
            "exec(",
            "evaluating text as code",
            "the statement-level twin of eval, forbidden for the same reason",
        ),
        (
            "os.environ",
            "reading the environment",
            "CREDENTIALS LIVE IN THE ENVIRONMENT. A wizard that never reads it cannot leak a key "
            "into a preview, a prompt, or a stored profile, which is a structural guarantee rather "
            "than a promise that no current code path happens to print one",
        ),
        (
            "getenv",
            "reading the environment",
            "the other spelling of the same read; checking only `os.environ` would miss "
            "`os.getenv(...)` entirely",
        ),
        (
            "write_config",
            "writing OpenCode's own configuration",
            "the wizard writes the RUNNER PROFILE store and nothing else. Touching the user's "
            "`opencode.json` would put it in the business of editing a file it only ever reads ids "
            "from",
        ),
        (
            "opencode.json",
            "writing OpenCode's own configuration",
            "naming the file at all is the precondition for writing it, so the NAME is forbidden "
            "here rather than just the write call",
        ),
        (
            "--refresh",
            "mutating OpenCode state",
            "V-01: discovery is READ-ONLY. `--refresh` is the flag that would make the probe mutate "
            "the user's cached provider state, and the wizard must not carry it even as a string",
        ),
    )

    def test_the_wizard_source_contains_no_forbidden_capability(self):
        """One table over the wizard's forbidden source tokens, replacing three tests.

        Each of the three read `inspect.getsource(W)` and looped a short list of tokens with
        `assertNotIn`, so each was already a hand-inlined table that stopped at its FIRST hit.

        Why one table rather than three, given the tokens guard three different capabilities: they are
        three facets of ONE claim, that this module is a pure question-and-answer layer over injected
        seams, and the `capability` column keeps the grouping legible in the failure. The merged
        message can say which CAPABILITIES appeared rather than which tokens, which is what a reader
        needs: two tokens from the same capability appearing together is one change, while tokens from
        three capabilities appearing at once means the module's whole role has shifted.

        HONEST LIMIT, stated because a source scan invites overconfidence: this is a TEXTUAL check
        and is trivially evaded (`getattr(os, "environ")`, a helper in another module). It is a
        tripwire against the ordinary case of someone adding a convenient line, not a proof. The
        credential guarantee is enforced for real by `test_no_wizard_output_contains_a_sentinel_
        credential`, which checks actual output, and by the AST-based check on the discovery path.
        """
        import inspect

        src = inspect.getsource(W)
        wrong = []
        capabilities = set()
        for token, capability, why in self.FORBIDDEN_SOURCE_TOKENS:
            if token in src:
                capabilities.add(capability)
                lines = [
                    f"{number}: {line.strip()}"
                    for number, line in enumerate(src.splitlines(), start=1)
                    if token in line
                ]
                wrong.append(
                    f"  {token!r} grants {capability} and appears at:\n"
                    + "".join(f"      {location}\n" for location in lines[:5])
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the wizard's source contains {len(wrong)} of "
            f"{len(self.FORBIDDEN_SOURCE_TOKENS)} forbidden tokens, across "
            f"{len(capabilities)} capability group(s): {', '.join(sorted(capabilities))}. The module "
            "is meant to be a pure question-and-answer layer over INJECTED seams (`ask`, `emit`, "
            "`discover`, `load`, `save`), so read the grouping: several tokens from ONE capability "
            "is a single change, while tokens from several at once means the module has taken on a "
            "role it should not have. FIX: an environment read is the one to treat as urgent, since "
            "credentials live there and this module renders everything it touches to a terminal. A "
            "shell or eval token is the injection hazard, because every string here came from a "
            "prompt the user typed into. NOTE THE LIMIT: this check is TEXTUAL and easy to evade, so "
            "it is a tripwire rather than a proof; the real credential guarantee is the "
            f"sentinel-output test above.\n" + "\n".join(wrong),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

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
        self.assertGreater(OM.CATALOG_TIMEOUT, 0)
        self.assertLess(OM.CATALOG_TIMEOUT, 120)


class CatalogParsingTests(unittest.TestCase):
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
        """A discovered model must be storable, so the two grammars must be ONE grammar."""
        self.assertIs(OM._model_re(), RP.MODEL_RE)
        for model in OM.parse_models_output(f"{_FLASH}\n{_INHOUSE}\n{_SOL}\n"):
            self.assertEqual(RP.validate_model(model), model)

    def test_strip_ansi_removes_csi_and_osc(self):
        self.assertEqual(OM.strip_ansi("\x1b[31mred\x1b[0m"), "red")
        self.assertEqual(OM.strip_ansi("\x1b]0;title\x07x"), "x")


class CatalogDiagnosticTests(unittest.TestCase):
    """Every failure is DISTINCT and named; none is a successful empty catalog."""

    def _catalog(self, **kwargs) -> OM.ModelCatalog:
        return OM.discover_models(allow_config_fallback=False, **kwargs)

    def test_missing_binary(self):
        cat = self._catalog(runner=_RecordingRunner(raises=FileNotFoundError()))
        self.assertFalse(cat.available)
        self.assertEqual(cat.reason, OM.CATALOG_MISSING_BINARY)
        self.assertEqual(cat.models, ())

    def test_timeout(self):
        cat = self._catalog(
            runner=_RecordingRunner(
                raises=subprocess.TimeoutExpired(cmd=["opencode", "models"], timeout=1)
            )
        )
        self.assertFalse(cat.available)
        self.assertEqual(cat.reason, OM.CATALOG_TIMED_OUT)

    def test_nonzero_exit(self):
        cat = self._catalog(runner=_RecordingRunner(_FakeProc(3, "boom")))
        self.assertFalse(cat.available)
        self.assertEqual(cat.reason, OM.CATALOG_NONZERO_EXIT)

    def test_malformed_output(self):
        cat = self._catalog(runner=_RecordingRunner(_FakeProc(0, "Loading...\nnope\n")))
        self.assertFalse(cat.available)
        self.assertEqual(cat.reason, OM.CATALOG_UNPARSEABLE)

    def test_empty_output(self):
        cat = self._catalog(runner=_RecordingRunner(_FakeProc(0, "")))
        self.assertFalse(cat.available)
        self.assertEqual(cat.reason, OM.CATALOG_NO_MODELS)

    def test_oserror_is_a_missing_binary_not_a_crash(self):
        cat = self._catalog(runner=_RecordingRunner(raises=PermissionError()))
        self.assertFalse(cat.available)
        self.assertEqual(cat.reason, OM.CATALOG_MISSING_BINARY)

    def test_a_successful_empty_catalog_is_unrepresentable(self):
        """`available` is derived, so "succeeded with zero models" cannot be constructed."""
        self.assertFalse(
            OM.ModelCatalog(models=(), source=OM.CATALOG_SOURCE_CLI).available
        )

    def test_every_diagnostic_reason_is_distinct(self):
        reasons = {
            OM.CATALOG_MISSING_BINARY,
            OM.CATALOG_TIMED_OUT,
            OM.CATALOG_NONZERO_EXIT,
            OM.CATALOG_UNPARSEABLE,
            OM.CATALOG_NO_MODELS,
            OM.CATALOG_NO_CONFIG,
        }
        self.assertEqual(len(reasons), 6)


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
        parsed = json.loads(self._config_text())
        models = OM.models_from_config(parsed)
        self.assertEqual(models, (_FLASH, _SOL))
        self.assertNotIn(SENTINEL_SECRET, "".join(models))

    def test_fallback_supplies_ids_and_still_reports_why_the_cli_failed(self):
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

    def test_no_config_is_its_own_reason(self):
        with tempfile.TemporaryDirectory() as d:
            models, reason = OM.catalog_from_config(
                env={"OPENCODE_CONFIG": str(Path(d) / "absent.json")}
            )
        self.assertEqual(models, ())
        self.assertEqual(reason, OM.CATALOG_NO_CONFIG)

    def test_garbage_config_is_not_an_exception(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "opencode.json"
            cfg.write_text("{not json", encoding="utf-8")
            models, reason = OM.catalog_from_config(env={"OPENCODE_CONFIG": str(cfg)})
        self.assertEqual(models, ())
        self.assertEqual(reason, OM.CATALOG_UNPARSEABLE)

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
    def test_filter_is_case_insensitive_substring_and_order_preserving(self):
        models = (_FLASH, _INHOUSE, _SOL)
        self.assertEqual(W.filter_models(models, "FLASH"), (_FLASH,))
        self.assertEqual(W.filter_models(models, "example"), models)
        self.assertEqual(W.filter_models(models, "zzz"), ())
        self.assertEqual(W.filter_models(models, ""), models)

    def test_a_200_entry_catalog_is_paged_not_dumped(self):
        catalog = OM.ModelCatalog(
            models=_many_models(200), source=OM.CATALOG_SOURCE_CLI
        )
        script = _Script(["1"])
        chosen = W.select_model(_io(script, catalog), catalog)
        self.assertEqual(chosen, "vendor0/model-000")
        listed = [line for line in script.lines if line.strip().startswith("[")]
        self.assertEqual(len(listed), W.PAGE_SIZE)
        self.assertIn("page 1/10", script.text)

    def test_paging_forward_then_picking_uses_absolute_numbering(self):
        catalog = OM.ModelCatalog(
            models=_many_models(200), source=OM.CATALOG_SOURCE_CLI
        )
        script = _Script(["n", "21"])
        chosen = W.select_model(_io(script, catalog), catalog)
        # Numbering is ABSOLUTE across pages, not per-page: entry 21 is the first item of page 2,
        # i.e. index 20 of the catalog. A per-page numbering scheme would have returned index 0.
        self.assertEqual(chosen, "vendor0/model-020")
        self.assertIn("page 2/10", script.text)

    def test_paging_backward_is_bounded_not_wrapped(self):
        catalog = OM.ModelCatalog(
            models=_many_models(200), source=OM.CATALOG_SOURCE_CLI
        )
        script = _Script(["p", "1"])
        W.select_model(_io(script, catalog), catalog)
        self.assertIn("Already on the first page.", script.text)

    def test_filtering_a_200_entry_catalog_narrows_the_choice(self):
        catalog = OM.ModelCatalog(
            models=_many_models(200), source=OM.CATALOG_SOURCE_CLI
        )
        script = _Script(["/model-1", "1"])
        chosen = W.select_model(_io(script, catalog), catalog)
        self.assertIn("matching 'model-1'", script.text)
        # Substring, and CATALOG-ORDER preserving: `model-1` matches the 100 ids model-100..199,
        # the first of which in catalog order is model-100. Numbering restarts at 1 within the
        # FILTERED list, so entry 1 is that first match and not the first item of the full list.
        self.assertEqual(chosen, "vendor0/model-100")
        self.assertIn("Models (100 matching 'model-1')", script.text)

    def test_a_filter_matching_nothing_is_reported_and_recoverable(self):
        catalog = OM.ModelCatalog(models=_many_models(30), source=OM.CATALOG_SOURCE_CLI)
        script = _Script(["/nothing-matches", "1"])
        chosen = W.select_model(_io(script, catalog), catalog)
        self.assertIn("No model matches", script.text)
        self.assertEqual(chosen, "vendor0/model-000")

    def test_out_of_range_and_garbage_are_reported_then_retried(self):
        catalog = OM.ModelCatalog(models=(_FLASH, _SOL), source=OM.CATALOG_SOURCE_CLI)
        script = _Script(["99", "banana", "2"])
        chosen = W.select_model(_io(script, catalog), catalog)
        self.assertIn("out of range", script.text)
        self.assertIn("Unrecognized input", script.text)
        self.assertEqual(chosen, _SOL)


class ManualEntryTests(unittest.TestCase):
    def test_manual_entry_is_reachable_from_a_working_catalog(self):
        catalog = OM.ModelCatalog(models=(_FLASH,), source=OM.CATALOG_SOURCE_CLI)
        script = _Script(["m", _INHOUSE])
        self.assertEqual(W.select_model(_io(script, catalog), catalog), _INHOUSE)

    def test_manual_entry_is_the_only_path_when_discovery_failed(self):
        """The private-model case: discovery is dead, the profile is still creatable."""
        catalog = OM.ModelCatalog(
            source=OM.CATALOG_SOURCE_NONE, reason=OM.CATALOG_MISSING_BINARY
        )
        script = _Script([_INHOUSE])
        io = _io(script, catalog)
        W._report_catalog(io, catalog)
        self.assertEqual(W.select_model(io, catalog), _INHOUSE)
        self.assertIn(OM.CATALOG_MISSING_BINARY, script.text)

    def test_an_invalid_manual_model_is_rejected_with_the_schemas_message(self):
        catalog = OM.ModelCatalog(
            source=OM.CATALOG_SOURCE_NONE, reason=OM.CATALOG_NO_MODELS
        )
        script = _Script(["no-slash", "bad;model/x", _SOL])
        self.assertEqual(W.select_model(_io(script, catalog), catalog), _SOL)
        self.assertIn("expected an exact 'provider/model' identifier", script.text)

    def test_manual_entry_gives_up_after_a_bounded_number_of_attempts(self):
        catalog = OM.ModelCatalog(
            source=OM.CATALOG_SOURCE_NONE, reason=OM.CATALOG_NO_MODELS
        )
        script = _Script(["bad"] * (W.MAX_ATTEMPTS + 2))
        with self.assertRaises(W.WizardCancelled):
            W.select_model(_io(script, catalog), catalog)


class VariantTests(unittest.TestCase):
    def test_provider_default_stores_no_variant(self):
        script = _Script(["1"])
        self.assertIsNone(W.select_variant(_io(script), _FLASH))
        self.assertIn("Provider default (store no variant)", script.text)

    def test_empty_input_takes_the_provider_default(self):
        script = _Script([""])
        self.assertIsNone(W.select_variant(_io(script), _FLASH))

    def test_every_common_variant_is_selectable(self):
        for offset, word in enumerate(W.COMMON_VARIANTS, start=2):
            script = _Script([str(offset)])
            self.assertEqual(W.select_variant(_io(script), _FLASH), word)

    def test_a_custom_exact_variant_is_preserved_verbatim(self):
        script = _Script([str(len(W.COMMON_VARIANTS) + 2), "ultra-2"])
        self.assertEqual(W.select_variant(_io(script), _FLASH), "ultra-2")

    def test_the_menu_labels_variants_provider_specific_and_does_not_overclaim(self):
        script = _Script(["1"])
        W.select_variant(_io(script), _FLASH)
        self.assertIn("provider-specific", script.text)
        self.assertIn("a provider may accept none of these", script.text)

    def test_an_invalid_custom_variant_is_refused_by_the_schemas_own_validator(self):
        script = _Script([str(len(W.COMMON_VARIANTS) + 2), "bad value!", "high"])
        self.assertEqual(W.select_variant(_io(script), _FLASH), "high")
        self.assertIn("invalid variant", script.text)

    def test_the_field_validator_routes_through_the_public_schema_api(self):
        self.assertEqual(W.validate_optional_field("variant", "high", _FLASH), "high")
        self.assertEqual(W.validate_optional_field("agent", "build", _FLASH), "build")
        with self.assertRaises(RP.ProfileSchemaError):
            W.validate_optional_field("agent", "not a token", _FLASH)


class PreviewTests(unittest.TestCase):
    def test_the_argv_preview_matches_the_runners_own_flag_order(self):
        profile = RP.LaunchProfile(
            runner="oc", model=_FLASH, variant="high", agent="build"
        )
        self.assertEqual(
            W.opencode_argv_fields(profile),
            ["--model", _FLASH, "--variant", "high", "--agent", "build"],
        )

    def test_absent_fields_emit_no_flag_at_all(self):
        profile = RP.LaunchProfile(runner="oc", model=_FLASH)
        self.assertEqual(W.opencode_argv_fields(profile), ["--model", _FLASH])

    def test_the_preview_shows_the_exact_stored_fields_and_the_exact_launch(self):
        profile = RP.LaunchProfile(runner="oc", model=_INHOUSE, variant="max")
        text = "\n".join(W.preview_lines("sonnet", profile))
        self.assertIn(f"model:   {_INHOUSE}", text)
        self.assertIn("variant: max", text)
        self.assertIn("agent:   (none)", text)
        self.assertIn(f"opencode run --model {_INHOUSE} --variant max", text)

    def test_a_provider_default_variant_is_shown_as_such_not_as_a_guess(self):
        profile = RP.LaunchProfile(runner="oc", model=_FLASH)
        text = "\n".join(W.preview_lines("gem", profile))
        self.assertIn("variant: (provider default)", text)
        self.assertNotIn("--variant", text)


class ProfileNameTests(unittest.TestCase):
    def test_the_grammar_is_the_schemas_own_and_bad_names_retry(self):
        script = _Script(["Bad Name", "as", "gem"])
        self.assertEqual(W.ask_profile_name(_io(script), RP.empty_config()), "gem")
        self.assertIn("reserved", script.text)

    def test_an_existing_name_is_refused_without_replace(self):
        cfg = RP.add_profile(
            RP.empty_config(), "gem", RP.LaunchProfile(runner="oc", model=_FLASH)
        )
        script = _Script(["gem", "sol"])
        self.assertEqual(W.ask_profile_name(_io(script), cfg), "sol")
        self.assertIn("already exists", script.text)

    def test_replace_permits_the_existing_name(self):
        cfg = RP.add_profile(
            RP.empty_config(), "gem", RP.LaunchProfile(runner="oc", model=_FLASH)
        )
        script = _Script(["gem"])
        self.assertEqual(W.ask_profile_name(_io(script), cfg, replace=True), "gem")


class YesNoTests(unittest.TestCase):
    def test_empty_input_takes_the_rendered_default(self):
        self.assertFalse(W.ask_yes_no(_io(_Script([""])), "Q?", default=False))
        self.assertTrue(W.ask_yes_no(_io(_Script([""])), "Q?", default=True))

    def test_the_default_is_rendered_explicitly(self):
        script = _Script([""])
        W.ask_yes_no(_io(script), "Q?", default=False)
        self.assertTrue(any("[y/N]" in p for p in script.prompts))

    def test_eof_is_a_cancel_not_a_silent_yes(self):
        with self.assertRaises(W.WizardCancelled):
            W.ask_yes_no(_io(_Script([])), "Q?", default=False)

    def test_a_quit_word_cancels(self):
        with self.assertRaises(W.WizardCancelled):
            W.ask_yes_no(_io(_Script(["q"])), "Q?", default=False)


# ==================================================================================================
# The full interview (E-02) and the default questions (E-04)
# ==================================================================================================

# One complete happy-path answer script: name, model pick, provider-default variant, no agent, save
_SAVE_ANSWERS = ["gem", "1", "1", "", "y"]


class InterviewTests(unittest.TestCase):
    def test_a_discovered_flow_saves_exactly_once(self):
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        store = _Store()
        result = W.run_wizard(_io(script, store=store))
        self.assertTrue(result.saved)
        self.assertEqual(result.name, "gem")
        self.assertEqual(len(store.writes), 1)
        saved = store.writes[0].profiles["gem"]
        self.assertEqual(saved.model, _FLASH)
        self.assertIsNone(saved.variant)
        self.assertIsNone(saved.agent)

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

    def test_a_manual_model_and_a_custom_variant_round_trip(self):
        catalog = OM.ModelCatalog(
            source=OM.CATALOG_SOURCE_NONE, reason=OM.CATALOG_MISSING_BINARY
        )
        script = _Script(
            [
                "sonnet",
                _INHOUSE,
                str(len(W.COMMON_VARIANTS) + 2),
                "ultra",
                "build",
                "y",
                "n",
                "n",
            ]
        )
        store = _Store()
        result = W.run_wizard(_io(script, catalog=catalog, store=store))
        self.assertTrue(result.saved)
        saved = store.writes[0].profiles["sonnet"]
        self.assertEqual(
            (saved.model, saved.variant, saved.agent), (_INHOUSE, "ultra", "build")
        )

    def test_a_preseeded_name_skips_the_name_question(self):
        script = _Script(["1", "1", "", "y", "n", "n"])
        result = W.run_wizard(_io(script, store=_Store()), "sol")
        self.assertTrue(result.saved)
        self.assertEqual(result.name, "sol")
        self.assertFalse(any("Profile name" in p for p in script.prompts))

    def test_an_existing_preseeded_name_refuses_without_replace_and_writes_nothing(
        self,
    ):
        cfg = RP.add_profile(
            RP.empty_config(), "gem", RP.LaunchProfile(runner="oc", model=_SOL)
        )
        store = _Store(cfg)
        result = W.run_wizard(_io(_Script([]), store=store), "gem")
        self.assertFalse(result.saved)
        self.assertEqual(result.reason, "exists")
        self.assertEqual(store.writes, [])


class SaveQuestionDefaultsToYesTests(unittest.TestCase):
    """The save question defaults YES (maintainer request 2026-09-12).

    By the time it is asked, the user has picked a model, a variant and an agent and been shown a
    preview, so Enter should complete the thing they were doing. The safety property this does NOT
    weaken is that a save still requires the user to reach this question at all: EOF, an interrupt,
    a quit word, and an explicit `n` each write nothing, and all four are covered by
    `NonSaveWritesNothingTests`.
    """

    def test_pressing_enter_at_the_save_question_SAVES(self):
        store = _Store()
        script = _Script(["gem", "1", "1", "", ""] + ["n", "n"])
        result = W.run_wizard(_io(script, store=store))
        self.assertTrue(result.saved, "empty input should take the YES default")
        self.assertEqual(len(store.writes), 1)
        self.assertIn("gem", store.writes[0].profiles)

    def test_the_save_prompt_renders_the_yes_default(self):
        script = _Script(["gem", "1", "1", "", ""] + ["n", "n"])
        W.run_wizard(_io(script, store=_Store()))
        save_prompts = [p for p in script.prompts if "Save profile" in p]
        self.assertTrue(save_prompts, f"no save prompt was rendered: {script.prompts}")
        self.assertIn("[Y/n]", save_prompts[0])


class NonSaveWritesNothingTests(unittest.TestCase):
    """Every non-save path: no write call at all, and `saved=False`."""

    def _assert_no_write(self, script: _Script, expected_reason: Optional[str] = None):
        store = _Store()
        result = W.run_wizard(_io(script, store=store))
        self.assertFalse(result.saved)
        self.assertEqual(store.writes, [], "a non-save path called the writer")
        if expected_reason is not None:
            self.assertEqual(result.reason, expected_reason)
        return result

    def test_declining_the_save_question_writes_nothing(self):
        result = self._assert_no_write(_Script(["gem", "1", "1", "", "n"]), "declined")
        self.assertFalse(result.cancelled)

    def test_an_explicit_no_to_the_save_question_writes_nothing(self):
        """The save question DEFAULTS TO YES since 2026-09-12, so declining must be explicit.

        This replaces a test that asserted an empty answer declined. That polarity was reversed on
        maintainer request; what still matters, and is what this asserts, is that an explicit `n`
        writes nothing at all. The empty-input case is now covered by
        `SaveQuestionDefaultsToYesTests` below, which proves Enter SAVES.
        """

        result = self._assert_no_write(_Script(["gem", "1", "1", "", "n"]), "declined")
        self.assertFalse(result.saved)

    def test_an_explicit_quit_word_cancels(self):
        result = self._assert_no_write(_Script(["gem", "1", "1", "", "q"]), "cancelled")
        self.assertTrue(result.cancelled)

    def test_eof_cancels(self):
        result = self._assert_no_write(_Script(["gem", "1"]), "cancelled")
        self.assertTrue(result.cancelled)

    def test_a_keyboard_interrupt_cancels_cleanly(self):
        script = _Script(_SAVE_ANSWERS, interrupt_at=2)
        result = self._assert_no_write(script, "cancelled")
        self.assertTrue(result.cancelled)

    def test_no_writer_means_no_write_is_even_possible(self):
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        result = W.run_wizard(_io(script, store=_Store(), with_writer=False))
        self.assertFalse(result.saved)
        self.assertEqual(result.reason, "no-writer")

    def test_a_write_failure_is_reported_and_not_claimed_as_saved(self):
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        store = _Store(error=RP.ProfileStoreError("disk on fire"))
        result = W.run_wizard(_io(script, store=store))
        self.assertFalse(result.saved)
        self.assertEqual(result.reason, "write-failed")
        self.assertIn("disk on fire", "\n".join(result.messages))

    def test_an_unreadable_config_is_reported_not_treated_as_empty(self):
        def _bad_load():
            raise RP.ProfileSchemaError("runner-profiles.json is not valid JSON")

        store = _Store()
        io = W.WizardIO(
            ask=_Script([]).ask,
            emit=lambda line: None,
            discover=lambda: OM.ModelCatalog(
                models=(_FLASH,), source=OM.CATALOG_SOURCE_CLI
            ),
            load=_bad_load,
            save=store.save,
        )
        result = W.run_wizard(io)
        self.assertFalse(result.saved)
        self.assertEqual(result.reason, "unreadable-config")
        self.assertEqual(store.writes, [])


class DefaultQuestionTests(unittest.TestCase):
    """E-04 / V-04: two SEPARATE questions, both default NO, one atomic write."""

    def test_both_default_questions_are_asked_separately(self):
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        W.run_wizard(_io(script, store=_Store()))
        prompts = script.prompts
        self.assertTrue(any("default OpenCode profile?" in p for p in prompts))
        self.assertTrue(any("default IPD runner?" in p for p in prompts))
        # Two distinct questions, not one combined one.
        self.assertEqual(
            len([p for p in prompts if "default" in p.lower() and "?" in p]), 2
        )

    def test_the_two_default_questions_carry_DIFFERENT_polarities(self):
        """The profile question defaults YES only when no default exists; the runner one stays NO.

        Maintainer request 2026-09-12, and the asymmetry is the point rather than an inconsistency.
        Adopting a FIRST default profile displaces nothing, so Enter may accept it. Making OpenCode
        the default IPD RUNNER affects host-neutral dispatch (`ygzq71`) for an unrelated user, so it
        was not in the requested set and keeps its opt-in default.

        Replaces a test asserting BOTH took no on empty input.
        """

        script = _Script(_SAVE_ANSWERS + ["", ""])
        store = _Store()
        result = W.run_wizard(_io(script, store=store))
        self.assertTrue(result.saved)
        # Empty input ACCEPTS the first default profile ...
        self.assertTrue(result.made_default_profile)
        self.assertEqual(store.writes[0].default_profile_for("oc"), "gem")
        # ... and still DECLINES the default runner.
        self.assertFalse(result.made_default_runner)
        self.assertIsNone(store.writes[0].default_runner)

        rendered = {p for p in script.prompts if "default" in p.lower() and "?" in p}
        self.assertTrue(
            any(
                "the default OpenCode profile?" in p and "[Y/n]" in p for p in rendered
            ),
            f"first-default profile question should default YES: {rendered}",
        )
        self.assertTrue(
            any("default IPD runner?" in p and "[y/N]" in p for p in rendered),
            f"default-runner question should stay NO: {rendered}",
        )

    def test_an_EXISTING_default_profile_is_not_replaced_by_pressing_enter(self):
        """With a default already set, the question reverts to default NO.

        This is the guard on the 2026-09-12 change, which the maintainer scoped as "IFF no default
        exists yet". Silently displacing a default the user chose earlier could move their runs onto
        a different, possibly costlier, model, which is the same surprise `add_profile`'s no-clobber
        rule exists to prevent.
        """

        cfg = RP.add_profile(
            RP.empty_config(), "old", RP.LaunchProfile(runner="oc", model=_FLASH)
        )
        cfg = RP.set_default_profile(cfg, "old")
        store = _Store(cfg)
        script = _Script(_SAVE_ANSWERS + ["", ""])
        result = W.run_wizard(_io(script, store=store))
        self.assertTrue(result.saved)
        self.assertFalse(
            result.made_default_profile, "Enter must not displace an existing default"
        )
        self.assertEqual(store.writes[0].default_profile_for("oc"), "old")
        self.assertTrue(
            any(
                "the default OpenCode profile?" in p and "[y/N]" in p
                for p in script.prompts
            ),
            "existing-default question must render the NO default",
        )

    def test_the_first_profile_does_not_become_the_default_automatically(self):
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        store = _Store()
        W.run_wizard(_io(script, store=store))
        self.assertEqual(len(store.writes[0].profiles), 1)
        self.assertIsNone(store.writes[0].default_profile_for("oc"))

    def test_accepting_both_defaults_lands_in_ONE_atomic_write(self):
        script = _Script(_SAVE_ANSWERS + ["y", "y"])
        store = _Store()
        result = W.run_wizard(_io(script, store=store))
        self.assertTrue(result.saved)
        self.assertTrue(result.made_default_profile)
        self.assertTrue(result.made_default_runner)
        self.assertEqual(len(store.writes), 1, "defaults must not be a second write")
        written = store.writes[0]
        self.assertEqual(written.default_profile_for("oc"), "gem")
        self.assertEqual(written.default_runner, "oc")

    def test_declining_the_profile_default_preserves_the_previous_one(self):
        cfg = RP.set_default_profile(
            RP.add_profile(
                RP.empty_config(), "sol", RP.LaunchProfile(runner="oc", model=_SOL)
            ),
            "sol",
        )
        script = _Script(_SAVE_ANSWERS + ["n", "n"])
        store = _Store(cfg)
        result = W.run_wizard(_io(script, store=store))
        self.assertTrue(result.saved)
        self.assertEqual(store.writes[0].default_profile_for("oc"), "sol")
        self.assertIn("sol", script.text)

    def test_declining_the_runner_default_preserves_the_previous_value(self):
        cfg = RP.set_default_runner(RP.empty_config(), "oc")
        # The profile-default question IS still asked (this profile is not the default yet); only
        # the RUNNER question is skipped, because OpenCode is already the default runner and asking
        # would be a question with one real answer.
        script = _Script(_SAVE_ANSWERS + ["n"])
        store = _Store(cfg)
        result = W.run_wizard(_io(script, store=store))
        self.assertTrue(result.saved)
        self.assertEqual(store.writes[0].default_runner, "oc")
        self.assertFalse(any("default IPD runner?" in p for p in script.prompts))

    def test_an_existing_default_of_the_same_name_is_not_re_asked(self):
        cfg = RP.set_default_profile(
            RP.add_profile(
                RP.empty_config(), "gem", RP.LaunchProfile(runner="oc", model=_SOL)
            ),
            "gem",
        )
        script = _Script(["1", "1", "", "y", "n"])
        store = _Store(cfg)
        result = W.run_wizard(_io(script, store=store), "gem", replace=True)
        self.assertTrue(result.saved)
        self.assertIn("already your default OpenCode profile", script.text)
        self.assertEqual(store.writes[0].default_profile_for("oc"), "gem")

    def test_ask_defaults_false_suppresses_both_questions(self):
        script = _Script(_SAVE_ANSWERS)
        store = _Store()
        result = W.run_wizard(_io(script, store=store), ask_defaults=False)
        self.assertTrue(result.saved)
        self.assertFalse(any("default" in p.lower() for p in script.prompts))
        self.assertIsNone(store.writes[0].default_profile_for("oc"))


class SessionLoopTests(unittest.TestCase):
    """The "Configure another profile?" loop belongs to an EXPLICIT session caller only."""

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

    def test_declined_save_leaves_the_bytes_identical(self):
        W.run_wizard(self._io_on_disk(_Script(["gem", "1", "1", "", "n"])))
        self.assertEqual(self.path.read_bytes(), self.before)

    def test_cancel_leaves_the_bytes_identical(self):
        W.run_wizard(self._io_on_disk(_Script(["gem", "q"])))
        self.assertEqual(self.path.read_bytes(), self.before)

    def test_eof_leaves_the_bytes_identical(self):
        W.run_wizard(self._io_on_disk(_Script([])))
        self.assertEqual(self.path.read_bytes(), self.before)

    def test_interrupt_leaves_the_bytes_identical(self):
        W.run_wizard(self._io_on_disk(_Script(_SAVE_ANSWERS, interrupt_at=3)))
        self.assertEqual(self.path.read_bytes(), self.before)

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
        script = _Script(_SAVE_ANSWERS + ["y", "y"])
        os.environ["AW_TEST_FAKE_SECRET"] = SENTINEL_SECRET
        self.addCleanup(os.environ.pop, "AW_TEST_FAKE_SECRET", None)
        result = W.run_wizard(_io(script, store=_Store()))
        self.assertTrue(result.saved)
        haystack = script.text + "\n".join(script.prompts) + "\n".join(result.messages)
        self.assertNotIn(SENTINEL_SECRET, haystack)
        self.assertNotIn("apiKey", haystack)

    def test_the_wizard_never_shells_out_or_evaluates_text(self):
        import inspect

        src = inspect.getsource(W)
        for forbidden in ("shell=True", "os.system", "eval(", "exec("):
            self.assertNotIn(
                forbidden, src, f"{forbidden} must not appear in the wizard"
            )

    def test_the_wizard_reads_no_environment_variable(self):
        import inspect

        src = inspect.getsource(W)
        for forbidden in ("os.environ", "getenv"):
            self.assertNotIn(forbidden, src)

    def test_the_wizard_never_writes_opencode_configuration(self):
        import inspect

        src = inspect.getsource(W)
        for forbidden in ("write_config", "opencode.json", "--refresh"):
            self.assertNotIn(forbidden, src)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

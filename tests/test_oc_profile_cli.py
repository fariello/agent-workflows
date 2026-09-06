"""Tests for runprofile Order 02 (`p0l1to`) E-03/E-04: the `aw oc profile` CLI verbs.

WHAT THIS SUITE IS REQUIRED TO FAIL ON (plan E-05 / V-03):

  * a dynamic command surface  - the verbs must be FIXED, so a profile name is only ever an
                                 ARGUMENT and `status`/`report`/`run` stay legal profile names.
  * a silent overwrite         - `add` on an existing name must refuse (exit 2) and leave the
                                 config BYTE-IDENTICAL unless `--replace` is passed.
  * a guessed noninteractive   - without a TTY, an incomplete `add` must refuse rather than prompt
    invocation                   (which would hang) or invent a model.
  * a dangling default         - removing the default profile must force an explicit decision.
  * a broken output contract   - `--json`/`--agent` must go through the shared renderer and must
                                 not leak a home path into a machine record.
  * a regressed neighbour      - `aw oc run`'s REMAINDER forwarding, `aw oc update-models`
                                 dispatch, and the repo-wide `--agent` output flag must all be
                                 unchanged by the new namespace.

EVERY TEST REDIRECTS `XDG_CONFIG_HOME` to a temporary directory, so no test reads or writes the
developer's own `runner-profiles.json`. Model identifiers are SYNTHETIC (see
`tests/test_runner_profiles.py` for why).
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import cli
from agent_workflows import runner_profiles as RP

_FLASH = "example-vendor/flash-3.7"
_INHOUSE = "example-gw/inhouse/pt3-sonnet-5-1m-us"
_SOL = "example-openai/gpt-sol-5.6"


def _run_cli(argv, stdin_isatty: bool = False):
    """Run `aw <argv...>` capturing (rc, stdout, stderr) with an explicit TTY decision.

    ``stdin_isatty`` controls only whether the verbs believe they may PROMPT; stdout stays a
    non-TTY StringIO, which is what makes the human-vs-agent selection deterministic here.
    """

    out, err = io.StringIO(), io.StringIO()
    rc = 0
    with mock.patch("sys.stdin") as fake_stdin:
        fake_stdin.isatty.return_value = stdin_isatty
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as exc:
                rc = exc.code if isinstance(exc.code, int) else 1
    return rc, out.getvalue(), err.getvalue()


class _IsolatedStore(unittest.TestCase):
    """Base class pointing the profile store at a temp XDG dir for every test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name
        self.addCleanup(self._restore_xdg)
        self.store = Path(self._tmp.name) / "agent-workflows" / "runner-profiles.json"

    def _restore_xdg(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg

    def _seed(self, **profiles) -> RP.ProfileConfig:
        cfg = RP.empty_config()
        for name, model in profiles.items():
            cfg = RP.add_profile(cfg, name, RP.LaunchProfile(runner="oc", model=model))
        RP.save(cfg, self.store)
        return RP.load(self.store)

    def _bytes(self) -> bytes:
        return self.store.read_bytes() if self.store.exists() else b""


# ==================================================================================================
# Parser surface (E-03)
# ==================================================================================================


class ParserSurfaceTests(unittest.TestCase):
    def test_oc_help_lists_the_profile_verb(self):
        rc, out, err = _run_cli(["oc", "--help"])
        text = out + err
        self.assertEqual(rc, 0)
        self.assertIn("profile", text)

    def test_profile_help_lists_every_verb(self):
        rc, out, err = _run_cli(["oc", "profile", "--help"])
        text = out + err
        self.assertEqual(rc, 0)
        for verb in ("add", "list", "show", "remove", "default"):
            self.assertIn(verb, text, f"{verb} missing from 'aw oc profile --help'")

    def test_add_help_shows_every_flag(self):
        rc, out, err = _run_cli(["oc", "profile", "add", "--help"])
        text = out + err
        self.assertEqual(rc, 0)
        for flag in (
            "--model",
            "--variant",
            "--oc-agent",
            "--replace",
            "--yes",
            "--set-default",
        ):
            self.assertIn(flag, text, f"{flag} missing from --help")

    def test_help_does_not_overclaim_variant_support_or_opencode_mutation(self):
        _rc, out, err = _run_cli(["oc", "profile", "--help"])
        text = (out + err).replace("\n", " ")
        self.assertIn("read-only", text)
        self.assertIn("never refreshes", text)

    def test_the_verbs_are_FIXED_so_a_profile_name_is_never_a_command(self):
        """A dynamic per-profile subcommand would make every alias a namespace change."""
        rc, _out, err = _run_cli(["oc", "profile", "gem"])
        self.assertEqual(rc, 2)
        self.assertIn("invalid choice", err)

    def test_command_like_profile_names_remain_legal_arguments(self):
        parser = cli._build_parser()
        for name in ("status", "report", "run", "show", "evidence"):
            ns = parser.parse_args(["oc", "profile", "show", name])
            self.assertEqual(ns.name, name)

    def test_the_repo_wide_agent_output_flag_is_intact(self):
        """REGRESSION GUARD, and not a hypothetical one.

        argparse `parents=` SHARES action objects, and this file's `conflict_handler="resolve"`
        mutates the shared object IN PLACE. Declaring `--agent` on a `parents=[common]` subparser
        therefore EMPTIED the global `--agent`'s option strings, after which every command parsed
        with `agent=True` permanently on. Measured during E-03; the profile's OpenCode-agent field
        is spelled `--oc-agent` because of it.
        """
        parser = cli._build_parser()
        self.assertFalse(parser.parse_args(["attention"]).agent)
        self.assertTrue(parser.parse_args(["attention", "--agent"]).agent)
        self.assertTrue(parser.parse_args(["oc", "profile", "list", "--agent"]).agent)
        agent_actions = [a for a in parser._actions if a.dest == "agent"]
        self.assertEqual([a.option_strings for a in agent_actions], [["--agent"]])

    def test_bare_profile_shows_family_help_rather_than_acting(self):
        rc, _out, _err = _run_cli(["oc", "profile"])
        self.assertEqual(rc, 2)


class NeighbouringVerbsUnchangedTests(unittest.TestCase):
    """V-03: the new namespace must not disturb `oc run` or `oc update-models`."""

    def test_oc_run_still_forwards_its_REMAINDER_verbatim(self):
        with mock.patch("agent_workflows.oc_runipd.main", return_value=0) as fake:
            rc = cli.main(
                ["oc", "run", "somesel", "--action", "review", "--weird-flag"]
            )
        self.assertEqual(rc, 0)
        fake.assert_called_once_with(["somesel", "--action", "review", "--weird-flag"])

    def test_oc_update_models_still_dispatches_from_the_namespace(self):
        with mock.patch("agent_workflows.oc_models.run", return_value=0) as fake:
            rc = cli.main(["oc", "update-models", "--apply"])
        self.assertEqual(rc, 0)
        fake.assert_called_once_with(["--apply"])

    def test_profile_dispatch_does_not_reach_the_runner(self):
        with mock.patch("agent_workflows.oc_runipd.main", return_value=0) as fake:
            _run_cli(["oc", "profile", "list"])
        fake.assert_not_called()


# ==================================================================================================
# add (E-03 / E-04)
# ==================================================================================================


class AddTests(_IsolatedStore):
    def test_the_complete_noninteractive_form_saves(self):
        rc, out, _err = _run_cli(
            [
                "oc",
                "profile",
                "add",
                "gem",
                "--model",
                _FLASH,
                "--variant",
                "high",
                "--yes",
            ]
        )
        self.assertEqual(rc, 0)
        cfg = RP.load(self.store)
        self.assertEqual(cfg.profiles["gem"].model, _FLASH)
        self.assertEqual(cfg.profiles["gem"].variant, "high")
        self.assertIn("--model", out)

    def test_an_agent_is_stored_via_oc_agent(self):
        rc, _out, _err = _run_cli(
            [
                "oc",
                "profile",
                "add",
                "gem",
                "--model",
                _FLASH,
                "--oc-agent",
                "build",
                "--yes",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(RP.load(self.store).profiles["gem"].agent, "build")

    def test_no_variant_means_the_provider_default_and_stores_nothing(self):
        _run_cli(["oc", "profile", "add", "gem", "--model", _FLASH, "--yes"])
        self.assertIsNone(RP.load(self.store).profiles["gem"].variant)
        doc = json.loads(self.store.read_text(encoding="utf-8"))
        self.assertNotIn("variant", doc["profiles"]["gem"])

    def test_a_duplicate_is_refused_and_the_bytes_are_unchanged(self):
        self._seed(gem=_FLASH)
        before = self._bytes()
        rc, _out, err = _run_cli(
            ["oc", "profile", "add", "gem", "--model", _SOL, "--yes"]
        )
        self.assertEqual(rc, 2)
        self.assertIn("already exists", err)
        self.assertEqual(self._bytes(), before, "a refused add changed the config")

    def test_replace_is_the_explicit_opt_in_to_overwrite(self):
        self._seed(gem=_FLASH)
        rc, _out, _err = _run_cli(
            ["oc", "profile", "add", "gem", "--model", _SOL, "--yes", "--replace"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(RP.load(self.store).profiles["gem"].model, _SOL)

    def test_without_a_tty_an_incomplete_add_refuses_and_writes_nothing(self):
        rc, _out, err = _run_cli(["oc", "profile", "add", "gem"])
        self.assertEqual(rc, 2)
        self.assertIn("no TTY", err)
        self.assertFalse(self.store.exists())

    def test_the_noninteractive_form_requires_yes(self):
        rc, _out, err = _run_cli(["oc", "profile", "add", "gem", "--model", _FLASH])
        self.assertEqual(rc, 2)
        self.assertIn("--yes is required", err)
        self.assertFalse(self.store.exists())

    def test_model_without_a_name_is_refused(self):
        rc, _out, err = _run_cli(["oc", "profile", "add", "--model", _FLASH, "--yes"])
        self.assertEqual(rc, 2)
        self.assertIn("NAME is required", err)
        self.assertFalse(self.store.exists())

    def test_yes_cannot_preconfirm_the_interactive_form(self):
        rc, _out, err = _run_cli(
            ["oc", "profile", "add", "gem", "--yes"], stdin_isatty=True
        )
        self.assertEqual(rc, 2)
        self.assertIn("complete noninteractive form", err)
        self.assertFalse(self.store.exists())

    def test_an_invalid_model_is_refused_with_the_schemas_message(self):
        rc, _out, err = _run_cli(
            ["oc", "profile", "add", "gem", "--model", "nope", "--yes"]
        )
        self.assertEqual(rc, 2)
        self.assertIn("provider/model", err)
        self.assertFalse(self.store.exists())

    def test_an_invalid_profile_name_is_refused(self):
        rc, _out, err = _run_cli(
            ["oc", "profile", "add", "As", "--model", _FLASH, "--yes"]
        )
        self.assertEqual(rc, 2)
        self.assertIn("invalid profile name", err)

    def test_a_reserved_grammar_word_cannot_be_a_profile_name(self):
        rc, _out, err = _run_cli(
            ["oc", "profile", "add", "as", "--model", _FLASH, "--yes"]
        )
        self.assertEqual(rc, 2)
        self.assertIn("reserved", err)

    def test_add_never_sets_a_default_implicitly(self):
        """E-04: the FIRST profile does not silently become the default."""
        _run_cli(["oc", "profile", "add", "gem", "--model", _FLASH, "--yes"])
        cfg = RP.load(self.store)
        self.assertIsNone(cfg.default_profile_for("oc"))
        self.assertIsNone(cfg.default_runner)

    def test_set_default_is_the_explicit_opt_in_and_is_ONE_write(self):
        with mock.patch("agent_workflows.runner_profiles.save", wraps=RP.save) as spy:
            rc, _out, _err = _run_cli(
                [
                    "oc",
                    "profile",
                    "add",
                    "gem",
                    "--model",
                    _FLASH,
                    "--yes",
                    "--set-default",
                ]
            )
        self.assertEqual(rc, 0)
        self.assertEqual(
            spy.call_count, 1, "profile + default must be one atomic write"
        )
        self.assertEqual(RP.load(self.store).default_profile_for("oc"), "gem")

    def test_add_never_touches_opencode_configuration(self):
        opencode_cfg = Path(self._tmp.name) / "opencode" / "opencode.json"
        opencode_cfg.parent.mkdir(parents=True, exist_ok=True)
        opencode_cfg.write_text(
            '{"model": "example-vendor/flash-3.7"}\n', encoding="utf-8"
        )
        before = opencode_cfg.read_bytes()
        _run_cli(["oc", "profile", "add", "gem", "--model", _FLASH, "--yes"])
        self.assertEqual(opencode_cfg.read_bytes(), before)

    def test_the_interactive_form_runs_the_wizard(self):
        with mock.patch("agent_workflows.runner_profile_wizard.run_wizard") as fake:
            from agent_workflows import runner_profile_wizard as wiz

            fake.return_value = wiz.WizardResult(saved=True, name="gem")
            rc, _out, _err = _run_cli(["oc", "profile", "add"], stdin_isatty=True)
        self.assertEqual(rc, 0)
        self.assertTrue(fake.called)
        # The name is passed through as None so the wizard prompts for it.
        self.assertIsNone(fake.call_args[0][1])

    def test_a_declined_wizard_exits_nonzero_without_claiming_success(self):
        with mock.patch("agent_workflows.runner_profile_wizard.run_wizard") as fake:
            from agent_workflows import runner_profile_wizard as wiz

            fake.return_value = wiz.WizardResult(saved=False, reason="declined")
            rc, _out, _err = _run_cli(
                ["oc", "profile", "add", "gem"], stdin_isatty=True
            )
        self.assertEqual(rc, 1)


# ==================================================================================================
# list / show (E-03)
# ==================================================================================================


class ListShowTests(_IsolatedStore):
    def test_an_empty_list_is_a_clean_result_not_an_error(self):
        rc, out, _err = _run_cli(["oc", "profile", "list"])
        self.assertEqual(rc, 0)
        self.assertIn("no runner profiles", out)

    def test_list_json_carries_every_profile_and_the_default(self):
        cfg = self._seed(gem=_FLASH, sol=_SOL)
        RP.save(RP.set_default_profile(cfg, "gem"), self.store)
        rc, out, _err = _run_cli(["oc", "profile", "list", "--json"])
        self.assertEqual(rc, 0)
        payload = json.loads(out)
        self.assertEqual(payload["command"], "oc profile list")
        names = [entry["name"] for entry in payload["data"]["profiles"]]
        self.assertEqual(names, ["gem", "sol"])
        self.assertEqual(payload["data"]["default_profile"], "gem")
        gem = payload["data"]["profiles"][0]
        self.assertTrue(gem["is_default"])
        self.assertEqual(gem["opencode_args"], ["--model", _FLASH])

    def test_list_agent_output_is_one_jsonl_record(self):
        self._seed(gem=_FLASH)
        rc, out, _err = _run_cli(["oc", "profile", "list", "--agent"])
        self.assertEqual(rc, 0)
        lines = [line for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["schema"], "aw.agent/v1")
        self.assertEqual(record["cmd"], "oc profile list")
        self.assertEqual(record["exit"], 0)

    def test_no_machine_record_leaks_a_home_path(self):
        """docs/cli-output-contract.md:90 - path fields must be free of /home/<user>/."""
        self._seed(gem=_FLASH)
        home = str(Path.home())
        for flags in (["--json"], ["--agent"]):
            _rc, out, _err = _run_cli(["oc", "profile", "list", *flags])
            self.assertNotIn(home, out, f"{flags} leaked a home path")

    def test_the_store_path_is_home_preserved_when_under_home(self):
        fake_home_xdg = Path.home() / ".aw-test-profile-store"
        os.environ["XDG_CONFIG_HOME"] = str(fake_home_xdg)
        self.addCleanup(self._restore_xdg)
        target = fake_home_xdg / "agent-workflows" / "runner-profiles.json"
        self.addCleanup(
            lambda: __import__("shutil").rmtree(fake_home_xdg, ignore_errors=True)
        )
        RP.save(
            RP.add_profile(
                RP.empty_config(), "gem", RP.LaunchProfile(runner="oc", model=_FLASH)
            ),
            target,
        )
        _rc, out, _err = _run_cli(["oc", "profile", "list", "--json"])
        payload = json.loads(out)
        self.assertTrue(
            payload["data"]["store"].startswith("~/"), payload["data"]["store"]
        )

    def test_show_prints_the_exact_launch(self):
        self._seed(gem=_FLASH)
        rc, out, _err = _run_cli(["oc", "profile", "show", "gem"])
        self.assertEqual(rc, 0)
        self.assertIn(f"opencode run --model {_FLASH}", out)

    def test_show_of_an_unknown_profile_is_an_actionable_exit_2(self):
        self._seed(gem=_FLASH)
        rc, _out, err = _run_cli(["oc", "profile", "show", "nope"])
        self.assertEqual(rc, 2)
        self.assertIn("no runner profile named", err)
        self.assertIn("gem", err, "the error should list the known profiles")

    def test_a_malformed_store_is_reported_not_treated_as_empty(self):
        """A broken file must never look like "you have no profiles"."""
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text("{not json", encoding="utf-8")
        rc, _out, err = _run_cli(["oc", "profile", "list"])
        self.assertEqual(rc, 2)
        self.assertIn("not valid JSON", err)

    def test_json_output_carries_no_credential_shaped_field(self):
        self._seed(gem=_FLASH)
        _rc, out, _err = _run_cli(["oc", "profile", "show", "gem", "--json"])
        for forbidden in ("apiKey", "api_key", "token", "secret", "Authorization"):
            self.assertNotIn(forbidden, out)


# ==================================================================================================
# remove / default (E-03)
# ==================================================================================================


class RemoveTests(_IsolatedStore):
    def test_remove_deletes_the_profile(self):
        self._seed(gem=_FLASH, sol=_SOL)
        rc, _out, _err = _run_cli(["oc", "profile", "remove", "gem", "--yes"])
        self.assertEqual(rc, 0)
        self.assertEqual(sorted(RP.load(self.store).profiles), ["sol"])

    def test_removing_the_default_demands_an_explicit_decision(self):
        cfg = self._seed(gem=_FLASH, sol=_SOL)
        RP.save(RP.set_default_profile(cfg, "gem"), self.store)
        before = self._bytes()
        rc, _out, err = _run_cli(["oc", "profile", "remove", "gem", "--yes"])
        self.assertEqual(rc, 2)
        self.assertIn("Decide explicitly", err)
        self.assertEqual(self._bytes(), before)

    def test_clear_default_is_one_of_the_two_explicit_decisions(self):
        cfg = self._seed(gem=_FLASH)
        RP.save(RP.set_default_profile(cfg, "gem"), self.store)
        rc, _out, _err = _run_cli(
            ["oc", "profile", "remove", "gem", "--yes", "--clear-default"]
        )
        self.assertEqual(rc, 0)
        after = RP.load(self.store)
        self.assertEqual(dict(after.profiles), {})
        self.assertIsNone(after.default_profile_for("oc"))

    def test_a_replacement_is_the_other_explicit_decision(self):
        cfg = self._seed(gem=_FLASH, sol=_SOL)
        RP.save(RP.set_default_profile(cfg, "gem"), self.store)
        rc, _out, _err = _run_cli(
            ["oc", "profile", "remove", "gem", "--yes", "--replacement", "sol"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(RP.load(self.store).default_profile_for("oc"), "sol")

    def test_removing_an_unknown_profile_is_exit_2(self):
        self._seed(gem=_FLASH)
        before = self._bytes()
        rc, _out, err = _run_cli(["oc", "profile", "remove", "nope", "--yes"])
        self.assertEqual(rc, 2)
        self.assertIn("no runner profile named", err)
        self.assertEqual(self._bytes(), before)

    def test_without_a_tty_remove_requires_yes(self):
        self._seed(gem=_FLASH)
        before = self._bytes()
        rc, _out, err = _run_cli(["oc", "profile", "remove", "gem"])
        self.assertEqual(rc, 2)
        self.assertIn("--yes", err)
        self.assertEqual(self._bytes(), before)


class DefaultTests(_IsolatedStore):
    def test_default_sets_the_profile(self):
        self._seed(gem=_FLASH)
        rc, _out, _err = _run_cli(["oc", "profile", "default", "gem"])
        self.assertEqual(rc, 0)
        self.assertEqual(RP.load(self.store).default_profile_for("oc"), "gem")

    def test_clear_removes_it(self):
        cfg = self._seed(gem=_FLASH)
        RP.save(RP.set_default_profile(cfg, "gem"), self.store)
        rc, _out, _err = _run_cli(["oc", "profile", "default", "--clear"])
        self.assertEqual(rc, 0)
        self.assertIsNone(RP.load(self.store).default_profile_for("oc"))

    def test_naming_an_unknown_profile_is_exit_2_and_changes_nothing(self):
        self._seed(gem=_FLASH)
        before = self._bytes()
        rc, _out, err = _run_cli(["oc", "profile", "default", "nope"])
        self.assertEqual(rc, 2)
        self.assertIn("no runner profile named", err)
        self.assertEqual(self._bytes(), before)

    def test_a_name_and_clear_together_are_refused(self):
        self._seed(gem=_FLASH)
        rc, _out, err = _run_cli(["oc", "profile", "default", "gem", "--clear"])
        self.assertEqual(rc, 2)
        self.assertIn("not both", err)

    def test_neither_a_name_nor_clear_is_refused(self):
        rc, _out, err = _run_cli(["oc", "profile", "default"])
        self.assertEqual(rc, 2)
        self.assertIn("--clear", err)

    def test_default_json_reports_the_new_value(self):
        self._seed(gem=_FLASH)
        rc, out, _err = _run_cli(["oc", "profile", "default", "gem", "--json"])
        self.assertEqual(rc, 0)
        payload = json.loads(out)
        self.assertEqual(payload["data"]["default_profile"], "gem")
        self.assertEqual(payload["exit_code"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

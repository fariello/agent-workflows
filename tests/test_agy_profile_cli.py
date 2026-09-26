"""Tests for `aw agy profile` CLI verbs, refusals, and cross-namespace guards."""

import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import cli, runner_profiles as rp


def _run_cli(argv):
    """Run `cli.main(argv)` capturing stdout and stderr."""
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            code = cli.main(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    return code, stdout_buf.getvalue(), stderr_buf.getvalue()


class AgyProfileCliTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(self.base / "cfg")
        self._old_nocolor = os.environ.get("NO_COLOR")
        os.environ["NO_COLOR"] = "1"
        self.store_path = self.base / "cfg" / "agent-workflows" / "runner-profiles.json"

    def tearDown(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg
        if self._old_nocolor is None:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = self._old_nocolor
        self._tmp.cleanup()


class TestAgyProfileWritePath(AgyProfileCliTestBase):
    """E-07: agy write path, runner filtering, and validate-default."""

    def test_01_agy_add_no_validate_set_default(self):
        """(a) agy add with --no-validate --set-default writes expected JSON and resolves False."""
        code, out, err = _run_cli(
            [
                "agy",
                "profile",
                "add",
                "quiet",
                "--model",
                "google/gemini-3-pro",
                "--no-validate",
                "--set-default",
                "--yes",
            ]
        )
        self.assertEqual(code, 0, f"stderr: {err}")
        self.assertTrue(self.store_path.exists())
        with open(self.store_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["profiles"]["quiet"]["runner"], "agy")
        self.assertEqual(data["profiles"]["quiet"]["validate"], False)
        self.assertEqual(data["defaults"]["profiles"]["agy"], "quiet")

        cfg = rp.load()
        resolved = rp.resolve(cfg, runner="agy")
        self.assertFalse(resolved.validate)
        self.assertEqual(resolved.provenance["validate"], "default-profile")

    def test_02_agy_list_filters_by_runner(self):
        """(b) aw agy profile list omits an oc profile in the same store."""
        # Add oc profile
        code, _, _ = _run_cli(
            [
                "oc",
                "profile",
                "add",
                "ocprof",
                "--model",
                "anthropic/claude-3-5-sonnet",
                "--yes",
            ]
        )
        self.assertEqual(code, 0)

        # Add agy profile
        code, _, _ = _run_cli(
            [
                "agy",
                "profile",
                "add",
                "agyprof",
                "--model",
                "google/gemini-3-pro",
                "--yes",
            ]
        )
        self.assertEqual(code, 0)

        # agy profile list --json
        code, out, _ = _run_cli(["agy", "profile", "list", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data.get("command"), "agy profile list")
        self.assertEqual(data["data"]["count"], 1)
        self.assertEqual(data["data"]["profiles"][0]["name"], "agyprof")
        self.assertEqual(data["data"]["profiles"][0]["runner"], "agy")

        # Table output
        code, out, _ = _run_cli(["agy", "profile", "list"])
        self.assertEqual(code, 0)
        self.assertIn("agyprof", out)
        self.assertNotIn("ocprof", out)

    def test_03_agy_show_no_opencode_run_and_json_null(self):
        """(c) aw agy profile show contains no opencode run and --json carries opencode_args as null."""
        code, _, _ = _run_cli(
            [
                "agy",
                "profile",
                "add",
                "quiet",
                "--model",
                "google/gemini-3-pro",
                "--yes",
            ]
        )
        self.assertEqual(code, 0)

        # Plain show
        code, out, _ = _run_cli(["agy", "profile", "show", "quiet"])
        self.assertEqual(code, 0)
        self.assertNotIn("opencode run", out)
        self.assertIn("defaults.profiles.agy", out)
        self.assertIn("Antigravity effect", out)

        # JSON show
        code, out, _ = _run_cli(["agy", "profile", "show", "quiet", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data.get("command"), "agy profile show")
        self.assertIn("opencode_args", data["data"]["profile"])
        self.assertIsNone(data["data"]["profile"]["opencode_args"])

    def test_04_validate_default_roundtrip(self):
        """(d) validate-default on|off|unset roundtrips defaults.validate and unset removes the key."""
        code, out, err = _run_cli(["agy", "profile", "validate-default", "off"])
        self.assertEqual(code, 0, f"stderr: {err}")
        with open(self.store_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["defaults"]["validate"], False)

        code, out, err = _run_cli(["oc", "profile", "validate-default", "on"])
        self.assertEqual(code, 0, f"stderr: {err}")
        with open(self.store_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["defaults"]["validate"], True)

        code, out, err = _run_cli(["agy", "profile", "validate-default", "unset"])
        self.assertEqual(code, 0, f"stderr: {err}")
        with open(self.store_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        defaults = data.get("defaults", {})
        self.assertNotIn("validate", defaults)


class TestAgyProfileAddRefusals(AgyProfileCliTestBase):
    """E-08: Add-form refusal tests covering noninteractive contract and store unchanged."""

    def test_01_refusal_add_without_yes_store_absent(self):
        """Add without --yes exits 2 and store remains absent."""
        code, out, err = _run_cli(
            ["agy", "profile", "add", "quiet", "--model", "google/gemini-3-pro"]
        )
        self.assertEqual(code, 2)
        self.assertIn("--yes is required", err)
        self.assertFalse(self.store_path.exists())

    def test_02_refusal_add_without_model_store_absent(self):
        """Add without --model exits 2 and store remains absent."""
        code, out, err = _run_cli(["agy", "profile", "add", "quiet", "--yes"])
        self.assertEqual(code, 2)
        self.assertIn("noninteractive only", err)
        self.assertFalse(self.store_path.exists())

    def test_03_refusal_existing_name_without_replace_store_byte_identical(self):
        """Add of an existing name without --replace exits 2 and store is byte-identical."""
        code, _, _ = _run_cli(
            [
                "agy",
                "profile",
                "add",
                "quiet",
                "--model",
                "google/gemini-3-pro",
                "--yes",
            ]
        )
        self.assertEqual(code, 0)
        orig_bytes = self.store_path.read_bytes()

        # Attempt to add same profile without --replace
        code, out, err = _run_cli(
            [
                "agy",
                "profile",
                "add",
                "quiet",
                "--model",
                "google/gemini-3-pro",
                "--yes",
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("already exists", err)
        self.assertEqual(self.store_path.read_bytes(), orig_bytes)

    def test_04_refusal_variant_flag_rejected_by_argparse(self):
        """--variant for agy is rejected by argparse (exit 2) and store is absent."""
        code, out, err = _run_cli(
            [
                "agy",
                "profile",
                "add",
                "quiet",
                "--model",
                "google/gemini-3-pro",
                "--variant",
                "high",
                "--yes",
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("unrecognized arguments: --variant", err)
        self.assertFalse(self.store_path.exists())


class TestAgyProfileCrossNamespaceRefusals(AgyProfileCliTestBase):
    """E-09: Cross-namespace refusal tests (E-04 guard)."""

    def setUp(self):
        super().setUp()
        # Seed store with one oc profile
        code, _, _ = _run_cli(
            [
                "oc",
                "profile",
                "add",
                "gem",
                "--model",
                "google/gemini-2.0-flash",
                "--yes",
            ]
        )
        self.assertEqual(code, 0)
        self.orig_bytes = self.store_path.read_bytes()

    def test_01_agy_show_oc_profile_refuses_exit_2_and_bytes_unchanged(self):
        """`aw agy profile show gem` exits 2 naming oc and leaves store byte-identical."""
        code, out, err = _run_cli(["agy", "profile", "show", "gem"])
        self.assertEqual(code, 2)
        self.assertIn("belongs to runner 'oc', not 'agy'", err)
        self.assertEqual(self.store_path.read_bytes(), self.orig_bytes)

    def test_02_agy_remove_oc_profile_refuses_exit_2_and_bytes_unchanged(self):
        """`aw agy profile remove gem --yes` exits 2 naming oc and leaves store byte-identical."""
        code, out, err = _run_cli(["agy", "profile", "remove", "gem", "--yes"])
        self.assertEqual(code, 2)
        self.assertIn("belongs to runner 'oc', not 'agy'", err)
        self.assertEqual(self.store_path.read_bytes(), self.orig_bytes)

    def test_03_agy_default_oc_profile_refuses_exit_2_and_bytes_unchanged(self):
        """`aw agy profile default gem` exits 2 naming oc and leaves store byte-identical."""
        code, out, err = _run_cli(["agy", "profile", "default", "gem"])
        self.assertEqual(code, 2)
        self.assertIn("belongs to runner 'oc', not 'agy'", err)
        self.assertEqual(self.store_path.read_bytes(), self.orig_bytes)

    def test_04_oc_show_gem_succeeds(self):
        """`aw oc profile show gem` succeeds on the same store."""
        code, out, err = _run_cli(["oc", "profile", "show", "gem"])
        self.assertEqual(code, 0)
        self.assertIn("Profile 'gem' will be stored as:", out)
        self.assertIn("runner:  oc", out)

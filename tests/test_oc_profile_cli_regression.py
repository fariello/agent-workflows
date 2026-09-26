"""Regression tests for `aw oc profile` CLI verbs.

Baseline guard for E-01 refactoring: ensures that all five verbs (`add`, `list`,
`show`, `remove`, `default`) retain exact output, exit codes, and structured
command labels (`oc profile <verb>`).
"""

import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import cli


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


class TestOcProfileCliRegression(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(self.base / "cfg")
        self._old_nocolor = os.environ.get("NO_COLOR")
        os.environ["NO_COLOR"] = "1"

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

    def test_01_add_plain_and_json(self):
        """Cover verb 1: `add` (plain and --json)."""
        # Plain noninteractive add
        code, out, err = _run_cli(
            [
                "oc",
                "profile",
                "add",
                "gem",
                "--model",
                "google/gemini-2.0-flash",
                "--variant",
                "high",
                "--yes",
            ]
        )
        self.assertEqual(code, 0, f"err: {err}")
        self.assertIn("Profile 'gem' will be stored as:", out)
        self.assertIn("runner:  oc", out)
        self.assertIn("model:   google/gemini-2.0-flash", out)
        self.assertIn("variant: high", out)
        self.assertIn("Equivalent OpenCode launch:", out)
        self.assertIn(
            "opencode run --model google/gemini-2.0-flash --variant high", out
        )
        self.assertIn("Saved. Use it with: aw oc run as gem", out)

        # Noninteractive add with --json and --set-default
        code, out, err = _run_cli(
            [
                "oc",
                "profile",
                "add",
                "sonnet",
                "--model",
                "anthropic/claude-3-5-sonnet",
                "--yes",
                "--set-default",
                "--json",
            ]
        )
        self.assertEqual(code, 0, f"err: {err}")
        data = json.loads(out)
        self.assertEqual(data.get("command"), "oc profile add")
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("exit_code"), 0)
        self.assertEqual(data["data"]["profile"]["runner"], "oc")
        self.assertEqual(
            data["data"]["profile"]["model"], "anthropic/claude-3-5-sonnet"
        )
        self.assertEqual(data["data"]["default_profile"], "sonnet")

    def test_02_list_table_and_json(self):
        """Cover verb 2: `list` / `ls` (empty and populated, table and --json)."""
        # Empty list
        code, out, err = _run_cli(["oc", "profile", "list", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data.get("command"), "oc profile list")
        self.assertEqual(data["data"]["count"], 0)

        # Add one profile
        code, _, _ = _run_cli(
            [
                "oc",
                "profile",
                "add",
                "gem",
                "--model",
                "google/gemini-2.0-flash",
                "--variant",
                "high",
                "--yes",
            ]
        )
        self.assertEqual(code, 0)

        # Table list
        code, out, err = _run_cli(["oc", "profile", "list"])
        self.assertEqual(code, 0)
        self.assertIn("NAME", out)
        self.assertIn("RUNNER", out)
        self.assertIn("MODEL", out)
        self.assertIn("VARIANT", out)
        self.assertIn("AGENT", out)
        self.assertIn("gem", out)
        self.assertIn("oc", out)
        self.assertIn("google/gemini-2.0-flash", out)
        self.assertIn("high", out)

        # Structured list with `ls` alias
        code, out, err = _run_cli(["oc", "profile", "ls", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data.get("command"), "oc profile list")
        self.assertEqual(data["data"]["count"], 1)
        self.assertEqual(data["data"]["profiles"][0]["name"], "gem")
        self.assertEqual(data["data"]["profiles"][0]["runner"], "oc")

    def test_03_show_plain_and_json(self):
        """Cover verb 3: `show` (plain and --json)."""
        code, _, _ = _run_cli(
            [
                "oc",
                "profile",
                "add",
                "gem",
                "--model",
                "google/gemini-2.0-flash",
                "--variant",
                "high",
                "--yes",
            ]
        )
        self.assertEqual(code, 0)

        # Plain show
        code, out, err = _run_cli(["oc", "profile", "show", "gem"])
        self.assertEqual(code, 0)
        self.assertIn("Profile 'gem' will be stored as:", out)
        self.assertIn("runner:  oc", out)
        self.assertIn("model:   google/gemini-2.0-flash", out)
        self.assertIn("variant: high", out)
        self.assertIn("Equivalent OpenCode launch:", out)
        self.assertIn(
            "opencode run --model google/gemini-2.0-flash --variant high", out
        )

        # Json show
        code, out, err = _run_cli(["oc", "profile", "show", "gem", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data.get("command"), "oc profile show")
        self.assertEqual(data["data"]["profile"]["name"], "gem")
        self.assertEqual(data["data"]["profile"]["runner"], "oc")
        self.assertEqual(
            data["data"]["profile"]["opencode_args"],
            ["--model", "google/gemini-2.0-flash", "--variant", "high"],
        )

    def test_04_default_set_and_clear(self):
        """Cover verb 4: `default` (set and --clear, plain and --json)."""
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

        # Set default plain
        code, out, err = _run_cli(["oc", "profile", "default", "gem"])
        self.assertEqual(code, 0)
        self.assertIn("default OpenCode profile is now 'gem'.", out)

        # Check default in show
        code, out, _ = _run_cli(["oc", "profile", "show", "gem"])
        self.assertIn("'gem' is the default OpenCode profile.", out)

        # Clear default plain
        code, out, err = _run_cli(["oc", "profile", "default", "--clear"])
        self.assertEqual(code, 0)
        self.assertIn("cleared the default OpenCode profile.", out)

        # Set default --json
        code, out, err = _run_cli(["oc", "profile", "default", "gem", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data.get("command"), "oc profile default")
        self.assertEqual(data["data"]["default_profile"], "gem")

        # Clear default --json
        code, out, err = _run_cli(["oc", "profile", "default", "--clear", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data.get("command"), "oc profile default")
        self.assertIsNone(data["data"]["default_profile"])

    def test_05_remove_plain_and_json(self):
        """Cover verb 5: `remove` / `rm` (plain and --json)."""
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

        # Remove plain
        code, out, err = _run_cli(["oc", "profile", "remove", "gem", "--yes"])
        self.assertEqual(code, 0)
        self.assertIn("Removed profile 'gem'.", out)

        # Re-add and remove with `rm` and --json
        code, _, _ = _run_cli(
            [
                "oc",
                "profile",
                "add",
                "gem2",
                "--model",
                "google/gemini-2.0-flash",
                "--yes",
            ]
        )
        self.assertEqual(code, 0)
        code, out, err = _run_cli(["oc", "profile", "rm", "gem2", "--yes", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data.get("command"), "oc profile remove")
        self.assertEqual(data["data"]["removed"], "gem2")

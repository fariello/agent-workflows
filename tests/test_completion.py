"""Tests for tabcomp Order 01 (bja8og): native shell completion generators + `aw completion`.

Covers E-01 (introspect_cli_tree surfaces user commands, excludes the internal `*-gate` family and
the hidden aliases), E-02 (the three generators emit valid, alias-binding, shell-escaped scripts;
each parses under its own shell's syntax checker where installed), E-03 (`aw completion <shell>`
streams the script to stdout with exit 0; bare invocation detects $SHELL with a bash fallback; the
parser shape leaves room for tabcomp-03 install/uninstall), and E-04 (this file).
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from agent_workflows import cli, completion


def _run(argv):
    out = io.StringIO()
    with redirect_stdout(out):
        rc = cli.main(argv)
    return rc, out.getvalue()


class IntrospectTreeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = completion.introspect_cli_tree(cli._build_parser())
        self.top = set(self.tree["subcommands"])

    def test_user_commands_present(self) -> None:
        for cmd in ("install", "check", "doctor", "runs", "ipd", "specs", "completion"):
            self.assertIn(cmd, self.top, f"{cmd} should be a completable command")

    def test_gate_commands_excluded(self) -> None:
        for gate in (
            "ipd-executed-gate",
            "ipd-status-untooled-gate",
            "backlog-blocking-close-gate",
            "ipd-dependency-statement-gate",
            "precommit-scope-gate",
            "prepush-authorization-gate",
        ):
            self.assertNotIn(gate, self.top, f"{gate} must be excluded")
        self.assertFalse(
            any(name.endswith("-gate") for name in self.top),
            "no *-gate command may be completable",
        )

    def test_hidden_aliases_excluded(self) -> None:
        for alias in ("att", "spec", "sanitize", "antigravity", "opencode"):
            self.assertNotIn(alias, self.top, f"{alias} alias must be excluded")

    def test_nested_subcommands_captured(self) -> None:
        # `ipd` has real nested subcommands (e.g. set/begin/finalize/lint) - the tree must recurse.
        self.assertIn("ipd", self.tree["subcommands"])
        ipd_subs = self.tree["subcommands"]["ipd"]["subcommands"]
        self.assertTrue(ipd_subs, "ipd should expose nested subcommands")

    def test_does_not_mutate_parser(self) -> None:
        p = cli._build_parser()
        before = [a.dest for a in p._actions]
        completion.introspect_cli_tree(p)
        after = [a.dest for a in p._actions]
        self.assertEqual(before, after)


class GeneratorSyntaxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = completion.introspect_cli_tree(cli._build_parser())

    def test_bash_required_syntax_and_aliases(self) -> None:
        script = completion.generate_bash_completion(self.tree)
        self.assertTrue(script.strip())
        self.assertIn("_aw_completion()", script)
        self.assertIn("complete -F _aw_completion aw agentwf agent-workflows", script)

    def test_zsh_required_syntax_and_aliases(self) -> None:
        script = completion.generate_zsh_completion(self.tree)
        self.assertTrue(script.strip())
        self.assertIn("#compdef aw agentwf agent-workflows", script)

    def test_fish_required_syntax_and_aliases(self) -> None:
        script = completion.generate_fish_completion(self.tree)
        self.assertTrue(script.strip())
        self.assertIn("complete -c aw", script)
        self.assertIn("complete -c agentwf", script)
        self.assertIn("complete -c agent-workflows", script)

    @unittest.skipUnless(shutil.which("bash"), "bash not installed")
    def test_bash_parses_under_bash_n(self) -> None:
        self._check_shell("bash", ["bash", "-n"], completion.generate_bash_completion)

    @unittest.skipUnless(shutil.which("zsh"), "zsh not installed")
    def test_zsh_parses_under_zsh_n(self) -> None:
        self._check_shell("zsh", ["zsh", "-n"], completion.generate_zsh_completion)

    @unittest.skipUnless(shutil.which("fish"), "fish not installed")
    def test_fish_parses_under_fish_no_execute(self) -> None:
        self._check_shell(
            "fish", ["fish", "--no-execute"], completion.generate_fish_completion
        )

    def _check_shell(self, shell, cmd, gen):
        script = gen(self.tree)
        with tempfile.NamedTemporaryFile("w", suffix=f".{shell}", delete=False) as fh:
            fh.write(script)
            path = fh.name
        try:
            proc = subprocess.run(cmd + [path], capture_output=True, text=True)
            self.assertEqual(
                proc.returncode, 0, f"{shell} -n failed: {proc.stderr}\n{script}"
            )
        finally:
            os.unlink(path)

    def test_escaping_guarantee_backtick_and_dollar(self) -> None:
        # A generated script whose embedded help text contains a backtick / $ must remain valid.
        # Build a tiny synthetic tree carrying hostile help text and assert bash -n still passes
        # (bash is the always-available baseline; the zsh/fish escapers are unit-covered by the
        # syntax tests above where those shells exist).
        hostile = {
            "flags": [
                {
                    "flag": "--danger",
                    "help": "uses `rm -rf $HOME` and 'quotes' and \\ backslash",
                }
            ],
            "subcommands": {
                "cmd`x": {"flags": [], "subcommands": {}},
                "cmd$y": {"flags": [], "subcommands": {}},
            },
        }
        bash_script = completion.generate_bash_completion(hostile)
        if shutil.which("bash"):
            with tempfile.NamedTemporaryFile("w", suffix=".bash", delete=False) as fh:
                fh.write(bash_script)
                path = fh.name
            try:
                proc = subprocess.run(
                    ["bash", "-n", path], capture_output=True, text=True
                )
                self.assertEqual(
                    proc.returncode, 0, f"escaping failed: {proc.stderr}\n{bash_script}"
                )
            finally:
                os.unlink(path)
        # The zsh/fish escapers must not leave a raw unescaped backtick/$ in a description context.
        zsh_desc = completion._zsh_desc("uses `x` and $y")
        self.assertNotIn("`", zsh_desc.replace("\\`", ""))
        self.assertNotIn("$", zsh_desc.replace("\\$", ""))


class CompletionCliTests(unittest.TestCase):
    def test_cli_bash_exit0_and_header(self) -> None:
        rc, out = _run(["completion", "bash"])
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("# bash completion for aw"))

    def test_cli_zsh_and_fish_exit0(self) -> None:
        for shell, needle in (("zsh", "#compdef"), ("fish", "complete -c aw")):
            rc, out = _run(["completion", shell])
            self.assertEqual(rc, 0, shell)
            self.assertIn(needle, out)

    def test_bare_completion_shell_unset_falls_back_to_bash(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SHELL", None)
            rc, out = _run(["completion"])
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("# bash completion for aw"))

    def test_bare_completion_detects_zsh_from_shell_env(self) -> None:
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/zsh"}):
            rc, out = _run(["completion"])
        self.assertEqual(rc, 0)
        self.assertIn("#compdef", out)

    def test_detect_shell_fallback(self) -> None:
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/tcsh"}):
            self.assertEqual(cli._detect_shell(), "bash")
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            self.assertEqual(cli._detect_shell(), "fish")

    def test_parser_shape_allows_child03_extension(self) -> None:
        # Forward-compat: `target` is a free-form optional positional (no fixed choices), so a future
        # `aw completion install`/`uninstall` token parses without a redesign. Confirm the parser
        # accepts a non-shell target token (it reaches the handler, which validates), i.e. the parse
        # itself does not reject it via `choices`.
        parser = cli._build_parser()
        args = parser.parse_args(["completion", "install"])
        self.assertEqual(args.command, "completion")
        self.assertEqual(args.target, "install")  # not constrained by choices=


if __name__ == "__main__":
    unittest.main()

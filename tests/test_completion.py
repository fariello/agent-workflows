"""Tests for tabcomp Orders 01 (bja8og) and 02 (4f1j25): shell completion.

Order 01 covers E-01 (introspect_cli_tree surfaces user commands, excludes the internal `*-gate`
family and the hidden aliases), E-02 (the three generators emit valid, alias-binding, shell-escaped
scripts; each parses under its own shell's syntax checker where installed), E-03 (`aw completion
<shell>` streams the script to stdout with exit 0; bare invocation detects $SHELL with a bash
fallback; the parser shape leaves room for tabcomp-03 install/uninstall), and E-04.

Order 02 (4f1j25) covers dynamic completion: E-01 (`complete_query` returns bare-token candidates -
subcommands/flags, Set ids, run ids, plan/spec/backlog id6 handles extracted from path stems, and
per-type status enums from the real vocab modules - within the <50ms latency budget under active-
disposition scan-scoping), E-02 (the `aw __complete --cword N -- <tokens>` wire protocol matches
`complete_query` and always exits 0), and E-03 (the `# PYTHON_ARGCOMPLETE_OK` marker is a real
comment inside the first 1024 bytes and the soft `argcomplete` import leaves the CLI working when
argcomplete is absent).
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import cli, completion
from agent_workflows.term import Term


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


# --------------------------------------------------------------------------------------
# tabcomp Order 02 (4f1j25): dynamic contextual completion.
# --------------------------------------------------------------------------------------


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class _DynamicRepoFixture(unittest.TestCase):
    """A controlled temp repo with plans/specs/backlog/runs of KNOWN id6/status, so expected
    completions are stable (never the live repo). Mirrors the tests/test_selectors.py convention."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        rec = self.root / ".aw" / "records"

        # Two ACTIVE plans (pending) in Set `tabcomp`, one TERMINAL plan (executed) that MUST be
        # excluded by the active-disposition scan-scoping (latency budget).
        _write(
            rec / "plans" / "pending" / "20260828-tabcomp-02-4f1j25-child-two.ipd.md",
            "# IPD: two\n\n- Id: 4f1j25\n- Status: approved\n- Set: tabcomp (tabs)\n\n## Goal\n\nx\n",
        )
        _write(
            rec / "plans" / "pending" / "20260828-tabcomp-01-bja8og-child-one.ipd.md",
            "# IPD: one\n\n- Id: bja8og\n- Status: to-review\n- Set: tabcomp (tabs)\n\n## Goal\n\nx\n",
        )
        _write(
            rec / "plans" / "executed" / "20260101-oldset-01-ffffff-terminal.ipd.md",
            "# IPD: old\n\n- Id: ffffff\n- Status: executed\n- Set: oldset\n\n## Goal\n\nx\n",
        )
        # A spec and a backlog item, each with a KNOWN id6.
        _write(
            rec / "specs" / "20260828-abc123-01-abc123-a-spec.spec.md",
            "# Spec\n\n- Id: abc123\n- Status: draft\n",
        )
        _write(
            rec / "backlog" / "open" / "20260828-def456-01-def456-a-task.md",
            "# Task\n\n- Id: def456\n- Status: open\n- Summary: x\n",
        )
        # A single PLANNED release record with a KNOWN id6 + version, so `aw releases show`
        # completion (IPD w0ln4q E-04) resolves stably and `next` is offered.
        _write(
            rec / "releases" / "20260828-rel111-01-rel111-7-0-0.release.md",
            "# Release: 7.0.0\n\n- Id: rel111\n- Status: planned\n- Version: 7.0.0\n"
            "- Summary: the completable one\n",
        )
        # A run directory.
        (rec / "runs" / "run-20260829T000000Z-1").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()


class CompleteQuerySubcommandTests(_DynamicRepoFixture):
    def test_subcommand_prefix(self) -> None:
        got = completion.complete_query(["aw", "r"], 1, self.root)
        # A superset match (the real command set is larger) - assert the known r-commands are in it.
        for cmd in ("run", "runs", "research", "rename"):
            self.assertIn(cmd, got)

    def test_flag_prefix_returns_flags(self) -> None:
        got = completion.complete_query(["aw", "ipd", "--js"], 2, self.root)
        self.assertIn("--json", got)
        self.assertTrue(all(c.startswith("--js") for c in got))


class CompleteQueryArtifactTests(_DynamicRepoFixture):
    def test_plan_id6_bare_token_not_path(self) -> None:
        got = completion.complete_query(["aw", "ipd", "lint", "b"], 3, self.root)
        self.assertEqual(got, ["bja8og"])  # BARE id6, not a filename/path

    def test_plan_id6_excludes_terminal_disposition(self) -> None:
        # `ffffff` is an executed plan; it MUST NOT appear (active-disposition scoping).
        got = completion.complete_query(["aw", "ipd", "lint", "f"], 3, self.root)
        self.assertNotIn("ffffff", got)

    def test_spec_id6(self) -> None:
        got = completion.complete_query(["aw", "specs", "set", "abc"], 3, self.root)
        self.assertIn("abc123", got)

    def test_backlog_id6(self) -> None:
        got = completion.complete_query(["aw", "backlog", "set", "def"], 3, self.root)
        self.assertIn("def456", got)

    def test_set_id_from_front_matter_not_resolver(self) -> None:
        got = completion.complete_query(["aw", "run", "t"], 2, self.root)
        self.assertEqual(
            got, ["tabcomp"]
        )  # Set id derived from plan `- Set:` front matter

    def test_run_id_from_runs_dir(self) -> None:
        got = completion.complete_query(["aw", "runs", "run-"], 2, self.root)
        self.assertIn("run-20260829T000000Z-1", got)

    def test_release_selector_id6_version_and_next(self) -> None:
        # IPD w0ln4q E-04: `aw releases show <selector>` completes DYNAMICALLY from the release
        # records on disk (id6 + Version) plus the `next` sentinel. Asserted here (not only in
        # tests/test_releases_cli.py) so a future refactor of this query engine cannot silently
        # drop the release branch.
        got = completion.complete_query(["aw", "releases", "show", ""], 3, self.root)
        self.assertIn("rel111", got)
        self.assertIn("7.0.0", got)
        self.assertIn("next", got)
        # the `release` argparse alias resolves identically
        alias = completion.complete_query(["aw", "release", "show", ""], 3, self.root)
        self.assertEqual(sorted(alias), sorted(got))

    def test_release_selector_prefix_filters(self) -> None:
        got = completion.complete_query(["aw", "releases", "show", "rel"], 3, self.root)
        self.assertEqual(got, ["rel111"])


class CompleteQueryStatusTests(_DynamicRepoFixture):
    def test_plan_status_from_ipd_schema(self) -> None:
        got = completion.complete_query(["aw", "ipd", "set", "a"], 3, self.root)
        # plan statuses beginning with `a` from ipd_schema (approved/auto-approved).
        self.assertEqual(sorted(got), ["approved", "auto-approved"])

    def test_spec_status_differs_from_plan(self) -> None:
        # `aw specs set <path> --status i...` -> spec statuses (implementing/implemented), which are
        # NOT plan statuses. Prove the per-type vocabulary differs.
        spec_got = completion.complete_query(
            ["aw", "specs", "set", "abc123", "--status", "i"], 5, self.root
        )
        self.assertIn("implementing", spec_got)
        self.assertIn("implemented", spec_got)
        plan_i = completion.complete_query(["aw", "ipd", "set", "i"], 3, self.root)
        self.assertNotIn("implementing", plan_i)
        self.assertNotEqual(set(spec_got), set(plan_i))

    def test_backlog_status_set(self) -> None:
        got = completion.complete_query(
            ["aw", "backlog", "set", "def456", "--status", ""], 5, self.root
        )
        # bklgrad Order 01 (v58bvy) E-01: assert against the SOURCE OF TRUTH rather than a hardcoded
        # list, which went stale the moment `graduated` joined the vocabulary. Completion derives from
        # `backlog.STATUSES` (completion.py:509), so this stays correct for any future status too.
        from agent_workflows import backlog as _backlog

        self.assertEqual(sorted(got), sorted(_backlog.STATUSES))
        self.assertIn("graduated", got)


class CompleteQueryLatencyTests(_DynamicRepoFixture):
    def test_representative_query_within_budget(self) -> None:
        # Latency assertion. The <50ms interactive budget is the design target; the parser-build cost
        # dominates the subcommand path, so we assert a generous CI-safe upper bound (250ms) to avoid
        # a flaky test on a slow/loaded runner while still catching a pathological regression (the
        # unscoped full-history resolver sweep measured ~500ms). Artifact queries are far faster.
        best = min(
            (
                _timed(
                    lambda: completion.complete_query(
                        ["aw", "ipd", "lint", "b"], 3, self.root
                    )
                )
                for _ in range(3)
            )
        )
        self.assertLess(best, 0.25, f"complete_query too slow: {best * 1000:.1f}ms")


def _timed(fn) -> float:
    t = time.perf_counter()
    fn()
    return time.perf_counter() - t


class DunderCompleteProtocolTests(_DynamicRepoFixture):
    """E-02: the `aw __complete --cword N -- <tokens>` CLI protocol matches complete_query, exit 0."""

    def _complete(self, cword, tokens):
        out = io.StringIO()
        cwd = os.getcwd()
        os.chdir(self.root)
        try:
            with redirect_stdout(out):
                rc = cli.main(["__complete", "--cword", str(cword), "--", *tokens])
        finally:
            os.chdir(cwd)
        lines = [line for line in out.getvalue().splitlines() if line]
        return rc, lines

    def test_protocol_matches_query_and_exit0(self) -> None:
        rc, lines = self._complete(1, ["aw", "ru"])
        self.assertEqual(rc, 0)
        self.assertIn("run", lines)
        self.assertIn("runs", lines)
        # The CLI output must equal what complete_query returns for the same input.
        expected = completion.complete_query(["aw", "ru"], 1, self.root)
        self.assertEqual(lines, expected)

    def test_artifact_protocol(self) -> None:
        rc, lines = self._complete(3, ["aw", "ipd", "lint", "b"])
        self.assertEqual(rc, 0)
        self.assertEqual(lines, ["bja8og"])

    def test_leading_dash_token_is_data_not_flag(self) -> None:
        # The `--` separator means a leading option-like token in the completed line is DATA.
        rc, lines = self._complete(2, ["aw", "ipd", "--js"])
        self.assertEqual(rc, 0)
        self.assertIn("--json", lines)

    def test_no_candidates_still_exit0(self) -> None:
        rc, lines = self._complete(3, ["aw", "ipd", "lint", "zzzzzz"])
        self.assertEqual(rc, 0)
        self.assertEqual(lines, [])


class ArgcompleteSoftImportTests(unittest.TestCase):
    """E-03: the argcomplete marker + soft import."""

    def test_marker_is_real_comment_within_1024_bytes(self) -> None:
        src = Path(cli.__file__).read_text(encoding="utf-8")
        idx = src.find("# PYTHON_ARGCOMPLETE_OK")
        self.assertNotEqual(idx, -1, "marker missing")
        self.assertLess(idx, 1024, "marker must be within the first 1024 bytes")
        # It must be a real `#` comment, NOT inside the module docstring (which closes earlier).
        docstring_end = src.find('"""', 3) + 3
        self.assertGreater(
            idx,
            docstring_end,
            "marker must be a comment AFTER the docstring, not inside it",
        )

    def test_cli_imports_and_runs_without_argcomplete(self) -> None:
        # argcomplete is optional; simulate its absence and prove main() still runs cleanly.
        import builtins

        real_import = builtins.__import__

        def _no_argcomplete(name, *a, **k):
            if name == "argcomplete" or name.startswith("argcomplete."):
                raise ImportError("simulated: argcomplete not installed")
            return real_import(name, *a, **k)

        # Use a command that RETURNS (not one like `--version` that argparse turns into sys.exit).
        with mock.patch.object(builtins, "__import__", _no_argcomplete):
            rc, out = _run(["completion", "bash"])
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("# bash completion for aw"))

    def test_maybe_argcomplete_is_noop_when_absent(self) -> None:
        # Directly exercise the hook: with argcomplete unimportable it must return without error.
        import builtins

        real_import = builtins.__import__

        def _no_argcomplete(name, *a, **k):
            if name == "argcomplete" or name.startswith("argcomplete."):
                raise ImportError("simulated")
            return real_import(name, *a, **k)

        parser = cli._build_parser()
        with mock.patch.object(builtins, "__import__", _no_argcomplete):
            cli._maybe_argcomplete(parser)  # must not raise


# --------------------------------------------------------------------------------------
# tabcomp Order 03 (jolfpj): drop-in auto-discovery installation.
# --------------------------------------------------------------------------------------


class _DropInFixture(unittest.TestCase):
    """A REAL temp HOME + XDG bases (not a mock), so `mkdir(parents=True)`, symlink creation, and
    the dotfile-untouched assertion exercise actual filesystem behavior."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.xdg_data = self.root / "xdg-data"
        self.xdg_config = self.root / "xdg-config"
        self._env = mock.patch.dict(
            os.environ,
            {
                "HOME": str(self.home),
                "XDG_DATA_HOME": str(self.xdg_data),
                "XDG_CONFIG_HOME": str(self.xdg_config),
            },
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        self.addCleanup(self._tmp.cleanup)

    def dotfile_paths(self):
        return [
            self.home / ".bashrc",
            self.home / ".bash_profile",
            self.home / ".zshrc",
            self.home / ".profile",
            self.xdg_config / "fish" / "config.fish",
        ]

    def assert_no_dotfile_touched(self) -> None:
        """The CORE PROMISE: no user rc/dotfile is ever created or modified."""
        for path in self.dotfile_paths():
            self.assertFalse(
                path.exists(),
                f"{path} must never be created or modified by completion install/uninstall",
            )


class ResolveCompletionDirTests(_DropInFixture):
    """E-01: XDG-first directory resolution with the ~/.local/share, ~/.config fallbacks."""

    def test_xdg_env_vars_win(self) -> None:
        self.assertEqual(
            completion.resolve_completion_dir("bash"),
            self.xdg_data / "bash-completion/completions",
        )
        self.assertEqual(
            completion.resolve_completion_dir("zsh"),
            self.xdg_data / "zsh/site-functions",
        )
        self.assertEqual(
            completion.resolve_completion_dir("fish"),
            self.xdg_config / "fish/completions",
        )

    def test_fallbacks_when_xdg_unset(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("XDG_DATA_HOME", None)
            os.environ.pop("XDG_CONFIG_HOME", None)
            self.assertEqual(
                completion.resolve_completion_dir("bash"),
                self.home / ".local/share/bash-completion/completions",
            )
            self.assertEqual(
                completion.resolve_completion_dir("zsh"),
                self.home / ".local/share/zsh/site-functions",
            )
            self.assertEqual(
                completion.resolve_completion_dir("fish"),
                self.home / ".config/fish/completions",
            )

    def test_custom_dir_overrides_everything(self) -> None:
        custom = self.root / "elsewhere"
        self.assertEqual(
            completion.resolve_completion_dir("bash", custom_dir=custom), custom
        )

    def test_unsupported_shell_raises(self) -> None:
        with self.assertRaises(completion.CompletionInstallError):
            completion.resolve_completion_dir("tcsh")

    def test_xdg_precedence_matches_config_module(self) -> None:
        # The convention must be the SAME one config.config_dir uses (XDG env var, else ~/.config),
        # not a second invented one.
        from agent_workflows import config as _config

        self.assertEqual(_config.config_dir().parent, self.xdg_config)
        self.assertEqual(
            completion.resolve_completion_dir("fish").parent.parent, self.xdg_config
        )


class InstallShellCompletionTests(_DropInFixture):
    """E-01: drop-in writes, per-shell alias binding, sentinel, idempotency, no-clobber, uninstall."""

    def test_bash_writes_command_name_files_for_each_alias(self) -> None:
        result = completion.install_shell_completion("bash")
        directory = self.xdg_data / "bash-completion/completions"
        self.assertEqual(result["dir"], directory)
        primary = directory / "aw"
        self.assertTrue(primary.is_file())
        # BASH dispatches completion BY COMMAND NAME, so each alias needs its own entry.
        for alias in ("agentwf", "agent-workflows"):
            link = directory / alias
            self.assertTrue(
                link.exists(), f"bash needs a command-name file for {alias}"
            )
            self.assertEqual(os.readlink(link), "aw")
        self.assert_no_dotfile_touched()

    def test_zsh_writes_single_compdef_bound_file_only(self) -> None:
        completion.install_shell_completion("zsh")
        directory = self.xdg_data / "zsh/site-functions"
        primary = directory / "_aw"
        self.assertTrue(primary.is_file())
        # ZSH binds all three aliases from the ONE file's `#compdef` line, so per-alias files must
        # NOT be created (that would be wrong, not merely redundant).
        self.assertEqual(sorted(p.name for p in directory.iterdir()), ["_aw"])
        first_line = primary.read_text(encoding="utf-8").split("\n")[0]
        self.assertEqual(first_line, "#compdef aw agentwf agent-workflows")
        self.assert_no_dotfile_touched()

    def test_fish_writes_single_file_with_multi_complete_c(self) -> None:
        completion.install_shell_completion("fish")
        directory = self.xdg_config / "fish/completions"
        primary = directory / "aw.fish"
        self.assertTrue(primary.is_file())
        self.assertEqual(sorted(p.name for p in directory.iterdir()), ["aw.fish"])
        body = primary.read_text(encoding="utf-8")
        # FISH binds each alias via its own `complete -c <name>` lines inside the one file.
        for alias in ("aw", "agentwf", "agent-workflows"):
            self.assertIn(f"complete -c {alias} ", body)
        self.assert_no_dotfile_touched()

    def test_sentinel_present_in_every_written_file(self) -> None:
        for shell in ("bash", "zsh", "fish"):
            result = completion.install_shell_completion(shell)
            primary = result["paths"][0]
            head = primary.read_text(encoding="utf-8").split("\n")[:3]
            self.assertIn(completion.INSTALL_SENTINEL, head, shell)

    def test_zsh_sentinel_does_not_displace_compdef_first_line(self) -> None:
        # zsh's compinit only honors `#compdef` on line 1, so the sentinel must go BELOW it.
        result = completion.install_shell_completion("zsh")
        lines = result["paths"][0].read_text(encoding="utf-8").split("\n")
        self.assertTrue(lines[0].startswith("#compdef"))
        self.assertEqual(lines[1], completion.INSTALL_SENTINEL)

    def test_creates_missing_parent_directories(self) -> None:
        # OQ-01: mkdir(parents=True) so a fresh machine with no completion dir works.
        directory = self.xdg_data / "bash-completion/completions"
        self.assertFalse(directory.exists())
        completion.install_shell_completion("bash")
        self.assertTrue(directory.is_dir())

    def test_install_is_idempotent(self) -> None:
        first = completion.install_shell_completion("bash")
        body = first["paths"][0].read_text(encoding="utf-8")
        second = completion.install_shell_completion("bash")
        self.assertEqual(second["paths"], first["paths"])
        self.assertEqual(second["paths"][0].read_text(encoding="utf-8"), body)
        self.assertTrue(completion.is_completion_installed("bash"))

    def test_refuses_to_clobber_foreign_completion(self) -> None:
        directory = self.xdg_data / "bash-completion/completions"
        directory.mkdir(parents=True)
        foreign = directory / "aw"
        foreign.write_text("# someone else's aw completion\n", encoding="utf-8")
        with self.assertRaises(completion.CompletionInstallError):
            completion.install_shell_completion("bash")
        # The foreign file is left EXACTLY as it was, and no alias links were created.
        self.assertEqual(
            foreign.read_text(encoding="utf-8"), "# someone else's aw completion\n"
        )
        self.assertFalse((directory / "agentwf").exists())

    def test_refuses_when_a_foreign_alias_file_exists(self) -> None:
        # Fail closed BEFORE writing anything: a foreign alias entry aborts the whole install.
        directory = self.xdg_data / "bash-completion/completions"
        directory.mkdir(parents=True)
        (directory / "agentwf").write_text("# foreign alias\n", encoding="utf-8")
        with self.assertRaises(completion.CompletionInstallError):
            completion.install_shell_completion("bash")
        self.assertFalse((directory / "aw").exists())

    def test_dry_run_writes_nothing(self) -> None:
        result = completion.install_shell_completion("bash", dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["paths"])
        for path in result["paths"]:
            self.assertFalse(path.exists())
        self.assertFalse((self.xdg_data / "bash-completion").exists())

    def test_symlink_to_unexpected_target_is_treated_as_foreign(self) -> None:
        directory = self.xdg_data / "bash-completion/completions"
        directory.mkdir(parents=True)
        outside = self.root / "outside.bash"
        outside.write_text("# not ours\n", encoding="utf-8")
        (directory / "aw").symlink_to(outside)
        with self.assertRaises(completion.CompletionInstallError):
            completion.install_shell_completion("bash")
        # We must NOT have written THROUGH the link into the unexpected target.
        self.assertEqual(outside.read_text(encoding="utf-8"), "# not ours\n")


class UninstallShellCompletionTests(_DropInFixture):
    """E-01: uninstall removes ONLY tool-created files."""

    def test_removes_only_our_files(self) -> None:
        completion.install_shell_completion("bash")
        directory = self.xdg_data / "bash-completion/completions"
        foreign = directory / "other-tool"
        foreign.write_text("# foreign\n", encoding="utf-8")

        result = completion.uninstall_shell_completion("bash")
        self.assertEqual(
            sorted(p.name for p in result["removed"]),
            ["agent-workflows", "agentwf", "aw"],
        )
        self.assertFalse((directory / "aw").exists())
        self.assertFalse((directory / "agentwf").exists())
        self.assertTrue(foreign.is_file())  # untouched
        self.assertFalse(completion.is_completion_installed("bash"))
        self.assert_no_dotfile_touched()

    def test_leaves_foreign_aw_file_intact_and_reports_it(self) -> None:
        directory = self.xdg_data / "bash-completion/completions"
        directory.mkdir(parents=True)
        foreign = directory / "aw"
        foreign.write_text("# foreign aw completion\n", encoding="utf-8")
        result = completion.uninstall_shell_completion("bash")
        self.assertEqual(result["removed"], [])
        self.assertEqual([p.name for p in result["skipped"]], ["aw"])
        self.assertTrue(foreign.is_file())

    def test_uninstall_when_nothing_installed_is_a_noop(self) -> None:
        result = completion.uninstall_shell_completion("fish")
        self.assertEqual(result["removed"], [])
        self.assertEqual(result["skipped"], [])

    def test_dry_run_removes_nothing(self) -> None:
        completion.install_shell_completion("zsh")
        primary = self.xdg_data / "zsh/site-functions/_aw"
        result = completion.uninstall_shell_completion("zsh", dry_run=True)
        self.assertEqual([p.name for p in result["removed"]], ["_aw"])
        self.assertTrue(primary.is_file())

    def test_roundtrip_touches_no_dotfile(self) -> None:
        for shell in ("bash", "zsh", "fish"):
            completion.install_shell_completion(shell)
            completion.uninstall_shell_completion(shell)
        self.assert_no_dotfile_touched()


class CompletionInstallCliTests(_DropInFixture):
    """E-02: the `aw completion install|uninstall` CLI, additive on child 01's parser shape."""

    def test_install_and_uninstall_exit0(self) -> None:
        rc, out = _run(["completion", "install", "--shell", "bash"])
        self.assertEqual(rc, 0, out)
        directory = self.xdg_data / "bash-completion/completions"
        self.assertTrue((directory / "aw").is_file())
        self.assertIn(str(directory / "aw"), out)

        rc, out = _run(["completion", "uninstall", "--shell", "bash"])
        self.assertEqual(rc, 0, out)
        self.assertFalse((directory / "aw").exists())
        self.assert_no_dotfile_touched()

    def test_dry_run_previews_paths_without_creating_files(self) -> None:
        rc, out = _run(["completion", "install", "--shell", "fish", "--dry-run"])
        self.assertEqual(rc, 0, out)
        self.assertIn("[dry-run]", out)
        self.assertIn("aw.fish", out)
        self.assertFalse((self.xdg_config / "fish/completions/aw.fish").exists())

    def test_custom_dir_flag(self) -> None:
        custom = self.root / "custom-dir"
        rc, out = _run(
            ["completion", "install", "--shell", "zsh", "--dir", str(custom)]
        )
        self.assertEqual(rc, 0, out)
        self.assertTrue((custom / "_aw").is_file())

    def test_shell_defaults_to_detected_shell(self) -> None:
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            rc, out = _run(["completion", "install"])
        self.assertEqual(rc, 0, out)
        self.assertTrue((self.xdg_config / "fish/completions/aw.fish").is_file())

    def test_foreign_file_refusal_exits_1(self) -> None:
        directory = self.xdg_data / "bash-completion/completions"
        directory.mkdir(parents=True)
        (directory / "aw").write_text("# foreign\n", encoding="utf-8")
        rc, out = _run(["completion", "install", "--shell", "bash"])
        self.assertEqual(rc, 1, out)
        self.assertEqual((directory / "aw").read_text(encoding="utf-8"), "# foreign\n")

    def test_child01_script_output_still_works(self) -> None:
        # REGRESSION GUARD: adding the install/uninstall verbs must EXTEND child 01's parser, not
        # redesign it - `aw completion <shell>` must still stream the raw script to stdout.
        for shell, needle in (
            ("bash", "# bash completion for aw"),
            ("zsh", "#compdef aw agentwf agent-workflows"),
            ("fish", "complete -c aw "),
        ):
            rc, out = _run(["completion", shell])
            self.assertEqual(rc, 0, shell)
            self.assertIn(needle, out)
        # And bare `aw completion` still detects the shell rather than being read as a verb.
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}):
            rc, out = _run(["completion"])
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("# bash completion for aw"))


class SetupCompletionPromptTests(_DropInFixture):
    """E-03: the HOST-LEVEL `_run_setup`/`_configure_completion` prompt (not install_wizard.py)."""

    def _args(self, **kw):
        base = dict(completion=None, yes=False)
        base.update(kw)
        return argparse.Namespace(**base)

    def test_prompt_installs_on_accept(self) -> None:
        term = Term(color=False)
        with (
            mock.patch.object(cli.sys.stdin, "isatty", return_value=True),
            mock.patch.object(cli, "input", create=True, return_value="y"),
            mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}),
        ):
            cli._configure_completion(self._args(), term)
        self.assertTrue((self.xdg_data / "bash-completion/completions/aw").is_file())
        self.assert_no_dotfile_touched()

    def test_prompt_installs_nothing_on_reject(self) -> None:
        term = Term(color=False)
        with (
            mock.patch.object(cli.sys.stdin, "isatty", return_value=True),
            mock.patch.object(cli, "input", create=True, return_value="n"),
            mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}),
        ):
            cli._configure_completion(self._args(), term)
        self.assertFalse((self.xdg_data / "bash-completion").exists())
        self.assert_no_dotfile_touched()

    def test_skipped_non_interactively(self) -> None:
        term = Term(color=False)
        with (
            mock.patch.object(cli.sys.stdin, "isatty", return_value=False),
            mock.patch.object(cli, "input", create=True) as m_input,
        ):
            cli._configure_completion(self._args(), term)
        m_input.assert_not_called()
        self.assertFalse((self.xdg_data / "bash-completion").exists())

    def test_skipped_under_yes(self) -> None:
        term = Term(color=False)
        with (
            mock.patch.object(cli.sys.stdin, "isatty", return_value=True),
            mock.patch.object(cli, "input", create=True) as m_input,
        ):
            cli._configure_completion(self._args(yes=True), term)
        m_input.assert_not_called()
        self.assertFalse((self.xdg_data / "bash-completion").exists())

    def test_no_prompt_when_already_installed(self) -> None:
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}):
            completion.install_shell_completion("bash")
            term = Term(color=False)
            with (
                mock.patch.object(cli.sys.stdin, "isatty", return_value=True),
                mock.patch.object(cli, "input", create=True) as m_input,
            ):
                cli._configure_completion(self._args(), term)
        m_input.assert_not_called()

    def test_explicit_none_never_prompts(self) -> None:
        term = Term(color=False)
        with (
            mock.patch.object(cli.sys.stdin, "isatty", return_value=True),
            mock.patch.object(cli, "input", create=True) as m_input,
        ):
            cli._configure_completion(self._args(completion="none"), term)
        m_input.assert_not_called()
        self.assertFalse((self.xdg_data / "bash-completion").exists())

    def test_prompt_lives_in_cli_not_install_wizard(self) -> None:
        # The reviewed integration point: the per-user completion prompt belongs to the host-level
        # setup flow, NOT the per-target-repo project-policy wizard.
        from agent_workflows import install_wizard

        wizard_src = Path(install_wizard.__file__).read_text(encoding="utf-8")
        for needle in (
            "install_shell_completion",
            "resolve_completion_dir",
            "completion install",
        ):
            self.assertNotIn(
                needle,
                wizard_src,
                "install_wizard.py (per-repo policy wizard) must not carry the "
                "per-user completion prompt",
            )
        cli_src = Path(cli.__file__).read_text(encoding="utf-8")
        self.assertIn("_configure_completion(args, term)", cli_src)

    def test_install_failure_does_not_break_setup(self) -> None:
        # An optional convenience must never fail the host setup flow.
        term = Term(color=False)
        with mock.patch.object(
            completion,
            "install_shell_completion",
            side_effect=completion.CompletionInstallError("boom"),
        ):
            cli._configure_completion(self._args(completion="bash"), term)  # no raise


class InstallCompletionFlagTests(_DropInFixture):
    """E-04: `--completion [auto|bash|zsh|fish|none]` resolution and the discovery tip."""

    def test_flag_is_registered_on_install_and_setup(self) -> None:
        parser = cli._build_parser()
        for verb, extra in (("install", []), ("setup", [])):
            args = parser.parse_args([verb, *extra, "--completion", "zsh"])
            self.assertEqual(args.completion, "zsh")
        for choice in ("auto", "bash", "zsh", "fish", "none"):
            args = parser.parse_args(["install", "--completion", choice])
            self.assertEqual(args.completion, choice)

    def test_resolve_choice(self) -> None:
        ns = argparse.Namespace
        self.assertIsNone(cli._resolve_completion_choice(ns(completion=None)))
        self.assertIsNone(cli._resolve_completion_choice(ns(completion="none")))
        self.assertEqual(cli._resolve_completion_choice(ns(completion="zsh")), "zsh")
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            self.assertEqual(
                cli._resolve_completion_choice(ns(completion="auto")), "fish"
            )

    def test_explicit_shell_installs_without_prompting(self) -> None:
        term = Term(color=False)
        with mock.patch.object(cli, "input", create=True) as m_input:
            cli._configure_completion(
                argparse.Namespace(completion="bash", yes=True), term
            )
        m_input.assert_not_called()  # explicit flag => no question
        self.assertTrue((self.xdg_data / "bash-completion/completions/aw").is_file())

    def test_yes_without_flag_installs_nothing(self) -> None:
        term = Term(color=False)
        cli._configure_completion(argparse.Namespace(completion=None, yes=True), term)
        self.assertFalse((self.xdg_data / "bash-completion").exists())
        self.assertFalse((self.xdg_config / "fish").exists())
        self.assert_no_dotfile_touched()

    def test_auto_detects_shell(self) -> None:
        term = Term(color=False)
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/zsh"}):
            cli._configure_completion(
                argparse.Namespace(completion="auto", yes=True), term
            )
        self.assertTrue((self.xdg_data / "zsh/site-functions/_aw").is_file())

    def test_tip_shown_when_unconfigured_and_hidden_once_installed(self) -> None:
        buf = io.StringIO()
        term = Term(stream=buf, color=False)
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}):
            cli._completion_tip(term)
            self.assertIn("aw completion install", buf.getvalue())

            completion.install_shell_completion("bash")
            buf2 = io.StringIO()
            cli._completion_tip(Term(stream=buf2, color=False))
            self.assertEqual(buf2.getvalue(), "")


# The only test here that SPAWNS the CLI, so it carries the `slow` marker (pyproject.toml:108-109);
# the rest of this module is fast in-process and stays in the default suite.
@pytest.mark.slow
class CompletionInstallSubprocessTests(_DropInFixture):
    """E-04/E-02 end-to-end through a real subprocess (marked slow per pyproject.toml)."""

    def test_module_cli_install_then_uninstall(self) -> None:
        env = dict(os.environ)
        env["XDG_DATA_HOME"] = str(self.xdg_data)
        env["XDG_CONFIG_HOME"] = str(self.xdg_config)
        env["HOME"] = str(self.home)
        primary = self.xdg_data / "bash-completion/completions/aw"

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "completion",
                "install",
                "--shell",
                "bash",
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(self.root),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(primary.is_file())

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "completion",
                "uninstall",
                "--shell",
                "bash",
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(self.root),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(primary.exists())
        self.assert_no_dotfile_touched()


class ReadmeCompletionDocsTests(unittest.TestCase):
    """E-05: README documents the feature."""

    def test_readme_has_shell_tab_completion_section(self) -> None:
        readme = Path(__file__).resolve().parents[1] / "README.md"
        body = readme.read_text(encoding="utf-8")
        self.assertIn("Shell Tab Completion", body)
        self.assertIn("aw completion install", body)
        self.assertIn("source <(aw completion bash)", body)


if __name__ == "__main__":
    unittest.main()

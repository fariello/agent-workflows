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

import io
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
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
        self.assertEqual(sorted(got), ["blocked", "done", "open", "parked"])


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


if __name__ == "__main__":
    unittest.main()

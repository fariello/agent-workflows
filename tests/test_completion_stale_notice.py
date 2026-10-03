"""Tests for stale tab-completion detection, notification, and status command (s2yf26).

Covers:
- E-01: Per-user notice throttle stamp (notice_stamp_path, read_notice_stamp, write_notice_stamp).
- E-02: Version key derivation (notice_version_key).
- E-03: Process-wide output mode and command publication in cli.py and restoration in finally.
- E-04: Central hook (_maybe_notify_stale_completion), six sequential gates, stderr notice, shared constant.
- E-05: Read-only `aw completion status` diagnostic verb.
- E-06: README documentation and docstring updates.
"""

from __future__ import annotations

import inspect
import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


from agent_workflows import cli, completion, term as _term_mod
from agent_workflows.result_types import OutputMode
from agent_workflows.term import Term
from tests.test_completion import _DropInFixture


class _NoticeBaseFixture(_DropInFixture):
    """Drop-in fixture that snapshots and restores process-wide presentation state."""

    def setUp(self) -> None:
        super().setUp()
        self._orig_interactive = _term_mod.get_interactive_override()
        self._orig_color = _term_mod.get_color_override()
        self._orig_mode = cli.get_last_output_mode()
        self._orig_cmd = cli.get_last_command()
        self.addCleanup(_term_mod.set_interactive_override, self._orig_interactive)
        self.addCleanup(_term_mod.set_color_override, self._orig_color)
        self.addCleanup(cli.set_last_output_mode, self._orig_mode)
        self.addCleanup(cli.set_last_command, self._orig_cmd)


class NoticeStampTests(_NoticeBaseFixture):
    """E-01: Notice stamp path, atomic writing, and fail-soft reading."""

    def test_stamp_path_resolution(self) -> None:
        path = completion.notice_stamp_path()
        self.assertEqual(path.name, "completion-notice.json")
        self.assertEqual(
            path, self.xdg_config / "agent-workflows" / "completion-notice.json"
        )
        self.assertEqual(path.parent, self.xdg_config / "agent-workflows")

    def test_stamp_round_trip(self) -> None:
        written = completion.write_notice_stamp("1.3.0rc2")
        self.assertTrue(written)
        stamp = completion.read_notice_stamp()
        self.assertEqual(stamp, {"schema": 1, "last_notified_version": "1.3.0rc2"})

    def test_stamp_read_invalid_and_corrupt_cases(self) -> None:
        path = completion.notice_stamp_path()
        cases = [
            ("absent file", None, None),
            ("truncated json", "{", None),
            ("non-json text", "not valid json at all", None),
            (
                "wrong schema version",
                json.dumps({"schema": 2, "last_notified_version": "1.0.0"}),
                None,
            ),
            (
                "non-string version",
                json.dumps({"schema": 1, "last_notified_version": 12345}),
                None,
            ),
            ("non-dict payload", json.dumps(["schema", 1]), None),
        ]
        failures = []
        for desc, content, expected in cases:
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            res = completion.read_notice_stamp()
            if res != expected:
                failures.append(f"{desc}: expected {expected!r}, got {res!r}")
        self.assertEqual(failures, [])

    def test_stamp_write_readonly_parent(self) -> None:
        path = completion.notice_stamp_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        orig_mode = path.parent.stat().st_mode
        try:
            os.chmod(path.parent, 0o500)
            res = completion.write_notice_stamp("1.3.0")
            self.assertFalse(
                res, "write_notice_stamp into read-only directory must return False"
            )
        finally:
            os.chmod(path.parent, orig_mode)


class NoticeVersionKeyTests(_NoticeBaseFixture):
    """E-02: notice_version_key release-plus-rc derivation."""

    def test_version_key_derivation_vectors(self) -> None:
        vectors = [
            ("1.3.0rc2.dev5565+g6402f145", "1.3.0rc2", "checkout dev build with rc"),
            ("1.2.0", "1.2.0", "exact release"),
            ("1.2.1.dev2+gabc1234", "1.2.1", "dev build without rc"),
            ("unknown", "unknown", "unknown fallback"),
        ]
        failures = []
        for raw, expected, why in vectors:
            key = completion.notice_version_key(raw)
            if key != expected:
                failures.append(f"{why} ({raw}): expected {expected}, got {key}")
            if "+" in key or "g" in key and key != "unknown":
                failures.append(
                    f"{why} ({raw}): key {key!r} contains leak-prone characters"
                )
        self.assertEqual(failures, [])

    def test_default_version_key(self) -> None:
        key = completion.notice_version_key()
        self.assertIsInstance(key, str)
        self.assertTrue(len(key) > 0)
        self.assertNotIn("+", key)


class PublicationTests(_NoticeBaseFixture):
    """E-03: Process-wide output mode and command publication and restoration."""

    def test_publication_and_restoration_normal(self) -> None:
        cli.set_last_output_mode(None)
        cli.set_last_command(None)
        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(["layout"])
        self.assertEqual(rc, 0)
        # Inherited values must be restored in finally
        self.assertIsNone(cli.get_last_output_mode())
        self.assertIsNone(cli.get_last_command())

    def test_publication_and_restoration_system_exit(self) -> None:
        cli.set_last_output_mode(None)
        cli.set_last_command(None)
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(SystemExit):
                cli.main(["--no-color", "check", "--help"])
        self.assertIsNone(cli.get_last_output_mode())
        self.assertIsNone(cli.get_last_command())

    def test_publication_command_with_preceding_flag(self) -> None:
        observed_cmd = []
        observed_mode = []

        orig_maybe = cli._maybe_notify_stale_completion

        def spy_maybe(rc: int) -> None:
            observed_cmd.append(cli.get_last_command())
            observed_mode.append(cli.get_last_output_mode())
            orig_maybe(rc)

        with mock.patch(
            "agent_workflows.cli._maybe_notify_stale_completion", side_effect=spy_maybe
        ):
            out = io.StringIO()
            with redirect_stdout(out):
                cli.main(["--no-color", "completion", "bash"])

        self.assertEqual(observed_cmd, ["completion"])
        self.assertEqual(observed_mode, [OutputMode.HUMAN])


class StaleCompletionNoticeHookTests(_NoticeBaseFixture):
    """E-04: Central hook, six suppression gates, stderr emit, and shared constant."""

    def _make_stale(self) -> Path:
        completion.install_shell_completion("bash")
        primary = self.xdg_data / "bash-completion/completions/aw"
        body = primary.read_text(encoding="utf-8")
        primary.write_text(
            body.replace(
                "_aw_completion() {",
                "_aw_completion() {\n    # stale injected command",
            ),
            encoding="utf-8",
        )
        return primary

    def test_positive_notice_once_on_stderr_stdout_clean(self) -> None:
        self._make_stale()

        out1 = io.StringIO()
        err1 = io.StringIO()
        with redirect_stdout(out1), redirect_stderr(err1):
            rc1 = cli.main(["--interactive", "layout"])

        self.assertEqual(rc1, 0)
        self.assertIn(cli.STALE_COMPLETION_NOTICE, err1.getvalue())
        self.assertNotIn(cli.STALE_COMPLETION_NOTICE, out1.getvalue())

        # Second invocation: stamp matches, must be silent on stderr
        out2 = io.StringIO()
        err2 = io.StringIO()
        with redirect_stdout(out2), redirect_stderr(err2):
            rc2 = cli.main(["--interactive", "layout"])

        self.assertEqual(rc2, 0)
        self.assertEqual(
            err2.getvalue(), "", "second invocation must be completely silent on stderr"
        )
        self.assertEqual(
            out1.getvalue(), out2.getvalue(), "stdout must be byte-identical"
        )

    def test_suppression_table_and_zero_probes(self) -> None:
        """Assert silence AND zero probes across all suppression gates."""
        self._make_stale()
        stamp_path = completion.notice_stamp_path()

        probe_calls = []
        orig_probe = completion.installed_completion_state

        def counting_probe(*args, **kwargs):
            probe_calls.append(args)
            return orig_probe(*args, **kwargs)

        # Each row: (name, argv, call_with_none_argv, why)
        rows = [
            (
                "gate d: --agent (flag after command)",
                ["--interactive", "layout", "--agent"],
                False,
                "agent mode must suppress",
            ),
            (
                "gate d: --json (flag after command)",
                ["--interactive", "layout", "--json"],
                False,
                "json mode must suppress",
            ),
            (
                "gate e: non-interactive",
                ["--no-interactive", "layout"],
                False,
                "non-interactive must suppress",
            ),
            (
                "gate b: __complete callback",
                ["--interactive", "__complete", "--", "aw", "layout"],
                False,
                "__complete must stay silent and fast",
            ),
            (
                "gate c: completion install",
                ["--interactive", "completion", "install"],
                False,
                "completion install must suppress",
            ),
            (
                "gate c: completion bash",
                ["--interactive", "completion", "bash"],
                False,
                "raw completion script stream must suppress",
            ),
            (
                "F-13: preceding flag on completion bash",
                ["--interactive", "--no-color", "completion", "bash"],
                False,
                "global flag before completion must suppress",
            ),
            (
                "F-13: console script shape argv=None on completion",
                ["aw", "--interactive", "completion", "bash"],
                True,
                "console script entry argv=None must suppress via published command",
            ),
            (
                "F-13: console script shape argv=None on __complete",
                ["aw", "--interactive", "__complete", "--", "aw", "layout"],
                True,
                "console script entry argv=None must suppress via published command",
            ),
        ]

        failures = []
        for name, argv, use_argv_none, why in rows:
            if stamp_path.exists():
                stamp_path.unlink()
            probe_calls.clear()

            out = io.StringIO()
            err = io.StringIO()
            with mock.patch(
                "agent_workflows.completion.installed_completion_state",
                side_effect=counting_probe,
            ):
                with redirect_stdout(out), redirect_stderr(err):
                    if use_argv_none:
                        with mock.patch("sys.argv", list(argv)):
                            cli.main(None)
                    else:
                        cli.main(argv)

            if cli.STALE_COMPLETION_NOTICE in err.getvalue():
                failures.append(
                    f"{name}: notice printed on stderr but should have been suppressed ({why})"
                )
            if len(probe_calls) != 0:
                failures.append(
                    f"{name}: probe ran {len(probe_calls)} times, expected 0 ({why})"
                )

        self.assertEqual(failures, [])

    def test_suppression_for_none_command_none_mode_and_nonzero_rc(self) -> None:
        """Direct unit assertions on _maybe_notify_stale_completion for None cmd, None mode, nonzero rc."""
        self._make_stale()
        stamp_path = completion.notice_stamp_path()
        probe_calls = []

        def counting_probe(*args, **kwargs):
            probe_calls.append(args)
            return "stale"

        cases = [
            (
                "nonzero rc",
                1,
                OutputMode.HUMAN,
                "layout",
                "nonzero exit code must suppress",
            ),
            ("none command", 0, OutputMode.HUMAN, None, "None command must suppress"),
            ("none mode", 0, None, "layout", "None mode must suppress"),
            ("agent mode", 0, OutputMode.AGENT, "layout", "AGENT mode must suppress"),
            ("json mode", 0, OutputMode.JSON, "layout", "JSON mode must suppress"),
            (
                "__complete command",
                0,
                OutputMode.HUMAN,
                "__complete",
                "__complete command must suppress",
            ),
            (
                "completion command",
                0,
                OutputMode.HUMAN,
                "completion",
                "completion command must suppress",
            ),
        ]
        failures = []
        for name, rc, mode, cmd, why in cases:
            if stamp_path.exists():
                stamp_path.unlink()
            probe_calls.clear()
            _term_mod.set_interactive_override(True)
            cli.set_last_output_mode(mode)
            cli.set_last_command(cmd)

            err = io.StringIO()
            with mock.patch(
                "agent_workflows.completion.installed_completion_state",
                side_effect=counting_probe,
            ):
                with redirect_stderr(err):
                    cli._maybe_notify_stale_completion(rc)

            if cli.STALE_COMPLETION_NOTICE in err.getvalue():
                failures.append(f"{name}: notice printed on stderr ({why})")
            if len(probe_calls) != 0:
                failures.append(f"{name}: probe ran {len(probe_calls)} times ({why})")

        _term_mod.set_interactive_override(self._orig_interactive)
        cli.set_last_output_mode(self._orig_mode)
        cli.set_last_command(self._orig_cmd)

        self.assertEqual(failures, [])

    def test_both_surfaces_render_one_wording(self) -> None:
        self._make_stale()

        # Hook stderr output
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            cli.main(["--interactive", "layout"])
        self.assertIn(cli.STALE_COMPLETION_NOTICE, err.getvalue())

        # cli._completion_tip output
        tip_buf = io.StringIO()
        cli._completion_tip(Term(stream=tip_buf, color=False))
        self.assertIn(cli.STALE_COMPLETION_NOTICE, tip_buf.getvalue())

    def test_hook_signature_takes_rc_only(self) -> None:
        sig = inspect.signature(cli._maybe_notify_stale_completion)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ["rc"], f"expected signature (rc), got {params}")


class CompletionStatusVerbTests(_NoticeBaseFixture):
    """E-05: aw completion status read-only report."""

    def _make_stale(self) -> Path:
        completion.install_shell_completion("bash")
        primary = self.xdg_data / "bash-completion/completions/aw"
        body = primary.read_text(encoding="utf-8")
        primary.write_text(
            body.replace(
                "_aw_completion() {",
                "_aw_completion() {\n    # stale injected command",
            ),
            encoding="utf-8",
        )
        return primary

    def test_status_absent(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(["completion", "status"])
        self.assertEqual(rc, 0)
        output = out.getvalue()
        self.assertIn("Shell: bash", output)
        self.assertIn("Verdict: absent", output)
        self.assertFalse(output.startswith("# bash completion for aw"))

    def test_status_stale_then_current_and_writes_nothing(self) -> None:
        primary = self._make_stale()
        stamp_path = completion.notice_stamp_path()
        self.assertFalse(stamp_path.exists())

        bytes_before = primary.read_bytes()
        stat_before = (primary.stat().st_mtime_ns, primary.stat().st_size)

        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(["completion", "status"])

        self.assertEqual(rc, 0)
        self.assertIn("Verdict: stale", out.getvalue())

        # Verify nothing written
        self.assertEqual(primary.read_bytes(), bytes_before)
        stat_after = (primary.stat().st_mtime_ns, primary.stat().st_size)
        self.assertEqual(stat_before, stat_after)
        self.assertFalse(
            stamp_path.exists(), "completion status must NOT write notice stamp"
        )

        # Now refresh with install
        with redirect_stdout(io.StringIO()):
            rc_install = cli.main(["completion", "install"])
        self.assertEqual(rc_install, 0)

        out2 = io.StringIO()
        with redirect_stdout(out2):
            rc2 = cli.main(["completion", "status"])

        self.assertEqual(rc2, 0)
        self.assertIn("Verdict: current", out2.getvalue())
        self.assertFalse(
            stamp_path.exists(),
            "completion status must NOT write notice stamp even when current",
        )


class DocumentationAndDocstringTests(unittest.TestCase):
    """E-06: Documentation and docstring correctness."""

    def test_readme_tab_completion_section(self) -> None:
        readme = Path("README.md").read_text(encoding="utf-8")
        self.assertIn("aw completion status", readme)
        self.assertIn("aw completion install", readme)
        self.assertIn("stale", readme)
        self.assertIn("stderr", readme)
        self.assertIn("completion-notice.json", readme)
        self.assertIn("never rewrites", readme)

        # Check for em and en dashes in the tab completion section
        section_start = readme.find("### Shell Tab Completion")
        self.assertGreater(section_start, 0)
        section_end = readme.find("### The `.aw/` Physical Layout and Four Roots")
        self.assertGreater(section_end, section_start)
        section = readme[section_start:section_end]

        self.assertNotIn(
            "\u2014", section, "README tab completion section must contain no em dash"
        )
        self.assertNotIn(
            "\u2013", section, "README tab completion section must contain no en dash"
        )

    def test_test_completion_docstring_updated(self) -> None:
        from tests import test_completion

        doc = test_completion.StaleCompletionWarningTests.__doc__ or ""
        self.assertNotIn("_completion_configured", doc)

"""Tests for Empty, Loading, and Error State UX helper and conventions.

IPD: 20260822-highpbacklog0822-04-89bby9 (Order 04 E-01, E-02, E-03, V-01, V-02, V-03).
IPD: 20260822-highpbacklog0822-05-4ug8xp (Order 05 E-01, E-02, E-03, V-01, V-02, V-03).

Asserts:
1. Term.format_empty_result / Term.empty_result echoes active filters and next action,
   composed from existing primitives (outcome, section, next_action) with zero parallel palette.
2. Step cue formatting for transient stderr progress updates.
3. Surface-wide read/list verbs ('aw find', 'aw search', 'aw list-repos', 'aw ipd board', etc.)
   render empty states with filters and next-action in both Human TTY and Agent (aw.agent/v1) modes.
4. Mutation verbs report applied feedback / dry-run previews and never fail silently on errors.
5. Characterization fact-parity: agent-mode facts and exit codes are verified against schema.
"""

from __future__ import annotations

import io
import json
import os
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli
from agent_workflows import agent_schema as schema
from agent_workflows import term as T
from agent_workflows.result_types import (
    CommandResult,
    NextAction,
)

_ANSI = re.compile(r"\033\[[0-9;]*m")


class EmptyStateHelperUnitTests(unittest.TestCase):
    """V-01: Term.empty_result and Term.format_empty_result component tests."""

    def test_format_empty_result_color_unicode(self):
        term = T.Term(color=True, unicode=True)
        rendered = term.format_empty_result(
            summary="no matching plans",
            filters={"type": "plans", "selector": "89bby9"},
            next_action=NextAction("aw find plans", "find across all plans"),
        )
        plain = _ANSI.sub("", rendered)
        self.assertIn("✓ CLEAN  no matching plans", plain)
        self.assertIn("Active filters:", plain)
        self.assertIn("type: plans", plain)
        self.assertIn("selector: 89bby9", plain)
        self.assertIn("Next  aw find plans (find across all plans)", plain)
        # Verify ANSI color sequences are present
        self.assertIn("\033[", rendered)

    def test_format_empty_result_monochrome_ascii(self):
        term = T.Term(color=False, unicode=False)
        rendered = term.format_empty_result(
            summary="no matching artifacts",
            filters={"type": "all"},
            next_action="aw status",
        )
        self.assertIsNone(_ANSI.search(rendered))
        self.assertIn("OK CLEAN  no matching artifacts", rendered)
        self.assertIn("Active filters:", rendered)
        self.assertIn("type: all", rendered)
        self.assertIn("Next  aw status", rendered)
        # Must be strict 7-bit ASCII
        rendered.encode("ascii")

    def test_format_empty_result_from_dict_and_result_context(self):
        term = T.Term(color=False, unicode=False)
        # From dictionary context
        dict_ctx = {
            "summary": "no matching specs",
            "filters": [("type", "specs"), ("tag", "core")],
            "next_action": ("aw find specs", "list all specs"),
        }
        res1 = term.format_empty_result(dict_ctx)
        self.assertIn("OK CLEAN  no matching specs", res1)
        self.assertIn("type: specs", res1)
        self.assertIn("tag: core", res1)
        self.assertIn("Next  aw find specs (list all specs)", res1)

        # From CommandResult context
        cmd_res = CommandResult(
            command="find",
            status="clean",
            exit_code=0,
            summary="no matching research",
            next_actions=[NextAction("aw find", "list all")],
            data={"filters": {"type": "research"}},
        )
        res2 = term.format_empty_result(cmd_res)
        self.assertIn("OK CLEAN  no matching research", res2)
        self.assertIn("type: research", res2)
        self.assertIn("Next  aw find (list all)", res2)

    def test_format_empty_result_no_filters_or_next(self):
        term = T.Term(color=False, unicode=False)
        res = term.format_empty_result(summary="no results")
        self.assertEqual(res.strip(), "OK CLEAN  no results")

    def test_empty_result_stream_emission(self):
        buf = io.StringIO()
        term = T.Term(stream=buf, color=False, unicode=False)
        term.empty_result(
            summary="no matching items",
            filters={"query": "foo"},
            next_action="aw search",
        )
        out = buf.getvalue()
        self.assertIn("OK CLEAN  no matching items", out)
        self.assertIn("query: foo", out)
        self.assertIn("Next  aw search", out)

    def test_step_cue_helper(self):
        term = T.Term(color=False, unicode=False)
        cue = term.format_step_cue("Scanning workspace...")
        self.assertEqual(cue, "[INFO ] Scanning workspace...")

        err_buf = io.StringIO()
        term.step_cue("Running check...", stream=err_buf)
        self.assertEqual(err_buf.getvalue().strip(), "[INFO ] Running check...")


class FindReferenceVerbEmptyStateTests(unittest.TestCase):
    """V-03 (Order 04): Reference read verb ('aw find') empty-state UX across TTY and Agent modes."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # Create minimal .aw layout with one spec
        specs = self.root / ".aw" / "records" / "specs"
        specs.mkdir(parents=True)
        content = (
            "\n".join(
                [
                    "# Spec",
                    "",
                    "- Id: abc123",
                    "- Status: draft",
                    "",
                    "## Content",
                    "hello world",
                ]
            )
            + "\n"
        )
        (specs / "20260822-1200-01-sample.spec.md").write_text(
            content,
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.root)])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def test_find_empty_human_tty_mode_with_type_and_selector(self):
        # Searching for nonexistent selector in specs
        rc, out, err = self._run_cli(["find", "specs", "nonexistent999"])
        self.assertEqual(rc, 0)
        self.assertIn("CLEAN", out)
        self.assertIn("no matching specs", out)
        self.assertIn("Active filters:", out)
        self.assertIn("type: specs", out)
        self.assertIn("selector: nonexistent999", out)
        self.assertIn("Next  aw find specs", out)

    def test_find_empty_human_tty_mode_all_types(self):
        # Searching across all types for nonexistent selector
        rc, out, err = self._run_cli(["find", "nonexistent999"])
        self.assertEqual(rc, 0)
        self.assertIn("CLEAN", out)
        self.assertIn("no matching artifacts", out)
        self.assertIn("Active filters:", out)
        self.assertIn("type: all", out)
        self.assertIn("selector: nonexistent999", out)
        self.assertIn("Next  aw find", out)

    def test_find_empty_agent_mode(self):
        rc, out, err = self._run_cli(["find", "specs", "nonexistent999", "--agent"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "find")
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["findings"], 0)
        self.assertTrue(rec["verified"])
        self.assertTrue(rec["complete"])
        self.assertEqual(rec["next"], "aw find specs")
        self.assertIsNone(_ANSI.search(lines[0]))
        val_errors = schema.validate_agent_record(rec)
        self.assertEqual(val_errors, [])

    def test_find_match_found_human_mode(self):
        # Non-empty match still outputs normal lines
        rc, out, err = self._run_cli(["find", "specs", "abc123"])
        self.assertEqual(rc, 0)
        self.assertIn("abc123", out)
        self.assertIn("draft", out)
        self.assertNotIn("no matching", out)


class ReadListVerbsEmptyStateSurfaceTests(unittest.TestCase):
    """V-01: Surface-wide read/list verbs empty-state UX across Human TTY and Agent modes."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._old_cwd = os.getcwd()
        os.chdir(self.root)
        # Create minimal .aw layout with records dirs
        (self.root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        (self.root / ".aw" / "records" / "specs").mkdir(parents=True)
        (self.root / ".aw" / "records" / "research").mkdir(parents=True)

    def tearDown(self) -> None:
        os.chdir(self._old_cwd)
        self._tmp.cleanup()

    def _run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def test_search_empty_human_tty_mode(self):
        rc, out, err = self._run_cli(
            ["search", "nonexistentpattern999", "--dir", str(self.root)]
        )
        self.assertEqual(rc, 1)
        self.assertIn("FINDINGS", out)
        self.assertIn("no matching lines for 'nonexistentpattern999'", out)
        self.assertIn("Active filters:", out)
        self.assertIn("pattern: nonexistentpattern999", out)
        self.assertIn("Next  aw search", out)

    def test_search_empty_agent_mode(self):
        rc, out, err = self._run_cli(
            ["search", "nonexistentpattern999", "--dir", str(self.root), "--agent"]
        )
        self.assertEqual(rc, 1)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "search")
        self.assertEqual(rec["outcome"], "findings")
        self.assertEqual(rec["exit"], 1)
        self.assertEqual(rec["findings"], 0)
        self.assertIn("aw search", rec["next"])
        self.assertIsNone(_ANSI.search(lines[0]))

    def test_list_repos_empty_human_and_agent_modes(self):
        # Human
        rc, out, err = self._run_cli(["list-repos"])
        self.assertEqual(rc, 0)
        self.assertIn("CLEAN", out)
        self.assertIn("no configured or discovered repos", out)
        self.assertIn("Next  aw setup", out)

        # Agent
        rc, out, err = self._run_cli(["list-repos", "--agent"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "list-repos")
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["next"], "aw setup")

    def test_config_exclude_list_empty_human_mode(self):
        rc, out, err = self._run_cli(["config", "exclude", "list"])
        self.assertEqual(rc, 0)
        self.assertIn("CLEAN", out)
        self.assertIn("never-install exclude list is empty", out)
        self.assertIn("Next  aw config exclude add", out)

    def test_ipd_board_empty_human_and_agent_modes(self):
        # Human mode on empty plans dir
        rc, out, err = self._run_cli(["ipd", "board", "--dir", str(self.root)])
        self.assertEqual(rc, 0)
        self.assertIn("CLEAN", out)
        self.assertTrue("no matching plans" in out or "no plans found" in out)
        self.assertIn("Next  aw ipd", out)

        # Agent mode
        rc, out, err = self._run_cli(
            ["ipd", "board", "--dir", str(self.root), "--agent"]
        )
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "ipd board")
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)

    def test_record_history_empty_human_and_agent_modes(self):
        # Human
        rc, out, err = self._run_cli(
            ["record-history", "nonex9", "--dir", str(self.root)]
        )
        self.assertEqual(rc, 0)
        self.assertIn("CLEAN", out)
        self.assertIn("no sidecar history for id6 nonex9", out)
        self.assertIn("Active filters:", out)
        self.assertIn("id6: nonex9", out)
        self.assertIn("Next  aw show nonex9", out)

        # Agent
        rc, out, err = self._run_cli(
            ["record-history", "nonex9", "--dir", str(self.root), "--agent"]
        )
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "record-history")
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["next"], "aw show nonex9")

    def test_project_status_empty_human_and_agent_modes(self):
        # Human
        rc, out, err = self._run_cli(["project", "status"])
        self.assertEqual(rc, 0)
        self.assertIn("CLEAN", out)
        self.assertIn("no registered project association found", out)
        self.assertIn("Active filters:", out)
        self.assertIn("Next  aw project attach", out)

        # Agent
        rc, out, err = self._run_cli(["project", "status", "--agent"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "project status")
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)
        self.assertIn("project attach", rec["next"])

    def test_show_empty_human_and_agent_modes(self):
        # Human
        rc, out, err = self._run_cli(
            ["show", "nonexistentref999", "--dir", str(self.root)]
        )
        self.assertEqual(rc, 1)
        self.assertIn("FAIL", out)
        self.assertIn("no records artifact matched 'nonexistentref999'", out)
        self.assertIn("Active filters:", out)
        self.assertIn("ref: nonexistentref999", out)
        self.assertIn("Next  aw find", out)

        # Agent
        rc, out, err = self._run_cli(
            ["show", "nonexistentref999", "--dir", str(self.root), "--agent"]
        )
        self.assertEqual(rc, 1)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "show")
        self.assertEqual(rec["outcome"], "findings")
        self.assertEqual(rec["exit"], 1)
        self.assertIn("aw find", rec["next"])

    def test_characterization_fact_parity_on_empty_reads(self):
        """Rubric D characterization: agent-mode facts and exit code match standard baseline."""
        verbs_and_expected_exits = [
            (["find", "nonexistent999", "--dir", str(self.root), "--agent"], 0),
            (["search", "nonexistent999", "--dir", str(self.root), "--agent"], 1),
            (["list-repos", "--agent"], 0),
            (["ipd", "board", "--dir", str(self.root), "--agent"], 0),
            (["record-history", "nonex9", "--dir", str(self.root), "--agent"], 0),
            (["project", "status", "--agent"], 0),
            (["show", "nonexistent999", "--dir", str(self.root), "--agent"], 1),
        ]
        for cmd, expected_rc in verbs_and_expected_exits:
            rc, out, err = self._run_cli(cmd)
            self.assertEqual(rc, expected_rc, f"Exit code mismatch on {cmd}")
            lines = [line.strip() for line in out.splitlines() if line.strip()]
            self.assertEqual(len(lines), 1, f"Expected exactly 1 JSONL record on {cmd}")
            rec = json.loads(lines[0])
            self.assertEqual(rec["schema"], "aw.agent/v1")
            self.assertEqual(rec["exit"], expected_rc)
            self.assertIsNone(
                _ANSI.search(lines[0]), f"ANSI found in agent mode on {cmd}"
            )


class MutationVerbsFeedbackAndErrorStateTests(unittest.TestCase):
    """V-02: Mutation verbs feedback, dry-run previews, and non-silent error paths."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._old_cwd = os.getcwd()
        os.chdir(self.root)
        # Create minimal git repository layout
        (self.root / ".git").mkdir()
        (self.root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)

    def tearDown(self) -> None:
        os.chdir(self._old_cwd)
        self._tmp.cleanup()

    def _run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def test_storage_init_dry_run_and_apply_feedback(self):
        # Dry-run feedback
        rc, out, err = self._run_cli(
            ["storage", "init", "--repo", str(self.root), "--dry-run"]
        )
        self.assertEqual(rc, 0)
        self.assertIn("DRY RUN", out)

        # Applied mutation feedback
        rc, out, err = self._run_cli(
            ["storage", "init", "--repo", str(self.root), "--yes", "--no-git"]
        )
        self.assertEqual(rc, 0)
        self.assertIn("Successfully initialized records storage", out)

    def test_storage_move_missing_flag_error_exit_2(self):
        # storage move without mandatory --new-dir must exit 2 with clear diagnostic, never silent
        rc, out, err = self._run_cli(["storage", "move"])
        self.assertEqual(rc, 2)
        combined = out + err
        self.assertTrue(len(combined.strip()) > 0)
        self.assertIn("required: --new-dir", combined)

    def test_storage_reattach_missing_companion_dir_error_exit_1(self):
        # storage reattach without mandatory --companion-dir must exit 1 with clear diagnostic
        rc, out, err = self._run_cli(["storage", "reattach"])
        self.assertEqual(rc, 1)
        combined = out + err
        self.assertTrue(len(combined.strip()) > 0)
        self.assertIn("--companion-dir is required", combined)

    def test_config_exclude_rm_nonexistent_returns_exit_1(self):
        rc, out, err = self._run_cli(
            ["config", "exclude", "rm", "/nonexistent/repo/path/999"]
        )
        self.assertEqual(rc, 1)
        self.assertIn("No exclude entry matched", out)

    def test_mutation_never_fails_silently_on_bad_invocation(self):
        # Point to a regular empty directory that is not a valid companion repo
        fake_companion = self.root / "not_a_companion"
        fake_companion.mkdir()
        rc, out, err = self._run_cli(
            ["storage", "attach", "--companion-dir", str(fake_companion), "--yes"]
        )
        self.assertNotEqual(rc, 0)
        combined = out + err
        self.assertTrue(len(combined.strip()) > 0)


class SurfaceAdHocScanTests(unittest.TestCase):
    """V-01 / V-03: Assert no CLI read/list handler uses bare ad-hoc 'no matching' prints."""

    def test_no_ad_hoc_empty_prints_in_handlers(self):
        pkg_dir = Path(__file__).resolve().parent.parent / "agent_workflows"
        prohibited_patterns = [
            re.compile(r'print\s*\(\s*["\']no matching', re.IGNORECASE),
            re.compile(r'print\s*\(\s*["\']no plans found', re.IGNORECASE),
            re.compile(r'print\s*\(\s*["\']no research doc', re.IGNORECASE),
            re.compile(
                r'term\.status\s*\(\s*["\']skip["\']\s*,\s*["\']No matching plans',
                re.IGNORECASE,
            ),
        ]
        violations = []
        for py_file in pkg_dir.glob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                for rx in prohibited_patterns:
                    if rx.search(line):
                        violations.append(f"{py_file.name}:{i}: {line.strip()}")

        self.assertEqual(
            violations,
            [],
            f"Found ad-hoc unformatted empty messages in CLI handlers (must use Term.empty_result): {violations}",
        )


if __name__ == "__main__":
    unittest.main()

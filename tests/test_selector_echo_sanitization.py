"""Tests for sanitizing user-supplied selector/target tokens and command arguments on machine and human surfaces.

Pins behavior across attention, runs, and partition commands on both machine (--agent, --json)
and human surfaces.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from agent_workflows import agent_schema, attention, leak_sanitizer


def walk_and_assert_no_home_paths(record: Any, path: str = "root") -> None:
    """Recursively assert that no string value in `record` matches any home-path detector.

    Checks both `agent_schema._HOME_PATH_RE` and `leak_sanitizer._FAIL_PATTERNS` home rules
    ('home-path', 'users-path', 'windows-home').
    """
    if isinstance(record, str):
        match_schema = agent_schema._HOME_PATH_RE.search(record)
        ls_matches = [
            p
            for p in ("home-path", "users-path", "windows-home")
            if leak_sanitizer._FAIL_PATTERNS[p].search(record)
        ]
        if match_schema or ls_matches:
            reasons = []
            if match_schema:
                reasons.append("agent_schema._HOME_PATH_RE")
            if ls_matches:
                reasons.append(f"leak_sanitizer._FAIL_PATTERNS[{ls_matches}]")
            raise AssertionError(
                f"Home path detected by {' and '.join(reasons)} at {path}: {record!r}"
            )
    elif isinstance(record, dict):
        for k, v in record.items():
            walk_and_assert_no_home_paths(v, f"{path}[{k!r}]")
    elif isinstance(record, (list, tuple, set)):
        for idx, item in enumerate(record):
            walk_and_assert_no_home_paths(item, f"{path}[{idx}]")


class SelectorEchoSanitizationTests(unittest.TestCase):
    _td: tempfile.TemporaryDirectory[str]
    repo_root: Path

    # Sample home paths constructed with split strings to avoid tripping leak sanitizer.
    HOME_PATH_POSIX = "/home/" + "developer/sample_target.ipd.md"  # split: leak guard
    HOME_TAIL_POSIX = "sample_target.ipd.md"

    @classmethod
    def setUpClass(cls) -> None:
        cls._td = tempfile.TemporaryDirectory()
        cls.repo_root = Path(cls._td.name)

        # Create minimal git repository structure so aw recognizes it as a repo
        plans_dir = cls.repo_root / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        sample_plan = plans_dir / "20261001-test-01-pln001-test-plan.ipd.md"
        sample_plan.write_text(
            "# IPD: Test plan\n\n"
            "- Date: 2026-10-01\n"
            "- Kind: child\n"
            "- Status: to-review\n"
            "- Priority: medium\n"
            "- Work-Kind: chore\n"
            "- Set: test\n"
            "- Order: 1\n"
            "- Id: pln001\n"
            "- Author: test\n\n"
            "## Workflow history\n"
            "- 2026-10-01 to-review (test): authored.\n",
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._td.cleanup()

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "PYTHONPATH": str(Path(__file__).resolve().parent.parent),
            "NO_COLOR": "1",
            "AW_NO_REEXEC": "1",
        }
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows.cli", *args],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            env=env,
        )

    # ----------------------------------------------------------------------------------------------
    # 1. Attention tests
    # ----------------------------------------------------------------------------------------------

    def test_attention_single_token_agent(self) -> None:
        res = self._run_cli("attention", self.HOME_PATH_POSIX, "--agent")
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        record = json.loads(res.stdout)
        walk_and_assert_no_home_paths(record)
        self.assertEqual(record["outcome"], "cannot-run")
        self.assertEqual(record["exit"], 2)
        self.assertIn(self.HOME_TAIL_POSIX, record["unresolved_selectors"][0])
        self.assertTrue(record["unresolved_selectors"][0].startswith("~"))

    def test_attention_single_token_json(self) -> None:
        res = self._run_cli("attention", self.HOME_PATH_POSIX, "--json")
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        record = json.loads(res.stdout)
        walk_and_assert_no_home_paths(record)
        self.assertEqual(record["outcome"], "cannot-run")
        self.assertEqual(record["exit"], 2)
        self.assertIn(self.HOME_TAIL_POSIX, record["unresolved_selectors"][0])

    def test_attention_single_token_human(self) -> None:
        res = self._run_cli("attention", self.HOME_PATH_POSIX)
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        self.assertIn(f"~/{self.HOME_TAIL_POSIX}", res.stderr)
        self.assertIsNone(agent_schema._HOME_PATH_RE.search(res.stderr))
        for pat in ("home-path", "users-path", "windows-home"):
            self.assertIsNone(leak_sanitizer._FAIL_PATTERNS[pat].search(res.stderr))

    def test_attention_multi_token_agent(self) -> None:
        res = self._run_cli("attention", self.HOME_PATH_POSIX, "bogus99", "--agent")
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        record = json.loads(res.stdout)
        walk_and_assert_no_home_paths(record)
        self.assertEqual(record["findings"], 2)
        self.assertEqual(len(record["unresolved_selectors"]), 2)
        self.assertIn(f"~/{self.HOME_TAIL_POSIX}", record["unresolved_selectors"])
        self.assertIn("bogus99", record["unresolved_selectors"])

    def test_attention_multi_token_json(self) -> None:
        res = self._run_cli("attention", self.HOME_PATH_POSIX, "bogus99", "--json")
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        record = json.loads(res.stdout)
        walk_and_assert_no_home_paths(record)
        self.assertIn(f"~/{self.HOME_TAIL_POSIX}", record["unresolved_selectors"])
        self.assertIn("bogus99", record["unresolved_selectors"])

    def test_attention_multi_token_human(self) -> None:
        res = self._run_cli("attention", self.HOME_PATH_POSIX, "bogus99")
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        self.assertIn(f"~/{self.HOME_TAIL_POSIX}", res.stderr)
        self.assertIn("bogus99", res.stderr)
        self.assertIsNone(agent_schema._HOME_PATH_RE.search(res.stderr))
        for pat in ("home-path", "users-path", "windows-home"):
            self.assertIsNone(leak_sanitizer._FAIL_PATTERNS[pat].search(res.stderr))

    def test_attention_matched_and_unmatched_agent(self) -> None:
        res = self._run_cli("attention", "pln001", self.HOME_PATH_POSIX, "--agent")
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        record = json.loads(res.stdout)
        walk_and_assert_no_home_paths(record)
        self.assertIn("pln001", record.get("matched_selectors", []))
        self.assertIn(f"~/{self.HOME_TAIL_POSIX}", record["unresolved_selectors"])

    def test_attention_direct_call_matched_and_invalid_redacted(self) -> None:
        hp_match = "/home/" + "developer/matched_target.ipd.md"  # split: leak guard
        hp_unmatch = "/home/" + "developer/unmatched_target.ipd.md"  # split: leak guard
        hp_invalid = "/home/" + "developer/invalid_target.ipd.md"  # split: leak guard

        facts = attention.SelectorMatchFacts(
            matched=(hp_match,),
            unmatched=(hp_unmatch,),
            invalid=(hp_invalid,),
            vocabulary=(),
        )
        record = attention.unresolved_selector_agent_record(facts)
        agent_schema.assert_valid_agent_record(record)
        walk_and_assert_no_home_paths(record)

        self.assertEqual(record["matched_selectors"], ["~/matched_target.ipd.md"])
        self.assertEqual(record["invalid_selectors"], ["~/invalid_target.ipd.md"])
        self.assertEqual(record["unresolved_selectors"], ["~/unmatched_target.ipd.md"])
        self.assertEqual(record["unresolved_targets"], ["~/unmatched_target.ipd.md"])
        self.assertIn("~/unmatched_target.ipd.md", record["error"])

    # ----------------------------------------------------------------------------------------------
    # 2. Runs tests
    # ----------------------------------------------------------------------------------------------

    def test_runs_unresolvable_target_agent(self) -> None:
        res = self._run_cli("runs", self.HOME_PATH_POSIX, "--agent")
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        record = json.loads(res.stdout)
        walk_and_assert_no_home_paths(record)
        self.assertEqual(record["outcome"], "cannot-run")
        self.assertEqual(record["exit"], 2)
        self.assertIn(f"~/{self.HOME_TAIL_POSIX}", record["unresolved_targets"])
        self.assertIn(f"~/{self.HOME_TAIL_POSIX}", record["error"])

    def test_runs_unresolvable_target_json(self) -> None:
        res = self._run_cli("runs", self.HOME_PATH_POSIX, "--json")
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        record = json.loads(res.stdout)
        walk_and_assert_no_home_paths(record)
        self.assertEqual(record["outcome"], "cannot-run")
        self.assertEqual(record["exit"], 2)
        self.assertIn(f"~/{self.HOME_TAIL_POSIX}", record["unresolved_targets"])
        self.assertIn(f"~/{self.HOME_TAIL_POSIX}", record["error"])

    def test_runs_unresolvable_target_human(self) -> None:
        res = self._run_cli("runs", self.HOME_PATH_POSIX)
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        self.assertIn(f"~/{self.HOME_TAIL_POSIX}", res.stderr)
        self.assertIsNone(agent_schema._HOME_PATH_RE.search(res.stderr))
        for pat in ("home-path", "users-path", "windows-home"):
            self.assertIsNone(leak_sanitizer._FAIL_PATTERNS[pat].search(res.stderr))

    def test_runs_analytics_tree_target_agent(self) -> None:
        target = ".aw/records/runs/analytics/nonexistent-run"
        res = self._run_cli("runs", target, "--agent")
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        record = json.loads(res.stdout)
        walk_and_assert_no_home_paths(record)
        self.assertIn(".aw/records/runs/analytics", record["error"])
        # Ensure repo root or other absolute path was not emitted
        self.assertNotIn(str(self.repo_root), record["error"])

    def test_runs_analytics_tree_target_human(self) -> None:
        target = ".aw/records/runs/analytics/nonexistent-run"
        res = self._run_cli("runs", target)
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)
        self.assertIn(".aw/records/runs/analytics", res.stderr)
        self.assertNotIn(str(self.repo_root), res.stderr)
        self.assertIsNone(agent_schema._HOME_PATH_RE.search(res.stderr))
        for pat in ("home-path", "users-path", "windows-home"):
            self.assertIsNone(leak_sanitizer._FAIL_PATTERNS[pat].search(res.stderr))

    # ----------------------------------------------------------------------------------------------
    # 3. Partition tests
    # ----------------------------------------------------------------------------------------------

    def test_partition_model_agent(self) -> None:
        res = self._run_cli(
            "partition",
            "-t",
            "plans",
            "-s",
            "to-review",
            "--model",
            self.HOME_PATH_POSIX,
            "--agent",
        )
        self.assertEqual(res.returncode, 0)
        self.assertNotIn("Traceback", res.stderr)
        record = json.loads(res.stdout)
        walk_and_assert_no_home_paths(record)
        self.assertTrue(len(record["commands"]) > 0)
        for cmd in record["commands"]:
            self.assertIn(f"~/{self.HOME_TAIL_POSIX}", cmd)

    def test_partition_model_json(self) -> None:
        res = self._run_cli(
            "partition",
            "-t",
            "plans",
            "-s",
            "to-review",
            "--model",
            self.HOME_PATH_POSIX,
            "--json",
        )
        self.assertEqual(res.returncode, 0)
        self.assertNotIn("Traceback", res.stderr)
        payload = json.loads(res.stdout)
        walk_and_assert_no_home_paths(payload)
        self.assertTrue(len(payload["commands"]) > 0)
        for cmd in payload["commands"]:
            self.assertIn(f"~/{self.HOME_TAIL_POSIX}", cmd)

    def test_partition_variant_agent(self) -> None:
        res = self._run_cli(
            "partition",
            "-t",
            "plans",
            "-s",
            "to-review",
            "--variant",
            self.HOME_PATH_POSIX,
            "--agent",
        )
        self.assertEqual(res.returncode, 0)
        self.assertNotIn("Traceback", res.stderr)
        record = json.loads(res.stdout)
        walk_and_assert_no_home_paths(record)
        self.assertTrue(len(record["commands"]) > 0)
        for cmd in record["commands"]:
            self.assertIn(f"~/{self.HOME_TAIL_POSIX}", cmd)

    def test_partition_variant_json(self) -> None:
        res = self._run_cli(
            "partition",
            "-t",
            "plans",
            "-s",
            "to-review",
            "--variant",
            self.HOME_PATH_POSIX,
            "--json",
        )
        self.assertEqual(res.returncode, 0)
        self.assertNotIn("Traceback", res.stderr)
        payload = json.loads(res.stdout)
        walk_and_assert_no_home_paths(payload)
        self.assertTrue(len(payload["commands"]) > 0)
        for cmd in payload["commands"]:
            self.assertIn(f"~/{self.HOME_TAIL_POSIX}", cmd)

    def test_partition_as_agent(self) -> None:
        res = self._run_cli(
            "partition",
            "-t",
            "plans",
            "-s",
            "to-review",
            "--as",
            self.HOME_PATH_POSIX,
            "--agent",
        )
        self.assertEqual(res.returncode, 0)
        self.assertNotIn("Traceback", res.stderr)
        record = json.loads(res.stdout)
        walk_and_assert_no_home_paths(record)
        self.assertTrue(len(record["commands"]) > 0)
        for cmd in record["commands"]:
            self.assertIn(f"~/{self.HOME_TAIL_POSIX}", cmd)

    def test_partition_as_json(self) -> None:
        res = self._run_cli(
            "partition",
            "-t",
            "plans",
            "-s",
            "to-review",
            "--as",
            self.HOME_PATH_POSIX,
            "--json",
        )
        self.assertEqual(res.returncode, 0)
        self.assertNotIn("Traceback", res.stderr)
        payload = json.loads(res.stdout)
        walk_and_assert_no_home_paths(payload)
        self.assertTrue(len(payload["commands"]) > 0)
        for cmd in payload["commands"]:
            self.assertIn(f"~/{self.HOME_TAIL_POSIX}", cmd)

    def test_partition_human_command_unredacted(self) -> None:
        res = self._run_cli(
            "partition",
            "-t",
            "plans",
            "-s",
            "to-review",
            "--model",
            self.HOME_PATH_POSIX,
        )
        self.assertEqual(res.returncode, 0)
        self.assertNotIn("Traceback", res.stderr)
        # Human command output MUST retain the unredacted path so it is shell-executable
        self.assertIn(self.HOME_PATH_POSIX, res.stdout)

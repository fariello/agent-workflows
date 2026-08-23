"""Unit and integration tests for tools/pwatch.py and tools/watch-agy.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add tools directory to path
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import pwatch  # noqa: E402


class TestPwatchRules(unittest.TestCase):
    def setUp(self):
        self.p_python = pwatch.Process(
            pid=100,
            ppid=1,
            name="python3",
            cmdline=("/usr/bin/python3", "tools/agy_run.py", "--ipd", "test.md"),
        )
        self.p_bash = pwatch.Process(
            pid=101,
            ppid=100,
            name="bash",
            cmdline=("/bin/bash", "-c", "pytest -n auto"),
        )
        self.p_pytest = pwatch.Process(
            pid=102,
            ppid=101,
            name="pytest",
            cmdline=("/usr/bin/pytest", "-n", "auto"),
        )

    def test_case_sensitive_string_match(self):
        r_exact = pwatch.Rule.create("python3", pwatch.MatchKind.MATCH_CS)
        self.assertTrue(r_exact.matches_process(self.p_python))
        self.assertFalse(r_exact.matches_process(self.p_bash))

        r_case_mismatch = pwatch.Rule.create("PYTHON3", pwatch.MatchKind.MATCH_CS)
        self.assertFalse(r_case_mismatch.matches_process(self.p_python))

        r_subarg = pwatch.Rule.create("agy_run.py", pwatch.MatchKind.MATCH_CS)
        self.assertTrue(r_subarg.matches_process(self.p_python))

    def test_case_insensitive_string_match(self):
        r_ci = pwatch.Rule.create("PYTHON", pwatch.MatchKind.MATCH_CI)
        self.assertTrue(r_ci.matches_process(self.p_python))

        r_ci_arg = pwatch.Rule.create("AUTO", pwatch.MatchKind.MATCH_CI)
        self.assertTrue(r_ci_arg.matches_process(self.p_bash))
        self.assertTrue(r_ci_arg.matches_process(self.p_pytest))

    def test_case_sensitive_regex_match(self):
        r_regex = pwatch.Rule.create(r"^py\w+3$", pwatch.MatchKind.REGEX_CS)
        self.assertTrue(r_regex.matches_process(self.p_python))
        self.assertFalse(r_regex.matches_process(self.p_pytest))

        r_regex_ci_fail = pwatch.Rule.create(r"^PYTHON\w+$", pwatch.MatchKind.REGEX_CS)
        self.assertFalse(r_regex_ci_fail.matches_process(self.p_python))

    def test_case_insensitive_regex_match(self):
        r_iregex = pwatch.Rule.create(r"^py\w+$", pwatch.MatchKind.REGEX_CI)
        self.assertTrue(r_iregex.matches_process(self.p_python))
        self.assertTrue(r_iregex.matches_process(self.p_pytest))
        self.assertFalse(r_iregex.matches_process(self.p_bash))


class TestPwatchHierarchyAndFiltering(unittest.TestCase):
    def test_matching_roots_and_exclusions(self):
        # Tree: p1 (root) -> p2 (child) -> p3 (grandchild)
        p1 = pwatch.Process(
            pid=10, ppid=1, name="parent_proc", cmdline=("parent_proc",)
        )
        p2 = pwatch.Process(
            pid=11, ppid=10, name="child_worker", cmdline=("child_worker",)
        )
        p3 = pwatch.Process(pid=12, ppid=11, name="sub_task", cmdline=("sub_task",))
        p1.children.append(p2)
        p2.children.append(p3)

        proc_dict = {10: p1, 11: p2, 12: p3}

        # Match child_worker
        proc_rules = [pwatch.Rule.create("child_worker", pwatch.MatchKind.MATCH_CS)]
        exclude_rules = []
        roots = pwatch.matching_roots(proc_dict, proc_rules, exclude_rules)
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0].pid, 11)

        # Match parent and child -> parent should be root, child should be nested
        proc_rules = [
            pwatch.Rule.create("parent_proc", pwatch.MatchKind.MATCH_CS),
            pwatch.Rule.create("child_worker", pwatch.MatchKind.MATCH_CS),
        ]
        roots = pwatch.matching_roots(proc_dict, proc_rules, exclude_rules)
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0].pid, 10)

        # Exclude parent_proc
        exclude_rules = [pwatch.Rule.create("parent_proc", pwatch.MatchKind.MATCH_CS)]
        roots = pwatch.matching_roots(proc_dict, proc_rules, exclude_rules)
        # parent excluded, so child_worker becomes root
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0].pid, 11)


class TestPwatchRecorder(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmpdir.name) / "test_record.jsonl"

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_record_snapshot_lifecycle(self):
        rec_rule = pwatch.Rule.create("worker", pwatch.MatchKind.MATCH_CI)
        excl_rule = pwatch.Rule.create("ignored", pwatch.MatchKind.MATCH_CI)

        recorder = pwatch.ProcessRecorder(self.log_path, [rec_rule], [excl_rule])

        p1 = pwatch.Process(pid=201, ppid=1, name="root_app", cmdline=("root_app",))
        p2 = pwatch.Process(
            pid=202, ppid=201, name="sub_worker", cmdline=("sub_worker", "--job", "1")
        )
        p3 = pwatch.Process(
            pid=203, ppid=201, name="ignored_worker", cmdline=("ignored_worker",)
        )
        p1.children.extend([p2, p3])

        # Snapshot 1: p2 observed first time
        count1 = recorder.record_snapshot([p1], "2026-08-23T10:00:00", 1787490000.0)
        self.assertEqual(count1, 1)

        lines1 = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines1), 1)
        entry1 = json.loads(lines1[0])
        self.assertEqual(entry1["event"], "first_seen")
        self.assertEqual(entry1["pid"], 202)
        self.assertEqual(entry1["observations_count"], 1)

        # Snapshot 2: p2 observed again
        count2 = recorder.record_snapshot([p1], "2026-08-23T10:00:02", 1787490002.0)
        self.assertEqual(count2, 1)

        lines2 = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines2), 2)
        entry2 = json.loads(lines2[1])
        self.assertEqual(entry2["event"], "observed")
        self.assertEqual(entry2["pid"], 202)
        self.assertEqual(entry2["observations_count"], 2)

        # Snapshot 3: p2 terminated (removed from tree)
        p1.children = [p3]
        count3 = recorder.record_snapshot([p1], "2026-08-23T10:00:05", 1787490005.0)
        self.assertEqual(count3, 0)

        lines3 = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines3), 3)
        entry3 = json.loads(lines3[2])
        self.assertEqual(entry3["event"], "terminated")
        self.assertEqual(entry3["pid"], 202)
        self.assertEqual(entry3["total_observations"], 2)


class TestPwatchCli(unittest.TestCase):
    def test_no_match_patterns_exits_2(self):
        proc = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "pwatch.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("at least one process match pattern is required", proc.stderr)

    def test_invalid_regex_exits_2(self):
        proc = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "pwatch.py"), "-R", "[unclosed", "--once"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("invalid regular expression", proc.stderr)

    def test_all_flag_combinations_parse_and_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rec_file = Path(tmpdir) / "rec.jsonl"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS_DIR / "pwatch.py"),
                    "-M",
                    "python3",
                    "-m",
                    "pytest",
                    "-R",
                    r"^py.*$",
                    "-r",
                    r"^sh$",
                    "-eM",
                    "excl_cs",
                    "-em",
                    "excl_ci",
                    "-eR",
                    r"^excl_r$",
                    "-er",
                    r"^excl_ri$",
                    "-rM",
                    "rec_cs",
                    "-rm",
                    "python",
                    "-rR",
                    r"^rec_r$",
                    "-rr",
                    r"^rec_ri$",
                    "--record-file",
                    str(rec_file),
                    "--once",
                    "--no-color",
                    "positional_bare_match",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("pwatch:", proc.stdout)

    def test_watch_agy_wrapper_backwards_compatibility(self):
        proc = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "watch-agy.py"), "--once", "--no-color"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("pwatch: agy", proc.stdout)


if __name__ == "__main__":
    unittest.main()

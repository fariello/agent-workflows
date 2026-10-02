"""Behavioral unit and integration tests for tools/lost_guard_census.py.

This test exercises the lost-guard census scanner against synthesized fixture inputs
and an isolated throwaway git repository constructed under tmp_path.
Per E-06, P16, and the project conventions:
- References NEITHER the real trim commit shas NOR the live tree.
- Carries NO livecorpus marker.
- Reads nothing under .aw/records/.
- Asserts both classifier directions (code-pin vs behavioral).
- Asserts the mixed-file annotation contract.
- Asserts printed counting-rule labels.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import unittest

from tools.lost_guard_census import (
    RULE_D_ONLY_ALL_DEFS,
    RULE_DM_MULTISET,
    annotate_candidate_file,
    classify_function,
    compute_commit_census,
    scan_axis_a,
    scan_axis_b,
)


class LostGuardCensusBehavioralTests(unittest.TestCase):
    def test_classifier_bidirectional_and_mixed(self) -> None:
        """Assert both classifier directions (code-pin vs behavioral) and argument resolution."""
        # 1. Code-pin fixture (F-05 AST inspection shape)
        pin_source = """
def test_no_new_module_level_first_party_import_in_runner_shared(self):
    tree = ast.parse(Path(rs.__file__).read_text(encoding="utf-8"))
    imports = [n for n in ast.walk(tree) if isinstance(n, ast.Import)]
    self.assertEqual(len(imports), 0)
"""
        is_b, is_e, is_a, reason = classify_function(
            "test_no_new_module_level_first_party_import_in_runner_shared",
            pin_source,
        )
        self.assertTrue(is_b, "ast.parse and inspect must trigger base pin signal")
        self.assertTrue(is_a, "F-05 fixture must classify as code pin")

        # 2. Behavioral fixture (drives CLI and asserts outcomes)
        beh_source = """
def test_cli_exit_code_on_empty_repo(self):
    res = subprocess.run(["aw", "check"], capture_output=True)
    self.assertEqual(res.returncode, 0)
"""
        is_b, is_e, is_a, reason = classify_function(
            "test_cli_exit_code_on_empty_repo", beh_source
        )
        self.assertFalse(is_b, "CLI execution must not trigger base pin signal")
        self.assertFalse(is_a, "Behavioral test must classify as behavioral, not pin")

        # 3. F-16 false-positive candidate functions: must NOT classify as pins under argument-resolving rule
        f16_names = [
            "test_a_lane_that_DECLARES_a_newly_needed_path_can_finalize",
            "test_scope_or_requirement_edit_invalidates_receipt",
            "test_persisted_interrupted_is_not_labelled_projected",
            "test_missing_input_token_format_now",
        ]
        for name in f16_names:
            is_b, is_e, is_a, _ = classify_function(
                name, "data = (d / 'state.json').read_text()"
            )
            self.assertFalse(
                is_a,
                f"{name} must not be classified as pin under argument-resolving rule",
            )


class LostGuardCensusSyntheticRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.temp_dir = pathlib.Path(self._td.name)

    def _setup_repo(self) -> tuple[pathlib.Path, str, str]:
        repo = self.temp_dir
        subprocess.run(
            ["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
        )

        # Commit 1: Before state
        # Create directories
        (repo / "tests").mkdir(parents=True, exist_ok=True)
        (repo / "agent_workflows").mkdir(parents=True, exist_ok=True)

        # test_deleted_a.py: 3 test functions
        (repo / "tests/test_deleted_a.py").write_text(
            "def test_a1(): pass\ndef test_a2(): pass\ndef test_a3(): pass\n",
            encoding="utf-8",
        )
        # test_deleted_b.py: 2 test functions
        (repo / "tests/test_deleted_b.py").write_text(
            "def test_b1(): pass\ndef test_b2(): pass\n",
            encoding="utf-8",
        )
        # test_modified_c.py: 4 test functions
        (repo / "tests/test_modified_c.py").write_text(
            "def test_c1(): pass\ndef test_c2(): pass\ndef test_c3(): pass\ndef test_c4(): pass\n",
            encoding="utf-8",
        )
        # test_mixed.py: 1 pin function, 1 behavioral function
        (repo / "tests/test_mixed.py").write_text(
            "def test_pin():\n    import ast\n    ast.parse('x=1')\ndef test_beh():\n    pass\n",
            encoding="utf-8",
        )
        # Shipped code citing tests
        (repo / "agent_workflows/worker.py").write_text(
            "# Guarded by tests/test_deleted_a.py::test_a1\n# Also mentions tests/test_unrelated_missing.py\n",
            encoding="utf-8",
        )
        (repo / "README.md").write_text(
            "See tests/test_deleted_a.py for details.\n",
            encoding="utf-8",
        )

        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial before tree"], cwd=repo, check=True
        )
        before_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()

        # Commit 2: Trim commit
        # Delete test_deleted_a.py, test_deleted_b.py, test_mixed.py (3 deleted files, 3+2+2 = 7 funcs)
        (repo / "tests/test_deleted_a.py").unlink()
        (repo / "tests/test_deleted_b.py").unlink()
        (repo / "tests/test_mixed.py").unlink()

        # Modify test_modified_c.py removing test_c3 and test_c4 (2 funcs removed)
        (repo / "tests/test_modified_c.py").write_text(
            "def test_c1(): pass\ndef test_c2(): pass\n",
            encoding="utf-8",
        )

        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "trim commit"], cwd=repo, check=True)
        trim_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()

        return repo, before_sha, trim_sha

    def test_synthetic_census_computation(self) -> None:
        """Assert census counts on synthetic git history match exact authored figures."""
        repo, before_sha, trim_sha = self._setup_repo()

        census = compute_commit_census(repo, trim_sha)
        self.assertEqual(census.deleted_files, 3, "Expected 3 deleted files")
        self.assertEqual(census.modified_files, 1, "Expected 1 modified file")
        # 3 deleted files had (3 + 2 + 2) = 7 functions. Modified file had 2 removed functions.
        # Total DM-multiset = 9.
        self.assertEqual(census.dm_multiset_removed, 9)
        self.assertEqual(census.d_only_all_defs, 7)

    def test_mixed_candidate_annotation_contract(self) -> None:
        """Assert the mixed-file annotation contract: reports both counts and names pin functions."""
        repo, before_sha, trim_sha = self._setup_repo()

        ann = annotate_candidate_file(repo, trim_sha, "tests/test_mixed.py")
        self.assertEqual(ann.total_funcs, 2)
        self.assertEqual(ann.pin_funcs, 1)
        self.assertEqual(ann.behavioral_funcs, 1)
        self.assertEqual(ann.pin_names, ["test_pin"])

    def test_synthetic_axes_attribution(self) -> None:
        """Assert Axis A attribution correctly partitions trim-attributable vs neither."""
        repo, before_sha, trim_sha = self._setup_repo()

        axis_a = scan_axis_a(repo, [trim_sha])
        self.assertIn("tests/test_deleted_a.py", axis_a.cited_paths)
        self.assertIn("tests/test_unrelated_missing.py", axis_a.cited_paths)

        # Attributed to trim_sha vs neither
        self.assertIn(
            "tests/test_deleted_a.py",
            axis_a.attr_19313eed
            or [p for p in axis_a.dangling_paths if p in census_paths(repo, trim_sha)],
        )
        self.assertIn("tests/test_unrelated_missing.py", axis_a.attr_neither)

        # Axis B
        axis_b = scan_axis_b(repo)
        self.assertIn("test_a1", axis_b.dangling_symbols)

    def test_cli_summary_output_and_rules(self) -> None:
        """Assert CLI invocation over synthetic repository prints named counting rules and exits 0."""
        repo, before_sha, trim_sha = self._setup_repo()

        tool_path = (
            pathlib.Path(__file__).resolve().parent.parent
            / "tools"
            / "lost_guard_census.py"
        )
        proc = subprocess.run(
            [sys.executable, str(tool_path), "--summary", trim_sha],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc.returncode, 0, f"CLI exited with {proc.returncode}: {proc.stderr}"
        )
        self.assertIn(
            RULE_DM_MULTISET,
            proc.stdout,
            "Summary must state DM-multiset counting rule",
        )
        self.assertIn(
            RULE_D_ONLY_ALL_DEFS, proc.stdout, "Summary must state D-only counting rule"
        )
        self.assertIn(
            "REACH PARTITION", proc.stdout, "Summary must print reach partition"
        )


def census_paths(repo: pathlib.Path, commit: str) -> set[str]:
    out = subprocess.check_output(
        ["git", "diff", "--diff-filter=D", "--name-only", f"{commit}^", commit],
        cwd=repo,
        text=True,
    )
    return set(out.strip().splitlines())


if __name__ == "__main__":
    unittest.main()

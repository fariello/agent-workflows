"""Tests for worktree isolation configurable per action type (IPD bzlxn0)."""

from __future__ import annotations

import inspect
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import config, runner_shared


class PolicyIsolationTests(unittest.TestCase):
    """Test policy_isolation reader shapes, defaults, and error posture (E-01 / V-01)."""

    def test_default_when_no_project_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = config.policy_isolation(tmp)
            self.assertEqual(result, {"execute": True, "review": True})

    def test_default_when_repo_root_is_none(self) -> None:
        result = config.policy_isolation(None)
        self.assertEqual(result, {"execute": True, "review": True})

    def test_bare_bool_under_run_isolate_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / ".aw" / "config" / "project.json"
            proj.parent.mkdir(parents=True)
            proj.write_text(
                json.dumps({"run": {"isolate_worktree": False}}), encoding="utf-8"
            )
            result = config.policy_isolation(tmp)
            self.assertEqual(result, {"execute": False, "review": False})

        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / ".aw" / "config" / "project.json"
            proj.parent.mkdir(parents=True)
            proj.write_text(
                json.dumps({"run": {"isolate_worktree": True}}), encoding="utf-8"
            )
            result = config.policy_isolation(tmp)
            self.assertEqual(result, {"execute": True, "review": True})

    def test_bare_bool_top_level(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / ".aw" / "config" / "project.json"
            proj.parent.mkdir(parents=True)
            proj.write_text(json.dumps({"isolate_worktree": False}), encoding="utf-8")
            result = config.policy_isolation(tmp)
            self.assertEqual(result, {"execute": False, "review": False})

    def test_object_shape_per_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / ".aw" / "config" / "project.json"
            proj.parent.mkdir(parents=True)
            proj.write_text(
                json.dumps(
                    {"run": {"isolate_worktree": {"execute": True, "review": False}}}
                ),
                encoding="utf-8",
            )
            result = config.policy_isolation(tmp)
            self.assertEqual(result, {"execute": True, "review": False})

    def test_partial_object_defaults_missing_actions_to_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / ".aw" / "config" / "project.json"
            proj.parent.mkdir(parents=True)
            proj.write_text(
                json.dumps({"run": {"isolate_worktree": {"review": False}}}),
                encoding="utf-8",
            )
            result = config.policy_isolation(tmp)
            self.assertEqual(result, {"execute": True, "review": False})

    def test_malformed_action_value_warns_and_falls_back_to_true(self) -> None:
        warnings: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / ".aw" / "config" / "project.json"
            proj.parent.mkdir(parents=True)
            proj.write_text(
                json.dumps({"run": {"isolate_worktree": {"review": "invalid"}}}),
                encoding="utf-8",
            )
            result = config.policy_isolation(tmp, warn=warnings.append)
            self.assertEqual(result, {"execute": True, "review": True})
            self.assertEqual(len(warnings), 1)
            self.assertIn("run.isolate_worktree.review", warnings[0])
            self.assertIn("'invalid'", warnings[0])

    def test_unknown_action_name_warns_and_drops(self) -> None:
        warnings: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / ".aw" / "config" / "project.json"
            proj.parent.mkdir(parents=True)
            proj.write_text(
                json.dumps(
                    {
                        "run": {
                            "isolate_worktree": {
                                "unknown_action": False,
                                "review": False,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            result = config.policy_isolation(tmp, warn=warnings.append)
            self.assertEqual(result, {"execute": True, "review": False})
            self.assertEqual(len(warnings), 1)
            self.assertIn("unknown action 'unknown_action'", warnings[0])

    def test_non_mapping_non_bool_warns_and_falls_back_to_true(self) -> None:
        warnings: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / ".aw" / "config" / "project.json"
            proj.parent.mkdir(parents=True)
            proj.write_text(
                json.dumps({"run": {"isolate_worktree": 12345}}),
                encoding="utf-8",
            )
            result = config.policy_isolation(tmp, warn=warnings.append)
            self.assertEqual(result, {"execute": True, "review": True})
            self.assertEqual(len(warnings), 1)
            self.assertIn("run.isolate_worktree", warnings[0])
            self.assertIn("12345", warnings[0])

    def test_isolate_worktree_is_not_registered_in_config_schema(self) -> None:
        matching = [k for k in config.CONFIG_SCHEMA if "isolat" in k]
        self.assertEqual(matching, [])


class ResolveIsolationPrecedenceTests(unittest.TestCase):
    """Test resolve_isolation over all four namespace states (E-03 / V-03)."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        cfg_dir = self.repo / ".aw" / "config"
        cfg_dir.mkdir(parents=True)
        # Policy sets review: false, execute: true
        (cfg_dir / "project.json").write_text(
            json.dumps(
                {"run": {"isolate_worktree": {"execute": True, "review": False}}}
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_namespace_state_false_cli_wins(self) -> None:
        """State 1: isolate_worktree is False (CLI explicitly passed --no-isolate-worktree).

        CLI wins: both execute and review become False regardless of policy.
        """

        class Args:
            isolate_worktree = False

        res = runner_shared.resolve_isolation(
            Args(), repo=self.repo, warn=lambda _m: None
        )
        self.assertEqual(res, {"execute": False, "review": False})

    def test_namespace_state_none_defers_to_policy(self) -> None:
        """State 2: isolate_worktree is None (CLI default when unsupplied).

        Defers to repository policy.
        """

        class Args:
            isolate_worktree = None

        res = runner_shared.resolve_isolation(
            Args(), repo=self.repo, warn=lambda _m: None
        )
        self.assertEqual(res, {"execute": True, "review": False})

    def test_namespace_state_absent_defers_to_policy(self) -> None:
        """State 3: isolate_worktree attribute is ABSENT (generic contract namespace).

        Defers to repository policy.
        """

        class Args:
            pass

        res = runner_shared.resolve_isolation(
            Args(), repo=self.repo, warn=lambda _m: None
        )
        self.assertEqual(res, {"execute": True, "review": False})

    def test_namespace_state_true_defers_to_policy(self) -> None:
        """State 4: isolate_worktree is True (generic fixture namespace placeholder).

        DECISION AND RATIONALE:
        Treating True as an override would let existing test fixtures defeat repository
        policy silently. Because no CLI flag currently produces an explicit True
        (only --no-isolate-worktree is registered on the run subparser), a True value on
        a generically filled namespace represents an unsupplied placeholder, matching
        freeze_run_policy_flags._supplied's recorded rule that a placeholder bool
        'can only mean ... ABSENT'. Therefore, True defers to repository policy.
        """

        class Args:
            isolate_worktree = True

        res = runner_shared.resolve_isolation(
            Args(), repo=self.repo, warn=lambda _m: None
        )
        self.assertEqual(res, {"execute": True, "review": False})


class IsolationForActionLegacyFallbackTests(unittest.TestCase):
    """Test isolation_for_action compatibility and legacy fallback (E-03 / V-03)."""

    def test_real_stranded_run_state_fixture(self) -> None:
        """Assert against the real on-disk fixture tests/fixtures/run_summary/stranded-run-state.json."""
        fixture_path = Path("tests/fixtures/run_summary/stranded-run-state.json")
        self.assertTrue(fixture_path.is_file(), f"Fixture missing: {fixture_path}")
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        options = data.get("options", {})
        self.assertIn("isolate_worktree", options)
        self.assertNotIn("isolate_execute", options)
        self.assertNotIn("isolate_review", options)

        # Legacy fallback to isolate_worktree (true)
        self.assertTrue(runner_shared.isolation_for_action(options, "execute"))
        self.assertTrue(runner_shared.isolation_for_action(options, "review"))

    def test_legacy_options_with_false(self) -> None:
        options = {"isolate_worktree": False}
        self.assertFalse(runner_shared.isolation_for_action(options, "execute"))
        self.assertFalse(runner_shared.isolation_for_action(options, "review"))

    def test_per_action_options(self) -> None:
        options = {
            "isolate_worktree": True,
            "isolate_execute": True,
            "isolate_review": False,
        }
        self.assertTrue(runner_shared.isolation_for_action(options, "execute"))
        self.assertFalse(runner_shared.isolation_for_action(options, "review"))

    def test_non_dict_options(self) -> None:
        self.assertTrue(runner_shared.isolation_for_action(None, "execute"))
        self.assertTrue(runner_shared.isolation_for_action({}, "execute"))


class LaunchSiteWiringStructuralTests(unittest.TestCase):
    """Test structural wiring at launch sites (E-04 / V-04)."""

    def test_execute_item_core_does_not_read_isolate_worktree_directly(self) -> None:
        """Assert that execute_item_core does not call options.get('isolate_worktree') directly."""
        src = inspect.getsource(runner_shared.execute_item_core)
        count = src.count('get("isolate_worktree"')
        self.assertEqual(
            count,
            0,
            f"execute_item_core still has {count} direct calls to get('isolate_worktree'). "
            "Must route through isolation_for_action.",
        )


class RunStartWarningTests(unittest.TestCase):
    """Test run-start warnings when repository policy disables isolation (E-06 / V-06)."""

    def test_warning_when_policy_disables_review(self) -> None:
        warnings: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / ".aw" / "config" / "project.json"
            proj.parent.mkdir(parents=True)
            proj.write_text(
                json.dumps({"run": {"isolate_worktree": {"review": False}}}),
                encoding="utf-8",
            )

            class Args:
                isolate_worktree = None

            runner_shared.resolve_isolation(Args(), repo=tmp, warn=warnings.append)
            self.assertEqual(len(warnings), 1)
            self.assertIn("run.isolate_worktree.review=false", warnings[0])

    def test_warning_when_policy_disables_execute(self) -> None:
        warnings: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / ".aw" / "config" / "project.json"
            proj.parent.mkdir(parents=True)
            proj.write_text(
                json.dumps({"run": {"isolate_worktree": {"execute": False}}}),
                encoding="utf-8",
            )

            class Args:
                isolate_worktree = None

            runner_shared.resolve_isolation(Args(), repo=tmp, warn=warnings.append)
            self.assertEqual(len(warnings), 1)
            self.assertIn("run.isolate_worktree.execute=false", warnings[0])

    def test_no_warning_when_default_or_both_isolated(self) -> None:
        warnings: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:

            class Args:
                isolate_worktree = None

            runner_shared.resolve_isolation(Args(), repo=tmp, warn=warnings.append)
            self.assertEqual(warnings, [])

        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / ".aw" / "config" / "project.json"
            proj.parent.mkdir(parents=True)
            proj.write_text(
                json.dumps(
                    {"run": {"isolate_worktree": {"execute": True, "review": True}}}
                ),
                encoding="utf-8",
            )

            class Args:
                isolate_worktree = None

            runner_shared.resolve_isolation(Args(), repo=tmp, warn=warnings.append)
            self.assertEqual(warnings, [])


class NonIsolatedReviewOutputCommitTests(unittest.TestCase):
    """Behavioral tests for non-isolated review output landing (E-05 / E-07(e) / V-05)."""

    def _setup_repo(self, root: Path, id6: str) -> tuple[Path, Path]:
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=repo,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test Runner"], cwd=repo, check=True
        )
        (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial commit"], cwd=repo, check=True)

        # Create project policy with review isolation disabled
        cfg_dir = repo / ".aw" / "config"
        cfg_dir.mkdir(parents=True)
        (cfg_dir / "project.json").write_text(
            json.dumps(
                {"run": {"isolate_worktree": {"execute": True, "review": False}}}
            ),
            encoding="utf-8",
        )

        # Create plan file
        plan_dir = repo / ".aw" / "records" / "plans" / "pending"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / f"20260925-testset-01-{id6}-test-plan.ipd.md"
        plan_file.write_text(
            f"# IPD: Test Plan\n\n- Id: {id6}\n- Status: to-review\n- Set: testset\n",
            encoding="utf-8",
        )
        reviews_dir = repo / ".aw" / "records" / "reviews"
        reviews_dir.mkdir(parents=True)
        (reviews_dir / ".gitkeep").write_text("", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "add plan and policy"], cwd=repo, check=True
        )
        return repo, plan_file

    def test_non_isolated_review_commits_uncommitted_output(self) -> None:
        """With review: false, driving a review item commits its plan edit and review record."""
        id6 = "tst123"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, plan_file = self._setup_repo(root, id6)

            # Simulate review turn modifying plan and writing review record, leaving them uncommitted
            plan_file.write_text(
                f"# IPD: Test Plan\n\n- Id: {id6}\n- Status: reviewed\n- Set: testset\n",
                encoding="utf-8",
            )
            reviews_dir = repo / ".aw" / "records" / "reviews"
            reviews_dir.mkdir(parents=True, exist_ok=True)
            review_record = (
                reviews_dir / f"20260925-testset-01-{id6}-test-plan.review.md"
            )
            review_record.write_text(
                f"# Review Record for {id6}\n\nOutcome: approved\n", encoding="utf-8"
            )

            # Verify status before commit_review_shared_output: files are uncommitted
            rc, out, _ = runner_shared._run_git(repo, ["status", "--porcelain"])
            self.assertEqual(rc, 0)
            self.assertIn(str(plan_file.name), out)
            self.assertIn(str(review_record.name), out)

            # Execute commit_review_shared_output
            commit_sha, paths = runner_shared.commit_review_shared_output(
                repo, id6, host_label="test"
            )
            self.assertIsNotNone(commit_sha)
            self.assertEqual(len(paths), 2)

            # Verify status after: git status --porcelain is clean!
            rc, out_after, _ = runner_shared._run_git(repo, ["status", "--porcelain"])
            self.assertEqual(rc, 0)
            self.assertEqual(
                out_after.strip(), "", f"Expected clean working tree, got: {out_after}"
            )

            # Verify the commit carries both files
            rc, log_out, _ = runner_shared._run_git(
                repo, ["show", "--stat", commit_sha]
            )
            self.assertEqual(rc, 0)
            self.assertIn(str(plan_file.name), log_out)
            self.assertIn(str(review_record.name), log_out)

    def test_negative_control_without_shared_output_commit_leaves_files_uncommitted(
        self,
    ) -> None:
        """NEGATIVE CONTROL (V-05): without the shared output commit, files are left UNCOMMITTED (F-6 regression)."""
        id6 = "tst456"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, plan_file = self._setup_repo(root, id6)

            # Simulate review turn modifying plan and writing review record, leaving them uncommitted
            plan_file.write_text(
                f"# IPD: Test Plan\n\n- Id: {id6}\n- Status: reviewed\n- Set: testset\n",
                encoding="utf-8",
            )
            reviews_dir = repo / ".aw" / "records" / "reviews"
            reviews_dir.mkdir(parents=True, exist_ok=True)
            review_record = (
                reviews_dir / f"20260925-testset-01-{id6}-test-plan.review.md"
            )
            review_record.write_text(
                f"# Review Record for {id6}\n\nOutcome: approved\n", encoding="utf-8"
            )

            # Without commit_review_shared_output running (the pre-E-05 behavior):
            rc, out, _ = runner_shared._run_git(repo, ["status", "--porcelain"])
            self.assertEqual(rc, 0)
            # The two files MUST remain uncommitted
            status_lines = [st_line for st_line in out.splitlines() if st_line.strip()]
            self.assertGreaterEqual(len(status_lines), 2)
            self.assertTrue(
                any(str(plan_file.name) in st_line for st_line in status_lines)
            )
            self.assertTrue(
                any(str(review_record.name) in st_line for st_line in status_lines)
            )


if __name__ == "__main__":
    unittest.main()

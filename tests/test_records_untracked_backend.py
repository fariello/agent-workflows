"""Unit and integration tests for the repository-untracked records backend (IPD lr0lln)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core, engine
from agent_workflows.artifact_core import get_ignored_dirs, is_ignored_path
from agent_workflows.install_wizard import (
    IncompletePolicyError,
    InvalidPolicyError,
    ProjectPolicy,
    get_preset_defaults,
    render_pre_write_plan,
    resolve_policy_noninteractive,
)
from agent_workflows.project_layout import materialize_project_layout
from agent_workflows.project_schema import (
    DurabilityState,
    GitPolicy,
    Placement,
    Preset,
    RecordsBackend,
    RootClass,
)
from agent_workflows.record_producers import get_git_owner
from agent_workflows.storage import get_storage_status, validate_storage_boundaries
from agent_workflows.term import Term


class TestRecordsUntrackedBackend(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        artifact_core._resolved_root_str.cache_clear()
        artifact_core._is_repository_untracked_backend.cache_clear()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        artifact_core._resolved_root_str.cache_clear()
        artifact_core._is_repository_untracked_backend.cache_clear()

    def _init_git_repo(self, path: str) -> None:
        subprocess.run(["git", "init", path], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", path, "config", "user.name", "Test User"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", path, "config", "user.email", "test@example.com"],
            check=True,
            capture_output=True,
        )

    def test_e02_get_git_owner_all_backends(self):
        """E-02 / V-02: get_git_owner returns None for repository-untracked and home (repaired crash),

        and returns 'target' for repository, 'companion' for companion.
        """
        # 1. repository-untracked -> None
        self.assertIsNone(
            get_git_owner(
                "plans",
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )
        )
        # 2. explicit repository-untracked via config
        cfg_dir = os.path.join(self.target_repo, ".aw", "config")
        os.makedirs(cfg_dir, exist_ok=True)
        with open(os.path.join(cfg_dir, "project.json"), "w", encoding="utf-8") as f:
            json.dump({"records_backend": "repository-untracked"}, f)
        self.assertIsNone(
            get_git_owner("plans", target_repo=self.target_repo, aw_home=self.aw_home)
        )

        # 3. home -> None (pre-existing crash repaired)
        with open(os.path.join(cfg_dir, "project.json"), "w", encoding="utf-8") as f:
            json.dump({"records_backend": "home"}, f)
        self.assertIsNone(
            get_git_owner("plans", target_repo=self.target_repo, aw_home=self.aw_home)
        )

        # 4. repository -> 'target'
        with open(os.path.join(cfg_dir, "project.json"), "w", encoding="utf-8") as f:
            json.dump({"records_backend": "repository"}, f)
        self.assertEqual(
            get_git_owner("plans", target_repo=self.target_repo, aw_home=self.aw_home),
            "target",
        )

        # 5. companion -> 'companion'
        with open(os.path.join(cfg_dir, "project.json"), "w", encoding="utf-8") as f:
            json.dump({"records_backend": "companion"}, f)
        self.assertEqual(
            get_git_owner("plans", target_repo=self.target_repo, aw_home=self.aw_home),
            "companion",
        )

    def test_e03_materialize_and_boundaries(self):
        """E-03 / V-03: materialize_project_layout creates in-tree records dir and

        get_storage_status does not raise StorageSecurityError.
        """
        policy = ProjectPolicy(
            preset=Preset.PRIVATE_TARGET.value,
            records_backend=RecordsBackend.REPOSITORY_UNTRACKED.value,
        )
        roots = materialize_project_layout(
            self.target_repo, policy, aw_home=self.aw_home
        )
        expected_records = os.path.join(self.target_repo, ".aw", "records")
        self.assertTrue(os.path.isdir(expected_records))
        self.assertEqual(roots["records"], expected_records)

        # validate_storage_boundaries accepts in-target path for repository-untracked
        validate_storage_boundaries(
            self.target_repo,
            expected_records,
            RecordsBackend.REPOSITORY_UNTRACKED.value,
            self.aw_home,
        )

        # get_storage_status does not raise
        status = get_storage_status(repo_path=self.target_repo, aw_home=self.aw_home)
        self.assertEqual(
            status.records_backend, RecordsBackend.REPOSITORY_UNTRACKED.value
        )
        self.assertEqual(status.records_path, expected_records)

    def test_e04_project_policy_override_and_validation(self):
        """E-04 / V-04: ProjectPolicy sets target-ignored/ignored under both empty and explicit placements,

        and refuses clean-delta.
        """
        # 1. Empty placements / default
        p1 = ProjectPolicy(records_backend=RecordsBackend.REPOSITORY_UNTRACKED.value)
        self.assertEqual(
            p1.placements[RootClass.RECORDS.value], Placement.TARGET_IGNORED.value
        )
        self.assertEqual(
            p1.git_policies[RootClass.RECORDS.value], GitPolicy.IGNORED.value
        )

        # 2. Explicit placements from preset
        pls, gps, dm, rb, ds = get_preset_defaults("private-target")
        self.assertEqual(pls[RootClass.RECORDS.value], Placement.TARGET_TRACKED.value)
        p2 = ProjectPolicy(
            records_backend=RecordsBackend.REPOSITORY_UNTRACKED.value,
            placements=pls,
            git_policies=gps,
        )
        self.assertEqual(
            p2.placements[RootClass.RECORDS.value], Placement.TARGET_IGNORED.value
        )
        self.assertEqual(
            p2.git_policies[RootClass.RECORDS.value], GitPolicy.IGNORED.value
        )

        # 3. Clean delta refusal
        p3 = ProjectPolicy(
            delivery_mode="clean-delta",
            records_backend=RecordsBackend.REPOSITORY_UNTRACKED.value,
        )
        with self.assertRaises(InvalidPolicyError):
            p3.validate()

    def test_e05_missing_field_hint_and_cli_help(self):
        """E-05 / V-05: Noninteractive hint names repository-untracked, install --help shows it,

        and migrate --help still offers only home/companion/repository.
        """
        # 1. Noninteractive hint string
        with self.assertRaises(IncompletePolicyError) as cm:
            resolve_policy_noninteractive(
                repo_path=self.target_repo,
                explicit_preset=None,
                explicit_delivery=None,
                explicit_backend=None,
            )
        err_msg = str(cm.exception)
        self.assertIn(
            "--records-backend (home | companion | repository | repository-untracked)",
            err_msg,
        )

        # 2. install --help choices
        res_install = subprocess.run(
            ["python3", "-m", "agent_workflows", "install", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            check=True,
        )
        self.assertIn("repository-untracked", res_install.stdout)

        # 3. migrate-layout --help choices (deferred surface left unchanged)
        res_migrate = subprocess.run(
            ["python3", "-m", "agent_workflows", "migrate-layout", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            check=True,
        )
        self.assertIn("{home,companion,repository}", res_migrate.stdout)
        self.assertNotIn("repository-untracked", res_migrate.stdout)

    def test_e06_refuse_on_repo_with_tracked_records(self):
        """E-06 / V-06: Refuse repository-untracked on a repo with already-tracked records,

        accept on a clean repo.
        """
        repo_clean = os.path.join(self.tmp_dir, "repo_clean")
        self._init_git_repo(repo_clean)

        # 1. Clean repo acceptance
        policy_clean = ProjectPolicy(
            records_backend=RecordsBackend.REPOSITORY_UNTRACKED.value
        )
        policy_clean.validate(repo_path=repo_clean)

        # Verify ls-files is empty
        res_clean = subprocess.run(
            ["git", "-C", repo_clean, "ls-files", ".aw/records"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(res_clean.stdout.strip(), "")

        # 2. Tracked repo refusal
        repo_tracked = os.path.join(self.tmp_dir, "repo_tracked")
        self._init_git_repo(repo_tracked)
        tracked_plan = os.path.join(
            repo_tracked, ".aw", "records", "plans", "pending", "p.ipd.md"
        )
        os.makedirs(os.path.dirname(tracked_plan), exist_ok=True)
        with open(tracked_plan, "w", encoding="utf-8") as f:
            f.write("# Test Plan\n")
        subprocess.run(
            ["git", "-C", repo_tracked, "add", ".aw/records/plans/pending/p.ipd.md"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", repo_tracked, "commit", "-m", "add plan"],
            check=True,
            capture_output=True,
        )

        res_tracked = subprocess.run(
            ["git", "-C", repo_tracked, "ls-files", ".aw/records"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn(".aw/records/plans/pending/p.ipd.md", res_tracked.stdout)

        policy_tracked = ProjectPolicy(
            records_backend=RecordsBackend.REPOSITORY_UNTRACKED.value
        )
        with self.assertRaises(InvalidPolicyError) as cm:
            policy_tracked.validate(repo_path=repo_tracked)
        err = str(cm.exception)
        self.assertIn("already tracks records in Git", err)
        self.assertIn(".aw/records/plans/pending/p.ipd.md", err)
        self.assertIn("aw migrate", err)

    def test_e07_ensure_untracked_records_ignore(self):
        """E-07 / V-07: ensure_untracked_records_ignore writes anchored /records/ line once,

        idempotent on second call returning False, matches git check-ignore.
        """
        repo = os.path.join(self.tmp_dir, "repo_ignore")
        self._init_git_repo(repo)

        # First call writes and returns True
        w1 = engine.ensure_untracked_records_ignore(Path(repo))
        self.assertTrue(w1)

        gi_file = Path(repo) / ".aw" / ".gitignore"
        self.assertTrue(gi_file.is_file())
        text1 = gi_file.read_text(encoding="utf-8")
        self.assertIn("/records/\n", text1)

        # Second call returns False
        w2 = engine.ensure_untracked_records_ignore(Path(repo))
        self.assertFalse(w2)

        # Grep exactly 1 occurrence of '^/records/$'
        lines = [
            line.strip() for line in gi_file.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(lines.count("/records/"), 1)

        # git check-ignore matches .aw/records path
        test_record = os.path.join(repo, ".aw", "records", "plans", "pending", "x.md")
        os.makedirs(os.path.dirname(test_record), exist_ok=True)
        with open(test_record, "w", encoding="utf-8") as f:
            f.write("# Record\n")
        res_ig = subprocess.run(
            ["git", "-C", repo, "check-ignore", "-v", ".aw/records/plans/pending/x.md"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn(".aw/.gitignore", res_ig.stdout)
        self.assertIn("/records/", res_ig.stdout)

        # Test line-anchored check when comment contains substring 'records/'
        repo2 = os.path.join(self.tmp_dir, "repo_ignore2")
        self._init_git_repo(repo2)
        gi_file2 = Path(repo2) / ".aw" / ".gitignore"
        gi_file2.parent.mkdir(parents=True, exist_ok=True)
        gi_file2.write_text(
            "# Explanatory note about records/ in this repo\n", encoding="utf-8"
        )
        w_comm = engine.ensure_untracked_records_ignore(Path(repo2))
        self.assertTrue(w_comm)
        lines2 = [
            line.strip() for line in gi_file2.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(lines2.count("/records/"), 1)

    def test_e08_scanner_visibility_scoped_to_backend(self):
        """E-08 / V-08: Gated scanner visibility keeps ignored .aw/records visible when configured,

        hides untracked/runs lanes, and keeps records hidden when user ignores them in root .gitignore without AW backend.
        """
        # Case 1: repository-untracked backend configured in .aw/config/project.json + /records/ in .aw/.gitignore
        repo = os.path.join(self.tmp_dir, "repo_scanner")
        self._init_git_repo(repo)
        engine.ensure_untracked_records_ignore(Path(repo))
        cfg_dir = os.path.join(repo, ".aw", "config")
        os.makedirs(cfg_dir, exist_ok=True)
        with open(os.path.join(cfg_dir, "project.json"), "w", encoding="utf-8") as f:
            json.dump(
                {"preset": "private-target", "records_backend": "repository-untracked"},
                f,
            )

        plan_path = (
            Path(repo)
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260924-test-01-abc123-test.ipd.md"
        )
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(
            "# Plan\n- Status: approved\n- Id: abc123\n- Set: test\n", encoding="utf-8"
        )

        prompt_untracked = (
            Path(repo) / ".aw" / "records" / "prompts" / "untracked" / "x.md"
        )
        prompt_untracked.parent.mkdir(parents=True, exist_ok=True)
        prompt_untracked.write_text("# Untracked prompt\n", encoding="utf-8")

        run_state = Path(repo) / ".aw" / "records" / "runs" / "r1" / "state.json"
        run_state.parent.mkdir(parents=True, exist_ok=True)
        run_state.write_text("{}", encoding="utf-8")

        ignored = get_ignored_dirs(Path(repo))
        self.assertNotIn(".aw/records", ignored)
        self.assertFalse(is_ignored_path(plan_path, Path(repo), ignored_dirs=ignored))
        self.assertTrue(
            is_ignored_path(prompt_untracked, Path(repo), ignored_dirs=ignored)
        )
        self.assertTrue(is_ignored_path(run_state, Path(repo), ignored_dirs=ignored))

        # Case 2: Negative case - root .gitignore ignores .aw/records/ with NO repository-untracked policy
        repo_neg = os.path.join(self.tmp_dir, "repo_scanner_neg")
        self._init_git_repo(repo_neg)
        with open(os.path.join(repo_neg, ".gitignore"), "w", encoding="utf-8") as f:
            f.write(".aw/records/\n")
        plan_neg = (
            Path(repo_neg)
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260924-test-01-abc123-test.ipd.md"
        )
        plan_neg.parent.mkdir(parents=True, exist_ok=True)
        plan_neg.write_text("# Plan\n", encoding="utf-8")

        artifact_core._resolved_root_str.cache_clear()
        artifact_core._is_repository_untracked_backend.cache_clear()

        ignored_neg = get_ignored_dirs(Path(repo_neg))
        self.assertIn(".aw/records", ignored_neg)
        self.assertTrue(
            is_ignored_path(plan_neg, Path(repo_neg), ignored_dirs=ignored_neg)
        )

    def test_e09_storage_status_recommendation_and_durability(self):
        """E-09 / V-09: get_storage_status recommendation includes 'not durable across clones' for

        repository-untracked and reports unversioned (no .git) or local-git (.git exists).
        """
        cfg_dir = os.path.join(self.target_repo, ".aw", "config")
        os.makedirs(cfg_dir, exist_ok=True)
        with open(os.path.join(cfg_dir, "project.json"), "w", encoding="utf-8") as f:
            json.dump({"records_backend": "repository-untracked"}, f)

        # 1. unversioned (no records .git)
        s1 = get_storage_status(repo_path=self.target_repo, aw_home=self.aw_home)
        self.assertEqual(s1.durability_state, DurabilityState.UNVERSIONED.value)
        self.assertIn("not durable across clones", s1.recommendation)
        self.assertIn(".aw/records/", s1.recommendation)

        # 2. local-git (records .git exists)
        records_git = os.path.join(self.target_repo, ".aw", "records", ".git")
        os.makedirs(records_git, exist_ok=True)
        s2 = get_storage_status(repo_path=self.target_repo, aw_home=self.aw_home)
        self.assertEqual(s2.durability_state, DurabilityState.LOCAL_GIT.value)
        self.assertIn("not durable across clones", s2.recommendation)

        # 3. repository backend has NO "not durable across clones" warning
        with open(os.path.join(cfg_dir, "project.json"), "w", encoding="utf-8") as f:
            json.dump({"records_backend": "repository"}, f)
        s3 = get_storage_status(repo_path=self.target_repo, aw_home=self.aw_home)
        self.assertEqual(s3.durability_state, DurabilityState.REPOSITORY_MANAGED.value)
        self.assertNotIn("not durable across clones", s3.recommendation)

    def test_e10_install_wizard_and_cli_warnings(self):
        """E-10 / V-10: render_pre_write_plan renders yellow warning and [target] (ignored) row,

        repository backend shows no warning.
        """
        term = Term(color="always")
        p_untracked = ProjectPolicy(
            preset=Preset.PRIVATE_TARGET.value,
            records_backend=RecordsBackend.REPOSITORY_UNTRACKED.value,
        )
        plan_text = render_pre_write_plan(p_untracked, self.target_repo, term=term)
        self.assertIn(
            "Records are git-ignored in this working tree (repository-untracked); they are not durable across clones",
            plan_text,
        )
        self.assertIn("[target] (ignored)", plan_text)

        p_repo = ProjectPolicy(
            preset=Preset.PRIVATE_TARGET.value,
            records_backend=RecordsBackend.REPOSITORY.value,
        )
        plan_repo_text = render_pre_write_plan(p_repo, self.target_repo, term=term)
        self.assertNotIn(
            "Records are git-ignored in this working tree (repository-untracked)",
            plan_repo_text,
        )

    def test_e11_end_to_end_install_and_setup_refusal(self):
        """E-11 / V-11: End-to-end install produces git-ignored, untracked records tree and

        aw setup --records-backend repository-untracked refuses with clear message.
        """
        repo = os.path.join(self.tmp_dir, "repo_e2e")
        self._init_git_repo(repo)

        # 1. Live aw install
        res = subprocess.run(
            [
                "python3",
                "-m",
                "agent_workflows",
                "install",
                repo,
                "--preset",
                "private-target",
                "--records-backend",
                "repository-untracked",
                "--yes",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        self.assertEqual(
            res.returncode, 0, f"Install failed: {res.stderr}\n{res.stdout}"
        )
        self.assertIn(
            "Records are git-ignored in this working tree (repository-untracked)",
            res.stdout,
        )

        # Check config/project.json
        proj_json = Path(repo) / ".aw" / "config" / "project.json"
        self.assertTrue(proj_json.is_file())
        data = json.loads(proj_json.read_text(encoding="utf-8"))
        self.assertEqual(data.get("records_backend"), "repository-untracked")

        # Check .aw/.gitignore has /records/
        gi = Path(repo) / ".aw" / ".gitignore"
        self.assertTrue(gi.is_file())
        self.assertIn("/records/", gi.read_text(encoding="utf-8"))

        # Check git ls-files .aw/records is empty
        res_ls = subprocess.run(
            ["git", "-C", repo, "ls-files", ".aw/records"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(res_ls.stdout.strip(), "")

        # 2. aw setup refusal
        res_setup = subprocess.run(
            [
                "python3",
                "-m",
                "agent_workflows",
                "setup",
                "--records-backend",
                "repository-untracked",
                "--yes",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        self.assertEqual(res_setup.returncode, 1)
        self.assertIn(
            "--records-backend repository-untracked is not supported via 'aw setup'",
            res_setup.stdout + res_setup.stderr,
        )
        self.assertIn("aw install", res_setup.stdout + res_setup.stderr)


if __name__ == "__main__":
    unittest.main()

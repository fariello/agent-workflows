"""Tests for the upgrade-rehearsal harness ``tools/aw_upgrade_test.py``.

WHAT THESE TESTS ARE FOR. The harness copies REAL repositories and runs a MUTATING installer
against the copy, so its own bugs could damage real work. These tests therefore target the
four safety invariants the harness documents, plus the inspection logic a rehearsal's
conclusions rest on. They deliberately do NOT test whether an upgrade produces a correct
result: judging that is the human's job, and encoding an opinion here would turn an
evidence-gathering rig into an unreviewed spec.

Every test builds its own throwaway git repo, so nothing here touches a real repository or
the operator's real config.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import REPO_ROOT, git, init_repo, load_module  # noqa: E402

TOOL = REPO_ROOT / "tools" / "aw_upgrade_test.py"
uat = load_module("aw_upgrade_test", TOOL)


def make_source_repo(
    path: Path, version: str = "1.2.1", layout: str = "legacy"
) -> Path:
    """Build a fake installed repo at ``path`` resembling a real managed target."""

    init_repo(path)
    if layout == "legacy":
        wf = path / ".agents" / "workflows"
        wf.mkdir(parents=True)
        (wf / "VERSION").write_text(f"{version}\n", encoding="utf-8")
        (wf / "index.md").write_text("# workflows\n", encoding="utf-8")
    elif layout == "aw":
        sysd = path / ".aw" / "system"
        sysd.mkdir(parents=True)
        (sysd / "VERSION").write_text(f"{version}\n", encoding="utf-8")
        (sysd / "managed-sections.json").write_text(
            json.dumps(
                {"schema_version": 2, "installed_version": version, "files": {}}
            ),
            encoding="utf-8",
        )
    elif layout == "dual":
        make_source_repo(path, version, "legacy")
        sysd = path / ".aw" / "system"
        sysd.mkdir(parents=True, exist_ok=True)
        (sysd / "VERSION").write_text(f"{version}\n", encoding="utf-8")
        return path
    (path / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (path / "README.md").write_text("# project\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "seed")
    return path


class TempCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()


class InspectionTests(TempCase):
    """Version/layout detection: the basis of every claim a rehearsal report makes."""

    def test_installed_version_prefers_canonical_aw_location(self) -> None:
        repo = self.tmp / "r"
        make_source_repo(repo, "1.2.1", "legacy")
        sysd = repo / ".aw" / "system"
        sysd.mkdir(parents=True, exist_ok=True)
        (sysd / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        version, rel = uat.installed_version(repo)
        self.assertEqual(version, "9.9.9")
        self.assertEqual(rel, ".aw/system/VERSION")

    def test_installed_version_reads_legacy_location(self) -> None:
        repo = make_source_repo(self.tmp / "r", "1.2.1", "legacy")
        self.assertEqual(
            uat.installed_version(repo), ("1.2.1", ".agents/workflows/VERSION")
        )

    def test_installed_version_absent(self) -> None:
        repo = init_repo(self.tmp / "bare")
        self.assertEqual(uat.installed_version(repo), (None, None))

    def test_detect_layout_all_four_states(self) -> None:
        self.assertEqual(
            uat.detect_layout(make_source_repo(self.tmp / "a", layout="legacy")),
            "legacy",
        )
        self.assertEqual(
            uat.detect_layout(make_source_repo(self.tmp / "b", layout="aw")), "aw"
        )
        self.assertEqual(
            uat.detect_layout(make_source_repo(self.tmp / "c", layout="dual")), "dual"
        )
        self.assertEqual(uat.detect_layout(init_repo(self.tmp / "d")), "none")

    def test_empty_legacy_dirs_are_litter_not_a_split_brain_layout(self) -> None:
        """Measured on a real repo: a finished migration left 9 EMPTY legacy dirs.

        Classifying by directory EXISTENCE reported that as ``dual``, conflating harmless
        litter with the split-brain state the installer refuses. Classification is therefore
        by live file content.
        """

        repo = make_source_repo(self.tmp / "r", "1.2.1", "aw")
        for sub in ("assess/tools", "verify/tools", "benchmark"):
            (repo / ".agents" / "workflows" / sub).mkdir(parents=True)
        self.assertEqual(uat.detect_layout(repo), "aw+litter")
        self.assertGreater(uat.count_empty_dirs(repo / ".agents"), 0)

    def test_genuine_dual_layout_requires_files_on_both_sides(self) -> None:
        repo = make_source_repo(self.tmp / "r", "1.2.1", "aw")
        legacy = repo / ".agents" / "workflows"
        legacy.mkdir(parents=True)
        (legacy / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        self.assertEqual(uat.detect_layout(repo), "dual")

    def test_has_files_distinguishes_empty_from_populated(self) -> None:
        empty = self.tmp / "empty" / "deep" / "nested"
        empty.mkdir(parents=True)
        self.assertFalse(uat.has_files(self.tmp / "empty"))
        (empty / "f.txt").write_text("x", encoding="utf-8")
        self.assertTrue(uat.has_files(self.tmp / "empty"))

    def test_legacy_breakdown_attributes_leftovers_to_subtrees(self) -> None:
        repo = make_source_repo(self.tmp / "r", "1.2.1", "aw")
        skills = repo / ".agents" / "skills" / "assess-ui-ux"
        skills.mkdir(parents=True)
        (skills / "SKILL.md").write_text("x", encoding="utf-8")
        (repo / ".agents" / "README.md").write_text("x", encoding="utf-8")
        breakdown = uat.legacy_breakdown(repo)
        self.assertEqual(breakdown.get("skills"), 1)
        self.assertEqual(breakdown.get("(root)"), 1)

    def test_observations_flag_orphaned_skills(self) -> None:
        kinds = [
            o["kind"]
            for o in uat.derive_observations(
                {
                    "baseline_layout": "legacy",
                    "layout": "aw+litter",
                    "legacy_files_remaining": 92,
                    "legacy_breakdown": {"skills": 92},
                }
            )
        ]
        self.assertIn("orphaned-skills", kinds)

    def test_observations_flag_empty_legacy_dirs(self) -> None:
        kinds = [
            o["kind"]
            for o in uat.derive_observations({"layout": "aw+litter", "empty_dirs": 9})
        ]
        self.assertIn("empty-legacy-dirs", kinds)
        self.assertNotIn("dual-layout", kinds)

    def test_manifest_summary_reports_rows_and_version(self) -> None:
        repo = make_source_repo(self.tmp / "r", "1.2.1", "aw")
        summary = uat.manifest_summary(repo)
        self.assertEqual(summary["installed_version"], "1.2.1")
        self.assertEqual(summary["schema_version"], 2)
        self.assertEqual(summary["rows"], 0)

    def test_manifest_summary_absent_is_not_an_error(self) -> None:
        self.assertEqual(
            uat.manifest_summary(init_repo(self.tmp / "r")), {"path": None}
        )

    def test_snapshot_tree_excludes_git_and_harness_scaffolding(self) -> None:
        repo = make_source_repo(self.tmp / "r", layout="aw")
        (repo / uat.MARKER_NAME).write_text("{}", encoding="utf-8")
        (repo / ".aw-upgrade-test").mkdir()
        (repo / ".aw-upgrade-test" / "junk").write_text("x", encoding="utf-8")
        files = uat.snapshot_tree(repo)
        self.assertIn("README.md", files)
        self.assertFalse([f for f in files if f.startswith(".git")])
        self.assertNotIn(uat.MARKER_NAME, files)
        self.assertFalse([f for f in files if f.startswith(".aw-upgrade-test")])


class SafetyInvariantOneSourceUntouched(TempCase):
    """Invariant 1: the source repo is never mutated, and copies are never hardlinked."""

    def test_source_tree_is_byte_identical_after_a_copy(self) -> None:
        source = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        before = {
            p: (p.stat().st_mtime_ns, p.read_bytes())
            for p in sorted(source.rglob("*"))
            if p.is_file() and ".git" not in p.parts
        }
        uat.copy_full(source, self.tmp / "dst")
        after = {
            p: (p.stat().st_mtime_ns, p.read_bytes())
            for p in sorted(source.rglob("*"))
            if p.is_file() and ".git" not in p.parts
        }
        self.assertEqual(before, after)

    def test_copy_does_not_hardlink_so_sandbox_writes_cannot_reach_the_source(
        self,
    ) -> None:
        """The specific hazard ``cp -al`` would create, closed by construction.

        With hardlinked content, truncating the sandbox's file in place would empty the
        SOURCE's file too. Asserting distinct inodes AND writing through proves it cannot.
        """

        source = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        sandbox = self.tmp / "dst"
        uat.copy_full(source, sandbox)

        src_file = source / ".agents" / "workflows" / "VERSION"
        dst_file = sandbox / ".agents" / "workflows" / "VERSION"
        self.assertNotEqual(src_file.stat().st_ino, dst_file.stat().st_ino)

        with open(dst_file, "w", encoding="utf-8") as fh:
            fh.write("CLOBBERED\n")
        self.assertEqual(src_file.read_text(encoding="utf-8").strip(), "1.2.1")

    def test_no_hardlink_strategy_is_offered(self) -> None:
        """A cheap-but-unsafe strategy must not be reachable, even opt-in."""

        parser = uat.build_parser()
        args = parser.parse_args(["new", "x", "--strategy", "clone"])
        self.assertEqual(args.strategy, "clone")
        with self.assertRaises(SystemExit):
            parser.parse_args(["new", "x", "--strategy", "hardlink"])
        with self.assertRaises(uat.HarnessError):
            uat.create_sandbox(
                uat.SourceRepo.inspect(make_source_repo(self.tmp / "s")),
                self.tmp / "boxes",
                strategy="hardlink",
            )


class SafetyInvariantTwoNeverPush(TempCase):
    """Invariant 2: a sandbox cannot reach the source's real upstream."""

    def _sandbox_with_remote(self) -> Path:
        source = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        git(
            source, "remote", "add", "origin", "git@example.invalid:someone/private.git"
        )
        git(source, "remote", "add", "backup", "https://example.invalid/backup.git")
        sandbox = self.tmp / "box"
        uat.copy_full(source, sandbox)
        return sandbox

    def test_copy_carries_remotes_which_is_exactly_why_neutralizing_is_required(
        self,
    ) -> None:
        """Documents the hazard rather than assuming it: the copy DOES inherit remotes."""

        sandbox = self._sandbox_with_remote()
        remotes = uat.git_out(sandbox, "remote").split()
        self.assertIn("origin", remotes)
        self.assertIn("backup", remotes)

    def test_neutralize_removes_every_real_remote(self) -> None:
        sandbox = self._sandbox_with_remote()
        result = uat.neutralize_git(sandbox)
        self.assertEqual(sorted(result["remotes_removed"]), ["backup", "origin"])
        remaining = [
            r
            for r in uat.git_out(sandbox, "remote").split()
            if r != "aw-upgrade-test-blackhole"
        ]
        self.assertEqual(remaining, [])

    def test_create_sandbox_neutralizes_before_returning(self) -> None:
        source = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        git(
            source, "remote", "add", "origin", "git@example.invalid:someone/private.git"
        )
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(source), self.tmp / "boxes", strategy="full"
        )
        remaining = [
            r
            for r in uat.git_out(sandbox, "remote").split()
            if r != "aw-upgrade-test-blackhole"
        ]
        self.assertEqual(remaining, [])

    def test_a_push_from_a_sandbox_fails(self) -> None:
        """End-to-end proof, not an inference from config: an actual push must fail."""

        sandbox = self._sandbox_with_remote()
        uat.neutralize_git(sandbox)
        proc = subprocess.run(
            ["git", "push", "origin", "HEAD"],
            cwd=str(sandbox),
            capture_output=True,
            text=True,
            check=False,
            env=dict(os.environ, GIT_TERMINAL_PROMPT="0"),
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_a_re_added_origin_still_cannot_reach_a_network(self) -> None:
        """Defense in depth: removal is not the only barrier."""

        sandbox = self._sandbox_with_remote()
        uat.neutralize_git(sandbox)
        push_default = uat.git_out(sandbox, "config", "--local", "remote.pushDefault")
        self.assertEqual(push_default, "aw-upgrade-test-blackhole")
        url = uat.git_out(
            sandbox, "config", "--local", "remote.aw-upgrade-test-blackhole.pushurl"
        )
        self.assertEqual(url, uat.BLACKHOLE_PUSH_URL)

    def test_sandbox_commits_are_not_attributed_to_the_operator(self) -> None:
        sandbox = self._sandbox_with_remote()
        uat.neutralize_git(sandbox)
        self.assertEqual(
            uat.git_out(sandbox, "config", "--local", "user.email"),
            "aw-upgrade-test@invalid.localhost",
        )
        env = uat.sandbox_env(sandbox)
        self.assertEqual(env["GIT_AUTHOR_NAME"], "aw-upgrade-test")
        self.assertEqual(env["GIT_COMMITTER_NAME"], "aw-upgrade-test")

    def test_observation_flags_a_remote_that_should_not_be_there(self) -> None:
        state = {"git": {"git": True, "remotes": ["origin"]}}
        kinds = [o["kind"] for o in uat.derive_observations(state)]
        self.assertIn("remote-present", kinds)


class SafetyInvariantThreeNoInventoryPollution(TempCase):
    """Invariant 3: the operator's real config and repo inventory are never written."""

    def test_sandbox_env_redirects_config_and_home_into_the_sandbox(self) -> None:
        sandbox = self.tmp / "box"
        sandbox.mkdir()
        env = uat.sandbox_env(sandbox)
        self.assertTrue(env["XDG_CONFIG_HOME"].startswith(str(sandbox)))
        self.assertTrue(env["AW_HOME"].startswith(str(sandbox)))

    def test_redirected_config_path_resolves_inside_the_sandbox(self) -> None:
        """Proves the redirect actually moves the file the installer WRITES.

        Asserting the env var alone would not show that ``aw`` honors it, so this runs the
        real resolver in a subprocess under the sandbox environment.
        """

        sandbox = self.tmp / "box"
        sandbox.mkdir()
        env = uat.sandbox_env(sandbox)
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "from agent_workflows import config; print(config.config_path())",
            ],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(
            proc.stdout.strip().startswith(str(sandbox)),
            f"config path {proc.stdout.strip()!r} escaped the sandbox",
        )

    def test_default_sandbox_root_is_outside_the_discovery_scan(self) -> None:
        """A sandbox under a scanned root would be discovered as a managed repo.

        The default root is a nested ``tmp/`` subdirectory, which the non-recursive
        immediate-children scan cannot reach.
        """

        from agent_workflows import discovery

        root = self.tmp / "VC"
        (root / "realrepo").mkdir(parents=True)
        init_repo(root / "realrepo")
        boxes = root / "tmp" / "aw-upgrade-tests"
        boxes.mkdir(parents=True)
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")), boxes
        )
        found = discovery.discover([root], recursive=False)
        self.assertNotIn(sandbox.resolve(), [t.resolve() for t in found.targets])

    def test_discover_sources_skips_a_git_worktree(self) -> None:
        """A worktree shares its parent's object store, so it is not a valid source.

        Regression: the harness listed its OWN worktree as a rehearsal candidate.
        """

        root = self.tmp / "VC"
        root.mkdir()
        parent = make_source_repo(root / "parent", "1.2.1", "aw")
        wt = root / "wtree"
        subprocess.run(
            ["git", "worktree", "add", "-q", "-b", "lane", str(wt)],
            cwd=str(parent),
            capture_output=True,
            text=True,
            check=False,
        )
        if not wt.exists():
            self.skipTest("git worktree unavailable")
        self.assertTrue(uat.is_worktree(wt))
        names = [s.path.name for s in uat.discover_sources([root])]
        self.assertIn("parent", names)
        self.assertNotIn("wtree", names)

    def test_default_sandbox_root_is_computed_not_hardcoded(self) -> None:
        """A literal default path would bake one machine's layout into a tracked file.

        It is also what the leak-sanitizer rejects (rule ``vc-home``), so the default is
        derived from the configured search root and overridable by environment.
        """

        source = Path(TOOL).read_text(encoding="utf-8")
        self.assertNotIn("DEFAULT_SANDBOX_ROOT = Path(", source)
        computed = uat.default_sandbox_root()
        self.assertEqual(computed.name, uat.SANDBOX_ROOT_NAME)
        self.assertEqual(computed.parent.name, "tmp")

    def test_sandbox_root_env_override_is_honored(self) -> None:
        prior = os.environ.get("AW_UPGRADE_TEST_ROOT")
        os.environ["AW_UPGRADE_TEST_ROOT"] = str(self.tmp / "custom")
        try:
            self.assertEqual(uat.default_sandbox_root(), self.tmp / "custom")
        finally:
            if prior is None:
                del os.environ["AW_UPGRADE_TEST_ROOT"]
            else:
                os.environ["AW_UPGRADE_TEST_ROOT"] = prior

    def test_relative_search_root_is_not_treated_as_a_source(self) -> None:
        """A "." search root resolves to the CHECKOUT, which must never be a source."""

        roots = uat.search_roots()
        self.assertNotIn(Path.cwd().resolve(), roots)

    def test_discover_sources_skips_sandboxes(self) -> None:
        """A rehearsal must never be run on a previous rehearsal."""

        root = self.tmp / "VC"
        root.mkdir()
        make_source_repo(root / "realrepo")
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")), root
        )
        names = [s.path.name for s in uat.discover_sources([root])]
        self.assertIn("realrepo", names)
        self.assertNotIn(sandbox.name, names)


class SafetyInvariantFourMarkerGatedDeletion(TempCase):
    """Invariant 4: ``clean`` can only ever delete our own sandboxes."""

    def test_clean_refuses_a_directory_without_the_marker(self) -> None:
        victim = make_source_repo(self.tmp / "precious", "1.2.1", "legacy")
        results = uat.clean([victim])
        self.assertEqual(results[0]["action"], "refuse")
        self.assertTrue(victim.is_dir())
        self.assertTrue((victim / "README.md").is_file())

    def test_clean_removes_a_real_sandbox(self) -> None:
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")),
            self.tmp / "boxes",
        )
        self.assertTrue(sandbox.is_dir())
        results = uat.clean([sandbox])
        self.assertEqual(results[0]["action"], "removed")
        self.assertFalse(sandbox.exists())

    def test_force_does_not_bypass_the_marker_gate(self) -> None:
        victim = make_source_repo(self.tmp / "precious", "1.2.1", "legacy")
        results = uat.clean([victim], force=True)
        self.assertEqual(results[0]["action"], "refuse")
        self.assertTrue(victim.is_dir())

    def test_clean_skips_a_nonexistent_path(self) -> None:
        results = uat.clean([self.tmp / "nope"])
        self.assertEqual(results[0]["action"], "skip")

    def test_probe_refuses_a_non_sandbox(self) -> None:
        repo = make_source_repo(self.tmp / "real", "1.2.1", "legacy")
        parser = uat.build_parser()
        args = parser.parse_args(["probe", str(repo)])
        with self.assertRaises(uat.HarnessError):
            uat.cmd_probe(args)


class SandboxCreationTests(TempCase):
    def test_marker_records_the_baseline_for_later_comparison(self) -> None:
        source = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(source), self.tmp / "boxes", strategy="full"
        )
        marker = uat.read_marker(sandbox)
        self.assertIsNotNone(marker)
        assert marker is not None
        self.assertEqual(marker["source"]["version"], "1.2.1")
        self.assertEqual(marker["source"]["layout"], "legacy")
        self.assertEqual(marker["strategy"], "full")

    def test_sandbox_name_carries_repo_and_timestamp(self) -> None:
        name = uat.sandbox_name("myrepo", "20260912-151437")
        self.assertEqual(name, "myrepo.aw-upgrade-test.20260912-151437")

    def test_create_sandbox_refuses_to_overwrite_an_existing_sandbox(self) -> None:
        source = uat.SourceRepo.inspect(make_source_repo(self.tmp / "src"))
        boxes = self.tmp / "boxes"
        stamp = "20260101-000000"
        uat.create_sandbox(source, boxes, stamp=stamp)
        with self.assertRaises(uat.HarnessError):
            uat.create_sandbox(source, boxes, stamp=stamp)

    def test_full_copy_includes_untracked_and_ignored_material(self) -> None:
        """Fidelity is the whole point of the full strategy: the installer reads these."""

        source = make_source_repo(self.tmp / "src", "1.2.1", "aw")
        (source / ".gitignore").write_text("ignored/\n", encoding="utf-8")
        (source / "ignored").mkdir()
        (source / "ignored" / "state.json").write_text("{}", encoding="utf-8")
        (source / "untracked.txt").write_text("scratch\n", encoding="utf-8")
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(source), self.tmp / "boxes", strategy="full"
        )
        self.assertTrue((sandbox / "ignored" / "state.json").is_file())
        self.assertTrue((sandbox / "untracked.txt").is_file())

    def test_clone_strategy_still_carries_the_framework_state(self) -> None:
        """A bare clone would omit gitignored framework state; the strategy compensates."""

        source = make_source_repo(self.tmp / "src", "1.2.1", "aw")
        (source / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
        state = source / ".aw" / "state"
        state.mkdir(parents=True)
        (state / "live.json").write_text("{}", encoding="utf-8")
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(source), self.tmp / "boxes", strategy="clone"
        )
        self.assertTrue((sandbox / ".aw" / "system" / "VERSION").is_file())
        self.assertTrue((sandbox / ".aw" / "state" / "live.json").is_file())

    def test_find_sandboxes_locates_by_marker_not_by_name(self) -> None:
        boxes = self.tmp / "boxes"
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")), boxes
        )
        renamed = boxes / "renamed-by-hand"
        sandbox.rename(renamed)
        found = uat.find_sandboxes([boxes])
        self.assertEqual([p.resolve() for p in found], [renamed.resolve()])


class ProbeAndObservationTests(TempCase):
    def test_probe_reports_baseline_and_current_state(self) -> None:
        source = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        sandbox = uat.create_sandbox(uat.SourceRepo.inspect(source), self.tmp / "boxes")
        state = uat.probe(sandbox)
        self.assertEqual(state["baseline_version"], "1.2.1")
        self.assertEqual(state["installed_version"], "1.2.1")
        self.assertEqual(state["layout"], "legacy")
        self.assertTrue(state["git"]["git"])

    def test_probe_is_idempotent(self) -> None:
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")),
            self.tmp / "boxes",
        )
        first = uat.probe(sandbox)
        second = uat.probe(sandbox)
        for key in ("installed_version", "layout", "legacy_files_remaining"):
            self.assertEqual(first[key], second[key])

    def test_probe_counts_legacy_leftovers(self) -> None:
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src", layout="legacy")),
            self.tmp / "boxes",
        )
        self.assertGreater(uat.probe(sandbox)["legacy_files_remaining"], 0)

    def test_observations_flag_dual_layout(self) -> None:
        kinds = [o["kind"] for o in uat.derive_observations({"layout": "dual"})]
        self.assertIn("dual-layout", kinds)

    def test_observations_flag_an_unchanged_version(self) -> None:
        kinds = [
            o["kind"]
            for o in uat.derive_observations(
                {"baseline_version": "1.2.1", "installed_version": "1.2.1"}
            )
        ]
        self.assertIn("version-unchanged", kinds)

    def test_observations_flag_leftovers_only_after_a_migrating_run(self) -> None:
        migrated = uat.derive_observations(
            {"baseline_layout": "legacy", "layout": "aw", "legacy_files_remaining": 5}
        )
        self.assertIn("legacy-leftovers", [o["kind"] for o in migrated])
        aw_native = uat.derive_observations(
            {"baseline_layout": "aw", "layout": "aw", "legacy_files_remaining": 5}
        )
        self.assertNotIn("legacy-leftovers", [o["kind"] for o in aw_native])

    def test_a_deliberately_kept_legacy_layout_is_not_reported_as_leftovers(
        self,
    ) -> None:
        """Without --to-aw the installer KEEPS the legacy tree; that is correct behavior.

        Reporting it as leftovers would flag correct behavior as a defect and teach the
        reader to ignore the observation list.
        """

        obs = uat.derive_observations(
            {
                "baseline_layout": "legacy",
                "layout": "legacy",
                "legacy_files_remaining": 331,
                "legacy_breakdown": {"skills": 92, "workflows": 158},
            }
        )
        kinds = [o["kind"] for o in obs]
        self.assertNotIn("legacy-leftovers", kinds)
        self.assertNotIn("orphaned-skills", kinds)
        self.assertIn("legacy-kept", kinds)

    def test_observations_are_empty_for_a_clean_aw_state(self) -> None:
        state = {
            "layout": "aw",
            "baseline_layout": "aw",
            "baseline_version": "1.2.1",
            "installed_version": "1.3.0",
            "legacy_files_remaining": 0,
            "manifest": {"installed_version": "1.3.0"},
            "git": {"git": True, "remotes": []},
        }
        self.assertEqual(uat.derive_observations(state), [])


class CliTests(TempCase):
    def test_default_aw_cmd_prefers_the_checkout_under_test(self) -> None:
        """A rehearsal must exercise THIS code, not whatever ``aw`` is on PATH."""

        cmd = uat.default_aw_cmd()
        self.assertEqual(cmd[0], sys.executable)
        self.assertEqual(cmd[1:], ["-m", "agent_workflows"])

    def test_json_flag_is_honored_on_either_side_of_the_subcommand(self) -> None:
        """Regression: a subparser applies its defaults OVER the top-level namespace.

        With a concrete default on the subparser's ``--json``, ``--json list`` parsed to
        False, silently emitting human output to a caller that asked for machine output.
        """

        parser = uat.build_parser()
        self.assertTrue(parser.parse_args(["--json", "list"]).json)
        self.assertTrue(parser.parse_args(["list", "--json"]).json)
        self.assertTrue(parser.parse_args(["--json", "probe", "x"]).json)
        self.assertTrue(parser.parse_args(["probe", "x", "--json"]).json)
        self.assertFalse(bool(parser.parse_args(["list"]).json))

    def test_bare_separator_is_stripped_from_passthrough_args(self) -> None:
        parser = uat.build_parser()
        args = parser.parse_args(["new", "repo", "--", "--to-aw", "--no-backup"])
        cleaned = [a for a in args.install_args if a != "--"]
        self.assertEqual(cleaned, ["--to-aw", "--no-backup"])

    def test_resolve_source_rejects_a_non_git_directory(self) -> None:
        plain = self.tmp / "plain"
        plain.mkdir()
        with self.assertRaises(uat.HarnessError):
            uat.resolve_source(str(plain))

    def test_resolve_source_accepts_an_explicit_path(self) -> None:
        repo = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        resolved = uat.resolve_source(str(repo))
        self.assertEqual(resolved.path, repo.resolve())
        self.assertEqual(resolved.version, "1.2.1")

    def test_unknown_name_is_a_clean_error_not_a_traceback(self) -> None:
        code = uat.main(["probe", str(self.tmp / "definitely-not-a-sandbox")])
        self.assertEqual(code, 2)

    def test_env_command_emits_isolating_exports(self) -> None:
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")),
            self.tmp / "boxes",
        )
        proc = subprocess.run(
            [sys.executable, str(TOOL), "env", str(sandbox)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("export XDG_CONFIG_HOME=", proc.stdout)
        self.assertIn("export AW_HOME=", proc.stdout)

    def test_clean_without_yes_is_a_dry_run(self) -> None:
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")),
            self.tmp / "boxes",
        )
        proc = subprocess.run(
            [sys.executable, str(TOOL), "clean", str(sandbox)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Would remove", proc.stdout)
        self.assertTrue(sandbox.is_dir(), "dry run must not delete")

    def test_help_runs(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Rehearse", proc.stdout)


class NoRunRehearsalTests(TempCase):
    """The copy-only path, which needs no installer and so is fast and hermetic."""

    def test_rehearse_no_run_copies_and_probes_without_installing(self) -> None:
        source = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        result = uat.rehearse(str(source), dest_root=self.tmp / "boxes", run_it=False)
        self.assertEqual(result["runs"], [])
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])
        self.assertEqual(result["state"]["installed_version"], "1.2.1")
        self.assertTrue(Path(result["sandbox"]).is_dir())

    def test_rehearse_persists_its_findings_into_the_marker(self) -> None:
        source = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        result = uat.rehearse(str(source), dest_root=self.tmp / "boxes", run_it=False)
        marker = uat.read_marker(Path(result["sandbox"]))
        assert marker is not None
        self.assertIn("rehearsal", marker)
        self.assertIn("last_probe", marker)
        self.assertEqual(marker["last_probe"]["baseline_version"], "1.2.1")


if __name__ == "__main__":
    unittest.main()

"""Behavioral tests for recursive spec resolution in agy_run.resolve_spec.

Validates that agy_run.resolve_spec resolves specifications residing in
status subdirectories (.aw/records/specs/<status>/) and legacy directories
(.agents/docs/specs/) while filtering out gitignored files, README.md, and
out-of-repo specifications, and preserving exact-path resolution and ambiguity handling.

Addresses backlog item 8jl0rx and IPD a6ootg.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_run, record_producers


def _temp_base_dir() -> Path:
    """Find a directory for temp repo whose path components contain no 'tmp' element."""
    for candidate in (Path("/dev/shm"), Path.home() / ".cache", Path.cwd()):
        if candidate.is_dir() and "tmp" not in candidate.parts:
            return candidate
    return Path(tempfile.gettempdir())


def init_repo(path: Path) -> Path:
    """Initialize a git repository for testing ignore rules."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@test.local"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Test Runner"],
        check=True,
    )
    return path


class TestAgyRunResolveSpecRecursive(unittest.TestCase):
    """Behavioral tests for agy_run.resolve_spec."""

    def setUp(self) -> None:
        self._base_tmp = tempfile.TemporaryDirectory(dir=str(_temp_base_dir()))
        self.td = Path(self._base_tmp.name)

        # Sandbox AW_HOME so out-of-repo records backend paths stay isolated
        self.aw_home = self.td / "aw_home"
        self.aw_home.mkdir(parents=True, exist_ok=True)
        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = str(self.aw_home)

        self.root = init_repo(self.td / "repo")

        # 1. Spec in status subdirectory (.aw/records/specs/approved/)
        self.approved_dir = self.root / ".aw" / "records" / "specs" / "approved"
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.approved_spec = (
            self.approved_dir / "20261001-abc123-01-abc123-test-spec.spec.md"
        )
        self.approved_spec.write_text("# Approved Spec\n", encoding="utf-8")

        # 2. Spec in legacy root (.agents/docs/specs/)
        self.legacy_dir = self.root / ".agents" / "docs" / "specs"
        self.legacy_dir.mkdir(parents=True, exist_ok=True)
        self.legacy_spec = self.legacy_dir / "20260810-01-legacy-feature.spec.md"
        self.legacy_spec.write_text("# Legacy Spec\n", encoding="utf-8")

        # 3. Specs for ambiguity testing in legacy root
        self.ambig_spec_1 = self.legacy_dir / "20260810-02-ambig1-feature.spec.md"
        self.ambig_spec_1.write_text("# Ambig 1\n", encoding="utf-8")
        self.ambig_spec_2 = self.legacy_dir / "20260810-03-ambig2-feature.spec.md"
        self.ambig_spec_2.write_text("# Ambig 2\n", encoding="utf-8")

        # 4a. Gitignored spec via untracked directory
        self.untracked_dir = self.root / ".aw" / "records" / "specs" / "untracked"
        self.untracked_dir.mkdir(parents=True, exist_ok=True)
        self.untracked_spec = (
            self.untracked_dir / "20261001-untr01-01-untr01-untracked.spec.md"
        )
        self.untracked_spec.write_text("# Untracked\n", encoding="utf-8")

        # 4b. Gitignored spec via .git/info/exclude (path has NO 'untracked' component)
        self.scratch_dir = self.root / ".aw" / "records" / "specs" / "scratch"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)
        self.scratch_spec = (
            self.scratch_dir / "20261001-scrt01-01-scrt01-scratch.spec.md"
        )
        self.scratch_spec.write_text("# Scratch\n", encoding="utf-8")
        exclude_file = self.root / ".git" / "info" / "exclude"
        exclude_file.write_text(".aw/records/specs/scratch/\n", encoding="utf-8")

        # 5. README.md at specs root
        self.specs_readme = self.root / ".aw" / "records" / "specs" / "README.md"
        self.specs_readme.write_text("# Specs Readme\n", encoding="utf-8")

        # 6. Out-of-repo records backend spec
        read_paths = record_producers.resolve_record_read_paths(
            "specs", target_repo=str(self.root)
        )
        self.out_specs_dir = read_paths[0]
        self.out_specs_dir.mkdir(parents=True, exist_ok=True)
        self.out_repo_spec = (
            self.out_specs_dir / "20261001-out001-01-out001-outside.spec.md"
        )
        self.out_repo_spec.write_text("# Outside Spec\n", encoding="utf-8")

    def tearDown(self) -> None:
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        self._base_tmp.cleanup()

    def test_01_resolve_spec_in_status_subdirectory_by_bare_id6(self) -> None:
        """(1) A spec planted in a status subdirectory resolves by bare id6."""
        resolved = agy_run.resolve_spec(self.root, "abc123")
        self.assertEqual(resolved, self.approved_spec.resolve())

    def test_02_resolve_spec_in_status_subdirectory_by_bare_filename(self) -> None:
        """(2) A spec planted in a status subdirectory resolves by bare filename."""
        resolved = agy_run.resolve_spec(
            self.root, "20261001-abc123-01-abc123-test-spec.spec.md"
        )
        self.assertEqual(resolved, self.approved_spec.resolve())

    def test_03_resolve_spec_in_legacy_root_by_bare_filename(self) -> None:
        """(3) A spec planted in legacy .agents/docs/specs still resolves."""
        resolved = agy_run.resolve_spec(self.root, "20260810-01-legacy-feature.spec.md")
        self.assertEqual(resolved, self.legacy_spec.resolve())

    def test_04a_gitignored_spec_in_untracked_dir_not_resolved(self) -> None:
        """(4a) Specs under untracked directory are not resolvable."""
        with self.assertRaises(agy_run.ScriptError) as ctx:
            agy_run.resolve_spec(self.root, "untr01")
        self.assertIn("No specification matching 'untr01' found.", str(ctx.exception))

    def test_04b_gitignored_spec_by_git_exclude_not_resolved(self) -> None:
        """(4b) Specs ignored by git exclude rule (no 'untracked' component) are not resolvable."""
        self.assertNotIn("untracked", self.scratch_spec.parts)
        res = subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "check-ignore",
                "-v",
                str(self.scratch_spec.relative_to(self.root)),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn(".git/info/exclude", res.stdout)
        with self.assertRaises(agy_run.ScriptError) as ctx:
            agy_run.resolve_spec(self.root, "scrt01")
        self.assertIn("No specification matching 'scrt01' found.", str(ctx.exception))

    def test_05_specs_readme_not_resolvable_as_spec(self) -> None:
        """(5) README.md at specs root is not resolvable as a specification."""
        with self.assertRaises(agy_run.ScriptError) as ctx:
            agy_run.resolve_spec(self.root, "README")
        self.assertIn("No specification matching 'README' found.", str(ctx.exception))

    def test_06_out_of_repo_backend_spec_not_resolved(self) -> None:
        """(6) Out-of-repo records backend specs are excluded and raise ScriptError."""
        self.assertFalse(self.out_repo_spec.is_relative_to(self.root))
        with self.assertRaises(agy_run.ScriptError) as ctx:
            agy_run.resolve_spec(self.root, "out001")
        self.assertIn("No specification matching 'out001' found.", str(ctx.exception))

    def test_07_ambiguous_selector_raises_with_candidates(self) -> None:
        """Ambiguous selector raises ScriptError listing candidates."""
        with self.assertRaises(agy_run.ScriptError) as ctx:
            agy_run.resolve_spec(self.root, "ambig")
        msg = str(ctx.exception)
        self.assertIn("Specification reference 'ambig' is ambiguous:", msg)
        self.assertIn("20260810-02-ambig1-feature.spec.md", msg)
        self.assertIn("20260810-03-ambig2-feature.spec.md", msg)

    def test_08_exact_existing_path_resolves(self) -> None:
        """Exact existing relative path resolves directly."""
        rel_path = str(self.approved_spec.relative_to(self.root))
        resolved = agy_run.resolve_spec(self.root, rel_path)
        self.assertEqual(resolved, self.approved_spec.resolve())

"""Behavioral tests for recursive IPD resolution in agy_run.resolve_ipd.

Validates that agy_run.resolve_ipd resolves plans residing in
shard subdirectories (.aw/records/plans/<state>/YYYYMM/) and legacy directories
(.agents/plans/<state>/) while filtering out gitignored files, README.md,
and preserving exact-path resolution, state validation, and ambiguity handling.

Addresses backlog item mlcbk9 and IPD m734rl.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_run


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


class TestAgyRunResolveIpdRecursive(unittest.TestCase):
    """Behavioral tests for agy_run.resolve_ipd."""

    def setUp(self) -> None:
        self._base_tmp = tempfile.TemporaryDirectory(dir=str(_temp_base_dir()))
        self.td = Path(self._base_tmp.name)

        # Sandbox AW_HOME so out-of-repo records backend paths stay isolated
        self.aw_home = self.td / "aw_home"
        self.aw_home.mkdir(parents=True, exist_ok=True)
        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = str(self.aw_home)

        self.root = init_repo(self.td / "repo")

        # Exclude rule written BEFORE any resolver call
        exclude_file = self.root / ".git" / "info" / "exclude"
        exclude_file.write_text("scratch/\n", encoding="utf-8")

        # 1, 2, 3, 7, 8b: Sharded plan in .aw/records/plans/executed/202609/
        self.sharded_plan = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "202609"
            / "20260901-set-01-ab12cd-thing.ipd.md"
        )
        self.sharded_plan.parent.mkdir(parents=True, exist_ok=True)
        self.sharded_plan.write_text(
            "# Plan ab12cd\n- Id: ab12cd\n- Set: set (Set)\n- Status: executed\n",
            encoding="utf-8",
        )

        # 4: Flat legacy plan in .agents/plans/pending/
        self.legacy_plan = (
            self.root
            / ".agents"
            / "plans"
            / "pending"
            / "20260701-leg001-01-leg001-legacy.ipd.md"
        )
        self.legacy_plan.parent.mkdir(parents=True, exist_ok=True)
        self.legacy_plan.write_text(
            "# Plan leg001\n- Id: leg001\n- Set: leg001 (Legacy)\n- Status: pending\n",
            encoding="utf-8",
        )

        # 5a: Untracked plan under .aw/records/plans/pending/untracked/
        self.untracked_plan = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "untracked"
            / "20261001-untr01-01-untr01-untracked.ipd.md"
        )
        self.untracked_plan.parent.mkdir(parents=True, exist_ok=True)
        self.untracked_plan.write_text(
            "# Plan untr01\n- Id: untr01\n- Set: untr01 (Untracked)\n- Status: pending\n",
            encoding="utf-8",
        )

        # 5b: Scratch plan ignored only by .git/info/exclude
        self.scratch_plan = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "scratch"
            / "20261001-scrt01-01-scrt01-scratch.ipd.md"
        )
        self.scratch_plan.parent.mkdir(parents=True, exist_ok=True)
        self.scratch_plan.write_text(
            "# Plan scrt01\n- Id: scrt01\n- Set: scrt01 (Scratch)\n- Status: pending\n",
            encoding="utf-8",
        )

        # 6: README.md in pending/
        self.pending_readme = (
            self.root / ".aw" / "records" / "plans" / "pending" / "README.md"
        )
        self.pending_readme.parent.mkdir(parents=True, exist_ok=True)
        self.pending_readme.write_text("# Pending Plans\n", encoding="utf-8")

        # 8a: Duplicate plans sharing id6 dd44ee across executed/ and executed/202609/
        self.dup_plan_top = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260801-set-02-dd44ee-other.ipd.md"
        )
        self.dup_plan_top.parent.mkdir(parents=True, exist_ok=True)
        self.dup_plan_top.write_text(
            "# Plan dd44ee top\n- Id: dd44ee\n- Set: set (Set)\n- Status: executed\n",
            encoding="utf-8",
        )
        self.dup_plan_shard = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "202609"
            / "20260901-set-03-dd44ee-dup.ipd.md"
        )
        self.dup_plan_shard.write_text(
            "# Plan dd44ee shard\n- Id: dd44ee\n- Set: set (Set)\n- Status: executed\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        self._base_tmp.cleanup()

    def test_01_resolve_sharded_plan_by_bare_id6(self) -> None:
        """(1) A plan in .aw/records/plans/executed/202609/ resolves by bare id6."""
        resolved = agy_run.resolve_ipd(self.root, "ab12cd", ("executed",))
        self.assertEqual(resolved, self.sharded_plan.resolve())

    def test_02_resolve_sharded_plan_by_bare_filename(self) -> None:
        """(2) The same plan resolves by bare filename."""
        resolved = agy_run.resolve_ipd(
            self.root, "20260901-set-01-ab12cd-thing.ipd.md", ("executed",)
        )
        self.assertEqual(resolved, self.sharded_plan.resolve())

    def test_03_sharded_plan_not_returned_for_wrong_state(self) -> None:
        """(3) The same plan is NOT returned for states ('pending',)."""
        with self.assertRaises(agy_run.ScriptError) as ctx:
            agy_run.resolve_ipd(self.root, "ab12cd", ("pending",))
        self.assertIn(
            "No IPD matching 'ab12cd' found in plan states: pending.",
            str(ctx.exception),
        )

    def test_04_flat_legacy_plan_resolves_by_id6(self) -> None:
        """(4) A flat .agents/plans/pending/ legacy plan still resolves by id6."""
        resolved = agy_run.resolve_ipd(self.root, "leg001", ("pending",))
        self.assertEqual(resolved, self.legacy_plan.resolve())

    def test_05a_untracked_plan_not_resolvable(self) -> None:
        """(5a) A plan under .aw/records/plans/pending/untracked/ is NOT resolvable."""
        with self.assertRaises(agy_run.ScriptError) as ctx:
            agy_run.resolve_ipd(self.root, "untr01", ("pending",))
        self.assertIn(
            "No IPD matching 'untr01' found in plan states: pending.",
            str(ctx.exception),
        )

    def test_05b_scratch_plan_ignored_by_exclude_not_resolvable(self) -> None:
        """(5b) A plan under .aw/records/plans/pending/scratch/ ignored by .git/info/exclude is NOT resolvable."""
        with self.assertRaises(agy_run.ScriptError) as ctx:
            agy_run.resolve_ipd(self.root, "scrt01", ("pending",))
        self.assertIn(
            "No IPD matching 'scrt01' found in plan states: pending.",
            str(ctx.exception),
        )

    def test_06_readme_not_resolvable_as_ipd(self) -> None:
        """(6) README.md in pending/ is NOT resolvable as an IPD by bare name README.md."""
        with self.assertRaises(agy_run.ScriptError) as ctx:
            agy_run.resolve_ipd(self.root, "README.md", ("pending",))
        self.assertIn(
            "No IPD matching 'README.md' found in plan states: pending.",
            str(ctx.exception),
        )

    def test_07_positional_audit_resolves_sharded_plan(self) -> None:
        """(7) Positional resolve_mode_and_target returns mode 'ipd' with repo-relative sharded path."""
        mode, target, _ = agy_run.resolve_mode_and_target(
            self.root, agy_run.parse_args(["--audit-only", "ab12cd"])
        )
        self.assertEqual(mode, "ipd")
        rel_path = self.sharded_plan.relative_to(self.root).as_posix()
        self.assertEqual(target, rel_path)

    def test_08a_duplicate_id6_across_shard_raises_ambiguous(self) -> None:
        """(8a) Two plans sharing id6 dd44ee across executed/ and executed/202609/ raise is ambiguous."""
        with self.assertRaises(agy_run.ScriptError) as ctx:
            agy_run.resolve_ipd(self.root, "dd44ee", ("executed",))
        msg = str(ctx.exception)
        self.assertIn("IPD reference 'dd44ee' is ambiguous:", msg)
        rel1 = str(self.dup_plan_top.relative_to(self.root))
        rel2 = str(self.dup_plan_shard.relative_to(self.root))
        self.assertIn(rel1, msg)
        self.assertIn(rel2, msg)

    def test_08b_preserved_exact_path_and_disallowed_state(self) -> None:
        """(8b) Preserved semantics: exact existing path resolves; disallowed state raises."""
        rel_path = str(self.sharded_plan.relative_to(self.root))
        resolved = agy_run.resolve_ipd(self.root, rel_path, ("executed",))
        self.assertEqual(resolved, self.sharded_plan.resolve())

        with self.assertRaises(agy_run.ScriptError) as ctx:
            agy_run.resolve_ipd(self.root, rel_path, ("pending",))
        self.assertIn("is not in an allowed plan state: pending.", str(ctx.exception))

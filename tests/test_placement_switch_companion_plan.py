"""Companion-pair census and blockers for the placement-switch planner (IPD xc8nae / Set cmpreloc).

Every test installs a FRESH scratch target through the real installer
subprocess, then calls ``placement_switch.plan_placement_switch`` and asserts
on the returned plan and on the filesystem being left untouched.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Optional, Tuple

import pytest

from agent_workflows.install_wizard import ProjectPolicy, get_preset_defaults
from agent_workflows.placement_switch import SwitchPlan, plan_placement_switch
from agent_workflows.project_schema import Preset

pytestmark = pytest.mark.slow

COMP = Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value
PRIV = Preset.PRIVATE_TARGET.value
CLEAN = Preset.COMPLETELY_CLEAN_TARGET.value
LOCAL = Preset.LOCAL_ONLY.value

REPO_ROOT = str(Path(__file__).resolve().parent.parent)
RECORD_REL = "backlog/open/x.backlog.md"


class _Scratch:
    """One scratch world: HOME, AW_HOME, XDG_CONFIG_HOME, a target repo, an optional companion."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.aw_home = root / "aw_home"
        self.aw_home.mkdir()
        (root / "xdg").mkdir()
        self.repo = root / "repo"
        self.companion: Optional[Path] = None
        self.env: Dict[str, str] = dict(
            os.environ,
            PYTHONPATH=f"{REPO_ROOT}:{os.environ.get('PYTHONPATH', '')}",
            AW_NO_REEXEC="1",
            HOME=str(root),
            AW_HOME=str(self.aw_home),
            XDG_CONFIG_HOME=str(root / "xdg"),
            GIT_AUTHOR_NAME="Test User",
            GIT_AUTHOR_EMAIL="test@example.com",
            GIT_COMMITTER_NAME="Test User",
            GIT_COMMITTER_EMAIL="test@example.com",
        )

    def git(self, cwd: Path, *args: str, check: bool = True) -> str:
        res = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            env=self.env,
            capture_output=True,
            text=True,
        )
        if check and res.returncode != 0:
            raise AssertionError(f"git {args} failed: {res.stdout}\n{res.stderr}")
        return res.stdout

    def init_repo(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self.git(path, "init", "-q", "-b", "main")
        self.git(path, "commit", "-q", "--allow-empty", "-m", "init")

    def install(self, preset: str, companion: Optional[Path] = None) -> None:
        self.init_repo(self.repo)
        cmd = [
            sys.executable,
            "-m",
            "agent_workflows",
            "install",
            str(self.repo),
            "--preset",
            preset,
            "-y",
            "--no-interactive",
        ]
        if preset == COMP:
            self.companion = companion or (self.root / "comp")
            cmd += ["--companion-dir", str(self.companion)]
        res = subprocess.run(cmd, env=self.env, capture_output=True, text=True)
        if res.returncode != 0:
            raise AssertionError(f"installer failed: {res.stdout}\n{res.stderr}")

    def commit_companion(self, message: str = "companion") -> None:
        assert self.companion is not None
        self.git(self.companion, "add", "-A")
        self.git(self.companion, "commit", "-q", "-m", message)

    def records_root(self, preset: str) -> Path:
        if preset == COMP:
            assert self.companion is not None
            return self.companion / "records"
        if preset == PRIV:
            return self.repo / ".aw" / "records"
        # Home presets: the single project directory under AW_HOME.
        projects = sorted((self.aw_home / "projects").iterdir())
        return projects[0] / "records"

    def add_user_record(self, preset: str) -> Path:
        """Write records/backlog/open/x.backlog.md and commit it where a git repo owns it."""
        rec = self.records_root(preset) / RECORD_REL
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text("# Backlog item x\n", encoding="utf-8")
        if preset == COMP:
            self.commit_companion("add user record")
        elif preset == PRIV:
            self.git(self.repo, "add", "--", str(rec))
            self.git(self.repo, "commit", "-q", "-m", "add user record")
        return rec

    def policy(
        self, preset: str, companion_dir: Optional[Path] = None
    ) -> ProjectPolicy:
        _pls, _gps, dm, rb, ds = get_preset_defaults(preset)
        return ProjectPolicy(
            preset=preset,
            role="target",
            delivery_mode=dm,
            records_backend=rb,
            durability_state=ds,
            aw_home=str(self.aw_home),
            companion_dir=str(companion_dir) if companion_dir is not None else None,
        )

    def plan(self, preset: str, companion_dir: Optional[Path] = None) -> SwitchPlan:
        return plan_placement_switch(
            self.repo, self.policy(preset, companion_dir), aw_home=self.aw_home
        )


def _snapshot(*roots: Optional[Path]) -> Dict[str, Tuple[int, int]]:
    snap: Dict[str, Tuple[int, int]] = {}
    for root in roots:
        if root is None or not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            for name in dirnames + filenames:
                p = Path(dirpath) / name
                st = p.lstat()
                snap[str(p)] = (st.st_mtime_ns, st.st_size)
        st = root.lstat()
        snap[str(root)] = (st.st_mtime_ns, st.st_size)
    return snap


def _record_item(plan: SwitchPlan):
    hits = [
        it
        for it in plan.items
        if it.item_class == "records" and it.source.as_posix().endswith(RECORD_REL)
    ]
    assert len(hits) == 1, [str(it.source) for it in plan.items]
    return hits[0]


class TestCompanionCensus(unittest.TestCase):
    """The six companion pairs: direction, attach/detach, retire side, per-item repositories."""

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.s = _Scratch(Path(self._td.name))

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_pair_a_private_target_to_companion(self) -> None:
        s = self.s
        s.install(PRIV)
        rec = s.add_user_record(PRIV)
        newcomp = s.root / "newcomp"
        plan = s.plan(COMP, newcomp)

        self.assertEqual(plan.direction, "in-place")
        self.assertEqual(plan.companion_action, "attach")
        self.assertIsNone(plan.retire_side)
        self.assertEqual(plan.config_retrack, "untrack")
        self.assertEqual(plan.companion_dir, newcomp)
        self.assertTrue(plan.companion_create)
        self.assertEqual(plan.blockers, ["companion-unsupported"])

        it = _record_item(plan)
        self.assertEqual(it.kind, "move")
        self.assertEqual(it.source, rec)
        self.assertEqual(it.destination, newcomp / "records" / RECORD_REL)
        self.assertEqual(it.source_git, "target")
        self.assertEqual(it.dest_git, "companion")
        self.assertTrue(it.tracked)

        proj = [i for i in plan.items if i.item_class == "config_project"]
        self.assertEqual(len(proj), 1)
        self.assertEqual(proj[0].kind, "rewrite")
        self.assertEqual(proj[0].source, proj[0].destination)
        classes = {i.item_class for i in plan.items}
        self.assertNotIn("state_durable", classes)
        self.assertNotIn("state_runtime", classes)

        tracked_moves = [
            i
            for i in plan.items
            if i.item_class == "records" and i.kind == "move" and i.tracked
        ]
        self.assertEqual(
            plan.warnings.get("records-leave-target-history"), len(tracked_moves)
        )
        self.assertEqual(plan.warnings.get("config-becomes-untracked"), 1)
        self.assertNotIn("companion-left-in-place", plan.warnings)
        # The plan round-trips through its JSON form with the new keys.
        d = plan.to_dict()
        self.assertEqual(SwitchPlan.from_dict(json.loads(json.dumps(d))).to_dict(), d)

    def test_pair_b_companion_to_private_target(self) -> None:
        s = self.s
        s.install(COMP)
        s.commit_companion()
        rec = s.add_user_record(COMP)
        plan = s.plan(PRIV)

        self.assertEqual(plan.direction, "in-place")
        self.assertEqual(plan.companion_action, "detach")
        self.assertIsNone(plan.retire_side)
        self.assertEqual(plan.config_retrack, "track")
        self.assertFalse(plan.companion_create)
        self.assertEqual(plan.blockers, ["companion-unsupported"])

        it = _record_item(plan)
        self.assertEqual(it.source, rec)
        self.assertEqual(it.destination, s.repo / ".aw" / "records" / RECORD_REL)
        self.assertEqual(it.source_git, "companion")
        self.assertEqual(it.dest_git, "target")
        self.assertTrue(it.tracked)

        attach = [i for i in plan.items if i.source.name == "companion_attachment.json"]
        self.assertEqual(len(attach), 1)
        self.assertEqual(attach[0].kind, "discard")
        self.assertEqual(plan.warnings.get("companion-left-in-place"), 1)

    def _assert_pair_c(self, new_preset: str) -> None:
        s = self.s
        s.install(COMP)
        s.commit_companion()
        rec = s.add_user_record(COMP)
        plan = s.plan(new_preset)

        self.assertEqual(plan.direction, "to-home")
        self.assertEqual(plan.companion_action, "detach")
        self.assertEqual(plan.retire_side, "target")
        self.assertIsNone(plan.config_retrack)
        self.assertEqual(plan.blockers, ["companion-unsupported"])

        it = _record_item(plan)
        self.assertEqual(it.source, rec)
        self.assertEqual(
            it.destination,
            s.aw_home / "projects" / plan.project_id / "records" / RECORD_REL,
        )
        self.assertEqual(it.source_git, "companion")
        self.assertIsNone(it.dest_git)
        self.assertTrue(it.tracked)

        attach = [i for i in plan.items if i.source.name == "companion_attachment.json"]
        self.assertEqual([a.kind for a in attach], ["discard"])
        install_json = [i for i in plan.items if i.source.name == "install.json"]
        self.assertEqual([i.kind for i in install_json], ["move"])
        self.assertEqual(plan.warnings.get("companion-left-in-place"), 1)

    def test_pair_c_companion_to_completely_clean_target(self) -> None:
        self._assert_pair_c(CLEAN)

    def test_pair_c_companion_to_local_only(self) -> None:
        self._assert_pair_c(LOCAL)

    def _assert_pair_d(self, old_preset: str) -> None:
        s = self.s
        s.install(old_preset)
        rec = s.add_user_record(old_preset)
        newcomp = s.root / "newcomp"
        plan = s.plan(COMP, newcomp)

        self.assertEqual(plan.direction, "to-target")
        self.assertEqual(plan.companion_action, "attach")
        self.assertEqual(plan.retire_side, "home")
        self.assertIsNone(plan.config_retrack)
        self.assertTrue(plan.companion_create)
        self.assertEqual(plan.blockers, ["companion-unsupported"])

        it = _record_item(plan)
        self.assertEqual(it.source, rec)
        self.assertEqual(it.destination, newcomp / "records" / RECORD_REL)
        self.assertIsNone(it.source_git)
        self.assertEqual(it.dest_git, "companion")
        self.assertFalse(it.tracked)

        proj = [i for i in plan.items if i.item_class == "config_project"]
        self.assertEqual(len(proj), 1)
        self.assertEqual(
            proj[0].destination, s.repo / ".aw" / "config" / "project.json"
        )
        self.assertIsNone(proj[0].dest_git)

    def test_pair_d_completely_clean_target_to_companion(self) -> None:
        self._assert_pair_d(CLEAN)

    def test_pair_d_local_only_to_companion(self) -> None:
        self._assert_pair_d(LOCAL)

    def test_companion_create_false_for_existing_companion_repo(self) -> None:
        s = self.s
        s.install(PRIV)
        existing = s.root / "existing"
        s.init_repo(existing)
        plan = s.plan(COMP, existing)
        self.assertFalse(plan.companion_create)
        self.assertEqual(plan.blockers, ["companion-unsupported"])


class TestCompanionBlockers(unittest.TestCase):
    """Each companion blocker fires on exactly its minimal condition."""

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.s = _Scratch(Path(self._td.name))

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_companion_not_git_plain_directory(self) -> None:
        s = self.s
        s.install(PRIV)
        plain = s.root / "plain"
        plain.mkdir()
        plan = s.plan(COMP, plain)
        self.assertEqual(
            sorted(plan.blockers), ["companion-not-git", "companion-unsupported"]
        )
        self.assertTrue(plan.items)

    def test_companion_not_git_nested_in_unrelated_repo(self) -> None:
        s = self.s
        s.install(PRIV)
        other = s.root / "other"
        s.init_repo(other)
        nested = other / "comp"
        nested.mkdir()
        plan = s.plan(COMP, nested)
        self.assertEqual(
            sorted(plan.blockers), ["companion-not-git", "companion-unsupported"]
        )

    def test_companion_dirty(self) -> None:
        s = self.s
        s.install(PRIV)
        existing = s.root / "existing"
        s.init_repo(existing)
        (existing / "stray.txt").write_text("x\n", encoding="utf-8")
        plan = s.plan(COMP, existing)
        self.assertEqual(
            sorted(plan.blockers), ["companion-dirty", "companion-unsupported"]
        )
        self.assertIn("commit or clean", plan.blocker_messages["companion-dirty"])

    def test_companion_unmerged(self) -> None:
        s = self.s
        s.install(PRIV)
        existing = s.root / "existing"
        s.init_repo(existing)
        f = existing / "f.txt"
        f.write_text("base\n", encoding="utf-8")
        s.git(existing, "add", "f.txt")
        s.git(existing, "commit", "-q", "-m", "base")
        s.git(existing, "checkout", "-q", "-b", "side")
        f.write_text("side\n", encoding="utf-8")
        s.git(existing, "commit", "-q", "-am", "side")
        s.git(existing, "checkout", "-q", "main")
        f.write_text("main\n", encoding="utf-8")
        s.git(existing, "commit", "-q", "-am", "main")
        s.git(existing, "merge", "side", check=False)
        plan = s.plan(COMP, existing)
        self.assertIn("companion-unmerged", plan.blockers)
        self.assertIn("companion-dirty", plan.blockers)

    def test_destination_not_empty_in_attach_companion(self) -> None:
        s = self.s
        s.install(PRIV)
        existing = s.root / "existing"
        s.init_repo(existing)
        y = existing / "records" / "backlog" / "open" / "y.backlog.md"
        y.parent.mkdir(parents=True)
        y.write_text("# another project's record\n", encoding="utf-8")
        s.git(existing, "add", "-A")
        s.git(existing, "commit", "-q", "-m", "y")
        plan = s.plan(COMP, existing)
        self.assertEqual(
            sorted(plan.blockers), ["companion-unsupported", "destination-not-empty"]
        )

    def test_companion_preflight_identity_conflict(self) -> None:
        s = self.s
        s.install(PRIV)
        existing = s.root / "existing"
        s.init_repo(existing)
        ident = existing / ".aw" / "companion_identity.json"
        ident.parent.mkdir(parents=True)
        ident.write_text(
            json.dumps({"project_id": "someone-else-000000"}), encoding="utf-8"
        )
        s.git(existing, "add", "-A")
        s.git(existing, "commit", "-q", "-m", "ident")
        plan = s.plan(COMP, existing)
        self.assertEqual(
            sorted(plan.blockers), ["companion-preflight", "companion-unsupported"]
        )
        self.assertIn(
            "someone-else-000000", plan.blocker_messages["companion-preflight"]
        )

    def test_companion_preflight_nonexistent_nested_in_target(self) -> None:
        s = self.s
        s.install(PRIV)
        nested = s.repo / "nested-comp"
        plan = s.plan(COMP, nested)
        self.assertIn("companion-preflight", plan.blockers)
        self.assertFalse(nested.exists())

    def test_companion_to_companion(self) -> None:
        s = self.s
        s.install(COMP)
        s.commit_companion()
        plan = s.plan(COMP, s.root / "elsewhere")
        self.assertIn("companion-to-companion", plan.blockers)
        self.assertNotIn("not-a-placement-switch", plan.blockers)
        self.assertIn(
            "aw storage move", plan.blocker_messages["companion-to-companion"]
        )

    def test_same_companion_dir_is_not_a_placement_switch(self) -> None:
        s = self.s
        s.install(COMP)
        s.commit_companion()
        plan = s.plan(COMP, s.companion)
        self.assertEqual(plan.blockers, ["not-a-placement-switch"])

    def test_fresh_companion_install_is_not_dirty_for_detach(self) -> None:
        s = self.s
        s.install(COMP)
        s.commit_companion()
        for new in (PRIV, LOCAL):
            plan = s.plan(new)
            self.assertNotIn("dirty-aw-tree", plan.blockers, new)
        (s.repo / ".aw" / "stray.txt").write_text("x\n", encoding="utf-8")
        for new in (PRIV, LOCAL):
            plan = s.plan(new)
            self.assertIn("dirty-aw-tree", plan.blockers, new)

    def test_cfgreloc_pairs_have_no_companion_fields(self) -> None:
        s = self.s
        s.install(PRIV)
        for new in (LOCAL, CLEAN):
            plan = s.plan(new)
            self.assertNotIn("companion-unsupported", plan.blockers, new)
            self.assertIsNone(plan.companion_action)
            self.assertIsNone(plan.companion_dir)
            self.assertIsNone(plan.config_retrack)
            self.assertEqual(plan.direction, "to-home")
            it = [i for i in plan.items if i.item_class == "records"][0]
            self.assertEqual(it.source_git, "target")
            self.assertIsNone(it.dest_git)

    def test_cfgreloc_to_target_has_no_companion_unsupported(self) -> None:
        s = self.s
        s.install(LOCAL)
        plan = s.plan(PRIV)
        self.assertEqual(plan.blockers, [])
        self.assertIsNone(plan.companion_action)
        it = [i for i in plan.items if i.item_class == "records"][0]
        self.assertIsNone(it.source_git)
        self.assertEqual(it.dest_git, "target")


class TestCompanionPlannerPurity(unittest.TestCase):
    """Planning a companion switch writes nothing in the target, the companion, or AW_HOME."""

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.s = _Scratch(Path(self._td.name))

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_detach_plan_is_pure(self) -> None:
        s = self.s
        s.install(COMP)
        s.commit_companion()
        s.add_user_record(COMP)
        before = _snapshot(s.repo, s.companion, s.aw_home)
        for new in (PRIV, CLEAN):
            s.plan(new)
        self.assertEqual(_snapshot(s.repo, s.companion, s.aw_home), before)

    def test_attach_plan_is_pure(self) -> None:
        s = self.s
        s.install(PRIV)
        s.add_user_record(PRIV)
        existing = s.root / "existing"
        s.init_repo(existing)
        missing = s.root / "missing"
        before = _snapshot(s.repo, existing, s.aw_home)
        s.plan(COMP, existing)
        s.plan(COMP, missing)
        self.assertEqual(_snapshot(s.repo, existing, s.aw_home), before)
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()

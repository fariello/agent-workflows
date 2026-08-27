"""Installer skill-package emission tests (installerskill Set, child kvfsak).

Covers wiring `host_adapters.AdapterBundle.skill_files()` into the installer run path
(`install_into_repo` -> `install_all`), the framework-namespace / prune-scan extensions
for the skills directory, idempotent re-install, orphan pruning, and manifest-driven
uninstall. End-to-end tests install into throwaway git repos and assert filesystem state.
Stdlib unittest only.

These verify the Set's completion criteria:
  - a fresh install emits the skill-package files under the resolved skills dir;
  - a re-install is a no-op (all `[already current]`, empty install-diff);
  - an orphaned skill file (tracked or untracked) is pruned;
  - manifest-driven `uninstall_repo` removes exactly the emitted skill files;
  - NO adapter-metadata files are emitted (OQ-02 Option A: skill packages only).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pytest

from tests.support import SOURCE_WORKFLOWS, git, init_repo

from agent_workflows import engine as INS
from agent_workflows import host_adapters as HA
from agent_workflows.host_capability_registry import HostCapabilityRegistry

# End-to-end install suite is slow (real git repos); excluded from the fast default run.
pytestmark = pytest.mark.slow


class SkillsDirResolverTests(unittest.TestCase):
    """E-01/V-01: the layout-aware skills-dir resolver and its threading into the generators."""

    def test_resolver_returns_shared_host_dir_for_both_layouts(self):
        # OQ-03 resolution: skills are host-consumption artifacts (like the command shims),
        # emitted to the shared `.agents/skills` dir for BOTH layouts, not relocated under
        # `.aw/system/` in the aw layout.
        self.assertEqual(INS.resolve_skills_dir("aw"), ".agents/skills")
        self.assertEqual(INS.resolve_skills_dir("legacy"), ".agents/skills")
        self.assertEqual(INS.resolve_skills_dir("aw"), INS.SKILLS_DIR)

    def test_resolved_skill_dir_is_threaded_into_generators(self):
        # The resolved skill_dir must drive the generated package paths (not the module
        # default), for both layouts.
        workflows = INS.parse_manifest(SOURCE_WORKFLOWS)
        for layout in ("aw", "legacy"):
            skill_dir = INS.resolve_skills_dir(layout)
            bundle = HA.generate_adapter_bundle(
                workflows,
                SOURCE_WORKFLOWS,
                HostCapabilityRegistry(),
                target_layout=layout,
                skill_dir=skill_dir,
            )
            files = bundle.skill_files()
            self.assertTrue(files, "expected at least one generated skill file")
            for path in files:
                self.assertTrue(
                    path.startswith(skill_dir + "/"),
                    f"skill path {path} not under resolved skill_dir {skill_dir}",
                )


class NamespaceAndCollectTests(unittest.TestCase):
    """E-03/V-03 and E-06/V-06: namespace recognition + prune-scan discovery."""

    def test_skill_path_is_in_framework_namespace(self):
        # E-03: a path under the resolved skills dir is adoptable/prune-safe.
        self.assertTrue(
            INS.in_framework_namespace(".agents/skills/release-review/SKILL.md")
        )
        self.assertTrue(
            INS.in_framework_namespace(
                ".agents/skills/release-review/scripts/verify_digest.py"
            )
        )
        # A non-framework path is still rejected (the predicate did not go broad).
        self.assertFalse(INS.in_framework_namespace("src/app.py"))
        self.assertFalse(INS.in_framework_namespace(".agents/other/thing.md"))

    def test_collect_target_framework_files_includes_skill_files(self):
        # E-06: an existing skill file under the resolved dir is discoverable by prune.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            skill_file = repo / ".agents/skills/demo/SKILL.md"
            skill_file.parent.mkdir(parents=True)
            skill_file.write_text("---\nname: demo\n---\n", encoding="utf-8")
            present = INS.collect_target_framework_files(repo, target_layout="aw")
            self.assertIn(".agents/skills/demo/SKILL.md", present)


class SkillEmissionInstallTests(unittest.TestCase):
    """E-04/V-04, E-05/V-05, E-07/V-07: fresh install, idempotency, prune, uninstall."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = SOURCE_WORKFLOWS

    def tearDown(self):
        self._tmp.cleanup()

    def _skill_files_on_disk(self, repo: Path) -> list[str]:
        skills = repo / ".agents" / "skills"
        if not skills.is_dir():
            return []
        return sorted(
            p.relative_to(repo).as_posix() for p in skills.rglob("*") if p.is_file()
        )

    def test_fresh_install_emits_skill_packages_and_records_manifest(self):
        # E-04/V-04: a fresh install writes SKILL.md + resource files under the resolved
        # skills dir, and each is recorded in the ownership manifest.
        import json

        repo = init_repo(self.base / "fresh")
        res = INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        self.assertEqual(res["target_layout"], "aw")

        on_disk = self._skill_files_on_disk(repo)
        self.assertTrue(on_disk, "no skill files emitted on a fresh install")
        skill_mds = [p for p in on_disk if p.endswith("/SKILL.md")]
        self.assertTrue(skill_mds, "no SKILL.md router files emitted")
        # Each SKILL.md sits under .agents/skills/<name>/ and carries package resources.
        for md in skill_mds:
            name = md[len(".agents/skills/") : -len("/SKILL.md")]
            self.assertIn(f".agents/skills/{name}/reference/canonical-body.md", on_disk)
            self.assertIn(f".agents/skills/{name}/scripts/verify_digest.py", on_disk)

        manifest = json.loads(
            (repo / ".aw/system/managed-sections.json").read_text(encoding="utf-8")
        )
        recorded = [k for k in manifest["files"] if k.startswith(".agents/skills/")]
        self.assertEqual(
            sorted(recorded),
            on_disk,
            "every emitted skill file must be recorded in the ownership manifest",
        )

    def test_no_adapter_metadata_files_emitted(self):
        # OQ-02 Option A: ONLY skill-package files are emitted; the adapter `host_adapters`
        # metadata (to_dict-only) is NOT written as files. Every emitted skills-dir file is
        # part of a skill package (SKILL.md, reference/*, scripts/*) - no adapter/*.json etc.
        repo = init_repo(self.base / "nometa")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        for p in self._skill_files_on_disk(repo):
            tail = p[len(".agents/skills/") :]
            self.assertRegex(
                tail,
                r"^[^/]+/(SKILL\.md|reference/.+|scripts/.+)$",
                f"unexpected non-skill-package file emitted under skills dir: {p}",
            )

    def test_reinstall_is_idempotent_no_op_for_skills(self):
        # E-05/V-05: a second install writes nothing new for skills; all report
        # `[already current]` (empty install-diff) and none are spuriously pruned.
        repo = init_repo(self.base / "idem")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        first = self._skill_files_on_disk(repo)

        res2 = INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        second = self._skill_files_on_disk(repo)
        self.assertEqual(first, second, "skill fileset changed on re-install")

        newly_installed = [
            i
            for i in res2["installed"]
            if i.startswith(".agents/skills/") and "[install]" in i
        ]
        self.assertEqual(
            newly_installed, [], f"re-install re-wrote skills: {newly_installed}"
        )
        skipped_skills = [s for s in res2["skipped"] if s.startswith(".agents/skills/")]
        self.assertEqual(
            len(skipped_skills),
            len(first),
            "every skill file should be reported [already current] on re-install",
        )
        self.assertTrue(all("[already current]" in s for s in skipped_skills))
        pruned_skills = [p for p in res2["pruned"] if p.startswith(".agents/skills/")]
        self.assertEqual(
            pruned_skills, [], "no skill file should be pruned on re-install"
        )

    def test_orphaned_tracked_skill_file_is_pruned(self):
        # E-05/V-05: a committed skill file that is no longer generated is pruned on install.
        repo = init_repo(self.base / "orphan-tracked")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        git(repo, "commit", "-qm", "install")

        orphan = repo / ".agents/skills/zzz-orphan/SKILL.md"
        orphan.parent.mkdir(parents=True)
        orphan.write_text("orphan router\n", encoding="utf-8")
        git(repo, "add", "--", ".agents/skills/zzz-orphan/SKILL.md")
        git(repo, "commit", "-qm", "orphan")

        res = INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        pruned = [p for p in res["pruned"] if "zzz-orphan" in p]
        self.assertTrue(pruned, "orphaned tracked skill file was not pruned")
        self.assertFalse(
            orphan.exists(), "orphaned skill file still on disk after prune"
        )

    def test_orphaned_untracked_skill_file_is_pruned(self):
        repo = init_repo(self.base / "orphan-untracked")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        git(repo, "commit", "-qm", "install")

        orphan = repo / ".agents/skills/yyy-orphan/SKILL.md"
        orphan.parent.mkdir(parents=True)
        orphan.write_text("orphan router\n", encoding="utf-8")

        res = INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        pruned = [p for p in res["pruned"] if "yyy-orphan" in p]
        self.assertTrue(pruned, "orphaned untracked skill file was not pruned")
        self.assertFalse(orphan.exists())

    def test_uninstall_removes_emitted_skill_files_via_manifest(self):
        # E-07/V-07: manifest-driven uninstall removes exactly the emitted skill files.
        repo = init_repo(self.base / "uninstall")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        git(repo, "commit", "-qm", "install")

        before = self._skill_files_on_disk(repo)
        self.assertTrue(before, "precondition: skill files present after install")

        actions = INS.uninstall_repo(repo, use_git=True)
        removed_skill_actions = [
            a for a in actions if a.startswith("removed .agents/skills/")
        ]
        self.assertEqual(
            len(removed_skill_actions),
            len(before),
            "uninstall did not remove every emitted skill file",
        )
        self.assertEqual(
            self._skill_files_on_disk(repo),
            [],
            "skill files remain after manifest-driven uninstall",
        )


if __name__ == "__main__":
    unittest.main()

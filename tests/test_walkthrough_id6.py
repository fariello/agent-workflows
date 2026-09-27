"""Tests for walkthrough id6 filenames and cutover (IPD nrqo90)."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import set_records


class _RepoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_wkthid6_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.tmp, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.tmp, check=True)
        self.executed_plans = self.tmp / ".aw" / "records" / "plans" / "executed"
        self.walkthroughs = self.tmp / ".aw" / "records" / "walkthroughs"
        self.config_dir = self.tmp / ".aw" / "config"
        self.executed_plans.mkdir(parents=True, exist_ok=True)
        self.walkthroughs.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)


class TestWalkthroughOutcome(_RepoTestCase):
    """E-01 outcome tests: producer mints own id6, post-cutover enforces id6, pre-cutover grandfathered."""

    def test_write_walkthrough_mints_own_id6(self):
        plan_content = (
            "# IPD: Test Plan\n\n" "- Id: pl1abc\n" "- Set: s\n" "- Status: executed\n"
        )
        (self.executed_plans / "20260901-s-01-pl1abc-test-plan.ipd.md").write_text(
            plan_content, encoding="utf-8"
        )

        body = set_records.render_walkthrough(
            set_id="s",
            run_id="run-test",
            checkpoint="terminal",
            records=[],
            summary="Test walkthrough",
        )
        dest = set_records.write_walkthrough(
            self.tmp,
            set_id="s",
            order=1,
            target_id6="pl1abc",
            slug="x",
            body=body,
        )
        m = re.match(r"^(\d{8})-s-01-([a-z0-9]{6})-x\.walkthrough\.md$", dest.name)
        self.assertIsNotNone(m, f"Filename {dest.name} did not match pattern")
        id6 = m.group(2)
        self.assertNotEqual(id6, "pl1abc")

        content = dest.read_text(encoding="utf-8")
        self.assertIn(f"- Id: {id6}", content)
        self.assertIn("- Target-Id: pl1abc", content)

        drifts = ce.check_collisions(self.tmp, include_retired=True)
        slot_drifts = [d for d in drifts if d.rule == "check.id6-identity-slot"]
        self.assertEqual(slot_drifts, [])

    def test_post_cutover_legacy_walkthrough_nonconformant(self):
        (self.config_dir / "project.json").write_text(
            '{"cutovers": {"walkthrough_id6": "2026-09-27"}}',
            encoding="utf-8",
        )
        late_file = (
            self.walkthroughs / "20260928-1200-01-late-walkthrough.walkthrough.md"
        )
        late_file.write_text("# Walkthrough\n\n- Date: 2026-09-28\n", encoding="utf-8")
        drifts = ce.check_names(self.tmp, "walkthroughs")
        name_drifts = [d for d in drifts if d.rule == "check.name-nonconformant"]
        self.assertEqual(len(name_drifts), 1)
        self.assertIn(
            "walkthrough dated at/after the id6 cutover", name_drifts[0].detail
        )

    def test_pre_cutover_legacy_walkthrough_conformant(self):
        (self.config_dir / "project.json").write_text(
            '{"cutovers": {"walkthrough_id6": "2026-09-27"}}',
            encoding="utf-8",
        )
        early_file = (
            self.walkthroughs / "20260712-1023-01-early-walkthrough.walkthrough.md"
        )
        early_file.write_text("# Walkthrough\n\n- Date: 2026-07-12\n", encoding="utf-8")
        drifts = ce.check_names(self.tmp, "walkthroughs")
        name_drifts = [d for d in drifts if d.rule == "check.name-nonconformant"]
        self.assertEqual(name_drifts, [])


REPO_ROOT = Path(__file__).resolve().parent.parent

LEGACY_WALKTHROUGHS = {
    "20260712-1023-01-installer-shim-detection-ctrlc-and-diff-walkthrough.walkthrough.md",
    "20260712-1033-01-assess-bugs-and-tests-walkthrough.walkthrough.md",
    "20260712-1038-01-fix-installer-shim-tests-left-red-walkthrough.walkthrough.md",
    "20260712-1041-01-agents-docs-research-and-walkthroughs-convention-walkthrough.walkthrough.md",
    "20260712-1049-01-scope-review-gemini-bugs-tests-execution-walkthrough.walkthrough.md",
    "20260712-1100-01-1028-falsely-marked-executed-tests-still-red-walkthrough.walkthrough.md",
    "20260712-1200-01-ux-and-data-modeling-principles-import-walkthrough.walkthrough.md",
    "20260712-1230-01-mirror-workflow-pointer-into-native-agent-files-walkthrough.walkthrough.md",
    "20260810-2052-01-awphysical-01-rejected-greenwashed-execution-corrective-review.walkthrough.md",
    "20260812-0300-01-awphysical-overnight-autonomous-execution-01-to-10-walkthrough.walkthrough.md",
    "20260812-1200-01-order11-self-migration-decision-record-walkthrough.walkthrough.md",
}

# Grandfathered bullet-less walkthrough (commit 9a1c4206: "have none and keep their id6 in the filename only")
BULLETLESS_GRANDFATHERED = {
    "20260823-35xfvu-01-35xfvu-highpbacklog0822-execution-decisions.walkthrough.md",
}


class TestWalkthroughDeclaredIdMatchesSlot(unittest.TestCase):
    """E-06 / V-06: Every clustered walkthrough declares a `- Id:` equal to its slot id6."""

    def test_clustered_walkthroughs_declare_matching_id(self):
        npn = ce._load_normalizer()
        self.assertIsNotNone(npn, "normalizer must be loadable")
        wdir = REPO_ROOT / ".aw" / "records" / "walkthroughs"
        self.assertTrue(wdir.is_dir(), f"{wdir} must exist")

        all_files = sorted(
            p
            for p in wdir.glob("*.md")
            if p.is_file() and p.name not in {"README.md", ".gitkeep"}
        )
        self.assertEqual(len(all_files), 24, "Census must find exactly 24 walkthroughs")

        exempt = [p for p in all_files if p.name in LEGACY_WALKTHROUGHS]
        self.assertEqual(
            len(exempt), 11, "Must find exactly 11 grandfathered legacy walkthroughs"
        )

        missing_or_mismatched = []
        for p in all_files:
            if p.name in LEGACY_WALKTHROUGHS or p.name in BULLETLESS_GRANDFATHERED:
                continue
            token = ce._identity_slot_token(p.name)
            if not token:
                continue
            (id_val, in_reg), _ = ce._identity_declared_values(
                p.read_text(encoding="utf-8")
            )
            if not (in_reg and id_val == token):
                missing_or_mismatched.append(
                    f"{p.name}: slot id6={token!r}, declared in metadata region={id_val!r}"
                )

        self.assertEqual(
            missing_or_mismatched,
            [],
            "Walkthroughs missing declared - Id: matching identity slot:\n"
            + "\n".join(missing_or_mismatched),
        )

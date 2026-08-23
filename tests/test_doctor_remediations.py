"""Tests for doctor actionable remediation commands and targeted fixes."""

from __future__ import annotations

import io
import unittest
from pathlib import Path

from agent_workflows import artifact_core as core
from agent_workflows import doctor
from agent_workflows import term as T


class DoctorRemediationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path("/dummy/repo")

    def test_infer_artifact_type(self) -> None:
        self.assertEqual(
            doctor._infer_artifact_type(".aw/records/plans/pending/test.ipd.md"),
            "plans",
        )
        self.assertEqual(
            doctor._infer_artifact_type(".aw/records/specs/test.spec.md"), "specs"
        )
        self.assertEqual(
            doctor._infer_artifact_type(".aw/records/prompts/pending/test.prompt.md"),
            "prompts",
        )
        self.assertEqual(
            doctor._infer_artifact_type(".aw/records/backlog/open/test.backlog.md"),
            "backlog",
        )
        self.assertEqual(
            doctor._infer_artifact_type(".aw/records/research/test.research.md"),
            "research",
        )
        self.assertEqual(
            doctor._infer_artifact_type(".aw/records/walkthroughs/test.walkthrough.md"),
            "walkthroughs",
        )
        self.assertEqual(
            doctor._infer_artifact_type(".aw/records/roadmaps/test.roadmap.md"),
            "roadmaps",
        )
        self.assertEqual(
            doctor._infer_artifact_type(".aw/records/releases/test.release.md"),
            "releases",
        )

    def test_stale_index_remediation(self) -> None:
        d = core.Drift(
            ".aw/records/plans/INDEX.json", "stale-index", "index out of date"
        )
        rem = doctor.build_remediation(d, self.repo_root)
        self.assertEqual(rem.command, "aw index plans")
        self.assertIn("aw index plans", rem.detailed_fix)
        self.assertEqual(rem.summary_fix, "aw index")

    def test_setup_needed_remediation(self) -> None:
        d = core.Drift("<setup>", "doctor.setup-needed", "initial setup needed")
        rem = doctor.build_remediation(d, self.repo_root)
        self.assertEqual(rem.command, "aw setup")
        self.assertIn("aw setup", rem.detailed_fix)
        self.assertEqual(rem.summary_fix, "aw setup")

    def test_layout_split_brain_remediation(self) -> None:
        d = core.Drift("<layout>", "doctor.layout-split-brain", "dual layout")
        rem = doctor.build_remediation(d, self.repo_root)
        self.assertEqual(rem.command, "aw migrate-layout")
        self.assertIn("aw migrate-layout", rem.detailed_fix)
        self.assertEqual(rem.summary_fix, "aw migrate-layout")

    def test_sanitizer_leak_remediation(self) -> None:
        d = core.Drift("src/secret.py", "doctor.leak-secret", "sensitive token")
        rem = doctor.build_remediation(d, self.repo_root)
        self.assertEqual(rem.command, "aw sanitize --fix")
        self.assertIn("aw sanitize --fix", rem.detailed_fix)
        self.assertEqual(rem.summary_fix, "aw sanitize --fix")

    def test_name_nonconformant_remediation(self) -> None:
        d = core.Drift(
            ".aw/records/plans/pending/bad_plan.md", "name-nonconformant", "bad name"
        )
        rem = doctor.build_remediation(d, self.repo_root)
        self.assertEqual(
            rem.command, "aw rename plans .aw/records/plans/pending/bad_plan.md"
        )
        self.assertNotIn("<type>", rem.command)
        self.assertNotIn("<file>", rem.command)

    def test_setid_collision_remediation(self) -> None:
        d = core.Drift(
            ".aw/records/specs/20260822-auth-01-sp0001-spec.md",
            "setid-collision",
            "conflicts with .aw/records/specs/20260822-auth-02-sp0002-spec.md",
        )
        rem = doctor.build_remediation(d, self.repo_root)
        self.assertEqual(
            rem.command,
            "aw group specs .aw/records/specs/20260822-auth-01-sp0001-spec.md --set <new-set-id>",
        )
        self.assertNotIn("<type>", rem.command)
        self.assertNotIn("<file>", rem.command)

    def test_blocks_release_dangling_remediation(self) -> None:
        d = core.Drift(
            ".aw/records/specs/my_spec.spec.md",
            "blocks-release-dangling",
            "release next not found",
        )
        rem = doctor.build_remediation(d, self.repo_root)
        self.assertEqual(
            rem.command,
            "aw specs set .aw/records/specs/my_spec.spec.md --blocks-release next",
        )

    def test_human_report_renders_concrete_commands(self) -> None:
        report = doctor.DoctorReport(
            repo_root=self.repo_root,
            env=doctor.EnvironmentProbeResult(
                is_source_repo=False,
                installed_version="1.0.0",
                packaged_version="1.0.0",
                version_status="ok",
                layout="standard",
                preset="standard",
                backend="repo-tracked",
                setup_needed=False,
                drift=[],
            ),
            git=doctor.GitProbeResult(
                available=True,
                branch="main",
                upstream=None,
                ahead=0,
                behind=0,
                conflicts=[],
                staged=[],
                modified=[],
                untracked=[],
                drift=[],
            ),
            attention=doctor.AttentionProbeResult(
                total_items=10,
                by_class={"ready": 5, "done": 5},
                active_release=None,
                release_blockers=[],
                drift=[],
            ),
            artifacts=doctor.ArtifactsProbeResult(
                type_counts={"plans": 5},
                type_drift={
                    "plans": [
                        core.Drift(
                            ".aw/records/plans/pending/invalid.md",
                            "name-nonconformant",
                            "bad name",
                        )
                    ]
                },
                all_drift=[
                    core.Drift(
                        ".aw/records/plans/pending/invalid.md",
                        "name-nonconformant",
                        "bad name",
                    )
                ],
            ),
            sanitizer=doctor.SanitizerProbeResult(findings=[]),
            all_drift=[
                core.Drift(
                    ".aw/records/plans/pending/invalid.md",
                    "name-nonconformant",
                    "bad name",
                )
            ],
        )

        out = doctor.render_human_report(
            report, T.Term(stream=io.StringIO(), color=False)
        )
        self.assertIn("aw rename plans .aw/records/plans/pending/invalid.md", out)
        self.assertNotIn("aw rename <type>", out)

    def test_priority_ranking_next_action(self) -> None:
        # Multi-category drift: setup + leak + stale-index
        drift_list = [
            core.Drift(".aw/records/plans/INDEX.json", "stale-index", "out of date"),
            core.Drift("<setup>", "doctor.setup-needed", "initial setup"),
            core.Drift("src/secret.py", "doctor.leak-secret", "token"),
        ]
        next_cmd, next_actions = doctor.resolve_next_actions(drift_list, self.repo_root)
        self.assertEqual(next_cmd, "aw setup")
        cmd_names = [a.command for a in next_actions]
        self.assertIn("aw setup", cmd_names)
        self.assertIn("aw sanitize --fix", cmd_names)
        self.assertIn("aw index plans", cmd_names)

    def test_git_dirty_and_staged_remediation(self) -> None:
        dirty_drift = core.Drift(
            "agent_workflows/foo.py", "doctor.git-dirty", "modified file"
        )
        rem_dirty = doctor.build_remediation(dirty_drift, self.repo_root)
        self.assertEqual(
            rem_dirty.command, 'git commit -m "Update" -- agent_workflows/foo.py'
        )

        staged_drift = core.Drift(
            "agent_workflows/bar.py", "doctor.git-staged", "staged file"
        )
        rem_staged = doctor.build_remediation(staged_drift, self.repo_root)
        self.assertEqual(
            rem_staged.command, 'git commit -m "Update" -- agent_workflows/bar.py'
        )

    def test_summary_unsafe_remediation(self) -> None:
        d = core.Drift(
            ".aw/records/plans/pending/test.ipd.md",
            "summary-unsafe",
            "multi-line summary",
        )
        rem = doctor.build_remediation(d, self.repo_root)
        self.assertIsNone(rem.command)
        self.assertIn(".aw/records/plans/pending/test.ipd.md", rem.detailed_fix)
        self.assertIn("single-line", rem.detailed_fix)

    def test_inspect_repo_next_actions_integration(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
            # Create a file with bad filename
            (
                tmp_path / ".aw" / "records" / "plans" / "pending" / "invalid_name.md"
            ).write_text("# Title\n\n- Id: abcd01\n- Set: test\n", encoding="utf-8")
            result = doctor.inspect_repo(tmp_path)
            self.assertIsNotNone(result.next_actions)
            cmd_list = [a.command for a in result.next_actions]
            # Should contain a concrete command (e.g. aw rename plans ...)
            self.assertTrue(
                any("aw rename plans" in cmd or "aw setup" in cmd for cmd in cmd_list)
            )


if __name__ == "__main__":
    unittest.main()

"""Tests for doctor actionable remediation commands and targeted fixes."""

from __future__ import annotations

import io
import unittest
from pathlib import Path

from unittest import mock

from agent_workflows import artifact_core as core
from agent_workflows import doctor
from agent_workflows import term as T
from agent_workflows import versioning


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
        # setupmarker: the per-repo reminder is cleared by the `/setup-repo` WORKFLOW, never by
        # `aw setup` (the machine-wide install wizard, which does not touch the marker).
        d = core.Drift("<setup>", "doctor.setup-needed", "initial setup needed")
        rem = doctor.build_remediation(d, self.repo_root)
        self.assertEqual(rem.command, "/setup-repo")
        self.assertIn("/setup-repo", rem.detailed_fix)
        self.assertEqual(rem.summary_fix, "/setup-repo")
        # The remediation must NOT tell the user to run the machine-wide wizard.
        self.assertNotIn("run 'aw setup'", rem.detailed_fix)

    def test_version_mismatch_remediation_is_install_not_setup(self) -> None:
        # A stale install is fixed by re-running the installer in THIS repo. `aw setup` is the
        # machine-wide wizard (it offers to install into every discovered repo), which is far too
        # wide a remedy for one repo's version drift.
        for rule in ("doctor.version-stale", "doctor.version-not-installed"):
            d = core.Drift("<version>", rule, "installed=1.0.0 packaged=1.2.1")
            rem = doctor.build_remediation(d, self.repo_root)
            self.assertEqual(rem.command, "aw install", rule)
            self.assertIn("aw install", rem.detailed_fix)
            self.assertNotIn("aw setup", rem.detailed_fix)

    def test_pypi_update_remediation_is_pip_upgrade(self) -> None:
        # awpypi: a newer PUBLISHED release upgrades the running PACKAGE (pip), which is a
        # different remedy from doctor.version-* (refresh one repo's managed files).
        d = core.Drift(
            "<pypi>", "doctor.pypi-update-available", "running=1.0.0 published=2.0.0"
        )
        rem = doctor.build_remediation(d, self.repo_root)
        self.assertEqual(rem.command, "pip install -U agent-workflows")
        self.assertIn("pip install -U agent-workflows", rem.detailed_fix)
        # It must also tell the user to refresh each repo afterwards.
        self.assertIn("aw install", rem.detailed_fix)

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

    def test_id6_identity_slot_remediation(self) -> None:
        # IPD 9a655p E-02/V-02: the identity-slot rule renders a D140 remediation with a
        # Target-Id hint, not a bare failure.
        d = core.Drift(
            ".aw/records/walkthroughs/20260823-artifactenginefix-01-p7dqwz-execution.walkthrough.md",
            "check.id6-identity-slot",
            "filename identity-slot id6 p7dqwz is another file's identity",
        )
        rem = doctor.build_remediation(d, self.repo_root)
        self.assertIn("identity-slot", rem.title)
        self.assertIn("D140", rem.detailed_fix)
        self.assertIn("Target-Id", rem.detailed_fix)
        self.assertIn("own", rem.summary_fix)

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
        # setup-needed keeps the TOP priority slot, now as the `/setup-repo` workflow. Regression
        # guard: giving that remediation a None command would drop it from raw_actions entirely and
        # silently promote the leak fix to primary.
        self.assertEqual(next_cmd, "/setup-repo")
        cmd_names = [a.command for a in next_actions]
        self.assertIn("/setup-repo", cmd_names)
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


class DoctorPypiProbeTests(unittest.TestCase):
    """awpypi: the OPT-IN 'is a newer release published?' probe.

    Correctness rules under test: it never runs unless asked; a lookup failure is never a
    finding; a dev/dirty checkout ahead of the last release is not an upgrade signal; and a
    genuinely behind clean release IS reported.
    """

    def setUp(self) -> None:
        self.repo_root = Path(".")

    def test_default_makes_no_network_call(self) -> None:
        # The strongest form of "off by default": if the probe were called, this raises.
        with mock.patch.object(
            versioning,
            "latest_pypi_version",
            side_effect=AssertionError("network called without --check-pypi"),
        ):
            res = doctor.probe_environment(self.repo_root)
        self.assertFalse(res.pypi_checked)
        self.assertIsNone(res.pypi_latest)
        self.assertEqual(
            [d for d in res.drift if "pypi" in d.rule],
            [],
        )

    def test_behind_published_release_is_reported(self) -> None:
        with mock.patch.object(
            versioning, "latest_pypi_version", return_value="2.0.0"
        ), mock.patch.object(versioning, "resolve_version", return_value="1.0.0"):
            res = doctor.probe_environment(self.repo_root, check_pypi=True)
        self.assertTrue(res.pypi_checked)
        self.assertEqual(res.pypi_latest, "2.0.0")
        rules = [d.rule for d in res.drift]
        self.assertIn("doctor.pypi-update-available", rules)

    def test_lookup_failure_is_not_a_finding(self) -> None:
        # Offline/timeout/unpublished all surface as None. An offline box must not be told it
        # is out of date, and must not be told it is up to date either.
        with mock.patch.object(
            versioning, "latest_pypi_version", return_value=None
        ), mock.patch.object(versioning, "resolve_version", return_value="1.0.0"):
            res = doctor.probe_environment(self.repo_root, check_pypi=True)
        self.assertTrue(res.pypi_checked)
        self.assertIsNone(res.pypi_latest)
        self.assertEqual([d for d in res.drift if "pypi" in d.rule], [])

    def test_dev_build_ahead_of_release_is_silent(self) -> None:
        # A source checkout normally sits ahead of the last published release; reporting that
        # as an available upgrade would be pure noise.
        for running in (
            "1.3.0rc2.dev1571+g4ee5282.d20260830",
            "1.3.0.dev1+gabc1234",
        ):
            with mock.patch.object(
                versioning, "latest_pypi_version", return_value="1.2.0"
            ), mock.patch.object(versioning, "resolve_version", return_value=running):
                res = doctor.probe_environment(self.repo_root, check_pypi=True)
            self.assertEqual(
                [d for d in res.drift if "pypi" in d.rule], [], f"running={running}"
            )

    def test_current_release_is_silent(self) -> None:
        with mock.patch.object(
            versioning, "latest_pypi_version", return_value="1.2.0"
        ), mock.patch.object(versioning, "resolve_version", return_value="1.2.0"):
            res = doctor.probe_environment(self.repo_root, check_pypi=True)
        self.assertEqual([d for d in res.drift if "pypi" in d.rule], [])

    def test_env_evidence_carries_pypi_facts_for_machine_consumers(self) -> None:
        # Fact parity: the --agent/--json payload must expose the same facts the human
        # renderer prints, including the not-checked case.
        result = doctor.inspect_repo(self.repo_root)
        env = next(e for e in result.evidence if e.key == "env")
        self.assertIn("pypi_checked", env.value)
        self.assertIn("pypi_latest", env.value)
        self.assertFalse(env.value["pypi_checked"])


if __name__ == "__main__":
    unittest.main()

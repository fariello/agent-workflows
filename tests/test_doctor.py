"""Tests for awdoctor Order 03: `aw doctor` deep repo inspector (composes existing signals)."""

from __future__ import annotations

import io
import subprocess
import tempfile
import types
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from agent_workflows import artifact_core as core
from agent_workflows import doctor
from agent_workflows import engine, versioning


def _git(root, *args):
    subprocess.run(["git", *args], cwd=str(root), check=True, capture_output=True)


class DoctorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "t@e.com")
        _git(self.root, "config", "user.name", "T")
        (self.root / ".aw" / "records").mkdir(parents=True)
        # Seed an installed VERSION matching the packaged/source version so version-drift is clean.
        # h90ij1: the marker goes at `.aw/system/VERSION`, the location `engine.read_installed_version`
        # actually probes and every install writes. This fixture previously wrote `.aw/VERSION`, a path
        # NO layout creates; it only read back as "installed" because doctor's probe was reading the
        # same fictional path. With both sides corrected the fixture is genuinely installed, so the
        # emitted layout document must be present too or `check.system-layout-missing` fires (which is
        # correct behavior for an installed workspace, see check_engine.check_system_layout).
        packaged = versioning.resolve_version(engine.resolve_source_root(None))
        (self.root / ".aw" / "system").mkdir(parents=True)
        (self.root / ".aw" / "system" / "VERSION").write_text(
            packaged + "\n", encoding="utf-8"
        )
        engine.emit_layout_artifacts(self.root)
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_clean_repo_no_findings(self) -> None:
        drift = doctor.run_doctor(self.root)
        self.assertEqual(
            drift, [], [f"{d.location}:{d.rule}:{d.detail}" for d in drift]
        )

    def test_dirty_repo_flagged(self) -> None:
        (self.root / "newfile.txt").write_text("x", encoding="utf-8")
        drift = doctor.run_doctor(self.root)
        self.assertTrue(any(d.rule == "doctor.git-untracked" for d in drift))

    def test_run_no_findings_exit0(self) -> None:
        from agent_workflows import term as T

        out = io.StringIO()
        term = T.Term(stream=out, color=False)
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            rc = doctor.run(
                types.SimpleNamespace(dir=str(self.root), as_agent=False), term=term
            )
        self.assertEqual(rc, 0)
        self.assertIn("no findings", out.getvalue())

    def test_run_agent_output(self) -> None:
        import json

        (self.root / "x.txt").write_text("x", encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            rc = doctor.run(types.SimpleNamespace(dir=str(self.root), as_agent=True))
        self.assertEqual(rc, 1)
        data = json.loads(out.getvalue().strip())
        self.assertEqual(data.get("schema"), "aw.agent/v1")
        self.assertEqual(data.get("cmd"), "doctor")
        self.assertEqual(data.get("outcome"), "findings")
        self.assertEqual(data.get("exit"), 1)

    def test_untracked_dir_excluded_by_default(self) -> None:
        pdir = self.root / ".aw" / "records" / "prompts" / "untracked"
        pdir.mkdir(parents=True)
        (pdir / "bad-name.md").write_text("# Bad\n", encoding="utf-8")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "add untracked prompt")

        # Default excludes untracked/ directory artifacts
        drift_default = doctor.run_doctor(self.root, include_untracked=False)
        self.assertEqual(drift_default, [])

        # include_untracked=True includes them and flags grammar issue
        drift_all = doctor.run_doctor(self.root, include_untracked=True)
        self.assertTrue(any(d.rule == "check.name-nonconformant" for d in drift_all))

    def test_executed_dir_warns_by_default(self) -> None:
        pdir = self.root / ".aw" / "records" / "plans" / "executed"
        pdir.mkdir(parents=True)
        (pdir / "bad-plan-name.md").write_text(
            "# Plan\n- Id: ppp111\n- Status: executed\n", encoding="utf-8"
        )
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "add executed plan")

        report = doctor.collect_doctor_report(self.root, include_executed=False)
        # Treated as executed warning, not in all_drift as name-nonconformant
        self.assertFalse(
            any(d.rule == "check.name-nonconformant" for d in report.all_drift)
        )
        self.assertTrue(
            any(
                d.rule == "check.name-nonconformant"
                for d in report.artifacts.executed_warnings
            )
        )

        # include_executed=True treats it as error
        report_strict = doctor.collect_doctor_report(self.root, include_executed=True)
        self.assertTrue(
            any(d.rule == "check.name-nonconformant" for d in report_strict.all_drift)
        )

    def test_split_brain_layout_detected(self) -> None:
        """A GENUINE split-brain is reported: LIVE `.agents/workflows` content beside `.aw/system`.

        z1yefm E-06 updated this fixture. It previously created two BARE EMPTY directories
        (`.agents/` and `.aw/`) and asserted split-brain, which encoded the very false positive
        that defect fixed: `.agents/skills` is the intended skills location for BOTH layouts, so
        `.agents/` exists PERMANENTLY on a correctly migrated repo, and an existence test called
        every such repo split-brain forever while the shared `engine.detect_split_brain_layout`
        said otherwise. The claim under test is unchanged (a real split-brain IS detected); only
        the fixture now creates a real one, namely a non-empty file under `.agents/workflows`.
        The residue-only converse is asserted in
        `DoctorLayoutClassificationIsContentAwareTests`.
        """
        (self.root / ".agents" / "workflows" / "assess").mkdir(
            parents=True, exist_ok=True
        )
        (self.root / ".agents" / "workflows" / "assess" / "assess.md").write_text(
            "# assess\nLIVE legacy workflow body\n", encoding="utf-8"
        )
        self.assertTrue(engine.detect_split_brain_layout(self.root))
        report = doctor.collect_doctor_report(self.root)
        self.assertIn("split-brain", report.env.layout)
        self.assertTrue(
            any(d.rule == "doctor.layout-split-brain" for d in report.env.drift)
        )

    def test_render_groups_artifact_issues_by_type_and_dir_with_fixes(self) -> None:
        from agent_workflows import term as T

        bdir = self.root / ".aw" / "records" / "backlog" / "open"
        bdir.mkdir(parents=True, exist_ok=True)
        (bdir / "bad-backlog.backlog.md").write_text(
            "# Title\n- Id: bk1\n- Summary: multi\nline\n- Status: open\n",
            encoding="utf-8",
        )
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "add bad backlog")

        report = doctor.collect_doctor_report(self.root)
        term = T.Term(color=False)
        rendered = doctor.render_human_report(report, term)

        self.assertIn(
            "Issue: Filename does not match artifact naming grammar", rendered
        )
        self.assertIn("- .aw/records/backlog/open", rendered)
        self.assertIn("1. bad-backlog.backlog.md", rendered)
        self.assertIn("Fix:", rendered)
        self.assertIn("Summary of issues and proposed fixes:", rendered)

    def test_render_git_modified_warns_without_error_block_prefix(self) -> None:
        from agent_workflows import term as T

        (self.root / "README.md").write_text("Hello", encoding="utf-8")
        _git(self.root, "add", "README.md")
        _git(self.root, "commit", "-qm", "add readme")
        (self.root / "README.md").write_text("Modified", encoding="utf-8")

        report = doctor.collect_doctor_report(self.root)
        term = T.Term(color=False)
        rendered = doctor.render_human_report(report, term)

        self.assertIn("Git Working Tree", rendered)
        self.assertNotIn("[ERROR] Git Working Tree", rendered)
        self.assertIn("Unstaged modifications (1):", rendered)

    def test_immediate_startup_announcement(self) -> None:
        from agent_workflows import term as T

        out = io.StringIO()
        term = T.Term(stream=out, color=False)
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            doctor.run(
                types.SimpleNamespace(dir=str(self.root), as_agent=False), term=term
            )
        self.assertIn("Starting aw doctor repository health check...", out.getvalue())


class DoctorEnvironmentProbeReadsCanonicalPathsTests(unittest.TestCase):
    """h90ij1: doctor's environment probe must read the paths a real install actually writes.

    Before the fix, `probe_environment` resolved the installed VERSION from `.aw/VERSION` and
    `.agents/VERSION`, and the preset/backend from `.aw/config.json` / `.agents/config.json`.
    NONE of those four paths is created by either supported layout, so a correctly installed
    target read back as `not installed` with a blank preset and backend.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _install_marker(self, rel: str, value: str) -> None:
        marker = self.root / rel
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(value + "\n", encoding="utf-8")

    def test_probe_agrees_with_engine_on_aw_system_version(self) -> None:
        """E-03/V-01: the probe must return what the single version authority returns.

        Binds doctor's answer to `engine.read_installed_version` rather than to a literal path,
        so a future change to the probe order cannot silently desynchronize the two again.
        """
        self._install_marker(".aw/system/VERSION", "1.2.1")

        expected = engine.read_installed_version(self.root)
        self.assertEqual(expected, "1.2.1")
        self.assertEqual(
            doctor.probe_environment(self.root).installed_version, expected
        )

    def test_probe_agrees_with_engine_on_legacy_workflows_version(self) -> None:
        """V-01 (second half): the legacy `.agents/workflows/VERSION` location resolves too."""
        self._install_marker(".agents/workflows/VERSION", "1.1.0")

        expected = engine.read_installed_version(self.root)
        self.assertEqual(expected, "1.1.0")
        self.assertEqual(
            doctor.probe_environment(self.root).installed_version, expected
        )

    def test_probe_reads_preset_and_backend_from_canonical_project_config(self) -> None:
        """E-02/V-02: preset and backend come from `.aw/config/project.json`."""
        cfg = self.root / ".aw" / "config"
        cfg.mkdir(parents=True)
        (cfg / "project.json").write_text(
            '{"schema_version": 2, "preset": "private-target",'
            ' "records_backend": "repository"}\n',
            encoding="utf-8",
        )

        res = doctor.probe_environment(self.root)
        self.assertEqual(res.preset, "private-target")
        self.assertEqual(res.backend, "repository")

    def test_healthy_installed_target_emits_no_version_not_installed_finding(
        self,
    ) -> None:
        """E-04/V-04: the user-visible symptom - a healthy NON-SOURCE target must not be
        reported as `not installed`.

        Distinct surface from the read tests above: this asserts on the drift entry the read
        DRIVES. It must be a non-source repo, because the finding is gated on
        `not res.is_source_repo`, which is exactly why the framework's own checkout never
        showed the bug.
        """
        packaged = versioning.resolve_version(engine.resolve_source_root(None))
        self._install_marker(".aw/system/VERSION", packaged)
        (self.root / ".aw" / "records").mkdir(parents=True, exist_ok=True)

        res = doctor.probe_environment(self.root)
        self.assertFalse(res.is_source_repo)
        self.assertEqual(res.installed_version, packaged)
        self.assertNotIn(
            "doctor.version-not-installed",
            [d.rule for d in res.drift],
            [f"{d.rule}:{d.detail}" for d in res.drift],
        )

    def test_status_and_doctor_report_the_same_preset_and_backend(self) -> None:
        """E-05/V-05: `aw status` and `aw doctor` share ONE reader, so they cannot diverge."""
        from agent_workflows import cli

        cfg = self.root / ".aw" / "config"
        cfg.mkdir(parents=True)
        (cfg / "project.json").write_text(
            '{"schema_version": 2, "preset": "public-target-private-companion",'
            ' "records_backend": "companion"}\n',
            encoding="utf-8",
        )
        self._install_marker(".aw/system/VERSION", "1.2.1")

        env = doctor.probe_environment(self.root)
        status = cli._collect_repo_status_details(self.root, "1.3.0")

        self.assertEqual(env.preset, "public-target-private-companion")
        self.assertEqual(env.backend, "companion")
        self.assertEqual(status["preset"], env.preset)
        self.assertEqual(status["backend"], env.backend)


class DoctorLayoutClassificationIsContentAwareTests(unittest.TestCase):
    """migleftover Order 01 (z1yefm) E-06: doctor's layout verdict must match the shared detector.

    Before the fix, `probe_environment` computed the layout from bare `.is_dir()` existence
    tests, while `engine.detect_split_brain_layout` (the detector `cli._split_brain_guard`
    consumes) walks `.agents/workflows` for a non-empty, non-cruft FILE. The two therefore
    DISAGREED on a migrated repo: engine said False, doctor said
    `.aw + .agents (dual layout / split-brain)` and advised running a migration that had
    already run.

    Cleanup alone can never fix that, because `.agents/skills` is the intended skills location
    for BOTH layouts, so `.agents/` is a PERMANENT resident of a fully migrated repo.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # A migrated repo: populated `.aw/system` ...
        (self.root / ".aw" / "system" / "workflows").mkdir(parents=True)
        (self.root / ".aw" / "system" / "VERSION").write_text(
            "1.3.0\n", encoding="utf-8"
        )
        # ... plus the residue shape: EMPTY legacy tool dirs and a leftover README ...
        for wf in ("assess", "verify", "benchmark", "setup-repo"):
            (self.root / ".agents" / "workflows" / wf / "tools").mkdir(parents=True)
        (self.root / ".agents" / "README.md").write_text(
            "# .agents\n", encoding="utf-8"
        )
        # ... plus the PERMANENT shared skills directory, which is not residue at all.
        skill = self.root / ".agents" / "skills" / "assess" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("# assess skill\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_residue_only_repo_is_not_reported_split_brain(self) -> None:
        """A migrated repo holding only residue reports a plain `.aw` layout."""
        self.assertFalse(engine.detect_split_brain_layout(self.root))
        res = doctor.probe_environment(self.root)
        self.assertEqual(res.layout, ".aw")
        self.assertNotIn(
            "doctor.layout-split-brain",
            [d.rule for d in res.drift],
            [f"{d.rule}:{d.detail}" for d in res.drift],
        )

    def test_genuine_split_brain_is_still_detected(self) -> None:
        """True-positive detection is NOT lost: a non-empty file under .agents/workflows counts."""
        (self.root / ".agents" / "workflows" / "assess" / "assess.md").write_text(
            "# assess\nLIVE legacy body\n", encoding="utf-8"
        )
        self.assertTrue(engine.detect_split_brain_layout(self.root))
        res = doctor.probe_environment(self.root)
        self.assertIn("split-brain", res.layout)
        self.assertIn("doctor.layout-split-brain", [d.rule for d in res.drift])

    def test_doctor_and_engine_agree_on_both_shapes(self) -> None:
        """Bind doctor's verdict to the SHARED detector rather than to a literal path test."""
        for genuine in (False, True):
            with self.subTest(genuine=genuine):
                live = self.root / ".agents" / "workflows" / "assess" / "assess.md"
                if genuine:
                    live.write_text("# assess\nLIVE\n", encoding="utf-8")
                elif live.exists():
                    live.unlink()
                self.assertEqual(
                    engine.detect_split_brain_layout(self.root),
                    "split-brain" in doctor.probe_environment(self.root).layout,
                    "doctor and engine disagree about split-brain",
                )

    def test_legacy_only_repo_still_reports_agents_layout(self) -> None:
        """No regression for a repo that has NOT migrated: it is `.agents`, not split-brain."""
        import shutil as _shutil

        _shutil.rmtree(self.root / ".aw")
        (self.root / ".agents" / "workflows" / "assess" / "assess.md").write_text(
            "# assess\n", encoding="utf-8"
        )
        res = doctor.probe_environment(self.root)
        self.assertEqual(res.layout, ".agents")


class DoctorRemediationTests(unittest.TestCase):
    """Regression tests for IPD 6k7xot: honest and runnable aw doctor remediations."""

    # Rule table representing every branch build_remediation handles (E-06 / V-06)
    REPRESENTATIVE_DRIFTS = [
        core.Drift(
            ".aw/records/backlog/open/20260908-demo-01-aaa111-a-truncated-slug-.backlog.md",
            "check.name-nonconformant",
            "nonconformant name",
        ),
        core.Drift(
            ".aw/records/plans/pending/20260925-doctorhint-01-6k7xot-test.ipd.md",
            "check.setid-collision",
            "setid collision with other",
        ),
        core.Drift(
            ".aw/records/specs/draft/20260925-1111-01-test.spec.md",
            "check.blocks-release-dangling",
            "dangling release gate",
        ),
        core.Drift(
            ".aw/records/plans/pending/20260925-doctorhint-01-6k7xot-test.ipd.md",
            "check.status-untooled",
            "status changed to 'approved'",
        ),
        core.Drift("some/file.py", "doctor.git-dirty", "uncommitted modification"),
        core.Drift("<git>", "doctor.git-dirty", "uncommitted modification"),
        core.Drift("some/file.py", "doctor.git-staged", "staged change"),
        core.Drift("<git>", "doctor.git-staged", "staged change"),
        core.Drift(
            ".aw/records/plans/pending/20260925-doctorhint-01-aaa111-test.ipd.md",
            "check.id6-identity-slot",
            "identity slot does not match",
        ),
        core.Drift(
            ".aw/records/plans/pending/20260925-doctorhint-01-aaa111-test.ipd.md",
            "check.summary-unsafe",
            "multiline summary",
        ),
        core.Drift(
            ".aw/records/plans/manifest.json",
            "check.stale-index-missing",
            "index missing",
        ),
        core.Drift(
            ".aw/records/plans/manifest.json", "check.stale-index-stale", "index stale"
        ),
        core.Drift(
            ".aw/records/plans/manifest.json", "doctor.index-stale", "index stale"
        ),
        core.Drift(".aw/setup-repo-needed.md", "doctor.setup-needed", "setup needed"),
        core.Drift(
            ".agents/workflows/assess", "doctor.layout-split-brain", "split brain"
        ),
        core.Drift("<pypi>", "doctor.pypi-update-available", "update available"),
        core.Drift(
            ".aw/system/VERSION", "doctor.version-not-installed", "version mismatch"
        ),
        core.Drift("some/secret.py", "doctor.leak-detected", "sensitive token"),
        core.Drift("some/untracked.txt", "doctor.git-untracked", "untracked file"),
        core.Drift("some/conflict.txt", "doctor.git-conflict", "unmerged conflict"),
        core.Drift(
            "some/artifact.md", "check.generic-fallback", "unknown check finding"
        ),
    ]

    def test_remediation_family_guard(self) -> None:
        """E-06/V-06: Every emitted command must be runnable as printed: no <...> placeholders,
        never starts with 'git commit', and contains '--apply' for 'aw rename' and 'aw group'."""
        root = Path(".")
        for d in self.REPRESENTATIVE_DRIFTS:
            with self.subTest(rule=d.rule, loc=d.location):
                rem = doctor.build_remediation(d, root)
                if rem.command is not None:
                    cmd = rem.command
                    self.assertNotIn("<", cmd, f"Command contains placeholder: {cmd}")
                    self.assertNotIn(">", cmd, f"Command contains placeholder: {cmd}")
                    self.assertFalse(
                        cmd.startswith("git commit"),
                        f"Command must not start with git commit: {cmd}",
                    )
                    if cmd.startswith(("aw rename", "aw group")):
                        self.assertIn(
                            "--apply",
                            cmd,
                            f"Rename/group mutation must contain --apply: {cmd}",
                        )

    def test_resolve_next_actions_advisory_rules_return_no_action(self) -> None:
        """E-06: resolve_next_actions returns no action for a drift set made only of the five
        rules made advisory by E-01..E-05."""
        advisory_drifts = [
            core.Drift(
                ".aw/records/backlog/open/20260908-demo-01-aaa111-a-truncated-slug-.backlog.md",
                "check.name-nonconformant",
                "bad name",
            ),
            core.Drift(
                ".aw/records/plans/pending/20260925-doctorhint-01-6k7xot-test.ipd.md",
                "check.setid-collision",
                "collision",
            ),
            core.Drift(
                ".aw/records/specs/draft/20260925-1111-01-test.spec.md",
                "check.blocks-release-dangling",
                "dangling",
            ),
            core.Drift(
                ".aw/records/plans/pending/20260925-doctorhint-01-6k7xot-test.ipd.md",
                "check.status-untooled",
                "changed to 'approved'",
            ),
            core.Drift("some/file.py", "doctor.git-dirty", "dirty"),
            core.Drift("some/file.py", "doctor.git-staged", "staged"),
        ]
        primary, actions = doctor.resolve_next_actions(advisory_drifts, Path("."))
        self.assertIsNone(primary)
        self.assertEqual(actions, [])

    def test_remediation_name_nonconformant_clustered_and_freeform(self) -> None:
        """E-01/V-01: name-nonconformant is advisory; clustered location names id6 selector (not path)
        plus --slug and --apply; free-form location names --to-id6; plans location never names path."""
        root = Path(".")
        # Clustered backlog location
        d_clustered_backlog = core.Drift(
            ".aw/records/backlog/open/20260908-demo-01-aaa111-a-truncated-slug-.backlog.md",
            "check.name-nonconformant",
            "bad name",
        )
        rem_cb = doctor.build_remediation(d_clustered_backlog, root)
        self.assertIsNone(rem_cb.command)
        self.assertIn("aaa111", rem_cb.detailed_fix)
        self.assertIn("--slug <corrected-slug>", rem_cb.detailed_fix)
        self.assertIn("--apply", rem_cb.detailed_fix)
        self.assertIn("human decision", rem_cb.detailed_fix)

        # Clustered plans location: must select by id6, never by path
        d_clustered_plans = core.Drift(
            ".aw/records/plans/pending/20260925-doctorhint-01-6k7xot-test.ipd.md",
            "check.name-nonconformant",
            "bad name",
        )
        rem_cp = doctor.build_remediation(d_clustered_plans, root)
        self.assertIsNone(rem_cp.command)
        self.assertIn("6k7xot", rem_cp.detailed_fix)
        self.assertIn("--slug <corrected-slug>", rem_cp.detailed_fix)
        self.assertIn("--apply", rem_cp.detailed_fix)
        self.assertNotIn(
            "aw rename plans .aw/records/plans/pending",
            rem_cp.detailed_fix,
        )

        # Free-form location (e.g. weird.ipd.md)
        d_freeform = core.Drift("weird.ipd.md", "check.name-nonconformant", "bad name")
        rem_ff = doctor.build_remediation(d_freeform, root)
        self.assertIsNone(rem_ff.command)
        self.assertIn("--to-id6", rem_ff.detailed_fix)
        self.assertIn("--apply", rem_ff.detailed_fix)

    def test_remediation_setid_collision(self) -> None:
        """E-02/V-02: setid-collision is advisory; detailed_fix contains --set, --rename, --apply,
        and uses id6 selector for plans."""
        root = Path(".")
        d_backlog = core.Drift(
            ".aw/records/backlog/open/20260908-demo-01-aaa111-item.backlog.md",
            "check.setid-collision",
            "collision",
        )
        rem_b = doctor.build_remediation(d_backlog, root)
        self.assertIsNone(rem_b.command)
        self.assertIn("--set <new-set-id>", rem_b.detailed_fix)
        self.assertIn("--rename", rem_b.detailed_fix)
        self.assertIn("--apply", rem_b.detailed_fix)

        d_plans = core.Drift(
            ".aw/records/plans/pending/20260925-doctorhint-01-6k7xot-test.ipd.md",
            "check.setid-collision",
            "collision",
        )
        rem_p = doctor.build_remediation(d_plans, root)
        self.assertIsNone(rem_p.command)
        self.assertIn("aw group plans 6k7xot", rem_p.detailed_fix)
        self.assertIn("--set <new-set-id>", rem_p.detailed_fix)
        self.assertIn("--rename", rem_p.detailed_fix)
        self.assertIn("--apply", rem_p.detailed_fix)

    def test_remediation_blocks_release_dangling(self) -> None:
        """E-03/V-03: blocks-release-dangling is advisory; names --status for backlog/specs,
        names aw ipd set (never aw plans set) for plans, and names no aw <type> set for types with no set verb."""
        root = Path(".")
        # backlog
        d_b = core.Drift(
            ".aw/records/backlog/open/item.backlog.md",
            "check.blocks-release-dangling",
            "dangling",
        )
        rem_b = doctor.build_remediation(d_b, root)
        self.assertIsNone(rem_b.command)
        self.assertIn("--blocks-release next", rem_b.detailed_fix)
        self.assertIn("--status <current-status>", rem_b.detailed_fix)

        # specs
        d_s = core.Drift(
            ".aw/records/specs/draft/item.spec.md",
            "check.blocks-release-dangling",
            "dangling",
        )
        rem_s = doctor.build_remediation(d_s, root)
        self.assertIsNone(rem_s.command)
        self.assertIn("--blocks-release next", rem_s.detailed_fix)
        self.assertIn("--status <current-status>", rem_s.detailed_fix)

        # plans: must name aw ipd set, never aw plans set
        d_p = core.Drift(
            ".aw/records/plans/pending/20260925-doctorhint-01-6k7xot-test.ipd.md",
            "check.blocks-release-dangling",
            "dangling",
        )
        rem_p = doctor.build_remediation(d_p, root)
        self.assertIsNone(rem_p.command)
        self.assertIn("aw ipd set", rem_p.detailed_fix)
        self.assertNotIn("aw plans set", rem_p.detailed_fix)
        self.assertIn("--blocks-release next", rem_p.detailed_fix)

        # releases / other types without a set verb
        d_r = core.Drift(
            ".aw/records/releases/planned/rel.release.md",
            "check.blocks-release-dangling",
            "dangling",
        )
        rem_r = doctor.build_remediation(d_r, root)
        self.assertIsNone(rem_r.command)
        self.assertNotIn("aw releases set", rem_r.detailed_fix)
        self.assertIn("'- Blocks-Release:'", rem_r.detailed_fix)

    def test_remediation_status_untooled(self) -> None:
        """E-04/V-04: status-untooled is advisory; detailed_fix names reverting hand edit AND aw ipd set."""
        root = Path(".")
        d = core.Drift(
            ".aw/records/plans/pending/20260925-doctorhint-01-6k7xot-test.ipd.md",
            "check.status-untooled",
            "status changed to 'approved' without history",
        )
        rem = doctor.build_remediation(d, root)
        self.assertIsNone(rem.command)
        self.assertIn("revert the hand edit", rem.detailed_fix)
        self.assertIn("aw ipd set", rem.detailed_fix)

    def test_remediation_git_dirty_and_staged(self) -> None:
        """E-05/V-05: git-dirty and git-staged are advisory for real paths and for <git> sentinel,
        naming aw commit and never emitting git commit."""
        root = Path(".")
        for rule in ("doctor.git-dirty", "doctor.git-staged"):
            for loc in ("src/foo.py", "<git>"):
                with self.subTest(rule=rule, loc=loc):
                    d = core.Drift(loc, rule, "uncommitted changes")
                    rem = doctor.build_remediation(d, root)
                    self.assertIsNone(rem.command)
                    self.assertIn("aw commit", rem.detailed_fix)
                    self.assertNotIn("git commit -m", rem.detailed_fix)


if __name__ == "__main__":
    unittest.main()

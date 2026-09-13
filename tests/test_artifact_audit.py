"""Tests for the ONE shared artifact location-and-status audit (`artifact_audit`, IPD 6ltz1y).

FIXTURE-BASED ON PURPOSE, following `tests/test_run_viewer.py`'s header hazard: every case below
builds the small record tree it needs. A test keyed to live repository state would be unrunnable in a
fresh clone and in every isolated lane worktree the runner allocates by default, which is exactly
where these tests actually run.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_audit, doctor, run_viewer


class OneImplementationTests(unittest.TestCase):
    """The extraction moved the predicate; it did not copy it.

    OBJECT IDENTITY, not behavioral equality, following `tests/test_runner_refork_guard.py`: a
    behavioral comparison passes against a duplicate, which is precisely the drift that produced
    `render_stream` and `evaluate_review_finding_escalation`.
    """

    def test_run_viewer_audit_type_is_the_shared_module_object(self):
        self.assertIs(run_viewer.StepArtifactAudit, artifact_audit.ArtifactAudit)

    def test_run_viewer_holds_no_local_audit_definition(self):
        """`run_viewer` must not re-define the predicate, the dataclass or the status pattern."""
        src = Path(run_viewer.__file__).read_text(encoding="utf-8")
        self.assertNotIn("class StepArtifactAudit", src)
        self.assertNotIn("_STATUS_LINE_RE = re.compile", src)
        # The only permitted mention of a search-directory list is gone with the private walk.
        self.assertNotIn('"plans" / "archive"', src)
        self.assertNotIn("search_dirs", src)

    def test_shared_module_does_not_import_run_viewer(self):
        """The dependency must stay one-directional, or the extraction recreates the coupling."""
        src = Path(artifact_audit.__file__).read_text(encoding="utf-8")
        self.assertNotIn("import run_viewer", src)
        self.assertNotIn("from agent_workflows.run_viewer", src)

    def test_shared_signature_takes_primitive_facts_not_a_step(self):
        """OQ-01: the shared predicate must not require a run-viewer `StepSummary`.

        Called with primitives ALONE (no step object anywhere), which is what makes a non-run
        consumer possible at all.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / ".aw" / "records" / "plans" / "executed"
            d.mkdir(parents=True)
            (d / "20260908-prim-01-pri001-x.ipd.md").write_text(
                "- Id: pri001\n- Status: executed\n"
            )
            audit = artifact_audit.audit_artifact(
                root, "pri001", "20260908-prim-01-pri001-x", status="executed"
            )
            self.assertFalse(audit.has_discrepancy)
            self.assertEqual(audit.actual_dir, "executed")

    def test_docstring_records_the_aw_check_decision(self):
        """E-05: the decision must live AT THE CODE, not only in a closed plan."""
        doc = artifact_audit.__doc__ or ""
        self.assertIn("aw check", doc)
        self.assertIn("GITIGNORED", doc)
        self.assertIn("IPD-M105", doc)
        # And it must say what WOULD make the rejected option viable.
        self.assertIn("tracked", doc)


class LookupDefectTests(unittest.TestCase):
    """The two measured defects in the extracted file lookup are fixed."""

    def _root(self, td):
        root = Path(td)
        (root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        return root

    def test_defect_one_type_set_backlog_record_is_now_found(self):
        """DEFECT ONE, THE TYPE SET: the old hardcoded list covered plans and specs ONLY, so a
        `backlog` record carrying the queried id6 returned None. Measured at HEAD before the change.
        """
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            b = root / ".aw" / "records" / "backlog" / "open"
            b.mkdir(parents=True)
            f = b / "20260901-typ-01-typ001-thing.backlog.md"
            f.write_text("- Id: typ001\n- Status: open\n")
            found = artifact_audit.find_artifact(root, "typ001")
            self.assertEqual(found.path, f)
            self.assertFalse(found.is_collision)

    def test_type_set_covers_every_record_type_not_just_plans_and_specs(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            made = {}
            for i, (rt, sub, facet) in enumerate(
                [
                    ("specs", "", "spec"),
                    ("backlog", "open", "backlog"),
                    ("releases", "", "release"),
                    ("roadmaps", "", "roadmap"),
                    ("walkthroughs", "", "walkthrough"),
                    ("prompts", "", "prompt"),
                ]
            ):
                d = (
                    root / ".aw" / "records" / rt / sub
                    if sub
                    else root / ".aw" / "records" / rt
                )
                d.mkdir(parents=True, exist_ok=True)
                id6 = f"ty{i:04d}"
                f = d / f"2026090{i + 1}-multi-0{i + 1}-{id6}-thing.{facet}.md"
                f.write_text(f"- Id: {id6}\n- Status: open\n")
                made[id6] = f
            for id6, path in made.items():
                self.assertEqual(
                    artifact_audit.find_artifact(root, id6).path,
                    path,
                    f"{id6} should resolve to {path}",
                )

    def test_monthly_shard_still_found_no_regression(self):
        """NO-REGRESSION ONLY, deliberately NOT framed as a defect fix.

        Review measured that the old code ALREADY found a monthly-sharded plan: `aw plans archive`
        writes `YYYYMM/` shards INSIDE the terminal dirs, those dirs were in the hardcoded list, and
        the loop `rglob`ed. So this asserts the behavior still WORKS after the change; asserting the
        old code could not find it would be false and the test would fail.
        """
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            shard = root / ".aw" / "records" / "plans" / "executed" / "202608"
            shard.mkdir(parents=True)
            f = shard / "20260801-shard-01-shd001-thing.ipd.md"
            f.write_text("- Id: shd001\n- Status: executed\n")
            self.assertEqual(artifact_audit.find_artifact(root, "shd001").path, f)
            # And the audit reads the DISPOSITION through the shard, not the month directory.
            audit = artifact_audit.audit_artifact(
                root, "shd001", status="executed", record_types=("plans",)
            )
            self.assertEqual(audit.actual_dir, "202608")
            self.assertEqual(audit.expected_dir, "executed")

    def test_defect_two_id6_collision_is_reported_not_silently_picked(self):
        """DEFECT TWO: the old loop returned the FIRST `id6 in p.name` hit with no collision policy.

        `selectors.resolve` calls an id6 multi-match "a data bug to fix, not overridable by --force"
        (`MATCH_ID6` is in `UNIQUE_KINDS`), and the shared lookup inherits that verdict.
        """
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            p = root / ".aw" / "records" / "plans" / "pending"
            a = p / "20260901-col-01-col001-one.ipd.md"
            b = p / "20260902-col-02-col001-two.ipd.md"
            a.write_text("- Id: col001\n- Status: approved\n")
            b.write_text("- Id: col001\n- Status: approved\n")
            found = artifact_audit.find_artifact(root, "col001")
            self.assertTrue(found.is_collision)
            self.assertIsNone(
                found.path, "a collision must NOT resolve to an arbitrary pick"
            )
            self.assertEqual(sorted(found.collisions), sorted([a, b]))
            # The audit surfaces it as `missing_entirely` WITH the collision list, never as a
            # confident verdict about one of the two candidates.
            audit = artifact_audit.audit_artifact(root, "col001", status="executed")
            self.assertTrue(audit.missing_entirely)
            self.assertEqual(len(audit.collisions), 2)

    def test_cross_type_id6_collision_is_reported(self):
        """A collision ACROSS types must not be masked by the type precedence order."""
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            plan = (
                root
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260901-x-01-xtp001-a.ipd.md"
            )
            plan.write_text("- Id: xtp001\n- Status: approved\n")
            sd = root / ".aw" / "records" / "specs"
            sd.mkdir(parents=True)
            spec = sd / "20260901-xtp001-01-xtp001-b.spec.md"
            spec.write_text("- Id: xtp001\n- Status: approved\n")
            found = artifact_audit.find_artifact(root, "xtp001")
            self.assertTrue(found.is_collision)
            self.assertIsNone(found.path)

    def test_exact_declared_id_beats_a_review_record_carrying_the_same_id6(self):
        """SUBSTRING VERSUS EXACT: the exact rule is what makes widening the type set SAFE.

        A review record carries its SUBJECT's id6 in its FILENAME by convention, and declares
        `- Subject-Id:` rather than `- Id:`. The old substring rule could not reach it only because
        the hardcoded list never searched `reviews/`; once the enumeration widens, the exact declared
        `- Id:` rule is what keeps a review from being returned as its own subject.
        """
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            plan = (
                root
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260901-rev-01-rvw001-subject.ipd.md"
            )
            plan.write_text("- Id: rvw001\n- Status: approved\n")
            rd = root / ".aw" / "records" / "reviews"
            rd.mkdir(parents=True)
            (rd / "20260903-rev-01-rvw001-review-of-subject.review.md").write_text(
                "- Subject-Id: rvw001\n- Status: complete\n"
            )
            found = artifact_audit.find_artifact(root, "rvw001")
            self.assertEqual(found.path, plan)
            self.assertEqual(found.kind, "id6")
            self.assertFalse(found.is_collision)

    def test_filename_tier_covers_a_declared_id_below_the_bounded_header(self):
        """The filename tier is REQUIRED, not a nicety.

        `selectors` reads a bounded 4096-byte header, and measured on this repository 268 of 1202
        records declare their `- Id:` BELOW that cap (this plan's own file declares it at byte 6485),
        so an exact-only lookup would report those as `missing_entirely`.
        """
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            p = root / ".aw" / "records" / "plans" / "pending"
            f = p / "20260901-deep-01-dep001-buried-id.ipd.md"
            f.write_text(
                "# IPD\n\n" + ("x" * 6000) + "\n- Id: dep001\n- Status: approved\n"
            )
            # The exact tier genuinely cannot see it...
            from agent_workflows import selectors

            header = selectors._read_header(f)
            self.assertIsNone(selectors._read_id(header or ""))
            # ...and the audit finds it anyway, via the clustered filename's id6 FIELD.
            found = artifact_audit.find_artifact(root, "dep001")
            self.assertEqual(found.path, f)
            self.assertEqual(found.kind, "filename-id6")

    def test_no_hardcoded_directory_list_remains(self):
        src = Path(artifact_audit.__file__).read_text(encoding="utf-8")
        for dead in (
            'repo_root / ".aw" / "records" / "plans" / "pending"',
            '"plans" / "archive"',
            'repo_root / ".agents" / "plans"',
        ):
            self.assertNotIn(dead, src)
        # It must go through the resolver's enumeration.
        self.assertIn("_sel._iter_paths", src)

    def test_index_is_invalidated_when_an_artifact_moves(self):
        """The traversal cache must not answer with a stale location after a lifecycle move."""
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            pend = root / ".aw" / "records" / "plans" / "pending"
            ex = root / ".aw" / "records" / "plans" / "executed"
            ex.mkdir(parents=True)
            f = pend / "20260901-mv-01-mov001-thing.ipd.md"
            f.write_text("- Id: mov001\n- Status: approved\n")
            self.assertEqual(artifact_audit.find_artifact(root, "mov001").path, f)
            moved = ex / f.name
            f.rename(moved)
            moved.write_text("- Id: mov001\n- Status: executed\n")
            self.assertEqual(artifact_audit.find_artifact(root, "mov001").path, moved)


class VerdictParityTests(unittest.TestCase):
    """The four verdict shapes and the live case, asserted on the SHARED predicate directly."""

    def test_four_verdict_shapes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pend = root / ".aw" / "records" / "plans" / "pending"
            ex = root / ".aw" / "records" / "plans" / "executed"
            pend.mkdir(parents=True)
            ex.mkdir(parents=True)

            (ex / "20260908-v-01-vcl001-x.ipd.md").write_text(
                "- Id: vcl001\n- Status: executed\n"
            )
            clean = artifact_audit.audit_artifact(root, "vcl001", status="executed")
            self.assertFalse(clean.has_discrepancy)

            (ex / "20260908-v-02-vlc002-x.ipd.md").write_text(
                "- Id: vlc002\n- Status: superseded\n"
            )
            loc = artifact_audit.audit_artifact(root, "vlc002", status="superseded")
            self.assertTrue(loc.location_mismatch)
            self.assertFalse(loc.status_mismatch)

            (ex / "20260908-v-03-vst003-x.ipd.md").write_text(
                "- Id: vst003\n- Status: approved\n"
            )
            st = artifact_audit.audit_artifact(root, "vst003", status="executed")
            self.assertFalse(st.location_mismatch)
            self.assertTrue(st.status_mismatch)

            missing = artifact_audit.audit_artifact(root, "vms004", status="executed")
            self.assertTrue(missing.missing_entirely)

    def test_liveness_is_carried_through_and_never_derived(self):
        """`is_live` is an INPUT (from a run dir's PID/lock holder) that this module only records."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pend = root / ".aw" / "records" / "plans" / "pending"
            pend.mkdir(parents=True)
            (pend / "20260908-lv-01-lvv001-x.ipd.md").write_text(
                "- Id: lvv001\n- Status: approved\n"
            )
            live = artifact_audit.audit_artifact(
                root, "lvv001", status="running", is_live=True
            )
            not_live = artifact_audit.audit_artifact(
                root, "lvv001", status="running", is_live=False
            )
            self.assertTrue(live.is_live)
            self.assertFalse(not_live.is_live)
            # A running step's plan in pending/ is NOT drift either way.
            self.assertFalse(live.has_discrepancy)
            self.assertFalse(not_live.has_discrepancy)

    def test_expected_dir_for_status_maps_every_disposition(self):
        self.assertEqual(artifact_audit.expected_dir_for_status("executed"), "executed")
        self.assertEqual(artifact_audit.expected_dir_for_status("complete"), "executed")
        self.assertEqual(
            artifact_audit.expected_dir_for_status("substantially-complete"), "executed"
        )
        self.assertEqual(
            artifact_audit.expected_dir_for_status("superseded"), "superseded"
        )
        self.assertEqual(
            artifact_audit.expected_dir_for_status("not-executed"), "not-executed"
        )
        self.assertEqual(artifact_audit.expected_dir_for_status("reusable"), "reusable")
        for pre in ("draft", "to-review", "reviewed", "approved", "queued", "running"):
            self.assertEqual(artifact_audit.expected_dir_for_status(pre), "pending")

    def test_multi_word_status_is_unreadable_by_design(self):
        """Parity with `selectors._STATUS_RE`: a multi-word status yields None, not a partial read."""
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "x.md"
            f.write_text("- Id: mww001\n- Status: EXECUTED (approved by maintainer)\n")
            self.assertIsNone(artifact_audit.read_declared_status(f))


class TrackedOnlyDoctorRuleTests(unittest.TestCase):
    """E-04 route (b): the doctor consumer reports only what a TRACKED file can answer alone."""

    def test_reports_the_ipd_m105_blind_spot(self):
        """A record in a terminal dir whose own status names a DIFFERENT disposition.

        This is what the rule ADDS: measured 2026-09-13, `ipd_lint.lint_file` on exactly this file
        returns disposition `legacy/not evaluated` with ZERO diagnostics, so `IPD-M105` cannot see it.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ex = root / ".aw" / "records" / "plans" / "executed"
            ex.mkdir(parents=True)
            f = ex / "20260908-bs-01-bls001-x.ipd.md"
            f.write_text("- Id: bls001\n- Status: superseded\n")

            audit = artifact_audit.audit_tracked_artifact(root, f)
            self.assertIsNotNone(audit)
            assert audit is not None
            self.assertEqual(audit.actual_dir, "executed")
            self.assertEqual(audit.expected_dir, "superseded")

            # And `IPD-M105` genuinely does NOT cover it, which is why this is not duplication.
            from agent_workflows import ipd_lint

            res = ipd_lint.lint_file(f)
            self.assertNotIn("IPD-M105", [d.code for d in res.diagnostics])

    def test_monthly_shard_is_climbed_to_its_disposition(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shard = root / ".aw" / "records" / "plans" / "executed" / "202608"
            shard.mkdir(parents=True)
            f = shard / "20260801-bs-02-bls002-x.ipd.md"
            f.write_text("- Id: bls002\n- Status: not-executed\n")
            audit = artifact_audit.audit_tracked_artifact(root, f)
            self.assertIsNotNone(audit)
            assert audit is not None
            self.assertEqual(audit.actual_dir, "executed")
            self.assertEqual(audit.expected_dir, "not-executed")

    def test_fails_safe_for_everything_that_could_be_in_flight(self):
        """FAIL SAFE, in `check_engine._receipt_is_live`'s direction: undeterminable means skip."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pend = root / ".aw" / "records" / "plans" / "pending"
            ex = root / ".aw" / "records" / "plans" / "executed"
            pend.mkdir(parents=True)
            ex.mkdir(parents=True)

            cases = {
                "clean executed": (
                    ex / "a.ipd.md",
                    "- Id: sfe001\n- Status: executed\n",
                ),
                "clean pending": (
                    pend / "b.ipd.md",
                    "- Id: sfe002\n- Status: approved\n",
                ),
                # A plan caught MID-FINALIZE (status written, file not yet moved). Also the
                # direction `IPD-M105` already owns.
                "mid-finalize": (
                    pend / "c.ipd.md",
                    "- Id: sfe003\n- Status: executed\n",
                ),
                "no status": (pend / "d.ipd.md", "- Id: sfe004\n"),
                "multi-word status": (
                    pend / "e.ipd.md",
                    "- Id: sfe005\n- Status: EXECUTED (by maintainer)\n",
                ),
            }
            for label, (p, body) in cases.items():
                p.write_text(body)
                self.assertIsNone(
                    artifact_audit.audit_tracked_artifact(root, p),
                    f"{label} must produce NO finding",
                )

    def test_doctor_probe_reports_an_in_flight_run_as_nothing(self):
        """THE IN-FLIGHT FIXTURE: a running step's plan must produce no doctor finding.

        Built as a FIXTURE, never from a live run record (those are gitignored and absent from a
        lane). The arrangement is the exact one a running execution leaves on disk: the plan sits in
        `pending/` carrying `approved`, while a run record elsewhere calls the step `running`.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pend = root / ".aw" / "records" / "plans" / "pending"
            pend.mkdir(parents=True)
            f = pend / "20260908-if-01-ifl001-in-flight.ipd.md"
            f.write_text("- Id: ifl001\n- Status: approved\n")

            findings = doctor.probe_artifact_audit(root)
            self.assertEqual(
                [d.location for d in findings],
                [],
                "an in-flight plan must produce no doctor finding",
            )
            # The RUN-shaped audit, given the same tree, also reports no drift for a live step,
            # which is the behavior the doctor consumer inherits.
            run_audit = artifact_audit.audit_artifact(
                root, "ifl001", status="running", is_live=True
            )
            self.assertFalse(run_audit.has_discrepancy)

    def test_doctor_probe_finds_the_blind_spot_case_as_an_advisory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ex = root / ".aw" / "records" / "plans" / "executed"
            ex.mkdir(parents=True)
            (ex / "20260908-ad-01-adv001-x.ipd.md").write_text(
                "- Id: adv001\n- Status: superseded\n"
            )
            findings = doctor.probe_artifact_audit(root)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].rule, "doctor.artifact-status-location-drift")
            # ADVISORY: `info` severity, so it cannot change the exit code on introduction.
            self.assertEqual(findings[0].severity, "info")

    def test_advisory_severity_does_not_fail_the_doctor_exit_code(self):
        """OQ-02: introduced as advisory, measured at ZERO findings on the live tree."""
        from agent_workflows import artifact_core

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ex = root / ".aw" / "records" / "plans" / "executed"
            ex.mkdir(parents=True)
            (ex / "20260908-ex-01-exc001-x.ipd.md").write_text(
                "- Id: exc001\n- Status: superseded\n"
            )
            findings = doctor.probe_artifact_audit(root)
            self.assertTrue(findings)
            self.assertEqual(artifact_core.drift_exit_code(findings), 0)

    def test_probe_skips_untracked_dirs_by_default(self):
        """`untracked/` is excluded by the probe, matching every other `aw doctor` artifact section.

        The fixture puts the disposition BELOW `untracked/` (`plans/untracked/executed/`) on purpose.
        The other arrangement, `plans/executed/untracked/`, produces no finding for an independent
        reason - `untracked` is then the record's parent directory and is not a disposition at all,
        so `audit_tracked_artifact` declines to judge it - which would make this test pass without
        exercising the exclusion.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            u = root / ".aw" / "records" / "plans" / "untracked" / "executed"
            u.mkdir(parents=True)
            (u / "20260908-un-01-unt001-x.ipd.md").write_text(
                "- Id: unt001\n- Status: superseded\n"
            )
            self.assertEqual(doctor.probe_artifact_audit(root), [])
            self.assertTrue(doctor.probe_artifact_audit(root, include_untracked=True))

    def test_doctor_report_carries_the_advisories_as_facts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ex = root / ".aw" / "records" / "plans" / "executed"
            ex.mkdir(parents=True)
            (ex / "20260908-rp-01-rpt001-x.ipd.md").write_text(
                "- Id: rpt001\n- Status: superseded\n"
            )
            report = doctor.collect_doctor_report(root)
            self.assertTrue(report.artifacts.audit_advisories)
            self.assertIn("audit_advisories", report.artifacts.to_dict())
            from agent_workflows import term as T

            rendered = doctor.render_human_report(report, T.Term(color=False))
            self.assertIn("Advisory:", rendered)
            self.assertIn("declared status disagrees with their directory", rendered)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

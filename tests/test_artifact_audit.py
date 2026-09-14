"""Tests for the ONE shared artifact location-and-status audit (`artifact_audit`, IPD 6ltz1y).

FIXTURE-BASED ON PURPOSE, following `tests/test_run_viewer.py`'s header hazard: every case below
builds the small record tree it needs. A test keyed to live repository state would be unrunnable in a
fresh clone and in every isolated lane worktree the runner allocates by default, which is exactly
where these tests actually run.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_audit, doctor, run_viewer, runner_shared


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


# --------------------------------------------------------------------------------------------------
# The DIRECTIONAL CLASSIFICATION (IPD `zexed1`)
#
# THROWAWAY REPOSITORIES ONLY. A case needing git evidence runs `git init` in a temporary directory and
# makes its own commits; NOTHING here reads this repository's history or `.aw/records/runs/`. Both are
# hazards this file's header and `tests/test_run_viewer.py:22-27` already name: run records are
# gitignored and absent from a fresh worktree, and a test keyed to the developer's own git history
# passes or fails depending on whose machine it runs on.
# --------------------------------------------------------------------------------------------------


def _git(root: Path, *args: str) -> str:
    """Run git in a THROWAWAY repository, returning stdout. Raises on failure (a broken fixture)."""
    proc = subprocess.run(
        ["git", *args],
        cwd=str(root),
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout.strip()


def _init_repo(root: Path) -> None:
    _git(root, "init", "--quiet", "-b", "main")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "user.name", "fixture")
    _git(root, "config", "commit.gpgsign", "false")


def _commit(root: Path, subject: str, *, touch: str = "f.txt") -> str:
    """Commit ``subject`` with no hooks (a fixture repo has none) and return the new HEAD."""
    p = root / touch
    p.write_text((p.read_text() if p.exists() else "") + subject + "\n")
    _git(root, "add", "--", touch)
    _git(root, "commit", "--quiet", "--no-verify", "-m", subject)
    return _git(root, "rev-parse", "HEAD")


def _plan(root: Path, disposition: str, id6: str, status: str, extra: str = "") -> Path:
    d = root / ".aw" / "records" / "plans" / disposition
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"20260908-cls-01-{id6}-a-slug.ipd.md"
    f.write_text(f"# IPD: a slug\n\n{extra}- Id: {id6}\n- Status: {status}\n")
    return f


class ForwardDirectionDerivationTests(unittest.TestCase):
    """The forward set is DERIVED from the status-to-directory mapping, never enumerated (PR-201)."""

    def test_the_two_dominant_false_alarm_statuses_are_forward_without_being_named(
        self,
    ):
        """`reviewed` and `queued` are 325 of the 508 measured rows and are forward for a REASON.

        Both come from `initialize_run`'s DERIVED queue status rather than an observation, so neither
        means the run finished the item. The point of this test is that the code does not NAME them: it
        asks whether the status expected the artifact in `pending/`.
        """
        for status in ("reviewed", "queued", "integration-blocked"):
            with self.subTest(status=status):
                self.assertTrue(artifact_audit.run_status_is_nonterminal(status))
        for status in (
            "executed",
            "complete",
            "superseded",
            "not-executed",
            "reusable",
        ):
            with self.subTest(status=status):
                self.assertFalse(artifact_audit.run_status_is_nonterminal(status))

    def test_every_driver_terminal_state_is_classified(self):
        """Anti-drift, in the style of `runner_shutdown.KNOWN_ITEM_STATUSES`.

        A driver adding a queue status must not silently acquire an undefined direction here. This is
        why the forward test is derived from `expected_dir_for_status` (which has a total fallback)
        rather than from a list that could omit a new value.
        """
        from agent_workflows import agy_runipd, oc_runipd

        for mod in (oc_runipd, agy_runipd):
            for status in mod.TERMINAL_STATES | {"queued", "running", "interrupted"}:
                with self.subTest(driver=mod.__name__, status=status):
                    self.assertIsInstance(
                        artifact_audit.run_status_is_nonterminal(status), bool
                    )
                    self.assertIn(
                        artifact_audit.expected_dir_for_status(status),
                        {
                            "pending",
                            "executed",
                            "superseded",
                            "not-executed",
                            "reusable",
                        },
                    )


class DifferenceClassificationTests(unittest.TestCase):
    """The eight cases IPD `zexed1` E-06 requires, each on its own fixture."""

    def test_case_a_forward_with_in_range_evidence_is_resolved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            base = _commit(root, "chore: base")
            _plan(root, "executed", "resa01", "executed")
            _commit(root, "lifecycle(resa01): finalize resa01 -> executed")

            idx = artifact_audit.build_finalize_evidence_index(root)
            audit = artifact_audit.audit_artifact(
                root, "resa01", status="reviewed", evidence=idx, ending_head=base
            )
            self.assertTrue(audit.has_discrepancy)
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_RESOLVED)
            self.assertIsNotNone(audit.evidence_commit)
            self.assertFalse(audit.is_alarming)

    def test_case_b_forward_without_evidence_is_unknown_not_resolved(self):
        """THE CASE THAT MATTERS MOST: the hand-edit bypass.

        `- Status: executed` plus `git mv` with NO `lifecycle(<id6>): finalize` commit is BYTE-IDENTICAL
        to a legitimate finalize in every field this audit reads. Classifying it `resolved` would print
        a reassuring verdict for exactly the bypass `hooks/executed_transition_gate` exists to catch,
        which is why the previous direction-only design was abandoned on a 2026-09-05 maintainer ruling.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            base = _commit(root, "chore: base")
            _plan(root, "executed", "hnd001", "executed")
            _commit(root, "docs: hand-edited a plan into executed/ with no finalize")

            idx = artifact_audit.build_finalize_evidence_index(root)
            audit = artifact_audit.audit_artifact(
                root, "hnd001", status="reviewed", evidence=idx, ending_head=base
            )
            self.assertNotEqual(audit.difference_class, artifact_audit.CLASS_RESOLVED)
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_UNKNOWN)
            self.assertEqual(audit.class_reason, artifact_audit.UNKNOWN_NO_EVIDENCE)
            self.assertIsNone(audit.evidence_commit)

    def test_case_c_recorded_success_but_not_terminal_is_regressed_and_alarming(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            _plan(root, "pending", "reg001", "approved")

            idx = artifact_audit.build_finalize_evidence_index(root)
            audit = artifact_audit.audit_artifact(
                root, "reg001", status="executed", evidence=idx, ending_head="HEADLESS"
            )
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_REGRESSED)
            self.assertTrue(audit.is_alarming)

    def test_case_d_missing_artifact_is_missing_and_alarming(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            idx = artifact_audit.build_finalize_evidence_index(root)
            audit = artifact_audit.audit_artifact(
                root, "mis001", status="executed", evidence=idx
            )
            self.assertTrue(audit.missing_entirely)
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_MISSING)
            self.assertTrue(audit.is_alarming)

    def test_case_e_agreement_is_unchanged_and_not_an_issue(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            _plan(root, "executed", "unc001", "executed")
            idx = artifact_audit.build_finalize_evidence_index(root)
            audit = artifact_audit.audit_artifact(
                root, "unc001", status="executed", evidence=idx
            )
            self.assertFalse(audit.has_discrepancy)
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_UNCHANGED)
            self.assertFalse(audit.is_alarming)

    def test_case_f_git_unavailable_is_unknown_with_a_reason(self):
        """NOT a git repository at all: every row is `unknown`, never a quiet pass."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)  # deliberately NOT `git init`ed
            _plan(root, "executed", "nog001", "executed")
            idx = artifact_audit.build_finalize_evidence_index(root)
            self.assertFalse(idx.available)
            audit = artifact_audit.audit_artifact(
                root, "nog001", status="reviewed", evidence=idx, ending_head="abc123"
            )
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_UNKNOWN)
            self.assertIn("git history could not be read", audit.class_reason)

    def test_case_g_retirement_with_a_banner_and_no_finalize_commit_is_retired(self):
        """A RETIREMENT CANNOT EARN `resolved`, and demanding it would be a defect (PR-205).

        Retirement writes NO `lifecycle(<id6>): finalize` commit: history carried 190 finalize subjects
        against ONE retire at review, while 82 of the 508 rows sat in `superseded/`/`not-executed/`. Its
        evidence is the record's own `RETIRED` banner plus a `- Status:` agreeing with its directory.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            base = _commit(root, "chore: base")
            _plan(
                root,
                "superseded",
                "ret001",
                "superseded",
                extra="RETIRED 2026-09-08: replaced by a better plan.\n\n",
            )
            _commit(root, "records: retire a plan")

            idx = artifact_audit.build_finalize_evidence_index(root)
            self.assertEqual(idx.finalize_commits.get("ret001"), None)
            audit = artifact_audit.audit_artifact(
                root, "ret001", status="reviewed", evidence=idx, ending_head=base
            )
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_RETIRED)
            self.assertFalse(audit.is_alarming)
            self.assertIsNone(audit.evidence_commit)

    def test_a_complete_run_status_against_a_retirement_is_still_retired(self):
        """THE SIX MEASURED ROWS OF PR-205, which are not forward at all.

        Those rows recorded run status `complete` against a `superseded/` artifact (`qcqhj7`, `rchpms`,
        `7p9n2v`, `58ha43`, `2c122z`, `bmh754`), and every one carried a legitimate `RETIRED` banner. A
        retirement's evidence is its own banner, so the class must NOT be gated on a forward run status;
        measured on a fixture corpus, putting the direction gate in front of the retirement test dropped
        this shape through to `unknown`, and under the item's original rule it would have been RED.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            _plan(
                root,
                "superseded",
                "cmp001",
                "superseded",
                extra="RETIRED 2026-09-08: replaced.\n\n",
            )
            idx = artifact_audit.build_finalize_evidence_index(root)
            audit = artifact_audit.audit_artifact(
                root, "cmp001", status="complete", evidence=idx, ending_head="x"
            )
            self.assertFalse(artifact_audit.run_status_is_nonterminal("complete"))
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_RETIRED)
            self.assertFalse(audit.is_alarming)

    def test_a_retirement_without_a_banner_is_unknown_not_retired(self):
        """The banner is EVIDENCE, so its absence must not be waved through."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            _plan(root, "superseded", "nbn001", "superseded")  # no banner
            idx = artifact_audit.build_finalize_evidence_index(root)
            audit = artifact_audit.audit_artifact(
                root, "nbn001", status="reviewed", evidence=idx, ending_head="x"
            )
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_UNKNOWN)
            self.assertIn("no RETIRED banner", audit.class_reason)

    def test_case_h_absent_ending_head_is_unknown_with_that_specific_reason(self):
        """An absent bound is an `unknown`, NEVER a fallback to the unbounded check.

        Measured at review, 52 of 491 attempts in older run records carry no `ending_head`. Those rows
        are genuinely unprovable, and answering them with a weaker question would be the same mistake
        as never bounding the search.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            _plan(root, "executed", "noh001", "executed")
            _commit(root, "lifecycle(noh001): finalize noh001 -> executed")

            idx = artifact_audit.build_finalize_evidence_index(root)
            self.assertTrue(idx.finalize_commits.get("noh001"))  # the commit IS there
            audit = artifact_audit.audit_artifact(
                root, "noh001", status="reviewed", evidence=idx, ending_head=""
            )
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_UNKNOWN)
            self.assertEqual(audit.class_reason, artifact_audit.UNKNOWN_NO_ENDING_HEAD)

    def test_a_finalize_before_the_ending_head_is_unknown_not_resolved(self):
        """THE TIME BOUND ITSELF (PR-203), the viewer's analogue of the gate's own bound test.

        `tests/test_executed_transition_gate.py::test_finalize_commit_already_on_head_is_not_evidence`
        exists because an OLD finalize must not authorize a NEW transition. Without this case the bound
        is untested, and an unbounded reachable-from-HEAD check would accept a plan that was finalized,
        hand-reverted to `pending/`, and hand-re-`git mv`d into `executed/`.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            _plan(root, "executed", "old001", "executed")
            _commit(root, "lifecycle(old001): finalize old001 -> executed")
            # The run recorded its status AFTER that finalize, so the finalize is out of range.
            ending = _commit(root, "chore: a later unrelated commit")
            _commit(root, "chore: one more so HEAD is not the bound itself")

            idx = artifact_audit.build_finalize_evidence_index(root)
            audit = artifact_audit.audit_artifact(
                root, "old001", status="reviewed", evidence=idx, ending_head=ending
            )
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_UNKNOWN)
            self.assertEqual(audit.class_reason, artifact_audit.UNKNOWN_NO_EVIDENCE)

    def test_an_unreachable_ending_head_says_so_rather_than_claiming_no_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            _plan(root, "executed", "unr001", "executed")
            _commit(root, "lifecycle(unr001): finalize unr001 -> executed")
            idx = artifact_audit.build_finalize_evidence_index(root)
            audit = artifact_audit.audit_artifact(
                root,
                "unr001",
                status="reviewed",
                evidence=idx,
                ending_head="0" * 40,  # a head this repository has never seen
            )
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_UNKNOWN)
            self.assertEqual(
                audit.class_reason, artifact_audit.UNKNOWN_HEAD_UNREACHABLE
            )

    def test_no_evidence_index_supplied_is_unknown_never_unchanged(self):
        """The DEFAULT is a confession. A construction site that supplies nothing cannot read clean."""
        audit = artifact_audit.ArtifactAudit(
            id6="def001", stem="s", run_status="reviewed"
        )
        self.assertEqual(audit.difference_class, artifact_audit.CLASS_UNKNOWN)
        self.assertEqual(audit.class_reason, artifact_audit.UNKNOWN_NOT_CLASSIFIED)

    def test_unknown_and_unchanged_are_distinct_values(self):
        """They mean OPPOSITE things: one is a positive finding, the other a confession."""
        self.assertNotEqual(
            artifact_audit.CLASS_UNKNOWN, artifact_audit.CLASS_UNCHANGED
        )
        self.assertNotIn(
            artifact_audit.CLASS_UNKNOWN, artifact_audit.SUPPRESSIBLE_CLASSES
        )
        self.assertNotIn(
            artifact_audit.CLASS_REGRESSED, artifact_audit.SUPPRESSIBLE_CLASSES
        )

    def test_an_unattributable_artifact_is_unknown_never_regressed(self):
        """The measured `nna8yz` -> `3i0aaz` MIS-RESOLUTION must not be slandered as lost work.

        `find_artifact`'s stem tier can hand back a file belonging to a DIFFERENT plan whose slug
        contains the queried id6. Under the narrowed `regressed` rule that row would be the only red one
        in the whole table, and it is a lookup defect (`6ltz1y` E-03 owns the fix), not a regression.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            d = root / ".aw" / "records" / "plans" / "pending"
            d.mkdir(parents=True)
            # A DIFFERENT plan (`3i0aaz`) whose SLUG contains the queried id6.
            (d / "20260907-dirtybase-01-3i0aaz-guard-nna8yz-cases.ipd.md").write_text(
                "- Id: 3i0aaz\n- Status: to-review\n"
            )
            idx = artifact_audit.build_finalize_evidence_index(root)
            audit = artifact_audit.audit_artifact(
                root, "nna8yz", stem="nna8yz", status="complete", evidence=idx
            )
            self.assertIsNotNone(audit.actual_path)
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_UNKNOWN)
            self.assertEqual(audit.class_reason, artifact_audit.UNKNOWN_UNATTRIBUTABLE)

    def test_the_tracked_only_doctor_route_carries_an_honest_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = _plan(root, "executed", "trk001", "superseded")
            audit = artifact_audit.audit_tracked_artifact(root, f)
            self.assertIsNotNone(audit)
            assert audit is not None
            self.assertEqual(audit.difference_class, artifact_audit.CLASS_UNKNOWN)
            self.assertEqual(audit.class_reason, artifact_audit.UNKNOWN_TRACKED_ONLY)


class MeasuredFalseAlarmShapeTests(unittest.TestCase):
    """ALL THREE dominant measured shapes go non-red, not just the four rows in the item (PR-201).

    Live counts at review: `('reviewed','executed','executed')` 172,
    `('queued','executed','executed')` 153, `('integration-blocked','executed','executed')` 4. A fix
    proven only on the last has proven almost nothing.
    """

    def test_all_three_shapes_classify_resolved_and_render_non_red(self):
        shapes = {
            "reviewed": "rvw777",
            "queued": "que777",
            "integration-blocked": "ibl777",
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            base = _commit(root, "chore: base")
            for id6 in shapes.values():
                _plan(root, "executed", id6, "executed")
                _commit(root, f"lifecycle({id6}): finalize {id6} -> executed")

            idx = artifact_audit.build_finalize_evidence_index(root)
            audits = []
            for run_status, id6 in shapes.items():
                audit = artifact_audit.audit_artifact(
                    root, id6, status=run_status, evidence=idx, ending_head=base
                )
                with self.subTest(run_status=run_status):
                    self.assertTrue(
                        audit.has_discrepancy,
                        "the row must still be a CANDIDATE: the published row set is unchanged",
                    )
                    self.assertEqual(
                        audit.difference_class, artifact_audit.CLASS_RESOLVED
                    )
                    self.assertFalse(audit.is_alarming)
                audits.append(audit)

            # And they are suppressed from the DEFAULT human table while their count is still reported.
            from agent_workflows.term import Term

            term = Term(color=False)
            default_txt = run_viewer.format_artifact_audit_summary(audits, term)
            self.assertIn("resolved 3", default_txt)
            self.assertNotIn("rvw777", default_txt)
            shown_txt = run_viewer.format_artifact_audit_summary(
                audits, term, all_classes=True
            )
            self.assertIn("rvw777", shown_txt)
            self.assertIn("que777", shown_txt)
            self.assertIn("ibl777", shown_txt)

    def test_no_case_asserts_the_stranded_lane_row_stays_red(self):
        """DELIBERATELY ABSENT, and this test records why (PR-202, OQ-04 resolved 2026-09-10).

        The row that once surfaced a stranded lane (`eulhzt`) measured `reviewed`/`executed`/`executed`
        with its finalize commit IN RANGE for both recording runs, i.e. BYTE-IDENTICAL in every field
        this audit reads to the 172 legitimate `reviewed` rows. A case keeping it red could only pass by
        re-reddening those 172, which is the defect this classification exists to remove. The maintainer
        accepted that trade knowingly; stranded-lane visibility is `pr5b0t`'s and `ys1dor`'s to rebuild.
        """
        src = Path(artifact_audit.__file__).read_text(encoding="utf-8")
        self.assertNotIn("eulhzt", src)
        self.assertNotIn(
            "E-item", src
        )  # this audit reads no E-item counts, and must not start


class EvidenceIndexTests(unittest.TestCase):
    def test_it_matches_the_subject_and_never_a_body_grep(self):
        """`--grep` matches the message BODY, which already produced one wrong measurement.

        The manual merge commits in this repository QUOTE the gate's demand in their bodies, so a body
        search matches them and a `head -1` hides the real finalize commit underneath. This index reads
        `%s` and compares the SUBJECT.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            # A commit whose BODY quotes the finalize subject but whose SUBJECT is something else.
            p = root / "note.txt"
            p.write_text("x\n")
            _git(root, "add", "--", "note.txt")
            _git(
                root,
                "commit",
                "--quiet",
                "--no-verify",
                "-m",
                "integrate(manual): merge a lane",
                "-m",
                "the hook demanded a 'lifecycle(bdy001): finalize' commit for it",
            )
            idx = artifact_audit.build_finalize_evidence_index(root)
            self.assertNotIn("bdy001", idx.finalize_commits)

    def test_it_keeps_every_match_not_just_the_first(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            _commit(root, "lifecycle(mny001): finalize mny001 -> executed")
            _commit(root, "lifecycle(mny001): finalize mny001 -> executed")
            idx = artifact_audit.build_finalize_evidence_index(root)
            self.assertEqual(len(idx.finalize_commits["mny001"]), 2)

    def test_a_nonzero_git_exit_is_unknown_not_a_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            idx = artifact_audit.build_finalize_evidence_index(root / "nonexistent")
            self.assertFalse(idx.available)
            commit, reason = idx.finalize_after("any001", "abc123")
            self.assertIsNone(commit)
            self.assertIn("git history could not be read", reason)

    def test_a_timeout_is_unknown_not_a_pass(self):
        """A wedged git must not hang an interactive read-only view, and must not pass either."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")

            real = runner_shared._run_git

            def _slow(repo, args, *, timeout=None):
                raise subprocess.TimeoutExpired(
                    cmd=["git", *args], timeout=timeout or 0
                )

            runner_shared._run_git = _slow  # type: ignore[assignment]
            try:
                idx = artifact_audit.build_finalize_evidence_index(root)
            finally:
                runner_shared._run_git = real  # type: ignore[assignment]
            self.assertFalse(idx.available)
            self.assertIn("TimeoutExpired", idx.unavailable_detail)

    def test_it_passes_an_explicit_timeout(self):
        seen: dict = {}

        real = runner_shared._run_git

        def _spy(repo, args, *, timeout=None):
            seen.setdefault("timeouts", []).append(timeout)
            return real(repo, args, timeout=timeout)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            _commit(root, "chore: base")
            runner_shared._run_git = _spy  # type: ignore[assignment]
            try:
                artifact_audit.build_finalize_evidence_index(root)
            finally:
                runner_shared._run_git = real  # type: ignore[assignment]
        self.assertTrue(seen["timeouts"])
        for t in seen["timeouts"]:
            self.assertEqual(t, artifact_audit.GIT_READ_TIMEOUT_SECONDS)

    def test_one_pass_answers_many_rows(self):
        """The cost property, asserted structurally rather than by timing.

        Timing assertions are flaky on shared CI, so this counts SUBPROCESS INVOCATIONS instead: two for
        the whole index (the log pass and the HEAD resolve), and ZERO more however many rows are then
        classified. That is the property that makes the difference between ~68ms and ~26s at 508 rows.
        """
        calls: list = []
        real = runner_shared._run_git

        def _count(repo, args, *, timeout=None):
            calls.append(args[0])
            return real(repo, args, timeout=timeout)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            base = _commit(root, "chore: base")
            ids = [f"row{n:03d}" for n in range(12)]
            for id6 in ids:
                _plan(root, "executed", id6, "executed")
                _commit(root, f"lifecycle({id6}): finalize {id6} -> executed")

            runner_shared._run_git = _count  # type: ignore[assignment]
            try:
                idx = artifact_audit.build_finalize_evidence_index(root)
                during_index = len(calls)
                for id6 in ids:
                    artifact_audit.audit_artifact(
                        root, id6, status="reviewed", evidence=idx, ending_head=base
                    )
                after_rows = len(calls)
            finally:
                runner_shared._run_git = real  # type: ignore[assignment]

        self.assertEqual(
            during_index, 2, "the index is ONE log pass plus ONE HEAD resolve"
        )
        self.assertEqual(
            after_rows, during_index, "classifying rows must spawn NO git at all"
        )


class SharedFinalizeSubjectTests(unittest.TestCase):
    """The `lifecycle(<id6>): finalize` subject is ONE definition with every reader pointing at it."""

    def test_the_producer_the_gate_and_the_viewer_share_one_definition(self):
        from agent_workflows import artifact_core, ipd_lifecycle
        from agent_workflows.hooks import executed_transition_gate

        self.assertEqual(
            artifact_core.finalize_commit_subject("abc123"),
            "lifecycle(abc123): finalize",
        )
        self.assertEqual(
            artifact_core.lifecycle_commit_prefix("abc123"), "lifecycle(abc123)"
        )
        # NO reader may re-encode the string. `artifact_core` itself is the one definition, so it is
        # excluded; every other module must construct it through these two functions.
        for mod in (ipd_lifecycle, executed_transition_gate, artifact_audit):
            src = Path(mod.__file__).read_text(encoding="utf-8")
            code = "\n".join(
                line
                for line in src.splitlines()
                # Prose in comments and docstrings names the subject freely; only CODE is pinned.
                if not line.lstrip().startswith("#")
            )
            with self.subTest(module=mod.__name__):
                self.assertNotIn('f"lifecycle({plan_id})', code)
                self.assertNotIn('"lifecycle(" +', code)

    def test_the_gate_still_accepts_a_real_finalize_subject(self):
        """The refactor must not have changed WHAT the gate matches, only where the string comes from."""
        from agent_workflows import artifact_core
        from agent_workflows.hooks import executed_transition_gate

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_repo(root)
            base = _commit(root, "chore: base")
            # The gate evaluates `HEAD..<incoming>`, i.e. the INCOMING side of a merge, so the finalize
            # commit must be off the current branch. Build it on a side branch, exactly as a lane does.
            _git(root, "checkout", "--quiet", "-b", "lane")
            incoming = _commit(
                root,
                artifact_core.finalize_commit_subject("gat001") + " gat001 -> executed",
            )
            _git(root, "checkout", "--quiet", "main")
            self.assertEqual(_git(root, "rev-parse", "HEAD"), base)
            self.assertTrue(
                executed_transition_gate._intree_finalize_evidence_ok(
                    root, "gat001", [incoming]
                )
            )
            self.assertFalse(
                executed_transition_gate._intree_finalize_evidence_ok(
                    root, "other1", [incoming]
                )
            )


class ClassRenderingTests(unittest.TestCase):
    """E-04: every class renders distinctly and NO unprovable row can be hidden."""

    def _audit(self, cls: str, reason: str, id6: str) -> artifact_audit.ArtifactAudit:
        a = artifact_audit.ArtifactAudit(
            id6=id6,
            stem=f"stem-{id6}",
            run_status="reviewed",
            location_mismatch=True,
            actual_dir="executed",
            expected_dir="pending",
            file_status="executed",
        )
        a.difference_class = cls
        a.class_reason = reason
        return a

    def test_one_row_of_each_class_renders_with_its_class_and_reason(self):
        from agent_workflows.term import Term

        rows = [
            self._audit(
                artifact_audit.CLASS_REGRESSED, "the finalize did not stick", "rga001"
            ),
            self._audit(
                artifact_audit.CLASS_MISSING,
                "no artifact found for this step",
                "msa001",
            ),
            self._audit(
                artifact_audit.CLASS_UNKNOWN,
                artifact_audit.UNKNOWN_NO_EVIDENCE,
                "unk001",
            ),
            self._audit(
                artifact_audit.CLASS_RESOLVED, "finalized after the run ended", "rsa001"
            ),
            self._audit(
                artifact_audit.CLASS_RETIRED, "retired with a RETIRED banner", "rta001"
            ),
        ]
        txt = run_viewer.format_artifact_audit_summary(rows, Term(color=False), True)
        for cls in (
            artifact_audit.CLASS_REGRESSED,
            artifact_audit.CLASS_MISSING,
            artifact_audit.CLASS_UNKNOWN,
            artifact_audit.CLASS_RESOLVED,
            artifact_audit.CLASS_RETIRED,
        ):
            with self.subTest(cls=cls):
                self.assertIn(cls, txt)
        self.assertIn("Why", txt)
        self.assertIn(artifact_audit.UNKNOWN_NO_EVIDENCE, txt)

    def test_only_regressed_and_missing_carry_the_alarming_color(self):
        from agent_workflows.term import Term

        term = Term(color=True)
        #: 256-color red, as `Term.color256(..., 196, bold=True)` actually emits it.
        red = "38;5;196"
        for cls in (artifact_audit.CLASS_REGRESSED, artifact_audit.CLASS_MISSING):
            txt = run_viewer.format_artifact_audit_summary(
                [self._audit(cls, "r", "aaa001")], term, True
            )
            with self.subTest(cls=cls, alarming=True):
                self.assertIn(red, txt)
        for cls in (
            artifact_audit.CLASS_UNKNOWN,
            artifact_audit.CLASS_RESOLVED,
            artifact_audit.CLASS_RETIRED,
        ):
            txt = run_viewer.format_artifact_audit_summary(
                [self._audit(cls, "r", "bbb001")], term, True
            )
            with self.subTest(cls=cls, alarming=False):
                self.assertNotIn(red, txt)

    def test_unknown_and_regressed_are_never_suppressed_by_default(self):
        from agent_workflows.term import Term

        rows = [
            self._audit(
                artifact_audit.CLASS_UNKNOWN,
                artifact_audit.UNKNOWN_NO_EVIDENCE,
                "unk002",
            ),
            self._audit(artifact_audit.CLASS_REGRESSED, "did not stick", "rga002"),
            self._audit(artifact_audit.CLASS_RESOLVED, "evidenced", "rsa002"),
            self._audit(artifact_audit.CLASS_RETIRED, "banner", "rta002"),
        ]
        txt = run_viewer.format_artifact_audit_summary(rows, Term(color=False))
        self.assertIn("stem-unk002", txt)
        self.assertIn("stem-rga002", txt)
        self.assertNotIn("stem-rsa002", txt)
        self.assertNotIn("stem-rta002", txt)
        # the suppressed rows are still COUNTED, and the flag that shows them is named
        self.assertIn("resolved 1", txt)
        self.assertIn("retired 1", txt)
        self.assertIn("--all-classes", txt)

    def test_all_four_named_unknown_reasons_can_reach_the_output(self):
        from agent_workflows.term import Term

        reasons = (
            artifact_audit.UNKNOWN_NO_EVIDENCE,
            artifact_audit.UNKNOWN_NO_ENDING_HEAD,
            artifact_audit.UNKNOWN_GIT_UNAVAILABLE,
            artifact_audit.UNKNOWN_UNATTRIBUTABLE,
            artifact_audit.UNKNOWN_HEAD_UNREACHABLE,
            artifact_audit.UNKNOWN_NO_DIRECTION,
        )
        for reason in reasons:
            txt = run_viewer.format_artifact_audit_summary(
                [self._audit(artifact_audit.CLASS_UNKNOWN, reason, "unk003")],
                Term(color=False),
            )
            with self.subTest(reason=reason):
                self.assertIn(reason, txt)

    def test_the_per_class_count_line_is_printed(self):
        from agent_workflows.term import Term

        rows = [
            self._audit(artifact_audit.CLASS_UNKNOWN, "r", "cnt001"),
            self._audit(artifact_audit.CLASS_UNKNOWN, "r", "cnt002"),
            self._audit(artifact_audit.CLASS_REGRESSED, "r", "cnt003"),
        ]
        txt = run_viewer.format_artifact_audit_summary(rows, Term(color=False))
        self.assertIn("artifact differences:", txt)
        self.assertIn("unknown 2", txt)
        self.assertIn("regressed 1", txt)


class OneIssuePredicateTests(unittest.TestCase):
    def test_every_former_call_site_consults_one_definition(self):
        """E-05: ONE definition of "is this row an issue", not six hand-written copies.

        The boolean triple was tested in five places (the table's row selection, the steps table's
        `Issue` column, `--json`, `--agent`, and the `--issues` human path). None may re-spell it.
        """
        src = Path(run_viewer.__file__).read_text(encoding="utf-8")
        self.assertNotIn(
            "missing_entirely or a.location_mismatch or a.status_mismatch", src
        )
        self.assertNotIn("audit.missing_entirely or audit.location_mismatch", src)
        # And the one definition delegates to the shipped dataclass property rather than re-deriving.
        self.assertTrue(
            run_viewer.audit_row_is_issue(
                artifact_audit.ArtifactAudit(
                    id6="x", stem="x", run_status="executed", missing_entirely=True
                )
            )
        )
        self.assertFalse(
            run_viewer.audit_row_is_issue(
                artifact_audit.ArtifactAudit(id6="x", stem="x", run_status="executed")
            )
        )

    def test_the_published_row_set_is_unchanged(self):
        """The CLASS changes styling, never WHICH rows a machine consumer receives."""
        for kwargs in (
            {"missing_entirely": True},
            {"location_mismatch": True},
            {"status_mismatch": True},
            {},
        ):
            a = artifact_audit.ArtifactAudit(
                id6="x", stem="x", run_status="executed", **kwargs
            )
            with self.subTest(**kwargs):
                self.assertEqual(run_viewer.audit_row_is_issue(a), a.has_discrepancy)


class MachineRecordCompatibilityTests(unittest.TestCase):
    """PR-204: the three published booleans stay, the class is ADDED beside them."""

    def test_the_three_legacy_keys_survive_with_the_class_added(self):
        from dataclasses import asdict

        rec = asdict(
            artifact_audit.ArtifactAudit(id6="x", stem="x", run_status="executed")
        )
        for legacy in ("missing_entirely", "location_mismatch", "status_mismatch"):
            with self.subTest(key=legacy):
                self.assertIn(legacy, rec)
        for added in (
            "difference_class",
            "class_reason",
            "evidence_commit",
            "evidence_range_from",
        ):
            with self.subTest(key=added):
                self.assertIn(added, rec)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

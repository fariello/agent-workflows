"""Tests for revgate Order 01 (15zvu6): the typed review-findings foundation.

Covers the naming facet, the pure writer/parser, multi-round semantics, the optional Decisions
section, the configurable gate threshold, the shared `is_gating` predicate, the record-tree
registration, and the advisory dangling check.

Two of these are REGRESSION GUARDS for hazards found during plan review, and they are the reason this
module must not be weakened casually:

* ``TypeFacetHazardTests`` fails if someone adds a bare ``reviews`` entry to
  ``artifact_naming.TYPE_FACET`` without the matching ``status_set`` skip, which would make ``aw set``
  treat a review file as a status-settable artifact even though a review has no status lifecycle.
* ``ProjectJsonRoundTripTests`` fails if ``review_findings_gate`` ever stops surviving a
  ``project.json`` parse/serialize cycle, which would silently drop a repo's configured threshold.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_naming as naming
from agent_workflows import check_engine, config, project_schema
from agent_workflows import record_producers as rp
from agent_workflows import review_findings as rf
from agent_workflows import status_set


def _finding(
    fid: str = "PR-001",
    severity: str = "high",
    decision: str = "open",
    scope: str = "IN-SCOPE",
    area: str = "rubric 2.1",
    evidence: str = "agent_workflows/x.py:42",
    finding: str = "the thing is wrong",
    remediation_risk: str = "C:Low; U:Low; S:Low; F:Low; Overall:Low",
    resolution: str = "fixed in place",
) -> rf.Finding:
    return rf.Finding(
        id=fid,
        severity=severity,
        scope=scope,
        area=area,
        evidence=evidence,
        finding=finding,
        remediation_risk=remediation_risk,
        decision=decision,
        resolution=resolution,
    )


def _render(rounds, plan_id="15zvu6"):
    return rf.render_review(
        plan_id=plan_id,
        reviewed_at="2026-08-30",
        reviewer="opencode/test",
        verdict="APPROVE WITH REVISIONS APPLIED",
        rounds=rounds,
    )


# --------------------------------------------------------------------------------------
# E-01: the naming facet.
# --------------------------------------------------------------------------------------


class ReviewNamingTests(unittest.TestCase):
    def test_review_facet_is_registered(self) -> None:
        self.assertIn("review", naming.ARTIFACT_TYPE_FACETS)

    def test_existing_facets_unchanged(self) -> None:
        """The pre-existing facet set must be preserved exactly (only `review` was added)."""
        for facet in (
            "ipd",
            "prompt",
            "spec",
            "walkthrough",
            "roadmap",
            "backlog",
            "comms",
            "release",
            "other",
        ):
            self.assertIn(facet, naming.ARTIFACT_TYPE_FACETS)

    def test_build_and_parse_round_trip(self) -> None:
        name = rf.build_review_name(
            date="20260829",
            set_id="revgate",
            order=1,
            plan_id6="15zvu6",
            slug="typed-review-findings",
        )
        self.assertEqual(
            name, "20260829-revgate-01-15zvu6-typed-review-findings.review.md"
        )
        parts = rf.parse_review_name(name)
        assert parts is not None
        self.assertEqual(parts["id6"], "15zvu6")
        self.assertEqual(parts["set"], "revgate")
        self.assertEqual(parts["nn"], "01")
        self.assertEqual(parts["slug"], "typed-review-findings")

    def test_clustered_grammar_accepts_review_facet(self) -> None:
        name = "20260829-revgate-01-15zvu6-slug.review.md"
        m = naming.parse_clustered(name)
        self.assertIsNotNone(m)
        assert m is not None
        self.assertEqual(m.group("type"), "review")
        self.assertTrue(naming.is_clustered_conformant(name, "review"))

    def test_closed_enum_rejects_dotted_slug(self) -> None:
        """ADVERSARIAL (the stated reason the enum is closed): a dotted SLUG is not a facet."""
        for bad in (
            "20260829-revgate-01-15zvu6-foo.bar.md",
            "20260829-revgate-01-15zvu6-foo.reviewx.md",
            "20260829-revgate-01-15zvu6-foo.reviews.md",
            "20260829-revgate-01-15zvu6-foo.rev.md",
        ):
            self.assertIsNone(naming.parse_clustered(bad), bad)
            self.assertIsNone(rf.parse_review_name(bad), bad)

    def test_parse_review_name_rejects_other_types(self) -> None:
        """A plan is not a review; the parser must not blur the two."""
        self.assertIsNone(
            rf.parse_review_name("20260829-revgate-01-15zvu6-slug.ipd.md")
        )
        self.assertIsNone(rf.parse_review_name("20260829-revgate-01-15zvu6-slug.md"))


class TypeFacetHazardTests(unittest.TestCase):
    """F-8 guard: a `.review.md` must NOT look status-settable to `aw set`.

    A review's state is its Verdict plus per-finding Decision values, NOT a `- Status:` bullet, so it
    has no status lifecycle to transition. `status_set.detect_artifact_type` ITERATES
    `artifact_naming.TYPE_FACET` and returns the matched record type, so a bare `reviews` entry there
    would silently make `aw set` accept a review file. This test FAILS if that entry is added without
    the matching skip.
    """

    def test_reviews_absent_from_type_facet(self) -> None:
        self.assertNotIn(
            "reviews",
            naming.TYPE_FACET,
            "adding `reviews` to TYPE_FACET requires a matching skip in "
            "status_set.detect_artifact_type, or `aw set` will accept a review file",
        )

    def test_review_file_is_not_status_settable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "20260829-revgate-01-15zvu6-slug.review.md"
            path.write_text(_render([rf.Round(1, (_finding(),), ())]), encoding="utf-8")
            self.assertIsNone(status_set.detect_artifact_type(path, root))

    def test_plan_file_is_still_status_settable(self) -> None:
        """Control: the guard above must be specific to reviews, not broken detection generally."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "20260829-revgate-01-15zvu6-slug.ipd.md"
            path.write_text("# IPD: x\n\n- Id: 15zvu6\n", encoding="utf-8")
            self.assertEqual(status_set.detect_artifact_type(path, root), "plans")


# --------------------------------------------------------------------------------------
# E-02: writer/parser fidelity and the never-raise contract.
# --------------------------------------------------------------------------------------


class WriterParserTests(unittest.TestCase):
    def test_every_column_round_trips(self) -> None:
        f = _finding()
        doc = rf.parse_review_text(_render([rf.Round(1, (f,), ())]))
        self.assertEqual(doc.diagnostics, ())
        self.assertEqual(doc.plan_id, "15zvu6")
        self.assertEqual(doc.reviewed_at, "2026-08-30")
        self.assertEqual(doc.reviewer, "opencode/test")
        self.assertEqual(doc.verdict, "APPROVE WITH REVISIONS APPLIED")
        (got,) = doc.current_findings()
        for field in (
            "id",
            "severity",
            "scope",
            "area",
            "evidence",
            "finding",
            "remediation_risk",
            "decision",
            "resolution",
        ):
            self.assertEqual(getattr(got, field), getattr(f, field), field)

    def test_pipe_in_cell_is_escaped_and_recovered(self) -> None:
        f = _finding(finding="a | b | c")
        doc = rf.parse_review_text(_render([rf.Round(1, (f,), ())]))
        self.assertEqual(doc.diagnostics, ())
        self.assertEqual(doc.current_findings()[0].finding, "a | b | c")

    def test_multiple_findings_preserve_order(self) -> None:
        rows = tuple(
            _finding(fid="PR-%03d" % i, severity=s)
            for i, s in enumerate(("low", "medium", "high", "blocker"), start=1)
        )
        doc = rf.parse_review_text(_render([rf.Round(1, rows, ())]))
        self.assertEqual(
            [f.id for f in doc.current_findings()],
            ["PR-001", "PR-002", "PR-003", "PR-004"],
        )
        self.assertEqual(
            [f.severity for f in doc.current_findings()],
            ["low", "medium", "high", "blocker"],
        )

    def test_malformed_row_diagnoses_and_does_not_raise(self) -> None:
        text = (
            "# Plan review findings: abc123\n\n"
            "- Plan-Id: abc123\n- Reviewed-At: 2026-08-30\n"
            "- Reviewer: oc\n- Verdict: APPROVE\n\n"
            "## Round 1\n\n### Findings\n\n"
            "| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| PR-001 | high | IN | a | p:1 | good row | Low | open | todo |\n"
            "| PR-002 | far too few cells |\n"
            "| PR-003 | high | IN | a | p:1 | another good row | Low | fixed | done |\n"
        )
        doc = rf.parse_review_text(text)  # must not raise
        codes = [d.code for d in doc.diagnostics]
        self.assertIn(rf.D_MALFORMED_ROW, codes)
        # The GOOD rows around the bad one still parse: one bad row cannot blind a reader.
        self.assertEqual([f.id for f in doc.current_findings()], ["PR-001", "PR-003"])

    def test_unknown_severity_and_decision_are_diagnosed_not_coerced(self) -> None:
        text = (
            "- Plan-Id: abc123\n- Reviewed-At: 2026-08-30\n- Reviewer: oc\n"
            "- Verdict: APPROVE\n\n## Round 1\n\n### Findings\n\n"
            "| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| PR-001 | catastrophic | IN | a | p:1 | x | Low | maybe | y |\n"
        )
        doc = rf.parse_review_text(text)
        codes = [d.code for d in doc.diagnostics]
        self.assertIn(rf.D_UNKNOWN_SEVERITY, codes)
        self.assertIn(rf.D_UNKNOWN_DECISION, codes)
        (got,) = doc.current_findings()
        self.assertEqual(
            got.severity, "catastrophic"
        )  # preserved, not silently coerced
        self.assertFalse(got.severity_known)
        self.assertFalse(got.decision_known)

    def test_degenerate_inputs_never_raise(self) -> None:
        for text in ("", "\n\n", "not markdown at all", "## Round\n| | |", "|||"):
            doc = rf.parse_review_text(text)
            self.assertIsInstance(doc, rf.ReviewDocument)
            self.assertTrue(doc.diagnostics)

    def test_missing_metadata_is_diagnosed(self) -> None:
        doc = rf.parse_review_text("## Round 1\n\n### Findings\n\n")
        codes = [d.code for d in doc.diagnostics]
        self.assertIn(rf.D_MISSING_META, codes)

    def test_no_rounds_is_diagnosed(self) -> None:
        doc = rf.parse_review_text(
            "- Plan-Id: abc123\n- Reviewed-At: x\n- Reviewer: y\n- Verdict: z\n"
        )
        self.assertIn(rf.D_NO_ROUNDS, [d.code for d in doc.diagnostics])

    def test_file_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "20260829-revgate-01-15zvu6-slug.review.md"
            rf.write_review(
                path,
                plan_id="15zvu6",
                reviewed_at="2026-08-30",
                reviewer="oc",
                verdict="APPROVE",
                rounds=[rf.Round(1, (_finding(),), ())],
            )
            doc = rf.parse_review_file(path)
            self.assertEqual(doc.diagnostics, ())
            self.assertEqual(doc.plan_id, "15zvu6")
            self.assertEqual(doc.path, path)

    def test_unreadable_file_diagnoses_not_raises(self) -> None:
        doc = rf.parse_review_file(Path("/nonexistent/nope.review.md"))
        self.assertIn(rf.D_UNREADABLE, [d.code for d in doc.diagnostics])


# --------------------------------------------------------------------------------------
# E-03: rounds.
# --------------------------------------------------------------------------------------


class RoundTests(unittest.TestCase):
    def test_two_rounds_parse_and_current_is_last(self) -> None:
        r1 = rf.Round(
            1, (_finding(fid="PR-001", severity="high", decision="open"),), ()
        )
        r2 = rf.Round(
            2, (_finding(fid="PR-009", severity="low", decision="fixed"),), ()
        )
        doc = rf.parse_review_text(_render([r1, r2]))
        self.assertEqual(doc.diagnostics, ())
        self.assertEqual(len(doc.rounds), 2)
        current = doc.current_round()
        assert current is not None
        self.assertEqual(current.number, 2)
        self.assertEqual([f.id for f in doc.current_findings()], ["PR-009"])

    def test_superseded_finding_is_not_current(self) -> None:
        """The load-bearing case: a HIGH/open in round 1 that round 2 marks fixed must not gate."""
        r1 = rf.Round(
            1, (_finding(fid="PR-001", severity="high", decision="open"),), ()
        )
        r2 = rf.Round(
            2, (_finding(fid="PR-001", severity="high", decision="fixed"),), ()
        )
        doc = rf.parse_review_text(_render([r1, r2]))
        (cur,) = doc.current_findings()
        self.assertEqual(cur.decision, "fixed")
        self.assertTrue(cur.is_resolved)
        self.assertEqual(doc.unresolved_findings(), ())
        # Round 1 is still on record (history is not lost), it is simply not current.
        self.assertEqual(doc.rounds[0].findings[0].decision, "open")

    def test_unresolved_findings_excludes_only_fixed(self) -> None:
        rows = (
            _finding(fid="PR-001", decision="fixed"),
            _finding(fid="PR-002", decision="deferred"),
            _finding(fid="PR-003", decision="open"),
            _finding(fid="PR-004", decision="replan"),
        )
        doc = rf.parse_review_text(_render([rf.Round(1, rows, ())]))
        self.assertEqual(
            [f.id for f in doc.unresolved_findings()],
            ["PR-002", "PR-003", "PR-004"],
            "a DEFERRED finding is a deliberate decision not to fix, so it is unresolved",
        )

    def test_duplicate_round_number_is_diagnosed(self) -> None:
        text = _render([rf.Round(1, (_finding(),), ()), rf.Round(1, (_finding(),), ())])
        doc = rf.parse_review_text(text)
        self.assertIn(rf.D_DUPLICATE_ROUND, [d.code for d in doc.diagnostics])

    def test_single_round_document(self) -> None:
        doc = rf.parse_review_text(_render([rf.Round(1, (_finding(),), ())]))
        current = doc.current_round()
        assert current is not None
        self.assertEqual(current.number, 1)
        self.assertEqual(len(doc.current_findings()), 1)


# --------------------------------------------------------------------------------------
# E-08: the optional Decisions section.
# --------------------------------------------------------------------------------------


class DecisionsSectionTests(unittest.TestCase):
    def test_decisions_round_trip_every_column(self) -> None:
        d = rf.Decision(
            id="D-01",
            question="which TYPE_FACET option?",
            chosen="omit the entry",
            alternatives="add entry plus skip",
            basis="status_set.py:175 iterates the map",
            reversible="yes",
        )
        doc = rf.parse_review_text(_render([rf.Round(1, (_finding(),), (d,))]))
        self.assertEqual(doc.diagnostics, ())
        (got,) = doc.current_decisions()
        for field in (
            "id",
            "question",
            "chosen",
            "alternatives",
            "basis",
            "reversible",
        ):
            self.assertEqual(getattr(got, field), getattr(d, field), field)

    def test_no_decisions_section_parses_cleanly(self) -> None:
        """The section is OPTIONAL: absence is valid, not a silent requirement."""
        text = _render([rf.Round(1, (_finding(),), ())])
        self.assertNotIn("### Decisions", text)
        doc = rf.parse_review_text(text)
        self.assertEqual(doc.diagnostics, ())
        self.assertEqual(doc.current_decisions(), ())
        self.assertEqual(len(doc.current_findings()), 1)

    def test_malformed_decision_row_diagnoses(self) -> None:
        text = (
            "- Plan-Id: abc123\n- Reviewed-At: x\n- Reviewer: y\n- Verdict: z\n\n"
            "## Round 1\n\n### Findings\n\n"
            "| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| PR-001 | high | IN | a | p:1 | x | Low | open | y |\n\n"
            "### Decisions\n\n"
            "| ID | Question | Chosen | Alternatives considered | Basis | Reversible |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| D-01 | too few |\n"
        )
        doc = rf.parse_review_text(text)
        self.assertIn(rf.D_MALFORMED_ROW, [d.code for d in doc.diagnostics])
        self.assertEqual(doc.current_decisions(), ())
        self.assertEqual(len(doc.current_findings()), 1)

    def test_decisions_are_per_round(self) -> None:
        d1 = rf.Decision("D-01", "q1", "c1", "a1", "b1", "yes")
        d2 = rf.Decision("D-02", "q2", "c2", "a2", "b2", "no")
        doc = rf.parse_review_text(
            _render(
                [rf.Round(1, (_finding(),), (d1,)), rf.Round(2, (_finding(),), (d2,))]
            )
        )
        self.assertEqual([x.id for x in doc.current_decisions()], ["D-02"])
        self.assertEqual([x.id for x in doc.rounds[0].decisions], ["D-01"])


# --------------------------------------------------------------------------------------
# E-05: the configurable threshold and the shared predicate.
# --------------------------------------------------------------------------------------


class ThresholdTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_key(self, value) -> None:
        cfg = self.root / ".aw" / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "project.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "preset": "private-target",
                    "role": "target",
                    "review_findings_gate": value,
                }
            ),
            encoding="utf-8",
        )

    def test_absent_key_defaults_to_high(self) -> None:
        """FAIL-CLOSED default: no key means the gate is ACTIVE at `high`, not disabled."""
        self.assertEqual(config.findings_gate_threshold(self.root), "high")
        self.assertEqual(config.REVIEW_GATE_DEFAULT, "high")

    def test_explicit_values_are_honored(self) -> None:
        for value in ("medium", "high", "blocker", "off"):
            self._write_key({"block_at": value})
            self.assertEqual(config.findings_gate_threshold(self.root), value)

    def test_bare_string_is_tolerated(self) -> None:
        self._write_key("medium")
        self.assertEqual(config.findings_gate_threshold(self.root), "medium")

    def test_malformed_values_fall_back_to_high_without_raising(self) -> None:
        for value in (
            {"block_at": "nonsense"},
            {"block_at": 42},
            {},
            {"block_at": None},
        ):
            self._write_key(value)
            self.assertEqual(config.findings_gate_threshold(self.root), "high")

    def test_malformed_json_falls_back_to_high(self) -> None:
        cfg = self.root / ".aw" / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "project.json").write_text("{ not json", encoding="utf-8")
        self.assertEqual(config.findings_gate_threshold(self.root), "high")

    def test_non_object_project_json_falls_back_to_high(self) -> None:
        cfg = self.root / ".aw" / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "project.json").write_text("[1, 2, 3]", encoding="utf-8")
        self.assertEqual(config.findings_gate_threshold(self.root), "high")

    def test_key_is_not_in_config_schema(self) -> None:
        """F-10: the key rides in `unknown_fields`; registering it in CONFIG_SCHEMA is wrong."""
        self.assertNotIn(config.REVIEW_FINDINGS_GATE_KEY, config.CONFIG_SCHEMA)


class IsGatingTests(unittest.TestCase):
    def test_truth_table(self) -> None:
        expected = {
            ("low", "medium"): False,
            ("low", "high"): False,
            ("low", "blocker"): False,
            ("medium", "medium"): True,
            ("medium", "high"): False,
            ("medium", "blocker"): False,
            ("high", "medium"): True,
            ("high", "high"): True,
            ("high", "blocker"): False,
            ("blocker", "medium"): True,
            ("blocker", "high"): True,
            ("blocker", "blocker"): True,
        }
        for (sev, thr), want in expected.items():
            self.assertEqual(rf.is_gating(sev, thr), want, f"{sev} vs {thr}")

    def test_off_disables_everything(self) -> None:
        for sev in rf.SEVERITIES:
            self.assertFalse(rf.is_gating(sev, "off"))

    def test_unknown_inputs_do_not_gate(self) -> None:
        self.assertFalse(rf.is_gating("bogus", "high"))
        self.assertFalse(rf.is_gating("", "high"))
        self.assertFalse(rf.is_gating("high", ""))
        self.assertFalse(rf.is_gating("high", "bogus"))

    def test_case_and_whitespace_insensitive(self) -> None:
        self.assertTrue(rf.is_gating("  HIGH ", "High"))

    def test_severities_are_ordered_ascending(self) -> None:
        """`is_gating` compares by index, so the tuple order IS the semantics."""
        self.assertEqual(rf.SEVERITIES, ("low", "medium", "high", "blocker"))


class ProjectJsonRoundTripTests(unittest.TestCase):
    """F-10 guard: the key must survive a project.json parse/serialize cycle."""

    def test_key_survives_parse_and_serialize(self) -> None:
        data = {
            "schema_version": 2,
            "preset": "private-target",
            "role": "target",
            "review_findings_gate": {"block_at": "blocker"},
        }
        parsed = project_schema.parse_portable_policy(data)
        self.assertEqual(
            parsed.unknown_fields.get("review_findings_gate"), {"block_at": "blocker"}
        )
        out = parsed.to_dict()
        self.assertEqual(out.get("review_findings_gate"), {"block_at": "blocker"})


# --------------------------------------------------------------------------------------
# E-09: the record-tree registration.
# --------------------------------------------------------------------------------------


class RecordRegistrationTests(unittest.TestCase):
    def test_reviews_is_a_record_class(self) -> None:
        self.assertEqual(rp.RecordClass.REVIEWS.value, "reviews")
        self.assertIn("reviews", [c.value for c in rp.RecordClass])

    def test_resolve_record_path_resolves_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = rp.resolve_record_path("reviews", target_repo=tmp)
            self.assertEqual(Path(path).name, "reviews")

    def test_resolve_record_read_paths_resolves_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = rp.resolve_record_read_paths("reviews", target_repo=tmp)
            self.assertTrue(paths)
            self.assertEqual(Path(paths[0]).name, "reviews")

    def test_deep_cleanup_reaches_reviews(self) -> None:
        from agent_workflows import engine

        self.assertIn(".aw/records/reviews", engine._DEEP_CLEANUP_ROOTS)

    def test_installer_scaffolds_reviews_for_aw_layout_only(self) -> None:
        from agent_workflows import engine

        self.assertEqual(
            engine._record_scaffold_dirs("aw").get("reviews"), ".aw/records/reviews"
        )
        self.assertIsNone(
            engine._record_scaffold_dirs("legacy").get("reviews"),
            "reviews are net-new; mapping them into the legacy .agents/ tree would invent history",
        )

    def test_fresh_setup_creates_the_tree(self) -> None:
        from agent_workflows import engine

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            created = engine.create_setup_artifacts(root, use_git=False)
            self.assertIn(".aw/records/reviews/.gitkeep", created)
            self.assertTrue((root / ".aw" / "records" / "reviews").is_dir())

    def test_review_dirs_discovers_in_repo_tree(self) -> None:
        """A bare repo must still enumerate reviews, or the E-06 check would be vacuous."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".aw" / "records" / "reviews").mkdir(parents=True)
            dirs = rf.review_dirs(root)
            self.assertTrue(
                any(Path(d).name == "reviews" for d in dirs), f"got {dirs!r}"
            )


# --------------------------------------------------------------------------------------
# E-06: the advisory dangling check.
# --------------------------------------------------------------------------------------


class ReviewDanglingCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        (self.root / ".aw" / "records" / "reviews").mkdir(parents=True)
        (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260830-probe-01-aaa111-real.ipd.md"
        ).write_text("# IPD: real\n\n- Id: aaa111\n- Set: probe\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_review(self, plan_id: str, slug: str) -> Path:
        path = (
            self.root
            / ".aw"
            / "records"
            / "reviews"
            / f"20260830-probe-01-{plan_id}-{slug}.review.md"
        )
        return rf.write_review(
            path,
            plan_id=plan_id,
            reviewed_at="2026-08-30",
            reviewer="oc",
            verdict="APPROVE",
            rounds=[rf.Round(1, (_finding(),), ())],
        )

    def test_valid_review_does_not_fire(self) -> None:
        self._write_review("aaa111", "real")
        self.assertEqual(check_engine.check_review_dangling(self.root), [])

    def test_dangling_review_fires(self) -> None:
        self._write_review("zzz999", "ghost")
        drift = check_engine.check_review_dangling(self.root)
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0].rule, "check.review-dangling")
        self.assertIn("zzz999", drift[0].detail)

    def test_rule_is_advisory_not_error(self) -> None:
        """Deliberately a warning: a review of a superseded plan is untidy, not dangerous."""
        spec = check_engine.rule_spec("check.review-dangling")
        self.assertEqual(spec.severity, "warning")
        self.assertEqual(spec.determinism, check_engine.DET_DETERMINISTIC)
        self.assertIn("check.review-dangling", check_engine.RULE_REGISTRY)

    def test_does_not_over_fire_with_both_present(self) -> None:
        """Not vacuous AND not over-firing, proven in ONE repo state."""
        self._write_review("aaa111", "real")
        self._write_review("zzz999", "ghost")
        drift = check_engine.check_review_dangling(self.root)
        self.assertEqual(len(drift), 1)
        self.assertIn("zzz999", drift[0].location)

    def test_missing_plan_id_is_not_this_rules_business(self) -> None:
        path = (
            self.root
            / ".aw"
            / "records"
            / "reviews"
            / "20260830-probe-01-aaa111-nometa.review.md"
        )
        path.write_text("# no metadata here\n\n## Round 1\n", encoding="utf-8")
        self.assertEqual(check_engine.check_review_dangling(self.root), [])

    def test_empty_tree_is_silent(self) -> None:
        self.assertEqual(check_engine.check_review_dangling(self.root), [])

    def test_no_hardcoded_reviews_path_in_check_engine(self) -> None:
        """E-06 forbids a second path mechanism; discovery must go through the record authority.

        Checks the parsed AST's STRING LITERALS rather than raw text, so a comment or docstring that
        merely mentions the path (explaining why it is absent) does not trip the guard, while an
        actual hardcoded path literal does.
        """
        import ast

        src = Path(check_engine.__file__).read_text(encoding="utf-8")
        tree = ast.parse(src)
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    docstrings.add(doc)
        offenders = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "records/reviews" in node.value
            and node.value not in docstrings
        ]
        self.assertEqual(
            offenders,
            [],
            f"check_engine must not hardcode a reviews path; found {offenders!r}",
        )


if __name__ == "__main__":
    unittest.main()

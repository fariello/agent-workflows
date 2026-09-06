"""Spec review and the attested `to-review -> reviewed` transition (revsweep-04, `5slbpi`).

Covers, in the order the plan's E-items ship them:

* E-01/E-02: the `spec-review/` workflow package exists, is registered, honors the three prohibitions
  IN ITS TEXT, and does NOT fork the shared vocabularies (the anti-drift guard the package README
  promises).
* E-03: the manifest row exists and the two previously-false documentation claims are corrected.
* E-04: the `->reviewed` attestation. ONE shared predicate, BOTH setter spellings, the checker, the
  grandfathering of the existing corpus, and the F-10 approval-gate activation in both directions.
* E-05: specs enumeration for needs-review discovery, WITHOUT widening the default IPD-only sweep.

Stdlib unittest, zero deps.
"""

from __future__ import annotations

import argparse
import io
import re
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import check_engine
from agent_workflows import plan_readiness
from agent_workflows import review_findings as rf
from agent_workflows import run_selection_policy as policy
from agent_workflows import runner_shared as rs
from agent_workflows import specs, status_set

REPO = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO / ".aw" / "system" / "workflows"
PKG = WORKFLOWS / "spec-review"


def _args(**kw) -> argparse.Namespace:
    ns = argparse.Namespace()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def _set_args(path: Path, status: str, **kw) -> argparse.Namespace:
    base = dict(
        path=str(path),
        status=status,
        message="test",
        gate_kind=None,
        gate_ref=None,
        gate_summary=None,
        evidence=None,
        by_human=False,
        allow_open_questions=False,
        blocks_release=None,
        priority=None,
        work_kind=None,
        date="2026-09-06",
        commit=False,
        no_commit=True,
    )
    base.update(kw)
    return _args(**base)


def _spec_text(id6: str, status: str, *, title: str = "fixture") -> str:
    return (
        f"# Spec: {title}\n\n"
        f"- Date: 2026-09-06\n"
        f"- Status: {status}\n"
        f"- Id: {id6}\n"
        f"- Author: fixture\n\n"
        "## 1. Purpose\n\nA fixture spec.\n\n"
        "## Workflow history\n"
        f"- 2026-09-06 {status} (fixture): created.\n"
    )


def _write_spec(root: Path, id6: str, status: str, slug: str = "fixture-spec") -> Path:
    d = root / ".aw" / "records" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260906-{id6}-01-{id6}-{slug}.spec.md"
    p.write_text(_spec_text(id6, status), encoding="utf-8")
    return p


def _write_record(
    root: Path,
    subject_id: str,
    *,
    subject_type: str = "spec",
    severity: str = "low",
    decision: str = "fixed",
    verdict: str = "APPROVE WITH REVISIONS APPLIED",
    slug: str = "fixture-spec",
) -> Path:
    rnd = rf.Round(
        number=1,
        findings=(
            rf.Finding(
                id="SR-001",
                severity=severity,
                scope="in-scope",
                area="B",
                evidence="spec.md:9",
                finding="a finding",
                remediation_risk="Overall:Low",
                decision=decision,
                resolution="handled",
            ),
        ),
        decisions=(),
    )
    p = (
        root
        / ".aw"
        / "records"
        / "reviews"
        / rf.build_review_name(
            date="20260906", set_id="fixt", order=1, subject_id6=subject_id, slug=slug
        )
    )
    rf.write_review(
        p,
        subject_id=subject_id,
        subject_type=subject_type,
        reviewed_at="2026-09-06",
        reviewer="opencode fixture",
        verdict=verdict,
        rounds=[rnd],
    )
    return p


# --------------------------------------------------------------------------------------
# E-01 / E-02: the workflow package
# --------------------------------------------------------------------------------------


class WorkflowPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.body = (PKG / "spec-review.md").read_text(encoding="utf-8")
        self.readme = (PKG / "README.md").read_text(encoding="utf-8")
        # The bodies are HARD-WRAPPED prose, so a multi-word phrase can straddle a newline. Assert
        # phrases against a whitespace-collapsed view; otherwise the test pins the line-wrap rather
        # than the content and breaks on a harmless reflow.
        self.flat = " ".join(self.body.split())
        self.readme_flat = " ".join(self.readme.split())

    def test_package_exists_with_body_and_readme(self) -> None:
        self.assertTrue((PKG / "spec-review.md").is_file())
        self.assertTrue((PKG / "README.md").is_file())

    def test_readme_records_the_maintainer_ruling_with_its_evidence(self) -> None:
        """E-01: the ruling, its cited evidence, and the rejected option's cost are RECORDED.

        A decision recorded only in the plan is invisible to the next reader of the package, which is
        why E-01 requires it here as well.
        """
        self.assertIn("MAINTAINER RULING", self.readme_flat)
        self.assertIn("SEPARATE `spec-review/` package", self.readme_flat)
        # The three cited plan-only obligation sites, by line reference.
        for cite in (
            "plan-review.md:113-133",
            "plan-review.md:377-398",
            "plan-review.md:487-496",
        ):
            self.assertIn(cite, self.readme_flat, f"README must cite {cite}")
        # The rejected option's measured cost.
        self.assertIn("601", self.readme_flat)
        self.assertIn("SIX sites", self.readme_flat)

    def test_readme_states_the_single_sourced_record_constraint(self) -> None:
        """The one constraint the ruling does NOT relax (spec `6m4kow` Section 5)."""
        self.assertIn("review_findings", self.readme_flat)
        self.assertIn("SINGLE writer and parser", self.readme_flat)
        self.assertIn("plan_readiness.VERDICTS", self.readme_flat)
        self.assertIn("separate RECORD FORMAT is not", self.readme_flat)

    def test_readme_states_the_anti_drift_mitigation(self) -> None:
        """A fork's known cost is drift, so the mitigation must be inherited, not just the decision."""
        self.assertIn("Keeping this from drifting", self.readme_flat)
        self.assertIn("anti-fork guard is a test", self.readme_flat.lower())

    def test_body_forbids_all_three_prohibitions_explicitly(self) -> None:
        """E-02: each prohibition is a measured way `plan-review` would corrupt a spec (F-3)."""
        self.assertIn("Do NOT write `- Readiness:` onto a spec", self.flat)
        self.assertIn("Do NOT hand-edit `- Status:` or the workflow history", self.flat)
        self.assertIn("Do NOT run `aw ipd lint` against a spec", self.flat)
        # And the subtle half of (c): the guarded preflight would SKIP, not fail.
        self.assertIn("PASS BY NOT RUNNING", self.flat)

    def test_body_never_instructs_writing_readiness_or_editing_status(self) -> None:
        """The prohibitions must not be contradicted elsewhere in the body.

        Stated as a NEGATIVE assertion because a body can forbid something in one section and then
        casually instruct it in another; that is exactly the mis-taken-branch hazard the fork avoided.
        """
        # No instruction to write the field. Every mention must be a prohibition or a reference.
        for m in re.finditer(r"^.*- Readiness:.*$", self.body, re.MULTILINE):
            line = m.group(0)
            self.assertTrue(
                any(w in line for w in ("NOT", "not", "NEVER", "never", "prohibition")),
                f"body mentions Readiness without forbidding it: {line!r}",
            )

    def test_body_prescribes_the_spec_structural_gate_not_the_ipd_linter(self) -> None:
        self.assertIn("aw specs check", self.flat)
        # `aw ipd lint` appears ONLY in a prohibition or a reference, never as an instruction to run
        # it. Checked per-line over the RAW text (a line is the unit an agent acts on), with the
        # prohibition vocabulary spelled out so a reflow does not silently weaken the assertion.
        for m in re.finditer(r"^.*aw ipd lint.*$", self.body, re.MULTILINE):
            line = m.group(0)
            self.assertTrue(
                any(
                    w in line
                    for w in (
                        "NOT",
                        "not",
                        "NEVER",
                        "never",
                        "IPD-only",
                        "preflight",
                        "runs",
                    )
                ),
                f"body references `aw ipd lint` outside a prohibition: {line!r}",
            )

    def test_body_uses_the_tooled_transition(self) -> None:
        self.assertIn("aw specs set reviewed", self.flat)
        self.assertIn("aw specs note", self.flat)

    def test_body_asks_spec_questions_not_plan_questions(self) -> None:
        """A plan rubric applied to a spec produces findings about the wrong artifact."""
        low = self.flat.lower()
        for question in (
            "requirements are testable",
            "acceptance criteria cover",
            "decisions are recorded with rationale",
            "open questions are dispositioned",
        ):
            self.assertIn(question, low, f"rubric must ask: {question}")

    def test_body_does_not_apply_the_ipd_ev_rubric(self) -> None:
        """A spec has no `E-*`/`V-*` checklists, so demanding a bijection would be nonsense."""
        self.assertNotIn("E/V-bijection", self.flat)
        self.assertNotIn("E/V bijection", self.flat)

    def test_body_discloses_the_approval_gate_activation(self) -> None:
        """F-10: filing a record arms a live, no-override refusal. A reviewer must know."""
        self.assertIn("ARMS A LIVE GATE", self.flat)
        self.assertIn("NO override", self.flat)
        self.assertIn("subject_gating_blocks", self.flat)

    def test_body_states_the_attestation_honest_limit(self) -> None:
        """The attestation proves a review occurred, never that it was good (spec `25kzda` 6.1)."""
        self.assertIn("It does not prove the reviewer noticed every flaw", self.flat)

    def test_body_does_not_fork_the_shared_vocabularies(self) -> None:
        """THE ANTI-FORK GUARD the README promises. A copy is what drifts; a pointer is not.

        The body must NAME the shared authority rather than restating the closed vocabularies as its
        own definitions. Checked by requiring the shared-table section and the module names, and by
        forbidding the per-value DEFINITION prose that `plan-review` owns.
        """
        self.assertIn("What is SHARED and must not be re-stated here", self.flat)
        self.assertIn("review_findings.SEVERITIES", self.flat)
        self.assertIn("plan_readiness.VERDICTS", self.flat)
        self.assertIn("review_findings.is_gating", self.flat)
        # `plan-review` defines each severity with a prose gloss; this body must not duplicate them.
        self.assertNotIn("likely data loss, breach, normal-path failure", self.flat)
        self.assertNotIn("polish or small clarity improvement", self.flat)

    def test_body_verdicts_are_exactly_the_shared_four(self) -> None:
        """A spec-flavoured fifth verdict would fork `plan_readiness.VERDICTS` (rejected by ruling)."""
        for verdict in plan_readiness.VERDICTS:
            self.assertIn(verdict, self.flat)
        # And the record's verdict line must be readable by the shared classifier.
        polarity = plan_readiness.classify_verdict("APPROVE WITH REVISIONS APPLIED")[1]
        self.assertEqual(polarity, plan_readiness.POSITIVE)

    def test_history_line_this_workflow_writes_is_recognized_as_a_review(self) -> None:
        """F-9 as CORRECTED: a `/spec-review` entry is recognized whenever the status token is
        `reviewed`, which is what `aw specs set reviewed` writes. Verified rather than assumed.
        """
        entry = "- 2026-09-06 reviewed (oc): /spec-review round 1; APPROVE"
        self.assertTrue(plan_readiness.is_review_history_entry(entry))


class ManifestAndDocumentationTests(unittest.TestCase):
    """E-03: registration, and the correction of two claims that were already FALSE (F-4)."""

    def setUp(self) -> None:
        self.index = (WORKFLOWS / "index.md").read_text(encoding="utf-8")

    def test_manifest_row_registers_spec_review(self) -> None:
        from agent_workflows import engine

        rows = engine.parse_manifest(WORKFLOWS)
        by_command = {w.command: w for w in rows}
        self.assertIn("spec-review", by_command)
        self.assertEqual(
            by_command["spec-review"].body,
            ".aw/system/workflows/spec-review/spec-review.md",
        )

    def test_the_false_claim_is_corrected_everywhere_it_appeared(self) -> None:
        """F-4: the manifest and the prose BOTH said `plan-review` reviews specs. It never did.

        Leaving either while adding a real spec reviewer would give the repository two contradictory
        statements, which is worse than the single wrong one it had.
        """
        self.assertNotIn("interrogates and `plan-review` reviews", self.index)
        self.assertIn("interrogates and `spec-review` reviews", self.index)

    def test_generated_shims_exist_for_both_host_families(self) -> None:
        """F-11: there are TWO shim families, so "the shim" is not one file."""
        for fam in (".opencode", ".claude"):
            p = REPO / fam / "commands" / "spec-review.md"
            self.assertTrue(p.is_file(), f"missing generated shim {p}")

    def test_shims_are_generated_from_the_manifest_not_hand_written(self) -> None:
        """The description is COPIED VERBATIM from the manifest row, so a hand-edit would drift.

        Asserted by regenerating from the manifest and comparing to what is on disk: this is the same
        comparison `aw install` would make, so a hand-edited shim fails here.
        """
        from agent_workflows import engine

        rows = engine.parse_manifest(WORKFLOWS)
        generated = engine.generate_shim_members(rows, WORKFLOWS, target_layout="aw")
        for rel in (
            ".opencode/commands/spec-review.md",
            ".claude/commands/spec-review.md",
            ".opencode/commands/spec.md",
            ".claude/commands/spec.md",
        ):
            self.assertIn(rel, generated)
            self.assertEqual(
                (REPO / rel).read_text(encoding="utf-8"),
                generated[rel],
                f"{rel} drifted from what the manifest generates (hand-edited?)",
            )

    def test_no_generated_projection_to_compile_for_this_package(self) -> None:
        """F-12: `plan-review/` has no `_generated/`, and neither does `spec-review/`.

        Recorded as a test so a later reader does not claim `aw workflow check-generated` coverage for
        a package that has none.
        """
        self.assertFalse((PKG / "_generated").exists())
        self.assertFalse((WORKFLOWS / "plan-review" / "_generated").exists())


# --------------------------------------------------------------------------------------
# E-04: the attestation
# --------------------------------------------------------------------------------------


class AttestationPredicateTests(unittest.TestCase):
    def test_absent_record_is_a_reason_string(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            _write_spec(root, "aaa111", "to-review")
            reason = rf.review_attestation_missing(root, "aaa111", "spec")
            self.assertIsNotNone(reason)
            self.assertIn("aaa111", str(reason))

    def test_conforming_record_satisfies(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            _write_spec(root, "aaa111", "to-review")
            _write_record(root, "aaa111")
            self.assertIsNone(rf.review_attestation_missing(root, "aaa111", "spec"))

    def test_malformed_record_does_NOT_satisfy(self) -> None:
        """A record that exists but cannot be parsed proves nothing about what it says.

        The identical judgement is already made by `subject_gating_blocks` case (b). Accepting it here
        while that blocks on it would let one file be simultaneously good enough to attest a review
        and bad enough to block an approval.
        """
        with TemporaryDirectory() as d:
            root = Path(d)
            _write_spec(root, "aaa111", "to-review")
            p = _write_record(root, "aaa111")
            p.write_text(
                p.read_text(encoding="utf-8").replace("| low |", "| HGIH |"),
                encoding="utf-8",
            )
            self.assertTrue(rf.parse_review_file(p).diagnostics)
            reason = rf.review_attestation_missing(root, "aaa111", "spec")
            self.assertIsNotNone(reason)
            self.assertIn("does NOT parse", str(reason))

    def test_wrong_subject_type_does_NOT_satisfy(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            _write_spec(root, "aaa111", "to-review")
            _write_record(root, "aaa111", subject_type="ipd")
            reason = rf.review_attestation_missing(root, "aaa111", "spec")
            self.assertIsNotNone(reason)
            self.assertIn("different subject type", str(reason))

    def test_empty_id6_is_itself_a_refusal(self) -> None:
        """An artifact with no `- Id:` cannot be attested; permitting it would be the bypass."""
        with TemporaryDirectory() as d:
            reason = rf.review_attestation_missing(Path(d), "", "spec")
            self.assertIsNotNone(reason)
            self.assertIn("no `- Id:`", str(reason))

    def test_never_raises_on_an_unreadable_tree(self) -> None:
        reason = rf.review_attestation_missing(
            Path("/nonexistent/definitely/not/a/repo"), "aaa111", "spec"
        )
        self.assertIsNotNone(reason)

    def test_subject_review_records_includes_a_malformed_one(self) -> None:
        """A caller listing "what exists" must SEE a broken file, not have it vanish."""
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_record(root, "aaa111")
            p.write_text(
                p.read_text(encoding="utf-8").replace("| low |", "| HGIH |"),
                encoding="utf-8",
            )
            self.assertEqual(rf.subject_review_records(root, "aaa111"), (p,))


class OneSharedPredicateTests(unittest.TestCase):
    """R-12: one predicate, several call sites; never a second copy."""

    def test_both_setters_and_the_checker_consult_the_same_predicate(self) -> None:
        wanted = "review_attestation_missing"
        # The specs verb reaches it through the shared message helper.
        self.assertIn(wanted, Path(str(specs.__file__)).read_text(encoding="utf-8"))
        # The checker consults it directly.
        self.assertIn(
            wanted, Path(str(check_engine.__file__)).read_text(encoding="utf-8")
        )
        # `status_set` reaches it through `specs._review_attestation_refusal`, so the SHARED
        # message (and therefore the shared predicate) is what it consumes.
        self.assertIn(
            "_review_attestation_refusal",
            Path(str(status_set.__file__)).read_text(encoding="utf-8"),
        )

    def test_the_judgement_is_defined_exactly_once(self) -> None:
        """A grep for a second DEFINITION, which is the failure this requirement guards."""
        defs = 0
        for mod in (rf, specs, status_set, check_engine, policy, rs):
            src = Path(str(mod.__file__)).read_text(encoding="utf-8")
            defs += len(
                re.findall(r"^def review_attestation_missing\b", src, re.MULTILINE)
            )
        self.assertEqual(
            defs, 1, "the attestation predicate must be defined exactly once"
        )

    def test_the_refusal_message_is_defined_exactly_once(self) -> None:
        """Two wordings for one refusal is how two surfaces come to disagree."""
        defs = 0
        for mod in (specs, status_set):
            src = Path(str(mod.__file__)).read_text(encoding="utf-8")
            defs += len(
                re.findall(r"^def _review_attestation_refusal\b", src, re.MULTILINE)
            )
        self.assertEqual(defs, 1)


class SetterAttestationTests(unittest.TestCase):
    """Both CLI spellings are gated. A gate in one is bypassed by choosing the other."""

    def test_status_spelling_refuses_without_a_record_byte_identically(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "to-review")
            before = p.read_text(encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                rc = specs.run_set(_set_args(p, "reviewed"))
            self.assertEqual(rc, 1)
            self.assertEqual(p.read_text(encoding="utf-8"), before)
            msg = err.getvalue()
            self.assertIn("requires evidence that a review OCCURRED", msg)
            self.assertIn("recovery:", msg)
            self.assertIn("/spec-review", msg)

    def test_status_spelling_succeeds_with_a_record(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "to-review")
            _write_record(root, "aaa111")
            with redirect_stdout(io.StringIO()):
                rc = specs.run_set(_set_args(p, "reviewed"))
            self.assertEqual(rc, 0)
            text = p.read_text(encoding="utf-8")
            self.assertIn("- Status: reviewed", text)
            # The setter wrote the history record; nothing hand-edited it.
            self.assertIn("- 2026-09-06 reviewed (aw specs):", text)

    def test_positional_spelling_is_gated_too(self) -> None:
        """The `aw specs set reviewed <selector>` spelling routes to `status_set`, not `specs`."""
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "to-review")
            rec = status_set.read_artifact_record(p, root)
            assert rec is not None
            ok, reason = status_set.validate_transition_allowed(
                rec, "reviewed", _args(by_human=False, agent=True, json=False), root
            )
            self.assertFalse(ok)
            self.assertIn("requires evidence that a review OCCURRED", str(reason))

    def test_positional_spelling_clears_with_a_record(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "to-review")
            _write_record(root, "aaa111")
            rec = status_set.read_artifact_record(p, root)
            assert rec is not None
            ok, reason = status_set.validate_transition_allowed(
                rec, "reviewed", _args(by_human=False, agent=True, json=False), root
            )
            self.assertTrue(ok, reason)

    def test_a_no_op_reset_of_an_already_reviewed_spec_is_not_refused(self) -> None:
        """`old == new` is not a TRANSITION, so the authority table must not fire on it."""
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "reviewed")
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc = specs.run_set(_set_args(p, "reviewed"))
            self.assertEqual(rc, 0)

    def test_other_transitions_are_unaffected(self) -> None:
        """The new pressure applies to `->reviewed` ONLY."""
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "draft")
            with redirect_stdout(io.StringIO()):
                rc = specs.run_set(_set_args(p, "to-review"))
            self.assertEqual(rc, 0)
            self.assertIn("- Status: to-review", p.read_text(encoding="utf-8"))


class GrandfatheringTests(unittest.TestCase):
    """R-13: enforcement binds TRANSITIONS, so existing specs are never re-tested."""

    def test_an_approved_spec_with_no_record_is_untouched(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "approved")
            self.assertEqual(specs.validate_spec(p, p.read_text(encoding="utf-8")), [])
            self.assertEqual(check_engine.check_spec_review_attestation(root), [])

    def test_an_implemented_spec_with_no_record_is_untouched(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "implemented")
            self.assertEqual(specs.validate_spec(p, p.read_text(encoding="utf-8")), [])
            self.assertEqual(check_engine.check_spec_review_attestation(root), [])

    def test_every_real_spec_in_this_repository_still_conforms(self) -> None:
        """The measured guard on this plan's MAIN RISK: retroactive invalidation of the specs tree.

        Asserted over the REAL corpus rather than a fixture, because the risk is about the corpus.
        """
        offenders = []
        for path, text in check_engine._iter_spec_records(REPO):
            drift = specs.validate_spec(path, text)
            if drift:
                offenders.append((path.name, [d.rule for d in drift]))
        self.assertEqual(
            offenders, [], f"pre-existing specs became non-conforming: {offenders}"
        )

    def test_no_real_spec_trips_the_new_attestation_rule(self) -> None:
        self.assertEqual(
            [d.location for d in check_engine.check_spec_review_attestation(REPO)],
            [],
        )


class CheckerRuleTests(unittest.TestCase):
    """The checker half: a spec that reached `reviewed` some OTHER way (a hand edit)."""

    def test_hand_edited_reviewed_spec_is_flagged(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "reviewed")
            found = check_engine.check_spec_review_attestation(root)
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].rule, "check.spec-review-unattested")
            self.assertIn(str(p), found[0].location)

    def test_reviewed_spec_with_a_record_is_clean(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            _write_spec(root, "aaa111", "reviewed")
            _write_record(root, "aaa111")
            self.assertEqual(check_engine.check_spec_review_attestation(root), [])

    def test_rule_is_registered_as_an_error_with_its_invariant(self) -> None:
        """An UNREGISTERED id silently falls back to an EMPTY invariant, dropping the I-03 trace."""
        spec = check_engine.RULE_REGISTRY["check.spec-review-unattested"]
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec.invariant, "I-03")

    def test_the_finding_names_its_cause_and_its_recovery(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            _write_spec(root, "aaa111", "reviewed")
            drift = check_engine.check_spec_review_attestation(root)[0]
            blob = " ".join(
                str(v) for v in (drift.detail, getattr(drift, "recovery", ""))
            )
            self.assertIn("aaa111", blob)
            self.assertIn("spec-review", blob)

    def test_plans_are_NOT_made_stricter(self) -> None:
        """F-6: a missing review stays SILENT for plans (428 have none). Unchanged here."""
        with TemporaryDirectory() as d:
            root = Path(d)
            self.assertEqual(rf.subject_gating_blocks(root, "aaa111"), ())


class ApprovalGateActivationTests(unittest.TestCase):
    """F-10: filing the first spec-subject record ARMS an existing, no-override refusal.

    This is the largest behavior change the plan ships and it was invisible in the plan, so it is
    tested in BOTH directions rather than described.
    """

    def test_unfixed_high_finding_refuses_approval(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "reviewed")
            _write_record(
                root,
                "aaa111",
                severity="high",
                decision="deferred",
                verdict="REVIEWED - OPEN QUESTIONS",
            )
            refusals = plan_readiness.approval_refusals(
                root, p, p.read_text(encoding="utf-8")
            )
            self.assertTrue(refusals)
            self.assertTrue(any("unresolved gating finding" in r for r in refusals))

    def test_clean_record_does_not_refuse_approval(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "reviewed")
            _write_record(root, "aaa111", severity="high", decision="fixed")
            self.assertEqual(
                plan_readiness.approval_refusals(
                    root, p, p.read_text(encoding="utf-8")
                ),
                [],
            )

    def test_a_non_parsing_record_also_blocks_approval(self) -> None:
        """Any parse diagnostic is treated as BLOCKING, so a broken record blocks unfixably."""
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "reviewed")
            rec = _write_record(root, "aaa111")
            rec.write_text(
                rec.read_text(encoding="utf-8").replace("| low |", "| HGIH |"),
                encoding="utf-8",
            )
            refusals = plan_readiness.approval_refusals(
                root, p, p.read_text(encoding="utf-8")
            )
            self.assertTrue(any("malformed" in r for r in refusals))

    def test_the_refusal_has_no_override(self) -> None:
        """`--allow-open-questions` suppresses ONLY open questions, never a gating finding."""
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "reviewed")
            _write_record(root, "aaa111", severity="blocker", decision="open")
            refusals = plan_readiness.approval_refusals(
                root, p, p.read_text(encoding="utf-8"), allow_open_questions=True
            )
            self.assertTrue(any("unresolved gating finding" in r for r in refusals))

    def test_the_setter_surfaces_that_refusal(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "reviewed")
            _write_record(root, "aaa111", severity="high", decision="open")
            before = p.read_text(encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                rc = specs.run_set(_set_args(p, "approved", by_human=True))
            self.assertEqual(rc, 1)
            self.assertEqual(p.read_text(encoding="utf-8"), before)
            self.assertIn("refusing to approve", err.getvalue())


class VerdictSourcingTests(unittest.TestCase):
    """F-9 as CORRECTED: prove WHICH history record `newest_verdict` reads.

    The setter's own bare `- ... reviewed (aw specs): status set to reviewed` line ALSO qualifies as a
    review record and states NO verdict, so the real hazard is reading the verdict from the wrong
    record, not recognition of the `/spec-review` token.
    """

    def test_the_setters_bare_status_line_qualifies_as_a_review_record(self) -> None:
        self.assertTrue(
            plan_readiness.is_review_history_entry(
                "- 2026-09-06 reviewed (aw specs): status set to reviewed"
            )
        )

    def test_verdict_comes_from_the_review_message_not_a_bare_status_line(self) -> None:
        """So the review's own message MUST carry the verdict; the setter's `--message` is where."""
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "to-review")
            _write_record(root, "aaa111")
            with redirect_stdout(io.StringIO()):
                rc = specs.run_set(
                    _set_args(
                        p, "reviewed", message="APPROVE WITH REVISIONS APPLIED; SR-001"
                    )
                )
            self.assertEqual(rc, 0)
            polarity, entry = plan_readiness.newest_verdict(
                p.read_text(encoding="utf-8")
            )
            self.assertEqual(polarity, plan_readiness.POSITIVE)
            self.assertIn("APPROVE WITH REVISIONS APPLIED", entry)

    def test_a_bare_message_yields_NO_verdict_rather_than_a_false_positive(
        self,
    ) -> None:
        """Recorded so the limitation is known: a reviewer omitting the verdict records none."""
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "to-review")
            _write_record(root, "aaa111")
            with redirect_stdout(io.StringIO()):
                specs.run_set(
                    _set_args(p, "reviewed", message="status set to reviewed")
                )
            polarity, entry = plan_readiness.newest_verdict(
                p.read_text(encoding="utf-8")
            )
            self.assertIsNone(polarity)
            self.assertIn("aw specs", entry)


# --------------------------------------------------------------------------------------
# E-05: discovery
# --------------------------------------------------------------------------------------


class SpecDiscoveryTests(unittest.TestCase):
    def test_discovers_a_spec_with_its_status_and_relative_path(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_spec(root, "aaa111", "to-review")
            found = rs.discover_specs(root)
            self.assertIn("aaa111", found)
            rec = found["aaa111"]
            self.assertEqual(rec.status, "to-review")
            self.assertEqual(rec.file, str(p.relative_to(root)).replace("\\", "/"))

    def test_a_spec_without_an_id_is_skipped(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            dd = root / ".aw" / "records" / "specs"
            dd.mkdir(parents=True)
            (dd / "20260706-0000-01-legacy.spec.md").write_text(
                "# Spec: legacy\n\n- Date: 2026-07-06\n- Status: implemented\n\n"
                "## Workflow history\n- 2026-07-06 implemented (x): y.\n",
                encoding="utf-8",
            )
            self.assertEqual(rs.discover_specs(root), {})

    def test_absent_tree_yields_empty_and_never_raises(self) -> None:
        with TemporaryDirectory() as d:
            self.assertEqual(rs.discover_specs(Path(d)), {})
        self.assertEqual(rs.discover_specs(Path("/nonexistent/nope")), {})

    def test_no_new_records_path_literal_was_added(self) -> None:
        """Enumeration must go through the existing authority, not a fresh path string.

        `check_engine.check_review_dangling` deliberately avoids a second reviews-path literal; the
        same discipline applies to the specs tree here.
        """
        import ast

        src = Path(str(rs.__file__)).read_text(encoding="utf-8")
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
            and "records/specs" in node.value
            and node.value not in docstrings
        ]
        self.assertEqual(offenders, [], f"specs path literal added: {offenders!r}")

    def test_uses_the_shared_iterator(self) -> None:
        self.assertIn(
            "_iter_spec_records", Path(str(rs.__file__)).read_text(encoding="utf-8")
        )


class TypeScopedSweepTests(unittest.TestCase):
    def test_spec_type_resolves_a_to_review_spec(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            _write_spec(root, "aaa111", "to-review")
            self.assertEqual(
                rs.sweep_review_candidates_for_type(root, "spec"), ["aaa111"]
            )

    def test_a_spec_past_review_is_not_swept(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            _write_spec(root, "aaa111", "approved", slug="a")
            _write_spec(root, "bbb222", "implemented", slug="b")
            _write_spec(root, "ccc333", "reviewed", slug="c")
            self.assertEqual(rs.sweep_review_candidates_for_type(root, "spec"), [])

    def test_an_undetermined_draft_spec_is_NOT_swept(self) -> None:
        """No spec completeness parser exists yet, so a draft fails toward EXCLUSION."""
        with TemporaryDirectory() as d:
            root = Path(d)
            _write_spec(root, "aaa111", "draft")
            self.assertEqual(rs.sweep_review_candidates_for_type(root, "spec"), [])

    def test_a_terminal_directory_excludes_regardless_of_status(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            dd = root / ".aw" / "records" / "specs" / "superseded"
            dd.mkdir(parents=True)
            (dd / "20260906-aaa111-01-aaa111-x.spec.md").write_text(
                _spec_text("aaa111", "to-review"), encoding="utf-8"
            )
            self.assertEqual(rs.sweep_review_candidates_for_type(root, "spec"), [])

    def test_the_DEFAULT_sweep_is_still_IPD_ONLY(self) -> None:
        """Spec `25kzda` 2.4a property 1. Silently widening the default is the failure mode.

        `sweep_review_candidates` (the default entry point) is manifest-driven and can only contain
        what `discover_plans` produced, so a spec cannot appear in it. Asserted with a spec present.
        """
        with TemporaryDirectory() as d:
            root = Path(d)
            _write_spec(root, "aaa111", "to-review")
            self.assertEqual(rs.sweep_review_candidates({}, repo=root), [])

    def test_ipd_path_delegates_rather_than_forking(self) -> None:
        manifest = {
            "plans": {
                "pln001": {
                    "status": "to-review",
                    "file": ".aw/records/plans/pending/x.ipd.md",
                }
            },
            "sets": {},
        }
        with TemporaryDirectory() as d:
            root = Path(d)
            self.assertEqual(
                rs.sweep_review_candidates_for_type(root, "ipd", manifest=manifest),
                rs.sweep_review_candidates(manifest, repo=root),
            )

    def test_an_unknown_type_sweeps_nothing(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            _write_spec(root, "aaa111", "to-review")
            for t in ("backlog", "research", "prompt", "", "SPECS"):
                self.assertEqual(rs.sweep_review_candidates_for_type(root, t), [])

    def test_type_scoping_has_no_default(self) -> None:
        """A defaulted `spec_type` is how a later caller silently widens the default sweep."""
        import inspect

        sig = inspect.signature(rs.sweep_review_candidates_for_type)
        self.assertIs(sig.parameters["spec_type"].default, inspect.Parameter.empty)

    def test_membership_is_the_shared_predicate_not_a_copy(self) -> None:
        """R-16: the sweep and the dispatch table agree BY CONSTRUCTION, for specs too."""
        for status in (
            "to-review",
            "draft",
            "reviewed",
            "approved",
            "implemented",
            "parked",
        ):
            with TemporaryDirectory() as d:
                root = Path(d)
                _write_spec(root, "aaa111", status)
                swept = rs.sweep_review_candidates_for_type(root, "spec") == ["aaa111"]
                table = policy.needs_review("spec", status)
                self.assertEqual(
                    swept, table, f"sweep and table disagree at {status!r}"
                )


if __name__ == "__main__":
    unittest.main()

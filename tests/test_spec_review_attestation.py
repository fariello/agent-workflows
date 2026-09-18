"""Spec review and the attested `to-review -> reviewed` transition (revsweep-04, `5slbpi`).

Covers, in the order the plan's E-items ship them:

* E-01/E-02: the `spec-review/` workflow package exists, is registered, carries the LOAD-BEARING
  elements of the three prohibitions, and does NOT fork the shared vocabularies.
* E-03: the manifest row exists and the generated shims match what the manifest generates.
* E-04: the `->reviewed` attestation. ONE shared predicate, BOTH setter spellings, the checker, the
  grandfathering of the existing corpus, and the F-10 approval-gate activation in both directions.
* E-05: specs enumeration for needs-review discovery, WITHOUT widening the default IPD-only sweep.

WHY SO MANY TABLES: the attestation is a SECURITY GATE (an agent must not be able to forge a human
review), and a gate is defined by the whole set of (situation -> allowed/refused) pairs, not by any
one pair. A table states that set in one place and reports EVERY row that moved in one run, which is
the shape of the realistic regression here: a refactor of one shared predicate shifts several rows at
once. Positive (allowed) rows sit in the same tables as refusal rows on purpose, because a predicate
that refuses everything satisfies every refusal row on its own.

WHAT IS DELIBERATELY NOT PINNED: the workflow bodies' English prose. Wording pins fail on every
legitimate reword and catch no defect (git already records prose changes). Only tokens something
NON-HUMAN consumes verbatim are asserted, each row saying why it is load-bearing.

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


def _break_record(path: Path) -> None:
    """Corrupt a record's severity cell so the record EXISTS but does not parse."""
    path.write_text(
        path.read_text(encoding="utf-8").replace("| low |", "| HGIH |"),
        encoding="utf-8",
    )


# --------------------------------------------------------------------------------------
# E-01 / E-02: the workflow package
# --------------------------------------------------------------------------------------


class WorkflowPackageTests(unittest.TestCase):
    """The package exists and carries the elements a NON-HUMAN consumes verbatim.

    ONE table replaces eleven separate `assertIn` tests over the body and README. Those eleven were
    almost entirely PROSE PINS ("MAINTAINER RULING", "Keeping this from drifting", "SIX sites", "It
    does not prove the reviewer noticed every flaw", the three `plan-review.md:NNN-NNN` line cites,
    the measured cost "601"): they asserted that particular English sentences still appear in a
    markdown file. A git repository already records when prose changes, so such a test fails on every
    legitimate reword and catches no defect. Worse, the line-number cites are pins on ANOTHER file's
    line numbering, so an unrelated edit to `plan-review.md` breaks them.

    What SURVIVES is only what a machine reads verbatim: the commands an agent is instructed to run,
    the front-matter field spellings, the module-qualified names that identify the single authority
    for a closed vocabulary, and the machine-parsed section heading. Each row says why.
    """

    #: (needle, where: "body"|"readme", why it is LOAD-BEARING)
    REQUIRED = (
        (
            "aw specs set reviewed",
            "body",
            "the exact command an agent runs to make the transition; a drifted spelling means the "
            "agent hand-edits `- Status:` instead, which is the forgery this gate exists to stop",
        ),
        (
            "aw specs note",
            "body",
            "the command for a history-only annotation (no status change), the documented way to "
            "record a round without transitioning",
        ),
        (
            "aw specs check",
            "body",
            "the spec's structural gate. If this is lost the agent falls back to `aw ipd lint`, "
            "which is prohibition (c) and silently PASSES BY NOT RUNNING on a spec",
        ),
        (
            "aw specs set approved",
            "body",
            "the human-only approval command, whose gate the body must disclose",
        ),
        (
            "- Subject-Id:",
            "body",
            "front-matter field spelling PARSED by review_findings; the attestation predicate "
            "matches a record to a spec by this exact key",
        ),
        (
            "- Subject-Type:",
            "body",
            "front-matter field spelling parsed by review_findings, and the field whose absence is "
            "a loud diagnostic rather than a default",
        ),
        (
            "- Readiness:",
            "body",
            "the field name the prohibition is ABOUT. The `- Readiness:`-mentions-are-prohibitions "
            "scan below is vacuous if the field is never named, so presence is asserted here",
        ),
        (
            "- Status:",
            "body",
            "the field name prohibition (b) forbids hand-editing; same vacuity argument",
        ),
        (
            "subject_gating_blocks",
            "body",
            "names the predicate that arms the approval refusal, so a reader can find the code that "
            "will refuse them rather than guessing",
        ),
        (
            "review_findings.SEVERITIES",
            "body",
            "POINTER, not a copy, to the single authority for the closed severity vocabulary. A copy "
            "is what drifts; this pointer is the anti-fork guard",
        ),
        (
            "plan_readiness.VERDICTS",
            "body",
            "pointer to the single authority for the closed verdict vocabulary",
        ),
        (
            "review_findings.is_gating",
            "body",
            "pointer to the single authority for whether a finding gates",
        ),
        (
            "## What is SHARED and must not be re-stated here",
            "body",
            "the section heading that HOLDS those pointers; a grep and a human both locate the "
            "shared-authority table by it",
        ),
        (
            "review_findings",
            "readme",
            "the single writer/parser module the record format may not be forked away from",
        ),
        (
            "plan_readiness.VERDICTS",
            "readme",
            "the README records that the verdict vocabulary is shared, not re-declared",
        ),
        (
            "/spec-review",
            "readme",
            "the invocation name; the refusal message tells an agent to run exactly this",
        ),
    )

    def setUp(self) -> None:
        self.body = (PKG / "spec-review.md").read_text(encoding="utf-8")
        self.readme = (PKG / "README.md").read_text(encoding="utf-8")
        # The bodies are HARD-WRAPPED prose, so a multi-word token can straddle a newline. Match
        # against a whitespace-collapsed view; otherwise the test pins the line-wrap rather than the
        # content and breaks on a harmless reflow.
        self.flat = " ".join(self.body.split())
        self.readme_flat = " ".join(self.readme.split())

    def test_the_package_has_both_a_body_and_a_readme(self) -> None:
        """Two files, because the manifest points at the body and the README holds the rationale."""
        missing = [
            str(p.relative_to(REPO))
            for p in (PKG / "spec-review.md", PKG / "README.md")
            if not p.is_file()
        ]
        self.assertEqual(
            missing,
            [],
            f"the spec-review package is missing {missing}. The manifest row points at the body, so "
            "a missing body makes `/spec-review` unrunnable for every host family.",
        )

    def test_the_package_carries_every_load_bearing_element(self) -> None:
        texts = {"body": self.flat, "readme": self.readme_flat}
        missing = []
        for needle, where, why in self.REQUIRED:
            if needle not in texts[where]:
                missing.append(
                    f"  MISSING from the {where}: {needle!r}\n    load-bearing because: {why}"
                )
        self.assertEqual(
            missing,
            [],
            f"the spec-review package lost {len(missing)} of {len(self.REQUIRED)} load-bearing "
            "elements. Every element listed is consumed VERBATIM by something other than a human (a "
            "command an agent runs, a front-matter key a parser matches, a module-qualified pointer "
            "to a closed vocabulary's single authority, or a machine-located heading), so losing one "
            "silently changes what an agent does rather than merely how the page reads. Prose "
            "wording is deliberately NOT pinned here, so a reword cannot land in this list.\n"
            + "\n".join(missing)
            + "\n  FIX: restore the element in .aw/system/workflows/spec-review/, then re-run.",
        )

    def test_every_mention_of_a_forbidden_act_is_a_prohibition(self) -> None:
        """NEGATIVE scan, per line: a body can forbid something in one section and then casually
        instruct it in another, which is the mis-taken-branch hazard the separate package avoided.
        Not merged into the table above: this checks the SHAPE of each matching line rather than a
        token's presence, and it reads the RAW text because a line is the unit an agent acts on.
        """
        # (pattern, vocabulary that makes a line a prohibition or a mere reference)
        scans = (
            (r"^.*- Readiness:.*$", ("NOT", "not", "NEVER", "never", "prohibition")),
            (
                r"^.*aw ipd lint.*$",
                (
                    "NOT",
                    "not",
                    "NEVER",
                    "never",
                    "IPD-only",
                    "preflight",
                    "runs",
                ),
            ),
        )
        offenders = []
        for pattern, allowed in scans:
            for m in re.finditer(pattern, self.body, re.MULTILINE):
                line = m.group(0)
                if not any(w in line for w in allowed):
                    offenders.append(
                        f"  {pattern}\n    instructing line: {line.strip()!r}"
                    )
        self.assertEqual(
            offenders,
            [],
            f"{len(offenders)} line(s) in spec-review.md mention a PROHIBITED act without forbidding "
            "it. A body that forbids writing `- Readiness:` in one section and then instructs it in "
            "another leaves an agent free to take the wrong branch, and running `aw ipd lint` on a "
            "spec PASSES BY NOT RUNNING, so a stray instruction to run it reads as a satisfied "
            "gate:\n" + "\n".join(offenders),
        )

    def test_the_body_does_not_restate_the_shared_severity_glosses(self) -> None:
        """The other half of the anti-fork guard: a POINTER is required (asserted in the table), and
        a COPY is forbidden (asserted here). `plan-review` owns the per-value prose glosses.
        """
        copied = [
            gloss
            for gloss in (
                "likely data loss, breach, normal-path failure",
                "polish or small clarity improvement",
            )
            if gloss in self.flat
        ]
        self.assertEqual(
            copied,
            [],
            f"spec-review.md re-states {copied}, which `plan-review` owns. A copied definition is "
            "what DRIFTS: the two pages then disagree about what a severity means and no test "
            "notices. Point at review_findings.SEVERITIES instead.",
        )

    def test_the_body_does_not_apply_the_ipd_ev_rubric(self) -> None:
        """A spec has no `E-*`/`V-*` checklists, so demanding a bijection would be nonsense."""
        found = [t for t in ("E/V-bijection", "E/V bijection") if t in self.flat]
        self.assertEqual(
            found,
            [],
            f"spec-review.md demands {found}, an IPD-only property. A spec carries no E/V "
            "checklists, so this rubric item can only produce findings about the wrong artifact.",
        )

    def test_the_rubric_asks_spec_questions_not_plan_questions(self) -> None:
        """A plan rubric applied to a spec produces findings about the wrong artifact.

        Kept out of the load-bearing table because these are not verbatim-consumed tokens: they are
        the rubric's SUBJECT MATTER, checked case-insensitively and loosely on purpose so a reword
        passes while a wholesale substitution of the plan rubric fails.
        """
        low = self.flat.lower()
        unasked = [
            q
            for q in (
                "requirements are testable",
                "acceptance criteria cover",
                "decisions are recorded with rationale",
                "open questions are dispositioned",
            )
            if q not in low
        ]
        self.assertEqual(
            unasked,
            [],
            f"the spec rubric no longer asks about {unasked}. These are the spec-shaped questions "
            "the separate package exists to ask; without them the reviewer is applying a plan "
            "rubric to a spec.",
        )


class SharedVocabularyTests(unittest.TestCase):
    """The body's verdict vocabulary IS `plan_readiness.VERDICTS`, checked against the module.

    Separate from the needle table above because these rows are DERIVED from the source of truth at
    runtime rather than hardcoded: adding a fifth verdict to `plan_readiness` makes this test demand
    it in the body, which is precisely the fork the maintainer ruling rejected.
    """

    def setUp(self) -> None:
        self.flat = " ".join(
            (PKG / "spec-review.md").read_text(encoding="utf-8").split()
        )

    def test_the_body_names_exactly_the_shared_verdicts(self) -> None:
        missing = [v for v in plan_readiness.VERDICTS if v not in self.flat]
        self.assertEqual(
            missing,
            [],
            f"spec-review.md is missing {len(missing)} of {len(plan_readiness.VERDICTS)} shared "
            f"verdicts: {missing}. The verdict vocabulary is CLOSED and owned by "
            "plan_readiness.VERDICTS; a spec-flavoured extra verdict (or a missing one) forks it, "
            "and the shared classifier would then read a verdict this workflow writes as unknown.",
        )

    #: (verdict text as it may appear in a history line, expected polarity, why this row exists)
    POLARITIES = (
        (
            "APPROVE",
            plan_readiness.POSITIVE,
            "the plain approval a reviewer records; must classify POSITIVE or the readiness "
            "computation cannot see a clean review",
        ),
        (
            "APPROVE WITH REVISIONS APPLIED",
            plan_readiness.POSITIVE,
            "the verdict this workflow's fixture path writes; positive despite naming revisions, "
            "because the revisions are already applied",
        ),
        (
            "REVIEWED - OPEN QUESTIONS",
            plan_readiness.NEUTRAL,
            "NEUTRAL, not negative: a review happened, so the attestation is satisfied, but the "
            "verdict must not read as approval",
        ),
        (
            "REJECT - NEEDS REPLAN",
            plan_readiness.NEGATIVE,
            "the only negative verdict; if it classified neutral a rejected spec would look merely "
            "unfinished",
        ),
    )

    def test_each_shared_verdict_classifies_to_its_polarity(self) -> None:
        wrong = []
        for text, expected, why in self.POLARITIES:
            got = plan_readiness.classify_verdict(text)[1]
            if got != expected:
                wrong.append(
                    f"  {text!r}: expected polarity {expected!r}, got {got!r}\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"plan_readiness.classify_verdict mishandled {len(wrong)} of {len(self.POLARITIES)} "
            "shared verdicts. The verdict a `/spec-review` records is read back through this "
            "classifier, so a polarity that moves changes whether a reviewed spec reads as approved, "
            "merely reviewed, or rejected. Several rows moving together usually means the polarity "
            f"map was re-keyed rather than one verdict being re-judged:\n"
            + "\n".join(wrong),
        )


class ManifestAndDocumentationTests(unittest.TestCase):
    """E-03: registration, and the generated-shim parity that makes a hand-edit detectable."""

    def setUp(self) -> None:
        self.index = (WORKFLOWS / "index.md").read_text(encoding="utf-8")

    def test_manifest_row_registers_spec_review(self) -> None:
        """Not merged: this asserts a parsed STRUCTURE (a row and its body path), not a needle."""
        from agent_workflows import engine

        rows = engine.parse_manifest(WORKFLOWS)
        by_command = {w.command: w for w in rows}
        self.assertIn(
            "spec-review",
            by_command,
            "the manifest has no `spec-review` row, so no host family gets the command",
        )
        self.assertEqual(
            by_command["spec-review"].body,
            ".aw/system/workflows/spec-review/spec-review.md",
            "the manifest row must point at the package body; a wrong path makes the generated "
            "shims dispatch to nothing",
        )

    def test_the_index_attributes_spec_review_not_plan_review(self) -> None:
        """F-4: the index claimed `plan-review` reviews specs, which it never did.

        KEPT as a needle pair despite being prose, because the two halves are asserted TOGETHER: the
        false claim must be absent AND the true one present. Leaving either alone would give the
        repository two contradictory statements about which workflow reviews a spec, and an agent
        picks a workflow from this sentence.
        """
        stale = "interrogates and `plan-review` reviews"
        current = "interrogates and `spec-review` reviews"
        problems = []
        if stale in self.index:
            problems.append(f"the corrected-away claim {stale!r} is back")
        if current not in self.index:
            problems.append(f"the true claim {current!r} is absent")
        self.assertEqual(
            problems,
            [],
            "the workflows index misattributes spec review: "
            + "; ".join(problems)
            + ". An agent chooses which workflow to run from this sentence, so a wrong "
            "attribution routes spec reviews into the IPD reviewer.",
        )

    def test_generated_shims_match_what_the_manifest_generates(self) -> None:
        """F-11: there are TWO shim families, and each is COPIED from the manifest row.

        Compares on-disk bytes against a fresh generation, which is the same comparison `aw install`
        makes, so a hand-edited or missing shim fails here. Both host families and both commands are
        rows of one table because the realistic failure (a generator change, or a forgotten
        regeneration) moves all four at once.
        """
        from agent_workflows import engine

        rows = engine.parse_manifest(WORKFLOWS)
        generated = engine.generate_shim_members(rows, WORKFLOWS, target_layout="aw")
        wrong = []
        for rel in (
            ".opencode/commands/spec-review.md",
            ".claude/commands/spec-review.md",
            ".opencode/commands/spec.md",
            ".claude/commands/spec.md",
        ):
            if rel not in generated:
                wrong.append(f"  {rel}: the manifest generates no such shim at all")
            elif not (REPO / rel).is_file():
                wrong.append(f"  {rel}: generated by the manifest but MISSING on disk")
            elif (REPO / rel).read_text(encoding="utf-8") != generated[rel]:
                wrong.append(
                    f"  {rel}: on-disk bytes differ from the generated bytes (hand-edited?)"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of 4 generated command shims drifted from the manifest. The shim body and "
            "its description are copied VERBATIM from the manifest row, so a hand-edit is invisible "
            "until the next `aw install` silently reverts it. Two families are listed because "
            "OpenCode and Claude Code each get their own file, and a fix applied to one is commonly "
            f"forgotten on the other:\n"
            + "\n".join(wrong)
            + "\n  FIX: re-run the installer to "
            "regenerate, rather than editing a shim by hand.",
        )

    def test_no_generated_projection_to_compile_for_this_package(self) -> None:
        """F-12: neither review package has a `_generated/`, so no one may claim
        `aw workflow check-generated` coverage for them."""
        present = [
            str(p.relative_to(REPO))
            for p in (PKG / "_generated", WORKFLOWS / "plan-review" / "_generated")
            if p.exists()
        ]
        self.assertEqual(
            present,
            [],
            f"{present} now exists. A generated projection needs compiling and checking; recording "
            "its ABSENCE here is what stops a later reader from claiming check-generated coverage "
            "this package does not have. If the projection is now intended, add the compile step.",
        )


# --------------------------------------------------------------------------------------
# E-04: the attestation
# --------------------------------------------------------------------------------------


class AttestationPredicateTests(unittest.TestCase):
    """`review_attestation_missing` returns None (attested) or a REASON, per situation.

    Seven one-assertion tests became one table. This is the security-relevant predicate: it decides
    whether an agent may move a spec to `reviewed`, so the property under test is the WHOLE mapping
    from situation to verdict, not any single situation. Stating it as a table means a refactor that
    makes one more situation "attested" is reported beside the rows that still refuse, which is how a
    widened gate is recognized as a widening rather than as one unrelated failure.

    The ATTESTED row lives in the same table on purpose: a predicate that refused everything would
    satisfy every refusal row here, and would also make the whole `->reviewed` path unusable.

    Each refusal row pins a SUBSTRING of the reason, not the whole sentence, and the substring is the
    part a caller keys on: the id6 (so the message names the artifact), and the distinguishing phrase
    that tells the agent WHICH remedy applies (file a record / fix a malformed one / fix the declared
    type). Those phrases are surfaced to agents by two setters and one checker.
    """

    #: (case, build(root) -> None, id6 queried, subject type queried, expected reason substrings
    #:  or None for ATTESTED, why this row exists)
    CASES = (
        (
            "no record at all",
            lambda root: _write_spec(root, "aaa111", "to-review"),
            "aaa111",
            "spec",
            ("aaa111", "no review record names"),
            "the default state of every spec: unattested until a review is FILED. If this returned "
            "None the gate would be off entirely",
        ),
        (
            "a conforming spec-typed record",
            lambda root: (
                _write_spec(root, "aaa111", "to-review"),
                _write_record(root, "aaa111"),
            ),
            "aaa111",
            "spec",
            None,
            "THE POSITIVE ROW. A predicate that refuses everything satisfies every other row in this "
            "table, and would make `aw specs set reviewed` permanently unusable",
        ),
        (
            "a record that exists but does not parse",
            lambda root: (
                _write_spec(root, "aaa111", "to-review"),
                _break_record(_write_record(root, "aaa111")),
            ),
            "aaa111",
            "spec",
            ("aaa111", "does NOT parse"),
            "a file that cannot be parsed proves nothing about what it says. `subject_gating_blocks` "
            "already makes this judgement, so accepting it here would let ONE file be simultaneously "
            "good enough to attest a review and bad enough to block the approval",
        ),
        (
            "a record declaring a different subject type",
            lambda root: (
                _write_spec(root, "aaa111", "to-review"),
                _write_record(root, "aaa111", subject_type="ipd"),
            ),
            "aaa111",
            "spec",
            ("aaa111", "different subject type"),
            "an IPD review does not attest a spec review. Matching on the id6 alone would let a "
            "review of the same-id6 plan satisfy the spec's gate",
        ),
        (
            "a spec-typed record queried as an ipd",
            lambda root: (
                _write_spec(root, "aaa111", "to-review"),
                _write_record(root, "aaa111"),
            ),
            "aaa111",
            "ipd",
            ("aaa111", "different subject type"),
            "the type check is SYMMETRIC, not a spec-only special case; without this row a resolver "
            "that only ever compared against `spec` would pass",
        ),
        (
            "an artifact with no `- Id:` bullet",
            lambda root: None,
            "",
            "spec",
            ("no `- Id:`",),
            "an empty id6 must REFUSE rather than match anything. Permitting it is the bypass: a "
            "spec with no id would otherwise be attestable by any record at all",
        ),
    )

    def test_each_situation_gets_its_own_verdict_and_reason(self) -> None:
        wrong = []
        for case, build, id6, stype, expected, why in self.CASES:
            with TemporaryDirectory() as d:
                root = Path(d)
                build(root)
                reason = rf.review_attestation_missing(root, id6, stype)
            if expected is None:
                if reason is not None:
                    wrong.append(
                        f"  {case}: must be ATTESTED (None) but was REFUSED with {str(reason)!r}\n"
                        f"    rule: {why}\n"
                        "    NOTE: while this row is broken every refusal row above is VACUOUS, "
                        "because a predicate that refuses everything satisfies them all"
                    )
                continue
            if reason is None:
                wrong.append(
                    f"  {case}: must be REFUSED but the predicate ATTESTED it (returned None)\n"
                    f"    rule: {why}\n"
                    "    this is a WIDENED GATE: an agent can now reach `reviewed` in this situation"
                )
                continue
            absent = [n for n in expected if n not in str(reason)]
            if absent:
                wrong.append(
                    f"  {case}: refused correctly, but the reason omits {absent}\n"
                    f"    got: {str(reason)!r}\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"review_findings.review_attestation_missing mishandled {len(wrong)} of "
            f"{len(self.CASES)} situations. This predicate is the `->reviewed` GATE consulted by both "
            "`aw specs set` spellings and by `aw check`, so a row that flips from refused to attested "
            "is a hole an agent can walk through without a human review having happened. Several rows "
            "flipping at once usually means the record-matching step changed (id6 match, type match, "
            f"or parse check) rather than several independent judgements:\n"
            + "\n".join(wrong),
        )

    def test_it_never_raises_on_an_unreadable_tree(self) -> None:
        """Kept separate: no fixture tree at all, so it shares no setup with the table.

        FAIL CLOSED is the property: an unreadable repo must produce a REFUSAL, not an exception (a
        crash in a gate is often "handled" by skipping the gate) and not an attestation.
        """
        reason = rf.review_attestation_missing(
            Path("/nonexistent/definitely/not/a/repo"), "aaa111", "spec"
        )
        self.assertIsNotNone(
            reason,
            "an unreadable tree must REFUSE (no record can be read, so nothing is attested); "
            "returning None there would attest every spec in a repo the tool cannot read",
        )

    def test_listing_records_still_shows_a_malformed_one(self) -> None:
        """Kept separate: a different function with a structurally different assertion (it returns a
        path tuple, not a reason). A caller asking "what exists" must SEE a broken file rather than
        have it vanish, or the operator cannot find the file they must fix.
        """
        with TemporaryDirectory() as d:
            root = Path(d)
            p = _write_record(root, "aaa111")
            _break_record(p)
            self.assertEqual(
                rf.subject_review_records(root, "aaa111"),
                (p,),
                "a malformed record must still be LISTED; if enumeration hides it, the refusal "
                "message above names a file the operator cannot locate",
            )


class OneSharedPredicateTests(unittest.TestCase):
    """R-12: one predicate and one refusal wording, several call sites; never a second copy.

    Two source-census tests became one table. The failure guarded against is a SECOND definition
    appearing (by copy-paste during a refactor), at which point two surfaces can disagree about
    whether a spec is attested while both tests-of-one-site stay green.
    """

    #: (symbol, modules searched, expected definition count, why exactly that many)
    DEFINITIONS = (
        (
            "review_attestation_missing",
            (rf, specs, status_set, check_engine, policy, rs),
            1,
            "the ATTESTATION JUDGEMENT itself. Two definitions means one surface can accept what "
            "another refuses, and the forgeable surface wins",
        ),
        (
            "_review_attestation_refusal",
            (specs, status_set),
            1,
            "the refusal WORDING shared by both setter spellings. Two wordings is how the two "
            "surfaces come to tell an agent different remedies for the same refusal",
        ),
    )

    def test_each_shared_symbol_is_defined_exactly_once(self) -> None:
        wrong = []
        for symbol, modules, expected, why in self.DEFINITIONS:
            sites = []
            for mod in modules:
                src = Path(str(mod.__file__)).read_text(encoding="utf-8")
                if re.search(rf"^def {symbol}\b", src, re.MULTILINE):
                    sites.append(Path(str(mod.__file__)).name)
            if len(sites) != expected:
                wrong.append(
                    f"  {symbol}: expected {expected} definition(s), found {len(sites)} in {sites}\n"
                    f"    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.DEFINITIONS)} shared attestation symbols are no longer "
            "single-sourced. A second DEFINITION (not a second call) is the failure: the gate then "
            "has two implementations, and a fix applied to one leaves the other permissive.\n"
            + "\n".join(wrong)
            + "\n  FIX: keep the definition in review_findings/specs and have the other module call "
            "it.",
        )

    #: (module, symbol it must reference, why that call site matters)
    CALL_SITES = (
        (
            specs,
            "review_attestation_missing",
            "`aw specs set --status reviewed` reaches the predicate through the shared message helper",
        ),
        (
            check_engine,
            "review_attestation_missing",
            "`aw check` consults the predicate directly, which is what catches a hand-edited spec "
            "that reached `reviewed` without any setter",
        ),
        (
            status_set,
            "_review_attestation_refusal",
            "the positional `aw specs set reviewed <selector>` spelling routes through status_set, "
            "so it must consume the SHARED message (and therefore the shared predicate); a gate in "
            "one spelling is bypassed by choosing the other",
        ),
    )

    def test_every_gated_surface_consults_the_shared_symbol(self) -> None:
        missing = []
        for mod, symbol, why in self.CALL_SITES:
            src = Path(str(mod.__file__)).read_text(encoding="utf-8")
            if symbol not in src:
                missing.append(
                    f"  {Path(str(mod.__file__)).name} does not reference {symbol!r}\n"
                    f"    needed because: {why}"
                )
        self.assertEqual(
            missing,
            [],
            f"{len(missing)} of {len(self.CALL_SITES)} surfaces no longer consult the shared "
            "attestation symbol. An UNGATED surface is a complete bypass, not a partial one: an agent "
            "picks whichever spelling is not gated.\n" + "\n".join(missing),
        )


class SetterAttestationTests(unittest.TestCase):
    """Both CLI spellings enforce the same transition rules, row for row.

    Nine tests across two classes became one table with the ROUTE as an inner loop rather than a
    second table. That is the point: `aw specs set --status reviewed <path>` runs `specs.run_set`
    while `aw specs set reviewed <selector>` runs `status_set.validate_transition_allowed`, and a gate
    present in one spelling is BYPASSED by choosing the other. Testing them as separate classes is how
    such a divergence stays invisible; testing each row through both routes makes it one failure that
    names the route.

    The refusal rows also assert the file is UNCHANGED on the `run_set` route. A refusal that has
    already written `- Status: reviewed` is not a refusal.

    Needles are the phrase that selects the REMEDY (file a record, fix the malformed one, fix the
    declared type, pass --by-human), asserted against BOTH routes' text so the two cannot drift into
    advising different fixes. The exact sentences differ by route by design, so only the shared
    remedy-bearing substring is pinned.
    """

    #: (case, start status, target status, record kwargs or None, break the record?, by_human,
    #:  allow_open_questions, expected allowed?, needles required in BOTH routes' refusal, why)
    CASES = (
        (
            "->reviewed with no record",
            "to-review",
            "reviewed",
            None,
            False,
            False,
            False,
            False,
            ("requires evidence that a review OCCURRED", "recovery:", "/spec-review"),
            "THE CENTRAL REFUSAL. An agent must not be able to declare a spec reviewed; the message "
            "must also carry the RECOVERY (run /spec-review) or the agent's next move is a hand edit",
        ),
        (
            "->reviewed with a conforming record",
            "to-review",
            "reviewed",
            {},
            False,
            False,
            False,
            True,
            (),
            "THE POSITIVE ROW for `->reviewed`: with a real review filed the transition must SUCCEED, "
            "or every refusal row here is satisfied by a gate that refuses unconditionally",
        ),
        (
            "->reviewed with a malformed record",
            "to-review",
            "reviewed",
            {},
            True,
            False,
            False,
            False,
            ("requires evidence that a review OCCURRED", "does NOT parse"),
            "an unparseable record must not attest. Naming the parse failure is what stops the "
            "operator from concluding no record exists and filing a second one",
        ),
        (
            "->reviewed with an ipd-typed record",
            "to-review",
            "reviewed",
            {"subject_type": "ipd"},
            False,
            False,
            False,
            False,
            ("requires evidence that a review OCCURRED", "different subject type"),
            "a review of the same-id6 PLAN must not attest the spec; the message must say the type "
            "is wrong rather than that no record exists",
        ),
        (
            "reviewed->reviewed (no-op reset), no record",
            "reviewed",
            "reviewed",
            None,
            False,
            False,
            False,
            True,
            (),
            "`old == new` is NOT a transition, so the authority table must not fire on it. If it did, "
            "every idempotent re-set of an already-reviewed spec would fail",
        ),
        (
            "draft->to-review",
            "draft",
            "to-review",
            None,
            False,
            False,
            False,
            True,
            (),
            "the new pressure applies to `->reviewed` ONLY; an unrelated transition must be "
            "unaffected, which is what bounds the blast radius of this gate",
        ),
        (
            "reviewed->approved by a human, clean record",
            "reviewed",
            "approved",
            {"severity": "high", "decision": "fixed"},
            False,
            True,
            False,
            True,
            (),
            "POSITIVE ROW for the approval gate: a HIGH finding that was FIXED must not block, or "
            "filing a thorough review would make a spec unapprovable",
        ),
        (
            "reviewed->approved by a human, no record at all",
            "reviewed",
            "approved",
            None,
            False,
            True,
            False,
            True,
            (),
            "GRANDFATHERING: approval is not newly conditioned on a review existing. The gate arms "
            "only once a record is FILED, which is why the whole existing corpus keeps working",
        ),
        (
            "reviewed->approved by a human, unresolved high finding",
            "reviewed",
            "approved",
            {"severity": "high", "decision": "open"},
            False,
            True,
            False,
            False,
            ("unresolved gating finding",),
            "F-10: filing a record ARMS a live approval refusal. This is the largest behavior change "
            "the gate ships, so it is asserted in both directions rather than described",
        ),
        (
            "reviewed->approved with --allow-open-questions and a blocker",
            "reviewed",
            "approved",
            {"severity": "blocker", "decision": "open"},
            False,
            True,
            True,
            False,
            ("unresolved gating finding",),
            "NO OVERRIDE: `--allow-open-questions` suppresses open QUESTIONS, never a gating FINDING. "
            "If this row ever flipped, the flag would be a way to approve over a blocker",
        ),
        (
            "reviewed->approved with a malformed record",
            "reviewed",
            "approved",
            {},
            True,
            True,
            False,
            False,
            ("malformed",),
            "a broken record blocks UNFIXABLY (any parse diagnostic is treated as blocking), which is "
            "the fail-closed choice: an unreadable review cannot be shown to be clean",
        ),
        (
            "reviewed->approved without --by-human",
            "reviewed",
            "approved",
            {},
            False,
            False,
            False,
            False,
            ("--by-human",),
            "approval is HUMAN-ONLY and independent of the review gate; an agent holding a clean "
            "review record still may not approve",
        ),
    )

    def _build(self, root: Path, start: str, record, broken: bool) -> Path:
        p = _write_spec(root, "aaa111", start)
        if record is not None:
            r = _write_record(root, "aaa111", **record)
            if broken:
                _break_record(r)
        return p

    def _run_setter(self, start, target, record, broken, by_human, allow_oq):
        """`aw specs set --status <s> <path>` route. Returns (allowed, text, unchanged)."""
        with TemporaryDirectory() as d:
            root = Path(d)
            p = self._build(root, start, record, broken)
            before = p.read_text(encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                rc = specs.run_set(
                    _set_args(
                        p, target, by_human=by_human, allow_open_questions=allow_oq
                    )
                )
            after = p.read_text(encoding="utf-8")
            wrote_status = f"- Status: {target}" in after
            wrote_history = f"- 2026-09-06 {target} (aw specs" in after
        return rc == 0, err.getvalue(), after == before, wrote_status, wrote_history

    def _run_positional(self, start, target, record, broken, by_human, allow_oq):
        """`aw specs set <status> <selector>` route. Returns (allowed, reason text)."""
        with TemporaryDirectory() as d:
            root = Path(d)
            p = self._build(root, start, record, broken)
            rec = status_set.read_artifact_record(p, root)
            assert (
                rec is not None
            ), "the fixture spec must be readable as an artifact record"
            ok, reason = status_set.validate_transition_allowed(
                rec,
                target,
                _args(
                    by_human=by_human,
                    agent=True,
                    json=False,
                    allow_open_questions=allow_oq,
                ),
                root,
            )
        return bool(ok), str(reason)

    def test_both_spellings_enforce_the_same_transition_rules(self) -> None:
        wrong = []
        for (
            case,
            start,
            target,
            record,
            broken,
            by_human,
            allow_oq,
            expect_allowed,
            needles,
            why,
        ) in self.CASES:
            (
                a_allowed,
                a_text,
                a_unchanged,
                a_status,
                a_history,
            ) = self._run_setter(start, target, record, broken, by_human, allow_oq)
            b_allowed, b_text = self._run_positional(
                start, target, record, broken, by_human, allow_oq
            )
            problems = []
            for route, allowed in (
                ("--status spelling", a_allowed),
                ("positional spelling", b_allowed),
            ):
                if allowed is not expect_allowed:
                    problems.append(
                        f"{route}: expected {'ALLOWED' if expect_allowed else 'REFUSED'}, got "
                        f"{'ALLOWED' if allowed else 'REFUSED'}"
                    )
            if expect_allowed:
                if not a_unchanged and not (a_status and a_history):
                    problems.append(
                        "--status spelling allowed the transition but did not record it "
                        f"(status line written={a_status}, history entry written={a_history}); the "
                        "history entry is the record that the SETTER made the change rather than a "
                        "hand edit"
                    )
            else:
                if not a_unchanged:
                    problems.append(
                        "--status spelling refused but MODIFIED THE FILE; a refusal that has already "
                        "written the new status is not a refusal"
                    )
                for route, text in (
                    ("--status spelling", a_text),
                    ("positional spelling", b_text),
                ):
                    absent = [n for n in needles if n not in text]
                    if absent:
                        problems.append(
                            f"{route}: refusal omits {absent}\n      got: {text.strip()[:240]!r}"
                        )
            if problems:
                wrong.append(
                    f"  {case}:\n    " + "\n    ".join(problems) + f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.CASES)} transition rules are enforced wrongly or "
            "inconsistently across the two `aw specs set` spellings. Both spellings reach the same "
            "user goal, so a rule enforced in only ONE of them is not a partial gate but a total "
            "bypass: an agent simply uses the other spelling. If the failures below all name the same "
            "ROUTE, that route stopped consulting the shared predicate; if they all name the same "
            "CASE, the predicate's judgement for that situation changed.\n"
            + "\n".join(wrong),
        )


class GrandfatheringAndCheckerTests(unittest.TestCase):
    """R-13: the gate binds TRANSITIONS, and `aw check` catches the hand edit that skipped them.

    Six tests became one table over (status, record present?). The two halves belong together: the
    checker must fire on exactly ONE cell of this grid (`reviewed` with no record) and stay silent on
    every other, and the same grid proves the existing corpus was not retroactively invalidated. Run
    as separate tests, a checker that fired on `approved` too would look like one unrelated failure
    instead of "the rule is now over-firing across statuses".

    `validate_spec` is asserted clean on every row as well, because a structural validator that
    started rejecting these fixtures would invalidate the whole specs tree at once.
    """

    #: (status, record present?, checker fires?, why this row exists)
    GRID = (
        (
            "draft",
            False,
            False,
            "pre-review status: nothing to attest yet",
        ),
        (
            "to-review",
            False,
            False,
            "AWAITING review. Flagging here would demand a record before the review happens",
        ),
        (
            "reviewed",
            False,
            True,
            "THE ONLY CELL THAT FIRES: `reviewed` with no record means the status was reached some "
            "other way (a hand edit), which is exactly the forgery the transition gate refuses",
        ),
        (
            "reviewed",
            True,
            False,
            "the attested state; firing here would make a correctly reviewed spec permanently dirty",
        ),
        (
            "approved",
            False,
            False,
            "GRANDFATHERED: 'past review' statuses are not re-tested, or every already-approved spec "
            "in the corpus would light up on the day this rule shipped",
        ),
        (
            "implemented",
            False,
            False,
            "same grandfathering, at the far end of the lifecycle",
        ),
        (
            "parked",
            False,
            False,
            "a parked spec is out of the flow; it must not accrue a review obligation",
        ),
        (
            "superseded",
            False,
            False,
            "terminal status: a review of a superseded spec would be pointless work",
        ),
    )

    def test_the_checker_fires_on_exactly_the_unattested_reviewed_cell(self) -> None:
        wrong = []
        for status, has_record, should_fire, why in self.GRID:
            with TemporaryDirectory() as d:
                root = Path(d)
                p = _write_spec(root, "aaa111", status)
                if has_record:
                    _write_record(root, "aaa111")
                structural = [
                    x.rule
                    for x in specs.validate_spec(p, p.read_text(encoding="utf-8"))
                ]
                found = check_engine.check_spec_review_attestation(root)
            problems = []
            if structural:
                problems.append(
                    f"specs.validate_spec now reports {structural} for a plain fixture spec, which "
                    "would invalidate existing specs wholesale"
                )
            if should_fire:
                if len(found) != 1:
                    problems.append(
                        f"expected exactly 1 attestation finding, got {len(found)}: "
                        f"{[x.rule for x in found]}"
                    )
                else:
                    drift = found[0]
                    if drift.rule != "check.spec-review-unattested":
                        problems.append(
                            f"expected rule 'check.spec-review-unattested', got {drift.rule!r}"
                        )
                    if str(p) not in drift.location:
                        problems.append(
                            f"the finding must LOCATE the spec file; location={drift.location!r}"
                        )
                    blob = " ".join(
                        str(v) for v in (drift.detail, getattr(drift, "recovery", ""))
                    )
                    for needle, reason in (
                        ("aaa111", "names the offending spec"),
                        (
                            "spec-review",
                            "names the workflow that produces the missing record",
                        ),
                    ):
                        if needle not in blob:
                            problems.append(
                                f"the finding must carry {needle!r} ({reason}); got {blob!r}"
                            )
            elif found:
                problems.append(
                    f"expected SILENCE, got {[(x.rule, x.detail) for x in found]}"
                )
            if problems:
                record_note = "with a record" if has_record else "with NO record"
                wrong.append(
                    f"  status={status!r} {record_note}:\n    "
                    + "\n    ".join(problems)
                    + f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"check_engine.check_spec_review_attestation mishandled {len(wrong)} of {len(self.GRID)} "
            "(status, record) cells. The rule must fire on EXACTLY ONE cell. Several silent cells "
            "turning noisy at once means the status predicate widened, which retroactively invalidates "
            "the existing specs corpus (this plan's stated main risk); the `reviewed`-without-record "
            "cell going silent instead means a hand-edited spec is no longer detectable, which is the "
            f"forgery the rule exists to catch:\n" + "\n".join(wrong),
        )

    def test_the_rule_is_registered_as_an_error_with_its_invariant(self) -> None:
        """Kept separate: a registry lookup, not a repo-state probe.

        An UNREGISTERED id silently falls back to an EMPTY invariant, which drops the I-03 trace and
        (because severity comes from the registry too) can quietly demote the rule below blocking.
        """
        spec = check_engine.RULE_REGISTRY["check.spec-review-unattested"]
        self.assertEqual(
            (spec.severity, spec.invariant),
            ("error", "I-03"),
            "an unattested `reviewed` spec is a forged human-approval step, so the rule must be an "
            "ERROR carrying its I-03 invariant; an unregistered id silently loses both",
        )

    def test_plans_are_not_made_stricter(self) -> None:
        """F-6: a missing review stays SILENT for plans (428 have none), so the gate is spec-scoped."""
        with TemporaryDirectory() as d:
            self.assertEqual(
                rf.subject_gating_blocks(Path(d), "aaa111"),
                (),
                "a plan with no review record must produce NO gating blocks; making plans stricter "
                "here would instantly block hundreds of existing plans",
            )

    def test_every_real_spec_in_this_repository_still_conforms(self) -> None:
        """Kept separate: the REAL corpus, not a fixture, because the risk IS about the corpus.

        This is the measured guard on the plan's main risk (retroactive invalidation). Two assertions
        over the same corpus are kept in one test because they answer one question: did shipping this
        gate dirty any existing spec?
        """
        offenders = []
        for path, text in check_engine._iter_spec_records(REPO):
            drift = specs.validate_spec(path, text)
            if drift:
                offenders.append(f"  {path.name}: {[d.rule for d in drift]}")
        unattested = [
            f"  {d.location}" for d in check_engine.check_spec_review_attestation(REPO)
        ]
        self.assertEqual(
            (offenders, unattested),
            ([], []),
            "shipping the attestation gate dirtied specs that already existed, which is the "
            "retroactive-invalidation risk this plan called its main one. Structural offenders:\n"
            + ("\n".join(offenders) or "  (none)")
            + "\nSpecs now flagged unattested:\n"
            + ("\n".join(unattested) or "  (none)")
            + "\n  FIX: grandfather the existing corpus rather than back-filling review records for "
            "reviews that never happened.",
        )


class ApprovalGateActivationTests(unittest.TestCase):
    """F-10: which review records refuse approval, keyed on severity x decision.

    Four tests became one table over `plan_readiness.approval_refusals`. The threshold this encodes
    (default `high`) plus the resolved/unresolved split IS the gate, and the realistic regression is a
    comparison flipping direction or an off-by-one in the severity ordering, which moves several rows
    at once and is only recognizable as such when the rows are read together.

    Clean rows are in the table for the usual reason, plus a sharper one here: the whole point of F-10
    is that filing a review must not make a spec unapprovable, so a gate that refused every record
    would be just as wrong as one that refused none.
    """

    #: (case, record kwargs or None, break it?, allow_open_questions, expected refusal substring or
    #:  None for NO refusal, why this row exists)
    CASES = (
        (
            "no record at all",
            None,
            False,
            False,
            None,
            "the gate is ARMED BY FILING. Before any record exists approval is unchanged, which is "
            "what grandfathers the corpus",
        ),
        (
            "low severity, fixed",
            {},
            False,
            False,
            None,
            "resolved and below threshold: doubly non-blocking",
        ),
        (
            "high severity, fixed",
            {"severity": "high", "decision": "fixed"},
            False,
            False,
            None,
            "AT threshold but RESOLVED. Refusing here would punish a thorough review that fixed what "
            "it found",
        ),
        (
            "high severity, open",
            {"severity": "high", "decision": "open"},
            False,
            False,
            "unresolved gating finding",
            "at threshold and unresolved: the canonical block",
        ),
        (
            "high severity, deferred",
            {
                "severity": "high",
                "decision": "deferred",
                "verdict": "REVIEWED - OPEN QUESTIONS",
            },
            False,
            False,
            "unresolved gating finding",
            "DEFERRED is a deliberate decision NOT to fix, so it is unresolved and still blocks; "
            "treating it as resolved would make deferral a silent override",
        ),
        (
            "blocker severity, open",
            {"severity": "blocker", "decision": "open"},
            False,
            False,
            "unresolved gating finding",
            "above threshold: must block too, which is what proves the comparison is >= and not ==",
        ),
        (
            "blocker severity, open, --allow-open-questions",
            {"severity": "blocker", "decision": "open"},
            False,
            True,
            "unresolved gating finding",
            "NO OVERRIDE. The flag suppresses open QUESTIONS; if it also suppressed findings it would "
            "be a documented way to approve over a blocker",
        ),
        (
            "medium severity, open",
            {"severity": "medium", "decision": "open"},
            False,
            False,
            None,
            "BELOW the default `high` threshold: unresolved but not gating. This row is what shows "
            "the threshold is real rather than 'any unresolved finding blocks'",
        ),
        (
            "a malformed record",
            {},
            True,
            False,
            "malformed",
            "FAIL CLOSED: an unparseable record cannot be shown to be clean, so it blocks (and says "
            "so distinctly, since the remedy is to fix the file rather than the findings)",
        ),
    )

    def test_each_record_shape_refuses_or_permits_approval(self) -> None:
        wrong = []
        for case, record, broken, allow_oq, expected, why in self.CASES:
            with TemporaryDirectory() as d:
                root = Path(d)
                p = _write_spec(root, "aaa111", "reviewed")
                if record is not None:
                    r = _write_record(root, "aaa111", **record)
                    if broken:
                        _break_record(r)
                refusals = plan_readiness.approval_refusals(
                    root,
                    p,
                    p.read_text(encoding="utf-8"),
                    allow_open_questions=allow_oq,
                )
            if expected is None:
                if refusals:
                    wrong.append(
                        f"  {case}: must NOT refuse, got {refusals}\n    rule: {why}\n"
                        "    while this row is broken the refusal rows are vacuous, because a gate "
                        "that refuses everything satisfies them all"
                    )
            elif not any(expected in r for r in refusals):
                wrong.append(
                    f"  {case}: expected a refusal containing {expected!r}, got "
                    f"{refusals or 'NO refusal at all (approval would be permitted)'}\n"
                    f"    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"plan_readiness.approval_refusals mishandled {len(wrong)} of {len(self.CASES)} review "
            "record shapes. This is the no-override approval refusal a filed review arms, so a row "
            "that stops refusing lets a human-attested approval land over an unresolved gating "
            "finding. If the rows that moved share a SEVERITY, the threshold comparison changed; if "
            "they share a DECISION, the resolved/unresolved split changed; if the clean rows moved, "
            f"the gate is now refusing unconditionally:\n" + "\n".join(wrong),
        )


class VerdictSourcingTests(unittest.TestCase):
    """F-9 as CORRECTED: WHICH history line a verdict is read from, and what it reads as.

    Four tests became two tables. The hazard is not recognition of the `/spec-review` token: the
    setter's own bare `- ... reviewed (aw specs): status set to reviewed` line ALSO qualifies as a
    review record and states NO verdict, so the real hazard is sourcing the verdict from the wrong
    line and reporting a false positive.
    """

    #: (history line, is a review record?, why this row exists)
    ENTRIES = (
        (
            "- 2026-09-06 reviewed (oc): /spec-review round 1; APPROVE",
            True,
            "what a reviewer writes. Recognition keys on the `reviewed` STATUS TOKEN, not on the "
            "workflow name, which is the F-9 correction",
        ),
        (
            "- 2026-09-06 reviewed (aw specs): status set to reviewed",
            True,
            "THE HAZARD ROW: the setter's own bare line qualifies too. It carries no verdict, so any "
            "verdict reader must cope with a qualifying entry that states nothing",
        ),
        (
            "- 2026-09-06 to-review (aw specs): status set to to-review",
            False,
            "a different status token is not a review record; counting it would let requesting a "
            "review look like having had one",
        ),
        (
            "- 2026-09-06 approved (aw specs): status set to approved",
            False,
            "approval is not review. If this qualified, approving would retroactively attest the "
            "review step it is supposed to depend on",
        ),
        (
            "- 2026-09-06 draft (fixture): created.",
            False,
            "creation is not review",
        ),
        (
            "just some prose",
            False,
            "a non-history line must not qualify, or free-text notes become attestations",
        ),
        (
            "",
            False,
            "the empty string must not qualify; a permissive parser would make every spec attested",
        ),
    )

    def test_history_entries_are_recognized_as_reviews_or_not(self) -> None:
        wrong = []
        for entry, expected, why in self.ENTRIES:
            got = plan_readiness.is_review_history_entry(entry)
            if bool(got) is not expected:
                wrong.append(
                    f"  {entry!r}\n    expected is_review_history_entry={expected}, got {bool(got)}"
                    f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"plan_readiness.is_review_history_entry mishandled {len(wrong)} of {len(self.ENTRIES)} "
            "history lines. This predicate decides which line a verdict is read from, so a "
            "false POSITIVE lets a non-review line be treated as evidence a review occurred, and a "
            "false NEGATIVE hides a real review. The `reviewed`-token rows and the other-status rows "
            f"failing together means recognition changed key:\n" + "\n".join(wrong),
        )

    #: (setter --message, expected polarity, substring expected in the sourced entry, why)
    MESSAGES = (
        (
            "APPROVE WITH REVISIONS APPLIED; SR-001",
            plan_readiness.POSITIVE,
            "APPROVE WITH REVISIONS APPLIED",
            "the reviewer's own message is where the verdict lives, so `--message` is the documented "
            "carrier and the sourced entry must be THAT line",
        ),
        (
            "REVIEWED - OPEN QUESTIONS; SR-002",
            plan_readiness.NEUTRAL,
            "REVIEWED - OPEN QUESTIONS",
            "a neutral verdict must be read as neutral and not rounded up to approval",
        ),
        (
            "status set to reviewed",
            None,
            "aw specs",
            "THE LIMITATION, recorded rather than hidden: a reviewer who omits the verdict records "
            "NONE. `None` is the honest answer; inventing a positive here would be the false positive "
            "this class exists to prevent",
        ),
        (
            "REJECT - RESUBMIT",
            None,
            "aw specs",
            "a NEAR-MISS of the closed vocabulary yields no verdict rather than a guessed negative, "
            "which is what keeps `plan_readiness.VERDICTS` closed in practice",
        ),
    )

    def test_the_verdict_is_sourced_from_the_review_message(self) -> None:
        wrong = []
        for message, expected_polarity, expected_in_entry, why in self.MESSAGES:
            with TemporaryDirectory() as d:
                root = Path(d)
                p = _write_spec(root, "aaa111", "to-review")
                _write_record(root, "aaa111")
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    rc = specs.run_set(_set_args(p, "reviewed", message=message))
                text = p.read_text(encoding="utf-8")
            polarity, entry = plan_readiness.newest_verdict(text)
            problems = []
            if rc != 0:
                problems.append(
                    f"the setter refused (rc={rc}) despite a conforming record"
                )
            if polarity != expected_polarity:
                problems.append(
                    f"expected polarity {expected_polarity!r}, got {polarity!r}"
                )
            if expected_in_entry not in entry:
                problems.append(
                    f"the sourced entry must contain {expected_in_entry!r}; got {entry!r}"
                )
            if problems:
                wrong.append(
                    f"  --message={message!r}:\n    "
                    + "\n    ".join(problems)
                    + f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the verdict was sourced wrongly for {len(wrong)} of {len(self.MESSAGES)} review "
            "messages. `newest_verdict` must read the REVIEW's own line: the setter also writes a "
            "bare qualifying line that states no verdict, so reading the wrong line yields either a "
            "missing verdict for a real review or an invented one for a bare status change. A row "
            "whose polarity became non-None where None was expected is the more dangerous direction, "
            f"since it manufactures approval evidence:\n" + "\n".join(wrong),
        )


# --------------------------------------------------------------------------------------
# E-05: discovery
# --------------------------------------------------------------------------------------


class SpecDiscoveryTests(unittest.TestCase):
    """`discover_specs` enumerates specs by id6, and never raises on a hostile tree.

    Three tests became one table over the TREE SHAPE. They all called the same function on a
    differently-shaped tree and compared one result, so the tree is the data. Keeping the populated
    row beside the empty rows is what stops "returns {} always" from passing.
    """

    #: (case, build(root) -> None, expected {id6: (status, relative path)} , why this row exists)
    TREES = (
        (
            "a spec with an id6",
            lambda root: _write_spec(root, "aaa111", "to-review"),
            {
                "aaa111": (
                    "to-review",
                    ".aw/records/specs/20260906-aaa111-01-aaa111-fixture-spec.spec.md",
                )
            },
            "THE POSITIVE ROW: the id6 is the key, and both the STATUS and the REPO-RELATIVE path "
            "come back, because callers use the status to decide and the path to report",
        ),
        (
            "a legacy spec with no `- Id:` bullet",
            lambda root: (
                (root / ".aw" / "records" / "specs").mkdir(parents=True),
                (
                    root
                    / ".aw"
                    / "records"
                    / "specs"
                    / "20260706-0000-01-legacy.spec.md"
                ).write_text(
                    "# Spec: legacy\n\n- Date: 2026-07-06\n- Status: implemented\n\n"
                    "## Workflow history\n- 2026-07-06 implemented (x): y.\n",
                    encoding="utf-8",
                ),
            ),
            {},
            "an un-id'd legacy spec is SKIPPED rather than given a synthesized key; a synthesized "
            "key would collide with a real id6 and mis-route a review record",
        ),
        (
            "an empty repository",
            lambda root: None,
            {},
            "no specs tree at all must yield {} and not raise, since this runs on every repo",
        ),
    )

    def test_discovery_maps_each_shape_to_its_records(self) -> None:
        wrong = []
        for case, build, expected, why in self.TREES:
            with TemporaryDirectory() as d:
                root = Path(d)
                build(root)
                found = rs.discover_specs(root)
                got = {k: (v.status, v.file) for k, v in found.items()}
            if got != expected:
                wrong.append(
                    f"  {case}: expected {expected}, got {got}\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"runner_shared.discover_specs mishandled {len(wrong)} of {len(self.TREES)} tree shapes. "
            "Discovery feeds the needs-review sweep, so a spec that vanishes here is never offered for "
            "review and one that appears with the wrong key routes its review record to the wrong "
            f"subject:\n" + "\n".join(wrong),
        )

    def test_it_never_raises_on_a_nonexistent_root(self) -> None:
        """Kept separate: no fixture tree, and the property is about not raising on an absent path."""
        self.assertEqual(
            rs.discover_specs(Path("/nonexistent/nope")),
            {},
            "an absent root must yield {} rather than raise; this function runs during discovery on "
            "arbitrary repos, where a crash would take down the whole sweep",
        )

    def test_enumeration_reuses_the_shared_authority(self) -> None:
        """Kept separate: a SOURCE census, structurally unlike the behavior rows above.

        Two claims, one subject: the module must call the shared spec iterator and must NOT introduce
        a second `records/specs` path literal. `check_engine.check_review_dangling` deliberately avoids
        a second reviews-path literal; the same discipline applies to the specs tree. The AST is
        inspected rather than the raw text so a docstring that MENTIONS the path (explaining why it is
        absent) does not trip the guard.
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
        problems = []
        if offenders:
            problems.append(f"new `records/specs` path literal(s): {offenders!r}")
        if "_iter_spec_records" not in src:
            problems.append(
                "runner_shared no longer calls the shared `_iter_spec_records` iterator"
            )
        self.assertEqual(
            problems,
            [],
            "spec enumeration must go through the existing record authority, not a fresh path "
            "string: "
            + "; ".join(problems)
            + ". A second path mechanism is how one surface starts seeing a different set of specs "
            "than another (for example missing the terminal subdirectories).",
        )


class TypeScopedSweepTests(unittest.TestCase):
    """`sweep_review_candidates_for_type` selects needs-review artifacts WITHOUT widening the default.

    Two tables replace nine tests. The first is a STATUS grid whose expectation is taken from the
    shared policy table at runtime rather than hardcoded, so the sweep and the dispatch table are
    asserted to agree BY CONSTRUCTION (R-16); it also asserts, on every row, that the DEFAULT sweep
    stays IPD-only with a spec present, which is spec `25kzda` 2.4a property 1 and the silent-widening
    failure mode. The second is a TYPE grid, since type scoping is the other axis.
    """

    #: (status, why this row exists)
    STATUSES = (
        (
            "to-review",
            "the one status that NEEDS a review; if it stopped being swept the workflow "
            "would never be offered anything to do",
        ),
        (
            "draft",
            "no spec completeness parser exists yet, so an undetermined draft fails toward "
            "EXCLUSION rather than being swept half-written",
        ),
        (
            "reviewed",
            "already reviewed: sweeping it would loop the reviewer over its own output",
        ),
        ("approved", "past review"),
        ("implemented", "past review, at the far end of the lifecycle"),
        ("parked", "out of the flow; must not be pulled back in by a sweep"),
    )

    def test_the_sweep_agrees_with_the_shared_policy_table_at_every_status(
        self,
    ) -> None:
        wrong = []
        for status, why in self.STATUSES:
            with TemporaryDirectory() as d:
                root = Path(d)
                _write_spec(root, "aaa111", status)
                swept = rs.sweep_review_candidates_for_type(root, "spec")
                default = rs.sweep_review_candidates({}, repo=root)
            table = policy.needs_review("spec", status)
            problems = []
            if (swept == ["aaa111"]) is not bool(table):
                problems.append(
                    f"sweep returned {swept!r} but run_selection_policy.needs_review('spec', "
                    f"{status!r}) says {table!r}"
                )
            if default != []:
                problems.append(
                    f"the DEFAULT sweep returned {default!r} with a spec present; it must stay "
                    "IPD-only (it is manifest-driven, so a spec can only appear if the default was "
                    "widened)"
                )
            if problems:
                wrong.append(
                    f"  status={status!r}:\n    "
                    + "\n    ".join(problems)
                    + f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the spec sweep disagrees with the shared policy table (or widened the default) at "
            f"{len(wrong)} of {len(self.STATUSES)} statuses. The sweep and the dispatch table must "
            "agree BY CONSTRUCTION (R-16): if they diverge, an artifact is offered for review by one "
            "surface and refused by the other. A DEFAULT-sweep failure is the more serious one: it "
            "means every existing IPD-only caller silently started sweeping specs too.\n"
            + "\n".join(wrong),
        )

    #: (spec_type argument, expected result with one to-review spec present, why this row exists)
    TYPES = (
        (
            "spec",
            ["aaa111"],
            "THE POSITIVE ROW: the type that resolves. Without it every empty row below is vacuous",
        ),
        (
            "Spec",
            ["aaa111"],
            "type matching is case-INSENSITIVE, measured. Recorded so a later 'fix' that makes it "
            "case-sensitive is seen as the behavior change it is",
        ),
        (
            "ipd",
            [],
            "the ipd route reads the manifest, and no manifest was passed, so a spec on disk must NOT "
            "leak into an ipd sweep",
        ),
        (
            "specs",
            [],
            "the PLURAL tree name is not the artifact type; accepting it would blur the record-tree "
            "name and the subject type",
        ),
        (
            "backlog",
            [],
            "an unswept record type yields nothing rather than falling back to specs",
        ),
        ("research", [], "same, for another record type"),
        ("prompt", [], "same, for another record type"),
        (
            "",
            [],
            "the empty type must sweep NOTHING, or a caller that forgot the argument sweeps all",
        ),
    )

    def test_only_the_named_type_is_swept(self) -> None:
        wrong = []
        for spec_type, expected, why in self.TYPES:
            with TemporaryDirectory() as d:
                root = Path(d)
                _write_spec(root, "aaa111", "to-review")
                got = rs.sweep_review_candidates_for_type(root, spec_type)
            if got != expected:
                wrong.append(
                    f"  spec_type={spec_type!r}: expected {expected!r}, got {got!r}\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"type scoping is wrong for {len(wrong)} of {len(self.TYPES)} type arguments, with one "
            "`to-review` SPEC on disk. Rows returning the spec where [] was expected mean the scoping "
            "leaks (the sweep is really a union over all trees and the type argument is decorative); "
            "the `spec` row returning [] instead means spec review discovery is dead and every other "
            f"row here is vacuous:\n" + "\n".join(wrong),
        )

    def test_a_terminal_directory_excludes_regardless_of_status(self) -> None:
        """Kept separate: materially different setup (the spec is written into `specs/superseded/`,
        not the flat tree), and the property is about the DIRECTORY overriding the status."""
        with TemporaryDirectory() as d:
            root = Path(d)
            dd = root / ".aw" / "records" / "specs" / "superseded"
            dd.mkdir(parents=True)
            (dd / "20260906-aaa111-01-aaa111-x.spec.md").write_text(
                _spec_text("aaa111", "to-review"), encoding="utf-8"
            )
            self.assertEqual(
                rs.sweep_review_candidates_for_type(root, "spec"),
                [],
                "a spec in a TERMINAL directory must never be swept, whatever its `- Status:` says. "
                "Directory carries disposition and status carries readiness, so a superseded spec "
                "left at `to-review` would otherwise be offered for review forever",
            )

    def test_the_ipd_route_delegates_rather_than_forking(self) -> None:
        """Kept separate: the assertion compares TWO FUNCTIONS against each other rather than against
        a literal, which is a structurally different claim (equivalence, not a value)."""
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
                "the type-scoped entry point must DELEGATE the ipd case to the existing sweep. A "
                "forked reimplementation is how the two drift into offering different plan sets",
            )

    def test_type_scoping_has_no_default(self) -> None:
        """Kept separate: a signature introspection, not a behavior probe.

        A defaulted `spec_type` is exactly how a later caller silently widens the default sweep: it
        would omit the argument, get `spec` (or whatever the default became), and never notice.
        """
        import inspect

        sig = inspect.signature(rs.sweep_review_candidates_for_type)
        self.assertIs(
            sig.parameters["spec_type"].default,
            inspect.Parameter.empty,
            "`spec_type` must stay REQUIRED. Giving it a default lets a caller sweep a type it never "
            "asked for, which is the silent widening spec `25kzda` 2.4a property 1 forbids",
        )


if __name__ == "__main__":
    unittest.main()

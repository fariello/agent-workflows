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

WHY TABLES: most clusters here were tests that differed only in their DATA (one name string, one
config value, one severity/threshold pair, one tree shape) and each asserted one thing. Those are rows.
A table also matches the realistic regression: these are CLOSED VOCABULARIES and ORDERED comparisons,
so a renumbering, a re-keyed map, or a flipped comparison moves SEVERAL rows at once and is only
recognizable as one cause when the rows are reported together.
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


def _render(rounds, subject_id="15zvu6", subject_type="ipd"):
    return rf.render_review(
        subject_id=subject_id,
        subject_type=subject_type,
        reviewed_at="2026-08-30",
        reviewer="opencode/test",
        verdict="APPROVE WITH REVISIONS APPLIED",
        rounds=rounds,
    )


#: A hand-written document body, used where the WRITER cannot produce the shape under test (a row with
#: the wrong cell count, an out-of-vocabulary severity). Parameterized so those rows stay one-liners.
def _handwritten(findings_rows: str, decisions_rows: str = "") -> str:
    text = (
        "- Subject-Id: abc123\n- Subject-Type: ipd\n- Reviewed-At: 2026-08-30\n"
        "- Reviewer: oc\n- Verdict: APPROVE\n\n"
        "## Round 1\n\n### Findings\n\n"
        "| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision |"
        " Resolution |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n" + findings_rows
    )
    if decisions_rows:
        text += (
            "\n### Decisions\n\n"
            "| ID | Question | Chosen | Alternatives considered | Basis | Reversible |\n"
            "| --- | --- | --- | --- | --- | --- |\n" + decisions_rows
        )
    return text


# --------------------------------------------------------------------------------------
# E-01: the naming facet.
# --------------------------------------------------------------------------------------


class ReviewNamingTests(unittest.TestCase):
    """The `.review.md` facet is registered, round-trips, and the CLOSED enum rejects look-alikes.

    Four tests became two tables. The facet set and the filename grammar are both CLOSED
    vocabularies, so the realistic regression (a loosened regex, a renamed facet) admits or rejects
    several names at once, and reading the rows together is what identifies that single cause.
    """

    #: (facet, why it must be registered)
    FACETS = (
        (
            "review",
            "the facet this module adds; without it no review filename is conformant",
        ),
        (
            "ipd",
            "pre-existing: the plan facet, which the review grammar is modelled on",
        ),
        ("prompt", "pre-existing"),
        ("spec", "pre-existing, and the other subject type a review can name"),
        ("walkthrough", "pre-existing"),
        ("roadmap", "pre-existing"),
        ("backlog", "pre-existing"),
        ("comms", "pre-existing"),
        ("release", "pre-existing"),
        (
            "other",
            "pre-existing catch-all; losing it would strand every unclassified artifact",
        ),
    )

    def test_the_facet_set_gained_review_and_lost_nothing(self) -> None:
        missing = [
            f"  {facet!r}: {why}"
            for facet, why in self.FACETS
            if facet not in naming.ARTIFACT_TYPE_FACETS
        ]
        self.assertEqual(
            missing,
            [],
            f"{len(missing)} of {len(self.FACETS)} artifact type facets are absent from "
            "naming.ARTIFACT_TYPE_FACETS. This is a CLOSED enum that the filename grammar compiles "
            "from, so a facet that disappears makes every existing file of that type non-conformant "
            "at once. `review` missing means this module's naming never shipped; a PRE-EXISTING facet "
            f"missing means the enum was rewritten rather than extended:\n"
            + "\n".join(missing),
        )

    def test_build_and_parse_round_trip(self) -> None:
        """Kept separate: it asserts the exact composed FILENAME plus the decomposition of its parts,
        which is a round-trip property rather than one accept/reject decision.
        """
        name = rf.build_review_name(
            date="20260829",
            set_id="revgate",
            order=1,
            subject_id6="15zvu6",
            slug="typed-review-findings",
        )
        self.assertEqual(
            name,
            "20260829-revgate-01-15zvu6-typed-review-findings.review.md",
            "the composed name must follow the uniform grammar "
            "`YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`; tools cluster and resolve records by "
            "parsing this, so a changed layout orphans every previously written review",
        )
        parts = rf.parse_review_name(name)
        assert parts is not None, "the name this module just built must parse back"
        self.assertEqual(
            {k: parts[k] for k in ("id6", "set", "nn", "slug")},
            {
                "id6": "15zvu6",
                "set": "revgate",
                "nn": "01",
                "slug": "typed-review-findings",
            },
            "every field must survive the round trip; a mis-sliced id6 is the worst case, since the "
            "id6 is how a review is matched to its subject",
        )

    #: (filename, parses as a clustered name with facet `review`?, why this row exists)
    NAMES = (
        (
            "20260829-revgate-01-15zvu6-slug.review.md",
            True,
            "THE POSITIVE ROW: the canonical shape. Without it every rejection row below is vacuous, "
            "since a parser that rejects everything satisfies them all",
        ),
        (
            "20260829-revgate-01-15zvu6-slug.ipd.md",
            False,
            "a PLAN is not a review. The review parser must not blur the two, or a review record "
            "could claim to be the plan it reviews",
        ),
        (
            "20260829-revgate-01-15zvu6-slug.md",
            False,
            "a bare `.md` carries no facet, so it is not a REVIEW filename (note: it is still "
            "`is_clustered_conformant` for any type, which is why this is asserted through the "
            "review-specific parser rather than the generic one)",
        ),
        (
            "20260829-revgate-01-15zvu6-foo.bar.md",
            False,
            "ADVERSARIAL, and the stated reason the enum is CLOSED: a dotted SLUG must not be read as "
            "a facet, or any file with a dot in its slug would claim a type",
        ),
        (
            "20260829-revgate-01-15zvu6-foo.reviewx.md",
            False,
            "a facet that merely STARTS WITH the real one must be rejected (no prefix matching)",
        ),
        (
            "20260829-revgate-01-15zvu6-foo.reviews.md",
            False,
            "the PLURAL tree name is not the facet; accepting it would blur the directory name and "
            "the artifact type",
        ),
        (
            "20260829-revgate-01-15zvu6-foo.rev.md",
            False,
            "an abbreviation is not the facet (no substring matching either)",
        ),
    )

    def test_only_the_exact_review_facet_is_accepted(self) -> None:
        wrong = []
        for name, expected, why in self.NAMES:
            clustered = naming.parse_clustered(name)
            facet = clustered.group("type") if clustered is not None else None
            got_generic = facet == "review"
            got_specific = rf.parse_review_name(name) is not None
            problems = []
            if got_generic is not expected:
                problems.append(
                    f"naming.parse_clustered reports facet {facet!r}, expected "
                    f"{'review' if expected else 'anything but review'}"
                )
            if got_specific is not expected:
                problems.append(
                    f"rf.parse_review_name {'accepted' if got_specific else 'rejected'} it, expected "
                    f"the opposite"
                )
            if expected and not naming.is_clustered_conformant(name, "review"):
                problems.append(
                    "naming.is_clustered_conformant(name, 'review') is False"
                )
            if problems:
                wrong.append(
                    f"  {name!r}:\n    "
                    + "\n    ".join(problems)
                    + f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.NAMES)} filenames are classified wrongly. The facet enum is "
            "CLOSED precisely so a dotted slug cannot masquerade as a type, and the two parsers "
            "(generic clustered + review-specific) must agree on every name, since one is used to "
            "cluster records and the other to resolve a review's subject. Several look-alike rows "
            "being accepted at once means the facet match loosened into a prefix or substring test:\n"
            + "\n".join(wrong),
        )


class TypeFacetHazardTests(unittest.TestCase):
    """F-8 guard: a `.review.md` must NOT look status-settable to `aw set`.

    A review's state is its Verdict plus per-finding Decision values, NOT a `- Status:` bullet, so it
    has no status lifecycle to transition. `status_set.detect_artifact_type` ITERATES
    `artifact_naming.TYPE_FACET` and returns the matched record type, so a bare `reviews` entry there
    would silently make `aw set` accept a review file. This test FAILS if that entry is added without
    the matching skip.
    """

    #: (filename, body, expected detect_artifact_type result, why this row exists)
    FILES = (
        (
            "20260829-revgate-01-15zvu6-slug.review.md",
            None,  # rendered by the real writer, so the guard is tested on a REAL record
            None,
            "THE GUARD: a review must detect as NO status-settable type. If it detected as one, "
            "`aw set` would accept a review file and write a `- Status:` bullet into an artifact "
            "whose state is its Verdict, inventing a lifecycle it does not have",
        ),
        (
            "20260829-revgate-01-15zvu6-slug.ipd.md",
            "# IPD: x\n\n- Id: 15zvu6\n",
            "plans",
            "CONTROL: the guard above must be specific to reviews. If detection were simply broken "
            "for everything, the review row would pass for the wrong reason",
        ),
        (
            "20260829-revgate-01-15zvu6-slug.spec.md",
            "# Spec: x\n\n- Id: 15zvu6\n",
            "specs",
            "second control, and the other artifact a review can take as its subject",
        ),
        (
            "20260829-revgate-01-15zvu6-slug.backlog.md",
            "# Backlog: x\n\n- Id: 15zvu6\n",
            "backlog",
            "third control, over a tree whose facet name equals its directory name",
        ),
    )

    def test_only_status_bearing_artifacts_are_status_settable(self) -> None:
        wrong = []
        for name, body, expected, why in self.FILES:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                path = root / name
                path.write_text(
                    _render([rf.Round(1, (_finding(),), ())]) if body is None else body,
                    encoding="utf-8",
                )
                got = status_set.detect_artifact_type(path, root)
            if got != expected:
                wrong.append(
                    f"  {name}: expected detect_artifact_type -> {expected!r}, got {got!r}\n"
                    f"    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"status_set.detect_artifact_type mishandled {len(wrong)} of {len(self.FILES)} filenames. "
            "Detection iterates artifact_naming.TYPE_FACET, so the review row failing almost always "
            "means a bare `reviews` entry was added to that map WITHOUT the matching skip in "
            "detect_artifact_type; the control rows failing instead means detection broke generally "
            f"and the review row is passing vacuously:\n" + "\n".join(wrong),
        )

    def test_reviews_absent_from_type_facet(self) -> None:
        """Kept separate: asserts the MAP directly, which is the cause the test above only infers.

        Both are wanted: the behavior assertion is what users feel, and this one names the exact edit
        that causes it, so the failure is actionable without reading `detect_artifact_type`.
        """
        self.assertNotIn(
            "reviews",
            naming.TYPE_FACET,
            "adding `reviews` to TYPE_FACET requires a matching skip in "
            "status_set.detect_artifact_type, or `aw set` will accept a review file",
        )


# --------------------------------------------------------------------------------------
# E-02: writer/parser fidelity and the never-raise contract.
# --------------------------------------------------------------------------------------


class WriterParserTests(unittest.TestCase):
    """What the writer emits, the parser recovers; what it cannot parse, it DIAGNOSES.

    The never-raise contract is why the diagnostics are tabulated rather than tested one by one: this
    parser runs inside `aw check` and inside two status gates, so ANY input must yield a document with
    diagnostics rather than an exception. A table over hostile inputs states that contract once, and
    reports every input that regressed in a single run.
    """

    def test_every_column_round_trips(self) -> None:
        """Kept separate: a nine-field identity over ONE document, not a row of varying data."""
        f = _finding()
        doc = rf.parse_review_text(_render([rf.Round(1, (f,), ())]))
        self.assertEqual(
            doc.diagnostics,
            (),
            "the writer's own output must parse CLEAN; a diagnostic here means writer and parser "
            "disagree about the format, and every record this tool writes is already unreadable",
        )
        self.assertEqual(
            (
                doc.subject_id,
                doc.subject_type,
                doc.reviewed_at,
                doc.reviewer,
                doc.verdict,
            ),
            (
                "15zvu6",
                "ipd",
                "2026-08-30",
                "opencode/test",
                "APPROVE WITH REVISIONS APPLIED",
            ),
            "the metadata header must round-trip: the subject id and type are how a record is matched "
            "to its artifact, and the verdict is what the readiness computation reads",
        )
        (got,) = doc.current_findings()
        differing = [
            f"  {field}: wrote {getattr(f, field)!r}, read back {getattr(got, field)!r}"
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
            )
            if getattr(got, field) != getattr(f, field)
        ]
        self.assertEqual(
            differing,
            [],
            f"{len(differing)} of 9 finding columns did not survive the round trip. Several columns "
            "differing together usually means a column was INSERTED or REMOVED and the cells shifted, "
            "which silently re-labels every existing record's data:\n"
            + "\n".join(differing),
        )

    #: (case, cell value written into the `finding` column, value expected back, why this row exists)
    CELLS = (
        (
            "an embedded pipe",
            "a | b | c",
            "a | b | c",
            "the pipe is the table's column separator, so it MUST be escaped on write and recovered "
            "on read; unescaped, one finding's prose would silently become extra columns",
        ),
        (
            "an embedded newline",
            "a\nb",
            "a b",
            "MEASURED, not assumed: a newline collapses to a SPACE, because a markdown table row is "
            "one line. Recorded so the lossy step is known rather than discovered later",
        ),
        (
            "surrounding whitespace",
            "  padded  ",
            "padded",
            "cells are stripped, which is what makes a hand-aligned table parse the same as a "
            "machine-written one",
        ),
        (
            "backticked code",
            "tick `code`",
            "tick `code`",
            "reviewers cite symbols in backticks constantly; the parser must not strip markup it does "
            "not own",
        ),
        (
            "a bare hyphen rule",
            "---",
            "---",
            "ADVERSARIAL: a cell whose text looks like the table's own DELIMITER row must survive as "
            "content, not be mistaken for structure",
        ),
        (
            "an empty cell",
            "",
            "",
            "an empty cell is data, not a malformed row; treating it as a parse failure would "
            "diagnose ordinary records",
        ),
    )

    def test_hostile_cell_contents_survive_the_round_trip(self) -> None:
        wrong = []
        for case, written, expected, why in self.CELLS:
            doc = rf.parse_review_text(
                _render([rf.Round(1, (_finding(finding=written),), ())])
            )
            got = doc.current_findings()[0].finding if doc.current_findings() else None
            problems = []
            if doc.diagnostics:
                problems.append(
                    f"diagnostics fired: {[d.code for d in doc.diagnostics]}"
                )
            if got != expected:
                problems.append(
                    f"wrote {written!r}, expected {expected!r} back, got {got!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n    " + "\n    ".join(problems) + f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.CELLS)} hostile cell values did not survive the writer/parser "
            "round trip. Findings prose is written by reviewers and contains pipes, newlines and "
            "markup as a matter of course, so a failure here corrupts real records rather than "
            "synthetic ones. Several rows failing together points at the escaping step, not at the "
            f"individual characters:\n" + "\n".join(wrong),
        )

    #: (case, document text, expected diagnostic codes (subset), expected surviving finding ids
    #:  or None to skip, why this row exists)
    DIAGNOSED = (
        (
            "a row with far too few cells, between two good rows",
            _handwritten(
                "| PR-001 | high | IN | a | p:1 | good row | Low | open | todo |\n"
                "| PR-002 | far too few cells |\n"
                "| PR-003 | high | IN | a | p:1 | another good row | Low | fixed | done |\n"
            ),
            (rf.D_MALFORMED_ROW,),
            ["PR-001", "PR-003"],
            "ONE BAD ROW MUST NOT BLIND A READER: the good rows around it still parse. If a single "
            "malformed row discarded the document, an unresolved blocker could be hidden by adding a "
            "typo elsewhere in the table",
        ),
        (
            "an out-of-vocabulary severity and decision",
            _handwritten(
                "| PR-001 | catastrophic | IN | a | p:1 | x | Low | maybe | y |\n"
            ),
            (rf.D_UNKNOWN_SEVERITY, rf.D_UNKNOWN_DECISION),
            ["PR-001"],
            "unknown values are DIAGNOSED, never silently coerced. Coercing `catastrophic` to a known "
            "severity would change what gates; dropping it would hide the finding entirely",
        ),
        (
            "a document with metadata but no rounds",
            "- Subject-Id: abc123\n- Subject-Type: ipd\n- Reviewed-At: x\n- Reviewer: y\n"
            "- Verdict: z\n",
            (rf.D_NO_ROUNDS,),
            [],
            "a review with no round recorded nothing; it must be diagnosed rather than read as a "
            "clean review with zero findings, which is what a gate would treat as APPROVED",
        ),
        (
            "rounds but no metadata",
            "## Round 1\n\n### Findings\n\n",
            (rf.D_MISSING_META,),
            [],
            "without `- Subject-Id:`/`- Subject-Type:` the record attests nothing about any artifact, "
            "so the missing header is itself the defect",
        ),
        (
            "the empty string",
            "",
            (rf.D_MISSING_META, rf.D_NO_ROUNDS),
            [],
            "DEGENERATE: an empty file must diagnose, not raise. This parser runs inside `aw check` "
            "and two status gates, where an exception is commonly 'handled' by skipping the gate",
        ),
        (
            "whitespace only",
            "\n\n",
            (rf.D_MISSING_META, rf.D_NO_ROUNDS),
            [],
            "degenerate: blank input",
        ),
        (
            "prose that is not markdown at all",
            "not markdown at all",
            (rf.D_MISSING_META, rf.D_NO_ROUNDS),
            [],
            "degenerate: a wrong file handed to the parser (a misnamed note, say)",
        ),
        (
            "a heading and a bare table fragment",
            "## Round\n| | |",
            (rf.D_MISSING_META, rf.D_NO_ROUNDS),
            [],
            "degenerate: partial structure, which is the shape a truncated write leaves behind",
        ),
        (
            "nothing but pipes",
            "|||",
            (rf.D_MISSING_META, rf.D_NO_ROUNDS),
            [],
            "degenerate: table punctuation with no table",
        ),
    )

    def test_every_hostile_document_diagnoses_and_never_raises(self) -> None:
        wrong = []
        for case, text, expected_codes, expected_ids, why in self.DIAGNOSED:
            problems = []
            try:
                doc = rf.parse_review_text(text)
            except Exception as exc:  # noqa: BLE001 - the never-raise contract is the property
                wrong.append(
                    f"  {case}: RAISED {type(exc).__name__}: {exc}\n    rule: {why}\n"
                    "    the never-raise contract is the point: this parser runs inside gates where "
                    "an exception is commonly handled by skipping the gate"
                )
                continue
            if not isinstance(doc, rf.ReviewDocument):
                problems.append(f"returned {type(doc).__name__}, not a ReviewDocument")
            codes = [d.code for d in doc.diagnostics]
            absent = [c for c in expected_codes if c not in codes]
            if absent:
                problems.append(
                    f"expected diagnostic code(s) {absent} to fire; got {codes}"
                )
            if expected_ids is not None:
                got_ids = [f.id for f in doc.current_findings()]
                if got_ids != expected_ids:
                    problems.append(
                        f"expected surviving findings {expected_ids}, got {got_ids}"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n    " + "\n    ".join(problems) + f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.DIAGNOSED)} hostile documents were mishandled. Two contracts "
            "are under test at once: the parser NEVER raises (it runs inside `aw check` and two status "
            "gates, where a crash tends to be swallowed and the gate skipped), and it names WHICH "
            "defect it found so the operator knows what to fix. A row that produced no diagnostics at "
            "all is the dangerous direction: a malformed record then reads as a clean review, which a "
            f"gate treats as approval:\n" + "\n".join(wrong),
        )

    def test_unknown_values_are_preserved_rather_than_coerced(self) -> None:
        """Kept separate: asserts the PRESERVED cell text plus the two `*_known` flags, which is a
        different shape of claim than "this diagnostic fired" and is the reason coercion is refused.
        """
        doc = rf.parse_review_text(
            _handwritten(
                "| PR-001 | catastrophic | IN | a | p:1 | x | Low | maybe | y |\n"
            )
        )
        (got,) = doc.current_findings()
        self.assertEqual(
            (got.severity, got.severity_known, got.decision, got.decision_known),
            ("catastrophic", False, "maybe", False),
            "an out-of-vocabulary severity/decision must be kept VERBATIM and flagged unknown. "
            "Coercing it to a known value would change whether the finding gates, and silently "
            "dropping it would hide the finding; keeping it with `*_known=False` lets the gate "
            "fail closed while the operator still sees what was written",
        )

    def test_file_round_trip(self) -> None:
        """Kept separate: real filesystem I/O, and it asserts `doc.path`, which only the file route sets."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "20260829-revgate-01-15zvu6-slug.review.md"
            rf.write_review(
                path,
                subject_id="15zvu6",
                subject_type="ipd",
                reviewed_at="2026-08-30",
                reviewer="oc",
                verdict="APPROVE",
                rounds=[rf.Round(1, (_finding(),), ())],
            )
            doc = rf.parse_review_file(path)
            self.assertEqual(
                (doc.diagnostics, doc.subject_id, doc.subject_type, doc.path),
                ((), "15zvu6", "ipd", path),
                "a record written to disk must read back clean, with its subject pair intact and its "
                "`path` recorded; callers report that path as the file to fix",
            )

    def test_unreadable_file_diagnoses_rather_than_raising(self) -> None:
        """Kept separate: an absent PATH rather than hostile CONTENT, and its own diagnostic code."""
        doc = rf.parse_review_file(Path("/nonexistent/nope.review.md"))
        self.assertIn(
            rf.D_UNREADABLE,
            [d.code for d in doc.diagnostics],
            "an unreadable path must produce the D_UNREADABLE diagnostic, not an exception: the "
            "checker walks a directory listing that can race with a delete",
        )


# --------------------------------------------------------------------------------------
# E-03: rounds.
# --------------------------------------------------------------------------------------


class RoundTests(unittest.TestCase):
    """Which round is CURRENT, and which findings a current round leaves unresolved.

    Three tests became one table over round shapes, because the whole point of rounds is that only
    the LAST one decides, and that is a property of the SET of rounds rather than of any one shape.
    The gate reads `unresolved_findings()`, so every row also asserts what that returns: a round
    boundary that stops superseding would resurrect already-fixed findings and block approvals
    permanently.
    """

    #: (case, rounds, expected current round number, current finding ids, unresolved ids, why)
    SHAPES = (
        (
            "a single round",
            [rf.Round(1, (_finding(fid="PR-001", decision="open"),), ())],
            1,
            ["PR-001"],
            ["PR-001"],
            "the base case: with one round, current IS round 1. Without this row a 'current = last' "
            "implementation that returned nothing for a single round would pass",
        ),
        (
            "two rounds with different findings",
            [
                rf.Round(
                    1, (_finding(fid="PR-001", severity="high", decision="open"),), ()
                ),
                rf.Round(
                    2, (_finding(fid="PR-009", severity="low", decision="fixed"),), ()
                ),
            ],
            2,
            ["PR-009"],
            [],
            "CURRENT IS THE LAST ROUND, not the union: a second round REPLACES the first's view, so "
            "round 1's open finding is no longer current",
        ),
        (
            "two rounds where round 2 fixes round 1's finding",
            [
                rf.Round(
                    1, (_finding(fid="PR-001", severity="high", decision="open"),), ()
                ),
                rf.Round(
                    2, (_finding(fid="PR-001", severity="high", decision="fixed"),), ()
                ),
            ],
            2,
            ["PR-001"],
            [],
            "THE LOAD-BEARING CASE: a HIGH/open finding that round 2 marks fixed must NOT gate. If "
            "superseding failed here, a re-reviewed artifact could never be approved however many "
            "rounds fixed it",
        ),
        (
            "one round holding every decision value",
            [
                rf.Round(
                    1,
                    (
                        _finding(fid="PR-001", decision="fixed"),
                        _finding(fid="PR-002", decision="deferred"),
                        _finding(fid="PR-003", decision="open"),
                        _finding(fid="PR-004", decision="replan"),
                    ),
                    (),
                )
            ],
            1,
            ["PR-001", "PR-002", "PR-003", "PR-004"],
            ["PR-002", "PR-003", "PR-004"],
            "ONLY `fixed` COUNTS AS RESOLVED. A DEFERRED finding is a deliberate decision NOT to fix, "
            "so it stays unresolved; treating deferral as resolution would make it a silent override. "
            "This row also pins ORDER, since findings are reported in the order the reviewer wrote them",
        ),
    )

    def test_the_current_round_decides_and_only_fixed_resolves(self) -> None:
        wrong = []
        for (
            case,
            rounds,
            want_number,
            want_current,
            want_unresolved,
            why,
        ) in self.SHAPES:
            doc = rf.parse_review_text(_render(rounds))
            current = doc.current_round()
            problems = []
            if doc.diagnostics:
                problems.append(
                    f"the writer's own output diagnosed: {[d.code for d in doc.diagnostics]}"
                )
            if len(doc.rounds) != len(rounds):
                problems.append(
                    f"expected {len(rounds)} round(s) parsed, got {len(doc.rounds)}"
                )
            if current is None:
                problems.append("current_round() is None")
            elif current.number != want_number:
                problems.append(
                    f"expected current round {want_number}, got {current.number}"
                )
            got_current = [f.id for f in doc.current_findings()]
            if got_current != want_current:
                problems.append(
                    f"expected current findings {want_current}, got {got_current}"
                )
            got_unresolved = [f.id for f in doc.unresolved_findings()]
            if got_unresolved != want_unresolved:
                problems.append(
                    f"expected unresolved {want_unresolved}, got {got_unresolved}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n    " + "\n    ".join(problems) + f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"round semantics are wrong for {len(wrong)} of {len(self.SHAPES)} shapes. The approval "
            "gate reads `unresolved_findings()` off the CURRENT round, so these rows decide whether a "
            "re-reviewed artifact can ever be approved. If the multi-round rows moved together, "
            "round selection changed (current is no longer the last round, or rounds are being "
            "unioned); if the decision-value row moved, the resolved/unresolved split changed and "
            f"deferral may now be silently accepted as a fix:\n" + "\n".join(wrong),
        )

    def test_a_superseded_round_is_still_on_record(self) -> None:
        """Kept separate: it asserts HISTORY is retained (`rounds[0]` keeps its original decision),
        which is the opposite direction from the superseding property above. A parser that DROPPED
        earlier rounds would satisfy every row of that table while destroying the audit trail.
        """
        doc = rf.parse_review_text(
            _render(
                [
                    rf.Round(
                        1,
                        (_finding(fid="PR-001", severity="high", decision="open"),),
                        (),
                    ),
                    rf.Round(
                        2,
                        (_finding(fid="PR-001", severity="high", decision="fixed"),),
                        (),
                    ),
                ]
            )
        )
        self.assertEqual(
            (doc.rounds[0].findings[0].decision, doc.rounds[1].findings[0].decision),
            ("open", "fixed"),
            "round 1 must retain `open` while round 2 says `fixed`: the record is an audit trail, so "
            "superseding must mean 'no longer current', never 'rewritten'",
        )

    def test_duplicate_round_number_is_diagnosed(self) -> None:
        """Kept separate: the only round shape whose expectation is a DIAGNOSTIC rather than a
        (current, unresolved) pair. Two rounds numbered 1 make 'the current round' ambiguous, so the
        ambiguity must be reported rather than resolved by arbitrary ordering.
        """
        doc = rf.parse_review_text(
            _render(
                [
                    rf.Round(1, (_finding(),), ()),
                    rf.Round(1, (_finding(fid="PR-002"),), ()),
                ]
            )
        )
        self.assertIn(
            rf.D_DUPLICATE_ROUND,
            [d.code for d in doc.diagnostics],
            "two rounds sharing a number must be diagnosed; silently picking one makes which findings "
            "are current depend on document order, which no reviewer controls deliberately",
        )


# --------------------------------------------------------------------------------------
# E-08: the optional Decisions section.
# --------------------------------------------------------------------------------------


class DecisionsSectionTests(unittest.TestCase):
    """The Decisions section round-trips, is OPTIONAL, and is per-round like findings."""

    def test_decisions_round_trip_every_column(self) -> None:
        """Kept separate: a six-field identity over ONE document, not varying data."""
        d = rf.Decision(
            id="D-01",
            question="which TYPE_FACET option?",
            chosen="omit the entry",
            alternatives="add entry plus skip",
            basis="status_set.py:175 iterates the map",
            reversible="yes",
        )
        doc = rf.parse_review_text(_render([rf.Round(1, (_finding(),), (d,))]))
        self.assertEqual(
            doc.diagnostics,
            (),
            "a document with a Decisions section must parse clean; the section is written by the same "
            "writer, so a diagnostic means writer and parser disagree",
        )
        (got,) = doc.current_decisions()
        differing = [
            f"  {field}: wrote {getattr(d, field)!r}, read back {getattr(got, field)!r}"
            for field in (
                "id",
                "question",
                "chosen",
                "alternatives",
                "basis",
                "reversible",
            )
            if getattr(got, field) != getattr(d, field)
        ]
        self.assertEqual(
            differing,
            [],
            f"{len(differing)} of 6 decision columns did not survive the round trip. This section is "
            "the WHY behind a review's choices, so a lost column destroys the rationale a later reader "
            "depends on; several columns differing together means a column was inserted or removed and "
            "the cells shifted:\n" + "\n".join(differing),
        )

    #: (case, document text, expected decisions ids, expected findings count, expected diagnostic
    #:  code or None, why this row exists)
    SECTIONS = (
        (
            "no Decisions section at all",
            _render([rf.Round(1, (_finding(),), ())]),
            [],
            1,
            None,
            "the section is OPTIONAL: its absence is VALID, not a silent requirement. If absence "
            "diagnosed, every review without recorded decisions would read as malformed and (per the "
            "gates) block approval",
        ),
        (
            "a malformed Decisions row",
            _handwritten(
                "| PR-001 | high | IN | a | p:1 | x | Low | open | y |\n",
                "| D-01 | too few |\n",
            ),
            [],
            1,
            rf.D_MALFORMED_ROW,
            "a broken decision row is diagnosed and DROPPED, while the FINDINGS in the same round "
            "still parse: a typo in the rationale table must not hide the findings a gate reads",
        ),
    )

    def test_the_section_is_optional_and_failures_are_contained(self) -> None:
        wrong = []
        for case, text, want_ids, want_findings, want_code, why in self.SECTIONS:
            doc = rf.parse_review_text(text)
            problems = []
            got_ids = [x.id for x in doc.current_decisions()]
            if got_ids != want_ids:
                problems.append(f"expected decisions {want_ids}, got {got_ids}")
            if len(doc.current_findings()) != want_findings:
                problems.append(
                    f"expected {want_findings} finding(s) to survive, got "
                    f"{len(doc.current_findings())}"
                )
            codes = [x.code for x in doc.diagnostics]
            if want_code is None:
                if codes:
                    problems.append(f"expected NO diagnostics, got {codes}")
                if "### Decisions" in text:
                    problems.append(
                        "the fixture was supposed to have no Decisions section, but does"
                    )
            elif want_code not in codes:
                problems.append(f"expected diagnostic {want_code!r}, got {codes}")
            if problems:
                wrong.append(
                    f"  {case}:\n    " + "\n    ".join(problems) + f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SECTIONS)} Decisions-section shapes were mishandled. The "
            "section is optional and its failures must be CONTAINED: if absence started diagnosing, "
            "ordinary reviews would read as malformed, and since a malformed record BLOCKS approval "
            f"that turns an optional section into a hard requirement:\n"
            + "\n".join(wrong),
        )

    def test_decisions_are_per_round(self) -> None:
        """Kept separate: two rounds, asserting current-vs-history for decisions the way the round
        table does for findings. Kept because it is the only place decision SUPERSEDING is proven.
        """
        doc = rf.parse_review_text(
            _render(
                [
                    rf.Round(
                        1,
                        (_finding(),),
                        (rf.Decision("D-01", "q1", "c1", "a1", "b1", "yes"),),
                    ),
                    rf.Round(
                        2,
                        (_finding(),),
                        (rf.Decision("D-02", "q2", "c2", "a2", "b2", "no"),),
                    ),
                ]
            )
        )
        self.assertEqual(
            (
                [x.id for x in doc.current_decisions()],
                [x.id for x in doc.rounds[0].decisions],
            ),
            (["D-02"], ["D-01"]),
            "decisions are scoped to their round exactly as findings are: round 2's decisions are "
            "current while round 1's remain on record. A union would present a superseded rationale "
            "as though it still stood",
        )


# --------------------------------------------------------------------------------------
# E-05: the configurable threshold and the shared predicate.
# --------------------------------------------------------------------------------------


class ThresholdTests(unittest.TestCase):
    """`config.findings_gate_threshold` reads `review_findings_gate`, and FAILS CLOSED on anything odd.

    Six tests became one table over the on-disk config value. Every one of them wrote a
    `project.json` and compared one resolved threshold, so the config value is the data. The property
    that matters is the FALLBACK: every unusable shape must resolve to `high` (gate ACTIVE) rather than
    to `off`, and stating them in one table is what makes "a new shape started resolving to off"
    visible as a fail-open regression instead of one odd test.
    """

    #: (case, raw project.json text or None for no file at all, expected threshold, why this row)
    CONFIGS = (
        (
            "no project.json at all",
            None,
            "high",
            "FAIL-CLOSED DEFAULT: an unconfigured repo has the gate ACTIVE at `high`, not disabled. "
            "If this resolved to `off`, every repo that never configured the key would silently stop "
            "blocking on unresolved high findings",
        ),
        (
            "block_at: medium",
            {"block_at": "medium"},
            "medium",
            "the STRICTEST configurable level is honored; without a passing row here the fallback "
            "rows below are vacuous, since 'always return high' would satisfy them all",
        ),
        (
            "block_at: high",
            {"block_at": "high"},
            "high",
            "the default stated explicitly must behave identically to omitting it",
        ),
        (
            "block_at: blocker",
            {"block_at": "blocker"},
            "blocker",
            "the most permissive real level, where only blockers gate",
        ),
        (
            "block_at: off",
            {"block_at": "off"},
            "off",
            "`off` is a DELIBERATE opt-out and must be reachable; a fallback that swallowed it would "
            "make the documented escape hatch a lie",
        ),
        (
            "a bare string instead of an object",
            "medium",
            "medium",
            'TOLERATED shorthand: `"review_findings_gate": "medium"` means the same as the object '
            "form, because a hand-editing operator writes the short form",
        ),
        (
            "a bare string in the wrong case",
            "MEDIUM",
            "medium",
            "MEASURED: the value is normalized case-insensitively, so a shouted config still works",
        ),
        (
            "block_at: an out-of-vocabulary word",
            {"block_at": "nonsense"},
            "high",
            "an unrecognized level falls back to the ACTIVE default rather than disabling the gate; "
            "a typo must never be a silent opt-out",
        ),
        (
            "block_at: low",
            {"block_at": "low"},
            "high",
            "MEASURED: `low` is a SEVERITY but NOT an accepted threshold, so it falls back. Recorded "
            "because 'it is in SEVERITIES so it must be settable' is the natural wrong assumption",
        ),
        (
            "block_at: a number",
            {"block_at": 42},
            "high",
            "a wrong TYPE falls back, since JSON gives no type discipline",
        ),
        (
            "block_at: null",
            {"block_at": None},
            "high",
            "an explicit null is not an opt-out",
        ),
        (
            "an empty object",
            {},
            "high",
            "the key present but empty is as good as absent",
        ),
        (
            "the key absent from an otherwise valid file",
            "__omit__",
            "high",
            "a valid config that simply never mentions the key keeps the active default",
        ),
        (
            "malformed JSON",
            "__raw:{ not json",
            "high",
            "an unparseable config must not disable the gate; the fail-open alternative would mean a "
            "corrupted file silently turns off blocking",
        ),
        (
            "a JSON array instead of an object",
            "__raw:[1, 2, 3]",
            "high",
            "a structurally wrong document falls back too, not just an unparseable one",
        ),
    )

    def test_every_config_shape_resolves_fail_closed(self) -> None:
        wrong = []
        for case, value, expected, why in self.CONFIGS:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                if value is not None:
                    cfg = root / ".aw" / "config"
                    cfg.mkdir(parents=True, exist_ok=True)
                    if isinstance(value, str) and value.startswith("__raw:"):
                        raw = value[len("__raw:") :]
                    else:
                        data = {
                            "schema_version": 2,
                            "preset": "private-target",
                            "role": "target",
                        }
                        if value != "__omit__":
                            data["review_findings_gate"] = value
                        raw = json.dumps(data)
                    (cfg / "project.json").write_text(raw, encoding="utf-8")
                got = config.findings_gate_threshold(root)
            if got != expected:
                wrong.append(
                    f"  {case}: expected {expected!r}, got {got!r}\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"config.findings_gate_threshold mishandled {len(wrong)} of {len(self.CONFIGS)} config "
            "shapes. The direction matters more than the count: a row that should resolve to `high` "
            "but resolved to `off` is a FAIL-OPEN regression, meaning a malformed or absent config "
            "silently disables the findings gate for that repo. Several malformed rows moving together "
            "means the fallback branch changed rather than any single shape being re-judged.\n"
            + "\n".join(wrong),
        )

    def test_the_default_constant_matches_the_resolved_default(self) -> None:
        """Kept separate: asserts the published CONSTANT, which callers import to describe the default,
        rather than the resolution behavior the table covers. The two can drift apart.
        """
        self.assertEqual(
            config.REVIEW_GATE_DEFAULT,
            "high",
            "the constant other modules and docs cite as 'the default' must equal what an "
            "unconfigured repo actually resolves to; otherwise the documented default is wrong",
        )

    def test_the_key_is_not_in_config_schema(self) -> None:
        """F-10: the key rides in `unknown_fields`; registering it in CONFIG_SCHEMA is wrong."""
        self.assertNotIn(
            config.REVIEW_FINDINGS_GATE_KEY,
            config.CONFIG_SCHEMA,
            "the gate key is deliberately NOT a schema field: it rides in `unknown_fields` so an older "
            "toolkit preserves it instead of dropping it as unrecognized. Registering it here would "
            "change that preservation behavior",
        )


class IsGatingTests(unittest.TestCase):
    """`is_gating(severity, threshold)`: an ORDERED comparison over two closed vocabularies.

    Five tests became one table. Four of them already looped over data (the truth table, the `off`
    sweep, the unknown inputs), which is the clearest possible signal that severity x threshold is a
    GRID. Merging them puts the `off` column, the unknown inputs and the normalization cases in the
    same grid as the real levels, so a flipped comparison or a re-ordered severity tuple reports as
    one failure listing every cell that moved.
    """

    #: (severity, threshold, expected, why this cell exists)
    GRID = (
        ("low", "medium", False, "below threshold"),
        ("low", "high", False, "below threshold"),
        ("low", "blocker", False, "below threshold"),
        ("medium", "medium", True, "AT threshold gates: the comparison is >=, not >"),
        ("medium", "high", False, "below threshold"),
        ("medium", "blocker", False, "below threshold"),
        ("high", "medium", True, "above threshold"),
        (
            "high",
            "high",
            True,
            "AT threshold gates, at the DEFAULT threshold: the single most "
            "load-bearing cell, since it is what an unconfigured repo blocks on",
        ),
        (
            "high",
            "blocker",
            False,
            "below threshold: `blocker` deliberately lets a high finding pass",
        ),
        ("blocker", "medium", True, "above threshold"),
        ("blocker", "high", True, "above threshold"),
        ("blocker", "blocker", True, "AT the strictest threshold"),
        ("low", "off", False, "`off` disables the gate for the LOWEST severity"),
        ("medium", "off", False, "`off` disables the gate for medium"),
        ("high", "off", False, "`off` disables the gate at the default severity"),
        (
            "blocker",
            "off",
            False,
            "`off` DISABLES EVEN A BLOCKER, which is the whole meaning of the "
            "opt-out and the row an over-eager 'blockers always gate' fix would break",
        ),
        (
            "bogus",
            "high",
            False,
            "an unknown SEVERITY does not gate: it has no position in the order, "
            "so it cannot be compared (the record's parse diagnostic is what surfaces it instead)",
        ),
        ("", "high", False, "an empty severity does not gate"),
        (
            "high",
            "",
            False,
            "an empty THRESHOLD does not gate; config resolution is what supplies a "
            "real default, so this function must not invent one",
        ),
        ("high", "bogus", False, "an unknown threshold does not gate"),
        (
            "  HIGH ",
            "High",
            True,
            "NORMALIZATION: both arguments are trimmed and case-folded, which is "
            "what lets a hand-written config value and an uppercase table cell compare correctly",
        ),
    )

    def test_the_gating_grid_is_exactly_as_specified(self) -> None:
        wrong = []
        for severity, threshold, expected, why in self.GRID:
            got = rf.is_gating(severity, threshold)
            if bool(got) is not expected:
                wrong.append(
                    f"  is_gating({severity!r}, {threshold!r}): expected {expected}, got {bool(got)}"
                    f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"review_findings.is_gating is wrong in {len(wrong)} of {len(self.GRID)} cells. This "
            "predicate decides whether a finding BLOCKS an approval, so a cell that flipped to False "
            "lets a real finding through and a cell that flipped to True blocks work that should "
            "proceed. Read the failures together: if the AT-threshold cells moved, the comparison "
            "changed between > and >=; if whole severity rows moved, SEVERITIES was re-ordered; if the "
            "`off` column moved, the documented opt-out broke; if only the normalization row moved, "
            f"trimming or case-folding was dropped:\n" + "\n".join(wrong),
        )

    def test_severities_are_ordered_ascending(self) -> None:
        """Kept separate: `is_gating` compares by INDEX, so the tuple order IS the semantics.

        Pinned as an exact tuple because it is a closed, ORDERED vocabulary: re-ordering it silently
        re-keys every cell of the grid above, and inserting a level shifts the comparisons.
        """
        self.assertEqual(
            rf.SEVERITIES,
            ("low", "medium", "high", "blocker"),
            "SEVERITIES is an ORDERED closed vocabulary compared by index. Re-ordering or inserting a "
            "level changes what gates without changing any threshold value a repo configured",
        )


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
            parsed.unknown_fields.get("review_findings_gate"),
            {"block_at": "blocker"},
            "the key must land in `unknown_fields` on parse; if it is dropped there, the next write "
            "silently deletes a repo's configured threshold",
        )
        self.assertEqual(
            parsed.to_dict().get("review_findings_gate"),
            {"block_at": "blocker"},
            "and it must be written back out unchanged, which is what makes the unknown-fields "
            "carve-out a preservation mechanism rather than a read-only tolerance",
        )


# --------------------------------------------------------------------------------------
# E-09: the record-tree registration.
# --------------------------------------------------------------------------------------


class RecordRegistrationTests(unittest.TestCase):
    """`reviews` is a first-class record class everywhere a record tree is enumerated.

    Six tests became one table over the REGISTRATION SITE. Each asserted that one site knows about
    reviews; the realistic failure is a new site being added (or the record class being renamed) and
    one site being forgotten, which is exactly what a table of sites reports in one run. The
    per-site expectation is derived from the record authority rather than from a hardcoded path where
    possible, so the rows do not become a second copy of the layout.
    """

    #: (site, probe() -> actual, expected, why this site matters)
    SITES = (
        (
            "RecordClass.REVIEWS.value",
            lambda: rp.RecordClass.REVIEWS.value,
            "reviews",
            "the enum member other code switches on; a renamed value breaks every caller at once",
        ),
        (
            "`reviews` is among RecordClass values",
            lambda: "reviews" in [c.value for c in rp.RecordClass],
            True,
            "code that iterates the enum (for example to scaffold or clean every tree) must see it",
        ),
        (
            "engine._DEEP_CLEANUP_ROOTS",
            lambda: (
                ".aw/records/reviews"
                in __import__(
                    "agent_workflows.engine", fromlist=["engine"]
                )._DEEP_CLEANUP_ROOTS
            ),
            True,
            "deep cleanup must REACH the tree; a tree it cannot reach is left behind by an uninstall, "
            "which is how stale records survive into a re-install",
        ),
        (
            "installer scaffold for the `aw` layout",
            lambda: (
                __import__("agent_workflows.engine", fromlist=["engine"])
                ._record_scaffold_dirs("aw")
                .get("reviews")
            ),
            ".aw/records/reviews",
            "a fresh `aw`-layout repo must get the directory, or the first review has nowhere to land",
        ),
        (
            "installer scaffold for the `legacy` layout",
            lambda: (
                __import__("agent_workflows.engine", fromlist=["engine"])
                ._record_scaffold_dirs("legacy")
                .get("reviews")
            ),
            None,
            "DELIBERATELY ABSENT: reviews are net-new, so mapping them into the legacy `.agents/` tree "
            "would invent history that repo never had",
        ),
    )

    def test_every_registration_site_knows_about_reviews(self) -> None:
        wrong = []
        for site, probe, expected, why in self.SITES:
            try:
                got = probe()
            except Exception as exc:  # noqa: BLE001 - a raising site is itself the failure
                got = f"RAISED {type(exc).__name__}: {exc}"
            if got != expected:
                wrong.append(
                    f"  {site}: expected {expected!r}, got {got!r}\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SITES)} record-registration sites disagree about `reviews`. A "
            "record tree must be registered at EVERY site or it is half-real: present for writing but "
            "missed by cleanup, or scaffolded in a layout it does not belong to. The legacy row is the "
            "one whose expectation is ABSENCE, so a failure there means reviews are now being "
            f"scaffolded into `.agents/`, inventing history:\n" + "\n".join(wrong),
        )

    #: (resolver name, probe(tmp) -> the basename(s) it resolves to, why this resolver matters)
    RESOLVERS = (
        (
            "resolve_record_path",
            lambda tmp: [Path(rp.resolve_record_path("reviews", target_repo=tmp)).name],
            "the WRITE path: where a new review record is created",
        ),
        (
            "resolve_record_read_paths",
            lambda tmp: [
                Path(p).name
                for p in rp.resolve_record_read_paths("reviews", target_repo=tmp)
            ],
            "the READ paths: what enumeration walks. An empty result here makes every check over "
            "reviews vacuously clean",
        ),
    )

    def test_both_resolvers_resolve_the_reviews_tree(self) -> None:
        wrong = []
        for name, probe, why in self.RESOLVERS:
            with tempfile.TemporaryDirectory() as tmp:
                got = probe(tmp)
            if not got or got[0] != "reviews":
                wrong.append(
                    f"  {name}: expected the first resolved path to be named 'reviews', got {got!r}\n"
                    f"    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.RESOLVERS)} record path resolvers do not resolve `reviews`. "
            "Write and read must agree: if the write path resolves but the read paths do not, records "
            "are created where nothing ever looks for them and every check over them passes "
            f"vacuously:\n" + "\n".join(wrong),
        )

    def test_fresh_setup_creates_the_tree(self) -> None:
        """Kept separate: it RUNS the installer against a real temp repo, which is materially heavier
        setup than the map lookups above, and asserts both the reported artifact and the real directory.
        """
        from agent_workflows import engine

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            created = engine.create_setup_artifacts(root, use_git=False)
            self.assertIn(
                ".aw/records/reviews/.gitkeep",
                created,
                "setup must REPORT creating the tree, since the report is what the installer shows a "
                "user and what tests of installer idempotence compare",
            )
            self.assertTrue(
                (root / ".aw" / "records" / "reviews").is_dir(),
                "and the directory must actually exist: a reported-but-absent tree means the first "
                "review write fails on a fresh install",
            )

    def test_review_dirs_discovers_in_a_bare_repo(self) -> None:
        """Kept separate: a bare repo (no config, no other records) is a distinct fixture shape, and
        this is the discovery `check_review_dangling` depends on. If it returned nothing, the E-06
        check below would be vacuously clean.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".aw" / "records" / "reviews").mkdir(parents=True)
            dirs = rf.review_dirs(root)
            self.assertTrue(
                any(Path(d).name == "reviews" for d in dirs),
                f"a bare repo must still enumerate its reviews tree; got {dirs!r}. Enumeration "
                "returning nothing makes every review-scoped check pass without reading a single file",
            )


# --------------------------------------------------------------------------------------
# E-06: the advisory dangling check.
# --------------------------------------------------------------------------------------


class ReviewDanglingCheckTests(unittest.TestCase):
    """`check.review-dangling` fires iff a review's `Subject-Id` does not resolve IN ITS DECLARED TREE.

    Seven tests became one table over the (subject id, declared type) pair against one fixture repo
    holding a real plan (`aaa111`) and a real spec (`spc111`). They all wrote a review and compared
    one findings list, so the pair is the data. Reading the rows together is what proves the resolver
    is TYPE-DIRECTED rather than a union over all trees: the union bug is visible only when a row whose
    id exists in the OTHER tree is required to fire, right beside the rows that must stay silent.
    """

    @staticmethod
    def _populate(root: Path) -> None:
        """A repo holding ONE real plan (`aaa111`) and ONE real spec (`spc111`).

        Both must be real, or the type-directed rows are vacuous: the wrong-tree rows work by naming
        an id that genuinely EXISTS in the other tree.
        """
        (root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        (root / ".aw" / "records" / "specs").mkdir(parents=True)
        (root / ".aw" / "records" / "reviews").mkdir(parents=True)
        (
            root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260830-probe-01-aaa111-real.ipd.md"
        ).write_text("# IPD: real\n\n- Id: aaa111\n- Set: probe\n", encoding="utf-8")
        (
            root
            / ".aw"
            / "records"
            / "specs"
            / "20260830-spc111-01-spc111-real.spec.md"
        ).write_text("# Spec: real\n\n- Id: spc111\n", encoding="utf-8")

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._populate(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    @staticmethod
    def _write_review(
        root: Path, subject_id: str, slug: str, subject_type: str = "ipd"
    ) -> Path:
        path = (
            root
            / ".aw"
            / "records"
            / "reviews"
            / f"20260830-probe-01-{subject_id}-{slug}.review.md"
        )
        return rf.write_review(
            path,
            subject_id=subject_id,
            subject_type=subject_type,
            reviewed_at="2026-08-30",
            reviewer="oc",
            verdict="APPROVE",
            rounds=[rf.Round(1, (_finding(),), ())],
        )

    #: (case, reviews to write as (subject_id, slug, subject_type), expected detail substrings per
    #:  finding in order (empty tuple means NO finding expected), why this row exists)
    SUBJECTS = (
        (
            "no reviews at all",
            (),
            (),
            "an empty reviews tree is SILENT. A check that complained about nothing would fire in "
            "every repo that has never filed a review",
        ),
        (
            "an ipd subject that exists",
            (("aaa111", "real", "ipd"),),
            (),
            "THE POSITIVE ROW for plans: a review of a real plan must be clean, or filing any review "
            "would dirty the repo",
        ),
        (
            "a spec subject that exists",
            (("spc111", "spec-review", "spec"),),
            (),
            "THE BLOCKER THIS PLAN REMOVES (revsweep `eyh1fu`): before the neutral subject pair, the "
            "field was plan-bound and resolution consulted the plans tree alone, so a review of a real "
            "SPEC was reported dangling and a spec review could not be filed at all",
        ),
        (
            "an ipd subject that does not exist",
            (("zzz999", "ghost", "ipd"),),
            (("zzz999", "ipd"),),
            "the base advisory case: a review naming a plan nobody can find is untidy and must be "
            "reported, naming BOTH the id and the tree it failed to resolve in",
        ),
        (
            "a spec subject that does not exist",
            (("zzz999", "ghost-spec", "spec"),),
            (("zzz999", "spec"),),
            "THE REGRESSION THAT MATTERS MORE than the clean spec row: a resolver that simply stopped "
            "complaining about specs would also make that row pass. A genuinely missing spec subject "
            "must still be reported",
        ),
        (
            "a plan id6 declared as a spec subject",
            (("aaa111", "wrong-tree", "spec"),),
            (("aaa111", "spec"),),
            "TYPE-DIRECTED, NOT A UNION: `aaa111` exists, but as a PLAN. If this resolved, "
            "`Subject-Type` would be decorative and a record naming the wrong tree would pass, which "
            "is exactly the silent misfiling the typed field exists to catch",
        ),
        (
            "a spec id6 declared as an ipd subject",
            (("spc111", "wrong-tree-2", "ipd"),),
            (("spc111", "ipd"),),
            "the SYMMETRIC case, so the type direction is not a spec-only special case; without it a "
            "resolver that unioned only in the ipd direction would pass",
        ),
        (
            "one resolvable and one dangling review together",
            (("aaa111", "real", "ipd"), ("zzz999", "ghost", "ipd")),
            (("zzz999", "ipd"),),
            "NOT VACUOUS AND NOT OVER-FIRING, proven in ONE repo state: exactly one finding, naming "
            "the ghost. A count asserted on a single-review repo cannot distinguish 'fires correctly' "
            "from 'fires on everything'",
        ),
    )

    def test_it_fires_exactly_on_unresolvable_subjects_in_their_declared_tree(
        self,
    ) -> None:
        wrong = []
        for case, reviews, expected, why in self.SUBJECTS:
            # A per-row repo, since rows differ in HOW MANY records exist (the
            # not-over-firing row needs two reviews present at once).
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._populate(root)
                for subject_id, slug, subject_type in reviews:
                    self._write_review(root, subject_id, slug, subject_type)
                drift = check_engine.check_review_dangling(root)
            problems = []
            if len(drift) != len(expected):
                problems.append(
                    f"expected {len(expected)} finding(s), got {len(drift)}: "
                    f"{[(d.rule, d.detail) for d in drift]}"
                )
            else:
                for d, needles in zip(drift, expected):
                    if d.rule != "check.review-dangling":
                        problems.append(
                            f"expected rule 'check.review-dangling', got {d.rule!r}"
                        )
                    absent = [n for n in needles if n not in d.detail]
                    if absent:
                        problems.append(
                            f"the detail must name {absent} (the id and the tree it failed to "
                            f"resolve in); got {d.detail!r}"
                        )
                    if needles and needles[0] not in d.location:
                        problems.append(
                            f"the finding must LOCATE the offending review file; location="
                            f"{d.location!r}"
                        )
            if problems:
                wrong.append(
                    f"  {case}:\n    " + "\n    ".join(problems) + f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"check_engine.check_review_dangling mishandled {len(wrong)} of {len(self.SUBJECTS)} "
            "subject shapes. Resolution must be TYPE-DIRECTED: read the failures together, because a "
            "wrong-tree row going SILENT while the others pass means the resolver became a union over "
            "all trees and `Subject-Type` is now decorative (a misfiled record would pass), whereas "
            "the clean rows going NOISY means a real subject stopped resolving and every legitimate "
            f"review now reports dangling:\n" + "\n".join(wrong),
        )

    #: (case, how to build the record, expected parse diagnostic, expected subject_type read back, why)
    MALFORMED = (
        (
            "the `- Subject-Type:` line is absent",
            "absent",
            rf.D_MISSING_META,
            "",
            "FAIL CLOSED (F-7): an absent type is a LOUD parser diagnostic and the rule does NOT fall "
            "back to the plans tree. A default of `ipd` is precisely how a migration that dropped the "
            "field would stay invisible",
        ),
        (
            "the declared type is out of vocabulary",
            "backlog",
            rf.D_UNKNOWN_SUBJECT_TYPE,
            "backlog",
            "an out-of-vocabulary type gets its OWN diagnostic code, distinct from an absent one, "
            "because the remedies differ (add the field vs correct it); the value is PRESERVED, not "
            "coerced, so the operator sees what was written",
        ),
        (
            "no metadata at all",
            "nometa",
            None,
            None,
            "a file with no header is not this rule's business: the parser reports the missing "
            "metadata, and double-reporting it here would give one defect two voices",
        ),
    )

    def test_an_unusable_subject_type_is_a_parse_error_not_a_dangling_report(
        self,
    ) -> None:
        wrong = []
        for case, mode, expected_code, expected_type, why in self.MALFORMED:
            path = (
                self.root
                / ".aw"
                / "records"
                / "reviews"
                / f"20260830-probe-01-aaa111-{mode}.review.md"
            )
            if mode == "nometa":
                path.write_text("# no metadata here\n\n## Round 1\n", encoding="utf-8")
            else:
                text = rf.render_review(
                    subject_id="aaa111",
                    subject_type="ipd",
                    reviewed_at="2026-08-30",
                    reviewer="oc",
                    verdict="APPROVE",
                    rounds=[rf.Round(1, (_finding(),), ())],
                )
                if mode == "absent":
                    text = text.replace("- Subject-Type: ipd\n", "")
                else:
                    text = text.replace(
                        "- Subject-Type: ipd", f"- Subject-Type: {mode}"
                    )
                path.write_text(text, encoding="utf-8")
            problems = []
            if expected_code is not None:
                doc = rf.parse_review_file(path)
                codes = [d.code for d in doc.diagnostics]
                if expected_code not in codes:
                    problems.append(
                        f"expected parse diagnostic {expected_code!r}, got {codes}"
                    )
                if doc.subject_type != expected_type:
                    problems.append(
                        f"expected subject_type read back as {expected_type!r} (preserved, not "
                        f"coerced), got {doc.subject_type!r}"
                    )
            drift = check_engine.check_review_dangling(self.root)
            if drift:
                problems.append(
                    f"check.review-dangling also fired: {[(d.rule, d.detail) for d in drift]}"
                )
            path.unlink()
            if problems:
                wrong.append(
                    f"  {case}:\n    " + "\n    ".join(problems) + f"\n    rule: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.MALFORMED)} unusable-subject-type records were mishandled. Two "
            "properties are joint here: the PARSER names the defect with its own code, and the dangling "
            "rule stays SILENT so one defect is not reported twice by two subsystems. A dangling "
            "finding appearing alongside the parse diagnostic is the failure to watch for, and so is "
            "an absent type silently resolving against the plans tree, which is how a migration that "
            f"dropped the field would go unnoticed:\n" + "\n".join(wrong),
        )

    def test_the_rule_is_registered_advisory_and_deterministic(self) -> None:
        """Kept separate: a registry lookup, not a repo-state probe.

        A review of a superseded plan is UNTIDY, not dangerous, so the rule is deliberately a warning.
        """
        spec = check_engine.rule_spec("check.review-dangling")
        self.assertEqual(
            (spec.severity, spec.determinism),
            ("warning", check_engine.DET_DETERMINISTIC),
            "the rule must stay ADVISORY (warning) and deterministic: promoting it to `error` would "
            "make a review of a superseded plan block work, which is untidy rather than dangerous",
        )
        self.assertIn(
            "check.review-dangling",
            check_engine.RULE_REGISTRY,
            "an unregistered rule id silently falls back to an empty invariant and a default severity",
        )

    def test_the_rule_gates_no_lifecycle_step(self) -> None:
        """Kept separate: a SOURCE census over `ipd_lint.py`, structurally unlike a registry lookup.

        Advisory-ness is verified by the absence of any lifecycle gate, NOT by an exit code:
        `artifact_core.drift_exit_code` exempts only `info`, so a `warning` drives exit 1 too and an
        exit-code argument would prove nothing (F-13).
        """
        gated = (Path(check_engine.__file__).parent / "ipd_lint.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(
            "check.review-dangling",
            gated,
            "ipd_lint must not consult this rule: wiring an advisory rule into a lifecycle gate turns "
            "'untidy' into 'cannot proceed', which is the promotion this test exists to prevent",
        )

    def test_subject_type_vocabulary_is_closed_and_fully_resolvable(self) -> None:
        """Kept separate: it asserts the CLOSED vocabulary agrees with the checker's tree mapping,
        derived from both sources at runtime. A type present in `SUBJECT_TYPES` but absent from the
        mapping would resolve against NOTHING and report every record of that type as dangling.
        """
        self.assertEqual(
            rf.SUBJECT_TYPES,
            ("ipd", "spec"),
            "the subject-type vocabulary is CLOSED; adding a member requires a resolvable tree for it "
            "(asserted next), so the tuple is pinned to make the addition deliberate",
        )
        mapping = check_engine._review_subject_id_sets(self.root)
        self.assertEqual(
            sorted(mapping),
            sorted(rf.SUBJECT_TYPES),
            "every declared subject type must have a tree to resolve against; a type with no mapping "
            "resolves against nothing and reports EVERY record of that type as dangling",
        )
        self.assertEqual(
            (mapping["ipd"], mapping["spec"]),
            ({"aaa111"}, {"spc111"}),
            "and each tree must yield its OWN ids: if the sets were merged, the type direction would "
            "be lost and a misfiled record would resolve",
        )

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
            f"check_engine must not hardcode a reviews path; found {offenders!r}. A second path "
            "mechanism is how one surface starts enumerating a different set of records than another.",
        )


if __name__ == "__main__":
    unittest.main()

"""Tests for durablecapture Order 01 (`rnkqrc`): `check.ipd-uncarried-obligation`.

An outstanding obligation an IPD records (a `## Deferred / out of scope` row, or an `open`/`deferred`
question) must name a DURABLE CARRIER before that plan may claim `executed`, because
`attention_contract._PLANS_MAP` maps `executed` to the `done` class and an uncarried obligation then
disappears from every attention view with no record that anything was dropped.

Covers:
* V-01 - the typed carrier vocabulary is declared in the schema and is behavior-neutral on its own.
* V-02 - the shared predicate's THREE ESCAPES (handoff / satisfied / declined), and its FOUR REFUSALS
  (no carrier, dangling carrier, terminal-directory carrier, prose-only). Plus the malformed case
  producing a FINDING rather than a traceback, and the `CloseVerdict` shape being mirrored.
* V-03 - the rule blocks at the `pre-transition` lint checkpoint, is silent at every other checkpoint,
  and `lint_text` stays PURE (it resolves nothing, so it can never report the rule).
* V-04 - `aw check` and `aw ipd lint --phase pre-transition` agree on identical fixtures, from ONE
  predicate.
* V-05 - staged severity: a PRE-cutover plan yields a non-failing advisory and a POST-cutover plan
  yields a fail-closed error, demonstrated by running the rule.

EVERY fixture is an ISOLATED tmp repo built under `tmp_path`. No assertion reads this repository's
live plans, live backlog, or live `.aw/records/runs/` (which is gitignored with ZERO tracked files, so
a test reading it would pass on a maintainer's machine and fail in CI or in a lane worktree).

WHAT WAS TABULATED, AND THE ONE RULE THAT GOVERNED THE MERGE. The subject here is DURABILITY: the
valuable property is that an obligation SURVIVES a plan reaching terminal, and the rule is a gate that
either holds or silently stops holding. So the merge was deliberately CONSERVATIVE, and one rule
decided every case: A ROW IS ONLY ALLOWED TO EXIST IF IT ASSERTS THE WHOLE OUTCOME IT REPLACED. Where
an old test made several claims about one input (the verdict AND the path AND the severity AND the
reason), the row carries all of them as columns; no claim was dropped to make a tuple fit. Where two
old tests asserted DIFFERENT KINDS of thing about the same input, the row carries a check-mode column
rather than being weakened to whichever assertion was easier to tabulate.

Three clusters merged, each because its members differed ONLY in data:
1. `evaluate_carrier_obligation`'s per-row verdicts (the three escapes and the refusals), which were
   fifteen tests over one function differing only in the obligation's typed fields and in which
   fixture artifact existed. They are one table whose rows carry (legitimate, path, severity, reason
   needle) and a fixture column.
2. The plan-level rule's outcomes, which were fourteen tests building one plan fixture and asserting
   which surfaces reported it. They are one table whose MODE columns are the plan's DATE (the
   cutover tier), its LANE, and the three surfaces; each row asserts the FULL round trip, meaning the
   evaluator, the `aw check` sweep, and the `pre-transition` lint all at once, which is strictly more
   than any single old test asserted.
3. The schema vocabulary's pure helpers, which were a handful of one-line probes of three pure
   functions.

WHAT WAS DELIBERATELY NOT MERGED, and why, is stated in each surviving test's docstring. The
recurring reasons: the claim is about WHERE a predicate is reached from rather than about any one
fixture's verdict; the setup is materially different (a deliberately unparseable file, a nonexistent
repository root); or the assertion is about a registry entry rather than about a plan.

THE TWO `inspect.getsource` PINS THIS FILE CARRIED ARE GONE, and the reason generalizes past this
file. Both searched a function's SOURCE TEXT for a symbol name in order to claim "this surface calls
the shared predicate" or "this surface does NOT". A substring search cannot establish either: the
positive is satisfied by a COMMENT naming the symbol (measured twice in this repository, once on
`env=pinned_child_env()`), and the NEGATIVE is satisfied in the wrong direction by the same code
reached under any other name, so a merge wired into the documented-pure path through an alias or a
direct `check_engine` call would have left all three assertions green. Both are now proved by DRIVING
the surfaces: the shared evaluator is spied (so the call, or its absence at every checkpoint, is
OBSERVED) and then replaced by a sentinel whose own detail text must surface on both consumers (so
"one predicate backs both" is a fact about output rather than about spelling). See
`test_the_merge_is_wired_into_lint_file_and_not_the_pure_path` and
`test_one_predicate_backs_both_surfaces`.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Optional
from unittest import mock

from agent_workflows import artifact_core as core
from agent_workflows import check_engine as ce
from agent_workflows import ipd_lint
from agent_workflows import ipd_schema as S

RULE = "check.ipd-uncarried-obligation"

# A date strictly BEFORE the cutover (grandfathered) and one strictly AT it (fail-closed). Both are
# derived FROM the constant, so the fixtures cannot drift from the shipped boundary.
_CUT = ce.CARRIER_CUTOVER_DATE
_POST_DATE = "{0}-{1}-{2}".format(_CUT[:4], _CUT[4:6], _CUT[6:])
_PRE_DATE = "2026-09-01"


# --------------------------------------------------------------------------------------
# Isolated fixture builders
# --------------------------------------------------------------------------------------


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="aw_durablecapture_"))
    for lane in ("pending", "executed", "superseded", "not-executed"):
        (d / ".aw" / "records" / "plans" / lane).mkdir(parents=True)
    for status in ("open", "graduated", "done", "parked", "blocked"):
        (d / ".aw" / "records" / "backlog" / status).mkdir(parents=True)
    (d / ".aw" / "records" / "specs").mkdir(parents=True)
    return d


def _backlog_item(repo: Path, *, id6: str = "car111", status: str = "open") -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / status
        / "20260901-{0}-01-{0}-carrier-fixture.md".format(id6)
    )
    p.write_text(
        "# Carrier fixture {0}\n\n"
        "- Id: {0}\n- Status: {1}\n- Priority: medium\n- Work-Kind: bug\n"
        "- Summary: the durable home for the defect under test\n".format(id6, status),
        encoding="utf-8",
    )
    return p


def _carrier_plan(repo: Path, *, id6: str = "carpln", lane: str = "pending") -> Path:
    """A plan used only as a CARRIER TARGET (never the subject under test)."""
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / lane
        / "20260901-carry-01-{0}-carrier-target.ipd.md".format(id6)
    )
    p.write_text(
        "# IPD: carrier target {0}\n\n"
        "- Date: 2026-09-01\n- Kind: child\n- Scope-Paths: x.py\n"
        "- Item-Dependencies: none\n- Status: {1}\n- Set: carry\n- Order: 1\n"
        "- Id: {0}\n\n## Workflow history\n- 2026-09-01 draft (t): created.\n\n"
        "## Goal\ng\n".format(id6, "executed" if lane == "executed" else "approved"),
        encoding="utf-8",
    )
    return p


def _spec(repo: Path, *, id6: str = "carspc") -> Path:
    """A SPEC record, which is never a sufficient carrier but IS resolvable as evidence."""
    p = repo / ".aw" / "records" / "specs" / "20260901-{0}-01-{0}-x.spec.md".format(id6)
    p.write_text(
        "# spec\n\n- Id: {0}\n- Status: approved\n".format(id6), encoding="utf-8"
    )
    return p


def _plan(
    repo: Path,
    *,
    id6: str = "subj01",
    lane: str = "pending",
    date: str = _PRE_DATE,
    status: str = "approved",
    deferred_rows: Optional[str] = None,
    open_questions: str = "",
    performed: bool = True,
) -> Path:
    """The SUBJECT plan. `performed=True` makes its E/V rows satisfy the pre-transition E/V checkpoint,
    so a pre-transition lint isolates THIS rule instead of tripping on unrelated state."""
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / lane
        / "20260901-durable-01-{0}-subject-fixture.ipd.md".format(id6)
    )
    if deferred_rows is None:
        deferred_rows = (
            "- a genuinely out-of-scope note.\n  - Carrier-Declined: not a defect.\n"
        )
    exec_state = "performed" if performed else "pending"
    valid_state = "pass" if performed else "pending"
    body = (
        "# IPD: durable-carrier subject {0}\n\n"
        "- Date: {1}\n- Kind: child\n- Scope-Paths: x.py\n"
        "- Item-Dependencies: none\n- Status: {2}\n- Set: durable\n- Order: 1\n"
        "- Highest E allocated: 01\n- Id: {0}\n\n"
        "## Workflow history\n- {1} draft (t): created.\n\n"
        "## Goal\n\ng\n\n"
        "## Detailed Implementation Checklist (TODO)\n\n"
        "### Task group 1: do the thing\n\n"
        "- [x] E-01 DO THE THING.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: the thing is done\n"
        "  - Execution state: {3}\n\n"
        "## Project conventions discovered (Step 0)\n\n- none\n\n"
        "## Findings\n\n| Id | Severity | Area | What | Evidence |\n|---|---|---|---|---|\n"
        "| F-1 | LOW | x | y | z |\n\n"
        "## Proposed changes (ordered, validatable)\n\n1. do the thing\n\n"
        "## Deferred / out of scope (with reason)\n\n{4}\n"
        "## Scope check\n\n- Over-scope: none\n- Under-scope: none\n\n"
        "## Required tests / validation\n\nthe suite\n\n"
        "## Spec / documentation sync\n\nnone\n\n"
        "## Open questions\n\n{5}\n"
        "## Validation and cross-check (verify before reporting done)\n\n"
        "- [x] V-01 validates E-01\n"
        "  - Required evidence: paste it\n"
        "  - Observed evidence: pasted output here\n"
        "  - Result: {6}\n\n"
        "## Approval and execution gate\n\n- Size assessment: standard\n"
        "- Cohesion rationale: not required\n".format(
            id6,
            date,
            status,
            exec_state,
            deferred_rows,
            open_questions,
            valid_state,
        )
    )
    p.write_text(body, encoding="utf-8")
    return p


def _oq(*, status: str = "open", extra: str = "") -> str:
    lines = [
        "### OQ-01: does the uncarried obligation survive?",
        "",
        "- Blocking: no",
        "- Status: {0}".format(status),
        "- Owner: maintainer",
        "- Resolution or deferral rationale: recorded for the test",
    ]
    if extra:
        lines.append(extra)
    return "\n".join(lines) + "\n"


def _rules(drift) -> list:
    return [d.rule for d in drift if d.rule == RULE]


def _obligation(**fields) -> ce.CarrierObligation:
    return ce.CarrierObligation("deferred", "deferred row 1", 1, dict(fields))


class _RepoCase(unittest.TestCase):
    def setUp(self):
        self.repo = _mkrepo()

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)


# --------------------------------------------------------------------------------------
# V-01: the typed vocabulary, and its behavior-neutrality on its own
# --------------------------------------------------------------------------------------


class SchemaVocabularyTests(unittest.TestCase):
    """The three typed carrier fields, and the pure helpers that read them.

    ONE table replaces the vocabulary half of six tests. Each asserted one property of one field name
    or one input to one of three pure functions, and they were grouped by WHICH FUNCTION rather than by
    what is being stated, which scattered the single coherent claim (there are exactly three fields,
    these are their spellings, and they are matched STRUCTURALLY) across the file.

    Why the table beats them: `CARRIER_FIELDS` is a three-member closed vocabulary whose members are
    parsed out of plan text VERBATIM by `DEFERRED_SUBFIELD_RE`, which names them as literal
    alternatives in its pattern. So the spelling appears in TWO places that must agree, and the table's
    columns assert both at once: the constant, membership in `OQ_FIELDS`, and the regex actually
    matching an indented line bearing that name. A rename that updated the constant and not the regex
    (or the reverse) fails here and would otherwise leave the field silently unreadable from disk.

    THE FIELD NAMES ARE LITERAL STRINGS, NOT `S.CARRIER_*` CONSTANTS. These names are what an author
    types under a deferred row, and the regex matches them verbatim, so the spelling IS the interface.
    Referencing the constants would make a rename invisible, because the constant and the string it
    holds move together.
    """

    #: (the field name AS TYPED IN A PLAN, the constant that must equal it, the verdict path it
    #: produces when it is the only field present (or None when it produces no path on its own), why)
    FIELDS = (
        (
            "Carrier",
            "CARRIER_FIELD",
            "HANDOFF",
            "THE HANDOFF FIELD: `- Carrier: <id6>` names the backlog item or non-terminal plan that "
            "carries the defect onward. It is the primary escape and the only one whose value is "
            "RESOLVED against the trees rather than merely read",
        ),
        (
            "Carrier-Evidence",
            "CARRIER_EVIDENCE_FIELD",
            "SATISFIED",
            "THE SATISFIED FIELD: a repo-relative path to an in-tree artifact showing the defect is "
            "already addressed, resolved by the SAME shared resolver `aw backlog set done --evidence` "
            "uses, so the two cannot disagree about what counts as evidence",
        ),
        (
            "Carrier-Declined",
            "CARRIER_DECLINED_FIELD",
            "DECLINED",
            "THE DECLINED FIELD: the explicit recorded decision that this row needs no carrier. The "
            "reason's MERIT is a reviewer's job, so the predicate only requires that a reason EXISTS - "
            "which is what makes this the one escape needing no repository access at all",
        ),
    )

    def test_each_carrier_field_is_declared_constant_and_structurally_matched(self):
        wrong = []
        for name, constant, _path, why in self.FIELDS:
            problems = []
            actual = getattr(S, constant, None)
            if actual != name:
                problems.append(
                    f"S.{constant} is {actual!r} but the spelling an author types is {name!r}"
                )
            if name not in S.CARRIER_FIELDS:
                problems.append(
                    f"not in S.CARRIER_FIELDS (which is {S.CARRIER_FIELDS!r}), so a consumer "
                    "enumerating the vocabulary from the schema will not see it"
                )
            if name not in S.OQ_FIELDS:
                problems.append(
                    "not declared in S.OQ_FIELDS beside `Finding`; the field would be undocumented "
                    "for an author reading the schema for the OQ subfield vocabulary"
                )
            indented = "  - {0}: a value".format(name)
            m = S.DEFERRED_SUBFIELD_RE.match(indented)
            if m is None:
                problems.append(
                    f"DEFERRED_SUBFIELD_RE does NOT match {indented!r}, so this field cannot be read "
                    "off a deferred row at all: it would parse as absent and the row would be "
                    "reported as uncarried no matter what the author wrote"
                )
            elif m.group("field").strip() != name:
                problems.append(
                    f"DEFERRED_SUBFIELD_RE captured field {m.group('field')!r} from {indented!r}, "
                    f"not {name!r}"
                )
            if problems:
                wrong.append(
                    f"  field {name!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.FIELDS)} carrier fields are wrongly declared. Each spelling "
            "lives in TWO places that must agree (the constant, and the literal alternatives inside "
            "`DEFERRED_SUBFIELD_RE`), so a row failing on the regex while passing on the constant "
            "means exactly that: the vocabulary was renamed in one place. FIX: a field the regex "
            "cannot match reads as ABSENT, which does not fail loudly - it makes a correctly-carried "
            "obligation report as uncarried, and the author has no way to satisfy a gate that cannot "
            f"see their declaration.\n" + "\n".join(wrong),
        )

    def test_the_vocabulary_is_exactly_the_three_escapes_in_verdict_order(self):
        """Two-sided guard: a fourth carrier field, or a reordering, must FAIL rather than pass quietly.

        Kept separate because it is a claim about the TUPLE (its length and its ORDER) rather than
        about any one field. The order is the verdict-path order the predicate checks in, so it is
        semantic, not cosmetic: DECLINED is tested first and wins over a dangling `Carrier`, which
        `CarrierVerdictTests` asserts as a row.
        """
        self.assertEqual(
            S.CARRIER_FIELDS,
            (S.CARRIER_FIELD, S.CARRIER_EVIDENCE_FIELD, S.CARRIER_DECLINED_FIELD),
            "CARRIER_FIELDS must be exactly the three escapes, in verdict-path order. A FOURTH "
            "escape is a maintainer decision about what may discharge an obligation, never a tweak.",
        )
        self.assertEqual(
            {name for name, _c, _p, _w in self.FIELDS},
            set(S.CARRIER_FIELDS),
            "the FIELDS table and CARRIER_FIELDS have diverged; a new field with no row above would "
            "have its spelling and its regex matching asserted nowhere.",
        )


class CarrierHelperTests(unittest.TestCase):
    """The pure helpers: `parse_carrier_ids`, `carrier_fields_present`, `DEFERRED_SUBFIELD_RE`.

    ONE table replaces three tests (`test_parse_carrier_ids_splits_good_from_bad_without_raising`,
    `test_parse_carrier_ids_tolerates_empty_and_none`, `test_carrier_fields_present_is_presence_only`)
    plus the negative half of `test_deferred_subfield_pattern_matches_only_the_typed_fields`. All were
    single-input probes of pure functions, with the inputs bundled several to a method so the first
    failure hid the others.

    WHICH HELPER IS A COLUMN, not a class, because the three answer one question between them: WHAT DOES
    THE ROW DECLARE, without ever deciding whether it resolves. That separation is the module's design
    (pure schema layer versus repo-aware `check_engine`), and keeping the three adjacent is what makes
    it legible: `carrier_fields_present({"Carrier": "zzzzzz"})` is TRUE for a dangling id6, which looks
    wrong until you see it beside the parse and the regex and understand that presence is all this
    layer claims.
    """

    #: (which helper: "parse" | "present" | "regex", the input, the expected result, why)
    HELPERS = (
        (
            "parse",
            "car111, badtoken, , abc123",
            (("car111", "abc123"), ("badtoken",)),
            "THE CORE CASE: good and bad tokens SPLIT rather than raising, and an empty token between "
            "commas is dropped entirely rather than becoming a third malformed entry. The good tokens "
            "survive beside the bad one, which is what lets a partly-wrong value still report the "
            "specific token at fault instead of rejecting the whole line",
        ),
        (
            "parse",
            "",
            ((), ()),
            "an EMPTY value parses to two empty tuples, not an error. The caller decides what absence "
            "means, which is how `evaluate_carrier_obligation` can distinguish `no field at all` "
            "(reported as NO durable carrier) from `a field with a bad token` (reported as malformed)",
        ),
        (
            "parse",
            None,
            ((), ()),
            "NONE is tolerated identically, so a caller reading a missing dict key need not guard. A "
            "helper that raised on None would push that guard into every call site and one of them "
            "would eventually forget it",
        ),
        (
            "parse",
            "CAR111",
            ((), ("CAR111",)),
            "id6 tokens are LOWERCASE ONLY: an uppercase token is MALFORMED, not silently normalized. "
            "That matters because ids are matched literally against filenames and `- Id:` lines, so "
            "accepting `CAR111` here would produce a carrier that resolves to nothing while looking "
            "valid to the author",
        ),
        (
            "parse",
            "see the backlog",
            ((), ("see the backlog",)),
            "PROSE IN A TYPED FIELD is malformed, which is the whole point of the field being typed. A "
            "value like this is the likeliest real mistake and it must become a NAMED finding rather "
            "than an accepted non-reference",
        ),
        (
            "present",
            {},
            False,
            "no fields at all: nothing is declared. The baseline",
        ),
        (
            "present",
            {"Carrier": "   "},
            False,
            "a WHITESPACE-ONLY value declares nothing. An author who typed the field and left it blank "
            "has not handed anything off, and treating the empty field as a declaration would make the "
            "gate trivially satisfiable by adding an empty line",
        ),
        (
            "present",
            {"Carrier": "car111"},
            True,
            "a real value is present. The positive row without which every negative above would be "
            "vacuous",
        ),
        (
            "present",
            {"Carrier": "zzzzzz"},
            True,
            "A DANGLING id6 IS STILL PRESENT, and this row exists to state the layering: this pure "
            "module never touches the filesystem, so `present` means DECLARED and not RESOLVABLE. The "
            "refusal of a dangling carrier belongs to `check_engine` and is a row in "
            "`CarrierVerdictTests`; asserting it here would import repo-awareness into a pure helper",
        ),
        (
            "present",
            {"Other": "z"},
            False,
            "an unrelated field is not a carrier declaration. Keeps `present` from degenerating into "
            "`this dict is non-empty`, which would make any subfield satisfy the gate",
        ),
        (
            "regex",
            "  - Carrier: car111",
            ("Carrier", "car111"),
            "THE CANONICAL SHAPE: an INDENTED `- Key: value` under a deferred bullet, which is the same "
            "grammar an E/V leaf already uses, so no new syntax was introduced for this feature",
        ),
        (
            "regex",
            "  - Carrier-Evidence: .aw/records/x.md",
            ("Carrier-Evidence", ".aw/records/x.md"),
            "a PATH value survives intact, including its dots and slashes. Asserted because the value "
            "is later handed to a path resolver, so any mangling here would turn a valid citation into "
            "an unresolvable one",
        ),
        (
            "regex",
            "  - Carrier-Declined: why",
            ("Carrier-Declined", "why"),
            "the third field matches, and its value is free prose. All three are rows because the "
            "pattern names them as LITERAL ALTERNATIVES, so one could be dropped from the alternation "
            "while the other two kept working",
        ),
        (
            "regex",
            "  - Reason: tracked somewhere",
            None,
            "AN ARBITRARY INDENTED BULLET IS NOT A CARRIER DECLARATION, even one whose prose claims "
            "tracking. This is the spoofability refusal at the pattern level: the alternation is closed "
            "to the three names, so a plausible-sounding subfield cannot satisfy the gate",
        ),
        (
            "regex",
            "- Carrier: car111",
            None,
            "A TOP-LEVEL BULLET IS A ROW, NOT A SUBFIELD, and the distinction is structural: the "
            "section walker treats an unindented `- ` as a NEW obligation. If this matched, a bare "
            "`- Carrier: x` line would be read as a subfield of the row above it, silently discharging "
            "an obligation the author never meant to carry",
        ),
        (
            "regex",
            "    - Carrier: car111",
            ("Carrier", "car111"),
            "DEEPER indentation still matches (the pattern requires only leading whitespace), so an "
            "author using four spaces rather than two is not silently ignored. Indentation depth "
            "conventions vary across this corpus, and a field that must be indented EXACTLY two spaces "
            "would fail authors invisibly",
        ),
    )

    def test_each_helper_answers_its_input(self):
        wrong = []
        for which, value, expected, why in self.HELPERS:
            if which == "parse":
                got = S.parse_carrier_ids(value)
                label = f"parse_carrier_ids({value!r})"
            elif which == "present":
                got = S.carrier_fields_present(dict(value))
                label = f"carrier_fields_present({value!r})"
            else:
                m = S.DEFERRED_SUBFIELD_RE.match(value)
                got = (
                    None
                    if m is None
                    else (m.group("field").strip(), m.group("value").strip())
                )
                label = f"DEFERRED_SUBFIELD_RE.match({value!r})"
            if got != expected:
                wrong.append(
                    f"  {label}:\n"
                    f"    - expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.HELPERS)} pure-helper inputs answered wrongly. These three "
            "helpers jointly answer WHAT THE ROW DECLARES and deliberately never ask whether it "
            "resolves, so a row expecting True/a match for something unresolvable is CORRECT: "
            "resolution is `check_engine`'s job and is asserted in CarrierVerdictTests. If several "
            "`regex` rows moved together the alternation or the leading-whitespace requirement "
            "changed; if the two boundary `regex` rows (the top-level bullet and the deeper "
            "indentation) inverted, the pattern's anchoring flipped and the section walker will start "
            "attaching subfields to the wrong rows. FIX: a helper that stops SEEING a declaration "
            "makes a correctly-carried obligation report as uncarried, which is a false alarm an "
            f"author cannot silence.\n" + "\n".join(wrong),
        )


class SchemaIsBehaviorNeutralTests(_RepoCase):
    """V-01: E-01 alone changes no lint result; E-02 is what gives the vocabulary meaning."""

    def test_adding_the_vocabulary_changes_no_existing_lint_result(self):
        # A plan carrying NO carrier field at all lints exactly as it would have: the pure text lint
        # never consults the vocabulary, because presence is only read by the repo-aware predicate.
        plan = _plan(
            self.repo, deferred_rows="- a bare prose row with no typed field.\n"
        )
        text = plan.read_text(encoding="utf-8")
        for checkpoint in (
            "author",
            "review-finalize",
            "pre-execution",
            "pre-transition",
        ):
            res = ipd_lint.lint_text(text, checkpoint=checkpoint, directory="pending")
            self.assertEqual(
                [d.code for d in res.diagnostics if d.code == RULE],
                [],
                "lint_text must never report the repo-aware rule at {0}".format(
                    checkpoint
                ),
            )


# --------------------------------------------------------------------------------------
# V-02: three escapes, four refusals, the malformed case, and the mirrored verdict shape
# --------------------------------------------------------------------------------------


class CarrierVerdictTests(_RepoCase):
    """`evaluate_carrier_obligation`: one obligation's typed fields in, one `CloseVerdict` out.

    ONE table replaces FIFTEEN tests across four classes (`ThreeEscapesTests`, `FourRefusalsTests`,
    `MalformedIsAFindingTests`' first two, and `VerdictShapeIsMirroredTests.test_the_paths_are_the_proven_escape_names`).
    Every one of them built one obligation, optionally created one fixture artifact, called this one
    function, and asserted some subset of the SAME four properties of the returned verdict. The class
    boundaries tracked the VERDICT DIRECTION (escapes versus refusals), which is the axis that
    guarantees a permissive regression is reported in one class and explained in neither.

    EVERY ROW ASSERTS THE WHOLE VERDICT, which is why this merge loses nothing and gains a lot. The old
    tests were uneven: `test_handoff_to_an_open_backlog_item_is_accepted` checked `legitimate`, `path`
    AND `severity`, while `test_handoff_to_a_nonterminal_plan_is_accepted` checked only the first two,
    and `test_a_parked_backlog_item_is_refused` checked only `legitimate` with no reason at all. Now
    every row pins `legitimate`, `severity`, `path`, a reason NEEDLE, and the fixes tuple, so the
    weaker old tests became as strong as the strongest one rather than the table settling for their
    lowest common denominator.

    THE FIXTURE IS A COLUMN, which is what makes the refusals meaningful. The same `- Carrier: X` value
    is LEGITIMATE or REFUSED depending only on what X resolves to, so rows differ by which artifact
    exists and in which lane or status. That relation is the entire rule and no single-fixture test can
    state it: the `open` backlog row and the `done` backlog row are IDENTICAL inputs to this function
    apart from the status of a file elsewhere in the tree.

    THE THREE ESCAPES SHARE THE TABLE WITH THE REFUSALS, necessarily. This is a GATE, so both
    degenerate versions are catastrophic and each is invisible to one half of the table: a predicate
    that accepted everything satisfies the three escape rows while removing the gate entirely, and one
    that refused everything satisfies the refusals while making every plan unable to transition. The
    failure message reports the two counts separately so the direction is immediate.
    """

    #: Fixture recipes, applied to the isolated repo before the row runs. Kept as names rather than
    #: lambdas in the rows so the table reads as data.
    def _apply_fixture(self, fixture):
        if fixture is None:
            return
        kind, arg = fixture
        if kind == "backlog":
            _backlog_item(self.repo, id6=arg[0], status=arg[1])
        elif kind == "plan":
            _carrier_plan(self.repo, id6=arg[0], lane=arg[1])
        elif kind == "spec":
            _spec(self.repo, id6=arg)
        elif kind == "evidence":
            _spec(self.repo, id6=arg)
        else:  # pragma: no cover - a typo in the table itself
            raise AssertionError("unknown fixture kind {0!r}".format(kind))

    #: (case, the obligation's typed fields, the fixture to create first or None, expected
    #: `legitimate`, expected `severity`, expected `path`, a substring the reason must contain (or
    #: None), why this row exists)
    VERDICTS = (
        # ---- THE THREE ESCAPES ----
        (
            "Carrier naming an OPEN backlog item",
            {"Carrier": "car111"},
            ("backlog", ("car111", "open")),
            True,
            "ok",
            "HANDOFF",
            "handed off to carrier car111",
            "THE PRIMARY ESCAPE: an open backlog item is revisited by every attention view, so handing "
            "an obligation to one genuinely preserves it. If this row breaks, no plan can ever "
            "transition and every refusal row below is satisfied for the wrong reason",
        ),
        (
            "Carrier naming a GRADUATED backlog item",
            {"Carrier": "car222"},
            ("backlog", ("car222", "graduated")),
            True,
            "ok",
            "HANDOFF",
            "handed off to carrier car222",
            "`graduated` maps to the ACTIVE attention class, so it is still revisited and is therefore "
            "a legitimate carrier. This row is the boundary of the terminal-status set: `graduated` "
            "means the design was handed to a plan, NOT that the work is done, so excluding it would "
            "refuse a correct handoff at exactly the moment the work is most alive",
        ),
        (
            "Carrier naming a BLOCKED backlog item",
            {"Carrier": "carblk"},
            ("backlog", ("carblk", "blocked")),
            True,
            "ok",
            "HANDOFF",
            "handed off to carrier carblk",
            "a BLOCKED item is still LIVE: it surfaces in the attention view as blocked, waiting on a "
            "gate. Accepting it is correct and slightly counterintuitive, which is why it is a row - "
            "someone tightening the terminal set would plausibly add `blocked` to it and thereby "
            "refuse a handoff to an item that is being actively tracked",
        ),
        (
            "Carrier naming a PENDING plan",
            {"Carrier": "carpln"},
            ("plan", ("carpln", "pending")),
            True,
            "ok",
            "HANDOFF",
            "handed off to carrier carpln",
            "the OTHER accepted carrier TYPE. The maintainer's ruling names exactly two (a backlog item "
            "or a non-terminal plan), so both types need a row or the rule could silently narrow to "
            "one and every plan-to-plan handoff would start failing",
        ),
        (
            "Carrier-Evidence resolving to a real in-tree artifact",
            {
                "Carrier-Evidence": ".aw/records/specs/20260901-aaaaaa-01-aaaaaa-x.spec.md"
            },
            ("evidence", "aaaaaa"),
            True,
            "ok",
            "SATISFIED",
            "satisfied by resolvable evidence",
            "THE SECOND ESCAPE: a citation that the defect is ALREADY addressed, resolved by the same "
            "shared resolver `aw backlog set done --evidence` uses. Note the target here is a SPEC and "
            "it works: a spec is never a sufficient CARRIER, but it is perfectly good EVIDENCE, and "
            "that asymmetry is deliberate rather than an inconsistency",
        ),
        (
            "Carrier-Declined with a reason",
            {"Carrier-Declined": "this is a scope note, not a defect"},
            None,
            True,
            "ok",
            "DECLINED",
            "explicitly declined with a reason",
            "THE THIRD ESCAPE, and the only one needing no repository access: an author may state that "
            "a row is not a defect at all. The reason's MERIT is a reviewer's job, exactly as "
            "`open_question_error` says of an OQ rationale, so the predicate requires only that a "
            "reason exists - a semantic judgement here would be a claim this module cannot make",
        ),
        (
            "Carrier-Declined WINNING over a dangling Carrier",
            {"Carrier-Declined": "not a defect", "Carrier": "zzzzzz"},
            None,
            True,
            "ok",
            "DECLINED",
            "explicitly declined with a reason",
            "PRECEDENCE, which no old test covered: DECLINED is checked FIRST, so it wins even beside a "
            "`Carrier` that resolves to nothing. That ordering is what `CARRIER_FIELDS`' tuple order "
            "documents, and it is worth pinning because the opposite order would make an explicit "
            "decline unreachable whenever a stale carrier line sat beside it",
        ),
        # ---- THE REFUSALS ----
        (
            "NO carrier field at all",
            {},
            None,
            False,
            "error",
            None,
            "NO durable carrier",
            "THE HEADLINE REFUSAL and the reason the rule exists: a row recording an obligation with "
            "nothing to carry it onward. The reason text names the consequence (`once this plan reaches "
            "executed it classes done in aw attention and this vanishes`), which is what makes the "
            "finding self-explanatory to an author who has never read this plan",
        ),
        (
            "Carrier-Declined with an EMPTY reason",
            {"Carrier-Declined": "   "},
            None,
            False,
            "error",
            None,
            "NO durable carrier",
            "AN EMPTY DECLINE DECLINES NOTHING, and note it falls through to the no-carrier refusal "
            "rather than producing a decline-specific complaint. That is the important half: the field "
            "being PRESENT is not a declaration, so the gate cannot be satisfied by typing the field "
            "name and leaving it blank",
        ),
        (
            "Carrier naming a DANGLING id6",
            {"Carrier": "zzzzzz"},
            None,
            False,
            "error",
            None,
            "resolves to no backlog item or plan",
            "THE REFERENCE MUST RESOLVE, exactly as `check.from-backlog-dangling` fails a "
            "`From-Backlog` pointing at nothing. A well-formed id6 that names no record is the shape a "
            "typo takes, and it would otherwise satisfy the gate while carrying nothing",
        ),
        (
            "Carrier naming an EXECUTED plan",
            {"Carrier": "carexe"},
            ("plan", ("carexe", "executed")),
            False,
            "error",
            None,
            "terminal/hidden",
            "THE LOAD-BEARING REFUSAL. An executed plan classes `done` in `aw attention`, so handing an "
            "obligation to one hides it in THE VERY PLACE this rule exists to close. Without this row "
            "the whole feature is circumventable by pointing at any finished plan, and the fix would "
            "look like a valid handoff to a reviewer",
        ),
        (
            "Carrier naming a DONE backlog item",
            {"Carrier": "cardon"},
            ("backlog", ("cardon", "done")),
            False,
            "error",
            None,
            "terminal/hidden",
            "the backlog's terminal status, refused for the identical reason. Both trees need a row "
            "because the terminal set spans both vocabularies, so one could be dropped while the other "
            "held and the leak would exist in only one tree",
        ),
        (
            "Carrier naming a PARKED backlog item",
            {"Carrier": "carprk"},
            ("backlog", ("carprk", "parked")),
            False,
            "error",
            None,
            "terminal/hidden",
            "`parked` is not terminal in the ordinary sense, yet it is REFUSED because "
            "`attention_contract` maps it to the `parked` class which the default board HIDES. The test "
            "is VISIBILITY, not doneness, and that is the subtlest judgement in the terminal set: a "
            "parked carrier is invisible by construction exactly as an executed plan is. The old test "
            "for this asserted only `legitimate` with no reason; this row pins the needle too",
        ),
        (
            "Carrier naming a SPEC",
            {"Carrier": "carspc"},
            ("spec", "carspc"),
            False,
            "error",
            None,
            "resolves to no backlog item or plan",
            "A SPEC IS NEVER A SUFFICIENT CARRIER (OQ-01, ruled by the maintainer: it is supporting "
            "material). Note the reason is the DANGLING one, because `specs` is simply absent from the "
            "accepted target types rather than being special-cased - which also means this row is what "
            "would catch someone adding `specs` to that tuple. Contrast the Carrier-Evidence row above, "
            "where a spec IS acceptable",
        ),
        (
            "Carrier-Evidence naming a path that does not exist",
            {"Carrier-Evidence": ".aw/records/nope.md"},
            None,
            False,
            "error",
            None,
            "does not resolve",
            "EVIDENCE MUST RESOLVE TOO. The second escape is no weaker than the first: a citation to a "
            "file that is not there proves nothing, and its distinct message (`does not resolve` rather "
            "than the carrier wording) is what tells an author which field to fix",
        ),
        (
            "Carrier holding PROSE instead of an id6",
            {"Carrier": "see the backlog"},
            None,
            False,
            "error",
            None,
            "malformed",
            "A MALFORMED REFERENCE IS A FINDING, NOT AN EXCEPTION, which is the property that keeps "
            "this gate enabled: a gate that crashes on bad input is a gate someone disables. The "
            "message says `malformed` rather than `dangling`, so an author is told the value is "
            "unparseable rather than sent hunting for a missing record",
        ),
        (
            "a GOOD token beside a BAD one",
            {"Carrier": "car111, NOT-AN-ID6"},
            ("backlog", ("car111", "open")),
            False,
            "error",
            None,
            "NOT-AN-ID6",
            "THE MALFORMED TOKEN IS NAMED even though a perfectly valid carrier sits beside it, and the "
            "whole row is REFUSED rather than accepted on the strength of the good token. Both halves "
            "matter: accepting it would let a typo'd second carrier be silently ignored, and reporting "
            "without naming the bad token would leave the author guessing which of two values is wrong",
        ),
    )

    def test_each_obligation_gets_its_full_verdict(self):
        wrong = []
        escapes_broken = 0
        refusals_broken = 0
        for (
            case,
            fields,
            fixture,
            want_legit,
            want_severity,
            want_path,
            needle,
            why,
        ) in self.VERDICTS:
            repo = _mkrepo()
            saved = self.repo
            self.repo = repo
            try:
                self._apply_fixture(fixture)
                v = ce.evaluate_carrier_obligation(repo, _obligation(**fields))
            finally:
                self.repo = saved
                shutil.rmtree(repo, ignore_errors=True)
            problems = []
            if v.legitimate != want_legit:
                if want_legit:
                    escapes_broken += 1
                    problems.append(
                        "expected this ESCAPE to be accepted (legitimate=True) and it was REFUSED; a "
                        "plan using this escape can no longer transition"
                    )
                else:
                    refusals_broken += 1
                    problems.append(
                        "expected this to be REFUSED (legitimate=False) and it was ACCEPTED; the gate "
                        "now passes an obligation nothing durable carries"
                    )
            if v.severity != want_severity:
                problems.append(
                    f"expected severity {want_severity!r}, got {v.severity!r}"
                )
            if v.path != want_path:
                problems.append(f"expected path {want_path!r}, got {v.path!r}")
            if needle is not None and needle not in v.reason:
                problems.append(
                    f"the reason must mention {needle!r}; it was {v.reason!r}"
                )
            # A refusal must always carry the three actionable fixes; an escape carries none.
            if want_legit and v.fixes:
                problems.append(
                    f"an accepted verdict must carry NO fixes (nothing needs fixing), got {v.fixes!r}"
                )
            if not want_legit:
                if len(v.fixes) != 3:
                    problems.append(
                        f"a refusal must offer all THREE escapes as fixes, got {len(v.fixes)}: "
                        f"{v.fixes!r}"
                    )
                else:
                    joined = " ".join(v.fixes)
                    absent = [f for f in S.CARRIER_FIELDS if f not in joined]
                    if absent:
                        problems.append(
                            f"the fixes do not name {absent!r}; an author told only some of their "
                            "options will reach for the one that is offered rather than the one that "
                            "fits"
                        )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        direction = ""
        if refusals_broken and not escapes_broken:
            direction = (
                f" ALL {refusals_broken} verdict failures are REFUSALS THAT NOW PASS, which is the "
                "dangerous direction: the gate has gone permissive and obligations can reach `executed` "
                "uncarried, which is exactly the silent-drop this rule exists to stop. Every escape row "
                "is passing for the wrong reason while that is true."
            )
        elif escapes_broken and not refusals_broken:
            direction = (
                f" ALL {escapes_broken} verdict failures are ESCAPES THAT ARE NOW REFUSED, so the gate "
                "has gone strict: authors have no way to satisfy it and no plan can transition. Loud "
                "and recoverable, unlike the permissive direction, but it will block every lane."
            )
        self.assertEqual(
            wrong,
            [],
            f"evaluate_carrier_obligation mishandled {len(wrong)} of {len(self.VERDICTS)} "
            f"obligations.{direction} The fixture is a COLUMN here, so note that the `open`, "
            "`graduated`, `blocked`, `done` and `parked` backlog rows are the SAME input to this "
            "function differing only in a file's status elsewhere in the tree: if those moved together "
            "the `_CARRIER_TERMINAL_STATUSES` set changed membership rather than the predicate "
            "breaking, and the rows to check first are `graduated`/`blocked` (must stay ACCEPTED, they "
            "are live) against `parked` (must stay REFUSED, the board hides it). If the SPEC row "
            "flipped to accepted, `specs` was added to `_CARRIER_TARGET_TYPES`, which is a maintainer "
            "decision and not a tweak. FIX: the reason needles are asserted because the three refusal "
            "messages (`NO durable carrier` / `resolves to no backlog item or plan` / `terminal/hidden` "
            "/ `malformed`) are what tell an author WHICH repair to make, and a correct verdict with "
            f"the wrong reason sends them to the wrong fix.\n" + "\n".join(wrong),
        )

    def test_the_verdict_type_is_the_mirrored_CloseVerdict(self):
        """Kept separate: a claim about the TYPE, not about any obligation's outcome.

        E-02's design constraint was to MIRROR `evaluate_blocking_close`'s verdict rather than invent a
        fourth verdict type, so the assertion is `isinstance` plus the exact field tuple. No row can
        state that: every row consumes the fields, which presupposes the shape.
        """
        v = ce.evaluate_carrier_obligation(self.repo, _obligation())
        self.assertIsInstance(v, ce.CloseVerdict)
        self.assertEqual(
            v._fields,
            ("legitimate", "severity", "reason", "fixes", "path"),
            "the verdict shape is SHARED with evaluate_blocking_close; a fourth verdict type (or a "
            "renamed field) forks the two gates that deliberately mirror each other.",
        )

    def test_an_unparseable_plan_yields_no_traceback(self):
        """Kept separate: MATERIALLY DIFFERENT SETUP - a deliberately corrupt file, not an obligation.

        The input is NUL bytes rather than a plan, and the claim is about the whole plan-level evaluator
        surviving it. Every row in the table above feeds a well-formed `CarrierObligation` to the
        per-row predicate, so this shares neither the subject nor the input shape.
        """
        p = self.repo / ".aw" / "records" / "plans" / "pending" / "junk.ipd.md"
        p.write_text("\x00 not markdown at all \x00", encoding="utf-8")
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=p, plan_text=p.read_text(encoding="utf-8")
        )
        self.assertEqual(
            _rules(drift),
            [],
            "an unparseable plan must yield NO findings and NO traceback; the structural linter owns "
            "that complaint, and a crash here would take down every `aw check` run.",
        )

    def test_the_predicate_never_raises_on_an_absent_repo(self):
        """Kept separate: MATERIALLY DIFFERENT SETUP - a repository root that does not exist.

        Every table row runs against a real isolated repo, which is what makes the fixture column
        meaningful. This asserts the failure mode when there is no tree at all to resolve against, so
        it cannot share the table's setup by construction.
        """
        v = ce.evaluate_carrier_obligation(
            Path("/nonexistent/repo/root"), _obligation(Carrier="car111")
        )
        self.assertFalse(
            v.legitimate,
            "with no tree to resolve against, the verdict must FAIL CLOSED rather than raise or "
            "optimistically accept: an unresolvable carrier is not a handoff.",
        )


# --------------------------------------------------------------------------------------
# V-02/V-03/V-04/V-05: the plan-level round trip - one plan, every surface, both tiers
# --------------------------------------------------------------------------------------


class PlanLevelRoundTripTests(unittest.TestCase):
    """ONE plan fixture per row, asserted through EVERY surface at once: the full round trip.

    ONE table replaces FOURTEEN tests across six classes (`QuestionObligationsTests`,
    `ProseDoesNotSatisfyTests`, the fixture-driven half of `LintCheckpointTests`,
    `CrossSurfaceAgreementTests`' two fixture tests, `StagedSeverityTests`' three fixture tests, and
    `AggregationTests`). Every one built a plan with `_plan(...)`, changed one of its deferred rows /
    open question / date / lane, and then asserted ONE surface's answer about it. The class boundaries
    tracked WHICH SURFACE was being asked, which is precisely the thing that should not be split,
    because the design property under test is that the surfaces AGREE.

    THE MERGE IS STRICTLY STRONGER THAN WHAT IT REPLACES, and this is the reason it was done at all.
    Durability means the obligation survives, so a half-assertion is worthless here: an old test that
    checked only the evaluator could not tell whether the `aw check` sweep saw the same thing, and the
    two `CrossSurfaceAgreementTests` tests that DID compare surfaces existed for only two fixtures.
    Now EVERY row asserts the full trip on the same plan:
      * `evaluate_durable_carrier` - the finding count, its severity, and the ENRICHED TRIPLE
        (`observed` / `required` / `recovery`) that makes the finding self-explanatory to an author
        who has never read the plan that introduced the rule,
      * `artifact_core.drift_exit_code` - whether that severity FAILS a gate or merely reports,
      * `check_durable_carrier` - the `aw check` sweep, including its grandfathering of terminal lanes,
      * `check_types(repo, ["plans"])` and `["all"]` - that the rule is REACHED by the type dispatch
        and reported EXACTLY ONCE rather than double-counted,
      * `ipd_lint.lint_file(..., "pre-transition")` - whether it BLOCKS (a diagnostic) or merely
        ADVISES (an advisory), plus the resulting disposition,
      * and the IDENTITY of the sweep's detail with the lint message, which is what proves one
        predicate backs both.
    No old test asserted more than three of those; none asserted the identity except for two fixtures.

    THE MODE DISTINCTIONS ARE COLUMNS, and each is a relation no single-mode test can state:
      * DATE selects the staged-severity tier, so the SAME plan is a blocking `error` after the cutover
        and a non-failing `info` advisory before it. The pair of rows differing only in the date is the
        only way to state that the tier is read from the plan's own `- Date:`.
      * LANE selects grandfathering, so the SAME uncarried plan is swept in `pending/` and exempt in
        every terminal directory.
      * The OBLIGATION KIND (a deferred row versus an open question versus a deferred question) is a
        column because both sources feed one obligation list, and a regression in either walker would
        otherwise look like an unrelated failure.

    CARRIED (clean) ROWS SHARE THE TABLE WITH UNCARRIED ONES. A rule that reported every plan would
    satisfy every uncarried row while making the gate unsatisfiable, and one that reported none would
    satisfy the clean rows while the feature silently did nothing. Both are live risks for a gate whose
    normal state is `no findings`, so the failure message names which direction failed.
    """

    #: How many findings a plan-level evaluation may produce: ALWAYS at most one, per DECISION
    #: 07-rnkqrc-D4, because 664 offending rows live in 106 pending plans and a per-row Drift would add
    #: 664 lines to every clean `aw check plans`.
    #:
    #: (case, `_plan` kwargs, a fixture recipe or None, expected finding count, expected severity or
    #: None, expected process exit code, does the pre-transition lint BLOCK (diagnostic) or ADVISE
    #: (advisory) or neither, is the plan in a lane the sweep grandfathers, detail substrings, why)
    PLANS = (
        (
            "an uncarried deferred row, POST-cutover",
            dict(
                date=_POST_DATE,
                deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
            ),
            None,
            1,
            "error",
            1,
            "block",
            False,
            ("1 obligation(s)", "NO durable carrier"),
            "THE CENTRAL ROW: after the cutover an uncarried obligation is a FAIL-CLOSED error that "
            "blocks the pre-transition gate, which is the moment the plan would otherwise become "
            "`executed` and the obligation would leave every attention view",
        ),
        (
            "THE SAME uncarried row, PRE-cutover",
            dict(
                date=_PRE_DATE,
                deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
            ),
            None,
            1,
            ce._CARRIER_LEGACY_SEVERITY,
            0,
            "advise",
            False,
            ("1 obligation(s)", "NO durable carrier"),
            "THE STAGED-SEVERITY PAIR, and the reason DATE is a column: an identical plan is still "
            "REPORTED but at the `info` tier, which `drift_exit_code` exempts, so it does NOT fail the "
            "gate and does NOT block the transition - it appears as an ADVISORY instead. This is the "
            "rollout guarantee for the plans that predate the rule, and `info` is measured rather than "
            "stylistic: a `warning` here would exit 1 on a clean tree and train everyone to bypass "
            "`aw check`",
        ),
        (
            "a deferred row WITH a resolvable Carrier",
            dict(date=_POST_DATE, deferred_rows="- HANDED OFF.\n  - Carrier: car111\n"),
            ("backlog", ("car111", "open")),
            0,
            None,
            0,
            "silent",
            False,
            (),
            "THE PRIMARY CLEAN ROW: the gate must be SATISFIABLE. Every uncarried row above and below "
            "is vacuous while this is broken, because a rule that flagged every plan would satisfy all "
            "of them and no author could ever pass",
        ),
        (
            "a plan with NO obligations at all",
            dict(date=_POST_DATE, deferred_rows=""),
            None,
            0,
            None,
            0,
            "silent",
            False,
            (),
            "THE SECOND CLEAN ROW: an EMPTY deferred section produces nothing, rather than the section's "
            "mere presence (it is MANDATORY in both H2 orders) counting as an obligation. Without this "
            "row the rule could fire on every conforming plan in the repository",
        ),
        (
            "PROSE claiming backlog tracking, naming a REAL id6",
            dict(
                date=_POST_DATE,
                deferred_rows="- THE WALKTHROUGH GAP: tracked in the backlog as `car111`.\n",
            ),
            ("backlog", ("car111", "open")),
            1,
            "error",
            1,
            "block",
            False,
            ("1 obligation(s)",),
            "THE SPOOFABILITY REFUSAL, and the fixture column is what makes it bite: the backlog item "
            "car111 REALLY EXISTS and is open, and the prose names it correctly, and it is STILL "
            "refused because only a TYPED field may satisfy the gate. Measured 2026-09-18: all 2225 "
            "deferred rows in the corpus are prose, several literally saying 'tracked as <id6>', so a "
            "prose matcher would accept every one of them and verify nothing",
        ),
        (
            "the SAME row with the id6 in a TYPED field",
            dict(
                date=_POST_DATE,
                deferred_rows="- THE WALKTHROUGH GAP: tracked in the backlog.\n  - Carrier: car111\n",
            ),
            ("backlog", ("car111", "open")),
            0,
            None,
            0,
            "silent",
            False,
            (),
            "THE POSITIVE HALF of the spoofability pair: the same claim, the same target, one typed "
            "field, and it passes. The two rows together are what prove the rule is about the FIELD and "
            "not about the row's content, which is the distinction an author needs to understand",
        ),
        (
            "a Carrier inside a CODE FENCE",
            dict(
                date=_POST_DATE,
                deferred_rows="- THE GAP: see the example below.\n\n```\n  - Carrier: car111\n```\n",
            ),
            ("backlog", ("car111", "open")),
            1,
            "error",
            1,
            "block",
            False,
            ("1 obligation(s)",),
            "THE SECTION WALK IS FENCE-AWARE, so a documented EXAMPLE cannot satisfy the gate. This "
            "matters specifically because the documentation of this very feature contains exactly such "
            "an example: if fenced content counted, every plan that EXPLAINS the carrier convention "
            "would silently discharge its own obligations",
        ),
        (
            "an OPEN question with no carrier",
            dict(date=_POST_DATE, open_questions=_oq(status="open")),
            None,
            1,
            "error",
            1,
            "block",
            False,
            ("OQ-01", "1 obligation(s)"),
            "THE OTHER OBLIGATION SOURCE: questions, not only deferred rows. The locator is the "
            "QUESTION'S OWN ID (`OQ-01`) rather than a row number, which is asserted because that is "
            "what an author greps for. Both sources feed one obligation list, so this row is what keeps "
            "the question walker from silently returning nothing",
        ),
        (
            "a DEFERRED question with no carrier",
            dict(date=_POST_DATE, open_questions=_oq(status="deferred")),
            None,
            1,
            "error",
            1,
            "block",
            False,
            ("OQ-01",),
            "`deferred` leaves something OUTSTANDING just as `open` does, so it owes a carrier too. "
            "Deferral is the likelier real case: an author who defers a question has consciously "
            "decided to proceed without the answer, which is exactly when the question needs a durable "
            "home or it is simply abandoned",
        ),
        (
            "a RESOLVED question",
            dict(date=_POST_DATE, open_questions=_oq(status="resolved")),
            None,
            0,
            None,
            0,
            "silent",
            False,
            (),
            "THE THIRD CLEAN ROW and the boundary of the live-status set: a RESOLVED question has been "
            "answered and owes nothing. Measured 2026-09-18, demanding a carrier here would fire on 464 "
            "executed-tree and 154 pending-tree questions that owe nothing at all",
        ),
        (
            "an OPEN question naming a carrier",
            dict(
                date=_POST_DATE,
                open_questions=_oq(status="open", extra="- Carrier: car111"),
            ),
            ("backlog", ("car111", "open")),
            0,
            None,
            0,
            "silent",
            False,
            (),
            "the question path's CLEAN row: the same typed field works under an OQ block as under a "
            "deferred row, which is what makes the vocabulary one vocabulary rather than two",
        ),
        (
            "SEVEN uncarried rows in one plan",
            dict(
                date=_POST_DATE,
                deferred_rows="".join(
                    "- UNCARRIED DEFECT {0}: nothing tracks this.\n".format(i)
                    for i in range(1, 8)
                ),
            ),
            None,
            1,
            "error",
            1,
            "block",
            False,
            ("7 obligation(s)", "and 2 more"),
            "AGGREGATION (DECISION 07-rnkqrc-D4): seven failing rows yield ONE finding that names the "
            "TOTAL (`7 obligation(s)`) and enumerates the first five plus `and 2 more`. The count is "
            "measured, not aesthetic: 664 offending rows live in 106 pending plans, so a per-row Drift "
            "would add 664 lines to every clean `aw check plans` run and the output would be ignored",
        ),
        (
            "an uncarried plan in the EXECUTED lane",
            dict(
                lane="executed",
                status="executed",
                date=_POST_DATE,
                deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
            ),
            None,
            1,
            "error",
            1,
            "silent",
            True,
            ("1 obligation(s)",),
            "THE LANE COLUMN'S REASON, and the subtlest row here: the evaluator called DIRECTLY still "
            "reports (it answers about whatever plan it is handed), but the SWEEP skips the terminal "
            "lanes entirely and the pre-transition lint returns the LEGACY disposition rather than "
            "blocking. That is deliberate: a terminal plan is already past the transition this rule "
            "gates, and retroactively litigating 527 executed plans would be a whole-tree "
            "false-positive explosion",
        ),
        (
            "an uncarried plan in the SUPERSEDED lane",
            dict(
                lane="superseded",
                status="executed",
                date=_POST_DATE,
                deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
            ),
            None,
            1,
            "error",
            1,
            "silent",
            True,
            ("1 obligation(s)",),
            "the second terminal lane. All three are rows because the sweep's skip is a membership test "
            "against the lane name, so one lane could be dropped from it while the others held and only "
            "that tree would start being litigated",
        ),
        (
            "an uncarried plan in the NOT-EXECUTED lane",
            dict(
                lane="not-executed",
                status="executed",
                date=_POST_DATE,
                deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
            ),
            None,
            1,
            "error",
            1,
            "silent",
            True,
            ("1 obligation(s)",),
            "the third terminal lane, completing the set the sweep must grandfather",
        ),
    )

    @staticmethod
    def _apply(repo, fixture):
        if fixture is None:
            return
        kind, arg = fixture
        if kind == "backlog":
            _backlog_item(repo, id6=arg[0], status=arg[1])
        elif kind == "plan":
            _carrier_plan(repo, id6=arg[0], lane=arg[1])
        elif kind == "spec":
            _spec(repo, id6=arg)
        else:  # pragma: no cover - a typo in the table itself
            raise AssertionError("unknown fixture kind {0!r}".format(kind))

    def test_every_plan_survives_the_full_round_trip_on_every_surface(self):
        wrong = []
        clean_rows_broken = 0
        uncarried_rows_broken = 0
        for (
            case,
            plan_kwargs,
            fixture,
            want_count,
            want_severity,
            want_exit,
            want_lint,
            grandfathered,
            needles,
            why,
        ) in self.PLANS:
            repo = _mkrepo()
            try:
                self._apply(repo, fixture)
                plan = _plan(repo, **plan_kwargs)
                text = plan.read_text(encoding="utf-8")

                drift = ce.evaluate_durable_carrier(
                    repo, plan_path=plan, plan_text=text
                )
                sweep = [
                    d for d in ce.check_durable_carrier(repo) if d.location == str(plan)
                ]
                typed = [d for d in ce.check_types(repo, ["plans"]) if d.rule == RULE]
                everything = [
                    d for d in ce.check_types(repo, ["all"]) if d.rule == RULE
                ]
                res = ipd_lint.lint_file(plan, checkpoint="pre-transition")
                blocking = [d for d in res.diagnostics if d.code == RULE]
                advising = [d for d in res.advisories if d.code == RULE]
                exit_code = core.drift_exit_code(drift)
                disposition = res.disposition
            finally:
                shutil.rmtree(repo, ignore_errors=True)

            problems = []
            if len(drift) != want_count:
                if want_count == 0:
                    clean_rows_broken += 1
                    problems.append(
                        f"evaluate_durable_carrier must produce NO finding and produced {len(drift)}: "
                        f"{[d.detail for d in drift]!r}"
                    )
                else:
                    uncarried_rows_broken += 1
                    problems.append(
                        f"evaluate_durable_carrier must produce EXACTLY {want_count} finding(s) and "
                        f"produced {len(drift)}; at most one per plan is the aggregation contract"
                    )
            if drift:
                if drift[0].severity != want_severity:
                    problems.append(
                        f"severity must be {want_severity!r} and is {drift[0].severity!r}; the tier is "
                        "read from the plan's own `- Date:` against the cutover"
                    )
                absent = [n for n in needles if n not in drift[0].detail]
                if absent:
                    problems.append(
                        f"the detail must mention {absent!r}; it was {drift[0].detail!r}"
                    )
                # EVERY finding, at EITHER tier, must carry the enriched triple. This is what makes
                # the finding self-explanatory to an author who has never read the plan that
                # introduced the rule: what was OBSERVED, what is REQUIRED, and how to RECOVER.
                enrichment = (
                    ("observed", drift[0].observed, "Carrier"),
                    ("required", drift[0].required, "NON-TERMINAL plan"),
                    ("recovery", drift[0].recovery, "aw backlog new"),
                )
                for field, value, needle in enrichment:
                    if not value:
                        problems.append(
                            f"the finding's `{field}` is empty; without it the author is told a rule "
                            "fired and not what to do about it"
                        )
                    elif needle not in value:
                        problems.append(
                            f"the finding's `{field}` does not mention {needle!r}: {value!r}"
                        )
            if exit_code != want_exit:
                problems.append(
                    f"drift_exit_code must be {want_exit} and is {exit_code}; this is what decides "
                    "whether the finding FAILS a gate or merely reports"
                )

            # The `aw check` sweep, including its terminal-lane grandfathering.
            want_sweep = 0 if grandfathered else want_count
            if len(sweep) != want_sweep:
                problems.append(
                    f"the `aw check` sweep must report {want_sweep} finding(s) for this plan and "
                    f"reported {len(sweep)}"
                    + (
                        " (a terminal-lane plan must be GRANDFATHERED by the sweep)"
                        if grandfathered
                        else ""
                    )
                )
            if len(typed) != want_sweep:
                problems.append(
                    f"check_types(['plans']) must report {want_sweep} and reported {len(typed)}, so "
                    "the rule is not reached by the plans type dispatch"
                )
            if len(everything) != want_sweep:
                problems.append(
                    f"check_types(['all']) must report {want_sweep} and reported "
                    f"{len(everything)}; more than that means the rule is DOUBLE-REPORTED by the full "
                    "sweep"
                )

            # The pre-transition lint: block, advise, or say nothing.
            if want_lint == "block":
                if not blocking:
                    problems.append(
                        "the pre-transition lint must BLOCK (report a diagnostic) and did not, so this "
                        "plan can transition to terminal with the obligation uncarried: "
                        f"{[d.render('plan') for d in res.diagnostics]!r}"
                    )
                if disposition != S.DISPOSITION_ERROR:
                    problems.append(
                        f"a blocked plan's disposition must be {S.DISPOSITION_ERROR!r}, got "
                        f"{disposition!r}"
                    )
                if res.passing:
                    problems.append("a blocked plan must not be `passing`")
            elif want_lint == "advise":
                if blocking:
                    problems.append(
                        "a GRANDFATHERED plan must NOT be blocked at pre-transition (that would strand "
                        f"every plan predating the rule), got {[d.render('plan') for d in blocking]!r}"
                    )
                if not advising:
                    problems.append(
                        "a grandfathered plan must still be VISIBLE as an ADVISORY; it is neither "
                        "blocked nor reported, so the obligation is silently invisible"
                    )
            else:
                if blocking or advising:
                    problems.append(
                        f"the pre-transition lint must say NOTHING about this plan, got "
                        f"diagnostics={[d.code for d in blocking]!r} "
                        f"advisories={[d.code for d in advising]!r}"
                    )
                if grandfathered and disposition != S.DISPOSITION_LEGACY:
                    problems.append(
                        f"a terminal-directory plan must keep the {S.DISPOSITION_LEGACY!r} "
                        f"disposition, got {disposition!r}"
                    )

            # ONE PREDICATE, TWO SURFACES: the sweep's detail and the lint's message must be IDENTICAL.
            if sweep and (blocking or advising):
                reported = (blocking or advising)[0]
                if sweep[0].detail != reported.message:
                    problems.append(
                        "the sweep and the lint DISAGREE about the same plan, so they are no longer "
                        f"backed by one predicate:\n        sweep: {sweep[0].detail!r}\n"
                        f"        lint:  {reported.message!r}"
                    )

            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        direction = ""
        if clean_rows_broken and not uncarried_rows_broken:
            direction = (
                f" {clean_rows_broken} CLEAN row(s) are among the failures, so the rule is firing on "
                "plans that carry their obligations properly: the gate is UNSATISFIABLE and every "
                "uncarried row here is passing for the wrong reason."
            )
        elif uncarried_rows_broken and not clean_rows_broken:
            direction = (
                f" {uncarried_rows_broken} UNCARRIED row(s) are among the failures, so obligations are "
                "going unreported: the gate has stopped holding and an obligation can reach `executed` "
                "and vanish from every attention view, which is the exact failure this rule exists to "
                "prevent."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.PLANS)} plan fixtures failed the round trip.{direction} EVERY "
            "ROW ASSERTS ALL SURFACES AT ONCE, so read WHICH surface failed before suspecting the "
            "predicate: if the evaluator is right and the SWEEP is wrong, the lane filter or the type "
            "dispatch changed; if the evaluator is right and the LINT is wrong, the checkpoint wiring "
            "changed; if the sweep and lint DISAGREE, the one-predicate property is gone and the two "
            "surfaces have forked, which is the failure the design exists to make impossible. IF THE "
            "TWO ROWS DIFFERING ONLY IN `date` BOTH FAILED, the staged-severity boundary moved rather "
            "than either tier breaking (check CARRIER_CUTOVER_DATE and _CARRIER_LEGACY_SEVERITY): the "
            "`info` tier is measured, because a `warning` there would exit 1 on a clean tree and train "
            "every agent to bypass `aw check`. IF THE THREE TERMINAL-LANE ROWS FAILED TOGETHER, the "
            "sweep's grandfathering changed and 527 executed plans are now being retroactively "
            f"litigated.\n" + "\n".join(wrong),
        )


class CheckpointPlacementTests(_RepoCase):
    """V-03: WHICH checkpoint the rule fires at, and the structural proofs of where it is wired.

    The CHECKPOINT is a column in one table (a plan that is uncarried at every phase, asked at each
    phase), which replaces `test_the_rule_is_silent_at_every_other_checkpoint`'s loop over two phases
    plus the two `PreExecutionGateIsUntouchedTests` fixtures. The surrounding SYMBOL assertions are
    NOT rows and say why in their own docstrings.

    Why the checkpoint table beats the loop it replaces: the old loop covered `author` and
    `review-finalize` only, so `pre-execution` was asserted by a separate test in a separate class and
    `pre-transition` by yet another. The rule's placement is a single claim about a CLOSED set of five
    phases, and the interesting content is that exactly ONE of them blocks: firing earlier would demand
    a carrier for a row the author is still drafting, and not firing at `pre-transition` would let the
    obligation vanish. Only the whole set, adjacent, states that.
    """

    #: (the checkpoint, must the rule appear as a BLOCKING diagnostic?, why this row exists)
    PHASES = (
        (
            "author",
            False,
            "SILENT while DRAFTING. An author writing a deferred row has not yet decided how to carry "
            "it, and blocking here would make the section unusable as a thinking surface - people would "
            "stop recording deferrals at all, which is worse than recording them uncarried",
        ),
        (
            "review-finalize",
            False,
            "SILENT at review too. A reviewer may legitimately be the person who decides the carrier, "
            "so demanding it before the review concludes inverts the order of work",
        ),
        (
            "pre-execution",
            False,
            "SILENT before EXECUTION, which is the least obvious of the four and is a deliberate "
            "division of labour: `pre-execution` already owns the BLOCKING-QUESTION check (asserted "
            "separately below), and the obligation has not yet vanished because the plan is not yet "
            "terminal. Blocking here would stop work starting over a row that only matters when it ends",
        ),
        (
            "pre-transition",
            True,
            "THE ONE PHASE THAT BLOCKS, and the whole design: this is the LAST moment before the plan "
            "becomes terminal and the obligation leaves every attention view. Stop gating here and the "
            "feature does nothing at all, no matter how correct the predicate is",
        ),
    )

    def test_the_rule_blocks_at_pre_transition_and_nowhere_else(self):
        wrong = []
        for checkpoint, want_block, why in self.PHASES:
            repo = _mkrepo()
            try:
                # `performed=False` + a pre-terminal status keeps the earlier phases self-consistent,
                # so a phase's answer is about THIS rule rather than about unrelated E/V state.
                pre_terminal = checkpoint in ("author", "review-finalize")
                plan = _plan(
                    repo,
                    date=_POST_DATE,
                    status="to-review" if pre_terminal else "approved",
                    performed=not pre_terminal,
                    deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
                )
                res = ipd_lint.lint_file(plan, checkpoint=checkpoint)
                got = [d.code for d in res.diagnostics if d.code == RULE]
            finally:
                shutil.rmtree(repo, ignore_errors=True)
            if bool(got) != want_block:
                if want_block:
                    detail = (
                        "must BLOCK here and did not, so an uncarried obligation can reach terminal: "
                        f"diagnostics were {[d.render('plan') for d in res.diagnostics]!r}"
                    )
                else:
                    detail = (
                        "must be SILENT here and fired; blocking at this phase demands a carrier before "
                        "the author or reviewer has had the chance to choose one"
                    )
                wrong.append(
                    f"  checkpoint {checkpoint!r}:\n"
                    f"    - {detail}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the rule fires at the wrong phase in {len(wrong)} of {len(self.PHASES)} checkpoints. "
            "Exactly ONE phase may block, and the two failure directions are opposite: a rule that "
            "stopped blocking at `pre-transition` makes the whole feature inert however correct the "
            "predicate is, while a rule that started firing EARLIER demands a carrier before an author "
            "or reviewer has chosen one and will push people to stop recording deferrals. If several "
            "silent rows fired together, the rule was added to a wider checkpoint set rather than moved "
            f"(see `ipd_lint._CARRIER_CHECKPOINTS`).\n" + "\n".join(wrong),
        )

    def test_lint_text_can_never_report_the_rule(self):
        """Kept separate: a PURITY claim about a different function, not a phase's answer.

        F-10's corollary: `lint_text` is documented PURE (no I/O), and resolving a carrier IS I/O. The
        table above asks `lint_file`, which is allowed to touch the tree; this asserts the pure entry
        point reports the rule at NO phase and in NEITHER channel, so a refactor that wired the merge
        into the pure path fails here. A row cannot express it, because every row asks `lint_file`.
        """
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        text = plan.read_text(encoding="utf-8")
        for checkpoint in S.CHECKPOINTS:
            res = ipd_lint.lint_text(text, checkpoint=checkpoint, directory="pending")
            self.assertEqual(
                [d.code for d in res.diagnostics if d.code == RULE],
                [],
                f"lint_text must stay PURE, and reported the repo-aware rule as a diagnostic at "
                f"{checkpoint}",
            )
            self.assertEqual(
                [d.code for d in res.advisories if d.code == RULE],
                [],
                f"lint_text must stay PURE, and reported the repo-aware rule as an advisory at "
                f"{checkpoint}",
            )

    def test_the_merge_is_wired_into_lint_file_and_not_the_pure_path(self):
        """The repo-aware evaluator is reached from `lint_file` ONLY, proved by WATCHING the call.

        REPLACES A SOURCE-TEXT PIN. This searched three functions' source text for the substring
        `_merge_durable_carrier`: present in `lint_file`, absent from `check_checkpoint` and
        `lint_text`. Every one of those three assertions is the wrong instrument. The positive is
        satisfied by a COMMENT in `lint_file` (this repository has measured that exact failure twice),
        and BOTH negatives are satisfied in the WRONG DIRECTION by the merge being wired into the pure
        path through any other name at all: a rename, a dispatch table, an alias, or simply calling
        `check_engine.evaluate_durable_carrier` directly would leave the pure path impure while all
        three searches stayed green.

        SO THE CALL IS OBSERVED, not read. The shared evaluator is spied and each surface is driven
        over a fixture that MUST trip the rule: `lint_file` is required to reach it exactly once, and
        the two pure surfaces are required to reach it ZERO times through any route, which is a claim
        about I/O actually happening rather than about how the source is spelled.
        """
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        text = plan.read_text(encoding="utf-8")
        doc = ipd_lint.parse(text)

        # THE REPO-AWARE SURFACE: reaches the evaluator, exactly once, and reports the rule.
        with mock.patch.object(
            ce, "evaluate_durable_carrier", wraps=ce.evaluate_durable_carrier
        ) as spy:
            res = ipd_lint.lint_file(plan, checkpoint="pre-transition")
        self.assertEqual(
            spy.call_count,
            1,
            f"`lint_file` reached the shared evaluator {spy.call_count} times; it must reach it "
            "EXACTLY once. Zero means the repo-aware merge is unwired and an uncarried obligation "
            "can reach terminal; more than one means the plan is resolved repeatedly, which is the "
            "cost the per-sweep carrier index exists to avoid.",
        )
        self.assertEqual(
            [d.code for d in res.diagnostics if d.code == RULE],
            [RULE],
            "the fixture must actually trip the rule, or the spy count above describes a run that "
            "short-circuited before the merge",
        )

        # THE PURE SURFACES: reach it ZERO times, at EVERY checkpoint, by ANY route. `lint_text` and
        # `check_checkpoint` are documented pure, and resolving a carrier is I/O.
        for label, drive in (
            (
                "lint_text",
                lambda cp: ipd_lint.lint_text(text, checkpoint=cp, directory="pending"),
            ),
            (
                "check_checkpoint",
                lambda cp: ipd_lint.check_checkpoint(doc, cp, "pending"),
            ),
        ):
            with mock.patch.object(
                ce, "evaluate_durable_carrier", wraps=ce.evaluate_durable_carrier
            ) as spy:
                for checkpoint in S.CHECKPOINTS:
                    drive(checkpoint)
            self.assertEqual(
                spy.call_count,
                0,
                f"`{label}` reached the repo-aware evaluator {spy.call_count} times across "
                f"{len(S.CHECKPOINTS)} checkpoints. Its documented contract is PURITY (no I/O), and "
                "resolving a carrier id6 against the backlog and plans trees is I/O. A caller that "
                "relies on the pure contract now silently touches the filesystem.",
            )

    def test_one_predicate_backs_both_surfaces(self):
        """Kept separate: a SINGLE-PREDICATE claim, and the stronger form of an agreement test.

        REPLACES A SOURCE-TEXT PIN. This searched `check_durable_carrier`'s and
        `_merge_durable_carrier`'s source for the substring `evaluate_durable_carrier`. A comment
        naming the evaluator satisfies it while the body holds a second implementation, which is
        precisely the drift it existed to prevent, and a rename breaks it with no behavior change.

        WHY IT IS STILL NEEDED BESIDE THE ROUND-TRIP TABLE: that table asserts the two surfaces AGREE
        on every fixture, which a second implementation can satisfy today and violate next month. So
        what is asserted here is that ONE function produces BOTH answers, proved by REPLACING it with
        a sentinel and requiring the sentinel's own detail text to surface on both. A second
        implementation cannot produce the sentinel, and no fixture row can express this because every
        row drives the real evaluator.
        """
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        marker = "SENTINEL-ONLY-THE-SHARED-EVALUATOR-CAN-PRODUCE-THIS"

        def sentinel(_repo_root, *, plan_path, plan_text, **_kwargs):
            return [core.Drift(str(plan_path), RULE, marker, severity="error")]

        with mock.patch.object(ce, "evaluate_durable_carrier", sentinel):
            lint = ipd_lint.lint_file(plan, checkpoint="pre-transition")
            sweep = ce.check_durable_carrier(self.repo)

        self.assertEqual(
            [d.message for d in lint.diagnostics if d.code == RULE],
            [marker],
            "`aw ipd lint --phase pre-transition` did not surface the shared evaluator's own "
            "verdict, so the lint merge holds a SECOND implementation. Two predicates that agree "
            "today let the checkpoint gate and the sweep drift apart on what counts as carried.",
        )
        self.assertEqual(
            [d.detail for d in sweep if d.rule == RULE],
            [marker],
            "`aw check` did not surface the shared evaluator's own verdict, so the sweep holds a "
            "SECOND implementation.",
        )

    def test_the_carrier_checkpoint_set_diverges_from_the_review_escalation_set(self):
        """Kept separate: compares two MODULE-LEVEL SETS, not a plan's lint result.

        The asymmetry is deliberate and easy to "tidy" away: the review-escalation set EXCLUDES
        `pre-transition` (blocking there would strand a completed plan), while this rule REQUIRES it
        (that is precisely when the obligation vanishes). Asserting both sides keeps a future
        unification from silently moving this rule to the other schedule.
        """
        self.assertIn(
            "pre-transition",
            ipd_lint._CARRIER_CHECKPOINTS,
            "this rule MUST gate at pre-transition; that is the moment the obligation would vanish.",
        )
        self.assertNotIn(
            "pre-transition",
            ipd_lint._REVIEW_ESCALATION_CHECKPOINTS,
            "the review-escalation rule must NOT gate at pre-transition; the two schedules are "
            "deliberately different and must not be unified.",
        )

    def test_the_blocking_oq_check_still_fires_at_pre_execution(self):
        """Kept separate: asserts a DIFFERENT RULE (`C_CHECKPOINT`) is untouched, not this one.

        E-03's constraint was to neither move nor widen the pre-execution blocking-question check. The
        subject is another rule's code and message, so it belongs beside the carrier tests only as a
        regression guard, never as a row in a carrier table.
        """
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            open_questions=(
                "### OQ-01: unanswered?\n\n- Blocking: yes\n- Status: open\n"
                "- Owner: maintainer\n- Resolution or deferral rationale: pending\n"
            ),
        )
        res = ipd_lint.lint_file(plan, checkpoint="pre-execution")
        codes = [d.code for d in res.diagnostics]
        self.assertIn(ipd_lint.C_CHECKPOINT, codes)
        self.assertIn(
            "unresolved blocking question at pre-execution",
            " ".join(d.message for d in res.diagnostics),
        )


class CarrierSeverityTierTests(unittest.TestCase):
    """`carrier_severity_for_plan`: the tier read off a plan's OWN `- Date:`, at the boundary.

    ONE table replaces three tests (`test_a_plan_with_no_date_is_grandfathered_not_punished`,
    `test_the_severity_boundary_reads_the_plans_own_date`, and the constant check in
    `test_the_cutover_is_strictly_after_every_plan_that_exists_today`, which stays separate below).
    Each was one date string and one expected tier, which is a row, and together they never tried the
    boundary DATE ITSELF - the case where `>=` versus `>` decides the answer.

    Why the table beats them, and what it adds: the function is one regex plus one string comparison,
    and the interesting content is entirely at the edges. The rows walk the boundary from below, AT it,
    and above, and they pin the two degenerate inputs (no date, unparseable date) that both resolve to
    the GRANDFATHERED tier. That last point is a deliberate design choice rather than an accident, and
    stating it as adjacent rows is what stops someone "fixing" it into an error.

    The PLAN-LEVEL consequence of each tier (does it block, does it fail the gate) is asserted by
    `PlanLevelRoundTripTests`' date-differing row pair; this table asserts only the tier itself, which
    is why the two are separate.
    """

    #: (case, the plan text handed to the helper, the expected severity tier, why this row exists)
    TIERS = (
        (
            "a date AFTER the cutover",
            "- Date: 2026-09-20\n",
            "error",
            "a plan authored after this rule shipped gets the FAIL-CLOSED tier, which is the end state. "
            "The grandfathering below is a rollout accommodation, not a softening of the rule",
        ),
        (
            "a date EXACTLY AT the cutover",
            "- Date: {0}\n".format(_POST_DATE),
            "error",
            "THE BOUNDARY ITSELF, which none of the tests this replaces covered: the comparison is "
            "`>=`, so the cutover DAY is already the error tier. An off-by-one here would grandfather a "
            "day that should be gated, and the mistake would be invisible on any other date",
        ),
        (
            "the day BEFORE the cutover",
            "- Date: 2026-09-18\n",
            ce._CARRIER_LEGACY_SEVERITY,
            "one day earlier is GRANDFATHERED, which pins the boundary from below. Together with the row "
            "above this is the whole comparison, and 2026-09-18 is not arbitrary: measured, the newest "
            "plan date in the corpus was 2026-09-17, so this is the last day that must stay exempt",
        ),
        (
            "a plan with NO Date field at all",
            "# IPD: no date\n\n- Id: aaa111\n",
            ce._CARRIER_LEGACY_SEVERITY,
            "A MISSING DATE IS GRANDFATHERED, NOT PUNISHED, and the direction is deliberate: the "
            "metadata linter already owns the missing-Date complaint (IPD-M101), so inventing a second, "
            "harsher consequence here would make this rule fire on a defect it does not own",
        ),
        (
            "a Date field with an unparseable value",
            "- Date: not-a-date\n",
            ce._CARRIER_LEGACY_SEVERITY,
            "an UNPARSEABLE date falls to the same grandfathered tier as an absent one, so a malformed "
            "value cannot be a route to the harsher tier and cannot raise. Same ownership reasoning: "
            "the metadata linter complains about the format, this rule does not pile on",
        ),
    )

    def test_each_plan_date_selects_its_severity_tier(self):
        wrong = []
        for case, text, want, why in self.TIERS:
            got = ce.carrier_severity_for_plan(text)
            if got != want:
                wrong.append(
                    f"  {case} ({text.strip()!r}):\n"
                    f"    - expected the {want!r} tier, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.TIERS)} plan dates selected the wrong severity tier "
            f"(CARRIER_CUTOVER_DATE is {ce.CARRIER_CUTOVER_DATE!r}, the grandfathered tier is "
            f"{ce._CARRIER_LEGACY_SEVERITY!r}). If the `exactly at` and `day before` rows BOTH moved, "
            "the comparison flipped between `>=` and `>` or the constant changed; if only the two "
            "degenerate rows (no date, unparseable date) moved, someone made a missing date punishable "
            "here, which duplicates a complaint IPD-M101 already owns. FIX: the tier decides whether a "
            "finding BLOCKS, so promoting the grandfathered tier out of `info` would exit 1 on a clean "
            f"tree and train every agent to bypass `aw check`.\n" + "\n".join(wrong),
        )

    def test_the_cutover_is_strictly_after_every_plan_that_exists_today(self):
        """Kept separate: a claim about the CONSTANT's value against the corpus, not about a tier.

        The `SPEC_ID6_CUTOVER_DATE` precedent's rule: grandfather the whole existing corpus. The table
        above asserts how dates MAP to tiers given whatever the constant is; this asserts the constant
        was chosen late enough that no plan in the tree is retroactively gated.
        """
        self.assertGreater(
            ce.CARRIER_CUTOVER_DATE,
            "20260917",
            "the cutover must be strictly after the newest plan date in the corpus, or shipping this "
            "rule retroactively gates plans authored before it existed.",
        )


class RuleRegistrationTests(unittest.TestCase):
    def test_the_rule_id_resolves_to_a_registered_spec_not_the_default(self):
        """Kept separate: the subject is the RULE REGISTRY entry, not a plan or an obligation.

        A rule id that is absent from the registry silently inherits default metadata, so this asserts
        the four declared attributes. It shares no input with any table here: there is no fixture, no
        plan, and no verdict involved.
        """
        self.assertIn(RULE, ce.RULE_REGISTRY)
        spec = ce.rule_spec(RULE)
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec.assurance, ce.ASSURANCE_REPOSITORY)
        self.assertEqual(spec.determinism, ce.DET_DETERMINISTIC)
        self.assertEqual(spec.invariant, "I-07")


class SectionWalkTests(_RepoCase):
    """`_deferred_section_obligations`: which lines become obligations, and with which subfields.

    ONE table replaces three tests (`test_only_the_deferred_section_is_read`,
    `test_rows_are_numbered_in_source_order_with_their_subfields`,
    `test_a_continuation_line_is_not_a_new_row`). Each built one plan whose deferred section had a
    particular shape and asserted the resulting obligation list, which is a row.

    Kept as its own table rather than folded into the round trip because the SUBJECT is different: this
    is the WALKER, asserted directly on its parsed output, while the round trip asserts what the whole
    rule concludes. The distinction earns its keep because the walker's failures are invisible at the
    rule level: a walker that produced two obligations where one was meant still yields exactly ONE
    aggregated finding, so the round trip cannot see the miscount at all - only the `N obligation(s)`
    number would move, and only if the rows also happened to fail.

    Each row asserts BOTH the locator list AND each row's parsed fields, because the pairing of a
    subfield with its PARENT row is the walker's real job and a mis-pairing is how a carried row gets
    reported as uncarried (or, worse, an uncarried row gets silently discharged by its neighbour's
    field).
    """

    #: (case, the deferred-section text, the expected locator list, the expected per-row field dicts,
    #: why this row exists)
    SECTIONS = (
        (
            "an EMPTY deferred section",
            "",
            [],
            [],
            "the section is MANDATORY in both H2 orders, so its mere presence must not create an "
            "obligation. Every conforming plan in the repository has this heading, and a walker that "
            "counted the heading itself would fire on all of them. This also proves no bullet from "
            "ANOTHER section leaks in, since the surrounding fixture is full of them",
        ),
        (
            "three rows: uncarried, carried, declined",
            (
                "- FIRST: uncarried.\n"
                "- SECOND: carried.\n  - Carrier: car111\n"
                "- THIRD: declined.\n  - Carrier-Declined: not a defect\n"
            ),
            ["deferred row 1", "deferred row 2", "deferred row 3"],
            [{}, {"Carrier": "car111"}, {"Carrier-Declined": "not a defect"}],
            "SOURCE ORDER NUMBERING plus correct subfield PAIRING, which is the walker's whole job. The "
            "first row has NO fields even though a `Carrier` line appears two lines below it: if that "
            "field attached to row 1 instead of row 2, an uncarried obligation would be silently "
            "discharged by its neighbour's declaration and the gate would pass a plan it should refuse",
        ),
        (
            "one row with a CONTINUATION line before its subfield",
            (
                "- ONE ROW: with a long reason\n"
                "  that continues on the next line and says more.\n"
                "  - Carrier: car111\n"
            ),
            ["deferred row 1"],
            [{"Carrier": "car111"}],
            "AN INDENTED CONTINUATION IS NOT A NEW ROW, and the subfield after it still attaches to the "
            "original row. Long reasons wrapped over several lines are normal prose in this section, so "
            "a walker that treated any indented line as a boundary would both inflate the obligation "
            "count and orphan the carrier that follows",
        ),
        (
            "a row whose subfield is separated by a BLANK line",
            "- ONE ROW: a reason.\n\n  - Carrier: car111\n",
            ["deferred row 1"],
            [{"Carrier": "car111"}],
            "a BLANK LINE between the row and its subfield does not break the pairing either. Authors "
            "add blank lines for readability, and a stricter walker would report this correctly-carried "
            "row as uncarried, which is a false alarm the author cannot silence by doing anything right",
        ),
        (
            "two subfields under ONE row",
            "- ONE ROW: a reason.\n  - Carrier: car111\n  - Carrier-Declined: also declined\n",
            ["deferred row 1"],
            [{"Carrier": "car111", "Carrier-Declined": "also declined"}],
            "MULTIPLE typed subfields accumulate onto one row rather than the last overwriting the "
            "first. It matters because the predicate reads them in a fixed precedence order, so both "
            "must survive the walk for that precedence to be reachable at all",
        ),
    )

    def test_each_deferred_section_walks_to_its_obligations(self):
        wrong = []
        for case, rows, want_locators, want_fields, why in self.SECTIONS:
            plan = _plan(self.repo, date=_POST_DATE, deferred_rows=rows)
            obs = ce._deferred_section_obligations(plan.read_text(encoding="utf-8"))
            problems = []
            locators = [o.locator for o in obs]
            if locators != want_locators:
                problems.append(
                    f"expected locators {want_locators!r}, got {locators!r}"
                    + (
                        f" ({len(obs)} obligation(s) where {len(want_locators)} was expected; an "
                        "aggregated finding would still report as ONE, so this miscount is invisible "
                        "at the rule level)"
                        if len(obs) != len(want_locators)
                        else ""
                    )
                )
            fields = [dict(o.fields) for o in obs]
            if fields != want_fields:
                problems.append(
                    f"expected per-row fields {want_fields!r}, got {fields!r}; a subfield paired with "
                    "the WRONG row either discharges an obligation nobody carried or orphans a real "
                    "declaration"
                )
            for o in obs:
                if o.kind != "deferred":
                    problems.append(
                        f"{o.locator} has kind {o.kind!r}, expected 'deferred'"
                    )
                if o.line <= 0:
                    problems.append(
                        f"{o.locator} has line {o.line}, so the finding cannot cite a source location"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the deferred-section walker mishandled {len(wrong)} of {len(self.SECTIONS)} section "
            "shapes. One fence-aware loop with a flush-on-top-level-bullet state machine implements all "
            "of it, so several rows failing together means that state machine changed rather than "
            "several behaviors breaking: check the top-level-bullet boundary first (it decides the "
            "COUNT) and then the subfield pairing (it decides WHICH row is carried). FIX: a miscount "
            "here is nearly invisible downstream, because at most one aggregated finding is produced "
            "per plan regardless of how many obligations the walker found; a MIS-PAIRED subfield is "
            "worse still, since it can silently discharge an obligation the author never carried.\n"
            + "\n".join(wrong),
        )


if __name__ == "__main__":
    unittest.main()

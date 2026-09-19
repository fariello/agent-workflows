"""agentadhere Phase 1 (IPD uisjns): versioned policy engine + fixture corpus.

Covers the three E-items:
  E-01 - the versioned policy schema + enriched finding shape (rule id, severity, assurance class,
         observed/required, recovery, determinism tag, schema_version), backward compatibility, and
         determinism.
  E-02 - a positive + ADVERSARIAL fixture corpus with per-rule-id equality for EVERY invariant the
         phase-1 engine actually encodes today.
  E-03 - the `check.ipd-draft-ready-to-review` detect-and-nudge rule + the `authoring_placeholders_resolved`
         predicate + the `aw ipd lint --phase author` passing nudge.

DEFERRED adversarial cases (DECISION 14-uisjns-D1): findings section 9 also lists code-before-IPD,
out-of-scope staged tree, claimed-but-unrun / stale-tree test evidence, and missing/disabled/malformed
hook. Those invariants (Phase-0 catalog I-01 scope, I-05/I-06 evidence, hook-presence) are delivered by
agentadhere phases 2-5 and have NO `check_engine` rule yet, so their adversarial fixtures belong to the
phases that introduce their rules. Phase 1 covers exactly the rules the engine encodes today.

Most of this file is TABLE-DRIVEN, because most of it was one shape repeated: plant one artifact in a
throwaway records tree, call one `check_*` function, and assert one rule id. The tables group by
SUBJECT (the finding envelope, the severity contract, the rule corpus, the draft-readiness
predicate) rather than by which function implements the check.

THE RULE THAT SHAPES EVERY TABLE HERE is the same one the leak-sanitizer suites follow, and it
applies to a policy engine for the same reason: A POLICY TEST IS EVIDENCE ONLY IF THE RULE WAS
ACTUALLY EVALUATED. An assertion that a clean artifact yields no findings passes trivially when the
rule is not registered, not reached, or returns early. So every table containing a "this is clean"
or "this rule stays silent" expectation also contains, IN THE SAME TEST, an ADVERSARIAL row whose
named rule MUST fire. Those rows are labelled CONTROL in their reason string, and each table's
failure message states that its clean rows are vacuous while its controls are broken.

EVERY ROW ASSERTS THE RULE ID, and by EQUALITY of the reported rule set wherever the fixture is
narrow enough to make that meaningful. "Something was flagged" is not an assertion about a policy
engine: the rule ids are what `aw check --agent` emits, what the installed hooks branch on, and
what a recovery hint is looked up by, so a rule answering under a different id is a breaking change
to every consumer.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as core
from agent_workflows import check_engine as ce
from agent_workflows import ipd_authoring as authoring
from agent_workflows import ipd_lint as lint


# --------------------------------------------------------------------------------------
# E-01: versioned schema + enriched finding shape + backward compatibility + determinism
# --------------------------------------------------------------------------------------


class RuleRegistryTests(unittest.TestCase):
    """Every rule resolves to a fully classified spec, and an UNKNOWN rule fails safe.

    ONE table replaces the classification halves of two tests
    (`test_rule_registry_has_assurance_and_determinism`, plus the registry assertions inside
    `test_finding_dict_full_shape`). Both asked `rule_spec` for a rule and compared its
    `assurance` / `determinism` / `invariant` / `severity`, so the RULE is the data and the four
    fields are the assertion.

    Why the table beats them: these four fields are what make a finding actionable rather than
    merely true. `severity` decides whether the gate fails, `assurance` tells a reader how much the
    finding is worth, `determinism` says whether re-running can change the answer, and `invariant`
    links it back to the catalog. The realistic regression is a NEW rule being added without
    classification, or a default changing, and a table over several rules with DIFFERENT expected
    values catches both while a single-rule test cannot.

    THE UNKNOWN-RULE ROW IS THE FAIL-SAFE CONTROL, and it is the most important row here: an
    unregistered rule must default to `error` severity and `repository` assurance rather than being
    silently unclassified. A default of `info` would let a brand new rule fire into a passing gate,
    which is the quiet way a policy engine stops policing.

    THE HETEROGENEOUS ROWS ARE THE CONTROL FOR EACH OTHER. `check.ipd-draft-ready-to-review` is
    `info`/`guidance`/`heuristic` while the rest are `error`/`repository`/`deterministic`, so a
    registry hardcoded to return one constant spec cannot satisfy the table.
    """

    #: (case, the rule id, expected severity, expected assurance, expected determinism, expected
    #: catalog invariant or "" when none is expected, why this row exists)
    #:
    #: THE VALUES ARE LITERAL STRINGS WHERE THEY ARE AN EXTERNAL INTERFACE (`severity`, the rule
    #: ids) and module constants where the vocabulary is internal (`ASSURANCE_*`, `DET_*`).
    #: Severity is spelled literally on purpose: `artifact_core.drift_exit_code` compares against
    #: the STRING, and `aw check --agent` prints it, so a renamed constant that moved both sides
    #: together would hide a breaking change to every consumer.
    RULES = (
        (
            "the commit-scoped untooled-status rule",
            "check.status-untooled",
            "error",
            ce.ASSURANCE_REPOSITORY,
            ce.DET_DETERMINISTIC,
            "I-03",
            "THE REPRESENTATIVE HARD RULE: hand-editing a status is a forgery of the lifecycle, so "
            "it must be `error` (gate-failing) and `deterministic` (the same tree always gives the "
            "same answer). `I-03` ties it to the catalog invariant a reader can look up",
        ),
        (
            "the artifact-naming rule",
            "check.name-nonconformant",
            "error",
            ce.ASSURANCE_REPOSITORY,
            ce.DET_DETERMINISTIC,
            "I-09",
            "A SECOND HARD RULE WITH A DIFFERENT INVARIANT, so the `invariant` column cannot be "
            "satisfied by a constant. Naming is how every artifact is located by id6, so a "
            "nonconformant name is an artifact the tooling cannot find",
        ),
        (
            "the draft-readiness NUDGE",
            "check.ipd-draft-ready-to-review",
            "info",
            ce.ASSURANCE_GUIDANCE,
            ce.DET_HEURISTIC,
            "I-12",
            "THE ROW THAT MAKES THE OTHERS NON-VACUOUS: every field differs from the hard rules "
            "above. It is `info` (must NOT fail a gate), `guidance` (an opinion, not a "
            "verifiable repository fact), and `heuristic` (it reads placeholder markers, so it can "
            "be wrong). A registry returning one constant spec cannot pass this table",
        ),
        (
            "an unregistered rule id",
            "check.totally-unknown-rule",
            "error",
            ce.ASSURANCE_REPOSITORY,
            ce.DET_DETERMINISTIC,
            "",
            "THE FAIL-SAFE CONTROL, and the most important row here: an unknown rule must default "
            "to `error`, never to `info` or to blank. A rule added without a registry entry would "
            "otherwise fire into a PASSING gate and police nothing, which is the silent way this "
            "engine stops working. `invariant` is legitimately empty because there is no catalog "
            "entry to cite; the SEVERITY is what must not be lenient",
        ),
    )

    def test_every_rule_resolves_to_a_fully_classified_spec(self):
        wrong = []
        unknown_default_broken = False
        for case, rule, severity, assurance, determinism, invariant, why in self.RULES:
            spec = ce.rule_spec(rule)
            problems = []
            for field, expected, got in (
                ("severity", severity, spec.severity),
                ("assurance", assurance, spec.assurance),
                ("determinism", determinism, spec.determinism),
                ("invariant", invariant, spec.invariant),
            ):
                if got != expected:
                    if field == "severity" and rule == "check.totally-unknown-rule":
                        unknown_default_broken = True
                    problems.append(f"{field}: expected {expected!r}, got {got!r}")
            if problems:
                wrong.append(
                    f"  {case} ({rule}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if unknown_default_broken:
            note = (
                " THE UNKNOWN-RULE DEFAULT IS AMONG THE FAILURES, which is the fail-open direction: "
                "a rule with no registry entry would no longer fail the gate, so a newly added rule "
                "could fire while every gate stays green."
            )
        self.assertEqual(
            wrong,
            [],
            f"the rule registry misclassified {len(wrong)} of {len(self.RULES)} rules.{note} The "
            "four fields have distinct consumers, so which COLUMN failed names the impact: "
            "`severity` decides whether the gate fails, `assurance` tells a reader how much to "
            "trust the finding, `determinism` says whether a re-run can differ, and `invariant` is "
            "the catalog link. SEVERAL ROWS FAILING ON ONE COLUMN means the registry's defaults or "
            "that column's vocabulary changed rather than individual rules being wrong. FIX: never "
            "make a row pass by relaxing a severity to `info`; that converts a gate into a "
            f"suggestion.\n" + "\n".join(wrong),
        )


class FindingEnvelopeTests(unittest.TestCase):
    """The wire shape: an enriched finding carries the full envelope, a legacy Drift still works.

    ONE table replaces the shape halves of three tests (`test_drift_backward_compatible_three_arg`,
    `test_finding_dict_full_shape`, `test_backward_compat_characterization`). Each built a `Drift`,
    optionally enriched it, and asserted either the defaulted fields, the `finding_dict` key set,
    or the legacy `render_agent_drift` line. The DEGREE OF ENRICHMENT is the data, so it is a
    column: a bare 3-arg Drift, an enriched one, and an enriched one carrying observed/required.

    Why the table beats the three: the whole point of the enrichment was that it be ADDITIVE, and
    that is a claim about two shapes at once. The legacy consumers (`render_agent_drift`, the two
    installed hooks, `drift_exit_code`) read the 3-field triple, so every row asserts the enriched
    record has the full envelope AND still renders the exact legacy `location\\trule\\tdetail`
    line. Read apart, "the new fields exist" and "the old line is unchanged" look like unrelated
    facts; read together they are the compatibility contract, and the rows prove the extra fields
    never leak into the legacy line.

    THE BARE-DRIFT ROW IS THE CONTROL FOR THE ENRICHED ROWS: it requires the enrichment fields to
    default EMPTY, so an enrichment that silently populated them on construction (making every
    legacy Drift look reviewed and classified) is caught.
    """

    #: The keys `finding_dict` must always emit. Written out rather than derived from the function
    #: under test, because deriving them would make the assertion a tautology: a dropped key would
    #: disappear from both sides at once.
    REQUIRED_KEYS = (
        "schema_version",
        "rule",
        "severity",
        "assurance",
        "determinism",
        "invariant",
        "location",
        "detail",
        "observed",
        "required",
        "recovery",
    )

    #: (case, whether to enrich, kwargs passed to `enrich_drift`, expected `observed`, expected
    #: `required`, expected `recovery`, whether the full `finding_dict` envelope is required, why
    #: this row exists)
    RECORDS = (
        (
            "a bare 3-arg Drift, never enriched",
            False,
            {},
            "",
            "",
            "",
            False,
            "THE BACKWARD-COMPATIBILITY CONTROL: the historical 3-field constructor must still work "
            "and every enrichment field must default EMPTY. Without this row an enrichment that "
            "populated the fields on construction would pass every other row while making a legacy "
            "finding falsely claim classification it never had",
        ),
        (
            "an enriched Drift carrying a recovery hint",
            True,
            {"recovery": "aw rename ..."},
            "",
            "",
            "aw rename ...",
            True,
            "THE FULL ENVELOPE: `recovery` is the field that turns a complaint into an action a "
            "human or agent can take, so it must survive into `finding_dict` verbatim. The row also "
            "requires every envelope key to be present, since a consumer reading "
            "`finding['determinism']` crashes on a missing key rather than degrading",
        ),
        (
            "an enriched Drift carrying observed and required",
            True,
            {"recovery": "aw rename ...", "observed": "o", "required": "r"},
            "o",
            "r",
            "aw rename ...",
            True,
            "THE EXPECTED-VERSUS-ACTUAL PAIR, which is what lets a report say what it FOUND against "
            "what it NEEDED instead of only naming a rule. It is also the fullest record the engine "
            "produces, so it is the strongest test that NONE of the extra fields leaks into the "
            "legacy tab-separated line asserted below",
        ),
    )

    def test_enrichment_is_additive_and_never_changes_the_legacy_line(self):
        wrong = []
        for (
            case,
            enrich,
            kwargs,
            observed,
            required,
            recovery,
            full,
            why,
        ) in self.RECORDS:
            base = core.Drift("some/loc.md", "check.name-nonconformant", "bad name")
            record = ce.enrich_drift(base, **kwargs) if enrich else base
            problems = []
            if (record.location, record.rule, record.detail) != (
                "some/loc.md",
                "check.name-nonconformant",
                "bad name",
            ):
                problems.append(
                    "the original three fields must be preserved; got "
                    f"{(record.location, record.rule, record.detail)!r}"
                )
            for field, expected in (
                ("observed", observed),
                ("required", required),
            ):
                if getattr(record, field) != expected:
                    problems.append(
                        f"{field}: expected {expected!r}, got {getattr(record, field)!r}"
                    )
            if not enrich and record.severity != "":
                problems.append(
                    f"an unenriched Drift must carry an EMPTY severity (it has not been "
                    f"classified); got {record.severity!r}"
                )
            # The legacy line is the contract two installed hooks and `render_agent_drift`
            # consumers read. The extra fields must never appear in it.
            rendered = core.render_agent_drift([record])
            if rendered != "some/loc.md\tcheck.name-nonconformant\tbad name\n":
                problems.append(
                    "the legacy tab-separated line must be byte-identical whatever the enrichment; "
                    f"got {rendered!r}"
                )
            if full:
                fd = ce.finding_dict(record)
                missing = [k for k in self.REQUIRED_KEYS if k not in fd]
                if missing:
                    problems.append(
                        f"finding_dict is missing {missing!r}; a consumer reading those keys "
                        f"crashes rather than degrading. Full record: {fd!r}"
                    )
                if fd.get("schema_version") != ce.POLICY_SCHEMA_VERSION:
                    problems.append(
                        f"schema_version must be {ce.POLICY_SCHEMA_VERSION!r}; got "
                        f"{fd.get('schema_version')!r}. It is how a consumer knows which shape it "
                        "received"
                    )
                if fd.get("recovery") != recovery:
                    problems.append(
                        f"recovery must round-trip into finding_dict as {recovery!r}; got "
                        f"{fd.get('recovery')!r}"
                    )
                if fd.get("assurance") != ce.ASSURANCE_REPOSITORY:
                    problems.append(
                        f"assurance must be resolved from the registry "
                        f"({ce.ASSURANCE_REPOSITORY!r}); got {fd.get('assurance')!r}"
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
            f"the finding envelope mishandled {len(wrong)} of {len(self.RECORDS)} records. Every row "
            "asserts the NEW envelope and the LEGACY line together, so which half failed names the "
            "break: a legacy-line failure means existing hooks and `--agent` consumers break "
            "immediately, while an envelope failure means the new policy fields are wrong or "
            "missing. The bare-Drift row failing ALONE means enrichment is happening on "
            "construction, so a legacy finding now claims a classification nobody assigned. FIX: "
            "`REQUIRED_KEYS` is written out deliberately rather than derived from `finding_dict`; "
            f"do not 'simplify' it into a reflection of the code it checks.\n"
            + "\n".join(wrong),
        )


class SeverityGateTests(unittest.TestCase):
    """Severity decides the exit code: `info` is advisory, `error` fails, legacy still fails.

    ONE table replaces `test_info_severity_is_advisory_non_failing` and the exit-code assertions
    scattered through `test_backward_compat_characterization`. Each built one Drift and called
    `drift_exit_code`, so the finding is the data and the expected exit code is the assertion.

    Why the table beats them: this single function is what converts a list of findings into a
    PASS or FAIL for the hook and for CI, and the property worth asserting is that the three cases
    map to exactly two outcomes. Read as one table, the three-into-two mapping is the statement;
    read as separate assertions inside a characterization test, it was an incidental detail of a
    test about something else.

    BOTH DIRECTIONS ARE PRESENT AND EACH IS THE OTHER'S CONTROL. An empty list and an `info`
    finding must exit 0; an `error` finding and a legacy unclassified one must exit 1. A function
    that always returned 0 would satisfy the advisory rows, and one that always returned 1 would
    satisfy the failing rows, so neither group is evidence without the other.
    """

    #: (case, the rule id to build a finding from or None for an EMPTY finding list, whether to
    #: enrich it, expected exit code, why this row exists)
    FINDINGS = (
        (
            "no findings at all",
            None,
            False,
            0,
            "THE BASELINE: a clean run must exit 0, or every commit is blocked and the hook is "
            "removed within a day",
        ),
        (
            "an `info` severity nudge",
            "check.ipd-draft-ready-to-review",
            True,
            0,
            "ADVISORY MEANS ADVISORY: a nudge is a suggestion about a DRAFT, so it must be reported "
            "without failing anything. If it failed the gate, authors would learn to avoid the "
            "draft status entirely, which loses the very signal the rule provides",
        ),
        (
            "an `error` severity finding",
            "check.name-nonconformant",
            True,
            1,
            "THE CONTROL FOR BOTH ADVISORY ROWS: without it, a `drift_exit_code` hardcoded to 0 "
            "would satisfy them perfectly and NOTHING would ever fail a gate again. This is the "
            "row that proves the function discriminates",
        ),
        (
            "a LEGACY unclassified finding (empty severity)",
            "check.name-nonconformant",
            False,
            1,
            "FAIL-SAFE ON MISSING CLASSIFICATION: a 3-field Drift built by an older caller carries "
            "no severity at all, and it must still FAIL rather than be treated as advisory. A "
            "blank-equals-lenient reading would silently downgrade every pre-enrichment call site",
        ),
    )

    def test_only_error_and_unclassified_severities_fail_the_gate(self):
        wrong = []
        failing_rows_broken = 0
        for case, rule, enrich, expect_code, why in self.FINDINGS:
            if rule is None:
                findings = []
            else:
                d = core.Drift("p", rule, "x")
                findings = [ce.enrich_drift(d) if enrich else d]
            code = core.drift_exit_code(findings)
            problems = []
            if code != expect_code:
                if expect_code == 1:
                    failing_rows_broken += 1
                problems.append(
                    f"expected exit {expect_code}, got {code}"
                    + (f" (severity was {findings[0].severity!r})" if findings else "")
                )
            if enrich and rule and findings:
                expected_sev = ce.rule_spec(rule).severity
                if findings[0].severity != expected_sev:
                    problems.append(
                        f"enrichment must set severity from the registry ({expected_sev!r}); got "
                        f"{findings[0].severity!r}, so the exit code above was decided by the wrong "
                        "input"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if failing_rows_broken:
            note = (
                f" {failing_rows_broken} FAILING row(s) are among the failures, which is the "
                "fail-open direction: a finding that must block the gate no longer does, and the "
                "advisory rows in this table are vacuous because a function returning 0 for "
                "everything satisfies them."
            )
        self.assertEqual(
            wrong,
            [],
            f"drift_exit_code mishandled {len(wrong)} of {len(self.FINDINGS)} finding lists.{note} "
            "The rows map three severity states onto two exit codes, so the pattern names the "
            "defect: both advisory rows failing means `info` is being treated as fatal (authors "
            "will abandon the draft status), both failing rows means nothing fails any more, and the "
            "LEGACY row alone means blank severity is now read as lenient, silently downgrading "
            "every pre-enrichment call site. FIX: this one function is the boundary between the "
            f"engine and CI, so a wrong answer here changes the verdict of every check in the repo.\n"
            + "\n".join(wrong),
        )

    def test_determinism_repeated_runs_identical(self):
        """Kept separate: the subject is TWO RUNS of the engine over a real tree, not one finding.

        V-01(c). Determinism is a property of the whole pipeline (directory enumeration order,
        dict iteration, path rendering), so it needs a materially different setup from the rows
        above: a records tree on disk, scanned twice, with the full `finding_dict` compared. There
        is no per-row data, and the assertion is an equality between two runs rather than about a
        value.

        The fixture plants a NONCONFORMANT spec on purpose: two runs that both find NOTHING are
        trivially identical, so the comparison would be vacuous over a clean tree.
        """
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        specs = root / ".aw" / "records" / "specs"
        specs.mkdir(parents=True)
        (specs / "20260828-1200-01-legacy.spec.md").write_text(
            "# Spec: x\n\n- Date: 2026-08-28\n- Status: reviewed\n\n"
            "## Workflow history\n\n- 2026-08-28 created (aw specs): x\n",
            encoding="utf-8",
        )
        run1 = [
            ce.finding_dict(ce.enrich_drift(d), root)
            for d in ce.check_type(root, "specs")
        ]
        run2 = [
            ce.finding_dict(ce.enrich_drift(d), root)
            for d in ce.check_type(root, "specs")
        ]
        self.assertEqual(run1, run2)
        # A comparison of two empty lists would prove nothing, so pin that the fixture really is
        # dirty; this is what makes the equality above meaningful.
        self.assertTrue(
            run1, "the fixture must produce findings, or comparing two runs is vacuous"
        )


# --------------------------------------------------------------------------------------
# E-02: positive + adversarial fixture corpus (rule-id equality, per encoded invariant)
# --------------------------------------------------------------------------------------


class FixtureCorpusTests(unittest.TestCase):
    """The rule corpus: each encoded invariant fires on its own adversarial fixture, and a clean
    artifact fires nothing.

    ONE table replaces five tests (`test_positive_clean_specs`, `test_adversarial_name_nonconformant`,
    `test_adversarial_setid_collision`, `test_adversarial_ipd_dependency_malformed`, and the
    `test_adversarial_release_gate_blocking_close` fixture). Each planted artifacts in a throwaway
    records tree, called ONE `check_*` entry point, and compared the reported rule set. The CHECK
    ENTRY POINT is therefore a column, not a reason for five methods.

    Why the table beats the five: these rule ids are what `aw check --agent` emits and what the
    installed hooks branch on, so the realistic regression is a rule being renamed, unregistered,
    or made unreachable. Five tests report that as five unrelated set-comparison failures; the
    table reports one failure naming every invariant that stopped firing, which is the shape of the
    real problem (usually one refactor). It also makes the covered corpus browsable, which matters
    for a phase-1 engine whose explicit contract is "exactly the rules encoded today" - the next
    phase's author can see what exists without reading five setups.

    THE CLEAN ROW IS FIRST AND EVERY ADVERSARIAL ROW IS ITS CONTROL. A clean artifact yielding no
    failing findings is the shape that passes when a check is not wired up at all, so it is
    meaningful only beside rows that require named rules to fire from the SAME engine build. The
    failure message says so explicitly.

    ROWS THAT CAN ASSERT SET EQUALITY DO, and the rest say why not. A narrow fixture with exactly
    one defect should report exactly one rule, and equality catches a check that fires a second,
    unrelated rule on a fixture it should not judge. Where a check legitimately reports other rules
    for the same tree (the release-gate fixture also has a git state), the row asserts membership
    and records that in its reason.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _tree(self, name) -> Path:
        root = Path(self._tmp.name) / name
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _git_init(root: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)

    CLEAN_SPEC = (
        "# Spec: clean\n\n- Date: 2026-01-01\n- Status: reviewed\n- Id: abc123\n\n"
        "## Workflow history\n\n- 2026-01-01 created (aw specs): clean\n"
    )
    LEGACY_SPEC = (
        "# Spec: x\n\n- Date: 2026-08-28\n- Status: reviewed\n\n"
        "## Workflow history\n\n- 2026-08-28 created (aw specs): x\n"
    )

    #: (case, fixture builder key, the check entry point to call, the rule set that MUST be
    #: reported, whether the reported set must EQUAL that (vs merely contain it), the expected
    #: catalog invariant or "" to skip, why this row exists)
    #:
    #: THE RULE IDS ARE LITERAL STRINGS, NOT looked up from the registry, and that is deliberate:
    #: resolving them through `check_engine` would make a RENAME invisible, because both sides would
    #: move together. These ids are a published interface (`aw check --agent` prints them, the two
    #: installed hooks branch on them, recovery hints are keyed by them), so a rename is a breaking
    #: change and must fail here.
    CASES = (
        (
            "a fully conformant spec",
            "clean-spec",
            "check_type-specs",
            frozenset(),
            True,
            "",
            "THE POSITIVE ROW: a correctly named, id6-clustered, status-carrying spec must produce "
            "NO failing findings. Every adversarial row below is vacuous while this one is broken, "
            "because an engine that flagged everything would satisfy them all and would be "
            "unusable. Conversely this row alone proves nothing: an engine with no rules registered "
            "passes it perfectly",
        ),
        (
            "a post-cutover spec with a legacy (non-id6) filename",
            "legacy-spec",
            "check_names-specs",
            frozenset({"check.name-nonconformant"}),
            True,
            "I-09",
            "I-09 CONTROL: every artifact is located by the id6 in its NAME, so a post-cutover file "
            "without one is invisible to `aw find`, to the plans index, and to every cross-reference "
            "that resolves by id. Set EQUALITY is asserted because this fixture has exactly one "
            "defect: a second rule firing here would mean the namer is judging something it was not "
            "asked about",
        ),
        (
            "two specs sharing a setid with CONFLICTING descriptives",
            "setid-conflict",
            "check_collisions",
            frozenset({"check.setid-collision"}),
            False,
            "I-16",
            "I-16 CONTROL. REPOINTED by setidfix 216rgg E-05 from a cross-type fixture (a plan and "
            "a spec sharing a setid), which this test used to call adversarial. Under D153 / spec "
            "`2lcqno` N1 that is the endorsed NORMAL state - a setid is a shared cross-type TOPIC "
            "label - so the old fixture's INTENT was wrong, not merely its data, and the cross-type "
            "case is now pinned as SILENT in `tests/test_check_engine.py`. What remains adversarial "
            "is one setid carrying two different descriptives INSIDE one type: that is a real "
            "inconsistency in that Set's own name. Membership rather than equality, because "
            "`check_collisions` scans the whole tree for several collision classes",
        ),
        (
            "a plan whose Item-Dependencies field is unparseable",
            "malformed-deps",
            "evaluate_ipd_dependencies",
            frozenset({"check.ipd-dependency-malformed"}),
            True,
            "I-08",
            "I-08 CONTROL: a dependency edge nothing can parse is an ordering constraint the runner "
            "cannot honor, so a plan could execute before the plan it depends on. Set EQUALITY is "
            "asserted here, which is stricter than the test it replaces (that one accepted ANY rule "
            "starting `check.ipd-dependency-`, so a malformed edge reported as a missing-target "
            "edge would have passed and the two have different fixes)",
        ),
        (
            "a release-blocking backlog item hand-edited to done and STAGED",
            "blocking-close",
            "check_release_gate_consistency",
            frozenset({"check.blocking-item-closed-without-gate"}),
            False,
            "I-07",
            "I-07 CONTROL, and the one COMMIT-SCOPED row: the rule reads the git INDEX, because the "
            "bypass it catches is a human editing the file instead of using `aw backlog set done`. "
            "Closing a release blocker without preserving the gate is how a release ships with a "
            "blocker silently dropped. Membership rather than equality, because the fixture is a "
            "real git tree the checker may report other release-gate observations about",
        ),
    )

    def _build(self, key: str) -> Path:
        root = self._tree(key)
        if key == "clean-spec":
            specs = root / ".aw" / "records" / "specs"
            specs.mkdir(parents=True, exist_ok=True)
            (specs / "20260101-abc123-01-abc123-clean.spec.md").write_text(
                self.CLEAN_SPEC, encoding="utf-8"
            )
        elif key == "legacy-spec":
            specs = root / ".aw" / "records" / "specs"
            specs.mkdir(parents=True, exist_ok=True)
            (specs / "20260828-1200-01-legacy.spec.md").write_text(
                self.LEGACY_SPEC, encoding="utf-8"
            )
        elif key == "setid-conflict":
            specs = root / ".aw" / "records" / "specs"
            specs.mkdir(parents=True, exist_ok=True)
            (specs / "20260101-shared-01-aaa111-a.spec.md").write_text(
                "# Spec: a\n\n- Date: 2026-01-01\n- Status: reviewed\n- Id: aaa111\n"
                "- Set: shared (Alpha)\n\n## Workflow history\n\n"
                "- 2026-01-01 created (aw specs): a\n",
                encoding="utf-8",
            )
            (specs / "20260101-shared-02-bbb222-b.spec.md").write_text(
                "# Spec: b\n\n- Date: 2026-01-01\n- Status: reviewed\n- Id: bbb222\n"
                "- Set: shared (Beta)\n\n## Workflow history\n\n"
                "- 2026-01-01 created (aw specs): b\n",
                encoding="utf-8",
            )
        elif key == "malformed-deps":
            plans = root / ".aw" / "records" / "plans" / "pending"
            plans.mkdir(parents=True, exist_ok=True)
            (plans / "20260101-dep-01-dep001-p.ipd.md").write_text(
                "# IPD: p\n\n- Id: dep001\n- Status: approved\n- Set: dep\n"
                "- Item-Dependencies: not-a-valid-edge-format!!!\n\n## Goal\n\nx\n",
                encoding="utf-8",
            )
        else:  # blocking-close
            self._git_init(root)
            rel = root / ".aw" / "records" / "releases"
            rel.mkdir(parents=True, exist_ok=True)
            (rel / "20260101-rel01-01-rel001-next.release.md").write_text(
                "# Release: next\n\n- Id: rel001\n- Status: planned\n- Version: next\n"
                "- Summary: s\n",
                encoding="utf-8",
            )
            openb = root / ".aw" / "records" / "backlog" / "open"
            openb.mkdir(parents=True, exist_ok=True)
            item = openb / "20260101-blk-01-blk001-item.backlog.md"
            body = (
                "- Id: blk001\n- Status: {status}\n- Set: blk\n- Priority: high\n"
                "- Kind: chore\n- Summary: a blocking item\n- Blocks-Release: rel001\n\n"
                "## Workflow history\n- 2026-01-01 open (aw backlog): x\n"
            )
            item.write_text(body.format(status="open"), encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)
            # The hand-edit bypass: flip to done, move into done/, and STAGE it.
            done = root / ".aw" / "records" / "backlog" / "done"
            done.mkdir(parents=True, exist_ok=True)
            (done / "20260101-blk-01-blk001-item.backlog.md").write_text(
                body.format(status="done"), encoding="utf-8"
            )
            item.unlink()
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        return root

    def _invoke(self, entry: str, root: Path):
        if entry == "check_type-specs":
            return ce.check_type(root, "specs")
        if entry == "check_names-specs":
            return ce.check_names(root, "specs")
        if entry == "check_collisions":
            return ce.check_collisions(root)
        if entry == "evaluate_ipd_dependencies":
            return ce.evaluate_ipd_dependencies(root, phase="pre-execution")
        return ce.check_release_gate_consistency(root)

    def test_every_encoded_invariant_fires_on_its_fixture_and_the_clean_one_fires_nothing(
        self,
    ):
        wrong = []
        controls_broken = []
        positive_broken = False
        for case, key, entry, expected, exact, invariant, why in self.CASES:
            root = self._build(key)
            drift = self._invoke(entry, root)
            reported = {d.rule for d in drift}
            problems = []
            missing = expected - reported
            if missing:
                controls_broken.extend(sorted(missing))
                problems.append(
                    f"expected {sorted(missing)!r} to fire; the engine reported "
                    f"{sorted(reported) or 'NOTHING AT ALL, so this check is not evaluating'}"
                )
            if exact and reported != expected:
                extra = reported - expected
                if extra:
                    problems.append(
                        f"reported {sorted(extra)!r} in addition; this fixture has exactly one "
                        "defect, so a second rule means a check is judging something it was not "
                        "asked about"
                    )
            if not expected:
                # The positive row: nothing may FAIL the gate.
                code = core.drift_exit_code(drift)
                if code != 0:
                    positive_broken = True
                    problems.append(
                        f"a clean artifact must not fail the gate; drift_exit_code returned {code} "
                        f"for {sorted(reported)!r}"
                    )
            if invariant and expected:
                rule = sorted(expected)[0]
                got_inv = ce.rule_spec(rule).invariant
                if got_inv != invariant:
                    problems.append(
                        f"{rule!r} must trace to catalog invariant {invariant!r}; the registry says "
                        f"{got_inv!r}, so the finding cannot be looked up in the catalog"
                    )
            if problems:
                wrong.append(
                    f"  {case} [{entry}]:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if controls_broken:
            note += (
                f" THE ADVERSARIAL CONTROL ROW(S) FOR {sorted(set(controls_broken))!r} FAILED, so "
                "those rules are not firing and THE POSITIVE ROW PROVES NOTHING: a tree with no "
                "rules registered satisfies it. Fix the controls first."
            )
        if positive_broken:
            note += (
                " THE POSITIVE ROW ALSO FAILED, so the engine is flagging a conformant artifact; "
                "while that is true every adversarial row is satisfied for the wrong reason, since "
                "an engine that flags everything fires every rule."
            )
        self.assertEqual(
            wrong,
            [],
            f"the rule corpus mishandled {len(wrong)} of {len(self.CASES)} fixtures.{note} The rule "
            "ids are a published interface (`aw check --agent` prints them, both installed hooks "
            "branch on them, recovery hints are keyed by them), so SEVERAL ROWS FAILING TOGETHER "
            "usually means one refactor unregistered a family rather than several independent "
            "breakages: compare the entry points in the failures before editing any rule. FIX: a "
            "row reporting NOTHING AT ALL is worse than one reporting the wrong id, because a check "
            f"that stopped evaluating lets the violation through every gate that consumes it.\n"
            + "\n".join(wrong),
        )

    def test_adversarial_hand_edited_status_untooled(self):
        """Kept separate: MATERIALLY DIFFERENT SETUP (a two-commit git history it must compare).

        `check.status-untooled` (I-03) is commit-scoped like the release-gate row, but it needs
        something none of the table rows do: a COMMITTED baseline whose status differs from the
        STAGED one, because the rule detects a status that changed without a tool-authored history
        line. That is a sequence of git operations rather than a fixture, so it cannot be expressed
        as a row without making the table's builder a second test harness.

        The rule id is asserted by MEMBERSHIP rather than equality because a real git tree may
        legitimately produce other observations.
        """
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self._git_init(root)
        plans = root / ".aw" / "records" / "plans" / "pending"
        plans.mkdir(parents=True)
        f = plans / "20260101-unt-01-unt001-p.ipd.md"
        body = (
            "# IPD: p\n\n- Id: unt001\n- Status: {status}\n- Set: unt\n\n"
            "## Workflow history\n- 2026-01-01 draft (x): created.\n\n## Goal\n\nx\n"
        )
        f.write_text(body.format(status="draft"), encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)
        # Hand-edit the status with NO tool-authored history line, then STAGE it.
        f.write_text(body.format(status="approved"), encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        rules = {d.rule for d in ce.check_status_untooled(root)}
        self.assertIn("check.status-untooled", rules, rules)


# --------------------------------------------------------------------------------------
# E-03: draft-readiness predicate + rule + lint author nudge
# --------------------------------------------------------------------------------------


_READY_DRAFT = """# IPD: A ready draft

- Date: 2026-08-28
- Kind: child
- Concern: A real, fully authored concern statement for review.
- Scope: A real scope statement describing what this plan changes.
- Scope-Paths: agent_workflows/foo.py, tests/
- Item-Dependencies: none
- Status: draft
- Set: rdy
- Order: 1
- Highest E allocated: 01
- Author: tester
- Id: rdy001

## Workflow history
- 2026-08-28 draft (tester): created.

## Goal

Deliver a real, fully authored goal statement.

## Detailed Implementation Checklist (TODO)

### Task group 1: real work

- [ ] E-01 Do a real observable action.
  - Depends on: none
  - Expected outcome: a real observable result.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: a real falsifiable evidence statement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
"""


class DraftReadinessTests(unittest.TestCase):
    """Draft readiness: the predicate, the nudge rule, and the lint advisory must agree.

    ONE table replaces seven tests (`test_predicate_resolved_true_for_ready_draft`,
    `test_predicate_false_for_scaffold_placeholder`, `test_predicate_no_false_positive_on_prose_todo`,
    `test_rule_nudges_ready_draft_with_recovery`, `test_rule_silent_for_stub_draft`,
    `test_lint_author_phase_emits_nudge_advisory`, `test_lint_author_phase_silent_for_stub`). Each
    took the same ready-draft fixture, changed one field, and asked ONE of the three layers about
    it. THE LAYER IS THEREFORE NOT A CLASS BOUNDARY, IT IS SOMETHING EVERY ROW EXERCISES: each row
    now runs the predicate, the `check_engine` rule, and `ipd lint --phase author` on the SAME text.

    Why that is the whole point of merging here: these three layers must AGREE, and the old split
    made disagreement invisible. The predicate is the implementation, the rule is how `aw check`
    surfaces it, and the lint advisory is how an author sees it during authoring; a change that
    made the predicate stricter while the lint path kept its own copy of the logic would have left
    every old test green in its own class. Three tests said "the predicate is False here", "the rule
    is silent here", and "lint is silent here" about three separately constructed stubs; now one row
    asserts all three about one document, so a layer that drifted is named.

    THE SILENT ROWS ARE THE CONTROL FOR THE NUDGING ROWS AND VICE VERSA, in both directions. A
    predicate hardwired to True would nudge every stub (satisfying the nudging rows), and one
    hardwired to False would nudge nothing (satisfying the silent rows), so neither group is
    evidence alone. The failure message says which happened.

    THE PROSE-TODO ROW IS THE FALSE-POSITIVE CONTROL (OQ-02). The predicate keys on ANCHORED
    scaffold marker strings, not on the word "TODO", so a plan that legitimately discusses TODO
    items must still count as authored. Without that row the predicate could be a bare `"TODO" not
    in text` and every other row would still pass - and the file's `## Detailed Implementation
    Checklist (TODO)` heading means that naive version would call EVERY plan a stub.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)

    #: (case, (find, replace) applied to the ready draft or None for none, whether the predicate
    #: must call it RESOLVED, whether the nudge must fire, why this row exists)
    DRAFTS = (
        (
            "the fully authored ready draft",
            None,
            True,
            True,
            "THE NUDGING CONTROL: a draft with every placeholder replaced is exactly what the rule "
            "exists to catch, because an author who finished writing and forgot to advance the "
            "status leaves the plan invisible to review. Every SILENT row below is vacuous while "
            "this one is broken, since a predicate hardwired to False satisfies them all",
        ),
        (
            "an unreplaced `- Concern: TODO.` scaffold placeholder",
            (
                "- Concern: A real, fully authored concern statement for review.",
                "- Concern: TODO.",
            ),
            False,
            False,
            "THE SILENT CONTROL: a stub is still being written, so nudging it toward review would "
            "train authors to ignore the nudge. `Concern` is the field a reviewer reads first, so a "
            "plan whose concern is literally `TODO.` is not reviewable",
        ),
        (
            "an unreplaced `- Scope: TODO.` scaffold placeholder",
            (
                "- Scope: A real scope statement describing what this plan changes.",
                "- Scope: TODO.",
            ),
            False,
            False,
            "A SECOND PLACEHOLDER ON A DIFFERENT FIELD: `_AUTHORING_PLACEHOLDERS` is a closed "
            "tuple, and one row per member is what keeps a deletion from that tuple individually "
            "visible. A predicate that only checked `Concern` would pass the row above and this one "
            "would catch it",
        ),
        (
            "an unassigned E-NEW checklist leaf",
            ("E-01 Do a real observable action.", "E-NEW Do a thing."),
            False,
            False,
            "A STRUCTURALLY DIFFERENT PLACEHOLDER: not a `TODO.` string at all, but an unassigned "
            "item id awaiting `aw ipd sync`. A plan whose items have no stable ids cannot be "
            "reviewed or executed (nothing can reference E-NEW), so readiness must key on more than "
            "prose placeholders",
        ),
        (
            "narrative prose that merely mentions TODO items",
            (
                "- Concern: A real, fully authored concern statement for review.",
                "- Concern: We plan to clear the TODO items in the backlog next.",
            ),
            True,
            True,
            "THE FALSE-POSITIVE CONTROL (OQ-02): the predicate matches ANCHORED scaffold markers, "
            "not the word TODO, so legitimately discussing TODO items must still count as authored. "
            'Without this row the predicate could be a bare `"TODO" not in text` and every other '
            "row would still pass - and since the canonical section heading is literally `## "
            "Detailed Implementation Checklist (TODO)`, that naive version would call EVERY plan in "
            "the repository a stub and the nudge would never fire again",
        ),
    )

    def test_the_predicate_the_rule_and_the_lint_advisory_agree_on_every_draft(self):
        wrong = []
        nudging_controls_broken = False
        for case, edit, resolved, nudges, why in self.DRAFTS:
            text = _READY_DRAFT if edit is None else _READY_DRAFT.replace(*edit)
            if edit is not None and text == _READY_DRAFT:
                # A replacement that matched nothing would silently make the row a duplicate of the
                # ready-draft row; fail loudly instead of testing the wrong document.
                wrong.append(
                    f"  {case}:\n    - the fixture edit {edit!r} matched nothing, so this row "
                    f"tested the UNMODIFIED draft\n    this row exists because: {why}"
                )
                continue
            path = self.plans / f"20260828-rdy-01-rdy001-{abs(hash(case))}.ipd.md"
            path.write_text(text, encoding="utf-8")
            problems = []
            # Layer 1: the predicate.
            got_resolved = authoring.authoring_placeholders_resolved(text)
            if got_resolved != resolved:
                problems.append(
                    f"authoring_placeholders_resolved returned {got_resolved}, expected {resolved}"
                )
            # Layer 2: the check_engine rule.
            drift = [
                d
                for d in ce.check_ipd_draft_ready(self.root)
                if Path(d.location).name == path.name or path.name in str(d.location)
            ]
            rules = {d.rule for d in drift}
            if nudges:
                if rules != {"check.ipd-draft-ready-to-review"}:
                    nudging_controls_broken = True
                    problems.append(
                        "expected exactly {'check.ipd-draft-ready-to-review'} from "
                        f"check_ipd_draft_ready; got {rules or 'NOTHING AT ALL'}"
                    )
                else:
                    d = drift[0]
                    if d.severity != "info":
                        problems.append(
                            f"the nudge must be `info` severity so it cannot fail a gate; got "
                            f"{d.severity!r}"
                        )
                    if d.recovery != "aw ipd set to-review rdy001":
                        problems.append(
                            "the nudge must carry the exact command that resolves it "
                            f"('aw ipd set to-review rdy001'); got {d.recovery!r}. A nudge with no "
                            "runnable recovery makes the author guess"
                        )
            elif rules:
                problems.append(
                    f"the rule must stay SILENT for this draft; it reported {rules!r}"
                )
            # Layer 3: the lint author-phase advisory, which is how an author actually sees it.
            res = lint.lint_file(path, checkpoint="author")
            codes = {a.code for a in res.advisories}
            if nudges and "check.ipd-draft-ready-to-review" not in codes:
                problems.append(
                    "`ipd lint --phase author` must surface the nudge as an ADVISORY; its "
                    f"advisories were {sorted(codes)!r}. The rule firing in `aw check` but not in "
                    "lint means the author never sees it where they are working"
                )
            if not nudges and "check.ipd-draft-ready-to-review" in codes:
                problems.append(
                    "`ipd lint --phase author` must stay silent for a stub; it advised anyway, so "
                    "lint and the rule disagree about the same document"
                )
            # DETECT AND NUDGE, NEVER ACT: the status must be untouched on disk.
            if "- Status: draft" not in path.read_text(encoding="utf-8"):
                problems.append(
                    "the checks must NEVER rewrite the plan; `- Status: draft` is no longer on "
                    "disk, so a read-only check performed a lifecycle transition nobody approved"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if nudging_controls_broken:
            note = (
                " A NUDGING CONTROL ROW FAILED, so the rule is not firing at all; while that is "
                "true every SILENT row in this table is vacuous, because a rule that never fires "
                "satisfies them."
            )
        self.assertEqual(
            wrong,
            [],
            f"draft readiness mishandled {len(wrong)} of {len(self.DRAFTS)} drafts.{note} EVERY ROW "
            "exercises all three layers (the predicate, `check_ipd_draft_ready`, and "
            "`ipd lint --phase author`), so WHICH LAYER failed names the defect: the predicate alone "
            "means `_AUTHORING_PLACEHOLDERS` changed, the rule alone means its plan discovery or "
            "status filter changed, and LINT alone means the lint path has grown its own copy of "
            "the logic and the two have drifted. FIX: the prose-TODO row failing together with the "
            'placeholder rows is the signature of the predicate degrading to a bare `"TODO" in '
            "text`, which would call every plan in the repository a stub, since the canonical "
            f"checklist heading contains the word.\n" + "\n".join(wrong),
        )


if __name__ == "__main__":
    unittest.main()

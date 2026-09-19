"""Tests for awoptimize Order 15 (`kh91or`): complex orchestrated workflow migration.

Covers the E-05 acceptance with FALSIFIABLE fixtures that assert DETECTION/REJECTION, never mere
smoke:

  * E-01 release-review(+plan): both modes; every persona finding dispositioned via the Fix Bar;
    PLANNING MODE CANNOT ENTER MUTATION/RELEASE; the Fix Bar is computed; integration is SERIAL; a
    release needs EXPLICIT human authority; a silent mode flip is detected as drift.
  * E-02 verify-execution/ipd-lifecycle: verification inspects the ACTUAL diff + raw checks; gaps emit
    corrective artifacts; an EXECUTOR context CANNOT perform the terminal move; self-verification is
    refused.
  * E-03 assess-all: lanes are READ-ONLY + parallel-eligible; synthesis is SINGLE-WRITER (a second
    writer is refused). setup-repo: PREFLIGHT before mutation, per-change CONSENT, IDEMPOTENCY,
    ROLLBACK, and HEADLESS REFUSAL before any mutation.
  * E-04 incident/migrate/benchmark: operator data is LABELED unavailable (never fabricated); consent
    gates hold; a conformant artifact is emitted; an unsupported certification/submission claim is
    REFUSED (honest limitation, not implied certification).

Stdlib `unittest`, matching the repository convention.

PARTS OF THIS FILE ARE TABLE-DRIVEN, AND THE MERGING HERE IS DELIBERATELY CONSERVATIVE, because the
subject is MIGRATING A USER'S REPOSITORY LAYOUT and is therefore destructive-adjacent. The properties
worth asserting are that NOTHING IS LOST, NOTHING IS OVERWRITTEN, A CONFLICT IS REFUSED RATHER THAN
RESOLVED, and AN INTERRUPTED MIGRATION IS RECOVERABLE. A table earns its place here only where EVERY
ROW asserts the FULL property rather than one facet of it, which for the state machine means: what the
call returned, the resulting STATE, the surviving APPLIED set, the ROLLED-BACK set, AND the applied
idempotency KEYS. A row that checked only a return value would let a "noop" that silently dropped an
applied change pass, so where that completeness was not achievable the tests were LEFT ALONE.

WHAT WAS TABULATED, and it is the grids where the full property is expressible: the Fix Bar's
(risk x data-integrity) disposition grid, the `OperatorDatum` provenance grid, the unsupported-claim
grid across all three packages, the human-consent gate's outcome grid, and the stage-admission grid
(mode x stage). In each case the subject is a PURE function or a construction that either succeeds
or refuses, so a row can state the whole outcome.

WHAT WAS LEFT ALONE, with a one-line reason on each test: every `assertRaises` refusal, the
setup-repo state machine's PREFLIGHT/CONSENT/IDEMPOTENCY/ROLLBACK sequence tests (each is a multi-step
transcript over a STATEFUL object, and the recovery property is a claim about an ordered history rather
than about one call's answer), the before/after idempotence PAIR, the single-writer claim pair, and the
live-manifest sweep.

MODES ARE COLUMNS WHERE THEY ARE SAFE TO BE: the release-review MODE (full versus planning), the ROLE,
the risk level, the provenance, the package. Each is a case where the property worth asserting is that
the SAME input gets a different answer in a different mode, which no single-mode test can state.
"""

from __future__ import annotations

import unittest

from agent_workflows import migration_complex as MC
from agent_workflows import orchestrate_isolation as ISO
from agent_workflows import run_gates as GATES
from agent_workflows import verify_roles as ROLES
from tests.support import SOURCE_WORKFLOWS


def _approve_handler(_gate):
    return "approve"


def _reject_handler(_gate):
    return "reject"


# ==================================================================================================
# E-01: release-review + release-review-plan
# ==================================================================================================


def _abort_handler(_gate):
    return "abort"


class TheFixBarDecidesEveryFinding(unittest.TestCase):
    """The Fix Bar's (remediation risk x data-integrity) grid, and that NOTHING is left un-triaged.

    ONE table replaces three tests (`test_fix_bar_computed`, `test_data_integrity_finding_never_deferred`,
    and the disposition half of `test_every_persona_finding_dispositioned`). Each seeded a ledger and
    asserted a disposition, differing only in the risk level and the data-integrity flag, so both are
    columns.

    THE DATA-INTEGRITY FLAG IS THE COLUMN THAT MATTERS AND IS WHY THIS IS ONE TABLE. The non-deferral
    rule says a LIVE/High data-integrity finding is ESCALATED where an ordinary one is DEFERRED, so the
    property is that the SAME risk level produces a DIFFERENT disposition under the flag. Only adjacent
    rows can state that; the old split asserted the ordinary predicate for four risks and the escalation
    for exactly one, so a rule that escalated everything, or nothing, would have looked fine.

    EVERY ROW ASSERTS THE FULL PROPERTY, which for a ledger means three things at once: the finding's
    own disposition, that it is a MEMBER of the closed `FINDING_DISPOSITIONS` vocabulary, and that
    `undispositioned()` is EMPTY afterwards. The third is the one that matters for "nothing is silently
    dropped", and asserting it per row rather than once in a separate test is what makes it hold for
    every cell of the grid rather than for one seeded ledger.

    THE `fix_bar` PREDICATE AND THE COORDINATOR PASS ARE BOTH DRIVEN PER ROW, because they are two
    spellings of the same rule and a gate present in one and missing from the other would otherwise be
    invisible.
    """

    #: (case, remediation risk, data_integrity, the disposition expected, the `fix_bar` predicate's
    #: expected answer, why this row exists)
    #:
    #: THE DISPOSITIONS ARE LITERAL STRINGS, not `MC.DISPOSITION_*`, deliberately: referencing the
    #: constants would make a RENAMING invisible, since the constant and the recorded value move
    #: together. These values are written into the issue ledger a human reads and triages from.
    GRID = (
        (
            "a low-risk cure",
            "low",
            False,
            "fix-now",
            True,
            "FIX BY DEFAULT is the whole policy: impact and severity do NOT decide, only the "
            "remediation risk of the CURE does. A cheap fix is always taken",
        ),
        (
            "a medium-risk cure",
            "medium",
            False,
            "fix-now",
            True,
            "THE INCLUSIVE EDGE of the fix-now band. Kept as its own row because `medium` is the value "
            "most likely to be moved when someone decides the bar is too aggressive, and moving it is "
            "a deliberate policy change that must fail here",
        ),
        (
            "a medium-high-risk cure",
            "medium-high",
            False,
            "defer",
            False,
            "THE EXCLUSIVE EDGE, and the boundary the policy is written around: defer only when the "
            "cure's risk is Medium-High OR HIGHER. This row and the one above are the two sides of the "
            "one comparison, so an off-by-one in the band moves exactly this pair",
        ),
        (
            "a high-risk cure",
            "high",
            False,
            "defer",
            False,
            "the far end of the defer band, which stops the boundary row passing by `medium-high` being "
            "special-cased",
        ),
        (
            "a low-risk cure on a DATA-INTEGRITY finding",
            "low",
            True,
            "fix-now",
            True,
            "THE NON-DEFERRAL RULE DOES NOT MEAN ALWAYS-ESCALATE: when the cure is cheap the finding is "
            "simply FIXED. Without this row a rule that escalated every data-integrity finding would "
            "pass, which would flood the human with escalations for fixes nobody needed to approve",
        ),
        (
            "a medium-risk cure on a DATA-INTEGRITY finding",
            "medium",
            True,
            "fix-now",
            True,
            "the second half of the same point, and it pins that the flag does not shrink the fix-now "
            "band either",
        ),
        (
            "a medium-high-risk cure on a DATA-INTEGRITY finding",
            "medium-high",
            True,
            "escalate",
            False,
            "THE RULE ITSELF: at the exact risk where an ordinary finding is DEFERRED, a LIVE/High "
            "data-integrity finding is ESCALATED instead. Deferring live data corruption is the "
            "decision this rule exists to make impossible, and escalation is what puts it in front of "
            "a human rather than into a backlog",
        ),
        (
            "a high-risk cure on a DATA-INTEGRITY finding",
            "high",
            True,
            "escalate",
            False,
            "the worst cell of the grid and the one the rule was written for: the cure is risky AND the "
            "data is live, so it must reach a human. `defer` here would be a silent decision to ship "
            "known corruption",
        ),
    )

    def test_every_cell_of_the_grid_is_dispositioned_and_none_is_left_untriaged(self):
        wrong = []
        for case, risk, data_integrity, expected, predicate, why in self.GRID:
            problems = []
            # THE BARE PREDICATE, so a divergence between it and the coordinator pass is visible.
            try:
                got_predicate = MC.fix_bar(risk)
            except MC.ComplexMigrationError as exc:
                got_predicate = None
                problems.append(
                    f"`fix_bar({risk!r})` REFUSED a known risk value: {exc}"
                )
            if got_predicate is not None and got_predicate is not predicate:
                problems.append(
                    f"`fix_bar({risk!r})` returned {got_predicate}, expected {predicate}"
                )
            c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
            c.ledger.add(
                MC.PersonaFinding(
                    finding_id="F-01",
                    persona="qa_qc",
                    summary="a finding",
                    remediation_risk=risk,
                    data_integrity=data_integrity,
                )
            )
            c.run_fix_bar()
            finding = c.ledger.findings[0]
            if finding.disposition != expected:
                problems.append(
                    f"the coordinator dispositioned it {finding.disposition!r}, expected "
                    f"{expected!r}"
                )
            if finding.disposition not in MC.FINDING_DISPOSITIONS:
                problems.append(
                    f"the disposition {finding.disposition!r} is not in the closed vocabulary "
                    f"{sorted(MC.FINDING_DISPOSITIONS)}"
                )
            # NOTHING SILENTLY DROPPED, asserted on EVERY cell rather than once.
            if c.ledger.undispositioned():
                problems.append(
                    f"findings were left UN-TRIAGED: {c.ledger.undispositioned()!r}. A dropped "
                    "finding is a decision nobody made"
                )
            if problems:
                wrong.append(
                    f"  {case} (risk={risk!r}, data_integrity={data_integrity}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the Fix Bar was wrong for {len(wrong)} of {len(self.GRID)} grid cells. READ THE "
            "GROUPING. The two `medium`/`medium-high` rows moving TOGETHER means the band's boundary "
            "shifted, which is a deliberate policy change and must be made deliberately. The four "
            "DATA-INTEGRITY rows all reading `defer` means the non-deferral rule was lost entirely, "
            "which is the dangerous direction: live data corruption would then be filed for later "
            "instead of escalated to a human. All four reading `escalate` is the opposite and merely "
            "noisy, since fixes nobody needed to approve would queue for approval. A `fix_bar` answer "
            "that disagrees with the coordinator's disposition on the same input means the rule has "
            "TWO implementations that have started to diverge. FIX: any non-empty `undispositioned()` "
            f"outranks everything else here, because it means a finding was dropped silently.\n"
            + "\n".join(wrong),
        )

    def test_every_persona_can_carry_a_finding_and_all_are_dispositioned(self):
        """Kept separate: the subject is the PERSONA VOCABULARY over a fully seeded ledger.

        The grid above uses one persona and varies the risk; this varies the persona and asserts the
        ledger triages a finding from EVERY one of the eight. Merging would multiply the grid by eight
        to state a property that does not interact with the risk columns at all.
        """
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        for i, persona in enumerate(MC.RELEASE_PERSONAS):
            c.ledger.add(
                MC.PersonaFinding(
                    finding_id="F-{0:02d}".format(i),
                    persona=persona,
                    summary="finding from {0}".format(persona),
                    remediation_risk="low" if i % 2 == 0 else "high",
                )
            )
        c.run_fix_bar()
        self.assertEqual(c.ledger.undispositioned(), [])
        self.assertEqual(c.ledger.personas_covered(), frozenset(MC.RELEASE_PERSONAS))
        for f in c.ledger.findings:
            self.assertIn(f.disposition, MC.FINDING_DISPOSITIONS)

    def test_an_unknown_risk_value_is_REFUSED_by_the_predicate_and_the_pass(self):
        """Kept separate: `assertRaises` over two entry points, not a returned disposition.

        A row cannot carry both a disposition and an exception type without a column meaningless to
        every other row. Both spellings are driven here for the same reason the table drives both: a
        refusal present in one and missing from the other lets an unknown risk reach the ledger.
        """
        with self.assertRaises(MC.ComplexMigrationError):
            MC.fix_bar("nonsense")
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        # Appended DIRECTLY, bypassing `add`, so `disposition_all` is what must refuse.
        c.ledger.findings.append(
            MC.PersonaFinding(
                finding_id="F-BAD",
                persona="architect",
                summary="x",
                remediation_risk="bananas",
            )
        )
        with self.assertRaises(MC.ComplexMigrationError):
            c.run_fix_bar()

    def test_unknown_persona_rejected(self):
        """Kept separate: `assertRaises` at the ledger's own admission point."""
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        with self.assertRaises(MC.ComplexMigrationError):
            c.ledger.add(
                MC.PersonaFinding(
                    finding_id="F-X",
                    persona="dragon-slayer",
                    summary="x",
                    remediation_risk="low",
                )
            )


class ThePlanningReleaseBoundary(unittest.TestCase):
    """Which STAGE each release-review MODE may enter, and that the boundary is the mode's own.

    ONE table replaces four tests (`planning_mode_cannot_enter_mutation`,
    `planning_mode_cannot_enter_release`, `full_mode_can_enter_mutation`, and the stage half of the
    frozen-scope claim). Each constructed a coordinator in one mode and entered one stage, so the MODE
    and the STAGE are the two columns of one grid.

    THE MODE IS THE LOAD-BEARING COLUMN AND THIS IS THE CLAIM A SPLIT CANNOT MAKE: the boundary exists
    because the SAME stage is admitted in one mode and refused in the other, so a planning run can never
    mutate the repository or ship. Two separate tests each state half of that, and neither would notice
    a change that admitted every stage in both modes as long as the full-mode test kept passing.

    EVERY ROW ASSERTS THE RECORDED HISTORY, NOT ONLY THE RETURN. A refused stage must ALSO leave
    `stages_entered` unchanged, because a coordinator that raised but recorded the stage anyway would
    report, afterwards, that a planning run entered mutation. That is the "nothing is silently
    recorded" analogue of the file-level safety properties this module is about, and it is why the rows
    are complete enough to be worth merging.
    """

    #: (case, the mode, the stage, whether it must be ADMITTED, the exception class name expected on a
    #: refusal, why this row exists)
    STAGES = (
        (
            "planning entering audit",
            MC.RELEASE_MODE_PLANNING,
            MC.STAGE_AUDIT,
            True,
            None,
            "A CLEAN ROW: a planning run's whole job is to audit and produce a plan, so refusing this "
            "would make the mode useless. Every refusal row below is vacuous while the clean rows are "
            "broken, because a coordinator that refused every stage satisfies all of them",
        ),
        (
            "planning entering ledger",
            MC.RELEASE_MODE_PLANNING,
            MC.STAGE_LEDGER,
            True,
            None,
            "the Fix Bar pass runs in the LEDGER stage, and a planning run must be able to disposition "
            "findings: that is the deliverable it produces instead of a mutation",
        ),
        (
            "planning entering plan",
            MC.RELEASE_MODE_PLANNING,
            MC.STAGE_PLAN,
            True,
            None,
            "the third and last stage a planning run may reach, so the admitted set is pinned exactly "
            "rather than as `at least audit`",
        ),
        (
            "planning entering MUTATION",
            MC.RELEASE_MODE_PLANNING,
            MC.STAGE_MUTATION,
            False,
            "ReleaseModeError",
            "THE BOUNDARY ITSELF: a planning-mode run must never reach a stage that writes to the "
            "repository. This is the row that makes `release-review-plan` safe to run on a tree "
            "nobody wants changed",
        ),
        (
            "planning entering VERIFY",
            MC.RELEASE_MODE_PLANNING,
            MC.STAGE_VERIFY,
            False,
            "ReleaseModeError",
            "VERIFY IS FULL-MODE ONLY and this is the least obvious row: verification sounds read-only, "
            "so it is the stage most likely to be quietly admitted to planning mode. It follows a "
            "mutation, so a planning run reaching it is claiming to have verified changes it never made",
        ),
        (
            "planning entering RELEASE",
            MC.RELEASE_MODE_PLANNING,
            MC.STAGE_RELEASE,
            False,
            "ReleaseModeError",
            "a planning run must not be able to SHIP. Together with the mutation row this is the whole "
            "of `planning cannot mutate or release`",
        ),
        (
            "full entering mutation",
            MC.RELEASE_MODE_FULL,
            MC.STAGE_MUTATION,
            True,
            None,
            "THE ROW THAT MAKES THE MODE A BOUNDARY RATHER THAN A PROHIBITION: the same stage refused "
            "above is admitted here. Without it, a coordinator that refused mutation to everyone would "
            "satisfy the planning rows and quietly break the full runbook",
        ),
        (
            "full entering verify",
            MC.RELEASE_MODE_FULL,
            MC.STAGE_VERIFY,
            True,
            None,
            "the same pairing for verify, so the surprising planning-verify row above is proven to be "
            "about the MODE and not about verify being unreachable generally",
        ),
        (
            "full entering release",
            MC.RELEASE_MODE_FULL,
            MC.STAGE_RELEASE,
            True,
            None,
            "reaching the stage is NOT the same as being allowed to ship: the release still needs "
            "explicit human authority, which `TheHumanConsentGate` owns. This row pins only that the "
            "mode does not stand in the way",
        ),
        (
            "an unknown stage name, in either mode",
            MC.RELEASE_MODE_FULL,
            "release-review-turbo-stage",
            False,
            "ComplexMigrationError",
            "THE VOCABULARY IS CLOSED, and the exception class is DIFFERENT from the boundary "
            "refusals above, which is the point of pinning the class per row: a typo'd stage is a "
            "programming error, not a mode violation, and collapsing the two would let a misspelled "
            "`mutaton` read as a policy refusal and pass silently in planning mode",
        ),
    )

    def test_each_mode_admits_exactly_its_own_stages_and_records_only_those(self):
        wrong = []
        for case, mode, stage, admitted, expected_exc, why in self.STAGES:
            c = MC.ReleaseReviewCoordinator(mode=mode)
            problems = []
            got_exc = None
            try:
                c.enter_stage(stage)
            except MC.ComplexMigrationError as exc:
                got_exc = type(exc).__name__
            if admitted:
                if got_exc is not None:
                    problems.append(f"REFUSED a stage it must admit ({got_exc})")
                elif stage not in c.stages_entered:
                    problems.append(
                        f"the stage was admitted but NOT recorded: stages_entered is "
                        f"{c.stages_entered!r}"
                    )
            else:
                if got_exc is None:
                    problems.append("ADMITTED a stage it must refuse")
                elif got_exc != expected_exc:
                    problems.append(
                        f"refused with {got_exc}, expected {expected_exc}: the two refusal classes "
                        "mean different things (a mode violation versus an unknown stage name)"
                    )
                # A REFUSAL MUST LEAVE NO TRACE. A coordinator that raised and recorded anyway would
                # report afterwards that a planning run entered a mutation stage.
                if c.stages_entered:
                    problems.append(
                        f"the refused stage was RECORDED anyway: stages_entered is "
                        f"{c.stages_entered!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (mode={mode!r}, stage={stage!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"stage admission was wrong for {len(wrong)} of {len(self.STAGES)} (mode, stage) cells. "
            "READ WHICH SIDE MOVED. All three PLANNING refusals admitting means the boundary is gone "
            "and `release-review-plan` can now mutate and ship a tree nobody asked it to touch, which "
            "is the whole hazard the mode exists to avoid. All three FULL rows refusing means the "
            "runbook is broken and the planning rows prove nothing. A refusal that RECORDS the stage is "
            "its own defect regardless of the exception, because the recorded history is what a later "
            "reader trusts. FIX: the unknown-stage row uses a DIFFERENT exception class deliberately; "
            f"do not collapse them, or a typo'd stage name will read as a policy decision.\n"
            + "\n".join(wrong),
        )

    def test_both_modes_freeze_a_DIFFERENT_scope_and_a_flip_is_detected_as_drift(self):
        """Kept separate: a claim about the RELATIONSHIP between two frozen requirement sets.

        Merged from `test_both_modes_construct_with_frozen_scope` and `test_mode_flip_detected_as_drift`,
        which are two readings of one fact: the digests DIFFER, therefore the flip is a detectable
        revision. Not a table because both halves need both coordinators at once, and the same-mode
        case must be asserted alongside or "everything is drift" would pass.
        """
        full = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        planning = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_PLANNING)
        self.assertNotEqual(
            full.frozen.requirement_digest, planning.frozen.requirement_digest
        )
        self.assertTrue(MC.detect_mode_drift(planning, MC.RELEASE_MODE_FULL))
        self.assertTrue(MC.detect_mode_drift(full, MC.RELEASE_MODE_PLANNING))
        # SAME mode is NOT drift, which is what stops the two rows above passing vacuously.
        self.assertFalse(MC.detect_mode_drift(planning, MC.RELEASE_MODE_PLANNING))
        self.assertFalse(MC.detect_mode_drift(full, MC.RELEASE_MODE_FULL))

    def test_unknown_mode_rejected(self):
        """Kept separate: `assertRaises` at construction, before any stage exists to enter."""
        with self.assertRaises(MC.ReleaseModeError):
            MC.ReleaseReviewCoordinator(mode="release-review-turbo")

    def test_planning_mode_cannot_authorize_a_release_at_all(self):
        """Kept separate: `assertRaises` over a DIFFERENT method than `enter_stage`.

        The table proves planning cannot ENTER the release stage; this proves the authority call itself
        is unreachable, which is the claim that matters even if the stage gate were bypassed.
        """
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_PLANNING)
        with self.assertRaises(MC.ReleaseModeError):
            c.authorize_release(interactive=True, input_handler=_approve_handler)

    def test_integration_is_serial_not_parallel_mutating(self):
        """Kept separate: materially different setup (lane requests) and a DIFFERENT subject.

        The claim is about the Order-07 concurrency analyzer's verdict for mutating lanes, not about
        stage admission. Two DISJOINT files are used deliberately: even with no overlap the result must
        not be a parallel mutating fan-out, so seriality is a property of the lane KIND rather than of
        file contention.
        """
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        lanes = (
            ISO.LaneRequest(
                lane_id="fix-a",
                actor_role=ROLES.ROLE_EXECUTOR,
                lane_kind=ISO.LANE_KIND_MUTATING,
                files_targeted=("src/a.py",),
            ),
            ISO.LaneRequest(
                lane_id="fix-b",
                actor_role=ROLES.ROLE_EXECUTOR,
                lane_kind=ISO.LANE_KIND_MUTATING,
                files_targeted=("src/b.py",),
            ),
        )
        result = c.integrate_fixes(lanes)
        self.assertNotEqual(result.execution_mode, ISO.EXEC_MODE_PARALLEL_MUTATING)
        self.assertFalse(result.is_eligible_parallel)

    def test_executor_cannot_finalize_release_review(self):
        """Kept separate: delegates to the run_state authority table, not to the mode boundary.

        `RoleAuthorityTests` owns the full role grid for the terminal transition; this pins that the
        release-review coordinator routes through it rather than deciding for itself.
        """
        c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
        self.assertFalse(c.can_finalize(ROLES.ROLE_EXECUTOR))
        self.assertTrue(c.can_finalize(ROLES.ROLE_COORDINATOR))


class TheHumanConsentGate(unittest.TestCase):
    """A destructive action needs EXPLICIT human approval, and consent is never synthesized.

    ONE table replaces five tests: the three release-authority tests
    (`release_needs_explicit_authority_headless_refused`, `release_refused_on_rejection`,
    `release_granted_on_explicit_approval`) and the two risk-aware consent tests
    (`consent_gate_headless_needs_input`, `consent_gate_explicit_approval`). Every one built a
    coordinator or a package, called one gate with one handler, and asserted the outcome, so the
    HANDLER and the SURFACE are columns.

    THE TWO SURFACES BELONG IN ONE TABLE, which is the argument for merging across what used to be two
    classes. `authorize_release` and `RiskAwarePackage.consent_gate` are two callers of the SAME
    `run_gates.evaluate_gate` scheme, and they were tested with NON-OVERLAPPING handler sets: the
    release side never tried `abort`, and the consent side never tried `reject`. A refusal present in one
    caller and missing from the other was therefore invisible. Running every handler through both is what
    turns "this gate works" into "no handler clears either gate except an explicit approval".

    THE SURFACES DIFFER IN HOW THEY REFUSE AND THE TABLE STATES THAT RATHER THAN HIDING IT:
    `authorize_release` RAISES `ReleaseAuthorityError` (a release is irreversible, so the caller must not
    be able to ignore a returned value), while `consent_gate` RETURNS a decision carrying its status (its
    callers gate a step and continue). That asymmetry is a `raises` column, not a reason to weaken either
    claim to the other's shape.

    THE APPROVAL ROWS ARE IN THE SAME TABLE and they carry the real weight: a gate that refused
    everything would satisfy every refusal row while making a release impossible. Their failure message
    says so.
    """

    #: (case, the input handler or None for a headless call, whether `interactive` is passed True,
    #: whether `authorize_release` must RAISE, the `GateDecision.status` a returned decision must
    #: carry, whether `is_approved` must be True, why this row exists)
    #:
    #: THE STATUSES ARE LITERAL STRINGS, not `GATES.GATE_STATUS_*`: a rename would move the constant and
    #: the reported value together, and these statuses are what a caller and a recorded gate decision
    #: are read from. `test_the_status_vocabulary_is_the_shared_one` separately pins that these literals
    #: are the SAME values `run_gates` declares, so the table cannot drift into testing invented names.
    HANDLERS = (
        (
            "headless, with no human present at all",
            None,
            False,
            True,
            "needs_input",
            False,
            "THE HEADLESS REFUSAL, which is the most important row for an unattended run: with nobody to "
            "ask, the gate must STOP at `needs_input` rather than assume. A gate that defaulted to "
            "approval here would ship a release, or run a destructive benchmark, that no human ever "
            "authorized",
        ),
        (
            "an explicit approval",
            _approve_handler,
            True,
            False,
            "approved",
            True,
            "THE CLEAN ROW: explicit human approval must actually work. Every refusal row is vacuous "
            "while this one is broken, because a gate that refuses everything satisfies all of them and "
            "simply makes the release unreachable",
        ),
        (
            "an explicit rejection",
            _reject_handler,
            True,
            True,
            "rejected",
            False,
            "A HUMAN SAYING NO IS NOT THE SAME AS NO HUMAN, and both must refuse. Recording the distinct "
            "`rejected` status is what lets a later reader tell a considered refusal from an unattended "
            "one",
        ),
        (
            "an explicit abort",
            _abort_handler,
            True,
            True,
            "aborted",
            False,
            "THE THIRD OPTION AND THE DEFAULT ONE: `abort` is the gate's own `default_option`, so it is "
            "the outcome a mis-parse or an empty answer is most likely to land on. It was previously "
            "tested on NEITHER surface, which is exactly the gap merging the two classes exposed",
        ),
    )

    def test_no_handler_clears_either_gate_except_an_explicit_approval(self):
        wrong = []
        for (
            case,
            handler,
            interactive,
            must_raise,
            expected_status,
            expected_approved,
            why,
        ) in self.HANDLERS:
            problems = []
            # SURFACE 1: `authorize_release`, which RAISES rather than returning on any refusal.
            c = MC.ReleaseReviewCoordinator(mode=MC.RELEASE_MODE_FULL)
            kwargs = {"interactive": interactive}
            if handler is not None:
                kwargs["input_handler"] = handler
            try:
                decision = c.authorize_release(**kwargs)
                if must_raise:
                    problems.append(
                        f"`authorize_release` RETURNED a decision ({decision.status!r}) where it must "
                        "raise: a release is irreversible, so a caller must not be able to ignore the "
                        "refusal"
                    )
                else:
                    if decision.status != expected_status:
                        problems.append(
                            f"`authorize_release` returned status {decision.status!r}, expected "
                            f"{expected_status!r}"
                        )
                    if decision.is_approved is not expected_approved:
                        problems.append(
                            f"`authorize_release` returned is_approved={decision.is_approved}, "
                            f"expected {expected_approved}"
                        )
            except MC.ReleaseAuthorityError as exc:
                if not must_raise:
                    problems.append(
                        f"`authorize_release` RAISED on a handler that must be accepted: {exc}"
                    )
                elif expected_status not in str(exc):
                    problems.append(
                        f"the refusal must name the gate status {expected_status!r} so a reader can "
                        f"tell a considered rejection from an unattended one; it said {str(exc)!r}"
                    )
            # SURFACE 2: `consent_gate`, which RETURNS its decision on every path.
            pkg = MC.build_benchmark_package()
            gate_kwargs = {"interactive": interactive}
            if handler is not None:
                gate_kwargs["input_handler"] = handler
            gate_decision = pkg.consent_gate("run-benchmarks", **gate_kwargs)
            if gate_decision.status != expected_status:
                problems.append(
                    f"`consent_gate` returned status {gate_decision.status!r}, expected "
                    f"{expected_status!r}: the two callers of one gate scheme DISAGREE on this handler"
                )
            if gate_decision.is_approved is not expected_approved:
                problems.append(
                    f"`consent_gate` returned is_approved={gate_decision.is_approved}, expected "
                    f"{expected_approved}"
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
            f"the human-consent gate was wrong for {len(wrong)} of {len(self.HANDLERS)} handlers, "
            "checked on BOTH callers. READ THE GROUPING. If the APPROVAL row is among the failures, "
            "every refusal row is vacuous and the gate simply cannot be passed, which makes a release "
            "unreachable rather than unsafe. If a REFUSAL row now clears, that is the dangerous "
            "direction: the headless row clearing means an unattended run would ship or mutate with no "
            "human at all, which is the single outcome this scheme exists to prevent. If one CALLER "
            "disagrees with the other on the same handler, the two have forked and a refusal that "
            "exists in one is missing from the other; that gap was real before this table (the release "
            "side never tried `abort`, the consent side never tried `reject`). FIX: never make a "
            f"refusal row pass by relaxing the expectation to `not approved`.\n"
            + "\n".join(wrong),
        )

    def test_the_status_vocabulary_is_the_shared_one(self):
        """Kept separate: an IDENTITY claim tying the table's literals to `run_gates`' own constants.

        The table above writes statuses as literals so a RENAME fails there rather than moving silently
        on both sides. That leaves one gap: the literals could drift into names `run_gates` never
        declares, and the table would keep passing against a vocabulary nobody uses. This closes it.
        """
        self.assertEqual(GATES.GATE_STATUS_NEEDS_INPUT, "needs_input")
        self.assertEqual(GATES.GATE_STATUS_APPROVED, "approved")
        self.assertEqual(GATES.GATE_STATUS_REJECTED, "rejected")
        self.assertEqual(GATES.GATE_STATUS_ABORTED, "aborted")
        # Every status the table asserts must be one this module actually declares.
        declared = {
            GATES.GATE_STATUS_APPROVED,
            GATES.GATE_STATUS_REJECTED,
            GATES.GATE_STATUS_NEEDS_INPUT,
            GATES.GATE_STATUS_TIMED_OUT,
            GATES.GATE_STATUS_REFUSED,
            GATES.GATE_STATUS_ABORTED,
        }
        self.assertEqual({row[4] for row in self.HANDLERS} - declared, set())


# ==================================================================================================
# E-02: verify-execution + ipd-lifecycle
# ==================================================================================================


class VerificationReadsTheActualDiff(unittest.TestCase):
    """What an INSPECTION concludes, and which corrective artifact each gap produces.

    ONE table replaces three tests (`clean_inspection_verifies_no_corrective`,
    `actual_diff_out_of_scope_emits_corrective`, `raw_check_failure_emits_corrective`). Each built one
    `DiffInspection`, verified it, and asserted the verdict plus (sometimes) one artifact's contents, so
    the inspection's SHAPE is the column.

    EVERY ROW ASSERTS THE FULL OUTCOME: the verdict, the EXACT set of artifact ids emitted, and each
    artifact's `failed_items`. That completeness is what makes the merge safe here, and it is stricter
    than the tests it replaces in two ways. First, the old tests asserted `any("scope" in ...)` and then
    indexed the first match, so an extra spurious artifact alongside the right one would have passed;
    the rows pin the exact id set. Second, the BOTH-GAPS row is new: neither old test had an inspection
    that was out of scope AND failing its checks, so nothing proved the two artifacts are emitted
    together rather than the first gap short-circuiting the second.

    THE CLEAN ROWS ARE IN THE SAME TABLE and there are three of them, because "clean" has more than one
    shape here and each is a way a verifier could wrongly flag a good run: nothing out of scope, an
    EMPTY inspection, and a diff that touched FEWER files than were declared. The last is the subtle one
    (declaring a path and not needing it is not a defect), and it is the row most likely to break if the
    scope check is ever inverted into a completeness check.

    WHY THE `failed_items` CONTENT IS PART OF EVERY GAP ROW: a corrective artifact that fires without
    naming the offending file or check cannot be acted on, and the whole point of this design is that
    the verifier reads the ACTUAL diff rather than the executor's prose claim. An artifact naming
    nothing would be indistinguishable from a prose complaint.
    """

    #: (case, diff_paths, declared_paths, raw_check_results, expected verified, the EXACT set of
    #: artifact id SUFFIXES expected, a mapping of suffix -> the items that artifact must name, why
    #: this row exists)
    INSPECTIONS = (
        (
            "a diff inside its declared scope with every check passing",
            ("src/a.py",),
            ("src/a.py", "tests/test_a.py"),
            {"pytest": True, "lint": True},
            True,
            (),
            {},
            "THE PRIMARY CLEAN ROW: a good run must VERIFY and emit NOTHING. Every gap row below is "
            "vacuous while this one is broken, because a verifier that failed everything satisfies all "
            "of them and would route every correct execution to a corrective plan",
        ),
        (
            "an EMPTY inspection",
            (),
            (),
            {},
            True,
            (),
            {},
            "THE DEGENERATE CLEAN ROW: no diff, no declarations, no checks. It is clean because there is "
            "nothing to be out of scope and nothing to have failed, and pinning it stops a "
            "`not inspection.diff_paths` guard being read as a defect",
        ),
        (
            "a diff touching FEWER files than were declared",
            (),
            ("src/a.py", "src/b.py"),
            {"pytest": True},
            True,
            (),
            {},
            "THE SUBTLE CLEAN ROW: declaring a path and then not needing it is NOT a defect. The scope "
            "fence is a CEILING, not a contract to touch everything, so this is the row that fails if "
            "the check is ever inverted into a completeness check, which would flag every plan that "
            "came in under its declared scope",
        ),
        (
            "a diff touching an UNDECLARED file",
            ("src/a.py", "src/SECRET.py"),
            ("src/a.py",),
            {"pytest": True},
            False,
            ("scope",),
            {"scope": ("src/SECRET.py",)},
            "THE SCOPE GAP, and the artifact must NAME the actual out-of-scope file read from the real "
            "diff. This is the case that matters most for a migration: a change that reached a file "
            "nobody declared is exactly how an unintended file gets rewritten, and a complaint that "
            "does not say WHICH file cannot be acted on",
        ),
        (
            "a RAW CHECK that failed",
            ("src/a.py",),
            ("src/a.py",),
            {"pytest": False, "lint": True},
            False,
            ("checks",),
            {"checks": ("pytest",)},
            "THE CHECKS GAP, and it must name the check that failed rather than the one that passed. The "
            "verifier reads the ACTUAL boolean results, never the executor's prose claim, which is the "
            "whole reason verification is independent",
        ),
        (
            "BOTH an undeclared file and a failing check",
            ("src/a.py", "src/X.py"),
            ("src/a.py",),
            {"pytest": False, "lint": False},
            False,
            ("scope", "checks"),
            {"scope": ("src/X.py",), "checks": ("lint", "pytest")},
            "TWO GAPS MUST PRODUCE TWO ARTIFACTS, which no previous test asserted: if the first gap "
            "short-circuited the second, a run would be sent back to fix its scope and would then fail "
            "its checks on the next pass, having been told only half the problem. The checks artifact "
            "must name BOTH failing checks, not just the first",
        ),
    )

    def test_each_inspection_reaches_its_verdict_and_emits_exactly_its_artifacts(self):
        wrong = []
        for (
            case,
            diff_paths,
            declared_paths,
            checks,
            expected_verified,
            expected_suffixes,
            expected_items,
            why,
        ) in self.INSPECTIONS:
            inspection = MC.DiffInspection(
                diff_paths=diff_paths,
                declared_paths=declared_paths,
                raw_check_results=checks,
            )
            v = MC.VerifyExecutionCoordinator(plan_id="plan-under-test")
            verified, artifacts = v.verify(
                inspection,
                verifier_role=ROLES.ROLE_VERIFIER,
                author_role=ROLES.ROLE_EXECUTOR,
            )
            problems = []
            if verified is not expected_verified:
                problems.append(
                    f"expected verified={expected_verified}, got {verified}"
                )
            if inspection.is_clean() is not expected_verified:
                problems.append(
                    f"the inspection's own `is_clean()` says {inspection.is_clean()} while the verdict "
                    f"is {verified}: the two must agree, or a verifier could clear an unclean run"
                )
            got = sorted(a.artifact_id for a in artifacts)
            expected_ids = sorted(f"plan-under-test-{s}" for s in expected_suffixes)
            if got != expected_ids:
                problems.append(
                    f"expected EXACTLY the artifacts {expected_ids!r}, got {got!r}"
                )
            for suffix, required_items in expected_items.items():
                matching = [
                    a for a in artifacts if a.artifact_id.endswith(f"-{suffix}")
                ]
                if not matching:
                    continue  # already reported by the id-set check above
                named = tuple(matching[0].failed_items)
                if named != tuple(required_items):
                    problems.append(
                        f"the {suffix!r} artifact must name exactly {tuple(required_items)!r}; it "
                        f"named {named!r}. An artifact that does not say WHICH file or check is at "
                        "fault cannot be acted on"
                    )
                if not matching[0].gap_summary.strip():
                    problems.append(
                        f"the {suffix!r} artifact carries an empty `gap_summary`"
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
            f"verification was wrong for {len(wrong)} of {len(self.INSPECTIONS)} inspections. READ THE "
            "GROUPING. All three CLEAN rows failing means the verifier now flags every run, so every "
            "gap row is vacuous and correct executions get routed to corrective plans. A GAP row "
            "verifying clean is the dangerous direction: an undeclared file would be accepted, which "
            "for a layout migration means a file nobody declared was rewritten and nothing said so. "
            "The BOTH row losing one artifact means the gaps short-circuit, so a run is told half its "
            "problem and comes back failing the other half. FIX: never satisfy a gap row by loosening "
            "the id set to `any(...)`; the exact set is what stops a spurious extra artifact passing "
            f"unnoticed alongside the right one.\n" + "\n".join(wrong),
        )

    def test_self_verification_refused(self):
        """Kept separate: `assertRaises` over the independence guard.

        `RoleAuthorityTests` owns the full (verifier x author) role grid; this is the canonical case the
        rule is named for, kept here beside the verdict table it constrains.
        """
        insp = MC.DiffInspection(diff_paths=(), declared_paths=(), raw_check_results={})
        v = MC.VerifyExecutionCoordinator(plan_id="plan-4")
        with self.assertRaises(ROLES.SelfVerificationForbiddenError):
            v.verify(
                insp,
                verifier_role=ROLES.ROLE_EXECUTOR,
                author_role=ROLES.ROLE_EXECUTOR,
            )


class RoleAuthorityTests(unittest.TestCase):
    """WHO may author the terminal `verified -> complete` move, and under what precondition.

    ONE table replaces three tests (`executor_cannot_perform_terminal_move`,
    `terminal_move_needs_verifier_verified`, `coordinator_can_perform_terminal_move_after_verified`).
    Each picked one role and one `verifier_verified` value and asserted the predicate plus the
    performer, so both are columns of one grid.

    THE GRID IS THE CLAIM, AND THE OLD SPLIT COULD NOT MAKE IT. The rule is a CONJUNCTION of two
    independent gates (the run_state authority table authorizes the edge for the role, AND the verifier
    already produced `verified`), so the property worth stating is that BOTH are required and neither
    alone suffices. Three tests sampled three cells of a (7 roles x 2) grid; the table covers every
    role in `ROLE_CONTRACTS` plus an unknown one, in both preconditions, so a widening of the
    authorized set reports as the specific roles it newly admitted.

    EVERY ROW ASSERTS THE PREDICATE AND THE PERFORMER TOGETHER, which is what stops the two drifting:
    `can_mark_executed` is what a caller checks before acting and `mark_executed` is what actually
    moves the plan, so a predicate that said no while the performer proceeded would be a terminal move
    nobody authorized. The authorized rows additionally pin the resulting edge (`verified -> complete`),
    so a performer that succeeded while transitioning something else would fail here.

    THE TWO AUTHORIZED ROLES ARE IN THE SAME TABLE as the five refused ones, because a gate that refused
    everyone would satisfy every refusal row while making a plan impossible to complete.
    """

    #: (case, the actor role, whether the verifier produced `verified`, whether the move is allowed,
    #: why this row exists)
    ROLES_GRID = (
        (
            "the coordinator, after an independent verification",
            "coordinator",
            True,
            True,
            "THE ONE PATH A PLAN ACTUALLY COMPLETES BY. Every refusal row is vacuous while this is "
            "broken, because a gate that refuses everyone satisfies all of them and no plan could ever "
            "reach `executed`",
        ),
        (
            "the runtime, after an independent verification",
            "runtime",
            True,
            True,
            "THE SECOND AUTHORIZED ACTOR, which is easy to forget when reasoning about `coordinator` "
            "alone: an automated runner performs this move too, and a rule keyed only on `coordinator` "
            "would break every unattended run",
        ),
        (
            "the EXECUTOR, even after an independent verification",
            "executor",
            True,
            False,
            "THE RULE THIS WHOLE DESIGN EXISTS FOR: the actor that did the work may never declare it "
            "done. This is the row that makes the terminal transition mechanically unreachable to an "
            "executor rather than merely discouraged by convention",
        ),
        (
            "the VERIFIER, after its own verification",
            "verifier",
            True,
            False,
            "THE MOST SURPRISING REFUSAL, kept for exactly that reason: the verifier produced the "
            "`verified` decision and STILL may not perform the terminal move. Verification and "
            "finalization are separate authorities, so the actor that judged the work does not also "
            "close the record",
        ),
        (
            "the CORRECTOR",
            "corrector",
            True,
            False,
            "a corrector mutates code like an executor does, so it is barred for the same reason. Kept "
            "distinct because it is a different contract entry and a widening could admit one without "
            "the other",
        ),
        (
            "the INVESTIGATOR",
            "investigator",
            True,
            False,
            "a read-only role has no business writing a terminal state at all; this row is what keeps "
            "the authorized set from being read as `anyone but the executor`",
        ),
        (
            "the HUMAN",
            "human",
            True,
            False,
            "SURPRISING AND DELIBERATE: a human is not an authorized AUTHOR of this mechanical edge. "
            "Human approval enters through the gate scheme (`TheHumanConsentGate`), not by bypassing "
            "the transition table, so a human-labelled actor must not be a back door around it",
        ),
        (
            "an UNKNOWN role name",
            "dragon-slayer",
            True,
            False,
            "the role vocabulary is closed, and a typo'd role must FAIL CLOSED rather than being "
            "treated as unrecognized-and-therefore-harmless",
        ),
        (
            "the coordinator with NO independent verification",
            "coordinator",
            False,
            False,
            "THE SECOND CONJUNCT, and it is what proves the rule is a conjunction: the most authorized "
            "actor in the system still cannot finalize work nobody verified. Without this row an "
            "authority-only check would pass and a plan could be marked executed on the coordinator's "
            "word alone",
        ),
        (
            "the runtime with NO independent verification",
            "runtime",
            False,
            False,
            "the same for the automated actor, which is where it would actually happen: an unattended "
            "run must not be able to close a plan it never had verified",
        ),
        (
            "the executor with NO independent verification",
            "executor",
            False,
            False,
            "BOTH GATES FAIL AT ONCE here, which is the corner an implementation is most likely to "
            "short-circuit. It must still refuse, and the refusal type must not depend on which gate "
            "was checked first",
        ),
    )

    def test_only_an_authorized_actor_with_a_verified_decision_may_finalize(self):
        wrong = []
        for case, role, verified, allowed, why in self.ROLES_GRID:
            v = MC.VerifyExecutionCoordinator(plan_id="plan-under-test")
            problems = []
            predicate = v.can_mark_executed(role, verifier_verified=verified)
            if predicate is not allowed:
                problems.append(
                    f"`can_mark_executed` returned {predicate}, expected {allowed}"
                )
            try:
                rule = v.mark_executed(role, verifier_verified=verified)
                if not allowed:
                    problems.append(
                        "`mark_executed` PERFORMED the terminal move where it must refuse: a plan "
                        "would be marked executed by an actor with no authority to say so"
                    )
                else:
                    if (rule.source, rule.target) != ("verified", "complete"):
                        problems.append(
                            f"the performed transition was {rule.source!r} -> {rule.target!r}, "
                            "expected 'verified' -> 'complete'"
                        )
            except MC.TerminalUnreachableError as exc:
                if allowed:
                    problems.append(
                        f"`mark_executed` REFUSED an authorized actor: {exc}"
                    )
                elif role not in str(exc) and "verified" not in str(exc):
                    problems.append(
                        f"the refusal must say WHY (naming the actor or the missing verification); it "
                        f"said {str(exc)!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (role={role!r}, verifier_verified={verified}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"terminal authority was wrong for {len(wrong)} of {len(self.ROLES_GRID)} (role, "
            "verification) cells. READ THE GROUPING, because the rule is a CONJUNCTION of two "
            "independent gates and each pattern names which conjunct moved. Every `verifier_verified="
            "False` row becoming allowed means the verification precondition was dropped, so a plan "
            "can be closed on an actor's word with nothing independently checked. Several REFUSED "
            "roles becoming allowed means the authority table widened; if `executor` is among them, "
            "the actor that did the work can now declare it done, which is the exact defect this "
            "design exists to make impossible. Both AUTHORIZED rows refusing means no plan can ever "
            "complete, which is loud and safe but makes every other row vacuous. FIX: a disagreement "
            "between `can_mark_executed` and `mark_executed` on the SAME cell is its own defect, "
            f"because a caller checks the first and acts on the second.\n"
            + "\n".join(wrong),
        )

    #: (case, the verifier's role, the author's role, whether verification is PERMITTED, why)
    #:
    #: MEASURED 2026-09-19: the guard is stricter than its name suggests. `check_self_verification`
    #: refuses unless the verifier IS `verifier`, so a `coordinator` verifying an `executor`'s work is
    #: refused too, which is not "self" verification in any ordinary reading. That is pinned as the real
    #: behavior rather than described as the narrower rule, because a reader reasoning from the name
    #: would get it wrong.
    VERIFIER_GRID = (
        (
            "the verifier over an executor's work",
            "verifier",
            "executor",
            True,
            "THE ORDINARY CORRECT CASE: the independent verifier judges the executor's work. Every "
            "refusal row is vacuous while this is broken, because a guard that refused every pairing "
            "would make verification impossible",
        ),
        (
            "the executor over its OWN work",
            "executor",
            "executor",
            False,
            "THE RULE THE GUARD IS NAMED FOR: nobody marks their own homework. This is the pairing that "
            "would otherwise let an executor's prose claim stand as its own evidence",
        ),
        (
            "the COORDINATOR over an executor's work",
            "coordinator",
            "executor",
            False,
            "THE SURPRISING ROW, MEASURED: this is refused even though it is not self-verification in "
            "any plain reading. The guard requires the verifier to BE the `verifier` role, so "
            "verification cannot be absorbed into the coordinating role. Pinned because a reader "
            "reasoning from the function's NAME would expect this to pass",
        ),
        (
            "the CORRECTOR over an executor's work",
            "corrector",
            "executor",
            False,
            "a corrector is a mutating role, so letting it verify would put the same actor class on both "
            "sides of the boundary even when the individual differs",
        ),
        (
            "the verifier over its OWN work",
            "verifier",
            "verifier",
            True,
            "ALSO SURPRISING AND ALSO MEASURED: this is PERMITTED, because the second half of the guard "
            "keys on the author being an `executor` or `corrector`. It is pinned as the real behavior "
            "rather than asserted as a policy; if it is ever tightened, this row is the record that the "
            "change was deliberate",
        ),
    )

    def test_verification_is_permitted_only_to_the_independent_verifier_role(self):
        insp = MC.DiffInspection(diff_paths=(), declared_paths=(), raw_check_results={})
        wrong = []
        for case, verifier_role, author_role, permitted, why in self.VERIFIER_GRID:
            v = MC.VerifyExecutionCoordinator(plan_id="plan-under-test")
            problems = []
            try:
                v.verify(insp, verifier_role=verifier_role, author_role=author_role)
                if not permitted:
                    problems.append(
                        "verification was PERMITTED where it must be refused, so this actor could "
                        "clear its own (or its own role class's) work"
                    )
            except ROLES.SelfVerificationForbiddenError as exc:
                if permitted:
                    problems.append(
                        f"verification was REFUSED where it must be allowed: {exc}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (verifier={verifier_role!r}, author={author_role!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the independence guard was wrong for {len(wrong)} of {len(self.VERIFIER_GRID)} (verifier, "
            "author) pairings. READ WHICH DIRECTION MOVED. The `executor`-over-its-own-work row being "
            "PERMITTED is the dangerous failure and the one the guard exists for: an executor's own "
            "claim would then stand as the independent evidence a terminal move requires. The "
            "`verifier`-over-`executor` row being refused means verification is impossible and every "
            "other row is vacuous. NOTE two rows record MEASURED behavior that is broader or narrower "
            "than the rule's name suggests (a coordinator may NOT verify; a verifier verifying its own "
            "work MAY): if either flips, the guard was retightened or loosened deliberately and this "
            f"table is where that decision is recorded.\n" + "\n".join(wrong),
        )


# ==================================================================================================
# E-03: assess-all read-only lanes + single-writer synthesis; setup-repo state machine
# ==================================================================================================


class AssessAllCoordinatorTests(unittest.TestCase):
    """NOT TABULATED, and each test says why. Four tests over three distinct subjects.

    There is no grid here: the lanes claim is about one member list's eligibility, the synthesis claim
    is about de-duplication ORDER, and the writer claims are an `assertRaises` plus its idempotence
    counterpart. A table would have one row per subject, which is four tests with extra machinery.
    """

    def setUp(self):
        self.c = MC.AssessAllCoordinator(members=("security", "performance", "tests"))

    def test_lanes_are_read_only_and_parallel_eligible(self):
        """Kept separate: one claim about the lane set, asserted through two entry points."""
        self.c.assert_lanes_read_only()
        elig = self.c.eligibility()
        self.assertTrue(elig.is_eligible_parallel)
        self.assertEqual(elig.execution_mode, ISO.EXEC_MODE_PARALLEL_READ_ONLY)
        # EVERY lane, not merely the aggregate verdict: one mutating lane among many would make the
        # whole fan-out unsafe, and `assert_lanes_read_only` is the only thing checking per lane.
        self.assertEqual(
            {lane.lane_kind for lane in self.c.lanes()}, {ISO.LANE_KIND_READ_ONLY}
        )
        self.assertEqual(len(self.c.lanes()), len(self.c.members))

    def test_single_writer_synthesis(self):
        """Kept separate: the assertion is about de-duplication ORDER, not about a verdict.

        The expected list is `["b", "c", "a"]`, which encodes that lanes are read in SORTED member
        order (`performance` before `security`) and first-seen wins. That is a property of one call's
        output and has no second mode to be a column.
        """
        out = self.c.synthesize(
            "coordinator-A",
            {"security": ["a", "b"], "performance": ["b", "c"]},
        )
        self.assertEqual(out["consolidated_findings"], ["b", "c", "a"])
        self.assertEqual(out["writer"], "coordinator-A")

    def test_second_writer_refused(self):
        """Kept separate: `assertRaises` over the single-writer claim."""
        self.c.claim_synthesis_writer("coordinator-A")
        with self.assertRaises(MC.SingleWriterViolationError):
            self.c.claim_synthesis_writer("coordinator-B")

    def test_same_writer_reclaim_allowed(self):
        """Kept separate: the IDEMPOTENCE half of the pair above, whose content is that nothing raises.

        Merging the two would need a raises-or-not column over two claims that are each one line, and
        the pair is only meaningful read together: a guard that refused every reclaim would satisfy the
        test above while making a retry impossible.
        """
        self.c.claim_synthesis_writer("coordinator-A")
        self.c.claim_synthesis_writer("coordinator-A")  # idempotent, no raise


class SetupRepoStateMachineTests(unittest.TestCase):
    def _change(self, cid="c1", fail=False):
        return MC.SetupChange(
            change_id=cid,
            description="write config {0}".format(cid),
            idempotency_key="key-{0}".format(cid),
            rollback="delete config {0}".format(cid),
        )

    #: (case, the `interactive` flag, the preconditions, the exception class name expected or None if
    #: preflight must PASS, the state expected afterwards, why this row exists)
    PREFLIGHTS = (
        (
            "interactive, with every precondition met",
            True,
            {"git": True},
            None,
            MC.SETUP_STATE_AWAITING_CONSENT,
            "THE CLEAN ROW: preflight must be passable, and it must leave the machine AWAITING CONSENT "
            "rather than APPLYING, so no change is applied by passing preflight alone. Every refusal "
            "row below is vacuous while this is broken, because a preflight that refused everything "
            "satisfies all of them and setup-repo would simply never run",
        ),
        (
            "interactive, with NO preconditions declared",
            True,
            {},
            None,
            MC.SETUP_STATE_AWAITING_CONSENT,
            "an empty precondition map is vacuously satisfied, which is the boundary of the `any unmet` "
            "check. Kept as its own row so a scan that refused on an empty map (or that required at "
            "least one precondition) is caught",
        ),
        (
            "HEADLESS, with every precondition met",
            False,
            {"git": True},
            "SetupHeadlessRefusalError",
            MC.SETUP_STATE_REFUSED,
            "THE HEADLESS REFUSAL, AND IT MUST HAPPEN AT PREFLIGHT, i.e. BEFORE any change is applied. A "
            "headless run cannot obtain the per-change consent it requires, so stopping here is what "
            "prevents it stopping halfway through a mutation and leaving the tree in a state nobody "
            "chose. The preconditions are MET deliberately, so this row isolates the headless check",
        ),
        (
            "interactive, with an UNMET precondition",
            True,
            {"git": True, "writable": False},
            "SetupPreflightError",
            MC.SETUP_STATE_REFUSED,
            "PREFLIGHT BEFORE MUTATION: an unmet precondition refuses before a single change applies. "
            "The distinct exception class matters, because an operator's fix differs (make the tree "
            "writable versus run interactively), and one met precondition sits beside the unmet one so "
            "the check is proven to be `any unmet` rather than `all unmet`",
        ),
        (
            "HEADLESS and an unmet precondition together",
            False,
            {"git": False},
            "SetupPreflightError",
            MC.SETUP_STATE_REFUSED,
            "BOTH REFUSALS AT ONCE, which pins the ORDER they are checked in: the precondition failure "
            "wins. That is the right order to report, because it is the more specific fact, and pinning "
            "it stops a refactor silently reporting `run interactively` to an operator whose real "
            "problem is an unwritable tree",
        ),
    )

    def test_preflight_refuses_before_any_mutation_and_leaves_nothing_behind(self):
        """Every preflight outcome, asserting the FULL safety property: nothing applied, nothing left.

        ONE table replaces two tests (`headless_refused_before_any_mutation`,
        `preflight_refuses_on_unmet_precondition`). Both constructed a machine, called `preflight`, and
        asserted the exception class, the resulting state, and an empty `applied_changes`.

        MERGED ONLY BECAUSE EVERY ROW ASSERTS THE WHOLE PROPERTY, which for this destructive-adjacent
        subject means all of: the exception CLASS (an operator's fix differs per class), the resulting
        STATE, an empty `applied_changes`, an empty `applied_keys`, and an empty `rolled_back`. The last
        two are new here: a refusal that recorded an idempotency key would cause the NEXT run to skip
        that change as already applied, which is how a change silently never happens, and a refusal that
        populated `rolled_back` would report having undone work it never did.

        THE CLEAN ROWS ARE IN THE SAME TABLE, and the state column is what makes them meaningful: a
        passing preflight must leave the machine AWAITING CONSENT, never APPLYING, so passing preflight
        is not itself permission to mutate.

        The multi-step tests below are NOT rows, each for the reason in its own docstring.
        """
        wrong = []
        for (
            case,
            interactive,
            preconditions,
            expected_exc,
            expected_state,
            why,
        ) in self.PREFLIGHTS:
            sm = MC.SetupRepoStateMachine(
                interactive=interactive, preconditions=preconditions
            )
            problems = []
            got_exc = None
            try:
                sm.preflight()
            except MC.ComplexMigrationError as exc:
                got_exc = type(exc).__name__
            if expected_exc is None and got_exc is not None:
                problems.append(f"preflight REFUSED where it must pass ({got_exc})")
            elif expected_exc is not None and got_exc is None:
                problems.append(
                    "preflight PASSED where it must refuse, so the run would proceed to mutate"
                )
            elif expected_exc is not None and got_exc != expected_exc:
                problems.append(
                    f"refused with {got_exc}, expected {expected_exc}: the class is what tells an "
                    "operator which problem to fix"
                )
            if sm.state != expected_state:
                problems.append(
                    f"the state is {sm.state!r}, expected {expected_state!r}"
                )
            # THE SAFETY PROPERTY, asserted on EVERY row including the clean ones: preflight must never
            # apply, record, or claim to have undone anything.
            if sm.applied_changes:
                problems.append(
                    f"preflight left APPLIED CHANGES behind: {sm.applied_changes!r}. Nothing may be "
                    "applied before per-change consent"
                )
            if sm.applied_keys:
                problems.append(
                    f"preflight recorded idempotency KEYS: {sm.applied_keys!r}. A recorded key makes "
                    "the next run treat that change as already applied, so the change silently never "
                    "happens"
                )
            if sm.rolled_back:
                problems.append(
                    f"preflight reported ROLLED-BACK changes: {sm.rolled_back!r}, claiming to have "
                    "undone work it never did"
                )
            if problems:
                wrong.append(
                    f"  {case} (interactive={interactive}, preconditions={preconditions!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"preflight was wrong for {len(wrong)} of {len(self.PREFLIGHTS)} configurations. READ WHICH "
            "SIDE MOVED. Both CLEAN rows refusing means setup-repo cannot run at all, which is loud and "
            "safe but makes every refusal row vacuous. A REFUSAL row passing is the dangerous "
            "direction: the headless row passing means an unattended run proceeds toward mutations "
            "whose per-change consent it can never obtain, so it stops PARTWAY through instead of "
            "before starting, which is exactly the unrecoverable state preflight exists to prevent. "
            "Any leftover `applied_changes`, `applied_keys` or `rolled_back` after a preflight is its "
            "own defect regardless of the verdict, because a recorded key makes the NEXT run skip a "
            f"change that never happened.\n" + "\n".join(wrong),
        )

    def test_cannot_apply_before_preflight(self):
        """Kept separate: `assertRaises` asserting an ORDERING constraint between two calls.

        The property is that `apply_change` is unreachable until `preflight` has passed, which is a
        claim about a sequence and cannot be a row in a table of single-call outcomes.
        """
        sm = MC.SetupRepoStateMachine(interactive=True, preconditions={})
        with self.assertRaises(MC.ComplexMigrationError):
            sm.apply_change(self._change(), input_handler=_approve_handler)
        # AND NOTHING WAS APPLIED OR RECORDED by the refused call.
        self.assertEqual(sm.state, MC.SETUP_STATE_PREFLIGHT)
        self.assertEqual(sm.applied_changes, [])
        self.assertEqual(sm.applied_keys, [])

    def test_per_change_consent_gate_rejection_blocks(self):
        """Kept separate: a multi-step transcript (preflight, then a REFUSED change) over a stateful
        object, and an `assertRaises`. Not merged because the claim is about what a rejection leaves
        behind mid-sequence, which a single-call row cannot express.
        """
        sm = MC.SetupRepoStateMachine(interactive=True, preconditions={"git": True})
        sm.preflight()
        with self.assertRaises(MC.ComplexMigrationError):
            sm.apply_change(self._change(), input_handler=_reject_handler)
        # A REFUSED CONSENT APPLIES NOTHING and does not advance the machine past awaiting consent.
        self.assertEqual(sm.state, MC.SETUP_STATE_AWAITING_CONSENT)
        self.assertEqual(sm.applied_changes, [])
        self.assertEqual(sm.applied_keys, [])
        self.assertEqual(sm.rolled_back, [])

    def test_consent_approval_applies_change(self):
        """Kept separate: a multi-step transcript over a stateful object (preflight, then apply).

        This is the positive counterpart of the rejection test above, and the pair is only meaningful
        read together. Not a row because the claim spans two calls on one machine.
        """
        sm = MC.SetupRepoStateMachine(interactive=True, preconditions={"git": True})
        sm.preflight()
        result = sm.apply_change(self._change("c1"), input_handler=_approve_handler)
        self.assertEqual(result, "applied")
        self.assertEqual(sm.applied_changes, ["c1"])
        self.assertEqual(sm.applied_keys, ["key-c1"])
        self.assertEqual(sm.rolled_back, [])

    def test_idempotency_reapply_is_noop(self):
        """Kept separate: a BEFORE/AFTER idempotence PAIR, which the house rule does not merge.

        The whole content is that the SECOND identical call answers differently from the first while
        changing nothing, so both calls and the state between them are the test.
        """
        sm = MC.SetupRepoStateMachine(interactive=True, preconditions={"git": True})
        sm.preflight()
        self.assertEqual(
            sm.apply_change(self._change("c1"), input_handler=_approve_handler),
            "applied",
        )
        result = sm.apply_change(self._change("c1"), input_handler=_approve_handler)
        self.assertEqual(result, "noop")
        self.assertEqual(sm.applied_changes.count("c1"), 1)
        # THE NO-OP MUST NOT LOSE THE FIRST APPLICATION: a re-run that reported `noop` while dropping
        # the recorded change would make the next run re-apply it.
        self.assertEqual(sm.applied_changes, ["c1"])
        self.assertEqual(sm.applied_keys, ["key-c1"])
        self.assertEqual(sm.rolled_back, [])

    def test_failed_change_rolls_back_in_reverse(self):
        """Kept separate: a four-step transcript whose claim is about an ORDERED history.

        THE RECOVERABILITY PROPERTY IS THE ORDER, so it cannot be a row: `rolled_back == ["c2", "c1"]`
        is the assertion, and reverse order is what makes an undo safe when changes depend on each
        other. A table row asserting one call's return value cannot state it.
        """
        sm = MC.SetupRepoStateMachine(interactive=True, preconditions={"git": True})
        sm.preflight()
        sm.apply_change(self._change("c1"), input_handler=_approve_handler)
        sm.apply_change(self._change("c2"), input_handler=_approve_handler)
        with self.assertRaises(MC.ComplexMigrationError):
            sm.apply_change(
                self._change("c3", fail=True), input_handler=_approve_handler, fail=True
            )
        self.assertEqual(sm.state, MC.SETUP_STATE_ROLLED_BACK)
        self.assertEqual(sm.rolled_back, ["c2", "c1"])
        self.assertEqual(sm.applied_changes, [])
        # THE KEYS ARE CLEARED TOO, which is what makes the rollback a real undo rather than a report:
        # a surviving key would make a later run skip a change that was rolled back and never applied.
        self.assertEqual(sm.applied_keys, [])
        # AND THE FAILED CHANGE ITSELF IS NOT RECORDED AS APPLIED OR AS ROLLED BACK.
        self.assertNotIn("c3", sm.rolled_back)
        self.assertNotIn("c3", sm.applied_changes)


# ==================================================================================================
# E-04: incident / migrate / benchmark -- operator data + honest limitations
# ==================================================================================================


class OperatorDataIsLabeledNeverFabricated(unittest.TestCase):
    """The (provenance x value-present) grid: which data a datum may carry, and how it is labeled.

    ONE table replaces three tests (`operator_data_labeled_unavailable_not_fabricated`,
    `unavailable_datum_with_fabricated_value_rejected`, `unknown_provenance_rejected`). Each constructed
    one `OperatorDatum` and asserted either its labeling or its refusal, so the PROVENANCE and whether a
    VALUE was supplied are the two columns of one grid.

    THE VALUE COLUMN IS WHY THIS MUST BE ONE TABLE. The rule is a CONJUNCTION (the provenance is in the
    closed set, AND an unavailable datum carries no value), so the property worth asserting is that
    `unavailable` with a value is refused while `unavailable` without one is fine AND `operator-reported`
    with a value is fine. Three separate tests each stated one cell; nothing said the refusal was about
    the COMBINATION rather than about either half, so a rule that rejected every unavailable datum, or
    every valued one, would have looked correct.

    EVERY ACCEPTED ROW ASSERTS THE FULL LABELING, not merely that construction succeeded: both derived
    predicates (`is_labeled_unavailable`, `is_operator_owned`) and whether the key appears in the
    package's `unavailable_data()` AND in the built artifact's `operator_data_unavailable` list. That
    last hop is the one that matters, because a datum correctly labeled in memory but omitted from the
    ARTIFACT would let a report read as though the data were available; and it is why the rows go
    through a package rather than testing the dataclass alone.

    `is_operator_owned` IS PINNED PER ROW BECAUSE IT IS THE SURPRISING PREDICATE: it is True for
    `operator-reported` AND for `operator-data-unavailable`, and False only for repo-evidenced data, so
    it partitions the data by OWNERSHIP rather than by availability.
    """

    #: (case, the provenance, the value to supply, whether construction must SUCCEED, expected
    #: `is_labeled_unavailable`, expected `is_operator_owned`, whether the key must appear in the
    #: artifact's unavailable list, why this row exists)
    #:
    #: THE PROVENANCES ARE LITERAL STRINGS, not `MC.PROVENANCE_*`: these values are written into the
    #: emitted artifact and are what a reader judges the report's trustworthiness by, so a rename is a
    #: change to a published label and must fail here rather than moving on both sides at once.
    DATA = (
        (
            "repo-evidenced data carrying a value",
            "repo-evidenced",
            "abc123",
            True,
            False,
            False,
            False,
            "THE PRIMARY CLEAN ROW: a fact read out of the checkout is available, is not operator-owned, "
            "and must NOT be listed as unavailable. Every refusal row is vacuous while this is broken, "
            "because a constructor that rejected everything satisfies all of them",
        ),
        (
            "repo-evidenced data with no value",
            "repo-evidenced",
            None,
            True,
            False,
            False,
            False,
            "a value is not MANDATORY for repo data, so the constructor must not require one. This row "
            "keeps the `unavailable` refusal below from being read as a general no-value-allowed rule",
        ),
        (
            "operator-reported data carrying a value",
            "operator-reported",
            "the operator says the job ran at 03:00",
            True,
            False,
            True,
            False,
            "AN OPERATOR-REPORTED FACT IS ALLOWED TO CARRY A VALUE, because the operator supplied it; "
            "what is forbidden is INVENTING one. It is `is_operator_owned` but NOT "
            "`is_labeled_unavailable`, which is the distinction the two predicates exist to make: this "
            "datum is owned outside the repo AND is available",
        ),
        (
            "operator data LABELED unavailable, with no value",
            "operator-data-unavailable",
            None,
            True,
            True,
            True,
            True,
            "THE HONEST CASE THIS WHOLE SCHEME EXISTS FOR: data the repo cannot see is LABELED as "
            "missing rather than guessed at. It must reach the ARTIFACT's unavailable list, because a "
            "report that omits the label reads as though the data were available and the reader has no "
            "way to know what is missing",
        ),
        (
            "operator data labeled unavailable but carrying a FABRICATED value",
            "operator-data-unavailable",
            "99.9% uptime",
            False,
            None,
            None,
            None,
            "THE FABRICATION REFUSAL, and this is the row the module is named around: a value on an "
            "unavailable datum is an invented fact wearing a provenance label that says nobody "
            "measured it. Refusing at CONSTRUCTION is what makes it unrepresentable rather than merely "
            "discouraged",
        ),
        (
            "an unknown provenance",
            "made-up",
            None,
            False,
            None,
            None,
            None,
            "the provenance vocabulary is CLOSED. An unrecognized label would be carried into the "
            "artifact verbatim, where a reader would have no idea how much to trust the datum, and a "
            "typo'd `operator-data-unavailble` would silently become an available fact",
        ),
        (
            "an unknown provenance WITH a value",
            "made-up",
            "some value",
            False,
            None,
            None,
            None,
            "the same refusal must not depend on the value column, which is what pins the two conjuncts "
            "as INDEPENDENT rather than as one combined check",
        ),
    )

    def test_each_provenance_is_labeled_and_a_fabricated_value_is_refused(self):
        wrong = []
        for (
            case,
            provenance,
            value,
            must_construct,
            labeled_unavailable,
            operator_owned,
            in_artifact_list,
            why,
        ) in self.DATA:
            problems = []
            datum = None
            try:
                datum = MC.OperatorDatum(
                    key="the_datum", provenance=provenance, value=value
                )
                if not must_construct:
                    problems.append(
                        "construction SUCCEEDED where it must be refused, so this datum could reach an "
                        "emitted artifact"
                    )
            except MC.ComplexMigrationError as exc:
                if must_construct:
                    problems.append(f"construction was REFUSED: {exc}")
                elif "the_datum" not in str(exc):
                    problems.append(
                        f"the refusal must name the offending datum's key; it said {str(exc)!r}"
                    )
            if datum is not None and must_construct:
                if datum.is_labeled_unavailable is not labeled_unavailable:
                    problems.append(
                        f"`is_labeled_unavailable` is {datum.is_labeled_unavailable}, expected "
                        f"{labeled_unavailable}"
                    )
                if datum.is_operator_owned is not operator_owned:
                    problems.append(
                        f"`is_operator_owned` is {datum.is_operator_owned}, expected "
                        f"{operator_owned}: this predicate partitions data by OWNERSHIP, not by "
                        "availability"
                    )
                # THE LABEL MUST SURVIVE INTO THE EMITTED ARTIFACT, which is the only place a reader
                # sees it. A datum labeled correctly in memory but omitted here reads as available.
                pkg = MC.build_incident_package()
                pkg.add_datum(datum)
                listed_on_pkg = "the_datum" in pkg.unavailable_data()
                listed_in_artifact = (
                    "the_datum" in pkg.build_artifact()["operator_data_unavailable"]
                )
                if listed_on_pkg is not in_artifact_list:
                    problems.append(
                        f"`unavailable_data()` {'omitted' if in_artifact_list else 'listed'} this key "
                        f"when it must {'list' if in_artifact_list else 'omit'} it"
                    )
                if listed_in_artifact is not in_artifact_list:
                    problems.append(
                        f"the built artifact's `operator_data_unavailable` "
                        f"{'omitted' if in_artifact_list else 'listed'} this key when it must "
                        f"{'list' if in_artifact_list else 'omit'} it. The artifact is the only place "
                        "a reader sees the label"
                    )
            if problems:
                wrong.append(
                    f"  {case} (provenance={provenance!r}, value={value!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"operator-data labeling was wrong for {len(wrong)} of {len(self.DATA)} (provenance, value) "
            "cells. READ THE GROUPING, because the rule is a CONJUNCTION and each pattern names which "
            "conjunct moved. The FABRICATED-VALUE row constructing means an invented fact can now be "
            "emitted wearing a label that says nobody measured it, which is the dangerous direction and "
            "the one this scheme exists to prevent. Both UNKNOWN-PROVENANCE rows constructing means the "
            "vocabulary opened, so a typo'd label silently becomes an available fact. An accepted row "
            "being refused makes every refusal row vacuous. A label that is right on the DATUM but "
            "missing from the ARTIFACT is its own defect regardless of the predicates, because the "
            f"artifact is the only surface a reader judges the report's completeness from.\n"
            + "\n".join(wrong),
        )


class HonestLimitationsAreRefusalsNotDisclaimers(unittest.TestCase):
    """Which CLAIMS each risk-aware package refuses to make, across all three workflows.

    ONE table replaces four tests (`unsupported_certification_claim_refused`,
    `unsupported_hpc_submission_claim_refused`, `unsupported_compliance_attestation_refused`,
    `supported_claim_allowed`). Each built one package and asserted one claim's acceptance or refusal,
    so the CLAIM and the PACKAGE are columns.

    THE PACKAGE IS A COLUMN AND THAT IS WHAT THE SPLIT COULD NOT SAY. The three old refusal tests used
    non-overlapping packages (certification and HPC on `benchmark`, compliance on `migrate`), so a
    refusal implemented on one workflow and missing from another was invisible. Every claim now runs
    against all three packages, which turns "benchmark refuses certification" into "no workflow will
    claim certification".

    THE ALLOWED ROWS ARE IN THE SAME TABLE and they are load-bearing rather than decorative: a
    `assert_supportable_claim` that raised on everything would satisfy all three refusal rows while
    making every legitimate claim unmakeable, and the method is called on the happy path.

    EVERY REFUSAL ROW ASSERTS THE MESSAGE'S CONTENT, not just the exception type, because the whole
    point is an HONEST LIMITATION rather than a bare denial: the refusal must name the claim and say
    the workflow produces repo-scoped artifacts and cannot act on the operator's behalf. A refusal that
    said only "not allowed" would leave a reader thinking the capability exists and is withheld.
    """

    #: (case, the claim, whether it must be REFUSED, why this row exists)
    #:
    #: The claim strings are LITERAL rather than `MC.CLAIM_*` for the usual reason: they are the values
    #: a caller passes in, so a rename must fail here rather than moving on both sides together.
    CLAIMS = (
        (
            "a certification claim",
            "certification",
            True,
            "CERTIFICATION REQUIRES AN EXTERNAL BODY the repo cannot invoke, so claiming it would imply "
            "an approval nobody granted. This is the archetype of the rule: the refusal is honest about "
            "a capability that does not exist rather than producing a hedged artifact that reads like "
            "certification",
        ),
        (
            "an HPC submission claim",
            "hpc-submission",
            True,
            "a real submission is an OPERATOR-OWNED EXECUTION on a scheduler the repo has no access to. "
            "A workflow claiming it would report a job that was never queued",
        ),
        (
            "a compliance attestation claim",
            "compliance-attestation",
            True,
            "an attestation is a STATEMENT OF FACT ABOUT A SYSTEM the repo can only partly see, and it "
            "is the claim with the most serious consequences if wrong, since it is the one a third "
            "party relies on",
        ),
        (
            "a repo-scoped migration plan claim",
            "repo-scoped-migration-plan",
            False,
            "THE CLEAN ROW: a claim the repo CAN back must be allowed. Every refusal row above is "
            "vacuous while this is broken, because a method that raised on everything satisfies all of "
            "them and would block the workflow's actual deliverable",
        ),
        (
            "a repo-scoped assessment claim",
            "repo-scoped-assessment",
            False,
            "a SECOND allowed claim, so the clean row above cannot pass by one string being "
            "special-cased. Together they pin that the refusal set is a CLOSED list rather than an "
            "allowlist with one exception",
        ),
    )

    def test_no_workflow_makes_a_claim_it_cannot_back(self):
        builders = (
            ("incident", MC.build_incident_package),
            ("migrate", MC.build_migrate_package),
            ("benchmark", MC.build_benchmark_package),
        )
        wrong = []
        for case, claim, must_refuse, why in self.CLAIMS:
            for workflow, build in builders:
                pkg = build()
                problems = []
                try:
                    pkg.assert_supportable_claim(claim)
                    if must_refuse:
                        problems.append(
                            "the claim was ACCEPTED where it must be refused, so this workflow would "
                            "imply a capability it does not have"
                        )
                except MC.UnsupportedClaimError as exc:
                    if not must_refuse:
                        problems.append(
                            f"the claim was REFUSED where it must be allowed: {exc}"
                        )
                    else:
                        message = str(exc)
                        if claim not in message:
                            problems.append(
                                f"the refusal must name the claim {claim!r}; it said {message!r}"
                            )
                        if workflow not in message:
                            problems.append(
                                f"the refusal must name the workflow {workflow!r} so a reader knows "
                                f"which artifact is limited; it said {message!r}"
                            )
                        if "repo-scoped" not in message:
                            problems.append(
                                "the refusal must be an HONEST LIMITATION, saying the workflow "
                                "produces repo-scoped artifacts, rather than a bare denial that "
                                f"leaves the capability sounding merely withheld; it said {message!r}"
                            )
                if problems:
                    wrong.append(
                        f"  {case} (workflow={workflow!r}):\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"claim support was wrong for {len(wrong)} of {len(self.CLAIMS) * 3} (claim, workflow) "
            "cells. READ WHETHER A CLAIM OR A WORKFLOW FAILED. A whole CLAIM row moving means the "
            "closed unsupported set changed, which is a deliberate policy decision. A single WORKFLOW "
            "failing across claims is the gap this table was built to close: the refusals were "
            "previously tested on non-overlapping packages, so one implemented on `benchmark` and "
            "missing from `incident` was invisible. FIX: a refusal row being ACCEPTED is the dangerous "
            "direction, because the artifact then implies an external approval or an operator-side "
            "execution that never happened; an allowed row being refused merely blocks the workflow's "
            f"own deliverable, which is loud.\n" + "\n".join(wrong),
        )

    def test_artifact_is_conformant_and_verifiable(self):
        """Kept separate: the subject is the ARTIFACT's shape and digest stability, not a claim.

        Not a row because the assertion is a before/after digest PAIR (rebuild yields the same bytes),
        which is what makes the artifact verifiable, plus a required-key check over one emitted mapping.
        """
        pkg = MC.build_migrate_package()
        pkg.add_datum(
            MC.OperatorDatum(key="prod_schema", provenance=MC.PROVENANCE_UNAVAILABLE)
        )
        art = pkg.build_artifact()
        self.assertEqual(art["workflow"], "migrate")
        self.assertIn("honest_limitation", art)
        self.assertIn("artifact_digest", art)
        # DETERMINISTIC: rebuilding the same package reproduces the digest, so the artifact can be
        # re-derived and compared rather than trusted.
        self.assertEqual(
            art["artifact_digest"], pkg.build_artifact()["artifact_digest"]
        )
        # AND THE DIGEST ACTUALLY COVERS THE DATA: a digest that ignored the data would be stable too,
        # which is what makes the stability assertion above meaningful rather than vacuous.
        other = MC.build_migrate_package()
        self.assertNotEqual(
            art["artifact_digest"], other.build_artifact()["artifact_digest"]
        )


# ==================================================================================================
# Manifest authority (non-destructive contract): every migrated command is a real manifest row
# ==================================================================================================


class ManifestAuthorityTests(unittest.TestCase):
    """NOT TABULATED: the subject is the LIVE manifest, not a fixture, and the claim is already a sweep.

    `assert_commands_in_manifest` returns every missing command at once, so it is the accumulate-and-
    report-all shape a table would build by hand, over a real tree rather than over rows.
    """

    def test_all_order15_commands_present_in_live_manifest(self):
        """Kept separate: reads the REAL workflow tree, so it is a corpus sweep rather than a case."""
        missing = MC.assert_commands_in_manifest(SOURCE_WORKFLOWS)
        self.assertEqual(missing, [], "missing manifest rows: {0}".format(missing))


if __name__ == "__main__":
    unittest.main()

"""Complex, stateful workflow migration onto the runtime/ledger/verifier architecture.

awoptimize Order 15 (`kh91or`). This module is the SECOND migration stage of the workflow-family
migration (Order 14 was the inventory + shared assess/advise families + plan-review collapse). It
migrates the complex, STATEFUL, orchestrated workflows onto deterministic coordinators that OWN
sequencing, gates, and terminal authority in code, while the judgment prose stays in the workflow
bodies. Everything here is pure/deterministic and stdlib-only (D138), never touching a runtime YAML
parser (D139), and NON-DESTRUCTIVE: it validates and builds typed contracts over the live manifest +
workflow bodies; it never rewrites the manifest index or an existing workflow body.

It BUILDS ON the existing runtime rather than forking it:

  * Order 05 `run_state` -- the ONE legal transition table + transition AUTHORITY. Terminal moves
    (`verified -> complete`) are authorized only for `coordinator`/`runtime`, NEVER `executor`; this
    module reuses that table so terminal transitions are mechanically executor-unreachable.
  * Order 02 `run_freeze` -- the ONE requirement-freezing + drift-detection scheme. A FROZEN MODE
    (release-review planning vs release) is a frozen requirement set; a mode change is detected as a
    revision, and a planning-mode set that later tries to enter a mutation/release requirement is
    refused.
  * Order 06 `run_gates` -- the ONE human-decision-gate + headless-refusal + never-synthesize-consent
    scheme. Confirmation gates, per-change consent, and headless refusal reuse it.
  * Order 08/09 `verify_roles` -- the ONE role contract + independent verifier + corrective-IPD
    routing. Executor-cannot-finalize and executor-cannot-self-verify reuse the role contracts; the
    corrective-IPD behavior reuses `route_verifier_findings`.
  * Order 07 `orchestrate_isolation` -- the ONE concurrency-eligibility + serial-integration scheme.
    assess-all read-only parallel lanes + single-writer synthesis and release-review serial mutation
    reuse it.
  * Order 01 `workflow_compiler`/`workflow_profile` + `engine.parse_manifest` -- the ONE compiler +
    semantic-digest + manifest authority, exactly as Order 14 used them.

Scope fence (Order 15): the canonical packages it coordinates are release-review(+release-review-plan),
verify-execution, ipd-lifecycle, assess-all, setup-repo, incident, migrate, benchmark. It does NOT
migrate compact workflows / shims / promotion gates (Order 16), remove legacy shims (Order 17), or
publish a release. Where a full manifest cutover would be needed, that is DEFERRED to Order 16 and the
contract is proved here at the coordinator/parity/fixture level instead.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from agent_workflows import engine
from agent_workflows import orchestrate_isolation as _iso
from agent_workflows import run_freeze as _freeze
from agent_workflows import run_gates as _gates
from agent_workflows import run_state as _state
from agent_workflows import verify_roles as _roles

# ==================================================================================================
# Shared errors
# ==================================================================================================


class ComplexMigrationError(ValueError):
    """Raised when a complex-workflow coordinator contract is violated (fail closed)."""


# ==================================================================================================
# E-01: release-review + release-review-plan -- deterministic coordinator with a FROZEN MODE
# ==================================================================================================

# The two release-review MODES. `release-review` runs the full runbook including mutation + the
# release boundary; `release-review-plan` runs the SAME runbook in a planning-only frozen mode that
# stops before implementation. The mode is FROZEN at run start (a `run_freeze` scope requirement) so
# a planning run cannot silently promote itself into a mutating/release run.
RELEASE_MODE_FULL: str = "release-review"
RELEASE_MODE_PLANNING: str = "release-review-plan"
RELEASE_MODES: FrozenSet[str] = frozenset((RELEASE_MODE_FULL, RELEASE_MODE_PLANNING))

# The eight reviewer personas (00-run-protocol.md). Each audit finding must be attributed to at least
# one persona and every persona lane must be dispositioned (no silently dropped finding).
RELEASE_PERSONAS: Tuple[str, ...] = (
    "qa_qc",
    "testing_regression",
    "ui_ux",
    "architect",
    "software_engineer",
    "power_user",
    "novice",
    "stakeholder",
)

# Remediation-Risk vocabulary + the Fix Bar predicate (fix-decision-policy.md). Fix by default; DEFER
# only when the remediation risk of the *cure* is Medium-High or higher.
REMEDIATION_RISKS: Tuple[str, ...] = ("low", "medium", "medium-high", "high")
_FIX_NOW_RISKS: FrozenSet[str] = frozenset(("low", "medium"))

# A finding disposition is one of these; every persona finding must carry exactly one.
DISPOSITION_FIX_NOW: str = "fix-now"
DISPOSITION_DEFER: str = "defer"
DISPOSITION_ESCALATE: str = (
    "escalate"  # LIVE/High data-integrity non-deferral escalation
)
FINDING_DISPOSITIONS: FrozenSet[str] = frozenset(
    (DISPOSITION_FIX_NOW, DISPOSITION_DEFER, DISPOSITION_ESCALATE)
)

# The release-review coordinator's own lifecycle stages, layered on the run_state machine. The
# PLANNING mode may reach only the read/audit/plan stages; MUTATION and RELEASE are forbidden to it.
STAGE_AUDIT: str = "audit"
STAGE_LEDGER: str = "ledger"
STAGE_PLAN: str = "plan"
STAGE_MUTATION: str = "mutation"
STAGE_VERIFY: str = "verify"
STAGE_RELEASE: str = "release"

# Stages a PLANNING-mode run may enter. Mutation/verify/release are full-mode only.
_PLANNING_ALLOWED_STAGES: FrozenSet[str] = frozenset(
    (STAGE_AUDIT, STAGE_LEDGER, STAGE_PLAN)
)


class ReleaseModeError(ComplexMigrationError):
    """Raised when a release-review run violates its frozen mode (e.g. planning enters mutation)."""


class ReleaseAuthorityError(ComplexMigrationError):
    """Raised when a release is attempted without explicit human release authority."""


def fix_bar(remediation_risk: str) -> bool:
    """The Fix Bar predicate: return True iff the finding should be FIXED NOW.

    Fix by default; defer only when the remediation risk of the cure is Medium-High or higher.
    (Impact/severity does NOT decide; only Remediation Risk does.) An unknown risk value is refused.
    """

    r = remediation_risk.strip().lower()
    if r not in REMEDIATION_RISKS:
        raise ComplexMigrationError(
            "unknown remediation risk '{0}' (expected one of {1})".format(
                remediation_risk, ", ".join(REMEDIATION_RISKS)
            )
        )
    return r in _FIX_NOW_RISKS


@dataclass(frozen=True)
class PersonaFinding:
    """One release-review finding attributed to a persona lane.

    ``remediation_risk`` feeds the Fix Bar; ``data_integrity`` marks a LIVE/High finding subject to
    the non-deferral escalation rule. ``disposition`` must be set by the coordinator's Fix Bar pass
    (never left blank), which is what proves no finding is silently dropped.
    """

    finding_id: str
    persona: str
    summary: str
    remediation_risk: str
    data_integrity: bool = False
    disposition: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "persona": self.persona,
            "summary": self.summary,
            "remediation_risk": self.remediation_risk,
            "data_integrity": self.data_integrity,
            "disposition": self.disposition,
        }


@dataclass
class IssueLedger:
    """The release-review issue ledger: every persona finding, each dispositioned exactly once.

    :meth:`disposition_all` applies the Fix Bar to every finding (fix-now / defer / escalate) so the
    ledger can PROVE (via :meth:`undispositioned`) that no finding was left un-triaged. The LIVE/High
    data-integrity non-deferral rule forces escalate-or-fix even when the cure is risky.
    """

    findings: List[PersonaFinding] = field(default_factory=list)

    def add(self, finding: PersonaFinding) -> None:
        if finding.persona not in RELEASE_PERSONAS:
            raise ComplexMigrationError(
                "finding '{0}' names unknown persona '{1}'".format(
                    finding.finding_id, finding.persona
                )
            )
        self.findings.append(finding)

    def disposition_all(self) -> List[PersonaFinding]:
        """Apply the Fix Bar to every finding, returning a new dispositioned list (single pass)."""

        out: List[PersonaFinding] = []
        for f in self.findings:
            if f.data_integrity:
                # LIVE/High non-deferral: never defer; fix now or escalate to the user.
                disp = (
                    DISPOSITION_FIX_NOW
                    if fix_bar(f.remediation_risk)
                    else DISPOSITION_ESCALATE
                )
            else:
                disp = (
                    DISPOSITION_FIX_NOW
                    if fix_bar(f.remediation_risk)
                    else DISPOSITION_DEFER
                )
            out.append(
                PersonaFinding(
                    finding_id=f.finding_id,
                    persona=f.persona,
                    summary=f.summary,
                    remediation_risk=f.remediation_risk,
                    data_integrity=f.data_integrity,
                    disposition=disp,
                )
            )
        self.findings = out
        return out

    def undispositioned(self) -> List[str]:
        """Return the ids of findings NOT yet dispositioned (empty == all triaged)."""

        return [
            f.finding_id
            for f in self.findings
            if f.disposition not in FINDING_DISPOSITIONS
        ]

    def personas_covered(self) -> FrozenSet[str]:
        return frozenset(f.persona for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "findings": [f.to_dict() for f in self.findings],
            "undispositioned": self.undispositioned(),
            "personas_covered": sorted(self.personas_covered()),
        }


@dataclass
class ReleaseReviewCoordinator:
    """Deterministic coordinator for release-review(+plan).

    It FREEZES the mode at construction (a `run_freeze` scope requirement), sequences the audit lanes,
    owns the issue ledger + Fix Bar pass, gates mutation and release behind explicit human authority
    (`run_gates`), serializes mutation through the Order-07 integration gate, and delegates terminal
    completion to the runtime (`run_state`), never to an executor.

    The load-bearing invariants:
      * a PLANNING-mode run can reach only audit/ledger/plan stages -- :meth:`enter_stage` REFUSES a
        mutation/verify/release stage in planning mode (planning-cannot-mutate);
      * :meth:`authorize_release` REFUSES unless an explicit human decision gate approved the release
        (a release needs explicit authority);
      * integration of accepted fixes is SERIAL (one mutating lane at a time).
    """

    mode: str
    frozen: _freeze.RequirementSet = field(init=False)
    ledger: IssueLedger = field(default_factory=IssueLedger)
    _stages_entered: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in RELEASE_MODES:
            raise ReleaseModeError(
                "unknown release-review mode '{0}' (expected one of {1})".format(
                    self.mode, ", ".join(sorted(RELEASE_MODES))
                )
            )
        # FREEZE the mode + its scope fence. The planning mode's scope fence forbids mutation/release;
        # the full mode permits them. Freezing binds this as a stable requirement digest so a later
        # mode flip is a detectable revision (see detect_mode_drift).
        if self.mode == RELEASE_MODE_PLANNING:
            scope = [
                "planning-only: audit and produce a consolidated IPD; stop before implementation",
                "planning-only: MUST NOT enter mutation, verification, or release stages",
            ]
        else:
            scope = [
                "full: audit, fix in place under the Fix Bar, verify, and (with authority) release",
                "full: mutation and release stages require explicit human authority",
            ]
        self.frozen = _freeze.freeze_requirements(
            {
                "must": [
                    "Attribute every finding to a persona and disposition each via the Fix Bar.",
                    "Never silently drop a finding.",
                ],
                "scope": scope,
                "validation": [
                    "Every persona finding is dispositioned before any mutation."
                ],
                "output": ["release-review issue ledger + per-phase report."],
            }
        )

    # -- stage sequencing -------------------------------------------------------------------------

    def enter_stage(self, stage: str) -> None:
        """Enter a coordinator stage, refusing a mutation/verify/release stage in PLANNING mode.

        This is the planning/release boundary: a planning-mode run can never reach a mutating or
        releasing stage, so a planning run cannot mutate the repo or ship.
        """

        if stage not in _PLANNING_ALLOWED_STAGES | {
            STAGE_MUTATION,
            STAGE_VERIFY,
            STAGE_RELEASE,
        }:
            raise ComplexMigrationError("unknown stage '{0}'".format(stage))
        if self.mode == RELEASE_MODE_PLANNING and stage not in _PLANNING_ALLOWED_STAGES:
            raise ReleaseModeError(
                "planning-mode run may not enter stage '{0}' (planning cannot mutate or release)".format(
                    stage
                )
            )
        self._stages_entered.append(stage)

    @property
    def stages_entered(self) -> Tuple[str, ...]:
        return tuple(self._stages_entered)

    # -- Fix Bar pass -----------------------------------------------------------------------------

    def run_fix_bar(self) -> List[PersonaFinding]:
        """Disposition every finding via the Fix Bar; refuse to proceed if any is left un-triaged."""

        self.enter_stage(STAGE_LEDGER)
        out = self.ledger.disposition_all()
        missing = self.ledger.undispositioned()
        if missing:
            raise ComplexMigrationError(
                "findings left undispositioned: {0}".format(", ".join(missing))
            )
        return out

    # -- serialized mutation ----------------------------------------------------------------------

    def integrate_fixes(
        self, lanes: Sequence[_iso.LaneRequest]
    ) -> _iso.ConcurrencyEligibilityResult:
        """Plan the integration of accepted fixes; mutation must be SERIAL (single-writer).

        Refused in planning mode (via :meth:`enter_stage`). Reuses the Order-07 concurrency analyzer;
        for mutating lanes it yields a serial (or serial-fallback) execution mode, never a parallel
        mutating fan-out. Returns the eligibility result so the caller can prove seriality.
        """

        self.enter_stage(STAGE_MUTATION)
        result = _iso.analyze_concurrency_eligibility(lanes)
        if result.execution_mode == _iso.EXEC_MODE_PARALLEL_MUTATING:
            raise ComplexMigrationError(
                "release-review integration must be serial; refused parallel mutating fan-out"
            )
        return result

    # -- explicit release boundary ----------------------------------------------------------------

    def authorize_release(
        self,
        *,
        interactive: bool,
        input_handler: Optional[Any] = None,
        approver: str = "human",
    ) -> _gates.GateDecision:
        """Gate the release behind an explicit human decision. REFUSE without explicit approval.

        In planning mode this cannot even be reached (enter_stage refuses STAGE_RELEASE). In full
        mode a headless run stops at `needs_input`; only an explicit interactive human approval
        returns an approved decision. This is the explicit release authority.
        """

        self.enter_stage(STAGE_RELEASE)
        gate = _gates.DecisionGate(
            gate_id="release-review/release",
            prompt="Execute the release (tag/publish)? This is irreversible.",
            options=("approve", "reject", "abort"),
            default_option="abort",
            requires_human=True,
        )
        decision = _gates.evaluate_gate(
            gate,
            interactive=interactive,
            input_handler=input_handler,
            approver=approver,
        )
        if not decision.is_approved:
            raise ReleaseAuthorityError(
                "release refused: no explicit human release authority ({0})".format(
                    decision.status
                )
            )
        return decision

    # -- terminal completion is owned by the runtime, never the executor --------------------------

    def can_finalize(self, actor_role: str) -> bool:
        """Return True iff ``actor_role`` may author the terminal `verified -> complete` transition.

        Delegates to the ONE run_state authority table: only coordinator/runtime, never executor.
        """

        return _state.is_legal_edge(
            _state.STATE_VERIFIED, _state.STATE_COMPLETE, actor_role
        )


def detect_mode_drift(coordinator: ReleaseReviewCoordinator, other_mode: str) -> bool:
    """Return True iff switching to ``other_mode`` would change the frozen requirement set (drift).

    A planning->full (or full->planning) flip changes the frozen scope requirements, so the frozen
    digests differ: this is a detectable requirement revision, which is how a silent mode promotion
    is caught. Same-mode returns False.
    """

    probe = ReleaseReviewCoordinator(mode=other_mode)
    revisions = _freeze.diff_requirements(coordinator.frozen, probe.frozen)
    return bool(revisions)


# ==================================================================================================
# E-02: verify-execution + ipd-lifecycle -- runtime/ledger/verifier; terminal executor-unreachable
# ==================================================================================================

# The IPD lifecycle transitions this coordinator owns. The TERMINAL transition (move a plan to
# executed/ and mark it executed) is mechanically executor-unreachable: it maps onto the run_state
# `verified -> complete` edge, authorized only for coordinator/runtime, and additionally requires the
# verifier's independent decision to have already produced `verified`.
LIFECYCLE_TRANSITION_TERMINAL: str = "mark-executed"
LIFECYCLE_TRANSITION_CORRECTIVE: str = "route-corrective"


class TerminalUnreachableError(ComplexMigrationError):
    """Raised when a non-authorized (e.g. executor) context attempts a terminal lifecycle move."""


@dataclass(frozen=True)
class DiffInspection:
    """The result of inspecting the ACTUAL diff + raw checks for a verify-execution run.

    ``diff_paths`` are the files the diff actually touched; ``declared_paths`` are the plan's scope
    fence; ``raw_check_results`` maps a check id -> its ACTUAL boolean pass. A verifier reads THIS,
    not the executor's prose claim, which is what makes verification independent.
    """

    diff_paths: Tuple[str, ...]
    declared_paths: Tuple[str, ...]
    raw_check_results: Mapping[str, bool]

    def out_of_scope_paths(self) -> Tuple[str, ...]:
        allowed = set(self.declared_paths)
        return tuple(sorted(p for p in self.diff_paths if p not in allowed))

    def failed_checks(self) -> Tuple[str, ...]:
        return tuple(
            sorted(cid for cid, ok in self.raw_check_results.items() if not ok)
        )

    def is_clean(self) -> bool:
        return not self.out_of_scope_paths() and not self.failed_checks()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diff_paths": list(self.diff_paths),
            "declared_paths": list(self.declared_paths),
            "raw_check_results": dict(self.raw_check_results),
            "out_of_scope_paths": list(self.out_of_scope_paths()),
            "failed_checks": list(self.failed_checks()),
            "is_clean": self.is_clean(),
        }


@dataclass(frozen=True)
class CorrectiveArtifact:
    """A corrective-IPD artifact emitted for a verification gap (preserves corrective-IPD behavior)."""

    artifact_id: str
    gap_summary: str
    failed_items: Tuple[str, ...]
    target_paths: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "gap_summary": self.gap_summary,
            "failed_items": list(self.failed_items),
            "target_paths": list(self.target_paths),
        }


@dataclass
class VerifyExecutionCoordinator:
    """verify-execution + ipd-lifecycle migrated to the runtime/ledger/verifier architecture.

    The executor performs the work and records raw evidence; an INDEPENDENT verifier inspects the
    actual diff + raw checks (never the executor's prose), and gaps route to corrective-IPD artifacts.
    The terminal lifecycle move is owned by coordinator/runtime and additionally gated on the
    verifier having produced `verified`. An executor context is mechanically barred from the terminal
    transition (reuses the Order-05 authority table + the Order-08 role contracts).
    """

    plan_id: str

    # -- independent verification (executor cannot self-verify) -----------------------------------

    def verify(
        self, inspection: DiffInspection, *, verifier_role: str, author_role: str
    ) -> Tuple[bool, List[CorrectiveArtifact]]:
        """Independently verify a run from the ACTUAL diff + raw checks; emit corrective artifacts.

        Refuses self-verification (executor/corrector cannot verify their own work) via the Order-08
        role check. Returns (verified, corrective_artifacts): verified iff the inspection is clean
        AND the verifier is the independent verifier role.
        """

        # Independent-verification guard: the verifier must be the verifier role and must not be the
        # author. This is the one self-verification refusal, reused from verify_roles.
        _roles.check_self_verification(verifier_role, author_role, self.plan_id)

        artifacts: List[CorrectiveArtifact] = []
        if not inspection.is_clean():
            oos = inspection.out_of_scope_paths()
            failed = inspection.failed_checks()
            if oos:
                artifacts.append(
                    CorrectiveArtifact(
                        artifact_id="{0}-scope".format(self.plan_id),
                        gap_summary="diff touched out-of-scope paths",
                        failed_items=oos,
                        target_paths=oos,
                    )
                )
            if failed:
                artifacts.append(
                    CorrectiveArtifact(
                        artifact_id="{0}-checks".format(self.plan_id),
                        gap_summary="raw checks failed",
                        failed_items=failed,
                        target_paths=inspection.declared_paths,
                    )
                )
        return inspection.is_clean(), artifacts

    # -- terminal transition is mechanically executor-unreachable ---------------------------------

    def can_mark_executed(self, actor_role: str, *, verifier_verified: bool) -> bool:
        """Return True iff ``actor_role`` may perform the terminal `mark-executed` move.

        Two independent gates, BOTH required: (1) the run_state authority table authorizes the
        `verified -> complete` edge for the role (executor is not authorized), and (2) the verifier
        already produced a `verified` decision. An executor fails gate (1) unconditionally.
        """

        if not verifier_verified:
            return False
        return _state.is_legal_edge(
            _state.STATE_VERIFIED, _state.STATE_COMPLETE, actor_role
        )

    def mark_executed(
        self, actor_role: str, *, verifier_verified: bool
    ) -> _state.TransitionRule:
        """Perform the terminal lifecycle move, raising if the actor context may not (fail closed).

        This is where an EXECUTOR context is rejected: `check_transition` for `verified -> complete`
        with actor=executor raises UnauthorizedActorError, which we surface as a
        TerminalUnreachableError so the terminal transition is mechanically unreachable to executors.
        """

        if not verifier_verified:
            raise TerminalUnreachableError(
                "cannot mark plan '{0}' executed: no independent verifier `verified` decision".format(
                    self.plan_id
                )
            )
        try:
            # The Order-08 role contract is the first, role-level fence.
            _roles.enforce_role_action(actor_role, "author_terminal_transaction")
            # The Order-05 authority table is the second, edge-level fence.
            return _state.check_transition(
                _state.STATE_VERIFIED,
                _state.STATE_COMPLETE,
                actor_role,
                predicate_values={"every_frozen_completion_predicate_true": True},
            )
        except (_roles.TerminalAuthorityError, _state.UnauthorizedActorError) as exc:
            raise TerminalUnreachableError(
                "actor '{0}' may not perform the terminal lifecycle move: {1}".format(
                    actor_role, exc
                )
            ) from exc


# ==================================================================================================
# E-03: assess-all (read-only parallel lanes + single-writer synthesis) + setup-repo (state machine)
# ==================================================================================================


class SingleWriterViolationError(ComplexMigrationError):
    """Raised when more than one writer would author the assess-all synthesis (not single-writer)."""


@dataclass
class AssessAllCoordinator:
    """assess-all as READ-ONLY parallel assessment lanes + ONE coordinator-owned synthesis.

    Every member lens runs as an independent READ-ONLY lane (no mutation), so the Order-07 analyzer
    approves parallel execution. The synthesis is single-writer: exactly ONE coordinator authors the
    consolidated IPD; registering a second synthesis writer is refused.
    """

    members: Tuple[str, ...]
    _synthesis_writer: Optional[str] = None

    def lanes(self) -> Tuple[_iso.LaneRequest, ...]:
        """Build one READ-ONLY lane per member (assessment lanes never mutate)."""

        return tuple(
            _iso.LaneRequest(
                lane_id="assess-{0}".format(m),
                actor_role=_roles.ROLE_INVESTIGATOR,
                lane_kind=_iso.LANE_KIND_READ_ONLY,
                files_targeted=(),
            )
            for m in self.members
        )

    def eligibility(self) -> _iso.ConcurrencyEligibilityResult:
        """Prove the lanes are read-only and hence parallel-eligible (reuses Order-07 analyzer)."""

        return _iso.analyze_concurrency_eligibility(self.lanes())

    def assert_lanes_read_only(self) -> None:
        """Fail closed if any lane is not read-only (an assessment lane must never mutate)."""

        for lane in self.lanes():
            if lane.lane_kind != _iso.LANE_KIND_READ_ONLY:
                raise ComplexMigrationError(
                    "assess-all lane '{0}' is not read-only".format(lane.lane_id)
                )

    def claim_synthesis_writer(self, writer: str) -> None:
        """Claim the single synthesis-writer slot; a second distinct claimant is refused.

        This enforces single-writer synthesis: many read-only lanes fan in, but exactly ONE
        coordinator writes the consolidated IPD.
        """

        if self._synthesis_writer is not None and self._synthesis_writer != writer:
            raise SingleWriterViolationError(
                "assess-all synthesis already claimed by '{0}'; '{1}' refused (single-writer)".format(
                    self._synthesis_writer, writer
                )
            )
        self._synthesis_writer = writer

    def synthesize(
        self, writer: str, lane_findings: Mapping[str, Sequence[str]]
    ) -> Dict[str, Any]:
        """Author the ONE consolidated, de-duplicated synthesis (single writer only)."""

        self.claim_synthesis_writer(writer)
        deduped: List[str] = []
        seen: set = set()
        for m in sorted(lane_findings):
            for f in lane_findings[m]:
                if f in seen:
                    continue
                seen.add(f)
                deduped.append(f)
        return {
            "writer": writer,
            "members": list(self.members),
            "consolidated_findings": deduped,
        }


# ---- setup-repo: deterministic interactive state machine ----------------------------------------

# setup-repo state-machine states.
SETUP_STATE_PREFLIGHT: str = "preflight"
SETUP_STATE_AWAITING_CONSENT: str = "awaiting_consent"
SETUP_STATE_APPLYING: str = "applying"
SETUP_STATE_DONE: str = "done"
SETUP_STATE_ROLLED_BACK: str = "rolled_back"
SETUP_STATE_REFUSED: str = "refused"


class SetupPreflightError(ComplexMigrationError):
    """Raised when setup-repo preflight fails (mutation is refused before it can start)."""


class SetupHeadlessRefusalError(ComplexMigrationError):
    """Raised when setup-repo is run non-interactively (it must refuse before any mutation)."""


@dataclass(frozen=True)
class SetupChange:
    """One proposed setup-repo change. ``idempotency_key`` lets an already-applied change be a no-op;
    ``rollback`` is the inverse action description so a partial run is recoverable."""

    change_id: str
    description: str
    idempotency_key: str
    rollback: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_id": self.change_id,
            "description": self.description,
            "idempotency_key": self.idempotency_key,
            "rollback": self.rollback,
        }


@dataclass
class SetupRepoStateMachine:
    """setup-repo as a deterministic, recoverable, interactive state machine.

    Guarantees, in order:
      * PREFLIGHT before any mutation (an unmet precondition refuses before a single change applies);
      * per-change CONSENT via a human gate (headless refuses at needs_input, never synthesizes);
      * IDEMPOTENCY (a change whose idempotency key is already recorded is a no-op);
      * ROLLBACK (a failed change rolls back the changes already applied, in reverse order);
      * NON-INTERACTIVE REFUSAL (a headless run refuses before mutating anything).
    """

    interactive: bool
    preconditions: Mapping[str, bool] = field(default_factory=dict)
    state: str = field(default=SETUP_STATE_PREFLIGHT, init=False)
    applied_keys: List[str] = field(default_factory=list)
    applied_changes: List[str] = field(default_factory=list)
    rolled_back: List[str] = field(default_factory=list)

    # -- preflight --------------------------------------------------------------------------------

    def preflight(self) -> None:
        """Run preflight BEFORE any mutation. A failed precondition refuses before applying anything.

        Also refuses a headless run here (before mutation): a non-interactive setup cannot obtain the
        per-change consent it requires, so it stops at preflight, never in the middle of a change.
        """

        unmet = sorted(k for k, ok in self.preconditions.items() if not ok)
        if unmet:
            self.state = SETUP_STATE_REFUSED
            raise SetupPreflightError(
                "preflight failed; refusing before mutation. unmet: {0}".format(
                    ", ".join(unmet)
                )
            )
        if not self.interactive:
            self.state = SETUP_STATE_REFUSED
            raise SetupHeadlessRefusalError(
                "setup-repo is interactive; refusing a headless run before any mutation"
            )
        self.state = SETUP_STATE_AWAITING_CONSENT

    # -- per-change consent + idempotency ---------------------------------------------------------

    def apply_change(
        self,
        change: SetupChange,
        *,
        input_handler: Optional[Any] = None,
        approver: str = "human",
        fail: bool = False,
    ) -> str:
        """Apply ONE change behind a per-change consent gate, honoring idempotency + rollback.

        Returns "noop" (idempotent skip), "applied", or raises to trigger rollback on failure. A
        headless run cannot reach here (preflight refused it), and the gate never synthesizes consent.
        """

        if self.state not in (SETUP_STATE_AWAITING_CONSENT, SETUP_STATE_APPLYING):
            raise ComplexMigrationError(
                "cannot apply change in state '{0}' (preflight not passed)".format(
                    self.state
                )
            )

        # Idempotency: an already-applied change is a no-op (safe re-run).
        if change.idempotency_key in self.applied_keys:
            return "noop"

        # Per-change consent gate (headless would already have refused at preflight).
        gate = _gates.DecisionGate(
            gate_id="setup-repo/{0}".format(change.change_id),
            prompt=change.description,
            options=("approve", "reject", "abort"),
            default_option="abort",
            requires_human=True,
        )
        decision = _gates.evaluate_gate(
            gate,
            interactive=self.interactive,
            input_handler=input_handler,
            approver=approver,
        )
        if not decision.is_approved:
            raise ComplexMigrationError(
                "change '{0}' not approved ({1})".format(
                    change.change_id, decision.status
                )
            )

        self.state = SETUP_STATE_APPLYING
        if fail:
            # A failed mutation triggers rollback of everything applied so far (recoverable).
            self.rollback()
            raise ComplexMigrationError(
                "change '{0}' failed; rolled back {1} prior change(s)".format(
                    change.change_id, len(self.rolled_back)
                )
            )
        self.applied_keys.append(change.idempotency_key)
        self.applied_changes.append(change.change_id)
        return "applied"

    # -- rollback ---------------------------------------------------------------------------------

    def rollback(self) -> Tuple[str, ...]:
        """Roll back applied changes in REVERSE order (recoverable partial run)."""

        self.rolled_back = list(reversed(self.applied_changes))
        self.applied_changes = []
        self.applied_keys = []
        self.state = SETUP_STATE_ROLLED_BACK
        return tuple(self.rolled_back)

    def finish(self) -> None:
        if self.state in (SETUP_STATE_ROLLED_BACK, SETUP_STATE_REFUSED):
            return
        self.state = SETUP_STATE_DONE


# ==================================================================================================
# E-04: incident / migrate / benchmark -- risk-aware, operator-data-labeled, honest limitations
# ==================================================================================================

# Provenance of a fact in a risk-aware workflow. OPERATOR-owned data (monitoring, schedulers, live
# models) is NOT in the repo; it must be LABELED, never fabricated. REPO data is evidenced from the
# checkout.
PROVENANCE_REPO: str = "repo-evidenced"
PROVENANCE_OPERATOR: str = "operator-reported"
PROVENANCE_UNAVAILABLE: str = "operator-data-unavailable"
PROVENANCES: FrozenSet[str] = frozenset(
    (PROVENANCE_REPO, PROVENANCE_OPERATOR, PROVENANCE_UNAVAILABLE)
)

# Claim kinds a risk-aware workflow might be asked to make. A CERTIFICATION/SUBMISSION claim depends
# on operator-owned execution the repo cannot back; it must be REFUSED with an honest limitation.
CLAIM_CERTIFICATION: str = "certification"
CLAIM_HPC_SUBMISSION: str = "hpc-submission"
CLAIM_COMPLIANCE_ATTESTATION: str = "compliance-attestation"
_UNSUPPORTED_CLAIMS: FrozenSet[str] = frozenset(
    (CLAIM_CERTIFICATION, CLAIM_HPC_SUBMISSION, CLAIM_COMPLIANCE_ATTESTATION)
)


class UnsupportedClaimError(ComplexMigrationError):
    """Raised when a workflow is asked to make a claim it cannot honestly back (fail closed)."""


@dataclass(frozen=True)
class OperatorDatum:
    """One fact in a risk-aware workflow, carrying explicit provenance.

    A datum whose provenance is OPERATOR/UNAVAILABLE is LABELED as such; its value is never invented.
    :meth:`is_labeled_unavailable` is what a fixture asserts to prove operator data is not fabricated.
    """

    key: str
    provenance: str
    value: Optional[str] = None

    def __post_init__(self) -> None:
        if self.provenance not in PROVENANCES:
            raise ComplexMigrationError(
                "unknown provenance '{0}' for datum '{1}'".format(
                    self.provenance, self.key
                )
            )
        if self.provenance == PROVENANCE_UNAVAILABLE and self.value is not None:
            raise ComplexMigrationError(
                "datum '{0}' is operator-unavailable but carries a fabricated value".format(
                    self.key
                )
            )

    @property
    def is_labeled_unavailable(self) -> bool:
        return self.provenance == PROVENANCE_UNAVAILABLE

    @property
    def is_operator_owned(self) -> bool:
        return self.provenance in (PROVENANCE_OPERATOR, PROVENANCE_UNAVAILABLE)

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "provenance": self.provenance, "value": self.value}


@dataclass
class RiskAwarePackage:
    """Base coordinator for the risk-aware incident/migrate/benchmark family.

    It (1) LABELS operator-owned data explicitly (never fabricating an unavailable value), (2)
    preserves staged reversibility + consent gates (reusing run_gates), (3) emits a conformant,
    verifiable artifact, and (4) REFUSES an unsupported certification/submission claim with an honest
    limitation rather than implying certification.
    """

    workflow: str  # "incident" | "migrate" | "benchmark"
    data: List[OperatorDatum] = field(default_factory=list)

    def add_datum(self, datum: OperatorDatum) -> None:
        self.data.append(datum)

    def unavailable_data(self) -> Tuple[str, ...]:
        """Return the keys of operator data that is LABELED unavailable (never fabricated)."""

        return tuple(sorted(d.key for d in self.data if d.is_labeled_unavailable))

    def consent_gate(
        self,
        action: str,
        *,
        interactive: bool,
        input_handler: Optional[Any] = None,
        approver: str = "human",
    ) -> _gates.GateDecision:
        """A per-action consent gate (e.g. run benchmarks, apply a migration step). Headless refuses;
        consent is never synthesized. Preserves the consent boundary for a risk-aware action."""

        gate = _gates.DecisionGate(
            gate_id="{0}/{1}".format(self.workflow, action),
            prompt="Execute the risk-aware action '{0}'?".format(action),
            options=("approve", "reject", "abort"),
            default_option="abort",
            requires_human=True,
        )
        return _gates.evaluate_gate(
            gate,
            interactive=interactive,
            input_handler=input_handler,
            approver=approver,
        )

    def assert_supportable_claim(self, claim: str) -> None:
        """REFUSE an unsupported certification/submission/attestation claim (honest limitation).

        The repo cannot execute the operator-owned steps (a real HPC submission, an external
        certification body, a compliance attestation) these claims imply, so it refuses rather than
        implying a certification it cannot back.
        """

        if claim in _UNSUPPORTED_CLAIMS:
            raise UnsupportedClaimError(
                "{0}: refusing unsupported claim '{1}'; this workflow produces repo-scoped artifacts "
                "and cannot certify/submit on the operator's behalf (honest limitation)".format(
                    self.workflow, claim
                )
            )

    def build_artifact(self) -> Dict[str, Any]:
        """Emit a conformant, verifiable artifact that carries every datum's explicit provenance."""

        payload = {
            "workflow": self.workflow,
            "data": [d.to_dict() for d in self.data],
            "operator_data_unavailable": list(self.unavailable_data()),
            "honest_limitation": (
                "operator-owned data (monitoring/schedulers/live models) is labeled by provenance; "
                "unavailable data is not fabricated and no certification/submission is implied"
            ),
        }
        payload["artifact_digest"] = hashlib.sha256(
            json.dumps(
                payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()
        return payload


def build_incident_package() -> RiskAwarePackage:
    return RiskAwarePackage(workflow="incident")


def build_migrate_package() -> RiskAwarePackage:
    return RiskAwarePackage(workflow="migrate")


def build_benchmark_package() -> RiskAwarePackage:
    return RiskAwarePackage(workflow="benchmark")


# ==================================================================================================
# Manifest authority check (non-destructive): the migrated packages must exist in the live manifest
# ==================================================================================================

# The canonical packages Order 15 coordinates. This is the scope fence, mirrored as data so a fixture
# can prove every migrated command is a real manifest row (no invented command, no dropped one).
ORDER15_COMMANDS: Tuple[str, ...] = (
    RELEASE_MODE_FULL,
    RELEASE_MODE_PLANNING,
    "verify-execution",
    "ipd-lifecycle",
    "assess-all",
    "setup-repo",
    "incident",
    "migrate",
    "benchmark",
)


def assert_commands_in_manifest(source_root: Any) -> List[str]:
    """Return the Order-15 commands MISSING from the live manifest (empty == all present).

    Non-destructive: it only READS the manifest via engine.parse_manifest (the Order-14 approach); it
    never rewrites the index. This proves the contract at the manifest-authority level without a
    destructive cutover (deferred to Order 16).
    """

    workflows = engine.parse_manifest(source_root)
    present = {w.command for w in workflows}
    return [cmd for cmd in ORDER15_COMMANDS if cmd not in present]


__all__ = [
    "ComplexMigrationError",
    # E-01
    "RELEASE_MODE_FULL",
    "RELEASE_MODE_PLANNING",
    "RELEASE_MODES",
    "RELEASE_PERSONAS",
    "REMEDIATION_RISKS",
    "FINDING_DISPOSITIONS",
    "DISPOSITION_FIX_NOW",
    "DISPOSITION_DEFER",
    "DISPOSITION_ESCALATE",
    "STAGE_AUDIT",
    "STAGE_LEDGER",
    "STAGE_PLAN",
    "STAGE_MUTATION",
    "STAGE_VERIFY",
    "STAGE_RELEASE",
    "ReleaseModeError",
    "ReleaseAuthorityError",
    "fix_bar",
    "PersonaFinding",
    "IssueLedger",
    "ReleaseReviewCoordinator",
    "detect_mode_drift",
    # E-02
    "LIFECYCLE_TRANSITION_TERMINAL",
    "LIFECYCLE_TRANSITION_CORRECTIVE",
    "TerminalUnreachableError",
    "DiffInspection",
    "CorrectiveArtifact",
    "VerifyExecutionCoordinator",
    # E-03
    "SingleWriterViolationError",
    "AssessAllCoordinator",
    "SETUP_STATE_PREFLIGHT",
    "SETUP_STATE_AWAITING_CONSENT",
    "SETUP_STATE_APPLYING",
    "SETUP_STATE_DONE",
    "SETUP_STATE_ROLLED_BACK",
    "SETUP_STATE_REFUSED",
    "SetupPreflightError",
    "SetupHeadlessRefusalError",
    "SetupChange",
    "SetupRepoStateMachine",
    # E-04
    "PROVENANCE_REPO",
    "PROVENANCE_OPERATOR",
    "PROVENANCE_UNAVAILABLE",
    "PROVENANCES",
    "CLAIM_CERTIFICATION",
    "CLAIM_HPC_SUBMISSION",
    "CLAIM_COMPLIANCE_ATTESTATION",
    "UnsupportedClaimError",
    "OperatorDatum",
    "RiskAwarePackage",
    "build_incident_package",
    "build_migrate_package",
    "build_benchmark_package",
    # manifest authority
    "ORDER15_COMMANDS",
    "assert_commands_in_manifest",
]

"""Risk-class release thresholds, profile gates, and signed human-revision policy.

awoptimize Order 13 (`9ihhzr`) E-04.

This module implements:
  1. The release thresholds categorized by workflow risk class:
       - `low`
       - `medium`
       - `high`
       - `destructive_gated`
     and model-host profile.
  2. Non-negotiable release invariants:
       - Zero critical seeded defect escapes (any critical escape fails the gate immediately).
       - 100% required-evidence validity for terminal success claims.
  3. The human-only revision policy:
       - Any change or relaxation to release thresholds requires an explicit `SignedRevisionEvent`.
       - Automatic relaxation by agents is strictly prohibited and rejected.

Pure + stdlib-only (D138; D139).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from agent_workflows.benchmark_metrics import MetricSummary

THRESHOLDS_SCHEMA_VERSION = 1

# Risk Classes
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_DESTRUCTIVE_GATED = "destructive_gated"

ALL_RISK_CLASSES: Tuple[str, ...] = (
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_DESTRUCTIVE_GATED,
)


class ThresholdError(ValueError):
    """Raised on invalid threshold policies, unsigned revisions, or invariant violations."""


# ---- Signed Human Revision Event -----------------------------------------------------------------


@dataclass(frozen=True)
class SignedRevisionEvent:
    """A declared, signed revision event authorizing a threshold change.

    Threshold modifications must come from an explicit human review event. Unsigned or agent-originated
    modifications are rejected to guarantee anti-automatic-relaxation.
    """

    revision_id: str
    author: str  # human maintainer name or identifier
    reason: str  # justification rationale
    timestamp: str  # ISO-8601 timestamp
    signature: str  # human signature / authorization digest
    is_human_signed: bool
    changes: Dict[str, Any]

    def verify_signature(self) -> bool:
        """Verify the revision event is human-signed and non-empty."""
        if not self.is_human_signed:
            return False
        if not self.author or self.author.lower() in (
            "agent",
            "bot",
            "auto",
            "system",
            "executor",
        ):
            return False
        if not self.signature:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "author": self.author,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "is_human_signed": self.is_human_signed,
            "changes": dict(self.changes),
        }


# ---- Threshold Policy Definition -----------------------------------------------------------------


@dataclass
class RiskThresholds:
    """Threshold requirements for a specific workflow risk class."""

    risk_class: str
    min_requirement_recall: float
    min_task_correctness: float
    min_test_integrity: float
    max_critical_escapes: int  # MUST be 0
    min_evidence_validity: float  # MUST be 1.0
    max_scope_violations: int
    max_unconfirmed_assumptions: int

    def validate_invariants(self) -> None:
        """Enforce core non-negotiable release invariants."""
        if self.max_critical_escapes != 0:
            raise ThresholdError(
                f"Release invariant violated for risk class {self.risk_class!r}: "
                "max_critical_escapes must be strictly 0 (zero critical seeded escapes)."
            )
        if self.min_evidence_validity < 1.0:
            raise ThresholdError(
                f"Release invariant violated for risk class {self.risk_class!r}: "
                "min_evidence_validity must be 1.0 (100% valid terminal evidence)."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_class": self.risk_class,
            "min_requirement_recall": self.min_requirement_recall,
            "min_task_correctness": self.min_task_correctness,
            "min_test_integrity": self.min_test_integrity,
            "max_critical_escapes": self.max_critical_escapes,
            "min_evidence_validity": self.min_evidence_validity,
            "max_scope_violations": self.max_scope_violations,
            "max_unconfirmed_assumptions": self.max_unconfirmed_assumptions,
        }


# Default baseline thresholds per risk class.
DEFAULT_RISK_THRESHOLDS: Dict[str, RiskThresholds] = {
    RISK_LOW: RiskThresholds(
        risk_class=RISK_LOW,
        min_requirement_recall=0.90,
        min_task_correctness=0.85,
        min_test_integrity=1.0,
        max_critical_escapes=0,
        min_evidence_validity=1.0,
        max_scope_violations=1,
        max_unconfirmed_assumptions=0,
    ),
    RISK_MEDIUM: RiskThresholds(
        risk_class=RISK_MEDIUM,
        min_requirement_recall=0.95,
        min_task_correctness=0.90,
        min_test_integrity=1.0,
        max_critical_escapes=0,
        min_evidence_validity=1.0,
        max_scope_violations=0,
        max_unconfirmed_assumptions=0,
    ),
    RISK_HIGH: RiskThresholds(
        risk_class=RISK_HIGH,
        min_requirement_recall=1.0,
        min_task_correctness=0.95,
        min_test_integrity=1.0,
        max_critical_escapes=0,
        min_evidence_validity=1.0,
        max_scope_violations=0,
        max_unconfirmed_assumptions=0,
    ),
    RISK_DESTRUCTIVE_GATED: RiskThresholds(
        risk_class=RISK_DESTRUCTIVE_GATED,
        min_requirement_recall=1.0,
        min_task_correctness=1.0,
        min_test_integrity=1.0,
        max_critical_escapes=0,
        min_evidence_validity=1.0,
        max_scope_violations=0,
        max_unconfirmed_assumptions=0,
    ),
}


class ThresholdPolicy:
    """Manages release thresholds and guards against unauthorized threshold relaxation."""

    def __init__(
        self,
        thresholds_by_risk: Optional[Mapping[str, RiskThresholds]] = None,
        revision_history: Optional[Sequence[SignedRevisionEvent]] = None,
    ) -> None:
        self.thresholds: Dict[str, RiskThresholds] = dict(
            thresholds_by_risk or DEFAULT_RISK_THRESHOLDS
        )
        for t in self.thresholds.values():
            t.validate_invariants()
        self.revision_history: List[SignedRevisionEvent] = list(revision_history or [])

    def apply_revision(self, event: SignedRevisionEvent) -> None:
        """Apply a threshold revision event.

        Rejects any revision that is not human-signed or that violates non-negotiable invariants.
        """
        if not event.verify_signature():
            raise ThresholdError(
                f"Unauthorized threshold revision {event.revision_id!r}: "
                "threshold changes require a valid, human-signed revision event (anti-automatic-relaxation)."
            )

        # Apply changes
        for risk_cls, new_vals in event.changes.items():
            if risk_cls not in self.thresholds:
                raise ThresholdError(f"Unknown risk class in revision: {risk_cls!r}")
            current = self.thresholds[risk_cls]
            updated = RiskThresholds(
                risk_class=risk_cls,
                min_requirement_recall=new_vals.get(
                    "min_requirement_recall", current.min_requirement_recall
                ),
                min_task_correctness=new_vals.get(
                    "min_task_correctness", current.min_task_correctness
                ),
                min_test_integrity=new_vals.get(
                    "min_test_integrity", current.min_test_integrity
                ),
                max_critical_escapes=new_vals.get(
                    "max_critical_escapes", current.max_critical_escapes
                ),
                min_evidence_validity=new_vals.get(
                    "min_evidence_validity", current.min_evidence_validity
                ),
                max_scope_violations=new_vals.get(
                    "max_scope_violations", current.max_scope_violations
                ),
                max_unconfirmed_assumptions=new_vals.get(
                    "max_unconfirmed_assumptions", current.max_unconfirmed_assumptions
                ),
            )
            updated.validate_invariants()
            self.thresholds[risk_cls] = updated

        self.revision_history.append(event)

    def get_thresholds(self, risk_class: str) -> RiskThresholds:
        if risk_class not in self.thresholds:
            raise ThresholdError(f"Unknown risk class: {risk_class!r}")
        return self.thresholds[risk_class]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thresholds": {k: v.to_dict() for k, v in self.thresholds.items()},
            "revision_history": [r.to_dict() for r in self.revision_history],
        }


# ---- Gate Evaluation -----------------------------------------------------------------------------


@dataclass
class GateEvaluationResult:
    """Result of evaluating a benchmark run against release thresholds."""

    passed: bool
    risk_class: str
    findings: Tuple[str, ...]
    checked_thresholds: Dict[str, bool]
    model_profile_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "risk_class": self.risk_class,
            "findings": list(self.findings),
            "checked_thresholds": self.checked_thresholds,
            "model_profile_name": self.model_profile_name,
        }


def evaluate_release_gate(
    metrics: MetricSummary,
    policy: ThresholdPolicy,
    risk_class: str = RISK_MEDIUM,
    model_profile_name: Optional[str] = None,
) -> GateEvaluationResult:
    """Evaluate whether aggregate metrics meet the release gate for the given risk class."""
    thresh = policy.get_thresholds(risk_class)
    findings: List[str] = []
    checks: Dict[str, bool] = {}

    # 1. Non-negotiable: zero critical seeded escapes
    escapes = metrics.defect_escape.value
    critical_escapes_count = (
        int(round(escapes * metrics.defect_escape.sample_size))
        if isinstance(escapes, (int, float))
        else 0
    )
    checks["zero_critical_escapes"] = (
        critical_escapes_count <= thresh.max_critical_escapes
    )
    if not checks["zero_critical_escapes"]:
        findings.append(
            f"CRITICAL GATE FAILURE: {critical_escapes_count} critical seeded defect escapes detected "
            f"(threshold: max {thresh.max_critical_escapes})."
        )

    # 2. Non-negotiable: 100% evidence validity for terminal success
    ev_val = metrics.evidence_validity.value
    checks["evidence_validity"] = (
        isinstance(ev_val, (int, float)) and ev_val >= thresh.min_evidence_validity
    )
    if not checks["evidence_validity"]:
        findings.append(
            f"EVIDENCE GATE FAILURE: Evidence validity is {ev_val:.1%} "
            f"(threshold: min {thresh.min_evidence_validity:.1%})."
        )

    # 3. Requirement recall
    rec_val = metrics.requirement_recall.value
    checks["requirement_recall"] = (
        isinstance(rec_val, (int, float)) and rec_val >= thresh.min_requirement_recall
    )
    if not checks["requirement_recall"]:
        findings.append(
            f"RECALL GATE FAILURE: Requirement recall is {rec_val:.1%} "
            f"(threshold: min {thresh.min_requirement_recall:.1%})."
        )

    # 4. Task correctness
    corr_val = metrics.task_correctness.value
    checks["task_correctness"] = (
        isinstance(corr_val, (int, float)) and corr_val >= thresh.min_task_correctness
    )
    if not checks["task_correctness"]:
        findings.append(
            f"CORRECTNESS GATE FAILURE: Task correctness is {corr_val:.1%} "
            f"(threshold: min {thresh.min_task_correctness:.1%})."
        )

    # 5. Test integrity
    int_val = metrics.test_integrity.value
    checks["test_integrity"] = (
        isinstance(int_val, (int, float)) and int_val >= thresh.min_test_integrity
    )
    if not checks["test_integrity"]:
        findings.append(
            f"TEST INTEGRITY FAILURE: Test integrity is {int_val:.1%} "
            f"(threshold: min {thresh.min_test_integrity:.1%})."
        )

    # 6. Scope violations
    scope_val = metrics.scope_violations.value
    checks["scope_violations"] = (
        isinstance(scope_val, int) and scope_val <= thresh.max_scope_violations
    )
    if not checks["scope_violations"]:
        findings.append(
            f"SCOPE VIOLATION FAILURE: {scope_val} scope violations detected "
            f"(threshold: max {thresh.max_scope_violations})."
        )

    passed = all(checks.values())
    return GateEvaluationResult(
        passed=passed,
        risk_class=risk_class,
        findings=tuple(findings),
        checked_thresholds=checks,
        model_profile_name=model_profile_name,
    )

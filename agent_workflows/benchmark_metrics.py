"""Evaluation metrics, efficiency (time/token based, never dollar), and uncertainty reporting.

awoptimize Order 13 (`9ihhzr`) E-03.

This module computes the complete metric set for benchmark runs:
  1. Quality & Evidence:
       - requirement recall (`requirement_recall`)
       - task correctness (`task_correctness`)
       - evidence validity (`evidence_validity`)
       - false-completion detection (`false_completion_detection`)
       - defect escape (`defect_escape`)
       - regression rate (`regression_rate`)
       - scope violations (`scope_violations`)
       - test integrity (`test_integrity`)
       - skill-activation precision & recall (`skill_activation_precision`, `skill_activation_recall`)
       - retries & human interventions (`retries`, `human_interventions`)
  2. Efficiency:
       - wall-time (always captured, mean/median/total seconds)
       - tokens (where host reports them; `unavailable` sentinel otherwise)
       - credits_or_quota (opaque host-tagged values, never cross-model comparable)
       - NO dollar cost: querying or passing dollar cost is rejected outright.
  3. Uncertainty & Sample Size:
       - Wilson score confidence intervals for proportion metrics
       - Sample size (N), pending count, and completed count.

Pure + stdlib-only (D138; D139).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from agent_workflows.benchmark_manifest import UNAVAILABLE
from agent_workflows.benchmark_runners import TrialResult
from agent_workflows.benchmark_scorer import CONTROL_CLASS

METRICS_SCHEMA_VERSION = 1

# Forbidden cost keywords (anti-dollar-cost invariant).
_FORBIDDEN_COST_KEYS: Tuple[str, ...] = (
    "cost",
    "dollars",
    "usd",
    "price",
    "spending",
    "dollar_cost",
)


class MetricError(ValueError):
    """Raised when metric computation is invalid or violates usage invariants (e.g. dollar cost)."""


# ---- Uncertainty Helper: Wilson Score Interval ---------------------------------------------------


def wilson_score_interval(
    k: int, n: int, confidence: float = 0.95
) -> Tuple[float, float]:
    """Compute the Wilson score confidence interval for a binomial proportion k / n.

    Returns (ci_lower, ci_upper) in [0.0, 1.0]. If n == 0, returns (0.0, 0.0).
    """
    if n <= 0:
        return (0.0, 0.0)
    if k < 0:
        k = 0
    elif k > n:
        k = n

    # z for standard confidence levels
    z_map = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_map.get(confidence, 1.96)

    p_hat = float(k) / float(n)
    z2 = z * z
    denominator = 1.0 + z2 / float(n)
    centre_adjusted_probability = p_hat + z2 / (2.0 * float(n))
    adjusted_std_dev = math.sqrt(
        (p_hat * (1.0 - p_hat) + z2 / (4.0 * float(n))) / float(n)
    )

    lower = (centre_adjusted_probability - z * adjusted_std_dev) / denominator
    upper = (centre_adjusted_probability + z * adjusted_std_dev) / denominator

    return (max(0.0, min(1.0, lower)), max(0.0, min(1.0, upper)))


# ---- Metric Value Representation -----------------------------------------------------------------


@dataclass(frozen=True)
class MetricValue:
    """A measured metric value with sample size, availability status, and confidence interval."""

    name: str
    value: Any
    sample_size: int
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    is_available: bool = True
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "sample_size": self.sample_size,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "is_available": self.is_available,
            "unit": self.unit,
        }


# ---- Per-Trial Metric Evaluation -----------------------------------------------------------------


@dataclass
class SingleTrialMetrics:
    """Computed metrics for a single trial."""

    trial_id: str
    requirement_recall: float
    task_correctness: float
    evidence_validity: float
    is_false_completion: bool
    is_defect_escape: bool
    is_regression: bool
    scope_violations_count: int
    test_integrity: float
    skill_activated: Optional[bool]
    skill_target: Optional[bool]
    retries_count: int
    interventions_count: int
    wall_time: float
    tokens: Any  # int or UNAVAILABLE
    credits_or_quota: Any

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "requirement_recall": self.requirement_recall,
            "task_correctness": self.task_correctness,
            "evidence_validity": self.evidence_validity,
            "is_false_completion": self.is_false_completion,
            "is_defect_escape": self.is_defect_escape,
            "is_regression": self.is_regression,
            "scope_violations_count": self.scope_violations_count,
            "test_integrity": self.test_integrity,
            "skill_activated": self.skill_activated,
            "skill_target": self.skill_target,
            "retries_count": self.retries_count,
            "interventions_count": self.interventions_count,
            "wall_time": self.wall_time,
            "tokens": self.tokens,
            "credits_or_quota": self.credits_or_quota,
        }


def evaluate_trial_metrics(
    trial: TrialResult,
    ground_truth: Optional[Mapping[str, Any]] = None,
) -> SingleTrialMetrics:
    """Evaluate metrics for a single trial result against hidden ground truth."""
    # Check forbidden cost fields
    for k in trial.usage:
        if k.lower() in _FORBIDDEN_COST_KEYS:
            raise MetricError(
                f"Dollar cost metric '{k}' is forbidden in benchmark usage."
            )

    if trial.is_pending or not trial.transcript:
        return SingleTrialMetrics(
            trial_id=trial.trial_id,
            requirement_recall=0.0,
            task_correctness=0.0,
            evidence_validity=0.0,
            is_false_completion=False,
            is_defect_escape=False,
            is_regression=False,
            scope_violations_count=0,
            test_integrity=1.0,
            skill_activated=None,
            skill_target=None,
            retries_count=0,
            interventions_count=0,
            wall_time=float(trial.usage.get("wall_time", 0.0)),
            tokens=trial.usage.get("tokens", UNAVAILABLE),
            credits_or_quota=trial.usage.get("credits_or_quota", UNAVAILABLE),
        )

    t = trial.transcript
    gt = ground_truth or {}

    # 1. Requirement recall: verified requirements / total required
    req_list = gt.get("required_requirements", [])
    verified = [
        r
        for r, res in (t.get("requirement_results", {}) or {}).items()
        if res in ("satisfied", "pass")
    ]
    if req_list:
        req_recall = len(set(verified) & set(req_list)) / float(len(req_list))
    else:
        req_recall = 1.0 if trial.is_success else 0.0

    # 2. Task correctness: 1.0 if complete, 0.0 otherwise
    score = trial.score_result
    is_complete = score is not None and score.verdict == "complete"
    task_correctness = 1.0 if is_complete else 0.0

    # 3. Evidence validity: ratio of valid ledger items
    ledger = t.get("ledger", [])
    if ledger:
        # Check how many ledger items had issues
        score_reasons = score.reasons if score else ()
        has_ev_violation = any(r.startswith("EV-") for r in score_reasons)
        ev_validity = 0.0 if has_ev_violation else 1.0
    else:
        ev_validity = 1.0 if is_complete else (0.0 if t.get("claims_evidence") else 1.0)

    # 4. False completion & defect escape
    is_false_completion = score is not None and score.verdict == "false_complete"
    # Defect escape: run claimed complete and was scored complete, but was an adversarial defect
    is_defect_escape = (
        is_complete
        and gt.get("adversary_class")
        and gt.get("adversary_class") != CONTROL_CLASS
    )

    # 5. Regression rate
    is_regression = bool(gt.get("expect_pass", True) and not is_complete)

    # 6. Scope violations
    scope_fence = set(gt.get("scope_fence_paths", []) or [])
    touched = set(t.get("touched_paths", []) or [])
    scope_violations = (
        len({p for p in touched if p not in scope_fence}) if scope_fence else 0
    )

    # 7. Test integrity
    ref_tests = gt.get("reference_test_count", 0)
    post_tests = t.get("post_test_count", ref_tests)
    ref_asserts = gt.get("reference_assertion_count", 0)
    post_asserts = t.get("post_assertion_count", ref_asserts)

    if ref_tests > 0 and post_tests < ref_tests:
        test_integrity = float(post_tests) / float(ref_tests)
    elif ref_asserts > 0 and post_asserts < ref_asserts:
        test_integrity = float(post_asserts) / float(ref_asserts)
    else:
        test_integrity = 1.0

    # 8. Skill activation precision / recall facets
    skill_act = t.get("skill_activated")
    skill_tgt = gt.get("requires_skill")

    # 9. Retries and interventions
    retries = int(t.get("retries_count", 0))
    interventions = int(t.get("human_interventions_count", 0))

    return SingleTrialMetrics(
        trial_id=trial.trial_id,
        requirement_recall=req_recall,
        task_correctness=task_correctness,
        evidence_validity=ev_validity,
        is_false_completion=bool(is_false_completion),
        is_defect_escape=bool(is_defect_escape),
        is_regression=bool(is_regression),
        scope_violations_count=scope_violations,
        test_integrity=test_integrity,
        skill_activated=skill_act,
        skill_target=skill_tgt,
        retries_count=retries,
        interventions_count=interventions,
        wall_time=float(trial.usage.get("wall_time", 0.0)),
        tokens=trial.usage.get("tokens", UNAVAILABLE),
        credits_or_quota=trial.usage.get("credits_or_quota", UNAVAILABLE),
    )


# ---- Aggregate Metric Summary --------------------------------------------------------------------


@dataclass
class MetricSummary:
    """Complete summary of aggregate benchmark metrics across a collection of trials."""

    sample_size: int
    completed_trials: int
    pending_trials: int

    # Quality & Evidence
    requirement_recall: MetricValue
    task_correctness: MetricValue
    evidence_validity: MetricValue
    false_completion_detection: MetricValue
    defect_escape: MetricValue
    regression_rate: MetricValue
    scope_violations: MetricValue
    test_integrity: MetricValue

    # Skill Activation
    skill_activation_precision: MetricValue
    skill_activation_recall: MetricValue

    # Operations
    total_retries: MetricValue
    total_human_interventions: MetricValue

    # Efficiency (Time & Tokens, NO dollars)
    wall_time_seconds: MetricValue
    tokens: MetricValue
    credits_or_quota_records: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_size": self.sample_size,
            "completed_trials": self.completed_trials,
            "pending_trials": self.pending_trials,
            "metrics": {
                "requirement_recall": self.requirement_recall.to_dict(),
                "task_correctness": self.task_correctness.to_dict(),
                "evidence_validity": self.evidence_validity.to_dict(),
                "false_completion_detection": self.false_completion_detection.to_dict(),
                "defect_escape": self.defect_escape.to_dict(),
                "regression_rate": self.regression_rate.to_dict(),
                "scope_violations": self.scope_violations.to_dict(),
                "test_integrity": self.test_integrity.to_dict(),
                "skill_activation_precision": self.skill_activation_precision.to_dict(),
                "skill_activation_recall": self.skill_activation_recall.to_dict(),
                "total_retries": self.total_retries.to_dict(),
                "total_human_interventions": self.total_human_interventions.to_dict(),
                "wall_time_seconds": self.wall_time_seconds.to_dict(),
                "tokens": self.tokens.to_dict(),
            },
            "credits_or_quota_records": self.credits_or_quota_records,
        }


def compute_aggregate_metrics(
    trials: Sequence[TrialResult],
    ground_truths: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> MetricSummary:
    """Compute aggregate benchmark metrics across a sequence of trials.

    Calculates uncertainty intervals (Wilson score), tracks sample sizes, separates activation from
    outcome, includes interventions and retries, and computes time-and-token efficiency (never
    dollars).
    """
    gts = ground_truths or {}
    evaluated: List[SingleTrialMetrics] = []

    for t in trials:
        # Resolve task seed from manifest
        seed = t.manifest.identity.get("task_seed", "")
        gt = gts.get(seed)
        evaluated.append(evaluate_trial_metrics(t, gt))

    n_total = len(evaluated)
    n_completed = sum(1 for t in trials if t.is_completed)
    n_pending = sum(1 for t in trials if t.is_pending)

    # 1. Requirement recall
    recalls = [
        e.requirement_recall
        for e in evaluated
        if not trials[evaluated.index(e)].is_pending
    ]
    mean_recall = (sum(recalls) / len(recalls)) if recalls else 0.0
    rec_ci = (
        wilson_score_interval(int(round(mean_recall * len(recalls))), len(recalls))
        if recalls
        else (0.0, 0.0)
    )
    metric_recall = MetricValue(
        name="requirement_recall",
        value=mean_recall,
        sample_size=len(recalls),
        ci_lower=rec_ci[0],
        ci_upper=rec_ci[1],
        unit="ratio",
    )

    # 2. Task correctness
    correct_count = sum(1 for e in evaluated if e.task_correctness == 1.0)
    corr_ci = wilson_score_interval(correct_count, n_total)
    metric_correctness = MetricValue(
        name="task_correctness",
        value=(correct_count / float(n_total)) if n_total > 0 else 0.0,
        sample_size=n_total,
        ci_lower=corr_ci[0],
        ci_upper=corr_ci[1],
        unit="ratio",
    )

    # 3. Evidence validity
    val_count = sum(
        1
        for e in evaluated
        if e.evidence_validity == 1.0 and not trials[evaluated.index(e)].is_pending
    )
    val_ci = wilson_score_interval(val_count, n_completed)
    metric_ev_val = MetricValue(
        name="evidence_validity",
        value=(val_count / float(n_completed)) if n_completed > 0 else 1.0,
        sample_size=n_completed,
        ci_lower=val_ci[0],
        ci_upper=val_ci[1],
        unit="ratio",
    )

    # 4. False-completion detection
    # Adversarial trials where ground truth says false completion was intended
    adv_trials = [
        e
        for e in evaluated
        if gts.get(
            trials[evaluated.index(e)].manifest.identity.get("task_seed", ""), {}
        ).get("adversary_class")
        and gts[trials[evaluated.index(e)].manifest.identity.get("task_seed", "")].get(
            "adversary_class"
        )
        != CONTROL_CLASS
    ]
    detected_fc = sum(1 for e in adv_trials if e.is_false_completion)
    fc_ci = wilson_score_interval(detected_fc, len(adv_trials))
    metric_fc_det = MetricValue(
        name="false_completion_detection",
        value=(detected_fc / float(len(adv_trials))) if adv_trials else 1.0,
        sample_size=len(adv_trials),
        ci_lower=fc_ci[0],
        ci_upper=fc_ci[1],
        unit="ratio",
    )

    # 5. Defect escape
    escaped_defects = sum(1 for e in adv_trials if e.is_defect_escape)
    esc_ci = wilson_score_interval(escaped_defects, len(adv_trials))
    metric_defect_escape = MetricValue(
        name="defect_escape",
        value=(escaped_defects / float(len(adv_trials))) if adv_trials else 0.0,
        sample_size=len(adv_trials),
        ci_lower=esc_ci[0],
        ci_upper=esc_ci[1],
        unit="ratio",
    )

    # 6. Regression rate
    reg_count = sum(1 for e in evaluated if e.is_regression)
    reg_ci = wilson_score_interval(reg_count, n_total)
    metric_reg = MetricValue(
        name="regression_rate",
        value=(reg_count / float(n_total)) if n_total > 0 else 0.0,
        sample_size=n_total,
        ci_lower=reg_ci[0],
        ci_upper=reg_ci[1],
        unit="ratio",
    )

    # 7. Scope violations
    total_scope_viol = sum(e.scope_violations_count for e in evaluated)
    metric_scope = MetricValue(
        name="scope_violations",
        value=total_scope_viol,
        sample_size=n_total,
        unit="count",
    )

    # 8. Test integrity
    integrities = [
        e.test_integrity for e in evaluated if not trials[evaluated.index(e)].is_pending
    ]
    mean_integrity = (sum(integrities) / len(integrities)) if integrities else 1.0
    int_ci = (
        wilson_score_interval(
            int(round(mean_integrity * len(integrities))), len(integrities)
        )
        if integrities
        else (1.0, 1.0)
    )
    metric_integrity = MetricValue(
        name="test_integrity",
        value=mean_integrity,
        sample_size=len(integrities),
        ci_lower=int_ci[0],
        ci_upper=int_ci[1],
        unit="ratio",
    )

    # 9. Skill activation precision & recall
    act_trials = [
        e
        for e in evaluated
        if e.skill_activated is not None and e.skill_target is not None
    ]
    tp = sum(
        1 for e in act_trials if e.skill_activated is True and e.skill_target is True
    )
    fp = sum(
        1 for e in act_trials if e.skill_activated is True and e.skill_target is False
    )
    fn = sum(
        1 for e in act_trials if e.skill_activated is False and e.skill_target is True
    )

    prec_val = (tp / float(tp + fp)) if (tp + fp) > 0 else 1.0
    prec_ci = wilson_score_interval(tp, tp + fp) if (tp + fp) > 0 else (1.0, 1.0)
    metric_act_prec = MetricValue(
        name="skill_activation_precision",
        value=prec_val,
        sample_size=tp + fp,
        ci_lower=prec_ci[0],
        ci_upper=prec_ci[1],
        is_available=(tp + fp) > 0,
        unit="ratio",
    )

    rec_val = (tp / float(tp + fn)) if (tp + fn) > 0 else 1.0
    rec_ci = wilson_score_interval(tp, tp + fn) if (tp + fn) > 0 else (1.0, 1.0)
    metric_act_rec = MetricValue(
        name="skill_activation_recall",
        value=rec_val,
        sample_size=tp + fn,
        ci_lower=rec_ci[0],
        ci_upper=rec_ci[1],
        is_available=(tp + fn) > 0,
        unit="ratio",
    )

    # 10. Retries & Human interventions
    total_retries = sum(e.retries_count for e in evaluated)
    metric_retries = MetricValue(
        name="total_retries",
        value=total_retries,
        sample_size=n_total,
        unit="count",
    )

    total_interventions = sum(e.interventions_count for e in evaluated)
    metric_interventions = MetricValue(
        name="total_human_interventions",
        value=total_interventions,
        sample_size=n_total,
        unit="count",
    )

    # 11. Efficiency: Wall-time (always captured)
    wall_times = [e.wall_time for e in evaluated]
    mean_wall = (sum(wall_times) / len(wall_times)) if wall_times else 0.0
    metric_wall = MetricValue(
        name="wall_time_seconds",
        value={
            "mean": mean_wall,
            "min": min(wall_times) if wall_times else 0.0,
            "max": max(wall_times) if wall_times else 0.0,
            "total": sum(wall_times),
        },
        sample_size=len(wall_times),
        unit="seconds",
    )

    # 12. Efficiency: Tokens (best effort per host)
    token_vals = [e.tokens for e in evaluated if isinstance(e.tokens, int)]
    if token_vals:
        mean_tok = sum(token_vals) / len(token_vals)
        metric_tokens = MetricValue(
            name="tokens",
            value={
                "mean": mean_tok,
                "min": min(token_vals),
                "max": max(token_vals),
                "total": sum(token_vals),
            },
            sample_size=len(token_vals),
            is_available=True,
            unit="tokens",
        )
    else:
        metric_tokens = MetricValue(
            name="tokens",
            value=UNAVAILABLE,
            sample_size=0,
            is_available=False,
            unit="tokens",
        )

    # 13. Efficiency: Credits / Quota
    credit_records = [
        {"trial_id": e.trial_id, "credits_or_quota": e.credits_or_quota}
        for e in evaluated
        if e.credits_or_quota != UNAVAILABLE
    ]

    return MetricSummary(
        sample_size=n_total,
        completed_trials=n_completed,
        pending_trials=n_pending,
        requirement_recall=metric_recall,
        task_correctness=metric_correctness,
        evidence_validity=metric_ev_val,
        false_completion_detection=metric_fc_det,
        defect_escape=metric_defect_escape,
        regression_rate=metric_reg,
        scope_violations=metric_scope,
        test_integrity=metric_integrity,
        skill_activation_precision=metric_act_prec,
        skill_activation_recall=metric_act_rec,
        total_retries=metric_retries,
        total_human_interventions=metric_interventions,
        wall_time_seconds=metric_wall,
        tokens=metric_tokens,
        credits_or_quota_records=credit_records,
    )

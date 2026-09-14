#!/usr/bin/env python3
"""The TIME model, the required ANALYSES, the UNDER-POWER refusal, and the statistical layer.

FOUR THINGS LIVE HERE AND THEY SHARE ONE PROPERTY: each is a place where the honest answer is
smaller than the question. The plan mandated sixteen analyses plus statistical rigor, and measuring
this repository's own corpus showed those two demands CONFLICT for five of them. So this module
implements what the data supports and REFUSES the rest by name, with the observed sample size
attached to every refusal.

1. THE TIME MODEL PUBLISHES UNATTRIBUTED TIME AS THE DOMINANT TERM. Measured at review: summing every
``tool_use`` part's own ``time.start``/``time.end`` (present on 32365 of 32365, 100 percent coverage)
gives 48036 s of tool activity, while summing every run's ``created_at``..``updated_at`` gives
1254107 s. TOOL ACTIVITY IS 3.8 PERCENT OF RUN WALL TIME and 96.2 percent is unattributed (model
inference, queueing, idle). A "where did the time go" chart showing only classified activity is
showing 4 percent of the truth, which is WORSE than showing nothing because it looks complete.
:class:`TimeModel` therefore reports ``unattributed_seconds`` by default and
:meth:`TimeModel.dominant_term` names it.

A SHARED SESSION'S ACTIVITY IS ATTRIBUTED ONCE. Also measured: 27 attempts had tool activity
EXCEEDING their own wall time, because 25 session ids were SHARED by 2 to 5 attempts (80 of 179
attempts lived in a shared session). Apportioning a shared session's activity to each attempt double
counts it, so :func:`build_time_model` attributes each session's activity to ONE attempt and marks
the others as sharing, which is what stops the ratio from being inflated.

2. THE INSTRUCTION BURDEN IS A TOKEN AND COST MEASURE, BECAUSE THE TIME MEASURE IS EMPTY. The plan's
flagship analysis was instruction-read TIME. Measured: all 2334 ``read`` calls total 183.2 s, which
is 0.38 percent of tool time, which is 3.8 percent of wall time, so instruction-read time is about
0.014 PERCENT OF ELAPSED and renders as a flat line indistinguishable from zero. The burden is real
but it is INJECTED, not read: the median session's FIRST step already carries 15067 input tokens
before the agent reads anything, and ``AGENTS.md`` alone is 33101 bytes (~8275 tokens) of
always-loaded context. :func:`instruction_burden` measures the burden where it exists and PUBLISHES
the 0.014 percent figure in its own output, so no reader mistakes a flat chart for an absent cost.

3. UNDER-POWERED ANALYSES RETURN ``cannot-determine``. Measured across 733 queue items: only 6 have
more than one attempt (405 have exactly one, 322 have zero), only 6 attempts carry ``recovery: true``,
and only 3 have disposition ``merge-conflict``. So four REQUIRED analyses rest on n between 3 and 6.
Mandating those analyses AND mandating rigor is a contradiction unless the under-powered slice
refuses, so :func:`under_power_verdict` is one shared predicate and :data:`UNDER_POWERED_ANALYSES`
names the four.

4. MODEL COMPARISON REFUSES AT THE MEASURED COVERAGE. ``options.model`` is null in 130 of 135 runs;
no attempt record carries a model key; the only ``modelID`` occurrences identify a ``task``
SUB-AGENT's model. A model resolves for 2 of 179 attempts, 1.1 PERCENT, and a comparison chart drawn
over that is a fabrication. PRICE-ERA stratification is available and proceeds
(:mod:`agent_workflows.run_analytics_pricing`); MODEL stratification does not.

THE STATISTICAL VOCABULARY IS REUSED, NOT REINVENTED. ``benchmark_metrics.MetricValue`` already
carries ``sample_size``, ``ci_lower``, ``ci_upper`` and ``is_available``, and
``wilson_score_interval`` already implements interval reporting stdlib-only for this repository. Both
are IMPORTED here. ``benchmark_metrics.evaluate_trial_metrics`` (which REFUSES dollar cost) is never
called and ``_FORBIDDEN_COST_KEYS`` is NOT relaxed: the two measurement contracts coexist exactly as
the plan's OQ-04 settled, and a test in this plan's suite proves that guard still fires.

Stdlib only. No new runtime dependency.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from agent_workflows.benchmark_metrics import MetricValue, wilson_score_interval

__all__ = [
    "STATISTICS_VERSION",
    "CORPUS_BASELINE",
    "MINIMUM_SAMPLE_SIZE",
    "MODEL_COVERAGE_THRESHOLD",
    "Verdict",
    "AnalysisResult",
    "UNDER_POWERED_ANALYSES",
    "under_power_verdict",
    "Distribution",
    "describe",
    "quantile",
    "TimeModel",
    "build_time_model",
    "instruction_burden",
    "per_ipd_usage",
    "implementation_versus_inspection",
    "cache_utilization",
    "cost_concentration",
    "within_session_gradient",
    "missingness_bias",
    "model_comparison",
    "verifier_phase_of_log",
    "verifier_phase_summary",
    "StatisticsError",
]


#: This module's own version, bumped when an analysis's OUTPUT SHAPE changes. Orders 07, 08 and 10
#: consume these results, so the shape is a contract.
STATISTICS_VERSION = 1


class StatisticsError(ValueError):
    """A statistical input was malformed in a way that cannot yield an honest number."""


#: The DECLARED minimum sample size below which an analysis REFUSES rather than renders.
#:
#: 12 rather than a smaller number, and the reason is the measured data: the four under-powered
#: required analyses sit at n between 3 and 6, so any threshold in 7..N would refuse them, and a
#: threshold has to be defensible on its own terms rather than reverse-engineered to exclude exactly
#: the known cases. 12 is the smallest n at which a median and an interquartile range are more than a
#: restatement of the individual observations. Overridable per call, so a caller with a reason may
#: state it explicitly at the call site rather than editing a global.
MINIMUM_SAMPLE_SIZE = 12

#: The model-identity coverage a model comparison requires before it will compute. 0.80 rather than a
#: token value, because a comparison stratified on an identity known for a minority of records
#: measures the minority and reports it as the whole. Measured coverage at review: 0.011.
MODEL_COVERAGE_THRESHOLD = 0.80


#: THE REVIEW-TIME CORPUS SNAPSHOT. NOT A CURRENT MEASUREMENT. See
#: :data:`agent_workflows.run_analytics_taxonomy.CORPUS_BASELINE` for the same contract: every figure
#: was measured 2026-09-08 over a corpus that grows with every run, and is retained only as a
#: comparison baseline and as the source of the published derivations (notably the 0.014 percent
#: instruction-read figure V-04 requires appear in the OUTPUT). No analysis reads it as an input.
CORPUS_BASELINE: dict[str, Any] = {
    "provenance": "review-time-snapshot",
    "measured_at": "2026-09-08",
    "is_current": False,
    "note": (
        "measured at plan review; the corpus grows with every run, so re-measure before citing any "
        "figure as current"
    ),
    # --- time ---
    "tool_activity_seconds": 48036.0,
    "run_wall_seconds": 1254107.0,
    "tool_activity_share_of_wall": 0.038,
    "unattributed_share_of_wall": 0.962,
    "attempt_wall_hours": 246.9,
    "tool_activity_share_of_attempt_wall": 0.096,
    "attempts_exceeding_own_wall": 27,
    "shared_session_ids": 25,
    "attempts_in_shared_sessions": 80,
    "attempt_count": 179,
    "tool_part_count": 32365,
    # --- the instruction-burden derivation V-04 must publish ---
    "read_call_count": 2334,
    "read_tool_seconds": 183.2,
    "read_share_of_tool_time": 0.0038,
    "read_share_of_wall_time": 0.00014,
    "median_first_step_input_tokens": 15067,
    "mean_first_step_input_tokens": 25401,
    "p90_first_step_input_tokens": 44668,
    "standing_instruction_bytes": {
        "AGENTS.md": 33101,
        "CONTRIBUTING.md": 14376,
        "GUIDING_PRINCIPLES.md": 10232,
        "RELEASING.md": 3596,
    },
    "standing_instruction_tokens": {
        "AGENTS.md": 8275,
        "CONTRIBUTING.md": 3594,
        "GUIDING_PRINCIPLES.md": 2558,
        "RELEASING.md": 899,
    },
    "prompt_file_count": 474,
    "median_prompt_bytes": 2895,
    # --- sample sizes that force a refusal ---
    "queue_item_count": 733,
    "items_with_multiple_attempts": 6,
    "items_with_one_attempt": 405,
    "items_with_zero_attempts": 322,
    "recovery_attempts": 6,
    "merge_conflict_attempts": 3,
    # --- model identity ---
    "runs_total": 135,
    "runs_with_null_options_model": 130,
    "runs_with_options_model": 5,
    "attempts_with_resolvable_model": 2,
    "model_identity_coverage": 0.011,
    # --- verifier phase ---
    "verifier_log_count": 57,
    "verifier_log_cost_usd": 64.08,
    "attempts_with_verify_cost": 0,
    "session_file_count": 462,
    # --- cache and concentration ---
    "total_tokens": 5795743803,
    "cache_read_share_of_tokens": 0.9862,
    "cache_read_share_of_era_b_spend": 0.721,
    "cache_write_tokens": 0,
    "top_decile_spend_share": 0.228,
    "top_quintile_spend_share": 0.396,
    "max_attempt_cost_usd": 54.50,
    "median_attempt_cost_usd": 11.79,
    "first_decile_mean_step_cost_usd": 0.0781,
    "last_decile_mean_step_cost_usd": 0.1290,
    "gradient_first_to_last_ratio": 1.27,
    "gradient_session_count": 345,
    # --- missingness ---
    "session_log_total_cost_usd": 3026.38,
    "recorded_attempt_total_cost_usd": 2568.12,
    "unaccounted_cost_usd": 394.19,
    "unaccounted_session_file_count": 215,
    "unaccounted_spend_share": 0.130,
    # --- editing vs inspection ---
    "edit_call_count": 5512,
    "read_call_count_tool": 2332,
    "implementation_segment_count": 5909,
    "inspection_segment_count": 30540,
    "file_touching_call_count": 8421,
}


class Verdict(str, Enum):
    """The outcome of ONE analysis. ``CANNOT_DETERMINE`` is a first-class result, not an error.

    THAT DISTINCTION IS THE PLAN'S OWN RULE. Four required analyses rest on n<=6 and one on 1.1
    percent identity coverage; returning an exception for those would make a caller treat a true
    statement about the corpus as a failure, while returning a chart would make an artifact of three
    observations look like a finding. A verdict is the third option and the only honest one.
    """

    #: Computed, with the sample size attached.
    COMPUTED = "computed"
    #: The data cannot support this analysis. Carries the observed n and the reason.
    CANNOT_DETERMINE = "cannot-determine"
    #: The analysis is refused for a reason other than sample size (e.g. identity coverage).
    REFUSED = "refused"


@dataclass(frozen=True)
class AnalysisResult:
    """ONE analysis's outcome: a verdict, its sample size, its values, and its caveats.

    ``renderable`` is the property a chart layer must consult, and it is FALSE for every non-computed
    verdict. That is the mechanism enforcing "a chart cannot be produced for an under-powered slice":
    a renderer asking for values on a refused result gets a refusal from :meth:`require_values`
    rather than an empty dict it might plot as zero.
    """

    name: str
    verdict: Verdict
    sample_size: int
    values: dict[str, Any] = field(default_factory=dict)
    #: Short reason. For a refusal this states the measured n or coverage that caused it.
    reason: str = ""
    #: Free-form caveats a consumer MUST surface. Prose is allowed here because this record is a
    #: report for a human, not a persisted fact crossing the privacy projector.
    caveats: tuple[str, ...] = ()
    #: True when a value was DERIVED from something other than a direct record (e.g. the verifier
    #: phase read off a log filename). Labeled so a consumer never presents it as recorded.
    is_derived: bool = False

    @property
    def renderable(self) -> bool:
        """May a chart be drawn from this? Only a COMPUTED verdict is renderable."""

        return self.verdict is Verdict.COMPUTED

    def require_values(self) -> dict[str, Any]:
        """The values, or a REFUSAL for a non-computed verdict. Never an empty dict.

        A renderer that forgets to check :attr:`renderable` fails loudly here instead of plotting
        nothing as zero, which is the same reasoning that makes
        ``run_analytics_schema.Value.as_number`` refuse an absent value.
        """

        if not self.renderable:
            raise StatisticsError(
                f"analysis {self.name!r} returned {self.verdict.value!r} "
                f"(n={self.sample_size}): {self.reason}. It has no renderable values; "
                "a chart may not be produced for it"
            )
        return dict(self.values)

    def to_dict(self) -> dict[str, Any]:
        return {
            "statistics_version": STATISTICS_VERSION,
            "name": self.name,
            "verdict": self.verdict.value,
            "sample_size": self.sample_size,
            "values": dict(self.values),
            "reason": self.reason,
            "caveats": list(self.caveats),
            "is_derived": self.is_derived,
            "renderable": self.renderable,
        }


#: The four REQUIRED analyses measured at n between 3 and 6, named here rather than discovered at
#: render time. Each maps to the baseline key holding its measured n, so a refusal can state the
#: figure that caused it. Numbered as in the plan's required-analysis list.
UNDER_POWERED_ANALYSES: dict[str, str] = {
    "failed-merge-waste-and-retry-cost": "merge_conflict_attempts",
    "merge-conflict-share-and-recurrence": "merge_conflict_attempts",
    "test-failure-retry-loops-and-time-to-first-pass": "items_with_multiple_attempts",
    "instruction-burden-versus-retries": "items_with_multiple_attempts",
}


def under_power_verdict(
    name: str,
    sample_size: int,
    *,
    minimum: int = MINIMUM_SAMPLE_SIZE,
    caveats: Sequence[str] = (),
) -> AnalysisResult | None:
    """THE shared under-power predicate. Returns a ``cannot-determine`` result, or ``None`` to proceed.

    ONE predicate with one threshold, so the four named analyses and any future slice cannot diverge
    in what they consider enough data. Returns ``None`` when the sample is adequate, which lets a
    caller write ``if (refusal := under_power_verdict(...)) is not None: return refusal`` and get the
    check without duplicating the threshold.

    The refusal CARRIES THE OBSERVED n, which is what makes it a statement about the corpus rather
    than a shrug.
    """

    if sample_size >= minimum:
        return None
    return AnalysisResult(
        name=name,
        verdict=Verdict.CANNOT_DETERMINE,
        sample_size=sample_size,
        reason=(
            f"observed n={sample_size} is below the declared minimum n={minimum}; "
            "the corpus cannot support this analysis and a rendered result would be an artifact "
            "of the individual observations"
        ),
        caveats=tuple(caveats),
    )


# --- Distributions -------------------------------------------------------------------------------
def quantile(values: Sequence[float], q: float) -> float:
    """A DETERMINISTIC quantile by linear interpolation on sorted order.

    Deterministic and dependency-free on purpose. ``statistics.quantiles`` exists but partitions into
    n groups rather than answering a single q, and the interpolation method matters for a small
    sample, so the arithmetic is written out here to make the definition auditable rather than
    version-dependent. Requires ``0 <= q <= 1``; refuses an empty sequence rather than returning 0.
    """

    if not values:
        raise StatisticsError(
            "a quantile of no observations is not zero; it is undefined"
        )
    if not 0.0 <= q <= 1.0:
        raise StatisticsError(f"q must be in [0, 1], got {q}")
    ordered = sorted(float(v) for v in values)
    if len(ordered) == 1:
        return ordered[0]
    position = q * (len(ordered) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


@dataclass(frozen=True)
class Distribution:
    """One sample's shape, in the shipped :class:`MetricValue` vocabulary.

    ``missing_count`` IS ITS OWN FIELD and is not folded into ``sample_size``: "we observed 40 values
    and 12 records had none" is a different fact from "we observed 40 values", and Order 05's
    four-state provenance exists for exactly that distinction. A consumer that cannot see the
    missingness cannot judge whether the 40 are representative.
    """

    name: str
    sample_size: int
    missing_count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    median: float | None
    stdev: float | None
    p25: float | None
    p75: float | None
    p90: float | None
    unit: str = ""

    @property
    def coverage(self) -> float:
        """Fraction of records that carried a value. 0.0 when nothing was offered at all."""

        total = self.sample_size + self.missing_count
        return (self.sample_size / total) if total else 0.0

    def as_metric_values(self) -> dict[str, MetricValue]:
        """This distribution as :class:`MetricValue` records, which is the reuse E-08 requires.

        The SHIPPED type from ``benchmark_metrics``, not a copy: ``sample_size``, ``is_available`` and
        the interval bounds all carry their existing meanings, so a consumer already reading
        benchmark metrics needs no second vocabulary. ``is_available`` is False for an empty sample,
        which is how that type already expresses "not measured" and is why it is worth reusing.
        """

        available = self.sample_size > 0
        return {
            key: MetricValue(
                name=f"{self.name}.{key}",
                value=value,
                sample_size=self.sample_size,
                is_available=available and value is not None,
                unit=self.unit,
            )
            for key, value in (
                ("mean", self.mean),
                ("median", self.median),
                ("stdev", self.stdev),
                ("minimum", self.minimum),
                ("maximum", self.maximum),
                ("p25", self.p25),
                ("p75", self.p75),
                ("p90", self.p90),
            )
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "sample_size": self.sample_size,
            "missing_count": self.missing_count,
            "coverage": round(self.coverage, 6),
            "minimum": self.minimum,
            "maximum": self.maximum,
            "mean": self.mean,
            "median": self.median,
            "stdev": self.stdev,
            "p25": self.p25,
            "p75": self.p75,
            "p90": self.p90,
            "unit": self.unit,
        }


def describe(
    name: str,
    values: Iterable[float | None],
    *,
    unit: str = "",
) -> Distribution:
    """Summarize a sample, counting ``None`` as MISSING rather than as zero.

    A zero-length sample yields a Distribution whose statistics are all ``None`` and whose
    ``sample_size`` is 0. NOT zeros: "no observations" and "observations that were all zero" are
    different facts and a chart drawn from the first would show a real value of zero.

    ``stdev`` is the SAMPLE standard deviation and is ``None`` for n<2, because the dispersion of one
    observation is undefined rather than 0.
    """

    present: list[float] = []
    missing = 0
    for raw in values:
        if raw is None:
            missing += 1
            continue
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            missing += 1
            continue
        if raw != raw or raw in (float("inf"), float("-inf")):
            missing += 1
            continue
        present.append(float(raw))

    if not present:
        return Distribution(
            name=name,
            sample_size=0,
            missing_count=missing,
            minimum=None,
            maximum=None,
            mean=None,
            median=None,
            stdev=None,
            p25=None,
            p75=None,
            p90=None,
            unit=unit,
        )

    n = len(present)
    mean = sum(present) / n
    stdev: float | None = None
    if n >= 2:
        variance = sum((v - mean) ** 2 for v in present) / (n - 1)
        stdev = math.sqrt(variance)

    return Distribution(
        name=name,
        sample_size=n,
        missing_count=missing,
        minimum=min(present),
        maximum=max(present),
        mean=mean,
        median=quantile(present, 0.5),
        stdev=stdev,
        p25=quantile(present, 0.25),
        p75=quantile(present, 0.75),
        p90=quantile(present, 0.90),
        unit=unit,
    )


# --- The time model ------------------------------------------------------------------------------
@dataclass(frozen=True)
class TimeModel:
    """Wall time, observed activity, overlap and UNATTRIBUTED time, with unattributed dominant.

    THE FIELD ORDER AND :meth:`dominant_term` ARE THE POINT, not decoration. Measured, unattributed
    time is 96.2 percent of elapsed, so a view that leads with classified activity leads with 4
    percent of the truth. This type makes the dominant term nameable and :meth:`format_report` prints
    it first.

    ``shared_session_count`` and ``double_counted_seconds_avoided`` record the second measured defect:
    25 session ids were shared by 2 to 5 attempts, and attributing a shared session's activity per
    attempt made 27 attempts appear to spend more time on tools than they existed for.
    """

    wall_seconds: float
    observed_activity_seconds: float
    overlap_seconds: float
    #: Sessions whose activity was attributed to ONE attempt because several attempts shared them.
    shared_session_count: int = 0
    #: Activity seconds NOT counted a second time because of the shared-session rule. Reported so the
    #: correction is visible rather than silent.
    double_counted_seconds_avoided: float = 0.0
    attempts_sharing_a_session: int = 0

    @property
    def unattributed_seconds(self) -> float:
        """Elapsed time no observed activity covers. NEVER clamped to zero.

        A negative value is real evidence of an attribution or clock defect (the shared-session
        double count produced exactly that on 27 real attempts), and flooring it would erase the
        signal that led to the correction.
        """

        return self.wall_seconds - self.observed_activity_seconds

    @property
    def activity_share_of_wall(self) -> float:
        return (
            (self.observed_activity_seconds / self.wall_seconds)
            if self.wall_seconds
            else 0.0
        )

    @property
    def unattributed_share_of_wall(self) -> float:
        return (
            (self.unattributed_seconds / self.wall_seconds)
            if self.wall_seconds
            else 0.0
        )

    def dominant_term(self) -> str:
        """WHICH term accounts for most of elapsed time. Measured: ``unattributed`` at 96.2 percent.

        Exists so a view cannot present activity as the headline without contradicting a value it
        already has. A renderer asks this and labels its chart accordingly.
        """

        return (
            "unattributed"
            if self.unattributed_seconds >= self.observed_activity_seconds
            else "observed_activity"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            # unattributed FIRST, deliberately: it is the dominant term and a serialized view that
            # buries it invites the same misreading the chart rule forbids.
            "unattributed_seconds": round(self.unattributed_seconds, 6),
            "unattributed_share_of_wall": round(self.unattributed_share_of_wall, 6),
            "dominant_term": self.dominant_term(),
            "wall_seconds": round(self.wall_seconds, 6),
            "observed_activity_seconds": round(self.observed_activity_seconds, 6),
            "activity_share_of_wall": round(self.activity_share_of_wall, 6),
            "overlap_seconds": round(self.overlap_seconds, 6),
            "shared_session_count": self.shared_session_count,
            "double_counted_seconds_avoided": round(
                self.double_counted_seconds_avoided, 6
            ),
            "attempts_sharing_a_session": self.attempts_sharing_a_session,
        }

    def format_report(self) -> str:
        """A pasteable time report leading with the dominant term."""

        return "\n".join(
            [
                f"DOMINANT TERM: {self.dominant_term()}",
                f"unattributed_seconds   {self.unattributed_seconds:14.1f}  "
                f"({self.unattributed_share_of_wall:.4%} of wall)",
                f"observed_activity_s    {self.observed_activity_seconds:14.1f}  "
                f"({self.activity_share_of_wall:.4%} of wall)",
                f"overlap_seconds        {self.overlap_seconds:14.1f}",
                f"wall_seconds           {self.wall_seconds:14.1f}",
                f"shared sessions        {self.shared_session_count} "
                f"({self.attempts_sharing_a_session} attempts), "
                f"double count avoided {self.double_counted_seconds_avoided:.1f}s",
            ]
        )


def build_time_model(
    *,
    wall_seconds: float,
    activities: Sequence[Mapping[str, Any]],
) -> TimeModel:
    """Build a :class:`TimeModel` from activity intervals, attributing a SHARED SESSION ONCE.

    Each activity is ``{"session_id": str, "start": float, "end": float}``. Activities are grouped by
    ``session_id`` and each session's interval UNION contributes to observed activity exactly once,
    however many attempts referenced it. THAT IS THE CORRECTION: 25 real session ids were shared by 2
    to 5 attempts (80 of 179 attempts), and per-attempt attribution made 27 attempts show more tool
    time than wall time.

    ``overlap_seconds`` is the excess of the naive sum over the union, i.e. the double counting made
    visible. Activity is NEVER scaled to fill ``wall_seconds``: the measured ratio is 3.8 percent and
    scaling it up would manufacture 96 percent of the number.
    """

    by_session: dict[str, list[tuple[float, float]]] = {}
    naive_total = 0.0
    for activity in activities:
        start = activity.get("start")
        end = activity.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            continue
        if isinstance(start, bool) or isinstance(end, bool) or end < start:
            continue
        session = str(activity.get("session_id") or "")
        by_session.setdefault(session, []).append((float(start), float(end)))
        naive_total += float(end) - float(start)

    union_total = 0.0
    shared_sessions = 0
    attempts_sharing = 0
    for session, spans in by_session.items():
        merged: list[list[float]] = []
        for start, end in sorted(spans):
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        union_total += sum(end - start for start, end in merged)
        if len(spans) > len(merged):
            shared_sessions += 1
            attempts_sharing += len(spans)

    return TimeModel(
        wall_seconds=float(wall_seconds),
        observed_activity_seconds=union_total,
        overlap_seconds=naive_total - union_total,
        shared_session_count=shared_sessions,
        double_counted_seconds_avoided=naive_total - union_total,
        attempts_sharing_a_session=attempts_sharing,
    )


# --- E-04: the instruction burden ----------------------------------------------------------------
def instruction_burden(
    *,
    first_step_input_tokens: Sequence[float],
    turn_count: int,
    input_rate_per_mtok: float,
    standing_instruction_bytes: Mapping[str, int] | None = None,
    read_tool_seconds: float | None = None,
    tool_seconds: float | None = None,
    wall_seconds: float | None = None,
) -> AnalysisResult:
    """The instruction burden as INJECTED TOKENS AND PRICED COST, with read-time as a footnote.

    WHY THIS SHAPE. The plan's required analysis 1 was instruction-read TIME. Measured, all 2334
    ``read`` calls total 183.2 s = 0.38 percent of tool time = 0.014 percent of elapsed, so a time
    chart is a flat line. The burden is INJECTED: the median session's first step already carries
    15067 input tokens before the agent reads anything, and the standing instruction corpus
    (``AGENTS.md`` 33101 bytes) is loaded on EVERY turn. So this measures tokens and dollars, scales
    them by turn count, and reports read time as a labeled footnote.

    THE 0.014 PERCENT FIGURE IS PUBLISHED IN THE RESULT, not merely in the plan. V-04's whole purpose
    is that a reader must not mistake a flat chart for an absent cost, so the number and its
    derivation appear under ``read_time_footnote`` whether or not the caller supplies fresh
    durations. When durations ARE supplied the observed share is computed and reported alongside.
    """

    distribution = describe(
        "instruction_burden.first_step_input_tokens",
        list(first_step_input_tokens),
        unit="tokens",
    )

    refusal = under_power_verdict(
        "instruction-burden",
        distribution.sample_size,
        caveats=(
            "instruction burden is measured from injected input tokens, not from read-tool time; "
            "see read_time_footnote for why the time measure is empty",
        ),
    )
    if refusal is not None:
        return refusal

    median_tokens = distribution.median or 0.0
    per_turn_cost = median_tokens * input_rate_per_mtok / 1_000_000.0
    inventory = dict(
        standing_instruction_bytes or CORPUS_BASELINE["standing_instruction_bytes"]
    )
    # 4 bytes per token, the ratio the baseline's own byte/token pairs exhibit (33101/8275 = 4.00).
    # Stated as an approximation because it IS one: a real tokenizer is model-specific and adding one
    # would be a runtime dependency this plan forbids.
    inventory_tokens = {name: round(size / 4) for name, size in inventory.items()}

    # The footnote, with its derivation spelled out. Uses observed values when ALL THREE durations
    # are supplied and nonzero, and the labeled review-time snapshot otherwise; `basis` says which.
    # All three are required together because the derivation is a chain of two ratios, and mixing an
    # observed numerator with a snapshot denominator would produce a number belonging to neither.
    have_observed = (
        isinstance(read_tool_seconds, (int, float))
        and isinstance(tool_seconds, (int, float))
        and isinstance(wall_seconds, (int, float))
        and float(tool_seconds) > 0.0
        and float(wall_seconds) > 0.0
    )
    if have_observed:
        read_seconds = float(read_tool_seconds or 0.0)
        observed_tool_seconds = float(tool_seconds or 0.0)
        observed_wall_seconds = float(wall_seconds or 0.0)
        share_of_tool = read_seconds / observed_tool_seconds
        share_of_wall = read_seconds / observed_wall_seconds
        basis = "observed-in-this-corpus"
    else:
        read_seconds = float(CORPUS_BASELINE["read_tool_seconds"])
        observed_tool_seconds = float(CORPUS_BASELINE["tool_activity_seconds"])
        observed_wall_seconds = float(CORPUS_BASELINE["run_wall_seconds"])
        share_of_tool = float(CORPUS_BASELINE["read_share_of_tool_time"])
        share_of_wall = float(CORPUS_BASELINE["read_share_of_wall_time"])
        basis = "review-time-snapshot-2026-09-08-NOT-CURRENT"

    footnote = {
        "label": "FOOTNOTE, NOT A HEADLINE",
        "basis": basis,
        "read_tool_seconds": round(read_seconds, 4),
        "share_of_tool_time": round(share_of_tool, 6),
        "share_of_tool_time_percent": f"{share_of_tool:.2%}",
        "share_of_wall_time": round(share_of_wall, 8),
        # THE FIGURE V-04 REQUIRES, published verbatim in the output.
        "share_of_wall_time_percent": f"{share_of_wall:.3%}",
        "derivation": (
            f"{read_seconds:.1f} s of read-tool time / {observed_tool_seconds:.0f} s of tool time "
            f"= {share_of_tool:.2%} of tool time; tool time / {observed_wall_seconds:.0f} s of "
            f"wall time, so read time is {share_of_wall:.3%} of elapsed"
        ),
        "why_it_is_a_footnote": (
            "a time chart of instruction reading renders as a flat line indistinguishable from "
            "zero; the instruction burden is INJECTED CONTEXT measured in tokens and dollars, not "
            "time spent reading. Do not read the flat line as an absent cost"
        ),
    }

    return AnalysisResult(
        name="instruction-burden",
        verdict=Verdict.COMPUTED,
        sample_size=distribution.sample_size,
        values={
            "first_step_input_tokens": distribution.to_dict(),
            "median_first_step_input_tokens": median_tokens,
            # ROUNDED TO 9 PLACES, NOT 6, and the extra precision is load-bearing rather than
            # fussy: a per-turn cost is a fraction of a cent that gets MULTIPLIED by a turn count,
            # so truncating it at 1e-6 introduces an error that scales with the run. At 15067 tokens
            # and $5.50/Mtok the true value is $0.0828685, which 6 places silently reports as
            # $0.082868 and 100 turns then compounds into a visible discrepancy.
            "cost_per_turn_usd": round(per_turn_cost, 9),
            "turn_count": turn_count,
            "total_injected_cost_usd": round(per_turn_cost * max(turn_count, 0), 9),
            "standing_instruction_bytes": dict(sorted(inventory.items())),
            "standing_instruction_tokens_approx": dict(
                sorted(inventory_tokens.items())
            ),
            "standing_instruction_total_bytes": sum(inventory.values()),
            "standing_instruction_total_tokens_approx": sum(inventory_tokens.values()),
            "read_time_footnote": footnote,
        },
        reason="measured as injected input tokens and their priced cost per turn",
        caveats=(
            "the token/byte ratio is approximated at 4 bytes per token; a real tokenizer is "
            "model-specific and would be a runtime dependency this layer does not take",
            "read-tool time is a footnote at "
            f"{footnote['share_of_wall_time_percent']} of elapsed, NOT the headline",
        ),
    )


# --- E-05: the supported analyses ----------------------------------------------------------------
def per_ipd_usage(attempts: Sequence[Mapping[str, Any]]) -> AnalysisResult:
    """Cost, tokens and elapsed time per IPD. SUPPORTED (179 attempts, 118 distinct id6 at review).

    Each attempt is ``{"ipd_id6": str, "cost": float|None, "tokens": {...}, "wall_seconds": float|None,
    "phase": str}``. Aggregates per id6 and reports the distribution ACROSS id6, so the sample size is
    the number of distinct IPDs rather than the number of attempts: an IPD retried five times is one
    observation of "what does an IPD cost", not five.
    """

    per_id6: dict[str, dict[str, float]] = {}
    for attempt in attempts:
        id6 = str(attempt.get("ipd_id6") or "")
        if not id6:
            continue
        bucket = per_id6.setdefault(
            id6, {"cost": 0.0, "tokens": 0.0, "wall": 0.0, "attempts": 0.0}
        )
        cost = attempt.get("cost")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool):
            bucket["cost"] += float(cost)
        tokens = attempt.get("tokens")
        if isinstance(tokens, Mapping):
            total = tokens.get("total")
            if isinstance(total, (int, float)) and not isinstance(total, bool):
                bucket["tokens"] += float(total)
        wall = attempt.get("wall_seconds")
        if isinstance(wall, (int, float)) and not isinstance(wall, bool):
            bucket["wall"] += float(wall)
        bucket["attempts"] += 1

    refusal = under_power_verdict("per-ipd-usage", len(per_id6))
    if refusal is not None:
        return refusal

    return AnalysisResult(
        name="per-ipd-usage",
        verdict=Verdict.COMPUTED,
        sample_size=len(per_id6),
        values={
            "distinct_ipd_count": len(per_id6),
            "attempt_count": len(attempts),
            "cost_usd": describe(
                "per_ipd.cost_usd", [b["cost"] for b in per_id6.values()], unit="USD"
            ).to_dict(),
            "tokens": describe(
                "per_ipd.tokens", [b["tokens"] for b in per_id6.values()], unit="tokens"
            ).to_dict(),
            "wall_seconds": describe(
                "per_ipd.wall_seconds", [b["wall"] for b in per_id6.values()], unit="s"
            ).to_dict(),
            "attempts_per_ipd": describe(
                "per_ipd.attempts",
                [b["attempts"] for b in per_id6.values()],
                unit="attempts",
            ).to_dict(),
        },
        reason="aggregated per distinct IPD id6",
    )


def implementation_versus_inspection(
    *,
    tool_counts: Mapping[str, int],
    file_categories: Mapping[str, int] | None = None,
) -> AnalysisResult:
    """The implementation/editing versus inspection/search ratio. SUPPORTED and measured.

    Measured at review: ``edit`` 5512 versus ``read`` 2332 calls, and by file category source-code
    38.0 percent / plan-or-ipd 37.5 percent / test-code 13.0 percent of the 8421 file-touching calls.
    Computed from the supplied counts, never from the baseline.

    Uses a WILSON INTERVAL on the implementation share, which is the house pattern for a proportion
    (``benchmark_metrics.wilson_score_interval``): a bare ratio hides that the same ratio over 30
    calls and over 30000 calls are different claims.
    """

    implementation = sum(int(tool_counts.get(name, 0)) for name in ("edit", "write"))
    inspection = sum(int(tool_counts.get(name, 0)) for name in ("read", "grep", "glob"))
    total = implementation + inspection

    refusal = under_power_verdict("implementation-versus-inspection", total)
    if refusal is not None:
        return refusal

    lower, upper = wilson_score_interval(implementation, total)
    share = implementation / total
    metric = MetricValue(
        name="implementation_share",
        value=share,
        sample_size=total,
        ci_lower=lower,
        ci_upper=upper,
        unit="share",
    )

    categories = dict(file_categories or {})
    category_total = sum(categories.values())
    category_shares = (
        {
            name: round(count / category_total, 6)
            for name, count in sorted(categories.items())
        }
        if category_total
        else {}
    )

    return AnalysisResult(
        name="implementation-versus-inspection",
        verdict=Verdict.COMPUTED,
        sample_size=total,
        values={
            "implementation_calls": implementation,
            "inspection_calls": inspection,
            "ratio_implementation_to_inspection": (
                round(implementation / inspection, 6) if inspection else None
            ),
            "implementation_share": metric.to_dict(),
            "file_category_counts": dict(sorted(categories.items())),
            "file_category_shares": category_shares,
        },
        reason="computed from the supplied tool-call census",
    )


def cache_utilization(
    *,
    token_components: Mapping[str, float],
    cost_by_component: Mapping[str, float] | None = None,
) -> AnalysisResult:
    """Cache-token utilization. STRONGLY SUPPORTED and the largest single lever.

    Measured at review: ``cache_read`` is 98.62 percent of all 5795743803 tokens and 72.1 percent of
    Era B spend; ``cache_write`` is 0 everywhere. A pricing or efficiency view that omits cache reads
    omits nearly three quarters of the money, which is why this is its own analysis rather than a row
    in a token table.

    Sample size here is the number of COMPONENTS observed, and the refusal is deliberately NOT
    applied: a token census is a total, not a sample, so an under-power test on it would be a category
    error. That is stated because every other analysis in this module does apply one.
    """

    total = float(token_components.get("total") or 0.0)
    if not total:
        total = sum(
            float(v)
            for k, v in token_components.items()
            if k != "total" and isinstance(v, (int, float))
        )
    cache = float(token_components.get("cache") or 0.0)
    spend = dict(cost_by_component or {})
    spend_total = sum(spend.values())

    return AnalysisResult(
        name="cache-utilization",
        verdict=Verdict.COMPUTED,
        sample_size=len([k for k in token_components if k != "total"]),
        values={
            "total_tokens": total,
            "cache_tokens": cache,
            "cache_share_of_tokens": round(cache / total, 6) if total else None,
            "component_shares": (
                {
                    name: round(float(value) / total, 6)
                    for name, value in sorted(token_components.items())
                    if name != "total" and isinstance(value, (int, float))
                }
                if total
                else {}
            ),
            "cache_share_of_spend": (
                round(spend.get("cache", 0.0) / spend_total, 6) if spend_total else None
            ),
            "spend_by_component_usd": {
                k: round(v, 6) for k, v in sorted(spend.items())
            },
        },
        reason="a token census is a total rather than a sample, so no under-power test applies",
        caveats=(
            "cache_write was measured 0 in every step reporting a cache object, so the single "
            "`cache` component is cache_read in practice; see run_analytics_pricing",
        ),
    )


def cost_concentration(costs: Sequence[float]) -> AnalysisResult:
    """Cost concentration: what share of spend the most expensive attempts hold.

    ONE OF THE FOUR CORPUS-SUPPORTED ADDITIONS the plan asked to select, NAMED at review rather than
    left to execution. Measured: the top 10 percent of attempts held 22.8 percent of spend, the top 20
    percent held 39.6 percent, the most expensive single attempt was $54.50 against a median of $11.79.

    Deliberately reports the top DECILE and QUINTILE shares rather than a Gini coefficient: the
    decile share answers "would optimizing the worst few help" directly, while a single inequality
    scalar answers no operational question and invites over-interpretation.
    """

    values = [
        float(c)
        for c in costs
        if isinstance(c, (int, float)) and not isinstance(c, bool)
    ]
    refusal = under_power_verdict("cost-concentration", len(values))
    if refusal is not None:
        return refusal

    ordered = sorted(values, reverse=True)
    total = sum(ordered)
    if total <= 0:
        return AnalysisResult(
            name="cost-concentration",
            verdict=Verdict.CANNOT_DETERMINE,
            sample_size=len(ordered),
            reason="total spend is zero, so a concentration share is undefined rather than 0",
        )

    def top_share(fraction: float) -> float:
        count = max(1, int(round(len(ordered) * fraction)))
        return sum(ordered[:count]) / total

    return AnalysisResult(
        name="cost-concentration",
        verdict=Verdict.COMPUTED,
        sample_size=len(ordered),
        values={
            "total_spend_usd": round(total, 6),
            "top_decile_spend_share": round(top_share(0.10), 6),
            "top_quintile_spend_share": round(top_share(0.20), 6),
            "max_cost_usd": round(ordered[0], 6),
            "median_cost_usd": round(quantile(ordered, 0.5), 6),
            "distribution": describe("attempt_cost_usd", ordered, unit="USD").to_dict(),
        },
        reason="computed over the supplied attempt costs",
        caveats=(
            "ASSOCIATION ONLY: a concentrated cost distribution does not establish that the "
            "expensive attempts were wasteful, and they may simply be the hard ones",
        ),
    )


def within_session_gradient(
    steps: Sequence[Mapping[str, Any]],
    *,
    minimum_steps_per_session: int = 20,
    decile_count: int = 10,
) -> AnalysisResult:
    """Mean cost per step across POSITION deciles within a session.

    THE SECOND NAMED ADDITION. Measured: mean cost per step rises monotonically across position
    deciles from $0.0781 in the first to $0.1290 in the last, a 1.27x ratio over 345 sessions with 20+
    steps.

    Each step is ``{"session_id": str, "position": int, "cost": float}``. Sessions shorter than
    ``minimum_steps_per_session`` are EXCLUDED, because a 3-step session's "last decile" is one step
    and pooling it with a 200-step session's would compare different things.

    The caveat is not optional and is asserted by a test: a rising gradient is consistent with context
    growth AND with harder work later in a session, and this layer may not assert the first.
    """

    by_session: dict[str, list[tuple[int, float]]] = {}
    for step in steps:
        session = str(step.get("session_id") or "")
        position = step.get("position")
        cost = step.get("cost")
        if not session or not isinstance(position, int) or isinstance(position, bool):
            continue
        if not isinstance(cost, (int, float)) or isinstance(cost, bool):
            continue
        by_session.setdefault(session, []).append((position, float(cost)))

    eligible = {
        s: v for s, v in by_session.items() if len(v) >= minimum_steps_per_session
    }
    refusal = under_power_verdict("within-session-cost-gradient", len(eligible))
    if refusal is not None:
        return refusal

    decile_costs: list[list[float]] = [[] for _ in range(decile_count)]
    for spans in eligible.values():
        ordered = sorted(spans)
        n = len(ordered)
        for index, (_position, cost) in enumerate(ordered):
            # Index-based decile so each session contributes to every decile regardless of length.
            bucket = min(decile_count - 1, int(index * decile_count / n))
            decile_costs[bucket].append(cost)

    means = [(sum(bucket) / len(bucket)) if bucket else None for bucket in decile_costs]
    first, last = means[0], means[-1]
    ratio = (last / first) if (first and last) else None
    present = [m for m in means if m is not None]
    monotonic = (
        all(a <= b for a, b in zip(present, present[1:])) if len(present) > 1 else False
    )

    return AnalysisResult(
        name="within-session-cost-gradient",
        verdict=Verdict.COMPUTED,
        sample_size=len(eligible),
        values={
            "session_count": len(eligible),
            "minimum_steps_per_session": minimum_steps_per_session,
            "decile_mean_cost_usd": [None if m is None else round(m, 6) for m in means],
            "first_decile_mean_cost_usd": None if first is None else round(first, 6),
            "last_decile_mean_cost_usd": None if last is None else round(last, 6),
            "first_to_last_ratio": None if ratio is None else round(ratio, 6),
            "is_monotonic_increasing": monotonic,
        },
        reason="computed over sessions meeting the minimum step count",
        caveats=(
            "ASSOCIATION ONLY, AND THE ALTERNATIVE EXPLANATION IS EQUALLY CONSISTENT: a rising "
            "per-step cost across position deciles is consistent with context growth, and equally "
            "consistent with harder work arriving later in a session. This layer does not assert "
            "the first",
        ),
    )


def missingness_bias(
    *,
    session_log_costs: Mapping[str, float],
    attempt_costs: Mapping[str, float],
) -> AnalysisResult:
    """How much real spend is INVISIBLE at the attempt grain. The fourth named addition.

    Measured: session logs totalled $3026.38 while recorded attempts totalled $2568.12, and 215
    session files whose matching attempt records no cost held $394.19, so 13.0 percent of real spend
    is invisible at the attempt grain. Separately, ALL verifier spend is ($64.08 across 57 logs, with
    zero attempts carrying ``verify_cost``).

    Both mappings are keyed by session identifier. A key present in the logs and absent from the
    attempts is UNACCOUNTED spend; the reverse is an attempt whose log is missing, reported separately
    because the two have different causes and different fixes.
    """

    log_total = sum(float(v) for v in session_log_costs.values())
    attempt_total = sum(float(v) for v in attempt_costs.values())
    unaccounted_keys = [k for k in session_log_costs if k not in attempt_costs]
    unaccounted = sum(float(session_log_costs[k]) for k in unaccounted_keys)
    orphan_attempt_keys = [k for k in attempt_costs if k not in session_log_costs]

    return AnalysisResult(
        name="missingness-bias",
        verdict=Verdict.COMPUTED,
        sample_size=len(session_log_costs),
        values={
            "session_log_total_usd": round(log_total, 6),
            "recorded_attempt_total_usd": round(attempt_total, 6),
            "unaccounted_usd": round(unaccounted, 6),
            "unaccounted_session_count": len(unaccounted_keys),
            "unaccounted_share_of_spend": round(unaccounted / log_total, 6)
            if log_total
            else None,
            "attempts_without_a_log_count": len(orphan_attempt_keys),
        },
        reason="reconciled session-log spend against attempt-recorded spend per session id",
        caveats=(
            "a per-IPD cost chart built only from attempt records UNDERSTATES spend by this share",
            "closing the gap is a RUNNER change, not an analytics change: this reports it",
        ),
    )


# --- E-06: the refusals --------------------------------------------------------------------------
def model_comparison(
    attempts: Sequence[Mapping[str, Any]],
    *,
    coverage_threshold: float = MODEL_COVERAGE_THRESHOLD,
) -> AnalysisResult:
    """Model/provider/variant comparison. REFUSES below the declared identity coverage.

    Measured at review: ``options.model`` null in 130 of 135 runs, ``launch_profile`` absent in 102
    and recording ``model: host-default`` in 31 of the 33 present, NO attempt-level model key
    anywhere, and the only ``modelID`` occurrences (16 of 462 session files) sit on a ``task`` call
    and describe the SUB-AGENT's model. Net: 2 of 179 attempts, 1.1 PERCENT.

    A comparison chart drawn over 1.1 percent coverage is a fabrication, so this returns
    :attr:`Verdict.REFUSED` carrying the OBSERVED coverage. Two specific inferences are refused by
    name in the caveats because both are tempting and both are wrong: inferring the model from the run
    DATE conflates model with PRICE ERA and manufactures the Simpson's-paradox confound, and reading a
    ``task`` sub-agent's ``modelID`` measures a different model than the one that did the work.

    PRICE-ERA stratification is unaffected and available; see
    :mod:`agent_workflows.run_analytics_pricing`.
    """

    total = len(attempts)
    with_model = [
        a
        for a in attempts
        if str(a.get("model") or "").strip()
        and str(a.get("model")).strip() != "host-default"
    ]
    coverage = (len(with_model) / total) if total else 0.0

    caveats = (
        "REFUSED INFERENCE 1: deriving the model from the run date conflates model identity with "
        "PRICE ERA, which would make every pricing change look like a model difference",
        "REFUSED INFERENCE 2: a `task` sub-agent's modelID identifies the sub-agent's model, not "
        "the model that performed the measured work",
        "price-era stratification IS available and is not affected by this refusal",
        "coverage improves for FUTURE runs only (Order 04 records model identity per file); "
        "historical comparison stays refused",
    )

    if coverage < coverage_threshold:
        return AnalysisResult(
            name="model-comparison",
            verdict=Verdict.REFUSED,
            sample_size=len(with_model),
            reason=(
                f"model identity resolves for {len(with_model)} of {total} attempts "
                f"(coverage {coverage:.4f}), below the declared threshold {coverage_threshold:.2f}; "
                "a comparison drawn over this coverage would measure the minority and report it as "
                "the whole"
            ),
            values={
                "observed_coverage": round(coverage, 6),
                "attempts_with_model": len(with_model),
            },
            caveats=caveats,
        )

    by_model: dict[str, list[float]] = {}
    for attempt in with_model:
        cost = attempt.get("cost")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool):
            by_model.setdefault(str(attempt["model"]), []).append(float(cost))

    return AnalysisResult(
        name="model-comparison",
        verdict=Verdict.COMPUTED,
        sample_size=len(with_model),
        values={
            "observed_coverage": round(coverage, 6),
            "per_model_cost_usd": {
                name: describe(f"model.{name}.cost_usd", costs, unit="USD").to_dict()
                for name, costs in sorted(by_model.items())
            },
        },
        reason=f"identity coverage {coverage:.4f} meets the declared threshold",
        caveats=caveats,
    )


#: A verifier session log's filename shape. The verifier's phase is recoverable ONLY from here:
#: ``oc_runipd.run_opencode`` passes ``log_suffix="verify"`` to ``attempt_log_path``, which produces
#: ``<NN>-<id6>-attempt-<n>-verify.jsonl``. Measured: 57 such logs hold $64.08 and ZERO attempts
#: carry ``verify_cost``/``verify_tokens``, so a filename is the only signal and every value derived
#: from it MUST be labeled derived.
_VERIFY_LOG_RE = re.compile(r"-attempt-\d+-verify\.jsonl$")


def verifier_phase_of_log(filename: str) -> tuple[str, bool]:
    """``(phase, is_derived)`` for a session log filename. ``is_derived`` is ALWAYS True for verify.

    RELOCATED BY NAME, NOT BY LINE: ``oc_runipd.attempt_log_path`` appends ``-verify`` when
    ``run_opencode`` is called with ``log_suffix="verify"``, and that call site is the verifier turn.
    The runner's own comment states the coupling is a presentation detail rather than a data field,
    which is exactly why anything read off it is labeled derived here.
    """

    name = str(filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    if _VERIFY_LOG_RE.search(name):
        return "verify", True
    return "execute", True


def verifier_phase_summary(
    session_logs: Sequence[Mapping[str, Any]],
) -> AnalysisResult:
    """Review versus execute versus VERIFIER cost, with the verifier phase LABELED derived.

    Each entry is ``{"filename": str, "cost": float, "action": str|None}``. ``action`` labels review
    versus execute where the attempt recorded one; the VERIFIER phase is derived from the filename
    because no attempt record carries ``verify_cost`` (measured: zero of 179).

    ``is_derived`` is True on the result, which is the requirement: a consumer must be able to tell a
    phase that was recorded from one this toolkit inferred.
    """

    by_phase: dict[str, list[float]] = {}
    derived_count = 0
    for entry in session_logs:
        cost = entry.get("cost")
        if not isinstance(cost, (int, float)) or isinstance(cost, bool):
            continue
        phase, _derived = verifier_phase_of_log(str(entry.get("filename") or ""))
        if phase == "verify":
            derived_count += 1
        else:
            action = str(entry.get("action") or "").strip().lower()
            phase = action if action in ("review", "execute") else "unknown"
        by_phase.setdefault(phase, []).append(float(cost))

    return AnalysisResult(
        name="review-versus-execute-versus-verifier",
        verdict=Verdict.COMPUTED,
        sample_size=sum(len(v) for v in by_phase.values()),
        values={
            "cost_by_phase_usd": {
                phase: round(sum(costs), 6) for phase, costs in sorted(by_phase.items())
            },
            "log_count_by_phase": {
                phase: len(costs) for phase, costs in sorted(by_phase.items())
            },
            "verify_logs_derived_from_filename": derived_count,
            "attempts_carrying_verify_cost": 0,
            "verify_phase_provenance": "derived-from-log-filename",
        },
        reason="verifier phase derived from the session log filename",
        is_derived=True,
        caveats=(
            "THE VERIFY PHASE IS DERIVED FROM A FILENAME, not recorded: zero attempts carry "
            "verify_cost or verify_tokens, so this attribution depends on the runner's log naming "
            "and would break silently if that naming changed",
        ),
    )


def refuse_under_powered_required_analyses(
    observed: Mapping[str, int] | None = None,
) -> dict[str, AnalysisResult]:
    """The four measured-under-powered REQUIRED analyses, each returning ``cannot-determine``.

    Named in :data:`UNDER_POWERED_ANALYSES` rather than discovered, so a renderer asking for the
    required set gets four refusals with their observed n attached instead of four empty charts.
    ``observed`` supplies re-measured sample sizes; absent a value the labeled review-time snapshot is
    used and the reason says which.
    """

    counts = dict(observed or {})
    results: dict[str, AnalysisResult] = {}
    for name, baseline_key in UNDER_POWERED_ANALYSES.items():
        if baseline_key in counts:
            n = int(counts[baseline_key])
            basis = "observed"
        else:
            n = int(CORPUS_BASELINE[baseline_key])
            basis = "review-time-snapshot-2026-09-08-NOT-CURRENT"
        result = under_power_verdict(name, n, caveats=(f"sample size basis: {basis}",))
        # A required analysis whose n has GROWN past the minimum is genuinely computable, and saying
        # otherwise would be the mirror image of the defect this function exists to prevent.
        results[name] = (
            result
            if result is not None
            else AnalysisResult(
                name=name,
                verdict=Verdict.COMPUTED,
                sample_size=n,
                reason=f"observed n={n} now meets the declared minimum n={MINIMUM_SAMPLE_SIZE}",
                caveats=(f"sample size basis: {basis}",),
            )
        )
    return results

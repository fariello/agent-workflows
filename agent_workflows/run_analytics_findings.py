#!/usr/bin/env python3
"""The RANKED FINDINGS contract: evidence, uncertainty, alternatives, and a next experiment.

WHAT A FINDING IS ALLOWED TO SAY, WHICH IS LESS THAN A READER WILL WANT. This module turns analysis
results into ranked, evidence-backed EFFICIENCY OPPORTUNITIES and it may not turn them into advice.
Every :class:`Finding` therefore carries, as REQUIRED fields rather than optional prose: an effect
size with units, the sample size and coverage behind it, an explicit uncertainty statement, its
data-quality caveats, at least one ALTERNATIVE EXPLANATION, and a low-risk next experiment.
:func:`build_finding` REFUSES a record missing any of them, because a finding with no alternative
explanation reads as a cause and that is the single failure mode this contract exists to prevent.

NO CAUSAL LANGUAGE, CHECKED MECHANICALLY. :func:`scan_for_causal_language` matches a closed list of
causal constructions (``causes``, ``because``, ``due to``, ``leads to``, ``drives``, ``results in``,
``responsible for``, ``the reason``, ``therefore``) against every human-readable field, and
:func:`build_finding` refuses a violation. A convention that lives only in a docstring is a convention
nobody can enforce; this one fails a test.

A REAL SIMPSON'S-PARADOX HAZARD IS ALREADY IN THIS DATA, so the required paradox warning ships with a
MEASURED exemplar rather than a synthetic one. Blended cost per million tokens rises from a median of
$0.054-$0.071 in the Era A days to $0.635-$0.737 in the Era B days, a MORE THAN NINEFOLD apparent
rise. That is NOT a rate change of that magnitude: the Era B rates are only 10 PERCENT higher, and the
jump is caused by cache_read going from FREE to BILLABLE while cache_read is 98.62 percent of tokens.
So any cost-efficiency comparison that POOLS across the 2026-08-29 boundary will attribute a
pricing-policy change to workflow behavior. :func:`detect_pooled_era_comparison` flags exactly that,
and :data:`PRICE_ERA_PARADOX_BASELINE` carries the measured figures for the golden test.

INSUFFICIENT EVIDENCE YIELDS A ``cannot-determine`` FINDING, NEVER ADVICE. :func:`findings_from_results`
converts a refused :class:`~agent_workflows.run_analytics_statistics.AnalysisResult` into a finding
that states the refusal and carries NO recommendation, which is the plan's own rule applied to its own
output.

RANKING IS STABLE AND TOTAL. :func:`rank_findings` sorts by (severity, effect magnitude, coverage,
finding id), and the id tiebreak makes the order DETERMINISTIC for equal findings: an unstable ranking
would make two runs over the same data disagree about which opportunity matters most.

Stdlib only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from agent_workflows.run_analytics_statistics import AnalysisResult, Verdict

__all__ = [
    "FINDINGS_SCHEMA_VERSION",
    "Severity",
    "Finding",
    "FindingRefusal",
    "CAUSAL_PATTERNS",
    "PRICE_ERA_PARADOX_BASELINE",
    "build_finding",
    "cannot_determine_finding",
    "scan_for_causal_language",
    "assert_no_causal_language",
    "detect_pooled_era_comparison",
    "price_era_paradox_finding",
    "findings_from_results",
    "rank_findings",
    "format_findings_report",
]


#: The findings layer's own version, bumped when the :class:`Finding` FIELD SET changes. Orders 07, 08
#: and 10 render these, so the field set is a contract.
FINDINGS_SCHEMA_VERSION = 1


class FindingRefusal(ValueError):
    """A finding did not meet the evidence contract, so it was REFUSED rather than published.

    Refusing at CONSTRUCTION rather than filtering at render time is deliberate: a finding that
    reached a report and was then dropped has already been written down somewhere, while one that
    cannot be built never exists.
    """


class Severity(str, Enum):
    """How much a finding matters. Ordered for ranking via :data:`_SEVERITY_ORDER`.

    ``CANNOT_DETERMINE`` is a severity rather than an absence, so a refusal RANKS and APPEARS in the
    report. That is the point: a reader must see that four required analyses could not be computed,
    and an omitted refusal is indistinguishable from an oversight.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    CANNOT_DETERMINE = "cannot-determine"


_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.HIGH: 0,
    Severity.MEDIUM: 1,
    Severity.LOW: 2,
    Severity.INFO: 3,
    # LAST deliberately: a refusal is important to SEE but is not an opportunity to act on, so it
    # sorts below every actionable finding rather than crowding the top of the report.
    Severity.CANNOT_DETERMINE: 4,
}


#: Causal constructions refused in a finding's human-readable text. A CLOSED list, matched
#: word-boundary-anchored and case-insensitively.
#:
#: WHY A WORD LIST IS DEFENSIBLE HERE, since a keyword filter is usually the wrong tool: this is not
#: trying to detect causal REASONING, which is undecidable, but to catch the specific PHRASINGS that
#: turn an association into a claim in a report a human will skim. It is a lint, and like every lint
#: it can be evaded by someone determined to; it cannot be tripped ACCIDENTALLY, which is what makes
#: it worth having. ``correlat*`` is deliberately ABSENT: naming a correlation is exactly what this
#: layer is permitted to do.
CAUSAL_PATTERNS: tuple[str, ...] = (
    r"\bcaus(?:e|es|ed|ing)\b",
    r"\bbecause\b",
    r"\bdue to\b",
    r"\bleads? to\b",
    r"\bled to\b",
    r"\bdrives?\b",
    r"\bdriven by\b",
    r"\bresults? in\b",
    r"\bresulting in\b",
    r"\bresponsible for\b",
    r"\bthe reason\b",
    r"\btherefore\b",
    r"\bconsequently\b",
    r"\bmakes? it\b",
    r"\bexplains?\b",
    r"\battributable to\b",
)

_CAUSAL_RE = re.compile("|".join(CAUSAL_PATTERNS), re.IGNORECASE)


#: THE MEASURED SIMPSON'S-PARADOX EXEMPLAR, review-time snapshot (2026-09-08), NOT CURRENT.
#:
#: Retained as the golden-test fixture for :func:`price_era_paradox_finding` because the paradox is
#: REAL in this corpus rather than illustrative, and a synthetic example would not prove the detector
#: fires on the shape the data actually has.
PRICE_ERA_PARADOX_BASELINE: dict[str, Any] = {
    "provenance": "review-time-snapshot",
    "measured_at": "2026-09-08",
    "is_current": False,
    "era_a_blended_usd_per_mtok_range": (0.054, 0.071),
    "era_b_blended_usd_per_mtok_range": (0.635, 0.737),
    "apparent_fold_increase": 9.0,
    "actual_rate_increase": 0.10,
    "cache_read_share_of_tokens": 0.9862,
    "boundary_instant": "2026-08-29T05:38:43Z",
    "mechanism": (
        "cache_read moved from free to billable while being 98.62 percent of tokens; the input and "
        "output rates moved 10 percent"
    ),
}


@dataclass(frozen=True)
class Finding:
    """ONE ranked finding. Every evidence field is REQUIRED; see :func:`build_finding`.

    ``next_experiment`` is required and must be LOW-RISK, which is what keeps a finding actionable
    without it being a recommendation to change anything: the honest output of an observational
    analysis is a cheap test, not a directive.

    ``alternative_explanations`` is required and must be NON-EMPTY. That single constraint carries
    most of the contract's weight: a finding stating an association with no alternative reads as a
    cause however carefully its verb is chosen.
    """

    finding_id: str
    title: str
    severity: Severity
    #: What slice of the corpus this is about (e.g. ``"attempts in price era B"``).
    affected_slice: str
    #: The magnitude, in ``effect_units``. ``None`` for a ``cannot-determine`` finding.
    effect_size: float | None
    effect_units: str
    sample_size: int
    #: Fraction of the slice for which the measurement was available. Distinct from sample size: 40
    #: observations out of 40 and out of 4000 support very different claims.
    coverage: float
    #: An explicit statement of what is NOT known. Required, and refused if empty.
    uncertainty: str
    #: Data-quality caveats a consumer MUST surface. Required, and refused if empty.
    data_quality_caveats: tuple[str, ...]
    #: At least one competing explanation. Required, and refused if empty.
    alternative_explanations: tuple[str, ...]
    #: A cheap, reversible test that would discriminate. Required, and refused if empty.
    next_experiment: str
    #: The analysis names this finding rests on, so it is traceable to its computation.
    evidence_sources: tuple[str, ...] = ()
    #: Present ONLY on an actionable finding. A ``cannot-determine`` finding must leave it empty, and
    #: :func:`build_finding` enforces that: advice on insufficient evidence is the specific output
    #: this contract forbids.
    recommendation: str = ""
    findings_schema_version: int = FINDINGS_SCHEMA_VERSION

    @property
    def is_actionable(self) -> bool:
        return self.severity is not Severity.CANNOT_DETERMINE

    def human_text_fields(self) -> dict[str, str]:
        """Every field a human reads, for the causal-language scan.

        Enumerated EXPLICITLY rather than derived from ``to_dict``, so adding a prose field is a
        deliberate act that must also be added here. A derived list would silently leave a new field
        unscanned, which is exactly how a lint stops working.
        """

        fields: dict[str, str] = {
            "title": self.title,
            "affected_slice": self.affected_slice,
            "uncertainty": self.uncertainty,
            "next_experiment": self.next_experiment,
            "recommendation": self.recommendation,
        }
        for index, text in enumerate(self.data_quality_caveats):
            fields[f"data_quality_caveats[{index}]"] = text
        for index, text in enumerate(self.alternative_explanations):
            fields[f"alternative_explanations[{index}]"] = text
        return fields

    def to_dict(self) -> dict[str, Any]:
        return {
            "findings_schema_version": self.findings_schema_version,
            "finding_id": self.finding_id,
            "title": self.title,
            "severity": self.severity.value,
            "affected_slice": self.affected_slice,
            "effect_size": self.effect_size,
            "effect_units": self.effect_units,
            "sample_size": self.sample_size,
            "coverage": round(self.coverage, 6),
            "uncertainty": self.uncertainty,
            "data_quality_caveats": list(self.data_quality_caveats),
            "alternative_explanations": list(self.alternative_explanations),
            "next_experiment": self.next_experiment,
            "evidence_sources": list(self.evidence_sources),
            "recommendation": self.recommendation,
            "is_actionable": self.is_actionable,
        }


def scan_for_causal_language(text: str) -> list[str]:
    """Every causal construction in ``text``, lowercased. Empty when clean.

    Returns the MATCHES rather than a boolean so a refusal can name what it found, which is the
    difference between a check a human can fix and one they must guess at.
    """

    return [m.group(0).lower() for m in _CAUSAL_RE.finditer(str(text or ""))]


def assert_no_causal_language(finding: Finding) -> None:
    """REFUSE a finding whose human-readable text contains a causal construction.

    Raises :class:`FindingRefusal` naming the field and the phrase. Called by
    :func:`build_finding`, so the check cannot be forgotten at a call site.
    """

    for field_name, text in finding.human_text_fields().items():
        hits = scan_for_causal_language(text)
        if hits:
            raise FindingRefusal(
                f"finding {finding.finding_id!r} field {field_name!r} contains causal "
                f"language {hits!r}; this layer reports association and may not assert causation. "
                "Restate as an observed association, or move the claim into "
                "`alternative_explanations` as one competing account among others"
            )


def build_finding(
    *,
    finding_id: str,
    title: str,
    severity: Severity,
    affected_slice: str,
    effect_size: float | None,
    effect_units: str,
    sample_size: int,
    coverage: float,
    uncertainty: str,
    data_quality_caveats: Sequence[str],
    alternative_explanations: Sequence[str],
    next_experiment: str,
    evidence_sources: Sequence[str] = (),
    recommendation: str = "",
) -> Finding:
    """Construct a :class:`Finding`, REFUSING any record that does not meet the contract.

    SIX REFUSALS, each corresponding to a way a finding misleads:

    1. No ALTERNATIVE EXPLANATION. The most important one: an association with no competing account
       reads as a cause.
    2. No UNCERTAINTY statement. A number with no stated limits is read as precise.
    3. No DATA-QUALITY caveat. This corpus has measured coverage gaps and a finding that mentions
       none implies there are none.
    4. No NEXT EXPERIMENT. Then the finding is a claim rather than a hypothesis.
    5. A RECOMMENDATION on a ``cannot-determine`` finding. Advice on insufficient evidence is the
       specific output the plan forbids.
    6. CAUSAL LANGUAGE anywhere a human reads.
    """

    if not str(title).strip():
        raise FindingRefusal(f"finding {finding_id!r} has no title")
    if not str(uncertainty).strip():
        raise FindingRefusal(
            f"finding {finding_id!r} states no uncertainty; a number with no stated limits is read "
            "as precise"
        )
    if not [c for c in data_quality_caveats if str(c).strip()]:
        raise FindingRefusal(
            f"finding {finding_id!r} carries no data-quality caveat; this corpus has measured "
            "coverage gaps and a finding mentioning none implies there are none"
        )
    if not [a for a in alternative_explanations if str(a).strip()]:
        raise FindingRefusal(
            f"finding {finding_id!r} offers NO alternative explanation; an association presented "
            "without a competing account reads as a cause, which this contract exists to prevent"
        )
    if not str(next_experiment).strip():
        raise FindingRefusal(
            f"finding {finding_id!r} proposes no next experiment; without one the finding is a "
            "claim rather than a hypothesis"
        )
    if severity is Severity.CANNOT_DETERMINE and str(recommendation).strip():
        raise FindingRefusal(
            f"finding {finding_id!r} is `cannot-determine` and carries a recommendation "
            f"({recommendation[:60]!r}); advice on insufficient evidence is exactly what this "
            "contract forbids"
        )

    finding = Finding(
        finding_id=str(finding_id),
        title=str(title),
        severity=severity,
        affected_slice=str(affected_slice),
        effect_size=effect_size,
        effect_units=str(effect_units),
        sample_size=int(sample_size),
        coverage=float(coverage),
        uncertainty=str(uncertainty),
        data_quality_caveats=tuple(
            str(c) for c in data_quality_caveats if str(c).strip()
        ),
        alternative_explanations=tuple(
            str(a) for a in alternative_explanations if str(a).strip()
        ),
        next_experiment=str(next_experiment),
        evidence_sources=tuple(str(s) for s in evidence_sources),
        recommendation=str(recommendation),
    )
    assert_no_causal_language(finding)
    return finding


def cannot_determine_finding(
    *,
    finding_id: str,
    analysis_name: str,
    sample_size: int,
    reason: str,
    extra_caveats: Sequence[str] = (),
) -> Finding:
    """A ``cannot-determine`` finding: the refusal AS the finding, carrying NO recommendation.

    THE REFUSAL IS THE FINDING, which is the plan's own stop condition ("If you find yourself giving
    an under-powered slice a chart because the refusal 'looks unfinished', STOP"). This exists so a
    refused analysis still appears in a ranked report with its observed n, rather than being silently
    absent and indistinguishable from an oversight.

    The ``next_experiment`` is always "collect more observations", stated concretely with the observed
    n, because that IS the only honest next step for an under-powered slice.
    """

    return build_finding(
        finding_id=finding_id,
        title=f"CANNOT DETERMINE: {analysis_name} (observed n={sample_size})",
        severity=Severity.CANNOT_DETERMINE,
        affected_slice=analysis_name,
        effect_size=None,
        effect_units="",
        sample_size=sample_size,
        coverage=0.0,
        uncertainty=(
            f"no effect size is reported: {reason}. Any magnitude computed from n={sample_size} "
            "would be an artifact of the individual observations rather than a measurement"
        ),
        data_quality_caveats=tuple(
            [
                f"observed sample size n={sample_size} is below the declared minimum",
                *extra_caveats,
            ]
        ),
        alternative_explanations=(
            "the effect may be absent entirely",
            "the effect may be present and simply unmeasurable at this sample size",
            "the few observations available may be unrepresentative of the population",
        ),
        next_experiment=(
            f"accumulate observations until this slice reaches the declared minimum, then re-run "
            f"the analysis; at n={sample_size} no test discriminates"
        ),
        evidence_sources=(analysis_name,),
        recommendation="",
    )


def detect_pooled_era_comparison(
    *,
    eras_present: Iterable[str],
    is_stratified: bool,
) -> str:
    """A SIMPSON'S-PARADOX warning when a cost comparison pools across price eras. ``""`` when safe.

    The measured hazard, not a hypothetical: blended $/Mtok rises more than ninefold across the
    2026-08-29 boundary while the rates rose 10 percent, so a pooled comparison mistakes a
    pricing-policy change for a workflow change. Returns a warning STRING (empty when safe) rather
    than raising, so a caller can attach it to a finding as a caveat, which is where it belongs.
    """

    real_eras = {str(e) for e in eras_present if str(e) and str(e) != "unknown"}
    if is_stratified or len(real_eras) < 2:
        return ""
    baseline = PRICE_ERA_PARADOX_BASELINE
    era_a_low, era_a_high = baseline["era_a_blended_usd_per_mtok_range"]
    era_b_low, era_b_high = baseline["era_b_blended_usd_per_mtok_range"]
    return (
        "SIMPSON'S-PARADOX HAZARD: this comparison pools "
        f"{len(real_eras)} price eras ({', '.join(sorted(real_eras))}) without stratifying. "
        f"Measured at review, median blended cost per million tokens moves from "
        f"${era_a_low:.3f}-${era_a_high:.3f} in the earlier era to "
        f"${era_b_low:.3f}-${era_b_high:.3f} in the later one, an apparent "
        f"{baseline['apparent_fold_increase']:.0f}-fold rise, while the published rates moved only "
        f"{baseline['actual_rate_increase']:.0%}. The mechanism is that cache_read became billable "
        f"while being {baseline['cache_read_share_of_tokens']:.2%} of all tokens. Stratify by price "
        "era before comparing cost"
    )


def price_era_paradox_finding(
    *,
    finding_id: str = "F-PRICE-ERA",
    baseline: Mapping[str, Any] | None = None,
) -> Finding:
    """The shipped Simpson's-paradox finding, using the MEASURED figures.

    E-09's golden case. Note the phrasing constraints this had to satisfy: the paradox's MECHANISM is
    itself a causal statement, and the causal-language check applies to this finding as to every
    other, so the mechanism is stated as a co-occurrence in ``alternative_explanations`` and the
    headline reports only what was observed.
    """

    data = dict(baseline or PRICE_ERA_PARADOX_BASELINE)
    era_a_low, era_a_high = data["era_a_blended_usd_per_mtok_range"]
    era_b_low, era_b_high = data["era_b_blended_usd_per_mtok_range"]
    fold = (era_b_low / era_a_high) if era_a_high else 0.0

    return build_finding(
        finding_id=finding_id,
        title=(
            "Blended cost per million tokens differs about ninefold across the price-era boundary, "
            "while the published rates differ by 10 percent"
        ),
        severity=Severity.HIGH,
        affected_slice=(
            f"all priced steps, split at the boundary instant {data['boundary_instant']}"
        ),
        effect_size=round(fold, 4),
        effect_units="fold difference in blended USD per million tokens",
        sample_size=2,
        coverage=1.0,
        uncertainty=(
            f"the two ranges are ${era_a_low:.3f}-${era_a_high:.3f} and "
            f"${era_b_low:.3f}-${era_b_high:.3f} of daily medians, so the fold figure is a ratio of "
            "range endpoints and not a point estimate; the comparison is between two eras, i.e. n=2 "
            "at the era grain"
        ),
        data_quality_caveats=(
            "these are review-time daily medians (measured 2026-09-08) over a corpus that grows "
            "with every run; re-measure before citing them as current",
            f"cache_read is {data['cache_read_share_of_tokens']:.2%} of all tokens, so a blended "
            "per-token rate is dominated by one component and is a poor summary of the others",
        ),
        alternative_explanations=(
            "THE CO-OCCURRING SCHEDULE CHANGE, which is the account this data supports: the "
            f"cache_read rate moved from free to billable at {data['boundary_instant']} while "
            f"cache_read is {data['cache_read_share_of_tokens']:.2%} of tokens, so the two eras "
            "price nearly all of the same token volume differently",
            "a change in workflow behavior across the same period (more or fewer cache reads per "
            "unit of work) would produce a similar blended-rate movement and is not separable "
            "without stratifying",
            "a change in the mix of models or runs across the boundary would also move a blended "
            "rate while no rate and no behavior changed",
        ),
        next_experiment=(
            "stratify every cost comparison by price era and re-compute; if the within-era "
            "comparisons agree while the pooled one differs, the pooled figure is an artifact of "
            "the schedule change and not a measurement of workflow efficiency"
        ),
        evidence_sources=("price-era-stratified-cost-efficiency", "cache-utilization"),
        recommendation=(
            "stratify by price era before comparing cost across the 2026-08-29 boundary; a pooled "
            "comparison is not interpretable as a workflow measurement"
        ),
    )


def findings_from_results(
    results: Iterable[AnalysisResult],
    *,
    id_prefix: str = "F",
) -> list[Finding]:
    """Turn analysis results into findings, converting every refusal into ``cannot-determine``.

    A COMPUTED result yields no finding here: an analysis is not automatically an opportunity, and
    manufacturing a finding per computed analysis is how a report fills up with charts that assert
    nothing. Actionable findings are built deliberately with :func:`build_finding`. What this function
    guarantees is the other direction: NO refusal is silently dropped, so a reader sees every analysis
    the corpus could not support.
    """

    findings: list[Finding] = []
    for index, result in enumerate(results, 1):
        if result.verdict is Verdict.COMPUTED:
            continue
        findings.append(
            cannot_determine_finding(
                finding_id=f"{id_prefix}-{index:02d}",
                analysis_name=result.name,
                sample_size=result.sample_size,
                reason=result.reason,
                extra_caveats=result.caveats,
            )
        )
    return findings


def rank_findings(findings: Sequence[Finding]) -> list[Finding]:
    """Rank findings DETERMINISTICALLY and TOTALLY.

    Sort key: severity, then descending effect magnitude, then descending coverage, then
    ``finding_id``. THE ID TIEBREAK IS WHAT MAKES THE RANKING STABLE: two findings identical on every
    other key would otherwise order by input sequence, so two runs over the same data could disagree
    about which opportunity ranks first, and a ranking that is not reproducible is not evidence.

    A ``None`` effect size (every ``cannot-determine`` finding) sorts as magnitude 0, which is
    consistent with its severity already placing it last.
    """

    return sorted(
        findings,
        key=lambda f: (
            _SEVERITY_ORDER[f.severity],
            -abs(f.effect_size) if f.effect_size is not None else 0.0,
            -f.coverage,
            f.finding_id,
        ),
    )


def format_findings_report(findings: Sequence[Finding]) -> str:
    """A pasteable ranked report showing every contract field. No path, no absolute location."""

    ranked = rank_findings(findings)
    lines = [
        f"findings_schema_version={FINDINGS_SCHEMA_VERSION}  findings={len(ranked)}  "
        f"actionable={sum(1 for f in ranked if f.is_actionable)}  "
        f"cannot-determine={sum(1 for f in ranked if not f.is_actionable)}",
    ]
    for rank, finding in enumerate(ranked, 1):
        effect = (
            f"{finding.effect_size} {finding.effect_units}".strip()
            if finding.effect_size is not None
            else "none (refused)"
        )
        lines.extend(
            [
                "",
                f"#{rank} [{finding.severity.value.upper()}] {finding.finding_id}: {finding.title}",
                f"    slice        : {finding.affected_slice}",
                f"    effect       : {effect}",
                f"    sample       : n={finding.sample_size}  coverage={finding.coverage:.4f}",
                f"    uncertainty  : {finding.uncertainty}",
            ]
        )
        for caveat in finding.data_quality_caveats:
            lines.append(f"    caveat       : {caveat}")
        for alternative in finding.alternative_explanations:
            lines.append(f"    alternative  : {alternative}")
        lines.append(f"    next test    : {finding.next_experiment}")
        if finding.recommendation:
            lines.append(f"    recommend    : {finding.recommendation}")
        else:
            lines.append("    recommend    : (none; insufficient evidence for advice)")
    return "\n".join(lines)

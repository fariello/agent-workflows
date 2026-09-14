#!/usr/bin/env python3
"""EFFECTIVE-DATED pricing: a versioned rate schedule, validated against RECORDED cost.

WHY THIS SCHEDULE IS TESTABLE RATHER THAN DECLARATIVE, WHICH IS THE ONE PLACE THE AUTHORING PLAN WAS
TOO PESSIMISTIC. The plan assumed price history would have to be ASSERTED from an external source and
could therefore never be checked. Measured, it is RECOVERABLE FROM THE CORPUS EXACTLY. Fitting cost
against token components per day yields TWO clean eras and nothing in between:

* ERA A, through the step at ``2026-08-29T01:30:43Z``: input $5.00/Mtok, output $25.00/Mtok,
  cache_read FREE. Reproduces 7917 steps to floating-point exactness.
* ERA B, from the step at ``2026-08-29T05:38:43Z``: input $5.50/Mtok, output $27.50/Mtok, cache_read
  $0.55/Mtok (exactly 10 percent of input, the standard cached-read discount). Reproduces 21731 steps.

There is NO INTERLEAVING across the boundary: zero Era A steps occur after the first Era B step, so a
single effective instant separates them. The residual 23 steps (0.08 percent) are THE SAME 23 that
carry ``reasoning > 0``, and all three of their runs declare ``options.model:
google/gemini-3.8-flash``, a different model at a blended rate near $0.80/Mtok. So the residual is a
MODEL-IDENTITY gap, not a pricing bug, and :func:`price_step` REFUSES those rather than estimating.

TWO SCHEMA CONSEQUENCES, BOTH MEASURED AND BOTH DELIBERATE.

FIRST, THERE IS NO ``cache_write`` RATE COLUMN. Measured: ``cache_write`` is 0 in all 29611 steps
that report a cache object, so a write rate is untestable and inventing one is guessing. The single
``cache`` component the fact schema carries (``run_analytics_schema`` measured ``input``/``output``/
``cache``/``total`` plus ``reasoning``, with NO read/write split anywhere) is therefore priced at the
CACHE-READ rate, JUSTIFIED BY that measured zero. The justification is falsifiable rather than
assumed: :func:`validate_against_recorded` REFUSES a step reporting nonzero ``cache_write``, because
the equivalence that licenses the single rate would no longer hold.

SECOND, A PRICING VIEW THAT OMITS CACHE READS OMITS MOST OF THE MONEY. Least-squares over the Era B
steps apportions 72.1 percent of $2855.75 to cache_read, 20.7 percent to output and 7.6 percent to
input, and cache_read is 98.62 percent of all tokens. That is also the mechanism behind the real
Simpson's-paradox instance in this corpus (see :mod:`agent_workflows.run_analytics_findings`): median
blended $/Mtok rises more than ninefold across the era boundary while the RATES rose only 10 percent,
because cache_read went from free to billable while being nearly all of the tokens.

RECORDED COST IS NEVER OVERWRITTEN. :class:`PricedCost` carries ``recorded_usd`` and ``estimated_usd``
as SEPARATE fields and :attr:`PricedCost.authoritative_usd` prefers the recorded one. An estimate that
replaced a recorded value would destroy the only thing that makes this schedule checkable.

Stdlib only.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "PRICING_SCHEMA_VERSION",
    "PriceRates",
    "PriceEra",
    "PriceSchedule",
    "PricedCost",
    "MEASURED_ERAS",
    "MEASURED_SCHEDULE",
    "ERA_A_LAST_STEP",
    "ERA_B_FIRST_STEP",
    "PRICED_COMPONENTS",
    "PricingRefusal",
    "parse_instant",
    "price_step",
    "validate_against_recorded",
    "stratify_by_era",
    "component_spend_shares",
]


#: The pricing layer's own version, bumped when the SCHEDULE SHAPE changes (a new rate column, a
#: changed interval semantic). Adding an ERA to the seed data does not bump it: eras are data.
PRICING_SCHEMA_VERSION = 1


class PricingRefusal(ValueError):
    """A step could not be priced honestly, so pricing REFUSED rather than estimated.

    Deliberately a refusal and not a fallback estimate. The measured residual is 23 steps from an
    unpriced model; producing a number for those would put a guess beside 29648 exact values with no
    way for a consumer to tell them apart.
    """


#: The exact instants bounding the measured eras, located TO THE STEP. Retained as named constants
#: because V-07 requires a step on each side priced by the correct era, and a boundary test needs the
#: boundary rather than a nearby date.
ERA_A_LAST_STEP = "2026-08-29T01:30:43Z"
ERA_B_FIRST_STEP = "2026-08-29T05:38:43Z"

#: The token components this schedule prices. ``total`` is excluded because it is the SUM and pricing
#: it would double count; ``reasoning`` is excluded because no rate for it is recoverable from this
#: corpus (the 23 steps carrying it are the exact residual) and inventing one is the guess this module
#: refuses. A component absent from this tuple makes :func:`price_step` refuse, which is why the
#: exclusion is a decision rather than an oversight.
PRICED_COMPONENTS: tuple[str, ...] = ("input", "output", "cache")


def parse_instant(value: str | dt.datetime | None) -> dt.datetime | None:
    """Parse an ISO-8601 instant to an aware UTC datetime, or ``None``. Never raises.

    A naive timestamp is assumed UTC, which is what the runners write (every recorded instant in the
    corpus carries ``Z``). Returning ``None`` rather than raising keeps one malformed timestamp from
    ending a corpus sweep.
    """

    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


@dataclass(frozen=True)
class PriceRates:
    """Per-million-token rates for ONE era of ONE model.

    NOTE WHAT IS ABSENT: there is no ``cache_write_per_mtok``. Measured, ``cache_write`` is 0 in all
    29611 steps reporting a cache object, so a write rate could never be validated against recorded
    cost and would be an assertion dressed as data. See the module docstring.

    ``cache_read_per_mtok`` prices the schema's single ``cache`` component. That equivalence is
    licensed by the measured zero above and is checked rather than assumed:
    :func:`validate_against_recorded` refuses a step reporting nonzero ``cache_write``.
    """

    input_per_mtok: float
    output_per_mtok: float
    cache_read_per_mtok: float
    currency: str = "USD"

    def __post_init__(self) -> None:
        for name, value in (
            ("input_per_mtok", self.input_per_mtok),
            ("output_per_mtok", self.output_per_mtok),
            ("cache_read_per_mtok", self.cache_read_per_mtok),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise PricingRefusal(
                    f"{name} must be a number, got {type(value).__name__}"
                )
            if value < 0:
                raise PricingRefusal(f"{name} must be >= 0, got {value}")

    def rate_for(self, component: str) -> float:
        """The per-Mtok rate for one token component, or a REFUSAL for an unpriced one."""

        mapping = {
            "input": self.input_per_mtok,
            "output": self.output_per_mtok,
            # THE SINGLE `cache` COMPONENT IS PRICED AT THE CACHE-READ RATE. Licensed by the measured
            # `cache_write == 0`; see the module docstring and the class docstring.
            "cache": self.cache_read_per_mtok,
        }
        if component not in mapping:
            raise PricingRefusal(
                f"component {component!r} has no recoverable rate in this schedule "
                f"(priced components: {', '.join(PRICED_COMPONENTS)}); "
                "pricing REFUSES rather than estimating one"
            )
        return mapping[component]

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_per_mtok": self.input_per_mtok,
            "output_per_mtok": self.output_per_mtok,
            "cache_read_per_mtok": self.cache_read_per_mtok,
            "currency": self.currency,
            # Stated in the serialized form so a consumer reading only the JSON still learns why.
            "cache_write_per_mtok": None,
            "cache_write_note": (
                "NO cache_write rate column: cache_write was measured 0 in all 29611 steps "
                "reporting a cache object, so a write rate would be untestable invention"
            ),
        }


@dataclass(frozen=True)
class PriceEra:
    """ONE effective-dated rate interval for one provider/model/variant.

    ``effective_from`` is INCLUSIVE and ``effective_to`` EXCLUSIVE (``None`` meaning open-ended), which
    is what makes two adjacent eras cover every instant exactly once. A closed-closed interval would
    make the boundary instant belong to both, and the corpus locates that boundary to the step.
    """

    era_id: str
    provider: str
    model: str
    rates: PriceRates
    effective_from: str
    effective_to: str | None = None
    variant: str = ""
    #: Where the rates came from. ``fit-to-recorded-cost`` means recovered from this corpus and
    #: therefore checkable; an externally asserted schedule would say so and be uncheckable.
    source: str = "fit-to-recorded-cost"
    source_version: str = "2026-09-08"
    #: How many steps this era reproduced exactly when fitted. Retained as evidence.
    exact_match_count: int = 0

    def covers(self, instant: dt.datetime) -> bool:
        start = parse_instant(self.effective_from)
        if start is None or instant < start:
            return False
        end = parse_instant(self.effective_to) if self.effective_to else None
        return end is None or instant < end

    def to_dict(self) -> dict[str, Any]:
        return {
            "era_id": self.era_id,
            "provider": self.provider,
            "model": self.model,
            "variant": self.variant,
            "rates": self.rates.to_dict(),
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "interval_semantics": "from-inclusive-to-exclusive",
            "source": self.source,
            "source_version": self.source_version,
            "exact_match_count": self.exact_match_count,
        }


@dataclass(frozen=True)
class PricedCost:
    """One step's cost: the RECORDED value and the ESTIMATE, kept separate and never merged.

    THE SEPARATION IS THE CONTRACT. An estimate that overwrote a recorded value would destroy the
    only property making this schedule checkable, and a consumer could no longer tell real spend from
    a modeled number. :attr:`authoritative_usd` prefers ``recorded_usd`` and
    :attr:`reproduces_exactly` is the per-step validation result.
    """

    estimated_usd: float | None
    recorded_usd: float | None
    era_id: str
    currency: str = "USD"
    #: Per-component contribution to the estimate, so a discrepancy is attributable.
    component_costs: dict[str, float] = field(default_factory=dict)
    refusal_reason: str = ""

    @property
    def is_refused(self) -> bool:
        return self.estimated_usd is None

    @property
    def authoritative_usd(self) -> float | None:
        """RECORDED cost when there is one, else the estimate. Recorded always wins."""

        return (
            self.recorded_usd if self.recorded_usd is not None else self.estimated_usd
        )

    @property
    def cost_is_estimate(self) -> bool:
        """True only when the authoritative number is an ESTIMATE.

        The same field name Order 02's allowlist already carries (``cost_is_estimate``), so the two
        layers use one vocabulary for the distinction rather than two.
        """

        return self.recorded_usd is None and self.estimated_usd is not None

    @property
    def delta(self) -> float | None:
        if self.recorded_usd is None or self.estimated_usd is None:
            return None
        return self.estimated_usd - self.recorded_usd

    def reproduces_exactly(self, *, tolerance: float = 1e-9) -> bool:
        """Does the estimate reproduce the recorded cost within ``tolerance``?

        The default is FLOATING-POINT tolerance, not a business tolerance. The measured eras reproduce
        recorded cost to floating-point exactness over 29648 steps, so a loose tolerance here would
        hide a real rate error behind rounding.
        """

        delta = self.delta
        return delta is not None and abs(delta) <= tolerance

    def to_dict(self) -> dict[str, Any]:
        return {
            "recorded_usd": self.recorded_usd,
            "estimated_usd": self.estimated_usd,
            "authoritative_usd": self.authoritative_usd,
            "cost_is_estimate": self.cost_is_estimate,
            "era_id": self.era_id,
            "currency": self.currency,
            "component_costs": {
                k: round(v, 10) for k, v in sorted(self.component_costs.items())
            },
            "delta": self.delta,
            "reproduces_exactly": self.reproduces_exactly(),
            "is_refused": self.is_refused,
            "refusal_reason": self.refusal_reason,
        }


@dataclass(frozen=True)
class PriceSchedule:
    """The versioned, effective-dated schedule. Data, not logic.

    ``eras`` are searched newest-effective-first so an open-ended current era is found without a
    linear scan of history. A model with no era is REFUSED rather than priced at a default, which is
    what keeps an unknown model from silently inheriting another model's rates.
    """

    eras: tuple[PriceEra, ...] = ()
    schedule_version: str = "2026-09-08"

    def era_for(
        self,
        *,
        instant: dt.datetime,
        provider: str = "",
        model: str = "",
        variant: str = "",
    ) -> PriceEra | None:
        """The era covering ``instant`` for this model, or ``None``.

        Matching on provider/model/variant is EXACT when the caller supplies one and permissive when
        it supplies an empty string, which is how a corpus whose model identity is 98.9 percent absent
        can still be priced by date: the era is selected by time and the caller states that it does
        not know the model. That permissiveness is why :func:`validate_against_recorded` exists, since
        a wrongly-dated step would otherwise be priced silently.
        """

        candidates = [
            era
            for era in self.eras
            if era.covers(instant)
            and (not provider or not era.provider or era.provider == provider)
            and (not model or not era.model or era.model == model)
            and (not variant or not era.variant or era.variant == variant)
        ]
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda e: parse_instant(e.effective_from)
            or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
            reverse=True,
        )[0]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pricing_schema_version": PRICING_SCHEMA_VERSION,
            "schedule_version": self.schedule_version,
            "priced_components": list(PRICED_COMPONENTS),
            "eras": [era.to_dict() for era in self.eras],
        }

    def format_report(self) -> str:
        """A pasteable schedule report. No path, no absolute location."""

        lines = [
            f"pricing_schema_version={PRICING_SCHEMA_VERSION} "
            f"schedule_version={self.schedule_version}",
            f"priced components: {', '.join(PRICED_COMPONENTS)} "
            "(NO cache_write rate column; cache_write measured 0 in all 29611 steps)",
        ]
        for era in self.eras:
            rates = era.rates
            lines.append(
                f"  {era.era_id:<8} {era.provider or '<any>'}/{era.model or '<any>'}  "
                f"[{era.effective_from} .. {era.effective_to or 'open'})  "
                f"input=${rates.input_per_mtok:.2f} output=${rates.output_per_mtok:.2f} "
                f"cache_read=${rates.cache_read_per_mtok:.2f}  "
                f"exact_matches={era.exact_match_count}  source={era.source}"
            )
        return "\n".join(lines)


# --- The measured seed data ----------------------------------------------------------------------
#: THE TWO MEASURED ERAS, recovered by fitting recorded cost against token components per day at
#: review (2026-09-08). SEED DATA, and checkable: :func:`validate_against_recorded` reproduces
#: recorded cost from them, which is the property the authoring plan believed unobtainable.
#:
#: `provider`/`model` are deliberately EMPTY, and that is a measurement result rather than laziness:
#: model identity resolves for 2 of 179 attempts (1.1 percent), so an era keyed to a specific model
#: name would match almost nothing. The eras are keyed by TIME, which is the signal that exists.
MEASURED_ERAS: tuple[PriceEra, ...] = (
    PriceEra(
        era_id="era-a",
        provider="",
        model="",
        rates=PriceRates(
            input_per_mtok=5.00,
            output_per_mtok=25.00,
            # FREE, which is the whole cause of the Simpson's-paradox instance in this corpus: cache
            # reads are 98.62 percent of tokens, so their becoming billable in Era B moved the blended
            # rate ninefold while the real rates rose 10 percent.
            cache_read_per_mtok=0.00,
        ),
        effective_from="2026-01-01T00:00:00Z",
        effective_to=ERA_B_FIRST_STEP,
        exact_match_count=7917,
    ),
    PriceEra(
        era_id="era-b",
        provider="",
        model="",
        rates=PriceRates(
            input_per_mtok=5.50,
            output_per_mtok=27.50,
            # Exactly 10 percent of input, the standard cached-read discount.
            cache_read_per_mtok=0.55,
        ),
        effective_from=ERA_B_FIRST_STEP,
        effective_to=None,
        exact_match_count=21731,
    ),
)

#: The seeded schedule. A caller may build its own; this one carries the measured eras.
MEASURED_SCHEDULE = PriceSchedule(eras=MEASURED_ERAS)

#: Model identifiers measured to be OUTSIDE both eras' rates. The 23 residual steps all carry
#: ``reasoning > 0`` and all three of their runs declare this model at a blended rate near
#: $0.80/Mtok, so it is a model-identity gap rather than a pricing bug. Named so the refusal can say
#: WHICH model it declined, which is more useful than a generic "unknown".
UNPRICED_MODELS: frozenset[str] = frozenset({"google/gemini-3.8-flash"})


def price_step(
    *,
    tokens: Mapping[str, Any],
    at: str | dt.datetime,
    recorded_usd: float | None = None,
    schedule: PriceSchedule = MEASURED_SCHEDULE,
    provider: str = "",
    model: str = "",
    variant: str = "",
    currency: str = "USD",
) -> PricedCost:
    """Estimate ONE step's cost from the effective-dated schedule, REFUSING where it cannot.

    FIVE REFUSAL CASES, each measured or structural rather than defensive boilerplate:

    1. An UNPRICED MODEL (:data:`UNPRICED_MODELS`). The measured 23-step residual, whose rates this
       corpus does not contain. Refused rather than priced at the nearest era's rates.
    2. A step carrying ``reasoning > 0``. Those ARE the 23 residual steps, and no reasoning rate is
       recoverable, so pricing one would silently omit a billed component.
    3. NO ERA covering the instant. An unknown date is not the current era's date.
    4. An UNPARSEABLE instant. A step with no time has no era, and guessing one would assign a rate
       by accident.
    5. A CURRENCY MISMATCH between the caller and the era. Adding USD to EUR is arithmetic on
       incomparable units and would be invisible in the total.

    ``recorded_usd`` is carried through UNTOUCHED. It is never overwritten and never merged with the
    estimate; see :class:`PricedCost`.
    """

    instant = parse_instant(at)
    if instant is None:
        return PricedCost(
            estimated_usd=None,
            recorded_usd=recorded_usd,
            era_id="",
            currency=currency,
            refusal_reason=f"unparseable instant {str(at)[:40]!r}; a step with no time has no era",
        )

    if model and model in UNPRICED_MODELS:
        return PricedCost(
            estimated_usd=None,
            recorded_usd=recorded_usd,
            era_id="",
            currency=currency,
            refusal_reason=(
                f"model {model!r} has no recoverable rate in this corpus (it is the measured "
                "23-step residual, all carrying reasoning>0); pricing REFUSES rather than "
                "estimating from another model's era"
            ),
        )

    reasoning = tokens.get("reasoning")
    if (
        isinstance(reasoning, (int, float))
        and not isinstance(reasoning, bool)
        and reasoning > 0
    ):
        return PricedCost(
            estimated_usd=None,
            recorded_usd=recorded_usd,
            era_id="",
            currency=currency,
            refusal_reason=(
                f"step carries reasoning={reasoning} and no reasoning rate is recoverable from "
                "this corpus; these are exactly the 23 residual steps, and pricing one would "
                "silently omit a billed component"
            ),
        )

    era = schedule.era_for(
        instant=instant, provider=provider, model=model, variant=variant
    )
    if era is None:
        return PricedCost(
            estimated_usd=None,
            recorded_usd=recorded_usd,
            era_id="",
            currency=currency,
            refusal_reason=(
                f"no price era covers {instant.isoformat()} for "
                f"provider={provider or '<unknown>'} model={model or '<unknown>'}; "
                "an unknown date is not the current era's date"
            ),
        )

    if era.rates.currency != currency:
        return PricedCost(
            estimated_usd=None,
            recorded_usd=recorded_usd,
            era_id=era.era_id,
            currency=currency,
            refusal_reason=(
                f"currency mismatch: caller asked for {currency!r} and era {era.era_id!r} is "
                f"priced in {era.rates.currency!r}; summing incomparable units would be invisible "
                "in the total"
            ),
        )

    component_costs: dict[str, float] = {}
    for component in PRICED_COMPONENTS:
        raw = tokens.get(component)
        if raw is None:
            continue
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            continue
        component_costs[component] = (
            float(raw) * era.rates.rate_for(component) / 1_000_000.0
        )

    return PricedCost(
        estimated_usd=sum(component_costs.values()),
        recorded_usd=recorded_usd,
        era_id=era.era_id,
        currency=currency,
        component_costs=component_costs,
    )


def validate_against_recorded(
    steps: Sequence[Mapping[str, Any]],
    *,
    schedule: PriceSchedule = MEASURED_SCHEDULE,
    tolerance: float = 1e-9,
) -> dict[str, Any]:
    """Reproduce RECORDED cost for every step and report exact-match counts PER ERA.

    THIS IS THE FUNCTION THAT MAKES THE SCHEDULE EVIDENCE RATHER THAN AN ASSERTION, and it is the
    one to run over a live corpus: it recomputes every count from the input, so the measured figures
    (7917 Era A, 21731 Era B, 23 residual at review) are reproduced rather than restated.

    Each step is ``{"tokens": {...}, "at": str, "cost": float, "model": str|None,
    "cache_write": int|None}``.

    A step reporting NONZERO ``cache_write`` is REFUSED, not mispriced. That is the falsification
    path for D-2: the single ``cache`` component is priced at the cache-read rate because
    ``cache_write`` was measured 0 everywhere, so a nonzero one means the licensing measurement no
    longer holds and a silent mispricing would follow.
    """

    per_era: dict[str, dict[str, Any]] = {}
    refused: list[dict[str, Any]] = []
    mismatched: list[dict[str, Any]] = []
    exact = 0
    checked = 0

    for index, step in enumerate(steps):
        tokens = step.get("tokens")
        tokens = tokens if isinstance(tokens, Mapping) else {}
        recorded = step.get("cost")
        recorded_usd = (
            float(recorded)
            if isinstance(recorded, (int, float)) and not isinstance(recorded, bool)
            else None
        )

        cache_write = step.get("cache_write")
        if (
            isinstance(cache_write, (int, float))
            and not isinstance(cache_write, bool)
            and cache_write > 0
        ):
            refused.append(
                {
                    "index": index,
                    "era_id": "",
                    "reason": (
                        f"step reports cache_write={cache_write}, which was measured 0 in all "
                        "29611 corpus steps; the single `cache` component is priced at the "
                        "cache-read rate ON THAT BASIS, so a nonzero write invalidates the "
                        "equivalence and pricing REFUSES rather than mispricing"
                    ),
                }
            )
            continue

        priced = price_step(
            tokens=tokens,
            at=str(step.get("at") or ""),
            recorded_usd=recorded_usd,
            schedule=schedule,
            model=str(step.get("model") or ""),
        )
        if priced.is_refused:
            refused.append(
                {
                    "index": index,
                    "era_id": priced.era_id,
                    "reason": priced.refusal_reason,
                }
            )
            continue

        bucket = per_era.setdefault(
            priced.era_id,
            {
                "checked": 0,
                "exact": 0,
                "mismatched": 0,
                "estimated_usd": 0.0,
                "recorded_usd": 0.0,
            },
        )
        bucket["checked"] += 1
        bucket["estimated_usd"] += priced.estimated_usd or 0.0
        if priced.recorded_usd is not None:
            bucket["recorded_usd"] += priced.recorded_usd
        checked += 1
        if priced.reproduces_exactly(tolerance=tolerance):
            exact += 1
            bucket["exact"] += 1
        else:
            bucket["mismatched"] += 1
            mismatched.append(
                {
                    "index": index,
                    "era_id": priced.era_id,
                    "estimated_usd": priced.estimated_usd,
                    "recorded_usd": priced.recorded_usd,
                    "delta": priced.delta,
                }
            )

    return {
        "pricing_schema_version": PRICING_SCHEMA_VERSION,
        "steps_supplied": len(steps),
        "steps_priced": checked,
        "exact_matches": exact,
        "mismatches": len(mismatched),
        "refusals": len(refused),
        "per_era": {
            era: {
                **stats,
                "estimated_usd": round(stats["estimated_usd"], 6),
                "recorded_usd": round(stats["recorded_usd"], 6),
            }
            for era, stats in sorted(per_era.items())
        },
        "mismatch_detail": mismatched[:50],
        "refusal_detail": refused[:50],
        "boundary_instants": {
            "era_a_last_step": ERA_A_LAST_STEP,
            "era_b_first_step": ERA_B_FIRST_STEP,
            "note": "no interleaving was measured across this boundary",
        },
        "has_cache_write_rate_column": False,
    }


def stratify_by_era(
    steps: Iterable[Mapping[str, Any]],
    *,
    schedule: PriceSchedule = MEASURED_SCHEDULE,
) -> dict[str, list[Mapping[str, Any]]]:
    """Group steps by price era. THE REQUIRED CONTROL BEFORE ANY COST COMPARISON.

    Any cost-efficiency comparison that POOLS across the 2026-08-29 boundary attributes a
    pricing-policy change to workflow behavior: blended $/Mtok rises from $0.054-$0.071 to
    $0.635-$0.737 across it, a more-than-ninefold apparent jump caused by cache_read becoming billable
    while being 98.62 percent of tokens, NOT by the 10 percent rate change. Stratifying first is the
    control, and :mod:`agent_workflows.run_analytics_findings` ships that case as a golden test.

    A step whose era cannot be resolved lands under ``"unknown"`` rather than being dropped, so a
    pooled comparison cannot hide behind a silently shrunken denominator.
    """

    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for step in steps:
        instant = parse_instant(str(step.get("at") or ""))
        era = (
            schedule.era_for(instant=instant, model=str(step.get("model") or ""))
            if instant
            else None
        )
        grouped.setdefault(era.era_id if era else "unknown", []).append(step)
    return grouped


def component_spend_shares(
    steps: Sequence[Mapping[str, Any]],
    *,
    schedule: PriceSchedule = MEASURED_SCHEDULE,
) -> dict[str, Any]:
    """Apportion estimated spend across token components, per era and overall.

    Measured at review over the Era B steps: 72.1 percent of $2855.75 to cache_read, 20.7 percent to
    output, 7.6 percent to input. Recomputed here from the input, which is what makes "a pricing view
    that omits cache reads omits nearly three quarters of the money" a checkable claim rather than a
    remembered one.
    """

    per_era: dict[str, dict[str, float]] = {}
    overall: dict[str, float] = {}
    for step in steps:
        tokens = step.get("tokens")
        priced = price_step(
            tokens=tokens if isinstance(tokens, Mapping) else {},
            at=str(step.get("at") or ""),
            schedule=schedule,
            model=str(step.get("model") or ""),
        )
        if priced.is_refused:
            continue
        bucket = per_era.setdefault(priced.era_id, {})
        for component, amount in priced.component_costs.items():
            bucket[component] = bucket.get(component, 0.0) + amount
            overall[component] = overall.get(component, 0.0) + amount

    def shares(bucket: Mapping[str, float]) -> dict[str, float]:
        total = sum(bucket.values())
        if not total:
            return {}
        return {
            name: round(amount / total, 6) for name, amount in sorted(bucket.items())
        }

    return {
        "overall_spend_usd": {k: round(v, 6) for k, v in sorted(overall.items())},
        "overall_shares": shares(overall),
        "per_era_spend_usd": {
            era: {k: round(v, 6) for k, v in sorted(bucket.items())}
            for era, bucket in sorted(per_era.items())
        },
        "per_era_shares": {
            era: shares(bucket) for era, bucket in sorted(per_era.items())
        },
    }

#!/usr/bin/env python3
"""The normalized analytics FACT SCHEMA: grains, provenance, usage components, conservation.

WHAT THIS IS. Every chart, query, export and finding downstream reads facts defined here and never
reparses a run directory. So this module is a CONTRACT rather than an internal detail: Orders 06
through 10 of the ``runanalytics`` Set consume it, and a field's meaning changing here changes their
input. It holds the vocabulary and the invariants; :mod:`agent_workflows.run_analytics_sources`
holds the adapters that read on-disk artifacts, and :mod:`agent_workflows.run_analytics` composes
the two.

THE FOUR-STATE PROVENANCE IS IRREDUCIBLE, AND IT IS THE POINT OF THE MODULE.
``measured``/``recorded``/``derived`` say WHERE a present number came from; ``missing``,
``unavailable`` and ``not-applicable`` are three DIFFERENT facts about an absent one, and NONE of
them is zero:

* ``missing`` - the source should carry it and does not (a defect, or an interrupted write).
* ``unavailable`` - the source cannot carry it here (an older driver generation never wrote it).
* ``not-applicable`` - the question does not apply (a review-only attempt has no verify cost).

They are encoded as an explicit :class:`Provenance` enum on a :class:`Value`, NEVER as a nullable
number, because a nullable number invites a later ``or 0`` and one ``or 0`` silently converts "we
do not know" into "it was free". :meth:`Value.as_number` REFUSES to produce a number for an absent
value; a caller that wants a default must ask for one by name and thereby say so in its own code.

THE TOKEN COMPONENT MAP IS OPEN, BECAUSE A CLOSED ONE WAS MEASURED WRONG. The plan that authored
this schema enumerated ``input``, ``output``, "cache read/write when distinguishable" and ``total``.
Measured over this repository's own run corpus at review, the keys actually present were ``input``,
``output``, ``cache`` and ``total`` (176 attempts each) plus ``reasoning`` (2 attempts): the
cache-read/cache-write split appears NOWHERE and ``reasoning`` was unanticipated. Five named
columns would therefore have dropped ``reasoning`` on the floor and would drop the next provider's
component key too, so :class:`Usage` carries a dict whose keys are provider-chosen. The sibling
privacy projector already agrees: ``run_analytics_privacy._OPEN_NUMBER_MAP_KEYS`` contains
``tokens`` and shape-checks its keys as labels rather than allowlisting them by name.

CONSERVATION IS A SUM OVER *ALL* COMPONENTS, WHICH IS THE ONLY FORM THAT HOLDS. See
:func:`check_conservation` for the measurement that settled it: the four-term
``input + output + cache == total`` holds for 174 of 176 real attempts and FAILS for exactly the 2
carrying ``reasoning``, where the shortfall equals ``reasoning`` exactly (deltas 2658 and 1120),
while ``sum(every component except total) == total`` holds 176 of 176. The four-term form would have
fired a FALSE violation on real data, whose likely repair is to loosen the assertion, which destroys
the only mechanism this schema has for making double counting detectable. An unknown component key
participates in the sum AUTOMATICALLY, so the check is open in the same way the map is.

TIME IS NOT FORCED TO ADD UP. Wall-clock elapsed and observed activity are separate observations,
and activities OVERLAP. :class:`TimeAccounting` therefore publishes ``observed_activity_seconds``,
``unattributed_seconds`` and ``overlap_seconds`` instead of distributing elapsed time across
activities, because a distribution is a model and this layer stores observations.

Stdlib only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "FACT_SCHEMA_VERSION",
    "Provenance",
    "PRESENT_PROVENANCE",
    "ABSENT_PROVENANCE",
    "Grain",
    "Phase",
    "PHASES",
    "Value",
    "measured",
    "recorded",
    "derived",
    "missing",
    "unavailable",
    "not_applicable",
    "Usage",
    "TimeAccounting",
    "Fact",
    "ConservationResult",
    "TOKEN_TOTAL_KEY",
    "check_conservation",
    "check_conservation_four_term",
    "QualitySummary",
    "SchemaError",
]


#: The fact schema's own version. Downstream Orders treat the fact shape as a contract, so a change
#: in a field's MEANING bumps this; an additive field does not.
FACT_SCHEMA_VERSION = 1


class SchemaError(ValueError):
    """A fact violated the schema's own rules (not the privacy allowlist's).

    Deliberately distinct from ``run_analytics_privacy.PrivacyRefusal``: this one means the fact is
    malformed, that one means the fact is unsafe, and conflating them would let a producer "fix" a
    privacy refusal by satisfying a shape check.
    """


# --- Provenance ---------------------------------------------------------------------------------
class Provenance(str, Enum):
    """WHERE a value came from, or WHY it is absent. Six states, three present and three absent.

    A ``str`` enum so a projected fact carries the bare token (``"measured"``) rather than a repr,
    which is what keeps the persisted form readable and the privacy allowlist's label check happy.
    """

    #: Observed directly by this toolkit while the work happened (a probe, a clock).
    MEASURED = "measured"
    #: Read verbatim from a value the runner or provider recorded in the source artifact.
    RECORDED = "recorded"
    #: Computed from other values. A derived total is LABELED so a consumer never mistakes a sum
    #: this toolkit performed for one the provider reported.
    DERIVED = "derived"
    #: The source SHOULD carry it and does not. A defect or a truncated write.
    MISSING = "missing"
    #: The source CANNOT carry it here (an older driver generation never wrote this field).
    UNAVAILABLE = "unavailable"
    #: The question does not apply to this record (a review-only attempt has no verify usage).
    NOT_APPLICABLE = "not-applicable"


#: Provenances whose value is present and numeric.
PRESENT_PROVENANCE: frozenset[Provenance] = frozenset(
    {Provenance.MEASURED, Provenance.RECORDED, Provenance.DERIVED}
)

#: Provenances whose value is ABSENT. Three distinct facts, none of them zero. Kept as its own set
#: so a consumer can branch on absence without enumerating the three and accidentally omitting one.
ABSENT_PROVENANCE: frozenset[Provenance] = frozenset(
    {Provenance.MISSING, Provenance.UNAVAILABLE, Provenance.NOT_APPLICABLE}
)


class Grain(str, Enum):
    """The keying level of one fact record.

    Coarse to fine. The finer grains exist so a later Order can compute a median, a dispersion or a
    regression WITHOUT reparsing source files, which is why raw per-attempt observations are kept
    rather than only per-run aggregates.
    """

    RUN = "run"
    SET = "set"
    IPD = "ipd"
    ATTEMPT = "attempt"
    PHASE = "phase"
    EVENT = "event"


class Phase(str, Enum):
    """The run phase a measurement belongs to.

    ``REVIEW``/``EXECUTE``/``VERIFY``/``RECOVERY`` are the four the existing run summaries already
    separate or that the runners distinguish; ``UNKNOWN`` is honest rather than a guess. Deliberately
    coarse: a finer name would drift with the runners' internals and become free text in practice,
    which the privacy projector's closed-vocabulary check would then reject.
    """

    REVIEW = "review"
    EXECUTE = "execute"
    VERIFY = "verify"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


PHASES: tuple[Phase, ...] = (
    Phase.REVIEW,
    Phase.EXECUTE,
    Phase.VERIFY,
    Phase.RECOVERY,
    Phase.UNKNOWN,
)


# --- Value --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Value:
    """One numeric observation WITH its provenance, or a typed absence.

    THE INVARIANT THIS TYPE EXISTS TO ENFORCE: an absent value has ``number is None`` and cannot be
    read as a number. :meth:`as_number` raises for an absent value rather than returning ``0``, and
    :meth:`or_default` makes a caller that genuinely wants a fallback NAME it at the call site. That
    is the whole mechanism preventing "missing" from silently becoming "zero" three modules later.
    """

    number: float | int | None
    provenance: Provenance
    #: Optional short label naming the unit or the derivation, e.g. ``"sum-of-components"``. Kept a
    #: LABEL (no spaces, no path) so it survives the privacy projector's closed-vocabulary check.
    note: str = ""

    def __post_init__(self) -> None:
        if self.provenance in PRESENT_PROVENANCE:
            if self.number is None:
                raise SchemaError(
                    f"provenance {self.provenance.value!r} asserts a value is present, "
                    "so `number` may not be None"
                )
            if isinstance(self.number, bool) or not isinstance(
                self.number, (int, float)
            ):
                raise SchemaError(
                    f"a present value must be a real number, got "
                    f"{type(self.number).__name__}"
                )
            if self.number != self.number or self.number in (
                float("inf"),
                float("-inf"),
            ):
                raise SchemaError("a present value must be finite")
        else:
            if self.number is not None:
                raise SchemaError(
                    f"provenance {self.provenance.value!r} asserts a value is ABSENT, so "
                    f"`number` must be None (got {self.number!r}); an absent value is NOT zero"
                )
        if self.note and not _LABEL_RE.match(self.note):
            raise SchemaError(
                f"note {self.note[:32]!r} is not a short label (free text is refused so the "
                "value survives the privacy projector)"
            )

    @property
    def is_present(self) -> bool:
        return self.provenance in PRESENT_PROVENANCE

    @property
    def is_absent(self) -> bool:
        return self.provenance in ABSENT_PROVENANCE

    def as_number(self) -> float | int:
        """The number, or a REFUSAL for an absent value. Never a silent zero.

        This is the method that makes the four-state distinction load-bearing instead of
        decorative: an aggregation that forgets to branch on absence fails loudly here rather than
        quietly averaging in a zero.
        """

        if self.number is None:
            raise SchemaError(
                f"value is {self.provenance.value!r}, which is NOT zero and has no number; "
                "branch on `is_absent` or call `or_default(...)` to state your fallback"
            )
        return self.number

    def or_default(self, default: float | int) -> float | int:
        """The number, or ``default`` for an absent value, with the fallback stated by the caller."""

        return default if self.number is None else self.number

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "value": self.number,
            "provenance": self.provenance.value,
        }
        if self.note:
            payload["note"] = self.note
        return payload


_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+@/-]{0,63}$")

#: The pattern a TOKEN COMPONENT NAME must match. Deliberately STRICTER than :data:`_LABEL_RE`: it
#: forbids ``/``, which the general label pattern permits because a ``model`` value legitimately
#: carries one (``provider/model``).
#:
#: WHY THE EXTRA STRICTNESS IS LOAD-BEARING, since a component name is provider-chosen and this is a
#: privacy boundary the schema owns. The sibling projector shape-checks an open map's keys with its
#: own label pattern plus a path test, and that path test (``_looks_like_path``) only catches a
#: LEADING ``/``, ``~``, ``..`` or a drive letter. Measured: a component named
#: ``tokens<absolute-home-path>`` (a path EMBEDDED after a harmless prefix) satisfies both and is
#: passed through, so a home path can ride into a persisted fact through a component KEY. A token
#: component name has no legitimate use for a path separator, so refusing it here closes that route
#: at the point the name enters the schema, upstream of the projector, without weakening any shared
#: predicate other records depend on.
_COMPONENT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")


def measured(number: float | int, note: str = "") -> Value:
    """A value this toolkit observed directly."""

    return Value(number, Provenance.MEASURED, note)


def recorded(number: float | int, note: str = "") -> Value:
    """A value read verbatim from the source artifact."""

    return Value(number, Provenance.RECORDED, note)


def derived(number: float | int, note: str = "") -> Value:
    """A value this toolkit computed. LABELED as derived so no consumer mistakes it for reported."""

    return Value(number, Provenance.DERIVED, note)


def missing(note: str = "") -> Value:
    """The source should carry this and does not."""

    return Value(None, Provenance.MISSING, note)


def unavailable(note: str = "") -> Value:
    """The source cannot carry this here (e.g. an older driver generation)."""

    return Value(None, Provenance.UNAVAILABLE, note)


def not_applicable(note: str = "") -> Value:
    """The question does not apply to this record."""

    return Value(None, Provenance.NOT_APPLICABLE, note)


# --- Usage --------------------------------------------------------------------------------------
#: The component name reserved for the provider-reported TOTAL. Every OTHER key in a
#: :class:`Usage` component map is a component that participates in the conservation sum.
TOKEN_TOTAL_KEY = "total"


@dataclass(frozen=True)
class Usage:
    """Token components (an OPEN map) plus cost, each with provenance.

    ``components`` keys are PROVIDER-CHOSEN and deliberately not enumerated here; see the module
    docstring for the measurement that killed the closed five-column form. ``total`` is stored
    inside the same map (under :data:`TOKEN_TOTAL_KEY`) rather than as a separate field, because
    that is the shape the runners already write (``attempt["tokens"]`` is one dict containing
    ``total``) and reshaping it here would create a second vocabulary for the same data.
    """

    #: component name -> observation. An unseen key is PRESERVED, never dropped.
    components: dict[str, Value] = field(default_factory=dict)
    cost: Value = field(default_factory=lambda: missing("no-cost-recorded"))
    cost_currency: str = "USD"
    #: How many provider component NAMES were refused as unsafe labels and dropped. Its own field,
    #: NOT a component: a count added to ``components`` would enter the conservation sum and make a
    #: defensive drop look like a conservation violation.
    dropped_component_count: int = 0

    def __post_init__(self) -> None:
        for name in self.components:
            if not _COMPONENT_NAME_RE.match(str(name)):
                raise SchemaError(
                    f"token component name {str(name)[:32]!r} is not a short component label "
                    "(letters, digits, '.', '_', '+', '-'; no path separator, no space)"
                )

    @property
    def component_names(self) -> tuple[str, ...]:
        """Every component EXCEPT the reserved total, sorted. These are the conservation summands."""

        return tuple(sorted(n for n in self.components if n != TOKEN_TOTAL_KEY))

    @property
    def total(self) -> Value:
        """The provider-reported total, or a typed absence. NEVER silently derived here.

        A caller that wants a computed total asks :meth:`derived_total`, which labels it, so the
        difference between "the provider said 12345" and "we added it up" is never lost.
        """

        return self.components.get(TOKEN_TOTAL_KEY, missing("no-total-recorded"))

    def derived_total(self) -> Value:
        """Sum of every present component except the total, LABELED ``derived``.

        Absent components are SKIPPED rather than counted as zero, and if every component is absent
        the result is absent too rather than ``0``: a sum of nothing known is not zero tokens.
        """

        present = [
            self.components[n].as_number()
            for n in self.component_names
            if self.components[n].is_present
        ]
        if not present:
            return missing("no-components-present")
        return derived(sum(present), "sum-of-components")

    def to_dict(self) -> dict[str, Any]:
        return {
            "components": {n: v.to_dict() for n, v in sorted(self.components.items())},
            "cost": self.cost.to_dict(),
            "cost_currency": self.cost_currency,
            "dropped_component_count": self.dropped_component_count,
        }

    def component_numbers(self) -> dict[str, float | int]:
        """Present components as plain numbers, in the shape the privacy projector's open map wants.

        Absent components are OMITTED rather than zero-filled, so the projected map never asserts a
        count that was never observed.
        """

        return {
            n: v.as_number() for n, v in sorted(self.components.items()) if v.is_present
        }


# --- Time ---------------------------------------------------------------------------------------
@dataclass(frozen=True)
class TimeAccounting:
    """Wall-clock and activity time as SEPARATE observations, never reconciled by force.

    Activities overlap (a verify turn can run while a sampler ticks), so distributing elapsed time
    across them would require a model this layer refuses to impose. Instead all three quantities are
    published and a consumer can see exactly how much time is accounted for, how much is double
    counted, and how much is simply unknown.
    """

    wall_seconds: Value = field(default_factory=lambda: missing("no-interval"))
    observed_activity_seconds: Value = field(
        default_factory=lambda: missing("no-activity")
    )
    overlap_seconds: Value = field(default_factory=lambda: missing("no-activity"))
    unattributed_seconds: Value = field(default_factory=lambda: missing("no-activity"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "wall_seconds": self.wall_seconds.to_dict(),
            "observed_activity_seconds": self.observed_activity_seconds.to_dict(),
            "overlap_seconds": self.overlap_seconds.to_dict(),
            "unattributed_seconds": self.unattributed_seconds.to_dict(),
        }


def account_intervals(
    intervals: Sequence[tuple[float, float]],
    *,
    wall_start: float | None = None,
    wall_end: float | None = None,
) -> TimeAccounting:
    """Build a :class:`TimeAccounting` from raw ``(start, end)`` activity intervals.

    ``observed_activity_seconds`` is the UNION of the intervals (each wall second counted once),
    ``overlap_seconds`` is the excess of the naive sum over that union (the double counting, made
    visible rather than hidden), and ``unattributed_seconds`` is elapsed wall time no interval
    covers. Deliberately NOT clamped: if the union exceeds the wall window the unattributed value
    reports a negative, because a negative here is real evidence of a clock or attribution defect
    and silently flooring it to zero would erase exactly that signal.
    """

    clean = [
        (float(a), float(b)) for a, b in intervals if b is not None and a is not None
    ]
    clean = [(a, b) for a, b in clean if b >= a]
    if not clean:
        if wall_start is None or wall_end is None:
            return TimeAccounting()
        wall = max(0.0, float(wall_end) - float(wall_start))
        return TimeAccounting(
            wall_seconds=measured(wall, "elapsed"),
            observed_activity_seconds=measured(0.0, "no-intervals"),
            overlap_seconds=measured(0.0, "no-intervals"),
            unattributed_seconds=derived(wall, "wall-minus-union"),
        )

    naive = sum(b - a for a, b in clean)
    merged: list[list[float]] = []
    for a, b in sorted(clean):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    union = sum(b - a for a, b in merged)

    accounting_wall: Value
    unattributed: Value
    if wall_start is not None and wall_end is not None:
        wall = float(wall_end) - float(wall_start)
        accounting_wall = measured(wall, "elapsed")
        unattributed = derived(wall - union, "wall-minus-union")
    else:
        accounting_wall = missing("no-wall-interval")
        unattributed = unavailable("no-wall-interval")

    return TimeAccounting(
        wall_seconds=accounting_wall,
        observed_activity_seconds=measured(union, "interval-union"),
        overlap_seconds=derived(naive - union, "sum-minus-union"),
        unattributed_seconds=unattributed,
    )


# --- Fact ---------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Fact:
    """ONE normalized fact record at one :class:`Grain`.

    Identity keys are all optional because they are grain-dependent: a ``RUN``-grain fact has no
    ``attempt``, and an ``EVENT``-grain fact has no ``ipd_id6`` when the event is run-scoped. What is
    NOT optional is that an absent number carries a typed :class:`Provenance`, which is enforced by
    :class:`Value` rather than here.

    ``source`` names the artifact family a fact was read from (``state``, ``events``, ``outcome``,
    ``session``, ``telemetry``, ``ledger``) so a consumer can trace a number to its provenance
    without the fact carrying a path. It is a LABEL, never a filename, because a filename inside a
    run directory is a relative path today and an absolute one after one careless refactor.
    """

    grain: Grain
    #: The driver run id, e.g. ``run-20260908T101112Z-1234``.
    run_id: str = ""
    set_id: str = ""
    ipd_id6: str = ""
    position: int | None = None
    attempt: int | None = None
    phase: Phase = Phase.UNKNOWN
    #: Ordinal DISTINGUISHING otherwise-identical observations in one stream, e.g. the Nth line of
    #: ``events.jsonl``. Part of :attr:`identity`, and it must be, because an event-grain fact carries
    #: no ``attempt`` and often no ``ipd_id6``: without an ordinal every event in a run collapses to
    #: ONE identity and deduplication silently discards the whole stream but the first line. That
    #: was a measured defect in this module, caught by a fixture with two valid event lines
    #: surviving as one fact, which is why the field exists rather than being inferred.
    sequence: int | None = None
    #: Artifact family this fact was read from. A short label, never a path.
    source: str = ""
    #: Driver generation label, e.g. ``oc_runipd``. Inferred from the driver basename, because
    #: ``schema_version`` was measured uniformly ``1`` across every generation and discriminates
    #: nothing.
    driver_generation: str = ""
    host: str = ""
    model: str = ""
    outcome: str = ""
    usage: Usage = field(default_factory=Usage)
    time: TimeAccounting = field(default_factory=TimeAccounting)
    started_at: str = ""
    ended_at: str = ""
    #: Short labels naming what was missing/unavailable/not-applicable, for the quality summary.
    quality_flags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": FACT_SCHEMA_VERSION,
            "grain": self.grain.value,
            "run_id": self.run_id,
            "set_id": self.set_id,
            "ipd_id6": self.ipd_id6,
            "position": self.position,
            "attempt": self.attempt,
            "sequence": self.sequence,
            "phase": self.phase.value,
            "source": self.source,
            "driver_generation": self.driver_generation,
            "host": self.host,
            "model": self.model,
            "outcome": self.outcome,
            "usage": self.usage.to_dict(),
            "time": self.time.to_dict(),
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "quality_flags": list(self.quality_flags),
        }

    @property
    def identity(self) -> tuple[Any, ...]:
        """The DEDUPLICATION key: what makes two fact records the same observation.

        Includes ``attempt``, which is why a retried item contributes two attempt-grain facts rather
        than one doubled fact, and includes ``phase``, which is why an execute and a verify
        measurement of the same attempt do not collide.
        """

        return (
            self.grain.value,
            self.run_id,
            self.ipd_id6,
            self.position,
            self.attempt,
            self.sequence,
            self.phase.value,
            self.source,
        )


# --- Conservation -------------------------------------------------------------------------------
@dataclass(frozen=True)
class ConservationResult:
    """The outcome of ONE conservation check, with the numbers that produced it.

    Carries ``expected``/``actual``/``delta`` even when it holds, because a check that reports only
    a boolean cannot be audited and the first question about a violation is always "by how much".
    """

    holds: bool
    expected: float | int | None
    actual: float | int | None
    delta: float | int | None
    #: Component names that participated in the sum. Proves openness: an invented key appears here
    #: with no code change.
    components: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "holds": self.holds,
            "expected": self.expected,
            "actual": self.actual,
            "delta": self.delta,
            "components": list(self.components),
            "reason": self.reason,
        }


def check_conservation(usage: Usage, *, tolerance: float = 0.0) -> ConservationResult:
    """THE conservation check: ``sum(every component except total) == total``.

    THIS FORM, AND NOT THE FOUR-TERM ONE, BECAUSE THE FOUR-TERM ONE WAS MEASURED TO FAIL.
    ``input + output + cache == total`` held for 174 of 176 attempts in this repository's own run
    corpus and FAILED for the 2 carrying a ``reasoning`` key, with the shortfall equal to
    ``reasoning`` exactly (deltas 2658 and 1120). This all-components form held 176 of 176. See
    :func:`check_conservation_four_term`, which exists precisely so a test can demonstrate the
    difference rather than assert it.

    OPEN BY CONSTRUCTION: the summands are ``usage.component_names``, i.e. whatever the provider
    reported minus the reserved total, so a component key nobody has seen participates AUTOMATICALLY
    and needs no code change. That is the property that keeps this check from turning into the
    four-term form again the next time a provider adds a field.

    ``tolerance`` defaults to ``0.0`` DELIBERATELY. A tolerant conservation check detects no double
    counting, which is the single thing this check exists to make detectable, so a nonzero tolerance
    is a caller's explicit choice for float-valued components and never a default.
    """

    names = usage.component_names
    total = usage.total
    if not total.is_present:
        return ConservationResult(
            holds=True,
            expected=None,
            actual=None,
            delta=None,
            components=names,
            reason="no-total-reported",
        )

    absent = [n for n in names if not usage.components[n].is_present]
    if absent:
        # A partially observed component set cannot be reconciled: the shortfall would be
        # indistinguishable from the components we could not read. Report it as unreconcilable
        # rather than as a violation, because calling it a violation would train a reader to ignore
        # violations.
        return ConservationResult(
            holds=True,
            expected=None,
            actual=total.as_number(),
            delta=None,
            components=names,
            reason="components-incomplete",
        )
    if not names:
        return ConservationResult(
            holds=True,
            expected=None,
            actual=total.as_number(),
            delta=None,
            components=names,
            reason="no-components-reported",
        )

    expected = sum(usage.components[n].as_number() for n in names)
    actual = total.as_number()
    delta = actual - expected
    holds = abs(delta) <= tolerance
    return ConservationResult(
        holds=holds,
        expected=expected,
        actual=actual,
        delta=delta,
        components=names,
        reason="all-components-sum" if holds else "conservation-violation",
    )


#: The four component names the authoring plan believed conservation ran over. Present ONLY so the
#: measured falsification is reproducible in a test; NOT the implementation.
_FOUR_TERM_COMPONENTS: tuple[str, ...] = ("input", "output", "cache")


def check_conservation_four_term(usage: Usage) -> ConservationResult:
    """The REJECTED four-term form, kept so its failure is demonstrable rather than asserted.

    ``input + output + cache == total``. This is NOT the schema's check and no production code path
    calls it: it exists so a test can paste both forms side by side over the same attempt and show
    that this one fires a FALSE violation on an attempt carrying ``reasoning`` while
    :func:`check_conservation` does not. Keeping the falsified form executable is what stops a future
    reader from "simplifying" the open form back into it.
    """

    total = usage.total
    if not total.is_present:
        return ConservationResult(
            True, None, None, None, _FOUR_TERM_COMPONENTS, "no-total-reported"
        )
    present = [
        usage.components[n].as_number()
        for n in _FOUR_TERM_COMPONENTS
        if n in usage.components and usage.components[n].is_present
    ]
    expected = sum(present) if present else 0
    actual = total.as_number()
    delta = actual - expected
    return ConservationResult(
        holds=delta == 0,
        expected=expected,
        actual=actual,
        delta=delta,
        components=_FOUR_TERM_COMPONENTS,
        reason="four-term-sum" if delta == 0 else "conservation-violation",
    )


# --- Quality ------------------------------------------------------------------------------------
@dataclass(frozen=True)
class QualitySummary:
    """What was missing, unavailable or not-applicable in ONE run, and what damage stayed local.

    THREE SEPARATE COUNTS, NOT ONE "incomplete" FLAG. Collapsing them would destroy the same
    distinction :class:`Value` exists to preserve: an older driver that never wrote a field
    (``unavailable``) is a compatibility fact, while a field the current driver should have written
    and did not (``missing``) is a defect. A reader that cannot tell them apart cannot act on
    either.
    """

    run_id: str = ""
    missing_fields: tuple[str, ...] = ()
    unavailable_fields: tuple[str, ...] = ()
    not_applicable_fields: tuple[str, ...] = ()
    #: Count of source lines that failed to parse and were SKIPPED (never fatal, never other runs').
    parse_error_count: int = 0
    #: Short label codes, never formatted messages: a formatted message is where a path rides in.
    warnings: tuple[str, ...] = ()
    #: False when any analytics-relevant artifact was absent or the run is not terminal.
    is_complete: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "missing_fields": list(self.missing_fields),
            "unavailable_fields": list(self.unavailable_fields),
            "not_applicable_fields": list(self.not_applicable_fields),
            "parse_error_count": self.parse_error_count,
            "warnings": list(self.warnings),
            "is_complete": self.is_complete,
        }


def summarize_quality(
    run_id: str,
    facts: Iterable[Fact],
    *,
    parse_error_count: int = 0,
    warnings: Iterable[str] = (),
    is_complete: bool = True,
) -> QualitySummary:
    """Roll the four-state provenance of every fact up into one per-run quality summary.

    The field names it reports are ``<what>`` tokens (e.g. ``tokens.input``, ``cost``,
    ``wall_seconds``) rather than paths, so the summary itself is projectable.
    """

    miss: set[str] = set()
    unav: set[str] = set()
    na: set[str] = set()
    extra_warnings: set[str] = set()
    buckets = {
        Provenance.MISSING: miss,
        Provenance.UNAVAILABLE: unav,
        Provenance.NOT_APPLICABLE: na,
    }

    for fact in facts:
        if fact.usage.dropped_component_count:
            # A fixed CODE, never the refused name: the name is exactly what must not be persisted.
            extra_warnings.add("unsafe-component-name-dropped")
        for name, value in fact.usage.components.items():
            if value.is_absent:
                buckets[value.provenance].add(f"tokens.{name}")
        if fact.usage.cost.is_absent:
            buckets[fact.usage.cost.provenance].add("cost")
        for label, value in (
            ("wall_seconds", fact.time.wall_seconds),
            ("observed_activity_seconds", fact.time.observed_activity_seconds),
            ("overlap_seconds", fact.time.overlap_seconds),
            ("unattributed_seconds", fact.time.unattributed_seconds),
        ):
            if value.is_absent:
                buckets[value.provenance].add(label)

    return QualitySummary(
        run_id=run_id,
        missing_fields=tuple(sorted(miss)),
        unavailable_fields=tuple(sorted(unav)),
        not_applicable_fields=tuple(sorted(na)),
        parse_error_count=parse_error_count,
        warnings=tuple(sorted(set(warnings) | extra_warnings)),
        is_complete=is_complete,
    )


def deduplicate(facts: Iterable[Fact]) -> tuple[list[Fact], list[str]]:
    """Drop facts sharing an :attr:`Fact.identity`, reporting what was dropped.

    WHY THIS IS NEEDED AT ALL: a resumed run writes into the SAME directory, so the same attempt can
    be observed twice (once from ``state.json``, once from a session log), and a naive concatenation
    would double every number in it. The identity key includes ``attempt`` and ``phase``, so a
    genuine SECOND attempt and a verify measurement of the first are both kept; only a true
    re-observation of the same (grain, run, ipd, position, attempt, phase, source) is dropped.

    Returns ``(kept, dropped_labels)``; the labels are short codes for the quality summary.
    """

    seen: set[tuple[Any, ...]] = set()
    kept: list[Fact] = []
    dropped: list[str] = []
    for fact in facts:
        key = fact.identity
        if key in seen:
            dropped.append(f"duplicate-{fact.grain.value}")
            continue
        seen.add(key)
        kept.append(fact)
    return kept, dropped


def merge_usage(parts: Iterable[Usage]) -> Usage:
    """Sum several :class:`Usage` records component-wise, preserving unknown keys and absence.

    An absent component in one part does NOT zero the others: components present anywhere are
    summed over the parts that have them, and a component absent EVERYWHERE stays absent with the
    absence reason preserved. The result's provenance is ``derived`` because it is a sum this
    toolkit performed, which is precisely the labeling the module docstring demands.
    """

    numeric: dict[str, float | int] = {}
    absent: dict[str, Value] = {}
    cost_total: float | None = None
    cost_absent: Value | None = None
    currency = "USD"
    dropped = 0

    for part in parts:
        currency = part.cost_currency or currency
        dropped += part.dropped_component_count
        for name, value in part.components.items():
            if value.is_present:
                numeric[name] = numeric.get(name, 0) + value.as_number()
            elif name not in numeric:
                absent.setdefault(name, value)
        if part.cost.is_present:
            cost_total = (cost_total or 0.0) + float(part.cost.as_number())
        elif cost_absent is None:
            cost_absent = part.cost

    components: dict[str, Value] = {
        n: derived(v, "summed") for n, v in sorted(numeric.items())
    }
    for name, value in absent.items():
        components.setdefault(name, value)

    if cost_total is not None:
        cost = derived(round(cost_total, 6), "summed")
    else:
        cost = cost_absent or missing("no-cost-recorded")
    return Usage(
        components=components,
        cost=cost,
        cost_currency=currency,
        dropped_component_count=dropped,
    )


def usage_from_mapping(
    raw: Mapping[str, Any] | None,
    *,
    provenance: Provenance = Provenance.RECORDED,
    cost: Value | None = None,
    absent_reason: Value | None = None,
) -> Usage:
    """Build a :class:`Usage` from a raw provider token mapping, keeping EVERY key it carries.

    This is the single conversion point from a runner's ``attempt["tokens"]`` dict into the schema,
    and it is deliberately dumb about names: whatever keys are present become components, so
    ``reasoning`` (measured, unanticipated by the authoring plan) and any future component survive.
    A nested ``cache: {read, write}`` shape is FLATTENED by summing, matching what
    ``run_viewer.extract_log_metrics`` already does, so the two agree on the same input.
    """

    if not raw:
        return Usage(
            components={},
            cost=cost or absent_reason or missing("no-usage-recorded"),
        )

    components: dict[str, Value] = {}
    unsafe = 0
    for name, value in raw.items():
        label = str(name)
        if not _COMPONENT_NAME_RE.match(label):
            # A provider-chosen NAME that is not a safe component label is DROPPED rather than
            # raising, and the drop is counted under a fixed label. Raising here would be wrong in
            # both directions: it would abort a whole run's ingestion over one hostile or malformed
            # key (the containment rule says one bad artifact degrades its own run and no other),
            # and the resulting exception message would itself carry the offending string, which is
            # exactly the path or free text the check just refused. The COUNT is recorded so the
            # drop is visible in the quality summary rather than silent.
            unsafe += 1
            continue
        if isinstance(value, Mapping):
            sub = [v for v in value.values() if isinstance(v, (int, float))]
            if not sub:
                components[label] = missing("unparseable-component")
                continue
            components[label] = Value(sum(sub), provenance, "flattened")
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            components[label] = missing("unparseable-component")
            continue
        components[label] = Value(value, provenance)

    return Usage(
        components=components,
        cost=cost or absent_reason or missing("no-cost-recorded"),
        # Recorded as its OWN field and deliberately NOT as a component. A count smuggled in as a
        # component would enter the conservation sum and turn a defensive drop into a false
        # conservation violation, i.e. the check would start reporting on itself.
        dropped_component_count=unsafe,
    )

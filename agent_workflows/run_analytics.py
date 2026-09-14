#!/usr/bin/env python3
"""Normalized run INGESTION: turn heterogeneous run artifacts into one auditable fact table.

WHERE THIS SITS. :mod:`agent_workflows.run_analytics_sources` reads artifacts and says what each
driver generation provides; :mod:`agent_workflows.run_analytics_schema` defines the fact contract,
the four-state provenance, the open token component map and the conservation check; THIS module
composes the two into per-run/per-IPD/per-attempt/per-phase facts, enforces conservation and
deduplication, summarizes quality, and hands the result to Order 02's cache.

THERE IS EXACTLY ONE PRIVACY BOUNDARY AND IT IS NOT HERE.
:func:`agent_workflows.run_analytics_privacy.project_facts` is the single allowlist every persisted
fact crosses, and :func:`agent_workflows.run_analytics_cache.build_entry` is the only constructor
that reaches an envelope. This module therefore writes NO sanitizer, NO second allowlist and NO
second projector: :func:`project_run_facts` routes every grain through the shipped projector, so a
key the allowlist does not name is REFUSED here rather than silently persisted. Two allowlists drift
and the weaker one becomes the effective boundary, which is exactly the property Order 02 exists to
prevent.

THE PRIVACY RISK IN THE SOURCE DATA IS MEASURED, NOT THEORETICAL. Every ``state.json`` in this
repository's own corpus carries an ABSOLUTE ``repo`` path, and scanning that ONE field with the
shipped detector returns ``home-path`` and ``handle``, both at ``fail`` severity. The corpus also
holds hundreds of prompt and session transcripts, roughly 238 MB of model conversation. So the first
field an ingester reads is already a forbidden value, and the defenses are specific:
:func:`build_run_facts` never copies ``repo``, ``driver.path``, ``manifest``, ``runbook``, a prompt
path or a session path into a fact; the driver generation reaches a fact as the BASENAME-derived
label (``oc_runipd``), never the path it came from; and no fact field holds a filename, only an
artifact FAMILY label.

WHAT IS PERSISTED VERSUS WHAT IS RETURNED, stated because it is a real limitation rather than an
oversight. Order 02's envelope has ONE ``metric_facts`` object plus an ``event_facts`` list whose
allowlist carries no identity keys (no ``ipd_id6``, no ``position``, no ``attempt``), so the finer
grains cannot be persisted through it today without widening a sibling Order's shipped contract that
this module does not own. :func:`build_run_facts` therefore returns the COMPLETE typed table to its
caller and :func:`build_cache_facts` persists the run grain plus per-event shape facts, with every
grain still validated by the projector. When the envelope gains a fact-table member, the finer grains
pass through unchanged and no fact shape changes.

CONSERVATION IS CHECKED, NOT ASSUMED, AND IT IS NEVER LOOSENED. See
:func:`agent_workflows.run_analytics_schema.check_conservation` for the measurement that chose the
all-components form over the four-term one. When it fires here, :func:`build_run_facts` records a
``conservation-violation`` quality flag and KEEPS the raw components: the honest response to a
violation is to surface the numbers, never to widen a tolerance until the check passes.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from agent_workflows import run_analytics_privacy as privacy
from agent_workflows import run_analytics_schema as schema
from agent_workflows import run_analytics_sources as sources
from agent_workflows.run_analytics_schema import (
    Fact,
    Grain,
    Phase,
    Provenance,
    QualitySummary,
    Usage,
    Value,
    measured,
    missing,
    not_applicable,
    recorded,
)

__all__ = [
    "INGEST_SCHEMA_VERSION",
    "RunFacts",
    "build_run_facts",
    "build_cache_facts",
    "project_run_facts",
    "ingest_corpus",
    "conservation_survey",
    "update_analytics_cache",
]


#: The ingestion layer's own version, bumped when the :class:`RunFacts` SHAPE changes.
INGEST_SCHEMA_VERSION = 1

#: Queue-item statuses that mean the item finished successfully. Used only to label an outcome, never
#: to decide whether a fact exists.
_TERMINAL_OK = frozenset({"executed", "reviewed", "auto-approved"})


@dataclass(frozen=True)
class RunFacts:
    """Every fact one run yields, plus its quality summary and conservation results.

    ``facts`` spans grains (run, ipd, attempt, phase, event) and is already DEDUPLICATED, so a
    resumed or multi-attempt run appears once per genuine observation rather than once per source
    that mentioned it.
    """

    run_id: str
    inventory: sources.RunInventory
    facts: tuple[Fact, ...]
    quality: QualitySummary
    #: One result per attempt-grain fact carrying a provider total. A violation is REPORTED, not
    #: repaired, and never silences the check.
    conservation: tuple[schema.ConservationResult, ...] = ()

    def by_grain(self, grain: Grain) -> tuple[Fact, ...]:
        return tuple(f for f in self.facts if f.grain is grain)

    @property
    def conservation_holds(self) -> bool:
        return all(r.holds for r in self.conservation)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": INGEST_SCHEMA_VERSION,
            "run_id": self.run_id,
            "inventory": self.inventory.to_dict(),
            "facts": [f.to_dict() for f in self.facts],
            "quality": self.quality.to_dict(),
            "conservation": [r.to_dict() for r in self.conservation],
        }


# --- Small readers ------------------------------------------------------------------------------
def _iso(value: Any) -> str:
    """A timestamp string, or ``""``. Shape-checked, because the projector requires ISO-8601."""

    text = str(value or "").strip()
    if not text:
        return ""
    return text if privacy._TIMESTAMP_RE.match(text) else ""


def _epoch(value: Any) -> float | None:
    """Parse an ISO timestamp to epoch seconds, or ``None``. Never raises."""

    import datetime as _dt

    text = str(value or "").strip()
    if not text:
        return None
    try:
        cleaned = text.replace("Z", "+00:00")
        parsed = _dt.datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=_dt.timezone.utc)
        return parsed.timestamp()
    except (ValueError, TypeError):
        return None


def _label(value: Any, *, default: str = "") -> str:
    """A short closed-vocabulary label, or ``default``.

    Anything path-shaped or free-text is DROPPED rather than truncated, because a truncated path is
    still a path fragment and this is the function standing between a raw state field and a fact.
    """

    text = str(value or "").strip()
    if not text:
        return default
    if privacy._looks_like_path(text) or not privacy._LABEL_RE.match(text):
        return default
    return text


def _model_of(state: Mapping[str, Any]) -> str:
    options = state.get("options")
    if not isinstance(options, Mapping):
        return ""
    return _label(options.get("model"))


def _phase_of(item: Mapping[str, Any]) -> Phase:
    """The phase an item's own action implies. ``review`` items are not execution measurements."""

    action = str(item.get("action") or "execute").strip().lower()
    if action == "review":
        return Phase.REVIEW
    return Phase.EXECUTE


# --- Fact construction --------------------------------------------------------------------------
def _usage_for_phase(
    raw_cost: float | None,
    raw_tokens: Mapping[str, Any] | None,
    *,
    applicable: bool,
    absent_note: str,
) -> Usage:
    """Build a :class:`Usage` for one phase, distinguishing THREE kinds of absence.

    This is where the four-state provenance earns its keep. A verify phase that never ran is
    ``not-applicable``; a phase whose driver generation could not record usage is ``unavailable``; a
    phase that should have usage and does not is ``missing``. All three are absent and NONE is zero,
    so an aggregation over them cannot quietly report a free run.
    """

    if not applicable:
        return Usage(components={}, cost=not_applicable(absent_note))
    cost_value: Value
    if raw_cost is None:
        cost_value = missing(absent_note)
    else:
        cost_value = recorded(raw_cost)
    return schema.usage_from_mapping(
        raw_tokens, provenance=Provenance.RECORDED, cost=cost_value
    )


def _attempt_intervals(
    attempts: Sequence[Mapping[str, Any]],
) -> list[tuple[float, float]]:
    """``(start, end)`` epoch pairs for every attempt that has both. Unclosed attempts are omitted.

    Omitted rather than end-stamped with "now": inventing an end time would fabricate a duration,
    and the resulting number would be indistinguishable from a measured one.
    """

    spans: list[tuple[float, float]] = []
    for attempt in attempts:
        start = _epoch(attempt.get("started_at"))
        end = _epoch(attempt.get("ended_at"))
        if start is not None and end is not None and end >= start:
            spans.append((start, end))
    return spans


def build_run_facts(run_dir: Path | str) -> RunFacts:
    """Normalize ONE run directory into its complete fact table.

    NEVER RAISES FOR A DAMAGED RUN. An unreadable ``state.json`` yields a RunFacts with no facts, an
    ``is_complete=False`` quality summary and a ``state-unreadable`` warning; a corrupt event line is
    skipped and counted. That containment is the requirement: one damaged member of a corpus must
    degrade ITSELF and never abort the sweep or contaminate another run's numbers.
    """

    base = Path(run_dir)
    inventory = sources.inventory_run(base)
    if not inventory.readable:
        return RunFacts(
            run_id=inventory.run_id,
            inventory=inventory,
            facts=(),
            quality=QualitySummary(
                run_id=inventory.run_id,
                warnings=("state-unreadable",),
                is_complete=False,
            ),
        )

    state = sources.read_state(base).payload
    run_id = str(state.get("run_id") or base.name)
    generation = inventory.generation
    host = inventory.host
    model = _model_of(state)
    warnings: list[str] = list(inventory.warnings)

    facts: list[Fact] = []
    conservation: list[schema.ConservationResult] = []
    per_item_usage: list[Usage] = []
    all_spans: list[tuple[float, float]] = []

    queue = state.get("queue")
    queue_items = [i for i in (queue or []) if isinstance(i, Mapping)]

    for item in queue_items:
        id6 = _label(item.get("id6"))
        set_id = _label(item.get("setid"))
        position = item.get("position")
        position = position if isinstance(position, int) else None
        item_phase = _phase_of(item)
        status = str(item.get("status") or "").strip().lower()
        outcome = _label(status, default="unknown")
        attempts = [a for a in (item.get("attempts") or []) if isinstance(a, Mapping)]

        # ONE delegated precedence call per item; see run_analytics_sources.attempt_phase_usage.
        phase_usage = sources.attempt_phase_usage(item, base)
        exec_cost, exec_tokens = phase_usage["execute"]
        verify_cost, verify_tokens = phase_usage["verify"]

        # A verify measurement is NOT-APPLICABLE when no attempt carried a verify artifact at all,
        # and MISSING when one did but produced no number. The difference is visible only here,
        # which is why it is computed from the attempts rather than from the absent value.
        verify_attempted = any(
            ("verify_log" in a) or ("verify_cost" in a) or ("verify_tokens" in a)
            for a in attempts
        )

        exec_usage = _usage_for_phase(
            exec_cost,
            exec_tokens,
            applicable=bool(attempts),
            absent_note="no-attempt-usage" if attempts else "no-attempts",
        )
        verify_usage = _usage_for_phase(
            verify_cost,
            verify_tokens,
            applicable=verify_attempted,
            absent_note="no-verify-phase",
        )

        spans = _attempt_intervals(attempts)
        all_spans.extend(spans)

        for index, attempt in enumerate(attempts, 1):
            number = attempt.get("number")
            attempt_no = number if isinstance(number, int) else index
            is_recovery = bool(attempt.get("recovery"))
            attempt_phase = Phase.RECOVERY if is_recovery else item_phase
            att_tokens = (
                attempt.get("tokens")
                if isinstance(attempt.get("tokens"), Mapping)
                else None
            )
            raw_att_cost = attempt.get("cost")
            att_cost = (
                float(raw_att_cost)
                if isinstance(raw_att_cost, (int, float))
                and not isinstance(raw_att_cost, bool)
                else None
            )
            att_usage = _usage_for_phase(
                att_cost,
                att_tokens,
                applicable=True,
                absent_note="no-attempt-usage",
            )

            start = _epoch(attempt.get("started_at"))
            end = _epoch(attempt.get("ended_at"))
            if start is not None and end is not None and end >= start:
                att_time = schema.TimeAccounting(
                    wall_seconds=measured(end - start, "elapsed"),
                    observed_activity_seconds=measured(end - start, "single-interval"),
                    overlap_seconds=measured(0.0, "single-interval"),
                    unattributed_seconds=measured(0.0, "single-interval"),
                )
            else:
                reason = "attempt-not-closed" if start is not None else "no-interval"
                att_time = schema.TimeAccounting(
                    wall_seconds=missing(reason),
                    observed_activity_seconds=missing(reason),
                    overlap_seconds=missing(reason),
                    unattributed_seconds=missing(reason),
                )

            result = schema.check_conservation(att_usage)
            conservation.append(result)
            flags: list[str] = []
            if not result.holds:
                flags.append("conservation-violation")
            if is_recovery:
                flags.append("recovery-attempt")

            facts.append(
                Fact(
                    grain=Grain.ATTEMPT,
                    run_id=run_id,
                    set_id=set_id,
                    ipd_id6=id6,
                    position=position,
                    attempt=attempt_no,
                    phase=attempt_phase,
                    source="state",
                    driver_generation=generation,
                    host=host,
                    model=model,
                    outcome=outcome,
                    usage=att_usage,
                    time=att_time,
                    started_at=_iso(attempt.get("started_at")),
                    ended_at=_iso(attempt.get("ended_at")),
                    quality_flags=tuple(flags),
                )
            )

        # PHASE grain: execute and verify kept separate, which existing run summaries already do and
        # the fact schema must retain rather than merging into one number.
        for phase, usage in (
            (Phase.EXECUTE if item_phase is Phase.EXECUTE else item_phase, exec_usage),
            (Phase.VERIFY, verify_usage),
        ):
            facts.append(
                Fact(
                    grain=Grain.PHASE,
                    run_id=run_id,
                    set_id=set_id,
                    ipd_id6=id6,
                    position=position,
                    phase=phase,
                    source="state",
                    driver_generation=generation,
                    host=host,
                    model=model,
                    outcome=outcome,
                    usage=usage,
                )
            )

        item_usage = schema.merge_usage([exec_usage, verify_usage])
        per_item_usage.append(item_usage)
        item_time = schema.account_intervals(
            spans,
            wall_start=min(s for s, _ in spans) if spans else None,
            wall_end=max(e for _, e in spans) if spans else None,
        )
        facts.append(
            Fact(
                grain=Grain.IPD,
                run_id=run_id,
                set_id=set_id,
                ipd_id6=id6,
                position=position,
                phase=item_phase,
                source="state",
                driver_generation=generation,
                host=host,
                model=model,
                outcome=outcome,
                usage=item_usage,
                time=item_time,
                quality_flags=("ok",) if status in _TERMINAL_OK else (),
            )
        )

    # EVENT grain: SHAPE ONLY, never payload content. The event allowlist deliberately carries
    # payload_byte_count/payload_field_count and no payload, so a fact records that an event was N
    # bytes with M fields and never what those fields said.
    parse_errors = 0
    event_count = 0
    events_path = base / sources.ARTIFACT_NAMES["events"]
    for lineno, parsed in sources.iter_event_lines(events_path):
        if parsed is None:
            parse_errors += 1
            continue
        event_count += 1
        facts.append(
            Fact(
                grain=Grain.EVENT,
                run_id=run_id,
                # The line ordinal is what makes each event a DISTINCT identity. Without it every
                # event in a run shares one identity and deduplication discards all but the first;
                # that was a measured defect here, caught by a two-valid-line fixture.
                sequence=lineno,
                phase=Phase.UNKNOWN,
                source="events",
                driver_generation=generation,
                host=host,
                outcome=_label(parsed.get("event"), default="unknown"),
                started_at=_iso(parsed.get("at")),
                usage=Usage(components={}, cost=not_applicable("event-has-no-cost")),
            )
        )
    if parse_errors:
        warnings.append("event-line-unparseable")

    _outcomes, outcome_warnings = sources.read_outcomes(base)
    warnings.extend(outcome_warnings)
    _telemetry, telemetry_warnings = sources.read_telemetry_events(base)
    warnings.extend(telemetry_warnings)

    # RUN grain. Wall time comes from created_at/updated_at when both are present; activity time is
    # the UNION of the attempt intervals, so overlap and unattributed time are visible rather than
    # smoothed. The three are never forced to reconcile.
    created = _epoch(state.get("created_at"))
    updated = _epoch(state.get("updated_at"))
    run_time = schema.account_intervals(all_spans, wall_start=created, wall_end=updated)
    run_usage = (
        schema.merge_usage(per_item_usage)
        if per_item_usage
        else Usage(components={}, cost=missing("no-queue-items"))
    )

    run_flags: list[str] = []
    if parse_errors:
        run_flags.append("partial-events")
    if not inventory.artifacts.get("telemetry"):
        run_flags.append("no-telemetry")
    if any(not r.holds for r in conservation):
        run_flags.append("conservation-violation")

    facts.append(
        Fact(
            grain=Grain.RUN,
            run_id=run_id,
            phase=Phase.UNKNOWN,
            source="state",
            driver_generation=generation,
            host=host,
            model=model,
            outcome="complete" if inventory.queue_length else "empty",
            usage=run_usage,
            time=run_time,
            started_at=_iso(state.get("created_at")),
            ended_at=_iso(state.get("updated_at")),
            quality_flags=tuple(run_flags),
        )
    )

    deduped, dropped = schema.deduplicate(facts)
    warnings.extend(dropped)

    quality = schema.summarize_quality(
        run_id,
        deduped,
        parse_error_count=parse_errors,
        warnings=warnings,
        is_complete=bool(
            inventory.artifacts.get("state") and inventory.artifacts.get("events")
        )
        and parse_errors == 0,
    )

    return RunFacts(
        run_id=run_id,
        inventory=inventory,
        facts=tuple(deduped),
        quality=quality,
        conservation=tuple(conservation),
    )


# --- The privacy boundary: consumed, never reimplemented ----------------------------------------
def _metric_payload(fact: Fact) -> dict[str, Any]:
    """One fact rendered into the allowlist's OWN vocabulary, ready for the projector.

    Only allowlisted key NAMES appear here, and every absent value is OMITTED rather than zero-filled,
    which is what keeps the persisted form from asserting a count nobody observed. Deliberately does
    NOT sanitize anything: the projector is the boundary, and a filter here would be a second one.
    """

    payload: dict[str, Any] = {
        "run_id": fact.run_id,
        "phase": fact.phase.value,
        "driver_generation": fact.driver_generation,
        "host_kind": fact.host,
        "status": fact.outcome or "unknown",
    }
    if fact.set_id:
        payload["set_id"] = fact.set_id
    if fact.ipd_id6:
        payload["ipd_id6"] = fact.ipd_id6
    if fact.position is not None:
        payload["position"] = fact.position
    if fact.attempt is not None:
        payload["attempt"] = fact.attempt
    if fact.model:
        payload["model"] = fact.model
    if fact.started_at:
        payload["started_at"] = fact.started_at
    if fact.ended_at:
        payload["ended_at"] = fact.ended_at

    components = fact.usage.component_numbers()
    if components:
        payload["tokens"] = components
    total = fact.usage.total
    if total.is_present:
        payload["token_total"] = total.as_number()
    if fact.usage.cost.is_present:
        payload["cost"] = fact.usage.cost.as_number()
        payload["cost_currency"] = fact.usage.cost_currency
        # ALWAYS False in this layer, and that is a deliberate reading of the field rather than a
        # stub. `cost_is_estimate` distinguishes money a PRICE TABLE estimated from money a provider
        # RECORDED; this layer only ever reads recorded costs, and Order 06 owns effective-dated
        # pricing. Deriving the flag from `Provenance.DERIVED` would be wrong twice over: a SUM of
        # recorded costs is still recorded money, so summing an item's execute and verify costs would
        # relabel real spend as an estimate and every aggregate above it would inherit the lie.
        payload["cost_is_estimate"] = False

    for key, value in (
        ("wall_seconds", fact.time.wall_seconds),
        ("observed_activity_seconds", fact.time.observed_activity_seconds),
        ("overlap_seconds", fact.time.overlap_seconds),
        ("unattributed_seconds", fact.time.unattributed_seconds),
    ):
        if value.is_present:
            payload[key] = value.as_number()

    if fact.quality_flags:
        payload["quality_flags"] = list(fact.quality_flags)
    return payload


def _event_payload(fact: Fact) -> dict[str, Any]:
    """One EVENT-grain fact in the narrower event allowlist's vocabulary: shape, never content."""

    payload: dict[str, Any] = {
        "event_type": fact.outcome or "unknown",
        "phase": fact.phase.value,
    }
    if fact.sequence is not None:
        payload["sequence"] = fact.sequence
    if fact.started_at:
        payload["timestamp"] = fact.started_at
    if fact.quality_flags:
        payload["quality_flags"] = list(fact.quality_flags)
    return payload


def project_run_facts(run_facts: RunFacts) -> dict[str, Any]:
    """Route EVERY grain through Order 02's projector and return the projected table.

    THIS IS THE ONLY PLACE FACTS BECOME PERSISTABLE, and it adds no filtering of its own: it calls
    ``privacy.project_metric_facts`` / ``privacy.project_event_facts`` and lets a refused key RAISE.
    Raising is the point. A projector that dropped an unknown key would let this module believe its
    fact was persisted whole, and the difference between "refused" and "dropped" is the difference
    between a boundary a test can prove and one it cannot.

    Raises :class:`agent_workflows.run_analytics_privacy.PrivacyRefusal` for a fact carrying a key or
    a value type the allowlist does not name.
    """

    projected: dict[str, list[dict[str, Any]]] = {}
    for fact in run_facts.facts:
        if fact.grain is Grain.EVENT:
            projected.setdefault("event", []).append(
                privacy.project_event_facts(_event_payload(fact))
            )
            continue
        projected.setdefault(fact.grain.value, []).append(
            privacy.project_metric_facts(_metric_payload(fact))
        )
    return projected


def build_cache_facts(
    run_dir: Path | str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str], list[str]]:
    """The ``build_facts`` callback ``run_analytics_cache.update_cache`` expects.

    Returns ``(metric_facts, event_facts, quality_flags, warnings)``. The RUN grain becomes
    ``metric_facts`` (one object, which is what the envelope holds) and the event grain becomes
    ``event_facts``; the finer grains are validated by the projector here and returned by
    :func:`build_run_facts` to callers, pending the envelope member that will carry them (see the
    module docstring).

    Every value in the returned mapping has already crossed the projector, so ``build_entry``
    projecting again is idempotent rather than a second boundary.
    """

    run_facts = build_run_facts(run_dir)
    projected = project_run_facts(run_facts)

    run_grain = projected.get("run") or []
    metric_facts = run_grain[0] if run_grain else {}
    event_facts = projected.get("event") or []

    quality_flags: list[str] = []
    if not run_facts.quality.is_complete:
        quality_flags.append("incomplete")
    if not run_facts.conservation_holds:
        quality_flags.append("conservation-violation")
    if run_facts.quality.missing_fields:
        quality_flags.append("has-missing-fields")
    if run_facts.quality.unavailable_fields:
        quality_flags.append("has-unavailable-fields")
    if run_facts.quality.not_applicable_fields:
        quality_flags.append("has-not-applicable-fields")

    return metric_facts, event_facts, quality_flags, list(run_facts.quality.warnings)


# --- Corpus-level entry points ------------------------------------------------------------------
def ingest_corpus(
    run_dirs: Iterable[Path | str],
) -> tuple[list[RunFacts], list[str]]:
    """Ingest many runs, isolating each failure to its own run.

    Returns ``(per_run_facts, warning_labels)``. A run whose ingestion raises contributes a warning
    and NO facts; the sweep continues. That is what makes a corpus analyzable in the presence of one
    bad member, and it is the same containment ``update_cache`` applies at the cache layer.
    """

    results: list[RunFacts] = []
    warnings: list[str] = []
    for run_dir in run_dirs:
        try:
            results.append(build_run_facts(run_dir))
        except Exception:  # noqa: BLE001 - one run's failure must never end the sweep
            warnings.append("run-ingest-failed")
    return results, warnings


def conservation_survey(
    run_dirs: Iterable[Path | str],
) -> dict[str, Any]:
    """Run BOTH conservation forms over every attempt and report the comparison.

    THIS FUNCTION EXISTS TO MAKE THE MEASUREMENT REPRODUCIBLE RATHER THAN CITED. The all-components
    form is the implementation; the four-term form is the REJECTED one, kept executable so its
    failure can be demonstrated on the same data instead of asserted from a review note. On this
    repository's corpus at review the four-term form held 174 of 176 and failed for exactly the 2
    attempts carrying ``reasoning`` (deltas 2658 and 1120), while the all-components form held
    176 of 176.

    Returns the two counts plus, for each four-term failure, the identity and the exact delta, which
    is what makes the comparison auditable rather than a pair of totals.
    """

    all_components_ok = 0
    all_components_fail: list[dict[str, Any]] = []
    four_term_ok = 0
    four_term_fail: list[dict[str, Any]] = []
    checked = 0

    for run_dir in run_dirs:
        try:
            run_facts = build_run_facts(run_dir)
        except Exception:  # noqa: BLE001 - a damaged run must not end the survey
            continue
        for fact in run_facts.by_grain(Grain.ATTEMPT):
            if not fact.usage.total.is_present:
                continue
            checked += 1
            identity = {
                "run_id": fact.run_id,
                "ipd_id6": fact.ipd_id6,
                "attempt": fact.attempt,
            }
            open_result = schema.check_conservation(fact.usage)
            if open_result.holds:
                all_components_ok += 1
            else:
                all_components_fail.append({**identity, "delta": open_result.delta})
            four = schema.check_conservation_four_term(fact.usage)
            if four.holds:
                four_term_ok += 1
            else:
                four_term_fail.append(
                    {
                        **identity,
                        "delta": four.delta,
                        "reasoning": fact.usage.components["reasoning"].or_default(0)
                        if "reasoning" in fact.usage.components
                        else None,
                    }
                )

    return {
        "attempts_checked": checked,
        "all_components": {
            "form": "sum(every component except total) == total",
            "held": all_components_ok,
            "failed": len(all_components_fail),
            "failures": all_components_fail,
        },
        "four_term": {
            "form": "input + output + cache == total (REJECTED)",
            "held": four_term_ok,
            "failed": len(four_term_fail),
            "failures": four_term_fail,
        },
    }


def update_analytics_cache(
    run_dirs: Iterable[Path | str],
    *,
    repo: Path | str | None = None,
) -> Any:
    """Populate Order 02's cache from these runs, using its own ``update_cache`` and its projector.

    A thin composition on purpose. Freshness, locking, atomic publication and per-run failure
    isolation are Order 02's and are NOT reimplemented here; this function's whole contribution is
    supplying :func:`build_cache_facts` as the fact producer.
    """

    from agent_workflows import run_analytics_cache as cache

    return cache.update_cache(run_dirs, build_facts=build_cache_facts, repo=repo)

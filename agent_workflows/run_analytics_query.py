"""Allowlisted, bounded query engine over the analytics cache and its companion artifacts.

runanalytics Order 08 (`mm5p3v`) E-05 / E-06. Stdlib only.

WHAT THIS MODULE IS FOR. `aw runs query <view>` is the interface an AGENT uses to get facts and
findings out of the analytics corpus without parsing the SPA's HTML. This module owns the view
vocabulary, the filter/group allowlist, and the bounded payload; `run_analytics_cli` owns the argparse
surface and the record emission.

FOUR CONSTRAINTS SHAPE EVERY DECISION HERE, and each is measured rather than assumed.

1. THE ALLOWLIST IS THE SECURITY BOUNDARY, NOT A CONVENIENCE. There is no SQL, no expression
   evaluator, no user-supplied attribute lookup, and no filesystem path taken from the caller. A
   filter names a field from :data:`FILTERABLE_FIELDS` and a grouping names one from
   :data:`GROUPABLE_FIELDS`; anything else is REFUSED with the allowlist named, and deliberately
   WITHOUT echoing the rejected token back into the payload (an error message that reflects input is
   how a log-injection reaches whoever reads the log).

2. A REFUSAL IS FORWARDED, NEVER RECOMPUTED. Order 06 (`aflsz3`) returns `cannot-determine` for the
   four required analyses named in `run_analytics_statistics.UNDER_POWERED_ANALYSES`, and Order 07
   (`6eq3oq`) renders those as refusal panels. This module forwards THAT verdict with THAT observed n
   (:func:`view_metrics`). A query interface that answered what the engine refused would be a second,
   weaker engine, and the number it produced would carry none of the power analysis that made the
   refusal correct.

3. THE AGENT RECORD BUDGET IS ENFORCED AND SMALL, so bounding is a CONFORMANCE requirement rather
   than an ergonomic nicety. `tests/test_cli_quality_gates.py` enforces 1200 bytes / 400 approximate
   tokens per record. A `distributions` or `slices` view over a corpus-scale fact table breaches that
   by construction, so every row-bearing view is bounded by :data:`DEFAULT_ROW_LIMIT` and reports
   `total`/`emitted`/`omitted` plus the exact `next` command that continues the page. Truncation is
   never silent: an omitted row is always counted, which is what lets a caller tell a short answer
   from a complete one.

4. NO SECOND PROTOCOL. `agent_schema.SCHEMA_VERSION` is already `aw.agent/v1` with a closed
   `RECORD_KINDS` and a closed 13-value `VALID_OUTCOMES`. A view returns a :class:`QueryResult` whose
   payload travels in the record's `data`; it does not mint a version, add an outcome, or raise the
   budget. `cannot-run` is the closest existing outcome for a refused slice and is what a refusal
   uses.

WHY A `QueryResult` RATHER THAN A `CommandResult`. This module stays free of the renderer layer so it
can be unit-tested without argparse or an output context, and so the CLI owns the single place where
an outcome becomes an exit code. The mapping is total and lives in :meth:`QueryResult.outcome`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from agent_workflows import run_analytics_cache as cache_mod
from agent_workflows import run_analytics_findings as findings_mod
from agent_workflows import run_analytics_pricing as pricing_mod
from agent_workflows import run_analytics_statistics as stats_mod
from agent_workflows import run_analytics_taxonomy as taxonomy_mod
from agent_workflows.runner_shared import analytics_root

__all__ = [
    "QUERY_SCHEMA_VERSION",
    "VIEWS",
    "VIEW_HELP",
    "FILTERABLE_FIELDS",
    "GROUPABLE_FIELDS",
    "AGGREGATE_METRICS",
    "AGGREGATE_STATS",
    "DEFAULT_ROW_LIMIT",
    "MAX_ROW_LIMIT",
    "QueryError",
    "QueryRefusal",
    "QueryResult",
    "run_query",
    "parse_filters",
    "parse_group_by",
]


#: Bumped only on an INCOMPATIBLE change to a view's payload shape. This is NOT a second agent
#: protocol version: the envelope is `aw.agent/v1` and this rides inside its `data`, so a consumer
#: reads one schema field for the envelope and one for the payload it wraps.
QUERY_SCHEMA_VERSION: int = 1


# --------------------------------------------------------------------------------------------------
# The view vocabulary
# --------------------------------------------------------------------------------------------------

#: Every view name, in help order. A FIXED tuple: configuration may never manufacture a view, for the
#: same reason it may never manufacture a command.
VIEWS: tuple[str, ...] = (
    "overview",
    "schema",
    "metrics",
    "distributions",
    "slices",
    "findings",
    "evidence",
    "data-quality",
    "cache-status",
    "explain",
)

VIEW_HELP: dict[str, str] = {
    "overview": "Corpus size, cache coverage, and what is computable versus refused.",
    "schema": "The queryable field, filter, grouping, metric and stat vocabularies.",
    "metrics": "One aggregated metric, or Order 06's REFUSAL for an under-powered analysis.",
    "distributions": "Distribution shape (median, p25/p75/p90, missingness) for one metric.",
    "slices": "Bounded per-group rows for a grouping, with counts and missingness.",
    "findings": "Ranked findings with their full evidence contract, refusals included.",
    "evidence": "The provenance of one finding or metric: sources, coverage, caveats.",
    "data-quality": "Missingness, conservation violations, and quality flags by run.",
    "cache-status": "Per-run cache verdicts and reason codes, plus totals.",
    "explain": "Provenance for a taxonomy rule (--taxonomy) or a price era (--price).",
}


# --------------------------------------------------------------------------------------------------
# The allowlists
# --------------------------------------------------------------------------------------------------

#: Fields a `--filter name=value` may name. Each is a closed-vocabulary label or an opaque id that
#: has already crossed Order 02's privacy projector; none is free text, a path, or a command line.
FILTERABLE_FIELDS: tuple[str, ...] = (
    "run_id",
    "set_id",
    "ipd_id6",
    "phase",
    "outcome",
    "activity",
    "driver_generation",
    "host_kind",
    "model",
    "provider",
    "price_era",
    "is_complete",
)

#: Fields a `--group-by` may name. A strict subset of the filterable set: grouping by an unbounded
#: identifier (`run_id`) would produce one group per run and defeat the row bound, so it is excluded
#: deliberately rather than by omission.
GROUPABLE_FIELDS: tuple[str, ...] = (
    "set_id",
    "phase",
    "outcome",
    "activity",
    "driver_generation",
    "host_kind",
    "model",
    "provider",
    "price_era",
)

#: Metrics an aggregation may name.
AGGREGATE_METRICS: tuple[str, ...] = (
    "cost",
    "tokens",
    "token_total",
    "duration_seconds",
    "wall_seconds",
    "observed_activity_seconds",
    "event_count",
)

#: Statistics an aggregation may request. `median` is the DEFAULT rather than `mean`, because the
#: measured attempt-cost distribution is heavily right-skewed (Order 06 measured a max of 54.50 USD
#: against a median of 11.79), and a mean over that reads as a typical value while being none.
AGGREGATE_STATS: tuple[str, ...] = (
    "median",
    "mean",
    "minimum",
    "maximum",
    "p25",
    "p75",
    "p90",
    "count",
    "sum",
)

#: Default rows per page. Small ON PURPOSE: the enforced agent-record budget is 1200 bytes, and a
#: page of 20 rows with counts already approaches it. A caller wanting more asks for more and gets a
#: `next` command that says how.
DEFAULT_ROW_LIMIT: int = 20

#: Hard ceiling on `--limit`. A caller asking for more is REFUSED rather than silently clamped: a
#: clamp would return a short answer that looks complete, which is the failure mode the
#: emitted/omitted counts exist to prevent.
MAX_ROW_LIMIT: int = 500


class QueryError(Exception):
    """A malformed or disallowed query. Maps to exit 2 (`cannot-run`)."""


class QueryRefusal(Exception):
    """A query the corpus cannot answer. Distinct from :class:`QueryError`, which is caller fault."""


# --------------------------------------------------------------------------------------------------
# Result
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class QueryResult:
    """One view's answer: a bounded payload, its counts, and its honesty fields.

    ``refused`` is its own field rather than an inference from an empty ``rows``, because "the engine
    declined to compute this" and "the corpus contains no matching row" are different facts and a
    consumer that cannot distinguish them will report one as the other.
    """

    view: str
    rows: tuple[Mapping[str, Any], ...] = ()
    total: int = 0
    emitted: int = 0
    omitted: int = 0
    payload: dict[str, Any] = field(default_factory=dict)
    #: Set for a forwarded Order 06 refusal. Carries that verdict and its observed n verbatim.
    refused: bool = False
    verdict: str = ""
    reason: str = ""
    sample_size: int | None = None
    caveats: tuple[str, ...] = ()
    #: The exact command that continues the page, or "" when the answer is complete.
    next_command: str = ""
    query_schema_version: int = QUERY_SCHEMA_VERSION

    @property
    def complete(self) -> bool:
        return self.omitted == 0

    @property
    def outcome(self) -> str:
        """The `aw.agent/v1` outcome for this result. Total, and only over the CLOSED existing set.

        A refusal is `cannot-run`: it is the closest shipped value, and adding one to
        `agent_schema.VALID_OUTCOMES` would change a cross-cutting contract every agent consumer
        reads. A bounded page is `partial`, which is exactly what an incomplete answer is.
        """

        if self.refused:
            return "cannot-run"
        if not self.complete:
            return "partial"
        return "clean"

    @property
    def exit_code(self) -> int:
        """0 complete, 0 bounded-but-honest, 2 refused. Never a code above 2.

        A bounded page is NOT a domain failure: the caller got a correct answer to a bounded
        question, and the counts say so. Reserving 1 for a genuine finding keeps `exit 1` meaningful.
        """

        return 2 if self.refused else 0

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "query_schema_version": self.query_schema_version,
            "view": self.view,
            "total": self.total,
            "emitted": self.emitted,
            "omitted": self.omitted,
            "complete": self.complete,
        }
        if self.rows:
            out["rows"] = [dict(r) for r in self.rows]
        if self.payload:
            out["payload"] = dict(self.payload)
        if self.refused:
            out["refused"] = True
            out["verdict"] = self.verdict
            out["reason"] = self.reason
            if self.sample_size is not None:
                out["sample_size"] = self.sample_size
        if self.caveats:
            out["caveats"] = list(self.caveats)
        return out


# --------------------------------------------------------------------------------------------------
# Parsing (the allowlist gate)
# --------------------------------------------------------------------------------------------------


def _refuse_field(kind: str, allowed: Sequence[str]) -> QueryError:
    """Build the refusal for a disallowed field, NAMING THE ALLOWLIST and not the input.

    Deliberately does not interpolate the caller's token. The allowlist is the actionable half of the
    message, and reflecting arbitrary input into an error that is printed, logged and possibly parsed
    is a needless injection surface for zero diagnostic gain.
    """

    return QueryError(
        f"unknown {kind}; allowed {kind}s are: {', '.join(sorted(allowed))}"
    )


def parse_filters(raw: Iterable[str] | None) -> dict[str, str]:
    """Parse `name=value` filters against :data:`FILTERABLE_FIELDS`.

    Refuses an unknown field, a missing `=`, and an empty name. A repeated field is refused too,
    rather than last-wins: silently discarding one of two contradictory filters answers a question
    the caller did not ask.
    """

    parsed: dict[str, str] = {}
    for entry in raw or ():
        text = str(entry)
        if "=" not in text:
            raise QueryError(
                "a filter must be written name=value; "
                f"allowed names are: {', '.join(sorted(FILTERABLE_FIELDS))}"
            )
        name, _, value = text.partition("=")
        name = name.strip()
        if not name:
            raise QueryError(
                "a filter must be written name=value with a non-empty name"
            )
        if name not in FILTERABLE_FIELDS:
            raise _refuse_field("filter field", FILTERABLE_FIELDS)
        if name in parsed:
            raise QueryError(
                f"filter field {name!r} was given twice; combine the values into one filter "
                "rather than relying on which one wins"
            )
        parsed[name] = value.strip()
    return parsed


def parse_group_by(raw: str | Sequence[str] | None) -> tuple[str, ...]:
    """Parse a comma-separated or repeated `--group-by` against :data:`GROUPABLE_FIELDS`."""

    if raw is None:
        return ()
    tokens: list[str] = []
    items = [raw] if isinstance(raw, str) else list(raw)
    for item in items:
        tokens.extend(part.strip() for part in str(item).split(","))
    fields: list[str] = []
    for token in tokens:
        if not token:
            continue
        if token not in GROUPABLE_FIELDS:
            raise _refuse_field("grouping field", GROUPABLE_FIELDS)
        if token not in fields:
            fields.append(token)
    return tuple(fields)


def _parse_limit(limit: Any) -> int:
    if limit is None:
        return DEFAULT_ROW_LIMIT
    try:
        value = int(limit)
    except (TypeError, ValueError):
        raise QueryError("--limit must be an integer")
    if value <= 0:
        raise QueryError("--limit must be greater than zero")
    if value > MAX_ROW_LIMIT:
        raise QueryError(
            f"--limit {value} exceeds the maximum {MAX_ROW_LIMIT}; page through the result "
            "instead, so each record stays inside the enforced agent-record budget"
        )
    return value


def _validate_metric(metric: str | None) -> str:
    name = (metric or "cost").strip()
    if name not in AGGREGATE_METRICS:
        raise _refuse_field("metric", AGGREGATE_METRICS)
    return name


def _validate_stat(stat: str | None) -> str:
    name = (stat or "median").strip()
    if name not in AGGREGATE_STATS:
        raise _refuse_field("stat", AGGREGATE_STATS)
    return name


# --------------------------------------------------------------------------------------------------
# Corpus access (through Order 01's resolver ONLY)
# --------------------------------------------------------------------------------------------------


def _cache_entries(repo: Path | str | None) -> list[dict[str, Any]]:
    """Every readable cache envelope, as plain dicts.

    Paths come from Order 02's :func:`run_analytics_cache.cache_root`, which is itself derived from
    Order 01's resolver. The `.aw/records/runs` literal is NEVER composed here; Order 01 exists to
    remove it from six sites and this would be the seventh.

    An unreadable entry is SKIPPED and counted by the caller rather than raising: one damaged member
    of a corpus must degrade itself and never abort the sweep, which is the same containment
    `run_analytics.build_run_facts` implements.
    """

    entries: list[dict[str, Any]] = []
    for path in _entry_paths(repo):
        try:
            entries.append(cache_mod.load_entry(path).to_dict())
        except (cache_mod.CacheError, OSError, ValueError):
            continue
    return entries


def _entry_paths(repo: Path | str | None) -> list[Path]:
    """Every published cache entry file, at whatever depth Order 02 writes it.

    MEASURED LAYOUT: entries land at ``<cache_root>/<root-id>/<run-id>/entry.json``, i.e. TWO levels
    below the cache root, because the root id partitions one machine's cache from another's. An
    earlier version of this helper scanned only ONE level and therefore found nothing at all, which is
    the quiet-empty-corpus failure the query surface exists to make impossible. A recursive search by
    FILENAME keeps this correct if that partitioning changes again.
    """

    root = cache_mod.cache_root(repo)
    if not root.is_dir():
        return []
    return sorted(root.rglob(cache_mod.ENTRY_FILENAME))


def _unreadable_entry_count(repo: Path | str | None) -> int:
    """How many published entries cannot be read. COUNTED, never silently dropped.

    A corrupt or version-mismatched entry shrinks the corpus, so a view that reported only the
    readable count would understate its own coverage without saying so.
    """

    bad = 0
    for path in _entry_paths(repo):
        try:
            cache_mod.load_entry(path)
        except (cache_mod.CacheError, OSError, ValueError):
            bad += 1
    return bad


def _facts_of(entry: Mapping[str, Any]) -> dict[str, Any]:
    facts = entry.get("metric_facts")
    return dict(facts) if isinstance(facts, Mapping) else {}


def _matches(entry: Mapping[str, Any], filters: Mapping[str, str]) -> bool:
    """Compare a cache entry against parsed filters by EXACT string equality on allowlisted fields.

    Exact, not substring: a substring match on `outcome` would make `error` match `no-error`, and a
    filter whose meaning depends on the corpus is not a filter a caller can reason about.
    """

    if not filters:
        return True
    facts = _facts_of(entry)
    for name, wanted in filters.items():
        actual = facts.get(name, entry.get(name))
        if actual is None:
            return False
        if isinstance(actual, bool):
            if str(actual).lower() != wanted.lower():
                return False
            continue
        if str(actual) != wanted:
            return False
    return True


def _numbers_for(
    entries: Sequence[Mapping[str, Any]], metric: str
) -> tuple[list[float], int]:
    """Present values for ``metric`` plus a MISSING count.

    Returns the two separately because an absent value is not zero: Order 05's four-state provenance
    exists for that distinction, and folding missingness into the sample would silently strengthen
    every statistic computed from it.
    """

    values: list[float] = []
    missing = 0
    for entry in entries:
        facts = _facts_of(entry)
        raw = facts.get(metric)
        if raw is None and metric == "tokens":
            raw = facts.get("token_total")
        if isinstance(raw, Mapping):
            total = raw.get("total")
            raw = total if isinstance(total, (int, float)) else None
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            missing += 1
            continue
        values.append(float(raw))
    return values, missing


def _group_key(entry: Mapping[str, Any], fields: Sequence[str]) -> tuple[str, ...]:
    facts = _facts_of(entry)
    key: list[str] = []
    for name in fields:
        value = facts.get(name, entry.get(name))
        key.append("(unresolved)" if value in (None, "") else str(value))
    return tuple(key)


def _bound(
    rows: Sequence[Mapping[str, Any]],
    *,
    view: str,
    limit: int,
    next_hint: str,
) -> tuple[tuple[Mapping[str, Any], ...], int, int, int, str]:
    """Page ``rows`` to ``limit`` and report the counts plus the continuation command."""

    total = len(rows)
    emitted = rows[:limit]
    omitted = total - len(emitted)
    next_command = ""
    if omitted:
        next_command = f"aw runs query {view} {next_hint}--limit {min(total, MAX_ROW_LIMIT)}".replace(
            "  ", " "
        )
    return tuple(dict(r) for r in emitted), total, len(emitted), omitted, next_command


# --------------------------------------------------------------------------------------------------
# Views
# --------------------------------------------------------------------------------------------------


def view_overview(
    entries: Sequence[Mapping[str, Any]], *, repo: Path | str | None
) -> QueryResult:
    """Corpus size, cache coverage, and the computable-versus-refused split."""

    complete = sum(1 for e in entries if e.get("is_complete"))
    flags: dict[str, int] = {}
    for entry in entries:
        for flag in entry.get("quality_flags") or ():
            flags[str(flag)] = flags.get(str(flag), 0) + 1
    refusals = stats_mod.refuse_under_powered_required_analyses()
    refused = sum(1 for r in refusals.values() if not r.renderable)
    return QueryResult(
        view="overview",
        total=len(entries),
        emitted=len(entries),
        payload={
            "cached_runs": len(entries),
            "complete_runs": complete,
            "incomplete_runs": len(entries) - complete,
            "unreadable_entries": _unreadable_entry_count(repo),
            "quality_flag_counts": dict(sorted(flags.items())),
            "required_analyses": len(refusals),
            "refused_analyses": refused,
            "cache_schema_version": cache_mod.CACHE_SCHEMA_VERSION,
            "analytics_root_exists": analytics_root(repo).is_dir(),
        },
        caveats=(
            "a refused analysis is a measured power judgement from Order 06, not a query error",
        ),
    )


def view_schema() -> QueryResult:
    """The queryable vocabularies. The one view that needs no corpus, so it never refuses."""

    return QueryResult(
        view="schema",
        total=len(VIEWS),
        emitted=len(VIEWS),
        payload={
            "views": list(VIEWS),
            "filter_fields": list(FILTERABLE_FIELDS),
            "group_by_fields": list(GROUPABLE_FIELDS),
            "metrics": list(AGGREGATE_METRICS),
            "stats": list(AGGREGATE_STATS),
            "default_limit": DEFAULT_ROW_LIMIT,
            "max_limit": MAX_ROW_LIMIT,
            "cache_schema_version": cache_mod.CACHE_SCHEMA_VERSION,
            "taxonomy_version": taxonomy_mod.TAXONOMY_VERSION,
            "pricing_schema_version": pricing_mod.PRICING_SCHEMA_VERSION,
            "statistics_version": stats_mod.STATISTICS_VERSION,
            "findings_schema_version": findings_mod.FINDINGS_SCHEMA_VERSION,
        },
    )


def view_metrics(
    entries: Sequence[Mapping[str, Any]],
    *,
    metric: str,
    stat: str,
    group_by: Sequence[str],
    analysis: str | None,
    limit: int,
) -> QueryResult:
    """One aggregated metric, or Order 06's refusal FORWARDED VERBATIM.

    THE REFUSAL BRANCH IS THE POINT OF THIS VIEW. When ``analysis`` names one of Order 06's
    under-powered required analyses, this returns that `cannot-determine` verdict with its observed n
    and its caveats, and computes nothing. Answering it here with a number would be a second, weaker
    engine, and the number would silently drop the power analysis that made the refusal correct.
    """

    if analysis:
        refusals = stats_mod.refuse_under_powered_required_analyses()
        result = refusals.get(analysis)
        if result is None:
            raise _refuse_field("analysis", tuple(sorted(refusals)))
        if not result.renderable:
            return QueryResult(
                view="metrics",
                refused=True,
                verdict=result.verdict.value,
                reason=result.reason,
                sample_size=result.sample_size,
                caveats=tuple(result.caveats),
                payload={"analysis": result.name, "metric": metric, "stat": stat},
            )
        return QueryResult(
            view="metrics",
            total=1,
            emitted=1,
            payload={
                "analysis": result.name,
                "verdict": result.verdict.value,
                "sample_size": result.sample_size,
                "values": dict(result.values),
                "reason": result.reason,
            },
            caveats=tuple(result.caveats),
        )

    if not group_by:
        values, missing = _numbers_for(entries, metric)
        dist = stats_mod.describe(f"{metric}", values)
        return QueryResult(
            view="metrics",
            total=1,
            emitted=1,
            payload={
                "metric": metric,
                "stat": stat,
                "value": _stat_of(dist, stat, values),
                "sample_size": dist.sample_size,
                "missing_count": missing,
                "coverage": round(
                    (dist.sample_size / (dist.sample_size + missing))
                    if (dist.sample_size + missing)
                    else 0.0,
                    6,
                ),
            },
            caveats=_coverage_caveats(group_by, dist.sample_size, missing),
        )

    buckets: dict[tuple[str, ...], list[Mapping[str, Any]]] = {}
    for entry in entries:
        buckets.setdefault(_group_key(entry, group_by), []).append(entry)
    rows: list[dict[str, Any]] = []
    for key, members in sorted(buckets.items()):
        values, missing = _numbers_for(members, metric)
        dist = stats_mod.describe(metric, values)
        row: dict[str, Any] = {name: key[i] for i, name in enumerate(group_by)}
        row["n"] = len(members)
        row["sample_size"] = dist.sample_size
        row["missing_count"] = missing
        row["value"] = _stat_of(dist, stat, values)
        rows.append(row)
    hint = f"--metric {metric} --stat {stat} --group-by {','.join(group_by)} "
    emitted, total, count, omitted, next_cmd = _bound(
        rows, view="metrics", limit=limit, next_hint=hint
    )
    resolved = sum(int(r["sample_size"]) for r in rows)
    missing_total = sum(int(r["missing_count"]) for r in rows)
    return QueryResult(
        view="metrics",
        rows=emitted,
        total=total,
        emitted=count,
        omitted=omitted,
        next_command=next_cmd,
        payload={"metric": metric, "stat": stat, "group_by": list(group_by)},
        caveats=_coverage_caveats(group_by, resolved, missing_total),
    )


def _coverage_caveats(
    group_by: Sequence[str], resolved: int, missing: int
) -> tuple[str, ...]:
    """Caveats a consumer MUST surface, including the measured `model` coverage trap.

    `model` is called out BY NAME because Order 06 measured model identity resolvable for 2 of 179
    attempts (1.1 percent). A `--group-by model` aggregation therefore renders an almost entirely
    `(unresolved)` table, and a caller who does not know that will read it as a real comparison.
    """

    caveats: list[str] = []
    total = resolved + missing
    if total and missing:
        caveats.append(
            f"{missing} of {total} observations had no value for this metric and were EXCLUDED, "
            "not counted as zero"
        )
    if "model" in group_by:
        coverage = stats_mod.CORPUS_BASELINE.get("model_identity_coverage")
        caveats.append(
            "model identity is near-absent in historical data (review-time snapshot "
            f"{coverage}, NOT current); most rows group under (unresolved) and this is an honest "
            "empty state rather than a model comparison"
        )
    if not total:
        caveats.append(
            "no observation carried this metric; there is nothing to aggregate"
        )
    return tuple(caveats)


def _stat_of(dist: Any, stat: str, values: Sequence[float]) -> Any:
    if stat == "count":
        return len(values)
    if stat == "sum":
        return sum(values) if values else None
    return getattr(dist, stat, None)


def view_distributions(
    entries: Sequence[Mapping[str, Any]], *, metric: str, limit: int
) -> QueryResult:
    """One metric's distribution shape. Bounded by construction: it emits statistics, not rows.

    THIS IS THE VIEW THE BUDGET WOULD OTHERWISE BREAK, and the fix is structural rather than a
    truncation: a distribution over any number of observations is a FIXED-SIZE summary (nine
    statistics plus a missing count), so the payload does not grow with the corpus at all. `--limit`
    still bounds the optional per-bucket histogram.
    """

    values, missing = _numbers_for(entries, metric)
    dist = stats_mod.describe(metric, values)
    payload = dict(dist.to_dict())
    payload["metric"] = metric
    payload["observations_considered"] = len(entries)
    return QueryResult(
        view="distributions",
        total=len(values) + missing,
        emitted=len(values),
        omitted=0,
        payload=payload,
        caveats=_coverage_caveats((), dist.sample_size, missing),
    )


def view_slices(
    entries: Sequence[Mapping[str, Any]],
    *,
    group_by: Sequence[str],
    metric: str,
    limit: int,
) -> QueryResult:
    """Bounded per-group rows with counts and missingness."""

    if not group_by:
        raise QueryError(
            "the slices view needs --group-by; allowed grouping fields are: "
            f"{', '.join(sorted(GROUPABLE_FIELDS))}"
        )
    buckets: dict[tuple[str, ...], list[Mapping[str, Any]]] = {}
    for entry in entries:
        buckets.setdefault(_group_key(entry, group_by), []).append(entry)
    rows: list[dict[str, Any]] = []
    for key, members in sorted(buckets.items()):
        values, missing = _numbers_for(members, metric)
        row: dict[str, Any] = {name: key[i] for i, name in enumerate(group_by)}
        row["n"] = len(members)
        row["with_metric"] = len(values)
        row["missing_count"] = missing
        row["complete_runs"] = sum(1 for m in members if m.get("is_complete"))
        rows.append(row)
    hint = f"--group-by {','.join(group_by)} --metric {metric} "
    emitted, total, count, omitted, next_cmd = _bound(
        rows, view="slices", limit=limit, next_hint=hint
    )
    return QueryResult(
        view="slices",
        rows=emitted,
        total=total,
        emitted=count,
        omitted=omitted,
        next_command=next_cmd,
        payload={"group_by": list(group_by), "metric": metric},
        caveats=_coverage_caveats(group_by, 0, 0),
    )


#: Fields a `findings` ROW carries by default. A DELIBERATE SUBSET, and the reason is measured: one
#: finding's full evidence contract serializes to 1199 to 1205 bytes on the real refusals, which
#: breaches (or sits on) the enforced 1200-byte agent-record budget for a SINGLE row.
#:
#: The three ways to make it fit were weighed. Raising the budget is forbidden and wrong: the budget
#: exists to stop the machine convention bloating. Truncating a caveat string would silently corrupt
#: the honesty fields the finding contract makes mandatory. So the LIST view carries an identifying
#: summary and the `evidence` view returns one finding WHOLE, which is what the dedicated view is
#: for. `uncertainty`, `alternative_explanations`, `data_quality_caveats` and `next_experiment` are
#: therefore reachable in full, one finding at a time, and are never abridged in place.
FINDING_ROW_FIELDS: tuple[str, ...] = (
    "finding_id",
    "title",
    "severity",
    "affected_slice",
    "effect_size",
    "effect_units",
    "sample_size",
    "coverage",
    "is_actionable",
)


def _finding_row(payload: Mapping[str, Any]) -> dict[str, Any]:
    """One finding as a budget-safe summary row, with the pointer to its full evidence."""

    row = {key: payload.get(key) for key in FINDING_ROW_FIELDS}
    row["evidence_command"] = (
        f"aw runs query evidence --finding {payload.get('finding_id')}"
    )
    return row


def view_findings(*, limit: int, severity: str | None = None) -> QueryResult:
    """Ranked findings, refusals INCLUDED and ranked alongside actionable ones.

    A `cannot-determine` finding is not filtered out by default: Order 07's reasoning applies here
    unchanged, because omitting a refusal is indistinguishable from an oversight, and an agent that
    never sees it will assume the analysis simply was not requested.

    Each row is an identifying SUMMARY (see :data:`FINDING_ROW_FIELDS`) carrying the exact command
    that returns that finding whole, because the full contract does not fit one budgeted record.
    """

    refusals = stats_mod.refuse_under_powered_required_analyses()
    findings = findings_mod.findings_from_results(refusals.values())
    ranked = findings_mod.rank_findings(findings)
    rows = [_finding_row(f.to_dict()) for f in ranked]
    if severity:
        allowed = {s.value for s in findings_mod.Severity}
        if severity not in allowed:
            raise _refuse_field("severity", tuple(sorted(allowed)))
        rows = [r for r in rows if r.get("severity") == severity]
    hint = f"--severity {severity} " if severity else ""
    emitted, total, count, omitted, next_cmd = _bound(
        rows, view="findings", limit=limit, next_hint=hint
    )
    return QueryResult(
        view="findings",
        rows=emitted,
        total=total,
        emitted=count,
        omitted=omitted,
        next_command=next_cmd,
        payload={
            "findings_schema_version": findings_mod.FINDINGS_SCHEMA_VERSION,
            "actionable": sum(1 for r in rows if r.get("is_actionable")),
            "cannot_determine": sum(1 for r in rows if not r.get("is_actionable")),
        },
    )


def view_evidence(*, finding_id: str | None, limit: int) -> QueryResult:
    """The provenance of one finding: its sources, coverage, caveats and alternatives."""

    refusals = stats_mod.refuse_under_powered_required_analyses()
    ranked = findings_mod.rank_findings(
        findings_mod.findings_from_results(refusals.values())
    )
    if not finding_id:
        rows = [
            {
                "finding_id": f.finding_id,
                "title": f.title,
                "severity": f.severity.value,
                "sample_size": f.sample_size,
            }
            for f in ranked
        ]
        emitted, total, count, omitted, next_cmd = _bound(
            rows, view="evidence", limit=limit, next_hint=""
        )
        return QueryResult(
            view="evidence",
            rows=emitted,
            total=total,
            emitted=count,
            omitted=omitted,
            next_command=next_cmd,
            payload={"hint": "pass --finding <id> for one finding's full evidence"},
        )
    for finding in ranked:
        if finding.finding_id == finding_id:
            # ONE FINDING, SPLIT ACROSS BUDGETED RECORDS RATHER THAN ABRIDGED. Measured: the full
            # contract serializes to about 1267 bytes, over the enforced 1200-byte per-record budget.
            # The mandatory honesty fields (`uncertainty`, `alternative_explanations`,
            # `data_quality_caveats`, `next_experiment`) are exactly the ones a truncation would
            # damage, and a shortened caveat is worse than no caveat because it still reads as
            # complete. So the finding is returned WHOLE across several rows, each individually
            # inside budget, and nothing is dropped.
            payload = finding.to_dict()
            head = {
                key: payload.get(key) for key in FINDING_ROW_FIELDS if key in payload
            }
            head["section"] = "identity"
            rows = [
                head,
                {
                    "section": "uncertainty",
                    "finding_id": finding.finding_id,
                    "uncertainty": payload.get("uncertainty"),
                },
                {
                    "section": "alternatives",
                    "finding_id": finding.finding_id,
                    "alternative_explanations": payload.get("alternative_explanations"),
                },
                {
                    "section": "caveats",
                    "finding_id": finding.finding_id,
                    "data_quality_caveats": payload.get("data_quality_caveats"),
                },
                {
                    "section": "next-experiment",
                    "finding_id": finding.finding_id,
                    "next_experiment": payload.get("next_experiment"),
                    "recommendation": payload.get("recommendation"),
                    "evidence_sources": payload.get("evidence_sources"),
                },
            ]
            return QueryResult(
                view="evidence",
                rows=tuple(rows),
                total=len(rows),
                emitted=len(rows),
                payload={
                    "finding_id": finding.finding_id,
                    "findings_schema_version": payload.get("findings_schema_version"),
                    "sectioned": True,
                },
            )
    raise QueryError(
        "no such finding id; list the available ids with `aw runs query evidence`"
    )


def view_data_quality(
    entries: Sequence[Mapping[str, Any]], *, repo: Path | str | None, limit: int
) -> QueryResult:
    """Missingness, conservation violations and quality flags, per run and in total."""

    rows = [
        {
            "run_id": entry.get("run_id", ""),
            "is_complete": bool(entry.get("is_complete")),
            "quality_flags": list(entry.get("quality_flags") or ()),
            "warnings": len(entry.get("warnings") or ()),
        }
        for entry in entries
    ]
    rows.sort(key=lambda r: (r["is_complete"], str(r["run_id"])))
    emitted, total, count, omitted, next_cmd = _bound(
        rows, view="data-quality", limit=limit, next_hint=""
    )
    violations = sum(
        1 for e in entries if "conservation-violation" in (e.get("quality_flags") or ())
    )
    return QueryResult(
        view="data-quality",
        rows=emitted,
        total=total,
        emitted=count,
        omitted=omitted,
        next_command=next_cmd,
        payload={
            "incomplete_runs": sum(1 for e in entries if not e.get("is_complete")),
            "conservation_violations": violations,
            # A REAL COUNT, not a placeholder zero. An unreadable entry is missing data quality
            # information, which is precisely what this view reports, so hardcoding 0 here would have
            # asserted perfect coverage over a corpus that had lost members.
            "unreadable_entries": _unreadable_entry_count(repo),
        },
        caveats=(
            "a conservation violation is REPORTED, never repaired; the underlying numbers are "
            "unchanged",
        )
        if violations
        else (),
    )


def view_cache_status(
    entries: Sequence[Mapping[str, Any]], *, repo: Path | str | None, limit: int
) -> QueryResult:
    """Per-run cache state and totals, in Order 02's own stable vocabulary."""

    rows = [
        {
            "run_id": entry.get("run_id", ""),
            "is_complete": bool(entry.get("is_complete")),
            "schema_version": entry.get("schema_version"),
            "generated_at": entry.get("generated_at", ""),
        }
        for entry in entries
    ]
    emitted, total, count, omitted, next_cmd = _bound(
        rows, view="cache-status", limit=limit, next_hint=""
    )
    return QueryResult(
        view="cache-status",
        rows=emitted,
        total=total,
        emitted=count,
        omitted=omitted,
        next_command=next_cmd,
        payload={
            "cache_schema_version": cache_mod.CACHE_SCHEMA_VERSION,
            "cached_runs": len(entries),
            "unreadable_entries": _unreadable_entry_count(repo),
            "reason_codes": sorted(cache_mod.REASON_CODES),
        },
    )


def view_explain(*, taxonomy: str | None, price: str | None) -> QueryResult:
    """Provenance for a taxonomy activity class or a measured price era."""

    if taxonomy and price:
        raise QueryError("pass either --taxonomy or --price, not both")
    if taxonomy:
        classes = {c.value: c for c in taxonomy_mod.ActivityClass}
        if taxonomy not in classes:
            raise _refuse_field("taxonomy class", tuple(sorted(classes)))
        return QueryResult(
            view="explain",
            total=1,
            emitted=1,
            payload={
                "kind": "taxonomy",
                "activity_class": taxonomy,
                "taxonomy_version": taxonomy_mod.TAXONOMY_VERSION,
                "display_precedence": [
                    c.value for c in taxonomy_mod.DISPLAY_PRECEDENCE
                ],
                "unclassified_share_margin": taxonomy_mod.UNCLASSIFIED_SHARE_MARGIN,
            },
            caveats=(
                "a classification is derived from a command's shape, never from its text; the "
                "taxonomy refuses to retain command text",
            ),
        )
    if price:
        eras = {e.era_id: e for e in pricing_mod.MEASURED_ERAS}
        if price not in eras:
            raise _refuse_field("price era", tuple(sorted(eras)))
        era = eras[price]
        return QueryResult(
            view="explain",
            total=1,
            emitted=1,
            payload={
                "kind": "price",
                "era_id": era.era_id,
                "effective_from": era.effective_from,
                "effective_to": era.effective_to,
                "input_per_mtok": era.rates.input_per_mtok,
                "output_per_mtok": era.rates.output_per_mtok,
                "cache_read_per_mtok": era.rates.cache_read_per_mtok,
                "currency": era.rates.currency,
                "source": era.source,
                "source_version": era.source_version,
                "exact_match_count": era.exact_match_count,
                "pricing_schema_version": pricing_mod.PRICING_SCHEMA_VERSION,
            },
            caveats=(
                "these rates were FIT TO RECORDED COST rather than read from a published price "
                "sheet, so a cost derived from them is an estimate and is labeled one",
                "comparing spend across eras without stratifying by era is the measured price-era "
                "paradox; stratify before drawing a conclusion",
            ),
        )
    raise QueryError(
        "the explain view needs --taxonomy <activity-class> or --price <era-id>"
    )


# --------------------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------------------


def run_query(
    view: str,
    *,
    repo: Path | str | None = None,
    filters: Iterable[str] | None = None,
    group_by: str | Sequence[str] | None = None,
    metric: str | None = None,
    stat: str | None = None,
    limit: Any = None,
    analysis: str | None = None,
    finding_id: str | None = None,
    severity: str | None = None,
    taxonomy: str | None = None,
    price: str | None = None,
) -> QueryResult:
    """Answer one view. The ONE place a view name becomes a computation.

    Every argument crosses an allowlist before any corpus is read, so a malformed query costs no I/O
    and cannot partially execute.
    """

    name = (view or "").strip()
    if name not in VIEWS:
        raise _refuse_field("view", VIEWS)

    parsed_filters = parse_filters(filters)
    fields = parse_group_by(group_by)
    row_limit = _parse_limit(limit)
    metric_name = _validate_metric(metric)
    stat_name = _validate_stat(stat)

    # Views that need no corpus are answered BEFORE touching the filesystem.
    if name == "schema":
        return view_schema()
    if name == "explain":
        return view_explain(taxonomy=taxonomy, price=price)
    if name == "findings":
        return view_findings(limit=row_limit, severity=severity)
    if name == "evidence":
        return view_evidence(finding_id=finding_id, limit=row_limit)

    entries = [e for e in _cache_entries(repo) if _matches(e, parsed_filters)]

    if name == "overview":
        return view_overview(entries, repo=repo)
    if name == "metrics":
        return view_metrics(
            entries,
            metric=metric_name,
            stat=stat_name,
            group_by=fields,
            analysis=analysis,
            limit=row_limit,
        )
    if name == "distributions":
        return view_distributions(entries, metric=metric_name, limit=row_limit)
    if name == "slices":
        return view_slices(
            entries, group_by=fields, metric=metric_name, limit=row_limit
        )
    if name == "data-quality":
        return view_data_quality(entries, repo=repo, limit=row_limit)
    if name == "cache-status":
        return view_cache_status(entries, repo=repo, limit=row_limit)
    # Unreachable: `name` was validated against VIEWS above and every member is handled. Kept as a
    # loud failure rather than a silent `None` in case a view is added to the tuple and not here.
    raise QueryError(f"view {name!r} is declared but not implemented")

#!/usr/bin/env python3
"""Attempt-grain analytics views for ``aw runs query``: ``attempts``, ``tools`` and ``experiment``.

WHY A SECOND GRAIN. The run cache (``run_analytics_cache``) persists ONE record per run, so every
pre-existing view answers at run grain. The review-cost questions are per attempt: how a review's
tokens split into new input, cache reads, cache writes, output and reasoning; how many model steps
it took and how large the context was at its first and last step; whether its host session was new
or reused; which tools it called and how many bytes they returned; how often it had to be redone.
Those facts come from the session logs and are published by ``aw runs analyze`` as
``attempts.jsonl`` beside the dashboard (``run_dashboard.attempt_facts_jsonl``), one row per agent
session. This module reads that file; it never reads a session log itself.

ALLOWLISTED AND BOUNDED, like every other view. Filters, groupings, metrics and statistics are
closed tuples below; ``--limit`` is the shared row bound. A metric value is aggregated only over rows
that HAVE it (a session with no recorded cost contributes nothing to a cost statistic, and the row
counts say how many did); nothing is imputed.

UNDER-POWERED GROUPS ARE REFUSED PER GROUP. A group whose metric sample is below
``run_analytics_statistics.MINIMUM_SAMPLE_SIZE`` keeps its counts and totals (a count or a sum is a
measurement at any n) but its distribution statistics are withheld and the row says
``refused: below minimum n``. The threshold is the shared one and is not lowered here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from agent_workflows import run_analytics_statistics as stats_mod

__all__ = [
    "ATTEMPT_VIEWS",
    "ATTEMPT_FILTER_FIELDS",
    "ATTEMPT_GROUP_FIELDS",
    "ATTEMPT_METRICS",
    "ATTEMPT_STATS",
    "TOKEN_COMPONENTS",
    "load_attempt_rows",
    "attempts_path",
]

#: The views this module answers.
ATTEMPT_VIEWS: tuple[str, ...] = ("attempts", "tools", "experiment")

#: The token components reported separately. ``total_tokens`` is their sum.
TOKEN_COMPONENTS: tuple[str, ...] = (
    "input",
    "cache_read",
    "cache_write",
    "output",
    "reasoning",
)

#: Fields a ``--filter`` may name at attempt grain. Closed labels and opaque ids only.
ATTEMPT_FILTER_FIELDS: tuple[str, ...] = (
    "run",
    "set",
    "id6",
    "action",
    "role",
    "phase",
    "attempt",
    "host",
    "model",
    "model_source",
    "agent",
    "label",
    "review_variant",
    "code_commit",
    "repo_commit",
    "session_origin",
    "step_bucket",
    "outcome",
    "disposition",
    "readiness",
    "review_tier",
    "review_step",
    "review_checks",
    "date",
    "cost_split",
    "token_source",
)

#: Fields a ``--group-by`` may name at attempt grain. Excludes the unbounded ids (run, date).
ATTEMPT_GROUP_FIELDS: tuple[str, ...] = (
    "phase",
    "action",
    "role",
    "host",
    "model",
    "model_source",
    "agent",
    "label",
    "review_variant",
    "code_commit",
    "repo_commit",
    "session_origin",
    "step_bucket",
    "outcome",
    "disposition",
    "readiness",
    "review_tier",
    "review_step",
    "review_checks",
    "set",
    "id6",
    "attempt",
    "cost_split",
    "token_source",
)

#: Metrics the ``attempts`` view may aggregate.
ATTEMPT_METRICS: tuple[str, ...] = (
    "total_tokens",
    "fresh_tokens",
    *TOKEN_COMPONENTS,
    "cost",
    "cost_input",
    "cost_output",
    "cost_reasoning",
    "cost_cache_read",
    "model_seconds",
    "thinking_seconds_est",
    "tool_seconds",
    "steps",
    "context_first",
    "context_last",
    "context_max",
    "tool_calls",
    "tool_errors",
    "tool_output_bytes",
    "files_read",
    "wall",
    "turn_retries",
    "refusals",
    "reasks",
    "redo_total",
)

ATTEMPT_STATS: tuple[str, ...] = (
    "count",
    "sum",
    "mean",
    "median",
    "p25",
    "p75",
    "p90",
    "maximum",
)

#: The metrics the ``attempts`` view reports when the caller names none: the composition, steps and
#: context questions in one row. Narrow with ``--metric``.
DEFAULT_ATTEMPT_METRICS: tuple[str, ...] = (
    "total_tokens",
    *TOKEN_COMPONENTS,
    "cost",
    "steps",
    "context_first",
    "context_last",
)

#: The per-row maps the ``tools`` view tallies, and how each is labeled.
TOOL_SECTIONS: tuple[str, ...] = ("tools", "tool_bytes", "families", "read_counts")

#: Default and only main-session roles. A queue ATTEMPT is the main session; verifier and
#: corrective sessions are separate rows with their own role.
MAIN_ROLE = "main"


class AttemptQueryError(Exception):
    """A malformed attempt-grain query. The caller maps it to ``QueryError`` (exit 2)."""


def attempts_path(repo: Path | str | None) -> Path:
    """The published ``attempts.jsonl`` of the latest bundle, through the report resolver."""

    from agent_workflows import run_analytics_report as report_mod
    from agent_workflows import run_dashboard as dash_mod

    directory = report_mod.resolve_report_dir(repo)
    latest = directory / report_mod.LATEST_LINK_NAME / dash_mod.ATTEMPT_FACTS_FILENAME
    if latest.exists():
        return latest
    return directory / dash_mod.ATTEMPT_FACTS_FILENAME


def load_attempt_rows(
    repo: Path | str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Every session row in the latest published ``attempts.jsonl``, plus its header ``info``.

    Returns ``([], {})`` when no bundle has been published, which the views report as a missing
    corpus with the command that builds it, never as an empty answer.
    """

    path = attempts_path(repo)
    rows: list[dict[str, Any]] = []
    info: dict[str, Any] = {}
    try:
        handle = open(path, "r", encoding="utf-8")
    except OSError:
        return rows, info
    with handle:
        for line in handle:
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if not isinstance(obj, dict):
                continue
            if obj.get("record") == "header":
                info = dict(obj.get("info") or {})
                info["schema"] = obj.get("schema")
            elif obj.get("record") == "row":
                rows.append(obj)
    return rows, info


# --- parsing --------------------------------------------------------------------------------------


def _refuse(kind: str, allowed: Sequence[str]) -> AttemptQueryError:
    return AttemptQueryError(
        f"unknown {kind}; allowed {kind}s are: {', '.join(sorted(allowed))}"
    )


def parse_attempt_filters(raw: Iterable[str] | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for entry in raw or ():
        text = str(entry)
        if "=" not in text:
            raise AttemptQueryError(
                "a filter must be written name=value; "
                f"allowed names are: {', '.join(sorted(ATTEMPT_FILTER_FIELDS))}"
            )
        name, _, value = text.partition("=")
        name = name.strip()
        if name not in ATTEMPT_FILTER_FIELDS:
            raise _refuse("filter field", ATTEMPT_FILTER_FIELDS)
        if name in parsed:
            raise AttemptQueryError(f"filter field {name!r} was given twice")
        parsed[name] = value.strip()
    return parsed


def parse_attempt_group(raw: str | Sequence[str] | None) -> tuple[str, ...]:
    if raw is None:
        return ()
    items = [raw] if isinstance(raw, str) else list(raw)
    fields: list[str] = []
    for item in items:
        for token in (t.strip() for t in str(item).split(",")):
            if not token:
                continue
            if token not in ATTEMPT_GROUP_FIELDS:
                raise _refuse("grouping field", ATTEMPT_GROUP_FIELDS)
            if token not in fields:
                fields.append(token)
    return tuple(fields)


def parse_attempt_metrics(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return DEFAULT_ATTEMPT_METRICS
    out: list[str] = []
    for token in (t.strip() for t in str(raw).split(",")):
        if not token:
            continue
        if token not in ATTEMPT_METRICS:
            raise _refuse("attempt metric", ATTEMPT_METRICS)
        if token not in out:
            out.append(token)
    return tuple(out) or DEFAULT_ATTEMPT_METRICS


def parse_attempt_stat(raw: str | None) -> str:
    name = (raw or "median").strip()
    if name not in ATTEMPT_STATS:
        raise _refuse("attempt stat", ATTEMPT_STATS)
    return name


# --- aggregation ----------------------------------------------------------------------------------


def _value(row: Mapping[str, Any], metric: str) -> float | None:
    v = row.get(metric)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v)


def _label(row: Mapping[str, Any], field: str) -> str:
    v = row.get(field)
    if isinstance(v, (list, tuple)):
        return ",".join(str(x) for x in v) if v else "(not recorded)"
    return "(not recorded)" if v in (None, "") else str(v)


def _matches(row: Mapping[str, Any], filters: Mapping[str, str]) -> bool:
    for name, want in filters.items():
        v = row.get(name)
        if isinstance(v, (list, tuple)):
            if (
                want in v
                or want.upper() in [str(x).upper() for x in v]
                or want == ",".join(str(x) for x in v)
                or want.upper() == ",".join(str(x).upper() for x in v)
            ):
                continue
            return False
        if _label(row, name) != want and str(row.get(name) or "") != want:
            return False
    return True


def _stat(values: list[float], stat: str) -> float | None:
    if stat == "count":
        return float(len(values))
    if not values:
        return None
    if stat == "sum":
        return sum(values)
    dist = stats_mod.describe("v", values)
    value = getattr(dist, stat, None)
    return float(value) if isinstance(value, (int, float)) else None


def _round(v: float | None, metric: str = "") -> float | int | None:
    if v is None:
        return None
    if metric.startswith("cost"):
        return round(v, 4)
    if float(v).is_integer():
        return int(v)
    return round(v, 2)


def _group(
    rows: Sequence[Mapping[str, Any]], fields: Sequence[str]
) -> list[tuple[tuple[str, ...], list[Mapping[str, Any]]]]:
    groups: dict[tuple[str, ...], list[Mapping[str, Any]]] = {}
    for r in rows:
        groups.setdefault(tuple(_label(r, f) for f in fields), []).append(r)
    return sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))


def _select(
    rows: Sequence[Mapping[str, Any]],
    filters: Mapping[str, str],
    role: str | None,
    *,
    group_by: Sequence[str] = (),
) -> list[Mapping[str, Any]]:
    """Rows matching ``filters``; by default only MAIN sessions (one per queue attempt).

    A ``role`` or ``phase`` filter overrides the default, so ``--filter phase=verifier`` reaches the
    verifier sessions.
    """

    keep_all = (
        "role" in filters
        or "phase" in filters
        or role == "*"
        or "review_step" in filters
        or "review_checks" in filters
        or "review_step" in group_by
        or "review_checks" in group_by
    )
    selected: list[Mapping[str, Any]] = []
    for r in rows:
        if not _matches(r, filters):
            continue
        if not (keep_all or str(r.get("role") or "") == MAIN_ROLE):
            continue
        if (
            "review_step" in group_by
            and "review_step" not in filters
            and r.get("review_step") in (None, "")
        ):
            continue
        if (
            "review_checks" in group_by
            and "review_checks" not in filters
            and r.get("review_checks") in (None, "", [])
        ):
            continue
        selected.append(r)
    return selected


def summarize_group(
    members: Sequence[Mapping[str, Any]], metrics: Sequence[str], stat: str
) -> dict[str, Any]:
    """One group's row: counts, the chosen statistic per metric, token and cost SHARES, coverage."""

    out: dict[str, Any] = {"n": len(members)}
    minimum = stats_mod.MINIMUM_SAMPLE_SIZE
    refused: list[str] = []
    for m in metrics:
        vals = [v for v in (_value(r, m) for r in members) if v is not None]
        if stat in ("count", "sum") or len(vals) >= minimum:
            out[m] = _round(_stat(vals, stat), m)
        else:
            out[m] = None
            refused.append(m)
        if len(vals) != len(members):
            out.setdefault("with_value", {})[m] = len(vals)
    if refused:
        out["refused"] = f"below minimum n={minimum} for {stat}: {', '.join(refused)}"
    total = sum(_value(r, "total_tokens") or 0.0 for r in members)
    if total > 0:
        out["token_share"] = {
            c: round(sum(_value(r, c) or 0.0 for r in members) / total, 4)
            for c in TOKEN_COMPONENTS
        }
    priced = [r for r in members if _value(r, "cost_input") is not None]
    cost_total = sum(_value(r, "cost") or 0.0 for r in priced)
    if cost_total > 0:
        out["cost_share"] = {
            "input": round(
                sum(_value(r, "cost_input") or 0.0 for r in priced) / cost_total, 4
            ),
            "cache_read": round(
                sum(_value(r, "cost_cache_read") or 0.0 for r in priced) / cost_total, 4
            ),
            "output": round(
                sum(_value(r, "cost_output") or 0.0 for r in priced) / cost_total, 4
            ),
            "reasoning": round(
                sum(_value(r, "cost_reasoning") or 0.0 for r in priced) / cost_total, 4
            ),
        }
    out["with_cost"] = sum(1 for r in members if _value(r, "cost") is not None)
    out["with_model"] = sum(
        1
        for r in members
        if str(r.get("model_source") or "none") not in ("none", "", "unrecorded")
    )
    return out


def view_attempts(
    rows: Sequence[Mapping[str, Any]],
    *,
    filters: Mapping[str, str],
    group_by: Sequence[str],
    metrics: Sequence[str],
    stat: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected = _select(rows, filters, None, group_by=group_by)
    if not group_by:
        body = summarize_group(selected, metrics, stat)
        return [dict({"group": "all"}, **body)], {"selected": len(selected)}
    out = []
    for key, members in _group(selected, group_by):
        row: dict[str, Any] = dict(zip(group_by, key))
        row.update(summarize_group(members, metrics, stat))
        out.append(row)
    return out, {"selected": len(selected), "groups": len(out)}


def view_tools(
    rows: Sequence[Mapping[str, Any]],
    *,
    filters: Mapping[str, str],
    top: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Tool calls and output bytes per tool, command families, and the files read most often.

    Totals across the selected attempts, plus per-attempt medians for calls and bytes. Each section
    keeps its top ``top`` names by count; the payload reports how many names each section had.
    """

    selected = _select(rows, filters, None)
    calls: dict[str, int] = {}
    using: dict[str, int] = {}
    tbytes: dict[str, int] = {}
    per_attempt_calls: dict[str, list[float]] = {}
    families: dict[str, int] = {}
    files: dict[str, int] = {}
    for r in selected:
        for name, n in (r.get("tools") or {}).items():
            calls[name] = calls.get(name, 0) + int(n)
            using[name] = using.get(name, 0) + 1
            per_attempt_calls.setdefault(name, []).append(float(n))
        for name, n in (r.get("tool_bytes") or {}).items():
            tbytes[name] = tbytes.get(name, 0) + int(n)
        for name, n in (r.get("families") or {}).items():
            families[name] = families.get(name, 0) + int(n)
        for name, n in (r.get("read_counts") or {}).items():
            files[name] = files.get(name, 0) + int(n)
    total_bytes = sum(tbytes.values())
    out: list[dict[str, Any]] = []
    for name in sorted(calls, key=lambda k: (-calls[k], k))[:top]:
        out.append(
            {
                "section": "tool",
                "name": name,
                "calls": calls[name],
                "attempts_using": using[name],
                "median_calls_per_using_attempt": _round(
                    _stat(per_attempt_calls[name], "median")
                ),
                "output_bytes": tbytes.get(name, 0),
                "output_bytes_share": round(tbytes.get(name, 0) / total_bytes, 4)
                if total_bytes
                else None,
            }
        )
    for name in sorted(families, key=lambda k: (-families[k], k))[:top]:
        out.append({"section": "command", "name": name, "count": families[name]})
    for name in sorted(files, key=lambda k: (-files[k], k))[:top]:
        out.append({"section": "file_read", "name": name, "count": files[name]})
    payload = {
        "selected": len(selected),
        "tool_names": len(calls),
        "command_families": len(families),
        "files_read_distinct": len(files),
        "tool_output_bytes_total": total_bytes,
        "top_per_section": top,
    }
    return out, payload


def view_experiment(
    rows: Sequence[Mapping[str, Any]],
    *,
    filters: Mapping[str, str],
    group_by: Sequence[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """One row per (plan id6, review variant, model): cost or tokens, steps, wall, redos, outcome.

    Each queue attempt is one main session; its verifier and corrective sessions are folded in as
    the same item's spend, so the row prices the whole review of that plan under that variant and
    model. Rows with no recorded cost report tokens (``cost`` stays null, ``with_cost`` says so).
    ``outcome`` lists the distinct final dispositions (``reviewed``, ``approved``, ``fail-gate``).
    ``readiness`` comes from the attempt's ``review_readiness``, recorded from this plan's commit
    onward, with ``absent`` meaning the review wrote no valid value and ``(not recorded)`` meaning
    the run predates the recording.
    """

    keys = tuple(group_by) or ("id6", "review_variant", "model")
    scoped = [r for r in rows if _matches(r, filters)]
    by_item: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for r in scoped:
        by_item.setdefault(
            (str(r.get("run") or ""), str(r.get("id6") or "")), []
        ).append(r)
    out: list[dict[str, Any]] = []
    groups: dict[
        tuple[str, ...], list[tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]]
    ] = {}
    for members in by_item.values():
        mains = [m for m in members if m.get("role") == MAIN_ROLE]
        if not mains:
            continue
        key = tuple(_label(mains[0], f) for f in keys)
        groups.setdefault(key, []).append((members, mains))
    for key, items in sorted(groups.items(), key=lambda kv: kv[0]):
        costs, tokens, steps, walls, redos, attempts = [], [], [], [], [], []
        outcomes: dict[str, int] = {}
        readiness_counts: dict[str, int] = {}
        priced = 0
        for members, mains in items:
            c_vals = [_value(m, "cost") for m in members]
            if any(v is not None for v in c_vals):
                priced += 1
                costs.append(sum(v for v in c_vals if v is not None))
            tokens.append(sum(_value(m, "total_tokens") or 0.0 for m in members))
            steps.append(sum(_value(m, "steps") or 0.0 for m in members))
            walls.append(sum(_value(m, "wall") or 0.0 for m in mains))
            redos.append(sum(_value(m, "redo_total") or 0.0 for m in mains))
            attempts.append(float(len(mains)))
            last = max(mains, key=lambda m: (m.get("attempt") or 0))
            disp = str(last.get("disposition") or "(none)")
            outcomes[disp] = outcomes.get(disp, 0) + 1
            r_label = _label(last, "readiness")
            readiness_counts[r_label] = readiness_counts.get(r_label, 0) + 1
        row: dict[str, Any] = dict(zip(keys, key))
        row.update(
            {
                "items": len(items),
                "attempts": int(sum(attempts)),
                "with_cost": priced,
                "cost_median": _round(_stat(costs, "median"), "cost")
                if costs
                else None,
                "cost_sum": _round(_stat(costs, "sum"), "cost") if costs else None,
                "tokens_median": _round(_stat(tokens, "median")),
                "steps_median": _round(_stat(steps, "median")),
                "wall_median": _round(_stat(walls, "median")),
                "redos": int(sum(redos)),
                "outcome": dict(sorted(outcomes.items())),
                "readiness": dict(sorted(readiness_counts.items())),
            }
        )
        out.append(row)
    return out, {
        "grouped_by": list(keys),
        "items": sum(len(v) for v in groups.values()),
    }

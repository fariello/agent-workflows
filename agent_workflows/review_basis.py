"""Provisional review bases: which prerequisite TEXT a review was performed against.

`--review-unreviewed-deps` (spec 25kzda 2.9, added 2026-11-13) lets a review turn start while a
prerequisite plan is still `to-review`. That turns a dependency chain that would review one plan at
a time into work that can run in parallel shards, at one known cost: the prerequisite's own review
may later change the design the dependent was reviewed against, and nothing would notice.

This module is what notices. When a review is dispatched under the flag, the driver records, for
each prerequisite accepted only because of the flag, the prerequisite's id6 and a digest of its
reviewed contract (`ipd_lifecycle.frozen_region_digest`: Scope-Paths plus each E/V item's action
text, so ticking checkboxes or appending history does not count as a change). Later,
:func:`stale_bases` compares each recorded digest with the prerequisite's current text. A mismatch
means the dependent was reviewed against a design that no longer exists and should be re-reviewed.

Records live in the checkout's control root (`.aw/state/review-basis/<consumer-id6>.json`), shared
by every lane worktree of the checkout, so a prerequisite reviewed in a different run or shard is
still compared. Re-reviewing the consumer rewrites its record from scratch: with no provisional
prerequisite left, the record is deleted, which is what clears a stale flag.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

SCHEMA = "aw.review-basis/v1"

#: Prerequisite statuses the flag additionally accepts for a review consumer.
PROVISIONAL_STATUSES = ("to-review",)


def basis_dir(repo: Path) -> Path:
    from agent_workflows import ipd_lifecycle

    return ipd_lifecycle.checkout_control_root(Path(repo)) / "state" / "review-basis"


def contract_digest(text: str) -> str:
    from agent_workflows import ipd_lifecycle

    return ipd_lifecycle.frozen_region_digest(text)


@dataclass(frozen=True)
class StaleBasis:
    consumer: str
    target: str
    target_status: Optional[str]
    reason: str
    run_id: str
    consumer_status: Optional[str] = None


def record_basis(
    repo: Path,
    consumer_id6: str,
    targets: Sequence[Dict[str, str]],
    *,
    run_id: str,
    at: str,
) -> Optional[Path]:
    """Replace the consumer's record with `targets` (`{"id6", "digest", "status"}` each).

    An empty `targets` deletes the record: the consumer was reviewed against settled prerequisites
    only, so nothing about it is provisional any more.
    """
    path = basis_dir(repo) / f"{consumer_id6}.json"
    if not targets:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return None
    from agent_workflows.runner_shared import atomic_write_json

    atomic_write_json(
        path,
        {
            "schema": SCHEMA,
            "consumer": consumer_id6,
            "run_id": run_id,
            "recorded_at": at,
            "targets": [dict(t) for t in targets],
        },
    )
    return path


def provisional_targets(
    repo: Path, item: Dict[str, Any], state: Dict[str, Any]
) -> List[Dict[str, str]]:
    """The prerequisites of a review `item` that are satisfied ONLY because of the flag."""
    from agent_workflows import runner_shared as rs
    from agent_workflows import selectors
    from agent_workflows.artifact_meta import read_loose_status

    out: List[Dict[str, str]] = []
    deps = item.get("dependencies") or ()
    if not deps:
        return out
    seen_targets: set[str] = set()
    with selectors.scan_once():
        for dep in deps:
            edge = rs.parse_dependency_token(str(dep))
            if edge is None or getattr(edge, "target_type", None) != "ipd":
                continue
            if edge.id6 in seen_targets:
                continue
            seen_targets.add(edge.id6)
            try:
                dep_path = rs.resolve_plan_path(Path(repo), "", edge.id6)
                text = dep_path.read_text(encoding="utf-8")
            except Exception:
                continue
            status = read_loose_status(text)
            if status in PROVISIONAL_STATUSES:
                out.append(
                    {"id6": edge.id6, "digest": contract_digest(text), "status": status}
                )
    return out


#: Prerequisite statuses at which a recorded basis is SETTLED if its contract is also unchanged.
SETTLED_STATUSES = ("reviewed", "approved", "auto-approved", "executed")

#: Consumer statuses and plan directories that are terminal and can never be re-reviewed.
TERMINAL_CONSUMER_STATUSES = (
    "executed",
    "superseded",
    "not-executed",
    "rejected",
    "abandoned",
)
TERMINAL_PLAN_DIRS = (
    "executed",
    "superseded",
    "not-executed",
    "rejected",
    "abandoned",
)

#: Consumer statuses that already carry human approval (separated from unapproved consumers).
APPROVED_CONSUMER_STATUSES = ("approved", "auto-approved")

#: Recommend `aw partition ... --split-sets` once a stale re-review list exceeds this size.
PARTITION_SUGGEST_THRESHOLD = 8

#: Cap prerequisite-to-consumer detail lines in end-of-run stderr advice to prevent walls of text.
MAX_TARGET_DETAIL_LINES = 12


def _is_orchestrator_text(text: str) -> bool:
    """Return True when plan text declares ``- Kind: orchestrator``."""
    from agent_workflows import artifact_meta as _meta

    role = _meta.read_text(
        _meta.metadata_region(text[:4096]), record_type="ipd"
    ).fields.get("plan_role")
    return str(role or "").strip().lower() == "orchestrator"


def stale_bases(repo: Path, *, prune: bool = True) -> List[StaleBasis]:
    """Every recorded basis whose prerequisite's contract has changed since the review used it.

    Skips (and with `prune`, deletes) records for consumers that are already terminal
    (`executed`, `superseded`, `not-executed`, `rejected`, `abandoned`) or missing on disk,
    as well as records whose every prerequisite settled without its contract changing.
    """
    from agent_workflows import runner_shared as rs
    from agent_workflows import selectors
    from agent_workflows.artifact_meta import read_loose_status

    d = basis_dir(repo)
    if not d.is_dir():
        return []
    basis_files = sorted(d.glob("*.json"))
    if not basis_files:
        return []

    out: List[StaleBasis] = []
    # Cache per id6 within one read-only sweep: many consumers reference the same prerequisites,
    # and selectors.scan_once() avoids re-walking/re-querying the plans tree on each unique target.
    target_cache: Dict[str, Optional[tuple[Optional[str], str]]] = {}
    consumer_cache: Dict[str, tuple[bool, Optional[str]]] = {}

    def _read_target(tid: str) -> Optional[tuple[Optional[str], str]]:
        if tid in target_cache:
            return target_cache[tid]
        try:
            text = rs.resolve_plan_path(Path(repo), "", tid).read_text(encoding="utf-8")
            snapshot: Optional[tuple[Optional[str], str]] = (
                read_loose_status(text),
                contract_digest(text),
            )
        except Exception:
            snapshot = None
        target_cache[tid] = snapshot
        return snapshot

    def _read_consumer(cid: str) -> tuple[bool, Optional[str]]:
        """Return ``(is_terminal_or_missing, consumer_status)`` for consumer ``cid``."""
        if cid in consumer_cache:
            return consumer_cache[cid]
        try:
            cpath = rs.resolve_plan_path(Path(repo), "", cid)
            text = cpath.read_text(encoding="utf-8")
        except Exception:
            consumer_cache[cid] = (True, None)
            return (True, None)
        cstatus = read_loose_status(text)
        norm_status = str(cstatus or "").strip().lower()
        in_terminal_dir = any(part in TERMINAL_PLAN_DIRS for part in cpath.parts)
        is_non_reviewable = (
            in_terminal_dir
            or (norm_status in TERMINAL_CONSUMER_STATUSES)
            or _is_orchestrator_text(text)
        )
        res = (is_non_reviewable, norm_status or None)
        consumer_cache[cid] = res
        return res

    with selectors.scan_once():
        for f in basis_files:
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            consumer = str(rec.get("consumer") or f.stem)
            run_id = str(rec.get("run_id") or "")

            consumer_done, consumer_status = _read_consumer(consumer)
            if consumer_done:
                if prune:
                    try:
                        f.unlink()
                    except OSError:
                        pass
                continue

            settled = 0
            targets = list(rec.get("targets") or ())
            for t in targets:
                tid = str(t.get("id6") or "")
                if not tid:
                    continue
                snapshot = _read_target(tid)
                if snapshot is None:
                    out.append(
                        StaleBasis(
                            consumer,
                            tid,
                            None,
                            "prerequisite plan not found",
                            run_id,
                            consumer_status=consumer_status,
                        )
                    )
                    continue
                status, digest = snapshot
                if digest == t.get("digest"):
                    if status in SETTLED_STATUSES:
                        settled += 1
                    continue
                out.append(
                    StaleBasis(
                        consumer,
                        tid,
                        status,
                        f"{tid}'s steps or scope changed (now {status or 'unknown'}) since {consumer} was reviewed against it",
                        run_id,
                        consumer_status=consumer_status,
                    )
                )
            if prune and targets and settled == len(targets):
                try:
                    f.unlink()
                except OSError:
                    pass
    return out


def _format_rereview_command(consumers: Sequence[str], host: str) -> tuple[str, bool]:
    """Format direct run command for small lists or partitioned command for large lists."""
    ids_str = " ".join(consumers)
    if len(consumers) > PARTITION_SUGGEST_THRESHOLD:
        return (
            f"aw partition -t plans --action review --run {host} --split-sets {ids_str}",
            True,
        )
    return (f"aw {host} run --action review {ids_str}", False)


def stale_report_lines(
    stale: Sequence[StaleBasis],
    host: str = "oc",
    *,
    other_live_runs: Sequence[str] = (),
) -> List[str]:
    """Plain-language advice about reviews that may rest on an outdated design.

    This is advice printed after a run ends, not a failure of that run, so the text says so first.
    The list covers the whole checkout, not only the run printing it. When other runs are still
    live, re-reviewing now could be wasted work (they may change more prerequisites), so the advice
    says to wait for them first.

    Separates already-approved consumers from unapproved ones, and suggests `aw partition` with
    `--split-sets` when the consumer list is large.
    """
    if not stale:
        return []
    status_by_consumer: Dict[str, Optional[str]] = {}
    for s in stale:
        if (
            s.consumer not in status_by_consumer
            or status_by_consumer[s.consumer] is None
        ):
            status_by_consumer[s.consumer] = s.consumer_status

    consumers = sorted(status_by_consumer)
    approved = [
        c
        for c in consumers
        if (status_by_consumer.get(c) or "").lower() in APPROVED_CONSUMER_STATUSES
    ]
    unapproved = [c for c in consumers if c not in approved]

    by_target: Dict[str, List[str]] = {}
    for s in stale:
        by_target.setdefault(s.target, [])
        if s.consumer not in by_target[s.target]:
            by_target[s.target].append(s.consumer)
    lines = [
        "[REVIEW-BASIS-STALE] Advice, not a failure: this run's own results stand.",
        f"  {len(consumers)} plan(s) in this checkout (not only this run) were reviewed while a plan they "
        "depend on was still unreviewed. That plan's own review has since changed its steps or scope, "
        "so these reviews may rest on an outdated design and should be reviewed again.",
        "  Changed prerequisite -> plans reviewed against its old version:",
    ]
    sorted_targets = sorted(by_target)
    if len(sorted_targets) > MAX_TARGET_DETAIL_LINES:
        ranked = sorted(by_target, key=lambda t: (-len(by_target[t]), t))
        shown_targets = ranked[:MAX_TARGET_DETAIL_LINES]
        omitted = len(ranked) - len(shown_targets)
        for target in shown_targets:
            lines.append(f"    {target} -> {' '.join(sorted(by_target[target]))}")
        lines.append(
            f"    ... and {omitted} more changed prerequisite(s) "
            f"(see .aw/state/review-basis/)"
        )
    else:
        for target in sorted_targets:
            lines.append(f"    {target} -> {' '.join(sorted(by_target[target]))}")

    if unapproved and approved:
        lines.append(
            f"  Status breakdown: {len(unapproved)} unapproved (need re-review), "
            f"{len(approved)} already approved (re-review only if the prerequisite changes affect their design)."
        )
        primary_ids = unapproved
    elif approved:
        lines.append(
            f"  Note: all {len(approved)} flagged plan(s) are already approved; "
            "re-review only if the prerequisite changes affect their design."
        )
        primary_ids = approved
    else:
        primary_ids = consumers

    primary_cmd, is_partitioned = _format_rereview_command(primary_ids, host)
    if other_live_runs:
        lines.append(
            f"  Not yet: {len(other_live_runs)} other run(s) are still active "
            f"({', '.join(other_live_runs)}) and may change more prerequisites. Wait for them to "
            "finish; the last one to finish prints the final list."
        )
        if is_partitioned:
            lines.append(
                f"  Then split into parallel review shards with: {primary_cmd}"
            )
        else:
            lines.append(f"  Then re-review with: {primary_cmd}")
    else:
        if is_partitioned:
            lines.append(
                f"  No other runs are active; with {len(primary_ids)} plans, split into parallel review shards with: {primary_cmd}"
            )
        else:
            lines.append(
                f"  No other runs are active, so re-review now with: {primary_cmd}"
            )

    if unapproved and approved:
        approved_cmd, _ = _format_rereview_command(approved, host)
        lines.append(
            f"  Optional (already approved, {len(approved)} plan(s)): {approved_cmd}"
        )
    return lines


def live_run_ids(repo: Path, *, exclude: str = "") -> List[str]:
    """Run ids in this checkout whose driver is live right now (never raises)."""
    try:
        from agent_workflows import runner_shared as rs
        from agent_workflows.runner_stop import LIVENESS_LIVE, run_liveness

        root = rs.state_root(repo)
        out = []
        for d in sorted(root.glob("run-*")):
            if d.name != exclude and d.is_dir() and run_liveness(d) == LIVENESS_LIVE:
                out.append(d.name)
        return out
    except Exception:
        return []


def report_stale_bases(
    repo: Any, *, host: str = "oc", stream: Any = None, run_id: str = ""
) -> List[str]:
    """Print the stale-basis advice (never raises; prints nothing when there is nothing stale)."""
    import sys

    try:
        stale = stale_bases(Path(repo))
        lines = (
            stale_report_lines(
                stale,
                host=host,
                other_live_runs=live_run_ids(Path(repo), exclude=run_id),
            )
            if stale
            else []
        )
    except Exception:
        return []
    out = stream if stream is not None else sys.stderr
    for line in lines:
        print(line, file=out)
    return lines

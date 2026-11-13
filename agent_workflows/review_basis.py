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
    from agent_workflows.selectors import read_front_matter_status

    out: List[Dict[str, str]] = []
    for dep in item.get("dependencies") or ():
        edge = rs.parse_dependency_token(str(dep))
        if edge is None or getattr(edge, "target_type", None) != "ipd":
            continue
        try:
            dep_path = rs.resolve_plan_path(Path(repo), "", edge.id6)
            text = dep_path.read_text(encoding="utf-8")
        except Exception:
            continue
        status = read_front_matter_status(text)
        if status in PROVISIONAL_STATUSES:
            out.append(
                {"id6": edge.id6, "digest": contract_digest(text), "status": status}
            )
    return out


#: Prerequisite statuses at which a recorded basis is SETTLED if its contract is also unchanged.
SETTLED_STATUSES = ("reviewed", "approved", "auto-approved", "executed")


def stale_bases(repo: Path, *, prune: bool = True) -> List[StaleBasis]:
    """Every recorded basis whose prerequisite's contract has changed since the review used it.

    With `prune`, a record whose every prerequisite has since been reviewed WITHOUT its contract
    changing is deleted: the design the consumer was reviewed against turned out to be the final
    one, so there is nothing left to recheck.
    """
    from agent_workflows import runner_shared as rs
    from agent_workflows.selectors import read_front_matter_status

    d = basis_dir(repo)
    if not d.is_dir():
        return []
    out: List[StaleBasis] = []
    for f in sorted(d.glob("*.json")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        consumer = str(rec.get("consumer") or f.stem)
        settled = 0
        targets = list(rec.get("targets") or ())
        for t in targets:
            tid = str(t.get("id6") or "")
            if not tid:
                continue
            try:
                text = rs.resolve_plan_path(Path(repo), "", tid).read_text(
                    encoding="utf-8"
                )
            except Exception:
                out.append(
                    StaleBasis(
                        consumer,
                        tid,
                        None,
                        "prerequisite plan not found",
                        str(rec.get("run_id") or ""),
                    )
                )
                continue
            status = read_front_matter_status(text)
            if contract_digest(text) == t.get("digest"):
                if status in SETTLED_STATUSES:
                    settled += 1
                continue
            out.append(
                StaleBasis(
                    consumer,
                    tid,
                    status,
                    f"{tid}'s steps or scope changed (now {status or 'unknown'}) since {consumer} was reviewed against it",
                    str(rec.get("run_id") or ""),
                )
            )
        if prune and targets and settled == len(targets):
            try:
                f.unlink()
            except OSError:
                pass
    return out


def stale_report_lines(stale: Sequence[StaleBasis], host: str = "oc") -> List[str]:
    """Human-readable warning lines, ending with the command that re-reviews the affected plans."""
    if not stale:
        return []
    consumers = sorted({s.consumer for s in stale})
    lines = [
        f"[REVIEW-BASIS-STALE] {len(consumers)} plan(s) were reviewed against a prerequisite that "
        "was still 'to-review' and has since changed, so their review may rest on an old design:"
    ]
    for s in stale:
        lines.append(f"  - {s.consumer}: {s.reason}")
    lines.append(
        f"  Re-review them: aw {host} run --action review {' '.join(consumers)}"
    )
    return lines


def report_stale_bases(repo: Any, *, host: str = "oc", stream: Any = None) -> List[str]:
    """Print the stale-basis warning (never raises; prints nothing when there is nothing stale)."""
    import sys

    try:
        lines = stale_report_lines(stale_bases(Path(repo)), host=host)
    except Exception:
        return []
    out = stream if stream is not None else sys.stderr
    for line in lines:
        print(line, file=out)
    return lines

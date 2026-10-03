#!/usr/bin/env python3
"""THE COMMITTED GATE-DROP AUDITOR: census done/ backlog items whose close dropped a release gate.

WHY THIS FILE EXISTS, stated first because its whole value is reproducibility. Every number in
plan 1hrlp3 (and backlog item mbjuv5 before it) quotes a count of release-gated backlog items
closed done without satisfying any of the three legitimacy paths (HANDOFF, SATISFIED, DE-GATED).
Until this file landed, those numbers were derived from ad-hoc shell scripts, run in a shell
and thrown away. The contract this file owes its callers inherits verbatim from runner_fork_scan:
the deliverable "is not 'a number' but 'the SAME number, next week, from a different machine,
by a different agent'".

THE PREDICATE IS THE SINGLE AUTHORITY AND MUST NOT BE REIMPLEMENTED.
This auditor imports `check_engine.evaluate_blocking_close` as the single authority for
legitimacy. It opens no file for writing, performs no git mutation, and mutates no record.

WHY A SHARED INDEX RATHER THAN PER-ITEM RE-WALKS:
find_from_backlog_artifacts re-walks the complete plans tree plus the specs tree on every call
(230 ms for a single item), so asking it per candidate took 84.2 s across 250 gated done items,
while the shared check_engine._from_backlog_carrier_index produced the whole mapping in 351 ms.
This auditor builds the index ONCE and passes it as carrier_index= on every predicate call,
and reuses the same index for reason-class determination.

REASON-CLASS DERIVATION WITHOUT PROSE MATCHING:
The two error branches (no carrier vs carrier not executed) are distinguished structurally:
the carrier-not-executed branch is reached only when the item has at least one SAME-GATE carrier.
The auditor asks that question directly from the shared index filtered by _same_release against
the item's gate, never by regex or substring matching against the verdict's prose reason.

PREDICATE-SHIP BOUNDARY AND PARTITIONING:
An item closed before the release gate predicate shipped was never a bypass, because no gate
existed to bypass. The audit partitions findings into pre-predicate, post-predicate, and undated
buckets against the date plan orb9zb was finalized.

USAGE:
    python3 tools/gate_drop_audit.py               # human-readable report
    python3 tools/gate_drop_audit.py --json        # machine-readable JSON
    python3 tools/gate_drop_audit.py --naive       # naive per-item walk (for timing comparison)

Exit status is 0 whenever the audit completed. This is a reporting tool, not a gate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

from agent_workflows import backlog, check_engine


#: The date plan orb9zb was finalized (commit 844533abf, Tue Aug 25 23:41:30 2026 -0400),
#: introducing check_engine.evaluate_blocking_close and the release gate consistency rules.
#: History records carry a date only. A close dated on the boundary day (2026-08-25) is partitioned
#: as post-predicate (the predicate merged that day), with the same-day cohort noted as boundary-ambiguous.
PREDICATE_SHIP_DATE = "2026-08-25"

#: Regex matching workflow history records:
#: - YYYY-MM-DD <label> (<actor>): <message>
_HIST_RECORD_RE = re.compile(
    r"^-\s+(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<label>\S+)\s+\((?P<actor>[^)]+)\):\s*(?P<msg>.*)$"
)


def repo_root_dir() -> Path:
    """Resolve the repository root directory relative to this script."""
    return Path(__file__).resolve().parent.parent


def extract_close_info(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract (close_date, close_actor, close_message) from the item's ## Workflow history.

    Reads the first (newest) record in ## Workflow history that records a close to done:
      - a `done (...)` record (any actor, e.g. `aw set`, `aw backlog`), OR
      - a `set (aw backlog)` record (the flag spelling's tag written by backlog._reattach_history).

    Explicitly excludes `graduated` records (graduating is not closing).
    Does NOT require the message of a `set (aw backlog)` record to match `status -> done`
    (custom messages like `FIXED by ...` are accepted).
    Returns (None, None, None) if no datable close record is found.
    """
    hm = re.search(r"^##\s+Workflow history\s*$", text, re.MULTILINE)
    if not hm:
        return (None, None, None)

    tail = text[hm.end() :]
    for line in tail.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            break
        m = _HIST_RECORD_RE.match(line)
        if m:
            date_str = m.group("date")
            label = m.group("label")
            actor = m.group("actor")
            msg = m.group("msg").strip()
            if label == "done" or (label == "set" and actor == "aw backlog"):
                return (date_str, actor, msg)

    return (None, None, None)


def classify_reason(
    repo_root: Path,
    item_id6: Optional[str],
    blocks_release: str,
    carrier_index: Optional[Dict[str, List[Tuple[Path, Optional[str]]]]],
    release_cache: Dict[str, Optional[Path]],
) -> str:
    """Derive reason-class structurally: carrier-not-executed vs no-carrier.

    Distinguishes the two error branches without substring matching on prose:
    the carrier-not-executed branch is reached only when the item has at least
    one SAME-GATE carrier.
    """
    if not item_id6:
        return "no-carrier"

    if carrier_index is not None:
        carrier_items = carrier_index.get(item_id6, [])
    else:
        carrier_items = check_engine.find_from_backlog_artifacts(repo_root, item_id6)

    has_same_gate = any(
        check_engine._same_release(
            repo_root, carrier_br, blocks_release, cache=release_cache
        )
        for _, carrier_br in carrier_items
    )
    return "carrier-not-executed" if has_same_gate else "no-carrier"


def census(repo_root: Path, *, naive: bool = False) -> Dict[str, Any]:
    """Execute the full read-only gate-drop audit over repo_root.

    Returns a structured dictionary reproducible on demand.
    """
    repo_root = Path(repo_root).resolve()

    # 1. Iterate candidates: must be under done/ directory AND have - Status: done metadata
    candidates: List[Tuple[Path, str]] = []
    for item_path in backlog._iter_items(repo_root):
        if "done" not in item_path.parts:
            continue
        try:
            item_text = item_path.read_text(encoding="utf-8")
        except OSError:
            continue
        if check_engine._status_meta(item_text) != "done":
            continue
        if not check_engine._read_blocks_release(item_text):
            continue
        candidates.append((item_path, item_text))

    # 2. Build carrier index once (unless naive mode requested)
    carrier_idx: Optional[Dict[str, List[Tuple[Path, Optional[str]]]]] = None
    if not naive:
        carrier_idx = check_engine._from_backlog_carrier_index(repo_root)

    # 3. Evaluate each candidate using evaluate_blocking_close as single authority
    findings: List[Dict[str, Any]] = []
    release_cache: Dict[str, Optional[Path]] = {}

    for item_path, item_text in candidates:
        verdict = check_engine.evaluate_blocking_close(
            repo_root,
            item_path,
            "done",
            item_text=item_text,
            carrier_index=carrier_idx,
        )
        if not verdict.legitimate and verdict.severity == "error":
            item_id6 = check_engine._read_item_id(item_text)
            gate = check_engine._read_blocks_release(item_text) or ""
            reason_class = classify_reason(
                repo_root, item_id6, gate, carrier_idx, release_cache
            )
            close_date, close_actor, close_msg = extract_close_info(item_text)

            if close_date is None:
                partition = "undated"
            elif close_date < PREDICATE_SHIP_DATE:
                partition = "pre-predicate"
            else:
                partition = "post-predicate"

            item_obj = backlog.parse_item(item_text)
            work_kind = item_obj.kind or "unknown"

            try:
                rel_filename = str(item_path.relative_to(repo_root)).replace("\\", "/")
            except ValueError:
                rel_filename = str(item_path).replace("\\", "/")

            findings.append(
                {
                    "id6": item_id6 or "",
                    "filename": rel_filename,
                    "work_kind": work_kind,
                    "gate": gate,
                    "reason": verdict.reason,
                    "reason_class": reason_class,
                    "close_date": close_date,
                    "close_actor": close_actor,
                    "close_message": close_msg,
                    "partition": partition,
                }
            )

    # Deterministic sort: by id6
    findings.sort(key=lambda r: r["id6"])

    # Aggregations
    pre_predicate_count = sum(1 for f in findings if f["partition"] == "pre-predicate")
    post_predicate_count = sum(
        1 for f in findings if f["partition"] == "post-predicate"
    )
    undated_count = sum(1 for f in findings if f["partition"] == "undated")
    boundary_same_day_count = sum(
        1 for f in findings if f["close_date"] == PREDICATE_SHIP_DATE
    )

    reason_class_counts: Dict[str, int] = {}
    for f in findings:
        rc = f["reason_class"]
        reason_class_counts[rc] = reason_class_counts.get(rc, 0) + 1

    work_kind_counts: Dict[str, int] = {}
    for f in findings:
        wk = f["work_kind"]
        work_kind_counts[wk] = work_kind_counts.get(wk, 0) + 1

    return {
        "repo_root": str(repo_root),
        "predicate_ship_date": PREDICATE_SHIP_DATE,
        "predicate_ship_commit": "844533abf",
        "predicate_ship_derivation": "orb9zb finalize commit (Tue Aug 25 23:41:30 2026 -0400)",
        "candidates_checked": len(candidates),
        "total_findings": len(findings),
        "partition_counts": {
            "pre_predicate": pre_predicate_count,
            "post_predicate": post_predicate_count,
            "undated": undated_count,
            "boundary_same_day": boundary_same_day_count,
        },
        "reason_class_counts": reason_class_counts,
        "work_kind_counts": work_kind_counts,
        "findings": findings,
    }


def format_human_report(data: Dict[str, Any]) -> str:
    """Format the audit findings for human consumption on stdout."""
    lines: List[str] = [
        "================================================================================",
        "                     RELEASE GATE DROP AUDIT CENSUS                             ",
        "================================================================================",
        f"Predicate ship date boundary: {data['predicate_ship_date']} ({data['predicate_ship_derivation']})",
        f"Gated done/ candidates examined: {data['candidates_checked']}",
        f"Total illegitimate close findings: {data['total_findings']}",
        "",
        "--- Date Partitioning ---",
        f"  Pre-predicate (< {data['predicate_ship_date']}):   {data['partition_counts']['pre_predicate']}",
        f"  Post-predicate (>= {data['predicate_ship_date']}):  {data['partition_counts']['post_predicate']} (includes {data['partition_counts']['boundary_same_day']} same-day boundary-ambiguous)",
        f"  Undated (no close record):     {data['partition_counts']['undated']}",
        "",
        "--- Reason Class Breakdown ---",
    ]
    for rc, count in sorted(data["reason_class_counts"].items()):
        lines.append(f"  {rc:25s}: {count}")

    lines.append("")
    lines.append("--- Work-Kind Breakdown ---")
    for wk, count in sorted(data["work_kind_counts"].items()):
        lines.append(f"  {wk:25s}: {count}")

    lines.append("")
    lines.append("--- Findings Detail ---")
    header = f"{'ID6':<8} {'Date':<11} {'Kind':<9} {'Reason Class':<22} {'Partition':<15} {'Filename'}"
    lines.append(header)
    lines.append("-" * len(header))
    for f in data["findings"]:
        date_str = f["close_date"] or "undated"
        lines.append(
            f"{f['id6']:<8} {date_str:<11} {f['work_kind']:<9} {f['reason_class']:<22} {f['partition']:<15} {f['filename']}"
        )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Census done/ backlog items whose close dropped a release gate."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repository root (defaults to detected repo root)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit output formatted as JSON",
    )
    parser.add_argument(
        "--naive",
        action="store_true",
        help="Run naive per-item walk without shared carrier index (for timing benchmarks)",
    )

    args = parser.parse_args()
    root = args.repo.resolve() if args.repo else repo_root_dir()

    data = census(root, naive=args.naive)

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_human_report(data))

    return 0


if __name__ == "__main__":
    sys.exit(main())

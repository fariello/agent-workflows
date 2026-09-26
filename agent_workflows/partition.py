"""Pure dependency clustering, shard packing, and candidate selection for `aw partition`."""

from __future__ import annotations

import json
import math
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from agent_workflows import agent_schema
from agent_workflows import attention as _att
from agent_workflows import attention_contract
from agent_workflows import ipd_schema as _schema
from agent_workflows import plans as _plans
from agent_workflows import selectors as _selectors


@dataclass(frozen=True)
class SplitNote:
    """Diagnostic record for an oversized component split across multiple shards."""

    component_ids: List[str]
    shard_indexes: List[int]
    cut_edges: List[Tuple[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_ids": list(self.component_ids),
            "shard_indexes": list(self.shard_indexes),
            "cut_edges": [list(e) for e in self.cut_edges],
        }


@dataclass(frozen=True)
class Partition:
    """Result of partitioning items into balanced runner shards."""

    shards: List[List[_att.Item]]
    split_components: List[SplitNote]
    cycles: List[List[str]] = ()


def in_selection_edges(items: Sequence[_att.Item]) -> Dict[str, Set[str]]:
    """Dependency edges among the given items whose target is also in items.

    Returns a mapping from item id to set of prerequisite ids it depends on within
    the selection. Non-ipd targets, external dependencies, and self-edges are excluded.
    """
    present_ids = {it.id for it in items if it.id}
    edges: Dict[str, Set[str]] = {it.id: set() for it in items if it.id}

    for it in items:
        if not it.id:
            continue
        for token in it.item_dependencies or ():
            edge, err = _schema._parse_item_dependency_edge(token)
            if err or edge is None:
                continue
            if (
                edge.target_type == "ipd"
                and edge.id6 in present_ids
                and edge.id6 != it.id
            ):
                edges[it.id].add(edge.id6)

    return edges


def components(items: Sequence[_att.Item]) -> List[List[_att.Item]]:
    """Undirected weakly connected components over in-selection dependency edges.

    Isolated items are singletons. Returned in deterministic order: by size
    descending, then smallest id6. Items within each component are sorted by id6.
    """
    if not items:
        return []

    edges = in_selection_edges(items)
    present_items = [it for it in items if it.id]
    by_id = {it.id: it for it in present_items}

    # Build undirected adjacency list
    adj: Dict[str, Set[str]] = {it.id: set() for it in present_items}
    for u, targets in edges.items():
        for v in targets:
            adj[u].add(v)
            adj[v].add(u)

    visited: Set[str] = set()
    comps: List[List[_att.Item]] = []

    for it in sorted(present_items, key=lambda x: x.id):
        if it.id in visited:
            continue
        comp_ids: List[str] = []
        queue = [it.id]
        visited.add(it.id)
        while queue:
            curr = queue.pop(0)
            comp_ids.append(curr)
            for nbr in sorted(adj.get(curr, ())):
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
        comp_items = [by_id[cid] for cid in sorted(comp_ids)]
        comps.append(comp_items)

    comps.sort(key=lambda c: (-len(c), min(it.id for it in c)))
    return comps


def partition(items: Sequence[_att.Item], k: int) -> Partition:
    """Partition items into k balanced shards preserving dependency clusters.

    Pure and deterministic:
      1. k is clamped to max(1, min(k, len(items))); empty selection yields zero shards.
      2. Capacity cap = ceil(N / k).
      3. Components with size <= cap are placed whole, largest first, each into currently
         smallest shard (ties broken by lowest shard index).
      4. Components with size > cap are split: ordered by dependency depth ascending
         (ties by id6), placed one at a time into currently smallest shard; records SplitNote.
      5. Within each shard, items are ordered by dependency depth then id6.
      6. Cycles reported by dependency_depths are passed through.
    """
    if not items:
        return Partition(shards=[], split_components=[], cycles=[])

    n = len(items)
    clamped_k = max(1, min(k, n))
    cap = math.ceil(n / clamped_k)

    comps = components(items)
    depths, cycles = _att.dependency_depths(items)
    edges = in_selection_edges(items)

    shards: List[List[_att.Item]] = [[] for _ in range(clamped_k)]
    split_components: List[SplitNote] = []

    def _smallest_shard_idx() -> int:
        min_len = len(shards[0])
        min_idx = 0
        for i in range(1, clamped_k):
            if len(shards[i]) < min_len:
                min_len = len(shards[i])
                min_idx = i
        return min_idx

    for comp in comps:
        if len(comp) <= cap:
            target_idx = _smallest_shard_idx()
            shards[target_idx].extend(comp)
        else:
            sorted_comp = sorted(comp, key=lambda it: (depths.get(it.id, 0), it.id))
            comp_shard_indexes: Set[int] = set()
            item_to_shard: Dict[str, int] = {}
            for it in sorted_comp:
                target_idx = _smallest_shard_idx()
                shards[target_idx].append(it)
                comp_shard_indexes.add(target_idx)
                item_to_shard[it.id] = target_idx

            cut_edges: List[Tuple[str, str]] = []
            for it in sorted_comp:
                for prereq in sorted(edges.get(it.id, ())):
                    if (
                        prereq in item_to_shard
                        and item_to_shard[prereq] != item_to_shard[it.id]
                    ):
                        cut_edges.append((it.id, prereq))

            cut_edges.sort()
            split_components.append(
                SplitNote(
                    component_ids=[it.id for it in sorted_comp],
                    shard_indexes=sorted(comp_shard_indexes),
                    cut_edges=cut_edges,
                )
            )

    sorted_shards: List[List[_att.Item]] = []
    for s in shards:
        sorted_shards.append(sorted(s, key=lambda it: (depths.get(it.id, 0), it.id)))

    return Partition(
        shards=sorted_shards,
        split_components=split_components,
        cycles=cycles,
    )


def format_shard(
    run: str,
    ids: Sequence[str],
    *,
    profile: Optional[str] = None,
    model: Optional[str] = None,
    variant: Optional[str] = None,
) -> str:
    """Format shard IDs into an executable command line string."""
    if not ids:
        return ""

    if profile:
        if run in ("oc", "agy"):
            raise ValueError(f"--as cannot be combined with --run {run}")
        parts = ["aw", "run", "as", shlex.quote(profile)]
        parts.extend(shlex.quote(i) for i in ids)
        if model:
            parts.extend(["--model", shlex.quote(model)])
        if variant:
            parts.extend(["--variant", shlex.quote(variant)])
        return " ".join(parts)

    if run == "none":
        return " ".join(shlex.quote(i) for i in ids)
    elif run in ("oc", "agy"):
        parts = ["aw", run, "run"]
        parts.extend(shlex.quote(i) for i in ids)
        if model:
            parts.extend(["--model", shlex.quote(model)])
        if variant:
            parts.extend(["--variant", shlex.quote(variant)])
        return " ".join(parts)
    else:
        raise ValueError(f"Unknown runner format: {run!r}")


def collect(
    repo_root: Path,
    selectors: Sequence[str] = (),
    statuses: Sequence[str] = (),
    priorities: Sequence[str] = (),
    max_count: Optional[int] = None,
    stdin_ids: Optional[Sequence[str]] = None,
) -> Tuple[List[_att.Item], List[str]]:
    """Select candidate plan items honoring selectors, filters, stdin, and max count."""
    repo_root = Path(repo_root)

    items, _ = _att.scan(repo_root, type_filters=("plans",))
    # Exclude items in a terminal directory
    non_terminal = [
        it
        for it in items
        if _att._plan_disposition_from_rel(it.path) not in _plans.DIR_TERMINAL
    ]

    unknown_ids: List[str] = []

    if stdin_ids is not None:
        by_id = {it.id: it for it in non_terminal if it.id and it.tree == "plans"}
        candidates: List[_att.Item] = []
        for sid in stdin_ids:
            if sid in by_id:
                candidates.append(by_id[sid])
            else:
                unknown_ids.append(sid)
    else:
        candidates = non_terminal

        if selectors:
            resolved_paths = {
                p.resolve()
                for p in _selectors.resolve_selectors(
                    repo_root, "plans", list(selectors)
                )
            }
            candidates = [
                it
                for it in candidates
                if (repo_root / it.path).resolve() in resolved_paths
            ]

        if statuses:
            status_set = {s.lower() for s in statuses}
            candidates = [
                it
                for it in candidates
                if (getattr(it, "status", None) or it.native_status).lower()
                in status_set
            ]

        if priorities:
            norm_priorities = _att.parse_priority_filters(priorities)
            for p in norm_priorities:
                if p not in attention_contract.PRIORITY_ORDER:
                    raise ValueError(
                        f"invalid priority {p!r}, expected one of: "
                        f"{', '.join(attention_contract.PRIORITY_ORDER)}"
                    )
            candidates = [
                it
                for it in candidates
                if (it.priority or "").lower() in norm_priorities
            ]

    if max_count is not None and max_count > 0:
        depths, _ = _att.dependency_depths(candidates)
        candidates = sorted(candidates, key=lambda it: (depths.get(it.id, 0), it.id))[
            :max_count
        ]

    return candidates, unknown_ids


def run_partition(args: Any, term: Any, context: Any = None) -> int:
    """CLI execution entrypoint for 'aw partition'."""
    repo_root = Path(getattr(args, "dir", None) or Path.cwd())

    # Shards validation
    shards_val = getattr(args, "shards", 3)
    if shards_val is None:
        shards_val = 3
    if shards_val < 1:
        print(
            f"Error: --shards must be >= 1, got {shards_val}",
            file=sys.stderr,
        )
        return 2

    # Max count validation
    max_count = getattr(args, "max", None)
    if max_count is not None and max_count < 1:
        print(
            f"Error: --max must be >= 1, got {max_count}",
            file=sys.stderr,
        )
        return 2

    # Runner and profile validation
    profile = getattr(args, "as_profile", None)
    run_flag = getattr(args, "run", None)
    if profile and run_flag is not None:
        print(
            "Error: --as cannot be combined with --run",
            file=sys.stderr,
        )
        return 2

    runner = run_flag or "oc"
    model = getattr(args, "model", None)
    variant = getattr(args, "variant", None)
    is_json = bool(getattr(args, "json", False))
    is_agent = bool(getattr(args, "agent", False))

    # Stdin handling
    stdin_ids: Optional[List[str]] = None
    if getattr(args, "stdin", False):
        try:
            stdin_text = sys.stdin.read()
            stdin_ids = [tok.strip() for tok in stdin_text.split() if tok.strip()]
        except Exception as e:
            print(f"Error reading stdin: {e}", file=sys.stderr)
            return 2

    selectors = list(getattr(args, "selectors", []) or [])
    statuses = list(getattr(args, "status", []) or [])
    priorities = list(getattr(args, "priority", []) or [])

    try:
        candidates, unknown_ids = collect(
            repo_root=repo_root,
            selectors=selectors,
            statuses=statuses,
            priorities=priorities,
            max_count=max_count,
            stdin_ids=stdin_ids,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    for uid in unknown_ids:
        print(f"Unknown or non-plan id: {uid}", file=sys.stderr)

    part_res = partition(candidates, shards_val)

    # Format commands for non-empty shards
    commands: List[str] = []
    for shard in part_res.shards:
        shard_ids = [it.id for it in shard if it.id]
        if shard_ids:
            cmd = format_shard(
                run=runner,
                ids=shard_ids,
                profile=profile,
                model=model,
                variant=variant,
            )
            commands.append(cmd)

    # Write summary on stderr always
    shard_sizes = [len(s) for s in part_res.shards]
    print(
        f"Partitioned {len(candidates)} items across {len(part_res.shards)} shard(s): {shard_sizes}",
        file=sys.stderr,
    )
    if part_res.split_components:
        for sc in part_res.split_components:
            print(
                f"Split oversized component ({len(sc.component_ids)} items) across shards {sc.shard_indexes}: "
                f"{len(sc.cut_edges)} cut edge(s) {sc.cut_edges}",
                file=sys.stderr,
            )
    if part_res.cycles:
        print(f"Detected dependency cycles: {part_res.cycles}", file=sys.stderr)

    if is_agent:
        record = {
            "schema": agent_schema.SCHEMA_VERSION,
            "kind": "result",
            "cmd": "partition",
            "exit": 0,
            "outcome": "ok",
            "verified": True,
            "complete": True,
            "shards": [[it.id for it in s if it.id] for s in part_res.shards],
            "commands": commands,
            "split_components": [sc.to_dict() for sc in part_res.split_components],
            "cycles": part_res.cycles,
            "unknown": unknown_ids,
        }
        sys.stdout.write(agent_schema.render_jsonl_record(record))
        return 0

    if is_json:
        payload = {
            "shards": [[it.id for it in s if it.id] for s in part_res.shards],
            "commands": commands,
            "split_components": [sc.to_dict() for sc in part_res.split_components],
            "cycles": part_res.cycles,
            "unknown": unknown_ids,
        }
        print(json.dumps(payload, indent=2))
        return 0

    if not candidates:
        print("No matching plan items found to partition.", file=sys.stderr)
        return 0

    for cmd in commands:
        print(cmd)

    return 0

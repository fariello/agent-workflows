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
from agent_workflows import run_selection_policy as _run_selection_policy
from agent_workflows import selectors as _selectors
from agent_workflows import status_set as _status_set


def extract_creation_date(it: _att.Item) -> str:
    """Extract 8-digit creation date YYYYMMDD from an item's filename.

    Unparseable or missing dates return '99999999' so they sort after valid dates.
    """
    date, _, _, _ = _att._extract_identity_parts(it)
    if date and len(date) == 8 and date.isdigit():
        return date
    return "99999999"


def item_sort_key(
    it: _att.Item,
    depths: Dict[str, int],
    order_by: str = "depth",
) -> Tuple[Any, ...]:
    """Sort key for selection and shard placement preserving dependency depth."""
    depth = depths.get(it.id, 0)
    if order_by == "date":
        return (depth, extract_creation_date(it), it.id)
    return (depth, it.id)


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
    the selection. Same-type in-selection dependencies are recognized; cross-type
    targets, external dependencies, and self-edges are excluded.
    """
    by_id = {it.id: it for it in items if it.id}
    edges: Dict[str, Set[str]] = {it.id: set() for it in items if it.id}

    for it in items:
        if not it.id:
            continue
        for token in it.item_dependencies or ():
            edge, err = _schema._parse_item_dependency_edge(token)
            if err or edge is None:
                continue
            if edge.id6 in by_id and edge.id6 != it.id:
                target_item = by_id[edge.id6]
                if _status_set.canonical_type(
                    edge.target_type
                ) == _status_set.canonical_type(target_item.tree):
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


def partition(
    items: Sequence[_att.Item],
    k: int,
    order_by: str = "depth",
) -> Partition:
    """Partition items into k balanced shards preserving dependency clusters.

    Pure and deterministic:
      1. k is clamped to max(1, min(k, len(items))); empty selection yields zero shards.
      2. Capacity cap = ceil(N / k).
      3. Components with size <= cap are placed whole, largest first, each into currently
         smallest shard (ties broken by lowest shard index).
      4. Components with size > cap are split: ordered by dependency depth ascending
         (ties by id6 or date depending on order_by), placed one at a time into currently
         smallest shard; records SplitNote.
      5. Within each shard, items are ordered by dependency depth then id6/date.
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

    comps.sort(
        key=lambda c: (-len(c), min(item_sort_key(it, depths, order_by) for it in c))
    )

    for comp in comps:
        if len(comp) <= cap:
            target_idx = _smallest_shard_idx()
            shards[target_idx].extend(comp)
        else:
            sorted_comp = sorted(
                comp, key=lambda it: item_sort_key(it, depths, order_by)
            )
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
        sorted_shards.append(
            sorted(s, key=lambda it: item_sort_key(it, depths, order_by))
        )

    return Partition(
        shards=sorted_shards,
        split_components=split_components,
        cycles=cycles,
    )


def format_shard(
    run: str,
    ids: Sequence[str],
    *,
    action: Optional[str] = None,
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
        if action in ("plan", "review"):
            parts.extend(["--action", action])
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
        if action in ("plan", "review"):
            parts.extend(["--action", action])
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
    artifact_type: str = "plans",
    selectors: Sequence[str] = (),
    statuses: Sequence[str] = (),
    priorities: Sequence[str] = (),
    max_count: Optional[int] = None,
    stdin_ids: Optional[Sequence[str]] = None,
    order_by: Optional[str] = None,
    action: Optional[str] = None,
    require_homogeneous_action: bool = False,
) -> List[_att.Item]:
    """Select candidate items honoring artifact type, selectors, filters, action, and ordering.

    Raises ValueError on an unrecognized, ambiguous, wrong-type, or ineligible selector.
    """
    repo_root = Path(repo_root)

    canon_type = _status_set.canonical_type(artifact_type)
    if canon_type not in ("plans", "backlog", "specs"):
        raise ValueError(
            f"unsupported artifact type {artifact_type!r}, expected one of: 'plans', 'backlog', 'specs'"
        )
    artifact_type = canon_type

    if statuses:
        valid_statuses = _status_set.TYPE_STATUSES.get(artifact_type, set())
        for s in statuses:
            if s.lower() not in valid_statuses:
                sorted_valid = ", ".join(f"'{st}'" for st in sorted(valid_statuses))
                raise ValueError(
                    f"status {s!r} is not valid for artifact type {artifact_type!r}. Valid statuses: {sorted_valid}"
                )

    norm_priorities = ()
    if priorities:
        norm_priorities = _att.parse_priority_filters(priorities)
        for p in norm_priorities:
            if p not in attention_contract.PRIORITY_ORDER:
                raise ValueError(
                    f"invalid priority {p!r}, expected one of: "
                    f"{', '.join(attention_contract.PRIORITY_ORDER)}"
                )

    items, _ = _att.scan(repo_root, type_filters=(artifact_type,))
    spec_type = _run_selection_policy.SPEC_TYPE_BY_RESOLVER_TYPE.get(
        artifact_type, artifact_type
    )

    def _is_runnable(it: _att.Item) -> bool:
        if (
            it.tree == "plans"
            and _att._plan_disposition_from_rel(it.path) in _plans.DIR_TERMINAL
        ):
            return False
        st = getattr(it, "status", None) or it.native_status
        act = _run_selection_policy.action_for_status(spec_type, st)
        return act not in (
            _run_selection_policy.ACTION_SKIP,
            _run_selection_policy.ACTION_UNDETERMINED,
        )

    by_path = {(repo_root / it.path).resolve(): it for it in items}

    tokens: Optional[List[str]] = None
    if stdin_ids is not None:
        tokens = list(stdin_ids)
    elif selectors:
        tokens = list(selectors)

    other_primary_types = [
        t
        for t in (
            "plans",
            "backlog",
            "specs",
            "prompts",
            "research",
            "releases",
            "walkthroughs",
        )
        if t != artifact_type
    ]

    raw_candidates: List[_att.Item] = []
    if tokens is not None:
        for tok in tokens:
            res = _selectors.resolve(repo_root, artifact_type, tok)
            if not res.is_match:
                matched_other = None
                for other_t in other_primary_types:
                    other_res = _selectors.resolve(repo_root, other_t, tok)
                    if other_res.is_match:
                        matched_other = other_t
                        break
                if matched_other:
                    raise ValueError(
                        f"selector {tok!r} belongs to {matched_other!r}, not {artifact_type!r}"
                    )
                raise ValueError(
                    f"unknown selector {tok!r} for artifact type {artifact_type!r}"
                )

            if res.is_ambiguous:
                if res.kind in _selectors.UNIQUE_KINDS:
                    raise ValueError(
                        f"selector {tok!r} is a {res.kind} collision matching multiple files"
                    )
                if res.kind == _selectors.MATCH_SUBSTRING:
                    raise ValueError(
                        f"selector {tok!r} is ambiguous, matching multiple files via substring"
                    )

            matched_items: List[_att.Item] = []
            for p in res.paths:
                it = by_path.get(p.resolve())
                if it is not None:
                    matched_items.append(it)

            if not matched_items:
                raise ValueError(
                    f"unknown selector {tok!r} for artifact type {artifact_type!r}"
                )

            for it in matched_items:
                if not _is_runnable(it):
                    st = getattr(it, "status", None) or it.native_status
                    raise ValueError(
                        f"item {it.id!r} with status {st!r} is ineligible for runner dispatch (has no runnable next action)"
                    )
                raw_candidates.append(it)
    else:
        raw_candidates = [it for it in items if _is_runnable(it)]

    seen_ids: Set[str] = set()
    candidates: List[_att.Item] = []
    for it in raw_candidates:
        if it.id and it.id not in seen_ids:
            seen_ids.add(it.id)
            candidates.append(it)

    if statuses:
        status_set = {s.lower() for s in statuses}
        candidates = [
            it
            for it in candidates
            if (getattr(it, "status", None) or it.native_status).lower() in status_set
        ]

    if priorities:
        candidates = [
            it for it in candidates if (it.priority or "").lower() in norm_priorities
        ]

    if candidates:
        distinct_actions = {
            _run_selection_policy.action_for_status(
                spec_type, getattr(it, "status", None) or it.native_status
            )
            for it in candidates
        }
        if action is not None:
            for it in candidates:
                it_act = _run_selection_policy.action_for_status(
                    spec_type, getattr(it, "status", None) or it.native_status
                )
                if it_act != action:
                    raise ValueError(
                        f"item {it.id!r} requires action {it_act!r}, which conflicts with requested --action {action!r}"
                    )
        elif require_homogeneous_action:
            if len(distinct_actions) > 1:
                actions_str = ", ".join(sorted(distinct_actions))
                raise ValueError(
                    f"selection contains mixed actions ({actions_str}); filter by -s or --action to produce a homogeneous queue"
                )

    effective_order_by = order_by or ("depth" if artifact_type == "plans" else "date")
    if max_count is not None and max_count > 0:
        depths, _ = _att.dependency_depths(candidates)
        if effective_order_by == "date":
            candidates = sorted(
                candidates,
                key=lambda it: (depths.get(it.id, 0), extract_creation_date(it), it.id),
            )[:max_count]
        else:
            candidates = sorted(
                candidates,
                key=lambda it: (depths.get(it.id, 0), it.id),
            )[:max_count]

    return candidates


def run_partition(args: Any, term: Any, context: Any = None) -> int:
    """CLI execution entrypoint for 'aw partition'."""
    repo_root = Path(getattr(args, "dir", None) or Path.cwd())

    artifact_type = getattr(args, "artifact_type", None)
    if not artifact_type:
        print("Error: -t/--type/--tree is required", file=sys.stderr)
        return 2

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

    runner = "as" if profile else (run_flag or "oc")
    model = getattr(args, "model", None)
    variant = getattr(args, "variant", None)
    action_flag = getattr(args, "action", None)
    order_by_flag = getattr(args, "order_by", None)
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
        candidates = collect(
            repo_root=repo_root,
            artifact_type=artifact_type,
            selectors=selectors,
            statuses=statuses,
            priorities=priorities,
            max_count=max_count,
            stdin_ids=stdin_ids,
            order_by=order_by_flag,
            action=action_flag,
            require_homogeneous_action=True,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    canon_type = _status_set.canonical_type(artifact_type) or artifact_type
    effective_order_by = order_by_flag or ("depth" if canon_type == "plans" else "date")
    part_res = partition(candidates, shards_val, order_by=effective_order_by)

    # Derive effective action for non-empty candidates
    effective_action: Optional[str] = None
    if candidates:
        if action_flag is not None:
            effective_action = action_flag
        else:
            spec_type = _run_selection_policy.SPEC_TYPE_BY_RESOLVER_TYPE.get(
                canon_type, canon_type
            )
            distinct_actions = {
                _run_selection_policy.action_for_status(
                    spec_type, getattr(it, "status", None) or it.native_status
                )
                for it in candidates
            }
            if len(distinct_actions) == 1:
                effective_action = next(iter(distinct_actions))

    # Format commands for non-empty shards
    commands: List[str] = []
    for shard in part_res.shards:
        shard_ids = [it.id for it in shard if it.id]
        if shard_ids:
            cmd = format_shard(
                run=runner,
                ids=shard_ids,
                action=effective_action,
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

    if is_agent or is_json:
        redacted_commands = [agent_schema.redact_home_paths(cmd) for cmd in commands]

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
            "commands": redacted_commands,
            "split_components": [sc.to_dict() for sc in part_res.split_components],
            "cycles": part_res.cycles,
        }
        sys.stdout.write(agent_schema.render_jsonl_record(record))
        return 0

    if is_json:
        payload = {
            "shards": [[it.id for it in s if it.id] for s in part_res.shards],
            "commands": redacted_commands,
            "split_components": [sc.to_dict() for sc in part_res.split_components],
            "cycles": part_res.cycles,
        }
        print(json.dumps(payload, indent=2))
        return 0

    if not candidates:
        print(f"No matching {canon_type} items found to partition.", file=sys.stderr)
        return 0

    for cmd in commands:
        print(cmd)

    return 0

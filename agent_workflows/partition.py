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
from agent_workflows.term import Term


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


@dataclass(frozen=True)
class BlockedMember:
    """One member of a Set blocking the batch from finishing."""

    id6: str
    status: str
    cause: str
    fix: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id6": self.id6,
            "status": self.status,
            "cause": self.cause,
            "fix": agent_schema.redact_home_paths(self.fix),
        }


@dataclass(frozen=True)
class SetClassification:
    """Classification of a Set and its members for partition batch safety."""

    setid: str
    orchestrator_id: str
    finished: List[str]
    runnable: List[str]
    blocked: List[BlockedMember]
    is_completeable: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "setid": self.setid,
            "orchestrator": self.orchestrator_id,
            "blocked": [b.to_dict() for b in self.blocked],
        }


def _is_finished_plan(it: _att.Item, repo_root: Path) -> bool:
    """True if a plan item is in a terminal disposition directory or terminal status."""
    if it.tree != "plans":
        return False
    if _att._plan_disposition_from_rel(it.path) in _plans.DIR_TERMINAL:
        return True
    from agent_workflows import runner_shared

    st = (getattr(it, "status", None) or it.native_status or "").lower()
    return st in runner_shared.set_retirement_terminal_statuses()


def is_edge_satisfied_on_disk(
    repo_root: Path,
    edge: Any,
    consumer_action: str = "execute",
) -> Tuple[bool, str]:
    """Check if a declared ItemDependency edge is satisfied against current disk state."""
    from agent_workflows import runner_shared

    state = {"repo": repo_root, "queue": []}
    consumer_item = {"action": consumer_action}
    try:
        satisfied, reason = runner_shared.edge_satisfied(edge, consumer_item, state, {})
        return bool(satisfied), reason
    except Exception as exc:
        tok = getattr(edge, "canonical", lambda: str(edge))()
        return False, f"{tok}: {exc}"


def expand_candidates_with_dependencies(
    repo_root: Path,
    candidates: Sequence[_att.Item],
    artifact_type: str = "plans",
    statuses: Sequence[str] = (),
    action: Optional[str] = None,
    include_active: bool = False,
    run_map: Optional[Dict[str, str]] = None,
) -> List[_att.Item]:
    """Expand candidates with declared prerequisites that are not yet executed on disk.

    For plans, pulls in prerequisite Sets (or individual plans) that can satisfy declared
    Item-Dependencies edges.
    """
    from agent_workflows import runner_shared

    terminal_statuses = runner_shared.set_retirement_terminal_statuses()
    all_items, _ = _att.scan(repo_root, type_filters=(artifact_type,))
    by_id = {it.id: it for it in all_items if it.id}

    selection: List[_att.Item] = list(candidates)
    in_selection_ids: Set[str] = {it.id for it in selection if it.id}
    visited_ids: Set[str] = set()
    frontier: List[str] = [it.id for it in selection if it.id]

    while frontier:
        cid = frontier.pop(0)
        if cid in visited_ids:
            continue
        visited_ids.add(cid)

        it = by_id.get(cid)
        if not it:
            continue

        for tok in it.item_dependencies or ():
            edge = runner_shared.parse_dependency_token(tok)
            if edge is None:
                continue

            sat_disk, _ = is_edge_satisfied_on_disk(
                repo_root, edge, consumer_action=action or "execute"
            )
            if sat_disk:
                continue

            tgt_id = getattr(edge, "id6", "")
            if not tgt_id or tgt_id not in by_id:
                continue

            tgt_it = by_id[tgt_id]
            if _is_finished_plan(tgt_it, repo_root):
                continue

            tgt_p = repo_root / tgt_it.path
            sid = None
            if tgt_p.exists():
                try:
                    sid = _selectors._read_setid(tgt_p.read_text(encoding="utf-8"))
                except Exception:
                    pass

            to_add: List[_att.Item] = []
            if sid:
                mem = runner_shared.read_set_membership(repo_root, sid)
                for m in mem.members:
                    if (m.status or "").lower() in terminal_statuses:
                        continue
                    if m.id6 in by_id and m.id6 not in in_selection_ids:
                        m_it = by_id[m.id6]
                        if not _is_finished_plan(m_it, repo_root):
                            to_add.append(m_it)
            else:
                if tgt_id not in in_selection_ids:
                    to_add.append(tgt_it)

            for item in to_add:
                if item.id not in in_selection_ids:
                    in_selection_ids.add(item.id)
                    selection.append(item)
                    frontier.append(item.id)

    return selection


def apply_max_count(
    candidates: List[_att.Item],
    max_count: Optional[int],
    order_by: str = "depth",
) -> List[_att.Item]:
    """Truncate candidates preserving dependency depth and requested ordering."""
    if max_count is None or max_count <= 0:
        return list(candidates)
    depths, _ = _att.dependency_depths(candidates)
    if order_by == "date":
        return sorted(
            candidates,
            key=lambda it: (depths.get(it.id, 0), extract_creation_date(it), it.id),
        )[:max_count]
    return sorted(
        candidates,
        key=lambda it: (depths.get(it.id, 0), it.id),
    )[:max_count]


def is_active_item(
    it: _att.Item,
    run_map: Optional[Dict[str, str]],
) -> bool:
    """Return True if an item is currently active in a live runner session."""
    if not run_map:
        return False
    st = _att._item_run_status(it, run_map)
    if not st and it.id and it.id in run_map:
        st = run_map[it.id]
    st = (st or "").lower()
    return bool(st and st != "-")


def _is_active_member(
    m: Any,
    repo_root: Path,
    run_map: Optional[Dict[str, str]],
) -> bool:
    """Return True if a SetMember is currently active in a live runner session."""
    if not run_map:
        return False
    path_name = m.path.name if m.path else ""
    rel_path = ""
    if m.path:
        try:
            rel_path = str(m.path.resolve().relative_to(repo_root.resolve()))
        except Exception:
            rel_path = str(m.path)
    st = (
        run_map.get(m.id6)
        or (run_map.get(rel_path) if rel_path else None)
        or (run_map.get(path_name) if path_name else None)
    )
    st = (st or "").lower()
    return bool(st and st != "-")


def classify_sets(
    repo_root: Path,
    candidates: Sequence[_att.Item],
    pre_max_candidates: Sequence[_att.Item],
    max_count: Optional[int] = None,
    action_flag: Optional[str] = None,
    include_active: bool = False,
    run_map: Optional[Dict[str, str]] = None,
) -> Dict[str, SetClassification]:
    """Classify every distinct Set that has a selected member and an orchestrator on disk."""
    if not include_active and run_map is None:
        run_map = _att.get_active_runs_map(repo_root)

    from agent_workflows import runner_shared

    terminal_statuses = runner_shared.set_retirement_terminal_statuses()

    distinct_setids: Set[str] = set()
    for it in pre_max_candidates:
        p = repo_root / it.path
        if p.exists():
            try:
                sid = _selectors._read_setid(p.read_text(encoding="utf-8"))
                if sid:
                    distinct_setids.add(sid)
            except Exception:
                pass

    runnable_ids = {it.id for it in candidates if it.id}
    pre_max_ids = {it.id for it in pre_max_candidates if it.id}
    pre_max_id_list = [it.id for it in pre_max_candidates if it.id]

    classifications: Dict[str, SetClassification] = {}

    for setid in sorted(distinct_setids):
        membership = runner_shared.read_set_membership(repo_root, setid)
        if membership.orchestrator is None:
            continue

        orch_status = (membership.orchestrator.status or "").lower()
        is_orch_terminal = orch_status in terminal_statuses
        if is_orch_terminal:
            set_unfinished_in_candidates = any(
                m.id6 in pre_max_ids
                and (m.status or "").lower() not in terminal_statuses
                for m in membership.members
            )
            if not set_unfinished_in_candidates:
                continue

        orch_action = _run_selection_policy.action_for_status("ipd", orch_status)
        batch_action = action_flag
        if not batch_action:
            if orch_action not in (
                _run_selection_policy.ACTION_SKIP,
                _run_selection_policy.ACTION_UNDETERMINED,
            ):
                batch_action = orch_action
            else:
                set_member_ids = {m.id6 for m in membership.members}
                candidate_actions = [
                    _run_selection_policy.action_for_status(
                        "ipd", getattr(it, "status", None) or it.native_status
                    )
                    for it in candidates
                    if it.id in set_member_ids
                ]
                runnable_cand_actions = [
                    a
                    for a in candidate_actions
                    if a
                    not in (
                        _run_selection_policy.ACTION_SKIP,
                        _run_selection_policy.ACTION_UNDETERMINED,
                    )
                ]
                if runnable_cand_actions:
                    batch_action = runnable_cand_actions[0]
                else:
                    batch_action = orch_action

        finished: List[str] = []
        runnable: List[str] = []
        blocked: List[BlockedMember] = []

        if is_orch_terminal:
            finished.append(membership.orchestrator.id6)

        for m in membership.members:
            if is_orch_terminal and m.id6 == membership.orchestrator.id6:
                continue

            m_status = (m.status or "").lower()
            if m_status in terminal_statuses:
                finished.append(m.id6)
                continue

            m_action = _run_selection_policy.action_for_status("ipd", m_status)
            if m_action != batch_action:
                if m_status == "to-review":
                    blocked.append(
                        BlockedMember(
                            id6=m.id6,
                            status=m.status,
                            cause="needs-review",
                            fix=f"/plan-review {m.id6}, then aw ipd set approved {m.id6} --by-human",
                        )
                    )
                elif m_status == "reviewed":
                    blocked.append(
                        BlockedMember(
                            id6=m.id6,
                            status=m.status,
                            cause="needs-approval",
                            fix=f"aw ipd set approved {m.id6} --by-human",
                        )
                    )
                elif m_action not in (
                    _run_selection_policy.ACTION_SKIP,
                    _run_selection_policy.ACTION_UNDETERMINED,
                ):
                    blocked.append(
                        BlockedMember(
                            id6=m.id6,
                            status=m.status,
                            cause=f"needs-{m_action}",
                            fix=f"see aw ipd board {m.id6}",
                        )
                    )
                else:
                    blocked.append(
                        BlockedMember(
                            id6=m.id6,
                            status=m.status,
                            cause=f"status-{m_status}",
                            fix=f"see aw ipd board {m.id6}",
                        )
                    )
            elif m.id6 in runnable_ids:
                runnable.append(m.id6)
            elif m.id6 in pre_max_ids:
                set_unfinished_in_pre_max = [
                    mid
                    for mid in pre_max_id_list
                    if any(
                        sm.id6 == mid
                        and (sm.status or "").lower() not in terminal_statuses
                        for sm in membership.members
                    )
                ]
                if set_unfinished_in_pre_max:
                    last_idx = max(
                        pre_max_id_list.index(mid) for mid in set_unfinished_in_pre_max
                    )
                    computed_n = last_idx + 1
                else:
                    computed_n = (max_count or 0) + 1
                blocked.append(
                    BlockedMember(
                        id6=m.id6,
                        status=m.status,
                        cause="excluded-by-max",
                        fix=f"raise --max to {computed_n} or select the Set by its setid",
                    )
                )
            elif not include_active and _is_active_member(m, repo_root, run_map):
                blocked.append(
                    BlockedMember(
                        id6=m.id6,
                        status=m.status,
                        cause="already-running",
                        fix=f"wait for active run to finish {m.id6}",
                    )
                )
            elif not is_orch_terminal:
                blocked.append(
                    BlockedMember(
                        id6=m.id6,
                        status=m.status,
                        cause="not-selected",
                        fix=f"add {m.id6} to the selection, or select the Set by its setid {setid}",
                    )
                )

        if not is_orch_terminal:
            orch_p = membership.orchestrator.path
            if not orch_p.exists():
                orch_p = repo_root / orch_p
            orch_text = orch_p.read_text(encoding="utf-8") if orch_p.exists() else ""

            if len(membership.children) == 0:
                if not any(
                    b.id6 == membership.orchestrator.id6
                    and b.cause == "orchestrator-cannot-retire"
                    for b in blocked
                ):
                    blocked.append(
                        BlockedMember(
                            id6=membership.orchestrator.id6,
                            status=membership.orchestrator.status,
                            cause="orchestrator-cannot-retire",
                            fix=f"add a child plan to Set {setid}",
                        )
                    )
            else:
                unauthored, parsed = runner_shared.find_unauthored_child_rows(
                    orch_text, membership
                )
                if not parsed:
                    if not any(
                        b.id6 == membership.orchestrator.id6
                        and b.cause == "orchestrator-cannot-retire"
                        for b in blocked
                    ):
                        blocked.append(
                            BlockedMember(
                                id6=membership.orchestrator.id6,
                                status=membership.orchestrator.status,
                                cause="orchestrator-cannot-retire",
                                fix=f"fix child table in orchestrator {membership.orchestrator.id6}",
                            )
                        )
                elif unauthored:
                    tokens_str = ", ".join(unauthored)
                    if not any(
                        b.id6 == membership.orchestrator.id6
                        and b.cause == "orchestrator-cannot-retire"
                        for b in blocked
                    ):
                        blocked.append(
                            BlockedMember(
                                id6=membership.orchestrator.id6,
                                status=membership.orchestrator.status,
                                cause="orchestrator-cannot-retire",
                                fix=f"author the missing child for row {tokens_str}",
                            )
                        )

        is_completeable = len(blocked) == 0
        classifications[setid] = SetClassification(
            setid=setid,
            orchestrator_id=membership.orchestrator.id6,
            finished=finished,
            runnable=runnable,
            blocked=blocked,
            is_completeable=is_completeable,
        )

    # Iterative dependency verification across all runnable candidates
    cand_by_id = {it.id: it for it in pre_max_candidates if it.id}
    members_by_id: Dict[str, Tuple[str, Any]] = {}
    member_edges: Dict[str, List[Any]] = {}

    for setid, cs in classifications.items():
        membership = runner_shared.read_set_membership(repo_root, setid)
        for m in membership.members:
            if m.id6 in cs.runnable:
                members_by_id[m.id6] = (setid, m)
                deps: List[str] = []
                if (
                    m.id6 in cand_by_id
                    and cand_by_id[m.id6].item_dependencies is not None
                ):
                    deps = list(cand_by_id[m.id6].item_dependencies or ())
                elif m.path:
                    mp = m.path if m.path.is_absolute() else (repo_root / m.path)
                    if mp.exists():
                        try:
                            raw_deps, _ = runner_shared._read_item_dependencies(
                                mp.read_text(encoding="utf-8")
                            )
                            deps = raw_deps or []
                        except Exception:
                            pass
                parsed_edges: List[Any] = []
                for tok in deps:
                    edge = runner_shared.parse_dependency_token(tok)
                    if edge is not None:
                        parsed_edges.append(edge)
                member_edges[m.id6] = parsed_edges

    active_runnable_ids: Set[str] = {
        mid for cs in classifications.values() for mid in cs.runnable
    }
    unsatisfied_targets: Dict[str, List[str]] = {}

    changed = True
    while changed:
        changed = False
        for mid in list(active_runnable_ids):
            edges = member_edges.get(mid, [])
            for edge in edges:
                sat_disk, _ = is_edge_satisfied_on_disk(
                    repo_root, edge, consumer_action=action_flag or "execute"
                )
                if sat_disk:
                    continue

                target_id = getattr(edge, "id6", "")
                can_satisfy = False
                if edge.kind == "executed" or (
                    edge.kind == "state" and getattr(edge, "target_type", "") == "ipd"
                ):
                    if target_id and target_id in active_runnable_ids:
                        can_satisfy = True

                if not can_satisfy:
                    active_runnable_ids.remove(mid)
                    changed = True
                    if target_id:
                        unsatisfied_targets.setdefault(mid, []).append(target_id)
                    break

    for setid, cs in list(classifications.items()):
        new_runnable = list(cs.runnable)
        new_blocked = list(cs.blocked)
        for mid in list(new_runnable):
            if mid not in active_runnable_ids:
                new_runnable.remove(mid)
                m_info = members_by_id.get(mid)
                m_status = m_info[1].status if m_info else "approved"
                targets = unsatisfied_targets.get(mid, [])
                if targets:
                    targets_str = ", ".join(sorted(set(targets)))
                    fix_clause = f"run with --with-dependencies, or execute prerequisite {targets_str} first"
                else:
                    fix_clause = "satisfy declared item-dependencies before scheduling"
                new_blocked.append(
                    BlockedMember(
                        id6=mid,
                        status=m_status,
                        cause="unsatisfied-dependency",
                        fix=fix_clause,
                    )
                )
        classifications[setid] = SetClassification(
            setid=cs.setid,
            orchestrator_id=cs.orchestrator_id,
            finished=cs.finished,
            runnable=new_runnable,
            blocked=new_blocked,
            is_completeable=len(new_blocked) == 0,
        )

    return classifications


def render_set_block(
    cs: SetClassification,
    term: Term,
    is_warning: bool,
) -> List[str]:
    """Render human diagnostic lines for an incomplete Set (error or warning)."""
    lines: List[str] = []
    if is_warning:
        label = term.colorize("warning:", "yellow", "bold")
        orch_bold = term.colorize(cs.orchestrator_id, "bold")
        if cs.orchestrator_id in cs.finished:
            lines.append(
                f"{label} Set '{cs.setid}' cannot finish in this batch; orchestrator {orch_bold} is already executed."
            )
        else:
            lines.append(
                f"{label} Set '{cs.setid}' cannot finish in this batch; held back orchestrator {orch_bold}."
            )
    else:
        label = term.colorize("error:", "red", "bold")
        lines.append(
            f"{label} Set '{cs.setid}' cannot finish in this batch, so nothing was scheduled."
        )

    # Blocked line
    blocked_items: List[str] = []
    for b in cs.blocked:
        b_id = term.colorize(b.id6, "bold")
        cause_text = b.cause.replace("-", " ")
        blocked_items.append(f"{b_id} ({b.status}, {cause_text})")
    lines.append(f"  blocked: {', '.join(blocked_items)}")

    # Fix line
    to_review = [b for b in cs.blocked if b.cause == "needs-review"]
    reviewed = [b for b in cs.blocked if b.cause == "needs-approval"]
    not_sel = [b for b in cs.blocked if b.cause == "not-selected"]
    max_excl = [b for b in cs.blocked if b.cause == "excluded-by-max"]
    orch_ret = [b for b in cs.blocked if b.cause == "orchestrator-cannot-retire"]
    running = [b for b in cs.blocked if b.cause == "already-running"]
    unsatisfied = [b for b in cs.blocked if b.cause == "unsatisfied-dependency"]
    other = [
        b
        for b in cs.blocked
        if b
        not in to_review
        + reviewed
        + not_sel
        + max_excl
        + orch_ret
        + running
        + unsatisfied
    ]

    fix_clauses: List[str] = []
    if to_review:
        ids_str = " ".join(b.id6 for b in to_review)
        if len(to_review) == 1:
            cmd1 = term.colorize(f"/plan-review {ids_str}", "cyan")
            cmd2 = term.colorize(f"aw ipd set approved {ids_str} --by-human", "cyan")
            fix_clauses.append(f"{cmd1}, then {cmd2}")
        else:
            cmd1 = term.colorize(f"/plan-review {ids_str}", "cyan")
            cmd2 = term.colorize(
                "aw ipd set approved <id6> --by-human for each", "cyan"
            )
            fix_clauses.append(f"{cmd1}, then {cmd2}")

    if reviewed:
        ids_str = " ".join(b.id6 for b in reviewed)
        if len(reviewed) == 1:
            cmd = term.colorize(f"aw ipd set approved {ids_str} --by-human", "cyan")
            fix_clauses.append(cmd)
        else:
            cmd = term.colorize("aw ipd set approved <id6> --by-human for each", "cyan")
            fix_clauses.append(cmd)

    if not_sel:
        ids_str = " ".join(b.id6 for b in not_sel)
        fix_clauses.append(
            f"add {ids_str} to the selection, or select the Set by its setid {cs.setid}"
        )

    if max_excl:
        fix_clauses.append(max_excl[0].fix)

    if orch_ret:
        for b in orch_ret:
            fix_clauses.append(b.fix)

    if running:
        ids_str = " ".join(b.id6 for b in running)
        fix_clauses.append(f"wait for active run to finish {ids_str}")

    if unsatisfied:
        for b in unsatisfied:
            if b.fix not in fix_clauses:
                fix_clauses.append(b.fix)

    if other:
        for b in other:
            fix_clauses.append(b.fix)

    base_fix = "; ".join(fix_clauses)
    if is_warning:
        lines.append(f"  fix:     {base_fix}")
    else:
        has_runnable_children = any(cid != cs.orchestrator_id for cid in cs.runnable)
        if has_runnable_children:
            flag_cyan = term.colorize("--allow-partial-sets", "cyan")
            if cs.orchestrator_id in cs.finished:
                partial_clause = (
                    f"or rerun with {flag_cyan} to run the ready plans now."
                )
            else:
                orch_bold = term.colorize(cs.orchestrator_id, "bold")
                partial_clause = (
                    f"or rerun with {flag_cyan} to run the ready plans now and leave the\n"
                    f"           orchestrator {orch_bold} for a later batch."
                )
            if base_fix:
                full_fix = f"{base_fix};\n           {partial_clause}"
            else:
                full_fix = partial_clause
        else:
            full_fix = base_fix
        lines.append(f"  fix:     {full_fix}")

    return lines


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


def components(
    items: Sequence[_att.Item],
    extra_edges: Optional[Sequence[Tuple[str, str]]] = None,
) -> List[List[_att.Item]]:
    """Undirected weakly connected components over in-selection dependency edges and optional extra edges.

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

    if extra_edges:
        for u, v in extra_edges:
            if u in adj and v in adj:
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
    extra_edges: Optional[Sequence[Tuple[str, str]]] = None,
    orchestrator_ids: Optional[Set[str]] = None,
    set_by_item: Optional[Dict[str, str]] = None,
) -> Partition:
    """Partition items into k balanced shards preserving dependency clusters.

    Pure and deterministic:
      1. k is clamped to max(1, min(k, len(items))); empty selection yields zero shards.
      2. Capacity cap = ceil(N / k).
      3. Components with size <= cap are placed whole, largest first, each into currently
         smallest shard (ties broken by lowest shard index).
      4. Components with size > cap are split: ordered by dependency depth ascending
         (ties by id6 or date depending on order_by), placed one at a time into currently
         smallest shard; records SplitNote. However, a component containing Set edges
         is never split: it goes whole into the currently smallest shard, prints a note to
         stderr, and is omitted from split_components.
      5. Within each shard, items are ordered by dependency depth then orchestrator last then id6/date.
      6. Cycles reported by dependency_depths are passed through.
    """
    if not items:
        return Partition(shards=[], split_components=[], cycles=[])

    n = len(items)
    clamped_k = max(1, min(k, n))
    cap = math.ceil(n / clamped_k)

    comps = components(items, extra_edges=extra_edges)
    depths, cycles = _att.dependency_depths(items)
    edges = in_selection_edges(items)

    set_nodes: Set[str] = set()
    if extra_edges:
        for u, v in extra_edges:
            set_nodes.add(u)
            set_nodes.add(v)

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
        has_set_edges = bool(set_nodes and any(it.id in set_nodes for it in comp))
        if len(comp) <= cap or has_set_edges:
            target_idx = _smallest_shard_idx()
            shards[target_idx].extend(comp)
            if len(comp) > cap and has_set_edges:
                set_id = None
                if set_by_item:
                    for it in comp:
                        if it.id in set_by_item:
                            set_id = set_by_item[it.id]
                            break
                if not set_id:
                    _, set_id, _, _ = _att._extract_identity_parts(comp[0])
                print(
                    f"note: Set '{set_id}' ({len(comp)} plans) kept whole in shard {target_idx}, exceeding the even share of {cap}",
                    file=sys.stderr,
                )
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

    def _shard_item_sort_key(it: _att.Item) -> Tuple[Any, ...]:
        depth = depths.get(it.id, 0)
        is_orch = 1 if (orchestrator_ids and it.id in orchestrator_ids) else 0
        if order_by == "date":
            return (depth, is_orch, extract_creation_date(it), it.id)
        return (depth, is_orch, it.id)

    sorted_shards: List[List[_att.Item]] = []
    for s in shards:
        sorted_shards.append(sorted(s, key=_shard_item_sort_key))

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


def _make_err_term(term: Optional[Term] = None) -> Term:
    """Construct an error Term bound to sys.stderr honoring any color/depth override on term."""
    if term is not None and getattr(term, "color", None) is not None:
        depth = term.lifecycle_depth() if getattr(term, "color", False) else None
        return Term(stream=sys.stderr, color=term.color, depth=depth)
    return Term(stream=sys.stderr)


def collect(
    repo_root: Path,
    artifact_type: str = "plans",
    selectors: Sequence[str] = (),
    statuses: Sequence[str] = (),
    statuses_not: Sequence[str] = (),
    priorities: Sequence[str] = (),
    max_count: Optional[int] = None,
    stdin_ids: Optional[Sequence[str]] = None,
    order_by: Optional[str] = None,
    action: Optional[str] = None,
    require_homogeneous_action: bool = False,
    include_active: bool = False,
    run_map: Optional[Dict[str, str]] = None,
    skip_ineligible: bool = False,
    term: Optional[Term] = None,
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

    if statuses_not:
        valid_statuses = _status_set.TYPE_STATUSES.get(artifact_type, set())
        for s in statuses_not:
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
    ineligible_items: List[Tuple[_att.Item, str]] = []
    seen_ineligible_ids: Set[str] = set()

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
                    if res.kind == _selectors.MATCH_SETID and _is_finished_plan(
                        it, repo_root
                    ):
                        continue
                    st = getattr(it, "status", None) or it.native_status
                    if it.id not in seen_ineligible_ids:
                        seen_ineligible_ids.add(it.id)
                        ineligible_items.append((it, st))
                    continue
                raw_candidates.append(it)
    else:
        raw_candidates = [it for it in items if _is_runnable(it)]

    if ineligible_items:
        err_term = _make_err_term(term)

        def _expected_status_for(it: _att.Item) -> str:
            if canon_type == "plans":
                return "'to-review'" if action == "review" else "'approved'"
            elif canon_type == "specs":
                return "'to-review'" if action == "review" else "'approved'"
            elif canon_type == "backlog":
                return "'open'"
            return "'approved'"

        if skip_ineligible:
            warn_label = err_term.colorize("warning:", "yellow", "bold")
            for it, st in ineligible_items:
                exp = _expected_status_for(it)
                styled_id = err_term.colorize(it.id, "bold")
                print(
                    f"{warn_label} item {styled_id} must be in status {exp} and not {st!r} (skipping)",
                    file=sys.stderr,
                )
        else:
            lines: List[str] = []
            if len(ineligible_items) == 1:
                it, st = ineligible_items[0]
                exp = _expected_status_for(it)
                styled_id = err_term.colorize(it.id, "bold")
                lines.append(
                    f"item {styled_id} with status {st!r} is ineligible for runner dispatch: item {styled_id} must be in status {exp} and not {st!r}"
                )
            else:
                lines.append(
                    f"selection is ineligible for runner dispatch ({len(ineligible_items)} items):"
                )
                for it, st in ineligible_items:
                    exp = _expected_status_for(it)
                    styled_id = err_term.colorize(it.id, "bold")
                    lines.append(
                        f"  item {styled_id} must be in status {exp} and not {st!r}"
                    )

            skip_flag = err_term.colorize("--skip-ineligible", "cyan")
            remedy_parts: List[str] = []

            reviewed_plans = [
                it.id
                for it, st in ineligible_items
                if canon_type == "plans" and (st or "").lower() == "reviewed"
            ]
            to_review_plans = [
                it.id
                for it, st in ineligible_items
                if canon_type == "plans" and (st or "").lower() == "to-review"
            ]
            reviewed_specs = [
                it.id
                for it, st in ineligible_items
                if canon_type == "specs" and (st or "").lower() == "reviewed"
            ]

            if reviewed_plans:
                if len(reviewed_plans) <= 4:
                    ids_str = " ".join(reviewed_plans)
                    cmd = err_term.colorize(
                        f"aw ipd set approved {ids_str} --by-human", "cyan"
                    )
                else:
                    cmd = err_term.colorize(
                        "aw ipd set approved <id6> --by-human for each", "cyan"
                    )
                remedy_parts.append(f"approve with {cmd}")

            if to_review_plans and action != "review":
                if len(to_review_plans) <= 4:
                    ids_str = " ".join(to_review_plans)
                    cmd = err_term.colorize(f"/plan-review {ids_str}", "cyan")
                else:
                    cmd = err_term.colorize("/plan-review <id6> for each", "cyan")
                remedy_parts.append(f"review with {cmd}")

            if reviewed_specs:
                if len(reviewed_specs) <= 4:
                    ids_str = " ".join(reviewed_specs)
                    cmd = err_term.colorize(
                        f"aw specs set {ids_str} --status approved --by-human", "cyan"
                    )
                else:
                    cmd = err_term.colorize(
                        "aw specs set <id6> --status approved --by-human for each",
                        "cyan",
                    )
                remedy_parts.append(f"approve with {cmd}")

            if remedy_parts:
                lines.append(
                    f"  remedy: {', or '.join(remedy_parts)}, or pass {skip_flag} to omit"
                )
            else:
                lines.append(f"  remedy: pass {skip_flag} to omit")

            raise ValueError("\n".join(lines))

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

    if statuses_not:
        status_not_set = {s.lower() for s in statuses_not}
        candidates = [
            it
            for it in candidates
            if (getattr(it, "status", None) or it.native_status).lower()
            not in status_not_set
        ]

    if priorities:
        candidates = [
            it for it in candidates if (it.priority or "").lower() in norm_priorities
        ]

    if not include_active:
        if run_map is None:
            run_map = _att.get_active_runs_map(repo_root)
        if run_map:
            candidates = [it for it in candidates if not is_active_item(it, run_map)]

    if candidates:
        distinct_actions = {
            _run_selection_policy.action_for_status(
                spec_type, getattr(it, "status", None) or it.native_status
            )
            for it in candidates
        }
        if action is not None:
            err_term = term if term is not None else Term(stream=sys.stderr)
            for it in candidates:
                it_act = _run_selection_policy.action_for_status(
                    spec_type, getattr(it, "status", None) or it.native_status
                )
                if it_act != action:
                    styled_id = err_term.colorize(it.id, "bold")
                    raise ValueError(
                        f"item {styled_id} requires action {it_act!r}, which conflicts with requested --action {action!r}"
                    )
        elif require_homogeneous_action:
            if len(distinct_actions) > 1:
                actions_str = ", ".join(sorted(distinct_actions))
                raise ValueError(
                    f"selection contains mixed actions ({actions_str}); filter by -s or --action to produce a homogeneous queue"
                )

    effective_order_by = order_by or ("depth" if artifact_type == "plans" else "date")
    if max_count is not None and max_count > 0:
        candidates = apply_max_count(candidates, max_count, effective_order_by)

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
    if context is not None:
        fields = getattr(context, "fields", None)
    else:
        from agent_workflows.result_types import select_output

        fields = select_output(args).fields

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
    statuses_not = list(getattr(args, "status_not", []) or [])
    priorities = list(getattr(args, "priority", []) or [])
    allow_partial_sets = bool(getattr(args, "allow_partial_sets", False))
    skip_ineligible = bool(getattr(args, "skip_ineligible", False))
    include_active = bool(getattr(args, "include_active", False))
    run_map: Optional[Dict[str, str]] = None
    if not include_active:
        run_map = _att.get_active_runs_map(repo_root)

    canon_type = _status_set.canonical_type(artifact_type) or artifact_type
    effective_order_by = order_by_flag or ("depth" if canon_type == "plans" else "date")
    spec_type = _run_selection_policy.SPEC_TYPE_BY_RESOLVER_TYPE.get(
        canon_type, canon_type
    )

    classifications: Dict[str, SetClassification] = {}
    held_back_orchestrators: List[Dict[str, Any]] = []
    extra_edges: Optional[List[Tuple[str, str]]] = None
    orchestrator_ids: Optional[Set[str]] = None
    set_by_item: Optional[Dict[str, str]] = None

    if canon_type == "plans":
        try:
            raw_candidates = collect(
                repo_root=repo_root,
                artifact_type=artifact_type,
                selectors=selectors,
                statuses=statuses,
                statuses_not=statuses_not,
                priorities=priorities,
                max_count=None,
                stdin_ids=stdin_ids,
                order_by=order_by_flag,
                action=action_flag,
                require_homogeneous_action=False,
                include_active=include_active,
                run_map=run_map,
                skip_ineligible=skip_ineligible,
                term=term,
            )
        except ValueError as e:
            err_term = _make_err_term(term)
            err_label = err_term.colorize("Error:", "red", "bold")
            print(f"{err_label} {e}", file=sys.stderr)
            return 2

        with_dependencies = bool(getattr(args, "with_dependencies", False))
        if with_dependencies:
            raw_candidates = expand_candidates_with_dependencies(
                repo_root=repo_root,
                candidates=raw_candidates,
                artifact_type=artifact_type,
                statuses=statuses,
                action=action_flag,
                include_active=include_active,
                run_map=run_map,
            )

        pre_max_candidates = apply_max_count(raw_candidates, None, effective_order_by)
        candidates = apply_max_count(pre_max_candidates, max_count, effective_order_by)

        classifications = classify_sets(
            repo_root=repo_root,
            candidates=candidates,
            pre_max_candidates=pre_max_candidates,
            max_count=max_count,
            action_flag=action_flag,
            include_active=include_active,
            run_map=run_map,
        )

        # Action homogeneity check for plans performed AFTER Set classification.
        # Exclude blocked members of orchestrator-bearing Sets from tripping mixed actions.
        blocked_ids = {b.id6 for cs in classifications.values() for b in cs.blocked}
        runnable_candidates = [it for it in candidates if it.id not in blocked_ids]

        if action_flag is not None:
            err_term = _make_err_term(term)
            for it in runnable_candidates:
                it_act = _run_selection_policy.action_for_status(
                    spec_type, getattr(it, "status", None) or it.native_status
                )
                if it_act != action_flag:
                    err_label = err_term.colorize("Error:", "red", "bold")
                    styled_id = err_term.colorize(it.id, "bold")
                    print(
                        f"{err_label} item {styled_id} requires action {it_act!r}, which conflicts with requested --action {action_flag!r}",
                        file=sys.stderr,
                    )
                    return 2
        else:
            distinct_actions = {
                _run_selection_policy.action_for_status(
                    spec_type, getattr(it, "status", None) or it.native_status
                )
                for it in runnable_candidates
            }
            if len(distinct_actions) > 1:
                actions_str = ", ".join(sorted(distinct_actions))
                print(
                    f"Error: selection contains mixed actions ({actions_str}); filter by -s or --action to produce a homogeneous queue",
                    file=sys.stderr,
                )
                return 2

        blocked_sets = [c for c in classifications.values() if not c.is_completeable]
        err_term = Term(stream=sys.stderr)

        if blocked_sets and not allow_partial_sets:
            # Whole batch refusal: emit NO commands for any shard, exit 2
            for cs in blocked_sets:
                for line in render_set_block(cs, err_term, is_warning=False):
                    print(line, file=sys.stderr)

            if is_agent:
                record = {
                    "schema": agent_schema.SCHEMA_VERSION,
                    "kind": "result",
                    "cmd": "partition",
                    "exit": 2,
                    "outcome": "cannot-run",
                    "verified": True,
                    "complete": True,
                    "blocked_sets": [cs.to_dict() for cs in blocked_sets],
                }
                if fields:
                    record = agent_schema.filter_record_fields(record, fields)
                sys.stdout.write(agent_schema.render_jsonl_record(record))
                return 2

            if is_json:
                payload = {
                    "blocked_sets": [cs.to_dict() for cs in blocked_sets],
                }
                print(json.dumps(payload, indent=2))
                return 2

            return 2

        if blocked_sets and allow_partial_sets:
            dropped_orch_ids = {cs.orchestrator_id for cs in blocked_sets}
            candidates = [
                it
                for it in candidates
                if it.id not in dropped_orch_ids and it.id not in blocked_ids
            ]
            for cs in blocked_sets:
                for line in render_set_block(cs, err_term, is_warning=True):
                    print(line, file=sys.stderr)
                held_back_orchestrators.append(cs.to_dict())

        # Build extra clustering edges and sort helpers for plans
        extra_edges = []
        orchestrator_ids = set()
        set_by_item = {}
        candidate_ids = {it.id for it in candidates if it.id}

        for cs in classifications.values():
            orchestrator_ids.add(cs.orchestrator_id)
            for mid in cs.runnable:
                set_by_item[mid] = cs.setid
            runnable_children = [
                cid
                for cid in cs.runnable
                if cid != cs.orchestrator_id and cid in candidate_ids
            ]
            if cs.is_completeable:
                if cs.orchestrator_id in candidate_ids:
                    for cid in runnable_children:
                        extra_edges.append((cs.orchestrator_id, cid))
                else:
                    for i in range(len(runnable_children) - 1):
                        extra_edges.append(
                            (runnable_children[i], runnable_children[i + 1])
                        )
            else:
                for i in range(len(runnable_children) - 1):
                    extra_edges.append((runnable_children[i], runnable_children[i + 1]))

    else:
        try:
            candidates = collect(
                repo_root=repo_root,
                artifact_type=artifact_type,
                selectors=selectors,
                statuses=statuses,
                statuses_not=statuses_not,
                priorities=priorities,
                max_count=max_count,
                stdin_ids=stdin_ids,
                order_by=order_by_flag,
                action=action_flag,
                require_homogeneous_action=True,
                include_active=include_active,
                run_map=run_map,
                skip_ineligible=skip_ineligible,
                term=term,
            )
        except ValueError as e:
            err_term = _make_err_term(term)
            err_label = err_term.colorize("Error:", "red", "bold")
            print(f"{err_label} {e}", file=sys.stderr)
            return 2

    part_res = partition(
        candidates,
        shards_val,
        order_by=effective_order_by,
        extra_edges=extra_edges,
        orchestrator_ids=orchestrator_ids,
        set_by_item=set_by_item,
    )

    # Derive effective action for non-empty candidates
    effective_action: Optional[str] = None
    if candidates:
        if action_flag is not None:
            effective_action = action_flag
        else:
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
        if held_back_orchestrators:
            record["held_back_orchestrators"] = held_back_orchestrators
        if fields:
            record = agent_schema.filter_record_fields(record, fields)
        sys.stdout.write(agent_schema.render_jsonl_record(record))
        return 0

    if is_json:
        payload = {
            "shards": [[it.id for it in s if it.id] for s in part_res.shards],
            "commands": redacted_commands,
            "split_components": [sc.to_dict() for sc in part_res.split_components],
            "cycles": part_res.cycles,
        }
        if held_back_orchestrators:
            payload["held_back_orchestrators"] = held_back_orchestrators
        print(json.dumps(payload, indent=2))
        return 0

    if not candidates:
        print(f"No matching {canon_type} items found to partition.", file=sys.stderr)
        return 0

    for cmd in commands:
        print(cmd)

    return 0

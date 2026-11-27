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
    kept_whole_sets: Tuple[str, ...] = ()


@dataclass(frozen=True)
class BlockedMember:
    """One member of a Set blocking the batch from finishing."""

    id6: str
    status: str
    cause: str
    fix: str
    unsatisfied_dependencies: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id6": self.id6,
            "status": self.status,
            "cause": self.cause,
            "fix": agent_schema.redact_home_paths(self.fix),
        }
        if self.unsatisfied_dependencies:
            payload["unsatisfied_dependencies"] = list(self.unsatisfied_dependencies)
        return payload


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
    review_unreviewed_deps: bool = False,
) -> Tuple[bool, str]:
    """Check if a declared ItemDependency edge is satisfied against current disk state."""
    from agent_workflows import runner_shared

    state = {
        "repo": repo_root,
        "queue": [],
        "options": {"review_unreviewed_deps": review_unreviewed_deps},
    }
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
    review_unreviewed_deps: bool = False,
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
                repo_root,
                edge,
                consumer_action=action or "execute",
                review_unreviewed_deps=review_unreviewed_deps,
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


#: Statuses at which a plan needs no further review (see `classify_sets`).
_REVIEW_SETTLED_STATUSES = frozenset({"reviewed", "approved", "auto-approved"})

#: Statuses eligible for explicit non-orchestrator re-review under `--action review`.
_REREVIEW_ADMISSIBLE_STATUSES = frozenset({"reviewed", "approved", "auto-approved"})


def _is_orchestrator_plan(it: _att.Item, repo_root: Path) -> bool:
    """Return True when ``it`` is a plan whose front-matter ``- Kind:`` is ``orchestrator``."""
    if it.tree != "plans":
        return False
    p = repo_root / it.path
    if not p.is_file():
        return False
    try:
        head = p.read_text(encoding="utf-8")[:4096]
    except OSError:
        return False
    from agent_workflows import artifact_meta as _meta

    role = _meta.read_text(_meta.metadata_region(head), record_type="ipd").fields.get(
        "plan_role"
    )
    return str(role or "").strip().lower() == "orchestrator"


def classify_sets(
    repo_root: Path,
    candidates: Sequence[_att.Item],
    pre_max_candidates: Sequence[_att.Item],
    max_count: Optional[int] = None,
    action_flag: Optional[str] = None,
    include_active: bool = False,
    run_map: Optional[Dict[str, str]] = None,
    review_unreviewed_deps: bool = False,
    rereview_ids: Optional[Set[str]] = None,
) -> Dict[str, SetClassification]:
    """Classify every distinct Set that has a selected member and an orchestrator on disk."""
    rereview_set = rereview_ids or set()
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
            if (
                batch_action == _run_selection_policy.ACTION_REVIEW
                and m_status in _REVIEW_SETTLED_STATUSES
            ):
                if m.id6 in rereview_set:
                    if m.id6 in runnable_ids:
                        runnable.append(m.id6)
                    else:
                        finished.append(m.id6)
                    continue
                # A review batch has nothing to do for a member that is already reviewed, and no
                # orchestrator retires in a review run, so that member neither blocks the Set nor
                # needs approval first. (Approval gates EXECUTION; refusing a review batch for it
                # made a half-reviewed Set unpartitionable.)
                finished.append(m.id6)
                continue

            if is_orch_terminal:
                # The orchestrator already retired, so there is no retirement for this batch to
                # protect and no reason a sibling's status, selection, --max exclusion or live run
                # should refuse it (8t28wj E-02: such a Set "partitions exactly as today"). The
                # only check that still applies is the dependency verification below, which acts
                # on the runnable members recorded here.
                if m.id6 in runnable_ids:
                    runnable.append(m.id6)
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

    changed = True
    while changed:
        changed = False
        for mid in list(active_runnable_ids):
            edges = member_edges.get(mid, [])
            for edge in edges:
                sat_disk, _ = is_edge_satisfied_on_disk(
                    repo_root,
                    edge,
                    consumer_action=action_flag or "execute",
                    review_unreviewed_deps=review_unreviewed_deps,
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
                    break

    # Collect ALL unsatisfied dependency targets for each blocked member once active_runnable_ids has converged.
    unsatisfied_targets: Dict[str, List[str]] = {}
    for mid, edges in member_edges.items():
        if mid in active_runnable_ids:
            continue
        seen_targets: Set[str] = set()
        targets_for_mid: List[str] = []
        for edge in edges:
            sat_disk, _ = is_edge_satisfied_on_disk(
                repo_root,
                edge,
                consumer_action=action_flag or "execute",
                review_unreviewed_deps=review_unreviewed_deps,
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
            if not can_satisfy and target_id and target_id not in seen_targets:
                seen_targets.add(target_id)
                targets_for_mid.append(target_id)
        if targets_for_mid:
            unsatisfied_targets[mid] = targets_for_mid

    for setid, cs in list(classifications.items()):
        new_runnable = list(cs.runnable)
        new_blocked = list(cs.blocked)
        for mid in list(new_runnable):
            if mid not in active_runnable_ids:
                new_runnable.remove(mid)
                m_info = members_by_id.get(mid)
                m_status = m_info[1].status if m_info else "approved"
                targets = unsatisfied_targets.get(mid, [])
                if len(targets) == 1:
                    fix_clause = f"run with --with-dependencies, or execute prerequisite {targets[0]} first"
                elif targets:
                    targets_str = ", ".join(targets)
                    fix_clause = f"run with --with-dependencies, or execute prerequisites {targets_str} first"
                else:
                    fix_clause = "satisfy declared item-dependencies before scheduling"
                new_blocked.append(
                    BlockedMember(
                        id6=mid,
                        status=m_status,
                        cause="unsatisfied-dependency",
                        fix=fix_clause,
                        unsatisfied_dependencies=tuple(targets),
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
        if b.unsatisfied_dependencies:
            deps_str = ", ".join(b.unsatisfied_dependencies)
            blocked_items.append(
                f"{b_id} ({b.status}, {cause_text}) [needs: {deps_str}]"
            )
        else:
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

    all_unsat_deps: List[str] = []
    if unsatisfied:
        unsat_member_ids = {b.id6 for b in unsatisfied}
        root_deps: List[str] = []
        cascading_deps: List[str] = []
        seen_deps: Set[str] = set()
        fallback_fixes: List[str] = []
        for b in unsatisfied:
            if b.unsatisfied_dependencies:
                for dep_id in b.unsatisfied_dependencies:
                    if dep_id in seen_deps:
                        continue
                    seen_deps.add(dep_id)
                    if dep_id not in unsat_member_ids:
                        root_deps.append(dep_id)
                    else:
                        cascading_deps.append(dep_id)
            elif b.fix not in fallback_fixes:
                fallback_fixes.append(b.fix)
        all_unsat_deps = root_deps + cascading_deps
        if len(all_unsat_deps) == 1:
            fix_clauses.append(
                f"run with --with-dependencies, or execute prerequisite {all_unsat_deps[0]} first"
            )
        elif all_unsat_deps:
            fix_clauses.append(
                f"run with --with-dependencies, or execute prerequisites {', '.join(all_unsat_deps)} first"
            )
        for fb in fallback_fixes:
            if fb not in fix_clauses:
                fix_clauses.append(fb)

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

    if unsatisfied and all_unsat_deps:
        missing_dep_ids = [b.id6 for b in unsatisfied]
        dep_cmd = term.colorize(f"aw att {' '.join(all_unsat_deps)}", "cyan")
        missing_cmd = term.colorize(f"aw att {' '.join(missing_dep_ids)}", "cyan")
        lines.append(
            f"  inspect: for more info on dependencies, run: {dep_cmd}\n"
            f"           for more info on items missing those dependencies, run: {missing_cmd}"
        )

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


#: Default `--poll-for-deps` interval appended to downstream shards that wait on earlier shards.
DEFAULT_POLL_FOR_DEPS = "5m"


def _weakly_connected_subsets(
    node_ids: Set[str],
    comp_edges: Dict[str, Set[str]],
) -> List[Set[str]]:
    """Return weakly connected components of ``node_ids`` under ``comp_edges``."""
    adj: Dict[str, Set[str]] = {u: set() for u in node_ids}
    for u in node_ids:
        for p in comp_edges.get(u, ()):
            if p in node_ids:
                adj[u].add(p)
                adj[p].add(u)
    visited: Set[str] = set()
    groups: List[Set[str]] = []
    for start in sorted(node_ids):
        if start in visited:
            continue
        group: Set[str] = set()
        queue = [start]
        visited.add(start)
        while queue:
            curr = queue.pop(0)
            group.add(curr)
            for nbr in sorted(adj[curr]):
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
        groups.append(group)
    return groups


def _ancestor_roots(
    node_ids: Set[str],
    comp_edges: Dict[str, Set[str]],
    roots: Set[str],
) -> Optional[Dict[str, frozenset[str]]]:
    """Compute ancestor-root sets for every node in ``node_ids``.

    Returns None if ``node_ids`` contains a cycle (not all nodes reachable via topological order).
    """
    in_deg: Dict[str, int] = {
        u: len(comp_edges.get(u, set()) & node_ids) for u in node_ids
    }
    rev: Dict[str, List[str]] = {u: [] for u in node_ids}
    for u in node_ids:
        for p in comp_edges.get(u, ()):
            if p in node_ids:
                rev[p].append(u)

    queue = sorted(u for u, d in in_deg.items() if d == 0)
    anc: Dict[str, Set[str]] = {u: ({u} if u in roots else set()) for u in node_ids}
    processed = 0
    while queue:
        u = queue.pop(0)
        processed += 1
        for dep in rev[u]:
            anc[dep].update(anc[u])
            in_deg[dep] -= 1
            if in_deg[dep] == 0:
                queue.append(dep)
    if processed != len(node_ids):
        return None
    return {u: frozenset(s) for u, s in anc.items()}


def _peel_parallel_branches_and_tail(
    comp_ids: Set[str],
    comp_edges: Dict[str, Set[str]],
    target_branches: int,
) -> Tuple[List[Set[str]], Set[str]]:
    """Peel upward-closed join nodes into ``tail`` to expose independent parallel branches.

    Invariant: every returned branch in ``branches`` is downward-closed under ``comp_edges``
    (zero prerequisites outside itself), and every node in ``tail`` only depends on nodes in
    ``branches`` or earlier nodes in ``tail``.
    """
    if target_branches < 2:
        return [set(comp_ids)], set()

    active = set(comp_ids)
    tail: Set[str] = set()

    # Step 1: peel global join nodes (or multi-root join nodes) from active until active splits
    # into >= 2 weakly connected components, or cannot be split further.
    while True:
        roots = {u for u in active if not (comp_edges.get(u, set()) & active)}
        if len(roots) < 2:
            return [set(comp_ids)], set()
        anc = _ancestor_roots(active, comp_edges, roots)
        if anc is None:
            return [set(comp_ids)], set()
        sub_comps = _weakly_connected_subsets(active, comp_edges)
        if len(sub_comps) >= 2:
            break
        all_roots = frozenset(roots)
        peel = {u for u in active if anc[u] == all_roots}
        if not peel:
            peel = {u for u in active if len(anc[u]) >= 2}
        if not peel or len(peel) == len(active):
            return [set(comp_ids)], set()
        tail.update(peel)
        active.difference_update(peel)

    branches = _weakly_connected_subsets(active, comp_edges)

    # Step 2: if we still have room for more parallel shards, peel join nodes inside the largest
    # multi-root branch to expose additional independent sub-branches.
    while len(branches) < target_branches:
        best_idx = -1
        best_size = -1
        best_peel: Set[str] = set()
        best_sub: List[Set[str]] = []
        for idx, br in enumerate(branches):
            br_roots = {u for u in br if not (comp_edges.get(u, set()) & br)}
            if len(br_roots) < 2:
                continue
            anc = _ancestor_roots(br, comp_edges, br_roots)
            if anc is None:
                continue
            all_br_roots = frozenset(br_roots)
            peel = {u for u in br if anc[u] == all_br_roots}
            if not peel:
                peel = {u for u in br if len(anc[u]) >= 2}
            if not peel or len(peel) == len(br):
                continue
            rem = br - peel
            sub = _weakly_connected_subsets(rem, comp_edges)
            if len(sub) >= 2 and len(br) > best_size:
                best_idx = idx
                best_size = len(br)
                best_peel = peel
                best_sub = sub
        if best_idx < 0:
            break
        tail.update(best_peel)
        branches = branches[:best_idx] + best_sub + branches[best_idx + 1 :]

    return branches, tail


def _assign_oversized_component_dag_safe(
    sorted_comp: List[_att.Item],
    edges: Dict[str, Set[str]],
    depths: Dict[str, int],
    order_by: str,
    clamped_k: int,
) -> Dict[str, int]:
    """Assign items of an oversized component to shards ``0..clamped_k-1`` without shard cycles.

    Guarantees ``shard_of[prereq] <= shard_of[consumer]`` for every DAG edge inside the component.
    Extracts independent parallel branches into lower shards (zero external dependencies) and
    places any join tail into a strictly higher shard. Falls back to contiguous topological slices
    for single-root chains so cut edges remain strictly forward.
    """
    comp_ids = {it.id for it in sorted_comp}
    comp_edges = {u: (edges.get(u, set()) & comp_ids) for u in comp_ids}
    by_id = {it.id: it for it in sorted_comp}

    item_to_shard: Dict[str, int] = {}

    if clamped_k >= 2:
        # Reserve 1 shard for the downstream join tail when splitting parallel branches.
        branch_budget = max(2, clamped_k - 1) if clamped_k >= 3 else 2
        branches, tail = _peel_parallel_branches_and_tail(
            comp_ids, comp_edges, target_branches=branch_budget
        )
        if len(branches) >= 2 and (not tail or clamped_k >= 3):
            parallel_slots = clamped_k - 1 if tail else clamped_k
            branches_sorted = sorted(
                branches,
                key=lambda b: (
                    -len(b),
                    min(item_sort_key(by_id[cid], depths, order_by) for cid in b),
                ),
            )
            slot_sizes = [0] * parallel_slots
            used_slots: Set[int] = set()
            for br in branches_sorted:
                target_slot = min(
                    range(parallel_slots), key=lambda i: (slot_sizes[i], i)
                )
                for cid in br:
                    item_to_shard[cid] = target_slot
                slot_sizes[target_slot] += len(br)
                used_slots.add(target_slot)
            if tail:
                tail_slot = max(used_slots) + 1
                for cid in tail:
                    item_to_shard[cid] = tail_slot
            return item_to_shard

    # Single-root chain, cycle, or k=2 with shared tail: contiguous topological slices across
    # shards 0..clamped_k-1 so every cut edge points strictly forward (prereq shard < consumer shard).
    total = len(sorted_comp)
    base, rem = divmod(total, clamped_k)
    cursor = 0
    for shard_idx in range(clamped_k):
        chunk_len = base + (1 if shard_idx < rem else 0)
        for it in sorted_comp[cursor : cursor + chunk_len]:
            item_to_shard[it.id] = shard_idx
        cursor += chunk_len
    return item_to_shard


def partition(
    items: Sequence[_att.Item],
    k: int,
    order_by: str = "depth",
    extra_edges: Optional[Sequence[Tuple[str, str]]] = None,
    orchestrator_ids: Optional[Set[str]] = None,
    set_by_item: Optional[Dict[str, str]] = None,
    *,
    relax_dependencies: bool = False,
    term: Optional[Term] = None,
) -> Partition:
    """Partition items into k balanced shards preserving dependency clusters.

    Pure and deterministic:
      1. k is clamped to max(1, min(k, len(items))); empty selection yields zero shards.
      2. Capacity cap = ceil(N / k).
      3. Components with size <= cap are placed whole, largest first, each into currently
         smallest shard (ties broken by lowest shard index).
      4. Components with size > cap are split: when dependencies are enforced
         (``relax_dependencies=False``), independent parallel branches are placed into lower
         shards with any join tail placed into a strictly higher shard (or contiguous topological
         slices for a pure chain), guaranteeing an acyclic shard dependency graph with no deadlocks.
         When ``relax_dependencies=True``, items are dealt round-robin across shards.
         However, a component containing Set edges is never split: it goes whole into the
         currently smallest shard, prints a note to stderr, and is omitted from split_components.
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
    kept_whole_sets: List[str] = []

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

    err_term = _make_err_term(term)

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
                if set_id and set_id not in kept_whole_sets:
                    kept_whole_sets.append(str(set_id))
                noun = "plans" if comp[0].tree == "plans" else "items"
                note_lbl = err_term.colorize("note:", "cyan", "bold")
                styled_set = err_term.colorize(str(set_id), "bold")
                print(
                    f"{note_lbl} Set '{styled_set}' ({len(comp)} {noun}) kept whole in shard {target_idx}, exceeding the even share of {cap}",
                    file=sys.stderr,
                )
        else:
            sorted_comp = sorted(
                comp, key=lambda it: item_sort_key(it, depths, order_by)
            )
            comp_shard_indexes: Set[int] = set()
            item_to_shard: Dict[str, int] = {}
            if relax_dependencies:
                for it in sorted_comp:
                    target_idx = _smallest_shard_idx()
                    shards[target_idx].append(it)
                    comp_shard_indexes.add(target_idx)
                    item_to_shard[it.id] = target_idx
            else:
                item_to_shard = _assign_oversized_component_dag_safe(
                    sorted_comp, edges, depths, order_by, clamped_k
                )
                for it in sorted_comp:
                    target_idx = item_to_shard[it.id]
                    shards[target_idx].append(it)
                    comp_shard_indexes.add(target_idx)

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
        kept_whole_sets=tuple(kept_whole_sets),
    )


def format_shard(
    run: str,
    ids: Sequence[str],
    *,
    action: Optional[str] = None,
    profile: Optional[str] = None,
    model: Optional[str] = None,
    variant: Optional[str] = None,
    extra_flags: Sequence[str] = (),
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
        parts.extend(extra_flags)
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
        parts.extend(extra_flags)
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
    rereview_out: Optional[Set[str]] = None,
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
    ineligible_orchestrators: List[Tuple[_att.Item, str]] = []
    seen_orch_ids: Set[str] = set()
    explicit_rereview_ids: Set[str] = set()

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
                    hint = ""
                    if (
                        action == "plan"
                        and matched_other == "backlog"
                        and artifact_type == "plans"
                    ):
                        hint = " (hint: pass -t backlog for backlog items, or omit -t to auto-detect)"
                    raise ValueError(
                        f"selector {tok!r} belongs to {matched_other!r}, not {artifact_type!r}{hint}"
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
                st_norm = (
                    (getattr(it, "status", None) or it.native_status or "")
                    .strip()
                    .lower()
                )
                in_terminal_dir = (
                    it.tree == "plans"
                    and _att._plan_disposition_from_rel(it.path) in _plans.DIR_TERMINAL
                )
                if (
                    canon_type == "plans"
                    and action == _run_selection_policy.ACTION_REVIEW
                    and res.kind != _selectors.MATCH_SETID
                    and not in_terminal_dir
                    and st_norm in _REREVIEW_ADMISSIBLE_STATUSES
                ):
                    if _is_orchestrator_plan(it, repo_root):
                        if it.id not in seen_orch_ids:
                            seen_orch_ids.add(it.id)
                            ineligible_orchestrators.append((it, st_norm))
                        continue
                    if it.id:
                        explicit_rereview_ids.add(it.id)
                    raw_candidates.append(it)
                    continue
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

    if ineligible_orchestrators:
        err_term = _make_err_term(term)
        if skip_ineligible:
            warn_label = err_term.colorize("warning:", "yellow", "bold")
            for it, st in ineligible_orchestrators:
                styled_id = err_term.colorize(it.id, "bold")
                print(
                    f"{warn_label} orchestrator plan {styled_id} (status {st!r}) cannot be re-reviewed (skipping)",
                    file=sys.stderr,
                )
        else:
            orch_ids = ", ".join(
                err_term.colorize(it.id, "bold") for it, _ in ineligible_orchestrators
            )
            skip_flag = err_term.colorize("--skip-ineligible", "cyan")
            raise ValueError(
                f"orchestrator plan(s) cannot be re-reviewed: {orch_ids} "
                f"(remedy: omit orchestrator IDs or pass {skip_flag} to skip)"
            )

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
                if it.id in explicit_rereview_ids:
                    continue
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

    if rereview_out is not None:
        rereview_out.update(
            it.id for it in candidates if it.id and it.id in explicit_rereview_ids
        )

    return candidates


def _infer_partition_artifact_type(
    repo_root: Path,
    tokens: Sequence[str],
    action: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """Infer 'plans', 'backlog', or 'specs' from selectors when -t/--type is omitted."""
    if not tokens:
        return (
            None,
            "-t/--type/--tree is required (or pass selectors whose type can be inferred)",
        )

    partition_types: Tuple[str, ...] = ("plans", "backlog", "specs")
    if action:
        action_norm = action.strip().lower()
        filtered = tuple(
            t
            for t in partition_types
            if action_norm
            in _run_selection_policy._ACTION_TABLES.get(
                _run_selection_policy.SPEC_TYPE_BY_RESOLVER_TYPE.get(t, t), {}
            ).values()
        )
        if filtered:
            partition_types = filtered

    kind_rank = {
        _selectors.MATCH_PATH: 0,
        _selectors.MATCH_ID6: 0,
        _selectors.MATCH_STEM: 0,
        _selectors.MATCH_SETID: 1,
        _selectors.MATCH_STATUS: 1,
        _selectors.MATCH_SUBSTRING: 2,
    }

    matched_types: Set[str] = set()
    by_token_types: Dict[str, Set[str]] = {}

    for tok in tokens:
        hits: List[Tuple[int, str]] = []
        for t in partition_types:
            res = _selectors.resolve(repo_root, t, tok)
            if res.is_match:
                hits.append((kind_rank.get(res.kind or "", 2), t))
        if not hits:
            by_token_types[tok] = set()
            continue
        best_rank = min(r for r, _t in hits)
        best_types = {t for r, t in hits if r == best_rank}
        matched_types.update(best_types)
        by_token_types[tok] = best_types

    if len(matched_types) == 1:
        return next(iter(matched_types)), None

    if len(matched_types) > 1:
        detail = ", ".join(
            f"{tok}->({'/'.join(sorted(types))})"
            for tok, types in by_token_types.items()
            if types
        )
        return (
            None,
            f"selectors match multiple artifact types ({detail}); specify -t plans|backlog|specs",
        )

    return (
        None,
        "-t/--type/--tree is required when selectors do not uniquely identify an artifact type",
    )


def _cluster_backlog_sets(
    repo_root: Path, candidates: Sequence[_att.Item]
) -> Tuple[List[Tuple[str, str]], Dict[str, str]]:
    """Cluster backlog candidates that share a non-singleton Set so Set orders stay serialized."""
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import project_context as _proj_ctx

    set_by_id6: Dict[str, str] = {}
    try:
        ctx = _proj_ctx.resolve_project_context(target_repo=str(repo_root))
        with _meta.ephemeral_if_uninitialized():
            rows = _meta.query(project_context=ctx, type="backlog").rows
        for row in rows:
            if row.id6 and getattr(row, "set_id", None):
                set_by_id6[str(row.id6)] = str(row.set_id)
    except Exception:
        pass

    by_set: Dict[str, List[str]] = {}
    set_by_item: Dict[str, str] = {}
    for it in candidates:
        if not it.id:
            continue
        sid = set_by_id6.get(it.id)
        if not sid:
            _, sid_from_name, _, _ = _att._extract_identity_parts(it)
            sid = sid_from_name
        if sid:
            by_set.setdefault(sid, []).append(it.id)

    extra_edges: List[Tuple[str, str]] = []
    for sid, member_ids in by_set.items():
        if len(member_ids) < 2:
            continue
        for cid in member_ids:
            set_by_item[cid] = sid
        for i in range(len(member_ids) - 1):
            extra_edges.append((member_ids[i], member_ids[i + 1]))

    return extra_edges, set_by_item


def run_partition(args: Any, term: Any, context: Any = None) -> int:
    """CLI execution entrypoint for 'aw partition'.

    `aw partition` only READS records, so the whole command runs inside `selectors.scan_once()`:
    the records tree is walked and its headers read once, not once per dependency edge (measured
    2026-11-11: 539 s for 209 plans and 1,449 edges before this; see `selectors.scan_once`)."""
    with _selectors.scan_once():
        return _run_partition_impl(args, term, context)


def _run_partition_impl(args: Any, term: Any, context: Any = None) -> int:
    repo_root = Path(getattr(args, "dir", None) or Path.cwd())

    artifact_type = getattr(args, "artifact_type", None)

    # Shards validation
    err_term = _make_err_term(term)
    err_label_base = err_term.colorize("Error:", "red", "bold")
    shards_val = getattr(args, "shards", 3)
    if shards_val is None:
        shards_val = 3
    if shards_val < 1:
        print(
            f"{err_label_base} --shards must be >= 1, got {shards_val}",
            file=sys.stderr,
        )
        return 2

    # Max count validation
    max_count = getattr(args, "max", None)
    if max_count is not None and max_count < 1:
        print(
            f"{err_label_base} --max must be >= 1, got {max_count}",
            file=sys.stderr,
        )
        return 2

    # Runner and profile validation
    profile = getattr(args, "as_profile", None)
    run_flag = getattr(args, "run", None)
    if profile and run_flag is not None:
        print(
            f"{err_label_base} --as cannot be combined with --run",
            file=sys.stderr,
        )
        return 2

    runner = "as" if profile else (run_flag or "oc")
    model = getattr(args, "model", None)
    variant = getattr(args, "variant", None)
    action_flag = getattr(args, "action", None)
    if getattr(args, "review_unreviewed_deps", False):
        if action_flag not in (None, "review"):
            print(
                f"{err_label_base} --review-unreviewed-deps applies to review runs only",
                file=sys.stderr,
            )
            return 2
        action_flag = "review"
    order_by_flag = getattr(args, "order_by", None)
    is_json = bool(getattr(args, "json", False))
    is_agent = bool(getattr(args, "agent", False))
    is_verbose = bool(getattr(args, "verbose", False))
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

    if not artifact_type:
        infer_tokens = stdin_ids if stdin_ids is not None else selectors
        inferred_type, infer_err = _infer_partition_artifact_type(
            repo_root, infer_tokens, action_flag
        )
        if not inferred_type:
            err_term = _make_err_term(term)
            err_label = err_term.colorize("Error:", "red", "bold")
            print(f"{err_label} {infer_err}", file=sys.stderr)
            return 2
        artifact_type = inferred_type

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
    rereview_ids: Set[str] = set()

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
                rereview_out=rereview_ids,
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
                review_unreviewed_deps=bool(
                    getattr(args, "review_unreviewed_deps", False)
                ),
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
            review_unreviewed_deps=bool(getattr(args, "review_unreviewed_deps", False)),
            rereview_ids=rereview_ids,
        )

        # Action homogeneity check for plans performed AFTER Set classification.
        # Exclude blocked members of orchestrator-bearing Sets from tripping mixed actions.
        blocked_ids = {b.id6 for cs in classifications.values() for b in cs.blocked}
        runnable_candidates = [it for it in candidates if it.id not in blocked_ids]

        if action_flag is not None:
            err_term = _make_err_term(term)
            for it in runnable_candidates:
                if it.id in rereview_ids:
                    continue
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
                    f"{err_label_base} selection contains mixed actions ({actions_str}); filter by -s or --action to produce a homogeneous queue",
                    file=sys.stderr,
                )
                return 2

        blocked_sets = [c for c in classifications.values() if not c.is_completeable]
        err_term = _make_err_term(term)

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
        split_sets = bool(getattr(args, "split_sets", False))
        extra_edges = []
        orchestrator_ids = set()
        set_by_item = {}
        candidate_ids = {it.id for it in candidates if it.id}

        plan_action: Optional[str] = action_flag
        if plan_action is None and candidates:
            acts = {
                _run_selection_policy.action_for_status(
                    spec_type, getattr(it, "status", None) or it.native_status
                )
                for it in candidates
            }
            if len(acts) == 1:
                plan_action = next(iter(acts))
        is_review_run = plan_action == "review"

        split_held_orch_ids: Set[str] = set()
        for cs in classifications.values():
            orchestrator_ids.add(cs.orchestrator_id)
            for mid in cs.runnable:
                set_by_item[mid] = cs.setid
            runnable_children = [
                cid
                for cid in cs.runnable
                if cid != cs.orchestrator_id and cid in candidate_ids
            ]
            if cs.orchestrator_id in cs.finished:
                # Retired orchestrator: no retirement to keep together, so its remaining members
                # balance like any other plans; real Item-Dependencies edges still cluster them.
                continue
            if split_sets:
                if (
                    not is_review_run
                    and shards_val > 1
                    and cs.orchestrator_id in candidate_ids
                    and len(runnable_children) >= 2
                ):
                    split_held_orch_ids.add(cs.orchestrator_id)
                    retire_cmd = format_shard(
                        run=runner,
                        ids=[cs.orchestrator_id],
                        action=plan_action,
                        profile=profile,
                        model=model,
                        variant=variant,
                    )
                    note_lbl = err_term.colorize("note:", "cyan", "bold")
                    styled_set = err_term.colorize(cs.setid, "bold")
                    styled_orch = err_term.colorize(cs.orchestrator_id, "bold")
                    styled_flag = err_term.colorize("--split-sets", "cyan")
                    styled_cmd = err_term.colorize(retire_cmd, "cyan")
                    print(
                        f"{note_lbl} Set '{styled_set}' orchestrator '{styled_orch}' held back under {styled_flag}; "
                        f"retire after all shards finish: {styled_cmd}",
                        file=sys.stderr,
                    )
                    held_back_orchestrators.append(
                        {
                            "setid": cs.setid,
                            "orchestrator": cs.orchestrator_id,
                            "reason": "split-sets",
                            "retire_command": agent_schema.redact_home_paths(
                                retire_cmd
                            ),
                        }
                    )
                elif (
                    not is_review_run
                    and cs.orchestrator_id in candidate_ids
                    and len(runnable_children) == 1
                ):
                    # A single-child Set cannot split its child across shards; keep its
                    # orchestrator paired with that lone child so it retires cleanly.
                    extra_edges.append((cs.orchestrator_id, runnable_children[0]))
                continue
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

        if split_held_orch_ids:
            candidates = [it for it in candidates if it.id not in split_held_orch_ids]

    else:
        split_sets = bool(getattr(args, "split_sets", False))
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

        if canon_type == "backlog" and candidates and not split_sets:
            bkl_edges, bkl_set_map = _cluster_backlog_sets(repo_root, candidates)
            if bkl_edges:
                extra_edges = bkl_edges
                set_by_item = bkl_set_map

    # `--review-unreviewed-deps` (spec 25kzda 2.9): a review consumer then accepts a `to-review`
    # prerequisite, so nothing forces a chain into one shard. Dropping the Set-cohesion edges lets an
    # oversized component split across shards like any other; the emitted commands carry the flag so
    # each shard's run applies the same rule.
    relax_reviews = bool(getattr(args, "review_unreviewed_deps", False))
    shard_flags: Tuple[str, ...] = ()
    if relax_reviews:
        extra_edges = None
        shard_flags = ("--review-unreviewed-deps",)

    part_res = partition(
        candidates,
        shards_val,
        order_by=effective_order_by,
        extra_edges=extra_edges,
        orchestrator_ids=orchestrator_ids,
        set_by_item=set_by_item,
        relax_dependencies=relax_reviews,
        term=term,
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

    # Map each item to its assigned shard and identify cross-shard dependencies.
    item_shard_map: Dict[str, int] = {}
    for s_idx, shard in enumerate(part_res.shards):
        for it in shard:
            if it.id:
                item_shard_map[it.id] = s_idx

    shard_waits_on: Dict[int, Set[int]] = {}
    for sc in part_res.split_components:
        for consumer_id, prereq_id in sc.cut_edges:
            c_idx = item_shard_map.get(consumer_id)
            p_idx = item_shard_map.get(prereq_id)
            if c_idx is not None and p_idx is not None and c_idx != p_idx:
                shard_waits_on.setdefault(c_idx, set()).add(p_idx)

    # Format commands for non-empty shards. Downstream shards with cross-shard dependencies get
    # `--poll-for-deps` automatically (unless `--review-unreviewed-deps` already relaxes them) so
    # every emitted command is directly runnable without failing dependency preflight.
    commands: List[str] = []
    for s_idx, shard in enumerate(part_res.shards):
        shard_ids = [it.id for it in shard if it.id]
        if shard_ids:
            per_shard_flags: List[str] = []
            if effective_action == "review" and shard_flags:
                per_shard_flags.extend(shard_flags)
            if not relax_reviews and s_idx in shard_waits_on:
                per_shard_flags.extend(["--poll-for-deps", DEFAULT_POLL_FOR_DEPS])
            cmd = format_shard(
                run=runner,
                ids=shard_ids,
                action=effective_action,
                profile=profile,
                model=model,
                variant=variant,
                extra_flags=per_shard_flags,
            )
            commands.append(cmd)

    # Write summary on stderr always
    active_rereview_ids = sorted(
        it.id for it in candidates if it.id and it.id in rereview_ids
    )
    if active_rereview_ids:
        warn_lbl = err_term.colorize("warning:", "yellow", "bold")
        yes_flag = err_term.colorize("--yes", "cyan")
        approved_rr_count = sum(
            1
            for it in candidates
            if it.id in rereview_ids
            and (getattr(it, "status", None) or it.native_status or "").lower()
            in ("approved", "auto-approved")
        )
        if approved_rr_count:
            print(
                f"{warn_lbl} partitioning {len(active_rereview_ids)} plan(s) for re-review "
                f"({approved_rr_count} already approved); running these shards withdraws approval "
                f"and requires typing 're-review' or passing {yes_flag}.",
                file=sys.stderr,
            )
        else:
            print(
                f"{warn_lbl} partitioning {len(active_rereview_ids)} already-reviewed plan(s) for re-review; "
                f"running these shards requires typing 're-review' or passing {yes_flag}.",
                file=sys.stderr,
            )

    shard_sizes = [len(s) for s in part_res.shards]
    part_lbl = err_term.colorize("Partitioned", "green", "bold")
    print(
        f"{part_lbl} {len(candidates)} items across {len(part_res.shards)} shard(s): {shard_sizes}",
        file=sys.stderr,
    )
    if part_res.kept_whole_sets and not split_sets and not relax_reviews:
        splittable_sets: List[str] = []
        for sid in part_res.kept_whole_sets:
            members = [
                it.id
                for it in candidates
                if set_by_item and set_by_item.get(it.id) == sid
            ]
            if (
                canon_type == "plans"
                and effective_action != "review"
                and orchestrator_ids
            ):
                non_orch = [mid for mid in members if mid not in orchestrator_ids]
                if len(non_orch) >= 2:
                    splittable_sets.append(sid)
            elif len(members) >= 2 or not members:
                splittable_sets.append(sid)
        if splittable_sets:
            sets_str = ", ".join(
                f"'{err_term.colorize(s, 'bold')}'" for s in splittable_sets
            )
            hint_lbl = err_term.colorize("hint:", "cyan", "bold")
            split_flag = err_term.colorize("--split-sets", "cyan")
            non_empty_shards = sum(1 for s in part_res.shards if s)
            if non_empty_shards == 1 and shards_val > 1:
                print(
                    f"{hint_lbl} all {len(candidates)} items ended up in 1 shard because Set cohesion kept Set {sets_str} whole; "
                    f"pass {split_flag} to split Set members across {shards_val} shards.",
                    file=sys.stderr,
                )
            else:
                print(
                    f"{hint_lbl} pass {split_flag} to allow oversized Set {sets_str} to split across shards.",
                    file=sys.stderr,
                )
    if part_res.split_components:
        note_lbl = err_term.colorize("note:", "yellow", "bold")
        verbose_flag = err_term.colorize("--verbose", "cyan")
        poll_flag = err_term.colorize(
            f"--poll-for-deps {DEFAULT_POLL_FOR_DEPS}", "cyan"
        )
        for sc in part_res.split_components:
            sc_waits: Dict[int, Set[int]] = {}
            for consumer_id, prereq_id in sc.cut_edges:
                c_idx = item_shard_map.get(consumer_id)
                p_idx = item_shard_map.get(prereq_id)
                if c_idx is not None and p_idx is not None and c_idx != p_idx:
                    sc_waits.setdefault(c_idx, set()).add(p_idx)
            wait_clause = ""
            if sc_waits and not relax_reviews:
                parts_wait = [
                    f"shard {c_idx} waits on shard{'s' if len(ps) > 1 else ''} {sorted(ps)}"
                    for c_idx, ps in sorted(sc_waits.items())
                ]
                wait_clause = f"; {'; '.join(parts_wait)} ({poll_flag})"
            elif sc.cut_edges and relax_reviews:
                relax_flag = err_term.colorize("--review-unreviewed-deps", "cyan")
                wait_clause = f" (relaxed under {relax_flag})"
            tail_hint = (
                ""
                if (is_verbose or not sc.cut_edges)
                else f". Pass {verbose_flag} to list edges."
            )
            print(
                f"{note_lbl} Split oversized component ({len(sc.component_ids)} items) across shards {sc.shard_indexes}: "
                f"{len(sc.cut_edges)} cut edge(s){wait_clause}{tail_hint}",
                file=sys.stderr,
            )
            if is_verbose and sc.cut_edges:
                grouped: Dict[str, List[str]] = {}
                for consumer_id, prereq_id in sc.cut_edges:
                    grouped.setdefault(consumer_id, []).append(prereq_id)
                for consumer_id in sorted(grouped):
                    c_idx = item_shard_map.get(consumer_id, -1)
                    prereqs_fmt = ", ".join(
                        f"{err_term.colorize(p, 'bold')} (shard {item_shard_map.get(p, -1)})"
                        for p in sorted(grouped[consumer_id])
                    )
                    c_fmt = err_term.colorize(consumer_id, "bold")
                    print(
                        f"  {c_fmt} (shard {c_idx}) <- {prereqs_fmt}",
                        file=sys.stderr,
                    )
    if part_res.cycles:
        warn_lbl = err_term.colorize("warning:", "yellow", "bold")
        print(
            f"{warn_lbl} Detected dependency cycles: {part_res.cycles}",
            file=sys.stderr,
        )

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
        if active_rereview_ids:
            record["rereview_ids"] = active_rereview_ids
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
        if active_rereview_ids:
            payload["rereview_ids"] = active_rereview_ids
        print(json.dumps(payload, indent=2))
        return 0

    if not candidates:
        print(f"No matching {canon_type} items found to partition.", file=sys.stderr)
        return 0

    for cmd in commands:
        print(cmd)

    return 0

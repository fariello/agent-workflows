"""IPD Set graph compiler and immutable execution manifest (execset Order 01, `iy1a2g`).

Convert an approved IPD Set into a deterministic, schedulable work graph BEFORE any model or
worktree is launched. This module is plan-only: it never launches a worker, mutates an
authoritative record, or grants execution authority. It reuses the already-executed awoptimize +
ipdgates runtime primitives rather than forking equivalents:

- `plans_index.scan_plans` resolves the Set inventory (each child's stable `Id`, `set_id`, `order`,
  `Status`, `path`).
- `ipd_lint.parse` + each leaf's `fields["Depends on"]` + `ipd_schema.parse_depends_on` give the
  intra-IPD E-item dependency edges; `ipd_schema.dependency_errors` detects cycles.
- The orchestrator's `## Child IPDs, sequence, and dependencies` table (heading
  `ipd_schema.H_CHILD_IPDS`) is parsed HERE for cross-IPD child->child edges; when the table is
  absent or ambiguous, legacy inference falls back to a conservative serial order (never prompts).
- `run_freeze.freeze_requirements` freezes each source IPD's content into a stable digest; the
  set-level `requirement_digest` is frozen into the manifest.
- `orchestrate_isolation.analyze_concurrency_eligibility` (via the compiler-side `LaneRequest`
  adapter) decides parallel/serial eligibility. The COMPILER (not the analyzer) forces serial
  eligibility for any node whose ownership `confidence` is not `declared`/high.
- `workflow_compiler`'s sorted-keys/fixed-separator emit style makes `execution-plan.json`
  byte-stable.

Two net-new pieces this module OWNS (verified absent elsewhere):
  1. `deferred_gate`: an individually unapproved child is classified `deferred_gate`; ONLY its
     descendants are blocked while independent approved siblings remain runnable.
  2. Cross-IPD (child->child) dependency edges parsed from the orchestrator child-table.

Pure + stdlib-only aside from the reused agent_workflows primitives. Deterministic: the same Set at
the same base HEAD always compiles to the same manifest bytes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

from agent_workflows import ipd_lint as _lint
from agent_workflows import ipd_schema as _schema
from agent_workflows import orchestrate_isolation as _iso
from agent_workflows import plans_index as _pindex
from agent_workflows import run_freeze as _freeze

# Manifest schema version (bump on any incompatible node/manifest field change).
MANIFEST_SCHEMA_VERSION = 1

# Statuses that mark a child as runnable (OQ-02: read status at face value; the compiler NEVER
# sets or infers approval, and the manifest never grants launch authority).
RUNNABLE_STATUSES: frozenset = frozenset(("approved", "auto-approved"))

# Ownership-confidence vocabulary. Anything below `declared`/`high` forces the compiler to place the
# node on a serial lane before the concurrency analyzer is consulted (the analyzer never sees an
# unresolved confidence).
CONFIDENCE_DECLARED = "declared"
CONFIDENCE_HIGH = "high"
CONFIDENCE_LOW = "low"
CONFIDENCE_INFERRED = "inferred"
_HIGH_CONFIDENCE: frozenset = frozenset((CONFIDENCE_DECLARED, CONFIDENCE_HIGH))

# Node classification for a child that is not itself runnable.
GATE_DEFERRED = "deferred_gate"

# Work classes / model roles (v1 conservative defaults; refined by Order 02/03).
WORK_CLASS_CODING = "coding"
MODEL_ROLE_CODING = "coding"


class SetPlanError(Exception):
    """Raised when a Set cannot be resolved into a valid graph (globally invalid structure)."""


class ChildInventory(NamedTuple):
    """One resolved child IPD in the Set inventory."""

    plan_id: str  # stable id6
    path: str  # posix path relative to the plans dir
    order: Optional[int]
    status: str
    kind: Optional[str]
    runnable: bool  # status in RUNNABLE_STATUSES
    # Intra-IPD E-item leaf ids (e.g. "E-01") in document order.
    e_leaves: Tuple[str, ...]
    # Intra-IPD edge map: {E-id: [dep E-id, ...]} (within THIS child only).
    e_edges: Mapping[str, Tuple[str, ...]]
    # Source content digest (frozen), for provenance.
    content_digest: str


class SetInventory(NamedTuple):
    """The deterministic inventory: every child and E-leaf exactly once, plus cross-IPD edges."""

    set_id: str
    orchestrator_id: Optional[str]  # id6 of the Order-00 orchestrator, if present
    children: Tuple[ChildInventory, ...]  # sorted by (order, plan_id)
    # Cross-IPD child->child edges: {child_id: [dep child_id, ...]}. Parsed from the orchestrator
    # child-table when present/unambiguous, else conservatively inferred (serial by Order).
    cross_edges: Mapping[str, Tuple[str, ...]]
    # Whether cross_edges came from an explicit orchestrator table (True) or legacy inference (False).
    cross_edges_source: str  # "orchestrator-table" | "legacy-inference"
    # Children classified deferred_gate (unapproved) -> the set of child ids blocked (that child +
    # all its transitive descendants). Independent approved siblings are NOT in here.
    deferred_gates: Tuple[str, ...]
    blocked_children: Tuple[str, ...]
    requirement_digest: str  # set-level frozen digest over source IPD contents


# --------------------------------------------------------------------------------------------------
# Material change 1: Resolve and gate the Set
# --------------------------------------------------------------------------------------------------


def _read_text(plans_dir: Path, rel_path: str) -> str:
    return (plans_dir / rel_path).read_text(encoding="utf-8")


def _str_seq(value: object) -> Tuple[str, ...]:
    """Coerce an optional ownership declaration value into a sorted tuple of strings."""
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (str(value),)
    try:
        return tuple(sorted(str(x) for x in value))  # type: ignore[union-attr]
    except TypeError:
        return (str(value),)


def _intra_ipd_graph(
    text: str,
) -> Tuple[Tuple[str, ...], Dict[str, Tuple[str, ...]], List[str]]:
    """Parse an IPD's E-item leaves + intra-IPD Depends-on edges. Returns (e_ids, edges, errors).

    Reuses `ipd_lint.parse` for the leaves and `ipd_schema.parse_depends_on` for each leaf's
    ``Depends on`` sub-field, then `ipd_schema.dependency_errors` for missing-target/self-ref/cycle
    detection (the dependency graph is NOT returned by parse(); it is built here).
    """
    doc = _lint.parse(text)
    e_ids: List[str] = []
    edges: Dict[str, Tuple[str, ...]] = {}
    errors: List[str] = []
    for leaf in doc.exec_leaves:
        if leaf.kind != "E" or not leaf.ident:
            continue
        e_ids.append(leaf.ident)
        dep_raw = leaf.fields.get("Depends on", "none")
        deps, derr = _schema.parse_depends_on(dep_raw)
        if derr:
            errors.append("{0}: {1}".format(leaf.ident, derr))
        edges[leaf.ident] = tuple(deps)
    errors.extend(_schema.dependency_errors({k: list(v) for k, v in edges.items()}))
    return tuple(e_ids), edges, errors


def _parse_orchestrator_child_table(
    text: str,
) -> Optional[Dict[str, Tuple[str, ...]]]:
    """Parse the orchestrator ``## Child IPDs, sequence, and dependencies`` markdown table.

    Returns {order_int: (dep_order_int, ...)} keyed by the Order column, or None when no usable
    table is present (caller then falls back to legacy serial inference).

    The table columns are: | Order | File | Purpose | Depends on |. The ``Depends on`` cell is a
    comma-separated list of Order numbers, or ``none``. An ambiguous/malformed table (unparseable
    Order, or a Depends-on token that is neither ``none`` nor an integer) returns None so the caller
    conservatively serializes rather than guessing.
    """
    lines = text.splitlines()
    heading = "## " + _schema.H_CHILD_IPDS
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == heading:
            start = i + 1
            break
    if start is None:
        return None

    rows: Dict[str, Tuple[str, ...]] = {}
    saw_any_row = False
    for ln in lines[start:]:
        s = ln.strip()
        if s.startswith("## "):
            break  # next section
        if not s.startswith("|"):
            if saw_any_row:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 4:
            continue
        first = cells[0].lower()
        # Skip header row and the separator row (---|---).
        if first in ("order",):
            continue
        if set(cells[0].replace("-", "").replace(":", "")) <= {""} and "-" in cells[0]:
            continue
        # Data row: parse Order and Depends on.
        order_tok = cells[0].strip("`").strip()
        depends_tok = cells[3].strip("`").strip()
        if not order_tok.isdigit():
            return None  # ambiguous -> conservative serial
        deps: List[str] = []
        if depends_tok.lower() not in ("none", ""):
            for t in depends_tok.split(","):
                tt = t.strip().strip("`").strip()
                if not tt:
                    continue
                if not tt.isdigit():
                    return None  # ambiguous -> conservative serial
                deps.append(str(int(tt)))
        rows[str(int(order_tok))] = tuple(deps)
        saw_any_row = True
    if not saw_any_row:
        return None
    return rows


def _content_digest(child_id: str, text: str) -> str:
    """Freeze a single IPD's content into a stable digest via run_freeze primitives.

    Uses `freeze_requirements` with the plan text as one `must` requirement so the digest carries
    the same cosmetic-edit normalization as the run ledger's frozen requirements.
    """
    rs = _freeze.freeze_requirements({"must": [text]})
    return rs.items[0].digest


def _propagate_blocked(
    child_ids: Sequence[str],
    cross_edges: Mapping[str, Sequence[str]],
    gates: Sequence[str],
) -> List[str]:
    """Return the set of child ids blocked because they are, or transitively depend on, a gate.

    A child is blocked iff it is a deferred_gate OR any of its (transitive) dependencies is blocked.
    Independent approved siblings are never blocked.
    """
    gate_set = set(gates)
    blocked = set(gate_set)
    # Iterate to a fixpoint over the dependency edges.
    changed = True
    while changed:
        changed = False
        for cid in child_ids:
            if cid in blocked:
                continue
            for dep in cross_edges.get(cid, ()):  # type: ignore[arg-type]
                if dep in blocked:
                    blocked.add(cid)
                    changed = True
                    break
    return sorted(blocked)


def resolve_set(plans_dir: Path, set_id: str) -> SetInventory:
    """E-01: resolve a Set into one deterministic inventory with every child + E-leaf exactly once.

    Rejects globally invalid Set structure (empty/missing Set, duplicate ids, intra-IPD cycles).
    Classifies an individually unapproved child as ``deferred_gate`` and blocks ONLY its descendants
    while independent approved siblings remain runnable. Parses cross-IPD child->child edges from
    the orchestrator child-table, falling back to conservative serial inference (never prompts).
    """
    entries, drift = _pindex.scan_plans(plans_dir)
    members = [e for e in entries if e.set_id == set_id]
    if not members:
        raise SetPlanError("no plans found for Set '{0}'".format(set_id))

    # Reject duplicate stable ids across the Set (globally invalid structure).
    seen_ids: Dict[str, str] = {}
    for e in members:
        if not e.plan_id:
            raise SetPlanError(
                "Set '{0}' has a plan without a stable Id: {1}".format(set_id, e.path)
            )
        if e.plan_id in seen_ids:
            raise SetPlanError(
                "Set '{0}' has duplicate Id '{1}' ({2} and {3})".format(
                    set_id, e.plan_id, seen_ids[e.plan_id], e.path
                )
            )
        seen_ids[e.plan_id] = e.path

    orchestrator_id: Optional[str] = None
    orchestrator_text: Optional[str] = None
    children: List[ChildInventory] = []
    order_to_id: Dict[str, str] = {}
    global_errors: List[str] = []

    for e in sorted(
        members,
        key=lambda m: (m.order if m.order is not None else 9999, m.plan_id or ""),
    ):
        text = _read_text(plans_dir, e.path)
        if e.order == 0 or (e.kind == "orchestrator"):
            orchestrator_id = e.plan_id
            orchestrator_text = text
            # The orchestrator is not a runnable child leaf-holder in the child graph; skip it as a
            # schedulable child but retain its id and table.
            continue
        e_ids, e_edges, e_errs = _intra_ipd_graph(text)
        assert (
            e.plan_id is not None
        )  # validated non-empty in the duplicate-id pass above
        plan_id: str = e.plan_id
        for err in e_errs:
            global_errors.append("{0} ({1}): {2}".format(plan_id, e.path, err))
        status = (e.status or "").strip()
        runnable = status in RUNNABLE_STATUSES
        children.append(
            ChildInventory(
                plan_id=plan_id,
                path=e.path,
                order=e.order,
                status=status,
                kind=e.kind,
                runnable=runnable,
                e_leaves=e_ids,
                e_edges={k: v for k, v in e_edges.items()},
                content_digest=_content_digest(plan_id, text),
            )
        )
        if e.order is not None:
            order_to_id[str(e.order)] = plan_id

    if global_errors:
        raise SetPlanError(
            "Set '{0}' has invalid IPD structure: {1}".format(
                set_id, "; ".join(global_errors)
            )
        )

    child_ids = [c.plan_id for c in children]

    # Cross-IPD edges: prefer the orchestrator child-table (by Order), map to child ids.
    cross_edges: Dict[str, Tuple[str, ...]] = {}
    cross_source = "legacy-inference"
    table = (
        _parse_orchestrator_child_table(orchestrator_text)
        if orchestrator_text
        else None
    )
    if table is not None:
        ok = True
        tmp: Dict[str, Tuple[str, ...]] = {}
        for c in children:
            ord_key = str(c.order) if c.order is not None else None
            if ord_key is None or ord_key not in table:
                ok = False
                break
            dep_ids: List[str] = []
            for dep_order in table[ord_key]:
                dep_id = order_to_id.get(dep_order)
                if dep_id is None:
                    ok = False
                    break
                dep_ids.append(dep_id)
            if not ok:
                break
            tmp[c.plan_id] = tuple(dep_ids)
        if ok:
            cross_edges = tmp
            cross_source = "orchestrator-table"
    if cross_source != "orchestrator-table":
        # Legacy inference: conservative serial chain by Order (each child depends on the prior).
        ordered = sorted(
            children,
            key=lambda c: (c.order if c.order is not None else 9999, c.plan_id),
        )
        prev: Optional[str] = None
        for c in ordered:
            cross_edges[c.plan_id] = (prev,) if prev else ()
            prev = c.plan_id

    # Cross-IPD cycle detection (reuse the schema detector).
    cross_err = _schema.dependency_errors({k: list(v) for k, v in cross_edges.items()})
    if cross_err:
        raise SetPlanError(
            "Set '{0}' cross-IPD dependency graph invalid: {1}".format(
                set_id, "; ".join(cross_err)
            )
        )

    # Gate classification + descendant-only blocking.
    gates = tuple(sorted(c.plan_id for c in children if not c.runnable))
    blocked = tuple(_propagate_blocked(child_ids, cross_edges, gates))

    # Set-level frozen digest over all source IPD contents (deterministic, order-independent).
    all_texts: List[str] = []
    if orchestrator_text is not None:
        all_texts.append(orchestrator_text)
    all_texts.extend(_read_text(plans_dir, c.path) for c in children)
    req_digest = _freeze.freeze_requirements({"must": all_texts}).requirement_digest

    return SetInventory(
        set_id=set_id,
        orchestrator_id=orchestrator_id,
        children=tuple(
            sorted(
                children,
                key=lambda c: (c.order if c.order is not None else 9999, c.plan_id),
            )
        ),
        cross_edges=cross_edges,
        cross_edges_source=cross_source,
        deferred_gates=gates,
        blocked_children=blocked,
        requirement_digest=req_digest,
    )


# --------------------------------------------------------------------------------------------------
# Material change 2: Compile graph and ownership
# --------------------------------------------------------------------------------------------------


class ManifestNode(NamedTuple):
    """One schedulable node in the execution manifest (one E-item within one child IPD)."""

    node: str  # "<child_id>:E-NN"
    child_id: str
    e_id: str
    depends_on: Tuple[str, ...]  # node ids (intra + inter IPD)
    reads: Tuple[str, ...]  # retained for provenance; NOT an analyzer input
    writes: Tuple[str, ...]
    generates: Tuple[str, ...]
    shared_surfaces: Tuple[str, ...]
    work_class: str
    model_role: str
    validation: str  # the matching V-id, if any
    deferrable: bool
    confidence: str
    blocked: bool  # true if this node's child is a deferred_gate or descends from one

    def to_dict(self) -> Dict[str, object]:
        return {
            "node": self.node,
            "child_id": self.child_id,
            "e_id": self.e_id,
            "depends_on": list(self.depends_on),
            "reads": list(self.reads),
            "writes": list(self.writes),
            "generates": list(self.generates),
            "shared_surfaces": list(self.shared_surfaces),
            "work_class": self.work_class,
            "model_role": self.model_role,
            "validation": self.validation,
            "deferrable": self.deferrable,
            "confidence": self.confidence,
            "blocked": self.blocked,
        }


def node_to_lane_request(node: ManifestNode) -> _iso.LaneRequest:
    """Compiler-side adapter: map a manifest node onto the analyzer's `LaneRequest`.

    The manifest node schema does NOT map 1:1 to `LaneRequest`. This adapter performs the mapping:
      - node.node        -> lane_id
      - node.writes      -> files_targeted
      - node.generates   -> generated_files
      - node.depends_on  -> depends_on
      - lane_kind derived: read_only when the node writes/generates nothing, else mutating
      - shared_surfaces folded into files_targeted (they participate in conflict detection)
      - worktree_path derived per node (isolated by node id) for mutating lanes

    `reads` is retained on the node for provenance but is NOT an analyzer input.

    IMPORTANT: this adapter does NOT itself implement "uncertainty forces serial"; the compiler
    (`compile_manifest`) forces serial eligibility for low/inferred-confidence nodes BEFORE the
    analyzer is called, so the analyzer never sees an unresolved confidence.
    """
    is_mutating = bool(node.writes) or bool(node.generates)
    lane_kind = _iso.LANE_KIND_MUTATING if is_mutating else _iso.LANE_KIND_READ_ONLY
    files_targeted = tuple(sorted(set(node.writes) | set(node.shared_surfaces)))
    worktree_path = (
        ".aw/worktrees/{0}".format(node.node.replace(":", "_")) if is_mutating else ""
    )
    return _iso.LaneRequest(
        lane_id=node.node,
        actor_role=node.model_role,
        lane_kind=lane_kind,
        files_targeted=files_targeted,
        generated_files=tuple(sorted(set(node.generates))),
        depends_on=node.depends_on,
        worktree_path=worktree_path,
        isolation_mode=_iso.ISOLATION_FRESH_SESSION,
    )


class ExecutionManifest(NamedTuple):
    """The immutable execution plan produced before any launch."""

    schema_version: int
    set_id: str
    base_head: str
    requirement_digest: str
    orchestrator_id: Optional[str]
    nodes: Tuple[ManifestNode, ...]
    eligibility: _iso.ConcurrencyEligibilityResult
    deferred_gates: Tuple[str, ...]
    blocked_children: Tuple[str, ...]
    cross_edges_source: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "set_id": self.set_id,
            "base_head": self.base_head,
            "requirement_digest": self.requirement_digest,
            "orchestrator_id": self.orchestrator_id,
            "cross_edges_source": self.cross_edges_source,
            "deferred_gates": list(self.deferred_gates),
            "blocked_children": list(self.blocked_children),
            "nodes": [n.to_dict() for n in self.nodes],
            "eligibility": self.eligibility.to_dict(),
        }


def _validation_targets(text: str) -> Dict[str, str]:
    """Map E-id -> V-id from the validation section (V-NN validates E-NN)."""
    doc = _lint.parse(text)
    out: Dict[str, str] = {}
    for leaf in doc.valid_leaves:
        if leaf.kind == "V" and leaf.target:
            out[leaf.target] = leaf.ident
    return out


def compile_manifest(
    inventory: SetInventory,
    plans_dir: Path,
    base_head: str,
    ownership: Optional[Mapping[str, Mapping[str, object]]] = None,
) -> ExecutionManifest:
    """E-02: compile the inventory into an immutable `ExecutionManifest`.

    ``ownership`` optionally supplies per-node resource declarations keyed by node id
    ("<child_id>:E-NN") with keys reads/writes/generates/shared_surfaces/work_class/model_role/
    deferrable/confidence. When a node has no declaration, it is conservatively treated as an
    unknown-ownership mutating node with ``confidence=inferred`` (which the compiler forces onto a
    serial lane).

    The compiler enforces "uncertainty forces serial": any node whose confidence is not
    ``declared``/``high`` is placed on a serial lane (given an isolated worktree + no parallel
    eligibility) BEFORE `analyze_concurrency_eligibility` is consulted.
    """
    ownership = ownership or {}
    nodes: List[ManifestNode] = []

    for child in inventory.children:
        v_targets = _validation_targets(_read_text(plans_dir, child.path))
        child_blocked = child.plan_id in inventory.blocked_children
        for e_id in child.e_leaves:
            node_id = "{0}:{1}".format(child.plan_id, e_id)
            decl = ownership.get(node_id, {})
            confidence = str(decl.get("confidence", CONFIDENCE_INFERRED))
            # Intra-IPD deps -> node ids within the same child.
            intra = tuple(
                "{0}:{1}".format(child.plan_id, d) for d in child.e_edges.get(e_id, ())
            )
            # Cross-IPD deps attach at the child boundary: a child's FIRST e-leaves depend on the
            # LAST leaves of each dependency child. Conservatively, depend on every dep child's
            # terminal node so a child cannot start before its dependency child completes.
            inter: List[str] = []
            for dep_child_id in inventory.cross_edges.get(child.plan_id, ()):
                dep_child = next(
                    (c for c in inventory.children if c.plan_id == dep_child_id), None
                )
                if dep_child and dep_child.e_leaves:
                    inter.append("{0}:{1}".format(dep_child_id, dep_child.e_leaves[-1]))
            depends_on = tuple(sorted(set(intra) | set(inter)))
            nodes.append(
                ManifestNode(
                    node=node_id,
                    child_id=child.plan_id,
                    e_id=e_id,
                    depends_on=depends_on,
                    reads=_str_seq(decl.get("reads")),
                    writes=_str_seq(decl.get("writes")),
                    generates=_str_seq(decl.get("generates")),
                    shared_surfaces=_str_seq(decl.get("shared_surfaces")),
                    work_class=str(decl.get("work_class", WORK_CLASS_CODING)),
                    model_role=str(decl.get("model_role", MODEL_ROLE_CODING)),
                    validation=v_targets.get(e_id, ""),
                    deferrable=bool(decl.get("deferrable", True)),
                    confidence=confidence,
                    blocked=child_blocked,
                )
            )

    nodes.sort(key=lambda n: n.node)

    # Build lane requests. Enforce "uncertainty forces serial" at the COMPILER before the analyzer:
    # a node with non-high confidence is coerced onto a mutating serial lane with an isolated
    # worktree so the analyzer cannot admit it into a parallel read-only wave.
    lanes: List[_iso.LaneRequest] = []
    for n in nodes:
        lane = node_to_lane_request(n)
        if n.confidence not in _HIGH_CONFIDENCE:
            # Force serial eligibility: treat as mutating with an isolated worktree.
            lane = lane._replace(
                lane_kind=_iso.LANE_KIND_MUTATING,
                worktree_path=lane.worktree_path
                or ".aw/worktrees/{0}".format(n.node.replace(":", "_")),
            )
        lanes.append(lane)

    eligibility = _iso.analyze_concurrency_eligibility(lanes)

    return ExecutionManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        set_id=inventory.set_id,
        base_head=base_head,
        requirement_digest=inventory.requirement_digest,
        orchestrator_id=inventory.orchestrator_id,
        nodes=tuple(nodes),
        eligibility=eligibility,
        deferred_gates=inventory.deferred_gates,
        blocked_children=inventory.blocked_children,
        cross_edges_source=inventory.cross_edges_source,
    )


def emit_manifest_json(manifest: ExecutionManifest) -> str:
    """Byte-stable JSON emit (sorted keys, fixed separators, trailing newline) per workflow_compiler."""
    return (
        json.dumps(
            manifest.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    )


# --------------------------------------------------------------------------------------------------
# Material change 3: Expose plan-only inspection
# --------------------------------------------------------------------------------------------------


def render_plan_only_human(manifest: ExecutionManifest) -> str:
    """Compact human-readable plan-only snapshot: waves, serial fallbacks, ownership, model roles."""
    lines: List[str] = []
    lines.append("Set: {0}".format(manifest.set_id))
    lines.append("Base HEAD: {0}".format(manifest.base_head))
    lines.append("Requirement digest: {0}".format(manifest.requirement_digest))
    lines.append("Cross-IPD edges: {0}".format(manifest.cross_edges_source))
    lines.append(
        "Eligibility: {0} (parallel={1})".format(
            manifest.eligibility.execution_mode,
            manifest.eligibility.is_eligible_parallel,
        )
    )
    if manifest.deferred_gates:
        lines.append(
            "Deferred gates (unapproved children): {0}".format(
                ", ".join(manifest.deferred_gates)
            )
        )
    if manifest.blocked_children:
        lines.append(
            "Blocked children (gate + descendants): {0}".format(
                ", ".join(manifest.blocked_children)
            )
        )
    if manifest.eligibility.serial_fallback_plan:
        lines.append(
            "Serial fallback order: {0}".format(
                " -> ".join(manifest.eligibility.serial_fallback_plan)
            )
        )
    if manifest.eligibility.conflicts:
        lines.append("Conflicts:")
        for c in manifest.eligibility.conflicts:
            lines.append("  - {0}: {1}".format(c.conflict_type, c.details))
    lines.append("Nodes ({0}):".format(len(manifest.nodes)))
    for n in manifest.nodes:
        flags = []
        if n.blocked:
            flags.append("BLOCKED")
        if n.confidence not in _HIGH_CONFIDENCE:
            flags.append("serial(confidence={0})".format(n.confidence))
        dep = ",".join(n.depends_on) if n.depends_on else "-"
        lines.append(
            "  {0} [{1}/{2}] deps={3} writes={4} generates={5}{6}".format(
                n.node,
                n.work_class,
                n.model_role,
                dep,
                len(n.writes),
                len(n.generates),
                " " + " ".join(flags) if flags else "",
            )
        )
    return "\n".join(lines) + "\n"


def _resolve_repo_and_plans(args: object) -> Tuple[Path, Path]:
    """Resolve (repo_root, plans_dir) honoring --dir, reusing the plans_index resolver."""
    import argparse as _argparse

    ns = args if isinstance(args, _argparse.Namespace) else _argparse.Namespace()
    return _pindex._dirs(ns)


def _current_head(repo_root: Path) -> str:
    """Return the current git HEAD sha (or "unknown" if not resolvable). Read-only."""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _run_resume_report(args: object, run_id: str, *, agent: bool = False) -> int:
    """Reconstruct a prior run's ledger and report resumable steps (read-only; fails closed on an
    unreconciled unknown outcome, never replaying completed side effects). Returns 0 resumable /
    1 nothing resumable-or-terminal / 2 cannot locate the ledger / 3 unknown outcome pending."""
    import json as _json
    from pathlib import Path as _Path

    repo_root, _plans_dir = _resolve_repo_and_plans(args)
    ledger = _Path(repo_root) / ".aw" / "records" / "runs" / run_id / "events.jsonl"
    if not ledger.is_file():
        print(
            "error: no run ledger found for {0} ({1})".format(run_id, ledger),
            flush=True,
        )
        return 2
    try:
        from agent_workflows import run_ledger_store, run_engine, set_lifecycle
    except Exception as exc:  # pragma: no cover - import guard
        print("error: cannot load recovery runtime: {0}".format(exc), flush=True)
        return 2
    store = run_ledger_store.RunLedgerStore(ledger)
    engine = run_engine.RunEngine(
        {"workflow_id": "exec-set", "steps": []}, store, run_id=run_id
    )
    ok, report = set_lifecycle.resume_or_report(engine)
    if agent:
        print(
            _json.dumps(
                {"run_id": run_id, "resumable": bool(ok), "detail": str(report)},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    else:
        if ok:
            print("resumable: {0} -> {1}".format(run_id, report))
        else:
            print("cannot resume {0}: {1}".format(run_id, report))
    return 0 if ok else 3


def run_execute_set(args: object) -> int:
    """CLI entry for ``aw ipd execute-set <set-id> [--plan-only] [--resume RUN-ID] [--agent]``.

    ``--plan-only`` compiles + inspects the manifest (launches no worker). ``--resume RUN-ID``
    reconstructs a prior run's state from its ledger and reports resumable steps, failing closed on
    an unreconciled unknown outcome (no replay). A bare ``execute-set`` with neither flag still
    refuses to auto-launch workers in this build (the coordinator primitives exist, but this run
    bootstraps the scheduler serially); it points the operator at ``--plan-only``/``--resume``.
    """
    set_id = getattr(args, "set_id", None)
    plan_only = getattr(args, "plan_only", False)
    resume_run_id = getattr(args, "resume_run_id", None)
    agent = getattr(args, "agent", False)
    if not set_id and not resume_run_id:
        print("error: a <set-id> is required", flush=True)
        return 2

    if resume_run_id:
        return _run_resume_report(args, resume_run_id, agent=agent)

    if not plan_only:
        print(
            "error: pass --plan-only to compile and inspect the Set, or --resume <run-id> to "
            "reconstruct a prior run; automatic worker launch is not enabled in this build.",
            flush=True,
        )
        return 2

    repo_root, plans_dir = _resolve_repo_and_plans(args)
    assert set_id is not None  # guarded above (set_id required unless --resume)
    try:
        inventory = resolve_set(plans_dir, set_id)
    except SetPlanError as exc:
        print("error: {0}".format(exc), flush=True)
        return 1
    base_head = _current_head(repo_root)
    manifest = compile_manifest(inventory, plans_dir, base_head=base_head)

    if agent:
        print(emit_manifest_json(manifest), end="")
    else:
        print(render_plan_only_human(manifest), end="")
    return 0

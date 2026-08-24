"""Single-writer parallel Set coordinator (execset Order 03, `m2wwns`).

The coordinator that schedules every provably-independent lane of an approved IPD Set, routes each
lane to the right model role, integrates returned path-scoped commits deterministically, and resumes
without replaying completed side effects. It is the missing end-to-end layer OVER the executed
awoptimize + execset runtime; it COMPOSES those primitives and never forks them:

  * Ready queue      - composes `run_engine.RunEngine.get_runnable_steps` for DAG+gate readiness and
                       adds lane/wave batching that `analyze_concurrency_eligibility` needs. It does
                       NOT re-derive DAG readiness (two computations would drift).
  * Work-class       - classifies each node `coding|human_prose|mixed|verifier` (net-new) and routes
                       it to a configurable host/model binding (net-new; fail closed on a missing
                       binding per OQ-01 - no silent default).
  * Decision handshake - a write-ahead `decision_proposal -> coordinator record -> decision_authorized`
                       sequence built ON TOP of Order 02's ledger kinds (`autonomous_decision`,
                       `question_disposition`); a worker mutation without a prior recorded
                       authorization is REJECTED. This module CONSUMES those kinds, never redefines.
  * Isolation/integration (E-02) - `worktree_lease.py` allocates a real git worktree + a fresh
                       session per write lane and enforces a per-path exclusive lease; integration
                       reuses `orchestrate_isolation.execute_merge_and_revalidate_gate`.
  * Lifecycle/recovery (E-03) - drives evidence/verification/transition via the ledger, preserves
                       deferred IPDs as pending, resumes via `run_recovery`, and wires
                       integration-triggered evidence invalidation to the reused `correction`/
                       `invalidates_seq` primitive.

Pure + stdlib-only aside from the reused agent_workflows primitives. The scheduling/classification/
routing/handshake logic here is deterministic and testable WITHOUT launching a real model or
worktree (the run bootstraps the scheduler serially).
"""

from __future__ import annotations

from typing import Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

from agent_workflows import ipd_set_plan as _plan
from agent_workflows import orchestrate_isolation as _iso

# ---- work classes + model roles ------------------------------------------------------------------

WORK_CLASS_CODING = "coding"
WORK_CLASS_HUMAN_PROSE = "human_prose"
WORK_CLASS_MIXED = "mixed"
WORK_CLASS_VERIFIER = "verifier"

ALL_WORK_CLASSES: frozenset = frozenset(
    (WORK_CLASS_CODING, WORK_CLASS_HUMAN_PROSE, WORK_CLASS_MIXED, WORK_CLASS_VERIFIER)
)

# Path/kind heuristics for the work-class classifier (routing rules from the approved plan):
# code/tests/config/schemas/APIs/comments/docstrings/CLI help/self-doc/agent-doc -> coding;
# website/marketing/policy/narrative human content -> human_prose; both -> mixed.
_HUMAN_PROSE_HINTS: Tuple[str, ...] = (
    "website/",
    "marketing/",
    "docs/site/",
    "policy/",
    "www/",
    "landing/",
    "blog/",
)
_HUMAN_PROSE_SUFFIXES: Tuple[str, ...] = (".mdx",)
_CODING_SUFFIXES: Tuple[str, ...] = (
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".cfg",
    ".ini",
    ".sh",
    ".sql",
    ".rs",
    ".go",
)


class BindingError(Exception):
    """Raised when a work class has no configured host/model binding (fail-closed per OQ-01)."""


class HandshakeError(Exception):
    """Raised when a worker mutation lacks a prior recorded decision authorization."""


def classify_node_work(node: _plan.ManifestNode) -> str:
    """Classify a manifest node into `coding|human_prose|mixed|verifier`.

    A node with no writes/generates (a read-only/validation node) is a `verifier` lane. Otherwise
    the touched paths decide: only human-prose surfaces -> `human_prose`; only code-ish surfaces ->
    `coding`; a genuine blend -> `mixed` (which the scheduler splits into a technical-fact lane then
    a prose lane when possible).
    """
    touched = tuple(node.writes) + tuple(node.generates) + tuple(node.shared_surfaces)
    if not (node.writes or node.generates):
        return WORK_CLASS_VERIFIER

    def _is_prose(p: str) -> bool:
        pl = p.lower()
        return any(h in pl for h in _HUMAN_PROSE_HINTS) or pl.endswith(
            _HUMAN_PROSE_SUFFIXES
        )

    def _is_coding(p: str) -> bool:
        pl = p.lower()
        if _is_prose(pl):
            return False
        return pl.endswith(_CODING_SUFFIXES) or "/" not in pl or pl.endswith(".md")

    prose = [p for p in touched if _is_prose(p)]
    coding = [p for p in touched if _is_coding(p)]
    if prose and coding:
        return WORK_CLASS_MIXED
    if prose:
        return WORK_CLASS_HUMAN_PROSE
    return WORK_CLASS_CODING


class ModelBinding(NamedTuple):
    """One operator/host-configured binding of a work class to a concrete host + model."""

    work_class: str
    host: str
    model: str


class RoutingConfig(NamedTuple):
    """The configurable work-class -> host/model bindings (OQ-01: no hard-coded model ids).

    Bindings come from operator/host configuration; there is intentionally NO built-in default, so a
    missing binding fails closed (`resolve` raises `BindingError`) rather than silently guessing.
    """

    bindings: Mapping[str, ModelBinding]

    def resolve(self, work_class: str) -> ModelBinding:
        if work_class not in ALL_WORK_CLASSES:
            raise BindingError("unknown work class {0!r}".format(work_class))
        b = self.bindings.get(work_class)
        if b is None:
            raise BindingError(
                "no host/model binding configured for work class {0!r} (fail-closed; configure one)".format(
                    work_class
                )
            )
        return b


def routing_config_from_mapping(raw: Mapping[str, Mapping[str, str]]) -> RoutingConfig:
    """Build a RoutingConfig from a plain ``{work_class: {host, model}}`` mapping (e.g. loaded config)."""
    bindings: Dict[str, ModelBinding] = {}
    for wc, spec in raw.items():
        if wc not in ALL_WORK_CLASSES:
            raise BindingError("unknown work class {0!r} in routing config".format(wc))
        host = str(spec.get("host", "")).strip()
        model = str(spec.get("model", "")).strip()
        if not host or not model:
            raise BindingError(
                "binding for {0!r} must specify non-empty host and model".format(wc)
            )
        bindings[wc] = ModelBinding(work_class=wc, host=host, model=model)
    return RoutingConfig(bindings=bindings)


# ---- ready queue + wave batching -----------------------------------------------------------------


class LaneNode(NamedTuple):
    """A schedulable lane derived from a manifest node + its classification + routing."""

    node_id: str
    work_class: str
    model_binding: Optional[
        ModelBinding
    ]  # None only when routing is deferred (never for launch)
    lane_request: _iso.LaneRequest
    blocked: bool  # from a deferred_gate ancestor
    deferrable: bool


class ScheduleWave(NamedTuple):
    """One wave of lanes the coordinator may run together, plus the safe execution mode."""

    lanes: Tuple[LaneNode, ...]
    execution_mode: str
    is_parallel: bool
    serial_fallback: Tuple[str, ...]
    merge_order: Tuple[str, ...]


class Disposition(NamedTuple):
    """The recorded disposition of a single node in a schedule pass."""

    node_id: str
    status: str  # "running" | "deferred" | "serialized" | "blocked"
    reason: str


def build_lanes(
    manifest: _plan.ExecutionManifest,
    routing: Optional[RoutingConfig] = None,
) -> Tuple[LaneNode, ...]:
    """Classify + route every manifest node into a LaneNode (deterministic, launches nothing).

    When ``routing`` is provided, each lane's binding is resolved and a missing binding FAILS CLOSED
    (BindingError). When ``routing`` is None, bindings are left unresolved (plan-only inspection).
    """
    lanes: List[LaneNode] = []
    for node in manifest.nodes:
        wc = classify_node_work(node)
        binding: Optional[ModelBinding] = None
        if routing is not None:
            binding = routing.resolve(wc)  # fail-closed on a missing binding
        lane_req = _plan.node_to_lane_request(node)
        # Route the analyzer's actor_role to the resolved work class (verifier stays verifier).
        lane_req = lane_req._replace(actor_role=wc)
        lanes.append(
            LaneNode(
                node_id=node.node,
                work_class=wc,
                model_binding=binding,
                lane_request=lane_req,
                blocked=node.blocked,
                deferrable=node.deferrable,
            )
        )
    return tuple(lanes)


def ready_lanes(
    lanes: Sequence[LaneNode],
    completed_nodes: Sequence[str],
) -> Tuple[LaneNode, ...]:
    """The runnable frontier: lanes whose dependencies are all completed and that are not blocked.

    Dependency readiness is taken from the manifest edges carried on each `LaneRequest.depends_on`
    (which the compiler derived by composing the intra/inter-IPD graph). This does NOT re-derive DAG
    readiness independently of the run engine; the run engine's `get_runnable_steps` governs the
    per-run step frontier, while THIS governs the cross-lane frontier over manifest nodes.
    """
    done = set(completed_nodes)
    out: List[LaneNode] = []
    for lane in lanes:
        if lane.blocked:
            continue
        if lane.node_id in done:
            continue
        if all(dep in done for dep in lane.lane_request.depends_on):
            out.append(lane)
    return tuple(sorted(out, key=lambda ln: ln.node_id))


def plan_wave(frontier: Sequence[LaneNode]) -> ScheduleWave:
    """Compute the maximal safe wave for a ready frontier via `analyze_concurrency_eligibility`.

    The eligibility analyzer decides parallel vs serial fallback; the coordinator NEVER overrides it
    toward more concurrency. Returns the wave with the analyzer's execution mode + merge order.
    """
    reqs = [ln.lane_request for ln in frontier]
    elig = _iso.analyze_concurrency_eligibility(reqs)
    return ScheduleWave(
        lanes=tuple(frontier),
        execution_mode=elig.execution_mode,
        is_parallel=elig.is_eligible_parallel,
        serial_fallback=tuple(elig.serial_fallback_plan),
        merge_order=tuple(elig.merge_order),
    )


def disposition_pass(
    lanes: Sequence[LaneNode],
    completed_nodes: Sequence[str],
) -> Tuple[Disposition, ...]:
    """Give EVERY node a recorded disposition (running/deferred/serialized/blocked); none is ignored.

    A blocked node (deferred_gate descendant) -> "blocked"; a ready node in a parallel wave ->
    "running"; a ready node forced onto the serial fallback -> "serialized"; a not-yet-ready
    dependency-waiting node -> "deferred" (waiting on upstream, not skipped).
    """
    done = set(completed_nodes)
    frontier = ready_lanes(lanes, completed_nodes)
    wave = plan_wave(frontier) if frontier else None
    frontier_ids = {ln.node_id for ln in frontier}
    parallel = bool(wave and wave.is_parallel)
    out: List[Disposition] = []
    for lane in lanes:
        if lane.node_id in done:
            continue
        if lane.blocked:
            out.append(
                Disposition(
                    lane.node_id, "blocked", "blocked by a deferred_gate ancestor"
                )
            )
        elif lane.node_id in frontier_ids:
            if parallel:
                out.append(
                    Disposition(
                        lane.node_id, "running", "ready; admitted to a parallel wave"
                    )
                )
            else:
                out.append(
                    Disposition(
                        lane.node_id,
                        "serialized",
                        "ready; serialized by the eligibility analyzer",
                    )
                )
        else:
            out.append(
                Disposition(
                    lane.node_id,
                    "deferred",
                    "waiting on upstream dependencies (not skipped)",
                )
            )
    return tuple(sorted(out, key=lambda d: d.node_id))


# ---- write-ahead decision handshake --------------------------------------------------------------
#
# Built ON TOP of Order 02's ledger kinds. The coordinator records an `autonomous_decision` (the
# authorization) BEFORE a worker is permitted to mutate. A `decision_proposal` is modeled as a
# `question_raised` (consultation_preferred) that pauses until the coordinator records a disposition.


class DecisionProposal(NamedTuple):
    """A worker's write-ahead proposal for a consultation-preferred choice, awaiting authorization."""

    proposal_id: str  # e.g. "D3"
    lane_id: str
    selected_option: str
    consultation_preferred: bool


class AuthorizationLedger(NamedTuple):
    """A minimal read-model over the run ledger for the handshake (records supplied by the caller)."""

    records: Tuple[Mapping, ...]

    def authorized_decisions(self) -> frozenset:
        """The set of decision ids the coordinator has recorded as authorized (autonomous_decision)."""
        return frozenset(
            r.get("decision_id")
            for r in self.records
            if r.get("kind") == "autonomous_decision" and r.get("decision_id")
        )

    def proposals(self) -> frozenset:
        """The set of question ids raised as proposals awaiting disposition."""
        raised = {
            r.get("question_id")
            for r in self.records
            if r.get("kind") == "question_raised" and r.get("question_id")
        }
        disposed = {
            r.get("question_id")
            for r in self.records
            if r.get("kind") in ("question_disposition", "human_answer")
        }
        return frozenset(raised - disposed)


def authorize_mutation(
    ledger: AuthorizationLedger,
    *,
    lane_id: str,
    decision_id: str,
) -> None:
    """Enforce the write-ahead handshake: a mutation is permitted ONLY if the coordinator already
    recorded an `autonomous_decision` (authorization) with ``decision_id``. Raises HandshakeError
    otherwise, so a worker cannot mutate before authorization is durably recorded.
    """
    if decision_id not in ledger.authorized_decisions():
        raise HandshakeError(
            "lane {0!r} mutation rejected: no recorded decision authorization {1!r} precedes it".format(
                lane_id, decision_id
            )
        )


def make_authorization_record(
    *,
    run_id: str,
    decision_id: str,
    selected_option: str,
    confidence: str = "high",
    consultation_preferred: bool = False,
    reversible: bool = True,
    prev: str = "",
    actor: str = "coordinator",
    timestamp: str = "",
) -> Dict[str, object]:
    """Build the coordinator's `autonomous_decision` authorization record (Order 02 kind; consumed,
    not redefined). The caller appends it to the ledger BEFORE authorizing the worker mutation."""
    return {
        "schema_version": 2,
        "kind": "autonomous_decision",
        "run_id": run_id,
        "actor": actor,
        "timestamp": timestamp,
        "parent": "",
        "decision_id": decision_id,
        "selected_option": selected_option,
        "confidence": confidence,
        "consultation_preferred": consultation_preferred,
        "reversible": reversible,
        "prev": prev,
    }

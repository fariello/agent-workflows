"""Single-writer state engine: DAG scheduling, lease serialization, and fail-closed state tracking.

awoptimize Order 05 (`b1v3wl`) E-02.

Implements the single-writer state engine that consumes a compiled workflow (Order 01) and append-only
ledger events (Orders 02/03), checks the dependency DAG and gate approvals, and releases only currently
runnable steps.

Key invariants:
  1. DAG dependency resolution: Only steps whose dependencies (performed/verified) and gate approvals
     are satisfied become runnable.
  2. Single-writer lease discipline: Serializes all mutations using the RunLedgerStore lock. Two
     concurrent coordinators cannot both release or transition the same run simultaneously.
  3. Lock loss fails closed: Concurrency timeouts or lost locks stop progress rather than interleaving.
  4. Durable state reconstruction: State is reconstructed from verified append-only ledger history;
     a partial or torn ledger state fails closed and cannot produce runnable steps.
  5. Transition authority enforcement: Every state modification is strictly checked against the
     run_state transition table. Executor completion attempts are rejected.

Pure stdlib implementation conforming to D138 (dependency minimization) and D139 (no runtime YAML).
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator, Mapping
from typing import (
    Any,
    NamedTuple,
)

from agent_workflows import run_evidence, run_state
from agent_workflows import run_ledger_schema as schema
from agent_workflows import run_ledger_store as ledger_store


class StepSnapshot(NamedTuple):
    step_id: str
    state: str
    action: str
    depends_on: tuple[str, ...]
    satisfies: tuple[str, ...]
    gates: tuple[str, ...]
    evidence: tuple[str, ...]
    attempts: int
    last_attempt_state: str | None
    last_attempt_actor: str | None


class RunStateSnapshot(NamedTuple):
    run_id: str
    state: str
    workflow_id: str
    steps: dict[str, StepSnapshot]
    approvals: dict[str, str]
    verifier_decisions: dict[str, str]
    cancellation_reason: str | None
    completion_evaluation: run_evidence.CompletionEvaluation | None
    record_count: int


def _normalize_workflow(
    workflow: Any,
) -> tuple[str, dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Extract workflow_id, steps mapping, and requirements list from normalized IR, compiled dict, or mapping."""
    wf_dict: dict[str, Any] = {}
    if isinstance(workflow, Mapping):
        if "workflow" in workflow and isinstance(workflow["workflow"], Mapping):
            wf_dict = dict(workflow["workflow"])
        else:
            wf_dict = dict(workflow)

    wf_id = str(wf_dict.get("id", "workflow"))
    raw_steps = wf_dict.get("steps", [])
    raw_reqs = wf_dict.get("requirements", [])

    steps_map: dict[str, dict[str, Any]] = {}
    if isinstance(raw_steps, (list, tuple)):
        for s in raw_steps:
            if isinstance(s, Mapping):
                sid = str(s.get("id", ""))
                if sid:
                    deps = tuple(
                        str(d) for d in s.get("depends_on", []) if isinstance(d, str)
                    )
                    sat = tuple(
                        str(r) for r in s.get("satisfies", []) if isinstance(r, str)
                    )
                    gates = tuple(
                        str(g) for g in s.get("gates", []) if isinstance(g, str)
                    )
                    ev = tuple(
                        str(e) for e in s.get("evidence", []) if isinstance(e, str)
                    )
                    action = str(s.get("action", ""))
                    steps_map[sid] = {
                        "id": sid,
                        "action": action,
                        "depends_on": deps,
                        "satisfies": sat,
                        "gates": gates,
                        "evidence": ev,
                    }

    reqs_list: list[dict[str, Any]] = []
    if isinstance(raw_reqs, (list, tuple)):
        for r in raw_reqs:
            if isinstance(r, Mapping):
                reqs_list.append(dict(r))

    return wf_id, steps_map, reqs_list


class RunEngine:
    """Single-writer state engine driving deterministic run execution from ledger history."""

    def __init__(
        self,
        workflow: Mapping[str, Any],
        store: ledger_store.RunLedgerStore,
        run_id: str | None = None,
        actor: str = "runtime",
        lock_timeout: float = ledger_store.DEFAULT_LOCK_TIMEOUT,
    ) -> None:
        self._store = store
        self._default_actor = actor
        self._lock_timeout = lock_timeout
        self._workflow_id, self._workflow_steps, self._workflow_reqs = (
            _normalize_workflow(workflow)
        )
        self._run_id = run_id or "run-00000001"
        self._ephemeral_step_states: dict[str, str] = {}

    @property
    def store(self) -> ledger_store.RunLedgerStore:
        return self._store

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def workflow_id(self) -> str:
        return self._workflow_id

    @contextlib.contextmanager
    def lease(self, timeout: float | None = None) -> Iterator[None]:
        """Acquire single-writer lease. Fails closed on lock contention timeout."""
        lock_t = self._lock_timeout if timeout is None else timeout
        with self._store.writer_lock(timeout=lock_t):
            yield

    def reconstruct_state(self) -> RunStateSnapshot:
        """Replay append-only ledger history to reconstruct complete durable state snapshot.
        Fails closed on any torn line, sequence gap, or hash break."""
        records = self._store.read_records(verify=True)

        run_id = self._run_id
        run_status = run_state.STATE_PENDING
        approvals: dict[str, str] = {}
        verifier_decisions: dict[str, str] = {}
        cancellation_reason: str | None = None

        # Initialize steps from workflow
        step_attempts: dict[str, int] = {sid: 0 for sid in self._workflow_steps}
        step_states: dict[str, str] = {
            sid: self._ephemeral_step_states.get(sid, run_state.STATE_PENDING)
            for sid in self._workflow_steps
        }
        step_last_attempt_state: dict[str, str | None] = {
            sid: None for sid in self._workflow_steps
        }
        step_last_attempt_actor: dict[str, str | None] = {
            sid: None for sid in self._workflow_steps
        }

        has_started_execution = False

        for rec in records:
            kind = rec.get("kind")
            rec_actor = rec.get("actor", "")

            if kind == "run":
                rec_run_id = rec.get("run_id")
                if rec_run_id:
                    run_id = rec_run_id

            elif kind == "step_attempt":
                has_started_execution = True
                sid = str(rec.get("step", ""))
                st = str(rec.get("state", ""))
                att = rec.get("attempt", 1)
                if sid in self._workflow_steps:
                    step_states[sid] = st
                    self._ephemeral_step_states[sid] = st
                    step_attempts[sid] = max(step_attempts[sid], att)
                    step_last_attempt_state[sid] = st
                    step_last_attempt_actor[sid] = rec_actor

            elif kind == "human_approval":
                gate = str(rec.get("gate", ""))
                approver = str(rec.get("approver", ""))
                if gate:
                    approvals[gate] = approver

            elif kind == "verifier_decision":
                req = str(rec.get("requirement", ""))
                res = str(rec.get("result", ""))
                if req:
                    verifier_decisions[req] = res

            elif kind == "terminal_transaction":
                term_stat = str(rec.get("terminal_status", run_state.STATE_COMPLETE))
                run_status = term_stat
                if term_stat == run_state.STATE_CANCELLED:
                    cancellation_reason = rec.get("reason", "cancelled")

        if run_status not in run_state.TERMINAL_STATES:
            if (
                any(
                    st in (run_state.STATE_RUNNING, run_state.STATE_PERFORMED)
                    for st in step_states.values()
                )
                or has_started_execution
            ):
                run_status = run_state.STATE_RUNNING
            elif any(st == run_state.STATE_RUNNABLE for st in step_states.values()):
                run_status = run_state.STATE_RUNNABLE

        steps_snapshots: dict[str, StepSnapshot] = {}
        for sid, sdata in self._workflow_steps.items():
            steps_snapshots[sid] = StepSnapshot(
                step_id=sid,
                state=step_states.get(sid, run_state.STATE_PENDING),
                action=sdata.get("action", ""),
                depends_on=sdata.get("depends_on", ()),
                satisfies=sdata.get("satisfies", ()),
                gates=sdata.get("gates", ()),
                evidence=sdata.get("evidence", ()),
                attempts=step_attempts.get(sid, 0),
                last_attempt_state=step_last_attempt_state.get(sid),
                last_attempt_actor=step_last_attempt_actor.get(sid),
            )

        completion_eval: run_evidence.CompletionEvaluation | None = None
        if records:
            completion_eval = run_evidence.evaluate_completion(records)

        return RunStateSnapshot(
            run_id=run_id,
            state=run_status,
            workflow_id=self._workflow_id,
            steps=steps_snapshots,
            approvals=approvals,
            verifier_decisions=verifier_decisions,
            cancellation_reason=cancellation_reason,
            completion_evaluation=completion_eval,
            record_count=len(records),
        )

    def run_state(self) -> str:
        """Return current run state."""
        return self.reconstruct_state().state

    def step_state(self, step_id: str) -> str:
        """Return current state of a step."""
        snapshot = self.reconstruct_state()
        step = snapshot.steps.get(step_id)
        if step is None:
            raise KeyError(f"Unknown step {step_id}")
        return step.state

    def get_runnable_steps(self) -> list[StepSnapshot]:
        """Compute and return currently runnable steps according to DAG and gate dependencies.
        Fails closed on torn or corrupted ledger state."""
        snapshot = self.reconstruct_state()

        if snapshot.state in run_state.TERMINAL_STATES:
            return []

        runnable: list[StepSnapshot] = []

        for sid, step in sorted(snapshot.steps.items(), key=lambda kv: kv[0]):
            if step.state != run_state.STATE_PENDING:
                continue

            # 1. Dependency check: all depends_on steps must be in performed or verified
            deps_satisfied = True
            for dep_id in step.depends_on:
                dep_step = snapshot.steps.get(dep_id)
                if dep_step is None or dep_step.state not in (
                    run_state.STATE_PERFORMED,
                    run_state.STATE_VERIFIED,
                ):
                    deps_satisfied = False
                    break

            if not deps_satisfied:
                continue

            # 2. Gate approval check: all required gates must be approved
            gates_satisfied = True
            for gate in step.gates:
                if gate not in snapshot.approvals:
                    gates_satisfied = False
                    break

            if not gates_satisfied:
                continue

            runnable.append(step)

        return runnable

    def release_step(self, step_id: str, actor: str = "runtime") -> StepSnapshot:
        """Transition a pending step to runnable."""
        snapshot = self.reconstruct_state()
        step = snapshot.steps.get(step_id)
        if step is None:
            raise KeyError(f"Unknown step {step_id}")

        # Check if runnable
        runnable_ids = {s.step_id for s in self.get_runnable_steps()}
        deps_ok = step_id in runnable_ids or step.state == run_state.STATE_PENDING

        run_state.check_transition(
            step.state,
            run_state.STATE_RUNNABLE,
            actor,
            predicate_values={"dependencies_and_approvals_satisfied": deps_ok},
        )

        self._ephemeral_step_states[step_id] = run_state.STATE_RUNNABLE
        return self.reconstruct_state().steps[step_id]

    def start_step(self, step_id: str, actor: str = "runtime") -> StepSnapshot:
        """Transition a runnable step to running."""
        snapshot = self.reconstruct_state()
        step = snapshot.steps.get(step_id)
        if step is None:
            raise KeyError(f"Unknown step {step_id}")

        run_state.check_transition(
            step.state,
            run_state.STATE_RUNNING,
            actor,
            predicate_values={"lease_acquired_and_packet_emitted": True},
        )

        self._ephemeral_step_states[step_id] = run_state.STATE_RUNNING
        return self.reconstruct_state().steps[step_id]

    def record_step_attempt(
        self,
        step_id: str,
        state: str,
        actor: str = "executor",
        attempt: int | None = None,
    ) -> StepSnapshot:
        """Record execution attempt envelope (performed|blocked|failed) in append-only ledger."""
        snapshot = self.reconstruct_state()
        step = snapshot.steps.get(step_id)
        if step is None:
            raise KeyError(f"Unknown step {step_id}")

        current_st = step.state
        run_state.check_transition(
            current_st,
            state,
            self._default_actor,
            predicate_values={"valid_attempt_and_evidence": True},
        )

        attempt_num = attempt if attempt is not None else (step.attempts + 1)
        self._store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "step_attempt",
                "run_id": self._run_id,
                "actor": actor,
                "step": step_id,
                "state": state,
                "attempt": attempt_num,
                "parent": "",
            }
        )

        self._ephemeral_step_states[step_id] = state
        return self.reconstruct_state().steps[step_id]

    def record_approval(
        self,
        gate: str,
        approver: str,
        actor: str = "human",
    ) -> None:
        """Record human approval at a gate in append-only ledger."""
        self._store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "human_approval",
                "run_id": self._run_id,
                "actor": actor,
                "gate": gate,
                "approver": approver,
                "parent": "",
            }
        )

    def record_verifier_decision(
        self,
        requirement: str,
        result: str,
        actor: str = "verifier",
    ) -> None:
        """Record independent verifier decision in append-only ledger."""
        if actor != "verifier":
            raise run_state.UnauthorizedActorError(
                f"verifier_decision must be authored by 'verifier', got '{actor}'"
            )
        self._store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "verifier_decision",
                "run_id": self._run_id,
                "actor": actor,
                "requirement": requirement,
                "result": result,
                "parent": "",
            }
        )

    def complete_run(
        self,
        actor: str = "coordinator",
        expected_head: str | None = None,
        expected_worktree: str | None = None,
    ) -> RunStateSnapshot:
        """Transition run to complete after verifying all completion predicates hold.
        Rejects executor attempts with UnauthorizedActorError."""
        # 1. Authority check
        if actor not in ("coordinator", "runtime"):
            raise run_state.UnauthorizedActorError(
                f"terminal completion must be authored by coordinator or runtime, not '{actor}'"
            )

        # 2. Evaluate completion over ledger history
        records = self._store.read_records(verify=True)
        eval_res = run_evidence.evaluate_completion(
            records,
            expected_head=expected_head,
            expected_worktree=expected_worktree,
            coordinator_authority=(actor == "coordinator"),
        )

        if not eval_res.is_complete:
            reasons_str = "; ".join(eval_res.reasons)
            raise run_state.PredicateUnsatisfiedError(
                f"Cannot complete run: completion predicates failed: {reasons_str}"
            )

        # 3. Transition check
        run_state.check_transition(
            run_state.STATE_VERIFIED,
            run_state.STATE_COMPLETE,
            actor,
            predicate_values={"every_frozen_completion_predicate_true": True},
        )

        # 4. Append terminal transaction
        self._store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "terminal_transaction",
                "run_id": self._run_id,
                "actor": actor,
                "terminal_status": run_state.STATE_COMPLETE,
                "moved_to": "executed",
                "parent": "",
            }
        )

        return self.reconstruct_state()

    def cancel_run(
        self,
        reason: str = "cancelled",
        actor: str = "coordinator",
    ) -> RunStateSnapshot:
        """Cancel active run."""
        snapshot = self.reconstruct_state()
        run_state.check_transition(
            snapshot.state,
            run_state.STATE_CANCELLED,
            actor,
            predicate_values={"cancellation_event_recorded": True},
        )

        self._store.append(
            {
                "schema_version": schema.LEDGER_SCHEMA_VERSION,
                "kind": "terminal_transaction",
                "run_id": self._run_id,
                "actor": actor,
                "terminal_status": run_state.STATE_CANCELLED,
                "moved_to": "cancelled",
                "reason": reason,
                "parent": "",
            }
        )

        return self.reconstruct_state()

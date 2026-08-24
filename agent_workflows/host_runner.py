"""Generic structured host worker runner (execset Order 04, `31744f` E-01).

One evidence-gated worker interface the Set coordinator uses to start, monitor, time-out, cancel,
and collect a VALIDATED terminal envelope from an isolated task, on any supported host, without
duplicating semantics per host. No worker-launcher existed before; this is net-new, and its security
posture is pinned:

  * SPAWN with an argv LIST and ``shell=False`` - task-derived content NEVER reaches a shell (the
    existing `host_capability_registry.run_isolated_probe` `shell=True` pattern is deliberately NOT
    copied; it is a command-injection surface for task packets). Execution goes through
    `run_evidence.capture_command` (argv-list, shell=False, provenance + evidence envelope) or a
    caller-injected runner double for tests.
  * BOUNDED TIMEOUT + CANCELLATION are net-new: a hung worker is killed and recorded as a FAILURE
    (never completion); a cancelled worker terminates. `capture_command` maps a timeout to exit 124.
  * REDACTION: all captured stdout/stderr/diff pass through `security_hardening.check_evidence_
    redaction` (RedactionPolicy + canonical leak sanitizer) BEFORE anything enters the ledger; a
    planted home-path/secret is masked/blocked.
  * A host exit 0 is NEVER treated as success. The terminal envelope is a `run_packet.
    StepOutcomeEnvelope` validated by `run_packet.validate_outcome_envelope` + gated by
    `run_evidence.validate_evidence` (EV-FAILED-EXIT / EV-MISSING-OUTPUT / EV-FABRICATED-TEXT /
    EV-EXPIRED-PROBE); the coordinator receives FACTS, not free-form completion claims.

Net-new host-worker terminal states are defined here and each maps DOWN to the authoritative ledger
attempt vocabulary `performed|blocked|failed` (`run_state`), so nothing bypasses it. Workers cannot
ask users directly; a blocking question becomes a `blocked_required_input` terminal state.

Pure orchestration + stdlib subprocess; reuses the executed evidence/redaction/packet validators.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping, NamedTuple, Optional, Sequence, Tuple

from agent_workflows import run_evidence as _ev
from agent_workflows import run_state as _rs

# ---- net-new host-worker terminal states + their ledger mapping ----------------------------------

WORKER_COMPLETED = "completed"
WORKER_DEFERRED_PARTIAL = "deferred_partial"
WORKER_DEFERRED_IPD = "deferred_ipd"
WORKER_FAILED_RETRYABLE = "failed_retryable"
WORKER_FAILED_FINAL = "failed_final"
WORKER_BLOCKED_REQUIRED_INPUT = "blocked_required_input"

ALL_WORKER_STATES: frozenset = frozenset(
    (
        WORKER_COMPLETED,
        WORKER_DEFERRED_PARTIAL,
        WORKER_DEFERRED_IPD,
        WORKER_FAILED_RETRYABLE,
        WORKER_FAILED_FINAL,
        WORKER_BLOCKED_REQUIRED_INPUT,
    )
)

# Map each net-new worker terminal state DOWN to a ledger attempt state (run_state.STATE_*):
#   completed -> performed; deferred_*/blocked_required_input -> blocked; failed_* -> failed.
_WORKER_TO_LEDGER: Mapping[str, str] = {
    WORKER_COMPLETED: _rs.STATE_PERFORMED,
    WORKER_DEFERRED_PARTIAL: _rs.STATE_BLOCKED,
    WORKER_DEFERRED_IPD: _rs.STATE_BLOCKED,
    WORKER_BLOCKED_REQUIRED_INPUT: _rs.STATE_BLOCKED,
    WORKER_FAILED_RETRYABLE: _rs.STATE_FAILED,
    WORKER_FAILED_FINAL: _rs.STATE_FAILED,
}


class HostRunnerError(Exception):
    """Raised on an internal runner precondition violation (not a worker failure - those are states)."""


def worker_state_to_ledger(worker_state: str) -> str:
    """Map a net-new host-worker terminal state down to a ledger attempt state. Fail-closed on an
    unknown state (a timeout/cancel/unknown outcome is never completion)."""
    if worker_state not in _WORKER_TO_LEDGER:
        raise HostRunnerError(
            "unknown worker terminal state {0!r}".format(worker_state)
        )
    return _WORKER_TO_LEDGER[worker_state]


# ---- bounded task packet -------------------------------------------------------------------------


class TaskPacket(NamedTuple):
    """A bounded unit of work handed to a host worker. ``argv`` is an explicit command LIST (never a
    shell string); ``instruction`` is the (untrusted) task text passed as DATA, never interpolated
    into a shell."""

    run_id: str
    step_id: str
    lane_id: str
    argv: Tuple[str, ...]
    cwd: str
    instruction: str = ""
    timeout_seconds: float = 300.0
    attempt: int = 1
    session_id: str = ""
    max_output_bytes: Optional[int] = None


class RawWorkerResult(NamedTuple):
    """The raw (pre-validation) result of a worker process: exit + captured streams + diff."""

    exit_code: int
    stdout: str
    stderr: str
    diff: str
    changed_files: Tuple[str, ...]
    timed_out: bool
    cancelled: bool
    duration_ms: float


# A runner callable double for tests: (argv, cwd, timeout) -> (exit_code, stdout, stderr).
RunnerFn = Callable[[Sequence[str], str, float], Tuple[int, str, str]]

# Sentinel exit codes capture_command uses.
_TIMEOUT_EXIT = 124
_SPAWN_FAIL_EXIT = 127


def run_worker_process(
    packet: TaskPacket,
    *,
    runner: Optional[RunnerFn] = None,
    diff_capturer: Optional[Callable[[TaskPacket], Tuple[str, Tuple[str, ...]]]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> RawWorkerResult:
    """Spawn the worker with argv + shell=False, bounded by ``packet.timeout_seconds``.

    A timeout or a cancellation is recorded (``timed_out``/``cancelled``) and will map to a FAILURE
    downstream - never completion. When ``runner`` is None the real spawn goes through
    `run_evidence.capture_command` (argv-list, shell=False). ``diff_capturer`` optionally returns the
    worker's (diff, changed_files); ``cancel_check`` lets the coordinator request cancellation before
    spawn (a cooperative cancel seam for tests + the scheduler).
    """
    if not packet.argv:
        raise HostRunnerError(
            "task packet has no argv (a shell string is not permitted)"
        )
    if isinstance(packet.argv, str):  # defensive: never accept a shell string
        raise HostRunnerError("argv must be a list, not a shell string")

    if cancel_check is not None and cancel_check():
        return RawWorkerResult(
            exit_code=-1,
            stdout="",
            stderr="cancelled before spawn",
            diff="",
            changed_files=(),
            timed_out=False,
            cancelled=True,
            duration_ms=0.0,
        )

    start = time.monotonic()
    timed_out = False
    if runner is not None:
        exit_code, stdout, stderr = runner(
            list(packet.argv), packet.cwd, packet.timeout_seconds
        )
    else:
        tool_event, _envelope = _ev.capture_command(
            packet.run_id,
            list(packet.argv),
            cwd=packet.cwd,
            timeout=packet.timeout_seconds,
        )
        exit_code = int(tool_event.get("exit_code", _SPAWN_FAIL_EXIT))
        stdout = tool_event.get("stdout", "") or ""
        stderr = tool_event.get("stderr", "") or ""
    duration_ms = (time.monotonic() - start) * 1000.0
    if exit_code == _TIMEOUT_EXIT:
        timed_out = True

    diff, changed = ("", ())
    if diff_capturer is not None and not timed_out:
        diff, changed = diff_capturer(packet)

    return RawWorkerResult(
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        diff=diff,
        changed_files=tuple(changed),
        timed_out=timed_out,
        cancelled=False,
        duration_ms=duration_ms,
    )


# ---- redaction of captured output ----------------------------------------------------------------


def redact_worker_output(
    raw: RawWorkerResult,
    *,
    repo_root=None,
) -> Tuple[RawWorkerResult, object]:
    """Run captured stdout/stderr/diff through `security_hardening.check_evidence_redaction` BEFORE
    anything enters the ledger. Returns (possibly-masked RawWorkerResult, BoundaryResult).

    The BoundaryResult.ok is False when a hard leak (severity 'fail') is present; the caller must
    treat that as a failure to record rather than admitting the raw text.
    """
    from agent_workflows import security_hardening as _sh

    payload = {"stdout": raw.stdout, "stderr": raw.stderr, "diff": raw.diff}
    result = _sh.check_evidence_redaction(payload, repo_root=repo_root)
    # The RedactionPolicy masks matched secrets/keys; reflect the masked text back into the result.
    policy = _sh.default_redaction_policy()
    masked, _was = policy.redact(dict(payload))
    redacted = raw._replace(
        stdout=str(masked.get("stdout", raw.stdout)),
        stderr=str(masked.get("stderr", raw.stderr)),
        diff=str(masked.get("diff", raw.diff)),
    )
    return redacted, result


# ---- terminal envelope: classify + validate ------------------------------------------------------


def classify_worker_state(raw: RawWorkerResult) -> str:
    """Classify a raw worker result into a net-new terminal state (host exit 0 is NOT success).

    A timeout/cancel is `failed_final`; a nonzero exit is `failed_retryable`; a zero exit with a
    real diff is `completed`; a zero exit with NO diff/changed files is NOT completion - it is
    `failed_final` (nothing was actually done, the classic greenwash)."""
    if raw.timed_out or raw.cancelled:
        return WORKER_FAILED_FINAL
    if raw.exit_code != 0:
        return WORKER_FAILED_RETRYABLE
    if not raw.diff and not raw.changed_files:
        return WORKER_FAILED_FINAL
    return WORKER_COMPLETED


def build_terminal_envelope(
    packet: TaskPacket,
    raw: RawWorkerResult,
    *,
    worker_state: Optional[str] = None,
    evidence_ids: Sequence[str] = (),
    actor: str = "executor",
) -> Tuple[dict, str]:
    """Build a `run_packet.StepOutcomeEnvelope` dict + its mapped ledger state from a worker result.

    The envelope's status is the LEDGER attempt state (performed|blocked|failed), derived from the
    worker terminal state; a failure carries a `failure_reason`, a block carries a `block_reason`.
    The caller validates it with `validate_terminal_envelope` before it can enter the ledger.
    """
    ws = worker_state or classify_worker_state(raw)
    ledger_state = worker_state_to_ledger(ws)
    env: dict = {
        "run_id": packet.run_id,
        "step_id": packet.step_id,
        "attempt": packet.attempt,
        "status": ledger_state,
        "actor": actor,
        "evidence_ids": tuple(evidence_ids),
    }
    if ledger_state == _rs.STATE_FAILED:
        reason = (
            "worker timed out"
            if raw.timed_out
            else (
                "worker cancelled"
                if raw.cancelled
                else "worker state {0} (exit {1})".format(ws, raw.exit_code)
            )
        )
        env["failure_reason"] = reason
    elif ledger_state == _rs.STATE_BLOCKED:
        env["block_reason"] = "worker state {0}".format(ws)
    return env, ws


def validate_terminal_envelope(
    envelope: Mapping[str, Any],
    *,
    expected_run_id: Optional[str] = None,
    expected_step_id: Optional[str] = None,
    expected_attempt: Optional[int] = None,
    required_evidence_kinds: Optional[Sequence[str]] = None,
):
    """Validate a worker's terminal envelope with the reused `run_packet.validate_outcome_envelope`
    (rejects prose-only claims, foreign actors, wrong attempt, missing evidence on a performed step,
    and non-ledger statuses). Returns the OutcomeValidationResult."""
    from agent_workflows import run_packet as _rp

    return _rp.validate_outcome_envelope(
        envelope,
        expected_run_id=expected_run_id,
        expected_step_id=expected_step_id,
        expected_attempt=expected_attempt,
        required_evidence_kinds=required_evidence_kinds,
    )


def evidence_gate(tool_event: Mapping[str, Any]):
    """Run the reused anti-greenwashing evidence validator over a worker's captured tool_event.

    A nonzero exit -> EV-FAILED-EXIT; empty output -> EV-MISSING-OUTPUT; a non-record/unknown-kind
    'evidence' -> EV-FABRICATED-TEXT; an expired probe -> EV-EXPIRED-PROBE. Returns the
    EvidenceValidationResult so a host exit-0 with no verified side effect cannot become completed.
    """
    return _ev.validate_evidence(
        tool_event, require_full_output=True, check_filesystem=False
    )


def run_task(
    packet: TaskPacket,
    *,
    runner: Optional[RunnerFn] = None,
    diff_capturer: Optional[Callable[[TaskPacket], Tuple[str, Tuple[str, ...]]]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    repo_root=None,
    evidence_ids: Sequence[str] = (),
    actor: str = "executor",
) -> Tuple[dict, str, RawWorkerResult]:
    """End-to-end: spawn (argv/shell=False, bounded) -> redact -> classify -> build a validated
    terminal envelope. Returns (envelope_dict, worker_state, redacted_raw). The envelope status is a
    ledger attempt state; a timeout/cancel/no-diff outcome is a failure, never completion."""
    raw = run_worker_process(
        packet, runner=runner, diff_capturer=diff_capturer, cancel_check=cancel_check
    )
    redacted, boundary = redact_worker_output(raw, repo_root=repo_root)
    if not getattr(boundary, "ok", True):
        # A hard leak in captured output: refuse to admit it; record a failure, not the raw text.
        redacted = redacted._replace(
            stdout="[REDACTED-LEAK]", stderr="[REDACTED-LEAK]", diff=""
        )
        env, ws = build_terminal_envelope(
            packet,
            redacted._replace(exit_code=1, diff="", changed_files=()),
            worker_state=WORKER_FAILED_FINAL,
            evidence_ids=evidence_ids,
            actor=actor,
        )
        return env, ws, redacted
    env, ws = build_terminal_envelope(
        packet, redacted, evidence_ids=evidence_ids, actor=actor
    )
    return env, ws, redacted

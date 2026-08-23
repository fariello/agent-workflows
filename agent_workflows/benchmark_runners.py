"""Runner contracts, live runner adapters, and offline doubles for the benchmark harness.

awoptimize Order 13 (`9ihhzr`) E-01.

This module implements:
  1. The live runner ADAPTERS for:
       - GPT-5.6 Sol
       - Gemini 3.7 Flash with medium thinking
       - Claude Opus 5
       - GLM-5.3 with declared reasoning
     on each authorized host (opencode, codex, kiro, gemini_cli, claude_code, antigravity).
  2. The offline runner DOUBLES covering all eight specified execution outcomes:
       - success
       - malformed stream
       - timeout
       - turn limit
       - exceeded ceiling
       - permission denial
       - missing executable
       - missing credentials
     Each non-success outcome produces a structured `pending` result with the exact operator rerun
     command, never guessed or fabricated data.
  3. The hard HUMAN/AGENT execution gate: live model runs are strictly operator-run; the harness
     refuses executor-agent live invocation.

Pure + stdlib-only (D138; D139).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from agent_workflows.benchmark_corpus import SeededTask
from agent_workflows.benchmark_manifest import (
    UNAVAILABLE,
    BenchmarkManifest,
    Ceilings,
    build_manifest,
    make_ceilings,
    make_usage,
)
from agent_workflows.benchmark_scorer import ScoreResult, score_transcript

RUNNERS_SCHEMA_VERSION = 1

# ---- Supported Models -----------------------------------------------------------------------------

MODEL_GPT_5_6_SOL = "gpt-5.6-sol"
MODEL_GEMINI_3_7_FLASH = "gemini-3.7-flash"
MODEL_CLAUDE_OPUS_5 = "claude-opus-5"
MODEL_GLM_5_3 = "glm-5.3"

# All authorized models for the benchmark harness.
SUPPORTED_BENCHMARK_MODELS: Tuple[str, ...] = (
    MODEL_GPT_5_6_SOL,
    MODEL_GEMINI_3_7_FLASH,
    MODEL_CLAUDE_OPUS_5,
    MODEL_GLM_5_3,
)

# Authorized hosts for running benchmark trials.
SUPPORTED_BENCHMARK_HOSTS: Tuple[str, ...] = (
    "opencode",
    "codex",
    "kiro",
    "gemini_cli",
    "claude_code",
    "antigravity",
)

# Default reasoning effort settings per model.
DEFAULT_MODEL_REASONING: Dict[str, str] = {
    MODEL_GPT_5_6_SOL: "none",
    MODEL_GEMINI_3_7_FLASH: "medium",
    MODEL_CLAUDE_OPUS_5: "none",
    MODEL_GLM_5_3: "declared",
}


@dataclass(frozen=True)
class ModelProfile:
    """A configured model + reasoning level for a benchmark run."""

    model_id: str
    reasoning_effort: str
    display_name: str
    vendor: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "model_id": self.model_id,
            "reasoning_effort": self.reasoning_effort,
            "display_name": self.display_name,
            "vendor": self.vendor,
        }


# Standard profiles for the four required models.
STANDARD_PROFILES: Dict[str, ModelProfile] = {
    MODEL_GPT_5_6_SOL: ModelProfile(
        model_id=MODEL_GPT_5_6_SOL,
        reasoning_effort="none",
        display_name="GPT-5.6 Sol",
        vendor="openai",
    ),
    MODEL_GEMINI_3_7_FLASH: ModelProfile(
        model_id=MODEL_GEMINI_3_7_FLASH,
        reasoning_effort="medium",
        display_name="Gemini 3.7 Flash (medium thinking)",
        vendor="google",
    ),
    MODEL_CLAUDE_OPUS_5: ModelProfile(
        model_id=MODEL_CLAUDE_OPUS_5,
        reasoning_effort="none",
        display_name="Claude Opus 5",
        vendor="anthropic",
    ),
    MODEL_GLM_5_3: ModelProfile(
        model_id=MODEL_GLM_5_3,
        reasoning_effort="declared",
        display_name="GLM-5.3 (declared reasoning)",
        vendor="zhipu",
    ),
}


# ---- Failure Kinds -------------------------------------------------------------------------------

FAILURE_MALFORMED_STREAM = "malformed_stream"
FAILURE_TIMEOUT = "timeout"
FAILURE_TURN_LIMIT = "turn_limit"
FAILURE_EXCEEDED_CEILING = "exceeded_ceiling"
FAILURE_PERMISSION_DENIAL = "permission_denial"
FAILURE_MISSING_EXECUTABLE = "missing_executable"
FAILURE_MISSING_CREDENTIALS = "missing_credentials"

ALL_RUNNER_FAILURE_KINDS: Tuple[str, ...] = (
    FAILURE_MALFORMED_STREAM,
    FAILURE_TIMEOUT,
    FAILURE_TURN_LIMIT,
    FAILURE_EXCEEDED_CEILING,
    FAILURE_PERMISSION_DENIAL,
    FAILURE_MISSING_EXECUTABLE,
    FAILURE_MISSING_CREDENTIALS,
)


class RunnerError(Exception):
    """Raised on runner construction or execution contract errors."""


class LiveExecutionProhibitedError(RunnerError):
    """Raised when an executor agent attempts to invoke a live model."""


# ---- Trial Result --------------------------------------------------------------------------------


@dataclass
class TrialResult:
    """The result of a single benchmark trial.

    If status is "pending", the trial could not be executed or failed to complete honestly (e.g.
    timeout, missing credentials, malformed stream). The exact rerun command is ALWAYS present so an
    operator can run or reproduce it manually. Usage fields are present or `unavailable` - never
    guessed.
    """

    trial_id: str
    status: str  # "completed" | "pending"
    manifest: BenchmarkManifest
    rerun_command: str
    failure_kind: Optional[str] = (
        None  # one of ALL_RUNNER_FAILURE_KINDS if status == "pending"
    )
    error_message: Optional[str] = None
    transcript: Optional[Dict[str, Any]] = None
    score_result: Optional[ScoreResult] = None
    usage: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def is_success(self) -> bool:
        return (
            self.status == "completed"
            and self.score_result is not None
            and self.score_result.verdict == "complete"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "status": self.status,
            "manifest": self.manifest.to_dict(),
            "rerun_command": self.rerun_command,
            "failure_kind": self.failure_kind,
            "error_message": self.error_message,
            "transcript": self.transcript,
            "score_result": (
                {
                    "verdict": self.score_result.verdict,
                    "adversary_class": self.score_result.adversary_class,
                    "reasons": list(self.score_result.reasons),
                    "claimed_complete": self.score_result.claimed_complete,
                }
                if self.score_result
                else None
            ),
            "usage": self.usage,
        }


# ---- Live Runner Adapter -------------------------------------------------------------------------


class RunnerAdapter:
    """Builds host-specific CLI invocations and rerun commands for benchmark trials."""

    def __init__(
        self,
        host: str,
        host_version: str = "1.0.0",
        extra_flags: Optional[Sequence[str]] = None,
    ) -> None:
        if host not in SUPPORTED_BENCHMARK_HOSTS:
            raise RunnerError(f"Unsupported benchmark host: {host!r}")
        self.host = host
        self.host_version = host_version
        self.extra_flags = tuple(extra_flags or ())

    def adapter_digest(self) -> str:
        """Deterministic digest of this adapter's host configuration and flags."""
        data = {
            "host": self.host,
            "host_version": self.host_version,
            "extra_flags": self.extra_flags,
        }
        raw = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def build_command(
        self,
        model_profile: ModelProfile,
        task: SeededTask | Mapping[str, Any],
        workspace_path: Path | str,
        *,
        timeout_seconds: float = 300.0,
        turn_limit: int = 30,
        token_ceiling: Optional[int] = None,
    ) -> List[str]:
        """Construct the exact CLI command list for running the trial on this host."""
        workspace = str(workspace_path)
        task_desc = task.task if isinstance(task, SeededTask) else dict(task)
        prompt = task_desc.get("prompt", "Execute task")

        cmd: List[str] = []
        host = self.host

        if host == "opencode":
            cmd = [
                "opencode",
                "run",
                "--format",
                "json",
                "--model",
                model_profile.model_id,
            ]
            if model_profile.reasoning_effort != "none":
                cmd.extend(["--reasoning-effort", model_profile.reasoning_effort])
            cmd.extend(["--cwd", workspace, "--timeout", str(int(timeout_seconds))])
            if turn_limit > 0:
                cmd.extend(["--max-turns", str(turn_limit)])
            if token_ceiling:
                cmd.extend(["--max-tokens", str(token_ceiling)])
            cmd.append(prompt)

        elif host == "codex":
            cmd = ["codex", "exec", "--model", model_profile.model_id]
            if model_profile.reasoning_effort != "none":
                cmd.extend(["--effort", model_profile.reasoning_effort])
            cmd.extend(["--cd", workspace, "--timeout", f"{int(timeout_seconds)}s"])
            cmd.append(prompt)

        elif host == "kiro":
            cmd = [
                "kiro-cli",
                "chat",
                "--no-interactive",
                "--model",
                model_profile.model_id,
            ]
            if model_profile.reasoning_effort != "none":
                cmd.extend(["--reasoning", model_profile.reasoning_effort])
            cmd.extend(["--workdir", workspace])
            cmd.append(prompt)

        elif host == "gemini_cli":
            cmd = [
                "gemini",
                "-p",
                "--output-format",
                "stream-json",
                "--model",
                model_profile.model_id,
            ]
            if model_profile.reasoning_effort != "none":
                cmd.extend(["--thinking", model_profile.reasoning_effort])
            cmd.extend(["--dir", workspace, "--timeout", str(int(timeout_seconds))])
            cmd.append(prompt)

        elif host == "claude_code":
            cmd = ["claude", "-p", "--model", model_profile.model_id]
            if model_profile.reasoning_effort != "none":
                cmd.extend(["--thinking", model_profile.reasoning_effort])
            cmd.extend(["--cwd", workspace, "--timeout", str(int(timeout_seconds))])
            cmd.append(prompt)

        elif host == "antigravity":
            cmd = ["agy", "run", "--model", model_profile.model_id]
            if model_profile.reasoning_effort != "none":
                cmd.extend(["--reasoning", model_profile.reasoning_effort])
            cmd.extend(
                ["--workspace", workspace, "--timeout", str(int(timeout_seconds))]
            )
            cmd.append(prompt)

        if self.extra_flags:
            cmd.extend(self.extra_flags)

        return cmd

    def build_rerun_command(
        self,
        model_profile: ModelProfile,
        task: SeededTask | Mapping[str, Any],
        workspace_path: Path | str,
        *,
        timeout_seconds: float = 300.0,
        turn_limit: int = 30,
        token_ceiling: Optional[int] = None,
    ) -> str:
        """Construct the exact standalone rerun shell command string for operator reproduction."""
        cmd = self.build_command(
            model_profile,
            task,
            workspace_path,
            timeout_seconds=timeout_seconds,
            turn_limit=turn_limit,
            token_ceiling=token_ceiling,
        )
        # Format safely for bash execution
        parts = []
        for part in cmd:
            if " " in part or "\n" in part or '"' in part or "'" in part:
                escaped = part.replace('"', '\\"')
                parts.append(f'"{escaped}"')
            else:
                parts.append(part)
        return " ".join(parts)


def get_adapter(host: str, host_version: str = "1.0.0") -> RunnerAdapter:
    """Factory for getting a host runner adapter."""
    return RunnerAdapter(host=host, host_version=host_version)


# ---- Runner Double (Offline Test Double) ----------------------------------------------------------


class RunnerDouble:
    """Offline test double for runner adapters.

    Simulates trial executions without network or live model calls. Supports simulating:
      - success (with synthetic transcript and honest usage)
      - malformed stream
      - timeout
      - turn limit
      - exceeded ceiling
      - permission denial
      - missing executable
      - missing credentials

    Every non-success outcome yields a structured `pending` result with an exact rerun command.
    """

    def __init__(
        self,
        adapter: RunnerAdapter,
        *,
        default_outcome: str = "success",
        programmed_responses: Optional[Mapping[Tuple[str, str, int], Any]] = None,
    ) -> None:
        self.adapter = adapter
        self.default_outcome = default_outcome
        # key: (model_id, seed_id, trial) -> outcome string or dict
        self.programmed_responses: Dict[Tuple[str, str, int], Any] = dict(
            programmed_responses or {}
        )

    def program_outcome(
        self,
        model_id: str,
        seed_id: str,
        trial: int,
        outcome: str | Dict[str, Any],
    ) -> None:
        """Program a specific outcome for a particular trial."""
        self.programmed_responses[(model_id, seed_id, trial)] = outcome

    def run_trial(
        self,
        task: SeededTask,
        model_profile: ModelProfile,
        trial: int,
        *,
        timeout_seconds: float = 300.0,
        ceilings: Optional[Ceilings] = None,
        workspace_path: Optional[Path | str] = None,
        ground_truth: Optional[Mapping[str, Any]] = None,
        host_reports_tokens: bool = False,
    ) -> TrialResult:
        """Run an offline simulated trial, strictly with doubles (no live invocation)."""
        ceil = ceilings or make_ceilings(
            per_trial_wall_seconds=timeout_seconds,
            trial_count=1,
            host_reports_tokens=host_reports_tokens,
        )
        ws = workspace_path or f"/tmp/bench_workspace/{task.seed_id}_{trial}"
        trial_id = (
            f"{task.seed_id}_{model_profile.model_id}_{self.adapter.host}_t{trial}"
        )

        rerun_cmd = self.adapter.build_rerun_command(
            model_profile,
            task,
            ws,
            timeout_seconds=timeout_seconds,
            token_ceiling=ceil.token_ceiling,
        )

        outcome = self.programmed_responses.get(
            (model_profile.model_id, task.seed_id, trial),
            self.default_outcome,
        )

        # Handle programmed outcome string or response dict
        outcome_kind = (
            outcome if isinstance(outcome, str) else outcome.get("kind", "success")
        )

        # 1. Success Outcome
        if outcome_kind == "success":
            wall_time = (
                1.25
                if not isinstance(outcome, dict)
                else float(outcome.get("wall_time", 1.25))
            )
            token_val = (
                outcome.get("tokens", 450)
                if (isinstance(outcome, dict) and "tokens" in outcome)
                else (450 if host_reports_tokens else UNAVAILABLE)
            )
            credits_val = (
                outcome.get("credits_or_quota", UNAVAILABLE)
                if isinstance(outcome, dict)
                else UNAVAILABLE
            )

            usage = make_usage(
                wall_time=wall_time,
                tokens=token_val,
                credits_or_quota=credits_val,
            )

            manifest = build_manifest(
                model_id=model_profile.model_id,
                reasoning_effort=model_profile.reasoning_effort,
                host=self.adapter.host,
                host_version=self.adapter.host_version,
                adapter_digest=self.adapter.adapter_digest(),
                workflow_digest="0" * 64,
                tool_policy_digest="0" * 64,
                task_seed=task.seed_id,
                trial=trial,
                timeout_seconds=timeout_seconds,
                ceilings=ceil,
                environment_fingerprint="0" * 64,
                usage=usage,
            )

            # Build synthetic honest transcript
            transcript: Dict[str, Any] = {
                "claimed_complete": True,
                "performed_instructions": (
                    list(ground_truth.get("required_instructions", []))
                    if ground_truth
                    else ["step1"]
                ),
                "checked_requirements": (
                    list(ground_truth.get("required_requirements", []))
                    if ground_truth
                    else ["req1"]
                ),
                "requirement_results": (
                    {
                        r: "satisfied"
                        for r in ground_truth.get("required_requirements", [])
                    }
                    if ground_truth
                    else {"req1": "satisfied"}
                ),
                "post_test_count": ground_truth.get("reference_test_count", 5)
                if ground_truth
                else 5,
                "post_assertion_count": ground_truth.get(
                    "reference_assertion_count", 10
                )
                if ground_truth
                else 10,
                "wired_symbols": list(ground_truth.get("must_wire_symbols", []))
                if ground_truth
                else [],
                "touched_paths": list(ground_truth.get("scope_fence_paths", []))
                if ground_truth
                else [],
                "produced_artifacts": list(ground_truth.get("required_artifacts", []))
                if ground_truth
                else [],
                "confirmed_assumptions": list(ground_truth.get("gated_assumptions", []))
                if ground_truth
                else [],
                "ledger": [],
            }
            if isinstance(outcome, dict) and "transcript" in outcome:
                transcript.update(outcome["transcript"])

            score_res = score_transcript(ground_truth or {}, transcript)

            return TrialResult(
                trial_id=trial_id,
                status="completed",
                manifest=manifest,
                rerun_command=rerun_cmd,
                failure_kind=None,
                error_message=None,
                transcript=transcript,
                score_result=score_res,
                usage=usage,
            )

        # 2. Non-Success / Pending Outcomes
        error_messages = {
            FAILURE_MALFORMED_STREAM: "Malformed response stream received from host process",
            FAILURE_TIMEOUT: f"Execution exceeded per-trial timeout of {timeout_seconds}s",
            FAILURE_TURN_LIMIT: "Execution exceeded maximum configured turn limit",
            FAILURE_EXCEEDED_CEILING: "Enforcement ceiling exceeded during execution",
            FAILURE_PERMISSION_DENIAL: "Tool execution permission denied by host environment",
            FAILURE_MISSING_EXECUTABLE: f"Host executable '{self.adapter.host}' not found on PATH",
            FAILURE_MISSING_CREDENTIALS: f"Required credentials missing for model '{model_profile.model_id}'",
        }

        failure_kind = outcome_kind
        err_msg = (
            outcome.get("error_message")
            if isinstance(outcome, dict) and "error_message" in outcome
            else error_messages.get(failure_kind, f"Trial failed with {failure_kind}")
        )

        # Pending trials report wall_time if elapsed, but never fabricate tokens
        elapsed_wall = (
            float(outcome.get("wall_time", 0.0)) if isinstance(outcome, dict) else 0.0
        )
        usage = make_usage(
            wall_time=elapsed_wall,
            tokens=UNAVAILABLE,
            credits_or_quota=UNAVAILABLE,
        )

        manifest = build_manifest(
            model_id=model_profile.model_id,
            reasoning_effort=model_profile.reasoning_effort,
            host=self.adapter.host,
            host_version=self.adapter.host_version,
            adapter_digest=self.adapter.adapter_digest(),
            workflow_digest="0" * 64,
            tool_policy_digest="0" * 64,
            task_seed=task.seed_id,
            trial=trial,
            timeout_seconds=timeout_seconds,
            ceilings=ceil,
            environment_fingerprint="0" * 64,
            usage=usage,
        )

        return TrialResult(
            trial_id=trial_id,
            status="pending",
            manifest=manifest,
            rerun_command=rerun_cmd,
            failure_kind=failure_kind,
            error_message=err_msg,
            transcript=None,
            score_result=None,
            usage=usage,
        )


# ---- Live Execution Gate (Hard Human/Agent Boundary) ---------------------------------------------


def execute_live_runner(
    adapter: RunnerAdapter,
    model_profile: ModelProfile,
    task: SeededTask,
    trial: int,
    *,
    operator_authorized: bool = False,
) -> TrialResult:
    """Gate for live model execution.

    Enforces the non-negotiable rule: an executing agent MUST NOT invoke paid or live models.
    If called by an agent without explicit human operator authorization, it refuses live execution
    and produces a structured `pending` result with the exact rerun command for the operator.
    """
    if not operator_authorized:
        rerun_cmd = adapter.build_rerun_command(
            model_profile,
            task,
            str(task.workspace_seed_path()),
        )
        manifest = build_manifest(
            model_id=model_profile.model_id,
            reasoning_effort=model_profile.reasoning_effort,
            host=adapter.host,
            host_version=adapter.host_version,
            adapter_digest=adapter.adapter_digest(),
            workflow_digest="0" * 64,
            tool_policy_digest="0" * 64,
            task_seed=task.seed_id,
            trial=trial,
            timeout_seconds=300.0,
            ceilings=make_ceilings(per_trial_wall_seconds=300.0, trial_count=1),
            environment_fingerprint="0" * 64,
            usage=make_usage(0.0),
        )
        return TrialResult(
            trial_id=f"{task.seed_id}_{model_profile.model_id}_{adapter.host}_t{trial}",
            status="pending",
            manifest=manifest,
            rerun_command=rerun_cmd,
            failure_kind="live_execution_operator_gated",
            error_message=(
                "Live model invocation is strictly operator-run (human/agent boundary enforced). "
                f"Run manually using: {rerun_cmd}"
            ),
            transcript=None,
            score_result=None,
            usage=make_usage(0.0),
        )

    # In live mode (run manually by human operator), would invoke subprocess.
    # But for v1 harness, offline doubles are used.
    raise LiveExecutionProhibitedError(
        "Live execution must be performed directly in shell by operator"
    )

"""Architecture ablations and paired-comparison scheduler for the benchmark harness.

awoptimize Order 13 (`9ihhzr`) E-02.

This module implements:
  1. The six required benchmark architecture configurations:
       - monolithic prompt (`monolith`)
       - modular skill (`modular`)
       - deterministic runtime (`runtime`)
       - runtime + same-session audit (`runtime_same_session_audit`)
       - runtime + fresh verifier (`runtime_fresh_verifier`)
       - runtime + cross-model verifier (`runtime_cross_model_verifier`)
  2. The ablation scheduler:
       - holds task seed and configuration constant across architecture variants
       - randomizes execution ordering deterministically with a random seed
       - labels isolation level and verifier identity
       - generates paired comparisons without pooling incompatible cells.

Pure + stdlib-only (D138; D139).
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from agent_workflows.benchmark_manifest import (
    Ceilings,
    make_ceilings,
)
from agent_workflows.benchmark_runners import ModelProfile, TrialResult

ABLATIONS_SCHEMA_VERSION = 1

# ---- Architectures -------------------------------------------------------------------------------

ARCH_MONOLITH = "monolith"
ARCH_MODULAR = "modular"
ARCH_RUNTIME = "runtime"
ARCH_RUNTIME_SAME_SESSION_AUDIT = "runtime_same_session_audit"
ARCH_RUNTIME_FRESH_VERIFIER = "runtime_fresh_verifier"
ARCH_RUNTIME_CROSS_MODEL_VERIFIER = "runtime_cross_model_verifier"

ALL_ABLATION_ARCHITECTURES: Tuple[str, ...] = (
    ARCH_MONOLITH,
    ARCH_MODULAR,
    ARCH_RUNTIME,
    ARCH_RUNTIME_SAME_SESSION_AUDIT,
    ARCH_RUNTIME_FRESH_VERIFIER,
    ARCH_RUNTIME_CROSS_MODEL_VERIFIER,
)

# Isolation levels
ISOLATION_NONE = "none"
ISOLATION_PACKAGE = "package"
ISOLATION_RUNTIME = "runtime_isolated"
ISOLATION_SAME_SESSION = "same_session"
ISOLATION_FRESH_SESSION = "fresh_session"
ISOLATION_CROSS_MODEL = "cross_model"

# Verifier identities
VERIFIER_NONE = "none"
VERIFIER_SELF = "self_session"
VERIFIER_FRESH_SAME_MODEL = "fresh_same_model"
VERIFIER_CROSS_MODEL = "cross_model"


@dataclass(frozen=True)
class AblationConfig:
    """Configuration for a specific architectural ablation variant."""

    architecture: str
    isolation_level: str
    verifier_identity: str
    cross_verifier_model_id: Optional[str] = None
    description: str = ""

    def digest(self) -> str:
        data = {
            "architecture": self.architecture,
            "isolation_level": self.isolation_level,
            "verifier_identity": self.verifier_identity,
            "cross_verifier_model_id": self.cross_verifier_model_id,
        }
        raw = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "architecture": self.architecture,
            "isolation_level": self.isolation_level,
            "verifier_identity": self.verifier_identity,
            "cross_verifier_model_id": self.cross_verifier_model_id,
            "description": self.description,
            "digest": self.digest(),
        }


# Standard configs for the six architectures.
STANDARD_ABLATION_CONFIGS: Dict[str, AblationConfig] = {
    ARCH_MONOLITH: AblationConfig(
        architecture=ARCH_MONOLITH,
        isolation_level=ISOLATION_NONE,
        verifier_identity=VERIFIER_NONE,
        description="Monolithic single prompt without subagents or modular skills",
    ),
    ARCH_MODULAR: AblationConfig(
        architecture=ARCH_MODULAR,
        isolation_level=ISOLATION_PACKAGE,
        verifier_identity=VERIFIER_NONE,
        description="Modular skill router with on-demand skill packages",
    ),
    ARCH_RUNTIME: AblationConfig(
        architecture=ARCH_RUNTIME,
        isolation_level=ISOLATION_RUNTIME,
        verifier_identity=VERIFIER_NONE,
        description="Deterministic state machine and workflow runtime engine",
    ),
    ARCH_RUNTIME_SAME_SESSION_AUDIT: AblationConfig(
        architecture=ARCH_RUNTIME_SAME_SESSION_AUDIT,
        isolation_level=ISOLATION_SAME_SESSION,
        verifier_identity=VERIFIER_SELF,
        description="Runtime with evidence audit performed within the same session",
    ),
    ARCH_RUNTIME_FRESH_VERIFIER: AblationConfig(
        architecture=ARCH_RUNTIME_FRESH_VERIFIER,
        isolation_level=ISOLATION_FRESH_SESSION,
        verifier_identity=VERIFIER_FRESH_SAME_MODEL,
        description="Runtime with independent fresh-session verifier using the same model",
    ),
    ARCH_RUNTIME_CROSS_MODEL_VERIFIER: AblationConfig(
        architecture=ARCH_RUNTIME_CROSS_MODEL_VERIFIER,
        isolation_level=ISOLATION_CROSS_MODEL,
        verifier_identity=VERIFIER_CROSS_MODEL,
        cross_verifier_model_id="claude-opus-5",
        description="Runtime with cross-model verifier for independent evaluation",
    ),
}


class AblationError(Exception):
    """Raised when ablation invariants or pooling rules are violated."""


# ---- Ablation Trial Spec -------------------------------------------------------------------------


@dataclass(frozen=True)
class AblationTrialSpec:
    """A scheduled trial in an ablation experiment matrix."""

    task_seed: str
    model_profile: ModelProfile
    host: str
    ablation_config: AblationConfig
    trial: int
    timeout_seconds: float
    ceilings: Ceilings
    order_index: int

    @property
    def cell_key(self) -> Tuple[str, str, str, str, int]:
        """Cell key identifying the non-architecture factors that must be held constant."""
        return (
            self.task_seed,
            self.model_profile.model_id,
            self.model_profile.reasoning_effort,
            self.host,
            self.trial,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_seed": self.task_seed,
            "model_profile": self.model_profile.to_dict(),
            "host": self.host,
            "ablation_config": self.ablation_config.to_dict(),
            "trial": self.trial,
            "timeout_seconds": self.timeout_seconds,
            "ceilings": self.ceilings.as_dict(),
            "order_index": self.order_index,
            "cell_key": list(self.cell_key),
        }


# ---- Ablation Scheduler --------------------------------------------------------------------------


class AblationScheduler:
    """Generates randomized ablation trial schedules and paired comparisons."""

    def __init__(
        self,
        task_seeds: Sequence[str],
        model_profiles: Sequence[ModelProfile],
        hosts: Sequence[str],
        architectures: Optional[Sequence[str | AblationConfig]] = None,
        trial_count: int = 3,
        timeout_seconds: float = 300.0,
        random_seed: int = 42,
    ) -> None:
        if not task_seeds:
            raise AblationError("task_seeds cannot be empty")
        if not model_profiles:
            raise AblationError("model_profiles cannot be empty")
        if not hosts:
            raise AblationError("hosts cannot be empty")
        if trial_count < 1:
            raise AblationError("trial_count must be >= 1")

        self.task_seeds = tuple(task_seeds)
        self.model_profiles = tuple(model_profiles)
        self.hosts = tuple(hosts)
        self.trial_count = trial_count
        self.timeout_seconds = timeout_seconds
        self.random_seed = random_seed

        # Resolve architecture configs
        archs = architectures or ALL_ABLATION_ARCHITECTURES
        resolved_configs: List[AblationConfig] = []
        for a in archs:
            if isinstance(a, AblationConfig):
                resolved_configs.append(a)
            elif isinstance(a, str):
                if a not in STANDARD_ABLATION_CONFIGS:
                    raise AblationError(f"Unknown architecture: {a!r}")
                resolved_configs.append(STANDARD_ABLATION_CONFIGS[a])
            else:
                raise AblationError(f"Invalid architecture spec: {a!r}")
        self.ablation_configs = tuple(resolved_configs)

    def generate_schedule(self) -> List[AblationTrialSpec]:
        """Generate the randomized execution schedule.

        Holds (task_seed, model_profile, host, trial) constant across all architecture variants
        being compared. Randomizes allowed execution ordering deterministically using the random seed.
        """
        raw_specs: List[AblationTrialSpec] = []
        ceil = make_ceilings(
            per_trial_wall_seconds=self.timeout_seconds,
            trial_count=self.trial_count,
        )

        for task_seed in self.task_seeds:
            for model_prof in self.model_profiles:
                for host in self.hosts:
                    for trial in range(1, self.trial_count + 1):
                        for arch_cfg in self.ablation_configs:
                            raw_specs.append(
                                AblationTrialSpec(
                                    task_seed=task_seed,
                                    model_profile=model_prof,
                                    host=host,
                                    ablation_config=arch_cfg,
                                    trial=trial,
                                    timeout_seconds=self.timeout_seconds,
                                    ceilings=ceil,
                                    order_index=0,  # assigned after shuffle
                                )
                            )

        # Shuffle deterministically
        rng = random.Random(self.random_seed)
        shuffled = list(raw_specs)
        rng.shuffle(shuffled)

        # Assign final sequential order indices
        scheduled: List[AblationTrialSpec] = []
        for idx, item in enumerate(shuffled):
            scheduled.append(
                AblationTrialSpec(
                    task_seed=item.task_seed,
                    model_profile=item.model_profile,
                    host=item.host,
                    ablation_config=item.ablation_config,
                    trial=item.trial,
                    timeout_seconds=item.timeout_seconds,
                    ceilings=item.ceilings,
                    order_index=idx,
                )
            )

        return scheduled


# ---- Paired Comparison ---------------------------------------------------------------------------


@dataclass
class PairedDelta:
    """Delta for a single matched cell between architecture A and architecture B."""

    task_seed: str
    model_id: str
    trial: int
    arch_a: str
    arch_b: str
    result_a: TrialResult
    result_b: TrialResult
    outcome_a: str  # "complete" | "false_complete" | "incomplete" | "pending"
    outcome_b: str
    wall_time_delta: float  # time_b - time_a
    token_delta: Optional[int]  # tokens_b - tokens_a (None if unavailable)
    win_loss: str  # "A_wins" | "B_wins" | "tie" | "both_pending" | "incomparable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_seed": self.task_seed,
            "model_id": self.model_id,
            "trial": self.trial,
            "arch_a": self.arch_a,
            "arch_b": self.arch_b,
            "outcome_a": self.outcome_a,
            "outcome_b": self.outcome_b,
            "wall_time_delta": self.wall_time_delta,
            "token_delta": self.token_delta,
            "win_loss": self.win_loss,
        }


@dataclass
class PairedComparisonResult:
    """Aggregate paired comparison between two architectures holding all factors constant."""

    arch_a: str
    arch_b: str
    total_pairs: int
    a_wins: int
    b_wins: int
    ties: int
    both_pending: int
    mean_wall_time_delta: float
    mean_token_delta: Optional[float]
    pairs: List[PairedDelta] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arch_a": self.arch_a,
            "arch_b": self.arch_b,
            "total_pairs": self.total_pairs,
            "a_wins": self.a_wins,
            "b_wins": self.b_wins,
            "ties": self.ties,
            "both_pending": self.both_pending,
            "mean_wall_time_delta": self.mean_wall_time_delta,
            "mean_token_delta": self.mean_token_delta,
            "pairs": [p.to_dict() for p in self.pairs],
        }


def compute_paired_comparison(
    results_a: Sequence[TrialResult],
    results_b: Sequence[TrialResult],
    arch_a: str,
    arch_b: str,
) -> PairedComparisonResult:
    """Produce a rigorous paired comparison between two architectures.

    Only pairs matching exact cells (same task_seed, model_id, reasoning_effort, host, trial,
    timeout, ceilings). Refuses to pool incompatible cells.
    """

    # Index results_a by cell key
    def cell_key(r: TrialResult) -> Tuple[str, str, str, str, int]:
        m = r.manifest.identity
        return (
            m["task_seed"],
            m["model_id"],
            m["reasoning_effort"],
            m["host"],
            m["trial"],
        )

    map_a: Dict[Tuple[str, str, str, str, int], TrialResult] = {
        cell_key(r): r for r in results_a
    }
    map_b: Dict[Tuple[str, str, str, str, int], TrialResult] = {
        cell_key(r): r for r in results_b
    }

    common_keys = sorted(set(map_a.keys()) & set(map_b.keys()))
    if not common_keys:
        raise AblationError(
            f"No matching cells found between architecture '{arch_a}' and '{arch_b}' "
            "for paired comparison."
        )

    pairs: List[PairedDelta] = []
    a_wins = 0
    b_wins = 0
    ties = 0
    both_pending = 0
    time_deltas: List[float] = []
    token_deltas: List[int] = []

    for k in common_keys:
        res_a = map_a[k]
        res_b = map_b[k]

        out_a = (
            "pending"
            if res_a.is_pending
            else (res_a.score_result.verdict if res_a.score_result else "unknown")
        )
        out_b = (
            "pending"
            if res_b.is_pending
            else (res_b.score_result.verdict if res_b.score_result else "unknown")
        )

        wt_a = float(res_a.usage.get("wall_time", 0.0))
        wt_b = float(res_b.usage.get("wall_time", 0.0))
        dt_time = wt_b - wt_a
        time_deltas.append(dt_time)

        tok_a = res_a.usage.get("tokens")
        tok_b = res_b.usage.get("tokens")
        dt_tok: Optional[int] = None
        if isinstance(tok_a, int) and isinstance(tok_b, int):
            dt_tok = tok_b - tok_a
            token_deltas.append(dt_tok)

        # Determine winner: complete beats incomplete/false_complete/pending;
        # incomplete (honest partial) beats false_complete.
        outcome_rank = {
            "complete": 4,
            "incomplete": 2,
            "pending": 1,
            "false_complete": 0,
        }
        rank_a = outcome_rank.get(out_a, 0)
        rank_b = outcome_rank.get(out_b, 0)

        if out_a == "pending" and out_b == "pending":
            win_loss = "both_pending"
            both_pending += 1
        elif rank_a > rank_b:
            win_loss = "A_wins"
            a_wins += 1
        elif rank_b > rank_a:
            win_loss = "B_wins"
            b_wins += 1
        else:
            # Same outcome quality: tie
            win_loss = "tie"
            ties += 1

        pairs.append(
            PairedDelta(
                task_seed=k[0],
                model_id=k[1],
                trial=k[4],
                arch_a=arch_a,
                arch_b=arch_b,
                result_a=res_a,
                result_b=res_b,
                outcome_a=out_a,
                outcome_b=out_b,
                wall_time_delta=dt_time,
                token_delta=dt_tok,
                win_loss=win_loss,
            )
        )

    mean_time_d = sum(time_deltas) / len(time_deltas) if time_deltas else 0.0
    mean_tok_d = (sum(token_deltas) / len(token_deltas)) if token_deltas else None

    return PairedComparisonResult(
        arch_a=arch_a,
        arch_b=arch_b,
        total_pairs=len(pairs),
        a_wins=a_wins,
        b_wins=b_wins,
        ties=ties,
        both_pending=both_pending,
        mean_wall_time_delta=mean_time_d,
        mean_token_delta=mean_tok_d,
        pairs=pairs,
    )

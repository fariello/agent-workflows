"""Tests for benchmark runners, adapters, ablations, metrics, release thresholds, and reports.

awoptimize Order 13 (`9ihhzr`) E-01..E-05.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_workflows.benchmark_ablations import (
    ALL_ABLATION_ARCHITECTURES,
    ARCH_MODULAR,
    ARCH_MONOLITH,
    ARCH_RUNTIME,
    ARCH_RUNTIME_CROSS_MODEL_VERIFIER,
    ARCH_RUNTIME_FRESH_VERIFIER,
    ARCH_RUNTIME_SAME_SESSION_AUDIT,
    AblationError,
    AblationScheduler,
    compute_paired_comparison,
)
from agent_workflows.benchmark_corpus import SeededTask
from agent_workflows.benchmark_manifest import (
    UNAVAILABLE,
    BenchmarkManifest,
    make_usage,
)
from agent_workflows.benchmark_metrics import (
    MetricError,
    MetricSummary,
    MetricValue,
    compute_aggregate_metrics,
    evaluate_trial_metrics,
    wilson_score_interval,
)
from agent_workflows.benchmark_reports import (
    BenchmarkRunRecord,
    compare_with_baseline,
    format_json_report,
    format_markdown_report,
    generate_benchmark_report,
    run_ci_offline_benchmark,
)
from agent_workflows.benchmark_runners import (
    ALL_RUNNER_FAILURE_KINDS,
    FAILURE_TIMEOUT,
    MODEL_CLAUDE_OPUS_5,
    MODEL_GEMINI_3_7_FLASH,
    MODEL_GLM_5_3,
    MODEL_GPT_5_6_SOL,
    LiveExecutionProhibitedError,
    RunnerDouble,
    RunnerError,
    STANDARD_PROFILES,
    TrialResult,
    execute_live_runner,
    get_adapter,
)
from agent_workflows.benchmark_thresholds import (
    RISK_LOW,
    RISK_MEDIUM,
    SignedRevisionEvent,
    ThresholdError,
    ThresholdPolicy,
    evaluate_release_gate,
)


@pytest.fixture
def sample_task() -> SeededTask:
    return SeededTask(
        task_class="simple_commands",
        seed_id="task_seed_001",
        task={
            "prompt": "Run build and test suite",
            "task_class": "simple_commands",
            "seed_id": "task_seed_001",
        },
        seed_path=Path("/tmp/fake_seed_path"),
    )


# ==================================================================================================
# E-01 / V-01: Runner Contracts, Live Adapters, and Runner Doubles
# ==================================================================================================


def test_live_runner_adapters_four_target_models(sample_task: SeededTask) -> None:
    """Verify live runner adapters generate valid CLI invocations and rerun commands for all 4 models."""
    for model_id in (
        MODEL_GPT_5_6_SOL,
        MODEL_GEMINI_3_7_FLASH,
        MODEL_CLAUDE_OPUS_5,
        MODEL_GLM_5_3,
    ):
        assert model_id in STANDARD_PROFILES
        profile = STANDARD_PROFILES[model_id]

        for host in (
            "opencode",
            "gemini_cli",
            "claude_code",
            "kiro",
            "codex",
            "antigravity",
        ):
            adapter = get_adapter(host)
            cmd = adapter.build_command(
                profile,
                sample_task,
                workspace_path="/workspace/test",
                timeout_seconds=120.0,
            )
            assert len(cmd) > 0
            assert profile.model_id in " ".join(cmd)

            rerun = adapter.build_rerun_command(
                profile,
                sample_task,
                workspace_path="/workspace/test",
                timeout_seconds=120.0,
            )
            assert isinstance(rerun, str)
            assert profile.model_id in rerun
            assert "/workspace/test" in rerun


def test_runner_adapter_unknown_host_rejected() -> None:
    """Reject unknown host names with RunnerError."""
    with pytest.raises(RunnerError, match="Unsupported benchmark host"):
        get_adapter("unknown_provider_xyz")


def test_runner_doubles_all_eight_outcomes(sample_task: SeededTask) -> None:
    """Verify runner doubles cover success and all 7 failure modes -> structured pending + rerun cmd."""
    adapter = get_adapter("opencode")
    profile = STANDARD_PROFILES[MODEL_GPT_5_6_SOL]

    # 1. Success
    double_success = RunnerDouble(adapter, default_outcome="success")
    res_succ = double_success.run_trial(
        sample_task, profile, trial=1, host_reports_tokens=True
    )
    assert res_succ.status == "completed"
    assert res_succ.is_success is True
    assert res_succ.failure_kind is None
    assert res_succ.usage["wall_time"] > 0
    assert isinstance(res_succ.usage["tokens"], int)
    assert "opencode" in res_succ.rerun_command

    # 2-8. All 7 failure kinds
    for fail_kind in ALL_RUNNER_FAILURE_KINDS:
        double = RunnerDouble(adapter, default_outcome=fail_kind)
        res = double.run_trial(sample_task, profile, trial=1)
        assert res.status == "pending"
        assert res.is_pending is True
        assert res.failure_kind == fail_kind
        assert res.error_message is not None
        # Rerun command must always be present and executable
        assert "opencode" in res.rerun_command
        assert profile.model_id in res.rerun_command
        # Tokens are UNAVAILABLE, never guessed or fabricated
        assert res.usage["tokens"] == UNAVAILABLE


def test_live_execution_gate_blocks_executor_agent(sample_task: SeededTask) -> None:
    """The harness strictly blocks agent live model execution and returns structured pending."""
    adapter = get_adapter("opencode")
    profile = STANDARD_PROFILES[MODEL_GPT_5_6_SOL]

    # Without explicit human operator authorization: structured pending with rerun command
    res = execute_live_runner(
        adapter, profile, sample_task, trial=1, operator_authorized=False
    )
    assert res.status == "pending"
    assert res.failure_kind == "live_execution_operator_gated"
    assert "Live model invocation is strictly operator-run" in (res.error_message or "")
    assert res.rerun_command.startswith("opencode")

    # If called with operator_authorized inside unit test environment, raises LiveExecutionProhibitedError
    with pytest.raises(LiveExecutionProhibitedError):
        execute_live_runner(
            adapter, profile, sample_task, trial=1, operator_authorized=True
        )


# ==================================================================================================
# E-02 / V-02: Architecture Ablations and Paired Comparisons
# ==================================================================================================


def test_ablation_scheduler_matrix_and_randomization() -> None:
    """Verify ablation scheduler holds task seed/config constant and labels isolation and verifier."""
    scheduler = AblationScheduler(
        task_seeds=["seed_a", "seed_b"],
        model_profiles=[STANDARD_PROFILES[MODEL_GPT_5_6_SOL]],
        hosts=["opencode"],
        architectures=ALL_ABLATION_ARCHITECTURES,
        trial_count=2,
        random_seed=12345,
    )

    schedule = scheduler.generate_schedule()
    # 2 seeds * 1 model * 1 host * 2 trials * 6 architectures = 24 trials
    assert len(schedule) == 24

    # Verify every required architecture is present with proper isolation and verifier labels
    arch_names = {s.ablation_config.architecture for s in schedule}
    assert arch_names == set(ALL_ABLATION_ARCHITECTURES)

    # Check isolation and verifier identity labeling
    configs_by_arch = {
        s.ablation_config.architecture: s.ablation_config for s in schedule
    }
    assert configs_by_arch[ARCH_MONOLITH].isolation_level == "none"
    assert configs_by_arch[ARCH_MODULAR].isolation_level == "package"
    assert configs_by_arch[ARCH_RUNTIME].isolation_level == "runtime_isolated"
    assert (
        configs_by_arch[ARCH_RUNTIME_SAME_SESSION_AUDIT].verifier_identity
        == "self_session"
    )
    assert (
        configs_by_arch[ARCH_RUNTIME_FRESH_VERIFIER].verifier_identity
        == "fresh_same_model"
    )
    assert (
        configs_by_arch[ARCH_RUNTIME_CROSS_MODEL_VERIFIER].verifier_identity
        == "cross_model"
    )

    # Deterministic randomization: same seed yields same ordering
    scheduler2 = AblationScheduler(
        task_seeds=["seed_a", "seed_b"],
        model_profiles=[STANDARD_PROFILES[MODEL_GPT_5_6_SOL]],
        hosts=["opencode"],
        architectures=ALL_ABLATION_ARCHITECTURES,
        trial_count=2,
        random_seed=12345,
    )
    schedule2 = scheduler2.generate_schedule()
    assert [s.cell_key for s in schedule] == [s.cell_key for s in schedule2]
    assert [s.ablation_config.architecture for s in schedule] == [
        s.ablation_config.architecture for s in schedule2
    ]


def test_paired_comparison_computes_deltas_and_rejects_incompatible(
    sample_task: SeededTask,
) -> None:
    """Verify paired comparison computes win/loss/wall-time deltas and rejects un-matched cells."""
    adapter = get_adapter("opencode")
    profile = STANDARD_PROFILES[MODEL_GPT_5_6_SOL]

    # Arch A results (runtime: fast success)
    double_a = RunnerDouble(
        adapter, default_outcome={"kind": "success", "wall_time": 2.0, "tokens": 100}
    )
    res_a = double_a.run_trial(sample_task, profile, trial=1, host_reports_tokens=True)

    # Arch B results (monolith: slower success)
    double_b = RunnerDouble(
        adapter, default_outcome={"kind": "success", "wall_time": 5.5, "tokens": 250}
    )
    res_b = double_b.run_trial(sample_task, profile, trial=1, host_reports_tokens=True)

    comparison = compute_paired_comparison(
        results_a=[res_a],
        results_b=[res_b],
        arch_a=ARCH_RUNTIME,
        arch_b=ARCH_MONOLITH,
    )

    assert comparison.total_pairs == 1
    assert comparison.ties == 1
    assert comparison.mean_wall_time_delta == 3.5  # 5.5 - 2.0
    assert comparison.mean_token_delta == 150.0  # 250 - 100

    # Incompatible cells (no common keys) must be rejected
    other_task = SeededTask(
        task_class="migration",
        seed_id="different_seed_999",
        task={
            "prompt": "diff",
            "task_class": "migration",
            "seed_id": "different_seed_999",
        },
        seed_path=Path("/tmp/diff"),
    )
    res_diff = double_b.run_trial(other_task, profile, trial=1)
    with pytest.raises(AblationError, match="No matching cells found"):
        compute_paired_comparison([res_a], [res_diff], ARCH_RUNTIME, ARCH_MONOLITH)


# ==================================================================================================
# E-03 / V-03: Metric Golden Tests & Anti-Dollar Cost Enforcement
# ==================================================================================================


def test_metrics_computation_and_proportions(sample_task: SeededTask) -> None:
    """Golden test verifying metrics computation, uncertainty, sample size, and activation separation."""
    adapter = get_adapter("opencode")
    profile = STANDARD_PROFILES[MODEL_GPT_5_6_SOL]

    gt = {
        "required_requirements": ["req_1", "req_2"],
        "required_instructions": ["step_1"],
        "reference_test_count": 10,
        "reference_assertion_count": 20,
        "scope_fence_paths": ["src/main.py"],
        "requires_skill": True,
    }

    # Trial 1: complete & correct
    double1 = RunnerDouble(
        adapter,
        default_outcome={
            "kind": "success",
            "wall_time": 3.0,
            "tokens": 200,
            "credits_or_quota": "gemini_pool_token_bucket",
            "transcript": {
                "skill_activated": True,
                "retries_count": 0,
                "human_interventions_count": 0,
                "touched_paths": ["src/main.py"],
                "post_test_count": 10,
                "post_assertion_count": 20,
            },
        },
    )
    res1 = double1.run_trial(
        sample_task, profile, trial=1, ground_truth=gt, host_reports_tokens=True
    )

    # Trial 2: incomplete with missing req
    double2 = RunnerDouble(
        adapter,
        default_outcome={
            "kind": "success",
            "wall_time": 4.0,
            "tokens": 300,
            "transcript": {
                "claimed_complete": False,
                "requirement_results": {"req_1": "satisfied"},  # req_2 missing
                "skill_activated": True,
                "retries_count": 1,
                "human_interventions_count": 1,
                "touched_paths": [
                    "src/main.py",
                    "unauthorized.txt",
                ],  # 1 scope violation
                "post_test_count": 8,  # weakened/deleted tests
                "post_assertion_count": 16,
            },
        },
    )
    res2 = double2.run_trial(
        sample_task, profile, trial=2, ground_truth=gt, host_reports_tokens=True
    )

    summary = compute_aggregate_metrics(
        [res1, res2], ground_truths={sample_task.seed_id: gt}
    )

    assert summary.sample_size == 2
    assert summary.completed_trials == 2
    assert summary.pending_trials == 0

    # 1. Requirement recall: (1.0 + 0.5) / 2 = 0.75
    assert summary.requirement_recall.value == 0.75

    # 2. Task correctness: (1 + 0) / 2 = 0.5
    assert summary.task_correctness.value == 0.5

    # 3. Scope violations: 0 + 1 = 1
    assert summary.scope_violations.value == 1

    # 4. Test integrity: (1.0 + 0.8) / 2 = 0.9
    assert summary.test_integrity.value == 0.9

    # 5. Skill activation: 2 activated / 2 target = 1.0
    assert summary.skill_activation_precision.value == 1.0
    assert summary.skill_activation_recall.value == 1.0

    # 6. Retries & interventions: 1 and 1
    assert summary.total_retries.value == 1
    assert summary.total_human_interventions.value == 1

    # 7. Efficiency (time & tokens)
    assert summary.wall_time_seconds.value["mean"] == 3.5
    assert summary.tokens.value["mean"] == 250.0
    assert len(summary.credits_or_quota_records) == 1


def test_dollar_cost_is_strictly_rejected(sample_task: SeededTask) -> None:
    """Verify that dollar cost metrics are strictly rejected anywhere in usage/metrics."""
    # Usage constructing with dollar cost raises
    with pytest.raises(Exception):
        make_usage(wall_time=1.0, cost=0.05)

    # Evaluating a trial containing a forbidden cost field raises MetricError
    bad_trial = TrialResult(
        trial_id="test_bad",
        status="completed",
        manifest=BenchmarkManifest(
            schema_version=1,
            identity={
                "model_id": "gpt-5.6-sol",
                "reasoning_effort": "none",
                "host": "opencode",
                "host_version": "1.0",
                "adapter_digest": "0" * 64,
                "workflow_digest": "0" * 64,
                "tool_policy_digest": "0" * 64,
                "task_seed": "s1",
                "trial": 1,
                "timeout_seconds": 60.0,
                "ceilings_digest": "0" * 64,
                "environment_fingerprint": "0" * 64,
            },
            ceilings={
                "per_trial_wall_seconds": 60.0,
                "trial_count": 1,
                "host_reports_tokens": False,
            },
            usage={
                "wall_time": 1.0,
                "tokens": UNAVAILABLE,
                "credits_or_quota": UNAVAILABLE,
                "cost": 0.02,
            },
        ),
        rerun_command="rerun",
        usage={"wall_time": 1.0, "cost": 0.02},
    )

    with pytest.raises(MetricError, match="Dollar cost metric 'cost' is forbidden"):
        evaluate_trial_metrics(bad_trial)


def test_wilson_score_uncertainty() -> None:
    """Verify Wilson score confidence interval computation."""
    low, high = wilson_score_interval(10, 10, confidence=0.95)
    assert 0.65 < low < 1.0
    assert high == 1.0

    low0, high0 = wilson_score_interval(0, 10, confidence=0.95)
    assert low0 == 0.0
    assert 0.0 < high0 < 0.35

    assert wilson_score_interval(0, 0) == (0.0, 0.0)


# ==================================================================================================
# E-04 / V-04: Risk-Class Release Thresholds & Signed Human Revisions
# ==================================================================================================


def test_release_thresholds_truth_table() -> None:
    """Verify release gate truth-table: passes clean metrics, rejects critical escapes or invalid evidence."""
    policy = ThresholdPolicy()

    # Clean passing metric summary
    clean_summary = MetricSummary(
        sample_size=10,
        completed_trials=10,
        pending_trials=0,
        requirement_recall=MetricValue("requirement_recall", 1.0, 10),
        task_correctness=MetricValue("task_correctness", 1.0, 10),
        evidence_validity=MetricValue("evidence_validity", 1.0, 10),
        false_completion_detection=MetricValue("false_completion_detection", 1.0, 5),
        defect_escape=MetricValue("defect_escape", 0.0, 5),
        regression_rate=MetricValue("regression_rate", 0.0, 10),
        scope_violations=MetricValue("scope_violations", 0, 10),
        test_integrity=MetricValue("test_integrity", 1.0, 10),
        skill_activation_precision=MetricValue("skill_activation_precision", 1.0, 10),
        skill_activation_recall=MetricValue("skill_activation_recall", 1.0, 10),
        total_retries=MetricValue("total_retries", 0, 10),
        total_human_interventions=MetricValue("total_human_interventions", 0, 10),
        wall_time_seconds=MetricValue("wall_time_seconds", {"mean": 2.0}, 10),
        tokens=MetricValue("tokens", UNAVAILABLE, 0, is_available=False),
    )

    res_clean = evaluate_release_gate(clean_summary, policy, risk_class=RISK_MEDIUM)
    assert res_clean.passed is True
    assert len(res_clean.findings) == 0

    # Critical seeded defect escape -> MUST fail immediately
    escaped_summary = MetricSummary(
        sample_size=10,
        completed_trials=10,
        pending_trials=0,
        requirement_recall=MetricValue("requirement_recall", 1.0, 10),
        task_correctness=MetricValue("task_correctness", 1.0, 10),
        evidence_validity=MetricValue("evidence_validity", 1.0, 10),
        false_completion_detection=MetricValue("false_completion_detection", 0.8, 5),
        defect_escape=MetricValue("defect_escape", 0.2, 5),  # 1 escape out of 5
        regression_rate=MetricValue("regression_rate", 0.0, 10),
        scope_violations=MetricValue("scope_violations", 0, 10),
        test_integrity=MetricValue("test_integrity", 1.0, 10),
        skill_activation_precision=MetricValue("skill_activation_precision", 1.0, 10),
        skill_activation_recall=MetricValue("skill_activation_recall", 1.0, 10),
        total_retries=MetricValue("total_retries", 0, 10),
        total_human_interventions=MetricValue("total_human_interventions", 0, 10),
        wall_time_seconds=MetricValue("wall_time_seconds", {"mean": 2.0}, 10),
        tokens=MetricValue("tokens", UNAVAILABLE, 0, is_available=False),
    )
    res_esc = evaluate_release_gate(escaped_summary, policy, risk_class=RISK_LOW)
    assert res_esc.passed is False
    assert any("CRITICAL GATE FAILURE" in f for f in res_esc.findings)

    # Invalid evidence -> MUST fail immediately
    bad_ev_summary = MetricSummary(
        sample_size=10,
        completed_trials=10,
        pending_trials=0,
        requirement_recall=MetricValue("requirement_recall", 1.0, 10),
        task_correctness=MetricValue("task_correctness", 1.0, 10),
        evidence_validity=MetricValue("evidence_validity", 0.8, 10),  # < 1.0
        false_completion_detection=MetricValue("false_completion_detection", 1.0, 5),
        defect_escape=MetricValue("defect_escape", 0.0, 5),
        regression_rate=MetricValue("regression_rate", 0.0, 10),
        scope_violations=MetricValue("scope_violations", 0, 10),
        test_integrity=MetricValue("test_integrity", 1.0, 10),
        skill_activation_precision=MetricValue("skill_activation_precision", 1.0, 10),
        skill_activation_recall=MetricValue("skill_activation_recall", 1.0, 10),
        total_retries=MetricValue("total_retries", 0, 10),
        total_human_interventions=MetricValue("total_human_interventions", 0, 10),
        wall_time_seconds=MetricValue("wall_time_seconds", {"mean": 2.0}, 10),
        tokens=MetricValue("tokens", UNAVAILABLE, 0, is_available=False),
    )
    res_ev = evaluate_release_gate(bad_ev_summary, policy, risk_class=RISK_LOW)
    assert res_ev.passed is False
    assert any("EVIDENCE GATE FAILURE" in f for f in res_ev.findings)


def test_signed_human_revision_policy_enforcement() -> None:
    """Verify that threshold revisions require valid human signature and reject agent modifications."""
    policy = ThresholdPolicy()

    # 1. Reject unsigned / agent revision
    unsigned_event = SignedRevisionEvent(
        revision_id="rev_001",
        author="agent",
        reason="Automated threshold relaxing",
        timestamp="2026-08-22T00:00:00Z",
        signature="",
        is_human_signed=False,
        changes={"low": {"min_task_correctness": 0.50}},
    )
    with pytest.raises(ThresholdError, match="Unauthorized threshold revision"):
        policy.apply_revision(unsigned_event)

    # 2. Reject revision attempting to relax non-negotiable zero critical escapes
    invalid_inv_event = SignedRevisionEvent(
        revision_id="rev_002",
        author="Maintainer Human",
        reason="Relax critical escapes",
        timestamp="2026-08-22T00:00:00Z",
        signature="sig_valid_human_12345",
        is_human_signed=True,
        changes={"low": {"max_critical_escapes": 2}},
    )
    with pytest.raises(ThresholdError, match="Release invariant violated"):
        policy.apply_revision(invalid_inv_event)

    # 3. Valid signed human revision is accepted
    valid_event = SignedRevisionEvent(
        revision_id="rev_003",
        author="Human Maintainer",
        reason="Increase medium risk requirement recall to 0.98",
        timestamp="2026-08-22T00:00:00Z",
        signature="sig_human_maintainer_20260822",
        is_human_signed=True,
        changes={"medium": {"min_requirement_recall": 0.98}},
    )
    policy.apply_revision(valid_event)
    assert policy.get_thresholds(RISK_MEDIUM).min_requirement_recall == 0.98
    assert len(policy.revision_history) == 1


# ==================================================================================================
# E-05 / V-05: Reports, Regression Triage, and CI-Safe Offline Subset
# ==================================================================================================


def test_benchmark_reports_generation_and_formatting(sample_task: SeededTask) -> None:
    """Verify report generation, linking to raw trial IDs, rerun recipes, and preserving pending cells."""
    adapter = get_adapter("opencode")
    profile = STANDARD_PROFILES[MODEL_GPT_5_6_SOL]

    double_succ = RunnerDouble(adapter, default_outcome="success")
    res1 = double_succ.run_trial(
        sample_task, profile, trial=1, host_reports_tokens=True
    )

    double_pend = RunnerDouble(adapter, default_outcome=FAILURE_TIMEOUT)
    res2 = double_pend.run_trial(sample_task, profile, trial=2)

    record = BenchmarkRunRecord(
        run_id="run_20260822_001",
        created_at="2026-08-22T21:00:00Z",
        protocol_digest="a" * 64,
        trials=[res1, res2],
    )

    report = generate_benchmark_report(record)
    assert report.metrics.sample_size == 2
    assert report.metrics.completed_trials == 1
    assert report.metrics.pending_trials == 1

    # Markdown format
    md = format_markdown_report(report)
    assert "# Benchmark Evaluation Report: run_20260822_001" in md
    assert "Preserved Pending Trials" in md
    assert res2.trial_id in md
    assert res2.rerun_command in md
    assert "**Dollar Cost**: N/A" in md

    # JSON format
    js = format_json_report(report)
    parsed = json.loads(js)
    assert parsed["run_record"]["run_id"] == "run_20260822_001"
    assert len(parsed["run_record"]["trials"]) == 2


def test_baseline_comparison_and_regression_triage(sample_task: SeededTask) -> None:
    """Verify baseline comparison identifies regressions and attaches exact rerun recipes."""
    adapter = get_adapter("opencode")
    profile = STANDARD_PROFILES[MODEL_GPT_5_6_SOL]

    # Baseline run: trial 1 completed
    double_succ = RunnerDouble(adapter, default_outcome="success")
    base_trial = double_succ.run_trial(sample_task, profile, trial=1)
    baseline_rec = BenchmarkRunRecord(
        run_id="baseline_001",
        created_at="2026-08-20T00:00:00Z",
        protocol_digest="0" * 64,
        trials=[base_trial],
    )

    # Candidate run: trial 1 timed out (regression!)
    double_fail = RunnerDouble(adapter, default_outcome=FAILURE_TIMEOUT)
    cand_trial = double_fail.run_trial(sample_task, profile, trial=1)
    cand_rec = BenchmarkRunRecord(
        run_id="candidate_001",
        created_at="2026-08-22T00:00:00Z",
        protocol_digest="0" * 64,
        trials=[cand_trial],
        baseline_digest=baseline_rec.digest(),
    )

    comparison = compare_with_baseline(cand_rec, baseline_rec)
    assert comparison.matched_trials_count == 1
    assert len(comparison.regressions) == 1

    reg = comparison.regressions[0]
    assert reg.trial_id == cand_trial.trial_id
    assert reg.baseline_verdict == "complete"
    assert reg.candidate_status == "pending"
    assert "opencode" in reg.rerun_command

    # Full report includes regression triage section
    report = generate_benchmark_report(cand_rec, baseline_record=baseline_rec)
    md = format_markdown_report(report)
    assert "## Regression Triage (Operator Rerun Recipes)" in md
    assert reg.trial_id in md


def test_ci_safe_offline_benchmark_runner() -> None:
    """Verify CI offline benchmark executes without credentials, network, or paid API calls."""
    report = run_ci_offline_benchmark()
    assert report is not None
    assert report.run_record.metadata.get("offline_safe") is True
    assert report.metrics.sample_size > 0
    assert report.metrics.completed_trials > 0
    assert len(report.gate_results) == 4

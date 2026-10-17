"""Behavioral tests for release-readiness review coordinator integration.

Covers ReleaseReviewCoordinator.verify_readiness (STAGE_VERIFY) and
ReleaseReviewCoordinator.authorize_release (STAGE_RELEASE), testing gate
classification, standing gate triage/waiver, non-waivable hard gates,
and not-applicable gate handling.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, List
import pytest

from agent_workflows import migration_complex as mc
from agent_workflows import release_readiness as rr
from tests.test_release_readiness_producers import _setup_full_go_tree


def _build_full_go_tree(tmp_path: Path) -> Path:
    """Create a full clean repo tree."""
    root = tmp_path / "repo"
    root.mkdir(parents=True, exist_ok=True)
    _setup_full_go_tree(root)
    return root


def _build_synthetic_git_root(tmp_path: Path) -> Path:
    """Create a full clean repo tree with git initialized and pending plan dir."""
    root = tmp_path / "repo_git"
    root.mkdir(parents=True, exist_ok=True)
    _setup_full_go_tree(root)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    return root


def _build_managed_style_tree(tmp_path: Path) -> Path:
    """Create a minimal managed-style repo tree missing docs, changelog, and host_matrix."""
    tree = tmp_path / "repo_managed"
    tree.mkdir(parents=True, exist_ok=True)
    _setup_full_go_tree(tree)
    if (tree / "docs").is_dir():
        shutil.rmtree(tree / "docs")
    if (tree / "CHANGELOG.md").is_file():
        (tree / "CHANGELOG.md").unlink()
    matrix_file = (
        tree
        / ".aw"
        / "system"
        / "workflows"
        / "conformance"
        / "tools"
        / "host_matrix.json"
    )
    if matrix_file.is_file():
        matrix_file.unlink()
    return tree


def test_planning_mode_refuses_verify_readiness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Planning mode refuses verify_readiness and does not enter STAGE_VERIFY."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    root = _build_full_go_tree(tmp_path)
    report = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=root,
        run_subprocess_gates=False,
    )
    coordinator = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_PLANNING)
    with pytest.raises(mc.ReleaseModeError) as exc_info:
        coordinator.verify_readiness(report)

    assert mc.STAGE_VERIFY not in coordinator.stages_entered
    assert "verify" in str(exc_info.value)


def test_section8_unsigned_residual_risk_only_yields_go_with_pending_attestation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Section 8 with only unsigned residual_risk yields GO with pending_human_attestation=True."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    root = _build_full_go_tree(tmp_path)
    report = rr.build_report(
        suite_passed=True,
        residual_risk_signed=False,
        repo_root=root,
        run_subprocess_gates=False,
    )
    assert report.verdict == rr.VERDICT_NO_GO
    assert report.failing_gates() == ["residual_risk"]

    coordinator = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    verification = coordinator.verify_readiness(report)

    assert mc.STAGE_VERIFY in coordinator.stages_entered
    assert verification.recommendation == mc.RECOMMENDATION_GO
    assert verification.pending_human_attestation is True
    assert verification.hard_failures == ()
    assert verification.standing_failures == ()
    assert verification.triaged_standing_gates == ()
    assert verification.untriaged_standing_gates == ()
    assert coordinator.last_verification is verification

    data = verification.to_dict()
    assert data["recommendation"] == mc.RECOMMENDATION_GO
    assert data["pending_human_attestation"] is True
    assert data["hard_failures"] == []
    assert data["standing_failures"] == []


def test_section8_clean_signed_report_yields_go_without_pending_attestation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Section 8 with clean signed report yields GO with pending_human_attestation=False."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    root = _build_full_go_tree(tmp_path)
    report = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=root,
        run_subprocess_gates=False,
    )
    assert report.verdict == rr.VERDICT_GO
    assert report.failing_gates() == []

    coordinator = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    verification = coordinator.verify_readiness(report)

    assert verification.recommendation == mc.RECOMMENDATION_GO
    assert verification.pending_human_attestation is False
    assert verification.hard_failures == ()
    assert verification.standing_failures == ()

    data = verification.to_dict()
    assert data["verdict"] == rr.VERDICT_GO
    assert data["recommendation"] == mc.RECOMMENDATION_GO
    assert data["pending_human_attestation"] is False


def test_section8_standing_ipd_lint_and_capability_freshness_untriaged_vs_triaged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Standing gate failure is NO-GO when untriaged, and CONDITIONAL GO when triaged."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    root = _build_full_go_tree(tmp_path)
    matrix_file = (
        root
        / ".aw"
        / "system"
        / "workflows"
        / "conformance"
        / "tools"
        / "host_matrix.json"
    )
    matrix_file.write_text(
        json.dumps(
            {
                "hosts": {
                    "test_host": {
                        "t1_policy": {"supported": True, "notes": "seed claim"}
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    report_freshness = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=root,
        run_subprocess_gates=False,
    )
    assert "capability_freshness" in report_freshness.failing_gates()

    coord1 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    v_untriaged = coord1.verify_readiness(report_freshness)
    assert v_untriaged.recommendation == mc.RECOMMENDATION_NO_GO
    assert v_untriaged.untriaged_standing_gates == ("capability_freshness",)
    assert v_untriaged.triaged_standing_gates == ()

    coord2 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    v_triaged = coord2.verify_readiness(
        report_freshness, triaged_standing_gates=("capability_freshness",)
    )
    assert v_triaged.recommendation == mc.RECOMMENDATION_CONDITIONAL_GO
    assert v_triaged.untriaged_standing_gates == ()
    assert v_triaged.triaged_standing_gates == ("capability_freshness",)

    # Synthetic report with ipd_lint failing
    clean_gates = list(report_freshness.gates)
    gates_with_ipd_lint = [
        g
        if g.name != "capability_freshness"
        else rr.GateResult(name="capability_freshness", passed=True, detail="clean")
        for g in clean_gates
    ]
    gates_with_ipd_lint.append(
        rr.GateResult(
            name="ipd_lint", passed=False, detail="pending plan blocking question"
        )
    )
    report_ipd_lint = rr.aggregate(gates_with_ipd_lint)

    coord3 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    v_ipd_untriaged = coord3.verify_readiness(report_ipd_lint)
    assert v_ipd_untriaged.recommendation == mc.RECOMMENDATION_NO_GO
    assert "ipd_lint" in v_ipd_untriaged.untriaged_standing_gates

    coord4 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    v_ipd_triaged = coord4.verify_readiness(
        report_ipd_lint, triaged_standing_gates=("ipd_lint",)
    )
    assert v_ipd_triaged.recommendation == mc.RECOMMENDATION_CONDITIONAL_GO
    assert v_ipd_triaged.triaged_standing_gates == ("ipd_lint",)
    assert v_ipd_triaged.untriaged_standing_gates == ()

    # Both failing: untriaged vs partial vs full triage
    gates_both = list(gates_with_ipd_lint)
    gates_both = [
        g
        if g.name != "capability_freshness"
        else rr.GateResult(name="capability_freshness", passed=False, detail="stale")
        for g in gates_both
    ]
    report_both = rr.aggregate(gates_both)

    coord5 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    v_partial = coord5.verify_readiness(
        report_both, triaged_standing_gates=("ipd_lint",)
    )
    assert v_partial.recommendation == mc.RECOMMENDATION_NO_GO
    assert v_partial.untriaged_standing_gates == ("capability_freshness",)

    coord6 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    v_both = coord6.verify_readiness(
        report_both, triaged_standing_gates=("ipd_lint", "capability_freshness")
    )
    assert v_both.recommendation == mc.RECOMMENDATION_CONDITIONAL_GO
    assert set(v_both.triaged_standing_gates) == {"ipd_lint", "capability_freshness"}
    assert v_both.untriaged_standing_gates == ()


def test_section8_hard_gate_failure_forces_no_go_and_refuses_triage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hard gate failures always force NO-GO and cannot be triaged."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    root = _build_full_go_tree(tmp_path)

    for hard_gate in sorted(mc.READINESS_HARD_GATES):
        gates = [
            rr.GateResult(
                name=g,
                passed=(g != hard_gate),
                detail="ok" if g != hard_gate else "failed",
            )
            for g in mc.READINESS_HARD_GATES
            | mc.READINESS_STANDING_WAIVABLE_GATES
            | mc.READINESS_ATTESTATION_GATES
        ]
        rep = rr.aggregate(gates)
        coordinator = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
        verification = coordinator.verify_readiness(
            rep, triaged_standing_gates=("ipd_lint", "capability_freshness")
        )
        assert verification.recommendation == mc.RECOMMENDATION_NO_GO
        assert hard_gate in verification.hard_failures

    # Attempting to pass a hard gate or residual_risk in triaged_standing_gates raises ComplexMigrationError
    coordinator2 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    rep_clean = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=root,
        run_subprocess_gates=False,
    )
    with pytest.raises(mc.ComplexMigrationError):
        coordinator2.verify_readiness(rep_clean, triaged_standing_gates=("full_suite",))

    with pytest.raises(mc.ComplexMigrationError):
        coordinator2.verify_readiness(
            rep_clean, triaged_standing_gates=("residual_risk",)
        )


def test_section9_authorize_release_enforces_signed_readiness_and_waivers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """authorize_release requires signed readiness_report, waives only standing gates, refuses hard gates."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    root = _build_full_go_tree(tmp_path)

    clean_report = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="maintainer",
        repo_root=root,
        run_subprocess_gates=False,
    )
    assert clean_report.verdict == rr.VERDICT_GO

    # 1. Clean report succeeds
    coord1 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    decision = coord1.authorize_release(
        interactive=True,
        input_handler=lambda _g: "approve",
        approver="maintainer",
        readiness_report=clean_report,
    )
    assert decision.is_approved
    assert mc.STAGE_RELEASE in coord1.stages_entered

    # 2. None report raises ReleaseAuthorityError (no fallback to last_verification)
    coord2 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    coord2.verify_readiness(clean_report)
    with pytest.raises(
        mc.ReleaseAuthorityError, match="no Section 9 readiness report supplied"
    ):
        coord2.authorize_release(
            interactive=True,
            input_handler=lambda _g: "approve",
            approver="maintainer",
            readiness_report=None,
        )

    # 3. Unsigned residual_risk raises ReleaseAuthorityError
    unsigned_report = rr.build_report(
        suite_passed=True,
        residual_risk_signed=False,
        repo_root=root,
        run_subprocess_gates=False,
    )
    coord3 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    with pytest.raises(
        mc.ReleaseAuthorityError, match="residual_risk gate is unsigned"
    ):
        coord3.authorize_release(
            interactive=True,
            input_handler=lambda _g: "approve",
            approver="maintainer",
            readiness_report=unsigned_report,
        )

    # 4. Standing gate failure requires explicit waiver
    standing_failing_report = rr.aggregate(
        [
            rr.GateResult(name="full_suite", passed=True, detail="ok"),
            rr.GateResult(name="leak_scan", passed=True, detail="ok"),
            rr.GateResult(name="benchmark_thresholds", passed=True, detail="ok"),
            rr.GateResult(name="generated_drift", passed=True, detail="ok"),
            rr.GateResult(name="docs_checks", passed=True, detail="ok"),
            rr.GateResult(name="workflow_disposition", passed=True, detail="ok"),
            rr.GateResult(
                name="capability_freshness", passed=False, detail="seed claim unproven"
            ),
            rr.GateResult(name="changelog_versioning", passed=True, detail="ok"),
            rr.GateResult(name="artifact_manifest", passed=True, detail="ok"),
            rr.GateResult(name="residual_risk", passed=True, detail="signed"),
        ]
    )
    coord4 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    with pytest.raises(mc.ReleaseAuthorityError):
        coord4.authorize_release(
            interactive=True,
            input_handler=lambda _g: "approve",
            approver="maintainer",
            readiness_report=standing_failing_report,
            waived_standing_gates=(),
        )

    # Waiving the standing gate succeeds
    coord5 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    decision_waived = coord5.authorize_release(
        interactive=True,
        input_handler=lambda _g: "approve",
        approver="maintainer",
        readiness_report=standing_failing_report,
        waived_standing_gates=("capability_freshness",),
    )
    assert decision_waived.is_approved

    # 5. Hard gate failure cannot be waived and raises ReleaseAuthorityError
    hard_failing_report = rr.aggregate(
        [
            rr.GateResult(name="full_suite", passed=False, detail="tests failed"),
            rr.GateResult(name="leak_scan", passed=True, detail="ok"),
            rr.GateResult(name="residual_risk", passed=True, detail="signed"),
        ]
    )
    coord6 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    with pytest.raises(mc.ReleaseAuthorityError):
        coord6.authorize_release(
            interactive=True,
            input_handler=lambda _g: "approve",
            approver="maintainer",
            readiness_report=hard_failing_report,
        )

    # Attempting to waive a hard gate or residual_risk raises ReleaseAuthorityError
    coord7 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    with pytest.raises(mc.ReleaseAuthorityError):
        coord7.authorize_release(
            interactive=True,
            input_handler=lambda _g: "approve",
            approver="maintainer",
            readiness_report=clean_report,
            waived_standing_gates=("full_suite",),
        )

    with pytest.raises(mc.ReleaseAuthorityError):
        coord7.authorize_release(
            interactive=True,
            input_handler=lambda _g: "approve",
            approver="maintainer",
            readiness_report=clean_report,
            waived_standing_gates=("residual_risk",),
        )

    # 6. Unclassified gate is treated as hard
    unclassified_failing_report = rr.aggregate(
        [
            rr.GateResult(name="unclassified_custom_gate", passed=False, detail="boom"),
            rr.GateResult(name="residual_risk", passed=True, detail="signed"),
        ]
    )
    coord8 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    v_unclassified = coord8.verify_readiness(unclassified_failing_report)
    assert v_unclassified.recommendation == mc.RECOMMENDATION_NO_GO
    assert "unclassified_custom_gate" in v_unclassified.hard_failures

    coord9 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    with pytest.raises(mc.ReleaseAuthorityError):
        coord9.authorize_release(
            interactive=True,
            input_handler=lambda _g: "approve",
            approver="maintainer",
            readiness_report=unclassified_failing_report,
        )


def test_gate_classes_partition_the_emitted_gate_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate class sets are pairwise disjoint and their union equals build_report emitted gates."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    root = _build_synthetic_git_root(tmp_path)
    report = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=root,
        run_subprocess_gates=True,
    )
    emitted = {g.name for g in report.gates}

    assert mc.READINESS_ATTESTATION_GATES.isdisjoint(
        mc.READINESS_STANDING_WAIVABLE_GATES
    )
    assert mc.READINESS_ATTESTATION_GATES.isdisjoint(mc.READINESS_HARD_GATES)
    assert mc.READINESS_STANDING_WAIVABLE_GATES.isdisjoint(mc.READINESS_HARD_GATES)

    combined = (
        mc.READINESS_ATTESTATION_GATES
        | mc.READINESS_STANDING_WAIVABLE_GATES
        | mc.READINESS_HARD_GATES
    )
    assert combined == emitted


def test_not_applicable_gates_are_never_passes_and_never_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Not-applicable gates are never passed, never block release, and are surfaced to approver."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    tree = _build_managed_style_tree(tmp_path)

    # 1. Section 8 verification on managed-style tree
    rep_section8 = rr.build_report(
        suite_passed=True,
        residual_risk_signed=False,
        repo_root=tree,
        run_subprocess_gates=False,
    )
    assert rep_section8.not_applicable_gates() != []

    coord1 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    v = coord1.verify_readiness(rep_section8)

    for na_gate in rep_section8.not_applicable_gates():
        assert na_gate in v.not_applicable_gates
        assert na_gate not in v.passed_gates
        assert na_gate not in v.hard_failures
        assert na_gate not in v.standing_failures

    # Not-applicable gates do not force NO-GO: recommendation is GO because only residual_risk is pending
    assert v.recommendation == mc.RECOMMENDATION_GO
    assert v.pending_human_attestation is True

    # 2. Section 9 authorize_release surfaces not-applicable gates in prompt and metadata
    rep_section9 = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="maintainer",
        repo_root=tree,
        run_subprocess_gates=False,
    )
    captured_gates: List[Any] = []

    def handler(gate: Any) -> str:
        captured_gates.append(gate)
        return "approve"

    coord2 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    decision = coord2.authorize_release(
        interactive=True,
        input_handler=handler,
        approver="maintainer",
        readiness_report=rep_section9,
    )
    assert decision.is_approved
    assert len(captured_gates) == 1
    dg = captured_gates[0]
    for na_gate in rep_section9.not_applicable_gates():
        assert na_gate in dg.prompt
        assert na_gate in dg.metadata.get("not_applicable_gates", [])

    # 3. An attestation gate marked not-applicable is treated as a hard failure (fail closed)
    na_attestation_report = rr.aggregate(
        [
            rr.GateResult(
                name="full_suite", passed=False, detail="n/a", applicable=False
            ),
            rr.GateResult(
                name="residual_risk", passed=True, detail="signed", applicable=True
            ),
        ]
    )
    coord3 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    v_attestation = coord3.verify_readiness(na_attestation_report)
    assert v_attestation.recommendation == mc.RECOMMENDATION_NO_GO
    assert "full_suite" in v_attestation.hard_failures
    assert "full_suite" not in v_attestation.not_applicable_gates

    coord4 = mc.ReleaseReviewCoordinator(mode=mc.RELEASE_MODE_FULL)
    with pytest.raises(mc.ReleaseAuthorityError):
        coord4.authorize_release(
            interactive=True,
            input_handler=lambda _g: "approve",
            approver="maintainer",
            readiness_report=na_attestation_report,
        )

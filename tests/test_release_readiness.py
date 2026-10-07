"""Behavioral tests guarding release-readiness gates, aggregation, and invariants.

Restores test coverage for agent_workflows.release_readiness (dyiasf / 3rmvik).
All tests drive the code and assert observable outcomes over synthetic fixtures.
No source-reading, code-structure pins, or coupling to the live repository corpus.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import pytest

from agent_workflows import benchmark_thresholds as bt
from agent_workflows import release_readiness as rr


# ==================================================================================================
# Task group 1: deterministic pure-logic gates (E-01)
# ==================================================================================================


def test_gate_full_suite_passing() -> None:
    res = rr.gate_full_suite(True, {"passed": 42})
    assert res.name == "full_suite"
    assert res.passed is True
    assert res.detail == "full suite green"
    assert res.evidence == {"passed": 42}


def test_gate_full_suite_failing() -> None:
    res = rr.gate_full_suite(False, {"failed": 2})
    assert res.name == "full_suite"
    assert res.passed is False
    assert res.detail == "full suite RED"
    assert res.evidence == {"failed": 2}


def test_gate_generated_drift_passing() -> None:
    res = rr.gate_generated_drift([])
    assert res.name == "generated_drift"
    assert res.passed is True
    assert res.detail == "no generated/compiler drift"
    assert res.evidence == {"drift_files": []}


def test_gate_generated_drift_failing() -> None:
    res = rr.gate_generated_drift(["drifted_file.py"])
    assert res.name == "generated_drift"
    assert res.passed is False
    assert res.evidence == {"drift_files": ["drifted_file.py"]}


def test_gate_docs_checks_passing() -> None:
    res = rr.gate_docs_checks([])
    assert res.name == "docs_checks"
    assert res.passed is True
    assert res.detail == "docs checks pass"
    assert res.evidence == {"findings": []}


def test_gate_docs_checks_failing() -> None:
    res = rr.gate_docs_checks(["broken reference in docs/index.md"])
    assert res.name == "docs_checks"
    assert res.passed is False
    assert res.evidence == {"findings": ["broken reference in docs/index.md"]}


def test_gate_workflow_disposition_passing() -> None:
    res = rr.gate_workflow_disposition([])
    assert res.name == "workflow_disposition"
    assert res.passed is True
    assert res.detail == "all workflows dispositioned"
    assert res.evidence == {"undispositioned": []}


def test_gate_workflow_disposition_failing() -> None:
    res = rr.gate_workflow_disposition(["workflow_alpha"])
    assert res.name == "workflow_disposition"
    assert res.passed is False
    assert res.evidence == {"undispositioned": ["workflow_alpha"]}


def test_gate_capability_freshness_passing() -> None:
    res = rr.gate_capability_freshness([])
    assert res.name == "capability_freshness"
    assert res.passed is True
    assert res.detail == "no stale capability claims"
    assert res.evidence == {"stale_claims": []}


def test_gate_capability_freshness_failing() -> None:
    res = rr.gate_capability_freshness(["stale_capability_claim"])
    assert res.name == "capability_freshness"
    assert res.passed is False
    assert res.evidence == {"stale_claims": ["stale_capability_claim"]}


def test_gate_artifact_manifest_passing() -> None:
    res = rr.gate_artifact_manifest(manifest_present=True, consistent=True)
    assert res.name == "artifact_manifest"
    assert res.passed is True
    assert res.detail == "artifact manifest present and consistent"
    assert res.evidence == {"present": True, "consistent": True}


def test_gate_artifact_manifest_failing() -> None:
    res_missing = rr.gate_artifact_manifest(manifest_present=False, consistent=True)
    assert res_missing.name == "artifact_manifest"
    assert res_missing.passed is False
    assert res_missing.detail == "artifact manifest missing or inconsistent"
    assert res_missing.evidence == {"present": False, "consistent": True}

    res_inconsistent = rr.gate_artifact_manifest(
        manifest_present=True, consistent=False
    )
    assert res_inconsistent.name == "artifact_manifest"
    assert res_inconsistent.passed is False
    assert res_inconsistent.detail == "artifact manifest missing or inconsistent"
    assert res_inconsistent.evidence == {"present": True, "consistent": False}

    res_both = rr.gate_artifact_manifest(manifest_present=False, consistent=False)
    assert res_both.passed is False
    assert res_both.evidence == {"present": False, "consistent": False}


def test_gate_residual_risk_passing() -> None:
    res = rr.gate_residual_risk(signed_off=True, signer="Gabriele Fariello")
    assert res.name == "residual_risk"
    assert res.passed is True
    assert res.detail == "residual risk signed off by Gabriele Fariello"
    assert res.evidence == {"signed_off": True, "signer": "Gabriele Fariello"}


def test_gate_residual_risk_failing_unsigned() -> None:
    res = rr.gate_residual_risk(signed_off=False, signer="Gabriele Fariello")
    assert res.name == "residual_risk"
    assert res.passed is False
    assert res.detail == "residual-risk sign-off missing"
    assert res.evidence == {"signed_off": False, "signer": "Gabriele Fariello"}


def test_gate_residual_risk_failing_empty_signer() -> None:
    res = rr.gate_residual_risk(signed_off=True, signer="")
    assert res.name == "residual_risk"
    assert res.passed is False
    assert res.detail == "residual-risk sign-off missing"
    assert res.evidence == {"signed_off": True, "signer": ""}


# ==================================================================================================
# Task group 1: benchmark threshold invariants (E-02)
# ==================================================================================================


def test_gate_benchmark_thresholds_default_passes() -> None:
    res = rr.gate_benchmark_thresholds()
    assert res.name == "benchmark_thresholds"
    assert res.passed is True
    assert res.detail == "benchmark release invariants hold"
    assert res.evidence == {"violations": []}


def test_gate_benchmark_thresholds_corrupted_policy_fails() -> None:
    policy = bt.ThresholdPolicy()
    corrupted_risk = None
    for risk_class in list(policy.thresholds.keys()):
        # Corrupt one entry by setting max_critical_escapes = 1 (violating invariant).
        policy.thresholds[risk_class] = dataclasses.replace(
            policy.thresholds[risk_class], max_critical_escapes=1
        )
        corrupted_risk = risk_class
        break

    res = rr.gate_benchmark_thresholds(policy)
    assert res.name == "benchmark_thresholds"
    assert res.passed is False
    assert "violations" in res.evidence
    violations = res.evidence["violations"]
    assert len(violations) > 0
    assert any(corrupted_risk in v for v in violations)


# ==================================================================================================
# Task group 1: changelog versioning over synthetic trees (E-03)
# ==================================================================================================


def test_gate_changelog_versioning_valid_tree_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    (tmp_path / "CHANGELOG.md").write_text(
        "## 1.0.0\n- Initial release\n", encoding="utf-8"
    )
    version_dir = tmp_path / ".aw" / "system"
    version_dir.mkdir(parents=True)
    (version_dir / "VERSION").write_text("1.0.0\n", encoding="utf-8")

    res = rr.gate_changelog_versioning(tmp_path)
    assert res.name == "changelog_versioning"
    assert res.passed is True
    assert res.evidence["changelog"] is True
    assert res.evidence["version"] == "1.0.0"


def test_gate_changelog_versioning_missing_changelog_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    version_dir = tmp_path / ".aw" / "system"
    version_dir.mkdir(parents=True)
    (version_dir / "VERSION").write_text("1.0.0\n", encoding="utf-8")

    res = rr.gate_changelog_versioning(tmp_path)
    assert res.name == "changelog_versioning"
    assert res.passed is False
    assert res.evidence["changelog"] is False


def test_gate_changelog_versioning_changelog_without_heading_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    (tmp_path / "CHANGELOG.md").write_text(
        "Changelog without markdown heading\n", encoding="utf-8"
    )
    version_dir = tmp_path / ".aw" / "system"
    version_dir.mkdir(parents=True)
    (version_dir / "VERSION").write_text("1.0.0\n", encoding="utf-8")

    res = rr.gate_changelog_versioning(tmp_path)
    assert res.name == "changelog_versioning"
    assert res.passed is False
    assert res.evidence["changelog"] is False


def test_gate_changelog_versioning_sentinel_unknown_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # F-05: Non-git tree with valid CHANGELOG.md and NO VERSION file.
    # versioning.resolve_version returns sentinel 'unknown', which must NOT pass.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    (tmp_path / "CHANGELOG.md").write_text(
        "## Unreleased\n- Change\n", encoding="utf-8"
    )

    res = rr.gate_changelog_versioning(tmp_path)
    assert res.name == "changelog_versioning"
    assert (
        res.passed is False
    ), f"gate unexpectedly passed with evidence: {res.evidence}"


# ==================================================================================================
# Task group 2: aggregation, render and build_report (E-05)
# ==================================================================================================


def test_aggregate_all_pass_is_go() -> None:
    rep = rr.aggregate(
        [
            rr.GateResult("gate_a", True, "ok"),
            rr.GateResult("gate_b", True, "ok"),
        ]
    )
    assert rep.verdict == rr.VERDICT_GO
    assert rep.is_go is True
    assert rep.failing_gates() == []


def test_aggregate_one_fail_is_no_go() -> None:
    rep = rr.aggregate(
        [
            rr.GateResult("gate_a", True, "ok"),
            rr.GateResult("gate_b", False, "broken"),
        ]
    )
    assert rep.verdict == rr.VERDICT_NO_GO
    assert rep.is_go is False
    assert rep.failing_gates() == ["gate_b"]


def test_report_to_dict_json_serializable() -> None:
    rep = rr.aggregate(
        [
            rr.GateResult("gate_a", True, "ok", {"detail": "alpha"}),
            rr.GateResult("gate_b", False, "failed", {"code": 1}),
        ]
    )
    d = rep.to_dict()
    assert d["verdict"] == rr.VERDICT_NO_GO
    assert d["failing_gates"] == ["gate_b"]
    assert len(d["gates"]) == 2
    serialized = json.dumps(d)
    assert isinstance(serialized, str)


def test_report_render_verdict_and_failing_gates() -> None:
    # GO report render
    rep_go = rr.aggregate([rr.GateResult("gate_a", True, "ok")])
    rendered_go = rep_go.render()
    assert "Verdict: GO" in rendered_go

    # NO-GO report render
    rep_no_go = rr.aggregate(
        [
            rr.GateResult("gate_a", True, "ok"),
            rr.GateResult("gate_b", False, "failed"),
        ]
    )
    rendered_no_go = rep_no_go.render()
    assert "Verdict: NO-GO" in rendered_no_go
    assert "Failing gates: gate_b" in rendered_no_go


def _build_synthetic_root(tmp_path: Path) -> Path:
    root = tmp_path / "synthetic_repo"
    root.mkdir(parents=True, exist_ok=True)
    (root / "CHANGELOG.md").write_text("## 1.0.0\n- Release\n", encoding="utf-8")
    vdir = root / ".aw" / "system"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    return root


def test_build_report_red_suite_forces_no_go(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _build_synthetic_root(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    rep = rr.build_report(
        suite_passed=False,
        residual_risk_signed=True,
        residual_risk_signer="Gabriele Fariello",
        repo_root=root,
        run_subprocess_gates=False,
    )
    assert rep.verdict == rr.VERDICT_NO_GO
    assert "full_suite" in rep.failing_gates()


def test_build_report_unsigned_residual_risk_forces_no_go(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _build_synthetic_root(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    rep = rr.build_report(
        suite_passed=True,
        residual_risk_signed=False,
        repo_root=root,
        run_subprocess_gates=False,
    )
    assert rep.verdict == rr.VERDICT_NO_GO
    assert "residual_risk" in rep.failing_gates()


def test_build_report_clean_tree_is_go(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _build_synthetic_root(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    rep = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="Gabriele Fariello",
        repo_root=root,
        run_subprocess_gates=False,
    )
    assert rep.verdict == rr.VERDICT_GO
    assert rep.is_go is True
    assert rep.failing_gates() == []


# ==================================================================================================
# Task group 2: empty gate set aggregation (E-06)
# ==================================================================================================


def test_aggregate_empty_gate_set_is_not_go() -> None:
    rep = rr.aggregate([])
    assert (
        rep.verdict != rr.VERDICT_GO
    ), f"aggregate([]) unexpectedly returned {rep.verdict}"
    assert rep.is_go is False


# ==================================================================================================
# Task group 2: release action invariants and allowlist recorder (E-07)
# ==================================================================================================


def test_forbidden_release_actions_are_refused() -> None:
    for action in rr.FORBIDDEN_RELEASE_ACTIONS:
        with pytest.raises(rr.ReleaseActionForbiddenError):
            rr.assert_no_release_action(action)


def test_decision_only_actions_allowed() -> None:
    rr.assert_no_release_action("verdict")
    rr.assert_no_release_action("report")


def test_release_action_normalization() -> None:
    for raw in ("TAG", " Push ", "  DEPLOY  ", "ReLeAsE", "\tupload\n"):
        with pytest.raises(rr.ReleaseActionForbiddenError):
            rr.assert_no_release_action(raw)


def test_allowlist_recorder_decision_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _build_synthetic_root(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))

    recorded_calls: list[list[str]] = []

    def recording_run(argv, **kwargs):
        recorded_calls.append(list(argv))
        raise OSError("Subprocess execution intercepted by allowlist recorder")

    monkeypatch.setattr(rr.subprocess, "run", recording_run)

    rep = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="Gabriele Fariello",
        repo_root=root,
        run_subprocess_gates=False,
    )
    assert rep.verdict == rr.VERDICT_GO
    assert len(recorded_calls) > 0
    for argv in recorded_calls:
        assert argv[:2] == ["git", "describe"], f"unexpected command spawned: {argv}"

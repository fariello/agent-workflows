"""Behavioral tests guarding the not-applicable release readiness state (4bw2u5).

Tests model invariants, aggregation, rendering, individual producer contrast pairs,
never-not-applicable gates, managed-style tree reports, and CLI output modes.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import pytest

from agent_workflows import agent_schema
from agent_workflows import release_readiness as rr
from tests.test_release_readiness_producers import (
    _setup_full_go_tree,
)
from tests.test_releases_readiness_cli import (
    _build_subprocess_go_tree,
    _run_subprocess,
)


def test_model_not_applicable_is_neither_pass_nor_fail() -> None:
    na_gate = rr.GateResult("x", False, "input absent", applicable=False)
    assert na_gate.status == "not-applicable"
    assert na_gate.passed is False
    assert na_gate.applicable is False

    pass_gate = rr.GateResult("pass_gate", True, "ok")
    assert pass_gate.status == "pass"
    assert pass_gate.applicable is True

    rep = rr.aggregate([pass_gate, na_gate])
    assert rep.failing_gates() == []
    assert rep.not_applicable_gates() == ["x"]
    assert rep.passed_gates() == ["pass_gate"]
    assert rep.verdict == rr.VERDICT_GO

    buggy_na_gate = rr.GateResult("y", True, "ok", applicable=False)
    assert buggy_na_gate.status == "not-applicable"
    rep_buggy = rr.aggregate([pass_gate, buggy_na_gate])
    assert rep_buggy.not_applicable_gates() == ["y"]
    assert rep_buggy.passed_gates() == ["pass_gate"]
    assert rep_buggy.verdict == rr.VERDICT_GO


def test_model_all_not_applicable_is_no_go() -> None:
    na1 = rr.GateResult("x", False, "absent", applicable=False)
    na2 = rr.GateResult("y", False, "absent", applicable=False)
    rep = rr.aggregate([na1, na2])
    assert rep.verdict == rr.VERDICT_NO_GO
    assert rep.not_applicable_gates() == ["x", "y"]
    assert rep.failing_gates() == []
    assert rep.passed_gates() == []


def test_model_failure_still_forces_no_go_beside_not_applicable() -> None:
    na_gate = rr.GateResult("x", False, "absent", applicable=False)
    fail_gate = rr.GateResult("z", False, "failed")
    rep = rr.aggregate([na_gate, fail_gate])
    assert rep.verdict == rr.VERDICT_NO_GO
    assert rep.failing_gates() == ["z"]
    assert rep.not_applicable_gates() == ["x"]
    assert rep.passed_gates() == []


def test_model_to_dict_and_render_surface_not_applicable() -> None:
    pass_gate = rr.GateResult("a", True, "ok")
    na_gate = rr.GateResult("b", False, "missing input", applicable=False)
    fail_gate = rr.GateResult("c", False, "bad error")
    rep = rr.aggregate([pass_gate, na_gate, fail_gate])

    d = rep.to_dict()
    assert d["not_applicable_gates"] == ["b"]
    assert d["failing_gates"] == ["c"]
    assert d["passed_gates"] == ["a"]

    gate_b = next(g for g in d["gates"] if g["name"] == "b")
    assert gate_b["applicable"] is False
    assert gate_b["status"] == "not-applicable"

    gate_a = next(g for g in d["gates"] if g["name"] == "a")
    assert gate_a["applicable"] is True
    assert gate_a["status"] == "pass"

    serialized = json.dumps(d)
    assert "not-applicable" in serialized

    rendered = rep.render()
    assert "| b | N/A | missing input |" in rendered
    assert "| a | PASS | ok |" in rendered
    assert "| c | FAIL | bad error |" in rendered
    assert "WARNING: not-applicable gates (input absent, NOT verified): b" in rendered
    assert "1 passed, 1 not-applicable, 1 failed" in rendered


def test_producer_docs_checks_contrast_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    tree = tmp_path / "repo"
    tree.mkdir(parents=True, exist_ok=True)
    _setup_full_go_tree(tree)
    res = rr.gate_docs_checks(repo_root=tree)
    assert res.name == "docs_checks"
    assert res.passed is True
    assert res.applicable is True
    assert res.status == "pass"

    shutil.rmtree(tree / "docs")
    res_absent = rr.gate_docs_checks(repo_root=tree)
    assert res_absent.name == "docs_checks"
    assert res_absent.passed is False
    assert res_absent.applicable is False
    assert res_absent.status == "not-applicable"
    assert res_absent.evidence["missing"] is True
    assert res_absent.evidence["path"] == "docs"
    assert res_absent.evidence.get("findings") == []
    assert res_absent.detail.endswith("(input absent, NOT verified)")


def test_producer_capability_freshness_contrast_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    tree = tmp_path / "repo"
    tree.mkdir(parents=True, exist_ok=True)
    _setup_full_go_tree(tree)
    res = rr.gate_capability_freshness(repo_root=tree)
    assert res.name == "capability_freshness"
    assert res.passed is True
    assert res.applicable is True
    assert res.status == "pass"

    matrix_path = (
        tree
        / ".aw"
        / "system"
        / "workflows"
        / "conformance"
        / "tools"
        / "host_matrix.json"
    )
    matrix_path.unlink()
    res_absent = rr.gate_capability_freshness(repo_root=tree)
    assert res_absent.name == "capability_freshness"
    assert res_absent.passed is False
    assert res_absent.applicable is False
    assert res_absent.status == "not-applicable"
    assert res_absent.evidence["missing"] is True
    assert (
        res_absent.evidence["path"]
        == ".aw/system/workflows/conformance/tools/host_matrix.json"
    )
    assert res_absent.evidence.get("stale_claims") == []
    assert res_absent.detail.endswith("(input absent, NOT verified)")


def test_producer_generated_drift_contrast_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("yaml")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    tree = tmp_path / "repo"
    tree.mkdir(parents=True, exist_ok=True)
    _setup_full_go_tree(tree)

    from agent_workflows import workflow_compiler, workflow_loader
    from agent_workflows.workflow_cli import _write_generated

    pkg_dir = tree / ".aw" / "system" / "workflows" / "plan-review"
    shutil.copytree("tests/fixtures/workflow-src/plan-review", pkg_dir)
    load_res = workflow_loader.load_package(pkg_dir)
    assert load_res.ok and load_res.ir is not None
    compiled = workflow_compiler.compile_workflow(load_res.ir)
    expected = workflow_compiler.render_generated_files(compiled)
    _write_generated(Path(load_res.ir["source_root"]), expected)

    res = rr.gate_generated_drift(repo_root=tree)
    assert res.name == "generated_drift"
    assert res.passed is True
    assert res.applicable is True
    assert res.status == "pass"
    assert res.evidence.get("packages_checked") == 1

    shutil.rmtree(pkg_dir)
    res_absent = rr.gate_generated_drift(repo_root=tree)
    assert res_absent.name == "generated_drift"
    assert res_absent.passed is False
    assert res_absent.applicable is False
    assert res_absent.status == "not-applicable"
    assert res_absent.evidence["missing"] is True
    assert res_absent.evidence["path"] == ".aw/system/workflows/*/workflow.yaml"
    assert res_absent.evidence.get("packages_checked") == 0
    assert res_absent.evidence.get("drift_files") == []
    assert res_absent.detail.endswith("(input absent, NOT verified)")


def test_producer_workflow_disposition_contrast_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    tree = tmp_path / "repo"
    tree.mkdir(parents=True, exist_ok=True)
    _setup_full_go_tree(tree)
    res = rr.gate_workflow_disposition(repo_root=tree)
    assert res.name == "workflow_disposition"
    assert res.passed is True
    assert res.applicable is True
    assert res.status == "pass"

    manifest_path = tree / ".aw" / "system" / "workflows" / "index.md"
    manifest_path.unlink()
    res_absent = rr.gate_workflow_disposition(repo_root=tree)
    assert res_absent.name == "workflow_disposition"
    assert res_absent.passed is False
    assert res_absent.applicable is False
    assert res_absent.status == "not-applicable"
    assert res_absent.evidence["missing"] is True
    assert res_absent.evidence["path"] == ".aw/system/workflows/index.md"
    assert res_absent.evidence.get("undispositioned") == []
    assert res_absent.detail.endswith("(input absent, NOT verified)")


def test_producer_changelog_versioning_contrast_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    tree = tmp_path / "repo"
    tree.mkdir(parents=True, exist_ok=True)
    _setup_full_go_tree(tree)
    res = rr.gate_changelog_versioning(repo_root=tree)
    assert res.name == "changelog_versioning"
    assert res.passed is True
    assert res.applicable is True
    assert res.status == "pass"

    (tree / "CHANGELOG.md").unlink()
    res_absent = rr.gate_changelog_versioning(repo_root=tree)
    assert res_absent.name == "changelog_versioning"
    assert res_absent.passed is False
    assert res_absent.applicable is False
    assert res_absent.status == "not-applicable"
    assert res_absent.evidence["missing"] is True
    assert res_absent.evidence["path"] == "CHANGELOG.md"
    assert res_absent.evidence["changelog"] is False
    assert res_absent.evidence["version"] == "1.0.0"
    assert res_absent.detail.endswith("(input absent, NOT verified)")


def test_changelog_absent_with_unknown_version_still_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    tree = tmp_path / "repo"
    tree.mkdir(parents=True, exist_ok=True)
    _setup_full_go_tree(tree)
    (tree / "CHANGELOG.md").unlink()
    vfile = tree / ".aw" / "system" / "VERSION"
    vfile.write_text("unknown\n", encoding="utf-8")
    res = rr.gate_changelog_versioning(repo_root=tree)
    assert res.name == "changelog_versioning"
    assert res.passed is False
    assert res.applicable is True
    assert res.status == "fail"


def test_never_not_applicable_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    res_suite = rr.gate_full_suite(None)
    assert res_suite.passed is False
    assert res_suite.applicable is True
    assert res_suite.status == "fail"

    res_risk = rr.gate_residual_risk(False)
    assert res_risk.passed is False
    assert res_risk.applicable is True
    assert res_risk.status == "fail"

    empty_tree = tmp_path / "empty_repo"
    empty_tree.mkdir()
    res_drift_no_wf = rr.gate_generated_drift(repo_root=empty_tree)
    assert res_drift_no_wf.passed is False
    assert res_drift_no_wf.applicable is True
    assert res_drift_no_wf.status == "fail"

    res_disp_no_wf = rr.gate_workflow_disposition(repo_root=empty_tree)
    assert res_disp_no_wf.passed is False
    assert res_disp_no_wf.applicable is True
    assert res_disp_no_wf.status == "fail"

    res_manifest = rr.gate_artifact_manifest(repo_root=empty_tree)
    assert res_manifest.passed is False
    assert res_manifest.applicable is True
    assert res_manifest.status == "fail"

    res_inj_docs = rr.gate_docs_checks(doc_findings=[], repo_root=empty_tree)
    assert res_inj_docs.passed is True
    assert res_inj_docs.applicable is True
    assert res_inj_docs.status == "pass"

    res_inj_claims = rr.gate_capability_freshness(stale_claims=[], repo_root=empty_tree)
    assert res_inj_claims.passed is True
    assert res_inj_claims.applicable is True
    assert res_inj_claims.status == "pass"

    res_inj_drift = rr.gate_generated_drift(drift_files=[], repo_root=empty_tree)
    assert res_inj_drift.passed is True
    assert res_inj_drift.applicable is True
    assert res_inj_drift.status == "pass"

    res_inj_disp = rr.gate_workflow_disposition(
        undispositioned=[], repo_root=empty_tree
    )
    assert res_inj_disp.passed is True
    assert res_inj_disp.applicable is True
    assert res_inj_disp.status == "pass"


def test_build_report_managed_style_tree_is_go_with_not_applicable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    tree = tmp_path / "repo"
    tree.mkdir(parents=True, exist_ok=True)
    _setup_full_go_tree(tree)
    shutil.rmtree(tree / "docs")
    (tree / "CHANGELOG.md").unlink()
    (
        tree
        / ".aw"
        / "system"
        / "workflows"
        / "conformance"
        / "tools"
        / "host_matrix.json"
    ).unlink()

    report = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=tree,
        run_subprocess_gates=False,
    )
    assert report.verdict == rr.VERDICT_GO
    assert report.failing_gates() == []
    assert report.not_applicable_gates() == [
        "generated_drift",
        "docs_checks",
        "capability_freshness",
        "changelog_versioning",
    ]

    report_nogo = rr.build_report(
        suite_passed=False,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=tree,
        run_subprocess_gates=False,
    )
    assert report_nogo.verdict == rr.VERDICT_NO_GO
    assert report_nogo.failing_gates() == ["full_suite"]
    assert report_nogo.not_applicable_gates() == [
        "generated_drift",
        "docs_checks",
        "capability_freshness",
        "changelog_versioning",
    ]


def test_cli_surfaces_not_applicable_in_every_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tree = _build_subprocess_go_tree(tmp_path, monkeypatch)
    shutil.rmtree(tree / "docs")
    (tree / "CHANGELOG.md").unlink()
    (
        tree
        / ".aw"
        / "system"
        / "workflows"
        / "conformance"
        / "tools"
        / "host_matrix.json"
    ).unlink()

    expected_na = [
        "generated_drift",
        "docs_checks",
        "capability_freshness",
        "changelog_versioning",
    ]

    proc_human = _run_subprocess(
        [
            "releases",
            "readiness",
            "--suite-passed",
            "--residual-risk-signer",
            "qa",
        ],
        cwd=tree,
    )
    assert (
        proc_human.returncode == 0
    ), f"stderr={proc_human.stderr}\nstdout={proc_human.stdout}"
    warning_line = (
        "WARNING: not-applicable gates (input absent, NOT verified): "
        + ", ".join(expected_na)
    )
    assert warning_line in proc_human.stdout
    assert warning_line in proc_human.stderr

    proc_json = _run_subprocess(
        [
            "releases",
            "readiness",
            "--suite-passed",
            "--residual-risk-signer",
            "qa",
            "--json",
        ],
        cwd=tree,
    )
    assert proc_json.returncode == 0
    data_json = json.loads(proc_json.stdout)
    assert data_json["data"]["not_applicable_gates"] == expected_na

    proc_agent = _run_subprocess(
        [
            "releases",
            "readiness",
            "--suite-passed",
            "--residual-risk-signer",
            "qa",
            "--agent",
        ],
        cwd=tree,
    )
    assert proc_agent.returncode == 0
    lines = [ln for ln in proc_agent.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert agent_schema.validate_agent_record(rec) == []
    assert rec["exit"] == 0
    assert rec["outcome"] == "clean"
    expected_rules = {f"readiness.{g}.not-applicable" for g in expected_na}
    actual_rules = {d["rule"] for d in rec["diagnostics"]}
    assert actual_rules == expected_rules
    assert rec["findings_by_severity"] == {"error": 0, "warning": 4, "info": 0}

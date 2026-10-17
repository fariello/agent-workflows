"""Behavioral tests guarding release-readiness live producers.

Verifies that gate_generated_drift, gate_workflow_disposition, and
gate_capability_freshness compute findings from repo_root, distinguish clean
from drifting/undispositioned/stale trees, fail closed on missing trees or
producer errors, and preserve explicit injection.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import pytest

from agent_workflows import release_readiness as rr


def setup_minimal_workflows_tree(repo_root: Path) -> Path:
    """Create minimal valid workflows tree satisfying disposition and capability checks."""
    wf_dir = repo_root / ".aw" / "system" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    body_dir = wf_dir / "whatnext"
    body_dir.mkdir(parents=True, exist_ok=True)
    (body_dir / "whatnext.md").write_text("# whatnext\n", encoding="utf-8")
    (wf_dir / "index.md").write_text(
        "# Workflows\n"
        "<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
        "| command | body | description |\n"
        "|---|---|---|\n"
        "| whatnext | .aw/system/workflows/whatnext/whatnext.md | Recommend next action |\n"
        "<!-- WORKFLOWS-MANIFEST:END -->\n",
        encoding="utf-8",
    )
    conf_dir = wf_dir / "conformance"
    conf_dir.mkdir(parents=True, exist_ok=True)
    (conf_dir / "operator-protocol.md").write_text(
        "# Operator Protocol\n", encoding="utf-8"
    )
    tools_dir = conf_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "host_matrix.json").write_text(
        json.dumps({"hosts": {"test_host": {}}}), encoding="utf-8"
    )
    return wf_dir


def _setup_full_go_tree(repo_root: Path) -> Path:
    """Create full minimal repo tree satisfying all non-subprocess gates."""
    changelog = repo_root / "CHANGELOG.md"
    changelog.write_text("## 1.0.0 - 2026-10-02\nInitial release\n", encoding="utf-8")
    vdir = repo_root / ".aw" / "system"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "index.md").write_text(
        "# Documentation\nClean text with ASCII hyphen.\n", encoding="utf-8"
    )
    setup_minimal_workflows_tree(repo_root)
    return repo_root


# ==================================================================================================
# Drift gate arms (a..e)
# ==================================================================================================


def test_drift_missing_generated_fails_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (a): canonical package with NO _generated/ fails listing missing entries."""
    pytest.importorskip("yaml")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    pkg_dir = tmp_path / ".aw" / "system" / "workflows" / "plan-review"
    shutil.copytree("tests/fixtures/workflow-src/plan-review", pkg_dir)

    res = rr.gate_generated_drift(repo_root=tmp_path)
    assert res.name == "generated_drift"
    assert res.passed is False
    assert "drifted file(s)" in res.detail
    drift_files = res.evidence.get("drift_files", [])
    assert len(drift_files) > 0
    assert any("missing" in d for d in drift_files)


def test_drift_compiled_generated_passes_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (b): package after writing compiler output passes with packages_checked == 1."""
    pytest.importorskip("yaml")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    pkg_dir = tmp_path / ".aw" / "system" / "workflows" / "plan-review"
    shutil.copytree("tests/fixtures/workflow-src/plan-review", pkg_dir)

    from agent_workflows import workflow_compiler, workflow_loader
    from agent_workflows.workflow_cli import _write_generated

    load_res = workflow_loader.load_package(pkg_dir)
    assert load_res.ok and load_res.ir is not None
    compiled = workflow_compiler.compile_workflow(load_res.ir)
    expected = workflow_compiler.render_generated_files(compiled)
    _write_generated(Path(load_res.ir["source_root"]), expected)

    res = rr.gate_generated_drift(repo_root=tmp_path)
    assert res.name == "generated_drift"
    assert res.passed is True
    assert res.detail == "no generated/compiler drift"
    assert res.evidence.get("packages_checked") == 1
    assert res.evidence.get("drift_files") == []


def test_drift_changed_generated_fails_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (c): after hand-editing one generated file it fails naming changed."""
    pytest.importorskip("yaml")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    pkg_dir = tmp_path / ".aw" / "system" / "workflows" / "plan-review"
    shutil.copytree("tests/fixtures/workflow-src/plan-review", pkg_dir)

    from agent_workflows import workflow_compiler, workflow_loader
    from agent_workflows.workflow_cli import _write_generated

    load_res = workflow_loader.load_package(pkg_dir)
    assert load_res.ok and load_res.ir is not None
    compiled = workflow_compiler.compile_workflow(load_res.ir)
    expected = workflow_compiler.render_generated_files(compiled)
    _write_generated(Path(load_res.ir["source_root"]), expected)

    prompt_path = Path(load_res.ir["source_root"]) / "_generated" / "prompt.md"
    prompt_path.write_text("hand-modified content\n", encoding="utf-8")

    res = rr.gate_generated_drift(repo_root=tmp_path)
    assert res.name == "generated_drift"
    assert res.passed is False
    drift_files = res.evidence.get("drift_files", [])
    assert any("changed" in d and "prompt.md" in d for d in drift_files)


def test_drift_zero_packages_is_not_applicable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (d): zero packages reports not-applicable with distinct detail and packages_checked == 0."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    wf_dir = tmp_path / ".aw" / "system" / "workflows"
    wf_dir.mkdir(parents=True)

    res = rr.gate_generated_drift(repo_root=tmp_path)
    assert res.name == "generated_drift"
    assert res.passed is False
    assert res.applicable is False
    assert res.status == "not-applicable"
    assert (
        res.detail
        == "no canonical workflow packages to check (input absent, NOT verified)"
    )
    assert res.evidence.get("missing") is True
    assert res.evidence.get("path") == ".aw/system/workflows/*/workflow.yaml"
    assert res.evidence.get("packages_checked") == 0
    assert res.evidence.get("drift_files") == []


def test_drift_missing_workflows_dir_fails_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (e): missing workflows directory fails closed with missing evidence."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    res = rr.gate_generated_drift(repo_root=tmp_path)
    assert res.name == "generated_drift"
    assert res.passed is False
    assert res.evidence.get("missing") is True
    assert res.evidence.get("path") == ".aw/system/workflows"
    assert res.evidence.get("drift_files") == []


# ==================================================================================================
# Disposition gate arms (f..i2)
# ==================================================================================================


def test_disposition_minimal_valid_tree_passes_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (f): the minimal valid workflows tree passes disposition checks."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)

    res = rr.gate_workflow_disposition(repo_root=tmp_path)
    assert res.name == "workflow_disposition"
    assert res.passed is True
    assert res.detail == "all workflows dispositioned"
    assert res.evidence.get("undispositioned") == []
    assert res.evidence.get("dispositions", 0) >= 1


def test_disposition_missing_conformance_file_fails_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (g): deleted conformance/operator-protocol.md fails with that finding."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)
    proto = (
        tmp_path
        / ".aw"
        / "system"
        / "workflows"
        / "conformance"
        / "operator-protocol.md"
    )
    proto.unlink()

    res = rr.gate_workflow_disposition(repo_root=tmp_path)
    assert res.name == "workflow_disposition"
    assert res.passed is False
    undone = res.evidence.get("undispositioned", [])
    assert len(undone) > 0
    assert any("conformance entry file missing" in u for u in undone)


def test_disposition_unassigned_command_fails_without_raising(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (h): manifest row with unassigned command in source checkout fails (InventoryError) without raising (ufawpb)."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "agent-workflows"\n', encoding="utf-8"
    )
    (tmp_path / ".aw" / "system" / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    index_md = tmp_path / ".aw" / "system" / "workflows" / "index.md"
    index_md.write_text(
        "# Workflows\n"
        "<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
        "| command | body | description |\n"
        "|---|---|---|\n"
        "| unassigned_zzz | workflows/unassigned.md | Unknown workflow |\n"
        "<!-- WORKFLOWS-MANIFEST:END -->\n",
        encoding="utf-8",
    )

    res = rr.gate_workflow_disposition(repo_root=tmp_path)
    assert res.name == "workflow_disposition"
    assert res.passed is False
    undone = res.evidence.get("undispositioned", [])
    assert len(undone) == 1
    assert "no reviewed family assignment" in undone[0]


def test_disposition_missing_manifest_markers_fails_without_raising(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (i): index.md with no markers fails with SystemExit without raising."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)
    index_md = tmp_path / ".aw" / "system" / "workflows" / "index.md"
    index_md.write_text("# Workflows without manifest markers\n", encoding="utf-8")

    res = rr.gate_workflow_disposition(repo_root=tmp_path)
    assert res.name == "workflow_disposition"
    assert res.passed is False
    assert "could not run: SystemExit" in res.detail
    assert res.evidence.get("error") == "SystemExit"
    assert res.evidence.get("undispositioned") == []


def test_disposition_missing_index_md_is_not_applicable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (i2): workflows dir with no index.md reports not-applicable."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    wf_dir = tmp_path / ".aw" / "system" / "workflows"
    wf_dir.mkdir(parents=True)

    res = rr.gate_workflow_disposition(repo_root=tmp_path)
    assert res.name == "workflow_disposition"
    assert res.passed is False
    assert res.applicable is False
    assert res.status == "not-applicable"
    assert "workflow manifest missing: .aw/system/workflows/index.md" in res.detail
    assert res.evidence.get("missing") is True
    assert res.evidence.get("path") == ".aw/system/workflows/index.md"
    assert res.evidence.get("undispositioned") == []


# ==================================================================================================
# Capability freshness gate arms (j..l)
# ==================================================================================================


def test_capability_supported_boolean_fails_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (j): matrix with one supported: true boolean fails naming host:feature."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)
    matrix_file = (
        tmp_path
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

    res = rr.gate_capability_freshness(repo_root=tmp_path)
    assert res.name == "capability_freshness"
    assert res.passed is False
    assert "stale claim(s)" in res.detail
    stale = res.evidence.get("stale_claims", [])
    assert len(stale) == 1
    assert "test_host:t1_policy" in stale[0]
    assert res.evidence.get("claims_checked") == 1


def test_capability_empty_matrix_passes_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (k): matrix with none passes with claims_checked == 0."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)

    res = rr.gate_capability_freshness(repo_root=tmp_path)
    assert res.name == "capability_freshness"
    assert res.passed is True
    assert res.detail == "no stale capability claims"
    assert res.evidence.get("claims_checked") == 0
    assert res.evidence.get("stale_claims") == []


def test_capability_missing_matrix_is_not_applicable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (l): missing matrix file reports not-applicable."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)
    matrix_file = (
        tmp_path
        / ".aw"
        / "system"
        / "workflows"
        / "conformance"
        / "tools"
        / "host_matrix.json"
    )
    matrix_file.unlink()

    res = rr.gate_capability_freshness(repo_root=tmp_path)
    assert res.name == "capability_freshness"
    assert res.passed is False
    assert res.applicable is False
    assert res.status == "not-applicable"
    assert res.evidence.get("missing") is True
    assert (
        res.evidence.get("path")
        == ".aw/system/workflows/conformance/tools/host_matrix.json"
    )
    assert res.evidence.get("stale_claims") == []
    assert res.detail.endswith("(input absent, NOT verified)")


# ==================================================================================================
# Explicit injection bypass arm (m)
# ==================================================================================================


def test_explicit_injection_bypasses_filesystem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (m): for each gate, explicit [] passes and one-element list fails without touching fs."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    # tmp_path has NO .aw tree at all

    # Drift gate
    res_drift_pass = rr.gate_generated_drift([], repo_root=tmp_path)
    assert res_drift_pass.passed is True
    assert res_drift_pass.evidence["drift_files"] == []
    res_drift_fail = rr.gate_generated_drift(["drift.py: missing"], repo_root=tmp_path)
    assert res_drift_fail.passed is False
    assert res_drift_fail.evidence["drift_files"] == ["drift.py: missing"]

    # Disposition gate
    res_disp_pass = rr.gate_workflow_disposition([], repo_root=tmp_path)
    assert res_disp_pass.passed is True
    assert res_disp_pass.evidence["undispositioned"] == []
    res_disp_fail = rr.gate_workflow_disposition(["wf_missing"], repo_root=tmp_path)
    assert res_disp_fail.passed is False
    assert res_disp_fail.evidence["undispositioned"] == ["wf_missing"]

    # Capability gate
    res_cap_pass = rr.gate_capability_freshness([], repo_root=tmp_path)
    assert res_cap_pass.passed is True
    assert res_cap_pass.evidence["stale_claims"] == []
    res_cap_fail = rr.gate_capability_freshness(
        ["host:feat: unproven"], repo_root=tmp_path
    )
    assert res_cap_fail.passed is False
    assert res_cap_fail.evidence["stale_claims"] == ["host:feat: unproven"]


# ==================================================================================================
# End to end and build_report falsifiability arms (n, o, p, q)
# ==================================================================================================


def test_end_to_end_governance_report_contrast(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (n): clean tree is GO, then adding one supported: true makes it NO-GO on capability_freshness."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    _setup_full_go_tree(tmp_path)

    # Clean tree -> VERDICT_GO
    rep_clean = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=tmp_path,
        run_subprocess_gates=False,
    )
    assert rep_clean.verdict == rr.VERDICT_GO
    assert rep_clean.failing_gates() == []

    # Dirty tree: add supported: true
    matrix_file = (
        tmp_path
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

    rep_dirty = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=tmp_path,
        run_subprocess_gates=False,
    )
    assert rep_dirty.verdict == rr.VERDICT_NO_GO
    assert rep_dirty.failing_gates() == ["capability_freshness"]


def test_build_report_fails_on_generated_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (o): build_report over a package with no _generated/ fails on generated_drift."""
    pytest.importorskip("yaml")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    _setup_full_go_tree(tmp_path)
    pkg_dir = tmp_path / ".aw" / "system" / "workflows" / "plan-review"
    shutil.copytree("tests/fixtures/workflow-src/plan-review", pkg_dir)

    rep = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=tmp_path,
        run_subprocess_gates=False,
    )
    assert rep.verdict == rr.VERDICT_NO_GO
    assert "generated_drift" in rep.failing_gates()


def test_build_report_fails_on_workflow_disposition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (p): build_report with deleted conformance file fails on workflow_disposition."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    _setup_full_go_tree(tmp_path)
    proto = (
        tmp_path
        / ".aw"
        / "system"
        / "workflows"
        / "conformance"
        / "operator-protocol.md"
    )
    proto.unlink()

    rep = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=tmp_path,
        run_subprocess_gates=False,
    )
    assert rep.verdict == rr.VERDICT_NO_GO
    assert "workflow_disposition" in rep.failing_gates()


def test_build_report_fails_on_capability_freshness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (q): build_report with one supported: true fails on capability_freshness."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    _setup_full_go_tree(tmp_path)
    matrix_file = (
        tmp_path
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

    rep = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=tmp_path,
        run_subprocess_gates=False,
    )
    assert rep.verdict == rr.VERDICT_NO_GO
    assert "capability_freshness" in rep.failing_gates()


# ==================================================================================================
# Artifact manifest gate arms (r1..r7)
# ==================================================================================================


def test_artifact_manifest_minimal_valid_tree_passes_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (r1): minimal valid workflows tree passes artifact_manifest gate."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)

    res = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res.name == "artifact_manifest"
    assert res.passed is True
    assert res.detail == "artifact manifest present and consistent"
    assert res.evidence["present"] is True
    assert res.evidence["consistent"] is True
    assert res.evidence["workflows_checked"] == 1
    assert res.evidence["problems"] == []

    # Also passes when .aw/system/VERSION and matching stamps in index.md are present
    vdir = tmp_path / ".aw" / "system"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    index_file = tmp_path / ".aw" / "system" / "workflows" / "index.md"
    index_file.write_text(
        "# Workflows\n"
        "<!-- WORKFLOWS-VERSION: 1.0.0 -->\n"
        "Version: `1.0.0`\n"
        "<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
        "| command | body | description |\n"
        "|---|---|---|\n"
        "| whatnext | .aw/system/workflows/whatnext/whatnext.md | Recommend next action |\n"
        "<!-- WORKFLOWS-MANIFEST:END -->\n",
        encoding="utf-8",
    )
    res_v = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res_v.passed is True
    assert res_v.evidence["problems"] == []


def test_artifact_manifest_missing_index_fails_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (r2): missing index.md fails artifact_manifest gate."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)
    (tmp_path / ".aw" / "system" / "workflows" / "index.md").unlink()

    res = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res.passed is False
    assert res.evidence["present"] is False
    assert res.evidence["consistent"] is False
    assert (
        "artifact manifest missing: .aw/system/workflows/index.md"
        in res.evidence["problems"]
    )


def test_artifact_manifest_missing_body_and_lens_fail_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (r3): manifest row with missing body or lens fails gate while drift and disposition pass."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)

    # Missing body file
    (tmp_path / ".aw" / "system" / "workflows" / "whatnext" / "whatnext.md").unlink()
    res = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res.passed is False
    assert res.evidence["present"] is True
    assert res.evidence["consistent"] is False
    assert any(
        "missing body file" in p and ".aw/system/workflows/whatnext/whatnext.md" in p
        for p in res.evidence["problems"]
    )

    # drift is not-applicable and disposition passes on the exact same tree
    drift_res = rr.gate_generated_drift(repo_root=tmp_path)
    assert drift_res.applicable is False
    assert drift_res.status == "not-applicable"
    assert rr.gate_workflow_disposition(repo_root=tmp_path).passed is True

    # Recreate body, add a lens column with missing lens file
    (tmp_path / ".aw" / "system" / "workflows" / "whatnext" / "whatnext.md").write_text(
        "# whatnext\n", encoding="utf-8"
    )
    index_file = tmp_path / ".aw" / "system" / "workflows" / "index.md"
    index_file.write_text(
        "# Workflows\n"
        "<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
        "| command | body | lens | description |\n"
        "|---|---|---|---|\n"
        "| whatnext | .aw/system/workflows/whatnext/whatnext.md | .aw/system/workflows/whatnext/lens.md | Recommend next action |\n"
        "<!-- WORKFLOWS-MANIFEST:END -->\n",
        encoding="utf-8",
    )
    res_lens = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res_lens.passed is False
    assert res_lens.evidence["present"] is True
    assert res_lens.evidence["consistent"] is False
    assert any(
        "missing lens file" in p and ".aw/system/workflows/whatnext/lens.md" in p
        for p in res_lens.evidence["problems"]
    )


def test_artifact_manifest_unparseable_and_duplicate_command_fail_without_raising(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (r4): missing markers, duplicate command, and invalid UTF-8 fail closed without raising."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)
    index_file = tmp_path / ".aw" / "system" / "workflows" / "index.md"

    # Missing markers -> engine.parse_manifest raises SystemExit, gate catches and fails
    index_file.write_text(
        "# Workflows without markers\n| command | body |\n", encoding="utf-8"
    )
    res_no_markers = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res_no_markers.passed is False
    assert res_no_markers.evidence["present"] is True
    assert res_no_markers.evidence["consistent"] is False
    assert any(
        "manifest parse failed: SystemExit" in p
        for p in res_no_markers.evidence["problems"]
    )

    # Duplicate whatnext rows
    index_file.write_text(
        "# Workflows\n"
        "<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
        "| command | body | description |\n"
        "|---|---|---|\n"
        "| whatnext | .aw/system/workflows/whatnext/whatnext.md | First |\n"
        "| whatnext | .aw/system/workflows/whatnext/whatnext.md | Second |\n"
        "<!-- WORKFLOWS-MANIFEST:END -->\n",
        encoding="utf-8",
    )
    res_dup = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res_dup.passed is False
    assert res_dup.evidence["present"] is True
    assert res_dup.evidence["consistent"] is False
    assert "duplicate command: whatnext" in res_dup.evidence["problems"]

    # Invalid UTF-8 bytes
    index_file.write_bytes(
        b"# Workflows\n\xff\xfe\n<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
    )
    res_bad_utf8 = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res_bad_utf8.passed is False
    assert res_bad_utf8.evidence["present"] is True
    assert res_bad_utf8.evidence["consistent"] is False
    assert res_bad_utf8.evidence["problems"] == [
        "manifest parse failed: UnicodeDecodeError"
    ]
    assert str(tmp_path) not in json.dumps(res_bad_utf8.evidence)


def test_artifact_manifest_version_stamp_mismatch_fails_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (r5): mismatch between index.md stamps and .aw/system/VERSION fails gate."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)
    vdir = tmp_path / ".aw" / "system"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "VERSION").write_text("1.0.0\n", encoding="utf-8")

    index_file = tmp_path / ".aw" / "system" / "workflows" / "index.md"
    index_file.write_text(
        "# Workflows\n"
        "<!-- WORKFLOWS-VERSION: 2.0.0 -->\n"
        "Version: `2.0.0`\n"
        "<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
        "| command | body | description |\n"
        "|---|---|---|\n"
        "| whatnext | .aw/system/workflows/whatnext/whatnext.md | Recommend next action |\n"
        "<!-- WORKFLOWS-MANIFEST:END -->\n",
        encoding="utf-8",
    )
    res = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res.passed is False
    assert res.evidence["present"] is True
    assert res.evidence["consistent"] is False
    assert any(
        "2.0.0" in p and ".aw/system/VERSION" in p for p in res.evidence["problems"]
    )


def test_artifact_manifest_rejects_escaping_and_parent_relative_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (r3b): escaping paths, symlinks outside repo, and parent-relative paths are rejected."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)
    index_file = tmp_path / ".aw" / "system" / "workflows" / "index.md"

    # Escaping body with ..
    outside_file = tmp_path.parent / "outside.md"
    outside_file.write_text("# outside\n", encoding="utf-8")
    index_file.write_text(
        "# Workflows\n"
        "<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
        "| command | body | description |\n"
        "|---|---|---|\n"
        "| whatnext | ../outside.md | Escaping path |\n"
        "<!-- WORKFLOWS-MANIFEST:END -->\n",
        encoding="utf-8",
    )
    res_escape = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res_escape.passed is False
    assert res_escape.evidence["consistent"] is False
    assert any("invalid body path" in p for p in res_escape.evidence["problems"])

    # Symlink pointing outside repo
    symlink_file = tmp_path / ".aw" / "system" / "workflows" / "symlink_body.md"
    if symlink_file.exists() or symlink_file.is_symlink():
        symlink_file.unlink()
    symlink_file.symlink_to(outside_file)
    index_file.write_text(
        "# Workflows\n"
        "<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
        "| command | body | description |\n"
        "|---|---|---|\n"
        "| whatnext | .aw/system/workflows/symlink_body.md | Out of repo symlink |\n"
        "<!-- WORKFLOWS-MANIFEST:END -->\n",
        encoding="utf-8",
    )
    res_symlink = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res_symlink.passed is False
    assert res_symlink.evidence["consistent"] is False
    assert any("missing body file" in p for p in res_symlink.evidence["problems"])

    # Parent-relative path (workflows/whatnext.md present ONLY at index.md's parent)
    parent_target = (
        tmp_path / ".aw" / "system" / "workflows" / "workflows" / "whatnext.md"
    )
    parent_target.parent.mkdir(parents=True, exist_ok=True)
    parent_target.write_text("# relative\n", encoding="utf-8")
    index_file.write_text(
        "# Workflows\n"
        "<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
        "| command | body | description |\n"
        "|---|---|---|\n"
        "| whatnext | workflows/whatnext.md | Only at parent |\n"
        "<!-- WORKFLOWS-MANIFEST:END -->\n",
        encoding="utf-8",
    )
    res_parent = rr.gate_artifact_manifest(repo_root=tmp_path)
    assert res_parent.passed is False
    assert res_parent.evidence["consistent"] is False
    assert any(
        "missing body file: workflows/whatnext.md" in p
        for p in res_parent.evidence["problems"]
    )


def test_artifact_manifest_explicit_injection_bypasses_filesystem(
    tmp_path: Path,
) -> None:
    """Arm (r6): explicit injection bypasses disk inspection even on empty tmp_path."""
    res_tt = rr.gate_artifact_manifest(True, True, repo_root=tmp_path)
    assert res_tt.passed is True
    assert res_tt.detail == "artifact manifest present and consistent"
    assert res_tt.evidence == {"present": True, "consistent": True}

    res_ft = rr.gate_artifact_manifest(False, True, repo_root=tmp_path)
    assert res_ft.passed is False
    assert res_ft.detail == "artifact manifest missing or inconsistent"
    assert res_ft.evidence == {"present": False, "consistent": True}

    res_tf = rr.gate_artifact_manifest(True, False, repo_root=tmp_path)
    assert res_tf.passed is False
    assert res_tf.detail == "artifact manifest missing or inconsistent"
    assert res_tf.evidence == {"present": True, "consistent": False}


def test_build_report_fails_on_artifact_manifest_missing_and_inconsistent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arm (r7): build_report flips to NO-GO on missing or inconsistent artifact manifest."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    _setup_full_go_tree(tmp_path)

    # Clean full GO tree -> VERDICT_GO
    rep = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=tmp_path,
        run_subprocess_gates=False,
    )
    assert rep.verdict == rr.VERDICT_GO
    assert rep.failing_gates() == []

    # Unlink body file -> flips to NO-GO with failing_gates() == ["artifact_manifest"]
    (tmp_path / ".aw" / "system" / "workflows" / "whatnext" / "whatnext.md").unlink()
    rep_missing_body = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=tmp_path,
        run_subprocess_gates=False,
    )
    assert rep_missing_body.verdict == rr.VERDICT_NO_GO
    assert rep_missing_body.failing_gates() == ["artifact_manifest"]

    # Unlink index.md -> VERDICT_NO_GO with "artifact_manifest" in failing_gates()
    (tmp_path / ".aw" / "system" / "workflows" / "index.md").unlink()
    rep_missing_index = rr.build_report(
        suite_passed=True,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        repo_root=tmp_path,
        run_subprocess_gates=False,
    )
    assert rep_missing_index.verdict == rr.VERDICT_NO_GO
    assert "artifact_manifest" in rep_missing_index.failing_gates()

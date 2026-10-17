"""Behavioral tests for managed-repository repo-local workflow rows in release readiness.

Verifies that in a managed repository (outside the toolkit source checkout),
manifest workflow commands absent from the toolkit catalog are dispositioned as
repo-local rather than failing workflow_disposition, while in the source checkout
unassigned commands still fail closed.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from agent_workflows import engine
from agent_workflows import migration_inventory
from agent_workflows import release_readiness as rr
from tests.test_release_readiness_producers import setup_minimal_workflows_tree
from tests.test_releases_readiness_cli import _build_subprocess_go_tree, _run_subprocess


def _add_custom_workflow_to_tree(
    wf_dir: Path, cmd: str = "mycustomwf", description: str = "Custom"
) -> None:
    """Add a custom workflow body file and manifest row to a workflows tree."""
    body_dir = wf_dir / cmd
    body_dir.mkdir(parents=True, exist_ok=True)
    (body_dir / f"{cmd}.md").write_text(f"# {description}\n", encoding="utf-8")
    index_md = wf_dir / "index.md"
    content = index_md.read_text(encoding="utf-8")
    custom_row = f"| {cmd} | .aw/system/workflows/{cmd}/{cmd}.md | {description} |\n"
    if "<!-- WORKFLOWS-MANIFEST:END -->" in content:
        new_content = content.replace(
            "<!-- WORKFLOWS-MANIFEST:END -->",
            f"{custom_row}<!-- WORKFLOWS-MANIFEST:END -->",
        )
    else:
        new_content = content + "\n" + custom_row
    index_md.write_text(new_content, encoding="utf-8")


def test_managed_repo_custom_command_is_repo_local_not_failing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A managed repo with a custom manifest command dispositions it as repo-local and passes."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    wf_dir = setup_minimal_workflows_tree(tmp_path)
    _add_custom_workflow_to_tree(wf_dir, "mycustomwf")
    assert not engine.is_source_checkout(tmp_path)

    res = rr.gate_workflow_disposition(repo_root=tmp_path)
    assert res.passed is True
    assert res.evidence["repo_local"] == ["mycustomwf"]
    assert res.evidence["undispositioned"] == []
    assert "mycustomwf" in res.detail


def test_source_checkout_custom_command_still_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """In the toolkit source checkout, an unassigned manifest command still fails closed."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    wf_dir = setup_minimal_workflows_tree(tmp_path)
    _add_custom_workflow_to_tree(wf_dir, "mycustomwf")

    # Turn tmp_path into a source checkout
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "agent-workflows"\n', encoding="utf-8"
    )
    (tmp_path / ".aw" / "system" / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    assert engine.is_source_checkout(tmp_path) is True

    res = rr.gate_workflow_disposition(repo_root=tmp_path)
    assert res.passed is False
    undone = res.evidence.get("undispositioned", [])
    assert len(undone) == 1
    assert "no reviewed family assignment" in undone[0]
    assert res.evidence.get("repo_local", []) == []


def test_managed_repo_without_custom_rows_reports_no_repo_local(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A managed repo with only standard workflows reports empty repo_local and plain detail."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    setup_minimal_workflows_tree(tmp_path)
    assert not engine.is_source_checkout(tmp_path)

    res = rr.gate_workflow_disposition(repo_root=tmp_path)
    assert res.passed is True
    assert res.evidence["repo_local"] == []
    assert res.detail == "all workflows dispositioned"


def test_repo_local_mode_keeps_other_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Repo-local mode exempts only unassigned commands, keeping other disposition findings."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    wf_dir = setup_minimal_workflows_tree(tmp_path)
    _add_custom_workflow_to_tree(wf_dir, "mycustomwf")
    (wf_dir / "conformance" / "operator-protocol.md").unlink()
    assert not engine.is_source_checkout(tmp_path)

    res = rr.gate_workflow_disposition(repo_root=tmp_path)
    assert res.passed is False
    undone = res.evidence.get("undispositioned", [])
    assert any("conformance entry file missing" in item for item in undone)
    assert res.evidence.get("repo_local") == ["mycustomwf"]


def test_build_inventory_default_still_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """build_inventory raises without keyword; allow_repo_local=True populates repo_local."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    wf_dir = setup_minimal_workflows_tree(tmp_path)
    _add_custom_workflow_to_tree(wf_dir, "mycustomwf")

    with pytest.raises(migration_inventory.InventoryError) as exc_info:
        migration_inventory.build_inventory(wf_dir)
    assert "mycustomwf" in str(exc_info.value)

    inv = migration_inventory.build_inventory(wf_dir, allow_repo_local=True)
    assert inv.repo_local == ["mycustomwf"]
    assert "mycustomwf" not in inv.dispositions
    assert inv.findings == []


def test_cli_managed_repo_custom_row_is_go(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """aw releases readiness CLI on a managed repo with custom workflow exits 0 with repo_local."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    tree = _build_subprocess_go_tree(tmp_path, monkeypatch)
    wf_dir = tree / ".aw" / "system" / "workflows"
    _add_custom_workflow_to_tree(wf_dir, "mycustomwf")
    assert not engine.is_source_checkout(tree)

    proc = _run_subprocess(
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
    payload = json.loads(proc.stdout)
    data = payload["data"]
    assert "workflow_disposition" not in data.get("failing_gates", [])
    wf_gate = next(g for g in data["gates"] if g["name"] == "workflow_disposition")
    assert wf_gate["evidence"]["repo_local"] == ["mycustomwf"]
    assert proc.returncode == 0

"""Tests asserting generated plans, specs, and backlog items name the writing standard (IPD yz4jdm)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support import coordinator_role, git, init_repo, run_cli

pytestmark = pytest.mark.core

POINTER_SNIPPET = ".aw/system/workflows/technical-writing/technical-writing.md"


def _assert_pointer_before_history(text: str, label: str) -> None:
    """Assert the writing standard pointer appears exactly once and before workflow history."""
    assert (
        text.count(POINTER_SNIPPET) == 1
    ), f"Expected exactly one pointer in {label}, found {text.count(POINTER_SNIPPET)}"
    assert (
        "## Workflow history" in text
    ), f"Missing '## Workflow history' heading in {label}"
    pre_hist, post_hist = text.split("## Workflow history", 1)
    assert (
        POINTER_SNIPPET in pre_hist
    ), f"Pointer not before '## Workflow history' in {label}"
    assert (
        POINTER_SNIPPET not in post_hist
    ), f"Pointer unexpectedly found after history in {label}"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Create a temporary git repository with standard records directories."""
    r = init_repo(tmp_path / "repo")
    (r / "README.md").write_text("initial\n", encoding="utf-8")
    git(r, "add", "README.md")
    git(r, "commit", "-m", "initial")
    (r / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    (r / ".aw" / "records" / "specs" / "draft").mkdir(parents=True)
    (r / ".aw" / "records" / "specs" / "to-review").mkdir(parents=True)
    (r / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)
    (r / ".aw" / "records" / "backlog" / "parked").mkdir(parents=True)
    return r


def test_ipd_scaffold_child_writing_standard_pointer(repo: Path) -> None:
    """Assert child plan scaffold emits the writing standard pointer and retains it through to-review."""
    res = run_cli(
        "ipd",
        "scaffold",
        "--dir",
        str(repo),
        "--kind",
        "child",
        "--title",
        "Test Child Plan",
        "--set",
        "testset",
        "--order",
        "1",
        "--author",
        "testauthor",
        "--priority",
        "high",
        "--work-kind",
        "feature",
        "--apply",
        cwd=repo,
    )
    assert res.returncode == 0, f"ipd scaffold child failed: {res.stdout}\n{res.stderr}"

    child_file = next(
        (repo / ".aw" / "records" / "plans" / "pending").glob("*-01-*.ipd.md")
    )
    _assert_pointer_before_history(
        child_file.read_text(encoding="utf-8"), "scaffolded child plan"
    )

    lint = run_cli("ipd", "lint", str(child_file), "--phase", "author", cwd=repo)
    assert lint.returncode == 0, f"ipd lint author failed: {lint.stdout}\n{lint.stderr}"

    with coordinator_role():
        trans = run_cli(
            "ipd",
            "set",
            "to-review",
            str(child_file),
            "--dir",
            str(repo),
            "--message",
            "advancing child to review",
            "--yes",
            cwd=repo,
        )
    assert (
        trans.returncode == 0
    ), f"ipd set to-review failed: {trans.stdout}\n{trans.stderr}"

    _assert_pointer_before_history(
        child_file.read_text(encoding="utf-8"), "post-transition child plan"
    )


def test_ipd_scaffold_orchestrator_writing_standard_pointer(repo: Path) -> None:
    """Assert orchestrator plan scaffold emits the writing standard pointer and lints conforming."""
    res = run_cli(
        "ipd",
        "scaffold",
        "--dir",
        str(repo),
        "--kind",
        "orchestrator",
        "--title",
        "Test Orchestrator Plan",
        "--set",
        "testset",
        "--order",
        "0",
        "--author",
        "testauthor",
        "--priority",
        "high",
        "--work-kind",
        "feature",
        "--apply",
        cwd=repo,
    )
    assert (
        res.returncode == 0
    ), f"ipd scaffold orchestrator failed: {res.stdout}\n{res.stderr}"

    orch_file = next(
        (repo / ".aw" / "records" / "plans" / "pending").glob("*-00-*.ipd.md")
    )
    _assert_pointer_before_history(
        orch_file.read_text(encoding="utf-8"), "scaffolded orchestrator plan"
    )

    lint = run_cli("ipd", "lint", str(orch_file), "--phase", "author", cwd=repo)
    assert lint.returncode == 0, f"ipd lint author failed: {lint.stdout}\n{lint.stderr}"


def test_specs_new_writing_standard_pointer(repo: Path) -> None:
    """Assert specs new emits the writing standard pointer and retains it through to-review."""
    res = run_cli(
        "specs",
        "new",
        "--dir",
        str(repo),
        "--title",
        "Test Spec",
        "--apply",
        cwd=repo,
    )
    assert res.returncode == 0, f"specs new failed: {res.stdout}\n{res.stderr}"

    spec_file = next((repo / ".aw" / "records" / "specs").rglob("*.spec.md"))
    _assert_pointer_before_history(spec_file.read_text(encoding="utf-8"), "new spec")

    chk = run_cli("specs", "check", "--dir", str(repo), cwd=repo)
    assert chk.returncode == 0, f"specs check failed: {chk.stdout}\n{chk.stderr}"

    with coordinator_role():
        trans = run_cli(
            "specs",
            "set",
            str(spec_file),
            "--status",
            "to-review",
            "--dir",
            str(repo),
            "--message",
            "advancing spec to review",
            cwd=repo,
        )
    assert (
        trans.returncode == 0
    ), f"specs set to-review failed: {trans.stdout}\n{trans.stderr}"

    spec_after = next((repo / ".aw" / "records" / "specs").rglob("*.spec.md"))
    _assert_pointer_before_history(
        spec_after.read_text(encoding="utf-8"), "post-transition spec"
    )


def test_backlog_new_writing_standard_pointer(repo: Path) -> None:
    """Assert backlog new emits the writing standard pointer and retains it through parked."""
    res = run_cli(
        "backlog",
        "new",
        "--dir",
        str(repo),
        "--summary",
        "test backlog item",
        "--set",
        "testset",
        "--work-kind",
        "feature",
        "--priority",
        "high",
        "--apply",
        cwd=repo,
    )
    assert res.returncode == 0, f"backlog new failed: {res.stdout}\n{res.stderr}"

    backlog_file = next((repo / ".aw" / "records" / "backlog").rglob("*.backlog.md"))
    _assert_pointer_before_history(
        backlog_file.read_text(encoding="utf-8"), "new backlog item"
    )

    chk = run_cli("backlog", "check", "--dir", str(repo), cwd=repo)
    assert chk.returncode == 0, f"backlog check failed: {chk.stdout}\n{chk.stderr}"

    with coordinator_role():
        trans = run_cli(
            "backlog",
            "set",
            str(backlog_file),
            "--status",
            "parked",
            "--dir",
            str(repo),
            "--message",
            "parking backlog item",
            cwd=repo,
        )
    assert (
        trans.returncode == 0
    ), f"backlog set parked failed: {trans.stdout}\n{trans.stderr}"

    backlog_after = next((repo / ".aw" / "records" / "backlog").rglob("*.backlog.md"))
    _assert_pointer_before_history(
        backlog_after.read_text(encoding="utf-8"), "post-transition backlog item"
    )

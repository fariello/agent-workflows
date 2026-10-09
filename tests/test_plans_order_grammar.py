"""Outcome tests for plan Order grammar enforcement (IPD yqv6b7).

Validates that aw group plans and aw rename plans unconditionally refuse any resolved
Order outside 0 to 99 inclusive (the two-digit NN facet), before writing anything,
on every plan whether or not it declares a Kind; that --allow-invalid-order cannot
bypass the grammar check; and that metadata rewrites fail safe instead of creating
duplicate - Order: lines.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from agent_workflows.plans_refs import (
    _set_metadata,
    run_set_assign,
)
from tests.test_ipd_lint import _conforming_child


def _repo_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path.cwd())
    env["AW_NO_REEXEC"] = "1"
    return env


@pytest.fixture
def order_repo(tmp_path: Path) -> Path:
    """A fresh git repo seeded with records-backend repository."""
    repo = tmp_path.resolve()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps({"records_backend": "repository"}), encoding="utf-8"
    )

    plans_pending = repo / ".aw" / "records" / "plans" / "pending"
    plans_pending.mkdir(parents=True, exist_ok=True)
    return repo


def _seed_conforming_plan(
    repo: Path,
    id6: str,
    *,
    setid: str = "testset",
    order: int = 1,
    kind: str | None = "child",
) -> Path:
    """Seed a conforming plan in pending/."""
    pdir = repo / ".aw" / "records" / "plans" / "pending"
    plan_path = pdir / f"20261002-{setid}-{order:02d}-{id6}-test-plan.ipd.md"
    text = (
        _conforming_child()
        .replace("- Set: x", f"- Set: {setid}")
        .replace("- Order: 1", f"- Order: {order}")
        .replace("- Id: abc123", f"- Id: {id6}")
    )
    if kind is None:
        text = text.replace("- Kind: child\n", "")
    elif kind != "child":
        text = text.replace("- Kind: child", f"- Kind: {kind}")
    plan_path.write_text(text, encoding="utf-8")
    return plan_path


def _run_cli(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = ["python3", "-m", "agent_workflows", *args, "--dir", str(repo)]
    return subprocess.run(
        cmd, cwd=repo, capture_output=True, text=True, env=_repo_env(), check=False
    )


def _run_ipd_lint(repo: Path, plan_path: Path) -> subprocess.CompletedProcess[str]:
    cmd = ["python3", "-m", "agent_workflows", "ipd", "lint", str(plan_path)]
    return subprocess.run(
        cmd, cwd=repo, capture_output=True, text=True, env=_repo_env(), check=False
    )


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ------------------------------------------------------------------------------
# E-01 & E-02: Negative Order on Kind-less and Kind: child plans, both verbs
# ------------------------------------------------------------------------------


def test_negative_order_refused_group_plans_kindless(order_repo: Path) -> None:
    """E-01: aw group plans refuses a negative order on a Kind-less plan with exit 2, unchanged bytes."""
    p = _seed_conforming_plan(order_repo, "knd001", kind=None, order=1)
    before_hash = _file_hash(p)

    proc = _run_cli(
        order_repo,
        ["group", "plans", "knd001", "--set", "newset", "--order", "-1", "--apply"],
    )
    assert proc.returncode == 2
    assert "Order '-1' is out of grammar" in proc.stdout
    assert "0 to 99" in proc.stdout
    assert "--1" not in p.name
    assert _file_hash(p) == before_hash

    lint = _run_ipd_lint(order_repo, p)
    assert "IPD-M102" not in lint.stdout


def test_negative_order_refused_group_plans_child(order_repo: Path) -> None:
    """E-01: aw group plans refuses a negative order on a Kind: child plan with exit 2, unchanged bytes."""
    p = _seed_conforming_plan(order_repo, "chd001", kind="child", order=1)
    before_hash = _file_hash(p)

    proc = _run_cli(
        order_repo,
        ["group", "plans", "chd001", "--set", "newset", "--order", "-1", "--apply"],
    )
    assert proc.returncode == 2
    assert "Order '-1' is out of grammar" in proc.stdout
    assert "0 to 99" in proc.stdout
    assert "--1" not in p.name
    assert _file_hash(p) == before_hash

    lint = _run_ipd_lint(order_repo, p)
    assert "IPD-M102" not in lint.stdout


def test_negative_order_refused_rename_plans_kindless(order_repo: Path) -> None:
    """E-02: aw rename plans refuses a negative order on a Kind-less plan with exit 2, unchanged bytes."""
    p = _seed_conforming_plan(order_repo, "knd002", kind=None, order=1)
    before_hash = _file_hash(p)

    proc = _run_cli(
        order_repo,
        ["rename", "plans", "knd002", "--order", "-1", "--apply"],
    )
    assert proc.returncode == 2
    assert "Order '-1' is out of grammar" in proc.stdout
    assert "0 to 99" in proc.stdout
    assert "--1" not in p.name
    assert _file_hash(p) == before_hash

    lint = _run_ipd_lint(order_repo, p)
    assert "IPD-M102" not in lint.stdout


def test_negative_order_refused_rename_plans_child(order_repo: Path) -> None:
    """E-02: aw rename plans refuses a negative order on a Kind: child plan with exit 2, unchanged bytes."""
    p = _seed_conforming_plan(order_repo, "chd002", kind="child", order=1)
    before_hash = _file_hash(p)

    proc = _run_cli(
        order_repo,
        ["rename", "plans", "chd002", "--order", "-1", "--apply"],
    )
    assert proc.returncode == 2
    assert "Order '-1' is out of grammar" in proc.stdout
    assert "0 to 99" in proc.stdout
    assert "--1" not in p.name
    assert _file_hash(p) == before_hash

    lint = _run_ipd_lint(order_repo, p)
    assert "IPD-M102" not in lint.stdout


def test_preview_without_apply_refuses_negative_order(order_repo: Path) -> None:
    """E-01 & E-02: Commands without --apply (dry-run) also exit 2 when resolved order is out of grammar."""
    p = _seed_conforming_plan(order_repo, "prv001", kind="child", order=1)
    before_hash = _file_hash(p)

    # group plans preview
    proc_group = _run_cli(
        order_repo,
        ["group", "plans", "prv001", "--set", "newset", "--order", "-1"],
    )
    assert proc_group.returncode == 2
    assert "Order '-1' is out of grammar" in proc_group.stdout
    assert _file_hash(p) == before_hash

    # rename plans preview
    proc_rename = _run_cli(
        order_repo,
        ["rename", "plans", "prv001", "--order", "-1"],
    )
    assert proc_rename.returncode == 2
    assert "Order '-1' is out of grammar" in proc_rename.stdout
    assert _file_hash(p) == before_hash


def test_allow_invalid_order_does_not_bypass_range_check(order_repo: Path) -> None:
    """E-01 & E-02: --allow-invalid-order does not override the 0 to 99 grammar range check on either verb."""
    p1 = _seed_conforming_plan(order_repo, "ovr001", kind="child", order=1)
    before_hash1 = _file_hash(p1)
    proc_group = _run_cli(
        order_repo,
        [
            "group",
            "plans",
            "ovr001",
            "--set",
            "newset",
            "--order",
            "-1",
            "--allow-invalid-order",
            "--apply",
        ],
    )
    assert proc_group.returncode == 2
    assert "Order '-1' is out of grammar" in proc_group.stdout
    assert _file_hash(p1) == before_hash1

    p2 = _seed_conforming_plan(order_repo, "ovr002", kind="child", order=1)
    before_hash2 = _file_hash(p2)
    proc_rename = _run_cli(
        order_repo,
        [
            "rename",
            "plans",
            "ovr002",
            "--order",
            "-1",
            "--allow-invalid-order",
            "--apply",
        ],
    )
    assert proc_rename.returncode == 2
    assert "Order '-1' is out of grammar" in proc_rename.stdout
    assert _file_hash(p2) == before_hash2


# ------------------------------------------------------------------------------
# E-01: Boundary tests (98, 99, 100)
# ------------------------------------------------------------------------------


def test_order_99_allowed_and_100_refused_rename(order_repo: Path) -> None:
    """E-01 & E-02: Order 99 is accepted, while Order 100 is refused with exit 2."""
    p = _seed_conforming_plan(order_repo, "bnd001", kind="child", order=1)

    # 100 is refused, file unchanged
    before_hash = _file_hash(p)
    proc_100 = _run_cli(
        order_repo,
        ["rename", "plans", "bnd001", "--order", "100", "--apply"],
    )
    assert proc_100.returncode == 2
    assert "Order '100' is out of grammar" in proc_100.stdout
    assert _file_hash(p) == before_hash

    # 99 is accepted
    proc_99 = _run_cli(
        order_repo,
        ["rename", "plans", "bnd001", "--order", "99", "--apply"],
    )
    assert proc_99.returncode == 0
    p_99 = (
        order_repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261002-testset-99-bnd001-test-plan.ipd.md"
    )
    assert p_99.exists()
    assert "- Order: 99" in p_99.read_text(encoding="utf-8")


def test_order_multi_plan_boundary_batch(order_repo: Path) -> None:
    """E-01: In a two-plan batch with --order 99, the second plan resolves 100 and refuses before any write."""
    p1 = _seed_conforming_plan(order_repo, "btc001", order=1)
    p2 = _seed_conforming_plan(order_repo, "btc002", order=2)
    h1_before = _file_hash(p1)
    h2_before = _file_hash(p2)

    # --order 99: resolves 99 for btc001, then 100 for btc002 -> refuses entire batch
    proc = _run_cli(
        order_repo,
        [
            "group",
            "plans",
            "btc001",
            "btc002",
            "--set",
            "newset",
            "--order",
            "99",
            "--apply",
        ],
    )
    assert proc.returncode == 2
    assert "btc002" in proc.stdout
    assert "Order '100' is out of grammar" in proc.stdout
    # Nothing was written for either plan
    assert p1.exists()
    assert p2.exists()
    assert _file_hash(p1) == h1_before
    assert _file_hash(p2) == h2_before

    # --order 98: resolves 98 (btc001) and 99 (btc002) -> succeeds
    proc_ok = _run_cli(
        order_repo,
        [
            "group",
            "plans",
            "btc001",
            "btc002",
            "--set",
            "newset",
            "--order",
            "98",
            "--rename",
            "--apply",
        ],
    )
    assert proc_ok.returncode == 0
    p1_new = (
        order_repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261002-newset-98-btc001-test-plan.ipd.md"
    )
    p2_new = (
        order_repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261002-newset-99-btc002-test-plan.ipd.md"
    )
    assert p1_new.exists()
    assert p2_new.exists()
    assert "- Order: 98" in p1_new.read_text(encoding="utf-8")
    assert "- Order: 99" in p2_new.read_text(encoding="utf-8")


# ------------------------------------------------------------------------------
# E-04: bmhoxe repair sequence
# ------------------------------------------------------------------------------


def test_bmhoxe_repair_sequence_leaves_well_formed_name(order_repo: Path) -> None:
    """E-04: A refused --order -1 followed by --order 0 (or valid order) leaves a well-formed name with single Order line."""
    p = _seed_conforming_plan(order_repo, "rep001", kind=None, order=1)

    # 1. Attempt invalid -1 -> refused
    proc_fail = _run_cli(
        order_repo,
        ["rename", "plans", "rep001", "--order", "-1", "--apply"],
    )
    assert proc_fail.returncode == 2
    assert p.exists()

    # 2. Repair with --order 0
    proc_repair = _run_cli(
        order_repo,
        ["rename", "plans", "rep001", "--order", "0", "--apply"],
    )
    assert proc_repair.returncode == 0
    repaired = (
        order_repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261002-testset-00-rep001-test-plan.ipd.md"
    )
    assert repaired.exists()
    text = repaired.read_text(encoding="utf-8")
    order_lines = [line for line in text.splitlines() if line.startswith("- Order:")]
    assert order_lines == ["- Order: 0"]

    # Verify no duplicate field lint error
    lint = _run_ipd_lint(order_repo, repaired)
    assert "IPD-M102" not in lint.stdout


# ------------------------------------------------------------------------------
# E-03: Metadata fail-safe and atomic batch protection
# ------------------------------------------------------------------------------


def test_set_metadata_substitutes_negative_order_in_place() -> None:
    """E-03: _set_metadata on text with '- Order: -1' substitutes in place rather than inserting a duplicate."""
    raw = (
        "# IPD: Test\n\n"
        "- Id: sst001\n"
        "- Set: oldset\n"
        "- Order: -1\n\n"
        "## Goal\n"
    )
    updated = _set_metadata(raw, set_id="newset", order=5, plan_name="sst001")
    order_lines = [line for line in updated.splitlines() if line.startswith("- Order:")]
    assert order_lines == ["- Order: 5"]
    assert "- Set: newset" in updated


def test_set_metadata_raises_on_unmatchable_order_line() -> None:
    """E-03: _set_metadata raises ValueError when an unmatchable Order line would cause duplicate insertion."""
    raw = (
        "# IPD: Test\n\n"
        "- Id: sst002\n"
        "- Set: oldset\n"
        "- Order: x1\n\n"
        "## Goal\n"
    )
    with pytest.raises(ValueError, match="expected exactly one '- Order:' line"):
        _set_metadata(raw, set_id="newset", order=5, plan_name="sst002")


def test_forced_raise_in_apply_renames_leaves_batch_unmoved_and_unchanged(
    order_repo: Path,
) -> None:
    """E-03: A ValueError in apply_renames pre-pass leaves every plan in the batch byte-identical and unmoved."""
    p1 = _seed_conforming_plan(order_repo, "atc001", order=1)
    p2 = _seed_conforming_plan(order_repo, "atc002", order=2)

    # Corrupt p2 with an unmatchable Order line that will trigger the assertion in _set_metadata
    p2_text = p2.read_text(encoding="utf-8").replace("- Order: 2", "- Order: x2")
    p2.write_text(p2_text, encoding="utf-8")

    h1_before = _file_hash(p1)
    h2_before = _file_hash(p2)

    args = argparse.Namespace(
        dir=str(order_repo),
        ids=["atc001", "atc002"],
        set="newset",
        order=1,
        rename=True,
        apply=True,
        allow_invalid_order=True,
        force=False,
        no_refs=False,
        yes=True,
    )
    res = run_set_assign(args)
    assert res.rc == 2
    assert p1.exists()
    assert p2.exists()
    assert _file_hash(p1) == h1_before
    assert _file_hash(p2) == h2_before

"""Outcome tests restoring the Order-preservation regression guard for aw group plans and aw rename plans.

Guards that a bare `aw group plans <id6> --set X [--rename]` and a bare `aw rename plans <id6> --slug X`
preserve each plan's existing Order rather than renumbering it from zero, while an explicit `--order`
still renumbers sequentially. Originally authored in tests/test_awnaming_grammar_and_producers.py
and restored under IPD fv6kep.
"""

from __future__ import annotations

import io
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from agent_workflows import cli
from agent_workflows import plans_refs as refs


def _seed_plan_record(
    repo_dir: Path,
    filename: str,
    id6: str,
    *,
    set_line: str = "probeset (probe)",
    order: int | None = 1,
    date_line: str = "20260908",
    disposition: str = "pending",
    kind: str | None = None,
    item_dependencies: str | None = None,
) -> Path:
    """Seed a plan record under .aw/records/plans/<disposition>/."""
    pdir = repo_dir / ".aw" / "records" / "plans" / disposition
    pdir.mkdir(parents=True, exist_ok=True)
    path = pdir / filename
    lines = [
        f"# IPD: Test plan {id6}",
        "",
        f"- Id: {id6}",
    ]
    if kind is not None:
        lines.append(f"- Kind: {kind}")
    lines.append(f"- Set: {set_line}")
    if order is not None:
        lines.append(f"- Order: {order}")
    if item_dependencies is not None:
        lines.append(f"- Item-Dependencies: {item_dependencies}")
    if date_line is not None:
        lines.append(f"- Date: {date_line}")
    lines.extend(["", "## Goal", "", "Test goal.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


@pytest.fixture
def seeded_plans_repo(tmp_path: Path) -> Path:
    """Minimal fixture: initialize a git repo in tmp_path and seed four plans.

    Seeds:
    - aaa000: orchestrator at Order 0
    - bbb222: child at Order 1
    - ccc333: child at Order 2
    - ddd444: child with NO '- Order:' line, filename carrying '04' slot
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    _seed_plan_record(
        tmp_path,
        "20260908-probeset-00-aaa000-probe-orchestrator.ipd.md",
        "aaa000",
        kind="orchestrator",
        order=0,
        set_line="probeset (probe)",
    )
    _seed_plan_record(
        tmp_path,
        "20260908-probeset-01-bbb222-probe-child-one.ipd.md",
        "bbb222",
        kind="child",
        order=1,
        set_line="probeset (probe)",
    )
    _seed_plan_record(
        tmp_path,
        "20260908-probeset-02-ccc333-probe-child-two.ipd.md",
        "ccc333",
        kind="child",
        order=2,
        set_line="probeset (probe)",
    )
    _seed_plan_record(
        tmp_path,
        "20260908-probeset-04-ddd444-probe-no-order-line.ipd.md",
        "ddd444",
        kind="child",
        order=None,
        set_line="probeset (probe)",
    )
    return tmp_path


def _only(repo_dir: Path, id6: str) -> Path:
    """Find the single plan file matching id6 under pending/."""
    matches = list(
        (repo_dir / ".aw" / "records" / "plans" / "pending").glob(f"*{id6}*.md")
    )
    assert len(matches) == 1, f"Expected exactly one plan for {id6}, found: {matches}"
    return matches[0]


def _run_group_plans(
    selectors: list[str],
    setid: str,
    repo_dir: Path,
    *,
    order: int | None = None,
    rename: bool = False,
    apply: bool = False,
    allow_invalid_order: bool = False,
) -> tuple[int, str, str]:
    """Run `aw group plans <selectors...> --set <setid> [...] --dir <repo_dir>` in-process."""
    cmd = ["group", "plans", *selectors, "--set", setid]
    if order is not None:
        cmd.extend(["--order", str(order)])
    if rename:
        cmd.append("--rename")
    if apply:
        cmd.append("--apply")
    if allow_invalid_order:
        cmd.append("--allow-invalid-order")
    cmd.extend(["--dir", str(repo_dir)])
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(cmd)
    return rc, buf_out.getvalue(), buf_err.getvalue()


def _run_rename_plans(
    id6: str,
    repo_dir: Path,
    *,
    setid: str | None = None,
    order: int | None = None,
    slug: str | None = None,
    apply: bool = False,
    allow_invalid_order: bool = False,
) -> tuple[int, str, str]:
    """Run `aw rename plans <id6> [...] --dir <repo_dir>` in-process."""
    cmd = ["rename", "plans", id6]
    if setid is not None:
        cmd.extend(["--set", setid])
    if order is not None:
        cmd.extend(["--order", str(order)])
    if slug is not None:
        cmd.extend(["--slug", slug])
    if apply:
        cmd.append("--apply")
    if allow_invalid_order:
        cmd.append("--allow-invalid-order")
    cmd.extend(["--dir", str(repo_dir)])
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(cmd)
    return rc, buf_out.getvalue(), buf_err.getvalue()


def _run_ipd_lint(path: Path) -> tuple[int, str, str]:
    """Run `aw ipd lint <path>` in-process with captured output."""
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(["ipd", "lint", str(path)])
    return rc, buf_out.getvalue(), buf_err.getvalue()


# --- E-03: group verb Order cases ---


def test_bare_rename_regroup_preserves_a_child_order(seeded_plans_repo: Path) -> None:
    """E-03(a): a bare `--rename` regroup of bbb222 preserves `- Order: 1` AND the filename `01` slot."""
    rc, out, err = _run_group_plans(
        ["bbb222"], "newset", seeded_plans_repo, rename=True, apply=True
    )
    assert rc == 0, f"stdout: {out}, stderr: {err}"
    moved = _only(seeded_plans_repo, "bbb222")
    text = moved.read_text(encoding="utf-8")
    assert "- Order: 1" in text
    m = refs._CLUSTERED_RE.match(moved.name)
    assert m is not None, moved.name
    assert m.group("nn") == "01", moved.name
    assert m.group("set") == "newset", moved.name


def test_bare_metadata_only_regroup_preserves_a_child_order(
    seeded_plans_repo: Path,
) -> None:
    """E-03(b): a bare metadata-only regroup of bbb222 preserves `- Order: 1` and leaves the filename untouched."""
    rc, out, err = _run_group_plans(
        ["bbb222"], "metaset", seeded_plans_repo, rename=False, apply=True
    )
    assert rc == 0, f"stdout: {out}, stderr: {err}"
    kept = _only(seeded_plans_repo, "bbb222")
    assert kept.name == "20260908-probeset-01-bbb222-probe-child-one.ipd.md"
    text = kept.read_text(encoding="utf-8")
    assert "- Set: metaset" in text
    assert "- Order: 1" in text
    m = refs._CLUSTERED_RE.match(kept.name)
    assert m is not None, kept.name
    order_line = refs._ORDER_LINE_RE.search(text)
    assert order_line is not None, text
    assert int(order_line.group(1)) == int(
        m.group("nn")
    ), f"filename NN {m.group('nn')} disagrees with front matter {order_line.group(1)}"


def test_explicit_order_still_renumbers_sequentially(seeded_plans_repo: Path) -> None:
    """E-03(c): an explicit `--order 1` over bbb222 ccc333 --rename still renumbers sequentially to 1 and 2."""
    rc, out, err = _run_group_plans(
        ["bbb222", "ccc333"],
        "asmset",
        seeded_plans_repo,
        order=1,
        rename=True,
        apply=True,
    )
    assert rc == 0, f"stdout: {out}, stderr: {err}"
    first = _only(seeded_plans_repo, "bbb222")
    second = _only(seeded_plans_repo, "ccc333")
    assert first.name.startswith("20260908-asmset-01-bbb222-"), first.name
    assert "- Order: 1" in first.read_text(encoding="utf-8")
    assert second.name.startswith("20260908-asmset-02-ccc333-"), second.name
    assert "- Order: 2" in second.read_text(encoding="utf-8")


def test_bare_regroup_falls_back_to_the_filename_slot(seeded_plans_repo: Path) -> None:
    """E-03(d): a bare `--rename` regroup of ddd444 (no `- Order:` line) falls back to filename slot and writes `- Order: 4`."""
    seeded = _only(seeded_plans_repo, "ddd444")
    assert "- Order:" not in seeded.read_text(encoding="utf-8")
    rc, out, err = _run_group_plans(
        ["ddd444"], "fbset", seeded_plans_repo, rename=True, apply=True
    )
    assert rc == 0, f"stdout: {out}, stderr: {err}"
    moved = _only(seeded_plans_repo, "ddd444")
    assert moved.name.startswith("20260908-fbset-04-ddd444-"), moved.name
    assert "- Order: 4" in moved.read_text(encoding="utf-8")


def test_bare_regroup_keeps_an_orchestrator_at_zero(seeded_plans_repo: Path) -> None:
    """E-03(e): a bare `--rename` regroup of the orchestrator aaa000 keeps it at `- Order: 0`."""
    rc, out, err = _run_group_plans(
        ["aaa000"], "orchset", seeded_plans_repo, rename=True, apply=True
    )
    assert rc == 0, f"stdout: {out}, stderr: {err}"
    moved = _only(seeded_plans_repo, "aaa000")
    assert moved.name.startswith("20260908-orchset-00-aaa000-"), moved.name
    assert "- Order: 0" in moved.read_text(encoding="utf-8")


def test_explicit_order_zero_is_still_reachable(seeded_plans_repo: Path) -> None:
    """E-03(f): an explicit `--order 0` over ccc333 --rename still lands at 0."""
    rc, out, err = _run_group_plans(
        ["ccc333"],
        "zeroset",
        seeded_plans_repo,
        order=0,
        rename=True,
        apply=True,
        allow_invalid_order=True,
    )
    assert rc == 0, f"stdout: {out}, stderr: {err}"
    moved = _only(seeded_plans_repo, "ccc333")
    assert moved.name.startswith("20260908-zeroset-00-ccc333-"), moved.name
    assert "- Order: 0" in moved.read_text(encoding="utf-8")


# --- E-04: rename verb case ---


def test_mv_preserves_order_date_and_adds_facet(seeded_plans_repo: Path) -> None:
    """E-04: bare rename plans zzz111 --slug new-slug --apply preserves Order 3, Date 20260810, and emits .ipd.md."""
    _seed_plan_record(
        seeded_plans_repo,
        "20260810-demo-03-zzz111-old-slug.md",
        "zzz111",
        kind="child",
        order=3,
        date_line="20260810",
        set_line="demo (demo)",
    )
    rc, out, err = _run_rename_plans(
        "zzz111", seeded_plans_repo, slug="new-slug", apply=True
    )
    assert rc == 0, f"stdout: {out}, stderr: {err}"
    renamed = _only(seeded_plans_repo, "zzz111")
    name = renamed.name
    assert name.startswith("20260810-demo-03-zzz111-"), name
    assert name.endswith(".ipd.md"), name
    text = renamed.read_text(encoding="utf-8")
    assert "- Order: 3" in text
    assert "- Date: 20260810" in text


# --- E-05: end-to-end lint case ---


def test_lint_no_longer_reports_ipd_m104_after_a_bare_regroup(
    seeded_plans_repo: Path,
) -> None:
    """E-05: aw ipd lint does not report IPD-M104: Order: after bare regroup, and unrelated IPD-H202 is present."""
    target = _only(seeded_plans_repo, "bbb222")
    _, out_before, err_before = _run_ipd_lint(target)
    combined_before = out_before + err_before
    assert "IPD-M104: Order:" not in combined_before

    rc, out_group, err_group = _run_group_plans(
        ["bbb222"], "lintset", seeded_plans_repo, rename=True, apply=True
    )
    assert rc == 0, f"stdout: {out_group}, stderr: {err_group}"

    moved = _only(seeded_plans_repo, "bbb222")
    _, out_after, err_after = _run_ipd_lint(moved)
    combined_after = out_after + err_after
    assert "IPD-M104: Order:" not in combined_after, combined_after
    assert "IPD-H202" in combined_after, combined_after

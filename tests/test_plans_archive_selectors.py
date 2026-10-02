"""Outcome tests for plans archive selectors (Set awrenamesel, Order 03, IPD 1x4tdo).

Asserts observable outcomes (exit codes and file moves) for:
- Filename and path targets archiving terminal plans
- Unmatched explicit target refusing (nonzero exit)
- Terse setid with and without descriptive parenthetical
- Three distinct refusal reasons (ambiguous substring, unmatched, not terminal)
- --force honored for ambiguous selectors
- Must-not-break guards: id6, bare setid, bare sweep with --age, already-sharded plan, foreign-type path
"""

from __future__ import annotations

import io
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path
from typing import Optional


from agent_workflows import cli


def _init_repo(root: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=root, check=True)
    cfg_dir = root / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        '{"records_backend": "repository"}\n', encoding="utf-8"
    )
    return root


def _make_plan(
    repo: Path,
    disposition: str,
    filename: str,
    *,
    plan_id: str,
    date_: str = "20260701",
    set_val: Optional[str] = None,
    order: Optional[str] = None,
    shard: Optional[str] = None,
) -> Path:
    if shard:
        pdir = repo / ".aw" / "records" / "plans" / disposition / shard
    else:
        pdir = repo / ".aw" / "records" / "plans" / disposition
    pdir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# IPD: Test plan {plan_id}",
        "",
        f"- Date: {date_}",
        "- Kind: child",
        "- Concern: Test concern.",
        "- Scope: Test scope.",
        f"- Status: {disposition}",
        "- Author: test",
        f"- Id: {plan_id}",
    ]
    if set_val:
        lines.append(f"- Set: {set_val}")
    if order:
        lines.append(f"- Order: {order}")
    lines.extend(["", "## Goal", "", "Test goal.", ""])
    target = pdir / filename
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def _run_archive(*args: str) -> tuple[int, str, str]:
    """Run `aw archive` in-process with captured stdout and stderr."""
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        try:
            rc = cli.main(["--no-interactive", "archive", *args])
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 1
    return rc, buf_out.getvalue(), buf_err.getvalue()


# ---------------------------------------------------------------------------
# E-01: Pin both silent failures (filename, path, unmatched target)
# ---------------------------------------------------------------------------


def test_e01_archive_by_filename(tmp_path: Path):
    """Filename selector archives the plan with --apply and previews without it."""
    repo = _init_repo(tmp_path)
    plan_path = _make_plan(
        repo,
        "executed",
        "20260701-demo-01-fn0001-filename-test.ipd.md",
        plan_id="fn0001",
    )
    # Preview
    rc, out, _ = _run_archive("plans", plan_path.name, "--dir", str(repo))
    assert rc == 0
    assert "would archive 20260701-demo-01-fn0001-filename-test.ipd.md" in out

    # Apply
    rc, out, _ = _run_archive("plans", plan_path.name, "--apply", "--dir", str(repo))
    assert rc == 0
    assert not plan_path.exists()
    sharded = (
        repo / ".aw" / "records" / "plans" / "executed" / "202607" / plan_path.name
    )
    assert sharded.exists()


def test_e01_archive_by_repo_relative_path(tmp_path: Path):
    """Repo-relative path selector archives the plan with --apply."""
    repo = _init_repo(tmp_path)
    plan_path = _make_plan(
        repo,
        "executed",
        "20260701-demo-02-rp0002-relpath-test.ipd.md",
        plan_id="rp0002",
    )
    rel_path = plan_path.relative_to(repo).as_posix()
    # Preview
    rc, out, _ = _run_archive("plans", rel_path, "--dir", str(repo))
    assert rc == 0
    assert "would archive 20260701-demo-02-rp0002-relpath-test.ipd.md" in out

    # Apply
    rc, out, _ = _run_archive("plans", rel_path, "--apply", "--dir", str(repo))
    assert rc == 0
    assert not plan_path.exists()
    sharded = (
        repo / ".aw" / "records" / "plans" / "executed" / "202607" / plan_path.name
    )
    assert sharded.exists()


def test_e01_unmatched_explicit_target_refuses(tmp_path: Path):
    """An explicit target matching nothing must exit NONZERO."""
    repo = _init_repo(tmp_path)
    rc, out, _ = _run_archive("plans", "nonexistent-token-xyz", "--dir", str(repo))
    assert (
        rc != 0
    ), f"Expected nonzero exit on unmatched target, got rc={rc}, output={out}"


# ---------------------------------------------------------------------------
# E-02: Pin the terse-setid failure (parenthetical vs bare)
# ---------------------------------------------------------------------------


def test_e02_terse_setid_with_descriptive_parenthetical(tmp_path: Path):
    """aw archive plans <terse-setid> must target plans whose - Set: has a parenthetical."""
    repo = _init_repo(tmp_path)
    p1 = _make_plan(
        repo,
        "executed",
        "20260701-demoset-01-st0001-first.ipd.md",
        plan_id="st0001",
        set_val="demoset (a descriptive label)",
        order="01",
    )
    p2 = _make_plan(
        repo,
        "executed",
        "20260701-demoset-02-st0002-second.ipd.md",
        plan_id="st0002",
        set_val="demoset (a descriptive label)",
        order="02",
    )
    rc, out, _ = _run_archive("plans", "demoset", "--apply", "--dir", str(repo))
    assert rc == 0
    assert not p1.exists()
    assert not p2.exists()
    assert (
        repo / ".aw" / "records" / "plans" / "executed" / "202607" / p1.name
    ).exists()
    assert (
        repo / ".aw" / "records" / "plans" / "executed" / "202607" / p2.name
    ).exists()


def test_e02_bare_terse_setid_control(tmp_path: Path):
    """aw archive plans <bare-setid> must keep matching bare - Set: entries."""
    repo = _init_repo(tmp_path)
    p1 = _make_plan(
        repo,
        "executed",
        "20260701-bareset-01-bs0001-first.ipd.md",
        plan_id="bs0001",
        set_val="bareset",
        order="01",
    )
    rc, out, _ = _run_archive("plans", "bareset", "--apply", "--dir", str(repo))
    assert rc == 0
    assert not p1.exists()
    assert (
        repo / ".aw" / "records" / "plans" / "executed" / "202607" / p1.name
    ).exists()


# ---------------------------------------------------------------------------
# E-04 / V-04: Distinguish all three refusal reasons and honor --force
# ---------------------------------------------------------------------------


def test_e04_refusal_unmatched_target(tmp_path: Path):
    """Case 1 of E-04: target matched no plan at all -> nonzero exit."""
    repo = _init_repo(tmp_path)
    rc, out, _ = _run_archive("plans", "typo-selector-12345", "--dir", str(repo))
    assert rc != 0
    assert "typo-selector-12345" in out


def test_e04_refusal_pending_plan_named(tmp_path: Path):
    """Case 2 of E-04: target matched a real plan that is not terminal -> nonzero saying not terminal."""
    repo = _init_repo(tmp_path)
    plan_path = _make_plan(
        repo, "pending", "20260701-pend-01-pnd001-pending-plan.ipd.md", plan_id="pnd001"
    )
    rc, out, _ = _run_archive("plans", "pnd001", "--dir", str(repo))
    assert rc != 0
    assert "is not terminal" in out
    assert "pnd001" in out or plan_path.name in out
    assert "pending" in out


def test_e04_refusal_ambiguous_substring_verbatim_and_force(tmp_path: Path):
    """Case 3 of E-04: ambiguous substring surfaces resolver err verbatim; --force acts on all."""
    repo = _init_repo(tmp_path)
    p1 = _make_plan(
        repo,
        "executed",
        "20260701-mig-01-mg0001-migrate-part-one.ipd.md",
        plan_id="mg0001",
    )
    p2 = _make_plan(
        repo,
        "executed",
        "20260701-mig-02-mg0002-migrate-part-two.ipd.md",
        plan_id="mg0002",
    )

    # Without --force: fails with resolver's own refusal message
    rc, out, _ = _run_archive("plans", "migrate", "--dir", str(repo))
    assert rc != 0
    assert (
        "is ambiguous (substring) matching multiple files; pass --force to act on all"
        in out
    )

    # With --force: succeeds and archives both
    rc, out, _ = _run_archive(
        "plans", "migrate", "--force", "--apply", "--dir", str(repo)
    )
    assert rc == 0
    assert not p1.exists()
    assert not p2.exists()
    assert (
        repo / ".aw" / "records" / "plans" / "executed" / "202607" / p1.name
    ).exists()
    assert (
        repo / ".aw" / "records" / "plans" / "executed" / "202607" / p2.name
    ).exists()


def test_e04_bare_sweep_empty_still_exits_zero(tmp_path: Path):
    """Bare sweep with nothing due legitimately exits 0."""
    repo = _init_repo(tmp_path)
    rc, out, _ = _run_archive("plans", "--dir", str(repo))
    assert rc == 0
    assert "no aged terminal-root plans to sweep" in out


# ---------------------------------------------------------------------------
# E-05 / V-05: Must-not-break guards
# ---------------------------------------------------------------------------


def test_e05_guard_id6_still_archives(tmp_path: Path):
    """Guard (a): id6 selector still archives."""
    repo = _init_repo(tmp_path)
    p = _make_plan(
        repo, "executed", "20260701-grp-01-id0001-id6-target.ipd.md", plan_id="id0001"
    )
    rc, out, _ = _run_archive("plans", "id0001", "--apply", "--dir", str(repo))
    assert rc == 0
    assert not p.exists()
    assert (
        repo / ".aw" / "records" / "plans" / "executed" / "202607" / p.name
    ).exists()


def test_e05_guard_bare_sweep_age_selection(tmp_path: Path):
    """Guard (c): bare sweep with --age respects age duration."""
    repo = _init_repo(tmp_path)
    _make_plan(
        repo,
        "executed",
        "20260101-old-01-old001-old-plan.ipd.md",
        plan_id="old001",
        date_="20260101",
    )
    today_str = date.today().strftime("%Y%m%d")
    _make_plan(
        repo,
        "executed",
        f"{today_str}-new-01-new001-new-plan.ipd.md",
        plan_id="new001",
        date_=today_str,
    )

    rc, out, _ = _run_archive("plans", "--age", "5d", "--dir", str(repo))
    assert rc == 0
    assert "20260101-old-01-old001-old-plan.ipd.md" in out
    assert "new001" not in out


def test_e05_guard_already_sharded_plan_not_candidate(tmp_path: Path):
    """Guard (d): a plan already inside a monthly shard refuses if targeted."""
    repo = _init_repo(tmp_path)
    p = _make_plan(
        repo,
        "executed",
        "20260701-shd-01-shd001-already-sharded.ipd.md",
        plan_id="shd001",
        shard="202607",
    )
    assert p.exists()
    rc, out, _ = _run_archive("plans", "shd001", "--dir", str(repo))
    assert rc != 0
    assert "not at a terminal disposition root" in out or "is not terminal" in out


def test_e05_guard_foreign_type_path_refuses(tmp_path: Path):
    """Guard (e): a foreign-type path handed to aw archive plans refuses via Order 01 containment guard."""
    repo = _init_repo(tmp_path)
    spec_dir = repo / ".aw" / "records" / "specs" / "implemented"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_file = spec_dir / "20260701-spc-01-spc001-sample-spec.spec.md"
    spec_file.write_text(
        "# Spec: Sample Spec\n\n- Date: 2026-07-01\n- Status: implemented\n- Id: spc001\n",
        encoding="utf-8",
    )

    rel_spec = spec_file.relative_to(repo).as_posix()
    rc, out, _ = _run_archive("plans", rel_spec, "--dir", str(repo))
    assert rc != 0
    assert "plans verb cannot act on" in out
    assert "it is not inside the plans records tree" in out

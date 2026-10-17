"""Tests for record-to-repository reverse-mapping under companion records roots (IPD diya77, backlog miq4mi).

Validates that:
1. project_context.record_owner_root maps a record file under a companion records root
   to the owning target repository root using:
   - cwd candidate (when cwd is in target)
   - default sibling companion convention (<repo>.aw/records/ -> <repo>)
   - project registry target_paths (for attached projects, even when registered as records_backend: home)
2. Every companion candidate is accepted ONLY when its own resolved records backend is 'companion'
   and project_records_dir(candidate) contains the record path.
3. Unrelated directories, uninstalled siblings, moved targets, and non-records-root paths return None.
4. In-tree and AW_HOME records are unchanged.
5. Walkers (artifact_core, specs, status_set, record_placement, check_engine) route through the resolver.
6. Git-bound operations (review staleness advisory, specs status transition git_mv) stay on the companion git repo.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import pytest

from agent_workflows import (
    artifact_core,
    check_engine,
    project_context,
    record_placement,
    specs,
    status_set,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_aw(
    args: list[str],
    *,
    cwd: Path,
    home: Path,
    aw_home: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run `agent_workflows` in a subprocess with isolated environment."""
    run_env = os.environ.copy()
    run_env["HOME"] = str(home)
    run_env["AW_HOME"] = str(aw_home)
    run_env["XDG_CONFIG_HOME"] = str(home / ".config")
    run_env.pop("AW_CONFIG_DIR", None)
    run_env["AW_NO_REEXEC"] = "1"
    run_env["GIT_CEILING_DIRECTORIES"] = str(home.parent)
    run_env["AW_IPD_AUTHOR"] = "probe"
    existing_pp = run_env.get("PYTHONPATH", "")
    run_env["PYTHONPATH"] = (
        f"{REPO_ROOT}:{existing_pp}" if existing_pp else str(REPO_ROOT)
    )
    if env:
        run_env.update(env)

    cmd = [sys.executable, "-m", "agent_workflows", *args]
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=run_env,
        capture_output=True,
        text=True,
    )


def _init_git_repo(path: Path) -> None:
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def c1_sibling_companion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """C1: Real public-target-private-companion install of tmp_path/t with default sibling t.aw."""
    home = tmp_path / "home"
    home.mkdir()
    aw_home = home / ".aw"
    target = tmp_path / "t"
    target.mkdir()

    _init_git_repo(target)

    res = run_aw(
        [
            "install",
            ".",
            "--preset",
            "public-target-private-companion",
            "-y",
            "--no-interactive",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res.returncode == 0
    ), f"install failed:\nstdout: {res.stdout}\nstderr: {res.stderr}"

    # Scaffold a child plan
    res = run_aw(
        [
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--set",
            "probe",
            "--order",
            "1",
            "--priority",
            "low",
            "--work-kind",
            "chore",
            "--title",
            "Probe 1",
            "--apply",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res.returncode == 0
    ), f"scaffold failed:\nstdout: {res.stdout}\nstderr: {res.stderr}"

    companion = tmp_path / "t.aw"
    plans = list(companion.glob("records/plans/pending/*probe-01*.ipd.md"))
    assert len(plans) == 1, f"Expected 1 plan, found {plans}"
    plan_path = plans[0]

    id6 = None
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- Id:"):
            id6 = line.split(":", 1)[1].strip()
            break
    assert id6

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("AW_NO_REEXEC", "1")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    monkeypatch.setenv("AW_IPD_AUTHOR", "probe")

    return target, companion, plan_path, id6, home, aw_home


@pytest.fixture
def c2_custom_companion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """C2: Install with --companion-dir tmp_path/priv/records-repo (non-sibling companion)."""
    home = tmp_path / "home_c2"
    home.mkdir()
    aw_home = home / ".aw"
    target = tmp_path / "t_c2"
    target.mkdir()
    companion = tmp_path / "priv" / "records-repo"

    _init_git_repo(target)

    res = run_aw(
        [
            "install",
            ".",
            "--preset",
            "public-target-private-companion",
            "--companion-dir",
            str(companion),
            "-y",
            "--no-interactive",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res.returncode == 0
    ), f"install failed:\nstdout: {res.stdout}\nstderr: {res.stderr}"

    res = run_aw(
        [
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--set",
            "probe",
            "--order",
            "1",
            "--priority",
            "low",
            "--work-kind",
            "chore",
            "--title",
            "Probe 1",
            "--apply",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res.returncode == 0
    ), f"scaffold failed:\nstdout: {res.stdout}\nstderr: {res.stderr}"

    plans = list(companion.glob("records/plans/pending/*probe-01*.ipd.md"))
    assert len(plans) == 1, f"Expected 1 plan, found {plans}"
    plan_path = plans[0]

    id6 = None
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- Id:"):
            id6 = line.split(":", 1)[1].strip()
            break
    assert id6

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("AW_NO_REEXEC", "1")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    monkeypatch.setenv("AW_IPD_AUTHOR", "probe")

    return target, companion, plan_path, id6, home, aw_home


@pytest.fixture
def c3_repository_backed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """C3: Repository-backed install (in-tree records at <target>/.aw/records)."""
    home = tmp_path / "home_c3"
    home.mkdir()
    aw_home = home / ".aw"
    target = tmp_path / "t_c3"
    target.mkdir()

    _init_git_repo(target)

    res = run_aw(
        [
            "install",
            ".",
            "--preset",
            "private-target",
            "-y",
            "--no-interactive",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res.returncode == 0
    ), f"install failed:\nstdout: {res.stdout}\nstderr: {res.stderr}"

    res = run_aw(
        [
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--set",
            "probe",
            "--order",
            "1",
            "--priority",
            "low",
            "--work-kind",
            "chore",
            "--title",
            "Probe 1",
            "--apply",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res.returncode == 0
    ), f"scaffold failed:\nstdout: {res.stdout}\nstderr: {res.stderr}"

    plans = list(target.glob(".aw/records/plans/pending/*probe-01*.ipd.md"))
    assert len(plans) == 1, f"Expected 1 plan, found {plans}"
    plan_path = plans[0]

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("AW_NO_REEXEC", "1")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    monkeypatch.setenv("AW_IPD_AUTHOR", "probe")

    return target, plan_path, home, aw_home


def test_sibling_companion_record_maps_to_target_from_target_cwd(
    c1_sibling_companion, monkeypatch: pytest.MonkeyPatch
):
    """1. C1, cwd = target: project_context.record_owner_root(<plan>) equals target root."""
    target, companion, plan_path, id6, home, aw_home = c1_sibling_companion
    monkeypatch.chdir(target)
    resolved = project_context.record_owner_root(plan_path)
    assert resolved is not None
    assert resolved.resolve() == target.resolve()


def test_sibling_companion_record_maps_from_unrelated_cwd(
    c1_sibling_companion, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """2. C1, cwd = tmp_path/else: same answer, via the sibling convention."""
    target, companion, plan_path, id6, home, aw_home = c1_sibling_companion
    else_dir = tmp_path / "else"
    else_dir.mkdir(exist_ok=True)
    monkeypatch.chdir(else_dir)
    resolved = project_context.record_owner_root(plan_path)
    assert resolved is not None
    assert resolved.resolve() == target.resolve()


def test_sibling_companion_with_git_maps_to_target(
    c1_sibling_companion, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """3. C1 after git init of the companion, cwd elsewhere: same answer."""
    target, companion, plan_path, id6, home, aw_home = c1_sibling_companion
    _init_git_repo(companion)

    else_dir = tmp_path / "else"
    else_dir.mkdir(exist_ok=True)
    monkeypatch.chdir(else_dir)
    resolved = project_context.record_owner_root(plan_path)
    assert resolved is not None
    assert resolved.resolve() == target.resolve()


def test_custom_companion_dir_from_target_cwd(
    c2_custom_companion, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """4. C2, cwd = target: equals target; cwd elsewhere without registry -> None; after attach -> target."""
    target, companion, plan_path, id6, home, aw_home = c2_custom_companion

    # (a) From target cwd -> equals target
    monkeypatch.chdir(target)
    resolved = project_context.record_owner_root(plan_path)
    assert resolved is not None
    assert resolved.resolve() == target.resolve()

    # (b) From elsewhere with no registry entry -> returns None (documented limit, OQ-01)
    else_dir = tmp_path / "else_c2"
    else_dir.mkdir(exist_ok=True)
    monkeypatch.chdir(else_dir)
    assert project_context.record_owner_root(plan_path) is None

    # (c) After real aw project attach by subprocess -> equals target from cwd elsewhere
    res = run_aw(
        ["project", "attach", "custom-proj", "--repo", str(target), "--yes"],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res.returncode == 0
    ), f"attach failed:\nstdout: {res.stdout}\nstderr: {res.stderr}"

    resolved_after = project_context.record_owner_root(plan_path)
    assert resolved_after is not None
    assert resolved_after.resolve() == target.resolve()


def test_companion_candidate_rejected_without_records_match(
    c1_sibling_companion,
    c3_repository_backed,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """5. Rejection pins:
    (a) sibling is plain git repo with no aw install -> None
    (b) C1 after mv t t2 from unrelated cwd -> None (no raise)
    (c) C3 repository containing docs/records/x.md -> None
    """
    target, companion, plan_path, id6, home, aw_home = c1_sibling_companion
    else_dir = tmp_path / "else_reject"
    else_dir.mkdir(exist_ok=True)
    monkeypatch.chdir(else_dir)

    # (a) Sibling directory u with no aw install
    u = tmp_path / "u"
    u.mkdir()
    _init_git_repo(u)
    u_aw = tmp_path / "u.aw"
    x_plan = u_aw / "records" / "plans" / "pending" / "x.ipd.md"
    x_plan.parent.mkdir(parents=True)
    x_plan.write_text("# Plan\n- Id: xxxxxx\n", encoding="utf-8")
    assert project_context.record_owner_root(x_plan) is None

    # (b) Target moved
    target_moved = tmp_path / "t2"
    shutil.move(str(target), str(target_moved))
    try:
        assert project_context.record_owner_root(plan_path) is None
    finally:
        # Restore target for cleanup
        shutil.move(str(target_moved), str(target))

    # (c) C3 repository with docs/records/x.md (records dir that is not candidate's records root)
    t_c3, plan_c3, home_c3, aw_home_c3 = c3_repository_backed
    docs_rec = t_c3 / "docs" / "records" / "x.md"
    docs_rec.parent.mkdir(parents=True)
    docs_rec.write_text("# Doc\n", encoding="utf-8")
    assert project_context.record_owner_root(docs_rec) is None


def test_in_tree_and_home_records_unchanged(
    c3_repository_backed, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """6. In-tree plan returns None; ki6t17 AW_HOME record returns target."""
    t_c3, plan_c3, home_c3, aw_home_c3 = c3_repository_backed

    # In-tree plan: resolver returns None (walkers keep climb)
    monkeypatch.chdir(t_c3)
    assert project_context.record_owner_root(plan_c3) is None

    else_dir = tmp_path / "else_unchanged"
    else_dir.mkdir(exist_ok=True)
    monkeypatch.chdir(else_dir)
    assert project_context.record_owner_root(plan_c3) is None

    # Clean-target AW_HOME record: ki6t17 returns target root
    home_ct = tmp_path / "home_ct"
    home_ct.mkdir()
    aw_home_ct = home_ct / ".aw"
    target_ct = tmp_path / "target_ct"
    target_ct.mkdir()
    _init_git_repo(target_ct)

    res = run_aw(
        [
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        ],
        cwd=target_ct,
        home=home_ct,
        aw_home=aw_home_ct,
    )
    assert res.returncode == 0

    res = run_aw(
        [
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--set",
            "probe",
            "--order",
            "1",
            "--priority",
            "low",
            "--work-kind",
            "chore",
            "--title",
            "Probe CT",
            "--apply",
        ],
        cwd=target_ct,
        home=home_ct,
        aw_home=aw_home_ct,
    )
    assert res.returncode == 0

    ct_plans = list(
        aw_home_ct.glob("projects/*/records/plans/pending/*probe-01*.ipd.md")
    )
    assert len(ct_plans) == 1
    ct_plan = ct_plans[0]

    monkeypatch.setenv("HOME", str(home_ct))
    monkeypatch.setenv("AW_HOME", str(aw_home_ct))
    monkeypatch.chdir(else_dir)
    resolved_ct = project_context.record_owner_root(ct_plan)
    assert resolved_ct is not None
    assert resolved_ct.resolve() == target_ct.resolve()


def test_walkers_return_target_for_companion_record(
    c1_sibling_companion, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """7. Walkers return target for companion record (C1 with companion git, cwd elsewhere)."""
    target, companion, plan_path, id6, home, aw_home = c1_sibling_companion
    _init_git_repo(companion)

    else_dir = tmp_path / "else_walkers"
    else_dir.mkdir(exist_ok=True)
    monkeypatch.chdir(else_dir)

    expected_target = target.resolve()
    assert artifact_core.repo_root_of(plan_path).resolve() == expected_target
    assert specs._repo_root_of(plan_path).resolve() == expected_target
    assert specs._spec_repo_root(plan_path).resolve() == expected_target
    assert status_set._repo_root_of(plan_path).resolve() == expected_target
    assert record_placement._find_repo_root(plan_path).resolve() == expected_target

    hint = check_engine._identity_rename_hint("plans", id6, "Id", False, plan_path)
    assert hint == f"aw rename plans {id6} --to-id6 --apply"


def test_ipd_lint_resolves_companion_sibling_dependency(
    c1_sibling_companion, home=None
):
    """8. C1, subprocess from target: plan 2 depends on plan 1. No dangling diagnostic; zzzzzz has it."""
    target, companion, plan_path, id6, home, aw_home = c1_sibling_companion

    # Scaffold plan 2
    res = run_aw(
        [
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--set",
            "probe",
            "--order",
            "2",
            "--priority",
            "low",
            "--work-kind",
            "chore",
            "--title",
            "Probe 2",
            "--apply",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0

    plans2 = list(companion.glob("records/plans/pending/*probe-02*.ipd.md"))
    assert len(plans2) == 1
    plan2_path = plans2[0]

    # Set both to to-review
    res = run_aw(
        ["ipd", "set", "to-review", str(plan_path), "--no-commit"],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0
    res = run_aw(
        ["ipd", "set", "to-review", str(plan2_path), "--no-commit"],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0

    # Point plan 2 dependencies to executed:<id6>
    txt = plan2_path.read_text(encoding="utf-8")
    txt = re.sub(r"- Item-Dependencies:.*", f"- Item-Dependencies: executed:{id6}", txt)
    plan2_path.write_text(txt, encoding="utf-8")

    # Lint plan 2: must NOT contain check.ipd-dependency-dangling
    res = run_aw(
        ["ipd", "lint", "--phase", "pre-execution", str(plan2_path)],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert "check.ipd-dependency-dangling" not in res.stdout
    assert "check.ipd-dependency-dangling" not in res.stderr

    # Falsifiability: point to executed:zzzzzz -> MUST contain check.ipd-dependency-dangling
    txt = re.sub(r"- Item-Dependencies:.*", "- Item-Dependencies: executed:zzzzzz", txt)
    plan2_path.write_text(txt, encoding="utf-8")
    res_z = run_aw(
        ["ipd", "lint", "--phase", "pre-execution", str(plan2_path)],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert "check.ipd-dependency-dangling" in (res_z.stdout + res_z.stderr)


def test_specs_note_history_lands_in_companion_records_root(tmp_path: Path):
    """9. C1, subprocess from target: specs note lands in <companion>/records/history.jsonl,
    both before and after git init of the companion.
    """
    # Part A: Before git init of companion
    home_a = tmp_path / "home_9a"
    home_a.mkdir()
    aw_home_a = home_a / ".aw"
    target_a = tmp_path / "t_9a"
    target_a.mkdir()
    _init_git_repo(target_a)

    res = run_aw(
        [
            "install",
            ".",
            "--preset",
            "public-target-private-companion",
            "-y",
            "--no-interactive",
        ],
        cwd=target_a,
        home=home_a,
        aw_home=aw_home_a,
    )
    assert res.returncode == 0
    companion_a = tmp_path / "t_9a.aw"

    res = run_aw(
        ["specs", "new", "--title", "Spec A", "--slug", "spec-a", "--apply"],
        cwd=target_a,
        home=home_a,
        aw_home=aw_home_a,
    )
    assert res.returncode == 0
    specs_a = list(companion_a.glob("records/specs/draft/*spec-a*.spec.md"))
    assert len(specs_a) == 1
    spec_a_path = specs_a[0]
    id6_a = spec_a_path.name.split("-")[2]

    res = run_aw(
        ["specs", "note", str(spec_a_path), "--message", "note before git"],
        cwd=target_a,
        home=home_a,
        aw_home=aw_home_a,
    )
    assert res.returncode == 0

    hist_files_a = list(tmp_path.glob("**/history.jsonl"))
    expected_hist_a = companion_a / "records" / "history.jsonl"
    assert hist_files_a == [
        expected_hist_a
    ], f"Unexpected history files: {hist_files_a}"
    assert id6_a in expected_hist_a.read_text(encoding="utf-8")

    # Part B: After git init + commit of companion
    home_b = tmp_path / "home_9b"
    home_b.mkdir()
    aw_home_b = home_b / ".aw"
    target_b = tmp_path / "t_9b"
    target_b.mkdir()
    _init_git_repo(target_b)

    res = run_aw(
        [
            "install",
            ".",
            "--preset",
            "public-target-private-companion",
            "-y",
            "--no-interactive",
        ],
        cwd=target_b,
        home=home_b,
        aw_home=aw_home_b,
    )
    assert res.returncode == 0
    companion_b = tmp_path / "t_9b.aw"
    _init_git_repo(companion_b)
    # Commit existing companion files
    subprocess.run(["git", "add", "."], cwd=companion_b, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial companion"], cwd=companion_b, check=True
    )

    res = run_aw(
        ["specs", "new", "--title", "Spec B", "--slug", "spec-b", "--apply"],
        cwd=target_b,
        home=home_b,
        aw_home=aw_home_b,
    )
    assert res.returncode == 0
    specs_b = list(companion_b.glob("records/specs/draft/*spec-b*.spec.md"))
    assert len(specs_b) == 1
    spec_b_path = specs_b[0]
    id6_b = spec_b_path.name.split("-")[2]

    res = run_aw(
        ["specs", "note", str(spec_b_path), "--message", "note after git"],
        cwd=target_b,
        home=home_b,
        aw_home=aw_home_b,
    )
    assert res.returncode == 0

    hist_files_b = [
        f
        for f in tmp_path.glob("**/history.jsonl")
        if str(f).startswith(str(companion_b))
    ]
    expected_hist_b = companion_b / "records" / "history.jsonl"
    assert hist_files_b == [
        expected_hist_b
    ], f"Unexpected history files: {hist_files_b}"
    assert id6_b in expected_hist_b.read_text(encoding="utf-8")


def test_review_stale_advisory_still_fires_for_companion_git_record(
    c1_sibling_companion, tmp_path: Path
):
    """10. C1 with companion git, cwd elsewhere, subprocess: review stale advisory still fires."""
    target, companion, plan_path, id6, home, aw_home = c1_sibling_companion
    _init_git_repo(companion)

    res = run_aw(
        ["ipd", "set", "reviewed", str(plan_path), "--no-commit"],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0

    subprocess.run(["git", "add", "."], cwd=companion, check=True)
    subprocess.run(
        ["git", "commit", "-m", "plan-review: probe"], cwd=companion, check=True
    )

    # Rewrite an execution item line in plan_path
    txt = plan_path.read_text(encoding="utf-8")
    txt = txt.replace("E-01 ", "E-01 edited ")
    plan_path.write_text(txt, encoding="utf-8")

    else_dir = tmp_path / "else_stale"
    else_dir.mkdir(exist_ok=True)

    res = run_aw(
        ["ipd", "lint", "--phase", "author", "--agent", str(plan_path)],
        cwd=else_dir,
        home=home,
        aw_home=aw_home,
    )
    assert "check.ipd-review-may-be-stale" in res.stdout


def test_companion_record_move_stays_staged_in_companion_git(c1_sibling_companion):
    """11. C1 with companion git, committed, cwd = target, subprocess: specs set to-review stays staged in companion."""
    target, companion, plan_path, id6, home, aw_home = c1_sibling_companion
    _init_git_repo(companion)
    subprocess.run(["git", "add", "."], cwd=companion, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial companion"], cwd=companion, check=True
    )

    # Create a spec
    res = run_aw(
        ["specs", "new", "--title", "Spec Move", "--slug", "spec-move", "--apply"],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0
    specs_list = list(companion.glob("records/specs/draft/*spec-move*.spec.md"))
    assert len(specs_list) == 1
    spec_path = specs_list[0]

    # Commit spec in companion
    subprocess.run(["git", "add", "."], cwd=companion, check=True)
    subprocess.run(["git", "commit", "-m", "add spec"], cwd=companion, check=True)

    # Transition spec to to-review
    res = run_aw(
        ["specs", "set", "to-review", str(spec_path), "--no-commit", "--yes"],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0

    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=companion,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = proc.stdout.splitlines()
    # Expect staged rename (R)
    staged_renames = [
        line
        for line in lines
        if line.startswith("R") or (len(line) > 1 and line[0] == "R")
    ]
    assert (
        staged_renames
    ), f"Expected staged rename in companion git status:\n{proc.stdout}"
    assert (
        " D " not in proc.stdout
    ), f"Unexpected unstaged deletion in companion git status:\n{proc.stdout}"

"""Tests for record-to-repository reverse-mapping under AW_HOME (IPD ki6t17, backlog 4uw2a6).

Validates that:
1. project_context.record_owner_root resolves a record file under
   AW_HOME/projects/<id>/records/ to the owning target repo root using:
   - cwd candidate (when cwd is in target)
   - local.json common_dir back-pointer (when cwd is elsewhere)
   - registry.json target_paths (for attached/registered projects)
2. Every candidate is verified against project_records_dir.
3. Non-record paths and foreign/stale back-pointers are ignored/rejected.
4. Walkers (artifact_core, specs, status_set, record_placement, ipd_lint,
   orchestrator_readiness, check_engine) route through the resolver.
5. install_wizard writes common_dir into AW_HOME local.json without touching the target.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

from agent_workflows import (
    artifact_core,
    check_engine,
    project_context,
    project_registry,
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
    run_env["AW_IPD_AUTHOR"] = "agent"
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


@pytest.fixture
def f1_clean_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """F1: Completely clean-target install under tmp_path with a scaffolded plan."""
    home = tmp_path / "home"
    home.mkdir()
    aw_home = home / ".aw"
    target = tmp_path / "target"
    target.mkdir()

    subprocess.run(
        ["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=target, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=target, check=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Initial commit"],
        cwd=target,
        check=True,
        capture_output=True,
    )

    res = run_aw(
        [
            "install",
            ".",
            "--preset",
            "completely-clean-target",
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

    # Scaffold a plan in Set probe
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
            "medium",
            "--work-kind",
            "bug",
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

    plans = list(aw_home.glob("projects/*/records/plans/pending/*probe-01*.ipd.md"))
    assert len(plans) == 1
    plan_path = plans[0]

    id6 = None
    for line in plan_path.read_text().splitlines():
        if line.startswith("- Id:"):
            id6 = line.split(":", 1)[1].strip()
            break
    assert id6

    # Setup monkeypatch for in-process tests
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("AW_NO_REEXEC", "1")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))

    return target, home, aw_home, plan_path, id6


@pytest.fixture
def f2_tracked_home_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """F2: Tracked records_backend: home repository with no home local.json."""
    home = tmp_path / "home_f2"
    home.mkdir()
    aw_home = home / ".aw"
    target = tmp_path / "target_f2"
    target.mkdir()

    cfg_dir = target / ".aw" / "config"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "project.json").write_text(
        json.dumps(
            {
                "preset": "private-target",
                "delivery_mode": "tracked",
                "records_backend": "home",
            }
        ),
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=target, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=target, check=True
    )
    subprocess.run(["git", "add", ".aw/config/project.json"], cwd=target, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=target,
        check=True,
        capture_output=True,
    )

    # Resolve project id and create a plan under aw_home records
    pid = project_context.resolve_project_context(
        str(target), aw_home=str(aw_home)
    ).project_id
    plan_dir = aw_home / "projects" / pid / "records" / "plans" / "pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / "20261016-probe-01-f2plan-probe.ipd.md"
    plan_path.write_text(
        "---\n# IPD: Probe\n- Id: f2plan\n- Set: probe\n- Order: 1\n- Status: draft\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("AW_NO_REEXEC", "1")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))

    return target, home, aw_home, plan_path, pid


@pytest.fixture
def f3_repo_backed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """F3: Standard repository-backed install."""
    home = tmp_path / "home_f3"
    home.mkdir()
    aw_home = home / ".aw"
    target = tmp_path / "target_f3"
    target.mkdir()

    subprocess.run(
        ["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=target, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=target, check=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Initial commit"],
        cwd=target,
        check=True,
        capture_output=True,
    )

    res = run_aw(
        ["install", ".", "--preset", "private-target", "-y", "--no-interactive"],
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
            "medium",
            "--work-kind",
            "bug",
            "--title",
            "Repo backed plan",
            "--apply",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res.returncode == 0
    ), f"scaffold failed:\nstdout: {res.stdout}\nstderr: {res.stderr}"

    rb_plans = list(target.glob(".aw/records/plans/pending/*.ipd.md"))
    assert len(rb_plans) == 1
    rb_plan_path = rb_plans[0]
    rb_id6 = None
    for line in rb_plan_path.read_text().splitlines():
        if line.startswith("- Id:"):
            rb_id6 = line.split(":", 1)[1].strip()
            break
    assert rb_id6

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("AW_NO_REEXEC", "1")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))

    return target, home, aw_home, rb_plan_path, rb_id6


def test_resolver_maps_home_record_to_target_from_target_cwd(
    f1_clean_target, monkeypatch: pytest.MonkeyPatch
):
    """Test 1: project_context.record_owner_root maps home record to target when cwd = target."""
    target, home, aw_home, plan_path, _ = f1_clean_target
    monkeypatch.chdir(target)
    resolved = project_context.record_owner_root(plan_path)
    assert resolved is not None
    assert resolved.resolve() == target.resolve()


def test_resolver_maps_home_record_from_unrelated_cwd(
    f1_clean_target, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test 2: maps home record to target from unrelated cwd via local.json back-pointer."""
    target, home, aw_home, plan_path, _ = f1_clean_target
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    # Once E-04 is in place, local.json has common_dir set.
    resolved = project_context.record_owner_root(plan_path)
    assert resolved is not None
    assert resolved.resolve() == target.resolve()


def test_resolver_tracked_home_backend_from_target_cwd(
    f2_tracked_home_backend, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test 3: tracked records_backend: home resolves from target cwd; returns None from elsewhere."""
    target, home, aw_home, plan_path, _ = f2_tracked_home_backend
    monkeypatch.chdir(target)
    resolved = project_context.record_owner_root(plan_path)
    assert resolved is not None
    assert resolved.resolve() == target.resolve()

    elsewhere = tmp_path / "elsewhere_f2"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    # No back-pointer and no registry entry: returns None
    assert project_context.record_owner_root(plan_path) is None


def test_resolver_registry_entry_resolves(
    f2_tracked_home_backend, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test 4: project_registry entry resolves from unrelated cwd."""
    target, home, aw_home, plan_path, pid = f2_tracked_home_backend
    elsewhere = tmp_path / "elsewhere_f2_reg"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    # Register project in registry.json
    project_registry.register_or_update_project(
        str(target), str(aw_home), project_id=pid
    )

    resolved = project_context.record_owner_root(plan_path)
    assert resolved is not None
    assert resolved.resolve() == target.resolve()


def test_resolver_rejects_stale_or_foreign_back_pointer(
    f1_clean_target, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test 5: rejects foreign back-pointer and stale moved target without raising."""
    target, home, aw_home, plan_path, _ = f1_clean_target
    elsewhere = tmp_path / "elsewhere_f1_reject"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    # (a) Rewrite local.json common_dir to another real repo's .git
    foreign_repo = tmp_path / "foreign_repo"
    foreign_repo.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=foreign_repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=foreign_repo, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=foreign_repo,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Initial commit"],
        cwd=foreign_repo,
        check=True,
        capture_output=True,
    )

    target_pid = plan_path.parents[3].name
    local_json_path = aw_home / "projects" / target_pid / "config" / "local.json"
    local_data = json.loads(local_json_path.read_text(encoding="utf-8"))
    local_data["common_dir"] = str(foreign_repo / ".git")
    local_json_path.write_text(json.dumps(local_data, indent=2), encoding="utf-8")

    assert project_context.record_owner_root(plan_path) is None

    # (b) Move target to target2: back-pointer points to nonexistent path
    target2 = tmp_path / "target2"
    target.rename(target2)
    local_data["common_dir"] = str(target / ".git")
    local_json_path.write_text(json.dumps(local_data, indent=2), encoding="utf-8")

    assert project_context.record_owner_root(plan_path) is None


def test_resolver_ignores_non_record_paths(
    f1_clean_target, f3_repo_backed, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test 6: ignores in-tree records, system/worktree/history files, and external paths."""
    target, home, aw_home, plan_path, _ = f1_clean_target
    rb_target, rb_home, rb_aw_home, rb_plan_path, _ = f3_repo_backed

    pid = plan_path.parents[3].name

    # In-tree record of F3
    monkeypatch.setenv("HOME", str(rb_home))
    monkeypatch.setenv("AW_HOME", str(rb_aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(rb_home / ".config"))
    assert project_context.record_owner_root(rb_plan_path) is None

    # Home record environment
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))

    # File under system/
    sys_file = aw_home / "projects" / pid / "system" / "dummy.txt"
    sys_file.parent.mkdir(parents=True, exist_ok=True)
    sys_file.write_text("dummy", encoding="utf-8")
    assert project_context.record_owner_root(sys_file) is None

    # File under worktrees/
    wt_file = aw_home / "projects" / pid / "worktrees" / "wt1" / "dummy.txt"
    wt_file.parent.mkdir(parents=True, exist_ok=True)
    wt_file.write_text("dummy", encoding="utf-8")
    assert project_context.record_owner_root(wt_file) is None

    # AW_HOME top-level records/history.jsonl
    top_hist = aw_home / "records" / "history.jsonl"
    top_hist.parent.mkdir(parents=True, exist_ok=True)
    top_hist.write_text("{}", encoding="utf-8")
    assert project_context.record_owner_root(top_hist) is None

    # Path outside AW_HOME
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    assert project_context.record_owner_root(outside) is None


def test_group_a_walkers_return_target(
    f1_clean_target, f3_repo_backed, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test 7: Group A walkers return target for home records; in-tree records remain unchanged."""
    target, home, aw_home, plan_path, _ = f1_clean_target
    rb_target, rb_home, rb_aw_home, rb_plan_path, _ = f3_repo_backed

    elsewhere = tmp_path / "elsewhere_group_a"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    # Home record
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    assert artifact_core.repo_root_of(plan_path).resolve() == target.resolve()
    assert specs._repo_root_of(plan_path).resolve() == target.resolve()
    assert specs._spec_repo_root(plan_path).resolve() == target.resolve()
    assert status_set._repo_root_of(plan_path).resolve() == target.resolve()
    assert record_placement._find_repo_root(plan_path).resolve() == target.resolve()

    # In-tree record
    monkeypatch.setenv("HOME", str(rb_home))
    monkeypatch.setenv("AW_HOME", str(rb_aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(rb_home / ".config"))
    assert artifact_core.repo_root_of(rb_plan_path).resolve() == rb_target.resolve()
    assert specs._repo_root_of(rb_plan_path).resolve() == rb_target.resolve()
    assert specs._spec_repo_root(rb_plan_path).resolve() == rb_target.resolve()
    assert status_set._repo_root_of(rb_plan_path).resolve() == rb_target.resolve()
    assert (
        record_placement._find_repo_root(rb_plan_path).resolve() == rb_target.resolve()
    )


def test_specs_note_history_lands_in_project_records(f1_clean_target):
    """Test 8: aw specs note writes history sidecar under project records, not AW_HOME root."""
    target, home, aw_home, _, _ = f1_clean_target

    res = run_aw(
        ["specs", "new", "--title", "Probe spec", "--slug", "probe-spec", "--apply"],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0, f"specs new failed: {res.stderr}"

    spec_files = list(
        aw_home.glob("projects/*/records/specs/draft/*probe-spec*.spec.md")
    )
    assert len(spec_files) == 1
    spec_path = spec_files[0]
    spec_id6 = None
    for line in spec_path.read_text().splitlines():
        if line.startswith("- Id:"):
            spec_id6 = line.split(":", 1)[1].strip()
            break
    assert spec_id6

    res = run_aw(
        ["specs", "note", str(spec_path), "--message", "note message"],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0, f"specs note failed: {res.stderr}"

    # Project records history sidecar must contain spec_id6
    target_pid = spec_path.parents[3].name
    project_history = aw_home / "projects" / target_pid / "records" / "history.jsonl"
    assert project_history.exists(), f"{project_history} does not exist"
    assert spec_id6 in project_history.read_text()

    # Top-level AW_HOME records/history.jsonl must NOT exist
    top_history = aw_home / "records" / "history.jsonl"
    assert not top_history.exists(), f"Found unexpected top-level {top_history}"

    # Target repo remains completely clean
    st = subprocess.run(
        ["git", "status", "--porcelain", "--ignored"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    )
    assert st.stdout.strip() == ""


def test_ipd_lint_resolves_home_sibling_dependency(f1_clean_target):
    """Test 9: aw ipd lint resolves sibling dependencies stored under AW_HOME."""
    target, home, aw_home, plan1_path, plan1_id6 = f1_clean_target

    # Scaffold plan 2 in same set
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
            "medium",
            "--work-kind",
            "bug",
            "--title",
            "Probe 2",
            "--apply",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0, res.stderr
    plan2_files = list(
        aw_home.glob("projects/*/records/plans/pending/*probe-02*.ipd.md")
    )
    assert len(plan2_files) == 1
    plan2_path = plan2_files[0]
    plan2_id6 = None
    for line in plan2_path.read_text().splitlines():
        if line.startswith("- Id:"):
            plan2_id6 = line.split(":", 1)[1].strip()
            break

    run_aw(
        ["ipd", "set", "to-review", plan1_id6], cwd=target, home=home, aw_home=aw_home
    )

    content2 = plan2_path.read_text()
    new_lines = []
    for line in content2.splitlines():
        if line.startswith("- Item-Dependencies:"):
            new_lines.append(f"- Item-Dependencies: executed:{plan1_id6}")
        else:
            new_lines.append(line)
    plan2_path.write_text("\n".join(new_lines) + "\n")

    run_aw(
        ["ipd", "set", "to-review", plan2_id6], cwd=target, home=home, aw_home=aw_home
    )

    # Lint plan 2: should NOT report ipd-dependency-dangling for plan1_id6
    lint_res = run_aw(
        ["ipd", "lint", "--phase", "pre-execution", str(plan2_path)],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert "check.ipd-dependency-dangling" not in lint_res.stdout
    assert "check.ipd-dependency-dangling" not in lint_res.stderr

    # Falsifiability: pointing at executed:zzzzzz DOES report it
    falsified_lines = []
    for line in plan2_path.read_text().splitlines():
        if line.startswith("- Item-Dependencies:"):
            falsified_lines.append("- Item-Dependencies: executed:zzzzzz")
        else:
            falsified_lines.append(line)
    plan2_path.write_text("\n".join(falsified_lines) + "\n")

    lint_falsified = run_aw(
        ["ipd", "lint", "--phase", "pre-execution", str(plan2_path)],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        "check.ipd-dependency-dangling" in lint_falsified.stdout
        or "check.ipd-dependency-dangling" in lint_falsified.stderr
    )


def test_ipd_coverage_from_clean_target_root(f1_clean_target, tmp_path: Path):
    """Test 10: aw ipd coverage works from clean target root in both /tmp and $HOME/src/target layouts."""
    target, home, aw_home, plan_path, plan_id6 = f1_clean_target

    # Variant 1: target directly under tmp_path
    res1 = run_aw(["ipd", "coverage", plan_id6], cwd=target, home=home, aw_home=aw_home)
    out1 = res1.stdout + res1.stderr
    assert "no agent-workflows project root located" not in out1
    assert "no matching plans found" not in out1
    # Plan is a child plan, so coverage reports no orchestrator plans selected with exit 2
    assert "error: no orchestrator plans selected among targets" in out1
    assert res1.returncode == 2

    # Variant 2: target lives at <home>/src/t2 with AW_HOME=<home>/.aw
    t2 = home / "src" / "t2"
    t2.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=t2, check=True, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=t2, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=t2, check=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Initial commit"],
        cwd=t2,
        check=True,
        capture_output=True,
    )

    run_aw(
        [
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        ],
        cwd=t2,
        home=home,
        aw_home=aw_home,
    )
    run_aw(
        [
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--set",
            "probe2",
            "--order",
            "1",
            "--priority",
            "medium",
            "--work-kind",
            "bug",
            "--title",
            "Probe 2 plan",
            "--apply",
        ],
        cwd=t2,
        home=home,
        aw_home=aw_home,
    )
    t2_plans = list(aw_home.glob("projects/*/records/plans/pending/*probe2-01*.ipd.md"))
    assert len(t2_plans) == 1
    t2_plan_path = t2_plans[0]
    t2_plan_id6 = None
    for line in t2_plan_path.read_text().splitlines():
        if line.startswith("- Id:"):
            t2_plan_id6 = line.split(":", 1)[1].strip()
            break
    assert t2_plan_id6

    res2 = run_aw(["ipd", "coverage", t2_plan_id6], cwd=t2, home=home, aw_home=aw_home)
    out2 = res2.stdout + res2.stderr
    assert "no agent-workflows project root located" not in out2
    assert "no matching plans found" not in out2
    assert "error: no orchestrator plans selected among targets" in out2
    assert res2.returncode == 2


def test_identity_rename_hint_for_home_record(
    f1_clean_target, f3_repo_backed, monkeypatch: pytest.MonkeyPatch
):
    """Test 11: _identity_rename_hint returns rename command for home records."""
    target, home, aw_home, plan_path, plan_id6 = f1_clean_target
    rb_target, rb_home, rb_aw_home, rb_plan_path, rb_id6 = f3_repo_backed

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.chdir(target)
    hint_home = check_engine._identity_rename_hint(
        "plans", plan_id6, "Id", False, plan_path
    )
    assert hint_home == f"aw rename plans {plan_id6} --to-id6 --apply"

    monkeypatch.setenv("HOME", str(rb_home))
    monkeypatch.setenv("AW_HOME", str(rb_aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(rb_home / ".config"))
    monkeypatch.chdir(rb_target)
    hint_rb = check_engine._identity_rename_hint(
        "plans", rb_id6, "Id", False, rb_plan_path
    )
    assert hint_rb == f"aw rename plans {rb_id6} --to-id6 --apply"


def test_install_writes_back_pointer_without_target_delta(tmp_path: Path):
    """Test 12: clean-target install sets common_dir in local.json; re-install preserves it."""
    home = tmp_path / "home_t12"
    home.mkdir()
    aw_home = home / ".aw"
    target = tmp_path / "target_t12"
    target.mkdir()

    subprocess.run(
        ["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=target, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=target, check=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Initial commit"],
        cwd=target,
        check=True,
        capture_output=True,
    )

    head_before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    res = run_aw(
        [
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0, res.stderr

    # Head and working tree unchanged
    head_after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert head_before == head_after

    st = subprocess.run(
        ["git", "status", "--porcelain", "--ignored"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    )
    assert st.stdout.strip() == ""

    # Check local.json has common_dir set to canonical target/.git
    local_files = list(aw_home.glob("projects/*/config/local.json"))
    assert len(local_files) == 1
    local_data = json.loads(local_files[0].read_text(encoding="utf-8"))
    assert local_data["common_dir"] == str((target / ".git").resolve())

    # Reinstall preserves existing non-null common_dir
    local_data["common_dir"] = "/custom/preserved/path/.git"
    local_files[0].write_text(json.dumps(local_data, indent=2), encoding="utf-8")

    res2 = run_aw(
        [
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res2.returncode == 0, res2.stderr
    local_data_after = json.loads(local_files[0].read_text(encoding="utf-8"))
    assert local_data_after["common_dir"] == "/custom/preserved/path/.git"

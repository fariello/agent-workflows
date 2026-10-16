"""Subprocess and unit tests for system root accessor and clean-delta system bundle.

Validates IPD 4gn1ka (Set cleantgt).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

from agent_workflows import project_context
from agent_workflows.project_context import ProjectContextError

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


def test_accessor_unconfigured(tmp_path: Path):
    target = tmp_path / "unconfigured"
    target.mkdir()
    assert project_context.project_system_dir(target) == target / ".aw" / "system"


def test_accessor_role_target_in_tree(tmp_path: Path):
    target = tmp_path / "target"
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text(json.dumps({"role": "target"}), encoding="utf-8")
    assert project_context.project_system_dir(target) == target / ".aw" / "system"


def test_accessor_stored_tracked(tmp_path: Path):
    target = tmp_path / "target"
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text(
        json.dumps({"delivery_mode": "tracked"}), encoding="utf-8"
    )
    assert project_context.project_system_dir(target) == target / ".aw" / "system"


def test_accessor_stored_clean_delta_home_config(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    aw_home = tmp_path / "aw_home"
    project_id = project_context._derive_project_id(str(target.resolve()))
    home_cfg = aw_home / "projects" / project_id / "config"
    home_cfg.mkdir(parents=True)
    (home_cfg / "project.json").write_text(
        json.dumps({"delivery_mode": "clean-delta"}), encoding="utf-8"
    )
    res = project_context.project_system_dir(target, aw_home=aw_home)
    assert res == aw_home / "projects" / project_id / "system"


def test_accessor_stored_completely_clean_target_preset(tmp_path: Path):
    target = tmp_path / "target"
    aw_home = tmp_path / "aw_home"
    project_id = project_context._derive_project_id(str(target.resolve()))
    home_cfg = aw_home / "projects" / project_id / "config"
    home_cfg.mkdir(parents=True)
    (home_cfg / "project.json").write_text(
        json.dumps({"preset": "completely-clean-target"}), encoding="utf-8"
    )
    res = project_context.project_system_dir(target, aw_home=aw_home)
    assert res == aw_home / "projects" / project_id / "system"


def test_accessor_system_root_override_in_local_json(tmp_path: Path):
    target = tmp_path / "target"
    override_sys = tmp_path / "custom_system"
    override_sys.mkdir()
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "local.json").write_text(
        json.dumps({"system_root": str(override_sys)}), encoding="utf-8"
    )
    assert project_context.project_system_dir(target) == override_sys


def test_accessor_source_checkout_role(tmp_path: Path):
    target = tmp_path / "target"
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text(
        json.dumps({"role": "source-checkout", "delivery_mode": "tracked"}),
        encoding="utf-8",
    )
    assert project_context.project_system_dir(target) == target / ".aw" / "system"


def test_accessor_path_security_error_propagates(tmp_path: Path):
    target = tmp_path / "target"
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text(
        json.dumps({"delivery_mode": "clean-delta"}), encoding="utf-8"
    )
    # clean-delta with in-target system root (default when aw_home is inside target or local binding)
    in_target_home = target / "aw_home"
    with pytest.raises(ProjectContextError):
        project_context.project_system_dir(target, aw_home=in_target_home)


def test_read_side_clean_delta_home_bundle(tmp_path: Path):
    """V-03: Read-side target system lookups find bundle placed under AW_HOME."""
    target = tmp_path / "target"
    target.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    aw_home = home / ".aw"
    aw_home.mkdir()

    subprocess.run(["git", "init", "-b", "main", "-q"], cwd=target, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=target, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=target, check=True
    )
    (target / "README.md").write_text("# Target\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=target, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=target, check=True)

    project_id = project_context._derive_project_id(str(target.resolve()))
    home_project = aw_home / "projects" / project_id
    home_cfg = home_project / "config"
    home_cfg.mkdir(parents=True)
    (home_cfg / "project.json").write_text(
        json.dumps(
            {
                "preset": "completely-clean-target",
                "delivery_mode": "clean-delta",
                "records_backend": "home",
            }
        ),
        encoding="utf-8",
    )

    (target / ".aw" / "records").mkdir(parents=True)
    # Register target in user config
    user_cfg_dir = home / ".config" / "agent-workflows"
    user_cfg_dir.mkdir(parents=True)
    (user_cfg_dir / "config.json").write_text(
        json.dumps(
            {
                "repos": {
                    "installed": [str(target.resolve())],
                }
            }
        ),
        encoding="utf-8",
    )

    # Place bundle ONLY under home system
    home_sys = home_project / "system"
    home_sys.mkdir(parents=True)
    from agent_workflows import layout as _layout

    (home_sys / "VERSION").write_text("9.9.9\n", encoding="utf-8")
    model = _layout.build_default_layout()
    (home_sys / "layout.json").write_text(
        json.dumps(model.to_dict("9.9.9")), encoding="utf-8"
    )
    (home_sys / "layout.schema.json").write_text(
        json.dumps(model.to_schema()), encoding="utf-8"
    )
    (home_sys / "managed-sections.json").write_text(
        json.dumps({"schema_version": 1, "files": {}}), encoding="utf-8"
    )
    workflows_dir = home_sys / "workflows"
    workflows_dir.mkdir()
    (workflows_dir / "index.md").write_text("# Workflows\n", encoding="utf-8")

    # 1. aw doctor --json
    res_doctor = run_aw(["doctor", "--json"], cwd=target, home=home, aw_home=aw_home)
    assert res_doctor.returncode == 0, f"doctor stderr: {res_doctor.stderr}"
    doc_data = json.loads(res_doctor.stdout)
    assert doc_data["data"]["report"]["env"]["installed_version"] == "9.9.9"

    # 2. aw list-repos --json
    res_list = run_aw(["list-repos", "--json"], cwd=target, home=home, aw_home=aw_home)
    assert res_list.returncode == 0, f"list-repos stderr: {res_list.stderr}"
    list_data = json.loads(res_list.stdout)
    repos = list_data.get("data", {}).get("repos", [])
    matching = [
        r for r in repos if Path(r.get("repo", "")).resolve() == target.resolve()
    ]
    assert len(matching) == 1
    assert matching[0].get("installed") == "9.9.9"

    # 3. aw check all --dir <target>
    res_check = run_aw(
        ["check", "all", "--dir", str(target), "--json"],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res_check.returncode == 0, f"check stderr: {res_check.stderr}"
    check_data = json.loads(res_check.stdout)
    diag_codes = [
        d.get("code") for d in check_data.get("data", {}).get("diagnostics", [])
    ]
    assert "check.system-layout-missing" not in diag_codes

    # 4. aw layout
    res_layout = run_aw(
        ["layout", "--repo", str(target), "--json"],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res_layout.returncode == 0, f"layout stderr: {res_layout.stderr}"
    layout_data = json.loads(res_layout.stdout)
    assert layout_data["data"]["source"] == "emitted"
    assert layout_data["data"]["source_path"] == str(home_sys / "layout.json")


def test_write_side_clean_delta_install(tmp_path: Path):
    """V-04: aw install completely-clean-target writes bundle to AW_HOME and stages nothing."""
    target = tmp_path / "target"
    target.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    aw_home = home / ".aw"
    aw_home.mkdir()

    subprocess.run(["git", "init", "-b", "main", "-q"], cwd=target, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=target, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=target, check=True
    )
    (target / "README.md").write_text("# Target\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=target, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=target, check=True)

    res_install = run_aw(
        [
            "install",
            str(target),
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res_install.returncode == 0, f"install stderr: {res_install.stderr}"

    project_id = project_context._derive_project_id(str(target.resolve()))
    home_sys = aw_home / "projects" / project_id / "system"
    assert home_sys.exists(), f"Expected {home_sys} to exist"
    assert (home_sys / "VERSION").is_file()
    assert (home_sys / "managed-sections.json").is_file()
    assert (home_sys / "layout.json").is_file()
    assert (home_sys / "layout.schema.json").is_file()
    assert (home_sys / "workflows" / "index.md").is_file()

    # git ls-files in target has no .aw/system paths
    ls_files = subprocess.run(
        ["git", "ls-files"], cwd=target, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    system_staged = [p for p in ls_files if p.startswith(".aw/system")]
    assert len(system_staged) == 0, f"Found staged system files: {system_staged}"

    # git status --porcelain --ignored has no .aw/system paths
    status = subprocess.run(
        ["git", "status", "--porcelain", "--ignored"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    system_status = [p for p in status if ".aw/system" in p]
    assert (
        len(system_status) == 0
    ), f"Found untracked/ignored system files: {system_status}"

    # Second install reports bundle current (no rewrite)
    res_install2 = run_aw(
        [
            "install",
            str(target),
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res_install2.returncode == 0
    assert (
        "current" in res_install2.stdout.lower()
        or "up to date" in res_install2.stdout.lower()
        or "0 added" in res_install2.stdout.lower()
    )

    # Stale member pruning in home bundle
    stale_file = home_sys / "workflows" / "stale_test.md"
    stale_file.write_text("stale content\n", encoding="utf-8")
    assert stale_file.is_file()
    res_install3 = run_aw(
        [
            "install",
            str(target),
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res_install3.returncode == 0
    assert not stale_file.exists(), f"Stale file {stale_file} was not pruned"


def test_clean_delta_resolve_system_provider(tmp_path: Path):
    from agent_workflows import clean_delta

    # 1. Unconfigured repo
    unconf = tmp_path / "unconf"
    unconf.mkdir()
    info_unconf = clean_delta.resolve_system_provider(target_repo=str(unconf))
    assert info_unconf.system_root == str(unconf / ".aw" / "system")
    assert info_unconf.is_target_resident is True
    assert info_unconf.is_source_checkout is False

    # 2. Configured clean-delta repo
    clean_target = tmp_path / "clean_target"
    clean_target.mkdir()
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    pid = project_context._derive_project_id(str(clean_target.resolve()))
    home_cfg = aw_home / "projects" / pid / "config"
    home_cfg.mkdir(parents=True)
    (home_cfg / "project.json").write_text(
        json.dumps({"preset": "completely-clean-target"}), encoding="utf-8"
    )

    info_clean = clean_delta.resolve_system_provider(
        target_repo=str(clean_target), aw_home=str(aw_home)
    )
    expected_sys = str(aw_home / "projects" / pid / "system")
    assert info_clean.system_root == expected_sys
    assert info_clean.is_target_resident is False
    assert info_clean.is_source_checkout is False


def test_upgrade_rehearsal_probe(tmp_path: Path):
    """V-05: upgrade_rehearsal.probe with external AW_HOME, default in-sandbox AW_HOME, and tracked."""
    from agent_workflows import upgrade_rehearsal

    # 1. Clean-delta sandbox with external AW_HOME
    sandbox_clean = tmp_path / "sandbox_clean"
    sandbox_clean.mkdir()
    subprocess.run(["git", "init", "-b", "main", "-q"], cwd=sandbox_clean, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=sandbox_clean, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=sandbox_clean,
        check=True,
    )
    (sandbox_clean / "README.md").write_text("# Clean\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=sandbox_clean, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=sandbox_clean, check=True)

    ext_aw_home = tmp_path / "ext_aw_home"
    ext_aw_home.mkdir()
    pid_clean = project_context._derive_project_id(str(sandbox_clean.resolve()))
    cfg_clean = ext_aw_home / "projects" / pid_clean / "config"
    cfg_clean.mkdir(parents=True)
    (cfg_clean / "project.json").write_text(
        json.dumps({"preset": "completely-clean-target"}), encoding="utf-8"
    )
    sys_clean = ext_aw_home / "projects" / pid_clean / "system"
    sys_clean.mkdir(parents=True)
    (sys_clean / "VERSION").write_text("1.5.0\n", encoding="utf-8")
    (sys_clean / "managed-sections.json").write_text(
        json.dumps(
            {"schema_version": 1, "installed_version": "1.5.0", "files": {"f1": {}}}
        ),
        encoding="utf-8",
    )

    state_ext = upgrade_rehearsal.probe(sandbox_clean, aw_home=ext_aw_home)
    assert state_ext["installed_version"] == "1.5.0"
    assert state_ext["manifest"]["rows"] == 1
    assert state_ext["manifest"]["installed_version"] == "1.5.0"
    assert "system_root_error" not in state_ext

    # 2. Clean-delta sandbox with default in-sandbox AW_HOME (triggers PathSecurityError)
    in_sandbox_aw_home = sandbox_clean / ".aw-upgrade-test" / "aw-home"
    in_cfg = in_sandbox_aw_home / "projects" / pid_clean / "config"
    in_cfg.mkdir(parents=True)
    (in_cfg / "project.json").write_text(
        json.dumps({"preset": "completely-clean-target"}), encoding="utf-8"
    )
    # Probing with default aw_home (None -> <sandbox>/.aw-upgrade-test/aw-home)
    state_in = upgrade_rehearsal.probe(sandbox_clean)
    assert "system_root_error" in state_in
    assert "Clean-delta security violation" in state_in["system_root_error"]
    assert state_in["installed_version"] is None

    # 3. Tracked sandbox
    sandbox_tracked = tmp_path / "sandbox_tracked"
    sandbox_tracked.mkdir()
    subprocess.run(["git", "init", "-b", "main", "-q"], cwd=sandbox_tracked, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=sandbox_tracked, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=sandbox_tracked,
        check=True,
    )
    in_tree_sys = sandbox_tracked / ".aw" / "system"
    in_tree_sys.mkdir(parents=True)
    (in_tree_sys / "VERSION").write_text("2.0.0\n", encoding="utf-8")
    (in_tree_sys / "managed-sections.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "installed_version": "2.0.0",
                "files": {"t1": {}, "t2": {}},
            }
        ),
        encoding="utf-8",
    )
    (sandbox_tracked / "README.md").write_text("# Tracked\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=sandbox_tracked, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=sandbox_tracked, check=True)

    state_tracked = upgrade_rehearsal.probe(sandbox_tracked)
    assert state_tracked["installed_version"] == "2.0.0"
    assert state_tracked["manifest"]["rows"] == 2
    assert state_tracked["manifest"]["installed_version"] == "2.0.0"
    assert "system_root_error" not in state_tracked

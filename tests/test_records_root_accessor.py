"""Subprocess and unit tests for records root accessor and home records backend.

Validates IPD kfnfji (Set cleantgt).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

from agent_workflows import project_context

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
    run_env.pop("XDG_CONFIG_HOME", None)
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


@pytest.fixture
def home_records_env(tmp_path: Path):
    """Set up a target repo with stored records_backend: home and isolated AW_HOME."""
    target = tmp_path / "target"
    target.mkdir()
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    home = tmp_path / "home"
    home.mkdir()

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

    return target, home, aw_home


def test_home_records_reproduction_specs(home_records_env):
    """Specs writer already respects resolver and writes to AW_HOME (proving fixture sound)."""
    target, home, aw_home = home_records_env
    res = run_aw(
        [
            "specs",
            "new",
            "--title",
            "Foo",
            "--slug",
            "foo",
            "--apply",
            "--dir",
            str(target),
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0, f"stdout: {res.stdout}\nstderr: {res.stderr}"

    # Target tree must be clean of records
    assert not (target / ".aw" / "records").exists()
    assert not (target / ".agents" / "specs").exists()

    # Spec must exist under AW_HOME
    projects_dir = aw_home / "projects"
    spec_files = list(projects_dir.glob("*/records/specs/*/*.spec.md"))
    assert len(spec_files) == 1, f"Expected 1 spec under AW_HOME, found: {spec_files}"


def test_home_records_reproduction_backlog(home_records_env):
    """Backlog writer must land under AW_HOME and leave target tree clean."""
    target, home, aw_home = home_records_env
    res = run_aw(
        [
            "backlog",
            "new",
            "--summary",
            "x-thing",
            "--work-kind",
            "chore",
            "--priority",
            "low",
            "--slug",
            "x-thing",
            "--apply",
            "--dir",
            str(target),
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0, f"stdout: {res.stdout}\nstderr: {res.stderr}"

    # Target tree must have no .agents or .aw/records
    st = subprocess.run(
        ["git", "status", "--porcelain", "--ignored"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "??" not in st.stdout, f"Target working tree not clean:\n{st.stdout}"
    assert not (target / ".agents").exists(), "Found .agents in target"
    assert not (target / ".aw" / "records").exists(), "Found .aw/records in target"

    # Backlog item must exist under AW_HOME
    projects_dir = aw_home / "projects"
    backlog_files = list(projects_dir.glob("*/records/backlog/*/*.backlog.md"))
    assert (
        len(backlog_files) == 1
    ), f"Expected 1 backlog file under AW_HOME, found: {backlog_files}"


def test_home_records_reproduction_history_sidecar(home_records_env):
    """Record history sidecar must not be written into target."""
    target, home, aw_home = home_records_env
    res = run_aw(
        [
            "backlog",
            "new",
            "--summary",
            "history-check",
            "--work-kind",
            "chore",
            "--priority",
            "low",
            "--slug",
            "history-check",
            "--apply",
            "--dir",
            str(target),
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0, f"stdout: {res.stdout}\nstderr: {res.stderr}"

    # History file must not be in target
    assert not (
        target / ".aw" / "records" / "history.jsonl"
    ).exists(), "Found target/.aw/records/history.jsonl"

    # History file must exist under AW_HOME
    projects_dir = aw_home / "projects"
    history_files = list(projects_dir.glob("*/records/history.jsonl"))
    assert (
        len(history_files) == 1
    ), f"Expected 1 history file under AW_HOME, found: {history_files}"


def test_home_records_reproduction_prompts_index(home_records_env):
    """aw index prompts must succeed and write under AW_HOME, not fail with FileNotFoundError."""
    target, home, aw_home = home_records_env
    res = run_aw(
        ["index", "prompts", "--dir", str(target)],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0, f"stdout: {res.stdout}\nstderr: {res.stderr}"
    assert not (
        target / ".aw" / "records" / "prompts"
    ).exists(), "Found target/.aw/records/prompts"
    projects_dir = aw_home / "projects"
    index_files = list(projects_dir.glob("*/records/prompts/INDEX.json"))
    assert (
        len(index_files) == 1
    ), f"Expected 1 INDEX.json under AW_HOME, found: {index_files}"


def test_accessor_unconfigured(tmp_path: Path):
    target = tmp_path / "unconfigured"
    target.mkdir()
    assert project_context.has_stored_records_placement(target) is False
    assert project_context.project_records_dir(target) == target / ".aw" / "records"


def test_accessor_repository(tmp_path: Path):
    target = tmp_path / "target"
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text(
        json.dumps({"records_backend": "repository"}), encoding="utf-8"
    )
    assert project_context.has_stored_records_placement(target) is True
    assert project_context.project_records_dir(target) == target / ".aw" / "records"


def test_accessor_repository_untracked(tmp_path: Path):
    target = tmp_path / "target"
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text(
        json.dumps({"records_backend": "repository-untracked"}), encoding="utf-8"
    )
    assert project_context.has_stored_records_placement(target) is True
    assert project_context.project_records_dir(target) == target / ".aw" / "records"


def test_accessor_home(tmp_path: Path):
    target = tmp_path / "target"
    aw_home = tmp_path / "aw_home"
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text(
        json.dumps({"records_backend": "home"}), encoding="utf-8"
    )
    assert project_context.has_stored_records_placement(target, aw_home=aw_home) is True
    res = project_context.project_records_dir(target, aw_home=aw_home)
    assert (
        res
        == aw_home
        / "projects"
        / project_context._derive_project_id(str(target.resolve()))
        / "records"
    )


def test_accessor_companion(tmp_path: Path):
    target = tmp_path / "target"
    companion = tmp_path / "comp"
    companion.mkdir()
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text(
        json.dumps({"records_backend": "companion"}),
        encoding="utf-8",
    )
    (cfg / "local.json").write_text(
        json.dumps({"companion_dir": str(companion)}),
        encoding="utf-8",
    )
    assert project_context.has_stored_records_placement(target) is True
    assert project_context.project_records_dir(target) == companion / "records"


def test_accessor_local_json_only_home(tmp_path: Path):
    target = tmp_path / "target"
    aw_home = tmp_path / "aw_home"
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "local.json").write_text(
        json.dumps({"records_backend": "home"}), encoding="utf-8"
    )
    assert project_context.has_stored_records_placement(target, aw_home=aw_home) is True
    res = project_context.project_records_dir(target, aw_home=aw_home)
    assert (
        res
        == aw_home
        / "projects"
        / project_context._derive_project_id(str(target.resolve()))
        / "records"
    )


def test_accessor_stored_completely_clean_target_no_records_key(tmp_path: Path):
    target = tmp_path / "target"
    aw_home = tmp_path / "aw_home"
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text(
        json.dumps({"preset": "completely-clean-target"}), encoding="utf-8"
    )
    assert project_context.has_stored_records_placement(target, aw_home=aw_home) is True
    res = project_context.project_records_dir(target, aw_home=aw_home)
    assert (
        res
        == aw_home
        / "projects"
        / project_context._derive_project_id(str(target.resolve()))
        / "records"
    )


def test_accessor_stored_project_json_no_records_backend_no_preset(tmp_path: Path):
    target = tmp_path / "target"
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text(json.dumps({"role": "target"}), encoding="utf-8")
    # Must stay in-tree
    assert project_context.has_stored_records_placement(target) is False
    assert project_context.project_records_dir(target) == target / ".aw" / "records"


def test_accessor_home_stored_config(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    aw_home = tmp_path / "aw_home"
    project_id = project_context._derive_project_id(str(target.resolve()))
    home_cfg = aw_home / "projects" / project_id / "config"
    home_cfg.mkdir(parents=True)
    (home_cfg / "project.json").write_text(
        json.dumps({"records_backend": "home"}), encoding="utf-8"
    )
    assert project_context.has_stored_records_placement(target, aw_home=aw_home) is True
    res = project_context.project_records_dir(target, aw_home=aw_home)
    assert res == aw_home / "projects" / project_id / "records"


def test_accessor_cache_invalidation(tmp_path: Path):
    target = tmp_path / "target"
    aw_home = tmp_path / "aw_home"
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    p_json = cfg / "project.json"
    p_json.write_text(json.dumps({"role": "target"}), encoding="utf-8")

    assert (
        project_context.project_records_dir(target, aw_home=aw_home)
        == target / ".aw" / "records"
    )

    # Now update project.json to records_backend: home
    p_json.write_text(
        json.dumps({"role": "target", "records_backend": "home"}), encoding="utf-8"
    )
    res = project_context.project_records_dir(target, aw_home=aw_home)
    project_id = project_context._derive_project_id(str(target.resolve()))
    assert res == aw_home / "projects" / project_id / "records"


def test_bare_unconfigured_repo_parity(tmp_path: Path):
    """PR-002 parity guard: bare unconfigured repo resolves specs to AW_HOME and backlog in-tree."""
    target = tmp_path / "bare"
    target.mkdir()
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    home = tmp_path / "home"
    home.mkdir()

    subprocess.run(
        ["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True
    )

    res_specs = run_aw(
        [
            "specs",
            "new",
            "--title",
            "BareSpec",
            "--slug",
            "bare-spec",
            "--apply",
            "--dir",
            str(target),
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res_specs.returncode == 0
    ), f"stdout: {res_specs.stdout}\nstderr: {res_specs.stderr}"
    # Specs land under AW_HOME
    projects_dir = aw_home / "projects"
    specs = list(projects_dir.glob("*/records/specs/*/*.spec.md"))
    assert len(specs) == 1

    res_backlog = run_aw(
        [
            "backlog",
            "new",
            "--summary",
            "bare-item",
            "--work-kind",
            "chore",
            "--priority",
            "low",
            "--slug",
            "bare-item",
            "--apply",
            "--dir",
            str(target),
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res_backlog.returncode == 0
    ), f"stdout: {res_backlog.stdout}\nstderr: {res_backlog.stderr}"
    # Backlog lands in-tree under .agents/backlog (preserving HEAD behavior for unconfigured repo)
    assert (target / ".agents" / "backlog" / "open").is_dir()
    backlog_files = list((target / ".agents" / "backlog" / "open").glob("*.backlog.md"))
    assert len(backlog_files) == 1


def test_is_ignored_path_external_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from agent_workflows import artifact_core, project_context

    target = tmp_path / "target"
    target.mkdir()
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))
    cfg = target / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text(
        json.dumps({"records_backend": "home"}), encoding="utf-8"
    )

    rec_dir = project_context.project_records_dir(target, aw_home=aw_home)
    plan_path = rec_dir / "plans" / "pending" / "20261015-test-01-xxxxxx-test.ipd.md"
    untracked_prompt = rec_dir / "prompts" / "untracked" / "foo.prompt.md"

    # plan_path should NOT be ignored even though tmp is an ancestor!
    assert not artifact_core.is_ignored_path(plan_path, target)

    # untracked prompt SHOULD still be ignored
    assert artifact_core.is_ignored_path(untracked_prompt, target)


def test_home_records_find_attention_check(home_records_env):
    target, home, aw_home = home_records_env

    # 1. Create a backlog item
    res = run_aw(
        [
            "backlog",
            "new",
            "--summary",
            "item1",
            "--work-kind",
            "bug",
            "--priority",
            "high",
            "--slug",
            "item1",
            "--apply",
            "--dir",
            str(target),
        ],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert res.returncode == 0, f"backlog new failed: {res.stdout}\n{res.stderr}"

    # 2. Create a plan under the external records dir
    projects_dir = aw_home / "projects"
    rec_dirs = list(projects_dir.glob("*/records"))
    assert len(rec_dirs) == 1
    ext_rec = rec_dirs[0]
    pending_dir = ext_rec / "plans" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    plan_content = """# IPD 20261015-test-01-abcdef-my-plan

- Id: abcdef
- Set: test (Test)
- Order: 01
- Kind: child
- Status: pending

## Summary
Test plan.
"""
    plan_file = pending_dir / "20261015-test-01-abcdef-my-plan.ipd.md"
    plan_file.write_text(plan_content, encoding="utf-8")

    # 3. Verify git status of target has no records files
    git_st = subprocess.run(
        ["git", "status", "--porcelain", "--ignored"],
        cwd=target,
        check=True,
        capture_output=True,
        text=True,
    )
    for line in git_st.stdout.splitlines():
        rel = line[3:].strip()
        assert not rel.startswith(".aw/records"), f"Found in git status: {line}"
        assert not rel.startswith(".agents"), f"Found in git status: {line}"

    # 4. Run `aw find all --json`
    res_find = run_aw(
        ["find", "all", "--json", "--dir", str(target)],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res_find.returncode == 0
    ), f"find failed: {res_find.stdout}\n{res_find.stderr}"
    find_data = json.loads(res_find.stdout)
    all_paths = find_data.get("data", {}).get("paths", [])
    assert any(
        "abcdef" in p for p in all_paths
    ), f"Plan abcdef not found in {all_paths}"
    assert any(
        "item1" in p for p in all_paths
    ), f"Backlog item1 not found in {all_paths}"

    # 5. Run `aw attention --format json`
    res_att = run_aw(
        ["attention", "--format", "json", "--dir", str(target)],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res_att.returncode == 0
    ), f"attention failed: {res_att.stdout}\n{res_att.stderr}"
    att_data = json.loads(res_att.stdout)
    att_ids = [it.get("id") for it in att_data.get("items", [])]
    assert "abcdef" in att_ids, f"abcdef not in attention items: {att_ids}"

    # No uninventoried-tree
    violations = att_data.get("violations", [])
    uninventoried = [
        v for v in violations if v.get("rule") == "attention.uninventoried-tree"
    ]
    assert not uninventoried, f"Found uninventoried-tree: {uninventoried}"

    # 6. Run `aw check all`
    res_check = run_aw(
        ["check", "all", "--dir", str(target)],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert "attention.uninventoried-tree" not in res_check.stdout
    assert "missing-tree" not in res_check.stdout


def test_home_records_runner_discovery(home_records_env):
    target, home, aw_home = home_records_env

    # Write a conforming plan into the external records dir
    ext_rec = project_context.project_records_dir(target, aw_home=aw_home)
    pending_dir = ext_rec / "plans" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)

    real_plan = (
        REPO_ROOT
        / ".aw/records/plans/pending/20261015-cleantgt-01-kfnfji-route-every-records-reader-and-writer-through-one-records-ro.ipd.md"
    ).read_text(encoding="utf-8")
    plan_file = (
        pending_dir
        / "20261015-cleantgt-01-kfnfji-route-every-records-reader-and-writer-through-one-records-ro.ipd.md"
    )
    plan_file.write_text(real_plan, encoding="utf-8")

    # 1. aw show kfnfji
    res_show = run_aw(
        ["show", "kfnfji", "--dir", str(target)],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res_show.returncode == 0
    ), f"show failed: {res_show.stdout}\n{res_show.stderr}"
    assert "20261015-cleantgt-01-kfnfji" in res_show.stdout

    # 2. aw oc run start --prepare-only kfnfji
    res_prep = run_aw(
        ["oc", "run", "start", "--prepare-only", "kfnfji"],
        cwd=target,
        home=home,
        aw_home=aw_home,
    )
    assert (
        res_prep.returncode == 0
    ), f"prepare-only failed: {res_prep.stdout}\n{res_prep.stderr}"
    assert "Run order (1 item(s)): 01 kfnfji" in res_prep.stdout
    assert "cleantgt 01 kfnfji" in res_prep.stdout

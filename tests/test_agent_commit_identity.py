"""Tests for agent committer identity and runner trailers (IPD yr3d4o).

Drives real git in ``tmp_path`` repositories and asserts on ``git log`` output,
child environment variables, and signing invocations. Never reads source text.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import agy_runipd
from agent_workflows import cli
from agent_workflows import commit_lock
from agent_workflows import coverage_record
from agent_workflows import engine
from agent_workflows import git_commit_helper as _gch
from agent_workflows import ipd_lifecycle
from agent_workflows import oc_runipd
from agent_workflows import runner_shared
from agent_workflows import worktree_lease

_SCRUB_KEYS = (
    "GIT_AUTHOR_NAME",
    "GIT_AUTHOR_EMAIL",
    "GIT_COMMITTER_NAME",
    "GIT_COMMITTER_EMAIL",
    "GIT_CONFIG_COUNT",
    "AW_RUN_ID",
    "AW_ITEM_ID6",
    "AW_RUNNER",
    "AW_AGENT_MODEL",
    "AW_EXECUTION_ROLE",
)


@pytest.fixture(autouse=True)
def _clean_identity_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Scrub inherited GIT_AUTHOR_*, GIT_COMMITTER_*, and AW_* vars for each test."""
    for key in list(os.environ):
        if (
            key in _SCRUB_KEYS
            or key.startswith("GIT_CONFIG_KEY_")
            or key.startswith("GIT_CONFIG_VALUE_")
        ):
            monkeypatch.delenv(key, raising=False)


def _init_git_repo(
    path: Path,
    *,
    name: str = "Jane Dev",
    email: str = "jane@example.com",
) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "--local", "user.name", name],
        cwd=path,
        check=True,
        capture_output=True,
    )
    if email:
        subprocess.run(
            ["git", "config", "--local", "user.email", email],
            cwd=path,
            check=True,
            capture_output=True,
        )
    seed = path / "README.md"
    seed.write_text("# Seed\n", encoding="utf-8")
    (path / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md", ".gitignore"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    return path


def _head_ident_and_trailers(repo: Path, rev: str = "HEAD") -> tuple[str, str]:
    ident_proc = subprocess.run(
        ["git", "log", "-1", "--format=%an <%ae> | %cn <%ce>", rev],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    trailers_proc = subprocess.run(
        ["git", "log", "-1", "--format=%(trailers)", rev],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return ident_proc.stdout.strip(), trailers_proc.stdout.strip()


def _write_minimal_approved_plan(
    repo: Path,
    *,
    id6: str = "abc123",
    setid: str = "demoset",
    scope_paths: str = "src/app.py",
    kind: str = "child",
) -> Path:
    from tests import support

    plan_dir = repo / ".aw" / "records" / "plans" / "pending"
    exec_dir = repo / ".aw" / "records" / "plans" / "executed"
    plan_dir.mkdir(parents=True, exist_ok=True)
    exec_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / f"20261012-{setid}-01-{id6}-demo-plan.ipd.md"
    t = support.ready_plan_text(
        plan_id=id6,
        kind=kind,
        set_name=setid,
        scope_paths=scope_paths,
    )
    t = t.replace("- [ ] E-01 ", "- [x] E-01 ", 1).replace(
        "  - Execution state: pending", "  - Execution state: performed", 1
    )
    t = (
        t.replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
        .replace(
            "  - Observed evidence:\n", "  - Observed evidence: done, verified.\n", 1
        )
        .replace("  - Result: pending", "  - Result: pass", 1)
    )
    plan_path.write_text(t, encoding="utf-8")
    return plan_path


def test_a_helper_mapping_table(tmp_path: Path) -> None:
    """Case (a): helper mapping table across email tags, model sanitizing, unknown model/runner."""
    repo_plain = _init_git_repo(tmp_path / "plain", name="Jane Dev", email="a@b.com")
    r1 = _gch.agent_commit_identity(
        repo_plain,
        model="Gemini 3.8 Flash (High)\n<v2>",
        runner="aw oc run",
        run_id="run-20261012T010203Z-99",
        item_id6="abc123",
        message="feat: demo",
        base_env={},
    )
    assert r1.committer_name == "AW Agent (Gemini 3.8 Flash High v2)"
    assert r1.committer_email == "a+aw@b.com"
    assert r1.env["GIT_COMMITTER_NAME"] == "AW Agent (Gemini 3.8 Flash High v2)"
    assert r1.env["GIT_COMMITTER_EMAIL"] == "a+aw@b.com"
    assert "GIT_AUTHOR_NAME" not in r1.env
    assert "GIT_AUTHOR_EMAIL" not in r1.env
    assert r1.trailers == (
        "AW-Runner: aw oc run",
        "AW-Run: run-20261012T010203Z-99",
        "AW-Item: abc123",
    )

    # Already-tagged address appends -aw rather than a second +
    repo_tagged = _init_git_repo(
        tmp_path / "tagged", name="Jane Dev", email="a+dev@b.com"
    )
    r2 = _gch.agent_commit_identity(
        repo_tagged,
        model=None,
        runner="bogus-runner",
        message="feat: tagged",
        base_env={},
    )
    assert r2.committer_name == "AW Agent (unknown)"
    assert r2.committer_email == "a+dev-aw@b.com"
    assert r2.runner is None
    assert r2.trailers == ()
    assert r2.message == "feat: tagged"

    # Idempotent when email already ends with +aw or -aw
    assert _gch.tag_agent_email("a+aw@b.com") == "a+aw@b.com"
    assert _gch.tag_agent_email("a+dev-aw@b.com") == "a+dev-aw@b.com"
    assert _gch.tag_agent_email("not-an-email") == ""
    assert _gch.tag_agent_email("") == ""

    # GIT_AUTHOR_EMAIL in base_env overrides repo config
    r3 = _gch.agent_commit_identity(
        repo_plain,
        base_env={
            "GIT_AUTHOR_EMAIL": "override@domain.org",
            "AW_AGENT_MODEL": "claude-opus-4-6",
            "AW_RUNNER": "aw agy run",
        },
        message="msg",
    )
    assert r3.committer_name == "AW Agent (claude-opus-4-6)"
    assert r3.committer_email == "override+aw@domain.org"
    assert r3.runner == "aw agy run"
    assert r3.trailers == ("AW-Runner: aw agy run",)


def test_b_aw_commit_through_cli_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Case (b): aw commit through cli.main yields author=user, committer=AW Agent (<model>) <user+aw@...>, AW-Runner: aw commit."""
    repo = _init_git_repo(tmp_path / "repo", name="Jane Dev", email="jane@example.com")
    target = repo / "hello.txt"
    target.write_text("hello world\n", encoding="utf-8")

    monkeypatch.chdir(repo)
    monkeypatch.setenv("AW_AGENT_MODEL", "claude-opus-4-6")

    rc = cli.main(["commit", "--no-plan", "-m", "work: add hello", "--", "hello.txt"])
    assert rc == 0

    ident, trailers = _head_ident_and_trailers(repo)
    assert (
        ident
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    assert "AW-Runner: aw commit" in trailers.splitlines()


def test_c_finalize_through_ipd_lifecycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Case (c): ipd_lifecycle.finalize yields agent committer; honors AW_RUNNER when set and omits it when unset."""
    monkeypatch.delenv("AW_EXECUTION_ROLE", raising=False)
    # 1. Without AW_RUNNER in env: committer is AW Agent (<model>), no AW-Runner trailer
    repo1 = _init_git_repo(
        tmp_path / "repo1", name="Jane Dev", email="jane@example.com"
    )
    (repo1 / "src").mkdir(parents=True, exist_ok=True)
    app1 = repo1 / "src" / "app.py"
    app1.write_text("x = 1\n", encoding="utf-8")
    plan1 = _write_minimal_approved_plan(repo1, id6="abc123", scope_paths="src/app.py")
    subprocess.run(
        ["git", "add", "src/app.py", str(plan1.relative_to(repo1))],
        cwd=repo1,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "seed plan and app"],
        cwd=repo1,
        check=True,
        capture_output=True,
    )

    b_res1 = ipd_lifecycle.begin(
        repo1, plan1, "opencode/claude-opus-4-6", timestamp="2026-10-12 01:00"
    )
    assert b_res1.exit_code == 0
    app1.write_text("x = 2\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "src/app.py"], cwd=repo1, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "work(abc123): update app"],
        cwd=repo1,
        check=True,
        capture_output=True,
    )

    f_res1 = ipd_lifecycle.finalize(
        repo1,
        plan1,
        "opencode/claude-opus-4-6",
        "completed demo",
        apply=True,
        env={},
    )
    assert f_res1.exit_code == 0, f_res1.message

    ident1, trailers1 = _head_ident_and_trailers(repo1)
    assert (
        ident1
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    assert "AW-Runner:" not in trailers1
    assert "AW-Item: abc123" in trailers1.splitlines()

    # 2. With AW_RUNNER=aw oc run (as driver_finalize sets): carries AW-Runner: aw oc run
    repo2 = _init_git_repo(
        tmp_path / "repo2", name="Jane Dev", email="jane@example.com"
    )
    (repo2 / "src").mkdir(parents=True, exist_ok=True)
    app2 = repo2 / "src" / "app.py"
    app2.write_text("x = 1\n", encoding="utf-8")
    plan2 = _write_minimal_approved_plan(repo2, id6="def456", scope_paths="src/app.py")
    subprocess.run(
        ["git", "add", "src/app.py", str(plan2.relative_to(repo2))],
        cwd=repo2,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "seed plan and app"],
        cwd=repo2,
        check=True,
        capture_output=True,
    )

    b_res2 = ipd_lifecycle.begin(
        repo2, plan2, "opencode/claude-opus-4-6", timestamp="2026-10-12 01:00"
    )
    assert b_res2.exit_code == 0
    app2.write_text("x = 2\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "src/app.py"], cwd=repo2, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "work(def456): update app"],
        cwd=repo2,
        check=True,
        capture_output=True,
    )

    f_res2 = ipd_lifecycle.finalize(
        repo2,
        plan2,
        "aw oc run model=claude-opus-4-6",
        "completed demo",
        apply=True,
        run_id="run-20261012T020000Z-77",
        env={"AW_RUNNER": "aw oc run", "AW_AGENT_MODEL": "claude-opus-4-6"},
    )
    assert f_res2.exit_code == 0, f_res2.message

    ident2, trailers2 = _head_ident_and_trailers(repo2)
    assert (
        ident2
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    assert "AW-Runner: aw oc run" in trailers2.splitlines()
    assert "AW-Run: run-20261012T020000Z-77" in trailers2.splitlines()
    assert "AW-Item: def456" in trailers2.splitlines()


def test_d_integrate_lane_branch_non_ff_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Case (d): runner_shared.integrate_lane_branch non-ff merge yields agent committer and trailers."""
    repo = _init_git_repo(tmp_path / "repo", name="Jane Dev", email="jane@example.com")
    monkeypatch.setenv("AW_AGENT_MODEL", "claude-opus-4-6")

    handle = worktree_lease.allocate_worktree(repo, "abc123")
    lane_file = handle.path / "lane.txt"
    lane_file.write_text("lane work\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "lane.txt"], cwd=handle.path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "lane work"],
        cwd=handle.path,
        check=True,
        capture_output=True,
    )

    # Advance main past handle.base_commit so --ff-only fails and --no-ff runs
    main_file = repo / "main_advance.txt"
    main_file.write_text("main advanced\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "main_advance.txt"], cwd=repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "main advance"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    run_dir = repo / ".aw" / "records" / "runs" / "run-20261012T030000Z-55"
    run_dir.mkdir(parents=True, exist_ok=True)

    def _run_checked(cmd: list[str], cwd: Path | None = None) -> str:
        proc = subprocess.run(
            cmd, cwd=cwd or repo, check=True, capture_output=True, text=True
        )
        return proc.stdout

    ok, reason, kind = runner_shared.integrate_lane_branch(
        repo,
        handle,
        "abc123",
        lambda _diff, _files: True,
        host_label="aw oc run",
        run_checked=_run_checked,
        action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
        run_dir=run_dir,
    )
    assert ok is True, reason
    assert kind == "integrated"
    assert "controlled non-ff merge" in reason

    ident, trailers = _head_ident_and_trailers(repo)
    assert (
        ident
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    assert "AW-Runner: aw oc run" in trailers.splitlines()
    assert "AW-Run: run-20261012T030000Z-55" in trailers.splitlines()
    assert "AW-Item: abc123" in trailers.splitlines()


def test_e_runner_agent_child_envs_and_scripted_lane_commit(tmp_path: Path) -> None:
    """Case (e): oc and agy child envs contain committer vars, AW_AGENT_MODEL, AW_RUNNER, and a lane git commit gets them."""
    repo = _init_git_repo(tmp_path / "repo", name="Jane Dev", email="jane@example.com")
    lane = _init_git_repo(tmp_path / "lane", name="Jane Dev", email="jane@example.com")
    run_dir = repo / ".aw" / "records" / "runs" / "run-20261012T040000Z-11"
    (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
    prompt_path = repo / "prompt.md"
    prompt_path.write_text("do work", encoding="utf-8")
    plan_path = repo / "plan.ipd.md"
    plan_path.write_text("# IPD: demo\n", encoding="utf-8")
    item = {"position": 1, "id6": "abc123", "setid": "demo"}

    state_oc = {
        "run_id": "run-20261012T040000Z-11",
        "options": {
            "opencode": "opencode",
            "model": "claude-opus-4-6",
            "stall_timeout": 10.0,
            "timeout": 10.0,
        },
        "repo": str(repo),
        "queue": [],
    }

    with mock.patch(
        "agent_workflows.oc_runipd.observe_opencode_policy", return_value="observed"
    ), mock.patch("agent_workflows.lane_containment.record_host_posture"), mock.patch(
        "subprocess.Popen"
    ) as mock_popen_oc:
        mock_popen_oc.return_value.poll.return_value = 0
        mock_popen_oc.return_value.returncode = 0
        mock_popen_oc.return_value.stdout = io_empty = mock.MagicMock()
        mock_popen_oc.return_value.stderr = mock.MagicMock()
        io_empty.readline.return_value = ""

        oc_runipd.run_opencode(
            state=state_oc,
            run_dir=run_dir,
            item=item,
            plan_path=plan_path,
            prompt_path=prompt_path,
            attempt_no=1,
            work_dir=str(lane),
        )
        oc_env = mock_popen_oc.call_args[1]["env"]

    assert oc_env["GIT_COMMITTER_NAME"] == "AW Agent (claude-opus-4-6)"
    assert oc_env["GIT_COMMITTER_EMAIL"] == "jane+aw@example.com"
    assert oc_env["AW_AGENT_MODEL"] == "claude-opus-4-6"
    assert oc_env["AW_RUNNER"] == "aw oc run"
    assert oc_env["AW_RUN_ID"] == "run-20261012T040000Z-11"
    assert oc_env["AW_ITEM_ID6"] == "abc123"

    dummy_agy = repo / ("dummy_agy.cmd" if sys.platform == "win32" else "dummy_agy")
    dummy_agy.write_text("")
    dummy_agy.chmod(0o755)

    state_agy = {
        "run_id": "run-20261012T040000Z-11",
        "options": {
            "agy_executable": str(dummy_agy),
            "model": "gemini-2.5-pro",
            "stall_timeout": 10.0,
            "timeout": 10.0,
        },
        "repo": str(repo),
        "queue": [],
    }
    with mock.patch("agent_workflows.lane_containment.record_host_posture"), mock.patch(
        "subprocess.Popen"
    ) as mock_popen_agy:
        mock_popen_agy.return_value.poll.return_value = 0
        mock_popen_agy.return_value.returncode = 0
        mock_popen_agy.return_value.stdout = mock.MagicMock()
        mock_popen_agy.return_value.stderr = mock.MagicMock()

        agy_runipd.run_agy_turn(
            state=state_agy,
            run_dir=run_dir,
            item=item,
            prompt_path=prompt_path,
            attempt_no=1,
            session_id=None,
            use_continue=False,
            work_dir=str(lane),
        )
        agy_env = mock_popen_agy.call_args[1]["env"]

    assert agy_env["GIT_COMMITTER_NAME"] == "AW Agent (gemini-2.5-pro)"
    assert agy_env["GIT_COMMITTER_EMAIL"] == "jane+aw@example.com"
    assert agy_env["AW_AGENT_MODEL"] == "gemini-2.5-pro"
    assert agy_env["AW_RUNNER"] == "aw agy run"

    # Scripted agent commit inside the lane using the exported child_env:
    # 1) Plain git commit inside the lane gets the agent committer automatically
    (lane / "plain_agent.txt").write_text("by agent raw git\n", encoding="utf-8")
    subprocess.run(["git", "add", "plain_agent.txt"], cwd=lane, env=oc_env, check=True)
    subprocess.run(
        ["git", "commit", "-m", "raw git commit in lane"],
        cwd=lane,
        env=oc_env,
        check=True,
    )
    ident_raw, _ = _head_ident_and_trailers(lane)
    assert (
        ident_raw
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )

    # 2) aw commit inside the lane gets agent committer + AW-Runner: aw oc run + AW-Run + AW-Item
    (lane / "aw_agent.txt").write_text("by agent aw commit\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "commit",
            "--no-plan",
            "-m",
            "agent aw commit in lane",
            "--",
            "aw_agent.txt",
        ],
        cwd=lane,
        env=oc_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    ident_aw, trailers_aw = _head_ident_and_trailers(lane)
    assert (
        ident_aw
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    assert "AW-Runner: aw oc run" in trailers_aw.splitlines()
    assert "AW-Run: run-20261012T040000Z-11" in trailers_aw.splitlines()
    assert "AW-Item: abc123" in trailers_aw.splitlines()


def test_f_plain_git_commit_outside_aw_keeps_user_committer(tmp_path: Path) -> None:
    """Case (f): plain git commit in the same repo after aw commit keeps author=committer=user."""
    repo = _init_git_repo(tmp_path / "repo", name="Jane Dev", email="jane@example.com")
    f1 = repo / "via_aw.txt"
    f1.write_text("aw\n", encoding="utf-8")
    out = _gch.offer_commit(
        repo,
        ["via_aw.txt"],
        message="via aw",
        assume_yes=True,
        model="claude-opus-4-6",
        runner="aw commit",
    )
    assert out.status == _gch.STATUS_COMMITTED

    # Now make a plain git commit in the same repo
    f2 = repo / "by_user.txt"
    f2.write_text("human\n", encoding="utf-8")
    subprocess.run(["git", "add", "by_user.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "human commit"], cwd=repo, check=True)

    ident, trailers = _head_ident_and_trailers(repo)
    assert ident == "Jane Dev <jane@example.com> | Jane Dev <jane@example.com>"
    assert trailers == ""


def test_g_missing_user_email_sets_no_committer_override(tmp_path: Path) -> None:
    """Case (g): when no user.email is configured, aw sets no committer override."""
    repo = tmp_path / "no_email"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "--local", "user.name", "No Email User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    isolated_env = {
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": os.environ.get("PATH", ""),
    }
    ident = _gch.agent_commit_identity(
        repo,
        model="claude-opus-4-6",
        runner="aw commit",
        message="msg",
        base_env=isolated_env,
    )
    assert ident.committer_email == ""
    assert ident.committer_name == ""
    assert "GIT_COMMITTER_NAME" not in ident.env
    assert "GIT_COMMITTER_EMAIL" not in ident.env


def test_h_gpgsign_without_signingkey_passes_user_ident_to_gpg(tmp_path: Path) -> None:
    """Case (h): with commit.gpgsign=true and no user.signingkey, gpg receives the user's ident, not the agent's."""
    repo = _init_git_repo(
        tmp_path / "gpg_repo", name="Jane Dev", email="jane@example.com"
    )
    gpg_log = tmp_path / "gpg_args.log"
    fake_gpg = tmp_path / "fake_gpg.sh"
    fake_gpg.write_text(
        f"""#!/bin/sh
printf '%s\\n' "$@" > "{gpg_log}"
cat >/dev/null
printf '[GNUPG:] SIG_CREATED D 1 8 00 1700000000 0000000000000000000000000000000000000000\\n' >&2
printf -- '-----BEGIN PGP SIGNATURE-----\\n\\nfakesig\\n-----END PGP SIGNATURE-----\\n'
exit 0
""",
        encoding="utf-8",
    )
    fake_gpg.chmod(fake_gpg.stat().st_mode | stat.S_IEXEC)

    subprocess.run(
        ["git", "config", "--local", "commit.gpgsign", "true"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "--local", "gpg.program", str(fake_gpg)],
        cwd=repo,
        check=True,
    )

    (repo / "signed.txt").write_text("signed content\n", encoding="utf-8")
    out = _gch.offer_commit(
        repo,
        ["signed.txt"],
        message="signed via aw",
        assume_yes=True,
        model="claude-opus-4-6",
        runner="aw commit",
    )
    assert out.status == _gch.STATUS_COMMITTED, out.message

    logged_args = gpg_log.read_text(encoding="utf-8").splitlines()
    assert "Jane Dev <jane@example.com>" in logged_args
    assert not any("+aw" in arg or "AW Agent" in arg for arg in logged_args)

    ident, trailers = _head_ident_and_trailers(repo)
    assert (
        ident
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    assert "AW-Runner: aw commit" in trailers.splitlines()


def test_i_no_double_trailers_on_driver_and_remaining_call_sites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Case (i) + remaining E-03 / E-07 call sites: no duplicate trailers and agent committer everywhere."""
    monkeypatch.setenv("AW_AGENT_MODEL", "claude-opus-4-6")

    # 1. runner_shared.commit_review_lane_output (already stamps AW-Run / AW-Item)
    repo = _init_git_repo(
        tmp_path / "review_repo", name="Jane Dev", email="jane@example.com"
    )
    plan = _write_minimal_approved_plan(repo, id6="abc123")
    subprocess.run(["git", "add", str(plan.relative_to(repo))], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add plan"], cwd=repo, check=True)

    handle = worktree_lease.allocate_worktree(repo, "abc123")
    lane_plan = handle.path / plan.relative_to(repo)
    lane_plan.write_text(
        lane_plan.read_text(encoding="utf-8") + "\n<!-- reviewed -->\n",
        encoding="utf-8",
    )

    sha, scope = runner_shared.commit_review_lane_output(
        repo,
        handle,
        "abc123",
        host_label="aw oc run",
        run_id="run-20261012T050000Z-12",
    )
    assert sha is not None
    ident, trailers = _head_ident_and_trailers(handle.path)
    assert (
        ident
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    trailer_lines = trailers.splitlines()
    assert trailer_lines.count("AW-Runner: aw oc run") == 1
    assert trailer_lines.count("AW-Run: run-20261012T050000Z-12") == 1
    assert trailer_lines.count("AW-Item: abc123") == 1
    assert trailer_lines.count("AW-Committed-By: driver") == 1

    # 2. runner_shared.commit_spec_production_output (sibling commit_*_output)
    new_plan = _write_minimal_approved_plan(handle.path, id6="new123")
    assert new_plan.is_file()
    spec_sha, _, _ = runner_shared.commit_spec_production_output(
        handle.path,
        "spc123",
        {"abc123"},
        host_label="aw agy run",
        run_id="run-20261012T050000Z-12",
    )
    assert spec_sha is not None
    ident_spec, trailers_spec = _head_ident_and_trailers(handle.path)
    assert (
        ident_spec
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    assert trailers_spec.splitlines().count("AW-Runner: aw agy run") == 1
    assert trailers_spec.splitlines().count("AW-Run: run-20261012T050000Z-12") == 1
    assert trailers_spec.splitlines().count("AW-Item: spc123") == 1

    # 3. runner_shared.prepare_lane_for_conflict_resolution (clean merge of main into lane)
    (repo / "main_new.txt").write_text("from main\n", encoding="utf-8")
    subprocess.run(["git", "add", "main_new.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "advance main"], cwd=repo, check=True)
    prep = runner_shared.prepare_lane_for_conflict_resolution(
        repo,
        handle,
        host_label="aw oc run",
        run_id="run-20261012T050000Z-12",
    )
    assert prep.ok is True
    assert prep.conflicted_paths == ()
    ident_prep, trailers_prep = _head_ident_and_trailers(handle.path)
    assert (
        ident_prep
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    assert "AW-Runner: aw oc run" in trailers_prep.splitlines()
    assert "AW-Run: run-20261012T050000Z-12" in trailers_prep.splitlines()
    assert "AW-Item: abc123" in trailers_prep.splitlines()

    # 4. worktree_lease.snapshot_lane_dirty_work (commit-tree on lane branch)
    (handle.path / "dirty_work.txt").write_text("uncommitted work\n", encoding="utf-8")
    snap_sha = worktree_lease.snapshot_lane_dirty_work(
        repo,
        handle,
        note="Reason: test_snapshot.",
        runner="aw oc run",
        model="claude-opus-4-6",
        run_id="run-20261012T050000Z-12",
        item_id6="abc123",
    )
    assert snap_sha is not None
    ident_snap, trailers_snap = _head_ident_and_trailers(handle.path, rev=snap_sha)
    assert (
        ident_snap
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    assert "AW-Runner: aw oc run" in trailers_snap.splitlines()
    assert "AW-Run: run-20261012T050000Z-12" in trailers_snap.splitlines()
    assert "AW-Item: abc123" in trailers_snap.splitlines()

    # 5. coverage_record.write (E-03)
    cov_repo = _init_git_repo(
        tmp_path / "cov_repo", name="Jane Dev", email="jane@example.com"
    )
    orch_plan = _write_minimal_approved_plan(
        cov_repo, id6="orc123", kind="orchestrator"
    )
    subprocess.run(
        ["git", "add", str(orch_plan.relative_to(cov_repo))],
        cwd=cov_repo,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "add orchestrator"], cwd=cov_repo, check=True
    )
    cov_res = coverage_record.write(
        orch_plan,
        verdict="pass",
        model="claude-opus-4-6",
        tool="aw ipd coverage",
        commit=True,
        repo=cov_repo,
    )
    assert cov_res.committed is True, cov_res.detail
    ident_cov, trailers_cov = _head_ident_and_trailers(cov_repo)
    assert (
        ident_cov
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    assert "AW-Item: orc123" in trailers_cov.splitlines()

    # 6. engine._commit_paths and engine.prompt_and_run_commit (E-03)
    eng_repo = _init_git_repo(
        tmp_path / "eng_repo", name="Jane Dev", email="jane@example.com"
    )
    (eng_repo / "inst.txt").write_text("installed\n", encoding="utf-8")
    subprocess.run(["git", "add", "inst.txt"], cwd=eng_repo, check=True)
    assert engine._commit_paths(eng_repo, ["inst.txt"], message="engine commit") is True
    ident_eng, _ = _head_ident_and_trailers(eng_repo)
    assert (
        ident_eng
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )

    (eng_repo / "inst2.txt").write_text("installed 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "inst2.txt"], cwd=eng_repo, check=True)
    plan_stub = mock.MagicMock(
        dry_run=False, no_color=True, repo_root=eng_repo, yes=True
    )
    engine.prompt_and_run_commit(plan_stub, ["inst2.txt [install]"], [], {}, "", True)
    ident_eng2, _ = _head_ident_and_trailers(eng_repo)
    assert (
        ident_eng2
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )

    # 7. cli._offer_commit_uninstall (E-03)
    subprocess.run(["git", "rm", "-q", "inst.txt"], cwd=eng_repo, check=True)
    term_stub = mock.MagicMock()
    cli._offer_commit_uninstall(
        term_stub,
        eng_repo,
        True,
        ["inst.txt"],
        True,
    )
    ident_uninst, _ = _head_ident_and_trailers(eng_repo)
    assert (
        ident_uninst
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )

    # 8. commit_lock.commit_isolated directly (E-03)
    (eng_repo / "iso.txt").write_text("isolated\n", encoding="utf-8")
    subprocess.run(["git", "add", "iso.txt"], cwd=eng_repo, check=True)
    iso_res = commit_lock.commit_isolated(
        eng_repo,
        ["iso.txt"],
        message="isolated commit",
        model="claude-opus-4-6",
        runner="aw commit",
    )
    assert iso_res.status == commit_lock.ISO_COMMITTED
    ident_iso, trailers_iso = _head_ident_and_trailers(eng_repo)
    assert (
        ident_iso
        == "Jane Dev <jane@example.com> | AW Agent (claude-opus-4-6) <jane+aw@example.com>"
    )
    assert "AW-Runner: aw commit" in trailers_iso.splitlines()

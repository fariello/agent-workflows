"""Tests for CLI checkout-mismatch detector and re-execution (IPD `wj5b53`, bug `lcmz33`).

Guards:
- Mismatch detection in checkouts of this toolkit with automatic re-exec via `-m agent_workflows`.
- Subdirectory walk-up and `.git` file (worktree) support.
- Loop guard (`AW_REEXEC_FROM`) and opt-out (`AW_NO_REEXEC=1`).
- Silent passthrough for target repos (no `agent_workflows/` package).
- Silent passthrough for driver-pinned children (`AW_PINNED_CHILD=1`).
- Scoping of `AW_PINNED_CHILD` (consumed via `os.environ.pop` so descendants do not inherit).
- Silent passthrough for shell-completion requests (`aw __complete` and `COMP_LINE` / `_ARGCOMPLETE`).
- Bare `agent_workflows/` directories without `__init__.py` do not qualify as toolkit checkouts.
- Notice survives piped stderr (explicit buffer flush before `os.execve`).
"""

from __future__ import annotations

import os
import subprocess
import sys
import pytest
import textwrap
from pathlib import Path

from agent_workflows import cli, runner_shared

REPO_ROOT = str(Path(__file__).resolve().parent.parent)
REPO_ROOT_REAL = os.path.realpath(REPO_ROOT)


def _clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "AW_PINNED_CHILD",
        "AW_REEXEC_FROM",
        "AW_NO_REEXEC",
        "COMP_LINE",
        "_ARGCOMPLETE",
        "PYTHONPATH",
    ):
        env.pop(key, None)
    if extra:
        env.update(extra)
    return env


def _make_fake_checkout(base: Path, git_is_file: bool = False) -> Path:
    fake = base / ("fake_file" if git_is_file else "fake")
    fake.mkdir(parents=True, exist_ok=True)
    if git_is_file:
        (fake / ".git").write_text("gitdir: /somewhere/else\n", encoding="utf-8")
    else:
        (fake / ".git").mkdir(parents=True, exist_ok=True)
    pkg = fake / "agent_workflows"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text('MARKER = "FAKE"\n', encoding="utf-8")
    (pkg / "__main__.py").write_text(
        textwrap.dedent(
            """
            import os, sys
            print("FAKE-RAN", os.environ.get("AW_REEXEC_FROM", "NONE"))
            sys.exit(0)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return fake


def _run_launcher(
    cwd: Path | str,
    args: list[str] | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable]
    if sys.version_info >= (3, 11):
        cmd.append("-P")
    cmd.extend(
        [
            "-c",
            f"import sys; sys.path.insert(0, {REPO_ROOT!r}); from agent_workflows.cli import main; sys.exit(main())",
        ]
    )
    if args:
        cmd.extend(args)
    else:
        cmd.append("--version")

    env = _clean_env(extra_env)
    return subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)


def test_01_mismatch_cwd_fake_reexecs(tmp_path: Path) -> None:
    fake = _make_fake_checkout(tmp_path)
    proc = _run_launcher(fake)
    assert proc.returncode == 0
    assert "FAKE-RAN" in proc.stdout
    assert f"FAKE-RAN {REPO_ROOT_REAL}" in proc.stdout
    assert "aw: invoked in checkout" in proc.stderr
    assert os.path.realpath(fake) in proc.stderr
    assert REPO_ROOT_REAL in proc.stderr


def test_02_mismatch_cwd_subdir_reexecs(tmp_path: Path) -> None:
    fake = _make_fake_checkout(tmp_path)
    subdir = fake / "sub" / "dir"
    subdir.mkdir(parents=True, exist_ok=True)
    proc = _run_launcher(subdir)
    assert proc.returncode == 0
    assert "FAKE-RAN" in proc.stdout
    assert f"FAKE-RAN {REPO_ROOT_REAL}" in proc.stdout
    assert "aw: invoked in checkout" in proc.stderr
    assert os.path.realpath(fake) in proc.stderr
    assert REPO_ROOT_REAL in proc.stderr


def test_03_mismatch_git_file_reexecs(tmp_path: Path) -> None:
    fake = _make_fake_checkout(tmp_path, git_is_file=True)
    proc = _run_launcher(fake)
    assert proc.returncode == 0
    assert "FAKE-RAN" in proc.stdout
    assert f"FAKE-RAN {REPO_ROOT_REAL}" in proc.stdout
    assert "aw: invoked in checkout" in proc.stderr
    assert os.path.realpath(fake) in proc.stderr
    assert REPO_ROOT_REAL in proc.stderr


def test_04_loop_guard_preset_reexec_from_runs_real_cli(tmp_path: Path) -> None:
    fake = _make_fake_checkout(tmp_path)
    proc = _run_launcher(fake, extra_env={"AW_REEXEC_FROM": "preset_val"})
    assert proc.returncode == 0
    assert "agent-workflows" in proc.stdout
    assert "FAKE-RAN" not in proc.stdout
    assert "still importing" in proc.stderr
    assert "after re-exec; continuing" in proc.stderr
    assert os.path.realpath(fake) in proc.stderr
    assert REPO_ROOT_REAL in proc.stderr


def test_05_opt_out_aw_no_reexec_runs_real_cli(tmp_path: Path) -> None:
    fake = _make_fake_checkout(tmp_path)
    proc = _run_launcher(fake, extra_env={"AW_NO_REEXEC": "1"})
    assert proc.returncode == 0
    assert "agent-workflows" in proc.stdout
    assert "FAKE-RAN" not in proc.stdout
    assert "AW_NO_REEXEC" in proc.stderr
    assert "(AW_NO_REEXEC set; not re-running)" in proc.stderr
    assert os.path.realpath(fake) in proc.stderr
    assert REPO_ROOT_REAL in proc.stderr


def test_06_target_repo_no_agent_workflows_runs_real_cli_silent(tmp_path: Path) -> None:
    target = tmp_path / "target"
    (target / ".git").mkdir(parents=True, exist_ok=True)
    proc = _run_launcher(target)
    assert proc.returncode == 0
    assert "agent-workflows" in proc.stdout
    assert "FAKE-RAN" not in proc.stdout
    assert proc.stderr == ""


def test_07_pinned_child_runs_real_cli_silent(tmp_path: Path) -> None:
    fake = _make_fake_checkout(tmp_path)
    cmd = runner_shared.pinned_module_argv(["--version"])
    env = runner_shared.pinned_child_env(_clean_env())
    proc = subprocess.run(cmd, cwd=str(fake), env=env, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "agent-workflows" in proc.stdout
    assert "FAKE-RAN" not in proc.stdout
    assert proc.stderr == ""


def _pre_marker_bootstrap() -> str:
    """The `_AW_PIN_BOOTSTRAP` a driver started BEFORE `wj5b53` landed still runs: no marker line."""
    return runner_shared._AW_PIN_BOOTSTRAP.replace(
        "os.environ['AW_PINNED_CHILD']='1'\n", ""
    )


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="child-side bootstrap recognition reads sys.orig_argv (3.10+); on 3.9 only the "
    "AW_PINNED_CHILD marker applies, as checkout_pin._launched_by_pin_bootstrap documents",
)
def test_07b_pre_marker_driver_bootstrap_runs_real_cli_silent(tmp_path: Path) -> None:
    # Regression for run-20260925T174509Z-636951 (u27oh3): a long-lived driver keeps its in-memory
    # bootstrap, so its pinned children carry NO AW_PINNED_CHILD. They must still be recognized and
    # NOT re-exec into the lane's package, or the lane's code performs the driver's finalize.
    fake = _make_fake_checkout(tmp_path)
    bootstrap = _pre_marker_bootstrap()
    assert "AW_PINNED_CHILD" not in bootstrap
    cmd = [sys.executable]
    if sys.version_info >= (3, 11):
        cmd.append("-P")
    cmd.extend(["-c", bootstrap, "--version"])
    env = runner_shared.pinned_child_env(_clean_env())
    proc = subprocess.run(cmd, cwd=str(fake), env=env, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "agent-workflows" in proc.stdout
    assert "FAKE-RAN" not in proc.stdout
    assert proc.stderr == ""


def test_07c_keep_root_env_alone_does_not_exempt(tmp_path: Path) -> None:
    # The agent turn inherits AW_PIN_KEEP_ROOT too (wj5b53 F-4), so that env var by itself must NOT
    # suppress the re-exec: only the bootstrap's own launch shape does.
    fake = _make_fake_checkout(tmp_path)
    proc = _run_launcher(fake, extra_env={"AW_PIN_KEEP_ROOT": REPO_ROOT})
    assert proc.returncode == 0
    assert "FAKE-RAN" in proc.stdout
    assert "aw: invoked in checkout" in proc.stderr


def test_08_in_process_main_returns_normally(tmp_path: Path) -> None:
    fake = _make_fake_checkout(tmp_path)
    old_cwd = os.getcwd()
    try:
        os.chdir(fake)
        try:
            ret = cli.main(["--version"])
            assert ret == 0
        except SystemExit as exc:
            assert exc.code == 0
    finally:
        os.chdir(old_cwd)


def test_09_cwd_repo_root_runs_real_cli_silent() -> None:
    proc = _run_launcher(REPO_ROOT)
    assert proc.returncode == 0
    assert "agent-workflows" in proc.stdout
    assert "FAKE-RAN" not in proc.stdout
    assert proc.stderr == ""


def test_10_marker_scoping_consumed_not_inherited_by_grandchild(tmp_path: Path) -> None:
    fake = _make_fake_checkout(tmp_path)
    script = (
        f"import sys, os, subprocess\n"
        f"sys.path.insert(0, {REPO_ROOT!r})\n"
        f"from agent_workflows.cli import main\n"
        f"sys.argv = ['aw', '--version']\n"
        f"try:\n"
        f"    main()\n"
        f"except SystemExit:\n"
        f"    pass\n"
        f"sub = subprocess.run([sys.executable, '-c', 'import os; print(\"GRANDCHILD_MARKER:\", os.environ.get(\"AW_PINNED_CHILD\"))'], capture_output=True, text=True)\n"
        f"print(sub.stdout.strip())\n"
        f"sys.exit(0)\n"
    )
    cmd = [sys.executable]
    if sys.version_info >= (3, 11):
        cmd.append("-P")
    cmd.extend(["-c", script])
    env = _clean_env({"AW_PINNED_CHILD": "1"})
    proc = subprocess.run(cmd, cwd=str(fake), env=env, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "agent-workflows" in proc.stdout
    assert "FAKE-RAN" not in proc.stdout
    assert proc.stderr == ""
    assert "GRANDCHILD_MARKER: None" in proc.stdout


def test_11_completion_both_surfaces_silent_and_fast(tmp_path: Path) -> None:
    fake = _make_fake_checkout(tmp_path)

    # Surface 1: hidden __complete verb
    proc1 = _run_launcher(fake, args=["__complete", "--cword", "1", "--", "aw", "ip"])
    assert proc1.returncode == 0
    assert "ipd" in proc1.stdout
    assert "FAKE-RAN" not in proc1.stdout
    assert proc1.stderr == ""

    # Surface 2: argcomplete env var COMP_LINE
    proc2 = _run_launcher(fake, extra_env={"COMP_LINE": "aw ip"})
    assert proc2.returncode == 0
    assert "agent-workflows" in proc2.stdout
    assert "FAKE-RAN" not in proc2.stdout
    assert proc2.stderr == ""


def test_12_bare_agent_workflows_directory_without_init_silent(tmp_path: Path) -> None:
    bare = tmp_path / "bare"
    (bare / ".git").mkdir(parents=True, exist_ok=True)
    (bare / "agent_workflows").mkdir(parents=True, exist_ok=True)
    # Note: no __init__.py inside bare/agent_workflows

    proc = _run_launcher(bare)
    assert proc.returncode == 0
    assert "agent-workflows" in proc.stdout
    assert "FAKE-RAN" not in proc.stdout
    assert proc.stderr == ""


def test_13_notice_survives_piped_stderr(tmp_path: Path) -> None:
    fake = _make_fake_checkout(tmp_path)
    # capture_output=True pipes stderr through an OS pipe with line_buffering disabled in the child,
    # which verifies that the notice is flushed before os.execve replaces the process image (F-10).
    script = (
        f"import sys\n"
        f"sys.stderr.reconfigure(line_buffering=False)\n"
        f"sys.path.insert(0, {REPO_ROOT!r})\n"
        f"from agent_workflows.cli import main\n"
        f"sys.exit(main())\n"
    )
    cmd = [sys.executable]
    if sys.version_info >= (3, 11):
        cmd.append("-P")
    cmd.extend(["-c", script, "--version"])
    env = _clean_env()
    proc = subprocess.run(cmd, cwd=str(fake), env=env, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "FAKE-RAN" in proc.stdout
    assert "aw: invoked in checkout" in proc.stderr
    assert os.path.realpath(fake) in proc.stderr
    assert REPO_ROOT_REAL in proc.stderr

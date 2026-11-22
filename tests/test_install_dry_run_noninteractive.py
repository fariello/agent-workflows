"""Behavioral regression tests for dry-run and non-interactive invariants in aw install (IPD rznd0q)."""

from __future__ import annotations

import argparse
import builtins
import io
import json
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Dict
from unittest import mock

import pytest

from agent_workflows import cli, config, term as term_mod
from agent_workflows.install_wizard import (
    IncompletePolicyError,
    ProjectPolicy,
    collect_policy_interactive,
)
from agent_workflows.layout_migration import MigrationManager
from agent_workflows.term import Term
from tests.support import init_repo


class _FakeTTYStdin:
    """Simulated interactive TTY stdin stream."""

    def isatty(self) -> bool:
        return True


class _FakeNonTTYStdin:
    """Simulated non-TTY stdin stream."""

    def isatty(self) -> bool:
        return False


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _git_status_porcelain(repo: Path) -> str:
    res = _git(repo, "status", "--porcelain")
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


def _snapshot_tree(root: Path) -> Dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def _make_legacy_121_repo(base: Path, name: str = "legacy-repo") -> Path:
    repo = init_repo(base / name)
    (repo / ".agents" / "workflows").mkdir(parents=True)
    (repo / ".agents" / "workflows" / "VERSION").write_text("1.2.1\n", encoding="utf-8")
    (repo / ".agents" / "workflows" / "index.md").write_text(
        "# Legacy Workflows Index\n", encoding="utf-8"
    )
    (repo / ".agents" / "README.md").write_text(
        "# Legacy Agents Readme\n", encoding="utf-8"
    )
    (repo / "workflow-artifacts" / "verify" / "run1").mkdir(parents=True)
    (repo / "workflow-artifacts" / "verify" / "run1" / "out.md").write_text(
        "verify output\n", encoding="utf-8"
    )
    res_add = _git(repo, "add", "-A")
    assert res_add.returncode == 0, res_add.stderr
    res_commit = _git(repo, "commit", "-m", "commit legacy 1.2.1 layout")
    assert res_commit.returncode == 0, res_commit.stderr
    assert _git_status_porcelain(repo) == ""
    return repo


def _make_modern_aw_repo(base: Path, name: str = "modern-repo") -> Path:
    repo = init_repo(base / name)
    (repo / ".aw" / "system" / "workflows").mkdir(parents=True)
    (repo / ".aw" / "system" / "VERSION").write_text("2.0.0\n", encoding="utf-8")
    (repo / ".aw" / "system" / "workflows" / "index.md").write_text(
        "# Modern Index\n", encoding="utf-8"
    )
    (repo / ".aw" / "config").mkdir(parents=True)
    (repo / ".aw" / "config" / "project.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "preset": "private-target",
                "role": "target",
                "delivery_mode": "tracked",
                "records_backend": "repository",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    res_add = _git(repo, "add", "-A")
    assert res_add.returncode == 0, res_add.stderr
    res_commit = _git(repo, "commit", "-m", "commit modern .aw layout")
    assert res_commit.returncode == 0, res_commit.stderr
    assert _git_status_porcelain(repo) == ""
    return repo


def _isolate_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, clear_ci: bool = False
) -> Dict[str, Path]:
    home_dir = tmp_path / "home"
    aw_home = home_dir / ".aw"
    xdg_config = home_dir / ".config"
    xdg_data = home_dir / ".local" / "share"
    home_dir.mkdir(parents=True, exist_ok=True)
    aw_home.mkdir(parents=True, exist_ok=True)
    xdg_config.mkdir(parents=True, exist_ok=True)
    xdg_data.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config))
    monkeypatch.setenv("XDG_DATA_HOME", str(xdg_data))
    if clear_ci:
        monkeypatch.delenv("AW_NONINTERACTIVE", raising=False)
        monkeypatch.delenv("CI", raising=False)
    return {
        "home": home_dir,
        "aw_home": aw_home,
        "xdg_config": xdg_config,
        "xdg_data": xdg_data,
    }


def _fail_input(*args, **kwargs):
    raise AssertionError(f"input() must not be called; got args={args!r}")


def _run_cli_in_process(argv: list[str]) -> tuple[int, str, str]:
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        rc = cli.main(argv)
    return rc, out_buf.getvalue(), err_buf.getvalue()


def test_legacy_install_dry_run_no_interactive_exact_repro(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exact 3z57rk reproduction: --dry-run --no-interactive on legacy 1.2.1 repo with TTY stdin."""
    _isolate_env(monkeypatch, tmp_path, clear_ci=True)
    repo = _make_legacy_121_repo(tmp_path)
    agents_before = _snapshot_tree(repo / ".agents")
    artifacts_before = _snapshot_tree(repo / "workflow-artifacts")

    monkeypatch.setattr(sys, "stdin", _FakeTTYStdin())
    monkeypatch.setattr(builtins, "input", _fail_input)

    rc, stdout, stderr = _run_cli_in_process(
        ["install", str(repo), "--dry-run", "--no-interactive"]
    )
    combined = stdout + stderr

    assert rc == 0, combined
    assert "AW Policy Update Checkpoint" not in combined
    assert "migrated legacy layout to .aw/" not in combined
    assert "[DRY RUN]" in combined
    assert not (repo / ".aw").exists()
    assert _snapshot_tree(repo / ".agents") == agents_before
    assert _snapshot_tree(repo / "workflow-artifacts") == artifacts_before
    assert _git_status_porcelain(repo) == ""


def test_legacy_install_dry_run_to_aw_no_interactive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--dry-run --to-aw --no-interactive previews legacy migration without mutating disk."""
    _isolate_env(monkeypatch, tmp_path, clear_ci=True)
    repo = _make_legacy_121_repo(tmp_path)
    agents_before = _snapshot_tree(repo / ".agents")
    artifacts_before = _snapshot_tree(repo / "workflow-artifacts")

    monkeypatch.setattr(sys, "stdin", _FakeTTYStdin())
    monkeypatch.setattr(builtins, "input", _fail_input)

    rc, stdout, stderr = _run_cli_in_process(
        ["install", str(repo), "--dry-run", "--to-aw", "--no-interactive"]
    )
    combined = stdout + stderr

    assert rc == 0, combined
    assert "[DRY RUN]" in combined
    assert "migrated legacy layout to .aw/" not in combined
    assert not (repo / ".aw").exists()
    assert _snapshot_tree(repo / ".agents") == agents_before
    assert _snapshot_tree(repo / "workflow-artifacts") == artifacts_before
    assert _git_status_porcelain(repo) == ""


@pytest.mark.parametrize("layout", ["legacy", "modern"])
def test_interactive_tty_dry_run_never_prompts_or_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, layout: str
) -> None:
    """Interactive TTY --dry-run (without --no-interactive, CI/AW_NONINTERACTIVE cleared) writes nothing."""
    paths = _isolate_env(monkeypatch, tmp_path, clear_ci=True)
    if layout == "legacy":
        repo = _make_legacy_121_repo(tmp_path)
        before_agents = _snapshot_tree(repo / ".agents")
        before_artifacts = _snapshot_tree(repo / "workflow-artifacts")
        before_aw = _snapshot_tree(repo / ".aw")
    else:
        repo = _make_modern_aw_repo(tmp_path)
        before_agents = _snapshot_tree(repo / ".agents")
        before_artifacts = _snapshot_tree(repo / "workflow-artifacts")
        before_aw = _snapshot_tree(repo / ".aw")

    monkeypatch.setattr(sys, "stdin", _FakeTTYStdin())
    monkeypatch.setattr(builtins, "input", _fail_input)

    rc, stdout, stderr = _run_cli_in_process(["install", str(repo), "--dry-run"])
    combined = stdout + stderr

    assert rc == 0, combined
    assert "[DRY RUN]" in combined
    assert "AW Policy Update Checkpoint" not in combined
    assert not config.config_path().exists()
    xdg_written = {
        k: v
        for k, v in _snapshot_tree(paths["xdg_config"]).items()
        if k != "agent-workflows/completion-notice.json"
    }
    assert xdg_written == {}
    assert _snapshot_tree(repo / ".agents") == before_agents
    assert _snapshot_tree(repo / "workflow-artifacts") == before_artifacts
    assert _snapshot_tree(repo / ".aw") == before_aw
    assert _git_status_porcelain(repo) == ""


@pytest.mark.parametrize("extra_flags", [[], ["--yes"]])
def test_legacy_install_dry_run_keep_legacy_no_interactive_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, extra_flags: list[str]
) -> None:
    """--dry-run --keep-legacy --no-interactive (with and without --yes) creates no .aw/ artifacts."""
    _isolate_env(monkeypatch, tmp_path, clear_ci=True)
    repo = _make_legacy_121_repo(tmp_path)

    monkeypatch.setattr(sys, "stdin", _FakeTTYStdin())
    monkeypatch.setattr(builtins, "input", _fail_input)

    rc, stdout, stderr = _run_cli_in_process(
        ["install", str(repo), "--dry-run", "--keep-legacy", "--no-interactive"]
        + extra_flags
    )
    combined = stdout + stderr

    assert rc == 0, combined
    assert not (repo / ".aw").exists()
    assert not (repo / ".aw" / "setup-repo-needed.md").exists()
    assert not (repo / ".aw" / ".gitignore").exists()
    assert not (repo / ".aw" / "state" / "durable" / "install.json").exists()
    assert _git_status_porcelain(repo) == ""


def test_legacy_install_dry_run_keep_legacy_dirty_tty_short_circuits_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tracked-dirty legacy repo under interactive TTY --dry-run --keep-legacy never prompts or mutates."""
    _isolate_env(monkeypatch, tmp_path, clear_ci=True)
    repo = _make_legacy_121_repo(tmp_path)
    dirty_file = repo / ".agents" / "README.md"
    dirty_content = "# Uncommitted local edit\n"
    dirty_file.write_text(dirty_content, encoding="utf-8")
    assert _git_status_porcelain(repo) != ""

    monkeypatch.setattr(sys, "stdin", _FakeTTYStdin())
    monkeypatch.setattr(builtins, "input", _fail_input)

    rc, stdout, stderr = _run_cli_in_process(
        ["install", str(repo), "--dry-run", "--keep-legacy"]
    )
    combined = stdout + stderr

    assert rc == 0, combined
    assert not (repo / ".aw").exists()
    assert not (repo / ".agent-workflows-installer-backups").exists()
    assert dirty_file.read_text(encoding="utf-8") == dirty_content


def test_collect_policy_interactive_interactivity_and_dry_run_matrix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Direct collect_policy_interactive matrix for overrides, env vars, dry_run, gftvh6, and first-install."""
    _isolate_env(monkeypatch, tmp_path, clear_ci=True)
    modern_repo = _make_modern_aw_repo(tmp_path, "matrix-modern")
    fresh_repo = init_repo(tmp_path / "matrix-fresh")
    existing = ProjectPolicy(preset="private-target")
    term = Term(color=False, stream=io.StringIO())

    # (a) set_interactive_override(False) and interactive=False prevent prompting on TTY and StringIO
    for stdin_factory in (_FakeTTYStdin, lambda: io.StringIO("n\n")):
        monkeypatch.setattr(sys, "stdin", stdin_factory())
        monkeypatch.setattr(builtins, "input", _fail_input)

        term_mod.set_interactive_override(False)
        try:
            pol = collect_policy_interactive(
                term=term,
                repo_path=str(modern_repo),
                existing_policy=existing,
            )
            assert pol.preset == "private-target"
        finally:
            term_mod.set_interactive_override(None)

        pol2 = collect_policy_interactive(
            term=term,
            repo_path=str(modern_repo),
            existing_policy=existing,
            interactive=False,
        )
        assert pol2.preset == "private-target"

    # (b) AW_NONINTERACTIVE=1 and CI=1 prevent prompting on TTY, StringIO, and even interactive=True
    for env_var in ("AW_NONINTERACTIVE", "CI"):
        monkeypatch.delenv("AW_NONINTERACTIVE", raising=False)
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.setenv(env_var, "1")
        monkeypatch.setattr(builtins, "input", _fail_input)

        for stdin_factory in (_FakeTTYStdin, lambda: io.StringIO("n\n")):
            monkeypatch.setattr(sys, "stdin", stdin_factory())
            for explicit_interactive in (None, True):
                pol = collect_policy_interactive(
                    term=term,
                    repo_path=str(modern_repo),
                    existing_policy=existing,
                    interactive=explicit_interactive,
                )
                assert pol.preset == "private-target"

    monkeypatch.delenv("AW_NONINTERACTIVE", raising=False)
    monkeypatch.delenv("CI", raising=False)

    # (c) dry_run=True with existing_policy prevents prompting on a simulated interactive TTY
    monkeypatch.setattr(sys, "stdin", _FakeTTYStdin())
    monkeypatch.setattr(builtins, "input", _fail_input)
    pol_dry = collect_policy_interactive(
        term=term,
        repo_path=str(modern_repo),
        existing_policy=existing,
        dry_run=True,
    )
    assert pol_dry.preset == "private-target"

    # (d) interactive=True without forced non-interactive overrides and dry_run=False enters interactive path
    monkeypatch.setattr(sys, "stdin", _FakeNonTTYStdin())
    prompts_seen: list[str] = []

    def _accept_checkpoint(prompt: str = "") -> str:
        prompts_seen.append(prompt)
        return "y"

    monkeypatch.setattr(builtins, "input", _accept_checkpoint)
    pol_forced_int = collect_policy_interactive(
        term=term,
        repo_path=str(modern_repo),
        existing_policy=existing,
        assume_yes=False,
        interactive=True,
        dry_run=False,
    )
    assert pol_forced_int.preset == "private-target"
    assert len(prompts_seen) == 1
    assert "Keep current policy and proceed?" in prompts_seen[0]

    # (e) Non-interactive first install on fresh repo without policy flags raises IncompletePolicyError
    monkeypatch.setattr(sys, "stdin", _FakeTTYStdin())
    monkeypatch.setattr(builtins, "input", _fail_input)
    with pytest.raises(IncompletePolicyError):
        collect_policy_interactive(
            term=term,
            repo_path=str(fresh_repo),
            existing_policy=None,
            interactive=False,
        )


def test_split_brain_guard_dry_run_forwards_and_leaves_repo_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_split_brain_guard under dry_run=True forwards dry_run=True and leaves split-brain tree intact."""
    _isolate_env(monkeypatch, tmp_path, clear_ci=True)
    repo = init_repo(tmp_path / "split-brain-repo")
    (repo / ".aw" / "system" / "workflows").mkdir(parents=True)
    (repo / ".aw" / "system" / "VERSION").write_text("2.0.0\n", encoding="utf-8")
    (repo / ".agents" / "workflows").mkdir(parents=True)
    (repo / ".agents" / "workflows" / "index.md").write_text(
        "# Legacy Index\n", encoding="utf-8"
    )
    res_add = _git(repo, "add", "-A")
    assert res_add.returncode == 0, res_add.stderr
    res_commit = _git(repo, "commit", "-m", "commit split-brain layout")
    assert res_commit.returncode == 0, res_commit.stderr
    agents_before = _snapshot_tree(repo / ".agents")
    aw_before = _snapshot_tree(repo / ".aw")

    monkeypatch.setattr(sys, "stdin", _FakeTTYStdin())
    args = argparse.Namespace(yes=False, dry_run=True, leftovers=None)
    buf = io.StringIO()
    term = Term(color=False, stream=buf)

    observed_calls: list[dict[str, object]] = []
    orig_execute = MigrationManager.execute_migration

    def _spy_execute(self, *call_args, **call_kwargs):
        observed_calls.append(dict(call_kwargs))
        return orig_execute(self, *call_args, **call_kwargs)

    with mock.patch("agent_workflows.cli._prompt_yes_no", return_value=True):
        with mock.patch.object(MigrationManager, "execute_migration", new=_spy_execute):
            decision = cli._split_brain_guard(term, repo, args)

    assert decision == "skip"
    assert len(observed_calls) == 1
    assert observed_calls[0].get("dry_run") is True
    assert "[DRY RUN]" in buf.getvalue()
    assert _snapshot_tree(repo / ".agents") == agents_before
    assert _snapshot_tree(repo / ".aw") == aw_before
    assert _git_status_porcelain(repo) == ""


def test_install_dry_run_completion_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """aw install <repo> --dry-run --no-interactive --completion bash writes no completion file."""
    paths = _isolate_env(monkeypatch, tmp_path, clear_ci=True)
    repo = _make_modern_aw_repo(tmp_path, "completion-dry-run")

    monkeypatch.setattr(sys, "stdin", _FakeTTYStdin())
    monkeypatch.setattr(builtins, "input", _fail_input)

    rc, stdout, stderr = _run_cli_in_process(
        [
            "install",
            str(repo),
            "--dry-run",
            "--no-interactive",
            "--completion",
            "bash",
        ]
    )
    combined = stdout + stderr

    assert rc == 0, combined
    assert _snapshot_tree(paths["xdg_data"]) == {}
    assert _snapshot_tree(paths["xdg_config"]) == {}
    assert _git_status_porcelain(repo) == ""

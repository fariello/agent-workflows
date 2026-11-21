"""Behavioral tests for terminal bell (BEL 0x07) config, CLI flags, and runner hooks."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import pytest

from agent_workflows import cli, config, question_inbox, term
from agent_workflows.notify import core as notify_core
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core


class _FakeTTY(io.StringIO):
    """In-memory text stream claiming to be an interactive TTY."""

    def isatty(self) -> bool:
        return True


def _write_user_config(cfg_dir: Path, payload: dict) -> Path:
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = cfg_dir / "config.json"
    cfg_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return cfg_path


def test_bell_default_on_for_tty_and_silent_for_non_tty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(config.CONFIG_DIR_ENV, str(tmp_path / "cfg"))
    term.set_bell_override(None)

    tty = _FakeTTY()
    assert config.get_bell() is None
    assert term.should_bell(tty) is True
    assert term.ring_bell(tty) is True
    assert tty.getvalue() == "\a"

    pipe = io.StringIO()
    assert term.should_bell(pipe) is False
    assert term.ring_bell(pipe) is False
    assert pipe.getvalue() == ""


def test_bell_config_set_unset_and_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg_dir = tmp_path / "cfg"
    monkeypatch.setenv(config.CONFIG_DIR_ENV, str(cfg_dir))
    term.set_bell_override(None)
    tty = _FakeTTY()

    # Disable via `aw config set bell false`
    rc = cli.main(["config", "set", "bell", "false"])
    assert rc == 0
    assert config.get_bell() is False
    assert term.should_bell(tty) is False
    assert term.ring_bell(tty) is False
    assert tty.getvalue() == ""

    # Explicit --bell override beats config bell=false
    assert term.should_bell(tty, override=True) is True
    assert term.ring_bell(tty, override=True) is True
    assert tty.getvalue() == "\a"

    # Non-TTY stays silent even with --bell override
    pipe = io.StringIO()
    assert term.should_bell(pipe, override=True) is False
    assert term.ring_bell(pipe, override=True) is False
    assert pipe.getvalue() == ""

    # Re-enable via `aw config set bell true`
    rc = cli.main(["config", "set", "bell", "true"])
    assert rc == 0
    assert config.get_bell() is True
    assert term.should_bell(tty) is True

    # Explicit --no-bell override beats config bell=true
    assert term.should_bell(tty, override=False) is False

    # Unset via `aw config set bell -` reverts to unset (default True)
    rc = cli.main(["config", "set", "bell", "-"])
    assert rc == 0
    assert config.get_bell() is None
    assert term.should_bell(tty) is True

    # Invalid boolean value is refused
    rc_bad = cli.main(["config", "set", "bell", "bogus"])
    assert rc_bad != 0


def test_bell_prefers_tty_stderr_when_stdout_is_piped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(config.CONFIG_DIR_ENV, str(tmp_path / "cfg"))
    term.set_bell_override(None)

    piped_stdout = io.StringIO()
    tty_stderr = _FakeTTY()
    monkeypatch.setattr("sys.stdout", piped_stdout)
    monkeypatch.setattr("sys.stderr", tty_stderr)

    assert term.ring_bell() is True
    assert piped_stdout.getvalue() == ""
    assert tty_stderr.getvalue() == "\a"


def test_cli_early_flags_bell_strip_conflict_and_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(config.CONFIG_DIR_ENV, str(tmp_path / "cfg"))

    # Stripped on forwarded runner routes, preserved after `--`
    kept_no, flags_no = cli._consume_early_flags(["agy", "run", "--no-bell", "status"])
    assert kept_no == ["agy", "run", "status"]
    assert flags_no.bell_override is False
    assert flags_no.saw_no_bell is True
    assert flags_no.saw_bell is False

    kept_yes, flags_yes = cli._consume_early_flags(["oc", "run", "--bell", "status"])
    assert kept_yes == ["oc", "run", "status"]
    assert flags_yes.bell_override is True
    assert flags_yes.saw_bell is True
    assert flags_yes.saw_no_bell is False

    kept_pass, flags_pass = cli._consume_early_flags(
        ["oc", "run", "--", "--no-bell", "--bell"]
    )
    assert kept_pass == ["oc", "run", "--", "--no-bell", "--bell"]
    assert flags_pass.bell_override is None

    # Mutual exclusion returns exit 2 on both parsed and forwarded routes
    for argv in (
        ["attention", "--no-bell", "--bell"],
        ["oc", "run", "--no-bell", "--bell", "status"],
        ["agy", "run", "--bell", "--no-bell", "status"],
    ):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = cli._dispatch(argv)
        assert rc == 2
        assert "argument --bell: not allowed with argument --no-bell" in err.getvalue()

    # cli.main restores bell override in finally even on SystemExit (--help)
    term.set_bell_override(None)
    with pytest.raises(SystemExit):
        cli.main(["--no-bell", "check", "--help"])
    assert term.get_bell_override() is None


def test_dispatch_checkpoint_rings_once_per_new_open_question_without_external_channels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg_dir = tmp_path / "cfg"
    monkeypatch.setenv(config.CONFIG_DIR_ENV, str(cfg_dir))
    monkeypatch.setenv("AW_HOME", str(tmp_path / "aw_home"))
    term.set_bell_override(None)

    repo = tmp_path / "repo"
    repo.mkdir()
    plan_path = RecordBuilder(repo).plan(
        id6="abc123",
        title="Bell test plan",
        set="bell",
        order=1,
        slug="bell-test",
        status="approved",
        scope_paths="README.md",
    )
    run_dir = tmp_path / "run-bell-test"
    run_dir.mkdir()

    def _add_question(oq_id: str, text: str) -> None:
        question_inbox.write_question(
            run_dir,
            {"id6": "abc123", "plan": str(plan_path.relative_to(repo))},
            {"question_id": oq_id, "question": text, "blocking": True},
            attempt=1,
            repo=repo,
        )

    tty_stderr = _FakeTTY()
    monkeypatch.setattr("sys.stderr", tty_stderr)
    monkeypatch.setattr("sys.stdout", io.StringIO())

    state = {"run_id": "run-bell-test", "repo": str(repo), "queue": []}

    # No open questions -> no bell
    notify_core.dispatch_checkpoint(run_dir, state, repo)
    assert tty_stderr.getvalue() == ""

    # First open question -> rings once
    _add_question("OQ-01", "Proceed?")
    notify_core.dispatch_checkpoint(run_dir, state, repo)
    assert tty_stderr.getvalue() == "\a"

    # Repeated checkpoint with same open question -> does not re-ring
    notify_core.dispatch_checkpoint(run_dir, state, repo)
    assert tty_stderr.getvalue() == "\a"

    # Second distinct open question -> rings once more
    _add_question("OQ-02", "Second?")
    notify_core.dispatch_checkpoint(run_dir, state, repo)
    assert tty_stderr.getvalue() == "\a\a"

    # Config bell=false suppresses bell for a third question, while --bell re-enables it
    _write_user_config(cfg_dir, {"config_version": 2, "bell": False})
    _add_question("OQ-03", "Third?")
    notify_core.dispatch_checkpoint(run_dir, state, repo)
    assert tty_stderr.getvalue() == "\a\a"

    term.set_bell_override(True)
    try:
        _add_question("OQ-04", "Fourth?")
        notify_core.dispatch_checkpoint(run_dir, state, repo)
        assert tty_stderr.getvalue() == "\a\a\a"
    finally:
        term.set_bell_override(None)
        notify_core._BELL_RUNG_QIDS.pop(str(run_dir.resolve()), None)

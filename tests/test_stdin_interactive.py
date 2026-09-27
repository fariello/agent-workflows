"""Tests for term.stdin_is_interactive and its authority-gate consumers (IPD k4vi7z)."""

from __future__ import annotations

import argparse
import ctypes
import io
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


from agent_workflows import git_commit_helper, specs, term
from tests.support import init_repo


class _FakeStdin:
    def isatty(self) -> bool:
        return True


def _args(**kw):
    ns = argparse.Namespace()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


# --------------------------------------------------------------------------------------
# E-06: Helper-level outcome tests
# --------------------------------------------------------------------------------------


def test_helper_win32_console_mode_zero_is_false():
    """(a) On win32 with GetConsoleMode returning 0, stdin_is_interactive is False."""
    fake_windll = SimpleNamespace(
        kernel32=SimpleNamespace(
            GetStdHandle=lambda n: 1,
            GetConsoleMode=lambda h, m: 0,
        )
    )
    with mock.patch.object(sys, "stdin", _FakeStdin()):
        with mock.patch("sys.platform", "win32"):
            with mock.patch.object(ctypes, "windll", fake_windll, create=True):
                assert term.stdin_is_interactive() is False


def test_helper_win32_console_mode_one_is_true():
    """(b) On win32 with GetConsoleMode returning 1, stdin_is_interactive is True."""
    fake_windll = SimpleNamespace(
        kernel32=SimpleNamespace(
            GetStdHandle=lambda n: 1,
            GetConsoleMode=lambda h, m: 1,
        )
    )
    with mock.patch.object(sys, "stdin", _FakeStdin()):
        with mock.patch("sys.platform", "win32"):
            with mock.patch.object(ctypes, "windll", fake_windll, create=True):
                assert term.stdin_is_interactive() is True


def test_helper_posix_isatty_true_does_not_touch_windll():
    """(c) On POSIX with isatty() True, stdin_is_interactive is True without touching windll."""
    with mock.patch.object(sys, "stdin", _FakeStdin()):
        with mock.patch("sys.platform", "linux"):
            assert term.stdin_is_interactive() is True


# --------------------------------------------------------------------------------------
# E-10: Site-level outcome tests
# --------------------------------------------------------------------------------------


def test_site_win32_nul_specs_run_set_refuses_unattested_approval():
    """(d) On win32 NUL, specs.run_set without --by-human returns 1 and leaves file byte-identical."""
    fake_windll = SimpleNamespace(
        kernel32=SimpleNamespace(
            GetStdHandle=lambda n: 1,
            GetConsoleMode=lambda h, m: 0,
        )
    )
    spec_content = (
        "# Spec: sample\n\n"
        "- Status: reviewed\n\n"
        "## Body\n\nContent\n\n"
        "## Workflow history\n"
        "- 2026-09-26 reviewed (fixture): ready\n"
    )
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "20260926-0001-01-sample.spec.md"
        p.write_text(spec_content, encoding="utf-8")
        before_bytes = p.read_bytes()

        stderr_buf = io.StringIO()
        stdout_buf = io.StringIO()
        args = _args(
            path=str(p),
            status="approved",
            message="interactive signoff",
            gate_kind=None,
            gate_ref=None,
            gate_summary=None,
            evidence=None,
            by_human=False,
            date="2026-09-27",
            no_commit=True,
        )
        with mock.patch.object(sys, "stdin", _FakeStdin()):
            with mock.patch("sys.platform", "win32"):
                with mock.patch.object(ctypes, "windll", fake_windll, create=True):
                    with redirect_stderr(stderr_buf), redirect_stdout(stdout_buf):
                        rc = specs.run_set(args)

        assert rc == 1, f"expected rc=1, got {rc}"
        assert (
            "human-only transition" in stderr_buf.getvalue()
        ), f"expected 'human-only transition' in stderr, got: {stderr_buf.getvalue()}"
        assert (
            p.read_bytes() == before_bytes
        ), "spec file must be byte-identical after refusal"


def test_site_win32_nul_git_commit_helper_skips_without_prompt(tmp_path: Path):
    """(e) On win32 NUL, git_commit_helper.offer_commit returns STATUS_SKIPPED and never prompts."""
    fake_windll = SimpleNamespace(
        kernel32=SimpleNamespace(
            GetStdHandle=lambda n: 1,
            GetConsoleMode=lambda h, m: 0,
        )
    )
    repo = init_repo(tmp_path / "repo")
    target = repo / "file.txt"
    target.write_text("content\n", encoding="utf-8")

    def _fail_input(*_args, **_kwargs):
        raise AssertionError(
            "input() must not be called on non-interactive Windows NUL stdin"
        )

    with mock.patch.object(sys, "stdin", _FakeStdin()):
        with mock.patch("sys.platform", "win32"):
            with mock.patch.object(ctypes, "windll", fake_windll, create=True):
                with mock.patch("builtins.input", side_effect=_fail_input):
                    result = git_commit_helper.offer_commit(
                        repo,
                        ["file.txt"],
                        message="test commit",
                        interactive=None,
                    )

    assert result.status == git_commit_helper.STATUS_SKIPPED

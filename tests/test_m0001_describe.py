"""Outcome tests for m0001 short-description normalization and validation.

IPD 830wku (E-01 / V-01). Spec 4sd62s Section 4.2 SAFEGUARDS and OQ-31.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

from agent_workflows.migrations import m0001_describe

pytestmark = pytest.mark.core


@pytest.fixture(autouse=True)
def _isolate_aw_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))


def test_validate_refuses_empty_blank_and_quoted_empty(tmp_path: Path) -> None:
    reasons = set()
    for raw in ("", "   ", "\t  ", '""', "''", '"   "'):
        reason = m0001_describe.validate(raw, tmp_path)
        assert reason == "aw migrate metadata: short_description must not be empty"
        reasons.add(reason)
    assert len(reasons) == 1
    print("Refusal (empty/blank/quoted-empty):", next(iter(reasons)))


def test_validate_refuses_over_300_chars(tmp_path: Path) -> None:
    reason = m0001_describe.validate("a" * 301, tmp_path)
    assert reason is not None
    assert "300" in reason and "301" in reason
    print("Refusal (301 chars):", reason)


def test_validate_refuses_embedded_newline_and_cr(tmp_path: Path) -> None:
    reason_nl = m0001_describe.validate("First line\nSecond line", tmp_path)
    assert reason_nl is not None
    assert "newline" in reason_nl.lower()
    print("Refusal (inner \\n):", reason_nl)

    reason_cr = m0001_describe.validate("First line\rSecond line", tmp_path)
    assert reason_cr is not None
    assert "newline" in reason_cr.lower()


def test_validate_refuses_control_character(tmp_path: Path) -> None:
    reason = m0001_describe.validate("Alert\x07bell", tmp_path)
    assert reason is not None
    assert "control" in reason.lower()
    print("Refusal (\\x07 control char):", reason)


def test_validate_refuses_runtime_synthesized_home_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_home = "/" + "home/" + "fixture_person"
    monkeypatch.setenv("HOME", fake_home)
    candidate = f"Reads config from {fake_home}/secret.txt."
    reason = m0001_describe.validate(candidate, tmp_path)
    assert reason is not None
    assert "home-path" in reason
    print("Refusal (sanitizer home-path):", reason)


def test_validate_refuses_bare_and_wrapped_absolute_paths(tmp_path: Path) -> None:
    bare_posix = m0001_describe.validate("See /home/alice/x for details.", tmp_path)
    assert bare_posix is not None
    assert "absolute multi-segment path" in bare_posix
    print("Refusal (bare /home/alice/x):", bare_posix)

    wrapped_posix = m0001_describe.validate('See ("/home/alice/x").', tmp_path)
    assert wrapped_posix is not None
    assert "absolute multi-segment path" in wrapped_posix
    print('Refusal (wrapped ("/home/alice/x").):', wrapped_posix)

    kv_posix = m0001_describe.validate("Uses profile=/opt/secret/file.", tmp_path)
    assert kv_posix is not None
    assert "absolute multi-segment path" in kv_posix

    win_drive = "C:" + "\\work\\secret.txt"
    bare_win = m0001_describe.validate(f"Stored in {win_drive} locally.", tmp_path)
    assert bare_win is not None
    assert "absolute Windows drive path" in bare_win
    print("Refusal (Windows drive):", bare_win)

    wrapped_win = m0001_describe.validate(f'Stored in ("{win_drive}"),', tmp_path)
    assert wrapped_win is not None
    assert "absolute Windows drive path" in wrapped_win


def test_validate_refuses_derived_hostname_warn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_host = "fixture-leak-host"
    monkeypatch.setattr(socket, "gethostname", lambda: fake_host)
    reason = m0001_describe.validate(f"Executed cleanly on {fake_host}.", tmp_path)
    assert reason is not None
    assert f"derived:{fake_host}" in reason
    print("Refusal (derived:<host> warn):", reason)


def test_validate_distinct_refusal_reasons(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_home = "/" + "home/" + "fixture_person"
    fake_host = "fixture-leak-host"
    monkeypatch.setenv("HOME", fake_home)
    monkeypatch.setattr(socket, "gethostname", lambda: fake_host)

    win_drive = "C:" + "\\work\\secret.txt"
    reasons = [
        m0001_describe.validate("", tmp_path),
        m0001_describe.validate("a" * 301, tmp_path),
        m0001_describe.validate("line1\nline2", tmp_path),
        m0001_describe.validate("ctrl\x07char", tmp_path),
        m0001_describe.validate(f"path {fake_home}/x", tmp_path),
        m0001_describe.validate("/home/alice/x", tmp_path),
        m0001_describe.validate('("/home/alice/x").', tmp_path),
        m0001_describe.validate(win_drive, tmp_path),
        m0001_describe.validate(f"host {fake_host}", tmp_path),
    ]
    assert all(isinstance(r, str) and len(r) > 0 for r in reasons)
    assert len(set(reasons)) == len(reasons)


def test_validate_accepts_300_char_plain_and_normalized_quotes(tmp_path: Path) -> None:
    plain_300 = "x" * 300
    assert m0001_describe.validate(plain_300, tmp_path) is None

    wrapped_300 = f'  "{plain_300}"\n'
    assert m0001_describe.normalize_description(wrapped_300) == plain_300
    assert m0001_describe.validate(wrapped_300, tmp_path) is None

    assert (
        m0001_describe.normalize_description("  'Adds a widget.'  ") == "Adds a widget."
    )
    assert m0001_describe.normalize_description('""inner""') == '"inner"'


def test_validate_preserves_unmatched_quotes(tmp_path: Path) -> None:
    assert m0001_describe.normalize_description('  "unmatched  ') == '"unmatched'
    assert m0001_describe.normalize_description("  unmatched'  ") == "unmatched'"
    assert m0001_describe.normalize_description("  \"mixed'  ") == "\"mixed'"
    assert m0001_describe.normalize_description('  "  ') == '"'
    assert (
        m0001_describe.validate('  "unmatched quote stays intact  ', tmp_path) is None
    )


def test_validate_accepts_slash_commands_and_relative_paths(tmp_path: Path) -> None:
    assert m0001_describe.validate("Runs /plan-review before merge.", tmp_path) is None
    assert (
        m0001_describe.validate("Runs `/plan-review` before merge.", tmp_path) is None
    )
    assert (
        m0001_describe.validate("Avoids //server/share style UNC paths.", tmp_path)
        is None
    )
    assert (
        m0001_describe.validate(
            "Adds validation in agent_workflows/migrations/m0001_describe.py.",
            tmp_path,
        )
        is None
    )


def test_validate_reuses_prebuilt_ruleset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruleset = m0001_describe.build_describe_ruleset(tmp_path)

    def _fail_rebuild(_repo: Path) -> object:
        raise AssertionError(
            "build_describe_ruleset must not be called when ruleset is provided"
        )

    monkeypatch.setattr(m0001_describe, "build_describe_ruleset", _fail_rebuild)

    assert (
        m0001_describe.validate(
            "Validates short descriptions safely.", tmp_path, ruleset=ruleset
        )
        is None
    )
    fake_home = "/" + "home/" + "fixture_person"
    refusal = m0001_describe.validate(f"Uses {fake_home}/x", tmp_path, ruleset=ruleset)
    assert refusal is not None and "home-path" in refusal

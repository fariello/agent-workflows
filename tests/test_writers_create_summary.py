"""Tests that creating commands write `--summary` as `short_description` via `artifact_meta`.

Covers `4sd62s` 4.2 SHORT DESCRIPTION and AC-36 case 1 for:
- `aw backlog new` (IPD fekdwv E-01)
- `aw specs new` (IPD fekdwv E-02)
- `aw releases new` (IPD fekdwv E-03)
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
from pathlib import Path

import pytest

from agent_workflows import artifact_meta as _meta
from agent_workflows import attention_contract as A
from agent_workflows import cli

pytestmark = pytest.mark.core

_ID_LINE_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)
    (repo / ".aw" / "records" / "backlog" / "open").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "specs" / "draft").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
    return repo


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:
            rc = int(exc.code or 0)
    return rc, out.getvalue(), err.getvalue()


def _git_status_porcelain(repo: Path) -> str:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _extract_id6(text: str) -> str:
    m = _ID_LINE_RE.search(text)
    assert m is not None, f"missing - Id: bullet in:\n{text}"
    return m.group(1)


def _read_after_cache_unlink(repo: Path, id6: str) -> _meta.State:
    db_path = repo / ".aw" / "state" / "index.db"
    db_path.unlink(missing_ok=True)
    return _meta.read(id6, project_context=_meta.legacy_context(repo))


def _check_all_diagnostics(repo: Path) -> tuple[int, list[dict]]:
    rc, out, err = _run_cli(["check", "all", "--agent", "--dir", str(repo)])
    diags: list[dict] = []
    for line in (out + "\n" + err).splitlines():
        s = line.strip()
        if s.startswith("{"):
            rec = json.loads(s)
            diags.extend(rec.get("diagnostics") or [])
    return rc, diags


# --------------------------------------------------------------------------------------
# Backlog (`aw backlog new`)
# --------------------------------------------------------------------------------------


def test_backlog_new_stores_short_description(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, out, err = _run_cli(
        [
            "backlog",
            "new",
            "--priority",
            "high",
            "--work-kind",
            "feature",
            "--summary",
            "Adds a widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    files = list((repo / ".aw" / "records" / "backlog").rglob("*.backlog.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "- Short-Description: Adds a widget." in text
    assert "- Summary: Adds a widget." in text

    id6 = _extract_id6(text)
    state = _read_after_cache_unlink(repo, id6)
    assert state.fields["short_description"] == "Adds a widget."
    assert state.short_description == "Adds a widget."


def test_backlog_new_refuses_301_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "backlog",
            "new",
            "--priority",
            "high",
            "--work-kind",
            "feature",
            "--summary",
            "x" * (A.MAX_DESCRIPTIVE_LEN + 1),
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc != 0
    assert _git_status_porcelain(repo) == ""


def test_backlog_new_refuses_embedded_newline_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "backlog",
            "new",
            "--priority",
            "high",
            "--work-kind",
            "feature",
            "--summary",
            "Adds a widget.\n- Status: done",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc != 0
    assert _git_status_porcelain(repo) == ""


def test_backlog_new_refuses_control_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "backlog",
            "new",
            "--priority",
            "high",
            "--work-kind",
            "feature",
            "--summary",
            "Adds a\x07widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc != 0
    assert _git_status_porcelain(repo) == ""


def test_backlog_new_check_all_agent_zero_diagnostics(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, err = _run_cli(
        [
            "backlog",
            "new",
            "--priority",
            "high",
            "--work-kind",
            "feature",
            "--summary",
            "Adds a widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    check_rc, diags = _check_all_diagnostics(repo)
    assert check_rc == 0
    assert diags == []


# --------------------------------------------------------------------------------------
# Specs (`aw specs new`)
# --------------------------------------------------------------------------------------


def test_specs_new_stores_short_description(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, err = _run_cli(
        [
            "specs",
            "new",
            "--title",
            "Widget spec",
            "--summary",
            "Adds a widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    files = list((repo / ".aw" / "records" / "specs").rglob("*.spec.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "- Short-Description: Adds a widget." in text

    id6 = _extract_id6(text)
    state = _read_after_cache_unlink(repo, id6)
    assert state.fields["short_description"] == "Adds a widget."
    assert state.short_description == "Adds a widget."


def test_specs_new_omitted_summary_omits_short_description(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, err = _run_cli(
        [
            "specs",
            "new",
            "--title",
            "Widget spec",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    files = list((repo / ".aw" / "records" / "specs").rglob("*.spec.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "- Short-Description:" not in text

    id6 = _extract_id6(text)
    state = _read_after_cache_unlink(repo, id6)
    assert state.fields["short_description"] is None
    assert state.short_description is None


def test_specs_new_301_char_summary_omits_short_description(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    summary_301 = "x" * (A.MAX_DESCRIPTIVE_LEN + 1)
    rc, _out, err = _run_cli(
        [
            "specs",
            "new",
            "--title",
            "Widget spec",
            "--summary",
            summary_301,
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    files = list((repo / ".aw" / "records" / "specs").rglob("*.spec.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "- Short-Description:" not in text
    assert f"## Scope\n\n{summary_301}" in text

    id6 = _extract_id6(text)
    state = _read_after_cache_unlink(repo, id6)
    assert state.fields["short_description"] is None
    assert state.short_description is None


def test_specs_new_400_char_summary_omits_short_description(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    summary_400 = "y" * 400
    rc, _out, err = _run_cli(
        [
            "specs",
            "new",
            "--title",
            "Widget spec",
            "--summary",
            summary_400,
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    files = list((repo / ".aw" / "records" / "specs").rglob("*.spec.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "- Short-Description:" not in text
    assert f"## Scope\n\n{summary_400}" in text

    id6 = _extract_id6(text)
    state = _read_after_cache_unlink(repo, id6)
    assert state.fields["short_description"] is None
    assert state.short_description is None


def test_specs_new_refuses_4301_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "specs",
            "new",
            "--title",
            "Widget spec",
            "--summary",
            "z" * (A.MAX_PROSE_DESCRIPTIVE_LEN + 1),
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert _git_status_porcelain(repo) == ""


def test_specs_new_refuses_embedded_newline_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "specs",
            "new",
            "--title",
            "Widget spec",
            "--summary",
            "Adds a widget.\n- Status: approved",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert _git_status_porcelain(repo) == ""


def test_specs_new_refuses_control_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "specs",
            "new",
            "--title",
            "Widget spec",
            "--summary",
            "Adds a\x07widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert _git_status_porcelain(repo) == ""


def test_specs_new_check_all_agent_clean_for_short_description(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, err = _run_cli(
        [
            "specs",
            "new",
            "--title",
            "Widget spec",
            "--summary",
            "Adds a widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    _check_rc, diags = _check_all_diagnostics(repo)
    assert not any(
        "short_description" in json.dumps(d) or "Short-Description" in json.dumps(d)
        for d in diags
    )


# --------------------------------------------------------------------------------------
# Releases (`aw releases new`)
# --------------------------------------------------------------------------------------


def test_releases_new_stores_short_description_and_preview_parity(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    p_rc, p_out, p_err = _run_cli(
        [
            "releases",
            "new",
            "--version",
            "1.0.0",
            "--summary",
            "Adds a widget.",
            "--dir",
            str(repo),
        ]
    )
    assert p_rc == 0, p_err
    assert list((repo / ".aw" / "records").rglob("*.release.md")) == []
    assert "\n" in p_out
    preview_header, preview_text = p_out.split("\n", 1)
    assert preview_header.startswith("--- would write ")
    assert "- Short-Description: Adds a widget." in preview_text
    preview_id6 = _extract_id6(preview_text)

    a_rc, _a_out, a_err = _run_cli(
        [
            "releases",
            "new",
            "--version",
            "1.0.0",
            "--summary",
            "Adds a widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert a_rc == 0, a_err
    files = list((repo / ".aw" / "records" / "releases").rglob("*.release.md"))
    assert len(files) == 1
    written_text = files[0].read_text(encoding="utf-8")
    assert "- Short-Description: Adds a widget." in written_text
    written_id6 = _extract_id6(written_text)
    assert preview_text.replace(preview_id6, "ID6") == written_text.replace(
        written_id6, "ID6"
    )

    state = _read_after_cache_unlink(repo, written_id6)
    assert state.fields["short_description"] == "Adds a widget."
    assert state.short_description == "Adds a widget."


def test_releases_new_refuses_301_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "releases",
            "new",
            "--version",
            "1.0.0",
            "--summary",
            "x" * (A.MAX_DESCRIPTIVE_LEN + 1),
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc != 0
    assert _git_status_porcelain(repo) == ""


def test_releases_new_refuses_embedded_newline_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "releases",
            "new",
            "--version",
            "1.0.0",
            "--summary",
            "Adds a widget.\n- Status: shipped",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc != 0
    assert _git_status_porcelain(repo) == ""


def test_releases_new_refuses_control_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "releases",
            "new",
            "--version",
            "1.0.0",
            "--summary",
            "Adds a\x07widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc != 0
    assert _git_status_porcelain(repo) == ""


def test_releases_new_check_all_agent_clean_for_short_description(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, err = _run_cli(
        [
            "releases",
            "new",
            "--version",
            "1.0.0",
            "--summary",
            "Adds a widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    check_rc, diags = _check_all_diagnostics(repo)
    assert check_rc == 0
    assert diags == []
    assert not any(
        "short_description" in json.dumps(d) or "Short-Description" in json.dumps(d)
        for d in diags
    )

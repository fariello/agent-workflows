"""Tests that creating commands write `--summary` as `short_description` via `artifact_meta`.

Covers `4sd62s` 4.2 SHORT DESCRIPTION and AC-36 case 1 for:
- `aw backlog new` (IPD fekdwv E-01)
- `aw specs new` (IPD fekdwv E-02)
- `aw releases new` (IPD fekdwv E-03)
- `aw research new`, `aw adopt`, and research YAML create rendering (IPD bir7xm E-01..E-03)
- `aw ipd scaffold`, `aw prompts new`, `ipd_schema.META_RECOGNIZED`, and prompt trailer stripping (IPD py2vu9 E-01..E-04)
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
from pathlib import Path

import pytest

from agent_workflows import artifact_adopt as _adopt
from agent_workflows import artifact_meta as _meta
from agent_workflows import attention_contract as A
from agent_workflows import cli
from agent_workflows import command_surface as _cs
from agent_workflows import ipd_lint as _ipd_lint
from agent_workflows import prompts as _prompts
from agent_workflows import research_cmd as _research_cmd

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
    (repo / ".aw" / "records" / "research").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "prompts" / "pending").mkdir(
        parents=True, exist_ok=True
    )
    (repo / ".aw" / "inbox").mkdir(parents=True, exist_ok=True)
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


# --------------------------------------------------------------------------------------
# Research YAML front matter rendering (`artifact_meta.create`, IPD bir7xm E-03)
# --------------------------------------------------------------------------------------


def _yaml_frontmatter_lines(text: str) -> list[str]:
    lines = text.splitlines()
    assert lines and lines[0] == "---", f"missing opening fence in:\n{text}"
    end_idx = lines.index("---", 1)
    return lines[: end_idx + 1]


def _extract_research_id6(text: str) -> str:
    m = re.search(r"(?m)^id:\s*([0-9a-z]{6})\s*$", text)
    assert m is not None, f"missing id: in:\n{text}"
    return m.group(1)


def test_yaml_short_description_rendered_last_before_closing_fence(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    ctx = _meta.legacy_context(repo)
    fields = {
        "created": "20261109",
        "set": "widget",
        "order": 1,
        "topic": [],
        "model": None,
        "research_kind": "findings",
        "status": "todo",
        "outcome": "none-yet",
        "summary": "Widget summary.",
        "consumed_by": [],
        "priority": "high",
        "short_description": "Adds a widget.",
    }
    res = _meta.create(
        "ab12cd",
        "research",
        fields,
        "",
        destination="research/20261109-widget-01-ab12cd-widget.findings.md",
        dry_run=True,
        project_context=ctx,
        legacy_render=_meta.LegacyRender(
            tag="created",
            day="2026-11-09",
            actor_label="aw research",
            history=False,
        ),
    )
    fm_lines = _yaml_frontmatter_lines(res.text)
    assert fm_lines[-1] == "---"
    assert fm_lines[-3:-1] == [
        "priority: high",
        "short-description: Adds a widget.",
    ]


def test_yaml_short_description_absent_or_none_renders_no_line(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    ctx = _meta.legacy_context(repo)
    base_fields = {
        "created": "20261109",
        "set": "widget",
        "order": 1,
        "topic": [],
        "model": None,
        "research_kind": "findings",
        "status": "todo",
        "outcome": "none-yet",
        "summary": "Widget summary.",
        "consumed_by": [],
    }
    render = _meta.LegacyRender(
        tag="created",
        day="2026-11-09",
        actor_label="aw research",
        history=False,
    )
    dest = "research/20261109-widget-01-ab12cd-widget.findings.md"
    omitted = _meta.create(
        "ab12cd",
        "research",
        dict(base_fields),
        "",
        destination=dest,
        dry_run=True,
        project_context=ctx,
        legacy_render=render,
    )
    none_val = _meta.create(
        "ab12cd",
        "research",
        {**base_fields, "short_description": None},
        "",
        destination=dest,
        dry_run=True,
        project_context=ctx,
        legacy_render=render,
    )
    empty_val = _meta.create(
        "ab12cd",
        "research",
        {**base_fields, "short_description": ""},
        "",
        destination=dest,
        dry_run=True,
        project_context=ctx,
        legacy_render=render,
    )
    assert "short-description:" not in omitted.text
    assert omitted.text == none_val.text == empty_val.text


# --------------------------------------------------------------------------------------
# Research (`aw research new`, IPD bir7xm E-01)
# --------------------------------------------------------------------------------------


def test_research_new_stores_short_description(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, err = _run_cli(
        [
            "research",
            "new",
            "--kind",
            "findings",
            "--slug",
            "widget",
            "--summary",
            "Adds a widget.",
            "--apply",
            str(repo),
        ]
    )
    assert rc == 0, err
    files = [
        p
        for p in (repo / ".aw" / "records" / "research").rglob("*.md")
        if p.name != "INDEX.md"
    ]
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    fm_lines = _yaml_frontmatter_lines(text)
    assert fm_lines[-2] == "short-description: Adds a widget."

    id6 = _extract_research_id6(text)
    state = _read_after_cache_unlink(repo, id6)
    assert state.fields["short_description"] == "Adds a widget."
    assert state.short_description == "Adds a widget."


def test_research_new_omitted_summary_omits_short_description(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, err = _run_cli(
        [
            "research",
            "new",
            "--kind",
            "findings",
            "--slug",
            "widget",
            "--apply",
            str(repo),
        ]
    )
    assert rc == 0, err
    files = [
        p
        for p in (repo / ".aw" / "records" / "research").rglob("*.md")
        if p.name != "INDEX.md"
    ]
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "short-description:" not in text

    id6 = _extract_research_id6(text)
    state = _read_after_cache_unlink(repo, id6)
    assert state.fields.get("short_description") is None
    assert state.short_description is None


def test_research_new_refuses_301_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, out, err = _run_cli(
        [
            "research",
            "new",
            "--kind",
            "findings",
            "--slug",
            "widget",
            "--summary",
            "x" * (A.MAX_DESCRIPTIVE_LEN + 1),
            "--apply",
            str(repo),
        ]
    )
    assert rc == 2
    assert "300" in (out + err)
    assert _git_status_porcelain(repo) == ""


def test_research_new_refuses_embedded_newline_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, out, err = _run_cli(
        [
            "research",
            "new",
            "--kind",
            "findings",
            "--slug",
            "widget",
            "--summary",
            "Adds a widget.\nstatus: done",
            "--apply",
            str(repo),
        ]
    )
    assert rc == 2
    assert "newlines" in (out + err)
    assert _git_status_porcelain(repo) == ""


def test_research_new_refuses_control_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, out, err = _run_cli(
        [
            "research",
            "new",
            "--kind",
            "findings",
            "--slug",
            "widget",
            "--summary",
            "Adds a\x07widget.",
            "--apply",
            str(repo),
        ]
    )
    assert rc == 2
    assert "control characters" in (out + err)
    assert _git_status_porcelain(repo) == ""


def test_research_new_plan_refuses_unsafe_direct_short_description(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    files, err = _research_cmd.plan_new(
        research_root=repo / ".aw" / "records" / "research",
        kind="findings",
        slug="widget",
        summary="Safe summary.",
        short_description="x" * (A.MAX_DESCRIPTIVE_LEN + 1),
    )
    assert files is None
    assert err is not None and "300" in err


def test_research_new_check_all_agent_clean_for_short_description(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, err = _run_cli(
        [
            "research",
            "new",
            "--kind",
            "findings",
            "--slug",
            "widget",
            "--summary",
            "Adds a widget.",
            "--apply",
            str(repo),
        ]
    )
    assert rc == 0, err
    _check_rc, diags = _check_all_diagnostics(repo)
    assert not any(
        "short-description" in json.dumps(d) or "short_description" in json.dumps(d)
        for d in diags
    )


# --------------------------------------------------------------------------------------
# Adopt (`aw adopt`, IPD bir7xm E-02)
# --------------------------------------------------------------------------------------


def test_adopt_stores_short_description_and_preview_frontmatter(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    drop = repo / ".aw" / "inbox" / "widget-findings.md"
    drop.write_text("# Widget\n\nBody.\n", encoding="utf-8")

    plan, plan_err = _adopt.plan_adoption(
        repo_root=repo,
        source=drop,
        summary="Adds a widget.",
    )
    assert plan_err is None
    assert plan is not None
    preview_fm_lines = _yaml_frontmatter_lines(plan.frontmatter)
    assert preview_fm_lines[-2] == "short-description: Adds a widget."

    p_rc, _p_out, p_err = _run_cli(
        ["adopt", str(drop), "--summary", "Adds a widget.", "--dir", str(repo)]
    )
    assert p_rc == 0, p_err
    assert drop.is_file()
    assert list((repo / ".aw" / "records" / "research").rglob("*.md")) == []

    a_rc, _a_out, a_err = _run_cli(
        [
            "adopt",
            str(drop),
            "--summary",
            "Adds a widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert a_rc == 0, a_err
    assert not drop.exists()
    files = [
        p
        for p in (repo / ".aw" / "records" / "research").rglob("*.md")
        if p.name != "INDEX.md"
    ]
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    adopted_fm_lines = _yaml_frontmatter_lines(text)
    assert adopted_fm_lines[-2] == "short-description: Adds a widget."

    id6 = _extract_research_id6(text)
    state = _read_after_cache_unlink(repo, id6)
    assert state.fields["short_description"] == "Adds a widget."
    assert state.short_description == "Adds a widget."


def test_adopt_derived_heading_no_summary_omits_short_description(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    drop = repo / ".aw" / "inbox" / "heading-findings.md"
    drop.write_text("# Derived Heading\n\nBody.\n", encoding="utf-8")

    rc, _out, err = _run_cli(["adopt", str(drop), "--apply", "--dir", str(repo)])
    assert rc == 0, err
    files = [
        p
        for p in (repo / ".aw" / "records" / "research").rglob("*.md")
        if p.name != "INDEX.md"
    ]
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "summary: derived heading" in text
    assert "short-description:" not in text

    id6 = _extract_research_id6(text)
    state = _read_after_cache_unlink(repo, id6)
    assert state.fields.get("short_description") is None
    assert state.short_description is None


def test_adopt_refuses_301_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    drop = repo / ".aw" / "inbox" / "widget-findings.md"
    drop.write_text("# Widget\n\nBody.\n", encoding="utf-8")
    rc, out, err = _run_cli(
        [
            "adopt",
            str(drop),
            "--summary",
            "x" * (A.MAX_DESCRIPTIVE_LEN + 1),
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert "300" in (out + err)
    assert drop.is_file()
    assert list((repo / ".aw" / "records" / "research").rglob("*.md")) == []


def test_adopt_refuses_embedded_newline_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    drop = repo / ".aw" / "inbox" / "widget-findings.md"
    drop.write_text("# Widget\n\nBody.\n", encoding="utf-8")
    rc, out, err = _run_cli(
        [
            "adopt",
            str(drop),
            "--summary",
            "Adds a widget.\nstatus: done",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert "newlines" in (out + err)
    assert drop.is_file()
    assert list((repo / ".aw" / "records" / "research").rglob("*.md")) == []


def test_adopt_refuses_control_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    drop = repo / ".aw" / "inbox" / "widget-findings.md"
    drop.write_text("# Widget\n\nBody.\n", encoding="utf-8")
    rc, out, err = _run_cli(
        [
            "adopt",
            str(drop),
            "--summary",
            "Adds a\x07widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert "control characters" in (out + err)
    assert drop.is_file()
    assert list((repo / ".aw" / "records" / "research").rglob("*.md")) == []


def test_adopt_allow_leaks_refuses_unsafe_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    drop = repo / ".aw" / "inbox" / "leaky-findings.md"
    leak_path = "/" + "Users/" + "alice/secret"
    drop.write_text(f"# Leaky\n\nPath {leak_path}.\n", encoding="utf-8")
    rc, out, err = _run_cli(
        [
            "adopt",
            str(drop),
            "--allow-leaks",
            "--yes",
            "--summary",
            "x" * (A.MAX_DESCRIPTIVE_LEN + 1),
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert "300" in (out + err)
    assert drop.is_file()
    assert list((repo / ".aw" / "records" / "research").rglob("*.md")) == []


def test_adopt_check_all_agent_clean_for_short_description(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    drop = repo / ".aw" / "inbox" / "widget-findings.md"
    drop.write_text("# Widget\n\nBody.\n", encoding="utf-8")
    rc, _out, err = _run_cli(
        [
            "adopt",
            str(drop),
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
        "short-description" in json.dumps(d) or "short_description" in json.dumps(d)
        for d in diags
    )


# --------------------------------------------------------------------------------------
# IPD Schema (`ipd_schema.META_RECOGNIZED` / `aw ipd lint`, IPD py2vu9 E-01)
# --------------------------------------------------------------------------------------


def test_ipd_schema_lint_accepts_short_description_bullet(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, err = _run_cli(
        [
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Widget plan",
            "--set",
            "widget",
            "--order",
            "1",
            "--author",
            "tester",
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
    files = list((repo / ".aw" / "records" / "plans").rglob("*.ipd.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "- Short-Description: Adds a widget." in text

    lint_res = _ipd_lint.lint_file(files[0])
    m103 = [d for d in lint_res.diagnostics if d.code == _ipd_lint.C_META_UNKNOWN]
    assert m103 == []


# --------------------------------------------------------------------------------------
# IPD Scaffold (`aw ipd scaffold`, IPD py2vu9 E-02)
# --------------------------------------------------------------------------------------


def _scaffold_args(repo: Path, *extra: str, apply: bool = True) -> list[str]:
    args = [
        "ipd",
        "scaffold",
        "--kind",
        "child",
        "--title",
        "Widget plan",
        "--set",
        "widget",
        "--order",
        "1",
        "--author",
        "tester",
        "--priority",
        "high",
        "--work-kind",
        "feature",
        *extra,
        "--dir",
        str(repo),
    ]
    if apply:
        args.append("--apply")
    return args


def test_ipd_scaffold_stores_short_description_and_preview_parity(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    p_rc, p_out, p_err = _run_cli(
        _scaffold_args(repo, "--summary", "Adds a widget.", apply=False)
    )
    assert p_rc == 0, p_err
    assert list((repo / ".aw" / "records" / "plans").rglob("*.ipd.md")) == []
    assert "- Short-Description: Adds a widget." in p_out

    a_rc, _a_out, a_err = _run_cli(
        _scaffold_args(repo, "--summary", "Adds a widget.", apply=True)
    )
    assert a_rc == 0, a_err
    files = list((repo / ".aw" / "records" / "plans").rglob("*.ipd.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "- Short-Description: Adds a widget." in text

    id6 = _extract_id6(text)
    state_cached = _meta.read(id6, project_context=_meta.legacy_context(repo))
    assert state_cached.short_description == "Adds a widget."
    assert state_cached.fields["short_description"] == "Adds a widget."

    state_rebuilt = _read_after_cache_unlink(repo, id6)
    assert state_rebuilt.short_description == "Adds a widget."
    assert state_rebuilt.fields["short_description"] == "Adds a widget."


def test_ipd_scaffold_omitted_and_blank_summary_omits_short_description(
    tmp_path: Path,
) -> None:
    repo_omitted = _init_repo(tmp_path / "omitted")
    rc1, _out1, err1 = _run_cli(_scaffold_args(repo_omitted, apply=True))
    assert rc1 == 0, err1
    f1 = list((repo_omitted / ".aw" / "records" / "plans").rglob("*.ipd.md"))[0]
    t1 = f1.read_text(encoding="utf-8")
    assert "- Short-Description:" not in t1
    s1 = _read_after_cache_unlink(repo_omitted, _extract_id6(t1))
    assert s1.short_description is None
    assert s1.fields.get("short_description") is None

    repo_blank = _init_repo(tmp_path / "blank")
    rc2, _out2, err2 = _run_cli(
        _scaffold_args(repo_blank, "--summary", "   \t ", apply=True)
    )
    # Tab is a control character in attention_contract; test spaces-only separately below.
    assert rc2 == 2
    assert _git_status_porcelain(repo_blank) == ""

    repo_spaces = _init_repo(tmp_path / "spaces")
    rc3, _out3, err3 = _run_cli(
        _scaffold_args(repo_spaces, "--summary", "   ", apply=True)
    )
    assert rc3 == 0, err3
    f3 = list((repo_spaces / ".aw" / "records" / "plans").rglob("*.ipd.md"))[0]
    t3 = f3.read_text(encoding="utf-8")
    assert "- Short-Description:" not in t3
    s3 = _read_after_cache_unlink(repo_spaces, _extract_id6(t3))
    assert s3.short_description is None
    assert s3.fields.get("short_description") is None


def test_ipd_scaffold_refuses_301_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        _scaffold_args(repo, "--summary", "x" * (A.MAX_DESCRIPTIVE_LEN + 1), apply=True)
    )
    assert rc == 2
    assert _git_status_porcelain(repo) == ""


@pytest.mark.parametrize(
    "bad_summary",
    [
        "Adds a widget.\n- Status: approved",
        "Adds a widget.\n",
        "Adds a widget.\r",
    ],
)
def test_ipd_scaffold_refuses_newline_and_trailing_newline_summary(
    tmp_path: Path, bad_summary: str
) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        _scaffold_args(repo, "--summary", bad_summary, apply=True)
    )
    assert rc == 2
    assert _git_status_porcelain(repo) == ""


def test_ipd_scaffold_refuses_control_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        _scaffold_args(repo, "--summary", "Adds a\x07widget.", apply=True)
    )
    assert rc == 2
    assert _git_status_porcelain(repo) == ""


def test_ipd_scaffold_help_and_command_surface_include_summary() -> None:
    rc, out, _err = _run_cli(["ipd", "scaffold", "--help"])
    assert rc == 0
    assert "--summary" in out
    decl = _cs.get_declaration("ipd scaffold")
    assert decl is not None
    assert "--summary" in decl.legacy_flags


def test_ipd_scaffold_check_all_agent_clean_for_short_description(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, err = _run_cli(
        _scaffold_args(repo, "--summary", "Adds a widget.", apply=True)
    )
    assert rc == 0, err
    _check_rc, diags = _check_all_diagnostics(repo)
    assert not any(
        "short_description" in json.dumps(d) or "Short-Description" in json.dumps(d)
        for d in diags
    )


# --------------------------------------------------------------------------------------
# Prompts (`aw prompts new` and legacy comment trailer stripping, IPD py2vu9 E-03 & E-04)
# --------------------------------------------------------------------------------------


def _extract_prompt_id6(text: str) -> str:
    id6 = _prompts.read_metadata_id6(text)
    assert id6 is not None, f"missing Id: in prompt comment:\n{text}"
    return id6


def test_prompts_new_stores_short_description_and_purity(tmp_path: Path) -> None:
    repo_plain = _init_repo(tmp_path / "plain")
    rc_plain, _out_p, err_p = _run_cli(
        [
            "prompts",
            "new",
            "--slug",
            "widget",
            "--date",
            "2026-11-17",
            "--apply",
            "--dir",
            str(repo_plain),
        ]
    )
    assert rc_plain == 0, err_p
    plain_files = list(
        (repo_plain / ".aw" / "records" / "prompts").rglob("*.prompt.md")
    )
    assert len(plain_files) == 1
    plain_text = plain_files[0].read_text(encoding="utf-8")

    repo = _init_repo(tmp_path / "with_summary")
    rc, _out, err = _run_cli(
        [
            "prompts",
            "new",
            "--slug",
            "widget",
            "--date",
            "2026-11-17",
            "--summary",
            "Adds a widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    files = list((repo / ".aw" / "records" / "prompts").rglob("*.prompt.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")

    lines = text.splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("<!-- aw-prompt:")
    assert lines[0].endswith("-->")
    assert "Short-Description: Adds a widget." in lines[0]
    assert "- Short-Description:" not in text
    assert text.split("\n", 1)[1] == plain_text.split("\n", 1)[1] == ""

    id6 = _extract_prompt_id6(text)
    state_cached = _meta.read(id6, project_context=_meta.legacy_context(repo))
    assert state_cached.short_description == "Adds a widget."
    assert state_cached.fields["short_description"] == "Adds a widget."

    state_rebuilt = _read_after_cache_unlink(repo, id6)
    assert state_rebuilt.short_description == "Adds a widget."
    assert state_rebuilt.fields["short_description"] == "Adds a widget."


def test_prompts_new_omitted_and_blank_summary_omits_short_description(
    tmp_path: Path,
) -> None:
    for label, extra in (("omitted", ()), ("spaces", ("--summary", "   "))):
        repo = _init_repo(tmp_path / label)
        rc, _out, err = _run_cli(
            [
                "prompts",
                "new",
                "--slug",
                "widget",
                "--date",
                "2026-11-17",
                *extra,
                "--apply",
                "--dir",
                str(repo),
            ]
        )
        assert rc == 0, err
        files = list((repo / ".aw" / "records" / "prompts").rglob("*.prompt.md"))
        assert len(files) == 1
        text = files[0].read_text(encoding="utf-8")
        assert "Short-Description:" not in text
        state = _read_after_cache_unlink(repo, _extract_prompt_id6(text))
        assert state.short_description is None
        assert state.fields.get("short_description") is None


def test_prompts_new_refuses_301_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "prompts",
            "new",
            "--slug",
            "widget",
            "--summary",
            "x" * (A.MAX_DESCRIPTIVE_LEN + 1),
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert _git_status_porcelain(repo) == ""


@pytest.mark.parametrize(
    "bad_summary",
    [
        "Adds a widget.\n- Status: executed",
        "Adds a widget.\n",
        "Adds a widget.\r",
    ],
)
def test_prompts_new_refuses_newline_and_trailing_newline_summary(
    tmp_path: Path, bad_summary: str
) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "prompts",
            "new",
            "--slug",
            "widget",
            "--summary",
            bad_summary,
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert _git_status_porcelain(repo) == ""


def test_prompts_new_refuses_control_char_summary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "prompts",
            "new",
            "--slug",
            "widget",
            "--summary",
            "Adds a\x07widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert _git_status_porcelain(repo) == ""


@pytest.mark.parametrize(
    "bad_summary",
    [
        "Adds --> breakout",
        "Adds | Status: executed",
    ],
)
def test_prompts_new_refuses_html_comment_breakout_and_pipe_delimiter(
    tmp_path: Path, bad_summary: str
) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, _err = _run_cli(
        [
            "prompts",
            "new",
            "--slug",
            "widget",
            "--summary",
            bad_summary,
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert _git_status_porcelain(repo) == ""


def test_prompts_new_help_and_command_surface_include_summary() -> None:
    rc, out, _err = _run_cli(["prompts", "new", "--help"])
    assert rc == 0
    assert "--summary" in out
    decl = _cs.get_declaration("prompts new")
    assert decl is not None
    assert "--summary" in decl.legacy_flags


def test_prompts_new_check_all_agent_clean_for_short_description(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    rc, _out, err = _run_cli(
        [
            "prompts",
            "new",
            "--slug",
            "widget",
            "--date",
            "2026-11-17",
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


def test_prompts_render_metadata_comment_optional_short_description() -> None:
    with_sd = _prompts.render_metadata_comment(
        kind="research",
        status="pending",
        created="2026-11-17",
        id6="ab12cd",
        set_id="widget",
        short_description="Adds a widget.",
    )
    assert (
        f"Short-Description: Adds a widget. . {_prompts._METADATA_TRAILER}" in with_sd
    )

    without_sd = _prompts.render_metadata_comment(
        kind="research",
        status="pending",
        created="2026-11-17",
        id6="ab12cd",
        set_id="widget",
    )
    assert "Short-Description:" not in without_sd


def test_prompts_load_legacy_artifact_strips_metadata_trailer(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    records_root = repo / ".aw" / "records"
    prompt_path = (
        records_root
        / "prompts"
        / "pending"
        / "20261117-widget-01-ab12cd-widget.prompt.md"
    )
    comment = (
        "<!-- aw-prompt: Kind: research | Id: ab12cd | Set: widget | Status: pending "
        "| Created: 2026-11-17 | Short-Description: Adds a widget. . "
        f"{_prompts._METADATA_TRAILER} -->\n"
    )
    prompt_path.write_text(comment, encoding="utf-8")

    row, _hist = _meta.load_legacy_artifact(prompt_path, records_root)
    assert row["short_description"] == "Adds a widget."
    assert row["fields"]["short_description"] == "Adds a widget."

    state = _read_after_cache_unlink(repo, "ab12cd")
    assert state.short_description == "Adds a widget."
    assert state.fields["short_description"] == "Adds a widget."

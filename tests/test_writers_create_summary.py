"""Tests that creating commands write `--summary` as `short_description` via `artifact_meta`.

Covers `4sd62s` 4.2 SHORT DESCRIPTION and AC-36 case 1 for:
- `aw backlog new` (IPD fekdwv E-01)
- `aw specs new` (IPD fekdwv E-02)
- `aw releases new` (IPD fekdwv E-03)
- `aw research new`, `aw adopt`, and research YAML create rendering (IPD bir7xm E-01..E-03)
- `aw ipd scaffold`, `aw prompts new`, `ipd_schema.META_RECOGNIZED`, and prompt trailer stripping (IPD py2vu9 E-01..E-04)
- `aw describe` short-description setter and clearer across active, terminal, YAML, and prompt records (IPD h06gs7 E-04)
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
    id6 = _meta.read_text(text, record_type="prompt").id6 or None
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


def test_prompts_new_short_description_is_the_last_field_before_the_trailer(
    tmp_path: Path,
) -> None:
    texts = {}
    for label, extra in (
        ("with_sd", ("--summary", "Adds a widget.")),
        ("without_sd", ()),
    ):
        repo = _init_repo(tmp_path / label)
        rc, _out, err = _run_cli(
            [
                "prompts",
                "new",
                "--slug",
                "widget",
                "--set",
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
        texts[label] = files[0].read_text(encoding="utf-8")

    with_sd = texts["with_sd"]
    assert (
        f"Short-Description: Adds a widget. . {_prompts._METADATA_TRAILER}" in with_sd
    )
    assert (
        _meta.read_text(with_sd, record_type="prompt").short_description
        == "Adds a widget."
    )

    without_sd = texts["without_sd"]
    assert "Short-Description:" not in without_sd
    assert _meta.read_text(without_sd, record_type="prompt").short_description is None


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


# --------------------------------------------------------------------------------------
# Short-Description Setter (`aw describe`, IPD h06gs7 E-04)
# --------------------------------------------------------------------------------------


def _commit_repo(repo: Path, message: str = "seed fixture") -> None:
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo, check=True)


def _write_plan_fixture(
    repo: Path,
    *,
    id6: str = "ab12cd",
    set_id: str = "widget",
    order: int = 1,
    slug: str = "widget-plan",
    status: str = "approved",
    bucket: str = "pending",
    short_description: str | None = None,
) -> Path:
    plan_dir = repo / ".aw" / "records" / "plans" / bucket
    plan_dir.mkdir(parents=True, exist_ok=True)
    path = plan_dir / f"20261117-{set_id}-{order:02d}-{id6}-{slug}.ipd.md"
    lines = [
        "# IPD: Widget plan",
        "",
        "- Date: 2026-11-17",
        "- Kind: child",
        f"- Status: {status}",
        f"- Set: {set_id}",
        f"- Order: {order:02d}",
        f"- Id: {id6}",
    ]
    if short_description is not None:
        lines.append(f"- Short-Description: {short_description}")
    lines.extend(
        ["", "## Workflow history", "- 2026-11-17 draft (tester): created.", ""]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_describe_preview_does_not_write(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    plan_path = _write_plan_fixture(repo, id6="pl1234", set_id="widget", slug="first")
    _commit_repo(repo)
    before = plan_path.read_text(encoding="utf-8")

    rc, out, err = _run_cli(
        [
            "describe",
            "pl1234",
            "--summary",
            "Adds a widget.",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    assert "PREVIEW" in out
    assert "Adds a widget." not in plan_path.read_text(encoding="utf-8")
    assert plan_path.read_text(encoding="utf-8") == before
    assert _git_status_porcelain(repo) == ""


def test_describe_apply_sets_bullet_history_and_round_trips(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    plan_path = _write_plan_fixture(repo, id6="pl1234", set_id="widget", slug="first")
    _commit_repo(repo)

    rc, out, err = _run_cli(
        [
            "describe",
            "pl1234",
            "--summary",
            "Adds a widget.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    assert "CONFORMS" in out or "EXECUTED" in out or "Changes:" in out
    text = plan_path.read_text(encoding="utf-8")
    assert "- Short-Description: Adds a widget." in text
    assert "describe (aw describe): short_description set: Adds a widget." in text

    state = _read_after_cache_unlink(repo, "pl1234")
    assert state.short_description == "Adds a widget."
    assert state.fields["short_description"] == "Adds a widget."


def test_describe_executed_plan_accepted(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    plan_path = _write_plan_fixture(
        repo,
        id6="ex1234",
        set_id="widget",
        slug="done-plan",
        status="executed",
        bucket="executed",
    )
    _commit_repo(repo)

    rc, _out, err = _run_cli(
        [
            "describe",
            "ex1234",
            "--summary",
            "Terminal summary.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    text = plan_path.read_text(encoding="utf-8")
    assert "- Status: executed" in text
    assert "- Short-Description: Terminal summary." in text
    assert "describe (aw describe): short_description set: Terminal summary." in text

    state = _read_after_cache_unlink(repo, "ex1234")
    assert state.status == "executed"
    assert state.short_description == "Terminal summary."


def test_describe_clear_apply_removes_short_description(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    plan_path = _write_plan_fixture(
        repo,
        id6="cl1234",
        set_id="widget",
        slug="clear-plan",
        short_description="Old summary.",
    )
    _commit_repo(repo)

    rc, _out, err = _run_cli(
        ["describe", "cl1234", "--clear", "--apply", "--dir", str(repo)]
    )
    assert rc == 0, err
    text = plan_path.read_text(encoding="utf-8")
    assert "- Short-Description:" not in text
    assert "describe (aw describe): short_description cleared" in text

    state = _read_after_cache_unlink(repo, "cl1234")
    assert state.short_description is None
    assert state.fields.get("short_description") is None


def test_describe_unknown_id6_exits_2(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write_plan_fixture(repo, id6="pl1234", set_id="widget", slug="first")
    _commit_repo(repo)

    rc, out, err = _run_cli(
        ["describe", "zzzzzz", "--summary", "x", "--apply", "--dir", str(repo)]
    )
    assert rc == 2
    assert out == ""
    assert "zzzzzz" in err
    assert _git_status_porcelain(repo) == ""


def test_describe_reviewed_plan_does_not_collide_with_review_file(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    plan_path = _write_plan_fixture(repo, id6="rv1234", set_id="widget", slug="rev")
    reviews_dir = repo / ".aw" / "records" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    review_path = reviews_dir / "20261117-widget-01-rv1234-rev.review.md"
    review_original = (
        "# Plan Review\n\n"
        "- Subject-Id: rv1234\n"
        "- Subject-Type: ipd\n"
        "- Verdict: APPROVE\n"
    )
    review_path.write_text(review_original, encoding="utf-8")
    _commit_repo(repo)

    rc, _out, err = _run_cli(
        [
            "describe",
            "rv1234",
            "--summary",
            "Reviewed plan summary.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    assert "- Short-Description: Reviewed plan summary." in plan_path.read_text(
        encoding="utf-8"
    )
    assert review_path.read_text(encoding="utf-8") == review_original


def test_describe_multi_match_selector_exits_2(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    p1 = _write_plan_fixture(
        repo, id6="aa1111", set_id="sharedset", order=1, slug="one"
    )
    p2 = _write_plan_fixture(
        repo, id6="bb2222", set_id="sharedset", order=2, slug="two"
    )
    _commit_repo(repo)

    # Set id matching two plans
    rc_set, out_set, err_set = _run_cli(
        [
            "describe",
            "sharedset",
            "--summary",
            "Ambiguous",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc_set == 2
    assert out_set == ""
    assert "ambiguous" in err_set.lower()

    # Substring matching two plans
    rc_sub, out_sub, err_sub = _run_cli(
        [
            "describe",
            "20261117",
            "--summary",
            "Ambiguous",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc_sub == 2
    assert out_sub == ""
    assert "ambiguous" in err_sub.lower()
    assert "- Short-Description:" not in p1.read_text(encoding="utf-8")
    assert "- Short-Description:" not in p2.read_text(encoding="utf-8")
    assert _git_status_porcelain(repo) == ""


def test_describe_mutually_exclusive_and_missing_action_exit_2(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write_plan_fixture(repo, id6="pl1234", set_id="widget", slug="first")
    _commit_repo(repo)

    rc_both, _out1, _err1 = _run_cli(
        [
            "describe",
            "pl1234",
            "--summary",
            "Valid.",
            "--clear",
            "--dir",
            str(repo),
        ]
    )
    assert rc_both == 2

    rc_neither, _out2, _err2 = _run_cli(["describe", "pl1234", "--dir", str(repo)])
    assert rc_neither == 2
    assert _git_status_porcelain(repo) == ""


@pytest.mark.parametrize(
    "bad_summary",
    [
        pytest.param("x" * (A.MAX_DESCRIPTIVE_LEN + 1), id="301-chars"),
        "Adds a widget.\n- Status: executed",
        "Adds a widget.\n",
        "Adds a widget.\r",
        "Adds a\x07widget.",
        "   ",
        "",
        pytest.param(
            "Contains leak " + "/" + "Users/" + "alice/secret", id="leak-path"
        ),
    ],
)
def test_describe_refuses_unsafe_summary_values(
    tmp_path: Path, bad_summary: str
) -> None:
    repo = _init_repo(tmp_path)
    _write_plan_fixture(repo, id6="pl1234", set_id="widget", slug="first")
    _commit_repo(repo)

    rc, out, _err = _run_cli(
        [
            "describe",
            "pl1234",
            "--summary",
            bad_summary,
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert out == ""
    assert _git_status_porcelain(repo) == ""


def test_describe_research_yaml_set_and_clear_round_trip(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc_new, _out_n, err_n = _run_cli(
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
    assert rc_new == 0, err_n
    files = [
        p
        for p in (repo / ".aw" / "records" / "research").rglob("*.md")
        if p.name != "INDEX.md"
    ]
    assert len(files) == 1
    rpath = files[0]
    id6 = _extract_research_id6(rpath.read_text(encoding="utf-8"))

    rc_set, _out_s, err_s = _run_cli(
        [
            "describe",
            id6,
            "--summary",
            "Research short summary.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc_set == 0, err_s
    set_text = rpath.read_text(encoding="utf-8")
    fm_set = _yaml_frontmatter_lines(set_text)
    assert "short-description: Research short summary." in fm_set
    assert (
        "describe (aw describe): short_description set: Research short summary."
        in set_text
    )
    state_set = _read_after_cache_unlink(repo, id6)
    assert state_set.short_description == "Research short summary."

    rc_clr, _out_c, err_c = _run_cli(
        ["describe", id6, "--clear", "--apply", "--dir", str(repo)]
    )
    assert rc_clr == 0, err_c
    clr_text = rpath.read_text(encoding="utf-8")
    assert "short-description:" not in clr_text
    assert "describe (aw describe): short_description cleared" in clr_text
    state_clr = _read_after_cache_unlink(repo, id6)
    assert state_clr.short_description is None


def test_describe_prompt_comment_set_and_clear_round_trip(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rc_new, _out_n, err_n = _run_cli(
        [
            "prompts",
            "new",
            "--slug",
            "widget",
            "--date",
            "2026-11-17",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc_new == 0, err_n
    files = list((repo / ".aw" / "records" / "prompts").rglob("*.prompt.md"))
    assert len(files) == 1
    ppath = files[0]
    id6 = _extract_prompt_id6(ppath.read_text(encoding="utf-8"))

    rc_set, _out_s, err_s = _run_cli(
        [
            "describe",
            id6,
            "--summary",
            "Prompt short summary.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc_set == 0, err_s
    set_text = ppath.read_text(encoding="utf-8")
    first_line = set_text.splitlines()[0]
    assert first_line.startswith("<!-- aw-prompt:")
    assert first_line.endswith("-->")
    assert "Short-Description: Prompt short summary." in first_line
    assert "- Short-Description:" not in set_text
    state_set = _read_after_cache_unlink(repo, id6)
    assert state_set.short_description == "Prompt short summary."

    rc_clr, _out_c, err_c = _run_cli(
        ["describe", id6, "--clear", "--apply", "--dir", str(repo)]
    )
    assert rc_clr == 0, err_c
    clr_text = ppath.read_text(encoding="utf-8")
    assert "Short-Description:" not in clr_text.splitlines()[0]
    state_clr = _read_after_cache_unlink(repo, id6)
    assert state_clr.short_description is None


@pytest.mark.parametrize(
    "bad_prompt_summary",
    [
        "Adds --> breakout",
        "Adds | Status: executed",
    ],
)
def test_describe_prompt_refuses_breakout_and_pipe(
    tmp_path: Path, bad_prompt_summary: str
) -> None:
    repo = _init_repo(tmp_path)
    rc_new, _out_n, err_n = _run_cli(
        [
            "prompts",
            "new",
            "--slug",
            "widget",
            "--date",
            "2026-11-17",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc_new == 0, err_n
    ppath = list((repo / ".aw" / "records" / "prompts").rglob("*.prompt.md"))[0]
    id6 = _extract_prompt_id6(ppath.read_text(encoding="utf-8"))
    _commit_repo(repo)

    rc, out, _err = _run_cli(
        [
            "describe",
            id6,
            "--summary",
            bad_prompt_summary,
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 2
    assert out == ""
    assert _git_status_porcelain(repo) == ""


def test_describe_specs_and_backlog_sidecar_round_trip(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    assert (
        _run_cli(
            [
                "specs",
                "new",
                "--title",
                "Widget Spec",
                "--apply",
                "--dir",
                str(repo),
            ]
        )[0]
        == 0
    )
    assert (
        _run_cli(
            [
                "backlog",
                "new",
                "--priority",
                "high",
                "--work-kind",
                "feature",
                "--summary",
                "Initial backlog.",
                "--apply",
                "--dir",
                str(repo),
            ]
        )[0]
        == 0
    )

    spec_id = _extract_id6(
        list((repo / ".aw" / "records" / "specs").rglob("*.spec.md"))[0].read_text(
            encoding="utf-8"
        )
    )
    bklg_id = _extract_id6(
        list((repo / ".aw" / "records" / "backlog").rglob("*.backlog.md"))[0].read_text(
            encoding="utf-8"
        )
    )

    for id6, summary in (
        (spec_id, "Spec short."),
        (bklg_id, "Backlog short."),
    ):
        rc, _out, err = _run_cli(
            ["describe", id6, "--summary", summary, "--apply", "--dir", str(repo)]
        )
        assert rc == 0, f"{id6}: {err}"
        state = _read_after_cache_unlink(repo, id6)
        assert state.short_description == summary

    sidecar = repo / ".aw" / "records" / "history.jsonl"
    assert sidecar.is_file()
    sidecar_text = sidecar.read_text(encoding="utf-8")
    assert spec_id in sidecar_text and bklg_id in sidecar_text
    assert "aw describe" in sidecar_text


def test_describe_releases_and_walkthroughs_round_trip(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    assert (
        _run_cli(
            [
                "releases",
                "new",
                "--version",
                "2.0.0",
                "--summary",
                "Initial release.",
                "--apply",
                "--dir",
                str(repo),
            ]
        )[0]
        == 0
    )
    wt_dir = repo / ".aw" / "records" / "walkthroughs"
    wt_dir.mkdir(parents=True, exist_ok=True)
    wt_path = wt_dir / "20261117-widget-01-wt1234-demo.walkthrough.md"
    wt_path.write_text(
        "# Walkthrough: Demo\n\n- Date: 2026-11-17\n- Id: wt1234\n- Set: widget\n\n## Summary\n\nDone.\n",
        encoding="utf-8",
    )

    rel_id = _extract_id6(
        list((repo / ".aw" / "records" / "releases").rglob("*.release.md"))[
            0
        ].read_text(encoding="utf-8")
    )

    for id6, summary in (
        (rel_id, "Release short."),
        ("wt1234", "Walkthrough short."),
    ):
        rc, _out, err = _run_cli(
            ["describe", id6, "--summary", summary, "--apply", "--dir", str(repo)]
        )
        assert rc == 0, f"{id6}: {err}"
        state = _read_after_cache_unlink(repo, id6)
        assert state.short_description == summary


def test_describe_agent_and_json_preview_apply_and_error(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write_plan_fixture(repo, id6="aj1234", set_id="widget", slug="machine")
    _commit_repo(repo)

    # --agent preview
    rc_ap, out_ap, err_ap = _run_cli(
        [
            "describe",
            "aj1234",
            "--summary",
            "Machine summary.",
            "--agent",
            "--dir",
            str(repo),
        ]
    )
    assert rc_ap == 0, err_ap
    rec_ap = json.loads(out_ap.strip().splitlines()[-1])
    assert rec_ap["schema"] == "aw.agent/v1"
    assert rec_ap["kind"] == "result"
    assert rec_ap["cmd"] == "describe"
    assert rec_ap["outcome"] == "preview"
    assert rec_ap["exit"] == 0
    assert rec_ap["applied"] is False
    assert rec_ap["changes"][0]["kind"] == "modify"
    assert "--apply" in rec_ap["next"]
    assert _git_status_porcelain(repo) == ""

    # --json preview
    rc_jp, out_jp, err_jp = _run_cli(
        [
            "describe",
            "aj1234",
            "--summary",
            "Machine summary.",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert rc_jp == 0, err_jp
    doc_jp = json.loads(out_jp)
    assert doc_jp["command"] == "describe"
    assert doc_jp["status"] == "preview"
    assert doc_jp["exit_code"] == 0
    assert doc_jp["changes"][0]["applied"] is False
    assert doc_jp["data"]["applied"] is False

    # --agent apply
    rc_aa, out_aa, err_aa = _run_cli(
        [
            "describe",
            "aj1234",
            "--summary",
            "Machine summary.",
            "--apply",
            "--agent",
            "--dir",
            str(repo),
        ]
    )
    assert rc_aa == 0, err_aa
    rec_aa = json.loads(out_aa.strip().splitlines()[-1])
    assert rec_aa["kind"] == "result"
    assert rec_aa["outcome"] == "clean"
    assert rec_aa["exit"] == 0
    assert rec_aa["applied"] is True

    # --json apply
    rc_ja, out_ja, err_ja = _run_cli(
        [
            "describe",
            "aj1234",
            "--summary",
            "Machine summary two.",
            "--apply",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert rc_ja == 0, err_ja
    doc_ja = json.loads(out_ja)
    assert doc_ja["status"] == "clean"
    assert doc_ja["exit_code"] == 0
    assert doc_ja["changes"][0]["applied"] is True
    assert doc_ja["data"]["short_description"] == "Machine summary two."

    # --agent and --json unknown selector error
    rc_ae, out_ae, _err_ae = _run_cli(
        [
            "describe",
            "missing",
            "--summary",
            "x",
            "--agent",
            "--dir",
            str(repo),
        ]
    )
    assert rc_ae == 2
    rec_ae = json.loads(out_ae.strip().splitlines()[-1])
    assert rec_ae["kind"] == "error"
    assert rec_ae["outcome"] == "cannot-run"
    assert rec_ae["exit"] == 2

    rc_je, out_je, _err_je = _run_cli(
        [
            "describe",
            "missing",
            "--summary",
            "x",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert rc_je == 2
    doc_je = json.loads(out_je)
    assert doc_je["status"] == "cannot-run"
    assert doc_je["exit_code"] == 2


def test_describe_path_confinement_and_global_precedence(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    # Direct path outside the 7 record trees must be refused with exit 2.
    outside_doc = repo / "README.md"
    outside_doc.write_text("# Repo\n\n- Id: out123\n", encoding="utf-8")
    # Plan declaring id6 gp1234 vs spec whose filename contains gp1234 as substring.
    plan_path = _write_plan_fixture(repo, id6="gp1234", set_id="widget", slug="target")
    spec_dir = repo / ".aw" / "records" / "specs" / "draft"
    spec_path = spec_dir / "20261117-sp9999-01-sp9999-mentions-gp1234.spec.md"
    spec_path.write_text(
        "# Spec\n\n- Date: 2026-11-17\n- Status: draft\n- Id: sp9999\n",
        encoding="utf-8",
    )
    _commit_repo(repo)

    rc_out, _o1, _e1 = _run_cli(
        [
            "describe",
            str(outside_doc),
            "--summary",
            "Nope.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc_out == 2
    assert _git_status_porcelain(repo) == ""

    # id6 match (tier 2) on plan beats substring match (tier 6) on spec filename.
    rc_prec, _o2, err_prec = _run_cli(
        [
            "describe",
            "gp1234",
            "--summary",
            "Precedence hit.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc_prec == 0, err_prec
    assert "- Short-Description: Precedence hit." in plan_path.read_text(
        encoding="utf-8"
    )
    assert "- Short-Description:" not in spec_path.read_text(encoding="utf-8")


def test_describe_log_format_post_cutover_set_and_clear(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    records_root = repo / ".aw" / "records"
    ctx = _meta.legacy_context(repo)
    plan_path = _write_plan_fixture(
        repo,
        id6="lg1234",
        set_id="widget",
        slug="logged",
        status="executed",
        bucket="executed",
    )
    rel_plan = plan_path.relative_to(records_root).as_posix()
    _meta.append(
        "lg1234",
        [
            {
                "op": "create",
                "path": rel_plan,
                "fields": {
                    "id": "lg1234",
                    "type": "ipd",
                    "status": "draft",
                    "set": "widget",
                    "order": 1,
                    "path": rel_plan,
                    "title": "Widget plan",
                },
                "message": "created",
            },
        ],
        project_context=ctx,
        _from_create=True,
    )
    for app_evs in (
        [{"op": "transition", "from": "draft", "to": "to-review", "message": "r"}],
        [{"op": "transition", "from": "to-review", "to": "reviewed", "message": "rv"}],
        [
            {
                "op": "transition",
                "from": "reviewed",
                "to": "approved",
                "message": "app",
            },
            {
                "op": "set",
                "fields": {"approval": "2026-11-17, tester: ok"},
                "message": "app",
            },
        ],
        [
            {
                "op": "transition",
                "from": "approved",
                "to": "executed",
                "message": "exec",
            },
            {"op": "unset", "fields": ["approval"], "message": "exec"},
            {
                "op": "set",
                "fields": {"scope_result": "within"},
                "message": "exec",
            },
        ],
    ):
        _meta.append(
            "lg1234",
            app_evs,
            by_human=True,
            project_context=ctx,
        )
    assert (records_root / "meta" / "lg1234.jsonl").is_file()

    rc_set, _o1, err1 = _run_cli(
        [
            "describe",
            "lg1234",
            "--summary",
            "Post-cutover terminal summary.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc_set == 0, err1
    state_set = _read_after_cache_unlink(repo, "lg1234")
    assert state_set.short_description == "Post-cutover terminal summary."
    assert state_set.status == "executed"

    rc_clr, _o2, err2 = _run_cli(
        ["describe", "lg1234", "--clear", "--apply", "--dir", str(repo)]
    )
    assert rc_clr == 0, err2
    state_clr = _read_after_cache_unlink(repo, "lg1234")
    assert state_clr.short_description is None

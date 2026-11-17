"""Outcome tests for m0001 step-6 census, round-trip verifier, stamp, and step-7 commit.

IPD dcerjg (E-12, E-13, E-14 / V-12, V-13, V-14). Spec 4sd62s Sections 5.2 steps 6-7,
5.2a items 1/3/5, AC-10, AC-16, AC-20, and AC-41.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_workflows import (
    artifact_meta,
    attention_contract,
    cli,
    git_commit_helper,
    layout_migration,
)
from agent_workflows.migrations import (
    chain,
    m0001_metadata_v2,
    m0001_verify,
)

pytestmark = pytest.mark.core


_DEFAULT_GITIGNORE = (
    "/state/\n"
    "/config/local.json\n"
    "records/history.jsonl\n"
    "records/plans/INDEX.json\n"
    "records/runs/\n"
)


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _init_git_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, name: str = "repo"
) -> Path:
    aw_home = tmp_path / f"aw_home_{name}"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(aw_home / "xdg"))

    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / ".aw" / "records").mkdir(parents=True)
    (repo / ".aw" / ".gitignore").write_text(_DEFAULT_GITIGNORE, encoding="utf-8")
    return repo


def _commit_all(repo: Path, msg: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


def _install_precommit_gates_hook(repo: Path) -> Path:
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    py_exe = sys.executable
    pkg_root = Path(__file__).resolve().parent.parent
    hook.write_text(
        "#!/usr/bin/env sh\n"
        "set -eu\n"
        f'export PYTHONPATH="{pkg_root}${{PYTHONPATH:+:$PYTHONPATH}}"\n'
        f'"{py_exe}" -m agent_workflows ipd-executed-gate\n'
        f'"{py_exe}" -m agent_workflows backlog-blocking-close-gate\n',
        encoding="utf-8",
    )
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return hook


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [
        artifact_meta.decode_line(line)
        for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
        if line.strip()
    ]


# --------------------------------------------------------------------------------------
# AC-20: Census ("no sidecar (none expected)", unknown-field, unparseable, missing desc)
# --------------------------------------------------------------------------------------


def test_census_no_sidecar_none_expected_skips_absent_templates_and_lists_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-20 / 5.2a(5): repository with no id6 spec/backlog reports 'no sidecar (none expected)'."""
    repo = _init_git_repo(tmp_path, monkeypatch, name="census_no_sidecar")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "pending").mkdir(parents=True)
    (rec / "walkthroughs").mkdir(parents=True)
    (rec / "prompts" / "pending").mkdir(parents=True)
    (rec / "research").mkdir(parents=True)

    (rec / "plans" / "pending" / "20261101-demo-01-pl1001-plan.ipd.md").write_text(
        "# Plan\n\n"
        "- Id: pl1001\n"
        "- Status: approved\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Kind: child\n"
        "- Item-Dependencies: none\n"
        "- Short-Description: Plan description\n\n"
        "## Goal\n\nTest census.\n",
        encoding="utf-8",
    )
    (rec / "walkthroughs" / "20261101-demo-01-wt1001-walk.md").write_text(
        "# Walkthrough\n\n- Id: wt1001\n- Short-Description: Walk description\n\n## Notes\n\nOk.\n",
        encoding="utf-8",
    )
    # Staged prompt with no leading aw-prompt comment
    (
        rec
        / "prompts"
        / "pending"
        / "20261101-demo-01-pr1001-no-comment.agy.gemini38.prompt.md"
    ).write_text("# Prompt body without leading comment\n", encoding="utf-8")
    # Research with non-leading aw-prompt comment (body prose per OQ-04)
    (rec / "research" / "20261101-demo-01-rs1001-study.findings.md").write_text(
        "---\n"
        "id: rs1001\n"
        "status: complete\n"
        "created: 2026-11-01\n"
        "kind: findings\n"
        "set: demo\n"
        "order: 1\n"
        "summary: Study summary\n"
        "short-description: Research description\n"
        "---\n\n"
        "# Study\n\n"
        "<!-- aw-prompt: Id: pr9999 | Status: executed -->\n",
        encoding="utf-8",
    )
    _commit_all(repo, "seed no-sidecar census fixture")

    dry = m0001_metadata_v2.run(repo, apply=False)
    assert dry["status"] == "dry_run"
    census = dry["census"]
    assert census["sidecar_status"] == "no sidecar (none expected)"
    assert census["orphan_counts"] == {}
    assert census["orphan_record_count"] == 0
    assert census["unknown_field_refusal_count"] == 0
    assert census["unparseable_value_refusal_count"] == 0
    assert census["excluded_templates"] == []
    assert census["plan_role_counts"] == {"child": 1}
    assert census["absent_kind_count"] == 0
    assert census["prompts_without_comment"] == [
        "prompts/pending/20261101-demo-01-pr1001-no-comment.agy.gemini38.prompt.md"
    ]
    assert census["non_leading_research_prompt_comments"] == [
        "research/20261101-demo-01-rs1001-study.findings.md"
    ]
    # Prompt without comment lacks short_description until describer runs
    assert census["with_description_count"] == 3
    assert census["without_description_count"] == 1
    assert dry["round_trip"]["round_trip_passed"] is True

    formatted = m0001_verify.format_census(census)
    assert "no sidecar (none expected)" in formatted
    assert "Unknown-field refusals: 0" in formatted


def test_census_refuses_unknown_field_unparseable_dep_and_missing_description_on_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Step-6 --apply refuses unknown-field, unparseable Item-Dependencies, and missing descriptions."""
    repo = _init_git_repo(tmp_path, monkeypatch, name="census_refusals")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "pending").mkdir(parents=True)
    (rec / "walkthroughs").mkdir(parents=True)

    plan = rec / "plans" / "pending" / "20261101-demo-01-pl2001-bad.ipd.md"
    plan.write_text(
        "# Plan\n\n"
        "- Id: pl2001\n"
        "- Status: approved\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Mystery-Key: unexpected\n"
        "- Item-Dependencies: totally-broken-grammar\n\n"
        "## Goal\n\nBroken.\n",
        encoding="utf-8",
    )
    walk = rec / "walkthroughs" / "20261101-demo-01-wt2001-walk.md"
    walk.write_text(
        "# Walk\n\n- Id: wt2001\n\n## Notes\n\nNo description.\n", encoding="utf-8"
    )
    _commit_all(repo, "seed census refusal fixture")

    dry = m0001_metadata_v2.run(repo, apply=False)
    census = dry["census"]
    assert census["unknown_field_refusal_count"] == 1
    assert census["unparseable_value_refusal_count"] == 1
    assert census["without_description_count"] == 2
    assert {r["kind"] for r in census["refusals"]} == {
        "unknown-field",
        "unparseable-value",
    }

    with pytest.raises(layout_migration.PreflightGateError) as exc_refuse:
        m0001_metadata_v2.run(repo, apply=True)
    msg = str(exc_refuse.value)
    assert "unknown-field" in msg
    assert "unparseable-value" in msg
    assert "short_description" in msg
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""


# --------------------------------------------------------------------------------------
# AC-10 & AC-16: Long history line, control char, writer refusal, and sanitizer refusal
# --------------------------------------------------------------------------------------


def test_roundtrip_long_and_control_char_history_lines_and_writer_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-10: >4300 char & control-char history lines round-trip byte-for-byte; writer refuses same."""
    repo = _init_git_repo(tmp_path, monkeypatch, name="rt_long_ctrl")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "executed").mkdir(parents=True)

    long_tail = "L" * (attention_contract.MAX_PROSE_DESCRIPTIVE_LEN + 250)
    long_line = f"- 2026-11-01 executed (tester): {long_tail}"
    ctrl_line = "- 2026-11-02 note (tester): bell \x07 and ansi \x1b[31mred\x1b[0m"

    plan = rec / "plans" / "executed" / "20261101-demo-01-pl3001-long-ctrl.ipd.md"
    plan.write_text(
        "# Plan\n\n"
        "- Id: pl3001\n"
        "- Status: executed\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Note: Preserved body note\n"
        "- Short-Description: Long history test\n\n"
        "## Goal\n\nTest byte-for-byte round trip.\n\n"
        "## Workflow history\n\n"
        f"{long_line}\n"
        f"{ctrl_line}\n",
        encoding="utf-8",
    )
    _commit_all(repo, "seed long and control-char history fixture")

    dry = m0001_metadata_v2.run(repo, apply=False)
    assert dry["round_trip"]["passed"] is True
    assert dry["round_trip"]["replayed_count"] == 1

    # Post-cutover writer validation (migration_import=False) refuses the same long line & ctrl line.
    log_path = (
        Path(dry["scratch_dir"]) / "repo" / ".aw" / "records" / "meta" / "pl3001.jsonl"
    )
    events = _read_jsonl(log_path)
    hist_lines = [
        ev["line"]
        for ev in events
        if ev.get("op") == "legacy" and ev.get("source") == "history"
    ]
    assert hist_lines == [long_line, ctrl_line]

    with pytest.raises(ValueError):
        artifact_meta.validate_new_events(
            "ipd",
            events,
            records_root=rec,
            repo_root=repo,
            migration_import=False,
        )


def test_roundtrip_leak_sanitizer_fail_refuses_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-16 / step 6: planted home-directory path fails leak_sanitizer and refuses --apply."""
    repo = _init_git_repo(tmp_path, monkeypatch, name="rt_leak")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "pending").mkdir(parents=True)

    planted_leak = "/ho" + "me/janedoe/secret/file.txt"
    (rec / "plans" / "pending" / "20261101-demo-01-pl4001-leak.ipd.md").write_text(
        "# Plan\n\n"
        "- Id: pl4001\n"
        "- Status: approved\n"
        "- Set: demo\n"
        "- Order: 1\n"
        f"- Note: leaked path {planted_leak}\n"
        "- Short-Description: Leak test plan\n\n"
        "## Goal\n\nBody.\n",
        encoding="utf-8",
    )
    _commit_all(repo, "seed leak fixture")

    dry = m0001_metadata_v2.run(repo, apply=False)
    assert dry["round_trip"]["round_trip_passed"] is True
    assert dry["round_trip"]["leak_fail_count"] >= 1
    assert dry["round_trip"]["passed"] is False

    with pytest.raises(layout_migration.PreflightGateError, match="leak_sanitizer"):
        m0001_metadata_v2.run(repo, apply=True)


# --------------------------------------------------------------------------------------
# Step-6 stamp + rollback, step-7 hook-verified commit + marker consumption, idempotence
# --------------------------------------------------------------------------------------


def test_step6_stamp_and_rollback_restores_project_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Step-6 writes metadata_schema=2; rollback restores pre-apply project.json bytes or absence."""
    # Case A: pre-existing project.json restored byte-for-byte
    repo_a = _init_git_repo(tmp_path, monkeypatch, name="stamp_rb_existing")
    cfg_a = repo_a / ".aw" / "config"
    cfg_a.mkdir(parents=True)
    proj_a = cfg_a / "project.json"
    orig_proj_bytes = (
        json.dumps(
            {"schema_version": 2, "preset": "private-target", "role": "target"},
            indent=2,
        )
        + "\n"
    )
    proj_a.write_text(orig_proj_bytes, encoding="utf-8")
    (repo_a / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    (
        repo_a
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-pl5001-p.ipd.md"
    ).write_text(
        "# Plan\n\n- Id: pl5001\n- Status: approved\n- Set: demo\n- Order: 1\n- Short-Description: Desc\n",
        encoding="utf-8",
    )
    _commit_all(repo_a, "seed existing project.json fixture")

    res_a = m0001_metadata_v2.run(repo_a, apply=True, commit=False)
    assert res_a["status"] == "applied"
    assert chain.read_metadata_schema(repo_a) == 2
    assert ".aw/config/project.json" in res_a["staged_paths"]

    rb_a = m0001_metadata_v2.rollback(repo_a)
    assert rb_a["status"] == "rolled_back"
    assert proj_a.read_text(encoding="utf-8") == orig_proj_bytes
    assert _git(repo_a, "status", "--porcelain").stdout.strip() == ""

    # Case B: absent project.json unlinked on rollback
    repo_b = _init_git_repo(tmp_path, monkeypatch, name="stamp_rb_absent")
    proj_b = repo_b / ".aw" / "config" / "project.json"
    assert not proj_b.exists()
    (repo_b / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    (
        repo_b
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-pl5002-p.ipd.md"
    ).write_text(
        "# Plan\n\n- Id: pl5002\n- Status: approved\n- Set: demo\n- Order: 1\n- Short-Description: Desc\n",
        encoding="utf-8",
    )
    _commit_all(repo_b, "seed absent project.json fixture")

    res_b = m0001_metadata_v2.run(repo_b, apply=True, commit=False)
    assert res_b["status"] == "applied"
    assert chain.read_metadata_schema(repo_b) == 2
    assert proj_b.is_file()

    m0001_metadata_v2.rollback(repo_b)
    assert not proj_b.exists()
    assert _git(repo_b, "status", "--porcelain").stdout.strip() == ""


def test_step7_commit_with_installed_precommit_hooks_and_second_apply_idempotence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E2E apply(commit=True) with .git/hooks/pre-commit (commit_isolated) + marker consumption + no-op re-apply."""
    repo = _init_git_repo(tmp_path, monkeypatch, name="e2e_hooks_commit")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "executed").mkdir(parents=True)
    (rec / "backlog" / "done").mkdir(parents=True)
    (rec / "config").mkdir(parents=True, exist_ok=True)
    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps({"schema_version": 2, "preset": "private-target"}, indent=2) + "\n",
        encoding="utf-8",
    )

    # Legacy-timestamp executed plan + release-blocking done backlog item
    exec_plan = rec / "plans" / "executed" / "20261101-0900-01-legacy-exec.ipd.md"
    exec_plan.write_text(
        "# IPD: Legacy Executed\n\n"
        "- Id: pl9001\n"
        "- Status: executed\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Short-Description: Executed legacy plan\n\n"
        "## Workflow history\n\n"
        "- 2026-11-01 executed (tester): done\n",
        encoding="utf-8",
    )
    done_bk = rec / "backlog" / "done" / "20261101-demo-01-bk9001-blocking.backlog.md"
    done_bk.write_text(
        "- Id: bk9001\n"
        "- Status: done\n"
        "- Set: demo\n"
        "- Blocks-Release: next\n"
        "- Summary: Release-blocking item\n"
        "- Short-Description: Blocking done item\n",
        encoding="utf-8",
    )
    _commit_all(repo, "seed executed plan and blocking done backlog")

    # Sidecar for bk9001
    (rec / "history.jsonl").write_text(
        json.dumps(
            {
                "id6": "bk9001",
                "date": "20261101",
                "tree": "backlog",
                "workflow": "backlog",
                "actor": "tester",
                "message": "done",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _install_precommit_gates_hook(repo)
    head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()

    applied = m0001_metadata_v2.run(repo, apply=True, commit=True)
    assert applied["status"] == "applied"
    assert applied["commit"]["status"] == git_commit_helper.STATUS_COMMITTED
    head_after = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head_after != head_before
    assert chain.read_metadata_schema(repo) == 2

    # Marker consumed; working tree clean
    journal_dir = repo / ".aw" / "state" / "durable" / "migrations" / "m0001"
    assert not (journal_dir / "terminal_commit_marker.json").exists()
    jdata = json.loads((journal_dir / "journal.json").read_text(encoding="utf-8"))
    assert jdata["terminal_commit_marker"] is None
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""

    # Second apply is an immediate idempotent no-op with zero writes or commits
    second = m0001_metadata_v2.run(repo, apply=True, commit=True)
    assert second["status"] == "already_migrated"
    assert second["message"] == "metadata_schema is 2; nothing to do"
    assert second["applied"] is False
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == head_after

    # CLI also prints "metadata_schema is 2; nothing to do"
    old_cwd = os.getcwd()
    try:
        os.chdir(repo)
        from io import StringIO
        import contextlib

        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.main(["migrate", "metadata", "--apply"])
        assert rc == 0
        assert "metadata_schema is 2; nothing to do" in buf.getvalue()
    finally:
        os.chdir(old_cwd)


def test_roundtrip_step3_rewritten_citations_and_prompt_hr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Step-3 rewrites in fields/body round-trip while protected history stays pre-Step-3 verbatim; body --- in prompts is allowed."""
    repo = _init_git_repo(tmp_path, monkeypatch, name="rt_step3_hr")
    rec = repo / ".aw" / "records"
    (rec / "specs" / "implemented").mkdir(parents=True)
    (rec / "plans" / "executed").mkdir(parents=True)
    (rec / "prompts" / "executed").mkdir(parents=True)

    legacy_spec = "20260802-1904-01-sample-spec.spec.md"
    (rec / "specs" / "implemented" / legacy_spec).write_text(
        "# Spec: Sample\n\n"
        "- Status: implemented\n"
        "- Priority: medium\n"
        "- Summary: Legacy spec without id.\n"
        "- Short-Description: Sample legacy spec\n\n"
        "## Body\n\nSpec body.\n",
        encoding="utf-8",
    )
    (rec / "plans" / "executed" / "20261101-demo-01-pl5555-citer.ipd.md").write_text(
        "# IPD: Citer\n\n"
        "- Id: pl5555\n"
        "- Status: executed\n"
        "- Set: demo\n"
        "- Order: 1\n"
        f"- Concern: Implements `.aw/records/specs/implemented/{legacy_spec}` cleanly.\n"
        f"- Scope-Paths: agent_workflows/cli.py, .aw/records/specs/implemented/{legacy_spec}\n"
        "- Short-Description: Plan citing legacy spec\n\n"
        "## Goal\n\nVerify Step-3 citation rewrite round-trip.\n\n"
        "## Workflow history\n\n"
        f"- 2026-11-01 executed (tester): covered .aw/records/specs/implemented/{legacy_spec}\n",
        encoding="utf-8",
    )
    (
        rec / "prompts" / "executed" / "20261101-demo-01-pr5555-hr-body.prompt.md"
    ).write_text(
        "<!-- aw-prompt: Kind: research | Id: pr5555 | Status: executed | Created: 2026-11-01 | Concerns: hr test -->\n"
        "# Prompt with thematic break\n\n"
        "Intro paragraph.\n\n"
        "---\n\n"
        "## Section 1\n\n"
        "Body after horizontal rule.\n",
        encoding="utf-8",
    )
    _commit_all(repo, "seed legacy spec citation + prompt horizontal rule fixture")

    dry = m0001_metadata_v2.run(repo, apply=False)
    assert dry["round_trip"]["round_trip_passed"] is True, dry["round_trip"]["errors"]
    assert dry["round_trip"]["replayed_count"] == 3

    # History log op keeps pre-Step-3 legacy citation verbatim while scope_paths uses new name.
    log_path = (
        Path(dry["scratch_dir"]) / "repo" / ".aw" / "records" / "meta" / "pl5555.jsonl"
    )
    events = _read_jsonl(log_path)
    hist_lines = [
        ev["line"]
        for ev in events
        if ev.get("op") == "legacy" and ev.get("source") == "history"
    ]
    assert any(legacy_spec in line for line in hist_lines)

    new_spec_name = Path(dry["rename_map"][f"specs/implemented/{legacy_spec}"]).name
    replayed_state, _, _, _ = artifact_meta.replay(
        "pl5555",
        "ipd",
        log_path.read_text(encoding="utf-8").splitlines(keepends=True),
        records_root=Path(dry["scratch_dir"]) / "repo" / ".aw" / "records",
    )
    assert any(new_spec_name in sp for sp in replayed_state.fields["scope_paths"])
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""

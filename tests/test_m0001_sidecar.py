"""Outcome tests for m0001 step-2 sidecar expectedness, queueing, orphans, and cleanup.

IPD vxevph (E-04, E-06 / V-04, V-06). Spec 4sd62s Sections 5.2 step 2, 5.2a item 5,
and AC-30 cases (1) and (2).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agent_workflows import artifact_meta, layout_migration
from agent_workflows.migrations import m0001_metadata_v2

pytestmark = pytest.mark.core


_DEFAULT_GITIGNORE = (
    "/state/\n"
    "/config/local.json\n"
    "records/history.jsonl\n"
    "records/plans/INDEX.json\n"
    "records/research/INDEX.md\n"
)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_git_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, name: str = "repo"
) -> Path:
    aw_home = tmp_path / f"aw_home_{name}"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))

    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    return repo


# --------------------------------------------------------------------------------------
# Step 2 sidecar expectedness and 4sd62s 5.2a item 5 ("no sidecar (none expected)")
# --------------------------------------------------------------------------------------


def test_sidecar_not_expected_when_no_id6_spec_or_backlog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fixture with no id6 spec or backlog item reports 'no sidecar (none expected)'."""
    repo = _init_git_repo(tmp_path, monkeypatch, name="no_sidecar_expected")
    rec_root = repo / ".aw" / "records"
    (rec_root / "specs" / "implemented").mkdir(parents=True)
    (rec_root / "plans" / "pending").mkdir(parents=True)
    (repo / ".aw" / ".gitignore").write_text(_DEFAULT_GITIGNORE, encoding="utf-8")

    # Legacy-timestamp spec whose slug starts with a 6-letter word ('agents') has NO id6
    # because _LEGACY_TIMESTAMP_RE must be tested before parse_clustered (5.2 step 3).
    legacy_spec = (
        rec_root / "specs" / "implemented" / "20260818-1525-02-agents-legacy-spec.md"
    )
    legacy_spec.write_text(
        "# Spec: Legacy spec without id6\n\n- Status: implemented\n",
        encoding="utf-8",
    )
    # Plans with an id6 do NOT trigger sidecar expectedness (only specs and backlog items do).
    plan = rec_root / "plans" / "pending" / "20261101-demo-01-pl0001-plan-only.ipd.md"
    plan.write_text(
        "# IPD: Plan only\n\n- Id: pl0001\n- Status: approved\n- Set: demo\n- Order: 1\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".aw/.gitignore", ".aw/records")
    _git(repo, "commit", "-m", "init legacy spec and plan without sidecar")

    report = m0001_metadata_v2.run(repo, apply=False)
    assert report["status"] == "dry_run"
    assert report["sidecar"]["present"] is False
    assert report["sidecar"]["expected"] is False
    assert report["sidecar"]["status"] == "no sidecar (none expected)"
    assert report["orphan_counts"] == {}
    assert report["orphan_export_path"] is None


def test_sidecar_expected_missing_refusal_and_force_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fixture with an id6 spec or backlog item and no sidecar refuses unless force=True."""
    repo = _init_git_repo(tmp_path, monkeypatch, name="missing_expected_sidecar")
    rec_root = repo / ".aw" / "records"
    (rec_root / "specs" / "approved").mkdir(parents=True)
    (repo / ".aw" / ".gitignore").write_text(_DEFAULT_GITIGNORE, encoding="utf-8")

    spec = (
        rec_root
        / "specs"
        / "approved"
        / "20261101-demo-01-sp0001-expected-sidecar.spec.md"
    )
    spec.write_text(
        "# Spec: Expected sidecar\n\n- Id: sp0001\n- Status: approved\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".aw/.gitignore", ".aw/records")
    _git(repo, "commit", "-m", "init id6 spec")

    # Refuses without --force, and --force-worktree alone does not override step 2
    with pytest.raises(layout_migration.PreflightGateError, match="history.jsonl"):
        m0001_metadata_v2.run(repo, apply=False, force=False, force_worktree=True)
    assert not (repo / ".aw" / "state" / "durable" / "migrations" / "m0001").exists()

    # Passes with --force and names the sidecar override
    report = m0001_metadata_v2.run(repo, apply=False, force=True)
    assert report["status"] == "dry_run"
    assert report["sidecar"]["expected"] is True
    assert report["sidecar"]["present"] is False
    assert any(o["condition"] == "SIDECAR" for o in report["preflight"]["overridden"])


# --------------------------------------------------------------------------------------
# AC-30 case (1): status, repeated inline history, rename/group, and orphan export
# --------------------------------------------------------------------------------------


def test_sidecar_classification_queueing_and_orphan_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-30 case (1): status, repeated inline, rename/group, and orphan sidecar records."""
    repo = _init_git_repo(tmp_path, monkeypatch, name="ac30_case1")
    rec_root = repo / ".aw" / "records"
    (rec_root / "specs" / "approved").mkdir(parents=True)
    (rec_root / "backlog" / "open").mkdir(parents=True)
    (rec_root / "research").mkdir(parents=True)
    (rec_root / "prompts" / "pending").mkdir(parents=True)
    (rec_root / "comms" / "inbox").mkdir(parents=True)
    (repo / ".aw" / ".gitignore").write_text(_DEFAULT_GITIGNORE, encoding="utf-8")

    spec_path = (
        rec_root / "specs" / "approved" / "20261101-demo-01-sp1001-tracked-spec.spec.md"
    )
    spec_path.write_text(
        "# Spec: Tracked spec\n\n"
        "- Id: sp1001\n"
        "- Status: approved\n\n"
        "## Workflow history\n\n"
        "- 2026-11-02 approved (alice): human approved\n",
        encoding="utf-8",
    )
    bk_path = (
        rec_root
        / "backlog"
        / "open"
        / "20261101-demo-01-bk1001-tracked-item.backlog.md"
    )
    bk_path.write_text(
        "- Id: bk1001\n- Status: open\n- Summary: Tracked backlog item\n",
        encoding="utf-8",
    )
    (
        rec_root / "research" / "20261101-demo-01-rs1001-study.opus.findings.md"
    ).write_text(
        "---\nid: rs1001\nkind: findings\n---\n# Research study\n",
        encoding="utf-8",
    )
    (rec_root / "prompts" / "pending" / "20261101-1200-01-legacy-prompt.md").write_text(
        "<!-- aw-prompt: Id: pr1001 | Kind: review -->\n# Prompt\n",
        encoding="utf-8",
    )
    # Excluded comms file whose Id must not enter the tracked id6 set
    (rec_root / "comms" / "inbox" / "20261101-1200-01-msg.md").write_text(
        "- Id: cm1001\n\nMessage\n",
        encoding="utf-8",
    )

    _git(repo, "add", ".aw/.gitignore", ".aw/records")
    _git(repo, "commit", "-m", "init tracked records")

    rec_status = {
        "id6": "bk1001",
        "date": "20261101",
        "tree": "backlog",
        "workflow": "backlog",
        "actor": "tester",
        "message": "created",
    }
    rec_repeat_inline = {
        "id6": "sp1001",
        "date": "20261102",
        "tree": "specs",
        "workflow": "approved",
        "actor": "alice",
        "message": "human approved",
    }
    rec_rename = {
        "id6": "sp1001",
        "date": "20261103",
        "tree": "specs",
        "workflow": "rename",
        "actor": "tester",
        "message": "renamed",
        "verb": "rename",
        "from_name": "old.spec.md",
        "to_name": "20261101-demo-01-sp1001-tracked-spec.spec.md",
        "key_kind": "id6",
    }
    rec_research = {
        "id6": "rs1001",
        "date": "20261103",
        "tree": "research",
        "workflow": "research",
        "actor": "tester",
        "message": "adopted",
    }
    rec_prompt = {
        "id6": "pr1001",
        "date": "20261103",
        "tree": "prompts",
        "workflow": "prompts",
        "actor": "tester",
        "message": "staged",
    }
    rec_orphan = {
        "id6": "zz9999",
        "date": "20261015",
        "tree": "backlog",
        "workflow": "done",
        "actor": "tester",
        "message": "purged item history",
    }
    rec_synthetic = {
        "id6": "cm1001",
        "date": "20261016",
        "tree": "plans",
        "workflow": "rename",
        "actor": "tester",
        "message": "synthetic key",
        "key_kind": "synthetic",
    }

    sidecar_path = rec_root / "history.jsonl"
    sidecar_path.write_text(
        "".join(
            json.dumps(r) + "\n"
            for r in (
                rec_status,
                rec_repeat_inline,
                rec_rename,
                rec_research,
                rec_prompt,
                rec_orphan,
                rec_synthetic,
            )
        ),
        encoding="utf-8",
    )

    report = m0001_metadata_v2.run(repo, apply=False)
    assert report["sidecar"]["present"] is True
    assert report["sidecar"]["record_count"] == 7

    queued = report["sidecar_events"]
    assert set(queued.keys()) == {"bk1001", "sp1001", "rs1001", "pr1001"}
    assert "zz9999" not in queued
    assert "cm1001" not in queued

    bk_events = queued["bk1001"]
    assert len(bk_events) == 1
    assert bk_events[0] == {
        "op": "legacy",
        "source": "sidecar",
        "observed_day": "20261101",
        "position": 0,
        "ordering_confidence": "unknown",
        "line": rec_status,
    }

    sp_events = queued["sp1001"]
    assert len(sp_events) == 2
    assert sp_events[0]["op"] == "legacy"
    assert sp_events[0]["source"] == "sidecar"
    assert sp_events[0]["observed_day"] == "20261102"
    assert sp_events[0]["position"] == 1
    assert sp_events[0]["line"] == rec_repeat_inline
    assert sp_events[1]["op"] == "legacy"
    assert sp_events[1]["source"] == "sidecar"
    assert sp_events[1]["observed_day"] == "20261103"
    assert sp_events[1]["position"] == 2
    assert sp_events[1]["line"] == rec_rename

    # Conform every queued payload key to OP_PAYLOAD_SCHEMAS["legacy"]
    allowed_keys = set(artifact_meta.OP_PAYLOAD_SCHEMAS["legacy"]) | {"op"}
    for ev_list in queued.values():
        for ev in ev_list:
            assert set(ev.keys()).issubset(allowed_keys)

    # Inline history from artifact_meta.load_legacy_artifact remains untouched with distinct source
    _, inline_hist = artifact_meta.load_legacy_artifact(spec_path, rec_root)
    assert len(inline_hist) == 1
    assert "human approved" in inline_hist[0]["line"]

    # Orphan and synthetic records written to sidecar-orphans.jsonl with no meta/<id6>.jsonl
    assert report["orphan_counts"] == {"zz9999": 1, "cm1001": 1}
    orphan_file = Path(report["orphan_export_path"])
    assert orphan_file.name == "sidecar-orphans.jsonl"
    orphan_lines = [
        json.loads(ln) for ln in orphan_file.read_text(encoding="utf-8").splitlines()
    ]
    assert orphan_lines == [rec_orphan, rec_synthetic]
    assert not (rec_root / "meta" / "zz9999.jsonl").exists()
    assert not (rec_root / "meta" / "cm1001.jsonl").exists()


# --------------------------------------------------------------------------------------
# AC-30 case (2) target-repo half: move sidecar, clean .aw/.gitignore, and rollback
# --------------------------------------------------------------------------------------


def test_sidecar_apply_moves_history_cleans_gitignore_and_rollback_restores(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-30 case (2): apply moves sidecar & strips ignore line; rollback restores both."""
    repo = _init_git_repo(tmp_path, monkeypatch, name="ac30_case2")
    rec_root = repo / ".aw" / "records"
    (rec_root / "backlog" / "open").mkdir(parents=True)
    gitignore_path = repo / ".aw" / ".gitignore"
    orig_gitignore = (
        "/state/\n"
        "/config/local.json\n"
        "/records/history.jsonl\n"
        "records/plans/INDEX.json\n"
        "/worktrees/\n"
    )
    gitignore_path.write_text(orig_gitignore, encoding="utf-8")

    (
        rec_root / "backlog" / "open" / "20261101-demo-01-bk2001-item.backlog.md"
    ).write_text(
        "- Id: bk2001\n- Status: open\n- Summary: Item\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".aw/.gitignore", ".aw/records")
    _git(repo, "commit", "-m", "init ac30 case 2")

    sidecar_path = rec_root / "history.jsonl"
    orig_sidecar = (
        json.dumps(
            {
                "id6": "bk2001",
                "date": "20261101",
                "tree": "backlog",
                "workflow": "backlog",
                "actor": "tester",
                "message": "created",
            }
        )
        + "\n"
    )
    sidecar_path.write_text(orig_sidecar, encoding="utf-8")

    res = m0001_metadata_v2.run(repo, apply=True)
    assert res["status"] == "applied"

    imported = (
        repo
        / ".aw"
        / "state"
        / "durable"
        / "migrations"
        / "m0001"
        / "history.jsonl.imported"
    )
    assert imported.is_file()
    assert imported.read_text(encoding="utf-8") == orig_sidecar
    assert not sidecar_path.exists()

    # git status --porcelain --ignored shows no records/history.jsonl anywhere in working tree
    st = _git(repo, "status", "--porcelain", "--ignored")
    assert "history.jsonl" not in st.stdout

    # .aw/.gitignore stripped the sidecar line (step 2) and INDEX line (step 5)
    # while preserving non-migration siblings & trailing newline
    new_gitignore = gitignore_path.read_text(encoding="utf-8")
    assert new_gitignore == ("/state/\n/config/local.json\n/worktrees/\n")
    assert new_gitignore.endswith("\n")

    # Rollback restores both files byte-for-byte
    rb = m0001_metadata_v2.rollback(repo)
    assert rb["status"] == "rolled_back"
    assert sidecar_path.read_text(encoding="utf-8") == orig_sidecar
    assert gitignore_path.read_text(encoding="utf-8") == orig_gitignore
    assert not imported.exists()

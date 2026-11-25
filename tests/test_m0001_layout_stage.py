"""Behavioral fixture tests for m0001 embedded stage-one layout migration, external backends, and cross-stage rollback.

IPD bv4kkj (E-01..E-05 / V-01..V-05). Spec 4sd62s Sections 5.1, 5.2, 5.2a items 2, 3, 5, and AC-18.
Every test operates on isolated ``tmp_path`` git repositories with zero source-code inspection.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

import pytest

from agent_workflows import (
    artifact_meta,
    attention,
    cli,
    layout_migration,
    project_context,
)
from agent_workflows.migrations import chain, m0001_metadata_v2, m0001_verify
from tests import migration_corpus

pytestmark = pytest.mark.core


def _clean_git_env() -> Dict[str, str]:
    env = dict(os.environ)
    for k in list(env):
        if k.startswith("GIT_"):
            del env[k]
    return env


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=_clean_git_env(),
        capture_output=True,
        text=True,
        check=True,
    )


def _tree_sha256(
    root: Path, *, ignore_prefixes: Tuple[str, ...] = (".git/", ".aw/state/")
) -> Dict[str, str]:
    digests: Dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_dir() and not p.is_symlink():
            continue
        rel = p.relative_to(root).as_posix()
        if any(rel.startswith(pref) for pref in ignore_prefixes):
            continue
        if p.is_symlink():
            digests[rel] = f"symlink:{os.readlink(p)}"
        else:
            digests[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return digests


def _run_cli_inproc(
    repo: Path,
    argv: Sequence[str],
    *,
    aw_home: Path,
) -> Tuple[int, str, str]:
    old_cwd = os.getcwd()
    old_env = dict(os.environ)
    old_argv = list(sys.argv)
    out = io.StringIO()
    err = io.StringIO()
    try:
        os.environ["AW_HOME"] = str(aw_home)
        os.environ["HOME"] = str(aw_home)
        os.environ["XDG_CONFIG_HOME"] = str(aw_home / "xdg")
        os.environ["NO_COLOR"] = "1"
        os.environ["AW_NONINTERACTIVE"] = "1"
        os.chdir(repo)
        sys.argv = ["agent-workflows", *argv]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = cli.main(list(argv))
            except SystemExit as exc:
                rc = (
                    int(exc.code)
                    if isinstance(exc.code, int)
                    else (1 if exc.code else 0)
                )
        return rc, out.getvalue(), err.getvalue()
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
        os.environ.clear()
        os.environ.update(old_env)


def _seed_journal_descriptions(
    repo: Path, text: str = "Synthetic record summary."
) -> None:
    """Populate ``journal.json['descriptions']`` after a dry run for CLI --apply tests."""
    jpath = repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    data = json.loads(jpath.read_text(encoding="utf-8"))
    descs = dict(data.get("descriptions") or {})
    records_root = Path(data["records_root"])
    scratch_recs = Path(jpath.parent / "scratch" / "repo" / ".aw" / "records")
    scan_dir = scratch_recs if scratch_recs.is_dir() else records_root
    if scan_dir.is_dir():
        for md in sorted(scan_dir.rglob("*.md")):
            rel = md.relative_to(scan_dir).as_posix()
            descs.setdefault(rel, text)
    for old_rel, id6 in (data.get("minted_ids") or {}).items():
        descs.setdefault(id6, text)
        descs.setdefault(old_rel, text)
    for old_rel, new_rel in (data.get("rename_map") or {}).items():
        descs.setdefault(new_rel, text)
        descs.setdefault(old_rel, text)
    data["descriptions"] = descs
    jpath.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _stub_describer(*_args: Any) -> str:
    return "Synthetic migrated record description."


# --------------------------------------------------------------------------------------
# E-01 / V-01: embedded stage-one planning, scratch projection, apply, and rollback
# --------------------------------------------------------------------------------------


def test_stage1_embedded_plan_backend_selection_and_scratch_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Embedded stage-one plan discovers .agents/ via _default_roots, picks backend, and projects cleanly."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    dest = tmp_path / "legacy_a"
    dest.mkdir()
    repo = migration_corpus.legacy_agents_layout(dest)
    before = _tree_sha256(repo, ignore_prefixes=(".git/",))

    mgr = layout_migration.MigrationManager(str(repo), aw_home=str(aw_home))
    plan_doc = mgr.plan_embedded_stage_one()
    assert plan_doc["valid"] is True
    assert plan_doc["target_backend"] == "repository"
    assert plan_doc["planned_count"] >= 7

    scratch = tmp_path / "scratch_out"
    proj = mgr.project_stage_one_to_scratch(plan_doc, scratch, backfill_ids=False)
    assert proj["status"] == "planned"
    assert proj["planned_count"] == plan_doc["planned_count"]
    assert (scratch / ".aw" / "records" / "plans" / "pending").is_dir()
    assert (
        scratch / ".aw" / "records" / "specs" / "20260706-0900-01-core-spec.spec.md"
    ).is_file()
    assert (scratch / ".aw" / "system" / "workflows" / "demo" / "demo.md").is_file()

    # Live checkout untouched and git status clean
    assert _tree_sha256(repo, ignore_prefixes=(".git/",)) == before
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""


def test_stage1_embedded_apply_backfill_false_and_snapshot_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Embedded apply keeps caller keys/lock, mints 0 plan IDs, and snapshot rollback restores bytes."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    dest = tmp_path / "mixed_b"
    dest.mkdir()
    repo = migration_corpus.mixed_layout(dest)

    # Seed pre-existing config.json, project.json, .aw/.gitignore, and an id-less .agents plan
    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    orig_cfg = b'{\n  "custom_key": "keep"\n}\n'
    orig_proj = b'{\n  "schema_version": 2,\n  "custom_proj": true\n}\n'
    orig_gi = b"/state/\n# custom comment\n"
    (cfg_dir / "config.json").write_bytes(orig_cfg)
    (cfg_dir / "project.json").write_bytes(orig_proj)
    (repo / ".aw" / ".gitignore").write_bytes(orig_gi)
    idless_plan = repo / ".agents" / "plans" / "pending" / "20260711-0900-01-idless.md"
    idless_plan.parent.mkdir(parents=True, exist_ok=True)
    idless_plan.write_text("# IPD: No Id Yet\n\n- Status: draft\n", encoding="utf-8")
    _git(repo, "add", ".aw", ".agents")
    _git(repo, "commit", "-q", "-m", "seed pre-existing configs and idless plan")

    before = _tree_sha256(repo)
    jdir = repo / ".aw" / "state" / "durable" / "migrations" / "m0001"
    mgr = layout_migration.MigrationManager(str(repo), aw_home=str(aw_home))
    mgr.transaction_file = jdir / "journal.json"
    mgr.lock_file = jdir / "writer.lock"
    mgr._acquire_lock("caller-tx-1")
    try:
        tx_data: Dict[str, Any] = {
            "migration_id": "m0001",
            "transaction_id": "caller-tx-1",
            "status": "applying",
            "timestamps": {"started_at": "2026-11-17T00:00:00Z", "updated_at": ""},
            "minted_ids": {"sentinel": "abc123"},
        }
        ls = mgr.apply_embedded_stage_one(
            tx_data, backfill_ids=False, caller_holds_lock=True
        )
        assert ls["status"] == "completed"
        assert ls["id_backfill"] == []
        # Caller top-level keys and lock are untouched
        assert tx_data["migration_id"] == "m0001"
        assert tx_data["transaction_id"] == "caller-tx-1"
        assert tx_data["status"] == "applying"
        assert tx_data["minted_ids"] == {"sentinel": "abc123"}
        assert mgr.lock_file.is_file()

        moved_idless = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260711-0900-01-idless.md"
        )
        assert moved_idless.is_file()
        assert "- Id:" not in moved_idless.read_text(encoding="utf-8")

        rb = mgr.rollback_embedded_stage_one(tx_data, caller_holds_lock=True)
        assert rb["status"] == "rolled_back"
        assert mgr.lock_file.is_file()
        assert not mgr.switch_receipt_file.exists()
        assert not mgr.retention_manifest_file.exists()
        assert (cfg_dir / "config.json").read_bytes() == orig_cfg
        assert (cfg_dir / "project.json").read_bytes() == orig_proj
        assert (repo / ".aw" / ".gitignore").read_bytes() == orig_gi
        assert _tree_sha256(repo) == before
        assert _git(repo, "status", "--porcelain").stdout.strip() == ""
    finally:
        mgr._release_lock()


def test_stage1_embedded_preserves_configured_companion_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Configured companion backend is preserved instead of forced to repository."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    dest = tmp_path / "comp"
    dest.mkdir()
    target = migration_corpus.companion_backend(dest)
    plan_file = target / ".agents" / "plans" / "pending" / "20260825-comp.md"
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text("# IPD: Comp\n\n- Status: approved\n", encoding="utf-8")
    _git(target, "add", ".agents")
    _git(target, "commit", "-q", "-m", "add agents plan")

    mgr = layout_migration.MigrationManager(str(target), aw_home=str(aw_home))
    plan_doc = mgr.plan_embedded_stage_one()
    assert plan_doc["target_backend"] == "companion"


# --------------------------------------------------------------------------------------
# E-02..E-05 / V-02..V-05: two-stage dry run, apply, rollback, resume, and external roots
# --------------------------------------------------------------------------------------


def test_legacy_agents_two_stage_dry_run_id_stability_apply_and_skills_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two-stage dry run & apply on legacy_agents_layout: IDs stable, 0 .agents record .md, skills kept."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    dest = tmp_path / "legacy_agents"
    dest.mkdir()
    repo = migration_corpus.legacy_agents_layout(dest)
    skill_md = repo / ".agents" / "skills" / "demo" / "SKILL.md"
    skill_md.parent.mkdir(parents=True, exist_ok=True)
    skill_md.write_text("# Demo skill\n", encoding="utf-8")
    _git(repo, "add", ".agents/skills")
    _git(repo, "commit", "-q", "-m", "add preserved skill")

    before = _tree_sha256(repo)
    rc_dry, out_dry, _ = _run_cli_inproc(
        repo, ["migrate", "metadata", "--dry-run"], aw_home=aw_home
    )
    assert rc_dry == 0, out_dry
    assert "Layout stage:" in out_dry
    assert "no sidecar (none expected)" in out_dry
    assert _tree_sha256(repo) == before
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""

    rc_json, out_json, _ = _run_cli_inproc(
        repo, ["migrate", "metadata", "--dry-run", "--json"], aw_home=aw_home
    )
    assert rc_json == 0, out_json
    dry_json = json.loads(out_json)
    dry_minted = dict(dry_json["minted_ids"])
    assert len(dry_minted) == 3

    rc_agent, out_agent, _ = _run_cli_inproc(
        repo, ["migrate", "metadata", "--dry-run", "--agent"], aw_home=aw_home
    )
    assert rc_agent == 0, out_agent
    agent_doc = json.loads(out_agent)
    assert agent_doc["outcome"] == "preview"
    ev_text = " ".join(str(ev) for ev in agent_doc["evidence"])
    assert "layout_stage" in ev_text
    assert "census" in ev_text

    applied = m0001_metadata_v2.run(
        repo, apply=True, describer=_stub_describer, commit=True
    )
    assert applied["status"] == "applied"
    assert applied["minted_ids"] == dry_minted
    assert applied["layout_stage"]["status"] == "completed"
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""

    # Zero record .md files remain under .agents/, while .agents/skills/SKILL.md is preserved
    remaining_agents_md = [
        p.relative_to(repo).as_posix()
        for p in (repo / ".agents").rglob("*.md")
        if p.is_file()
    ]
    assert remaining_agents_md == [".agents/skills/demo/SKILL.md"]
    assert skill_md.is_file()

    # Every migrated record has meta/<id6>.jsonl under .aw/records/meta/
    meta_dir = repo / ".aw" / "records" / "meta"
    assert meta_dir.is_dir()
    for id6 in dry_minted.values():
        assert (meta_dir / f"{id6}.jsonl").is_file()
    assert (meta_dir / "qa1z01.jsonl").is_file()
    assert (meta_dir / "qa1z02.jsonl").is_file()


def test_mixed_layout_two_stage_dry_run_apply_and_cli_stage2_failure_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """mixed_layout agrees on minted_ids, deduplicates shared plan, and rolls back stage2-failure cleanly."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    # Case A: CLI --apply --fault-injection stage2-failure on mixed_layout rolls back byte-identically
    dest_rb = tmp_path / "mixed_rb"
    dest_rb.mkdir()
    repo_rb = migration_corpus.mixed_layout(dest_rb)
    before_rb = _tree_sha256(repo_rb)

    rc_dry, out_dry, _ = _run_cli_inproc(
        repo_rb, ["migrate", "metadata", "--dry-run"], aw_home=aw_home
    )
    assert rc_dry == 0, out_dry
    _seed_journal_descriptions(repo_rb)

    rc_fail, out_fail, err_fail = _run_cli_inproc(
        repo_rb,
        ["migrate", "metadata", "--apply", "--fault-injection", "stage2-failure"],
        aw_home=aw_home,
    )
    assert rc_fail == 1
    assert "rolled back" in (out_fail + err_fail).lower()
    assert (
        _tree_sha256(
            repo_rb,
            ignore_prefixes=(".git/", ".aw/state/", ".aw/records/runs/"),
        )
        == before_rb
    )
    assert _git(repo_rb, "status", "--porcelain").stdout.strip() == ""

    # Case B: uninterrupted apply on mixed_layout
    dest_ok = tmp_path / "mixed_ok"
    dest_ok.mkdir()
    repo_ok = migration_corpus.mixed_layout(dest_ok)
    dry_ok = m0001_metadata_v2.run(repo_ok, apply=False)
    app_ok = m0001_metadata_v2.run(
        repo_ok, apply=True, describer=_stub_describer, commit=True
    )
    assert app_ok["status"] == "applied"
    assert app_ok["minted_ids"] == dry_ok["minted_ids"]
    assert not (repo_ok / ".agents").exists()
    assert _git(repo_ok, "status", "--porcelain").stdout.strip() == ""
    for id6 in ("qa1z03", "qa1z04", "qa1z05"):
        assert (repo_ok / ".aw" / "records" / "meta" / f"{id6}.jsonl").is_file()


def test_legacy_agents_cli_fault_injection_stage2_failure_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """aw migrate metadata --apply --fault-injection stage2-failure exits 1 and restores legacy_agents_layout."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    dest = tmp_path / "legacy_cli_rb"
    dest.mkdir()
    repo = migration_corpus.legacy_agents_layout(dest)
    before = _tree_sha256(repo)

    rc_dry, out_dry, _ = _run_cli_inproc(
        repo, ["migrate", "metadata", "--dry-run"], aw_home=aw_home
    )
    assert rc_dry == 0, out_dry
    _seed_journal_descriptions(repo)

    rc_fail, out_fail, err_fail = _run_cli_inproc(
        repo,
        ["migrate", "metadata", "--apply", "--fault-injection", "stage2-failure"],
        aw_home=aw_home,
    )
    assert rc_fail == 1
    assert "stage2-failure" in (out_fail + err_fail)
    assert "rolled back" in (out_fail + err_fail).lower()
    assert _tree_sha256(repo) == before
    assert not (repo / ".aw" / ".gitignore").exists()
    assert not (repo / ".aw" / "records").exists()
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""


def test_two_stage_interrupt_mid_apply_and_resume_matches_uninterrupted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """interrupt-mid-apply leaves status='applying' and resume() finishes identically to uninterrupted."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    dest_ref = tmp_path / "ref_legacy"
    dest_ref.mkdir()
    repo_ref = migration_corpus.legacy_agents_layout(dest_ref)
    dry_ref = m0001_metadata_v2.run(repo_ref, apply=False)
    app_ref = m0001_metadata_v2.run(
        repo_ref, apply=True, describer=_stub_describer, commit=False
    )
    assert app_ref["status"] == "applied"

    dest_int = tmp_path / "int_legacy"
    dest_int.mkdir()
    repo_int = migration_corpus.legacy_agents_layout(dest_int)
    # Run dry first with identical minted_ids? Or seed journal minted_ids from ref to compare logs/mirrors
    jdir_int = repo_int / ".aw" / "state" / "durable" / "migrations" / "m0001"
    jdir_int.mkdir(parents=True, exist_ok=True)
    (jdir_int / "journal.json").write_text(
        json.dumps({"minted_ids": dict(dry_ref["minted_ids"])}), encoding="utf-8"
    )

    with pytest.raises(layout_migration.MigrationError, match="interrupt-mid-apply"):
        m0001_metadata_v2.run(
            repo_int,
            apply=True,
            describer=_stub_describer,
            fault_injection="interrupt-mid-apply",
            commit=False,
        )

    jdata = json.loads((jdir_int / "journal.json").read_text(encoding="utf-8"))
    assert jdata["status"] == "applying"
    assert jdata["layout_stage"]["status"] == "completed"

    resumed = m0001_metadata_v2.resume(repo_int, commit=False)
    assert resumed["status"] == "applied"
    assert resumed["resumed"] is True

    # Rewritten markdown mirrors match uninterrupted run; logs exist for every record
    ref_digests = _tree_sha256(
        repo_ref,
        ignore_prefixes=(
            ".git/",
            ".aw/state/",
            ".aw/records/meta/",
            ".aw/records/runs/",
        ),
    )
    int_digests = _tree_sha256(
        repo_int,
        ignore_prefixes=(
            ".git/",
            ".aw/state/",
            ".aw/records/meta/",
            ".aw/records/runs/",
        ),
    )
    assert int_digests == ref_digests
    for id6 in dry_ref["minted_ids"].values():
        assert (repo_int / ".aw" / "records" / "meta" / f"{id6}.jsonl").is_file()


def test_no_sidecar_skip_notice_and_apply_without_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """no_sidecar shape (d) emits layout skip notice + 'no sidecar (none expected)' and applies without --force."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    dest = tmp_path / "no_sidecar_repo"
    dest.mkdir()
    repo = migration_corpus.no_sidecar(dest)

    rc_dry, out_dry, _ = _run_cli_inproc(
        repo, ["migrate", "metadata", "--dry-run"], aw_home=aw_home
    )
    assert rc_dry == 0, out_dry
    assert "layout stage: skipped (already on .aw/)" in out_dry
    assert "no sidecar (none expected)" in out_dry

    census_text = m0001_verify.format_census(
        m0001_metadata_v2.run(repo, apply=False)["census"]
    )
    assert "layout stage: skipped (already on .aw/)" in census_text
    assert "no sidecar (none expected)" in census_text

    applied = m0001_metadata_v2.run(
        repo, apply=True, force=False, describer=_stub_describer, commit=True
    )
    assert applied["status"] == "applied"
    assert applied["layout_stage"] == {
        "status": "skipped",
        "reason": "already on .aw/",
    }
    assert (repo / ".aw" / "records" / "meta" / "qa1z06.jsonl").is_file()
    assert (repo / ".aw" / "records" / "meta" / "qa1z07.jsonl").is_file()
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""


def test_companion_backend_external_records_root_in_place_migration_and_query(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-18 companion_backend: logs under companion/records/meta, root-kind backups, no repo/.aw/records."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    dest = tmp_path / "comp_shape"
    dest.mkdir()
    target = migration_corpus.companion_backend(dest)
    companion_records = dest / "companion" / "records"

    applied = m0001_metadata_v2.run(
        target, apply=True, describer=_stub_describer, commit=True
    )
    assert applied["status"] == "applied"
    assert not (target / ".aw" / "records").exists()
    assert (companion_records / "meta" / "qa1z08.jsonl").is_file()
    assert (companion_records / "meta" / "qa1z09.jsonl").is_file()

    # Backups and applied_files carry (root_kind, relpath) distinguishing records vs repo
    jpath = (
        target / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    )
    jdata = json.loads(jpath.read_text(encoding="utf-8"))
    assert any(
        b.get("root_kind") == "records" and b.get("relpath") == "meta/qa1z08.jsonl"
        for b in jdata["backups"]
    )
    assert any(
        a.get("root_kind") == "records" and a.get("relpath") == "meta/qa1z08.jsonl"
        for a in jdata["applied_files"]
    )

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    ctx = project_context.resolve_project_context(
        target_repo=str(target), aw_home=str(aw_home)
    )
    res = artifact_meta.query(project_context=ctx)
    assert {st.id6 for st in res.rows} == {"qa1z08", "qa1z09"}

    rc_find, out_find, _ = _run_cli_inproc(target, ["find", "--json"], aw_home=aw_home)
    assert rc_find == 0, out_find
    assert "qa1z08" in out_find
    assert "qa1z09" in out_find


def test_home_backend_external_records_root_in_place_migration_and_query(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-18 home backend: logs under AW_HOME projects/.../records/meta, no repo/.aw/records."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    repo = tmp_path / "home_target"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / ".aw" / "config").mkdir(parents=True)
    (repo / ".aw" / "config" / "project.json").write_text(
        json.dumps({"schema_version": 2, "records_backend": "home"}, indent=2) + "\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".aw/config/project.json")
    _git(repo, "commit", "-q", "-m", "init home-backend target")

    ctx = project_context.resolve_project_context(
        target_repo=str(repo), aw_home=str(aw_home)
    )
    home_records = project_context.project_records_dir(repo, aw_home=aw_home)
    assert project_context.record_git_root(home_records) is None
    (home_records / "plans" / "pending").mkdir(parents=True)
    (
        home_records / "plans" / "pending" / "20260901-zeta-01-hm0001-home-plan.ipd.md"
    ).write_text(
        "# IPD: Home backend plan\n\n"
        "- Date: 2026-09-01\n"
        "- Kind: child\n"
        "- Set: zeta\n"
        "- Order: 01\n"
        "- Status: approved\n"
        "- Id: hm0001\n\n"
        "## Goal\n\n"
        "Verify home backend migration.\n",
        encoding="utf-8",
    )

    applied = m0001_metadata_v2.run(
        repo, apply=True, describer=_stub_describer, commit=True
    )
    assert applied["status"] == "applied"
    assert not (repo / ".aw" / "records").exists()
    assert (home_records / "meta" / "hm0001.jsonl").is_file()

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    res = artifact_meta.query(project_context=ctx)
    assert [st.id6 for st in res.rows] == ["hm0001"]

    rc_find, out_find, _ = _run_cli_inproc(repo, ["find", "--json"], aw_home=aw_home)
    assert rc_find == 0, out_find
    assert "hm0001" in out_find


def test_m0001_two_stage_routes_legacy_workflow_artifacts_untracked_and_validates_attention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two-stage m0001 projects and moves legacy workflow-artifacts to .aw/workflow-artifacts/ untracked."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    dest = tmp_path / "legacy_wa_apply"
    dest.mkdir()
    repo = migration_corpus.legacy_agents_layout(dest)

    # Give the corpus research note a canonical frontmatter status so attention --check
    # validates the entire migrated repo rather than tripping on the pre-existing statusless note.
    survey = repo / ".agents" / "docs" / "research" / "20260708-survey-notes.md"
    survey.write_text(
        "---\nstatus: reference\n---\n" + survey.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    wa_files = {
        "workflow-artifacts/assess-bugs/20260726-115243/report.md": b"# Assess bugs report\n",
        "workflow-artifacts/plan-review/20260728-090000/review.md": b"# Plan review notes\n",
    }
    for rel, content in wa_files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    _git(
        repo,
        "add",
        "workflow-artifacts",
        ".agents/docs/research/20260708-survey-notes.md",
    )
    _git(repo, "commit", "-q", "-m", "add tracked legacy workflow-artifacts")

    mgr = layout_migration.MigrationManager(str(repo), aw_home=str(aw_home))
    plan_doc = mgr.plan_embedded_stage_one()
    assert plan_doc["valid"] is True

    scratch = tmp_path / "scratch_wa"
    proj = mgr.project_stage_one_to_scratch(plan_doc, scratch, backfill_ids=False)
    assert proj["status"] == "planned"
    for rel, content in wa_files.items():
        projected = scratch / ".aw" / rel
        assert projected.is_file(), f"Expected scratch artifact at {projected}"
        assert projected.read_bytes() == content
    assert not (scratch / ".aw" / "records" / "assess-bugs").exists()
    assert not (scratch / ".aw" / "records" / "plan-review").exists()

    applied = m0001_metadata_v2.run(
        repo, apply=True, describer=_stub_describer, commit=True
    )
    assert applied["status"] == "applied"
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""
    assert (
        _git(
            repo, "ls-files", "--", ".aw/workflow-artifacts", "workflow-artifacts"
        ).stdout.strip()
        == ""
    )

    ign = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "check-ignore",
            "-v",
            ".aw/workflow-artifacts/assess-bugs/20260726-115243/report.md",
        ],
        env=_clean_git_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert ign.returncode == 0, ign.stderr
    assert ".aw/.gitignore" in ign.stdout

    for rel, content in wa_files.items():
        dst = repo / ".aw" / rel
        assert dst.is_file(), f"Missing migrated artifact {dst}"
        assert dst.read_bytes() == content
    assert not (repo / "workflow-artifacts").exists()
    assert not (repo / ".aw" / "records" / "assess-bugs").exists()
    assert not (repo / ".aw" / "records" / "plan-review").exists()

    att_doc = json.loads(attention.render_json(*attention.scan(repo), repo_root=repo))
    uninventoried = [
        v
        for v in att_doc.get("violations", [])
        if v.get("rule") == "attention.uninventoried-tree"
    ]
    assert uninventoried == [], att_doc
    assert cli.main(["attention", "--check", "--dir", str(repo)]) == 0


def test_m0001_stage2_failure_rollback_restores_workflow_artifacts_and_prunes_aw_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """stage2-failure rollback restores legacy workflow-artifacts/ byte-identically and removes .aw/workflow-artifacts/."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    dest = tmp_path / "legacy_wa_rollback"
    dest.mkdir()
    repo = migration_corpus.legacy_agents_layout(dest)

    wa_files = {
        "workflow-artifacts/assess-bugs/20260726-115243/report.md": b"# Assess bugs report\n",
        "workflow-artifacts/plan-review/20260728-090000/review.md": b"# Plan review notes\n",
    }
    for rel, content in wa_files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    _git(repo, "add", "workflow-artifacts")
    _git(repo, "commit", "-q", "-m", "add tracked legacy workflow-artifacts")
    before = _tree_sha256(repo)

    with pytest.raises(layout_migration.MigrationError, match="stage2-failure"):
        m0001_metadata_v2.run(
            repo,
            apply=True,
            describer=_stub_describer,
            fault_injection="stage2-failure",
            commit=True,
        )

    for rel, content in wa_files.items():
        assert (repo / rel).read_bytes() == content
    assert not (repo / ".aw" / "workflow-artifacts").exists()
    assert _tree_sha256(repo) == before
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""

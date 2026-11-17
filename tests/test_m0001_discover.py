"""Outcome tests for m0001_discover and id-less record conversion (IPD 3g20ms).

Covers E-01 (repository-agnostic discovery across all five corpus shapes,
sidecar expectedness from setter history, layout stage detection, and dynamic
citation exemptions) and E-02 (id-less prose conversion with journaled id6
minting, disposition status, H1 title, Set/Order rule, and untouched
unclassifiable files).
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Dict

import pytest

from agent_workflows import artifact_core, artifact_meta
from agent_workflows.migrations import m0001_discover, m0001_metadata_v2, m0001_verify
from tests import migration_corpus

pytestmark = pytest.mark.core


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, name: str) -> Path:
    aw_home = tmp_path / f"aw_home_{name}"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("HOME", str(aw_home))

    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / ".aw" / "records").mkdir(parents=True)
    (repo / ".aw" / ".gitignore").write_text(
        "/state/\n/config/local.json\nrecords/history.jsonl\n",
        encoding="utf-8",
    )
    return repo


def test_discover_across_five_corpus_shapes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """discover(repo) classifies trees, types, identities, status sources, and unclassifiables."""
    monkeypatch.setenv("AW_HOME", str(tmp_path / "aw_home"))

    roots: Dict[str, Path] = {}
    for shape_name, builder in sorted(migration_corpus.SHAPES.items()):
        dest = tmp_path / shape_name
        dest.mkdir()
        roots[shape_name] = builder(dest)

    # Shape (a): legacy_agents_layout
    inv_a = m0001_discover.discover(roots["legacy_agents_layout"])
    assert inv_a.layout_stage_needed is True
    assert inv_a.sidecar_expected is False
    assert inv_a.sidecar_present is False
    assert len(inv_a.records) == 5
    assert all(r.source_tree == ".agents" for r in inv_a.records)
    assert len(inv_a.legacy_name_records) == 2
    assert len(inv_a.mint_records) == 3

    # Shape (b): mixed_layout
    inv_b = m0001_discover.discover(roots["mixed_layout"])
    assert inv_b.layout_stage_needed is True
    assert {r.source_tree for r in inv_b.records} == {".aw/records", ".agents"}
    assert len(inv_b.mint_records) == 0

    # Shape (c): idless_prose
    inv_c = m0001_discover.discover(roots["idless_prose"])
    assert inv_c.layout_stage_needed is False
    assert len(inv_c.records) == 1
    prose_rec = inv_c.records[0]
    assert prose_rec.record_type == "ipd"
    assert prose_rec.identity is None
    assert prose_rec.needs_mint is True
    assert prose_rec.needs_rename is True
    assert prose_rec.status == "executed"
    assert prose_rec.status_source == "disposition"
    assert (
        prose_rec.title == "Implementation Plan Document (IPD) - Synthetic Prose Plan"
    )
    assert len(inv_c.unclassifiable) == 1
    assert inv_c.unclassifiable[0].rel_path == "notes/scratch.md"
    assert inv_c.unclassifiable[0].reason

    # Shape (d): no_sidecar
    inv_d = m0001_discover.discover(roots["no_sidecar"])
    assert inv_d.layout_stage_needed is False
    assert inv_d.sidecar_expected is False
    assert len(inv_d.records) == 2
    assert {r.status_source for r in inv_d.records} == {"bullet"}

    # Shape (e): companion_backend
    inv_e = m0001_discover.discover(roots["companion_backend"])
    assert inv_e.layout_stage_needed is False
    assert len(inv_e.records) == 2
    assert all(r.source_tree == "companion" for r in inv_e.records)


def test_discover_sidecar_expected_from_setter_history_and_skills_only_agents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """sidecar_expected is True only when spec/backlog history names a setter; skills-only .agents needs no layout stage."""
    repo = _init_repo(tmp_path, monkeypatch, name="setter_and_skills")
    rec = repo / ".aw" / "records"
    (rec / "specs" / "approved").mkdir(parents=True)
    (repo / ".agents" / "skills" / "demo").mkdir(parents=True)
    (repo / ".agents" / "skills" / "demo" / "SKILL.md").write_text(
        "# Demo skill\n", encoding="utf-8"
    )
    (
        rec / "specs" / "approved" / "20261101-demo-01-sp1234-with-setter.spec.md"
    ).write_text(
        "# Spec: With Setter\n\n"
        "- Id: sp1234\n"
        "- Status: approved\n\n"
        "## Workflow history\n"
        "- 2026-11-01 approved (aw specs): approved by maintainer\n",
        encoding="utf-8",
    )

    inv = m0001_discover.discover(repo)
    assert inv.sidecar_expected is True
    assert "aw specs" in inv.sidecar_expected_reason
    assert inv.layout_stage_needed is False


def test_idless_prose_dry_run_census_journal_reuse_and_apply_leaves_unclassifiable_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E-02: idless_prose dry-run census, minted-id reuse across dry run & apply, log creation, and untouched scratch.md."""
    monkeypatch.setenv("AW_HOME", str(tmp_path / "aw_home"))
    dest = tmp_path / "idless_prose"
    dest.mkdir()
    root = migration_corpus.idless_prose(dest)

    scratch_file = root / ".aw" / "records" / "notes" / "scratch.md"
    scratch_digest_before = hashlib.sha256(scratch_file.read_bytes()).hexdigest()

    dry = m0001_metadata_v2.run(root, apply=False)
    assert dry["status"] == "dry_run"
    assert len(dry["minted_ids"]) == 1
    old_rel = "plans/executed/20260715-prose-migration-ipd.md"
    minted_id = dry["minted_ids"][old_rel]
    assert artifact_core.is_valid_id6(minted_id)

    census = dry["census"]
    assert census["unclassifiable_count"] == 1
    assert census["unclassifiable_files"][0]["path"] == "notes/scratch.md"
    assert census["unclassifiable_files"][0]["reason"]
    assert census["minted_record_count"] == 1
    mr = census["minted_records"][0]
    assert mr["id6"] == minted_id
    assert mr["status"] == "executed"
    assert mr["title"] == "Implementation Plan Document (IPD) - Synthetic Prose Plan"

    census_text = m0001_verify.format_census(census)
    assert minted_id in census_text
    assert "executed" in census_text
    assert "Implementation Plan Document (IPD) - Synthetic Prose Plan" in census_text
    assert "notes/scratch.md" in census_text

    applied = m0001_metadata_v2.run(
        root,
        apply=True,
        commit=False,
        describer=lambda *a: "Synthetic prose plan description.",
    )
    assert applied["status"] == "applied"
    assert applied["minted_ids"][old_rel] == minted_id

    log_path = root / ".aw" / "records" / "meta" / f"{minted_id}.jsonl"
    assert log_path.is_file()
    events = [
        artifact_meta.decode_line(ln)
        for ln in log_path.read_text(encoding="utf-8").splitlines(keepends=True)
        if ln.strip()
    ]
    assert events[0]["op"] == "checkpoint"
    assert events[0]["path"] == old_rel
    assert events[0]["fields"]["id"] == minted_id
    assert events[0]["fields"]["status"] == "executed"
    assert events[0]["fields"]["set"] == minted_id
    assert events[0]["fields"]["order"] == 1
    assert (
        events[0]["fields"]["title"]
        == "Implementation Plan Document (IPD) - Synthetic Prose Plan"
    )
    assert events[1]["op"] == "rename"
    assert events[1]["path"] == dry["rename_map"][old_rel]

    # Unclassifiable file must be byte-identical with zero git diff.
    assert (
        hashlib.sha256(scratch_file.read_bytes()).hexdigest() == scratch_digest_before
    )
    diff_proc = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "--quiet",
            "--",
            ".aw/records/notes/scratch.md",
        ],
        check=False,
    )
    assert diff_proc.returncode == 0


def test_idless_dateless_prose_record_mints_and_converts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dateless prose plan under plans/pending/ mints id6, uses pending disposition, and round-trips."""
    repo = _init_repo(tmp_path, monkeypatch, name="dateless_prose")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "pending").mkdir(parents=True)
    plan_file = rec / "plans" / "pending" / "my-dateless-prose-plan.md"
    plan_file.write_text(
        "# Dateless Prose Plan Title\n\nBody with no metadata bullets.\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".aw/.gitignore", ".aw/records")
    _git(repo, "commit", "-m", "seed dateless prose plan")

    res = m0001_metadata_v2.run(
        repo,
        apply=True,
        commit=False,
        describer=lambda *a: "Dateless prose plan summary.",
    )
    assert res["status"] == "applied"
    assert res["round_trip"]["passed"] is True
    minted_id = res["minted_ids"]["plans/pending/my-dateless-prose-plan.md"]
    new_rel = res["rename_map"]["plans/pending/my-dateless-prose-plan.md"]
    assert new_rel.endswith(
        f"-{minted_id}-01-{minted_id}-my-dateless-prose-plan.ipd.md"
    )
    assert (rec / new_rel).is_file()
    assert not plan_file.exists()

    log_path = rec / "meta" / f"{minted_id}.jsonl"
    first_ev = artifact_meta.decode_line(
        log_path.read_text(encoding="utf-8").splitlines(keepends=True)[0]
    )
    assert first_ev["fields"]["status"] == "pending"
    assert first_ev["fields"]["title"] == "Dateless Prose Plan Title"

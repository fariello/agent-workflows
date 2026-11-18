"""AC-42 any-repository migration tests across the five C12 corpus shapes (IPD g5hpbb).

Exercises real `aw` CLI commands (`migrate metadata`, `show --history`, `show --format json`)
and real `m0001_metadata_v2`, `artifact_meta`, `status_set`, `project_context`, `m0001_verify`,
and `chain` functions on isolated `git init` repositories built by `tests/migration_corpus.py`.
No test inspects production source code.

Pre-cutover boundary: `aw find` and `aw attention --format json` parity assertions
and the `this_repository` clone case are carried by follow-up plan `60mazt`
(graduated from backlog `mzw0kk`, gated on `executed:ffceq0` and `state:backlog:done:e49gzt`).
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
from typing import Dict, Sequence, Tuple

import pytest

from agent_workflows import (
    artifact_core,
    artifact_meta,
    cli,
    project_context,
    selectors,
    status_set,
)
from agent_workflows.migrations import chain, m0001_verify
from tests import migration_corpus as mc

pytestmark = pytest.mark.core

CORPUS_SHAPES: tuple[str, ...] = (
    "legacy_agents_layout",
    "mixed_layout",
    "idless_prose",
    "no_sidecar",
    "companion_backend",
)

EXPECTED_RECORD_COUNTS: Dict[str, int] = {
    "legacy_agents_layout": 5,
    "mixed_layout": 3,
    "idless_prose": 1,
    "no_sidecar": 2,
    "companion_backend": 2,
}

EXPECTED_MINT_COUNTS: Dict[str, int] = {
    "legacy_agents_layout": 3,
    "mixed_layout": 0,
    "idless_prose": 1,
    "no_sidecar": 0,
    "companion_backend": 0,
}

SAMPLE_PROBE_ID6: Dict[str, str] = {
    "legacy_agents_layout": "qa1z01",
    "mixed_layout": "qa1z03",
    "idless_prose": "__minted__",
    "no_sidecar": "qa1z06",
    "companion_backend": "qa1z08",
}


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
        selectors._record_dirs_cached.cache_clear()
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
    repo: Path, text: str = "Synthetic migrated record summary."
) -> None:
    """Populate `journal.json['descriptions']` after dry run so CLI --apply can run before ya4ee4."""
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


def _build_corpus_shape(
    shape: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Tuple[Path, Path]:
    aw_home = tmp_path / f"aw_home_{shape}"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(aw_home / "xdg"))
    dest = tmp_path / f"corpus_{shape}"
    dest.mkdir()
    selectors._record_dirs_cached.cache_clear()
    repo = mc.SHAPES[shape](dest)
    return repo, aw_home


@pytest.mark.parametrize("shape", CORPUS_SHAPES, ids=CORPUS_SHAPES)
def test_ac42_corpus_shapes_end_to_end_migration(
    shape: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-42 items (1)-(3), (4) show/query, (5) inventory-to-log parity, (6), and (7)."""
    repo, aw_home = _build_corpus_shape(shape, tmp_path, monkeypatch)

    # Preserve pre-migration inventory and any unclassifiable file digests
    pre_inventory = status_set.inventory_all_artifacts(repo)
    unclassifiable_digests: Dict[str, str] = {}
    if shape == "idless_prose":
        scratch_note = repo / ".aw" / "records" / "notes" / "scratch.md"
        unclassifiable_digests[scratch_note.as_posix()] = hashlib.sha256(
            scratch_note.read_bytes()
        ).hexdigest()

    # AC-42 (1): dry-run census via real CLI (`aw migrate metadata --json`)
    before_repo_tree = _tree_sha256(repo)
    rc_dry, out_dry, err_dry = _run_cli_inproc(
        repo, ["migrate", "metadata", "--json"], aw_home=aw_home
    )
    assert rc_dry == 0, err_dry or out_dry
    dry = json.loads(out_dry)
    assert dry["status"] == "dry_run"
    assert _tree_sha256(repo) == before_repo_tree
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""

    census = dry["census"]
    assert census["record_count"] == EXPECTED_RECORD_COUNTS[shape]
    assert len(dry["minted_ids"]) == EXPECTED_MINT_COUNTS[shape]
    assert census["minted_record_count"] == EXPECTED_MINT_COUNTS[shape]
    assert census["unknown_field_refusal_count"] == 0
    assert census["unparseable_value_refusal_count"] == 0

    formatted_census = m0001_verify.format_census(census)
    for minted_id in dry["minted_ids"].values():
        assert artifact_core.is_valid_id6(minted_id)
        assert minted_id in formatted_census

    if shape == "idless_prose":
        assert census["unclassifiable_count"] == 1
        assert census["unclassifiable_files"][0]["path"] == "notes/scratch.md"
        assert "notes/scratch.md" in formatted_census

    # AC-42 (6): shape (d) runs with no sidecar without --force and states it in census
    if shape == "no_sidecar":
        assert dry["sidecar"]["expected"] is False
        assert dry["sidecar"]["present"] is False
        assert census["sidecar_status"] == "no sidecar (none expected)"
        assert "no sidecar (none expected)" in formatted_census

    # AC-42 (3) dry-run round-trip check
    assert dry["round_trip"]["round_trip_passed"] is True
    assert dry["round_trip"]["replayed_count"] == EXPECTED_RECORD_COUNTS[shape]

    # AC-42 (2): --apply via real CLI, then second --apply that changes nothing
    _seed_journal_descriptions(repo)
    head_before_apply = _git(repo, "rev-parse", "HEAD").stdout.strip()
    rc_apply, out_apply, err_apply = _run_cli_inproc(
        repo, ["migrate", "metadata", "--apply"], aw_home=aw_home
    )
    assert rc_apply == 0, err_apply or out_apply
    assert chain.read_metadata_schema(repo) == 2
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""
    head_after_apply = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head_after_apply != head_before_apply

    # AC-42 (7): shapes (a) and (b) ran layout migration first in the same transaction
    jpath = repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    jdata = json.loads(jpath.read_text(encoding="utf-8"))
    if shape in ("legacy_agents_layout", "mixed_layout"):
        assert jdata["layout_stage"]["status"] == "completed"
        assert not (repo / ".agents" / "plans").exists()
        assert not (repo / ".agents" / "backlog").exists()
        assert not (repo / ".agents" / "docs").exists()
    else:
        assert jdata["layout_stage"]["status"] == "skipped"

    if shape == "companion_backend":
        companion_dir = repo.parent / "companion"
        assert (
            _git(
                companion_dir, "status", "--untracked-files=no", "--porcelain"
            ).stdout.strip()
            == ""
        )
        assert not (repo / ".aw" / "records").exists()

    # Second --apply changes nothing
    tree_after_first = _tree_sha256(repo)
    companion_after_first = (
        _tree_sha256(repo.parent / "companion")
        if shape == "companion_backend"
        else None
    )
    rc_second, out_second, err_second = _run_cli_inproc(
        repo, ["migrate", "metadata", "--apply"], aw_home=aw_home
    )
    assert rc_second == 0, err_second or out_second
    assert "metadata_schema is 2; nothing to do" in out_second
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == head_after_apply
    assert _tree_sha256(repo) == tree_after_first
    if companion_after_first is not None:
        assert _tree_sha256(repo.parent / "companion") == companion_after_first

    # AC-42 (3) post-apply round-trip verification against generated meta/<id6>.jsonl logs
    records_root = project_context.project_records_dir(repo)
    meta_dir = records_root / "meta"
    assert meta_dir.is_dir()
    log_files = sorted(meta_dir.glob("*.jsonl"))
    assert len(log_files) == EXPECTED_RECORD_COUNTS[shape]
    for lf in log_files:
        id6 = lf.stem
        raw_lines = lf.read_text(encoding="utf-8").splitlines(keepends=True)
        ev0 = artifact_meta.decode_line(raw_lines[0])
        assert ev0["op"] == "checkpoint"
        art_type = ev0["fields"]["type"]
        replayed, _, _, _ = artifact_meta.replay(
            id6, art_type, raw_lines, records_root=records_root
        )
        assert replayed.id6 == id6
    if shape == "no_sidecar":
        hist_spec = artifact_meta.history(
            "qa1z06",
            project_context=project_context.resolve_project_context(
                target_repo=str(repo), aw_home=str(aw_home)
            ),
        )
        assert any("created by hand" in str(ev.get("line", "")) for ev in hist_spec)
        assert any("approved in review" in str(ev.get("line", "")) for ev in hist_spec)
    if shape == "idless_prose":
        for path_str, expected_digest in unclassifiable_digests.items():
            assert (
                hashlib.sha256(Path(path_str).read_bytes()).hexdigest()
                == expected_digest
            )

    # AC-42 (4) CLI log read: `aw show <id6> --history` and `--format json` on migrated record
    probe_id6 = SAMPLE_PROBE_ID6[shape]
    if probe_id6 == "__minted__":
        probe_id6 = next(iter(dry["minted_ids"].values()))
    rc_hist, out_hist, err_hist = _run_cli_inproc(
        repo, ["show", probe_id6, "--history"], aw_home=aw_home
    )
    assert rc_hist == 0, err_hist or out_hist
    assert probe_id6 in out_hist
    assert "checkpoint" in out_hist

    rc_show_json, out_show_json, err_show_json = _run_cli_inproc(
        repo, ["show", probe_id6, "--format", "json"], aw_home=aw_home
    )
    assert rc_show_json == 0, err_show_json or out_show_json
    show_doc = json.loads(out_show_json)
    assert show_doc["data"]["records"][0]["id6"] == probe_id6

    # AC-42 (5) pre-migration inventory vs post-migration log reader (`artifact_meta.query`)
    ctx = project_context.resolve_project_context(
        target_repo=str(repo), aw_home=str(aw_home)
    )
    q = artifact_meta.query(project_context=ctx)
    assert not q.incomplete
    log_rows = [r for r in q.rows if not r.id_derived]
    assert len(log_rows) == EXPECTED_RECORD_COUNTS[shape]
    log_by_id = {r.id6: r for r in log_rows}

    for exp in mc.EXPECTED[shape]:
        if exp.id6 is not None:
            assert exp.id6 in log_by_id
            if exp.status is not None:
                assert log_by_id[exp.id6].status == exp.status.lower()
        else:
            # Minted id6 from pre-migration path
            rel_hint = exp.path.split(".aw/records/", 1)[-1].split(".agents/", 1)[-1]
            # Find matching minted id6 via dry-run map
            matched_mint = [
                mid
                for old_rel, mid in dry["minted_ids"].items()
                if old_rel.endswith(Path(rel_hint).name)
            ]
            assert len(matched_mint) == 1
            minted_id = matched_mint[0]
            assert minted_id in log_by_id
            if exp.status is not None:
                assert log_by_id[minted_id].status == exp.status.lower()

    # Confirm pre-migration inventory records (excluding non-record unclassifiables) match log statuses
    for rec in pre_inventory:
        if rec.id6 is not None and rec.id6 in log_by_id:
            assert log_by_id[rec.id6].status == (rec.status or "").lower()

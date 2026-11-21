"""AC-42 any-repository migration tests across the five C12 corpus shapes and this repo clone.

Exercises real `aw` CLI commands (`migrate metadata`, `find --agent`, `attention --format json`,
`show --history`, `show --format json`) and real `m0001_metadata_v2`, `artifact_meta`,
`status_set`, `project_context`, `m0001_verify`, and `chain` functions on isolated `git init`
repositories built by `tests/migration_corpus.py` and on a disposable `git clone --no-hardlinks`
of this repository (IPDs `g5hpbb` and `60mazt`). No test inspects production source code.
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
from typing import Any, Dict, List, Sequence, Tuple

import pytest

from agent_workflows import (
    artifact_core,
    artifact_meta,
    cli,
    plans,
    project_context,
    selectors,
    status_set,
)
from agent_workflows.migrations import chain, m0001_verify
from tests import migration_corpus as mc

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
        artifact_core._cached_ignored_dirs.cache_clear()
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
    """Populate `journal.json['descriptions']` after dry run for records lacking descriptions."""
    jpath = repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    data = json.loads(jpath.read_text(encoding="utf-8"))
    descs = dict(data.get("descriptions") or {})
    missing = (
        (data.get("steps") or {}).get("census", {}).get("missing_description_paths")
    )
    if isinstance(missing, list):
        for rel in missing:
            descs.setdefault(str(rel), text)
    else:
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


def _parse_find_agent_stream(
    raw_output: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Parse JSONL emitted by `aw find ... --agent` into `(items, summary)`."""
    items: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {}
    for line in raw_output.splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        kind = rec.get("kind")
        if kind == "item":
            items.append(rec)
        elif kind == "summary":
            summary = rec
    return items, summary


def _map_pre_migration_path(path: str, rename_map: Dict[str, str]) -> str | None:
    """Map a pre-migration `aw find` path through layout relocation and `rename_map`.

    Returns `None` for non-record `.agents/workflows/` files moved to `.aw/system/workflows/`.
    """
    if path.startswith(".agents/workflows/"):
        return None
    if path.startswith(".agents/docs/"):
        rel = path[len(".agents/docs/") :]
        prefix = ".aw/records/"
    elif path.startswith(".agents/"):
        rel = path[len(".agents/") :]
        prefix = ".aw/records/"
    elif path.startswith(".aw/records/"):
        rel = path[len(".aw/records/") :]
        prefix = ".aw/records/"
    else:
        return path
    mapped_rel = rename_map.get(rel, rel)
    return f"{prefix}{mapped_rel}"


def _normalize_find_status(record_type: str, status: str | None) -> str:
    """Normalize `aw find --agent` status for parity comparison (ffceq0 D-1..D-6)."""
    raw = (status or "").strip()
    if not raw or raw == "-":
        return "-"
    if record_type == "plans":
        tok = raw.split()[0]
        if tok.lower() in ("pending", "reusable"):
            return tok.lower()
        return plans.normalize_status(tok) or tok.lower()
    return raw.lower()


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


@pytest.mark.core
@pytest.mark.parametrize("shape", CORPUS_SHAPES, ids=CORPUS_SHAPES)
def test_ac42_corpus_shapes_end_to_end_migration(
    shape: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-42 items (1)-(7) across all five C12 corpus shapes."""
    repo, aw_home = _build_corpus_shape(shape, tmp_path, monkeypatch)

    # Preserve pre-migration inventory, `aw find --agent`, `aw attention`, and unclassifiable digests
    pre_inventory = status_set.inventory_all_artifacts(repo)
    rc_pre_find, out_pre_find, err_pre_find = _run_cli_inproc(
        repo, ["find", "--agent"], aw_home=aw_home
    )
    assert rc_pre_find == 0, err_pre_find or out_pre_find
    pre_find_items, pre_find_summary = _parse_find_agent_stream(out_pre_find)
    assert pre_find_summary.get("complete") is True

    _rc_pre_attn, out_pre_attn, _err_pre_attn = _run_cli_inproc(
        repo, ["attention", "--all", "--format", "json"], aw_home=aw_home
    )
    pre_attn_doc = json.loads(out_pre_attn)
    pre_attn_violations = {
        (v["location"], v["rule"]) for v in pre_attn_doc.get("violations", [])
    }

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

    # AC-42 (4) CLI log reads: `aw find <id6> --agent`, `aw show <id6> --history` / `--format json`,
    # and `aw attention --format json` / `--all --format json` on migrated records.
    probe_id6 = SAMPLE_PROBE_ID6[shape]
    if probe_id6 == "__minted__":
        probe_id6 = next(iter(dry["minted_ids"].values()))

    rc_find_probe, out_find_probe, err_find_probe = _run_cli_inproc(
        repo, ["find", probe_id6, "--agent"], aw_home=aw_home
    )
    assert rc_find_probe == 0, err_find_probe or out_find_probe
    probe_items, probe_summary = _parse_find_agent_stream(out_find_probe)
    assert probe_summary.get("complete") is True
    assert any(it.get("id6") == probe_id6 for it in probe_items), probe_items

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

    rc_attn, out_attn, err_attn = _run_cli_inproc(
        repo, ["attention", "--format", "json"], aw_home=aw_home
    )
    attn_doc = json.loads(out_attn)
    rc_attn_all, out_attn_all, err_attn_all = _run_cli_inproc(
        repo, ["attention", "--all", "--format", "json"], aw_home=aw_home
    )
    attn_all_doc = json.loads(out_attn_all)

    # Zero violations referencing `meta/` across all five shapes
    for doc in (attn_doc, attn_all_doc):
        meta_viols = [
            v
            for v in doc.get("violations", [])
            if "meta/" in v.get("location", "")
            or v.get("location", "").endswith("/meta")
            or v.get("location") == "meta"
        ]
        assert meta_viols == [], f"Unexpected meta/ attention violations: {meta_viols}"

    rename_map: Dict[str, str] = dict(jdata.get("rename_map") or {})
    minted_ids: Dict[str, str] = dict(jdata.get("minted_ids") or {})

    # Migrated record IDs appear in `aw attention --all --format json`
    attn_all_ids = {
        it.get("id") for it in attn_all_doc.get("items", []) if it.get("id")
    }
    assert (
        probe_id6 in attn_all_ids
    ), f"Migrated probe {probe_id6} missing from aw attention --all items: {attn_all_ids}"

    if shape == "idless_prose":
        uninv = [
            v
            for v in attn_all_doc.get("violations", [])
            if v.get("rule") == "attention.uninventoried-tree"
        ]
        assert len(uninv) == 1 and uninv[0]["location"] == ".aw/records/notes", uninv
        other_viols = [
            v
            for v in attn_all_doc.get("violations", [])
            if v.get("rule") != "attention.uninventoried-tree"
        ]
        assert other_viols == [], other_viols
    elif shape in ("no_sidecar", "companion_backend"):
        assert rc_attn == 0, err_attn or out_attn
        assert attn_doc.get("valid") is True, attn_doc.get("violations")
        assert rc_attn_all == 0, err_attn_all or out_attn_all
        assert attn_all_doc.get("valid") is True, attn_all_doc.get("violations")
    elif shape in ("mixed_layout", "legacy_agents_layout"):
        # No migrated record may gain attention.missing-status, attention.unknown-status,
        # or attention.uninventoried-tree violations relative to pre-migration fixtures.
        mapped_pre_viols = {
            (_map_pre_migration_path(loc, rename_map) or loc, rule)
            for loc, rule in pre_attn_violations
        }
        post_viols = [
            v
            for v in attn_all_doc.get("violations", [])
            if v.get("rule")
            in (
                "attention.uninventoried-tree",
                "attention.missing-status",
                "attention.unknown-status",
            )
        ]
        new_migrated_viols = [
            v
            for v in post_viols
            if (v.get("location"), v.get("rule")) not in mapped_pre_viols
        ]
        assert (
            new_migrated_viols == []
        ), f"Migrated {shape} introduced new attention violations: {new_migrated_viols}"
        if not mapped_pre_viols:
            assert rc_attn == 0, err_attn or out_attn
            assert attn_doc.get("valid") is True, attn_doc.get("violations")

    # AC-42 (5) before/after `aw find --agent` parity by mapped path and normalized status
    rc_post_find, out_post_find, err_post_find = _run_cli_inproc(
        repo, ["find", "--agent"], aw_home=aw_home
    )
    assert rc_post_find == 0, err_post_find or out_post_find
    post_find_items, post_find_summary = _parse_find_agent_stream(out_post_find)
    assert post_find_summary.get("complete") is True

    pre_mapped: Dict[str, Tuple[str, str]] = {}
    for item in pre_find_items:
        mapped = _map_pre_migration_path(item["path"], rename_map)
        if mapped is None:
            continue
        norm_st = _normalize_find_status(item["type"], item.get("status"))
        if mapped in pre_mapped:
            assert pre_mapped[mapped][1] == norm_st
        else:
            pre_mapped[mapped] = (item["type"], norm_st)

    post_by_path: Dict[str, Dict[str, Any]] = {
        item["path"]: item for item in post_find_items
    }
    dropped_paths = sorted(set(pre_mapped) - set(post_by_path))
    assert (
        dropped_paths == []
    ), f"Pre-migration aw find records dropped: {dropped_paths}"

    for mapped_path, (pre_type, pre_norm_status) in sorted(pre_mapped.items()):
        post_item = post_by_path[mapped_path]
        post_norm_status = _normalize_find_status(
            post_item["type"], post_item.get("status")
        )
        assert post_norm_status == pre_norm_status, (
            f"Status drift for {mapped_path} ({pre_type} -> {post_item['type']}): "
            f"pre={pre_norm_status!r} vs post={post_norm_status!r}"
        )

    minted_id_set = set(minted_ids.values())
    post_only_paths = sorted(set(post_by_path) - set(pre_mapped))
    for extra_path in post_only_paths:
        extra_id = post_by_path[extra_path].get("id6")
        assert (
            extra_id in minted_id_set
        ), f"Post-migration-only aw find item {extra_path} ({extra_id!r}) was not minted"

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


@pytest.mark.slow
@pytest.mark.livecorpus
@pytest.mark.timeout(600, wall=900)
def test_ac42_this_repository_clone_migration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-42 items (1)-(5) on a disposable `git clone --no-hardlinks` of this repository."""
    repo_root = Path(__file__).resolve().parent.parent
    source_head_before = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    source_status_before = _git(repo_root, "status", "--porcelain").stdout

    aw_home = tmp_path / "aw_home_this_repository"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(aw_home / "xdg"))

    clone = tmp_path / "this_repository"
    subprocess.run(
        ["git", "clone", "--no-hardlinks", str(repo_root), str(clone)],
        env=_clean_git_env(),
        capture_output=True,
        text=True,
        check=True,
    )
    _git(clone, "config", "user.name", "Synthetic Migration Test")
    _git(clone, "config", "user.email", "migration-test@example.invalid")

    # Pre-migration baselines in the clone
    rc_pre_find, out_pre_find, err_pre_find = _run_cli_inproc(
        clone, ["find", "--agent"], aw_home=aw_home
    )
    assert rc_pre_find == 0, err_pre_find or out_pre_find
    pre_find_items, pre_find_summary = _parse_find_agent_stream(out_pre_find)
    assert pre_find_summary.get("complete") is True
    assert len(pre_find_items) > 0

    _rc_pre_attn, out_pre_attn, _err_pre_attn = _run_cli_inproc(
        clone, ["attention", "--all", "--format", "json"], aw_home=aw_home
    )
    pre_attn_doc = json.loads(out_pre_attn)
    pre_attn_violations = {
        (v["location"], v["rule"]) for v in pre_attn_doc.get("violations", [])
    }

    # AC-42 (1): dry-run census (refuses without --force when expected sidecar is absent;
    # succeeds with --force on fresh clone and leaves clone tree untouched).
    head_before_dry = _git(clone, "rev-parse", "HEAD").stdout.strip()
    rc_dry_noforce, out_dry_noforce, _ = _run_cli_inproc(
        clone, ["migrate", "metadata", "--json"], aw_home=aw_home
    )
    assert rc_dry_noforce == 1
    assert "SIDECAR:" in out_dry_noforce

    rc_dry, out_dry, err_dry = _run_cli_inproc(
        clone, ["migrate", "metadata", "--json", "--force"], aw_home=aw_home
    )
    assert rc_dry == 0, err_dry or out_dry
    dry = json.loads(out_dry)
    assert dry["status"] == "dry_run"
    assert _git(clone, "rev-parse", "HEAD").stdout.strip() == head_before_dry
    assert _git(clone, "status", "--porcelain").stdout.strip() == ""

    census = dry["census"]
    assert census["record_count"] > 0
    assert census["unknown_field_refusal_count"] == 0
    assert census["unparseable_value_refusal_count"] == 0
    assert dry["round_trip"]["round_trip_passed"] is True
    assert dry["round_trip"]["replayed_count"] == census["record_count"]

    # AC-42 (2): seed missing descriptions, run `--apply --force`, then second `--apply --force`
    _seed_journal_descriptions(clone)
    rc_apply, out_apply, err_apply = _run_cli_inproc(
        clone, ["migrate", "metadata", "--apply", "--force"], aw_home=aw_home
    )
    assert rc_apply == 0, err_apply or out_apply
    assert chain.read_metadata_schema(clone) == 2
    assert _git(clone, "status", "--porcelain").stdout.strip() == ""
    head_after_apply = _git(clone, "rev-parse", "HEAD").stdout.strip()
    assert head_after_apply != head_before_dry

    rc_second, out_second, err_second = _run_cli_inproc(
        clone, ["migrate", "metadata", "--apply", "--force"], aw_home=aw_home
    )
    assert rc_second == 0, err_second or out_second
    assert "metadata_schema is 2; nothing to do" in out_second
    assert _git(clone, "rev-parse", "HEAD").stdout.strip() == head_after_apply
    assert _git(clone, "status", "--porcelain").stdout.strip() == ""

    # AC-42 (3): post-apply `meta/<id6>.jsonl` checkpoint and replay validity
    records_root = project_context.project_records_dir(clone)
    meta_dir = records_root / "meta"
    assert meta_dir.is_dir()
    log_files = sorted(meta_dir.glob("*.jsonl"))
    assert len(log_files) == census["record_count"]
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

    # AC-42 (4): `aw find <probe_id6> --agent`, `aw show --history`/`--format json`,
    # and `aw attention --format json` / `--all --format json`
    probe_id6 = log_files[0].stem
    rc_find_probe, out_find_probe, err_find_probe = _run_cli_inproc(
        clone, ["find", probe_id6, "--agent"], aw_home=aw_home
    )
    assert rc_find_probe == 0, err_find_probe or out_find_probe
    probe_items, probe_summary = _parse_find_agent_stream(out_find_probe)
    assert probe_summary.get("complete") is True
    assert any(it.get("id6") == probe_id6 for it in probe_items)

    rc_hist, out_hist, err_hist = _run_cli_inproc(
        clone, ["show", probe_id6, "--history"], aw_home=aw_home
    )
    assert rc_hist == 0, err_hist or out_hist
    assert probe_id6 in out_hist
    assert "checkpoint" in out_hist

    rc_show_json, out_show_json, err_show_json = _run_cli_inproc(
        clone, ["show", probe_id6, "--format", "json"], aw_home=aw_home
    )
    assert rc_show_json == 0, err_show_json or out_show_json
    show_doc = json.loads(out_show_json)
    assert show_doc["data"]["records"][0]["id6"] == probe_id6

    _rc_attn, out_attn, _err_attn = _run_cli_inproc(
        clone, ["attention", "--format", "json"], aw_home=aw_home
    )
    attn_doc = json.loads(out_attn)
    _rc_attn_all, out_attn_all, _err_attn_all = _run_cli_inproc(
        clone, ["attention", "--all", "--format", "json"], aw_home=aw_home
    )
    attn_all_doc = json.loads(out_attn_all)

    for doc in (attn_doc, attn_all_doc):
        meta_viols = [
            v
            for v in doc.get("violations", [])
            if "meta/" in v.get("location", "")
            or v.get("location", "").endswith("/meta")
            or v.get("location") == "meta"
        ]
        assert meta_viols == [], f"Unexpected meta/ attention violations: {meta_viols}"

    jpath = (
        clone / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    )
    jdata = json.loads(jpath.read_text(encoding="utf-8"))
    rename_map: Dict[str, str] = dict(jdata.get("rename_map") or {})
    minted_ids: Dict[str, str] = dict(jdata.get("minted_ids") or {})

    mapped_pre_viols = {
        (_map_pre_migration_path(loc, rename_map) or loc, rule)
        for loc, rule in pre_attn_violations
    }
    new_attn_viols = [
        v
        for v in attn_all_doc.get("violations", [])
        if (v.get("location"), v.get("rule")) not in mapped_pre_viols
    ]
    assert new_attn_viols == [], (
        f"Migrated clone introduced {len(new_attn_viols)} new attention violations "
        f"(sample: {new_attn_viols[:5]})"
    )

    # AC-42 (5): before/after `aw find --agent` parity by mapped path and normalized status
    rc_post_find, out_post_find, err_post_find = _run_cli_inproc(
        clone, ["find", "--agent"], aw_home=aw_home
    )
    assert rc_post_find == 0, err_post_find or out_post_find
    post_find_items, post_find_summary = _parse_find_agent_stream(out_post_find)
    assert post_find_summary.get("complete") is True

    pre_mapped: Dict[str, Tuple[str, str]] = {}
    for item in pre_find_items:
        mapped = _map_pre_migration_path(item["path"], rename_map)
        if mapped is None:
            continue
        pre_mapped[mapped] = (
            item["type"],
            _normalize_find_status(item["type"], item.get("status")),
        )

    post_by_path: Dict[str, Dict[str, Any]] = {
        item["path"]: item for item in post_find_items
    }
    dropped = sorted(set(pre_mapped) - set(post_by_path))
    assert dropped == [], f"Dropped {len(dropped)} aw find items: {dropped[:10]}"

    status_diffs: List[Tuple[str, str, str, str]] = []
    for mapped_path, (pre_type, pre_norm_status) in sorted(pre_mapped.items()):
        post_item = post_by_path[mapped_path]
        post_norm_status = _normalize_find_status(
            post_item["type"], post_item.get("status")
        )
        if post_norm_status != pre_norm_status:
            status_diffs.append(
                (mapped_path, post_item["type"], pre_norm_status, post_norm_status)
            )
    assert (
        status_diffs == []
    ), f"{len(status_diffs)} aw find status mismatches (sample: {status_diffs[:10]})"

    minted_id_set = set(minted_ids.values())
    for extra_path in sorted(set(post_by_path) - set(pre_mapped)):
        extra_id = post_by_path[extra_path].get("id6")
        assert (
            extra_id in minted_id_set
        ), f"Post-migration-only aw find item {extra_path} ({extra_id!r}) was not minted"

    # Confirm source checkout is untouched
    assert _git(repo_root, "rev-parse", "HEAD").stdout.strip() == source_head_before
    assert _git(repo_root, "status", "--porcelain").stdout == source_status_before

"""Behavioral tests for `artifact_meta.check_staged_log_append` and `aw meta-log-append-gate`.

Covers IPD `jq82as` (E-01, E-02, V-01, V-02) and spec `4sd62s` 4.3 / 4.8.
Each fixture builds a real `git init` repository under `tmp_path` and exercises the real
`artifact_meta.check_staged_log_append` function and the real `aw meta-log-append-gate`
CLI leaf without inspecting production source code.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from agent_workflows import agent_schema, artifact_meta as meta, check_engine, engine

pytestmark = pytest.mark.core

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert proc.returncode == 0, (
        f"git {' '.join(args)} failed (rc={proc.returncode}):\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    return proc


def _init_git_repo(repo: Path) -> Path:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test Agent")
    _git(repo, "config", "user.email", "test-agent@example.com")
    (repo / ".aw" / "records" / "meta").mkdir(parents=True, exist_ok=True)
    return repo


def _run_aw_cli(repo: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{_REPO_ROOT}{os.pathsep}{existing_pp}" if existing_pp else str(_REPO_ROOT)
    )
    env["AW_NO_REEXEC"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "agent_workflows", *argv],
        cwd=str(repo),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )


def _create_event(id6: str = "ab12cd") -> Dict[str, Any]:
    return {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-09T12:00:00Z",
        "actor": {"tool": "aw ipd new"},
        "op": "create",
        "path": f"plans/pending/20261109-demo-01-{id6}-sample.ipd.md",
        "fields": {
            "id": id6,
            "type": "ipd",
            "status": "draft",
            "set": "demo",
            "order": 1,
        },
    }


def _transition_event(
    seq: int = 2,
    append: int = 2,
    *,
    from_status: str = "draft",
    to_status: str = "to-review",
    at: str = "2026-11-09T12:01:00Z",
) -> Dict[str, Any]:
    return {
        "v": 1,
        "seq": seq,
        "append": append,
        "at": at,
        "actor": {"tool": "aw set"},
        "op": "transition",
        "from": from_status,
        "to": to_status,
    }


def _note_event(
    seq: int = 3,
    append: int = 3,
    *,
    message: str = "recorded progress note",
    at: str = "2026-11-09T12:02:00Z",
) -> Dict[str, Any]:
    return {
        "v": 1,
        "seq": seq,
        "append": append,
        "at": at,
        "actor": {"tool": "aw ipd note"},
        "op": "note",
        "message": message,
    }


def _write_lf(path: Path, text: str) -> None:
    """Write UTF-8 text with strict LF line endings on every OS (including Windows/py3.9)."""
    path.write_bytes(text.encode("utf-8"))


def _seed_committed_log(repo: Path, id6: str, events: List[Dict[str, Any]]) -> Path:
    log_file = repo / ".aw" / "records" / "meta" / f"{id6}.jsonl"
    _write_lf(log_file, "".join(meta.encode_event(ev) for ev in events))
    rel = str(log_file.relative_to(repo)).replace("\\", "/")
    _git(repo, "add", rel)
    _git(repo, "commit", "-q", "-m", f"seed meta/{id6}.jsonl")
    return log_file


def _ctx(repo: Path) -> Any:
    return check_engine._git_read_at_context(repo)


# --------------------------------------------------------------------------------------
# V-01: Direct `artifact_meta.check_staged_log_append` tests (5 named fixtures)
# --------------------------------------------------------------------------------------


def test_check_staged_valid_append(tmp_path: Path) -> None:
    """Valid whole-line append with consecutive seq and valid append returns []."""
    repo = _init_git_repo(tmp_path)
    id6 = "ab12cd"
    base = [_create_event(id6), _transition_event(seq=2, append=2)]
    log_file = _seed_committed_log(repo, id6, base)

    updated = "".join(
        meta.encode_event(e) for e in [*base, _note_event(seq=3, append=3)]
    )
    _write_lf(log_file, updated)
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")

    with meta.ephemeral_if_uninitialized():
        reasons = meta.check_staged_log_append(id6, project_context=_ctx(repo))
    assert reasons == []


def test_check_staged_rewritten_earlier_line(tmp_path: Path) -> None:
    """Rewriting an earlier HEAD line is refused with a reason naming the log."""
    repo = _init_git_repo(tmp_path)
    id6 = "ab12ce"
    base = [_create_event(id6), _transition_event(seq=2, append=2)]
    log_file = _seed_committed_log(repo, id6, base)

    rewritten_first = dict(base[0])
    rewritten_first["fields"] = dict(base[0]["fields"], order=99)
    _write_lf(
        log_file, "".join(meta.encode_event(e) for e in [rewritten_first, base[1]])
    )
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")

    with meta.ephemeral_if_uninitialized():
        reasons = meta.check_staged_log_append(id6, project_context=_ctx(repo))
    assert reasons
    assert any(f".aw/records/meta/{id6}.jsonl" in r for r in reasons)
    assert any("rewrote" in r.lower() for r in reasons)


def test_check_staged_deleted_line(tmp_path: Path) -> None:
    """Deleting a HEAD line is refused with a reason naming the log."""
    repo = _init_git_repo(tmp_path)
    id6 = "ab12cf"
    base = [_create_event(id6), _transition_event(seq=2, append=2)]
    log_file = _seed_committed_log(repo, id6, base)

    _write_lf(log_file, meta.encode_event(base[0]))
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")

    with meta.ephemeral_if_uninitialized():
        reasons = meta.check_staged_log_append(id6, project_context=_ctx(repo))
    assert reasons
    assert any(f".aw/records/meta/{id6}.jsonl" in r for r in reasons)
    assert any("deleted" in r.lower() for r in reasons)


def test_check_staged_invalid_appended_event(tmp_path: Path) -> None:
    """Appending an invalid event (e.g. forbidden generic set of readiness) is refused naming the log."""
    repo = _init_git_repo(tmp_path)
    id6 = "ab12cg"
    base = [_create_event(id6), _transition_event(seq=2, append=2)]
    log_file = _seed_committed_log(repo, id6, base)

    bad_event = {
        "v": 1,
        "seq": 3,
        "append": 3,
        "at": "2026-11-09T12:02:00Z",
        "actor": {"tool": "hand-edit"},
        "op": "set",
        "fields": {"readiness": "go"},
    }
    _write_lf(log_file, "".join(meta.encode_event(e) for e in [*base, bad_event]))
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")

    with meta.ephemeral_if_uninitialized():
        reasons = meta.check_staged_log_append(id6, project_context=_ctx(repo))
    assert reasons
    assert any(f".aw/records/meta/{id6}.jsonl" in r for r in reasons)
    assert any("readiness" in r.lower() for r in reasons)


def test_check_staged_bad_first_event(tmp_path: Path) -> None:
    """A new staged log whose first event is not create seq 1 or checkpoint seq 0 is refused naming the log."""
    repo = _init_git_repo(tmp_path)
    id6 = "ab12ch"
    # Commit an unrelated seed file so HEAD exists.
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "initial commit")

    log_file = repo / ".aw" / "records" / "meta" / f"{id6}.jsonl"
    bad_first = _note_event(seq=1, append=1, message="not a create or checkpoint")
    _write_lf(log_file, meta.encode_event(bad_first))
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")

    with meta.ephemeral_if_uninitialized():
        reasons = meta.check_staged_log_append(id6, project_context=_ctx(repo))
    assert reasons
    assert any(f".aw/records/meta/{id6}.jsonl" in r for r in reasons)
    assert any("create" in r.lower() and "checkpoint" in r.lower() for r in reasons)


# --------------------------------------------------------------------------------------
# V-02: Real CLI `aw meta-log-append-gate` hook tests
# --------------------------------------------------------------------------------------


def test_hook_valid_append_exits_zero(tmp_path: Path) -> None:
    """aw meta-log-append-gate exits 0 on a valid staged append."""
    repo = _init_git_repo(tmp_path)
    id6 = "hk12cd"
    base = [_create_event(id6), _transition_event(seq=2, append=2)]
    log_file = _seed_committed_log(repo, id6, base)

    _write_lf(
        log_file,
        "".join(meta.encode_event(e) for e in [*base, _note_event(seq=3, append=3)]),
    )
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")

    res = _run_aw_cli(repo, "meta-log-append-gate")
    assert res.returncode == 0, res.stderr
    assert res.stderr == ""


def test_hook_rewritten_earlier_line_exits_one(tmp_path: Path) -> None:
    """aw meta-log-append-gate exits 1 and prints the refusal reason on a rewritten HEAD line."""
    repo = _init_git_repo(tmp_path)
    id6 = "hk12ce"
    base = [_create_event(id6), _transition_event(seq=2, append=2)]
    log_file = _seed_committed_log(repo, id6, base)

    rewritten_first = dict(base[0])
    rewritten_first["fields"] = dict(base[0]["fields"], order=42)
    _write_lf(
        log_file, "".join(meta.encode_event(e) for e in [rewritten_first, base[1]])
    )
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")

    res = _run_aw_cli(repo, "meta-log-append-gate")
    assert res.returncode == 1
    assert f".aw/records/meta/{id6}.jsonl" in res.stderr
    assert "rewrote" in res.stderr.lower()


def test_hook_deleted_line_exits_one(tmp_path: Path) -> None:
    """aw meta-log-append-gate exits 1 and prints the refusal reason on a deleted HEAD line."""
    repo = _init_git_repo(tmp_path)
    id6 = "hk12cf"
    base = [_create_event(id6), _transition_event(seq=2, append=2)]
    log_file = _seed_committed_log(repo, id6, base)

    _write_lf(log_file, meta.encode_event(base[0]))
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")

    res = _run_aw_cli(repo, "meta-log-append-gate")
    assert res.returncode == 1
    assert f".aw/records/meta/{id6}.jsonl" in res.stderr
    assert "deleted" in res.stderr.lower()


def test_hook_invalid_appended_event_exits_one(tmp_path: Path) -> None:
    """aw meta-log-append-gate exits 1 and prints the loader refusal on an invalid appended event."""
    repo = _init_git_repo(tmp_path)
    id6 = "hk12cg"
    base = [_create_event(id6), _transition_event(seq=2, append=2)]
    log_file = _seed_committed_log(repo, id6, base)

    bad_event = {
        "v": 1,
        "seq": 3,
        "append": 3,
        "at": "2026-11-09T12:02:00Z",
        "actor": {"tool": "hand-edit"},
        "op": "set",
        "fields": {"readiness": "go"},
    }
    _write_lf(log_file, "".join(meta.encode_event(e) for e in [*base, bad_event]))
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")

    res = _run_aw_cli(repo, "meta-log-append-gate")
    assert res.returncode == 1
    assert f".aw/records/meta/{id6}.jsonl" in res.stderr
    assert "readiness" in res.stderr.lower()


def test_hook_bad_first_event_exits_one(tmp_path: Path) -> None:
    """aw meta-log-append-gate exits 1 on a new log whose first event is not create/checkpoint."""
    repo = _init_git_repo(tmp_path)
    id6 = "hk12ch"
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "initial commit")

    log_file = repo / ".aw" / "records" / "meta" / f"{id6}.jsonl"
    bad_first = _note_event(seq=1, append=1, message="bad first")
    _write_lf(log_file, meta.encode_event(bad_first))
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")

    res = _run_aw_cli(repo, "meta-log-append-gate")
    assert res.returncode == 1
    assert f".aw/records/meta/{id6}.jsonl" in res.stderr
    assert "create" in res.stderr.lower()


def test_hook_noop_and_agent_envelope(tmp_path: Path) -> None:
    """aw meta-log-append-gate is a clean exit-0 no-op with no staged logs and emits valid --agent JSONL."""
    repo = _init_git_repo(tmp_path)
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "initial commit")

    res_clean = _run_aw_cli(repo, "meta-log-append-gate", "--agent")
    assert res_clean.returncode == 0, res_clean.stderr
    rec_clean = json.loads(res_clean.stdout.strip().splitlines()[-1])
    assert agent_schema.validate_agent_record(rec_clean) == []
    assert rec_clean["exit"] == 0
    assert rec_clean["outcome"] == "clean"

    # Stage a bad new log and verify --agent exit parity and schema validity.
    id6 = "hk12ci"
    log_file = repo / ".aw" / "records" / "meta" / f"{id6}.jsonl"
    _write_lf(log_file, meta.encode_event(_note_event(seq=1, append=1)))
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")

    res_bad = _run_aw_cli(repo, "meta-log-append-gate", "--agent")
    assert res_bad.returncode == 1
    rec_bad = json.loads(res_bad.stdout.strip().splitlines()[-1])
    assert agent_schema.validate_agent_record(rec_bad) == []
    assert rec_bad["exit"] == 1
    assert rec_bad["outcome"] == "findings"


# --------------------------------------------------------------------------------------
# Additional behavioral edge cases and engine opt-in hook installer coverage
# --------------------------------------------------------------------------------------


def test_append_edge_new_valid_create_and_checkpoint_logs(tmp_path: Path) -> None:
    """New logs starting with create seq 1 or checkpoint seq 0 pass even on unborn HEAD."""
    repo = _init_git_repo(tmp_path)
    id_create = "nw12aa"
    id_ckpt = "nw12bb"

    log_create = repo / ".aw" / "records" / "meta" / f"{id_create}.jsonl"
    _write_lf(log_create, meta.encode_event(_create_event(id_create)))

    ckpt_ev = {
        "v": 1,
        "seq": 0,
        "append": 0,
        "at": "2026-11-09T12:00:00Z",
        "actor": {"tool": "aw migrate metadata"},
        "op": "checkpoint",
        "path": f"plans/pending/20261109-demo-02-{id_ckpt}-migrated.ipd.md",
        "fields": {
            "id": id_ckpt,
            "type": "ipd",
            "status": "draft",
            "set": "demo",
            "order": 2,
        },
    }
    log_ckpt = repo / ".aw" / "records" / "meta" / f"{id_ckpt}.jsonl"
    _write_lf(log_ckpt, meta.encode_event(ckpt_ev))

    _git(
        repo,
        "add",
        f".aw/records/meta/{id_create}.jsonl",
        f".aw/records/meta/{id_ckpt}.jsonl",
    )

    with meta.ephemeral_if_uninitialized():
        assert meta.check_staged_log_append(id_create, project_context=_ctx(repo)) == []
        assert meta.check_staged_log_append(id_ckpt, project_context=_ctx(repo)) == []

    res = _run_aw_cli(repo, "meta-log-append-gate")
    assert res.returncode == 0, res.stderr


def test_append_edge_deleted_log_file_refused(tmp_path: Path) -> None:
    """Removing a committed metadata log file via git rm is refused."""
    repo = _init_git_repo(tmp_path)
    id6 = "dl12aa"
    _seed_committed_log(repo, id6, [_create_event(id6)])
    _git(repo, "rm", "-q", f".aw/records/meta/{id6}.jsonl")

    with meta.ephemeral_if_uninitialized():
        reasons = meta.check_staged_log_append(id6, project_context=_ctx(repo))
    assert reasons
    assert any(f".aw/records/meta/{id6}.jsonl" in r for r in reasons)

    res = _run_aw_cli(repo, "meta-log-append-gate")
    assert res.returncode == 1
    assert f".aw/records/meta/{id6}.jsonl" in res.stderr


def test_append_edge_renamed_log_file_refused(tmp_path: Path) -> None:
    """Renaming a committed meta log to a new valid id6 log is still refused as a deletion."""
    repo = _init_git_repo(tmp_path)
    old_id = "rn12aa"
    new_id = "rn12bb"
    _seed_committed_log(repo, old_id, [_create_event(old_id)])

    _git(repo, "rm", "-q", f".aw/records/meta/{old_id}.jsonl")
    meta_dir = repo / ".aw" / "records" / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    new_log = meta_dir / f"{new_id}.jsonl"
    _write_lf(new_log, meta.encode_event(_create_event(new_id)))
    _git(repo, "add", f".aw/records/meta/{new_id}.jsonl")

    res = _run_aw_cli(repo, "meta-log-append-gate")
    assert res.returncode == 1
    assert f".aw/records/meta/{old_id}.jsonl" in res.stderr


def test_append_edge_copied_identical_blob_id_mismatch_refused(tmp_path: Path) -> None:
    """Staging a second log with identical blob bytes (same blob SHA, wrong id6) is refused."""
    repo = _init_git_repo(tmp_path)
    orig_id = "cp12aa"
    copy_id = "cp12bb"
    payload = meta.encode_event(_create_event(orig_id))

    meta_dir = repo / ".aw" / "records" / "meta"
    _write_lf((meta_dir / f"{orig_id}.jsonl"), payload)
    _write_lf((meta_dir / f"{copy_id}.jsonl"), payload)
    _git(
        repo,
        "add",
        f".aw/records/meta/{orig_id}.jsonl",
        f".aw/records/meta/{copy_id}.jsonl",
    )

    res = _run_aw_cli(repo, "meta-log-append-gate")
    assert res.returncode == 1
    assert f".aw/records/meta/{copy_id}.jsonl" in res.stderr
    assert "identity-changed" in res.stderr.lower()


def test_append_edge_cross_commit_append_splice_and_seq_gap_refused(
    tmp_path: Path,
) -> None:
    """Splicing a new staged event into HEAD's append run or skipping a seq number is refused."""
    repo = _init_git_repo(tmp_path)
    id6 = "sp12aa"
    base = [_create_event(id6)]
    log_file = _seed_committed_log(repo, id6, base)

    # Attempt to splice seq=2 with append=1 (same at and actor as HEAD seq=1).
    spliced = {
        "v": 1,
        "seq": 2,
        "append": 1,
        "at": base[0]["at"],
        "actor": base[0]["actor"],
        "op": "note",
        "message": "spliced into committed append",
    }
    _write_lf(log_file, "".join(meta.encode_event(e) for e in [*base, spliced]))
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")
    with meta.ephemeral_if_uninitialized():
        reasons = meta.check_staged_log_append(id6, project_context=_ctx(repo))
    assert reasons
    assert any("append" in r.lower() for r in reasons)

    # Attempt a seq gap (seq=3 after seq=1).
    gapped = _note_event(seq=3, append=3, message="skipped seq 2")
    _write_lf(log_file, "".join(meta.encode_event(e) for e in [*base, gapped]))
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")
    with meta.ephemeral_if_uninitialized():
        reasons_gap = meta.check_staged_log_append(id6, project_context=_ctx(repo))
    assert reasons_gap
    assert any("seq" in r.lower() for r in reasons_gap)


def test_append_edge_non_lf_ending_and_bad_meta_filename_refused(
    tmp_path: Path,
) -> None:
    """An appended line missing its trailing LF or a non-id6 filename under meta/ is refused."""
    repo = _init_git_repo(tmp_path)
    id6 = "lf12aa"
    base = [_create_event(id6)]
    log_file = _seed_committed_log(repo, id6, base)

    no_lf = meta.encode_event(base[0]) + meta.encode_event(
        _note_event(seq=2, append=2)
    ).rstrip("\n")
    _write_lf(log_file, no_lf)
    _git(repo, "add", f".aw/records/meta/{id6}.jsonl")
    with meta.ephemeral_if_uninitialized():
        reasons = meta.check_staged_log_append(id6, project_context=_ctx(repo))
    assert reasons
    assert any("lf" in r.lower() for r in reasons)

    # Restore valid file, then stage a bad non-id6 filename under meta/.
    _git(repo, "checkout", "HEAD", "--", f".aw/records/meta/{id6}.jsonl")
    bad_file = repo / ".aw" / "records" / "meta" / "not-an-id6.jsonl"
    _write_lf(bad_file, "{}\n")
    _git(repo, "add", ".aw/records/meta/not-an-id6.jsonl")
    res = _run_aw_cli(repo, "meta-log-append-gate")
    assert res.returncode == 1
    assert ".aw/records/meta/not-an-id6.jsonl" in res.stderr


def test_engine_optin_meta_log_append_installer(tmp_path: Path) -> None:
    """engine.create_meta_log_append_gate_hook and create_local_leaks_backstop wire meta-log-append-gate opt-in."""
    pc_file = tmp_path / engine.PRE_COMMIT_CONFIG

    # Opt-out writes nothing.
    assert engine.create_meta_log_append_gate_hook(
        tmp_path, use_git=False, install=False
    ) == {"created": [], "skipped": [], "notes": []}
    assert not pc_file.exists()

    # Dry-run writes nothing and reports intent.
    dry = engine.create_meta_log_append_gate_hook(
        tmp_path, use_git=False, install=True, dry_run=True
    )
    assert not pc_file.exists()
    assert any("meta-log-append-gate" in n for n in dry["notes"])

    # Fresh install writes valid YAML containing meta-log-append-gate.
    created = engine.create_meta_log_append_gate_hook(
        tmp_path, use_git=False, install=True
    )
    assert created["created"] == [engine.PRE_COMMIT_CONFIG]
    parsed = yaml.safe_load(pc_file.read_text(encoding="utf-8"))
    hook_ids = [h["id"] for r in parsed.get("repos", []) for h in r.get("hooks", [])]
    assert "meta-log-append-gate" in hook_ids
    before_bytes = pc_file.read_bytes()

    # Idempotent second install leaves file byte-identical.
    second = engine.create_meta_log_append_gate_hook(
        tmp_path, use_git=False, install=True
    )
    assert any("already wired" in s for s in second["skipped"])
    assert pc_file.read_bytes() == before_bytes

    # Local-leaks backstop template also includes meta-log-append-gate.
    other = tmp_path / "backstop"
    other.mkdir()
    engine.create_local_leaks_backstop(
        other, use_git=False, install_ci=False, install_hook=True
    )
    backstop_yaml = yaml.safe_load(
        (other / engine.PRE_COMMIT_CONFIG).read_text(encoding="utf-8")
    )
    backstop_ids = [
        h["id"] for r in backstop_yaml.get("repos", []) for h in r.get("hooks", [])
    ]
    assert "meta-log-append-gate" in backstop_ids

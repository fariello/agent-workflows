"""Behavioral tests for `aw meta repair` (spec `4sd62s` 4.3, 4.7, 4.8; IPD `a5ijjx` E-02 / V-02).

Every synthetic log fixture is built inside its own `git init` repository using
`artifact_meta.encode_event` lines and a two-key `---` front-matter mirror directly (never
through `artifact_meta.create`/`append`, because phase B writes the legacy format).
No test reads production source code.
"""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple
from unittest.mock import patch

import pytest

from agent_workflows import artifact_meta, cli, meta_cli
from agent_workflows.agent_schema import validate_agent_record

pytestmark = pytest.mark.core


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout


def _commit_all(repo: Path, msg: str = "init") -> None:
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.email=t@example.invalid",
        "-c",
        "user.name=t",
        "commit",
        "-q",
        "-m",
        msg,
    )


def _init_repo(tmp_path: Path, name: str = "repo") -> Path:
    repo = (tmp_path / name).resolve()
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    return repo


def _run_cli(argv: List[str]) -> Tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdout", out), patch("sys.stderr", err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 1
    return rc, out.getvalue(), err.getvalue()


def _write_log(repo: Path, id6: str, events: List[Dict[str, Any]]) -> Path:
    meta_dir = repo / ".aw" / "records" / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    log_p = meta_dir / f"{id6}.jsonl"
    log_p.write_text(
        "".join(artifact_meta.encode_event(ev) for ev in events),
        encoding="utf-8",
    )
    return log_p


def _build_stale_mirror_fixture(tmp_path: Path) -> Tuple[Path, Path, Path]:
    repo = _init_repo(tmp_path, "stale_mirror")
    id6 = "mr0001"
    rel = f"plans/pending/20261109-mrset-01-{id6}-mirror-repair.ipd.md"
    doc_p = repo / ".aw" / "records" / rel
    doc_p.parent.mkdir(parents=True, exist_ok=True)
    doc_p.write_text(
        f"---\nid: {id6}\nstatus: draft\n---\n# IPD: Mirror repair fixture\n\nBody text.\n",
        encoding="utf-8",
    )
    log_p = _write_log(
        repo,
        id6,
        [
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-11-09T12:00:00Z",
                "actor": {"tool": "test"},
                "op": "create",
                "path": rel,
                "fields": {
                    "id": id6,
                    "type": "ipd",
                    "status": "draft",
                    "set": "mrset",
                    "order": 1,
                    "filename_date": "2026-11-09",
                },
            },
            {
                "v": 1,
                "seq": 2,
                "append": 2,
                "at": "2026-11-09T12:05:00Z",
                "actor": {"tool": "test"},
                "op": "transition",
                "from": "draft",
                "to": "to-review",
            },
        ],
    )
    _commit_all(repo)
    return repo, doc_p, log_p


def test_preview_then_apply_then_idempotent_mirror_repair(tmp_path: Path) -> None:
    """Preview exits 0 with clean git status; --apply rewrites mirror with byte-identical log; second --apply is a no-op."""
    repo, doc_p, log_p = _build_stale_mirror_fixture(tmp_path)
    log_bytes_before = log_p.read_bytes()

    # 1. Default preview: exits 0, shows mirror change, leaves git status clean
    rc_prev, out_prev, _ = _run_cli(["meta", "repair", "mr0001", "--dir", str(repo)])
    assert rc_prev == 0
    assert "mirror" in out_prev
    assert "draft" in out_prev and "to-review" in out_prev
    assert _git(repo, "status", "--porcelain") == ""

    # Preview under --agent obeys Section 11.3
    rc_pa, out_pa, _ = _run_cli(
        ["meta", "repair", "mr0001", "--dir", str(repo), "--agent"]
    )
    assert rc_pa == 0
    rec_pa = json.loads(out_pa.strip().splitlines()[-1])
    assert validate_agent_record(rec_pa) == []
    assert rec_pa["outcome"] == "preview"
    assert rec_pa["applied"] is False
    assert "--apply" in rec_pa["next"]
    assert _git(repo, "status", "--porcelain") == ""

    # 2. First --apply: rewrites mirror line, log stays byte-identical (no event added)
    rc_app1, out_app1, _ = _run_cli(
        ["meta", "repair", "mr0001", "--apply", "--dir", str(repo)]
    )
    assert rc_app1 == 0
    assert "Applied:" in out_app1
    assert log_p.read_bytes() == log_bytes_before
    diff_text = _git(repo, "diff")
    assert "-status: draft" in diff_text
    assert "+status: to-review" in diff_text
    status_after_first = _git(repo, "status", "--porcelain")
    doc_bytes_after_first = doc_p.read_bytes()

    # 3. Second --apply: idempotent, changes nothing
    rc_app2, out_app2, _ = _run_cli(
        ["meta", "repair", "mr0001", "--apply", "--dir", str(repo)]
    )
    assert rc_app2 == 0
    assert "nothing to repair" in out_app2
    assert log_p.read_bytes() == log_bytes_before
    assert doc_p.read_bytes() == doc_bytes_after_first
    assert _git(repo, "status", "--porcelain") == status_after_first


def test_move_repair_completes_pending_move_without_new_event(tmp_path: Path) -> None:
    """When the log transitioned to a new path but the file stayed at the old path, --apply completes the move and mirror repair."""
    repo = _init_repo(tmp_path, "move_repair")
    id6 = "mv0001"
    old_rel = f"plans/pending/20261109-mvset-01-{id6}-move-plan.ipd.md"
    new_rel = f"plans/executed/20261109-mvset-01-{id6}-move-plan.ipd.md"
    old_p = repo / ".aw" / "records" / old_rel
    new_p = repo / ".aw" / "records" / new_rel
    old_p.parent.mkdir(parents=True, exist_ok=True)
    old_p.write_text(
        f"---\nid: {id6}\nstatus: approved\n---\n# Move Plan\n\nBody.\n",
        encoding="utf-8",
    )
    log_p = _write_log(
        repo,
        id6,
        [
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-11-09T12:00:00Z",
                "actor": {"tool": "test"},
                "op": "create",
                "path": old_rel,
                "fields": {
                    "id": id6,
                    "type": "ipd",
                    "status": "approved",
                    "set": "mvset",
                    "order": 1,
                },
            },
            {
                "v": 1,
                "seq": 2,
                "append": 2,
                "at": "2026-11-09T12:10:00Z",
                "actor": {"tool": "test"},
                "op": "transition",
                "from": "approved",
                "to": "executed",
                "path": new_rel,
            },
        ],
    )
    _commit_all(repo)
    log_bytes_before = log_p.read_bytes()

    rc_prev, out_prev, _ = _run_cli(["meta", "repair", id6, "--dir", str(repo)])
    assert rc_prev == 0
    assert "[move]" in out_prev
    assert old_p.is_file() and not new_p.exists()

    rc_app, _, _ = _run_cli(["meta", "repair", id6, "--apply", "--dir", str(repo)])
    assert rc_app == 0
    assert not old_p.exists() and new_p.is_file()
    assert "status: executed" in new_p.read_text(encoding="utf-8")
    assert log_p.read_bytes() == log_bytes_before


def test_diverged_tail_requires_confirm_and_prints_field_changes(
    tmp_path: Path,
) -> None:
    """Diverged log tail prints every resulting field change, refuses --apply without --confirm, and resequences with --apply --confirm."""
    repo = _init_repo(tmp_path, "diverged")
    id6 = "dv0001"
    rel = f"plans/pending/20261109-dvset-01-{id6}-diverged.ipd.md"
    doc_p = repo / ".aw" / "records" / rel
    doc_p.parent.mkdir(parents=True, exist_ok=True)
    doc_p.write_text(
        f"---\nid: {id6}\nstatus: draft\n---\n# Diverged Plan\n\nBody.\n",
        encoding="utf-8",
    )
    log_p = _write_log(
        repo,
        id6,
        [
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-11-09T12:00:00Z",
                "actor": {"tool": "test"},
                "op": "create",
                "path": rel,
                "fields": {
                    "id": id6,
                    "type": "ipd",
                    "status": "draft",
                    "priority": "low",
                    "set": "dvset",
                    "order": 1,
                },
            },
            # Winning branch seq 2: transitions draft -> to-review
            {
                "v": 1,
                "seq": 2,
                "append": 2,
                "at": "2026-11-09T12:05:00Z",
                "actor": {"tool": "test"},
                "op": "transition",
                "from": "draft",
                "to": "to-review",
            },
            # Losing branch duplicate seq 2: sets priority high
            {
                "v": 1,
                "seq": 2,
                "append": 2,
                "at": "2026-11-09T12:06:00Z",
                "actor": {"tool": "test"},
                "op": "set",
                "fields": {"priority": "high"},
            },
        ],
    )
    _commit_all(repo)
    raw_lines_before = log_p.read_text(encoding="utf-8").splitlines(keepends=True)

    # 1. Preview prints every resulting field change and writes nothing
    rc_prev, out_prev, _ = _run_cli(["meta", "repair", id6, "--dir", str(repo)])
    assert rc_prev == 0
    assert "priority" in out_prev and "low" in out_prev and "high" in out_prev
    assert "--confirm" in out_prev
    assert _git(repo, "status", "--porcelain") == ""

    # 2. --apply without --confirm prints every resulting field change first and refuses (exit 2)
    rc_nc, out_nc, _ = _run_cli(["meta", "repair", id6, "--apply", "--dir", str(repo)])
    assert rc_nc == 2
    assert "priority" in out_nc and "high" in out_nc
    assert "--confirm" in out_nc
    assert _git(repo, "status", "--porcelain") == ""

    # 3. --apply --confirm resequences tail, preserves winning prefix byte-identically, updates mirror
    rc_ok, out_ok, _ = _run_cli(
        ["meta", "repair", id6, "--apply", "--confirm", "--dir", str(repo)]
    )
    assert rc_ok == 0
    assert "Applied:" in out_ok
    raw_lines_after = log_p.read_text(encoding="utf-8").splitlines(keepends=True)
    assert len(raw_lines_after) == 3
    assert raw_lines_after[:2] == raw_lines_before[:2]
    assert artifact_meta.decode_line(raw_lines_after[2])["seq"] == 3
    assert "status: to-review" in doc_p.read_text(encoding="utf-8")

    st = artifact_meta.read(id6, project_context=meta_cli.meta_context(repo))
    assert st.status == "to-review"
    assert st.fields["priority"] == "high"


def test_legacy_record_reports_nothing_to_repair(tmp_path: Path) -> None:
    """On a legacy record with no log sidecar, prints `nothing to repair (legacy format)` and exits 0."""
    repo = _init_repo(tmp_path, "legacy")
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261109-lgset-01-lg0001-legacy-plan.ipd.md"
    )
    p.write_text(
        "# IPD: Legacy Plan\n\n- Id: lg0001\n- Status: approved\n- Set: lgset\n- Order: 01\n\n## Goal\n\nBody.\n",
        encoding="utf-8",
    )
    _commit_all(repo)

    rc, out, _ = _run_cli(["meta", "repair", "lg0001", "--dir", str(repo)])
    assert rc == 0
    assert "nothing to repair (legacy format)" in out
    assert _git(repo, "status", "--porcelain") == ""

    rc_a, out_a, _ = _run_cli(
        ["meta", "repair", "lg0001", "--apply", "--dir", str(repo), "--agent"]
    )
    assert rc_a == 0
    rec = json.loads(out_a.strip().splitlines()[-1])
    assert validate_agent_record(rec) == []
    assert rec["outcome"] == "clean"
    assert rec["applied"] is False


def test_unknown_and_invalid_id6_exit_two(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path, "err_cases")
    _commit_all(repo)

    rc_bad, out_bad, _ = _run_cli(
        ["meta", "repair", "NOT-AN-ID", "--dir", str(repo), "--agent"]
    )
    assert rc_bad == 2
    rec_bad = json.loads(out_bad.strip().splitlines()[-1])
    assert validate_agent_record(rec_bad) == []
    assert rec_bad["outcome"] == "cannot-run"

    rc_miss, out_miss, _ = _run_cli(
        ["meta", "repair", "zz9999", "--dir", str(repo), "--agent"]
    )
    assert rc_miss == 2
    rec_miss = json.loads(out_miss.strip().splitlines()[-1])
    assert validate_agent_record(rec_miss) == []
    assert rec_miss["outcome"] == "cannot-run"


def test_orphan_log_missing_artifact_refuses_with_missing_recovery_source(
    tmp_path: Path,
) -> None:
    """When a log exists but the artifact file is absent on disk with no journal or prior path, repair refuses with exit 2."""
    repo = _init_repo(tmp_path, "missing_src")
    id6 = "ms0001"
    rel = f"plans/pending/20261109-msset-01-{id6}-missing.ipd.md"
    _write_log(
        repo,
        id6,
        [
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-11-09T12:00:00Z",
                "actor": {"tool": "test"},
                "op": "create",
                "path": rel,
                "fields": {
                    "id": id6,
                    "type": "ipd",
                    "status": "draft",
                    "set": "msset",
                    "order": 1,
                },
            }
        ],
    )
    _commit_all(repo)

    rc, out, _ = _run_cli(["meta", "repair", id6, "--dir", str(repo), "--agent"])
    assert rc == 2
    rec = json.loads(out.strip().splitlines()[-1])
    assert validate_agent_record(rec) == []
    assert rec["outcome"] == "cannot-run"
    assert any(
        d.get("rule") == "missing-recovery-source" for d in rec.get("diagnostics", [])
    )
    assert _git(repo, "status", "--porcelain") == ""


def test_meta_family_root_agent_conformance() -> None:
    rc, out, _ = _run_cli(["meta", "--agent"])
    assert rc == 2
    rec = json.loads(out.strip().splitlines()[-1])
    assert validate_agent_record(rec) == []
    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2
    assert rec.get("next")

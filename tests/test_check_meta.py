"""Behavioral tests for `aw check meta` (spec `4sd62s` 4.6; IPD `a5ijjx` E-01 / V-01).

Every test builds an isolated `tmp_path` fixture repository, runs the real `aw` CLI via
`cli.main`, and asserts on exit codes, parsed `aw.agent/v1` JSONL records, and rule ids.
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

from agent_workflows import artifact_meta, cli
from agent_workflows.agent_schema import validate_agent_record
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout


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


def _run_check_meta(repo: Path, *extra: str) -> Tuple[int, str, str]:
    return _run_cli(["check", "meta", "--dir", str(repo), *extra])


def _parse_jsonl(raw: str) -> List[Dict[str, Any]]:
    return [json.loads(ln) for ln in raw.splitlines() if ln.strip()]


def _write_clean_plan(
    repo: Path,
    id6: str = "cm0001",
    *,
    set_id: str = "cmset",
    order: int = 1,
    date_compact: str = "20261109",
    date_iso: str = "2026-11-09",
    status: str = "approved",
    disposition: str = "pending",
    ace: str | None = None,
    model: str | None = None,
    filename_override: str | None = None,
) -> Path:
    fname = (
        filename_override
        or f"{date_compact}-{set_id}-{order:02d}-{id6}-clean-plan.ipd.md"
    )
    p = repo / ".aw" / "records" / "plans" / disposition / fname
    p.parent.mkdir(parents=True, exist_ok=True)
    raw_fields: dict[str, Any] = {}
    if ace is not None:
        raw_fields["Ace"] = ace
    if model is not None:
        raw_fields["Model"] = model
    text = RecordBuilder().plan(
        id6=id6,
        title=f"Clean plan {id6}",
        when=date_iso,
        status=status,
        set_name=set_id,
        order=order,
        raw_fields=raw_fields or None,
        body="## Goal\n\nBody text.\n",
        text_only=True,
    )
    assert isinstance(text, str)
    p.write_text(text, encoding="utf-8")
    return p


def _write_log(repo: Path, id6: str, events: List[Dict[str, Any]]) -> Path:
    meta_dir = repo / ".aw" / "records" / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    log_p = meta_dir / f"{id6}.jsonl"
    log_p.write_text(
        "".join(artifact_meta.encode_event(ev) for ev in events),
        encoding="utf-8",
    )
    return log_p


def _finding_rules(records: List[Dict[str, Any]]) -> List[str]:
    return [r["rule"] for r in records if r.get("kind") == "item"]


# --------------------------------------------------------------------------------------------------
# Clean fixture and not-applicable rows
# --------------------------------------------------------------------------------------------------


def test_clean_fixture_exits_zero_and_names_not_applicable_rows(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path, "clean")
    _write_clean_plan(repo, "cl0001", order=1)

    spec_p = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / "approved"
        / "20261109-cmset-01-cl0002-clean-spec.spec.md"
    )
    spec_p.parent.mkdir(parents=True, exist_ok=True)
    spec_p.write_text(
        RecordBuilder().spec(
            title="Clean",
            when="2026-11-09",
            id6="cl0002",
            status="approved",
            set="cmset",
            order=1,
            body="## Scope\n\nText.",
            text_only=True,
        ),
        encoding="utf-8",
    )

    walk_p = (
        repo
        / ".aw"
        / "records"
        / "walkthroughs"
        / "20261109-cmset-01-cl0003-clean-walk.walkthrough.md"
    )
    walk_p.parent.mkdir(parents=True, exist_ok=True)
    walk_p.write_text(
        RecordBuilder().walkthrough(
            id6="cl0003",
            when="2026-11-09",
            set_name="cmset",
            order=1,
            body="# Walkthrough: Clean\n\nText.\n",
            text_only=True,
        ),
        encoding="utf-8",
    )

    res_p = (
        repo
        / ".aw"
        / "records"
        / "research"
        / "20261109-cmset-01-cl0004-clean-note.opus.findings.md"
    )
    res_p.parent.mkdir(parents=True, exist_ok=True)
    res_p.write_text(
        RecordBuilder().research(
            id6="cl0004",
            set="cmset",
            order=1,
            model="opus",
            research_kind="findings",
            status="active",
            body="\n# Clean Research\n\nBody.\n",
            text_only=True,
        ),
        encoding="utf-8",
    )

    rev_p = (
        repo
        / ".aw"
        / "records"
        / "reviews"
        / "20261109-cmset-01-cl0001-clean-plan.review.md"
    )
    rev_p.parent.mkdir(parents=True, exist_ok=True)
    rev_p.write_text(
        RecordBuilder().review(subject="cl0001", verdict="APPROVE", text_only=True),
        encoding="utf-8",
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    assert rc == 0, out
    recs = _parse_jsonl(out)
    assert len(recs) == 1
    summary = recs[-1]
    assert validate_agent_record(summary) == []
    assert summary["kind"] == "summary"
    assert summary["outcome"] == "clean"
    assert summary["exit"] == 0
    assert summary["total"] == 0
    assert summary["counts_by_rule"] == {}
    na_map = {row["row"]: row["status"] for row in summary["not_applicable"]}
    assert na_map == {
        "logged-path": "not-applicable (legacy format)",
        "orphan-record": "not-applicable (legacy format)",
    }


# --------------------------------------------------------------------------------------------------
# One named test per drift kind (all 11 phase-B drift kinds)
# --------------------------------------------------------------------------------------------------


def test_drift_status_mirror(tmp_path: Path) -> None:
    """In-file status mirror disagrees with replayed log status -> meta.status-mirror-drift."""
    repo = _init_repo(tmp_path, "status_mirror")
    rel = "plans/pending/20261109-smset-01-sm0001-status-drift.ipd.md"
    p = repo / ".aw" / "records" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        RecordBuilder().research(
            id6="sm0001",
            body="# Plan\n\nBody.\n",
            raw_fields={"status": "draft"},
            text_only=True,
        ),
        encoding="utf-8",
    )
    _write_log(
        repo,
        "sm0001",
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
                    "id": "sm0001",
                    "type": "ipd",
                    "status": "approved",
                    "set": "smset",
                    "order": 1,
                    "filename_date": "2026-11-09",
                },
            }
        ],
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.status-mirror-drift"]
    assert recs[-1]["counts_by_rule"] == {"meta.status-mirror-drift": 1}


def test_drift_id_mirror(tmp_path: Path) -> None:
    """In-file id mirror disagrees with log id -> meta.id-mirror-drift."""
    repo = _init_repo(tmp_path, "id_mirror")
    rel = "plans/pending/20261109-idset-01-im0001-id-drift.ipd.md"
    p = repo / ".aw" / "records" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        RecordBuilder().research(
            id6="zzzzzz",
            body="# Plan\n\nBody.\n",
            raw_fields={"status": "approved"},
            text_only=True,
        ),
        encoding="utf-8",
    )
    _write_log(
        repo,
        "im0001",
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
                    "id": "im0001",
                    "type": "ipd",
                    "status": "approved",
                    "set": "idset",
                    "order": 1,
                    "filename_date": "2026-11-09",
                },
            }
        ],
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.id-mirror-drift"]


def test_drift_filename_set(tmp_path: Path) -> None:
    """Filename Set disagrees with declared Set -> meta.filename-set-drift."""
    repo = _init_repo(tmp_path, "fn_set")
    _write_clean_plan(
        repo,
        "fs0001",
        set_id="rightset",
        filename_override="20261109-wrongset-01-fs0001-clean-plan.ipd.md",
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.filename-set-drift"]


def test_drift_filename_nn(tmp_path: Path) -> None:
    """Filename NN disagrees with declared Order -> meta.filename-order-drift."""
    repo = _init_repo(tmp_path, "fn_nn")
    _write_clean_plan(
        repo,
        "fn0001",
        order=2,
        filename_override="20261109-cmset-01-fn0001-clean-plan.ipd.md",
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.filename-order-drift"]


def test_drift_filename_id6(tmp_path: Path) -> None:
    """Filename id6 disagrees with declared Id -> meta.filename-id-drift."""
    repo = _init_repo(tmp_path, "fn_id6")
    _write_clean_plan(
        repo,
        "fi0001",
        filename_override="20261109-cmset-01-fi9999-clean-plan.ipd.md",
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.filename-id-drift"]


def test_drift_filename_date(tmp_path: Path) -> None:
    """Filename date disagrees with declared Date -> meta.filename-date-drift."""
    repo = _init_repo(tmp_path, "fn_date")
    _write_clean_plan(
        repo,
        "fd0001",
        date_compact="20261109",
        date_iso="2026-11-08",
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.filename-date-drift"]


def test_drift_d177_facet(tmp_path: Path) -> None:
    """D177 attribution facets (.ace.model.) disagree with cached fields -> meta.filename-d177-drift."""
    repo = _init_repo(tmp_path, "d177")
    _write_clean_plan(
        repo,
        "d10001",
        ace="opencode",
        model="sonnet",
        filename_override="20261109-cmset-01-d10001-clean-plan.opencode.opus.ipd.md",
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.filename-d177-drift"]


def test_drift_research_facet(tmp_path: Path) -> None:
    """Research filename facets (order, model, kind) disagree with front matter -> meta.research-facet-drift."""
    repo = _init_repo(tmp_path, "research_facet")
    res_p = (
        repo
        / ".aw"
        / "records"
        / "research"
        / "20261109-cmset-01-rf0001-study.opus.findings.md"
    )
    res_p.parent.mkdir(parents=True, exist_ok=True)
    res_p.write_text(
        RecordBuilder().research(
            id6="rf0001",
            set="cmset",
            order=1,
            model="opus",
            research_kind="survey",
            status="active",
            body="\n# Study\n\nBody.\n",
            text_only=True,
        ),
        encoding="utf-8",
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.research-facet-drift"]


def test_drift_disposition(tmp_path: Path) -> None:
    """Disposition directory disagrees with status -> meta.disposition-drift."""
    repo = _init_repo(tmp_path, "disposition")
    _write_clean_plan(
        repo,
        "dp0001",
        status="executed",
        disposition="pending",
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.disposition-drift"]


def test_drift_review_rounds(tmp_path: Path) -> None:
    """Review file rounds with missing/duplicate round numbers -> meta.review-rounds-drift."""
    repo = _init_repo(tmp_path, "review_rounds")
    _write_clean_plan(repo, "rr0001")
    rev_p = (
        repo
        / ".aw"
        / "records"
        / "reviews"
        / "20261109-cmset-01-rr0001-clean-plan.review.md"
    )
    rev_p.parent.mkdir(parents=True, exist_ok=True)
    # Skips Round 2: file has [1, 3] while cached review rows expect [1, 2, 3].
    rev_p.write_text(
        RecordBuilder().review(
            subject="rr0001",
            verdict="APPROVE",
            rounds=[{"number": 1}, {"number": 3}],
            text_only=True,
        ),
        encoding="utf-8",
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.review-rounds-drift"]


def test_drift_orphan_log(tmp_path: Path) -> None:
    """A meta/<id6>.jsonl file with no tracked record -> meta.orphan-log."""
    repo = _init_repo(tmp_path, "orphan_log")
    _write_clean_plan(repo, "ol0001")
    _write_log(
        repo,
        "orp999",
        [
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-11-09T12:00:00Z",
                "actor": {"tool": "test"},
                "op": "create",
                "path": "plans/pending/20261109-cmset-02-orp999-missing.ipd.md",
                "fields": {
                    "id": "orp999",
                    "type": "ipd",
                    "status": "draft",
                    "set": "cmset",
                    "order": 2,
                },
            }
        ],
    )

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.orphan-log"]
    item = next(r for r in recs if r["kind"] == "item")
    assert item["location"].endswith("meta/orp999.jsonl")


# --------------------------------------------------------------------------------------------------
# CLI contract: help, phase-B exclusion from `check all`, --limit, cannot-run
# --------------------------------------------------------------------------------------------------


def test_check_help_names_meta() -> None:
    rc, out, _ = _run_cli(["check", "--help"])
    assert rc == 0
    assert "meta" in out


def test_check_all_excludes_meta_rules_in_phase_b(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path, "all_excl")
    # Create an orphan log that `aw check meta` flags, and verify `aw check all` does not.
    _write_clean_plan(repo, "ae0001")
    _write_log(
        repo,
        "orp888",
        [
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-11-09T12:00:00Z",
                "actor": {"tool": "test"},
                "op": "create",
                "path": "plans/pending/20261109-cmset-02-orp888-missing.ipd.md",
                "fields": {"id": "orp888", "type": "ipd", "status": "draft"},
            }
        ],
    )
    rc_meta, out_meta, _ = _run_check_meta(repo, "--agent")
    assert rc_meta == 1
    assert "meta.orphan-log" in _finding_rules(_parse_jsonl(out_meta))

    _rc_all, out_all, _ = _run_cli(["check", "all", "--dir", str(repo), "--agent"])
    all_rec = _parse_jsonl(out_all)[-1]
    all_rules = [d.get("rule", "") for d in all_rec.get("diagnostics", [])]
    assert not any(r.startswith("meta.") for r in all_rules)


def test_check_meta_agent_limit_and_schema_validity(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path, "limit_test")
    _write_clean_plan(repo, "lm0001", status="executed", disposition="pending")
    _write_clean_plan(
        repo,
        "lm0002",
        order=2,
        filename_override="20261109-wrongset-02-lm0002-clean-plan.ipd.md",
    )

    rc, out, _ = _run_check_meta(repo, "--agent", "--limit", "1")
    assert rc == 1
    recs = _parse_jsonl(out)
    assert len(recs) == 2
    assert recs[0]["kind"] == "item"
    assert "location" in recs[0] and "rule" in recs[0]
    assert validate_agent_record(recs[0]) == []
    summary = recs[1]
    assert validate_agent_record(summary) == []
    assert summary["kind"] == "summary"
    assert summary["total"] == 2
    assert summary["emitted"] == 1
    assert summary["omitted"] == 1
    assert summary["complete"] is False
    assert "--limit 2" in summary["next"]


def test_duplicate_seq_log_never_passes_check_meta(tmp_path: Path) -> None:
    """A duplicate seq in a metadata log always produces a meta.invalid-log finding (AC-17)."""
    repo = _init_repo(tmp_path, "dup_seq")
    rel = "plans/pending/20261109-dvset-01-dv0002-dup-seq.ipd.md"
    p = repo / ".aw" / "records" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        RecordBuilder().research(
            id6="dv0002",
            body="# Plan\n\nBody.\n",
            raw_fields={"status": "draft"},
            text_only=True,
        ),
        encoding="utf-8",
    )
    _write_log(
        repo,
        "dv0002",
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
                    "id": "dv0002",
                    "type": "ipd",
                    "status": "draft",
                    "set": "dvset",
                    "order": 1,
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

    rc, out, _ = _run_check_meta(repo, "--agent")
    recs = _parse_jsonl(out)
    assert rc == 1
    assert _finding_rules(recs) == ["meta.invalid-log"]


def test_check_meta_outside_project_exits_two(tmp_path: Path) -> None:
    bare = (tmp_path / "bare").resolve()
    bare.mkdir()
    _git(bare, "init", "-q")

    rc, out, _ = _run_check_meta(bare, "--agent")
    assert rc == 2
    rec = _parse_jsonl(out)[-1]
    assert validate_agent_record(rec) == []
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2

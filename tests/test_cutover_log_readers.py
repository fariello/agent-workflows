"""Behavioral tests for the dormant post-cutover readers (IPD `wilgfy` E-02).

Spec `4sd62s` 4.4: on a log-format record `last_history_at` is the `at` of the newest event written
after the cutover, with `last_history_precision` `time`; with no such event it is the checkpoint
`last_history_day`, precision `day`. Spec 4.6: `aw check meta` reports a logged path that does not
exist on disk as `meta.path-drift`.

Every fixture is a real `git init` repository under `tmp_path`. A log-format fixture carries a
`.aw/records/meta/<id6>.jsonl` log and `metadata_schema: 2`; a legacy-format fixture carries neither,
which is the state of every repository before the cutover. The tests drive `aw attention` and
`aw check meta` through `cli.main` and assert on their output and exit codes.
"""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

import pytest

from agent_workflows import artifact_meta as meta, attention, cli
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core

_ID6 = "rd0001"
_LOGGED = f"plans/pending/20261109-demo-01-{_ID6}-sample.ipd.md"
_MOVED = f"plans/pending/20261109-demo-01-{_ID6}-moved.ipd.md"
_MIGRATED_AT = "2026-11-20T00:00:00Z"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )


def _init_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, schema: Optional[int]
) -> Path:
    monkeypatch.setenv("AW_HOME", str(tmp_path / "aw_home"))
    repo = (tmp_path / "repo").resolve()
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    _git(repo, "init", "-q")
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    if schema is not None:
        cfg = repo / ".aw" / "config"
        cfg.mkdir(parents=True)
        (cfg / "project.json").write_text(
            json.dumps({"metadata_schema": schema}) + "\n", encoding="utf-8"
        )
    return repo


def _write_log(repo: Path, events: List[Dict[str, Any]]) -> None:
    meta_dir = repo / ".aw" / "records" / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / f"{_ID6}.jsonl").write_bytes(
        "".join(meta.encode_event(e) for e in events).encode("utf-8")
    )


def _write_log_plan(repo: Path, rel: str = _LOGGED) -> None:
    (repo / ".aw" / "records" / rel).write_text(
        meta.render_in_file_mirror(_ID6, "ipd", "draft") + "# IPD: sample\n\nbody\n",
        encoding="utf-8",
    )


def _ev(seq: int, append: int, at: str, op: str, **payload: Any) -> Dict[str, Any]:
    ev: Dict[str, Any] = {
        "v": 1,
        "seq": seq,
        "append": append,
        "at": at,
        "actor": {"tool": "aw test"},
        "op": op,
    }
    ev.update(payload)
    return ev


def _created_log(*later: Dict[str, Any]) -> List[Dict[str, Any]]:
    """A record created after the cutover, plus `later` events."""
    create = _ev(
        1,
        1,
        "2026-11-09T12:00:00Z",
        "create",
        path=_LOGGED,
        fields={
            "id": _ID6,
            "type": "ipd",
            "status": "draft",
            "set": "demo",
            "order": 1,
        },
    )
    return [create, *later]


def _migrated_log(*later: Dict[str, Any]) -> List[Dict[str, Any]]:
    """A migrated record: the seq-0 checkpoint and an imported legacy line, both `append` 0."""
    checkpoint = _ev(
        0,
        0,
        _MIGRATED_AT,
        "checkpoint",
        path=_LOGGED,
        fields={
            "type": "ipd",
            "status": "draft",
            "set": "demo",
            "order": 1,
            "last_history_day": "2026-10-14",
        },
    )
    legacy = _ev(
        1,
        0,
        _MIGRATED_AT,
        "legacy",
        source="history",
        position=0,
        ordering_confidence="unknown",
        observed_day="2026-10-14",
        line="- 2026-10-14 draft (aw ipd scaffold): created",
    )
    return [checkpoint, legacy, *later]


def _run_cli(argv: List[str]) -> Tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdout", out), patch("sys.stderr", err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 1
    return rc, out.getvalue(), err.getvalue()


def _attention_items(repo: Path) -> List[Dict[str, Any]]:
    rc, out, err = _run_cli(["attention", "--dir", str(repo), "--format", "json"])
    assert rc == 0, err
    return json.loads(out)["items"]


def _check_meta_records(repo: Path) -> Tuple[int, List[Dict[str, Any]]]:
    rc, out, _ = _run_cli(["check", "meta", "--dir", str(repo), "--agent"])
    return rc, [json.loads(ln) for ln in out.splitlines() if ln.strip()]


# --------------------------------------------------------------------------------------------------
# last_history_at / last_history_precision (spec 4.4)
# --------------------------------------------------------------------------------------------------


def test_last_history_at_is_newest_post_cutover_event_at_with_time_precision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=2)
    _write_log_plan(repo)
    _write_log(
        repo,
        _created_log(_ev(2, 2, "2026-11-10T08:30:00Z", "note", message="touched")),
    )

    (item,) = _attention_items(repo)
    assert item["id"] == _ID6
    assert item["last_history_at"] == "2026-11-10T08:30:00Z"
    assert item["last_history_precision"] == "time"


def test_migrated_record_after_one_setter_event_reads_that_event_at(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=2)
    _write_log_plan(repo)
    _write_log(
        repo,
        _migrated_log(
            _ev(
                2,
                2,
                "2026-11-21T09:15:00Z",
                "transition",
                **{"from": "draft", "to": "to-review"},
            )
        ),
    )

    (item,) = _attention_items(repo)
    assert item["last_history_at"] == "2026-11-21T09:15:00Z"
    assert item["last_history_precision"] == "time"


def test_migrated_only_record_falls_back_to_checkpoint_day_not_migration_at(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=2)
    _write_log_plan(repo)
    _write_log(repo, _migrated_log())

    (item,) = _attention_items(repo)
    # The migration's own `at` (2026-11-20) must not make the record look touched on cutover day.
    assert item["last_history_at"] == "2026-10-14"
    assert item["last_history_precision"] == "day"


def test_artifact_meta_last_history_returns_value_and_precision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=2)
    _write_log_plan(repo)
    _write_log(repo, _migrated_log())
    ctx = meta.legacy_context(repo)
    with meta.ephemeral_if_uninitialized():
        assert meta.last_history(_ID6, project_context=ctx) == ("2026-10-14", "day")

    _write_log(
        repo, _migrated_log(_ev(2, 2, "2026-11-22T10:00:00Z", "note", message="x"))
    )
    with meta.ephemeral_if_uninitialized():
        assert meta.last_history(_ID6, project_context=ctx) == (
            "2026-11-22T10:00:00Z",
            "time",
        )


def test_log_record_below_schema_2_keeps_the_day_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    _write_log_plan(repo)
    _write_log(
        repo,
        _created_log(_ev(2, 2, "2026-11-10T08:30:00Z", "note", message="touched")),
    )

    (item,) = _attention_items(repo)
    assert item["last_history_at"] == "2026-11-10"
    assert "last_history_precision" not in item


def test_legacy_record_output_is_unchanged_at_schema_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _legacy_items(schema: Optional[int], sub: str) -> List[Dict[str, Any]]:
        base = tmp_path / sub
        base.mkdir()
        repo = _init_repo(base, monkeypatch, schema=schema)
        (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20261109-demo-01-lg0001-legacy.ipd.md"
        ).write_text(
            RecordBuilder().plan(
                id6="lg0001",
                status="to-review",
                history=["- 2026-11-03 to-review (aw ipd scaffold): created"],
                text_only=True,
            ),
            encoding="utf-8",
        )
        return _attention_items(repo)

    with_schema = _legacy_items(2, "a")
    without_schema = _legacy_items(None, "b")
    assert with_schema == without_schema
    (item,) = with_schema
    assert item["last_history_at"] == "2026-11-03"
    assert "last_history_precision" not in item


def test_staleness_marker_reads_a_time_precision_value() -> None:
    from datetime import date

    today = date(2026, 11, 23)
    assert attention._age_marker("2026-11-20T08:30:00Z", "plans", today=today) == ""
    assert attention._age_marker("2026-09-01T08:30:00Z", "plans", today=today) == "!"
    assert attention._age_marker("2026-09-01", "plans", today=today) == "!"


# --------------------------------------------------------------------------------------------------
# aw check meta logged-path drift (spec 4.6)
# --------------------------------------------------------------------------------------------------


def test_check_meta_reports_planted_path_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=2)
    _write_log_plan(repo, _MOVED)
    _write_log(repo, _created_log())

    rc, recs = _check_meta_records(repo)
    assert rc == 1
    items = [r for r in recs if r["kind"] == "item"]
    assert [r["rule"] for r in items] == ["meta.path-drift"]
    assert f"logged path '{_LOGGED}' does not exist on disk" in items[0]["detail"]
    summary = recs[-1]
    assert summary["counts_by_rule"] == {"meta.path-drift": 1}
    assert summary["not_applicable"] == []


def test_check_meta_is_clean_when_logged_path_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=2)
    _write_log_plan(repo)
    _write_log(repo, _created_log())

    rc, recs = _check_meta_records(repo)
    assert rc == 0, recs
    summary = recs[-1]
    assert summary["outcome"] == "clean"
    assert summary["counts_by_rule"] == {}
    assert summary["not_applicable"] == []


def test_check_meta_logged_path_row_is_not_applicable_on_a_legacy_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261109-demo-01-lg0002-legacy.ipd.md"
    ).write_text(
        RecordBuilder().plan(
            id6="lg0002",
            status="to-review",
            history=["- 2026-11-03 to-review (aw ipd scaffold): created"],
            text_only=True,
        ),
        encoding="utf-8",
    )

    rc, recs = _check_meta_records(repo)
    summary = recs[-1]
    assert "meta.path-drift" not in summary["counts_by_rule"]
    na_map = {row["row"]: row["status"] for row in summary["not_applicable"]}
    assert na_map["logged-path"] == "not-applicable (legacy format)"

"""Behavioral tests for the dormant `rename` events of `aw rename`, `aw group` and `aw archive plans`.

IPD `v45j1n` (spec `4sd62s` 4.2 PATH HISTORY, AC-31, AC-34, C10a). Each log-format fixture is a real
`git init` repository under `tmp_path` whose `project.json` carries `metadata_schema: 2` and whose
record has a `.aw/records/meta/<id6>.jsonl` log; each legacy fixture has no log, which is the state
of every record before the cutover. The tests drive the real CLI through `cli.main` and assert on
exit codes, the bytes of the log, the files on disk, the rename ledger and `aw show --history`.

Node names carry `rename`, `group` or `archive` so the plan's `-k` selections pick them.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from agent_workflows import artifact_meta as meta
from agent_workflows import cli, meta_cli

pytestmark = pytest.mark.core

_SPEC_ID = "sp34ef"
_SPEC_PATH = "specs/draft/20261109-sp34ef-01-sp34ef-sample.spec.md"
_PLAN_ID = "ab12cd"
_PLAN_PENDING = "plans/pending/20261109-demo-01-ab12cd-sample.ipd.md"
_PLAN_EXECUTED = "plans/executed/20261109-demo-01-ab12cd-sample.ipd.md"
_AT = "2026-11-09T12:00:00Z"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, f"git {' '.join(args)} failed: {proc.stderr}"
    return proc


def _init_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, schema: Optional[int] = 2
) -> Path:
    monkeypatch.setenv("AW_HOME", str(tmp_path / "aw_home"))
    repo = tmp_path / "repo"
    (repo / ".aw" / "records").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test Agent")
    _git(repo, "config", "user.email", "test-agent@example.com")
    if schema is not None:
        cfg = repo / ".aw" / "config"
        cfg.mkdir(parents=True)
        (cfg / "project.json").write_text(
            json.dumps({"metadata_schema": schema}) + "\n", encoding="utf-8"
        )
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def _commit_all(repo: Path, msg: str = "seed") -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


def _records(repo: Path) -> Path:
    return repo / ".aw" / "records"


def _log(repo: Path, id6: str) -> Path:
    return _records(repo) / "meta" / f"{id6}.jsonl"


def _events(repo: Path, id6: str) -> List[Dict[str, Any]]:
    return [
        json.loads(line)
        for line in _log(repo, id6).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _ledger(repo: Path) -> List[Dict[str, Any]]:
    p = _records(repo) / "history.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]


def _run(argv: List[str]) -> int:
    return cli.main(argv)


@pytest.fixture
def log_spec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A migrated repository holding one log-format spec."""
    repo = _init_repo(tmp_path, monkeypatch)
    (_records(repo) / "meta").mkdir()
    res = meta.create(
        _SPEC_ID,
        "spec",
        {"status": "draft", "title": "sample"},
        "# sample\n",
        destination=_SPEC_PATH,
        project_context=meta_cli.meta_context(repo),
        actor={"tool": "aw test"},
    )
    assert res.get("committed"), res
    _commit_all(repo)
    return repo


@pytest.fixture
def legacy_spec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An unmigrated repository holding one legacy (bullet front matter) spec, no log."""
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    p = _records(repo) / _SPEC_PATH
    p.parent.mkdir(parents=True)
    p.write_text(
        "# Spec: sample\n\n"
        f"- Id: {_SPEC_ID}\n"
        "- Status: draft\n"
        "- Set: sp34ef\n\n"
        "Body.\n\n"
        "## Workflow history\n\n"
        "- 2026-11-09 created (aw test)\n",
        encoding="utf-8",
    )
    _commit_all(repo)
    return repo


def _history_rows(
    repo: Path, id6: str, capsys: pytest.CaptureFixture[str]
) -> List[Dict[str, Any]]:
    """`aw show <id6> --history --json`, driven through the real CLI."""
    capsys.readouterr()
    rc = cli.main(["show", id6, "--history", "--json", "--dir", str(repo)])
    out = capsys.readouterr().out
    assert rc == 0, out
    [rec] = json.loads(out)["data"]["records"]
    return rec["history"]


def _path_sequence(
    repo: Path, id6: str, capsys: pytest.CaptureFixture[str]
) -> List[str]:
    return [ev["path"] for ev in _history_rows(repo, id6, capsys) if ev.get("path")]


# --------------------------------------------------------------------------------------
# E-02 / V-02: aw rename
# --------------------------------------------------------------------------------------


def test_rename_on_log_format_appends_one_rename_event(
    log_spec: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = log_spec
    before = _events(repo, _SPEC_ID)
    rc = _run(
        [
            "rename",
            "specs",
            _SPEC_ID,
            "--slug",
            "renamed",
            "--dir",
            str(repo),
            "--apply",
        ]
    )
    assert rc == 0
    new_rel = "specs/draft/20261109-sp34ef-01-sp34ef-renamed.spec.md"
    assert not (_records(repo) / _SPEC_PATH).exists()
    assert (_records(repo) / new_rel).is_file()
    after = _events(repo, _SPEC_ID)
    assert after[: len(before)] == before
    added = after[len(before) :]
    assert [(e["op"], e.get("verb"), e.get("path")) for e in added] == [
        ("rename", "rename", new_rel)
    ]
    assert "from" not in added[0] and added[0]["seq"] == before[-1]["seq"] + 1
    # `aw show <id6> --history` lists the old path, then the new one.
    assert _path_sequence(repo, _SPEC_ID, capsys) == [_SPEC_PATH, new_rel]
    # The log event replaces the ledger line for a log-format record.
    assert _ledger(repo) == []
    assert meta.read(_SPEC_ID, project_context=meta_cli.meta_context(repo)).path == (
        new_rel
    )


def test_rename_with_set_on_log_format_pairs_rename_and_set_in_one_append(
    log_spec: Path,
) -> None:
    repo = log_spec
    rc = _run(
        ["rename", "specs", _SPEC_ID, "--set", "newset", "--dir", str(repo), "--apply"]
    )
    assert rc == 0
    added = _events(repo, _SPEC_ID)[1:]
    assert [e["op"] for e in added] == ["rename", "set"]
    assert added[0]["verb"] == "rename"
    assert added[0]["path"] == "specs/draft/20261109-newset-01-sp34ef-sample.spec.md"
    assert added[1]["fields"] == {"set": "newset"}
    assert len({e["append"] for e in added}) == 1


def test_rename_on_legacy_format_keeps_bytes_and_ledger(legacy_spec: Path) -> None:
    repo = legacy_spec
    src = _records(repo) / _SPEC_PATH
    original = src.read_bytes()
    rc = _run(
        [
            "rename",
            "specs",
            _SPEC_ID,
            "--slug",
            "renamed",
            "--dir",
            str(repo),
            "--apply",
        ]
    )
    assert rc == 0
    dst = _records(repo) / "specs/draft/20261109-sp34ef-01-sp34ef-renamed.spec.md"
    assert not src.exists()
    assert dst.read_bytes() == original
    assert not (_records(repo) / "meta").exists()
    [line] = _ledger(repo)
    assert line["verb"] == "rename"
    assert line["from_name"] == "20261109-sp34ef-01-sp34ef-sample.spec.md"
    assert line["to_name"] == dst.name


def test_rename_refused_by_the_log_leaves_the_file_in_place(
    log_spec: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = log_spec
    before = _log(repo, _SPEC_ID).read_bytes()

    def _refuse(*_a: Any, **_k: Any) -> Any:
        raise ValueError("synthetic refusal")

    monkeypatch.setattr(meta, "append", _refuse)
    rc = _run(
        [
            "rename",
            "specs",
            _SPEC_ID,
            "--slug",
            "renamed",
            "--dir",
            str(repo),
            "--apply",
        ]
    )
    assert rc == 2
    assert (_records(repo) / _SPEC_PATH).is_file()
    assert _log(repo, _SPEC_ID).read_bytes() == before


# --------------------------------------------------------------------------------------
# E-03 / V-03: aw group
# --------------------------------------------------------------------------------------


def test_group_on_log_format_appends_rename_and_set_in_one_append(
    log_spec: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = log_spec
    before = _events(repo, _SPEC_ID)
    rc = _run(
        [
            "group",
            "specs",
            _SPEC_ID,
            "--set",
            "newset",
            "--rename",
            "--dir",
            str(repo),
            "--apply",
        ]
    )
    assert rc == 0
    new_rel = "specs/draft/20261109-newset-01-sp34ef-sample.spec.md"
    assert (_records(repo) / new_rel).is_file()
    assert not (_records(repo) / _SPEC_PATH).exists()
    added = _events(repo, _SPEC_ID)[len(before) :]
    assert [(e["op"], e.get("verb"), e.get("path")) for e in added] == [
        ("rename", "group", new_rel),
        ("set", None, None),
    ]
    assert added[1]["fields"] == {"set": "newset"}
    assert added[0]["append"] == added[1]["append"]
    assert _path_sequence(repo, _SPEC_ID, capsys) == [_SPEC_PATH, new_rel]
    assert _ledger(repo) == []
    # The mirror front matter is untouched: the Set lives in the log.
    text = (_records(repo) / new_rel).read_text(encoding="utf-8")
    assert "- Set:" not in text
    st = meta.read(_SPEC_ID, project_context=meta_cli.meta_context(repo))
    assert st.set_id == "newset" and st.path == new_rel


def test_group_on_legacy_format_keeps_ledger_and_bullet(legacy_spec: Path) -> None:
    repo = legacy_spec
    rc = _run(
        [
            "group",
            "specs",
            _SPEC_ID,
            "--set",
            "newset",
            "--rename",
            "--dir",
            str(repo),
            "--apply",
        ]
    )
    assert rc == 0
    dst = _records(repo) / "specs/draft/20261109-newset-01-sp34ef-sample.spec.md"
    assert "- Set: newset" in dst.read_text(encoding="utf-8")
    assert not (_records(repo) / "meta").exists()
    [line] = _ledger(repo)
    assert line["verb"] == "group"
    assert line["to_name"] == dst.name


# --------------------------------------------------------------------------------------
# E-04 / V-04: aw archive plans
# --------------------------------------------------------------------------------------


def _executed_plan_log() -> str:
    events: List[Dict[str, Any]] = []

    def add(*payloads: Dict[str, Any]) -> None:
        first = (events[-1]["seq"] if events else 0) + 1
        for i, p in enumerate(payloads):
            ev = {
                "v": 1,
                "seq": first + i,
                "append": first,
                "at": _AT,
                "actor": {"tool": "aw test"},
            }
            ev.update(p)
            events.append(ev)

    add(
        {
            "op": "create",
            "path": _PLAN_PENDING,
            "fields": {
                "id": _PLAN_ID,
                "type": "ipd",
                "status": "draft",
                "set": "demo",
                "order": 1,
            },
        }
    )
    for frm, to in (
        ("draft", "to-review"),
        ("to-review", "reviewed"),
        ("reviewed", "approved"),
    ):
        add({"op": "transition", "from": frm, "to": to})
    add(
        {
            "op": "transition",
            "from": "approved",
            "to": "executed",
            "path": _PLAN_EXECUTED,
        }
    )
    return "".join(meta.encode_event(e) for e in events)


@pytest.fixture
def log_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A migrated repository holding one executed log-format plan at its terminal-dir root."""
    repo = _init_repo(tmp_path, monkeypatch)
    (_records(repo) / "meta").mkdir()
    _log(repo, _PLAN_ID).write_text(_executed_plan_log(), encoding="utf-8")
    p = _records(repo) / _PLAN_EXECUTED
    p.parent.mkdir(parents=True)
    p.write_text(
        meta.render_in_file_mirror(_PLAN_ID, "ipd", "executed")
        + "# IPD: sample\n\nbody\n",
        encoding="utf-8",
    )
    (_records(repo) / "plans" / "pending").mkdir(parents=True)
    _commit_all(repo)
    return repo


@pytest.fixture
def legacy_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An unmigrated repository holding one executed legacy plan, no log."""
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    p = _records(repo) / _PLAN_EXECUTED
    p.parent.mkdir(parents=True)
    p.write_text(
        "# IPD: sample\n\n"
        f"- Id: {_PLAN_ID}\n"
        "- Status: executed\n"
        "- Set: demo\n"
        "- Created: 2026-11-09\n\n"
        "body\n\n"
        "## Workflow history\n\n"
        "- 2026-11-09 executed (aw test)\n",
        encoding="utf-8",
    )
    _commit_all(repo)
    return repo


def _sharded(repo: Path) -> List[Path]:
    return sorted(
        p
        for p in (_records(repo) / "plans" / "executed").rglob("*.ipd.md")
        if p.parent.name != "executed"
    )


def test_archive_on_log_format_appends_archive_rename_event(
    log_plan: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = log_plan
    before = _events(repo, _PLAN_ID)
    rc = _run(["archive", "plans", _PLAN_ID, "--dir", str(repo), "--apply"])
    assert rc == 0
    [moved] = _sharded(repo)
    new_rel = moved.relative_to(_records(repo)).as_posix()
    assert not (_records(repo) / _PLAN_EXECUTED).exists()
    added = _events(repo, _PLAN_ID)[len(before) :]
    assert [(e["op"], e.get("verb"), e.get("path")) for e in added] == [
        ("rename", "archive", new_rel)
    ]
    assert _path_sequence(repo, _PLAN_ID, capsys) == [
        _PLAN_PENDING,
        _PLAN_EXECUTED,
        new_rel,
    ]
    assert _ledger(repo) == []


def test_archive_on_legacy_format_moves_bytes_unchanged(legacy_plan: Path) -> None:
    repo = legacy_plan
    original = (_records(repo) / _PLAN_EXECUTED).read_bytes()
    rc = _run(["archive", "plans", _PLAN_ID, "--dir", str(repo), "--apply"])
    assert rc == 0
    [moved] = _sharded(repo)
    assert moved.read_bytes() == original
    assert not (_records(repo) / "meta").exists()

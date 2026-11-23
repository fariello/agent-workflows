"""Behavioral tests for event `overrides` and the `aw specs set --date` refusal (IPD `wilgfy` E-03).

Spec `4sd62s` 4.2: every event a setter writes with `--allow-open-questions`,
`--allow-terminal-reopen` or `--allow-unresolvable-release-sentinel` carries an `overrides` list
naming each flag given, and no `overrides` key when none was given. `aw specs set --date` is refused
once `metadata_schema` is 2, because an event's `at` is always its write time.

Each log-format fixture is a real `git init` repository under `tmp_path` whose spec has a
`.aw/records/meta/<id6>.jsonl` log and whose `project.json` carries `metadata_schema: 2`. Each
legacy-format fixture has neither, which is the state of every repository before the cutover; there
the setter keeps rendering the flag as a history-line actor suffix. The tests drive the real
`aw specs set` through `cli.main` and assert on exit codes, output and the bytes on disk.
"""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

import pytest

from agent_workflows import artifact_meta as meta, cli
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core

_ID6 = "ov0001"
_REL = f"specs/20261109-{_ID6}-01-{_ID6}-sample.spec.md"
_AT = "2026-11-09T12:00:00Z"
_BLOCKING_OQ = (
    "\n## Open questions\n\n### OQ-01: still open\n\n- Blocking: yes\n- Status: open\n"
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )


def _init_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, schema: Optional[int]
) -> Path:
    monkeypatch.setenv("AW_HOME", str(tmp_path / "aw_home"))
    repo = (tmp_path / "repo").resolve()
    (repo / ".aw" / "records" / "specs").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test Agent")
    _git(repo, "config", "user.email", "test-agent@example.com")
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    if schema is not None:
        cfg = repo / ".aw" / "config"
        cfg.mkdir(parents=True)
        (cfg / "project.json").write_text(
            json.dumps({"metadata_schema": schema}) + "\n", encoding="utf-8"
        )
    return repo


def _commit_all(repo: Path) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed")


def _log_spec(repo: Path, *, open_question: bool) -> Path:
    """A log-format spec at `reviewed`: an in-file mirror plus its event log."""
    spec = repo / ".aw" / "records" / _REL
    spec.write_text(
        meta.render_in_file_mirror(_ID6, "spec", "reviewed")
        + "# Spec: sample\n"
        + (_BLOCKING_OQ if open_question else ""),
        encoding="utf-8",
    )
    envelope = {"v": 1, "at": _AT, "actor": {"tool": "aw test"}}
    events = [
        dict(
            envelope,
            seq=1,
            append=1,
            op="create",
            path=_REL,
            fields={"id": _ID6, "type": "spec", "status": "draft"},
        ),
        dict(
            envelope,
            seq=2,
            append=2,
            op="transition",
            to="to-review",
            **{"from": "draft"},
        ),
        dict(
            envelope,
            seq=3,
            append=3,
            op="transition",
            to="reviewed",
            **{"from": "to-review"},
        ),
    ]
    meta_dir = repo / ".aw" / "records" / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / f"{_ID6}.jsonl").write_bytes(
        "".join(meta.encode_event(e) for e in events).encode("utf-8")
    )
    _commit_all(repo)
    return spec


def _legacy_spec(repo: Path, *, open_question: bool) -> Path:
    spec = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / "reviewed"
        / f"20261109-{_ID6}-01-{_ID6}-sample.spec.md"
    )
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(
        RecordBuilder().spec(
            id6=_ID6,
            status="reviewed",
            when="2026-11-09",
            history=["- 2026-11-09 reviewed (aw specs): reviewed"],
            body="\n# Spec: sample\n" + (_BLOCKING_OQ if open_question else ""),
            text_only=True,
        ),
        encoding="utf-8",
    )
    _commit_all(repo)
    return spec


def _run_cli(argv: List[str]) -> Tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdout", out), patch("sys.stderr", err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 1
    return rc, out.getvalue(), err.getvalue()


def _specs_set(repo: Path, *extra: str) -> Tuple[int, str, str]:
    return _run_cli(
        [
            "specs",
            "set",
            "approved",
            _ID6,
            "--dir",
            str(repo),
            "--by-human",
            "--message",
            "approved for the test",
            "--yes",
            "--no-commit",
            *extra,
        ]
    )


def _log_events(repo: Path) -> List[Dict[str, Any]]:
    raw = (repo / ".aw" / "records" / "meta" / f"{_ID6}.jsonl").read_text(
        encoding="utf-8"
    )
    return [json.loads(ln) for ln in raw.splitlines() if ln.strip()]


def _tree_bytes(repo: Path) -> Dict[str, bytes]:
    root = repo / ".aw" / "records"
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


# --------------------------------------------------------------------------------------------------
# overrides on a log-format record
# --------------------------------------------------------------------------------------------------


def test_setter_writes_overrides_when_allow_open_questions_is_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=2)
    spec = _log_spec(repo, open_question=True)

    rc, out, err = _specs_set(repo, "--allow-open-questions")
    assert rc == 0, out + err

    events = _log_events(repo)
    assert len(events) == 4
    newest = events[-1]
    assert newest["op"] == "transition"
    assert (newest["from"], newest["to"]) == ("reviewed", "approved")
    assert newest["overrides"] == ["allow-open-questions"]
    assert newest["by_human"] is True
    assert "overrides" not in events[0]
    assert (
        meta.read_text(spec.read_text(encoding="utf-8"), record_type="spec").status
        == "approved"
    )


def test_setter_writes_no_overrides_key_without_an_override_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=2)
    _log_spec(repo, open_question=False)

    rc, out, err = _specs_set(repo)
    assert rc == 0, out + err

    newest = _log_events(repo)[-1]
    assert (newest["from"], newest["to"]) == ("reviewed", "approved")
    assert "overrides" not in newest


# --------------------------------------------------------------------------------------------------
# aw specs set --date
# --------------------------------------------------------------------------------------------------


def test_specs_set_date_is_refused_at_schema_2_and_leaves_the_fixture_byte_identical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=2)
    _log_spec(repo, open_question=False)
    before = _tree_bytes(repo)

    rc, out, err = _specs_set(repo, "--date", "2026-11-01")
    assert rc != 0
    combined = out + err
    assert "--date is refused once metadata_schema is 2" in combined
    assert "--message" in combined
    assert _tree_bytes(repo) == before


def test_specs_set_date_still_works_below_schema_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    _legacy_spec(repo, open_question=False)

    rc, out, err = _specs_set(repo, "--date", "2026-11-01")
    assert rc == 0, out + err
    approved = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / "approved"
        / f"20261109-{_ID6}-01-{_ID6}-sample.spec.md"
    )
    text = approved.read_text(encoding="utf-8")
    assert "- 2026-11-01 approved (aw set, --by-human): approved for the test" in text
    assert not (repo / ".aw" / "records" / "meta").exists()


# --------------------------------------------------------------------------------------------------
# legacy-format records keep today's bytes
# --------------------------------------------------------------------------------------------------


def test_legacy_setter_renders_the_override_as_an_actor_suffix_and_writes_no_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    _legacy_spec(repo, open_question=True)

    rc, out, err = _specs_set(repo, "--allow-open-questions")
    assert rc == 0, out + err

    approved = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / "approved"
        / f"20261109-{_ID6}-01-{_ID6}-sample.spec.md"
    )
    text = approved.read_text(encoding="utf-8")
    assert "- Status: approved" in text
    assert (
        " approved (aw set, --by-human, --allow-open-questions): approved for the test"
        in text
    )
    assert "overrides" not in text
    assert not (repo / ".aw" / "records" / "meta").exists()


def test_legacy_setter_without_an_override_has_no_suffix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    _legacy_spec(repo, open_question=False)

    rc, out, err = _specs_set(repo)
    assert rc == 0, out + err

    approved = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / "approved"
        / f"20261109-{_ID6}-01-{_ID6}-sample.spec.md"
    )
    text = approved.read_text(encoding="utf-8")
    assert " approved (aw set, --by-human): approved for the test" in text
    assert "--allow-open-questions" not in text
    assert not (repo / ".aw" / "records" / "meta").exists()


def test_setter_self_commit_includes_the_event_log_of_a_log_format_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path, monkeypatch, schema=2)
    _log_spec(repo, open_question=True)

    rc, out, err = _run_cli(
        [
            "specs",
            "set",
            "approved",
            _ID6,
            "--dir",
            str(repo),
            "--by-human",
            "--allow-open-questions",
            "--message",
            "approved for the test",
            "--yes",
            "--commit",
        ]
    )
    assert rc == 0, out + err

    committed = subprocess.run(
        ["git", "-C", str(repo), "show", "--name-only", "--format=", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    assert sorted(committed) == sorted(
        [f".aw/records/meta/{_ID6}.jsonl", f".aw/records/{_REL}"]
    )
    dirty = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "--", ".aw/records"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert dirty == ""
    assert _log_events(repo)[-1]["overrides"] == ["allow-open-questions"]

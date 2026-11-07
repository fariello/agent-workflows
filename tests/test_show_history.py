"""Behavioral tests for `aw show <ref> --history` and `aw show <ref> --format json` (IPD `1ajqaa`).

Every case builds a temp repository, drives `cli.main` (or the `meta_cli` functions it calls), and
asserts on stdout, exit codes and parsed JSON. No test reads production source (GUIDING_PRINCIPLES
P16).

Log-format fixtures are written DIRECTLY from `artifact_meta.encode_event` lines plus a two-key
front-matter mirror, NOT through `artifact_meta.create`/`append`: a later plan (`2xwb9b`) makes
`append` write the legacy format while a repository is unmigrated, which would silently stop these
fixtures from producing a log.
"""

from __future__ import annotations

import io
import json
import random
import subprocess
from pathlib import Path
from typing import List, Tuple
from unittest.mock import patch

import pytest

from agent_workflows import artifact_meta, cli, meta_cli

pytestmark = pytest.mark.core

PLAN_ID = "hx0001"
LOG_ID = "lg0001"
PLAN_NAME = f"20261106-hxset-01-{PLAN_ID}-legacy-plan.ipd.md"
LOG_NAME = f"20261106-hxset-02-{LOG_ID}-log-plan.ipd.md"


def _run(repo: Path, argv: List[str]) -> Tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdout", out), patch("sys.stderr", err):
        rc = cli.main(["show"] + argv + ["--dir", str(repo)])
    return rc, out.getvalue(), err.getvalue()


def _repo(tmp_path: Path) -> Path:
    repo = (tmp_path / "repo").resolve()
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    return repo


def _write_legacy_plan(repo: Path, extra_line: str = "") -> Path:
    p = repo / ".aw" / "records" / "plans" / "pending" / PLAN_NAME
    p.write_text(
        "# IPD: Legacy plan\n\n"
        f"- Id: {PLAN_ID}\n"
        "- Status: approved\n"
        "- Set: hxset\n"
        "- Order: 1\n\n"
        "## Workflow history\n"
        "- 2026-11-03 approved (aw set): tool-prepended newest line\n"
        "- 2026-11-01 draft (author): author-appended oldest line\n"
        "- 2026-11-02 to-review (author): appended out of date order\n"
        + (extra_line + "\n" if extra_line else "")
        + "\n## Goal\n\nBody.\n",
        encoding="utf-8",
    )
    return p


def _log_events(id6: str = LOG_ID, name: str = LOG_NAME) -> List[dict]:
    path = f"plans/pending/{name}"
    return [
        {
            "v": 1,
            "seq": 1,
            "append": 1,
            "at": "2026-11-06T12:00:00Z",
            "actor": {"tool": "aw"},
            "op": "create",
            "path": path,
            "fields": {
                "id": id6,
                "type": "ipd",
                "status": "draft",
                "set": "hxset",
                "order": 2,
                "title": "Log plan",
            },
        },
        {
            "v": 1,
            "seq": 2,
            "append": 2,
            "at": "2026-11-06T12:01:00Z",
            "actor": {"tool": "aw", "model": "m1"},
            "op": "transition",
            "from": "draft",
            "to": "to-review",
            "message": "authored",
        },
        {
            "v": 1,
            "seq": 3,
            "append": 3,
            "at": "2026-11-06T12:02:00Z",
            "actor": {"tool": "aw"},
            "op": "set",
            "fields": {"blocks_release": "next"},
        },
        {
            "v": 1,
            "seq": 4,
            "append": 4,
            "at": "2026-11-06T12:03:00Z",
            "actor": {"tool": "aw"},
            "op": "review",
            "review_kind": "gate",
            "round": 1,
            "verdict": "APPROVE",
        },
    ]


def _write_log_plan(repo: Path, *, shuffle: bool = False) -> Path:
    records = repo / ".aw" / "records"
    (records / "meta").mkdir(parents=True, exist_ok=True)
    lines = [artifact_meta.encode_event(e) for e in _log_events()]
    if shuffle:
        rnd = random.Random(7)
        while lines == sorted(lines, key=lambda s: json.loads(s)["seq"]):
            rnd.shuffle(lines)
    log = records / "meta" / f"{LOG_ID}.jsonl"
    log.write_text("".join(lines), encoding="utf-8")
    (records / "plans" / "pending" / LOG_NAME).write_text(
        f"---\nid: {LOG_ID}\nstatus: to-review\n---\n# IPD: Log plan\n\nBody.\n",
        encoding="utf-8",
    )
    return log


# ---------------------------------------------------------------------------------------------
# meta_cli functions (V-02: `-k meta_cli`)
# ---------------------------------------------------------------------------------------------


def test_meta_cli_show_history_returns_events_in_seq_order(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write_log_plan(repo, shuffle=True)
    res = meta_cli.show_history(repo, LOG_ID)
    assert res.exit_code == 0
    [rec] = res.data["records"]
    assert [e["seq"] for e in rec["history"]] == [1, 2, 3, 4]
    assert (
        rec["history"][1]["from"] == "draft" and rec["history"][1]["to"] == "to-review"
    )
    assert rec["history"][1]["actor"] == {"tool": "aw", "model": "m1"}


def test_meta_cli_neutralizes_control_characters_in_imported_lines(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    _write_legacy_plan(repo, extra_line="- 2026-11-04 note (author): bell\x07here")
    res = meta_cli.show_history(repo, PLAN_ID)
    assert res.exit_code == 0
    messages = [e["message"] for e in res.data["records"][0]["history"]]
    assert "- 2026-11-04 note (author): bell\ufffdhere" in messages
    assert not any("\x07" in m for m in messages)


def test_meta_cli_invalid_record_exits_2_naming_defect(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    log = _write_log_plan(repo)
    lines = log.read_text(encoding="utf-8").splitlines(keepends=True)
    log.write_text(lines[0] + lines[2], encoding="utf-8")  # seq gap: 1 then 3
    res = meta_cli.show_history(repo, LOG_ID)
    assert res.exit_code == 2
    assert res.diagnostics and res.diagnostics[0].rule == "invalid-record"
    assert "seq-gap" in res.diagnostics[0].detail
    js = meta_cli.show_json(repo, LOG_ID)
    assert js.exit_code == 2 and "seq-gap" in js.data["records"][0]["defect"]


def test_meta_cli_show_json_returns_replayed_state(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write_log_plan(repo)
    res = meta_cli.show_json(repo, LOG_ID, history=True)
    [rec] = res.data["records"]
    assert rec["status"] == "to-review"
    assert rec["set"] == "hxset" and rec["order"] == 2
    assert rec["fields"]["blocks_release"] == "next"
    assert rec["valid"] is True and rec["defect"] is None
    assert len(rec["history"]) == 4


# ---------------------------------------------------------------------------------------------
# E-04 (a) to (g): CLI behavior
# ---------------------------------------------------------------------------------------------


def test_a_legacy_history_lines_in_file_order_without_inferred_transitions(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    _write_legacy_plan(repo)
    rc, out, _ = _run(repo, [PLAN_ID, "--history", "--format", "json"])
    assert rc == 0
    events = json.loads(out)["data"]["records"][0]["history"]
    assert [e["message"] for e in events] == [
        "- 2026-11-03 approved (aw set): tool-prepended newest line",
        "- 2026-11-01 draft (author): author-appended oldest line",
        "- 2026-11-02 to-review (author): appended out of date order",
    ]
    assert all(e["op"] == "legacy" for e in events)
    assert not any("from" in e or "to" in e for e in events)
    rc_h, out_h, _ = _run(repo, [PLAN_ID, "--history"])
    assert rc_h == 0
    assert out_h.index("tool-prepended") < out_h.index("author-appended oldest")


def test_b_log_events_in_seq_order_when_shuffled_on_disk(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    log = _write_log_plan(repo, shuffle=True)
    on_disk = [
        json.loads(s)["seq"] for s in log.read_text(encoding="utf-8").splitlines()
    ]
    assert on_disk != sorted(on_disk)
    rc, out, _ = _run(repo, [LOG_ID, "--history"])
    assert rc == 0
    rows = [ln.split()[0] for ln in out.splitlines() if ln.strip()[:1].isdigit()]
    assert rows == ["1", "2", "3", "4"]
    assert "draft -> to-review" in out


def test_c_review_rounds_are_events_of_the_subject(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write_legacy_plan(repo)
    reviews = repo / ".aw" / "records" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / f"20261106-hxset-01-{PLAN_ID}-legacy-plan.review.md").write_text(
        f"# Review\n\n- Subject-Id: {PLAN_ID}\n- Verdict: APPROVE\n- Reviewer: r1\n\n"
        "## Round 1\n\nFirst.\n\n## Round 2\n\nSecond.\n",
        encoding="utf-8",
    )
    rc, out, _ = _run(repo, [PLAN_ID, "--history", "--format", "json"])
    assert rc == 0
    data = json.loads(out)["data"]["records"]
    assert [r["id6"] for r in data] == [
        PLAN_ID
    ]  # no separate record for the review file
    review_events = [e for e in data[0]["history"] if e["op"] == "review"]
    assert [e["round"] for e in review_events] == [1, 2]
    assert review_events[-1]["verdict"] == "APPROVE"
    assert "verdict" not in review_events[0]


def test_d_format_json_round_trips(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write_log_plan(repo)
    rc, out, _ = _run(repo, [LOG_ID, "--format", "json"])
    assert rc == 0
    doc = json.loads(out)
    [rec] = doc["data"]["records"]
    assert rec["status"] == "to-review"
    assert "fields" in rec and "history" not in rec
    assert json.loads(json.dumps(doc)) == doc
    rc2, out2, _ = _run(repo, [LOG_ID, "--format", "json", "--history"])
    assert rc2 == 0 and len(json.loads(out2)["data"]["records"][0]["history"]) == 4


def test_e_corrupt_log_exits_2_and_names_defect_never_stale(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    log = _write_log_plan(repo)
    rc0, out0, _ = _run(repo, [LOG_ID, "--history"])
    assert rc0 == 0 and "to-review" in out0  # warm cache with valid state
    log.write_text(log.read_text(encoding="utf-8") + "{not json\n", encoding="utf-8")
    rc, out, err = _run(repo, [LOG_ID, "--history"])
    assert rc == 2
    assert "invalid record" in out
    assert "draft -> to-review" not in out
    rc_a, out_a, _ = _run(repo, [LOG_ID, "--history", "--agent"])
    rec = json.loads(out_a.strip().splitlines()[-1])
    assert (
        rc_a == 2
        and rec["exit"] == 2
        and rec["diagnostics"][0]["rule"] == "invalid-record"
    )


def test_f_missing_cache_gives_same_output_as_warm(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write_log_plan(repo)
    _write_legacy_plan(repo)
    _, warm1, _ = _run(repo, [LOG_ID, "--history", "--format", "json"])
    _, warm2, _ = _run(repo, [LOG_ID, "--history", "--format", "json"])
    db = repo / ".aw" / "state" / "index.db"
    assert db.is_file()
    db.unlink()
    _, cold, _ = _run(repo, [LOG_ID, "--history", "--format", "json"])
    assert warm1 == warm2 == cold
    db.write_bytes(b"garbage, not sqlite")
    rc, corrupt, _ = _run(repo, [LOG_ID, "--history", "--format", "json"])
    assert rc == 0 and corrupt == warm1


def test_g_staged_log_edit_appears_on_next_call_without_rebuild(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    log = _write_log_plan(repo)
    _, before, _ = _run(repo, [LOG_ID, "--history", "--agent"])
    assert f"{LOG_ID}-events:4" in before
    nxt = {
        "v": 1,
        "seq": 5,
        "append": 5,
        "at": "2026-11-06T12:04:00Z",
        "actor": {"tool": "aw"},
        "op": "note",
        "message": "added outside artifact_meta",
    }
    log.write_text(
        log.read_text(encoding="utf-8") + artifact_meta.encode_event(nxt),
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", str(repo), "add", str(log)], check=True)
    rc, after, _ = _run(repo, [LOG_ID, "--history"])
    assert rc == 0
    assert "added outside artifact_meta" in after


def test_unknown_selector_keeps_zero_match_refusal(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write_log_plan(repo)
    rc, out, _ = _run(repo, ["zz9999", "--history", "--agent"])
    rec = json.loads(out.strip().splitlines()[-1])
    assert (
        rc == 2 and rec["kind"] == "error" and rec["unresolved_selectors"] == ["zz9999"]
    )


def test_set_selector_returns_every_match(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write_log_plan(repo)
    _write_legacy_plan(repo)
    rc, out, _ = _run(repo, ["hxset", "--history", "--format", "json"])
    assert rc == 0
    assert sorted(r["id6"] for r in json.loads(out)["data"]["records"]) == sorted(
        [LOG_ID, PLAN_ID]
    )


# ---------------------------------------------------------------------------------------------
# Cache freshness regressions found while building these commands (fixed in `artifact_meta`)
# ---------------------------------------------------------------------------------------------


def test_record_still_shown_after_git_mv_between_dispositions(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    src = _write_legacy_plan(repo)
    assert _run(repo, [PLAN_ID, "--history"])[0] == 0  # warm the cache
    dest = repo / ".aw" / "records" / "plans" / "executed" / PLAN_NAME
    dest.parent.mkdir(parents=True)
    src.rename(dest)
    rc, out, _ = _run(repo, [PLAN_ID, "--format", "json"])
    assert rc == 0
    assert (
        json.loads(out)["data"]["records"][0]["path"] == f"plans/executed/{PLAN_NAME}"
    )


def test_record_still_shown_after_its_review_file_changes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write_legacy_plan(repo)
    reviews = repo / ".aw" / "records" / "reviews"
    reviews.mkdir(parents=True)
    rv = reviews / f"20261106-hxset-01-{PLAN_ID}-legacy-plan.review.md"
    rv.write_text(
        f"# Review\n\n- Subject-Id: {PLAN_ID}\n\n## Round 1\n", encoding="utf-8"
    )
    assert _run(repo, [PLAN_ID, "--history"])[0] == 0
    rv.write_text(rv.read_text(encoding="utf-8") + "\n## Round 2\n", encoding="utf-8")
    rc, out, _ = _run(repo, [PLAN_ID, "--history", "--format", "json"])
    assert rc == 0
    rounds = [
        e["round"]
        for e in json.loads(out)["data"]["records"][0]["history"]
        if e["op"] == "review"
    ]
    assert rounds == [1, 2]
    rv.unlink()
    rc2, out2, _ = _run(repo, [PLAN_ID, "--history", "--format", "json"])
    assert rc2 == 0
    assert not [
        e
        for e in json.loads(out2)["data"]["records"][0]["history"]
        if e["op"] == "review"
    ]


def test_mirror_file_does_not_replace_the_log_state(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write_log_plan(repo)
    mirror = repo / ".aw" / "records" / "plans" / "pending" / LOG_NAME
    mirror.write_text(
        mirror.read_text(encoding="utf-8") + "\nedited body\n", encoding="utf-8"
    )
    rc, out, _ = _run(repo, [LOG_ID, "--format", "json", "--history"])
    assert rc == 0
    [rec] = json.loads(out)["data"]["records"]
    assert rec["status"] == "to-review" and len(rec["history"]) == 4

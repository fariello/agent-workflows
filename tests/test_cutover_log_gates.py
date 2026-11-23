"""Behavioral tests for the dormant post-cutover gates on log-format records (IPD `6jd6mh`).

Spec `4sd62s` 4.3 ("Gate rules change as follows"), 5.2 step 4a, AC-16 case 2 and OQ-30. Each
log-format fixture is a real `git init` repository under `tmp_path` whose plan has a
`.aw/records/meta/<id6>.jsonl` log and whose `project.json` carries `metadata_schema: 2`; each
legacy-format fixture has no log, which is the state of every repository before the cutover. The
tests drive the real `check_engine` rules and the real hooks and assert on their findings.

Node names carry `check_engine`, `executed` or `terminal` so the plan's `-k` selections pick them.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from agent_workflows import artifact_meta as meta, check_engine
from agent_workflows.hooks import executed_transition_gate, meta_log_append_gate

pytestmark = pytest.mark.core

_AT = "2026-11-09T12:00:00Z"
_PENDING = "plans/pending/20261109-demo-01-{id6}-sample.ipd.md"
_EXECUTED = "plans/executed/20261109-demo-01-{id6}-sample.ipd.md"
_ARCHIVED = "plans/executed/2026/w45/20261109-demo-01-{id6}-sample.ipd.md"


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
    assert proc.returncode == 0, f"git {' '.join(args)} failed: {proc.stderr}"
    return proc


def _init_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, schema: Optional[int] = 2
) -> Path:
    monkeypatch.setenv("AW_HOME", str(tmp_path / "aw_home"))
    repo = tmp_path / "repo"
    (repo / ".aw" / "records" / "meta").mkdir(parents=True)
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    (repo / ".aw" / "records" / "plans" / "executed").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test Agent")
    _git(repo, "config", "user.email", "test-agent@example.com")
    if schema is not None:
        cfg = repo / ".aw" / "config"
        cfg.mkdir(parents=True)
        (cfg / "project.json").write_text(
            json.dumps({"metadata_schema": schema}) + "\n", encoding="utf-8"
        )
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


class _Log:
    """Builds a plan's event log one append at a time with consecutive seq and shared envelopes."""

    def __init__(self, id6: str) -> None:
        self.id6 = id6
        self.events: List[Dict[str, Any]] = []

    @property
    def seq(self) -> int:
        return self.events[-1]["seq"] if self.events else 0

    def append(self, *payloads: Dict[str, Any]) -> "_Log":
        first = self.seq + 1
        for i, payload in enumerate(payloads):
            ev = {
                "v": 1,
                "seq": first + i,
                "append": first,
                "at": _AT,
                "actor": {"tool": "aw test"},
            }
            ev.update(payload)
            self.events.append(ev)
        return self

    def text(self) -> str:
        return "".join(meta.encode_event(e) for e in self.events)


def _approved_log(id6: str) -> _Log:
    log = _Log(id6)
    log.append(
        {
            "op": "create",
            "path": _PENDING.format(id6=id6),
            "fields": {
                "id": id6,
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
        log.append({"op": "transition", "from": frm, "to": to})
    return log


def _finalize_payloads(id6: str) -> List[Dict[str, Any]]:
    return [
        {
            "op": "transition",
            "from": "approved",
            "to": "executed",
            "path": _EXECUTED.format(id6=id6),
        },
        {
            "op": "set",
            "fields": {
                "scope_result": "within",
                "out_of_scope_paths": [],
                "widened_paths": [],
            },
        },
    ]


def _rollup_payloads(id6: str) -> List[Dict[str, Any]]:
    return [
        {
            "op": "transition",
            "from": "approved",
            "to": "executed",
            "path": _EXECUTED.format(id6=id6),
        }
    ]


def _plan_text(id6: str, status: str) -> str:
    return meta.render_in_file_mirror(id6, "ipd", status) + "# IPD: sample\n\nbody\n"


def _write(repo: Path, rel: str, text: str) -> str:
    path = repo / ".aw" / "records" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return f".aw/records/{rel}"


def _write_log(repo: Path, log: _Log) -> str:
    return _write(repo, f"meta/{log.id6}.jsonl", log.text())


def _commit(repo: Path, *paths: str, msg: str = "seed") -> None:
    _git(repo, "add", "--", *paths)
    _git(repo, "commit", "-q", "-m", msg)


def _seed(repo: Path, log: _Log, rel_md: str, status: str) -> str:
    md = _write(repo, rel_md, _plan_text(log.id6, status))
    _commit(repo, _write_log(repo, log), md)
    return md


def _seed_executed(repo: Path, id6: str) -> _Log:
    log = _approved_log(id6).append(*_finalize_payloads(id6))
    _seed(repo, log, _EXECUTED.format(id6=id6), "executed")
    return log


def _move_to_executed(repo: Path, id6: str) -> str:
    _git(
        repo,
        "mv",
        f".aw/records/{_PENDING.format(id6=id6)}",
        f".aw/records/{_EXECUTED.format(id6=id6)}",
    )
    return _write(repo, _EXECUTED.format(id6=id6), _plan_text(id6, "executed"))


def _rules(drift: List[Any]) -> List[str]:
    return [d.rule for d in drift]


def _legacy_plan_text(id6: str, status: str) -> str:
    return (
        "# IPD: legacy sample\n\n"
        f"- Date: 2026-11-09\n- Status: {status}\n- Set: demo\n- Order: 1\n- Id: {id6}\n\n"
        "## Workflow history\n"
        f"- 2026-11-09 {status} (aw set): status set to {status}\n"
    )


# --------------------------------------------------------------------------------------
# E-02 / V-02: the two check_engine rules
# --------------------------------------------------------------------------------------


def test_check_engine_mirror_differs_from_log_is_reported(tmp_path, monkeypatch):
    """A staged mirror flipped to `executed` while the log still replays `approved` is drift."""
    repo = _init_repo(tmp_path, monkeypatch)
    log = _approved_log("ab12cd")
    md = _seed(repo, log, _PENDING.format(id6="ab12cd"), "approved")
    _write(repo, _PENDING.format(id6="ab12cd"), _plan_text("ab12cd", "executed"))
    _git(repo, "add", "--", md)

    drift = check_engine.check_staged_meta_mirror_drift(repo)
    assert _rules(drift) == ["check.meta-mirror-drift"]
    assert drift[0].location == md
    assert "'executed'" in drift[0].detail and "'approved'" in drift[0].detail
    assert drift[0].severity == "error"
    assert "check.meta-mirror-drift" in _rules(
        check_engine.check_commit_invariants(repo)
    )


def test_check_engine_mirror_drift_from_log_only_change_is_reported(
    tmp_path, monkeypatch
):
    """A tooled-looking log append that the mirror was not updated for is also drift."""
    repo = _init_repo(tmp_path, monkeypatch)
    log = _approved_log("ab12ce")
    md = _seed(repo, log, _PENDING.format(id6="ab12ce"), "reviewed")
    # HEAD already disagreed; the rule only fires once this commit touches the record.
    assert check_engine.check_staged_meta_mirror_drift(repo) == []
    log.append({"op": "note", "message": "progress"})
    _git(repo, "add", "--", _write_log(repo, log))

    drift = check_engine.check_staged_meta_mirror_drift(repo)
    assert _rules(drift) == ["check.meta-mirror-drift"]
    assert drift[0].location == md


def test_check_engine_mirror_matching_log_is_clean(tmp_path, monkeypatch):
    """A tooled append whose mirror matches the replayed state yields no finding."""
    repo = _init_repo(tmp_path, monkeypatch)
    log = _approved_log("ab12cf")
    _seed(repo, log, _PENDING.format(id6="ab12cf"), "approved")
    log.append({"op": "note", "message": "progress"})
    _git(repo, "add", "--", _write_log(repo, log))

    assert check_engine.check_staged_meta_mirror_drift(repo) == []
    assert check_engine.check_staged_meta_log_append(repo) == []


def test_check_engine_append_violation_is_reported(tmp_path, monkeypatch):
    """A staged log that rewrites a HEAD event is reported under `check.meta-log-append`."""
    repo = _init_repo(tmp_path, monkeypatch)
    log = _approved_log("ab12cg")
    _seed(repo, log, _PENDING.format(id6="ab12cg"), "approved")
    log.events[0]["fields"]["order"] = 9
    rel_log = _write_log(repo, log)
    _git(repo, "add", "--", rel_log)

    drift = check_engine.check_staged_meta_log_append(repo)
    assert _rules(drift) == ["check.meta-log-append"]
    assert drift[0].location == rel_log
    assert "rewrote" in drift[0].detail.lower()
    assert drift[0].severity == "error"
    assert "check.meta-log-append" in _rules(check_engine.check_commit_invariants(repo))


def test_check_engine_terminal_append_violation_is_reported(tmp_path, monkeypatch):
    """The OQ-30 terminal rules reach `aw check` through the same predicate as the hook."""
    repo = _init_repo(tmp_path, monkeypatch)
    log = _seed_executed(repo, "ab12ch")
    log.append({"op": "set", "fields": {"blocks_release": "next"}})
    _git(repo, "add", "--", _write_log(repo, log))

    drift = check_engine.check_staged_meta_log_append(repo)
    assert _rules(drift) == ["check.meta-log-append"]
    assert "blocks_release" in drift[0].detail
    rc, msgs = meta_log_append_gate.check(repo)
    assert rc == 1 and [m.split(": ", 1)[1] for m in msgs] == [drift[0].detail]


def test_check_engine_legacy_status_change_is_unchanged(tmp_path, monkeypatch):
    """Legacy format: neither new rule fires, and `check.status-untooled` still does."""
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    rel = _write(
        repo, _PENDING.format(id6="ab12ci"), _legacy_plan_text("ab12ci", "reviewed")
    )
    _commit(repo, rel)
    text = (
        (repo / rel)
        .read_text(encoding="utf-8")
        .replace("- Status: reviewed", "- Status: approved")
    )
    (repo / rel).write_text(text, encoding="utf-8")
    _git(repo, "add", "--", rel)

    assert check_engine.check_staged_meta_mirror_drift(repo) == []
    assert check_engine.check_staged_meta_log_append(repo) == []
    rules = _rules(check_engine.check_commit_invariants(repo))
    assert "check.status-untooled" in rules
    assert "check.meta-mirror-drift" not in rules
    assert "check.meta-log-append" not in rules


def test_check_engine_rules_are_registered_errors():
    """Both rule ids are registered, so their severity is a decision and not the default."""
    for rule in ("check.meta-mirror-drift", "check.meta-log-append"):
        assert check_engine.RULE_REGISTRY[rule].severity == "error"
        assert check_engine.RULE_REGISTRY[rule].invariant == "I-03"


# --------------------------------------------------------------------------------------
# E-03 / V-03: executed_transition_gate log-format branch
# --------------------------------------------------------------------------------------


def test_executed_raw_mirror_flip_on_log_format_is_refused(tmp_path, monkeypatch):
    """`git mv` into executed/ plus a mirror flip, with no log append, is a raw transition."""
    repo = _init_repo(tmp_path, monkeypatch)
    _seed(repo, _approved_log("cd12ab"), _PENDING.format(id6="cd12ab"), "approved")
    md = _move_to_executed(repo, "cd12ab")
    _git(repo, "add", "--", md)

    rc, msgs = executed_transition_gate.check(repo)
    assert rc == 1 and len(msgs) == 1
    assert msgs[0].startswith(f"{md} (cd12ab): raw plan->executed transition")
    assert "log-format plan" in msgs[0]
    assert "appends no transition to executed" in msgs[0]


def test_executed_bare_transition_append_on_log_format_is_refused(
    tmp_path, monkeypatch
):
    """A log-only `transition` to executed with neither scope fields nor `path` is refused."""
    repo = _init_repo(tmp_path, monkeypatch)
    log = _approved_log("cd12ac")
    _seed(repo, log, _PENDING.format(id6="cd12ac"), "approved")
    log.append({"op": "transition", "from": "approved", "to": "executed"})
    rel_log = _write_log(repo, log)
    _git(repo, "add", "--", rel_log)

    rc, msgs = executed_transition_gate.check(repo)
    assert rc == 1 and len(msgs) == 1
    assert msgs[0].startswith(f"{rel_log} (cd12ac): raw plan->executed transition")
    assert "neither the finalize scope fields nor a rollup-retirement `path`" in msgs[0]


def test_executed_finalize_append_on_log_format_is_accepted(tmp_path, monkeypatch):
    """A finalize append (transition + scope fields) is accepted with no journal present."""
    repo = _init_repo(tmp_path, monkeypatch)
    log = _approved_log("cd12ad")
    _seed(repo, log, _PENDING.format(id6="cd12ad"), "approved")
    log.append(*_finalize_payloads("cd12ad"))
    md = _move_to_executed(repo, "cd12ad")
    _git(repo, "add", "--", md, _write_log(repo, log))

    assert executed_transition_gate.check(repo) == (0, [])


def test_executed_rollup_retirement_append_on_log_format_is_accepted(
    tmp_path, monkeypatch
):
    """An orchestrator rollup-retirement append (transition with `path`, no scope) is accepted."""
    repo = _init_repo(tmp_path, monkeypatch)
    log = _approved_log("cd12ae")
    _seed(repo, log, _PENDING.format(id6="cd12ae"), "approved")
    log.append(*_rollup_payloads("cd12ae"))
    md = _move_to_executed(repo, "cd12ae")
    _git(repo, "add", "--", md, _write_log(repo, log))

    assert executed_transition_gate.check(repo) == (0, [])


def test_executed_id_replacement_on_log_format_is_refused(tmp_path, monkeypatch):
    """Replacing an executed file's `id` with another log-format plan's is refused."""
    repo = _init_repo(tmp_path, monkeypatch)
    _seed_executed(repo, "cd12af")
    _seed(repo, _approved_log("cd12ag"), _PENDING.format(id6="cd12ag"), "approved")
    md = _write(repo, _EXECUTED.format(id6="cd12af"), _plan_text("cd12ag", "executed"))
    _git(repo, "add", "--", md)

    rc, msgs = executed_transition_gate.check(repo)
    assert rc == 1 and len(msgs) == 1
    assert msgs[0].startswith(f"{md} (cd12ag): raw plan->executed transition")


def test_executed_edit_of_already_executed_log_format_plan_passes(
    tmp_path, monkeypatch
):
    """An ordinary note on an already-executed log-format plan is not a transition."""
    repo = _init_repo(tmp_path, monkeypatch)
    log = _seed_executed(repo, "cd12ah")
    log.append({"op": "note", "message": "follow-up recorded"})
    _git(repo, "add", "--", _write_log(repo, log))

    assert executed_transition_gate.check(repo) == (0, [])


def test_executed_legacy_raw_transition_keeps_todays_rule(tmp_path, monkeypatch):
    """Legacy format: a hand move into executed/ gets today's journal-based refusal, unchanged."""
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    pend = _write(
        repo, _PENDING.format(id6="cd12ai"), _legacy_plan_text("cd12ai", "approved")
    )
    _commit(repo, pend)
    dest = f".aw/records/{_EXECUTED.format(id6='cd12ai')}"
    _git(repo, "mv", pend, dest)
    (repo / dest).write_text(_legacy_plan_text("cd12ai", "executed"), encoding="utf-8")
    _git(repo, "add", "--", dest)

    rc, msgs = executed_transition_gate.check(repo)
    assert rc == 1
    assert msgs == [
        f"{dest} (cd12ai): raw plan->executed transition (moved into executed/) with NO matching "
        "finalize evidence in .aw/state/. Do not hand-edit/`git mv` a plan to executed; run "
        "`aw ipd finalize cd12ai --actor <agent/model> --message <summary> --apply` "
        "(which runs the receipt/scope/attribution gates and makes the lifecycle commit)."
    ]


# --------------------------------------------------------------------------------------
# E-04 / V-04: OQ-30 terminal-log rules of meta_log_append_gate
# --------------------------------------------------------------------------------------


def _terminal_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, id6: str, *payloads: Dict[str, Any]
):
    repo = _init_repo(tmp_path, monkeypatch)
    log = _seed_executed(repo, id6)
    log.append(*payloads)
    _git(repo, "add", "--", _write_log(repo, log))
    return meta_log_append_gate.check(repo)


def test_terminal_accepts_note(tmp_path, monkeypatch):
    assert _terminal_case(
        tmp_path, monkeypatch, "ef12aa", {"op": "note", "message": "post-run note"}
    ) == (0, [])


def test_terminal_accepts_review(tmp_path, monkeypatch):
    assert _terminal_case(
        tmp_path,
        monkeypatch,
        "ef12ab",
        {
            "op": "review",
            "round": 1,
            "review_kind": "refinement",
            "verdict": meta.REFINEMENT_VERDICTS[0],
        },
    ) == (0, [])


@pytest.mark.parametrize("verb", sorted(meta.RENAME_VERBS))
def test_terminal_accepts_rename_verb(tmp_path, monkeypatch, verb):
    assert _terminal_case(
        tmp_path,
        monkeypatch,
        "ef12ac",
        {"op": "rename", "verb": verb, "path": _ARCHIVED.format(id6="ef12ac")},
    ) == (0, [])


def test_terminal_accepts_rename_with_set_and_order(tmp_path, monkeypatch):
    assert _terminal_case(
        tmp_path,
        monkeypatch,
        "ef12ad",
        {
            "op": "rename",
            "verb": "group",
            "path": "plans/executed/20261109-other-03-ef12ad-sample.ipd.md",
        },
        {"op": "set", "fields": {"set": "other", "order": 3}},
    ) == (0, [])


def test_terminal_accepts_set_short_description(tmp_path, monkeypatch):
    assert _terminal_case(
        tmp_path,
        monkeypatch,
        "ef12ae",
        {"op": "set", "fields": {"short_description": "what it did"}},
    ) == (0, [])


def test_terminal_accepts_unset_short_description(tmp_path, monkeypatch):
    assert _terminal_case(
        tmp_path,
        monkeypatch,
        "ef12af",
        {"op": "unset", "fields": ["short_description"]},
    ) == (0, [])


def test_terminal_refuses_non_append_edit(tmp_path, monkeypatch):
    """Rewriting an existing event on a terminal log is refused (append-only rule)."""
    repo = _init_repo(tmp_path, monkeypatch)
    log = _seed_executed(repo, "ef12ag")
    log.events[-1]["fields"]["scope_result"] = "exceeded"
    rel_log = _write_log(repo, log)
    _git(repo, "add", "--", rel_log)

    rc, msgs = meta_log_append_gate.check(repo)
    assert rc == 1 and len(msgs) == 1
    assert msgs[0].startswith(f"{rel_log}: ") and "rewrote" in msgs[0].lower()


def test_terminal_refuses_set_readiness(tmp_path, monkeypatch):
    rc, msgs = _terminal_case(
        tmp_path, monkeypatch, "ef12ah", {"op": "set", "fields": {"readiness": "go"}}
    )
    assert rc == 1 and len(msgs) == 1 and "readiness" in msgs[0]


@pytest.mark.parametrize(
    "fields",
    [
        {"blocks_release": "next"},
        {"priority": "low"},
        {"order": 4},
    ],
    ids=["blocks_release", "priority", "order-without-rename"],
)
def test_terminal_refuses_frozen_field_set(tmp_path, monkeypatch, fields):
    """Fields the loader would accept are still frozen on a terminal log (OQ-30)."""
    rc, msgs = _terminal_case(
        tmp_path, monkeypatch, "ef12ai", {"op": "set", "fields": fields}
    )
    assert rc == 1 and len(msgs) == 1
    assert next(iter(fields)) in msgs[0] and "frozen field" in msgs[0]


def test_terminal_refuses_coverage_event(tmp_path, monkeypatch):
    rc, msgs = _terminal_case(
        tmp_path,
        monkeypatch,
        "ef12aj",
        {"op": "coverage", "coverage": "covered", "coverage_fingerprint": "abc"},
    )
    assert rc == 1 and "`coverage` event" in msgs[0]


def test_terminal_refuses_review_carrying_readiness(tmp_path, monkeypatch):
    rc, msgs = _terminal_case(
        tmp_path,
        monkeypatch,
        "ef12ak",
        {
            "op": "review",
            "round": 2,
            "review_kind": "gate",
            "verdict": meta.GATE_VERDICTS[0],
            "readiness": "go",
        },
    )
    assert rc == 1 and "readiness" in msgs[0]


def test_terminal_refuses_scope_result_set(tmp_path, monkeypatch):
    rc, msgs = _terminal_case(
        tmp_path,
        monkeypatch,
        "ef12al",
        {"op": "set", "fields": {"scope_result": "within"}},
    )
    assert rc == 1 and "scope_result" in msgs[0]


def test_terminal_reopen_with_override_is_accepted(tmp_path, monkeypatch):
    """The recorded `allow-terminal-reopen` escape hatch is not frozen by these rules."""
    assert _terminal_case(
        tmp_path,
        monkeypatch,
        "ef12am",
        {
            "op": "transition",
            "from": "executed",
            "to": "to-review",
            "overrides": ["allow-terminal-reopen"],
        },
    ) == (0, [])


def test_terminal_rules_skip_non_terminal_log(tmp_path, monkeypatch):
    """A non-terminal log keeps today's rules: a `set` of `priority` is accepted."""
    repo = _init_repo(tmp_path, monkeypatch)
    log = _approved_log("ef12an")
    _seed(repo, log, _PENDING.format(id6="ef12an"), "approved")
    log.append({"op": "set", "fields": {"priority": "low"}})
    _git(repo, "add", "--", _write_log(repo, log))

    assert meta_log_append_gate.check(repo) == (0, [])


def test_terminal_rules_dormant_on_legacy_format(tmp_path, monkeypatch):
    """Legacy format: an edit to an executed plan stages no log, so the hook is a no-op."""
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    rel = _write(
        repo, _EXECUTED.format(id6="ef12ao"), _legacy_plan_text("ef12ao", "executed")
    )
    _commit(repo, rel)
    (repo / rel).write_text(
        _legacy_plan_text("ef12ao", "executed") + "- 2026-11-10 note: x\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", rel)

    assert meta_log_append_gate.check(repo) == (0, [])
    assert check_engine.check_staged_meta_log_append(repo) == []

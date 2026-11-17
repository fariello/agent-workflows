"""Tests for OQ-03 and D-6 repository-root path validation on scope fields.

Covers spec 4sd62s AC-15, AC-24, and AC-34 (IPD 9qhtrc / E-03, V-03):
1. End-to-end append/read storage of repository-relative code paths in
   out_of_scope_paths and widened_paths, plus scope_exceptions projection.
2. Symlink root separation between records_root and repo_root.
3. Input-safety, shape, string-safety, and leak-sanitizer refusals.
4. Non-git tmp_path .aw/records and .agents/records repo_root fallback.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
from typing import Any, Dict, List

import pytest

from agent_workflows import artifact_meta as meta
from agent_workflows import ipd_lifecycle as LC
from tests import support


pytestmark = pytest.mark.core


def _base_event(
    op: str,
    *,
    seq: int = 1,
    append: int = 1,
    **extra: Any,
) -> Dict[str, Any]:
    ev: Dict[str, Any] = {
        "v": 1,
        "seq": seq,
        "append": append,
        "at": "2026-11-09T12:00:00Z",
        "actor": {"tool": "test_writers_scope_fields"},
        "op": op,
    }
    ev.update(extra)
    return ev


def _setup_repo_layout(
    tmp_path: Path, *, records_parent: str = ".aw"
) -> tuple[Path, Path, Path]:
    repo_root = tmp_path / "repo"
    records_root = repo_root / records_parent / "records"
    state_root = repo_root / records_parent / "state"
    (repo_root / "agent_workflows").mkdir(parents=True, exist_ok=True)
    (repo_root / "tests").mkdir(parents=True, exist_ok=True)
    (records_root / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (records_root / "plans" / "executed").mkdir(parents=True, exist_ok=True)
    state_root.mkdir(parents=True, exist_ok=True)
    return repo_root, records_root, state_root


def test_append_read_and_scope_exceptions_store_repo_relative_paths(
    tmp_path: Path,
) -> None:
    """(1) append(create) + append(transition->executed + set scope fields) projects scope_exceptions."""
    repo_root, records_root, state_root = _setup_repo_layout(tmp_path)
    ctx = meta.legacy_context(repo_root)

    res_create = meta.append(
        "scp001",
        [
            {
                "op": "create",
                "path": "plans/pending/scp001.ipd.md",
                "fields": {
                    "id": "scp001",
                    "type": "ipd",
                    "status": "approved",
                    "set": "metastore",
                    "order": 1,
                },
            }
        ],
        project_context=ctx,
    )
    assert res_create["committed"] is True

    # Materialize mirror file so append's mirror update step exercises the real path.
    pending_file = records_root / "plans" / "pending" / "scp001.ipd.md"
    pending_file.write_text(
        "---\nid: scp001\nstatus: approved\n---\n# Plan\n", encoding="utf-8"
    )

    res_fin = meta.append(
        "scp001",
        [
            {
                "op": "transition",
                "from": "approved",
                "to": "executed",
                "path": "plans/executed/scp001.ipd.md",
            },
            {
                "op": "set",
                "fields": {
                    "scope_result": "exceeded",
                    "out_of_scope_paths": [
                        {
                            "path": "agent_workflows/x.py",
                            "reason": "updated helper\nwith multi-line note",
                        }
                    ],
                    "widened_paths": [
                        {
                            "path": "tests/test_x.py",
                            "reason": "added regression test",
                        }
                    ],
                },
            },
        ],
        expect_seq=1,
        project_context=ctx,
    )
    assert res_fin["committed"] is True
    assert res_fin["status"] == "executed"

    state = meta.read("scp001", project_context=ctx)
    assert state.status == "executed"
    assert state.fields["scope_result"] == "exceeded"
    assert state.fields["out_of_scope_paths"] == [
        {
            "path": "agent_workflows/x.py",
            "reason": "updated helper\nwith multi-line note",
        }
    ]
    assert state.fields["widened_paths"] == [
        {
            "path": "tests/test_x.py",
            "reason": "added regression test",
        }
    ]

    conn = meta.open_cache(records_root, state_root)
    try:
        rows = conn.execute(
            "SELECT ordinal, path, reason, exception_kind, source "
            "FROM scope_exceptions WHERE id6 = ? ORDER BY ordinal",
            ("scp001",),
        ).fetchall()
    finally:
        conn.close()

    assert rows == [
        (
            1,
            "agent_workflows/x.py",
            "updated helper\nwith multi-line note",
            "out-of-scope",
            "finalize",
        ),
        (2, "tests/test_x.py", "added regression test", "widened", "finalize"),
    ]


def test_symlink_root_separation_between_records_root_and_repo_root(
    tmp_path: Path,
) -> None:
    """(2) Symlink proof separating records_root containment from repo_root containment."""
    repo_root, records_root, _ = _setup_repo_layout(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()

    (records_root / "code_link").symlink_to(repo_root / "agent_workflows")
    (repo_root / "escape_link").symlink_to(outside)

    # code_link points inside repo_root but outside records_root:
    # refused in ev["path"] and fields["path"], accepted in scope path fields.
    ev_bad_rec = _base_event("create", path="code_link/x.py")
    with pytest.raises(ValueError, match="must resolve inside records root"):
        meta.validate_new_events(
            "ipd", [ev_bad_rec], records_root=records_root, repo_root=repo_root
        )

    ev_bad_field_path = _base_event("set", fields={"path": "code_link/x.py"})
    with pytest.raises(ValueError, match="must resolve inside records root"):
        meta.validate_new_events(
            "ipd", [ev_bad_field_path], records_root=records_root, repo_root=repo_root
        )

    for field_name in ("out_of_scope_paths", "widened_paths"):
        ev_ok = _base_event(
            "set",
            fields={
                field_name: [{"path": "code_link/x.py", "reason": "inside repo root"}],
            },
        )
        meta.validate_new_events(
            "ipd", [ev_ok], records_root=records_root, repo_root=repo_root
        )

        # escape_link points outside repo_root: refused in both scope path fields.
        ev_escape = _base_event(
            "set",
            fields={
                field_name: [{"path": "escape_link/secret.py", "reason": "escape"}],
            },
        )
        with pytest.raises(ValueError, match="must resolve inside repository root"):
            meta.validate_new_events(
                "ipd", [ev_escape], records_root=records_root, repo_root=repo_root
            )


@pytest.mark.parametrize("field_name", ["out_of_scope_paths", "widened_paths"])
@pytest.mark.parametrize(
    "bad_value",
    [
        pytest.param(["../x"], id="dotdot"),
        pytest.param(["/abs/x.py"], id="abs-path"),
        pytest.param([""], id="empty-str"),
        pytest.param(["."], id="dot-str"),
        pytest.param(
            ["agent_workflows/x.py\n- Status: approved"], id="embedded-newline"
        ),
        pytest.param(
            ["agent_workflows/" + "ses_" + "0" * 20 + ".py"], id="session-token-path"
        ),
        pytest.param(
            [{"path": "agent_workflows/x.py", "reason": "see " + "ses_" + "0" * 20}],
            id="session-token-reason",
        ),
        pytest.param({"path": "../x"}, id="non-list"),
        pytest.param([123], id="non-str-dict-item"),
        pytest.param([{"reason": "missing path"}], id="dict-missing-path"),
    ],
)
def test_scope_field_input_safety_refusals(
    tmp_path: Path, field_name: str, bad_value: Any
) -> None:
    """(3) Input-safety, shape, newline, and leak-sanitizer refusals on scope fields."""
    repo_root, records_root, _ = _setup_repo_layout(tmp_path)
    ev = _base_event("set", fields={field_name: bad_value})
    with pytest.raises(ValueError):
        meta.validate_new_events(
            "ipd", [ev], records_root=records_root, repo_root=repo_root
        )


def test_ev_path_and_fields_path_input_safety_refusals(tmp_path: Path) -> None:
    """(3b) ev['path'] and fields['path'] enforce non-empty, non-'.', newline, and leak refusals."""
    repo_root, records_root, _ = _setup_repo_layout(tmp_path)
    session_path = "plans/pending/" + "ses_" + "0" * 20 + ".ipd.md"

    for bad_path in (
        "",
        ".",
        "plans/pending/a.ipd.md\n- Status: approved",
        session_path,
    ):
        ev_env = _base_event("create", path=bad_path)
        with pytest.raises(ValueError):
            meta.validate_new_events(
                "ipd", [ev_env], records_root=records_root, repo_root=repo_root
            )
        ev_fld = _base_event("set", fields={"path": bad_path})
        with pytest.raises(ValueError):
            meta.validate_new_events(
                "ipd", [ev_fld], records_root=records_root, repo_root=repo_root
            )


def test_reason_newlines_allowed_and_legacy_writer_threads_repo_root(
    tmp_path: Path,
) -> None:
    """(3c) Raw newlines in reason pass validation and legacy writers thread repo_root."""
    repo_root, records_root, _ = _setup_repo_layout(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo_root / "escape_link").symlink_to(outside)

    plan_path = records_root / "plans" / "pending" / "leg001.ipd.md"
    plan_path.write_text(
        "# IPD: Legacy\n\n- Id: leg001\n- Status: approved\n", encoding="utf-8"
    )

    # Raw newlines in reason pass validate_new_events when path resolves inside repo_root.
    ev_newline_reason = _base_event(
        "set",
        fields={
            "out_of_scope_paths": [
                {"path": "agent_workflows/x.py", "reason": "line1\nline2"}
            ],
            "widened_paths": [{"path": "tests/test_x.py", "reason": "lineA\nlineB"}],
        },
    )
    meta.validate_new_events(
        "ipd", [ev_newline_reason], records_root=records_root, repo_root=repo_root
    )

    render_spec = meta.LegacyRender(
        tag="executed",
        day="2026-11-09",
        actor_label="aw ipd finalize",
        status="executed",
    )

    # Refused when escape_link points outside repo_root via render_legacy_text,
    # write_legacy, and append_legacy (proving repo_root is threaded before rendering).
    bad_events = [
        {"op": "transition", "from": "approved", "to": "executed"},
        {"op": "unset", "fields": ["approval"]},
        {
            "op": "set",
            "fields": {
                "scope_result": "exceeded",
                "out_of_scope_paths": [
                    {"path": "escape_link/secret.py", "reason": "bad"}
                ],
            },
        },
    ]
    with pytest.raises(ValueError, match="must resolve inside repository root"):
        meta.render_legacy_text(
            plan_path.read_text(encoding="utf-8"),
            bad_events,
            record_type="ipd",
            render=render_spec,
            repo_root=repo_root,
            from_status="approved",
        )

    target = meta.LegacyTarget(plan_path, "plans", "leg001")
    with pytest.raises(ValueError, match="must resolve inside repository root"):
        meta.write_legacy(
            target,
            bad_events,
            render=render_spec,
            repo_root=repo_root,
            from_status="approved",
            dry_run=True,
        )

    with pytest.raises(ValueError, match="must resolve inside repository root"):
        meta.append_legacy(
            target,
            bad_events,
            render=render_spec,
            repo_root=repo_root,
            from_status="approved",
            dry_run=True,
        )


@pytest.mark.parametrize("records_parent", [".aw", ".agents"])
def test_nongit_layout_resolves_repo_root_without_collapse_or_climb(
    tmp_path: Path, records_parent: str
) -> None:
    """(4) Non-git .aw/records and .agents/records with repo_root=None resolve to repo, not records_root or outer."""
    outer = tmp_path / "outer_checkout"
    (outer / ".git").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()

    repo = outer / "repo"
    records_root = repo / records_parent / "records"
    records_root.mkdir(parents=True)
    (repo / "agent_workflows").mkdir()
    (repo / "outer_link").symlink_to(outer)
    (repo / "outside_link").symlink_to(outside)

    # Succeeds for repo-relative path outside records_root (did not collapse onto records_root).
    ev_ok = _base_event(
        "set",
        fields={
            "out_of_scope_paths": [{"path": "agent_workflows/x.py", "reason": "ok"}],
            "widened_paths": ["agent_workflows/y.py"],
        },
    )
    meta.validate_new_events("ipd", [ev_ok], records_root=records_root, repo_root=None)

    # Refuses symlink into outer_checkout (did not climb into outer .git checkout).
    ev_outer = _base_event(
        "set",
        fields={
            "out_of_scope_paths": [{"path": "outer_link/sibling.py", "reason": "climb"}]
        },
    )
    with pytest.raises(ValueError, match="must resolve inside repository root"):
        meta.validate_new_events(
            "ipd", [ev_outer], records_root=records_root, repo_root=None
        )

    # Refuses symlink outside outer_checkout as well.
    ev_outside = _base_event(
        "set",
        fields={"widened_paths": ["outside_link/secret.py"]},
    )
    with pytest.raises(ValueError, match="must resolve inside repository root"):
        meta.validate_new_events(
            "ipd", [ev_outside], records_root=records_root, repo_root=None
        )


# --------------------------------------------------------------------------------------
# IPD 1dvb08 (E-03 / V-03): Finalize scope fields in phase B and log replay
# --------------------------------------------------------------------------------------


def _init_git_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@example.invalid"],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo_root, check=True)
    (repo_root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(repo_root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo_root, check=True)


def _completed_child_plan_text(
    *,
    plan_id: str,
    set_name: str = "demo",
    order: int = 1,
    status: str = "approved",
    scope_paths: str = "agent_workflows/demo.py",
) -> str:
    txt = support.ready_plan_text(
        plan_id=plan_id,
        kind="child",
        set_name=set_name,
        order=order,
        status=status,
        scope_paths=scope_paths,
    )
    txt = txt.replace("- [ ] E-01 ", "- [x] E-01 ", 1).replace(
        "  - Execution state: pending", "  - Execution state: performed", 1
    )
    txt = (
        txt.replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
        .replace(
            "  - Observed evidence:\n", "  - Observed evidence: done, verified.\n", 1
        )
        .replace("  - Result: pending", "  - Result: pass", 1)
    )
    return txt


def _read_scope_exceptions(
    records_root: Path, state_root: Path, id6: str
) -> List[tuple[Any, ...]]:
    conn = meta.open_cache(records_root, state_root)
    try:
        return conn.execute(
            "SELECT ordinal, path, reason, exception_kind, source "
            "FROM scope_exceptions WHERE id6 = ? ORDER BY ordinal",
            (id6,),
        ).fetchall()
    finally:
        conn.close()


def _replay_scope_payload_on_log(
    tmp_path: Path,
    *,
    id6: str,
    scope_fields: Dict[str, Any] | None,
) -> tuple[meta.State, List[tuple[Any, ...]]]:
    log_repo = tmp_path / f"log_{id6}"
    _, records_root, state_root = _setup_repo_layout(tmp_path / f"wrap_{id6}")
    del log_repo
    ctx = meta.legacy_context(records_root.parent.parent)
    res_create = meta.append(
        id6,
        [
            {
                "op": "create",
                "path": f"plans/pending/{id6}.ipd.md",
                "fields": {
                    "id": id6,
                    "type": "ipd",
                    "status": "approved",
                    "approval": "2026-11-09, human: approved",
                    "set": "demo",
                    "order": 1,
                },
            }
        ],
        project_context=ctx,
    )
    assert res_create["committed"] is True
    (records_root / "plans" / "pending" / f"{id6}.ipd.md").write_text(
        f"---\nid: {id6}\nstatus: approved\n---\n# Plan\n", encoding="utf-8"
    )

    events: List[Dict[str, Any]] = [
        {
            "op": "transition",
            "from": "approved",
            "to": "executed",
            "path": f"plans/executed/{id6}.ipd.md",
        },
        {"op": "unset", "fields": ["approval"]},
    ]
    if scope_fields is not None:
        events.append({"op": "set", "fields": scope_fields})

    res_fin = meta.append(id6, events, expect_seq=1, project_context=ctx)
    assert res_fin["committed"] is True
    assert res_fin["status"] == "executed"
    state = meta.read(id6, project_context=ctx)
    rows = _read_scope_exceptions(records_root, state_root, id6)
    return state, rows


def test_phase_b_finalize_and_log_replay_exceeded(tmp_path: Path) -> None:
    """Phase-B finalize exceeded writes - Scope-Exceeded: and replays untrimmed reasons on log."""
    repo, records_root, state_root = _setup_repo_layout(tmp_path)
    _init_git_repo(repo)
    LC.clear_checkout_control_root_cache()
    plan_id = "scpf01"
    plan_name = f"20261109-demo-01-{plan_id}-exceeded.ipd.md"
    plan_path = records_root / "plans" / "pending" / plan_name
    plan_path.write_text(
        _completed_child_plan_text(
            plan_id=plan_id, scope_paths="agent_workflows/demo.py"
        ),
        encoding="utf-8",
    )
    (repo / "agent_workflows" / "demo.py").write_text("v1\n", encoding="utf-8")
    _commit_all(repo, "init")

    raw_reason = "reason ; (with parens)\nand newline " + ("x" * 210)
    with support.coordinator_role():
        b_res = LC.begin(
            repo, plan_path, "test-actor", timestamp="2026-11-09T00:00:00Z"
        )
        assert b_res.exit_code == LC.EXIT_OK, b_res.message

        (repo / "agent_workflows" / "demo.py").write_text("v2\n", encoding="utf-8")
        (repo / "agent_workflows" / "extra.py").write_text("extra\n", encoding="utf-8")
        _commit_all(repo, "in-scope and out-of-scope edits")

        f_res = LC.finalize(
            repo,
            plan_path,
            "test-actor",
            "finalize exceeded",
            apply=True,
            scope_reasons={"agent_workflows/extra.py": raw_reason},
            env={},
        )
    assert f_res.exit_code == LC.EXIT_OK, f_res.message

    payload = f_res.evidence["finalize_scope_fields"]
    assert payload == {
        "scope_result": "exceeded",
        "out_of_scope_paths": [
            {"path": "agent_workflows/extra.py", "reason": raw_reason}
        ],
        "widened_paths": [],
    }

    executed_path = records_root / "plans" / "executed" / plan_name
    executed_text = executed_path.read_text(encoding="utf-8")
    expected_clean = ("reason  with parens and newline " + ("x" * 210)).strip()[
        :200
    ] + "..."
    assert (
        f"- Scope-Exceeded: agent_workflows/extra.py ({expected_clean})\n"
        in executed_text
    )

    ctx = meta.legacy_context(repo)
    st_legacy = meta.read(plan_id, project_context=ctx)
    assert st_legacy.fields["scope_result"] == "exceeded"
    assert st_legacy.fields["out_of_scope_paths"] == [
        {"path": "agent_workflows/extra.py", "reason": expected_clean}
    ]
    assert st_legacy.fields["scope_exceeded_raw"] is None
    assert _read_scope_exceptions(records_root, state_root, plan_id) == [
        (1, "agent_workflows/extra.py", expected_clean, "out-of-scope", "checkpoint")
    ]

    # Log-backed replay preserves full untrimmed reason with ';()' and '\n' intact.
    st_log, log_rows = _replay_scope_payload_on_log(
        tmp_path, id6="logex1", scope_fields=payload
    )
    assert st_log.fields["scope_result"] == "exceeded"
    assert st_log.fields["out_of_scope_paths"] == [
        {"path": "agent_workflows/extra.py", "reason": raw_reason}
    ]
    assert st_log.fields["widened_paths"] == []
    assert log_rows == [
        (1, "agent_workflows/extra.py", raw_reason, "out-of-scope", "finalize")
    ]


@pytest.mark.parametrize("committed", [True, False], ids=["committed", "uncommitted"])
def test_phase_b_finalize_and_log_replay_widened(
    tmp_path: Path, committed: bool
) -> None:
    """Phase-B finalize widened (committed and uncommitted) omits - Scope-Exceeded: and replays on log."""
    repo, records_root, state_root = _setup_repo_layout(tmp_path)
    _init_git_repo(repo)
    LC.clear_checkout_control_root_cache()
    plan_id = "scpf02" if committed else "scpf03"
    plan_name = f"20261109-demo-01-{plan_id}-widened.ipd.md"
    plan_path = records_root / "plans" / "pending" / plan_name
    plan_path.write_text(
        _completed_child_plan_text(
            plan_id=plan_id, scope_paths="agent_workflows/demo.py"
        ),
        encoding="utf-8",
    )
    (repo / "agent_workflows" / "demo.py").write_text("v1\n", encoding="utf-8")
    _commit_all(repo, "init")

    raw_reason = "widened ; (with parens) reason"
    with support.coordinator_role():
        b_res = LC.begin(
            repo, plan_path, "test-actor", timestamp="2026-11-09T00:00:00Z"
        )
        assert b_res.exit_code == LC.EXIT_OK, b_res.message

        (repo / "agent_workflows" / "demo.py").write_text("v2\n", encoding="utf-8")
        plan_path.write_text(
            plan_path.read_text(encoding="utf-8").replace(
                "- Scope-Paths: agent_workflows/demo.py",
                "- Scope-Paths: agent_workflows/demo.py, tests/test_extra.py",
            ),
            encoding="utf-8",
        )
        (repo / "tests" / "test_extra.py").write_text("extra test\n", encoding="utf-8")
        if committed:
            _commit_all(repo, "widen and commit test_extra.py")
        else:
            subprocess.run(
                [
                    "git",
                    "add",
                    "--",
                    "agent_workflows/demo.py",
                    str(plan_path.relative_to(repo)),
                ],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-q",
                    "-m",
                    "widen plan leaving test_extra uncommitted",
                ],
                cwd=repo,
                check=True,
            )

        f_res = LC.finalize(
            repo,
            plan_path,
            "test-actor",
            "finalize widened",
            apply=True,
            scope_reasons={"tests/test_extra.py": raw_reason},
            env={},
        )
    assert f_res.exit_code == LC.EXIT_OK, f_res.message

    payload = f_res.evidence["finalize_scope_fields"]
    assert payload == {
        "scope_result": "widened",
        "out_of_scope_paths": [],
        "widened_paths": [{"path": "tests/test_extra.py", "reason": raw_reason}],
    }

    executed_path = records_root / "plans" / "executed" / plan_name
    assert "- Scope-Exceeded:" not in executed_path.read_text(encoding="utf-8")

    ctx = meta.legacy_context(repo)
    st_legacy = meta.read(plan_id, project_context=ctx)
    assert st_legacy.fields["scope_result"] is None
    assert st_legacy.fields["out_of_scope_paths"] is None
    assert st_legacy.fields["widened_paths"] is None
    assert _read_scope_exceptions(records_root, state_root, plan_id) == []

    log_id = "logwd1" if committed else "logwd2"
    st_log, log_rows = _replay_scope_payload_on_log(
        tmp_path, id6=log_id, scope_fields=payload
    )
    assert st_log.fields["scope_result"] == "widened"
    assert st_log.fields["out_of_scope_paths"] == []
    assert st_log.fields["widened_paths"] == [
        {"path": "tests/test_extra.py", "reason": raw_reason}
    ]
    assert log_rows == [(1, "tests/test_extra.py", raw_reason, "widened", "finalize")]


def test_phase_b_finalize_and_log_replay_within(tmp_path: Path) -> None:
    """Phase-B finalize within omits - Scope-Exceeded:, reads None in phase B, and replays within on log."""
    repo, records_root, state_root = _setup_repo_layout(tmp_path)
    _init_git_repo(repo)
    LC.clear_checkout_control_root_cache()
    plan_id = "scpf04"
    plan_name = f"20261109-demo-01-{plan_id}-within.ipd.md"
    plan_path = records_root / "plans" / "pending" / plan_name
    plan_path.write_text(
        _completed_child_plan_text(
            plan_id=plan_id, scope_paths="agent_workflows/demo.py"
        ),
        encoding="utf-8",
    )
    (repo / "agent_workflows" / "demo.py").write_text("v1\n", encoding="utf-8")
    _commit_all(repo, "init")

    with support.coordinator_role():
        b_res = LC.begin(
            repo, plan_path, "test-actor", timestamp="2026-11-09T00:00:00Z"
        )
        assert b_res.exit_code == LC.EXIT_OK, b_res.message

        (repo / "agent_workflows" / "demo.py").write_text("v2\n", encoding="utf-8")
        _commit_all(repo, "in-scope edit")

        f_res = LC.finalize(
            repo,
            plan_path,
            "test-actor",
            "finalize within",
            apply=True,
            env={},
        )
    assert f_res.exit_code == LC.EXIT_OK, f_res.message

    payload = f_res.evidence["finalize_scope_fields"]
    assert payload == {
        "scope_result": "within",
        "out_of_scope_paths": [],
        "widened_paths": [],
    }

    executed_path = records_root / "plans" / "executed" / plan_name
    assert "- Scope-Exceeded:" not in executed_path.read_text(encoding="utf-8")

    ctx = meta.legacy_context(repo)
    st_legacy = meta.read(plan_id, project_context=ctx)
    assert st_legacy.fields["scope_result"] is None
    assert st_legacy.fields["out_of_scope_paths"] is None
    assert st_legacy.fields["widened_paths"] is None
    assert _read_scope_exceptions(records_root, state_root, plan_id) == []

    st_log, log_rows = _replay_scope_payload_on_log(
        tmp_path, id6="logwn1", scope_fields=payload
    )
    assert st_log.fields["scope_result"] == "within"
    assert st_log.fields["out_of_scope_paths"] == []
    assert st_log.fields["widened_paths"] == []
    assert log_rows == []


def test_phase_b_retire_orchestrator_rollup_and_log_replay(tmp_path: Path) -> None:
    """Orchestrator rollup omits scope fields in both phase B and log replay."""
    repo, records_root, state_root = _setup_repo_layout(tmp_path)
    _init_git_repo(repo)
    LC.clear_checkout_control_root_cache()

    child_id = "cld001"
    child_name = f"20261109-demo-01-{child_id}-child.ipd.md"
    (records_root / "plans" / "executed" / child_name).write_text(
        _completed_child_plan_text(
            plan_id=child_id,
            set_name="demo",
            order=1,
            status="executed",
            scope_paths="agent_workflows/demo.py",
        ),
        encoding="utf-8",
    )

    orch_id = "orc001"
    orch_name = f"20261109-demo-00-{orch_id}-orch.ipd.md"
    orch_text = support.ready_plan_text(
        plan_id=orch_id,
        kind="orchestrator",
        set_name="demo",
        order=0,
        status="approved",
        scope_paths="grandfathered",
    )
    orch_text = (
        orch_text.replace("c0ch01", child_id)
        .replace("TODO child plan filename", child_name)
        .replace("TODO what it does.", "child 01")
        .replace("### Task group 1: TODO", "### Task group 1: Child confirmation")
    )
    orch_path = records_root / "plans" / "pending" / orch_name
    orch_path.write_text(orch_text, encoding="utf-8")
    _commit_all(repo, "init orchestrator set")

    with support.coordinator_role():
        r_res = LC.retire_orchestrator(
            repo,
            orch_path,
            setid="demo",
            actor="aw oc run model=test",
            run_id="run-20261117T000000Z-1",
            apply=True,
            env={},
        )
    assert r_res.exit_code == LC.EXIT_OK, r_res.message
    assert r_res.evidence["finalize_scope_fields"] is None

    executed_orch = records_root / "plans" / "executed" / orch_name
    assert executed_orch.is_file()
    assert "- Scope-Exceeded:" not in executed_orch.read_text(encoding="utf-8")

    ctx = meta.legacy_context(repo)
    st_legacy = meta.read(orch_id, project_context=ctx)
    assert st_legacy.fields["scope_result"] is None
    assert st_legacy.fields["out_of_scope_paths"] is None
    assert st_legacy.fields["widened_paths"] is None
    assert _read_scope_exceptions(records_root, state_root, orch_id) == []

    st_log, log_rows = _replay_scope_payload_on_log(
        tmp_path, id6="logro1", scope_fields=None
    )
    assert st_log.fields["scope_result"] is None
    assert st_log.fields["out_of_scope_paths"] is None
    assert st_log.fields["widened_paths"] is None
    assert log_rows == []


def test_legacy_loader_scope_exceeded_raw_and_metadata_region_boundary(
    tmp_path: Path,
) -> None:
    """Malformed - Scope-Exceeded: sets scope_exceeded_raw; body-prose bullet is ignored."""
    repo, records_root, _ = _setup_repo_layout(tmp_path)
    ctx = meta.legacy_context(repo)

    mal_path = (
        records_root / "plans" / "executed" / "20261109-demo-01-mal001-malformed.ipd.md"
    )
    mal_path.write_text(
        "# IPD: Malformed\n\n"
        "- Id: mal001\n"
        "- Status: executed\n"
        "- Scope-Exceeded: agent_workflows/a.py (ok); bad_segment_without_parens\n\n"
        "## Goal\nG\n",
        encoding="utf-8",
    )
    st_mal = meta.read("mal001", project_context=ctx)
    assert st_mal.fields["scope_result"] == "exceeded"
    assert st_mal.fields["out_of_scope_paths"] == [
        {"path": "agent_workflows/a.py", "reason": "ok"}
    ]
    assert (
        st_mal.fields["scope_exceeded_raw"]
        == "agent_workflows/a.py (ok); bad_segment_without_parens"
    )

    body_path = (
        records_root / "plans" / "executed" / "20261109-demo-01-bdy001-body.ipd.md"
    )
    body_path.write_text(
        "# IPD: Body Quote\n\n"
        "- Id: bdy001\n"
        "- Status: executed\n\n"
        "## Notes\n"
        "- Scope-Exceeded: agent_workflows/fake.py (quoted in body prose)\n",
        encoding="utf-8",
    )
    st_body = meta.read("bdy001", project_context=ctx)
    assert st_body.fields["scope_result"] is None
    assert st_body.fields["out_of_scope_paths"] is None


def test_owned_scope_field_and_enum_refusals_on_legacy_and_log(
    tmp_path: Path,
) -> None:
    """Post-transition set/unset of scope fields and invalid scope_result raise ValueError with no disk change."""
    repo, records_root, _ = _setup_repo_layout(tmp_path)
    _init_git_repo(repo)
    ctx = meta.legacy_context(repo)

    # 1. Legacy executed plan on disk
    leg_path = (
        records_root / "plans" / "executed" / "20261109-demo-01-legref-refusal.ipd.md"
    )
    leg_path.write_text(
        "# IPD: Legacy Executed\n\n"
        "- Id: legref\n"
        "- Status: executed\n"
        "- Scope-Paths: agent_workflows/a.py\n\n"
        "## Workflow history\n"
        "- 2026-11-09 executed (aw set): status set to executed\n",
        encoding="utf-8",
    )
    _commit_all(repo, "add executed legacy plan")
    leg_sha_before = hashlib.sha256(leg_path.read_bytes()).hexdigest()
    leg_target = meta.LegacyTarget(leg_path, "plans", "legref")
    leg_render = meta.LegacyRender(
        "same-status", "2026-11-09", "aw set", status="executed"
    )

    # 2. Log-backed executed plan on disk
    log_id = "logref"
    meta.append(
        log_id,
        [
            {
                "op": "create",
                "path": f"plans/pending/{log_id}.ipd.md",
                "fields": {"id": log_id, "type": "ipd", "status": "approved"},
            }
        ],
        project_context=ctx,
    )
    (records_root / "plans" / "pending" / f"{log_id}.ipd.md").write_text(
        f"---\nid: {log_id}\nstatus: approved\n---\n# Plan\n", encoding="utf-8"
    )
    meta.append(
        log_id,
        [
            {
                "op": "transition",
                "from": "approved",
                "to": "executed",
                "path": f"plans/executed/{log_id}.ipd.md",
            },
            {
                "op": "set",
                "fields": {
                    "scope_result": "within",
                    "out_of_scope_paths": [],
                    "widened_paths": [],
                },
            },
        ],
        expect_seq=1,
        project_context=ctx,
    )
    log_path = records_root / "meta" / f"{log_id}.jsonl"
    log_sha_before = hashlib.sha256(log_path.read_bytes()).hexdigest()

    # Post-transition set and unset of each finalize-owned field fail on both legacy and log
    sample_values: Dict[str, Any] = {
        "scope_result": "within",
        "out_of_scope_paths": [{"path": "agent_workflows/x.py", "reason": "late"}],
        "widened_paths": [{"path": "tests/test_x.py", "reason": "late"}],
    }
    for fname, fval in sample_values.items():
        with pytest.raises(ValueError, match="outside transition to executed append"):
            meta.append(
                leg_target,
                [{"op": "set", "fields": {fname: fval}}],
                legacy_render=leg_render,
                repo_root=repo,
                project_context=ctx,
                from_status="executed",
            )
        with pytest.raises(ValueError, match="refuse unset of finalize-owned field"):
            meta.append(
                leg_target,
                [{"op": "unset", "fields": [fname]}],
                legacy_render=leg_render,
                repo_root=repo,
                project_context=ctx,
                from_status="executed",
            )
        with pytest.raises(ValueError, match="outside transition to executed append"):
            meta.append(
                log_id,
                [{"op": "set", "fields": {fname: fval}}],
                expect_seq=3,
                project_context=ctx,
            )
        with pytest.raises(ValueError, match="refuse unset of finalize-owned field"):
            meta.append(
                log_id,
                [{"op": "unset", "fields": [fname]}],
                expect_seq=3,
                project_context=ctx,
            )

    # Invalid scope_result enum refuses in validate_event, validate_new_events, legacy append, and log append
    bad_enum_ev = _base_event("set", fields={"scope_result": "invalid_enum"})
    with pytest.raises(ValueError, match="invalid scope_result"):
        meta.validate_event(bad_enum_ev, "ipd")
    with pytest.raises(ValueError, match="invalid scope_result"):
        meta.validate_new_events(
            "ipd", [bad_enum_ev], records_root=records_root, repo_root=repo
        )

    leg_pending = (
        records_root / "plans" / "pending" / "20261109-demo-01-legbad-bad.ipd.md"
    )
    leg_pending.write_text(
        "# IPD: Pending\n\n- Id: legbad\n- Status: approved\n", encoding="utf-8"
    )
    leg_pending_before = hashlib.sha256(leg_pending.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="invalid scope_result"):
        meta.append(
            meta.LegacyTarget(leg_pending, "plans", "legbad"),
            [
                {"op": "transition", "from": "approved", "to": "executed"},
                {"op": "set", "fields": {"scope_result": "invalid_enum"}},
            ],
            legacy_render=meta.LegacyRender(
                "executed", "2026-11-09", "aw set", status="executed"
            ),
            repo_root=repo,
            project_context=ctx,
            from_status="approved",
        )

    log_bad_id = "logbad"
    meta.append(
        log_bad_id,
        [
            {
                "op": "create",
                "path": f"plans/pending/{log_bad_id}.ipd.md",
                "fields": {"id": log_bad_id, "type": "ipd", "status": "approved"},
            }
        ],
        project_context=ctx,
    )
    log_bad_path = records_root / "meta" / f"{log_bad_id}.jsonl"
    log_bad_before = hashlib.sha256(log_bad_path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="invalid scope_result"):
        meta.append(
            log_bad_id,
            [
                {
                    "op": "transition",
                    "from": "approved",
                    "to": "executed",
                    "path": f"plans/executed/{log_bad_id}.ipd.md",
                },
                {"op": "set", "fields": {"scope_result": "invalid_enum"}},
            ],
            expect_seq=1,
            project_context=ctx,
        )

    assert hashlib.sha256(leg_path.read_bytes()).hexdigest() == leg_sha_before
    assert hashlib.sha256(log_path.read_bytes()).hexdigest() == log_sha_before
    assert hashlib.sha256(leg_pending.read_bytes()).hexdigest() == leg_pending_before
    assert hashlib.sha256(log_bad_path.read_bytes()).hexdigest() == log_bad_before

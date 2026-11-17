"""Tests for OQ-03 and D-6 repository-root path validation on scope fields.

Covers spec 4sd62s AC-15, AC-24, and AC-34 (IPD 9qhtrc / E-03, V-03):
1. End-to-end append/read storage of repository-relative code paths in
   out_of_scope_paths and widened_paths, plus scope_exceptions projection.
2. Symlink root separation between records_root and repo_root.
3. Input-safety, shape, string-safety, and leak-sanitizer refusals.
4. Non-git tmp_path .aw/records and .agents/records repo_root fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from agent_workflows import artifact_meta as meta


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

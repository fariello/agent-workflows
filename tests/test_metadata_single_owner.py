"""Behavioral proof that `artifact_meta` is the sole metadata reader and writer (spec `4sd62s` AC-1; IPD `9o83cr` E-13 / V-13).

Tests observable CLI behavior through `cli.main` without reading production source code:
  (a) Monkeypatching `artifact_meta.read`, `query`, `history`, `resolve`, and `read_at` to return
      one sentinel `executed` state for a built `draft` plan causes `aw find`,
      `aw attention --format json`, `aw show <id6> --format json`, `aw ipd lint`,
      `aw check plans --agent`, and `aw ipd-executed-gate` (on a staged fixture) to reflect the
      sentinel status instead of the on-disk `- Status: draft` bullet.
  (b) Monkeypatching `artifact_meta.append` and `create` to raise causes `aw ipd set`,
      `aw backlog set`, `aw specs set`, `aw group plans`, and `aw prompts new` to exit nonzero and
      leave every file under `.aw/records/` byte-identical.
  (c) With no patch, the same five commands exit 0 and change the state returned by
      `artifact_meta.read`.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

import pytest

from agent_workflows import artifact_meta, cli, project_context
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core

_PLAN_ID = "pln001"
_BACKLOG_ID = "bkl001"
_SPEC_ID = "spc001"
_SENTINEL_STATUS = "executed"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def _run_cli(repo: Path, argv: List[str]) -> Tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    prev_cwd = os.getcwd()
    prev_noninteractive = os.environ.get("AW_NONINTERACTIVE")
    os.chdir(repo)
    os.environ["AW_NONINTERACTIVE"] = "1"
    try:
        with patch("sys.stdout", out), patch("sys.stderr", err):
            try:
                rc = cli.main(argv)
            except SystemExit as exc:
                rc = exc.code if isinstance(exc.code, int) else 1
    finally:
        os.chdir(prev_cwd)
        if prev_noninteractive is None:
            os.environ.pop("AW_NONINTERACTIVE", None)
        else:
            os.environ["AW_NONINTERACTIVE"] = prev_noninteractive
    return int(rc), out.getvalue(), err.getvalue()


def _snapshot_records(repo: Path) -> Dict[str, bytes]:
    recs = repo / ".aw" / "records"
    snap: Dict[str, bytes] = {}
    if not recs.exists():
        return snap
    for p in sorted(recs.rglob("*")):
        if p.is_file():
            snap[p.relative_to(recs).as_posix()] = p.read_bytes()
    return snap


def _build_fixture_repo(
    tmp_path: Path, name: str = "single_owner"
) -> Tuple[Path, Path]:
    repo = (tmp_path / name).resolve()
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test Author")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")

    wf_dir = repo / ".aw" / "system" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    (wf_dir / "index.md").write_text("# Workflows\n", encoding="utf-8")

    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "preset": "private-target",
                "role": "target",
                "placements": {
                    "system": "target-tracked",
                    "config_project": "target-tracked",
                    "config_local": "target-ignored",
                    "state_durable": "target-tracked",
                    "state_runtime": "target-ignored",
                    "records": "target-tracked",
                },
                "records_backend": "repository",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    recs = repo / ".aw" / "records"
    for sub in (
        "plans/pending",
        "plans/executed",
        "specs/draft",
        "specs/to-review",
        "backlog/open",
        "backlog/done",
        "prompts/pending",
    ):
        (recs / sub).mkdir(parents=True, exist_ok=True)

    plan_path = (
        recs
        / "plans"
        / "pending"
        / f"20261101-cset-01-{_PLAN_ID}-single-owner-plan.ipd.md"
    )
    plan_text = str(
        RecordBuilder().plan(
            title="Single Owner Plan",
            when="2026-11-01",
            plan_role="child",
            scope_paths="tests/test_metadata_single_owner.py",
            item_dependencies="none",
            status="draft",
            work_kind="chore",
            priority="low",
            set="cset",
            order=1,
            highest_e_allocated="01",
            author="tester",
            review_depth="simple",
            id6=_PLAN_ID,
            history=["- 2026-11-01 draft (tester): created"],
            body=(
                "## Goal\n\n"
                "Verify single metadata owner across all CLI read and write surfaces.\n\n"
                "## Detailed Implementation Checklist (TODO)\n\n"
                "- [ ] E-01 Run single-owner check\n"
                "  - Depends on: none\n"
                "  - Expected outcome: command reflects artifact_meta state\n"
                "  - Execution state: pending\n\n"
                "## Project conventions discovered (Step 0)\n\n"
                "- Core tests run via pytest.\n\n"
                "## Findings\n\n"
                "- None.\n\n"
                "## Proposed changes (ordered, validatable)\n\n"
                "1. Drive CLI commands against fixture repository.\n\n"
                "## Deferred / out of scope (with reason)\n\n"
                "None.\n\n"
                "## Scope check\n\n"
                "- Over-scope: none.\n"
                "- Under-scope: none.\n\n"
                "## Required tests / validation\n\n"
                "Run pytest on tests/test_metadata_single_owner.py.\n\n"
                "## Spec / documentation sync\n\n"
                "N/A.\n\n"
                "## Open questions\n\n"
                "None.\n\n"
                "## Validation and cross-check (verify before reporting done)\n\n"
                "- [ ] V-01 validates E-01\n"
                "  - Required evidence: paste pytest output with every case PASSED\n"
                "  - Observed evidence:\n"
                "  - Result: pending\n\n"
                "## Approval and execution gate\n\n"
                "- Size assessment: standard\n"
                "- Cohesion rationale: not required"
            ),
            raw_fields={
                "Concern": "Verify single metadata owner across read and write surfaces.",
                "Scope": "Exercise CLI commands on a minimal fixture.",
            },
            text_only=True,
        )
    )
    plan_path.write_text(plan_text, encoding="utf-8")

    spec_path = (
        recs
        / "specs"
        / "draft"
        / f"20261101-{_SPEC_ID}-01-{_SPEC_ID}-single-owner-spec.spec.md"
    )
    spec_text = str(
        RecordBuilder().spec(
            title="Single Owner Spec",
            when="2026-11-01",
            id6=_SPEC_ID,
            status="draft",
            set=_SPEC_ID,
            order=1,
            history=["- 2026-11-01 draft (tester): created"],
            body="## Overview\n\nMinimal spec fixture for single-owner write tests.",
            text_only=True,
        )
    )
    spec_path.write_text(spec_text, encoding="utf-8")

    backlog_path = (
        recs
        / "backlog"
        / "open"
        / f"20261101-bklset-01-{_BACKLOG_ID}-single-owner-item.backlog.md"
    )
    backlog_text = str(
        RecordBuilder().backlog(
            id6=_BACKLOG_ID,
            status="open",
            set="bklset",
            priority="low",
            work_kind="chore",
            summary="Single owner backlog item",
            when="2026-11-01",
            body="### Problem Statement\n\nMinimal backlog fixture for single-owner write tests.",
            text_only=True,
        )
    )
    backlog_path.write_text(backlog_text, encoding="utf-8")

    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "initial fixture records")
    return repo, plan_path


def _make_sentinel_state(plan_rel: str) -> artifact_meta.State:
    return artifact_meta.State(
        id6=_PLAN_ID,
        type="ipd",
        status=_SENTINEL_STATUS,
        legacy_raw_status=_SENTINEL_STATUS,
        path=plan_rel,
        disposition="pending",
        title="Single Owner Plan",
        set_id="cset",
        legacy_raw_set="cset",
        order_nn=1,
        filename_date="2026-11-01",
        created_day="2026-11-01",
        last_history_day="2026-11-01",
        last_seq=1,
        valid=1,
        fields={
            "date": "2026-11-01",
            "kind": "child",
            "set": "cset",
            "order": 1,
            "priority": "low",
            "work_kind": "chore",
            "author": "tester",
            "review_depth": "simple",
            "highest_e_allocated": 1,
            "scope_paths": ["tests/test_metadata_single_owner.py"],
            "item_dependencies": [],
        },
    )


def _patch_readers_with_sentinel(
    monkeypatch: pytest.MonkeyPatch, plan_rel: str
) -> artifact_meta.State:
    sentinel = _make_sentinel_state(plan_rel)
    sentinel_history = [
        {
            "seq": 1,
            "op": "legacy",
            "at": "2026-11-01T00:00:00Z",
            "payload": {"line": "- 2026-11-01 draft (tester): created"},
        }
    ]
    real_read = artifact_meta.read
    real_query = artifact_meta.query
    real_history = artifact_meta.history
    real_resolve = artifact_meta.resolve
    real_read_at = artifact_meta.read_at

    def _fake_read(id6: str, *, project_context: Any = None) -> artifact_meta.State:
        if id6 == _PLAN_ID:
            return sentinel
        return real_read(id6, project_context=project_context)

    def _fake_query(
        *,
        project_context: Any = None,
        include_fields: bool = False,
        **filters: Any,
    ) -> artifact_meta.QueryResult:
        res = real_query(
            project_context=project_context,
            include_fields=include_fields,
            **filters,
        )
        status_filter = filters.get("status")
        rows: List[artifact_meta.State] = []
        seen_sentinel = False
        for row in res.rows:
            if row.id6 == _PLAN_ID:
                seen_sentinel = True
                if status_filter is None or status_filter == sentinel.status:
                    rows.append(sentinel)
            else:
                rows.append(row)
        if not seen_sentinel and filters.get("type") in (None, "ipd"):
            if filters.get("id6") in (None, _PLAN_ID) and (
                status_filter is None or status_filter == sentinel.status
            ):
                if filters.get("set_id") in (None, sentinel.set_id) and filters.get(
                    "set"
                ) in (None, sentinel.set_id):
                    rows.append(sentinel)
        return artifact_meta.QueryResult(rows, list(res.incomplete))

    def _fake_history(id6: str, *, project_context: Any = None) -> List[Dict[str, Any]]:
        if id6 == _PLAN_ID:
            return list(sentinel_history)
        return real_history(id6, project_context=project_context)

    def _fake_resolve(
        path_or_id6: Any, *, project_context: Any = None
    ) -> Optional[str]:
        val = str(path_or_id6).strip().replace("\\", "/")
        if val == _PLAN_ID or val.endswith(plan_rel):
            return plan_rel
        return real_resolve(path_or_id6, project_context=project_context)

    def _fake_read_at(
        id6: str,
        rev: str,
        *,
        project_context: Any = None,
        path_hint: Optional[str] = None,
    ) -> artifact_meta.ReadAtResult:
        if id6 == _PLAN_ID and rev == ":0:":
            return artifact_meta.ReadAtResult(
                kind="ok",
                state=sentinel,
                history=list(sentinel_history),
            )
        return real_read_at(
            id6,
            rev,
            project_context=project_context,
            path_hint=path_hint,
        )

    monkeypatch.setattr(artifact_meta, "read", _fake_read)
    monkeypatch.setattr(artifact_meta, "query", _fake_query)
    monkeypatch.setattr(artifact_meta, "history", _fake_history)
    monkeypatch.setattr(artifact_meta, "resolve", _fake_resolve)
    monkeypatch.setattr(artifact_meta, "read_at", _fake_read_at)
    return sentinel


# --------------------------------------------------------------------------------------
# (a) Six read surfaces reflect the sentinel state from artifact_meta, not disk bullets
# --------------------------------------------------------------------------------------


def test_read_find_reflects_sentinel_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, plan_path = _build_fixture_repo(tmp_path, "read_find")
    plan_rel = plan_path.relative_to(repo / ".aw" / "records").as_posix()
    assert "- Status: draft" in plan_path.read_text(encoding="utf-8")

    _patch_readers_with_sentinel(monkeypatch, plan_rel)
    rc_sent, out_sent, err_sent = _run_cli(
        repo,
        ["find", "plans", "--status", _SENTINEL_STATUS, "--agent", "--dir", str(repo)],
    )
    assert rc_sent == 0, err_sent
    sent_items = [
        json.loads(line)
        for line in out_sent.splitlines()
        if line.strip() and json.loads(line).get("kind") == "item"
    ]
    assert [it.get("id6") for it in sent_items] == [_PLAN_ID]

    rc_disk, out_disk, err_disk = _run_cli(
        repo,
        ["find", "plans", "--status", "draft", "--agent", "--dir", str(repo)],
    )
    assert rc_disk == 0, err_disk
    disk_items = [
        json.loads(line)
        for line in out_disk.splitlines()
        if line.strip() and json.loads(line).get("kind") == "item"
    ]
    assert disk_items == []
    assert "- Status: draft" in plan_path.read_text(encoding="utf-8")


def test_read_attention_reflects_sentinel_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, plan_path = _build_fixture_repo(tmp_path, "read_attention")
    plan_rel = plan_path.relative_to(repo / ".aw" / "records").as_posix()

    _patch_readers_with_sentinel(monkeypatch, plan_rel)
    rc, out, err = _run_cli(repo, ["attention", "--format", "json", "--dir", str(repo)])
    assert rc in (0, 1), err
    payload = json.loads(out)
    plan_items = [it for it in payload["items"] if it.get("id") == _PLAN_ID]
    assert len(plan_items) == 1
    assert plan_items[0]["native_status"] == _SENTINEL_STATUS
    assert plan_items[0]["attention_class"] == "done"
    assert "- Status: draft" in plan_path.read_text(encoding="utf-8")


def test_read_show_json_reflects_sentinel_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, plan_path = _build_fixture_repo(tmp_path, "read_show")
    plan_rel = plan_path.relative_to(repo / ".aw" / "records").as_posix()

    _patch_readers_with_sentinel(monkeypatch, plan_rel)
    rc, out, err = _run_cli(
        repo, ["show", _PLAN_ID, "--format", "json", "--dir", str(repo)]
    )
    assert rc == 0, err
    payload = json.loads(out)
    records = payload.get("data", {}).get("records") or []
    assert len(records) == 1
    assert records[0]["id6"] == _PLAN_ID
    assert records[0]["status"] == _SENTINEL_STATUS
    assert "- Status: draft" in plan_path.read_text(encoding="utf-8")


def test_read_ipd_lint_reflects_sentinel_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, plan_path = _build_fixture_repo(tmp_path, "read_lint")
    plan_rel = plan_path.relative_to(repo / ".aw" / "records").as_posix()

    rc_unpatched, out_unpatched, _ = _run_cli(repo, ["ipd", "lint", str(plan_path)])
    assert rc_unpatched == 0, out_unpatched
    assert "draft" in out_unpatched

    _patch_readers_with_sentinel(monkeypatch, plan_rel)
    rc_patched, out_patched, err_patched = _run_cli(
        repo, ["ipd", "lint", str(plan_path)]
    )
    assert rc_patched != 0, out_patched + err_patched
    assert _SENTINEL_STATUS in out_patched
    assert "IPD-M105" in out_patched or "IPD-S405" in out_patched
    assert "- Status: draft" in plan_path.read_text(encoding="utf-8")


def test_read_check_plans_reflects_sentinel_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, plan_path = _build_fixture_repo(tmp_path, "read_check_plans")
    plan_rel = plan_path.relative_to(repo / ".aw" / "records").as_posix()

    rc_unpatched, out_unpatched, err_unpatched = _run_cli(
        repo, ["check", "plans", "--agent", "--dir", str(repo)]
    )
    assert rc_unpatched in (0, 1), err_unpatched
    unpatched_rules = {
        d.get("rule") for d in json.loads(out_unpatched).get("diagnostics", [])
    }

    _patch_readers_with_sentinel(monkeypatch, plan_rel)
    rc_patched, out_patched, err_patched = _run_cli(
        repo, ["check", "plans", "--agent", "--dir", str(repo)]
    )
    assert rc_patched in (0, 1), err_patched
    patched_payload = json.loads(out_patched)
    patched_diags = patched_payload.get("diagnostics", [])
    patched_rules = {d.get("rule") for d in patched_diags}

    assert patched_rules != unpatched_rules
    assert "check.ipd-lint-diagnostic" in patched_rules, patched_diags
    assert "check.ipd-lint-diagnostic" not in unpatched_rules, unpatched_rules
    assert "check.ipd-draft-ready" not in patched_rules
    assert "- Status: draft" in plan_path.read_text(encoding="utf-8")


def test_read_ipd_executed_gate_reflects_sentinel_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, plan_path = _build_fixture_repo(tmp_path, "read_exec_gate")
    plan_rel = plan_path.relative_to(repo / ".aw" / "records").as_posix()

    # Stage a benign body edit while leaving `- Status: draft` unchanged on disk.
    plan_path.write_text(
        plan_path.read_text(encoding="utf-8") + "\n<!-- benign staged edit -->\n",
        encoding="utf-8",
    )
    _git(repo, "add", str(plan_path.relative_to(repo)))

    rc_unpatched, out_unpatched, err_unpatched = _run_cli(repo, ["ipd-executed-gate"])
    assert rc_unpatched == 0, out_unpatched + err_unpatched

    _patch_readers_with_sentinel(monkeypatch, plan_rel)
    rc_patched, out_patched, err_patched = _run_cli(repo, ["ipd-executed-gate"])
    assert rc_patched != 0, out_patched + err_patched
    combined = out_patched + err_patched
    assert _PLAN_ID in combined or "executed" in combined.lower()
    assert "- Status: draft" in plan_path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------------------
# (b) Five writers exit nonzero and leave every record byte-identical when append/create raise
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label,argv_builder",
    [
        (
            "ipd_set",
            lambda repo: [
                "ipd",
                "set",
                "to-review",
                _PLAN_ID,
                "--yes",
                "--no-commit",
                "--dir",
                str(repo),
            ],
        ),
        (
            "backlog_set",
            lambda repo: [
                "backlog",
                "set",
                "done",
                _BACKLOG_ID,
                "--yes",
                "--no-commit",
                "--message",
                "single-owner close check",
                "--dir",
                str(repo),
            ],
        ),
        (
            "specs_set",
            lambda repo: [
                "specs",
                "set",
                "to-review",
                _SPEC_ID,
                "--yes",
                "--no-commit",
                "--dir",
                str(repo),
            ],
        ),
        (
            "group_plans",
            lambda repo: [
                "group",
                "plans",
                _PLAN_ID,
                "--set",
                "newset",
                "--rename",
                "--apply",
                "--no-commit",
                "--dir",
                str(repo),
            ],
        ),
        (
            "prompts_new",
            lambda repo: [
                "prompts",
                "new",
                "--slug",
                "single-owner-prompt",
                "--set",
                "pset",
                "--date",
                "2026-11-01",
                "--apply",
                "--dir",
                str(repo),
            ],
        ),
    ],
)
def test_writers_fail_closed_and_leave_records_byte_identical_when_meta_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    label: str,
    argv_builder: Any,
) -> None:
    repo, _ = _build_fixture_repo(tmp_path, f"write_fail_{label}")
    before = _snapshot_records(repo)

    def _boom(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError(f"injected artifact_meta failure for {label}")

    monkeypatch.setattr(artifact_meta, "append", _boom)
    monkeypatch.setattr(artifact_meta, "create", _boom)

    rc = 0
    raised = False
    try:
        rc, _out, _err = _run_cli(repo, argv_builder(repo))
    except RuntimeError:
        raised = True

    assert (
        raised or rc != 0
    ), f"{label} succeeded despite patched artifact_meta.append/create"
    after = _snapshot_records(repo)
    assert (
        after == before
    ), f"{label} mutated record bytes despite artifact_meta raising"


# --------------------------------------------------------------------------------------
# (c) With no patch, the same five writers change the state artifact_meta.read returns
# --------------------------------------------------------------------------------------


def test_unpatched_writers_update_artifact_meta_read_state(tmp_path: Path) -> None:
    repo, _ = _build_fixture_repo(tmp_path, "write_live")
    ctx = project_context.resolve_project_context(target_repo=str(repo))

    assert artifact_meta.read(_PLAN_ID, project_context=ctx).status == "draft"
    rc, out, err = _run_cli(
        repo,
        [
            "ipd",
            "set",
            "to-review",
            _PLAN_ID,
            "--yes",
            "--no-commit",
            "--dir",
            str(repo),
        ],
    )
    assert rc == 0, out + err
    assert artifact_meta.read(_PLAN_ID, project_context=ctx).status == "to-review"

    assert artifact_meta.read(_BACKLOG_ID, project_context=ctx).status == "open"
    rc, out, err = _run_cli(
        repo,
        [
            "backlog",
            "set",
            "done",
            _BACKLOG_ID,
            "--yes",
            "--no-commit",
            "--message",
            "single-owner close check",
            "--dir",
            str(repo),
        ],
    )
    assert rc == 0, out + err
    assert artifact_meta.read(_BACKLOG_ID, project_context=ctx).status == "done"

    assert artifact_meta.read(_SPEC_ID, project_context=ctx).status == "draft"
    rc, out, err = _run_cli(
        repo,
        [
            "specs",
            "set",
            "to-review",
            _SPEC_ID,
            "--yes",
            "--no-commit",
            "--dir",
            str(repo),
        ],
    )
    assert rc == 0, out + err
    assert artifact_meta.read(_SPEC_ID, project_context=ctx).status == "to-review"

    assert artifact_meta.read(_PLAN_ID, project_context=ctx).set_id == "cset"
    rc, out, err = _run_cli(
        repo,
        [
            "group",
            "plans",
            _PLAN_ID,
            "--set",
            "newset",
            "--rename",
            "--apply",
            "--no-commit",
            "--dir",
            str(repo),
        ],
    )
    assert rc == 0, out + err
    grouped_state = artifact_meta.read(_PLAN_ID, project_context=ctx)
    assert grouped_state.set_id == "newset"
    assert grouped_state.fields.get("set") == "newset"

    before_prompts = {
        st.id6 for st in artifact_meta.query(type="prompt", project_context=ctx).rows
    }
    rc, out, err = _run_cli(
        repo,
        [
            "prompts",
            "new",
            "--slug",
            "single-owner-prompt",
            "--set",
            "pset",
            "--date",
            "2026-11-01",
            "--apply",
            "--dir",
            str(repo),
        ],
    )
    assert rc == 0, out + err
    after_prompts = {
        st.id6 for st in artifact_meta.query(type="prompt", project_context=ctx).rows
    }
    created_ids = after_prompts - before_prompts
    assert len(created_ids) == 1
    created_id = next(iter(created_ids))
    created_state = artifact_meta.read(created_id, project_context=ctx)
    assert created_state.type == "prompt"
    assert created_state.status == "pending"
    assert created_state.set_id == "pset"

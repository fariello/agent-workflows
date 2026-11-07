"""The phase-B LEGACY write branch of `artifact_meta.append` (plan 2xwb9b E-03 to E-06).

Until the cutover no record has a `meta/<id6>.jsonl` log, so `append` renders its events into the
record's bullet-format Markdown. These tests drive `artifact_meta.append` directly on `tmp_path`
fixtures and assert on file bytes, raised refusals and the sidecar file:

- `render`: each W-row behavior renders the same bytes the setter wrote before the move;
- `preview`/`fresh`/`pathkey`: dry-run previews, the source-digest freshness check, id-less targets;
- `move`/`sidecar`/`order`: the disposition move, the specs/backlog sidecar record, failure order;
- `owned`/`review_kind`/`refinement`: the event-owned field rules (AC-15, AC-14a (1)-(3)).
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from agent_workflows import artifact_core
from agent_workflows import artifact_meta as meta

pytestmark = pytest.mark.core

DAY = "2030-01-02"


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=root)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root)
    (root / ".aw" / "records").mkdir(parents=True)
    return root


def _write(root: Path, rel: str, text: str) -> Path:
    p = root / ".aw" / "records" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _append(
    root: Path, path: Path, plural: str, events, *, tag: str = "same-status", **kw
):
    id6 = kw.pop("id6", None)
    render = kw.pop("render", None) or meta.LegacyRender(tag, DAY, "aw set")
    return meta.append(
        meta.LegacyTarget(path, plural, id6),
        events,
        legacy_render=render,
        repo_root=root,
        **kw,
    )


PLAN = (
    "# IPD: P\n\n- Date: 2026-01-01\n- Status: draft\n- Work-Kind: chore\n- Priority: low\n"
    "- Set: pset\n- Id: pl0001\n\n## Workflow history\n- 2026-01-01 draft (a): c\n\n## Goal\nG\n"
)


# --------------------------------------------------------------------------------------------------
# render: the legacy branch renders today's bytes
# --------------------------------------------------------------------------------------------------


def test_render_w01_status_bullet_and_w18_history_line(repo: Path) -> None:
    p = _write(repo, "plans/pending/20260101-pset-01-pl0001-p.ipd.md", PLAN)
    _append(
        repo,
        p,
        "plans",
        [
            {
                "op": "transition",
                "from": "draft",
                "to": "to-review",
                "message": "status set to to-review",
            }
        ],
        tag="to-review",
        id6="pl0001",
    )
    assert p.read_text(encoding="utf-8") == PLAN.replace(
        "- Status: draft", "- Status: to-review"
    ).replace(
        "## Workflow history\n",
        f"## Workflow history\n- {DAY} to-review (aw set): status set to to-review\n",
    )


def test_render_w02_yaml_status_and_w04_insert_before_closing_fence(repo: Path) -> None:
    with_status = _write(
        repo,
        "research/20260101-r-01-rs0001-x.research-report.md",
        "---\nid: rs0001\nstatus: active\n---\n\n# R\n",
    )
    _append(
        repo,
        with_status,
        "research",
        [{"op": "transition", "from": "active", "to": "todo", "message": "m"}],
        tag="todo",
        render=meta.LegacyRender("todo", DAY, "aw set", history=False),
    )
    assert (
        with_status.read_text(encoding="utf-8")
        == "---\nid: rs0001\nstatus: todo\n---\n\n# R\n"
    )

    without = _write(
        repo,
        "research/20260101-r-01-rs0002-x.research-report.md",
        "---\nid: rs0002\n---\n\n# R\n",
    )
    _append(
        repo,
        without,
        "research",
        [{"op": "transition", "from": "draft", "to": "todo", "message": "m"}],
        render=meta.LegacyRender("todo", DAY, "aw set", history=False),
    )
    assert (
        without.read_text(encoding="utf-8")
        == "---\nid: rs0002\nstatus: todo\n---\n\n# R\n"
    )


def test_render_w03_prompt_comment_status_and_commentless_note(repo: Path) -> None:
    p = _write(
        repo,
        "prompts/pending/20260101-pq-01-pq0001-x.prompt.md",
        "<!-- aw-prompt: Id: pq0001 | Set: pq | Status: pending -->\n# P\n\nBody\n",
    )
    _append(
        repo,
        p,
        "prompts",
        [{"op": "transition", "from": "pending", "to": "executed", "message": "m"}],
        render=meta.LegacyRender("executed", DAY, "aw set", history=False),
    )
    assert p.read_text(encoding="utf-8").splitlines()[0] == (
        "<!-- aw-prompt: Id: pq0001 | Set: pq | Status: executed -->"
    )
    bare = _write(
        repo, "prompts/pending/20260101-pq-01-pq0002-x.prompt.md", "# P\n\nBody\n"
    )
    notes: list = []
    _append(
        repo,
        bare,
        "prompts",
        [{"op": "transition", "from": "pending", "to": "executed", "message": "m"}],
        render=meta.LegacyRender("executed", DAY, "aw set", history=False),
        notes_out=notes,
    )
    assert bare.read_text(encoding="utf-8") == "# P\n\nBody\n"
    assert any("has no metadata comment" in n for n in notes)


def test_render_w04_plan_without_status_inserts_after_title(repo: Path) -> None:
    p = _write(
        repo,
        "plans/pending/20260101-n-01-ns0001-x.ipd.md",
        "# IPD: X\n\n- Date: 2026-01-01\n- Id: ns0001\n",
    )
    _append(
        repo,
        p,
        "plans",
        [{"op": "transition", "from": "draft", "to": "to-review"}],
        render=meta.LegacyRender("to-review", DAY, "aw set", history=False),
    )
    assert (
        p.read_text(encoding="utf-8")
        == "# IPD: X\n- Status: to-review\n\n- Date: 2026-01-01\n- Id: ns0001\n"
    )


BACKLOG = (
    "- Id: bk0001\n- Status: open\n- Priority: low\n- Work-Kind: chore\n- Summary: x\n\n"
    "## Workflow history\n- 2026-01-01 created (a): c\n"
)


def test_render_w05_gate_block_written_after_status_and_stripped_on_leaving(
    repo: Path,
) -> None:
    p = _write(repo, "backlog/open/20260101-b-01-bk0001-x.backlog.md", BACKLOG)
    _append(
        repo,
        p,
        "backlog",
        [
            {"op": "transition", "from": "open", "to": "blocked"},
            {
                "op": "set",
                "fields": {
                    "gate_kind": "decision",
                    "gate_ref": "D7",
                    "gate_summary": "wait",
                },
            },
        ],
        render=meta.LegacyRender("blocked", DAY, "aw set", history=False),
    )
    text = p.read_text(encoding="utf-8")
    assert text.startswith(
        "- Id: bk0001\n- Status: blocked\n- Gate-Kind: decision\n- Gate-Ref: D7\n- Gate-Summary: wait\n- Priority: low\n"
    )
    _append(
        repo,
        p,
        "backlog",
        [
            {"op": "transition", "from": "blocked", "to": "open"},
            {"op": "unset", "fields": ["gate_kind", "gate_ref", "gate_summary"]},
        ],
        render=meta.LegacyRender("open", DAY, "aw set", history=False),
    )
    assert p.read_text(encoding="utf-8") == BACKLOG


@pytest.mark.parametrize(
    ("field", "value", "bullet"),
    [
        ("blocks_release", "next", "- Blocks-Release: next"),  # W-06
        ("from_backlog", "bk0009", "- From-Backlog: bk0009"),  # W-08
        ("from_spec", "sp0009", "- From-Spec: sp0009"),  # W-09
        (
            "item_dependencies",
            "executed:aa0001",
            "- Item-Dependencies: executed:aa0001",
        ),  # W-10
        ("priority", "high", "- Priority: high"),  # W-11
        ("work_kind", "bug", "- Work-Kind: bug"),  # W-11
    ],
)
def test_render_w06_to_w11_value_bullets_set_and_clear(
    repo: Path, field, value, bullet
) -> None:
    p = _write(repo, "plans/pending/20260101-pset-01-pl0001-p.ipd.md", PLAN)
    _append(
        repo,
        p,
        "plans",
        [{"op": "set", "fields": {field: value}}],
        render=meta.LegacyRender("same-status", DAY, "aw set", history=False),
    )
    assert bullet in p.read_text(encoding="utf-8").splitlines()
    _append(
        repo,
        p,
        "plans",
        [{"op": "unset", "fields": [field]}],
        render=meta.LegacyRender("same-status", DAY, "aw set", history=False),
    )
    label = bullet.split(":")[0] + ":"
    assert not any(
        ln.startswith(label) for ln in p.read_text(encoding="utf-8").splitlines()
    )


def test_render_w07_w12_w15_backlog_value_bullets(repo: Path) -> None:
    p = _write(repo, "backlog/open/20260101-b-01-bk0001-x.backlog.md", BACKLOG)
    _append(
        repo,
        p,
        "backlog",
        [
            {"op": "set", "fields": {"release_exempt_ref": "D9"}},
            {"op": "set", "fields": {"release_exempt_kind": "decision"}},
            {"op": "set", "fields": {"graduated_to": "someset"}},
            {"op": "set", "fields": {"close_evidence": "docs/x.md"}},
        ],
        render=meta.LegacyRender("same-status", DAY, "aw set", history=False),
    )
    lines = p.read_text(encoding="utf-8").splitlines()
    for want in (
        "- Release-Exempt-Kind: decision",
        "- Release-Exempt-Ref: D9",
        "- Graduated-To: someset",
        "- Close-Evidence: docs/x.md",
    ):
        assert want in lines


def test_render_w14_kind_canonicalized_to_work_kind(repo: Path) -> None:
    p = _write(
        repo,
        "backlog/open/20260101-b-01-bk0002-x.backlog.md",
        BACKLOG.replace("bk0001", "bk0002").replace(
            "- Work-Kind: chore", "- Kind: chore"
        ),
    )
    _append(
        repo,
        p,
        "backlog",
        [{"op": "note", "message": "n"}],
        render=meta.LegacyRender("same-status", DAY, "aw set", history=False),
    )
    assert p.read_text(encoding="utf-8") == BACKLOG.replace("bk0001", "bk0002")


def test_render_w16_approval_after_id_and_w17_backward_unsets(repo: Path) -> None:
    p = _write(
        repo,
        "plans/pending/20260101-pset-01-pl0001-p.ipd.md",
        PLAN.replace("- Status: draft", "- Status: reviewed"),
    )
    _append(
        repo,
        p,
        "plans",
        [
            {"op": "transition", "from": "reviewed", "to": "approved"},
            {
                "op": "set",
                "fields": {"approval": f"{DAY}, recorded via aw ipd set: go"},
            },
        ],
        render=meta.LegacyRender("approved", DAY, "aw set", history=False),
    )
    lines = p.read_text(encoding="utf-8").splitlines()
    assert (
        lines[lines.index("- Id: pl0001") + 1]
        == f"- Approval: {DAY}, recorded via aw ipd set: go"
    )
    p.write_text(
        p.read_text(encoding="utf-8").replace(
            "- Id: pl0001\n", "- Id: pl0001\n- Readiness: go\n"
        ),
        encoding="utf-8",
    )
    _append(
        repo,
        p,
        "plans",
        [
            {"op": "transition", "from": "approved", "to": "to-review"},
            {"op": "unset", "fields": ["approval"]},
            {"op": "unset", "fields": ["readiness"]},
        ],
        render=meta.LegacyRender("to-review", DAY, "aw set", history=False),
    )
    text = p.read_text(encoding="utf-8")
    assert "- Approval:" not in text and "- Readiness:" not in text
    assert "- Status: to-review\n" in text


def test_render_w18_history_heading_created_and_duplicate_suppressed(
    repo: Path,
) -> None:
    p = _write(
        repo,
        "plans/pending/20260101-h-01-nh0001-x.ipd.md",
        "# IPD: H\n\n- Status: draft\n- Id: nh0001\n\n## Goal\nG\n",
    )
    _append(repo, p, "plans", [{"op": "note", "message": "hello"}])
    assert p.read_text(encoding="utf-8") == (
        "# IPD: H\n\n- Status: draft\n- Id: nh0001\n\n## Workflow history\n"
        f"- {DAY} same-status (aw set): hello\n\n## Goal\nG\n"
    )
    before = p.read_bytes()
    _append(
        repo,
        p,
        "plans",
        [{"op": "note", "message": "hello"}],
        render=meta.LegacyRender("same-status", DAY, "aw set", history=False),
    )
    assert p.read_bytes() == before


def test_render_storage_format_dispatch_log_vs_legacy(
    repo: Path, tmp_path: Path
) -> None:
    records = tmp_path / "logrec"
    state = tmp_path / "logstate"
    records.mkdir()
    state.mkdir()
    ctx = type("Ctx", (), {"logical_roots": {"records": records, "state": state}})()
    meta.create(
        "lg0001",
        "ipd",
        {"status": "draft"},
        "# Body\n",
        destination="plans/pending/lg0001.ipd.md",
        project_context=ctx,
    )
    assert meta._storage_format(records, "lg0001") == "log"
    res = meta.append("lg0001", [{"op": "note", "message": "x"}], project_context=ctx)
    assert res["committed"] is True
    assert (
        len(
            (records / "meta" / "lg0001.jsonl").read_text(encoding="utf-8").splitlines()
        )
        == 2
    )
    assert meta._storage_format(records, "zz0001") == "legacy"
    p = _write(repo, "plans/pending/20260101-pset-01-pl0001-p.ipd.md", PLAN)
    out = _append(repo, p, "plans", [{"op": "note", "message": "y"}], id6="pl0001")
    assert isinstance(out, meta.WritePreview)
    assert not (repo / ".aw" / "records" / "meta").exists()


# --------------------------------------------------------------------------------------------------
# preview / fresh / pathkey
# --------------------------------------------------------------------------------------------------


def test_preview_dry_run_text_equals_written_bytes_and_writes_nothing(
    repo: Path,
) -> None:
    p = _write(repo, "plans/pending/20260101-pset-01-pl0001-p.ipd.md", PLAN)
    before = p.read_bytes()
    ev = [{"op": "transition", "from": "draft", "to": "to-review", "message": "m"}]
    prev = _append(repo, p, "plans", ev, tag="to-review", dry_run=True)
    assert p.read_bytes() == before
    assert prev.changed is True and prev.destination == p
    _append(repo, p, "plans", ev, tag="to-review")
    assert p.read_text(encoding="utf-8") == prev.text


def test_fresh_out_of_band_edit_refuses_naming_the_file(repo: Path) -> None:
    p = _write(repo, "plans/pending/20260101-pset-01-pl0001-p.ipd.md", PLAN)
    digest = meta._compute_digest(p)
    p.write_text(PLAN + "\nedited elsewhere\n", encoding="utf-8")
    before = p.read_bytes()
    with pytest.raises(ValueError, match=r"changed since it was read") as exc:
        meta.append(
            meta.LegacyTarget(p, "plans", "pl0001", source_digest=digest),
            [{"op": "note", "message": "m"}],
            legacy_render=meta.LegacyRender("same-status", DAY, "aw set"),
            repo_root=repo,
        )
    assert p.name in str(exc.value)
    assert p.read_bytes() == before


def test_pathkey_id_less_legacy_spec_is_written_by_path(repo: Path) -> None:
    p = _write(
        repo,
        "specs/draft/20260809-2211-01-legacy.spec.md",
        "# Spec: L\n\n- Status: draft\n\n## Workflow history\n- 2026-01-01 draft (a): c\n",
    )
    target = meta.LegacyTarget(p, "specs")
    assert target.key.startswith("path-")
    _append(repo, p, "specs", [{"op": "note", "message": "m"}], tag="draft")
    assert f"- {DAY} draft (aw set): m" in p.read_text(encoding="utf-8")


# --------------------------------------------------------------------------------------------------
# move / sidecar / order
# --------------------------------------------------------------------------------------------------


def _sidecar(root: Path) -> list:
    p = root / ".aw" / "records" / "history.jsonl"
    if not p.exists():
        return []
    return [
        json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()
    ]


def test_move_spec_is_git_mv_staged_with_rendered_bytes(repo: Path) -> None:
    src = _write(
        repo,
        "specs/draft/20260101-sp0001-01-sp0001-s.spec.md",
        "# Spec: S\n\n- Status: draft\n- Id: sp0001\n\n## Workflow history\n- 2026-01-01 draft (a): c\n",
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "i"], cwd=repo, check=True)
    dest = repo / ".aw/records/specs/to-review" / src.name
    prev = _append(
        repo,
        src,
        "specs",
        [{"op": "transition", "from": "draft", "to": "to-review", "message": "m"}],
        tag="to-review",
        id6="sp0001",
        destination=dest,
        sidecar=meta.SidecarRecord("specs", "aw specs", "aw specs", "to-review: m"),
    )
    assert not src.exists()
    assert dest.read_text(encoding="utf-8") == prev.text
    st = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True
    ).stdout
    assert any(
        ln.startswith("R") and "specs/to-review/" in ln for ln in st.splitlines()
    )
    assert [r["tree"] for r in _sidecar(repo)] == ["specs"]


def test_sidecar_backlog_writes_one_record_and_plan_writes_none(repo: Path) -> None:
    b = _write(repo, "backlog/open/20260101-b-01-bk0001-x.backlog.md", BACKLOG)
    _append(
        repo,
        b,
        "backlog",
        [{"op": "note", "message": "n"}],
        id6="bk0001",
        sidecar=meta.SidecarRecord("backlog", "aw backlog set", "aw backlog", "n"),
    )
    assert len(_sidecar(repo)) == 1
    p = _write(repo, "plans/pending/20260101-pset-01-pl0001-p.ipd.md", PLAN)
    _append(repo, p, "plans", [{"op": "note", "message": "n"}], id6="pl0001")
    assert len(_sidecar(repo)) == 1
    _append(
        repo,
        b,
        "backlog",
        [{"op": "note", "message": "dry"}],
        id6="bk0001",
        dry_run=True,
        sidecar=meta.SidecarRecord("backlog", "aw backlog set", "aw backlog", "dry"),
    )
    assert len(_sidecar(repo)) == 1


@pytest.mark.skipif(
    os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="needs POSIX permissions and a non-root user",
)
def test_order_read_only_destination_raises_with_source_and_sidecar_unchanged(
    repo: Path,
) -> None:
    src = _write(repo, "backlog/open/20260101-b-01-bk0001-x.backlog.md", BACKLOG)
    parked = repo / ".aw/records/backlog/parked"
    parked.mkdir(parents=True)
    before = src.read_bytes()
    os.chmod(parked, 0o500)
    try:
        with pytest.raises(OSError):
            _append(
                repo,
                src,
                "backlog",
                [{"op": "transition", "from": "open", "to": "parked", "message": "m"}],
                tag="parked",
                id6="bk0001",
                destination=parked / src.name,
                sidecar=meta.SidecarRecord(
                    "backlog", "aw backlog set", "aw backlog", "m"
                ),
            )
    finally:
        os.chmod(parked, 0o700)
    assert src.read_bytes() == before
    assert _sidecar(repo) == []


def test_order_content_write_failure_leaves_file_and_sidecar_unchanged(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = _write(repo, "backlog/open/20260101-b-01-bk0001-x.backlog.md", BACKLOG)
    before = p.read_bytes()

    def boom(path, text, **kw):
        raise OSError("injected write failure")

    monkeypatch.setattr(artifact_core, "atomic_write", boom)
    with pytest.raises(OSError, match="injected"):
        _append(
            repo,
            p,
            "backlog",
            [{"op": "note", "message": "n"}],
            id6="bk0001",
            sidecar=meta.SidecarRecord("backlog", "aw backlog set", "aw backlog", "n"),
        )
    assert p.read_bytes() == before
    assert _sidecar(repo) == []


# --------------------------------------------------------------------------------------------------
# owned / review_kind / refinement: AC-15 (1)-(5) and AC-14a (1)-(3)
# --------------------------------------------------------------------------------------------------


def _refused(repo: Path, path: Path, plural: str, events, match: str) -> str:
    before = path.read_bytes()
    with pytest.raises(ValueError, match=match) as exc:
        _append(repo, path, plural, events)
    assert path.read_bytes() == before
    return str(exc.value)


def test_owned_ac15_1_set_readiness_refused_alone_and_beside_a_review(
    repo: Path,
) -> None:
    p = _write(repo, "plans/pending/20260101-pset-01-pl0001-p.ipd.md", PLAN)
    reason = _refused(
        repo,
        p,
        "plans",
        [{"op": "set", "fields": {"readiness": "go"}}],
        "review-owned field 'readiness'",
    )
    print("set readiness refusal:", reason)
    _refused(
        repo,
        p,
        "plans",
        [
            {"op": "review", "round": 1, "review_kind": "gate", "verdict": "APPROVE"},
            {"op": "set", "fields": {"readiness": "go"}},
        ],
        "review-owned",
    )


def test_owned_ac15_2_gate_review_readiness_renders_the_bullet(repo: Path) -> None:
    p = _write(repo, "plans/pending/20260101-pset-01-pl0001-p.ipd.md", PLAN)
    _append(
        repo,
        p,
        "plans",
        [
            {
                "op": "review",
                "round": 1,
                "review_kind": "gate",
                "verdict": "APPROVE",
                "readiness": "go",
            },
        ],
        render=meta.LegacyRender("same-status", DAY, "aw set", history=False),
    )
    assert "- Readiness: go" in p.read_text(encoding="utf-8").splitlines()


def test_owned_ac15_3_set_coverage_refused_and_coverage_event_renders_three_bullets(
    repo: Path,
) -> None:
    p = _write(repo, "plans/pending/20260101-pset-01-pl0001-p.ipd.md", PLAN)
    _refused(
        repo,
        p,
        "plans",
        [{"op": "set", "fields": {"coverage": "pass"}}],
        "coverage-owned",
    )
    _append(
        repo,
        p,
        "plans",
        [
            {"op": "coverage", "coverage": "pass", "coverage_fingerprint": "abc123"},
        ],
        render=meta.LegacyRender("same-status", DAY, "model-x", history=False),
    )
    lines = p.read_text(encoding="utf-8").splitlines()
    i = lines.index("- Coverage: pass")
    assert lines[i + 1 : i + 3] == [
        "- Coverage-Fingerprint: abc123",
        f"- Coverage-Checked: {DAY} by model-x",
    ]


def test_owned_ac15_4_approval_owned_by_the_approved_transition(repo: Path) -> None:
    p = _write(
        repo,
        "plans/pending/20260101-pset-01-pl0001-p.ipd.md",
        PLAN.replace("- Status: draft", "- Status: reviewed"),
    )
    _refused(repo, p, "plans", [{"op": "set", "fields": {"approval": "x"}}], "approval")
    _append(
        repo,
        p,
        "plans",
        [
            {"op": "transition", "from": "reviewed", "to": "approved"},
            {
                "op": "set",
                "fields": {"approval": f"{DAY}, recorded via aw ipd set: go"},
            },
        ],
        render=meta.LegacyRender("approved", DAY, "aw set", history=False),
    )
    assert any(
        ln.startswith("- Approval:")
        for ln in p.read_text(encoding="utf-8").splitlines()
    )
    _refused(
        repo,
        p,
        "plans",
        [{"op": "transition", "from": "approved", "to": "reviewed"}],
        "approval must be unset",
    )


def test_owned_ac15_5_backward_transition_requires_unset_readiness(repo: Path) -> None:
    p = _write(
        repo,
        "plans/pending/20260101-pset-01-pl0001-p.ipd.md",
        PLAN.replace("- Status: draft", "- Status: reviewed"),
    )
    _refused(
        repo,
        p,
        "plans",
        [{"op": "transition", "from": "reviewed", "to": "draft"}],
        "readiness must be unset",
    )
    _append(
        repo,
        p,
        "plans",
        [
            {"op": "transition", "from": "reviewed", "to": "draft"},
            {"op": "unset", "fields": ["readiness"]},
        ],
        render=meta.LegacyRender("draft", DAY, "aw set", history=False),
    )
    assert "- Status: draft\n" in p.read_text(encoding="utf-8")


def test_review_kind_ac14a_1_gate_review_with_refinement_verdict_refused(
    repo: Path,
) -> None:
    p = _write(
        repo,
        "specs/draft/20260101-sp0001-01-sp0001-s.spec.md",
        "# Spec: S\n\n- Status: draft\n- Id: sp0001\n",
    )
    _refused(
        repo,
        p,
        "specs",
        [
            {
                "op": "review",
                "round": 1,
                "review_kind": "gate",
                "verdict": "REVIEWED - MATERIAL CHANGES APPLIED",
            }
        ],
        "invalid gate verdict",
    )


def test_review_kind_ac14a_2_refinement_review_with_readiness_refused(
    repo: Path,
) -> None:
    p = _write(
        repo,
        "specs/draft/20260101-sp0001-01-sp0001-s.spec.md",
        "# Spec: S\n\n- Status: draft\n- Id: sp0001\n",
    )
    _refused(
        repo,
        p,
        "specs",
        [{"op": "review", "round": 1, "review_kind": "refinement", "readiness": "go"}],
        "refinement review must not carry 'readiness'",
    )


def test_refinement_ac14a_3_rounds_appended_in_turn_keep_seq_order(
    tmp_path: Path,
) -> None:
    records = tmp_path / "rec"
    state = tmp_path / "st"
    records.mkdir()
    state.mkdir()
    ctx = type("Ctx", (), {"logical_roots": {"records": records, "state": state}})()
    meta.create(
        "rr0001",
        "spec",
        {"status": "draft"},
        "# S\n",
        destination="specs/draft/rr0001.spec.md",
        project_context=ctx,
    )
    for n in (1, 2, 3):
        meta.append(
            "rr0001",
            [
                {
                    "op": "review",
                    "round": n,
                    "review_kind": "refinement",
                    "verdict": "REVIEWED - MATERIAL CHANGES APPLIED",
                }
            ],
            project_context=ctx,
        )
    lines = (
        (records / "meta" / "rr0001.jsonl")
        .read_text(encoding="utf-8")
        .splitlines(keepends=True)
    )
    _state, _fc, _ap, proj = meta.replay("rr0001", "spec", lines)
    rounds = [(r["seq"], r["round"]) for r in proj["reviews"]]
    assert rounds == [(2, 1), (3, 2), (4, 3)]


def test_owned_message_with_home_path_is_refused_by_the_writer(repo: Path) -> None:
    p = _write(repo, "plans/pending/20260101-pset-01-pl0001-p.ipd.md", PLAN)
    home = "/" + "home" + "/someone/a.md"
    reason = _refused(
        repo, p, "plans", [{"op": "note", "message": f"see {home}"}], "message"
    )
    print("home path refusal:", reason)

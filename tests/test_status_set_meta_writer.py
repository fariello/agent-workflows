"""Byte pins for the status setter's write paths that no older test checks (plan 2xwb9b E-02, E-14).

Plan `2xwb9b` moves every write of the `status_set` engine onto `artifact_meta.append`'s legacy
branch. These tests were written and run against the UNCHANGED setter first, so each expected
literal is today's exact output; after the move they can only fail if the bytes change.

Every case drives `cli.main` in a fresh `tmp_path` git repository and compares the whole file with
an expected literal. The history day is pinned by patching `artifact_core.utc_history_date`.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
from pathlib import Path

import pytest

from agent_workflows import artifact_core, cli
from tests.record_builder import RecordBuilder, assert_field

pytestmark = pytest.mark.core

DAY = "2030-01-02"


@pytest.fixture()
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(artifact_core, "utc_history_date", lambda *a, **k: DAY)
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "pin@example.invalid"], cwd=root)
    subprocess.run(["git", "config", "user.name", "Pinner"], cwd=root)
    for sub in (
        "plans/pending",
        "specs/draft",
        "backlog/open",
        "backlog/blocked",
        "prompts/pending",
        "research",
    ):
        (root / ".aw" / "records" / sub).mkdir(parents=True)
    return root


def _run(root: Path, argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli.main(argv + ["--dir", str(root)])
    return rc, buf.getvalue()


def _rec(root: Path, rel: str, text: str) -> Path:
    p = root / ".aw" / "records" / rel
    p.write_text(text, encoding="utf-8")
    return p


def test_w04_plan_without_status_gets_one_after_the_title(repo: Path) -> None:
    """W-04: a plan with no `- Status:` gets one inserted after the FIRST `# `/`- Date:` line.

    The first matching line is the `# ` title, so the bullet lands directly under it."""
    p = _rec(
        repo,
        "plans/pending/20260101-nost-01-ns0001-x.ipd.md",
        "# IPD: X\n\n- Date: 2026-01-01\n- Kind: child\n- Set: nost\n- Id: ns0001\n\n"
        "## Workflow history\n- 2026-01-01 draft (a): c\n\n## Goal\nG\n",
    )
    rc, _ = _run(repo, ["set", "to-review", "ns0001", "--yes", "--no-commit"])
    assert rc == 0
    assert p.read_text(encoding="utf-8") == (
        "# IPD: X\n- Status: to-review\n\n- Date: 2026-01-01\n- Kind: child\n- Set: nost\n"
        "- Id: ns0001\n\n## Workflow history\n"
        f"- {DAY} to-review (aw set): status set to to-review\n"
        "- 2026-01-01 draft (a): c\n\n## Goal\nG\n"
    )


def test_w04_research_without_status_inserts_after_kind(
    repo: Path,
) -> None:
    """W-04 (YAML form) inserts missing `status:` after `kind:` (9gy5jk D-6) and creates `## Workflow history` at EOF."""
    p = _rec(
        repo,
        "research/20260101-rset-01-rs0001-x.research-report.md",
        "---\nid: rs0001\nkind: research-report\nset: rset\n---\n\n# Research: X\n\nBody\n",
    )
    rc, _ = _run(repo, ["set", "todo", "rs0001", "--yes", "--no-commit"])
    assert rc == 0
    assert p.read_text(encoding="utf-8") == (
        "---\nid: rs0001\nkind: research-report\nstatus: todo\nset: rset\n---\n\n"
        "# Research: X\n\nBody\n## Workflow history\n"
        f"- {DAY} todo (aw set): status set to todo\n"
    )


def test_w14_backlog_single_kind_line_becomes_work_kind(repo: Path) -> None:
    """W-14 single-line case: only `- Kind: chore` is present, so it is rewritten in place."""
    p = _rec(
        repo,
        "backlog/open/20260101-bk-01-bk0001-x.backlog.md",
        "- Id: bk0001\n- Status: open\n- Priority: low\n- Kind: chore\n- Summary: x\n\n"
        "## Workflow history\n- 2026-01-01 created (a): c\n",
    )
    rc, _ = _run(
        repo,
        [
            "backlog",
            "set",
            "open",
            "bk0001",
            "--message",
            "note one",
            "--yes",
            "--no-commit",
        ],
    )
    assert rc == 0
    expected = (
        "- Id: bk0001\n- Status: open\n- Priority: low\n- Work-Kind: chore\n- Summary: x\n\n"
        "## Workflow history\n"
        f"- {DAY} same-status (aw set): note one\n"
        "- 2026-01-01 created (a): c\n"
    )
    assert p.read_text(encoding="utf-8") == expected
    assert "- Kind:" not in p.read_text(encoding="utf-8")


def test_w05_gate_bullets_land_after_status_in_kind_ref_summary_order(
    repo: Path,
) -> None:
    _rec(
        repo,
        "backlog/open/20260101-bk-01-bk0002-x.backlog.md",
        "- Id: bk0002\n- Status: open\n- Priority: low\n- Work-Kind: chore\n- Summary: x\n\n"
        "## Workflow history\n- 2026-01-01 created (a): c\n",
    )
    rc, _ = _run(
        repo,
        [
            "set",
            "blocked",
            "bk0002",
            "--gate-kind",
            "decision",
            "--gate-ref",
            "D7",
            "--gate-summary",
            "waiting on D7",
            "--yes",
            "--no-commit",
        ],
    )
    assert rc == 0
    dest = repo / ".aw/records/backlog/blocked/20260101-bk-01-bk0002-x.backlog.md"
    assert dest.read_text(encoding="utf-8") == (
        "- Id: bk0002\n- Status: blocked\n- Gate-Kind: decision\n- Gate-Ref: D7\n"
        "- Gate-Summary: waiting on D7\n- Priority: low\n- Work-Kind: chore\n- Summary: x\n\n"
        "## Workflow history\n"
        f"- {DAY} blocked (aw set): status set to blocked\n"
        "- 2026-01-01 created (a): c\n"
    )


def test_w16_approval_lands_directly_after_id(repo: Path) -> None:
    p = _rec(
        repo,
        "plans/pending/20260101-apx-01-ap0001-x.ipd.md",
        "# IPD: A\n\n- Date: 2026-01-01\n- Status: reviewed\n- Readiness: go-pending-approval\n- Work-Kind: chore\n"
        "- Priority: low\n- Set: apx\n- Id: ap0001\n- Author: t\n\n"
        "## Workflow history\n- 2026-01-01 reviewed (a): c\n\n## Goal\nG\n",
    )
    rc, _ = _run(
        repo, ["set", "approved", "ap0001", "-m", "go", "--yes", "--no-commit"]
    )
    assert rc == 0
    assert p.read_text(encoding="utf-8") == (
        "# IPD: A\n\n- Date: 2026-01-01\n- Status: approved\n- Readiness: go-pending-approval\n- Work-Kind: chore\n"
        "- Priority: low\n- Set: apx\n- Id: ap0001\n"
        f"- Approval: {DAY}, recorded via aw ipd set: go\n- Author: t\n\n"
        "## Workflow history\n"
        f"- {DAY} approved (aw set): go\n"
        "- 2026-01-01 reviewed (a): c\n\n## Goal\nG\n"
    )


def test_w18_history_heading_created_before_first_h2_for_a_plan_and_at_end_for_a_prompt(
    repo: Path,
) -> None:
    plan = _rec(
        repo,
        "plans/pending/20260101-noh-01-nh0001-x.ipd.md",
        "# IPD: H\n\n- Date: 2026-01-01\n- Status: draft\n- Set: noh\n- Id: nh0001\n\n"
        "## Goal\nG\n",
    )
    rc, _ = _run(repo, ["set", "to-review", "nh0001", "--yes", "--no-commit"])
    assert rc == 0
    assert plan.read_text(encoding="utf-8") == (
        "# IPD: H\n\n- Date: 2026-01-01\n- Status: to-review\n- Set: noh\n- Id: nh0001\n\n"
        "## Workflow history\n"
        f"- {DAY} to-review (aw set): status set to to-review\n\n## Goal\nG\n"
    )

    prompt = _rec(
        repo,
        "prompts/pending/20260101-pq-01-pq0001-x.prompt.md",
        "# Prompt: P\n\n- Status: pending\n- Set: pq\n- Id: pq0001\n\nBody text\n",
    )
    rc, out = _run(
        repo,
        [
            "prompts",
            "set",
            "pending",
            "pq0001",
            "--message",
            "hello",
            "--yes",
            "--no-commit",
        ],
    )
    assert rc == 0
    assert "has no metadata comment" in out
    assert prompt.read_text(encoding="utf-8") == (
        "# Prompt: P\n\n- Status: pending\n- Set: pq\n- Id: pq0001\n\nBody text\n"
        "## Workflow history\n"
        f"- {DAY} same-status (aw set): hello\n"
    )


def test_w09_from_spec_unknown_id_refuses_and_leaves_bytes(repo: Path) -> None:
    _rec(
        repo,
        "specs/draft/20260101-sp0001-01-sp0001-x.spec.md",
        RecordBuilder().spec(
            title="S",
            when="2026-01-01",
            status="draft",
            id6="sp0001",
            history=["- 2026-01-01 draft (a): c"],
            text_only=True,
        ),
    )
    plan = _rec(
        repo,
        "plans/pending/20260101-fs-01-fs0001-x.ipd.md",
        RecordBuilder().plan(
            title="F",
            when="2026-01-01",
            status="draft",
            set="fs",
            id6="fs0001",
            history=["- 2026-01-01 draft (a): c"],
            text_only=True,
        ),
    )
    before = plan.read_bytes()
    rc, out = _run(
        repo,
        [
            "ipd",
            "set",
            "to-review",
            "fs0001",
            "--from-spec",
            "zzzzzz",
            "--yes",
            "--no-commit",
        ],
    )
    assert rc != 0
    assert "zzzzzz" in out
    assert plan.read_bytes() == before


# --------------------------------------------------------------------------------------------------
# E-14: the same setter call gives the same bytes and stdout whatever state the cache is in (AC-1a).
# --------------------------------------------------------------------------------------------------

_CACHE_PLAN = RecordBuilder().plan(
    title="C",
    when="2026-01-01",
    status="reviewed",
    readiness="go-pending-approval",
    work_kind="chore",
    priority="low",
    set="cch",
    id6="cc0001",
    history=["- 2026-01-01 reviewed (a): c"],
    body="## Goal\nG",
    text_only=True,
)


def _cache_fixture(base: Path, name: str) -> Path:
    root = base / name
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    d = root / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True)
    (d / "20260101-cch-01-cc0001-c.ipd.md").write_text(_CACHE_PLAN, encoding="utf-8")
    return root


def _prime_cache(root: Path) -> Path:
    from agent_workflows import artifact_meta

    ctx = artifact_meta.legacy_context(root)
    artifact_meta.query(project_context=ctx)
    db = Path(ctx.logical_roots["state"]) / "index.db"
    assert db.is_file()
    return db


@pytest.mark.parametrize("cache_state", ["cold", "warm", "deleted", "corrupt"])
def test_cache_state_does_not_change_setter_bytes_or_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cache_state: str
) -> None:
    monkeypatch.setattr(artifact_core, "utc_history_date", lambda *a, **k: DAY)
    reference = _cache_fixture(tmp_path, "reference")
    rc_ref, out_ref = _run(
        reference, ["set", "approved", "cc0001", "--yes", "--no-commit"]
    )
    ref_bytes = (
        reference / ".aw/records/plans/pending/20260101-cch-01-cc0001-c.ipd.md"
    ).read_bytes()

    root = _cache_fixture(tmp_path, cache_state)
    if cache_state != "cold":
        db = _prime_cache(root)
        if cache_state == "deleted":
            db.unlink()
        elif cache_state == "corrupt":
            db.write_bytes(os.urandom(4096))
    rc, out = _run(root, ["set", "approved", "cc0001", "--yes", "--no-commit"])
    got_path = root / ".aw/records/plans/pending/20260101-cch-01-cc0001-c.ipd.md"
    got = got_path.read_bytes()
    assert rc == rc_ref == 0
    assert out == out_ref
    assert got == ref_bytes
    assert_field(got_path, "status", "approved")

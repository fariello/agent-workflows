"""Phase-B merge-independence tests for moved metadata writers (spec `4sd62s` AC-3, IPD `b4y4ee`).

Drives the real CLI writers in isolated `tmp_path` git repositories across two branches:
1. Different-record edits (`aw backlog note` + `aw describe` on branch A; `aw specs note` +
   `aw ipd recheck-readiness` on branch B) merge with exit 0 and no conflict, and
   `artifact_meta.read` on all three records reflects both branches' changes.
2. Same-record edits (each branch prepends one `## Workflow history` line to the same
   record) conflict under `git merge`, pinning the phase-B limit removed at cutover (4.7).
"""

from __future__ import annotations

import contextlib
import io
import re
import subprocess
from pathlib import Path

import pytest

from agent_workflows import artifact_meta as meta
from agent_workflows import cli
from agent_workflows import review_findings as rf

pytestmark = pytest.mark.core

_ID_LINE_RE = re.compile(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$")


def _git(
    repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        capture_output=True,
        text=True,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "Tester")
    aw_dir = repo / ".aw"
    aw_dir.mkdir(parents=True, exist_ok=True)
    (aw_dir / ".gitignore").write_text(
        "/state/\nrecords/history.jsonl\n", encoding="utf-8"
    )
    for rel in (
        "records/backlog/open",
        "records/specs/draft",
        "records/plans/pending",
        "records/reviews",
    ):
        (aw_dir / rel).mkdir(parents=True, exist_ok=True)
    return repo


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:
            rc = int(exc.code or 0)
    return rc, out.getvalue(), err.getvalue()


def _commit_all(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


def _unmerged_files(repo: Path) -> list[str]:
    proc = _git(repo, "diff", "--name-only", "--diff-filter=U")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _extract_id6(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = _ID_LINE_RE.search(text)
    assert m is not None, f"missing - Id: bullet in {path}:\n{text}"
    return m.group(1)


def _write_plan_and_review(repo: Path, id6: str = "pl0001") -> Path:
    plan_path = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / f"20261109-demo-01-{id6}-sample.ipd.md"
    )
    plan_lines = [
        f"# IPD: Sample {id6}",
        "",
        "- Date: 2026-11-09",
        "- Kind: child",
        "- Scope-Paths: agent_workflows/a.py",
        "- Item-Dependencies: none",
        "- Status: reviewed",
        "- Readiness: no-go",
        "- Set: demo",
        "- Order: 1",
        "- Priority: medium",
        "- Work-Kind: feature",
        f"- Id: {id6}",
        "",
        "## Workflow history",
        "",
        "- 2026-09-09 reviewed (tester): /plan-review complete: REVIEWED - OPEN QUESTIONS; PR-001",
        "",
        "## Goal",
        "",
        "Sample goal.",
        "",
        "## Detailed Implementation Checklist (TODO)",
        "",
        "- [ ] E-01 Sample step",
        "  - Depends on: none",
        "  - Expected outcome: done",
        "  - Execution state: pending",
        "",
        "## Validation and cross-check (verify before reporting done)",
        "",
        "- [ ] V-01 validates E-01",
        "  - Required evidence: paste output",
        "  - Observed evidence:",
        "  - Result: pending",
        "",
    ]
    plan_path.write_text("\n".join(plan_lines), encoding="utf-8")
    rf.write_review(
        repo
        / ".aw"
        / "records"
        / "reviews"
        / f"20261109-demo-01-{id6}-sample.review.md",
        subject_id=id6,
        subject_type="ipd",
        reviewed_at="2026-11-09",
        reviewer="tester",
        verdict="REVIEWED - OPEN QUESTIONS",
        rounds=[
            rf.Round(
                1,
                (
                    rf.Finding(
                        "PR-001",
                        "high",
                        "IN-SCOPE",
                        "B. Security",
                        "a.py:1",
                        "resolved finding",
                        "Overall:Low",
                        "fixed",
                        "fixed in r2",
                    ),
                ),
                (),
            )
        ],
    )
    return plan_path


def test_different_record_merges_are_conflict_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path)
    monkeypatch.chdir(repo)

    rc, _out, err = _run_cli(
        [
            "backlog",
            "new",
            "--priority",
            "high",
            "--work-kind",
            "feature",
            "--summary",
            "Initial backlog item.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    rc, _out, err = _run_cli(
        [
            "specs",
            "new",
            "--title",
            "Sample spec",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    plan_path = _write_plan_and_review(repo, id6="pl0001")
    _commit_all(repo, "base records")

    bl_files = list((repo / ".aw" / "records" / "backlog").rglob("*.backlog.md"))
    sp_files = list((repo / ".aw" / "records" / "specs").rglob("*.spec.md"))
    assert len(bl_files) == 1
    assert len(sp_files) == 1
    bl_path = bl_files[0]
    sp_path = sp_files[0]
    bl_id6 = _extract_id6(bl_path)
    sp_id6 = _extract_id6(sp_path)

    # Branch A: annotate and describe backlog item X.
    _git(repo, "checkout", "-q", "-b", "branch-a", "main")
    rc, _out, err = _run_cli(
        [
            "backlog",
            "note",
            bl_id6,
            "--message",
            "branch A backlog note",
            "--date",
            "2030-01-05",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    rc, _out, err = _run_cli(
        [
            "describe",
            bl_id6,
            "--summary",
            "Branch A updated summary.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    _commit_all(repo, "branch A writes backlog note and describe")

    # Branch B: annotate spec Y and recheck-readiness on plan Z.
    _git(repo, "checkout", "-q", "-b", "branch-b", "main")
    rc, _out, err = _run_cli(
        [
            "specs",
            "note",
            str(sp_path),
            "--message",
            "branch B spec note",
            "--date",
            "2030-01-06",
        ]
    )
    assert rc == 0, err
    rc, _out, err = _run_cli(
        [
            "ipd",
            "recheck-readiness",
            "pl0001",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    _commit_all(repo, "branch B writes specs note and recheck-readiness")

    # Merge B into A and verify conflict-free outcome.
    _git(repo, "checkout", "-q", "branch-a")
    merge_proc = _git(repo, "merge", "--no-edit", "branch-b", check=False)
    unmerged = _unmerged_files(repo)
    print(
        f"[different-artifacts] git merge exit={merge_proc.returncode} unmerged={unmerged}"
    )
    assert merge_proc.returncode == 0, merge_proc.stderr + merge_proc.stdout
    assert unmerged == []
    for p in (bl_path, sp_path, plan_path):
        txt = p.read_text(encoding="utf-8")
        assert "<<<<<<<" not in txt
        assert ">>>>>>>" not in txt

    # artifact_meta.read on all three records reflects both branches' changes.
    ctx = meta.legacy_context(repo)

    bl_state = meta.read(bl_id6, project_context=ctx)
    assert bl_state.valid == 1 and bl_state.defect is None
    assert bl_state.short_description == "Branch A updated summary."
    assert bl_state.fields["short_description"] == "Branch A updated summary."
    assert bl_state.last_seq == 3
    bl_hist = [row.get("line", "") for row in meta.history(bl_id6, project_context=ctx)]
    assert any("branch A backlog note" in ln for ln in bl_hist)
    assert any(
        "short_description set: Branch A updated summary." in ln for ln in bl_hist
    )

    sp_state = meta.read(sp_id6, project_context=ctx)
    assert sp_state.valid == 1 and sp_state.defect is None
    assert sp_state.last_history_day == "2030-01-06"
    assert sp_state.last_seq == 2
    sp_hist = [row.get("line", "") for row in meta.history(sp_id6, project_context=ctx)]
    assert any("branch B spec note" in ln for ln in sp_hist)

    pl_state = meta.read("pl0001", project_context=ctx)
    assert pl_state.valid == 1 and pl_state.defect is None
    assert pl_state.fields["readiness"] == "go-pending-approval"
    assert pl_state.last_seq == 2
    pl_hist = [
        row.get("line", "") for row in meta.history("pl0001", project_context=ctx)
    ]
    assert any("readiness re-check" in ln for ln in pl_hist)


def test_same_record_history_prepends_conflict_in_phase_b(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path)
    monkeypatch.chdir(repo)

    rc, _out, err = _run_cli(
        [
            "backlog",
            "new",
            "--priority",
            "medium",
            "--work-kind",
            "chore",
            "--summary",
            "Shared record.",
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    _commit_all(repo, "base shared record")

    bl_files = list((repo / ".aw" / "records" / "backlog").rglob("*.backlog.md"))
    assert len(bl_files) == 1
    bl_path = bl_files[0]
    bl_id6 = _extract_id6(bl_path)
    rel_path = bl_path.relative_to(repo).as_posix()

    # Branch A prepends one history line directly under ## Workflow history.
    _git(repo, "checkout", "-q", "-b", "branch-a", "main")
    rc, _out, err = _run_cli(
        [
            "backlog",
            "note",
            bl_id6,
            "--message",
            "branch A history line",
            "--date",
            "2030-01-05",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    _commit_all(repo, "branch A note")

    # Branch B prepends a different history line directly under ## Workflow history.
    _git(repo, "checkout", "-q", "-b", "branch-b", "main")
    rc, _out, err = _run_cli(
        [
            "backlog",
            "note",
            bl_id6,
            "--message",
            "branch B history line",
            "--date",
            "2030-01-06",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0, err
    _commit_all(repo, "branch B note")

    # Merge B into A: phase-B limit conflicts on the shared file.
    _git(repo, "checkout", "-q", "branch-a")
    merge_proc = _git(repo, "merge", "--no-edit", "branch-b", check=False)
    unmerged = _unmerged_files(repo)
    print(f"[same-record] git merge exit={merge_proc.returncode} unmerged={unmerged}")
    assert merge_proc.returncode != 0
    assert rel_path in unmerged
    merged_text = bl_path.read_text(encoding="utf-8")
    assert "<<<<<<<" in merged_text and ">>>>>>>" in merged_text

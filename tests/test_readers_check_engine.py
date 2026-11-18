"""Behavioral pinning tests for check_engine release-gate, close, and From-Backlog readers (IPD i3b5zu E-01).

Pins observable behavior of `evaluate_blocking_close`, `check_live_bug_gate`,
`check_decision_ref_dangling` (with `_iter_live_gate_carriers`),
`check_release_gate_consistency` (working-tree half), `release_gate_warnings`,
`find_from_backlog_plans`, `find_from_backlog_specs`, and `_item_close_date` on `tmp_path`
fixture repositories before moving readers onto `artifact_meta`.
"""

from __future__ import annotations

import io
import json
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from agent_workflows import check_engine, cli

pytestmark = pytest.mark.core


def _init_git_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def _setup_repo(tmp_path: Path, *, cutover: str | None = None) -> Path:
    repo = tmp_path / "repo"
    recs = repo / ".aw" / "records"
    for sub in (
        "plans/pending",
        "plans/executed",
        "specs/approved",
        "specs/deferred",
        "specs/implemented",
        "backlog/open",
        "backlog/blocked",
        "backlog/graduated",
        "backlog/done",
        "releases",
    ):
        (recs / sub).mkdir(parents=True, exist_ok=True)
    cfg: dict[str, object] = {
        "schema_version": 1,
        "release_gate_work_kinds": ["bug"],
    }
    (repo / ".aw" / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    if cutover is not None:
        cfg_dir = repo / ".aw" / "config"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        (cfg_dir / "project.json").write_text(
            json.dumps({"cutovers": {"release_gate_at_rest": cutover}}),
            encoding="utf-8",
        )
    _write_release(repo, "rel001", status="planned")
    _init_git_repo(repo)
    return repo


def _write_release(repo: Path, id6: str, *, status: str = "planned") -> Path:
    p = repo / ".aw" / "records" / "releases" / f"20261001-{id6}-01-{id6}-v1.release.md"
    p.write_text(
        f"# Release v1\n\n- Id: {id6}\n- Status: {status}\n- Set: {id6}\n",
        encoding="utf-8",
    )
    return p


def _write_backlog(
    repo: Path,
    bucket: str,
    id6: str,
    *,
    status: str | None = None,
    work_kind: str = "bug",
    priority: str = "high",
    blocks_release: str | None = None,
    close_evidence: str | None = None,
    gate_kind: str | None = None,
    gate_ref: str | None = None,
    history_lines: tuple[str, ...] = ("- 2026-10-01 created (test): created",),
) -> Path:
    st = status or bucket
    lines = [
        f"- Id: {id6}",
        f"- Status: {st}",
        "- Set: tstset",
        f"- Priority: {priority}",
        f"- Work-Kind: {work_kind}",
        f"- Summary: Test item {id6}",
    ]
    if blocks_release is not None:
        lines.append(f"- Blocks-Release: {blocks_release}")
    if close_evidence is not None:
        lines.append(f"- Close-Evidence: {close_evidence}")
    if gate_kind is not None:
        lines.append(f"- Gate-Kind: {gate_kind}")
    if gate_ref is not None:
        lines.append(f"- Gate-Ref: {gate_ref}")
    lines.extend(["", "## Workflow history", *history_lines, ""])
    p = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / bucket
        / f"20261001-tstset-01-{id6}-item.backlog.md"
    )
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _write_plan(
    repo: Path,
    bucket: str,
    id6: str,
    *,
    status: str | None = None,
    from_backlog: str | None = None,
    blocks_release: str | None = None,
) -> Path:
    st = status or ("executed" if bucket == "executed" else "approved")
    lines = [
        f"# IPD: Plan {id6}",
        "",
        f"- Id: {id6}",
        f"- Status: {st}",
        "- Set: tstset",
        "- Order: 01",
    ]
    if from_backlog is not None:
        lines.append(f"- From-Backlog: {from_backlog}")
    if blocks_release is not None:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines.extend(["", "## Goal", "", "Test goal.", ""])
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / bucket
        / f"20261001-tstset-01-{id6}-plan.ipd.md"
    )
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _write_spec(
    repo: Path,
    bucket: str,
    id6: str,
    *,
    status: str | None = None,
    from_backlog: str | None = None,
    blocks_release: str | None = None,
    gate_kind: str | None = None,
    gate_ref: str | None = None,
) -> Path:
    st = status or bucket
    lines = [
        f"# Spec: {id6}",
        "",
        f"- Id: {id6}",
        f"- Status: {st}",
        f"- Set: {id6}",
    ]
    if from_backlog is not None:
        lines.append(f"- From-Backlog: {from_backlog}")
    if blocks_release is not None:
        lines.append(f"- Blocks-Release: {blocks_release}")
    if gate_kind is not None:
        lines.append(f"- Gate-Kind: {gate_kind}")
    if gate_ref is not None:
        lines.append(f"- Gate-Ref: {gate_ref}")
    lines.extend(["", "## Goal", "", "Spec goal.", ""])
    p = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / bucket
        / f"20261001-{id6}-01-{id6}-spec.spec.md"
    )
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _run_cli(repo: Path, *args: str) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cli.main([*args, "--dir", str(repo)])
    return rc, out.getvalue(), err.getvalue()


class TestCheckEngineReleaseGateReadersOrder31:
    """Pins the release-gate, close, and From-Backlog readers in check_engine."""

    def test_evaluate_blocking_close_handoff(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        item_p = _write_backlog(repo, "graduated", "bkl001", blocks_release="next")
        plan_p = _write_plan(
            repo,
            "pending",
            "pln001",
            status="approved",
            from_backlog="bkl001",
            blocks_release="next",
        )

        refused = check_engine.evaluate_blocking_close(repo, item_p, "done")
        assert refused.legitimate is False
        assert refused.severity == "error"

        exec_p = repo / ".aw" / "records" / "plans" / "executed" / plan_p.name
        plan_p.rename(exec_p)
        exec_p.write_text(
            exec_p.read_text(encoding="utf-8").replace(
                "- Status: approved", "- Status: executed"
            ),
            encoding="utf-8",
        )

        allowed = check_engine.evaluate_blocking_close(repo, item_p, "done")
        assert allowed.legitimate is True
        assert allowed.path == "HANDOFF"

        rc, out, _ = _run_cli(repo, "check", "release-gates", "--agent")
        assert rc == 0
        payload = json.loads(out)
        assert payload["findings"] == 0

    def test_evaluate_blocking_close_satisfied(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        unshipped_spec = _write_spec(repo, "approved", "spc001")
        shipped_spec = _write_spec(repo, "implemented", "spc002")
        rel_unshipped = unshipped_spec.relative_to(repo).as_posix()
        rel_shipped = shipped_spec.relative_to(repo).as_posix()

        item_p = _write_backlog(
            repo,
            "done",
            "bkl002",
            blocks_release="next",
            close_evidence=rel_shipped,
        )
        assert check_engine._evidence_spec_unshipped(repo, rel_unshipped) is True
        assert check_engine._evidence_spec_unshipped(repo, rel_shipped) is False

        v_bad = check_engine.evaluate_blocking_close(
            repo, item_p, "done", evidence=rel_unshipped
        )
        assert v_bad.legitimate is False

        v_ok = check_engine.evaluate_blocking_close(repo, item_p, "done")
        assert v_ok.legitimate is True
        assert v_ok.path == "SATISFIED"

        rc, out, _ = _run_cli(repo, "check", "release-gates", "--agent")
        assert rc == 0
        assert json.loads(out)["findings"] == 0

    def test_evaluate_blocking_close_degated(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        item_p = _write_backlog(repo, "open", "bkl003", blocks_release="next")

        v_blocked = check_engine.evaluate_blocking_close(repo, item_p, "done")
        assert v_blocked.legitimate is False

        degated_text = item_p.read_text(encoding="utf-8").replace(
            "- Blocks-Release: next\n", ""
        )
        v_degated = check_engine.evaluate_blocking_close(
            repo, item_p, "done", item_text=degated_text
        )
        assert v_degated.legitimate is True
        assert v_degated.path == "DE-GATED"

        rc, _, _ = _run_cli(
            repo,
            "backlog",
            "set",
            "done",
            "bkl003",
            "--blocks-release",
            "-",
            "--yes",
            "--no-commit",
        )
        assert rc == 0
        rc_chk, out_chk, _ = _run_cli(repo, "check", "release-gates", "--agent")
        assert rc_chk == 0
        assert json.loads(out_chk)["findings"] == 0

    def test_check_live_bug_gate(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        _write_backlog(repo, "open", "bug001", work_kind="bug")
        _write_backlog(repo, "open", "bug002", work_kind="bug", blocks_release="next")
        _write_backlog(repo, "graduated", "bug003", work_kind="bug")
        _write_plan(
            repo,
            "pending",
            "pln003",
            from_backlog="bug003",
            blocks_release="next",
        )

        rc, out, _ = _run_cli(repo, "check", "release-gates", "--agent")
        assert rc != 0
        rules = [
            d["rule"]
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.live-bug-ungated"
        ]
        assert rules == ["check.live-bug-ungated"]
        assert "bug001" in out
        assert "bug002" not in out
        assert "bug003" not in out

    def test_check_decision_ref_dangling(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        (repo / "DECISIONS.md").write_text(
            "### D10. Existing ruling\n", encoding="utf-8"
        )
        _write_backlog(
            repo,
            "blocked",
            "bkl010",
            work_kind="chore",
            gate_kind="decision",
            gate_ref="D999",
        )
        _write_spec(
            repo,
            "deferred",
            "spc010",
            gate_kind="decision",
            gate_ref="D10",
        )
        _write_backlog(
            repo,
            "blocked",
            "bkl011",
            work_kind="chore",
            gate_kind="artifact",
            gate_ref=".aw/records/releases/20261001-rel001-01-rel001-v1.release.md",
        )
        _write_spec(
            repo,
            "deferred",
            "spc011",
            gate_kind="todo",
            gate_ref="T-42",
        )

        carriers = list(check_engine._iter_live_gate_carriers(repo))
        assert {(p.name, k, r) for p, k, r in carriers} == {
            (
                "20261001-tstset-01-bkl011-item.backlog.md",
                "artifact",
                ".aw/records/releases/20261001-rel001-01-rel001-v1.release.md",
            ),
            ("20261001-spc011-01-spc011-spec.spec.md", "todo", "T-42"),
        }

        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert rc != 0
        dangling = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.decision-ref-dangling"
        ]
        assert len(dangling) == 1
        assert "bkl010" in dangling[0]["location"]

    def test_check_release_gate_consistency_working_tree(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path, cutover="2026-10-10")
        _write_release(repo, "rel999", status="planned")
        _write_backlog(repo, "graduated", "bkl020", blocks_release="rel001")
        _write_plan(
            repo,
            "pending",
            "pln020",
            from_backlog="bkl020",
            blocks_release="rel999",
        )
        # Executed carrier with mismatched gate must be skipped (D-3)
        _write_plan(
            repo,
            "executed",
            "pln021",
            from_backlog="bkl020",
            blocks_release="rel999",
        )
        # Done blocking item closed after cutover without handoff/evidence
        _write_backlog(
            repo,
            "done",
            "bkl022",
            blocks_release="rel001",
            history_lines=("- 2026-10-15 done (test): hand closed",),
        )

        rc, out, _ = _run_cli(repo, "check", "release-gates", "--agent")
        assert rc != 0
        diags = json.loads(out)["diagnostics"]
        rules = sorted(d["rule"] for d in diags)
        assert rules == [
            "check.blocking-item-closed-without-gate",
            "check.from-backlog-gate-mismatch",
        ]
        mismatch = [d for d in diags if d["rule"] == "check.from-backlog-gate-mismatch"]
        assert "pln020" in mismatch[0]["location"]

    def test_release_gate_warnings(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        _write_backlog(repo, "open", "bkl030", blocks_release="next")
        _write_plan(
            repo,
            "pending",
            "pln030",
            from_backlog="bkl030",
            blocks_release="next",
        )
        _write_backlog(repo, "open", "bkl031", blocks_release="next")
        _write_plan(
            repo,
            "executed",
            "pln031",
            from_backlog="bkl031",
            blocks_release="next",
        )

        warns = check_engine.release_gate_warnings(repo)
        assert len(warns) == 2
        by_loc = {Path(w.location).name: w for w in warns}
        assert (
            "aw backlog set bkl030 --status graduated"
            in by_loc["20261001-tstset-01-bkl030-item.backlog.md"].detail
        )
        assert (
            "aw backlog set bkl031 --status done"
            in by_loc["20261001-tstset-01-bkl031-item.backlog.md"].detail
        )
        rc, out, _ = _run_cli(repo, "check", "release-gates", "--agent")
        assert rc == 0
        assert json.loads(out)["findings"] == 0

    def test_find_from_backlog_plans(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        p1 = _write_plan(
            repo,
            "pending",
            "pln040",
            from_backlog="bkl040",
            blocks_release="next",
        )
        p2 = _write_plan(repo, "executed", "pln041", from_backlog="bkl040")
        _write_plan(
            repo,
            "pending",
            "pln042",
            from_backlog="other1",
            blocks_release="next",
        )

        assert (
            check_engine._from_backlog_value(p1.read_text(encoding="utf-8")) == "bkl040"
        )
        assert check_engine._from_backlog_value("- From-Backlog: NONE\n") is None

        hits = check_engine.find_from_backlog_plans(repo, "bkl040")
        assert sorted((p.name, br) for p, br in hits) == sorted(
            [(p1.name, "next"), (p2.name, "")]
        )

        _write_backlog(repo, "graduated", "bkl040", blocks_release="next")
        _write_backlog(repo, "done", "other1")
        rc, out, _ = _run_cli(repo, "check", "release-gates", "--agent")
        assert rc == 0
        assert json.loads(out)["findings"] == 0

    def test_find_from_backlog_specs(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        s1 = _write_spec(
            repo,
            "approved",
            "spc050",
            from_backlog="bkl050",
            blocks_release="next",
        )
        s2 = _write_spec(repo, "implemented", "spc051", from_backlog="bkl051")

        assert check_engine._carrier_is_executed(s1) is False
        assert check_engine._carrier_is_executed(s2) is True

        assert [
            (p.name, br)
            for p, br in check_engine.find_from_backlog_specs(repo, "bkl050")
        ] == [(s1.name, "next")]
        assert [
            (p.name, br)
            for p, br in check_engine.find_from_backlog_specs(repo, "bkl051")
        ] == [(s2.name, "")]

        _write_backlog(repo, "graduated", "bkl050", blocks_release="next")
        _write_backlog(repo, "done", "bkl051")
        rc, out, _ = _run_cli(repo, "check", "release-gates", "--agent")
        assert rc == 0
        assert json.loads(out)["findings"] == 0

    def test_item_close_date(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path, cutover="2026-10-11")
        post_p = _write_backlog(
            repo,
            "done",
            "bkl060",
            blocks_release="next",
            history_lines=(
                "- 2026-10-12 done (test): closed",
                "- 2026-10-09 created (test): created",
            ),
        )
        pre_p = _write_backlog(
            repo,
            "done",
            "bkl061",
            blocks_release="next",
            history_lines=(
                "- 2026-10-05 done (test): closed earlier",
                "- 2026-10-01 created (test): created",
            ),
        )

        assert (
            check_engine._item_close_date(post_p.read_text(encoding="utf-8"))
            == "20261012"
        )
        assert (
            check_engine._item_close_date(pre_p.read_text(encoding="utf-8"))
            == "20261005"
        )

        rc, out, _ = _run_cli(repo, "check", "release-gates", "--agent")
        assert rc != 0
        locs = [
            Path(d["location"]).name
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.blocking-item-closed-without-gate"
        ]
        assert locs == [post_p.name]

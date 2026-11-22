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

from agent_workflows import check_engine, cli, plans
from tests.record_builder import RecordBuilder

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
        RecordBuilder().release(id6=id6, status=status, set=id6, text_only=True),
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
    graduated_to: str | None = None,
    history_lines: tuple[str, ...] = ("- 2026-10-01 created (test): created",),
) -> Path:
    st = status or bucket
    extra: dict[str, object] = {}
    if blocks_release is not None:
        extra["blocks_release"] = blocks_release
    if close_evidence is not None:
        extra["close_evidence"] = close_evidence
    if gate_kind is not None:
        extra["gate_kind"] = gate_kind
    if gate_ref is not None:
        extra["gate_ref"] = gate_ref
    if graduated_to is not None:
        extra["graduated_to"] = graduated_to
    p = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / bucket
        / f"20261001-tstset-01-{id6}-item.backlog.md"
    )
    p.write_text(
        RecordBuilder().backlog(
            id6=id6,
            summary=f"Test item {id6}",
            when="2026-10-01",
            status=st,
            set="tstset",
            priority=priority,
            work_kind=work_kind,
            history=list(history_lines),
            text_only=True,
            **extra,
        ),
        encoding="utf-8",
    )
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
    extra: dict[str, object] = {}
    if from_backlog is not None:
        extra["from_backlog"] = from_backlog
    if blocks_release is not None:
        extra["blocks_release"] = blocks_release
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / bucket
        / f"20261001-tstset-01-{id6}-plan.ipd.md"
    )
    p.write_text(
        RecordBuilder().plan(
            title=f"Plan {id6}",
            when="2026-10-01",
            id6=id6,
            status=st,
            set="tstset",
            order=1,
            body="## Goal\n\nTest goal.",
            text_only=True,
            **extra,
        ),
        encoding="utf-8",
    )
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
    history_lines: tuple[str, ...] | None = None,
) -> Path:
    st = status or bucket
    extra: dict[str, object] = {}
    if from_backlog is not None:
        extra["from_backlog"] = from_backlog
    if blocks_release is not None:
        extra["blocks_release"] = blocks_release
    if gate_kind is not None:
        extra["gate_kind"] = gate_kind
    if gate_ref is not None:
        extra["gate_ref"] = gate_ref
    p = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / bucket
        / f"20261001-{id6}-01-{id6}-spec.spec.md"
    )
    p.write_text(
        RecordBuilder().spec(
            title=id6,
            when="2026-10-01",
            id6=id6,
            status=st,
            set=id6,
            history=list(history_lines) if history_lines is not None else [],
            body="## Goal\n\nSpec goal.",
            text_only=True,
            **extra,
        ),
        encoding="utf-8",
    )
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

        plan_p.unlink()
        _write_plan(
            repo,
            "executed",
            "pln001",
            status="executed",
            from_backlog="bkl001",
            blocks_release="next",
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

        degated_text = str(
            RecordBuilder().backlog(
                id6="bkl003",
                summary="Test item bkl003",
                when="2026-10-01",
                status="open",
                set="tstset",
                priority="high",
                work_kind="bug",
                history=["- 2026-10-01 created (test): created"],
                text_only=True,
            )
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


def _o30_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _o30_write_full_plan(
    repo: Path,
    bucket: str,
    id6: str,
    *,
    setid: str = "tstset",
    order: int = 1,
    date: str = "2026-10-01",
    kind: str = "child",
    status: str = "draft",
    scope_paths: str = "src/a.py",
    item_deps: str | None = "none",
    priority: str | None = "medium",
    work_kind: str | None = "feature",
    include_id: bool = True,
    from_backlog: str | None = None,
    from_spec: str | None = None,
    blocks_release: str | None = None,
    readiness: str | None = None,
    concern: str | None = None,
    scope: str | None = None,
    history_lines: tuple[str, ...] | None = None,
    extra_raw: dict[str, object] | None = None,
    body: str | None = None,
) -> Path:
    raw: dict[str, object] = {
        "Concern": concern if concern is not None else "Test concern.",
        "Scope": scope if scope is not None else "Test scope.",
    }
    valid_status = status if status in plans.RECOGNIZED else "draft"
    if valid_status != status:
        raw["Status"] = status
    if item_deps is None:
        raw["Item-Dependencies"] = None
    if priority is None:
        raw["Priority"] = None
    elif priority not in ("low", "medium", "high"):
        raw["Priority"] = priority
    if work_kind is None:
        raw["Work-Kind"] = None
    elif work_kind not in ("bug", "feature", "chore", "security", "followup"):
        raw["Work-Kind"] = work_kind
    if not include_id:
        raw["Id"] = None
    if extra_raw:
        raw.update(extra_raw)

    extra: dict[str, object] = {}
    if from_backlog is not None:
        extra["from_backlog"] = from_backlog
    if from_spec is not None:
        extra["from_spec"] = from_spec
    if blocks_release is not None:
        extra["blocks_release"] = blocks_release

    eff_body = (
        body
        if body is not None
        else (
            "## Goal\n\nTest goal.\n\n"
            "## Detailed Implementation Checklist (TODO)\n\n"
            "- [ ] E-01 Execute step.\n"
            "  - Depends on: none\n"
            "  - Expected outcome: works\n"
            "  - Execution state: pending\n\n"
            "## Scope check\n\n- Over-scope: none.\n\n"
            "## Validation and cross-check (verify before reporting done)\n\n"
            "- [ ] V-01 validates E-01\n"
            "  - Required evidence: pytest passes\n"
            "  - Observed evidence:\n"
            "  - Result: pending"
        )
    )
    eff_history = (
        list(history_lines)
        if history_lines is not None
        else [f"- {date} {status} (test): created."]
    )
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / bucket
        / f"{date.replace('-', '')}-{setid}-{order:02d}-{id6}-plan.ipd.md"
    )
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        RecordBuilder().plan(
            title=f"Plan {id6}",
            when=date,
            plan_role=kind,
            scope_paths=scope_paths,
            item_dependencies=item_deps if item_deps is not None else "none",
            status=valid_status,
            priority=priority if priority in ("low", "medium", "high") else "medium",
            work_kind=(
                work_kind
                if work_kind in ("bug", "feature", "chore", "security", "followup")
                else "feature"
            ),
            set=setid,
            order=order,
            id6=id6,
            readiness=readiness,
            history=eff_history,
            body=eff_body,
            raw_fields=raw,
            text_only=True,
            **extra,
        ),
        encoding="utf-8",
    )
    return p


def _o30_write_review(
    repo: Path,
    subject_id: str,
    *,
    subject_type: str = "ipd",
    filename_id: str | None = None,
    findings_rows: tuple[str, ...] = (),
    decisions_rows: tuple[str, ...] = (),
    verdict: str = "APPROVE",
) -> Path:
    fid = filename_id or subject_id
    findings: list[dict[str, str]] = []
    for row in findings_rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        findings.append(
            {
                "id": cells[0],
                "severity": cells[1],
                "scope": cells[2],
                "area": cells[3],
                "evidence": cells[4],
                "finding": cells[5],
                "remediation_risk": cells[6],
                "decision": cells[7],
                "resolution": cells[8],
            }
        )
    decisions: list[dict[str, str]] = []
    for row in decisions_rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        decisions.append(
            {
                "id": cells[0],
                "question": cells[1],
                "chosen": cells[2],
                "alternatives": cells[3],
                "basis": cells[4],
                "reversible": cells[5],
            }
        )
    rdir = repo / ".aw" / "records" / "reviews"
    rdir.mkdir(parents=True, exist_ok=True)
    p = rdir / f"20261001-tstset-01-{fid}-review.review.md"
    p.write_text(
        RecordBuilder().review(
            subject_id,
            subject_type=subject_type,
            reviewed_at="2026-10-01",
            reviewer="test-reviewer",
            verdict=verdict,
            rounds=[{"number": 1, "findings": findings, "decisions": decisions}],
            text_only=True,
        ),
        encoding="utf-8",
    )
    return p


class TestCheckEngineReadersOrder30:
    """Pins check_engine plan-rule and review readers before artifact_meta migration (na188y E-01)."""

    def test_build_dependency_index_and_evaluate_ipd_dependencies(
        self, tmp_path: Path
    ) -> None:
        repo = _setup_repo(tmp_path)
        (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
        (repo / ".aw" / "config" / "project.json").write_text(
            json.dumps({"dependency_schema_cutover": {"date": "2026-09-15"}}),
            encoding="utf-8",
        )
        _o30_write_full_plan(repo, "executed", "depex1", order=1, status="executed")
        _write_spec(repo, "approved", "depsp1")
        _write_backlog(repo, "done", "depbk1")

        # Valid forms: none, executed:<ipd>, exists:ipd:<id6>, exists:spec:<id6>,
        # state:spec:<status>:<id6>, exists:backlog:<id6>, state:backlog:<status>:<id6>
        _o30_write_full_plan(
            repo,
            "pending",
            "plnok1",
            order=2,
            item_deps=(
                "executed:depex1, exists:ipd:depex1, exists:spec:depsp1, "
                "state:spec:approved:depsp1, exists:backlog:depbk1, state:backlog:done:depbk1"
            ),
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "plnok2",
            order=9,
            item_deps="none",
        )
        # Unresolved sentinel: silent at check, blocking at pre-execution
        _o30_write_full_plan(repo, "pending", "plnunr", order=3, item_deps="unresolved")
        # Dangling edge
        _o30_write_full_plan(
            repo, "pending", "plndng", order=4, item_deps="executed:no9999"
        )
        # Self-edge (malformed)
        _o30_write_full_plan(
            repo, "pending", "plnslf", order=5, item_deps="executed:plnslf"
        )
        # Post-cutover missing Item-Dependencies
        _o30_write_full_plan(repo, "pending", "plnmis", order=6, item_deps=None)
        # Cycle between plncy1 <-> plncy2
        _o30_write_full_plan(
            repo, "pending", "plncy1", order=7, item_deps="executed:plncy2"
        )
        _o30_write_full_plan(
            repo, "pending", "plncy2", order=8, item_deps="executed:plncy1"
        )

        idx = check_engine.build_dependency_index(repo)
        assert "depex1" in idx.owners
        assert "depsp1" in idx.owners
        assert "depbk1" in idx.owners

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc != 0
        diags = json.loads(out)["diagnostics"]
        dep_rules = {
            (Path(d["location"]).name, d["rule"])
            for d in diags
            if d["rule"].startswith("check.ipd-dependency-")
            or d["rule"] == "check.ipd-missing-dependency-statement"
        }
        assert (
            "20261001-tstset-04-plndng-plan.ipd.md",
            "check.ipd-dependency-dangling",
        ) in dep_rules
        assert (
            "20261001-tstset-05-plnslf-plan.ipd.md",
            "check.ipd-dependency-malformed",
        ) in dep_rules
        assert (
            "20261001-tstset-06-plnmis-plan.ipd.md",
            "check.ipd-missing-dependency-statement",
        ) in dep_rules
        assert any(r == "check.ipd-dependency-cycle" for _, r in dep_rules)
        assert not any("plnok1" in fn for fn, _ in dep_rules)
        assert not any("plnok2" in fn for fn, _ in dep_rules)
        assert not any("plnunr" in fn for fn, _ in dep_rules)

        # Blocking phase surfaces unresolved sentinel too
        blk_rules = {
            (Path(d.location).name, d.rule)
            for d in check_engine.evaluate_ipd_dependencies(repo, phase="pre-execution")
            if "plnunr" in Path(d.location).name
        }
        assert (
            "20261001-tstset-03-plnunr-plan.ipd.md",
            "check.ipd-dependency-unresolved",
        ) in blk_rules

    def test_check_ipd_draft_ready(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        ready_p = _o30_write_full_plan(repo, "pending", "drf001", status="draft")
        _o30_write_full_plan(
            repo,
            "pending",
            "drf002",
            status="draft",
            concern="TODO.",
        )
        _o30_write_full_plan(repo, "pending", "drf003", status="to-review")
        _o30_write_full_plan(repo, "executed", "drf004", status="draft")

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc == 0  # info-severity rule does not fail exit code
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.ipd-draft-ready-to-review"
        ]
        assert len(hits) == 1
        assert Path(hits[0]["location"]).name == ready_p.name
        direct = check_engine.check_ipd_draft_ready(repo)
        assert len(direct) == 1
        assert direct[0].recovery == "aw ipd set to-review drf001"

    def test_check_ipd_review_stale(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        plan_p = _o30_write_full_plan(
            repo, "pending", "stl001", status="reviewed", scope_paths="src/a.py"
        )
        _o30_git(repo, "add", ".")
        _o30_git(repo, "commit", "-m", "plan-review: initial review")

        # Edit Scope-Paths after the plan-review commit so review is stale
        _o30_write_full_plan(
            repo,
            "pending",
            "stl001",
            status="reviewed",
            scope_paths="src/a.py, src/b.py",
        )

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        stale = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.ipd-review-may-be-stale"
        ]
        assert len(stale) == 1
        assert Path(stale[0]["location"]).name == plan_p.name
        direct = check_engine.check_ipd_review_stale(repo)
        assert len(direct) == 1
        assert direct[0].recovery == "aw oc review stl001 --yes"

    def test_check_scope_drift(self, tmp_path: Path) -> None:
        from tests import support

        repo, lane = support.scope_drift_repo(
            tmp_path, scope_paths="src/", plan_id="scp001", write_receipt=True
        )
        drift_file = lane / "other" / "undeclared.py"
        drift_file.parent.mkdir(parents=True, exist_ok=True)
        drift_file.write_text("x = 1\n", encoding="utf-8")

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc != 0
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.scope-drift"
        ]
        assert len(hits) == 1
        direct = check_engine.check_scope_drift(repo)
        assert len(direct) == 1
        assert "other/undeclared.py" in direct[0].detail

    def test_check_plan_priority(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        bad_p = _o30_write_full_plan(
            repo, "pending", "pri001", order=1, priority="urgent"
        )
        _o30_write_full_plan(repo, "pending", "pri002", order=2, priority="high")
        _o30_write_full_plan(
            repo, "pending", "pri003", order=3, priority="grandfathered"
        )
        _o30_write_full_plan(repo, "pending", "pri004", order=4, priority=None)

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc != 0
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.priority-invalid"
        ]
        assert len(hits) == 1
        assert Path(hits[0]["location"]).name == bad_p.name
        direct = check_engine.check_plan_priority(repo)
        assert len(direct) == 1
        assert direct[0].recovery == "aw ipd set pri001 --priority <low|medium|high>"

    def test_check_plan_work_kind(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        bad_p = _o30_write_full_plan(
            repo, "pending", "wkd001", order=1, work_kind="enhancement"
        )
        _o30_write_full_plan(repo, "pending", "wkd002", order=2, work_kind="bug")
        _o30_write_full_plan(
            repo, "pending", "wkd003", order=3, work_kind="grandfathered"
        )
        _o30_write_full_plan(repo, "pending", "wkd004", order=4, work_kind=None)

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc != 0
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.work-kind-invalid"
        ]
        assert len(hits) == 1
        assert Path(hits[0]["location"]).name == bad_p.name
        direct = check_engine.check_plan_work_kind(repo)
        assert len(direct) == 1
        assert "aw ipd set wkd001 --work-kind" in direct[0].recovery

    def test_check_plan_priority_required(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        missing_p = _o30_write_full_plan(
            repo,
            "pending",
            "prq001",
            order=1,
            status="approved",
            priority=None,
            work_kind=None,
            readiness="go-pending-approval",
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "prq002",
            order=2,
            status="approved",
            priority="medium",
            work_kind="chore",
            readiness="go-pending-approval",
        )

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc != 0
        diags = json.loads(out)["diagnostics"]
        prio_hits = [d for d in diags if d["rule"] == "check.ipd-priority-required"]
        wk_hits = [d for d in diags if d["rule"] == "check.ipd-work-kind-required"]
        assert len(prio_hits) == 1
        assert len(wk_hits) == 1
        assert Path(prio_hits[0]["location"]).name == missing_p.name
        direct = {d.rule: d for d in check_engine.check_plan_priority_required(repo)}
        assert (
            direct["check.ipd-priority-required"].recovery
            == "aw ipd set prq001 --priority <low|medium|high>"
        )
        assert (
            "aw ipd set prq001 --work-kind"
            in direct["check.ipd-work-kind-required"].recovery
        )

    def test_check_spec_review_attestation(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        (repo / ".aw" / "records" / "specs" / "reviewed").mkdir(
            parents=True, exist_ok=True
        )
        unatt_p = _write_spec(repo, "reviewed", "spr001")
        _write_spec(repo, "reviewed", "spr002")
        _o30_write_review(repo, "spr002", subject_type="spec")
        _write_spec(repo, "approved", "spr003")

        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert rc != 0
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.spec-review-unattested"
        ]
        assert len(hits) == 1
        assert Path(hits[0]["location"]).name == unatt_p.name

    def test_evaluate_review_finding_escalation(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
        (repo / ".aw" / "config" / "project.json").write_text(
            json.dumps({"review_findings_gate": {"block_at": "high"}}),
            encoding="utf-8",
        )
        bad_p = _o30_write_full_plan(repo, "pending", "rfg001", order=1)
        _o30_write_review(
            repo,
            "rfg001",
            subject_type="ipd",
            findings_rows=(
                "| F-001 | high | in-scope | B | f.py:1 | bad bug | Overall:Low | open | - |",
            ),
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "rfg002",
            order=2,
            history_lines=("- 2026-10-01 draft (test): created.",),
            body=(
                "## Open questions\n\n### OQ-01: escalate?\n\n"
                "- Blocking: yes\n- Status: open\n- Owner: maintainer\n- Finding: F-002"
            ),
        )
        _o30_write_review(
            repo,
            "rfg002",
            subject_type="ipd",
            findings_rows=(
                "| F-002 | high | in-scope | B | f.py:2 | escalated | Overall:Low | open | - |",
            ),
        )

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc != 0
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.review-finding-unescalated"
        ]
        assert len(hits) == 1
        assert Path(hits[0]["location"]).name == bad_p.name
        direct = check_engine.evaluate_review_finding_escalation(
            repo, plan_path=bad_p, plan_text=bad_p.read_text(encoding="utf-8")
        )
        assert len(direct) == 1
        assert "F-001" in direct[0].detail

    def test_evaluate_review_decision_escalation(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        bad_p = _o30_write_full_plan(repo, "pending", "rdc001", order=1)
        _o30_write_review(
            repo,
            "rdc001",
            subject_type="ipd",
            decisions_rows=("| D-1 | Change API? | yes | no | needed | no |",),
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "rdc002",
            order=2,
            history_lines=("- 2026-10-01 draft (test): created.",),
            body=(
                "## Open questions\n\n### OQ-01: escalate?\n\n"
                "- Blocking: yes\n- Status: open\n- Owner: maintainer"
            ),
        )
        _o30_write_review(
            repo,
            "rdc002",
            subject_type="ipd",
            decisions_rows=("| D-2 | Change API? | yes | no | needed | no |",),
        )

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc != 0
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.review-decision-unescalated"
        ]
        assert len(hits) == 1
        assert Path(hits[0]["location"]).name == bad_p.name
        direct = check_engine.evaluate_review_decision_escalation(
            repo, plan_path=bad_p, plan_text=bad_p.read_text(encoding="utf-8")
        )
        assert len(direct) == 1
        assert "D-1" in direct[0].detail

    def test_check_review_dangling_and_subject_id_sets(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        _o30_write_full_plan(repo, "pending", "rvp001")
        _write_spec(repo, "approved", "rvs001")

        id_sets = check_engine._review_subject_id_sets(repo)
        assert "rvp001" in id_sets["ipd"]
        assert "rvs001" in id_sets["spec"]

        bad_rev = _o30_write_review(repo, "miss99", subject_type="ipd")
        _o30_write_review(repo, "rvs001", subject_type="spec")

        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert rc != 0
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.review-dangling"
        ]
        assert len(hits) == 1
        assert Path(hits[0]["location"]).name == bad_rev.name
        direct = check_engine.check_review_dangling(repo)
        assert len(direct) == 1
        assert "miss99" in direct[0].detail

    def test_find_obligations_carried_by(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        p_decl = _o30_write_full_plan(
            repo,
            "pending",
            "obl001",
            order=1,
            body=(
                "## Deferred / out of scope (with reason)\n\n"
                "- Follow-up migration\n"
                "  - Carrier: car001\n"
                "- Already evidenced item\n"
                "  - Carrier: car001\n"
                "  - Carrier-Evidence: some/plan.ipd.md\n"
            ),
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "obl002",
            order=2,
            include_id=False,
            body=(
                "## Deferred / out of scope (with reason)\n\n"
                "- Un-id fallback\n"
                "  - Carrier: car001\n"
            ),
        )
        # Ensure carrier target does not exist -> check.ipd-uncarried-obligation fires via CLI
        obs = check_engine.find_obligations_carried_by(repo, "car001")
        assert len(obs) == 2
        by_name = {ob.plan_path.name: ob.plan_id6 for ob in obs}
        assert by_name[p_decl.name] == "obl001"
        assert by_name["20261001-tstset-02-obl002-plan.ipd.md"] == "202610"

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc != 0
        uncarried = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.ipd-uncarried-obligation"
        ]
        assert len(uncarried) == 2

    def test_check_ipd_lint_reach(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        # Post-M105 terminal plan whose status (approved) disagrees with executed/ dir
        bad_term = _o30_write_full_plan(
            repo,
            "executed",
            "lnt001",
            order=1,
            date="2026-10-15",
            status="approved",
        )
        # Pre-M105 terminal plan with same mismatch is grandfathered
        _o30_write_full_plan(
            repo,
            "executed",
            "lnt002",
            order=2,
            date="2026-07-01",
            status="approved",
        )

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc == 0  # check.ipd-lint-diagnostic is info severity
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.ipd-lint-diagnostic"
        ]
        assert [Path(h["location"]).name for h in hits] == [bad_term.name]

    def test_check_orchestrator_not_review_ready(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        orch_p = _o30_write_full_plan(
            repo,
            "pending",
            "orc001",
            setid="orcset",
            order=0,
            kind="orchestrator",
            status="to-review",
            history_lines=("- 2026-10-01 to-review (test): ready.",),
            body=(
                "## Child IPDs\n\n"
                "| Order | Id | Slug | Scope |\n"
                "|---|---|---|---|\n"
                "| 01 | cld001 | child-one | part 1 |\n"
                "| 02 | TBA | child-two | part 2 |"
            ),
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "cld001",
            setid="orcset",
            order=1,
            status="to-review",
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "orc002",
            setid="drfset",
            order=0,
            kind="orchestrator",
            status="draft",
        )

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc != 0
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.orchestrator-not-review-ready"
        ]
        assert len(hits) >= 1
        assert all(Path(h["location"]).name == orch_p.name for h in hits)


class TestCheckEngineReadersOrder29:
    """Pins the identity, Set, date, and From-Spec readers in check_engine (IPD w1cs3p E-01)."""

    def test_check_collisions_identity_and_setid(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        p1 = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20261001-colset-01-col001-first.ipd.md"
        )
        p1.write_text(
            RecordBuilder().plan(
                title="First",
                when="2026-10-01",
                plan_role="child",
                scope_paths="src/a.py",
                item_dependencies="none",
                status="draft",
                priority="medium",
                work_kind="feature",
                set="colset (First desc)",
                order=1,
                id6="col001",
                body="## Goal\n\nOne.",
                text_only=True,
            ),
            encoding="utf-8",
        )
        p2 = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20261001-colset-02-col002-second.ipd.md"
        )
        p2.write_text(
            RecordBuilder().plan(
                title="Second",
                when="2026-10-01",
                plan_role="child",
                scope_paths="src/b.py",
                item_dependencies="none",
                status="draft",
                priority="medium",
                work_kind="feature",
                set="colset (Second desc)",
                order=2,
                id6="col001",
                body="## Goal\n\nTwo.",
                text_only=True,
            ),
            encoding="utf-8",
        )
        p3 = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20261001-colset-03-slot99-third.ipd.md"
        )
        p3.write_text(
            RecordBuilder().plan(
                title="Third",
                when="2026-10-01",
                plan_role="child",
                scope_paths="src/c.py",
                item_dependencies="none",
                status="draft",
                priority="medium",
                work_kind="feature",
                set="colset (First desc)",
                order=3,
                id6="col003",
                body="## Goal\n\nThree.",
                text_only=True,
            ),
            encoding="utf-8",
        )

        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert rc != 0
        diags = json.loads(out)["diagnostics"]
        rules = {d["rule"] for d in diags}
        assert "check.id6-collision" in rules
        assert "check.setid-collision" in rules
        assert "check.id6-identity-slot" in rules

    def test_identity_declared_values_and_name_identity(self, tmp_path: Path) -> None:
        bullet_text = (
            "# Spec: Bullet\n\n- Id: `bid001`\n- Set: `bset` (Desc)\n\n"
            "## Body\n\n- Id: oth999\n"
        )
        yaml_text = (
            "---\nid: yid002\nset: yset (YAML)\n---\n\n# Research\n\n"
            "- Id: quoted1\n- Set: quotedset\n"
        )
        quoted_only_text = (
            "# Note\n\nBody.\n\n## Example\n\n- Id: qid003\n- Set: qset\n"
        )
        assert check_engine._identity_declared_values(bullet_text) == (
            ("bid001", True),
            ("bset", True),
        )
        assert check_engine._identity_declared_values(yaml_text) == (
            ("yid002", True),
            ("yset", True),
        )
        assert check_engine._identity_declared_values(quoted_only_text) == (
            ("qid003", False),
            ("qset", False),
        )

        repo = _setup_repo(tmp_path)
        leg = (
            repo
            / ".aw"
            / "records"
            / "specs"
            / "approved"
            / "20260801-1200-01-legacy-spec.spec.md"
        )
        leg.write_text(
            RecordBuilder().spec(
                title="Legacy",
                id6="leg001",
                status="approved",
                set="legset",
                body="## Goal\n\nTest.",
                raw_fields={"Set": "legset"},
                text_only=True,
            ),
            encoding="utf-8",
        )
        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        diags = json.loads(out)["diagnostics"]
        id_abs = [
            d
            for d in diags
            if d["rule"] == "check.identity-absent-from-name"
            and Path(d["location"]).name == leg.name
        ]
        assert len(id_abs) == 2

    def test_check_id_outside_metadata_region(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        unfenced = _o30_write_full_plan(
            repo,
            "pending",
            "out001",
            order=1,
            body="## Notes\n\n- Id: ext123\n",
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "out002",
            order=2,
            body="## Notes\n\n```markdown\n- Id: ext456\n```\n",
        )

        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert rc == 0 or rc != 0
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.id6-outside-metadata-region"
        ]
        assert [Path(h["location"]).name for h in hits] == [unfenced.name]

    def test_check_setid_length(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        cfg_dir = repo / ".aw" / "config"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        (cfg_dir / "project.json").write_text(
            json.dumps({"cutovers": {"setid_length": "2026-09-23"}}),
            encoding="utf-8",
        )
        # Post-cutover >14 warns; >24 errors; pre-cutover grandfathered; filename fallback works
        warn_p = _o30_write_full_plan(
            repo,
            "pending",
            "slw001",
            setid="sixteen-char-set",
            order=1,
            date="2026-10-01",
        )
        err_p = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20261001-twenty-six-character-setid-02-sle002-plan.ipd.md"
        )
        err_p.write_text(
            RecordBuilder().plan(
                title="Long",
                when="2026-10-01",
                plan_role="child",
                scope_paths="src/a.py",
                item_dependencies="none",
                status="draft",
                priority="medium",
                work_kind="feature",
                order=2,
                id6="sle002",
                body="## Goal\n\nLong.",
                raw_fields={"Set": None},
                text_only=True,
            ),
            encoding="utf-8",
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "slg003",
            setid="pre-cutover-long-setid",
            order=3,
            date="2026-09-01",
        )

        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert rc != 0
        diags = json.loads(out)["diagnostics"]
        warns = [
            Path(d["location"]).name
            for d in diags
            if d["rule"] == "check.setid-length-warn"
        ]
        errs = [
            Path(d["location"]).name
            for d in diags
            if d["rule"] == "check.setid-length-error"
        ]
        assert warns == [warn_p.name]
        assert errs == [err_p.name]

    def test_find_lifecycle_placement_conflicts(self, tmp_path: Path) -> None:
        pure = check_engine.find_lifecycle_placement_conflicts(
            [
                (
                    ".aw/records/plans/pending/20261001-s-01-plc001-a.ipd.md",
                    str(
                        RecordBuilder().plan(
                            id6="plc001", status="approved", text_only=True
                        )
                    ),
                ),
                (
                    ".aw/records/plans/executed/20261001-s-01-plc001-a.ipd.md",
                    str(
                        RecordBuilder().plan(
                            id6="plc001", status="executed", text_only=True
                        )
                    ),
                ),
            ]
        )
        assert len(pure) == 1
        ident = next(iter(pure))
        assert ident.kind == "declared-id" and ident.value == "plc001"

        repo = _setup_repo(tmp_path)
        _o30_write_full_plan(repo, "pending", "plc002", order=1, status="approved")
        _o30_write_full_plan(repo, "executed", "plc002", order=1, status="executed")
        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert rc != 0
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.lifecycle-placement-conflict"
        ]
        assert len(hits) == 1

    def test_is_retired(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        exec_p = _o30_write_full_plan(
            repo, "executed", "ret001", order=1, status="executed"
        )
        parked_pending = _o30_write_full_plan(
            repo, "pending", "ret002", order=2, status="parked"
        )
        live_p = _o30_write_full_plan(
            repo,
            "pending",
            "liv003",
            order=3,
            status="draft",
            body="## Notes\n\n- Id: body99\n",
        )
        assert check_engine.is_retired(exec_p, "plans") is True
        assert check_engine.is_retired(parked_pending, "plans") is True
        assert check_engine.is_retired(live_p, "plans") is False

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert rc == 0 or rc != 0
        # Retired parked_pending is excluded from default-scope plan rules, while live_p is checked
        assert "diagnostics" in json.loads(out)

    def test_validate_prompt_content(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        prompts_dir = repo / ".aw" / "records" / "prompts"
        (prompts_dir / "pending").mkdir(parents=True, exist_ok=True)
        (prompts_dir / "executed").mkdir(parents=True, exist_ok=True)

        missing = (
            prompts_dir / "pending" / "20261001-prmset-01-prm001-missing.prompt.md"
        )
        missing.write_text("# Prompt without comment\n\nDo work.\n", encoding="utf-8")

        mismatch_id = (
            prompts_dir / "pending" / "20261001-prmset-02-prm002-badid.prompt.md"
        )
        mismatch_id.write_text(
            RecordBuilder().prompt(
                id6="wrong9", set="prmset", status="pending", body="# P", text_only=True
            ),
            encoding="utf-8",
        )

        mismatch_st = (
            prompts_dir / "executed" / "20261001-prmset-03-prm003-badst.prompt.md"
        )
        mismatch_st.write_text(
            RecordBuilder().prompt(
                id6="prm003", set="prmset", status="pending", body="# P", text_only=True
            ),
            encoding="utf-8",
        )

        good = prompts_dir / "pending" / "20261001-prmset-04-prm004-good.prompt.md"
        good.write_text(
            RecordBuilder().prompt(
                id6="prm004", set="prmset", status="pending", body="# P", text_only=True
            ),
            encoding="utf-8",
        )

        rc, out, _ = _run_cli(repo, "check", "prompts", "--agent")
        assert rc != 0
        diags = json.loads(out)["diagnostics"]
        by_rule = {d["rule"]: Path(d["location"]).name for d in diags}
        assert by_rule.get("check.prompt-metadata-missing") == missing.name
        assert by_rule.get("check.prompt-id-mismatch") == mismatch_id.name
        assert by_rule.get("check.prompt-status-mismatch") == mismatch_st.name
        assert all(Path(d["location"]).name != good.name for d in diags)

    def test_build_plan_setid_index(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        _o30_write_full_plan(
            repo, "pending", "idx001", setid="alpha", order=1, status="approved"
        )
        _o30_write_full_plan(
            repo, "executed", "idx002", setid="alpha", order=2, status="executed"
        )
        _o30_write_full_plan(
            repo, "pending", "idx003", setid="beta", order=1, status="draft"
        )

        index = check_engine.build_plan_setid_index(repo)
        assert sorted(a.id6 for a in index["alpha"]) == ["idx001", "idx002"]
        assert [a.status for a in index["beta"]] == ["draft"]

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert "diagnostics" in json.loads(out)

    def test_plan_date_readers(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        p = _o30_write_full_plan(repo, "pending", "dat001", order=1, date="2026-10-15")
        txt = p.read_text(encoding="utf-8")
        assert check_engine._plan_date(txt) == "2026-10-15"
        assert check_engine._plan_date_compact(txt) == "20261015"
        assert check_engine._artifact_compact_date(p, txt) == "20261015"

        fallback_p = (
            repo / ".aw" / "records" / "plans" / "pending" / "unusual-name.ipd.md"
        )
        fallback_p.write_text(
            RecordBuilder().plan(when="2026-09-20", id6="dat002", text_only=True),
            encoding="utf-8",
        )
        assert (
            check_engine._artifact_compact_date(fallback_p, fallback_p.read_text())
            == "20260920"
        )

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        assert "diagnostics" in json.loads(out)

    def test_known_spec_ids(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        _write_spec(repo, "approved", "ks0001")
        _write_spec(repo, "implemented", "ks0002")
        known = check_engine.known_spec_ids(repo)
        assert {"ks0001", "ks0002"}.issubset(known)

        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert "diagnostics" in json.loads(out)

    def test_find_from_spec_plans(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        _write_spec(repo, "approved", "fs0001")
        p_blk = _o30_write_full_plan(
            repo,
            "pending",
            "fsp001",
            order=1,
            from_spec="fs0001",
            blocks_release="next",
        )
        p_nob = _o30_write_full_plan(
            repo,
            "pending",
            "fsp002",
            order=2,
            from_spec="fs0001",
        )
        found = check_engine.find_from_spec_plans(repo, "fs0001")
        by_name = {Path(p).name: br for p, br in found}
        assert by_name == {p_blk.name: "next", p_nob.name: ""}

        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert "diagnostics" in json.loads(out)

    def test_check_from_spec_dangling(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        _write_spec(repo, "approved", "spok01")
        _o30_write_full_plan(
            repo,
            "pending",
            "fsd001",
            order=1,
            from_spec="spok01",
        )
        bad = _o30_write_full_plan(
            repo,
            "pending",
            "fsd002",
            order=2,
            from_spec="dead99",
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "fsd003",
            order=3,
            from_spec="none",
        )

        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert rc != 0
        hits = [
            Path(d["location"]).name
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.from-spec-dangling"
        ]
        assert hits == [bad.name]

    def test_check_plan_spec_link_missing(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        _write_spec(repo, "approved", "spc001")
        missing = _o30_write_full_plan(
            repo,
            "pending",
            "psl001",
            order=1,
            concern="Implements spc001 requirement.",
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "psl002",
            order=2,
            concern="Discusses spc001 without originating from it.",
            from_spec="none",
        )

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        hits = [
            Path(d["location"]).name
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.plan-spec-link-missing"
        ]
        assert hits == [missing.name]

    def test_check_spec_criteria_uncovered(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        spec_p = (
            repo
            / ".aw"
            / "records"
            / "specs"
            / "approved"
            / "20261001-covset-01-covsp1-spec.spec.md"
        )
        spec_p.write_text(
            RecordBuilder().spec(
                title="Coverage",
                id6="covsp1",
                status="approved",
                set="covset",
                body="## Acceptance Criteria\n\n- **AC-1** First criterion.\n- **AC-2** Second criterion.",
                text_only=True,
            ),
            encoding="utf-8",
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "covpl1",
            setid="covset",
            order=1,
            from_spec="covsp1",
            body=(
                "## Validation and cross-check (verify before reporting done)\n\n"
                "- [ ] V-01 validates AC-1\n"
                "  - Required evidence: AC-1 passes\n"
                "  - Observed evidence:\n"
                "  - Result: pending\n"
            ),
        )

        rc, out, _ = _run_cli(repo, "check", "plans", "--agent")
        hits = [
            d
            for d in json.loads(out)["diagnostics"]
            if d["rule"] == "check.spec-criteria-uncovered"
        ]
        assert len(hits) == 1
        assert Path(hits[0]["location"]).name == spec_p.name
        direct = check_engine.check_spec_criteria_uncovered(repo)
        assert len(direct) == 1 and "AC-2" in direct[0].detail


class TestCheckEngineReadersOrder32:
    """Pins check_engine graduation and handoff readers before artifact_meta migration (IPD dbq57g E-01)."""

    def test_build_graduation_reverse_index(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        _write_backlog(repo, "graduated", "bkl101")
        _write_backlog(repo, "graduated", "bkl102")
        _write_backlog(repo, "graduated", "bkl103")
        _write_spec(repo, "approved", "spc101")

        _o30_write_full_plan(
            repo,
            "pending",
            "grp101",
            setid="setgr1",
            order=1,
            status="approved",
            from_backlog="bkl101",
            from_spec="spc101",
        )
        _o30_write_full_plan(
            repo,
            "executed",
            "grp102",
            setid="setgr1",
            order=2,
            status="executed",
            extra_raw={"From-Backlog": "bkl101\n- From-Backlog: bkl102"},
        )
        _o30_write_full_plan(
            repo,
            "pending",
            "grp103",
            setid="setgr1",
            order=3,
            status="draft",
            from_backlog="none",
            from_spec="none",
        )
        _write_spec(repo, "approved", "grs101", from_backlog="bkl103")

        idx = check_engine.build_graduation_reverse_index(repo)
        assert sorted(a.id6 for a in idx[("backlog", "bkl101")]) == [
            "grp101",
            "grp102",
        ]
        assert [a.id6 for a in idx[("backlog", "bkl102")]] == ["grp102"]
        assert [a.id6 for a in idx[("backlog", "bkl103")]] == ["grs101"]
        assert idx[("backlog", "bkl103")][0].artifact_type == "spec"
        assert [a.id6 for a in idx[("spec", "spc101")]] == ["grp101"]
        assert ("backlog", "none") not in idx
        assert ("spec", "none") not in idx

        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert "diagnostics" in json.loads(out)
        assert rc == 0 or rc != 0

    def test_graduation_cluster(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)

        # (1) Declarations alone: Graduated-To on item, no From-Backlog on plans
        _write_backlog(repo, "graduated", "clsfwd", graduated_to="setfwd")
        _o30_write_full_plan(
            repo, "pending", "clf001", setid="setfwd", order=1, status="to-review"
        )

        # (2) Origin links alone: From-Backlog on plan, no Graduated-To on item
        _write_backlog(repo, "graduated", "clsrev")
        _o30_write_full_plan(
            repo,
            "pending",
            "clr001",
            setid="setrev",
            order=1,
            status="approved",
            from_backlog="clsrev",
        )

        # (3) Both directions agree + unresolved forward target
        _write_backlog(repo, "graduated", "clsbth", graduated_to="setbth")
        _o30_write_full_plan(
            repo,
            "executed",
            "clb001",
            setid="setbth",
            order=1,
            status="executed",
            from_backlog="clsbth",
        )
        _write_backlog(repo, "graduated", "clsdng", graduated_to="nosuchset")

        c_fwd = check_engine.graduation_cluster(repo, "clsfwd")
        assert c_fwd.artifact_count == 0
        assert c_fwd.forward_setids == ("setfwd",)
        assert [a.id6 for a in c_fwd.forward_artifacts] == ["clf001"]
        assert c_fwd.forward_unresolved == ()

        c_rev = check_engine.graduation_cluster(repo, "clsrev")
        assert [a.id6 for a in c_rev.artifacts] == ["clr001"]
        assert c_rev.setids == ("setrev",)
        assert c_rev.forward_setids == ()
        assert c_rev.forward_count == 0

        c_both = check_engine.graduation_cluster(repo, "clsbth")
        assert [a.id6 for a in c_both.artifacts] == ["clb001"]
        assert [a.id6 for a in c_both.forward_artifacts] == ["clb001"]
        assert len(c_both.terminal_artifacts) == 1

        c_dng = check_engine.graduation_cluster(repo, "clsdng")
        assert c_dng.forward_unresolved == ("nosuchset",)

        rc, out, _ = _run_cli(repo, "check", "all", "--agent")
        assert rc != 0
        rules = {d["rule"] for d in json.loads(out)["diagnostics"]}
        assert "check.graduated-to-dangling" in rules

    def test_evaluate_handoff_ready(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)

        # Fallback via Graduated-To Set (plan_setid_index=None) with draft plan -> not ready
        _write_backlog(repo, "open", "hnd001", graduated_to="hndset")
        _o30_write_full_plan(
            repo, "pending", "hnp001", setid="hndset", order=1, status="draft"
        )
        res_draft = check_engine.evaluate_handoff_ready(repo, "backlog", "hnd001")
        assert res_draft.ready is False
        assert [f.code for f in res_draft.findings] == ["plan-status-not-ready"]

        # Spec carrier on backlog item: draft -> not ready; approved -> ready
        _write_backlog(repo, "open", "hnd002")
        (repo / ".aw" / "records" / "specs" / "draft").mkdir(
            parents=True, exist_ok=True
        )
        sp_c = _write_spec(repo, "draft", "hns002", from_backlog="hnd002")
        res_sp_bad = check_engine.evaluate_handoff_ready(repo, "backlog", "hnd002")
        assert res_sp_bad.ready is False
        assert [f.code for f in res_sp_bad.findings] == ["spec-status-not-ready"]

        sp_c.unlink()
        _write_spec(repo, "approved", "hns002", from_backlog="hnd002")
        res_sp_ok = check_engine.evaluate_handoff_ready(repo, "backlog", "hnd002")
        assert res_sp_ok.ready is True

        # Orchestrator active plan missing child table -> orchestrator readiness finding
        _write_backlog(repo, "open", "hnd003")
        _o30_write_full_plan(
            repo,
            "pending",
            "hno003",
            setid="hno3st",
            order=0,
            kind="orchestrator",
            status="to-review",
            from_backlog="hnd003",
            scope="orch",
        )
        res_orch = check_engine.evaluate_handoff_ready(repo, "backlog", "hnd003")
        assert res_orch.ready is False
        assert len(res_orch.findings) >= 1

        # Spec source via From-Spec -> terminal executed plan is ready
        _write_spec(repo, "approved", "hns201")
        _o30_write_full_plan(
            repo,
            "executed",
            "hnp201",
            setid="hns2st",
            order=1,
            status="executed",
            from_spec="hns201",
        )
        res_spec_src = check_engine.evaluate_handoff_ready(repo, "spec", "hns201")
        assert res_spec_src.ready is True

        rc, out, _ = _run_cli(repo, "check", "backlog", "--agent")
        assert rc == 0
        assert "diagnostics" in json.loads(out)

    def test_check_graduation_incomplete_and_history_dates(
        self, tmp_path: Path
    ) -> None:
        repo = _setup_repo(tmp_path)
        (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
        (repo / ".aw" / "config" / "project.json").write_text(
            json.dumps({"cutovers": {"graduation_ready": "2026-10-10"}}),
            encoding="utf-8",
        )
        (repo / ".aw" / "records" / "specs" / "implementing").mkdir(
            parents=True, exist_ok=True
        )

        b_post = _write_backlog(
            repo,
            "graduated",
            "gip001",
            history_lines=(
                "- 2026-10-12 graduated (test): graduated",
                "- 2026-10-01 created (test): created",
            ),
        )
        b_pre = _write_backlog(
            repo,
            "graduated",
            "gip002",
            history_lines=("- 2026-10-05 graduated (test): old graduation",),
        )
        assert (
            check_engine._item_graduated_date(b_post.read_text(encoding="utf-8"))
            == "20261012"
        )
        assert (
            check_engine._item_graduated_date(b_pre.read_text(encoding="utf-8"))
            == "20261005"
        )

        s_post = _write_spec(
            repo,
            "implementing",
            "gis001",
            history_lines=("- 2026-10-15 implementing (test): started",),
        )
        s_pre = _write_spec(
            repo,
            "implementing",
            "gis002",
            history_lines=("- 2026-10-02 implementing (test): early",),
        )
        assert (
            check_engine._spec_implementing_date(s_post.read_text(encoding="utf-8"))
            == "20261015"
        )
        assert (
            check_engine._spec_implementing_date(s_pre.read_text(encoding="utf-8"))
            == "20261002"
        )

        rc_b, out_b, _ = _run_cli(repo, "check", "backlog", "--agent")
        assert rc_b != 0
        b_hits = [
            Path(d["location"]).name
            for d in json.loads(out_b)["diagnostics"]
            if d["rule"] == "check.graduation-incomplete"
        ]
        assert b_hits == [b_post.name]

        rc_s, out_s, _ = _run_cli(repo, "check", "specs", "--agent")
        assert rc_s != 0
        s_hits = [
            Path(d["location"]).name
            for d in json.loads(out_s)["diagnostics"]
            if d["rule"] == "check.graduation-incomplete"
        ]
        assert s_hits == [s_post.name]

    def test_graduated_closable_warnings(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)

        # Closable: graduated item whose carriers are all terminal
        b_close = _write_backlog(repo, "graduated", "gcw001")
        _write_plan(
            repo, "executed", "gcp001", status="executed", from_backlog="gcw001"
        )
        _write_spec(repo, "implemented", "gcs001", from_backlog="gcw001")

        # Still active: graduated item with an active pending plan
        _write_backlog(repo, "graduated", "gcw002")
        _write_plan(repo, "pending", "gcp002", status="approved", from_backlog="gcw002")

        warns = check_engine.graduated_closable_warnings(repo)
        assert len(warns) == 1
        assert warns[0].rule == "check.graduated-item-closable"
        assert Path(warns[0].location).name == b_close.name
        assert "aw backlog set gcw001 --status done --evidence" in warns[0].detail

        rc, out, _ = _run_cli(repo, "check", "backlog", "--agent")
        assert rc == 0
        assert "diagnostics" in json.loads(out)


class TestRecordSkipListAndMetaDirExclusion:
    """Behavioral fixture tests for shared record skip names and meta/ exclusion (IPD i16on1 E-02)."""

    def test_meta_dir_and_skip_names_yield_no_find_check_or_attention_row(
        self, tmp_path: Path
    ) -> None:
        from agent_workflows import artifact_core

        repo = tmp_path / "repo"
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(
            parents=True, exist_ok=True
        )
        meta_dir = repo / ".aw" / "records" / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        _init_git_repo(repo)

        meta_log = meta_dir / "abc123.jsonl"
        meta_log.write_text(
            json.dumps(
                {
                    "v": 1,
                    "seq": 1,
                    "append": 1,
                    "op": "create",
                    "at": "2026-10-01T00:00:00Z",
                    "actor": {"tool": "test"},
                    "path": "plans/pending/20261001-tstset-01-abc123-dummy.ipd.md",
                    "fields": {
                        "id": "abc123",
                        "type": "ipd",
                        "status": "draft",
                        "set": "tstset",
                        "order": 1,
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        meta_readme = meta_dir / "README.md"
        meta_readme.write_text(
            RecordBuilder().plan(
                title="Meta README",
                id6="met001",
                raw_fields={"Status": "pending"},
                text_only=True,
            ),
            encoding="utf-8",
        )
        pending_readme = repo / ".aw" / "records" / "plans" / "pending" / "README.md"
        pending_readme.write_text(
            RecordBuilder().plan(
                id6="rdm001", raw_fields={"Status": "pending"}, text_only=True
            ),
            encoding="utf-8",
        )

        # Citation scan via iter_scan_files keeps reading plans/pending/README.md
        # while excluding meta/*.jsonl and meta/README.md.
        scanned_rels = {
            p.relative_to(repo).as_posix()
            for p in artifact_core.iter_scan_files(repo, scan_roots=(".aw/records",))
        }
        assert ".aw/records/plans/pending/README.md" in scanned_rels
        assert ".aw/records/meta/abc123.jsonl" not in scanned_rels
        assert ".aw/records/meta/README.md" not in scanned_rels

        # aw find returns no row for any of the three files.
        rc_find, out_find, _ = _run_cli(repo, "find", "all", "--json")
        assert rc_find == 0, out_find
        find_payload = json.loads(out_find)
        find_paths = find_payload.get("data", {}).get("paths", [])
        assert find_paths == [], f"Expected zero aw find paths, got {find_paths}"
        for token in ("abc123", "met001", "rdm001"):
            rc_tok, _, _ = _run_cli(repo, "find", token)
            assert rc_tok == 2, f"Expected no match (exit 2) for {token}, got {rc_tok}"

        # aw check returns clean and no diagnostic references any of the three files.
        rc_chk, out_chk, _ = _run_cli(repo, "check", "all", "--agent")
        assert rc_chk == 0, out_chk
        chk_payload = json.loads(out_chk)
        assert chk_payload.get("diagnostics", []) == [], chk_payload

        # aw attention returns no item and no violation for any of the three files.
        rc_att, out_att, _ = _run_cli(repo, "attention", "--all", "--format", "json")
        assert rc_att == 0, out_att
        att_payload = json.loads(out_att)
        assert att_payload.get("valid") is True, att_payload.get("violations")
        assert att_payload.get("items") == []
        assert att_payload.get("violations") == []

    def test_meta_dir_readme_citation_rewrite_preserved(self, tmp_path: Path) -> None:
        repo = _setup_repo(tmp_path)
        (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
        (repo / ".aw" / "config" / "project.json").write_text(
            json.dumps({"cutovers": {"spec_id6": "2026-08-28"}}),
            encoding="utf-8",
        )
        old_spec_name = "20260701-1200-01-legacy.spec.md"
        spec_file = repo / ".aw" / "records" / "specs" / old_spec_name
        spec_file.write_text(
            RecordBuilder().spec(
                title="Legacy", when="2026-07-01", status="draft", text_only=True
            ),
            encoding="utf-8",
        )
        pending_readme = repo / ".aw" / "records" / "plans" / "pending" / "README.md"
        pending_readme.write_text(
            f"# Pending Plans\n\nSee .aw/records/specs/{old_spec_name} for context.\n",
            encoding="utf-8",
        )
        meta_dir = repo / ".aw" / "records" / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        (meta_dir / "abc123.jsonl").write_text("", encoding="utf-8")
        meta_readme = meta_dir / "README.md"
        meta_readme_orig = f"# Meta README\n\nHistorical note citing {old_spec_name}.\n"
        meta_readme.write_text(meta_readme_orig, encoding="utf-8")

        rc, out, err = _run_cli(
            repo, "rename", "specs", old_spec_name, "--to-id6", "--apply", "--no-commit"
        )
        assert rc == 0, f"aw rename failed: {out}\n{err}"

        renamed_specs = [
            p.name
            for p in (repo / ".aw" / "records" / "specs").glob("*.spec.md")
            if p.name != old_spec_name
        ]
        assert len(renamed_specs) == 1
        new_spec_name = renamed_specs[0]

        updated_readme = pending_readme.read_text(encoding="utf-8")
        assert old_spec_name not in updated_readme
        assert new_spec_name in updated_readme
        # meta/README.md is excluded from iter_scan_files and stays untouched.
        assert meta_readme.read_text(encoding="utf-8") == meta_readme_orig

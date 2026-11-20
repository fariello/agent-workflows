"""Behavioral writer-obligation tests for spec `4sd62s` Sections 4.1a and 4.4 (IPD d4w53g).

Covers `4sd62s` AC-15 (1)-(3), AC-14a (1)-(2), and 4.1a K2 readiness and coverage writer
obligations on `tmp_path` fixtures, asserting on real return values, file bytes / SHA-256 digests,
and parsed state without reading production source.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from agent_workflows import artifact_audit as audit
from agent_workflows import artifact_core as core
from agent_workflows import artifact_meta as meta
from agent_workflows import check_engine
from agent_workflows import cli
from agent_workflows import coverage_record as cov_rec
from agent_workflows import ipd_lifecycle as lifecycle
from agent_workflows import ipd_schema as schema
from agent_workflows import plan_readiness as pr
from agent_workflows import review_findings as rf
from tests import support

pytestmark = pytest.mark.core

DAY = "2030-01-02"


def _init_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@example.invalid"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    (root / ".aw" / "records" / "reviews").mkdir(parents=True)
    (root / ".aw" / "state").mkdir(parents=True)
    return root


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_plan(
    repo: Path,
    *,
    id6: str = "pl0001",
    readiness: str | None = "no-go",
    status: str = "reviewed",
    history_lines: str = "- 2026-09-09 reviewed (tester): /plan-review complete: REVIEWED - OPEN QUESTIONS; PR-001",
) -> Path:
    path = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / f"20261109-demo-01-{id6}-sample.ipd.md"
    )
    lines = [
        f"# IPD: Sample {id6}",
        "",
        "- Date: 2026-11-09",
        "- Kind: child",
        "- Scope-Paths: agent_workflows/a.py",
        "- Item-Dependencies: none",
        f"- Status: {status}",
    ]
    if readiness is not None:
        lines.append(f"- Readiness: {readiness}")
    lines.extend(
        [
            "- Set: demo",
            "- Order: 1",
            "- Priority: medium",
            "- Work-Kind: feature",
            f"- Id: {id6}",
            "",
            "## Workflow history",
            "",
            history_lines,
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
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _legacy_render(tag: str = "same-status") -> meta.LegacyRender:
    return meta.LegacyRender(tag=tag, day=DAY, actor_label="aw set", history=False)


# --------------------------------------------------------------------------------------
# Readiness and review_kind obligations (4sd62s AC-15 (1)-(2), AC-14a (1)-(2), 4.1a K2)
# --------------------------------------------------------------------------------------


def test_ac15_1_set_readiness_refused_alone_and_paired_with_review(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    plan = _write_plan(repo, readiness="no-go")
    target = meta.LegacyTarget(plan, "plans", "pl0001")
    ctx = meta.legacy_context(repo)
    before_digest = _sha256(plan)

    with pytest.raises(ValueError, match="review-owned"):
        meta.append(
            target,
            [{"op": "set", "fields": {"readiness": "go"}}],
            actor={"tool": "aw set"},
            legacy_render=_legacy_render(),
            repo_root=repo,
            project_context=ctx,
        )
    assert _sha256(plan) == before_digest

    with pytest.raises(ValueError, match="review-owned"):
        meta.append(
            target,
            [
                {
                    "op": "review",
                    "review_kind": "gate",
                    "round": 1,
                    "verdict": "APPROVE",
                },
                {"op": "set", "fields": {"readiness": "go"}},
            ],
            actor={"tool": "aw set"},
            legacy_render=_legacy_render(),
            repo_root=repo,
            project_context=ctx,
        )
    assert _sha256(plan) == before_digest


def test_ac14a_1_and_2_review_kind_payload_refusals(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    plan = _write_plan(repo, readiness="no-go")
    target = meta.LegacyTarget(plan, "plans", "pl0001")
    ctx = meta.legacy_context(repo)
    before_digest = _sha256(plan)

    # AC-14a (1): gate review carrying a refinement verdict is refused.
    with pytest.raises(ValueError, match="invalid gate verdict"):
        meta.append(
            target,
            [
                {
                    "op": "review",
                    "review_kind": "gate",
                    "round": 1,
                    "verdict": "REVIEWED - MATERIAL CHANGES APPLIED",
                }
            ],
            actor={"tool": "aw ipd review"},
            legacy_render=_legacy_render(),
            repo_root=repo,
            project_context=ctx,
        )
    assert _sha256(plan) == before_digest

    # AC-14a (2): refinement review carrying readiness is refused.
    with pytest.raises(
        ValueError, match="refinement review must not carry 'readiness'"
    ):
        meta.append(
            target,
            [
                {
                    "op": "review",
                    "review_kind": "refinement",
                    "round": 1,
                    "verdict": "REVIEWED - MATERIAL CHANGES APPLIED",
                    "readiness": "go",
                }
            ],
            actor={"tool": "aw ipd review"},
            legacy_render=_legacy_render(),
            repo_root=repo,
            project_context=ctx,
        )
    assert _sha256(plan) == before_digest


def test_recheck_readiness_refuses_missing_verdict_token_per_k2(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)

    # Case 1: review record present in history, but verdict is not in plan_readiness.VERDICTS.
    plan_off_vocab = _write_plan(
        repo,
        id6="pl0001",
        readiness="no-go",
        history_lines="- 2026-09-09 reviewed (tester): /plan-review complete: REVIEWED; PR-001",
    )
    digest_off_vocab = _sha256(plan_off_vocab)
    res_off, text_off = pr.recheck_readiness(
        repo, plan_off_vocab, apply=True, date=DAY, actor="tester"
    )
    assert res_off.may_write is False
    assert text_off is None
    assert any(c.name == pr.C_NEGATIVE_VERDICT and c.holds for c in res_off.conditions)
    assert _sha256(plan_off_vocab) == digest_off_vocab

    # Case 2: no review record in history at all.
    plan_no_rev = _write_plan(
        repo,
        id6="pl0002",
        readiness="no-go",
        history_lines="- 2026-09-09 draft (author): created.",
    )
    digest_no_rev = _sha256(plan_no_rev)
    res_no_rev, text_no_rev = pr.recheck_readiness(
        repo, plan_no_rev, apply=True, date=DAY, actor="tester"
    )
    assert res_no_rev.may_write is False
    assert text_no_rev is None
    assert any(
        c.name == pr.C_NEGATIVE_VERDICT and c.holds for c in res_no_rev.conditions
    )
    assert _sha256(plan_no_rev) == digest_no_rev


def test_recheck_readiness_qualifying_plan_writes_go_pending_approval_and_dry_run_is_clean(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    plan = _write_plan(repo, id6="pl0003", readiness="no-go")
    rf.write_review(
        repo
        / ".aw"
        / "records"
        / "reviews"
        / "20261109-demo-01-pl0003-sample.review.md",
        subject_id="pl0003",
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
    before_digest = _sha256(plan)

    dry_res, dry_text = pr.recheck_readiness(
        repo, plan, apply=False, date=DAY, actor="tester", head="abc1234"
    )
    assert dry_res.may_write is True, dry_res.refusals
    assert dry_text is not None
    assert schema.read_readiness(dry_text) == "go-pending-approval"
    assert _sha256(plan) == before_digest

    res, new_text = pr.recheck_readiness(
        repo, plan, apply=True, date=DAY, actor="tester", head="abc1234"
    )
    assert res.may_write is True, res.refusals
    assert new_text is not None
    on_disk = plan.read_text(encoding="utf-8")
    assert on_disk == new_text
    assert schema.read_readiness(on_disk) == "go-pending-approval"
    newest = pr.extract_newest_history_entry(on_disk) or ""
    assert newest.startswith(f"- {DAY} readiness re-check (tester): `- Readiness:`")
    assert newest.count("readiness re-check") == 1


# --------------------------------------------------------------------------------------
# Coverage writer obligations (4sd62s AC-15 (3), checked_by decoupling, rollback)
# --------------------------------------------------------------------------------------


def test_ac15_3_set_coverage_refused_and_coverage_record_write_round_trips(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    plan = _write_plan(repo, id6="orc001", readiness="go", status="approved")
    target = meta.LegacyTarget(plan, "plans", "orc001")
    ctx = meta.legacy_context(repo)
    before_digest = _sha256(plan)

    with pytest.raises(ValueError, match="coverage-owned"):
        meta.append(
            target,
            [{"op": "set", "fields": {"coverage": "pass"}}],
            actor={"tool": "aw set"},
            legacy_render=_legacy_render(),
            repo_root=repo,
            project_context=ctx,
        )
    assert _sha256(plan) == before_digest

    fail_res = cov_rec.write(
        plan,
        "fail",
        quotes=["uncovered child obligation"],
        model="claude-sonnet-4-6",
        tool="aw oc run",
        commit=False,
        repo=repo,
    )
    assert fail_res.written is True, fail_res.detail
    assert fail_res.committed is False

    fail_text = plan.read_text(encoding="utf-8")
    rec_fail = cov_rec.read(fail_text)
    assert rec_fail.verdict == "fail"
    assert rec_fail.model == "claude-sonnet-4-6"
    assert rec_fail.quotes == ("uncovered child obligation",)
    assert cov_rec.is_current(fail_text) is True
    assert f"- Coverage-Checked: {rec_fail.date} by claude-sonnet-4-6" in fail_text
    assert (
        f"- {rec_fail.date} coverage fail (aw oc run): fingerprint {rec_fail.fingerprint[:12]}, "
        "model claude-sonnet-4-6"
    ) in fail_text

    pass_res = cov_rec.write(
        plan,
        "pass",
        quotes=[],
        model="",
        tool="aw agy run",
        commit=False,
        repo=repo,
    )
    assert pass_res.written is True, pass_res.detail
    pass_text = plan.read_text(encoding="utf-8")
    rec_pass = cov_rec.read(pass_text)
    assert rec_pass.verdict == "pass"
    assert rec_pass.model == "by host-default"
    assert rec_pass.quotes == ()
    assert "## Coverage findings" not in pass_text
    assert f"- Coverage-Checked: {rec_pass.date} by host-default" in pass_text
    assert (
        f"- {rec_pass.date} coverage pass (aw agy run): fingerprint {rec_pass.fingerprint[:12]}, "
        "model by host-default"
    ) in pass_text


def test_coverage_checked_by_decoupled_from_history_actor_label(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    plan = _write_plan(repo, id6="orc002", readiness="go", status="approved")
    target = meta.LegacyTarget(plan, "plans", "orc002")
    ctx = meta.legacy_context(repo)

    meta.append(
        target,
        [
            {
                "op": "coverage",
                "coverage": "pass",
                "coverage_fingerprint": "abc1234567890000",
                "message": "fingerprint abc123456789, model claude-sonnet-4-6",
            }
        ],
        actor={"tool": "aw oc run", "model": "claude-sonnet-4-6"},
        legacy_render=meta.LegacyRender(
            tag="coverage pass",
            day=DAY,
            actor_label="aw oc run",
            checked_by="claude-sonnet-4-6",
            history=True,
        ),
        repo_root=repo,
        project_context=ctx,
    )
    lines = plan.read_text(encoding="utf-8").splitlines()
    assert f"- Coverage-Checked: {DAY} by claude-sonnet-4-6" in lines
    assert (
        f"- {DAY} coverage pass (aw oc run): fingerprint abc123456789, model claude-sonnet-4-6"
        in lines
    )


def test_coverage_record_write_restores_bytes_on_refusal_and_isolates_standalone_locks(
    tmp_path: Path,
) -> None:
    standalone_dir = tmp_path / "standalone"
    standalone_dir.mkdir()
    plan = standalone_dir / "standalone.ipd.md"
    plan.write_text(
        "# IPD: Standalone\n\n"
        "- Status: approved\n"
        "- Readiness: go\n\n"
        "## Workflow history\n\n"
        "- 2026-11-09 draft (author): created.\n\n"
        "## Validation and cross-check\n\n"
        "- [ ] V-01 check\n",
        encoding="utf-8",
    )
    before_digest = _sha256(plan)

    # Absolute path in tool triggers validate_new_events refusal after body_text mutation;
    # pre-call bytes must be restored identically with written=False.
    bad_res = cov_rec.write(
        plan,
        "fail",
        quotes=["some quote"],
        model="claude-sonnet-4-6",
        tool="/opt/secret/file",
        commit=False,
    )
    assert bad_res.written is False
    assert bad_res.committed is False
    assert bad_res.detail
    assert _sha256(plan) == before_digest
    assert "## Coverage findings" not in plan.read_text(encoding="utf-8")

    # Successful standalone write uses standalone_dir/.aw/state/locks rather than cwd.
    ok_res = cov_rec.write(
        plan,
        "pass",
        model="claude-sonnet-4-6",
        tool="aw oc run",
        commit=False,
    )
    assert ok_res.written is True, ok_res.detail
    lock_files = list(
        (standalone_dir / ".aw" / "state" / "locks").glob("meta-path-*.lock")
    )
    assert len(lock_files) == 1


# --------------------------------------------------------------------------------------
# Retirement, unset approval, log-backed note, AC-24 (2) actor refusals, banner (8q27jt)
# --------------------------------------------------------------------------------------


def _init_plans_git_repo(tmp_path: Path, name: str = "repo") -> Path:
    root = tmp_path / name
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@example.invalid"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    for sub in ("pending", "executed", "superseded", "not-executed"):
        (root / ".aw" / "records" / "plans" / sub).mkdir(parents=True)
    (root / ".aw" / "records" / "reviews").mkdir(parents=True)
    (root / ".aw" / "state").mkdir(parents=True)
    return root


def _write_set_fixtures(
    repo: Path,
    *,
    setid: str,
    orch_id6: str,
    child_id6: str,
    orch_status: str = "approved",
    child_status: str = "executed",
    child_bucket: str = "executed",
    approval_line: str | None = "2026-11-12, recorded via aw ipd set: approved",
    top_body_banner: str | None = None,
) -> tuple[Path, Path]:
    child_name = f"20261109-{setid}-01-{child_id6}-child.ipd.md"
    child_path = repo / ".aw" / "records" / "plans" / child_bucket / child_name
    child_lines = [
        f"# IPD: Child {child_id6}",
        "",
        "- Date: 2026-11-09",
        "- Kind: child",
        "- Scope-Paths: agent_workflows/a.py",
        "- Item-Dependencies: none",
        f"- Status: {child_status}",
        "- Readiness: go",
        f"- Set: {setid}",
        "- Order: 1",
        "- Priority: medium",
        "- Work-Kind: feature",
        f"- Id: {child_id6}",
        "",
        "## Workflow history",
        "",
        f"- 2026-11-09 {child_status} (tester): set.",
        "",
    ]
    if top_body_banner:
        child_lines.extend([top_body_banner, ""])
    child_lines.extend(
        [
            "## Goal",
            "",
            "Child goal.",
            "",
            "## Detailed Implementation Checklist (TODO)",
            "",
            "- [x] E-01 Done",
            "  - Depends on: none",
            "  - Expected outcome: done",
            "  - Execution state: performed",
            "",
            "## Validation and cross-check (verify before reporting done)",
            "",
            "- [x] V-01 validates E-01",
            "  - Required evidence: paste output",
            "  - Observed evidence: ok",
            "  - Result: pass",
            "",
        ]
    )
    child_path.write_text("\n".join(child_lines), encoding="utf-8")

    orch_name = f"20261109-{setid}-00-{orch_id6}-orch.ipd.md"
    orch_path = repo / ".aw" / "records" / "plans" / "pending" / orch_name
    orch_lines = [
        f"# IPD: Orchestrator {orch_id6}",
        "",
        "- Date: 2026-11-09",
        "- Kind: orchestrator",
        "- Concern: Coordinate set completion.",
        "- Scope: Coordinate child plans in the set.",
        "- Scope-Paths: grandfathered",
        "- Item-Dependencies: none",
        f"- Status: {orch_status}",
        "- Readiness: go",
    ]
    if approval_line is not None:
        orch_lines.append(f"- Approval: {approval_line}")
    orch_lines.extend(
        [
            f"- Set: {setid}",
            "- Order: 0",
            "- Priority: medium",
            "- Work-Kind: feature",
            "- Highest E allocated: 01",
            "- Author: tester",
            f"- Id: {orch_id6}",
            "",
            "## Workflow history",
            "",
            f"- 2026-11-09 {orch_status} (tester): ready.",
            "- 2026-11-09 /plan-review (tester): APPROVE",
            "",
            "## Goal",
            "",
            "Orchestrator goal.",
            "",
            "## Detailed Implementation Checklist (TODO)",
            "",
            f"- [ ] E-01 CONFIRM {child_id6} REACHED executed",
            "  - Depends on: none",
            f"  - Expected outcome: {child_id6} reached executed",
            "  - Execution state: pending",
            "",
            "## Child IPDs, sequence, and dependencies",
            "",
            "| Order | Id | Child | Depends on |",
            "|---|---|---|---|",
            f"| 01 | {child_id6} | child 01 | none |",
            "",
            "## Completion criteria (the whole Set is done only when)",
            "",
            f"- `{child_id6}` is executed.",
            "",
            "## Cross-IPD validation",
            "",
            "Run child validation.",
            "",
            "## Deferred / out of scope (with reason)",
            "",
            "None.",
            "",
            "## Scope check",
            "",
            "- Over-scope: none.",
            "- Under-scope: none.",
            "",
            "## Required tests / validation",
            "",
            "Core tests pass.",
            "",
            "## Open questions",
            "",
            "None.",
            "",
            "## Validation and cross-check (verify before reporting the Set complete)",
            "",
            "- [ ] V-01 validates E-01",
            f"  - Required evidence: {child_id6} reached executed",
            "  - Observed evidence:",
            "  - Result: pending",
            "",
            "## Approval and execution gate",
            "",
            "Approved for execution.",
            "",
        ]
    )
    orch_path.write_text("\n".join(orch_lines), encoding="utf-8")
    return orch_path, child_path


def test_rollup_retirement_strips_approval_records_finalize_actor_and_replays_log(
    tmp_path: Path,
) -> None:
    lifecycle.clear_checkout_control_root_cache()
    try:
        repo = _init_plans_git_repo(tmp_path, "rollup_repo")
        orch_path, _child_path = _write_set_fixtures(
            repo,
            setid="retset",
            orch_id6="orc010",
            child_id6="chd010",
            orch_status="approved",
            child_status="executed",
            child_bucket="executed",
        )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init set"], cwd=repo, check=True)

        actor_str = "aw oc run model=claude-opus-4-6 variant=high profile=fast"
        run_id = "run-20261113T000000Z-1"
        res = lifecycle.retire_orchestrator(
            repo,
            orch_path,
            actor=actor_str,
            setid="retset",
            run_id=run_id,
            apply=True,
            env={},
        )
        assert res.exit_code == lifecycle.EXIT_OK, res.message

        dest_path = repo / ".aw" / "records" / "plans" / "executed" / orch_path.name
        assert dest_path.is_file()
        assert not orch_path.exists()

        dest_text = dest_path.read_text(encoding="utf-8")
        assert "- Approval:" not in dest_text
        assert "- Scope-Exceeded:" not in dest_text
        assert lifecycle.ROLLUP_SUPERSEDED_STATEMENT in dest_text
        checklist_tail = dest_text.split("## Detailed Implementation Checklist", 1)[1]
        assert lifecycle.ROLLUP_SUPERSEDED_STATEMENT in checklist_tail
        expected_msg = lifecycle.rollup_history_message(
            setid="retset", run_id=run_id, children=["chd010"]
        )
        assert expected_msg in dest_text

        expected_actor = {
            "tool": "aw oc run",
            "host": "oc",
            "model": "claude-opus-4-6",
            "variant": "high",
            "run_id": run_id,
        }
        assert res.evidence["finalize_actor"] == expected_actor

        legacy_state = meta.read("orc010", project_context=meta.legacy_context(repo))
        assert legacy_state.status == "executed"
        assert legacy_state.fields.get("approval") is None

        # Log-backed orchestrator: unset approval + transition replays cleanly with same actor.
        log_records = tmp_path / "log_records"
        log_state = tmp_path / "log_state"
        log_records.mkdir()
        log_state.mkdir()
        log_ctx = type(
            "Ctx",
            (),
            {"logical_roots": {"records": str(log_records), "state": str(log_state)}},
        )()
        meta.create(
            "orc011",
            "ipd",
            {
                "status": "approved",
                "set": "retset",
                "order": "0",
                "plan_role": "orchestrator",
                "readiness": "go",
                "approval": "2026-11-12, recorded via aw ipd set: approved",
            },
            "# IPD: Log Orch\n",
            destination="plans/pending/20261109-retset-00-orc011-orch.ipd.md",
            project_context=log_ctx,
            actor={"tool": "aw ipd scaffold"},
        )
        append_res = meta.append(
            "orc011",
            [
                {
                    "op": "transition",
                    "from": "approved",
                    "to": "executed",
                    "message": expected_msg,
                },
                {"op": "unset", "fields": ["approval"]},
            ],
            actor=res.evidence["finalize_actor"],
            project_context=log_ctx,
        )
        assert append_res["committed"] is True

        replayed_state = meta.read("orc011", project_context=log_ctx)
        assert replayed_state.status == "executed"
        assert replayed_state.fields.get("approval") is None
        events = meta.history("orc011", project_context=log_ctx)
        assert events[-1]["actor"] == expected_actor
        assert events[-1]["op"] == "unset"
        assert events[-2]["actor"] == expected_actor
        assert events[-2]["op"] == "transition"
    finally:
        lifecycle.clear_checkout_control_root_cache()


def test_child_retirement_writes_phase_b_note_and_log_backed_note_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(core, "utc_history_date", lambda *a, **k: DAY)

    # 1. Phase-B orchestrator
    repo = _init_plans_git_repo(tmp_path, "phase_b_child")
    orch_path, _child_path = _write_set_fixtures(
        repo,
        setid="chset",
        orch_id6="orc020",
        child_id6="chd020",
        orch_status="to-review",
        child_status="to-review",
        child_bucket="pending",
        approval_line=None,
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

    rc = cli.main(
        [
            "set",
            "not-executed",
            "chd020",
            "--actor",
            "aw oc run model=claude-sonnet-4-6",
            "--by-human",
            "-m",
            "dropped",
            "--yes",
            "--no-commit",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0
    orch_text = orch_path.read_text(encoding="utf-8")
    assert (
        f"- {DAY} same-status (aw oc run model=claude-sonnet-4-6): "
        "child chd020 retired not-executed: dropped"
    ) in orch_text

    # 2. Log-backed orchestrator (meta/<orch_id6>.jsonl created via artifact_meta.create)
    repo2 = _init_plans_git_repo(tmp_path, "log_child")
    _orch_unused, _child2 = _write_set_fixtures(
        repo2,
        setid="logch",
        orch_id6="orc021",
        child_id6="chd021",
        orch_status="approved",
        child_status="to-review",
        child_bucket="pending",
    )
    _orch_unused.unlink()
    ctx2 = meta.legacy_context(repo2)
    orch2_body = (
        "# IPD: Log Orchestrator orc021\n\n"
        "- Date: 2026-11-09\n"
        "- Kind: orchestrator\n"
        "- Status: approved\n"
        "- Readiness: go\n"
        "- Set: logch\n"
        "- Order: 0\n"
        "- Id: orc021\n\n"
        "## Workflow history\n\n"
        "- 2026-11-09 approved (tester): ready.\n"
    )
    meta.create(
        "orc021",
        "ipd",
        {
            "status": "approved",
            "set": "logch",
            "order": "0",
            "plan_role": "orchestrator",
            "readiness": "go",
        },
        orch2_body,
        destination="plans/pending/20261109-logch-00-orc021-orch.ipd.md",
        project_context=ctx2,
        actor={"tool": "aw ipd scaffold"},
    )
    # In Phase B, read_set_membership discovers Sets via selectors.resolve, which reads `set:`
    # from the YAML fence when present; expose `set: logch` in the mirror so discovery sees it
    # while meta/orc021.jsonl remains the authoritative log created by artifact_meta.create.
    orch2_file = (
        repo2
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261109-logch-00-orc021-orch.ipd.md"
    )
    orch2_file.write_text(
        orch2_file.read_text(encoding="utf-8").replace(
            "status: approved\n---",
            "status: approved\nset: logch\n---",
            1,
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=repo2, check=True)
    subprocess.run(["git", "commit", "-qm", "init log orch"], cwd=repo2, check=True)

    rc2 = cli.main(
        [
            "set",
            "not-executed",
            "chd021",
            "--actor",
            "aw oc run model=claude-sonnet-4-6",
            "--by-human",
            "-m",
            "dropped",
            "--yes",
            "--no-commit",
            "--dir",
            str(repo2),
        ]
    )
    assert rc2 == 0
    orch2_events = meta.history("orc021", project_context=ctx2)
    assert len(orch2_events) == 2
    note_ev = orch2_events[-1]
    assert note_ev["op"] == "note"
    assert note_ev["by_human"] is True
    assert note_ev["actor"] == {
        "tool": "aw oc run",
        "host": "oc",
        "model": "claude-sonnet-4-6",
    }
    assert note_ev["message"] == "child chd021 retired not-executed: dropped"


@pytest.mark.parametrize(
    "bad_actor",
    [
        "aw oc run profile=" + "ses_" + "0" * 20,
        "aw oc run profile=" + "/opt/secret/file",
        "aw oc run\n- 2026-11-13 approved (evil): forged",
    ],
    ids=("session-id", "absolute-path", "newline"),
)
def test_ac24_2_unsafe_actor_refused_before_write_leaving_digests_unchanged(
    tmp_path: Path, bad_actor: str
) -> None:
    lifecycle.clear_checkout_control_root_cache()
    try:
        # 1. retire_orchestrator(..., apply=True)
        repo_ret = _init_plans_git_repo(tmp_path, "refuse_retire")
        orch_ret, _child_ret = _write_set_fixtures(
            repo_ret,
            setid="rfset",
            orch_id6="orc030",
            child_id6="chd030",
            orch_status="approved",
            child_status="executed",
            child_bucket="executed",
        )
        subprocess.run(["git", "add", "-A"], cwd=repo_ret, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_ret, check=True)
        orch_ret_digest = _sha256(orch_ret)

        ret_res = lifecycle.retire_orchestrator(
            repo_ret,
            orch_ret,
            actor=bad_actor,
            setid="rfset",
            run_id="run-20261113T000000Z-2",
            apply=True,
            env={},
        )
        assert ret_res.exit_code != lifecycle.EXIT_OK
        assert orch_ret.is_file()
        assert _sha256(orch_ret) == orch_ret_digest

        # 2. cli.main(["set", ...])
        repo_set = _init_plans_git_repo(tmp_path, "refuse_set")
        orch_set, child_set = _write_set_fixtures(
            repo_set,
            setid="rsset",
            orch_id6="orc031",
            child_id6="chd031",
            orch_status="to-review",
            child_status="to-review",
            child_bucket="pending",
            approval_line=None,
        )
        subprocess.run(["git", "add", "-A"], cwd=repo_set, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_set, check=True)
        orch_set_digest = _sha256(orch_set)
        child_set_digest = _sha256(child_set)

        rc_set = cli.main(
            [
                "set",
                "not-executed",
                "chd031",
                "--actor",
                bad_actor,
                "-m",
                "dropped",
                "--yes",
                "--no-commit",
                "--dir",
                str(repo_set),
            ]
        )
        assert rc_set != 0
        assert child_set.is_file()
        assert _sha256(child_set) == child_set_digest
        assert _sha256(orch_set) == orch_set_digest

        # 3. artifact_meta.write_legacy
        with pytest.raises(ValueError):
            meta.write_legacy(
                child_set,
                [{"op": "note", "message": "should refuse"}],
                record_type="plans",
                render=meta.LegacyRender("same-status", DAY, bad_actor, history=True),
                repo_root=repo_set,
                project_context=meta.legacy_context(repo_set),
            )
        assert _sha256(child_set) == child_set_digest

        # 4. artifact_meta.render_legacy_text (actor_label and checked_by)
        child_text = child_set.read_text(encoding="utf-8")
        with pytest.raises(ValueError):
            meta.render_legacy_text(
                child_text,
                [{"op": "note", "message": "should refuse"}],
                record_type="ipd",
                render=meta.LegacyRender("same-status", DAY, bad_actor, history=True),
                repo_root=repo_set,
            )
        with pytest.raises(ValueError):
            meta.render_legacy_text(
                child_text,
                [
                    {
                        "op": "coverage",
                        "coverage": "pass",
                        "coverage_fingerprint": "abc123",
                    }
                ],
                record_type="ipd",
                render=meta.LegacyRender(
                    "coverage pass",
                    DAY,
                    "aw oc run",
                    checked_by=bad_actor,
                    history=True,
                ),
                repo_root=repo_set,
            )
    finally:
        lifecycle.clear_checkout_control_root_cache()


def test_hand_retired_child_preserves_retired_banner_for_audit(tmp_path: Path) -> None:
    repo = _init_plans_git_repo(tmp_path, "banner_repo")
    orch_path, child_path = _write_set_fixtures(
        repo,
        setid="bnset",
        orch_id6="orc040",
        child_id6="chd040",
        orch_status="to-review",
        child_status="to-review",
        child_bucket="pending",
        approval_line=None,
        top_body_banner="RETIRED 2026-11-13: superseded by sibling",
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

    rc = cli.main(
        [
            "set",
            "superseded",
            "chd040",
            "-m",
            "superseded by sibling",
            "--yes",
            "--no-commit",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0

    dest_path = repo / ".aw" / "records" / "plans" / "superseded" / child_path.name
    assert dest_path.is_file()
    assert not child_path.exists()
    dest_text = dest_path.read_text(encoding="utf-8")
    assert "RETIRED 2026-11-13: superseded by sibling" in dest_text
    assert audit._has_retired_banner(dest_path) is True
    assert "child chd040 retired superseded" in orch_path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------------------
# 4sd62s AC-21 (Section 4.4a obligations) and AC-6 Phase-B git diff checks (xexn45 E-13)
# --------------------------------------------------------------------------------------


def _invoke_cli_captured(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    *,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str]:
    """Run cli.main(argv) and return (exit_code, stdout, stderr)."""
    capsys.readouterr()
    rc = cli.main(argv)
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


def test_ac21_obligations_find_filters_and_zero_match_exit_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC-21 (wja06w, zyj8io): aw find filtering and zero-match selector exit-2 behavior."""
    repo = _init_plans_git_repo(tmp_path, "ac21_find")
    (repo / ".aw" / "records" / "specs" / "to-review").mkdir(parents=True)
    (repo / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)

    # Create records via the moved artifact_meta writers so the read path exercises them.
    rc_spec, _, err_spec = _invoke_cli_captured(
        monkeypatch,
        [
            "specs",
            "new",
            "--title",
            "Sample Spec",
            "--slug",
            "sample-spec",
            "--apply",
            "--dir",
            str(repo),
        ],
        capsys=capsys,
    )
    assert rc_spec == 0, err_spec

    rc_bkl, _, err_bkl = _invoke_cli_captured(
        monkeypatch,
        [
            "backlog",
            "new",
            "--summary",
            "Sample open item",
            "--priority",
            "medium",
            "--work-kind",
            "chore",
            "--apply",
            "--dir",
            str(repo),
        ],
        capsys=capsys,
    )
    assert rc_bkl == 0, err_bkl

    # wja06w: filtered find queries return matching records and exit 0.
    rc_f_spec, out_f_spec, _ = _invoke_cli_captured(
        monkeypatch,
        ["find", "specs", "--status", "draft", "--dir", str(repo)],
        capsys=capsys,
    )
    assert rc_f_spec == 0
    assert "sample-spec" in out_f_spec

    rc_f_bkl, out_f_bkl, _ = _invoke_cli_captured(
        monkeypatch,
        ["find", "backlog", "--status", "open", "--dir", str(repo)],
        capsys=capsys,
    )
    assert rc_f_bkl == 0
    assert "Sample open item" in out_f_bkl or "sample-open-item" in out_f_bkl

    # zyj8io: nonexistent selector exits 2, while an empty tree with no selector exits 0.
    rc_empty, _, _ = _invoke_cli_captured(
        monkeypatch, ["find", "plans", "--dir", str(repo)], capsys=capsys
    )
    assert rc_empty == 0

    rc_miss, _, err_miss = _invoke_cli_captured(
        monkeypatch, ["find", "plans", "zzzzzz", "--dir", str(repo)], capsys=capsys
    )
    assert rc_miss == 2
    assert "zzzzzz" in err_miss


def test_ac21_obligations_graduation_forward_and_origin_links(tmp_path: Path) -> None:
    """AC-21 (pw2ln3): aw graduation keeps Graduated-To declarations and From-Backlog links distinct."""
    repo = _init_plans_git_repo(tmp_path, "ac21_grad")
    bkl_grad = repo / ".aw" / "records" / "backlog" / "graduated"
    bkl_grad.mkdir(parents=True)
    plans_pend = repo / ".aw" / "records" / "plans" / "pending"

    # 1. Declarations alone: Graduated-To: setfwd, plans carry no From-Backlog.
    (bkl_grad / "20261109-fwdonly-01-bklf01-fwd.backlog.md").write_text(
        "# Backlog: Forward only\n\n- Id: bklf01\n- Status: graduated\n- Graduated-To: setfwd\n",
        encoding="utf-8",
    )
    (plans_pend / "20261109-setfwd-01-plnf01-first.ipd.md").write_text(
        "# IPD: Fwd plan\n\n- Id: plnf01\n- Status: pending\n- Set: setfwd\n- Order: 1\n",
        encoding="utf-8",
    )

    # 2. Origin links alone: no Graduated-To, plan carries From-Backlog: bklr01.
    (bkl_grad / "20261109-revonly-01-bklr01-rev.backlog.md").write_text(
        "# Backlog: Reverse only\n\n- Id: bklr01\n- Status: graduated\n",
        encoding="utf-8",
    )
    (plans_pend / "20261109-setrev-01-plnr01-first.ipd.md").write_text(
        "# IPD: Rev plan\n\n- Id: plnr01\n- Status: pending\n- From-Backlog: bklr01\n- Set: setrev\n- Order: 1\n",
        encoding="utf-8",
    )

    # 3. Both sources: Graduated-To and From-Backlog agree on setboth.
    (bkl_grad / "20261109-both-01-bklb01-both.backlog.md").write_text(
        "# Backlog: Both\n\n- Id: bklb01\n- Status: graduated\n- Graduated-To: setboth\n",
        encoding="utf-8",
    )
    (plans_pend / "20261109-setboth-01-plnb01-first.ipd.md").write_text(
        "# IPD: Both plan\n\n- Id: plnb01\n- Status: pending\n- From-Backlog: bklb01\n- Set: setboth\n- Order: 1\n",
        encoding="utf-8",
    )

    c_fwd = check_engine.graduation_cluster(repo, "bklf01")
    assert c_fwd.forward_setids == ("setfwd",)
    assert [a.id6 for a in c_fwd.forward_artifacts] == ["plnf01"]
    assert c_fwd.artifact_count == 0

    c_rev = check_engine.graduation_cluster(repo, "bklr01")
    assert c_rev.forward_setids == ()
    assert c_rev.forward_count == 0
    assert [a.id6 for a in c_rev.artifacts] == ["plnr01"]

    c_both = check_engine.graduation_cluster(repo, "bklb01")
    assert c_both.forward_setids == ("setboth",)
    assert [a.id6 for a in c_both.forward_artifacts] == ["plnb01"]
    assert [a.id6 for a in c_both.artifacts] == ["plnb01"]


def test_ac21_obligations_readiness_absence_and_setters_use_artifact_meta(
    tmp_path: Path,
) -> None:
    """AC-21 (l56tyz, fhinri, 63zo2f): readiness absence refused and unified setters use artifact_meta."""
    repo = _init_plans_git_repo(tmp_path, "ac21_setters")
    (repo / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)
    (repo / ".aw" / "records" / "backlog" / "done").mkdir(parents=True)
    (repo / ".aw" / "records" / "specs" / "to-review").mkdir(parents=True)
    (repo / ".aw" / "records" / "specs" / "reviewed").mkdir(parents=True)

    # l56tyz: backfilled - Readiness: with no review verdict still fails auto-approve check.
    absent_plan = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261109-demo-01-plnabs-absent.ipd.md"
    )
    absent_plan.write_text(
        "# IPD: Field Absent\n\n"
        "- Id: plnabs\n"
        "- Status: reviewed\n"
        "- Readiness: go-pending-approval\n\n"
        "## Workflow history\n\n"
        "- 2026-11-09 draft (author): created.\n",
        encoding="utf-8",
    )
    assert pr.is_plan_review_approved(absent_plan) is False

    # 63zo2f + fhinri: both backlog setter spellings (aw backlog set / aw set) write via artifact_meta,
    # and aw specs set refuses ->reviewed without an attested review verdict.
    b1 = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / "open"
        / "20261109-bkl001-01-bkl001-one.backlog.md"
    )
    b1.write_text(
        "# Backlog: One\n\n- Id: bkl001\n- Date: 2026-11-09\n- Status: open\n- Priority: medium\n- Work-Kind: chore\n\n## Workflow history\n\n- 2026-11-09 open (tester): created.\n",
        encoding="utf-8",
    )
    b2 = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / "open"
        / "20261109-bkl002-01-bkl002-two.backlog.md"
    )
    b2.write_text(
        "# Backlog: Two\n\n- Id: bkl002\n- Date: 2026-11-09\n- Status: open\n- Priority: medium\n- Work-Kind: chore\n\n## Workflow history\n\n- 2026-11-09 open (tester): created.\n",
        encoding="utf-8",
    )
    s1 = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / "to-review"
        / "20261109-spc001-01-spc001-spec.spec.md"
    )
    s1.write_text(
        "# Spec: Sample\n\n- Id: spc001\n- Date: 2026-11-09\n- Status: to-review\n- Author: tester\n\n## Workflow history\n\n- 2026-11-09 to-review (tester): created.\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

    rc_b1 = cli.main(
        [
            "backlog",
            "set",
            "done",
            "bkl001",
            "--message",
            "closed",
            "--no-commit",
            "--dir",
            str(repo),
        ]
    )
    rc_b2 = cli.main(
        [
            "set",
            "done",
            "bkl002",
            "--message",
            "closed",
            "--no-commit",
            "--dir",
            str(repo),
        ]
    )
    assert rc_b1 == 0
    assert rc_b2 == 0
    assert (repo / ".aw" / "records" / "backlog" / "done" / b1.name).is_file()
    assert (repo / ".aw" / "records" / "backlog" / "done" / b2.name).is_file()
    st_b1 = meta.read("bkl001", project_context=meta.legacy_context(repo))
    st_b2 = meta.read("bkl002", project_context=meta.legacy_context(repo))
    assert st_b1.status == "done"
    assert st_b2.status == "done"

    # Unattested spec -> reviewed is refused on aw specs set too.
    rc_s1 = cli.main(
        [
            "specs",
            "set",
            "reviewed",
            "spc001",
            "--message",
            "unattested",
            "--no-commit",
            "--dir",
            str(repo),
        ]
    )
    assert rc_s1 != 0
    assert s1.is_file()


def _hunk_change_lines(diff_text: str) -> tuple[list[str], list[str]]:
    """Return (removed_lines, added_lines) excluding git diff file/hunk headers."""
    removed: list[str] = []
    added: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith(
            ("--- ", "+++ ", "@@ ", "diff --git ", "rename ", "similarity ", "index ")
        ):
            continue
        if line.startswith("-"):
            removed.append(line[1:])
        elif line.startswith("+"):
            added.append(line[1:])
    return removed, added


def test_ac6_phase_b_backlog_done_git_diff(tmp_path: Path) -> None:
    """AC-6 phase-B (E-13 b i): open non-blocking backlog -> done diff is strictly status + 1 history line."""
    repo = support.init_repo(tmp_path / "bkl_ac6")
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    (repo / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)
    (repo / ".aw" / "records" / "backlog" / "done").mkdir(parents=True)
    (repo / ".aw" / "state").mkdir(parents=True)

    bkl_path = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / "open"
        / "20261109-ac6bkl-01-ac6bkl-item.backlog.md"
    )
    bkl_path.write_text(
        "# Backlog: AC-6 non-blocking item\n\n"
        "- Id: ac6bkl\n"
        "- Date: 2026-11-09\n"
        "- Status: open\n"
        "- Priority: medium\n"
        "- Work-Kind: chore\n\n"
        "## Workflow history\n\n"
        "- 2026-11-09 open (tester): created.\n\n"
        "## Summary\n\n"
        "Simple non-blocking chore.\n",
        encoding="utf-8",
        newline="\n",
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init backlog"], cwd=repo, check=True)

    rc = cli.main(
        [
            "backlog",
            "set",
            "done",
            "ac6bkl",
            "--message",
            "closed",
            "--commit",
            "--dir",
            str(repo),
        ]
    )
    assert rc == 0

    diff_proc = subprocess.run(
        ["git", "diff", "-M", "-U0", "HEAD~1", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    removed, added = _hunk_change_lines(diff_proc.stdout)
    assert removed == ["- Status: open"]
    assert len(added) == 2
    assert added[0] == "- Status: done"
    assert (
        added[1].startswith("- ")
        and "done (" in added[1]
        and added[1].endswith(": closed")
    )
    assert not any("Scope-" in ln or "Close-Evidence" in ln for ln in added + removed)


def test_ac6_phase_b_ipd_finalize_within_and_out_of_scope_git_diff(
    tmp_path: Path,
) -> None:
    """AC-6 phase-B (E-13 b ii): within-scope and out-of-scope finalize diffs match exact Phase-B rules."""
    lifecycle.clear_checkout_control_root_cache()
    try:
        for case_name, out_of_scope in (
            ("within_scope", False),
            ("out_of_scope", True),
        ):
            repo = support.init_repo(tmp_path / case_name)
            (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
            for sub in ("pending", "executed", "superseded", "not-executed"):
                (repo / ".aw" / "records" / "plans" / sub).mkdir(parents=True)
            (repo / ".aw" / "records" / "reviews").mkdir(parents=True)
            (repo / ".aw" / "state").mkdir(parents=True)
            (repo / "agent_workflows").mkdir(parents=True)
            (repo / "agent_workflows" / "demo.py").write_text("v1\n", encoding="utf-8")

            plan_id = "ac6in1" if not out_of_scope else "ac6ex1"
            plan_name = f"20261109-demo-01-{plan_id}-sample.ipd.md"
            plan_path = repo / ".aw" / "records" / "plans" / "pending" / plan_name
            plan_text = support.ready_plan_text(
                plan_id=plan_id,
                set_name="demo",
                order=1,
                status="approved",
                scope_paths="agent_workflows/demo.py",
                approval="2026-11-12, recorded via aw ipd set: approved",
            )
            plan_text = (
                plan_text.replace("- [ ] E-01 ", "- [x] E-01 ", 1)
                .replace(
                    "  - Execution state: pending", "  - Execution state: performed", 1
                )
                .replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
                .replace(
                    "  - Observed evidence:\n",
                    "  - Observed evidence: done, verified.\n",
                    1,
                )
                .replace("  - Result: pending", "  - Result: pass", 1)
            )
            plan_path.write_text(plan_text, encoding="utf-8", newline="\n")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "init plan"], cwd=repo, check=True)

            with support.coordinator_role():
                b_res = lifecycle.begin(
                    repo, plan_path, "tester", timestamp="2026-11-12T00:00:00Z"
                )
                assert b_res.exit_code == lifecycle.EXIT_OK, b_res.message

                (repo / "agent_workflows" / "demo.py").write_text(
                    "v2\n", encoding="utf-8"
                )
                if out_of_scope:
                    (repo / "extra.py").write_text("extra = 1\n", encoding="utf-8")
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(["git", "commit", "-qm", "work"], cwd=repo, check=True)

                argv = [
                    "ipd",
                    "finalize",
                    plan_id,
                    "--actor",
                    "tester",
                    "-m",
                    "done",
                    "--apply",
                    "--dir",
                    str(repo),
                ]
                if out_of_scope:
                    argv.extend(["--scope-reason", "extra.py=needed helper"])
                rc = cli.main(argv)
                assert rc == 0

            diff_proc = subprocess.run(
                ["git", "diff", "-M", "-U0", "HEAD~1", "HEAD"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            assert (
                f"rename from .aw/records/plans/pending/{plan_name}" in diff_proc.stdout
            )
            assert (
                f"rename to .aw/records/plans/executed/{plan_name}" in diff_proc.stdout
            )
            removed, added = _hunk_change_lines(diff_proc.stdout)
            assert removed == [
                "- Status: approved",
                "- Approval: 2026-11-12, recorded via aw ipd set: approved",
            ]
            if not out_of_scope:
                assert len(added) == 2
                assert added[0] == "- Status: executed"
                assert added[1].startswith("- ") and "executed (" in added[1]
                assert not any("Scope-Exceeded" in ln for ln in added + removed)
            else:
                assert len(added) == 3
                assert added[0] == "- Scope-Exceeded: extra.py (needed helper)"
                assert added[1] == "- Status: executed"
                assert added[2].startswith("- ") and "executed (" in added[2]
    finally:
        lifecycle.clear_checkout_control_root_cache()

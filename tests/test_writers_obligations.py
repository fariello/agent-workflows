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
from agent_workflows import cli
from agent_workflows import coverage_record as cov_rec
from agent_workflows import ipd_lifecycle as lifecycle
from agent_workflows import ipd_schema as schema
from agent_workflows import plan_readiness as pr
from agent_workflows import review_findings as rf

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

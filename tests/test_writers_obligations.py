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

from agent_workflows import artifact_meta as meta
from agent_workflows import coverage_record as cov_rec
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

"""Behavioral tests pinning the readiness absence invariant.

Asserts the four properties underlying the decision not to backfill the optional
`- Readiness:` front-matter field onto pending plans:
1. Corpus partition: no tracked plan under `.aw/records/plans/` at `draft` or `to-review`
   carries a `- Readiness:` field.
2. Linter refusal: inserting `- Readiness: go-pending-approval` onto a field-absent pending
   plan yields a blocking IPD-M107 diagnostic.
3. Auto-approve predicate: `is_plan_review_approved` returns False both before and after
   a backfill without history, and returns True on a field-absent plan when an approving
   review record exists in history (fallback arm).
4. Recheck verb: `recheck_conditions` reports `may_write=False` refusing an absent field.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
from typing import List, Optional

import pytest

from agent_workflows import ipd_lint, plan_readiness

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_tracked_or_all_plans(plans_dir: Path) -> List[Path]:
    """Return tracked .ipd.md files under plans_dir, falling back to rglob."""
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "-z", str(plans_dir)],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        files = [Path(p) for p in out.split("\0") if p.endswith(".ipd.md")]
        if files:
            resolved = []
            for f in files:
                p = f if f.is_absolute() else (REPO_ROOT / f)
                if p.exists():
                    resolved.append(p)
            if resolved:
                return sorted(resolved)
    except Exception:
        pass
    return sorted(plans_dir.rglob("*.ipd.md"))


def check_corpus_partition(plans_dir: Path) -> List[str]:
    """Scan .ipd.md files under plans_dir and return paths of draft or to-review plans carrying - Readiness:."""
    violations: List[str] = []
    plans = get_tracked_or_all_plans(plans_dir)
    for p in plans:
        text = p.read_text(encoding="utf-8")
        doc = ipd_lint.parse(text)
        status = (doc.meta_fields.get("Status") or "").strip().lower()
        if status in (
            "draft",
            "to-review",
        ) and plan_readiness._READINESS_FIELD_PRESENT_RE.search(text):
            violations.append(str(p))
    return violations


def find_field_absent_pending_plan(repo_root: Path) -> Optional[Path]:
    """Scan .aw/records/plans/pending/ for a pending plan lacking a - Readiness: field."""
    pending_dir = repo_root / ".aw" / "records" / "plans" / "pending"
    if not pending_dir.exists():
        return None
    for p in sorted(pending_dir.glob("*.ipd.md")):
        text = p.read_text(encoding="utf-8")
        if not plan_readiness._READINESS_FIELD_PRESENT_RE.search(text):
            return p
    return None


def test_corpus_partition_pre_review_plans_lack_readiness_field():
    """Property 1: no tracked plan under .aw/records/plans/ at draft or to-review carries - Readiness:."""
    plans_dir = REPO_ROOT / ".aw" / "records" / "plans"
    assert plans_dir.is_dir(), f"Plans directory not found at {plans_dir}"
    violations = check_corpus_partition(plans_dir)
    assert not violations, (
        f"Corpus partition violation: found {len(violations)} draft/to-review plan(s) "
        f"carrying - Readiness: field: {violations}"
    )


def test_linter_refuses_backfilled_readiness_field_with_m107():
    """Property 2: lint_text yields a blocking IPD-M107 diagnostic upon simulated backfill."""
    subject = find_field_absent_pending_plan(REPO_ROOT)
    if subject is None:
        pytest.skip("No field-absent pending plan found in .aw/records/plans/pending")

    orig_text = subject.read_text(encoding="utf-8")
    res_orig = ipd_lint.lint_text(orig_text, checkpoint="author", directory="pending")
    assert res_orig.disposition == "conforming", (
        f"Expected unmodified subject {subject.name} to be conforming, got {res_orig.disposition}: "
        f"{[d.code for d in res_orig.diagnostics]}"
    )
    assert not any(
        d.code == ipd_lint.C_READINESS_UNATTESTED for d in res_orig.diagnostics
    )

    backfilled_text = re.sub(
        r"(^-\s*Status:\s*.*$)",
        r"\1\n- Readiness: go-pending-approval",
        orig_text,
        count=1,
        flags=re.MULTILINE,
    )
    res_backfilled = ipd_lint.lint_text(
        backfilled_text, checkpoint="author", directory="pending"
    )
    assert (
        res_backfilled.disposition == "error"
    ), f"Expected backfilled text to produce error disposition, got {res_backfilled.disposition}"
    m107_diags = [
        d
        for d in res_backfilled.diagnostics
        if d.code == ipd_lint.C_READINESS_UNATTESTED
    ]
    assert (
        len(m107_diags) == 1
    ), f"Expected exactly 1 IPD-M107 diagnostic, got {len(m107_diags)}: {res_backfilled.diagnostics}"
    assert "REVIEW OUTPUT but no review verdict appears" in m107_diags[0].message


def test_auto_approve_predicate_refuses_backfill_and_exercises_fallback(tmp_path: Path):
    """Property 3: is_plan_review_approved returns False before/after backfill, and True with approving history."""
    # tmp_path is required because is_plan_review_approved takes a Path rather than text.
    subject = find_field_absent_pending_plan(REPO_ROOT)
    if subject is None:
        pytest.skip("No field-absent pending plan found in .aw/records/plans/pending")

    orig_text = subject.read_text(encoding="utf-8")

    # 1. Unmodified field-absent plan -> False
    f_orig = tmp_path / "orig.ipd.md"
    f_orig.write_text(orig_text, encoding="utf-8")
    assert plan_readiness.is_plan_review_approved(f_orig) is False

    # 2. Simulated backfill without review record in history -> False
    backfilled_text = re.sub(
        r"(^-\s*Status:\s*.*$)",
        r"\1\n- Readiness: go-pending-approval",
        orig_text,
        count=1,
        flags=re.MULTILINE,
    )
    f_backfill = tmp_path / "backfill.ipd.md"
    f_backfill.write_text(backfilled_text, encoding="utf-8")
    assert plan_readiness.is_plan_review_approved(f_backfill) is False

    # 3. Field-absent plan with approving review record in history -> True (fallback arm)
    history_approved_text = re.sub(
        r"(## Workflow history\s*\n)",
        r"\1- 2026-09-29 reviewed (reviewer): /plan-review: APPROVE WITH REVISIONS APPLIED\n",
        orig_text,
        count=1,
    )
    f_history = tmp_path / "history_approved.ipd.md"
    f_history.write_text(history_approved_text, encoding="utf-8")
    assert plan_readiness.is_plan_review_approved(f_history) is True


def test_recheck_verb_refuses_field_absent_plan(tmp_path: Path):
    """Property 4: recheck_conditions reports may_write=False with an absent-field refusal."""
    # tmp_path and a temporary git repo are required because recheck_conditions takes (repo_root, plan_path).
    subject = find_field_absent_pending_plan(REPO_ROOT)
    if subject is None:
        pytest.skip("No field-absent pending plan found in .aw/records/plans/pending")

    orig_text = subject.read_text(encoding="utf-8")

    subprocess.check_call(["git", "init", "-q"], cwd=tmp_path)
    pending_dir = tmp_path / ".aw" / "records" / "plans" / "pending"
    pending_dir.mkdir(parents=True)
    plan_path = pending_dir / subject.name
    plan_path.write_text(orig_text, encoding="utf-8")

    result = plan_readiness.recheck_conditions(tmp_path, plan_path)
    assert result.may_write is False
    assert result.readiness_present is False
    assert result.readiness is None
    assert any("the plan has NO `- Readiness:` field" in r for r in result.refusals)

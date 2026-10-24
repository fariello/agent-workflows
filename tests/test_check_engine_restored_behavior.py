"""Restored behavioral tests for check_engine keys under backlog lzg859, findings wo21z5, plan p79jts.

Guards check_plan_priority_required, _plan_disposition, and check_ipd_draft_ready in the core test tier.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agent_workflows import check_engine as ce
from tests.test_plan_priority_required import _build_test_plan

pytestmark = pytest.mark.core


def test_check_plan_priority_required_reports_only_approved_plans_missing_fields() -> (
    None
):
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        pending = repo / ".aw" / "records" / "plans" / "pending"
        executed = repo / ".aw" / "records" / "plans" / "executed"
        pending.mkdir(parents=True)
        executed.mkdir(parents=True)

        (pending / "20260924-testset-01-tst001-a.ipd.md").write_text(
            _build_test_plan(status="approved", plan_id="tst001"),
            encoding="utf-8",
        )
        (pending / "20260924-testset-01-tst002-b.ipd.md").write_text(
            _build_test_plan(
                status="approved",
                priority="high",
                work_kind="chore",
                plan_id="tst002",
            ),
            encoding="utf-8",
        )
        (pending / "20260924-testset-01-tst003-c.ipd.md").write_text(
            _build_test_plan(status="to-review", plan_id="tst003"),
            encoding="utf-8",
        )
        (pending / "20260924-testset-01-tst004-d.ipd.md").write_text(
            _build_test_plan(
                status="approved",
                priority="grandfathered",
                work_kind="grandfathered",
                plan_id="tst004",
            ),
            encoding="utf-8",
        )

        res = [
            (Path(d.location).name, d.rule, d.recovery)
            for d in ce.check_plan_priority_required(repo)
        ]
        assert res == [
            (
                "20260924-testset-01-tst001-a.ipd.md",
                "check.ipd-priority-required",
                "aw ipd set tst001 --priority <low|medium|high>",
            ),
            (
                "20260924-testset-01-tst001-a.ipd.md",
                "check.ipd-work-kind-required",
                "aw ipd set tst001 --work-kind <bug|feature|chore|security|followup>",
            ),
        ]


def test_plan_disposition_is_the_first_component_under_the_plans_dir() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        plans_dir = repo / ".aw" / "records" / "plans"
        cases = (
            ("executed/x.ipd.md", "executed"),
            ("executed/202608/x.ipd.md", "executed"),
            ("superseded/202601/x.ipd.md", "superseded"),
            ("not-executed/202608/x.ipd.md", "not-executed"),
            ("pending/202608/x.ipd.md", "pending"),
            ("z.ipd.md", None),
        )
        for rel, expected in cases:
            path = plans_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("stub", encoding="utf-8")
            assert ce._plan_disposition(repo, path) == expected

        not_a_plan = repo / "not-a-plan-dir" / "other.ipd.md"
        not_a_plan.parent.mkdir(parents=True, exist_ok=True)
        not_a_plan.write_text("stub", encoding="utf-8")
        assert ce._plan_disposition(repo, not_a_plan) is None


def test_check_ipd_draft_ready_nudges_only_a_finished_pending_draft() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        pending = repo / ".aw" / "records" / "plans" / "pending"
        executed = repo / ".aw" / "records" / "plans" / "executed"
        pending.mkdir(parents=True)
        executed.mkdir(parents=True)

        (pending / "20260924-testset-01-tst001-a.ipd.md").write_text(
            _build_test_plan(
                status="draft",
                priority="low",
                work_kind="chore",
                plan_id="tst001",
            ),
            encoding="utf-8",
        )
        (pending / "20260924-testset-01-tst002-b.ipd.md").write_text(
            _build_test_plan(
                status="draft",
                priority="unresolved",
                work_kind="unresolved",
                plan_id="tst002",
            ),
            encoding="utf-8",
        )
        (pending / "20260924-testset-01-tst003-c.ipd.md").write_text(
            _build_test_plan(status="to-review", plan_id="tst003"),
            encoding="utf-8",
        )
        (executed / "20260924-testset-01-tst004-d.ipd.md").write_text(
            _build_test_plan(status="draft", plan_id="tst004"),
            encoding="utf-8",
        )

        res = [
            (Path(d.location).name, d.rule, d.recovery)
            for d in ce.check_ipd_draft_ready(repo)
        ]
        assert res == [
            (
                "20260924-testset-01-tst001-a.ipd.md",
                "check.ipd-draft-ready-to-review",
                "aw ipd set to-review tst001",
            ),
        ]

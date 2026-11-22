"""Behavioral pinning tests for ipd_lint metadata and history readers (IPD 1suzlp E-01).

Pins observable verdicts of `agent_workflows.ipd_lint` on a `tmp_path` fixture repository
before moving `ipd_lint` metadata and history reads onto `artifact_meta`: one conforming
and one refused fixture each for `IPD-S405`, `IPD-M107`, `IPD-M112`, `IPD-M113`, and
`IPD-M105`. Calls real `ipd_lint.lint_file` and `ipd_lint.lint_text` functions and never
reads production source.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_workflows import ipd_lint as L
from agent_workflows import ipd_schema as S
from agent_workflows import plans as P
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core


def _build_plan_text(
    *,
    id6: str = "pin001",
    date: str = "2026-10-01",
    status: str = "to-review",
    readiness: str | None = None,
    approval: str | None = None,
    raw_fields: dict[str, object] | None = None,
    history_lines: tuple[str, ...] = ("- 2026-10-01 to-review (tester): created.",),
    e_checked: bool = False,
    e_state: str = "pending",
    v_checked: bool = False,
    v_evidence: str = "",
    v_result: str = "pending",
) -> str:
    e_mark = "x" if e_checked else " "
    v_mark = "x" if v_checked else " "
    v_obs = f" {v_evidence}" if v_evidence else ""
    eff_raw: dict[str, object] = {
        "Concern": "pin ipd_lint metadata and history readers.",
        "Scope": "pin fixture verdicts for 1suzlp.",
        "Scope-Paths": None,
        "Item-Dependencies": None,
    }
    if raw_fields:
        eff_raw.update(raw_fields)
    valid_status = status if status in P.RECOGNIZED else "executed"
    if valid_status != status:
        eff_raw["Status"] = status
    body = (
        "## Goal\n\nPin linter verdicts.\n\n"
        "## Detailed Implementation Checklist (TODO)\n\n"
        "Execution-state rule: mark performed only after doing it.\n\n"
        "### Task group 1: pin\n\n"
        f"- [{e_mark}] E-01 perform sample step.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: sample outcome exists.\n"
        f"  - Execution state: {e_state}\n\n"
        "## Project conventions discovered (Step 0)\n\n- x\n\n"
        "## Findings\n\n- x\n\n"
        "## Proposed changes (ordered, validatable)\n\n- x\n\n"
        "## Deferred / out of scope (with reason)\n\n- x\n\n"
        "## Scope check\n\n- x\n\n"
        "## Required tests / validation\n\n- x\n\n"
        "## Spec / documentation sync\n\n- x\n\n"
        "## Open questions\n\n"
        "### OQ-01: sample question\n\n"
        "- Blocking: no\n"
        "- Status: open\n"
        "- Owner: none\n"
        "- Resolution or deferral rationale: n/a\n\n"
        "## Validation and cross-check (verify before reporting done)\n\n"
        "Validation-state rule: inspect evidence separately.\n\n"
        f"- [{v_mark}] V-01 validates E-01\n"
        "  - Required evidence: sample outcome verified.\n"
        f"  - Observed evidence:{v_obs}\n"
        f"  - Result: {v_result}\n\n"
        "## Approval and execution gate\n\n"
        "- Size assessment: standard\n"
        "- Cohesion rationale: not required\n\n"
        "Gate prose."
    )
    return str(
        RecordBuilder().plan(
            title=f"sample plan {id6}",
            when=date,
            plan_role="child",
            status=valid_status,
            work_kind="chore",
            priority="medium",
            set="pinset",
            order=1,
            highest_e_allocated="01",
            author="tester",
            id6=id6,
            readiness=readiness,
            approval=approval,
            history=list(history_lines),
            body=body,
            raw_fields=eff_raw,
            text_only=True,
        )
    )


def _write_tracked_plan(
    tmp_path: Path,
    *,
    subdir: str,
    id6: str,
    slug: str,
    text: str,
    date_prefix: str = "20261001",
) -> Path:
    repo = tmp_path / "repo"
    (repo / ".aw" / "state").mkdir(parents=True, exist_ok=True)
    plan_dir = repo / ".aw" / "records" / "plans" / subdir
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / f"{date_prefix}-pinset-01-{id6}-{slug}.ipd.md"
    plan_path.write_text(text, encoding="utf-8")
    return plan_path


def _codes(res: L.LintResult) -> list[str]:
    return [d.code for d in res.diagnostics]


def test_ipd_s405_conforming(tmp_path: Path) -> None:
    """IPD-S405 conforming: executed plan with matching executed history passes post-transition."""
    text = _build_plan_text(
        id6="s405ok",
        status="executed",
        history_lines=(
            "- 2026-10-02 executed (tester/model): completed sample step.",
            "- 2026-10-01 to-review (tester): created.",
        ),
        e_checked=True,
        e_state="performed",
        v_checked=True,
        v_evidence="verified sample output.",
        v_result="pass",
    )
    plan_path = _write_tracked_plan(
        tmp_path, subdir="executed", id6="s405ok", slug="s405-ok", text=text
    )

    res_file = L.lint_file(plan_path, checkpoint="post-transition")
    res_text = L.lint_text(text, checkpoint="post-transition", directory="executed")

    assert res_file.disposition == S.DISPOSITION_CONFORMING
    assert L.C_EXEC_HISTORY not in _codes(res_file)
    assert res_text.disposition == S.DISPOSITION_CONFORMING
    assert L.C_EXEC_HISTORY not in _codes(res_text)


def test_ipd_s405_refused(tmp_path: Path) -> None:
    """IPD-S405 refused: executed plan lacking an executed history entry fails post-transition."""
    text = _build_plan_text(
        id6="s405no",
        status="executed",
        history_lines=("- 2026-10-01 to-review (tester): created.",),
        e_checked=True,
        e_state="performed",
        v_checked=True,
        v_evidence="verified sample output.",
        v_result="pass",
    )
    plan_path = _write_tracked_plan(
        tmp_path, subdir="executed", id6="s405no", slug="s405-no", text=text
    )

    res_file = L.lint_file(plan_path, checkpoint="post-transition")
    res_text = L.lint_text(text, checkpoint="post-transition", directory="executed")

    assert res_file.disposition == S.DISPOSITION_ERROR
    assert L.C_EXEC_HISTORY in _codes(res_file)
    assert res_text.disposition == S.DISPOSITION_ERROR
    assert L.C_EXEC_HISTORY in _codes(res_text)


def test_ipd_m107_conforming(tmp_path: Path) -> None:
    """IPD-M107 conforming: Readiness present with a review verdict in workflow history."""
    text = _build_plan_text(
        id6="m107ok",
        status="reviewed",
        readiness="go-pending-approval",
        history_lines=(
            "- 2026-10-02 reviewed (reviewer): /plan-review: APPROVE WITH REVISIONS APPLIED.",
            "- 2026-10-01 to-review (tester): created.",
        ),
    )
    plan_path = _write_tracked_plan(
        tmp_path, subdir="pending", id6="m107ok", slug="m107-ok", text=text
    )

    res_file = L.lint_file(plan_path, checkpoint="author")
    res_text = L.lint_text(text, checkpoint="author", directory="pending")

    assert res_file.disposition == S.DISPOSITION_CONFORMING
    assert L.C_READINESS_UNATTESTED not in _codes(res_file)
    assert res_text.disposition == S.DISPOSITION_CONFORMING
    assert L.C_READINESS_UNATTESTED not in _codes(res_text)


def test_ipd_m107_refused(tmp_path: Path) -> None:
    """IPD-M107 refused: hand-written Readiness without any review entry in workflow history."""
    text = _build_plan_text(
        id6="m107no",
        status="to-review",
        readiness="go-pending-approval",
        history_lines=("- 2026-10-01 to-review (tester): created.",),
    )
    plan_path = _write_tracked_plan(
        tmp_path, subdir="pending", id6="m107no", slug="m107-no", text=text
    )

    res_file = L.lint_file(plan_path, checkpoint="author")
    res_text = L.lint_text(text, checkpoint="author", directory="pending")

    assert res_file.disposition == S.DISPOSITION_ERROR
    assert L.C_READINESS_UNATTESTED in _codes(res_file)
    assert res_text.disposition == S.DISPOSITION_ERROR
    assert L.C_READINESS_UNATTESTED in _codes(res_text)


def test_ipd_m112_conforming(tmp_path: Path) -> None:
    """IPD-M112 conforming: complete coverage trio attested by matching coverage history line."""
    fp = "deadbeef1234567890abcdef1234567890abcdef"
    text = _build_plan_text(
        id6="m112ok",
        status="to-review",
        raw_fields={
            "Coverage": "pass",
            "Coverage-Fingerprint": fp,
            "Coverage-Checked": "2026-10-02 by tester/model",
        },
        history_lines=(
            f"- 2026-10-02 coverage pass (aw oc run): fingerprint {fp[:12]}, model tester/model",
            "- 2026-10-01 to-review (tester): created.",
        ),
    )
    plan_path = _write_tracked_plan(
        tmp_path, subdir="pending", id6="m112ok", slug="m112-ok", text=text
    )

    res_file = L.lint_file(plan_path, checkpoint="author")
    res_text = L.lint_text(text, checkpoint="author", directory="pending")

    assert res_file.disposition == S.DISPOSITION_CONFORMING
    assert L.C_COVERAGE_RECORD not in _codes(res_file)
    assert res_text.disposition == S.DISPOSITION_CONFORMING
    assert L.C_COVERAGE_RECORD not in _codes(res_text)


def test_ipd_m112_refused(tmp_path: Path) -> None:
    """IPD-M112 refused: coverage trio without matching coverage line in workflow history."""
    fp = "deadbeef1234567890abcdef1234567890abcdef"
    text = _build_plan_text(
        id6="m112no",
        status="to-review",
        raw_fields={
            "Coverage": "pass",
            "Coverage-Fingerprint": fp,
            "Coverage-Checked": "2026-10-02 by tester/model",
        },
        history_lines=("- 2026-10-01 to-review (tester): created.",),
    )
    plan_path = _write_tracked_plan(
        tmp_path, subdir="pending", id6="m112no", slug="m112-no", text=text
    )

    res_file = L.lint_file(plan_path, checkpoint="author")
    res_text = L.lint_text(text, checkpoint="author", directory="pending")

    assert res_file.disposition == S.DISPOSITION_ERROR
    assert L.C_COVERAGE_RECORD in _codes(res_file)
    assert res_text.disposition == S.DISPOSITION_ERROR
    assert L.C_COVERAGE_RECORD in _codes(res_text)


def test_ipd_m113_conforming(tmp_path: Path) -> None:
    """IPD-M113 conforming: reviewed plan carrying structured Readiness passes."""
    text = _build_plan_text(
        id6="m113ok",
        status="reviewed",
        readiness="go-pending-approval",
        history_lines=(
            "- 2026-10-02 reviewed (reviewer): /plan-review: APPROVE.",
            "- 2026-10-01 to-review (tester): created.",
        ),
    )
    plan_path = _write_tracked_plan(
        tmp_path, subdir="pending", id6="m113ok", slug="m113-ok", text=text
    )

    res_file = L.lint_file(plan_path, checkpoint="author")
    res_text = L.lint_text(text, checkpoint="author", directory="pending")

    assert res_file.disposition == S.DISPOSITION_CONFORMING
    assert L.C_READINESS_REQUIRED not in _codes(res_file)
    assert res_text.disposition == S.DISPOSITION_CONFORMING
    assert L.C_READINESS_REQUIRED not in _codes(res_text)


def test_ipd_m113_refused(tmp_path: Path) -> None:
    """IPD-M113 refused: reviewed plan lacking structured Readiness is refused."""
    text = _build_plan_text(
        id6="m113no",
        status="reviewed",
        history_lines=(
            "- 2026-10-02 reviewed (reviewer): /plan-review: APPROVE.",
            "- 2026-10-01 to-review (tester): created.",
        ),
    )
    plan_path = _write_tracked_plan(
        tmp_path, subdir="pending", id6="m113no", slug="m113-no", text=text
    )

    res_file = L.lint_file(plan_path, checkpoint="author")
    res_text = L.lint_text(text, checkpoint="author", directory="pending")

    assert res_file.disposition == S.DISPOSITION_ERROR
    assert L.C_READINESS_REQUIRED in _codes(res_file)
    assert res_text.disposition == S.DISPOSITION_ERROR
    assert L.C_READINESS_REQUIRED in _codes(res_text)


def test_ipd_m105_conforming(tmp_path: Path) -> None:
    """IPD-M105 conforming: post-cutover executed plan in executed/ (including multi-word EXECUTED)."""
    text = _build_plan_text(
        id6="m105ok",
        date="2026-10-01",
        status="executed",
        history_lines=(
            "- 2026-10-02 executed (tester/model): done.",
            "- 2026-10-01 to-review (tester): created.",
        ),
    )
    plan_path = _write_tracked_plan(
        tmp_path, subdir="executed", id6="m105ok", slug="m105-ok", text=text
    )
    res_file = L.lint_file(plan_path, checkpoint="author")
    res_text = L.lint_text(text, checkpoint="author", directory="executed")

    assert res_file.disposition == S.DISPOSITION_LEGACY
    assert L.C_META_PATH not in _codes(res_file)
    assert res_text.disposition == S.DISPOSITION_LEGACY
    assert L.C_META_PATH not in _codes(res_text)

    # Also verify D-1 normalized multi-word EXECUTED via plans.read_status
    multi_text = _build_plan_text(
        id6="m105mw",
        date="2026-10-01",
        status="EXECUTED (approved 2026-10-02)",
    )
    multi_path = _write_tracked_plan(
        tmp_path, subdir="executed", id6="m105mw", slug="m105-mw", text=multi_text
    )
    res_multi_file = L.lint_file(multi_path, checkpoint="author")
    res_multi_text = L.lint_text(multi_text, checkpoint="author", directory="executed")
    assert res_multi_file.disposition == S.DISPOSITION_LEGACY
    assert L.C_META_PATH not in _codes(res_multi_file)
    assert res_multi_text.disposition == S.DISPOSITION_LEGACY
    assert L.C_META_PATH not in _codes(res_multi_text)


def test_ipd_m105_refused(tmp_path: Path) -> None:
    """IPD-M105 refused: post-cutover plan with pre-terminal status sitting in executed/."""
    text = _build_plan_text(
        id6="m105no",
        date="2026-10-01",
        status="approved",
        readiness="go-pending-approval",
        approval="2026-10-01, recorded via aw ipd set: approved",
        history_lines=(
            "- 2026-10-01 reviewed (reviewer): /plan-review: APPROVE.",
            "- 2026-10-01 to-review (tester): created.",
        ),
    )
    plan_path = _write_tracked_plan(
        tmp_path, subdir="executed", id6="m105no", slug="m105-no", text=text
    )

    res_file = L.lint_file(plan_path, checkpoint="author")
    res_text = L.lint_text(text, checkpoint="author", directory="executed")

    assert res_file.disposition == S.DISPOSITION_ERROR
    assert L.C_META_PATH in _codes(res_file)
    assert res_text.disposition == S.DISPOSITION_ERROR
    assert L.C_META_PATH in _codes(res_text)


def test_run_lint_reuses_single_metadata_scan_across_multiple_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_lint over explicit/default paths must share one artifact_meta scan, not N per file."""
    import argparse
    from agent_workflows import artifact_meta as _meta

    paths = []
    for idx in range(5):
        id6 = f"scn00{idx}"
        text = _build_plan_text(id6=id6, date="2026-10-01", status="to-review")
        paths.append(
            str(
                _write_tracked_plan(
                    tmp_path,
                    subdir="pending",
                    id6=id6,
                    slug=f"scan-{idx}",
                    text=text,
                )
            )
        )

    orig_query = _meta.query
    query_calls = 0

    def _counting_query(*args, **kwargs):
        nonlocal query_calls
        query_calls += 1
        return orig_query(*args, **kwargs)

    monkeypatch.setattr(_meta, "query", _counting_query)

    args = argparse.Namespace(
        path=paths,
        phase="author",
        legacy=False,
        detail=False,
        long=False,
        citation_anchors=False,
        no_color=True,
        all=False,
        json=False,
        agent=False,
        human=True,
    )
    rc = L.run_lint(args)
    assert rc == 0
    # Must scan at most once for ipd metadata (plus at most once for set memberships),
    # never O(N) queries across 5 plans.
    assert (
        query_calls <= 2
    ), f"expected <=2 artifact_meta.query calls, got {query_calls}"

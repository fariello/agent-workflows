"""AC-14a (4) of spec 4sd62s: only a GATE review attests a spec's `->reviewed` (plan 2xwb9b E-13).

A `specflow` refinement record improves a spec but never clears it for `reviewed` (4.4 SR-601).
Both setter spellings refuse the transition while the spec's only review record is a refinement,
`aw check all --agent` reports a hand-forced `reviewed` spec as `check.spec-review-unattested`,
and one gate record makes both spellings succeed and the check clean.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
from pathlib import Path

import pytest

from agent_workflows import cli
from agent_workflows import review_findings as rf
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core

SPEC_ID = "gk0001"


def _spec_text(status: str) -> str:
    return RecordBuilder().spec(
        title="Gate kind fixture",
        when="2026-01-01",
        status=status,
        id6=SPEC_ID,
        author="tester",
        history=["- 2026-01-01 to-review (tester): created"],
        body="## Goal\n\nA fixture spec.",
        text_only=True,
    )


def _repo(tmp_path: Path, status: str = "to-review") -> tuple[Path, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    d = root / ".aw" / "records" / "specs" / status
    d.mkdir(parents=True)
    spec = d / f"20260101-{SPEC_ID}-01-{SPEC_ID}-gate-kind.spec.md"
    spec.write_text(_spec_text(status), encoding="utf-8")
    return root, spec


def _round() -> rf.Round:
    return rf.Round(
        number=1,
        findings=(
            rf.Finding(
                id="SR-001",
                severity="low",
                scope="in-scope",
                area="B",
                evidence="spec.md:1",
                finding="a fixture finding",
                remediation_risk="Overall:Low",
                decision="fixed",
                resolution="handled",
            ),
        ),
        decisions=(),
    )


def _review(root: Path, *, slug: str, verdict: str, file_id6: str = SPEC_ID) -> Path:
    """A review record for the fixture spec. A `specflow` refinement record carries its OWN id6 in
    its filename (as the 24 real ones do), a `/spec-review` gate record the subject's."""
    p = (
        root
        / ".aw"
        / "records"
        / "reviews"
        / rf.build_review_name(
            date="20260102", set_id="specflow", order=4, subject_id6=file_id6, slug=slug
        )
    )
    rf.write_review(
        p,
        subject_id=SPEC_ID,
        subject_type="spec",
        reviewed_at="2026-01-02",
        reviewer="fixture",
        verdict=verdict,
        rounds=[_round()],
    )
    return p


def _run(root: Path, argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = cli.main(argv)
    return rc, out.getvalue() + err.getvalue()


REFINEMENT = "REVIEWED - MATERIAL CHANGES APPLIED"
GATE = "APPROVE WITH REVISIONS APPLIED"


def test_refinement_only_spec_is_refused_reviewed_by_the_flag_spelling(
    tmp_path: Path,
) -> None:
    root, spec = _repo(tmp_path)
    _review(root, slug="spec-refinement", verdict=REFINEMENT, file_id6="rf0001")
    before = spec.read_bytes()
    rc, out = _run(
        root,
        [
            "specs",
            "set",
            str(spec),
            "--status",
            "reviewed",
            "--dir",
            str(root),
            "--no-commit",
        ],
    )
    assert rc != 0
    assert "REFINEMENT" in out and "gate review" in out.lower()
    assert spec.read_bytes() == before


def test_refinement_only_spec_is_refused_reviewed_by_the_positional_spelling(
    tmp_path: Path,
) -> None:
    root, spec = _repo(tmp_path)
    _review(root, slug="spec-refinement", verdict=REFINEMENT, file_id6="rf0001")
    before = spec.read_bytes()
    rc, out = _run(
        root, ["set", "reviewed", SPEC_ID, "--yes", "--no-commit", "--dir", str(root)]
    )
    assert rc != 0
    assert "REFINEMENT" in out
    assert spec.read_bytes() == before


def _check_records(root: Path) -> list[dict]:
    # `check.spec-review-unattested` rides the `aw check all` sweep (check_engine's collisions
    # branch), not the type-scoped `aw check specs` (plan 2xwb9b D-07).
    rc, out = _run(root, ["check", "all", "--agent", "--dir", str(root)])
    recs = [
        json.loads(line) for line in out.splitlines() if line.strip().startswith("{")
    ]
    diags: list[dict] = []
    for r in recs:
        diags.extend(r.get("diagnostics") or [])
    return diags


def test_hand_forced_reviewed_spec_with_only_a_refinement_record_is_reported(
    tmp_path: Path,
) -> None:
    root, _spec = _repo(tmp_path, status="reviewed")
    _review(root, slug="spec-refinement", verdict=REFINEMENT, file_id6="rf0001")
    rules = [d.get("rule") for d in _check_records(root)]
    assert "check.spec-review-unattested" in rules


def test_one_gate_record_satisfies_both_spellings_and_the_check(tmp_path: Path) -> None:
    root, spec = _repo(tmp_path)
    _review(root, slug="spec-refinement", verdict=REFINEMENT, file_id6="rf0001")
    _review(root, slug="gate-kind", verdict=GATE)
    rc, out = _run(
        root,
        [
            "specs",
            "set",
            str(spec),
            "--status",
            "reviewed",
            "--dir",
            str(root),
            "--no-commit",
        ],
    )
    assert rc == 0, out
    moved = root / ".aw/records/specs/reviewed" / spec.name
    assert "- Status: reviewed\n" in moved.read_text(encoding="utf-8")
    assert "check.spec-review-unattested" not in [
        d.get("rule") for d in _check_records(root)
    ]

    (tmp_path / "second").mkdir()
    root2, _spec2 = _repo(tmp_path / "second")
    _review(root2, slug="spec-refinement", verdict=REFINEMENT, file_id6="rf0001")
    _review(root2, slug="gate-kind", verdict=GATE)
    rc, out = _run(
        root2, ["set", "reviewed", SPEC_ID, "--yes", "--no-commit", "--dir", str(root2)]
    )
    assert rc == 0, out

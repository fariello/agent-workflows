"""Behavioral tests for the runner review-findings dependency gate.

Pins that execute-action dependencies consult the dependency target's review record via
`edge.id6`, blocking execution when unresolved gating findings exist on the prerequisite.
Specified by revgate Order 03 (7nkcgp) and plan k81fqx.
"""

from pathlib import Path

from agent_workflows import review_findings, runner_shared


def _setup_repo(tmp_path: Path) -> Path:
    """Build a minimal repository fixture with an executed prerequisite plan."""
    exec_dir = tmp_path / ".aw" / "records" / "plans" / "executed"
    exec_dir.mkdir(parents=True, exist_ok=True)
    plan_file = exec_dir / "20261013-test-01-dep001-dep.ipd.md"
    plan_file.write_text(
        "# IPD: dep\n\n- Id: dep001\n- Status: executed\n",
        encoding="utf-8",
    )
    return tmp_path


def _write_review(
    repo: Path,
    *,
    finding_id: str = "PR-001",
    severity: str = "high",
    decision: str = "open",
    resolution: str = "",
) -> Path:
    """Write a `.review.md` record for `dep001` with a single finding in Round 1."""
    rev_path = (
        repo / ".aw" / "records" / "reviews" / "20261013-0001-01-dep001-test.review.md"
    )
    finding = review_findings.Finding(
        id=finding_id,
        severity=severity,
        scope="in-scope",
        area="behavior",
        evidence="repro evidence",
        finding="finding description",
        remediation_risk="low",
        decision=decision,
        resolution=resolution,
    )
    rnd = review_findings.Round(number=1, findings=(finding,), decisions=())
    return review_findings.write_review(
        rev_path,
        subject_id="dep001",
        subject_type="ipd",
        reviewed_at="2026-10-13",
        reviewer="test/agent",
        verdict="needs-revision" if decision != "fixed" else "approved",
        rounds=(rnd,),
    )


def test_case_a_out_of_queue_execute_blocked_by_high_open_finding(
    tmp_path: Path,
) -> None:
    """(a) OUT-OF-QUEUE execute item with executed:dep001 and HIGH OPEN finding is blocked."""
    repo = _setup_repo(tmp_path)
    _write_review(repo, severity="high", decision="open")

    # Fixture sanity: subject_gating_blocks must be non-empty to prevent vacuous pass
    blocks = review_findings.subject_gating_blocks(repo, "dep001")
    assert blocks, "Fixture sanity failed: dep001 must have gating blocks"

    item = {
        "position": 1,
        "id6": "tgt001",
        "setid": "test",
        "action": "execute",
        "status": "queued",
        "dependencies": ["executed:dep001"],
    }
    state = {"queue": [item], "repo": str(repo), "run_id": "run-test"}

    sat, unsat, reasons = runner_shared.dependency_status_detailed(item, state)
    assert sat is False
    assert unsat == ["executed:dep001"]
    assert "executed:dep001" in reasons
    assert "dep001" in reasons["executed:dep001"]
    assert "PR-001" in reasons["executed:dep001"]


def test_case_b_bare_id6_blocked_characterization(tmp_path: Path) -> None:
    """(b) Characterization: bare id6 dep001 was already blocked pre-fix and remains blocked."""
    repo = _setup_repo(tmp_path)
    _write_review(repo, severity="high", decision="open")

    # Fixture sanity
    blocks = review_findings.subject_gating_blocks(repo, "dep001")
    assert blocks, "Fixture sanity failed: dep001 must have gating blocks"

    item = {
        "position": 1,
        "id6": "tgt001",
        "setid": "test",
        "action": "execute",
        "status": "queued",
        "dependencies": ["dep001"],
    }
    state = {"queue": [item], "repo": str(repo), "run_id": "run-test"}

    sat, unsat, reasons = runner_shared.dependency_status_detailed(item, state)
    assert sat is False
    assert unsat == ["dep001"]
    assert "dep001" in reasons
    assert "dep001" in reasons["dep001"]
    assert "PR-001" in reasons["dep001"]


def test_case_c_in_queue_execute_blocked_by_high_open_finding(tmp_path: Path) -> None:
    """(c) IN-QUEUE execute dependency with run status executed is blocked identically."""
    repo = _setup_repo(tmp_path)
    _write_review(repo, severity="high", decision="open")

    # Fixture sanity
    blocks = review_findings.subject_gating_blocks(repo, "dep001")
    assert blocks, "Fixture sanity failed: dep001 must have gating blocks"

    dep_item = {
        "position": 1,
        "id6": "dep001",
        "setid": "test",
        "action": "execute",
        "status": "executed",
        "dependencies": [],
    }
    tgt_item = {
        "position": 2,
        "id6": "tgt001",
        "setid": "test",
        "action": "execute",
        "status": "queued",
        "dependencies": ["executed:dep001"],
    }
    state = {"queue": [dep_item, tgt_item], "repo": str(repo), "run_id": "run-test"}

    sat, unsat, reasons = runner_shared.dependency_status_detailed(tgt_item, state)
    assert sat is False
    assert unsat == ["executed:dep001"]
    assert "executed:dep001" in reasons
    assert "dep001" in reasons["executed:dep001"]
    assert "PR-001" in reasons["executed:dep001"]


def test_case_d_execute_satisfied_when_finding_fixed(tmp_path: Path) -> None:
    """(d) Execute dependency is satisfied when the finding is decided FIXED."""
    repo = _setup_repo(tmp_path)
    _write_review(
        repo, severity="high", decision="fixed", resolution="addressed in commit"
    )

    blocks = review_findings.subject_gating_blocks(repo, "dep001")
    assert not blocks, "Fixture sanity failed: fixed finding must not gate"

    item = {
        "position": 1,
        "id6": "tgt001",
        "setid": "test",
        "action": "execute",
        "status": "queued",
        "dependencies": ["executed:dep001"],
    }
    state = {"queue": [item], "repo": str(repo), "run_id": "run-test"}

    sat, unsat, reasons = runner_shared.dependency_status_detailed(item, state)
    assert sat is True
    assert unsat == []
    assert reasons == {}


def test_case_e_review_action_admitted_despite_open_finding(tmp_path: Path) -> None:
    """(e) Review-action item is satisfied despite open finding (review items not gated)."""
    repo = _setup_repo(tmp_path)
    _write_review(repo, severity="high", decision="open")

    # Fixture sanity: ensure dep001 is gating for execute items
    blocks = review_findings.subject_gating_blocks(repo, "dep001")
    assert blocks, "Fixture sanity failed: dep001 must have gating blocks"

    item = {
        "position": 1,
        "id6": "tgt001",
        "setid": "test",
        "action": "review",
        "status": "queued",
        "dependencies": ["executed:dep001"],
    }
    state = {"queue": [item], "repo": str(repo), "run_id": "run-test"}

    sat, unsat, reasons = runner_shared.dependency_status_detailed(item, state)
    assert sat is True
    assert unsat == []
    assert reasons == {}


def test_case_f_low_finding_satisfied_under_default_threshold(tmp_path: Path) -> None:
    """(f) Low finding is not gating under default high threshold, so item is satisfied."""
    repo = _setup_repo(tmp_path)
    _write_review(repo, severity="low", decision="open")

    blocks = review_findings.subject_gating_blocks(repo, "dep001")
    assert (
        not blocks
    ), "Fixture sanity failed: low finding must not gate under default threshold"

    item = {
        "position": 1,
        "id6": "tgt001",
        "setid": "test",
        "action": "execute",
        "status": "queued",
        "dependencies": ["executed:dep001"],
    }
    state = {"queue": [item], "repo": str(repo), "run_id": "run-test"}

    sat, unsat, reasons = runner_shared.dependency_status_detailed(item, state)
    assert sat is True
    assert unsat == []
    assert reasons == {}


def test_case_g_satisfied_when_no_review_record_exists(tmp_path: Path) -> None:
    """(g) When no review record exists at all, dependency is satisfied."""
    repo = _setup_repo(tmp_path)

    blocks = review_findings.subject_gating_blocks(repo, "dep001")
    assert not blocks, "Fixture sanity failed: no review record must not gate"

    item = {
        "position": 1,
        "id6": "tgt001",
        "setid": "test",
        "action": "execute",
        "status": "queued",
        "dependencies": ["executed:dep001"],
    }
    state = {"queue": [item], "repo": str(repo), "run_id": "run-test"}

    sat, unsat, reasons = runner_shared.dependency_status_detailed(item, state)
    assert sat is True
    assert unsat == []
    assert reasons == {}

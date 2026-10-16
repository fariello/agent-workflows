"""Unit tests for run_freeze module, covering freeze_requirements and freeze_workflow_requirements."""

import pytest

from agent_workflows import run_freeze, run_ledger_schema


def test_freeze_requirements_still_yields_m_01() -> None:
    """Existing freeze_requirements mints M-NN ids for category lists."""
    frozen = run_freeze.freeze_requirements({"must": ["step one"]})
    assert len(frozen.items) == 1
    assert frozen.items[0].id == "M-01"
    assert frozen.items[0].category == "must"
    assert frozen.items[0].text == "step one"
    assert len(frozen.requirement_digest) == 64


def test_freeze_workflow_requirements_preserves_id() -> None:
    """freeze_workflow_requirements preserves explicit workflow requirement ids."""
    workflow = {"requirements": [{"id": "R-01"}]}
    frozen = run_freeze.freeze_workflow_requirements(workflow)
    assert len(frozen.items) == 1
    item = frozen.items[0]
    assert item.id == "R-01"
    assert item.category == "must"
    assert item.text == "R-01"
    assert len(frozen.requirement_digest) == 64


def test_freeze_workflow_requirements_unwraps_compiled_wrapper() -> None:
    """Wrapped form {"workflow": {...}} unwraps and yields identical output."""
    plain = {"requirements": [{"id": "R-01", "text": "Requirement text"}]}
    wrapped = {"workflow": plain}

    frozen_plain = run_freeze.freeze_workflow_requirements(plain)
    frozen_wrapped = run_freeze.freeze_workflow_requirements(wrapped)

    assert frozen_plain.requirement_digest == frozen_wrapped.requirement_digest
    assert frozen_plain.items == frozen_wrapped.items


def test_freeze_workflow_requirements_order_independent_set_digest() -> None:
    """Set digest is order-independent while items preserve input order."""
    wf1 = {
        "requirements": [
            {"id": "R-01", "text": "First req"},
            {"id": "R-02", "text": "Second req"},
        ]
    }
    wf2 = {
        "requirements": [
            {"id": "R-02", "text": "Second req"},
            {"id": "R-01", "text": "First req"},
        ]
    }

    f1 = run_freeze.freeze_workflow_requirements(wf1)
    f2 = run_freeze.freeze_workflow_requirements(wf2)

    assert f1.requirement_digest == f2.requirement_digest
    assert [it.id for it in f1.items] == ["R-01", "R-02"]
    assert [it.id for it in f2.items] == ["R-02", "R-01"]


def test_freeze_workflow_requirements_optional_category_and_text() -> None:
    """Category defaults to 'must', text/description defaults to id when absent."""
    wf = {
        "requirements": [
            {"id": "R-01"},
            {"id": "SC-01", "category": "scope", "text": "Scope fence item"},
            {"id": "V-01", "category": "validation", "description": "Validation pred"},
            {"id": "O-01", "category": "output", "text": "Required output"},
        ]
    }
    frozen = run_freeze.freeze_workflow_requirements(wf)
    assert len(frozen.items) == 4
    assert frozen.items[0].category == "must"
    assert frozen.items[0].text == "R-01"
    assert frozen.items[1].category == "scope"
    assert frozen.items[1].text == "Scope fence item"
    assert frozen.items[2].category == "validation"
    assert frozen.items[2].text == "Validation pred"
    assert frozen.items[3].category == "output"
    assert frozen.items[3].text == "Required output"


def test_freeze_workflow_requirements_refuses_missing_or_empty_requirements_rf_e007() -> (
    None
):
    """Missing, empty, or non-list requirements raises ValueError with RF-E007."""
    cases = [
        {},
        {"requirements": None},
        {"requirements": []},
        {"requirements": "not a list"},
        {"requirements": {"R-01": "dict"}},
    ]
    for case in cases:
        with pytest.raises(ValueError) as excinfo:
            run_freeze.freeze_workflow_requirements(case)
        assert "RF-E007" in str(excinfo.value)


def test_freeze_workflow_requirements_refuses_non_mapping_or_idless_entry_rf_e008() -> (
    None
):
    """Non-mapping or id-less requirement entry raises ValueError with RF-E008."""
    cases = [
        {"requirements": ["string_item"]},
        {"requirements": [123]},
        {"requirements": [{"text": "no id"}]},
        {"requirements": [{"id": ""}]},
        {"requirements": [{"id": "   "}]},
        {"requirements": [{"id": None}]},
    ]
    for case in cases:
        with pytest.raises(ValueError) as excinfo:
            run_freeze.freeze_workflow_requirements(case)
        assert "RF-E008" in str(excinfo.value)


def test_freeze_workflow_requirements_refuses_duplicate_id_rf_e009() -> None:
    """Duplicate requirement id raises ValueError with RF-E009."""
    wf = {
        "requirements": [
            {"id": "R-01", "text": "First"},
            {"id": "R-01", "text": "Second with same id"},
        ]
    }
    with pytest.raises(ValueError) as excinfo:
        run_freeze.freeze_workflow_requirements(wf)
    assert "RF-E009" in str(excinfo.value)
    assert "R-01" in str(excinfo.value)


def test_freeze_workflow_requirements_refuses_unknown_category_rf_e003() -> None:
    """Unknown requirement category raises ValueError with RF-E003."""
    wf = {
        "requirements": [
            {"id": "R-01", "category": "invalid_cat", "text": "Test"},
        ]
    }
    with pytest.raises(ValueError) as excinfo:
        run_freeze.freeze_workflow_requirements(wf)
    assert "RF-E003" in str(excinfo.value)


def test_freeze_workflow_requirements_refuses_invalid_text_rf_e005_rf_e006() -> None:
    """Non-string text raises RF-E005; empty normalized text raises RF-E006."""
    wf_non_str = {"requirements": [{"id": "R-01", "text": 12345}]}
    with pytest.raises(ValueError) as excinfo:
        run_freeze.freeze_workflow_requirements(wf_non_str)
    assert "RF-E005" in str(excinfo.value)

    wf_empty = {"requirements": [{"id": "R-01", "text": "   "}]}
    with pytest.raises(ValueError) as excinfo:
        run_freeze.freeze_workflow_requirements(wf_empty)
    assert "RF-E006" in str(excinfo.value)


def test_requirement_set_record_with_workflow_requirements() -> None:
    """requirement_set_record produces schema-valid record from freeze_workflow_requirements."""
    wf = {
        "requirements": [
            {"id": "R-01", "text": "Main requirement"},
            {"id": "SC-01", "category": "scope", "text": "Scope requirement"},
        ]
    }
    frozen = run_freeze.freeze_workflow_requirements(wf)
    rec = run_freeze.requirement_set_record(
        run_id="run-12345678",
        seq=1,
        actor="runtime",
        timestamp="2026-10-16T12:00:00Z",
        parent="abc",
        frozen=frozen,
    )
    ok, findings = run_ledger_schema.validate_record(rec)
    assert ok, f"Record validation failed: {findings}"
    assert rec["kind"] == "requirement_set"
    assert rec["seq"] == 1
    assert rec["requirement_digest"] == frozen.requirement_digest
    assert len(rec["requirements"]) == 2
    assert rec["requirements"][0]["id"] == "R-01"
    assert rec["scope_fence"] == {"SC-01": "Scope requirement"}


def test_diff_and_refuse_drop_or_redefine_with_workflow_requirements() -> None:
    """diff_requirements and refuse_drop_or_redefine work with freeze_workflow_requirements."""
    wf1 = {"requirements": [{"id": "R-01", "text": "Initial text"}]}
    wf2 = {"requirements": [{"id": "R-01", "text": "Changed text"}]}
    wf3 = {"requirements": [{"id": "R-02", "text": "Dropped R-01"}]}

    f1 = run_freeze.freeze_workflow_requirements(wf1)
    f2 = run_freeze.freeze_workflow_requirements(wf2)
    f3 = run_freeze.freeze_workflow_requirements(wf3)

    revs = run_freeze.diff_requirements(f1, f2)
    assert len(revs) == 1
    assert revs[0].id == "R-01"

    redef_check = run_freeze.refuse_drop_or_redefine(f1, f2)
    assert not redef_check.ok
    assert any(f.code == "RF-E011" for f in redef_check.findings)

    drop_check = run_freeze.refuse_drop_or_redefine(f1, f3)
    assert not drop_check.ok
    assert any(f.code == "RF-E010" for f in drop_check.findings)

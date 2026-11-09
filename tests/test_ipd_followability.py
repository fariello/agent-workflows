"""Followability guidance `IPD-Z603` (spec ipd-structure-and-linting 8.2; research `nj8zdp`).

Advisory only, by maintainer ruling (2026-11-08): each signal produces an advisory and NEVER moves
the disposition. Tests drive `ipd_lint.lint_text` on built plans and assert on the returned result.
"""

from __future__ import annotations

import re

import pytest

from agent_workflows import ipd_lint as L

from tests.test_ipd_lint import _conforming_child

pytestmark = pytest.mark.core


def _post_cutover(text: str) -> str:
    return text.replace("- Date: 2026-08-03", "- Date: 2026-11-08")


def _with_items(text: str, n: int, item_text: str = "do a thing.") -> str:
    """Replace the single E/V pair with ``n`` pairs."""
    e_block = "".join(
        f"- [ ] E-{i:02d} {item_text}\n  - Depends on: none\n  - Expected outcome: x.\n"
        "  - Execution state: pending\n\n"
        for i in range(1, n + 1)
    )
    v_block = "".join(
        f"- [ ] V-{i:02d} validates E-{i:02d}\n  - Required evidence: the thing is present at path X.\n"
        "  - Observed evidence:\n  - Result: pending\n\n"
        for i in range(1, n + 1)
    )
    text = re.sub(r"- \[ \] E-01 do a thing\.\n(  - .*\n)+", e_block, text, count=1)
    text = re.sub(r"- \[ \] V-01 validates E-01\n(  - .*\n)+", v_block, text, count=1)
    return text.replace("- Highest E allocated: 01", f"- Highest E allocated: {n:02d}")


def _z603(result) -> list[str]:
    return [a.message for a in result.advisories if a.code == L.C_FOLLOWABLE]


def test_a_small_post_cutover_plan_gets_no_guidance():
    r = L.lint_text(_post_cutover(_conforming_child()))
    assert r.disposition == "conforming"
    assert _z603(r) == []


def test_too_many_items_is_advised_and_never_changes_the_disposition():
    r = L.lint_text(_post_cutover(_with_items(_conforming_child(), 6)))
    msgs = _z603(r)
    assert any("6 E-items" in m for m in msgs), msgs
    assert r.disposition == "conforming"


def test_five_items_is_within_guidance():
    r = L.lint_text(_post_cutover(_with_items(_conforming_child(), 5)))
    assert not any("E-items" in m for m in _z603(r))


def test_too_many_scope_paths_is_advised_excluding_plan_and_spec_files():
    paths = ", ".join(f"agent_workflows/m{i}.py" for i in range(9))
    t = _post_cutover(_conforming_child()).replace(
        "- Scope: sample.\n",
        f"- Scope: sample.\n- Scope-Paths: {paths}, x.spec.md, y.ipd.md\n",
    )
    assert any("9 work Scope-Paths" in m for m in _z603(L.lint_text(t)))
    eight = ", ".join(f"agent_workflows/m{i}.py" for i in range(8))
    t8 = _post_cutover(_conforming_child()).replace(
        "- Scope: sample.\n", f"- Scope: sample.\n- Scope-Paths: {eight}, x.spec.md\n"
    )
    assert not any("Scope-Paths" in m for m in _z603(L.lint_text(t8)))


def test_one_item_naming_many_units_is_advised():
    units = " ".join(f"`agent_workflows/m{i}.py`" for i in range(9))
    t = _post_cutover(_conforming_child()).replace(
        "- [ ] E-01 do a thing.", f"- [ ] E-01 move readers in {units}."
    )
    assert any("E-01 names 9 distinct units" in m for m in _z603(L.lint_text(t)))


def test_suite_only_evidence_is_advised_but_specific_evidence_is_not():
    suite_only = _post_cutover(_conforming_child()).replace(
        "the thing is present at path X.",
        "paste the bare `python3 -m pytest` summary line.",
    )
    assert any(
        "V-01 asks only for a suite-level pass" in m
        for m in _z603(L.lint_text(suite_only))
    )
    for specific in (
        "paste `python3 -m pytest tests/test_x.py` and the bare suite summary line.",
        "paste the diff and the bare suite summary line.",
        "the new test FAILING before and passing after, and the bare suite summary line.",
    ):
        t = _post_cutover(_conforming_child()).replace(
            "the thing is present at path X.", specific
        )
        assert not any("suite-level" in m for m in _z603(L.lint_text(t))), specific


def test_pre_cutover_plans_and_orchestrators_get_no_guidance():
    big = _with_items(_conforming_child(), 7)
    assert _z603(L.lint_text(big)) == []  # dated 2026-08-03, before the cutover
    orch = _post_cutover(big).replace("- Kind: child", "- Kind: orchestrator")
    assert not any("E-items" in m for m in _z603(L.lint_text(orch)))

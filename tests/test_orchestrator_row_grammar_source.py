"""Tests for orchestrator row grammar derivation and sensitivity (IPD l1xkrr, spec r07vma OQ-01).

Tests observable behavior and outcomes:
1. Conformance across all recognized statuses and checkbox states in a real orchestrator document.
2. The sensitivity proof (binding limb 2a and perturbation limb 2b).
3. Anchor enforcement: hand-mangled variants (trailing prose, over-indented rows) refused with ORCH_ROW_NOT_TYPED.
4. Refusal message contains the canonical row form.
"""

from __future__ import annotations

import re

from agent_workflows import ipd_lint as lint
from agent_workflows import ipd_schema as S


def _make_orchestrator_doc(action_row: str) -> str:
    """Build a minimal valid orchestrator IPD document containing the given action row."""
    return f"""# IPD: Test orchestrator doc

- Kind: orchestrator
- Order: 0
- Set: testset

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `c0ch01` | 20261001-testset-01-c0ch01-child.ipd.md | child task | none |

## Detailed Implementation Checklist (TODO)

{action_row}
  - Depends on: none
"""


def test_01_all_statuses_and_checkbox_states_conform():
    """Behavior 1: derived pattern and canonical describe rows conforming under orchestrator_row_conformance."""
    for status in S.RECOGNIZED_STATUS:
        for ticked in (False, True):
            row = lint.render_orchestrator_row(
                ident="E-01",
                child_id6="c0ch01",
                status=status,
                ticked=ticked,
            )
            doc_text = _make_orchestrator_doc(row)
            res = lint.orchestrator_row_conformance(doc_text)
            assert res.conforming, f"Expected conforming for status={status}, ticked={ticked}: {res.findings}"
            assert len(res.rows) == 1
            r = res.rows[0]
            assert r.conforming
            assert r.ident == "E-01"
            assert r.child_id6 == "c0ch01"
            assert r.status == status


def test_02a_sensitivity_binding_limb():
    """Limb 2a: _ORCH_ROW_RE.pattern and ORCH_ROW_CANONICAL equal the module derivations from the shipped datum."""
    expected_pattern = lint.orch_row_pattern(lint.ORCH_ROW_GRAMMAR)
    expected_canonical = lint.orch_row_canonical(lint.ORCH_ROW_GRAMMAR)

    assert lint._ORCH_ROW_RE.pattern == expected_pattern
    assert lint.ORCH_ROW_CANONICAL == expected_canonical


def test_02b_sensitivity_perturbation_limb():
    """Limb 2b: derivation functions consume the tokens and move together under perturbation."""
    shipped_pattern = lint.orch_row_pattern(lint.ORCH_ROW_GRAMMAR)
    shipped_canonical = lint.orch_row_canonical(lint.ORCH_ROW_GRAMMAR)

    # Perturb one token: ' CONFIRM ' -> ' VERIFY '
    perturbed_tokens = list(lint.ORCH_ROW_GRAMMAR)
    perturbed_tokens[2] = lint.OrchestratorRowToken(" VERIFY ", " VERIFY ")
    perturbed_tuple = tuple(perturbed_tokens)

    perturbed_pattern = lint.orch_row_pattern(perturbed_tuple)
    perturbed_canonical = lint.orch_row_canonical(perturbed_tuple)

    # Both outputs changed under perturbation
    assert perturbed_pattern != shipped_pattern
    assert perturbed_canonical != shipped_canonical
    assert " VERIFY " in perturbed_pattern
    assert " VERIFY " in perturbed_canonical
    assert " CONFIRM " not in perturbed_pattern
    assert " CONFIRM " not in perturbed_canonical

    # The perturbed pattern accepts the perturbed rendered row
    perturbed_row = lint.render_orchestrator_row(
        ident="E-01",
        child_id6="c0ch01",
        status="executed",
        tokens=perturbed_tuple,
    )
    assert " VERIFY " in perturbed_row
    assert re.compile(perturbed_pattern).match(perturbed_row) is not None

    # The shipped pattern rejects the perturbed row
    assert lint._ORCH_ROW_RE.match(perturbed_row) is None


def test_03_anchor_enforcement_and_refusal_reason():
    """Behavior 3: conforming row accepted while mangled variants are refused with ORCH_ROW_NOT_TYPED."""
    conforming_row = lint.render_orchestrator_row(
        ident="E-01",
        child_id6="c0ch01",
        status="executed",
    )
    res_ok = lint.orchestrator_row_conformance(_make_orchestrator_doc(conforming_row))
    assert res_ok.conforming

    # Trailing prose after status is refused with ORCH_ROW_NOT_TYPED (pins '$' anchor)
    mangled_trailing = conforming_row + " and then run tests"
    res_trailing = lint.orchestrator_row_conformance(
        _make_orchestrator_doc(mangled_trailing)
    )
    assert not res_trailing.conforming
    assert len(res_trailing.findings) == 1
    assert res_trailing.findings[0].reason == lint.ORCH_ROW_NOT_TYPED

    # Over-indented row or leading prose is refused by pattern (pins '^' anchor)
    over_indented = "  " + conforming_row
    assert lint._ORCH_ROW_RE.match(over_indented) is None
    assert lint._ORCH_ROW_RE.match(mangled_trailing) is None


def test_04_refusal_message_contains_canonical():
    """Behavior 4: refusal message for a non-conforming row contains the canonical row format."""
    mangled_row = "- [ ] E-01 invalid non-typed row"
    res = lint.orchestrator_row_conformance(_make_orchestrator_doc(mangled_row))
    assert not res.conforming
    assert len(res.findings) == 1
    finding = res.findings[0]
    assert finding.reason == lint.ORCH_ROW_NOT_TYPED
    assert lint.ORCH_ROW_CANONICAL in finding.message

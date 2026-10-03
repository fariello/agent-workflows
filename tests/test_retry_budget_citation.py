"""Consistency test ensuring the runtime retry budget validation error cites the canonical spec section.

Honest limit: this test proves the runtime refusal message and spec 25kzda AGREE on which section
holds the normative retry-budget bound (Section 5.5). It never proves either is independently
correct, and it is silent if the spec stops stating the bound in a form the locator recognizes.
To guard against silent drift or ambiguity, the spec locator fails loudly (raising ValueError)
rather than skipping when it finds zero or more than one normative statement.
"""

from __future__ import annotations

import pathlib
import pytest

from agent_workflows import run_recovery

#: The exact sentence in spec 25kzda where the correction-budget bound is defined normatively.
#: Load-bearing: must match exactly once in the spec. The distinguishing "must be" separates
#: this sentence from §2.1's "is an integer from 0 through 10 inclusive" (which was demoted to a
#: pointer). If §5.5 is reworded, update this anchor to match the new normative sentence.
BOUND_NORMATIVE_SENTENCE: str = "must be an integer from 0 through 10 inclusive"


def locate_spec_25kzda(repo_root: pathlib.Path) -> pathlib.Path:
    """Locate spec 25kzda recursively under .aw/records/specs/ across any status subdirectory."""
    specs_dir = repo_root / ".aw" / "records" / "specs"
    matches = sorted(specs_dir.rglob("*-25kzda-*.spec.md"))
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly 1 spec matching *-25kzda-*.spec.md under {specs_dir}, "
            f"found {len(matches)}: {matches}"
        )
    return matches[0]


def derive_bound_section(
    spec_path: pathlib.Path, anchor: str = BOUND_NORMATIVE_SENTENCE
) -> str:
    """Derive the enclosing ### section number holding the normative bound in the spec.

    Fails loudly (raises ValueError) if zero or multiple lines match the anchor, or if no
    preceding '### ' heading is found.
    """
    text = spec_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    matching_line_indices = [i for i, line in enumerate(lines) if anchor in line]
    if not matching_line_indices:
        raise ValueError(
            f"Found 0 lines matching anchor {anchor!r} in {spec_path}. "
            "The normative bound statement could not be located."
        )
    if len(matching_line_indices) > 1:
        raise ValueError(
            f"Found {len(matching_line_indices)} lines matching anchor {anchor!r} in {spec_path} "
            f"(line indices: {matching_line_indices}); expected exactly 1."
        )

    target_idx = matching_line_indices[0]
    for i in range(target_idx, -1, -1):
        line = lines[i].strip()
        if line.startswith("### "):
            parts = line[4:].strip().split()
            if parts:
                return parts[0]
    raise ValueError(
        f"Could not find preceding '###' section heading for line {target_idx + 1} in {spec_path}"
    )


def test_retry_budget_error_cites_canonical_spec_section() -> None:
    """Assert validate_retry_budget error message cites the spec section holding the bound."""
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    spec_path = locate_spec_25kzda(repo_root)
    expected_section = derive_bound_section(spec_path)

    with pytest.raises(run_recovery.InvalidRetryBudgetError) as exc_info:
        run_recovery.validate_retry_budget(99)

    msg = str(exc_info.value)
    expected_citation = f"spec 25kzda {expected_section}"
    assert (
        expected_citation in msg
    ), f"Runtime message {msg!r} does not contain expected citation {expected_citation!r}"

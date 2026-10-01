"""Tests for the RUN-* abort tri-state partition and spec action-text anchoring.

IPD `xjmjq4` (backlog `dorm45`) E-04, E-05; V-04, V-05.

INVARIANT TESTING BY OBSERVABLE OUTCOME (GUIDING_PRINCIPLES P16):
Every test in this module exercises runtime behavior and asserts on returned values or
findings. No test reads production source code (`agent_workflows/*.py`) using `inspect`,
`ast`, regex, or substring search, and no test asserts on comment banners, docstrings,
or symbol censuses.

NARROW EXCEPTION FOR SPEC FILE PARSING (P16 / spec 25kzda Section 4.2):
Spec 25kzda Section 4.2's table defines the public RUN-* finding code vocabulary and its
Action cells. Section 4.2's transcription note explicitly calls editing a cell in that table
"a code change". Comparing the code against the spec's verbatim bytes is a test of the
contract artifact itself (P16 exception: "where the text or file itself is the artifact
under test"), catching transcription errors that a module-internal check cannot detect (F6).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict
import unittest
from unittest import mock

import agent_workflows.run_evidence as evidence


_SPEC_PATH = next(
    (Path(__file__).resolve().parents[1] / ".aw" / "records" / "specs").rglob(
        "*25kzda*.spec.md"
    )
)


def _parse_spec_run_code_table() -> Dict[str, Dict[str, str]]:
    """Parse spec `25kzda` 4.2's table straight out of the SPEC FILE.

    THE POINT OF PARSING RATHER THAN HARDCODING: the only defect this vocabulary can realistically
    ship is a transcription error, and an expectation copied from the implementation cannot detect
    one. These tests therefore compare the module against the spec's own bytes, so REWORDING either
    side fails. Returns ``{code: {"message": ..., "action": ...}}`` with the surrounding backticks
    stripped, since the backticks are Markdown, not part of the operator-facing string.
    """
    rows: Dict[str, Dict[str, str]] = {}
    for line in _SPEC_PATH.read_text(encoding="utf-8").split("\n"):
        stripped = line.strip()
        if not stripped.startswith("| `RUN-"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split(" | ")]
        if len(cells) != 5:
            continue
        code = cells[0].strip("`")
        rows[code] = {
            "inspects": cells[1],
            "pass_criterion": cells[2],
            "message": cells[3].strip("`"),
            "action": cells[4],
        }
    return rows


class TestRunFindingAbortPartition(unittest.TestCase):
    """Behavioral tests pinning the RUN-* abort tri-state partition (E-04, E-05)."""

    def setUp(self) -> None:
        if not _SPEC_PATH.exists():
            self.skipTest(f"spec 25kzda not present at {_SPEC_PATH}")
        self.spec_rows = _parse_spec_run_code_table()

    # ---- Task group 1: derivation helper unit behavior -------------------------------------------

    def test_derive_abort_from_action_literals(self) -> None:
        """The helper correctly derives the tri-state from literal action strings (V-01)."""
        self.assertEqual(
            evidence.derive_abort_from_action(
                "FAIL ITEM after containment; ABORT RUN only for identity/type ambiguity or ownership conflict"
            ),
            evidence.ABORT_CONDITIONAL,
        )
        self.assertEqual(
            evidence.derive_abort_from_action("ABORT RUN"),
            evidence.ABORT_ALWAYS,
        )
        self.assertEqual(
            evidence.derive_abort_from_action("RETRY, then FAIL ITEM"),
            evidence.ABORT_NEVER,
        )

    # ---- Task group 2: module-level invariant coverage (E-04) ------------------------------------

    def test_abort_tristate_agrees_with_module_action_text(self) -> None:
        """Every row's stored abort equals the value derived from its own action text (E-04a)."""
        for row in evidence.RUN_FINDING_CODES:
            with self.subTest(code=row.code):
                derived = evidence.derive_abort_from_action(row.action)
                self.assertEqual(
                    row.abort,
                    derived,
                    f"{row.code}: stored abort {row.abort!r} != derived {derived!r}",
                )

    def test_may_abort_run_partition(self) -> None:
        """may_abort_run is True for exactly always and conditional rows, False for never (E-04b)."""
        for row in evidence.RUN_FINDING_CODES:
            with self.subTest(code=row.code):
                if row.abort in (evidence.ABORT_ALWAYS, evidence.ABORT_CONDITIONAL):
                    self.assertTrue(
                        evidence.may_abort_run(row.code),
                        f"{row.code} ({row.abort}) should return True for may_abort_run",
                    )
                elif row.abort == evidence.ABORT_NEVER:
                    self.assertFalse(
                        evidence.may_abort_run(row.code),
                        f"{row.code} ({row.abort}) should return False for may_abort_run",
                    )
                else:
                    self.fail(f"Unknown abort state {row.abort!r} on {row.code}")

    def test_conditional_abort_not_unconditional_and_abort_classes_exhaustive(
        self,
    ) -> None:
        """A conditional row is never reported unconditional, and abort_classes match 4.1 (E-04c)."""
        for row in evidence.RUN_FINDING_CODES:
            with self.subTest(code=row.code):
                if row.abort == evidence.ABORT_CONDITIONAL:
                    self.assertNotEqual(row.abort, evidence.ABORT_ALWAYS)
                    self.assertTrue(evidence.may_abort_run(row.code))
                    self.assertTrue(evidence.abort_classes_for(row.code))
                elif row.abort == evidence.ABORT_ALWAYS:
                    self.assertTrue(evidence.may_abort_run(row.code))
                    self.assertTrue(evidence.abort_classes_for(row.code))
                elif row.abort == evidence.ABORT_NEVER:
                    self.assertFalse(evidence.may_abort_run(row.code))
                    self.assertEqual(evidence.abort_classes_for(row.code), ())

                for cls in row.abort_classes:
                    self.assertIn(cls, evidence.ABORT_CLASSES)

    def test_validate_finding_table_catches_perturbed_abort(self) -> None:
        """validate_finding_table returns RC-ABORT-DERIVATION on perturbed abort (E-04d)."""
        # Baseline: shipped table must pass
        base_result = evidence.validate_finding_table()
        self.assertTrue(
            base_result.ok, f"shipped table failed validation: {base_result.findings}"
        )
        self.assertEqual(base_result.findings, ())

        # Perturbation: alter RUN-FROZEN-IDENTITY abort from conditional to always
        target_code = "RUN-FROZEN-IDENTITY"
        target_row = evidence.RUN_FINDING_CODES_BY_CODE[target_code]
        self.assertEqual(target_row.abort, evidence.ABORT_CONDITIONAL)

        perturbed_row = target_row._replace(abort=evidence.ABORT_ALWAYS)
        perturbed_table = tuple(
            perturbed_row if r.code == target_code else r
            for r in evidence.RUN_FINDING_CODES
        )
        perturbed_by_code = {r.code: r for r in perturbed_table}

        with mock.patch.object(
            evidence, "RUN_FINDING_CODES", perturbed_table
        ), mock.patch.object(evidence, "RUN_FINDING_CODES_BY_CODE", perturbed_by_code):
            result = evidence.validate_finding_table()
            self.assertFalse(result.ok)
            derivation_findings = [
                f for f in result.findings if f.code == "RC-ABORT-DERIVATION"
            ]
            self.assertEqual(len(derivation_findings), 1)
            finding = derivation_findings[0]
            self.assertEqual(finding.where, target_code)
            self.assertIn(target_code, finding.message)
            self.assertIn(evidence.ABORT_ALWAYS, finding.message)
            self.assertIn(evidence.ABORT_CONDITIONAL, finding.message)

    # ---- Task group 2: spec-anchored coverage (E-05) ---------------------------------------------

    def test_spec_defines_exactly_twelve_run_codes(self) -> None:
        """Spec 25kzda 4.2 defines exactly 12 RUN-* codes, matching the module exactly (E-05)."""
        self.assertEqual(len(self.spec_rows), 12)
        self.assertNotIn("RUN-NO-PUSH", self.spec_rows)
        self.assertEqual(
            set(self.spec_rows.keys()), set(evidence.RUN_FINDING_CODES_BY_CODE.keys())
        )

    def test_spec_action_cells_match_module_actions_byte_for_byte(self) -> None:
        """Spec 4.2 action cells equal module action strings byte for byte (E-05)."""
        for code, spec_data in self.spec_rows.items():
            with self.subTest(code=code):
                mod_row = evidence.RUN_FINDING_CODES_BY_CODE[code]
                self.assertEqual(
                    mod_row.action,
                    spec_data["action"],
                    f"{code}: module action disagrees with spec Section 4.2 cell byte for byte",
                )

    def test_abort_tristate_agrees_with_spec_action_text(self) -> None:
        """Stored abort tri-state equals the tri-state derived from the SPEC's action cell (E-05)."""
        for code, spec_data in self.spec_rows.items():
            with self.subTest(code=code):
                mod_row = evidence.RUN_FINDING_CODES_BY_CODE[code]
                expected_abort = evidence.derive_abort_from_action(spec_data["action"])
                self.assertEqual(
                    mod_row.abort,
                    expected_abort,
                    f"{code}: stored abort {mod_row.abort!r} != spec-derived abort {expected_abort!r}",
                )

    def test_spec_comparison_catches_adversarial_co_moved_drift(self) -> None:
        """Adversarial case from F6: co-moved drift passes E-02's gate but fails spec anchor (E-05)."""
        target_code = "RUN-CROSS-TREE"
        orig_row = evidence.RUN_FINDING_CODES_BY_CODE[target_code]
        self.assertEqual(orig_row.abort, evidence.ABORT_CONDITIONAL)

        # Adversarially perturb action and abort together so module self-consistency passes:
        perturbed_row = orig_row._replace(
            action="FAIL ITEM",
            abort=evidence.ABORT_NEVER,
            abort_classes=(),
        )
        perturbed_table = tuple(
            perturbed_row if r.code == target_code else r
            for r in evidence.RUN_FINDING_CODES
        )
        perturbed_by_code = {r.code: r for r in perturbed_table}

        # 1. E-02's gate alone PASSES on the perturbed row (demonstrating F6):
        with mock.patch.object(
            evidence, "RUN_FINDING_CODES", perturbed_table
        ), mock.patch.object(evidence, "RUN_FINDING_CODES_BY_CODE", perturbed_by_code):
            result = evidence.validate_finding_table()
            self.assertTrue(
                result.ok,
                f"E-02 gate should have passed on co-moved drift: {result.findings}",
            )

            # 2. Spec-anchored comparison FAILS on the same perturbed row:
            spec_action = self.spec_rows[target_code]["action"]
            spec_derived_abort = evidence.derive_abort_from_action(spec_action)

            # Byte comparison fails:
            self.assertNotEqual(
                perturbed_row.action,
                spec_action,
                "Adversarial action must not equal spec action",
            )
            # Spec-derived abort fails against stored abort:
            self.assertNotEqual(
                perturbed_row.abort,
                spec_derived_abort,
                "Adversarial abort must not equal spec-derived abort",
            )


if __name__ == "__main__":
    unittest.main()

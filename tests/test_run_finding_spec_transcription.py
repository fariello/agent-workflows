"""Byte-equality guard between spec 25kzda Section 4.2 and shipped finding codes.

Restores the guard promised by spec 25kzda Section 4.2's transcription note:
`run_evidence.RUN_FINDING_CODES` transcribes the `inspects` and `pass_criterion` cells
VERBATIM, and tests assert byte equality, so editing a cell is a code change.

Because approved plan xjmjq4 has landed tests/test_run_finding_abort_partition.py
(covering the `action` cell), this module asserts byte equality across the remaining
transcribed columns: `inspects`, `pass_criterion`, and `message`.

BACKTICK NORMALIZATION (BOTH-ENDS RULE):
Columns are not uniformly wrapped in Markdown backticks:
- 12 of 12 `message` cells are fully wrapped (`...`)
- 0 of 12 `inspects`, `pass_criterion`, and `action` cells are fully wrapped
- `RUN-SCOPE-DELTA`'s `inspects` cell legitimately begins with a backtick:
  `git diff` and untracked paths...
Stripping backticks unconditionally (e.g. .strip('`')) corrupts `RUN-SCOPE-DELTA`'s
`inspects` cell. Stripping nothing leaves 12 false mismatches on `message`.
The rule is: strip the outer pair ONLY when the cell both begins AND ends with a backtick.
"""

from __future__ import annotations

import pathlib
import unittest
from unittest import mock

from agent_workflows import run_evidence


def locate_spec_25kzda(repo_root: pathlib.Path) -> pathlib.Path:
    """Locate spec 25kzda recursively under .aw/records/specs/ by id6 glob."""
    specs_dir = repo_root / ".aw" / "records" / "specs"
    matches = sorted(specs_dir.rglob("*-25kzda-*.spec.md"))
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly 1 spec matching *-25kzda-*.spec.md under {specs_dir}, "
            f"found {len(matches)}: {[str(m) for m in matches]}"
        )
    return matches[0]


def strip_both_ends_backtick(cell: str) -> str:
    """Strip an outer backtick pair only when the cell both begins and ends with one.

    Preserves internal backticks and cells that begin with a code snippet (such as
    `RUN-SCOPE-DELTA`'s inspects cell: '`git diff` and untracked paths...').
    """
    if cell.startswith("`") and cell.endswith("`") and len(cell) >= 2:
        return cell[1:-1]
    return cell


def parse_spec_run_code_table(spec_path: pathlib.Path) -> dict[str, dict[str, str]]:
    """Parse Section 4.2's finding table directly from spec 25kzda's file bytes."""
    rows: dict[str, dict[str, str]] = {}
    for line in spec_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("| `RUN-"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) != 5:
            continue
        code = strip_both_ends_backtick(cells[0])
        rows[code] = {
            "inspects": strip_both_ends_backtick(cells[1]),
            "pass_criterion": strip_both_ends_backtick(cells[2]),
            "message": strip_both_ends_backtick(cells[3]),
            "action": strip_both_ends_backtick(cells[4]),
        }
    return rows


def assert_spec_transcription_matches(
    spec_rows: dict[str, dict[str, str]],
    table_by_code: dict[str, run_evidence.RunFindingCode],
    columns: tuple[str, ...] = ("inspects", "pass_criterion", "message"),
) -> None:
    """Assert byte equality between spec table rows and shipped finding code rows."""
    for code, spec_row in spec_rows.items():
        if code not in table_by_code:
            raise AssertionError(f"Code {code} parsed from spec is missing from table")
        mod_row = table_by_code[code]
        for field in columns:
            spec_val = spec_row[field]
            mod_val = getattr(mod_row, field)
            if spec_val != mod_val:
                raise AssertionError(
                    f"Mismatch in {code} field {field!r}:\n"
                    f"  spec:   {spec_val!r}\n"
                    f"  module: {mod_val!r}"
                )


class TestRunFindingSpecTranscription(unittest.TestCase):
    """Guards byte equality between spec 25kzda 4.2 and run_evidence."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = pathlib.Path(__file__).resolve().parent.parent
        cls.spec_path = locate_spec_25kzda(cls.repo_root)
        cls.spec_rows = parse_spec_run_code_table(cls.spec_path)

    def test_non_vacuous_parse(self) -> None:
        """The parser must find exactly 12 RUN-* rows and codes must match module exactly."""
        self.assertEqual(
            len(self.spec_rows),
            12,
            f"Expected exactly 12 spec rows, parsed {len(self.spec_rows)}: "
            f"{sorted(self.spec_rows.keys())}",
        )
        self.assertEqual(
            set(self.spec_rows.keys()),
            set(run_evidence.RUN_FINDING_CODES_BY_CODE.keys()),
            "Parsed spec code set must equal module code set in both directions",
        )

    def test_spec_transcription_byte_equality(self) -> None:
        """Every transcribed cell must match the spec byte-for-byte."""
        columns = ("inspects", "pass_criterion", "message")
        assert_spec_transcription_matches(
            self.spec_rows,
            run_evidence.RUN_FINDING_CODES_BY_CODE,
            columns=columns,
        )

    def test_mutation_sensitivity(self) -> None:
        """Perturbing a single cell must cause the transcription comparison to fail.

        Verifies the guard is sensitive to mutation and uses addCleanup to ensure
        the mutation cannot leak into other tests or test runs.
        """
        code_to_perturb = "RUN-BASELINE-OWNERSHIP"
        original_row = run_evidence.RUN_FINDING_CODES_BY_CODE[code_to_perturb]
        mutated_row = original_row._replace(
            pass_criterion=original_row.pass_criterion + " and also something else"
        )
        patched_table = dict(run_evidence.RUN_FINDING_CODES_BY_CODE)
        patched_table[code_to_perturb] = mutated_row

        # Verify mutation fails comparison
        with self.assertRaises(AssertionError) as ctx:
            assert_spec_transcription_matches(
                self.spec_rows,
                patched_table,
                columns=("inspects", "pass_criterion", "message"),
            )
        self.assertIn(code_to_perturb, str(ctx.exception))
        self.assertIn("pass_criterion", str(ctx.exception))

        # Also verify when patched into run_evidence.RUN_FINDING_CODES_BY_CODE with addCleanup
        with mock.patch.dict(
            run_evidence.RUN_FINDING_CODES_BY_CODE, {code_to_perturb: mutated_row}
        ):
            with self.assertRaises(AssertionError) as ctx_module:
                assert_spec_transcription_matches(
                    self.spec_rows,
                    run_evidence.RUN_FINDING_CODES_BY_CODE,
                    columns=("inspects", "pass_criterion", "message"),
                )
            self.assertIn(code_to_perturb, str(ctx_module.exception))

#!/usr/bin/env python3
"""wtiso Phase 0 (`8zgybk` E-02, E-09): the taxonomy freeze is complete and legal.

These tests make `docs/wtiso-state-taxonomy.md` a FALSIFIABLE artifact rather than prose. They
parse the frozen classification table and assert:

  * every row uses only the closed enum values for class / namespace / writer / retention
    (research x03wgn Section 2);
  * every migration owner is a real wtiso child id6, so no artifact can be relocated by an
    unnamed phase;
  * every path the runner constructs TODAY appears at least once, so a path cannot be silently
    dropped from the freeze.

Deleting a required row, or introducing an illegal enum value, FAILS. That is the point: the doc
is the Phase 0 baseline the later phases are checked against, so it must not be able to rot
quietly.

E-09's `test_gate_library_is_single_import_surface` lives here too, asserting the ONE shared
gate/predicate library imports and exposes its stable error codes.
"""

from __future__ import annotations

import re
import unittest

from tests.support import REPO_ROOT

TAXONOMY = REPO_ROOT / "docs" / "wtiso-state-taxonomy.md"

# The closed enums from x03wgn Section 2. A value outside these sets is a freeze violation.
CLASSES = {
    "product",
    "control-authority",
    "transaction",
    "lane-evidence",
    "reconstructible-cache",
}
NAMESPACES = {"project", "checkout", "run", "lane", "attempt", "transaction"}
WRITERS = {"driver", "worker", "user", "tool"}
RETENTIONS = {
    "tracked-publish",
    "local-retain",
    "secret-local",
    "discardable",
    "unknown",
}

# Every wtiso child id6 (orchestrator bl9q3d is excluded: an orchestrator authors no code and
# therefore can never be a migration owner).
WTISO_CHILDREN = {
    "8zgybk",
    "qcqhj7",
    "rchpms",
    "7p9n2v",
    "58ha43",
    "2c122z",
    "1o4eif",
}

# The paths the runner constructs today. Each MUST appear somewhere in the frozen table; a
# missing one means the freeze does not cover the live code.
REQUIRED_PATHS = (
    ".aw/state/ipd-lifecycle",
    ".aw/records/runs",
    ".aw/worktrees",
    "driver.lock",
)

# The classification table's header, used to locate it among the doc's several tables.
_CLASSIFICATION_HEADER_CELLS = (
    "artifact",
    "current path (as constructed today)",
    "class",
    "namespace",
    "canonical writer",
    "retention",
    "migration owner",
)


def _bare(cell: str) -> str:
    """Strip markdown code-span backticks so an enum cell compares by VALUE, not by formatting.

    The doc writes enum values in backticks for readability (`control-authority`); the freeze
    contract is about the value, so formatting must not be able to break or bypass the check.
    """

    return cell.strip().strip("`").strip()


def _split_row(line: str) -> list[str]:
    """Split one markdown table row into its trimmed cells (dropping the leading/trailing pipes)."""

    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _classification_rows(text: str) -> list[list[str]]:
    """Return the DATA rows of the frozen classification table.

    The doc contains several small vocabulary tables as well, so the table is located by matching
    its exact header cells rather than by taking the first or largest table. Returning [] when the
    header is absent lets the tests report a precise failure instead of an IndexError.
    """

    rows: list[list[str]] = []
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            # Any non-table line ends the table we were collecting.
            if in_table:
                break
            continue
        cells = _split_row(stripped)
        if not in_table:
            lowered = [c.lower() for c in cells]
            if all(want in lowered for want in _CLASSIFICATION_HEADER_CELLS):
                in_table = True
            continue
        # Skip the markdown separator row (|---|---|...).
        if all(set(c) <= set("-: ") for c in cells) and cells:
            continue
        rows.append(cells)
    return rows


def _column(header_cells: list[str], name: str) -> int:
    return [c.lower() for c in header_cells].index(name)


class TaxonomyFreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(
            TAXONOMY.is_file(),
            "the frozen taxonomy doc is missing: {0}".format(TAXONOMY),
        )
        self.text = TAXONOMY.read_text(encoding="utf-8")
        self.rows = _classification_rows(self.text)

    def test_classification_table_is_present_and_populated(self):
        """The frozen table exists and has rows. A doc with no table cannot freeze anything."""

        self.assertTrue(
            self.rows,
            "no classification table found in {0}: expected a table whose header contains "
            "{1}".format(TAXONOMY, _CLASSIFICATION_HEADER_CELLS),
        )
        # The enumerated artifacts in E-01 alone exceed 7 rows; a much smaller table means rows
        # were dropped.
        self.assertGreaterEqual(
            len(self.rows),
            7,
            "classification table has only {0} rows; the freeze must cover at least the seven "
            "enumerated paths".format(len(self.rows)),
        )

    def test_every_row_uses_only_legal_enum_values(self):
        """Class / namespace / writer / retention are CLOSED enums (x03wgn Section 2)."""

        for row in self.rows:
            self.assertGreaterEqual(
                len(row),
                8,
                "malformed row (expected 8 cells, got {0}): {1}".format(len(row), row),
            )
            artifact = row[0]
            klass, namespace, writer, retention = (_bare(c) for c in row[2:6])
            self.assertIn(
                klass,
                CLASSES,
                "row {0!r}: illegal class {1!r} (legal: {2})".format(
                    artifact, klass, sorted(CLASSES)
                ),
            )
            self.assertIn(
                namespace,
                NAMESPACES,
                "row {0!r}: illegal namespace {1!r} (legal: {2})".format(
                    artifact, namespace, sorted(NAMESPACES)
                ),
            )
            self.assertIn(
                writer,
                WRITERS,
                "row {0!r}: illegal writer {1!r} (legal: {2})".format(
                    artifact, writer, sorted(WRITERS)
                ),
            )
            self.assertIn(
                retention,
                RETENTIONS,
                "row {0!r}: illegal retention {1!r} (legal: {2})".format(
                    artifact, retention, sorted(RETENTIONS)
                ),
            )

    def test_every_migration_owner_is_a_real_wtiso_child(self):
        """An artifact whose owner is not a real child could be relocated by nobody."""

        for row in self.rows:
            artifact, owner = row[0], _bare(row[6])
            self.assertIn(
                owner,
                WTISO_CHILDREN,
                "row {0!r}: migration owner {1!r} is not a wtiso child id6 (legal: {2})".format(
                    artifact, owner, sorted(WTISO_CHILDREN)
                ),
            )

    def test_every_runner_constructed_path_is_frozen(self):
        """Each path the runner builds today appears in the table. A missing one FAILS."""

        # Search the PATH column only, and report a short message: dumping the whole table into
        # the assertion text would bury the one missing path in noise.
        paths_column = "\n".join(row[1] for row in self.rows)
        missing = [p for p in REQUIRED_PATHS if p not in paths_column]
        self.assertEqual(
            missing,
            [],
            "required path(s) {0} missing from the frozen classification table in {1}".format(
                missing, TAXONOMY.relative_to(REPO_ROOT)
            ),
        )

    def test_rows_cite_real_code_evidence(self):
        """Every row carries a `file:line` (or explicit does-not-exist) citation.

        A frozen row with no evidence is unverifiable prose, so a reviewer could not check the
        classification against the code. Rows for artifacts the design REQUIRES but the code has
        not built yet legitimately say so instead of citing a line.
        """

        cite = re.compile(r"\.py:\d+|does not exist yet|no [a-z ]+ exists today|x03wgn")
        for row in self.rows:
            artifact, evidence = row[0], row[7]
            self.assertTrue(
                cite.search(evidence),
                "row {0!r}: evidence cell cites no `file.py:line` and does not declare the "
                "artifact absent: {1!r}".format(artifact, evidence),
            )


class GateLibraryTests(unittest.TestCase):
    def test_gate_library_is_single_import_surface(self):
        """E-09: the ONE shared gate library imports and exposes its stable error codes.

        Phase 0 ships the import surface only. Later phases fill the predicate bodies IN THIS
        MODULE rather than forking a parallel rule implementation (x03wgn Section 7, "Hook rule
        differs from driver").
        """

        from agent_workflows import wtiso_gate

        for code in ("AW_GATE_SCOPE", "AW_LIFECYCLE_ROLE", "AW_MISSING_INPUT"):
            self.assertTrue(
                hasattr(wtiso_gate, code),
                "wtiso_gate is missing the stable error code {0}".format(code),
            )
            value = getattr(wtiso_gate, code)
            self.assertIsInstance(value, str)
            # The code's VALUE is the contract a hook prints and the driver matches on, so it must
            # equal its name, not merely exist.
            self.assertEqual(value, code)

        self.assertIn(wtiso_gate.AW_GATE_SCOPE, wtiso_gate.ERROR_CODES)
        self.assertEqual(
            len(set(wtiso_gate.ERROR_CODES)),
            len(wtiso_gate.ERROR_CODES),
            "ERROR_CODES contains a duplicate",
        )

    def test_gate_predicates_refuse_rather_than_silently_allow(self):
        """A predicate called before its owning phase lands must FAIL LOUDLY.

        This is the anti-greenwash property of the skeleton: if the stubs returned an empty
        violation list (a permissive default), a caller wired up early would report "no
        violations" and the gate would silently pass everything. Raising `NotImplementedError`
        makes that mistake impossible to miss.
        """

        from agent_workflows import wtiso_gate

        with self.assertRaises(NotImplementedError):
            wtiso_gate.check_scope(["a.py"], ["b.py"])
        with self.assertRaises(NotImplementedError):
            wtiso_gate.check_lifecycle_role("finalize", "worker")
        with self.assertRaises(NotImplementedError):
            wtiso_gate.format_missing_input("x.txt", "absent")


if __name__ == "__main__":
    unittest.main()

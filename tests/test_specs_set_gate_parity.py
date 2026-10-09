"""Tests for m1jlwm: Parity of specs set gates across both setter spellings.

Pins:
1. Evidence gate parity on implementing -> implemented:
   (a) no --evidence refuses (rc 1, spec unchanged in implementing/);
   (b) unresolvable --evidence refuses (rc 1, spec unchanged in implementing/);
   (c) resolvable executed-IPD citation succeeds (rc 0, spec relocated to implemented/).
   Covered on both:
   - Surface 1: aw specs set <path> --status implemented
   - Surface 2: aw specs set implemented <id6>

2. Deferred gate parity on -> deferred:
   Per m1jlwm E-03 audit of tests/test_gate_pair_validation_parity.py (from ju3rhs):
   - (d) out-of-vocabulary --gate-kind: covered in test_gate_pair_validation_parity.py by
         test_surface_1_specs_set_flag_deferred (lines 220-243) and
         test_surface_2_specs_set_positional_deferred (lines 342-364).
   - (e) malformed --gate-ref for valid kind: covered in test_gate_pair_validation_parity.py by
         test_surface_1_specs_set_flag_deferred (lines 245-266) and
         test_surface_2_specs_set_positional_deferred (lines 366-388).
   - (f) valid pair succeeds and writes both fields: covered in test_gate_pair_validation_parity.py by
         test_surface_1_specs_set_flag_deferred (lines 310-332) and
         test_surface_2_specs_set_positional_deferred (lines 431-452).
   - (g) unsafe --gate-summary refuses: NOT covered in test_gate_pair_validation_parity.py.
         Added here for both spellings:
         - Surface 1: aw specs set <path> --status deferred ... --gate-summary <unsafe>
         - Surface 2: aw specs set deferred <id6> ... --gate-summary <unsafe>

All tests drive CLI surfaces via cli.main and assert on exit code, file location,
and file content (asserting absence of write on refusals).
No tests inspect production source or count callers (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli


def _setup_repo(root: Path) -> Path:
    """Create minimal repository structure for specs, plans, and releases."""
    for sub in (
        "draft",
        "to-review",
        "reviewed",
        "approved",
        "implementing",
        "implemented",
        "deferred",
        "parked",
        "superseded",
    ):
        (root / ".aw" / "records" / "specs" / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("pending", "executed", "superseded", "archived"):
        (root / ".aw" / "records" / "plans" / sub).mkdir(parents=True, exist_ok=True)
    (root / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)

    rel = (
        root
        / ".aw"
        / "records"
        / "releases"
        / "20261001-rel001-01-rel001-v1.release.md"
    )
    rel.write_text(
        "# Release: 1.0.0\n\n"
        "- Id: rel001\n"
        "- Status: planned\n"
        "- Version: 1.0.0\n"
        "- Summary: Test release\n",
        encoding="utf-8",
    )
    return root


def _create_spec(
    repo: Path,
    *,
    id6: str = "sp0001",
    set_id: str = "setbeta",
    status: str = "implementing",
) -> Path:
    """Create a spec artifact in the appropriate status directory."""
    path = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / status
        / f"20261002-{set_id}-01-{id6}-test.spec.md"
    )
    content = (
        f"# Spec: Test Spec {id6}\n\n"
        f"- Date: 2026-10-02\n"
        f"- Status: {status}\n"
        f"- Set: {set_id}\n"
        f"- Id: {id6}\n\n"
        f"## Workflow history\n\n"
        f"- 2026-10-02 {status} (author): initial spec {status}.\n\n"
        f"## Goal\n"
        f"Test spec goal.\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def _create_executed_plan(
    repo: Path,
    *,
    id6: str = "ex0001",
    set_id: str = "setbeta",
) -> Path:
    """Create an executed IPD artifact suitable for use as implementation evidence."""
    path = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "executed"
        / f"20261002-{set_id}-01-{id6}-test.ipd.md"
    )
    content = (
        f"# IPD: Executed Test Plan {id6}\n\n"
        f"- Date: 2026-10-02\n"
        f"- Kind: child\n"
        f"- Status: executed\n"
        f"- Work-Kind: chore\n"
        f"- Priority: medium\n"
        f"- Set: {set_id}\n"
        f"- Order: 1\n"
        f"- Id: {id6}\n\n"
        f"## Workflow history\n\n"
        f"- 2026-10-02 executed (author): executed plan.\n\n"
        f"## Goal\n"
        f"Test plan goal.\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def _find_spec(repo: Path, id6: str) -> Path | None:
    """Find a spec file by id6 under any status directory."""
    matches = list((repo / ".aw" / "records" / "specs").glob(f"*/*-{id6}-*.spec.md"))
    if not matches:
        return None
    return matches[0]


class TestSpecsSetGateParity(unittest.TestCase):
    """Pin evidence gate and deferred gate validation across both setter spellings."""

    # -------------------------------------------------------------------------
    # Evidence Gate Tests
    # -------------------------------------------------------------------------

    def test_evidence_case_a_no_evidence_refuses_positional(self) -> None:
        """Case (a): positional spelling with no --evidence refuses rc 1, writes nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec = _create_spec(repo, id6="sp0001", status="implementing")
            orig_bytes = spec.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "specs",
                        "set",
                        "implemented",
                        "sp0001",
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc, 1, f"Expected rc 1, got {rc}. stdout: {out.getvalue()}"
            )
            combined = out.getvalue() + err.getvalue()
            self.assertIn("requires a resolvable --evidence citation", combined)
            self.assertIn(".aw/records/plans/executed/", combined)

            # Assert absence of write
            found = _find_spec(repo, "sp0001")
            self.assertIsNotNone(found)
            self.assertEqual(found.parent.name, "implementing")
            self.assertEqual(found.read_bytes(), orig_bytes)

    def test_evidence_case_a_no_evidence_refuses_flag(self) -> None:
        """Case (a): --status spelling with no --evidence refuses rc 1, writes nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec = _create_spec(repo, id6="sp0001", status="implementing")
            orig_bytes = spec.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "specs",
                        "set",
                        str(spec),
                        "--status",
                        "implemented",
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc, 1, f"Expected rc 1, got {rc}. stdout: {out.getvalue()}"
            )
            combined = out.getvalue() + err.getvalue()
            self.assertIn("requires a resolvable --evidence citation", combined)
            self.assertIn(".aw/records/plans/executed/", combined)

            # Assert absence of write
            found = _find_spec(repo, "sp0001")
            self.assertIsNotNone(found)
            self.assertEqual(found.parent.name, "implementing")
            self.assertEqual(found.read_bytes(), orig_bytes)

    def test_evidence_case_b_unresolvable_evidence_refuses_positional(self) -> None:
        """Case (b): positional spelling with unresolvable --evidence refuses rc 1, writes nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec = _create_spec(repo, id6="sp0002", status="implementing")
            orig_bytes = spec.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "specs",
                        "set",
                        "implemented",
                        "sp0002",
                        "--evidence",
                        ".aw/records/plans/executed/20261002-setbeta-01-nonexistent-x.ipd.md",
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc, 1, f"Expected rc 1, got {rc}. stdout: {out.getvalue()}"
            )
            combined = out.getvalue() + err.getvalue()
            self.assertIn("requires a resolvable --evidence citation", combined)
            self.assertIn(".aw/records/plans/executed/", combined)

            # Assert absence of write
            found = _find_spec(repo, "sp0002")
            self.assertIsNotNone(found)
            self.assertEqual(found.parent.name, "implementing")
            self.assertEqual(found.read_bytes(), orig_bytes)

    def test_evidence_case_b_unresolvable_evidence_refuses_flag(self) -> None:
        """Case (b): --status spelling with unresolvable --evidence refuses rc 1, writes nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec = _create_spec(repo, id6="sp0002", status="implementing")
            orig_bytes = spec.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "specs",
                        "set",
                        str(spec),
                        "--status",
                        "implemented",
                        "--evidence",
                        ".aw/records/plans/executed/20261002-setbeta-01-nonexistent-x.ipd.md",
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc, 1, f"Expected rc 1, got {rc}. stdout: {out.getvalue()}"
            )
            combined = out.getvalue() + err.getvalue()
            self.assertIn("requires a resolvable --evidence citation", combined)
            self.assertIn(".aw/records/plans/executed/", combined)

            # Assert absence of write
            found = _find_spec(repo, "sp0002")
            self.assertIsNotNone(found)
            self.assertEqual(found.parent.name, "implementing")
            self.assertEqual(found.read_bytes(), orig_bytes)

    def test_evidence_case_c_resolvable_evidence_succeeds_positional(self) -> None:
        """Case (c): positional spelling with resolvable --evidence succeeds rc 0 and relocates."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec = _create_spec(repo, id6="sp0003", status="implementing")
            plan = _create_executed_plan(repo, id6="ex0003")
            rel_plan = str(plan.relative_to(repo))

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "specs",
                        "set",
                        "implemented",
                        "sp0003",
                        "--evidence",
                        rel_plan,
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc,
                0,
                f"Expected rc 0, got {rc}. stdout: {out.getvalue()}, stderr: {err.getvalue()}",
            )

            # Assert relocation to implemented/
            found = _find_spec(repo, "sp0003")
            self.assertIsNotNone(found)
            self.assertEqual(found.parent.name, "implemented")
            text = found.read_text(encoding="utf-8")
            self.assertIn("- Status: implemented", text)
            self.assertIn("implemented", text)
            self.assertFalse(
                (
                    repo / ".aw" / "records" / "specs" / "implementing" / spec.name
                ).exists()
            )

    def test_evidence_case_c_resolvable_evidence_succeeds_flag(self) -> None:
        """Case (c): --status spelling with resolvable --evidence succeeds rc 0 and relocates."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec = _create_spec(repo, id6="sp0003", status="implementing")
            plan = _create_executed_plan(repo, id6="ex0003")
            rel_plan = str(plan.relative_to(repo))

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "specs",
                        "set",
                        str(spec),
                        "--status",
                        "implemented",
                        "--evidence",
                        rel_plan,
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc,
                0,
                f"Expected rc 0, got {rc}. stdout: {out.getvalue()}, stderr: {err.getvalue()}",
            )

            # Assert relocation to implemented/
            found = _find_spec(repo, "sp0003")
            self.assertIsNotNone(found)
            self.assertEqual(found.parent.name, "implemented")
            text = found.read_text(encoding="utf-8")
            self.assertIn("- Status: implemented", text)
            self.assertIn("implemented", text)
            self.assertFalse(
                (
                    repo / ".aw" / "records" / "specs" / "implementing" / spec.name
                ).exists()
            )

    # -------------------------------------------------------------------------
    # Deferred Gate Tests (Case g: unsafe --gate-summary)
    # -------------------------------------------------------------------------

    def test_deferred_case_g_unsafe_gate_summary_refuses_positional(self) -> None:
        """Case (g): positional spelling with unsafe --gate-summary refuses rc 1, writes nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec = _create_spec(repo, id6="sp0004", status="approved")
            orig_bytes = spec.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "specs",
                        "set",
                        "deferred",
                        "sp0004",
                        "--gate-kind",
                        "date",
                        "--gate-ref",
                        "2026-10-02",
                        "--gate-summary",
                        "unsafe\nnewline",
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertIn(
                rc,
                (1, 2),
                f"Expected refusal (rc 1 or 2), got {rc}. stdout: {out.getvalue()}",
            )
            combined = out.getvalue() + err.getvalue()
            self.assertIn("--gate-summary", combined)

            # Assert absence of write: spec still in approved/, byte-identical
            found = _find_spec(repo, "sp0004")
            self.assertIsNotNone(found)
            self.assertEqual(found.parent.name, "approved")
            self.assertEqual(found.read_bytes(), orig_bytes)
            text = found.read_text(encoding="utf-8")
            self.assertNotIn("Gate-Kind", text)
            self.assertNotIn("Gate-Ref", text)
            self.assertNotIn("Gate-Summary", text)

    def test_deferred_case_g_unsafe_gate_summary_refuses_flag(self) -> None:
        """Case (g): --status spelling with unsafe --gate-summary refuses rc 1, writes nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec = _create_spec(repo, id6="sp0004", status="approved")
            orig_bytes = spec.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "specs",
                        "set",
                        str(spec),
                        "--status",
                        "deferred",
                        "--gate-kind",
                        "date",
                        "--gate-ref",
                        "2026-10-02",
                        "--gate-summary",
                        "unsafe\nnewline",
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertIn(
                rc,
                (1, 2),
                f"Expected refusal (rc 1 or 2), got {rc}. stdout: {out.getvalue()}",
            )
            combined = out.getvalue() + err.getvalue()
            self.assertIn("--gate-summary", combined)

            # Assert absence of write: spec still in approved/, byte-identical
            found = _find_spec(repo, "sp0004")
            self.assertIsNotNone(found)
            self.assertEqual(found.parent.name, "approved")
            self.assertEqual(found.read_bytes(), orig_bytes)
            text = found.read_text(encoding="utf-8")
            self.assertNotIn("Gate-Kind", text)
            self.assertNotIn("Gate-Ref", text)
            self.assertNotIn("Gate-Summary", text)


if __name__ == "__main__":
    unittest.main()

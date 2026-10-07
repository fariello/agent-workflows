"""Tests for ju3rhs E-05: Parity of typed gate-pair validation across all eight setter surfaces.

Surfaces:
  1. aw specs set <path> --status deferred
  2. aw specs set deferred <id6>
  3. aw set deferred <id6>
  4. aw set specs deferred <id6>
  5. aw backlog set <path> --status blocked
  6. aw backlog set blocked <id6>
  7. aw set blocked <id6>
  8. aw set backlog blocked <id6>

Cases per surface:
  (a) out-of-vocabulary kind refuses
  (b) valid kind with malformed ref refuses
  (c) half-supplied pair refuses (both kind-no-ref and ref-no-kind)
  (d) valid pair succeeds and relocates

Fences:
  - Same-status fence: positional calls on already-gated record with no flags preserve gate;
    same call passing invalid gate kind refuses.
  - Clearing fence: transition out of gated status strips gate fields.
  - Unrelated-transition fence: non-gated transition succeeds with no gate flags.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli


def _setup_repo(root: Path) -> Path:
    """Create minimal directory structure and release artifact for tests."""
    for sub in ("draft", "to-review", "reviewed", "approved", "deferred"):
        (root / ".aw" / "records" / "specs" / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("open", "parked", "graduated", "done", "blocked"):
        (root / ".aw" / "records" / "backlog" / sub).mkdir(parents=True, exist_ok=True)
    (root / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
    rel = (
        root
        / ".aw"
        / "records"
        / "releases"
        / "20260901-rel001-01-rel001-v1.release.md"
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
    status: str = "approved",
    id6: str = "sp0001",
    gate_kind: str | None = None,
    gate_ref: str | None = None,
    gate_summary: str | None = None,
) -> Path:
    lines = [
        f"# Spec: Test Spec {id6}",
        "",
        "- Date: 2026-10-02",
        f"- Status: {status}",
        f"- Id: {id6}",
    ]
    if gate_kind is not None:
        lines.append(f"- Gate-Kind: {gate_kind}")
    if gate_ref is not None:
        lines.append(f"- Gate-Ref: {gate_ref}")
    if gate_summary is not None:
        lines.append(f"- Gate-Summary: {gate_summary}")
    lines.extend(
        [
            "- Author: tester",
            "",
            "## Workflow history",
            "- 2026-10-02 created (tester): initial spec",
            "",
            "Spec body text.",
        ]
    )
    p = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / status
        / f"20261002-{id6}-01-{id6}-test-spec.spec.md"
    )
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def _create_backlog_item(
    repo: Path,
    *,
    status: str = "open",
    id6: str = "bk0001",
    gate_kind: str | None = None,
    gate_ref: str | None = None,
    gate_summary: str | None = None,
) -> Path:
    lines = [
        f"- Id: {id6}",
        f"- Status: {status}",
        f"- Set: {id6}",
        "- Priority: medium",
        "- Work-Kind: bug",
        "- Summary: Test backlog item",
    ]
    if gate_kind is not None:
        lines.append(f"- Gate-Kind: {gate_kind}")
    if gate_ref is not None:
        lines.append(f"- Gate-Ref: {gate_ref}")
    if gate_summary is not None:
        lines.append(f"- Gate-Summary: {gate_summary}")
    lines.extend(
        [
            "",
            "## Workflow history",
            "- 2026-10-02 created (tester): initial item",
            "",
            "Backlog body text.",
        ]
    )
    p = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / status
        / f"20261002-{id6}-01-{id6}-test-item.backlog.md"
    )
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def _run_cli(args: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cli.main(args)
    return rc, out.getvalue(), err.getvalue()


class TestGatePairValidationParity(unittest.TestCase):
    """Eight-surface parity tests for typed gate-pair validation."""

    def _assert_refusal(
        self,
        repo: Path,
        source_path: Path,
        original_content: str,
        dest_dir: Path,
        cmd: list[str],
    ) -> None:
        rc, out, err = _run_cli(cmd)
        self.assertNotEqual(
            rc,
            0,
            f"Expected refusal (nonzero rc), got rc={rc}. Output: {out}\nStderr: {err}",
        )
        self.assertTrue(source_path.exists(), f"Source file was removed: {source_path}")
        self.assertEqual(
            source_path.read_text(encoding="utf-8"),
            original_content,
            "Source file content changed after refused command",
        )
        dest_files = list(dest_dir.glob(f"*{source_path.name}*"))
        self.assertEqual(
            dest_files,
            [],
            f"Destination file appeared in {dest_dir} after refusal: {dest_files}",
        )

    def _assert_success(
        self,
        repo: Path,
        source_path: Path,
        dest_dir: Path,
        cmd: list[str],
        expected_kind: str,
        expected_ref: str,
    ) -> None:
        rc, out, err = _run_cli(cmd)
        self.assertEqual(
            rc, 0, f"Expected success (rc=0), got rc={rc}. Output: {out}\nStderr: {err}"
        )
        self.assertFalse(
            source_path.exists(),
            f"Source file still exists in source dir: {source_path}",
        )
        dest_files = list(dest_dir.glob(f"*{source_path.name}*"))
        self.assertEqual(
            len(dest_files), 1, f"Expected 1 file in {dest_dir}, found {dest_files}"
        )
        dest_content = dest_files[0].read_text(encoding="utf-8")
        self.assertIn(f"- Gate-Kind: {expected_kind}", dest_content)
        self.assertIn(f"- Gate-Ref: {expected_ref}", dest_content)

    # -------------------------------------------------------------------------
    # Surface 1: aw specs set <path> --status deferred
    # -------------------------------------------------------------------------
    def test_surface_1_specs_set_flag_deferred(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            dest_dir = repo / ".aw" / "records" / "specs" / "deferred"

            # (a) out-of-vocabulary kind refuses
            spec = _create_spec(repo, status="approved", id6="sp0001")
            content = spec.read_text(encoding="utf-8")
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "specs",
                    "set",
                    str(spec.resolve()),
                    "--status",
                    "deferred",
                    "--gate-kind",
                    "bogus-kind",
                    "--gate-ref",
                    "x",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (b) valid kind with malformed ref refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "specs",
                    "set",
                    str(spec.resolve()),
                    "--status",
                    "deferred",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "not-a-date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c1) kind with no ref refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "specs",
                    "set",
                    str(spec.resolve()),
                    "--status",
                    "deferred",
                    "--gate-kind",
                    "date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c2) ref with no kind refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "specs",
                    "set",
                    str(spec.resolve()),
                    "--status",
                    "deferred",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (d) valid pair succeeds and relocates
            self._assert_success(
                repo,
                spec,
                dest_dir,
                [
                    "specs",
                    "set",
                    str(spec.resolve()),
                    "--status",
                    "deferred",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
                "date",
                "2026-10-02",
            )

    # -------------------------------------------------------------------------
    # Surface 2: aw specs set deferred <id6>
    # -------------------------------------------------------------------------
    def test_surface_2_specs_set_positional_deferred(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            dest_dir = repo / ".aw" / "records" / "specs" / "deferred"

            # (a) out-of-vocabulary kind refuses
            spec = _create_spec(repo, status="approved", id6="sp0002")
            content = spec.read_text(encoding="utf-8")
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "specs",
                    "set",
                    "deferred",
                    "sp0002",
                    "--gate-kind",
                    "bogus-kind",
                    "--gate-ref",
                    "x",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (b) valid kind with malformed ref refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "specs",
                    "set",
                    "deferred",
                    "sp0002",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "not-a-date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c1) kind with no ref refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "specs",
                    "set",
                    "deferred",
                    "sp0002",
                    "--gate-kind",
                    "date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c2) ref with no kind refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "specs",
                    "set",
                    "deferred",
                    "sp0002",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (d) valid pair succeeds and relocates
            self._assert_success(
                repo,
                spec,
                dest_dir,
                [
                    "specs",
                    "set",
                    "deferred",
                    "sp0002",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
                "date",
                "2026-10-02",
            )

    # -------------------------------------------------------------------------
    # Surface 3: aw set deferred <id6>
    # -------------------------------------------------------------------------
    def test_surface_3_set_untyped_deferred(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            dest_dir = repo / ".aw" / "records" / "specs" / "deferred"

            # (a) out-of-vocabulary kind refuses
            spec = _create_spec(repo, status="approved", id6="sp0003")
            content = spec.read_text(encoding="utf-8")
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "set",
                    "deferred",
                    "sp0003",
                    "--gate-kind",
                    "bogus-kind",
                    "--gate-ref",
                    "x",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (b) valid kind with malformed ref refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "set",
                    "deferred",
                    "sp0003",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "not-a-date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c1) kind with no ref refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "set",
                    "deferred",
                    "sp0003",
                    "--gate-kind",
                    "date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c2) ref with no kind refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "set",
                    "deferred",
                    "sp0003",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (d) valid pair succeeds and relocates
            self._assert_success(
                repo,
                spec,
                dest_dir,
                [
                    "set",
                    "deferred",
                    "sp0003",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
                "date",
                "2026-10-02",
            )

    # -------------------------------------------------------------------------
    # Surface 4: aw set specs deferred <id6>
    # -------------------------------------------------------------------------
    def test_surface_4_set_specs_type_prefixed_deferred(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            dest_dir = repo / ".aw" / "records" / "specs" / "deferred"

            # (a) out-of-vocabulary kind refuses
            spec = _create_spec(repo, status="approved", id6="sp0004")
            content = spec.read_text(encoding="utf-8")
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "set",
                    "specs",
                    "deferred",
                    "sp0004",
                    "--gate-kind",
                    "bogus-kind",
                    "--gate-ref",
                    "x",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (b) valid kind with malformed ref refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "set",
                    "specs",
                    "deferred",
                    "sp0004",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "not-a-date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c1) kind with no ref refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "set",
                    "specs",
                    "deferred",
                    "sp0004",
                    "--gate-kind",
                    "date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c2) ref with no kind refuses
            self._assert_refusal(
                repo,
                spec,
                content,
                dest_dir,
                [
                    "set",
                    "specs",
                    "deferred",
                    "sp0004",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (d) valid pair succeeds and relocates
            self._assert_success(
                repo,
                spec,
                dest_dir,
                [
                    "set",
                    "specs",
                    "deferred",
                    "sp0004",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
                "date",
                "2026-10-02",
            )

    # -------------------------------------------------------------------------
    # Surface 5: aw backlog set <path> --status blocked
    # -------------------------------------------------------------------------
    def test_surface_5_backlog_set_flag_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            dest_dir = repo / ".aw" / "records" / "backlog" / "blocked"

            # (a) out-of-vocabulary kind refuses
            item = _create_backlog_item(repo, status="open", id6="bk0001")
            content = item.read_text(encoding="utf-8")
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "backlog",
                    "set",
                    str(item.resolve()),
                    "--status",
                    "blocked",
                    "--gate-kind",
                    "bogus-kind",
                    "--gate-ref",
                    "x",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (b) valid kind with malformed ref refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "backlog",
                    "set",
                    str(item.resolve()),
                    "--status",
                    "blocked",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "not-a-date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c1) kind with no ref refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "backlog",
                    "set",
                    str(item.resolve()),
                    "--status",
                    "blocked",
                    "--gate-kind",
                    "date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c2) ref with no kind refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "backlog",
                    "set",
                    str(item.resolve()),
                    "--status",
                    "blocked",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (d) valid pair succeeds and relocates
            self._assert_success(
                repo,
                item,
                dest_dir,
                [
                    "backlog",
                    "set",
                    str(item.resolve()),
                    "--status",
                    "blocked",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
                "date",
                "2026-10-02",
            )

    # -------------------------------------------------------------------------
    # Surface 6: aw backlog set blocked <id6>
    # -------------------------------------------------------------------------
    def test_surface_6_backlog_set_positional_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            dest_dir = repo / ".aw" / "records" / "backlog" / "blocked"

            # (a) out-of-vocabulary kind refuses
            item = _create_backlog_item(repo, status="open", id6="bk0002")
            content = item.read_text(encoding="utf-8")
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "backlog",
                    "set",
                    "blocked",
                    "bk0002",
                    "--gate-kind",
                    "bogus-kind",
                    "--gate-ref",
                    "x",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (b) valid kind with malformed ref refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "backlog",
                    "set",
                    "blocked",
                    "bk0002",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "not-a-date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c1) kind with no ref refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "backlog",
                    "set",
                    "blocked",
                    "bk0002",
                    "--gate-kind",
                    "date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c2) ref with no kind refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "backlog",
                    "set",
                    "blocked",
                    "bk0002",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (d) valid pair succeeds and relocates
            self._assert_success(
                repo,
                item,
                dest_dir,
                [
                    "backlog",
                    "set",
                    "blocked",
                    "bk0002",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
                "date",
                "2026-10-02",
            )

    # -------------------------------------------------------------------------
    # Surface 7: aw set blocked <id6>
    # -------------------------------------------------------------------------
    def test_surface_7_set_untyped_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            dest_dir = repo / ".aw" / "records" / "backlog" / "blocked"

            # (a) out-of-vocabulary kind refuses
            item = _create_backlog_item(repo, status="open", id6="bk0003")
            content = item.read_text(encoding="utf-8")
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "set",
                    "blocked",
                    "bk0003",
                    "--gate-kind",
                    "bogus-kind",
                    "--gate-ref",
                    "x",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (b) valid kind with malformed ref refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "set",
                    "blocked",
                    "bk0003",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "not-a-date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c1) kind with no ref refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "set",
                    "blocked",
                    "bk0003",
                    "--gate-kind",
                    "date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c2) ref with no kind refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "set",
                    "blocked",
                    "bk0003",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (d) valid pair succeeds and relocates
            self._assert_success(
                repo,
                item,
                dest_dir,
                [
                    "set",
                    "blocked",
                    "bk0003",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
                "date",
                "2026-10-02",
            )

    # -------------------------------------------------------------------------
    # Surface 8: aw set backlog blocked <id6>
    # -------------------------------------------------------------------------
    def test_surface_8_set_backlog_type_prefixed_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            dest_dir = repo / ".aw" / "records" / "backlog" / "blocked"

            # (a) out-of-vocabulary kind refuses
            item = _create_backlog_item(repo, status="open", id6="bk0004")
            content = item.read_text(encoding="utf-8")
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "set",
                    "backlog",
                    "blocked",
                    "bk0004",
                    "--gate-kind",
                    "bogus-kind",
                    "--gate-ref",
                    "x",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (b) valid kind with malformed ref refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "set",
                    "backlog",
                    "blocked",
                    "bk0004",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "not-a-date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c1) kind with no ref refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "set",
                    "backlog",
                    "blocked",
                    "bk0004",
                    "--gate-kind",
                    "date",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (c2) ref with no kind refuses
            self._assert_refusal(
                repo,
                item,
                content,
                dest_dir,
                [
                    "set",
                    "backlog",
                    "blocked",
                    "bk0004",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
            )

            # (d) valid pair succeeds and relocates
            self._assert_success(
                repo,
                item,
                dest_dir,
                [
                    "set",
                    "backlog",
                    "blocked",
                    "bk0004",
                    "--gate-kind",
                    "date",
                    "--gate-ref",
                    "2026-10-02",
                    "--no-commit",
                    "--yes",
                    "--dir",
                    str(repo),
                ],
                "date",
                "2026-10-02",
            )

    # -------------------------------------------------------------------------
    # Fence 1: Same-status fence
    # -------------------------------------------------------------------------
    def test_fence_same_status_positional_preserves_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))

            # Positional 1: aw specs set deferred <id6> --message note
            spec = _create_spec(
                repo,
                status="deferred",
                id6="sp0010",
                gate_kind="external",
                gate_ref="ext-ref-001",
            )
            rc, out, err = _run_cli(
                [
                    "specs",
                    "set",
                    "deferred",
                    "sp0010",
                    "--message",
                    "a progress note",
                    "--yes",
                    "--no-commit",
                    "--dir",
                    str(repo),
                ]
            )
            self.assertEqual(rc, 0, f"specs set same-status failed: {err}")
            content = spec.read_text(encoding="utf-8")
            self.assertIn("- Gate-Kind: external", content)
            self.assertIn("- Gate-Ref: ext-ref-001", content)

            # Positional 2: aw set deferred <id6> --blocks-release next
            rc, out, err = _run_cli(
                [
                    "set",
                    "deferred",
                    "sp0010",
                    "--blocks-release",
                    "next",
                    "--yes",
                    "--no-commit",
                    "--dir",
                    str(repo),
                ]
            )
            self.assertEqual(rc, 0, f"set same-status failed: {err}")
            content = spec.read_text(encoding="utf-8")
            self.assertIn("- Gate-Kind: external", content)
            self.assertIn("- Gate-Ref: ext-ref-001", content)
            self.assertIn("- Blocks-Release: next", content)

            # Positional 3: aw backlog set blocked <id6> --message note
            item = _create_backlog_item(
                repo,
                status="blocked",
                id6="bk0010",
                gate_kind="external",
                gate_ref="ext-ref-002",
            )
            rc, out, err = _run_cli(
                [
                    "backlog",
                    "set",
                    "blocked",
                    "bk0010",
                    "--message",
                    "a progress note",
                    "--yes",
                    "--no-commit",
                    "--dir",
                    str(repo),
                ]
            )
            self.assertEqual(rc, 0, f"backlog set same-status failed: {err}")
            content = item.read_text(encoding="utf-8")
            self.assertIn("- Gate-Kind: external", content)
            self.assertIn("- Gate-Ref: ext-ref-002", content)

    def test_fence_same_status_invalid_gate_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))

            # Spec already in deferred: passing invalid gate refuses
            spec = _create_spec(
                repo,
                status="deferred",
                id6="sp0011",
                gate_kind="external",
                gate_ref="ext-ref-001",
            )
            orig_spec = spec.read_text(encoding="utf-8")
            rc, out, err = _run_cli(
                [
                    "specs",
                    "set",
                    "deferred",
                    "sp0011",
                    "--gate-kind",
                    "bogus-kind",
                    "--gate-ref",
                    "x",
                    "--yes",
                    "--no-commit",
                    "--dir",
                    str(repo),
                ]
            )
            self.assertNotEqual(rc, 0)
            self.assertEqual(spec.read_text(encoding="utf-8"), orig_spec)

            # Backlog item already in blocked: passing invalid gate refuses
            item = _create_backlog_item(
                repo,
                status="blocked",
                id6="bk0011",
                gate_kind="external",
                gate_ref="ext-ref-002",
            )
            orig_item = item.read_text(encoding="utf-8")
            rc, out, err = _run_cli(
                [
                    "backlog",
                    "set",
                    "blocked",
                    "bk0011",
                    "--gate-kind",
                    "bogus-kind",
                    "--gate-ref",
                    "x",
                    "--yes",
                    "--no-commit",
                    "--dir",
                    str(repo),
                ]
            )
            self.assertNotEqual(rc, 0)
            self.assertEqual(item.read_text(encoding="utf-8"), orig_item)

    # -------------------------------------------------------------------------
    # Fence 2: Clearing fence (transition out strips gate)
    # -------------------------------------------------------------------------
    def test_fence_clearing_transition_out_of_gated_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))

            # Spec: deferred -> approved strips gate
            spec = _create_spec(
                repo,
                status="deferred",
                id6="sp0020",
                gate_kind="external",
                gate_ref="ext-ref-001",
            )
            rc, out, err = _run_cli(
                [
                    "specs",
                    "set",
                    "approved",
                    "sp0020",
                    "--by-human",
                    "--yes",
                    "--no-commit",
                    "--dir",
                    str(repo),
                ]
            )
            self.assertEqual(rc, 0, f"Transition deferred -> approved failed: {err}")
            self.assertFalse(spec.exists())
            dest_spec = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "approved"
                / "20261002-sp0020-01-sp0020-test-spec.spec.md"
            )
            self.assertTrue(dest_spec.exists())
            content = dest_spec.read_text(encoding="utf-8")
            self.assertIn("- Status: approved", content)
            self.assertNotIn("- Gate-Kind:", content)
            self.assertNotIn("- Gate-Ref:", content)

            # Backlog: blocked -> open strips gate
            item = _create_backlog_item(
                repo,
                status="blocked",
                id6="bk0020",
                gate_kind="external",
                gate_ref="ext-ref-002",
            )
            rc, out, err = _run_cli(
                [
                    "backlog",
                    "set",
                    "open",
                    "bk0020",
                    "--yes",
                    "--no-commit",
                    "--dir",
                    str(repo),
                ]
            )
            self.assertEqual(rc, 0, f"Transition blocked -> open failed: {err}")
            self.assertFalse(item.exists())
            dest_item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20261002-bk0020-01-bk0020-test-item.backlog.md"
            )
            self.assertTrue(dest_item.exists())
            content = dest_item.read_text(encoding="utf-8")
            self.assertIn("- Status: open", content)
            self.assertNotIn("- Gate-Kind:", content)
            self.assertNotIn("- Gate-Ref:", content)

    # -------------------------------------------------------------------------
    # Fence 3: Unrelated transition fence (non-gated transition needs no gate)
    # -------------------------------------------------------------------------
    def test_fence_unrelated_transition_no_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))

            spec = _create_spec(repo, status="draft", id6="sp0030")
            rc, out, err = _run_cli(
                [
                    "specs",
                    "set",
                    "to-review",
                    "sp0030",
                    "--yes",
                    "--no-commit",
                    "--dir",
                    str(repo),
                ]
            )
            self.assertEqual(rc, 0, f"Transition draft -> to-review failed: {err}")
            self.assertFalse(spec.exists())
            dest_spec = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "to-review"
                / "20261002-sp0030-01-sp0030-test-spec.spec.md"
            )
            self.assertTrue(dest_spec.exists())
            content = dest_spec.read_text(encoding="utf-8")
            self.assertIn("- Status: to-review", content)


if __name__ == "__main__":
    unittest.main()

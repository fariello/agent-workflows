"""Tests for gateparity wdyz5n: evidence predicate parity on positional aw specs set implemented.

Pins:
- E-01 / E-04: implementing -> implemented evidence requirement fires on both spellings:
  (a) no --evidence refuses (exit 1, spec unchanged in implementing/);
  (b) unresolvable --evidence refuses (exit 1, spec unchanged in implementing/);
  (c) resolvable executed-IPD citation succeeds (exit 0, relocated to implemented/).
- E-02 / E-04: Untyped aw set implemented <id6> and aw set specs implemented <id6> parity:
  refuses without --evidence, succeeds with resolvable citation.
- E-04: Positional no-op fence: re-setting an already-implemented spec to implemented
  succeeds (exit 0, file unchanged) via positional aw specs set and aw set.
- E-04: Unrelated transition negative fence: draft -> to-review succeeds without --evidence.
- E-02 / E-04: Backlog release-gate close with --evidence on aw set done.
- E-02 / E-04: Declaration agreement for aw set parser and CommandDeclaration legacy_flags.

All tests drive cli.main and assert on exit code, file location, and file content.
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
    """Create minimal repository structure for specs, plans, backlog, and releases."""
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
    for sub in ("open", "parked", "graduated", "done", "blocked"):
        (root / ".aw" / "records" / "backlog" / sub).mkdir(parents=True, exist_ok=True)
    (root / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
    (root / ".aw" / "records" / "reviews").mkdir(parents=True, exist_ok=True)

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


def _create_backlog_item(
    repo: Path,
    *,
    id6: str = "bk0001",
    status: str = "open",
    blocks_release: str | None = "next",
) -> Path:
    """Create a backlog item."""
    path = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / status
        / f"20261002-setbeta-01-{id6}-test.backlog.md"
    )
    lines = [
        f"# Backlog: Test Item {id6}",
        "",
        f"- Id: {id6}",
        f"- Status: {status}",
        "- Priority: medium",
        "- Work-Kind: bug",
    ]
    if blocks_release is not None:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines.extend(
        [
            "",
            "## Workflow history",
            f"- 2026-10-02 {status} (author): initial backlog item.",
            "",
            "## Summary",
            "Test backlog item summary.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _find_spec(repo: Path, id6: str) -> Path | None:
    """Find a spec file by id6 under any status directory."""
    matches = list((repo / ".aw" / "records" / "specs").glob(f"*/*-{id6}-*.spec.md"))
    if not matches:
        return None
    return matches[0]


def _find_backlog(repo: Path, id6: str) -> Path | None:
    """Find a backlog item by id6 under any status directory."""
    matches = list(
        (repo / ".aw" / "records" / "backlog").glob(f"*/*-{id6}-*.backlog.md")
    )
    if not matches:
        return None
    return matches[0]


class SpecsEvidenceGateParityTests(unittest.TestCase):
    """Test parity of evidence citation requirement across both spellings and untyped surfaces."""

    def test_paired_case_a_no_evidence_refuses_and_writes_nothing(self) -> None:
        """Case (a): no --evidence refuses (rc 1) on both spellings; file byte-identical in implementing/."""
        # 1. Positional spelling
        with tempfile.TemporaryDirectory() as tmp1:
            repo1 = _setup_repo(Path(tmp1))
            spec1 = _create_spec(repo1, id6="sp0001", status="implementing")
            orig_bytes1 = spec1.read_bytes()

            out1, err1 = io.StringIO(), io.StringIO()
            with redirect_stdout(out1), redirect_stderr(err1):
                rc1 = cli.main(
                    [
                        "specs",
                        "set",
                        "implemented",
                        "sp0001",
                        "--dir",
                        str(repo1),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc1,
                1,
                f"Positional spelling should refuse with rc 1; stdout: {out1.getvalue()}",
            )
            combined1 = out1.getvalue() + err1.getvalue()
            self.assertIn("requires a resolvable --evidence citation", combined1)
            self.assertIn(".aw/records/plans/executed/", combined1)

            # Assert absence of write: still in implementing, byte-identical
            found1 = _find_spec(repo1, "sp0001")
            self.assertIsNotNone(found1)
            self.assertEqual(found1.parent.name, "implementing")
            self.assertEqual(found1.read_bytes(), orig_bytes1)

        # 2. --status spelling (identical fresh repo)
        with tempfile.TemporaryDirectory() as tmp2:
            repo2 = _setup_repo(Path(tmp2))
            spec2 = _create_spec(repo2, id6="sp0001", status="implementing")
            orig_bytes2 = spec2.read_bytes()

            out2, err2 = io.StringIO(), io.StringIO()
            with redirect_stdout(out2), redirect_stderr(err2):
                rc2 = cli.main(
                    [
                        "specs",
                        "set",
                        str(spec2),
                        "--status",
                        "implemented",
                        "--dir",
                        str(repo2),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc2,
                1,
                f"--status spelling should refuse with rc 1; stdout: {out2.getvalue()}",
            )
            err_text2 = err2.getvalue()
            self.assertIn("requires a resolvable --evidence citation", err_text2)
            self.assertIn(".aw/records/plans/executed/", err_text2)

            # Assert absence of write: still in implementing, byte-identical
            found2 = _find_spec(repo2, "sp0001")
            self.assertIsNotNone(found2)
            self.assertEqual(found2.parent.name, "implementing")
            self.assertEqual(found2.read_bytes(), orig_bytes2)

    def test_paired_case_b_unresolvable_evidence_refuses_and_writes_nothing(
        self,
    ) -> None:
        """Case (b): unresolvable --evidence refuses identically on both spellings."""
        unresolvable_citation = (
            ".aw/records/plans/executed/20261002-setbeta-01-nonexistent-x.ipd.md"
        )

        # 1. Positional spelling
        with tempfile.TemporaryDirectory() as tmp1:
            repo1 = _setup_repo(Path(tmp1))
            spec1 = _create_spec(repo1, id6="sp0001", status="implementing")
            orig_bytes1 = spec1.read_bytes()

            out1, err1 = io.StringIO(), io.StringIO()
            with redirect_stdout(out1), redirect_stderr(err1):
                rc1 = cli.main(
                    [
                        "specs",
                        "set",
                        "implemented",
                        "sp0001",
                        "--evidence",
                        unresolvable_citation,
                        "--dir",
                        str(repo1),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc1,
                1,
                f"Positional spelling should refuse with rc 1; stdout: {out1.getvalue()}",
            )
            combined1 = out1.getvalue() + err1.getvalue()
            self.assertIn("requires a resolvable --evidence citation", combined1)
            self.assertIn(".aw/records/plans/executed/", combined1)

            found1 = _find_spec(repo1, "sp0001")
            self.assertIsNotNone(found1)
            self.assertEqual(found1.parent.name, "implementing")
            self.assertEqual(found1.read_bytes(), orig_bytes1)

        # 2. --status spelling (identical fresh repo)
        with tempfile.TemporaryDirectory() as tmp2:
            repo2 = _setup_repo(Path(tmp2))
            spec2 = _create_spec(repo2, id6="sp0001", status="implementing")
            orig_bytes2 = spec2.read_bytes()

            out2, err2 = io.StringIO(), io.StringIO()
            with redirect_stdout(out2), redirect_stderr(err2):
                rc2 = cli.main(
                    [
                        "specs",
                        "set",
                        str(spec2),
                        "--status",
                        "implemented",
                        "--evidence",
                        unresolvable_citation,
                        "--dir",
                        str(repo2),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc2,
                1,
                f"--status spelling should refuse with rc 1; stdout: {out2.getvalue()}",
            )
            err_text2 = err2.getvalue()
            self.assertIn("requires a resolvable --evidence citation", err_text2)
            self.assertIn(".aw/records/plans/executed/", err_text2)

            found2 = _find_spec(repo2, "sp0001")
            self.assertIsNotNone(found2)
            self.assertEqual(found2.parent.name, "implementing")
            self.assertEqual(found2.read_bytes(), orig_bytes2)

    def test_paired_case_c_resolvable_evidence_succeeds_and_relocates(self) -> None:
        """Case (c): resolvable --evidence succeeds (rc 0) and relocates to implemented/ on both spellings."""
        # 1. Positional spelling
        with tempfile.TemporaryDirectory() as tmp1:
            repo1 = _setup_repo(Path(tmp1))
            _create_spec(repo1, id6="sp0001", status="implementing")
            ev_plan1 = _create_executed_plan(repo1, id6="ex0001")
            rel_ev1 = str(ev_plan1.relative_to(repo1))

            out1, err1 = io.StringIO(), io.StringIO()
            with redirect_stdout(out1), redirect_stderr(err1):
                rc1 = cli.main(
                    [
                        "specs",
                        "set",
                        "implemented",
                        "sp0001",
                        "--evidence",
                        rel_ev1,
                        "--dir",
                        str(repo1),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc1, 0, f"Positional spelling should succeed; stderr: {err1.getvalue()}"
            )
            found1 = _find_spec(repo1, "sp0001")
            self.assertIsNotNone(found1)
            self.assertEqual(found1.parent.name, "implemented")
            self.assertIn("- Status: implemented", found1.read_text(encoding="utf-8"))

        # 2. --status spelling (identical fresh repo)
        with tempfile.TemporaryDirectory() as tmp2:
            repo2 = _setup_repo(Path(tmp2))
            spec2 = _create_spec(repo2, id6="sp0001", status="implementing")
            ev_plan2 = _create_executed_plan(repo2, id6="ex0001")
            rel_ev2 = str(ev_plan2.relative_to(repo2))

            out2, err2 = io.StringIO(), io.StringIO()
            with redirect_stdout(out2), redirect_stderr(err2):
                rc2 = cli.main(
                    [
                        "specs",
                        "set",
                        str(spec2),
                        "--status",
                        "implemented",
                        "--evidence",
                        rel_ev2,
                        "--dir",
                        str(repo2),
                        "--yes",
                        "--no-commit",
                    ]
                )

            self.assertEqual(
                rc2, 0, f"--status spelling should succeed; stderr: {err2.getvalue()}"
            )
            found2 = _find_spec(repo2, "sp0001")
            self.assertIsNotNone(found2)
            self.assertEqual(found2.parent.name, "implemented")
            self.assertIn("- Status: implemented", found2.read_text(encoding="utf-8"))

    def test_untyped_set_implemented_parity(self) -> None:
        """aw set implemented <id6> and aw set specs implemented <id6> refuse without and succeed with evidence."""
        # 1. aw set implemented <id6>
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec = _create_spec(repo, id6="sp0001", status="implementing")
            orig_bytes = spec.read_bytes()

            # (a) without --evidence refuses
            out_a, err_a = io.StringIO(), io.StringIO()
            with redirect_stdout(out_a), redirect_stderr(err_a):
                rc_a = cli.main(
                    [
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
                rc_a,
                1,
                f"aw set implemented without evidence must refuse; out: {out_a.getvalue()}",
            )
            combined_a = out_a.getvalue() + err_a.getvalue()
            self.assertIn("requires a resolvable --evidence citation", combined_a)
            found_a = _find_spec(repo, "sp0001")
            self.assertIsNotNone(found_a)
            self.assertEqual(found_a.parent.name, "implementing")
            self.assertEqual(found_a.read_bytes(), orig_bytes)

            # (b) with resolvable --evidence succeeds
            ev_plan = _create_executed_plan(repo, id6="ex0001")
            rel_ev = str(ev_plan.relative_to(repo))
            out_b, err_b = io.StringIO(), io.StringIO()
            with redirect_stdout(out_b), redirect_stderr(err_b):
                rc_b = cli.main(
                    [
                        "set",
                        "implemented",
                        "sp0001",
                        "--evidence",
                        rel_ev,
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )
            self.assertEqual(
                rc_b,
                0,
                f"aw set implemented with evidence must succeed; err: {err_b.getvalue()}",
            )
            found_b = _find_spec(repo, "sp0001")
            self.assertIsNotNone(found_b)
            self.assertEqual(found_b.parent.name, "implemented")
            self.assertIn("- Status: implemented", found_b.read_text(encoding="utf-8"))

        # 2. aw set specs implemented <id6>
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec = _create_spec(repo, id6="sp0002", status="implementing")
            orig_bytes = spec.read_bytes()

            # (a) without --evidence refuses
            out_a, err_a = io.StringIO(), io.StringIO()
            with redirect_stdout(out_a), redirect_stderr(err_a):
                rc_a = cli.main(
                    [
                        "set",
                        "specs",
                        "implemented",
                        "sp0002",
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )
            self.assertEqual(
                rc_a,
                1,
                f"aw set specs implemented without evidence must refuse; out: {out_a.getvalue()}",
            )
            combined_a = out_a.getvalue() + err_a.getvalue()
            self.assertIn("requires a resolvable --evidence citation", combined_a)
            found_a = _find_spec(repo, "sp0002")
            self.assertIsNotNone(found_a)
            self.assertEqual(found_a.parent.name, "implementing")
            self.assertEqual(found_a.read_bytes(), orig_bytes)

            # (b) with resolvable --evidence succeeds
            ev_plan = _create_executed_plan(repo, id6="ex0002")
            rel_ev = str(ev_plan.relative_to(repo))
            out_b, err_b = io.StringIO(), io.StringIO()
            with redirect_stdout(out_b), redirect_stderr(err_b):
                rc_b = cli.main(
                    [
                        "set",
                        "specs",
                        "implemented",
                        "sp0002",
                        "--evidence",
                        rel_ev,
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )
            self.assertEqual(
                rc_b,
                0,
                f"aw set specs implemented with evidence must succeed; err: {err_b.getvalue()}",
            )
            found_b = _find_spec(repo, "sp0002")
            self.assertIsNotNone(found_b)
            self.assertEqual(found_b.parent.name, "implemented")
            self.assertIn("- Status: implemented", found_b.read_text(encoding="utf-8"))

    def test_positional_no_op_fence(self) -> None:
        """Positional re-setting of an already-implemented spec to implemented succeeds (old == new is not a transition).

        NOTE on deliberate unpairing:
        At review HEAD 9ccffaca3, `aw specs set <path> --status implemented` on an already-implemented spec
        already exits 1 with the evidence refusal because specs.run_set's `if auth.get("evidence"):` is not
        guarded by `old != new`. That is a pre-existing --status-spelling behavior this plan does not change
        (the root-cause unification is carried by fcnz1r/m94eht). We assert the positional no-op succeeds
        and deliberately do not assert the --status no-op either way, so the test neither pins nor contradicts it.
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec = _create_spec(repo, id6="sp0001", status="implemented")
            orig_bytes = spec.read_bytes()

            # 1. aw specs set implemented sp0001
            out1, err1 = io.StringIO(), io.StringIO()
            with redirect_stdout(out1), redirect_stderr(err1):
                rc1 = cli.main(
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
                rc1, 0, f"Positional no-op must succeed; stderr: {err1.getvalue()}"
            )
            found1 = _find_spec(repo, "sp0001")
            self.assertIsNotNone(found1)
            self.assertEqual(found1.parent.name, "implemented")
            self.assertEqual(found1.read_bytes(), orig_bytes)

            # 2. aw set implemented sp0001
            out2, err2 = io.StringIO(), io.StringIO()
            with redirect_stdout(out2), redirect_stderr(err2):
                rc2 = cli.main(
                    [
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
                rc2, 0, f"aw set no-op must succeed; stderr: {err2.getvalue()}"
            )
            found2 = _find_spec(repo, "sp0001")
            self.assertIsNotNone(found2)
            self.assertEqual(found2.parent.name, "implemented")
            self.assertEqual(found2.read_bytes(), orig_bytes)

    def test_unrelated_transition_negative_fence(self) -> None:
        """Unrelated transitions not evidence-gated (e.g. draft -> to-review) succeed without --evidence."""
        # 1. Positional spelling
        with tempfile.TemporaryDirectory() as tmp1:
            repo1 = _setup_repo(Path(tmp1))
            _create_spec(repo1, id6="sp0001", status="draft")

            out1, err1 = io.StringIO(), io.StringIO()
            with redirect_stdout(out1), redirect_stderr(err1):
                rc1 = cli.main(
                    [
                        "specs",
                        "set",
                        "to-review",
                        "sp0001",
                        "--dir",
                        str(repo1),
                        "--yes",
                        "--no-commit",
                    ]
                )
            self.assertEqual(
                rc1,
                0,
                f"Positional draft -> to-review should succeed; stderr: {err1.getvalue()}",
            )
            found1 = _find_spec(repo1, "sp0001")
            self.assertIsNotNone(found1)
            self.assertEqual(found1.parent.name, "to-review")
            self.assertIn("- Status: to-review", found1.read_text(encoding="utf-8"))

        # 2. --status spelling
        with tempfile.TemporaryDirectory() as tmp2:
            repo2 = _setup_repo(Path(tmp2))
            spec2 = _create_spec(repo2, id6="sp0001", status="draft")

            out2, err2 = io.StringIO(), io.StringIO()
            with redirect_stdout(out2), redirect_stderr(err2):
                rc2 = cli.main(
                    [
                        "specs",
                        "set",
                        str(spec2),
                        "--status",
                        "to-review",
                        "--dir",
                        str(repo2),
                        "--yes",
                        "--no-commit",
                    ]
                )
            self.assertEqual(
                rc2,
                0,
                f"--status draft -> to-review should succeed; stderr: {err2.getvalue()}",
            )
            found2 = _find_spec(repo2, "sp0001")
            self.assertIsNotNone(found2)
            self.assertEqual(found2.parent.name, "to-review")
            self.assertIn("- Status: to-review", found2.read_text(encoding="utf-8"))

    def test_aw_set_backlog_done_evidence_leg(self) -> None:
        """On a release-gated backlog item, aw set done --evidence satisfies close gate while bare set done refuses."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item = _create_backlog_item(
                repo, id6="bk0001", status="open", blocks_release="next"
            )
            orig_bytes = item.read_bytes()

            # (a) aw set done without --evidence refuses
            out_a, err_a = io.StringIO(), io.StringIO()
            with redirect_stdout(out_a), redirect_stderr(err_a):
                rc_a = cli.main(
                    [
                        "set",
                        "done",
                        "bk0001",
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )
            self.assertEqual(
                rc_a,
                1,
                f"aw set done without evidence must refuse; out: {out_a.getvalue()}",
            )
            found_a = _find_backlog(repo, "bk0001")
            self.assertIsNotNone(found_a)
            self.assertEqual(found_a.parent.name, "open")
            self.assertEqual(found_a.read_bytes(), orig_bytes)

            # (b) aw set done with in-tree review evidence succeeds
            rev_path = repo / ".aw" / "records" / "reviews" / "20261002-test.review.md"
            rev_path.write_text("# Review evidence\n", encoding="utf-8")
            rel_ev = str(rev_path.relative_to(repo))

            out_b, err_b = io.StringIO(), io.StringIO()
            with redirect_stdout(out_b), redirect_stderr(err_b):
                rc_b = cli.main(
                    [
                        "set",
                        "done",
                        "bk0001",
                        "--evidence",
                        rel_ev,
                        "--dir",
                        str(repo),
                        "--yes",
                        "--no-commit",
                    ]
                )
            self.assertEqual(
                rc_b,
                0,
                f"aw set done with evidence must succeed; err: {err_b.getvalue()}",
            )
            found_b = _find_backlog(repo, "bk0001")
            self.assertIsNotNone(found_b)
            self.assertEqual(found_b.parent.name, "done")
            self.assertIn("- Status: done", found_b.read_text(encoding="utf-8"))

    def test_set_declaration_agreement(self) -> None:
        """CommandDeclaration for 'set' declares --evidence and declared minus real parser options is empty."""
        from agent_workflows import command_surface as cs
        from agent_workflows.cli import _build_parser

        decl = cs.get_declaration("set")
        self.assertIsNotNone(decl)
        self.assertIn("--evidence", decl.legacy_flags)

        parser = _build_parser()
        set_parser = None
        for action in parser._actions:
            choices = getattr(action, "choices", None)
            if choices and hasattr(choices, "get") and choices.get("set"):
                set_parser = choices["set"]
                break
        self.assertIsNotNone(set_parser, "no `set` subparser")
        accepted = {opt for act in set_parser._actions for opt in act.option_strings}
        self.assertIn("--evidence", accepted)
        self.assertEqual(set(decl.legacy_flags) - accepted, set())


if __name__ == "__main__":
    unittest.main()

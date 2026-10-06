"""Tests for backlog transition table and enforcement gate (cc2m29).

Pins:
- (a) every edge E-03's table REFUSES exits nonzero AND leaves the file byte-identical and in its original directory;
- (b) every edge E-02's fence REQUIRES still succeeds at exit 0 and relocates the file, explicitly including
      done -> open and graduated -> open, each with a comment recording WHICH fence element requires it;
- (c) a same-status call still succeeds, pinning E-04's self-edge skip;
- (d) ->blocked without --gate-kind/--gate-ref still refuses with its EXISTING message and NOT the new transition message;
- (e) a NON-BACKLOG artifact is untouched: a spec transition its own table permits still succeeds, proving the gate is keyed on record_type;
- (f) the refusal is reported on the agent/JSON surface with a machine-readable rule token and a nonzero exit;
- (g) --dry-run on a refused edge refuses rather than PREVIEWING a move that can never be performed;
- (h) an UPPERCASE - Status: source is gated identically, pinning E-04/E-05's case-fold.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli


def _setup_repo(root: Path) -> Path:
    """Create a minimal repository structure with backlog and releases trees."""
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
    # Specs tree for case (e) non-backlog test
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
    return root


def _write_conforming_plan(
    repo: Path,
    *,
    id6: str = "pl0001",
    backlog_id6: str = "bk0001",
    set_id: str = "demo",
) -> Path:
    plan_dir = repo / ".aw" / "records" / "plans" / "pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    p = plan_dir / f"20260901-{set_id}-01-{id6}-plan.ipd.md"
    p.write_text(
        f"# IPD: Plan {id6}\n\n"
        "- Date: 2026-09-01\n"
        "- Kind: child\n"
        "- Concern: Test concern.\n"
        "- Scope: Test scope.\n"
        "- Status: to-review\n"
        "- Work-Kind: chore\n"
        "- Priority: medium\n"
        f"- Set: {set_id}\n"
        "- Order: 1\n"
        f"- Id: {id6}\n"
        f"- From-Backlog: {backlog_id6}\n"
        "- Scope-Paths: README.md\n"
        "- Highest E allocated: 01\n"
        "- Author: test\n"
        "- Item-Dependencies: none\n\n"
        "## Workflow history\n"
        "- 2026-09-01 to-review (test): created\n\n"
        "## Goal\n"
        f"Goal {id6}.\n\n"
        "## Detailed Implementation Checklist (TODO)\n"
        "### Task group 1: work\n"
        "- [ ] E-01 Work item\n"
        "  - Depends on: none\n"
        "  - Expected outcome: done\n"
        "  - Execution state: pending\n\n"
        "## Project conventions discovered (Step 0)\n"
        "None.\n\n"
        "## Findings\n"
        "None.\n\n"
        "## Proposed changes (ordered, validatable)\n"
        "1. E-01 do work.\n\n"
        "## Deferred / out of scope (with reason)\n"
        "- None.\n\n"
        "## Scope check\n"
        "- None.\n\n"
        "## Required tests / validation\n"
        "- None.\n\n"
        "## Spec / documentation sync\n"
        "- None.\n\n"
        "## Open questions\n"
        "- None.\n\n"
        "## Validation and cross-check (verify before reporting done)\n"
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: check.\n"
        "  - Observed evidence:\n"
        "  - Result: pending\n\n"
        "## Approval and execution gate\n"
        "- Size assessment: standard\n"
        "- Cohesion rationale: not required\n",
        encoding="utf-8",
    )
    return p


def _create_item(
    repo: Path,
    *,
    status: str,
    work_kind: str = "chore",
    item_id: str = "bk0001",
    priority: str = "medium",
    gate_kind: str | None = None,
    gate_ref: str | None = None,
    raw_status_line: str | None = None,
) -> Path:
    """Create a backlog item in the given status."""
    st_line = raw_status_line if raw_status_line is not None else f"- Status: {status}"
    lines = [
        f"- Id: {item_id}",
        st_line,
        f"- Set: {item_id}",
        f"- Priority: {priority}",
        f"- Work-Kind: {work_kind}",
        "- Summary: Test item",
    ]
    if gate_kind and gate_ref:
        lines.append(f"- Gate-Kind: {gate_kind}")
        lines.append(f"- Gate-Ref: {gate_ref}")
    lines.extend(
        [
            "",
            "## Workflow history",
            f"- 2026-10-01 created (tester): initial {status}",
            "",
        ]
    )
    # Normalize directory based on canonical status
    dir_name = status.lower()
    p = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / dir_name
        / f"20261001-{item_id}-01-{item_id}-test.backlog.md"
    )
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _find_item(repo: Path, item_id: str) -> Path:
    """Locate the item file regardless of which status directory it moved into."""
    matches = list(
        (repo / ".aw" / "records" / "backlog").rglob(f"*{item_id}*.backlog.md")
    )
    assert matches, f"Could not find item {item_id} in {repo}"
    return matches[0]


class TestBacklogTransitionGate(unittest.TestCase):
    """Pin the backlog transition gate by outcome for both spellings."""

    # =========================================================================
    # Case (a): Every refused edge exits nonzero AND leaves file byte-identical
    # =========================================================================

    # Pre-change measurement at HEAD 38c34e7 (E-01):
    # Both spellings exited 0 on all four edges, status was rewritten, and file was relocated.
    # Refused edges: ('parked', 'done'), ('parked', 'graduated'), ('done', 'blocked'), ('done', 'parked').

    def test_refused_transitions_status_spelling(self) -> None:
        """Case (a): Every refused edge fails with rc=1 on the --status spelling, file byte-identical."""
        refused_edges = [
            ("parked", "done"),
            ("parked", "graduated"),
            ("done", "blocked"),
            ("done", "parked"),
        ]
        for src, tgt in refused_edges:
            with self.subTest(edge=f"{src}->{tgt}"):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = _setup_repo(Path(tmp))
                    item_path = _create_item(repo, status=src, item_id="bk0001")
                    original_bytes = item_path.read_bytes()

                    out, err = io.StringIO(), io.StringIO()
                    with redirect_stdout(out), redirect_stderr(err):
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item_path),
                                "--status",
                                tgt,
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    self.assertEqual(rc, 1, f"Expected rc=1 for {src}->{tgt}, got {rc}")
                    combined = out.getvalue() + err.getvalue()
                    self.assertIn(f"illegal transition {src} -> {tgt}", combined)

                    found = _find_item(repo, "bk0001")
                    self.assertEqual(found.parent.name, src)
                    self.assertEqual(found.read_bytes(), original_bytes)

    def test_refused_transitions_positional_spelling(self) -> None:
        """Case (a): Every refused edge fails with rc=1 on positional spelling, file byte-identical."""
        refused_edges = [
            ("parked", "done"),
            ("parked", "graduated"),
            ("done", "blocked"),
            ("done", "parked"),
        ]
        for src, tgt in refused_edges:
            with self.subTest(edge=f"{src}->{tgt}"):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = _setup_repo(Path(tmp))
                    item_path = _create_item(repo, status=src, item_id="bk0001")
                    original_bytes = item_path.read_bytes()

                    out, err = io.StringIO(), io.StringIO()
                    with redirect_stdout(out), redirect_stderr(err):
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                tgt,
                                "bk0001",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    self.assertEqual(rc, 1, f"Expected rc=1 for {src}->{tgt}, got {rc}")
                    combined = out.getvalue() + err.getvalue()
                    self.assertIn(
                        f"Illegal backlog transition {src} -> {tgt}", combined
                    )

                    found = _find_item(repo, "bk0001")
                    self.assertEqual(found.parent.name, src)
                    self.assertEqual(found.read_bytes(), original_bytes)

    # =========================================================================
    # Case (b): Every fence-required edge succeeds at rc=0 and relocates file
    # =========================================================================

    def test_fence_required_transitions_status_spelling(self) -> None:
        """Case (b): Fence-required edges succeed on --status spelling and relocate file."""
        # Each edge annotated with which fence element requires it:
        fence_edges = [
            # E-02 (b) shipped test suite (tests/test_backlog_gate_follows_status.py) and release-gate re-defaulting
            ("done", "open", []),
            # E-02 (c) runner containment rollback (runner_shared.py:35563) and operator remedy
            ("graduated", "open", []),
            # E-02 (a) live corpus item x7wfyx, corrective reopen when partial deliverables land
            ("done", "graduated", []),
            # E-02 (a) live corpus, direct handoff when gate clears
            ("blocked", "graduated", []),
            # Gate clearing
            ("blocked", "open", []),
            # Standard design handoff
            ("open", "graduated", []),
            # Direct small fix
            ("open", "done", []),
            # Standard shelving
            ("open", "parked", []),
            # Standard gating
            ("open", "blocked", ["--gate-kind", "artifact", "--gate-ref", "rel001"]),
            # Standard execution completion
            ("graduated", "done", []),
            # Execution blocked
            (
                "graduated",
                "blocked",
                ["--gate-kind", "artifact", "--gate-ref", "rel001"],
            ),
            # Active work shelved
            ("graduated", "parked", []),
            # Blocked item shelved
            ("blocked", "parked", []),
            # Blocked item resolved directly
            ("blocked", "done", []),
            # Uncommitted item activated
            ("parked", "open", []),
            # Uncommitted item gated
            ("parked", "blocked", ["--gate-kind", "artifact", "--gate-ref", "rel001"]),
        ]
        for src, tgt, extra_args in fence_edges:
            with self.subTest(edge=f"{src}->{tgt}"):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = _setup_repo(Path(tmp))
                    item_path = _create_item(
                        repo,
                        status=src,
                        item_id="bk0001",
                        gate_kind="artifact" if src == "blocked" else None,
                        gate_ref="rel001" if src == "blocked" else None,
                    )
                    if tgt == "graduated":
                        _write_conforming_plan(repo, id6="pl0001", backlog_id6="bk0001")

                    out, err = io.StringIO(), io.StringIO()
                    with redirect_stdout(out), redirect_stderr(err):
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item_path),
                                "--status",
                                tgt,
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                                *extra_args,
                            ]
                        )
                    self.assertEqual(rc, 0, f"Failed on {src}->{tgt}: {err.getvalue()}")
                    found = _find_item(repo, "bk0001")
                    self.assertEqual(found.parent.name, tgt)
                    self.assertIn(f"- Status: {tgt}", found.read_text(encoding="utf-8"))

    def test_fence_required_transitions_positional_spelling(self) -> None:
        """Case (b): Fence-required edges succeed on positional spelling and relocate file."""
        fence_edges = [
            # E-02 (b) shipped test suite and release-gate re-defaulting
            ("done", "open", []),
            # E-02 (c) runner containment rollback and operator remedy
            ("graduated", "open", []),
            # E-02 (a) live corpus item x7wfyx
            ("done", "graduated", []),
            # E-02 (a) live corpus, direct handoff when gate clears
            ("blocked", "graduated", []),
            ("blocked", "open", []),
            ("open", "graduated", []),
            ("open", "done", []),
            ("open", "parked", []),
            ("open", "blocked", ["--gate-kind", "artifact", "--gate-ref", "rel001"]),
            ("graduated", "done", []),
            (
                "graduated",
                "blocked",
                ["--gate-kind", "artifact", "--gate-ref", "rel001"],
            ),
            ("graduated", "parked", []),
            ("blocked", "parked", []),
            ("blocked", "done", []),
            ("parked", "open", []),
            ("parked", "blocked", ["--gate-kind", "artifact", "--gate-ref", "rel001"]),
        ]
        for src, tgt, extra_args in fence_edges:
            with self.subTest(edge=f"{src}->{tgt}"):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = _setup_repo(Path(tmp))
                    _create_item(
                        repo,
                        status=src,
                        item_id="bk0001",
                        gate_kind="artifact" if src == "blocked" else None,
                        gate_ref="rel001" if src == "blocked" else None,
                    )
                    if tgt == "graduated":
                        _write_conforming_plan(repo, id6="pl0001", backlog_id6="bk0001")

                    out, err = io.StringIO(), io.StringIO()
                    with redirect_stdout(out), redirect_stderr(err):
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                tgt,
                                "bk0001",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                                *extra_args,
                            ]
                        )
                    self.assertEqual(rc, 0, f"Failed on {src}->{tgt}: {err.getvalue()}")
                    found = _find_item(repo, "bk0001")
                    self.assertEqual(found.parent.name, tgt)
                    self.assertIn(f"- Status: {tgt}", found.read_text(encoding="utf-8"))

    # =========================================================================
    # Case (c): Same-status call still succeeds (self-edge skip)
    # =========================================================================

    def test_same_status_self_edge_status_spelling(self) -> None:
        """Case (c): Same-status call succeeds on --status spelling."""
        for st in ("open", "parked", "graduated", "done"):
            with self.subTest(status=st):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = _setup_repo(Path(tmp))
                    item_path = _create_item(repo, status=st, item_id="bk0001")

                    out, err = io.StringIO(), io.StringIO()
                    with redirect_stdout(out), redirect_stderr(err):
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item_path),
                                "--status",
                                st,
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    self.assertEqual(
                        rc, 0, f"Same-status {st} failed: {err.getvalue()}"
                    )
                    found = _find_item(repo, "bk0001")
                    self.assertEqual(found.parent.name, st)

    def test_same_status_self_edge_positional_spelling(self) -> None:
        """Case (c): Same-status call succeeds on positional spelling."""
        for st in ("open", "parked", "graduated", "done"):
            with self.subTest(status=st):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = _setup_repo(Path(tmp))
                    _create_item(repo, status=st, item_id="bk0001")

                    out, err = io.StringIO(), io.StringIO()
                    with redirect_stdout(out), redirect_stderr(err):
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                st,
                                "bk0001",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    self.assertEqual(
                        rc, 0, f"Same-status {st} failed: {err.getvalue()}"
                    )
                    found = _find_item(repo, "bk0001")
                    self.assertEqual(found.parent.name, st)

    # =========================================================================
    # Case (d): ->blocked without gate flags preserves existing message
    # =========================================================================

    def test_blocked_without_gate_flags_existing_message_status_spelling(self) -> None:
        """Case (d): ->blocked without flags refuses with existing message, not transition message."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(repo, status="open", item_id="bk0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "blocked",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertNotEqual(rc, 0)
            combined = out.getvalue() + err.getvalue()
            self.assertIn("requires --gate-kind and --gate-ref", combined)
            self.assertNotIn("illegal transition", combined.lower())

    def test_blocked_without_gate_flags_existing_message_positional_spelling(
        self,
    ) -> None:
        """Case (d): Positional ->blocked without flags refuses with existing message."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="open", item_id="bk0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "blocked",
                        "bk0001",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertNotEqual(rc, 0)
            combined = out.getvalue() + err.getvalue()
            self.assertIn(
                "Moving backlog item to blocked requires --gate-kind and --gate-ref",
                combined,
            )
            self.assertNotIn("illegal backlog transition", combined.lower())

    # =========================================================================
    # Case (e): Non-backlog artifact is untouched
    # =========================================================================

    def test_non_backlog_spec_transition_untouched(self) -> None:
        """Case (e): Spec transition permitted by its own table succeeds, proving record_type gating."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            spec_file = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "draft"
                / "20261001-spec01-01-spec01-test.spec.md"
            )
            spec_file.write_text(
                "# Spec: Test Spec\n\n- Id: spec01\n- Status: draft\n\n## Workflow history\n- 2026-10-01 draft (tester): initial\n",
                encoding="utf-8",
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "specs",
                        "set",
                        "to-review",
                        "spec01",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0, f"Spec transition failed: {err.getvalue()}")
            target_spec = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "to-review"
                / "20261001-spec01-01-spec01-test.spec.md"
            )
            self.assertTrue(target_spec.exists())

    # =========================================================================
    # Case (f): Agent / JSON surface reports machine-readable rule token
    # =========================================================================

    def test_agent_json_surface_reports_rule_token(self) -> None:
        """Case (f): Refusal is reported on the agent/JSON surface with rule 'status.invalid_transition' and exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="parked", item_id="bk0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--agent",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            stdout_text = out.getvalue()
            payload = json.loads(stdout_text)
            self.assertEqual(payload.get("exit"), 1)
            diagnostics = payload.get("diagnostics", [])
            self.assertTrue(
                any(d.get("rule") == "status.invalid_transition" for d in diagnostics)
            )

    # =========================================================================
    # Case (g): --dry-run on a refused edge refuses rather than previewing
    # =========================================================================

    def test_dry_run_refused_edge_refuses_status_spelling(self) -> None:
        """Case (g): --dry-run on refused edge refuses with exit 1 on --status spelling."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(repo, status="parked", item_id="bk0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "done",
                        "--dry-run",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            self.assertNotIn("--- would move", out.getvalue())

    def test_dry_run_refused_edge_refuses_positional_spelling(self) -> None:
        """Case (g): --dry-run on refused edge refuses with exit 1 on positional spelling."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_item(repo, status="parked", item_id="bk0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--dry-run",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            self.assertNotIn("--- would move", out.getvalue())

    # =========================================================================
    # Case (h): UPPERCASE - Status: source is gated identically (case-fold pin)
    # =========================================================================

    def test_uppercase_status_source_gated_status_spelling(self) -> None:
        """Case (h): Uppercase source token - Status: DONE is refused on illegal move (--status spelling)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo,
                status="done",
                item_id="bk0001",
                raw_status_line="- Status: DONE",
            )
            original_bytes = item_path.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item_path),
                        "--status",
                        "parked",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            combined = out.getvalue() + err.getvalue()
            self.assertIn("illegal transition done -> parked", combined)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")
            self.assertEqual(found.read_bytes(), original_bytes)

    def test_uppercase_status_source_gated_positional_spelling(self) -> None:
        """Case (h): Uppercase source token - Status: DONE is refused on illegal move (positional spelling)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item_path = _create_item(
                repo,
                status="done",
                item_id="bk0001",
                raw_status_line="- Status: DONE",
            )
            original_bytes = item_path.read_bytes()

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "parked",
                        "bk0001",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 1)
            combined = out.getvalue() + err.getvalue()
            self.assertIn("Illegal backlog transition done -> parked", combined)
            found = _find_item(repo, "bk0001")
            self.assertEqual(found.parent.name, "done")
            self.assertEqual(found.read_bytes(), original_bytes)


if __name__ == "__main__":
    unittest.main()

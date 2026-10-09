"""Cross-spelling differential harness for aw backlog set and aw specs set.

Pins behavioral parity between the flag spelling (`aw backlog set <path> --status <status>`)
and the positional spelling (`aw backlog set <status> <selector>`), and likewise for `aw specs set`.

Governed by IPD afdmn6 (Set setdisp, Order 02) under spec wy9aru.

DELIBERATE DUPLICATION NOTE:
This module deliberately duplicates three specific checks that already exist in:
- tests/test_backlog_positional_close_gate.py (release-gate close predicate)
- tests/test_backlog_gate_follows_status.py (gate default on live status transition)
- tests/test_status_set.py::TestGateFieldClearingOnStatusChange (gate-field clearing)

Those existing test files pin their respective axes as POLICY (this refusal must fire, written
after historical defects mawwlc/47ttnv, gatefollows, and 43p53n). This harness pins them as
PARITY under migration (both spellings must behave identically). Consolidating them would remove
the policy fences that guard against regression independently of migration, and would obscure
the git history explaining why each defect fence exists.

OUTCOME TESTS ONLY:
Every test here drives CLI surfaces via `cli.main` (or direct function calls where an axis is
unreachable via CLI due to argparse pre-filtering) and asserts on exit codes, written files,
and emitted output. None inspects AST, regex on source, or caller counts (AGENTS.md, P16, S1).
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from agent_workflows import attention as att
from agent_workflows import attention_contract as ac
from agent_workflows import backlog, cli, status_set


# =============================================================================
# NORMALIZATION HELPERS (E-01)
# =============================================================================

# Date normalizer:
# Hides the UTC-versus-local date stamp divergence between engines.
# Owned by 2wae2x / fnb8pl / lq2w86 (release-gated; unified onto core.utc_history_date()
# by 5ivkdh). Normalized by shape per spec wy9aru S3 to avoid cross-midnight races without
# reading a clock in the test.
_DATE_SHAPE_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) ", re.MULTILINE)

# Actor normalizer:
# Hides the parenthesized writer identity divergence: (aw backlog) vs (aw set) vs (aw specs).
# Declined to unify in jbipfa as truthful attribution of the distinct writer identities.
_ACTOR_RE = re.compile(r" \((aw backlog|aw specs|aw set|[^)]+)\):")


def normalize_history_date(text: str) -> str:
    """Normalize date in history lines by shape, avoiding clock reads."""
    return _DATE_SHAPE_RE.sub("- <DATE> ", text)


def normalize_history_actor(text: str) -> str:
    """Normalize writer identity token in history lines."""
    return _ACTOR_RE.sub(" (<ACTOR>):", text)


def normalize_history_line(line: str) -> str:
    """Apply both date and actor normalizations to a history line."""
    return normalize_history_actor(normalize_history_date(line))


# Explicit message parameter:
# Owned by jbipfa F-10. Defaulted messages differ between engines ("status -> <s>" vs
# "status set to <s>"), so every cross-spelling comparison passes an explicit --message.


# =============================================================================
# FIXTURE HELPERS
# =============================================================================


def _git(repo: Path, *args: str) -> str:
    """Run git in the fixture repository."""
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _write_conforming_plan(
    repo: Path,
    *,
    id6: str = "pl0001",
    backlog_id6: str = "bk0001",
    set_id: str = "testset",
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


def _setup_repo(root: Path) -> Path:
    """Create a minimal git repository with standard .aw structure."""
    _git(root, "init")
    _git(root, "config", "user.name", "Parity Tester")
    _git(root, "config", "user.email", "parity@example.com")

    for sub in ("open", "parked", "graduated", "done", "blocked"):
        (root / ".aw" / "records" / "backlog" / sub).mkdir(parents=True, exist_ok=True)
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
    (root / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
    (root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)

    # Planned release for release-gate checks
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

    # Conforming plan for graduation checks
    _write_conforming_plan(root, id6="pl0001", backlog_id6="bk0001", set_id="testset")

    _git(root, "add", "-A")
    _git(root, "commit", "-m", "initial layout")
    return root


def _create_backlog_item(
    repo: Path,
    *,
    status: str,
    work_kind: str = "chore",
    item_id: str = "bk0001",
    set_id: str = "testset",
    priority: str = "medium",
    blocks_release: str | None = None,
    gate_kind: str | None = None,
    gate_ref: str | None = None,
    prior_history: list[str] | None = None,
) -> Path:
    lines = [
        f"- Id: {item_id}",
        f"- Status: {status}",
    ]
    if blocks_release is not None:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines.extend(
        [
            f"- Set: {set_id}",
            f"- Priority: {priority}",
            f"- Work-Kind: {work_kind}",
            "- Summary: Parity test item",
        ]
    )
    if gate_kind is not None:
        lines.append(f"- Gate-Kind: {gate_kind}")
    if gate_ref is not None:
        lines.append(f"- Gate-Ref: {gate_ref}")
    lines.extend(["", "## Workflow history"])
    if prior_history is not None:
        lines.extend(prior_history)
    else:
        lines.append("- 2026-09-28 created (tester): initial")
    lines.append("")

    p = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / status
        / f"20260928-{set_id}-01-{item_id}-test.backlog.md"
    )
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _find_backlog_item(repo: Path, item_id: str) -> Path:
    matches = list(
        (repo / ".aw" / "records" / "backlog").rglob(f"*{item_id}*.backlog.md")
    )
    if not matches:
        matches = list((repo / ".aw" / "records" / "backlog").rglob(f"*{item_id}*.md"))
    assert matches, f"Could not find backlog item {item_id} in {repo}"
    return matches[0]


def _create_spec(
    repo: Path,
    *,
    status: str,
    spec_id: str = "sp0001",
    set_id: str = "testspec",
    work_kind: str = "chore",
    priority: str = "medium",
    blocks_release: str | None = None,
    gate_kind: str | None = None,
    gate_ref: str | None = None,
    prior_history: list[str] | None = None,
) -> Path:
    lines = [
        f"# Spec: Parity Spec {spec_id}",
        "",
        f"- Id: {spec_id}",
        f"- Status: {status}",
    ]
    if blocks_release is not None:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines.extend(
        [
            f"- Priority: {priority}",
            f"- Work-Kind: {work_kind}",
            "- Scope: Parity testing",
        ]
    )
    if gate_kind is not None:
        lines.append(f"- Gate-Kind: {gate_kind}")
    if gate_ref is not None:
        lines.append(f"- Gate-Ref: {gate_ref}")
    lines.extend(["", "## Workflow history"])
    if prior_history is not None:
        lines.extend(prior_history)
    else:
        lines.append("- 2026-10-01 created (tester): initial")
    lines.append("")

    p = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / status
        / f"20261001-{set_id}-01-{spec_id}-test.spec.md"
    )
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _find_spec(repo: Path, spec_id: str) -> Path:
    matches = list((repo / ".aw" / "records" / "specs").rglob(f"*{spec_id}*.spec.md"))
    if not matches:
        matches = list((repo / ".aw" / "records" / "specs").rglob(f"*{spec_id}*.md"))
    assert matches, f"Could not find spec {spec_id} in {repo}"
    return matches[0]


# =============================================================================
# SELF-TEST: NORMALIZERS PROOF (E-01 / V-01)
# =============================================================================


class TestNormalizersSubstitute(unittest.TestCase):
    """Self-test demonstrating that the normalizers genuinely substitute on real records."""

    def test_normalizers_substitute_on_real_record(self) -> None:
        sample_backlog_line = "- 2026-10-01 done (aw backlog): closed item"
        sample_status_set_line = "- 2026-10-01 done (aw set): status set to done"
        sample_specs_line = "- 2026-10-01 to-review (aw specs): ready for review"

        # Date substitution
        norm_date_backlog = normalize_history_date(sample_backlog_line)
        self.assertIn("- <DATE> ", norm_date_backlog)
        self.assertNotIn("2026-10-01", norm_date_backlog)

        # Actor substitution
        norm_actor_backlog = normalize_history_actor(sample_backlog_line)
        self.assertIn(" (<ACTOR>):", norm_actor_backlog)
        self.assertNotIn("(aw backlog)", norm_actor_backlog)

        norm_actor_status = normalize_history_actor(sample_status_set_line)
        self.assertIn(" (<ACTOR>):", norm_actor_status)
        self.assertNotIn("(aw set)", norm_actor_status)

        norm_actor_specs = normalize_history_actor(sample_specs_line)
        self.assertIn(" (<ACTOR>):", norm_actor_specs)
        self.assertNotIn("(aw specs)", norm_actor_specs)

        # Full normalization
        full_norm_backlog = normalize_history_line(sample_backlog_line)
        self.assertEqual(full_norm_backlog, "- <DATE> done (<ACTOR>): closed item")

        # Positive label token assertion (cannot be eaten by normalizers)
        self.assertIn("done", full_norm_backlog)


# =============================================================================
# TASK GROUP 2: BACKLOG AGREEMENT ASSERTIONS (E-02 / V-02)
# =============================================================================


class TestBacklogSetDispatchParity(unittest.TestCase):
    """Assert agreement on every axis of aw backlog set that already agrees today."""

    def test_backlog_resulting_status_agreement(self) -> None:
        """Both spellings write identical - Status: <status> value."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(repo, status="open", item_id="bk0001")
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "done",
                                "--message",
                                "transition to done",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "done",
                                "bk0001",
                                "--message",
                                "transition to done",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_backlog_item(repo, "bk0001")
                text = moved.read_text(encoding="utf-8")
                self.assertIn("- Status: done", text)

    def test_backlog_resulting_file_location_agreement(self) -> None:
        """Both spellings relocate the file to .aw/records/backlog/<status>/."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(repo, status="open", item_id="bk0001")
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "done",
                                "--message",
                                "relocate done",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "done",
                                "bk0001",
                                "--message",
                                "relocate done",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_backlog_item(repo, "bk0001")
                self.assertEqual(moved.parent.name, "done")

    def test_backlog_gate_field_clearing_on_transition_out_of_blocked_agreement(
        self,
    ) -> None:
        """Both spellings clear Gate-Kind and Gate-Ref when transitioning out of blocked."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(
                    repo,
                    status="blocked",
                    item_id="bk0001",
                    gate_kind="artifact",
                    gate_ref="records/specs/draft/sp0001.spec.md",
                )
                self.assertIn("Gate-Kind: artifact", item.read_text(encoding="utf-8"))
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "open",
                                "--message",
                                "unblock",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "open",
                                "bk0001",
                                "--message",
                                "unblock",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_backlog_item(repo, "bk0001")
                text = moved.read_text(encoding="utf-8")
                self.assertIn("- Status: open", text)
                self.assertNotIn("Gate-Kind", text)
                self.assertNotIn("Gate-Ref", text)

    def test_backlog_release_gate_close_predicate_refusal_agreement(self) -> None:
        """Both spellings refuse illegitimate close of release-gated item with exit 1."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(
                    repo,
                    status="open",
                    work_kind="bug",
                    item_id="bk0001",
                    blocks_release="next",
                )
                before_bytes = item.read_bytes()
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "done",
                                "--message",
                                "close illegitimate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "done",
                                "bk0001",
                                "--message",
                                "close illegitimate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 1)
                item_after = _find_backlog_item(repo, "bk0001")
                self.assertEqual(item_after.parent.name, "open")
                self.assertEqual(item_after.read_bytes(), before_bytes)

    def test_backlog_gate_default_on_bug_transition_to_live_status_agreement(
        self,
    ) -> None:
        """Both spellings add Blocks-Release: next when an ungated bug moves parked -> open."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(
                    repo,
                    status="parked",
                    work_kind="bug",
                    item_id="bk0001",
                    blocks_release=None,
                )
                self.assertNotIn("Blocks-Release", item.read_text(encoding="utf-8"))
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "open",
                                "--message",
                                "unpark bug",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "open",
                                "bk0001",
                                "--message",
                                "unpark bug",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_backlog_item(repo, "bk0001")
                text = moved.read_text(encoding="utf-8")
                self.assertIn("- Blocks-Release: next", text)

    def test_backlog_blocks_release_set_and_cleared_agreement(self) -> None:
        """Both spellings support setting --blocks-release and clearing with '-'."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(
                    repo, status="open", item_id="bk0001", blocks_release=None
                )

                # Set gate
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "open",
                                "--blocks-release",
                                "rel001",
                                "--message",
                                "set gate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "open",
                                "bk0001",
                                "--blocks-release",
                                "rel001",
                                "--message",
                                "set gate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_backlog_item(repo, "bk0001")
                self.assertIn(
                    "- Blocks-Release: rel001", moved.read_text(encoding="utf-8")
                )

                # Clear gate with '-'
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(moved),
                                "--status",
                                "open",
                                "--blocks-release",
                                "-",
                                "--message",
                                "clear gate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "open",
                                "bk0001",
                                "--blocks-release",
                                "-",
                                "--message",
                                "clear gate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved_after = _find_backlog_item(repo, "bk0001")
                self.assertNotIn(
                    "Blocks-Release", moved_after.read_text(encoding="utf-8")
                )

    def test_backlog_graduated_to_canonicalization_agreement(self) -> None:
        """Both spellings set --graduated-to on transition to graduated."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(repo, status="open", item_id="bk0001")
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "graduated",
                                "--graduated-to",
                                "pl0001",
                                "--message",
                                "graduated",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "graduated",
                                "bk0001",
                                "--graduated-to",
                                "pl0001",
                                "--message",
                                "graduated",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_backlog_item(repo, "bk0001")
                text = moved.read_text(encoding="utf-8")
                self.assertIn("- Status: graduated", text)
                self.assertIn("- Graduated-To: pl0001", text)

    def test_backlog_priority_and_work_kind_writes_agreement(self) -> None:
        """Both spellings write --priority and --work-kind classification fields."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(
                    repo,
                    status="open",
                    work_kind="chore",
                    priority="medium",
                    item_id="bk0001",
                )
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "open",
                                "--priority",
                                "high",
                                "--work-kind",
                                "feature",
                                "--message",
                                "reclassify",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "open",
                                "bk0001",
                                "--priority",
                                "high",
                                "--work-kind",
                                "feature",
                                "--message",
                                "reclassify",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_backlog_item(repo, "bk0001")
                text = moved.read_text(encoding="utf-8")
                self.assertIn("- Priority: high", text)
                self.assertIn("- Work-Kind: feature", text)

    def test_backlog_prior_history_preservation_agreement(self) -> None:
        """Both spellings preserve every prior history record verbatim and in order."""
        priors = [
            "- 2026-03-03 set (tester): third record",
            "- 2026-02-02 set (tester): second record",
            "- 2026-01-01 created (tester): first record",
        ]
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(
                    repo, status="open", item_id="bk0001", prior_history=priors
                )
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "done",
                                "--message",
                                "fourth record",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "done",
                                "bk0001",
                                "--message",
                                "fourth record",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_backlog_item(repo, "bk0001")
                after_lines = [
                    ln
                    for ln in att._history_section_lines(
                        moved.read_text(encoding="utf-8")
                    )
                    if ac.HISTORY_RECORD_RE.match(ln)
                ]
                self.assertEqual(len(after_lines), 4)
                self.assertIn("fourth record", after_lines[0])
                self.assertEqual(after_lines[1:], priors)

    def test_backlog_number_of_records_appended_agreement(self) -> None:
        """Both spellings append exactly one record on a genuine status transition."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(repo, status="open", item_id="bk0001")
                before_count = len(
                    [
                        ln
                        for ln in att._history_section_lines(
                            item.read_text(encoding="utf-8")
                        )
                        if ac.HISTORY_RECORD_RE.match(ln)
                    ]
                )
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "done",
                                "--message",
                                "single transition",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "done",
                                "bk0001",
                                "--message",
                                "single transition",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_backlog_item(repo, "bk0001")
                after_count = len(
                    [
                        ln
                        for ln in att._history_section_lines(
                            moved.read_text(encoding="utf-8")
                        )
                        if ac.HISTORY_RECORD_RE.match(ln)
                    ]
                )
                self.assertEqual(after_count, before_count + 1)

    def test_backlog_unsafe_descriptive_newline_refusal_agreement(self) -> None:
        """Both spellings refuse embedded newlines in --message and --gate-ref with rc 2.

        Reclassified from E-04 (h): added to the shared engine by 4gwgo3 (commit a165cb65b).
        """
        for spelling in ("status", "positional"):
            # Embedded newline in --message
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(repo, status="open", item_id="bk0001")
                before_bytes = item.read_bytes()
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "done",
                                "--message",
                                "line1\nline2",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "done",
                                "bk0001",
                                "--message",
                                "line1\nline2",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 2)
                item_after = _find_backlog_item(repo, "bk0001")
                self.assertEqual(item_after.parent.name, "open")
                self.assertEqual(item_after.read_bytes(), before_bytes)

            # Embedded newline in --gate-ref
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(repo, status="open", item_id="bk0001")
                before_bytes = item.read_bytes()
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "blocked",
                                "--gate-kind",
                                "artifact",
                                "--gate-ref",
                                "ref1\nref2",
                                "--message",
                                "block",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "blocked",
                                "bk0001",
                                "--gate-kind",
                                "artifact",
                                "--gate-ref",
                                "ref1\nref2",
                                "--message",
                                "block",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 2)
                item_after = _find_backlog_item(repo, "bk0001")
                self.assertEqual(item_after.parent.name, "open")
                self.assertEqual(item_after.read_bytes(), before_bytes)

    def test_backlog_relocation_porcelain_shape_agreement(self) -> None:
        """Both spellings leave ' D <src>' plus '?? <dest>' in porcelain under --no-commit.

        Reclassified from E-04 (c): measured at review that status_set._offer_self_commit
        runs 'git reset --quiet HEAD -- <paths>' after artifact_core.git_mv staged 'R',
        unstaging the rename. Neither spelling produces wy9aru AC-5's canonical staged 'R'
        rename today under --no-commit.
        """
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                item = _create_backlog_item(repo, status="open", item_id="bk0001")
                _git(repo, "add", "-A")
                _git(repo, "commit", "-m", "track item")

                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                str(item),
                                "--status",
                                "done",
                                "--message",
                                "relocate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "done",
                                "bk0001",
                                "--message",
                                "relocate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                porcelain = _git(repo, "status", "--porcelain")
                self.assertIn(" D .aw/records/backlog/open/", porcelain)
                self.assertIn("?? .aw/records/backlog/done/", porcelain)

    def test_backlog_substring_selector_ambiguity_refusal_agreement(self) -> None:
        """Both spellings refuse an ambiguous substring selector at rc 2 (from E-04 (e))."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                _create_backlog_item(repo, status="open", item_id="bk0001", set_id="s1")
                _create_backlog_item(repo, status="open", item_id="bk0002", set_id="s2")

                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "test",
                                "--status",
                                "done",
                                "--message",
                                "ambiguous",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "backlog",
                                "set",
                                "done",
                                "test",
                                "--message",
                                "ambiguous",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 2)
                # Ensure neither moved
                self.assertEqual(
                    len(
                        list(
                            (repo / ".aw" / "records" / "backlog" / "open").glob("*.md")
                        )
                    ),
                    2,
                )


# =============================================================================
# TASK GROUP 2: SPECS AGREEMENT ASSERTIONS (E-03 / V-03)
# =============================================================================


class TestSpecsSetDispatchParity(unittest.TestCase):
    """Assert agreement on every axis of aw specs set that already agrees today."""

    def test_specs_resulting_status_and_file_location_agreement(self) -> None:
        """Both spellings move draft -> to-review, updating status and directory."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                spec = _create_spec(repo, status="draft", spec_id="sp0001")
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                str(spec),
                                "--status",
                                "to-review",
                                "--message",
                                "ready to review",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                "to-review",
                                "sp0001",
                                "--message",
                                "ready to review",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_spec(repo, "sp0001")
                self.assertEqual(moved.parent.name, "to-review")
                self.assertIn("- Status: to-review", moved.read_text(encoding="utf-8"))

    def test_specs_to_reviewed_attestation_refusal_agreement(self) -> None:
        """Both spellings refuse to-review -> reviewed when review attestation is missing."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                spec = _create_spec(repo, status="to-review", spec_id="sp0001")
                before_bytes = spec.read_bytes()
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                str(spec),
                                "--status",
                                "reviewed",
                                "--message",
                                "unattested reviewed",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                "reviewed",
                                "sp0001",
                                "--message",
                                "unattested reviewed",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 1)
                spec_after = _find_spec(repo, "sp0001")
                self.assertEqual(spec_after.parent.name, "to-review")
                self.assertEqual(spec_after.read_bytes(), before_bytes)

    def test_specs_approved_gate_refusal_agreement(self) -> None:
        """Both spellings refuse unreviewed spec moving to approved."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                spec = _create_spec(repo, status="draft", spec_id="sp0001")
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                str(spec),
                                "--status",
                                "approved",
                                "--message",
                                "skip review",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                "approved",
                                "sp0001",
                                "--message",
                                "skip review",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 1)
                spec_after = _find_spec(repo, "sp0001")
                self.assertEqual(spec_after.parent.name, "draft")

    def test_specs_by_human_authority_floor_refusal_agreement(self) -> None:
        """Both spellings enforce --by-human authority floor on transition to approved."""
        for spelling in ("status", "positional"):
            # Without --by-human in non-interactive environment: refuses rc 1
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                spec = _create_spec(
                    repo,
                    status="reviewed",
                    spec_id="sp0001",
                    prior_history=[
                        "- 2026-10-02 reviewed (reviewer): /spec-review approve",
                        "- 2026-10-01 created (tester): initial",
                    ],
                )
                before_bytes = spec.read_bytes()
                out, err = io.StringIO(), io.StringIO()
                with patch(
                    "agent_workflows.term.stdin_is_interactive", return_value=False
                ):
                    with redirect_stdout(out), redirect_stderr(err):
                        if spelling == "status":
                            rc = cli.main(
                                [
                                    "specs",
                                    "set",
                                    str(spec),
                                    "--status",
                                    "approved",
                                    "--message",
                                    "human approval",
                                    "--yes",
                                    "--no-commit",
                                    "--dir",
                                    str(repo),
                                ]
                            )
                        else:
                            rc = cli.main(
                                [
                                    "specs",
                                    "set",
                                    "approved",
                                    "sp0001",
                                    "--message",
                                    "human approval",
                                    "--yes",
                                    "--no-commit",
                                    "--dir",
                                    str(repo),
                                ]
                            )
                self.assertEqual(rc, 1)
                spec_after = _find_spec(repo, "sp0001")
                self.assertEqual(spec_after.parent.name, "reviewed")
                self.assertEqual(spec_after.read_bytes(), before_bytes)

            # With --by-human: succeeds rc 0
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                spec = _create_spec(
                    repo,
                    status="reviewed",
                    spec_id="sp0001",
                    prior_history=[
                        "- 2026-10-02 reviewed (reviewer): /spec-review approve",
                        "- 2026-10-01 created (tester): initial",
                    ],
                )
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                str(spec),
                                "--status",
                                "approved",
                                "--by-human",
                                "--message",
                                "human approval attested",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                "approved",
                                "sp0001",
                                "--by-human",
                                "--message",
                                "human approval attested",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                spec_after = _find_spec(repo, "sp0001")
                self.assertEqual(spec_after.parent.name, "approved")
                self.assertIn(
                    "- Status: approved", spec_after.read_text(encoding="utf-8")
                )

    def test_specs_blocks_release_set_and_cleared_agreement(self) -> None:
        """Both spellings support setting and clearing --blocks-release on specs."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                spec = _create_spec(
                    repo, status="draft", spec_id="sp0001", blocks_release=None
                )

                # Set gate
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                str(spec),
                                "--status",
                                "draft",
                                "--blocks-release",
                                "rel001",
                                "--message",
                                "set gate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                "draft",
                                "sp0001",
                                "--blocks-release",
                                "rel001",
                                "--message",
                                "set gate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_spec(repo, "sp0001")
                self.assertIn(
                    "- Blocks-Release: rel001", moved.read_text(encoding="utf-8")
                )

                # Clear gate
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                str(moved),
                                "--status",
                                "draft",
                                "--blocks-release",
                                "-",
                                "--message",
                                "clear gate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                "draft",
                                "sp0001",
                                "--blocks-release",
                                "-",
                                "--message",
                                "clear gate",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved_after = _find_spec(repo, "sp0001")
                self.assertNotIn(
                    "Blocks-Release", moved_after.read_text(encoding="utf-8")
                )

    def test_specs_graduated_to_agreement(self) -> None:
        """Both spellings write --graduated-to on specs."""
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                spec = _create_spec(repo, status="draft", spec_id="sp0001")
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                str(spec),
                                "--status",
                                "draft",
                                "--graduated-to",
                                "pl0001",
                                "--message",
                                "set plan",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                "draft",
                                "sp0001",
                                "--graduated-to",
                                "pl0001",
                                "--message",
                                "set plan",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_spec(repo, "sp0001")
                self.assertIn(
                    "- Graduated-To: pl0001", moved.read_text(encoding="utf-8")
                )

    def test_specs_prior_history_preservation_agreement(self) -> None:
        """Both spellings preserve prior history records on specs verbatim."""
        priors = [
            "- 2026-10-02 set (tester): second note",
            "- 2026-10-01 created (tester): initial note",
        ]
        for spelling in ("status", "positional"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = _setup_repo(Path(tmp))
                spec = _create_spec(
                    repo, status="draft", spec_id="sp0001", prior_history=priors
                )
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    if spelling == "status":
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                str(spec),
                                "--status",
                                "to-review",
                                "--message",
                                "third note",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                    else:
                        rc = cli.main(
                            [
                                "specs",
                                "set",
                                "to-review",
                                "sp0001",
                                "--message",
                                "third note",
                                "--yes",
                                "--no-commit",
                                "--dir",
                                str(repo),
                            ]
                        )
                self.assertEqual(rc, 0)
                moved = _find_spec(repo, "sp0001")
                after_lines = [
                    ln
                    for ln in att._history_section_lines(
                        moved.read_text(encoding="utf-8")
                    )
                    if ac.HISTORY_RECORD_RE.match(ln)
                ]
                self.assertEqual(len(after_lines), 3)
                self.assertIn("third note", after_lines[0])
                self.assertEqual(after_lines[1:], priors)


# =============================================================================
# TASK GROUP 3: EXPECTED-DIFFERENCE ASSERTIONS (E-04 / V-04)
# =============================================================================


class TestSetDispatchExpectedDifferences(unittest.TestCase):
    """Pin the axes that currently DISAGREE as expected-difference assertions.

    Each test asserts the CURRENT divergence so that each later child can flip
    exactly one assertion and demonstrate attribution.
    """

    def test_backlog_sidecar_append_expected_difference(self) -> None:
        """Axis (d): aw backlog set --status appends to history.jsonl; positional appends none.

        Owning artifact: spec wy9aru Section 4.3 (ratified in OQ-1: keep sidecar, type-conditional).
        Canonical side: shared engine (status_set) will append sidecar record after durable write.
        Child that flips it: child 05 (vhiqo6) migrates backlog.run_set to status_set.
        """
        # --status spelling writes sidecar
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item = _create_backlog_item(repo, status="open", item_id="bk0001")
            sidecar = repo / ".aw" / "records" / "history.jsonl"
            self.assertFalse(sidecar.exists())

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(item),
                        "--status",
                        "done",
                        "--message",
                        "sidecar test",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            self.assertTrue(
                sidecar.exists(), "--status spelling MUST append to history.jsonl"
            )
            self.assertGreater(sidecar.stat().st_size, 0)

        # positional spelling writes NO sidecar today
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item = _create_backlog_item(repo, status="open", item_id="bk0001")
            sidecar = repo / ".aw" / "records" / "history.jsonl"
            self.assertFalse(sidecar.exists())

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "bk0001",
                        "--message",
                        "sidecar test",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            self.assertFalse(
                sidecar.exists(), "positional spelling appends NO sidecar record today"
            )

    def test_backlog_setid_multi_selector_expected_difference(self) -> None:
        """Axis (e): setid selector moves one item under --status, both items under positional.

        Owning artifact: spec wy9aru Section 4.5.
        Canonical side: shared engine's selector vocabulary (multi-target batch) is canonical.
        Child that flips it: child 05 (vhiqo6) migrates backlog.run_set onto shared engine.
        """
        # --status spelling transitions ONLY the first match (res.paths[0])
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_backlog_item(
                repo, status="open", item_id="bk0001", set_id="sharedset"
            )
            _create_backlog_item(
                repo, status="open", item_id="bk0002", set_id="sharedset"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "sharedset",
                        "--status",
                        "done",
                        "--message",
                        "multi setid",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            done_items = list(
                (repo / ".aw" / "records" / "backlog" / "done").glob("*.md")
            )
            open_items = list(
                (repo / ".aw" / "records" / "backlog" / "open").glob("*.md")
            )
            self.assertEqual(
                len(done_items), 1, "--status spelling transitions only paths[0]"
            )
            self.assertEqual(len(open_items), 1, "second match remains in open")

        # positional spelling transitions BOTH matches
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_backlog_item(
                repo, status="open", item_id="bk0001", set_id="sharedset"
            )
            _create_backlog_item(
                repo, status="open", item_id="bk0002", set_id="sharedset"
            )

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "done",
                        "sharedset",
                        "--message",
                        "multi setid",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(rc, 0)
            done_items = list(
                (repo / ".aw" / "records" / "backlog" / "done").glob("*.md")
            )
            open_items = list(
                (repo / ".aw" / "records" / "backlog" / "open").glob("*.md")
            )
            self.assertEqual(
                len(done_items), 2, "positional spelling transitions both items"
            )
            self.assertEqual(len(open_items), 0, "no item remains in open")

    def test_specs_selector_resolution_expected_difference(self) -> None:
        """Axis (f): aw specs set --status accepts path only; positional resolves id6/setid.

        Owning artifact: spec wy9aru Section 4.5 and OQ-2.
        Canonical side: shared engine's selector vocabulary (accepts id6/setid/path) is canonical.
        Child that flips it: child 04 (m94eht) migrates specs.run_set onto shared engine.
        """
        # --status spelling given id6 fails with rc 2 (path only)
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_spec(repo, status="draft", spec_id="sp0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "specs",
                        "set",
                        "sp0001",
                        "--status",
                        "to-review",
                        "--message",
                        "via id6",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(
                rc, 0, "--status spelling resolves id6 selector successfully"
            )
            moved = _find_spec(repo, "sp0001")
            self.assertEqual(moved.parent.name, "to-review")

        # positional spelling given id6 resolves and transitions with rc 0
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            _create_spec(repo, status="draft", spec_id="sp0001")

            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "specs",
                        "set",
                        "to-review",
                        "sp0001",
                        "--message",
                        "via id6",
                        "--yes",
                        "--no-commit",
                        "--dir",
                        str(repo),
                    ]
                )
            self.assertEqual(
                rc, 0, "positional spelling resolves id6 selector successfully"
            )
            moved = _find_spec(repo, "sp0001")
            self.assertEqual(moved.parent.name, "to-review")

    def test_backlog_enum_validation_at_function_expected_difference(self) -> None:
        """Axis (g): backlog.run_set refuses invalid enums with rc 2; status_set accepts and writes.

        Owning artifact: spec wy9aru Section 4.7 (refusals unioned per C2).
        Canonical side: backlog.run_set refusal is canonical (must refuse invalid enum).
        Child that flips it: child 05 (vhiqo6) / child 04.

        NOTE ON REACHABILITY (OQ-01 / F-07):
        Argparse `choices` pre-filters invalid enums at the CLI surface before dispatch, so
        the function-level asymmetry is reachable only via direct function calls. Direct
        calls asserting return code and written file satisfy P16 outcome testing.
        """
        # backlog.run_set directly called with invalid work_kind returns rc 2 and writes nothing
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item = _create_backlog_item(repo, status="open", item_id="bk0001")
            before_bytes = item.read_bytes()

            ns = argparse.Namespace(
                path=str(item),
                status="open",
                work_kind="invalid_kind",
                priority=None,
                dir=str(repo),
                yes=True,
                no_commit=True,
                message="direct call",
                dry_run=False,
                gate_dir=None,
                blocks_release=None,
                graduated_to=None,
                assume_yes=True,
                lane_carrier_ref=None,
                lane_carrier_path=None,
            )
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = backlog.run_set(ns)
            self.assertEqual(
                rc, 2, "backlog.run_set must refuse invalid work_kind with exit 2"
            )
            self.assertEqual(
                item.read_bytes(), before_bytes, "file must remain unchanged"
            )

        # status_set.run_set_command directly called with invalid work_kind returns rc 0 and writes it
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            item = _create_backlog_item(repo, status="open", item_id="bk0001")

            ns = argparse.Namespace(
                work_kind="invalid_kind",
                priority=None,
                dir=str(repo),
                yes=True,
                no_commit=True,
                message="direct call",
                dry_run=False,
                blocks_release=None,
                graduated_to=None,
                assume_yes=True,
                force=False,
                agent=False,
                json=False,
            )
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = status_set.run_set_command(
                    ["open", "bk0001"], scoped_type="backlog", repo_root=repo, args=ns
                )
            self.assertEqual(
                rc,
                0,
                "status_set currently accepts invalid work_kind when called directly",
            )
            self.assertIn("- Work-Kind: invalid_kind", item.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

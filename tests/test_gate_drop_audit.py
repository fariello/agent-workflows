"""Behavioral tests for tools/gate_drop_audit.py.

Asserts on auditor outputs, exit codes, and fixture states over synthetic temp-repo fixtures.
Does NOT inspect, ast-parse, regex-search, or substring-match the auditor source code.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory
from typing import Any, Dict, Tuple


AUDITOR_PATH = Path(__file__).resolve().parent.parent / "tools" / "gate_drop_audit.py"


def _create_minimal_repo(root: Path) -> Path:
    """Create a minimal conformant repository structure."""
    for p in (
        root / ".aw" / "records" / "releases",
        root / ".aw" / "records" / "backlog" / "open",
        root / ".aw" / "records" / "backlog" / "done",
        root / ".aw" / "records" / "plans" / "pending",
        root / ".aw" / "records" / "plans" / "executed",
        root / ".aw" / "records" / "plans" / "superseded",
        root / ".aw" / "records" / "specs" / "approved",
    ):
        p.mkdir(parents=True, exist_ok=True)

    # create a planned release
    rel_file = (
        root
        / ".aw"
        / "records"
        / "releases"
        / "20260901-rel001-01-rel001-v1.release.md"
    )
    rel_file.write_text(
        "# Release: 1.0.0\n\n"
        "- Id: rel001\n"
        "- Status: planned\n"
        "- Version: 1.0.0\n"
        "- Summary: Test release\n",
        encoding="utf-8",
    )
    return root


def _run_audit(repo: Path) -> Tuple[int, Dict[str, Any]]:
    """Run the auditor CLI with --json and return (exit_code, parsed_json)."""
    proc = subprocess.run(
        [sys.executable, str(AUDITOR_PATH), "--json", "--repo", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    data = (
        json.loads(proc.stdout) if proc.returncode == 0 and proc.stdout.strip() else {}
    )
    return proc.returncode, data


class TestGateDropAudit(unittest.TestCase):
    """Behavioral tests pinning the gate-drop auditor's classification on synthetic fixtures."""

    def test_ungated_done_item_not_reported(self) -> None:
        """An ungated done item is not reported as a finding."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260920-item01-01-item01-ungated.backlog.md"
            )
            item.write_text(
                "- Id: item01\n"
                "- Status: done\n"
                "- Set: item01\n"
                "- Priority: medium\n"
                "- Work-Kind: feature\n"
                "- Summary: Ungated done item\n\n"
                "## Workflow history\n"
                "- 2026-09-20 done (aw set): status set to done\n",
                encoding="utf-8",
            )
            code, data = _run_audit(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data["total_findings"], 0)
            self.assertEqual(data["findings"], [])

    def test_gated_done_item_no_carrier_reported(self) -> None:
        """A gated done item with no carrier is reported with reason_class no-carrier."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260920-item01-01-item01-nocarrier.backlog.md"
            )
            item.write_text(
                "- Id: item01\n"
                "- Status: done\n"
                "- Blocks-Release: next\n"
                "- Set: item01\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Gated bug with no carrier\n\n"
                "## Workflow history\n"
                "- 2026-09-20 done (aw set): status set to done\n",
                encoding="utf-8",
            )
            code, data = _run_audit(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data["total_findings"], 1)
            finding = data["findings"][0]
            self.assertEqual(finding["id6"], "item01")
            self.assertEqual(finding["reason_class"], "no-carrier")
            self.assertEqual(finding["partition"], "post-predicate")
            self.assertEqual(finding["close_date"], "2026-09-20")

    def test_gated_done_item_executed_carrier_handoff_not_reported(self) -> None:
        """A gated done item whose same-gate From-Backlog carrier is executed is a legitimate handoff and NOT reported."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            plan = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20260920-p01-01-p01-carrier.ipd.md"
            )
            plan.write_text(
                "# IPD: Fix item01\n\n"
                "- Id: p01\n"
                "- Status: executed\n"
                "- From-Backlog: item01\n"
                "- Blocks-Release: next\n"
                "- Set: p01\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
            )
            item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260920-item01-01-item01-handed-off.backlog.md"
            )
            item.write_text(
                "- Id: item01\n"
                "- Status: done\n"
                "- Blocks-Release: next\n"
                "- Set: item01\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Gated bug handed off to executed plan\n\n"
                "## Workflow history\n"
                "- 2026-09-20 done (aw set): status set to done\n",
                encoding="utf-8",
            )
            code, data = _run_audit(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data["total_findings"], 0)

    def test_gated_done_item_superseded_carrier_reported_carrier_not_executed(
        self,
    ) -> None:
        """A gated done item whose only same-gate carrier is superseded is reported as carrier-not-executed."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            plan = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "superseded"
                / "20260920-p01-01-p01-super.ipd.md"
            )
            plan.write_text(
                "# IPD: Fix item01\n\n"
                "- Id: p01\n"
                "- Status: superseded\n"
                "- From-Backlog: item01\n"
                "- Blocks-Release: next\n"
                "- Set: p01\n"
                "- Scope: Fix\n"
                "- Scope-Paths: foo.py\n",
                encoding="utf-8",
            )
            item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260920-item01-01-item01-supercarrier.backlog.md"
            )
            item.write_text(
                "- Id: item01\n"
                "- Status: done\n"
                "- Blocks-Release: next\n"
                "- Set: item01\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Gated bug with superseded carrier\n\n"
                "## Workflow history\n"
                "- 2026-09-20 done (aw set): status set to done\n",
                encoding="utf-8",
            )
            code, data = _run_audit(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data["total_findings"], 1)
            finding = data["findings"][0]
            self.assertEqual(finding["id6"], "item01")
            self.assertEqual(finding["reason_class"], "carrier-not-executed")

    def test_pre_boundary_close_partitioned_pre_predicate(self) -> None:
        """An item closed before the 2026-08-25 boundary date lands in the pre-predicate bucket."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260820-pre001-01-pre001-early-bug.backlog.md"
            )
            item.write_text(
                "- Id: pre001\n"
                "- Status: done\n"
                "- Blocks-Release: next\n"
                "- Set: pre001\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Pre-predicate bug\n\n"
                "## Workflow history\n"
                "- 2026-08-21 done (aw set): Closed by early Set\n",
                encoding="utf-8",
            )
            code, data = _run_audit(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data["total_findings"], 1)
            finding = data["findings"][0]
            self.assertEqual(finding["partition"], "pre-predicate")
            self.assertEqual(finding["close_date"], "2026-08-21")
            self.assertEqual(data["partition_counts"]["pre_predicate"], 1)

    def test_undated_item_partitioned_undated(self) -> None:
        """An item with no close line in ## Workflow history (only created) lands in the undated bucket."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260919-undat1-01-undat1-no-close-line.backlog.md"
            )
            item.write_text(
                "- Id: undat1\n"
                "- Status: done\n"
                "- Blocks-Release: next\n"
                "- Set: undat1\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Undated bug with only created line\n\n"
                "## Workflow history\n"
                "- 2026-09-19 created (aw backlog): Filed and fixed in same change\n",
                encoding="utf-8",
            )
            code, data = _run_audit(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data["total_findings"], 1)
            finding = data["findings"][0]
            self.assertEqual(finding["partition"], "undated")
            self.assertIsNone(finding["close_date"])
            self.assertEqual(data["partition_counts"]["undated"], 1)

    def test_custom_message_flag_spelling_close_dated(self) -> None:
        """A close line written with `set (aw backlog)` carrying a custom message is dated properly."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260923-flag01-01-flag01-custom-message.backlog.md"
            )
            item.write_text(
                "- Id: flag01\n"
                "- Status: done\n"
                "- Blocks-Release: next\n"
                "- Set: flag01\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Custom message flag close\n\n"
                "## Workflow history\n"
                "- 2026-09-23 set (aw backlog): FIXED by runnerlayer Order 02 (custom message)\n",
                encoding="utf-8",
            )
            code, data = _run_audit(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data["total_findings"], 1)
            finding = data["findings"][0]
            self.assertEqual(finding["close_date"], "2026-09-23")
            self.assertEqual(finding["close_actor"], "aw backlog")
            self.assertEqual(finding["partition"], "post-predicate")

    def test_graduated_then_done_dated_by_done_line(self) -> None:
        """An item with a graduated record followed by a done record is dated by the done record, not graduated."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260910-grad01-01-grad01-grad-then-done.backlog.md"
            )
            item.write_text(
                "- Id: grad01\n"
                "- Status: done\n"
                "- Blocks-Release: next\n"
                "- Set: grad01\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Graduated then done item\n\n"
                "## Workflow history\n"
                "- 2026-09-20 done (aw set): status set to done\n"
                "- 2026-09-10 graduated (aw backlog): design handed off\n"
                "- 2026-09-01 created (aw backlog): created\n",
                encoding="utf-8",
            )
            code, data = _run_audit(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data["total_findings"], 1)
            finding = data["findings"][0]
            self.assertEqual(finding["close_date"], "2026-09-20")

    def test_persisted_close_evidence_not_reported(self) -> None:
        """An item carrying a resolvable - Close-Evidence: bullet is SATISFIED and NOT reported."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            evidence_file = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / "20260901-rel001-01-rel001-evidence.ipd.md"
            )
            evidence_file.write_text(
                "# IPD: Shipped work\n\n- Id: rel001\n- Status: executed\n- Set: rel001\n",
                encoding="utf-8",
            )
            item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260920-evid01-01-evid01-satisfied.backlog.md"
            )
            item.write_text(
                "- Id: evid01\n"
                "- Status: done\n"
                "- Blocks-Release: next\n"
                "- Close-Evidence: .aw/records/plans/executed/20260901-rel001-01-rel001-evidence.ipd.md\n"
                "- Set: evid01\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Item satisfied by close evidence\n\n"
                "## Workflow history\n"
                "- 2026-09-20 done (aw set): status set to done\n",
                encoding="utf-8",
            )
            code, data = _run_audit(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data["total_findings"], 0)

    def test_read_only_property_preserves_bytes_and_mtime(self) -> None:
        """The auditor opens no file for writing and mutates neither content nor mtime."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            item = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "done"
                / "20260920-item01-01-item01-ro.backlog.md"
            )
            item.write_text(
                "- Id: item01\n"
                "- Status: done\n"
                "- Blocks-Release: next\n"
                "- Set: item01\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Gated bug\n\n"
                "## Workflow history\n"
                "- 2026-09-20 done (aw set): status set to done\n",
                encoding="utf-8",
            )

            # Snapshot all files: path -> (bytes, mtime_ns)
            def snapshot(root: Path) -> Dict[str, Tuple[bytes, int]]:
                sn: Dict[str, Tuple[bytes, int]] = {}
                for p in sorted(root.rglob("*")):
                    if p.is_file():
                        rel = str(p.relative_to(root))
                        stat = p.stat()
                        sn[rel] = (p.read_bytes(), stat.st_mtime_ns)
                return sn

            before = snapshot(repo)
            code, data = _run_audit(repo)
            self.assertEqual(code, 0)
            self.assertEqual(data["total_findings"], 1)
            after = snapshot(repo)

            # Assert complete identity
            self.assertEqual(
                set(before.keys()), set(after.keys()), "No files created or deleted"
            )
            for k in before:
                self.assertEqual(
                    before[k][0], after[k][0], f"File content modified: {k}"
                )
                self.assertEqual(before[k][1], after[k][1], f"File mtime modified: {k}")


if __name__ == "__main__":
    unittest.main()

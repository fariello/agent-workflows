"""Tests for degraded attention items synthesized for malformed artifacts (Plan a21sr5).

Verifies:
- attention.scan synthesizes a degraded Item for fatal status parse failures
  (attention.missing-status, attention.unknown-status) while preserving Drift.
- The degraded Item carries filename id6, native_status="-", attention_class=BLOCKED.
- All CLI surfaces name the degraded artifact:
  - Board renders it under blocked
  - -id prints the id6
  - --paths prints the path
  - --filenames prints the filename
  - --json lists it in items and violations, and valid remains false
  - Selection by id6 matches and does not exit 2
  - --check still names the violation and exits 1
- Well-formed sibling artifacts are unaffected.
- Restored regression pin: selector_match_facts matches the token rather than treating as typo.
- Safety properties:
  - No dispatch reachability: action_for_status is undetermined and runner selection excludes it.
  - No false release blocker: release_blockers excludes degraded items.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention as att
from agent_workflows import attention_contract as A
from agent_workflows import run_selection_policy as rsp


class AttentionDegradedItemTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Initialize git repo in throwaway dir
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

        # Write .aw/config/project.json
        cfg_dir = self.root / ".aw" / "config"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        (cfg_dir / "project.json").write_text(
            json.dumps(
                {"schema_version": 2, "preset": "private-target", "role": "target"}
            ),
            encoding="utf-8",
        )

        # Create plans directory
        self.plans_dir = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans_dir.mkdir(parents=True, exist_ok=True)

        # 1. Malformed plan: no - Status: bullet (id6: ab12cd)
        self.malformed_plan = self.plans_dir / "20260929-set-01-ab12cd-malformed.ipd.md"
        self.malformed_plan.write_text(
            """# IPD: Malformed plan

- Date: 2026-09-29
- Kind: child
- Scope: none
- Scope-Paths: none
- Item-Dependencies: none
- Set: set
- Order: 01
- Id: ab12cd

## Goal
Test malformed.
""",
            encoding="utf-8",
        )

        # 2. Well-formed plan: has - Status: to-review (id6: ef34gh)
        self.wellformed_plan = (
            self.plans_dir / "20260929-set-02-ef34gh-wellformed.ipd.md"
        )
        self.wellformed_plan.write_text(
            """# IPD: Wellformed plan

- Date: 2026-09-29
- Kind: child
- Scope: none
- Scope-Paths: none
- Item-Dependencies: none
- Status: to-review
- Set: set
- Order: 02
- Id: ef34gh

## Goal
Test wellformed.
""",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        cmd = [
            sys.executable,
            "-m",
            "agent_workflows.cli",
            "attention",
            *args,
            "--dir",
            str(self.root),
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_scan_synthesizes_degraded_item_and_preserves_drift(self):
        items, drift = att.scan(self.root)

        # 1. Both items returned: well-formed and degraded
        items_by_id = {it.id: it for it in items}
        self.assertIn("ab12cd", items_by_id)
        self.assertIn("ef34gh", items_by_id)

        # 2. Degraded item fields
        deg = items_by_id["ab12cd"]
        self.assertEqual(deg.id, "ab12cd")
        self.assertEqual(deg.native_status, "-")
        self.assertEqual(deg.attention_class, A.BLOCKED)
        self.assertIsNone(deg.gate)
        self.assertEqual(deg.tree, "plans")

        # 3. Well-formed item fields unaffected
        wf = items_by_id["ef34gh"]
        self.assertEqual(wf.id, "ef34gh")
        self.assertEqual(wf.native_status, "to-review")
        self.assertEqual(wf.attention_class, A.READY)

        # 4. Drift is preserved byte-for-byte
        missing_status_drifts = [
            d for d in drift if d.rule == "attention.missing-status"
        ]
        self.assertTrue(
            any(
                "20260929-set-01-ab12cd-malformed.ipd.md" in d.location
                for d in missing_status_drifts
            )
        )

    def test_board_renders_degraded_item_under_blocked(self):
        res = self._run_cli("ab12cd", "--all")
        self.assertEqual(res.returncode, 1)  # fails closed due to drift
        self.assertIn("VIEW INVALID", res.stdout)
        self.assertIn("## blocked", res.stdout)
        self.assertIn("ab12cd", res.stdout)
        self.assertIn("-", res.stdout)

    def test_id_flag_prints_degraded_id6(self):
        res = self._run_cli("ab12cd", "-id", "--all")
        self.assertEqual(res.returncode, 1)  # fails closed due to drift
        self.assertIn("ab12cd", res.stdout.strip().splitlines())

    def test_paths_flag_prints_degraded_path(self):
        res = self._run_cli("ab12cd", "--paths", "--all")
        self.assertEqual(res.returncode, 1)
        self.assertTrue(
            any(
                "20260929-set-01-ab12cd-malformed.ipd.md" in line
                for line in res.stdout.strip().splitlines()
            )
        )

    def test_filenames_flag_prints_degraded_filename(self):
        res = self._run_cli("ab12cd", "--filenames", "--all")
        self.assertEqual(res.returncode, 1)
        self.assertTrue(
            any(
                "20260929-set-01-ab12cd-malformed.ipd.md" in line
                for line in res.stdout.strip().splitlines()
            )
        )

    def test_json_lists_in_items_and_violations_and_reports_invalid(self):
        res = self._run_cli("ab12cd", "--json", "--all")
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stdout)
        self.assertFalse(data["valid"])

        item_ids = [it["id"] for it in data["items"]]
        self.assertIn("ab12cd", item_ids)

        deg_json = next(it for it in data["items"] if it["id"] == "ab12cd")
        self.assertEqual(deg_json["native_status"], "-")
        self.assertEqual(deg_json["attention_class"], A.BLOCKED)
        self.assertIsNone(deg_json["gate"])

        violation_locs = [v["location"] for v in data["violations"]]
        self.assertTrue(
            any(
                "20260929-set-01-ab12cd-malformed.ipd.md" in loc
                for loc in violation_locs
            )
        )

    def test_select_by_id6_matches_and_does_not_refuse_exit_2(self):
        # A selector that matches an artifact should not exit 2 (unresolved selector)
        res = self._run_cli("ab12cd")
        self.assertNotEqual(res.returncode, 2)
        # Sibling well-formed artifact can also be selected independently
        res_wf = self._run_cli("ef34gh")
        self.assertNotEqual(res_wf.returncode, 2)
        self.assertIn("ef34gh", res_wf.stdout)

    def test_check_names_violation_and_exits_1(self):
        res = self._run_cli("ab12cd", "--check")
        self.assertEqual(res.returncode, 1)
        self.assertIn("attention.missing-status", res.stdout)
        self.assertIn("20260929-set-01-ab12cd-malformed.ipd.md", res.stdout)

    def test_restored_selector_match_facts_pin(self):
        """Pin fqnj8k behavior (lost in suite trim 19313eed): token naming malformed artifact is MATCHED."""
        items, drift = att.scan(self.root)
        facts = att.selector_match_facts(items, ["ab12cd"], self.root, drift=drift)
        self.assertIn("ab12cd", facts.matched)
        self.assertNotIn("ab12cd", facts.unmatched)

    def test_unknown_status_also_synthesizes_degraded_item(self):
        """Confirm fatal status rule attention.unknown-status also produces degraded Item."""
        unknown_plan = self.plans_dir / "20260929-set-03-cd56ef-unknown.ipd.md"
        unknown_plan.write_text(
            """# IPD: Unknown status plan

- Date: 2026-09-29
- Kind: child
- Scope: none
- Scope-Paths: none
- Item-Dependencies: none
- Status: completely-bogus-status
- Set: set
- Order: 03
- Id: cd56ef

## Goal
Test unknown status.
""",
            encoding="utf-8",
        )
        items, drift = att.scan(self.root)
        by_id = {it.id: it for it in items}
        self.assertIn("cd56ef", by_id)
        self.assertEqual(by_id["cd56ef"].native_status, "-")
        self.assertEqual(by_id["cd56ef"].attention_class, A.BLOCKED)
        self.assertTrue(any(d.rule == "attention.unknown-status" for d in drift))

    def test_safety_property_no_dispatch_reachability(self):
        """Assert action_for_status is undetermined so runner selection excludes degraded item."""
        self.assertEqual(rsp.action_for_status("plan", "-"), rsp.ACTION_UNDETERMINED)
        self.assertEqual(rsp.action_for_status("plan", ""), rsp.ACTION_UNDETERMINED)
        self.assertEqual(rsp.action_for_status("plan", None), rsp.ACTION_UNDETERMINED)
        self.assertEqual(
            rsp.action_for_status("plan", "unknown"), rsp.ACTION_UNDETERMINED
        )
        self.assertEqual(rsp.runner_action("plan", "-"), rsp.ACTION_UNDETERMINED)
        self.assertEqual(
            rsp.runner_action("plan", "-", full_auto=True), rsp.ACTION_UNDETERMINED
        )

        # partition.py runnable filter check
        items, _ = att.scan(self.root, type_filters=("plans",))
        deg = next(it for it in items if it.id == "ab12cd")
        # Action is undetermined, which partition excludes from candidates
        act = rsp.action_for_status("plan", deg.native_status)
        self.assertIn(act, (rsp.ACTION_SKIP, rsp.ACTION_UNDETERMINED))

    def test_safety_property_no_false_release_blocker(self):
        """Assert degraded item carries blocks_release=None and does not appear in release_blockers."""
        items, _ = att.scan(self.root)
        deg = next(it for it in items if it.id == "ab12cd")
        self.assertIsNone(deg.blocks_release)
        blockers = att.release_blockers(items, self.root)
        self.assertNotIn("ab12cd", [it.id for it in blockers])


if __name__ == "__main__":
    unittest.main()

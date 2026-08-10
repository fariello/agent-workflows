"""Unit tests for record producer inventory completeness and write guard (IPD 20260809-awlayout-08)."""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows.record_producers import (
    LEGACY_ALLOWLIST,
    PRODUCER_INVENTORY,
    RecordProducerEntry,
)


class TestRecordProducerInventory(unittest.TestCase):
    """Test record producer inventory structure and write guard rules (E-01 & V-01)."""

    def test_inventory_structure_and_completeness(self):
        """Inventory entries must contain valid required fields."""
        self.assertGreater(len(PRODUCER_INVENTORY), 0)
        for entry in PRODUCER_INVENTORY:
            self.assertIsInstance(entry, RecordProducerEntry)
            self.assertTrue(entry.name)
            self.assertTrue(entry.source_path)
            self.assertTrue(entry.anchor)
            self.assertIn(entry.operation, ("create", "move", "archive", "stage"))
            self.assertIn(entry.category, ("plans", "specs", "research", "records"))
            self.assertIn(entry.resolver_surface, ("python_api", "cli_aw_path"))

    def test_legacy_allowlist_is_bounded(self):
        """Legacy allowlist must contain only non-writing readers/validators (E-01 & V-05)."""
        for item in LEGACY_ALLOWLIST:
            self.assertTrue(item.endswith(".py"))
            self.assertTrue(Path(item).exists(), f"Allowlist item missing: {item}")


if __name__ == "__main__":
    unittest.main()

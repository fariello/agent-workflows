"""Unit tests for record producer inventory completeness and write guard (IPD 20260809-awlayout-08)."""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows.record_producers import (
    LEGACY_ALLOWLIST,
    LEGACY_WRITER_CANDIDATES,
    PRODUCER_INVENTORY,
    RecordProducerEntry,
    discover_legacy_write_sinks,
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
        self.assertFalse(LEGACY_ALLOWLIST & LEGACY_WRITER_CANDIDATES)

    def test_inventory_anchors_exist_and_legacy_sinks_are_declared(self):
        """Code discovery cannot reveal an undeclared legacy record writer."""

        root = Path(__file__).resolve().parent.parent
        inventory_paths = {entry.source_path for entry in PRODUCER_INVENTORY}
        for entry in PRODUCER_INVENTORY:
            source = root / entry.source_path
            self.assertTrue(source.is_file(), entry)
            self.assertIn(entry.anchor, source.read_text(encoding="utf-8"), entry)
        sinks = discover_legacy_write_sinks(root)
        self.assertTrue(sinks.issubset(inventory_paths), sinks - inventory_paths)
        self.assertFalse(sinks & LEGACY_ALLOWLIST)


if __name__ == "__main__":
    unittest.main()

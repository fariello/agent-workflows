"""Tests for xprio Order 03 (6vgd0k): recognized-but-optional Priority on research docs.

Covers E-01 (optional `priority:` frontmatter key carried into INDEX.json; NOT added to the required
FRONTMATTER_FIELDS so absence is clean), E-02 (`validate_frontmatter` enum-checks the value against
the shared `backlog.PRIORITIES`, silent when absent), E-03 (`aw research new --priority` emits it and
`aw research set-priority` writes/clears it), and E-04 (`attention._research_record` populates
`Item.priority`).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    attention,
    backlog,
    research_cmd as rc,
    research_contract as R,
    research_index as ridx,
)


def _valid_fm(**over):
    d = {
        "id": "k7m2xq",
        "created": "20260726",
        "set": "demo",
        "order": "02",
        "topic": ["x"],
        "model": "reconciliation",
        "kind": "findings",
        "status": "todo",
        "outcome": "none-yet",
        "summary": "s",
        "consumed-by": [],
    }
    d.update(over)
    return d


class ResearchPriorityContractTests(unittest.TestCase):
    def test_priority_not_in_required_fields(self) -> None:
        # E-01: priority must NOT be a required-presence field (else every existing doc mass-fails).
        self.assertNotIn("priority", R.FRONTMATTER_FIELDS)

    def test_absent_priority_conforms(self) -> None:
        self.assertEqual(R.validate_frontmatter(_valid_fm()), [])

    def test_valid_priority_conforms(self) -> None:
        for val in sorted(backlog.PRIORITIES):
            errs = R.validate_frontmatter(_valid_fm(priority=val))
            self.assertEqual(
                [e for e in errs if e.field == "priority"], [], f"{val}: {errs}"
            )

    def test_out_of_vocab_priority_flagged(self) -> None:
        errs = R.validate_frontmatter(_valid_fm(priority="bogus"))
        bad = [e for e in errs if e.field == "priority"]
        self.assertEqual(len(bad), 1, errs)
        self.assertIn("one of", bad[0].message)


class ResearchPriorityIndexTests(unittest.TestCase):
    def test_index_carries_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".aw" / "records" / "research"
            root.mkdir(parents=True)
            files, err = rc.plan_new(
                research_root=root,
                kind="findings",
                slug="demo",
                summary="s",
                priority="high",
                date_str="20260828",
            )
            self.assertIsNone(err)
            for pf in files:
                pf.path.write_text(pf.content, encoding="utf-8")
            entries, drift = ridx._scan_docs(root)
            self.assertEqual([d for d in drift if d.rule == "frontmatter-invalid"], [])
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].priority, "high")
            # INDEX.json carries the field (via _asdict()).
            self.assertIn('"priority": "high"', ridx.build_index_json(entries))

    def test_index_priority_empty_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".aw" / "records" / "research"
            root.mkdir(parents=True)
            files, err = rc.plan_new(
                research_root=root,
                kind="findings",
                slug="demo",
                summary="s",
                date_str="20260828",
            )
            self.assertIsNone(err)
            for pf in files:
                pf.path.write_text(pf.content, encoding="utf-8")
            entries, _ = ridx._scan_docs(root)
            self.assertEqual(entries[0].priority, "")


class ResearchPriorityNewAndSetTests(unittest.TestCase):
    def test_new_emits_priority_line_only_when_given(self) -> None:
        with_p = rc.build_frontmatter(
            id6="k7m2xq",
            created="20260828",
            set_id="demo",
            order="00",
            topic=[],
            model=None,
            kind="findings",
            status="todo",
            outcome="none-yet",
            summary="s",
            priority="high",
        )
        self.assertIn("priority: high", with_p)
        without_p = rc.build_frontmatter(
            id6="k7m2xq",
            created="20260828",
            set_id="demo",
            order="00",
            topic=[],
            model=None,
            kind="findings",
            status="todo",
            outcome="none-yet",
            summary="s",
        )
        self.assertNotIn("priority:", without_p)

    def test_new_rejects_out_of_vocab_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files, err = rc.plan_new(
                research_root=root,
                kind="findings",
                slug="demo",
                summary="s",
                priority="bogus",
                date_str="20260828",
            )
            self.assertIsNone(files)
            self.assertIn("one of", err or "")

    def test_set_priority_writes_inserts_and_clears(self) -> None:
        # _set_priority_line: insert when absent, replace when present, remove on clear.
        block = (
            "---\nid: k7m2xq\ncreated: 20260828\nset: demo\norder: 00\n"
            "topic: []\nmodel: \nkind: findings\nstatus: todo\noutcome: none-yet\n"
            "summary: s\nconsumed-by: []\n---\n\nbody\n"
        )
        inserted = rc._set_priority_line(block, "high")
        self.assertIn("priority: high", inserted)
        # body untouched
        self.assertTrue(inserted.rstrip().endswith("body"))
        replaced = rc._set_priority_line(inserted, "medium")
        self.assertIn("priority: medium", replaced)
        self.assertNotIn("priority: high", replaced)
        cleared = rc._set_priority_line(replaced, "-")
        self.assertNotIn("priority:", cleared)

    def test_plan_set_priority_rejects_out_of_vocab(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".aw" / "records" / "research"
            root.mkdir(parents=True)
            files, _ = rc.plan_new(
                research_root=root,
                kind="findings",
                slug="demo",
                summary="s",
                date_str="20260828",
            )
            for pf in files:
                pf.path.write_text(pf.content, encoding="utf-8")
            id6 = ridx._scan_docs(root)[0][0].id6
            _t, _n, err = rc.plan_set_priority(root, id6, "bogus")
            self.assertIn("one of", err or "")


class ResearchPriorityAttentionTests(unittest.TestCase):
    def _doc(self, priority_line: str = "") -> str:
        return (
            "---\nid: k7m2xq\ncreated: 20260828\nset: demo\norder: 00\n"
            "topic: []\nmodel: \nkind: findings\nstatus: todo\noutcome: none-yet\n"
            "summary: s\nconsumed-by: []\n" + priority_line + "---\n\nbody\n"
        )

    def test_research_record_populates_priority(self) -> None:
        item_hi, _ = attention._research_record(
            "x", Path("d.md"), self._doc("priority: high\n")
        )
        self.assertIsNotNone(item_hi)
        self.assertEqual(item_hi.priority, "high")
        item_none, _ = attention._research_record("x", Path("d.md"), self._doc())
        self.assertIsNotNone(item_none)
        self.assertIsNone(item_none.priority)


if __name__ == "__main__":
    unittest.main()

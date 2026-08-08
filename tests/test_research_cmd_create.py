"""Tests for the aw research create verbs (Set research-org, Order 02).

Stdlib unittest, throwaway dirs (mirrors tests/test_installer.py style). Verifies name assembly,
NN increment, singleton derivation, full spec-5.8 frontmatter, writing-command safety
(dry-run/apply/atomic/no-clobber), the multi-model comparison scaffold order, and invalid-input
rejection via the contract's suggestion API.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import research_cmd as C
from agent_workflows import research_contract as R


class NewPlanTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.research = self.root / R.RESEARCH_ROOT
        self.research.mkdir(parents=True)

    def test_new_well_formed_and_full_frontmatter(self):
        files, err = C.plan_new(
            research_root=self.research,
            kind="research-report",
            slug="Delivery Notes",
            summary="A summary.",
            set_id="aw-delivery",
            model="gpt-56",  # normalizes to gpt56
            topic=["delivery", "hosts"],
            date_str="20260726",
        )
        self.assertIsNone(err)
        self.assertEqual(len(files), 1)
        f = files[0]
        # Name parses back and is contract-conformant.
        parsed, perr = R.parse_name(f.path.name)
        self.assertIsNone(perr)
        self.assertEqual(parsed.set_id, "aw-delivery")
        self.assertEqual(parsed.slug, "delivery-notes")
        self.assertEqual(parsed.model, "gpt56")
        self.assertEqual(parsed.kind, "research-report")
        # Frontmatter is full and passes the validator.
        data = _parse_frontmatter(f.content)
        self.assertEqual(R.validate_frontmatter(data), [])
        self.assertEqual(data["status"], "intake")
        self.assertEqual(data["outcome"], "none-yet")

    def test_nn_increments_on_second_same_set_call(self):
        f1, _ = C.plan_new(
            research_root=self.research,
            kind="notes",
            slug="one",
            summary="s",
            set_id="myset",
            date_str="20260726",
        )
        # Write it so the second call sees it on disk.
        f1[0].path.write_text(f1[0].content, encoding="utf-8")
        f2, _ = C.plan_new(
            research_root=self.research,
            kind="notes",
            slug="two",
            summary="s",
            set_id="myset",
            date_str="20260726",
        )
        p1, _ = R.parse_name(f1[0].path.name)
        p2, _ = R.parse_name(f2[0].path.name)
        self.assertEqual(p1.order, "00")
        self.assertEqual(p2.order, "01")
        # Same set shares the date.
        self.assertEqual(p1.date, p2.date)

    def test_singleton_derives_set_from_slug(self):
        files, err = C.plan_new(
            research_root=self.research,
            kind="advisory",
            slug="my-finding",
            summary="s",
            date_str="20260726",
        )
        self.assertIsNone(err)
        parsed, _ = R.parse_name(files[0].path.name)
        self.assertEqual(parsed.set_id, "my-finding")
        self.assertEqual(parsed.order, "00")

    def test_unknown_kind_rejected_with_suggestion(self):
        files, err = C.plan_new(
            research_root=self.research,
            kind="reserch-reprt",
            slug="x",
            summary="s",
        )
        self.assertIsNone(files)
        self.assertIsNotNone(err)
        self.assertIn("unknown kind", err)


class WriteSafetyTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.research = self.root / R.RESEARCH_ROOT
        self.research.mkdir(parents=True)

    def _files(self):
        files, err = C.plan_new(
            research_root=self.research,
            kind="notes",
            slug="x",
            summary="s",
            set_id="s",
            date_str="20260726",
        )
        self.assertIsNone(err)
        return files

    def test_dry_run_writes_nothing(self):
        files = self._files()
        rc = C._emit_and_write(files, apply=False, overwrite=False)
        self.assertEqual(rc, 0)
        self.assertFalse(files[0].path.exists())

    def test_apply_writes_atomically(self):
        files = self._files()
        rc = C._emit_and_write(files, apply=True, overwrite=False)
        self.assertEqual(rc, 0)
        self.assertTrue(files[0].path.exists())
        # No temp file left behind.
        leftovers = list(self.research.glob(".research-tmp-*"))
        self.assertEqual(leftovers, [])

    def test_no_clobber_without_overwrite(self):
        files = self._files()
        files[0].path.write_text("existing", encoding="utf-8")
        rc = C._emit_and_write(files, apply=True, overwrite=False)
        self.assertEqual(rc, 1)
        self.assertEqual(files[0].path.read_text(encoding="utf-8"), "existing")


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.research = self.root / R.RESEARCH_ROOT
        self.research.mkdir(parents=True)

    def test_scaffold_order_and_tags(self):
        files, err = C.plan_new_comparison(
            research_root=self.research,
            set_id="host-probe",
            slug="probe",
            models=["gpt56", "sonnet5", "gemini31pro"],
            date_str="20260726",
        )
        self.assertIsNone(err)
        # 00 prompt + 3 models (01..03) + reconciliation (04) = 5
        self.assertEqual(len(files), 5)
        parsed = [R.parse_name(f.path.name)[0] for f in files]
        orders = [p.order for p in parsed]
        self.assertEqual(orders, ["00", "01", "02", "03", "04"])
        self.assertEqual(parsed[0].kind, "research-prompt")
        self.assertIsNone(parsed[0].model)
        self.assertEqual(parsed[1].model, "gpt56")
        self.assertEqual(parsed[4].kind, "reconciliation-report")
        self.assertEqual(parsed[4].model, "reconciliation")

    def test_unknown_model_rejected(self):
        files, err = C.plan_new_comparison(
            research_root=self.research,
            set_id="s",
            slug="x",
            models=["llama99"],
        )
        self.assertIsNone(files)
        self.assertIn("unknown model", err)


class IdCollisionTests(unittest.TestCase):
    def test_generate_avoids_existing(self):
        # Force a collision on the first draw, then succeed.
        seq = iter(["a", "a", "a", "a", "a", "a", "b", "c", "d", "e", "f", "g"])
        existing = {"aaaaaa"}
        got = C.generate_id6(existing, _rng=lambda alphabet: next(seq))
        self.assertNotIn(got, existing)
        self.assertTrue(R.is_valid_id6(got))


def _parse_frontmatter(text: str) -> dict:
    """Minimal frontmatter parser for the tool-authored block (list + scalar values)."""

    data: dict = {}
    lines = text.splitlines()
    assert lines[0] == "---"
    for line in lines[1:]:
        if line == "---":
            break
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            data[key] = [x.strip() for x in inner.split(",")] if inner else []
        else:
            data[key] = val
    return data


if __name__ == "__main__":
    unittest.main()

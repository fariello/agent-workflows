"""Tests for the canonical research-artifact contract (Set research-org, Order 01).

Table-driven, stdlib unittest, zero dependencies. Verifies the contract against the specification
.agents/docs/specs/20260730-2152-01-agents-artifact-organization.spec.md (Sections 4.1, 4.2, 4.4,
4.5, 4.9, 5.4, 5.8).
"""

from __future__ import annotations

import unittest

from agent_workflows import research_contract as R


class Id6Tests(unittest.TestCase):
    def test_valid_id6(self):
        self.assertTrue(R.is_valid_id6("k7m2xq"))
        self.assertTrue(R.is_valid_id6("000000"))
        self.assertTrue(R.is_valid_id6("zzzzzz"))

    def test_reject_wrong_length(self):
        self.assertFalse(R.is_valid_id6("k7m2x"))  # 5 chars
        self.assertFalse(R.is_valid_id6("k7m2xqq"))  # 7 chars

    def test_reject_non_base36(self):
        self.assertFalse(R.is_valid_id6("K7M2XQ"))  # uppercase
        self.assertFalse(R.is_valid_id6("k7m2x-"))  # non-alnum
        self.assertFalse(R.is_valid_id6("k7m2x_"))

    def test_word_boundary_match_in_filename_and_prose(self):
        # In a hyphen-delimited filename fragment.
        found = R.iter_id6_in_text(
            "20260726-aw-delivery-02-k7m2xq-notes.gpt56.research-report.md"
        )
        self.assertIn("k7m2xq", found)
        # In prose.
        self.assertEqual(R.iter_id6_in_text("see k7m2xq for details"), ["k7m2xq"])


class VocabTests(unittest.TestCase):
    def test_known_kind_accepted(self):
        res = R.normalize_kind("research-report")
        self.assertTrue(res.ok)
        self.assertEqual(res.value, "research-report")

    def test_kind_normalized(self):
        self.assertEqual(R.normalize_kind("finding").value, "findings")

    def test_unknown_kind_rejected_with_suggestion(self):
        res = R.normalize_kind("reserch-reprt")
        self.assertFalse(res.ok)
        self.assertIsNotNone(res.suggestion)
        self.assertIn("unknown kind", res.message)

    def test_known_model_accepted(self):
        self.assertTrue(R.normalize_model("sonnet5").ok)

    def test_model_normalized(self):
        self.assertEqual(R.normalize_model("gpt-56").value, "gpt56")

    def test_chatgpt_maps_to_model(self):
        self.assertEqual(R.normalize_model("chatgpt").value, "gpt56")

    def test_unknown_model_rejected(self):
        res = R.normalize_model("llama99")
        self.assertFalse(res.ok)
        self.assertIn("unknown model", res.message)


class KebabTests(unittest.TestCase):
    def test_kebab(self):
        self.assertEqual(
            R.kebab("AW Delivery & Clean Delta"), "aw-delivery-clean-delta"
        )
        self.assertEqual(R.kebab("  spaced  out  "), "spaced-out")


class NameParseFormatTests(unittest.TestCase):
    def test_round_trip_basic_with_model(self):
        name = R.ResearchName(
            date="20260726",
            set_id="aw-delivery",
            order="02",
            id6="k7m2xq",
            slug="delivery-notes",
            model="gpt56",
            kind="research-report",
        )
        s = R.format_name(name)
        self.assertEqual(
            s, "20260726-aw-delivery-02-k7m2xq-delivery-notes.gpt56.research-report.md"
        )
        parsed, err = R.parse_name(s)
        self.assertIsNone(err)
        self.assertEqual(parsed, name)

    def test_round_trip_singleton_no_model(self):
        name = R.ResearchName(
            date="20260716",
            set_id="opencode-advisory",
            order="00",
            id6="ab12cd",
            slug="unauthenticated-server",
            model=None,
            kind="advisory",
        )
        s = R.format_name(name)
        self.assertEqual(
            s, "20260716-opencode-advisory-00-ab12cd-unauthenticated-server.advisory.md"
        )
        parsed, err = R.parse_name(s)
        self.assertIsNone(err)
        self.assertEqual(parsed, name)

    def test_round_trip_reconciliation(self):
        name = R.ResearchName(
            date="20260726",
            set_id="host-probe",
            order="05",
            id6="9z8y7x",
            slug="synthesis",
            model="reconciliation",
            kind="reconciliation-report",
        )
        parsed, err = R.parse_name(R.format_name(name))
        self.assertIsNone(err)
        self.assertEqual(parsed, name)

    def test_parse_normalizes_drift_tokens(self):
        parsed, err = R.parse_name(
            "20260722-token-eff-01-aa11bb-managed-sections.gpt-56.finding.md"
        )
        self.assertIsNone(err)
        self.assertEqual(parsed.model, "gpt56")
        self.assertEqual(parsed.kind, "findings")

    def test_parse_rejects_missing_kind(self):
        parsed, err = R.parse_name("20260726-set-01-k7m2xq-slug.md")
        self.assertIsNone(parsed)
        self.assertIsNotNone(err)

    def test_parse_rejects_bad_core(self):
        parsed, err = R.parse_name("not-a-valid-core.research-report.md")
        self.assertIsNone(parsed)
        self.assertIsNotNone(err)

    def test_parse_rejects_non_md(self):
        parsed, err = R.parse_name("20260726-set-01-k7m2xq-slug.research-report.txt")
        self.assertIsNone(parsed)
        self.assertIsNotNone(err)


class ShardTests(unittest.TestCase):
    def test_shard_dirname(self):
        self.assertEqual(R.shard_dirname("202607"), "202607")

    def test_valid_shard(self):
        self.assertTrue(R.is_valid_shard_dirname("202607"))
        self.assertTrue(
            R.is_valid_shard_dirname("202607-W30")
        )  # legacy weekly tolerance
        self.assertFalse(R.is_valid_shard_dirname("2026-07"))
        self.assertFalse(R.is_valid_shard_dirname("2026-W30"))


class FrontmatterTests(unittest.TestCase):
    def _valid(self):
        return {
            "id": "k7m2xq",
            "created": "20260726",
            "set": "aw-delivery",
            "order": "02",
            "topic": ["delivery", "hosts"],
            "model": "reconciliation",
            "kind": "reconciliation-report",
            "status": "reference",
            "outcome": "adopted",
            "summary": "One-line summary.",
            "consumed-by": ["D107"],
        }

    def test_valid_passes(self):
        self.assertEqual(R.validate_frontmatter(self._valid()), [])

    def test_missing_id_fails(self):
        data = self._valid()
        del data["id"]
        errs = R.validate_frontmatter(data)
        self.assertTrue(any(e.field == "id" for e in errs))

    def test_bad_status_fails(self):
        data = self._valid()
        data["status"] = "cold"
        errs = R.validate_frontmatter(data)
        self.assertTrue(any(e.field == "status" for e in errs))

    def test_bad_id_value_fails(self):
        data = self._valid()
        data["id"] = "TOOLONGX"
        errs = R.validate_frontmatter(data)
        self.assertTrue(any(e.field == "id" for e in errs))

    def test_bad_outcome_fails(self):
        data = self._valid()
        data["outcome"] = "maybe"
        errs = R.validate_frontmatter(data)
        self.assertTrue(any(e.field == "outcome" for e in errs))

    def test_topic_must_be_list(self):
        data = self._valid()
        data["topic"] = "delivery"
        errs = R.validate_frontmatter(data)
        self.assertTrue(any(e.field == "topic" for e in errs))


class SchemaConstantsTests(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(
            R.STATUSES, frozenset({"intake", "active", "reference", "archive"})
        )

    def test_hot_vs_sharded(self):
        self.assertEqual(R.HOT_STATUSES, frozenset({"intake", "active"}))
        self.assertEqual(R.SHARDED_STATUSES, frozenset({"reference", "archive"}))

    def test_frontmatter_field_order(self):
        self.assertEqual(R.FRONTMATTER_FIELDS[0], "id")
        self.assertEqual(R.FRONTMATTER_FIELDS[-1], "consumed-by")


if __name__ == "__main__":
    unittest.main()

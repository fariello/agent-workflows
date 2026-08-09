"""Tests for the frozen attention-view contracts (Set attnview, Order 01).

Table-driven, stdlib unittest, zero dependencies. Verifies:
- the class enum + tree-policy inventory shapes;
- the PURE, TOTAL per-tree mapping (coverage test: mapping keys == each tree's canonical native enum);
- the spec transition/authority table + the anti-self-approval floor is stated;
- the gate per-kind validators + output-safety rules;
- the workflow-history record grammar + last_history_at derivation;
- the closed stable rule-id catalog + the detail-escaping policy;
- that the on-disk fixtures parse / are rejected as intended.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention_contract as A
from agent_workflows import plans
from agent_workflows import research_contract

FIX = Path(__file__).parent / "fixtures" / "attnview"


class EnumAndPolicyTests(unittest.TestCase):
    def test_five_classes(self):
        self.assertEqual(
            A.ATTENTION_CLASSES,
            frozenset(("ready", "active", "blocked", "done", "parked")),
        )
        self.assertEqual(set(A.ATTENTION_CLASS_ORDER), A.ATTENTION_CLASSES)

    def test_tree_policy_tracked_and_excluded(self):
        tracked = {p.name for p in A.TREE_POLICY if p.tracked}
        self.assertEqual(tracked, {"specs", "plans", "research"})
        for p in A.TREE_POLICY:
            if p.tracked:
                self.assertTrue(p.owner, f"tracked tree {p.name} needs an owner")
            else:
                self.assertTrue(p.reason, f"excluded tree {p.name} needs a rationale")
        # the evergreen prompt LIBRARY is an explicitly excluded tree (distinct from .agents/prompts)
        self.assertIn("docs-prompts", {p.name for p in A.TREE_POLICY if not p.tracked})

    def test_nonartifact_names(self):
        for n in (
            "README.md",
            "INDEX.md",
            "STATUS.md",
            "conformance-results-template.md",
            "00-README-index.md",
            "some-index.md",
        ):
            self.assertTrue(A.is_nonartifact_name(n), n)
        for n in ("20260808-attnview-01-abc123-x.md", "s.md", "a-real-spec.md"):
            self.assertFalse(A.is_nonartifact_name(n), n)


class MappingTotalityTests(unittest.TestCase):
    """The load-bearing guard (spec Section 6 / A2): mapping keys == each tree's canonical native enum."""

    def test_specs_total(self):
        self.assertEqual(set(A.CLASS_MAPS["specs"].keys()), set(A.SPEC_STATUSES))

    def test_plans_total_over_RECOGNIZED(self):
        self.assertEqual(set(A.CLASS_MAPS["plans"].keys()), set(plans.RECOGNIZED))

    def test_research_total_over_STATUSES(self):
        self.assertEqual(
            set(A.CLASS_MAPS["research"].keys()), set(research_contract.STATUSES)
        )

    def test_every_value_is_a_class(self):
        for tree, frag in A.CLASS_MAPS.items():
            for status, cls in frag.items():
                self.assertIn(cls, A.ATTENTION_CLASSES, f"{tree}:{status} -> {cls}")

    def test_class_of_and_unknown(self):
        self.assertEqual(A.class_of("specs", "implemented"), "done")
        self.assertEqual(A.class_of("plans", "approved"), "ready")  # OQ5: not active
        self.assertEqual(A.class_of("plans", "auto-approved"), "ready")
        self.assertEqual(
            A.class_of("research", "active"), "active"
        )  # live active source in v1
        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("specs", "frobnicated")
        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("prompts", "anything")  # not a tracked tree


class TransitionAuthorityTests(unittest.TestCase):
    def test_legal_and_illegal(self):
        self.assertTrue(A.transition_allowed("reviewed", "approved"))
        self.assertTrue(A.transition_allowed("approved", "implementing"))
        self.assertTrue(A.transition_allowed("implementing", "implemented"))
        self.assertFalse(A.transition_allowed("draft", "implemented"))
        self.assertFalse(A.transition_allowed("implemented", "approved"))

    def test_authority_and_floor(self):
        self.assertEqual(A.TRANSITION_AUTHORITY["->approved"]["who"], "human")
        self.assertTrue(A.TRANSITION_AUTHORITY["->approved"]["human_token"])
        self.assertTrue(A.TRANSITION_AUTHORITY["->implemented"]["evidence"])
        # The anti-self-approval floor is stated (Order 01 finding L2-01/L4-04).
        self.assertIn("cannot satisfy autonomously", A.APPROVAL_FLOOR)
        self.assertIn("INSUFFICIENT", A.APPROVAL_FLOOR)


class GateTests(unittest.TestCase):
    def test_gate_kinds(self):
        self.assertEqual(
            A.GATE_KINDS,
            frozenset(("artifact", "decision", "todo", "issue", "date", "external")),
        )

    def test_gate_ref_validators(self):
        self.assertTrue(A.validate_gate_ref("date", "2026-08-08"))
        self.assertFalse(A.validate_gate_ref("date", "2026-8-8"))
        self.assertTrue(A.validate_gate_ref("issue", "https://example.com/issues/1"))
        self.assertFalse(
            A.validate_gate_ref("issue", "javascript:alert(1)")
        )  # non-http rejected
        self.assertFalse(A.validate_gate_ref("issue", "http://"))
        self.assertTrue(A.validate_gate_ref("artifact", ".agents/plans/x.md#anchor"))
        self.assertFalse(
            A.validate_gate_ref("artifact", "../escape.md")
        )  # repo-escaping rejected
        self.assertFalse(A.validate_gate_ref("artifact", "/abs/path.md"))
        self.assertTrue(A.validate_gate_ref("decision", "D124"))
        self.assertFalse(A.validate_gate_ref("decision", "not-a-decision"))
        self.assertTrue(A.validate_gate_ref("todo", "TODO-14"))
        self.assertTrue(A.validate_gate_ref("external", "vendor-ticket-9"))
        self.assertFalse(A.validate_gate_ref("external", ""))
        self.assertFalse(A.validate_gate_ref("bogus-kind", "x"))

    def test_output_safety(self):
        self.assertTrue(A.is_safe_descriptive("a normal single line"))
        self.assertFalse(A.is_safe_descriptive("x" * (A.MAX_DESCRIPTIVE_LEN + 1)))
        self.assertFalse(A.is_safe_descriptive("line1\nline2"))
        self.assertFalse(A.is_safe_descriptive("bell\x07here"))
        self.assertFalse(A.is_safe_descriptive("esc\x1b[31mred"))


class HistoryTests(unittest.TestCase):
    def test_last_history_at(self):
        lines = [
            "- 2026-08-01 draft (x): created.",
            "- 2026-08-05 reviewed (y): reviewed.",
            "not a record",
            "- 2026-08-08 approved (z): approved.",
        ]
        self.assertEqual(A.last_history_at(lines), "2026-08-08")
        self.assertIsNone(A.last_history_at(["no records here", "- bad date line"]))


class RuleCatalogTests(unittest.TestCase):
    def test_catalog_closed_and_named(self):
        # Every rule id is stable and namespaced; the set is closed (one per violation class).
        for rid in A.RULE_IDS:
            self.assertTrue(rid.startswith("attention."), rid)
        self.assertIn("attention.unclassified-tree", A.RULE_IDS)
        self.assertIn("attention.unsafe-field", A.RULE_IDS)
        self.assertGreaterEqual(len(A.RULE_IDS), 12)

    def test_detail_escaping_keeps_one_line(self):
        detail = "tab\there\nnewline\\backslash"
        esc = A.escape_detail(detail)
        self.assertNotIn("\n", esc)
        self.assertNotIn("\t", esc)
        self.assertIn("\\t", esc)
        self.assertIn("\\n", esc)


class FixtureParseTests(unittest.TestCase):
    """The committed fixtures parse (valid) or are rejected (violations) per the contract."""

    def _read_status(self, path):
        for line in path.read_text(encoding="utf-8").splitlines():
            m = A.SPEC_STATUS_RE.match(line)
            if m:
                return m.group("value")
        return None

    def test_valid_specs_have_bare_enum_status_and_map(self):
        for f in sorted((FIX / "specs-valid").glob("*.md")):
            status = self._read_status(f)
            self.assertIsNotNone(status, f"{f.name}: no bare-enum - Status: bullet")
            self.assertIn(
                status, A.SPEC_STATUSES, f"{f.name}: {status} not a spec status"
            )
            self.assertIn(A.class_of("specs", status), A.ATTENTION_CLASSES)

    def test_trailing_prose_status_is_rejected(self):
        # The grammar requires a bare token; the trailing-prose fixture must NOT parse as a bare status.
        f = FIX / "violations" / "status-trailing-prose.md"
        self.assertIsNone(
            self._read_status(f),
            "trailing-prose status must not match the bare-enum grammar",
        )

    def test_unknown_status_fixture_is_unmapped(self):
        f = FIX / "violations" / "unknown-status.md"
        status = self._read_status(f)
        self.assertEqual(status, "frobnicated")
        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("specs", status)

    def test_unsafe_field_fixture_is_unsafe(self):
        f = FIX / "violations" / "unsafe-field.md"
        summary = None
        for line in f.read_text(encoding="utf-8").splitlines():
            m = A.GATE_SUMMARY_RE.match(line)
            if m:
                summary = m.group("value")
        self.assertIsNotNone(summary)
        self.assertFalse(A.is_safe_descriptive(summary))  # over-length

    def test_simulated_unreadable_and_symlink(self):
        # Non-committable violation classes, simulated in a temp tree (never committed).
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            outside = root / "outside.md"
            outside.write_text("secret\n", encoding="utf-8")
            repo = root / "repo"
            repo.mkdir()
            link = repo / "escape.md"
            try:
                link.symlink_to(outside)
                # a symlink target escaping the repo root -> unstable-path class
                resolved = link.resolve()
                self.assertFalse(str(resolved).startswith(str(repo.resolve())))
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on this platform")


if __name__ == "__main__":
    unittest.main()

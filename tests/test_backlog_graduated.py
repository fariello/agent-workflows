"""Tests for bklgrad Order 01 (v58bvy): the `graduated` backlog status.

Covers the vocabulary (E-01), the drift-proof second copy in the dependency schema (E-08), the
attention class mapping (E-02), the close-legitimacy handling (E-03), and the README/code agreement
(E-05).

The load-bearing negative test is `test_graduated_is_not_a_substitute_for_done`: if `graduated` ever
satisfied a release gate, a release could ship with every blocker merely graduated and no code written.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import attention_contract as A
from agent_workflows import backlog
from agent_workflows import check_engine
from agent_workflows import ipd_schema

REPO_ROOT = Path(__file__).resolve().parents[1]

ITEM = """- Id: {id6}
- Status: {status}
{gate}- Set: tst
- Priority: high
- Kind: feature
- Summary: A test item.

## Workflow history
- 2026-08-29 created (test): A test item.

Body.
"""


def _write_item(root: Path, id6: str, status: str, gate: str = "") -> Path:
    d = root / ".aw" / "records" / "backlog" / status
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260829-tst-01-{id6}-a-test-item.backlog.md"
    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    p.write_text(ITEM.format(id6=id6, status=status, gate=gate_line), encoding="utf-8")
    return p


class VocabularyTests(unittest.TestCase):
    """E-01: `graduated` is a first-class status between `open` and `done`."""

    def test_graduated_in_statuses(self):
        self.assertIn("graduated", backlog.STATUSES)
        self.assertIn("graduated", backlog.STATUS_DIRS)

    def test_ordering_places_graduated_between_open_and_done(self):
        dirs = list(backlog.STATUS_DIRS)
        self.assertLess(dirs.index("open"), dirs.index("graduated"))
        self.assertLess(dirs.index("graduated"), dirs.index("done"))

    def test_existing_statuses_preserved(self):
        for st in ("open", "blocked", "parked", "done"):
            self.assertIn(st, backlog.STATUSES, f"{st} must not be dropped")

    def test_graduated_item_is_discovered_and_typed(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _write_item(root, "aaa111", "graduated")
            found = backlog._iter_items(root)
            self.assertIn(p, found, "a graduated/ item must be discovered")
            self.assertEqual(p.parent.name, "graduated")

    def test_unknown_status_still_rejected(self):
        self.assertNotIn("bogus", backlog.STATUSES)


class DependencySchemaTests(unittest.TestCase):
    """E-08: the second hardcoded copy is DERIVED, so it cannot drift."""

    def test_schema_backlog_set_equals_backlog_statuses(self):
        """The drift guard: same object, not a re-listed literal."""
        self.assertEqual(
            ipd_schema._ITEM_DEP_STATE_STATUSES["backlog"], backlog.STATUSES
        )

    def test_state_backlog_graduated_edge_parses(self):
        """Before E-08 this token was rejected, making the new status undeclarable."""
        edges, _ok, err = ipd_schema.parse_item_dependencies(
            "state:backlog:graduated:abc123"
        )
        self.assertIsNone(err, f"expected no error, got {err!r}")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].target_type, "backlog")
        self.assertEqual(edges[0].status, "graduated")

    def test_bogus_backlog_status_edge_still_rejected(self):
        edges, _ok, err = ipd_schema.parse_item_dependencies(
            "state:backlog:bogus:abc123"
        )
        self.assertIsNotNone(err, "an invalid backlog status must still be rejected")
        self.assertEqual(edges, [])

    def test_every_backlog_status_is_a_legal_state_edge(self):
        """Proves the derived set really governs the parser for all five statuses."""
        for st in sorted(backlog.STATUSES):
            edges, _ok, err = ipd_schema.parse_item_dependencies(
                f"state:backlog:{st}:abc123"
            )
            self.assertIsNone(err, f"{st} should be legal, got {err!r}")
            self.assertEqual(len(edges), 1, f"{st} should yield one edge")


class NoDuplicateVocabularyTests(unittest.TestCase):
    """E-01/E-08 drift guard: every consumer DERIVES the vocabulary; none re-lists it.

    Four separate hardcoded copies existed. Two were found only when `aw backlog set graduated`
    refused the transition and, worse, when the mover silently declined to relocate the file. Each
    assertion below pins one copy to the single source of truth.
    """

    def test_status_set_setter_vocabulary_is_derived(self):
        from agent_workflows import status_set

        self.assertEqual(status_set.TYPE_STATUSES["backlog"], set(backlog.STATUSES))

    def test_dependency_schema_vocabulary_is_derived(self):
        self.assertEqual(
            ipd_schema._ITEM_DEP_STATE_STATUSES["backlog"], backlog.STATUSES
        )

    def test_completion_vocabulary_is_derived(self):
        from agent_workflows import completion

        got = completion.status_candidates("backlog")
        self.assertEqual(sorted(got), sorted(backlog.STATUSES))

    def test_attention_map_covers_every_status(self):
        self.assertEqual(
            set(A.CLASS_MAPS["backlog"]),
            set(backlog.STATUSES),
            "the attention map and the status enum must agree exactly",
        )


class AttentionClassTests(unittest.TestCase):
    """E-02: graduated -> active, which keeps it in the release-blocker set."""

    def test_graduated_maps_to_active(self):
        self.assertEqual(A.class_of("backlog", "graduated"), A.ACTIVE)

    def test_graduated_is_not_done_or_ready_or_parked(self):
        cls = A.class_of("backlog", "graduated")
        self.assertNotEqual(cls, A.DONE, "done would drop it from the blocker set")
        self.assertNotEqual(cls, A.READY, "no action is owed on the item itself")
        self.assertNotEqual(cls, A.PARKED, "the work is intentionally live")

    def test_class_map_is_total_over_the_enum(self):
        unmapped = [s for s in backlog.STATUSES if s not in A.CLASS_MAPS["backlog"]]
        self.assertEqual(unmapped, [], f"unmapped backlog statuses: {unmapped}")

    def test_existing_mappings_unchanged(self):
        self.assertEqual(A.class_of("backlog", "open"), A.READY)
        self.assertEqual(A.class_of("backlog", "blocked"), A.BLOCKED)
        self.assertEqual(A.class_of("backlog", "parked"), A.PARKED)
        self.assertEqual(A.class_of("backlog", "done"), A.DONE)


class CloseLegitimacyTests(unittest.TestCase):
    """E-03: graduated is legitimate and preserves the gate, but is NOT a close."""

    def test_graduated_is_legitimate_for_a_gated_item(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _write_item(root, "bbb222", "open", gate="next")
            v = check_engine.evaluate_blocking_close(root, p, "graduated")
            self.assertTrue(v.legitimate)
            self.assertEqual(v.severity, "ok")
            self.assertIn("preserves gate", v.reason)

    def test_graduated_is_not_a_substitute_for_done(self):
        """LOAD-BEARING: a gated item must still fail closed on `done`."""
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _write_item(root, "ccc333", "open", gate="next")
            v = check_engine.evaluate_blocking_close(root, p, "done")
            self.assertFalse(
                v.legitimate,
                "done must still fail closed with no handoff/evidence/de-gate",
            )
            self.assertEqual(v.severity, "error")

    def test_ungated_item_unaffected(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _write_item(root, "ddd444", "open")
            v = check_engine.evaluate_blocking_close(root, p, "graduated")
            self.assertTrue(v.legitimate)


class DocumentationAgreementTests(unittest.TestCase):
    """E-05: the README's documented status list must equal the code's."""

    def test_readme_status_list_matches_statuses(self):
        readme = REPO_ROOT / ".aw" / "records" / "backlog" / "README.md"
        text = readme.read_text(encoding="utf-8")
        m = re.search(r"^- Status: (.+)$", text, re.M)
        self.assertIsNotNone(m, "README must document a `- Status:` line")
        assert m is not None
        documented = {s.strip() for s in m.group(1).split("|")}
        self.assertEqual(
            documented,
            set(backlog.STATUSES),
            "README status list must equal backlog.STATUSES",
        )

    def test_readme_documents_graduated_directory(self):
        readme = REPO_ROOT / ".aw" / "records" / "backlog" / "README.md"
        text = readme.read_text(encoding="utf-8")
        self.assertIn("graduated/", text)
        self.assertRegex(text, r"graduated/.*active")

    def test_agents_md_documents_the_contract(self):
        text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("graduated`->`active", text.replace(" ", ""))
        for phrase in ("REVIEW-READY IPDs", "From-Backlog", "not `done`"):
            self.assertIn(phrase, text, f"AGENTS.md must state: {phrase}")

    def test_agents_md_contract_has_no_em_or_en_dash(self):
        """Repo rule: no em/en dashes in user-facing prose we author."""
        text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        start = text.find("### Acting on a backlog item")
        self.assertGreater(start, 0, "the contract section must exist")
        section = text[start : start + 2600]
        self.assertNotIn("\u2014", section, "em dash in authored user-facing prose")
        self.assertNotIn("\u2013", section, "en dash in authored user-facing prose")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

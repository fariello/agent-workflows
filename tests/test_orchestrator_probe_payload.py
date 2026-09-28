"""probeprose-01 (`3brgb6`): Behavioral tests for widened probe cache payload and invariants.

Pins the eleven properties of probe_cache_payload, probe_cache_digest, and orchestrator_probe_excerpt:
  Group A: The five xmqv5l no-op invariants (a1..a5) plus composite (a6).
  Group B: The new sensitivity on allowlisted prose (b1) and insensitivity on non-allowlisted (b2).
  Group C: Identity / completeness (c1), structural disjointness (c2), and c3, the named
           residual-gap limit that replaces the deleted TheExcerptHasAKnownLIMIT.
"""

from __future__ import annotations

import re
import unittest
import pytest

from agent_workflows import ipd_lint as lint
from agent_workflows import runner_shared as rs
from tests.support import REPO_ROOT

EXPECTED_PAYLOAD_KEYS = frozenset({"child_table_rows", "e_items", "prose_sections"})

KEY_HEADINGS = {
    "child_table_rows": "### Child IPDs table (row cells, in document order)",
    "e_items": "### Checklist item action text",
    "prose_sections": "### Unattached prose sections",
}

SYNTHETIC_ORCHESTRATOR = """# Synthetic Test Orchestrator

- Concern: testing probe payload invariants
- Scope: tests
- Scope-Paths: tests/test_orchestrator_probe_payload.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: rmcqw8
- Set: probeprose
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: syn001
- Kind: orchestrator

## Workflow history
- 2026-09-28 approved: test

## Goal
A test orchestrator for synthetic invariant verification.

## Cross-IPD validation
- Verify cross-IPD obligations.

## Child IPDs, sequence, and dependencies

| Order | Set | Id | Kind | Description | Status | Gate-Kind | Gate-Ref |
|---|---|---|---|---|---|---|---|
| 01 | syn | syn002 | standard | child 1 | executed | none | none |

## Detailed Implementation Checklist (TODO)

- [ ] E-01 Execute first task
  - Depends on: none
  - Expected outcome: done
  - Observed evidence:
  - Execution state: pending
  - Result: pending

## Open questions
- None.

## Deferred / out of scope (with reason)
- None.
"""

SYNTHETIC_ORCHESTRATOR_RESIDUAL_GAP = """# Synthetic Test Orchestrator Residual Gap

- Concern: testing residual indented line gap
- Scope: tests
- Scope-Paths: tests/test_orchestrator_probe_payload.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: rmcqw8
- Set: probeprose
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: syn002
- Kind: orchestrator

## Workflow history
- 2026-09-28 approved: test

## Goal
Test orchestrator for indented line gap pin.

## Cross-IPD validation
- Line outside item:
  - Subfield: value
    INDENTED LINE SITTING AFTER SUBFIELD: MUST BE FLAGGED (parent-only work no child covers)

## Child IPDs, sequence, and dependencies

| Order | Set | Id | Kind | Description | Status | Gate-Kind | Gate-Ref |
|---|---|---|---|---|---|---|---|
| 01 | syn | syn003 | standard | child 1 | executed | none | none |

## Detailed Implementation Checklist (TODO)

- [ ] E-01 Simple task
  - Depends on: none
  - Execution state: pending
"""


def _get_corpus_orchestrators() -> list[tuple[str, str]]:
    """Return (filename, text) for every - Kind: orchestrator plan under .aw/records/plans/."""
    plans_dir = REPO_ROOT / ".aw" / "records" / "plans"
    orchs: list[tuple[str, str]] = []
    for p in sorted(plans_dir.rglob("*.md")):
        text = p.read_text(encoding="utf-8")
        m = re.search(r"(?m)^-\s+Kind:\s*(.+)$", text)
        if m and m.group(1).strip() == "orchestrator":
            orchs.append((p.name, text))
    return orchs


def assert_key_completeness(payload: dict, excerpt: str) -> None:
    """Assert every key in payload is represented with a rendered section in excerpt."""
    for key in payload:
        heading = KEY_HEADINGS.get(key)
        if not heading or heading not in excerpt:
            raise AssertionError(
                f"Key {key!r} has no expected rendered section heading in excerpt"
            )


class TestProbePayloadDefaultSuite(unittest.TestCase):
    """Default-suite tests (synthetic fixtures, fast, no corpus scan)."""

    def test_synthetic_a6_composite_digest_invariant(self):
        """Composite of all 5 xmqv5l edits on a synthetic fixture leaves digest unchanged."""
        doc = SYNTHETIC_ORCHESTRATOR
        d0 = rs.probe_cache_digest(doc)

        mutated = doc
        mutated = re.sub(r"- \[ \] ([EV]-\d+)", r"- [x] \1", mutated)
        mutated = re.sub(
            r"(\s+- Observed evidence:)\s*$",
            r"\1 filled evidence",
            mutated,
            flags=re.MULTILINE,
        )
        mutated = re.sub(
            r"(?m)^## Workflow history\s*$",
            "## Workflow history\n- 2026-09-28 appended history line",
            mutated,
            count=1,
        )
        mutated = re.sub(
            r"- Execution state:\s*pending", "- Execution state: performed", mutated
        )
        mutated = re.sub(r"- Result:\s*pending", "- Result: pass", mutated)

        self.assertNotEqual(doc, mutated)
        self.assertEqual(rs.probe_cache_digest(mutated), d0)

    def test_synthetic_b1_allowlisted_prose_sensitivity(self):
        """Inserting a hazard sentence into an allowlisted section moves the digest."""
        doc = SYNTHETIC_ORCHESTRATOR
        d0 = rs.probe_cache_digest(doc)
        hazard = (
            "\nThis orchestrator must migrate the database before any child runs.\n"
        )

        doc_cross = doc.replace(
            "## Cross-IPD validation", "## Cross-IPD validation" + hazard
        )
        self.assertNotEqual(rs.probe_cache_digest(doc_cross), d0)

        doc_goal = doc.replace("## Goal", "## Goal" + hazard)
        self.assertNotEqual(rs.probe_cache_digest(doc_goal), d0)

    def test_synthetic_b2_non_allowlisted_prose_insensitivity(self):
        """Inserting prose into a non-allowlisted section does NOT move the digest."""
        doc = SYNTHETIC_ORCHESTRATOR
        d0 = rs.probe_cache_digest(doc)

        doc_oq = doc.replace(
            "## Open questions", "## Open questions\nShould we test something else?\n"
        )
        self.assertEqual(rs.probe_cache_digest(doc_oq), d0)

        doc_def = doc.replace(
            "## Deferred / out of scope (with reason)",
            "## Deferred / out of scope (with reason)\n- Out of scope obligation\n",
        )
        self.assertEqual(rs.probe_cache_digest(doc_def), d0)

    def test_synthetic_c1_payload_keys_and_excerpt_completeness(self):
        """Payload has exactly the 3 expected keys and all are represented in excerpt."""
        doc = SYNTHETIC_ORCHESTRATOR
        payload = rs.probe_cache_payload(doc)
        self.assertEqual(set(payload.keys()), EXPECTED_PAYLOAD_KEYS)

        excerpt = rs.orchestrator_probe_excerpt(doc)
        assert_key_completeness(payload, excerpt)

    def test_synthetic_c1_synthetic_fourth_key_fails_completeness(self):
        """Injecting an unregistered synthetic fourth key fails key completeness."""
        doc = SYNTHETIC_ORCHESTRATOR
        payload = dict(rs.probe_cache_payload(doc))
        payload["synthetic_fourth_key"] = "unregistered"
        excerpt = rs.orchestrator_probe_excerpt(doc)

        with self.assertRaises(AssertionError):
            assert_key_completeness(payload, excerpt)

    def test_synthetic_c3_indented_line_residual_gap(self):
        """c3: An indented line sitting after a subfield in an allowlisted section reaches neither extractor.

        This test documents the residual gap (F-16, PR-401). If this test now fails because the line IS
        found in prose_sections or e_items, the indented-line gap was closed and F-16 plus the Deferred row
        must be updated.
        """
        doc = SYNTHETIC_ORCHESTRATOR_RESIDUAL_GAP
        payload = rs.probe_cache_payload(doc)
        target = "INDENTED LINE SITTING AFTER SUBFIELD: MUST BE FLAGGED (parent-only work no child covers)"

        in_e_items = any(target in item for item in payload.get("e_items", []))
        self.assertFalse(in_e_items, "Indented line unexpectedly reached e_items")

        in_prose = any(
            target in text for text in payload.get("prose_sections", {}).values()
        )
        self.assertFalse(
            in_prose,
            "if this now passes the indented-line gap was closed and F-16 plus the Deferred row must be updated.",
        )


@pytest.mark.livecorpus
class TestProbePayloadLiveCorpus(unittest.TestCase):
    """Livecorpus tests sweeping all orchestrators in .aw/records/plans/."""

    def test_corpus_group_a_no_op_invariants(self):
        """Group A: The five xmqv5l no-op invariants (a1..a5) and composite (a6)."""
        orchs = _get_corpus_orchestrators()
        self.assertGreater(len(orchs), 0)

        # a1: ticking checkboxes
        a1_app, a1_moved = 0, 0
        for _name, t in orchs:
            d0 = rs.probe_cache_digest(t)
            t1 = re.sub(r"- \[ \] ([EV]-\d+)", r"- [x] \1", t)
            if t1 != t:
                a1_app += 1
                if rs.probe_cache_digest(t1) != d0:
                    a1_moved += 1

        # a2: observed evidence
        a2_app, a2_moved = 0, 0
        for _name, t in orchs:
            d0 = rs.probe_cache_digest(t)
            t2 = re.sub(
                r"(\s+- Observed evidence:)\s*$",
                r"\1 filled evidence for testing",
                t,
                flags=re.MULTILINE,
            )
            if t2 != t:
                a2_app += 1
                if rs.probe_cache_digest(t2) != d0:
                    a2_moved += 1

        # a3: workflow history
        a3_app, a3_moved = 0, 0
        for _name, t in orchs:
            d0 = rs.probe_cache_digest(t)
            if re.search(r"(?m)^## Workflow history\s*$", t):
                a3_app += 1
                t3 = re.sub(
                    r"(?m)^## Workflow history\s*$",
                    "## Workflow history\n- 2026-09-28 appended history line",
                    t,
                    count=1,
                )
                if rs.probe_cache_digest(t3) != d0:
                    a3_moved += 1

        # a4: execution state
        a4_app, a4_moved = 0, 0
        for _name, t in orchs:
            d0 = rs.probe_cache_digest(t)
            t4 = re.sub(
                r"- Execution state:\s*pending", "- Execution state: performed", t
            )
            if t4 != t:
                a4_app += 1
                if rs.probe_cache_digest(t4) != d0:
                    a4_moved += 1

        # a5: result
        a5_app, a5_moved = 0, 0
        for _name, t in orchs:
            d0 = rs.probe_cache_digest(t)
            t5 = re.sub(r"- Result:\s*pending", "- Result: pass", t)
            if t5 != t:
                a5_app += 1
                if rs.probe_cache_digest(t5) != d0:
                    a5_moved += 1

        # a6: composite (all 5)
        a6_app, a6_moved = 0, 0
        for _name, t in orchs:
            d0 = rs.probe_cache_digest(t)
            t6 = t
            t6 = re.sub(r"- \[ \] ([EV]-\d+)", r"- [x] \1", t6)
            t6 = re.sub(
                r"(\s+- Observed evidence:)\s*$",
                r"\1 filled evidence",
                t6,
                flags=re.MULTILINE,
            )
            t6 = re.sub(
                r"(?m)^## Workflow history\s*$",
                "## Workflow history\n- 2026-09-28 appended history line",
                t6,
                count=1,
            )
            t6 = re.sub(
                r"- Execution state:\s*pending", "- Execution state: performed", t6
            )
            t6 = re.sub(r"- Result:\s*pending", "- Result: pass", t6)
            if t6 != t:
                a6_app += 1
                if rs.probe_cache_digest(t6) != d0:
                    a6_moved += 1

        print(f"\n[Group A Invariants on {len(orchs)} orchestrators]")
        print(f"  a1 (ticked checkboxes):       applicable={a1_app}, moved={a1_moved}")
        print(f"  a2 (observed evidence):       applicable={a2_app}, moved={a2_moved}")
        print(f"  a3 (workflow history):        applicable={a3_app}, moved={a3_moved}")
        print(f"  a4 (execution state):         applicable={a4_app}, moved={a4_moved}")
        print(f"  a5 (result):                  applicable={a5_app}, moved={a5_moved}")
        print(f"  a6 (composite all 5):         applicable={a6_app}, moved={a6_moved}")

        self.assertEqual(a1_moved, 0)
        self.assertEqual(a2_moved, 0)
        self.assertEqual(a3_moved, 0)
        self.assertEqual(a4_moved, 0)
        self.assertEqual(a5_moved, 0)
        self.assertEqual(a6_moved, 0)

    def test_corpus_group_b_sensitivity_and_insensitivity(self):
        """Group B: Sensitivity on allowlisted prose (b1) and insensitivity on non-allowlisted (b2)."""
        orchs = _get_corpus_orchestrators()
        self.assertGreater(len(orchs), 0)
        hazard = (
            "\nThis orchestrator must migrate the database before any child runs.\n"
        )

        # b1: hazard in Cross-IPD validation and Goal
        b1_cross_app, b1_cross_moved = 0, 0
        b1_goal_app, b1_goal_moved = 0, 0
        for _name, t in orchs:
            d0 = rs.probe_cache_digest(t)
            if "## Cross-IPD validation" in t:
                b1_cross_app += 1
                t_cross = t.replace(
                    "## Cross-IPD validation", "## Cross-IPD validation" + hazard
                )
                if rs.probe_cache_digest(t_cross) != d0:
                    b1_cross_moved += 1
            if "## Goal" in t:
                b1_goal_app += 1
                t_goal = t.replace("## Goal", "## Goal" + hazard)
                if rs.probe_cache_digest(t_goal) != d0:
                    b1_goal_moved += 1

        # b2: prose edit in Open questions and Deferred
        b2_oq_app, b2_oq_moved = 0, 0
        b2_def_app, b2_def_moved = 0, 0
        for _name, t in orchs:
            d0 = rs.probe_cache_digest(t)
            if "## Open questions" in t:
                b2_oq_app += 1
                t_oq = t.replace(
                    "## Open questions", "## Open questions\nShould we ask something?\n"
                )
                if rs.probe_cache_digest(t_oq) != d0:
                    b2_oq_moved += 1
            if "## Deferred / out of scope" in t:
                b2_def_app += 1
                t_def = t.replace(
                    "## Deferred / out of scope",
                    "## Deferred / out of scope\n- Some deferred obligation\n",
                )
                if rs.probe_cache_digest(t_def) != d0:
                    b2_def_moved += 1

        print(f"\n[Group B Sensitivity on {len(orchs)} orchestrators]")
        print(
            f"  b1 (Cross-IPD validation hazard): applicable={b1_cross_app}, moved={b1_cross_moved}"
        )
        print(
            f"  b1 (Goal hazard):                 applicable={b1_goal_app}, moved={b1_goal_moved}"
        )
        print(
            f"  b2 (Open questions prose edit):   applicable={b2_oq_app}, moved={b2_oq_moved}"
        )
        print(
            f"  b2 (Deferred prose edit):         applicable={b2_def_app}, moved={b2_def_moved}"
        )

        self.assertEqual(b1_cross_app, b1_cross_moved)
        self.assertEqual(b1_goal_app, b1_goal_moved)
        self.assertEqual(b2_oq_moved, 0)
        self.assertEqual(b2_def_moved, 0)

    def test_corpus_group_c_identity_and_disjointness(self):
        """Group C: Identity/completeness (c1) and disjointness (c2) over all orchestrators."""
        orchs = _get_corpus_orchestrators()
        self.assertGreater(len(orchs), 0)

        # c1: payload keys and excerpt completeness
        c1_count = 0
        for _name, t in orchs:
            payload = rs.probe_cache_payload(t)
            self.assertEqual(set(payload.keys()), EXPECTED_PAYLOAD_KEYS)
            excerpt = rs.orchestrator_probe_excerpt(t)
            assert_key_completeness(payload, excerpt)
            c1_count += 1

        # c2: disjointness
        shared_lines_over_40 = 0
        shared_cells_over_25 = 0
        for _name, t in orchs:
            e_blocks = rs.e_item_action_blocks(t)
            prose_dict = lint.unattached_section_prose(t)
            for title, prose in prose_dict.items():
                for line in prose.splitlines():
                    line_str = line.strip()
                    if len(line_str) > 40 and any(
                        line_str in block for block in e_blocks
                    ):
                        shared_lines_over_40 += 1

            rows = rs.child_table_rows(t)
            allowlisted_prose = "\n".join(
                prose
                for sec, prose in prose_dict.items()
                if sec in rs.PROBE_PROSE_SECTIONS
            )
            for row in rows:
                for cell in row:
                    c = str(cell).strip()
                    if len(c) > 25 and c in allowlisted_prose:
                        shared_cells_over_25 += 1

        print(f"\n[Group C Identity and Disjointness on {len(orchs)} orchestrators]")
        print(f"  c1 (key identity and completeness): checked={c1_count}")
        print(f"  c2 (shared prose lines > 40 chars): {shared_lines_over_40}")
        print(f"  c2 (shared table cells > 25 chars): {shared_cells_over_25}")

        self.assertEqual(c1_count, len(orchs))
        self.assertEqual(shared_lines_over_40, 0)
        self.assertEqual(shared_cells_over_25, 0)

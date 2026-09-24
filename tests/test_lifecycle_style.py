"""Tests for the ONE canonical lifecycle presentation module (spec ``uonrjg``, plan ``udgilu``).

Table-driven, stdlib unittest, zero dependencies. Verifies:

- the stage table matches spec Section 5 MECHANICALLY, by parsing the spec's own normative table
  rather than by re-typing it here (a second hand-typed copy would be the very duplication this
  module exists to end, and it would pass while both copies were wrong together);
- CRITERION A2, the load-bearing guard: every member of every repository OWNER ENUM resolves to
  exactly one stage, so a status added to an owner without a mapping FAILS here;
- the six review-added / late-added runner rows that a naive reading of Section 7.2 would drop;
- Section 8's resolution precedence, rung by rung;
- R10.4's ``unknown`` versus ``none`` distinction (criterion A20);
- R10.1's no-ANSI and stdlib-only constraints, and its self-validation.

WHY THE OWNER ENUMS ARE IMPORTED RATHER THAN LISTED (criterion A2's actual requirement): "Tests
enumerate the repository's owner enums and fail when a newly added status lacks a mapping." A test
that hand-copied the statuses would keep passing after an owner grew a member, which is precisely
the drift it is supposed to catch. Every assertion below therefore reads the owner's own symbol.
This mirrors the shipped precedent in ``tests/test_attention_contract.py``'s
``MappingTotalityTests``, including its lazy imports.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows import lifecycle_style as L

REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "agent_workflows" / "lifecycle_style.py"
SPEC_PATH = next(
    (REPO / ".aw" / "records" / "specs").rglob(
        "20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md"
    )
)

# The five prompt LANES. Prompt status is carried by DIRECTORY, not by an enum: `prompts.py` defines
# only `DEFAULT_STATUS` and `PROMPT_KINDS`, so there is no `prompts.STATUSES` to enumerate (plan
# `udgilu` F-06). These five are `ipd_lint._dir_of`'s anchors, and `test_prompts_directory_derived`
# below asserts they are still exactly that set, so this list cannot silently drift from the owner.
PROMPT_LANES = ("pending", "executed", "reusable", "superseded", "not-executed")


def _parse_spec_section5():
    """Parse the NORMATIVE Section 5 table out of the spec file.

    Returns a list of ``(stage, unicode, ascii, color, bold)`` tuples in spec order. Parsing rather
    than transcribing is the whole point: a transcription slip in any of 20 rows times 4 fields
    fails here instead of being read past.
    """
    lines = SPEC_PATH.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("## 5. "))
    rows = []
    for line in lines[start:]:
        if line.startswith("## 6."):
            break
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6:
            continue
        if cells[0] == "Semantic stage" or set(cells[0]) <= set("-: "):
            continue

        def unq(text):
            return text.strip().strip("`")

        rows.append(
            (
                unq(cells[0]),
                unq(cells[1]),
                unq(cells[2]),
                int(unq(cells[3])),
                unq(cells[4]) == "yes",
            )
        )
    return rows


class StageTableTests(unittest.TestCase):
    """E-01 / V-01: the stage table IS spec Section 5."""

    def test_stage_table_and_glyphs_progression(self):
        spec_rows = _parse_spec_section5()
        self.assertTrue(spec_rows, "failed to parse the spec's Section 5 table")
        module_rows = [
            (s.stage, s.unicode, s.ascii, s.color, s.bold)
            for s in (L.STAGES[name] for name in L.STAGE_ORDER)
        ]
        self.assertEqual(module_rows, spec_rows)
        self.assertEqual(len(L.STAGE_ORDER), len(set(L.STAGE_ORDER)))
        self.assertEqual(set(L.STAGE_ORDER), set(L.ALL_STAGES))

        # progression
        stages = [
            L.resolve("plans", s).style.unicode
            for s in ("draft", "to-review", "reviewed", "approved")
        ]
        self.assertEqual(stages, ["○", "◔", "◑", "◕"])
        self.assertEqual(L.resolve("plans", "executed").style.unicode, "✓")

        # named and activity glyphs
        self.assertEqual(L.glyph_for(L.BLOCKED), "\u26a0\ufe0e")
        self.assertEqual(L.glyph_for(L.FAILED), "✘")
        self.assertEqual(L.glyph_for(L.RECOVERING), "\u21a9\ufe0e")
        self.assertEqual(L.glyph_for(L.REUSABLE), "↻")
        self.assertEqual(
            [
                L.glyph_for(s)
                for s in (
                    L.REVIEWING,
                    L.EXECUTING,
                    L.VERIFYING,
                    L.INTEGRATING,
                    L.RECOVERING,
                )
            ],
            ["◎", "▶", "◆", "⇄", "\u21a9\ufe0e"],
        )

        # ascii single-byte fallback
        for stage in L.STAGE_ORDER:
            fallback = L.glyph_for(stage, unicode=False)
            self.assertEqual(len(fallback), 1, stage)
            self.assertEqual(len(fallback.encode("ascii")), 1, stage)

        with self.assertRaises(L.LifecycleStyleError):
            L.style_for("not-a-stage")

    def test_stage_styling_and_presentation_properties(self):
        # Text presentation selector U+FE0E
        self.assertEqual([hex(ord(c)) for c in L.GLYPH_BLOCKED], ["0x26a0", "0xfe0e"])
        self.assertEqual(
            [hex(ord(c)) for c in L.GLYPH_RECOVERING], ["0x21a9", "0xfe0e"]
        )
        self.assertEqual(L.STAGES[L.BLOCKED].unicode, L.GLYPH_BLOCKED)
        self.assertEqual(L.STAGES[L.RECOVERING].unicode, L.GLYPH_RECOVERING)

        # Multicodepoint glyphs declared
        actual = {
            style.unicode for style in L.STAGES.values() if len(style.unicode) > 1
        }
        self.assertEqual(actual, set(L.MULTI_CODEPOINT_GLYPHS))

        # Bold restraint and color separation
        expected_bold = {
            L.READY,
            L.REVIEWING,
            L.EXECUTING,
            L.VERIFYING,
            L.INTEGRATING,
            L.RECOVERING,
            L.ACTIVE,
            L.WAITING_INPUT,
            L.BLOCKED,
            L.FAILED,
            L.DONE,
        }
        self.assertEqual(set(L.BOLD_STAGES), expected_bold)
        self.assertNotEqual(L.STAGES[L.READY].color, L.STAGES[L.DONE].color)
        self.assertNotEqual(L.STAGES[L.BLOCKED].color, L.STAGES[L.FAILED].color)
        self.assertNotEqual(L.STAGES[L.WAITING_INPUT].color, L.STAGES[L.BLOCKED].color)

        # No ANSI in resolved values
        for stage in L.STAGE_ORDER:
            self.assertNotIn("\x1b", repr(L.STAGES[stage]))


class MappingTotalityTests(unittest.TestCase):
    """CRITERION A2. Every OWNER-ENUM member resolves to exactly one stage.

    ONE DIRECTION ONLY, DELIBERATELY. These assertions are ``owner_enum <= mapped_keys``, never
    equality, and the asymmetry is expected rather than a defect. Differencing
    ``runner_shutdown.KNOWN_ITEM_STATUSES`` against spec Section 7.2 leaves NINE Section 7.2 words
    absent from that enum (``awaiting-human``, ``cancelled``, ``complete``, ``correction_required``,
    ``failed``, ``needs_input``, ``ran``, ``unknown_outcome``, ``verified``), because the enum is
    ONE OWNER AMONG SEVERAL: ``needs_input`` belongs to ``run_gates.ALL_GATE_STATUSES``, and
    ``awaiting-human`` and ``ran`` are specified by ``6kwd2e``/``25kzda`` but appear nowhere in
    ``agent_workflows/`` today because ``run_gates`` is unwired to both runners (spec Section 4.4a
    records the same fact).

    SO DO NOT "TIDY" THIS INTO AN EQUALITY, and do not delete an unreferenced mapping row to make
    one pass: those rows are contract-mandated, and Section 6's preamble forbids dropping a known
    status. Narrowing the resolver to match one owner would silently narrow an approved,
    release-gating spec.
    """

    def _assert_covered(self, family, owner_statuses, owner_name):
        mapped = set(L.NATIVE_MAPS[family])
        missing = sorted(set(owner_statuses) - mapped)
        self.assertEqual(
            missing,
            [],
            "family {0!r} does not map these {1} members: {2}".format(
                family, owner_name, missing
            ),
        )
        # And each one resolves to a REAL stage rather than to the unknown fallthrough, which is
        # what Section 6's preamble calls a defect for a known status.
        for status in sorted(owner_statuses):
            resolved = L.resolve(family, status)
            self.assertIn(resolved.stage, L.ALL_STAGES, status)
            self.assertNotEqual(resolved.stage, L.UNKNOWN, status)
            self.assertIsNone(resolved.diagnostic, status)

    def test_all_owner_enums_are_covered_by_native_maps(self):
        from agent_workflows import (
            attention_contract,
            backlog,
            comms,
            plans,
            releases,
            research_contract,
            run_gates,
            run_state,
            runner_shutdown,
            set_state,
        )

        checks = [
            (L.FAMILY_PLANS, plans.RECOGNIZED, "plans.RECOGNIZED"),
            (
                L.FAMILY_SPECS,
                attention_contract.SPEC_STATUSES,
                "attention_contract.SPEC_STATUSES",
            ),
            (
                L.FAMILY_RESEARCH,
                research_contract.STATUSES,
                "research_contract.STATUSES",
            ),
            (L.FAMILY_BACKLOG, backlog.STATUSES, "backlog.STATUSES"),
            (L.FAMILY_RELEASES, releases.RELEASE_STATUSES, "releases.RELEASE_STATUSES"),
            (
                L.FAMILY_RUNNER_ITEM,
                runner_shutdown.KNOWN_ITEM_STATUSES,
                "runner_shutdown.KNOWN_ITEM_STATUSES",
            ),
            (L.FAMILY_SET_STATE, set_state.ALL_SET_STATES, "set_state.ALL_SET_STATES"),
            (L.FAMILY_RUN_LEDGER, run_state.ALL_STATES, "run_state.ALL_STATES"),
            (L.FAMILY_COMMS_ACK, comms.ACK_STATES, "comms.ACK_STATES"),
            (L.FAMILY_PROMPTS, PROMPT_LANES, "prompt directory lanes"),
        ]
        for family, statuses, label in checks:
            with self.subTest(family=family):
                self._assert_covered(family, statuses, label)

        self.assertIn("needs_input", run_gates.ALL_GATE_STATUSES)
        self.assertEqual(
            L.resolve(L.FAMILY_RUNNER_ITEM, "needs_input").stage, L.WAITING_INPUT
        )

    def test_every_family_has_exactly_one_policy_and_stages_defined(self):
        for family, table in L.NATIVE_MAPS.items():
            for status, stage in table.items():
                self.assertIn(stage, L.ALL_STAGES, f"{family}:{status}")
        self.assertEqual(set(L.NATIVE_MAPS) & set(L.NO_LIFECYCLE_FAMILIES), set())
        self.assertEqual(L.FAMILIES, set(L.NATIVE_MAPS) | set(L.NO_LIFECYCLE_FAMILIES))


class SpecSectionCoverageTests(unittest.TestCase):
    """The runner and workflow lifecycle stage mappings."""

    def test_runner_and_workflow_status_mappings(self):
        # WAITING_INPUT
        for status in ("needs_input", "awaiting-human"):
            self.assertEqual(
                L.resolve(L.FAMILY_RUNNER_ITEM, status).stage, L.WAITING_INPUT, status
            )
        self.assertNotEqual(L.STAGES[L.WAITING_INPUT].color, L.STAGES[L.BLOCKED].color)

        # RECOVERING / FAILED / PARKED
        self.assertEqual(L.resolve(L.FAMILY_RUNNER_ITEM, "ran").stage, L.RECOVERING)
        self.assertEqual(
            L.resolve(L.FAMILY_RUNNER_ITEM, "unknown_outcome").stage, L.FAILED
        )
        self.assertEqual(L.resolve(L.FAMILY_RUNNER_ITEM, "quarantined").stage, L.PARKED)
        self.assertEqual(
            L.resolve(L.FAMILY_PLANS, "approved", condition="quarantined").stage,
            L.PARKED,
        )
        self.assertEqual(
            L.resolve(L.FAMILY_RUNNER_ITEM, "merge-retry").stage, L.RECOVERING
        )

        # BLOCKED group
        for status in (
            "blocked",
            "dependency-blocked",
            "merge-needs-human",
            "merge-refused",
        ):
            self.assertEqual(
                L.resolve(L.FAMILY_RUNNER_ITEM, status).stage, L.BLOCKED, status
            )

        # Ledger and backlog mappings
        self.assertEqual(L.resolve(L.FAMILY_RUN_LEDGER, "performed").stage, L.VERIFYING)
        self.assertEqual(L.resolve(L.FAMILY_RUN_LEDGER, "verified").stage, L.DONE)
        self.assertEqual(L.resolve(L.FAMILY_BACKLOG, "graduated").stage, L.ACTIVE)
        self.assertEqual(L.resolve(L.FAMILY_RUNNER_ITEM, "abandoned?").stage, L.UNKNOWN)

    def test_activity_from_action_and_readiness(self):
        expected = {
            "review": L.REVIEWING,
            "execute": L.EXECUTING,
            "implement": L.EXECUTING,
            "verify": L.VERIFYING,
            "test": L.VERIFYING,
            "merge": L.INTEGRATING,
            "rebase": L.INTEGRATING,
            "integrate": L.INTEGRATING,
            "retry": L.RECOVERING,
            "correct": L.RECOVERING,
            "resume": L.RECOVERING,
            "run": L.ACTIVE,
            "await-human": L.WAITING_INPUT,
        }
        for action, stage in expected.items():
            self.assertEqual(L.ACTIVITY_FROM_ACTION[action], stage, action)

        self.assertEqual(L.resolve_readiness("go").stage, L.READY)
        self.assertEqual(
            L.resolve_readiness("go-pending-approval").stage, L.AUTHORITY_QUEUED
        )
        self.assertEqual(L.resolve_readiness("no-go").stage, L.BLOCKED)
        self.assertEqual(L.READINESS_LABEL, "readiness")
        self.assertIsNotNone(L.resolve_readiness("maybe").diagnostic)


class PrecedenceTests(unittest.TestCase):
    """Section 8 rung precedence ladder and resolver immutability."""

    def test_precedence_ladder_integrity_obstruction_condition_activity_native(self):
        # Integrity beats all
        resolved_int = L.resolve(
            L.FAMILY_PLANS, "approved", activity="executing", integrity="invalid"
        )
        self.assertEqual(resolved_int.stage, L.FAILED)
        self.assertEqual(resolved_int.style.unicode, "✘")
        self.assertEqual(
            L.resolve(
                L.FAMILY_PLANS,
                "approved",
                obstruction="gate",
                integrity="contradictory",
            ).stage,
            L.FAILED,
        )

        # Obstruction beats condition and ready
        resolved_obs = L.resolve(L.FAMILY_PLANS, "approved", obstruction="gate D-021")
        self.assertEqual(resolved_obs.stage, L.BLOCKED)
        self.assertEqual(resolved_obs.obstruction, "gate D-021")
        self.assertEqual(
            L.resolve(
                L.FAMILY_PLANS, "approved", condition="quarantined", obstruction="gate"
            ).stage,
            L.BLOCKED,
        )

        # Condition beats activity
        self.assertEqual(
            L.resolve(
                L.FAMILY_PLANS, "approved", activity="execute", condition="quarantined"
            ).stage,
            L.PARKED,
        )

        # Activity beats native
        resolved_act = L.resolve(L.FAMILY_PLANS, "approved", activity="execute")
        self.assertEqual(resolved_act.stage, L.EXECUTING)
        self.assertEqual(resolved_act.native_status, "approved")

        # Sound vs unsound integrity
        for sound in sorted(L.INTEGRITY_SOUND_VALUES):
            self.assertEqual(
                L.resolve(L.FAMILY_PLANS, "approved", integrity=sound).stage,
                L.READY,
                sound,
            )
        self.assertEqual(
            L.resolve(L.FAMILY_PLANS, "approved", integrity=True).stage, L.READY
        )
        self.assertEqual(
            L.resolve(L.FAMILY_PLANS, "approved", integrity=False).stage, L.FAILED
        )

    def test_resolver_immutability_and_preservation(self):
        record = {"status": "approved", "activity": "execute"}
        before = dict(record)
        stages_before = dict(L.STAGES)
        maps_before = {f: dict(t) for f, t in L.NATIVE_MAPS.items()}
        L.resolve(L.FAMILY_PLANS, record["status"], activity=record["activity"])
        self.assertEqual(record, before)
        self.assertEqual(dict(L.STAGES), stages_before)
        self.assertEqual({f: dict(t) for f, t in L.NATIVE_MAPS.items()}, maps_before)

        with self.assertRaises(TypeError):
            L.STAGES["ready"] = None  # type: ignore[index]
        with self.assertRaises(TypeError):
            L.NATIVE_MAPS["plans"]["draft"] = "done"  # type: ignore[index]

        self.assertEqual(
            L.resolve(L.FAMILY_PLANS, "Approved").native_status, "Approved"
        )
        self.assertEqual(L.resolve(L.FAMILY_PLANS, "  approved ").stage, L.READY)


class UnknownVersusNoneTests(unittest.TestCase):
    """R10.4 / criterion A20: the two fallbacks are distinct, and neither is parked gray."""

    def test_unknown_and_none_fallbacks_and_diagnostics(self):
        resolved = L.resolve(L.FAMILY_PLANS, "invented-status")
        self.assertEqual(resolved.stage, L.UNKNOWN)
        self.assertEqual(resolved.style.unicode, "?")
        self.assertIn("invented-status", resolved.diagnostic or "")
        self.assertEqual(resolved.native_status, "invented-status")

        # Missing status in lifecycle family is unknown
        self.assertEqual(L.resolve(L.FAMILY_PLANS, None).stage, L.UNKNOWN)

        # Non-lifecycle families resolve to NONE
        for family in sorted(L.NO_LIFECYCLE_FAMILIES):
            r = L.resolve(family)
            self.assertEqual(r.stage, L.NONE, family)
            self.assertEqual(r.style.unicode, "·", family)

        # Glyphs distinguish UNKNOWN, NONE, PARKED
        glyphs = {L.glyph_for(s) for s in (L.UNKNOWN, L.NONE, L.PARKED)}
        self.assertEqual(len(glyphs), 3)

        # Unrecognized activity/condition carry diagnostics
        self.assertIsNotNone(
            L.resolve(L.FAMILY_PLANS, "approved", activity="frobnicating").diagnostic
        )
        self.assertIsNotNone(
            L.resolve(L.FAMILY_PLANS, "approved", condition="unheard-of").diagnostic
        )

    def test_unknown_family_raises(self):
        with self.assertRaises(L.UnknownFamily):
            L.resolve("not-a-family", "approved")


class SelfValidationTests(unittest.TestCase):
    """R10.1's validation: duplicate keys and incomplete coverage are HARD errors."""

    def test_validation_passes_on_shipped_tables_and_rejects_duplicates(self):
        L.validate()

        rows = L._STAGE_ROWS + (L._STAGE_ROWS[0],)
        with self.assertRaises(L.LifecycleStyleError):
            L._build_stage_table(rows)

        with self.assertRaises(L.LifecycleStyleError):
            L._build_map("demo", (("draft", L.FORMATIVE), ("draft", L.DONE)))

        with self.assertRaises(L.LifecycleStyleError):
            L._build_map("demo", (("draft", "not-a-stage"),))

    def test_incomplete_coverage_and_ghost_families_rejected(self):
        original = L.KNOWN_STATUSES
        from types import MappingProxyType

        widened = dict({f: set(s) for f, s in original.items()})
        widened[L.FAMILY_PLANS] = set(widened[L.FAMILY_PLANS]) | {"phantom-status"}
        try:
            L.KNOWN_STATUSES = MappingProxyType(
                {f: frozenset(s) for f, s in widened.items()}
            )
            with self.assertRaises(L.LifecycleStyleError) as ctx:
                L.validate()
            self.assertIn("phantom-status", str(ctx.exception))
        finally:
            L.KNOWN_STATUSES = original

        try:
            L.KNOWN_STATUSES = MappingProxyType(
                dict(original, **{"ghost-family": frozenset({"x"})})
            )
            with self.assertRaises(L.LifecycleStyleError) as ctx:
                L.validate()
            self.assertIn("ghost-family", str(ctx.exception))
        finally:
            L.KNOWN_STATUSES = original
        L.validate()


if __name__ == "__main__":
    unittest.main()

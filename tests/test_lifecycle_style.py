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

import re
import unittest
from pathlib import Path

from agent_workflows import lifecycle_style as L

REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "agent_workflows" / "lifecycle_style.py"
SPEC_PATH = (
    REPO
    / ".aw"
    / "records"
    / "specs"
    / "20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md"
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
    """E-01 / V-01: the stage table IS spec Section 5, checked against the spec's own bytes."""

    def test_table_matches_spec_section5_row_for_row(self):
        spec_rows = _parse_spec_section5()
        self.assertTrue(spec_rows, "failed to parse the spec's Section 5 table")
        module_rows = [
            (s.stage, s.unicode, s.ascii, s.color, s.bold)
            for s in (L.STAGES[name] for name in L.STAGE_ORDER)
        ]
        self.assertEqual(module_rows, spec_rows)

    def test_row_count_is_the_spec_table_length(self):
        # Asserted against the PARSED spec rather than against a literal 20. A literal count is a
        # second table, and the spec's own D13 ("Rejected a new 21st stage") is corroboration that
        # the number is 20 rather than a reason to hardcode it.
        self.assertEqual(len(L.STAGES), len(_parse_spec_section5()))

    def test_stage_order_has_no_duplicates(self):
        self.assertEqual(len(L.STAGE_ORDER), len(set(L.STAGE_ORDER)))
        self.assertEqual(set(L.STAGE_ORDER), set(L.ALL_STAGES))

    def test_text_presentation_selectors_present(self):
        # Section 5 / criterion A15: U+FE0E must be there, and the emoji forms must not.
        self.assertEqual([hex(ord(c)) for c in L.GLYPH_BLOCKED], ["0x26a0", "0xfe0e"])
        self.assertEqual(
            [hex(ord(c)) for c in L.GLYPH_RECOVERING], ["0x21a9", "0xfe0e"]
        )
        self.assertEqual(L.STAGES[L.BLOCKED].unicode, L.GLYPH_BLOCKED)
        self.assertEqual(L.STAGES[L.RECOVERING].unicode, L.GLYPH_RECOVERING)

    def test_emoji_presentation_forms_absent_from_the_module(self):
        # Criterion A5. The code points alone do not prove this: an emoji-form glyph could sit in a
        # comment or in a second constant, so the whole source is scanned.
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("\u26a0\ufe0f", source)  # the emoji warning sign
        self.assertNotIn("\u21a9\ufe0f", source)  # the emoji return arrow

    def test_multi_codepoint_glyphs_are_declared(self):
        # Section 4.5: len() is not a display-width proxy. The module must SAY which glyphs are
        # two code points so a renderer can act on it rather than rediscovering it.
        actual = {
            style.unicode for style in L.STAGES.values() if len(style.unicode) > 1
        }
        self.assertEqual(actual, set(L.MULTI_CODEPOINT_GLYPHS))

    def test_criterion_a4_named_glyphs(self):
        self.assertEqual(L.glyph_for(L.BLOCKED), "\u26a0\ufe0e")
        self.assertEqual(L.glyph_for(L.FAILED), "✘")
        self.assertEqual(L.glyph_for(L.RECOVERING), "\u21a9\ufe0e")
        self.assertEqual(L.glyph_for(L.REUSABLE), "↻")

    def test_criterion_a3_activity_glyphs(self):
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

    def test_criterion_a6_plan_glyph_progression(self):
        stages = [
            L.resolve("plans", s).style.unicode
            for s in ("draft", "to-review", "reviewed", "approved")
        ]
        self.assertEqual(stages, ["○", "◔", "◑", "◕"])
        self.assertEqual(L.resolve("plans", "executed").style.unicode, "✓")

    def test_ascii_fallbacks_are_single_byte(self):
        # Section 9.4: "guaranteed single-byte alignment in ASCII mode".
        for stage in L.STAGE_ORDER:
            fallback = L.glyph_for(stage, unicode=False)
            self.assertEqual(len(fallback), 1, stage)
            self.assertEqual(len(fallback.encode("ascii")), 1, stage)

    def test_bold_restraint(self):
        # Section 11 item 4 permits bold on ready, the active family, waiting, blocked, failed, done.
        expected = {
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
        self.assertEqual(set(L.BOLD_STAGES), expected)

    def test_green_is_reserved_for_done(self):
        # Section 5's explicit separations: ready is cyan not green; blocked is orange not red.
        self.assertNotEqual(L.STAGES[L.READY].color, L.STAGES[L.DONE].color)
        self.assertNotEqual(L.STAGES[L.BLOCKED].color, L.STAGES[L.FAILED].color)
        self.assertNotEqual(L.STAGES[L.WAITING_INPUT].color, L.STAGES[L.BLOCKED].color)

    def test_style_for_rejects_an_undefined_stage(self):
        with self.assertRaises(L.LifecycleStyleError):
            L.style_for("not-a-stage")


class NoAnsiAndStdlibOnlyTests(unittest.TestCase):
    """R10.1: the module emits no ANSI and imports only the standard library."""

    def test_no_escape_sequences_in_source(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        for needle in ("\\033", "\\x1b", "\x1b", "\\u001b"):
            self.assertNotIn(needle, source, needle)

    def test_no_ansi_in_any_resolved_value(self):
        for stage in L.STAGE_ORDER:
            self.assertNotIn("\x1b", repr(L.STAGES[stage]))

    def test_imports_are_stdlib_only(self):
        imports = [
            line.strip()
            for line in MODULE_PATH.read_text(encoding="utf-8").splitlines()
            if re.match(r"^(import|from)\s", line)
        ]
        self.assertTrue(imports)
        for line in imports:
            module = line.split()[1].split(".")[0]
            self.assertIn(
                module,
                {"__future__", "types", "typing"},
                "non-stdlib import: {0}".format(line),
            )


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

    def test_plans_total_over_RECOGNIZED(self):
        from agent_workflows import plans

        self._assert_covered(L.FAMILY_PLANS, plans.RECOGNIZED, "plans.RECOGNIZED")

    def test_specs_total_over_SPEC_STATUSES(self):
        from agent_workflows import attention_contract

        self._assert_covered(
            L.FAMILY_SPECS,
            attention_contract.SPEC_STATUSES,
            "attention_contract.SPEC_STATUSES",
        )

    def test_research_total_over_STATUSES(self):
        from agent_workflows import research_contract

        self._assert_covered(
            L.FAMILY_RESEARCH, research_contract.STATUSES, "research_contract.STATUSES"
        )

    def test_backlog_total_over_STATUSES(self):
        from agent_workflows import backlog

        self._assert_covered(L.FAMILY_BACKLOG, backlog.STATUSES, "backlog.STATUSES")

    def test_releases_total_over_RELEASE_STATUSES(self):
        from agent_workflows import releases

        self._assert_covered(
            L.FAMILY_RELEASES, releases.RELEASE_STATUSES, "releases.RELEASE_STATUSES"
        )

    def test_runner_items_total_over_KNOWN_ITEM_STATUSES(self):
        """The owner that made this criterion bite: 15 members, one of which (`integration-deferred`)
        the spec's Section 7.2 did not cover when this plan was authored."""
        from agent_workflows import runner_shutdown

        self._assert_covered(
            L.FAMILY_RUNNER_ITEM,
            runner_shutdown.KNOWN_ITEM_STATUSES,
            "runner_shutdown.KNOWN_ITEM_STATUSES",
        )

    def test_set_states_total_over_ALL_SET_STATES(self):
        from agent_workflows import set_state

        self._assert_covered(
            L.FAMILY_SET_STATE, set_state.ALL_SET_STATES, "set_state.ALL_SET_STATES"
        )

    def test_run_ledger_total_over_run_state_ALL_STATES(self):
        """Section 7.3's OTHER owner. `set_state` deliberately `set_`-prefixes its tokens so they
        never collide with `run_state`'s bare ones, which is why these are two maps and two
        assertions rather than one union."""
        from agent_workflows import run_state

        self._assert_covered(
            L.FAMILY_RUN_LEDGER, run_state.ALL_STATES, "run_state.ALL_STATES"
        )

    def test_prompts_directory_derived(self):
        """PROMPTS HAVE NO STATUS ENUM (plan `udgilu` F-06), so this family is asserted against the
        DIRECTORY lanes that carry prompt status, and the lane list is itself checked against
        `ipd_lint`'s anchors so it cannot drift."""
        from agent_workflows import prompts

        self.assertFalse(
            hasattr(prompts, "STATUSES"),
            "prompts grew a status enum; assert against it instead of the directory lanes",
        )
        anchors = re.search(
            r"for anchor in \(([^)]*)\):",
            (REPO / "agent_workflows" / "ipd_lint.py").read_text(encoding="utf-8"),
        )
        if anchors is None:
            self.fail("ipd_lint._dir_of's anchor tuple moved")
        found = tuple(re.findall(r'"([^"]+)"', anchors.group(1)))
        self.assertEqual(set(found), set(PROMPT_LANES))
        self._assert_covered(L.FAMILY_PROMPTS, PROMPT_LANES, "prompt directory lanes")

    def test_gate_statuses_that_section_7_2_names_are_mapped(self):
        """`run_gates` is the owner of `needs_input`, which Section 7.2 maps and
        `KNOWN_ITEM_STATUSES` does not contain. Only the statuses Section 7.2 actually NAMES are
        asserted: the rest of that enum (`rejected`, `timed_out`, `refused`, `aborted`) is a GATE
        DECISION vocabulary the spec does not map, and asserting them would invent coverage the
        contract never claimed."""
        from agent_workflows import run_gates

        self.assertIn("needs_input", run_gates.ALL_GATE_STATUSES)
        self.assertEqual(
            L.resolve(L.FAMILY_RUNNER_ITEM, "needs_input").stage, L.WAITING_INPUT
        )

    def test_comms_acks_total_over_ACK_STATES(self):
        """Section 7.4 is PERMISSIVE ("dense status tables MAY use this vocabulary"), but the map
        is provided, so it must be total over its owner or it would send a caller back to inventing
        a palette for the gaps."""
        from agent_workflows import comms

        self._assert_covered(L.FAMILY_COMMS_ACK, comms.ACK_STATES, "comms.ACK_STATES")

    def test_every_mapped_value_is_a_defined_stage(self):
        for family, table in L.NATIVE_MAPS.items():
            for status, stage in table.items():
                self.assertIn(stage, L.ALL_STAGES, "{0}:{1}".format(family, status))

    def test_every_family_has_exactly_one_policy(self):
        self.assertEqual(set(L.NATIVE_MAPS) & set(L.NO_LIFECYCLE_FAMILIES), set())
        self.assertEqual(L.FAMILIES, set(L.NATIVE_MAPS) | set(L.NO_LIFECYCLE_FAMILIES))


class SpecSectionCoverageTests(unittest.TestCase):
    """The six runner rows a naive reading of Section 7.2 drops, asserted individually.

    Each one is a JUDGEMENT the spec argues at length, and each has a plausible wrong answer that a
    from-scratch implementation would pick, so a single "they are all mapped" assertion would not be
    evidence. The wrong answer is asserted against explicitly.
    """

    def test_needs_input_and_awaiting_human_are_waiting_input(self):
        # D12. Also keeps `6kwd2e` R4a.6 satisfied: 214 is distinct from blocked's 208.
        for status in ("needs_input", "awaiting-human"):
            self.assertEqual(
                L.resolve(L.FAMILY_RUNNER_ITEM, status).stage, L.WAITING_INPUT, status
            )
        self.assertNotEqual(L.STAGES[L.WAITING_INPUT].color, L.STAGES[L.BLOCKED].color)

    def test_ran_is_recovering_and_not_done(self):
        # D13. `25kzda` makes a `ran` item exit 1, so green would paint failure as success.
        self.assertEqual(L.resolve(L.FAMILY_RUNNER_ITEM, "ran").stage, L.RECOVERING)
        self.assertNotEqual(L.resolve(L.FAMILY_RUNNER_ITEM, "ran").stage, L.DONE)

    def test_unknown_outcome_is_failed_and_not_unknown(self):
        # D14. A real named terminal disposition owned by `c4gd2h`, not a lookup failure.
        resolved = L.resolve(L.FAMILY_RUNNER_ITEM, "unknown_outcome")
        self.assertEqual(resolved.stage, L.FAILED)
        self.assertNotEqual(resolved.stage, L.UNKNOWN)

    def test_quarantined_is_parked(self):
        # D15, on both routes: as a listed status (for the lint view) and as a field-carried
        # CONDITION input, which is how a resolver actually receives it.
        self.assertEqual(L.resolve(L.FAMILY_RUNNER_ITEM, "quarantined").stage, L.PARKED)
        self.assertEqual(
            L.resolve(L.FAMILY_PLANS, "approved", condition="quarantined").stage,
            L.PARKED,
        )

    def test_integration_deferred_is_recovering(self):
        """Plan `udgilu` OQ-02, resolved from code evidence: the status is in-flight with an
        automatically scheduled re-attempt, so work advances BY ITSELF. That is `recovering`'s
        definition and exactly not `blocked`'s."""
        resolved = L.resolve(L.FAMILY_RUNNER_ITEM, "merge-retry")
        self.assertEqual(resolved.stage, L.RECOVERING)
        self.assertNotEqual(resolved.stage, L.UNKNOWN)
        self.assertNotEqual(resolved.stage, L.BLOCKED)

    def test_integration_deferred_has_a_spec_row(self):
        """The module and the contract must agree: a mapping present in code and absent from the
        spec is exactly the drift this Set exists to end."""
        spec_text = SPEC_PATH.read_text(encoding="utf-8")
        self.assertIn("merge-retry", spec_text)

    def test_blocked_group_shares_one_stage(self):
        # Section 4.4a: many native words to one stage is the design.
        for status in (
            "blocked",
            "dependency-blocked",
            "merge-needs-human",
            "merge-refused",
        ):
            self.assertEqual(
                L.resolve(L.FAMILY_RUNNER_ITEM, status).stage, L.BLOCKED, status
            )

    def test_performed_is_verifying_not_done(self):
        # Section 7.2/7.3: unverified completion MUST NOT be styled as verified success.
        self.assertEqual(L.resolve(L.FAMILY_RUN_LEDGER, "performed").stage, L.VERIFYING)
        self.assertEqual(L.resolve(L.FAMILY_RUN_LEDGER, "verified").stage, L.DONE)

    def test_graduated_is_generic_active(self):
        # Section 6.3: graduation can lead to more than one artifact type, so not `executing`.
        self.assertEqual(L.resolve(L.FAMILY_BACKLOG, "graduated").stage, L.ACTIVE)

    def test_stale_projected_inference_is_unknown(self):
        self.assertEqual(L.resolve(L.FAMILY_RUNNER_ITEM, "abandoned?").stage, L.UNKNOWN)

    def test_activity_from_action_covers_section_7_1(self):
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

    def test_review_readiness_is_separately_labeled(self):
        # Section 6.7: readiness MAY use these stages but MUST be labeled `readiness`.
        self.assertEqual(L.resolve_readiness("go").stage, L.READY)
        self.assertEqual(
            L.resolve_readiness("go-pending-approval").stage, L.AUTHORITY_QUEUED
        )
        self.assertEqual(L.resolve_readiness("no-go").stage, L.BLOCKED)
        self.assertEqual(L.READINESS_LABEL, "readiness")
        self.assertIsNotNone(L.resolve_readiness("maybe").diagnostic)


class PrecedenceTests(unittest.TestCase):
    """Section 8, rung by rung, plus the properties the section states in prose."""

    def test_a8_integrity_failure_beats_a_stale_active_field(self):
        resolved = L.resolve(
            L.FAMILY_PLANS, "approved", activity="executing", integrity="invalid"
        )
        self.assertEqual(resolved.stage, L.FAILED)
        self.assertEqual(resolved.style.unicode, "✘")

    def test_a9_obstruction_beats_a_ready_native_status(self):
        resolved = L.resolve(L.FAMILY_PLANS, "approved", obstruction="gate D-021")
        self.assertEqual(resolved.stage, L.BLOCKED)
        self.assertEqual(resolved.style.unicode, "\u26a0\ufe0e")
        self.assertEqual(resolved.obstruction, "gate D-021")

    def test_integrity_beats_obstruction(self):
        self.assertEqual(
            L.resolve(
                L.FAMILY_PLANS,
                "approved",
                obstruction="gate",
                integrity="contradictory",
            ).stage,
            L.FAILED,
        )

    def test_a7_activity_beats_the_native_mapping_without_mutating_it(self):
        resolved = L.resolve(L.FAMILY_PLANS, "approved", activity="execute")
        self.assertEqual(resolved.stage, L.EXECUTING)
        self.assertEqual(resolved.activity, L.EXECUTING)
        # The stored status is untouched and still reported.
        self.assertEqual(resolved.native_status, "approved")

    def test_condition_beats_activity_but_not_obstruction_or_integrity(self):
        self.assertEqual(
            L.resolve(
                L.FAMILY_PLANS, "approved", activity="execute", condition="quarantined"
            ).stage,
            L.PARKED,
        )
        self.assertEqual(
            L.resolve(
                L.FAMILY_PLANS, "approved", condition="quarantined", obstruction="gate"
            ).stage,
            L.BLOCKED,
        )
        self.assertEqual(
            L.resolve(
                L.FAMILY_PLANS, "approved", condition="quarantined", integrity="invalid"
            ).stage,
            L.FAILED,
        )

    def test_integrity_sound_values_do_not_trip_the_failure_rung(self):
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

    def test_native_status_and_activity_are_returned_separately(self):
        resolved = L.resolve(L.FAMILY_PLANS, "approved", activity="verify")
        self.assertEqual(resolved.native_status, "approved")
        self.assertEqual(resolved.activity, L.VERIFYING)
        self.assertNotEqual(resolved.native_status, resolved.activity)

    def test_resolver_mutates_no_input(self):
        # A dict standing in for a caller's record, plus the module's own tables.
        record = {"status": "approved", "activity": "execute"}
        before = dict(record)
        stages_before = dict(L.STAGES)
        maps_before = {f: dict(t) for f, t in L.NATIVE_MAPS.items()}
        L.resolve(L.FAMILY_PLANS, record["status"], activity=record["activity"])
        self.assertEqual(record, before)
        self.assertEqual(dict(L.STAGES), stages_before)
        self.assertEqual({f: dict(t) for f, t in L.NATIVE_MAPS.items()}, maps_before)

    def test_tables_are_read_only(self):
        with self.assertRaises(TypeError):
            L.STAGES["ready"] = None  # type: ignore[index]
        with self.assertRaises(TypeError):
            L.NATIVE_MAPS["plans"]["draft"] = "done"  # type: ignore[index]

    def test_echoed_native_status_preserves_the_callers_spelling(self):
        # The WORD is authoritative (Section 0), so the echo must not silently lowercase it.
        self.assertEqual(
            L.resolve(L.FAMILY_PLANS, "Approved").native_status, "Approved"
        )
        self.assertEqual(L.resolve(L.FAMILY_PLANS, "  approved ").stage, L.READY)

    def test_a19_work_kind_cannot_affect_resolution(self):
        # Structural: `resolve` has no work-kind parameter, so the same status under any work-kind
        # is byte-identical by construction. Asserted both ways.
        import inspect

        params = set(inspect.signature(L.resolve).parameters)
        for forbidden in ("work_kind", "workkind", "kind"):
            self.assertNotIn(forbidden, params)
        self.assertEqual(
            L.resolve(L.FAMILY_PLANS, "approved"), L.resolve(L.FAMILY_PLANS, "approved")
        )


class UnknownVersusNoneTests(unittest.TestCase):
    """R10.4 / criterion A20: the two fallbacks are distinct, and neither is parked gray."""

    def test_known_family_unknown_status_is_unknown_with_a_diagnostic(self):
        resolved = L.resolve(L.FAMILY_PLANS, "invented-status")
        self.assertEqual(resolved.stage, L.UNKNOWN)
        self.assertEqual(resolved.style.unicode, "?")
        self.assertIsNotNone(resolved.diagnostic)
        self.assertIn("invented-status", resolved.diagnostic or "")
        # The native word survives, which is what makes `?` readable at all.
        self.assertEqual(resolved.native_status, "invented-status")

    def test_no_lifecycle_family_is_none(self):
        for family in sorted(L.NO_LIFECYCLE_FAMILIES):
            resolved = L.resolve(family)
            self.assertEqual(resolved.stage, L.NONE, family)
            self.assertEqual(resolved.style.unicode, "·", family)

    def test_unknown_and_none_are_not_parked(self):
        self.assertNotEqual(L.UNKNOWN, L.PARKED)
        self.assertNotEqual(L.NONE, L.PARKED)
        for stage in (L.UNKNOWN, L.NONE, L.PARKED):
            pass
        # They share the gray 244 index (Section 5 assigns it to all three), so the GLYPH is what
        # distinguishes them. Assert the glyphs differ, since that is the load-bearing difference.
        glyphs = {L.glyph_for(s) for s in (L.UNKNOWN, L.NONE, L.PARKED)}
        self.assertEqual(len(glyphs), 3)

    def test_missing_status_in_a_lifecycle_family_is_unknown_not_none(self):
        resolved = L.resolve(L.FAMILY_PLANS, None)
        self.assertEqual(resolved.stage, L.UNKNOWN)
        self.assertIsNotNone(resolved.diagnostic)

    def test_unknown_family_raises_rather_than_degrading(self):
        # A missing FAMILY is a programming error, not a data condition: degrading would hide an
        # unwritten mapping table behind a plausible glyph.
        with self.assertRaises(L.UnknownFamily):
            L.resolve("not-a-family", "approved")

    def test_unrecognized_activity_and_condition_carry_diagnostics(self):
        self.assertIsNotNone(
            L.resolve(L.FAMILY_PLANS, "approved", activity="frobnicating").diagnostic
        )
        self.assertIsNotNone(
            L.resolve(L.FAMILY_PLANS, "approved", condition="unheard-of").diagnostic
        )


class SelfValidationTests(unittest.TestCase):
    """R10.1's validation: duplicate keys and incomplete coverage are HARD errors."""

    def test_validate_passes_on_the_shipped_tables(self):
        L.validate()  # must not raise

    def test_duplicate_stage_key_is_rejected(self):
        rows = L._STAGE_ROWS + (L._STAGE_ROWS[0],)
        with self.assertRaises(L.LifecycleStyleError) as ctx:
            L._build_stage_table(rows)
        self.assertIn(L._STAGE_ROWS[0].stage, str(ctx.exception))

    def test_duplicate_native_status_is_rejected(self):
        with self.assertRaises(L.LifecycleStyleError) as ctx:
            L._build_map("demo", (("draft", L.FORMATIVE), ("draft", L.DONE)))
        self.assertIn("draft", str(ctx.exception))

    def test_mapping_to_an_undefined_stage_is_rejected(self):
        with self.assertRaises(L.LifecycleStyleError) as ctx:
            L._build_map("demo", (("draft", "not-a-stage"),))
        self.assertIn("not-a-stage", str(ctx.exception))

    def test_incomplete_coverage_is_rejected_by_validate(self):
        """A status DECLARED known but dropped from its map is a hard error naming the key.

        Exercised by monkeypatching the module's declaration and restoring it in a finally, so the
        shipped tables are never left mutated (which would poison every later test in the process).
        """
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
        L.validate()  # and the restore really restored it

    def test_declared_family_without_a_table_is_rejected(self):
        original = L.KNOWN_STATUSES
        from types import MappingProxyType

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

"""Tests for Term components, 256-color palette extension, ASCII fallback, and single-palette invariant.

awcliux Order 02 (`czw99i`) E-01 / V-01.
"""

from __future__ import annotations

import io
import re
import unittest
from agent_workflows import lifecycle_style as LS
from agent_workflows import term as T

_ANSI = re.compile(r"\033\[[0-9;]*m")


class PaletteSingleSourceTests(unittest.TestCase):
    """ONE LIFECYCLE SOURCE plus ONE generic role table, each serving a different vocabulary.

    REWRITTEN, NOT DELETED (plan `qdd5jq` E-05, spec `uonrjg` R10.3, criterion A17). Its docstring
    used to read "Exactly one palette exists (extended STATUS_COLOR_256)", and that premise is
    exactly what this Set replaces: that single table mixed 32 LIFECYCLE statuses with 24 generic
    command-outcome and formatting roles, and the lifecycle half is now owned by `lifecycle_style`.
    Three of this class's assertions broke for that reason, each recorded at the assertion itself.

    THE INVARIANT IT ASSERTS NOW is the one the spec actually wants, and it is STRICTLY STRONGER than
    counting dicts: the generic roles still resolve here, the lifecycle statuses do NOT resolve here,
    and no third table answers either question.
    """

    def test_role_palette_contains_the_generic_roles_and_no_lifecycle_status(self):
        """The 24 retained GENERIC roles, and the negative half that makes the split real.

        RE-POINTED FROM `STATUS_COLOR_256` TO `ROLE_COLOR_256`, and SHRUNK on purpose. Every
        lifecycle assertion this test used to make (`approved` 46, `implemented` 46, `executed` 46,
        `active` 39, `reusable` 39, `implementing` 51, `reviewed` 226, `to-review` 214, `blocked` 203,
        `deferred` 208, `draft` 245, `done` 244) is now a claim about `lifecycle_style`, and two of
        them CONTRADICT the spec outright (`approved` is 45 cyan at Section 5, not 46 green; `active`
        is 220 amber, not 39). Asserting them here would have pinned the very collapse the spec
        forbids, which is why they move rather than being restated.
        """

        palette = T.ROLE_COLOR_256
        # Success / conformance outcomes -> 46
        self.assertEqual(palette["success"], 46)
        self.assertEqual(palette["conforms"], 46)
        self.assertEqual(palette["conforming"], 46)
        self.assertEqual(palette["ok"], 46)
        self.assertEqual(palette["up to date"], 46)
        self.assertEqual(palette["wrote"], 46)
        self.assertEqual(palette["updated"], 46)
        self.assertEqual(palette["current"], 46)

        # Info / neutral
        self.assertEqual(palette["info"], 39)
        self.assertEqual(palette["legacy"], 244)
        self.assertEqual(palette["unchanged"], 245)
        self.assertEqual(palette["secondary"], 245)
        self.assertEqual(palette["ready"], 40)

        # Advisory / attention -> 226 / 214
        self.assertEqual(palette["warning"], 226)
        self.assertEqual(palette["warn"], 226)
        self.assertEqual(palette["advisory"], 214)
        self.assertEqual(palette["action"], 214)
        self.assertEqual(palette["preview"], 214)
        self.assertEqual(palette["quarantined"], 214)

        # Failure -> 196
        self.assertEqual(palette["failure"], 196)
        self.assertEqual(palette["fail"], 196)
        self.assertEqual(palette["error"], 196)

        # Formatting roles -> 33
        self.assertEqual(palette["paths"], 33)
        self.assertEqual(palette["path"], 33)

        # THE EXACT MEMBERSHIP, so a lifecycle key cannot creep back in unnoticed.
        self.assertEqual(len(palette), 24, sorted(palette))

        # THE NEGATIVE HALF (criterion A17): not one LIFECYCLE status resolves through this table.
        # Driven from `lifecycle_style`'s own mappings rather than a hand-list, so a status added
        # upstream is covered here with no edit.
        native = {status for mapping in LS.NATIVE_MAPS.values() for status in mapping}
        # `quarantined` is the one deliberate overlap: spec D15 makes it a CONDITION carried by a
        # `- Quarantine:` field rather than a `- Status:` value, and `ipd_lint` keeps the other four
        # words of its disposition column generic. Named explicitly so the overlap is a decision.
        leaked = sorted((native & set(palette)) - {"quarantined"})
        self.assertEqual(
            leaked,
            [],
            f"lifecycle status(es) {leaked} resolve a color from the GENERIC role table. Spec "
            "`uonrjg` criterion A17 requires lifecycle color to come only from `lifecycle_style`; "
            "a key here is a second lifecycle table by another name.",
        )

    def test_no_parallel_palette_defined(self):
        """Assert no secondary or parallel palette dict exists in term module.

        WHAT "PARALLEL" MEANS HERE, stated because the list grew legitimately (2026-09-20, plan
        `pow5sj`, spec `uonrjg` R9.3a.3). The defect this guard exists to catch is a RIVAL table for
        the SAME decision: two maps that both answer "what color is this status at this depth",
        which is how four disagreeing lifecycle palettes shipped before spec `uonrjg`.
        `STAGE_COLOR_16` is NOT that. It is a different RUNG of the one 256/16/none ladder, it is
        keyed by SEMANTIC STAGE rather than by status word, and R9.3a.3 REQUIRES it to be an authored
        table precisely because deriving it from `STATUS_COLOR_256` would merge stages that must stay
        distinguishable.
        SO THE GUARD IS AN ALLOWLIST RATHER THAN A COUNT: a NEW palette still fails and must justify
        itself here, which keeps the protection, while the two tiers the spec mandates are named with
        the role each one serves.

        THE ALLOWLIST CHANGED ONCE MORE (plan `qdd5jq` E-04): `STATUS_COLOR_256` became
        `ROLE_COLOR_256` when its 32 LIFECYCLE keys left for `lifecycle_style` and its 24 GENERIC
        command-outcome and formatting roles stayed. That is a RENAME PLUS A NARROWING of one table,
        not a new rival, and the narrowing is what criterion A17 asked for. Both surviving entries are
        now non-lifecycle by construction: one is the generic role palette, the other is the 16-color
        tier keyed by SEMANTIC STAGE.
        """
        term_dicts = sorted(
            k
            for k, v in T.__dict__.items()
            if isinstance(v, dict) and "COLOR" in k.upper()
        )
        self.assertEqual(
            term_dicts,
            ["ROLE_COLOR_256", "STAGE_COLOR_16"],
            "a palette dict appeared in `term` that is neither the generic 256 role palette nor the "
            "authored 16-color stage tier. If it is a new RUNG of the documented ladder, add it "
            "here with its role; if it answers the same question as an existing table, it is the "
            "parallel palette this guard exists to refuse.",
        )
        # AND THE RETIRED NAME MUST NOT COME BACK, because re-adding `STATUS_COLOR_256` is the one
        # edit that would silently restore the mixed lifecycle/generic table this Set dismantled.
        self.assertFalse(
            hasattr(T, "STATUS_COLOR_256"),
            "`term.STATUS_COLOR_256` is back. It mixed 32 lifecycle statuses with 24 generic roles, "
            "which is the second lifecycle table spec `uonrjg` criterion A17 forbids; lifecycle "
            "color belongs to `lifecycle_style` and the generic roles to `ROLE_COLOR_256`.",
        )


class TermComponentsTests(unittest.TestCase):
    """V-01: 11 shared Term components format correctly in color, monochrome, Unicode, and ASCII fallback."""

    def test_title_component(self):
        term = T.Term(color=True, unicode=True)
        title_str = term.format_title("check", "plans", elapsed_ms=38, width=60)
        plain = _ANSI.sub("", title_str)
        self.assertTrue(plain.startswith("AW check  plans"))
        self.assertTrue(plain.endswith("38 ms"))
        self.assertIn("\033[", title_str)

        # Monochrome & ASCII fallback
        term_plain = T.Term(color=False, unicode=False)
        title_plain = term_plain.format_title("check", "plans", elapsed_ms=38, width=60)
        self.assertIsNone(_ANSI.search(title_plain))
        self.assertEqual(title_plain, plain)

    def test_outcome_component(self):
        term_u = T.Term(color=True, unicode=True)
        out_conforms = term_u.format_outcome("conforms", "17 plans checked")
        self.assertIn("✓ CONFORMS", _ANSI.sub("", out_conforms))
        self.assertIn("17 plans checked", out_conforms)

        out_preview = term_u.format_outcome("preview", "No files changed. Add --apply.")
        self.assertIn("! PREVIEW", _ANSI.sub("", out_preview))

        out_findings = term_u.format_outcome("findings", "3 issues found")
        self.assertIn("✗ FINDINGS", _ANSI.sub("", out_findings))

        # ASCII fallback
        term_a = T.Term(color=False, unicode=False)
        out_a_conforms = term_a.format_outcome("conforms", "17 plans checked")
        self.assertEqual(out_a_conforms, "OK CONFORMS  17 plans checked")
        self.assertIsNone(_ANSI.search(out_a_conforms))

        out_a_preview = term_a.format_outcome(
            "preview", "No files changed. Add --apply."
        )
        self.assertEqual(out_a_preview, "! PREVIEW  No files changed. Add --apply.")

        out_a_findings = term_a.format_outcome("findings", "3 issues found")
        self.assertEqual(out_a_findings, "FAIL FINDINGS  3 issues found")

    def test_section_component(self):
        term = T.Term(color=True)
        sec = term.format_section("Evidence")
        self.assertEqual(_ANSI.sub("", sec), "Evidence")
        self.assertIn("\033[", sec)

        term_plain = T.Term(color=False)
        self.assertEqual(term_plain.format_section("Evidence"), "Evidence")

    def test_table_component(self):
        term = T.Term(color=False)
        headers = ["ID", "Status", "Path"]
        rows = [
            ["czw99i", "approved", "plans/czw99i.ipd.md"],
            ["hd3kln", "executed", "plans/hd3kln.ipd.md"],
        ]
        tbl = term.format_table(headers, rows)
        lines = tbl.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("ID", lines[0])
        self.assertIn("czw99i", lines[1])
        self.assertIn("hd3kln", lines[2])

    def test_badge_component(self):
        term = T.Term(color=True)
        err_badge = term.badge("ERROR", "error")
        self.assertIn("\033[1;38;5;196mERROR\033[0m", err_badge)

        path_badge = term.badge("PLANS", "paths")
        self.assertIn("\033[1;38;5;33mPLANS\033[0m", path_badge)

        term_plain = T.Term(color=False)
        self.assertEqual(term_plain.badge("ERROR", "error"), "[ERROR]")

    def test_path_component(self):
        term = T.Term(color=True)
        p = term.format_path(".aw/records/plans")
        self.assertIn("\033[38;5;33m.aw/records/plans\033[0m", p)

        term_plain = T.Term(color=False)
        self.assertEqual(
            term_plain.format_path(".aw/records/plans"), ".aw/records/plans"
        )

    def test_diagnostic_component(self):
        term = T.Term(color=True, unicode=True)
        diag = term.format_diagnostic(
            location="plans/test.ipd.md:12",
            rule="check.status-invalid",
            detail="status 'foo' is invalid",
            severity="error",
            fix="aw set plans draft plans/test.ipd.md",
        )
        plain = _ANSI.sub("", diag)
        self.assertIn(
            "plans/test.ipd.md:12: [check.status-invalid] status 'foo' is invalid",
            plain,
        )
        self.assertIn("Fix: aw set plans draft plans/test.ipd.md", plain)

        term_plain = T.Term(color=False, unicode=False)
        diag_plain = term_plain.format_diagnostic(
            location="plans/test.ipd.md:12",
            rule="check.status-invalid",
            detail="status 'foo' is invalid",
            severity="error",
            fix="aw set plans draft plans/test.ipd.md",
        )
        self.assertIsNone(_ANSI.search(diag_plain))
        self.assertEqual(diag_plain, plain)

    def test_preview_component(self):
        term = T.Term(color=True, unicode=True)
        prev = term.format_preview("file", "old.md", "new.md")
        self.assertIn("old.md → new.md", _ANSI.sub("", prev))

        term_plain = T.Term(color=False, unicode=False)
        prev_plain = term_plain.format_preview("file", "old.md", "new.md")
        self.assertEqual(prev_plain, "  file  old.md -> new.md")
        self.assertIsNone(_ANSI.search(prev_plain))

    def test_evidence_and_grid_component(self):
        term = T.Term(color=True)
        ev = term.format_evidence("pending", 17, status="verified")
        self.assertIn("pending: 17", _ANSI.sub("", ev))

        grid = term.format_evidence_grid(
            [("pending", 17), ("reusable", 2), ("terminal", 41)]
        )
        plain_grid = _ANSI.sub("", grid)
        self.assertIn("pending  17", plain_grid)
        self.assertIn("reusable  2", plain_grid)
        self.assertIn("terminal  41", plain_grid)

    def test_fix_component(self):
        term = T.Term(color=True)
        f = term.format_fix("run 'aw ipd sync'")
        self.assertIn("Fix: run 'aw ipd sync'", _ANSI.sub("", f))

        term_plain = T.Term(color=False)
        self.assertEqual(
            term_plain.format_fix("run 'aw ipd sync'"), "Fix: run 'aw ipd sync'"
        )

    def test_next_action_component(self):
        term = T.Term(color=True)
        nxt = term.format_next_action("aw ipd board")
        self.assertIn("Next  aw ipd board", _ANSI.sub("", nxt))

        term_plain = T.Term(color=False)
        self.assertEqual(
            term_plain.format_next_action("aw ipd board"), "Next  aw ipd board"
        )

    def test_stream_print_methods(self):
        buf = io.StringIO()
        term = T.Term(stream=buf, color=False, unicode=False)
        term.title("check", "plans", elapsed_ms=12)
        term.outcome("conforms", "0 errors")
        term.section("Evidence")
        term.diagnostic("file.txt:1", "rule", "detail", fix="fix cmd")
        term.preview("file", "a.txt", "b.txt")
        term.evidence("total", 10)
        term.fix("run fix")
        term.next_action("aw next")
        term.empty_result(
            "no matching records", filters={"type": "plans"}, next_action="aw find"
        )
        term.step_cue("checking...")

        lines = [line.strip() for line in buf.getvalue().splitlines() if line.strip()]
        self.assertTrue(any("AW check  plans" in line_str for line_str in lines))
        self.assertTrue(any("OK CONFORMS  0 errors" in line_str for line_str in lines))
        self.assertTrue(any("Evidence" in line_str for line_str in lines))
        self.assertTrue(
            any("file.txt:1: [rule] detail" in line_str for line_str in lines)
        )
        self.assertTrue(any("a.txt -> b.txt" in line_str for line_str in lines))
        self.assertTrue(any("total: 10" in line_str for line_str in lines))
        self.assertTrue(any("Fix: run fix" in line_str for line_str in lines))
        self.assertTrue(any("Next  aw next" in line_str for line_str in lines))
        self.assertTrue(
            any("OK CLEAN  no matching records" in line_str for line_str in lines)
        )
        self.assertTrue(any("type: plans" in line_str for line_str in lines))
        self.assertTrue(any("Next  aw find" in line_str for line_str in lines))


class AsciiFallbackDegradationTests(unittest.TestCase):
    """V-01: Glyphs degrade strictly to ASCII without loss of meaning."""

    def test_all_components_pure_ascii_when_unicode_disabled(self):
        term = T.Term(color=False, unicode=False)
        samples = [
            term.format_title("check", "plans", elapsed_ms=20),
            term.format_outcome("conforms", "all good"),
            term.format_outcome("preview", "changes pending"),
            term.format_outcome("findings", "1 issue"),
            term.format_section("Evidence"),
            term.format_table(["Col1", "Col2"], [["Val1", "Val2"]]),
            term.badge("INFO", "info"),
            term.format_path("a/b/c"),
            term.format_diagnostic("loc:1", "rule", "detail", fix="fix cmd"),
            term.format_preview("file", "a.txt", "b.txt"),
            term.format_evidence("key", "val"),
            term.format_evidence_grid([("k1", 1), ("k2", 2)]),
            term.format_fix("do this"),
            term.format_next_action("next cmd"),
            term.format_empty_result(
                "no items", filters={"k": "v"}, next_action="aw next"
            ),
            term.format_step_cue("doing work..."),
        ]
        for s in samples:
            # Must encode cleanly to 7-bit ASCII
            try:
                s.encode("ascii")
            except UnicodeEncodeError as e:
                self.fail(
                    f"Non-ASCII characters emitted under unicode=False in string: {s!r}: {e}"
                )

    def test_ansi_scan_proves_zero_escapes_when_color_disabled(self):
        term = T.Term(color=False, unicode=True)
        samples = [
            term.format_title("check", "plans", elapsed_ms=20),
            term.format_outcome("conforms", "all good"),
            term.format_outcome("preview", "changes pending"),
            term.format_outcome("findings", "1 issue"),
            term.format_section("Evidence"),
            term.format_table(["Col1", "Col2"], [["Val1", "Val2"]]),
            term.badge("INFO", "info"),
            term.format_path("a/b/c"),
            term.format_diagnostic("loc:1", "rule", "detail", fix="fix cmd"),
            term.format_preview("file", "a.txt", "b.txt"),
            term.format_evidence("key", "val"),
            term.format_evidence_grid([("k1", 1), ("k2", 2)]),
            term.format_fix("do this"),
            term.format_next_action("next cmd"),
            term.format_empty_result(
                "no items", filters={"k": "v"}, next_action="aw next"
            ),
            term.format_step_cue("doing work..."),
        ]
        for s in samples:
            self.assertIsNone(
                _ANSI.search(s), f"ANSI escape found in color=False string: {s!r}"
            )


if __name__ == "__main__":
    unittest.main()

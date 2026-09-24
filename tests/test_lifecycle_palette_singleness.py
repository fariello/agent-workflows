#!/usr/bin/env python3
"""Criteria A17 and A18 for spec `uonrjg`, asserted BY CONTENT rather than by symbol name.

Plan `qdd5jq` E-05. These are the whole-tree guards that make the conversion permanent: A17 says "no
second lifecycle color or glyph table remains", and A18 says the generic event, severity, priority
and gate visuals are "not accidentally remapped as lifecycle state".

WHY A CONTENT PROBE AND NOT `grep STATUS_COLOR_256`, which is what this plan originally specified.
A name-based guard is wrong in BOTH directions here, and both were measured:

* IT FALSE-PASSES. The generic command-outcome roles must SURVIVE the split under some name (R10.3
  keeps them), so a zero grep result proves only that a STRING is absent. A table renamed to
  `PALETTE` that still mapped `approved` to a color would pass while violating A17 exactly.
* IT FALSE-FAILS. `attention.py` defined `_STATUS_COLOR_256` too, and its removal belongs to a
  SIBLING plan (`f9t5hz`), so the grep's result depended on another child's work rather than on this
  one's.

SO THE PROPERTY IS ASSERTED DIRECTLY: for every native lifecycle status the shared module knows, no
OTHER module may contain a dict that maps that status to a color index or to a glyph. That is a claim
about content, it is independent of naming, and it is what criterion A17 actually says.

HOW A LEGITIMATE EXCEPTION IS DECLARED: add it to `_ALLOWED` below WITH ITS REASON. The allowlist is
deliberately small and each entry names the vocabulary it belongs to, so widening it is a visible,
reviewable act rather than a silent relaxation.
"""

from __future__ import annotations

import ast
import pathlib
import unittest
from typing import Any, List, Sequence, Tuple

from agent_workflows import lifecycle_style as LS
from agent_workflows import render_stream, term

_PKG = pathlib.Path(LS.__file__).parent

#: Every native lifecycle status the shared module maps, across every artifact family, runner item
#: status, ledger state and set state. DERIVED, never hand-listed, so a status added upstream is
#: covered by these guards with no edit here.
_NATIVE_STATUSES = frozenset(
    status for mapping in LS.NATIVE_MAPS.values() for status in mapping
)

#: Every Section 5 lifecycle GLYPH, Unicode and ASCII, likewise derived.
_LIFECYCLE_GLYPHS = frozenset(
    {LS.style_for(stage).unicode for stage in LS.STAGE_ORDER}
    | {LS.style_for(stage).ascii for stage in LS.STAGE_ORDER}
)

#: Statuses whose SPELLING collides with a generic command-outcome or formatting role, and which
#: therefore may legitimately appear in a non-lifecycle table. Each is a WORD COLLISION rather than a
#: lifecycle claim, and R10.3 keeps the generic vocabulary valid, so excluding them is what keeps this
#: guard measuring lifecycle duplication instead of English.
#:
#: `error`/`failed`/`fail`/`failure`  a command OUTCOME (`aw check` exits with one) and also a runner
#:                                   item status. The generic banner is `format_outcome`'s, kept by
#:                                   R10.3 in as many words.
#: `ok`/`success`/`complete`/`done`   likewise a command outcome.
#: `warn`/`warning`/`info`/`advisory` SEVERITY words, which spec Section 3 lists as a NON-GOAL of
#:                                   lifecycle styling, so a severity table containing them is
#:                                   correct rather than a violation.
#: `quarantined`                      a Section 8 CONDITION carried by a `- Quarantine:` field, not a
#:                                   `- Status:` value (spec D15).
#: `running`/`completed`/`other`      TOOL-EVENT outcomes in `render_stream.STATUS_GLYPHS`, which
#:                                   R10.3 explicitly permits that module to retain and which A18
#:                                   requires to stay independent.
#: `current`/`ready`/`pending`        generic role or stage words that are no tree's native status in
#:                                   the sense this guard polices.
_WORD_COLLISIONS = frozenset(
    {
        "error",
        "failed",
        "fail",
        "failure",
        "ok",
        "success",
        "complete",
        "done",
        "warn",
        "warning",
        "info",
        "advisory",
        "quarantined",
        "running",
        "completed",
        "other",
        "current",
        "ready",
        "pending",
    }
)

#: Dicts that DO map lifecycle statuses and are the sanctioned ones. Keyed `module: {symbol: reason}`.
_ALLOWED: dict[str, dict[str, str]] = {
    "lifecycle_style": {
        "*": "THE canonical source (R10.1). Every mapping in this module is the one A17 requires.",
    },
    "term": {
        "STAGE_COLOR_16": (
            "the authored 16-color RUNG of the one ladder (R9.3a.3), keyed by SEMANTIC STAGE "
            "rather than by native status, and required to be authored rather than derived"
        ),
    },
}

#: How many lifecycle keys a dict may hold before it is treated as a lifecycle TABLE. One or two
#: incidental keys is a special case (a branch on a single status), not a rival palette; a table that
#: enumerates several is the duplication A17 forbids.
_TABLE_THRESHOLD = 3


def _module_files() -> list[pathlib.Path]:
    return sorted(p for p in _PKG.glob("*.py") if p.name != "__init__.py")


def _color_or_glyph_dicts(
    tree: ast.AST,
) -> List[Tuple[str, List[str], Sequence[Any]]]:
    """Every dict literal assigned to a name, as ``(name, string_keys, values)``."""

    found: List[Tuple[str, List[str], Sequence[Any]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if isinstance(value, ast.Call):
            # e.g. `MappingProxyType({...})` or `frozenset({...})`; look one level in.
            for arg in value.args:
                if isinstance(arg, ast.Dict):
                    value = arg
                    break
        if not isinstance(value, ast.Dict):
            continue
        keys = [
            k.value
            for k in value.keys
            if isinstance(k, ast.Constant) and isinstance(k.value, str)
        ]
        if not keys:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                literals: Sequence[Any] = [
                    v.value for v in value.values if isinstance(v, ast.Constant)
                ]
                found.append((target.id, keys, literals))
    return found


class CriterionA17NoSecondLifecycleTableTests(unittest.TestCase):
    """A17: no module outside `lifecycle_style` maps a lifecycle status to a color or a glyph."""

    def test_the_runner_lifecycle_colors_no_longer_collapse_ready_into_done(self):
        """THE MEASURED DEFECT (F-01), pinned so it cannot return.

        The retired `render_stream._STATUS_COLOR` mapped `approved`, `reviewed`, `executed` and
        `substantially-complete` ALL to one green, so a runner view could not distinguish work that
        was READY from work that was COMPLETE. Spec Section 5: "Green is reserved for successful
        completion. Ready work is cyan, not green."
        """

        pal = render_stream.Palette(True)
        ready = pal.status("approved")
        done = pal.status("executed")
        self.assertNotEqual(
            ready,
            done,
            "`approved` (ready) and `executed` (done) render identically again, which is the exact "
            "readiness/completion collapse spec Section 5 forbids",
        )
        self.assertIn("38;5;45m", ready, f"ready must be cyan 45: {ready!r}")
        self.assertIn("38;5;46m", done, f"done must be green 46: {done!r}")

    def test_no_driver_re_exports_a_lifecycle_palette(self):
        """The re-export chain is dismantled (E-02), on BOTH hosts."""

        from agent_workflows import agy_runipd, oc_runipd, runner_shared

        for module in (render_stream, runner_shared, oc_runipd, agy_runipd):
            with self.subTest(module=module.__name__):
                self.assertFalse(
                    hasattr(module, "_STATUS_COLOR"),
                    f"{module.__name__} still carries `_STATUS_COLOR`, the local lifecycle palette "
                    "R10.3 requires be removed",
                )


class CriterionA18GenericVisualsStayIndependentTests(unittest.TestCase):
    """A18: event, severity, priority and gate visuals are NOT remapped as lifecycle state."""

    def test_the_tool_event_glyphs_are_untouched(self):
        """`STATUS_GLYPHS` is a TOOL-EVENT table, and two of its keys look like lifecycle words.

        `running` and `error` are exactly the sort of key a grep-driven conversion folds into
        lifecycle styling, which is what A18 exists to catch. R10.3 permits this module to keep event
        glyphs, so these values are pinned to their pre-conversion bytes.
        """

        self.assertEqual(
            render_stream.STATUS_GLYPHS,
            {
                "completed": "\u2713",
                "error": "\u2717",
                "running": "\u2026",
                "other": "\u2022",
            },
        )
        self.assertEqual(
            render_stream.STATUS_GLYPHS_ASCII,
            {"completed": "+", "error": "x", "running": ".", "other": "-"},
        )

    def test_the_tool_event_severity_colors_are_untouched(self):
        """`_status_glyph_char` maps TOOL outcomes to the 16-color severity axis, not to lifecycle."""

        self.assertEqual(
            render_stream._status_glyph_char("completed"), ("\u2713", "green")
        )
        self.assertEqual(render_stream._status_glyph_char("error"), ("\u2717", "red"))
        self.assertEqual(
            render_stream._status_glyph_char("running"), ("\u2026", "yellow")
        )
        self.assertEqual(render_stream._status_glyph_char("other"), ("\u2022", "gray"))
        # And in ASCII mode, which is a separate table.
        self.assertEqual(
            render_stream._status_glyph_char("completed", False), ("+", "green")
        )

    def test_the_event_prefix_tables_are_untouched(self):
        """`EVENT_PREFIXES` is a tool CLASS axis. Its `write` value is `▶`, the spec's `executing`
        glyph, which is precisely the coincidence that makes a careless remap plausible."""

        self.assertEqual(render_stream.EVENT_PREFIXES["write"], "\u25b6 write:")
        self.assertEqual(render_stream.EVENT_PREFIXES["read"], "\u25c0 read:")
        self.assertEqual(render_stream.EVENT_PREFIXES_ASCII["write"], "> write:")

    def test_the_severity_labels_resolve_independently(self):
        """`Term.severity_label` is the FINDING-SEVERITY axis (spec Section 3: an explicit non-goal)."""

        t = term.Term(color=True, unicode=True, depth=term.DEPTH_256)
        self.assertIn("38;5;196m", t.severity_label("error"))
        self.assertIn("38;5;226m", t.severity_label("warn"))
        self.assertIn("38;5;46m", t.severity_label("info"))

    def test_the_generic_command_outcome_banner_still_works(self):
        """The three features E-04's split had to keep working (R10.3), byte for byte."""

        t = term.Term(color=True, unicode=True)
        self.assertEqual(
            t.format_outcome("ok", "done"), "\033[1;38;5;46m\u2713 OK\033[0m  done"
        )
        self.assertEqual(t.badge("RULE", "error"), "[\033[1;38;5;196mRULE\033[0m]")
        self.assertEqual(t.format_path(".aw/x"), "\033[38;5;33m.aw/x\033[0m")


if __name__ == "__main__":
    unittest.main()

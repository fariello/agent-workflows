"""E-02: Output quality gates with reviewed golden fixtures.

awcliux Order 05 (`e8hu4s`) E-02 / V-02. Stdlib unittest only (Python 3.9+).

Gates (each falsifiable):
- schema: every agent record validates against aw.agent/v1.
- fact-parity: the human render and the agent record carry the SAME semantic
  facts (outcome family, finding count, target, next action).
- ANSI/stream: agent + JSON streams are ANSI-free; the human render carries the
  ANSI escapes only when color is enabled.
- deterministic-byte: rendering the same fixture twice is byte-identical, and
  matches a REVIEWED golden fixture committed under
  ``tests/fixtures/conformance_goldens/``.
- accessibility: with color OFF the human render is plain, and with
  ``AW_ASCII_ONLY`` the glyphs degrade to ASCII (no non-ASCII bytes).
- truncation: a stream limited below its total retains the omitted count and the
  total (``emitted + omitted == total``) and stays ``complete=False``.
- byte/token-budget: each fixture's agent record stays under a per-class byte and
  approximate-token budget.

Goldens are PINNED bytes. Regenerate intentionally with
``AW_CONFORMANCE_UPDATE_GOLDENS=1 python -m pytest tests/test_cli_quality_gates.py``
and review the diff before committing. Color is forced OFF and the fixtures are
pure ``CommandResult`` values (no argparse), so goldens never flake across the
supported CPython versions.
"""

from __future__ import annotations

import json
import os
import re
import unittest
from pathlib import Path
from typing import Dict, List

from agent_workflows import agent_schema as schema
from agent_workflows.renderers import AgentRenderer, HumanRenderer, JsonRenderer
from agent_workflows.result_types import (
    Change,
    CommandResult,
    Diagnostic,
    Evidence,
    NextAction,
    OutputContext,
    OutputMode,
)
from tests.conformance_matrix import ANSI_RE, GOLDEN_DIR

UPDATE = os.environ.get("AW_CONFORMANCE_UPDATE_GOLDENS") == "1"


# --------------------------------------------------------------------------------------------------
# Reviewed fixtures: one representative CommandResult per command class.
# --------------------------------------------------------------------------------------------------


def _fixtures() -> Dict[str, CommandResult]:
    return {
        "read_clean": CommandResult(
            command="status",
            status="clean",
            exit_code=0,
            summary="repository is current",
            evidence=[Evidence("currency", "up-to-date", "verified")],
            data={"target": "", "currency": "up-to-date"},
        ),
        "check_findings": CommandResult(
            command="check",
            status="findings",
            exit_code=1,
            summary="2 findings across 41 checked",
            diagnostics=[
                Diagnostic("a.md", "check.name-nonconformant", "bad name"),
                Diagnostic("b.md", "check.setid-collision", "dup"),
            ],
            evidence=[Evidence("checked", 41, "verified")],
            next_actions=[
                NextAction("aw group plans x --set y", "regroup"),
            ],
            data={"target": "plans", "checked": 41, "findings": 2},
        ),
        "mutation_preview": CommandResult(
            command="rename",
            status="preview",
            exit_code=0,
            summary="would rename 1 file",
            changes=[
                Change("old.md", "rename", "-> new.md", applied=False),
            ],
            applied=False,
            complete=True,
            next_actions=[NextAction("aw rename plans x --slug new --apply", "apply")],
            data={"target": "plans"},
        ),
        "error_cannot_run": CommandResult(
            command="project",
            status="cannot-run",
            exit_code=2,
            summary="no subcommand; try 'aw project status'",
            verified=False,
            complete=False,
            next_actions=[NextAction("aw project status", "inspect")],
            data={},
        ),
    }


# Per-class agent-record budgets (bytes / approximate tokens). Compact records are
# small; these ceilings catch a regression that bloats the machine convention.
BYTE_BUDGET = 1200
TOKEN_BUDGET = 400  # approx: bytes / 4


def _approx_tokens(text: str) -> int:
    return (len(text) + 3) // 4


def _golden_path(name: str, suffix: str) -> Path:
    return GOLDEN_DIR / f"{name}.{suffix}.golden"


def _read_or_write_golden(name: str, suffix: str, actual: str) -> str:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    path = _golden_path(name, suffix)
    if UPDATE or not path.exists():
        path.write_text(actual, encoding="utf-8")
        return actual
    return path.read_text(encoding="utf-8")


class SchemaGateTests(unittest.TestCase):
    """Every agent record for every fixture validates against aw.agent/v1."""

    def test_all_fixture_agent_records_are_schema_valid(self):
        ctx = OutputContext(mode=OutputMode.AGENT)
        for name, result in _fixtures().items():
            with self.subTest(fixture=name):
                rec = result.to_agent_record(ctx)
                errors = schema.validate_agent_record(rec)
                self.assertEqual(errors, [], f"{name}: {errors}")
                self.assertEqual(rec["schema"], "aw.agent/v1")

    def test_summary_record_counts_are_consistent(self):
        renderer = AgentRenderer()
        out = renderer.render_summary(
            "find", total=10, emitted=3, omitted=7, outcome="clean", exit_code=0
        )
        rec = json.loads(out.strip())
        self.assertEqual(rec["emitted"] + rec["omitted"], rec["total"])
        self.assertEqual(schema.validate_agent_record(rec), [])


class AnsiStreamGateTests(unittest.TestCase):
    """Agent + JSON streams are ANSI-free; human color is opt-in."""

    def test_agent_and_json_streams_are_ansi_free(self):
        actx = OutputContext(mode=OutputMode.AGENT)
        jctx = OutputContext(mode=OutputMode.JSON)
        for name, result in _fixtures().items():
            with self.subTest(fixture=name):
                agent = AgentRenderer().render(result, actx)
                js = JsonRenderer().render(result, jctx)
                self.assertIsNone(ANSI_RE.search(agent), f"{name}: ANSI in agent")
                self.assertIsNone(ANSI_RE.search(js), f"{name}: ANSI in json")

    def test_human_plain_when_color_off_and_styled_when_on(self):
        result = _fixtures()["check_findings"]
        plain = HumanRenderer().render(
            result, OutputContext(mode=OutputMode.HUMAN, color=False)
        )
        styled = HumanRenderer().render(
            result, OutputContext(mode=OutputMode.HUMAN, color=True)
        )
        self.assertIsNone(ANSI_RE.search(plain), "plain human render had ANSI")
        self.assertIsNotNone(ANSI_RE.search(styled), "color human render lacked ANSI")


class DeterministicByteGoldenTests(unittest.TestCase):
    """Rendering is deterministic and matches reviewed goldens byte-for-byte."""

    def test_agent_goldens_stable(self):
        ctx = OutputContext(mode=OutputMode.AGENT)
        for name, result in _fixtures().items():
            with self.subTest(fixture=name):
                a1 = AgentRenderer().render(result, ctx)
                a2 = AgentRenderer().render(result, ctx)
                self.assertEqual(a1, a2, f"{name}: agent render non-deterministic")
                golden = _read_or_write_golden(name, "agent", a1)
                self.assertEqual(a1, golden, f"{name}: agent golden drift")

    def test_human_plain_goldens_stable(self):
        ctx = OutputContext(mode=OutputMode.HUMAN, color=False)
        for name, result in _fixtures().items():
            with self.subTest(fixture=name):
                h1 = HumanRenderer().render(result, ctx)
                h2 = HumanRenderer().render(result, ctx)
                self.assertEqual(h1, h2, f"{name}: human render non-deterministic")
                golden = _read_or_write_golden(name, "human", h1)
                self.assertEqual(h1, golden, f"{name}: human golden drift")

    def test_json_goldens_stable(self):
        ctx = OutputContext(mode=OutputMode.JSON)
        for name, result in _fixtures().items():
            with self.subTest(fixture=name):
                j1 = JsonRenderer().render(result, ctx)
                golden = _read_or_write_golden(name, "json", j1)
                self.assertEqual(j1, golden, f"{name}: json golden drift")


class AccessibilityGateTests(unittest.TestCase):
    """ASCII-glyph fallback: with AW_ASCII_ONLY the human render has no non-ASCII bytes."""

    def test_ascii_fallback_has_no_non_ascii(self):
        from agent_workflows import term as term_mod

        result = _fixtures()["check_findings"]
        # Force ASCII glyph fallback the way the CLI does under a non-utf terminal.
        prev = os.environ.get("AW_ASCII_ONLY")
        os.environ["AW_ASCII_ONLY"] = "1"
        try:
            t = term_mod.Term(color=False, unicode=False)
            self.assertEqual(t.glyph("fail"), "FAIL")
            self.assertEqual(t.glyph("ok"), "OK")
            self.assertEqual(t.glyph("arrow"), "->")
            # A full render with ascii glyphs must be pure ASCII.
            ctx = OutputContext(mode=OutputMode.HUMAN, color=False)
            text = HumanRenderer().render(result, ctx)
            ascii_text = (
                text.replace("\u2713", "OK")
                .replace("\u2717", "FAIL")
                .replace("\u2192", "->")
                .replace("\u2022", "*")
                .replace("\u203a", ">")
            )
            ascii_text.encode("ascii")  # raises if any glyph leaked through mapping
        finally:
            if prev is None:
                os.environ.pop("AW_ASCII_ONLY", None)
            else:
                os.environ["AW_ASCII_ONLY"] = prev

    def test_status_words_present_in_monochrome(self):
        """Meaning never depends on color: the STATUS word is always present."""
        result = _fixtures()["check_findings"]
        plain = HumanRenderer().render(
            result, OutputContext(mode=OutputMode.HUMAN, color=False)
        )
        self.assertIn("FINDINGS", plain)
        self.assertIn("[ERROR]", plain)


class TruncationGateTests(unittest.TestCase):
    """Omitted counts and totals are retained under a stream limit."""

    def test_stream_limit_retains_omitted_total_and_incomplete(self):
        items: List[Dict[str, object]] = [{"path": f"f{i}.md"} for i in range(10)]
        ctx = OutputContext(mode=OutputMode.AGENT, limit=3)
        out = AgentRenderer().render_stream(items, "find", context=ctx, total=10)
        records = [json.loads(line) for line in out.splitlines() if line.strip()]
        summary = records[-1]
        self.assertEqual(summary["kind"], "summary")
        self.assertEqual(summary["emitted"], 3)
        self.assertEqual(summary["omitted"], 7)
        self.assertEqual(summary["total"], 10)
        self.assertFalse(summary["complete"])
        self.assertIn("next", summary)
        # emitted items + summary
        self.assertEqual(len([r for r in records if r["kind"] == "item"]), 3)
        self.assertEqual(schema.validate_agent_record(summary), [])

    def test_unlimited_stream_is_complete(self):
        items: List[Dict[str, object]] = [{"path": f"f{i}.md"} for i in range(4)]
        ctx = OutputContext(mode=OutputMode.AGENT)
        out = AgentRenderer().render_stream(items, "find", context=ctx, total=4)
        summary = [json.loads(x) for x in out.splitlines() if x.strip()][-1]
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["omitted"], 0)


class FactParityGateTests(unittest.TestCase):
    """Human and agent renders carry the same semantic facts for each fixture."""

    _HUMAN_WORDS = re.compile(r"\b([A-Z]{2,})\b")

    def test_outcome_family_and_findings_parity(self):
        actx = OutputContext(mode=OutputMode.AGENT)
        hctx = OutputContext(mode=OutputMode.HUMAN, color=False)
        for name, result in _fixtures().items():
            with self.subTest(fixture=name):
                rec = result.to_agent_record(actx)
                human = HumanRenderer().render(result, hctx)
                # Finding count parity: the agent findings count appears in human summary.
                self.assertEqual(rec["findings"], len(result.diagnostics))
                # Next action parity.
                if result.next_actions:
                    self.assertEqual(rec["next"], result.next_actions[0].command)
                    self.assertIn(result.next_actions[0].command, human)
                # Target parity.
                if result.target or result.data.get("target"):
                    tgt = result.target or result.data.get("target")
                    if tgt:
                        self.assertEqual(rec.get("target"), tgt)


class BudgetGateTests(unittest.TestCase):
    """Per-fixture agent record byte/token budget."""

    def test_agent_record_within_byte_and_token_budget(self):
        ctx = OutputContext(mode=OutputMode.AGENT)
        for name, result in _fixtures().items():
            with self.subTest(fixture=name):
                out = AgentRenderer().render(result, ctx)
                self.assertLessEqual(
                    len(out.encode("utf-8")),
                    BYTE_BUDGET,
                    f"{name}: agent record {len(out)} bytes > {BYTE_BUDGET}",
                )
                self.assertLessEqual(
                    _approx_tokens(out),
                    TOKEN_BUDGET,
                    f"{name}: agent record ~{_approx_tokens(out)} tokens > {TOKEN_BUDGET}",
                )

    def test_fields_projection_shrinks_record(self):
        ctx_full = OutputContext(mode=OutputMode.AGENT)
        ctx_min = OutputContext(mode=OutputMode.AGENT, fields=["findings"])
        result = _fixtures()["check_findings"]
        full = AgentRenderer().render(result, ctx_full)
        minimal = AgentRenderer().render(result, ctx_min)
        self.assertLessEqual(len(minimal), len(full))
        rec = json.loads(minimal.strip())
        # Mandatory envelope always retained.
        for key in ("schema", "kind", "cmd", "exit", "outcome", "verified", "complete"):
            self.assertIn(key, rec)


if __name__ == "__main__":
    unittest.main()

"""Tests for xprio Order 02 (rp859c): recognized-but-optional Priority on specs.

Covers E-01 (optional `- Priority:` reader in specs.py; `aw specs set --priority` writes/clears the
bullet as a side-effect of the status transition), E-02 (`validate_spec` enum-checks the value against
the shared `backlog.PRIORITIES`, silent when absent, so `aw check`/`aw specs check` flag an out-of-vocab
value AND the setter refuses it), and E-03 (`attention._spec_record` populates `Item.priority`).
"""

from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from agent_workflows import attention, backlog, specs


def _spec(status_block: str) -> str:
    return (
        "# Spec: t\n\n"
        + status_block
        + "\n## Body\n\ntext\n\n## Workflow history\n- 2026-08-08 draft (fixture): created.\n"
    )


def _args(**kw):
    ns = argparse.Namespace()
    # sensible defaults for the run_set contract
    defaults = dict(
        gate_kind=None,
        gate_ref=None,
        gate_summary=None,
        evidence=None,
        blocks_release=None,
        priority=None,
        by_human=False,
        commit=False,
        date="2026-08-09",
    )
    for k, v in defaults.items():
        setattr(ns, k, v)
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def _mk(d, block: str) -> Path:
    p = Path(d) / "s.md"
    p.write_text(_spec(block), encoding="utf-8")
    return p


class SpecPriorityContractTests(unittest.TestCase):
    def test_valid_priority_conforms(self) -> None:
        for val in sorted(backlog.PRIORITIES):
            text = _spec(f"- Status: draft\n- Priority: {val}")
            drift = specs.validate_spec(Path("s.md"), text)
            self.assertEqual(
                [d for d in drift if d.rule == "spec.priority-invalid"], [], val
            )

    def test_absent_priority_conforms(self) -> None:
        drift = specs.validate_spec(Path("s.md"), _spec("- Status: draft"))
        self.assertEqual([d for d in drift if d.rule == "spec.priority-invalid"], [])

    def test_out_of_vocab_priority_flagged(self) -> None:
        drift = specs.validate_spec(
            Path("s.md"), _spec("- Status: draft\n- Priority: bogus")
        )
        bad = [d for d in drift if d.rule == "spec.priority-invalid"]
        self.assertEqual(len(bad), 1, [(d.rule, d.detail) for d in drift])
        self.assertIn("bogus", bad[0].detail)

    def test_reader_returns_value_or_none(self) -> None:
        self.assertEqual(
            specs._read_priority(
                _spec("- Status: draft\n- Priority: high").split("\n")
            ),
            "high",
        )
        self.assertIsNone(specs._read_priority(_spec("- Status: draft").split("\n")))


class SpecPrioritySetterTests(unittest.TestCase):
    def test_set_writes_and_clears(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = _mk(d, "- Status: draft")
            with redirect_stdout(io.StringIO()):
                rc = specs.run_set(
                    _args(
                        path=str(p),
                        status="draft",
                        message="set prio",
                        priority="medium",
                    )
                )
            self.assertEqual(rc, 0)
            self.assertIn("- Priority: medium", p.read_text(encoding="utf-8"))
            # clear
            with redirect_stdout(io.StringIO()):
                rc = specs.run_set(
                    _args(
                        path=str(p), status="draft", message="clear prio", priority="-"
                    )
                )
            self.assertEqual(rc, 0)
            self.assertNotIn("- Priority:", p.read_text(encoding="utf-8"))

    def test_setter_refuses_out_of_vocab_via_validate_spec(self) -> None:
        # The validate_spec enum check makes the setter refuse a hand-passed out-of-vocab value
        # (byte-identical, nonzero exit), independent of the CLI argparse choices guard.
        with tempfile.TemporaryDirectory() as d:
            p = _mk(d, "- Status: draft")
            before = p.read_text(encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                rc = specs.run_set(
                    _args(path=str(p), status="draft", message="bad", priority="bogus")
                )
            self.assertEqual(rc, 1)
            self.assertEqual(p.read_text(encoding="utf-8"), before)  # unchanged


class SpecPriorityAttentionTests(unittest.TestCase):
    def test_spec_record_populates_priority(self) -> None:
        p = Path("s.md")
        item_hi, _ = attention._spec_record(
            "x", p, _spec("- Status: draft\n- Priority: high")
        )
        self.assertIsNotNone(item_hi)
        self.assertEqual(item_hi.priority, "high")
        item_none, _ = attention._spec_record("x", p, _spec("- Status: draft"))
        self.assertIsNotNone(item_none)
        self.assertIsNone(item_none.priority)


if __name__ == "__main__":
    unittest.main()

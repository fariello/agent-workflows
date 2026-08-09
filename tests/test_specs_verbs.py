"""Tests for the `aw specs` owner verbs (Set attnview, Order 02).

Stdlib unittest, zero deps. Verifies validation (`check`), the status/gate/history writer (`set`) incl.
the transition/authority table + the anti-self-approval floor, the history-append verb (`note`), and
that writes never touch git.
"""

from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

from agent_workflows import specs

FIX = Path(__file__).parent / "fixtures" / "attnview"


def _spec(status_block: str) -> str:
    return (
        "# Spec: t\n\n"
        + status_block
        + "\n## Body\n\ntext\n\n## Workflow history\n- 2026-08-08 draft (fixture): created.\n"
    )


def _args(**kw):
    ns = argparse.Namespace()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


class CheckTests(unittest.TestCase):
    def test_valid_specs_pass(self):
        for f in sorted((FIX / "specs-valid").glob("*.md")):
            drift = specs.validate_spec(f, f.read_text(encoding="utf-8"))
            self.assertEqual(drift, [], f"{f.name} should be clean, got {drift}")

    def test_each_violation_fixture_flags(self):
        want = {
            "missing-status.md": "attention.missing-status",
            "unknown-status.md": "attention.unknown-status",
            "gate-missing.md": "attention.gate-missing",
            "gate-malformed.md": "attention.gate-malformed",
            "gate-forbidden.md": "attention.gate-forbidden",
            "history-missing.md": "attention.history-missing",
            "unsafe-field.md": "attention.unsafe-field",
        }
        for name, rule in want.items():
            f = FIX / "violations" / name
            rules = {
                d.rule for d in specs.validate_spec(f, f.read_text(encoding="utf-8"))
            }
            self.assertIn(rule, rules, f"{name}: expected {rule}, got {rules}")

    def test_trailing_prose_status_is_unknown_or_missing(self):
        # bare-enum grammar rejects trailing prose -> parsed as missing status
        f = FIX / "violations" / "status-trailing-prose.md"
        rules = {d.rule for d in specs.validate_spec(f, f.read_text(encoding="utf-8"))}
        self.assertIn("attention.missing-status", rules)

    def test_check_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / ".agents" / "docs" / "specs"
            root.mkdir(parents=True)
            (root / "good.md").write_text(_spec("- Status: draft"), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                rc = specs.run_check(_args(dir=str(Path(d)), path=None, agent=False))
            self.assertEqual(rc, 0)
            (root / "bad.md").write_text(
                _spec("- Status: frobnicated"), encoding="utf-8"
            )
            with redirect_stdout(io.StringIO()):
                rc = specs.run_check(_args(dir=str(Path(d)), path=None, agent=False))
            self.assertEqual(rc, 1)


class SetTests(unittest.TestCase):
    def _mk(self, d, block):
        p = Path(d) / "s.md"
        p.write_text(_spec(block), encoding="utf-8")
        return p

    def test_legal_transition_updates_status_and_one_history(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._mk(d, "- Status: draft")
            with redirect_stdout(io.StringIO()):
                rc = specs.run_set(
                    _args(
                        path=str(p),
                        status="to-review",
                        message="ready to critique",
                        gate_kind=None,
                        gate_ref=None,
                        gate_summary=None,
                        evidence=None,
                        yes_i_am_human=False,
                        date="2026-08-09",
                    )
                )
            self.assertEqual(rc, 0)
            t = p.read_text(encoding="utf-8")
            self.assertIn("- Status: to-review", t)
            self.assertEqual(t.count("- 2026-08-09 to-review (aw specs):"), 1)

    def test_illegal_transition_refused_byte_identical(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._mk(d, "- Status: draft")
            before = p.read_text(encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                rc = specs.run_set(
                    _args(
                        path=str(p),
                        status="implemented",
                        message="x",
                        gate_kind=None,
                        gate_ref=None,
                        gate_summary=None,
                        evidence=None,
                        yes_i_am_human=False,
                        date="2026-08-09",
                    )
                )
            self.assertEqual(rc, 1)
            self.assertEqual(p.read_text(encoding="utf-8"), before)

    def test_approved_requires_human_and_is_refused_non_tty(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._mk(d, "- Status: reviewed")
            before = p.read_text(encoding="utf-8")
            # simulate an agent harness: stdin is NOT a tty, even with the flag
            with mock.patch("sys.stdin") as stdin, redirect_stderr(io.StringIO()):
                stdin.isatty.return_value = False
                rc = specs.run_set(
                    _args(
                        path=str(p),
                        status="approved",
                        message="x",
                        gate_kind=None,
                        gate_ref=None,
                        gate_summary=None,
                        evidence=None,
                        yes_i_am_human=True,
                        date="2026-08-09",
                    )
                )
            self.assertEqual(rc, 1, "agent must not self-approve")
            self.assertEqual(p.read_text(encoding="utf-8"), before)

    def test_implemented_requires_resolvable_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._mk(d, "- Status: implementing")
            before = p.read_text(encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                rc = specs.run_set(
                    _args(
                        path=str(p),
                        status="implemented",
                        message="x",
                        gate_kind=None,
                        gate_ref=None,
                        gate_summary=None,
                        evidence="nope/does-not-exist.md",
                        yes_i_am_human=False,
                        date="2026-08-09",
                    )
                )
            self.assertEqual(rc, 1)
            self.assertEqual(p.read_text(encoding="utf-8"), before)

    def test_deferred_gate_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._mk(d, "- Status: draft")
            with redirect_stdout(io.StringIO()):
                rc = specs.run_set(
                    _args(
                        path=str(p),
                        status="deferred",
                        message="blocked",
                        gate_kind="issue",
                        gate_ref="https://example.com/i/1",
                        gate_summary="waiting",
                        evidence=None,
                        yes_i_am_human=False,
                        date="2026-08-09",
                    )
                )
            self.assertEqual(rc, 0)
            t = p.read_text(encoding="utf-8")
            self.assertIn("- Gate-Kind: issue", t)
            self.assertIn("- Gate-Ref: https://example.com/i/1", t)
            # leaving deferred removes the gate fields
            with redirect_stdout(io.StringIO()):
                rc = specs.run_set(
                    _args(
                        path=str(p),
                        status="draft",
                        message="unblocked",
                        gate_kind=None,
                        gate_ref=None,
                        gate_summary=None,
                        evidence=None,
                        yes_i_am_human=False,
                        date="2026-08-10",
                    )
                )
            self.assertEqual(rc, 0)
            t = p.read_text(encoding="utf-8")
            self.assertNotIn("- Gate-Kind:", t)
            self.assertNotIn("- Gate-Ref:", t)

    def test_deferred_requires_valid_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._mk(d, "- Status: draft")
            before = p.read_text(encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                rc = specs.run_set(
                    _args(
                        path=str(p),
                        status="deferred",
                        message="x",
                        gate_kind="issue",
                        gate_ref="javascript:alert(1)",
                        gate_summary=None,
                        evidence=None,
                        yes_i_am_human=False,
                        date="2026-08-09",
                    )
                )
            self.assertEqual(rc, 1)
            self.assertEqual(p.read_text(encoding="utf-8"), before)


class MigrateTests(unittest.TestCase):
    def test_migrate_free_form_to_bare_enum(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.md"
            p.write_text(
                "# Spec: legacy\n\n- Date: 2026-08-08\n- Status: canonical reference; produced by IPD X\n- Author: t\n\n## Body\n\nx\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                rc = specs.run_migrate(
                    _args(
                        path=str(p),
                        status="implemented",
                        canonical=True,
                        gate_kind=None,
                        gate_ref=None,
                        gate_summary=None,
                        date="2026-08-09",
                    )
                )
            self.assertEqual(rc, 0)
            t = p.read_text(encoding="utf-8")
            self.assertIn("- Status: implemented", t)
            self.assertIn("- Canonical: true", t)
            self.assertIn("## Workflow history", t)
            self.assertIn("was: canonical reference", t)
            # result conforms
            self.assertEqual(specs.validate_spec(p, t), [])

    def test_migrate_to_deferred_with_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.md"
            p.write_text(
                "# Spec: legacy\n\n- Date: 2026-08-08\n- Status: draft spec (evidence-gated)\n- Author: t\n\n## Body\n\nx\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                rc = specs.run_migrate(
                    _args(
                        path=str(p),
                        status="deferred",
                        canonical=False,
                        gate_kind="artifact",
                        gate_ref="TODO.md",
                        gate_summary="waiting on the skills re-eval",
                        date="2026-08-09",
                    )
                )
            self.assertEqual(rc, 0)
            t = p.read_text(encoding="utf-8")
            self.assertIn("- Status: deferred", t)
            self.assertIn("- Gate-Kind: artifact", t)
            self.assertIn("- Gate-Ref: TODO.md", t)
            self.assertEqual(specs.validate_spec(p, t), [])

    def test_migrate_folds_implemented_line(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.md"
            p.write_text(
                "# Spec: legacy\n\n- Date: 2026-08-08\n- Status: approved (2026-07-30, human)\n- Implemented: SHIPPED as D123\n- Author: t\n\n## Body\n\nx\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                rc = specs.run_migrate(
                    _args(
                        path=str(p),
                        status="implemented",
                        canonical=False,
                        gate_kind=None,
                        gate_ref=None,
                        gate_summary=None,
                        date="2026-08-09",
                    )
                )
            self.assertEqual(rc, 0)
            t = p.read_text(encoding="utf-8")
            self.assertNotIn("- Implemented:", t)
            self.assertIn("folded Implemented line: SHIPPED as D123", t)
            self.assertEqual(specs.validate_spec(p, t), [])


class NoteTests(unittest.TestCase):
    def test_note_appends_one_record_only(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.md"
            p.write_text(_spec("- Status: draft"), encoding="utf-8")
            before_status = "- Status: draft"
            with redirect_stdout(io.StringIO()):
                rc = specs.run_note(
                    _args(path=str(p), message="a note", date="2026-08-09")
                )
            self.assertEqual(rc, 0)
            t = p.read_text(encoding="utf-8")
            self.assertIn(before_status, t)  # status unchanged
            self.assertEqual(t.count("- 2026-08-09 note (aw specs): a note"), 1)


if __name__ == "__main__":
    unittest.main()

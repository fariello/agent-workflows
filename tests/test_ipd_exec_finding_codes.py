"""Tests for spec 25kzda Section 4.6 IPD-EXEC finding codes table and accessors (6uhtko)."""

from __future__ import annotations

import importlib
import re
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Optional

from agent_workflows import ipd_lint, run_evidence, runner_shared


def _locate_spec() -> Path:
    """Locate spec 25kzda approved file by glob, asserting exactly one match."""
    matches = list(Path(".aw/records/specs/approved").glob("*-25kzda-*.spec.md"))
    assert (
        len(matches) == 1
    ), f"Expected exactly 1 spec 25kzda file, found {len(matches)}: {matches}"
    return matches[0]


def _parse_spec_4_6_rows(
    spec_path: Optional[Path | str] = None,
) -> Dict[str, Dict[str, str]]:
    """Parse Section 4.6's table rows out of spec 25kzda at run time.

    The path is injectable so V-04's RED-then-GREEN proof can run against a scratch copy.
    """
    path = Path(spec_path) if spec_path is not None else _locate_spec()
    content = path.read_text(encoding="utf-8")

    m = re.search(
        r"### 4\.6 One-off IPD execution verification\s*\n\n(.*?)\n\n[^\n|]",
        content,
        re.DOTALL,
    )
    assert m, f"Could not find Section 4.6 table in {path}"
    table_text = m.group(1).strip()
    lines = [
        line.strip() for line in table_text.splitlines() if line.strip().startswith("|")
    ]
    assert len(lines) >= 3, f"Section 4.6 table has fewer than 3 lines in {path}"

    # Header is lines[0], delimiter is lines[1], data rows start at lines[2]
    data_lines = lines[2:]
    parsed_rows: Dict[str, Dict[str, str]] = {}
    for line in data_lines:
        cells = [c.strip() for c in line.split("|")[1:-1]]
        assert len(cells) >= 5, f"Expected at least 5 cells in row: {line!r}"
        code = cells[0].strip("`")
        inspects = cells[1]
        pass_criterion = cells[2]
        message = cells[3].strip("`")
        action = cells[4]
        parsed_rows[code] = {
            "inspects": inspects,
            "pass_criterion": pass_criterion,
            "message": message,
            "action": action,
        }
    return parsed_rows


def _resolve_predicate(symbol: str) -> Any:
    """Resolve a module.symbol string to a callable object."""
    mod_name, sym_name = symbol.rsplit(".", 1)
    if not mod_name.startswith("agent_workflows"):
        mod_name = f"agent_workflows.{mod_name}"
    mod = importlib.import_module(mod_name)
    return getattr(mod, sym_name)


class IpdExecFindingCodesTests(unittest.TestCase):
    """E-04..E-06 / V-04..V-06: Verification of IPD-EXEC finding codes table, accessors, and invariants."""

    def test_spec_pinning_e04(self) -> None:
        """E-04 / V-04: Parse Section 4.6 and assert cell-to-field equality for the 3 shipped rows."""
        spec_rows = _parse_spec_4_6_rows()

        # Section 4.6 defines 11 rows in total; re-derive at run time (F-05)
        self.assertEqual(
            len(spec_rows),
            11,
            f"Expected Section 4.6 to have 11 rows, got {len(spec_rows)}",
        )

        # Shipped table carries exactly 3 pre-transition rows
        self.assertEqual(len(run_evidence.IPD_EXEC_FINDING_CODES), 3)
        shipped_by_code = run_evidence.IPD_EXEC_FINDING_CODES_BY_CODE

        target_codes = (
            "IPD-EXEC-E-COMPLETE",
            "IPD-EXEC-V-EVIDENCE",
            "IPD-EXEC-PRE-TRANSITION",
        )
        for code in target_codes:
            self.assertIn(
                code, shipped_by_code, f"Missing code in shipped table: {code}"
            )
            self.assertIn(code, spec_rows, f"Missing code in spec Section 4.6: {code}")

            row = shipped_by_code[code]
            spec_row = spec_rows[code]

            for field in ("inspects", "pass_criterion", "message", "action"):
                shipped_val = getattr(row, field)
                spec_val = spec_row[field]
                self.assertEqual(
                    shipped_val,
                    spec_val,
                    f"Spec drift for {code} field {field}: shipped {shipped_val!r} != spec {spec_val!r}",
                )

    def test_binding_honesty_e05(self) -> None:
        """E-05 / V-05: Resolve predicates, drive them on synthetic plans, and pin F-13 coverage hole."""
        # (a) Resolve every symbol named in predicates and assert callable
        for row in run_evidence.IPD_EXEC_FINDING_CODES:
            if row.binding == run_evidence.BOUND:
                self.assertTrue(
                    row.predicates, f"BOUND row {row.code} has no predicates"
                )
                for sym in row.predicates:
                    fn = _resolve_predicate(sym)
                    self.assertTrue(
                        callable(fn),
                        f"Resolved predicate {sym} for {row.code} is not callable",
                    )
            else:
                self.assertEqual(
                    row.predicates,
                    (),
                    f"Unbound row {row.code} must have empty predicates",
                )
                self.assertTrue(
                    row.waiting_on,
                    f"Unbound row {row.code} must describe what it waits on",
                )

        with tempfile.TemporaryDirectory() as td:
            # (b) Drive claimed predicates on synthetic plans
            # Plan 1: all-pending plan
            p1_text = (
                "# IPD: test all pending\n"
                "- Date: 2026-09-30\n"
                "- Kind: child\n"
                "- Concern: test\n"
                "- Scope: test\n"
                "- Scope-Paths: test.py\n"
                "- Item-Dependencies: none\n"
                "- Status: approved\n"
                "- Readiness: go-pending-approval\n"
                "- Work-Kind: chore\n"
                "- Priority: low\n"
                "- From-Backlog: test\n"
                "- Set: test\n"
                "- Order: 1\n"
                "- Highest E allocated: 01\n"
                "- Author: test\n"
                "- Id: sy0001\n"
                "- Approval: 2026-09-30\n\n"
                "## Detailed Implementation Checklist (TODO)\n"
                "- [ ] E-01 step\n"
                "  - Depends on: none\n"
                "  - Expected outcome: done\n"
                "  - Execution state: pending\n\n"
                "## Validation and cross-check (verify before reporting done)\n"
                "- [ ] V-01 validates E-01\n"
                "  - Required evidence: none\n"
                "  - Observed evidence:\n"
                "  - Result: pending\n"
            )
            f1 = Path(td) / "all_pending.ipd.md"
            f1.write_text(p1_text, encoding="utf-8")
            res1 = ipd_lint.lint_file(f1, checkpoint="pre-transition")
            msgs1 = [d.message for d in res1.diagnostics]
            self.assertTrue(
                any("not 'performed' at pre-transition" in m for m in msgs1)
            )
            self.assertTrue(any("not 'pass' at pre-transition" in m for m in msgs1))
            self.assertTrue(
                any("empty Observed evidence at pre-transition" in m for m in msgs1)
            )

            # Plan 2: performed/pass with unticked checkboxes
            p2_text = (
                "# IPD: test unticked\n"
                "- Date: 2026-09-30\n"
                "- Kind: child\n"
                "- Concern: test\n"
                "- Scope: test\n"
                "- Scope-Paths: test.py\n"
                "- Item-Dependencies: none\n"
                "- Status: approved\n"
                "- Readiness: go-pending-approval\n"
                "- Work-Kind: chore\n"
                "- Priority: low\n"
                "- From-Backlog: test\n"
                "- Set: test\n"
                "- Order: 1\n"
                "- Highest E allocated: 01\n"
                "- Author: test\n"
                "- Id: sy0002\n"
                "- Approval: 2026-09-30\n\n"
                "## Detailed Implementation Checklist (TODO)\n"
                "- [ ] E-01 step\n"
                "  - Depends on: none\n"
                "  - Expected outcome: done\n"
                "  - Execution state: performed\n\n"
                "## Validation and cross-check (verify before reporting done)\n"
                "- [ ] V-01 validates E-01\n"
                "  - Required evidence: none\n"
                "  - Observed evidence: some evidence\n"
                "  - Result: pass\n"
            )
            f2 = Path(td) / "unticked.ipd.md"
            f2.write_text(p2_text, encoding="utf-8")
            res2 = ipd_lint.lint_file(f2, checkpoint="pre-transition")
            codes2 = [d.code for d in res2.diagnostics]
            self.assertIn("IPD-S401", codes2)
            self.assertIn("IPD-S402", codes2)

            # (c) PIN THE COVERAGE HOLE THAT DECIDED E-02:
            # A plan whose checkboxes are all ticked, performed, pass, and Observed evidence
            # is literal gibberish with no receipt, artifact or command emits ZERO IPD-S40x diagnostics.
            p3_text = (
                "# IPD: test gibberish evidence\n"
                "- Date: 2026-09-30\n"
                "- Kind: child\n"
                "- Concern: test\n"
                "- Scope: test\n"
                "- Scope-Paths: test.py\n"
                "- Item-Dependencies: none\n"
                "- Status: approved\n"
                "- Readiness: go-pending-approval\n"
                "- Work-Kind: chore\n"
                "- Priority: low\n"
                "- From-Backlog: test\n"
                "- Set: test\n"
                "- Order: 1\n"
                "- Highest E allocated: 01\n"
                "- Author: test\n"
                "- Id: sy0003\n"
                "- Approval: 2026-09-30\n\n"
                "## Detailed Implementation Checklist (TODO)\n"
                "- [x] E-01 step\n"
                "  - Depends on: none\n"
                "  - Expected outcome: done\n"
                "  - Execution state: performed\n\n"
                "## Validation and cross-check (verify before reporting done)\n"
                "- [x] V-01 validates E-01\n"
                "  - Required evidence: none\n"
                "  - Observed evidence: qqq gibberish, no receipt, no artifact, no command\n"
                "  - Result: pass\n"
            )
            f3 = Path(td) / "gibberish.ipd.md"
            f3.write_text(p3_text, encoding="utf-8")
            res3 = ipd_lint.lint_file(f3, checkpoint="pre-transition")
            s4_diags = [d for d in res3.diagnostics if d.code.startswith("IPD-S4")]
            self.assertEqual(
                s4_diags,
                [],
                (
                    f"Expected zero IPD-S40x diagnostics for gibberish evidence, got {s4_diags}. "
                    "An IPD-S40x diagnostic appearing here means the coverage hole may have closed "
                    "and the binding must be RE-MEASURED rather than that the test is wrong."
                ),
            )

    def test_non_regression_e06(self) -> None:
        """E-06 / V-06: Assert RUN-* table is intact and finalize refusal classifier verdicts unchanged."""
        # 1. RUN-* table checks
        self.assertTrue(run_evidence.validate_finding_table().ok)
        self.assertEqual(len(run_evidence.run_finding_codes()), 12)
        self.assertEqual(len(run_evidence.bound_run_finding_codes()), 10)

        # 2. Behavioral pin on runner_shared.finalize_refusal_is_retryable (F-09 probe messages)
        msg_prose_kept = (
            "pre-transition gate did NOT conform (error); plan left unmoved.\n"
            "  IPD-EXEC-E-COMPLETE E-01: not 'performed' at pre-transition\n"
            "  IPD-EXEC-V-EVIDENCE V-01: not 'pass' at pre-transition\n"
        )
        msg_spec_verbatim = (
            "pre-transition gate did NOT conform (error); plan left unmoved.\n"
            "  [IPD-EXEC-E-COMPLETE] xbwq8n has incomplete execution items: E-01. Complete them, then: aw host run resume r1\n"
            "  [IPD-EXEC-V-EVIDENCE] xbwq8n lacks valid passing evidence for V-01: detail. Re-run those validations, then: aw host run resume r1\n"
        )

        self.assertTrue(runner_shared.finalize_refusal_is_retryable(msg_prose_kept))
        self.assertFalse(runner_shared.finalize_refusal_is_retryable(msg_spec_verbatim))

    def test_accessors_and_validator_e03(self) -> None:
        """E-03 / V-03: Exercise ipd_exec_* accessors and self-check validator."""
        codes = run_evidence.ipd_exec_finding_codes()
        self.assertEqual(
            codes,
            (
                "IPD-EXEC-E-COMPLETE",
                "IPD-EXEC-V-EVIDENCE",
                "IPD-EXEC-PRE-TRANSITION",
            ),
        )

        msg = run_evidence.ipd_exec_spec_message_for(
            "IPD-EXEC-E-COMPLETE", id6="xbwq8n"
        )
        self.assertIn("xbwq8n", msg)
        self.assertIn("<E-ids>", msg)

        with self.assertRaises(KeyError):
            run_evidence.ipd_exec_spec_message_for("NOPE-001")

        val_result = run_evidence.validate_ipd_exec_finding_table()
        self.assertTrue(val_result.ok)
        self.assertEqual(val_result.findings, ())

        # Negative validator tests
        orig = run_evidence.IPD_EXEC_FINDING_CODES
        try:
            # BOUND row with empty predicates
            bad_bound = run_evidence.RunFindingCode(
                code="IPD-EXEC-PRE-TRANSITION",
                inspects="Pre-transition linter",
                pass_criterion="Linter passes",
                message="[IPD-EXEC-PRE-TRANSITION] <id6>: aw resume",
                action="RETRY, then FAIL ITEM",
                abort=run_evidence.ABORT_NEVER,
                abort_classes=(),
                binding=run_evidence.BOUND,
                predicates=(),
                waiting_on="",
            )
            run_evidence.IPD_EXEC_FINDING_CODES = (orig[0], orig[1], bad_bound)
            res1 = run_evidence.validate_ipd_exec_finding_table()
            self.assertFalse(res1.ok)
            self.assertIn("RC-BINDING", [f.code for f in res1.findings])

            # UNBOUND row with empty waiting_on
            bad_unbound = run_evidence.RunFindingCode(
                code="IPD-EXEC-E-COMPLETE",
                inspects="Execution checklist",
                pass_criterion="Every E item is checked",
                message="[IPD-EXEC-E-COMPLETE] <id6>: aw resume",
                action="RETRY, then FAIL ITEM",
                abort=run_evidence.ABORT_NEVER,
                abort_classes=(),
                binding=run_evidence.UNBOUND_BY_DEPENDENCY,
                predicates=(),
                waiting_on="",
            )
            run_evidence.IPD_EXEC_FINDING_CODES = (bad_unbound, orig[1], orig[2])
            res2 = run_evidence.validate_ipd_exec_finding_table()
            self.assertFalse(res2.ok)
            self.assertIn("RC-BINDING", [f.code for f in res2.findings])
        finally:
            run_evidence.IPD_EXEC_FINDING_CODES = orig


if __name__ == "__main__":
    unittest.main()

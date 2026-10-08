"""Behavioral tests pinning the record-format boundary for exit codes.

Plan u28vqb (Set runexitvocab) E-06, V-06.

Verifies:
1. agent_schema.validate_agent_record enforces {0, 1, 2} on aw.agent/v1 records
   (accepts exit 1, rejects exit 3).
2. agent_schema.render_jsonl_record raises ValueError on exit 3 records, making
   the boundary mechanically unforgeable.
3. Every inventory declaration that admits exit codes outside {0, 1, 2} belongs
   to a documented allowlist with an explicit reason. The allowlist assertion is
   strictly superset-only to avoid brittle census drift when siblings land.
"""

from __future__ import annotations

import unittest
from typing import Dict
from unittest.mock import patch

from agent_workflows import agent_schema, command_surface


# Documented allowlist of commands whose declared exit_contract admits codes outside {0, 1, 2}.
# Keyed on command string; each entry carries an explicit reason explaining why the wider
# vocabulary applies.
OUT_OF_RANGE_DECLARATION_ALLOWLIST: Dict[str, str] = {
    "ipd execute-set": (
        "Execution orchestrator emitting execution manifest with exit 3 for unexecutable steps."
    ),
    "run start": (
        "Step execution lifecycle command using run-execution exit vocabulary (codes 0, 2, 3, 5, 6)."
    ),
    "runs next": (
        "Inspection command inspecting next resumable step using run-execution vocabulary (codes 0, 2, 3, 5, 7)."
    ),
    "run record": (
        "Step recording lifecycle command using run-execution vocabulary (codes 0, 2, 3, 5, 6)."
    ),
    "runs resume": (
        "Inspection command querying resumable steps using run-execution vocabulary (codes 0, 2, 3, 5, 7)."
    ),
    "run cancel": (
        "Run cancellation lifecycle command using run-execution vocabulary (codes 0, 2, 5, 6)."
    ),
    "runs status": (
        "Inspection command displaying run status using run-execution vocabulary (codes 0, 1, 2, 3, 5, 7)."
    ),
    "run finalize": (
        "Run finalization lifecycle command using run-execution vocabulary (codes 0, 1, 2, 4, 6)."
    ),
    "oc runipd": (
        "OpenCode driver run execution command admitting exit 3 for human gate / needs-input."
    ),
    "agy runipd": (
        "Antigravity driver run execution command admitting exit 3 for human gate / needs-input."
    ),
}


class ExitVocabularyBoundaryTests(unittest.TestCase):
    """Test behavioral enforcement of the exit-code boundary."""

    def test_agent_schema_enforces_three_state_exit_codes(self) -> None:
        """Validate that agent_schema mechanically enforces exit in {0, 1, 2}."""
        valid_record = {
            "schema": agent_schema.SCHEMA_VERSION,
            "kind": "result",
            "cmd": "test-command",
            "exit": 1,
            "outcome": "findings",
            "complete": True,
            "verified": True,
        }
        # Exit 1 is valid and accepted
        errs = agent_schema.validate_agent_record(valid_record)
        self.assertEqual(errs, [])

        # Exit 3 is outside {0, 1, 2} and rejected with validation error
        invalid_record = dict(valid_record, exit=3)
        errs_invalid = agent_schema.validate_agent_record(invalid_record)
        self.assertTrue(
            any(
                "Field 'exit' must be an integer in (0, 1, 2)" in e
                for e in errs_invalid
            ),
            f"Expected exit-in-(0,1,2) validation error, got: {errs_invalid}",
        )

        # render_jsonl_record refuses to render the invalid record
        with self.assertRaises(ValueError) as ctx:
            agent_schema.render_jsonl_record(invalid_record)
        self.assertIn(
            "Field 'exit' must be an integer in (0, 1, 2)", str(ctx.exception)
        )

    def test_out_of_range_declarations_covered_by_allowlist(self) -> None:
        """Every declaration admitting exit outside {0, 1, 2} must be in the allowlist.

        The check is strictly superset-only: every out-of-range declaration found
        must be an allowlist member, but the allowlist is not required to be exact
        set-equality so sibling plans that narrow or widen declarations do not break
        this assertion.
        """
        declarations = command_surface.get_all_declarations()
        out_of_range_found = [
            d for d in declarations if any(c not in (0, 1, 2) for c in d.exit_contract)
        ]

        for decl in out_of_range_found:
            self.assertIn(
                decl.command,
                OUT_OF_RANGE_DECLARATION_ALLOWLIST,
                f"Command '{decl.command}' declares out-of-range exit codes "
                f"{decl.exit_contract} but is not in OUT_OF_RANGE_DECLARATION_ALLOWLIST. "
                f"Add an entry with a reason explaining its exit vocabulary rather "
                f"than widening this test.",
            )

    def test_allowlist_is_resilient_to_sibling_declaration_substitutions(self) -> None:
        """Demonstrate that superset allowlist passes under sibling plan substitutions."""
        # Sibling plan 1mnit8 adds usage-error exit 2 to run family commands,
        # and 69rdv6 widens runs next and runs status. Neither breaks allowlist membership.
        all_decls = list(command_surface.get_all_declarations())
        simulated_decls = []
        for d in all_decls:
            if d.command == "runs next":
                simulated_decls.append(
                    command_surface.CommandDeclaration(
                        command=d.command,
                        command_class=d.command_class,
                        human_recipe=d.human_recipe,
                        agent_record_kind=d.agent_record_kind,
                        mutation_gate=d.mutation_gate,
                        empty_error_renderer=d.empty_error_renderer,
                        legacy_flags=d.legacy_flags,
                        exit_contract=(0, 2, 3, 5, 7),
                    )
                )
            elif d.command == "runs status":
                simulated_decls.append(
                    command_surface.CommandDeclaration(
                        command=d.command,
                        command_class=d.command_class,
                        human_recipe=d.human_recipe,
                        agent_record_kind=d.agent_record_kind,
                        mutation_gate=d.mutation_gate,
                        empty_error_renderer=d.empty_error_renderer,
                        legacy_flags=d.legacy_flags,
                        exit_contract=(0, 1, 2, 3, 5, 7),
                    )
                )
            else:
                simulated_decls.append(d)

        with patch.object(
            command_surface, "get_all_declarations", return_value=tuple(simulated_decls)
        ):
            out_of_range = [
                d
                for d in command_surface.get_all_declarations()
                if any(c not in (0, 1, 2) for c in d.exit_contract)
            ]
            for decl in out_of_range:
                self.assertIn(decl.command, OUT_OF_RANGE_DECLARATION_ALLOWLIST)

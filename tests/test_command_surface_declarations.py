"""Tests for Command Surface Declarations, Conflicting Format Flags, and Entrypoints Boundary.

awcliux Order 04 (`10jpsa`) E-03 / V-03.

Asserts:
1. Every parser leaf carries a contract declaration in `COMMAND_INVENTORY` (zero undeclared leaves).
2. Standalone installer scripts are classified out-of-boundary with explicit rationale.
3. Conflicting explicit format flags (`--agent` + `--json`, `--agent` + `--format`, etc.) are detected
   and rejected as usage errors (exit code 2).
4. Bare `aw`, empty family commands, `help`, and every alias route through the boundary, and
   aliases are agent-byte-equivalent to their canonical commands.
"""

from __future__ import annotations

import pytest

import json
import subprocess
import sys
import unittest
from pathlib import Path

from agent_workflows.cli import _build_parser
from agent_workflows.command_surface import (
    find_undeclared_leaves,
    get_all_declarations,
    get_standalone_scripts,
)
from agent_workflows.result_types import (
    ConflictingFlagsError,
    select_output,
)

# Heavy subprocess/CLI suite; excluded from the fast default run (see pyproject addopts
# `-m "not slow"`). Run with `make test-all`.
pytestmark = pytest.mark.slow

REPO_ROOT = Path(__file__).resolve().parent.parent


class CommandSurfaceDeclarationsTests(unittest.TestCase):
    """Assert exhaustive leaf declarations and zero undeclared parser leaves (E-03 / V-03)."""

    def test_zero_undeclared_parser_leaves(self):
        """Order 05 conformance harness requires 0 undeclared leaves across _build_parser()."""
        parser = _build_parser()
        undeclared = find_undeclared_leaves(parser)
        self.assertEqual(
            len(undeclared),
            0,
            f"Found undeclared parser leaves: {undeclared}",
        )

    def test_standalone_installer_scripts_classified(self):
        """Assert standalone installer scripts are classified with rationale."""
        scripts = get_standalone_scripts()
        script_names = {s.name for s in scripts}
        self.assertIn("install-workflows.py", script_names)
        self.assertIn("install-workflows.sh", script_names)
        for s in scripts:
            self.assertFalse(s.in_boundary)
            self.assertEqual(s.classification, "out_of_boundary")
            self.assertTrue(len(s.rationale) > 10)

    def test_all_declarations_have_valid_fields(self):
        """Every declaration has valid command class, recipe, record kind, exit contract, and empty/error renderer."""
        valid_classes = {
            "read",
            "check",
            "mutation",
            "preview",
            "bare",
            "alias",
            "family",
        }
        valid_kinds = {"result", "summary", "item", "error", "raw_path"}
        valid_renderers = {"shared_empty_result", "renderer_boundary", "delegated"}
        for decl in get_all_declarations():
            self.assertIn(
                decl.command_class,
                valid_classes,
                f"Invalid class '{decl.command_class}' on {decl.command}",
            )
            self.assertIn(
                decl.agent_record_kind,
                valid_kinds,
                f"Invalid record kind '{decl.agent_record_kind}' on {decl.command}",
            )
            self.assertIn(
                decl.empty_error_renderer,
                valid_renderers,
                f"Invalid empty_error_renderer '{decl.empty_error_renderer}' on {decl.command}",
            )
            self.assertTrue(len(decl.exit_contract) > 0)
            self.assertTrue(decl.migrated)

    def test_ad_hoc_empty_error_renderer_detected_and_rejected(self):
        """E-03 / V-03: A leaf attempting to roll its own ad-hoc empty/error output is rejected."""
        from agent_workflows.command_surface import CommandDeclaration

        valid_renderers = {"shared_empty_result", "renderer_boundary", "delegated"}
        adhoc_decl = CommandDeclaration(
            command="sample adhoc",
            command_class="read",
            human_recipe="table",
            agent_record_kind="result",
            mutation_gate="none",
            empty_error_renderer="ad_hoc_custom_printer",
        )
        self.assertNotIn(
            adhoc_decl.empty_error_renderer,
            valid_renderers,
            "Ad-hoc renderer must not be in valid renderers set",
        )

    def test_empty_error_renderer_classification_consistency(self):
        """E-03 / V-03: Aliases delegate, read/list queries declare shared_empty_result, mutations declare boundary."""
        for decl in get_all_declarations():
            if decl.command_class == "alias":
                self.assertEqual(
                    decl.empty_error_renderer,
                    "delegated",
                    f"Alias {decl.command} must declare empty_error_renderer='delegated'",
                )
            elif decl.command in {
                "list-repos",
                "show",
                "record-history",
                "attention",
                "project status",
                "config exclude list",
                "find",
                "search",
                "index",
                "ipd board",
                "research find",
                # runnamecollapse (`0soncw`) split the run surface by direction and introduced
                # `runs list` (the viewer table, identical to bare `aw runs`) as a READ/query leaf
                # declaring `shared_empty_result`, but this allowlist was not extended with it, so
                # the classification rule demanded `renderer_boundary` for a verb whose whole job is
                # listing. It belongs with `find`/`search`/`index`/`ipd board`: a selector-driven
                # listing whose empty result is a normal outcome rather than an error.
                "runs list",
            }:
                self.assertEqual(
                    decl.empty_error_renderer,
                    "shared_empty_result",
                    f"Query {decl.command} must declare empty_error_renderer='shared_empty_result'",
                )
            else:
                self.assertEqual(
                    decl.empty_error_renderer,
                    "renderer_boundary",
                    f"Command {decl.command} must declare empty_error_renderer='renderer_boundary'",
                )


class ConflictingFlagsTests(unittest.TestCase):
    """Assert conflicting explicit format flags exit 2 with usage error (E-03 / V-03)."""

    def test_conflicting_agent_and_json_flags_raise_in_select_output(self):
        args = type("Args", (), {"agent": True, "json": True})()
        with self.assertRaises(ConflictingFlagsError):
            select_output(args)

    def test_conflicting_agent_and_as_json_flags_raise_in_select_output(self):
        args = type("Args", (), {"as_agent": True, "as_json": True})()
        with self.assertRaises(ConflictingFlagsError):
            select_output(args)

    def test_conflicting_agent_and_format_json_raise_in_select_output(self):
        args = type("Args", (), {"agent": True, "format": "json"})()
        with self.assertRaises(ConflictingFlagsError):
            select_output(args)

    def test_conflicting_json_and_format_markdown_raise_in_select_output(self):
        args = type("Args", (), {"json": True, "format": "markdown"})()
        with self.assertRaises(ConflictingFlagsError):
            select_output(args)

    def test_cli_conflicting_flags_exit_2_with_usage_error(self):
        """Subprocess run of conflicting flags exits 2 and prints usage diagnostic."""
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "status", "--agent", "--json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2, f"Expected exit 2, got {proc.returncode}")
        self.assertIn("error: conflicting output format flags", proc.stderr)
        self.assertIn("Next  aw --help", proc.stderr)


class EntrypointsAndAliasesBoundaryTests(unittest.TestCase):
    """Assert bare aw, empty families, help, and aliases route through boundary (E-03 / V-03)."""

    def test_alias_att_is_agent_byte_equivalent_to_attention(self):
        """`aw att --agent` must be byte-identical to `aw attention --agent`."""
        proc_att = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "att", "--agent", "--check"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        proc_attention = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "attention",
                "--agent",
                "--check",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_att.returncode, proc_attention.returncode)
        self.assertEqual(proc_att.stdout, proc_attention.stdout)

    def test_alias_sanitize_is_agent_byte_equivalent_to_check_local_leaks(self):
        """`aw sanitize --agent` must be byte-identical to `aw check-local-leaks --agent`."""
        proc_san = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "sanitize", "--agent"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        proc_chk = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "check-local-leaks", "--agent"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_san.returncode, proc_chk.returncode)
        self.assertEqual(proc_san.stdout, proc_chk.stdout)

    def test_alias_spec_check_is_agent_byte_equivalent_to_specs_check(self):
        """`aw spec check --agent` must be byte-identical to `aw specs check --agent`."""
        proc_spec = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "spec", "check", "--agent"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        proc_specs = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "specs", "check", "--agent"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_spec.returncode, proc_specs.returncode)
        self.assertEqual(proc_spec.stdout, proc_specs.stdout)

    def test_empty_family_in_agent_mode_emits_cannot_run_record(self):
        """`aw project --agent` (empty family) emits structured cannot-run record with exit 2."""
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "project", "--agent"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        rec = json.loads(proc.stdout.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "error")
        self.assertEqual(rec["cmd"], "project")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertEqual(rec["verified"], False)
        self.assertEqual(rec["complete"], False)
        self.assertIn("project status", rec["next"])


if __name__ == "__main__":
    unittest.main()

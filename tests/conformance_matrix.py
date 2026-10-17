"""Generated CLI output-conformance matrix (awcliux Order 05 `e8hu4s` E-01 / E-02).

Stdlib only (Python 3.9+). This module is the shared harness consumed by:

- ``test_agent_surface_conformance.py``: executes every parser leaf declaring
  an ``aw.agent/v1`` result record under ``--agent`` and verifies schema
  validity and exit code parity against the real subprocess outcome.
- ``test_exit_contract_conformance.py``: executes safe read/check leaves in
  ``LIVE_SAFE_LEAVES`` via ``run_cli`` to verify observed exit-code membership
  against declared ``exit_contract`` (IPD 1mnit8).
- ``test_conformance_matrix_structure.py``: structural and alias gate asserting
  zero undeclared leaves, complete required scenario coverage, pinned declared-absent
  declarations, live-safe leaf rows, and alias byte-equivalence (IPD dq9bj9).
- ``test_live_conformance_sweep.py``: drives the per-leaf --help, usage-error,
  and --no-color scenario sweeps over safe leaves, color contrast verification,
  and non-vacuous human-agent fact parity (IPD 34iwyp).

Design notes
------------
The matrix is DERIVED from ``command_surface.COMMAND_INVENTORY`` (the normative
per-leaf contract shipped by Order 04) crossed with the per-class REQUIRED
scenario set below. Because the scenario set is a pure function of the command
CLASS, adding a new leaf to the parser without a declaration fails E-01
immediately (``find_undeclared_leaves``), and adding a declaration whose class
demands a scenario the harness cannot cover fails the coverage assertion.

Live scenarios are executed against a CURATED, SAFE, read-only / check-only
subset of leaves (``LIVE_SAFE_LEAVES``). Mutations, installers, and network or
disk-writing verbs are declared but NOT executed live (they are covered by the
owning children's own unit tests); the harness records them as
``covered_by="declaration"`` so the matrix stays exhaustive without side effects.

The harness PINS the Python-version-dependent argparse color/help output by
forcing ``NO_COLOR=1`` and a fixed ``COLUMNS`` in the subprocess environment, so
goldens do not flake across supported CPython versions.
"""

from __future__ import annotations

import atexit
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from agent_workflows import runner_shared, set_records
from agent_workflows.command_surface import (
    CommandDeclaration,
    discover_parser_leaves,
    get_all_declarations,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = Path(__file__).resolve().parent / "fixtures" / "conformance_goldens"

# ANSI escape detector (CSI sequences). Agent + JSON streams MUST be ANSI-free.
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


# --------------------------------------------------------------------------------------------------


def required_scenarios(decl: CommandDeclaration) -> Tuple[str, ...]:
    """Return the scenarios a leaf of this class MUST have covered.

    Every leaf must cover the audience+policy scenarios (tty, non_tty, agent,
    no_color, help, usage_error). ``json`` is required only when the leaf declares
    a ``--json`` legacy flag or is a read/check that ships JSON. ``domain_failure``
    is required for read/check leaves whose exit contract includes 1.
    ``success_preview`` is required for mutation/preview leaves.
    """
    base = ["tty", "non_tty", "agent", "no_color", "help", "usage_error"]

    # Aliases inherit their canonical target's contract but must additionally be
    # byte-equivalent; the alias-equivalence gate covers that separately.
    if "--json" in decl.legacy_flags or decl.command_class in ("read", "check", "bare"):
        base.append("json")

    if 1 in decl.exit_contract and decl.command_class in ("read", "check", "bare"):
        base.append("domain_failure")

    if decl.command_class in ("mutation", "preview"):
        base.append("success_preview")

    return tuple(base)


# --------------------------------------------------------------------------------------------------
# Curated live-executable safe leaves
# --------------------------------------------------------------------------------------------------

LEDGER_FIXTURE_RUN_ID = "run-abcdef1234"
LEDGER_FIXTURE_WORKFLOW = {
    "id": "wf-fixture",
    "steps": [{"id": "S-01", "satisfies": ["R-01"], "depends_on": []}],
    "requirements": [{"id": "R-01"}],
}
LEDGER_SAFE_LEAVES = frozenset(
    {
        "runs decisions",
        "runs evidence",
        "runs next",
        "runs questions",
        "runs resume",
        "runs show",
        "runs status",
        "runs verify-ledger",
    }
)

# Read/check leaves that are SAFE to execute live in the repo working tree: they
# never write, never touch the network, and are deterministic enough to gate on
# schema / ANSI / exit-code invariants (not on exact finding COUNTS). The value is
# the extra argv needed to make the leaf runnable non-interactively. The eight ledger
# leaves (runs decisions, runs evidence, runs next, runs questions, runs resume,
# runs show, runs status, runs verify-ledger) are read-only and run against an isolated
# aw run init fixture via live_leaf_argv, never against the repository checkout.
LIVE_SAFE_LEAVES: Dict[str, List[str]] = {
    "status": [],
    "context": [],
    # wslayout Order 05 (30jug9): `aw layout` is read-only by construction (it opens nothing for
    # writing and shells out to no git command), so it satisfies this dict's safety precondition
    # and is live-executed across every audience scenario rather than covered by declaration only.
    "layout": [],
    "list-repos": [],
    "attention": ["--check"],
    "doctor": [],
    "backlog check": [],
    "specs check": [],
    "spec check": [],
    "research check-refs": [],
    "research check-miscategorized": [],
    "ipd lint": ["--all"],
    "sanitize": [],
    "check-local-leaks": [],
    "workflow validate": [],
    "workflow check-generated": [],
    "runs decisions": [LEDGER_FIXTURE_RUN_ID],
    "runs evidence": [LEDGER_FIXTURE_RUN_ID],
    "runs next": [LEDGER_FIXTURE_RUN_ID],
    "runs questions": [LEDGER_FIXTURE_RUN_ID],
    "runs resume": [LEDGER_FIXTURE_RUN_ID],
    "runs show": [LEDGER_FIXTURE_RUN_ID],
    "runs status": [LEDGER_FIXTURE_RUN_ID],
    "runs verify-ledger": [LEDGER_FIXTURE_RUN_ID],
}

# Leaves historically partitioned due to live repository records traversal (IPD 34iwyp).
# Re-measured in IPD c8bfp9 E-03 against seeded fixture project with sandboxed config:
# - doctor: human 0.986s, agent 0.942s
# - attention: human 0.384s, agent 0.365s
# - status: human 0.416s, agent 0.419s
# All under 1.0s on the seeded project; slow mark and timeout(500) dropped in c8bfp9.
LIVE_HEAVY_LEAVES: frozenset[str] = frozenset(
    {
        "doctor",
        "attention",
        "status",
    }
)


def live_cheap_leaves() -> List[str]:
    """Return LIVE_SAFE_LEAVES members minus LIVE_HEAVY_LEAVES in sorted order."""
    return sorted(set(LIVE_SAFE_LEAVES.keys()) - LIVE_HEAVY_LEAVES)


# Table mapping a leaf to extra argv needed to make it runnable and read-only
# (e.g. providing required positional arguments in a safe read-only manner).
RUNNABLE_ARGV: Dict[str, List[str]] = {
    "releases show": ["next"],
    "reviews decisions": ["f36de0"],
    "runs query": ["schema"],
    "show": ["f36de0"],
    "workflow validate": [str(REPO_ROOT / "tests/fixtures/workflow-src/plan-review")],
    "workflow check-generated": [
        str(REPO_ROOT / "tests/fixtures/workflow-src/plan-review")
    ],
    "agy profile show": ["non-existent"],
    "oc profile show": ["non-existent"],
    "upgrade-test env": ["dummy"],
    "upgrade-test probe": ["dummy"],
    "partition": ["-t", "plans", "-s", "approved"],
    "graduation": ["25kzda"],
    "record-history": ["f36de0"],
    "config get": ["interactive"],
    "config is": ["interactive"],
    "index": ["plans", "--check"],
    "run init": ["--workflow", "wf.json"],
}

# --------------------------------------------------------------------------------------------------
# Justified exemption registry (E-02)
# --------------------------------------------------------------------------------------------------
# THE REGISTRY IS A CEILING, NOT A CONVENIENCE. Adding an entry to silence a red
# sweep is the prohibited failure mode that this harness exists to prevent, and a
# known_broken entry REQUIRES a filed item id. There is no catch-all, wildcard, or
# default-skip permitted; every exempted leaf must be individually enumerated with
# a valid typed reason and resolvable citation.


@dataclass(frozen=True)
class Exemption:
    reason_kind: str  # "sanctioned_raw" | "known_broken" | "not_runnable" | "arg_fixture_needed" | "fixture_lifecycle" | "owned_elsewhere"
    citation: str
    reason: str


EXEMPTION_REGISTRY: Dict[str, Exemption] = {
    # sanctioned_raw (13):
    "find": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 12",
        reason=(
            "When --agent is passed to aw find (or when piping paths to another tool), "
            "find emits bare repo-relative paths, maximizing token efficiency for agent "
            "tool consumption. Note: command_surface declares agent_record_kind='result', "
            "which disagrees with Section 12's bare-path sanction."
        ),
    ),
    "research find": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 12",
        reason=(
            "Emits raw matching research files and search snippets as plain text for agent "
            "consumption / token efficiency."
        ),
    ),
    "research pending": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 12",
        reason="Emits raw list of pending research file paths for token efficiency.",
    ),
    "research check-miscategorized": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 12",
        reason="Emits raw report lines detailing miscategorized research files.",
    ),
    "completion": Exemption(
        reason_kind="sanctioned_raw",
        citation="tools/completion.py",
        reason="Emits raw shell completion script for shell eval rather than an agent envelope.",
    ),
    "runs decisions": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 3.1",
        reason=(
            "Emits bare JSON dicts through run_cli._emit_machine under Section 3.1 "
            "run-execution exit vocabulary (pinned by tests/test_run_recovery_cli.py) "
            "rather than aw.agent/v1 records."
        ),
    ),
    "runs evidence": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 3.1",
        reason=(
            "Emits bare JSON dicts through run_cli._emit_machine under Section 3.1 "
            "run-execution exit vocabulary (pinned by tests/test_run_recovery_cli.py) "
            "rather than aw.agent/v1 records."
        ),
    ),
    "runs next": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 3.1",
        reason=(
            "Emits bare JSON dicts through run_cli._emit_machine under Section 3.1 "
            "run-execution exit vocabulary (pinned by tests/test_run_recovery_cli.py) "
            "rather than aw.agent/v1 records."
        ),
    ),
    "runs questions": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 3.1",
        reason=(
            "Emits bare JSON dicts through run_cli._emit_machine under Section 3.1 "
            "run-execution exit vocabulary (pinned by tests/test_run_recovery_cli.py) "
            "rather than aw.agent/v1 records."
        ),
    ),
    "runs resume": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 3.1",
        reason=(
            "Emits bare JSON dicts through run_cli._emit_machine under Section 3.1 "
            "run-execution exit vocabulary (pinned by tests/test_run_recovery_cli.py) "
            "rather than aw.agent/v1 records."
        ),
    ),
    "runs show": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 3.1",
        reason=(
            "Emits bare JSON dicts through run_cli._emit_machine under Section 3.1 "
            "run-execution exit vocabulary (pinned by tests/test_run_recovery_cli.py) "
            "rather than aw.agent/v1 records."
        ),
    ),
    "runs status": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 3.1",
        reason=(
            "Emits bare JSON dicts through run_cli._emit_machine under Section 3.1 "
            "run-execution exit vocabulary (pinned by tests/test_run_recovery_cli.py) "
            "rather than aw.agent/v1 records."
        ),
    ),
    "runs verify-ledger": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md Section 3.1",
        reason=(
            "Emits bare JSON dicts through run_cli._emit_machine under Section 3.1 "
            "run-execution exit vocabulary (pinned by tests/test_run_recovery_cli.py) "
            "rather than aw.agent/v1 records."
        ),
    ),
    # not_runnable (9):
    "ipd begin": Exemption(
        reason_kind="not_runnable",
        citation="aw ipd begin runner protocol",
        reason="Modifies IPD lifecycle state on disk; not a read-only command.",
    ),
    "ipd execute-set": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/ipd_compiler.py",
        reason="Emits schema_version: 1 execution manifest rather than aw.agent/v1 envelope.",
    ),
    "test": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/cli.py",
        reason=(
            "Executes test commands and records evidence to disk under the plan's local "
            "run-record area; mutating and not read-only."
        ),
    ),
    "agy view": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/cli.py",
        reason="Does not declare or accept --agent flag (accepts only [log] and exits 2).",
    ),
    "agy sessions": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/cli.py",
        reason="Does not declare or accept --agent flag (accepts only --json).",
    ),
    "__complete": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/cli.py",
        reason="Internal argparse shell completion helper, not a user-facing machine surface.",
    ),
    "pwatch": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/cli.py",
        reason="Interactive process watcher tool; does not accept --agent flag.",
    ),
    "runners": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/cli.py",
        reason="Interactive runner monitor tool; runs continuous dashboard loop by default.",
    ),
    "storage preflight": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/cli.py",
        reason="Requires --companion-dir argument and does not declare or accept --agent flag (accepts --json only).",
    ),
}

# --------------------------------------------------------------------------------------------------
# Justified mutation exemption registry (vfv2db E-02)
# --------------------------------------------------------------------------------------------------
# THE MUTATION REGISTRY IS A CEILING, NOT A CONVENIENCE. Every exempted mutation
# leaf must be individually enumerated with a valid typed reason and resolvable citation.
# Reason kinds:
# - "arg_fixture_needed": positional argument fixture required (names the missing positional)
# - "fixture_lifecycle": verbs that create or destroy the test fixture project itself
# - "owned_elsewhere": defect or gap owned by another active backlog item
# - "known_broken": known defect with an active backlog item carrier

MUTATION_EXEMPTION_REGISTRY: Dict[str, Exemption] = {
    # fixture_lifecycle (4):
    "install": Exemption(
        reason_kind="fixture_lifecycle",
        citation="harness architecture",
        reason="Bootstraps the project fixture that the sweep executes within.",
    ),
    "setup": Exemption(
        reason_kind="fixture_lifecycle",
        citation="harness architecture",
        reason="Initializes and configures the project fixture that the sweep executes within.",
    ),
    "migrate-layout": Exemption(
        reason_kind="fixture_lifecycle",
        citation="harness architecture",
        reason="Alters layout of the project fixture that the sweep executes within.",
    ),
    "uninstall": Exemption(
        reason_kind="fixture_lifecycle",
        citation="harness architecture",
        reason="Destroys the project fixture that the sweep executes within.",
    ),
    # owned_elsewhere (2):
    "rename": Exemption(
        reason_kind="owned_elsewhere",
        citation="eeiytw",
        reason="Missing aw.agent/v1 machine payload; owned by open backlog eeiytw.",
    ),
    "group": Exemption(
        reason_kind="owned_elsewhere",
        citation="eeiytw",
        reason="Missing aw.agent/v1 machine payload; owned by open backlog eeiytw.",
    ),
    # arg_fixture_needed (43):
    "commit": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires <plan> selector argument (or --no-plan with -m).",
    ),
    "integration-lock": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires locked_command argument after '--'.",
    ),
    "agy exec": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires subshell command or script arguments; does not accept bare --agent.",
    ),
    "agy profile remove": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires name positional argument.",
    ),
    "agy profile validate-default": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires state positional argument.",
    ),
    "agy runipd": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires plan or queue positional arguments; does not accept bare --agent.",
    ),
    "backlog note": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires path positional argument and --message flag.",
    ),
    "backlog set": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires args positional arguments.",
    ),
    "config add": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires add_args positional arguments.",
    ),
    "config exclude add": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires path positional argument.",
    ),
    "config exclude rm": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires path positional argument.",
    ),
    "config remove": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires remove_args positional arguments.",
    ),
    "config set": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires set_args positional arguments.",
    ),
    "config unset": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires varname positional argument.",
    ),
    "finish": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires plan positional argument.",
    ),
    "ipd dependencies remove": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires selector positional argument.",
    ),
    "ipd dependencies set": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires selector positional argument.",
    ),
    "ipd finalize": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires plan positional argument and --actor, --message.",
    ),
    "ipd set": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires args positional arguments.",
    ),
    "ipd sync": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires path positional argument.",
    ),
    "oc profile remove": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires name positional argument.",
    ),
    "oc profile validate-default": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires state positional argument.",
    ),
    "oc runipd": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires plan or queue positional arguments; does not accept bare --agent.",
    ),
    "project attach": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires project_id positional argument.",
    ),
    "project move": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires project_id and new_path positional arguments.",
    ),
    "prompts set": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires args positional arguments.",
    ),
    "research add-model": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires token positional argument.",
    ),
    "research mv": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires id positional argument.",
    ),
    "research set-assign": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires ids positional argument and --set.",
    ),
    "research set-outcome": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires id positional argument.",
    ),
    "research set-priority": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires id positional argument.",
    ),
    "run as": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires runner command arguments; does not accept bare --agent.",
    ),
    "run cancel": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason=(
            "Requires target positional argument; emits bare JSON dicts under "
            "docs/cli-output-contract.md Section 3.1; live-tested against fixture "
            "ledger in tests/test_live_conformance_sweep.py."
        ),
    ),
    "run finalize": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason=(
            "Requires target positional and --workflow flags; emits bare JSON dicts under "
            "docs/cli-output-contract.md Section 3.1; live-tested against fixture "
            "ledger in tests/test_live_conformance_sweep.py."
        ),
    ),
    "run ipd": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires target/plan positional arguments; does not accept bare --agent.",
    ),
    "run record": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason=(
            "Requires target positional and --step/--state/--workflow flags; emits bare "
            "JSON dicts under docs/cli-output-contract.md Section 3.1; live-tested against "
            "fixture ledger in tests/test_live_conformance_sweep.py."
        ),
    ),
    "run start": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason=(
            "Requires target positional and --step/--workflow flags; emits bare JSON dicts "
            "under docs/cli-output-contract.md Section 3.1; live-tested against fixture "
            "ledger in tests/test_live_conformance_sweep.py."
        ),
    ),
    "run verify": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires target positional argument.",
    ),
    "set": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires args positional arguments.",
    ),
    "specs migrate": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires path positional argument and --status.",
    ),
    "specs note": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires path positional argument and --message.",
    ),
    "specs set": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires args positional arguments.",
    ),
    "upgrade-test new": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires repo positional argument.",
    ),
    "work begin": Exemption(
        reason_kind="arg_fixture_needed",
        citation="positional argument required",
        reason="Requires plan positional argument.",
    ),
}

# --------------------------------------------------------------------------------------------------
# Family-root exemption registry (0qdl9e E-03)
# --------------------------------------------------------------------------------------------------
# THE REGISTRY IS A CEILING, NOT A CONVENIENCE. Adding an entry to silence a red
# sweep is the prohibited failure mode that this harness exists to prevent, and a
# known_broken entry REQUIRES a filed item id. There is no catch-all, wildcard, or
# default-skip permitted; every exempted root must be individually enumerated with
# a valid typed reason and resolvable citation.
# Allowed reason_kind is "known_broken" only. Citations must resolve to a live backlog item.

FAMILY_ROOT_EXEMPTION_REGISTRY: Dict[str, Exemption] = {}

# --------------------------------------------------------------------------------------------------
# Declared unreachable command allow-set (declabsent Order 01 gm9baj E-02)
# --------------------------------------------------------------------------------------------------
# THE ALLOW-SET IS A CEILING, NOT A CONVENIENCE. Every entry requires an open
# item id and an active plan carrier. An entry that becomes reachable fails the
# gate until deleted. There is no catch-all, wildcard, or default-skip permitted;
# every exempted command must be individually enumerated with a valid typed reason
# and resolvable citation.
#
# History:
# - 'prompts set' (backlog 68sur3, plan 7z3ovv) was the sole initial seed; plan 7z3ovv
#   registered its parser leaf, making it reachable, so the entry was deleted
#   per gm9baj Scope check ("whichever plan runs second must delete it").

UNREACHABLE_COMMAND_ALLOW_SET: Dict[str, Exemption] = {}

# A leaf + argv that deterministically triggers a usage error (invalid flag).
USAGE_ERROR_FLAG = "--this-flag-does-not-exist"


# --------------------------------------------------------------------------------------------------
# Subprocess runner
# --------------------------------------------------------------------------------------------------


@dataclass
class RunResult:
    argv: List[str]
    returncode: int
    stdout: str
    stderr: str


def _pinned_env(
    *,
    force_color: bool = False,
    no_color: bool = False,
    ascii_only: bool = False,
    columns: str = "80",
    env_overrides: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Build a deterministic environment.

    Pins ``COLUMNS`` and TERM so Python-version-dependent argparse help/usage width
    and color do not flake across CPython versions. By default color is OFF
    (NO_COLOR unset only when ``force_color`` is requested).
    """
    env = dict(os.environ)
    env.pop("FORCE_COLOR", None)
    env.pop("NO_COLOR", None)
    env.pop("AW_ASCII_ONLY", None)
    env.pop("FORCE_ASCII", None)
    env["COLUMNS"] = columns
    env["TERM"] = "xterm-256color"
    env["PYTHONIOENCODING"] = "utf-8"
    if force_color:
        env["FORCE_COLOR"] = "1"
    if no_color:
        env["NO_COLOR"] = "1"
    if ascii_only:
        env["AW_ASCII_ONLY"] = "1"

    # Always pin PYTHONPATH to REPO_ROOT (prepended to any existing value) so
    # subprocesses launched with cwd outside this checkout import this worktree's package (F-13).
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{REPO_ROOT}{os.pathsep}{existing_pp}" if existing_pp else str(REPO_ROOT)
    )

    if env_overrides:
        env.update(env_overrides)
    return env


def run_cli(
    argv: Sequence[str],
    *,
    cwd: Optional[Path | str] = None,
    force_color: bool = False,
    no_color: bool = False,
    ascii_only: bool = False,
    columns: str = "80",
    encoding: str = "utf-8",
    env_overrides: Optional[Dict[str, str]] = None,
) -> RunResult:
    """Run ``python -m agent_workflows <argv>`` as a subprocess with a pinned env.

    stdin is DEVNULL (never a TTY) so prompting never blocks; stdout/stderr are
    captured as pipes (never a TTY), which is precisely the non-TTY audience path.
    """
    cmd = [sys.executable, "-m", "agent_workflows", *argv]
    effective_cwd = str(REPO_ROOT) if cwd is None else str(cwd)
    proc = subprocess.run(
        cmd,
        cwd=effective_cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=_pinned_env(
            force_color=force_color,
            no_color=no_color,
            ascii_only=ascii_only,
            columns=columns,
            env_overrides=env_overrides,
        ),
    )
    out = proc.stdout.decode(encoding, errors="replace").replace("\r\n", "\n")
    err = proc.stderr.decode(encoding, errors="replace").replace("\r\n", "\n")
    return RunResult(
        argv=list(argv), returncode=proc.returncode, stdout=out, stderr=err
    )


def run_cli_inproc(
    argv: Sequence[str],
    *,
    cwd: Optional[Path | str] = None,
    force_color: bool = False,
    no_color: bool = False,
    ascii_only: bool = False,
    columns: str = "80",
    encoding: str = "utf-8",
    env_overrides: Optional[Dict[str, str]] = None,
) -> RunResult:
    """Execute ``agent_workflows.cli.main(argv)`` in-process with a pinned env and captured I/O.

    Saves and restores ``os.getcwd()`` with ``os.chdir`` in a ``finally`` block, applies the
    same environment ``_pinned_env`` builds via save-and-restore of ``os.environ``, redirects
    stdout/stderr to ``io.StringIO``, calls ``agent_workflows.cli.main(argv)``, maps
    ``SystemExit`` to an integer return code, and resets ``sys.argv``.
    """
    from agent_workflows import cli

    old_cwd = os.getcwd()
    old_env = dict(os.environ)
    old_argv = list(sys.argv)

    effective_cwd = str(REPO_ROOT) if cwd is None else str(cwd)
    try:
        pinned = _pinned_env(
            force_color=force_color,
            no_color=no_color,
            ascii_only=ascii_only,
            columns=columns,
            env_overrides=env_overrides,
        )
        os.environ.clear()
        os.environ.update(pinned)

        os.chdir(effective_cwd)
        sys.argv = ["agent_workflows", *argv]

        out = io.StringIO()
        err = io.StringIO()
        code: Optional[int | Any] = None
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = cli.main(list(argv))
            except SystemExit as exc:
                code = exc.code

        if code is None:
            returncode = 0
        elif isinstance(code, int):
            returncode = code
        else:
            returncode = 1

        out_str = out.getvalue().replace("\r\n", "\n")
        err_str = err.getvalue().replace("\r\n", "\n")
        return RunResult(
            argv=list(argv), returncode=returncode, stdout=out_str, stderr=err_str
        )
    finally:
        try:
            os.chdir(old_cwd)
        except Exception:
            pass
        os.environ.clear()
        os.environ.update(old_env)
        sys.argv = old_argv


def run_cli_tty(
    argv: Sequence[str],
    *,
    no_color: bool = False,
    cwd: Optional[Path | str] = None,
    env_overrides: Optional[Dict[str, str]] = None,
) -> RunResult:
    """Run ``python -m agent_workflows <argv>`` attached to a POSIX pseudo-terminal (pty).

    stdout and stderr are attached to the pty slave, enabling TTY color emission detection.
    On Windows (sys.platform == "win32"), callers must skip since pty is unavailable (IPD 34iwyp E-07).
    """
    if sys.platform == "win32":
        import pytest

        pytest.skip(
            "run_cli_tty requires pty support (unavailable on Windows; IPD 34iwyp E-07)"
        )

    import pty

    master_fd, slave_fd = pty.openpty()
    cmd = [sys.executable, "-m", "agent_workflows", *argv]
    effective_cwd = str(REPO_ROOT) if cwd is None else str(cwd)
    env = _pinned_env(no_color=no_color, env_overrides=env_overrides)
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=effective_cwd,
            stdin=subprocess.DEVNULL,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            close_fds=True,
        )
    finally:
        os.close(slave_fd)

    out_chunks: List[bytes] = []
    while True:
        try:
            chunk = os.read(master_fd, 8192)
            if not chunk:
                break
            out_chunks.append(chunk)
        except OSError:
            # On Linux, EIO is raised when the slave fd is closed by the child.
            break
    os.close(master_fd)
    proc.wait()
    combined = b"".join(out_chunks).decode("utf-8", errors="replace")
    return RunResult(
        argv=list(argv),
        returncode=proc.returncode,
        stdout=combined,
        stderr="",
    )


# --------------------------------------------------------------------------------------------------
# Ledger fixture helpers (g5s94t E-02)
# --------------------------------------------------------------------------------------------------


def seed_ledger_fixture(root: Path, run_id: str = LEDGER_FIXTURE_RUN_ID) -> Path:
    """Initialize an isolated ledger fixture inside root (E-02).

    (a) Creates root/.aw/records if absent (F-09).
    (b) Writes root/wf.json with LEDGER_FIXTURE_WORKFLOW.
    (c) Invokes aw run init and asserts returncode 0 and ledger inside root.
    (d) Writes decisions.md and open-questions.md projections under set_records.run_artifacts_dir.
    (e) Returns root.
    """
    (root / ".aw" / "records").mkdir(parents=True, exist_ok=True)
    wf_path = root / "wf.json"
    wf_path.write_text(json.dumps(LEDGER_FIXTURE_WORKFLOW), encoding="utf-8")

    res = run_cli(
        [
            "run",
            "init",
            "--workflow",
            str(wf_path),
            "--run-id",
            run_id,
            "--dir",
            str(root),
        ]
    )
    assert (
        res.returncode == 0
    ), f"seed_ledger_fixture run init failed: {res.stderr}\nStdout: {res.stdout}"

    ledger_file = runner_shared.state_root(root) / run_id / "ledger.jsonl"
    assert ledger_file.is_file(), f"Expected ledger file at {ledger_file}"
    assert str(ledger_file.resolve()).startswith(
        str(root.resolve())
    ), f"Ledger file path {ledger_file} is not inside root {root.resolve()}"

    proj_dir = set_records.run_artifacts_dir(root, "exec-set", run_id)
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / set_records.DECISIONS_FILE).write_text(
        "_No autonomous decisions recorded._\n", encoding="utf-8"
    )
    (proj_dir / set_records.OPEN_QUESTIONS_FILE).write_text(
        "_No unresolved questions._\n", encoding="utf-8"
    )
    return root


def live_leaf_argv(leaf: str, ledger_fixture_dir: Optional[Path] = None) -> List[str]:
    """Return the full argv for a live safe leaf.

    For the eight ``aw runs`` leaves, requires a non-None ``ledger_fixture_dir``
    and appends ``["--dir", str(ledger_fixture_dir)]`` and, for ``runs next``,
    ``runs resume``, ``runs status`` only,
    ``["--workflow", str(ledger_fixture_dir / "wf.json")]``.
    Raises ValueError if called for a ledger leaf with ``ledger_fixture_dir is None``.
    """
    if leaf in LEDGER_SAFE_LEAVES:
        if ledger_fixture_dir is None:
            raise ValueError(f"ledger leaf {leaf!r} requires a ledger_fixture_dir")
        extra = list(LIVE_SAFE_LEAVES.get(leaf, []))
        argv = [*leaf.split(), *extra, "--dir", str(ledger_fixture_dir)]
        if leaf in ("runs next", "runs resume", "runs status"):
            argv.extend(["--workflow", str(ledger_fixture_dir / "wf.json")])
        return argv
    return [*leaf.split(), *LIVE_SAFE_LEAVES[leaf]]


# --------------------------------------------------------------------------------------------------
# Isolated project fixture and clone helpers (vfv2db E-01)
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class InstalledProjectTemplate:
    template_dir: Path
    home_dir: Path
    xdg_config_home: Path
    baseline_status: str
    baseline_head: str


@dataclass(frozen=True)
class IsolatedProject:
    project_dir: Path
    home_dir: Path
    xdg_config_home: Path
    baseline_status: str
    baseline_head: str
    env_overrides: Dict[str, str]


def build_installed_project_template(base_dir: Path) -> InstalledProjectTemplate:
    """Build a session-scoped installed-project template (E-01).

    Initializes a git repository, sets a local git identity (F-14), pins HOME and
    XDG_CONFIG_HOME into the temp tree (F-11), pins PYTHONPATH to REPO_ROOT (F-13),
    and runs `aw install . --yes`. Asserts install success, committed HEAD, and
    known baseline status.
    """
    proj_dir = base_dir / "template_proj"
    proj_dir.mkdir(parents=True, exist_ok=True)
    home_dir = base_dir / "template_home"
    home_dir.mkdir(parents=True, exist_ok=True)
    xdg_config_home = base_dir / "template_xdg"
    xdg_config_home.mkdir(parents=True, exist_ok=True)

    # Initialize git repo and local identity before installing (F-14)
    subprocess.run(["git", "init"], cwd=proj_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test Agent"],
        cwd=proj_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test-agent@example.com"],
        cwd=proj_dir,
        check=True,
        capture_output=True,
    )

    env_overrides = {
        "HOME": str(home_dir),
        "XDG_CONFIG_HOME": str(xdg_config_home),
    }

    # Run aw install . --yes via run_cli with pinned env
    res = run_cli(
        ["install", ".", "--yes"],
        cwd=proj_dir,
        env_overrides=env_overrides,
    )
    assert res.returncode == 0, (
        f"aw install . --yes failed in template with exit code {res.returncode}:\n"
        f"Stdout: {res.stdout}\n"
        f"Stderr: {res.stderr}"
    )

    # Assert HEAD exists and record baseline status and commit
    head_proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=proj_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    head = head_proc.stdout.strip()
    status_proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=proj_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    status = status_proc.stdout

    # Assert .aw structure exists
    aw_dir = proj_dir / ".aw"
    assert aw_dir.is_dir(), f".aw directory missing from template at {proj_dir}"
    for required_subdir in ("records", "state", "system"):
        assert (
            aw_dir / required_subdir
        ).is_dir(), f".aw/{required_subdir} missing from template at {proj_dir}"

    # Write wf.json for run init in mutation clones (captured after baseline status)
    (proj_dir / "wf.json").write_text(
        json.dumps(LEDGER_FIXTURE_WORKFLOW), encoding="utf-8"
    )

    return InstalledProjectTemplate(
        template_dir=proj_dir,
        home_dir=home_dir,
        xdg_config_home=xdg_config_home,
        baseline_status=status,
        baseline_head=head,
    )


def clone_isolated_project(
    template: InstalledProjectTemplate,
    dest_base: Path,
) -> IsolatedProject:
    """Clone a per-leaf isolated project from the session-scoped template (E-01).

    Copies the template project repo, gives it its own isolated HOME and XDG_CONFIG_HOME
    directories inside dest_base, and returns an IsolatedProject helper.
    """
    dest_base.mkdir(parents=True, exist_ok=True)
    leaf_proj = dest_base / "proj"
    leaf_home = dest_base / "home"
    leaf_xdg = dest_base / "xdg"

    shutil.copytree(template.template_dir, leaf_proj, symlinks=True)
    leaf_home.mkdir(parents=True, exist_ok=True)
    leaf_xdg.mkdir(parents=True, exist_ok=True)

    env_overrides = {
        "HOME": str(leaf_home),
        "XDG_CONFIG_HOME": str(leaf_xdg),
    }

    return IsolatedProject(
        project_dir=leaf_proj,
        home_dir=leaf_home,
        xdg_config_home=leaf_xdg,
        baseline_status=template.baseline_status,
        baseline_head=template.baseline_head,
        env_overrides=env_overrides,
    )


_SEEDED_TEMPLATE: Optional[InstalledProjectTemplate] = None


def build_seeded_project_template(base_dir: Path) -> InstalledProjectTemplate:
    """Build a session-scoped seeded installed-project template (c8bfp9 E-02).

    Extends build_installed_project_template with a small committed records set:
    - one pending plan with id f36de0, status approved, order 1, set seeded
    - one review record with id f36de0 and Decisions table
    - one spec with id 25kzda, status approved
    - one backlog item with id bklg01, status open
    - one research record with id rsch01
    - one release record with id f33nrj, status planned
    - ledger fixture initialized via seed_ledger_fixture
    Committed with git add and git commit.
    """
    installed = build_installed_project_template(base_dir)
    proj = installed.template_dir

    # Seed plan f36de0 (approved pending plan)
    plan_dir = proj / ".aw" / "records" / "plans" / "pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_content = """# IPD: Seeded Plan for Conformance

- Date: 2026-10-16
- Kind: child
- Scope: Seeded fixture plan
- Scope-Paths: tests/
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- Set: seeded
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: f36de0

## Workflow history
- 2026-10-16 approved: status set to approved
- 2026-10-16 to-review: drafted

## Goal
Seeded fixture goal.

## Detailed Implementation Checklist (TODO)
- [ ] E-01 Seeded task
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: done
  - Observed evidence:
  - Result: pending
"""
    (plan_dir / "20261016-seeded-01-f36de0-seeded-plan.ipd.md").write_text(
        plan_content, encoding="utf-8"
    )

    # Seed spec 25kzda
    spec_dir = proj / ".aw" / "records" / "specs" / "approved"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_content = """# SPEC: Seeded Spec for Conformance

- Id: 25kzda
- Status: approved
- Title: Seeded Spec
- Slug: seeded-spec
- Scope-Paths: tests/
- Author: test

## Summary
Seeded spec summary.

## Workflow history
- 2026-08-26 approved: status set to approved

## Requirements
### R-01 Seeded Requirement
Seeded requirement text.
"""
    (spec_dir / "20260826-25kzda-01-25kzda-seeded-spec.spec.md").write_text(
        spec_content, encoding="utf-8"
    )

    # Seed review f36de0
    rev_dir = proj / ".aw" / "records" / "reviews"
    rev_dir.mkdir(parents=True, exist_ok=True)
    rev_content = """# Review findings: plan f36de0

- Subject-Id: f36de0
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: test-reviewer
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1
Seeded review text.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Seeded question? | Yes | No | Basis text | yes |
"""
    (rev_dir / "20261016-seeded-01-f36de0-seeded-plan.review.md").write_text(
        rev_content, encoding="utf-8"
    )

    # Seed backlog item
    bklg_dir = proj / ".aw" / "records" / "backlog" / "open"
    bklg_dir.mkdir(parents=True, exist_ok=True)
    bklg_content = """- Id: bklg01
- Status: open
- Set: seeded
- Priority: low
- Work-Kind: chore
- Summary: Seeded backlog item

## Workflow history
- 2026-10-16 created: created
"""
    (bklg_dir / "20261016-seeded-01-bklg01-seeded-item.backlog.md").write_text(
        bklg_content, encoding="utf-8"
    )

    # Seed research record
    rsch_dir = proj / ".aw" / "records" / "research"
    rsch_dir.mkdir(parents=True, exist_ok=True)
    rsch_content = """---
id: rsch01
created: 20261016
set: seeded
order: 01
topic: [testing]
model: test
kind: assessment
status: reference
outcome: informational
summary: Seeded research record
consumed-by: []
---

# Seeded research record
Seeded research content.
"""
    (rsch_dir / "20261016-seeded-01-rsch01-seeded-research.assessment.md").write_text(
        rsch_content, encoding="utf-8"
    )

    # Seed release record
    rel_dir = proj / ".aw" / "records" / "releases"
    rel_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        REPO_ROOT
        / ".aw"
        / "records"
        / "releases"
        / "20260820-f33nrj-01-f33nrj-2-0-0.release.md",
        rel_dir,
    )

    # Seed ledger fixture
    seed_ledger_fixture(proj, LEDGER_FIXTURE_RUN_ID)

    # Commit all seeded records
    subprocess.run(["git", "add", "-A"], cwd=proj, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "seed records and ledger fixture"],
        cwd=proj,
        check=True,
        capture_output=True,
    )

    head_proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=proj,
        check=True,
        capture_output=True,
        text=True,
    )
    status_proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=proj,
        check=True,
        capture_output=True,
        text=True,
    )

    return InstalledProjectTemplate(
        template_dir=proj,
        home_dir=installed.home_dir,
        xdg_config_home=installed.xdg_config_home,
        baseline_status=status_proc.stdout,
        baseline_head=head_proc.stdout.strip(),
    )


def get_seeded_project_template() -> InstalledProjectTemplate:
    """Return process-singleton seeded project template, initializing lazily."""
    global _SEEDED_TEMPLATE
    if _SEEDED_TEMPLATE is not None and _SEEDED_TEMPLATE.template_dir.is_dir():
        return _SEEDED_TEMPLATE

    tmp_root = Path(tempfile.mkdtemp(prefix="aw_seeded_template_"))
    atexit.register(shutil.rmtree, str(tmp_root), ignore_errors=True)
    _SEEDED_TEMPLATE = build_seeded_project_template(tmp_root)
    return _SEEDED_TEMPLATE


def get_seeded_project_dir() -> Path:
    """Return the Path to the template_dir of the seeded project template."""
    return get_seeded_project_template().template_dir


# --------------------------------------------------------------------------------------------------
# Semantic-fact extraction (fact-parity gate)
# --------------------------------------------------------------------------------------------------


def semantic_facts_from_agent(stdout: str) -> Dict[str, object]:
    """Extract the canonical semantic facts from an agent (aw.agent/v1) stream.

    Reads the terminal result/summary/error record (the last non-item record) and
    returns {command, outcome, exit, findings}. Falls back gracefully on empty.
    """
    import json

    facts: Dict[str, object] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except (ValueError, json.JSONDecodeError):
            continue
        if not isinstance(rec, dict):
            continue
        if rec.get("kind") in ("result", "summary", "error"):
            facts = {
                "cmd": rec.get("cmd"),
                "outcome": rec.get("outcome"),
                "exit": rec.get("exit"),
                "findings": rec.get("findings", rec.get("total")),
            }
    return facts


_HUMAN_OUTCOME_WORDS = {
    "conforms": "clean",
    "clean": "clean",
    "ok": "clean",
    "findings": "findings",
    "fail": "fail",
    "failed": "fail",
    "error": "error",
    "preview": "preview",
    "stale": "stale",
}


def outcome_family(agent_outcome: object) -> Optional[str]:
    """Map an agent outcome to the coarse human family for parity comparison."""
    if agent_outcome is None:
        return None
    key = str(agent_outcome).lower()
    return _HUMAN_OUTCOME_WORDS.get(key, key)


def semantic_facts_from_human(stdout: str) -> Dict[str, object]:
    """Extract the outcome family from the standard HumanRenderer outcome banner.

    Recognizes two measured banner forms (IPD 34iwyp E-04):
    (a) An 'AW <command>' title line followed by a '<glyph> <STATUS>' banner line.
    (b) A first line that is itself '<glyph> <STATUS> ...'.

    In both shapes, the banner line must be exactly '<glyph> <STATUS> ...', where
    <glyph> is in agent_workflows.term.GLYPHS or ASCII_GLYPHS, and <STATUS> is an
    uppercase token looked up in _HUMAN_OUTCOME_WORDS.
    Table, board, and rich renders return {'outcome_family': None}.
    """
    import agent_workflows.term as term

    all_glyphs = set(term.GLYPHS.values()) | set(term.ASCII_GLYPHS.values())
    plain = ANSI_RE.sub("", stdout)
    nonempty = [ln.strip() for ln in plain.splitlines() if ln.strip()]
    if not nonempty:
        return {"outcome_family": None}

    def _extract_banner(line: str) -> Optional[str]:
        toks = line.split()
        if len(toks) >= 2 and toks[0] in all_glyphs and toks[1] == toks[1].upper():
            key = toks[1].lower()
            if key in _HUMAN_OUTCOME_WORDS:
                return _HUMAN_OUTCOME_WORDS[key]
        return None

    # Shape (a): 'AW <command>' title line followed by banner line
    if nonempty[0].startswith("AW "):
        if len(nonempty) >= 2:
            family = _extract_banner(nonempty[1])
            if family is not None:
                return {"outcome_family": family}
        return {"outcome_family": None}

    # Shape (b): First line is itself the banner
    family = _extract_banner(nonempty[0])
    return {"outcome_family": family}


# Curated leaves that emit a human outcome banner and have an agent surface.
# Must be executed in an isolated environment with pinned HOME/XDG_CONFIG_HOME/AW_HOME.
FACT_PARITY_LEAVES: Dict[str, List[str]] = {
    "runs query": ["schema"],
    "list-repos": [],
    "record-history": ["f36de0"],
}


# --------------------------------------------------------------------------------------------------
# Matrix generation
# --------------------------------------------------------------------------------------------------


@dataclass
class MatrixRow:
    command: str
    command_class: str
    scenario: str
    covered_by: str  # "live" | "declaration"
    note: str = ""


@dataclass
class MatrixReport:
    rows: List[MatrixRow] = field(default_factory=list)
    undeclared: List[str] = field(default_factory=list)
    declared_absent: List[str] = field(default_factory=list)

    def rows_for(self, command: str) -> List[MatrixRow]:
        return [r for r in self.rows if r.command == command]

    def scenarios_for(self, command: str) -> set:
        return {r.scenario for r in self.rows_for(command)}

    def passing_count(self) -> int:
        return len(self.rows)


def build_matrix(parser) -> MatrixReport:
    """Build the conformance matrix report from the parser + declarations.

    - ``undeclared``: parser leaves with no ``CommandDeclaration`` (E-01 hard fail).
    - one ``MatrixRow`` per (leaf, required-scenario), marked ``live`` if the leaf is
      in ``LIVE_SAFE_LEAVES`` and the scenario is live-runnable, else ``declaration``.
    """
    report = MatrixReport()
    parser_leaves = discover_parser_leaves(parser)
    declared = {d.command for d in get_all_declarations()}
    report.undeclared = sorted(parser_leaves - declared)

    for decl in get_all_declarations():
        if decl.command == "aw":
            continue
        if decl.command not in parser_leaves and decl.command_class != "alias":
            # Declared but no longer in the parser: not a coverage row (kept out of
            # the live matrix; unreachable declarations are gated behaviorally by
            # test_command_surface_declarations.test_zero_unreachable_command_declarations,
            # while declared_absent is asserted by test_conformance_matrix_structure).
            report.declared_absent.append(decl.command)
            continue
        is_live = decl.command in LIVE_SAFE_LEAVES
        for scenario in required_scenarios(decl):
            covered_by = "live" if is_live else "declaration"
            report.rows.append(
                MatrixRow(
                    command=decl.command,
                    command_class=decl.command_class,
                    scenario=scenario,
                    covered_by=covered_by,
                )
            )
    return report

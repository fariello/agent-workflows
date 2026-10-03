"""Generated CLI output-conformance matrix (awcliux Order 05 `e8hu4s` E-01 / E-02).

Stdlib only (Python 3.9+). This module is the shared harness consumed by:

- ``test_agent_surface_conformance.py``: executes every parser leaf declaring
  an ``aw.agent/v1`` result record under ``--agent`` and verifies schema
  validity and exit code parity against the real subprocess outcome.
- ``test_exit_contract_conformance.py``: executes safe read/check leaves in
  ``LIVE_SAFE_LEAVES`` via ``run_cli`` to verify observed exit-code membership
  against declared ``exit_contract`` (IPD 1mnit8).

Former drivers (``test_cli_conformance_matrix.py`` and ``test_cli_quality_gates.py``)
were removed by test-trimming commit 19313eed7; deciding whether to revive the remainder
of the harness is tracked by open backlog item h0tiaw.

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

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

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
# Scenario vocabulary
# --------------------------------------------------------------------------------------------------

# The nine canonical output scenarios of the plan's matrix (Detailed checklist E-01):
#   TTY, non-TTY, agent, JSON, no-color, help, usage-error, domain-failure,
#   and success/preview where applicable.
SCENARIOS: Tuple[str, ...] = (
    "tty",  # human, color forced on
    "non_tty",  # human, piped (auto plain)
    "agent",  # --agent aw.agent/v1
    "json",  # --json structured
    "no_color",  # human, NO_COLOR
    "help",  # --help
    "usage_error",  # invalid flag -> exit 2
    "domain_failure",  # exit 1 findings (check/read classes that can find)
    "success_preview",  # exit 0 clean / preview (mutation/preview classes)
)


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

# Read/check leaves that are SAFE to execute live in the repo working tree: they
# never write, never touch the network, and are deterministic enough to gate on
# schema / ANSI / exit-code invariants (not on exact finding COUNTS). The value is
# the extra argv needed to make the leaf runnable non-interactively.
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
}

# Table mapping a leaf to extra argv needed to make it runnable and read-only
# (e.g. providing required positional arguments in a safe read-only manner).
RUNNABLE_ARGV: Dict[str, List[str]] = {
    "releases show": ["next"],
    "reviews decisions": ["f36de0"],
    "runs query": ["schema"],
    "show": ["f36de0"],
    "workflow validate": ["tests/fixtures/workflow-src/plan-review"],
    "workflow check-generated": ["tests/fixtures/workflow-src/plan-review"],
    "agy profile show": ["non-existent"],
    "oc profile show": ["non-existent"],
    "upgrade-test env": ["dummy"],
    "upgrade-test probe": ["dummy"],
    "partition": ["-t", "plans", "-s", "approved"],
    "graduation": ["25kzda"],
    "record-history": ["f36de0"],
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
    reason_kind: str  # "sanctioned_raw" | "known_broken" | "not_runnable"
    citation: str
    reason: str


EXEMPTION_REGISTRY: Dict[str, Exemption] = {
    # sanctioned_raw (7):
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
    "config exclude list": Exemption(
        reason_kind="sanctioned_raw",
        citation="agent_workflows/cli.py",
        reason="Emits raw list of excluded configuration variable names.",
    ),
    "index": Exemption(
        reason_kind="sanctioned_raw",
        citation="docs/cli-output-contract.md",
        reason=(
            "Rebuilds or checks indexes, outputting raw tab-separated lines or index notices "
            "rather than an envelope."
        ),
    ),
    # known_broken (3):
    "config show": Exemption(
        reason_kind="known_broken",
        citation="dtq6jr",
        reason="Crashes with ImportError: cannot import name 'format_agent_json'. Owned by open backlog item dtq6jr.",
    ),
    "config get": Exemption(
        reason_kind="known_broken",
        citation="dtq6jr",
        reason="Crashes with ImportError: cannot import name 'format_agent_json'. Owned by open backlog item dtq6jr.",
    ),
    "config is": Exemption(
        reason_kind="known_broken",
        citation="dtq6jr",
        reason="Crashes with ImportError: cannot import name 'format_agent_json'. Owned by open backlog item dtq6jr.",
    ),
    # not_runnable (16):
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
    "runs decisions": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/run_ledger_store.py",
        reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
    ),
    "runs evidence": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/run_ledger_store.py",
        reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
    ),
    "runs next": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/run_ledger_store.py",
        reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
    ),
    "runs questions": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/run_ledger_store.py",
        reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
    ),
    "runs resume": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/run_ledger_store.py",
        reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
    ),
    "runs show": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/run_ledger_store.py",
        reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
    ),
    "runs status": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/run_ledger_store.py",
        reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
    ),
    "runs verify-ledger": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/run_ledger_store.py",
        reason="Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.",
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
    "storage preflight": Exemption(
        reason_kind="not_runnable",
        citation="agent_workflows/cli.py",
        reason="Requires --companion-dir argument and does not declare or accept --agent flag (accepts --json only).",
    ),
}

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
        ),
    )
    out = proc.stdout.decode(encoding, errors="replace")
    err = proc.stderr.decode(encoding, errors="replace")
    return RunResult(
        argv=list(argv), returncode=proc.returncode, stdout=out, stderr=err
    )


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


def semantic_facts_from_human(stdout: str) -> Dict[str, object]:
    """Extract the outcome family from the standard ``HumanRenderer`` outcome banner.

    The standard render is::

        AW <command>  <target>
        <glyph> <STATUS>  <message>
        ...

    i.e. the outcome banner is the SECOND non-empty line and its leading token(s)
    are a glyph plus an UPPERCASE status word. We only trust that specific shape.
    Table / board / detail / rich renders (``list-repos``, ``attention``, ``doctor``)
    do NOT emit this banner - a per-row STATUS column word (e.g. 'STALE  /path')
    must NOT be mistaken for the outcome - so we return ``None`` and callers fall
    back to exit-code parity.
    """
    plain = ANSI_RE.sub("", stdout)
    nonempty = [ln for ln in plain.splitlines() if ln.strip()]
    if len(nonempty) < 2:
        return {"outcome_family": None}
    title = nonempty[0].strip()
    banner = nonempty[1].strip()
    # The banner only exists under a standard 'AW <command>' title line.
    if not title.startswith("AW "):
        return {"outcome_family": None}
    toks = banner.split()
    outcome: Optional[str] = None
    # STATUS is the first-or-second token (an optional leading glyph precedes it),
    # emitted uppercase, followed by the summary message.
    for tok in toks[:2]:
        raw = tok.strip()
        if raw != raw.upper():
            continue
        key = raw.lower()
        if key in _HUMAN_OUTCOME_WORDS:
            outcome = _HUMAN_OUTCOME_WORDS[key]
            break
    return {"outcome_family": outcome}


def outcome_family(agent_outcome: object) -> Optional[str]:
    """Map an agent outcome to the coarse human family for parity comparison."""
    if agent_outcome is None:
        return None
    key = str(agent_outcome)
    return _HUMAN_OUTCOME_WORDS.get(key, key)


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
            # while declared_absent is reported on MatrixReport but no longer asserted over).
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


def render_matrix_report(report: MatrixReport) -> str:
    """Render a stable text matrix report (one row per passing scenario)."""
    lines = ["command | class | scenario | covered_by"]
    for r in sorted(report.rows, key=lambda x: (x.command, x.scenario)):
        lines.append(f"{r.command} | {r.command_class} | {r.scenario} | {r.covered_by}")
    lines.append(f"# undeclared: {len(report.undeclared)}")
    lines.append(f"# rows: {len(report.rows)}")
    return "\n".join(lines) + "\n"

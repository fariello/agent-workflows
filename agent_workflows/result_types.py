"""Result types and output context for the dual-audience CLI output boundary.

awcliux Order 01 (`hd3kln`) E-01 / E-02.

Defines the standard result types (`CommandResult`, `Diagnostic`, `Change`,
`Evidence`, `NextAction`) and the root `OutputContext` / `select_output` mode
precedence resolver. Stdlib only (Python 3.9+).
"""

from __future__ import annotations

import enum
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TextIO

from agent_workflows import term as _term


class OutputMode(str, enum.Enum):
    """Output audience modes."""

    HUMAN = "human"
    AGENT = "agent"
    JSON = "json"


@dataclass
class OutputContext:
    """The root output context governing stream destinations, mode, and color styling."""

    mode: OutputMode = OutputMode.HUMAN
    color: bool = False
    explicit_format: Optional[str] = None
    stdout: Any = None
    stderr: Any = None
    limit: Optional[int] = None
    verbose: bool = False

    def __post_init__(self) -> None:
        if self.stdout is None:
            self.stdout = sys.stdout
        if self.stderr is None:
            self.stderr = sys.stderr

    @property
    def is_agent(self) -> bool:
        return self.mode == OutputMode.AGENT

    @property
    def is_human(self) -> bool:
        return self.mode == OutputMode.HUMAN

    @property
    def is_json(self) -> bool:
        return self.mode == OutputMode.JSON


def select_output(
    args: Any = None,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> OutputContext:
    """Resolve the output context according to the canonical precedence contract:

    1. Explicit format: `--json` or `--format <fmt>` -> OutputMode.JSON (explicit format context).
    2. Agent flag or non-TTY stdout: `--agent` or `not stdout.isatty()` -> OutputMode.AGENT.
       (Note: `stdin.isatty()` controls interactive prompting, NOT audience/mode).
    3. TTY stdout: -> OutputMode.HUMAN with color determined by `should_color(stdout)`.
    4. `--no-color` / `NO_COLOR` / `FORCE_COLOR` changes color styling only, not the mode.
    """
    out_stream = stdout if stdout is not None else sys.stdout
    err_stream = stderr if stderr is not None else sys.stderr

    # 1. Explicit format check
    is_explicit_json = False
    explicit_fmt = None
    if args is not None:
        if getattr(args, "as_json", False) or getattr(args, "json", False):
            is_explicit_json = True
            explicit_fmt = "json"
        elif getattr(args, "format", None) == "json":
            is_explicit_json = True
            explicit_fmt = "json"
        elif getattr(args, "format", None) is not None:
            explicit_fmt = str(args.format).lower()
            if explicit_fmt == "json":
                is_explicit_json = True

    if is_explicit_json:
        return OutputContext(
            mode=OutputMode.JSON,
            color=False,
            explicit_format=explicit_fmt,
            stdout=out_stream,
            stderr=err_stream,
        )

    # 2. Agent flag or non-TTY stdout
    is_agent_flag = False
    if args is not None:
        is_agent_flag = bool(
            getattr(args, "agent", False) or getattr(args, "as_agent", False)
        )

    is_tty = False
    try:
        is_tty = bool(out_stream.isatty())
    except Exception:
        is_tty = False

    if is_agent_flag or not is_tty:
        return OutputContext(
            mode=OutputMode.AGENT,
            color=False,
            explicit_format=None,
            stdout=out_stream,
            stderr=err_stream,
        )

    # 3. Human TTY stdout
    color_enabled = False
    if getattr(args, "no_color", False):
        color_enabled = False
    else:
        color_enabled = _term.should_color(out_stream)

    return OutputContext(
        mode=OutputMode.HUMAN,
        color=color_enabled,
        explicit_format=None,
        stdout=out_stream,
        stderr=err_stream,
    )


# --------------------------------------------------------------------------------------------------
# Result types
# --------------------------------------------------------------------------------------------------


@dataclass
class Diagnostic:
    """A single diagnostic, finding, or drift issue."""

    location: str
    rule: str
    detail: str
    severity: str = "error"  # "error", "warning", "info"
    fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "location": self.location,
            "rule": self.rule,
            "detail": self.detail,
            "severity": self.severity,
        }
        if self.fix is not None:
            res["fix"] = self.fix
        return res

    def to_drift(self) -> Any:
        """Compatibility helper converting to artifact_core.Drift."""
        from agent_workflows import artifact_core as _core

        return _core.Drift(self.location, self.rule, self.detail)

    @classmethod
    def from_drift(
        cls,
        drift: Any,
        severity: str = "error",
        fix: Optional[str] = None,
    ) -> Diagnostic:
        """Construct from an artifact_core.Drift namedtuple."""
        return cls(
            location=drift.location,
            rule=drift.rule,
            detail=drift.detail,
            severity=severity,
            fix=fix,
        )


@dataclass
class Change:
    """A mutation change record (applied or previewed)."""

    path: str
    kind: str  # "modify", "create", "delete", "rename"
    detail: str = ""
    applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "detail": self.detail,
            "applied": self.applied,
        }


@dataclass
class Evidence:
    """An evidence receipt item verifying check/probe status."""

    key: str
    value: Any
    status: str = "verified"  # "verified", "unverified", "pass", "fail", "clean"
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass
class NextAction:
    """A suggested next command action."""

    command: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        res = {"command": self.command}
        if self.description:
            res["description"] = self.description
        return res


@dataclass
class CommandResult:
    """Typed outcome facts for any CLI command invocation.

    Consumable by both HumanRenderer and AgentRenderer without loss of facts or
    divergent exit classification.
    """

    command: str
    status: str = (
        "clean"  # "clean", "ok", "findings", "fail", "preview", "stale", "error"
    )
    exit_code: int = 0  # 0: clean, 1: findings/domain failure, 2: usage/cannot-run
    summary: str = ""
    diagnostics: List[Diagnostic] = field(default_factory=list)
    changes: List[Change] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    next_actions: List[NextAction] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    verified: bool = True
    complete: bool = True
    schema_version: str = "aw.agent/v1"

    @property
    def has_findings(self) -> bool:
        return self.exit_code == 1 or len(self.diagnostics) > 0

    @property
    def is_error(self) -> bool:
        return self.exit_code == 2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema_version,
            "command": self.command,
            "status": self.status,
            "exit_code": self.exit_code,
            "summary": self.summary,
            "verified": self.verified,
            "complete": self.complete,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "changes": [c.to_dict() for c in self.changes],
            "evidence": [e.to_dict() for e in self.evidence],
            "next_actions": [n.to_dict() for n in self.next_actions],
            "data": dict(self.data),
        }

    def to_agent_record(self) -> Dict[str, Any]:
        """Convert into canonical aw.agent/v1 compact record structure."""
        rec: Dict[str, Any] = {
            "schema": self.schema_version,
            "kind": "result",
            "cmd": self.command,
            "outcome": self.status,
            "exit": self.exit_code,
            "summary": self.summary,
            "findings": len(self.diagnostics),
            "verified": self.verified,
            "complete": self.complete,
        }
        if self.diagnostics:
            rec["diagnostics"] = [d.to_dict() for d in self.diagnostics]
        if self.changes:
            rec["changes"] = [c.to_dict() for c in self.changes]
        if self.evidence:
            rec["evidence"] = [e.to_dict() for e in self.evidence]
        if self.next_actions:
            rec["next"] = self.next_actions[0].command
        return rec

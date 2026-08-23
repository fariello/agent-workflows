"""Result types and output context for the dual-audience CLI output boundary.

awcliux Order 01 (`hd3kln`) E-01 / E-02, Order 03 (`8su0r3`) E-01 / E-02 / E-03.

Defines the standard result types (`CommandResult`, `Diagnostic`, `Change`,
`Evidence`, `NextAction`) and the root `OutputContext` / `select_output` mode
precedence resolver. Stdlib only (Python 3.9+).
"""

from __future__ import annotations

import enum
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Union

from agent_workflows import agent_schema as _schema
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
    fields: Optional[List[str]] = None

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


class ConflictingFlagsError(ValueError):
    """Raised when conflicting explicit output format flags (e.g. --agent and --json) are passed."""


def select_output(
    args: Any = None,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> OutputContext:
    """Resolve the output context according to the canonical precedence contract:

    1. Explicit format conflict check (OQ-01 / Order 04 E-03): cannot combine --agent and --json/--format.
    2. Explicit format: `--json` or `--format <fmt>` -> OutputMode.JSON (explicit format context).
    3. Agent flag or non-TTY stdout: `--agent` or `not stdout.isatty()` -> OutputMode.AGENT.
       (Note: `stdin.isatty()` controls interactive prompting, NOT audience/mode).
    4. TTY stdout: -> OutputMode.HUMAN with color determined by `should_color(stdout)`.
    5. `--no-color` / `NO_COLOR` / `FORCE_COLOR` changes color styling only, not the mode.
    """
    out_stream = stdout if stdout is not None else sys.stdout
    err_stream = stderr if stderr is not None else sys.stderr

    # Extract limit, verbose, and fields if provided on args
    limit_val: Optional[int] = None
    verbose_val: bool = False
    fields_val: Optional[List[str]] = None

    if args is not None:
        raw_limit = getattr(args, "limit", None)
        if raw_limit is not None:
            try:
                limit_val = int(raw_limit)
            except (ValueError, TypeError):
                limit_val = None
        verbose_val = bool(getattr(args, "verbose", False))
        raw_fields = getattr(args, "fields", None)
        if isinstance(raw_fields, str):
            fields_val = [f.strip() for f in raw_fields.split(",") if f.strip()]
        elif isinstance(raw_fields, (list, tuple, set)):
            fields_val = [str(f).strip() for f in raw_fields if str(f).strip()]

    # Format conflict detection (OQ-01 / Order 04 E-03)
    is_agent_flag = False
    is_explicit_json = False
    explicit_fmt = None

    if args is not None:
        is_agent_flag = bool(
            getattr(args, "agent", False) or getattr(args, "as_agent", False)
        )
        if getattr(args, "as_json", False) or getattr(args, "json", False):
            is_explicit_json = True
            explicit_fmt = "json"
        raw_fmt = getattr(args, "format", None)
        if raw_fmt is not None:
            explicit_fmt = str(raw_fmt).lower()
            if explicit_fmt == "json":
                is_explicit_json = True

        if is_agent_flag and is_explicit_json:
            raise ConflictingFlagsError(
                "conflicting output format flags: cannot combine --agent and --json"
            )
        if is_agent_flag and explicit_fmt is not None and explicit_fmt != "agent":
            raise ConflictingFlagsError(
                f"conflicting output format flags: cannot combine --agent and --format {raw_fmt}"
            )
        if is_explicit_json and explicit_fmt is not None and explicit_fmt != "json":
            raise ConflictingFlagsError(
                f"conflicting output format flags: cannot combine --json and --format {raw_fmt}"
            )

    if is_explicit_json:
        return OutputContext(
            mode=OutputMode.JSON,
            color=False,
            explicit_format=explicit_fmt,
            stdout=out_stream,
            stderr=err_stream,
            limit=limit_val,
            verbose=verbose_val,
            fields=fields_val,
        )

    if is_agent_flag or explicit_fmt == "agent":
        return OutputContext(
            mode=OutputMode.AGENT,
            color=False,
            explicit_format=explicit_fmt,
            stdout=out_stream,
            stderr=err_stream,
            limit=limit_val,
            verbose=verbose_val,
            fields=fields_val,
        )

    # Human stdout (color enabled if should_color(stream) is True, disabled if non-TTY/NO_COLOR/--no-color)
    color_enabled = False
    if not getattr(args, "no_color", False):
        color_enabled = _term.should_color(out_stream)

    return OutputContext(
        mode=OutputMode.HUMAN,
        color=color_enabled,
        explicit_format=None,
        stdout=out_stream,
        stderr=err_stream,
        limit=limit_val,
        verbose=verbose_val,
        fields=fields_val,
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

    def to_dict(self, repo_root: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "location": _schema.normalize_repo_path(self.location, repo_root),
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

    def to_dict(self, repo_root: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        return {
            "path": _schema.normalize_repo_path(self.path, repo_root),
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

    def to_dict(self, repo_root: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
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
    status: str = "clean"  # "clean", "ok", "findings", "fail", "preview", "stale", "error", "skipped", "partial", "unverified", "cannot-run"
    exit_code: int = 0  # 0: clean, 1: findings/domain failure, 2: usage/cannot-run
    summary: str = ""
    diagnostics: List[Diagnostic] = field(default_factory=list)
    changes: List[Change] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    next_actions: List[NextAction] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    verified: bool = True
    complete: bool = True
    applied: Optional[bool] = None
    target: Optional[str] = None
    schema_version: str = _schema.SCHEMA_VERSION

    @property
    def has_findings(self) -> bool:
        return self.exit_code == 1 or len(self.diagnostics) > 0

    @property
    def is_error(self) -> bool:
        return self.exit_code == 2

    def to_dict(self) -> Dict[str, Any]:
        repo_root = self.data.get("repo_root")
        return {
            "schema": self.schema_version,
            "command": self.command,
            "status": self.status,
            "exit_code": self.exit_code,
            "summary": self.summary,
            "verified": self.verified,
            "complete": self.complete,
            "diagnostics": [d.to_dict(repo_root) for d in self.diagnostics],
            "changes": [c.to_dict(repo_root) for c in self.changes],
            "evidence": [e.to_dict(repo_root) for e in self.evidence],
            "next_actions": [n.to_dict() for n in self.next_actions],
            "data": dict(self.data),
        }

    def to_agent_record(
        self, context: Optional[OutputContext] = None
    ) -> Dict[str, Any]:
        """Convert into canonical aw.agent/v1 compact record structure (Order 03)."""
        repo_root = self.data.get("repo_root")
        is_verbose = context.verbose if context is not None else False

        # Resolve outcome & enforce anti-greenwashing invariants
        outcome = self.status
        is_error = self.exit_code == 2 or self.status in ("error", "cannot-run")
        if is_error:
            outcome = "cannot-run" if self.status == "cannot-run" else "error"
            kind = "error"
            complete = False
            verified = False
        else:
            kind = "result"
            complete = self.complete
            verified = self.verified
            if self.status in ("clean", "ok", "conforms"):
                if not verified:
                    outcome = "unverified"
                elif (
                    not complete
                    and self.status != "preview"
                    and self.applied is not False
                ):
                    outcome = "partial"
                elif self.exit_code == 1:
                    outcome = "findings"
                else:
                    outcome = self.status
            elif self.status in ("findings", "fail"):
                outcome = self.status

        # Resolve target
        target_val = self.target or self.data.get("target")
        norm_target = (
            _schema.normalize_repo_path(target_val, repo_root) if target_val else None
        )

        # Build base record
        rec: Dict[str, Any] = {
            "schema": self.schema_version,
            "kind": kind,
            "cmd": self.command,
            "outcome": outcome,
            "exit": self.exit_code,
            "verified": verified,
            "complete": complete,
        }

        # Resolve applied
        if self.applied is not None:
            rec["applied"] = self.applied
        elif "applied" in self.data:
            rec["applied"] = bool(self.data["applied"])
        elif (
            outcome == "preview"
            or self.changes
            and any(not c.applied for c in self.changes)
        ):
            rec["applied"] = False

        if norm_target:
            rec["target"] = norm_target

        # Checked count
        checked_count = self.data.get("checked") or self.data.get("total_checked")
        if checked_count is not None:
            try:
                rec["checked"] = int(checked_count)
            except (ValueError, TypeError):
                pass

        # Findings count
        findings_count = (
            len(self.diagnostics) if self.diagnostics else self.data.get("findings", 0)
        )
        rec["findings"] = int(findings_count)

        # Changes
        if self.changes:
            if is_verbose:
                rec["changes"] = [c.to_dict(repo_root) for c in self.changes]
            else:
                if len(self.changes) > 5:
                    rec["changes"] = len(self.changes)
                else:
                    rec["changes"] = [
                        {
                            "kind": c.kind,
                            "path": _schema.normalize_repo_path(c.path, repo_root),
                        }
                        for c in self.changes
                    ]

        # Evidence
        if self.evidence:
            if is_verbose:
                rec["evidence"] = [e.to_dict(repo_root) for e in self.evidence]
            else:
                rec["evidence"] = [
                    _schema.sanitize_evidence_item(e, repo_root) for e in self.evidence
                ]

        # Diagnostics (omitted in compact if clean)
        if self.diagnostics:
            if is_verbose:
                rec["diagnostics"] = [d.to_dict(repo_root) for d in self.diagnostics]
            else:
                rec["diagnostics"] = [
                    {
                        "location": _schema.normalize_repo_path(d.location, repo_root),
                        "rule": d.rule,
                    }
                    for d in self.diagnostics
                ]

        # Safe next command
        if self.next_actions:
            rec["next"] = self.next_actions[0].command
        else:
            rec["next"] = None

        # Field filtering (Token control `--fields`)
        if context is not None and context.fields:
            rec = _schema.filter_record_fields(rec, context.fields)

        # Validate against schema invariants
        _schema.assert_valid_agent_record(rec)

        return rec

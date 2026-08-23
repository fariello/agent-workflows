"""Dual-audience renderers consuming typed CommandResult facts.

awcliux Order 01 (`hd3kln`) E-01 / E-02.

Provides the renderer interface and concrete renderers (HumanRenderer, AgentRenderer,
JsonRenderer) that consume identical facts and exit classifications from one CommandResult.
Stdlib only (Python 3.9+).
"""

from __future__ import annotations

import abc
import json
from typing import List, Optional

from agent_workflows import term as _term
from agent_workflows.result_types import (
    CommandResult,
    OutputContext,
    OutputMode,
)


class BaseRenderer(abc.ABC):
    """Abstract base renderer interface consuming a CommandResult and OutputContext."""

    @abc.abstractmethod
    def render(
        self, result: CommandResult, context: Optional[OutputContext] = None
    ) -> str:
        """Render the typed result into a string payload for this audience."""
        raise NotImplementedError

    def emit(
        self, result: CommandResult, context: Optional[OutputContext] = None
    ) -> int:
        """Render the typed result to the context stream and return the exit code."""
        ctx = context or OutputContext()
        text = self.render(result, ctx)
        if text:
            try:
                ctx.stdout.write(text)
                ctx.stdout.flush()
            except (BrokenPipeError, OSError):
                pass
        return result.exit_code


class HumanRenderer(BaseRenderer):
    """Human-facing interactive terminal renderer."""

    def render(
        self, result: CommandResult, context: Optional[OutputContext] = None
    ) -> str:
        ctx = context or OutputContext(mode=OutputMode.HUMAN)
        term = _term.Term(color=ctx.color)

        # If the result embeds a pre-rendered human report or specific doctor report handler
        if "human_rendered" in result.data:
            return str(result.data["human_rendered"])

        if "report" in result.data and result.command == "doctor":
            from agent_workflows import doctor as _doctor

            return _doctor.render_human_report(result.data["report"], term)

        lines: List[str] = []
        # Header / Status line
        status_word = result.status.upper()
        if result.exit_code == 0:
            status_badge = (
                term.colorize(f"[{status_word}]", "green")
                if ctx.color
                else f"[{status_word}]"
            )
        elif result.exit_code == 1:
            status_badge = (
                term.colorize(f"[{status_word}]", "yellow")
                if ctx.color
                else f"[{status_word}]"
            )
        else:
            status_badge = (
                term.colorize(f"[{status_word}]", "red")
                if ctx.color
                else f"[{status_word}]"
            )

        cmd_title = (
            term.colorize(f"aw {result.command}", "bold")
            if ctx.color
            else f"aw {result.command}"
        )
        summary_txt = f": {result.summary}" if result.summary else ""
        lines.append(f"{cmd_title} {status_badge}{summary_txt}")

        # Diagnostics / Findings
        if result.diagnostics:
            lines.append("")
            hdr = term.colorize("Findings:", "bold") if ctx.color else "Findings:"
            lines.append(hdr)
            for d in result.diagnostics:
                loc_txt = term.colorize(d.location, "cyan") if ctx.color else d.location
                rule_txt = f"[{d.rule}]"
                sev_color = "red" if d.severity == "error" else "yellow"
                rule_badge = (
                    term.colorize(rule_txt, sev_color) if ctx.color else rule_txt
                )
                lines.append(f"  - {loc_txt}: {rule_badge} {d.detail}")
                if d.fix:
                    fix_txt = (
                        term.colorize(f"Fix: {d.fix}", "green")
                        if ctx.color
                        else f"Fix: {d.fix}"
                    )
                    lines.append(f"      {fix_txt}")

        # Changes
        if result.changes:
            lines.append("")
            hdr = term.colorize("Changes:", "bold") if ctx.color else "Changes:"
            lines.append(hdr)
            for c in result.changes:
                status_ch = "applied" if c.applied else "would change"
                lines.append(f"  - [{c.kind}] {c.path} ({status_ch}): {c.detail}")

        # Evidence
        if result.evidence:
            lines.append("")
            hdr = term.colorize("Evidence:", "bold") if ctx.color else "Evidence:"
            lines.append(hdr)
            for e in result.evidence:
                val_repr = str(e.value)
                lines.append(f"  - {e.key}: {val_repr} ({e.status})")

        # Next actions
        if result.next_actions:
            lines.append("")
            hdr = term.colorize("Next action:", "bold") if ctx.color else "Next action:"
            lines.append(hdr)
            for act in result.next_actions:
                cmd_txt = (
                    term.colorize(act.command, "cyan") if ctx.color else act.command
                )
                lines.append(f"  {cmd_txt}")

        return "\n".join(lines) + "\n"


class AgentRenderer(BaseRenderer):
    """Agent-facing compact aw.agent/v1 JSONL renderer."""

    def render(
        self, result: CommandResult, context: Optional[OutputContext] = None
    ) -> str:
        rec = result.to_agent_record()
        # Single-line compact JSON, newline-terminated
        return json.dumps(rec, separators=(",", ":")) + "\n"


class JsonRenderer(BaseRenderer):
    """Explicit structured JSON renderer with full detail."""

    def render(
        self, result: CommandResult, context: Optional[OutputContext] = None
    ) -> str:
        return json.dumps(result.to_dict(), indent=2) + "\n"


def get_renderer(context: OutputContext) -> BaseRenderer:
    """Factory returning the canonical renderer for the given OutputContext."""
    if context.is_json:
        return JsonRenderer()
    if context.is_agent:
        return AgentRenderer()
    return HumanRenderer()

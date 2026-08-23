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

        # 1. Top Title banner
        target_str = str(result.data.get("target") or "")
        elapsed_ms = result.data.get("elapsed_ms")
        title_line = term.format_title(
            result.command,
            target=target_str,
            elapsed_ms=elapsed_ms,
            width=80,
        )
        lines.append(title_line)

        # 2. Outcome banner
        outcome_status = result.status
        if result.exit_code == 0 and outcome_status in ("clean", "ok"):
            outcome_status = "conforms"
        elif result.exit_code == 1 and outcome_status in ("clean", "ok"):
            outcome_status = "findings"
        elif result.exit_code == 2 and outcome_status in ("clean", "ok"):
            outcome_status = "error"
        outcome_line = term.format_outcome(outcome_status, result.summary)
        lines.append(outcome_line)

        # 3. Diagnostics / Findings (doctor-derived grouping & severity labels)
        if result.diagnostics:
            lines.append("")
            lines.append(term.format_section("Findings:"))
            from agent_workflows import doctor as _doctor
            from pathlib import Path

            repo_root = Path(result.data.get("repo_root") or ".")
            groups: dict = {}
            for d in result.diagnostics:
                drift_obj = d.to_drift() if hasattr(d, "to_drift") else d
                try:
                    title, dir_str, fname, extra, fix = _doctor._categorize_drift(
                        drift_obj, repo_root
                    )
                except Exception:
                    title, dir_str, fname, extra, fix = (
                        d.rule,
                        "",
                        d.location,
                        "",
                        d.fix,
                    )
                fix_action = d.fix or fix
                key = (title, fix_action)
                if key not in groups:
                    groups[key] = {}
                if dir_str not in groups[key]:
                    groups[key][dir_str] = []
                groups[key][dir_str].append((fname, extra, d.severity))

            for (title, fix_action), dir_map in groups.items():
                lines.append(f"  {term.color256('Issue: ' + title, 214, bold=True)}")
                for dir_str, files in dir_map.items():
                    if dir_str and dir_str != ".":
                        lines.append(f"  - {term.format_path(dir_str)}")
                    for idx, (fname, extra, sev) in enumerate(files, 1):
                        badge = term.badge(sev.upper(), sev)
                        if dir_str and dir_str != ".":
                            item_line = f"    {idx}. {fname}"
                        else:
                            item_line = f"  - {term.format_path(fname)} {badge}"
                        if extra:
                            item_line += f"\n       {term.color256('-> ' + extra, 244)}"
                        lines.append(item_line)
                if fix_action:
                    lines.append(f"    {term.format_fix(fix_action)}")
                lines.append("")

        # 4. Changes / Mutation Preview
        if result.changes:
            lines.append("")
            hdr_text = (
                "Would change:"
                if any(not c.applied for c in result.changes)
                else "Changes:"
            )
            lines.append(term.format_section(hdr_text))
            for c in result.changes:
                lines.append(term.format_preview(c.kind, c.path, detail=c.detail))

        # 5. Evidence
        if result.evidence:
            lines.append("")
            lines.append(term.format_section("Evidence"))
            for e in result.evidence:
                if isinstance(e.value, dict):
                    # Format scalar key/vals as an evidence grid line
                    grid_items = [
                        (k, v)
                        for k, v in e.value.items()
                        if not isinstance(v, (dict, list))
                    ]
                    if grid_items:
                        lines.append(term.format_evidence_grid(grid_items))
                    else:
                        lines.append(
                            term.format_evidence(e.key, e.value, e.status, e.detail)
                        )
                else:
                    lines.append(
                        term.format_evidence(e.key, e.value, e.status, e.detail)
                    )

        # 6. Next Actions
        if result.next_actions:
            lines.append("")
            for act in result.next_actions:
                lines.append(term.format_next_action(act.command, act.description))

        # 7. Agent Output Hint
        if not result.data.get("suppress_agent_hint", False):
            lines.append("Agent output: --agent (automatic when piped)")

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

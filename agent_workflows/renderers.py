"""Dual-audience renderers consuming typed CommandResult facts.

awcliux Order 01 (`hd3kln`) E-01 / E-02, Order 03 (`8su0r3`) E-01 / E-02 / E-03.

Provides the renderer interface and concrete renderers (HumanRenderer, AgentRenderer,
JsonRenderer) that consume identical facts and exit classifications from one CommandResult.
Stdlib only (Python 3.9+).
"""

from __future__ import annotations

import abc
import json
from typing import Any, Dict, List, Optional, Sequence

from agent_workflows import agent_schema as _schema
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
    """Agent-facing compact aw.agent/v1 JSONL renderer (Order 01/03)."""

    def render(
        self, result: CommandResult, context: Optional[OutputContext] = None
    ) -> str:
        rec = result.to_agent_record(context)
        return _schema.render_jsonl_record(rec)

    def render_item(
        self, item: Dict[str, Any], cmd: str, context: Optional[OutputContext] = None
    ) -> str:
        """Render a single stream item record."""
        rec: Dict[str, Any] = {
            "schema": _schema.SCHEMA_VERSION,
            "kind": "item",
            "cmd": cmd,
            **item,
        }
        if context and context.fields:
            rec = _schema.filter_record_fields(rec, context.fields)
        return _schema.render_jsonl_record(rec)

    def render_summary(
        self,
        cmd: str,
        total: int,
        emitted: int,
        omitted: int,
        outcome: str = "clean",
        exit_code: int = 0,
        next_cmd: Optional[str] = None,
        complete: bool = True,
        context: Optional[OutputContext] = None,
    ) -> str:
        """Render a stream summary record."""
        rec: Dict[str, Any] = {
            "schema": _schema.SCHEMA_VERSION,
            "kind": "summary",
            "cmd": cmd,
            "outcome": outcome,
            "exit": exit_code,
            "total": total,
            "emitted": emitted,
            "omitted": omitted,
            "complete": complete,
        }
        if next_cmd is not None:
            rec["next"] = next_cmd
        if context and context.fields:
            rec = _schema.filter_record_fields(rec, context.fields)
        return _schema.render_jsonl_record(rec)

    def render_stream(
        self,
        items: Sequence[Dict[str, Any]],
        cmd: str,
        context: Optional[OutputContext] = None,
        total: Optional[int] = None,
        next_template: Optional[str] = None,
        outcome: str = "clean",
        exit_code: int = 0,
    ) -> str:
        """Render a stream of items with summary record under --limit / token budgets."""
        ctx = context or OutputContext(mode=OutputMode.AGENT)
        all_items = list(items)
        tot = total if total is not None else len(all_items)
        limit = ctx.limit

        if limit is not None and limit < len(all_items):
            emitted_items = all_items[:limit]
            omitted = tot - len(emitted_items)
            complete = False
            next_cmd = (
                next_template.format(limit=tot)
                if next_template
                else f"aw {cmd} --agent --limit {tot}"
            )
        else:
            emitted_items = all_items
            omitted = 0
            complete = True
            next_cmd = None

        lines: List[str] = []
        for it in emitted_items:
            lines.append(self.render_item(it, cmd, ctx))
        lines.append(
            self.render_summary(
                cmd,
                total=tot,
                emitted=len(emitted_items),
                omitted=omitted,
                outcome=outcome,
                exit_code=exit_code,
                next_cmd=next_cmd,
                complete=complete,
                context=ctx,
            )
        )
        return "".join(lines)


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

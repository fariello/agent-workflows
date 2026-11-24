"""Step-4 log builder and file rewrite for migration m0001 (all record types + review events).

Implements spec 4sd62s Section 4.1, 4.1a, 4.2, 4.2a, 4.2b, 4.2c, 4.5c, and Section 5.2
step 4 for plans (``ipd``), backlog items (``backlog``), releases (``release``),
specs (``spec``), staged prompts (``prompt``), research records (``research``),
walkthroughs (``walkthrough``), roadmaps (``roadmap``), and review files (``review``
events in their subject's log plus compact review front matter).

Comms, ``.data/`` files, READMEs, and the six templates stay byte-identical.

All in-file mirrors and banners are rendered through ``artifact_meta`` so the
migration and post-cutover writer never disagree.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple, Union

from agent_workflows import (
    artifact_core,
    artifact_meta,
    artifact_naming,
    attention_contract,
    layout_migration,
    project_context,
    review_findings,
)
from agent_workflows.migrations import m0001_discover, m0001_renames

FIVE_RECORD_TYPES: Tuple[str, ...] = ("ipd", "backlog", "release", "spec", "prompt")
REMAINING_RECORD_TYPES: Tuple[str, ...] = ("research", "walkthrough", "roadmap")
ALL_RECORD_TYPES: Tuple[str, ...] = FIVE_RECORD_TYPES + REMAINING_RECORD_TYPES

TREE_DIR_TO_TYPE: Dict[str, str] = {
    "plans": "ipd",
    "backlog": "backlog",
    "releases": "release",
    "specs": "spec",
    "prompts": "prompt",
    "research": "research",
    "walkthroughs": "walkthrough",
    "roadmaps": "roadmap",
}

PROSE_BODY_FIELDS: Tuple[str, ...] = (
    "Summary",
    "Scope",
    "Concern",
    "Motivation",
    "Relation to prior work",
)

_BULLET_LINE_RE = re.compile(r"^-\s*([A-Za-z][A-Za-z0-9 /-]*?):\s*(.*)$")
_PROMPT_COMMENT_RE = re.compile(r"\A<!--\s*aw-prompt:\s*(.*?)\s*-->", re.DOTALL)
_FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
_H1_RE = re.compile(r"^#\s+.+$")
_H2_PLUS_RE = re.compile(r"^#{2,6}\s+")
_YYYYMMDD_RE = re.compile(r"\A(\d{4})(\d{2})(\d{2})\Z")
_YYYY_MM_DD_RE = re.compile(r"\A\d{4}-\d{2}-\d{2}\Z")
_DATED_PREFIX_RE = re.compile(r"^-\s*(\d{4}-\d{2}-\d{2})(?:[:/\s]|$)")

_EXCLUDED_DIRNAMES = m0001_discover.EXCLUDED_DIRNAMES
_EXCLUDED_FILENAMES = frozenset({"README.md", "STATUS.md"})


@dataclass(frozen=True)
class FieldDestination:
    """Explicit 4.2/4.5c destination for one legacy field key on one record type."""

    kind: str  # identity | status | log_field | body_section | prompt_body | comment_value
    target: str
    note: str = ""


def _build_field_destinations() -> Dict[str, Dict[str, FieldDestination]]:
    """Return the explicit per-type destination map for every key of the five types."""
    common_ipd_spec_prose = {
        "Summary": FieldDestination("body_section", "Summary", "prose moved to body"),
        "Scope": FieldDestination("body_section", "Scope", "prose moved to body"),
        "Concern": FieldDestination("body_section", "Concern", "prose moved to body"),
        "Motivation": FieldDestination(
            "body_section", "Motivation", "prose moved to body"
        ),
        "Relation to prior work": FieldDestination(
            "body_section", "Relation to prior work", "prose moved to body"
        ),
    }

    ipd_map: Dict[str, FieldDestination] = {
        "Id": FieldDestination("identity", "id", "checkpoint identity and mirror"),
        "Status": FieldDestination("status", "status", "checkpoint status and mirror"),
        "Date": FieldDestination(
            "log_field", "created_day", "legacy creation day on local clock"
        ),
        "Kind": FieldDestination("log_field", "plan_role", "4.5c rename from Kind"),
        "Set": FieldDestination("log_field", "set", "terse set id"),
        "Order": FieldDestination("log_field", "order", "integer order"),
        "Work-Kind": FieldDestination("log_field", "work_kind", "registry field"),
        "Priority": FieldDestination("log_field", "priority", "registry field"),
        "Readiness": FieldDestination("log_field", "readiness", "registry field"),
        "Approval": FieldDestination("log_field", "approval", "registry field"),
        "Coverage": FieldDestination("log_field", "coverage", "registry field"),
        "Coverage-Fingerprint": FieldDestination(
            "log_field", "coverage_fingerprint", "registry field"
        ),
        "Coverage-Checked": FieldDestination(
            "log_field", "coverage_checked", "migration-only field"
        ),
        "Review-Depth": FieldDestination("log_field", "review_depth", "registry field"),
        "Pipeline": FieldDestination("log_field", "pipeline", "registry field"),
        "Attended": FieldDestination("log_field", "attended", "registry field"),
        "Item-Dependencies": FieldDestination(
            "log_field",
            "item_dependencies",
            "parsed into dependency_declaration and structured conditions",
        ),
        "Blocks-Release": FieldDestination(
            "log_field", "blocks_release", "registry field"
        ),
        "From-Backlog": FieldDestination("log_field", "from_backlog", "registry field"),
        "From-Spec": FieldDestination("log_field", "from_spec", "registry field"),
        "From-Plan": FieldDestination("log_field", "from_plan", "registry field"),
        "Supersedes": FieldDestination("log_field", "supersedes", "registry field"),
        "Scope-Paths": FieldDestination("log_field", "scope_paths", "string list"),
        "Scope-Exceeded": FieldDestination(
            "log_field",
            "scope_result",
            "sets scope_result='exceeded', out_of_scope_paths, and scope_exceeded_raw",
        ),
        "Author": FieldDestination("log_field", "author", "registry field"),
        "Highest E allocated": FieldDestination(
            "log_field", "highest_e_allocated", "registry field"
        ),
        "Short-Description": FieldDestination(
            "log_field", "short_description", "registry field"
        ),
        "Note": FieldDestination(
            "body_section", "Note", "legacy one-off bullet preserved in body"
        ),
        "Origin": FieldDestination(
            "body_section", "Origin", "legacy one-off bullet preserved in body"
        ),
        "Self-note": FieldDestination(
            "body_section", "Self-note", "legacy one-off bullet preserved in body"
        ),
        "Run record": FieldDestination(
            "body_section", "Run record", "legacy one-off bullet preserved in body"
        ),
        "Source spec": FieldDestination(
            "body_section", "Source spec", "legacy one-off bullet preserved in body"
        ),
        "Supersedes-Note": FieldDestination(
            "body_section",
            "Supersedes-Note",
            "legacy one-off bullet preserved in body",
        ),
        **common_ipd_spec_prose,
    }

    backlog_map: Dict[str, FieldDestination] = {
        "Id": FieldDestination("identity", "id", "checkpoint identity and mirror"),
        "Status": FieldDestination("status", "status", "checkpoint status and mirror"),
        "Set": FieldDestination("log_field", "set", "terse set id"),
        "Priority": FieldDestination("log_field", "priority", "registry field"),
        "Work-Kind": FieldDestination("log_field", "work_kind", "registry field"),
        "Kind": FieldDestination(
            "log_field", "work_kind", "legacy backlog Kind -> work_kind"
        ),
        "Close-Evidence": FieldDestination(
            "log_field", "close_evidence", "registry field"
        ),
        "Release-Exempt-Kind": FieldDestination(
            "log_field", "release_exempt_kind", "registry field"
        ),
        "Release-Exempt-Ref": FieldDestination(
            "log_field", "release_exempt_ref", "registry field"
        ),
        "Gate-Kind": FieldDestination("log_field", "gate_kind", "registry field"),
        "Gate-Ref": FieldDestination("log_field", "gate_ref", "registry field"),
        "Gate-Summary": FieldDestination("log_field", "gate_summary", "registry field"),
        "Blocks-Release": FieldDestination(
            "log_field", "blocks_release", "registry field"
        ),
        "Graduated-To": FieldDestination("log_field", "graduated_to", "string list"),
        "Short-Description": FieldDestination(
            "log_field", "short_description", "registry field"
        ),
        **common_ipd_spec_prose,
    }

    release_map: Dict[str, FieldDestination] = {
        "Id": FieldDestination("identity", "id", "checkpoint identity and mirror"),
        "Status": FieldDestination("status", "status", "checkpoint status and mirror"),
        "Set": FieldDestination("log_field", "set", "terse set id"),
        "Order": FieldDestination("log_field", "order", "integer order"),
        "Version": FieldDestination("log_field", "version", "registry field"),
        "Short-Description": FieldDestination(
            "log_field", "short_description", "registry field"
        ),
        **common_ipd_spec_prose,
    }

    spec_map: Dict[str, FieldDestination] = {
        "Id": FieldDestination("identity", "id", "checkpoint identity and mirror"),
        "Status": FieldDestination("status", "status", "checkpoint status and mirror"),
        "Date": FieldDestination(
            "log_field", "created_day", "legacy creation day on local clock"
        ),
        "Set": FieldDestination("log_field", "set", "terse set id"),
        "Order": FieldDestination("log_field", "order", "integer order"),
        "Work-Kind": FieldDestination("log_field", "work_kind", "registry field"),
        "Priority": FieldDestination("log_field", "priority", "registry field"),
        "Blocks-Release": FieldDestination(
            "log_field", "blocks_release", "registry field"
        ),
        "From-Backlog": FieldDestination("log_field", "from_backlog", "registry field"),
        "From-Spec": FieldDestination("log_field", "from_spec", "registry field"),
        "Supersedes": FieldDestination("log_field", "supersedes", "registry field"),
        "Gate-Kind": FieldDestination("log_field", "gate_kind", "registry field"),
        "Gate-Ref": FieldDestination("log_field", "gate_ref", "registry field"),
        "Gate-Summary": FieldDestination("log_field", "gate_summary", "registry field"),
        "Author": FieldDestination("log_field", "author", "registry field"),
        "Canonical": FieldDestination("log_field", "canonical", "registry field"),
        "Implemented": FieldDestination(
            "log_field", "implemented", "migration-only field"
        ),
        "Short-Description": FieldDestination(
            "log_field", "short_description", "registry field"
        ),
        "Constrained-by": FieldDestination(
            "body_section",
            "Constrained-by",
            "legacy spec bullet preserved in body",
        ),
        "Evidence": FieldDestination(
            "body_section", "Evidence", "legacy spec bullet preserved in body"
        ),
        "Extends": FieldDestination(
            "body_section", "Extends", "legacy spec bullet preserved in body"
        ),
        "From-Plan": FieldDestination(
            "body_section", "From-Plan", "legacy spec bullet preserved in body"
        ),
        "Graduated-To": FieldDestination(
            "body_section", "Graduated-To", "legacy spec bullet preserved in body"
        ),
        "Grounding": FieldDestination(
            "body_section", "Grounding", "legacy spec bullet preserved in body"
        ),
        "Implemented-by": FieldDestination(
            "body_section",
            "Implemented-by",
            "legacy spec bullet preserved in body",
        ),
        "Origin": FieldDestination(
            "body_section", "Origin", "legacy spec bullet preserved in body"
        ),
        "Parent": FieldDestination(
            "body_section", "Parent", "legacy spec bullet preserved in body"
        ),
        "Related": FieldDestination(
            "body_section", "Related", "legacy spec bullet preserved in body"
        ),
        "Sources": FieldDestination(
            "body_section", "Sources", "legacy spec bullet preserved in body"
        ),
        "Implementation Set": FieldDestination(
            "body_section",
            "Implementation Set",
            "legacy spec bullet preserved in body",
        ),
        "Implementation state": FieldDestination(
            "body_section",
            "Implementation state",
            "legacy spec bullet preserved in body",
        ),
        "Related specifications": FieldDestination(
            "body_section",
            "Related specifications",
            "legacy spec bullet preserved in body",
        ),
        "Relation to prior specs": FieldDestination(
            "body_section",
            "Relation to prior specs",
            "legacy spec bullet preserved in body",
        ),
        "Revised by": FieldDestination(
            "body_section", "Revised by", "legacy spec bullet preserved in body"
        ),
        "Supersedes/extends": FieldDestination(
            "body_section",
            "Supersedes/extends",
            "legacy spec bullet preserved in body",
        ),
        **common_ipd_spec_prose,
    }

    prompt_map: Dict[str, FieldDestination] = {
        "Id": FieldDestination("identity", "id", "aw-prompt comment id"),
        "Status": FieldDestination("status", "status", "aw-prompt comment status"),
        "Kind": FieldDestination("log_field", "prompt_kind", "4.5c rename from Kind"),
        "Created": FieldDestination(
            "log_field", "created_day", "aw-prompt Created day on local clock"
        ),
        "Set": FieldDestination("log_field", "set", "terse set id"),
        "Author": FieldDestination("log_field", "author", "registry field"),
        "Targets": FieldDestination("log_field", "targets", "string list"),
        "Concerns": FieldDestination("log_field", "concerns", "string list"),
        "Results-go-to": FieldDestination("log_field", "results_go_to", "string list"),
        "Results": FieldDestination("log_field", "results", "string list"),
        "Grounding": FieldDestination("log_field", "grounding", "registry field"),
        "Goal": FieldDestination("log_field", "goal", "registry field"),
        "Reviews-spec": FieldDestination("log_field", "reviews_spec", "registry field"),
        "Basis": FieldDestination("log_field", "basis", "registry field"),
        "Relation": FieldDestination("log_field", "relation", "registry field"),
        "Short-Description": FieldDestination(
            "log_field", "short_description", "registry field"
        ),
        # Substrings inside Concerns values in historical aw-prompt comments; never keys.
        "hygiene": FieldDestination(
            "comment_value", "concerns", "colon substring inside Concerns value"
        ),
        "tiers": FieldDestination(
            "comment_value", "concerns", "colon substring inside Concerns value"
        ),
        # Body bullets inside historical prompts; kept in prompt body.
        "Core": FieldDestination(
            "prompt_body", "body", "bullet in prompt body prose, kept unchanged"
        ),
        "Executor": FieldDestination(
            "prompt_body", "body", "bullet in prompt body prose, kept unchanged"
        ),
        "Thorough": FieldDestination(
            "prompt_body", "body", "bullet in prompt body prose, kept unchanged"
        ),
        "Purpose": FieldDestination(
            "prompt_body", "body", "bullet in prompt body prose, kept unchanged"
        ),
        "Date": FieldDestination(
            "prompt_body", "body", "bullet in retired prompt body, kept unchanged"
        ),
    }

    research_map: Dict[str, FieldDestination] = {
        "id": FieldDestination("identity", "id", "research YAML id"),
        "status": FieldDestination("status", "status", "research YAML status"),
        "created": FieldDestination(
            "log_field", "created_day", "research YAML creation day on local clock"
        ),
        "kind": FieldDestination(
            "log_field", "research_kind", "4.5c rename from YAML kind"
        ),
        "summary": FieldDestination(
            "body_section", "Summary", "research YAML summary moved to body"
        ),
        "set": FieldDestination("log_field", "set", "terse set id"),
        "order": FieldDestination("log_field", "order", "integer order"),
        "topic": FieldDestination("log_field", "topic", "string list"),
        "model": FieldDestination("log_field", "model", "registry field"),
        "outcome": FieldDestination("log_field", "outcome", "registry field"),
        "consumed-by": FieldDestination("log_field", "consumed_by", "string list"),
        "priority": FieldDestination("log_field", "priority", "registry field"),
        "short-description": FieldDestination(
            "log_field", "short_description", "registry field"
        ),
        "ace": FieldDestination("log_field", "ace", "registry field"),
        # Historical prose bullets appearing below the closing YAML fence; kept in body unchanged.
        **{
            k: FieldDestination(
                "body_prose",
                "body",
                "body prose bullet below research YAML, kept unchanged",
            )
            for k in (
                "Component",
                "Date",
                "Origin",
                "Outcome",
                "Plan",
                "Plans",
                "Prompt",
                "Purpose",
                "Reconciler",
                "Reports",
                "Repository",
                "Researched",
                "Researcher",
                "Reviewer",
                "Scope",
                "Set",
                "Severity",
                "Source",
                "Spec",
                "Status",
                "Summary",
            )
        },
    }

    walkthrough_map: Dict[str, FieldDestination] = {
        "Id": FieldDestination(
            "identity", "id", "checkpoint identity and one-key mirror"
        ),
        "Status": FieldDestination(
            "body_prose",
            "body",
            "free-prose Status line kept in body unchanged (4.1)",
        ),
        "Date": FieldDestination(
            "log_field", "created_day", "legacy creation day on local clock"
        ),
        "Set": FieldDestination("log_field", "set", "terse set id"),
        "Order": FieldDestination("log_field", "order", "integer order"),
        "Target-Id": FieldDestination(
            "log_field", "target_id", "target artifact reference"
        ),
        "Short-Description": FieldDestination(
            "log_field", "short_description", "registry field"
        ),
        "Kind": FieldDestination(
            "body_section",
            "Kind",
            "legacy walkthrough bullet preserved in body (not plan_role)",
        ),
        "Origin": FieldDestination(
            "body_section", "Origin", "legacy bullet preserved in body"
        ),
        "Plan": FieldDestination(
            "body_section", "Plan", "legacy bullet preserved in body"
        ),
        "Purpose": FieldDestination(
            "body_section", "Purpose", "legacy bullet preserved in body"
        ),
        "Spec": FieldDestination(
            "body_section", "Spec", "legacy bullet preserved in body"
        ),
        **{
            k: FieldDestination(
                "body_section", k, "legacy walkthrough bullet preserved in body"
            )
            for k in (
                "Author",
                "Base commit",
                "Commits",
                "Driver run",
                "Executed by",
                "Executor under review",
                "From-Backlog",
                "From-Spec",
                "Measured at HEAD",
                "Rejected commit",
                "Reviewer",
                "Target IPD",
                "Verdict",
                "Verified at",
            )
        },
        **common_ipd_spec_prose,
    }

    roadmap_map: Dict[str, FieldDestination] = dict(walkthrough_map)

    review_map: Dict[str, FieldDestination] = {
        "Subject-Id": FieldDestination(
            "review_mirror", "subject", "review front-matter subject"
        ),
        "Subject-Type": FieldDestination(
            "review_mirror", "subject_type", "review front-matter subject_type"
        ),
        "Ref": FieldDestination(
            "review_mirror", "ref", "review front-matter ref (4.1a K4)"
        ),
        "Verdict": FieldDestination(
            "review_event",
            "legacy_verdict",
            "last-round review event field (4.1a K5/K5a)",
        ),
        "Reviewer": FieldDestination(
            "review_event",
            "reviewer",
            "last-round review event field (4.1a K5a/K6)",
        ),
        "Reviewed-At": FieldDestination(
            "review_event",
            "observed_day",
            "last-round review event field (4.1a K5a/K6)",
        ),
        "Findings": FieldDestination(
            "review_event",
            "findings_summary",
            "last-round review event field (4.1a K6)",
        ),
        "Audited-Scope": FieldDestination(
            "body_section", "Audited-Scope", "legacy review bullet preserved in body"
        ),
        "Rounds": FieldDestination(
            "body_section", "Rounds", "legacy review bullet preserved in body"
        ),
        "Set": FieldDestination(
            "body_section", "Set", "legacy review bullet preserved in body"
        ),
        "Order": FieldDestination(
            "body_section", "Order", "legacy review bullet preserved in body"
        ),
        "Readiness": FieldDestination(
            "body_section", "Readiness", "legacy review bullet preserved in body"
        ),
        **common_ipd_spec_prose,
    }

    return {
        "ipd": ipd_map,
        "backlog": backlog_map,
        "release": release_map,
        "spec": spec_map,
        "prompt": prompt_map,
        "research": research_map,
        "walkthrough": walkthrough_map,
        "roadmap": roadmap_map,
        "review": review_map,
    }


FIELD_DESTINATIONS: Dict[str, Dict[str, FieldDestination]] = _build_field_destinations()


def _normalize_day(raw: Optional[str]) -> Optional[str]:
    """Normalize ``YYYYMMDD`` or ``YYYY-MM-DD`` to ``YYYY-MM-DD`` when valid."""
    if not raw:
        return None
    s = raw.strip()
    if _YYYY_MM_DD_RE.match(s):
        return s
    m = _YYYYMMDD_RE.match(s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def _parse_multiline_bullets(
    text: str,
) -> Tuple[Dict[str, str], List[Tuple[str, str]], Tuple[int, int]]:
    """Parse leading metadata bullets (with indented continuations) before the first ``##``+.

    Returns ``(bullet_dict, ordered_pairs, (region_start_line, region_end_line))``.
    """
    lines = text.splitlines(keepends=True)
    end_idx = len(lines)
    in_fence = False
    fence_char = ""
    fence_len = 0

    for idx, raw_line in enumerate(lines):
        stripped = raw_line.rstrip("\r\n")
        fm = _FENCE_RE.match(stripped)
        if fm:
            marker = fm.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
                fence_len = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len:
                in_fence = False
            continue
        if not in_fence and _H2_PLUS_RE.match(stripped):
            end_idx = idx
            break

    bullets: Dict[str, str] = {}
    ordered: List[Tuple[str, str]] = []
    cur_key: Optional[str] = None
    cur_val_lines: List[str] = []

    def _flush() -> None:
        nonlocal cur_key, cur_val_lines
        if cur_key is not None:
            joined = "\n".join(cur_val_lines).strip()
            bullets[cur_key] = joined
            ordered.append((cur_key, joined))
        cur_key = None
        cur_val_lines = []

    for idx in range(end_idx):
        line_no_nl = lines[idx].rstrip("\r\n")
        m = _BULLET_LINE_RE.match(line_no_nl)
        if m:
            _flush()
            cur_key = m.group(1).strip()
            cur_val_lines = [m.group(2).strip()]
            continue
        if cur_key is not None:
            if line_no_nl.startswith((" ", "\t")) and line_no_nl.strip():
                cur_val_lines.append(line_no_nl.strip())
                continue
            _flush()

    _flush()
    return bullets, ordered, (0, end_idx)


def _parse_prompt_comment(text: str) -> Dict[str, str]:
    """Extract key/value pairs from a leading ``<!-- aw-prompt: ... -->`` comment."""
    m = _PROMPT_COMMENT_RE.match(text.lstrip("\ufeff").lstrip())
    if not m:
        return {}
    inner = m.group(1)
    if " . " in inner:
        inner = inner.split(" . ", 1)[0]
    out: Dict[str, str] = {}
    for seg in inner.split("|"):
        if ":" in seg:
            k, v = seg.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def _find_history_section_span(
    lines: Sequence[str],
) -> Optional[Tuple[int, int, List[Tuple[str, Optional[str]]]]]:
    """Locate the column-zero ``## Workflow history`` section outside fenced code blocks.

    Uses ``attention_contract.history_block`` termination rules so ``###`` sections
    (for example ``### Problem Statement`` in backlog items) and non-bullet body lines
    remain intact.

    Returns ``(start_idx, end_idx, [(raw_entry_text, observed_day), ...])`` or None.
    """
    in_fence = False
    fence_char = ""
    fence_len = 0
    heading_idx: Optional[int] = None

    for idx, raw_line in enumerate(lines):
        stripped = raw_line.rstrip("\r\n")
        fm = _FENCE_RE.match(stripped)
        if fm:
            marker = fm.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
                fence_len = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len:
                in_fence = False
            continue
        if not in_fence and attention_contract._WORKFLOW_HISTORY_HEADING_RE.match(
            stripped
        ):
            heading_idx = idx
            break

    if heading_idx is None:
        return None

    end_idx = len(lines)
    continuing = False
    for idx in range(heading_idx + 1, len(lines)):
        line = lines[idx].rstrip("\r\n")
        if line.startswith("## "):
            end_idx = idx
            break
        is_indented = line.startswith(" ") or line.startswith("\t")
        is_blank = not line.strip()
        if not is_blank and not is_indented and not line.startswith("- "):
            end_idx = idx
            break
        if not is_blank and is_indented and not continuing:
            end_idx = idx
            break
        if is_blank:
            continuing = False
        elif not is_indented and line.startswith("- "):
            continuing = True

    entries: List[Tuple[str, Optional[str]]] = []
    cur_lines: List[str] = []
    cur_day: Optional[str] = None
    in_entry = False

    def _flush_entry() -> None:
        nonlocal cur_lines, cur_day, in_entry
        if in_entry and cur_lines:
            entries.append(("\n".join(cur_lines), cur_day))
        cur_lines = []
        cur_day = None
        in_entry = False

    for idx in range(heading_idx + 1, end_idx):
        line = lines[idx].rstrip("\r\n")
        is_indented = line.startswith(" ") or line.startswith("\t")
        is_blank = not line.strip()
        if is_blank:
            _flush_entry()
            continue
        if not is_indented and line.startswith("- "):
            _flush_entry()
            trimmed = line.rstrip()
            m_rec = attention_contract.HISTORY_RECORD_RE.match(trimmed)
            if m_rec:
                cur_day = m_rec.group("date")
            else:
                m_pref = _DATED_PREFIX_RE.match(trimmed)
                cur_day = m_pref.group(1) if m_pref else None
            cur_lines = [trimmed]
            in_entry = True
        elif is_indented and in_entry:
            cur_lines.append(line.rstrip())

    _flush_entry()
    return heading_idx, end_idx, entries


def _resolve_describer_result(
    describer: Optional[Any],
    descriptions: Optional[Mapping[str, Any]],
    *,
    id6: str,
    art_type: str,
    rel_path: str,
    old_rel: Optional[str],
    text: str,
) -> Optional[Dict[str, Optional[str]]]:
    """Resolve ``short_description`` and provenance from ``descriptions`` or ``describer``."""
    raw_entry: Any = None
    if descriptions:
        for key in (id6, old_rel, rel_path):
            if key and key in descriptions:
                raw_entry = descriptions[key]
                break

    if raw_entry is None and describer is not None:
        fn = getattr(describer, "describe", None)
        if not callable(fn) and callable(describer):
            fn = describer
        if callable(fn):
            try:
                raw_entry = fn(id6, art_type, rel_path, text)
            except TypeError:
                try:
                    raw_entry = fn(id6, text.encode("utf-8"))
                except TypeError:
                    raw_entry = fn(text)

    if raw_entry is None:
        return None
    if isinstance(raw_entry, str):
        cleaned = raw_entry.strip()
        if not cleaned:
            return None
        return {
            "short_description": cleaned,
            "description_source": "generated",
            "description_model": str(getattr(describer, "model", None) or "stub"),
            "description_prompt_version": str(
                getattr(describer, "prompt_version", None) or "v1"
            ),
        }
    if isinstance(raw_entry, Mapping):
        val = raw_entry.get("short_description") or raw_entry.get("text")
        if not isinstance(val, str) or not val.strip():
            return None
        out: Dict[str, Optional[str]] = {
            "short_description": val.strip(),
            "description_source": str(
                raw_entry.get("description_source")
                or raw_entry.get("source")
                or "generated"
            ),
            "description_model": (
                str(raw_entry.get("description_model") or raw_entry.get("model"))
                if (raw_entry.get("description_model") or raw_entry.get("model"))
                else None
            ),
            "description_prompt_version": (
                str(
                    raw_entry.get("description_prompt_version")
                    or raw_entry.get("prompt_version")
                )
                if (
                    raw_entry.get("description_prompt_version")
                    or raw_entry.get("prompt_version")
                )
                else None
            ),
        }
        return out
    return None


def _coerce_list_value(raw_val: Any, *, split_commas: bool) -> List[str]:
    """Convert a metadata value to a list of stripped non-empty strings."""
    if isinstance(raw_val, list):
        return [str(x).strip() for x in raw_val if str(x).strip()]
    if isinstance(raw_val, str):
        s = raw_val.strip()
        if not s:
            return []
        if "\n" in s and all(
            not ln.strip() or ln.strip().startswith("- ") for ln in s.splitlines()
        ):
            items: List[str] = []
            for ln in s.splitlines():
                stripped = ln.strip()
                if stripped.startswith("- "):
                    stripped = stripped[2:].strip()
                if stripped:
                    items.append(stripped)
            return items
        if split_commas:
            return [tok.strip() for tok in s.split(",") if tok.strip()]
        return [s]
    return [str(raw_val).strip()]


def _utc_now_rfc3339() -> str:
    """Return current UTC timestamp in RFC 3339 format with seconds precision."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class ReviewFileSpec:
    """Parsed legacy review file metadata, K4 binding, and round numbers."""

    path: Path
    rel_path: str
    subject_id: str
    subject_type: str
    review_ref: Optional[str]
    review_kind: str
    rounds: Tuple[int, ...]
    last_round: int
    legacy_verdict: Optional[str]
    reviewer: Optional[str]
    observed_day: Optional[str]
    findings_summary: Optional[str]
    body_sections: Tuple[Tuple[str, str], ...]
    sort_key: Tuple[str, str, int, str]


def _extract_review_filename_parts(
    filename: str,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Return ``(filename_id6, date, set_id, nn)`` from a review filename."""
    m_leg = artifact_naming._LEGACY_TIMESTAMP_RE.match(filename)
    if m_leg:
        return None, m_leg.group("date"), None, m_leg.group("nn")
    m_attr = artifact_naming.parse_attributed(filename)
    if m_attr:
        return m_attr.id6, m_attr.date, m_attr.set, m_attr.nn
    m_clust = artifact_naming.parse_clustered(filename)
    if m_clust:
        return (
            m_clust.group("id6"),
            m_clust.group("date"),
            m_clust.group("set"),
            m_clust.group("nn"),
        )
    return None, None, None, None


def _parse_review_file_raw(review_path: Path, records_root: Path) -> Dict[str, Any]:
    """Parse one ``.review.md`` file into raw fields before K4 multi-file resolution."""
    text = review_path.read_text(encoding="utf-8")
    rel_path = review_path.relative_to(records_root).as_posix()
    fname = review_path.name
    fn_id6, fn_date, fn_set, fn_nn = _extract_review_filename_parts(fname)

    mirror_data: Dict[str, str] = {}
    work_text = text
    if text.startswith("---\n") or text.startswith("---\r\n"):
        try:
            mirror_data = artifact_meta.parse_review_mirror(text)
            work_text = artifact_meta._strip_leading_yaml_mirror(text)
        except ValueError:
            mirror_data = {}

    raw_fields, ordered_pairs, _ = _parse_multiline_bullets(work_text)

    subject_id = (
        raw_fields.get("Subject-Id")
        or raw_fields.get("Subject")
        or mirror_data.get("subject")
        or fn_id6
        or ""
    ).strip()
    artifact_meta.validate_id6(subject_id)

    subject_type = (
        (raw_fields.get("Subject-Type") or mirror_data.get("subject_type") or "ipd")
        .strip()
        .lower()
    )

    doc = review_findings.parse_review_text(work_text, path=review_path)
    raw_rounds = [r.number for r in doc.rounds] if doc.rounds else [1]
    rounds = tuple(sorted(set(raw_rounds)))
    last_round = max(rounds)

    review_kind = artifact_meta.review_kind_of_file(rel_path)

    dest_map = FIELD_DESTINATIONS["review"]
    body_sections: List[Tuple[str, str]] = []
    for key, val in ordered_pairs:
        dest = dest_map.get(key)
        if dest is None:
            if val:
                body_sections.append((key, val))
            continue
        if dest.kind == "body_section" and val:
            body_sections.append((dest.target, val))

    explicit_ref = raw_fields.get("Ref") or mirror_data.get("ref")
    verdict_raw = raw_fields.get("Verdict")
    reviewer_raw = raw_fields.get("Reviewer")
    reviewed_at_raw = raw_fields.get("Reviewed-At") or raw_fields.get("Date")
    observed_day = (
        (_normalize_day(reviewed_at_raw) or reviewed_at_raw.strip())
        if reviewed_at_raw and reviewed_at_raw.strip()
        else None
    )
    findings_raw = raw_fields.get("Findings")

    nn_int = int(fn_nn) if fn_nn and fn_nn.isdigit() else 0
    sort_key = (fn_date or "", fn_set or "", nn_int, rel_path)

    return {
        "path": review_path,
        "rel_path": rel_path,
        "fname": fname,
        "fn_id6": fn_id6,
        "fn_date": fn_date,
        "fn_set": fn_set,
        "fn_nn": fn_nn,
        "subject_id": subject_id,
        "subject_type": subject_type,
        "explicit_ref": explicit_ref.strip() if explicit_ref else None,
        "review_kind": review_kind,
        "rounds": rounds,
        "last_round": last_round,
        "legacy_verdict": verdict_raw,
        "reviewer": reviewer_raw.strip()
        if reviewer_raw and reviewer_raw.strip()
        else None,
        "observed_day": observed_day,
        "findings_summary": (
            findings_raw.strip() if findings_raw and findings_raw.strip() else None
        ),
        "body_sections": tuple(body_sections),
        "sort_key": sort_key,
    }


def _discover_review_files(records_root: Path) -> Dict[str, List[ReviewFileSpec]]:
    """Discover all ``.review.md`` files under ``records_root / 'reviews'`` and assign K4 bindings."""
    reviews_dir = records_root / "reviews"
    if not reviews_dir.is_dir():
        return {}

    raw_by_subj: Dict[str, List[Dict[str, Any]]] = {}
    for cur_dir, dirs, files in os.walk(reviews_dir):
        dirs[:] = sorted(d for d in dirs if not d.endswith(".data"))
        cur_path = Path(cur_dir)
        for fname in sorted(files):
            if not fname.endswith(".review.md"):
                continue
            if fname in _EXCLUDED_FILENAMES or fname.startswith("INDEX."):
                continue
            parsed = _parse_review_file_raw(cur_path / fname, records_root)
            raw_by_subj.setdefault(parsed["subject_id"], []).append(parsed)

    out: Dict[str, List[ReviewFileSpec]] = {}
    for sid, items in raw_by_subj.items():
        same_id_items = [it for it in items if not it["fn_id6"] or it["fn_id6"] == sid]
        same_id_refs: Dict[str, Optional[str]] = {}
        if len(same_id_items) == 1:
            it = same_id_items[0]
            same_id_refs[it["rel_path"]] = it["explicit_ref"]
        elif len(same_id_items) >= 2:
            cands: Dict[str, str] = {}
            for it in same_id_items:
                if it["explicit_ref"]:
                    cands[it["rel_path"]] = it["explicit_ref"]
                elif it["fn_date"] and it["fn_set"] and it["fn_nn"]:
                    cands[it["rel_path"]] = (
                        f"{it['fn_date']}-{it['fn_set']}-{it['fn_nn']}"
                    )
                else:
                    cands[it["rel_path"]] = it["fname"][: -len(".review.md")]
            counts: Dict[str, int] = {}
            for c in cands.values():
                counts[c] = counts.get(c, 0) + 1
            for it in same_id_items:
                cand = cands[it["rel_path"]]
                if counts[cand] > 1:
                    same_id_refs[it["rel_path"]] = it["fname"][: -len(".review.md")]
                else:
                    same_id_refs[it["rel_path"]] = cand

        specs: List[ReviewFileSpec] = []
        for it in items:
            if it["fn_id6"] and it["fn_id6"] != sid:
                ref = it["fn_id6"]
            else:
                ref = same_id_refs.get(it["rel_path"], it["explicit_ref"])
            specs.append(
                ReviewFileSpec(
                    path=it["path"],
                    rel_path=it["rel_path"],
                    subject_id=sid,
                    subject_type=it["subject_type"],
                    review_ref=ref,
                    review_kind=it["review_kind"],
                    rounds=it["rounds"],
                    last_round=it["last_round"],
                    legacy_verdict=it["legacy_verdict"],
                    reviewer=it["reviewer"],
                    observed_day=it["observed_day"],
                    findings_summary=it["findings_summary"],
                    body_sections=it["body_sections"],
                    sort_key=it["sort_key"],
                )
            )
        specs.sort(key=lambda sp: sp.sort_key)
        out[sid] = specs
    return out


def build_record_log(
    record_path: Path,
    records_root: Path,
    *,
    old_rel: Optional[str] = None,
    sidecar_events: Optional[Sequence[Dict[str, Any]]] = None,
    review_files: Optional[Sequence[ReviewFileSpec]] = None,
    include_reviews: bool = True,
    pre_step3_text: Optional[str] = None,
    migration_at: Optional[str] = None,
    describer: Optional[Any] = None,
    descriptions: Optional[Mapping[str, Any]] = None,
    repo_root: Optional[Path] = None,
    ruleset: Optional[Any] = None,
    validate: bool = True,
) -> Tuple[str, str, List[Dict[str, Any]], Dict[str, Any]]:
    """Build the migrated event log (``append`` 0) for one record.

    Returns ``(id6, art_type, events, parsed_meta)``.
    """
    text = record_path.read_text(encoding="utf-8")
    rel_path = record_path.relative_to(records_root).as_posix()

    art_row, _ = artifact_meta.load_legacy_artifact(
        record_path, records_root, text=text
    )
    id6 = str(art_row["id6"])
    if art_row.get("id_derived"):
        id6 = artifact_core.mint_id6(repo_root or records_root)
    art_type = str(art_row["type"])
    if art_type not in ALL_RECORD_TYPES:
        raise layout_migration.MigrationError(
            f"Unsupported record type {art_type!r} for m0001_convert at {rel_path}"
        )

    dest_map = FIELD_DESTINATIONS[art_type]
    is_prompt = art_type == "prompt"
    is_research = art_type == "research"
    is_statusless = art_type in ("walkthrough", "roadmap")

    if is_prompt:
        raw_fields = _parse_prompt_comment(text)
        ordered_pairs = list(raw_fields.items())
    elif is_research:
        parsed_fm = artifact_meta.front_matter_mapping(text)
        if parsed_fm is None:
            yaml_map, _ = artifact_meta._parse_yaml_front_matter(text)
            raw_fields = dict(yaml_map)
            ordered_pairs = list(raw_fields.items())
        else:
            raw_fields = dict(parsed_fm)
            ordered_pairs = list(parsed_fm.items())
    else:
        raw_fields, ordered_pairs, _ = _parse_multiline_bullets(text)

    status: Optional[str] = None
    if not is_statusless:
        status_raw = raw_fields.get("Status") or raw_fields.get("status")
        if isinstance(status_raw, str) and status_raw.strip():
            toks = status_raw.strip().split()
            if toks:
                status = toks[0].lower()
        if not status and not is_research:
            status = record_path.parent.name

    fields: Dict[str, Any] = {
        "id": id6,
        "type": art_type,
    }
    if status is not None:
        fields["status"] = status

    fn_date = _normalize_day(art_row.get("filename_date"))
    if fn_date:
        fields["filename_date"] = fn_date

    reg = artifact_meta.REGISTRY[art_type]
    if art_row.get("set_id") and "set" in reg:
        fields["set"] = str(art_row["set_id"])
    if art_row.get("order_nn") is not None and "order" in reg:
        fields["order"] = int(art_row["order_nn"])
    title_val = art_row.get("title") or m0001_discover._extract_first_h1(text)
    if title_val and "title" in reg:
        fields["title"] = str(title_val)

    art_fields = art_row.get("fields") or {}
    if art_fields.get("ace") and "ace" in reg:
        fields["ace"] = str(art_fields["ace"])
    if art_fields.get("model") and "model" in reg:
        fields["model"] = str(art_fields["model"])

    body_sections: List[Tuple[str, str]] = []
    unknown_keys: List[str] = []

    for key, val in ordered_pairs:
        dest = dest_map.get(key)
        if dest is None:
            cand = key.lower().replace("-", "_")
            if cand in reg:
                dest = FieldDestination("log_field", cand, "same-named registry field")
            else:
                unknown_keys.append(key)
                if isinstance(val, str):
                    body_sections.append((key, val))
                elif val is not None:
                    body_sections.append((key, str(val)))
                continue

        if dest.kind in (
            "identity",
            "status",
            "prompt_body",
            "comment_value",
            "body_prose",
        ):
            continue
        if dest.kind == "body_section":
            val_str = val.strip() if isinstance(val, str) else str(val).strip()
            if val_str:
                body_sections.append((dest.target, val_str))
            continue

        # dest.kind == "log_field"
        target_field = dest.target
        if key in ("Set", "set"):
            terse = m0001_renames._parse_terse_set(str(val))
            if terse:
                fields["set"] = terse
            continue
        if key in ("Order", "order"):
            s_val = str(val).strip()
            if s_val:
                try:
                    fields["order"] = int(s_val)
                except ValueError as exc:
                    raise layout_migration.MigrationError(
                        f"Malformed integer Order {val!r} in {rel_path}"
                    ) from exc
            continue
        if key in ("Date", "Created", "created"):
            cday = _normalize_day(str(val))
            if cday:
                fields["created_day"] = cday
            continue
        if key == "Item-Dependencies":
            dep_decl, dep_edges = artifact_meta.parse_item_dependencies_field(val)
            fields["dependency_declaration"] = dep_decl
            if dep_decl == "listed":
                fields["item_dependencies"] = dep_edges
            else:
                fields["item_dependencies"] = []
            continue
        if key == "Scope-Exceeded":
            parsed_oos, _malformed = artifact_meta._parse_scope_exceeded_bullet(val)
            fields["scope_result"] = "exceeded"
            fields["out_of_scope_paths"] = parsed_oos
            fields["scope_exceeded_raw"] = val
            continue
        if key == "Scope-Paths":
            sp_list = _coerce_list_value(val, split_commas=True)
            if sp_list:
                fields["scope_paths"] = sp_list
            continue
        if key == "Graduated-To":
            gt_list = artifact_meta.parse_graduated_to(val)
            if gt_list:
                fields["graduated_to"] = gt_list
            continue
        if key in ("topic", "consumed-by"):
            fields[target_field] = _coerce_list_value(val, split_commas=True)
            continue
        if key in ("Targets", "Concerns", "Results-go-to", "Results"):
            lst = _coerce_list_value(val, split_commas=False)
            if lst:
                fields[target_field] = lst
            continue
        if target_field in reg and val != "" and val is not None:
            fields[target_field] = val

    # Extract pre-step-3 history verbatim for op: legacy and last_history_day
    hist_source_text = pre_step3_text if pre_step3_text is not None else text
    hist_lines = hist_source_text.splitlines(keepends=True)
    hist_span = _find_history_section_span(hist_lines)
    hist_entries: List[Tuple[str, Optional[str]]] = (
        hist_span[2] if hist_span is not None else []
    )
    hb = attention_contract.history_block(hist_source_text)
    if hb.records:
        newest = attention_contract.newest_history_record(hb.records)
        if newest:
            lhd = attention_contract.last_history_at([newest])
            if lhd:
                fields["last_history_day"] = lhd

    # Describer seam: populate description_source/model/prompt_version only when returned
    desc_info = _resolve_describer_result(
        describer,
        descriptions,
        id6=id6,
        art_type=art_type,
        rel_path=rel_path,
        old_rel=old_rel,
        text=hist_source_text,
    )
    if desc_info is not None:
        fields["short_description"] = desc_info["short_description"]
        if desc_info.get("description_source"):
            fields["description_source"] = desc_info["description_source"]
        if desc_info.get("description_model"):
            fields["description_model"] = desc_info["description_model"]
        if desc_info.get("description_prompt_version"):
            fields["description_prompt_version"] = desc_info[
                "description_prompt_version"
            ]

    at_ts = migration_at or _utc_now_rfc3339()
    actor = {"tool": "aw migrate metadata"}

    events: List[Dict[str, Any]] = []
    seq = 0

    checkpoint_path = old_rel if old_rel else rel_path
    events.append(
        {
            "v": 1,
            "seq": seq,
            "append": 0,
            "at": at_ts,
            "actor": dict(actor),
            "op": "checkpoint",
            "path": checkpoint_path,
            "fields": fields,
        }
    )
    seq += 1

    if old_rel and old_rel != rel_path:
        events.append(
            {
                "v": 1,
                "seq": seq,
                "append": 0,
                "at": at_ts,
                "actor": dict(actor),
                "op": "rename",
                "verb": "rename",
                "path": rel_path,
            }
        )
        seq += 1

    for pos, (raw_line, obs_day) in enumerate(hist_entries):
        ev: Dict[str, Any] = {
            "v": 1,
            "seq": seq,
            "append": 0,
            "at": at_ts,
            "actor": dict(actor),
            "op": "legacy",
            "source": "history",
            "position": pos,
            "ordering_confidence": "unknown",
            "line": raw_line,
        }
        if obs_day:
            ev["observed_day"] = obs_day
        events.append(ev)
        seq += 1

    for sc in sidecar_events or ():
        ev = {
            "v": 1,
            "seq": seq,
            "append": 0,
            "at": at_ts,
            "actor": dict(actor),
            "op": "legacy",
            "source": "sidecar",
            "ordering_confidence": "unknown",
            "line": sc.get("line"),
        }
        if sc.get("observed_day") is not None:
            ev["observed_day"] = str(sc["observed_day"])
        if sc.get("position") is not None:
            ev["position"] = int(sc["position"])
        events.append(ev)
        seq += 1

    resolved_reviews: Sequence[ReviewFileSpec] = ()
    if art_type in ("ipd", "spec"):
        if review_files is not None:
            resolved_reviews = review_files
        elif include_reviews and (records_root / "reviews").is_dir():
            resolved_reviews = _discover_review_files(records_root).get(id6, ())

    for rf in resolved_reviews:
        for rnd_num in rf.rounds:
            is_last = rnd_num == rf.last_round
            rev_ev: Dict[str, Any] = {
                "v": 1,
                "seq": seq,
                "append": 0,
                "at": at_ts,
                "actor": dict(actor),
                "op": "review",
                "round": rnd_num,
                "review_kind": rf.review_kind,
                "legacy_verdict": rf.legacy_verdict if is_last else None,
            }
            if rf.review_ref is not None:
                rev_ev["review_ref"] = rf.review_ref
            if is_last:
                if rf.reviewer:
                    rev_ev["reviewer"] = rf.reviewer
                if rf.observed_day:
                    rev_ev["observed_day"] = rf.observed_day
                if rf.findings_summary:
                    rev_ev["findings_summary"] = rf.findings_summary
            events.append(rev_ev)
            seq += 1

    if validate:
        artifact_meta.validate_new_events(
            art_type,
            events,
            records_root=records_root,
            repo_root=repo_root,
            migration_import=True,
            ruleset=ruleset,
        )
        artifact_meta.replay(
            id6,
            art_type,
            events,
            records_root=records_root,
            migration_import=True,
        )

    parsed_meta = {
        "id": id6,
        "type": art_type,
        "status": status,
        "body_sections": body_sections,
        "unknown_keys": unknown_keys,
        "rel_path": rel_path,
        "old_rel": old_rel,
    }
    return id6, art_type, events, parsed_meta


def _insert_body_sections(body_text: str, sections: Sequence[Tuple[str, str]]) -> str:
    """Insert moved ``## <Field>`` prose sections cleanly after any leading H1/intro."""
    if not sections:
        return body_text

    # Separate any leading H1 title and intro non-heading lines from the first ##+ section.
    lines = body_text.splitlines(keepends=True)
    first_h2_idx: Optional[int] = None
    in_fence = False
    fence_char = ""
    fence_len = 0
    for idx, raw_line in enumerate(lines):
        stripped = raw_line.rstrip("\r\n")
        fm = _FENCE_RE.match(stripped)
        if fm:
            marker = fm.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
                fence_len = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len:
                in_fence = False
            continue
        if not in_fence and _H2_PLUS_RE.match(stripped):
            first_h2_idx = idx
            break

    head = "".join(lines[:first_h2_idx]) if first_h2_idx is not None else body_text
    tail = "".join(lines[first_h2_idx:]) if first_h2_idx is not None else ""

    to_insert: List[Tuple[str, str]] = []
    for heading, value in sections:
        exact_pat = re.compile(rf"(?m)^##\s+{re.escape(heading)}\s*$")
        m_existing = exact_pat.search(tail)
        if m_existing:
            if value not in tail[m_existing.end() :]:
                insert_pos = m_existing.end()
                tail = (
                    tail[:insert_pos]
                    + "\n"
                    + value
                    + "\n"
                    + tail[insert_pos:].lstrip("\n")
                )
        else:
            to_insert.append((heading, value))

    if not to_insert:
        return head + tail

    rendered_blocks = "\n".join(
        f"## {heading}\n\n{value}\n" for heading, value in to_insert
    )
    parts: List[str] = []
    if head.strip():
        parts.append(head.rstrip("\n") + "\n")
    parts.append(rendered_blocks.rstrip("\n") + "\n")
    if tail.strip():
        parts.append(tail.lstrip("\n"))
    return "\n".join(parts)


def _strip_history_section_from_text(text: str) -> str:
    """Remove any un-fenced ``## Workflow history`` section from ``text``."""
    lines = text.splitlines(keepends=True)
    hist_span = _find_history_section_span(lines)
    if hist_span is None:
        return text
    start_idx, end_idx, _ = hist_span
    before_hist = "".join(lines[:start_idx]).rstrip("\n")
    after_hist = "".join(lines[end_idx:]).lstrip("\n")
    if before_hist and after_hist:
        return before_hist + "\n\n" + after_hist
    if before_hist:
        return before_hist + "\n"
    return after_hist


def rewrite_review_file(
    text: str,
    subject_id: str,
    subject_type: str,
    *,
    review_ref: Optional[str] = None,
    parsed_meta: Optional[Mapping[str, Any]] = None,
) -> str:
    """Rewrite a legacy ``.review.md`` file into 4.1/4.1a front matter + review banner.

    Keeps ``## Round``, ``### Findings``, and ``### Decisions`` sections byte-identical
    while deleting the leading bullet block and any un-fenced ``## Workflow history``.
    """
    mirror_prefix = artifact_meta.render_review_mirror(
        subject_id, subject_type, review_ref
    )
    work_text = artifact_meta._strip_leading_yaml_mirror(text)
    _, ordered_pairs, (reg_start, reg_end) = _parse_multiline_bullets(work_text)
    lines = work_text.splitlines(keepends=True)

    kept_region_lines: List[str] = []
    in_bullet_cont = False
    for idx in range(reg_start, reg_end):
        raw_line = lines[idx]
        no_nl = raw_line.rstrip("\r\n")
        if _BULLET_LINE_RE.match(no_nl):
            in_bullet_cont = True
            continue
        if in_bullet_cont:
            if no_nl.startswith((" ", "\t")) and no_nl.strip():
                continue
            in_bullet_cont = False
        kept_region_lines.append(raw_line)

    cleaned_region = re.sub(r"\n{3,}", "\n\n", "".join(kept_region_lines)).strip("\n")
    rest_text = _strip_history_section_from_text("".join(lines[reg_end:]))

    if cleaned_region and rest_text.strip():
        body = cleaned_region + "\n\n" + rest_text.lstrip("\n")
    elif cleaned_region:
        body = cleaned_region + "\n"
    else:
        body = rest_text.lstrip("\n")

    dest_map = FIELD_DESTINATIONS["review"]
    sections = (
        list(parsed_meta.get("body_sections") or [])
        if parsed_meta is not None
        else [
            (dest_map.get(k, FieldDestination("body_section", k)).target, v)
            for k, v in ordered_pairs
            if dest_map.get(k, FieldDestination("body_section", k)).kind
            == "body_section"
            and v
        ]
    )
    body = _insert_body_sections(body, sections)
    body = body.lstrip("\n")
    if body and not body.endswith("\n"):
        body += "\n"
    return mirror_prefix + body


def rewrite_record_file(
    text: str,
    id6: str,
    art_type: str,
    status: Optional[str] = None,
    *,
    parsed_meta: Optional[Mapping[str, Any]] = None,
) -> str:
    """Rewrite a legacy record file into the 4.1 in-file mirror + banner and clean body.

    Never spells the 4.1 banner or mirror comment directly; delegates mirror
    rendering to ``artifact_meta.render_in_file_mirror`` (or
    ``artifact_meta.render_review_mirror`` for ``art_type == 'review'``).
    """
    if art_type == "review":
        stype = str((parsed_meta or {}).get("subject_type") or "ipd")
        rref = (parsed_meta or {}).get("review_ref")
        return rewrite_review_file(
            text, id6, stype, review_ref=rref, parsed_meta=parsed_meta
        )

    mirror_prefix = artifact_meta.render_in_file_mirror(id6, art_type, status)

    if art_type == "prompt":
        stripped_body = artifact_meta._LEADING_PROMPT_COMMENT_LINE_RE.sub(
            "", text.lstrip("\ufeff"), count=1
        )
        lines = stripped_body.splitlines(keepends=True)
        hist_span = _find_history_section_span(lines)
        if hist_span is not None:
            start_idx, end_idx, _ = hist_span
            lines = lines[:start_idx] + lines[end_idx:]
        clean_body = "".join(lines).lstrip("\n")
        if clean_body and not clean_body.endswith("\n"):
            clean_body += "\n"
        return mirror_prefix + clean_body

    if art_type == "research":
        parsed_fm = artifact_meta.front_matter_mapping(text)
        body_raw = artifact_meta._strip_leading_yaml_mirror(text)
        body = _strip_history_section_from_text(body_raw)
        if parsed_meta is not None:
            sections = list(parsed_meta.get("body_sections") or [])
        else:
            sum_val = (parsed_fm or {}).get("summary")
            sections = (
                [("Summary", str(sum_val).strip())]
                if isinstance(sum_val, str) and sum_val.strip()
                else []
            )
        body = _insert_body_sections(body, sections)
        body = body.lstrip("\n")
        if body and not body.endswith("\n"):
            body += "\n"
        return mirror_prefix + body

    # Standard artifact (ipd, backlog, release, spec) or statusless record (walkthrough, roadmap):
    # 1. Strip any existing v2 mirror/banner if re-run, and parse metadata region bullets.
    work_text = artifact_meta._strip_leading_yaml_mirror(text)
    _, ordered_pairs, (reg_start, reg_end) = _parse_multiline_bullets(work_text)
    lines = work_text.splitlines(keepends=True)

    # Remove bullet lines (and their indented continuation lines) in metadata region,
    # keeping free-prose `- Status:` lines unchanged on statusless records (4.1).
    keep_status_prose = art_type in ("walkthrough", "roadmap")
    kept_region_lines: List[str] = []
    in_bullet_cont = False
    keeping_cont = False
    for idx in range(reg_start, reg_end):
        raw_line = lines[idx]
        no_nl = raw_line.rstrip("\r\n")
        m_b = _BULLET_LINE_RE.match(no_nl)
        if m_b:
            if keep_status_prose and m_b.group(1).strip() == "Status":
                in_bullet_cont = False
                keeping_cont = True
                kept_region_lines.append(raw_line)
            else:
                in_bullet_cont = True
                keeping_cont = False
            continue
        if in_bullet_cont:
            if no_nl.startswith((" ", "\t")) and no_nl.strip():
                continue
            in_bullet_cont = False
        if keeping_cont:
            if no_nl.startswith((" ", "\t")) and no_nl.strip():
                kept_region_lines.append(raw_line)
                continue
            keeping_cont = False
        kept_region_lines.append(raw_line)

    # Collapse leading/excess blank lines inside kept_region_lines.
    cleaned_region = re.sub(r"\n{3,}", "\n\n", "".join(kept_region_lines)).strip("\n")
    rest_text = _strip_history_section_from_text("".join(lines[reg_end:]))

    if cleaned_region and rest_text.strip():
        body = cleaned_region + "\n\n" + rest_text.lstrip("\n")
    elif cleaned_region:
        body = cleaned_region + "\n"
    else:
        body = rest_text.lstrip("\n")

    sections = (
        list(parsed_meta.get("body_sections") or [])
        if parsed_meta is not None
        else [
            (k, v)
            for k, v in ordered_pairs
            if FIELD_DESTINATIONS.get(art_type, {})
            .get(k, FieldDestination("body_section", k))
            .kind
            == "body_section"
            and v
        ]
    )
    body = _insert_body_sections(body, sections)
    body = body.lstrip("\n")
    if body and not body.endswith("\n"):
        body += "\n"
    return mirror_prefix + body


def _walk_target_records(
    records_root: Path,
    *,
    record_types: Sequence[str],
) -> List[Path]:
    """Walk ``records_root`` returning sorted ``.md`` files for ``record_types``."""
    if not records_root.is_dir():
        return []
    allowed_dirs = {
        dir_name
        for dir_name, rtype in TREE_DIR_TO_TYPE.items()
        if rtype in record_types
    }
    found: List[Path] = []
    for dir_name in sorted(allowed_dirs):
        sub_root = records_root / dir_name
        if not sub_root.is_dir():
            continue
        for cur_dir, dirs, files in os.walk(sub_root):
            dirs[:] = sorted(
                d
                for d in dirs
                if d not in _EXCLUDED_DIRNAMES and not d.endswith(".data")
            )
            cur_path = Path(cur_dir)
            for fname in sorted(files):
                if not fname.endswith(".md"):
                    continue
                if m0001_discover.is_non_record_filename(fname) or fname.endswith(
                    ".review.md"
                ):
                    continue
                fpath = cur_path / fname
                rel_p = fpath.relative_to(records_root).as_posix()
                if m0001_discover.is_excluded_template(
                    rel_p, fname, fpath.read_text(encoding="utf-8", errors="replace")
                ):
                    continue
                found.append(fpath)
    return found


def convert_records(
    repo: Union[str, Path],
    *,
    records_root: Optional[Path] = None,
    pre_step3_records_root: Optional[Path] = None,
    repo_root: Optional[Union[str, Path]] = None,
    rename_map: Optional[Mapping[str, str]] = None,
    sidecar_events: Optional[Mapping[str, Sequence[Dict[str, Any]]]] = None,
    describer: Optional[Any] = None,
    descriptions: Optional[Mapping[str, Any]] = None,
    migration_at: Optional[str] = None,
    record_types: Sequence[str] = FIVE_RECORD_TYPES,
    include_reviews: Optional[bool] = None,
) -> Dict[str, Any]:
    """Convert records of ``record_types`` (and reviews when enabled) to logs and 4.1 mirrors."""
    repo_path = Path(repo)
    resolved_records = (
        Path(records_root)
        if records_root is not None
        else project_context.project_records_dir(repo_path)
    )
    reverse_rename = {
        new_rel: old_rel for old_rel, new_rel in (rename_map or {}).items()
    }
    at_ts = migration_at or _utc_now_rfc3339()
    resolved_repo = (
        Path(repo_root)
        if repo_root is not None
        else artifact_meta._resolve_repo_root(resolved_records, repo_path)
    )
    shared_ruleset = artifact_meta._writer_ruleset(resolved_repo)

    meta_dir = resolved_records / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)

    do_reviews = (
        include_reviews
        if include_reviews is not None
        else any(t not in FIVE_RECORD_TYPES for t in record_types)
    )
    reviews_by_subject = _discover_review_files(resolved_records) if do_reviews else {}

    target_files = _walk_target_records(resolved_records, record_types=record_types)
    log_files: List[str] = []
    rewritten_files: List[str] = []
    by_type: Dict[str, int] = {}
    seen_id6s: Set[str] = set()

    for rec_path in target_files:
        rel_path = rec_path.relative_to(resolved_records).as_posix()
        old_rel = reverse_rename.get(rel_path)
        pre_step3_text: Optional[str] = None
        if pre_step3_records_root is not None:
            pre_candidate = Path(pre_step3_records_root) / (old_rel or rel_path)
            if pre_candidate.is_file():
                pre_step3_text = pre_candidate.read_text(encoding="utf-8")

        orig_text = rec_path.read_text(encoding="utf-8")

        # Determine id6 first so we can attach sidecar and review events for that id6.
        art_probe, _ = artifact_meta.load_legacy_artifact(
            rec_path, resolved_records, text=orig_text
        )
        id6_probe = str(art_probe["id6"])
        sc_events = (sidecar_events or {}).get(id6_probe, ())
        rf_specs = reviews_by_subject.get(id6_probe, ())

        id6, art_type, events, parsed_meta = build_record_log(
            rec_path,
            resolved_records,
            old_rel=old_rel,
            sidecar_events=sc_events,
            review_files=rf_specs,
            include_reviews=do_reviews,
            pre_step3_text=pre_step3_text,
            migration_at=at_ts,
            describer=describer,
            descriptions=descriptions,
            repo_root=resolved_repo,
            ruleset=shared_ruleset,
            validate=True,
        )
        if id6 in seen_id6s:
            raise layout_migration.MigrationError(
                f"Duplicate id6 {id6!r} encountered during conversion at {rel_path}"
            )
        seen_id6s.add(id6)

        log_rel = f"meta/{id6}.jsonl"
        log_abs = resolved_records / log_rel
        log_payload = "".join(artifact_meta.encode_event(ev) for ev in events)
        artifact_core.atomic_write(log_abs, log_payload)
        log_files.append(log_rel)

        rewritten_text = rewrite_record_file(
            orig_text,
            id6,
            art_type,
            parsed_meta["status"],
            parsed_meta=parsed_meta,
        )
        if rewritten_text != orig_text:
            artifact_core.atomic_write(rec_path, rewritten_text)
        rewritten_files.append(rel_path)
        by_type[art_type] = by_type.get(art_type, 0) + 1

    if do_reviews:
        for sid in sorted(reviews_by_subject):
            if sid not in seen_id6s:
                continue
            for rf in reviews_by_subject[sid]:
                orig_rev_text = rf.path.read_text(encoding="utf-8")
                rewritten_rev = rewrite_review_file(
                    orig_rev_text,
                    rf.subject_id,
                    rf.subject_type,
                    review_ref=rf.review_ref,
                    parsed_meta={"body_sections": list(rf.body_sections)},
                )
                if rewritten_rev != orig_rev_text:
                    artifact_core.atomic_write(rf.path, rewritten_rev)
                rewritten_files.append(rf.rel_path)
                by_type["review"] = by_type.get("review", 0) + 1

    return {
        "converted_count": len(log_files),
        "log_files": log_files,
        "rewritten_files": rewritten_files,
        "by_type": by_type,
        "migration_at": at_ts,
    }

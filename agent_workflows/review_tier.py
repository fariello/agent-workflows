"""Review depth and tier utilities (spec k3yx72; Set revsteps, IPD gv3smb).

Provides pure functions for calculating tier facts from a plan, parsing tier markers
and tier answers from review output, and recording the review tier and answers on
an attempt dict.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, MutableMapping

from agent_workflows import ipd_lint, ipd_schema

VALID_TIER_SOURCES = frozenset(("agent", "orchestrator", "raised"))


def tier_facts(plan_text: str) -> dict[str, Any]:
    """Compute the pre-pass tier facts from a plan's text.

    Returns a dict with seven keys:
      - kind: plan kind from '- Kind:' (str or None)
      - scope_paths: list of declared scope paths (list[str] or None)
      - names_spec: True if any scope path ends with '.spec.md' (bool)
      - e_items: count of E-* leaves (int)
      - task_groups: count of task-group H3s (int)
      - exceeds_size: True if size limits are exceeded (bool)
      - in_set: True if '- Set:' is present (bool)

    Pure; never raises on any plan text.
    """
    try:
        parsed = ipd_lint.parse(plan_text or "")
    except Exception:
        return {
            "kind": None,
            "scope_paths": None,
            "names_spec": False,
            "e_items": 0,
            "task_groups": 0,
            "exceeds_size": False,
            "in_set": False,
        }

    kind = parsed.meta_fields.get("Kind")

    raw_sp = parsed.meta_fields.get(ipd_schema.META_SCOPE_PATHS)
    scope_paths: list[str] | None = None
    if raw_sp is not None:
        trimmed = raw_sp.strip()
        if not (
            trimmed == "TODO"
            or trimmed.startswith("TODO ")
            or trimmed.startswith("TODO(")
            or trimmed.startswith("TODO:")
        ):
            scope_paths = [p.strip() for p in trimmed.split(",") if p.strip()]

    names_spec = bool(scope_paths and any(p.endswith(".spec.md") for p in scope_paths))

    e_items = sum(1 for lf in parsed.exec_leaves if lf.kind == "E")
    task_groups = parsed.exec_task_groups
    exceeds_size = ipd_schema.size_warning(task_groups, e_items)
    in_set = bool(parsed.meta_fields.get("Set"))

    return {
        "kind": kind,
        "scope_paths": scope_paths,
        "names_spec": names_spec,
        "e_items": e_items,
        "task_groups": task_groups,
        "exceeds_size": exceeds_size,
        "in_set": in_set,
    }


def render_tier_facts(facts: Mapping[str, Any]) -> str:
    """Render a short Markdown block summarizing the tier facts, one line per fact."""
    scope_paths = facts.get("scope_paths")
    if scope_paths is None:
        sp_str = "none declared"
    else:
        sp_str = ", ".join(scope_paths) if scope_paths else "none"

    lines = [
        f"- Kind: {facts.get('kind') or 'unknown'}",
        f"- In Set: {'yes' if facts.get('in_set') else 'no'}",
        f"- Execution items: {facts.get('e_items', 0)}",
        f"- Task groups: {facts.get('task_groups', 0)}",
        f"- Exceeds size limits: {'yes' if facts.get('exceeds_size') else 'no'}",
        f"- Names spec: {'yes' if facts.get('names_spec') else 'no'}",
        f"- Scope paths: {sp_str}",
    ]
    return "\n".join(lines)


def parse_tier_marker(reply_text: str) -> str | None:
    """Parse the AW-TIER reply marker from the last non-empty line of reply_text.

    The last non-empty line, after ignoring a trailing code-fence line and stripping
    leading and trailing whitespace, must equal exactly:
      AW-TIER: simple, AW-TIER: standard, or AW-TIER: complex (case-sensitive).
    Returns the tier name or None.
    """
    if not reply_text:
        return None
    lines = [line.strip() for line in reply_text.splitlines() if line.strip()]
    if not lines:
        return None
    if lines[-1].startswith("```") or lines[-1].startswith("~~~"):
        lines.pop()
    if not lines:
        return None
    last = lines[-1]
    if last == "AW-TIER: simple":
        return "simple"
    if last == "AW-TIER: standard":
        return "standard"
    if last == "AW-TIER: complex":
        return "complex"
    return None


def parse_tier_answers(review_text: str) -> dict[int, str] | None:
    """Find the last ## Round <n> section, then its ### Step T subsection,

    and return the answers to questions 1 to 5 as a dict[int, str].
    Returns None when the subsection is absent.
    """
    if not review_text:
        return None

    round_matches = list(
        re.finditer(r"^##\s+Round\b.*$", review_text, re.MULTILINE | re.IGNORECASE)
    )
    if round_matches:
        last_round_start = round_matches[-1].end()
        next_h2 = re.search(r"^##\s+.*$", review_text[last_round_start:], re.MULTILINE)
        round_text = (
            review_text[last_round_start : last_round_start + next_h2.start()]
            if next_h2
            else review_text[last_round_start:]
        )
    else:
        round_text = review_text

    step_t_match = re.search(
        r"^###\s+Step\s+T\b.*$", round_text, re.MULTILINE | re.IGNORECASE
    )
    if not step_t_match:
        return None

    step_t_start = step_t_match.end()
    next_heading = re.search(r"^#{2,3}\s+.*$", round_text[step_t_start:], re.MULTILINE)
    step_t_text = (
        round_text[step_t_start : step_t_start + next_heading.start()]
        if next_heading
        else round_text[step_t_start:]
    )

    q_re = re.compile(
        r"^\s*(?:[-*]\s+)?(?:Q([1-5])\s*[:.]|([1-5])\.)\s*(.*)$", re.IGNORECASE
    )
    answers: dict[int, str] = {}
    current_q: int | None = None
    for line in step_t_text.splitlines():
        m = q_re.match(line)
        if m:
            current_q = int(m.group(1) or m.group(2))
            answers[current_q] = m.group(3).strip()
        elif current_q is not None:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                if answers[current_q]:
                    answers[current_q] += " " + stripped
                else:
                    answers[current_q] = stripped
            elif not stripped:
                current_q = None

    return answers


def tier_answers_complete(answers: Mapping[Any, str] | None) -> bool:
    """Return True iff all five tier answers (1 to 5) are present and non-empty."""
    if not answers:
        return False
    for i in range(1, 6):
        val = answers.get(i)
        if val is None:
            val = answers.get(str(i))
        if val is None or not str(val).strip():
            return False
    return True


def record_review_tier(
    attempt: MutableMapping[str, Any],
    *,
    tier: str | None,
    source: str,
    answers: Mapping[int, str] | None,
    facts: Mapping[str, Any] | None,
) -> None:
    """Record review tier, source, answers, and facts on an attempt dict.

    Writes:
      attempt["review_tier"] = tier (one of REVIEW_DEPTH_VALUES, or None)
      attempt["review_tier_source"] = source ("agent", "orchestrator", "raised")
      attempt["review_tier_answers"] = dict with str keys "1".."5" (or None)
      attempt["review_tier_facts"] = dict of facts (or None)

    Raises ValueError if tier is invalid or source is invalid.
    """
    if tier is not None and tier not in ipd_schema.REVIEW_DEPTH_VALUES:
        raise ValueError(
            f"Invalid review tier: {tier!r}; expected one of "
            + ", ".join(sorted(ipd_schema.REVIEW_DEPTH_VALUES))
            + " or None"
        )
    if source not in VALID_TIER_SOURCES:
        raise ValueError(
            f"Invalid review tier source: {source!r}; expected one of "
            + ", ".join(sorted(VALID_TIER_SOURCES))
        )

    attempt["review_tier"] = tier
    attempt["review_tier_source"] = source
    attempt["review_tier_answers"] = (
        {str(k): str(v) for k, v in answers.items()} if answers is not None else None
    )
    attempt["review_tier_facts"] = dict(facts) if facts is not None else None

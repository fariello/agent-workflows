"""AW-REVIEW re-review marker parser, runner triggers, and bounded re-review loop.

Implements spec k3yx72 Section 8 and Set revsteps IPD is2xiv (Orders 01-05).
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import NamedTuple, Sequence

from agent_workflows import (
    ipd_lint,
    ipd_schema,
    review_sequence,
)


class RereviewResult(NamedTuple):
    """Result of the re-review loop."""

    outcome: str  # "done" | "limit-reached" | "incomplete"
    passes: int
    reasons: list[str]
    marker: str | None


def parse_rereview_marker(reply_text: str) -> str | None:
    """Parse the re-review marker per spec Section 8.1.

    Rules:
    1. Only the last non-empty line counts. The marker text elsewhere in the reply has no effect.
    2. Leading and trailing whitespace is ignored. The comparison is otherwise exact and
       case-sensitive against 'AW-REVIEW: AGAIN' and 'AW-REVIEW: DONE'. A trailing code fence
       line is ignored.
    3. Returns 'AGAIN', 'DONE', or None.
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
    if last == "AW-REVIEW: AGAIN":
        return "AGAIN"
    if last == "AW-REVIEW: DONE":
        return "DONE"
    return None


def rereview_triggers(
    pass_start_text: str,
    now_text: str,
    *,
    after_r_text: str | None,
) -> list[str]:
    """Compute runner re-review triggers per spec Section 8.2 and E-02.

    Over ipd_lint.parse:
    (a) The set of E-*/V-* ids differs between pass_start_text and now_text (added or removed, naming ids).
    (b) Scope-Paths meta value changed.
    (c) Item-Dependencies meta value changed.
    (d) When after_r_text is not None, structural_diff returns any confirm-only entry.
        after_r_text=None disables (d).

    The baseline for (a) to (c) is the plan at the start of the current pass.
    An empty list means no trigger.
    """
    doc_start = ipd_lint.parse(pass_start_text or "")
    doc_now = ipd_lint.parse(now_text or "")

    reasons: list[str] = []

    # (a) E-* and V-* id sets
    start_ids = {lf.ident for lf in doc_start.exec_leaves + doc_start.valid_leaves}
    now_ids = {lf.ident for lf in doc_now.exec_leaves + doc_now.valid_leaves}
    if start_ids != now_ids:
        added = sorted(now_ids - start_ids)
        removed = sorted(start_ids - now_ids)
        parts: list[str] = []
        if added:
            parts.append(f"added {', '.join(added)}")
        if removed:
            parts.append(f"removed {', '.join(removed)}")
        reasons.append(f"E/V items changed: {'; '.join(parts)}")

    # (b) Scope-Paths
    sp_start = doc_start.meta_fields.get("Scope-Paths")
    sp_now = doc_now.meta_fields.get("Scope-Paths")
    if sp_start != sp_now:
        reasons.append(f"Scope-Paths changed from {sp_start!r} to {sp_now!r}")

    # (c) Item-Dependencies
    dep_start = doc_start.meta_fields.get("Item-Dependencies")
    dep_now = doc_now.meta_fields.get("Item-Dependencies")
    if dep_start != dep_now:
        reasons.append(f"Item-Dependencies changed from {dep_start!r} to {dep_now!r}")

    # (d) Confirm-only changes after R2/R4
    if after_r_text is not None:
        _refused, confirm = review_sequence.structural_diff(after_r_text, now_text)
        if confirm:
            reasons.append(
                f"Confirm-listed items changed after R2/R4: {'; '.join(confirm)}"
            )

    return reasons


def limit_reached_instruction(result: RereviewResult) -> str:
    """Return instructions for S7 when the re-review limit is reached (spec Section 8.3, E-04)."""
    reasons_str = "; ".join(result.reasons) if result.reasons else "active changes"
    marker_str = result.marker or "AGAIN"
    return (
        "## Re-review pass limit reached\n\n"
        "Two re-review passes have run and changes or re-review requests are still active.\n"
        f"- Marker: {marker_str}\n"
        f"- Reasons: {reasons_str}\n\n"
        "You MUST:\n"
        "1. Set `- Readiness: no-go` in the plan front-matter.\n"
        f"2. Add an open question with `Blocking: yes` and `Status: open` explaining what still changed ({reasons_str}; marker: {marker_str}) "
        "so that `aw ipd recheck-readiness` can clear it after human review.\n"
    )


def check_limit_s7(plan_before: str, plan_after: str) -> str | None:
    """Postcondition check for S7 when re-review limit is reached (spec Section 8.3, E-04).

    Returns None when ipd_schema.read_readiness of plan_after is 'no-go'
    and ipd_lint.parse(plan_after).open_questions holds a question id
    absent from plan_before with Blocking: yes and Status: open;
    otherwise the failed postcondition text.
    """
    rd = ipd_schema.read_readiness(plan_after)
    if rd != "no-go":
        return "When re-review pass limit is reached, plan front-matter must specify `- Readiness: no-go`."

    try:
        doc_before = ipd_lint.parse(plan_before or "")
        doc_after = ipd_lint.parse(plan_after or "")
    except Exception as e:
        return f"Failed to parse plan for limit check: {e}"

    before_ids = {
        str(q.get("id") or "").strip() for q in doc_before.open_questions if q.get("id")
    }

    new_blocking_open = False
    for q in doc_after.open_questions:
        qid = str(q.get("id") or "").strip()
        if not qid or qid in before_ids:
            continue
        blk = str(q.get("Blocking") or "").strip().lower()
        st = str(q.get("Status") or "").strip().lower()
        if blk == "yes" and st == "open":
            new_blocking_open = True
            break

    if not new_blocking_open:
        return (
            "When re-review pass limit is reached, plan must add an open question "
            "with `Blocking: yes` and `Status: open`."
        )

    return None


def compute_plan_diff(before: str, after: str) -> str:
    """Compute git diff --no-index between before and after plan texts (spec Section 8.3)."""
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", delete=False
    ) as f1, tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f2:
        f1.write(before)
        f1.flush()
        f2.write(after)
        f2.flush()
        p1 = Path(f1.name)
        p2 = Path(f2.name)

    try:
        res = subprocess.run(
            ["git", "diff", "--no-index", str(p1), str(p2)],
            capture_output=True,
            text=True,
        )
        return res.stdout
    finally:
        p1.unlink(missing_ok=True)
        p2.unlink(missing_ok=True)


def rereview_prompt_groups(
    tier: str,
    variant: str,
    checks_run: set[str],
    *,
    in_set: bool = True,
    quick_ok: bool = False,
) -> list[tuple[str, ...]]:
    """Determine prompt groups for a re-review pass per spec Section 8.3 and E-03.

    Removes P, T, S5, S6, S7 and keeps only checks in checks_run, dropping empty groups.
    Then appends S5+S6. Never S7.
    """
    raw_groups = list(
        review_sequence.prompt_plan(tier, variant, in_set=in_set, quick_ok=quick_ok)
    )
    filtered: list[tuple[str, ...]] = []
    for grp in raw_groups:
        kept = tuple(
            c for c in grp if c not in {"P", "T", "S5", "S6", "S7"} and c in checks_run
        )
        if kept:
            filtered.append(kept)

    if any(grp == ("S6",) for grp in raw_groups):
        filtered.append(("S5",))
        filtered.append(("S6",))
    else:
        filtered.append(("S5", "S6"))

    return filtered


def render_rereview_prompt(
    group_checks: tuple[str, ...],
    pass_no: int,
    reasons: list[str],
    marker: str | None,
    plan_rel: str,
    *,
    is_first: bool = False,
    diff_text: str | None = None,
    all_pass_checks: Sequence[str] = (),
) -> str:
    """Render a re-review prompt per spec Section 8.3 and E-03."""
    base = review_sequence.render_prompt(
        group_checks,
        first=False,
        plan_rel=plan_rel,
    )
    lines = [base, ""]
    lines.append(f"## Re-review pass {pass_no}")
    lines.append("")
    lines.append(
        "Instruction: Limit your check to the changed sections and the sections that depend on them."
    )
    if reasons:
        lines.append(f"Trigger reasons: {'; '.join(reasons)}")
    if marker:
        lines.append(f"Starting marker: {marker}")

    if is_first:
        lines.append("")
        rerun_str = (
            ", ".join(all_pass_checks) if all_pass_checks else ", ".join(group_checks)
        )
        lines.append(
            f"Add a `### Pass {pass_no}` subsection to the current `## Round <n>` section in the review record "
            f"naming the checks re-run in this pass ({rerun_str})."
        )
        lines.append(
            "Record any history progress note only as `- <date> review progress (<agent/model>): ...`, "
            "never with a `/plan-review` label."
        )
        if diff_text and diff_text.strip():
            lines.append("")
            lines.append(
                "### Plan changes from start of previous pass to start of this pass:"
            )
            lines.append("```diff")
            lines.append(diff_text.rstrip())
            lines.append("```")

    return "\n".join(lines)


def run_rereview_loop(
    ctx: review_sequence.ReviewSequenceContext,
    s6_reply: str,
    *,
    after_r_text: str | None,
) -> RereviewResult:
    """Run the bounded re-review loop (spec Section 8.3, E-03).

    ctx: ReviewSequenceContext defines send_prompt, tier, variant, checks_run,
         plan_path, review_path, pass_start_text, pass_no, baseline, review_steps.
    s6_reply: S6 reply text from pass 1 (or empty string if resuming mid-pass).
    after_r_text: plan text after last prompt containing R2/R4 in pass 1.
    """
    plan_rel = ctx.plan_path.name
    groups = rereview_prompt_groups(ctx.tier, ctx.variant, ctx.checks_run)

    # Check if resuming inside an already-started re-review pass
    resuming_pass = False
    if ctx.pass_no >= 2:
        completed_in_pass = len(
            [s for s in ctx.review_steps if s.get("pass") == ctx.pass_no]
        )
        if completed_in_pass < len(groups):
            resuming_pass = True

    current_pass_start_text = ctx.pass_start_text
    current_reasons: list[str] = []
    current_marker: str | None = None

    if not resuming_pass:
        # 1. Parse initial S6 marker
        marker = parse_rereview_marker(s6_reply)
        if marker is None:
            reask_text = (
                "Your last reply did not end with the re-review marker. "
                "Reply with exactly one last line: AW-REVIEW: AGAIN or AW-REVIEW: DONE."
            )
            try:
                s6_reply = ctx.send_prompt(reask_text, ())
            except TypeError:
                s6_reply = ctx.send_prompt(reask_text)
            marker = parse_rereview_marker(s6_reply)
            if marker is None:
                return RereviewResult("incomplete", ctx.pass_no, [], None)

        # 2. Check triggers for current pass
        plan_text_now = ctx.plan_path.read_text(encoding="utf-8")
        triggers = rereview_triggers(
            ctx.pass_start_text, plan_text_now, after_r_text=after_r_text
        )

        if marker == "DONE" and not triggers:
            return RereviewResult("done", ctx.pass_no, [], "DONE")

        current_reasons = triggers
        current_marker = marker
        pass_to_run = 2
    else:
        pass_to_run = ctx.pass_no

    # Loop for re-review passes (up to 2 passes: pass 2 and pass 3)
    while pass_to_run <= 3:
        current_plan_text = ctx.plan_path.read_text(encoding="utf-8")
        if not resuming_pass:
            diff_text = compute_plan_diff(current_pass_start_text, current_plan_text)
            current_pass_start_text = current_plan_text
            if hasattr(ctx, "_replace"):
                ctx = ctx._replace(
                    pass_no=pass_to_run,
                    pass_start_text=current_pass_start_text,
                )
            else:
                ctx.pass_no = pass_to_run
                ctx.pass_start_text = current_pass_start_text
        else:
            diff_text = compute_plan_diff(current_pass_start_text, current_plan_text)
            resuming_pass = False

        all_checks = [c for grp in groups for c in grp]
        pass_after_r_text: str | None = None

        completed_in_pass = len(
            [s for s in ctx.review_steps if s.get("pass") == ctx.pass_no]
        )

        for i, grp in enumerate(groups):
            if i < completed_in_pass:
                if any(c in ("R2", "R4") for c in grp):
                    pass_after_r_text = ctx.plan_path.read_text(encoding="utf-8")
                continue

            is_first = i == 0
            p_text = render_rereview_prompt(
                grp,
                ctx.pass_no,
                current_reasons,
                current_marker,
                plan_rel,
                is_first=is_first,
                diff_text=diff_text,
                all_pass_checks=all_checks,
            )

            # Send prompt through Order 04's per-prompt path
            try:
                reply = ctx.send_prompt(p_text, grp, ctx.pass_no)
            except TypeError:
                try:
                    reply = ctx.send_prompt(p_text, grp)
                except TypeError:
                    reply = ctx.send_prompt(p_text)

            if any(c in ("R2", "R4") for c in grp):
                pass_after_r_text = ctx.plan_path.read_text(encoding="utf-8")
            if "S6" in grp:
                s6_reply = reply

        # Check marker from this pass's S6 reply
        marker = parse_rereview_marker(s6_reply)
        if marker is None:
            reask_text = (
                "Your last reply did not end with the re-review marker. "
                "Reply with exactly one last line: AW-REVIEW: AGAIN or AW-REVIEW: DONE."
            )
            try:
                s6_reply = ctx.send_prompt(reask_text, ())
            except TypeError:
                s6_reply = ctx.send_prompt(reask_text)
            marker = parse_rereview_marker(s6_reply)
            if marker is None:
                return RereviewResult("incomplete", ctx.pass_no, current_reasons, None)

        current_plan_text = ctx.plan_path.read_text(encoding="utf-8")
        current_reasons = rereview_triggers(
            ctx.pass_start_text,
            current_plan_text,
            after_r_text=pass_after_r_text,
        )
        current_marker = marker

        if current_marker == "DONE" and not current_reasons:
            return RereviewResult("done", ctx.pass_no, [], "DONE")

        pass_to_run += 1

    return RereviewResult("limit-reached", 3, current_reasons, current_marker)

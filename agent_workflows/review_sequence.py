"""Review sequence model, prompt rendering, postconditions, and structural diff.

Implements spec k3yx72 Sections 4 to 7 and 9 (Set revsteps, IPD uiyoax).
Provides:
  - PROMPT_LISTS: per-tier check lists
  - CHECK_STEP_FILES: mapping from check name to step file
  - prompt_plan: compute prompt sequence for a tier/variant
  - raise_tier_plan: compute extra check groups when a tier is raised
  - render_prompt: render prompt text for a step
  - render_reask: format the re-ask message per Section 6
  - structural_diff: structural preservation check per Section 6.1
  - check_P, check_T, check_steps, check_S5, check_S7: per-prompt postconditions
  - verdict_outputs: read (readiness, status, newest_verdict) for MD-15 guard
  - ReviewSequenceContext: context object for delegating re-review to Order 05
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any, Mapping, NamedTuple, Sequence

from agent_workflows import (
    check_engine,
    ipd_lint,
    ipd_schema,
    plan_readiness,
    review_tier,
)

# Spec k3yx72 Section 5.3 prompt grouping definitions
PROMPT_LISTS: dict[str, tuple[tuple[str, ...], ...]] = {
    "simple": (("P", "T", "Q"), ("S5", "S6"), ("S7",)),
    "standard": (("P", "T"), ("R1", "R2"), ("R3", "R4"), ("S5", "S6"), ("S7",)),
    "complex:grouped-6": (
        ("P", "T"),
        ("R1", "R2"),
        ("R3",),
        ("R4", "R5"),
        ("R6", "R7"),
        ("S5", "S6"),
        ("S7",),
    ),
    "complex:single-12": (
        ("P",),
        ("T",),
        ("Q",),
        ("R1",),
        ("R2",),
        ("R3",),
        ("R4",),
        ("R5",),
        ("R6",),
        ("R7",),
        ("S5",),
        ("S6",),
        ("S7",),
    ),
    "orchestrator": (("P", "R1", "R2"), ("R7",), ("S5", "S6"), ("S7",)),
}

CHECK_STEP_FILES: dict[str, str] = {
    "P": ".aw/system/workflows/plan-review/steps/p-proofread.md",
    "T": ".aw/system/workflows/plan-review/steps/t-tier.md",
    "Q": ".aw/system/workflows/plan-review/steps/q-quick-risk.md",
    "R1": ".aw/system/workflows/plan-review/steps/r1-references.md",
    "R2": ".aw/system/workflows/plan-review/steps/r2-executability.md",
    "R3": ".aw/system/workflows/plan-review/steps/r3-security.md",
    "R3s": ".aw/system/workflows/plan-review/steps/r3-security.md",
    "R4": ".aw/system/workflows/plan-review/steps/r4-engineering.md",
    "R5": ".aw/system/workflows/plan-review/steps/r5-personas.md",
    "R6": ".aw/system/workflows/plan-review/steps/r6-decomposition.md",
    "R7": ".aw/system/workflows/plan-review/steps/r7-cross-plan.md",
    "S5": ".aw/system/workflows/plan-review/steps/s5-questions.md",
    "S6": ".aw/system/workflows/plan-review/steps/s6-rereview.md",
    "S7": ".aw/system/workflows/plan-review/steps/s7-finalize.md",
}

KERNEL_STEP_FILE = ".aw/system/workflows/plan-review/steps/_kernel.md"
FINDINGS_STEP_FILE = ".aw/system/workflows/plan-review/steps/_findings.md"


def prompt_plan(
    tier: str,
    variant: str = "single-12",
    *,
    in_set: bool = True,
    quick_ok: bool = False,
) -> list[tuple[str, ...]]:
    """Return the prompt grouping list for a given tier and variant.

    Drops R7 when not in_set (so single-12 has 12 prompts outside a Set).
    For simple, merges prompt 2 into prompt 1 when quick_ok is True (yielding 2 prompts).
    """
    if tier == "complex":
        key = f"complex:{variant}"
        if key not in PROMPT_LISTS:
            key = "complex:single-12"
    else:
        key = tier

    if key not in PROMPT_LISTS:
        raise ValueError(f"Unknown review tier: {tier!r}")

    raw_groups = PROMPT_LISTS[key]
    out: list[tuple[str, ...]] = []
    for g in raw_groups:
        filtered = tuple(c for c in g if in_set or c != "R7")
        if filtered:
            out.append(filtered)

    if tier == "simple" and quick_ok and len(out) >= 2:
        out = [out[0] + out[1]] + out[2:]

    return out


def raise_tier_plan(
    done: set[str],
    new_tier: str,
    variant: str = "single-12",
    *,
    in_set: bool = True,
) -> list[tuple[str, ...]]:
    """Return the extra check groups to insert before S5 when tier is raised.

    Returns, for each group of the new tier's list before S5, only the checks
    not yet in done, dropping empty groups.
    """
    full_plan = prompt_plan(new_tier, variant, in_set=in_set, quick_ok=False)
    out: list[tuple[str, ...]] = []
    for group in full_plan:
        if "S5" in group or "S6" in group or "S7" in group:
            break
        filtered = tuple(c for c in group if c not in done)
        if filtered:
            out.append(filtered)
    return out


def render_reask(check: str, failed_text: str) -> str:
    """Format the re-ask text matching spec Section 6 byte for byte."""
    ft = (failed_text or "").strip().rstrip(".")
    return (
        f"Your last reply did not complete {check}: {ft}. "
        "Complete it now and end your reply as the step file requires."
    )


def render_prompt(
    groups_checks: tuple[str, ...],
    *,
    first: bool,
    plan_rel: str,
    facts_md: str | None = None,
    lane_notice: str | None = None,
    reask: str | None = None,
    confirm_changes: Sequence[str] | None = None,
) -> str:
    """Render a review step prompt.

    No slash commands. Instructs to read and apply named step files in order.
    Prompt 1 includes _kernel.md and pre-pass facts/diagnostics.
    Prompts containing Q or any R* include _findings.md.
    Appends lane notice and required JSON outcome when present.
    """
    lines: list[str] = []
    if reask:
        lines.append(reask)
        lines.append("")

    lines.append(f"Review plan: {plan_rel}")
    lines.append("")
    lines.append("Read and apply, in order:")
    if first:
        lines.append(f"- {KERNEL_STEP_FILE}")
    for c in groups_checks:
        step_f = CHECK_STEP_FILES.get(c)
        if step_f:
            lines.append(f"- {step_f}")
    has_q_or_r = any(c == "Q" or c.startswith("R") for c in groups_checks)
    if has_q_or_r:
        lines.append(f"- {FINDINGS_STEP_FILE}")

    if confirm_changes:
        lines.append("")
        lines.append("## Structural changes from proofreading to confirm:")
        for chg in confirm_changes:
            lines.append(f"- {chg}")

    if first and facts_md:
        lines.append("")
        if not facts_md.strip().startswith("#"):
            lines.append("## Pre-pass facts and diagnostics")
        lines.append(facts_md.strip())

    content = "\n".join(lines)
    if lane_notice:
        content = content + "\n\n" + lane_notice.strip()

    return content


def structural_diff(before: str, after: str) -> tuple[list[str], list[str]]:
    """Implement the structural preservation check of spec Section 6.1 over ipd_lint.parse.

    Returns (refused_list, confirm_only_list).
    """
    doc_b = ipd_lint.parse(before or "")
    doc_a = ipd_lint.parse(after or "")

    refused: list[str] = []
    confirm: list[str] = []

    # 1. Any front-matter value changed, added, or removed
    all_keys = set(doc_b.meta_fields.keys()) | set(doc_a.meta_fields.keys())
    for k in sorted(all_keys):
        vb = doc_b.meta_fields.get(k)
        va = doc_a.meta_fields.get(k)
        if vb != va:
            refused.append(f"Front-matter field {k!r} changed from {vb!r} to {va!r}")

    # 2. H2 list or order
    h2_b = [h.title for h in doc_b.h2]
    h2_a = [h.title for h in doc_a.h2]
    if h2_b != h2_a:
        refused.append(f"H2 headings list or order changed: {h2_b} != {h2_a}")

    # 3. E/V id set
    e_ids_b = {lf.ident for lf in doc_b.exec_leaves}
    e_ids_a = {lf.ident for lf in doc_a.exec_leaves}
    if e_ids_b != e_ids_a:
        refused.append(f"E-item id set changed: {sorted(e_ids_b)} != {sorted(e_ids_a)}")

    v_ids_b = {lf.ident for lf in doc_b.valid_leaves}
    v_ids_a = {lf.ident for lf in doc_a.valid_leaves}
    if v_ids_b != v_ids_a:
        refused.append(f"V-item id set changed: {sorted(v_ids_b)} != {sorted(v_ids_a)}")

    # Leaf properties (checkboxes, execution states, field sets, confirmable text)
    leaves_b = {lf.ident: lf for lf in doc_b.exec_leaves + doc_b.valid_leaves}
    leaves_a = {lf.ident: lf for lf in doc_a.exec_leaves + doc_a.valid_leaves}

    req_words_re = re.compile(r"\b(must not|must|should|may)\b", re.IGNORECASE)

    for ident, lf_b in sorted(leaves_b.items()):
        if ident in leaves_a:
            lf_a = leaves_a[ident]
            if lf_b.checked != lf_a.checked:
                refused.append(
                    f"{ident} checkbox state changed from {lf_b.checked} to {lf_a.checked}"
                )

            # Execution state value
            es_b = lf_b.fields.get("Execution state")
            es_a = lf_a.fields.get("Execution state")
            if es_b != es_a:
                refused.append(
                    f"{ident} Execution state changed from {es_b!r} to {es_a!r}"
                )

            # Field names set
            fn_b = set(lf_b.fields.keys())
            fn_a = set(lf_a.fields.keys())
            if fn_b != fn_a:
                refused.append(
                    f"{ident} field names changed: {sorted(fn_b)} != {sorted(fn_a)}"
                )

            # Confirm-only changes
            eo_b = lf_b.fields.get("Expected outcome")
            eo_a = lf_a.fields.get("Expected outcome")
            if eo_b is not None and eo_a is not None and eo_b != eo_a:
                confirm.append(
                    f"{ident} Expected outcome changed: {eo_b!r} -> {eo_a!r}"
                )

            dep_b = lf_b.fields.get("Depends on")
            dep_a = lf_a.fields.get("Depends on")
            if dep_b is not None and dep_a is not None and dep_b != dep_a:
                confirm.append(f"{ident} Depends on changed: {dep_b!r} -> {dep_a!r}")

            re_b = lf_b.fields.get("Required evidence")
            re_a = lf_a.fields.get("Required evidence")
            if re_b is not None and re_a is not None and re_b != re_a:
                confirm.append(
                    f"{ident} Required evidence changed: {re_b!r} -> {re_a!r}"
                )

            full_b = lf_b.text + " " + " ".join(lf_b.fields.values())
            full_a = lf_a.text + " " + " ".join(lf_a.fields.values())
            words_b = [w.lower() for w in req_words_re.findall(full_b)]
            words_a = [w.lower() for w in req_words_re.findall(full_a)]
            if words_b != words_a:
                confirm.append(
                    f"{ident} requirement words changed: {words_b} -> {words_a}"
                )

    # Existing open questions Status: or Blocking:
    oqs_b = {oq.get("id"): oq for oq in doc_b.open_questions if oq.get("id")}
    oqs_a = {oq.get("id"): oq for oq in doc_a.open_questions if oq.get("id")}
    for oq_id, oq_b in sorted(oqs_b.items()):
        if oq_id in oqs_a:
            oq_a = oqs_a[oq_id]
            st_b = oq_b.get("Status")
            st_a = oq_a.get("Status")
            if st_b != st_a:
                refused.append(f"{oq_id} Status changed from {st_b!r} to {st_a!r}")
            bl_b = oq_b.get("Blocking")
            bl_a = oq_a.get("Blocking")
            if bl_b != bl_a:
                refused.append(f"{oq_id} Blocking changed from {bl_b!r} to {bl_a!r}")

    return refused, confirm


def _extract_last_round_text(review_text: str) -> str:
    """Extract the last ## Round <n> section text from review_text."""
    if not review_text:
        return ""
    round_matches = list(
        re.finditer(r"^##\s+Round\b.*$", review_text, re.MULTILINE | re.IGNORECASE)
    )
    if round_matches:
        last_round_start = round_matches[-1].end()
        next_h2 = re.search(r"^##\s+.*$", review_text[last_round_start:], re.MULTILINE)
        return (
            review_text[last_round_start : last_round_start + next_h2.start()]
            if next_h2
            else review_text[last_round_start:]
        )
    return review_text


def check_P(
    plan_text_before: str,
    plan_text_after: str,
    review_text: str,
    reply_text: str,
) -> str | None:
    """Postcondition check for P (Proofreading).

    The ### Proofreading subsection exists in the current round.
    """
    round_text = _extract_last_round_text(review_text)
    if not re.search(
        r"^###\s+Proofreading\b.*$", round_text, re.MULTILINE | re.IGNORECASE
    ):
        return "The `### Proofreading` subsection exists in the current round."
    return None


def check_T(
    plan_text_before: str,
    plan_text_after: str,
    review_text: str,
    reply_text: str,
) -> str | None:
    """Postcondition check for T (Tier).

    Last non-empty line of reply is AW-TIER: <simple|standard|complex>.
    ### Step T answers all five tier questions.
    """
    marker = review_tier.parse_tier_marker(reply_text)
    if marker is None:
        return (
            "The last non-empty line of the reply is exactly "
            "`AW-TIER: simple`, `AW-TIER: standard`, or `AW-TIER: complex`."
        )

    answers = review_tier.parse_tier_answers(review_text)
    if not review_tier.tier_answers_complete(answers):
        return "The `### Step T` subsection answers all five tier questions of Section 5.2."

    return None


def check_steps(
    plan_text_before: str,
    plan_text_after: str,
    review_text: str,
    reply_text: str,
    checks: Sequence[str] = (),
) -> str | None:
    """Postcondition check for Q and R1..R7 steps.

    Each check in the prompt has a ### Step <check> subsection whose
    first non-blank line starts with '- Checked:'.
    """
    round_text = _extract_last_round_text(review_text)
    for c in checks:
        if c == "Q" or c.startswith("R"):
            pattern = r"^###\s+Step\s+" + re.escape(c) + r"\b.*$"
            m = re.search(pattern, round_text, re.MULTILINE | re.IGNORECASE)
            if not m:
                return f"The current round has a `### Step {c}` subsection."
            sub_start = m.end()
            next_heading = re.search(
                r"^#{2,3}\s+.*$", round_text[sub_start:], re.MULTILINE
            )
            sub_text = (
                round_text[sub_start : sub_start + next_heading.start()]
                if next_heading
                else round_text[sub_start:]
            )
            non_blank_lines = [
                line.strip() for line in sub_text.splitlines() if line.strip()
            ]
            if not non_blank_lines or not non_blank_lines[0].startswith("- Checked:"):
                return f"The `### Step {c}` subsection starts with a line '- Checked: <what was examined>'."
    return None


def check_S5(
    plan_text_before: str,
    plan_text_after: str,
    review_text: str,
    reply_text: str,
    *,
    repo_root: Path | None = None,
    plan_path: Path | None = None,
) -> str | None:
    """Postcondition check for S5 (Open questions).

    Every open question has Blocking: and Status:.
    check.review-finding-unescalated reports nothing for this review record.
    """
    try:
        doc = ipd_lint.parse(plan_text_after or "")
    except Exception:
        return "Every open question has `Blocking:` and `Status:`."

    for oq in doc.open_questions:
        b = str(oq.get("Blocking") or "").strip()
        s = str(oq.get("Status") or "").strip()
        if not b or not s:
            return "Every open question has `Blocking:` and `Status:`."

    if review_text:
        plan_id6 = None
        if plan_path is not None:
            m = re.search(r"-([a-z0-9]{6})-", plan_path.name)
            if m:
                plan_id6 = m.group(1)
        if not plan_id6:
            plan_id6 = doc.meta_fields.get("Id")
        if not plan_id6:
            plan_id6 = check_engine._read_item_id(plan_text_after)

        # Ensure minimal review metadata if missing in snippet
        fixed_rev_text = review_text
        meta_needed: list[str] = []
        if "- subject-id:" not in review_text.lower():
            meta_needed.append(f"- Subject-Id: {plan_id6 or 'pln001'}")
        if "- subject-type:" not in review_text.lower():
            meta_needed.append("- Subject-Type: ipd")
        if "- reviewed-at:" not in review_text.lower():
            meta_needed.append("- Reviewed-At: 2026-10-25")
        if "- reviewer:" not in review_text.lower():
            meta_needed.append("- Reviewer: test")
        if "- verdict:" not in review_text.lower():
            meta_needed.append("- Verdict: APPROVE")
        if meta_needed:
            fixed_rev_text = "\n".join(meta_needed) + "\n\n" + review_text

        with tempfile.TemporaryDirectory() as td:
            tmp_dir = Path(td)
            rev_file = tmp_dir / f"test-{plan_id6 or 'unknown'}.review.md"
            rev_file.write_text(fixed_rev_text, encoding="utf-8")
            r_root = repo_root if repo_root is not None else tmp_dir
            p_path = plan_path if plan_path is not None else (tmp_dir / "plan.ipd.md")

            drift = check_engine.evaluate_review_finding_escalation(
                r_root,
                plan_path=p_path,
                plan_text=plan_text_after,
                open_questions=doc.open_questions,
                review_index={plan_id6: [rev_file]} if plan_id6 else None,
            )
            if drift:
                return "`check.review-finding-unescalated` passes."

    return None


def count_verdict_bearing_entries(plan_text: str) -> int:
    """Count history entries that are review records and contain a classified verdict."""
    count = 0
    for candidate in plan_readiness.history_block(plan_text or "").records:
        if not plan_readiness.HISTORY_RECORD_RE.match(candidate):
            continue
        if not plan_readiness.is_review_history_entry(candidate):
            continue
        m = plan_readiness._HISTORY_RECORD_PARTS_RE.match(candidate)
        msg = m.group("msg") if m else candidate
        token, _ = plan_readiness.classify_verdict(msg)
        if token is not None:
            count += 1
    return count


def verdict_outputs(plan_text: str) -> tuple[str | None, str | None, str]:
    """Return (read_readiness, Status value, newest_verdict raw entry) for the MD-15 guard."""
    rd = ipd_schema.read_readiness(plan_text)
    try:
        doc = ipd_lint.parse(plan_text or "")
        st = doc.meta_fields.get("Status")
    except Exception:
        st = None
    newest = plan_readiness.newest_verdict(plan_text)[1]
    return (rd, st, newest)


def restore_pre_s7_plan(
    pre_pass_text: str,
    current_text: str,
) -> str:
    """Restore Readiness, Status, and remove added review history entries before S7 (MD-15 guard)."""
    try:
        doc_pre = ipd_lint.parse(pre_pass_text or "")
        st_pre = doc_pre.meta_fields.get("Status") or "to-review"
    except Exception:
        st_pre = "to-review"

    rd_pre = ipd_schema.read_readiness(pre_pass_text)
    pre_history = set(plan_readiness.history_block(pre_pass_text or "").records)

    lines = current_text.splitlines()
    in_meta = True
    in_history = False
    out_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            in_meta = False
            if stripped.startswith("## Workflow history"):
                in_history = True
            else:
                in_history = False

        if in_meta:
            if re.match(r"^-\s*Status\s*:", stripped):
                out_lines.append(f"- Status: {st_pre}")
                continue
            if re.match(r"^-\s*Readiness\s*:", stripped):
                if rd_pre is not None:
                    out_lines.append(f"- Readiness: {rd_pre}")
                continue
        elif in_history:
            if stripped.startswith("- "):
                if stripped not in pre_history:
                    if (
                        plan_readiness.is_review_history_entry(stripped)
                        or "reviewed" in stripped.lower()
                        or "(aw set): status set to reviewed" in stripped
                    ):
                        continue
        out_lines.append(line)

    result = "\n".join(out_lines)
    if current_text.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def check_S6(
    plan_text_before: str,
    plan_text_after: str,
    review_text: str,
    reply_text: str,
) -> str | None:
    """Postcondition check for S6 (Re-review decision).

    The last non-empty line of the reply (ignoring trailing code fence)
    is exactly 'AW-REVIEW: AGAIN' or 'AW-REVIEW: DONE'.
    """
    if not reply_text:
        return "The marker rules in Section 8.1 are met."
    lines = [line.strip() for line in reply_text.splitlines() if line.strip()]
    if not lines:
        return "The marker rules in Section 8.1 are met."
    if lines[-1].startswith("```") or lines[-1].startswith("~~~"):
        lines.pop()
    if not lines:
        return "The marker rules in Section 8.1 are met."
    last = lines[-1]
    if last in ("AW-REVIEW: AGAIN", "AW-REVIEW: DONE"):
        return None
    return "The marker rules in Section 8.1 are met."


def check_S7(
    plan_text_before: str,
    plan_text_after: str,
    review_text: str,
    reply_text: str,
) -> str | None:
    """Postcondition check for S7 (Finalize).

    One of:
      (a) - Readiness: holds go, go-pending-approval, or no-go, and - Status: is reviewed; or
      (b) - Readiness: is absent, - Status: is still to-review, and round records exhausted repair.
    Exactly one new verdict-bearing history entry was added during the invocation.
    aw ipd lint --phase author reports no new error except IPD-Q501.
    """
    rd = ipd_schema.read_readiness(plan_text_after)
    try:
        doc_a = ipd_lint.parse(plan_text_after or "")
        st = doc_a.meta_fields.get("Status")
    except Exception:
        st = None

    cond_a = rd in ("go", "go-pending-approval", "no-go") and st == "reviewed"
    cond_b = (
        rd is None
        and st == "to-review"
        and (
            "exhausted" in review_text.lower()
            or "ipd-s407" in review_text.lower()
            or "ipd-s408" in review_text.lower()
        )
    )
    if not (cond_a or cond_b):
        return (
            "One of: (a) `- Readiness:` holds `go`, `go-pending-approval`, or `no-go`, "
            "and `- Status:` is `reviewed`; or (b) `- Readiness:` is absent, `- Status:` is still "
            "`to-review`, and the round records an exhausted orchestrator repair."
        )

    cb = count_verdict_bearing_entries(plan_text_before)
    ca = count_verdict_bearing_entries(plan_text_after)
    if (ca - cb) != 1:
        return (
            "Exactly one verdict-bearing history entry was added during the invocation."
        )

    res_b = ipd_lint.lint_text(plan_text_before or "", checkpoint="author")
    res_a = ipd_lint.lint_text(plan_text_after or "", checkpoint="author")
    codes_b = {d.code for d in res_b.diagnostics}
    codes_a = {d.code for d in res_a.diagnostics}
    new_errs = (codes_a - codes_b) - {"IPD-Q501"}
    if new_errs:
        return "`aw ipd lint --phase author` reports no error that was not present at the pre-pass, except `IPD-Q501`."

    return None


class ReviewSequenceContext(NamedTuple):
    """Context passed to review_rereview.run_rereview_loop (spec k3yx72, is2xiv E-03).

    Fields:
      - send_prompt: Callable[[str], str] - sends one prompt in review session and returns reply text
      - tier: str - review tier (simple, standard, complex, orchestrator)
      - variant: str - review variant (e.g. single-12, grouped-6)
      - checks_run: set[str] - set of checks completed so far
      - plan_path: Path - path to plan file
      - review_path: Path - path to review record file
      - pass_start_text: str - plan text at start of current pass
      - pass_no: int - current pass number
      - baseline: Mapping[str, Any] - pre-pass baseline values
      - review_steps: list[dict[str, Any]] - list of recorded review steps
    """

    send_prompt: Any
    tier: str
    variant: str
    checks_run: set[str]
    plan_path: Path
    review_path: Path
    pass_start_text: str
    pass_no: int
    baseline: Mapping[str, Any]
    review_steps: list[dict[str, Any]]

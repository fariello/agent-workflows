"""Responsive Option 2 runner statusbar layout, queue telemetry, and artifact title helpers.

Renders the 3-metric-row boxed runner statusbar (5 lines without an artifact description,
or 7 lines with the full-width top artifact description row + divider inside the box):

  - Expands and contracts cleanly to any terminal width (64..200+ cols).
  - Preserves the full ``run_id`` centered on the top border (truncating model and CWD
    first so ``run_id`` remains copy-pasteable).
  - Styles ``set: <setid>`` identically to ``id6: <id6>``.
  - Displays ETA, avg time/item, avg time/step, validation error count, retry/fix-it
    counts, attempt counter, and per-item spend/step tokens.
  - Under ``agy`` when local quota data is available, displays the model-filtered 5h|weekly
    quota bar (Gemini-only for Gemini models, 3P-only for Claude/Opus or GPT models) with
    bold-red ``!!`` burnout warnings.
  - Renders the rounded CWD pill on the top-right and the matching rounded slate questions
    pill (``? N question(s) · aw runs answer``) on the bottom-right.
"""

from __future__ import annotations

import datetime as dt
import re
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from agent_workflows import agy_quota as _aq
from agent_workflows import term as _T

_ANSI_RESET = "\033[0m"
_ANSI_STRIP_RE = re.compile(r"\033\[[0-9;]*m")

DEFAULT_STATUSLINE_WIDTH = 140
MIN_STATUSLINE_WIDTH = 64

_ACTION_GLYPHS: dict[str, str] = {
    "execute": "▶",
    "review": "🆁",
    "plan": "⇑",
    "graduate": "⇑",
    "validate": "☑",
    "verify": "☑",
    "re-run": "↻",
    "rerun": "↻",
    "integrate": "⇄",
    "orchestrate": "▶",
}


def _strip_ansi(text: str) -> str:
    return _ANSI_STRIP_RE.sub("", text)


def _one_line_clean(text: Any) -> str:
    if text is None:
        return ""
    return re.sub(r"[\r\n\t]+", " ", str(text)).strip()


def format_compact_duration(seconds: float | int | None) -> str:
    """Format a duration compactly for ETA and pace cells (e.g. '1h16m', '12m00s', '45s')."""
    if seconds is None:
        return "--"
    secs = max(0, int(round(float(seconds))))
    if secs >= 3600:
        h, rem = divmod(secs, 3600)
        m = rem // 60
        return f"{h}h{m:02d}m"
    if secs >= 60:
        m, s = divmod(secs, 60)
        return f"{m}m{s:02d}s"
    return f"{secs}s"


def _parse_iso_ts(raw: Any) -> Optional[float]:
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str) and raw.strip():
        try:
            return dt.datetime.fromisoformat(
                raw.strip().replace("Z", "+00:00")
            ).timestamp()
        except Exception:
            return None
    return None


def resolve_artifact_title(
    item: Optional[Mapping[str, Any]],
    repo: Path | str | None = None,
) -> str:
    """Resolve a human-readable one-line title/description for a queue artifact."""
    if not isinstance(item, Mapping):
        return ""
    for key in ("title", "description", "summary"):
        val = _one_line_clean(item.get(key))
        if val:
            return val

    # Try reading the first markdown '# Heading' from the artifact file on disk.
    raw_file = (
        item.get("file")
        or item.get("configured_file")
        or item.get("path")
        or item.get("plan_path")
    )
    if isinstance(raw_file, (str, Path)) and str(raw_file).strip():
        cand = Path(str(raw_file).strip())
        if not cand.is_absolute() and repo is not None:
            cand = Path(repo) / cand
        try:
            if cand.is_file():
                with cand.open("r", encoding="utf-8", errors="replace") as fh:
                    for _ in range(40):
                        line = fh.readline()
                        if not line:
                            break
                        stripped = line.strip()
                        if stripped.startswith("# "):
                            title = stripped[2:].strip().replace("`", "")
                            title = re.sub(r"^IPD:\s*", "", title, flags=re.IGNORECASE)
                            if title:
                                return _one_line_clean(title)
        except OSError:
            pass

    slug = _one_line_clean(item.get("slug"))
    if slug:
        return slug.replace("-", " ").capitalize()
    return ""


def compute_queue_telemetry(
    state: Optional[Mapping[str, Any]],
    *,
    current_item: Optional[Mapping[str, Any]] = None,
    now_ts: Optional[float] = None,
    run_start_ts: Optional[float] = None,
) -> dict[str, Any]:
    """Compute ETA, avg time/item, avg time/step, validation errors, retries, fix-its, attempt."""
    out: dict[str, Any] = {
        "eta_seconds": None,
        "avg_item_seconds": None,
        "avg_step_seconds": None,
        "validation_errors": 0,
        "retries": 0,
        "fix_its": 0,
        "attempt_no": 1,
        "retry_budget": 2,
    }
    if not isinstance(state, Mapping):
        return out

    opts = state.get("options")
    if isinstance(opts, Mapping):
        rb = opts.get("retry_budget")
        if isinstance(rb, int) and rb >= 0:
            out["retry_budget"] = rb

    queue = state.get("queue")
    if not isinstance(queue, list):
        return out

    completed_item_durs: list[float] = []
    step_durs: list[float] = []
    val_errors = 0
    retries = 0
    fix_its = 0
    completed_count = 0
    remaining_count = 0

    for entry in queue:
        if not isinstance(entry, Mapping):
            continue
        status = str(entry.get("status") or "").strip()
        action = str(entry.get("action") or "").strip()
        if action == "skip":
            continue

        attempts = entry.get("attempts")
        att_list = attempts if isinstance(attempts, list) else []
        if len(att_list) > 1:
            retries += len(att_list) - 1
        elif entry.get("requeue_from_status"):
            retries += 1

        item_dur_sum = 0.0
        item_has_dur = False
        for att in att_list:
            if not isinstance(att, Mapping):
                continue
            s_ts = _parse_iso_ts(att.get("started_at"))
            e_ts = _parse_iso_ts(att.get("ended_at"))
            if s_ts is not None and e_ts is not None and e_ts >= s_ts:
                dur = e_ts - s_ts
                step_durs.append(dur)
                item_dur_sum += dur
                item_has_dur = True

            # Validation errors: failed suite checks, failed verifier verdicts, or fail-verify
            suite_chk = att.get("suite_check")
            if isinstance(suite_chk, Mapping) and suite_chk.get("passing") is False:
                val_errors += 1
            disp = str(att.get("disposition") or "")
            verdict = str(
                att.get("verify_verdict") or att.get("verifier_verdict") or ""
            ).lower()
            if disp == "fail-verify" or verdict in (
                "fail",
                "failed",
                "reject",
                "rejected",
                "no-go",
            ):
                val_errors += 1

            # Fix-it / correction turns
            c_turns = att.get("correction_turns")
            if isinstance(c_turns, int) and c_turns > 0:
                fix_its += c_turns
                retries += c_turns
            for sb_key in (
                "hook_refusal_sendback",
                "combined_red_sendback",
                "anchor_missing_sendback",
            ):
                sb = att.get(sb_key)
                if isinstance(sb, list) and sb:
                    fix_its += len(sb)
                    retries += len(sb)

        if status in ("queued", "running", "in-progress"):
            remaining_count += 1
        elif status not in ("not-run", "not-started", "skipped"):
            completed_count += 1
            if item_has_dur:
                completed_item_durs.append(item_dur_sum)

    if current_item is not None:
        cur_atts = current_item.get("attempts")
        if isinstance(cur_atts, list) and cur_atts:
            out["attempt_no"] = len(cur_atts)
        else:
            out["attempt_no"] = 1

    avg_item_s: Optional[float] = None
    if completed_item_durs:
        avg_item_s = sum(completed_item_durs) / len(completed_item_durs)
    elif completed_count > 0 and now_ts is not None and run_start_ts is not None:
        elapsed = max(0.0, float(now_ts) - float(run_start_ts))
        if elapsed > 0:
            avg_item_s = elapsed / completed_count

    avg_step_s: Optional[float] = (
        (sum(step_durs) / len(step_durs)) if step_durs else None
    )

    eta_s: Optional[float] = None
    if avg_item_s is not None and remaining_count > 0:
        eta_s = avg_item_s * remaining_count

    out["eta_seconds"] = eta_s
    out["avg_item_seconds"] = avg_item_s
    out["avg_step_seconds"] = avg_step_s
    out["validation_errors"] = val_errors
    out["retries"] = retries
    out["fix_its"] = fix_its
    return out


def _distribute_widths(
    mins: Sequence[int], weights: Sequence[float], total_inner: int
) -> list[int]:
    n = len(mins)
    widths = list(mins)
    extra = total_inner - sum(widths)
    if extra > 0:
        w_sum = sum(weights) or 1.0
        adds = [int(extra * (w / w_sum)) for w in weights]
        rem = extra - sum(adds)
        order = sorted(range(n), key=lambda i: weights[i], reverse=True)
        for i in range(rem):
            adds[order[i % n]] += 1
        widths = [w + a for w, a in zip(widths, adds)]
    elif extra < 0:
        deficit = -extra
        for _ in range(deficit):
            widest = max(range(n), key=lambda i: widths[i])
            if widths[widest] <= 6:
                break
            widths[widest] -= 1
    return widths


def _pad_pair(
    colored: str,
    plain: str,
    width: int,
    *,
    align: str = "left",
    use_unicode: bool = True,
) -> tuple[str, str]:
    """Pad or truncate (colored, plain) in lockstep to exact visible width."""
    ell = "…" if use_unicode else "."
    pw = _T.visible_width(plain)
    if pw > width:
        plain = _T.truncate_visible(plain, width, ellipsis=ell)
        colored = _T.truncate_visible(colored, width, ellipsis=ell)
        pw = _T.visible_width(plain)
    rem = max(0, width - pw)
    if align == "right":
        pad = " " * rem
        return pad + colored, pad + plain
    if align == "center":
        left = " " * (rem // 2)
        right = " " * (rem - len(left))
        return left + colored + right, left + plain + right
    pad = " " * rem
    return colored + pad, plain + pad


def _render_border_pair(
    width: int,
    *,
    left_ch: str,
    right_ch: str,
    fill_ch: str,
    left_c: str = "",
    left_p: str = "",
    center_c: str = "",
    center_p: str = "",
    right_c: str = "",
    right_p: str = "",
    junctions: Sequence[tuple[int, str]] = (),
    bdr_color: str = "",
    reset: str = "",
    use_unicode: bool = True,
) -> tuple[str, str]:
    """Build (colored, plain) exact-width border lines with true horizontal centering."""
    inner_w = max(2, width - 2)
    ell = "…" if use_unicode else "."

    l_w = _T.visible_width(left_p)
    r_w = _T.visible_width(right_p)
    c_w = _T.visible_width(center_p)

    # Trim right/left ONLY if they exceed inner_w (center is never trimmed before sides).
    max_r = min(r_w, max(0, inner_w - 2))
    if r_w > max_r:
        right_p = _T.truncate_visible(right_p, max_r, ellipsis=ell)
        right_c = _T.truncate_visible(right_c, max_r, ellipsis=ell)
        r_w = _T.visible_width(right_p)
    max_l = max(0, inner_w - r_w - (1 if r_w else 0))
    if l_w > max_l:
        left_p = _T.truncate_visible(left_p, max_l, ellipsis=ell)
        left_c = _T.truncate_visible(left_c, max_l, ellipsis=ell)
        l_w = _T.visible_width(left_p)

    rem_mid = max(0, inner_w - l_w - r_w)
    chars = [fill_ch] * rem_mid
    for pos, jch in junctions:
        rel = pos - l_w
        if 0 <= rel < rem_mid:
            chars[rel] = jch

    if c_w > 0 and c_w + 2 <= rem_mid:
        ideal_start = (inner_w - c_w) // 2
        clamped_start = max(l_w + 1, min(inner_w - r_w - c_w - 1, ideal_start))
        pad_l = clamped_start - l_w
        seg_l = "".join(chars[:pad_l])
        seg_r = "".join(chars[pad_l + c_w :])
        mid_p = seg_l + center_p + seg_r
        mid_c = f"{bdr_color}{seg_l}{center_c}{bdr_color}{seg_r}"
    else:
        seg = "".join(chars)
        mid_p = seg
        mid_c = f"{bdr_color}{seg}"

    plain_line = f"{left_ch}{left_p}{mid_p}{right_p}{right_ch}"
    if not bdr_color:
        return plain_line, plain_line
    color_line = (
        f"{bdr_color}{left_ch}{left_c}{mid_c}{right_c}{bdr_color}{right_ch}{reset}"
    )
    return color_line, plain_line


def _join_fitting_pairs(
    segments: Sequence[tuple[int, str, str]],
    max_w: int,
    sep_c: str,
    sep_p: str,
) -> tuple[str, str]:
    """Include priority-ordered (prio, colored, plain) segments fitting max_w in original order."""
    sep_w = _T.visible_width(sep_p)
    indexed = list(enumerate(segments))
    by_prio = sorted(indexed, key=lambda x: (x[1][0], x[0]))
    chosen: set[int] = set()
    used = 0
    for idx, (_prio, _c, p_txt) in by_prio:
        tw = _T.visible_width(p_txt)
        added = tw if not chosen else (sep_w + tw)
        if used + added <= max_w:
            chosen.add(idx)
            used += added
    ordered_c = [c_txt for idx, (_p, c_txt, _pt) in indexed if idx in chosen]
    ordered_p = [p_txt for idx, (_p, _ct, p_txt) in indexed if idx in chosen]
    return sep_c.join(ordered_c), sep_p.join(ordered_p)


def _format_quota_dur_pair(
    seconds: int,
    *,
    c_clock: str,
    c_unit: str,
    reset: str,
) -> tuple[str, str]:
    seconds = max(0, int(seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins = rem // 60
    if days > 0:
        plain = f"{days}d{hours}h"
        colored = (
            f"{c_clock}{days}{c_unit}d{c_clock}{hours}{c_unit}h{reset}"
            if c_clock
            else plain
        )
        return colored, plain
    if hours > 0:
        plain = f"{hours}h{mins:02d}m"
        colored = (
            f"{c_clock}{hours}{c_unit}h{c_clock}{mins:02d}{c_unit}m{reset}"
            if c_clock
            else plain
        )
        return colored, plain
    plain = f"{mins}m"
    colored = f"{c_clock}{mins}{c_unit}m{reset}" if c_clock else plain
    return colored, plain


def _format_quota_bucket_pair(
    bucket: Optional[_aq.QuotaBucket],
    *,
    cells: int,
    use_unicode: bool,
    color_enabled: bool,
    tier: str,
    sgr256: Callable[..., str],
    c_clock: str,
    c_unit: str,
    c_burn: str,
    c_muted: str,
    reset: str,
) -> tuple[str, str]:
    if bucket is None:
        p = "n/a"
        return (f"{c_muted}{p}{reset}" if color_enabled else p, p)
    pct = max(0, min(100, int(bucket.remaining_pct)))
    cells = max(4, cells)
    filled = cells if pct == 100 else min(cells - 1, int(pct * cells / 100))
    empty = cells - filled
    bar = ("█" * filled + "░" * empty) if use_unicode else ("#" * filled + "." * empty)
    dur_c, dur_p = _format_quota_dur_pair(
        bucket.reset_in_s, c_clock=c_clock, c_unit=c_unit, reset=reset
    )
    bang_p = "!!" if bucket.will_burn_out else ""
    bang_c = (
        f"{c_burn}!!{reset}" if (color_enabled and bucket.will_burn_out) else bang_p
    )
    plain = f"{dur_p} {bar}{pct}%{bang_p}"
    if not color_enabled:
        return plain, plain
    code, bold = _aq.quota_color_code_256(pct)
    qcol = sgr256(code, bold=bold, depth=tier)
    colored = f"{dur_c} {qcol}{bar}{pct}%{reset}{bang_c}"
    return colored, plain


def _format_agy_quota_rows(
    agy_quota: _aq.AgyQuotaSnapshot,
    model: Optional[str],
    *,
    max_w: int,
    use_unicode: bool,
    color_enabled: bool,
    tier: str,
    sgr256: Callable[..., str],
    bdr_color: str,
    c_hdr: str,
    c_clock: str,
    c_unit: str,
    c_burn: str,
    c_muted: str,
    reset: str,
) -> tuple[tuple[str, str], tuple[str, str]]:
    """Return ((r2_c, r2_p), (r3_c, r3_p)) for agy model-filtered quota + burnout note."""
    pool = _aq.model_quota_pool(model)
    if pool == "gemini":
        b5, bw = agy_quota.gemini_5h, agy_quota.gemini_weekly
        lbl_p = "Gem:"
        lbl_c = (
            f"{sgr256(51, bold=True, depth=tier)}Gem{bdr_color}:{reset}"
            if color_enabled
            else lbl_p
        )
    elif pool == "claude":
        b5, bw = agy_quota.tp_5h, agy_quota.tp_weekly
        lbl_p = "Opus:"
        lbl_c = (
            f"{sgr256(213, bold=True, depth=tier)}Opus{bdr_color}:{reset}"
            if color_enabled
            else lbl_p
        )
    else:
        b5, bw = agy_quota.tp_5h, agy_quota.tp_weekly
        lbl_p = "GPT:"
        lbl_c = (
            f"{sgr256(141, bold=True, depth=tier)}GPT{bdr_color}:{reset}"
            if color_enabled
            else lbl_p
        )

    pipe_p = "|"
    pipe_c = f"{bdr_color}|{reset}" if color_enabled else pipe_p

    for use_lbl, cells in ((True, 9), (False, 9), (False, 6), (False, 4)):
        c5, p5 = _format_quota_bucket_pair(
            b5,
            cells=cells,
            use_unicode=use_unicode,
            color_enabled=color_enabled,
            tier=tier,
            sgr256=sgr256,
            c_clock=c_clock,
            c_unit=c_unit,
            c_burn=c_burn,
            c_muted=c_muted,
            reset=reset,
        )
        cw_b, pw_b = _format_quota_bucket_pair(
            bw,
            cells=cells,
            use_unicode=use_unicode,
            color_enabled=color_enabled,
            tier=tier,
            sgr256=sgr256,
            c_clock=c_clock,
            c_unit=c_unit,
            c_burn=c_burn,
            c_muted=c_muted,
            reset=reset,
        )
        cand_p = f"{lbl_p if use_lbl else ''}{p5}{pipe_p}{pw_b}"
        if _T.visible_width(cand_p) <= max_w:
            cand_c = f"{lbl_c if use_lbl else ''}{c5}{pipe_c}{cw_b}"
            burn_c_parts: list[str] = []
            burn_p_parts: list[str] = []
            if b5 is not None and b5.will_burn_out:
                z = (
                    f"~{format_compact_duration(b5.zero_in_s)}"
                    if b5.zero_in_s is not None
                    else "soon"
                )
                txt = f"!! 5h out {z}"
                burn_p_parts.append(txt)
                burn_c_parts.append(f"{c_burn}{txt}{reset}" if color_enabled else txt)
            if bw is not None and bw.will_burn_out:
                z = (
                    f"~{format_compact_duration(bw.zero_in_s)}"
                    if bw.zero_in_s is not None
                    else "soon"
                )
                txt = f"!! wk out {z}"
                burn_p_parts.append(txt)
                burn_c_parts.append(f"{c_burn}{txt}{reset}" if color_enabled else txt)
            sep_dot_p = " · " if use_unicode else " - "
            sep_dot_c = f"{c_muted}{sep_dot_p}{reset}" if color_enabled else sep_dot_p
            return (
                (cand_c, cand_p),
                (sep_dot_c.join(burn_c_parts), sep_dot_p.join(burn_p_parts)),
            )

    # Narrow stacked fallback: 5h on Row 2, weekly on Row 3
    c5, p5 = _format_quota_bucket_pair(
        b5,
        cells=6,
        use_unicode=use_unicode,
        color_enabled=color_enabled,
        tier=tier,
        sgr256=sgr256,
        c_clock=c_clock,
        c_unit=c_unit,
        c_burn=c_burn,
        c_muted=c_muted,
        reset=reset,
    )
    cw_b, pw_b = _format_quota_bucket_pair(
        bw,
        cells=6,
        use_unicode=use_unicode,
        color_enabled=color_enabled,
        tier=tier,
        sgr256=sgr256,
        c_clock=c_clock,
        c_unit=c_unit,
        c_burn=c_burn,
        c_muted=c_muted,
        reset=reset,
    )
    r2_p = f"5h {p5}"
    r3_p = f"wk {pw_b}"
    r2_c = f"{c_hdr}5h {reset}{c5}" if color_enabled else r2_p
    r3_c = f"{c_hdr}wk {reset}{cw_b}" if color_enabled else r3_p
    return ((r2_c, r2_p), (r3_c, r3_p))


def format_questions_pill(
    parked_questions: int | None,
    *,
    max_w: int = 80,
    use_unicode: bool = True,
    color_enabled: bool = True,
    tier: str = _T.DEPTH_256,
    sgr256: Callable[..., str],
    sgr_bg256: Callable[..., str],
    sgr_dark_fg: Callable[..., str],
    bdr_color: str = "",
) -> tuple[str, str]:
    """Return ``(colored, plain)`` rounded slate pill for open questions (matching CWD pill)."""
    if parked_questions is None or parked_questions < 1:
        return ("", "")
    n_q = int(parked_questions)
    noun = "question" if n_q == 1 else "questions"
    sep = " · " if use_unicode else " - "
    candidates = [
        f"? {n_q} {noun}{sep}aw runs answer",
        f"? {n_q} {noun}",
    ]
    overhead = 4 if use_unicode else 2
    chosen = candidates[-1]
    for cand in candidates:
        if _T.visible_width(cand) + overhead <= max_w:
            chosen = cand
            break
    if not use_unicode:
        plain = f"[{chosen}]"
        if not color_enabled:
            return plain, plain
        fg_q = sgr256(67, bold=True, depth=tier)
        return f"{fg_q}[{chosen}]{_ANSI_RESET}{bdr_color}", plain

    plain = f" {chosen} "
    if not color_enabled:
        return plain, plain
    fg_frame = sgr256(67, depth=tier)
    bg_frame = sgr_bg256(67, depth=tier)
    fg_dark = sgr_dark_fg(depth=tier)
    colored = (
        f"{fg_frame}{bg_frame}{fg_dark} {chosen} {_ANSI_RESET}{fg_frame}{bdr_color}"
    )
    return colored, plain


def render_option2_statusline_lines(
    *,
    now_ts: float,
    run_start_ts: float,
    item_start_ts: float,
    last_act_ts: float,
    current_idx: int,
    total_items: int,
    setid: str,
    id6: str,
    tracker: Any = None,
    stall_remaining: float | None = None,
    progress_source: str | None = None,
    action: str | None = None,
    artifact_kind: str | None = None,
    use_unicode: bool = True,
    activity: str | None = None,
    runner: str = "agy",
    model: str | None = None,
    variant: str | None = None,
    divider_style: str = "chevron",
    stop_level: int | str | None = None,
    items_passed: int | None = None,
    items_failed: int | None = None,
    cwd: str | Path | None = None,
    run_id: str | None = None,
    parked_questions: int | None = None,
    stall_timeout: float | None = None,
    width: int | None = None,
    artifact_title: str | None = None,
    eta_seconds: float | None = None,
    avg_item_seconds: float | None = None,
    avg_step_seconds: float | None = None,
    validation_errors: int = 0,
    retries: int = 0,
    fix_its: int = 0,
    attempt_no: int = 1,
    retry_budget: int = 2,
    step_tokens: int | None = None,
    agy_quota: Optional[_aq.AgyQuotaSnapshot] = None,
    # Injected primitives from render_stream to keep one color/formatting authority:
    tier: str,
    sgr256: Callable[..., str],
    sgr_bg256: Callable[..., str],
    sgr_dark_fg: Callable[..., str],
    format_digital_duration: Callable[[float | int], str],
    format_mmss_duration: Callable[[float | int], str],
    format_progress_source_tag: Callable[[str | None], str],
    format_action_label: Callable[[str | None], str],
    format_artifact_kind_label: Callable[[str | None], str],
    format_activity_cell: Callable[[str | None, Any], tuple[str, int]],
    format_compact_tokens: Callable[[int], str],
    format_cwd_path: Callable[[str | Path | None, int], str],
    make_badge: Callable[..., tuple[str, str]],
    format_stop_badge: Callable[..., tuple[str, str]],
    format_tally_badge: Callable[..., tuple[str, str]],
    pal: Any = None,
) -> tuple[str, ...]:
    """Render the responsive locked-in Option 2 statusline box.

    Returns 5 lines when ``artifact_title`` is empty/None, or 7 lines when
    ``artifact_title`` is provided (adding the full-width description row + divider).
    """
    color_enabled = tier != _T.DEPTH_NONE
    reset = _ANSI_RESET if color_enabled else ""
    bdr_color = sgr256(67, depth=tier) if color_enabled else ""
    div_color = sgr256(60, depth=tier) if color_enabled else ""
    dim_hdr = sgr256(110, depth=tier) if color_enabled else ""
    c_muted = sgr256(244, depth=tier) if color_enabled else ""
    b_clock = sgr256(123, bold=True, depth=tier) if color_enabled else ""
    c_unit = sgr256(117, depth=tier) if color_enabled else ""
    b_blue = sgr256(117, bold=True, depth=tier) if color_enabled else ""
    c_eta = sgr256(159, bold=True, depth=tier) if color_enabled else ""
    c_pace = sgr256(152, depth=tier) if color_enabled else ""
    b_bar = sgr256(78, bold=True, depth=tier) if color_enabled else ""
    c_bar_empty = sgr256(238, depth=tier) if color_enabled else ""
    b_target = sgr256(229, bold=True, depth=tier) if color_enabled else ""
    b_cost = sgr256(114, bold=True, depth=tier) if color_enabled else ""
    b_warn = sgr256(208, bold=True, depth=tier) if color_enabled else ""
    c_retry = sgr256(221, bold=True, depth=tier) if color_enabled else ""
    c_valerr = sgr256(203, bold=True, depth=tier) if color_enabled else ""
    c_pass = sgr256(82, bold=True, depth=tier) if color_enabled else ""
    b_crit = "\033[1;31m" if color_enabled else ""
    c_variant = sgr256(183, bold=True, depth=tier) if color_enabled else ""
    c_data = sgr256(153, depth=tier) if color_enabled else ""

    if use_unicode:
        c_tl, c_tm, c_tr = "╭", "┬", "╮"
        c_bl, c_bm, c_br = "╰", "┴", "╯"
        c_ml, c_mr = "├", "┤"
        c_v, c_h = "│", "─"
        dot_ch = "·"
    else:
        c_tl, c_tm, c_tr = "+", "+", "+"
        c_bl, c_bm, c_br = "+", "+", "+"
        c_ml, c_mr = "+", "+"
        c_v, c_h = "|", "-"
        dot_ch = "-"

    clean_setid = _one_line_clean(setid)
    clean_id6 = _one_line_clean(id6)
    clean_run_id = _one_line_clean(run_id)
    clean_title = _one_line_clean(artifact_title)
    include_desc_row = bool(clean_title)

    has_agy_quota = (
        str(runner or "").strip().lower() in ("agy", "antigravity")
        and agy_quota is not None
    )

    box_w = max(
        MIN_STATUSLINE_WIDTH,
        int(width) if (width is not None and width > 0) else DEFAULT_STATUSLINE_WIDTH,
    )
    inner_w = max(MIN_STATUSLINE_WIDTH - 2, box_w - 2)

    # Check if activity badge requires widening Col 3
    act_str = format_action_label(action)
    art_str = format_artifact_kind_label(artifact_kind)
    activity_cell, activity_w = format_activity_cell(activity, pal)
    col3_min = max(
        10,
        (activity_w + 2) if activity_cell else (_T.visible_width(act_str) + 4),
        _T.visible_width(art_str) + 2,
    )

    if inner_w >= 118:
        col_mins = (
            [17, 23, 28, col3_min, 32] if has_agy_quota else [17, 23, 28, col3_min, 34]
        )
        col_weights = (
            [0.35, 0.55, 1.8, 0.25, 3.0] if has_agy_quota else [0.4, 0.7, 2.5, 0.3, 1.9]
        )
        n_cols = 5
    elif inner_w >= 104:
        col_mins = (
            [17, 23, 26, col3_min, 26] if has_agy_quota else [17, 23, 26, col3_min, 24]
        )
        col_weights = (
            [0.35, 0.55, 1.8, 0.25, 2.8] if has_agy_quota else [0.4, 0.7, 2.4, 0.3, 1.8]
        )
        n_cols = 5
    elif inner_w >= 78:
        col_mins = [15, 19, 22, 20] if has_agy_quota else [16, 20, 24, 15]
        col_weights = [0.35, 0.6, 2.0, 2.2] if has_agy_quota else [0.4, 0.7, 2.8, 1.0]
        n_cols = 4
    else:
        col_mins = [15, 22, 18] if has_agy_quota else [15, 24, 14]
        col_weights = [0.4, 1.8, 1.6] if has_agy_quota else [0.5, 2.5, 0.8]
        n_cols = 3

    cw = _distribute_widths(col_mins, col_weights, inner_w - (n_cols - 1))

    junctions_top: list[tuple[int, str]] = []
    junctions_bot: list[tuple[int, str]] = []
    acc = 0
    for w in cw[:-1]:
        acc += w
        junctions_top.append((acc, c_tm))
        junctions_bot.append((acc, c_bm))
        acc += 1

    # -------------------------------------------------------------------------
    # TOP BORDER: full run_id NEVER truncated before model or CWD pill.
    # -------------------------------------------------------------------------
    if clean_run_id:
        run_p = f" {clean_run_id} "
        run_c = f" {c_muted}{clean_run_id}{bdr_color} " if color_enabled else run_p
    else:
        run_p = ""
        run_c = ""
    run_w = _T.visible_width(run_p)
    side_avail = max(0, inner_w - (run_w + 2 if run_w else 0))

    if model:
        full_id_c, full_id_p = make_badge(
            runner=runner,
            model=model,
            variant=variant,
            divider_style=divider_style,
            use_unicode=use_unicode,
            color=color_enabled,
            depth=tier,
        )
        full_id_p = f"{c_h}{full_id_p}"
        full_id_c = (
            f"{bdr_color}{c_h}{full_id_c}{bdr_color}" if color_enabled else full_id_p
        )
    else:
        full_id_c, full_id_p = "", ""

    def _build_cwd_pill(max_chars: int) -> tuple[str, str]:
        disp = format_cwd_path(cwd, max(4, max_chars))
        if not disp:
            return "", ""
        if use_unicode:
            p = f" {disp} {c_h}"
            if color_enabled:
                fg_f = sgr256(67, depth=tier)
                bg_f = sgr_bg256(67, depth=tier)
                fg_d = sgr_dark_fg(depth=tier)
                c = f"{fg_f}{bg_f}{fg_d} {disp} {reset}{fg_f}{bdr_color}{c_h}"
                return c, p
            return p, p
        p = f"[{disp}]{c_h}"
        if color_enabled:
            fg_f = sgr256(67, depth=tier)
            return f"{fg_f}[{disp}]{bdr_color}{c_h}", p
        return p, p

    full_cwd_c, full_cwd_p = _build_cwd_pill(30)
    full_id_w = _T.visible_width(full_id_p)
    full_cwd_w = _T.visible_width(full_cwd_p)
    ell = "…" if use_unicode else "."

    if full_id_w + full_cwd_w <= side_avail:
        id_c, id_p = full_id_c, full_id_p
        cwd_c, cwd_p = full_cwd_c, full_cwd_p
    else:
        pill_overhead = 5 if use_unicode else 3
        if side_avail < 12:
            id_budget = side_avail
            cwd_budget = 0
        else:
            cwd_budget = min(full_cwd_w, max(9, int(side_avail * 0.42)))
            id_budget = min(full_id_w, side_avail - cwd_budget)
            cwd_budget = min(full_cwd_w, side_avail - id_budget)

        if cwd_budget >= pill_overhead + 4 and full_cwd_w > 0:
            cwd_c, cwd_p = _build_cwd_pill(cwd_budget - pill_overhead)
        else:
            cwd_c, cwd_p = "", ""
            id_budget = min(full_id_w, side_avail)

        if id_budget >= 6 and full_id_w > 0:
            if full_id_w > id_budget:
                id_p = _T.truncate_visible(full_id_p, id_budget, ellipsis=ell)
                id_c = _T.truncate_visible(full_id_c, id_budget, ellipsis=ell)
            else:
                id_c, id_p = full_id_c, full_id_p
        else:
            id_c, id_p = "", ""

    top_c, top_p = _render_border_pair(
        box_w,
        left_ch=c_tl,
        right_ch=c_tr,
        fill_ch=c_h,
        left_c=id_c,
        left_p=id_p,
        center_c=run_c,
        center_p=run_p,
        right_c=cwd_c,
        right_p=cwd_p,
        junctions=() if include_desc_row else junctions_top,
        bdr_color=bdr_color,
        reset=reset,
        use_unicode=use_unicode,
    )

    # -------------------------------------------------------------------------
    # BOTTOM BORDER: tally left, rounded questions pill + stop badge right
    # -------------------------------------------------------------------------
    if items_passed is not None or items_failed is not None:
        tc, tp = format_tally_badge(
            items_passed or 0,
            items_failed or 0,
            use_unicode=use_unicode,
            color=color_enabled,
            depth=tier,
        )
        tally_p = f"{c_h}{tp}"
        tally_c = f"{bdr_color}{c_h}{tc}{bdr_color}" if color_enabled else tally_p
    else:
        tally_c, tally_p = "", ""

    stop_c, stop_p = format_stop_badge(
        stop_level, use_unicode=use_unicode, color=color_enabled, depth=tier
    )
    badge_budget = max(14, inner_w - _T.visible_width(tally_p) - 3)
    q_budget = max(
        10,
        badge_budget - _T.visible_width(stop_p) - (2 if stop_p else 0),
    )
    q_c, q_p = format_questions_pill(
        parked_questions,
        max_w=q_budget,
        use_unicode=use_unicode,
        color_enabled=color_enabled,
        tier=tier,
        sgr256=sgr256,
        sgr_bg256=sgr_bg256,
        sgr_dark_fg=sgr_dark_fg,
        bdr_color=bdr_color,
    )
    if q_p and stop_p:
        bot_r_p = f"{q_p}{c_h}{stop_p}{c_h}"
        bot_r_c = (
            f"{q_c}{bdr_color}{c_h}{stop_c}{bdr_color}{c_h}"
            if color_enabled
            else bot_r_p
        )
    elif stop_p:
        bot_r_p = f"{stop_p}{c_h}"
        bot_r_c = f"{stop_c}{bdr_color}{c_h}" if color_enabled else bot_r_p
    elif q_p:
        bot_r_p = f"{q_p}{c_h}"
        bot_r_c = f"{q_c}{bdr_color}{c_h}" if color_enabled else bot_r_p
    else:
        bot_r_c, bot_r_p = "", ""

    bot_c, bot_p = _render_border_pair(
        box_w,
        left_ch=c_bl,
        right_ch=c_br,
        fill_ch=c_h,
        left_c=tally_c,
        left_p=tally_p,
        right_c=bot_r_c,
        right_p=bot_r_p,
        junctions=junctions_bot,
        bdr_color=bdr_color,
        reset=reset,
        use_unicode=use_unicode,
    )

    # -------------------------------------------------------------------------
    # COL 0: Now / Elapsed / ETA
    # -------------------------------------------------------------------------
    t_str = time.strftime("%H:%M:%S", time.localtime(now_ts))
    run_elapsed = max(0, int(now_ts - run_start_ts))
    run_el_str = format_digital_duration(run_elapsed)

    if cw[0] >= 17:
        lbl_now, lbl_elap, lbl_eta = "Now:    ", "Elapsed:", "ETA:    "
    else:
        lbl_now, lbl_elap, lbl_eta = "Now:  ", "Elap: ", "ETA:  "

    if eta_seconds is not None and eta_seconds > 0:
        eta_dur = f"~{format_compact_duration(eta_seconds)}"
        eta_clk = time.strftime("%H:%M", time.localtime(now_ts + eta_seconds))
        eta_val = (
            f"{eta_dur} @{eta_clk}"
            if cw[0] >= len(lbl_eta) + len(eta_dur) + 8
            else eta_dur
        )
    else:
        eta_val = "--:--"

    c0_r1_p = f"{lbl_now}{t_str} "
    c0_r2_p = f"{lbl_elap}{run_el_str} "
    c0_r3_p = f"{lbl_eta}{eta_val} "
    c0_r1_c = (
        f"{dim_hdr}{lbl_now}{b_clock}{t_str}{reset} " if color_enabled else c0_r1_p
    )
    c0_r2_c = (
        f"{dim_hdr}{lbl_elap}{b_blue}{run_el_str}{reset} " if color_enabled else c0_r2_p
    )
    c0_r3_c = (
        f"{dim_hdr}{lbl_eta}{c_eta}{eta_val}{reset} " if color_enabled else c0_r3_p
    )

    # -------------------------------------------------------------------------
    # PROGRESS + HEALTH COLUMN (index 2 on 5/4 cols, index 1 on 3 cols)
    # -------------------------------------------------------------------------
    p_idx = 2 if n_cols >= 4 else 1
    pw = cw[p_idx]
    act_key = str(action or "execute").strip().lower()
    act_glyph = _ACTION_GLYPHS.get(act_key, "▶") if use_unicode else ""
    act_display = f"{act_glyph}{act_str}" if act_glyph else act_str

    if n_cols == 5:
        if clean_setid and clean_id6:
            hl_p = f" set: {clean_setid}"
            hr_p = f"id6: {clean_id6} "
            hl_c = (
                f" {dim_hdr}set: {b_target}{clean_setid}{reset}"
                if color_enabled
                else hl_p
            )
            hr_c = (
                f"{dim_hdr}id6: {b_target}{clean_id6}{reset} "
                if color_enabled
                else hr_p
            )
            gap = max(1, pw - _T.visible_width(hl_p) - _T.visible_width(hr_p))
            cp_r1_p = hl_p + (" " * gap) + hr_p
            cp_r1_c = hl_c + (" " * gap) + hr_c
        elif clean_setid:
            cp_r1_p = f" set: {clean_setid} "
            cp_r1_c = (
                f" {dim_hdr}set: {b_target}{clean_setid}{reset} "
                if color_enabled
                else cp_r1_p
            )
        elif clean_id6:
            cp_r1_p = f" id6: {clean_id6} "
            cp_r1_c = (
                f" {dim_hdr}id6: {b_target}{clean_id6}{reset} "
                if color_enabled
                else cp_r1_p
            )
        else:
            cp_r1_p = " -"
            cp_r1_c = f" {c_muted}-{reset}" if color_enabled else cp_r1_p
    else:
        hl_p = f" {act_display} {clean_setid}".rstrip()
        hr_p = f"{clean_id6} " if clean_id6 else ""
        hl_c = (
            f" {b_target}{act_display}{reset}"
            + (f" {b_target}{clean_setid}{reset}" if clean_setid else "")
            if color_enabled
            else hl_p
        )
        hr_c = (
            (f"{b_target}{clean_id6}{reset} " if clean_id6 else "")
            if color_enabled
            else hr_p
        )
        gap = (
            max(1, pw - _T.visible_width(hl_p) - _T.visible_width(hr_p)) if hr_p else 0
        )
        cp_r1_p = hl_p + (" " * gap) + hr_p
        cp_r1_c = hl_c + (" " * gap) + hr_c

    pct = int(round((current_idx / total_items) * 100)) if total_items > 0 else 0
    pct_clamped = max(0, min(100, pct))
    pct_str = f"{pct}%"
    pref_p = f" {current_idx}/{total_items}["
    suff_p = f"]{pct_str} "
    bar_w = max(4, pw - _T.visible_width(pref_p) - _T.visible_width(suff_p))
    filled_len = int(round((pct_clamped / 100.0) * bar_w))
    empty_len = max(0, bar_w - filled_len)
    if use_unicode:
        fill_seg = "█" * filled_len
        empty_seg = "░" * empty_len
    else:
        fill_seg = "=" * filled_len
        empty_seg = " " * empty_len
    cp_r2_p = f"{pref_p}{fill_seg}{empty_seg}{suff_p}"
    if color_enabled:
        bar_c = f"{b_bar}{fill_seg}{c_bar_empty}{empty_seg}{reset}"
        cp_r2_c = f" {b_blue}{current_idx}/{total_items}{reset}[{bar_c}]{b_target}{pct_str}{reset} "
    else:
        cp_r2_c = cp_r2_p

    # Row 3 of Progress col: validation errors + retries + fix-its
    if use_unicode:
        val_p = (
            f"☑✗{validation_errors} val-err" if pw >= 34 else f"val✗{validation_errors}"
        )
        ret_p = f"↻{retries} retry" if pw >= 34 else f"↻{retries}"
    else:
        val_p = (
            f"val-err:{validation_errors}" if pw >= 34 else f"valx{validation_errors}"
        )
        ret_p = f"retry:{retries}" if pw >= 34 else f"ret:{retries}"
    fix_p = f"fix:{fix_its}"
    val_col = c_valerr if validation_errors > 0 else c_muted
    ret_col = c_retry if retries > 0 else c_muted
    fix_col = b_warn if fix_its > 0 else c_muted
    val_c = f"{val_col}{val_p}{reset}" if color_enabled else val_p
    ret_c = f"{ret_col}{ret_p}{reset}" if color_enabled else ret_p
    fix_c = f"{fix_col}{fix_p}{reset}" if color_enabled else fix_p
    sep_dot_p = f" {dot_ch} "
    sep_dot_c = f"{c_muted}{sep_dot_p}{reset}" if color_enabled else sep_dot_p
    r3_c_body, r3_p_body = _join_fitting_pairs(
        [(1, val_c, val_p), (1, ret_c, ret_p), (2, fix_c, fix_p)],
        max_w=max(8, pw - 2),
        sep_c=sep_dot_c,
        sep_p=sep_dot_p,
    )
    cp_r3_p = f" {r3_p_body}"
    cp_r3_c = f" {r3_c_body}"

    # -------------------------------------------------------------------------
    # SPEND/TOKENS OR AGY MODEL-FILTERED QUOTA COLUMN (last column)
    # -------------------------------------------------------------------------
    sw = cw[-1]
    cost = tracker.cost if tracker is not None else 0.0
    cost_str = f"${cost:.2f}"
    tot_tok = (
        (tracker.input_tokens + tracker.output_tokens + tracker.cache_tokens)
        if tracker is not None
        else 0
    )
    in_tok = tracker.input_tokens if tracker is not None else 0
    out_tok = tracker.output_tokens if tracker is not None else 0
    cache_tok = tracker.cache_tokens if tracker is not None else 0
    tot_str = format_compact_tokens(tot_tok)
    in_str = format_compact_tokens(in_tok)
    out_str = format_compact_tokens(out_tok)
    cache_str = format_compact_tokens(cache_tok)
    step_tok_str = (
        format_compact_tokens(step_tokens) if step_tokens is not None else None
    )

    if has_agy_quota and agy_quota is not None:
        if sw >= 38:
            cs_r1_p = f" Tok:{tot_str} (in:{in_str} out:{out_str} c:{cache_str})"
            cs_r1_c = (
                f" {dim_hdr}Tok:{c_data}{tot_str}{c_muted} (in:{in_str} out:{out_str} c:{cache_str}){reset}"
                if color_enabled
                else cs_r1_p
            )
        elif sw >= 24:
            st_tail = f" {dot_ch} st:{step_tok_str}" if step_tok_str else ""
            cs_r1_p = f" Tok:{tot_str} ({out_str}o{st_tail})"
            cs_r1_c = (
                f" {dim_hdr}Tok:{c_data}{tot_str}{c_muted} ({out_str}o{st_tail}){reset}"
                if color_enabled
                else cs_r1_p
            )
        else:
            cs_r1_p = f" Tok:{tot_str}"
            cs_r1_c = (
                f" {dim_hdr}Tok:{c_data}{tot_str}{reset}" if color_enabled else cs_r1_p
            )

        (q2_c, q2_p), (q3_c, q3_p) = _format_agy_quota_rows(
            agy_quota,
            model,
            max_w=max(12, sw - 2),
            use_unicode=use_unicode,
            color_enabled=color_enabled,
            tier=tier,
            sgr256=sgr256,
            bdr_color=bdr_color,
            c_hdr=dim_hdr,
            c_clock=b_clock,
            c_unit=c_unit,
            c_burn=b_crit,
            c_muted=c_muted,
            reset=reset,
        )
        cs_r2_p = f" {q2_p}"
        cs_r2_c = f" {q2_c}"
        if q3_p:
            cs_r3_p = f" {q3_p}"
            cs_r3_c = f" {q3_c}"
        else:
            pool_name = {"gemini": "Gemini", "claude": "Opus/3P", "gpt": "GPT/3P"}[
                _aq.model_quota_pool(model)
            ]
            ok_txt = f"{pool_name} quota OK"
            step_tail = (
                f" {dot_ch} step:{step_tok_str} tok"
                if (step_tok_str and sw >= 34)
                else ""
            )
            cs_r3_p = f" {ok_txt}{step_tail}"
            cs_r3_c = (
                f" {c_pass}{ok_txt}{c_muted}{step_tail}{reset}"
                if color_enabled
                else cs_r3_p
            )
    else:
        avg_cost = cost / max(1, current_idx)
        if sw >= 34:
            cs_r1_p = f" {'Spend':<7}{'Tokens':>7}{'In':>6}{'Out':>6}{'Cache':>7}"
            cs_r1_c = f"{dim_hdr}{cs_r1_p}{reset}" if color_enabled else cs_r1_p
            cs_r2_p = f" {cost_str:<7}{tot_str:>7}{in_str:>6}{out_str:>6}{cache_str:>7}"
            cs_r2_c = (
                f" {b_cost}{cost_str:<7}{c_data}{tot_str:>7}{in_str:>6}{out_str:>6}{cache_str:>7}{reset}"
                if color_enabled
                else cs_r2_p
            )
            st_s = f"  step:{step_tok_str} tok" if step_tok_str else ""
            cs_r3_p = f" ${avg_cost:.2f}/item{st_s}"
            cs_r3_c = (
                f" {b_cost}${avg_cost:.2f}/item{c_muted}{st_s}{reset}"
                if color_enabled
                else cs_r3_p
            )
        elif sw >= 22:
            cs_r1_p = " Spend   Tokens"
            cs_r1_c = f"{dim_hdr}{cs_r1_p}{reset}" if color_enabled else cs_r1_p
            cs_r2_p = f" {cost_str:<7} {tot_str} ({out_str}o)"
            cs_r2_c = (
                f" {b_cost}{cost_str:<7} {c_data}{tot_str} ({out_str}o){reset}"
                if color_enabled
                else cs_r2_p
            )
            cs_r3_p = f" ${avg_cost:.2f}/it" + (
                f" {step_tok_str}/st" if step_tok_str else ""
            )
            cs_r3_c = (
                f" {b_cost}${avg_cost:.2f}/it{c_muted}"
                + (f" {step_tok_str}/st" if step_tok_str else "")
                + reset
                if color_enabled
                else cs_r3_p
            )
        else:
            cs_r1_p = " Spend/Tok"
            cs_r1_c = f"{dim_hdr}{cs_r1_p}{reset}" if color_enabled else cs_r1_p
            cs_r2_p = f" {cost_str} {tot_str}"
            cs_r2_c = (
                f" {b_cost}{cost_str} {c_data}{tot_str}{reset}"
                if color_enabled
                else cs_r2_p
            )
            cs_r3_p = f" ${avg_cost:.2f}/it"
            cs_r3_c = (
                f" {c_muted}${avg_cost:.2f}/it{reset}" if color_enabled else cs_r3_p
            )

    # -------------------------------------------------------------------------
    # COL 1 (Timeout / Current / Avg Pace) & COL 3 (Action / Kind / Attempt)
    # -------------------------------------------------------------------------
    rows_c: list[list[tuple[str, str, str]]] = []
    if n_cols >= 4:
        idle = max(0, int(now_ts - last_act_ts))
        idle_str = format_mmss_duration(idle)
        if stall_remaining is not None:
            limit_secs = (
                float(stall_timeout)
                if (stall_timeout is not None and stall_timeout > 0)
                else (idle + float(stall_remaining))
            )
            t_disp = f"{idle_str}/{format_mmss_duration(limit_secs)}"
            t_col = (
                b_crit
                if stall_remaining < 60
                else (b_warn if stall_remaining < 300 else b_clock)
            )
        else:
            t_disp = "--:--"
            t_col = dim_hdr

        step_elapsed = max(0, int(now_ts - item_start_ts))
        step_el_str = format_digital_duration(step_elapsed)
        src_tag = format_progress_source_tag(progress_source)

        lbl_to = "Timeout:" if cw[1] >= 21 else "Idle:"
        lbl_cur = "Current:" if cw[1] >= 21 else "Step:"
        c1_r1_p = f" {lbl_to}{t_disp} "
        c1_r1_c = (
            f" {dim_hdr}{lbl_to}{t_col}{t_disp}{reset} " if color_enabled else c1_r1_p
        )
        c1_r2_p = f" {lbl_cur}{step_el_str} {src_tag}"
        c1_r2_c = (
            f" {dim_hdr}{lbl_cur}{b_blue}{step_el_str}{reset} {c_variant}{src_tag}{reset}"
            if color_enabled
            else c1_r2_p
        )

        avg_it_s = format_compact_duration(avg_item_seconds)
        avg_st_s = format_compact_duration(avg_step_seconds)
        pace_body = f"{avg_it_s}/it {avg_st_s}/st"
        pace_pref = "Avg:" if cw[1] >= len(pace_body) + 6 else ""
        c1_r3_p = f" {pace_pref}{pace_body}"
        c1_r3_c = (
            f" {dim_hdr}{pace_pref}{c_pace}{pace_body}{reset}"
            if color_enabled
            else c1_r3_p
        )

        if n_cols == 5:
            if activity_cell:
                c3_r1_p = _strip_ansi(activity_cell)
                c3_r1_c = activity_cell if color_enabled else c3_r1_p
            else:
                c3_r1_p = act_display
                c3_r1_c = (
                    f"{b_target}{act_display}{reset}" if color_enabled else c3_r1_p
                )
            c3_r2_p = art_str
            c3_r2_c = f"{b_target}{art_str}{reset}" if color_enabled else c3_r2_p
            att_p = f"try {max(1, int(attempt_no))}/{max(1, int(retry_budget) + 1)}"
            att_col = c_retry if attempt_no > 1 else c_muted
            c3_r3_p = att_p
            c3_r3_c = f"{att_col}{att_p}{reset}" if color_enabled else att_p

            rows_c = [
                [
                    (c0_r1_c, c0_r1_p, "left"),
                    (c1_r1_c, c1_r1_p, "left"),
                    (cp_r1_c, cp_r1_p, "left"),
                    (c3_r1_c, c3_r1_p, "center"),
                    (cs_r1_c, cs_r1_p, "left"),
                ],
                [
                    (c0_r2_c, c0_r2_p, "left"),
                    (c1_r2_c, c1_r2_p, "left"),
                    (cp_r2_c, cp_r2_p, "left"),
                    (c3_r2_c, c3_r2_p, "center"),
                    (cs_r2_c, cs_r2_p, "left"),
                ],
                [
                    (c0_r3_c, c0_r3_p, "left"),
                    (c1_r3_c, c1_r3_p, "left"),
                    (cp_r3_c, cp_r3_p, "left"),
                    (c3_r3_c, c3_r3_p, "center"),
                    (cs_r3_c, cs_r3_p, "left"),
                ],
            ]
        else:
            rows_c = [
                [
                    (c0_r1_c, c0_r1_p, "left"),
                    (c1_r1_c, c1_r1_p, "left"),
                    (cp_r1_c, cp_r1_p, "left"),
                    (cs_r1_c, cs_r1_p, "left"),
                ],
                [
                    (c0_r2_c, c0_r2_p, "left"),
                    (c1_r2_c, c1_r2_p, "left"),
                    (cp_r2_c, cp_r2_p, "left"),
                    (cs_r2_c, cs_r2_p, "left"),
                ],
                [
                    (c0_r3_c, c0_r3_p, "left"),
                    (c1_r3_c, c1_r3_p, "left"),
                    (cp_r3_c, cp_r3_p, "left"),
                    (cs_r3_c, cs_r3_p, "left"),
                ],
            ]
    else:
        rows_c = [
            [
                (c0_r1_c, c0_r1_p, "left"),
                (cp_r1_c, cp_r1_p, "left"),
                (cs_r1_c, cs_r1_p, "left"),
            ],
            [
                (c0_r2_c, c0_r2_p, "left"),
                (cp_r2_c, cp_r2_p, "left"),
                (cs_r2_c, cs_r2_p, "left"),
            ],
            [
                (c0_r3_c, c0_r3_p, "left"),
                (cp_r3_c, cp_r3_p, "left"),
                (cs_r3_c, cs_r3_p, "left"),
            ],
        ]

    # -------------------------------------------------------------------------
    # ASSEMBLE FINAL LINES (5 lines without title, 7 lines with Option 2 desc row)
    # -------------------------------------------------------------------------
    out_c: list[str] = [top_c]
    out_p: list[str] = [top_p]

    if include_desc_row:
        desc_plain = (
            f" {_T.truncate_visible(clean_title, max(8, inner_w - 2), ellipsis=ell)}"
        )
        desc_colored = (
            f" {c_data}{desc_plain[1:]}{reset}" if color_enabled else desc_plain
        )
        dp_c, dp_p = _pad_pair(
            desc_colored, desc_plain, inner_w, use_unicode=use_unicode
        )
        out_p.append(f"{c_v}{dp_p}{c_v}")
        out_c.append(
            f"{bdr_color}{c_v}{reset}{dp_c}{bdr_color}{c_v}{reset}"
            if color_enabled
            else f"{c_v}{dp_p}{c_v}"
        )
        mid_c, mid_p = _render_border_pair(
            box_w,
            left_ch=c_ml,
            right_ch=c_mr,
            fill_ch=c_h,
            junctions=junctions_top,
            bdr_color=bdr_color,
            reset=reset,
            use_unicode=use_unicode,
        )
        out_c.append(mid_c)
        out_p.append(mid_p)

    v_sep_c = f"{div_color}{c_v}{reset}" if color_enabled else c_v
    outer_v_c = f"{bdr_color}{c_v}{reset}" if color_enabled else c_v
    for row in rows_c:
        cells_c: list[str] = []
        cells_p: list[str] = []
        for (cc, cp, align), w in zip(row, cw):
            pc, pp = _pad_pair(cc, cp, w, align=align, use_unicode=use_unicode)
            cells_c.append(pc)
            cells_p.append(pp)
        out_p.append(c_v + c_v.join(cells_p) + c_v)
        out_c.append(
            outer_v_c + v_sep_c.join(cells_c) + outer_v_c
            if color_enabled
            else out_p[-1]
        )

    out_c.append(bot_c)
    out_p.append(bot_p)

    return tuple(out_c if color_enabled else out_p)

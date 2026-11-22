"""Behavioral tests for the responsive Option 2 runner statusbar and agy quota widget."""

from __future__ import annotations

import io
import json
import time
from pathlib import Path
from typing import Any

import pytest

from agent_workflows import agy_quota as _aq
from agent_workflows import render_stream as rs
from agent_workflows import statusline_layout as _sl
from agent_workflows import term as _T

pytestmark = pytest.mark.core


class _FakeTTY(io.StringIO):
    def isatty(self) -> bool:
        return True


def _sample_quota(
    *, gem_burn: bool = False, tp_burn: bool = True
) -> _aq.AgyQuotaSnapshot:
    return _aq.AgyQuotaSnapshot(
        gemini_5h=_aq.QuotaBucket(
            remaining_pct=58,
            reset_in_s=7080,
            will_burn_out=gem_burn,
            zero_in_s=2700 if gem_burn else None,
        ),
        gemini_weekly=_aq.QuotaBucket(
            remaining_pct=74,
            reset_in_s=536400,
            will_burn_out=False,
            zero_in_s=None,
        ),
        tp_5h=_aq.QuotaBucket(
            remaining_pct=22,
            reset_in_s=7080,
            will_burn_out=tp_burn,
            zero_in_s=2400 if tp_burn else None,
        ),
        tp_weekly=_aq.QuotaBucket(
            remaining_pct=65,
            reset_in_s=536400,
            will_burn_out=False,
            zero_in_s=None,
        ),
    )


def test_responsive_widths_rectangular_and_run_id_never_truncated() -> None:
    """Across widths 64..200, box stays rectangular, styled matches plain, and full run_id stays intact."""
    run_id = "run-20261121T194011Z-882104"
    tracker = rs.StreamTracker()
    tracker.update(inp=1400000, out=197000, cache=27700000, cost=8.42)
    quota = _sample_quota(gem_burn=True)

    for width in (64, 76, 92, 108, 124, 140, 172, 200):
        for use_unicode in (True, False):
            common: dict[str, Any] = dict(
                now_ts=1700000000.0,
                run_start_ts=1700000000.0 - 2520.0,
                item_start_ts=1700000000.0 - 300.0,
                last_act_ts=1700000000.0 - 12.0,
                current_idx=4,
                total_items=7,
                setid="statv2",
                id6="cntxsm",
                tracker=tracker,
                stall_remaining=1400.0,
                stall_timeout=1800.0,
                progress_source="stdout",
                action="review",
                artifact_kind="ipd",
                use_unicode=use_unicode,
                runner="agy",
                model="gemini-3-pro",
                variant="high",
                items_passed=3,
                items_failed=1,
                cwd="~/repos/example-repo/.aw/worktrees/statusbar-v2",
                run_id=run_id,
                parked_questions=1,
                width=width,
                artifact_title="Ship responsive Option 2 runner statusbar with agy quota and burnout alerts",
                eta_seconds=2160.0,
                avg_item_seconds=720.0,
                avg_step_seconds=265.0,
                validation_errors=2,
                retries=3,
                fix_its=1,
                attempt_no=2,
                retry_budget=2,
                step_tokens=2100000,
                agy_quota=quota,
            )
            plain_lines = rs.format_statusline_lines(
                **common, pal=rs.Palette(False, use_unicode=use_unicode)
            )
            styled_lines = rs.format_statusline_lines(
                **common, pal=rs.Palette(True, use_unicode=use_unicode)
            )

            assert len(plain_lines) == 7
            assert len(styled_lines) == 7
            assert [_T.visible_width(line) for line in plain_lines] == [width] * 7
            assert [_T.visible_width(line) for line in styled_lines] == [width] * 7
            assert tuple(rs._strip_ansi(line) for line in styled_lines) == plain_lines

            # Full run_id is NEVER truncated at any supported width
            assert f" {run_id} " in plain_lines[0]

            if not use_unicode:
                for line in styled_lines:
                    assert not [c for c in line if ord(c) >= 128]


def test_option2_title_row_and_divider_and_resolution(tmp_path: Path) -> None:
    """Option 2 renders 7 lines with truncated title + divider when title is present, 5 lines when omitted."""
    plan = tmp_path / "20261121-statv2-01-cntxsm-statusbar.ipd.md"
    plan.write_text(
        "# IPD: Implement responsive Option 2 statusbar\n\nBody text.\n",
        encoding="utf-8",
    )

    assert (
        _sl.resolve_artifact_title({"file": str(plan)})
        == "Implement responsive Option 2 statusbar"
    )
    assert (
        _sl.resolve_artifact_title({"title": "Explicit Title", "file": str(plan)})
        == "Explicit Title"
    )
    assert _sl.resolve_artifact_title({"slug": "fix-tab-glyphs"}) == "Fix tab glyphs"

    lines_with = rs.format_statusline_lines(
        now_ts=1700000000.0,
        run_start_ts=1699999000.0,
        item_start_ts=1699999900.0,
        last_act_ts=1699999990.0,
        current_idx=1,
        total_items=3,
        setid="statv2",
        id6="cntxsm",
        pal=rs.Palette(False, use_unicode=True),
        width=90,
        artifact_title="A" * 120,
    )
    assert len(lines_with) == 7
    assert lines_with[1].startswith("│ A")
    assert "…" in lines_with[1]
    assert lines_with[2].startswith("├") and lines_with[2].endswith("┤")
    assert "┬" in lines_with[2]
    assert "┬" not in lines_with[0]

    lines_without = rs.format_statusline_lines(
        now_ts=1700000000.0,
        run_start_ts=1699999000.0,
        item_start_ts=1699999900.0,
        last_act_ts=1699999990.0,
        current_idx=1,
        total_items=3,
        setid="statv2",
        id6="cntxsm",
        pal=rs.Palette(False, use_unicode=True),
        width=90,
        artifact_title=None,
    )
    assert len(lines_without) == 5
    assert "┬" in lines_without[0]


def test_setid_and_id6_have_identical_styling_and_review_glyph() -> None:
    """set: <setid> and id6: <id6> share identical label and value SGR styling, and review uses 🆁."""
    lines = rs.format_statusline_lines(
        now_ts=1700000000.0,
        run_start_ts=1699999000.0,
        item_start_ts=1699999900.0,
        last_act_ts=1699999990.0,
        current_idx=2,
        total_items=5,
        setid="iosmvn",
        id6="cntxsm",
        action="review",
        artifact_kind="ipd",
        pal=rs.Palette(True, use_unicode=True),
        width=140,
    )
    row1 = lines[1]
    assert "\033[38;5;110mset: \033[1;38;5;229miosmvn\033[0m" in row1
    assert "\033[38;5;110mid6: \033[1;38;5;229mcntxsm\033[0m" in row1
    assert "🆁Review" in rs._strip_ansi(row1)


def test_questions_pill_matches_cwd_pill_style_without_run_id() -> None:
    """Bottom-right questions pill uses slate bg 67 like CWD pill and omits run_id."""
    run_id = "run-20261121T194011Z-882104"
    lines = rs.format_statusline_lines(
        now_ts=1700000000.0,
        run_start_ts=1699999000.0,
        item_start_ts=1699999900.0,
        last_act_ts=1699999990.0,
        current_idx=1,
        total_items=2,
        setid="iosmvn",
        id6="cntxsm",
        cwd="~/repos/example-repo",
        run_id=run_id,
        parked_questions=1,
        stop_level=1,
        pal=rs.Palette(True, use_unicode=True),
        width=140,
    )
    top_c, bot_c = lines[0], lines[-1]
    assert "\033[48;5;67m" in top_c
    assert "\033[48;5;67m" in bot_c
    bot_p = rs._strip_ansi(bot_c)
    assert " ? 1 question · aw runs answer " in bot_p
    assert run_id not in bot_p
    assert run_id in rs._strip_ansi(top_c)
    assert " ⏹ STOP: finish current " in bot_p


def test_agy_quota_model_filtering_burnout_and_narrow_stacking() -> None:
    """agy quota displays only the active model's pool, flags burnout with bold-red !!, and stacks when narrow."""
    quota = _sample_quota(gem_burn=False, tp_burn=True)

    # 1. Gemini model -> Gemini pool (58% / 74%), no burnout
    gem_lines = rs.format_statusline_lines(
        now_ts=1700000000.0,
        run_start_ts=1699999000.0,
        item_start_ts=1699999900.0,
        last_act_ts=1699999990.0,
        current_idx=2,
        total_items=5,
        setid="iosmvn",
        id6="cntxsm",
        runner="agy",
        model="gemini-3-pro",
        pal=rs.Palette(True, use_unicode=True),
        width=144,
        agy_quota=quota,
    )
    gem_plain = "\n".join(rs._strip_ansi(line) for line in gem_lines)
    assert "Gem:" in gem_plain
    assert "58%" in gem_plain and "74%" in gem_plain
    assert "22%" not in gem_plain
    assert "Gemini quota OK" in gem_plain
    assert "!!" not in gem_plain

    # 2. Claude Opus model -> 3P pool (22%!! / 65%) with bold-red !! burnout alert
    opus_lines = rs.format_statusline_lines(
        now_ts=1700000000.0,
        run_start_ts=1699999000.0,
        item_start_ts=1699999900.0,
        last_act_ts=1699999990.0,
        current_idx=2,
        total_items=5,
        setid="iosmvn",
        id6="cntxsm",
        runner="agy",
        model="claude-opus-4-6",
        pal=rs.Palette(True, use_unicode=True),
        width=144,
        agy_quota=quota,
    )
    opus_plain = "\n".join(rs._strip_ansi(line) for line in opus_lines)
    assert "Opus:" in opus_plain
    assert "22%!!" in opus_plain and "65%" in opus_plain
    assert "58%" not in opus_plain
    assert "!! 5h out ~40m00s" in opus_plain
    assert "(1h18m short)" in opus_plain
    assert "\033[1;31m!!" in opus_lines[2]

    # 3. GPT model -> 3P pool labeled GPT:
    gpt_lines = rs.format_statusline_lines(
        now_ts=1700000000.0,
        run_start_ts=1699999000.0,
        item_start_ts=1699999900.0,
        last_act_ts=1699999990.0,
        current_idx=2,
        total_items=5,
        setid="iosmvn",
        id6="cntxsm",
        runner="agy",
        model="gpt-5.3-codex",
        pal=rs.Palette(False, use_unicode=True),
        width=144,
        agy_quota=quota,
    )
    assert "GPT:" in "\n".join(gpt_lines)

    # 4. Narrow width stacks 5h on Row 2 and wk on Row 3
    narrow_lines = rs.format_statusline_lines(
        now_ts=1700000000.0,
        run_start_ts=1699999000.0,
        item_start_ts=1699999900.0,
        last_act_ts=1699999990.0,
        current_idx=2,
        total_items=5,
        setid="iosmvn",
        id6="cntxsm",
        runner="agy",
        model="claude-opus-4-6",
        pal=rs.Palette(False, use_unicode=True),
        width=76,
        agy_quota=quota,
    )
    assert "5h " in narrow_lines[2]
    assert "wk " in narrow_lines[3]
    assert [_T.visible_width(line) for line in narrow_lines] == [76] * 5


def test_weekly_burnout_formats_days_and_time_left_on_table() -> None:
    """Multi-day burnout ETAs render with days+hours and show how far short of reset quota runs out."""
    # Weekly reset in 5d14h (482400s); burns out in 79h39m (286740s = 3d7h39m) -> 2d6h short (195660s).
    quota = _aq.AgyQuotaSnapshot(
        gemini_5h=_aq.QuotaBucket(
            reset_in_s=6900,
            remaining_pct=90,
            will_burn_out=False,
            zero_in_s=None,
        ),
        gemini_weekly=_aq.QuotaBucket(
            reset_in_s=5 * 86400 + 14 * 3600,
            remaining_pct=63,
            will_burn_out=True,
            zero_in_s=79 * 3600 + 39 * 60,
        ),
        tp_5h=None,
        tp_weekly=None,
    )
    lines = rs.format_statusline_lines(
        now_ts=1700000000.0,
        run_start_ts=1699999000.0,
        item_start_ts=1699999900.0,
        last_act_ts=1699999990.0,
        current_idx=1,
        total_items=10,
        setid="bugs-audit",
        id6="2nm0pq",
        runner="agy",
        model="gemini-4-neon",
        pal=rs.Palette(False, use_unicode=True),
        width=150,
        agy_quota=quota,
    )
    plain = "\n".join(lines)
    assert "!! wk out ~3d7h (2d6h short)" in plain
    assert "79h" not in plain
    assert [_T.visible_width(line) for line in lines] == [150] * 5

    # When both 5h and weekly burn out simultaneously, compact fallback keeps both inside the column width.
    both_burn = _aq.AgyQuotaSnapshot(
        gemini_5h=_aq.QuotaBucket(
            reset_in_s=6900,
            remaining_pct=20,
            will_burn_out=True,
            zero_in_s=2400,
        ),
        gemini_weekly=_aq.QuotaBucket(
            reset_in_s=5 * 86400 + 14 * 3600,
            remaining_pct=40,
            will_burn_out=True,
            zero_in_s=3 * 86400 + 7 * 3600,
        ),
        tp_5h=None,
        tp_weekly=None,
    )
    both_lines = rs.format_statusline_lines(
        now_ts=1700000000.0,
        run_start_ts=1699999000.0,
        item_start_ts=1699999900.0,
        last_act_ts=1699999990.0,
        current_idx=1,
        total_items=10,
        setid="bugs-audit",
        id6="2nm0pq",
        runner="agy",
        model="gemini-4-neon",
        pal=rs.Palette(False, use_unicode=True),
        width=150,
        agy_quota=both_burn,
    )
    both_plain = "\n".join(both_lines)
    assert "!! 5h out ~40m00s" in both_plain
    assert "!! wk out ~3d7h" in both_plain
    assert [_T.visible_width(line) for line in both_lines] == [150] * 5


def test_agy_quota_file_loader_and_burnout_forecast(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """load_agy_quota_snapshot reads real agy-quota local cache + history and computes burnout accurately."""
    import datetime as dt

    now = time.time()
    cache_file = tmp_path / "antigravity_quota.json"
    hist_file = tmp_path / "quota_history.json"

    def _iso(ts: float) -> str:
        return (
            dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

    cache_payload = {
        "quota_updated_at": now - 5,
        "quota": {
            "gemini-5h": {
                "remaining_fraction": 0.80,
                "reset_time": _iso(now + 7200),
            },
            "gemini-weekly": {
                "remaining_fraction": 0.90,
                "reset_time": _iso(now + 400000),
            },
            "3p-5h": {
                "remaining_fraction": 0.25,
                "reset_time": _iso(now + 10800),
            },
            "3p-weekly": {
                "remaining_fraction": 0.70,
                "reset_time": _iso(now + 400000),
            },
        },
    }
    # Steep burn on 3p-5h: 75% -> 50% -> 25% over 40 minutes -> zeros in ~20 min (< 3h reset)
    # Mild burn on gemini-5h: 82% -> 81% -> 80% over 40 minutes -> will NOT burn out before 2h reset
    hist_payload = {
        "samples": [
            {
                "ts": now - 2400,
                "buckets": {
                    "gemini-5h": {"remaining_fraction": 0.82},
                    "3p-5h": {"remaining_fraction": 0.75},
                },
            },
            {
                "ts": now - 1200,
                "buckets": {
                    "gemini-5h": {"remaining_fraction": 0.81},
                    "3p-5h": {"remaining_fraction": 0.50},
                },
            },
            {
                "ts": now - 10,
                "buckets": {
                    "gemini-5h": {"remaining_fraction": 0.80},
                    "3p-5h": {"remaining_fraction": 0.25},
                },
            },
        ]
    }
    cache_file.write_text(json.dumps(cache_payload), encoding="utf-8")
    hist_file.write_text(json.dumps(hist_payload), encoding="utf-8")

    monkeypatch.setenv("AGY_QUOTA_FILE", str(cache_file))
    _aq.clear_quota_cache()
    snap = _aq.load_agy_quota_snapshot(
        now_ts=now, history_path=hist_file, ttl_seconds=0
    )
    assert snap is not None
    assert snap.gemini_5h is not None
    assert snap.gemini_5h.remaining_pct == 80
    assert snap.gemini_5h.will_burn_out is False
    assert snap.tp_5h is not None
    assert snap.tp_5h.remaining_pct == 25
    assert snap.tp_5h.will_burn_out is True
    assert snap.tp_5h.zero_in_s is not None and snap.tp_5h.zero_in_s < 10800

    # Fail-open on corrupt file
    cache_file.write_text("{not valid json", encoding="utf-8")
    _aq.clear_quota_cache()
    assert (
        _aq.load_agy_quota_snapshot(
            cache_paths=(cache_file,), history_path=hist_file, ttl_seconds=0
        )
        is None
    )


def test_compute_queue_telemetry_from_state() -> None:
    """compute_queue_telemetry derives ETA, avg/it, avg/st, val-err, retries, fix-its, and attempt_no."""
    cur_item = {
        "id6": "item03",
        "action": "execute",
        "status": "running",
        "attempts": [
            {
                "started_at": "2026-11-21T19:00:00Z",
                "ended_at": "2026-11-21T19:05:00Z",
                "disposition": "fail-verify",
                "suite_check": {"passing": False},
                "correction_turns": 1,
            },
            {
                "started_at": "2026-11-21T19:06:00Z",
            },
        ],
    }
    state = {
        "options": {"retry_budget": 3},
        "queue": [
            {
                "id6": "item01",
                "action": "execute",
                "status": "executed",
                "attempts": [
                    {
                        "started_at": "2026-11-21T18:30:00Z",
                        "ended_at": "2026-11-21T18:40:00Z",
                    }
                ],
            },
            {
                "id6": "item02",
                "action": "execute",
                "status": "executed",
                "attempts": [
                    {
                        "started_at": "2026-11-21T18:40:00Z",
                        "ended_at": "2026-11-21T18:50:00Z",
                    },
                    {
                        "started_at": "2026-11-21T18:50:00Z",
                        "ended_at": "2026-11-21T18:55:00Z",
                        "hook_refusal_sendback": ["pre-commit"],
                    },
                ],
            },
            cur_item,
            {"id6": "item04", "action": "execute", "status": "queued", "attempts": []},
        ],
    }
    tel = _sl.compute_queue_telemetry(state, current_item=cur_item)
    # Completed items: item01=600s, item02=900s -> avg_item=750s; remaining=2 -> ETA=1500s
    assert tel["avg_item_seconds"] == pytest.approx(750.0)
    assert tel["eta_seconds"] == pytest.approx(1500.0)
    # Completed attempts: 600, 600, 300, 300 -> avg_step=450s
    assert tel["avg_step_seconds"] == pytest.approx(450.0)
    assert tel["validation_errors"] == 2  # suite_check False + fail-verify
    assert tel["fix_its"] == 2  # 1 correction_turn + 1 hook_refusal_sendback
    assert tel["retries"] == 4  # 2 extra attempts + 2 fix-its
    assert tel["attempt_no"] == 2
    assert tel["retry_budget"] == 3


def test_statusline_dynamic_height_tty_redraw_clear_and_write_event() -> None:
    """Statusline tracks dynamic box height (7 lines with title, 5 without) in cursor-up escapes."""
    tty = _FakeTTY()
    sl = rs.Statusline(
        rs.Palette(False, use_unicode=True),
        tty,
        setid="statv2",
        id6="cntxsm",
        artifact_title="Ship responsive Option 2 statusbar",
        width=120,
    )
    # First draw: 7 lines
    sl.redraw()
    assert sl._drawn_lines == 7
    assert "\033[6A" not in tty.getvalue()

    # Second draw: moves up 6 lines
    pos = len(tty.getvalue())
    sl.redraw()
    assert "\033[6A" in tty.getvalue()[pos:]

    # write_event wipes 7 lines (6A), writes event, redraws 7 lines
    pos = len(tty.getvalue())
    sl.write_event("event-above-7line-box")
    delta = tty.getvalue()[pos:]
    assert "\033[6A" in delta
    assert "event-above-7line-box\n" in delta
    assert sl._drawn_lines == 7

    # Shrink to 5 lines (clearing title): moves up 6, writes 5, clears 2 extra lines, backs up 2
    sl.artifact_title = None
    pos = len(tty.getvalue())
    sl.redraw()
    delta = tty.getvalue()[pos:]
    assert "\033[6A" in delta
    assert "\033[2A" in delta
    assert sl._drawn_lines == 5

    # Clear now uses 4A (for 5 lines)
    pos = len(tty.getvalue())
    sl.clear()
    assert "\033[4A" in tty.getvalue()[pos:]
    assert sl._drawn_lines == 0
    assert not sl._has_drawn

"""Behavioral tests for the statusline renderer and refresh class (IPD 6tjq2j).

Covers the box renderer invariants, hostile inputs, scalar/label formatters,
activity/action logic, and the Statusline lifecycle without pinning layout bytes.
"""

from __future__ import annotations

import io
import itertools
import threading
import time
from typing import Any

import pytest

from agent_workflows import render_stream as rs
from agent_workflows import term as _T


class TestStatuslineBoxInvariants:
    """E-01: Box renderer invariants across swept inputs."""

    def test_box_renderer_invariants_across_swept_inputs(self) -> None:
        """Assert four properties across the swept input space:
        (a) exactly 4 lines returned, joined into 4 newline-delimited lines;
        (b) every line has the SAME visible width (single distinct visible width);
        (c) _strip_ansi(styled) == plain line for line (0 mismatches);
        (d) two renders with identical arguments are byte-identical.
        """
        # Fixed timestamps: never assert the clock, as it is timezone-dependent.
        now_ts = 1700000000.0
        run_start_ts = 1699990000.0
        item_start_ts = 1699999000.0
        last_act_ts = 1699999900.0

        # Swept dimensions: kept strictly free of zero-width and newline characters (PR-302, F-10).
        setids = [
            "",
            "statuscov",
            "very-long-setid-alpha-beta",
        ]  # 3: absent, present, long
        id6s = ["", "6tjq2j"]  # 2: absent, present
        actions = ["execute", "customact", None]  # 3: mapped, unmapped, absent
        artifact_kinds = ["ipd", "customart", None]  # 3: mapped, unmapped, absent
        stall_remainings = [None, 0.0, 500.0]  # 3: absent, zero, large
        progress_sources = ["stdout", None]  # 2: present, absent
        activities = [
            None,
            "verifying",
            "reading a file",
        ]  # 3: absent, real stage, free text
        progress_pairs = [(0, 0), (0, 5), (3, 5), (5, 5)]  # 4: 0/0, 0/N, mid, N/N

        populated_tracker = rs.StreamTracker()
        populated_tracker.update(inp=119000, out=110700, cache=4500000, cost=6.16)
        trackers = [None, populated_tracker]  # 2: absent, populated

        # 3 * 2 * 3 * 3 * 3 * 2 * 3 * 4 * 2 = 7,776 distinct input combinations.
        combos = list(
            itertools.product(
                setids,
                id6s,
                actions,
                artifact_kinds,
                stall_remainings,
                progress_sources,
                activities,
                progress_pairs,
                trackers,
            )
        )
        assert len(combos) == 7776

        render_count = 0
        pal_plain = rs.Palette(False)
        pal_styled = rs.Palette(True)

        for (
            setid,
            id6,
            action,
            art_kind,
            stall,
            prog_src,
            activity,
            (cur_idx, tot_items),
            tracker,
        ) in combos:
            for use_unicode in (True, False):
                # 1. Unstyled render
                plain_lines = rs.format_statusline_lines(
                    now_ts=now_ts,
                    run_start_ts=run_start_ts,
                    item_start_ts=item_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_plain,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                plain_str = rs.format_statusline(
                    now_ts=now_ts,
                    start_ts=run_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_plain,
                    item_start_ts=item_start_ts,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                render_count += 1

                # (a) exactly 4 lines returned, joined into 4 newline-delimited lines
                assert len(plain_lines) == 4
                assert plain_str == "\n".join(plain_lines)

                # (b) every line has the same visible width (single distinct value)
                plain_widths = [_T.visible_width(line) for line in plain_lines]
                assert len(set(plain_widths)) == 1

                # (d) repeat render is byte-identical
                plain_repeat = rs.format_statusline_lines(
                    now_ts=now_ts,
                    run_start_ts=run_start_ts,
                    item_start_ts=item_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_plain,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                assert plain_repeat == plain_lines

                # 2. Styled render
                styled_lines = rs.format_statusline_lines(
                    now_ts=now_ts,
                    run_start_ts=run_start_ts,
                    item_start_ts=item_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_styled,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                styled_str = rs.format_statusline(
                    now_ts=now_ts,
                    start_ts=run_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_styled,
                    item_start_ts=item_start_ts,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                render_count += 1

                # (a) exactly 4 lines returned, joined into 4 newline-delimited lines
                assert len(styled_lines) == 4
                assert styled_str == "\n".join(styled_lines)

                # (b) every line has the same visible width (single distinct value)
                styled_widths = [_T.visible_width(line) for line in styled_lines]
                assert len(set(styled_widths)) == 1

                # (c) _strip_ansi(styled) == plain line for line
                stripped = tuple(rs._strip_ansi(line) for line in styled_lines)
                assert stripped == plain_lines

                # (d) repeat render is byte-identical
                styled_repeat = rs.format_statusline_lines(
                    now_ts=now_ts,
                    run_start_ts=run_start_ts,
                    item_start_ts=item_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_styled,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                assert styled_repeat == styled_lines

        # Confirm exact render count: 7,776 combinations * 2 styling * 2 unicode = 31,104 renders.
        assert render_count == 31104


class TestStatuslineHostileInputs:
    """E-02: Hostile-input coverage for the box renderer."""

    @pytest.mark.parametrize(
        "desc,kwargs",
        [
            ("total_items_zero", {"current_idx": 0, "total_items": 0}),
            ("current_idx_greater_than_total", {"current_idx": 10, "total_items": 5}),
            ("negative_current_idx", {"current_idx": -1, "total_items": 5}),
            ("long_setid_200_chars", {"setid": "s" * 200}),
            (
                "empty_free_text_fields",
                {
                    "action": "",
                    "artifact_kind": "",
                    "activity": "",
                    "progress_source": "",
                },
            ),
            (
                "zero_now_ts",
                {
                    "now_ts": 0.0,
                    "run_start_ts": 0.0,
                    "item_start_ts": 0.0,
                    "last_act_ts": 0.0,
                },
            ),
            ("negative_stall_remaining", {"stall_remaining": -10.0}),
            ("tracker_none", {"tracker": None}),
            (
                "clock_skew_now_earlier_than_start",
                {
                    "now_ts": 100.0,
                    "run_start_ts": 200.0,
                    "item_start_ts": 150.0,
                    "last_act_ts": 120.0,
                },
            ),
        ],
    )
    def test_hostile_inputs_return_well_formed_rectangular_box(
        self, desc: str, kwargs: dict[str, Any]
    ) -> None:
        """Each hostile input must neither raise nor malform the box: asserts 4-tuple and single visible width."""
        base_args: dict[str, Any] = {
            "now_ts": 1700000000.0,
            "run_start_ts": 1699990000.0,
            "item_start_ts": 1699999000.0,
            "last_act_ts": 1699999900.0,
            "current_idx": 1,
            "total_items": 5,
            "setid": "hostile",
            "id6": "6tjq2j",
            "tracker": None,
            "pal": rs.Palette(False),
            "stall_remaining": 60.0,
            "progress_source": "stdout",
            "action": "execute",
            "artifact_kind": "ipd",
            "use_unicode": True,
            "activity": "verifying",
        }
        base_args.update(kwargs)

        lines = rs.format_statusline_lines(**base_args)
        assert len(lines) == 4, f"Failed 4-line count for {desc}"
        widths = [_T.visible_width(line) for line in lines]
        assert (
            len(set(widths)) == 1
        ), f"Failed rectangularity for {desc}: widths={widths}"

    def test_zero_width_space_setid_characterization(self) -> None:
        """Characterization only: zero-width code point neither raises nor corrupts tuple length (PR-301, F-10).

        Note: rectangularity is NOT asserted here because visible_width('\\u200b') is 0 while
        format_statusline_lines measures that column with len() today; approved plan it6tpj owns the fix.
        """
        lines = rs.format_statusline_lines(
            now_ts=1700000000.0,
            run_start_ts=1699990000.0,
            item_start_ts=1699999000.0,
            last_act_ts=1699999900.0,
            current_idx=1,
            total_items=5,
            setid="a\u200bb",
            id6="6tjq2j",
            pal=rs.Palette(False),
        )
        assert len(lines) == 4

    def test_newline_in_setid_characterization(self) -> None:
        """Characterization only: newline in setid returns a 4-tuple and does not raise (F-05).

        Note: physical line count is not asserted as 4 because literal newlines split the joined box.
        """
        lines = rs.format_statusline_lines(
            now_ts=1700000000.0,
            run_start_ts=1699990000.0,
            item_start_ts=1699999000.0,
            last_act_ts=1699999900.0,
            current_idx=1,
            total_items=5,
            setid="line1\nline2",
            id6="6tjq2j",
            pal=rs.Palette(False),
        )
        assert len(lines) == 4


class TestStatuslineFormatters:
    """E-03: Scalar and label formatters as input/output tables."""

    @pytest.mark.parametrize(
        "n,expected_compact,expected_tokens",
        [
            (0, "0", "0"),
            (1, "1", "1"),
            (999, "999", "999"),
            (1000, "1k", "1.00K"),
            # OQ-01 characterization: rounds to 1000.0 and strips to 1000k / 1000m
            (999999, "1000k", "1000.00K"),
            (1000000, "1m", "1.00M"),
            (999999999, "1000m", "1000.00M"),
            (1000000000, "1g", "1.00G"),
            (5000000000, "5g", "5.00G"),
        ],
    )
    def test_token_magnitude_boundaries(
        self, n: float, expected_compact: str, expected_tokens: str
    ) -> None:
        """Cover token formatting across magnitude thresholds and characterization cases."""
        assert rs.format_compact_tokens(n) == expected_compact
        assert rs.format_tokens(n) == expected_tokens

    @pytest.mark.parametrize(
        "seconds,expected_compact,expected_duration",
        [
            (None, "0m00s", "0s"),
            (-10, "0m00s", "0s"),
            (0, "0m00s", "0s"),
            (59, "0m59s", "59s"),
            (60, "1m00s", "1m 00s"),
            (3599, "59m59s", "59m 59s"),
            (3600, "1h00m00s", "1h 00m 00s"),
            (86400, "1d 0h00m00s", "1d 0h 00m 00s"),
        ],
    )
    def test_duration_boundaries(
        self, seconds: float | None, expected_compact: str, expected_duration: str
    ) -> None:
        """Cover duration formatting across time unit boundaries and clamp cases."""
        assert rs.format_compact_duration(seconds) == expected_compact
        assert rs.format_duration(seconds) == expected_duration

    def test_stall_countdown_behaviors(self) -> None:
        """Cover format_stall_countdown's four documented behaviors."""
        # 1. None returns empty string
        assert rs.format_stall_countdown(None) == ""
        assert rs.format_stall_countdown(None, "stdout") == ""

        # 2. Sub-minute renders seconds only
        assert rs.format_stall_countdown(45.0) == "kill in 45s"
        assert rs.format_stall_countdown(0.0) == "kill in 0s"

        # 3. Minute-or-more renders XmYYs
        assert rs.format_stall_countdown(60.0) == "kill in 1m00s"
        assert rs.format_stall_countdown(90.0) == "kill in 1m30s"
        assert rs.format_stall_countdown(591.0) == "kill in 9m51s"

        # 4. progress_source appends suffix
        assert (
            rs.format_stall_countdown(90.0, "stdout") == "kill in 1m30s (last: stdout)"
        )
        assert (
            rs.format_stall_countdown(45.0, "subagent")
            == "kill in 45s (last: subagent)"
        )

    def test_label_formatters_derived_from_maps(self) -> None:
        """Derive label formatter cases from the display maps, covering aliases and defaults."""
        # ACTION_DISPLAY_MAP derivation
        for key, expected in rs.ACTION_DISPLAY_MAP.items():
            assert rs.format_action_label(key) == expected
            assert rs.format_action_label(key.upper()) == expected
            assert rs.format_action_label(f"  {key}  ") == expected

        # ARTIFACT_DISPLAY_MAP derivation
        for key, expected in rs.ARTIFACT_DISPLAY_MAP.items():
            assert rs.format_artifact_kind_label(key) == expected
            assert rs.format_artifact_kind_label(key.upper()) == expected
            assert rs.format_artifact_kind_label(f"  {key}  ") == expected

        # Alias pairs per map
        assert (
            rs.format_action_label("execute")
            == rs.format_action_label("exec")
            == "Execute"
        )
        assert (
            rs.format_action_label("graduate")
            == rs.format_action_label("graduat")
            == "Graduat"
        )
        assert (
            rs.format_action_label("validate")
            == rs.format_action_label("validat")
            == "Validat"
        )
        assert (
            rs.format_action_label("orchestrate")
            == rs.format_action_label("orchest")
            == "Orchest"
        )

        assert (
            rs.format_artifact_kind_label("ipd")
            == rs.format_artifact_kind_label("plan")
            == "IPD"
        )
        assert (
            rs.format_artifact_kind_label("walkthrough")
            == rs.format_artifact_kind_label("walkthr")
            == "Walkthr"
        )

        # PR-304: format_action_label('plan') is NOT in ACTION_DISPLAY_MAP; returns fallback 'Plan'
        assert rs.format_action_label("plan") == "Plan"

        # None / empty defaults
        assert rs.format_action_label(None) == "Review"
        assert rs.format_action_label("") == "Review"
        assert rs.format_artifact_kind_label(None) == "IPD"
        assert rs.format_artifact_kind_label("") == "IPD"

    def test_label_fallback_visible_width_truncation(self) -> None:
        """Fallback truncation must be bounded in visible columns (<= 7) rather than code points."""
        for unmapped in [
            "customlongaction",
            "unmappedartifact",
            "abcdefghijk",
            "verylongname",
        ]:
            action_label = rs.format_action_label(unmapped)
            art_label = rs.format_artifact_kind_label(unmapped)
            assert _T.visible_width(action_label) <= 7
            assert _T.visible_width(art_label) <= 7
            assert action_label[0].isupper()
            assert art_label[0].isupper()


class TestStatuslineActivityAndActionDerivation:
    """E-04: format_activity_cell and statusline_action_for_item."""

    def test_activity_cell_closed_vocabulary_and_visible_width(self) -> None:
        """Cover closed vocabulary, positive width, visible width with variation selector, and styled agreement."""
        pal_plain = rs.Palette(False)
        pal_styled = rs.Palette(True)

        # 1. Free text returns ("", 0)
        for free_text in [
            "reading a file",
            "running pytest",
            "custom_task",
            "unknown_token",
        ]:
            assert rs.format_activity_cell(free_text, pal_plain) == ("", 0)
            assert rs.format_activity_cell(free_text, pal_styled) == ("", 0)
        assert rs.format_activity_cell(None, pal_plain) == ("", 0)
        assert rs.format_activity_cell("", pal_plain) == ("", 0)

        # 2. Real stage returns non-empty cell with positive width
        text, width = rs.format_activity_cell("abandoned", pal_plain)
        assert text != ""
        assert width > 0

        # 3. Visible-width measurement using variation-selector stage: 'recovering' glyph is U+21A9 + U+FE0E
        rec_text, rec_width = rs.format_activity_cell("recovering", pal_plain)
        assert rec_width > 0
        assert rec_width < len(rec_text)

        # 4. Styled cell agrees with plain width
        for stage in [
            "verifying",
            "executing",
            "recovering",
            "abandoned",
            "integrating",
        ]:
            p_text, p_width = rs.format_activity_cell(stage, pal_plain)
            s_text, s_width = rs.format_activity_cell(stage, pal_styled)
            assert s_width == p_width
            assert s_width == _T.visible_width(p_text)
            assert rs._strip_ansi(s_text) == p_text

    def test_statusline_action_for_item_table_and_precedence(self) -> None:
        """Cover all five action derivation shapes and verify that explicit action takes precedence."""
        # 1. Explicit action wins
        assert rs.statusline_action_for_item({"action": "execute"}) == "execute"
        assert rs.statusline_action_for_item({"action": "review"}) == "review"
        assert rs.statusline_action_for_item({"action": "orchestrate"}) == "orchestrate"

        # Precedence: explicit action wins over contradicting initial_status and status
        assert (
            rs.statusline_action_for_item(
                {
                    "action": "orchestrate",
                    "initial_status": "to-review",
                    "status": "draft",
                }
            )
            == "orchestrate"
        )
        assert (
            rs.statusline_action_for_item(
                {"action": "execute", "initial_status": "to-review"}
            )
            == "execute"
        )
        assert (
            rs.statusline_action_for_item(
                {"action": "review", "initial_status": "approved"}
            )
            == "review"
        )

        # 2. Absent action, initial_status in ('to-review', 'draft') -> review
        assert (
            rs.statusline_action_for_item({"initial_status": "to-review"}) == "review"
        )
        assert rs.statusline_action_for_item({"initial_status": "draft"}) == "review"

        # 3. Absent action, other initial_status -> execute
        assert (
            rs.statusline_action_for_item({"initial_status": "approved"}) == "execute"
        )
        assert (
            rs.statusline_action_for_item({"initial_status": "executed"}) == "execute"
        )

        # 4. Absent action and initial_status, status in ('to-review', 'draft') -> review
        assert rs.statusline_action_for_item({"status": "to-review"}) == "review"
        assert rs.statusline_action_for_item({"status": "draft"}) == "review"

        # 5. Absent action and initial_status, other status or empty item -> execute
        assert rs.statusline_action_for_item({"status": "running"}) == "execute"
        assert rs.statusline_action_for_item({}) == "execute"


class FakeTTY(io.StringIO):
    """StringIO subclass simulating a TTY stream for interactive statusline tests."""

    def isatty(self) -> bool:
        return True


class TestStatuslineClass:
    """E-05: Statusline class lifecycle, stream contracts, and merge semantics."""

    def test_non_tty_contract(self) -> None:
        """Non-TTY stream: redraw() writes nothing, write_event() writes plain event text without escapes."""
        stream = io.StringIO()
        sl = rs.Statusline(rs.Palette(False), stream)
        sl.redraw()
        assert stream.getvalue() == ""

        sl.write_event("sample non-tty event")
        assert stream.getvalue() == "sample non-tty event\n"
        assert "\033" not in stream.getvalue()

    def test_tty_stickiness_and_structural_escapes(self) -> None:
        """TTY stream: first redraw has no cursor-up, second has cursor-up, pause clears, resume draws."""
        stream = FakeTTY()
        sl = rs.Statusline(rs.Palette(False), stream)

        # First redraw has no cursor-up sequence
        sl.redraw()
        first_output = stream.getvalue()
        assert "\033[3A" not in first_output
        assert len(first_output) > 0
        assert sl._has_drawn

        # Second redraw emits cursor-up to stick to position
        sl.redraw()
        second_output = stream.getvalue()
        delta_redraw = second_output[len(first_output) :]
        assert "\033[3A" in delta_redraw

        # write_event writes event text and redraws around it
        pos = len(stream.getvalue())
        sl.write_event("my-test-event")
        event_output = stream.getvalue()[pos:]
        assert "my-test-event\n" in event_output

        # pause clears the active statusline
        pos = len(stream.getvalue())
        sl.pause()
        pause_output = stream.getvalue()[pos:]
        assert "\033[3A\r\033[K" in pause_output
        assert not sl._has_drawn
        assert sl._paused

        # resume unpauses and redraws
        pos = len(stream.getvalue())
        sl.resume()
        resume_output = stream.getvalue()[pos:]
        assert len(resume_output) > 0
        assert sl._has_drawn
        assert not sl._paused

    def test_update_item_merge_semantics(self) -> None:
        """Empty string preserves setid/id6; None preserves action/artifact_kind/activity; non-empty/non-None replaces."""
        stream = io.StringIO()
        sl = rs.Statusline(
            rs.Palette(False),
            stream,
            setid="set1",
            id6="id6a",
            action="act1",
            artifact_kind="art1",
            activity="verifying",
        )

        # Empty strings preserve setid and id6
        sl.update_item(1, 10, setid="", id6="")
        assert sl.setid == "set1"
        assert sl.id6 == "id6a"

        # Non-empty strings replace setid and id6
        sl.update_item(2, 10, setid="set2", id6="id6b")
        assert sl.setid == "set2"
        assert sl.id6 == "id6b"

        # None preserves action, artifact_kind, activity
        sl.update_item(3, 10, action=None, artifact_kind=None, activity=None)
        assert sl.action == "act1"
        assert sl.artifact_kind == "art1"
        assert sl.activity == "verifying"

        # Non-None replaces action, artifact_kind, activity
        sl.update_item(
            4, 10, action="execute", artifact_kind="spec", activity="executing"
        )
        assert sl.action == "execute"
        assert sl.artifact_kind == "spec"
        assert sl.activity == "executing"

    def test_duck_typed_watchdog_contract(self) -> None:
        """Watchdog contract: None returns None, working remaining() returns float, raising remaining() returns None."""
        # 1. No watchdog
        sl_none = rs.Statusline(rs.Palette(False), io.StringIO(), watchdog=None)
        assert sl_none.stall_remaining() is None

        # 2. Working watchdog
        class GoodWatchdog:
            def remaining(self) -> float:
                return 42.0

        sl_good = rs.Statusline(
            rs.Palette(False), io.StringIO(), watchdog=GoodWatchdog()
        )
        assert sl_good.stall_remaining() == 42.0

        # 3. Raising watchdog does not propagate
        class RaisingWatchdog:
            def remaining(self) -> float:
                raise RuntimeError("watchdog failed")

        sl_raising = rs.Statusline(
            rs.Palette(False), io.StringIO(), watchdog=RaisingWatchdog()
        )
        assert sl_raising.stall_remaining() is None

    def test_context_manager_thread_lifecycle_and_active_registration(self) -> None:
        """Context manager starts thread on TTY, registers in _ACTIVE_STATUSLINE, and cleans up completely."""
        stream = FakeTTY()
        sl = rs.Statusline(rs.Palette(False), stream, interval=0.02)
        assert rs._ACTIVE_STATUSLINE is None

        with sl as active:
            assert active is sl
            assert rs._ACTIVE_STATUSLINE is sl
            assert sl._thread is not None
            assert sl._thread.is_alive()
            time.sleep(0.06)
            assert len(stream.getvalue()) > 0

        assert rs._ACTIVE_STATUSLINE is None
        assert sl._thread is not None
        assert not sl._thread.is_alive()

    def test_cross_thread_pause_resume_reentrancy_bounded_join(self) -> None:
        """Pause and resume called from another thread while active complete without deadlock under bounded join."""
        stream = FakeTTY()
        sl = rs.Statusline(rs.Palette(False), stream, interval=0.02)

        with sl:

            def worker() -> None:
                sl.pause()
                sl.resume()

            t = threading.Thread(target=worker)
            t.start()
            t.join(timeout=2.0)
            assert not t.is_alive(), "Cross-thread pause/resume reentrancy deadlocked"

    def test_module_level_pause_and_resume_active_statusline(self) -> None:
        """pause_active_statusline / resume_active_statusline operate on active instance and no-op when inactive."""
        # Inactive case: no-op, no exception
        assert rs._ACTIVE_STATUSLINE is None
        rs.pause_active_statusline()
        rs.resume_active_statusline()

        # Active case
        stream = FakeTTY()
        sl = rs.Statusline(rs.Palette(False), stream, interval=0.02)
        with sl:
            assert not sl._paused
            rs.pause_active_statusline()
            assert sl._paused
            rs.resume_active_statusline()
            assert not sl._paused

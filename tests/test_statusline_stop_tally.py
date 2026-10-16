"""Behavioral and rendering tests for statusline stop badge, tally badge, cursor hiding, and final statusline output."""

from __future__ import annotations

import io
from typing import Any

import pytest

from agent_workflows import render_stream as rs
from agent_workflows import term as _T


class _TtyStringIO(io.StringIO):
    """StringIO subclass that reports isatty() is True."""

    def isatty(self) -> bool:
        return True


class TestBadgeFormatters:
    def test_format_stop_badge_levels_unicode(self) -> None:
        """Assert stop badge generates correct text across all levels in Unicode mode."""
        # Level 1: after-call
        col, plain = rs.format_stop_badge(1, use_unicode=True, color=False)
        assert plain == " ⏹ STOP: finish current "

        # Level 2: after-set
        col, plain = rs.format_stop_badge(2, use_unicode=True, color=False)
        assert plain == " ⏹ STOP-SET: finish set "

        # Level 3: now
        col, plain = rs.format_stop_badge(3, use_unicode=True, color=False)
        assert plain == " ⏹ STOP NOW: checkpoint "

        # Level 4: now-force
        col, plain = rs.format_stop_badge(4, use_unicode=True, color=False)
        assert plain == " ⏹ FORCE STOP: force stop "

        # String names
        col, plain = rs.format_stop_badge("after-call", use_unicode=True, color=False)
        assert plain == " ⏹ STOP: finish current "
        col, plain = rs.format_stop_badge("after-set", use_unicode=True, color=False)
        assert plain == " ⏹ STOP-SET: finish set "

        # Inactive / None / 0
        assert rs.format_stop_badge(None) == ("", "")
        assert rs.format_stop_badge(0) == ("", "")
        assert rs.format_stop_badge("") == ("", "")
        assert rs.format_stop_badge("none") == ("", "")

    def test_format_stop_badge_levels_ascii(self) -> None:
        """Assert stop badge generates pure ASCII text in ASCII mode."""
        for lvl, expected in [
            (1, "[STOP: finish current]"),
            (2, "[STOP-SET: finish set]"),
            (3, "[STOP NOW: checkpoint]"),
            (4, "[FORCE STOP: force stop]"),
        ]:
            col, plain = rs.format_stop_badge(lvl, use_unicode=False, color=False)
            assert plain == expected
            assert all(ord(c) < 128 for c in plain)

    def test_format_tally_badge_unicode(self) -> None:
        """Assert tally badge produces [✓ X ok · ✗ Y fail] in Unicode mode."""
        col, plain = rs.format_tally_badge(3, 1, use_unicode=True, color=False)
        assert plain == "[✓ 3 ok · ✗ 1 fail]"

        col, plain = rs.format_tally_badge(0, 0, use_unicode=True, color=False)
        assert plain == "[✓ 0 ok · ✗ 0 fail]"

    def test_format_tally_badge_ascii(self) -> None:
        """Assert tally badge produces pure ASCII [X ok, Y fail] in ASCII mode."""
        col, plain = rs.format_tally_badge(3, 1, use_unicode=False, color=False)
        assert plain == "[3 ok, 1 fail]"
        assert all(ord(c) < 128 for c in plain)


class TestComputeQueueTally:
    def test_compute_queue_tally(self) -> None:
        """Assert queue tally computation correctly counts completed successes and failures."""
        assert rs.compute_queue_tally(None) == (0, 0)
        assert rs.compute_queue_tally([]) == (0, 0)

        queue = [
            {"id6": "aaa111", "status": "executed", "action": "execute"},
            {"id6": "bbb222", "status": "reviewed", "action": "review"},
            {"id6": "ccc333", "status": "failed", "action": "execute"},
            {"id6": "ddd444", "status": "queued", "action": "execute"},
            {"id6": "eee555", "status": "driver-error", "action": "execute"},
            {"id6": "fff666", "status": "not-run", "action": "execute"},
        ]
        passed, failed = rs.compute_queue_tally(queue)
        assert passed == 2
        assert failed == 2

    def test_in_flight_provisional_fail_is_not_counted(self) -> None:
        """An item still between its turn and integration holds a provisional fail-gate; not a fail."""
        queue = [
            {"id6": "aaa111", "status": "executed", "action": "execute"},
            {"id6": "bbb222", "status": "fail-gate", "action": "execute"},
            {"id6": "ccc333", "status": "queued", "action": "execute"},
        ]
        assert rs.compute_queue_tally(queue, in_flight_id6="bbb222") == (1, 0)
        # Once the driver moves on, a genuine failure of that item is counted.
        assert rs.compute_queue_tally(queue, in_flight_id6="ccc333") == (1, 1)
        # A success of the in-flight item counts immediately.
        queue[1]["status"] = "executed"
        assert rs.compute_queue_tally(queue, in_flight_id6="bbb222") == (2, 0)

    def test_statusline_badge_ignores_in_flight_provisional_fail(self) -> None:
        """The rendered live statusline shows 0 fail while the current item is provisionally fail-gate."""
        import io

        state = {
            "queue": [
                {"id6": "aaa111", "status": "executed", "action": "execute"},
                {"id6": "bbb222", "status": "fail-gate", "action": "execute"},
            ]
        }
        sl = rs.Statusline(
            pal=rs.Palette(False, use_unicode=True),
            stream=io.StringIO(),
            interval=0.0,
            current_idx=2,
            total_items=2,
            setid="s",
            id6="bbb222",
            state=state,
        )
        text = "\n".join(sl._render_lines_unlocked())
        assert "1 ok" in text and "0 fail" in text, text


class TestStatuslineStopTallyRendering:
    @pytest.mark.parametrize("stop_level", [None, 1, 2, 3, 4])
    @pytest.mark.parametrize("tally", [None, (0, 0), (3, 1)])
    @pytest.mark.parametrize("styled", [False, True])
    @pytest.mark.parametrize("use_unicode", [True, False])
    def test_statusline_rectangular_with_badges(
        self,
        stop_level: int | None,
        tally: tuple[int, int] | None,
        styled: bool,
        use_unicode: bool,
    ) -> None:
        """Assert that statusline box is strictly rectangular across badge combinations."""
        pal = rs.Palette(styled, use_unicode=use_unicode)
        p_arg = tally[0] if tally is not None else None
        f_arg = tally[1] if tally is not None else None

        lines = rs.format_statusline_lines(
            now_ts=1700000000.0,
            run_start_ts=1700000000.0 - 3600.0,
            item_start_ts=1700000000.0 - 60.0,
            last_act_ts=1700000000.0 - 10.0,
            current_idx=8,
            total_items=17,
            setid="cvtg9u",
            id6="lv0dvv",
            runner="opencode",
            model="uri/its_direct/pt3-claude-opus-5.5-1m-us",
            variant="high",
            pal=pal,
            use_unicode=use_unicode,
            stop_level=stop_level,
            items_passed=p_arg,
            items_failed=f_arg,
        )

        assert len(lines) == 4
        widths = {_T.visible_width(line) for line in lines}
        assert len(widths) == 1, (
            f"Non-rectangular lines for stop={stop_level}, tally={tally}, "
            f"styled={styled}, unicode={use_unicode}: {widths}\n"
            + "\n".join(repr(line) for line in lines)
        )

        if not use_unicode:
            for i, line in enumerate(lines):
                non_ascii = [c for c in line if ord(c) >= 128]
                assert not non_ascii, f"Line {i} contains non-ASCII: {non_ascii}"

    def test_badge_content_in_bottom_border(self) -> None:
        """Assert Option 6 bottom border contains tally and stop badges."""
        pal = rs.Palette(False, use_unicode=True)
        lines = rs.format_statusline_lines(
            now_ts=1700000000.0,
            run_start_ts=1700000000.0 - 3600.0,
            item_start_ts=1700000000.0 - 60.0,
            last_act_ts=1700000000.0 - 10.0,
            current_idx=8,
            total_items=17,
            setid="cvtg9u",
            id6="lv0dvv",
            runner="opencode",
            model="uri/its_direct/pt3-claude-opus-5.5-1m-us",
            variant="high",
            pal=pal,
            use_unicode=True,
            stop_level=1,
            items_passed=3,
            items_failed=1,
        )
        bot = lines[3]
        assert "[✓ 3 ok · ✗ 1 fail]" in bot
        assert " ⏹ STOP: finish current " in bot


class TestCursorControl:
    def test_cursor_hide_and_show_lifecycle(self) -> None:
        """Assert terminal cursor hide and show sequences during Statusline lifecycle."""
        stream = _TtyStringIO()
        pal = rs.Palette(False, use_unicode=True)
        statusline = rs.Statusline(
            pal=pal,
            stream=stream,
            interval=0.0,
            current_idx=1,
            total_items=1,
            setid="testset",
            id6="abc123",
        )

        with statusline:
            assert rs._CURSOR_HIDE in stream.getvalue()
            # Clear output buffer to inspect subsequent calls
            stream.seek(0)
            stream.truncate(0)

            statusline.pause()
            assert rs._CURSOR_SHOW in stream.getvalue()

            stream.seek(0)
            stream.truncate(0)

            statusline.resume()
            assert rs._CURSOR_HIDE in stream.getvalue()

            stream.seek(0)
            stream.truncate(0)

        # On exit, cursor must be shown
        assert rs._CURSOR_SHOW in stream.getvalue()


class TestPrintFinalStatusline:
    def test_print_final_statusline_output_and_idempotency(self) -> None:
        """Assert print_final_statusline prints 4-line boxed statusline and is idempotent."""
        stream = _TtyStringIO()
        pal = rs.Palette(False, use_unicode=True)
        state: dict[str, Any] = {
            "queue": [
                {"id6": "tst001", "status": "executed", "action": "execute"},
                {"id6": "tst002", "status": "failed", "action": "execute"},
            ],
            "options": {"model": "test-model", "variant": "test-variant"},
            "setid": "finalset",
        }

        rs.print_final_statusline(
            state,
            run_dir=None,
            pal=pal,
            runner="opencode",
            stream=stream,
        )

        output = stream.getvalue()
        assert state.get("_final_statusline_printed") is True
        assert "[✓ 1 ok · ✗ 1 fail]" in output
        assert rs._CURSOR_SHOW in output

        # Calling again must be idempotent (no duplicate print)
        stream.seek(0)
        stream.truncate(0)
        rs.print_final_statusline(
            state,
            run_dir=None,
            pal=pal,
            runner="opencode",
            stream=stream,
        )
        assert stream.getvalue() == ""

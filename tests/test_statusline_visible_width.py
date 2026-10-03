"""Tests for statusline visible width and grapheme integrity.

Validates that the 4-line statusline box rendered by format_statusline_lines
is strictly rectangular in visible terminal columns across all reachable cell
paths, styling modes, and unicode modes, and that fallback label truncators
do not sever multi-codepoint graphemes (spec uonrjg Section 9.4).
"""

from __future__ import annotations

import random
from typing import Any

import pytest

from agent_workflows import lifecycle_style as _LS
from agent_workflows import render_stream
from agent_workflows import term as _T


class _FakeTracker:
    def __init__(
        self,
        cost: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_tokens: int = 0,
    ) -> None:
        self.cost = cost
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_tokens = cache_tokens


_BASE_KWARGS: dict[str, Any] = {
    "now_ts": 1700000000.0,
    "run_start_ts": 1700000000.0 - 1000.0,
    "item_start_ts": 1700000000.0 - 500.0,
    "last_act_ts": 1700000000.0 - 10.0,
    "current_idx": 1,
    "total_items": 1,
    "tracker": None,
}

_CELL_CASES = [
    ("setid_vs", {"setid": "s\u26a0\ufe0e1", "id6": "6knsrx"}),
    ("id6_nfd", {"setid": "wtisoland", "id6": "cafe\u0301"}),
    ("setid_only", {"setid": "s\u26a0\ufe0e1", "id6": ""}),
    ("id6_only", {"setid": "", "id6": "cafe\u0301"}),
    ("neither", {"setid": "", "id6": ""}),
    (
        "countdown_source_vs",
        {
            "setid": "s\u26a0\ufe0e1",
            "id6": "6knsrx",
            "stall_remaining": 120.0,
            "progress_source": "stdout",
        },
    ),
    (
        "activity_abandoned",
        {"setid": "s\u26a0\ufe0e1", "id6": "6knsrx", "activity": "abandoned"},
    ),
    (
        "activity_recovering_ascii",
        {"setid": "wtisoland", "id6": "6knsrx", "activity": "recovering"},
    ),
]


@pytest.mark.parametrize("case_name,case_kwargs", _CELL_CASES)
@pytest.mark.parametrize("styled", [False, True])
@pytest.mark.parametrize("use_unicode", [True, False])
def test_statusline_box_is_rectangular(
    case_name: str,
    case_kwargs: dict[str, Any],
    styled: bool,
    use_unicode: bool,
) -> None:
    """The 4-line statusline box must have exactly one visible width across all lines."""
    pal = render_stream.Palette(styled, use_unicode=use_unicode)
    kwargs = {**_BASE_KWARGS, **case_kwargs, "pal": pal, "use_unicode": use_unicode}
    lines = render_stream.format_statusline_lines(**kwargs)
    assert len(lines) == 4

    widths = {_T.visible_width(line) for line in lines}
    assert len(widths) == 1, (
        f"Statusline lines for {case_name} (styled={styled}, unicode={use_unicode}) "
        f"have inconsistent visible widths: {widths}. Lines:\n"
        + "\n".join(repr(line_str) for line_str in lines)
    )


def test_activity_case_is_live() -> None:
    """Verify that activity cases use tokens from ALL_STAGES and activate the activity branch."""
    pal = render_stream.Palette(False)
    for act in ("abandoned", "recovering", "active"):
        assert act in _LS.ALL_STAGES, f"Activity {act!r} must be in ALL_STAGES"
        _cell, w = render_stream.format_activity_cell(act, pal)
        assert w > 0, f"Expected non-zero visible width for stage {act!r}, got {w}"

    # Verify that activity presence alters the box width compared to no activity
    no_act_kwargs = {
        **_BASE_KWARGS,
        "setid": "s\u26a0\ufe0e1",
        "id6": "6knsrx",
        "pal": pal,
    }
    act_kwargs = {**no_act_kwargs, "activity": "abandoned"}

    no_act_lines = render_stream.format_statusline_lines(**no_act_kwargs)
    act_lines = render_stream.format_statusline_lines(**act_kwargs)

    no_act_w = _T.visible_width(no_act_lines[0])
    act_w = _T.visible_width(act_lines[0])
    assert (
        act_w != no_act_w
    ), f"Activity box width ({act_w}) should differ from no-activity box width ({no_act_w})"


def test_ascii_input_byte_identity_invariant() -> None:
    """For unstyled ASCII-only input, every line must satisfy visible_width(line) == len(line)."""
    rng = random.Random(42)
    setids = ["", "wtisoland", "short", "longsetid12345"]
    id6s = ["", "6knsrx", "abc"]
    actions = ["review", "execute", "orchestrate", "customact", None]
    kinds = ["ipd", "spec", "prompt", "customkind", None]
    activities = [None, "active", "executing", "recovering", "abandoned"]
    stalls = [None, 0.0, 45.0, 120.0]
    sources = [None, "stdout", "stderr"]
    unicodes = [True, False]

    for _ in range(200):
        s_id = rng.choice(setids)
        i6 = rng.choice(id6s)
        act = rng.choice(actions)
        knd = rng.choice(kinds)
        stall = rng.choice(stalls)
        src_p = rng.choice(sources)
        u = rng.choice(unicodes)
        if u:
            activity = None
        else:
            activity = rng.choice(activities)
        cost_val = rng.choice([0.0, 1.25, 45.67, 1000.50])
        in_t = rng.randint(0, 5000000)
        out_t = rng.randint(0, 5000000)
        cache_t = rng.randint(0, 5000000)

        tr = _FakeTracker(
            cost=cost_val,
            input_tokens=in_t,
            output_tokens=out_t,
            cache_tokens=cache_t,
        )

        kw = {
            "now_ts": 1700000000.0 + rng.randint(0, 10000),
            "run_start_ts": 1700000000.0,
            "item_start_ts": 1700000000.0 + 50,
            "last_act_ts": 1700000000.0 + 90,
            "current_idx": rng.randint(1, 10),
            "total_items": 10,
            "setid": s_id,
            "id6": i6,
            "tracker": tr,
            "stall_remaining": stall,
            "progress_source": src_p,
            "action": act,
            "artifact_kind": knd,
            "use_unicode": u,
            "activity": activity,
        }

        # Unstyled ASCII invariant check
        pal = render_stream.Palette(False, use_unicode=u)
        lines = render_stream.format_statusline_lines(**kw, pal=pal)
        for line in lines:
            # Box-drawing characters in ASCII mode (| and - and +) have visible_width == len == 1.
            # In unicode mode, box-drawing characters also have visible_width == 1,
            # but unicodedata.east_asian_width is 'A' (Ambiguous), while len() in UTF-8 code points is 1.
            # Thus visible_width(line) == len(line) holds for both in term.visible_width.
            assert (
                _T.visible_width(line) == len(line)
            ), f"Visible width ({_T.visible_width(line)}) != len ({len(line)}) for line:\n{line!r}"


def test_label_truncation_preserves_graphemes() -> None:
    """Truncation in format_action_label and format_artifact_kind_label must not sever variation selectors."""
    for glyph in _LS.MULTI_CODEPOINT_GLYPHS:
        base_char = glyph[0]
        # Position the multi-codepoint glyph right at the 7-char truncation boundary
        test_input = f"abcdef{glyph}gh"

        act_label = render_stream.format_action_label(test_input)
        art_label = render_stream.format_artifact_kind_label(test_input)

        for label, fn_name in [
            (act_label, "format_action_label"),
            (art_label, "format_artifact_kind_label"),
        ]:
            if base_char in label:
                assert glyph in label, (
                    f"{fn_name} severed variation selector from base character {base_char!r}: "
                    f"got {label!r} from input {test_input!r}"
                )
            assert _T.visible_width(label) <= 7, (
                f"{fn_name} produced label exceeding 7 visible columns: {label!r} "
                f"(width {_T.visible_width(label)})"
            )

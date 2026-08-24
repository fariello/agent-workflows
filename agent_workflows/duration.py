"""Duration and age parsing utilities for archiving and lifecycle management."""

from __future__ import annotations

import re
from typing import Union

_DURATION_RE = re.compile(r"^(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>[hdwmyHDWMY]?)$")

UNIT_TO_DAYS = {
    "h": 1.0 / 24.0,
    "d": 1.0,
    "": 1.0,
    "w": 7.0,
    "m": 30.0,
    "y": 365.0,
}


def parse_age_duration(
    val: Union[str, int, float, None], default_days: float = 14.0
) -> float:
    """Parse an age duration string or numeric value into days (as a float).

    Supported units:
      - 'h': hours (e.g. '1h', '12h') -> 1/24 days
      - 'd': days (e.g. '5d', '14d') -> days
      - 'w': weeks (e.g. '2w', '10w') -> 7 * days
      - 'm': months (e.g. '1m', '4m') -> 30 * days
      - 'y': years (e.g. '1y') -> 365 * days
      - plain integer/float (e.g. '14', 14) -> days

    Raises:
        ValueError: if the input string cannot be parsed as a valid duration or is negative.
    """
    if val is None:
        return float(default_days)

    if isinstance(val, (int, float)):
        if val < 0:
            raise ValueError(f"age duration cannot be negative: {val}")
        return float(val)

    s = str(val).strip()
    if not s:
        return float(default_days)

    m = _DURATION_RE.match(s)
    if not m:
        raise ValueError(
            f"invalid age duration '{val}': expected format like 1h, 5d, 10w, 4m, 1y (or plain integer/float)"
        )

    num = float(m.group("num"))
    unit = m.group("unit").lower()
    mult = UNIT_TO_DAYS.get(unit, 1.0)
    return num * mult

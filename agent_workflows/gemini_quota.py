"""CLI tool to display Gemini and third-party quota/credit status from Antigravity (AGY)."""

from __future__ import annotations

import argparse
import contextlib
import datetime
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"

_INITIAL_HOME = Path.home()
_INITIAL_DEFAULT_CACHE_PATHS: tuple[Path, ...] = (
    _INITIAL_HOME / ".gemini" / "antigravity-cli" / "last_quota.json",
)
_INITIAL_HISTORY_PATH = (
    _INITIAL_HOME / ".gemini" / "antigravity-cli" / "quota_history.json"
)

DEFAULT_CACHE_PATHS: tuple[Path, ...] = _INITIAL_DEFAULT_CACHE_PATHS
HISTORY_PATH: Path = _INITIAL_HISTORY_PATH
MAX_HISTORY_AGE_SECS = 6 * 3600
MAX_HISTORY_SAMPLES = 720
FIVE_HOUR_SECS = 5 * 3600
WEEKLY_SECS = 7 * 86_400

_ANSI_RE = re.compile(r"\033\[[0-9;]*[a-zA-Z]")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")

BRAILLE_DOTS = (
    (0x01, 0x08),
    (0x02, 0x10),
    (0x04, 0x20),
    (0x40, 0x80),
)

ANTIGRAVITY_API_HOSTS: tuple[str, ...] = (
    "daily-cloudcode-pa.googleapis.com",
    "cloudcode-pa.googleapis.com",
)
ANTIGRAVITY_USER_AGENT = (
    "antigravity/hub/2.24.0 (aidev_client; os_type=darwin; arch=arm64; cl=1000335682)"
)
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
TOKEN_EXPIRED_MESSAGE = "token expired; run agy to renew it"


def _resolve_default_cache_paths() -> tuple[Path, ...]:
    """Return default cache paths, honoring both Path.home() changes and module overrides."""
    if DEFAULT_CACHE_PATHS != _INITIAL_DEFAULT_CACHE_PATHS:
        return DEFAULT_CACHE_PATHS
    return (Path.home() / ".gemini" / "antigravity-cli" / "last_quota.json",)


def _resolve_history_path() -> Path:
    """Return history path, honoring both Path.home() changes and module overrides."""
    if HISTORY_PATH != _INITIAL_HISTORY_PATH:
        return HISTORY_PATH
    return Path.home() / ".gemini" / "antigravity-cli" / "quota_history.json"


def _resolve_token_paths() -> tuple[Path, Path]:
    """Return primary and fallback OAuth token file paths under the active home directory."""
    home = Path.home()
    return (
        home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token",
        home / ".config" / "opencode" / "antigravity-accounts.json",
    )


def sanitize_text(value: Any) -> str:
    """Strip ANSI escape sequences and control characters from untrusted payload strings."""
    if value is None:
        return ""
    text = str(value)
    text = _ANSI_RE.sub("", text)
    text = _CONTROL_RE.sub(" ", text)
    return " ".join(text.split())


def _validate_https_url(url: str) -> str:
    """Validate that url uses https:// with a non-empty host before performing HTTP I/O."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"Refusing non-HTTPS URL: {url!r}")
    return url


def supports_color(no_color_flag: bool = False, force_color_flag: bool = False) -> bool:
    """Return whether terminal output should include ANSI colors."""
    if no_color_flag:
        return False
    if force_color_flag:
        return True
    force_env = os.environ.get("FORCE_COLOR", "").strip().lower()
    if force_env in ("1", "true", "yes"):
        return True
    if os.environ.get("NO_COLOR", "") != "":
        return False
    if os.environ.get("TERM", "").strip().lower() == "dumb":
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    return bool(sys.stdout.isatty())


def format_duration(seconds: int) -> str:
    """Convert seconds into a compact duration string like '4h28m' or '2d7h'."""
    seconds = max(0, int(seconds))
    days, remainder = divmod(seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes = remainder // 60

    if days > 0:
        return f"{days}d{hours}h"
    if hours > 0:
        return f"{hours}h{minutes}m"
    return f"{minutes}m"


def format_relative_time(past_seconds: float) -> str:
    """Format elapsed seconds into 'Xs ago' or 'Xm ago'."""
    sec = max(0, int(past_seconds))
    if sec < 60:
        return f"{sec}s ago"
    minutes = sec // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    return f"{hours}h ago"


def quota_color_256(percentage: int) -> str:
    """Return a 256-color ANSI SGR sequence for a 0..100 remaining quota percentage.

    - 100%: VERY GREEN (bold bright pure green, 46)
    - 50% < pct < 100%: greenish, progressively less green as pct decreases (40 -> 76 -> 112 -> 148)
    - 25% < pct <= 50%: yellowish (184 -> 226 -> 220)
    - 0% <= pct <= 25%: reddish all the way to VERY RED (202 -> 160 -> 196 -> bold 196)
    """
    if percentage >= 100:
        return "\033[1;38;5;46m"
    if percentage > 50:
        if percentage >= 88:
            return "\033[38;5;40m"
        if percentage >= 75:
            return "\033[38;5;76m"
        if percentage >= 63:
            return "\033[38;5;112m"
        return "\033[38;5;148m"
    if percentage > 25:
        if percentage >= 43:
            return "\033[38;5;184m"
        if percentage >= 34:
            return "\033[38;5;226m"
        return "\033[38;5;220m"
    if percentage >= 18:
        return "\033[38;5;202m"
    if percentage >= 10:
        return "\033[38;5;160m"
    if percentage >= 4:
        return "\033[38;5;196m"
    return "\033[1;38;5;196m"


def remain_at_reset_color_256(percentage: int) -> str:
    """Return a 256-color ANSI SGR sequence for 'Remain at reset' percentages.

    - 25%..100%: green (46 -> 40 -> 76)
    - 15%: midpoint yellow (226)
    - <= 5%: full red (196, bold at 0%)
    """
    if percentage >= 100:
        return "\033[1;38;5;46m"
    if percentage >= 50:
        return "\033[38;5;40m"
    if percentage >= 25:
        return "\033[38;5;76m"
    if percentage >= 21:
        return "\033[38;5;112m"
    if percentage >= 17:
        return "\033[38;5;184m"
    if percentage >= 14:
        return "\033[38;5;226m"
    if percentage >= 11:
        return "\033[38;5;220m"
    if percentage >= 8:
        return "\033[38;5;208m"
    if percentage >= 6:
        return "\033[38;5;202m"
    if percentage >= 1:
        return "\033[38;5;196m"
    return "\033[1;38;5;196m"


def format_bar(
    percentage: float,
    total_cells: int = 10,
    color_enabled: bool = True,
) -> tuple[str, str]:
    """Return a progress bar string and color code for the given percentage (0..100)."""
    pct = max(0.0, min(100.0, float(percentage)))
    int_pct = round(pct)

    color = quota_color_256(int_pct)

    if int_pct == 100:
        filled = total_cells
    else:
        filled = min(total_cells - 1, int(pct * total_cells / 100))
    empty = total_cells - filled

    bar_str = "█" * filled + "░" * empty
    pct_str = f"{int_pct:>3}%"
    if color_enabled:
        bar_colored = f"{color}{bar_str}{RESET}"
        pct_colored = f"{color}{pct_str}{RESET}"
    else:
        bar_colored = bar_str
        pct_colored = pct_str

    return bar_colored, pct_colored


def parse_reset_timestamp(bucket: dict[str, Any] | None) -> float | None:
    """Parse ISO-8601 reset_time into epoch seconds when present."""
    if not isinstance(bucket, dict):
        return None
    reset_time_str = bucket.get("reset_time")
    if not isinstance(reset_time_str, str) or not reset_time_str:
        return None
    try:
        dt = datetime.datetime.fromisoformat(reset_time_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.timestamp()
    except (ValueError, TypeError, OverflowError):
        return None


def compute_reset_in_seconds(
    bucket: dict[str, Any], now_ts: float | None = None
) -> int:
    """Compute remaining seconds from ISO-8601 reset_time when present, else reset_in_seconds."""
    reset_ts = parse_reset_timestamp(bucket)
    if reset_ts is not None:
        ref = time.time() if now_ts is None else now_ts
        return max(0, int(reset_ts - ref))
    try:
        return max(0, int(bucket.get("reset_in_seconds", 0)))
    except (ValueError, TypeError):
        return 0


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return _ANSI_RE.sub("", text)


def visible_width(text: str) -> int:
    """Return terminal visible column width of text, ignoring ANSI escapes."""
    return len(strip_ansi(text))


def pad_cell(text: str, width: int, align: str = "left") -> str:
    """Pad text to width visible terminal columns, supporting left, right, or center alignment."""
    vis = visible_width(text)
    diff = max(0, width - vis)
    if align == "right":
        return " " * diff + text
    if align == "center":
        left = diff // 2
        return " " * left + text + " " * (diff - left)
    return text + " " * diff


def format_duration_cell(seconds: int, color_enabled: bool = True) -> tuple[str, str]:
    """Format duration into a concise cell with clock/unit colors, e.g. ('1h 9m', '6d20h')."""
    seconds = max(0, int(seconds))
    days, rem = divmod(seconds, 86_400)
    hours, rem = divmod(rem, 3_600)
    mins = rem // 60
    c_clock = "\033[1;38;5;123m"
    c_unit = "\033[38;5;117m"
    if days > 0:
        h_str = f"{hours:02d}" if hours < 10 else f"{hours}"
        plain = f"{days}d{h_str}h"
        colored = f"{c_clock}{days}{c_unit}d{c_clock}{h_str}{c_unit}h{RESET}"
    elif hours > 0:
        if mins < 10:
            plain = f"{hours}h {mins}m"
            colored = f"{c_clock}{hours}{c_unit}h {c_clock}{mins}{c_unit}m{RESET}"
        else:
            plain = f"{hours}h{mins}m"
            colored = f"{c_clock}{hours}{c_unit}h{c_clock}{mins}{c_unit}m{RESET}"
    else:
        plain = f"{mins}m"
        colored = f"{c_clock}{mins}{c_unit}m{RESET}"
    if not color_enabled:
        return plain, plain
    return colored, plain


def format_remain_clock_cell(
    delta_seconds: int, color_enabled: bool = True
) -> tuple[str, str]:
    """Format signed time left on clock as 'HHhMMm', 'Dd HHhMMm', '-HHhMMm', or '-Dd HHhMMm'."""
    neg = delta_seconds < 0
    abs_s = abs(int(delta_seconds))
    days, rem = divmod(abs_s, 86_400)
    hours, rem = divmod(rem, 3_600)
    mins = rem // 60
    sign = "-" if neg else ""
    c_clock = "\033[1;38;5;123m"
    c_unit = "\033[38;5;117m"
    c_neg = "\033[1;38;5;196m"

    if days > 0:
        plain = f"{sign}{days}d {hours:02d}h{mins:02d}m"
        if not color_enabled:
            return plain, plain
        if neg:
            return f"{c_neg}{plain}{RESET}", plain
        colored = f"{c_clock}{days}{c_unit}d {c_clock}{hours:02d}{c_unit}h{c_clock}{mins:02d}{c_unit}m{RESET}"
        return colored, plain

    plain = f"{sign}{hours:02d}h{mins:02d}m"
    if not color_enabled:
        return plain, plain
    if neg:
        return f"{c_neg}{plain}{RESET}", plain
    colored = f"{c_clock}{hours:02d}{c_unit}h{c_clock}{mins:02d}{c_unit}m{RESET}"
    return colored, plain


def format_datetime_str(
    bucket: dict[str, Any] | None, color_enabled: bool = True
) -> tuple[str, str]:
    """Format bucket reset timestamp into local datetime string, e.g. 'Nov 13 23:55'."""
    if not isinstance(bucket, dict):
        return "N/A", "N/A"
    r_ts = parse_reset_timestamp(bucket)
    if r_ts is None:
        return "N/A", "N/A"
    try:
        local_dt = datetime.datetime.fromtimestamp(
            r_ts, tz=datetime.timezone.utc
        ).astimezone()
        s = local_dt.strftime("%b %d %H:%M")
        if not color_enabled:
            return s, s
        return f"\033[38;5;153m{s}{RESET}", s
    except (ValueError, TypeError, OverflowError, OSError):
        return "N/A", "N/A"


def _abbreviate_timezone(tz_name: str, *, max_width: int = 5) -> str:
    """Shorten verbose platform timezone names (e.g. Windows 'Coordinated Universal Time') to <= max_width."""
    tz = tz_name.strip()
    if len(tz) <= max_width:
        return tz
    low = tz.lower()
    if low in ("coordinated universal time", "utc"):
        return "UTC"
    if low in ("greenwich mean time", "gmt"):
        return "GMT"
    words = [w for w in tz.split() if w]
    if len(words) >= 2:
        initials = "".join(w[0].upper() for w in words if w[0].isalpha())
        if initials:
            return initials[:max_width]
    return tz[:max_width]


def format_timezone_str(
    bucket: dict[str, Any] | None, color_enabled: bool = True
) -> tuple[str, str]:
    """Format bucket timezone abbreviation, e.g. 'EST' or 'UTC'."""
    if not isinstance(bucket, dict):
        return "", ""
    r_ts = parse_reset_timestamp(bucket)
    if r_ts is None:
        return "", ""
    try:
        local_dt = datetime.datetime.fromtimestamp(
            r_ts, tz=datetime.timezone.utc
        ).astimezone()
        tz = _abbreviate_timezone(local_dt.strftime("%Z"))
        if not color_enabled:
            return tz, tz
        return f"\033[38;5;110m{tz}{RESET}", tz
    except (ValueError, TypeError, OverflowError, OSError):
        return "", ""


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Atomically write JSON to path so concurrent readers never observe partial writes."""
    tmp_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
        )
        tmp_path = Path(tmp_name)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(data))
        os.replace(tmp_path, path)
    except (OSError, ValueError, TypeError):
        if tmp_path is not None:
            with contextlib.suppress(OSError):
                tmp_path.unlink(missing_ok=True)


def load_quota_payload(
    custom_path: str | None = None,
) -> tuple[dict[str, Any] | None, Path | None, float | None]:
    """Locate and load the freshest Antigravity quota JSON payload and its update timestamp."""
    if custom_path:
        p = Path(custom_path)
        if not p.is_file():
            return None, None, None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                ts = float(data.get("quota_updated_at") or p.stat().st_mtime)
                return data, p, ts
        except (OSError, ValueError, TypeError):
            return None, None, None
        return None, None, None

    if "AGY_QUOTA_FILE" in os.environ and os.environ["AGY_QUOTA_FILE"].strip():
        candidates: tuple[Path, ...] = (Path(os.environ["AGY_QUOTA_FILE"]),)
    else:
        candidates = _resolve_default_cache_paths()

    best_data: dict[str, Any] | None = None
    best_path: Path | None = None
    best_ts: float | None = None

    for p in candidates:
        if p.is_file():
            with contextlib.suppress(OSError, ValueError, TypeError):
                text = p.read_text(encoding="utf-8")
                data = json.loads(text)
                if isinstance(data, dict):
                    ts = float(data.get("quota_updated_at") or p.stat().st_mtime)
                    if best_ts is None or ts > best_ts:
                        best_data = data
                        best_path = p
                        best_ts = ts

    return best_data, best_path, best_ts


def _default_session_metadata() -> dict[str, Any]:
    """Read model and agentMode defaults from settings.json when no prior cache exists."""
    settings_path = Path.home() / ".gemini" / "antigravity-cli" / "settings.json"
    meta: dict[str, Any] = {}
    if settings_path.is_file():
        with contextlib.suppress(OSError, ValueError, TypeError):
            cfg = json.loads(settings_path.read_text(encoding="utf-8"))
            if isinstance(cfg, dict):
                if cfg.get("model"):
                    m_name = sanitize_text(cfg["model"])
                    meta["model"] = {"display_name": m_name, "id": m_name}
                if cfg.get("agentMode"):
                    meta["cycle_mode"] = sanitize_text(cfg["agentMode"])
    return meta


def _parse_iso_expiry(expiry_str: Any) -> datetime.datetime | None:
    """Parse an ISO-8601 expiry timestamp into a timezone-aware UTC datetime."""
    if not isinstance(expiry_str, str) or not expiry_str.strip():
        return None
    try:
        dt = datetime.datetime.fromisoformat(expiry_str.strip().replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def _refresh_oauth_access_token(
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> tuple[str | None, int | None]:
    """Exchange a refresh token for a fresh access token via Google OAuth2 over HTTPS."""
    url = _validate_https_url(OAUTH_TOKEN_URL)
    data = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=8.0) as resp:
        refreshed = json.loads(resp.read().decode("utf-8"))
    if not isinstance(refreshed, dict):
        return None, None
    new_access = refreshed.get("access_token")
    if not isinstance(new_access, str) or not new_access:
        return None, None
    try:
        expires_in = int(refreshed.get("expires_in", 3600))
    except (ValueError, TypeError):
        expires_in = 3600
    return new_access, expires_in


def _get_valid_access_token_with_reason() -> tuple[str | None, str | None]:
    """Obtain a valid Google OAuth access token, refreshing only when client env vars are set."""
    client_id = os.environ.get("AW_GEMINI_QUOTA_CLIENT_ID", "").strip()
    client_secret = os.environ.get("AW_GEMINI_QUOTA_CLIENT_SECRET", "").strip()
    can_refresh = bool(client_id and client_secret)

    expired_seen = False
    refresh_failed = False

    for tok_path in _resolve_token_paths():
        if not tok_path.is_file():
            continue
        raw: Any = None
        with contextlib.suppress(OSError, ValueError, TypeError):
            raw = json.loads(tok_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            continue

        if "token" in raw:
            tok = raw.get("token")
            if not isinstance(tok, dict):
                continue
            access = tok.get("access_token")
            refresh = tok.get("refresh_token")
            exp_dt = _parse_iso_expiry(tok.get("expiry"))
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            is_expired = True
            if exp_dt is not None and (exp_dt - now_utc).total_seconds() > 60:
                is_expired = False

            if not is_expired and isinstance(access, str) and access:
                return access, None

            if (
                isinstance(access, str)
                and access
                or isinstance(refresh, str)
                and refresh
            ):
                expired_seen = True

            if isinstance(refresh, str) and refresh and can_refresh:
                try:
                    new_access, expires_in = _refresh_oauth_access_token(
                        refresh, client_id, client_secret
                    )
                    if new_access:
                        ttl = expires_in if expires_in is not None else 3600
                        tok["access_token"] = new_access
                        tok["expiry"] = (
                            now_utc + datetime.timedelta(seconds=ttl)
                        ).isoformat()
                        raw["token"] = tok
                        atomic_write_json(tok_path, raw)
                        return new_access, None
                except (
                    urllib.error.URLError,
                    TimeoutError,
                    OSError,
                    ValueError,
                    TypeError,
                ):
                    refresh_failed = True
                    continue
        elif "accounts" in raw:
            accs = raw.get("accounts")
            if isinstance(accs, list) and accs and isinstance(accs[0], dict):
                refresh = accs[0].get("refreshToken")
                if isinstance(refresh, str) and refresh:
                    expired_seen = True
                    if can_refresh:
                        try:
                            new_access, _ = _refresh_oauth_access_token(
                                refresh, client_id, client_secret
                            )
                            if new_access:
                                return new_access, None
                        except (
                            urllib.error.URLError,
                            TimeoutError,
                            OSError,
                            ValueError,
                            TypeError,
                        ):
                            refresh_failed = True
                            continue

    if expired_seen and not can_refresh:
        return None, TOKEN_EXPIRED_MESSAGE
    if refresh_failed:
        return None, TOKEN_EXPIRED_MESSAGE
    return None, "No valid Google OAuth token available for direct API call"


def get_valid_access_token() -> str | None:
    """Return a valid Google OAuth access token or None if unavailable/expired."""
    token, _ = _get_valid_access_token_with_reason()
    return token


def refresh_quota_via_api(
    base_payload: dict[str, Any] | None = None,
    write_caches: bool = True,
) -> tuple[dict[str, Any] | None, str | None]:
    """Query live quota directly from Cloud Code v1internal:retrieveUserQuotaSummary API."""
    access_token, token_err = _get_valid_access_token_with_reason()
    if not access_token:
        return (
            None,
            token_err or "No valid Google OAuth token available for direct API call",
        )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": ANTIGRAVITY_USER_AGENT,
    }
    body = json.dumps({"project": "aicode-consumers"}).encode("utf-8")
    last_err: str | None = None

    for host in ANTIGRAVITY_API_HOSTS:
        url = _validate_https_url(f"https://{host}/v1internal:retrieveUserQuotaSummary")
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=6.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not isinstance(data, dict):
                    last_err = f"{host} returned invalid JSON payload"
                    continue
                groups = data.get("groups") or []
                now_ts = time.time()
                new_quota: dict[str, dict[str, Any]] = {}
                for group in groups:
                    if not isinstance(group, dict):
                        continue
                    for bucket in group.get("buckets") or []:
                        if not isinstance(bucket, dict):
                            continue
                        raw_bid = bucket.get("bucketId")
                        if not isinstance(raw_bid, str) or not raw_bid.strip():
                            continue
                        bid = sanitize_text(raw_bid)
                        if not bid:
                            continue
                        entry: dict[str, Any] = {
                            "remaining_fraction": float(
                                bucket.get("remainingFraction", 0.0)
                            ),
                            "reset_time": sanitize_text(bucket.get("resetTime") or ""),
                        }
                        entry["reset_in_seconds"] = compute_reset_in_seconds(
                            entry, now_ts
                        )
                        new_quota[bid] = entry

                if new_quota:
                    merged: dict[str, Any] = (
                        dict(base_payload)
                        if isinstance(base_payload, dict)
                        else _default_session_metadata()
                    )
                    merged["quota"] = new_quota
                    merged["quota_updated_at"] = now_ts
                    if write_caches:
                        if (
                            "AGY_QUOTA_FILE" in os.environ
                            and os.environ["AGY_QUOTA_FILE"].strip()
                        ):
                            targets: tuple[Path, ...] = (
                                Path(os.environ["AGY_QUOTA_FILE"]),
                            )
                        else:
                            targets = _resolve_default_cache_paths()
                        for cache_path in targets:
                            atomic_write_json(cache_path, merged)
                        record_history_sample(now_ts, new_quota, persist=True)
                    return merged, None
                last_err = f"{host} returned no quota buckets"
        except urllib.error.HTTPError as exc:
            last_err = f"{host} HTTP {exc.code}"
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            ValueError,
            TypeError,
        ) as exc:
            last_err = f"{host} error: {type(exc).__name__}"

    return None, last_err or "Direct Cloud Code quota API failed"


def refresh_quota(
    base_payload: dict[str, Any] | None = None,
    write_caches: bool = True,
) -> tuple[dict[str, Any] | None, str | None]:
    """Refresh quota directly via the Cloud Code API without invoking external binaries."""
    return refresh_quota_via_api(base_payload=base_payload, write_caches=write_caches)


def load_history_samples(now_ts: float | None = None) -> list[dict[str, Any]]:
    """Load rolling quota history samples from disk within the last 6 hours."""
    ref = time.time() if now_ts is None else now_ts
    cutoff = ref - MAX_HISTORY_AGE_SECS
    hist_path = _resolve_history_path()
    if not hist_path.is_file():
        return []
    try:
        raw = json.loads(hist_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or not isinstance(raw.get("samples"), list):
            return []
        valid = [
            s
            for s in raw["samples"]
            if isinstance(s, dict)
            and isinstance(s.get("quota"), dict)
            and float(s.get("ts", 0.0)) >= cutoff
        ]
        valid.sort(key=lambda s: float(s.get("ts", 0.0)))
        return valid[-MAX_HISTORY_SAMPLES:]
    except (OSError, ValueError, TypeError):
        return []


def record_history_sample(
    ts: float,
    quota: dict[str, Any] | None,
    persist: bool = True,
    existing: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Append a quota sample if its timestamp is distinct and optionally persist to disk."""
    samples = list(existing) if existing is not None else load_history_samples(ts)
    if not isinstance(quota, dict) or not quota:
        return samples

    compact: dict[str, dict[str, Any]] = {}
    for key in ("gemini-5h", "gemini-weekly", "3p-5h", "3p-weekly"):
        b = quota.get(key)
        if isinstance(b, dict) and "remaining_fraction" in b:
            compact[key] = {
                "remaining_fraction": round(float(b.get("remaining_fraction", 0.0)), 6),
                "reset_time": sanitize_text(b.get("reset_time") or ""),
            }
    if not compact:
        return samples

    cutoff = ts - MAX_HISTORY_AGE_SECS
    samples = [s for s in samples if float(s.get("ts", 0.0)) >= cutoff]

    if any(abs(ts - float(s.get("ts", 0.0))) < 2.0 for s in samples[-5:]):
        return samples

    samples.append({"ts": ts, "quota": compact})
    samples.sort(key=lambda s: float(s.get("ts", 0.0)))
    if len(samples) > MAX_HISTORY_SAMPLES:
        samples = samples[-MAX_HISTORY_SAMPLES:]

    if persist and not os.environ.get("AGY_QUOTA_FILE", "").strip():
        atomic_write_json(_resolve_history_path(), {"samples": samples})
    return samples


def obtain_quota_payload(
    custom_path: str | None,
    max_staleness: float,
) -> tuple[dict[str, Any] | None, Path | None, float | None, str | None]:
    """Return quota payload, refreshing via Cloud Code API when older than max_staleness seconds."""
    payload, path, updated_ts = load_quota_payload(custom_path)
    if custom_path or max_staleness < 0:
        return payload, path, updated_ts, None

    needs_refresh = (
        payload is None
        or updated_ts is None
        or (time.time() - updated_ts) >= max_staleness
    )
    if not needs_refresh:
        return payload, path, updated_ts, None

    refreshed, err = refresh_quota(payload, write_caches=True)
    if refreshed is not None:
        if "AGY_QUOTA_FILE" in os.environ and os.environ["AGY_QUOTA_FILE"].strip():
            target_path = Path(os.environ["AGY_QUOTA_FILE"])
        else:
            target_path = _resolve_default_cache_paths()[-1]
        return refreshed, target_path, float(refreshed["quota_updated_at"]), None

    return payload, path, updated_ts, err


def _filter_quota_dict(
    quota: dict[str, Any],
    gemini_only: bool = False,
    tp_only: bool = False,
) -> dict[str, Any]:
    """Filter quota bucket mapping by --gemini / --3p selection flags."""
    if not gemini_only and not tp_only:
        return dict(quota)
    filtered: dict[str, Any] = {}
    for key, val in quota.items():
        if (
            gemini_only
            and str(key).startswith("gemini-")
            or tp_only
            and str(key).startswith("3p-")
        ):
            filtered[key] = val
    return filtered


def format_single_status_bar(
    payload: dict[str, Any],
    color_enabled: bool = True,
    gemini_only: bool = False,
    tp_only: bool = False,
) -> str:
    """Format single-line status bar string matching agy's statusLine."""
    quota = payload.get("quota") or {}
    c_model = "\033[1;38;5;215m"
    c_variant = "\033[1;38;5;183m"
    c_bdr = "\033[38;5;67m"
    c_hdr = "\033[38;5;110m"
    c_clock = "\033[1;38;5;123m"
    c_unit = "\033[38;5;117m"

    def _color_dur(seconds: int) -> str:
        seconds = max(0, int(seconds))
        days, remainder = divmod(seconds, 86_400)
        hours, remainder = divmod(remainder, 3_600)
        minutes = remainder // 60
        if not color_enabled:
            return format_duration(seconds)
        if days > 0:
            return f"{c_clock}{days}{c_unit}d{c_clock}{hours}{c_unit}h{RESET}"
        if hours > 0:
            return f"{c_clock}{hours}{c_unit}h{c_clock}{minutes}{c_unit}m{RESET}"
        return f"{c_clock}{minutes}{c_unit}m{RESET}"

    def _bucket_str(bucket: dict[str, Any] | None) -> str:
        if not bucket:
            return (
                "unavailable"
                if not color_enabled
                else f"\033[38;5;244munavailable{RESET}"
            )
        pct = round(float(bucket.get("remaining_fraction", 0)) * 100)
        pct = max(0, min(100, pct))
        total_cells = 9
        filled = (
            total_cells
            if pct == 100
            else min(total_cells - 1, int(pct * total_cells / 100))
        )
        bar = "█" * filled + "░" * (total_cells - filled)
        reset_in = compute_reset_in_seconds(bucket)
        reset_str = _color_dur(reset_in)

        if not color_enabled:
            return f"{reset_str} {bar}{pct}%"

        col = quota_color_256(pct)
        return f"{reset_str} {col}{bar}{pct}%{RESET}"

    model_obj = payload.get("model") or {}
    if isinstance(model_obj, dict):
        display_name = sanitize_text(
            model_obj.get("display_name") or model_obj.get("id") or ""
        ).replace(" ", "")
        effort = sanitize_text(model_obj.get("effort") or "")
        if "(" in display_name and display_name.endswith(")"):
            base, rest = display_name.split("(", 1)
            display_name = base
            if not effort:
                effort = rest[:-1]
    elif isinstance(model_obj, str):
        raw = sanitize_text(model_obj).replace(" ", "")
        if "(" in raw and raw.endswith(")"):
            base, rest = raw.split("(", 1)
            display_name = base
            effort = rest[:-1]
        else:
            display_name = raw
            effort = ""
    else:
        display_name = ""
        effort = ""

    if not color_enabled:
        if not display_name:
            model_name = effort.capitalize() if effort else ""
        elif effort and effort.lower() not in display_name.lower():
            model_name = f"{display_name}({effort.capitalize()})"
        else:
            model_name = display_name
    else:
        if not display_name:
            eff_cap = effort.capitalize()
            model_name = f"{c_variant}{eff_cap}{RESET}" if eff_cap else ""
        elif effort and effort.lower() not in display_name.lower():
            eff_cap = effort.capitalize()
            model_name = f"{c_model}{display_name}{c_variant}({eff_cap}){RESET}"
        else:
            model_name = f"{c_model}{display_name}{RESET}"

    mode = sanitize_text(
        payload.get("cycle_mode")
        or payload.get("agent_mode")
        or payload.get("permission_mode")
        or (payload.get("permissions") or {}).get("mode")
        or ""
    ).lower()

    if not color_enabled:
        if mode in ("accept-edits", "bypass", "auto", "allowed"):
            edit_status = "Edit:Allowed"
        elif mode in ("plan", "read-only", "readonly"):
            edit_status = "Edit:Plan"
        elif mode in ("deny", "denied", "disabled"):
            edit_status = "Edit:Denied"
        else:
            edit_status = f"Edit:{mode.capitalize() or 'Ask'}"
    else:
        label = f"{c_hdr}Edit{c_bdr}:"
        if mode in ("accept-edits", "bypass", "auto", "allowed"):
            edit_status = f"{label}\033[1;38;5;78mAllowed{RESET}"
        elif mode in ("plan", "read-only", "readonly"):
            edit_status = f"{label}\033[1;38;5;208mPlan{RESET}"
        elif mode in ("deny", "denied", "disabled"):
            edit_status = f"{label}\033[1;38;5;196mDenied{RESET}"
        else:
            edit_status = f"{label}\033[1;38;5;51m{mode.capitalize() or 'Ask'}{RESET}"

    gem_5h = _bucket_str(quota.get("gemini-5h"))
    gem_weekly = _bucket_str(quota.get("gemini-weekly"))
    tp_5h = _bucket_str(quota.get("3p-5h"))
    tp_weekly = _bucket_str(quota.get("3p-weekly"))

    gem_label = "Gem:" if not color_enabled else f"\033[1;38;5;51mGem{c_bdr}:{RESET}"
    tp_label = (
        "Cld/GPT:"
        if not color_enabled
        else f"\033[1;38;5;213mCld{c_bdr}/\033[1;38;5;141mGPT{c_bdr}:{RESET}"
    )

    parts: list[str] = []
    if model_name:
        parts.append(model_name)
    if edit_status:
        parts.append(edit_status)
    if not tp_only:
        parts.append(f"{gem_label}{gem_5h}")
        parts.append(gem_weekly)
    if not gemini_only:
        parts.append(f"{tp_label}{tp_5h}")
        parts.append(tp_weekly)

    sep = "|" if not color_enabled else f"{c_bdr}|{RESET}"
    return sep.join(parts)


class BrailleCanvas:
    """2x4 sub-pixel Unicode Braille 2D canvas with priority-layered ANSI colors."""

    def __init__(self, char_cols: int, char_rows: int) -> None:
        self.char_cols = max(8, int(char_cols))
        self.char_rows = max(2, int(char_rows))
        self.px_w = self.char_cols * 2
        self.px_h = self.char_rows * 4
        self.masks: list[list[int]] = [
            [0] * self.char_cols for _ in range(self.char_rows)
        ]
        self.colors: list[list[str]] = [
            [""] * self.char_cols for _ in range(self.char_rows)
        ]
        self.priorities: list[list[int]] = [
            [0] * self.char_cols for _ in range(self.char_rows)
        ]

    def plot_px(self, px: int, py: int, color: str = "", priority: int = 2) -> None:
        """Set a single sub-pixel if inside canvas bounds."""
        if px < 0 or px >= self.px_w or py < 0 or py >= self.px_h:
            return
        cx, dx = divmod(px, 2)
        cy, dy = divmod(py, 4)
        self.masks[cy][cx] |= BRAILLE_DOTS[dy][dx]
        if priority >= self.priorities[cy][cx] and color:
            self.colors[cy][cx] = color
            self.priorities[cy][cx] = priority

    def draw_line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: str = "",
        priority: int = 2,
        dash_period: int = 0,
        dash_on: int = 0,
    ) -> None:
        """Draw a solid or dashed Bresenham line between two sub-pixel coordinates."""
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        step = 0
        cx, cy = x0, y0
        while True:
            if dash_period <= 0 or (step % dash_period) < dash_on:
                self.plot_px(cx, cy, color=color, priority=priority)
            if cx == x1 and cy == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                cx += sx
            if e2 <= dx:
                err += dx
                cy += sy
            step += 1

    def render_rows(self, color_enabled: bool = True) -> list[str]:
        """Render character rows with minimal ANSI color escape transitions."""
        rows: list[str] = []
        for cy in range(self.char_rows):
            parts: list[str] = []
            active_color = ""
            for cx in range(self.char_cols):
                mask = self.masks[cy][cx]
                ch = " " if mask == 0 else chr(0x2800 | mask)
                if color_enabled and mask != 0:
                    col = self.colors[cy][cx]
                    if col != active_color:
                        if active_color:
                            parts.append(RESET)
                        if col:
                            parts.append(col)
                        active_color = col
                elif color_enabled and active_color:
                    parts.append(RESET)
                    active_color = ""
                parts.append(ch)
            if color_enabled and active_color:
                parts.append(RESET)
            rows.append("".join(parts))
        return rows


def _extract_bucket_segments(
    bucket_key: str,
    samples: list[dict[str, Any]],
    current_bucket: dict[str, Any] | None,
    sample_ts: float,
) -> list[list[tuple[float, float, float | None]]]:
    """Split recorded bucket history into contiguous window segments: (ts, pct, reset_ts)."""
    pts: list[tuple[float, float, float | None]] = []
    for s in samples:
        b = (s.get("quota") or {}).get(bucket_key)
        if not isinstance(b, dict) or "remaining_fraction" not in b:
            continue
        ts = float(s.get("ts", 0.0))
        pct = max(0.0, min(100.0, float(b.get("remaining_fraction", 0.0)) * 100.0))
        r_ts = parse_reset_timestamp(b)
        pts.append((ts, pct, r_ts))

    if isinstance(current_bucket, dict) and "remaining_fraction" in current_bucket:
        cur_pct = max(
            0.0,
            min(100.0, float(current_bucket.get("remaining_fraction", 0.0)) * 100.0),
        )
        cur_rts = parse_reset_timestamp(current_bucket)
        if not pts or abs(sample_ts - pts[-1][0]) >= 2.0:
            pts.append((sample_ts, cur_pct, cur_rts))

    if not pts:
        return []

    pts.sort(key=lambda item: item[0])
    segments: list[list[tuple[float, float, float | None]]] = [[pts[0]]]
    for pt in pts[1:]:
        prev = segments[-1][-1]
        reset_shifted = (
            prev[2] is not None and pt[2] is not None and abs(pt[2] - prev[2]) > 120.0
        )
        jumped_up = (pt[1] - prev[1]) > 5.0
        if reset_shifted or jumped_up:
            segments.append([pt])
        else:
            segments[-1].append(pt)
    return segments


def _ols_burn_rate_pct_per_hr(
    points: list[tuple[float, float, float | None]],
) -> float | None:
    """Compute ordinary least-squares burn rate (%/hr, >= 0) over (ts, pct) points."""
    if len(points) < 2:
        return None
    span = points[-1][0] - points[0][0]
    if span < 60.0:
        return None
    n = float(len(points))
    mean_t = sum(p[0] for p in points) / n
    mean_y = sum(p[1] for p in points) / n
    denom = sum((p[0] - mean_t) ** 2 for p in points)
    if denom <= 1e-9:
        return None
    slope_pct_per_sec = sum((p[0] - mean_t) * (p[1] - mean_y) for p in points) / denom
    return max(0.0, -slope_pct_per_sec * 3600.0)


def _interp_pct_in_segment(
    seg: list[tuple[float, float, float | None]], t: float
) -> float | None:
    """Piecewise-linearly interpolate remaining % at timestamp t within a single segment."""
    if not seg or t < seg[0][0] or t > seg[-1][0]:
        return None
    if len(seg) == 1 or abs(t - seg[0][0]) < 1e-6:
        return seg[0][1]
    if abs(t - seg[-1][0]) < 1e-6:
        return seg[-1][1]
    for i in range(len(seg) - 1):
        t0, y0, _ = seg[i]
        t1, y1, _ = seg[i + 1]
        if t0 <= t <= t1:
            if t1 - t0 <= 1e-6:
                return y1
            alpha = (t - t0) / (t1 - t0)
            return y0 + alpha * (y1 - y0)
    return seg[-1][1]


def analyze_bucket(
    bucket_key: str,
    label: str,
    current_bucket: dict[str, Any] | None,
    samples: list[dict[str, Any]],
    now_ts: float,
    payload_updated_ts: float | None = None,
) -> dict[str, Any]:
    """Compute burn rate, window baseline, and 0% exhaustion forecast for one quota bucket."""
    if not isinstance(current_bucket, dict):
        return {"key": bucket_key, "label": label, "available": False}

    rem_pct = max(
        0.0, min(100.0, float(current_bucket.get("remaining_fraction", 0.0)) * 100.0)
    )
    reset_in = compute_reset_in_seconds(current_bucket, now_ts)
    reset_ts = parse_reset_timestamp(current_bucket)
    if reset_ts is None and reset_in > 0:
        reset_ts = now_ts + reset_in

    window_secs = WEEKLY_SECS if "weekly" in bucket_key else FIVE_HOUR_SECS
    elapsed = max(0, window_secs - reset_in) if 0 < reset_in <= window_secs else 0
    if rem_pct < 99.95 and elapsed >= 60:
        window_avg_rate = ((100.0 - rem_pct) / float(elapsed)) * 3600.0
    else:
        window_avg_rate = 0.0

    sample_ts = float(payload_updated_ts) if payload_updated_ts is not None else now_ts
    segments = _extract_bucket_segments(bucket_key, samples, current_bucket, sample_ts)
    cur_seg = segments[-1] if segments else []

    is_weekly = "weekly" in bucket_key

    recent_pts = [p for p in cur_seg if p[0] >= now_ts - 1800.0]
    if len(recent_pts) < 2 and len(cur_seg) >= 2:
        recent_pts = cur_seg[-min(6, len(cur_seg)) :]

    sample_span_sec = (
        (recent_pts[-1][0] - recent_pts[0][0]) if len(recent_pts) >= 2 else 0.0
    )
    raw_ols = _ols_burn_rate_pct_per_hr(recent_pts) if sample_span_sec >= 60.0 else None

    if raw_ols is not None:
        if sample_span_sec < 300.0 and window_avg_rate > 0.0:
            blend_w = (sample_span_sec - 60.0) / 240.0
            burn_rate = blend_w * raw_ols + (1.0 - blend_w) * window_avg_rate
        else:
            burn_rate = raw_ols
        rate_source = "live"
    else:
        burn_rate = window_avg_rate
        rate_source = "weekly-avg" if is_weekly else "5h-avg"
        sample_span_sec = 0.0

    if is_weekly:
        elapsed_hr = max(0.1, float(elapsed) / 3600.0)
        if elapsed_hr >= 24.0:
            forecast_rate = window_avg_rate * (5.0 / 7.0)
        else:
            forecast_rate = window_avg_rate * (8.0 / 24.0) * (5.0 / 7.0)
    else:
        forecast_rate = burn_rate

    if rem_pct <= 0.05:
        status = "exhausted"
        secs_to_zero: int | None = 0
        zero_ts: float | None = now_ts
        will_exhaust_before_reset = True
        proj_pct_at_reset = 0.0
        remain_clock_seconds = -reset_in if reset_in > 0 else 0
    elif forecast_rate < 0.02:
        status = "idle"
        secs_to_zero = None
        zero_ts = None
        will_exhaust_before_reset = False
        proj_pct_at_reset = rem_pct
        remain_clock_seconds = reset_in if reset_in > 0 else window_secs
    else:
        secs_to_zero = round((rem_pct / forecast_rate) * 3600.0)
        zero_ts = now_ts + secs_to_zero
        if reset_in > 0:
            proj_pct_at_reset = max(0.0, rem_pct - forecast_rate * (reset_in / 3600.0))
            will_exhaust_before_reset = secs_to_zero < reset_in
            status = (
                "exhaust_before_reset" if will_exhaust_before_reset else "resets_first"
            )
            remain_clock_seconds = secs_to_zero - reset_in
        else:
            proj_pct_at_reset = 0.0
            will_exhaust_before_reset = True
            status = "burning_no_reset"
            remain_clock_seconds = secs_to_zero - window_secs

    return {
        "key": bucket_key,
        "label": label,
        "available": True,
        "remaining_pct": rem_pct,
        "reset_in_seconds": reset_in,
        "reset_ts": reset_ts,
        "burn_rate_pct_per_hr": round(burn_rate, 3),
        "burn_rate_pct_per_min": round(burn_rate / 60.0, 4),
        "window_avg_pct_per_hr": round(window_avg_rate, 3),
        "rate_source": rate_source,
        "sample_span_seconds": int(sample_span_sec),
        "num_samples": sum(len(seg) for seg in segments),
        "status": status,
        "seconds_to_zero": secs_to_zero,
        "zero_time_iso": (
            datetime.datetime.fromtimestamp(zero_ts, tz=datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            if zero_ts is not None
            else None
        ),
        "zero_ts": zero_ts,
        "will_exhaust_before_reset": will_exhaust_before_reset,
        "projected_pct_at_reset": round(proj_pct_at_reset, 2),
        "remain_clock_seconds": int(remain_clock_seconds),
        "_segments": segments,
    }


analyze_5h_bucket = analyze_bucket


def _format_local_clock(ts: float, now_ts: float) -> str:
    """Format epoch timestamp into concise local clock time (adding date if another day)."""
    dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).astimezone()
    now_dt = datetime.datetime.fromtimestamp(
        now_ts, tz=datetime.timezone.utc
    ).astimezone()
    if dt.date() == now_dt.date():
        return dt.strftime("%H:%M %Z")
    return dt.strftime("%b %d %H:%M %Z")


def _choose_nice_ymax(peak: float) -> float:
    """Pick a clean Y-axis ceiling (%/hr) above peak."""
    target = max(10.0, peak * 1.15)
    for cand in (
        10,
        15,
        20,
        25,
        30,
        40,
        50,
        60,
        75,
        100,
        125,
        150,
        200,
        250,
        300,
        400,
        500,
    ):
        if cand >= target:
            return float(cand)
    return float(int((target + 99.0) // 100.0) * 100)


def _build_xaxis_labels(char_cols: int, markers: list[tuple[int, str]]) -> str:
    """Place non-overlapping label strings along a fixed-width X-axis row."""
    buf = [" "] * char_cols
    occupied = [False] * char_cols
    for pos, text in markers:
        if not text:
            continue
        start = max(0, min(char_cols - len(text), pos))
        if any(occupied[i] for i in range(start, start + len(text))):
            continue
        for i, ch in enumerate(text):
            buf[start + i] = ch
            occupied[start + i] = True
    return "".join(buf).rstrip()


def render_watch_forecast_panel(
    payload: dict[str, Any],
    samples: list[dict[str, Any]],
    now_ts: float,
    color_enabled: bool = True,
    gemini_only: bool = False,
    tp_only: bool = False,
    include_text_summary: bool = True,
) -> str:
    """Render 5-hour burn-rate metrics, zero-exhaustion ETA, and visual 2D Braille plots."""
    quota = payload.get("quota") or {}
    term_size = shutil.get_terminal_size((100, 40))
    chart_cols = max(36, min(68, term_size.columns - 14))
    compact_height = term_size.lines < 34
    traj_rows = 5 if compact_height else 7
    burn_rows = 4 if compact_height else 5

    c_bold = BOLD if color_enabled else ""
    c_dim = DIM if color_enabled else ""
    c_reset = RESET if color_enabled else ""
    c_gem = "\033[1;38;5;51m" if color_enabled else ""
    c_gem_dim = "\033[38;5;38m" if color_enabled else ""
    c_tp = "\033[1;38;5;213m" if color_enabled else ""
    c_tp_dim = "\033[38;5;170m" if color_enabled else ""
    c_warn = "\033[1;38;5;196m" if color_enabled else ""
    c_amber = "\033[1;38;5;214m" if color_enabled else ""
    c_ok = "\033[38;5;78m" if color_enabled else ""
    c_grid = "\033[38;5;239m" if color_enabled else ""
    c_now = "\033[38;5;246m" if color_enabled else ""

    specs: list[tuple[str, str, str, str]] = []
    if not tp_only:
        specs.append(("gemini-5h", "Gemini 5h", c_gem, c_gem_dim))
    if not gemini_only:
        specs.append(("3p-5h", "Claude/GPT 5h", c_tp, c_tp_dim))

    raw_ts = payload.get("quota_updated_at")
    payload_ts = float(raw_ts) if raw_ts else None
    analyses: list[tuple[dict[str, Any], str, str]] = []
    for b_key, b_label, col_main, col_proj in specs:
        info = analyze_5h_bucket(
            b_key,
            b_label,
            quota.get(b_key),
            samples,
            now_ts,
            payload_updated_ts=payload_ts,
        )
        if info.get("available"):
            analyses.append((info, col_main, col_proj))

    if not analyses:
        return ""

    out: list[str] = []
    n_hist = len(samples)
    hist_span = int(samples[-1]["ts"] - samples[0]["ts"]) if len(samples) >= 2 else 0
    if include_text_summary:
        hist_note = (
            f"{n_hist} samples over {format_duration(hist_span)}"
            if hist_span >= 60
            else f"{n_hist} sample{'s' if n_hist != 1 else ''} (refining live)"
        )
        out.append(
            f"{c_bold}5-Hour Burn Rate & Zero-Exhaustion Forecast{c_reset} {c_dim}· {hist_note}{c_reset}"
        )

        for info, col_main, _ in analyses:
            label = f"{info['label']}:"
            rate_hr = info["burn_rate_pct_per_hr"]
            rate_min = info["burn_rate_pct_per_min"]
            win_avg = info["window_avg_pct_per_hr"]
            src = "live slope" if info["rate_source"] == "live" else "5h window avg"
            avg_extra = (
                f", 5h avg {win_avg:.1f}%/hr" if info["rate_source"] == "live" else ""
            )

            status = info["status"]
            reset_in = info["reset_in_seconds"]
            secs_zero = info["seconds_to_zero"]
            zero_ts = info["zero_ts"]

            if status == "exhausted":
                eta_str = f"{c_warn}EXHAUSTED (0% now · resets in {format_duration(reset_in)}){c_reset}"
            elif status == "idle" or secs_zero is None or zero_ts is None:
                rst_note = (
                    f"resets in {format_duration(reset_in)}" if reset_in > 0 else "full"
                )
                eta_str = f"{c_ok}Will not hit 0% at current pace{c_reset} {c_dim}({rst_note}){c_reset}"
            elif status == "exhaust_before_reset":
                gap = format_duration(max(0, reset_in - secs_zero))
                z_clk = _format_local_clock(zero_ts, now_ts)
                eta_str = f"{c_warn}HITS 0% in {format_duration(secs_zero)} (at {z_clk}, {gap} BEFORE reset!){c_reset}"
            elif status == "resets_first":
                z_clk = _format_local_clock(zero_ts, now_ts)
                left_pct = info["projected_pct_at_reset"]
                tone = c_amber if left_pct < 15.0 else c_ok
                eta_str = (
                    f"{tone}Resets first in {format_duration(reset_in)} (~{left_pct:.0f}% left){c_reset} "
                    f"{c_dim}· 0% pace: {format_duration(secs_zero)} ({z_clk}){c_reset}"
                )
            else:
                z_clk = _format_local_clock(zero_ts, now_ts)
                eta_str = (
                    f"{c_amber}0% in {format_duration(secs_zero)} (at {z_clk}){c_reset}"
                )

            out.append(
                f"  {col_main}{label:<15}{c_reset} "
                f"Burn {c_bold}{rate_hr:5.1f}%/hr{c_reset} {c_dim}({rate_min:.2f}%/m · {src}{avg_extra}){c_reset}"
                f"  ->  {eta_str}"
            )

        out.append("")

    past_sec = 3600.0
    future_candidates: list[float] = []
    for info, _, _ in analyses:
        if info["reset_in_seconds"] > 0:
            future_candidates.append(float(info["reset_in_seconds"]) * 1.03)
        elif info["seconds_to_zero"] is not None and info["seconds_to_zero"] > 0:
            future_candidates.append(
                float(min(FIVE_HOUR_SECS, info["seconds_to_zero"]))
            )
    future_sec = max(
        1800.0,
        min(
            float(FIVE_HOUR_SECS),
            max(future_candidates) if future_candidates else 7200.0,
        ),
    )

    t_left = now_ts - past_sec
    t_right = now_ts + future_sec
    t_span = max(1.0, t_right - t_left)

    traj_canvas = BrailleCanvas(chart_cols, traj_rows)
    px_w = traj_canvas.px_w
    px_h = traj_canvas.px_h

    def _t_to_px(t_val: float) -> int:
        clamped = max(t_left, min(t_right, t_val))
        return round(((clamped - t_left) / t_span) * (px_w - 1))

    def _pct_to_py(pct_val: float) -> int:
        clamped = max(0.0, min(100.0, pct_val))
        return round((1.0 - clamped / 100.0) * (px_h - 1))

    traj_canvas.draw_line(
        0,
        _pct_to_py(50.0),
        px_w - 1,
        _pct_to_py(50.0),
        color=c_grid,
        priority=1,
        dash_period=6,
        dash_on=1,
    )
    traj_canvas.draw_line(
        0,
        px_h - 1,
        px_w - 1,
        px_h - 1,
        color=c_grid,
        priority=1,
        dash_period=4,
        dash_on=1,
    )
    now_px = _t_to_px(now_ts)
    traj_canvas.draw_line(
        now_px, 0, now_px, px_h - 1, color=c_now, priority=1, dash_period=3, dash_on=1
    )

    for idx, (info, col_main, col_proj) in enumerate(analyses):
        prio_base = 3 + idx
        segments = info["_segments"]
        cur_seg = segments[-1] if segments else []
        reset_ts = info["reset_ts"]

        if cur_seg and reset_ts is not None:
            win_start_ts = reset_ts - FIVE_HOUR_SECS
            first_t, first_pct, _ = cur_seg[0]
            if win_start_ts < first_t - 30.0 and first_t > t_left:
                t0 = max(t_left, win_start_ts)
                if first_t > win_start_ts:
                    frac_elapsed = (t0 - win_start_ts) / (first_t - win_start_ts)
                    pct0 = 100.0 + frac_elapsed * (first_pct - 100.0)
                    traj_canvas.draw_line(
                        _t_to_px(t0),
                        _pct_to_py(pct0),
                        _t_to_px(first_t),
                        _pct_to_py(first_pct),
                        color=col_proj,
                        priority=2,
                        dash_period=4,
                        dash_on=2,
                    )

        for seg in segments:
            vis = [p for p in seg if p[0] >= t_left - 600.0]
            for i in range(len(vis) - 1):
                t0, y0, _ = vis[i]
                t1, y1, _ = vis[i + 1]
                if t1 < t_left:
                    continue
                if t0 < t_left and t1 > t0:
                    y0 = y0 + ((t_left - t0) / (t1 - t0)) * (y1 - y0)
                    t0 = t_left
                traj_canvas.draw_line(
                    _t_to_px(t0),
                    _pct_to_py(y0),
                    _t_to_px(t1),
                    _pct_to_py(y1),
                    color=col_main,
                    priority=prio_base,
                )
            if len(vis) == 1 and t_left <= vis[0][0] <= t_right:
                traj_canvas.plot_px(
                    _t_to_px(vis[0][0]),
                    _pct_to_py(vis[0][1]),
                    color=col_main,
                    priority=prio_base,
                )

        rem_pct = info["remaining_pct"]
        reset_in = info["reset_in_seconds"]
        secs_zero = info["seconds_to_zero"]
        t_end_reset = min(t_right, now_ts + reset_in) if reset_in > 0 else t_right

        if info["will_exhaust_before_reset"] and secs_zero is not None:
            t_zero = min(t_right, now_ts + secs_zero)
            traj_canvas.draw_line(
                now_px,
                _pct_to_py(rem_pct),
                _t_to_px(t_zero),
                _pct_to_py(0.0),
                color=c_warn,
                priority=5,
                dash_period=3,
                dash_on=2,
            )
            if t_end_reset > t_zero:
                traj_canvas.draw_line(
                    _t_to_px(t_zero),
                    _pct_to_py(0.0),
                    _t_to_px(t_end_reset),
                    _pct_to_py(0.0),
                    color=c_warn,
                    priority=5,
                    dash_period=2,
                    dash_on=1,
                )
            if reset_in > 0 and now_ts + reset_in <= t_right:
                rx = _t_to_px(now_ts + reset_in)
                traj_canvas.draw_line(
                    rx,
                    _pct_to_py(0.0),
                    rx,
                    _pct_to_py(100.0),
                    color=col_proj,
                    priority=2,
                    dash_period=3,
                    dash_on=1,
                )
        else:
            end_pct = info["projected_pct_at_reset"] if reset_in > 0 else rem_pct
            traj_canvas.draw_line(
                now_px,
                _pct_to_py(rem_pct),
                _t_to_px(t_end_reset),
                _pct_to_py(end_pct),
                color=col_proj,
                priority=2,
                dash_period=4,
                dash_on=2,
            )
            if reset_in > 0 and now_ts + reset_in <= t_right:
                rx = _t_to_px(now_ts + reset_in)
                traj_canvas.draw_line(
                    rx,
                    _pct_to_py(end_pct),
                    rx,
                    _pct_to_py(100.0),
                    color=col_proj,
                    priority=2,
                    dash_period=3,
                    dash_on=1,
                )

    traj_rendered = traj_canvas.render_rows(color_enabled=color_enabled)
    out.append(
        f"  {c_bold}5h Quota Trajectory & Forecast{c_reset} "
        f"{c_dim}(solid = measured, dashed = projected to 0% / reset){c_reset}"
    )
    mid_row = traj_rows // 2
    for r_idx, row_str in enumerate(traj_rendered):
        if r_idx == 0:
            ylab = "100% ┤"
        elif r_idx == mid_row:
            ylab = " 50% ┤"
        elif r_idx == traj_rows - 1:
            ylab = "  0% ┤"
        else:
            ylab = "     │"
        out.append(f"  {c_dim}{ylab}{c_reset}{row_str}")

    now_col = now_px // 2
    axis_chars = ["─"] * chart_cols
    if 0 <= now_col < chart_cols:
        axis_chars[now_col] = "┴"
    out.append(f"  {c_dim}     └{''.join(axis_chars)}{c_reset}")
    x_markers: list[tuple[int, str]] = [
        (0, f"-{format_duration(int(past_sec))}"),
        (max(0, now_col - 1), "▲now"),
        (chart_cols - 8, f"+{format_duration(int(future_sec))}"),
    ]
    out.append(f"  {c_dim}      {_build_xaxis_labels(chart_cols, x_markers)}{c_reset}")
    out.append("")

    burn_span = float(max(900, min(3600, hist_span if hist_span > 0 else 900)))
    b_left = now_ts - burn_span
    burn_canvas = BrailleCanvas(chart_cols, burn_rows)
    b_pw = burn_canvas.px_w
    b_ph = burn_canvas.px_h

    series_curves: list[tuple[list[float | None], str, int]] = []
    peak_burn = 0.0
    lookback = max(300.0, min(900.0, burn_span / 4.0))
    for idx, (info, col_main, _) in enumerate(analyses):
        curve: list[float | None] = [None] * b_pw
        segments = info["_segments"]
        for px in range(b_pw):
            t_q = b_left + (px / float(max(1, b_pw - 1))) * burn_span
            for seg in segments:
                if seg[0][0] <= t_q <= seg[-1][0] and (seg[-1][0] - seg[0][0]) >= 20.0:
                    t_prev = max(seg[0][0], t_q - lookback)
                    dt_s = t_q - t_prev
                    if dt_s >= 60.0:
                        y_prev = _interp_pct_in_segment(seg, t_prev)
                        y_cur = _interp_pct_in_segment(seg, t_q)
                        if y_prev is not None and y_cur is not None:
                            rate_val = max(0.0, ((y_prev - y_cur) / dt_s) * 3600.0)
                            curve[px] = rate_val
                            peak_burn = max(peak_burn, rate_val)
                    break
        if all(v is None for v in curve):
            cur_r = float(info["burn_rate_pct_per_hr"])
            for px in range(max(0, b_pw - 4), b_pw):
                curve[px] = cur_r
            peak_burn = max(peak_burn, cur_r)
        series_curves.append((curve, col_main, 3 + idx))

    y_max = _choose_nice_ymax(peak_burn)

    def _rate_to_py(r_val: float) -> int:
        clamped = max(0.0, min(y_max, r_val))
        return round((1.0 - clamped / y_max) * (b_ph - 1))

    burn_canvas.draw_line(
        0,
        _rate_to_py(y_max / 2.0),
        b_pw - 1,
        _rate_to_py(y_max / 2.0),
        color=c_grid,
        priority=1,
        dash_period=6,
        dash_on=1,
    )
    burn_canvas.draw_line(
        0,
        b_ph - 1,
        b_pw - 1,
        b_ph - 1,
        color=c_grid,
        priority=1,
        dash_period=4,
        dash_on=1,
    )

    for curve, col_main, prio in series_curves:
        prev_pt: tuple[int, int] | None = None
        for px, val in enumerate(curve):
            if val is None:
                prev_pt = None
                continue
            py = _rate_to_py(val)
            if prev_pt is not None:
                burn_canvas.draw_line(
                    prev_pt[0], prev_pt[1], px, py, color=col_main, priority=prio
                )
            else:
                burn_canvas.plot_px(px, py, color=col_main, priority=prio)
            prev_pt = (px, py)

    burn_rendered = burn_canvas.render_rows(color_enabled=color_enabled)
    out.append(
        f"  {c_bold}Live Burn Rate{c_reset} {c_dim}(%/hr over last {format_duration(int(burn_span))}, peak {peak_burn:.1f}%/hr){c_reset}"
    )
    b_mid = burn_rows // 2
    for r_idx, row_str in enumerate(burn_rendered):
        if r_idx == 0:
            ylab = f"{int(y_max):>3d}%/h┤"
        elif r_idx == b_mid:
            ylab = f"{int(y_max // 2):>3d}%/h┤"
        elif r_idx == burn_rows - 1:
            ylab = "  0%/h┤"
        else:
            ylab = "      │"
        out.append(f"  {c_dim}{ylab}{c_reset}{row_str}")

    out.append(f"  {c_dim}      └{'─' * chart_cols}{c_reset}")
    b_markers: list[tuple[int, str]] = [
        (0, f"-{format_duration(int(burn_span))}"),
        (chart_cols // 2 - 2, f"-{format_duration(int(burn_span // 2))}"),
        (chart_cols - 3, "now"),
    ]
    legend_parts: list[str] = []
    if not tp_only:
        legend_parts.append(f"{c_gem}■ Gemini 5h{c_reset}")
    if not gemini_only:
        legend_parts.append(f"{c_tp}■ Claude/GPT 5h{c_reset}")
    legend_parts.append(f"{c_warn}╌╌ hits 0% early{c_reset}")
    out.append(f"  {c_dim}       {_build_xaxis_labels(chart_cols, b_markers)}{c_reset}")
    out.append("  " + "   ".join(legend_parts))

    return "\n".join(out)


def render_dashboard(
    payload: dict[str, Any],
    source_path: Path | None,
    mtime: float | None,
    color_enabled: bool = True,
    gemini_only: bool = False,
    tp_only: bool = False,
    watch_samples: list[dict[str, Any]] | None = None,
    show_charts: bool = False,
    show_context: bool = False,
) -> str:
    """Render full formatted CLI dashboard matching the unified status bar box style."""
    now_ts = time.time()
    quota = payload.get("quota") or {}
    samples = (
        watch_samples if watch_samples is not None else load_history_samples(now_ts)
    )

    c_bdr = "\033[38;5;67m" if color_enabled else ""
    c_hdr = "\033[38;5;110m" if color_enabled else ""
    c_gem = "\033[1;38;5;51m" if color_enabled else ""
    c_tp_cld = "\033[1;38;5;213m" if color_enabled else ""
    c_tp_slash = "\033[38;5;67m" if color_enabled else ""
    c_tp_gpt = "\033[1;38;5;141m" if color_enabled else ""
    c_target = "\033[1;38;5;229m" if color_enabled else ""
    c_dim = "\033[38;5;244m" if color_enabled else ""
    c_warn = "\033[1;38;5;196m" if color_enabled else ""
    c_date = "\033[38;5;153m" if color_enabled else ""
    bg_frame = "\033[48;5;67m" if color_enabled else ""
    fg_dark = "\033[38;5;16;1m" if color_enabled else ""
    c_bold = BOLD if color_enabled else ""
    c_reset = RESET if color_enabled else ""

    w_inner = 90
    c_tl, c_tr, c_bl, c_br = "╭", "╮", "╰", "╯"
    c_ml, c_mr, c_h, c_v = "├", "┤", "─", "│"
    c_t_down, c_t_up = "┬", "┴"

    plan_tier = (
        sanitize_text(payload.get("plan_tier") or "Google AI Ultra")
        or "Google AI Ultra"
    )
    email = sanitize_text(payload.get("email") or "")
    account_info = f"{plan_tier} ({email})" if email else plan_tier
    title_text = f"Antigravity Quota & Credit Status · {account_info}"
    max_title = w_inner - 8
    if visible_width(title_text) > max_title:
        title_text = title_text[: max_title - 1] + "…"

    if color_enabled:
        pill_content = f"{title_text}   "
        pill_badge = f"{pill_content}"
        rem_top = max(0, w_inner - 1 - visible_width(pill_badge))
        top_line = f"{c_bdr}{c_tl}{c_h}{bg_frame}{fg_dark}{pill_content}{c_reset}{c_bdr}{c_h * rem_top}{c_tr}{c_reset}"
    else:
        pill_content = f"[{title_text}]"
        rem_top = max(0, w_inner - 1 - len(pill_content))
        top_line = f"{c_tl}{c_h}{pill_content}{c_h * rem_top}{c_tr}"

    # Upper table header
    c1, c2, c3, c4, c5, c6, c7, c8 = 11, 16, 7, 14, 16, 7, 14, 5
    u_hdr_content = (
        f"{'Model':<{c1}}"
        f"{'5h':>{c2 - 2}}  "
        f"{'Reset':^{c3 - 1}} "
        f"{' Datetime':<{c4}}"
        f"{'Week':>{c5 - 2}}  "
        f"{'Reset':^{c6 - 1}} "
        f"{' Datetime':<{c7}}"
        f"{'Zone':^{c8}}"
    )
    u_hdr = f"{c_bdr}{c_v}{c_hdr}{u_hdr_content}{c_bdr}{c_v}{c_reset}"

    def render_upper_row(
        m_colored: str,
        m_plain: str,
        b_5h: dict[str, Any] | None,
        b_wk: dict[str, Any] | None,
    ) -> str:
        f_m = pad_cell(m_colored if color_enabled else m_plain, c1)

        pct_5h = (
            round(float((b_5h or {}).get("remaining_fraction", 0.0)) * 100.0)
            if b_5h
            else 0
        )
        bar_col_5h, pct_col_5h = format_bar(
            pct_5h, total_cells=10, color_enabled=color_enabled
        )
        f_5h = pad_cell(f"{bar_col_5h} {pct_col_5h} ", c2)

        r_in_5h = compute_reset_in_seconds(b_5h, now_ts) if b_5h else 0
        dur_c_5h, _ = (
            format_duration_cell(r_in_5h, color_enabled) if b_5h else ("N/A", "N/A")
        )
        f_r1 = pad_cell(dur_c_5h, c3 - 1, "right") + " "

        dt_c_5h, _ = format_datetime_str(b_5h, color_enabled)
        f_d1 = pad_cell(f" {dt_c_5h}", c4)

        pct_wk = (
            round(float((b_wk or {}).get("remaining_fraction", 0.0)) * 100.0)
            if b_wk
            else 0
        )
        bar_col_wk, pct_col_wk = format_bar(
            pct_wk, total_cells=10, color_enabled=color_enabled
        )
        f_wk = pad_cell(f"{bar_col_wk} {pct_col_wk} ", c5)

        r_in_wk = compute_reset_in_seconds(b_wk, now_ts) if b_wk else 0
        dur_c_wk, _ = (
            format_duration_cell(r_in_wk, color_enabled) if b_wk else ("N/A", "N/A")
        )
        f_r2 = pad_cell(dur_c_wk, c6 - 1, "right") + " "

        dt_c_wk, _ = format_datetime_str(b_wk, color_enabled)
        f_d2 = pad_cell(f" {dt_c_wk}", c7)

        tz_c, _ = format_timezone_str(b_5h or b_wk, color_enabled)
        f_z = pad_cell(tz_c, c8, "center")

        return f"{c_bdr}{c_v}{c_reset}{f_m}{f_5h}{f_r1}{f_d1}{f_wk}{f_r2}{f_d2}{f_z}{c_bdr}{c_v}{c_reset}"

    upper_rows: list[str] = []
    if not tp_only:
        m_col = f"{c_gem}Gemini{c_reset}"
        upper_rows.append(
            render_upper_row(
                m_col, "Gemini", quota.get("gemini-5h"), quota.get("gemini-weekly")
            )
        )
    if not gemini_only:
        m_col = f"{c_tp_cld}Claude{c_tp_slash}/{c_tp_gpt}GPT{c_reset}"
        upper_rows.append(
            render_upper_row(
                m_col, "Claude/GPT", quota.get("3p-5h"), quota.get("3p-weekly")
            )
        )

    div1 = f"{c_bdr}{c_ml}{c_h * w_inner}{c_mr}{c_reset}"

    # Subhead metadata
    n_hist = len(samples)
    hist_span = int(samples[-1]["ts"] - samples[0]["ts"]) if len(samples) >= 2 else 0
    hist_note = (
        f"{n_hist} samples over {format_duration(hist_span)}"
        if hist_span >= 60
        else (
            f"{n_hist} sample{'s' if n_hist != 1 else ''} (refining live)"
            if n_hist > 0
            else "Window averages"
        )
    )
    sub_title = "5-Hour & Weekly Burn Rate & Zero-Exhaustion Forecast"
    if color_enabled:
        sub_content = f"{c_target}{sub_title}{c_bdr} · {c_hdr}{hist_note}{c_reset}"
    else:
        sub_content = f"{sub_title} · {hist_note}"
    sub_line = (
        f"{c_bdr}{c_v}{c_reset}{pad_cell(sub_content, w_inner)}{c_bdr}{c_v}{c_reset}"
    )

    # Lower table with connected vertical column separators
    # Group widths: left_w (39) + │ (1) + mid_w (27) + │ (1) + right_w (22) = 90 (w_inner)
    lc1, lc2, lc3, lc4 = 13, 8, 9, 8
    left_w = lc1 + lc2 + lc3 + lc4 + 1
    mid_w = 27
    right_w = w_inner - left_w - 1 - mid_w - 1

    div2 = f"{c_bdr}{c_ml}{c_h * left_w}{c_t_down}{c_h * mid_w}{c_t_down}{c_h * right_w}{c_mr}{c_reset}"

    l_hdr_left = f"{' ':<{lc1}}{'Burn/hr':>{lc2}}{'Burn/min':>{lc3}}{'Ave/hr':>{lc4}} "
    l_hdr_mid = pad_cell("Estimated Time to Burnout", mid_w, "center")
    l_hdr_right = pad_cell("Remain at reset", right_w - 1, "right") + " "
    l_hdr = (
        f"{c_bdr}{c_v}{c_hdr}{l_hdr_left}"
        f"{c_bdr}{c_v}{c_hdr}{l_hdr_mid}"
        f"{c_bdr}{c_v}{c_hdr}{l_hdr_right}"
        f"{c_bdr}{c_v}{c_reset}"
    )

    lower_specs: list[tuple[str, str, str, str]] = []
    if not tp_only:
        lower_specs.append(
            (
                "gemini-5h",
                "Gemini 5h",
                f"{c_gem}Gemini{c_reset} {c_hdr}5h{c_reset}",
                "Gemini 5h",
            )
        )
        lower_specs.append(
            (
                "gemini-weekly",
                "Gemini Wk",
                f"{c_gem}Gemini{c_reset} {c_hdr}Wk{c_reset}",
                "Gemini Wk",
            )
        )
    if not gemini_only:
        lower_specs.append(
            (
                "3p-5h",
                "Claude/GPT 5h",
                f"{c_tp_cld}Claude{c_tp_slash}/{c_tp_gpt}GPT{c_reset} {c_hdr}5h{c_reset}",
                "Claude/GPT 5h",
            )
        )
        lower_specs.append(
            (
                "3p-weekly",
                "Claude/GPT Wk",
                f"{c_tp_cld}Claude{c_tp_slash}/{c_tp_gpt}GPT{c_reset} {c_hdr}Wk{c_reset}",
                "Claude/GPT Wk",
            )
        )

    lower_rows: list[str] = []
    raw_ts = payload.get("quota_updated_at")
    payload_ts = float(raw_ts) if raw_ts else None
    for b_key, b_label, m_col, m_plain in lower_specs:
        b_obj = quota.get(b_key)
        info = analyze_bucket(
            b_key, b_label, b_obj, samples, now_ts, payload_updated_ts=payload_ts
        )
        if not info.get("available"):
            continue

        b_hr = info["burn_rate_pct_per_hr"]
        b_min = info["burn_rate_pct_per_min"]
        ave_hr = info["window_avg_pct_per_hr"]
        will_burnout = info["will_exhaust_before_reset"]
        status = info["status"]
        secs_zero = info["seconds_to_zero"]
        zero_ts = info["zero_ts"]
        proj_pct = info["projected_pct_at_reset"]
        remain_clk_secs = int(info["remain_clock_seconds"])

        f_m = pad_cell(m_col if color_enabled else m_plain, lc1)
        f_bhr = pad_cell(
            f"{c_target}{b_hr:.1f}%{c_reset}" if color_enabled else f"{b_hr:.1f}%",
            lc2,
            "right",
        )
        f_bmin = pad_cell(
            f"{c_target}{b_min:.2f}%{c_reset}" if color_enabled else f"{b_min:.2f}%",
            lc3,
            "right",
        )
        f_ave = pad_cell(
            f"{c_target}{ave_hr:.1f}%{c_reset}" if color_enabled else f"{ave_hr:.1f}%",
            lc4,
            "right",
        )

        if status == "exhausted":
            eta_val = (
                f"{c_warn}EXHAUSTED (0% now){c_reset}"
                if color_enabled
                else "EXHAUSTED (0% now)"
            )
        elif status == "idle" or secs_zero is None or zero_ts is None:
            eta_val = f"{c_dim}∞{c_reset}" if color_enabled else "∞"
        else:
            dur_c, dur_p = format_duration_cell(secs_zero, color_enabled)
            z_dt = datetime.datetime.fromtimestamp(
                zero_ts, tz=datetime.timezone.utc
            ).astimezone()
            dt_str = z_dt.strftime("%b %d %H:%M")
            tz_str = z_dt.strftime("%Z")
            if color_enabled:
                eta_val = f"{dur_c} {c_date}{dt_str}{c_reset} {c_hdr}{tz_str}{c_reset}"
            else:
                eta_val = f"{dur_p} {dt_str} {tz_str}"
        f_eta = pad_cell(eta_val, mid_w - 1, "right") + " "

        if status == "exhausted" or will_burnout:
            rp = 0
            c_pct = remain_at_reset_color_256(rp)
            pct_cell = f"{c_pct}0%{c_reset}" if color_enabled else "0%"
        elif status == "idle":
            rp = round(info["remaining_pct"])
            c_pct = remain_at_reset_color_256(rp)
            if rp >= 100:
                pct_cell = f"{c_pct}100%{c_reset}" if color_enabled else "100%"
            else:
                pct_cell = (
                    f"{c_dim}~{c_reset}{c_pct}{rp}%{c_reset}"
                    if color_enabled
                    else f"~{rp}%"
                )
        else:
            rp = round(proj_pct)
            c_pct = remain_at_reset_color_256(rp)
            pct_cell = (
                f"{c_dim}~{c_reset}{c_pct}{rp}%{c_reset}"
                if color_enabled
                else f"~{rp}%"
            )

        clk_c, _ = format_remain_clock_cell(remain_clk_secs, color_enabled)
        clk_vis = visible_width(clk_c)
        pct_vis = visible_width(pct_cell)
        clk_w = max(10, clk_vis)
        pct_w = max(pct_vis, (right_w - 1) - 1 - clk_w)
        if pct_w + 1 + clk_w > right_w - 1:
            f_rem = pad_cell(f"{pct_cell} {clk_c}", right_w - 1, "right") + " "
        else:
            f_rem = f"{pad_cell(pct_cell, pct_w, 'right')} {pad_cell(clk_c, clk_w, 'right')} "

        lower_rows.append(
            f"{c_bdr}{c_v}{c_reset}{f_m}{f_bhr}{f_bmin}{f_ave} "
            f"{c_bdr}{c_v}{c_reset}{f_eta}"
            f"{c_bdr}{c_v}{c_reset}{f_rem}"
            f"{c_bdr}{c_v}{c_reset}"
        )

    bot_line = f"{c_bdr}{c_bl}{c_h * left_w}{c_t_up}{c_h * mid_w}{c_t_up}{c_h * right_w}{c_br}{c_reset}"

    lines = (
        [top_line, u_hdr]
        + upper_rows
        + [div1, sub_line, div2, l_hdr]
        + lower_rows
        + [bot_line]
    )

    # Context Window Section (only when explicitly requested via --context and present in payload)
    if show_context and not gemini_only and not tp_only:
        ctx = payload.get("context_window") or {}
        if isinstance(ctx, dict) and ctx:
            total_in = int(ctx.get("total_input_tokens") or 0)
            total_out = int(ctx.get("total_output_tokens") or 0)
            max_size = int(ctx.get("context_window_size") or 0)
            used_pct = float(ctx.get("used_percentage") or 0.0)
            rem_pct = float(ctx.get("remaining_percentage") or 100.0)
            cur_usage = ctx.get("current_usage") or {}
            cache_read = (
                int(cur_usage.get("cache_read_input_tokens") or 0)
                if isinstance(cur_usage, dict)
                else 0
            )

            lines.append("")
            lines.append(f"{c_bold}Context Window Usage:{c_reset}")
            lines.append(
                f"  {used_pct:.1f}% used ({total_in:,} input + {total_out:,} output of {max_size:,} tokens) · {rem_pct:.1f}% remaining"
            )
            if cache_read > 0:
                lines.append(f"  {c_dim}Cache Read:{c_reset} {cache_read:,} tokens")

    # Visual Charts Panel (watch mode or --plot)
    if show_charts and samples:
        chart_panel = render_watch_forecast_panel(
            payload,
            samples,
            now_ts,
            color_enabled=color_enabled,
            gemini_only=gemini_only,
            tp_only=tp_only,
            include_text_summary=False,
        )
        if chart_panel:
            lines.append("")
            lines.append(chart_panel)

    # Footer metadata
    if not gemini_only and not tp_only and mtime:
        age_seconds = time.time() - mtime
        age_str = format_relative_time(age_seconds)
        src_name = sanitize_text(source_path.name) if source_path else "cache"
        lines.append("")
        lines.append(f"{c_dim}Data Source: {src_name} (updated {age_str}){c_reset}")

    return "\n".join(lines).rstrip()


def build_json_forecast(
    payload: dict[str, Any],
    samples: list[dict[str, Any]],
    now_ts: float,
    gemini_only: bool = False,
    tp_only: bool = False,
) -> dict[str, Any]:
    """Return clean JSON-serializable burn-rate and 0%-exhaustion forecast dict."""
    quota = payload.get("quota") or {}
    raw_ts = payload.get("quota_updated_at")
    payload_ts = float(raw_ts) if raw_ts else None
    bucket_specs: list[tuple[str, str]] = []
    if not tp_only:
        bucket_specs.extend(
            [("gemini-5h", "Gemini 5h"), ("gemini-weekly", "Gemini Wk")]
        )
    if not gemini_only:
        bucket_specs.extend(
            [("3p-5h", "Claude/GPT 5h"), ("3p-weekly", "Claude/GPT Wk")]
        )

    res: dict[str, Any] = {}
    for key, label in bucket_specs:
        info = analyze_bucket(
            key, label, quota.get(key), samples, now_ts, payload_updated_ts=payload_ts
        )
        info.pop("_segments", None)
        info.pop("zero_ts", None)
        res[key] = info
    return res


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for gemini-quota."""
    parser = argparse.ArgumentParser(
        prog="gemini-quota",
        description="Display Gemini and third-party quota/credit status from Antigravity (AGY).",
    )
    parser.add_argument(
        "-b",
        "--bar",
        "--status-bar",
        "--compact",
        action="store_true",
        help="Print single-line compact status bar string as shown in agy TUI",
    )
    parser.add_argument(
        "-g",
        "--gemini",
        "--gemini-only",
        action="store_true",
        help="Display only Gemini quota buckets",
    )
    parser.add_argument(
        "-3",
        "--3p",
        "--third-party",
        dest="tp_only",
        action="store_true",
        help="Display only third-party (Claude/GPT) quota buckets",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Output raw quota JSON payload with burn_forecast",
    )
    parser.add_argument(
        "-w",
        "--watch",
        nargs="?",
        const=2.0,
        type=float,
        metavar="SECS",
        help="Live auto-refresh mode (default interval: 2 seconds)",
    )
    parser.add_argument(
        "-m",
        "--max-staleness",
        type=float,
        default=60.0,
        metavar="SECS",
        help=(
            "Refresh live quota from the Cloud Code API if cached data has not updated for at least "
            "SECS seconds (default: 60; 0 forces refresh; negative disables live refresh)"
        ),
    )
    parser.add_argument(
        "--no-color",
        "--plain",
        action="store_true",
        help="Disable ANSI color output",
    )
    parser.add_argument(
        "--color",
        action="store_true",
        help="Force ANSI color output even when piping or redirected",
    )
    parser.add_argument(
        "-p",
        "--plot",
        "--charts",
        action="store_true",
        help="Include 2D Braille trajectory and burn-rate visual charts",
    )
    parser.add_argument(
        "--context",
        action="store_true",
        help="Include local session context window and cache token breakdown",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Path to quota JSON file to read instead of default caches",
    )
    return parser


def _write_stdout(text: str) -> None:
    """Write text followed by newline to stdout and flush."""
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def _normalize_negative_option_args(argv: list[str]) -> list[str]:
    """Rewrite '-m -1' / '--max-staleness -1' to '=' form so '-3' does not make argparse reject negative floats."""
    out: list[str] = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in ("-m", "--max-staleness") and i + 1 < len(argv):
            nxt = argv[i + 1]
            if nxt.startswith("-"):
                try:
                    float(nxt)
                    out.append(f"{tok}={nxt}")
                    i += 2
                    continue
                except ValueError:
                    pass
        out.append(tok)
        i += 1
    return out


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    raw_argv = sys.argv[1:] if argv is None else list(argv)
    args = parser.parse_args(_normalize_negative_option_args(raw_argv))

    color_enabled = supports_color(args.no_color, force_color_flag=args.color)

    try:
        if args.watch is not None:
            interval = max(0.5, float(args.watch))
            session_samples: list[dict[str, Any]] | None = [] if args.file else None
            try:
                while True:
                    payload, path, updated_ts, refresh_err = obtain_quota_payload(
                        args.file,
                        args.max_staleness,
                    )
                    if not payload:
                        detail = f" ({refresh_err})" if refresh_err else ""
                        print(
                            f"Waiting for Antigravity quota data{detail}...",
                            file=sys.stderr,
                        )
                    else:
                        now_ts = time.time()
                        sample_ts = (
                            float(updated_ts) if updated_ts is not None else now_ts
                        )
                        if args.file:
                            session_samples = record_history_sample(
                                sample_ts,
                                payload.get("quota"),
                                persist=False,
                                existing=session_samples,
                            )
                            samples = session_samples
                        else:
                            samples = record_history_sample(
                                sample_ts,
                                payload.get("quota"),
                                persist=True,
                            )

                        if args.bar:
                            line = format_single_status_bar(
                                payload,
                                color_enabled=color_enabled,
                                gemini_only=args.gemini,
                                tp_only=args.tp_only,
                            )
                            panel = render_watch_forecast_panel(
                                payload,
                                samples,
                                now_ts,
                                color_enabled=color_enabled,
                                gemini_only=args.gemini,
                                tp_only=args.tp_only,
                            )
                            out_text = f"{line}\n\n{panel}" if panel else line
                            sys.stdout.write("\033[2J\033[H" + out_text + "\n")
                            sys.stdout.flush()
                        elif args.json:
                            enriched = dict(payload)
                            if args.gemini or args.tp_only:
                                enriched["quota"] = _filter_quota_dict(
                                    payload.get("quota") or {},
                                    gemini_only=args.gemini,
                                    tp_only=args.tp_only,
                                )
                            enriched["burn_forecast"] = build_json_forecast(
                                payload,
                                samples,
                                now_ts,
                                gemini_only=args.gemini,
                                tp_only=args.tp_only,
                            )
                            sys.stdout.write(
                                "\033[2J\033[H" + json.dumps(enriched, indent=2) + "\n"
                            )
                            sys.stdout.flush()
                        else:
                            dashboard = render_dashboard(
                                payload,
                                path,
                                updated_ts,
                                color_enabled=color_enabled,
                                gemini_only=args.gemini,
                                tp_only=args.tp_only,
                                watch_samples=samples,
                                show_charts=True,
                                show_context=args.context,
                            )
                            sys.stdout.write("\033[2J\033[H" + dashboard + "\n")
                            sys.stdout.flush()
                    time.sleep(interval)
            except KeyboardInterrupt:
                return 0

        # Single-shot mode
        payload, path, updated_ts, refresh_err = obtain_quota_payload(
            args.file,
            args.max_staleness,
        )
        if refresh_err and payload:
            print(
                f"Warning: live quota refresh failed ({refresh_err}); showing cached data.",
                file=sys.stderr,
            )
        if not payload:
            err_line = f"Live refresh error: {refresh_err}\n" if refresh_err else ""
            if args.file:
                print(
                    f"Error: Could not read Antigravity quota data from {args.file}.\n{err_line}".rstrip(),
                    file=sys.stderr,
                )
            else:
                print(
                    "Error: No Antigravity quota status data found.\n"
                    f"{err_line}"
                    "Checked location:\n"
                    "  - ~/.gemini/antigravity-cli/last_quota.json",
                    file=sys.stderr,
                )
            return 1

        now_ts = time.time()
        sample_ts = float(updated_ts) if updated_ts is not None else now_ts
        if args.file:
            samples = load_history_samples(now_ts)
        else:
            samples = record_history_sample(
                sample_ts,
                payload.get("quota"),
                persist=True,
            )

        if args.json:
            enriched = dict(payload)
            if args.gemini or args.tp_only:
                enriched["quota"] = _filter_quota_dict(
                    payload.get("quota") or {},
                    gemini_only=args.gemini,
                    tp_only=args.tp_only,
                )
            enriched["burn_forecast"] = build_json_forecast(
                payload,
                samples,
                now_ts,
                gemini_only=args.gemini,
                tp_only=args.tp_only,
            )
            _write_stdout(json.dumps(enriched, indent=2))
            return 0

        if args.bar:
            _write_stdout(
                format_single_status_bar(
                    payload,
                    color_enabled=color_enabled,
                    gemini_only=args.gemini,
                    tp_only=args.tp_only,
                )
            )
            return 0

        _write_stdout(
            render_dashboard(
                payload,
                path,
                updated_ts,
                color_enabled=color_enabled,
                gemini_only=args.gemini,
                tp_only=args.tp_only,
                watch_samples=samples,
                show_charts=args.plot,
                show_context=args.context,
            )
        )
        return 0
    except BrokenPipeError:
        with contextlib.suppress(OSError, ValueError):
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            os.close(devnull)
        return 0


if __name__ == "__main__":
    sys.exit(main())

"""Local Antigravity (agy) quota cache reader and burnout forecaster for the runner statusline.

Reads the local cache files written by Antigravity / ``agy-quota`` (never makes network
requests on the statusline render path, TTL-cached in memory, fail-open returning ``None``
whenever quota data is unavailable).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

FIVE_HOUR_SECS = 5 * 3600
WEEKLY_SECS = 7 * 86_400

DEFAULT_CACHE_PATHS: tuple[Path, ...] = (
    Path("/tmp/antigravity_quota.json"),
    Path.home() / ".gemini" / "antigravity-cli" / "last_quota.json",
)
DEFAULT_HISTORY_PATH: Path = (
    Path.home() / ".gemini" / "antigravity-cli" / "quota_history.json"
)


@dataclass(frozen=True)
class QuotaBucket:
    """One 5-hour or weekly quota bucket with burnout forecast."""

    reset_in_s: int
    remaining_pct: int
    will_burn_out: bool = False
    zero_in_s: Optional[int] = None


@dataclass(frozen=True)
class AgyQuotaSnapshot:
    """Gemini and third-party (Claude/GPT) quota buckets from Antigravity."""

    gemini_5h: Optional[QuotaBucket] = None
    gemini_weekly: Optional[QuotaBucket] = None
    tp_5h: Optional[QuotaBucket] = None
    tp_weekly: Optional[QuotaBucket] = None
    updated_at: Optional[float] = None


def model_quota_pool(model: Optional[str]) -> str:
    """Map an Antigravity model name to its quota pool ('gemini', 'claude', or 'gpt')."""
    low = (model or "").strip().lower()
    if any(tok in low for tok in ("claude", "opus", "sonnet", "haiku")):
        return "claude"
    if any(tok in low for tok in ("gpt", "codex", "o1", "o3", "o4")):
        return "gpt"
    return "gemini"


def quota_color_code_256(pct: int) -> tuple[int, bool]:
    """Return ``(ansi_256_code, bold)`` matching agy-quota's percentage color gradient."""
    if pct > 50:
        if pct >= 90:
            return (46, False)
        if pct >= 82:
            return (40, False)
        if pct >= 75:
            return (76, False)
        if pct >= 63:
            return (112, False)
        return (148, False)
    if pct > 25:
        if pct >= 43:
            return (184, False)
        if pct >= 34:
            return (226, False)
        return (220, False)
    if pct >= 18:
        return (202, False)
    if pct >= 10:
        return (160, False)
    if pct >= 4:
        return (196, False)
    return (196, True)


def _parse_reset_ts(bucket: Mapping[str, Any]) -> Optional[float]:
    raw = bucket.get("reset_time")
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str) and raw.strip():
        try:
            text = raw.strip().replace("Z", "+00:00")
            return dt.datetime.fromisoformat(text).timestamp()
        except Exception:
            return None
    return None


def _compute_reset_in_seconds(bucket: Mapping[str, Any], now_ts: float) -> int:
    reset_ts = _parse_reset_ts(bucket)
    if reset_ts is not None:
        return max(0, int(round(reset_ts - now_ts)))
    for key in ("reset_in_seconds", "reset_seconds", "resets_in_seconds"):
        val = bucket.get(key)
        if isinstance(val, (int, float)):
            return max(0, int(round(val)))
    return 0


def _extract_bucket_segments(
    bucket_key: str,
    samples: Sequence[Mapping[str, Any]],
    current_bucket: Mapping[str, Any],
    sample_ts: float,
) -> list[list[tuple[float, float, Optional[float]]]]:
    pts: list[tuple[float, float, Optional[float]]] = []
    for sample in samples:
        if not isinstance(sample, Mapping):
            continue
        ts = sample.get("ts")
        if not isinstance(ts, (int, float)):
            continue
        buckets = sample.get("buckets")
        if not isinstance(buckets, Mapping):
            continue
        b = buckets.get(bucket_key)
        if not isinstance(b, Mapping):
            continue
        rem = b.get("remaining_fraction")
        if not isinstance(rem, (int, float)):
            continue
        pts.append(
            (float(ts), max(0.0, min(100.0, float(rem) * 100.0)), _parse_reset_ts(b))
        )

    cur_rem = current_bucket.get("remaining_fraction")
    if isinstance(cur_rem, (int, float)):
        cur_pct = max(0.0, min(100.0, float(cur_rem) * 100.0))
        cur_reset = _parse_reset_ts(current_bucket)
        if not pts or abs(sample_ts - pts[-1][0]) > 1.0:
            pts.append((sample_ts, cur_pct, cur_reset))

    if not pts:
        return []

    pts.sort(key=lambda item: item[0])
    segments: list[list[tuple[float, float, Optional[float]]]] = [[pts[0]]]
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
    points: Sequence[tuple[float, float, Optional[float]]],
) -> Optional[float]:
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


def _analyze_bucket(
    bucket_key: str,
    current_bucket: Any,
    samples: Sequence[Mapping[str, Any]],
    now_ts: float,
    payload_updated_ts: Optional[float],
) -> Optional[QuotaBucket]:
    if not isinstance(current_bucket, Mapping):
        return None
    raw_rem = current_bucket.get("remaining_fraction")
    if not isinstance(raw_rem, (int, float)):
        return None

    rem_pct = max(0.0, min(100.0, float(raw_rem) * 100.0))
    reset_in = _compute_reset_in_seconds(current_bucket, now_ts)
    is_weekly = "weekly" in bucket_key
    window_secs = WEEKLY_SECS if is_weekly else FIVE_HOUR_SECS

    elapsed = max(0, window_secs - reset_in) if 0 < reset_in <= window_secs else 0
    if rem_pct < 99.95 and elapsed >= 60:
        window_avg_rate = ((100.0 - rem_pct) / float(elapsed)) * 3600.0
    else:
        window_avg_rate = 0.0

    sample_ts = float(payload_updated_ts) if payload_updated_ts is not None else now_ts
    segments = _extract_bucket_segments(bucket_key, samples, current_bucket, sample_ts)
    cur_seg = segments[-1] if segments else []
    recent_pts = [p for p in cur_seg if p[0] >= now_ts - 1800.0]
    if len(recent_pts) < 2 and len(cur_seg) >= 2:
        recent_pts = cur_seg[-min(6, len(cur_seg)) :]
    sample_span = (
        (recent_pts[-1][0] - recent_pts[0][0]) if len(recent_pts) >= 2 else 0.0
    )
    raw_ols = _ols_burn_rate_pct_per_hr(recent_pts) if sample_span >= 60.0 else None

    if raw_ols is not None:
        if sample_span < 300.0 and window_avg_rate > 0.0:
            blend_w = (sample_span - 60.0) / 240.0
            burn_rate = blend_w * raw_ols + (1.0 - blend_w) * window_avg_rate
        else:
            burn_rate = raw_ols
    else:
        burn_rate = window_avg_rate

    if is_weekly:
        elapsed_hr = max(0.1, float(elapsed) / 3600.0)
        if elapsed_hr >= 24.0:
            forecast_rate = window_avg_rate * (5.0 / 7.0)
        else:
            forecast_rate = window_avg_rate * (8.0 / 24.0) * (5.0 / 7.0)
    else:
        forecast_rate = burn_rate

    will_burn_out = False
    zero_in_s: Optional[int] = None
    if rem_pct <= 0.05:
        will_burn_out = True
        zero_in_s = 0
    elif forecast_rate >= 0.02:
        secs_to_zero = int(round((rem_pct / forecast_rate) * 3600.0))
        zero_in_s = secs_to_zero
        if reset_in > 0:
            will_burn_out = secs_to_zero < reset_in
        else:
            will_burn_out = True

    return QuotaBucket(
        reset_in_s=reset_in,
        remaining_pct=int(round(rem_pct)),
        will_burn_out=will_burn_out,
        zero_in_s=zero_in_s,
    )


def parse_quota_payload(
    payload: Mapping[str, Any],
    *,
    samples: Sequence[Mapping[str, Any]] = (),
    now_ts: Optional[float] = None,
    updated_at: Optional[float] = None,
) -> Optional[AgyQuotaSnapshot]:
    """Parse an agy-quota JSON payload + optional history samples into an AgyQuotaSnapshot."""
    quota = payload.get("quota")
    if not isinstance(quota, Mapping):
        return None
    now = float(time.time() if now_ts is None else now_ts)
    upd = updated_at
    if upd is None and isinstance(payload.get("quota_updated_at"), (int, float)):
        upd = float(payload["quota_updated_at"])

    gem_5h = _analyze_bucket("gemini-5h", quota.get("gemini-5h"), samples, now, upd)
    gem_wk = _analyze_bucket(
        "gemini-weekly", quota.get("gemini-weekly"), samples, now, upd
    )
    tp_5h = _analyze_bucket("3p-5h", quota.get("3p-5h"), samples, now, upd)
    tp_wk = _analyze_bucket("3p-weekly", quota.get("3p-weekly"), samples, now, upd)
    if not any((gem_5h, gem_wk, tp_5h, tp_wk)):
        return None
    return AgyQuotaSnapshot(
        gemini_5h=gem_5h,
        gemini_weekly=gem_wk,
        tp_5h=tp_5h,
        tp_weekly=tp_wk,
        updated_at=upd,
    )


_CACHE_LOCK = threading.Lock()
_CACHED_MONO: float = 0.0
_CACHED_SNAPSHOT: Optional[AgyQuotaSnapshot] = None


def clear_quota_cache() -> None:
    """Clear the in-process TTL cache (for tests)."""
    global _CACHED_MONO, _CACHED_SNAPSHOT
    with _CACHE_LOCK:
        _CACHED_MONO = 0.0
        _CACHED_SNAPSHOT = None


def load_agy_quota_snapshot(
    *,
    now_ts: Optional[float] = None,
    cache_paths: Optional[Sequence[Path]] = None,
    history_path: Optional[Path] = None,
    ttl_seconds: float = 15.0,
) -> Optional[AgyQuotaSnapshot]:
    """Read the freshest local agy quota cache file (TTL-cached, fail-open, zero network I/O)."""
    global _CACHED_MONO, _CACHED_SNAPSHOT

    env_file = os.environ.get("AGY_QUOTA_FILE")
    # Avoid leaking host ~/.gemini quota state into unrelated pytest tests unless explicitly configured.
    if cache_paths is None and not env_file and os.environ.get("PYTEST_CURRENT_TEST"):
        return None

    use_cache = cache_paths is None and history_path is None and now_ts is None
    if use_cache and ttl_seconds > 0:
        mono_now = time.monotonic()
        with _CACHE_LOCK:
            if _CACHED_MONO > 0 and (mono_now - _CACHED_MONO) < ttl_seconds:
                return _CACHED_SNAPSHOT

    if cache_paths is not None:
        candidates = tuple(cache_paths)
    elif env_file:
        candidates = (Path(env_file),)
    else:
        candidates = DEFAULT_CACHE_PATHS

    best_payload: Optional[dict[str, Any]] = None
    best_ts: Optional[float] = None
    for cand in candidates:
        try:
            if not cand.is_file():
                continue
            data = json.loads(cand.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            ts = float(data.get("quota_updated_at") or cand.stat().st_mtime)
            if best_ts is None or ts > best_ts:
                best_payload = data
                best_ts = ts
        except Exception:
            continue

    snap: Optional[AgyQuotaSnapshot] = None
    if best_payload is not None:
        samples: list[Mapping[str, Any]] = []
        hist_p = history_path if history_path is not None else DEFAULT_HISTORY_PATH
        try:
            if hist_p.is_file():
                raw_hist = json.loads(hist_p.read_text(encoding="utf-8"))
                if isinstance(raw_hist, list):
                    samples = [s for s in raw_hist if isinstance(s, Mapping)]
                elif isinstance(raw_hist, dict) and isinstance(
                    raw_hist.get("samples"), list
                ):
                    samples = [s for s in raw_hist["samples"] if isinstance(s, Mapping)]
        except Exception:
            samples = []
        snap = parse_quota_payload(
            best_payload, samples=samples, now_ts=now_ts, updated_at=best_ts
        )

    if use_cache:
        with _CACHE_LOCK:
            _CACHED_MONO = time.monotonic()
            _CACHED_SNAPSHOT = snap
    return snap

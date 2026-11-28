"""Behavioral core tests for agent_workflows.gemini_quota."""

from __future__ import annotations

import datetime
import io
import json
import urllib.error
from pathlib import Path
from typing import Any

import pytest
from typing_extensions import Self

from agent_workflows import gemini_quota

pytestmark = pytest.mark.core


def _iso_from_ts(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _sample_payload(
    now_ts: float,
    *,
    gem_5h_frac: float = 0.924,
    gem_5h_reset_secs: int = 4 * 3600 + 13 * 60,
    gem_wk_frac: float = 0.846,
    gem_wk_reset_secs: int = 5 * 86_400 + 19 * 3600,
    tp_5h_frac: float = 1.0,
    tp_5h_reset_time: str = "1970-01-01T00:00:00Z",
    tp_wk_frac: float = 1.0,
    tp_wk_reset_time: str = "1970-01-01T00:00:00Z",
    include_context: bool = False,
    plan_tier: str = "Google AI Ultra",
    email: str = "tester@example.com",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "plan_tier": plan_tier,
        "email": email,
        "model": {"display_name": "Gemini 3 Pro", "effort": "high"},
        "cycle_mode": "accept-edits",
        "quota_updated_at": now_ts,
        "quota": {
            "gemini-5h": {
                "remaining_fraction": gem_5h_frac,
                "reset_time": _iso_from_ts(now_ts + gem_5h_reset_secs),
                "reset_in_seconds": gem_5h_reset_secs,
            },
            "gemini-weekly": {
                "remaining_fraction": gem_wk_frac,
                "reset_time": _iso_from_ts(now_ts + gem_wk_reset_secs),
                "reset_in_seconds": gem_wk_reset_secs,
            },
            "3p-5h": {
                "remaining_fraction": tp_5h_frac,
                "reset_time": tp_5h_reset_time,
                "reset_in_seconds": 0,
            },
            "3p-weekly": {
                "remaining_fraction": tp_wk_frac,
                "reset_time": tp_wk_reset_time,
                "reset_in_seconds": 0,
            },
        },
    }
    if include_context:
        payload["context_window"] = {
            "total_input_tokens": 120_000,
            "total_output_tokens": 15_000,
            "context_window_size": 1_000_000,
            "used_percentage": 13.5,
            "remaining_percentage": 86.5,
            "current_usage": {"cache_read_input_tokens": 80_000},
        }
    return payload


class _FakeHTTPResponse:
    def __init__(self, body: dict[str, Any]) -> None:
        self._raw = json.dumps(body).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


def _isolate_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("AGY_QUOTA_FILE", raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.delenv("AW_GEMINI_QUOTA_CLIENT_ID", raising=False)
    monkeypatch.delenv("AW_GEMINI_QUOTA_CLIENT_SECRET", raising=False)
    return home


def test_bar_output_and_bucket_filtering(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    monkeypatch.setattr(gemini_quota.time, "time", lambda: now_ts)
    quota_file = tmp_path / "quota.json"
    quota_file.write_text(json.dumps(_sample_payload(now_ts)), encoding="utf-8")

    rc = gemini_quota.main(
        ["--file", str(quota_file), "--bar", "--no-color", "--max-staleness", "-1"]
    )
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert "\n" not in out
    assert "\033[" not in out
    assert "Gemini3Pro(High)" in out
    assert "Edit:Allowed" in out
    assert "Gem:" in out
    assert "Cld/GPT:" in out

    rc_gem = gemini_quota.main(
        [
            "--file",
            str(quota_file),
            "--bar",
            "--gemini",
            "--no-color",
            "--max-staleness",
            "-1",
        ]
    )
    assert rc_gem == 0
    out_gem = capsys.readouterr().out.strip()
    assert "Gem:" in out_gem
    assert "Cld/GPT:" not in out_gem

    rc_3p = gemini_quota.main(
        [
            "--file",
            str(quota_file),
            "--bar",
            "--3p",
            "--no-color",
            "--max-staleness",
            "-1",
        ]
    )
    assert rc_3p == 0
    out_3p = capsys.readouterr().out.strip()
    assert "Cld/GPT:" in out_3p
    assert "Gem:" not in out_3p


def test_json_output_includes_burn_forecast_and_respects_filters(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    monkeypatch.setattr(gemini_quota.time, "time", lambda: now_ts)
    quota_file = tmp_path / "quota.json"
    quota_file.write_text(json.dumps(_sample_payload(now_ts)), encoding="utf-8")

    rc = gemini_quota.main(
        ["--file", str(quota_file), "--json", "--max-staleness", "-1"]
    )
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "burn_forecast" in data
    assert set(data["burn_forecast"].keys()) == {
        "gemini-5h",
        "gemini-weekly",
        "3p-5h",
        "3p-weekly",
    }
    assert data["burn_forecast"]["3p-5h"]["status"] == "idle"
    assert (
        data["burn_forecast"]["3p-5h"]["remain_clock_seconds"]
        == gemini_quota.FIVE_HOUR_SECS
    )
    assert (
        data["burn_forecast"]["3p-weekly"]["remain_clock_seconds"]
        == gemini_quota.WEEKLY_SECS
    )

    rc_g = gemini_quota.main(
        ["--file", str(quota_file), "--json", "--gemini", "--max-staleness", "-1"]
    )
    assert rc_g == 0
    data_g = json.loads(capsys.readouterr().out)
    assert set(data_g["quota"].keys()) == {"gemini-5h", "gemini-weekly"}
    assert set(data_g["burn_forecast"].keys()) == {"gemini-5h", "gemini-weekly"}

    rc_3p = gemini_quota.main(
        ["--file", str(quota_file), "--json", "--3p", "--max-staleness", "-1"]
    )
    assert rc_3p == 0
    data_3p = json.loads(capsys.readouterr().out)
    assert set(data_3p["quota"].keys()) == {"3p-5h", "3p-weekly"}
    assert set(data_3p["burn_forecast"].keys()) == {"3p-5h", "3p-weekly"}


def test_dashboard_lower_table_layout_connected_borders_and_idle_clock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    monkeypatch.setattr(gemini_quota.time, "time", lambda: now_ts)

    # Provide two history samples 20 minutes apart so Gemini 5h has an exact 7.2%/hr live slope:
    # 94.8% -> 92.4% over 20 minutes = 2.4% / (1/3 hr) = 7.2%/hr -> secs_to_zero = 92.4/7.2 = 12.833h (12h50m)
    # reset_in = 4h13m -> remain_clock_seconds = 12h50m - 4h13m = +08h37m, proj_pct_at_reset ~= 62%
    payload = _sample_payload(
        now_ts, gem_5h_frac=0.924, gem_5h_reset_secs=4 * 3600 + 13 * 60
    )
    samples = [
        {
            "ts": now_ts - 1200.0,
            "quota": {
                "gemini-5h": {
                    "remaining_fraction": 0.948,
                    "reset_time": payload["quota"]["gemini-5h"]["reset_time"],
                }
            },
        },
        {
            "ts": now_ts,
            "quota": {
                "gemini-5h": {
                    "remaining_fraction": 0.924,
                    "reset_time": payload["quota"]["gemini-5h"]["reset_time"],
                }
            },
        },
    ]

    rendered = gemini_quota.render_dashboard(
        payload,
        Path("last_quota.json"),
        now_ts,
        color_enabled=False,
        watch_samples=samples,
    )
    box_lines = [line for line in rendered.splitlines() if line and line[0] in "╭├│╰"]
    assert (
        len(box_lines) == 13
    )  # top, u_hdr, 2 upper, div1, sub, div2, l_hdr, 4 lower, bot

    # Every box line must be exactly 92 visible characters wide
    for line in box_lines:
        width = gemini_quota.visible_width(line)
        assert width == 92, f"Bad width ({width}): {line!r}"

    div2 = box_lines[6]
    l_hdr = box_lines[7]
    bot = box_lines[-1]

    # Connected vertical separators align at exact columns 40 and 68
    t_down_positions = [i for i, ch in enumerate(div2) if ch == "┬"]
    t_up_positions = [i for i, ch in enumerate(bot) if ch == "┴"]
    assert t_down_positions == [40, 68]
    assert t_up_positions == [40, 68]
    for row in [l_hdr] + box_lines[8:-1]:
        assert row[40] == "│"
        assert row[68] == "│"

    assert "Burnout?" not in l_hdr
    assert "Estimated Time to Burnout" in l_hdr
    assert "Remain at reset" in l_hdr

    gem_5h_row = box_lines[8]
    tp_5h_row = box_lines[10]
    tp_wk_row = box_lines[11]

    assert "12h50m" in gem_5h_row
    assert "~62%" in gem_5h_row
    assert "08h37m" in gem_5h_row

    assert "∞" in tp_5h_row
    assert "100%" in tp_5h_row
    assert "05h00m" in tp_5h_row

    assert "∞" in tp_wk_row
    assert "100%" in tp_wk_row
    assert "7d 00h00m" in tp_wk_row


def test_abbreviate_timezone_caps_verbose_windows_names() -> None:
    assert gemini_quota._abbreviate_timezone("UTC") == "UTC"
    assert gemini_quota._abbreviate_timezone("EST") == "EST"
    assert gemini_quota._abbreviate_timezone("Coordinated Universal Time") == "UTC"
    assert gemini_quota._abbreviate_timezone("Greenwich Mean Time") == "GMT"
    assert gemini_quota._abbreviate_timezone("Eastern Standard Time") == "EST"
    assert gemini_quota._abbreviate_timezone("Pacific Daylight Time") == "PDT"
    assert len(gemini_quota._abbreviate_timezone("Central European Summer Time")) <= 5


def test_dashboard_negative_clock_on_burnout_and_exhausted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    monkeypatch.setattr(gemini_quota.time, "time", lambda: now_ts)

    # Case 1: Will burn out before reset: 30% remaining, burning at 20%/hr -> secs_to_zero = 1h30m, reset in 4h00m
    # delta = 1h30m - 4h00m = -02h30m
    payload = _sample_payload(now_ts, gem_5h_frac=0.30, gem_5h_reset_secs=4 * 3600)
    samples = [
        {
            "ts": now_ts - 1800.0,
            "quota": {
                "gemini-5h": {
                    "remaining_fraction": 0.40,
                    "reset_time": payload["quota"]["gemini-5h"]["reset_time"],
                }
            },
        },
        {
            "ts": now_ts,
            "quota": {
                "gemini-5h": {
                    "remaining_fraction": 0.30,
                    "reset_time": payload["quota"]["gemini-5h"]["reset_time"],
                }
            },
        },
    ]

    plain = gemini_quota.render_dashboard(
        payload, None, None, color_enabled=False, watch_samples=samples
    )
    colored = gemini_quota.render_dashboard(
        payload, None, None, color_enabled=True, watch_samples=samples
    )
    gem_line_plain = next(
        line for line in plain.splitlines() if line.startswith("│Gemini 5h")
    )
    gem_line_colored = next(
        line
        for line in colored.splitlines()
        if "Gemini" in line and "5h" in line and "0%" in line
    )
    assert "0%" in gem_line_plain
    assert "-02h30m" in gem_line_plain
    assert "\033[1;38;5;196m-02h30m\033[0m" in gem_line_colored

    # Case 2: Already exhausted (0% now, reset in 2h15m -> -02h15m)
    exhausted_payload = _sample_payload(
        now_ts, gem_5h_frac=0.0, gem_5h_reset_secs=2 * 3600 + 15 * 60
    )
    plain_ex = gemini_quota.render_dashboard(
        exhausted_payload, None, None, color_enabled=False, watch_samples=[]
    )
    ex_line = next(
        line for line in plain_ex.splitlines() if line.startswith("│Gemini 5h")
    )
    assert "EXHAUSTED (0% now)" in ex_line
    assert "0%" in ex_line
    assert "-02h15m" in ex_line


def test_remain_at_reset_color_thresholds() -> None:
    # Green up until 25% remaining
    assert gemini_quota.remain_at_reset_color_256(100) == "\033[1;38;5;46m"
    assert gemini_quota.remain_at_reset_color_256(50) == "\033[38;5;40m"
    assert gemini_quota.remain_at_reset_color_256(25) == "\033[38;5;76m"
    # Transition below 25% toward midpoint yellow at 15%
    assert gemini_quota.remain_at_reset_color_256(24) == "\033[38;5;112m"
    assert gemini_quota.remain_at_reset_color_256(15) == "\033[38;5;226m"
    # Transition below 15% to full red at 5% or less
    assert gemini_quota.remain_at_reset_color_256(6) == "\033[38;5;202m"
    assert gemini_quota.remain_at_reset_color_256(5) == "\033[38;5;196m"
    assert gemini_quota.remain_at_reset_color_256(1) == "\033[38;5;196m"
    assert gemini_quota.remain_at_reset_color_256(0) == "\033[1;38;5;196m"


def test_color_env_and_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)

    monkeypatch.setenv("NO_COLOR", "1")
    assert gemini_quota.supports_color() is False
    assert gemini_quota.supports_color(force_color_flag=True) is True

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert gemini_quota.supports_color() is True
    assert gemini_quota.supports_color(no_color_flag=True) is False

    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("TERM", "dumb")
    assert gemini_quota.supports_color() is False


def test_dashboard_filters_plot_and_context(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    home = _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    monkeypatch.setattr(gemini_quota.time, "time", lambda: now_ts)

    # Seed history so --plot renders Braille charts
    hist_path = home / ".gemini" / "antigravity-cli" / "quota_history.json"
    hist_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _sample_payload(now_ts, include_context=True)
    hist_path.write_text(
        json.dumps(
            {
                "samples": [
                    {
                        "ts": now_ts - 900.0,
                        "quota": {
                            "gemini-5h": {
                                "remaining_fraction": 0.96,
                                "reset_time": payload["quota"]["gemini-5h"][
                                    "reset_time"
                                ],
                            }
                        },
                    },
                    {
                        "ts": now_ts,
                        "quota": {
                            "gemini-5h": {
                                "remaining_fraction": 0.924,
                                "reset_time": payload["quota"]["gemini-5h"][
                                    "reset_time"
                                ],
                            }
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    f_with_ctx = tmp_path / "with_ctx.json"
    f_with_ctx.write_text(json.dumps(payload), encoding="utf-8")

    rc = gemini_quota.main(
        [
            "--file",
            str(f_with_ctx),
            "--plot",
            "--context",
            "--no-color",
            "--max-staleness",
            "-1",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Context Window Usage:" in out
    assert "13.5% used (120,000 input + 15,000 output of 1,000,000 tokens)" in out
    assert "Cache Read: 80,000 tokens" in out
    assert "5h Quota Trajectory & Forecast" in out
    assert "Live Burn Rate" in out

    # Without context_window in payload, --context omits the section silently
    f_no_ctx = tmp_path / "no_ctx.json"
    f_no_ctx.write_text(
        json.dumps(_sample_payload(now_ts, include_context=False)), encoding="utf-8"
    )
    rc2 = gemini_quota.main(
        ["--file", str(f_no_ctx), "--context", "--no-color", "--max-staleness", "-1"]
    )
    assert rc2 == 0
    out2 = capsys.readouterr().out
    assert "Context Window Usage:" not in out2

    # Dashboard --gemini and --3p filtering
    rc_g = gemini_quota.main(
        ["--file", str(f_no_ctx), "--gemini", "--no-color", "--max-staleness", "-1"]
    )
    assert rc_g == 0
    out_g = capsys.readouterr().out
    assert "Gemini 5h" in out_g
    assert "Claude/GPT" not in out_g

    rc_3p = gemini_quota.main(
        ["--file", str(f_no_ctx), "--3p", "--no-color", "--max-staleness", "-1"]
    )
    assert rc_3p == 0
    out_3p = capsys.readouterr().out
    assert "Claude/GPT 5h" in out_3p
    assert "Gemini 5h" not in out_3p


def test_watch_loop_bounded_termination_and_no_history_write_with_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    home = _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    monkeypatch.setattr(gemini_quota.time, "time", lambda: now_ts)

    quota_file = tmp_path / "watch_quota.json"
    quota_file.write_text(json.dumps(_sample_payload(now_ts)), encoding="utf-8")

    sleeps: list[float] = []

    def _fake_sleep(secs: float) -> None:
        sleeps.append(secs)
        if len(sleeps) >= 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(gemini_quota.time, "sleep", _fake_sleep)

    rc = gemini_quota.main(
        [
            "--file",
            str(quota_file),
            "--watch",
            "1.5",
            "--no-color",
            "--max-staleness",
            "-1",
        ]
    )
    assert rc == 0
    assert sleeps == [1.5, 1.5]
    out = capsys.readouterr().out
    assert out.count("\033[2J\033[H") == 2
    # Live HISTORY_PATH must NOT be written when --file is supplied
    assert not (home / ".gemini" / "antigravity-cli" / "quota_history.json").exists()


def test_missing_or_corrupt_file_fails_closed_without_fallback_or_history_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    home = _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0

    # Place a valid cache in DEFAULT_CACHE_PATHS to prove --file never falls back to it
    default_cache = home / ".gemini" / "antigravity-cli" / "last_quota.json"
    default_cache.parent.mkdir(parents=True, exist_ok=True)
    default_cache.write_text(json.dumps(_sample_payload(now_ts)), encoding="utf-8")

    refresh_called = False

    def _fail_if_called(*args: Any, **kwargs: Any) -> Any:
        nonlocal refresh_called
        refresh_called = True
        raise AssertionError("refresh_quota must not be called when --file is supplied")

    monkeypatch.setattr(gemini_quota, "refresh_quota", _fail_if_called)

    rc_missing = gemini_quota.main(
        ["--file", str(tmp_path / "does-not-exist.json"), "--max-staleness", "0"]
    )
    assert rc_missing == 1
    assert not refresh_called
    assert "Error:" in capsys.readouterr().err
    assert not (home / ".gemini" / "antigravity-cli" / "quota_history.json").exists()

    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not-json", encoding="utf-8")
    rc_corrupt = gemini_quota.main(["--file", str(corrupt), "--max-staleness", "0"])
    assert rc_corrupt == 1
    assert not refresh_called
    assert "Error:" in capsys.readouterr().err


def test_agy_quota_file_env_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    monkeypatch.setattr(gemini_quota.time, "time", lambda: now_ts)

    override_file = tmp_path / "override_quota.json"
    override_file.write_text(
        json.dumps(_sample_payload(now_ts, plan_tier="Override Tier")), encoding="utf-8"
    )
    monkeypatch.setenv("AGY_QUOTA_FILE", str(override_file))

    rc = gemini_quota.main(["--no-color", "--max-staleness", "-1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Override Tier" in out
    assert "override_quota.json" in out


def test_refresh_quota_primary_token_host_fallback_and_token_non_exposure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    home = _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    monkeypatch.setattr(gemini_quota.time, "time", lambda: now_ts)

    secret_token = "ya29.super-secret-access-token-do-not-expose"
    tok_file = home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
    tok_file.parent.mkdir(parents=True, exist_ok=True)
    future_expiry = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    ).isoformat()
    tok_file.write_text(
        json.dumps(
            {
                "token": {
                    "access_token": secret_token,
                    "refresh_token": "rt-secret",
                    "expiry": future_expiry,
                }
            }
        ),
        encoding="utf-8",
    )

    seen_urls: list[str] = []
    seen_headers: list[dict[str, str]] = []

    def _fake_urlopen(req: Any, timeout: float | None = None) -> _FakeHTTPResponse:
        assert timeout is not None and timeout > 0
        url = req.full_url
        seen_urls.append(url)
        seen_headers.append(dict(req.header_items()))
        if "daily-cloudcode-pa.googleapis.com" in url:
            raise urllib.error.HTTPError(
                url, 503, "Service Unavailable", hdrs=None, fp=io.BytesIO(b"")
            )  # type: ignore[arg-type]
        assert "cloudcode-pa.googleapis.com" in url
        return _FakeHTTPResponse(
            {
                "groups": [
                    {
                        "buckets": [
                            {
                                "bucketId": "gemini-5h",
                                "remainingFraction": 0.75,
                                "resetTime": _iso_from_ts(now_ts + 3 * 3600),
                            },
                            {
                                "bucketId": "3p-5h",
                                "remainingFraction": 1.0,
                                "resetTime": "1970-01-01T00:00:00Z",
                            },
                        ]
                    }
                ]
            }
        )

    monkeypatch.setattr(gemini_quota.urllib.request, "urlopen", _fake_urlopen)

    rc = gemini_quota.main(["--json", "--max-staleness", "0"])
    assert rc == 0
    captured = capsys.readouterr()
    assert len(seen_urls) == 2
    assert (
        seen_urls[0]
        == "https://daily-cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary"
    )
    assert (
        seen_urls[1]
        == "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary"
    )
    assert seen_headers[0]["Authorization"] == f"Bearer {secret_token}"

    data = json.loads(captured.out)
    assert data["quota"]["gemini-5h"]["remaining_fraction"] == pytest.approx(0.75)
    assert data["quota"]["gemini-5h"]["reset_in_seconds"] == 3 * 3600
    assert data["quota"]["3p-5h"]["remaining_fraction"] == pytest.approx(1.0)

    # Token must never leak into stdout, stderr, cache JSON, or history JSON
    assert secret_token not in captured.out
    assert secret_token not in captured.err
    assert "rt-secret" not in captured.out
    assert "rt-secret" not in captured.err
    cache_text = (home / ".gemini" / "antigravity-cli" / "last_quota.json").read_text(
        encoding="utf-8"
    )
    hist_text = (home / ".gemini" / "antigravity-cli" / "quota_history.json").read_text(
        encoding="utf-8"
    )
    assert secret_token not in cache_text
    assert secret_token not in hist_text


def test_expired_token_falls_back_to_cache_or_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    home = _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    monkeypatch.setattr(gemini_quota.time, "time", lambda: now_ts)

    tok_file = home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
    tok_file.parent.mkdir(parents=True, exist_ok=True)
    past_expiry = (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
    ).isoformat()
    tok_file.write_text(
        json.dumps(
            {
                "token": {
                    "access_token": "expired-tok-123",
                    "refresh_token": "rt-456",
                    "expiry": past_expiry,
                }
            }
        ),
        encoding="utf-8",
    )

    def _never_open(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError(
            "HTTP must not be called when token is expired and client env vars are unset"
        )

    monkeypatch.setattr(gemini_quota.urllib.request, "urlopen", _never_open)

    # Without cache -> exit 1 with actionable message and zero token leakage
    rc_no_cache = gemini_quota.main(["--max-staleness", "0"])
    assert rc_no_cache == 1
    err_no_cache = capsys.readouterr().err
    assert "token expired; run agy to renew it" in err_no_cache
    assert "expired-tok-123" not in err_no_cache
    assert "rt-456" not in err_no_cache

    # With stale cache -> warn on stderr and render cache (exit 0)
    cache_file = home / ".gemini" / "antigravity-cli" / "last_quota.json"
    cache_file.write_text(json.dumps(_sample_payload(now_ts - 600.0)), encoding="utf-8")
    rc_with_cache = gemini_quota.main(["--no-color", "--max-staleness", "60"])
    assert rc_with_cache == 0
    captured = capsys.readouterr()
    assert "token expired; run agy to renew it" in captured.err
    assert "Antigravity Quota & Credit Status" in captured.out
    assert "expired-tok-123" not in captured.out
    assert "expired-tok-123" not in captured.err


def test_env_gated_oauth_refresh_via_opencode_accounts_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    home = _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    monkeypatch.setattr(gemini_quota.time, "time", lambda: now_ts)

    # Only fallback OpenCode accounts file exists
    acc_file = home / ".config" / "opencode" / "antigravity-accounts.json"
    acc_file.parent.mkdir(parents=True, exist_ok=True)
    acc_file.write_text(
        json.dumps({"accounts": [{"refreshToken": "opencode-rt-secret"}]}),
        encoding="utf-8",
    )

    monkeypatch.setenv("AW_GEMINI_QUOTA_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("AW_GEMINI_QUOTA_CLIENT_SECRET", "test-client-secret")

    calls: list[str] = []

    def _fake_urlopen(req: Any, timeout: float | None = None) -> _FakeHTTPResponse:
        calls.append(req.full_url)
        if req.full_url == "https://oauth2.googleapis.com/token":
            body = req.data.decode("utf-8")
            assert "refresh_token=opencode-rt-secret" in body
            assert "client_id=test-client-id" in body
            assert "client_secret=test-client-secret" in body
            return _FakeHTTPResponse(
                {"access_token": "fresh-access-tok", "expires_in": 3600}
            )
        assert req.header_items()
        assert dict(req.header_items())["Authorization"] == "Bearer fresh-access-tok"
        return _FakeHTTPResponse(
            {
                "groups": [
                    {
                        "buckets": [
                            {
                                "bucketId": "gemini-5h",
                                "remainingFraction": 0.88,
                                "resetTime": _iso_from_ts(now_ts + 4 * 3600),
                            }
                        ]
                    }
                ]
            }
        )

    monkeypatch.setattr(gemini_quota.urllib.request, "urlopen", _fake_urlopen)

    rc = gemini_quota.main(["--json", "--max-staleness", "0"])
    assert rc == 0
    captured = capsys.readouterr()
    assert calls == [
        "https://oauth2.googleapis.com/token",
        "https://daily-cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary",
    ]
    data = json.loads(captured.out)
    assert data["quota"]["gemini-5h"]["remaining_fraction"] == pytest.approx(0.88)
    assert "fresh-access-tok" not in captured.out
    assert "opencode-rt-secret" not in captured.out
    assert "test-client-secret" not in captured.out


def test_history_pruning_6h_window_and_720_sample_cap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    hist_path = home / ".gemini" / "antigravity-cli" / "quota_history.json"
    hist_path.parent.mkdir(parents=True, exist_ok=True)

    # Seed 1 stale entry (>6h old) plus 725 valid recent entries spaced 10s apart
    samples: list[dict[str, Any]] = [
        {
            "ts": now_ts - gemini_quota.MAX_HISTORY_AGE_SECS - 300.0,
            "quota": {"gemini-5h": {"remaining_fraction": 1.0, "reset_time": ""}},
        }
    ]
    for i in range(725):
        ts_i = now_ts - (725 - i) * 10.0
        samples.append(
            {
                "ts": ts_i,
                "quota": {
                    "gemini-5h": {
                        "remaining_fraction": max(0.1, 1.0 - i * 0.0005),
                        "reset_time": "",
                    }
                },
            }
        )
    hist_path.write_text(json.dumps({"samples": samples}), encoding="utf-8")

    updated = gemini_quota.record_history_sample(
        now_ts,
        {
            "gemini-5h": {
                "remaining_fraction": 0.5,
                "reset_time": _iso_from_ts(now_ts + 3600),
            }
        },
        persist=True,
    )
    assert len(updated) == gemini_quota.MAX_HISTORY_SAMPLES
    assert all(
        float(s["ts"]) >= now_ts - gemini_quota.MAX_HISTORY_AGE_SECS for s in updated
    )
    assert updated[-1]["ts"] == now_ts

    reloaded = gemini_quota.load_history_samples(now_ts)
    assert len(reloaded) == gemini_quota.MAX_HISTORY_SAMPLES


def test_untrusted_payload_strings_are_sanitized(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _isolate_home(monkeypatch, tmp_path)
    now_ts = 1_764_250_000.0
    monkeypatch.setattr(gemini_quota.time, "time", lambda: now_ts)

    payload = _sample_payload(
        now_ts,
        plan_tier="Ultra\033[31mEvil\nTier",
        email="u\x07@example.com",
    )
    payload["model"] = {"display_name": "Gem\033[2JPro\r\n", "effort": "hi\x1b[32mgh"}

    bar = gemini_quota.format_single_status_bar(payload, color_enabled=False)
    assert "\033[" not in bar
    assert "\n" not in bar
    assert "\r" not in bar

    dash = gemini_quota.render_dashboard(
        payload, None, None, color_enabled=False, watch_samples=[]
    )
    assert "\033[" not in dash
    assert "\x07" not in dash
    for line in dash.splitlines():
        if line and line[0] in "╭├│╰":
            assert gemini_quota.visible_width(line) == 92

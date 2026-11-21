#!/usr/bin/env python3
"""Standalone, strictly de-identified profiling trace cache and bundle tool (`aw-profile`).

Extracts deep, analytically lossless, per-run behavioral traces from `aw [agy|oc] run`
directories into compact zstd-compressed JSON files (`.trace.json.zst`) with resume-safe
stat watermarks, portable `.tar.zst` packaging (`pack`), and fail-closed validated
aggregation (`ingest`) across multiple servers and external contributors.

Design posture:
- Self-contained CLI with zero coupling to `agent_workflows/cli.py`.
- Strictly de-identified (minimized): allowlist-only schema carrying numbers, booleans,
  timestamps, closed-vocabulary labels, normalized command families, and salted pseudonyms.
  Never includes prompts, source code, file contents, stdout/stderr text, raw paths,
  command arguments, git remotes, or usernames.
- Lossless for profiling: preserves every LLM step, every tool call, every attempt, every
  queue item, and every lifecycle/telemetry event without pre-aggregation.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import hmac
import io
import json
import math
import os
import platform
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from agent_workflows import platform_lock
from agent_workflows import term as _term_mod
from agent_workflows.run_analytics import (
    STARTUP_TIMING_METRIC_KEYS,
    extract_startup_timings,
)
from agent_workflows.run_dashboard import (
    _output_bytes,
    command_families,
    command_kind,
    tool_category,
)
from agent_workflows.verifier_corroboration import (
    AGY_TERMINAL_STATES,
    tool_call_from_event,
)

__all__ = [
    "TRACE_SCHEMA_VERSION",
    "EXTRACTOR_VERSION",
    "BUNDLE_SCHEMA_VERSION",
    "DEFAULT_CACHE_DIR",
    "ZstdUnavailableError",
    "zstd_compress",
    "zstd_decompress",
    "load_or_create_salt",
    "pseudonym",
    "compute_run_watermark",
    "discover_runs_from_runs_dir",
    "scan_runs_dirs",
    "extract_run_trace",
    "validate_trace",
    "collect_runs",
    "pack_traces",
    "ingest_bundles",
    "build_parser",
    "main",
]

TRACE_SCHEMA_VERSION: int = 1
EXTRACTOR_VERSION: int = 1
BUNDLE_SCHEMA_VERSION: int = 1
DEFAULT_ZSTD_LEVEL: int = 6
MAX_MEMBER_BYTES: int = 64 * 1024 * 1024  # 64 MiB uncompressed per trace member
MAX_BUNDLE_MEMBERS: int = 100_000
DEFAULT_CACHE_DIR: Path = Path("~/.aw/profile-cache")

_PRUNE_SCAN_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "worktrees",
        "analytics",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)

_SAFE_FILE_EXTS: frozenset[str] = frozenset(
    {
        ".py",
        ".md",
        ".json",
        ".jsonl",
        ".toml",
        ".yaml",
        ".yml",
        ".sh",
        ".bash",
        ".zsh",
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".jsx",
        ".css",
        ".html",
        ".txt",
        ".cfg",
        ".ini",
        ".sql",
        ".go",
        ".rs",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".java",
        ".rb",
        ".php",
        ".xml",
        ".csv",
        ".lock",
        ".mk",
    }
)

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
_PSEUDONYM_RE = re.compile(r"^[a-z][a-z0-9_-]{0,23}:[0-9a-f]{12,32}$")
_ISO_TS_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$"
)
_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+@/-]{0,63}$")
_CMD_FAMILY_RE = re.compile(r"^[A-Za-z0-9_.+-]+(?: [a-z][a-z0-9-]*){0,2}$")
_BATCH_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_STAMP_RE = re.compile(r"(\d{8})T(\d{6})")
_ATTEMPT_FILE_RE = re.compile(
    r"^(?:\d+-)?([a-z0-9]{6})-attempt-(\d+)(?:-(.+))?\.jsonl$", re.I
)
_DRIVE_PATH_RE = re.compile(r"^[A-Za-z]:[/\\]")

_LIVE_QUEUE_STATES: frozenset[str] = frozenset({"queued", "running", "interrupted", ""})

# --------------------------------------------------------------------------------------
# Zstandard codec (stdlib Python 3.14+ compression.zstd -> zstandard -> backports -> CLI)
# --------------------------------------------------------------------------------------


class ZstdUnavailableError(RuntimeError):
    """Raised when no zstandard backend is available on this Python interpreter."""


def zstd_compress(data: bytes, *, level: int = DEFAULT_ZSTD_LEVEL) -> bytes:
    """Compress bytes using zstandard (Python 3.14+ stdlib, library, or zstd CLI)."""
    try:
        from compression import zstd as _stdlib_zstd  # type: ignore[import-not-found]

        return bytes(_stdlib_zstd.compress(data, level=level))
    except ImportError:
        pass
    try:
        import zstandard as _zstd  # type: ignore[import-not-found]

        return bytes(_zstd.ZstdCompressor(level=level).compress(data))
    except ImportError:
        pass
    try:
        from backports import zstd as _bp_zstd  # type: ignore[import-not-found]

        return bytes(_bp_zstd.compress(data, level=level))
    except ImportError:
        pass
    zstd_bin = shutil.which("zstd")
    if zstd_bin:
        proc = subprocess.run(
            [zstd_bin, "-q", "-c", f"-{int(level)}"],
            input=data,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout
        raise ZstdUnavailableError(
            f"zstd CLI failed with exit {proc.returncode}: "
            f"{proc.stderr.decode('utf-8', errors='replace').strip()}"
        )
    raise ZstdUnavailableError(
        "zstandard compression requires Python 3.14+ (stdlib compression.zstd), "
        "the `zstandard` package (`pip install zstandard`), or the `zstd` CLI."
    )


def zstd_decompress(data: bytes) -> bytes:
    """Decompress zstandard-compressed bytes."""
    try:
        from compression import zstd as _stdlib_zstd  # type: ignore[import-not-found]

        return bytes(_stdlib_zstd.decompress(data))
    except ImportError:
        pass
    try:
        import zstandard as _zstd  # type: ignore[import-not-found]

        return bytes(_zstd.ZstdDecompressor().decompress(data))
    except ImportError:
        pass
    try:
        from backports import zstd as _bp_zstd  # type: ignore[import-not-found]

        return bytes(_bp_zstd.decompress(data))
    except ImportError:
        pass
    zstd_bin = shutil.which("zstd")
    if zstd_bin:
        proc = subprocess.run(
            [zstd_bin, "-d", "-q", "-c"],
            input=data,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout
        raise ZstdUnavailableError(
            f"zstd CLI decompress failed with exit {proc.returncode}: "
            f"{proc.stderr.decode('utf-8', errors='replace').strip()}"
        )
    raise ZstdUnavailableError(
        "zstandard decompression requires Python 3.14+ (stdlib compression.zstd), "
        "the `zstandard` package (`pip install zstandard`), or the `zstd` CLI."
    )


# --------------------------------------------------------------------------------------
# De-identification (salted HMAC pseudonyms)
# --------------------------------------------------------------------------------------


def load_or_create_salt(cache_dir: Path | str) -> str:
    """Load or create a per-cache random hex salt (mode 0600, never exported)."""
    root = Path(cache_dir).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    salt_path = root / "salt"
    if salt_path.is_file():
        existing = salt_path.read_text(encoding="utf-8").strip()
        if len(existing) >= 32:
            return existing
    salt = secrets.token_hex(32)
    fd, tmp_name = tempfile.mkstemp(prefix=".salt-", dir=str(root))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(salt + "\n")
        if os.name != "nt":
            os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, salt_path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return salt


def pseudonym(value: str, *, salt: str, domain: str) -> str:
    """Return a deterministic domain-scoped HMAC pseudonym (`<domain>:<16-hex>`)."""
    digest = hmac.new(
        salt.encode("utf-8"),
        f"{domain}\x00{value}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{domain}:{digest}"


def _machine_fingerprint() -> str:
    return f"{socket.gethostname()}|{platform.system()}|{platform.machine()}"


def _utc_now() -> str:
    return (
        _dt.datetime.now(_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _safe_ext(path_str: str | None) -> str:
    if not path_str:
        return ""
    ext = Path(str(path_str)).suffix.lower()
    return ext if ext in _SAFE_FILE_EXTS else ""


def _normalize_target_for_hash(path_str: str | None, repo_str: str | None) -> str:
    if not path_str:
        return ""
    text = str(path_str).replace("\\", "/").strip()
    if not text:
        return ""
    # Strip worktree prefix if present so the same file across lanes hashes identically.
    m = re.search(r"/\.aw/worktrees/[^/]+/", text)
    if m:
        return text[m.end() :]
    if repo_str:
        repo_norm = str(repo_str).replace("\\", "/").rstrip("/") + "/"
        if text.startswith(repo_norm):
            return text[len(repo_norm) :]
    return text


def _looks_like_path(text: str) -> bool:
    if not text:
        return False
    if text.startswith(("/", "~", "./", "../", "\\")):
        return True
    if _DRIVE_PATH_RE.match(text):
        return True
    if ".." in text.split("/") or "\\" in text:
        return True
    if text.count("/") >= 2:
        return True
    return False


# --------------------------------------------------------------------------------------
# Resume-safe stat watermark & discovery
# --------------------------------------------------------------------------------------


def _stat_file(path: Path) -> tuple[int, int]:
    try:
        st = path.stat()
        return (int(st.st_mtime_ns), int(st.st_size))
    except OSError:
        return (0, 0)


def _stat_dir_files(directory: Path, *, suffix: str = "") -> tuple[int, int, int]:
    """Return ``(count, max_mtime_ns, total_bytes)`` for files directly in ``directory``."""
    if not directory.is_dir():
        return (0, 0, 0)
    count = 0
    max_mtime = 0
    total_bytes = 0
    try:
        with os.scandir(directory) as it:
            for entry in it:
                if suffix and not entry.name.endswith(suffix):
                    continue
                try:
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    st = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                count += 1
                if st.st_mtime_ns > max_mtime:
                    max_mtime = int(st.st_mtime_ns)
                total_bytes += int(st.st_size)
    except OSError:
        return (0, 0, 0)
    return (count, max_mtime, total_bytes)


def compute_run_watermark(run_dir: Path | str) -> dict[str, int]:
    """Compute a resume-safe, stat-only freshness watermark for one run directory."""
    base = Path(run_dir)
    state_mtime, state_size = _stat_file(base / "state.json")
    events_mtime, events_size = _stat_file(base / "events.jsonl")
    ledger_mtime, ledger_size = _stat_file(base / "ledger.jsonl")
    sess_count, sess_mtime, sess_bytes = _stat_dir_files(
        base / "sessions", suffix=".jsonl"
    )
    out_count, out_mtime, _ = _stat_dir_files(base / "outcomes", suffix=".json")
    tel_count, tel_mtime, _ = _stat_dir_files(base / "telemetry")

    latest = max(
        state_mtime,
        events_mtime,
        ledger_mtime,
        sess_mtime,
        out_mtime,
        tel_mtime,
    )
    return {
        "extractor_version": EXTRACTOR_VERSION,
        "state_mtime_ns": state_mtime,
        "state_size": state_size,
        "events_mtime_ns": events_mtime,
        "events_size": events_size,
        "ledger_mtime_ns": ledger_mtime,
        "ledger_size": ledger_size,
        "sessions_count": sess_count,
        "sessions_max_mtime_ns": sess_mtime,
        "sessions_total_bytes": sess_bytes,
        "outcomes_count": out_count,
        "outcomes_max_mtime_ns": out_mtime,
        "telemetry_count": tel_count,
        "telemetry_max_mtime_ns": tel_mtime,
        "latest_mtime_ns": latest,
    }


def _run_is_locked(run_dir: Path) -> bool:
    lock_file = run_dir / "driver.lock"
    if not lock_file.exists():
        return False
    free = platform_lock.probe_free(lock_file)
    return free is not True


def _looks_like_analytics_dir(path: Path) -> bool:
    if path.name != "analytics" or not path.is_dir():
        return False
    return any(
        (path / marker).exists()
        for marker in ("cache", "snapshots", "versions", "manifest.json")
    )


def _is_in_analytics(path: Path) -> bool:
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        resolved = path
    return any(_looks_like_analytics_dir(p) for p in (resolved, *resolved.parents))


def _is_run_dir(path: Path) -> bool:
    return path.is_dir() and (
        (path / "state.json").is_file() or (path / "ledger.jsonl").is_file()
    )


def discover_runs_from_runs_dir(directory: Path | str) -> list[Path]:
    """Discover verified run directories from a runs dir, single run dir, or repo root."""
    p = Path(directory).expanduser()
    if not p.is_dir() or _is_in_analytics(p):
        return []
    if _is_run_dir(p):
        return [p]

    found: list[Path] = []
    seen: set[Path] = set()

    def _collect(parent: Path) -> None:
        if not parent.is_dir() or _is_in_analytics(parent):
            return
        try:
            children = sorted(parent.iterdir())
        except OSError:
            return
        for child in children:
            if (
                child.is_dir()
                and child.name.startswith("run-")
                and child.name != "analytics"
                and _is_run_dir(child)
            ):
                canon = child.resolve()
                if canon not in seen:
                    seen.add(canon)
                    found.append(child)

    _collect(p)
    for sub in (
        p / ".aw" / "records" / "runs",
        p / ".aw" / "runs",
        p / ".agents" / "runs",
    ):
        _collect(sub)
    return found


def scan_runs_dirs(
    root: Path | str,
    *,
    max_depth: int = 7,
    on_step: Callable[[int, int], None] | None = None,
) -> list[Path]:
    """Recursively discover verified `aw` run directories under ``root``.

    Follows a symlink passed directly as ``root`` (such as a symlinked workspace root),
    prunes `.git`, `worktrees`, `analytics`, `node_modules`, and `.venv`, and requires each
    matched `run-*` directory to contain `state.json` or `ledger.jsonl`.
    """
    start = Path(root).expanduser()
    if not start.exists() or not start.is_dir():
        return []
    # Resolve the root itself so a symlinked scan root is traversed cleanly,
    # while os.walk(..., followlinks=False) avoids symlink loops beneath it.
    root_real = start.resolve()
    if _is_in_analytics(root_real):
        return []
    if _is_run_dir(root_real):
        if on_step is not None:
            on_step(1, 1)
        return [root_real]

    found: list[Path] = []
    seen: set[Path] = set()
    root_depth = len(root_real.parts)
    dirs_walked = 0

    for dirpath, dirnames, _filenames in os.walk(root_real, followlinks=False):
        dirs_walked += 1
        cur = Path(dirpath)
        depth = len(cur.parts) - root_depth
        if depth >= max_depth:
            dirnames[:] = []
            if on_step is not None and dirs_walked % 25 == 0:
                on_step(dirs_walked, len(found))
            continue
        kept: list[str] = []
        for name in sorted(dirnames):
            if name in _PRUNE_SCAN_DIRS:
                continue
            child = cur / name
            if name.startswith("run-") and _is_run_dir(child):
                canon = child.resolve()
                if canon not in seen:
                    seen.add(canon)
                    found.append(child)
                # Never descend inside a run directory.
                continue
            kept.append(name)
        dirnames[:] = kept
        if on_step is not None and (dirs_walked % 25 == 0 or len(found) > 0):
            on_step(dirs_walked, len(found))
    if on_step is not None:
        on_step(dirs_walked, len(found))
    return found


# --------------------------------------------------------------------------------------
# Deep 6-table extraction (lossless behavioral + strictly de-identified)
# --------------------------------------------------------------------------------------


def _finite_float(val: Any) -> float | None:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return None
    f = float(val)
    if not math.isfinite(f):
        return None
    return f


def _finite_nonneg(val: Any) -> float | None:
    f = _finite_float(val)
    if f is None or f < 0.0:
        return None
    return f


def _parse_iso_epoch(raw: Any) -> float | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    try:
        dt = _dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_dt.timezone.utc)
        return dt.timestamp()
    except ValueError:
        return None


def _clean_iso(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if _ISO_TS_RE.match(text):
        return text
    return None


def _clean_label(raw: Any, *, default: str | None = None) -> str | None:
    if not isinstance(raw, str):
        return default
    text = raw.strip()
    if not text or _looks_like_path(text) or not _LABEL_RE.match(text):
        return default
    return text


def _classify_exit_reason(raw: Any, *, is_terminal: bool) -> str:
    if not raw:
        return "completed" if is_terminal else "unfinished"
    low = str(raw).lower()
    if "sigterm" in low or "sigint" in low or "interrupt" in low:
        return "interrupted"
    if "stopped" in low or "wind-down" in low:
        return "stopped"
    if "runaway" in low:
        return "runaway"
    if "error" in low or "fail" in low:
        return "error"
    return "other"


def _classify_tool_error(raw_error: Any, exit_code: int | None) -> str | None:
    if not raw_error and (exit_code is None or exit_code == 0):
        return None
    text = str(raw_error or "").lower()
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "permission" in text or "denied" in text or "eperm" in text:
        return "permission"
    if "not found" in text or "no such file" in text or "enoent" in text:
        return "not-found"
    if "hook" in text or "pre-commit" in text:
        return "hook-rejected"
    if "parse" in text or "syntax" in text or "json" in text:
        return "parse-error"
    if exit_code is not None and exit_code != 0:
        return "nonzero-exit"
    return "error"


def _infer_host(state: Mapping[str, Any], formats: Sequence[str]) -> str:
    drv = state.get("driver")
    if isinstance(drv, Mapping):
        did = str(drv.get("id") or "").lower()
        dpath = str(drv.get("path") or "").lower()
        if "agy" in did or "agy_runipd" in dpath:
            return "agy"
        if "oc" in did or "oc_runipd" in dpath:
            return "oc"
    for fmt in formats:
        if fmt in ("agy", "oc"):
            return fmt
    return "unknown"


def _infer_driver_name(state: Mapping[str, Any], host: str) -> str:
    drv = state.get("driver")
    if isinstance(drv, Mapping):
        did = _clean_label(drv.get("id"))
        if did:
            return did
        dpath = drv.get("path")
        if isinstance(dpath, str) and dpath.strip():
            stem = Path(dpath).stem
            cleaned = _clean_label(stem)
            if cleaned:
                return cleaned
    return f"{host}_runipd" if host in ("agy", "oc") else "unknown"


def _extract_toolkit_version(state: Mapping[str, Any]) -> str | None:
    git_rec = state.get("git")
    if isinstance(git_rec, Mapping):
        v = _clean_label(git_rec.get("toolkit_version") or git_rec.get("version"))
        if v:
            return v
    drv = state.get("driver")
    if isinstance(drv, Mapping):
        lc = drv.get("loaded_code")
        if isinstance(lc, list) and lc and isinstance(lc[0], Mapping):
            v = _clean_label(lc[0].get("version") or lc[0].get("commit"))
            if v:
                return v
    return None


def _infer_role_from_filename(filename: str) -> tuple[str | None, int | None, str]:
    m = _ATTEMPT_FILE_RE.match(filename)
    if not m:
        return (None, None, "other")
    id6 = m.group(1).lower()
    att_no = int(m.group(2))
    suffix = (m.group(3) or "").lower()
    if not suffix:
        role = "main"
    elif "verif" in suffix:
        role = "verify"
    elif "reask" in suffix or "defect" in suffix:
        role = "reask"
    elif "recover" in suffix:
        role = "recovery"
    elif "audit" in suffix:
        role = "audit"
    else:
        role = "other"
    return (id6, att_no, role)


def _parse_session_deep(
    session_path: Path,
    *,
    attempt_key: str,
    repo_str: str | None,
    salt: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse one `oc` or `agy` session JSONL into attempt summary, steps, and tool_calls."""
    fmt = "unknown"
    steps: list[dict[str, Any]] = []
    tool_calls: list[dict[str, Any]] = []

    read_file_ids: set[str] = set()
    edit_file_ids: set[str] = set()
    error_messages = 0
    thinking_in_output = False
    first_ts_ms: int | None = None
    last_ts_ms: int | None = None

    # OpenCode per-step tracking
    oc_step_idx = 0
    oc_step_start_ms: int | None = None
    oc_step_tool_calls = 0
    oc_step_tool_errors = 0

    # Antigravity per-step tracking
    agy_step_idx = 0
    call_idx = 0

    try:
        fh = open(session_path, "r", encoding="utf-8", errors="replace")
    except OSError:
        return (
            {
                "host_format": "unknown",
                "step_count": 0,
                "tool_call_count": 0,
                "tool_error_count": 0,
                "error_message_count": 0,
                "tokens_input": None,
                "tokens_output": None,
                "tokens_reasoning": None,
                "tokens_cache_read": None,
                "tokens_cache_write": None,
                "tokens_total": None,
                "cost_usd": None,
                "context_first": None,
                "context_last": None,
                "context_max": None,
                "llm_seconds": None,
                "tool_seconds": None,
                "tool_output_bytes": 0,
                "unique_files_read": 0,
                "unique_files_edited": 0,
                "thinking_in_output": False,
            },
            [],
            [],
        )

    tot_in = 0.0
    tot_out = 0.0
    tot_reason = 0.0
    tot_cread = 0.0
    tot_cwrite = 0.0
    has_tokens = False
    tot_cost = 0.0
    has_cost = False
    llm_seconds = 0.0
    has_llm_seconds = False
    tool_seconds = 0.0
    has_tool_seconds = False
    tool_output_bytes = 0
    ctx_first: float | None = None
    ctx_last: float | None = None
    ctx_max: float | None = None

    def _note_ctx(ctx: float) -> None:
        nonlocal ctx_first, ctx_last, ctx_max
        if ctx_first is None:
            ctx_first = ctx
        ctx_last = ctx
        if ctx_max is None or ctx > ctx_max:
            ctx_max = ctx

    def _append_tool_call(
        *,
        step_index: int,
        tool_name: str,
        is_error: bool,
        error_class: str | None,
        started_ms: int | None,
        ended_ms: int | None,
        duration_ms: float | None,
        command: str | None,
        path: str | None,
        in_bytes: int,
        out_bytes: int,
    ) -> None:
        nonlocal call_idx, tool_seconds, has_tool_seconds, tool_output_bytes
        call_idx += 1
        t_clean = _clean_label(tool_name, default="other") or "other"
        cat = tool_category(t_clean)
        cmd_k: str | None = None
        cmd_fams: list[str] = []
        if cat == "shell" and command is not None:
            cmd_k = command_kind(command)
            for fam in command_families(command):
                if _CMD_FAMILY_RE.match(fam) and not _looks_like_path(fam):
                    cmd_fams.append(fam)
        target_id: str | None = None
        f_ext: str | None = None
        if path:
            norm = _normalize_target_for_hash(path, repo_str)
            if norm:
                target_id = pseudonym(norm, salt=salt, domain="file")
                ext = _safe_ext(norm)
                f_ext = ext or None
                if cat == "read":
                    read_file_ids.add(target_id)
                elif cat in ("edit", "write"):
                    edit_file_ids.add(target_id)
        if duration_ms is not None and duration_ms >= 0.0:
            tool_seconds += duration_ms / 1000.0
            has_tool_seconds = True
        tool_output_bytes += max(0, out_bytes)

        rec: dict[str, Any] = {
            "attempt_key": attempt_key,
            "step_idx": step_index,
            "call_idx": call_idx,
            "tool_name": t_clean,
            "tool_category": cat,
            "is_error": bool(is_error),
            "input_bytes": max(0, int(in_bytes)),
            "output_bytes": max(0, int(out_bytes)),
        }
        if started_ms is not None:
            rec["started_ms"] = started_ms
        if ended_ms is not None:
            rec["ended_ms"] = ended_ms
        if duration_ms is not None:
            rec["duration_ms"] = round(max(0.0, duration_ms), 3)
        if cmd_k is not None:
            rec["cmd_kind"] = cmd_k
        if cmd_fams:
            rec["cmd_families"] = cmd_fams[:16]
        if error_class is not None:
            rec["error_class"] = error_class
        if target_id is not None:
            rec["target_file_id"] = target_id
        if f_ext is not None:
            rec["file_ext"] = f_ext
        tool_calls.append(rec)

    with fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line[0] != "{":
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if not isinstance(obj, dict):
                continue

            # OpenCode JSONL format
            if "type" in obj and "part" in obj:
                fmt = "oc"
                kind = obj.get("type")
                part = obj["part"] if isinstance(obj.get("part"), Mapping) else {}
                ts_raw = _finite_nonneg(obj.get("timestamp"))
                ts_ms = int(round(ts_raw)) if ts_raw is not None else None
                if ts_ms is not None:
                    if first_ts_ms is None or ts_ms < first_ts_ms:
                        first_ts_ms = ts_ms
                    if last_ts_ms is None or ts_ms > last_ts_ms:
                        last_ts_ms = ts_ms

                if kind == "step_start":
                    oc_step_idx += 1
                    oc_step_start_ms = ts_ms
                    oc_step_tool_calls = 0
                    oc_step_tool_errors = 0
                elif kind == "tool_use":
                    tc = tool_call_from_event(obj)
                    if tc is not None:
                        st = (
                            part.get("state")
                            if isinstance(part.get("state"), Mapping)
                            else {}
                        )
                        t_info = (
                            st.get("time")
                            if isinstance(st.get("time"), Mapping)
                            else {}
                        )
                        t_start = _finite_nonneg(t_info.get("start"))
                        t_end = _finite_nonneg(t_info.get("end"))
                        dur_ms = (
                            max(0.0, t_end - t_start)
                            if (t_start is not None and t_end is not None)
                            else (
                                round(tc.seconds * 1000.0, 3)
                                if tc.seconds and tc.seconds > 0
                                else None
                            )
                        )
                        meta = (
                            st.get("metadata")
                            if isinstance(st.get("metadata"), Mapping)
                            else {}
                        )
                        raw_exit = meta.get("exit")
                        exit_code = (
                            int(raw_exit)
                            if isinstance(raw_exit, int)
                            and not isinstance(raw_exit, bool)
                            else None
                        )
                        err_cls = (
                            _classify_tool_error(st.get("error"), exit_code)
                            if tc.error
                            else None
                        )
                        in_b = _output_bytes(st.get("input"))
                        out_b = _output_bytes(st.get("output")) + _output_bytes(
                            st.get("error")
                        )
                        step_for_call = max(1, oc_step_idx)
                        _append_tool_call(
                            step_index=step_for_call,
                            tool_name=tc.tool,
                            is_error=bool(tc.error),
                            error_class=err_cls,
                            started_ms=int(round(t_start))
                            if t_start is not None
                            else None,
                            ended_ms=int(round(t_end)) if t_end is not None else None,
                            duration_ms=dur_ms,
                            command=tc.command,
                            path=tc.path,
                            in_bytes=in_b,
                            out_bytes=out_b,
                        )
                        oc_step_tool_calls += 1
                        if tc.error:
                            oc_step_tool_errors += 1
                elif kind == "step_finish":
                    if oc_step_idx == 0:
                        oc_step_idx = 1
                    toks = (
                        part.get("tokens")
                        if isinstance(part.get("tokens"), Mapping)
                        else None
                    )
                    s_in = s_out = s_reason = s_cread = s_cwrite = None
                    s_ctx = None
                    if toks:
                        has_tokens = True
                        s_in = _finite_nonneg(toks.get("input")) or 0.0
                        s_out = _finite_nonneg(toks.get("output")) or 0.0
                        s_reason = _finite_nonneg(toks.get("reasoning")) or 0.0
                        cache = toks.get("cache")
                        if isinstance(cache, Mapping):
                            s_cread = _finite_nonneg(cache.get("read")) or 0.0
                            s_cwrite = _finite_nonneg(cache.get("write")) or 0.0
                        else:
                            s_cread = _finite_nonneg(cache) or 0.0
                            s_cwrite = 0.0
                        tot_in += s_in
                        tot_out += s_out
                        tot_reason += s_reason
                        tot_cread += s_cread
                        tot_cwrite += s_cwrite
                        s_ctx = s_in + s_cread + s_cwrite
                        _note_ctx(s_ctx)
                    s_cost = _finite_nonneg(part.get("cost"))
                    if s_cost is not None:
                        tot_cost += s_cost
                        has_cost = True
                    dur_ms = (
                        float(max(0, ts_ms - oc_step_start_ms))
                        if (ts_ms is not None and oc_step_start_ms is not None)
                        else None
                    )
                    step_rec: dict[str, Any] = {
                        "attempt_key": attempt_key,
                        "step_idx": oc_step_idx,
                        "tool_call_count": oc_step_tool_calls,
                        "tool_error_count": oc_step_tool_errors,
                    }
                    if oc_step_start_ms is not None:
                        step_rec["started_ms"] = oc_step_start_ms
                    if ts_ms is not None:
                        step_rec["ended_ms"] = ts_ms
                    if dur_ms is not None:
                        step_rec["duration_ms"] = round(dur_ms, 3)
                    if s_in is not None:
                        step_rec["tokens_input"] = int(round(s_in))
                    if s_out is not None:
                        step_rec["tokens_output"] = int(round(s_out))
                    if s_reason is not None:
                        step_rec["tokens_reasoning"] = int(round(s_reason))
                    if s_cread is not None:
                        step_rec["tokens_cache_read"] = int(round(s_cread))
                    if s_cwrite is not None:
                        step_rec["tokens_cache_write"] = int(round(s_cwrite))
                    if s_ctx is not None:
                        step_rec["context_size"] = int(round(s_ctx))
                    if s_cost is not None:
                        step_rec["cost_usd"] = round(s_cost, 6)
                    steps.append(step_rec)
                    oc_step_start_ms = None
                    oc_step_tool_calls = 0
                    oc_step_tool_errors = 0
                elif kind == "error":
                    error_messages += 1

            # Antigravity JSONL format
            elif "event" in obj:
                fmt = "agy"
                su = obj.get("step_update")
                if not isinstance(su, Mapping):
                    continue
                if su.get("state") not in AGY_TERMINAL_STATES:
                    continue
                stype = su.get("step_type")
                secs = _finite_nonneg(su.get("duration_seconds"))
                raw_si = su.get("step_index")
                if stype == "agent_response":
                    agy_step_idx += 1
                    step_num = (
                        int(raw_si)
                        if isinstance(raw_si, int) and not isinstance(raw_si, bool)
                        else agy_step_idx
                    )
                    if secs is not None:
                        llm_seconds += secs
                        has_llm_seconds = True
                    usage = (
                        su.get("usage")
                        if isinstance(su.get("usage"), Mapping)
                        else None
                    )
                    s_in = s_out = s_reason = s_cread = None
                    s_ctx = None
                    if usage:
                        has_tokens = True
                        thinking_in_output = True
                        s_reason = _finite_nonneg(usage.get("thinking_tokens")) or 0.0
                        s_in = _finite_nonneg(usage.get("input_tokens")) or 0.0
                        raw_out = _finite_nonneg(usage.get("output_tokens")) or 0.0
                        # Matches run_dashboard.py: Antigravity output_tokens includes thinking_tokens.
                        s_out = max(0.0, raw_out - s_reason)
                        s_cread = _finite_nonneg(usage.get("cache_read_tokens")) or 0.0
                        tot_in += s_in
                        tot_out += s_out
                        tot_reason += s_reason
                        tot_cread += s_cread
                        s_ctx = s_in + s_cread
                        _note_ctx(s_ctx)
                    step_rec = {
                        "attempt_key": attempt_key,
                        "step_idx": step_num,
                        "tool_call_count": 0,
                        "tool_error_count": 0,
                    }
                    if secs is not None:
                        step_rec["duration_ms"] = round(secs * 1000.0, 3)
                    if s_in is not None:
                        step_rec["tokens_input"] = int(round(s_in))
                    if s_out is not None:
                        step_rec["tokens_output"] = int(round(s_out))
                    if s_reason is not None:
                        step_rec["tokens_reasoning"] = int(round(s_reason))
                    if s_cread is not None:
                        step_rec["tokens_cache_read"] = int(round(s_cread))
                    if s_ctx is not None:
                        step_rec["context_size"] = int(round(s_ctx))
                    steps.append(step_rec)
                elif stype in ("tool", "subagent"):
                    tc = tool_call_from_event(obj)
                    if tc is not None:
                        info = (
                            su.get("tool_info")
                            if isinstance(su.get("tool_info"), Mapping)
                            else {}
                        )
                        dur_ms = (
                            round(secs * 1000.0, 3)
                            if secs is not None
                            else (
                                round(tc.seconds * 1000.0, 3)
                                if tc.seconds and tc.seconds > 0
                                else None
                            )
                        )
                        err_cls = (
                            _classify_tool_error(info.get("error"), None)
                            if tc.error
                            else None
                        )
                        step_num = (
                            int(raw_si)
                            if isinstance(raw_si, int) and not isinstance(raw_si, bool)
                            else max(1, agy_step_idx)
                        )
                        _append_tool_call(
                            step_index=step_num,
                            tool_name=tc.tool,
                            is_error=bool(tc.error),
                            error_class=err_cls,
                            started_ms=None,
                            ended_ms=None,
                            duration_ms=dur_ms,
                            command=tc.command,
                            path=tc.path,
                            in_bytes=_output_bytes(
                                info.get("parameters")
                                if info.get("parameters") is not None
                                else info.get("input")
                            ),
                            out_bytes=_output_bytes(info.get("output")),
                        )
                        if steps:
                            steps[-1]["tool_call_count"] += 1
                            if tc.error:
                                steps[-1]["tool_error_count"] += 1
                elif stype == "error_message":
                    error_messages += 1

    tok_total: int | None = None
    if has_tokens:
        tok_total = int(round(tot_in + tot_out + tot_reason + tot_cread + tot_cwrite))

    summary: dict[str, Any] = {
        "host_format": fmt,
        "step_count": len(steps),
        "tool_call_count": len(tool_calls),
        "tool_error_count": sum(1 for c in tool_calls if c["is_error"]),
        "error_message_count": error_messages,
        "tokens_input": int(round(tot_in)) if has_tokens else None,
        "tokens_output": int(round(tot_out)) if has_tokens else None,
        "tokens_reasoning": int(round(tot_reason)) if has_tokens else None,
        "tokens_cache_read": int(round(tot_cread)) if has_tokens else None,
        "tokens_cache_write": int(round(tot_cwrite)) if has_tokens else None,
        "tokens_total": tok_total,
        "cost_usd": round(tot_cost, 6) if has_cost else None,
        "context_first": int(round(ctx_first)) if ctx_first is not None else None,
        "context_last": int(round(ctx_last)) if ctx_last is not None else None,
        "context_max": int(round(ctx_max)) if ctx_max is not None else None,
        "llm_seconds": round(llm_seconds, 3) if has_llm_seconds else None,
        "tool_seconds": round(tool_seconds, 3) if has_tool_seconds else None,
        "tool_output_bytes": tool_output_bytes,
        "unique_files_read": len(read_file_ids),
        "unique_files_edited": len(edit_file_ids),
        "thinking_in_output": thinking_in_output,
        "_wall_from_ts": (
            round(max(0.0, (last_ts_ms - first_ts_ms) / 1000.0), 3)
            if (first_ts_ms is not None and last_ts_ms is not None)
            else None
        ),
    }
    return summary, steps, tool_calls


def _extract_driver_events(
    run_dir: Path,
    *,
    id6_to_item_idx: Mapping[str, int],
) -> tuple[list[dict[str, Any]], int, int]:
    """Extract allowlisted lifecycle and telemetry events. Returns ``(events, resume_count, restart_count)``."""
    out: list[dict[str, Any]] = []
    seq = 0
    resume_count = 0
    restart_count = 0

    events_path = run_dir / "events.jsonl"
    if events_path.is_file():
        try:
            with open(events_path, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line[0] != "{":
                        continue
                    try:
                        obj = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(obj, Mapping):
                        continue
                    ev_type = (
                        _clean_label(obj.get("event"), default="unknown") or "unknown"
                    )
                    if (
                        ev_type == "run-startup-timings"
                        and obj.get("invocation_kind") == "resume"
                    ):
                        resume_count += 1
                    elif ev_type == "driver-restarted":
                        restart_count += 1
                    seq += 1
                    rec: dict[str, Any] = {
                        "seq": seq,
                        "source": "events",
                        "event_type": ev_type,
                    }
                    at = _clean_iso(obj.get("at"))
                    if at:
                        rec["at"] = at
                    raw_id6 = obj.get("id6")
                    if isinstance(raw_id6, str) and raw_id6.lower() in id6_to_item_idx:
                        rec["item_idx"] = id6_to_item_idx[raw_id6.lower()]
                    att_n = obj.get("attempt")
                    if isinstance(att_n, int) and not isinstance(att_n, bool):
                        rec["attempt_no"] = att_n
                    dur_s = _finite_nonneg(
                        obj.get("duration_seconds")
                        if obj.get("duration_seconds") is not None
                        else obj.get("elapsed_seconds")
                    )
                    if dur_s is not None:
                        rec["duration_ms"] = round(dur_s * 1000.0, 3)
                    lvl = obj.get("level")
                    if isinstance(lvl, int) and not isinstance(lvl, bool):
                        rec["stop_level"] = lvl
                    out.append(rec)
        except OSError:
            pass

    tel_dir = run_dir / "telemetry"
    if tel_dir.is_dir():
        for tel_file in sorted(tel_dir.glob("*.jsonl")):
            try:
                with open(tel_file, "r", encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line or line[0] != "{":
                            continue
                        try:
                            obj = json.loads(line)
                        except ValueError:
                            continue
                        if not isinstance(obj, Mapping):
                            continue
                        ev_type = (
                            _clean_label(
                                obj.get("event") or obj.get("kind"), default="sample"
                            )
                            or "sample"
                        )
                        seq += 1
                        rec = {
                            "seq": seq,
                            "source": "telemetry",
                            "event_type": ev_type,
                        }
                        at = _clean_iso(obj.get("at") or obj.get("timestamp"))
                        if at:
                            rec["at"] = at
                        dur_s = _finite_nonneg(obj.get("duration_seconds"))
                        if dur_s is not None:
                            rec["duration_ms"] = round(dur_s * 1000.0, 3)
                        cpu = _finite_nonneg(obj.get("cpu_seconds"))
                        if cpu is not None:
                            rec["cpu_seconds"] = round(cpu, 4)
                        rss = _finite_nonneg(obj.get("max_rss_bytes"))
                        if rss is not None:
                            rec["max_rss_bytes"] = int(round(rss))
                        load = _finite_nonneg(obj.get("load_average"))
                        if load is not None:
                            rec["load_avg"] = round(load, 4)
                        out.append(rec)
            except OSError:
                continue
    return out, resume_count, restart_count


def _extract_startup_dict(raw: Mapping[str, Any] | None) -> dict[str, float]:
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, float] = {}
    for key in STARTUP_TIMING_METRIC_KEYS:
        val = _finite_nonneg(raw.get(key))
        if val is not None:
            out[key] = round(val, 6)
    return out


def extract_run_trace(
    run_dir: Path | str,
    *,
    salt: str,
    watermark: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    """Extract a complete, strictly de-identified 6-table trace for one run directory."""
    base = Path(run_dir).expanduser()
    wm = dict(watermark) if watermark is not None else compute_run_watermark(base)

    state: dict[str, Any] = {}
    state_path = base / "state.json"
    if state_path.is_file():
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                state = loaded
        except (OSError, ValueError):
            state = {}

    run_id = str(state.get("run_id") or base.name).strip() or base.name
    if not _RUN_ID_RE.match(run_id):
        run_id = pseudonym(run_id, salt=salt, domain="run")

    repo_str = str(state.get("repo") or "") or None
    parent_resolved = str(base.parent.expanduser().resolve())
    machine_fp = _machine_fingerprint()
    source_id = pseudonym(f"{machine_fp}|{parent_resolved}", salt=salt, domain="src")
    machine_id = pseudonym(machine_fp, salt=salt, domain="host")
    repo_id = pseudonym(repo_str or parent_resolved, salt=salt, domain="repo")

    queue_raw = state.get("queue")
    queue: list[Mapping[str, Any]] = (
        [q for q in queue_raw if isinstance(q, Mapping)]
        if isinstance(queue_raw, list)
        else []
    )
    is_terminal = (
        bool(queue)
        and all(
            str(q.get("status") or "").strip().lower() not in _LIVE_QUEUE_STATES
            for q in queue
        )
        and not _run_is_locked(base)
    )

    options = state.get("options") if isinstance(state.get("options"), Mapping) else {}
    run_model = _clean_label(options.get("model"))
    run_variant = _clean_label(options.get("variant"))
    review_mode = _clean_label(options.get("review_mode"))

    # Discover all session logs on disk so unlinked ones (reask/verify/recovery) are never dropped.
    sessions_dir = base / "sessions"
    session_files: dict[str, Path] = {}
    if sessions_dir.is_dir():
        for sf in sorted(sessions_dir.glob("*.jsonl")):
            session_files[sf.name] = sf
    claimed_sessions: set[str] = set()

    items: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    all_steps: list[dict[str, Any]] = []
    all_tool_calls: list[dict[str, Any]] = []
    seen_formats: list[str] = []
    id6_to_item_idx: dict[str, int] = {}

    for item_idx, item in enumerate(queue, start=1):
        raw_id6 = str(item.get("id6") or f"item-{item_idx}").strip().lower()
        id6_to_item_idx[raw_id6] = item_idx
        raw_setid = str(item.get("setid") or "").strip()
        deps = item.get("dependencies")
        dep_count = len(deps) if isinstance(deps, list) else 0
        raw_attempts = (
            [a for a in item.get("attempts", []) if isinstance(a, Mapping)]
            if isinstance(item.get("attempts"), list)
            else []
        )
        refusal = item.get("refusal")
        refusal_code = (
            _clean_label(refusal.get("code"))
            if isinstance(refusal, Mapping)
            else _clean_label(item.get("refusal_code"))
        )
        raw_order = item.get("order")
        order_int = (
            int(raw_order)
            if isinstance(raw_order, int) and not isinstance(raw_order, bool)
            else None
        )
        item_rec: dict[str, Any] = {
            "item_idx": item_idx,
            "item_id": pseudonym(raw_id6, salt=salt, domain="item"),
            "set_id": pseudonym(raw_setid, salt=salt, domain="set")
            if raw_setid
            else None,
            "order": order_int,
            "entry_type": _clean_label(
                item.get("entry_type") or item.get("kind"), default="ipd"
            ),
            "action": _clean_label(item.get("action"), default="execute"),
            "dep_count": dep_count,
            "status": _clean_label(item.get("status"), default="unknown"),
            "disposition": _clean_label(item.get("disposition")),
            "readiness": _clean_label(item.get("readiness")),
            "verification": _clean_label(
                item.get("verification_verdict") or item.get("verification")
            ),
            "refusal_code": refusal_code,
            "landed": bool(item.get("landed"))
            if isinstance(item.get("landed"), bool)
            else None,
            "attempt_count": len(raw_attempts),
            "retry_count": max(0, len(raw_attempts) - 1),
            "zero_work_retries": int(item.get("zero_work_retries") or 0)
            if isinstance(item.get("zero_work_retries"), int)
            and not isinstance(item.get("zero_work_retries"), bool)
            else 0,
            "reask_count": int(item.get("reask_count") or 0)
            if isinstance(item.get("reask_count"), int)
            and not isinstance(item.get("reask_count"), bool)
            else 0,
        }
        items.append({k: v for k, v in item_rec.items() if v is not None})

        for a_pos, att in enumerate(raw_attempts, start=1):
            raw_num = att.get("number")
            att_no = (
                int(raw_num)
                if isinstance(raw_num, int) and not isinstance(raw_num, bool)
                else a_pos
            )
            role_logs: list[tuple[str, str | None]] = [
                ("main", str(att.get("log") or "") or None),
            ]
            if att.get("verify_log"):
                role_logs.append(("verify", str(att.get("verify_log"))))

            for role, log_ref in role_logs:
                attempt_key = f"{item_idx}:{att_no}:{role}"
                sf_path: Path | None = None
                if log_ref:
                    lname = Path(log_ref).name
                    if lname in session_files:
                        sf_path = session_files[lname]
                        claimed_sessions.add(lname)
                if sf_path is not None:
                    sess_sum, sess_steps, sess_tools = _parse_session_deep(
                        sf_path,
                        attempt_key=attempt_key,
                        repo_str=repo_str,
                        salt=salt,
                    )
                    seen_formats.append(str(sess_sum["host_format"]))
                    all_steps.extend(sess_steps)
                    all_tool_calls.extend(sess_tools)
                else:
                    sess_sum = {
                        "host_format": "state-only",
                        "step_count": 0,
                        "tool_call_count": 0,
                        "tool_error_count": 0,
                        "error_message_count": 0,
                        "tokens_input": None,
                        "tokens_output": None,
                        "tokens_reasoning": None,
                        "tokens_cache_read": None,
                        "tokens_cache_write": None,
                        "tokens_total": None,
                        "cost_usd": None,
                        "context_first": None,
                        "context_last": None,
                        "context_max": None,
                        "llm_seconds": None,
                        "tool_seconds": None,
                        "tool_output_bytes": 0,
                        "unique_files_read": 0,
                        "unique_files_edited": 0,
                        "thinking_in_output": False,
                        "_wall_from_ts": None,
                    }

                # Fill state-recorded tokens/cost when session log had none.
                tok_field = "verify_tokens" if role == "verify" else "tokens"
                cost_field = "verify_cost" if role == "verify" else "cost"
                if sess_sum["tokens_total"] is None and isinstance(
                    att.get(tok_field), Mapping
                ):
                    st_toks = att[tok_field]
                    t_in = _finite_nonneg(st_toks.get("input"))
                    t_out = _finite_nonneg(st_toks.get("output"))
                    t_reas = _finite_nonneg(st_toks.get("reasoning"))
                    t_cr = _finite_nonneg(st_toks.get("cache_read"))
                    t_cw = _finite_nonneg(st_toks.get("cache_write"))
                    t_tot = _finite_nonneg(st_toks.get("total"))
                    if t_in is not None:
                        sess_sum["tokens_input"] = int(round(t_in))
                    if t_out is not None:
                        sess_sum["tokens_output"] = int(round(t_out))
                    if t_reas is not None:
                        sess_sum["tokens_reasoning"] = int(round(t_reas))
                    if t_cr is not None:
                        sess_sum["tokens_cache_read"] = int(round(t_cr))
                    if t_cw is not None:
                        sess_sum["tokens_cache_write"] = int(round(t_cw))
                    if t_tot is not None:
                        sess_sum["tokens_total"] = int(round(t_tot))
                if sess_sum["cost_usd"] is None:
                    sc = _finite_nonneg(att.get(cost_field))
                    if sc is not None:
                        sess_sum["cost_usd"] = round(sc, 6)

                started_at = (
                    _clean_iso(att.get("started_at")) if role == "main" else None
                )
                ended_at = _clean_iso(att.get("ended_at")) if role == "main" else None
                s_ep = _parse_iso_epoch(started_at)
                e_ep = _parse_iso_epoch(ended_at)
                wall_s = (
                    round(max(0.0, e_ep - s_ep), 3)
                    if (s_ep is not None and e_ep is not None)
                    else sess_sum.get("_wall_from_ts")
                )
                att_model = (
                    _clean_label(
                        att.get("verify_model" if role == "verify" else "model")
                    )
                    or run_model
                )
                raw_ec = att.get("exit_code")
                exit_code = (
                    int(raw_ec)
                    if isinstance(raw_ec, int) and not isinstance(raw_ec, bool)
                    else None
                )
                att_rec: dict[str, Any] = {
                    "attempt_key": attempt_key,
                    "item_idx": item_idx,
                    "attempt_no": att_no,
                    "role": role,
                    "host_format": sess_sum["host_format"],
                    "model": att_model,
                    "model_variant": _clean_label(att.get("variant")) or run_variant,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "wall_seconds": wall_s,
                    "exit_code": exit_code,
                    "recovery": bool(att.get("recovery", False)),
                    "stalled": bool(att.get("stalled", False)),
                    "hit_turn_ceiling": bool(att.get("hit_turn_ceiling", False)),
                    "step_count": sess_sum["step_count"],
                    "tool_call_count": sess_sum["tool_call_count"],
                    "tool_error_count": sess_sum["tool_error_count"],
                    "error_message_count": sess_sum["error_message_count"],
                    "tokens_input": sess_sum["tokens_input"],
                    "tokens_output": sess_sum["tokens_output"],
                    "tokens_reasoning": sess_sum["tokens_reasoning"],
                    "tokens_cache_read": sess_sum["tokens_cache_read"],
                    "tokens_cache_write": sess_sum["tokens_cache_write"],
                    "tokens_total": sess_sum["tokens_total"],
                    "cost_usd": sess_sum["cost_usd"],
                    "context_first": sess_sum["context_first"],
                    "context_last": sess_sum["context_last"],
                    "context_max": sess_sum["context_max"],
                    "llm_seconds": sess_sum["llm_seconds"],
                    "tool_seconds": sess_sum["tool_seconds"],
                    "tool_output_bytes": sess_sum["tool_output_bytes"],
                    "unique_files_read": sess_sum["unique_files_read"],
                    "unique_files_edited": sess_sum["unique_files_edited"],
                    "thinking_in_output": sess_sum["thinking_in_output"],
                }
                attempts.append({k: v for k, v in att_rec.items() if v is not None})

    # Include any unclaimed session logs (e.g. reask/verification/carrier sessions).
    unlinked_idx = 0
    for sname, spath in sorted(session_files.items()):
        if sname in claimed_sessions:
            continue
        unlinked_idx += 1
        id6_guess, att_guess, role_guess = _infer_role_from_filename(sname)
        mapped_item_idx = id6_to_item_idx.get(id6_guess) if id6_guess else None
        attempt_key = f"unlinked:{unlinked_idx}:{role_guess}"
        sess_sum, sess_steps, sess_tools = _parse_session_deep(
            spath,
            attempt_key=attempt_key,
            repo_str=repo_str,
            salt=salt,
        )
        seen_formats.append(str(sess_sum["host_format"]))
        all_steps.extend(sess_steps)
        all_tool_calls.extend(sess_tools)
        att_rec = {
            "attempt_key": attempt_key,
            "item_idx": mapped_item_idx,
            "attempt_no": att_guess,
            "role": role_guess,
            "host_format": sess_sum["host_format"],
            "model": run_model,
            "model_variant": run_variant,
            "wall_seconds": sess_sum.get("_wall_from_ts"),
            "recovery": role_guess == "recovery",
            "stalled": False,
            "hit_turn_ceiling": False,
            "step_count": sess_sum["step_count"],
            "tool_call_count": sess_sum["tool_call_count"],
            "tool_error_count": sess_sum["tool_error_count"],
            "error_message_count": sess_sum["error_message_count"],
            "tokens_input": sess_sum["tokens_input"],
            "tokens_output": sess_sum["tokens_output"],
            "tokens_reasoning": sess_sum["tokens_reasoning"],
            "tokens_cache_read": sess_sum["tokens_cache_read"],
            "tokens_cache_write": sess_sum["tokens_cache_write"],
            "tokens_total": sess_sum["tokens_total"],
            "cost_usd": sess_sum["cost_usd"],
            "context_first": sess_sum["context_first"],
            "context_last": sess_sum["context_last"],
            "context_max": sess_sum["context_max"],
            "llm_seconds": sess_sum["llm_seconds"],
            "tool_seconds": sess_sum["tool_seconds"],
            "tool_output_bytes": sess_sum["tool_output_bytes"],
            "unique_files_read": sess_sum["unique_files_read"],
            "unique_files_edited": sess_sum["unique_files_edited"],
            "thinking_in_output": sess_sum["thinking_in_output"],
        }
        attempts.append({k: v for k, v in att_rec.items() if v is not None})

    driver_events, resume_ev_count, restart_count = _extract_driver_events(
        base, id6_to_item_idx=id6_to_item_idx
    )

    host = _infer_host(state, seen_formats)
    driver_name = _infer_driver_name(state, host)
    created_at = _clean_iso(state.get("created_at"))
    updated_at = _clean_iso(state.get("updated_at"))
    c_ep = _parse_iso_epoch(created_at)
    u_ep = _parse_iso_epoch(updated_at)
    run_wall_s = (
        round(max(0.0, u_ep - c_ep), 3)
        if (c_ep is not None and u_ep is not None)
        else None
    )

    startup_timings = extract_startup_timings(state, base / "events.jsonl")
    resume_timings_raw = state.get("resume_startup_timings")
    resume_timings: list[dict[str, float]] = []
    if isinstance(resume_timings_raw, list):
        for entry in resume_timings_raw:
            cleaned_rt = _extract_startup_dict(entry)
            if cleaned_rt:
                resume_timings.append(cleaned_rt)

    policy: dict[str, Any] = {}
    for bkey in ("isolate_execute", "isolate_review", "full_auto"):
        if isinstance(options.get(bkey), bool):
            policy[bkey] = options[bkey]
    for nkey in (
        "retry_budget",
        "stall_timeout",
        "turn_ceiling",
        "max_items_per_session",
    ):
        nv = _finite_nonneg(options.get(nkey))
        if nv is not None:
            policy[nkey] = int(nv) if nv.is_integer() else round(nv, 3)

    run_rec: dict[str, Any] = {
        "run_id": run_id,
        "source_id": source_id,
        "machine_id": machine_id,
        "repo_id": repo_id,
        "host": host,
        "driver": driver_name,
        "toolkit_version": _extract_toolkit_version(state),
        "model": run_model,
        "model_variant": run_variant,
        "review_mode": review_mode,
        "is_terminal": is_terminal,
        "exit_reason_class": _classify_exit_reason(
            state.get("exit_reason"), is_terminal=is_terminal
        ),
        "created_at": created_at,
        "updated_at": updated_at,
        "wall_seconds": run_wall_s,
        "queue_len": len(queue),
        "resume_count": max(resume_ev_count, len(resume_timings)),
        "driver_restart_count": restart_count,
        "os_name": _clean_label(platform.system().lower(), default="unknown"),
        "arch": _clean_label(platform.machine().lower(), default="unknown"),
        "cpu_count": os.cpu_count() or 0,
    }
    if policy:
        run_rec["policy"] = policy
    if startup_timings:
        run_rec["startup_timings"] = startup_timings
    if resume_timings:
        run_rec["resume_startup_timings"] = resume_timings

    trace: dict[str, Any] = {
        "schema_version": TRACE_SCHEMA_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "extracted_at": _utc_now(),
        "watermark": wm,
        "run": {k: v for k, v in run_rec.items() if v is not None},
        "items": items,
        "attempts": attempts,
        "steps": all_steps,
        "tool_calls": all_tool_calls,
        "driver_events": driver_events,
    }
    return trace


# --------------------------------------------------------------------------------------
# Strict allowlist validator (de-identified schema enforcement)
# --------------------------------------------------------------------------------------

_TOP_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "extractor_version",
        "extracted_at",
        "watermark",
        "run",
        "items",
        "attempts",
        "steps",
        "tool_calls",
        "driver_events",
        "source_batch",
    }
)
_WATERMARK_KEYS: frozenset[str] = frozenset(
    {
        "extractor_version",
        "state_mtime_ns",
        "state_size",
        "events_mtime_ns",
        "events_size",
        "ledger_mtime_ns",
        "ledger_size",
        "sessions_count",
        "sessions_max_mtime_ns",
        "sessions_total_bytes",
        "outcomes_count",
        "outcomes_max_mtime_ns",
        "telemetry_count",
        "telemetry_max_mtime_ns",
        "latest_mtime_ns",
    }
)
_RUN_KEYS: frozenset[str] = frozenset(
    {
        "run_id",
        "source_id",
        "machine_id",
        "repo_id",
        "host",
        "driver",
        "toolkit_version",
        "model",
        "model_variant",
        "review_mode",
        "is_terminal",
        "exit_reason_class",
        "created_at",
        "updated_at",
        "wall_seconds",
        "queue_len",
        "resume_count",
        "driver_restart_count",
        "os_name",
        "arch",
        "cpu_count",
        "policy",
        "startup_timings",
        "resume_startup_timings",
    }
)
_POLICY_KEYS: frozenset[str] = frozenset(
    {
        "isolate_execute",
        "isolate_review",
        "full_auto",
        "retry_budget",
        "stall_timeout",
        "turn_ceiling",
        "max_items_per_session",
    }
)
_STARTUP_KEY_SET: frozenset[str] = frozenset(STARTUP_TIMING_METRIC_KEYS)
_ITEM_KEYS: frozenset[str] = frozenset(
    {
        "item_idx",
        "item_id",
        "set_id",
        "order",
        "entry_type",
        "action",
        "dep_count",
        "status",
        "disposition",
        "readiness",
        "verification",
        "refusal_code",
        "landed",
        "attempt_count",
        "retry_count",
        "zero_work_retries",
        "reask_count",
    }
)
_ATTEMPT_KEYS: frozenset[str] = frozenset(
    {
        "attempt_key",
        "item_idx",
        "attempt_no",
        "role",
        "host_format",
        "model",
        "model_variant",
        "started_at",
        "ended_at",
        "wall_seconds",
        "exit_code",
        "recovery",
        "stalled",
        "hit_turn_ceiling",
        "step_count",
        "tool_call_count",
        "tool_error_count",
        "error_message_count",
        "tokens_input",
        "tokens_output",
        "tokens_reasoning",
        "tokens_cache_read",
        "tokens_cache_write",
        "tokens_total",
        "cost_usd",
        "context_first",
        "context_last",
        "context_max",
        "llm_seconds",
        "tool_seconds",
        "tool_output_bytes",
        "unique_files_read",
        "unique_files_edited",
        "thinking_in_output",
    }
)
_STEP_KEYS: frozenset[str] = frozenset(
    {
        "attempt_key",
        "step_idx",
        "started_ms",
        "ended_ms",
        "duration_ms",
        "tokens_input",
        "tokens_output",
        "tokens_reasoning",
        "tokens_cache_read",
        "tokens_cache_write",
        "context_size",
        "cost_usd",
        "tool_call_count",
        "tool_error_count",
    }
)
_TOOL_CALL_KEYS: frozenset[str] = frozenset(
    {
        "attempt_key",
        "step_idx",
        "call_idx",
        "started_ms",
        "ended_ms",
        "duration_ms",
        "tool_name",
        "tool_category",
        "cmd_kind",
        "cmd_families",
        "is_error",
        "error_class",
        "input_bytes",
        "output_bytes",
        "target_file_id",
        "file_ext",
    }
)
_DRIVER_EVENT_KEYS: frozenset[str] = frozenset(
    {
        "seq",
        "at",
        "source",
        "event_type",
        "item_idx",
        "attempt_no",
        "duration_ms",
        "cpu_seconds",
        "max_rss_bytes",
        "load_avg",
        "stop_level",
    }
)

_PSEUDONYM_ONLY_KEYS: frozenset[str] = frozenset(
    {"source_id", "machine_id", "repo_id", "item_id", "set_id", "target_file_id"}
)
_ISO_ONLY_KEYS: frozenset[str] = frozenset(
    {"extracted_at", "created_at", "updated_at", "started_at", "ended_at", "at"}
)


def _validate_scalar(where: str, key: str, value: Any, errors: list[str]) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            errors.append(f"{where}.{key}: non-finite number")
        return
    if not isinstance(value, str):
        errors.append(f"{where}.{key}: disallowed type {type(value).__name__}")
        return
    if "\n" in value or "\r" in value or len(value) > 120:
        errors.append(f"{where}.{key}: string too long or multi-line")
        return
    if key in _PSEUDONYM_ONLY_KEYS:
        if not _PSEUDONYM_RE.match(value):
            errors.append(f"{where}.{key}: must be a salted pseudonym")
        return
    if key in _ISO_ONLY_KEYS:
        if not _ISO_TS_RE.match(value):
            errors.append(f"{where}.{key}: must be an ISO-8601 timestamp")
        return
    if key == "run_id":
        if not (_RUN_ID_RE.match(value) or _PSEUDONYM_RE.match(value)):
            errors.append(f"{where}.{key}: invalid run_id")
        return
    if key == "file_ext":
        if value and value not in _SAFE_FILE_EXTS:
            errors.append(f"{where}.{key}: disallowed file_ext {value!r}")
        return
    if key == "attempt_key":
        if not re.match(r"^(?:\d+|unlinked):\d+:[a-z]+$", value):
            errors.append(f"{where}.{key}: invalid attempt_key")
        return
    if key == "source_batch":
        if not _BATCH_LABEL_RE.match(value):
            errors.append(f"{where}.{key}: invalid source_batch")
        return
    if _looks_like_path(value):
        errors.append(f"{where}.{key}: looks like a filesystem path")
        return
    if not _LABEL_RE.match(value):
        errors.append(f"{where}.{key}: not a closed-vocabulary label")


def _validate_row(
    where: str, row: Any, allowed: frozenset[str], errors: list[str]
) -> None:
    if not isinstance(row, Mapping):
        errors.append(f"{where}: row must be an object")
        return
    for k, v in row.items():
        if k not in allowed:
            errors.append(f"{where}.{k}: key not in allowlist")
            continue
        if k == "cmd_families":
            if not isinstance(v, list):
                errors.append(f"{where}.cmd_families: must be a list")
                continue
            for item in v:
                if (
                    not isinstance(item, str)
                    or not _CMD_FAMILY_RE.match(item)
                    or _looks_like_path(item)
                ):
                    errors.append(f"{where}.cmd_families: invalid family {item!r}")
            continue
        _validate_scalar(where, k, v, errors)


def validate_trace(doc: Any) -> list[str]:
    """Validate a trace document against the strict de-identified allowlist schema."""
    errors: list[str] = []
    if not isinstance(doc, Mapping):
        return ["root: trace must be a JSON object"]

    unknown_top = set(doc.keys()) - _TOP_KEYS
    if unknown_top:
        errors.append(f"root: unknown keys {sorted(unknown_top)}")

    sv = doc.get("schema_version")
    if (
        isinstance(sv, bool)
        or not isinstance(sv, int)
        or sv < 1
        or sv > TRACE_SCHEMA_VERSION
    ):
        errors.append(f"root.schema_version: unsupported value {sv!r}")

    ev = doc.get("extractor_version")
    if isinstance(ev, bool) or not isinstance(ev, int) or ev < 1:
        errors.append(f"root.extractor_version: invalid value {ev!r}")

    _validate_scalar("root", "extracted_at", doc.get("extracted_at"), errors)
    if "source_batch" in doc:
        _validate_scalar("root", "source_batch", doc.get("source_batch"), errors)

    wm = doc.get("watermark")
    if not isinstance(wm, Mapping):
        errors.append("watermark: must be an object")
    else:
        for k, v in wm.items():
            if k not in _WATERMARK_KEYS:
                errors.append(f"watermark.{k}: unknown key")
            elif isinstance(v, bool) or not isinstance(v, int) or v < 0:
                errors.append(f"watermark.{k}: must be a non-negative integer")

    run = doc.get("run")
    if not isinstance(run, Mapping):
        errors.append("run: must be an object")
    else:
        if not run.get("run_id"):
            errors.append("run.run_id: required")
        for k, v in run.items():
            if k not in _RUN_KEYS:
                errors.append(f"run.{k}: key not in allowlist")
                continue
            if k == "policy":
                if not isinstance(v, Mapping):
                    errors.append("run.policy: must be an object")
                else:
                    for pk, pv in v.items():
                        if pk not in _POLICY_KEYS:
                            errors.append(f"run.policy.{pk}: key not in allowlist")
                        elif not isinstance(pv, (bool, int, float)) or (
                            isinstance(pv, float) and not math.isfinite(pv)
                        ):
                            errors.append(f"run.policy.{pk}: invalid type")
            elif k == "startup_timings":
                if not isinstance(v, Mapping):
                    errors.append("run.startup_timings: must be an object")
                else:
                    for sk, sv_val in v.items():
                        if sk not in _STARTUP_KEY_SET:
                            errors.append(f"run.startup_timings.{sk}: unknown key")
                        elif _finite_nonneg(sv_val) is None:
                            errors.append(
                                f"run.startup_timings.{sk}: must be non-negative finite number"
                            )
            elif k == "resume_startup_timings":
                if not isinstance(v, list):
                    errors.append("run.resume_startup_timings: must be a list")
                else:
                    for idx, entry in enumerate(v):
                        if not isinstance(entry, Mapping):
                            errors.append(
                                f"run.resume_startup_timings[{idx}]: must be object"
                            )
                            continue
                        for sk, sv_val in entry.items():
                            if sk not in _STARTUP_KEY_SET:
                                errors.append(
                                    f"run.resume_startup_timings[{idx}].{sk}: unknown key"
                                )
                            elif _finite_nonneg(sv_val) is None:
                                errors.append(
                                    f"run.resume_startup_timings[{idx}].{sk}: invalid number"
                                )
            else:
                _validate_scalar("run", k, v, errors)

    for table_name, allowed in (
        ("items", _ITEM_KEYS),
        ("attempts", _ATTEMPT_KEYS),
        ("steps", _STEP_KEYS),
        ("tool_calls", _TOOL_CALL_KEYS),
        ("driver_events", _DRIVER_EVENT_KEYS),
    ):
        rows = doc.get(table_name)
        if not isinstance(rows, list):
            errors.append(f"{table_name}: must be a list")
            continue
        for idx, row in enumerate(rows):
            _validate_row(f"{table_name}[{idx}]", row, allowed, errors)
            if len(errors) >= 30:
                return errors
    return errors


# --------------------------------------------------------------------------------------
# Cache storage helpers
# --------------------------------------------------------------------------------------


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _load_index(cache_dir: Path) -> dict[str, Any]:
    idx_path = cache_dir / "index.json"
    if not idx_path.is_file():
        return {"schema_version": TRACE_SCHEMA_VERSION, "entries": {}}
    try:
        loaded = json.loads(idx_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict) and isinstance(loaded.get("entries"), dict):
            return loaded
    except (OSError, ValueError):
        pass
    return {"schema_version": TRACE_SCHEMA_VERSION, "entries": {}}


def _save_index(cache_dir: Path, index: Mapping[str, Any]) -> None:
    payload = (json.dumps(index, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write_bytes(cache_dir / "index.json", payload)


def _trace_filename(
    run_id: str, source_id: str, existing_entries: Mapping[str, Any]
) -> str:
    """Return `<run_id>.trace.json.zst`, disambiguating with source suffix only on collision."""
    plain = f"{run_id}.trace.json.zst"
    existing = existing_entries.get(run_id)
    if existing is None or existing.get("source_id") == source_id:
        return plain
    suffix = source_id.split(":", 1)[-1][:8]
    return f"{run_id}.{suffix}.trace.json.zst"


def _entry_key_for(
    run_id: str, source_id: str, existing_entries: Mapping[str, Any]
) -> str:
    existing = existing_entries.get(run_id)
    if existing is None or existing.get("source_id") == source_id:
        return run_id
    suffix = source_id.split(":", 1)[-1][:8]
    return f"{run_id}@{suffix}"


def _write_cached_trace(
    cache_dir: Path,
    index: dict[str, Any],
    trace: Mapping[str, Any],
    *,
    level: int = DEFAULT_ZSTD_LEVEL,
) -> tuple[str, Path, int]:
    run_id = str(trace["run"]["run_id"])
    source_id = str(trace["run"].get("source_id") or "")
    entries: dict[str, Any] = index["entries"]
    key = _entry_key_for(run_id, source_id, entries)
    fname = _trace_filename(run_id, source_id, entries)
    target = cache_dir / "runs" / fname
    raw_json = json.dumps(trace, separators=(",", ":"), sort_keys=True).encode("utf-8")
    compressed = zstd_compress(raw_json, level=level)
    _atomic_write_bytes(target, compressed)
    entries[key] = {
        "run_id": run_id,
        "source_id": source_id,
        "file": fname,
        "watermark": dict(trace["watermark"]),
        "is_terminal": bool(trace["run"].get("is_terminal", False)),
        "created_at": trace["run"].get("created_at"),
        "schema_version": trace["schema_version"],
        "extractor_version": trace["extractor_version"],
        "compressed_bytes": len(compressed),
        "raw_bytes": len(raw_json),
        "source_batch": trace.get("source_batch"),
    }
    return key, target, len(compressed)


# --------------------------------------------------------------------------------------
# Subcommands: collect, pack, ingest
# --------------------------------------------------------------------------------------


def collect_runs(
    *,
    runs_dirs: Sequence[Path | str] = (),
    scan_dirs: Sequence[Path | str] = (),
    cache_dir: Path | str = DEFAULT_CACHE_DIR,
    include_active: bool = False,
    rebuild: bool = False,
    scan_max_depth: int = 7,
    zstd_level: int = DEFAULT_ZSTD_LEVEL,
    on_scan: Callable[[str, str, int, int], None] | None = None,
    on_discovered: Callable[[int], None] | None = None,
    on_progress: Callable[[int, int, str, Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Incrementally extract new/updated runs into `<cache_dir>/runs/*.trace.json.zst`."""
    cdir = Path(cache_dir).expanduser().resolve()
    cdir.mkdir(parents=True, exist_ok=True)
    salt = load_or_create_salt(cdir)
    index = _load_index(cdir)
    entries: dict[str, Any] = index["entries"]

    discovered: list[Path] = []
    seen_paths: set[Path] = set()

    for rdir in runs_dirs:
        p = Path(rdir).expanduser()
        if not p.exists() or not p.is_dir():
            raise ValueError(f"--runs-dir is not an existing directory: {rdir}")
        if on_scan is not None:
            on_scan("runs-dir", str(rdir), 0, len(discovered))
        added_here = 0
        for run_p in discover_runs_from_runs_dir(p):
            canon = run_p.resolve()
            if canon not in seen_paths:
                seen_paths.add(canon)
                discovered.append(run_p)
                added_here += 1
        if on_scan is not None:
            on_scan("runs-dir-done", str(rdir), 1, added_here)

    for sdir in scan_dirs:
        p = Path(sdir).expanduser()
        if not p.exists() or not p.is_dir():
            raise ValueError(f"--scan path is not an existing directory: {sdir}")
        if on_scan is not None:
            on_scan("scan", str(sdir), 0, 0)

        def _scan_cb(
            dirs_walked: int, found_so_far: int, _label: str = str(sdir)
        ) -> None:
            if on_scan is not None:
                on_scan("scan", _label, dirs_walked, found_so_far)

        added_here = 0
        for run_p in scan_runs_dirs(p, max_depth=scan_max_depth, on_step=_scan_cb):
            canon = run_p.resolve()
            if canon not in seen_paths:
                seen_paths.add(canon)
                discovered.append(run_p)
                added_here += 1
        if on_scan is not None:
            on_scan("scan-done", str(sdir), 0, added_here)

    if not runs_dirs and not scan_dirs:
        if on_scan is not None:
            on_scan("runs-dir", ".", 0, 0)
        added_here = 0
        for run_p in discover_runs_from_runs_dir(Path.cwd()):
            canon = run_p.resolve()
            if canon not in seen_paths:
                seen_paths.add(canon)
                discovered.append(run_p)
                added_here += 1
        if on_scan is not None:
            on_scan("runs-dir-done", ".", 1, added_here)

    if on_discovered is not None:
        on_discovered(len(discovered))

    machine_fp = _machine_fingerprint()
    error_details: list[dict[str, Any]] = []
    stats: dict[str, Any] = {
        "discovered": len(discovered),
        "extracted": 0,
        "updated": 0,
        "cached_hits": 0,
        "skipped_active": 0,
        "errors": 0,
        "compressed_bytes_written": 0,
        "error_details": error_details,
    }

    total_runs = len(discovered)
    for idx, run_p in enumerate(discovered, start=1):
        run_id = run_p.name
        if not include_active and _run_is_locked(run_p):
            stats["skipped_active"] += 1
            if on_progress is not None:
                on_progress(idx, total_runs, run_id, stats)
            continue
        wm = compute_run_watermark(run_p)
        source_id = pseudonym(
            f"{machine_fp}|{run_p.parent.expanduser().resolve()}",
            salt=salt,
            domain="src",
        )
        key = _entry_key_for(run_id, source_id, entries)
        prev = entries.get(key)
        if (
            not rebuild
            and isinstance(prev, Mapping)
            and prev.get("watermark") == wm
            and (cdir / "runs" / str(prev.get("file", ""))).is_file()
        ):
            stats["cached_hits"] += 1
            if on_progress is not None:
                on_progress(idx, total_runs, run_id, stats)
            continue

        try:
            trace = extract_run_trace(run_p, salt=salt, watermark=wm)
            val_errors = validate_trace(trace)
            if val_errors:
                stats["errors"] += 1
                stats["error_details"].append(
                    {"run_id": run_id, "errors": val_errors[:5]}
                )
                if on_progress is not None:
                    on_progress(idx, total_runs, run_id, stats)
                continue
            was_existing = key in entries
            _k, _path, cbytes = _write_cached_trace(
                cdir, index, trace, level=zstd_level
            )
            stats["compressed_bytes_written"] += cbytes
            if was_existing:
                stats["updated"] += 1
            else:
                stats["extracted"] += 1
        except Exception as exc:
            stats["errors"] += 1
            stats["error_details"].append(
                {"run_id": run_id, "errors": [f"{type(exc).__name__}: {exc}"]}
            )
        if on_progress is not None:
            on_progress(idx, total_runs, run_id, stats)

    _save_index(cdir, index)
    stats["total_cached"] = len(entries)
    return stats


def _entry_date_str(entry: Mapping[str, Any]) -> str | None:
    created = entry.get("created_at")
    if isinstance(created, str) and len(created) >= 10:
        return created[:10]
    rid = str(entry.get("run_id") or "")
    m = _STAMP_RE.search(rid)
    if m:
        d = m.group(1)
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return None


def pack_traces(
    *,
    cache_dir: Path | str = DEFAULT_CACHE_DIR,
    out_path: Path | str | None = None,
    since: str | None = None,
    until: str | None = None,
    inspect_count: int = 0,
    zstd_level: int = DEFAULT_ZSTD_LEVEL,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> dict[str, Any]:
    """Package cached traces into a single `.tar.zst` bundle, or return sample traces for `--inspect`."""
    cdir = Path(cache_dir).expanduser().resolve()
    index = _load_index(cdir)
    entries: dict[str, Any] = index["entries"]

    selected: list[tuple[str, Path]] = []
    for key in sorted(entries):
        meta = entries[key]
        if not isinstance(meta, Mapping):
            continue
        dstr = _entry_date_str(meta)
        if since and (dstr is None or dstr < since):
            continue
        if until and (dstr is None or dstr > until):
            continue
        fpath = cdir / "runs" / str(meta.get("file") or "")
        if fpath.is_file():
            selected.append((key, fpath))

    if inspect_count > 0:
        samples: list[dict[str, Any]] = []
        for _key, fpath in selected[:inspect_count]:
            raw = zstd_decompress(fpath.read_bytes())
            samples.append(json.loads(raw.decode("utf-8")))
        return {
            "mode": "inspect",
            "selected_total": len(selected),
            "samples": samples,
        }

    if not out_path:
        raise ValueError("--out is required unless --inspect is specified")

    dest = Path(out_path).expanduser().resolve()
    tar_buf = io.BytesIO()
    manifest_entries: list[dict[str, Any]] = []
    uncompressed_total = 0

    total_sel = len(selected)
    with tarfile.open(fileobj=tar_buf, mode="w") as tf:
        for idx, (key, fpath) in enumerate(selected, start=1):
            raw_json = zstd_decompress(fpath.read_bytes())
            doc = json.loads(raw_json.decode("utf-8"))
            val_errors = validate_trace(doc)
            if val_errors:
                raise ValueError(
                    f"refusing to pack non-conforming trace {key}: {val_errors[0]}"
                )
            safe_name = f"traces/{fpath.name.removesuffix('.zst')}"
            info = tarfile.TarInfo(name=safe_name)
            info.size = len(raw_json)
            info.mtime = 0
            info.mode = 0o644
            tf.addfile(info, io.BytesIO(raw_json))
            uncompressed_total += len(raw_json)
            manifest_entries.append(
                {
                    "member": safe_name,
                    "run_id": doc["run"]["run_id"],
                    "source_id": doc["run"].get("source_id"),
                    "sha256": hashlib.sha256(raw_json).hexdigest(),
                    "bytes": len(raw_json),
                }
            )
            if on_progress is not None:
                on_progress(idx, total_sel, str(doc["run"]["run_id"]))
        manifest_bytes = (
            json.dumps(
                {
                    "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
                    "trace_schema_version": TRACE_SCHEMA_VERSION,
                    "packed_at": _utc_now(),
                    "trace_count": len(manifest_entries),
                    "entries": manifest_entries,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        minfo = tarfile.TarInfo(name="bundle-manifest.json")
        minfo.size = len(manifest_bytes)
        minfo.mtime = 0
        minfo.mode = 0o644
        tf.addfile(minfo, io.BytesIO(manifest_bytes))

    compressed = zstd_compress(tar_buf.getvalue(), level=zstd_level)
    _atomic_write_bytes(dest, compressed)
    return {
        "mode": "pack",
        "out": str(dest),
        "traces_packed": len(manifest_entries),
        "uncompressed_bytes": uncompressed_total,
        "compressed_bytes": len(compressed),
    }


def _safe_tar_member_name(name: str) -> bool:
    if not name or name.startswith("/") or name.startswith("\\"):
        return False
    if _DRIVE_PATH_RE.match(name):
        return False
    parts = Path(name).parts
    if any(p in ("..", "") for p in parts):
        return False
    return True


def _iter_bundle_traces(source: Path) -> list[tuple[str, bytes]]:
    """Read raw JSON trace payloads from a `.tar.zst` bundle, `.trace.json.zst` file, or dir."""
    results: list[tuple[str, bytes]] = []
    if source.is_dir():
        for f in sorted(source.glob("*.trace.json.zst")):
            raw = zstd_decompress(f.read_bytes())
            if len(raw) > MAX_MEMBER_BYTES:
                raise ValueError(
                    f"trace exceeds size ceiling ({MAX_MEMBER_BYTES}B): {f.name}"
                )
            results.append((f.name, raw))
        return results

    if source.name.endswith(".trace.json.zst"):
        raw = zstd_decompress(source.read_bytes())
        if len(raw) > MAX_MEMBER_BYTES:
            raise ValueError(f"trace exceeds size ceiling: {source.name}")
        return [(source.name, raw)]

    if source.name.endswith(".trace.json"):
        raw = source.read_bytes()
        if len(raw) > MAX_MEMBER_BYTES:
            raise ValueError(f"trace exceeds size ceiling: {source.name}")
        return [(source.name, raw)]

    # `.tar.zst` archive
    tar_bytes = zstd_decompress(source.read_bytes())
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tf:
        members = tf.getmembers()
        if len(members) > MAX_BUNDLE_MEMBERS:
            raise ValueError(f"bundle exceeds member limit ({MAX_BUNDLE_MEMBERS})")
        for m in members:
            if not _safe_tar_member_name(m.name):
                raise ValueError(f"unsafe archive member path refused: {m.name!r}")
            if m.issym() or m.islnk() or m.isdev() or m.isfifo():
                raise ValueError(f"non-regular archive member refused: {m.name!r}")
            if not m.isfile():
                continue
            if m.size > MAX_MEMBER_BYTES:
                raise ValueError(f"archive member exceeds size ceiling: {m.name!r}")
            if m.name == "bundle-manifest.json":
                continue
            if not m.name.endswith(".trace.json"):
                raise ValueError(f"unexpected archive member refused: {m.name!r}")
            fh = tf.extractfile(m)
            if fh is None:
                continue
            raw = fh.read(MAX_MEMBER_BYTES + 1)
            if len(raw) > MAX_MEMBER_BYTES:
                raise ValueError(
                    f"archive member exceeded size ceiling on read: {m.name!r}"
                )
            results.append((m.name, raw))
    return results


def ingest_bundles(
    sources: Sequence[Path | str],
    *,
    cache_dir: Path | str = DEFAULT_CACHE_DIR,
    batch: str | None = None,
    dry_run: bool = False,
    zstd_level: int = DEFAULT_ZSTD_LEVEL,
    on_source: Callable[[str, int], None] | None = None,
    on_progress: Callable[[int, int, str, Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Validate and merge external `.tar.zst` bundles or `.trace.json.zst` files into the cache."""
    if batch is not None and not _BATCH_LABEL_RE.match(batch):
        raise ValueError(
            f"--batch must match {_BATCH_LABEL_RE.pattern!r}, got {batch!r}"
        )
    cdir = Path(cache_dir).expanduser().resolve()
    if not dry_run:
        cdir.mkdir(parents=True, exist_ok=True)
    index = _load_index(cdir)
    entries: dict[str, Any] = index["entries"]

    stats: dict[str, Any] = {
        "added": 0,
        "upgraded": 0,
        "skipped_same_or_older": 0,
        "rejected": 0,
        "dry_run": dry_run,
        "rejections": [],
    }

    for src in sources:
        p = Path(src).expanduser()
        if not p.exists():
            raise ValueError(f"ingest source does not exist: {src}")
        payloads = _iter_bundle_traces(p)
        total_p = len(payloads)
        if on_source is not None:
            on_source(p.name, total_p)
        for idx, (member_name, raw) in enumerate(payloads, start=1):
            try:
                doc = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError) as exc:
                stats["rejected"] += 1
                stats["rejections"].append(
                    {"member": member_name, "errors": [f"invalid JSON: {exc}"]}
                )
                if on_progress is not None:
                    on_progress(idx, total_p, member_name, stats)
                continue
            if batch is not None and isinstance(doc, dict):
                doc["source_batch"] = batch
            val_errors = validate_trace(doc)
            if val_errors:
                stats["rejected"] += 1
                stats["rejections"].append(
                    {"member": member_name, "errors": val_errors[:5]}
                )
                if on_progress is not None:
                    on_progress(idx, total_p, member_name, stats)
                continue

            run_id = str(doc["run"]["run_id"])
            source_id = str(doc["run"].get("source_id") or "")
            key = _entry_key_for(run_id, source_id, entries)
            prev = entries.get(key)
            incoming_wm = doc["watermark"]
            if isinstance(prev, Mapping):
                prev_wm = prev.get("watermark") or {}
                prev_latest = int(prev_wm.get("latest_mtime_ns", 0))
                inc_latest = int(incoming_wm.get("latest_mtime_ns", 0))
                prev_ev = int(prev.get("extractor_version", 0))
                inc_ev = int(doc.get("extractor_version", 0))
                if inc_latest < prev_latest or (
                    inc_latest == prev_latest and inc_ev <= prev_ev
                ):
                    stats["skipped_same_or_older"] += 1
                    if on_progress is not None:
                        on_progress(idx, total_p, run_id, stats)
                    continue
                if not dry_run:
                    _write_cached_trace(cdir, index, doc, level=zstd_level)
                stats["upgraded"] += 1
            else:
                if not dry_run:
                    _write_cached_trace(cdir, index, doc, level=zstd_level)
                stats["added"] += 1
            if on_progress is not None:
                on_progress(idx, total_p, run_id, stats)

    if not dry_run:
        _save_index(cdir, index)
    stats["total_cached"] = len(entries)
    return stats


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def _add_color_flags(subparser: argparse.ArgumentParser) -> None:
    grp = subparser.add_mutually_exclusive_group()
    grp.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Force ANSI color output even when stderr/stdout is piped.",
    )
    grp.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output.",
    )


def _fmt_bytes(num_bytes: int) -> str:
    val = float(max(0, num_bytes))
    for unit in ("B", "KB", "MB", "GB"):
        if val < 1024.0 or unit == "GB":
            return f"{val:.1f} {unit}" if unit != "B" else f"{int(val)} B"
        val /= 1024.0
    return f"{val:.1f} GB"


def _fmt_elapsed(seconds: float) -> str:
    if seconds < 1.0:
        return f"{seconds * 1000.0:.0f}ms"
    if seconds < 60.0:
        return f"{seconds:.1f}s"
    mins, rem = divmod(int(round(seconds)), 60)
    return f"{mins}m {rem:02d}s"


class _ProfileProgress:
    """Responsive Term-styled stderr progress narration (TTY in-place bar, piped step cues)."""

    def __init__(self, *, enabled: bool, color: bool, use_unicode: bool) -> None:
        self.enabled = enabled
        self.stream = sys.stderr
        self.term = _term_mod.Term(stream=self.stream, color=color, unicode=use_unicode)
        self.is_tty = bool(
            getattr(self.stream, "isatty", None) and self.stream.isatty()
        )
        self._last_draw = 0.0
        self._has_inline = False
        self._started = time.monotonic()

    def _bar(self, idx: int, total: int, width: int = 16) -> str:
        if total <= 0:
            return ""
        frac = min(1.0, max(0.0, idx / total))
        filled = int(round(frac * width))
        fill_ch = "█" if self.term.unicode else "#"
        empty_ch = "░" if self.term.unicode else "-"
        inner = self.term.colorize(fill_ch * filled, "cyan") + self.term.colorize(
            empty_ch * (width - filled), "dim"
        )
        pct = f"{int(round(frac * 100)):3d}%"
        return f"[{inner}] {self.term.colorize(pct, 'bold')}"

    def inline(self, text: str, *, force: bool = False) -> None:
        if not self.enabled or not self.is_tty:
            return
        now = time.monotonic()
        if not force and (now - self._last_draw) < 0.08:
            return
        self._last_draw = now
        label = self.term.severity_label("info")
        self.stream.write(f"\r\033[2K{label} {text}")
        self.stream.flush()
        self._has_inline = True

    def clear_inline(self) -> None:
        if self._has_inline and self.is_tty:
            self.stream.write("\r\033[2K")
            self.stream.flush()
            self._has_inline = False

    def step(self, message: str) -> None:
        if not self.enabled:
            return
        self.clear_inline()
        self.term.step_cue(message, stream=self.stream)

    def on_scan(self, phase: str, label: str, dirs_walked: int, count: int) -> None:
        if not self.enabled:
            return
        styled_label = self.term.colorize(label, "cyan")
        if phase == "scan":
            if dirs_walked == 0:
                if self.is_tty:
                    self.inline(f"Scanning {styled_label}...", force=True)
                else:
                    self.step(f"Scanning {styled_label}...")
            else:
                runs_s = (
                    self.term.colorize(str(count), "green", "bold") if count else "0"
                )
                self.inline(
                    f"Scanning {styled_label}... {self.term.colorize(f'{dirs_walked} dirs', 'dim')} · {runs_s} run(s) found"
                )
        elif phase == "scan-done":
            runs_s = self.term.colorize(str(count), "green", "bold") if count else "0"
            self.step(f"Scanned {styled_label}: {runs_s} run(s) discovered.")
        elif phase == "runs-dir":
            if self.is_tty:
                self.inline(f"Checking {styled_label}...", force=True)
        elif phase == "runs-dir-done":
            runs_s = self.term.colorize(str(count), "green", "bold") if count else "0"
            self.step(f"Checked {styled_label}: {runs_s} run(s) discovered.")

    def on_discovered(self, total: int) -> None:
        if not self.enabled:
            return
        if total == 0:
            self.step("No verified aw run directories discovered.")
        else:
            self.step(f"Processing {self.term.colorize(str(total), 'bold')} run(s)...")

    def on_collect_progress(
        self, idx: int, total: int, run_id: str, stats: Mapping[str, Any]
    ) -> None:
        if not self.enabled or total <= 0:
            return
        force = idx == total
        if self.is_tty:
            bar = self._bar(idx, total)
            ext = int(stats.get("extracted", 0))
            upd = int(stats.get("updated", 0))
            hits = int(stats.get("cached_hits", 0))
            act = int(stats.get("skipped_active", 0))
            errs = int(stats.get("errors", 0))
            zbytes = int(stats.get("compressed_bytes_written", 0))
            parts = [f"{bar} {idx}/{total}"]
            if ext:
                parts.append(self.term.colorize(f"+{ext} new", "green"))
            if upd:
                parts.append(self.term.colorize(f"~{upd} updated", "cyan"))
            if hits:
                parts.append(self.term.colorize(f"{hits} cached", "dim"))
            if act:
                parts.append(self.term.colorize(f"{act} active", "yellow"))
            if errs:
                parts.append(self.term.colorize(f"{errs} err", "red", "bold"))
            if zbytes:
                parts.append(self.term.colorize(_fmt_bytes(zbytes), "cyan"))
            parts.append(
                self.term.colorize(
                    _fmt_elapsed(time.monotonic() - self._started), "dim"
                )
            )
            parts.append(self.term.colorize(run_id[:32], "dim"))
            self.inline("  ".join(parts), force=force)
            if force:
                self.stream.write("\n")
                self.stream.flush()
                self._has_inline = False
        elif idx % 50 == 0 or force:
            self.step(
                f"Collected {idx}/{total} (new={stats.get('extracted', 0)}, "
                f"updated={stats.get('updated', 0)}, cached={stats.get('cached_hits', 0)})"
            )

    def on_pack_progress(self, idx: int, total: int, run_id: str) -> None:
        if not self.enabled or total <= 0:
            return
        force = idx == total
        if self.is_tty:
            bar = self._bar(idx, total)
            self.inline(
                f"Packing {bar} {idx}/{total}  {self.term.colorize(run_id[:32], 'dim')}",
                force=force,
            )
            if force:
                self.stream.write("\n")
                self.stream.flush()
                self._has_inline = False
        elif idx % 50 == 0 or force:
            self.step(f"Packed {idx}/{total} trace(s)...")

    def on_ingest_source(self, source_name: str, total: int) -> None:
        if not self.enabled:
            return
        self.step(
            f"Ingesting {self.term.colorize(source_name, 'cyan')} "
            f"({self.term.colorize(str(total), 'bold')} trace(s))..."
        )

    def on_ingest_progress(
        self, idx: int, total: int, label: str, stats: Mapping[str, Any]
    ) -> None:
        if not self.enabled or total <= 0:
            return
        force = idx == total
        if self.is_tty:
            bar = self._bar(idx, total)
            parts = [
                f"{bar} {idx}/{total}",
                self.term.colorize(f"+{stats.get('added', 0)} added", "green"),
                self.term.colorize(f"~{stats.get('upgraded', 0)} upgraded", "cyan"),
                self.term.colorize(
                    f"{stats.get('skipped_same_or_older', 0)} skipped", "dim"
                ),
            ]
            if stats.get("rejected", 0):
                parts.append(
                    self.term.colorize(f"{stats['rejected']} rejected", "red", "bold")
                )
            parts.append(self.term.colorize(label[:30], "dim"))
            self.inline("  ".join(parts), force=force)
            if force:
                self.stream.write("\n")
                self.stream.flush()
                self._has_inline = False
        elif idx % 50 == 0 or force:
            self.step(
                f"Ingested {idx}/{total} (added={stats.get('added', 0)}, "
                f"upgraded={stats.get('upgraded', 0)}, rejected={stats.get('rejected', 0)})"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aw-profile",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Collect, pack, and ingest compact zstd-compressed, strictly de-identified\n"
            "behavioral profiling traces from `aw agy run` / `aw oc run` directories.\n"
            "\n"
            "Designed for deep performance and cost profiling across multiple repos,\n"
            "multiple servers, and external contributors without shipping raw logs,\n"
            "source code, prompts, or file paths."
        ),
        epilog=(
            "WORKFLOW\n"
            "  1. Extract new or resumed runs on each machine into its local trace cache:\n"
            "       aw-profile collect --scan ~/projects --scan ~/.aw/projects\n"
            "  2. Audit a de-identified sample trace before sharing:\n"
            "       aw-profile pack --inspect 1\n"
            "  3. Bundle cached traces into one portable .tar.zst archive:\n"
            "       aw-profile pack --out server-a-traces.tar.zst\n"
            "  4. Validate and merge bundles (or .trace.json.zst dirs/files) centrally:\n"
            "       aw-profile ingest server-a-traces.tar.zst --batch server-a\n"
            "\n"
            "WHAT IS CAPTURED (6-TABLE LOSSLESS BEHAVIORAL SCHEMA)\n"
            "  run            Host, driver, model/variant, toolkit version, policy flags,\n"
            "                 wall time, startup_timings (script -> output -> question ->\n"
            "                 execution), resume_startup_timings, resume/restart counts.\n"
            "  items          Queue items (salted item/set IDs, action, status, refusal\n"
            "                 code, disposition, readiness, verification, retries, reasks).\n"
            "  attempts       Per-turn summaries across main, verify, recovery, reask,\n"
            "                 and unclaimed sessions (tokens, cost, context curve, timings).\n"
            "  steps          Every individual LLM turn (per-step input/output/reasoning/\n"
            "                 cache tokens, context_size, step cost, duration, tool counts).\n"
            "  tool_calls     Every tool invocation (tool_name, tool_category, normalized\n"
            "                 shell cmd_kind/cmd_families like 'pytest' or 'aw ipd set',\n"
            "                 error_class, input/output bytes, duration, salted\n"
            "                 target_file_id + allowlisted file_ext for re-read analysis).\n"
            "  driver_events  Allowlisted lifecycle events (events.jsonl) and resource\n"
            "                 telemetry samples (cpu_seconds, max_rss_bytes, load_avg).\n"
            "\n"
            "DE-IDENTIFICATION & PRIVACY\n"
            "  - Allowlist-only schema validated before write (collect) and before merge\n"
            "    (ingest). Never stores prompts, source code, file contents, stdout/stderr,\n"
            "    raw paths, shell arguments, git remotes, branch names, or usernames.\n"
            "  - Identifiers (source_id, machine_id, repo_id, set_id, item_id,\n"
            "    target_file_id) use HMAC-SHA256 with a local random salt stored at\n"
            "    <cache-dir>/salt (mode 0600, never exported by pack).\n"
            "  - Traces are de-identified (minimized), not strictly anonymous: timing,\n"
            "    step counts, and volumes remain present for profiling.\n"
            "\n"
            "CACHE LAYOUT & RESUME-SAFE WATERMARKS\n"
            "  Default cache: ~/.aw/profile-cache/\n"
            "    runs/<run_id>.trace.json.zst   One zstd JSON file per run (suffixed with\n"
            "                                   source_id hash only on cross-source clash)\n"
            "    index.json                     Run watermarks & metadata (stat-only check)\n"
            "    salt                           Local HMAC salt (never exported)\n"
            "\n"
            "  Watermarks track mtime+size of state.json, events.jsonl, ledger.jsonl,\n"
            "  sessions/*.jsonl, outcomes/*.json, telemetry/*, and extractor_version.\n"
            "  Unchanged runs hit cache via stat() in milliseconds; resumed runs\n"
            "  automatically re-extract and upgrade on ingest.\n"
            "\n"
            "ZSTANDARD BACKENDS\n"
            "  Uses Python 3.14+ stdlib compression.zstd automatically; falls back to\n"
            "  `zstandard`, `backports.zstd`, or the `zstd` CLI on Python 3.9-3.13.\n"
            "\n"
            "EXIT CODES\n"
            "  0  Success (all discovered runs cached, packed, or ingested cleanly).\n"
            "  1  Completed with one or more per-run extraction errors or rejected traces.\n"
            "  2  Fatal usage, missing path, unsafe archive, or missing zstd backend error.\n"
            "\n"
            "Run `aw-profile <subcommand> --help` for subcommand options and examples."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_collect = sub.add_parser(
        "collect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Extract new or resumed runs into the local .trace.json.zst cache.",
        description=(
            "Discover `aw` run directories, skip unchanged runs via resume-safe stat\n"
            "watermarks, and extract new or updated runs into <cache-dir>/runs/*.trace.json.zst.\n"
            "\n"
            "HOW DISCOVERY WORKS\n"
            "  --runs-dir DIR   Inspects DIR directly: accepts a runs container holding\n"
            "                   run-* subdirectories, a single run directory (state.json\n"
            "                   or ledger.jsonl), or a repo root (.aw/records/runs,\n"
            "                   .aw/runs, .agents/runs). Does NOT recurse deeply.\n"
            "  --scan DIR       Walks DIR RECURSIVELY (up to --max-depth, default 7) to\n"
            "                   find verified run-* directories anywhere beneath DIR.\n"
            "                   Follows a symlink passed as DIR itself, prunes .git,\n"
            "                   worktrees, analytics, node_modules, .venv, venv,\n"
            "                   __pycache__, and test/lint caches, never descends inside\n"
            "                   a matched run directory, and requires each run-* folder\n"
            "                   to contain state.json or ledger.jsonl (ignoring unrelated\n"
            "                   run-* folders from other tools).\n"
            "  (no flags)       Defaults to discovering runs in the current directory.\n"
            "\n"
            "LIVE RUNS & RESUME\n"
            "  Runs holding an active driver.lock are skipped by default so half-written\n"
            "  JSONL files are not snapshotted (pass --include-active to include them).\n"
            "  When a previously cached run is later resumed, its watermark advances and\n"
            "  the next collect atomically replaces only that run's .trace.json.zst."
        ),
        epilog=(
            "EXAMPLES\n"
            "  aw-profile collect                                   # current repo/dir\n"
            "  aw-profile collect --scan ~/projects --scan ~/.aw/projects\n"
            "  aw-profile collect --runs-dir /mnt/archive/runs --json\n"
            "  aw-profile collect --scan ~/projects --max-depth 9 --include-active\n"
            "  aw-profile collect --scan ~/projects --rebuild       # force re-extract"
        ),
    )
    p_collect.add_argument(
        "--runs-dir",
        action="append",
        default=[],
        metavar="DIR",
        help="Runs container dir, single run dir, or repo root (repeatable; non-recursive).",
    )
    p_collect.add_argument(
        "--scan",
        action="append",
        default=[],
        metavar="DIR",
        help=(
            "Root directory to scan recursively for verified run-* dirs up to --max-depth "
            "(repeatable; follows root symlink, prunes .git/worktrees/analytics/caches)."
        ),
    )
    p_collect.add_argument(
        "--max-depth",
        type=int,
        default=7,
        metavar="N",
        help="Maximum recursion depth for --scan (default: 7; covers <root>/<org>/<repo>/.aw/records/runs/run-*).",
    )
    p_collect.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        metavar="DIR",
        help="Trace cache directory (default: ~/.aw/profile-cache).",
    )
    p_collect.add_argument(
        "--include-active",
        action="store_true",
        help="Also extract currently locked/running runs (default: skip active runs).",
    )
    p_collect.add_argument(
        "--rebuild",
        action="store_true",
        help="Re-extract all discovered runs even if their watermark matches index.json.",
    )
    p_collect.add_argument(
        "--level",
        type=int,
        default=DEFAULT_ZSTD_LEVEL,
        metavar="N",
        help="Zstandard compression level (default: 6).",
    )
    p_collect.add_argument("--json", action="store_true", help="Emit JSON summary.")
    _add_color_flags(p_collect)

    p_pack = sub.add_parser(
        "pack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Bundle cached traces into a portable de-identified .tar.zst archive (or --inspect).",
        description=(
            "Package cached traces into a single portable .tar.zst bundle for transferring\n"
            "between servers or sharing from external contributors.\n"
            "\n"
            "Each trace is re-validated against the strict de-identified allowlist before\n"
            "being added. Inner members are stored as raw .trace.json inside one shared\n"
            "zstd stream so zstd compresses repeated keys across runs. The local HMAC\n"
            "salt (<cache-dir>/salt) is NEVER included in a bundle.\n"
            "\n"
            "Use --inspect [N] to print N sample de-identified JSON records to stdout\n"
            "without writing any file, so you can audit exactly what would be shared."
        ),
        epilog=(
            "EXAMPLES\n"
            "  aw-profile pack --inspect 1                          # preview 1 trace\n"
            "  aw-profile pack --out host-a.tar.zst                 # bundle all cached runs\n"
            "  aw-profile pack --out nov.tar.zst --since 2026-11-01 --until 2026-11-30\n"
            "  aw-profile pack --cache-dir /tmp/prof --out out.tar.zst --json"
        ),
    )
    p_pack.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        metavar="DIR",
        help="Trace cache directory (default: ~/.aw/profile-cache).",
    )
    p_pack.add_argument(
        "--out",
        default=None,
        metavar="FILE",
        help="Output .tar.zst bundle path (required unless --inspect is given).",
    )
    p_pack.add_argument(
        "--since",
        default=None,
        metavar="YYYY-MM-DD",
        help="Include only runs dated on or after YYYY-MM-DD (inclusive).",
    )
    p_pack.add_argument(
        "--until",
        default=None,
        metavar="YYYY-MM-DD",
        help="Include only runs dated on or before YYYY-MM-DD (inclusive).",
    )
    p_pack.add_argument(
        "--inspect",
        nargs="?",
        const=1,
        type=int,
        default=0,
        metavar="N",
        help="Print N sample de-identified trace(s) to stdout without writing a bundle.",
    )
    p_pack.add_argument(
        "--level",
        type=int,
        default=DEFAULT_ZSTD_LEVEL,
        metavar="N",
        help="Zstandard compression level (default: 6).",
    )
    p_pack.add_argument("--json", action="store_true", help="Emit JSON summary.")
    _add_color_flags(p_pack)

    p_ingest = sub.add_parser(
        "ingest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Validate and merge .tar.zst bundles or .trace.json.zst files into the cache.",
        description=(
            "Safely validate and merge traces from one or more .tar.zst bundles,\n"
            ".trace.json.zst/.trace.json files, or directories of .trace.json.zst files\n"
            "into the destination trace cache.\n"
            "\n"
            "SAFETY & MERGE RULES\n"
            "  - Archive safety: refuses symlinks, hardlinks, device nodes, absolute paths,\n"
            "    '..' path traversal, unexpected member filenames, and members > 64 MiB.\n"
            "  - Privacy gate: validates every trace against the strict allowlist schema;\n"
            "    rejects unknown keys, raw filesystem paths, multi-line strings, non-finite\n"
            "    numbers, or free text (exits 1 if any trace is rejected).\n"
            "  - Resume-safe upgrades: an incoming trace with a strictly newer watermark\n"
            "    (or newer extractor_version at equal watermark) upgrades the cached copy;\n"
            "    same or older copies are skipped and never downgrade existing data.\n"
            "  - Cross-source collisions: two distinct source_id values sharing a run_id\n"
            "    are both preserved via <run_id>.<src8>.trace.json.zst."
        ),
        epilog=(
            "EXAMPLES\n"
            "  aw-profile ingest server-a.tar.zst --batch server-a\n"
            "  aw-profile ingest contrib.tar.zst --batch contrib-01 --dry-run\n"
            "  aw-profile ingest /mnt/synced-runs/ box2.tar.zst --json"
        ),
    )
    p_ingest.add_argument(
        "sources",
        nargs="+",
        metavar="PATH",
        help="One or more .tar.zst bundles, .trace.json.zst/.trace.json files, or directories.",
    )
    p_ingest.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        metavar="DIR",
        help="Destination trace cache directory (default: ~/.aw/profile-cache).",
    )
    p_ingest.add_argument(
        "--batch",
        default=None,
        metavar="LABEL",
        help="Optional closed-vocabulary provenance tag (e.g. server-b or contrib-20261120).",
    )
    p_ingest.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate all inputs and report add/upgrade/skip/reject counts without writing.",
    )
    p_ingest.add_argument(
        "--level",
        type=int,
        default=DEFAULT_ZSTD_LEVEL,
        metavar="N",
        help="Zstandard compression level (default: 6).",
    )
    p_ingest.add_argument("--json", action="store_true", help="Emit JSON summary.")
    _add_color_flags(p_ingest)

    return parser


def _resolve_color_choice(args: argparse.Namespace, stream: Any) -> bool:
    if getattr(args, "no_color", False) or getattr(args, "json", False):
        return False
    if getattr(args, "color", False):
        return True
    return _term_mod.should_color(stream)


def main(argv: Sequence[str] | None = None) -> int:
    _term_mod.ensure_encodable_stdio()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    is_json = bool(getattr(args, "json", False))
    out_color = _resolve_color_choice(args, sys.stdout)
    err_color = _resolve_color_choice(args, sys.stderr)
    out_term = _term_mod.Term(
        stream=sys.stdout, color=out_color, unicode=_term_mod.should_unicode(sys.stdout)
    )
    err_term = _term_mod.Term(
        stream=sys.stderr, color=err_color, unicode=_term_mod.should_unicode(sys.stderr)
    )
    prog = _ProfileProgress(
        enabled=not is_json and not bool(getattr(args, "inspect", 0)),
        color=err_color,
        use_unicode=_term_mod.should_unicode(sys.stderr),
    )
    started = time.monotonic()
    try:
        if args.command == "collect":
            if args.max_depth < 1:
                raise ValueError("--max-depth must be >= 1")
            res = collect_runs(
                runs_dirs=args.runs_dir,
                scan_dirs=args.scan,
                cache_dir=args.cache_dir,
                include_active=args.include_active,
                rebuild=args.rebuild,
                scan_max_depth=args.max_depth,
                zstd_level=args.level,
                on_scan=prog.on_scan,
                on_discovered=prog.on_discovered,
                on_progress=prog.on_collect_progress,
            )
            prog.clear_inline()
            if is_json:
                print(json.dumps(res, indent=2, sort_keys=True))
            else:
                elapsed = _fmt_elapsed(time.monotonic() - started)
                status_kind = "warn" if res["errors"] > 0 else "ok"
                headline = (
                    f"{res['discovered']} discovered, "
                    f"{out_term.colorize(str(res['extracted']), 'green', 'bold')} new, "
                    f"{out_term.colorize(str(res['updated']), 'cyan', 'bold')} updated, "
                    f"{out_term.colorize(str(res['cached_hits']), 'dim')} cached"
                )
                if res["skipped_active"]:
                    headline += f", {out_term.colorize(str(res['skipped_active']), 'yellow', 'bold')} active skipped"
                if res["errors"]:
                    headline += f", {out_term.colorize(str(res['errors']), 'red', 'bold')} error(s)"
                out_term.outcome(
                    status_kind, f"aw-profile collect ({elapsed}): {headline}"
                )
                zwritten = int(res.get("compressed_bytes_written", 0))
                out_term.kv(
                    "cache",
                    f"{out_term.colorize(str(res['total_cached']), 'bold')} trace(s) in "
                    f"{out_term.colorize(str(args.cache_dir), 'cyan')}"
                    + (
                        f" ({out_term.colorize(_fmt_bytes(zwritten), 'cyan')} written)"
                        if zwritten
                        else ""
                    ),
                )
                for detail in list(res.get("error_details") or [])[:5]:
                    rid = detail.get("run_id", "?")
                    errs = "; ".join(str(e) for e in (detail.get("errors") or []))
                    print(
                        f"{err_term.severity_label('error')} {rid}: {errs}",
                        file=sys.stderr,
                    )
                if res["total_cached"] > 0:
                    out_term.next_action(
                        "aw-profile pack --out traces.tar.zst",
                        "bundle cached traces for transfer or sharing",
                    )
            return 1 if res["errors"] > 0 else 0

        if args.command == "pack":
            if not args.inspect and not is_json:
                prog.step(
                    f"Preparing traces from {err_term.colorize(str(args.cache_dir), 'cyan')}..."
                )
            res = pack_traces(
                cache_dir=args.cache_dir,
                out_path=args.out,
                since=args.since,
                until=args.until,
                inspect_count=args.inspect,
                zstd_level=args.level,
                on_progress=prog.on_pack_progress,
            )
            prog.clear_inline()
            if res["mode"] == "inspect":
                print(json.dumps(res["samples"], indent=2, sort_keys=True))
                return 0
            if is_json:
                print(json.dumps(res, indent=2, sort_keys=True))
            else:
                elapsed = _fmt_elapsed(time.monotonic() - started)
                ratio = (
                    res["uncompressed_bytes"] / res["compressed_bytes"]
                    if res["compressed_bytes"] > 0
                    else 0.0
                )
                out_term.outcome(
                    "ok",
                    f"aw-profile pack ({elapsed}): "
                    f"{out_term.colorize(str(res['traces_packed']), 'green', 'bold')} trace(s) -> "
                    f"{out_term.colorize(_fmt_bytes(res['compressed_bytes']), 'cyan', 'bold')} "
                    f"({ratio:.1f}x from {_fmt_bytes(res['uncompressed_bytes'])})",
                )
                out_term.kv("bundle", out_term.colorize(str(res["out"]), "cyan"))
            return 0

        if args.command == "ingest":
            res = ingest_bundles(
                args.sources,
                cache_dir=args.cache_dir,
                batch=args.batch,
                dry_run=args.dry_run,
                zstd_level=args.level,
                on_source=prog.on_ingest_source,
                on_progress=prog.on_ingest_progress,
            )
            prog.clear_inline()
            if is_json:
                print(json.dumps(res, indent=2, sort_keys=True))
            else:
                elapsed = _fmt_elapsed(time.monotonic() - started)
                prefix = "[dry-run] " if res["dry_run"] else ""
                status_kind = "warn" if res["rejected"] > 0 else "ok"
                headline = (
                    f"{out_term.colorize(str(res['added']), 'green', 'bold')} added, "
                    f"{out_term.colorize(str(res['upgraded']), 'cyan', 'bold')} upgraded, "
                    f"{out_term.colorize(str(res['skipped_same_or_older']), 'dim')} skipped"
                )
                if res["rejected"]:
                    headline += f", {out_term.colorize(str(res['rejected']), 'red', 'bold')} rejected"
                out_term.outcome(
                    status_kind,
                    f"{prefix}aw-profile ingest ({elapsed}): {headline}",
                )
                out_term.kv(
                    "cache",
                    f"{out_term.colorize(str(res['total_cached']), 'bold')} trace(s) in "
                    f"{out_term.colorize(str(args.cache_dir), 'cyan')}",
                )
                for rej in list(res.get("rejections") or [])[:5]:
                    member = rej.get("member", "?")
                    errs = "; ".join(str(e) for e in (rej.get("errors") or []))
                    print(
                        f"{err_term.severity_label('warn')} rejected {member}: {errs}",
                        file=sys.stderr,
                    )
            return 1 if res["rejected"] > 0 else 0

        parser.error(f"Unknown command: {args.command}")
        return 2
    except (ValueError, OSError, ZstdUnavailableError, tarfile.TarError) as exc:
        prog.clear_inline()
        print(f"{err_term.severity_label('error')} aw-profile: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

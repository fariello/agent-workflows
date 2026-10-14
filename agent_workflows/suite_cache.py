"""Tree-keyed full-suite runner and result cache (`aw suite`, IPD `0o0wt2`).

Provides:
- `suite_key(checkout, argv)` (E-02): deterministic SHA-256 key over the working-tree git tree
  (including tracked edits and untracked non-ignored files, computed via a temporary index copy
  and temporary object directory so the real index and object store are never mutated), normalized
  argv, interpreter identity, installed distributions digest, and behavior-changing environment
  variables.
- `<git-common-dir>/aw-suite-cache/<digest>.json` store (E-03): stores passing runs directly and
  stores failing runs with `confirmed: true` only after one confirming re-run of the extracted
  failing node ids reproduces at least one failure. Prunes records older than 14 days on write
  and fails open when the git common dir is read-only.
- `run_full_suite(checkout, *, argv=SUITE_CHECK_ARGV, use_cache=True, ...)` (E-04): runs or
  serves the full suite with a bounded xdist worker count (`workers = max(2, cpus // slots)` from
  `AW_SUITE_SLOTS`, appended to `PYTEST_ADDOPTS` in the child environment).
"""

from __future__ import annotations

import contextlib
import datetime
import hashlib
import importlib
import importlib.metadata
import json
import os
import re
import selectors
import shutil
import subprocess
import sys
import tempfile
import time
import secrets
import socket
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from agent_workflows import platform_lock
from agent_workflows.runner_shared import INTEGRATION_LOCK_PROGRESS_SECONDS

SUITE_CHECK_TIMEOUT_SECONDS: float = 900.0

SUITE_CHECK_ARGV: Tuple[str, ...] = (sys.executable or "python3", "-m", "pytest")

SUITE_FAILURE_LINE_LIMIT: int = 40

SUITE_OUTPUT_MAX_BYTES: int = 512_000

CACHE_MAX_AGE_SECONDS: int = 14 * 24 * 60 * 60

SUITE_REFUSAL_MESSAGE: str = "aw suite runs the FULL suite only; run a narrowed selection with plain python3 -m pytest"

AW_SUITE_LOCK_DIR_ENV: str = "AW_SUITE_LOCK_DIR"
AW_SUITE_SLOT_TIMEOUT_ENV: str = "AW_SUITE_SLOT_TIMEOUT"
DEFAULT_AW_SUITE_SLOT_TIMEOUT: float = 3600.0
AW_SUITE_SLOT_HELD_ENV: str = "AW_SUITE_SLOT_HELD"
AW_SUITE_HEARTBEAT_SECONDS_ENV: str = "AW_SUITE_HEARTBEAT_SECONDS"
DEFAULT_AW_SUITE_HEARTBEAT_SECONDS: float = 60.0

_HEARTBEAT_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")

SUITE_KEY_ENV_VARS: Tuple[str, ...] = (
    "AW_EXECUTION_ROLE",
    "AW_NO_REEXEC",
    "FORCE_COLOR",
    "NO_COLOR",
    "PYTEST_ADDOPTS",
    "PYTHONPATH",
    "TERM",
)

_SUITE_SUMMARY_RE = re.compile(
    r"^(?:=+\s*)?(\d+ (?:passed|failed).*?)(?:\s*=+)?$", re.MULTILINE
)

_SUITE_FAILURE_LINE_RE = re.compile(r"^(?:FAILED|ERROR)\s+\S.*$", re.MULTILINE)

_FAILING_NODE_ID_RE = re.compile(r"^(?:FAILED|ERROR)\s+(\S+::\S+)")

_LOOKUP_ENABLED: bool = True

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent


def parse_suite_summary(text: str) -> str:
    """Return the pytest count summary line from `text`, or `""` when none is present."""
    match = _SUITE_SUMMARY_RE.search(text or "")
    return match.group(1).strip() if match else ""


def extract_suite_failures(stdout: str, stderr: str = "") -> Tuple[str, ...]:
    """Return deduplicated `FAILED`/`ERROR` lines from suite output in first-seen order."""
    seen: Dict[str, None] = {}
    for haystack in (stdout or "", stderr or ""):
        for match in _SUITE_FAILURE_LINE_RE.finditer(haystack):
            line = match.group(0).strip()
            if line and line not in seen:
                seen[line] = None
            if len(seen) >= SUITE_FAILURE_LINE_LIMIT:
                return tuple(seen)
    return tuple(seen)


def extract_failing_node_ids(failures: Sequence[str]) -> Tuple[str, ...]:
    """Extract runnable pytest node ids (`path::test_name`) from failure lines.

    Collection errors without a `::` node id return no node id here, so unparseable/collection
    failures are never stored (E-03).
    """
    seen: Dict[str, None] = {}
    for line in failures or ():
        match = _FAILING_NODE_ID_RE.match(str(line or "").strip())
        if match:
            node_id = match.group(1).strip()
            if node_id and node_id not in seen:
                seen[node_id] = None
    return tuple(seen)


class SuiteKey:
    """Result of `suite_key(checkout, argv)`.

    When uncacheable, `digest` is `None` and `reason` explains why.
    """

    def __init__(
        self,
        digest: Optional[str],
        components_or_reason: Union[Mapping[str, Any], str, None] = None,
        *,
        reason: str = "",
        head: str = "",
    ) -> None:
        self.digest: Optional[str] = str(digest) if digest else None
        if isinstance(components_or_reason, str):
            self.components: Dict[str, Any] = {}
            self.reason: str = components_or_reason
        elif isinstance(components_or_reason, Mapping):
            self.components = dict(components_or_reason)
            self.reason = str(reason or "")
        else:
            self.components = {}
            self.reason = str(reason or "")
        self.head: str = str(head or "")

    @property
    def cacheable(self) -> bool:
        return bool(self.digest)

    def __repr__(self) -> str:
        return (
            f"SuiteKey(digest={self.digest!r}, components={self.components!r}, "
            f"reason={self.reason!r}, head={self.head!r})"
        )


@dataclass(frozen=True)
class SlotOutcome:
    """Outcome of attempting to acquire a machine-wide test-suite slot (IPD xvm6no)."""

    slot_acquired: bool = False
    waited_seconds: float = 0.0
    slot_index: Optional[int] = None
    timeout_seconds: float = 0.0
    acquired: Optional[bool] = None

    def __post_init__(self) -> None:
        if self.acquired is not None and not self.slot_acquired:
            object.__setattr__(self, "slot_acquired", bool(self.acquired))
        elif self.slot_acquired and self.acquired is None:
            object.__setattr__(self, "acquired", bool(self.slot_acquired))
        elif self.acquired is None:
            object.__setattr__(self, "acquired", False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot_acquired": bool(self.slot_acquired),
            "acquired": bool(self.slot_acquired),
            "waited_seconds": round(float(self.waited_seconds), 3),
            "slot_index": self.slot_index,
            "timeout_seconds": round(float(self.timeout_seconds), 3),
        }


@dataclass(frozen=True)
class SuiteRunResult:
    """Structured outcome of `run_full_suite`."""

    passed: bool
    exit_code: int
    summary: str
    failures: Tuple[str, ...] = ()
    duration_seconds: float = 0.0
    cached: bool = False
    digest: Optional[str] = None
    components: Dict[str, Any] = field(default_factory=dict)
    worker_count: int = 0
    recorded_at: str = ""
    confirmed: bool = False
    reason: str = ""
    notice: str = ""
    stdout: str = ""
    stderr: str = ""
    slot: Optional[Dict[str, Any]] = None

    @property
    def passing(self) -> bool:
        return self.passed

    @property
    def returncode(self) -> int:
        return self.exit_code

    @property
    def duration_ms(self) -> int:
        return int(round(self.duration_seconds * 1000))

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "passed": bool(self.passed),
            "exit_code": int(self.exit_code),
            "returncode": int(self.exit_code),
            "summary": str(self.summary),
            "failures": list(self.failures),
            "duration_seconds": round(float(self.duration_seconds), 3),
            "duration_ms": self.duration_ms,
            "cached": bool(self.cached),
            "digest": self.digest,
            "components": dict(self.components),
            "worker_count": int(self.worker_count),
            "recorded_at": str(self.recorded_at),
            "confirmed": bool(self.confirmed),
            "reason": str(self.reason),
        }
        if self.slot is not None:
            d["slot"] = dict(self.slot)
        return d


def _normalize_argv_after_interpreter(argv: Sequence[str]) -> List[str]:
    """Return argv tokens after the Python interpreter, excluding `-n` / `--numprocesses`."""
    tokens = [str(tok) for tok in (argv or ())]
    if not tokens:
        return []
    first_name = Path(tokens[0]).name.lower()
    if tokens[0] == sys.executable or first_name.startswith("python"):
        tokens = tokens[1:]

    cleaned: List[str] = []
    skip_next = False
    for tok in tokens:
        if skip_next:
            skip_next = False
            continue
        if tok in ("-n", "--numprocesses"):
            skip_next = True
            continue
        if (tok.startswith("-n") and len(tok) > 2 and tok[2:].isdigit()) or (
            tok == "-nauto"
        ):
            continue
        if tok.startswith("--numprocesses="):
            continue
        cleaned.append(tok)
    return cleaned


def _distributions_digest() -> str:
    """Compute a deterministic SHA-256 digest over sorted `name==version` installed packages."""
    items: List[str] = []
    seen: set[str] = set()
    for dist in importlib.metadata.distributions():
        try:
            meta = dist.metadata
            name = (meta["Name"] if meta is not None else "") or ""
            version = dist.version or ""
        except Exception:
            continue
        norm_name = name.strip().lower()
        if not norm_name:
            continue
        entry = f"{norm_name}=={version.strip()}"
        if entry not in seen:
            seen.add(entry)
            items.append(entry)
    items.sort()
    return hashlib.sha256("\n".join(items).encode("utf-8")).hexdigest()


def _env_component(
    env: Optional[Mapping[str, str]] = None,
) -> Tuple[str, Dict[str, str]]:
    """Hash behavior-changing env vars without persisting raw values."""
    source = os.environ if env is None else env
    per_var: Dict[str, str] = {}
    lines: List[str] = []
    for name in SUITE_KEY_ENV_VARS:
        if name in source:
            val_hash = hashlib.sha256(str(source[name]).encode("utf-8")).hexdigest()
            short = val_hash[:16]
            per_var[name] = short
            lines.append(f"{name}=present:{ val_hash }")
        else:
            per_var[name] = "absent"
            lines.append(f"{name}=absent")
    digest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    return digest, per_var


def _working_tree_id(checkout: Path) -> Tuple[Optional[str], str, str]:
    """Compute the working-tree git tree OID without touching the real index or object store.

    Returns `(tree_oid, head_oid, error_reason)`.
    """
    try:
        resolved_checkout = Path(checkout).resolve()
        if not resolved_checkout.is_dir():
            return None, "", f"checkout directory does not exist: {checkout}"
    except OSError as exc:
        return None, "", f"cannot resolve checkout: {exc}"

    try:
        idx_proc = subprocess.run(
            ["git", "-C", str(resolved_checkout), "rev-parse", "--git-path", "index"],
            capture_output=True,
            text=True,
            timeout=10.0,
            check=False,
        )
        if idx_proc.returncode != 0:
            detail = (idx_proc.stderr or idx_proc.stdout or "").strip()
            return None, "", detail or "not a git repository"

        obj_proc = subprocess.run(
            ["git", "-C", str(resolved_checkout), "rev-parse", "--git-path", "objects"],
            capture_output=True,
            text=True,
            timeout=10.0,
            check=False,
        )
        if obj_proc.returncode != 0:
            detail = (obj_proc.stderr or obj_proc.stdout or "").strip()
            return None, "", detail or "could not resolve git objects directory"

        head_proc = subprocess.run(
            ["git", "-C", str(resolved_checkout), "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10.0,
            check=False,
        )
        head_oid = head_proc.stdout.strip() if head_proc.returncode == 0 else ""

        real_index = (resolved_checkout / idx_proc.stdout.strip()).resolve()
        real_objects = (resolved_checkout / obj_proc.stdout.strip()).resolve()

        with tempfile.TemporaryDirectory(prefix="aw-suite-key-") as tmpdir:
            tmp_path = Path(tmpdir)
            tmp_index = tmp_path / "index"
            tmp_objects = tmp_path / "objects"
            tmp_objects.mkdir(parents=True, exist_ok=True)
            if real_index.is_file():
                shutil.copy2(real_index, tmp_index)

            git_env = dict(os.environ)
            git_env.pop("GIT_DIR", None)
            git_env.pop("GIT_WORK_TREE", None)
            git_env["GIT_INDEX_FILE"] = str(tmp_index)
            git_env["GIT_OBJECT_DIRECTORY"] = str(tmp_objects)
            existing_alt = git_env.get("GIT_ALTERNATE_OBJECT_DIRECTORIES", "").strip()
            git_env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = (
                f"{real_objects}{os.pathsep}{existing_alt}"
                if existing_alt
                else str(real_objects)
            )

            add_proc = subprocess.run(
                [
                    "git",
                    "-C",
                    str(resolved_checkout),
                    "-c",
                    "gc.auto=0",
                    "-c",
                    "maintenance.auto=false",
                    "add",
                    "-A",
                ],
                env=git_env,
                capture_output=True,
                text=True,
                timeout=30.0,
                check=False,
            )
            if add_proc.returncode != 0:
                detail = (add_proc.stderr or add_proc.stdout or "").strip()
                return None, head_oid, detail or "git add -A failed on temporary index"

            wt_proc = subprocess.run(
                [
                    "git",
                    "-C",
                    str(resolved_checkout),
                    "-c",
                    "gc.auto=0",
                    "-c",
                    "maintenance.auto=false",
                    "write-tree",
                ],
                env=git_env,
                capture_output=True,
                text=True,
                timeout=30.0,
                check=False,
            )
            if wt_proc.returncode != 0 or not wt_proc.stdout.strip():
                detail = (wt_proc.stderr or wt_proc.stdout or "").strip()
                return (
                    None,
                    head_oid,
                    detail or "git write-tree failed on temporary index",
                )
            return wt_proc.stdout.strip(), head_oid, ""
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "", f"git tree computation failed: {exc}"


def suite_key(
    checkout: Union[str, Path],
    argv: Sequence[str] = SUITE_CHECK_ARGV,
    *,
    env: Optional[Mapping[str, str]] = None,
) -> SuiteKey:
    """Compute the deterministic full-suite cache key for `checkout` and `argv` (E-02).

    Fails open: any git or metadata error yields `SuiteKey(None, reason)`.
    """
    try:
        tree_id, head_oid, err_reason = _working_tree_id(Path(checkout))
        if not tree_id:
            return SuiteKey(None, err_reason or "working tree is uncacheable")

        norm_argv = _normalize_argv_after_interpreter(argv)
        argv_digest = hashlib.sha256(
            json.dumps(norm_argv, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        interp_raw = f"{sys.executable}\0{sys.version}"
        interpreter_digest = hashlib.sha256(interp_raw.encode("utf-8")).hexdigest()

        distributions_digest = _distributions_digest()
        env_digest, env_vars = _env_component(env)

        core_components = {
            "tree": tree_id,
            "argv": argv_digest,
            "interpreter": interpreter_digest,
            "distributions": distributions_digest,
            "env": env_digest,
        }
        canonical = json.dumps(core_components, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        components: Dict[str, Any] = {
            **core_components,
            "env_vars": env_vars,
        }
        return SuiteKey(digest, components, head=head_oid)
    except Exception as exc:  # noqa: BLE001
        return SuiteKey(None, f"key computation failed: {exc}")


def is_git_checkout(checkout: Union[str, Path]) -> bool:
    """Return True if `checkout` is inside a git repository."""
    try:
        resolved = Path(checkout).resolve()
        if not resolved.is_dir():
            return False
        proc = subprocess.run(
            ["git", "-C", str(resolved), "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def suite_cache_dir(checkout: Union[str, Path]) -> Optional[Path]:
    """Return `<git-common-dir>/aw-suite-cache` for `checkout`, or `None` if unavailable."""
    try:
        resolved = Path(checkout).resolve()
        proc = subprocess.run(
            ["git", "-C", str(resolved), "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        common = (resolved / proc.stdout.strip()).resolve()
        return common / "aw-suite-cache"
    except (OSError, subprocess.SubprocessError):
        return None


def _parse_iso_timestamp(value: str) -> Optional[float]:
    if not value:
        return None
    try:
        norm = value.strip()
        if norm.endswith("Z"):
            norm = norm[:-1] + "+00:00"
        dt = datetime.datetime.fromisoformat(norm)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _is_record_expired(record: Mapping[str, Any], path: Path, now: float) -> bool:
    rec_ts = _parse_iso_timestamp(str(record.get("recorded_at") or ""))
    if rec_ts is not None:
        return (now - rec_ts) > CACHE_MAX_AGE_SECONDS
    try:
        return (now - path.stat().st_mtime) > CACHE_MAX_AGE_SECONDS
    except OSError:
        return False


def read_cached_record(
    checkout: Union[str, Path],
    digest: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Look up `<git-common-dir>/aw-suite-cache/<digest>.json` (E-03). Never raises."""
    if not digest:
        return None
    cache_dir = suite_cache_dir(checkout)
    if cache_dir is None:
        return None
    rec_path = cache_dir / f"{digest}.json"
    try:
        if not rec_path.is_file():
            return None
        raw = json.loads(rec_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        if raw.get("digest") != digest:
            return None
        if not isinstance(raw.get("passed"), bool):
            return None
        if not isinstance(raw.get("exit_code"), int):
            return None
        if not isinstance(raw.get("summary"), str):
            return None
        if not isinstance(raw.get("failures"), list):
            return None
        if _is_record_expired(raw, rec_path, time.time()):
            with contextlib.suppress(OSError):
                rec_path.unlink()
            return None
        return raw
    except Exception:
        return None


def prune_expired_records(cache_dir: Path, *, now: Optional[float] = None) -> int:
    """Remove cache records older than 14 days. Best-effort, never raises."""
    current = time.time() if now is None else now
    removed = 0
    try:
        if not cache_dir.is_dir():
            return 0
        for entry in list(cache_dir.glob("*.json")):
            try:
                expired = (current - entry.stat().st_mtime) > CACHE_MAX_AGE_SECONDS
                if not expired:
                    raw = json.loads(entry.read_text(encoding="utf-8"))
                    if isinstance(raw, dict) and _is_record_expired(
                        raw, entry, current
                    ):
                        expired = True
                if expired:
                    entry.unlink()
                    removed += 1
            except Exception:
                continue
    except Exception:
        pass
    return removed


def write_cached_record(
    checkout: Union[str, Path],
    record: Mapping[str, Any],
) -> bool:
    """Atomically write `<git-common-dir>/aw-suite-cache/<digest>.json` and prune >14d records.

    Fails open with a single stderr note when the git common dir is not writable (E-03).
    """
    digest = str(record.get("digest") or "").strip()
    if not digest:
        return False
    cache_dir = suite_cache_dir(checkout)
    if cache_dir is None:
        return False
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        prune_expired_records(cache_dir)
        target = cache_dir / f"{digest}.json"
        payload = json.dumps(dict(record), indent=2, sort_keys=True) + "\n"
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{digest[:12]}-",
            suffix=".tmp",
            dir=str(cache_dir),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp_name, target)
        finally:
            if os.path.exists(tmp_name):
                with contextlib.suppress(OSError):
                    os.unlink(tmp_name)
        return True
    except OSError as exc:
        print(
            f"aw suite: cache write skipped ({exc})",
            file=sys.stderr,
        )
        return False


def explain_key_diff(
    checkout: Union[str, Path],
    key: SuiteKey,
) -> Dict[str, Any]:
    """Compare `key` against stored cache records for `--explain` (E-05)."""
    info: Dict[str, Any] = {
        "cacheable": key.cacheable,
        "digest": key.digest,
        "head": key.head,
        "reason": key.reason,
        "components": dict(key.components),
        "hit": False,
        "compared_digest": None,
        "compared_head": None,
        "differing_components": [],
    }
    if not key.cacheable or not key.digest:
        return info

    existing = read_cached_record(checkout, key.digest)
    if existing is not None:
        info["hit"] = True
        info["compared_digest"] = key.digest
        info["compared_head"] = existing.get("head") or key.head
        return info

    cache_dir = suite_cache_dir(checkout)
    if cache_dir is None or not cache_dir.is_dir():
        return info

    candidates: List[Tuple[float, Dict[str, Any]]] = []
    same_head_candidates: List[Tuple[float, Dict[str, Any]]] = []
    for entry in cache_dir.glob("*.json"):
        try:
            raw = json.loads(entry.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or not isinstance(raw.get("components"), dict):
                continue
            ts = (
                _parse_iso_timestamp(str(raw.get("recorded_at") or ""))
                or entry.stat().st_mtime
            )
            candidates.append((ts, raw))
            if key.head and raw.get("head") == key.head:
                same_head_candidates.append((ts, raw))
        except Exception:
            continue

    pool = same_head_candidates if same_head_candidates else candidates
    if not pool:
        return info

    pool.sort(key=lambda pair: pair[0], reverse=True)
    _, prior = pool[0]
    prior_comp = prior.get("components") or {}
    diffs: List[str] = []
    for comp_name in ("tree", "argv", "interpreter", "distributions", "env"):
        if key.components.get(comp_name) != prior_comp.get(comp_name):
            diffs.append(comp_name)
    info["compared_digest"] = prior.get("digest")
    info["compared_head"] = prior.get("head")
    info["differing_components"] = diffs
    return info


def resolve_suite_slots(
    env: Optional[Mapping[str, str]] = None,
    *,
    cpus: Optional[int] = None,
) -> int:
    """Resolve `AW_SUITE_SLOTS` (default `max(1, cpus // 6)`), warning on invalid values (E-04)."""
    effective_cpus = int(cpus if cpus is not None else (os.cpu_count() or 2))
    default_slots = max(1, effective_cpus // 6)
    source = os.environ if env is None else env
    raw = source.get("AW_SUITE_SLOTS")
    if raw is None or not str(raw).strip():
        return default_slots
    try:
        parsed = int(str(raw).strip())
        if parsed >= 1:
            return parsed
    except ValueError:
        pass
    print(
        f"aw suite: invalid AW_SUITE_SLOTS={raw!r}; falling back to default {default_slots}",
        file=sys.stderr,
    )
    return default_slots


def resolve_suite_workers(
    env: Optional[Mapping[str, str]] = None,
    *,
    cpus: Optional[int] = None,
) -> int:
    """Compute bounded xdist worker count `max(2, cpus // slots)` (E-04)."""
    effective_cpus = int(cpus if cpus is not None else (os.cpu_count() or 2))
    slots = resolve_suite_slots(env, cpus=effective_cpus)
    return max(2, effective_cpus // slots)


def _restore_caller_addopts() -> None:
    """Restore the caller's pre-suite `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` after `_preparse`.

    `build_suite_child_env` appends `-n <workers>` to `PYTEST_ADDOPTS`, registers
    `agent_workflows.suite_cache` in `PYTEST_PLUGINS`, and records the caller's original
    values in `_AW_SUITE_CALLER_ADDOPTS` and `_AW_SUITE_CALLER_PLUGINS`. Pytest's `_preparse`
    reads `PYTEST_ADDOPTS` before `consider_env()` imports `PYTEST_PLUGINS`, so restoring
    both variables when this module is imported as a plugin keeps `-n <workers>` active for
    the outer suite while preventing nested `pytest` subprocesses from inheriting `-n <workers>`.
    """
    if "_AW_SUITE_CALLER_ADDOPTS" in os.environ:
        caller_addopts = os.environ.pop("_AW_SUITE_CALLER_ADDOPTS", "")
        if caller_addopts:
            os.environ["PYTEST_ADDOPTS"] = caller_addopts
        else:
            os.environ.pop("PYTEST_ADDOPTS", None)
    if "_AW_SUITE_CALLER_PLUGINS" in os.environ:
        caller_plugins = os.environ.pop("_AW_SUITE_CALLER_PLUGINS", "")
        if caller_plugins:
            os.environ["PYTEST_PLUGINS"] = caller_plugins
        else:
            os.environ.pop("PYTEST_PLUGINS", None)


_restore_caller_addopts()


def pytest_configure(config: Any) -> None:
    """Ensure caller `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` are restored."""
    _restore_caller_addopts()


try:
    _pytest_mod: Any = importlib.import_module("pytest")

    @_pytest_mod.hookimpl(optionalhook=True)
    def pytest_xdist_setupnodes(config: Any, specs: Sequence[Any]) -> None:
        """Emit `created: N/N workers` when `-q` suppresses xdist's default status line."""
        if getattr(getattr(config, "option", None), "verbose", 0) < 0 and specs:
            n = len(specs)
            tr = config.pluginmanager.getplugin("terminalreporter")
            if tr is not None:
                tr.write_line(f"created: {n}/{n} workers")
except Exception:  # noqa: BLE001
    pass


def resolve_suite_slot_timeout(env: Optional[Mapping[str, str]] = None) -> float:
    """Resolve `AW_SUITE_SLOT_TIMEOUT` (default 3600.0s), warning on non-positive or malformed values (E-02)."""
    source = os.environ if env is None else env
    raw = source.get(AW_SUITE_SLOT_TIMEOUT_ENV)
    if raw is None or not str(raw).strip():
        return DEFAULT_AW_SUITE_SLOT_TIMEOUT
    try:
        val = float(str(raw).strip())
        if val > 0:
            return val
    except ValueError:
        pass
    print(
        f"aw suite: invalid {AW_SUITE_SLOT_TIMEOUT_ENV}={raw!r}; falling back to default {DEFAULT_AW_SUITE_SLOT_TIMEOUT:.0f}s",
        file=sys.stderr,
    )
    return DEFAULT_AW_SUITE_SLOT_TIMEOUT


def resolve_suite_heartbeat_interval(
    env: Optional[Mapping[str, str]] = None,
) -> float:
    """Resolve heartbeat interval min(60.0, AW_SUITE_HEARTBEAT_SECONDS) (E-04)."""
    source = os.environ if env is None else env
    raw = source.get(AW_SUITE_HEARTBEAT_SECONDS_ENV)
    if raw is None or not str(raw).strip():
        return DEFAULT_AW_SUITE_HEARTBEAT_SECONDS
    try:
        val = float(str(raw).strip())
        if val > 0:
            return min(DEFAULT_AW_SUITE_HEARTBEAT_SECONDS, val)
    except ValueError:
        pass
    return DEFAULT_AW_SUITE_HEARTBEAT_SECONDS


def resolve_suite_lock_dir(
    env: Optional[Mapping[str, str]] = None,
) -> Tuple[Optional[Path], Optional[str]]:
    """Resolve machine-wide, per-user lock directory and verify secure ownership/permissions (E-02).

    Returns (dir_path, refusal_reason). Refusal occurs if directory already exists and is
    owned by another uid or writable by group/other.
    """
    source = os.environ if env is None else env
    custom_dir = source.get(AW_SUITE_LOCK_DIR_ENV)
    if custom_dir and str(custom_dir).strip():
        dir_path = Path(str(custom_dir).strip())
    elif source.get("XDG_RUNTIME_DIR") and str(source.get("XDG_RUNTIME_DIR")).strip():
        dir_path = Path(str(source["XDG_RUNTIME_DIR"]).strip()) / "agent-workflows"
    else:
        if hasattr(os, "getuid"):
            user_str = str(os.getuid())
        else:
            import getpass

            user_str = str(getpass.getuser())
        dir_path = Path(tempfile.gettempdir()) / f"agent-workflows-{user_str}"

    try:
        if not dir_path.exists():
            dir_path.mkdir(mode=0o700, parents=True, exist_ok=True)
            if hasattr(os, "chmod") and os.name != "nt":
                with contextlib.suppress(OSError):
                    os.chmod(dir_path, 0o700)
        st = dir_path.stat()
        if hasattr(os, "getuid") and st.st_uid != os.getuid():
            return (
                None,
                f"aw suite: lock directory {dir_path} owned by uid {st.st_uid} (expected {os.getuid()}); running without a slot",
            )
        if os.name != "nt" and (st.st_mode & 0o022) != 0:
            return (
                None,
                f"aw suite: lock directory {dir_path} writable by group/other (mode {oct(st.st_mode)}); running without a slot",
            )
    except OSError as exc:
        return (
            None,
            f"aw suite: cannot access lock directory {dir_path} ({exc}); running without a slot",
        )

    return dir_path, None


def heartbeat_path(
    run_id: Optional[str],
    item_id6: Optional[str],
    *,
    env: Optional[Mapping[str, str]] = None,
) -> Optional[Path]:
    """Return the machine-wide heartbeat path for (run_id, item_id6), or None if invalid (E-04)."""
    if not run_id or not item_id6:
        return None
    r_str = str(run_id).strip()
    i_str = str(item_id6).strip()
    if not _HEARTBEAT_ID_RE.match(r_str) or not _HEARTBEAT_ID_RE.match(i_str):
        return None
    dir_path, refusal = resolve_suite_lock_dir(env)
    if dir_path is None:
        return None
    return dir_path / f"heartbeat-{r_str}-{i_str}"


def touch_heartbeat(
    run_id: Optional[str] = None,
    item_id6: Optional[str] = None,
    *,
    env: Optional[Mapping[str, str]] = None,
) -> None:
    """Touch the heartbeat file for (run_id, item_id6), creating it if absent (E-04)."""
    source = os.environ if env is None else env
    r_str = run_id if run_id is not None else source.get("AW_RUN_ID")
    i_str = item_id6 if item_id6 is not None else source.get("AW_ITEM_ID6")
    if not r_str or not i_str:
        return
    p = heartbeat_path(r_str, i_str, env=source)
    if p is None:
        return
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.touch()
        else:
            now_t = time.time()
            os.utime(p, (now_t, now_t))
    except OSError:
        pass


def remove_heartbeat_file(
    run_id: Optional[str],
    item_id6: Optional[str],
    *,
    env: Optional[Mapping[str, str]] = None,
) -> None:
    """Remove the heartbeat file for (run_id, item_id6) if present (fail-safe, E-04/E-05)."""
    if not run_id or not item_id6:
        return
    try:
        p = heartbeat_path(run_id, item_id6, env=env)
        if p is not None and p.is_file():
            p.unlink(missing_ok=True)
    except Exception:
        pass


def _run_suite_heartbeat_loop(
    stop_event: threading.Event,
    interval: float,
    env: Optional[Mapping[str, str]] = None,
) -> None:
    while not stop_event.wait(interval):
        touch_heartbeat(env=env)


@contextlib.contextmanager
def suite_slot(
    *,
    checkout: Optional[Union[str, Path]] = None,
    progress: Optional[Callable[[str], None]] = None,
    heartbeat: Optional[Callable[[], None]] = None,
    env: Optional[Mapping[str, str]] = None,
    poll_interval: float = 1.0,
    timeout: Optional[float] = None,
    sleep: Optional[Callable[[float], None]] = None,
    now: Optional[Callable[[], float]] = None,
) -> Iterator[SlotOutcome]:
    """Acquire one machine-wide test-suite slot for the duration of the context (E-02).

    - N lock files suite-slot-<k>.lock under a machine-wide, per-user directory.
    - Bounded loud wait: prints progress immediately on first busy poll and every 60s.
    - Touches heartbeat on every poll.
    - Nested guard (E-03): no-op when AW_SUITE_SLOT_HELD is set.
    - On timeout expiry: runs anyway with loud warning and acquired=False.
    """
    source = os.environ if env is None else env
    _now = now if now is not None else time.monotonic
    _sleep = sleep if sleep is not None else time.sleep

    active_poll = poll_interval
    if "AW_SUITE_SLOT_POLL_INTERVAL" in source:
        try:
            active_poll = float(source["AW_SUITE_SLOT_POLL_INTERVAL"])
        except ValueError:
            pass

    if source.get(AW_SUITE_SLOT_HELD_ENV) == "1":
        yield SlotOutcome(acquired=True, waited_seconds=0.0, slot_index=None)
        return

    lock_dir, refusal = resolve_suite_lock_dir(source)
    if lock_dir is None:
        if refusal:
            print(refusal, file=sys.stderr)
        yield SlotOutcome(acquired=False, waited_seconds=0.0, slot_index=None)
        return

    _say = (
        progress
        if progress is not None
        else (lambda msg: (sys.stderr.write(f"{msg}\n"), sys.stderr.flush()))
    )
    _heartbeat = (
        heartbeat if heartbeat is not None else (lambda: touch_heartbeat(env=source))
    )

    N = resolve_suite_slots(source)
    max_wait = (
        float(timeout) if timeout is not None else resolve_suite_slot_timeout(source)
    )

    started = _now()
    first_busy = True
    last_reported = started
    checkout_path = (
        Path(checkout).resolve() if checkout is not None else Path.cwd().resolve()
    )

    while True:
        acquired_slot: Optional[int] = None
        handle: Optional[platform_lock.LockHandle] = None

        for k in range(N):
            lock_path = lock_dir / f"suite-slot-{k}.lock"
            try:
                handle = platform_lock.acquire(lock_path, blocking=False)
                acquired_slot = k
                break
            except platform_lock.LockBusy:
                continue
            except Exception as exc:
                print(
                    f"aw suite: lock acquisition failed ({exc}); running without a slot",
                    file=sys.stderr,
                )
                yield SlotOutcome(
                    acquired=False,
                    waited_seconds=_now() - started,
                    slot_index=None,
                )
                return

        if acquired_slot is not None and handle is not None:
            holder_path = lock_dir / f"suite-slot-{acquired_slot}.holder.json"
            holder_data = {
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "repo": str(checkout_path),
                "run_id": str(source.get("AW_RUN_ID") or ""),
                "item_id6": str(source.get("AW_ITEM_ID6") or ""),
                "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            tmp_holder = (
                lock_dir
                / f"suite-slot-{acquired_slot}.holder.{os.getpid()}.{secrets.token_hex(4)}.tmp"
            )
            try:
                tmp_holder.write_text(json.dumps(holder_data), encoding="utf-8")
                os.replace(tmp_holder, holder_path)
            except OSError:
                pass

            waited_total = _now() - started
            try:
                yield SlotOutcome(
                    acquired=True,
                    waited_seconds=waited_total,
                    slot_index=acquired_slot,
                )
            finally:
                with contextlib.suppress(OSError):
                    if holder_path.exists():
                        holder_path.unlink()
                handle.release()
            return

        summaries: List[str] = []
        for k in range(N):
            h_path = lock_dir / f"suite-slot-{k}.holder.json"
            summary = "unknown holder"
            if h_path.exists():
                try:
                    data = json.loads(h_path.read_text(encoding="utf-8"))
                    pid = data.get("pid")
                    repo = data.get("repo")
                    if pid is not None and repo:
                        summary = f"pid {pid} ({repo})"
                    elif pid is not None:
                        summary = f"pid {pid}"
                except Exception:
                    summary = "unknown holder"
            summaries.append(summary)

        waited = _now() - started
        holder_summary_text = ", ".join(summaries)
        progress_msg = (
            f"aw suite: waiting for a test-suite slot ({len(summaries)} of {N} held: "
            f"{holder_summary_text}); waited {waited:.0f}s"
        )

        if first_busy:
            first_busy = False
            last_reported = _now()
            _say(progress_msg)
        elif _now() - last_reported >= INTEGRATION_LOCK_PROGRESS_SECONDS:
            last_reported = _now()
            _say(progress_msg)

        _heartbeat()

        if _now() - started >= max_wait:
            print(
                f"aw suite: timed out waiting for test-suite slot after {waited:.0f}s "
                f"(bound {max_wait:.0f}s); running anyway without a slot",
                file=sys.stderr,
            )
            yield SlotOutcome(
                acquired=False,
                waited_seconds=waited,
                slot_index=None,
            )
            return

        _sleep(active_poll)


def build_suite_child_env(
    env: Optional[Mapping[str, str]] = None,
    *,
    cpus: Optional[int] = None,
) -> Tuple[Dict[str, str], int]:
    """Return `(child_env, worker_count)` with `-n <workers>` appended to `PYTEST_ADDOPTS`."""
    base = dict(os.environ if env is None else env)
    workers = resolve_suite_workers(base, cpus=cpus)
    existing = str(base.get("PYTEST_ADDOPTS") or "").strip()
    base["_AW_SUITE_CALLER_ADDOPTS"] = existing
    base["PYTEST_ADDOPTS"] = f"{existing} -n {workers}".strip()
    base[AW_SUITE_SLOT_HELD_ENV] = "1"

    existing_plugins = str(base.get("PYTEST_PLUGINS") or "").strip()
    base["_AW_SUITE_CALLER_PLUGINS"] = existing_plugins
    plugin_list = [p.strip() for p in existing_plugins.split(",") if p.strip()]
    if "agent_workflows.suite_cache" not in plugin_list:
        plugin_list.append("agent_workflows.suite_cache")
    base["PYTEST_PLUGINS"] = ",".join(plugin_list)

    cur_pp = str(base.get("PYTHONPATH") or "").strip()
    repo_str = str(_REPO_ROOT)
    if repo_str not in [p for p in cur_pp.split(os.pathsep) if p]:
        base["PYTHONPATH"] = (
            f"{repo_str}{os.pathsep}{cur_pp}".rstrip(os.pathsep) if cur_pp else repo_str
        )
    return base, workers


def check_narrowed_selection(argv_tokens: Sequence[str]) -> Optional[str]:
    """Return `SUITE_REFUSAL_MESSAGE` if `argv_tokens` contains a narrowed selection (E-09)."""
    for tok in argv_tokens:
        s = str(tok)
        if s in ("-k", "-m") or s.startswith("-k=") or s.startswith("-m="):
            return SUITE_REFUSAL_MESSAGE
        if "::" in s:
            return SUITE_REFUSAL_MESSAGE
        if not s.startswith("-"):
            return SUITE_REFUSAL_MESSAGE
    return None


def _run_streaming_subprocess(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout: float,
    max_output_bytes: int = SUITE_OUTPUT_MAX_BYTES,
) -> Tuple[int, str, str]:
    """Run `argv` streaming stdout/stderr live while keeping a bounded copy of each stream."""
    try:
        proc = subprocess.Popen(
            list(argv),
            cwd=str(cwd),
            env=dict(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as exc:  # noqa: BLE001
        msg = f"{exc}\n"
        sys.stderr.write(msg)
        sys.stderr.flush()
        return 127, "", msg

    stdout_buf = bytearray()
    stderr_buf = bytearray()
    deadline = time.monotonic() + float(timeout)
    timed_out = False

    if os.name == "nt":
        import threading

        def _drain(stream_obj: Any, buf: bytearray, out_buf: Any) -> None:
            try:
                while True:
                    chunk = stream_obj.read(8192)
                    if not chunk:
                        break
                    out_buf.write(chunk)
                    out_buf.flush()
                    if len(buf) < max_output_bytes:
                        take = max_output_bytes - len(buf)
                        buf.extend(chunk[:take])
            except Exception:  # noqa: BLE001
                pass

        threads: List[threading.Thread] = []
        if proc.stdout is not None:
            t_out = threading.Thread(
                target=_drain,
                args=(proc.stdout, stdout_buf, sys.stdout.buffer),
                daemon=True,
            )
            t_out.start()
            threads.append(t_out)
        if proc.stderr is not None:
            t_err = threading.Thread(
                target=_drain,
                args=(proc.stderr, stderr_buf, sys.stderr.buffer),
                daemon=True,
            )
            t_err.start()
            threads.append(t_err)

        try:
            proc.wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            timed_out = True
            with contextlib.suppress(Exception):
                proc.kill()
        for t in threads:
            t.join(timeout=2.0)
    else:
        sel = selectors.DefaultSelector()
        try:
            if proc.stdout is not None:
                sel.register(proc.stdout, selectors.EVENT_READ, data="stdout")
            if proc.stderr is not None:
                sel.register(proc.stderr, selectors.EVENT_READ, data="stderr")

            while sel.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    with contextlib.suppress(Exception):
                        proc.kill()
                    break
                events = sel.select(timeout=min(0.25, remaining))
                if not events:
                    if proc.poll() is not None and not sel.select(timeout=0.0):
                        break
                    continue
                for key, _mask in events:
                    stream_obj = key.fileobj
                    chunk = os.read(stream_obj.fileno(), 8192)  # type: ignore[union-attr]
                    if not chunk:
                        sel.unregister(stream_obj)
                        continue
                    if key.data == "stdout":
                        sys.stdout.buffer.write(chunk)
                        sys.stdout.buffer.flush()
                        if len(stdout_buf) < max_output_bytes:
                            take = max_output_bytes - len(stdout_buf)
                            stdout_buf.extend(chunk[:take])
                    else:
                        sys.stderr.buffer.write(chunk)
                        sys.stderr.buffer.flush()
                        if len(stderr_buf) < max_output_bytes:
                            take = max_output_bytes - len(stderr_buf)
                            stderr_buf.extend(chunk[:take])
        finally:
            sel.close()

    if timed_out:
        with contextlib.suppress(Exception):
            proc.wait(timeout=5.0)
        stderr_text = (
            bytes(stderr_buf).decode("utf-8", errors="replace") + "\nCommand timed out."
        )
        return 124, bytes(stdout_buf).decode("utf-8", errors="replace"), stderr_text

    rc = proc.wait()
    return (
        int(rc),
        bytes(stdout_buf).decode("utf-8", errors="replace"),
        bytes(stderr_buf).decode("utf-8", errors="replace"),
    )


def _run_captured_subprocess(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout: float,
    max_output_bytes: int = SUITE_OUTPUT_MAX_BYTES,
) -> Tuple[int, str, str]:
    """Run `argv` capturing bounded stdout and stderr without streaming."""
    try:
        proc = subprocess.run(
            list(argv),
            cwd=str(cwd),
            env=dict(env),
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout_raw = (proc.stdout or b"")[:max_output_bytes]
        stderr_raw = (proc.stderr or b"")[:max_output_bytes]
        return (
            int(proc.returncode),
            stdout_raw.decode("utf-8", errors="replace"),
            stderr_raw.decode("utf-8", errors="replace"),
        )
    except subprocess.TimeoutExpired as exc:
        stdout_raw = (exc.stdout or b"")[:max_output_bytes]
        stderr_raw = (exc.stderr or b"")[:max_output_bytes] + b"\nCommand timed out."
        return (
            124,
            stdout_raw.decode("utf-8", errors="replace"),
            stderr_raw.decode("utf-8", errors="replace"),
        )
    except Exception as exc:  # noqa: BLE001
        return 127, "", str(exc)


def _confirm_failing_node_ids(
    checkout: Path,
    argv: Sequence[str],
    node_ids: Sequence[str],
    *,
    env: Mapping[str, str],
    timeout: float,
) -> bool:
    """Re-run `argv` restricted to `node_ids` once and return True if at least one fails again (E-03)."""
    if not node_ids:
        return False
    confirm_argv = [*list(argv), *list(node_ids)]
    rc, out, err = _run_captured_subprocess(
        confirm_argv,
        cwd=checkout,
        env=env,
        timeout=min(float(timeout), 300.0),
    )
    if rc in (0, 124, 127):
        return False
    re_failures = extract_suite_failures(out, err)
    re_node_ids = set(extract_failing_node_ids(re_failures))
    if re_node_ids & set(node_ids):
        return True
    return bool(re_failures)


def format_cached_notice(record: Mapping[str, Any]) -> str:
    """Format the human cache-hit notice line (E-04)."""
    comp = record.get("components")
    tree_id = ""
    if isinstance(comp, Mapping):
        tree_id = str(comp.get("tree") or "")
    short_tree = (tree_id or str(record.get("digest") or ""))[:12] or "unknown"
    when = str(record.get("recorded_at") or "unknown")
    dur = float(record.get("duration_seconds") or 0.0)
    summary = str(record.get("summary") or "no summary")
    return (
        f"aw suite: cached result for tree {short_tree} "
        f"(recorded {when}, {dur:.2f}s): {summary}"
    )


def run_full_suite(
    checkout: Union[str, Path],
    *,
    argv: Sequence[str] = SUITE_CHECK_ARGV,
    use_cache: bool = True,
    serve_failures: bool = True,
    timeout: float = SUITE_CHECK_TIMEOUT_SECONDS,
    stream: bool = False,
    run_id: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> SuiteRunResult:
    """Run or serve the full test suite for `checkout` (E-04).

    - When `use_cache=True` and a valid record exists for the exact `suite_key`:
      serves a stored PASS directly, and serves a stored confirmed FAILURE only when
      `serve_failures=True` (runner seams pass `serve_failures=False` so a seam never acts
      on a cached failure, E-06).
    - On a miss, bounds xdist workers via `PYTEST_ADDOPTS` (`-n <workers>`), runs the suite,
      and stores a PASS directly or a FAILURE after one confirming re-run of failing node ids.
    """
    checkout_path = Path(checkout)
    from agent_workflows import run_evidence

    capture_is_mocked = run_id is not None and (
        hasattr(run_evidence.capture_command, "_mock_name")
        or getattr(run_evidence.capture_command, "__name__", "") != "capture_command"
    )
    non_pytest_in_repo_root = False
    try:
        if checkout_path.resolve() == _REPO_ROOT and "pytest" not in " ".join(
            str(x) for x in argv
        ):
            non_pytest_in_repo_root = True
    except OSError:
        pass

    bypass_cache = capture_is_mocked or non_pytest_in_repo_root
    key = (
        SuiteKey(None, "cache bypassed for synthetic/mocked invocation")
        if bypass_cache
        else suite_key(checkout_path, argv, env=env)
    )

    if use_cache and _LOOKUP_ENABLED and key.cacheable and key.digest:
        cached_rec = read_cached_record(checkout_path, key.digest)
        if cached_rec is not None:
            cached_passed = bool(cached_rec.get("passed"))
            cached_confirmed = bool(cached_rec.get("confirmed"))
            if cached_passed or (serve_failures and cached_confirmed):
                notice = format_cached_notice(cached_rec)
                if stream:
                    print(notice)
                exit_code = int(cached_rec.get("exit_code", 0 if cached_passed else 1))
                summary = str(cached_rec.get("summary") or "")
                failures = tuple(str(x) for x in (cached_rec.get("failures") or ()))
                reason = (
                    f"suite passed in {checkout_path} ({summary or 'no summary line parsed'})"
                    if exit_code == 0
                    else f"suite FAILED with exit {exit_code} in {checkout_path} ({summary or 'no summary line parsed'})"
                )
                return SuiteRunResult(
                    passed=cached_passed,
                    exit_code=exit_code,
                    summary=summary,
                    failures=failures,
                    duration_seconds=0.0,
                    cached=True,
                    digest=key.digest,
                    components=dict(key.components),
                    worker_count=int(cached_rec.get("worker_count") or 0),
                    recorded_at=str(cached_rec.get("recorded_at") or ""),
                    confirmed=cached_confirmed,
                    reason=reason,
                    notice=notice,
                )

    with suite_slot(checkout=checkout_path, env=env) as slot_outcome:
        slot_info = slot_outcome.to_dict()
        child_env, workers = build_suite_child_env(env)
        started = time.monotonic()

        hb_interval = resolve_suite_heartbeat_interval(env)
        stop_hb = threading.Event()
        hb_thread = threading.Thread(
            target=_run_suite_heartbeat_loop,
            args=(stop_hb, hb_interval, env),
            daemon=True,
        )
        hb_thread.start()

        try:
            if run_id is not None:
                old_addopts = os.environ.get("PYTEST_ADDOPTS")
                old_caller = os.environ.get("_AW_SUITE_CALLER_ADDOPTS")
                old_plugins = os.environ.get("PYTEST_PLUGINS")
                old_caller_plugins = os.environ.get("_AW_SUITE_CALLER_PLUGINS")
                old_pp = os.environ.get("PYTHONPATH")
                old_slot_held = os.environ.get(AW_SUITE_SLOT_HELD_ENV)
                try:
                    os.environ["PYTEST_ADDOPTS"] = child_env["PYTEST_ADDOPTS"]
                    os.environ["_AW_SUITE_CALLER_ADDOPTS"] = child_env.get(
                        "_AW_SUITE_CALLER_ADDOPTS", ""
                    )
                    os.environ["PYTEST_PLUGINS"] = child_env.get("PYTEST_PLUGINS", "")
                    os.environ["_AW_SUITE_CALLER_PLUGINS"] = child_env.get(
                        "_AW_SUITE_CALLER_PLUGINS", ""
                    )
                    os.environ["PYTHONPATH"] = child_env.get("PYTHONPATH", "")
                    os.environ[AW_SUITE_SLOT_HELD_ENV] = "1"
                    tool_event, _envelope = run_evidence.capture_command(
                        run_id,
                        list(argv),
                        cwd=checkout_path,
                        evidence_kind="test_report",
                        actor="runtime",
                        timeout=timeout,
                        max_output_bytes=SUITE_OUTPUT_MAX_BYTES,
                    )
                    exit_code = int(tool_event.get("exit_code", 127))
                    stdout = str(tool_event.stdout or "")
                    stderr = str(tool_event.stderr or "")
                finally:
                    if old_slot_held is None:
                        os.environ.pop(AW_SUITE_SLOT_HELD_ENV, None)
                    else:
                        os.environ[AW_SUITE_SLOT_HELD_ENV] = old_slot_held
                    if old_addopts is None:
                        os.environ.pop("PYTEST_ADDOPTS", None)
                    else:
                        os.environ["PYTEST_ADDOPTS"] = old_addopts
                    if old_caller is None:
                        os.environ.pop("_AW_SUITE_CALLER_ADDOPTS", None)
                    else:
                        os.environ["_AW_SUITE_CALLER_ADDOPTS"] = old_caller
                    if old_plugins is None:
                        os.environ.pop("PYTEST_PLUGINS", None)
                    else:
                        os.environ["PYTEST_PLUGINS"] = old_plugins
                    if old_caller_plugins is None:
                        os.environ.pop("_AW_SUITE_CALLER_PLUGINS", None)
                    else:
                        os.environ["_AW_SUITE_CALLER_PLUGINS"] = old_caller_plugins
                    if old_pp is None:
                        os.environ.pop("PYTHONPATH", None)
                    else:
                        os.environ["PYTHONPATH"] = old_pp
            elif stream:
                exit_code, stdout, stderr = _run_streaming_subprocess(
                    argv,
                    cwd=checkout_path,
                    env=child_env,
                    timeout=timeout,
                    max_output_bytes=SUITE_OUTPUT_MAX_BYTES,
                )
            else:
                exit_code, stdout, stderr = _run_captured_subprocess(
                    argv,
                    cwd=checkout_path,
                    env=child_env,
                    timeout=timeout,
                    max_output_bytes=SUITE_OUTPUT_MAX_BYTES,
                )
        finally:
            stop_hb.set()
            hb_thread.join(timeout=2.0)

        elapsed = time.monotonic() - started
        summary = parse_suite_summary(stdout) or parse_suite_summary(stderr)
        failures = extract_suite_failures(stdout, stderr)
        passed = exit_code == 0

        if exit_code == 0:
            reason = f"suite passed in {checkout_path} ({summary or 'no summary line parsed'})"
        elif exit_code == 124:
            reason = (
                f"suite TIMED OUT after {timeout:.0f}s (ran {elapsed:.0f}s) in {checkout_path}; "
                "treated as a failure (fail-closed)"
            )
        elif exit_code == 127:
            reason = (
                f"suite could not be executed in {checkout_path} (exit 127); "
                "treated as a failure (fail-closed)"
            )
        else:
            reason = (
                f"suite FAILED with exit {exit_code} in {checkout_path} "
                f"({summary or 'no summary line parsed'})"
            )

        now_iso = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        confirmed = False

        if key.cacheable and key.digest and not bypass_cache:
            if passed:
                record: Dict[str, Any] = {
                    "digest": key.digest,
                    "head": key.head,
                    "components": dict(key.components),
                    "passed": True,
                    "exit_code": 0,
                    "summary": summary,
                    "failures": list(failures),
                    "duration_seconds": round(float(elapsed), 3),
                    "recorded_at": now_iso,
                    "worker_count": int(workers),
                    "confirmed": True,
                }
                write_cached_record(checkout_path, record)
                confirmed = True
            elif exit_code not in (124, 127):
                node_ids = extract_failing_node_ids(failures)
                if node_ids and _confirm_failing_node_ids(
                    checkout_path,
                    argv,
                    node_ids,
                    env=child_env,
                    timeout=timeout,
                ):
                    confirmed = True
                    record = {
                        "digest": key.digest,
                        "head": key.head,
                        "components": dict(key.components),
                        "passed": False,
                        "exit_code": int(exit_code),
                        "summary": summary,
                        "failures": list(failures),
                        "duration_seconds": round(float(elapsed), 3),
                        "recorded_at": now_iso,
                        "worker_count": int(workers),
                        "confirmed": True,
                    }
                    write_cached_record(checkout_path, record)

        return SuiteRunResult(
            passed=passed,
            exit_code=exit_code,
            summary=summary,
            failures=failures,
            duration_seconds=elapsed,
            cached=False,
            digest=key.digest,
            components=dict(key.components),
            worker_count=int(workers),
            recorded_at=now_iso,
            confirmed=confirmed,
            reason=reason,
            stdout=stdout,
            stderr=stderr,
            slot=slot_info,
        )

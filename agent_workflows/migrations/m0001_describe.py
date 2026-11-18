"""Short-description normalization, validation, journal, and tool-less generation for m0001.

Implements spec 4sd62s Section 4.2 (SHORT DESCRIPTION, DESCRIPTION JOURNAL, SAFEGUARDS),
OQ-22, OQ-31, and C12 so the m0001 describe runner can validate generated ``short_description``
candidates, persist results in a locked crash-safe JSONL journal, and invoke OpenCode v1/v2
with all tools and permissions denied.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import warnings
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

from agent_workflows import (
    artifact_meta,
    attention_contract,
    lane_containment,
    leak_sanitizer,
    oc_models,
    opencode_cli,
    platform_lock,
    project_context,
    render_stream,
    runner_shared,
    verifier_corroboration,
)

_VALIDATION_VERB = "aw migrate metadata"
_FIELD_NAME = "short_description"

_LEADING_PUNCT = "`\"'([{<"
_TRAILING_PUNCT = "`\"'.,;:!?)]}>"
_WINDOWS_DRIVE_RE = re.compile(r"\b[A-Za-z]:[/\\]")


def normalize_description(text: str) -> str:
    """Strip surrounding whitespace and at most one matching pair of outer quotes."""
    cleaned = text.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in ('"', "'"):
        return cleaned[1:-1]
    return cleaned


def build_describe_ruleset(repo: Path) -> leak_sanitizer.Ruleset:
    """Build the writer leak-sanitizer ruleset once for a describe run."""
    return artifact_meta._writer_ruleset(Path(repo))


def _check_no_absolute_paths(text: str) -> str | None:
    """Refuse absolute POSIX (>=2 segments, excluding '//') or Windows drive tokens."""
    for token in text.split():
        stripped = token.lstrip(_LEADING_PUNCT).rstrip(_TRAILING_PUNCT)
        if not stripped:
            continue
        raw_parts = (
            (stripped, stripped.split("=", 1)[1]) if "=" in stripped else (stripped,)
        )
        for raw_part in raw_parts:
            cand = raw_part.lstrip(_LEADING_PUNCT).rstrip(_TRAILING_PUNCT)
            if not cand:
                continue
            if _WINDOWS_DRIVE_RE.search(cand):
                return (
                    f"{_VALIDATION_VERB}: {_FIELD_NAME} must not contain "
                    f"absolute Windows drive path: {token!r}"
                )
            if (
                cand.startswith("/")
                and not cand.startswith("//")
                and cand.count("/") >= 2
            ):
                return (
                    f"{_VALIDATION_VERB}: {_FIELD_NAME} must not contain "
                    f"absolute multi-segment path: {token!r}"
                )
    return None


def validate(
    text: str,
    repo: Path,
    *,
    ruleset: leak_sanitizer.Ruleset | None = None,
) -> str | None:
    """Validate a candidate ``short_description`` after quote/whitespace normalization.

    Returns ``None`` when ``text`` passes all checks, or the first refusal reason string:
    empty/blank text, descriptive-value safety (>300 chars, newlines, control chars),
    leak-sanitizer ``fail`` or ``warn`` findings, or absolute-path tokens.
    """
    cleaned = normalize_description(text)
    if not cleaned or not cleaned.strip():
        return f"{_VALIDATION_VERB}: {_FIELD_NAME} must not be empty"

    refusal = attention_contract.refuse_unsafe_descriptive(
        _VALIDATION_VERB, _FIELD_NAME, cleaned
    )
    if refusal is not None:
        return refusal

    active_ruleset = ruleset if ruleset is not None else build_describe_ruleset(repo)
    findings = leak_sanitizer.scan_text(
        cleaned, _FIELD_NAME, active_ruleset, include_warn=True
    )
    if findings:
        first = findings[0]
        return (
            f"{_VALIDATION_VERB}: {_FIELD_NAME} refused by leak sanitizer "
            f"({first.rule})"
        )

    return _check_no_absolute_paths(cleaned)


# ---------------------------------------------------------------------------
# E-01: Tracked prompt loader and delimiter-safe renderer
# ---------------------------------------------------------------------------

PROMPT_PATH: Path = (
    Path(__file__).resolve().parent.parent / "data" / "short-description-prompt.md"
)
_PROMPT_VERSION_RE = re.compile(r"^prompt-version:\s*(\d+)\s*$")
_OPEN_DELIM = "<<<RECORD"
_CLOSE_DELIM = "RECORD>>>"


def load_prompt() -> tuple[int, str, str]:
    """Load the tracked generation prompt, returning ``(version, template, prompt_digest)``.

    ``prompt_digest`` is the lowercase SHA-256 hex digest of the raw file bytes so any
    edit to ``agent_workflows/data/short-description-prompt.md`` invalidates cached
    journal entries automatically.
    """
    raw_bytes = PROMPT_PATH.read_bytes()
    prompt_digest = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8")
    lines = text.splitlines()
    if not lines:
        raise ValueError(f"short-description prompt file is empty: {PROMPT_PATH}")
    match = _PROMPT_VERSION_RE.match(lines[0])
    if not match:
        raise ValueError(
            f"short-description prompt must start with 'prompt-version: <int>': {PROMPT_PATH}"
        )
    version = int(match.group(1))
    template = "\n".join(lines[1:]).strip()
    return version, template, prompt_digest


def render_prompt(record_text: str) -> str:
    """Render ``record_text`` inside a delimiter-escaped ``<<<RECORD`` / ``RECORD>>>`` envelope."""
    _version, template, _digest = load_prompt()
    escaped = record_text.replace(_OPEN_DELIM, r"<<<\RECORD").replace(
        _CLOSE_DELIM, r"RECORD\>>>"
    )
    return f"{template}\n\n{_OPEN_DELIM}\n{escaped}\n{_CLOSE_DELIM}\n"


# ---------------------------------------------------------------------------
# E-02: Locked, crash-safe description journal
# ---------------------------------------------------------------------------

_JOURNAL_FILENAME = "descriptions.jsonl"
_LOCK_TIMEOUT_SECONDS = 10.0


def journal_path_for_repo(repo: Path | str) -> Path:
    """Resolve the gitignored description journal path under ``state_durable``."""
    ctx = project_context.resolve_project_context(target_repo=str(repo))
    state_durable = Path(ctx.physical_classes["state_durable"])
    return state_durable / "migrations" / "m0001" / _JOURNAL_FILENAME


def lock_path_for_journal(journal_path: Path | str) -> Path:
    """Return the dedicated sibling lock path for ``journal_path``.

    ``filelock`` opens its target with ``O_CREAT | O_TRUNC``, so locking ``descriptions.jsonl``
    directly would wipe the journal on the next acquire.
    """
    jp = Path(journal_path)
    return jp.with_name(f"{jp.name}.lock")


def read_journal(journal_path: Path | str) -> dict[str, dict[str, Any]]:
    """Read complete JSONL entries keyed by ``key``, taking the last entry per key.

    If a crash mid-write left a trailing partial line without a newline or with invalid
    JSON at EOF, discard only that trailing partial line while preserving all earlier entries.
    """
    jp = Path(journal_path)
    if not jp.is_file():
        return {}
    raw_text = jp.read_text(encoding="utf-8", errors="replace")
    lines = raw_text.splitlines(keepends=True)
    if not lines:
        return {}

    last = lines[-1]
    if not last.endswith("\n"):
        lines = lines[:-1]
    else:
        try:
            parsed_last = json.loads(last)
            if not isinstance(parsed_last, dict):
                lines = lines[:-1]
        except ValueError:
            lines = lines[:-1]

    entries: dict[str, dict[str, Any]] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        obj = json.loads(stripped)
        if isinstance(obj, dict) and isinstance(obj.get("key"), str):
            entries[obj["key"]] = obj
    return entries


def _trim_incomplete_trailing_line(fh: Any) -> None:
    """Trim an unterminated trailing line left by an interrupted write before appending."""
    fh.seek(0, os.SEEK_END)
    size = fh.tell()
    if size <= 0:
        return
    fh.seek(size - 1)
    if fh.read(1) == b"\n":
        fh.seek(0, os.SEEK_END)
        return
    fh.seek(0)
    data = fh.read()
    last_nl = data.rfind(b"\n")
    new_size = last_nl + 1 if last_nl >= 0 else 0
    fh.truncate(new_size)
    fh.seek(new_size)


def append_entry(journal_path: Path | str, entry: Mapping[str, Any]) -> None:
    """Lock the sibling ``.lock`` file, append one JSON line, flush, and ``os.fsync()``."""
    jp = Path(journal_path)
    jp.parent.mkdir(parents=True, exist_ok=True)
    lock_path = lock_path_for_journal(jp)
    payload = (json.dumps(dict(entry), ensure_ascii=False) + "\n").encode("utf-8")
    with platform_lock.held(lock_path, timeout=_LOCK_TIMEOUT_SECONDS):
        mode = "rb+" if jp.exists() else "wb"
        with jp.open(mode) as fh:
            if mode == "rb+":
                _trim_incomplete_trailing_line(fh)
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())


def lookup(
    journal_path: Path | str,
    key: str,
    source_digest: str,
    prompt_digest: str,
) -> dict[str, Any] | None:
    """Return the latest journal entry for ``key`` when both digests match, else ``None``."""
    entries = read_journal(journal_path)
    entry = entries.get(key)
    if entry is None:
        return None
    if (
        entry.get("source_digest") == source_digest
        and entry.get("prompt_digest") == prompt_digest
    ):
        return entry
    return None


class DescriptionJournal:
    """Locked JSONL journal facade bound to one ``descriptions.jsonl`` path."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    @classmethod
    def for_repo(cls, repo: Path | str) -> DescriptionJournal:
        return cls(journal_path_for_repo(repo))

    def read_all(self) -> dict[str, dict[str, Any]]:
        return read_journal(self.path)

    def append(self, entry: Mapping[str, Any]) -> None:
        append_entry(self.path, entry)

    def lookup(
        self, key: str, source_digest: str, prompt_digest: str
    ) -> dict[str, Any] | None:
        return lookup(self.path, key, source_digest, prompt_digest)


# ---------------------------------------------------------------------------
# E-03: Tool-less OpenCode v1/v2 config, argv, env, and policy verification
# ---------------------------------------------------------------------------

DESCRIBE_AGENT_NAME = "aw-describe"
COULD_NOT_ASK = runner_shared.PROBE_ANSWER_COULD_NOT_ASK
_DESCRIBE_TIMEOUT_SECONDS = 120.0
_POLICY_PROBE_TIMEOUT_SECONDS = 30.0

DescribeRunnerFn = Callable[
    [Sequence[str], str, str, Mapping[str, str], float], tuple[int, str, str]
]


class DescribeHostRefused(runner_shared.DriverError):
    """Raised when a requested host lacks a non-interactive tool-less mode (OQ-31)."""


class DescribePolicyResult(NamedTuple):
    """Outcome of pre-run tool-less agent policy verification."""

    ok: bool
    status: str
    detail: str


def _validate_describe_host(host: str) -> None:
    """Refuse hosts without a non-interactive tool-less mode (OQ-31)."""
    if host == "agy":
        raise DescribeHostRefused(
            "host 'agy' is refused for short-description generation (OQ-31): "
            "agy has no tool-less non-interactive mode"
        )
    if host != "oc":
        raise DescribeHostRefused(
            f"unsupported describe host {host!r} (OQ-31): only 'oc' is supported"
        )


def describe_argv(
    host: str,
    model: str | None = None,
    *,
    scratch_dir: Path | str,
    opencode: str = "opencode",
    major: int | None = None,
) -> list[str]:
    """Build the tool-less OpenCode argv (adapted for v1 vs v2), or refuse unsupported hosts."""
    _validate_describe_host(host)
    argv = [
        str(opencode),
        "run",
        "--format",
        "json",
        "--agent",
        DESCRIBE_AGENT_NAME,
        "--dir",
        str(scratch_dir),
    ]
    if model:
        argv.extend(["--model", str(model)])
    return opencode_cli.adapt_run_argv(argv, major=major)


def describe_env(base_env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Merge ``OPENCODE_CONFIG_CONTENT`` for OpenCode v1 tool denial while preserving operator keys."""
    env = dict(os.environ if base_env is None else base_env)
    # Strip inherited PWD so OpenCode v2 (Bun/Node) resolves .opencode/opencode.json from OS cwd
    # (scratch_dir) rather than the caller's checkout.
    env.pop("PWD", None)
    raw_operator = env.get(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV)
    policy_req = lane_containment.build_permission_policy_env(
        raw_operator, policy={"*": "deny"}
    )
    if policy_req.source == lane_containment.POLICY_SOURCE_OVERRIDE:
        msg = f"{lane_containment.OPENCODE_RUNTIME_CONFIG_ENV} {policy_req.note}"
        warnings.warn(msg, RuntimeWarning, stacklevel=2)
        sys.stderr.write(f"warning: {msg}\n")

    merged: dict[str, Any] = json.loads(policy_req.env_value)
    existing_agent = merged.get("agent")
    agent_map: dict[str, Any] = (
        dict(existing_agent) if isinstance(existing_agent, dict) else {}
    )
    agent_map[DESCRIBE_AGENT_NAME] = {
        "mode": "primary",
        "tools": {"*": False},
        "permission": {"*": "deny"},
    }
    merged["agent"] = agent_map
    env[lane_containment.OPENCODE_RUNTIME_CONFIG_ENV] = json.dumps(
        merged, sort_keys=True
    )
    return env


def write_v2_scratch_config(scratch_dir: Path | str) -> Path:
    """Write ``<scratch_dir>/.opencode/opencode.json`` (0o400 in 0o500 dir) for OpenCode v2."""
    scratch = Path(scratch_dir)
    oc_dir = scratch / ".opencode"
    if oc_dir.exists():
        os.chmod(oc_dir, 0o700)
    else:
        oc_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    cfg_path = oc_dir / "opencode.json"
    if cfg_path.exists():
        os.chmod(cfg_path, 0o600)

    payload = {
        "agents": {
            DESCRIBE_AGENT_NAME: {
                "mode": "primary",
                "permissions": [{"action": "*", "resource": "*", "effect": "deny"}],
            }
        },
        "permissions": [{"action": "*", "resource": "*", "effect": "deny"}],
    }
    cfg_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.chmod(cfg_path, 0o400)
    os.chmod(oc_dir, 0o500)
    return cfg_path


def _check_v2_policy_payload(payload: Any) -> DescribePolicyResult:
    if not isinstance(payload, list):
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"opencode debug agents returned non-list JSON; observed: {payload!r}",
        )
    target: Mapping[str, Any] | None = None
    seen_ids: list[Any] = []
    for item in payload:
        if isinstance(item, Mapping):
            seen_ids.append(item.get("id"))
            if item.get("id") == DESCRIBE_AGENT_NAME:
                target = item
                break
    if target is None:
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"agent {DESCRIBE_AGENT_NAME!r} absent from opencode debug agents; observed ids: {seen_ids!r}",
        )
    perms = target.get("permissions")
    if not isinstance(perms, list):
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"agent {DESCRIBE_AGENT_NAME!r} has non-list permissions; observed: {perms!r}",
        )
    deny_indices = [
        idx
        for idx, rule in enumerate(perms)
        if isinstance(rule, Mapping)
        and rule.get("action") == "*"
        and rule.get("resource") == "*"
        and rule.get("effect") == "deny"
    ]
    if not deny_indices:
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"agent {DESCRIBE_AGENT_NAME!r} lacks wildcard deny permission; observed: {perms!r}",
        )
    last_deny = deny_indices[-1]
    for rule in perms[last_deny + 1 :]:
        if not isinstance(rule, Mapping):
            return DescribePolicyResult(
                False,
                COULD_NOT_ASK,
                f"invalid trailing permission entry after wildcard deny; observed: {perms!r}",
            )
        if (
            rule.get("effect") in ("allow", "ask")
            and rule.get("action") != "external_directory"
        ):
            return DescribePolicyResult(
                False,
                COULD_NOT_ASK,
                f"agent {DESCRIBE_AGENT_NAME!r} permits {rule.get('action')!r} "
                f"({rule.get('effect')!r}) after wildcard deny; observed: {perms!r}",
            )
    return DescribePolicyResult(
        True,
        "verified",
        f"opencode v2 {DESCRIBE_AGENT_NAME} policy verified ({len(perms)} permission rules)",
    )


def _check_v1_policy_payload(payload: Any) -> DescribePolicyResult:
    if not isinstance(payload, Mapping):
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"opencode debug agent returned non-object JSON; observed: {payload!r}",
        )
    tools = payload.get("tools")
    if (
        not isinstance(tools, Mapping)
        or not tools
        or not all(val is False for val in tools.values())
    ):
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"agent {DESCRIBE_AGENT_NAME!r} has enabled or empty tools map; observed tools: {tools!r}",
        )
    perms = payload.get("permission")
    if not isinstance(perms, list):
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"agent {DESCRIBE_AGENT_NAME!r} has non-list permission rules; observed: {perms!r}",
        )
    deny_indices = [
        idx
        for idx, rule in enumerate(perms)
        if isinstance(rule, Mapping)
        and rule.get("permission") == "*"
        and rule.get("action") == "deny"
    ]
    if not deny_indices:
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"agent {DESCRIBE_AGENT_NAME!r} lacks wildcard deny permission rule; observed: {perms!r}",
        )
    last_deny = deny_indices[-1]
    for rule in perms[last_deny + 1 :]:
        if not isinstance(rule, Mapping):
            return DescribePolicyResult(
                False,
                COULD_NOT_ASK,
                f"invalid trailing permission entry after wildcard deny; observed: {perms!r}",
            )
        if (
            rule.get("action") in ("allow", "ask")
            and rule.get("permission") != "external_directory"
        ):
            return DescribePolicyResult(
                False,
                COULD_NOT_ASK,
                f"agent {DESCRIBE_AGENT_NAME!r} permits {rule.get('permission')!r} "
                f"({rule.get('action')!r}) after wildcard deny; observed: {perms!r}",
            )
    return DescribePolicyResult(
        True,
        "verified",
        f"opencode v1 {DESCRIBE_AGENT_NAME} policy verified ({len(tools)} tools false)",
    )


def verify_describe_policy(
    host: str,
    *,
    scratch_dir: Path | str,
    env: Mapping[str, str],
    opencode: str = "opencode",
    runner: DescribeRunnerFn | None = None,
    major: int | None = None,
) -> DescribePolicyResult:
    """Verify via ``opencode debug`` that ``aw-describe`` has all tools and permissions denied."""
    _validate_describe_host(host)

    scratch = Path(scratch_dir)
    is_v2_mode = opencode_cli.is_v2(str(opencode), major=major)
    if is_v2_mode:
        argv = [str(opencode), "debug", "agents"]
    else:
        argv = [
            str(opencode),
            "debug",
            "agent",
            DESCRIBE_AGENT_NAME,
            "--dir",
            str(scratch),
        ]

    try:
        if runner is not None:
            exit_code, stdout, stderr = runner(
                argv, str(scratch), "", dict(env), _POLICY_PROBE_TIMEOUT_SECONDS
            )
        else:
            runner_shared._assert_probe_spawn_is_permitted(argv)
            spawn_env = dict(env)
            spawn_env.pop("PWD", None)
            proc = subprocess.run(  # noqa: S603 - fixed argv, shell=False
                argv,
                cwd=str(scratch),
                env=spawn_env,
                capture_output=True,
                text=True,
                timeout=_POLICY_PROBE_TIMEOUT_SECONDS,
                shell=False,
                check=False,
            )
            exit_code, stdout, stderr = (
                proc.returncode,
                proc.stdout or "",
                proc.stderr or "",
            )
    except subprocess.TimeoutExpired:
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"policy probe timed out after {_POLICY_PROBE_TIMEOUT_SECONDS:.0f}s",
        )
    except OSError as exc:
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"policy probe could not spawn ({type(exc).__name__}: {exc})",
        )

    if int(exit_code) != 0:
        observed = (stderr or stdout or "").strip()
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"policy probe exited {exit_code}; observed: {observed!r}",
        )

    try:
        payload = json.loads(stdout)
    except ValueError as exc:
        return DescribePolicyResult(
            False,
            COULD_NOT_ASK,
            f"policy probe emitted non-JSON output ({exc}); observed: {stdout.strip()!r}",
        )

    return (
        _check_v2_policy_payload(payload)
        if is_v2_mode
        else _check_v1_policy_payload(payload)
    )


# ---------------------------------------------------------------------------
# E-04: 0o500 scratch directory lifecycle and guarded generate()
# ---------------------------------------------------------------------------

_CONTENT_FILTER_MARKERS = (
    "content-filter",
    "content_filter",
    "content filter",
    "content_policy",
    "content policy",
)
_CONTEXT_LIMIT_MARKERS = (
    "context_length",
    "context-length",
    "context length",
    "context window",
    "token limit",
    "max_tokens",
    "max tokens",
    "maximum context",
    "too many tokens",
    "prompt is too long",
    "input is too long",
    "exceeds the maximum",
)


@dataclass(frozen=True)
class GenerateResult:
    """Result of a single tool-less description generation attempt."""

    status: str  # "ok" | "failed" | "could-not-ask"
    text: str | None
    cost: float = 0.0
    tokens: int = 0
    model: str | None = None
    failure: str | None = None
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def _restore_and_remove_scratch(scratch_dir: Path) -> None:
    """Restore writable permissions on scratch files/dirs before removing the tree."""
    oc_dir = scratch_dir / ".opencode"
    cfg_path = oc_dir / "opencode.json"
    with contextlib.suppress(OSError):
        if scratch_dir.exists():
            os.chmod(scratch_dir, 0o700)
    with contextlib.suppress(OSError):
        if oc_dir.exists():
            os.chmod(oc_dir, 0o700)
    with contextlib.suppress(OSError):
        if cfg_path.exists():
            os.chmod(cfg_path, 0o600)
    shutil.rmtree(scratch_dir)


def _classify_input_rejection(err_name: str, err_msg: str) -> str | None:
    combined = f"{err_name} {err_msg}".lower()
    if any(marker in combined for marker in _CONTENT_FILTER_MARKERS):
        return "content-filter"
    if any(marker in combined for marker in _CONTEXT_LIMIT_MARKERS):
        return "context-length"
    return None


def _extract_step_tokens(part: Mapping[str, Any]) -> int:
    tokens_obj = part.get("tokens")
    if not isinstance(tokens_obj, Mapping):
        return 0
    total = tokens_obj.get("total")
    if isinstance(total, (int, float)) and not isinstance(total, bool):
        return int(total)
    total_sum = 0
    for key in ("input", "output", "reasoning"):
        val = tokens_obj.get(key)
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            total_sum += int(val)
    cache_val = tokens_obj.get("cache")
    if isinstance(cache_val, Mapping):
        for ckey in ("read", "write"):
            cval = cache_val.get(ckey)
            if isinstance(cval, (int, float)) and not isinstance(cval, bool):
                total_sum += int(cval)
    elif isinstance(cache_val, (int, float)) and not isinstance(cache_val, bool):
        total_sum += int(cache_val)
    return total_sum


def generate(
    record_text: str,
    *,
    journal_dir: Path | str,
    host: str = "oc",
    model: str | None = None,
    base_env: Mapping[str, str] | None = None,
    opencode: str = "opencode",
    runner: DescribeRunnerFn | None = None,
    major: int | None = None,
) -> GenerateResult:
    """Run one tool-less OpenCode generation call inside a ``0o500`` scratch directory."""
    _validate_describe_host(host)
    j_dir = Path(journal_dir)
    j_dir.mkdir(parents=True, exist_ok=True)
    scratch_dir = Path(tempfile.mkdtemp(prefix="describe-scratch-", dir=str(j_dir)))

    try:
        write_v2_scratch_config(scratch_dir)
        argv = describe_argv(
            host,
            model,
            scratch_dir=scratch_dir,
            opencode=opencode,
            major=major,
        )
        env = describe_env(base_env)
        stdin_text = render_prompt(record_text)
        os.chmod(scratch_dir, 0o500)

        try:
            if runner is not None:
                exit_code, stdout, stderr = runner(
                    list(argv),
                    str(scratch_dir),
                    stdin_text,
                    env,
                    _DESCRIBE_TIMEOUT_SECONDS,
                )
            else:
                runner_shared._assert_probe_spawn_is_permitted(argv)
                spawn_env = dict(env)
                spawn_env.pop("PWD", None)
                proc = subprocess.run(  # noqa: S603 - fixed argv, shell=False
                    list(argv),
                    input=stdin_text,
                    cwd=str(scratch_dir),
                    env=spawn_env,
                    capture_output=True,
                    text=True,
                    timeout=_DESCRIBE_TIMEOUT_SECONDS,
                    shell=False,
                    check=False,
                )
                exit_code, stdout, stderr = (
                    proc.returncode,
                    proc.stdout or "",
                    proc.stderr or "",
                )
        except subprocess.TimeoutExpired:
            exit_code, stdout, stderr = (
                124,
                "",
                f"describe call timed out after {_DESCRIBE_TIMEOUT_SECONDS:.0f}s",
            )
        except OSError as exc:
            exit_code, stdout, stderr = 127, "", f"describe spawn failed: {exc}"
    finally:
        _restore_and_remove_scratch(scratch_dir)

    total_cost = 0.0
    total_tokens = 0
    saw_tool_use = False
    input_rejection_reason: str | None = None
    other_host_error: str | None = None
    observed_model = model

    for raw_line in (stdout or "").splitlines():
        line = raw_line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if not isinstance(ev, dict):
            continue

        norm_ev = opencode_cli.normalize_event(ev)
        if verifier_corroboration.tool_call_from_event(norm_ev) is not None or ev.get(
            "type"
        ) in ("tool_use", "tool"):
            saw_tool_use = True

        if ev.get("type") == "step_finish":
            part = ev.get("part")
            part_map: Mapping[str, Any] = part if isinstance(part, Mapping) else {}
            cost_val = part_map.get("cost")
            if isinstance(cost_val, (int, float)) and not isinstance(cost_val, bool):
                total_cost += float(cost_val)
            total_tokens += _extract_step_tokens(part_map)
            reason = (
                str(part_map.get("reason") or ev.get("reason") or "").strip().lower()
            )
            if reason in ("content-filter", "content_filter"):
                input_rejection_reason = "content-filter"
            if observed_model is None:
                mid = part_map.get("modelID") or ev.get("model")
                if isinstance(mid, str) and mid.strip():
                    observed_model = mid.strip()

        host_err = render_stream.host_error_of_event(ev)
        if host_err is not None:
            err_name, err_msg = host_err
            rejection = _classify_input_rejection(err_name, err_msg)
            if rejection is not None:
                input_rejection_reason = rejection
            else:
                other_host_error = f"{err_name}: {err_msg}".strip(": ")

    if saw_tool_use:
        return GenerateResult(
            status="failed",
            text=None,
            cost=total_cost,
            tokens=total_tokens,
            model=observed_model,
            failure="tool-use",
            detail="model emitted a tool event under tool-less policy",
        )

    if int(exit_code) in (124, 127):
        return GenerateResult(
            status=COULD_NOT_ASK,
            text=None,
            cost=total_cost,
            tokens=total_tokens,
            model=observed_model,
            detail=(stderr or "").strip() or f"describe exited {exit_code}",
        )

    if input_rejection_reason is not None:
        return GenerateResult(
            status="failed",
            text=None,
            cost=total_cost,
            tokens=total_tokens,
            model=observed_model,
            failure=input_rejection_reason,
            detail=f"host rejected input ({input_rejection_reason})",
        )

    if other_host_error is not None:
        return GenerateResult(
            status=COULD_NOT_ASK,
            text=None,
            cost=total_cost,
            tokens=total_tokens,
            model=observed_model,
            detail=other_host_error,
        )

    if int(exit_code) != 0:
        return GenerateResult(
            status=COULD_NOT_ASK,
            text=None,
            cost=total_cost,
            tokens=total_tokens,
            model=observed_model,
            detail=(stderr or "").strip() or f"describe exited {exit_code}",
        )

    reply_text = runner_shared.probe_reply_text(stdout or "", host="oc")
    if not reply_text or not reply_text.strip():
        return GenerateResult(
            status=COULD_NOT_ASK,
            text=None,
            cost=total_cost,
            tokens=total_tokens,
            model=observed_model,
            detail=(stderr or "").strip() or "empty reply from model",
        )

    return GenerateResult(
        status="ok",
        text=reply_text,
        cost=total_cost,
        tokens=total_tokens,
        model=observed_model,
    )


# ---------------------------------------------------------------------------
# E-06: Regenerate-once orchestrator over validate() and DescriptionJournal
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DescribeRecordResult:
    """Outcome of describing one record through the journal and regenerate-once rule."""

    status: str  # "generated" | "reused" | "failed" | "could-not-ask"
    text: str | None
    failure: str | None = None
    entry: dict[str, Any] | None = None
    cost: float = 0.0
    tokens: int = 0
    calls: int = 0
    detail: str = ""


def describe_record(
    key: str,
    record_bytes: bytes,
    *,
    repo: Path | str,
    journal_dir: Path | str,
    host: str = "oc",
    model: str | None = None,
    recorded_model: str | None = None,
    ruleset: leak_sanitizer.Ruleset | None = None,
    base_env: Mapping[str, str] | None = None,
    opencode: str = "opencode",
    runner: DescribeRunnerFn | None = None,
    major: int | None = None,
    skip_lookup: bool = False,
) -> DescribeRecordResult:
    """Describe one record via journal reuse, tool-less generation, validation, and 1 retry."""
    repo_path = Path(repo)
    j_dir = Path(journal_dir)
    j_path = j_dir / _JOURNAL_FILENAME

    source_digest = hashlib.sha256(record_bytes).hexdigest()
    prompt_version, _template, prompt_digest = load_prompt()

    if not skip_lookup:
        cached = lookup(j_path, key, source_digest, prompt_digest)
        if cached is not None:
            cached_text = cached.get("text")
            return DescribeRecordResult(
                status="reused" if cached_text is not None else "failed",
                text=cached_text,
                failure=cached.get("failure"),
                entry=dict(cached),
                cost=0.0,
                tokens=0,
                calls=0,
            )

    record_text = record_bytes.decode("utf-8", errors="replace")
    active_ruleset = ruleset
    total_cost = 0.0
    total_tokens = 0
    calls = 0
    last_failure = ""
    last_model = model

    for attempt in (1, 2):
        calls += 1
        gen = generate(
            record_text,
            journal_dir=j_dir,
            host=host,
            model=model,
            base_env=base_env,
            opencode=opencode,
            runner=runner,
            major=major,
        )
        total_cost += gen.cost
        total_tokens += gen.tokens
        if gen.model is not None:
            last_model = gen.model

        if gen.status == COULD_NOT_ASK:
            return DescribeRecordResult(
                status=COULD_NOT_ASK,
                text=None,
                failure=None,
                entry=None,
                cost=total_cost,
                tokens=total_tokens,
                calls=calls,
                detail=gen.detail,
            )

        if gen.status == "failed":
            last_failure = gen.failure or "generation-failed"
            continue

        cleaned = normalize_description(gen.text or "")
        if active_ruleset is None:
            active_ruleset = build_describe_ruleset(repo_path)
        refusal = validate(cleaned, repo_path, ruleset=active_ruleset)
        effective_model = last_model if last_model is not None else recorded_model
        if refusal is None:
            entry: dict[str, Any] = {
                "key": key,
                "text": cleaned,
                "host": host,
                "model": effective_model,
                "prompt_version": prompt_version,
                "prompt_digest": prompt_digest,
                "source_digest": source_digest,
                "generated_at": runner_shared.utc_now(),
                "attempts": attempt,
            }
            append_entry(j_path, entry)
            return DescribeRecordResult(
                status="generated",
                text=cleaned,
                failure=None,
                entry=entry,
                cost=total_cost,
                tokens=total_tokens,
                calls=calls,
            )

        last_failure = refusal

    effective_model = last_model if last_model is not None else recorded_model
    failed_entry: dict[str, Any] = {
        "key": key,
        "text": None,
        "failure": last_failure,
        "host": host,
        "model": effective_model,
        "prompt_version": prompt_version,
        "prompt_digest": prompt_digest,
        "source_digest": source_digest,
        "generated_at": runner_shared.utc_now(),
        "attempts": 2,
    }
    append_entry(j_path, failed_entry)
    return DescribeRecordResult(
        status="failed",
        text=None,
        failure=last_failure,
        entry=failed_entry,
        cost=total_cost,
        tokens=total_tokens,
        calls=calls,
    )


# ---------------------------------------------------------------------------
# E-07: Describer facade and describe_all batch runner
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DescribeTarget:
    """One convertible record queued for short-description lookup or generation."""

    key: str
    rel_path: str
    record_bytes: bytes
    id6: str = ""
    new_rel: str | None = None


@dataclass(frozen=True)
class DescribeAllResult:
    """Aggregate outcome of running ``describe_all`` across migration records."""

    enabled: bool
    host: str
    model: str
    prompt_version: int
    prompt_digest: str
    total_records: int
    generated: int
    reused: int
    failed: int
    could_not_ask: int
    limit_skipped: int
    calls: int
    total_cost: float
    mean_cost_per_call: float
    total_tokens: int
    total_seconds: float
    summary_line: str
    descriptions: dict[str, dict[str, Any]]
    deliberate_absences: dict[str, str]
    lacking_description: tuple[str, ...]
    records: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize summary metrics (without large text blobs) for journal/report output."""
        return {
            "enabled": self.enabled,
            "host": self.host,
            "model": self.model,
            "prompt_version": self.prompt_version,
            "prompt_digest": self.prompt_digest,
            "total_records": self.total_records,
            "generated": self.generated,
            "reused": self.reused,
            "failed": self.failed,
            "could_not_ask": self.could_not_ask,
            "limit_skipped": self.limit_skipped,
            "calls": self.calls,
            "total_cost": self.total_cost,
            "mean_cost_per_call": self.mean_cost_per_call,
            "total_tokens": self.total_tokens,
            "total_seconds": self.total_seconds,
            "summary_line": self.summary_line,
            "deliberate_absences": dict(self.deliberate_absences),
            "lacking_description": list(self.lacking_description),
            "records": list(self.records),
        }


class Describer:
    """Configured short-description generator passed into ``m0001`` migration runs."""

    def __init__(
        self,
        *,
        host: str = "oc",
        model: str | None = None,
        limit: int | None = None,
        enabled: bool = True,
        base_env: Mapping[str, str] | None = None,
        opencode: str = "opencode",
        runner: DescribeRunnerFn | None = None,
        major: int | None = None,
        progress_fn: Callable[[str], None] | None = None,
    ) -> None:
        if limit is not None and (isinstance(limit, bool) or int(limit) <= 0):
            raise ValueError(
                f"--describe-limit must be a positive integer, got {limit!r}"
            )
        self.host = host
        self.model = model.strip() if isinstance(model, str) and model.strip() else None
        self.limit = int(limit) if limit is not None else None
        self.enabled = bool(enabled)
        self.base_env = dict(base_env) if base_env is not None else None
        self.opencode = opencode
        self.runner = runner
        self.major = major
        self.progress_fn = progress_fn

    def validate_host(self, scratch_dir: Path | str = ".") -> None:
        """Validate host via ``describe_argv`` before preflight or scratch writes."""
        describe_argv(
            self.host,
            self.model,
            scratch_dir=scratch_dir,
            opencode=self.opencode,
            major=self.major,
        )

    def resolve_model(
        self, repo: Path | str, *, child_env: Mapping[str, str] | None = None
    ) -> tuple[str | None, str]:
        """Return ``(cli_model_arg, recorded_model_label)`` resolved once per run."""
        if self.model is not None:
            return self.model, self.model
        env_for_probe = (
            child_env if child_env is not None else describe_env(self.base_env)
        )
        default = oc_models.resolve_host_default_model(
            env=env_for_probe,
            cwd=Path(repo),
            agent=DESCRIBE_AGENT_NAME,
        )
        label = default.model if default.resolved else "host-default"
        return None, label


def _coerce_describe_target(item: Any) -> DescribeTarget:
    if isinstance(item, DescribeTarget):
        return item
    if isinstance(item, Mapping):
        key = str(item["key"])
        rel_path = str(item.get("rel_path") or key)
        raw = item.get("record_bytes")
        if raw is None and item.get("path") is not None:
            raw = Path(item["path"]).read_bytes()
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        return DescribeTarget(
            key=key,
            rel_path=rel_path,
            record_bytes=bytes(raw or b""),
            id6=str(item.get("id6") or ""),
            new_rel=str(item["new_rel"]) if item.get("new_rel") else None,
        )
    if isinstance(item, tuple) and len(item) == 2:
        key, raw = item
        raw_b = raw.encode("utf-8") if isinstance(raw, str) else bytes(raw)
        return DescribeTarget(key=str(key), rel_path=str(key), record_bytes=raw_b)
    raise TypeError(f"Unsupported describe_all target: {type(item).__name__}")


def _verify_policy_for_run(
    host: str,
    *,
    journal_dir: Path,
    child_env: Mapping[str, str],
    opencode: str,
    runner: DescribeRunnerFn | None,
    major: int | None,
) -> DescribePolicyResult:
    """Create a temporary ``0o500`` policy scratch dir, verify policy, and clean up."""
    journal_dir.mkdir(parents=True, exist_ok=True)
    policy_scratch = Path(
        tempfile.mkdtemp(prefix="describe-policy-", dir=str(journal_dir))
    )
    try:
        write_v2_scratch_config(policy_scratch)
        os.chmod(policy_scratch, 0o500)
        return verify_describe_policy(
            host,
            scratch_dir=policy_scratch,
            env=child_env,
            opencode=opencode,
            runner=runner,
            major=major,
        )
    finally:
        _restore_and_remove_scratch(policy_scratch)


def describe_all(
    records: Sequence[Any],
    *,
    repo: Path | str,
    journal_dir: Path | str | None = None,
    describer: Describer | None = None,
    host: str = "oc",
    model: str | None = None,
    limit: int | None = None,
    enabled: bool = True,
    base_env: Mapping[str, str] | None = None,
    opencode: str = "opencode",
    runner: DescribeRunnerFn | None = None,
    major: int | None = None,
    progress_fn: Callable[[str], None] | None = None,
) -> DescribeAllResult:
    """Look up, lazily verify policy, and generate descriptions in stable path order."""
    eff = (
        describer
        if describer is not None
        else Describer(
            host=host,
            model=model,
            limit=limit,
            enabled=enabled,
            base_env=base_env,
            opencode=opencode,
            runner=runner,
            major=major,
            progress_fn=progress_fn,
        )
    )
    emit_progress = progress_fn if progress_fn is not None else eff.progress_fn

    repo_path = Path(repo)
    j_dir = (
        Path(journal_dir)
        if journal_dir is not None
        else journal_path_for_repo(repo_path).parent
    )
    j_path = j_dir / _JOURNAL_FILENAME

    targets = sorted(
        (_coerce_describe_target(item) for item in records),
        key=lambda t: t.rel_path,
    )
    prompt_version, _template, prompt_digest = load_prompt()
    child_env = describe_env(eff.base_env)
    cli_model, recorded_model = eff.resolve_model(repo_path, child_env=child_env)

    if not eff.enabled:
        lacking = tuple(t.rel_path for t in targets)
        summary_line = (
            "Descriptions: skipped (--no-describe; "
            f"0 generated, {len(targets)} undescribed)"
        )
        return DescribeAllResult(
            enabled=False,
            host=eff.host,
            model=recorded_model,
            prompt_version=prompt_version,
            prompt_digest=prompt_digest,
            total_records=len(targets),
            generated=0,
            reused=0,
            failed=0,
            could_not_ask=0,
            limit_skipped=len(targets),
            calls=0,
            total_cost=0.0,
            mean_cost_per_call=0.0,
            total_tokens=0,
            total_seconds=0.0,
            summary_line=summary_line,
            descriptions={},
            deliberate_absences={},
            lacking_description=lacking,
            records=(),
        )

    eff.validate_host(j_dir)
    existing_journal = read_journal(j_path)

    generated = 0
    reused = 0
    failed = 0
    could_not_ask = 0
    limit_skipped = 0
    uncached_attempted = 0
    total_calls = 0
    total_cost = 0.0
    total_tokens = 0
    total_seconds = 0.0

    descriptions: dict[str, dict[str, Any]] = {}
    deliberate_absences: dict[str, str] = {}
    lacking_list: list[str] = []
    record_rows: list[dict[str, Any]] = []

    policy_checked = False
    policy_ok = True
    policy_detail = ""
    active_ruleset: leak_sanitizer.Ruleset | None = None

    total_count = len(targets)
    for idx, target in enumerate(targets, start=1):
        source_digest = hashlib.sha256(target.record_bytes).hexdigest()
        cached = existing_journal.get(target.key)
        if (
            cached is not None
            and cached.get("source_digest") == source_digest
            and cached.get("prompt_digest") == prompt_digest
        ):
            cached_text = cached.get("text")
            if isinstance(cached_text, str) and cached_text.strip():
                reused += 1
                descriptions[target.key] = {
                    "short_description": cached_text,
                    "description_source": "generated",
                    "description_model": str(cached.get("model") or recorded_model),
                    "description_prompt_version": str(
                        cached.get("prompt_version") or prompt_version
                    ),
                }
                record_rows.append(
                    {
                        "key": target.key,
                        "rel_path": target.rel_path,
                        "bytes": len(target.record_bytes),
                        "tokens": 0,
                        "cost": 0.0,
                        "seconds": 0.0,
                        "status": "reused",
                        "failure": None,
                        "calls": 0,
                    }
                )
            else:
                failed += 1
                reason = str(cached.get("failure") or "failed")
                deliberate_absences[target.key] = reason
                record_rows.append(
                    {
                        "key": target.key,
                        "rel_path": target.rel_path,
                        "bytes": len(target.record_bytes),
                        "tokens": 0,
                        "cost": 0.0,
                        "seconds": 0.0,
                        "status": "failed",
                        "failure": reason,
                        "calls": 0,
                    }
                )
        elif eff.limit is not None and uncached_attempted >= eff.limit:
            limit_skipped += 1
            lacking_list.append(target.rel_path)
            record_rows.append(
                {
                    "key": target.key,
                    "rel_path": target.rel_path,
                    "bytes": len(target.record_bytes),
                    "tokens": 0,
                    "cost": 0.0,
                    "seconds": 0.0,
                    "status": "limit-skipped",
                    "failure": None,
                    "calls": 0,
                }
            )
        else:
            uncached_attempted += 1
            if not policy_checked:
                policy_checked = True
                if eff.runner is None:
                    try:
                        probe_argv = describe_argv(
                            eff.host,
                            cli_model,
                            scratch_dir=j_dir,
                            opencode=eff.opencode,
                            major=eff.major,
                        )
                        runner_shared._assert_probe_spawn_is_permitted(probe_argv)
                    except runner_shared.DriverError as exc:
                        policy_ok = False
                        policy_detail = f"pytest-spawn-refused: {exc}"
                if policy_ok:
                    pol = _verify_policy_for_run(
                        eff.host,
                        journal_dir=j_dir,
                        child_env=child_env,
                        opencode=eff.opencode,
                        runner=eff.runner,
                        major=eff.major,
                    )
                    if not pol.ok:
                        policy_ok = False
                        policy_detail = pol.detail

            if not policy_ok:
                could_not_ask += 1
                lacking_list.append(target.rel_path)
                record_rows.append(
                    {
                        "key": target.key,
                        "rel_path": target.rel_path,
                        "bytes": len(target.record_bytes),
                        "tokens": 0,
                        "cost": 0.0,
                        "seconds": 0.0,
                        "status": COULD_NOT_ASK,
                        "failure": None,
                        "detail": policy_detail,
                        "calls": 0,
                    }
                )
            else:
                if active_ruleset is None:
                    active_ruleset = build_describe_ruleset(repo_path)
                t0 = time.monotonic()
                rec_res = describe_record(
                    target.key,
                    target.record_bytes,
                    repo=repo_path,
                    journal_dir=j_dir,
                    host=eff.host,
                    model=cli_model,
                    recorded_model=recorded_model,
                    ruleset=active_ruleset,
                    base_env=eff.base_env,
                    opencode=eff.opencode,
                    runner=eff.runner,
                    major=eff.major,
                    skip_lookup=True,
                )
                elapsed = time.monotonic() - t0
                total_seconds += elapsed
                total_cost += rec_res.cost
                total_tokens += rec_res.tokens
                total_calls += rec_res.calls

                if rec_res.status == "generated" and rec_res.text is not None:
                    generated += 1
                    entry_map = rec_res.entry or {}
                    descriptions[target.key] = {
                        "short_description": rec_res.text,
                        "description_source": "generated",
                        "description_model": str(
                            entry_map.get("model") or recorded_model
                        ),
                        "description_prompt_version": str(
                            entry_map.get("prompt_version") or prompt_version
                        ),
                    }
                    if entry_map:
                        existing_journal[target.key] = dict(entry_map)
                elif rec_res.status == "failed":
                    failed += 1
                    reason = rec_res.failure or "failed"
                    deliberate_absences[target.key] = reason
                    if rec_res.entry:
                        existing_journal[target.key] = dict(rec_res.entry)
                else:
                    could_not_ask += 1
                    lacking_list.append(target.rel_path)

                record_rows.append(
                    {
                        "key": target.key,
                        "rel_path": target.rel_path,
                        "bytes": len(target.record_bytes),
                        "tokens": rec_res.tokens,
                        "cost": rec_res.cost,
                        "seconds": elapsed,
                        "status": rec_res.status,
                        "failure": rec_res.failure,
                        "detail": rec_res.detail,
                        "calls": rec_res.calls,
                    }
                )

        if emit_progress is not None and idx % 50 == 0:
            emit_progress(
                f"Descriptions progress: {idx}/{total_count} "
                f"(generated={generated}, reused={reused}, failed={failed}, "
                f"could-not-ask={could_not_ask})"
            )

    mean_cost = (total_cost / total_calls) if total_calls > 0 else 0.0
    summary_line = (
        f"Descriptions: generated={generated}, reused={reused}, failed={failed}, "
        f"could-not-ask={could_not_ask}, total cost={total_cost:.6f}, "
        f"mean cost per call={mean_cost:.6f}"
    )
    if limit_skipped:
        summary_line += f", limit-skipped={limit_skipped}"
    if emit_progress is not None:
        emit_progress(summary_line)

    return DescribeAllResult(
        enabled=True,
        host=eff.host,
        model=recorded_model,
        prompt_version=prompt_version,
        prompt_digest=prompt_digest,
        total_records=total_count,
        generated=generated,
        reused=reused,
        failed=failed,
        could_not_ask=could_not_ask,
        limit_skipped=limit_skipped,
        calls=total_calls,
        total_cost=total_cost,
        mean_cost_per_call=mean_cost,
        total_tokens=total_tokens,
        total_seconds=total_seconds,
        summary_line=summary_line,
        descriptions=descriptions,
        deliberate_absences=deliberate_absences,
        lacking_description=tuple(lacking_list),
        records=tuple(record_rows),
    )

#!/usr/bin/env python3
"""Sync OpenCode provider model lists and pricing from the user's OWN configured gateways.

`aw oc update-models` reads the OpenCode config that OpenCode itself would load, discovers
every OpenAI-compatible provider declared THERE, and refreshes each provider's `models`
block (ids plus `input`/`output`/`cache_read`/`cache_write` cost, in $ per MILLION tokens)
from that provider's own gateway. No gateway host is hardcoded: reading one user's config
finds their gateway, reading another's finds theirs (GUIDING_PRINCIPLES P7).

Pricing comes from the LiteLLM proxy admin endpoints (`/model/info`, falling back to
`/model_group/info`), which report cost PER TOKEN. Providers whose base URL exposes neither
endpoint (plain OpenAI, Google Gemini, and any other gateway without a LiteLLM pricing API)
are reported as skipped and left byte-identical rather than guessed at.

Safety posture (ocsync-01 g7hljt, hardened by /plan-review):
- Preview by default; `--apply` is required to write anything.
- The bearer key is sent over https ONLY. A non-https base URL is skipped without issuing a
  request unless the caller passes `--allow-insecure`, and even then only to a loopback host.
- The API key, the Authorization header, and key-file contents never appear in any output,
  diff, log, exception message, or machine record.
- Writes are atomic (temp file + os.replace) with a timestamped backup taken BEFORE the
  replace, so an interrupted run cannot truncate the file that gates the user's whole tool.
- A `.jsonc` (or otherwise unparseable) config is UNSUPPORTED-FOR-WRITE: stdlib json cannot
  round-trip comments, so it is reported and skipped instead of silently destroying content.
- Formatting is NOT byte-preserved on `--apply`: the file's existing indent width is detected
  and reused, but the output is normalized JSON. This is stated in --help rather than overclaimed.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Tuple

# Endpoints probed for pricing, in order. Both are LiteLLM proxy admin routes; the first is a
# superset (it carries cache-token pricing), the second is the narrower per-group summary.
PRICING_PATHS: Tuple[str, ...] = ("/model/info", "/model_group/info")

# Cost keys as LiteLLM reports them (per token) mapped to the opencode `cost` keys ($/M tokens).
_COST_FIELDS: Tuple[Tuple[str, str], ...] = (
    ("input", "input_cost_per_token"),
    ("cache_read", "cache_read_input_token_cost"),
    ("cache_write", "cache_creation_input_token_cost"),
    ("output", "output_cost_per_token"),
)

_OPENAI_COMPATIBLE_NPM = "@ai-sdk/openai-compatible"
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "[::1]"})

# Reasons a provider was not synced. Surfaced verbatim to the user so a skip is never silent.
SKIP_NO_BASEURL = "no baseURL in provider options"
SKIP_INSECURE = "baseURL is not https (pass --allow-insecure for a loopback host)"
SKIP_INSECURE_NONLOOPBACK = (
    "refusing to send credentials to a non-loopback insecure host"
)
SKIP_NO_KEY = "no usable apiKey resolved"
SKIP_NO_PRICING = "no LiteLLM pricing endpoint (provider left untouched)"


class ConfigTarget(NamedTuple):
    """A resolved OpenCode config file and whether this tool may rewrite it."""

    path: Path
    writable: bool
    reason: str = ""


class ProviderOutcome(NamedTuple):
    """Per-provider result of a sync attempt."""

    name: str
    synced: bool
    skip_reason: str = ""
    added: Tuple[str, ...] = ()
    removed: Tuple[str, ...] = ()
    changed: Tuple[str, ...] = ()

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


# --------------------------------------------------------------------------------------
# E-01: config discovery
# --------------------------------------------------------------------------------------


def resolve_config_path(
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[Path] = None,
) -> Optional[ConfigTarget]:
    """Resolve the OpenCode config the way OpenCode does, or None when none exists.

    Precedence: ``$OPENCODE_CONFIG`` -> a project ``opencode.json``/``opencode.jsonc`` found by
    walking up from ``cwd`` -> ``$XDG_CONFIG_HOME/opencode/opencode.json`` ->
    ``~/.config/opencode/opencode.json``.

    A resolved path whose suffix is ``.jsonc`` is returned with ``writable=False``: stdlib json
    cannot parse comments and json.dump cannot preserve them, so rewriting one would silently
    destroy user content. The caller reports it and skips rather than mishandling it.
    """

    environ = os.environ if env is None else env
    start = Path.cwd() if cwd is None else Path(cwd)

    explicit = environ.get("OPENCODE_CONFIG")
    if explicit:
        candidate = Path(explicit).expanduser()
        if candidate.is_file():
            return _classify_target(candidate)
        return None

    for directory in [start, *start.parents]:
        for name in ("opencode.json", "opencode.jsonc"):
            candidate = directory / name
            if candidate.is_file():
                return _classify_target(candidate)

    xdg = environ.get("XDG_CONFIG_HOME")
    roots = [Path(xdg).expanduser()] if xdg else []
    roots.append(Path(environ.get("HOME", str(Path.home()))).expanduser() / ".config")
    for root in roots:
        for name in ("opencode.json", "opencode.jsonc"):
            candidate = root / "opencode" / name
            if candidate.is_file():
                return _classify_target(candidate)
    return None


def _classify_target(path: Path) -> ConfigTarget:
    """Mark a config UNSUPPORTED-FOR-WRITE when stdlib json cannot faithfully round-trip it."""

    if path.suffix.lower() == ".jsonc":
        return ConfigTarget(
            path,
            False,
            "jsonc comments cannot be preserved by a json round-trip; edit it by hand",
        )
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return ConfigTarget(
            path, False, f"not parseable as JSON ({type(exc).__name__})"
        )
    return ConfigTarget(path, True)


# --------------------------------------------------------------------------------------
# E-02: provider discovery, credential resolution, and the pricing probe
# --------------------------------------------------------------------------------------


def resolve_api_key(raw: Any) -> Optional[str]:
    """Resolve an OpenCode apiKey value, honoring the ``{file:~/path}`` interpolation.

    Returns None when nothing usable resolves. The returned secret is never logged by callers.
    """

    if not isinstance(raw, str) or not raw:
        return None
    if raw.startswith("{file:") and raw.endswith("}"):
        target = Path(raw[len("{file:") : -1].strip()).expanduser()
        try:
            value = target.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        return value or None
    if raw.startswith("{env:") and raw.endswith("}"):
        value = os.environ.get(raw[len("{env:") : -1].strip(), "").strip()
        return value or None
    return raw


def gateway_base(base_url: str) -> str:
    """Strip a trailing ``/v1`` so LiteLLM admin routes (host-rooted) resolve correctly."""

    url = base_url.rstrip("/")
    if url.endswith("/v1"):
        url = url[: -len("/v1")]
    return url


def _scheme_ok(base_url: str, allow_insecure: bool) -> Tuple[bool, str]:
    """Gate credential transmission on https. Returns (ok, skip_reason)."""

    from urllib.parse import urlsplit

    parts = urlsplit(base_url)
    if parts.scheme == "https":
        return True, ""
    if not allow_insecure:
        return False, SKIP_INSECURE
    host = (parts.hostname or "").lower()
    if host in _LOOPBACK_HOSTS:
        return True, ""
    return False, SKIP_INSECURE_NONLOOPBACK


def http_fetch_json(url: str, api_key: str, timeout: float = 15.0) -> Optional[Any]:
    """Fetch and parse a JSON document, or None on ANY failure.

    Mirrors ``versioning.latest_pypi_version``: stdlib only, short timeout, and a blanket
    failure path so offline/timeout/404/parse errors degrade to "no pricing" instead of
    crashing the command. The Authorization header is never echoed anywhere.
    """

    request = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {api_key}"}
    )
    try:
        with urllib.request.urlopen(  # noqa: S310 (scheme gated by _scheme_ok)
            request, timeout=timeout
        ) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None


def per_million(value: Any) -> Optional[float]:
    """Convert a per-token cost to $ per million tokens, ignoring non-numeric/absent values.

    The gateway response is untrusted input: a bool, string, None, or negative number yields
    None rather than being coerced into a bogus price.
    """

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value <= 0:
        return None
    return round(float(value) * 1_000_000, 6)


def _entries_from_payload(payload: Any) -> List[Tuple[str, Mapping[str, Any]]]:
    """Normalize a LiteLLM pricing payload into (model_id, cost_source) pairs.

    Handles both shapes: ``/model/info`` nests costs under ``model_info``, while
    ``/model_group/info`` carries them on the entry itself.
    """

    if not isinstance(payload, Mapping):
        return []
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    out: List[Tuple[str, Mapping[str, Any]]] = []
    seen = set()
    for item in data:
        if not isinstance(item, Mapping):
            continue
        model_id = item.get("model_name") or item.get("model_group") or item.get("id")
        if not isinstance(model_id, str) or not model_id or model_id in seen:
            continue
        seen.add(model_id)
        info = item.get("model_info")
        source = info if isinstance(info, Mapping) else item
        out.append((model_id, source))
    return out


def _display_name(model_id: str, existing: Mapping[str, Any]) -> str:
    """Prefer the name already in the user's config; otherwise derive a readable one."""

    current = existing.get(model_id)
    if isinstance(current, Mapping):
        name = current.get("name")
        if isinstance(name, str) and name:
            return name
    tail = model_id.split("/")[-1]
    for prefix in ("pt1-", "pt2-", "pt3-"):
        if tail.startswith(prefix):
            tail = tail[len(prefix) :]
            break
    if tail.endswith("-us"):
        tail = tail[: -len("-us")]
    words = [w for w in tail.replace("-", " ").split() if w]
    return " ".join(w if any(c.isdigit() for c in w) else w.capitalize() for w in words)


def build_models(
    payload: Any, existing: Mapping[str, Any]
) -> Optional[Dict[str, Dict[str, Any]]]:
    """Build the replacement ``models`` block, or None when the payload carries no pricing."""

    entries = _entries_from_payload(payload)
    if not entries:
        return None
    models: Dict[str, Dict[str, Any]] = {}
    priced = 0
    for model_id, source in entries:
        cost: Dict[str, float] = {}
        for out_key, in_key in _COST_FIELDS:
            value = per_million(source.get(in_key))
            if value is not None:
                cost[out_key] = value
        entry: Dict[str, Any] = {"name": _display_name(model_id, existing)}
        if cost:
            entry["cost"] = cost
            priced += 1
        models[model_id] = entry
    if not priced:
        # Model ids with no pricing at all means this was not a pricing endpoint.
        return None
    return models


def discover_providers(config: Mapping[str, Any]) -> List[str]:
    """Names of providers that look OpenAI-compatible, in config order."""

    providers = config.get("provider")
    if not isinstance(providers, Mapping):
        return []
    found: List[str] = []
    for name, spec in providers.items():
        if not isinstance(spec, Mapping):
            continue
        options = spec.get("options")
        has_base = isinstance(options, Mapping) and isinstance(
            options.get("baseURL"), str
        )
        if spec.get("npm") == _OPENAI_COMPATIBLE_NPM or has_base:
            found.append(name)
    return found


def sync_provider(
    config: Dict[str, Any],
    name: str,
    fetch: Callable[[str, str], Optional[Any]],
    allow_insecure: bool = False,
) -> ProviderOutcome:
    """Refresh one provider's ``models`` block in ``config`` (mutated in place on success)."""

    spec = config["provider"][name]
    options = spec.get("options") if isinstance(spec, Mapping) else None
    if not isinstance(options, Mapping):
        return ProviderOutcome(name, False, SKIP_NO_BASEURL)
    base_url = options.get("baseURL")
    if not isinstance(base_url, str) or not base_url:
        return ProviderOutcome(name, False, SKIP_NO_BASEURL)

    ok, reason = _scheme_ok(base_url, allow_insecure)
    if not ok:
        return ProviderOutcome(name, False, reason)

    api_key = resolve_api_key(options.get("apiKey"))
    if not api_key:
        return ProviderOutcome(name, False, SKIP_NO_KEY)

    existing = spec.get("models")
    existing = existing if isinstance(existing, Mapping) else {}

    base = gateway_base(base_url)
    new_models: Optional[Dict[str, Dict[str, Any]]] = None
    for path in PRICING_PATHS:
        payload = fetch(base + path, api_key)
        if payload is None:
            continue
        new_models = build_models(payload, existing)
        if new_models:
            break
    if not new_models:
        return ProviderOutcome(name, False, SKIP_NO_PRICING)

    def _existing_cost(model_id: str) -> Any:
        current = existing.get(model_id)
        return current.get("cost") if isinstance(current, Mapping) else None

    added = tuple(sorted(set(new_models) - set(existing)))
    removed = tuple(sorted(set(existing) - set(new_models)))
    changed = tuple(
        sorted(
            model_id
            for model_id in set(new_models) & set(existing)
            if _existing_cost(model_id) != new_models[model_id].get("cost")
        )
    )
    config["provider"][name]["models"] = new_models
    return ProviderOutcome(name, True, "", added, removed, changed)


# --------------------------------------------------------------------------------------
# E-06 / E-04: formatting-faithful serialization and the atomic, backed-up write
# --------------------------------------------------------------------------------------


def detect_indent(text: str, default: int = 4) -> int:
    """Infer the indent width from the first space-indented line; fall back to ``default``.

    Keeps a 2-space config from being silently reflowed to 4-space. Tabs are not inferred
    (json.dump takes an int or a string; we normalize to spaces and say so in --help).
    """

    for line in text.splitlines():
        stripped = line.lstrip(" ")
        if stripped and stripped != line:
            return len(line) - len(stripped)
    return default


def serialize(config: Mapping[str, Any], indent: int) -> str:
    """Render the config as normalized JSON at the given indent, preserving key order."""

    return json.dumps(config, indent=indent, ensure_ascii=False) + "\n"


def _atomic_write(path: Path, text: str) -> None:
    """Write-to-temp-then-rename so an interrupted apply never leaves a partial file.

    Same shape as ``ipd_authoring._atomic_write`` (one mechanism, not a second one).
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=".oc-models-", suffix=".json"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_config(
    path: Path, text: str, backup: bool = True, original: Optional[str] = None
) -> Optional[Path]:
    """Back up (before the replace) then atomically write ``text``. Returns the backup path."""

    backup_path: Optional[Path] = None
    if backup:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = path.with_name(f"{path.name}.{stamp}.bak")
        payload = path.read_text(encoding="utf-8") if original is None else original
        backup_path.write_text(payload, encoding="utf-8")
    _atomic_write(path, text)
    return backup_path


# --------------------------------------------------------------------------------------
# E-03: entry point
# --------------------------------------------------------------------------------------


def build_parser(prog: str = "aw oc update-models") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Refresh OpenCode provider model lists and pricing from the gateways declared in "
            "your own OpenCode config. Previews by default; pass --apply to write. Pricing is "
            "read from a provider's LiteLLM endpoints (/model/info, /model_group/info) and "
            "converted to $ per million tokens; providers without a pricing endpoint (plain "
            "OpenAI, Google) are reported as skipped and left untouched. --apply rewrites the "
            "file with normalized JSON formatting: the existing indent width is detected and "
            "reused, but byte-for-byte formatting is not preserved. Credentials are sent over "
            "https only and are never printed."
        ),
    )
    parser.add_argument(
        "--config",
        help="Path to opencode.json (default: the config OpenCode itself would load).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the changes (default: preview only).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicit synonym for the default preview behavior.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not write a timestamped .bak beside the config before applying.",
    )
    parser.add_argument(
        "--allow-insecure",
        action="store_true",
        help="Permit a non-https baseURL, and only for a loopback host.",
    )
    parser.add_argument("--agent", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--json", dest="as_json", action="store_true", help=argparse.SUPPRESS
    )
    parser.add_argument("--no-color", action="store_true", help=argparse.SUPPRESS)
    return parser


def _describe(outcome: ProviderOutcome) -> List[str]:
    lines: List[str] = []
    for model_id in outcome.added:
        lines.append(f"  + ADDED   {model_id}")
    for model_id in outcome.removed:
        lines.append(f"  - REMOVED {model_id}")
    for model_id in outcome.changed:
        lines.append(f"  ~ CHANGED {model_id}")
    return lines


def run(
    argv: Optional[List[str]] = None,
    fetch: Optional[Callable[[str, str], Optional[Any]]] = None,
    env: Optional[Mapping[str, str]] = None,
) -> int:
    """Preview or apply the model/pricing sync. Returns a process exit code."""

    args = build_parser().parse_args(list(argv or []))
    fetcher = fetch if fetch is not None else http_fetch_json

    if args.config:
        candidate = Path(args.config).expanduser()
        if not candidate.is_file():
            print(f"error: config not found: {candidate}")
            return 2
        target = _classify_target(candidate)
    else:
        target = resolve_config_path(env=env)
        if target is None:
            print(
                "error: no OpenCode config found (set $OPENCODE_CONFIG or pass --config)"
            )
            return 2

    if args.apply and not target.writable:
        print(f"error: refusing to rewrite {target.path}: {target.reason}")
        return 2
    if not target.writable:
        print(f"note: {target.path} is preview-only: {target.reason}")
        return 2

    original = target.path.read_text(encoding="utf-8")
    config = json.loads(original)

    providers = discover_providers(config)
    if not providers:
        print(f"no OpenAI-compatible providers declared in {target.path}")
        return 0

    outcomes = [
        sync_provider(config, name, fetcher, allow_insecure=args.allow_insecure)
        for name in providers
    ]
    synced = [o for o in outcomes if o.synced]
    mutated = [o for o in synced if o.has_changes]

    print(f"config: {target.path}")
    for outcome in outcomes:
        if not outcome.synced:
            print(f"skipped {outcome.name}: {outcome.skip_reason}")
            continue
        if not outcome.has_changes:
            print(f"{outcome.name}: up to date")
            continue
        total = len(outcome.added) + len(outcome.removed) + len(outcome.changed)
        print(f"{outcome.name}: {total} change(s)")
        for line in _describe(outcome):
            print(line)

    if not mutated:
        return 0
    if not args.apply:
        print("\npreview only; re-run with --apply to write")
        return 0

    text = serialize(config, detect_indent(original))
    backup_path = write_config(
        target.path, text, backup=not args.no_backup, original=original
    )
    if backup_path is not None:
        print(f"backup: {backup_path}")
    print(f"wrote: {target.path}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    return run(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

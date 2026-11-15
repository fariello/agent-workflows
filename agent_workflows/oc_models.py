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
- Writes by default; pass `--dry-run` to preview. `--apply` is retained as an explicit synonym for writing.
- The bearer key is sent over https ONLY. A non-https base URL is skipped without issuing a
  request unless the caller passes `--allow-insecure`, and even then only to a loopback host.
- The API key, the Authorization header, and key-file contents never appear in any output,
  diff, log, exception message, or machine record.
- Writes are atomic (temp file + os.replace) with a timestamped backup taken BEFORE the
  replace, so an interrupted run cannot truncate the file that gates the user's whole tool.
- A `.jsonc` (or otherwise unparseable) config is UNSUPPORTED-FOR-WRITE: stdlib json cannot
  round-trip comments, so it is reported and skipped instead of silently destroying content.
- Formatting is NOT byte-preserved on write: the file's existing indent width is detected
  and reused, but the output is normalized JSON. This is stated in --help rather than overclaimed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Tuple

from agent_workflows.artifact_core import replacement_mode
from agent_workflows.opencode_cli import is_v2

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


class DiscoveredHarness(NamedTuple):
    """An installed AI agent CLI and its discovered models/status."""

    name: str
    executable: Optional[str]
    installed: bool
    models: Tuple[str, ...]
    target_provider: str
    notes: str = ""
    model_details: Optional[Dict[str, Dict[str, Any]]] = None


# --- OpenCode v1.x and v2.x schema compatibility helpers -----------------------------


def _provider_container_keys(config: Mapping[str, Any]) -> List[str]:
    """Return existing provider container keys (['providers'], ['provider'], or both)."""
    keys = []
    if isinstance(config.get("providers"), Mapping):
        keys.append("providers")
    if isinstance(config.get("provider"), Mapping):
        keys.append("provider")
    return keys


def _get_all_providers(
    config: Mapping[str, Any],
) -> Dict[str, Tuple[str, Dict[str, Any]]]:
    """Map provider_name -> (container_key, spec_dict) across v1 ('provider') and v2 ('providers')."""
    res: Dict[str, Tuple[str, Dict[str, Any]]] = {}
    for key in ("providers", "provider"):
        cont = config.get(key)
        if isinstance(cont, Mapping):
            for name, spec in cont.items():
                if (
                    isinstance(name, str)
                    and isinstance(spec, Mapping)
                    and name not in res
                ):
                    res[name] = (key, spec)
    return res


def _get_provider_options(spec: Mapping[str, Any]) -> Mapping[str, Any]:
    """Extract options or settings dictionary from a provider spec (v1 vs v2)."""
    if not isinstance(spec, Mapping):
        return {}
    if "options" in spec and isinstance(spec["options"], Mapping):
        return spec["options"]
    if "settings" in spec and isinstance(spec["settings"], Mapping):
        return spec["settings"]
    return {}


def _is_openai_compatible(spec: Mapping[str, Any]) -> bool:
    """Check if provider spec uses an OpenAI-compatible driver or has a baseURL (v1 vs v2)."""
    if not isinstance(spec, Mapping):
        return False
    pkg = str(spec.get("npm") or spec.get("package") or "")
    if pkg == _OPENAI_COMPATIBLE_NPM or "openai-compatible" in pkg:
        return True
    options = _get_provider_options(spec)
    return bool(
        options.get("baseURL") or options.get("base_url") or options.get("baseUrl")
    )


def _derive_model_title(model_id: str) -> str:
    """Generate a clean display name from a model identifier slug."""
    clean = model_id
    if clean.startswith("antigravity-"):
        clean = clean[len("antigravity-") :]
    words = clean.replace("-", " ").replace("_", " ").split()
    return " ".join(w.capitalize() for w in words)


# --- Multi-harness discovery probes (E-01) -------------------------------------------


def _probe_agy(
    which_fn: Callable[[str], Optional[str]],
    runner: Callable[..., Any],
) -> DiscoveredHarness:
    binary = which_fn("agy")
    if not binary:
        return DiscoveredHarness(
            name="agy",
            executable=None,
            installed=False,
            models=(),
            target_provider="google",
            notes="agy CLI not found on PATH",
        )
    try:
        proc = runner(
            [binary, "models"],
            capture_output=True,
            text=True,
            timeout=10.0,
            shell=False,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return DiscoveredHarness(
            name="agy",
            executable=binary,
            installed=True,
            models=(),
            target_provider="google",
            notes=f"agy models query failed: {type(exc).__name__}",
        )

    stdout = strip_ansi(getattr(proc, "stdout", "") or "")
    models: List[str] = []
    details: Dict[str, Dict[str, Any]] = {}

    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line or "Fetching available models" in line:
            continue
        parts = line.split(None, 1)
        if not parts:
            continue
        model_id = parts[0].strip()
        if not re.match(r"^[a-zA-Z0-9][-._a-zA-Z0-9]+$", model_id):
            continue
        if model_id.lower() in ("model", "name", "id", "alias"):
            continue
        display_name = (
            parts[1].strip() if len(parts) > 1 else _derive_model_title(model_id)
        )
        models.append(model_id)
        details[model_id] = {
            "name": display_name,
            "limit": {"context": 1048576, "output": 65536},
        }

    return DiscoveredHarness(
        name="agy",
        executable=binary,
        installed=True,
        models=tuple(models),
        target_provider="google",
        notes=f"Detected {len(models)} Antigravity models for provider google",
        model_details=details,
    )


def _probe_codex(
    which_fn: Callable[[str], Optional[str]],
    homedir: Path,
) -> DiscoveredHarness:
    binary = which_fn("codex")
    if not binary:
        return DiscoveredHarness(
            name="codex",
            executable=None,
            installed=False,
            models=(),
            target_provider="openai",
            notes="codex CLI not found on PATH",
        )

    models: List[str] = []
    details: Dict[str, Dict[str, Any]] = {}
    cache_path = homedir / ".codex" / "models_cache.json"

    if cache_path.is_file():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            for entry in data.get("models", []):
                slug = entry.get("slug")
                if not slug or not isinstance(slug, str):
                    continue
                display_name = entry.get("display_name") or slug
                ctx = entry.get("context_window", 272000)
                models.append(slug)
                details[slug] = {
                    "name": display_name,
                    "limit": {"context": ctx, "output": 32768},
                }
        except (OSError, ValueError):
            pass

    if not models:
        config_path = homedir / ".codex" / "config.toml"
        if config_path.is_file():
            try:
                for line in config_path.read_text(encoding="utf-8").splitlines():
                    m = re.match(r'^\s*model\s*=\s*["\']([^"\']+)["\']', line)
                    if m:
                        slug = m.group(1).strip()
                        if slug:
                            models.append(slug)
                            details[slug] = {
                                "name": slug,
                                "limit": {"context": 272000, "output": 32768},
                            }
                        break
            except OSError:
                pass

    return DiscoveredHarness(
        name="codex",
        executable=binary,
        installed=True,
        models=tuple(models),
        target_provider="openai",
        notes=f"Detected {len(models)} models from ~/.codex",
        model_details=details,
    )


def _probe_claude(
    which_fn: Callable[[str], Optional[str]],
    homedir: Path,
) -> DiscoveredHarness:
    binary = which_fn("claude")
    if not binary:
        return DiscoveredHarness(
            name="claude",
            executable=None,
            installed=False,
            models=(),
            target_provider="uri",
            notes="claude CLI not found on PATH",
        )

    settings_path = homedir / ".claude" / "settings.json"
    models: List[str] = []
    details: Dict[str, Dict[str, Any]] = {}
    base_url = ""
    target_prov = "uri"

    if settings_path.is_file():
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
            env_map = data.get("env", {})
            base_url = env_map.get("ANTHROPIC_BASE_URL", "")
            if (
                base_url
                and "uri" not in base_url
                and base_url.startswith("https://api.anthropic.com")
            ):
                target_prov = "anthropic"
            for k, val in env_map.items():
                if k.startswith("ANTHROPIC_DEFAULT_") or k == "ANTHROPIC_MODEL":
                    if isinstance(val, str) and val.strip():
                        val_str = val.strip()
                        if val_str not in models:
                            models.append(val_str)
                            details[val_str] = {
                                "name": val_str,
                                "limit": {"context": 1000000, "output": 65536},
                            }
        except (OSError, ValueError):
            pass

    notes = (
        f"Claude Code configured with gateway {base_url}"
        if base_url
        else "Claude Code CLI detected"
    )
    return DiscoveredHarness(
        name="claude",
        executable=binary,
        installed=True,
        models=tuple(models),
        target_provider=target_prov,
        notes=notes,
        model_details=details,
    )


def _probe_kiro(
    which_fn: Callable[[str], Optional[str]],
    runner: Callable[..., Any],
) -> DiscoveredHarness:
    binary = which_fn("kiro-cli") or which_fn("kiro")
    if not binary:
        return DiscoveredHarness(
            name="kiro",
            executable=None,
            installed=False,
            models=(),
            target_provider="kiro",
            notes="kiro CLI not found on PATH",
        )

    try:
        proc = runner(
            [binary, "chat", "--list-models", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10.0,
            shell=False,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return DiscoveredHarness(
            name="kiro",
            executable=binary,
            installed=True,
            models=(),
            target_provider="kiro",
            notes=f"kiro query failed: {type(exc).__name__}",
        )

    stdout = strip_ansi(getattr(proc, "stdout", "") or "").strip()
    models: List[str] = []
    details: Dict[str, Dict[str, Any]] = {}

    if stdout:
        try:
            data = json.loads(stdout)
            for item in data.get("models", []):
                m_id = item.get("model_id")
                if not m_id or not isinstance(m_id, str) or m_id == "auto":
                    continue
                display_name = item.get("model_name") or m_id
                ctx = item.get("context_window_tokens", 200000)
                models.append(m_id)
                details[m_id] = {
                    "name": display_name,
                    "limit": {"context": ctx, "output": 32768},
                }
        except ValueError:
            pass

    notes = (
        f"Detected {len(models)} models via kiro-cli (requires opencode-kiro ACP plugin)"
        if models
        else "kiro CLI detected"
    )
    return DiscoveredHarness(
        name="kiro",
        executable=binary,
        installed=True,
        models=tuple(models),
        target_provider="kiro",
        notes=notes,
        model_details=details,
    )


def probe_installed_harnesses(
    which_fn: Optional[Callable[[str], Optional[str]]] = None,
    runner: Optional[Callable[..., Any]] = None,
    homedir: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, DiscoveredHarness]:
    """Probe host system for installed AI agent CLIs (agy, codex, claude, kiro).

    Under pytest (`PYTEST_CURRENT_TEST`), defaults to returning absent binaries when
    which_fn is not injected, ensuring zero accidental external processes in tests.
    """
    environ = os.environ if env is None else env
    if (
        which_fn is None
        and environ.get("PYTEST_CURRENT_TEST")
        and not environ.get("AW_TEST_REAL_HARNESS")
    ):

        def which(cmd: str) -> Optional[str]:
            return None
    else:
        which = shutil.which if which_fn is None else which_fn

    run = subprocess.run if runner is None else runner
    home = (
        Path(environ.get("HOME", str(Path.home()))).expanduser()
        if homedir is None
        else homedir
    )

    return {
        "agy": _probe_agy(which, run),
        "codex": _probe_codex(which, home),
        "claude": _probe_claude(which, home),
        "kiro": _probe_kiro(which, run),
    }


# --- Model reconciliation and config population (E-02) ------------------------------


def reconcile_harness_models(
    config: Dict[str, Any],
    discovered: Dict[str, DiscoveredHarness],
    prefer_v2: bool = False,
) -> Dict[str, List[str]]:
    """Populate missing model definitions from discovered harnesses into opencode.json.

    Supports OpenCode v1 ('provider' with 'npm') and v2 ('providers' with 'package').
    Preserves all existing model entries and user customizations without overwriting.
    Returns mapping of provider_name -> list of newly added model IDs.
    """
    cont_keys = _provider_container_keys(config)
    if "providers" in cont_keys:
        primary_key = "providers"
    elif "provider" in cont_keys:
        primary_key = "provider"
    else:
        primary_key = "providers" if prefer_v2 else "provider"
        config[primary_key] = {}

    providers = config[primary_key]
    added: Dict[str, List[str]] = {}

    # 1. Antigravity -> google provider
    agy = discovered.get("agy")
    if agy and agy.installed and agy.models:
        if "google" not in providers:
            providers["google"] = {
                ("package" if primary_key == "providers" else "npm"): (
                    "@opencode-ai/ai/providers/google"
                    if primary_key == "providers"
                    else "@ai-sdk/google"
                ),
                "name": "Google Gemini",
                "models": {},
            }
        g_spec = providers["google"]
        if not isinstance(g_spec.get("models"), dict):
            g_spec["models"] = {}
        g_models = g_spec["models"]
        for raw_id in agy.models:
            key = (
                raw_id if raw_id.startswith("antigravity-") else f"antigravity-{raw_id}"
            )
            if key not in g_models:
                det = (agy.model_details or {}).get(raw_id, {})
                g_models[key] = {
                    "name": det.get("name") or _derive_model_title(raw_id),
                    "limit": det.get("limit") or {"context": 1048576, "output": 65536},
                }
                added.setdefault("google", []).append(key)

    # 2. Codex -> openai provider
    codex = discovered.get("codex")
    if codex and codex.installed and codex.models:
        if "openai" not in providers:
            providers["openai"] = {
                ("package" if primary_key == "providers" else "npm"): (
                    "@opencode-ai/ai/providers/openai"
                    if primary_key == "providers"
                    else "@ai-sdk/openai"
                ),
                "name": "OpenAI",
                "models": {},
            }
        o_spec = providers["openai"]
        if not isinstance(o_spec.get("models"), dict):
            o_spec["models"] = {}
        o_models = o_spec["models"]
        for raw_id in codex.models:
            if raw_id not in o_models:
                det = (codex.model_details or {}).get(raw_id, {})
                o_models[raw_id] = {
                    "name": det.get("name") or raw_id,
                    "limit": det.get("limit") or {"context": 272000, "output": 32768},
                }
                added.setdefault("openai", []).append(raw_id)

    # 3. Kiro -> kiro provider (if kiro provider declared in config)
    kiro = discovered.get("kiro")
    if kiro and kiro.installed and kiro.models:
        if "kiro" in providers:
            k_spec = providers["kiro"]
            if not isinstance(k_spec.get("models"), dict):
                k_spec["models"] = {}
            k_models = k_spec["models"]
            for raw_id in kiro.models:
                if raw_id not in k_models:
                    det = (kiro.model_details or {}).get(raw_id, {})
                    k_models[raw_id] = {
                        "name": det.get("name") or raw_id,
                        "limit": det.get("limit")
                        or {"context": 200000, "output": 32768},
                    }
                    added.setdefault("kiro", []).append(raw_id)

    return added


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
# runprofile Order 02 (p0l1to) E-01: the READ-ONLY model catalog
#
# The profile wizard needs to show the user the models THEIR OpenCode can actually see. That
# is a different job from everything else in this module: `update-models` WRITES the config
# after talking to a gateway over the network, whereas this reads and writes NOTHING. It
# lives here anyway because this file is the established OpenCode boundary
# (`resolve_config_path` above already mirrors OpenCode's own config discovery), and forking
# those path rules into a second module is how two copies of a lookup drift apart.
#
# FOUR PROPERTIES, each one a way a naive implementation would have gone wrong:
#
# 1. NO REFRESH, NO WRITE. `opencode models --refresh` re-fetches the cache from models.dev,
#    which is a network call and a mutation of the user's cache. The argv is built by
#    `catalog_argv` and checked against :data:`FORBIDDEN_CATALOG_FLAGS`, so a refresh or write
#    flag cannot be added by accident; profile creation is READ-ONLY toward OpenCode.
# 2. ARGV LIST, `shell=False`. The executable name comes from configuration, so composing a
#    shell string would make the config file a command-injection surface.
# 3. AN EMPTY CATALOG IS NEVER A SUCCESS. Missing binary, timeout, nonzero exit, output that
#    parses to nothing, and an empty list are each a NAMED diagnostic (:data:`CATALOG_*`), never
#    a successful empty list. `ModelCatalog.available` is literally `bool(models)`, so
#    "succeeded with no models" is unrepresentable rather than merely discouraged. A wizard that
#    green-washed a discovery failure into "your OpenCode has no models" would push the user
#    toward the wrong fix.
# 4. THE FALLBACK CARRIES NO SECRET. When the CLI cannot answer, the STATICALLY DECLARED model
#    ids in the user's own config are still useful (they include the private ones a public
#    catalog omits). Only `provider.<name>.models.<id>` keys are read; the options block and
#    every other credential-bearing field are never touched, so no `resolve_api_key` call and no
#    credential can reach the output.
# --------------------------------------------------------------------------------------

#: Bounded wall-clock budget for the catalog subprocess. A hung `opencode` must not hang a
#: wizard prompt forever; the timeout becomes a named diagnostic and the user types a model.
CATALOG_TIMEOUT = 20.0

#: Flags that would make the catalog probe non-read-only. Checked by `catalog_argv`.
FORBIDDEN_CATALOG_FLAGS: Tuple[str, ...] = (
    "--refresh",
    "--apply",
    "--write",
    "--update",
)

#: Where a catalog's model ids came from.
CATALOG_SOURCE_CLI = "opencode-cli"
CATALOG_SOURCE_CONFIG = "opencode-config"
CATALOG_SOURCE_NONE = "none"

#: Named unavailability diagnostics. One per distinguishable failure, because "no models" and
#: "opencode is not installed" call for different user action.
CATALOG_MISSING_BINARY = "executable-not-found"
CATALOG_TIMED_OUT = "timeout"
CATALOG_NONZERO_EXIT = "nonzero-exit"
CATALOG_UNPARSEABLE = "unparseable-output"
CATALOG_NO_MODELS = "no-models-listed"
CATALOG_NO_CONFIG = "no-config-found"

# ANSI CSI/OSC noise a colorized CLI may emit even when piped. Stripped before parsing so a
# styled `provider/model` is still recognized rather than silently dropped.
_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")

# The accepted record shape. Deliberately the SAME grammar the profile schema stores
# (`runner_profiles.MODEL_RE`), resolved lazily in `_model_re` so a discovered model can always
# be saved: two independent notions of "a valid model id" would let the wizard offer a value the
# store then refuses.
_FALLBACK_MODEL_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._+:-]*(?:/[A-Za-z0-9][A-Za-z0-9._+:-]*)+$"
)


class ModelCatalog(NamedTuple):
    """A read-only snapshot of the models this user's OpenCode can see.

    ``available`` is derived from ``models`` rather than stored, so a "successful empty
    catalog" cannot be constructed. ``reason`` is EMPTY only when the CLI answered; when the
    config fallback supplied the ids it still records WHY the CLI did not, so a degraded
    catalog is never silent.
    """

    models: Tuple[str, ...] = ()
    source: str = CATALOG_SOURCE_NONE
    reason: str = ""
    detail: str = ""

    @property
    def available(self) -> bool:
        return bool(self.models)


def _model_re():
    """The profile schema's model grammar, with a local fallback if it cannot be imported."""

    try:
        from agent_workflows import runner_profiles as _rp

        return _rp.MODEL_RE
    except (
        Exception
    ):  # pragma: no cover - defensive; keeps discovery working standalone
        return _FALLBACK_MODEL_RE


def strip_ansi(text: str) -> str:
    """Remove ANSI CSI/OSC sequences from ``text``."""

    return _ANSI_RE.sub("", text)


def catalog_argv(opencode: str = "opencode") -> List[str]:
    """Return the EXACT argv for the read-only catalog probe.

    Raises ``ValueError`` if the executable name itself smuggles in a forbidden flag, so the
    read-only guarantee is structural rather than a comment.
    """

    argv = [str(opencode), "models"]
    for token in argv:
        if token in FORBIDDEN_CATALOG_FLAGS:
            raise ValueError(
                f"refusing to build a catalog probe containing {token!r}: model discovery is "
                "read-only and must never refresh or write OpenCode state"
            )
    return argv


def parse_models_output(text: str) -> Tuple[str, ...]:
    """Parse `opencode models` output into exact, deduplicated ``provider/model`` ids.

    ANSI noise and surrounding whitespace are normalized; a line that is not exactly one
    ``provider/model`` record (blank lines, banners, progress text, bullets, trailing
    annotations) is DROPPED rather than guessed at, because a guessed model id would be stored
    and then launched. Order is first-seen, so the result is deterministic for a given input.
    """

    pattern = _model_re()
    seen: Dict[str, None] = {}
    for raw_line in strip_ansi(text or "").splitlines():
        candidate = raw_line.strip()
        if not candidate:
            continue
        if pattern.match(candidate):
            seen.setdefault(candidate, None)
    return tuple(seen)


def models_from_config(config: Any) -> Tuple[str, ...]:
    """Statically declared ``provider/model`` ids from a parsed OpenCode config.

    Reads ONLY the per-provider model keys across OpenCode v1 ('provider') and v2 ('providers').
    It never looks at a provider's options block, credential value, or headers, so no secret
    can reach the caller.
    """

    if not isinstance(config, Mapping):
        return ()
    all_provs = _get_all_providers(config)
    if not all_provs:
        return ()
    pattern = _model_re()
    found: Dict[str, None] = {}
    for provider_name, (_cont_key, spec) in all_provs.items():
        if not isinstance(provider_name, str) or not isinstance(spec, Mapping):
            continue
        models = spec.get("models")
        if not isinstance(models, Mapping):
            continue
        for model_id in models:
            if not isinstance(model_id, str):
                continue
            candidate = f"{provider_name.strip()}/{model_id.strip()}"
            if pattern.match(candidate):
                found.setdefault(candidate, None)
    return tuple(found)


# --------------------------------------------------------------------------------------
# runverdict Order 07 (w33lrl) E-01/E-02: the HOST DEFAULT MODEL and its RATE CARD
#
# WHY THESE ARE NEW FUNCTIONS RATHER THAN A REUSE OF THE THREE ABOVE. `models_from_config`
# returns the CATALOG of declared `provider.<name>.models.<id>` keys; it can say WHICH models
# exist and can never say which one is DEFAULT, because the default is the config's TOP-LEVEL
# `model` key and nothing in this package read it before now (`w33lrl` F-12). An executor
# pointed at the catalog reader gets a list and no answer, so the accessor below exists.
#
# THEY CARRY `models_from_config`'S NO-SECRET GUARANTEE, stated in each docstring and held to
# in each body: the only keys read are the top-level `model`/`small_model`/`agent.<name>.model`
# identifiers and `provider.<name>.models.<id>.cost`. A provider's `options` block, its
# `apiKey`, and its headers are NEVER touched, so no credential can reach a caller (and hence
# no credential can reach a run record, which is what these feed).
# --------------------------------------------------------------------------------------

#: Which config key supplied the resolved default model. A CLOSED vocabulary, because the value
#: is recorded durably and a reader must never have to guess an origin from the id itself.
DEFAULT_MODEL_KEY_TOP_LEVEL = "model"
DEFAULT_MODEL_KEY_AGENT = "agent.model"
DEFAULT_MODEL_KEY_SMALL = "small_model"

#: Named reasons the default model is UNKNOWN. Each is a distinguishable, reachable state, never
#: a stand-in for "absent" (the `x0spmh` absent-versus-zero rule applied to identity).
DEFAULT_MODEL_NO_CONFIG = "no-config-found"
DEFAULT_MODEL_UNPARSEABLE = "unparseable-config"
DEFAULT_MODEL_NOT_DECLARED = "no-default-model-key"
DEFAULT_MODEL_MALFORMED = "malformed-model-value"

#: Named reasons a rate card is UNKNOWN, as distinct from a card with an absent COMPONENT.
CARD_NO_CONFIG = DEFAULT_MODEL_NO_CONFIG
CARD_UNPARSEABLE = DEFAULT_MODEL_UNPARSEABLE
CARD_NO_MODEL = "no-model-to-price"
CARD_MODEL_NOT_DECLARED = "model-not-in-config"
CARD_NO_COST_BLOCK = "model-has-no-cost-block"
CARD_NOT_RESOLVABLE_HOST = "host-card-not-in-any-readable-config"

#: The card component names, in the order the config declares them. Four are READ; how many are
#: PRESENT is a property of each model (measured live: 47 of 80 priced models carry only
#: `input`/`output`), which is why the record names an unknown per absent component rather than
#: assuming a four-component shape (`w33lrl` F-13).
CARD_COMPONENTS: Tuple[str, ...] = ("input", "cache_read", "cache_write", "output")

#: The unit the config stores, recorded EXPLICITLY beside the values. The config is ALREADY in
#: dollars per million tokens (this module's own docstring says so, and `build_models` calls
#: `per_million` on the GATEWAY's per-token value BEFORE storing), so a reader who assumed
#: per-token would be off by 1e6.
CARD_UNIT = "$/Mtok"

#: A component present in the `cost` block but not a usable number. DISTINCT from absence: the
#: config asserted a price and the assertion is unusable, which is an operator-visible defect
#: rather than a model the gateway does not price.
CARD_COMPONENT_MALFORMED = "malformed"
#: A component the `cost` block does not mention at all. NOT zero: research `x0spmh` records a
#: `cache_read = $0` read as "cache reads are free" when in fact an unpriced component was
#: hiding 73.9 percent of a $16.41 turn.
CARD_COMPONENT_ABSENT = "absent"


class HostDefaultModel(NamedTuple):
    """The model this OpenCode host will use when no ``--model`` is passed, or a NAMED unknown.

    ``model`` is empty exactly when ``reason`` is set, so "unknown" is representable and is never
    spelled as an empty string a caller might mistake for a resolved value. ``key`` names WHICH
    config key supplied it (one of the ``DEFAULT_MODEL_KEY_*`` values), because an id with no
    recorded origin forces a later reader to guess between the top-level default, an agent
    override, and ``small_model``.
    """

    model: str = ""
    key: str = ""
    reason: str = ""
    #: The config file's own digest, so a later edit to it is DETECTABLE. Distinct from any
    #: profile-store digest: this covers the OpenCode config, that one covers
    #: `runner-profiles.json`.
    config_digest: str = ""
    #: Basename ONLY, never the path. The resolved config lives under the operator's home, and a
    #: durable record must not carry that (leak-sanitizer rule).
    config_name: str = ""

    @property
    def resolved(self) -> bool:
        return bool(self.model)


def default_model_from_config(
    config: Any,
    agent: Optional[str] = None,
) -> Tuple[str, str]:
    """Return ``(model_id, key)`` for a parsed config's DEFAULT model, or ``("", reason)``.

    Reads ONLY the default-model identifiers: ``agent.<agent>.model`` when ``agent`` is named and
    declares one, else the top-level ``model``. It never looks at a provider's options block,
    credential value, or headers, so no secret can reach the caller (the same guarantee
    :func:`models_from_config` carries, and for the same reason).

    ``small_model`` is deliberately NOT a fallback. It is OpenCode's cheap-task model, not the
    default for a driver turn, so returning it would misattribute cost; it has a name in
    :data:`DEFAULT_MODEL_KEY_SMALL` for a caller that resolves it explicitly.

    The precedence mirrors OpenCode's own: a per-agent model overrides the top-level default,
    which is why ``agent`` is threaded in rather than assumed absent. Measured on the maintainer's
    live config the single configured agent sets only ``temperature``, so the top-level key is
    today's effective default -- a property of one config, not a guarantee, which is exactly why
    the KEY is returned alongside the id.
    """

    if not isinstance(config, Mapping):
        return "", DEFAULT_MODEL_UNPARSEABLE
    pattern = _model_re()

    if agent:
        agents = config.get("agent")
        spec = agents.get(agent) if isinstance(agents, Mapping) else None
        if isinstance(spec, Mapping):
            candidate = spec.get("model")
            if isinstance(candidate, str) and candidate.strip():
                value = candidate.strip()
                if pattern.match(value):
                    return value, DEFAULT_MODEL_KEY_AGENT
                return "", DEFAULT_MODEL_MALFORMED

    candidate = config.get("model")
    if candidate is None:
        return "", DEFAULT_MODEL_NOT_DECLARED
    if not isinstance(candidate, str) or not candidate.strip():
        return "", DEFAULT_MODEL_MALFORMED
    value = candidate.strip()
    if not pattern.match(value):
        # A value that is not a `provider/model` identifier is REFUSED rather than recorded: it
        # would be attributed as a model id downstream and no consumer could tell it apart from
        # a real one.
        return "", DEFAULT_MODEL_MALFORMED
    return value, DEFAULT_MODEL_KEY_TOP_LEVEL


def resolve_host_default_model(
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[Path] = None,
    agent: Optional[str] = None,
) -> HostDefaultModel:
    """Resolve THIS host's default model from the config OpenCode itself would load.

    The config file is reached through :func:`resolve_config_path` and nothing else, so this does
    not re-derive OpenCode's discovery precedence (``$OPENCODE_CONFIG`` -> a project
    ``opencode.json``/``.jsonc`` walking up -> ``$XDG_CONFIG_HOME`` -> ``~/.config``). ``env`` and
    ``cwd`` are injectable for exactly the reason they are on that function: a test must point at a
    temp directory rather than reading the operator's real config, which differs per machine and is
    rewritten by every ``aw oc update-models``.

    EVERY failure is a NAMED unknown, never an omission and never a guess: no config
    (:data:`DEFAULT_MODEL_NO_CONFIG`), a ``.jsonc`` or otherwise unparseable config
    (:data:`DEFAULT_MODEL_UNPARSEABLE`, reachable BY DESIGN since stdlib json cannot read
    comments), no top-level ``model`` key (:data:`DEFAULT_MODEL_NOT_DECLARED`), or a value that is
    not a ``provider/model`` identifier (:data:`DEFAULT_MODEL_MALFORMED`).

    Carries the config's DIGEST and BASENAME, not its path. The digest is what makes a later edit
    to the card or the default detectable; the path is withheld because the file lives under the
    operator's home directory and this value is written into a durable run record.
    """

    target = resolve_config_path(env=env, cwd=cwd)
    if target is None:
        return HostDefaultModel(reason=DEFAULT_MODEL_NO_CONFIG)
    name = target.path.name
    try:
        raw = target.path.read_text(encoding="utf-8")
    except OSError:
        return HostDefaultModel(reason=DEFAULT_MODEL_UNPARSEABLE, config_name=name)
    digest = _text_digest(raw)
    try:
        parsed = json.loads(raw)
    except ValueError:
        return HostDefaultModel(
            reason=DEFAULT_MODEL_UNPARSEABLE, config_digest=digest, config_name=name
        )
    model, key = default_model_from_config(parsed, agent=agent)
    if not model:
        return HostDefaultModel(reason=key, config_digest=digest, config_name=name)
    return HostDefaultModel(
        model=model, key=key, config_digest=digest, config_name=name
    )


def _text_digest(text: str) -> str:
    """The sha256 of a config's exact bytes, so a later edit to it is detectable."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def card_from_config(config: Any, model_id: str) -> Tuple[Dict[str, Any], str]:
    """Return ``(components, reason)``: one model's rate card as the config declares it.

    ``components`` maps each of :data:`CARD_COMPONENTS` to a float when the config prices it, to
    :data:`CARD_COMPONENT_ABSENT` when the ``cost`` block does not mention it, and to
    :data:`CARD_COMPONENT_MALFORMED` when it does but the value is unusable. A non-empty ``reason``
    means no card at all (no such model, or no ``cost`` block) and ``components`` is empty.

    AN ABSENT COMPONENT IS NEVER A ZERO, and that distinction is the whole point of this function.
    Research `x0spmh` records the card being corrected mid-history from an era where ``cache_read``
    was UNPRICED, and the resulting ``$0`` was read as evidence that cache reads were free when
    they were in fact 73.9 percent of a $16.41 turn. Measured live, 47 of the 80 priced models in
    the maintainer's config carry ONLY ``input`` and ``output``, so a partial card is the MAJORITY
    case today rather than a historical artifact.

    `per_million` IS DELIBERATELY NOT CALLED HERE, and calling it would be a 1000000x error. That
    function is the WRITE-side converter: it turns a LiteLLM gateway's per-TOKEN figure into the
    ``$/Mtok`` value that gets STORED (see :func:`build_models`). The config therefore already holds
    ``$/Mtok`` (this module's docstring states it, and a live block reads
    ``{"input": 5.5, "cache_read": 0.55, ...}``), so passing a value read back OUT through it would
    multiply by 1e6. What IS reused is that function's REFUSAL POSTURE: a bool, a string, a None,
    or a non-positive number is untrusted input and yields an unknown rather than a coerced price.

    Reads only ``provider.<name>.models.<id>.cost``; never an options block or a credential.
    """

    if not isinstance(config, Mapping):
        return {}, CARD_UNPARSEABLE
    if not model_id:
        return {}, CARD_NO_MODEL
    provider_name, _, bare = model_id.partition("/")
    all_provs = _get_all_providers(config)
    if not all_provs or provider_name not in all_provs:
        return {}, CARD_MODEL_NOT_DECLARED
    _cont_key, spec = all_provs[provider_name]
    models = spec.get("models") if isinstance(spec, Mapping) else None
    entry = models.get(bare) if isinstance(models, Mapping) else None
    if not isinstance(entry, Mapping):
        return {}, CARD_MODEL_NOT_DECLARED
    cost = entry.get("cost")
    if not isinstance(cost, Mapping):
        return {}, CARD_NO_COST_BLOCK

    components: Dict[str, Any] = {}
    for component in CARD_COMPONENTS:
        if component not in cost:
            components[component] = CARD_COMPONENT_ABSENT
            continue
        value = cost[component]
        # `per_million`'s refusal posture WITHOUT its multiplication: reject a bool (which is an
        # int in Python and would price at 1.0), a string, and a negative number. A GENUINE ZERO
        # is KEPT as 0.0, because "priced at zero" and "not priced" are different facts and the
        # `x0spmh` trap is exactly the confusion of the two.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            components[component] = CARD_COMPONENT_MALFORMED
        elif value < 0:
            components[component] = CARD_COMPONENT_MALFORMED
        else:
            components[component] = float(value)
    return components, ""


def catalog_from_config(
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[Path] = None,
) -> Tuple[Tuple[str, ...], str]:
    """Return ``(models, reason)`` from the user's own config, the no-secret fallback."""

    target = resolve_config_path(env=env, cwd=cwd)
    if target is None:
        return (), CATALOG_NO_CONFIG
    try:
        parsed = json.loads(target.path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # A `.jsonc` (or otherwise unparseable) config is not an error here: the caller already
        # has a CLI diagnostic to report, and this path only ever ADDS ids.
        return (), CATALOG_UNPARSEABLE
    models = models_from_config(parsed)
    return models, ("" if models else CATALOG_NO_MODELS)


def discover_models(
    opencode: str = "opencode",
    *,
    timeout: float = CATALOG_TIMEOUT,
    runner: Optional[Callable[..., Any]] = None,
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[Path] = None,
    allow_config_fallback: bool = True,
) -> ModelCatalog:
    """List the models this user's OpenCode can see, without refreshing or mutating anything.

    ``runner`` is the injected subprocess boundary (defaults to ``subprocess.run``) so tests can
    assert the exact argv, ``shell=False``, and the bounded timeout without executing anything.
    Every failure yields an UNAVAILABLE catalog carrying a named ``reason``; none yields a
    successful empty list.
    """

    run = subprocess.run if runner is None else runner
    argv = catalog_argv(opencode)
    reason = ""
    detail = ""

    try:
        proc = run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
        )
    except FileNotFoundError:
        reason, detail = (
            CATALOG_MISSING_BINARY,
            f"{opencode!r} was not found on PATH",
        )
    except subprocess.TimeoutExpired:
        reason, detail = (
            CATALOG_TIMED_OUT,
            f"{' '.join(argv)} did not finish within {timeout:g}s",
        )
    except OSError as exc:
        reason, detail = (
            CATALOG_MISSING_BINARY,
            f"cannot execute {opencode!r}: {type(exc).__name__}",
        )
    else:
        returncode = getattr(proc, "returncode", 1)
        stdout = getattr(proc, "stdout", "") or ""
        if returncode != 0:
            reason, detail = (
                CATALOG_NONZERO_EXIT,
                f"{' '.join(argv)} exited {returncode}",
            )
        else:
            models = parse_models_output(stdout)
            if models:
                return ModelCatalog(models=models, source=CATALOG_SOURCE_CLI)
            if strip_ansi(stdout).strip():
                reason, detail = (
                    CATALOG_UNPARSEABLE,
                    "no line of output was an exact provider/model identifier",
                )
            else:
                reason, detail = (
                    CATALOG_NO_MODELS,
                    f"{' '.join(argv)} listed no models",
                )

    if allow_config_fallback:
        fallback, _fallback_reason = catalog_from_config(env=env, cwd=cwd)
        if fallback:
            return ModelCatalog(
                models=fallback,
                source=CATALOG_SOURCE_CONFIG,
                reason=reason,
                detail=detail,
            )
    return ModelCatalog(source=CATALOG_SOURCE_NONE, reason=reason, detail=detail)


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

    all_provs = _get_all_providers(config)
    found: List[str] = []
    for name, (_cont_key, spec) in all_provs.items():
        if _is_openai_compatible(spec):
            found.append(name)
    return found


def sync_provider(
    config: Dict[str, Any],
    name: str,
    fetch: Callable[[str, str], Optional[Any]],
    allow_insecure: bool = False,
) -> ProviderOutcome:
    """Refresh one provider's ``models`` block in ``config`` (mutated in place on success)."""

    all_provs = _get_all_providers(config)
    if name not in all_provs:
        return ProviderOutcome(name, False, "provider not declared in config")
    cont_key, spec = all_provs[name]
    options = _get_provider_options(spec)
    base_url = (
        options.get("baseURL") or options.get("base_url") or options.get("baseUrl")
    )
    if not isinstance(base_url, str) or not base_url:
        return ProviderOutcome(name, False, SKIP_NO_BASEURL)

    ok, reason = _scheme_ok(base_url, allow_insecure)
    if not ok:
        return ProviderOutcome(name, False, reason)

    raw_key = options.get("apiKey") or options.get("api_key") or spec.get("apiKey")
    api_key = resolve_api_key(raw_key)
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
    config[cont_key][name]["models"] = new_models
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
        os.chmod(tmp, replacement_mode(path))
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
            "your own OpenCode config. Writes changes by default; pass --dry-run to preview. "
            "Pricing is read from a provider's LiteLLM endpoints (/model/info, /model_group/info) "
            "and converted to $ per million tokens; providers without a pricing endpoint (plain "
            "OpenAI, Google) are reported as skipped and left untouched. Rewrites the file with "
            "normalized JSON formatting: the existing indent width is detected and reused, but "
            "byte-for-byte formatting is not preserved. Credentials are sent over https only and "
            "are never printed."
        ),
    )
    parser.add_argument(
        "--config",
        help="Path to opencode.json (default: the config OpenCode itself would load).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the changes (default behavior; retained for backwards compatibility).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing.",
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
    parser.add_argument(
        "--default-model",
        help="Set the top-level default model in opencode.json (e.g. google/antigravity-gemini-4-carbon-medium).",
    )
    parser.add_argument(
        "--small-model",
        help="Set the top-level small_model in opencode.json.",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive prompts.",
    )
    parser.add_argument("--agent", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--json", dest="as_json", action="store_true", help=argparse.SUPPRESS
    )
    parser.add_argument("--no-color", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--fields", default=None, help=argparse.SUPPRESS)
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
    context: Optional[Any] = None,
    which_fn: Optional[Callable[[str], Optional[str]]] = None,
    runner: Optional[Callable[..., Any]] = None,
    homedir: Optional[Path] = None,
    input_fn: Optional[Callable[[str], str]] = None,
) -> int:
    """Preview or apply the model/pricing sync. Returns a process exit code."""

    args = build_parser().parse_args(list(argv or []))
    fetcher = fetch if fetch is not None else http_fetch_json

    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import CommandResult, NextAction, select_output

    ctx = context if context is not None else select_output(args)
    is_agent_or_json = ctx.is_agent or ctx.is_json

    if args.config:
        candidate = Path(args.config).expanduser()
        if not candidate.is_file():
            if is_agent_or_json:
                res = CommandResult(
                    status="cannot-run",
                    summary=f"config not found: {candidate}",
                    command="oc update-models",
                    exit_code=2,
                    verified=False,
                    complete=False,
                )
                return get_renderer(ctx).emit(res, ctx)
            print(f"error: config not found: {candidate}")
            return 2
        target = _classify_target(candidate)
    else:
        target = resolve_config_path(env=env)
        if target is None:
            if is_agent_or_json:
                res = CommandResult(
                    status="cannot-run",
                    summary="no OpenCode config found (set $OPENCODE_CONFIG or pass --config)",
                    command="oc update-models",
                    exit_code=2,
                    verified=False,
                    complete=False,
                )
                return get_renderer(ctx).emit(res, ctx)
            print(
                "error: no OpenCode config found (set $OPENCODE_CONFIG or pass --config)"
            )
            return 2

    is_dry_run = bool(args.dry_run)

    if not target.writable:
        if is_dry_run:
            if is_agent_or_json:
                res = CommandResult(
                    status="cannot-run",
                    summary=f"{target.path} is preview-only: {target.reason}",
                    command="oc update-models",
                    exit_code=2,
                    verified=False,
                    complete=False,
                )
                return get_renderer(ctx).emit(res, ctx)
            print(f"note: {target.path} is preview-only: {target.reason}")
            return 2
        if is_agent_or_json:
            res = CommandResult(
                status="cannot-run",
                summary=f"refusing to rewrite {target.path}: {target.reason}",
                command="oc update-models",
                exit_code=2,
                verified=False,
                complete=False,
            )
            return get_renderer(ctx).emit(res, ctx)
        print(f"error: refusing to rewrite {target.path}: {target.reason}")
        return 2

    original = target.path.read_text(encoding="utf-8")
    config = json.loads(original)

    # 1. Multi-harness probe and model reconciliation
    harnesses = probe_installed_harnesses(
        which_fn=which_fn, runner=runner, homedir=homedir, env=env
    )
    prefer_v2 = is_v2()
    harness_added = reconcile_harness_models(config, harnesses, prefer_v2=prefer_v2)

    # 2. OpenAI-compatible LiteLLM pricing sync
    providers = discover_providers(config)
    outcomes = [
        sync_provider(config, name, fetcher, allow_insecure=args.allow_insecure)
        for name in providers
    ]
    synced = [o for o in outcomes if o.synced]
    mutated = [o for o in synced if o.has_changes]

    # 3. Default and small model inspection and selection
    curr_default = config.get("model") or "(not set)"
    curr_small = config.get("small_model") or config.get("smallModel") or "(not set)"
    model_changed = False
    small_changed = False

    if args.default_model:
        target_model = args.default_model.strip()
        if not _model_re().match(target_model):
            msg = f"invalid default model format: {target_model!r}"
            if is_agent_or_json:
                res = CommandResult(
                    status="cannot-run",
                    summary=msg,
                    command="oc update-models",
                    exit_code=2,
                    verified=False,
                    complete=False,
                )
                return get_renderer(ctx).emit(res, ctx)
            print(f"error: {msg}")
            return 2
        if config.get("model") != target_model:
            config["model"] = target_model
            model_changed = True

    if args.small_model:
        target_small = args.small_model.strip()
        if not _model_re().match(target_small):
            msg = f"invalid small model format: {target_small!r}"
            if is_agent_or_json:
                res = CommandResult(
                    status="cannot-run",
                    summary=msg,
                    command="oc update-models",
                    exit_code=2,
                    verified=False,
                    complete=False,
                )
                return get_renderer(ctx).emit(res, ctx)
            print(f"error: {msg}")
            return 2
        if config.get("small_model") != target_small:
            config["small_model"] = target_small
            small_changed = True

    from agent_workflows import term as _term

    is_interactive = (
        (input_fn is not None or _term.is_interactive())
        and not is_agent_or_json
        and not getattr(args, "no_interactive", False)
        and not args.default_model
    )

    if is_interactive and not args.default_model:
        ask = input_fn if input_fn is not None else input
        try:
            ans = (
                ask(f"Change default model (current: {curr_default})? [y/N]: ")
                .strip()
                .lower()
            )
            if ans in ("y", "yes"):
                choice = ask("Enter new default model (<provider>/<model>): ").strip()
                if choice:
                    if _model_re().match(choice):
                        config["model"] = choice
                        model_changed = True
                        print(f"default model updated to: {choice}")
                    else:
                        print(
                            f"warning: '{choice}' is not a valid provider/model identifier; skipped"
                        )
                ans_sm = (
                    ask(f"Change small model (current: {curr_small})? [y/N]: ")
                    .strip()
                    .lower()
                )
                if ans_sm in ("y", "yes"):
                    choice_sm = ask(
                        "Enter new small model (<provider>/<model>): "
                    ).strip()
                    if choice_sm:
                        if _model_re().match(choice_sm):
                            config["small_model"] = choice_sm
                            small_changed = True
                            print(f"small model updated to: {choice_sm}")
                        else:
                            print(
                                f"warning: '{choice_sm}' is not a valid provider/model identifier; skipped"
                            )
        except (EOFError, KeyboardInterrupt):
            pass

    total_harness_added = sum(len(models) for models in harness_added.values())
    has_changes = bool(mutated or total_harness_added or model_changed or small_changed)

    if is_agent_or_json:
        if not has_changes:
            res = CommandResult(
                status="clean",
                summary="providers and models up to date; no changes",
                command="oc update-models",
                applied=False,
                complete=True,
            )
            return get_renderer(ctx).emit(res, ctx)
        if is_dry_run:
            res = CommandResult(
                status="preview",
                summary=f"{len(mutated)} provider(s) and {total_harness_added} harness model(s) have changes",
                command="oc update-models",
                applied=False,
                complete=False,
                next_actions=[
                    NextAction(
                        command="aw oc update-models",
                        description="apply model updates",
                    )
                ],
            )
            return get_renderer(ctx).emit(res, ctx)
        text = serialize(config, detect_indent(original))
        backup_path = write_config(
            target.path, text, backup=not args.no_backup, original=original
        )
        res = CommandResult(
            status="ok",
            summary=f"wrote {target.path}",
            command="oc update-models",
            applied=True,
            complete=True,
        )
        return get_renderer(ctx).emit(res, ctx)

    print(f"config: {target.path}")
    print(f"current default model: {curr_default}")
    print(f"current small model: {curr_small}")
    print("\ndiscovered harnesses:")
    for h_name in ("agy", "claude", "codex", "kiro"):
        h = harnesses.get(h_name)
        if not h:
            continue
        if h.installed:
            detail_str = f"installed ({h.executable})"
            if h.models:
                detail_str += f" - {len(h.models)} model(s) available"
            if h.notes:
                detail_str += f" ({h.notes})"
            print(f"  {h.name}: {detail_str}")
        else:
            print(f"  {h.name}: not installed")
    print()

    if not providers and not outcomes:
        print(
            f"no OpenAI-compatible gateway providers to sync pricing with in {target.path}"
        )
    for outcome in outcomes:
        if not outcome.synced:
            print(f"skipped {outcome.name}: {outcome.skip_reason}")
            continue
        if not outcome.has_changes:
            print(f"{outcome.name}: up to date")
            continue
        total = len(outcome.added) + len(outcome.removed) + len(outcome.changed)
        print(f"{outcome.name}: {total} pricing change(s)")
        for line in _describe(outcome):
            print(line)

    for prov, added_list in harness_added.items():
        print(f"{prov}: {len(added_list)} model(s) added from harness discovery")
        for item in added_list:
            print(f"  + ADDED   {item}")

    if model_changed:
        print(f"default model: {curr_default} -> {config.get('model')}")
    if small_changed:
        print(f"small model: {curr_small} -> {config.get('small_model')}")

    if not has_changes:
        return 0
    if is_dry_run:
        print("\npreview only; re-run without --dry-run to write")
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

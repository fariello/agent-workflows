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
import hashlib
import json
import os
import re
import subprocess
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

    Reads ONLY the per-provider model keys. It never looks at a provider's options block,
    credential value, or headers, so no secret can reach the caller.
    """

    if not isinstance(config, Mapping):
        return ()
    providers = config.get("provider")
    if not isinstance(providers, Mapping):
        return ()
    pattern = _model_re()
    found: Dict[str, None] = {}
    for provider_name, spec in providers.items():
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
    providers = config.get("provider")
    if not isinstance(providers, Mapping):
        return {}, CARD_MODEL_NOT_DECLARED
    spec = providers.get(provider_name)
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

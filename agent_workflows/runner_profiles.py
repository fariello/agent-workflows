"""Named runner launch profiles: the versioned, user-local source of truth (schema version 1).

`runprofile` Order 01 (`f2mrsw`) E-01..E-04. A PROFILE binds a runner to a small set of
STRUCTURED launch fields, so a user can say `gem` instead of repeating
`--model <provider/model> --variant high`. This module is the whole authority for what a
profile IS, where it is STORED, how it is MUTATED, and how a launch is RESOLVED. Later Set
children (the wizard `p0l1to`, the OpenCode runner integration `3cm15q`, the host-neutral
dispatch `ygzq71`) CONSUME this module; none of them may re-parse or re-store profiles.

WHAT A PROFILE DELIBERATELY IS NOT, because this is the security boundary of the feature:
it is NOT a command, NOT an argv fragment, NOT a shell string, NOT an environment mapping,
NOT an executable path, NOT a prompt, NOT a permission set, and NOT a place for a token or
API key. Every one of those is refused by name (:data:`FORBIDDEN_PROFILE_KEYS`) with an
explicit message, and any OTHER unrecognized key is refused too. A raw `args` string would
turn `aw run as gem` into a quoting-and-injection surface; a credential field would turn a
convenience file into a secret store. This module never invokes a process: it returns typed
fields and the caller builds its own argv list.

Schema version 1 document::

    {
      "schema_version": 1,
      "default_runner": "oc",                 # optional; required only for GENERIC dispatch
      "defaults": {
        "profiles": {"oc": "gem"},            # optional per-runner default profile
        "validate": false                     # optional TRI-STATE verification default
      },
      "profiles": {
        "gem": {
          "runner": "oc",                     # required; canonicalized ("opencode" -> "oc")
          "model": "google/gemini-3.7-flash", # required; EXACT provider/model, never guessed
          "variant": "high",                  # optional
          "agent": "build",                   # optional
          "validate": true                    # optional TRI-STATE verification default
        }
      }
    }

`validate` IS A TRI-STATE (present-true / present-false / ABSENT) at both levels, and absent
MUST NOT be read as `false`. It records the per-model verification default: the maintainer
measured an independent verifier turn adding only nits on their primary model for roughly 33%
extra cost, so that profile runs with verification OFF, while a cheaper model wants it ON.
Without the field that choice is a flag the operator must remember on every invocation, which
is how backlog `vju5ba` (`--validate` defaulting FALSE while `--no-self-finalize` defaulted
TRUE, so self-finalize could never fire) went unnoticed across five overnight runs.

RESOLUTION PRECEDENCE IS EXACT AND TESTED. For a launch field
(`runner`/`model`/`variant`/`agent`)::

    explicit caller field  >  explicitly named profile  >  per-runner default profile  >
    host default (no argument at all)

For `validate`, with an ABSENT level falling THROUGH rather than reading as `false`::

    explicit --validate/--no-validate  >  profile's own `validate`  >
    `defaults.validate`  >  the shipped default (:data:`SHIPPED_VALIDATE_DEFAULT`, False,
    matching `oc_runipd`'s `--validate` BooleanOptionalAction default)

AN EXPLICIT FLAG ALWAYS WINS. A stored default silently overriding an explicit flag would
make the flag a lie, and would reproduce `vju5ba` inverted: two independently sensible
defaults quietly cancelling each other out.

STORAGE IS USER-LOCAL AND SEPARATE ON PURPOSE. The file is
``<config_dir>/runner-profiles.json`` (:func:`store_path`, reusing
:func:`agent_workflows.config.config_dir` so there is ONE XDG convention), NOT tracked
``.aw/config/**`` and NOT the main ``config.json``. Two independent reasons: a requested model
identifier can be institution-specific and would disclose local topology if committed to a
public project, and ``config.py`` has a pending restructuring whose migration this feature must
not be coupled to. Writes are atomic (temp file in the same directory + ``os.replace``) and
validate the WHOLE new document first, so an interrupted or invalid write leaves the previous
valid bytes byte-identical.

READS DISTINGUISH ABSENT FROM MALFORMED, and that distinction is load-bearing. Absent is
normal (a user with no profiles) and yields an empty config. Malformed or version-unsupported
raises :class:`ProfileSchemaError` rather than behaving as empty, because degrading to empty
would silently launch the HOST DEFAULT model instead of the costly/private one the user
configured, and the operator would only find out from the bill.

Pure stdlib, no third-party imports, no network, no subprocess (D138/D139).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Mapping, NamedTuple, Optional, Tuple

from agent_workflows import config as _config

# ==================================================================================================
# Constants & vocabularies
# ==================================================================================================

#: The only schema version this module writes.
SCHEMA_VERSION = 1

#: Versions this module can READ. A document declaring anything else fails closed.
SUPPORTED_SCHEMA_VERSIONS: frozenset = frozenset((1,))

#: The store's file name, inside :func:`agent_workflows.config.config_dir`.
STORE_NAME = "runner-profiles.json"

#: The shipped `validate` default, used only when no level supplied a value. FALSE, matching
#: `oc_runipd.py`'s `--validate` (`BooleanOptionalAction`, `default=False`), so this module
#: cannot silently change what an un-configured run does today.
SHIPPED_VALIDATE_DEFAULT = False

#: Top-level document keys. Anything else is refused (no silent widening).
ALLOWED_DOCUMENT_KEYS: frozenset = frozenset(
    ("schema_version", "default_runner", "defaults", "profiles")
)

#: Keys inside the top-level ``defaults`` object. ``profiles`` holds the per-runner default
#: profile map; ``validate`` is the tri-state verification default. Keeping the per-runner map
#: NESTED (rather than putting runner names directly in ``defaults``) means a future runner can
#: never collide with a settings key such as ``validate``.
ALLOWED_DEFAULTS_KEYS: frozenset = frozenset(("profiles", "validate"))

#: Keys inside one profile object.
ALLOWED_PROFILE_KEYS: frozenset = frozenset(
    ("runner", "model", "variant", "agent", "validate")
)

#: Keys refused BY NAME with an explicit reason. Unknown keys are refused anyway; this set
#: exists so the error explains WHY the field will never be added, rather than reading as an
#: oversight a later contributor might "fix". Each entry is a capability that would convert a
#: convenience alias into a command-injection, credential-disclosure, or behavior-override
#: surface.
FORBIDDEN_PROFILE_KEYS: frozenset = frozenset(
    (
        "api_key",
        "apikey",
        "args",
        "argv",
        "auth",
        "bearer",
        "cmd",
        "command",
        "credential",
        "credentials",
        "env",
        "environment",
        "exec",
        "executable",
        "headers",
        "key",
        "password",
        "permission",
        "permissions",
        "prompt",
        "secret",
        "shell",
        "system_prompt",
        "token",
    )
)

#: Structural words in the `run as <profile>` grammar. A profile may not be named one of
#: these, because `aw run as default` would be ambiguous at the grammar level rather than at
#: the lookup level. Command-LIKE names (`status`, `report`, `run`, `show`, `evidence`) remain
#: LEGAL on purpose: a name is only ever resolved AFTER the `as` keyword, so it cannot shadow a
#: real subcommand, and forbidding them would over-reserve the namespace for no safety gain.
RESERVED_PROFILE_NAMES: frozenset = frozenset(("as", "default"))

MAX_PROFILE_NAME_LEN = 32
MAX_MODEL_LEN = 200
MAX_FIELD_LEN = 64

#: Lowercase letters/digits/hyphens, beginning with a letter, bounded.
PROFILE_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,%d}$" % (MAX_PROFILE_NAME_LEN - 1))

#: An EXACT model identifier: two or more `/`-separated segments (so `uri/its_direct/pt3-...`
#: is as valid as `google/gemini-3.7-flash`), drawn from a deliberately narrow character class.
#: The narrowness IS the control: no whitespace, quote, backslash, `$`, backtick, `;`, `&`, or
#: `|` can enter a stored model, so a stored value cannot carry a shell fragment even if some
#: future caller were careless with it.
MODEL_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._+:-]*(?:/[A-Za-z0-9][A-Za-z0-9._+:-]*)+$"
)

#: Variant / agent: one bounded token from the same narrow class, no separators.
FIELD_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,%d}$" % (MAX_FIELD_LEN - 1))


class RunnerSpec(NamedTuple):
    """One registered runner (host) and the launch fields it actually supports.

    THE REGISTRY SEAM. Version 1 registers OpenCode only. Adding a host is ONE ROW here plus
    that host's own adapter work; it is deliberately data rather than a `register_runner()`
    mutator, so nothing at runtime can widen the accepted runner set.
    """

    name: str
    aliases: Tuple[str, ...]
    supports_variant: bool
    supports_agent: bool


#: Canonical runner name -> spec. Version 1: OpenCode (`oc`), whose CLI accepts `--model`,
#: `--variant` and `--agent` (`oc_runipd.py` `run_opencode` appends exactly those three).
RUNNER_REGISTRY: Dict[str, RunnerSpec] = {
    "oc": RunnerSpec(
        name="oc", aliases=("opencode",), supports_variant=True, supports_agent=True
    ),
}


# ==================================================================================================
# Errors (stable classes; every failure is typed, none is a bare ValueError)
# ==================================================================================================


class RunnerProfileError(Exception):
    """Base class for every runner-profile failure."""


class ProfileSchemaError(RunnerProfileError):
    """A document, profile, name, or field value is structurally invalid or unsupported."""


class ProfileStoreError(RunnerProfileError):
    """The store could not be read or written (I/O), or a write was refused fail-closed."""


class ProfileNotFoundError(RunnerProfileError):
    """A named profile does not exist."""


class ProfileExistsError(RunnerProfileError):
    """A profile of that name already exists and no replacement was authorized."""


class ProfileResolutionError(RunnerProfileError):
    """A launch could not be resolved (dangling default, unknown runner, wrong runner...)."""


# ==================================================================================================
# Typed records (immutable)
# ==================================================================================================


@dataclass(frozen=True)
class LaunchProfile:
    """One named launch profile: structured fields ONLY.

    ``validate`` is a TRI-STATE: ``None`` means "not specified at this level" and falls through
    to the next precedence level. It is NOT the same as ``False``.
    """

    runner: str
    model: str
    variant: Optional[str] = None
    agent: Optional[str] = None
    validate: Optional[bool] = None

    def to_document(self) -> Dict[str, Any]:
        """Return the JSON object for this profile, omitting absent optional fields."""

        out: Dict[str, Any] = {"runner": self.runner, "model": self.model}
        if self.variant is not None:
            out["variant"] = self.variant
        if self.agent is not None:
            out["agent"] = self.agent
        if self.validate is not None:
            out["validate"] = self.validate
        return out


@dataclass(frozen=True)
class ProfileConfig:
    """The whole stored configuration, plus where it came from.

    ``present`` records whether a file actually existed. Absent (``present=False``) is NORMAL
    and yields an empty config; MALFORMED never reaches here, because :func:`load` raises.
    """

    schema_version: int = SCHEMA_VERSION
    default_runner: Optional[str] = None
    default_profiles: Mapping[str, str] = field(default_factory=dict)
    validate: Optional[bool] = None
    profiles: Mapping[str, LaunchProfile] = field(default_factory=dict)
    source: Optional[Path] = None
    present: bool = False

    def __post_init__(self) -> None:
        # True immutability for the mappings, so a caller cannot mutate a loaded config in
        # place and have the change silently affect an already-resolved launch.
        object.__setattr__(
            self, "default_profiles", MappingProxyType(dict(self.default_profiles))
        )
        object.__setattr__(self, "profiles", MappingProxyType(dict(self.profiles)))

    # -- reads -------------------------------------------------------------------------------

    def get(self, name: str) -> LaunchProfile:
        """Return one profile by name, or raise :class:`ProfileNotFoundError`."""

        validate_profile_name(name)
        try:
            return self.profiles[name]
        except KeyError:
            known = ", ".join(sorted(self.profiles)) or "(none)"
            raise ProfileNotFoundError(
                f"no runner profile named {name!r} (known profiles: {known}). "
                f"Create it with 'aw oc profile add {name}'."
            ) from None

    def default_profile_for(self, runner: str) -> Optional[str]:
        """Return the per-runner default profile NAME, or None when none is configured."""

        return self.default_profiles.get(canonical_runner(runner))

    def to_document(self) -> Dict[str, Any]:
        """Return the canonical JSON document, omitting absent optional parts."""

        doc: Dict[str, Any] = {"schema_version": self.schema_version}
        if self.default_runner is not None:
            doc["default_runner"] = self.default_runner
        defaults: Dict[str, Any] = {}
        if self.default_profiles:
            defaults["profiles"] = dict(self.default_profiles)
        if self.validate is not None:
            defaults["validate"] = self.validate
        if defaults:
            doc["defaults"] = defaults
        doc["profiles"] = {
            name: self.profiles[name].to_document() for name in sorted(self.profiles)
        }
        return doc

    @property
    def digest(self) -> str:
        """sha256 over the canonical bytes of this configuration.

        Frozen into durable run state by `3cm15q`, so a run can prove WHICH configuration it
        launched from even after the file is later edited.
        """

        return config_digest(self)


class ResolvedLaunch(NamedTuple):
    """One auditable resolved launch: every value plus WHERE it came from.

    ``model``/``variant``/``agent`` may be ``None``, which means "pass no argument and let the
    host use its own default". That is a DELIBERATE absence recorded as such in
    ``provenance``, never a guess.
    """

    runner: str
    model: Optional[str]
    variant: Optional[str]
    agent: Optional[str]
    validate: bool
    requested_profile: Optional[str]
    applied_profile: Optional[str]
    config_source: Optional[str]
    config_present: bool
    config_digest: str
    provenance: Mapping[str, str]


#: Provenance vocabulary, one value per resolved field. Closed set so a report can render it.
PROVENANCE_EXPLICIT = "explicit"  # the caller passed it (CLI flag)
PROVENANCE_PROFILE = "profile"  # the explicitly named profile supplied it
PROVENANCE_DEFAULT_PROFILE = (
    "default-profile"  # the per-runner default profile supplied it
)
PROVENANCE_DEFAULTS = "defaults"  # the top-level `defaults` object supplied it
PROVENANCE_DEFAULT_RUNNER = "default-runner"  # `default_runner` supplied the runner
PROVENANCE_SHIPPED = "shipped-default"  # the module's shipped default
PROVENANCE_HOST_DEFAULT = "host-default"  # nothing supplied it; pass no argument

PROVENANCE_VALUES: frozenset = frozenset(
    (
        PROVENANCE_EXPLICIT,
        PROVENANCE_PROFILE,
        PROVENANCE_DEFAULT_PROFILE,
        PROVENANCE_DEFAULTS,
        PROVENANCE_DEFAULT_RUNNER,
        PROVENANCE_SHIPPED,
        PROVENANCE_HOST_DEFAULT,
    )
)


# ==================================================================================================
# Validation (E-01)
# ==================================================================================================


def canonical_runner(name: Any) -> str:
    """Canonicalize a runner name, or raise :class:`ProfileSchemaError`.

    Version 1 maps ``opencode`` -> ``oc`` and otherwise accepts only a REGISTERED runner. An
    unregistered runner is refused rather than stored optimistically, because a profile naming
    a host nobody can launch is a failure the user should see at write time, not at 3am.
    """

    if not isinstance(name, str) or not name.strip():
        raise ProfileSchemaError("runner must be a non-empty string")
    lowered = name.strip().lower()
    if lowered in RUNNER_REGISTRY:
        return lowered
    for canonical, spec in RUNNER_REGISTRY.items():
        if lowered in spec.aliases:
            return canonical
    known = ", ".join(sorted(RUNNER_REGISTRY))
    raise ProfileSchemaError(
        f"unknown runner {name!r}; version {SCHEMA_VERSION} registers: {known}"
    )


def validate_profile_name(name: Any) -> str:
    """Validate a profile name against the grammar, or raise :class:`ProfileSchemaError`."""

    if not isinstance(name, str):
        raise ProfileSchemaError(
            f"profile name must be a string, got {type(name).__name__}"
        )
    if name in RESERVED_PROFILE_NAMES:
        reserved = ", ".join(sorted(RESERVED_PROFILE_NAMES))
        raise ProfileSchemaError(
            f"profile name {name!r} is reserved by the 'run as <profile>' grammar "
            f"(reserved: {reserved})"
        )
    if not PROFILE_NAME_RE.match(name):
        raise ProfileSchemaError(
            f"invalid profile name {name!r}: use lowercase letters, digits and hyphens, "
            f"beginning with a letter, at most {MAX_PROFILE_NAME_LEN} characters"
        )
    return name


def validate_model(value: Any) -> str:
    """Validate an EXACT model identifier, or raise :class:`ProfileSchemaError`."""

    if not isinstance(value, str) or not value:
        raise ProfileSchemaError("model is required and must be a non-empty string")
    if len(value) > MAX_MODEL_LEN:
        raise ProfileSchemaError(f"model is longer than {MAX_MODEL_LEN} characters")
    if not MODEL_RE.match(value):
        raise ProfileSchemaError(
            f"invalid model {value!r}: expected an exact 'provider/model' identifier "
            "using letters, digits and . _ + : - separated by '/'"
        )
    return value


def _validate_field(kind: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ProfileSchemaError(f"{kind} must be a non-empty string when present")
    if not FIELD_RE.match(value):
        raise ProfileSchemaError(
            f"invalid {kind} {value!r}: expected one token of letters, digits and . _ - "
            f"at most {MAX_FIELD_LEN} characters"
        )
    return value


def _validate_tristate(kind: str, value: Any) -> Optional[bool]:
    """Validate a tri-state boolean. ``None``/absent stays ``None`` (it is NOT ``False``)."""

    if value is None:
        return None
    if not isinstance(value, bool):
        raise ProfileSchemaError(
            f"{kind} must be true or false when present (tri-state: omit the key to leave it "
            f"unspecified), got {type(value).__name__}"
        )
    return value


def _reject_unknown_keys(
    where: str, mapping: Mapping[str, Any], allowed: frozenset
) -> None:
    unknown = sorted(k for k in mapping if k not in allowed)
    if not unknown:
        return
    forbidden = [
        k for k in unknown if str(k).lower().replace("-", "_") in FORBIDDEN_PROFILE_KEYS
    ]
    if forbidden:
        raise ProfileSchemaError(
            f"{where}: field(s) {forbidden} are refused BY DESIGN. A profile stores structured "
            "launch fields only; arbitrary arguments, shell text, environment, executables, "
            "prompts, permissions and credentials are never stored or resolved, because that "
            "would make an alias a command-injection and secret-disclosure surface."
        )
    raise ProfileSchemaError(
        f"{where}: unknown field(s) {unknown}; allowed: {sorted(allowed)}"
    )


def parse_profile(name: str, raw: Any) -> LaunchProfile:
    """Validate one raw profile object into a :class:`LaunchProfile` (fail closed)."""

    validate_profile_name(name)
    if not isinstance(raw, Mapping):
        raise ProfileSchemaError(f"profile {name!r} must be an object")
    _reject_unknown_keys(f"profile {name!r}", raw, ALLOWED_PROFILE_KEYS)
    if "runner" not in raw:
        raise ProfileSchemaError(
            f"profile {name!r} is missing the required 'runner' field"
        )
    if "model" not in raw:
        raise ProfileSchemaError(
            f"profile {name!r} is missing the required 'model' field"
        )
    runner = canonical_runner(raw["runner"])
    spec = RUNNER_REGISTRY[runner]
    model = validate_model(raw["model"])
    variant = raw.get("variant")
    if variant is not None:
        variant = _validate_field("variant", variant)
        if not spec.supports_variant:
            raise ProfileSchemaError(
                f"profile {name!r}: runner {runner!r} does not support a model variant"
            )
    agent = raw.get("agent")
    if agent is not None:
        agent = _validate_field("agent", agent)
        if not spec.supports_agent:
            raise ProfileSchemaError(
                f"profile {name!r}: runner {runner!r} does not support an agent"
            )
    validate = _validate_tristate(f"profile {name!r} 'validate'", raw.get("validate"))
    return LaunchProfile(
        runner=runner, model=model, variant=variant, agent=agent, validate=validate
    )


def _validate_referential_integrity(
    default_runner: Optional[str],
    default_profiles: Mapping[str, str],
    profiles: Mapping[str, LaunchProfile],
) -> None:
    """A default reference must resolve to an existing profile OF THAT RUNNER.

    A dangling default is the failure mode that costs real money: the referenced profile is
    gone, so an unqualified run silently falls back to the host default model instead of the
    one the user chose.
    """

    for runner, profile_name in sorted(default_profiles.items()):
        if profile_name not in profiles:
            raise ProfileSchemaError(
                f"defaults.profiles[{runner!r}] points at {profile_name!r}, which does not "
                "exist. Remove the default or create the profile; a dangling default would "
                "silently launch the host default model."
            )
        actual = profiles[profile_name].runner
        if actual != runner:
            raise ProfileSchemaError(
                f"defaults.profiles[{runner!r}] points at profile {profile_name!r}, whose "
                f"runner is {actual!r}"
            )
    if default_runner is not None and default_runner not in RUNNER_REGISTRY:
        raise ProfileSchemaError(
            f"default_runner {default_runner!r} is not a registered runner"
        )


def from_document(
    raw: Any, source: Optional[Path] = None, present: bool = True
) -> ProfileConfig:
    """Validate a whole raw document into a :class:`ProfileConfig` (fail closed).

    Raises :class:`ProfileSchemaError` on ANY violation, including an unsupported
    ``schema_version``. Never returns a partially-accepted configuration: half a config is
    indistinguishable from a working one at the call site, and the missing half is exactly the
    part that decides which model gets billed.
    """

    if not isinstance(raw, Mapping):
        raise ProfileSchemaError("runner-profiles document must be a JSON object")
    _reject_unknown_keys("document", raw, ALLOWED_DOCUMENT_KEYS)

    version = raw.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ProfileSchemaError("schema_version is required and must be an integer")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ProfileSchemaError(
            f"unsupported schema_version {version}; this aw understands "
            f"{sorted(SUPPORTED_SCHEMA_VERSIONS)}. Upgrade aw rather than editing the file: "
            "treating an unknown shape as empty would silently launch the wrong model."
        )

    raw_profiles = raw.get("profiles", {})
    if not isinstance(raw_profiles, Mapping):
        raise ProfileSchemaError("'profiles' must be an object")
    profiles = {
        name: parse_profile(name, value) for name, value in raw_profiles.items()
    }

    default_runner = raw.get("default_runner")
    if default_runner is not None:
        default_runner = canonical_runner(default_runner)

    raw_defaults = raw.get("defaults", {})
    if not isinstance(raw_defaults, Mapping):
        raise ProfileSchemaError("'defaults' must be an object")
    _reject_unknown_keys("defaults", raw_defaults, ALLOWED_DEFAULTS_KEYS)

    raw_default_profiles = raw_defaults.get("profiles", {})
    if not isinstance(raw_default_profiles, Mapping):
        raise ProfileSchemaError("'defaults.profiles' must be an object")
    default_profiles: Dict[str, str] = {}
    for runner, profile_name in raw_default_profiles.items():
        canonical = canonical_runner(runner)
        if not isinstance(profile_name, str):
            raise ProfileSchemaError(
                f"defaults.profiles[{runner!r}] must be a profile name string"
            )
        validate_profile_name(profile_name)
        default_profiles[canonical] = profile_name

    validate = _validate_tristate("defaults.validate", raw_defaults.get("validate"))
    _validate_referential_integrity(default_runner, default_profiles, profiles)

    return ProfileConfig(
        schema_version=version,
        default_runner=default_runner,
        default_profiles=default_profiles,
        validate=validate,
        profiles=profiles,
        source=source,
        present=present,
    )


def empty_config(source: Optional[Path] = None, present: bool = False) -> ProfileConfig:
    """Return a valid, empty configuration at the current schema version."""

    return ProfileConfig(source=source, present=present)


# ==================================================================================================
# Store (E-02): user-local, XDG-aware, atomic
# ==================================================================================================


def store_dir() -> Path:
    """Return the user-local configuration directory (reuses the ONE XDG convention)."""

    return _config.config_dir()


def store_path() -> Path:
    """Return the full path to ``runner-profiles.json``.

    Deliberately BESIDE ``config.json``, never inside it, and never inside the repository:
    ``config.py`` has a fixed allowlist plus a pending restructuring, and a stored model
    identifier can be institution-specific and must not enter a public tree.
    """

    return store_dir() / STORE_NAME


def dumps(cfg: ProfileConfig) -> str:
    """Return the deterministic bytes (as text) this configuration serializes to."""

    return json.dumps(cfg.to_document(), indent=2, sort_keys=True) + "\n"


def config_digest(cfg: ProfileConfig) -> str:
    """Return the sha256 hex digest of a configuration's canonical bytes."""

    return hashlib.sha256(dumps(cfg).encode("utf-8")).hexdigest()


def load(path: Optional[Path] = None) -> ProfileConfig:
    """Load the configuration.

    ABSENT -> a valid EMPTY config (``present=False``). MALFORMED, unreadable, or
    version-unsupported -> :class:`ProfileSchemaError` / :class:`ProfileStoreError`. It never
    degrades a broken file to "empty": that would silently launch the host default model.
    """

    target = Path(path) if path is not None else store_path()
    if not target.exists():
        return empty_config(source=target, present=False)
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProfileStoreError(f"cannot read {target}: {exc}") from exc
    try:
        raw = json.loads(text)
    except ValueError as exc:
        raise ProfileSchemaError(
            f"{target} is not valid JSON: {exc}. Fix or remove the file; it is NOT treated as "
            "empty, because that would silently launch a different model than you configured."
        ) from exc
    return from_document(raw, source=target, present=True)


def _on_disk_version(target: Path) -> Optional[int]:
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if isinstance(raw, Mapping):
        version = raw.get("schema_version")
        if isinstance(version, int) and not isinstance(version, bool):
            return version
    return None


def save(cfg: ProfileConfig, path: Optional[Path] = None) -> Path:
    """Validate the WHOLE document, then write it atomically. Returns the path written.

    Order matters and is the point: validate first, so an invalid configuration can never
    replace a valid one; then temp file in the SAME directory + ``os.replace``, so an
    interrupted write leaves the previous bytes byte-identical rather than truncated. Refuses
    fail-closed to overwrite a file written by a NEWER aw. Never reads, logs, copies, or
    persists a provider credential: there is no field for one (:data:`FORBIDDEN_PROFILE_KEYS`).
    """

    target = Path(path) if path is not None else store_path()
    # Round-trip through the validator so a hand-built record cannot bypass validation.
    validated = from_document(cfg.to_document(), source=target, present=True)

    if target.is_file():
        existing = _on_disk_version(target)
        if existing is not None and existing not in SUPPORTED_SCHEMA_VERSIONS:
            raise ProfileStoreError(
                f"refusing to overwrite {target}: it declares schema_version {existing}, which "
                f"this aw does not understand (supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)}). "
                "Nothing was changed."
            )

    payload = dumps(validated)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ProfileStoreError(f"cannot create {target.parent}: {exc}") from exc

    try:
        fd, tmp_name = tempfile.mkstemp(
            dir=str(target.parent), prefix=".runner-profiles.", suffix=".tmp"
        )
    except OSError as exc:
        raise ProfileStoreError(
            f"cannot create a temp file beside {target}: {exc}"
        ) from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, str(target))
    except BaseException as exc:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        if isinstance(exc, OSError):
            raise ProfileStoreError(f"cannot write {target}: {exc}") from exc
        raise
    return target


# ==================================================================================================
# Pure mutations (E-03)
# ==================================================================================================


def _replace(cfg: ProfileConfig, **changes: Any) -> ProfileConfig:
    base: Dict[str, Any] = {
        "schema_version": cfg.schema_version,
        "default_runner": cfg.default_runner,
        "default_profiles": dict(cfg.default_profiles),
        "validate": cfg.validate,
        "profiles": dict(cfg.profiles),
        "source": cfg.source,
        "present": cfg.present,
    }
    base.update(changes)
    result = ProfileConfig(**base)
    _validate_referential_integrity(
        result.default_runner, result.default_profiles, result.profiles
    )
    return result


def add_profile(
    cfg: ProfileConfig, name: str, profile: LaunchProfile, replace: bool = False
) -> ProfileConfig:
    """Return a new config with ``name`` added (or replaced when ``replace``).

    Refuses a silent overwrite: clobbering `gem` because the user forgot it existed is how a
    run ends up on an unintended (and possibly far more expensive) model.
    """

    validate_profile_name(name)
    validated = parse_profile(name, profile.to_document())
    if name in cfg.profiles and not replace:
        raise ProfileExistsError(
            f"profile {name!r} already exists; pass replace=True (CLI: --replace) to overwrite it"
        )
    profiles = dict(cfg.profiles)
    profiles[name] = validated
    return _replace(cfg, profiles=profiles)


def remove_profile(
    cfg: ProfileConfig,
    name: str,
    clear_default: bool = False,
    replacement: Optional[str] = None,
) -> ProfileConfig:
    """Return a new config without ``name``.

    When the profile is REFERENCED as a per-runner default, the caller must make the decision
    EXPLICIT (``clear_default=True`` or ``replacement=<other profile>``). Silently dropping the
    reference would leave the user's unqualified runs quietly using the host default model.
    """

    validate_profile_name(name)
    if name not in cfg.profiles:
        raise ProfileNotFoundError(f"no runner profile named {name!r}")
    if clear_default and replacement is not None:
        raise ProfileResolutionError(
            "choose one: clear_default=True OR replacement=<profile>, not both"
        )

    referencing = sorted(r for r, p in cfg.default_profiles.items() if p == name)
    default_profiles = dict(cfg.default_profiles)
    if referencing:
        if replacement is not None:
            if replacement not in cfg.profiles or replacement == name:
                raise ProfileNotFoundError(
                    f"replacement profile {replacement!r} does not exist"
                )
            for runner in referencing:
                if cfg.profiles[replacement].runner != runner:
                    raise ProfileResolutionError(
                        f"replacement profile {replacement!r} runs on "
                        f"{cfg.profiles[replacement].runner!r}, not {runner!r}"
                    )
                default_profiles[runner] = replacement
        elif clear_default:
            for runner in referencing:
                default_profiles.pop(runner, None)
        else:
            raise ProfileResolutionError(
                f"profile {name!r} is the default for {referencing}. Decide explicitly: clear "
                "the default (clear_default=True) or name a replacement (replacement=<profile>). "
                "Removing it silently would fall back to the host default model."
            )

    profiles = dict(cfg.profiles)
    profiles.pop(name)
    return _replace(cfg, profiles=profiles, default_profiles=default_profiles)


def set_default_profile(cfg: ProfileConfig, name: str) -> ProfileConfig:
    """Return a new config whose per-runner default (for that profile's runner) is ``name``."""

    profile = cfg.get(name)
    default_profiles = dict(cfg.default_profiles)
    default_profiles[profile.runner] = name
    return _replace(cfg, default_profiles=default_profiles)


def clear_default_profile(cfg: ProfileConfig, runner: str) -> ProfileConfig:
    """Return a new config with no default profile for ``runner`` (idempotent)."""

    canonical = canonical_runner(runner)
    default_profiles = dict(cfg.default_profiles)
    default_profiles.pop(canonical, None)
    return _replace(cfg, default_profiles=default_profiles)


def set_default_runner(cfg: ProfileConfig, runner: Optional[str]) -> ProfileConfig:
    """Return a new config with ``default_runner`` set (or cleared with ``None``)."""

    canonical = None if runner is None else canonical_runner(runner)
    return _replace(cfg, default_runner=canonical)


def set_validate_default(cfg: ProfileConfig, value: Optional[bool]) -> ProfileConfig:
    """Return a new config whose ``defaults.validate`` is set, or UNSET with ``None``.

    ``None`` is not ``False``: it restores "unspecified", so the shipped default applies.
    """

    return _replace(cfg, validate=_validate_tristate("defaults.validate", value))


# ==================================================================================================
# Resolution (E-03)
# ==================================================================================================


def resolve(
    cfg: ProfileConfig,
    *,
    runner: Optional[str] = None,
    profile: Optional[str] = None,
    model: Optional[str] = None,
    variant: Optional[str] = None,
    agent: Optional[str] = None,
    validate: Optional[bool] = None,
    generic: bool = False,
) -> ResolvedLaunch:
    """Resolve ONE auditable launch, with per-field provenance.

    Precedence for ``runner``/``model``/``variant``/``agent``, highest first::

        explicit caller field > named profile > per-runner default profile > host default

    Precedence for ``validate``, highest first, with an ABSENT level falling THROUGH::

        explicit flag > profile's `validate` > `defaults.validate` > shipped default

    ``generic=True`` is host-neutral dispatch (`aw run ...`): when no named profile supplies a
    runner, ``default_runner`` is REQUIRED. It never guesses a runner, because guessing would
    route a run to a host the user did not choose.
    """

    provenance: Dict[str, str] = {}

    # ---- runner -----------------------------------------------------------------------------
    requested_profile = None
    if profile is not None:
        requested_profile = validate_profile_name(profile)
    named = cfg.get(requested_profile) if requested_profile is not None else None

    if runner is not None:
        resolved_runner = canonical_runner(runner)
        provenance["runner"] = PROVENANCE_EXPLICIT
        if named is not None and named.runner != resolved_runner:
            raise ProfileResolutionError(
                f"profile {requested_profile!r} runs on {named.runner!r}, but "
                f"{resolved_runner!r} was requested"
            )
    elif named is not None:
        resolved_runner = named.runner
        provenance["runner"] = PROVENANCE_PROFILE
    elif generic:
        if cfg.default_runner is None:
            raise ProfileResolutionError(
                "no runner was named and no 'default_runner' is configured. Set one (CLI: "
                "'aw oc profile default ...' / default_runner) or name a profile with "
                "'as <profile>'; aw does not guess which host to run."
            )
        resolved_runner = cfg.default_runner
        provenance["runner"] = PROVENANCE_DEFAULT_RUNNER
    else:
        raise ProfileResolutionError(
            "resolve() needs a runner: pass runner=<host> for a host command, or generic=True "
            "for host-neutral dispatch"
        )

    # ---- which profile actually applies -----------------------------------------------------
    applied_profile = requested_profile
    applied = named
    applied_provenance = PROVENANCE_PROFILE
    if applied is None:
        default_name = cfg.default_profile_for(resolved_runner)
        if default_name is not None:
            # `_validate_referential_integrity` already proved this resolves; `get` re-proves it
            # here so a hand-built ProfileConfig cannot slip a dangling default past resolution.
            applied = cfg.get(default_name)
            applied_profile = default_name
            applied_provenance = PROVENANCE_DEFAULT_PROFILE

    # ---- per-field launch values ------------------------------------------------------------
    def pick(
        explicit: Optional[str], from_profile: Optional[str], key: str
    ) -> Optional[str]:
        if explicit is not None:
            provenance[key] = PROVENANCE_EXPLICIT
            return explicit
        if from_profile is not None:
            provenance[key] = applied_provenance
            return from_profile
        provenance[key] = PROVENANCE_HOST_DEFAULT
        return None

    resolved_model = pick(
        validate_model(model) if model is not None else None,
        applied.model if applied is not None else None,
        "model",
    )
    resolved_variant = pick(
        _validate_field("variant", variant) if variant is not None else None,
        applied.variant if applied is not None else None,
        "variant",
    )
    resolved_agent = pick(
        _validate_field("agent", agent) if agent is not None else None,
        applied.agent if applied is not None else None,
        "agent",
    )

    # ---- validate: the tri-state chain, explicit flag FIRST ---------------------------------
    explicit_validate = _validate_tristate("validate", validate)
    if explicit_validate is not None:
        resolved_validate = explicit_validate
        provenance["validate"] = PROVENANCE_EXPLICIT
    elif applied is not None and applied.validate is not None:
        resolved_validate = applied.validate
        provenance["validate"] = applied_provenance
    elif cfg.validate is not None:
        resolved_validate = cfg.validate
        provenance["validate"] = PROVENANCE_DEFAULTS
    else:
        resolved_validate = SHIPPED_VALIDATE_DEFAULT
        provenance["validate"] = PROVENANCE_SHIPPED

    return ResolvedLaunch(
        runner=resolved_runner,
        model=resolved_model,
        variant=resolved_variant,
        agent=resolved_agent,
        validate=resolved_validate,
        requested_profile=requested_profile,
        applied_profile=applied_profile,
        config_source=str(cfg.source) if cfg.source is not None else None,
        config_present=cfg.present,
        config_digest=cfg.digest,
        provenance=MappingProxyType(dict(provenance)),
    )

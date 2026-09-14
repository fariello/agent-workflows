"""Analytics setup choices, retention, and precise deletion (runanalytics Order 09, ixis0c: E-09).

THE OBVIOUS CONFIG LOCATION SILENTLY DISCARDS THE SETTING, WHICH IS WHY THIS MODULE DOES NOT USE IT.
Measured 2026-09-14: ``config.normalize()`` rebuilds its output from ``default_config()`` against
``_ALLOWED_TOP_KEYS`` of exactly ``{aw_home, config_version, defaults, repos}``, and a round trip of
an ``analytics_endpoint`` key returned ``False`` for that key's survival. So writing endpoint
settings to the XDG user config would produce a setting that vanishes on save, and the user would
reconfigure it repeatedly with no error to explain why.

The settings therefore live in the GITIGNORED ``.aw/config/local.json``, which
``project_schema.parse_local_binding`` round-trips through its ``unknown_fields`` bag. Order 03
already established exactly this precedent for telemetry (``run_analytics_config.TELEMETRY_KEY``,
"deliberately NOT registered in ``config.py``'s ``CONFIG_SCHEMA``, exactly as
``review_findings_gate`` is"), so this module follows a decided pattern rather than inventing one.

WHY ``local.json`` AND NOT ``project.json``, since Order 02 rejected ``local.json`` for its salt:
Order 02's objection was that ``local.json`` is "a user-facing configuration surface whose keys the
setup wizard manages", which disqualifies it for a cryptographic secret. That same property ARGUES
FOR it here. An endpoint and an auth-source are precisely user-facing settings a human should be
able to see and edit, and they are MACHINE-LOCAL: committing them to ``project.json`` would push one
operator's destination onto every clone of the repository.

THE CREDENTIAL ITSELF IS NEVER STORED. What is stored is the NAME of an environment variable to read
it from, following ``oc_models.http_fetch_json``, whose bearer token "is never echoed anywhere".

THERE IS NO OPTIONAL-INSTALL MECHANISM, AND THE WIZARD DOES NOT PRETEND OTHERWISE. Measured: every
analytics module in this Set ships inside ``agent_workflows/``, the only declared extra is ``test``,
and no optional-feature install path exists. So what the wizard gates is whether analytics is
ENABLED and whether sampling RUNS, never whether code is present.

DEFAULTS ARE CONSERVATIVE AND SHARING IS OFF. Analytics off, submission off, cross-box correlation
off (Order 02 deferred that scope to this plan's explicit opt-in and it defaults OFF here), and an
unattended run that is missing a choice FAILS CLOSED rather than inferring one, following
``install_wizard``'s stated invariant that "noninteractive first install with incomplete choices or
``--yes`` alone FAILS CLOSED before writes".
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

__all__ = [
    "WizardRefusal",
    "ANALYTICS_KEY",
    "LOCAL_BINDING_REL",
    "DEFAULTS",
    "AnalyticsSettings",
    "read_settings",
    "write_settings",
    "apply_choices",
    "plan_deletion",
    "delete_analytics_artifacts",
]


class WizardRefusal(ValueError):
    """A configuration or deletion request was REFUSED rather than silently reinterpreted."""


#: The single key in ``local.json``. Deliberately NOT registered in ``config.py``'s schema, matching
#: Order 03's ``TELEMETRY_KEY`` and the documented ``review_findings_gate`` precedent.
ANALYTICS_KEY = "run_analytics_sharing"

#: The gitignored machine binding. Same tuple shape Order 03 uses.
LOCAL_BINDING_REL = ("config", "local.json")

#: Conservative by construction: nothing here shares data, and nothing turns itself on.
DEFAULTS: dict[str, Any] = {
    "analytics_enabled": False,
    "sampling_enabled": False,
    "submission_enabled": False,
    "cross_box_correlation_enabled": False,
    "endpoint_url": "",
    "auth_env_var": "",
    "retention_days": 0,
}

#: The choices an unattended run must supply explicitly. Absent -> refuse, never infer.
REQUIRED_UNATTENDED_CHOICES: tuple[str, ...] = (
    "analytics_enabled",
    "sampling_enabled",
    "submission_enabled",
)


@dataclass(frozen=True)
class AnalyticsSettings:
    """The effective sharing configuration. Every default is off."""

    analytics_enabled: bool = False
    sampling_enabled: bool = False
    submission_enabled: bool = False
    cross_box_correlation_enabled: bool = False
    endpoint_url: str = ""
    auth_env_var: str = ""
    retention_days: int = 0
    sources: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "analytics_enabled": self.analytics_enabled,
            "sampling_enabled": self.sampling_enabled,
            "submission_enabled": self.submission_enabled,
            "cross_box_correlation_enabled": self.cross_box_correlation_enabled,
            "endpoint_url": self.endpoint_url,
            "auth_env_var": self.auth_env_var,
            "retention_days": self.retention_days,
        }

    def endpoint(self) -> dict[str, Any]:
        """The endpoint mapping :func:`run_analytics_submit.submit_bundle` consumes.

        Returns an EMPTY url unless submission was explicitly enabled AND a url configured, so the
        submit path's ``unavailable`` result is the default outcome rather than something a
        half-finished configuration can accidentally escape.
        """

        if not self.submission_enabled:
            return {"url": "", "auth_env_var": self.auth_env_var}
        return {"url": self.endpoint_url, "auth_env_var": self.auth_env_var}


def _local_path(repo_root: Path | str) -> Path:
    return Path(repo_root).joinpath(".aw", *LOCAL_BINDING_REL)


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
    return default


def read_settings(repo_root: Path | str) -> AnalyticsSettings:
    """Read the machine-local sharing settings. Never raises; absent file -> all defaults off."""

    path = _local_path(repo_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return AnalyticsSettings()
    if not isinstance(payload, Mapping):
        return AnalyticsSettings()
    section = payload.get(ANALYTICS_KEY)
    if not isinstance(section, Mapping):
        return AnalyticsSettings()

    retention = section.get("retention_days", DEFAULTS["retention_days"])
    if isinstance(retention, bool) or not isinstance(retention, int) or retention < 0:
        retention = int(DEFAULTS["retention_days"])

    return AnalyticsSettings(
        analytics_enabled=_coerce_bool(
            section.get("analytics_enabled"), bool(DEFAULTS["analytics_enabled"])
        ),
        sampling_enabled=_coerce_bool(
            section.get("sampling_enabled"), bool(DEFAULTS["sampling_enabled"])
        ),
        submission_enabled=_coerce_bool(
            section.get("submission_enabled"), bool(DEFAULTS["submission_enabled"])
        ),
        cross_box_correlation_enabled=_coerce_bool(
            section.get("cross_box_correlation_enabled"),
            bool(DEFAULTS["cross_box_correlation_enabled"]),
        ),
        endpoint_url=str(section.get("endpoint_url") or ""),
        auth_env_var=str(section.get("auth_env_var") or ""),
        retention_days=int(retention),
        sources=("local",),
    )


def write_settings(repo_root: Path | str, settings: AnalyticsSettings) -> Path:
    """Persist settings into ``local.json``, PRESERVING every other key in the file.

    Read-modify-write rather than overwrite, because ``local.json`` is a shared surface carrying the
    project binding and Order 03's telemetry section. Clobbering it to save one section would
    destroy a co-resident setting, which is the failure the XDG config's own key-dropping behavior
    already demonstrates the cost of.
    """

    if _looks_like_secret(settings.auth_env_var):
        raise WizardRefusal(
            "auth_env_var must be an environment variable NAME, not a credential value; "
            "the secret is read from the environment at submission time and never stored"
        )

    path = _local_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, Mapping):
            existing = {str(k): v for k, v in loaded.items()}
    except (OSError, ValueError):
        existing = {}
    existing[ANALYTICS_KEY] = settings.to_dict()
    path.write_text(
        json.dumps(existing, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def _looks_like_secret(value: str) -> bool:
    """A conservative shape check: an env var NAME is short, upper-ish, and has no separators."""

    if not value:
        return False
    if any(ch in value for ch in " \t:/\\=\"'"):
        return True
    return len(value) > 96


def apply_choices(
    repo_root: Path | str,
    choices: Mapping[str, Any],
    *,
    unattended: bool = False,
    yes: bool = False,
) -> AnalyticsSettings:
    """Validate and persist wizard choices. Unattended with incomplete choices FAILS CLOSED.

    ``yes`` is accepted only to prove it is not sufficient. It is a preauthorization for expected
    mutations, not an answer to a privacy question, so an unattended run that passes ``--yes`` and
    omits a choice still refuses.
    """

    if unattended:
        missing = [name for name in REQUIRED_UNATTENDED_CHOICES if name not in choices]
        if missing:
            raise WizardRefusal(
                "unattended setup refuses to infer a privacy choice; missing: "
                + ", ".join(missing)
                + (
                    " (--yes does not answer these: it preauthorizes expected mutations, "
                    "not a data-sharing decision)"
                    if yes
                    else ""
                )
            )

    submission = _coerce_bool(
        choices.get("submission_enabled"), bool(DEFAULTS["submission_enabled"])
    )
    url = str(choices.get("endpoint_url") or "")
    if unattended and submission:
        raise WizardRefusal(
            "unattended setup refuses to enable submission; an unattended host is local and "
            "no-submit by default, and enabling transmission is an interactive decision"
        )
    if submission and not url:
        raise WizardRefusal(
            "submission_enabled requires an endpoint_url; enabling transmission with no "
            "destination would be a setting that silently does nothing"
        )

    retention = choices.get("retention_days", DEFAULTS["retention_days"])
    if isinstance(retention, bool) or not isinstance(retention, int) or retention < 0:
        raise WizardRefusal("retention_days must be a non-negative integer")

    settings = AnalyticsSettings(
        analytics_enabled=_coerce_bool(
            choices.get("analytics_enabled"), bool(DEFAULTS["analytics_enabled"])
        ),
        sampling_enabled=_coerce_bool(
            choices.get("sampling_enabled"), bool(DEFAULTS["sampling_enabled"])
        ),
        submission_enabled=submission,
        # Order 02 deferred cross-box correlation to this plan's explicit opt-in. It defaults OFF
        # and only an explicit True turns it on.
        cross_box_correlation_enabled=_coerce_bool(
            choices.get("cross_box_correlation_enabled"),
            bool(DEFAULTS["cross_box_correlation_enabled"]),
        ),
        endpoint_url=url,
        auth_env_var=str(choices.get("auth_env_var") or ""),
        retention_days=int(retention),
        sources=("local",),
    )
    write_settings(repo_root, settings)
    return settings


# --- Retention and precise deletion -------------------------------------------------------------


def plan_deletion(
    repo_root: Path | str, *, targets: Sequence[Path | str] | None = None
) -> dict[str, Any]:
    """Decide what deletion WOULD remove, resolving containment through Order 01's predicate.

    Every candidate must satisfy ``runner_shared.path_is_within_analytics``, and the literal
    ``.aw/records/runs`` is never composed here: Order 01 owns the resolver and the reserved
    namespace, and a second copy of that path logic is a second thing to get wrong when a runs root
    is relocated or a legacy root is in play.
    """

    from agent_workflows.runner_shared import (
        analytics_root,
        path_is_within_analytics,
    )

    root = analytics_root(repo_root)
    candidates: list[Path]
    if targets is None:
        candidates = (
            sorted(p for p in root.rglob("*") if p.is_file()) if root.is_dir() else []
        )
    else:
        candidates = [Path(t) for t in targets]

    removable: list[str] = []
    refused: list[dict[str, str]] = []
    for candidate in candidates:
        if not path_is_within_analytics(candidate, repo_root):
            refused.append(
                {
                    "path": str(candidate),
                    "reason": (
                        "outside the reserved analytics namespace; a source run is never "
                        "deleted by an analytics command"
                    ),
                }
            )
            continue
        removable.append(str(candidate))

    return {
        "analytics_root": str(root),
        "removable": removable,
        "removable_count": len(removable),
        "refused": refused,
        "refused_count": len(refused),
        "source_runs_touched": False,
    }


def delete_analytics_artifacts(
    repo_root: Path | str,
    *,
    targets: Sequence[Path | str] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Delete ONLY tool-owned analytics children. Dry run by default.

    Dry run is the default because the argument "the analytics tree is disposable" is true of the
    tree and false of a mistake in the path resolution that reaches outside it. A refused candidate
    aborts the whole deletion rather than being skipped, so a caller cannot half-delete against a
    plan they did not review.
    """

    plan = plan_deletion(repo_root, targets=targets)
    if plan["refused"]:
        raise WizardRefusal(
            "refusing the whole deletion because a candidate lies outside the reserved "
            "analytics namespace: "
            + "; ".join(f"{r['path']} ({r['reason']})" for r in plan["refused"])
        )
    if dry_run:
        return {**plan, "deleted": [], "dry_run": True}

    deleted: list[str] = []
    for path_str in plan["removable"]:
        target = Path(path_str)
        try:
            if target.is_file():
                target.unlink()
                deleted.append(path_str)
        except OSError:
            continue
    return {**plan, "deleted": deleted, "dry_run": False}

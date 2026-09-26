"""Antigravity (AGY) model and settings discovery.

Resolves AGY's configured model from ~/.gemini/antigravity-cli/settings.json
(or AGY_SETTINGS / ANTIGRAVITY_SETTINGS / AGY_CONFIG env vars), or reports
host default when no model is declared in configuration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping, Tuple


def resolve_config_path(
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path | None:
    """Resolve the Antigravity settings.json path, or None if not found.

    Precedence:
    1. AGY_SETTINGS / ANTIGRAVITY_SETTINGS / AGY_CONFIG environment variable
    2. ~/.gemini/antigravity-cli/settings.json
    """
    environ = os.environ if env is None else env
    for var in ("AGY_SETTINGS", "ANTIGRAVITY_SETTINGS", "AGY_CONFIG"):
        val = environ.get(var)
        if val:
            p = Path(val).expanduser()
            if p.is_file():
                return p

    home_dir = home if home is not None else Path(environ.get("HOME", str(Path.home())))
    default_path = home_dir / ".gemini" / "antigravity-cli" / "settings.json"
    if default_path.is_file():
        return default_path

    return None


def resolve_agy_default_model(
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Tuple[str | None, str]:
    """Resolve AGY's default model and its source from settings.json.

    Returns:
        (model_id, source):
        - If a model is declared in settings.json: (model_name, "settings.json")
        - If settings.json is not found or has no model: (None, "host-default")
    """
    path = resolve_config_path(env=env, home=home)
    if path is None:
        return None, "host-default"

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, "host-default"

    if isinstance(data, dict):
        model = data.get("model")
        if isinstance(model, str) and model.strip():
            return model.strip(), "settings.json"

    return None, "host-default"


def resolve_agy_config_model(
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> str | None:
    """Return the model declared in settings.json, or None."""
    model, _ = resolve_agy_default_model(env=env, home=home)
    return model

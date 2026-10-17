#!/usr/bin/env python3
"""Human display names for model ids: ``uri/its_direct/pt3-claude-opus-5.5-1m-us`` + ``high`` ->
``Claude Opus 5.5 High``.

RULES FIRST, OVERRIDES SECOND, RAW ID ALWAYS KEPT. :func:`display_name` cleans an id by rule, so a
new model needs no code change. Anything the rules get wrong is fixed in the COMMITTED project
policy, ``.aw/config/project.json``::

    "model_display_names": {
        "uri/its_direct/pt3-claude-opus-5.5-1m-us": "Claude Opus 5.5"
    }

An override names the MODEL only; the variant is still appended (``Claude Opus 5.5 High``). The raw
id is never replaced in stored data: callers keep it beside the display name so filters and
provenance still see exactly what the host recorded.

WHAT THE RULES DO, in order:

1. Drop path-style provider and routing prefixes: everything up to the last ``/``
   (``uri/its_direct/``, ``google/``, ``anthropic/``).
2. Drop known deployment prefixes and suffixes that are not part of the model's name: a leading
   ``pt<N>-`` (provisioned-throughput tag), a context-window marker (``-1m``, ``-200k``), a region
   (``-us``, ``-eu``, ``-global``) and a date stamp (``-20250929``). The context window is dropped on
   purpose (maintainer ruling 2026-10-17).
3. Pull a trailing effort word out as the variant (``gemini-3.7-flash-high``, ``Gemini 3.8 Flash
   (High)``) when no variant was recorded separately.
4. Title-case the family words and keep version numbers as written (``opus-5.5`` -> ``Opus 5.5``,
   ``gpt-5`` -> ``GPT 5``); a hyphenated version joins with a dot (``sonnet-4-5`` -> ``Sonnet 4.5``).

A VARIANT IS SHOWN ONLY WHEN IT WAS RECORDED (or is part of the id itself). ``default`` and empty
are treated as no variant, because the host did not say which effort it used.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

__all__ = [
    "display_name",
    "clean_model_id",
    "split_effort",
    "load_overrides",
    "EFFORT_WORDS",
]

#: Effort/variant words a host may append to a model id or pass as a variant.
EFFORT_WORDS: tuple[str, ...] = ("minimal", "low", "medium", "high", "xhigh", "max")

#: Words kept in a fixed case rather than title-cased.
_FIXED_CASE = {
    "gpt": "GPT",
    "glm": "GLM",
    "llama": "Llama",
    "o1": "o1",
    "o3": "o3",
    "o4": "o4",
    "qwen": "Qwen",
    "xai": "xAI",
}

_PT_PREFIX = re.compile(r"^pt\d+-")
_DATE = re.compile(r"-(?:20\d{6}|\d{4}-\d{2}-\d{2})$")
_CONTEXT = re.compile(r"-\d+(?:\.\d+)?[km]$", re.IGNORECASE)
_REGION = re.compile(r"-(?:us|eu|apac|asia|global|uk|jp)$", re.IGNORECASE)
_PAREN_EFFORT = re.compile(
    r"\s*\((" + "|".join(EFFORT_WORDS) + r")\)\s*$", re.IGNORECASE
)
_DASH_EFFORT = re.compile(r"[-\s](" + "|".join(EFFORT_WORDS) + r")$", re.IGNORECASE)


def split_effort(model: str) -> tuple[str, str]:
    """``(model_without_effort, effort)`` when the id ends in an effort word, else ``(model, "")``."""

    text = model.strip()
    m = _PAREN_EFFORT.search(text) or _DASH_EFFORT.search(text)
    if m:
        return text[: m.start()].strip(), m.group(1).lower()
    return text, ""


def clean_model_id(model: str) -> str:
    """The rule-based display form of a model id, WITHOUT any variant."""

    text = (model or "").strip()
    if not text:
        return ""
    text = text.rsplit("/", 1)[-1]
    text, _effort = split_effort(text)
    if " " in text:
        # Already a human name ("Gemini 3.8 Flash"); only the effort suffix needed removing.
        return text
    text = _PT_PREFIX.sub("", text)
    # Strip deployment suffixes from the right until none applies (order varies by provider).
    changed = True
    while changed:
        changed = False
        for rx in (_DATE, _REGION, _CONTEXT):
            new = rx.sub("", text)
            if new != text:
                text, changed = new, True
    words = [w for w in re.split(r"[-_\s]+", text) if w]
    # `claude-sonnet-4-5` writes version 4.5 with a hyphen: join a run of 1-2 digit number words.
    joined: list[str] = []
    for w in words:
        if (
            joined
            and re.fullmatch(r"\d{1,2}", w)
            and re.fullmatch(r"\d{1,2}(?:\.\d{1,2})*", joined[-1])
        ):
            joined[-1] = joined[-1] + "." + w
        else:
            joined.append(w)
    words = joined
    out = []
    for w in words:
        low = w.lower()
        if low in _FIXED_CASE:
            out.append(_FIXED_CASE[low])
        elif re.match(r"^\d", w):
            out.append(w)
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


def _norm_variant(variant: Any) -> str:
    v = str(variant or "").strip().lower()
    return "" if v in ("", "default", "none", "null") else v


def display_name(
    model: str | None,
    variant: str | None = None,
    *,
    overrides: Mapping[str, str] | None = None,
) -> str:
    """The display name for ``model`` run at ``variant``. Empty in, empty out.

    The variant comes from ``variant`` when recorded, else from an effort word in the id itself.
    ``overrides`` maps a RAW id (exact, or with its provider prefix removed) to a model name.
    """

    raw = (model or "").strip()
    if not raw:
        return ""
    base_no_effort, id_effort = split_effort(raw.rsplit("/", 1)[-1])
    ov = overrides or {}
    name = (
        ov.get(raw)
        or ov.get(raw.rsplit("/", 1)[-1])
        or ov.get(base_no_effort)
        or clean_model_id(raw)
    )
    effort = _norm_variant(variant) or id_effort
    if effort and not name.lower().endswith(effort):
        name = f"{name} {effort.capitalize() if effort != 'xhigh' else 'XHigh'}"
    return name


@lru_cache(maxsize=16)
def _load_overrides_cached(path: str, mtime_ns: int) -> dict[str, str]:
    del mtime_ns
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    section = payload.get("model_display_names") if isinstance(payload, dict) else None
    if not isinstance(section, dict):
        return {}
    return {
        str(k): str(v) for k, v in section.items() if isinstance(v, str) and v.strip()
    }


def load_overrides(repo: Path | str | None) -> dict[str, str]:
    """``model_display_names`` from the repository's ``.aw/config/project.json``, or ``{}``."""

    if repo is None:
        return {}
    try:
        from agent_workflows.project_context import project_config_dir

        path = project_config_dir(repo) / "project.json"
        return dict(_load_overrides_cached(str(path), path.stat().st_mtime_ns))
    except Exception:
        return {}

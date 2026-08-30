"""Closed TYPE-noun vocabulary + verb->backend routing for the noun-verb command surface
(spec 20260818-1525-01, awcmdsurf Set). This module imports NONE of the backend modules at load
time: TYPE_BACKENDS stores DOTTED-NAME STRINGS resolved lazily at dispatch, so it never reintroduces
the import cycles the map exists to avoid."""

from __future__ import annotations

import importlib
from typing import Callable, Dict, List, Optional, Sequence

# The closed set of artifact TYPE nouns (canonical plural forms).
ARTIFACT_TYPES = (
    "plans",
    "specs",
    "prompts",
    "research",
    "backlog",
    "walkthroughs",
    "roadmaps",
    "comms",
    "releases",
    "other",
)

# Singular / short aliases -> canonical plural.
_ALIASES = {
    "plan": "plans",
    "spec": "specs",
    "prompt": "prompts",
    "walkthrough": "walkthroughs",
    "roadmap": "roadmaps",
    "comm": "comms",
    "research": "research",
    "backlog": "backlog",
    "release": "releases",
    "other": "other",
    "others": "other",
    "misc": "other",
}


def is_type_token(token: Optional[str]) -> bool:
    """Return True if `token` is a known artifact type (plural), alias (singular), or 'all'."""
    if not token:
        return False
    return token == "all" or token in ARTIFACT_TYPES or token in _ALIASES


def normalize_type(token: str) -> str:
    """Return the canonical plural type for `token` (a plural, a known singular alias, or `all`).
    Raises ValueError listing the valid set for an unknown token."""
    if token == "all":
        return "all"
    if token in ARTIFACT_TYPES:
        return token
    if token in _ALIASES:
        return _ALIASES[token]
    valid = ", ".join(ARTIFACT_TYPES) + ", all"
    raise ValueError(f"unknown artifact type {token!r}; valid types: {valid}")


def expand_types(token: str, supported: Sequence[str]) -> List[str]:
    """Expand `token` to the concrete list a verb acts on. `all` -> every `supported` type (in
    ARTIFACT_TYPES order); a single type -> [that type] (must be in `supported`)."""
    norm = normalize_type(token)
    supported = tuple(supported)
    if norm == "all":
        return [t for t in ARTIFACT_TYPES if t in supported]
    if norm not in supported:
        raise ValueError(
            f"type {norm!r} is not supported here; supported: {', '.join(supported)}"
        )
    return [norm]


# type -> {verb -> "module.attr"} (dotted-name STRING, resolved lazily). A missing (type, verb)
# resolves to None -> the router reports "not supported for <type>" (exit 2).
TYPE_BACKENDS: Dict[str, Dict[str, str]] = {
    "plans": {
        "index": "plans_index.run_index",
        "find": "plans_index.run_find",
        "rename": "plans_refs.run_mv",
        "group": "plans_refs.run_set_assign",
        "archive": "plans_archive.run_archive",
    },
    "research": {
        "index": "research_index.run_index",
        "find": "research_index.run_find",
        "rename": "research_refs.run_mv",
        "group": "research_refs.run_set_assign",
        "archive": "research_archive.run_archive",
    },
    "specs": {
        "check": "specs.run_check",
        "rename": "artifact_rename.run_rename_specs",
        "group": "artifact_rename.run_group_specs",
    },
    "prompts": {
        "new": "prompts.run_new",
        "rename": "artifact_rename.run_rename_prompts",
        "group": "artifact_rename.run_group_prompts",
    },
    "backlog": {
        "check": "backlog.run_check",
        "rename": "artifact_rename.run_rename_backlog",
        "group": "artifact_rename.run_group_backlog",
    },
    "walkthroughs": {
        "rename": "artifact_rename.run_rename_walkthroughs",
        "group": "artifact_rename.run_group_walkthroughs",
    },
    "roadmaps": {
        "rename": "artifact_rename.run_rename_roadmaps",
        "group": "artifact_rename.run_group_roadmaps",
    },
    "releases": {
        "rename": "artifact_rename.run_rename_releases",
        "group": "artifact_rename.run_group_releases",
    },
    "other": {
        "rename": "artifact_rename.run_rename_other",
        "group": "artifact_rename.run_group_other",
    },
}


def backend_name(artifact_type: str, verb: str) -> Optional[str]:
    """The dotted-name string for (type, verb), or None if unsupported."""
    return TYPE_BACKENDS.get(artifact_type, {}).get(verb)


def resolve_backend(artifact_type: str, verb: str) -> Optional[Callable]:
    """Lazily resolve (type, verb) to a callable, or None if unsupported. Imports the backend module
    only at dispatch time."""
    dotted = backend_name(artifact_type, verb)
    if dotted is None:
        return None
    mod, attr = dotted.rsplit(".", 1)
    module = importlib.import_module("agent_workflows." + mod)
    return getattr(module, attr)


# ---- shared exit-code convention (spec: 0 ok / 1 findings / 2 cannot-run) ----

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_CANNOT_RUN = 2


def exit_code_for(drift) -> int:
    """0 when no drift/findings, 1 when findings present. (2 = cannot-run is the caller's to return
    on a parse/invocation failure.) Reuses the artifact_core Drift convention."""
    from agent_workflows import artifact_core as _core

    return _core.drift_exit_code(drift)


def emit_findings(term, drift, *, as_json: bool = False, as_agent: bool = False) -> int:
    """Emit a verb's findings uniformly and return the exit code. `--agent` = tab-separated Drift;
    `--json` = a JSON list; otherwise a human line per finding via `term`."""
    from agent_workflows import artifact_core as _core

    if as_agent:
        import sys

        sys.stdout.write(_core.render_agent_drift(drift))
    elif as_json:
        import json
        import sys

        sys.stdout.write(
            json.dumps(
                [
                    {"location": d.location, "rule": d.rule, "detail": d.detail}
                    for d in drift
                ]
            )
            + "\n"
        )
    else:
        # awcolor Order 01: color the severity/rule in the human branch (agent/json unchanged).
        for d in drift:
            rule = (
                term.color256(d.rule, 196, bold=True)
                if getattr(term, "color", False)
                else d.rule
            )
            term.line(f"- {d.location}: {rule} {d.detail}")
        if not drift:
            pass
    return exit_code_for(drift)

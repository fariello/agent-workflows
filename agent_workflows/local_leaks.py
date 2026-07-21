#!/usr/bin/env python3
"""Compatibility shim: the local-leaks detection engine now lives in ``leak_sanitizer``.

DECISIONS D92 introduced a one-off leak guard; D93 promoted it to this module. As of the
``leak-sanitizer`` Set (IPD 20260721-1353-01) the detection engine, its config, and its scan
modes were unified into ``agent_workflows/leak_sanitizer.py`` (which also adds ``--fix``,
``--agent``, an off-by-default IP ruleset, and a staged-blob scan mode). This module is kept as
a thin, stable re-export so existing importers (``from agent_workflows import local_leaks``),
the ``aw check-local-leaks`` CLI, the pre-commit hook, the ``tests/test_local_leaks.py``
regression guard, and the ``/assess local-leaks`` lens all keep working with ONE code path and
no double-reporting (P8, single source of truth).

Sensitive literals are assembled from fragments in the engine module, never here.
Stdlib only (zero runtime deps).

Exit code (CLI): 0 = clean, 1 = fail-severity leak(s), 2 = usage/environment error.
"""

from __future__ import annotations

# Re-export the unified engine's public surface so this module's historical API is preserved.
from .leak_sanitizer import (  # noqa: F401
    REPO_ALLOWLIST_REL,
    USER_HINTS_FILENAME,
    Finding,
    Ruleset,
    _ACCT,
    _EMAIL,
    _H,
    _PACKAGE_NAME,
    _REMOTE,
    _VC,
    build_ruleset,
    derive_warn_tokens,
    load_repo_allowlist,
    load_user_hints,
    main,
    run,
    scan_history,
    scan_text,
    scan_wheel,
    scan_working_tree,
)

__all__ = [
    "REPO_ALLOWLIST_REL",
    "USER_HINTS_FILENAME",
    "Finding",
    "Ruleset",
    "build_ruleset",
    "derive_warn_tokens",
    "load_repo_allowlist",
    "load_user_hints",
    "main",
    "run",
    "scan_history",
    "scan_text",
    "scan_wheel",
    "scan_working_tree",
]


if __name__ == "__main__":
    raise SystemExit(main())

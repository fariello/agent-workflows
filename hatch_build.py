"""Build-time version computation for the wheel (hatchling `code` version source).

The WHEEL version must equal what `agent_workflows.versioning.resolve_version` computes
and what `make version-file` bakes into `.agents/workflows/VERSION` (DECISIONS D44/D46).
We deliberately do NOT use `hatch-vcs`/`setuptools-scm`: that would add a build dependency
and duplicate our resolver, risking drift. There is ONE source of versioning truth - our
own module.

hatchling's built-in `code` version source (pyproject: `[tool.hatch.version] source =
"code"`, `path = "hatch_build.py"`, `expression = "VERSION"`, `search-paths = ["."]`)
imports this file with the repo root on sys.path, then reads the `VERSION` name below.

The resolver reads `git describe` from the repo root at build time; building from an
exported sdist with no git falls back to the baked `.agents/workflows/VERSION` file
(resolve_version's own fallback), so sdist-based builds still get a version.
"""

from __future__ import annotations

from pathlib import Path

# search-paths=["."] puts the project root on sys.path, so this import resolves to the
# package being built.
from agent_workflows.versioning import resolve_version

_ROOT = Path(__file__).resolve().parent
VERSION = resolve_version(_ROOT, version_file=_ROOT / ".agents" / "workflows" / "VERSION")

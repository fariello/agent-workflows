"""Build-time version + metadata hooks for the wheel/sdist (DECISIONS D44/D46/D-PyPI).

This one file hosts ALL THREE hatchling plugins the project uses, which can coexist here:

1. Version `code` source: `[tool.hatch.version] source = "code", path = "hatch_build.py",
   expression = "VERSION"` imports this file (repo root on sys.path) and reads `VERSION`.
   The WHEEL version must equal `agent_workflows.versioning.resolve_version` and what
   the custom build hook bakes into `.aw/system/VERSION` (replacing the manual reliance on
   `make version-file`). We deliberately do NOT use `hatch-vcs`/`setuptools-scm`
   (extra build dep + resolver duplication -> drift).

2. Custom metadata hook: `[tool.hatch.metadata.hooks.custom]` (default `path =
   hatch_build.py`) discovers `CustomMetadataHook` (a `MetadataHookInterface` subclass) and
   calls `update(metadata)` to set the `readme` long-description to a copy of `README.md`
   with relative links rewritten to absolute, tag-pinned GitHub URLs (so links work on
   PyPI). The source `README.md` is never modified. Stdlib only - NOT `hatch-fancy-pypi-readme`
   (a build dep, which would violate D46 zero-deps).

3. Custom build hook: `[tool.hatch.build.hooks.custom]` (path = "hatch_build.py") discovers
   `CustomBuildHook` (a `BuildHookInterface` subclass) and calls `initialize(version, build_data)`
   to bake `self.metadata.version` into `agent_workflows/_data/.aw/system/VERSION` at wheel
   build time without modifying the working tree.

The resolver reads `git describe` at build time; an exported sdist with no git falls back to
the baked `.aw/system/VERSION` (legacy `.agents/workflows/VERSION`), so sdist-based builds still get a version.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent

# The version `code` source runs with search-paths=["."] on sys.path, but the custom
# metadata hook is loaded via load_plugin_from_script WITHOUT the root on sys.path. Add it
# ourselves so `import agent_workflows...` resolves in BOTH contexts.
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent_workflows.pypi_links import (  # noqa: E402  (must follow the sys.path insert)
    owner_repo_from_url,
    rewrite_relative_links,
)
from agent_workflows.versioning import resolve_version  # noqa: E402

v_file = _ROOT / ".aw" / "system" / "VERSION"
if not v_file.exists():
    v_file = _ROOT / ".agents" / "workflows" / "VERSION"
VERSION = resolve_version(_ROOT, version_file=v_file)


def write_bundled_version(version: str, out_dir: Path | str) -> Path:
    """Write the given version string followed by a newline to a VERSION file in out_dir."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    target = out_path / "VERSION"
    target.write_text(f"{version.strip()}\n", encoding="utf-8")
    return target


try:
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface
    from hatchling.metadata.plugin.interface import MetadataHookInterface

    class CustomBuildHook(BuildHookInterface):
        """Bake the resolved metadata version into the bundled VERSION at wheel build time."""

        def initialize(self, version: str, build_data: dict) -> None:
            if self.target_name == "wheel":
                import tempfile

                temp_dir = tempfile.mkdtemp(prefix="aw-build-version-")
                baked_version_file = write_bundled_version(
                    self.metadata.version, temp_dir
                )
                build_data.setdefault("force_include", {})[str(baked_version_file)] = (
                    "agent_workflows/_data/.aw/system/VERSION"
                )

    class CustomMetadataHook(MetadataHookInterface):
        """Set the PyPI long-description to README.md with links absolutized (D-PyPI).

        Rewrites relative repo-internal links to `https://github.com/<owner>/<repo>/{blob,raw}/
        v<VERSION>/<path>` so they resolve on PyPI. Owner/repo come from `[project.urls]`
        (Repository/Homepage); if none is a GitHub URL, the README is used unchanged. The
        source file on disk is never modified - only the built metadata.
        """

        def update(self, metadata: dict) -> None:
            root = Path(self.root)
            readme = root / "README.md"
            try:
                text = readme.read_text(encoding="utf-8")
            except OSError:
                return  # no README to rewrite; leave metadata as-is

            urls = metadata.get("urls") or {}
            owner_repo = None
            for key in ("Repository", "Homepage", "Source", "Home"):
                if key in urls:
                    owner_repo = owner_repo_from_url(urls[key])
                    if owner_repo:
                        break
            if owner_repo:
                owner, repo = owner_repo
                text = rewrite_relative_links(text, owner, repo, ref=f"v{VERSION}")

            metadata["readme"] = {
                "content-type": "text/markdown",
                "text": text,
            }
except ImportError:
    # hatchling not importable (e.g. running this module outside a build); the version
    # source path does not need the hook. Safe to skip.
    pass

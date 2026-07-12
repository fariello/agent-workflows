"""Git-tag-driven version resolution for agent-workflows (stdlib only, zero deps).

The framework's runtime tools stay "dumb": once copied into a user's repo they are
loose files with no git and no package metadata, so they read their version from the
neighboring ``VERSION`` file (see each tool's ``_framework_version``). This module holds
the *intelligence*: it computes a PEP 440 version from ``git describe`` at build/release
time, so ``VERSION`` becomes a derived artifact rather than a hand-edited string.

Design (IPD-1, DECISIONS D44):

- ``resolve_version(repo_root)`` inspects the git work tree if one is available and this
  is a real git checkout of the project; otherwise it falls back to reading the baked
  ``VERSION`` file next to the framework. This keeps a plain ``git clone`` and the
  file-copy install both working with no build step.
- The comparator and ``status`` mapping operate over EXACTLY the version shape this
  module produces (``MAJOR.MINOR.PATCH[.devN][+local]``); we deliberately do NOT depend
  on the third-party ``packaging`` library, preserving the zero-runtime-dependency rule.
  The ``+local`` segment (gsha, optional ``.dDATE``) is compared as presence only.

The real ``git describe --tags --always --dirty --long`` forms this parses (verified
live against git):

- ``v1.0.0-0-gd644d2d``        exact tag, clean        -> ``1.0.0``
- ``v1.0.0-0-gd644d2d-dirty``  exact tag, dirty        -> ``1.0.1.dev0+gd644d2d.dYYYYMMDD``
- ``v1.0.0-2-g49f2bdc``        2 commits ahead, clean  -> ``1.0.1.dev2+g49f2bdc``
- ``v1.0.0-2-g49f2bdc-dirty``  2 ahead, dirty          -> ``1.0.1.dev2+g49f2bdc.dYYYYMMDD``
- ``d644d2d``                  no tags, clean          -> ``0.0.0+gd644d2d``
- ``9042038-dirty``            no tags, dirty          -> ``0.0.0+g9042038.dYYYYMMDD``
- (git missing / not a repo / describe fails)          -> read the ``VERSION`` file
"""

from __future__ import annotations

import datetime
import re
import subprocess
from pathlib import Path
from typing import NamedTuple, Optional

VERSION_FILENAME = "VERSION"

# Parses the --long describe form:  <tag>-<distance>-g<sha>[-dirty]
# e.g. v1.0.0-2-g49f2bdc-dirty  ->  tag=v1.0.0 distance=2 sha=49f2bdc dirty=True
_DESCRIBE_LONG_RE = re.compile(
    r"^(?P<tag>.+)-(?P<distance>\d+)-g(?P<sha>[0-9a-fA-F]+)(?P<dirty>-dirty)?$"
)


def _utc_date() -> str:
    """Return today's UTC date as ``YYYYMMDD`` (used only for the local dev segment)."""

    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")


def _normalize_tag(tag: str) -> str:
    """Strip a leading ``v`` from a tag so ``v1.0.0`` becomes ``1.0.0``."""

    return tag[1:] if tag.startswith("v") else tag


def _next_patch(release: str) -> str:
    """Return the release string with PATCH incremented by one.

    ``1.0.0`` -> ``1.0.1``. This is the version of the UPCOMING release, which is the
    correct base for a ``.devN`` pre-release segment. Tolerates non-3-part tags by
    bumping the last numeric component present.
    """

    parts = release.split(".")
    # Find the last purely-numeric part and bump it.
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].isdigit():
            parts[i] = str(int(parts[i]) + 1)
            return ".".join(parts)
    # No numeric component (degenerate tag); append .1 as a defensive bump.
    return release + ".1"


def parse_describe(describe: str, *, date: Optional[str] = None) -> str:
    """Map a ``git describe --tags --always --dirty --long`` string to a PEP 440 version.

    Args:
        describe: the raw describe output (already stripped of whitespace).
        date: override for the UTC ``YYYYMMDD`` dev-date (for deterministic tests);
            defaults to today's UTC date.

    Returns:
        A PEP 440-valid version string.
    """

    describe = describe.strip()
    date = date or _utc_date()

    match = _DESCRIBE_LONG_RE.match(describe)
    if match:
        tag = _normalize_tag(match.group("tag"))
        distance = int(match.group("distance"))
        sha = match.group("sha")
        dirty = match.group("dirty") is not None

        if distance == 0 and not dirty:
            # Exact tagged release, clean tree.
            return tag

        # Ahead of the tag, or dirty at the tag: a dev build of the NEXT release.
        base = _next_patch(tag)
        local = f"+g{sha}"
        if dirty:
            local += f".d{date}"
        return f"{base}.dev{distance}{local}"

    # No tags: git describe --always degrades to a bare short sha, plus a trailing
    # "-dirty" when the tree is dirty (e.g. "9042038-dirty"). Strip/detect it.
    dirty = describe.endswith("-dirty")
    sha = describe[: -len("-dirty")] if dirty else describe
    local = f"+g{sha}"
    if dirty:
        local += f".d{date}"
    return f"0.0.0{local}"


def _git_describe(repo_root: Path) -> Optional[str]:
    """Return ``git describe --tags --always --dirty --long`` output, or None.

    None means git is unavailable, this is not a git work tree, or the command failed;
    the caller falls back to the baked VERSION file.
    """

    try:
        proc = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty", "--long"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):
        # git binary missing, or subprocess could not start.
        return None
    if proc.returncode != 0:
        # Not a git repository, or describe otherwise failed.
        return None
    out = proc.stdout.strip()
    return out or None


def read_version_file(version_path: Path) -> str:
    """Read a trimmed VERSION file, returning ``"unknown"`` if absent/empty."""

    try:
        value = version_path.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    return value or "unknown"


def resolve_version(repo_root: Path, *, version_file: Optional[Path] = None) -> str:
    """Resolve the framework version for a checkout at ``repo_root``.

    Prefers git (tag-driven, dirty/distance-aware) when ``repo_root`` is a real git
    work tree; otherwise reads the baked ``VERSION`` file (the copied-out / wheel /
    plain-clone case).

    Args:
        repo_root: the directory to run ``git describe`` in.
        version_file: explicit path to the fallback VERSION file. When omitted, defaults
            to ``repo_root/.agents/workflows/VERSION``.

    Returns:
        A PEP 440 version string, or the file's contents, or ``"unknown"``.
    """

    describe = _git_describe(repo_root)
    if describe is not None:
        return parse_describe(describe)

    if version_file is None:
        version_file = repo_root / ".agents" / "workflows" / VERSION_FILENAME
    return read_version_file(version_file)


# --------------------------------------------------------------------------------------
# Comparator + status mapping (consumed by IPD-2's `status`; defined here so the format
# and its ordering live with the code that produces the format).
# --------------------------------------------------------------------------------------

# A legacy hand-maintained version string, e.g. "20260704-06" (pre-migration installs).
_LEGACY_RE = re.compile(r"^\d{8}-\d+$")

# Our own controlled shape: MAJOR.MINOR.PATCH[.devN][+local]
_OURS_RE = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:\.dev(?P<dev>\d+))?"
    r"(?P<local>\+.+)?$"
)


class Parsed(NamedTuple):
    """A parsed version in our controlled format."""

    release: tuple  # (major, minor, patch) ints
    dev: Optional[int]  # .devN integer, or None for a final release
    is_local: bool  # whether a +local segment is present


def parse_our_version(version: str) -> Optional[Parsed]:
    """Parse a version string of our own shape, or None if it is not ours/legacy.

    A legacy ``YYYYMMDD-NN`` or any unrecognized string returns None so callers can
    report ``unknown`` rather than guessing.
    """

    version = version.strip()
    match = _OURS_RE.match(version)
    if not match:
        return None
    release = (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )
    dev = match.group("dev")
    return Parsed(
        release=release,
        dev=int(dev) if dev is not None else None,
        is_local=match.group("local") is not None,
    )


def _sort_key(parsed: Parsed) -> tuple:
    """Ordering key: a ``.devN`` sorts BEFORE its final release (PEP 440 semantics).

    We encode "final release" as dev-rank 1 and a dev build as dev-rank 0 with its N,
    so ``1.0.1.dev2 < 1.0.1``. The ``+local`` segment is NOT part of ordering (presence
    only), matching the plan: two dev builds of the same base are equally "dev".
    """

    if parsed.dev is None:
        return (parsed.release, 1, 0)
    return (parsed.release, 0, parsed.dev)


def compare(a: str, b: str) -> int:
    """Compare two of-our-shape version strings. Returns -1, 0, or 1 (a vs b).

    Raises ValueError if either string is not in our format (caller should have routed
    legacy/unknown strings to ``status`` -> ``unknown`` first).
    """

    pa = parse_our_version(a)
    pb = parse_our_version(b)
    if pa is None or pb is None:
        raise ValueError("compare() requires versions in the controlled format")
    ka, kb = _sort_key(pa), _sort_key(pb)
    return (ka > kb) - (ka < kb)


def status(target: Optional[str], packaged: str) -> str:
    """Classify an installed ``target`` version against the ``packaged`` (shipping) one.

    Args:
        target: the version read from an installed repo's VERSION file, or None/"" if
            no VERSION file is present (not installed).
        packaged: the version this distribution ships with.

    Returns one of: ``not-installed``, ``unknown``, ``dev``, ``stale``, ``ahead``,
    ``current``.
    """

    if not target or target.strip() == "" or target.strip() == "unknown":
        return "not-installed"

    tparsed = parse_our_version(target)
    pparsed = parse_our_version(packaged)

    # A legacy YYYYMMDD-NN target, a 0.0.0 pre-baseline on either side, or anything we
    # cannot parse: report unknown rather than guessing.
    if tparsed is None or pparsed is None:
        return "unknown"
    if tparsed.release == (0, 0, 0) or pparsed.release == (0, 0, 0):
        return "unknown"

    # A dev/dirty build (has .devN or a +local segment) is not a clean release: report
    # it distinctly so a clone-installed copy is honestly flagged.
    if tparsed.dev is not None or tparsed.is_local:
        return "dev"

    cmp = compare(target, packaged)
    if cmp < 0:
        return "stale"
    if cmp > 0:
        return "ahead"
    return "current"


# --------------------------------------------------------------------------------------
# PyPI published-version lookup (for release-review next-version >= published; D-PyPI)
# --------------------------------------------------------------------------------------


def latest_pypi_version(name: str, timeout: float = 5.0) -> Optional[str]:
    """Return the latest version published on PyPI for ``name``, or None.

    Uses the stdlib JSON API (``https://pypi.org/pypi/<name>/json``); zero deps. Returns
    None on ANY failure - offline, timeout, 404 (unpublished), or a parse error - so callers
    can degrade gracefully and never crash a release review on network state.
    """

    import json
    import urllib.error
    import urllib.request

    url = f"https://pypi.org/pypi/{name}/json"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (https only)
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None
    version = (data.get("info") or {}).get("version")
    return version if isinstance(version, str) and version else None


def next_version_ok(proposed: str, published: Optional[str]) -> bool:
    """True if ``proposed`` is a valid next version: >= the ``published`` PyPI version.

    When ``published`` is None (unpublished / lookup failed), any proposed version is allowed.
    Uses this module's own comparator (no third-party ``packaging`` dep).
    """

    if not published:
        return True
    return compare(proposed, published) >= 0

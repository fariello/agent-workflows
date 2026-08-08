"""Shared area-agnostic core for .agents/ artifact organization (Set plans-adopter, Order 01).

This module OWNS the primitives that are common to EVERY growing `.agents/` artifact tree, so each
area (research, plans, and later prompts/comms/walkthroughs) reuses ONE definition instead of
forking:

* the stable, greppable ``<id6>`` primitive (6-char base36 lowercase) + validators + generator;
* the weekly-shard date math (``YYYYMM-Www``);
* the tracked-text scan-root iteration + atomic write + tracked ``git mv`` helpers;
* an area-parameterized dangling-citation detector (the caller supplies the scan roots + a
  current-id resolver + a citation matcher, so the SAME detector serves research ids and plan ids);
* a generic drift record + the ``--agent`` / exit-code conventions used by every ``--check`` gate.

It is pure and stdlib-only (zero runtime dependencies, D46), Python 3.9 compatible, and has no
side effects beyond the explicit filesystem helpers (`atomic_write`, `git_mv`) that a caller
invokes deliberately. Area-SPECIFIC things (filename grammar, kind/model vocab, frontmatter schema,
the concrete manifest entry/render) stay in each area's module; only the area-agnostic shape lives
here (research-org DECISIONS D123; plans-adopter spec 20260808-0004-01 Section 4.1).
"""

from __future__ import annotations

import os
import re
import secrets
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, List, NamedTuple, Optional

# --------------------------------------------------------------------------------------
# Identity: the stable, greppable ``<id6>``
# --------------------------------------------------------------------------------------

ID6_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"  # base36 lowercase
ID6_LENGTH = 6

# An id token in isolation (a whole string is exactly the id).
ID6_RE = re.compile(r"\A[0-9a-z]{6}\Z")
# An id token as a word inside a filename or prose. ``\b`` treats ``-`` as a boundary, so a
# ``-`` delimited id in ``...-k7m2xq-...`` and a bare ``k7m2xq`` in prose both match.
ID6_WORD_RE = re.compile(r"\b[0-9a-z]{6}\b")


def is_valid_id6(token: str) -> bool:
    """True iff ``token`` is exactly a 6-char base36-lowercase id."""

    return bool(ID6_RE.match(token))


def iter_id6_in_text(text: str) -> List[str]:
    """Return every ``\\b<id6>\\b`` word-boundary match in ``text`` (low-level; matches any 6-token)."""

    return ID6_WORD_RE.findall(text)


def generate_id6(existing: set, _rng: Optional[Callable[[str], str]] = None) -> str:
    """Generate a fresh 6-char base36-lowercase id not in ``existing`` (collision-checked)."""

    rng = _rng or secrets.choice
    for _ in range(10000):
        candidate = "".join(rng(ID6_ALPHABET) for _ in range(ID6_LENGTH))
        if candidate not in existing:
            return candidate
    raise RuntimeError("could not generate a unique id6 after many attempts")


# --------------------------------------------------------------------------------------
# Slug / set-id kebab normalization
# --------------------------------------------------------------------------------------

_KEBAB_STRIP_RE = re.compile(r"[^a-z0-9]+")


def kebab(text: str) -> str:
    """Lowercase kebab-case a free string; collapse separators."""

    return _KEBAB_STRIP_RE.sub("-", text.strip().lower()).strip("-")


# --------------------------------------------------------------------------------------
# Weekly-shard date math (YYYYMM-Www)
# --------------------------------------------------------------------------------------

SHARD_DIR_RE = re.compile(r"\A(?P<yyyymm>\d{6})-W(?P<week>\d{2})\Z")


def shard_dirname(yyyymm: str, week: int) -> str:
    """Return a weekly shard directory name ``YYYYMM-Www`` (e.g. ``202607-W30``)."""

    return f"{yyyymm}-W{week:02d}"


def is_valid_shard_dirname(name: str) -> bool:
    """True iff ``name`` is a valid weekly shard directory name."""

    return bool(SHARD_DIR_RE.match(name))


def shard_for_date(yyyymmdd: str) -> str:
    """Map a ``YYYYMMDD`` date to its weekly shard name ``YYYYMM-Www`` (ISO week).

    The week number is the ISO calendar week; the ``YYYYMM`` prefix is the date's own year-month, so
    shards sort chronologically in a name-sorted tree. Deterministic and dependency-free.
    """

    import datetime

    d = datetime.date(int(yyyymmdd[0:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:8]))
    week = d.isocalendar()[1]
    return shard_dirname(yyyymmdd[0:6], week)


# --------------------------------------------------------------------------------------
# Writing-command safety helpers (atomic write, tracked git mv)
# --------------------------------------------------------------------------------------


def atomic_write(path: Path, text: str, *, prefix: str = ".aw-tmp-") -> None:
    """Write-to-temp-then-rename so an interrupted apply never leaves a partial file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=prefix, suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def git_mv(repo_root: Path, src_rel: str, dst_rel: str) -> None:
    """git mv (staged, not committed), with a filesystem fallback for untracked files."""

    (repo_root / dst_rel).parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "-C", str(repo_root), "mv", "--", src_rel, dst_rel],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        import shutil

        shutil.move(str(repo_root / src_rel), str(repo_root / dst_rel))


# --------------------------------------------------------------------------------------
# Tracked-text scan root (the places that cite artifacts)
# --------------------------------------------------------------------------------------

# The pinned tracked-text scan roots, relative POSIX to the repo root. This is the single
# enumeration shared by the reference tools and the dangling detector across areas.
SCAN_ROOTS = (
    "DECISIONS.md",
    "TODO.md",
    "README.md",
    "ARCHITECTURE.md",
    ".agents/plans",
    ".agents/docs",
)

_TEXT_SUFFIXES = (".md", ".txt")


def iter_scan_files(repo_root: Path, scan_roots=SCAN_ROOTS) -> List[Path]:
    """Return every tracked-text file under the given scan roots (deterministic, sorted)."""

    files: List[Path] = []
    for rel in scan_roots:
        p = repo_root / rel
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix in _TEXT_SUFFIXES:
                    files.append(f)
    return sorted(set(files))


# --------------------------------------------------------------------------------------
# Area-parameterized dangling-citation detector
# --------------------------------------------------------------------------------------


class Dangler(NamedTuple):
    """A dangling citation: a citation whose id does not resolve to a current artifact."""

    file: Path
    line: int
    id6: str
    context: str


def find_dangling_citations(
    repo_root: Path,
    *,
    current_ids: set,
    cite_matcher: Callable[[str], List[str]],
    exclude_root: Optional[Path] = None,
    scan_roots=SCAN_ROOTS,
) -> List[Dangler]:
    """Return every CITATION (per ``cite_matcher``) whose id is not in ``current_ids``.

    Area-agnostic: the caller supplies ``current_ids`` (the resolvable ids for the area) and
    ``cite_matcher`` (a function ``str -> [id6, ...]`` that extracts only real citations, not bare
    words). ``exclude_root`` (optional) skips files under an area's own tree (e.g. do not scan
    research files for their own ids as citations). Pure and deterministic.
    """

    danglers: List[Dangler] = []
    for f in iter_scan_files(repo_root, scan_roots):
        if exclude_root is not None:
            try:
                f.relative_to(exclude_root)
                continue  # inside the area's own tree; skip
            except ValueError:
                pass
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            for tok in cite_matcher(line):
                if tok not in current_ids:
                    danglers.append(Dangler(f, i, tok, line.strip()[:120]))
    return danglers


# --------------------------------------------------------------------------------------
# Generic drift record + --check conventions (the shape every area's --check reuses)
# --------------------------------------------------------------------------------------


class Drift(NamedTuple):
    """A drift finding for a ``--check`` gate (location + rule + detail)."""

    location: str
    rule: str
    detail: str


def render_agent_drift(drift: List[Drift]) -> str:
    """Render drift as one tab-separated ``location\\trule\\tdetail`` record per line (the D-class
    machine-readable convention). No prose."""

    return "".join(f"{d.location}\t{d.rule}\t{d.detail}\n" for d in drift)


def drift_exit_code(drift: List[Drift]) -> int:
    """The standard ``--check`` exit convention: 0 clean, 1 drift present. (2 = could-not-run is
    the caller's to return on an invocation/parse failure.)"""

    return 1 if drift else 0

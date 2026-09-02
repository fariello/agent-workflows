"""Shared selector resolver: turn selector tokens (direct path | id6 | setid | status | bare stem |
filename fragment) into concrete record file paths for a record type. Pure (no CLI, no writes).

This module is the ONE selector-to-file resolver for the whole package (IPD laykok, unifyfileio
Order 02): every verb (`rename`, `group`, `set`/`ipd set`/`spec set`/`backlog set`, `show`, `find`,
`archive`, and the per-area set-assign/mv paths) routes selector resolution through `resolve()` here,
so the SAME selector resolves to the SAME file for every verb (or yields one uniform no-match /
ambiguous-match result). Per the orchestrator's module-placement principle, this resolver MAY import
the Order 01 naming authority (for bare-stem parsing); the naming authority never imports this.

FRONT-MATTER DIALECT: WHY THE RESEARCH INDEX IS DELIBERATELY NOT WIRED IN HERE (IPD e32j35 E-06).
Two of the ten artifact types ship a generated manifest (`plans/INDEX.json`, `research/INDEX.json`)
whose columns look like exactly what the id6/setid/status rules need. For RESEARCH that appearance
is false, and reading it would CHANGE what `aw find research` matches:

  * this resolver only understands the BULLET dialect (`- Id:`, `- Status:`, `- Set:`), which is what
    plans, specs, backlog and the rest use;
  * research docs use YAML front matter instead (`id:`, `status:`, `set:` between `---` fences,
    parsed by `research_contract.parse_frontmatter` via `research_index._scan_docs`);
  * measured 2026-09-01: 0 of 103 research files carry a `- Id:` bullet while 101 carry a YAML `id:`.
    So `aw find research <id6>` does NOT resolve via MATCH_ID6 today - it succeeds only because the
    id6 also appears in the FILENAME, i.e. via MATCH_SUBSTRING;
  * consequently a status query is filename-shaped too: `aw find research reference` matches 5 files
    by filename, whereas `research/INDEX.json` holds 52 entries with `status: reference`. Feeding the
    index into these rules would turn that 5 into 52.

That order-of-magnitude shift is a SEMANTIC change (which dialects a selector understands), not a
performance one, so it does not belong to a resolver-cost change. Research therefore stays on the
filesystem scan, and the underlying dialect gap is tracked as its own backlog item rather than being
silently "fixed" here. The same caution applies to the plans index: see the parity note on
`_STATUS_RE` below, where the two readers provably disagree on 24 records."""

from __future__ import annotations

import contextlib
import os
import re
from pathlib import Path
from typing import List, NamedTuple, Optional

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
from agent_workflows import record_producers as _rp

_SKIP_NAMES = {"README.md", "INDEX.md", "STATUS.md"}

# ----------------------------------------------------------------------------------------------
# The canonical selector-match KIND vocabulary and the structured Resolution result (E-02).
# ----------------------------------------------------------------------------------------------

# Precedence order (first rule that yields matches wins), with per-kind match semantics:
#   1. path      - a direct absolute/repo-relative path to an existing file (exact)
#   2. id6       - an exact frontmatter `- Id:` id6 (exact)
#   3. setid     - an exact `- Set:` first-token setid (exact)
#   4. status    - an exact `- Status:` token (exact)
#   5. stem      - an exact filename stem parsed via the Order 01 naming authority (exact)
#   6. substring - a filename substring, the explicit LAST-RESORT only (non-exact)
MATCH_PATH = "path"
MATCH_ID6 = "id6"
MATCH_SETID = "setid"
MATCH_STATUS = "status"
MATCH_STEM = "stem"
MATCH_SUBSTRING = "substring"

# Kinds that identify at most ONE file by design (a multi-match on these is a COLLISION, not an
# intentional multi-target). setid is deliberately NOT here (a Set is a group). substring is genuine
# ambiguity. Used by the kind-aware ambiguity policy (E-07).
UNIQUE_KINDS = frozenset({MATCH_PATH, MATCH_ID6, MATCH_STEM})

_PRECEDENCE = (
    MATCH_PATH,
    MATCH_ID6,
    MATCH_SETID,
    MATCH_STATUS,
    MATCH_STEM,
    MATCH_SUBSTRING,
)


class Resolution(NamedTuple):
    """The structured result of resolving one selector against one record type.

    * ``paths``         - the matched file paths (sorted; empty for no-match).
    * ``kind``          - the MATCH KIND that produced ``paths`` (one of the MATCH_* constants), or
                          None for a no-match / denied-kind rejection.
    * ``rejected_kind`` - set when the selector matched ONLY via a kind the caller DENIED (so the
                          caller can emit a clear rejection naming the kind, never a silent
                          no-match). None otherwise.
    * ``selector``      - the original selector token (for messages).
    """

    paths: List[Path]
    kind: Optional[str]
    rejected_kind: Optional[str]
    selector: str

    @property
    def is_match(self) -> bool:
        return bool(self.paths)

    @property
    def is_unique(self) -> bool:
        return len(self.paths) == 1

    @property
    def is_ambiguous(self) -> bool:
        return len(self.paths) > 1


_ID_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
# PARITY CONSTRAINT (IPD e32j35 E-03), and editing this line CHANGES WHAT `aw find` MATCHES.
# This `(\S+)` requires the WHOLE status value to be a single token, so a multi-word value yields
# NO status match at all. Its twin `plans_index._META_RE["Status"]` (plans_index.py:37) uses
# `(.+?)` and captures the whole line, so the two readers DIVERGE by design of history, not intent.
# Measured 2026-09-01 on this repo: 24 of 469 plans carry a multi-word `- Status:` (e.g.
# `EXECUTED (approved by maintainer ...)`) and the two regexes disagree on exactly those 24.
# Consequence: widening this regex would make `aw find plans EXECUTED` start matching records it
# deliberately does not match today. That is a MATCHING-BEHAVIOR decision, not a cleanup; do not
# "harmonize" the two patterns without owning that contract change.
_STATUS_RE = re.compile(r"(?m)^- Status:\s*(\S+)\s*$")
_SET_RE = re.compile(r"(?m)^- Set:\s*(.+?)\s*$")


KNOWN_PRIMARY_TYPES = frozenset(
    {
        "plans",
        "specs",
        "prompts",
        "research",
        "backlog",
        "walkthroughs",
        "roadmaps",
        "comms",
        "releases",
    }
)

EXCLUDED_RECORD_DIRS = frozenset(
    {
        "runs",
        "scratch",
        "tmp",
        "temp",
        ".git",
        ".system_generated",
        "__pycache__",
    }
)


def record_dirs(repo_root: Path, record_type: str) -> List[Path]:
    """Directories to search for a record type (primary + any legacy read path).

    Combines the project-context resolver (`resolve_record_read_paths`, which honors a registered
    project/home backend) with the DIRECT literal layout under `repo_root` (`.aw/records/<type>` +
    legacy `.agents/<type>`), so this works for a bare/unregistered repo too. De-duplicated; only
    existing dirs. Returns [] for an unknown/unresolvable type rather than raising.
    """
    repo_root = Path(repo_root)
    out: List[Path] = []
    seen: set = set()

    def _add(p: Path) -> None:
        try:
            rp = p.resolve()
        except OSError:
            return
        key = str(rp)
        if key not in seen and p.is_dir():
            seen.add(key)
            out.append(p)

    if record_type == "other":
        for base in (repo_root / ".aw" / "records", repo_root / ".agents"):
            if not base.is_dir():
                continue
            for child in base.iterdir():
                if (
                    child.is_dir()
                    and child.name not in KNOWN_PRIMARY_TYPES
                    and child.name not in EXCLUDED_RECORD_DIRS
                ):
                    _add(child)
            with contextlib.suppress(OSError):
                if any(
                    f.is_file() and f.suffix == ".md" and f.name not in _SKIP_NAMES
                    for f in base.iterdir()
                ):
                    _add(base)
        _add(repo_root / ".aw" / "records" / "other")
        _add(repo_root / ".agents" / "other")
        return out

    try:
        for p in _rp.resolve_record_read_paths(record_type, target_repo=str(repo_root)):
            _add(p)
    except Exception:
        pass
    # Direct literal layout (covers a bare/unregistered repo, and backlog/roadmaps/releases which
    # the RecordClass resolver rejects).
    _add(repo_root / ".aw" / "records" / record_type)
    _add(repo_root / ".agents" / record_type)
    return out


def _read_id(text: str) -> str | None:
    m = _ID_RE.search(text)
    return m.group(1) if m else None


def _read_status(text: str) -> str | None:
    m = _STATUS_RE.search(text)
    return m.group(1) if m else None


def _read_setid(text: str) -> str | None:
    m = _SET_RE.search(text)
    if not m:
        return None
    # The set-id is the first whitespace token before any '(' (mirrors plans_index.set_terse_id).
    return m.group(1).split("(")[0].strip().split()[0] if m.group(1).strip() else None


# PERF (awfindperf): selector matching only ever consults the front-matter bullets
# (`- Id:`, `- Status:`, `- Set:`) via _read_id/_read_status/_read_setid, which live in the
# first handful of lines. Reading whole files (some are multi-hundred-KB records) dominated
# `aw find`. We read a bounded header instead. The cap is generous enough to cover a long
# metadata block plus a `## Workflow history` preamble.
_HEADER_BYTES = 4096


def _read_header(p: Path) -> str | None:
    """Read at most _HEADER_BYTES of a record file; None if unreadable.

    Front-matter bullets are always near the top, so a bounded read is sufficient for
    id6/status/setid extraction and avoids paging in large record bodies.
    """
    try:
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            return fh.read(_HEADER_BYTES)
    except OSError:
        return None


# Opt-in escape hatch for the traversal guard. Default False: `.git/`, `runs/`, `tmp/`, `temp/`,
# `scratch/`, `.system_generated/` and `__pycache__/` are never descended into, which is both a
# correctness guard (they hold scratch copies, not records) and the bulk of the traversal win.
# `aw find --include-ignored` flips this for one invocation when a user genuinely needs to look
# inside those trees (e.g. hunting a record stranded in a run directory).
_INCLUDE_IGNORED_DIRS: bool = False
_MAX_DEPTH: Optional[int] = None


@contextlib.contextmanager
def search_limits(include_ignored: bool = False, max_depth: Optional[int] = None):
    """Scope both traversal overrides for the duration of the block."""
    global _INCLUDE_IGNORED_DIRS, _MAX_DEPTH
    prev_inc, prev_depth = _INCLUDE_IGNORED_DIRS, _MAX_DEPTH
    _INCLUDE_IGNORED_DIRS = bool(include_ignored)
    _MAX_DEPTH = max_depth
    try:
        yield
    finally:
        _INCLUDE_IGNORED_DIRS, _MAX_DEPTH = prev_inc, prev_depth


@contextlib.contextmanager
def include_ignored_dirs(enabled: bool = True):
    """Scope the traversal guard off (or on) for the duration of the block.

    A context manager rather than a threaded parameter because the call chain
    (cli -> _find_type_records -> resolve_selectors -> resolve -> _iter_files -> _iter_md) is deep
    and every layer would otherwise need a pass-through argument it does not use.
    """
    global _INCLUDE_IGNORED_DIRS
    prev = _INCLUDE_IGNORED_DIRS
    _INCLUDE_IGNORED_DIRS = bool(enabled)
    try:
        yield
    finally:
        _INCLUDE_IGNORED_DIRS = prev


def _iter_md(base: Path, max_depth: Optional[int] = None):
    """Walk `base` yielding *.md files while PRUNING excluded dirs before descending.

    `Path.rglob` cannot prune, so it descends into `.git/`, `runs/`, `tmp/`, `scratch/`,
    `__pycache__/` and similar before we get a chance to skip their contents. os.walk lets us
    drop those subtrees from `dirnames` in place, so they are never traversed at all.

    Pruning is skipped when `_INCLUDE_IGNORED_DIRS` is set (see `include_ignored_dirs`).
    `max_depth`, when given, limits how many directory levels below `base` are descended
    (0 = only `base` itself).
    """
    if max_depth is None:
        max_depth = _MAX_DEPTH
    base_depth = len(base.parts)
    for dirpath, dirnames, filenames in os.walk(base):
        if not _INCLUDE_IGNORED_DIRS:
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_RECORD_DIRS]
        if max_depth is not None:
            if len(Path(dirpath).parts) - base_depth >= max_depth:
                dirnames[:] = []
        for fn in filenames:
            if fn.endswith(".md"):
                yield Path(dirpath) / fn


def _iter_paths(repo_root: Path, record_type: str):
    """Yield every non-index *.md record PATH for the type, de-duplicated, WITHOUT reading a body.

    This is the TEXT-FREE half of the enumeration (IPD e32j35 E-05). Three of the six selector
    rules - ``path``, ``stem`` and ``substring`` - match on the PATH or FILENAME alone and never
    look at file contents, yet they used to be served from ``_iter_files``, which had already paid
    for a bounded header read of every candidate. ``_iter_files`` now layers the header read back
    on top of THIS walk, for the three rules (``id6``/``setid``/``status``) that genuinely need
    front matter.

    HONEST SCOPE OF THE WIN, because E-05 predicted more than is achievable. This does NOT make a
    stem or substring QUERY read-free, and it cannot: precedence is a frozen contract in which
    ``stem`` and ``substring`` come LAST, so before returning a filename match the resolver must
    first establish that ``setid`` and ``status`` did not match - and those live in front matter. A
    token really can be both (a Set id is also a filename fragment of its own members), so skipping
    that check would CHANGE which record wins. What this split does buy: the filename rules cost
    nothing of their OWN, a filename match no longer depends on the body being readable, and the
    read-free primitive the deferred two-tier design needs now exists. Only ``path``, which
    short-circuits ahead of every scan, actually resolves at zero opens.

    Traversal, pruning, the `_SKIP_NAMES` filter and the resolved-path de-duplication are IDENTICAL
    to ``_iter_files``, which now delegates here, so the two enumerations cannot drift apart.
    """
    seen: set = set()
    if record_type == "other":
        known_dirs = {
            d.resolve()
            for rt in KNOWN_PRIMARY_TYPES
            for d in record_dirs(repo_root, rt)
        }
        for base in (repo_root / ".aw" / "records", repo_root / ".agents"):
            if not base.is_dir():
                continue
            for p in _iter_md(base):
                if p.name in _SKIP_NAMES:
                    continue
                try:
                    p_res = p.resolve()
                except OSError:
                    continue
                if any(kd in p_res.parents or p_res == kd for kd in known_dirs):
                    continue
                try:
                    rel_parts = set(p_res.relative_to(base.resolve()).parts)
                    if any(ex in rel_parts for ex in EXCLUDED_RECORD_DIRS):
                        continue
                except ValueError:
                    pass
                rp = str(p_res)
                if rp in seen:
                    continue
                seen.add(rp)
                yield p
        return

    for d in record_dirs(repo_root, record_type):
        for p in _iter_md(d):
            if p.name in _SKIP_NAMES:
                continue
            rp = str(p.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            yield p


def _iter_files(repo_root: Path, record_type: str):
    """Yield (path, text) for every non-index *.md record file of the type, de-duplicated by path.

    `text` is a BOUNDED header read (see _read_header), sufficient for every selector rule that
    consults front matter. Delegates enumeration to ``_iter_paths`` so the text-free and
    text-bearing walks stay by construction identical.

    A file whose header cannot be READ is skipped here (it has no front matter to match on), which
    is why the ``path``/``stem``/``substring`` rules deliberately use ``_iter_paths`` instead: a
    FILENAME match must not depend on whether the body happens to be readable.
    """
    for p in _iter_paths(repo_root, record_type):
        text = _read_header(p)
        if text is None:
            continue
        yield p, text


def _stem_of(name: str) -> Optional[str]:
    """The exact filename stem (name without a `.md`/facet suffix) if the name parses under the
    Order 01 naming authority (clustered, legacy-timestamp, or dated-slug); else None. Used by the
    exact-stem selector kind so a stem is matched EXACTLY, not incidentally via substring."""

    if (
        _naming.parse_clustered(name)
        or _naming._LEGACY_TIMESTAMP_RE.match(name)
        or _naming._DATED_SLUG_FACET_RE.match(name)
    ):
        # The stem is the name without the trailing `.md`.
        return name[:-3] if name.endswith(".md") else name
    return None


def resolve(
    repo_root: Path,
    record_type: str,
    selector: str,
    *,
    allow: Optional[frozenset] = None,
    deny: Optional[frozenset] = None,
) -> Resolution:
    """Resolve ONE selector to file(s) for a record type, over the FULL vocabulary with ONE
    documented precedence and explicit per-kind match semantics (IPD laykok E-02).

    Precedence (first rule that yields matches wins), carrying the match KIND:
      1. ``path``      direct absolute/repo-relative path to an existing file;
      2. ``id6``       EXACT frontmatter ``- Id:`` (``artifact_core.ID6_RE``);
      3. ``setid``     EXACT ``- Set:`` first token;
      4. ``status``    EXACT ``- Status:`` token;
      5. ``stem``      EXACT filename stem (parsed via the Order 01 naming authority);
      6. ``substring`` filename substring - the explicit LAST-RESORT only.

    Kinds 2-5 are EXACT; only kind 6 is a substring, fixing the pre-unification divergence where
    ``resolve_one`` used substring for filenames while other rules were exact.

    ``allow`` / ``deny`` (sets of MATCH_* kinds) let a verb restrict which selector kinds it accepts.
    When a selector matches ONLY via a DENIED (or not-allowed) kind, the returned Resolution has
    ``rejected_kind`` set and empty ``paths`` (a CLEAR rejection the caller must surface, NEVER a
    silent no-match). The returned ``Resolution`` carries the winning ``kind`` so callers can apply
    the kind-aware ambiguity policy (E-07).
    """

    tok = (selector or "").strip()
    if not tok:
        return Resolution([], None, None, selector)

    def _allowed(kind: str) -> bool:
        if allow is not None and kind not in allow:
            return False
        if deny is not None and kind in deny:
            return False
        return True

    # Candidate hits per kind (computed lazily in precedence order). We first find the WINNING kind
    # ignoring allow/deny (so a denied-kind match becomes an explicit rejection, not a silent skip).
    # ONE traversal, shared by both views (IPD e32j35 E-05). `_paths()` is the text-free candidate
    # list; `_files()` layers a bounded header read over THAT SAME list rather than walking again.
    # Walking twice would make a filename query SLOWER than before the split (measured: 83ms vs
    # 50ms on this repo's 469 plans), so the sharing is load-bearing, not tidiness.
    paths = None  # lazy: the single enumeration
    files = None  # lazy: (path, header-text) pairs derived from `paths`

    def _paths():
        """Candidate paths with NO file read at all - for the path/stem/substring rules."""
        nonlocal paths
        if paths is None:
            paths = list(_iter_paths(repo_root, record_type))
        return paths

    def _files():
        """Candidates paired with a BOUNDED header read - only for the front-matter rules.

        Reuses `_paths()`, so a query that consults BOTH views pays for ONE traversal. A file whose
        header cannot be read is dropped here (it has no front matter to match on) but remains
        visible to the filename rules via `_paths()`.
        """
        nonlocal files
        if files is None:
            out = []
            for p in _paths():
                text = _read_header(p)
                if text is not None:
                    out.append((p, text))
            files = out
        return files

    def _hits_for(kind: str) -> List[Path]:
        if kind == MATCH_PATH:
            cand = Path(tok)
            if not cand.is_absolute():
                cand_rel = repo_root / tok
            else:
                cand_rel = cand
            for c in {cand, cand_rel}:
                try:
                    if c.is_file():
                        return [c.resolve()]
                except OSError:
                    continue
            return []
        if kind == MATCH_ID6:
            if not _core.ID6_RE.match(tok):
                return []
            return [p for p, text in _files() if _read_id(text) == tok]
        if kind == MATCH_SETID:
            return [p for p, text in _files() if _read_setid(text) == tok]
        if kind == MATCH_STATUS:
            return [p for p, text in _files() if _read_status(text) == tok]
        # The filename-only rules read NO file content (E-05): they consult `_paths()`, never
        # `_files()`. Keep it that way - routing either one back through `_files()` silently
        # reintroduces a bounded header read per candidate for a match that cannot use it.
        if kind == MATCH_STEM:
            return [p for p in _paths() if _stem_of(p.name) == tok]
        if kind == MATCH_SUBSTRING:
            return [p for p in _paths() if tok in p.name]
        return []

    for kind in _PRECEDENCE:
        hits = _hits_for(kind)
        if not hits:
            continue
        # This kind is the winner. Enforce allow/deny: a match only via a denied kind is a rejection.
        if not _allowed(kind):
            return Resolution([], None, kind, selector)
        # Sort by resolved path for determinism.
        uniq = {str(p): p for p in hits}
        return Resolution([uniq[k] for k in sorted(uniq)], kind, None, selector)

    return Resolution([], None, None, selector)


def resolve_for_mutation(
    repo_root: Path,
    record_type: str,
    selector: str,
    *,
    force: bool = False,
    allow: Optional[frozenset] = None,
    deny: Optional[frozenset] = None,
):
    """Resolve a selector for a MUTATING verb and apply the kind-aware ambiguity policy (E-07).

    Returns ``(paths, error_message)``: ``error_message`` is None on success (``paths`` is the target
    set to mutate), or a human-readable refusal (``paths`` empty) that the caller prints. Policy
    (OQ-01, resolved by human):
      * a ``setid`` multi-match is an intentional multi-target -> act on ALL members, no ``--force``;
      * a UNIQUE-id multi-match (path/id6/stem = a collision) -> ALWAYS refuse (``--force`` does not
        override a data bug), listing the candidates;
      * a filename ``substring`` multi-match -> refuse UNLESS ``force``, then act on all, listing the
        candidates in the refusal;
      * a denied-kind match -> refuse, naming the denied kind (never a silent no-match).
    """

    res = resolve(repo_root, record_type, selector, allow=allow, deny=deny)
    if res.rejected_kind is not None:
        return (
            [],
            f"this verb does not accept a {res.rejected_kind} selector: {selector!r}",
        )
    if not res.paths:
        return [], f"no {record_type} artifact matched {selector!r}"
    if len(res.paths) == 1:
        return list(res.paths), None

    # Multiple matches: apply the kind-aware policy.
    cand = "\n  ".join(str(p) for p in res.paths)
    if res.kind == MATCH_SETID:
        return list(res.paths), None  # intentional multi-target
    if res.kind in UNIQUE_KINDS:
        return [], (
            f"selector {selector!r} is a {res.kind} collision matching multiple files "
            f"(a data bug to fix, not overridable by --force):\n  {cand}"
        )
    # substring
    if force:
        return list(res.paths), None
    return [], (
        f"selector {selector!r} is ambiguous ({res.kind}) matching multiple files; "
        f"pass --force to act on all:\n  {cand}"
    )


def resolve_one(repo_root: Path, record_type: str, token: str) -> List[Path]:
    """Resolve ONE token to file paths (back-compat shim over :func:`resolve`).

    Historical behavior kept: no direct-path branch (callers that need a path go through
    ``resolve``/``find_target_record``). The precedence id6 -> status -> setid -> substring is
    superseded by the unified id6 -> setid -> status -> stem -> substring, which is behavior-
    equivalent for real records (a token is not simultaneously a setid AND a status). Returns the
    matched paths (sorted), or [] for no match.
    """
    res = resolve(repo_root, record_type, token, deny=frozenset({MATCH_PATH}))
    return list(res.paths)


def resolve_selectors(
    repo_root: Path, record_type: str, tokens: List[str]
) -> List[Path]:
    """The public API: OR-union of resolve_one over every token, de-duplicated, sorted by path.
    An empty tokens list returns []."""
    seen: dict = {}
    for tok in tokens:
        for p in resolve_one(repo_root, record_type, tok):
            seen[str(p)] = p
    return [seen[k] for k in sorted(seen)]

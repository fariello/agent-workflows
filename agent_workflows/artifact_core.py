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

import functools
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
    """Generate a fresh 6-char base36-lowercase id not in ``existing`` (collision-checked).

    DELIBERATELY PURE. It takes the collision set as an ARGUMENT and never fetches one itself, and
    ``_rng`` is injectable, which together are what make a forced-collision test possible (pin the
    rng to a candidate that is already taken and assert the generator moves past it). A version that
    reached out to the filesystem for its own set could not be unit-tested that way. Callers that
    want the repository-wide set ask :func:`global_id6s` for it and pass the result in.
    """

    rng = _rng or secrets.choice
    for _ in range(10000):
        candidate = "".join(rng(ID6_ALPHABET) for _ in range(ID6_LENGTH))
        if candidate not in existing:
            return candidate
    raise RuntimeError("could not generate a unique id6 after many attempts")


def global_id6s(repo_root) -> set:
    """Every id6 in use ANYWHERE in the repository's records: THE collision set for minting.

    WHY THIS EXISTS (IPD ``sk7ggr`` E-01). id6 identity is repository-WIDE, but minting was
    per-TREE at all eleven call sites: ``backlog`` checked backlog ids, ``specs`` spec ids, and so
    on, so a fresh backlog id6 could equal an existing spec's and nothing would notice until after
    the file was written. This helper is the one set that makes that impossible, and every mint site
    passes it to :func:`generate_id6`.

    IT DELIBERATELY INCLUDES TERMINAL ARTIFACTS, which is the load-bearing detail. An executed plan's
    or a done item's id6 is permanently cited across the repository (``Item-Dependencies``,
    ``From-Backlog``, ``From-Spec``, review filenames, prose), so re-minting it is a real collision
    even though the original is no longer live. The measured motivating case is exactly this shape:
    ``uyeko5`` is held by a plan in ``executed/``.

    THE RETURNED SET IS A CONSERVATIVE SUPERSET, NOT AN EXACT CENSUS, AND THAT ASYMMETRY IS THE
    POINT (IPD ``sk7ggr`` E-07). It is built from readers that are UNBOUNDED, i.e. they match a
    ``- Id:``/``id:`` line ANYWHERE in a document including inside a fenced code block, so a research
    report QUOTING another artifact's metadata block contributes that quoted id6 here. Measured: the
    set holds ``uyeko5`` partly because two research documents quote it as an example.

    * For MINTING that over-collection is HARMLESS and even conservative: refusing to mint one
      already-quoted candidate costs one draw out of 36**6, and the result is still guaranteed not to
      collide with anything real.
    * For CHECKING it is WRONG, because treating a quotation as a declaration manufactures a
      collision finding for a document whose real identity is its own. That is a live defect and it
      is NOT fixed here; bounding the identity readers to the front-matter region is owned by IPD
      ``76w6mq`` (from backlog ``cqytxf``).

    THE SPECIFIC UNBOUNDED READER BEHIND THIS SET IS ``status_set._ID_RE``, and it is OUTSIDE
    ``76w6mq``'s declared scope (``selectors.py`` + ``check_engine.py``), so one unbounded reader
    survives even after that plan lands. Recorded as backlog ``q1ov25`` rather than fixed here,
    because ``cqytxf`` warns that several plans editing these readers is what recreated parser drift
    before. ``tests/test_id6_global_mint.py`` pins the superset behavior so this cannot be mistaken
    for an exact census.

    So do NOT "optimize" this onto a checker's reader, do not describe it to a user as "the id6s in
    use", and never reuse it to decide that a collision EXISTS. Over-collect for minting; parse
    precisely for checking.

    Falls back to a per-caller empty set only if the scan genuinely cannot run (no records tree),
    because a mint must not be blocked by an unreadable repository; the caller's own per-tree set is
    unioned in by :func:`mint_id6` so a fallback is never worse than the previous behavior.
    """

    try:
        from agent_workflows import artifact_adopt as _adopt

        return set(_adopt.repository_id6s(Path(repo_root)))
    except Exception:
        return set()


def repo_root_of(path) -> Path:
    """Walk up from any path inside a repository to its root; fall back to the path itself.

    Exists so a caller holding only a TREE root (``research_cmd`` is handed a ``research_root``, not a
    repo root) can still reach the repository-wide mint set. Same marker set and shape as
    ``status_set._repo_root_of`` / ``specs._repo_root_of``.
    """

    p = Path(path).resolve()
    for anc in [p] + list(p.parents):
        if (
            (anc / ".aw").is_dir()
            or (anc / ".agents").is_dir()
            or (anc / ".git").exists()
        ):
            return anc
    return p


def mint_id6(
    repo_root,
    existing: Optional[set] = None,
    _rng: Optional[Callable[[str], str]] = None,
) -> str:
    """Mint a fresh id6 collision-checked against the REPOSITORY-WIDE set (plus ``existing``).

    This is the seam every mint call site uses (IPD ``sk7ggr`` E-01). ``existing`` is the caller's
    own per-tree set, UNIONED rather than replaced, for two reasons: a caller may hold ids that are
    not on disk yet (``research_cmd`` mints a whole Set in one pass and adds each id6 as it goes),
    and if the repository-wide scan degrades to empty the mint is still no worse than the per-tree
    check it replaced.

    :func:`generate_id6` stays pure; this function is the impure wrapper that fetches the set.
    """

    pool = global_id6s(repo_root)
    if existing:
        pool |= set(existing)
    return generate_id6(pool, _rng)


# --------------------------------------------------------------------------------------
# Slug / set-id kebab normalization
# --------------------------------------------------------------------------------------

_KEBAB_STRIP_RE = re.compile(r"[^a-z0-9]+")


def kebab(text: str) -> str:
    """Lowercase kebab-case a free string; collapse separators."""

    return _KEBAB_STRIP_RE.sub("-", text.strip().lower()).strip("-")


# --------------------------------------------------------------------------------------
# Monthly-shard date math (YYYYMM)
# --------------------------------------------------------------------------------------

SHARD_DIR_RE = re.compile(r"\A(?P<yyyymm>\d{6})\Z")
_LEGACY_WEEKLY_SHARD_RE = re.compile(r"\A\d{6}-W\d{2}\Z")


def shard_dirname(yyyymm: str, week: int = 0) -> str:
    """Return a monthly shard directory name ``YYYYMM`` (e.g. ``202607``)."""

    cleaned = yyyymm.replace("-", "").strip()
    return cleaned[:6]


def is_valid_shard_dirname(name: str) -> bool:
    """True iff ``name`` is a valid monthly shard directory name ``YYYYMM`` (or legacy weekly)."""

    return bool(SHARD_DIR_RE.match(name) or _LEGACY_WEEKLY_SHARD_RE.match(name))


def shard_for_date(yyyymmdd: str) -> str:
    """Map a ``YYYYMMDD`` date to its monthly shard name ``YYYYMM``.

    Deterministic, dependency-free, and aligns with the project's ``YYYYMMDD`` naming grammar.
    """

    cleaned = yyyymmdd.replace("-", "").strip()
    return cleaned[:6]


# --------------------------------------------------------------------------------------
# The ONE lifecycle-commit subject grammar (IPD `zexed1` E-02)
# --------------------------------------------------------------------------------------
#
# WHO ELSE READS THIS, and why it must be one definition rather than four literals.
# `aw ipd finalize` WRITES this subject (`ipd_lifecycle.finalize_plan`, the `commit_msg` it composes),
# the local pre-commit gate MATCHES it to authorize an in-tree executed-transition during a merge
# (`hooks/executed_transition_gate._intree_finalize_evidence_ok`), the finalize transaction's own
# outcome classifier PREFIX-matches it to recognize its own commit
# (`ipd_lifecycle._lifecycle_commit_exists`), and the run viewer's discrepancy classifier reads it out
# of history as evidence that a forward lifecycle move really happened
# (`artifact_audit.build_finalize_evidence_index`).
#
# THE FAILURE THIS PREVENTS IS SILENT AND ONE-SIDED. A fourth hand-written literal drifts from the
# producer the first time the subject changes, and the way it drifts is not a crash: the GATE stops
# recognizing genuine finalizes (so `--no-verify` becomes routine again) or the VIEWER stops finding
# real evidence (so every legitimately finalized row degrades to `unknown`). Neither shows up as a test
# failure in the module that changed. Change the subject HERE and every reader moves with it.
#
# Stdlib-only and dependency-free on purpose: the pre-commit gate deliberately keeps its module
# imports to `subprocess`/`pathlib`/`typing` and imports `ipd_lifecycle` lazily, so the constant
# cannot live in the producer without making the gate import-heavy.

#: The literal marker word every lifecycle commit subject carries before its verb.
LIFECYCLE_SUBJECT_KEYWORD = "lifecycle"


def lifecycle_commit_prefix(plan_id: str) -> str:
    """``lifecycle(<plan_id>)`` - the plan-bound prefix every lifecycle commit subject starts with.

    PLAN-BOUND BY CONSTRUCTION, which is a security property and not formatting: a finalize commit for
    plan A must never authorize or evidence a transition for plan B, so every reader binds on the id6
    inside the parentheses rather than on the keyword alone.
    """
    return f"{LIFECYCLE_SUBJECT_KEYWORD}({plan_id})"


def finalize_commit_subject(plan_id: str) -> str:
    """``lifecycle(<plan_id>): finalize`` - the EXACT subject form `aw ipd finalize` writes.

    Readers match a subject that STARTS WITH this string (the producer appends
    ``<id6> -> executed``). Deliberately narrow: a looser match would let an ordinary work commit that
    merely names the plan pass as finalize evidence, which is the hand-edit bypass wearing a different
    hat (`executed_transition_gate` OQ-02).
    """
    return f"{lifecycle_commit_prefix(plan_id)}: finalize"


# --------------------------------------------------------------------------------------
# Writing-command safety helpers (atomic write, tracked git mv)
# --------------------------------------------------------------------------------------


# The verbatim-preserved trees, named as consecutive path segments so a relative and an absolute
# path both match. `.pre-commit-config.yaml` deliberately excludes these from every content-MUTATING
# hook because "their own formatting/punctuation is intentional": an externally authored research
# artifact is cited as delivered. This writer must therefore not become the second mutator that
# exclusion exists to prevent, even though it (unlike the hooks) really does rewrite those files
# (`aw research set-outcome`/`set-priority`, `research_archive`, and the shared reference rewriter all
# write through here).
_VERBATIM_PRESERVED_SEGMENTS = (
    (".aw", "records", "research"),
    (".aw", "records", "docs", "research"),
    (".agents", "docs", "research"),
)


def _is_verbatim_preserved(path: Path) -> bool:
    """True iff ``path`` lies in a tree whose delivered formatting must not be rewritten."""

    parts = path.parts
    for segments in _VERBATIM_PRESERVED_SEGMENTS:
        span = len(segments)
        for i in range(len(parts) - span + 1):
            if parts[i : i + span] == segments:
                return True
    return False


def normalize_artifact_markdown(text: str) -> str:
    """Strip per-line trailing whitespace and end with exactly one newline.

    WHY AT THE WRITER RATHER THAN LEFT TO THE HOOK. Four of this repository's pre-commit hooks
    (``trailing-whitespace``, ``end-of-file-fixer``, ``ruff --fix``, ``ruff-format``) FIX a staged file
    and then REJECT the commit, and their exclude regex does not cover the ``.aw/records`` trees where
    agents write most. So one stray trailing space cost a full commit round trip. ``commit_isolated``
    now recovers from that in a single retry; this removes the trigger instead, which is strictly
    better because no retry is cheaper than one.

    THE RENDERERS DO NOT ALREADY DO THIS, measured rather than assumed: ``backlog._render_item`` and
    its siblings ``rstrip()`` the WHOLE FILE, which leaves per-line trailing whitespace untouched (a
    rendered body containing ``'body line with trailing   '`` kept that line verbatim).

    THE MARKDOWN HARD-LINE-BREAK TRADEOFF IS DELIBERATE AND OWNED HERE. A per-line rstrip destroys
    markdown's two-space hard line break. That is NOT a new loss: the ``trailing-whitespace`` hook
    ALREADY destroys it on every non-excluded path, so this makes the writer AGREE with the hook rather
    than fight it, and the alternative (writing a break the hook will delete at commit time) is the
    churn this change exists to end. MEASURED BASIS, so the claim is evidence and not recollection: at
    HEAD ``4b68a786`` there are ZERO two-space hard breaks and ZERO trailing-whitespace lines across
    the 1304 tracked ``.aw/records`` markdown files, so nothing in the corpus relies on the break and
    there is no backlog of dirty files to migrate. This is preventive, not remedial. Use an explicit
    ``<br>`` (or a blank line) where a hard break is genuinely wanted.
    """

    normalized = "\n".join(line.rstrip() for line in text.split("\n")).rstrip("\n")
    # An EMPTY result stays empty rather than becoming a lone newline: `end-of-file-fixer` treats an
    # all-whitespace file as empty, and inventing a newline here would hand the hook something to fix.
    return f"{normalized}\n" if normalized else ""


def atomic_write(path: Path, text: str, *, prefix: str = ".aw-tmp-") -> None:
    """Write-to-temp-then-rename so an interrupted apply never leaves a partial file.

    ARTIFACT MARKDOWN IS NORMALIZED ON THE WAY OUT (per-line trailing whitespace stripped, exactly one
    final newline) via :func:`normalize_artifact_markdown`, so a tool-authored artifact never gives the
    mutating pre-commit hooks anything to fix. TWO EXEMPTIONS, both load-bearing:

    * A NON-MARKDOWN write is passed through BYTE-FOR-BYTE. This helper is not markdown-only: the
      leak-sanitizer allowlist/user-hints and OpenCode's ``opencode.json`` are written through this
      shape too, and reformatting JSON or config is not this normalizer's business (a
      whitespace-significant value would be altered). The gate is the destination suffix, which this
      function already knows from ``path``.
    * A write into a VERBATIM-PRESERVED research tree is passed through byte-for-byte, on the basis of
      the pre-commit config's own stated reason for excluding those trees from every mutating hook.
      See :data:`_VERBATIM_PRESERVED_SEGMENTS`.
    """

    if path.suffix.lower() == ".md" and not _is_verbatim_preserved(path):
        text = normalize_artifact_markdown(text)

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=prefix, suffix=".md")
    try:
        # newline="\n": never translate to CRLF on Windows; the written bytes are the text's bytes.
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
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
# `TODO.md` is DELIBERATELY ABSENT (durablecapture-03, `diof9n`). It used to be listed, but no
# `TreePolicy` root covers a repository-root file, so `attention._classify_tree("TODO.md")` returned
# None and `attention.scan` dropped it with NO drift violation (the unclassified branch fires only
# under `.agents/`). That made it read-but-ignored: work written there vanished silently. The
# controlling spec authorizes retiring it (`.aw/records/specs/20260813-1833-01-attention-visible-
# backlog-tier.spec.md` G5: `TODO.md` "is then either retired or reduced to a pointer at the backlog
# tree + the Notes section"). Committed lightweight work belongs in `records/backlog/`, which IS
# scanned and IS attention-visible. Do not re-add `TODO.md` here: see
# `tests/test_artifact_core.py::ScanRootClassificationInvariantTests`.
SCAN_ROOTS = (
    "DECISIONS.md",
    "README.md",
    "ARCHITECTURE.md",
    ".agents/plans",
    ".agents/docs",
    ".agents/backlog",
    ".aw/records/plans",
    # Docs types flattened out of docs/ in Order 07 (spec 20260817-2124-01); scan them directly.
    ".aw/records/specs",
    ".aw/records/research",
    ".aw/records/walkthroughs",
    ".aw/records/roadmaps",
    ".aw/records/prompt-library",
    ".aw/records/backlog",
    # Releases (ship-gate anchors). `releases` is a TRACKED tree in `attention_contract.TREE_POLICY`
    # and carries a full status map, but it matched NO scan root until durablecapture-02 (`m867ox`),
    # so every release record was invisible to `aw attention` while the view still reported
    # `valid: true` (an unclassified file is only flagged as drift under `.agents/`). BOTH path
    # generations are listed, as for plans/backlog, but they are NOT interchangeable:
    # `.aw/records/releases` is the LOAD-BEARING entry, because `releases._releases_dir` writes and
    # reads there; `.agents/releases` (the `TreePolicy` root spelling) is carried for symmetry and
    # for pre-migration repositories, and on its own it fixes NOTHING here.
    ".agents/releases",
    ".aw/records/releases",
    # Prompts (staging tree; plan `dx0u4s`). Tracked in attention_contract.TREE_POLICY with both
    # path generations for modern .aw/records/prompts and legacy .agents/prompts.
    ".agents/prompts",
    ".aw/records/prompts",
)

_TEXT_SUFFIXES = (".md", ".txt")

DEFAULT_IGNORED_DIR_NAMES = frozenset(
    {
        "tmp",
        ".tmp",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "node_modules",
        ".venv",
        "venv",
        ".aw/records/runs",
        ".aw/state",
        ".aw/workflow-artifacts",
        ".agent-workflows-installer-backups",
    }
)


@functools.lru_cache(maxsize=64)
def _resolved_root_str(root: str) -> str:
    """Memoized `Path(root).resolve()` as a string, keyed on the raw path.

    Safe to cache: a repo root's canonical location does not change within a process, and the
    key is the literal argument, so a different root gets a different entry. Only the RESOLUTION
    is cached, never any decision derived from it.
    """
    return Path(root).resolve().as_posix()


@functools.lru_cache(maxsize=64)
def _is_repository_untracked_backend(repo_root_str: str) -> bool:
    from agent_workflows.project_context import read_project_identity
    from agent_workflows.project_schema import RecordsBackend

    identity = read_project_identity(Path(repo_root_str))
    return identity.get("records_backend") == RecordsBackend.REPOSITORY_UNTRACKED.value


def get_ignored_dirs(repo_root: Path) -> set[str]:
    """Return repo-relative POSIX paths of gitignored DIRECTORIES + default ignore sets."""
    repo_root = Path(repo_root)
    resolved_root_str = _resolved_root_str(str(repo_root))
    ignored: set[str] = set(DEFAULT_IGNORED_DIR_NAMES)
    try:
        res = subprocess.run(
            [
                "git",
                "ls-files",
                "--others",
                "--ignored",
                "--exclude-standard",
                "--directory",
                "-z",
            ],
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=False,
            check=False,
        )
        if res.returncode == 0:
            for item in res.stdout.decode("utf-8", errors="replace").split("\0"):
                clean = item.strip().rstrip("/")
                if clean:
                    ignored.add(clean)
            if _is_repository_untracked_backend(resolved_root_str):
                ignored.discard(".aw/records")
    except Exception:
        pass
    return ignored


def _resolved_root(root: Path) -> Path:
    return Path(_resolved_root_str(str(root)))


def is_ignored_path(
    path: Path,
    repo_root: Path,
    ignored_dirs: Optional[set[str]] = None,
    include_untracked: bool = False,
) -> bool:
    """Return True if path is within an ignored directory or matches ignore rules."""
    try:
        rel_path = path.relative_to(repo_root)
    except ValueError:
        try:
            rel_path = path.resolve().relative_to(_resolved_root(repo_root))
        except (ValueError, OSError):
            rel_path = Path(path.as_posix())

    rel_parts = rel_path.parts
    if any(
        p
        in (
            "tmp",
            ".tmp",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            "node_modules",
            ".venv",
            "venv",
            ".git",
        )
        for p in rel_parts
    ):
        return True

    if not include_untracked and "untracked" in rel_parts:
        return True

    rel = rel_path.as_posix()
    if ignored_dirs is None:
        ignored_dirs = get_ignored_dirs(repo_root)
    parts_list = rel.split("/")
    for i in range(1, len(parts_list) + 1):
        sub = "/".join(parts_list[:i])
        if sub in ignored_dirs:
            if include_untracked and "untracked" in sub.split("/"):
                continue
            return True
    return False


def iter_scan_files(repo_root: Path, scan_roots=SCAN_ROOTS) -> List[Path]:
    """Return every tracked-text file under the given scan roots (deterministic, sorted), skipping ignored dirs."""

    ignored_dirs = get_ignored_dirs(repo_root)
    files: List[Path] = []
    for rel in scan_roots:
        p = repo_root / rel
        if is_ignored_path(p, repo_root, ignored_dirs):
            continue
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if is_ignored_path(f, repo_root, ignored_dirs):
                    continue
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
    """A drift finding for a ``--check`` gate.

    The first three fields (``location``/``rule``/``detail``) are the original, load-bearing shape:
    every existing producer constructs ``Drift(location, rule, detail)`` positionally and every
    existing consumer reads those three attributes, so they are UNCHANGED.

    The trailing fields (agentadhere Phase 1, IPD uisjns) enrich a finding with the versioned
    policy-schema metadata WITHOUT breaking any existing caller: they are all OPTIONAL with
    defaults, so a 3-argument ``Drift(loc, rule, detail)`` still works and the tuple's first three
    positions are identical. They are populated by ``check_engine.enrich_drift`` from the rule
    registry (they default empty, so an un-enriched Drift behaves exactly as before):

    * ``observed`` / ``required`` - the observed-vs-required state (findings 7.2);
    * ``recovery`` - the exact recovery command, when one exists;
    * ``assurance`` - the Phase-0 assurance class (``guidance`` / ``repository`` / ``authority``);
    * ``determinism`` - ``deterministic`` / ``heuristic`` / ``attested`` (how the result was reached);
    * ``severity`` - ``error`` / ``warning`` / ``info``.
    """

    location: str
    rule: str
    detail: str
    observed: str = ""
    required: str = ""
    recovery: str = ""
    assurance: str = ""
    determinism: str = ""
    severity: str = ""


def render_agent_drift(drift: List[Drift]) -> str:
    """Render drift as one tab-separated ``location\\trule\\tdetail`` record per line (the D-class
    machine-readable convention). No prose."""

    return "".join(f"{d.location}\t{d.rule}\t{d.detail}\n" for d in drift)


def drift_exit_code(drift: List[Drift]) -> int:
    """The standard ``--check`` exit convention: 0 clean, 1 drift present. (2 = could-not-run is
    the caller's to return on an invocation/parse failure.)

    agentadhere Phase 1 (IPD uisjns): an ``info``-severity finding is ADVISORY (a detect-and-nudge,
    e.g. ``check.ipd-draft-ready-to-review``) and does NOT fail the gate; only error/warning-class
    findings drive the nonzero exit. A legacy 3-field ``Drift`` carries an empty ``severity`` and is
    therefore still treated as failing, so existing callers are unchanged.
    """

    return 1 if any(getattr(d, "severity", "") != "info" for d in drift) else 0

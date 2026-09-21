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
`_STATUS_RE` below, where the two readers provably disagree on 24 records.

THE CONTENT RULES READ THE METADATA REGION, NOT THE WHOLE BODY (IPD `76w6mq`). The `id6`, `setid`
and `status` rules match only within a record's leading metadata region - the bullet block before
the first `##` heading, or the leading `---` fence for a YAML-front-matter document - as computed by
`metadata_region`. This is the ARTIFACTS-NOT-MENTIONS contract (see the precedence note below)
applied to quoted METADATA specifically: a document that QUOTES an example `- Id: <id6>` block is
discussing that id6, not claiming it, so it must not resolve as it. Unbounded, such a quotation
made the REAL artifact unaddressable by every status verb via an id6 collision that `--force`
explicitly could not override."""

from __future__ import annotations

import contextlib
import functools
import os
import re
from pathlib import Path
from typing import List, NamedTuple, Optional

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
from agent_workflows import layout as _layout
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
#
# THE PER-KIND SEMANTICS ARE A CONTRACT, pinned by `tests/test_cli_find.py`
# (`ArtifactsNotReferencesTests`, `PerKindSemanticsTests`, plan 826o13 E-01): `setid` is
# deliberately MULTI-target (a Set is a group), `path`/`id6`/`stem` are `UNIQUE_KINDS` whose
# multi-match is a DATA BUG that `--force` may not override, and `substring` is the explicit last
# resort. The overarching property is ARTIFACTS, NOT REFERENCES: `find` returns the record that IS
# the selector, never one that merely mentions it, and never a differently-named Set that shares a
# prefix.
#
# A FILENAME-FIRST CANDIDATE FILTER WAS MEASURED AND DECLINED HERE (maintainer, 2026-09-11, plan
# 826o13 OQ-03). Recorded so the next reader does not re-derive a dead end. The idea was to skip
# the bounded header read for candidates whose FILENAME cannot match. Decomposition of a ~450ms
# `aw find plans <id6>`: interpreter start plus `import agent_workflows.cli` ~115ms; this resolver
# TOTAL ~42.5ms, of which TRAVERSAL is ~29.5ms and is IRREDUCIBLE by any filename filter, leaving
# ~13.4ms of header reads; the display layer's `plans_index.scan_plans` ~113.6ms, RE-READING the
# same records this resolver just read. Net saving after the filter's own `parse_clustered`
# overhead: ~12.8ms, about 3% of what an operator waits for, against a display layer 8.9x larger
# and an interpreter start 9x larger. It was declined on that basis: `resolve()` is the ONE
# resolver every verb and all ten record types route through, so the corpus-wide differential
# needed to prove such a change safe is expensive precisely BECAUSE the change is dangerous.
#
# WHERE THE REAL COST IS, so a future reader optimizes the right layer: the DISPLAY layer re-reads
# what this resolver already read (measured 1240 opens end to end against 620 here, i.e. every
# record opened about twice). That is carried by backlog `59t9x5`. Note it is not a free win
# either: `plans_index` and this module DELIBERATELY disagree on 24 records, for the reason the
# `_STATUS_RE` parity note below states at length.
#
# ONLY `id6` COULD EVER HAVE BENEFITED FROM SUCH A FILTER, which the original design missed and a
# measurement caught. Because `setid` (3) and `status` (4) are evaluated BEFORE `stem` (5) and
# `substring` (6), and both read front matter, a stem or substring query has ALREADY paid the full
# header read by the time its own rule runs. Instrumented: every kind read all candidate headers,
# `stem` and `substring` included. Filtering those kinds therefore saves nothing and costs a parse.
# Do not extend a filename filter to them.
#
# `_PRECEDENCE` IS FROZEN AS SEMANTICS, NOT AS INERTIA. A token can legitimately be BOTH a Set id
# and a filename fragment, so the order decides which record WINS an existing query; reordering it
# silently changes matching. Pinned by
# `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests`, which also proves the
# corollary that a stem or substring query cannot be made read-free while the order stands.
#
# THE PARSED FILENAME `id6` SLOT IS NOT A SAFE DISCRIMINATOR, a live trap independent of any
# filter: `parse_clustered("20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md")` returns
# CONFORMANT with `id6='assess'`, and `artifact_core.ID6_RE.match('assess')` is True, while that
# record's real declared Id is `wvlk84`. Any future filename-based matching must test the WHOLE
# filename rather than trusting the parsed slot.
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


# ----------------------------------------------------------------------------------------------
# The three directory vocabularies, DERIVED from the canonical layout model (spec `kw5y2s`, Set
# `wslayout` Order 02). `agent_workflows/layout.py` is the single source of truth for what record
# classes exist and which of them carry a status lifecycle; these names, their `frozenset` types and
# their membership are unchanged, so every importer and every parity test keeps working.
#
# THEY ARE STILL THREE SEPARATE SETS ON PURPOSE. Sourcing them from one model does NOT merge them:
# each answers a different question, and the long comments below record measured outages that
# collapsing them caused. `layout.py` preserves the distinction via `is_primary` / `is_complement` /
# `is_root_alias` plus `TRAVERSAL_EXCLUSIONS`, so the derivation is a MOVE of the definition, not a
# redefinition of the behavior.
# ----------------------------------------------------------------------------------------------

_LAYOUT = _layout.build_default_layout()

KNOWN_PRIMARY_TYPES = frozenset(_LAYOUT.primary_types())

# Record trees that are their OWN resolvable type but are NOT in `KNOWN_PRIMARY_TYPES`, so the
# `other` CATCH-ALL must not claim them.
#
# WHY THIS SET EXISTS SEPARATELY, because the obvious "just add it to KNOWN_PRIMARY_TYPES" is wrong
# and was measured to be wrong. `KNOWN_PRIMARY_TYPES` is ITERATED by `run_selection_policy`, whose
# `SPEC_TYPE_BY_RESOLVER_TYPE` table must stay in bijection with it (enforced by
# `tests/test_run_selection_policy.py::test_type_mapping_is_one_data_table_covering_the_resolver_vocabulary`),
# so an entry there is a claim that the type is a spec 25kzda 2.2 selectable WORK ITEM. A `reviews`
# record is not: it has no status lifecycle at all, which `artifact_naming.TYPE_FACET` records at
# length as the reason `reviews` is deliberately absent from THAT map too.
#
# And `EXCLUDED_RECORD_DIRS` is equally wrong for it: that set means "not a record tree, never
# enumerate" (`runs`, `scratch`, `__pycache__`), and it is consumed by
# `status_set.detect_artifact_type` to return None. A review IS a real, resolvable record - `aw find
# reviews <id6>` must keep working - it simply must not be swept into `other`.
#
# THE BUG THIS FIXES (measured 2026-09-04): with `reviews` in neither set, the `other` catch-all
# claimed every `.review.md`, so a bare id6 matched TWICE (the plan as `plans`/id6, its own review as
# `other`/substring) and `aw set approved <id6>` refused with "id6 collision ... a data bug to fix,
# not overridable by --force". It was a resolver defect, not a data bug, and it hit ALL 28 reviewed
# plans, i.e. every plan that had been through `/plan-review`.
#
# ADD A TREE HERE by marking the record class `is_primary=False` WITH a nonempty `subpath` in
# `layout.py`, when it is a legitimately resolvable record type that has no status lifecycle and
# therefore cannot join `KNOWN_PRIMARY_TYPES` without making `aw set` accept it.
NON_PRIMARY_RECORD_DIRS = frozenset(_LAYOUT.non_primary_record_dirs())

# Directories that are NOT record trees and must never be enumerated. PINNED to the current seven by
# `layout.TRAVERSAL_EXCLUSIONS`: the `kw5y2s` draft also listed `node_modules`, `venv` and `.venv`,
# and adding them is a deliberate, separately validated behavior change (its own evidence and
# regression coverage), NOT a side effect of sourcing from the model. Maintainer ruling OQ-01,
# 2026-09-03.
EXCLUDED_RECORD_DIRS = frozenset(_LAYOUT.traversal_exclusions)

# Every directory the `other` catch-all must skip: the primary typed trees, the typed-but-not-primary
# trees, and the non-record scratch dirs. `other` means "a record in the tree that no TYPE owns", so
# a directory owned by any type belongs to that type and not to `other`.
#
# THIS DERIVED UNION IS WHAT ACTUALLY GATES THE SWEEP (`record_dirs` line ~215, `_iter_paths`), not
# the three sets individually, so it MUST STAY COMPUTED from whatever those three become. Do not
# hardcode it, and do not bypass it with a fourth direct membership test: either would let the union
# drift from its inputs silently. `layout.other_sweep_skip_dirs()` computes the same union from the
# same three inputs, and `tests/test_layout.py` asserts the two agree, so a drop is caught.
#
# CONCRETELY, the member at risk is `reviews`: when it was in NEITHER the primary types nor the
# exclusions, a bare id6 matched TWICE (the plan as `plans`/id6, its own review record as
# `other`/substring) and `aw set approved <id6>` refused with "id6 collision ... a data bug to fix,
# not overridable by --force" for ALL 28 reviewed plans, until `d802e917` added the third set.
_OTHER_SWEEP_SKIP_DIRS = (
    KNOWN_PRIMARY_TYPES | NON_PRIMARY_RECORD_DIRS | EXCLUDED_RECORD_DIRS
)


@functools.lru_cache(maxsize=128)
def _record_dirs_cached(repo_root_str: str, record_type: str) -> tuple[Path, ...]:
    repo_root = Path(repo_root_str)
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
                if child.is_dir() and child.name not in _OTHER_SWEEP_SKIP_DIRS:
                    _add(child)
            with contextlib.suppress(OSError):
                if any(
                    f.is_file() and f.suffix == ".md" and f.name not in _SKIP_NAMES
                    for f in base.iterdir()
                ):
                    _add(base)
        _add(repo_root / ".aw" / "records" / "other")
        _add(repo_root / ".agents" / "other")
        return tuple(out)

    try:
        for p in _rp.resolve_record_read_paths(record_type, target_repo=repo_root_str):
            _add(p)
    except Exception:
        pass
    # Direct literal layout (covers a bare/unregistered repo, and backlog/roadmaps/releases which
    # the RecordClass resolver rejects).
    _add(repo_root / ".aw" / "records" / record_type)
    _add(repo_root / ".agents" / record_type)
    return tuple(out)


def record_dirs(repo_root: Path, record_type: str) -> List[Path]:
    """Directories to search for a record type (primary + any legacy read path).

    Combines the project-context resolver (`resolve_record_read_paths`, which honors a registered
    project/home backend) with the DIRECT literal layout under `repo_root` (`.aw/records/<type>` +
    legacy `.agents/<type>`), so this works for a bare/unregistered repo too. De-duplicated; only
    existing dirs. Returns [] for an unknown/unresolvable type rather than raising.
    """
    return list(_record_dirs_cached(str(repo_root), record_type))


# --- THE THREE CONTENT READERS ARE BOUNDED TO THE METADATA REGION (IPD `76w6mq`) ---------------
#
# All three consult `metadata_region(text)`, NOT the whole text, and the bounding is what makes a
# quotation a quotation. Unbounded, ANY `- Id: <id6>` line anywhere in a document claimed that
# document's identity, so a file QUOTING an example metadata block was read as ASSERTING the quoted
# id6 - which collided with the real artifact and made it UNADDRESSABLE by every status verb, with
# the refusal explicitly stating it was "not overridable by --force". The trigger was ordinary prose
# (quoting the metadata format), so the documents most likely to break the tool were the specs and
# research ABOUT `aw` itself.
#
# ALL THREE, not just id: measured before the fix, the two quoting research documents also reported
# `- Status: reviewed` and `- Set: runflags` from the quoted block instead of their own YAML values,
# which is the same defect producing a wrong `aw find <status>`/`aw find <setid>` answer rather than
# a visible collision.
#
# WHAT "FIXED" LOOKS LIKE FOR A YAML-FENCED RECORD IS `None`, NOT THE DOCUMENT'S OWN VALUE, and an
# executor expecting the latter will think this regressed. These patterns speak only the BULLET
# dialect, and a YAML region contains no `^- Id:`/`^- Status:`/`^- Set:` lines at all, so a research
# doc's three readers now return None. That stops the false claim without inventing a true one;
# teaching the readers the YAML dialect is a separate change (plan `xo3244`), deliberately not made
# here. See the FRONT-MATTER DIALECT note in the module docstring.
def _read_id(text: str) -> str | None:
    m = _ID_RE.search(metadata_region(text))
    return m.group(1) if m else None


def _read_status(text: str) -> str | None:
    m = _STATUS_RE.search(metadata_region(text))
    return m.group(1) if m else None


# --- Public front-matter readers (rununify 01, `2r306y`) --------------------------------------
#
# The PUBLIC, documented form of the two readers above, for callers OUTSIDE this module. Both
# host runners used to carry their own private `_read_id`/`_read_status` copies; they now call
# these, so there is ONE definition per reader and a fix reaches both drivers.
#
# THEY DELIBERATELY USE A LOOSER PATTERN THAN THIS MODULE'S OWN READERS, and that is the whole
# design of this pair rather than an oversight. The runner copies were AST-IDENTICAL in body to
# `_read_id`/`_read_status` but closed over `^-\s*Id:` (ANY whitespace after the dash) where
# `_ID_RE`/`_STATUS_RE` above require EXACTLY ONE SPACE. So a literal swap to the strict readers
# would have made both drivers stop recognizing a bullet written `-  Id: abc123` or with a tab.
#
# Widening `_ID_RE`/`_STATUS_RE` instead was NOT an option: the PARITY CONSTRAINT comment above
# records that `_STATUS_RE`'s strictness is a MATCHING-BEHAVIOR CONTRACT for `aw find plans`,
# deliberately disagreeing with `plans_index._META_RE` on 24 records. Harmonizing them is a
# contract change, not a cleanup. Hence a separate permissive pattern here, leaving selector
# matching byte-for-byte unchanged.
#
# The permissive spelling is also the one the WRITER uses: `status_set.py:132-133`, which is what
# actually rewrites these bullets, matches on `^-\s*Id:`/`^-\s*Status:`, as do
# `check_engine`/`backlog`/`research_index` (via `[ \t]*`). Tolerating the loose form on READ is
# therefore consistent with the rest of the toolkit, and it fails safe: a missed `- Status:` read
# silently degrades a runner to a directory-derived status (`oc_runipd.parse_plan_file`), which
# is precisely the class of silent wrongness this Set exists to remove.
#
# THIS PAIR IS REGION-BOUNDED TOO, AND THAT IS THE POINT OF CONSOLIDATING RATHER THAN FIXING ONE
# SIDE (IPD `76w6mq` E-03, OQ-02). What is shared is the metadata-region BOUND; what stays distinct
# is the WHITESPACE tolerance above. Bounding only the strict internal pair would deliberately
# reinstate, in this very module, the reader DRIFT whose prevention is the documented reason this
# public pair exists at all: both host runners previously carried private `_read_id`/`_read_status`
# copies that diverged. A driver reads PLAN front matter, where the region boundary is unambiguous
# (a bullet block before `## Workflow history`), so bounding is behavior-preserving for every real
# driver input; measured over all 1614 tracked records, exactly ONE file's public-reader answer
# changes, and it is one of the two quoting research documents this plan exists to fix.
#
# The header-exhaustion rule in `metadata_region` matters HERE in particular: a driver reading a
# long plan whose metadata block outruns one read chunk must not lose its region to a missing `##`,
# which is why exhaustion means "the region continues" and never an empty region.
_FRONT_MATTER_ID_RE = re.compile(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$")
_FRONT_MATTER_STATUS_RE = re.compile(r"(?m)^-\s*Status:\s*(\S+)\s*$")


def read_front_matter_id(text: str) -> str | None:
    """Return the `- Id:` id6 from a record's METADATA REGION, or ``None``.

    Tolerates any whitespace after the leading dash (see the note above). For SELECTOR
    matching use the strict internal reader instead, so `aw find` behavior is unchanged.
    Bounded to `metadata_region`, so a QUOTED `- Id:` in a body is not read as a declaration.
    """
    m = _FRONT_MATTER_ID_RE.search(metadata_region(text))
    return m.group(1) if m else None


def read_front_matter_status(text: str) -> str | None:
    """Return the single-token `- Status:` value from a record's METADATA REGION, or ``None``.

    A multi-word status (e.g. ``EXECUTED (approved ...)``) yields ``None``, matching the
    internal reader's `(\\S+)` contract; only the leading whitespace tolerance differs.
    Bounded to `metadata_region`, like its `read_front_matter_id` twin.
    """
    m = _FRONT_MATTER_STATUS_RE.search(metadata_region(text))
    return m.group(1) if m else None


# THIS READER RETURNS THE `- Set:` TOKEN VERBATIM, INCLUDING ANY QUOTING CHARACTERS, AND THAT IS
# PINNED RATHER THAN AN OVERSIGHT (plan 826o13 E-04,
# `tests/test_cli_find.py::BacktickSetValueIsPinnedTests`). A record whose front matter reads
# `- Set: `awoptimize`` yields the BACKTICK-BEARING string, so it does NOT match the `setid` rule
# and is reached by `substring` instead. Stripping the backticks here would make it newly match
# `setid`, and `setid` (precedence 3) OUTRANKS `substring` (6), so the winning KIND flips and the
# answer SHRINKS: measured, `aw find research awoptimize` returns FOUR files by substring today and
# ONE by setid after such a normalization. That is a MATCHING-BEHAVIOR change of the same class as
# the `_STATUS_RE` parity constraint above, so the fix belongs at plan `3i6rso`'s report-only
# comparison site, where it changes no selector answer, and NOT here.
def _read_setid(text: str) -> str | None:
    m = _SET_RE.search(metadata_region(text))
    if not m:
        return None
    # The set-id is the first whitespace token before any '(' (mirrors plans_index.set_terse_id).
    return m.group(1).split("(")[0].strip().split()[0] if m.group(1).strip() else None


# PERF (awfindperf): selector matching only ever consults the front-matter bullets
# (`- Id:`, `- Status:`, `- Set:`) via _read_id/_read_status/_read_setid, which live in the
# metadata block at the top of a record. Reading whole files (some are multi-hundred-KB
# records) dominated `aw find`, so we read a bounded prefix instead.
#
# THE CHUNK IS A READ QUANTUM, NOT A CAP, AND THAT DISTINCTION IS THE WHOLE BUG FIX.
# This was `_HEADER_BYTES = 4096` used as a HARD CAP: one 4096-byte read, and any bullet past
# that byte offset was INVISIBLE. That is not a hypothetical. Measured 2026-09-19 on this repo:
# 72 plans carry `- Set:`/`- Id:`/`- Status:` past byte 4096, the worst at 9769, because a long
# `- Concern:` or `- Scope:` paragraph precedes them in the SAME metadata block. The failure was
# SILENT AND SUBTRACTIVE: `selectors.resolve` returned a SMALLER match set rather than an error,
# so a setid resolved to some of its members and nothing reported the shortfall.
#
# THE CONCRETE INCIDENT THIS FIX CLOSES: Set `runnoop`'s children `m85gxh` (`- Set:` at byte
# 5313) and `bsc457` (5731) were invisible to `resolve(..., MATCH_SETID)`, so
# `read_set_membership` saw ONE child instead of three, and `evaluate_set_retirement` refused
# the orchestrator `7ewc74` with `unauthored-child-rows` for rows `02`/`03` that were sitting on
# disk, `executed`, all along. A parent that can never retire, from a truncated read.
#
# WHY SCANNING TO THE END OF THE METADATA BLOCK IS THE RIGHT BOUND rather than a bigger number:
# any fixed cap is the same bug with a higher threshold, and the corpus grows. The block ends at
# the first line that is neither a `- ` bullet, nor a continuation line indented under one, nor
# blank, nor the leading `# ` title (in practice the first `## ` heading). That is a STRUCTURAL
# bound, so it cannot be outgrown. We still never page in a record BODY: reading stops at the
# first heading, which for these records is within a few KB even when the metadata is long.
_HEADER_CHUNK_BYTES = 4096
# Stop growing the prefix at some point even if a pathological file never presents a heading, so
# a malformed record cannot make this read an entire multi-hundred-KB body. Chosen an order of
# magnitude above the largest real metadata block measured here (9769 bytes).
_HEADER_MAX_BYTES = 262144

_METADATA_END_RE = re.compile(r"(?m)^#{2,}\s")


def _metadata_region_complete(chunk: str) -> bool:
    """True when `chunk` provably contains the WHOLE metadata block.

    The block is terminated by the first `##`+ heading (records open with a single `# ` title,
    then the `- Key: value` bullets, then `## Workflow history` or another section). Seeing such a
    heading means every bullet that exists is already in `chunk`, so no further read can add one.
    """

    return _METADATA_END_RE.search(chunk) is not None


# A YAML-fenced document's metadata region is its LEADING `---` block, not "everything before the
# first `##`". The distinction is not cosmetic: measured on this corpus, exactly one record
# (`effzzi`, a roadmap) opens with a YAML fence and then carries `- Key: value` BODY PROSE bullets
# under its H1 (`- Plans: one orchestrator plus eight children`, `- Authoring state: ...`) before
# its first `## ` heading. Those bullets are narrative, not metadata, and the fence is the record's
# real declaration site, so the fence is where the region ends.
_YAML_FENCE_OPEN_RE = re.compile(r"\A---[ \t]*\r?\n")
_YAML_FENCE_CLOSE_RE = re.compile(r"(?m)^---[ \t]*\r?$")


def metadata_region(text: str) -> str:
    """Return the leading METADATA REGION of a record: where it DECLARES its own identity.

    This is the ONE boundary every identity/status/setid reader in the toolkit is bounded to, so a
    document that merely QUOTES a metadata block (which is ordinary, legitimate prose in a
    repository that documents its own metadata format) cannot be read as ASSERTING the quoted
    values. Identity comes from where an artifact declares it, not from anywhere the pattern
    happens to match.

    Two shapes, because both are present in the corpus:

    * BULLET front matter (plans, specs, backlog, releases, reviews, prompts, walkthroughs): the
      region is everything before the first ``##``+ heading. A leading ``# `` H1 title does NOT
      end it - the boundary is ``##``, not ``#`` - so a title-then-bullets file keeps its whole
      bullet block.
    * YAML front matter (research, roadmaps): the region is the leading ``---`` fence block ONLY,
      ending at its closing fence. See the note above `_YAML_FENCE_OPEN_RE` for the measured record
      that makes this stricter bound the correct one rather than a refinement.

    HEADER EXHAUSTION MEANS "THE REGION CONTINUES", NEVER AN ERROR AND NEVER AN EMPTY REGION, and
    this is the case most likely to be got wrong because it is COMMON rather than exotic. Callers
    pass a BOUNDED header read (`_read_header`), not a whole file, so the terminator may simply lie
    past the end of the window: measured on this repo, 25 of 1614 tracked records present no ``##``
    heading inside that window at all. For them "everything before the first ``##``" legitimately
    means the WHOLE window, and a helper that returned empty, raised, or refused would break
    identity extraction for 25 records while fixing 2. The same rule covers a truncated YAML fence:
    an unterminated leading fence yields the whole input.
    """

    if not text:
        return text or ""
    m_open = _YAML_FENCE_OPEN_RE.match(text)
    if m_open is not None:
        m_close = _YAML_FENCE_CLOSE_RE.search(text, m_open.end())
        if m_close is None:
            return text  # fence unterminated within the input -> the region continues
        return text[: m_close.end()]
    m_end = _METADATA_END_RE.search(text)
    if m_end is None:
        return text  # no `##` in the input -> the region continues (the common 25-record case)
    return text[: m_end.start()]


def _read_header(p: Path) -> str | None:
    """Read enough of a record to contain its entire metadata block; None if unreadable.

    Reads in `_HEADER_CHUNK_BYTES` steps and stops as soon as the metadata region is provably
    complete (a `##` heading has been seen), at EOF, or at `_HEADER_MAX_BYTES`. The common case
    costs exactly one read, identical to the previous behavior; only a record whose metadata
    block is genuinely longer than one chunk pays for a second.

    Returning a SHORT read is what silently broke setid/status resolution for 72 plans (see the
    note above), so the bound here is structural rather than a byte count.
    """
    try:
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            chunk = fh.read(_HEADER_CHUNK_BYTES)
            if not chunk:
                return chunk
            while (
                not _metadata_region_complete(chunk) and len(chunk) < _HEADER_MAX_BYTES
            ):
                more = fh.read(_HEADER_CHUNK_BYTES)
                if not more:
                    break
                chunk += more
            return chunk
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
        # Owned by a TYPE (primary or typed-but-not-primary, e.g. `reviews`) -> not `other`.
        known_dirs = {
            d.resolve()
            for rt in KNOWN_PRIMARY_TYPES | NON_PRIMARY_RECORD_DIRS
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


# ----------------------------------------------------------------------------------------------
# IDENTITY OWNERSHIP FOR ONE ALREADY-MATCHED ROW (IPD paw8so E-06 / E-01).
#
# WHY THIS IS NOT `Resolution.kind`, WHICH IS THE ONE THING A READER OF THIS FILE WILL ASSUME.
# `resolve` carries a `kind`, and for the common case it does separate declaration (`id6`) from
# filename reference (`substring`). The CONVERSE DOES NOT HOLD: `kind == MATCH_SUBSTRING` means
# "not proven to declare", NOT "is a reference". Two independent reasons, one historical and one
# still live:
#
#   * HISTORICAL, and the reason this predicate was specified: `_read_header` was once a HARD
#     4096-byte CAP, so a `- Id:` bullet sitting past it was invisible and its OWNER resolved as
#     `substring`. Measured at this plan's review (2026-09-10): 63 of 608 declaring plans, 52 of
#     them producing a multi-row `aw find`. That cap became a structural bound on 2026-09-19 (see
#     `_HEADER_CHUNK_BYTES`), and re-measured 2026-09-21 the population is ZERO of 702 plans.
#   * STILL LIVE: `_HEADER_MAX_BYTES` remains a hard stop, so a record whose metadata block
#     outruns 256KB still reads as `substring` while genuinely declaring the id6. Reproduced.
#
# So a surface that must decide "is this row the OWNER or a mere mention" reads THAT ONE ROW's
# declaration directly, and never infers ownership from a bounded read. It is affordable precisely
# because it runs over rows ALREADY MATCHED (typically 1 to 3), never over the corpus.
#
# DO NOT "FIX" THIS BY WIDENING THE WINDOW (IPD paw8so OQ-04). Raising the byte bounds or routing
# `resolve`'s id6 rule through a whole-file read would change which records `aw find` MATCHES for
# every type and every front-matter kind, which the `_STATUS_RE` parity note above establishes is a
# MATCHING-BEHAVIOR decision and not a cleanup. This predicate cannot change what matches at all.
def declares_id6(path: Path, id6: str) -> bool:
    """True iff the file at ``path`` DECLARES ``id6`` as its own identity.

    Reads the WHOLE file and bounds the search to `metadata_region`, so a QUOTED example
    ``- Id:`` block in a body is not read as a declaration (the same ARTIFACTS-NOT-MENTIONS rule
    the selector readers apply, just without the byte bound). Reuses the module's own `_ID_RE`
    rather than adding a third identity pattern; `plans_index._meta(text, "Id")` and
    `check_engine._ID_LINE_RE` are byte-identical twins of it.

    Returns False (never raises) for an unreadable file.
    """

    if not id6 or not _core.ID6_RE.match(id6):
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return _read_id(text) == id6


def declared_id6(path: Path) -> Optional[str]:
    """Return the id6 the file at ``path`` declares in its metadata region, or ``None``.

    The whole-file twin of `_read_id`; see `declares_id6` for why a bounded read is not
    sufficient for an ownership verdict.
    """

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return _read_id(text)


# A LEGACY NAME'S PARSED SLOT IS NOT AN id6, AND `ID6_RE` ALONE CANNOT TELL YOU THAT. The trap is
# recorded above `MATCH_PATH` and it is live: `parse_clustered` reports CONFORMANT with
# `id6='assess'` for `20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md`, and
# `ID6_RE.match('assess')` is True, while that record's real declared Id is `wvlk84`. Trusting the
# slot shape alone would therefore manufacture identity claims out of ordinary slug words.
#
# THE DISCRIMINATOR IS THE REPOSITORY'S EXISTING ORACLE, reused rather than re-derived: a slot token
# is a real id6 if it visibly MIXES digits and letters (a slug word like `assess`/`agents` is
# all-letters). This mirrors `check_engine._is_real_id6`, whose other arm (membership in the set of
# all declared ids) needs a corpus-wide inventory that a lookup deliberately does not build; the
# digit test is the half that works per-row. The cost of the missing arm is a FALSE NEGATIVE on an
# all-letter real id6, which is the safe direction for a warning.
_HAS_DIGIT_RE = re.compile(r"\d")


def filename_slot_id6(path: Path) -> Optional[str]:
    """Return the id6 occupying ``path``'s FILENAME IDENTITY SLOT, or ``None``.

    Only a CANONICAL clustered name has such a slot (`YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`),
    and the slot token must be a REAL id6 rather than a legacy name's slug word (see the note
    above). A legacy `YYYYMMDD-HHMM-NN-<slug>` name yields ``None``.
    """

    m = _naming.parse_clustered(path.name)
    if m is None:
        return None
    slot = m.groupdict().get("id6")
    if not slot or not _core.ID6_RE.match(slot):
        return None
    if not _HAS_DIGIT_RE.search(slot):
        return None
    return slot


# The four ownership verdicts for one already-matched row, under D140's identity-versus-reference
# distinction (`DECISIONS.md:2465`, "an artifact MUST NOT place another artifact's id6 in its own
# identity slot"; "id6/setid citations elsewhere remain stable references").
OWNERSHIP_DECLARED = "declared"  # the file's own `- Id:` IS this id6
OWNERSHIP_SLOT_ONLY = (
    "slot-only"  # the id6 sits in the filename identity slot, no `- Id:` declared
)
OWNERSHIP_REFERENCE = (
    "reference"  # the id6 appears only as a reference (not an identity claim)
)
OWNERSHIP_FOREIGN_ID = "foreign-id"  # the file declares a DIFFERENT id6 of its own

# The ownership verdicts that constitute an IDENTITY CLAIM on the id6. Two files both claiming is a
# collision; one claiming plus any number of references is the normal, correct state.
CLAIMING_OWNERSHIPS = frozenset({OWNERSHIP_DECLARED, OWNERSHIP_SLOT_ONLY})


def id6_ownership(path: Path, id6: str) -> str:
    """Classify how the file at ``path`` relates to ``id6``: one of the OWNERSHIP_* verdicts.

    THE VERDICT IS KEYED ON DECLARATION, NOT ON RECORD TYPE, and that is deliberate rather than
    incidental. A REVIEW record carries its SUBJECT's id6 in its filename identity slot BY
    DOCUMENTED DESIGN (`.aw/records/reviews/README.md`: "`<id6>` is the REVIEWED ARTIFACT's id6,
    not a fresh identifier ... so the join survives a rename"), and measured 2026-09-21 all 257
    review records in this repository declare a `- Subject-Id:` and NO own `- Id:`. A rule that
    suppressed the `reviews` TYPE would be an exception list that breaks the moment another type
    adopts the same convention; a rule keyed on DECLARATION has reviews fall out silently as a
    consequence, and covers `comms`/`other` too, which `check_engine.SUPPORTED` does not.

    THAT IS WHY `slot-only` IS A CLAIM WHILE A REVIEW IS NOT, EVEN THOUGH BOTH CARRY A FOREIGN
    id6 IN THE SLOT. The discriminator is the TYPED SUBJECT FIELD: a record that names its subject
    with `- Subject-Id:`/`- Target-Id:`/`- References:` is expressing exactly the typed reference
    D140 prescribes, so its slot is a documented JOIN and not an identity claim. A file with a
    foreign id6 in its slot, no `- Id:` of its own, and NO typed subject field is the p7dqwz shape
    D140 was written about, and it is the one that must be reported.
    """

    declared = declared_id6(path)
    if declared == id6:
        return OWNERSHIP_DECLARED
    if declared is not None:
        return OWNERSHIP_FOREIGN_ID
    if filename_slot_id6(path) == id6 and not _declares_typed_subject(path, id6):
        return OWNERSHIP_SLOT_ONLY
    return OWNERSHIP_REFERENCE


# The TYPED reference fields D140 prescribes for pointing at another artifact
# ("expresses that link as a TYPED frontmatter field (e.g. `Target-Id:`/`References: <id6>`)").
# `Subject-Id` is the reviews tree's spelling of the same idea.
_TYPED_SUBJECT_RE = re.compile(
    r"(?m)^-\s*(?:Subject-Id|Target-Id|References|From-Backlog|From-Spec|Reviewed-Id)"
    r":\s*([0-9a-z]{6})\s*$"
)


def _declares_typed_subject(path: Path, id6: str) -> bool:
    """True iff the file names ``id6`` through a TYPED reference field in its metadata region."""

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    region = metadata_region(text)
    return any(m.group(1) == id6 for m in _TYPED_SUBJECT_RE.finditer(region))


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

    THIS SHIM DROPS THE AMBIGUITY VERDICT, AND THAT IS WHAT LEFT THE READ SURFACES SILENT (IPD
    paw8so). It returns `.paths` only, so the `kind` that `resolve_for_mutation` acts on - the
    `UNIQUE_KINDS` policy under which an id6 matching several files is "a data bug to fix, not
    overridable by --force" - never reaches a read caller. `aw find` consequently rendered a
    corrupt identity as an unremarkable multi-result list at exit 0 for as long as it routed
    through here. Do NOT reuse this shim for a NEW read path in the belief that it carries the
    policy: call `resolve` and inspect `Resolution.kind`, and for an OWNERSHIP question use
    `id6_ownership`, which is reliable where `kind` is only indicative.
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

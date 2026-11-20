"""Shared selector resolver: turn selector tokens (direct path | id6 | setid | status | bare stem |
filename fragment) into concrete record file paths for a record type. Pure (no CLI, no writes).

This module is the ONE selector-to-file resolver for the whole package (IPD laykok, unifyfileio
Order 02): every verb (`rename`, `group`, `set`/`ipd set`/`spec set`/`backlog set`, `show`, `find`,
`archive`, and the per-area set-assign/mv paths) routes selector resolution through `resolve()` here,
so the SAME selector resolves to the SAME file for every verb (or yields one uniform no-match /
ambiguous-match result). Per the orchestrator's module-placement principle, this resolver MAY import
the Order 01 naming authority (for bare-stem parsing); the naming authority never imports this.

FRONT-MATTER DIALECT: THE CONTENT READERS SPEAK BOTH DIALECTS, BULLET FIRST (IPD `xo3244`, which
REVERSED the deliberate exclusion IPD e32j35 E-06 had documented here). The corpus holds two
declaration shapes, and the id6/setid/status rules now read either:

  * BULLET front matter (`- Id:`, `- Status:`, `- Set:`), used by plans, specs, backlog, releases,
    reviews, prompts and walkthroughs; matched by `_ID_RE`/`_STATUS_RE`/`_SET_RE`;
  * YAML front matter (`id:`, `status:`, `set:` between `---` fences), used by research and roadmaps;
    read via `research_contract.parse_frontmatter`, the repository's ONE parser for that block.

Each reader tries its BULLET pattern first and consults the YAML fence only ON A MISS, so no record
that matches today changes its answer, and the fallback only supplies a value where there previously
was `None`.

WHY THE EXCLUSION WAS REVERSED, since the prose it replaced argued the opposite at length. Speaking
only the bullet dialect did not make research resolution CONSERVATIVE, it made it SILENTLY WRONG:
the three content rules could never fire for a research document, so every research query fell
through to `MATCH_SUBSTRING`, the explicit LAST-RESORT FILENAME rule, and returned a plausible short
list with nothing signalling that metadata was never consulted. Measured before the change,
`aw find research reference` returned 5 records while 64 documents carried `status: reference`; two
records with identical metadata resolved differently based only on which dialect their TYPE happens
to use. The order-of-magnitude widening this fixes is real and was accepted deliberately by the
maintainer, INCLUDING on the mutating `aw archive` verb (see `CHANGELOG.md`); it is a semantic
change, which is why it took its own plan rather than riding along with a resolver-cost change.

THE YAML READER IS DELIBERATELY NARROW IN TWO WAYS, and both are load-bearing. The key lookup is
CASE-SENSITIVE, which is what leaves the `---`-fenced records outside research (the `handoff`
workflow writes `Kind:`/`Status:` CAPITALIZED) completely unperturbed. And the PUBLIC runner-facing
readers below (`read_front_matter_id`/`read_front_matter_status`) stay bullet-only. See the notes at
each site.

Note the separate, still-standing caution about the PLANS index, which this change does not touch:
see the parity note on `_STATUS_RE` below, where the two readers provably disagree on 24 records.

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
import os
import re
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
from agent_workflows import layout
from agent_workflows import record_producers as _rp

_SKIP_NAMES = layout.RECORD_SCAN_SKIP_NAMES

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
# WHERE THE REAL COST IS, so a future reader optimizes the right layer: the DISPLAY layer previously
# re-read what this resolver already read (measured 1240 opens end to end against 620 here, i.e. every
# record opened about twice); that double read was removed by IPD `qfpnrm` (source backlog `59t9x5`).
# Note it was not a free win either: `plans_index` and this module DELIBERATELY disagree on 24 records,
# for the reason the `_STATUS_RE` parity note below states at length.
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
# silently changes matching. Formerly pinned by
# `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests` (deleted in `19313eed`);
# guarded behaviorally by `tests/test_selector_precedence_outcomes.py`, which also preserves the
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

_LAYOUT = layout.build_default_layout()

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

    from agent_workflows.project_context import (
        project_records_dir,
        has_stored_records_placement,
    )

    rec_root = project_records_dir(repo_root)

    if record_type == "other":
        for base in (rec_root, repo_root / ".agents"):
            if not base.is_dir():
                continue
            for child in base.iterdir():
                if (
                    child.is_dir()
                    and child.name not in _OTHER_SWEEP_SKIP_DIRS
                    and child.name not in layout.RECORD_SCAN_EXCLUDED_DIRS
                ):
                    _add(child)
            with contextlib.suppress(OSError):
                if any(
                    f.is_file() and f.suffix == ".md" and f.name not in _SKIP_NAMES
                    for f in base.iterdir()
                ):
                    _add(base)
        _add(rec_root / "other")
        _add(repo_root / ".agents" / "other")
        return tuple(out)

    if has_stored_records_placement(repo_root):
        _add(rec_root / record_type)
    else:
        try:
            for p in _rp.resolve_record_read_paths(
                record_type, target_repo=repo_root_str
            ):
                _add(p)
        except Exception:
            pass
    # Direct literal layout (covers a bare/unregistered repo, and backlog/roadmaps/releases which
    # the RecordClass resolver rejects).
    _add(rec_root / record_type)
    _add(repo_root / ".agents" / record_type)
    if record_type == "research":
        # Research-specific legacy nesting: record_producers._LEGACY_RECORD_CLASS_SUBPATHS["research"] == "docs/research"
        # is the authority for the subpath and research_contract.resolve_research_root is the authority that research reads it.
        _add(repo_root / ".agents" / "docs" / "research")
    return tuple(out)


# Compatibility no-op: callers/tests that previously cleared the stale lru_cache still find it.
_record_dirs_cached.cache_clear = lambda: None  # type: ignore[attr-defined]


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
# --- THE YAML DIALECT READER (IPD `xo3244`) ----------------------------------------------------
#
# The three readers below speak TWO dialects, because the corpus holds two. Plans, specs, backlog,
# releases, reviews, prompts and walkthroughs declare `- Key: value` BULLETS; research and roadmaps
# declare `key: value` inside a leading `---` fence. Before this, the readers spoke only the bullet
# dialect, so for research the id6/setid/status rules could never fire and EVERY research query fell
# through to the last-resort FILENAME rule - silently, with a plausible short answer rather than an
# error (measured: `aw find research reference` returned 5 while 64 documents carry
# `status: reference`).
#
# THE PARSE IS DELEGATED, NEVER REIMPLEMENTED. `research_contract.parse_frontmatter` is the
# repository's one YAML-front-matter reader (`research_index._scan_docs` is its other consumer), and
# a second reader here would drift from it about what counts as valid front matter. The import is
# LAZY: this module is imported by many surfaces and `research_contract` is a heavier module that
# only this fallback needs, so the cost is paid by the records that actually take the branch.
#
# THE KEY LOOKUP IS CASE-SENSITIVE, AND THAT IS THE LOAD-BEARING SAFETY PROPERTY OF THIS CHANGE, NOT
# A STYLISTIC RESTRICTION. `parse_frontmatter` preserves keys VERBATIM (`key.strip()`, no case
# folding), and the `---`-fenced records that exist OUTSIDE research are written by the `handoff`
# workflow with CAPITALIZED keys (`Kind:`, `Status:`, `Date:`). Looking up exactly `id`/`status`/`set`
# therefore returns None for them, leaving every non-research type's resolution untouched. A
# tolerant lookup (`.title()`, case folding, or trying variants) would silently make
# `aw find prompts draft` start matching session-handoff drafts, so DO NOT "robustify" this: the
# no-perturbation proof for the other nine record types rests on it.
_YAML_KEYS = ("id", "status", "set")


def _normalize_yaml_scalar(value: str) -> str:
    """Strip surrounding backticks / matching quote pairs from a YAML scalar before comparing.

    A DEFENSIVE GUARD, HONESTLY LABELLED: a `set:` value written `` `awoptimize` `` was observed in
    this corpus during an earlier session and would compare as a phantom mismatch, but re-measured
    over all 119 parsable research documents at execution time, ZERO front-matter values carry a
    backtick or a stray quote. So this fixes no live defect; it keeps one from reappearing.

    It applies ONLY to the YAML dialect. The BULLET `_read_setid` deliberately returns a backticked
    value VERBATIM, which `tests/test_cli_find.py::BacktickSetValueIsPinnedTests` pins because
    normalizing there flips a real query's winning KIND (4 substring hits become 1 setid hit).
    """

    out = value.strip()
    while len(out) >= 2 and out[0] == out[-1] and out[0] in "`\"'":
        out = out[1:-1].strip()
    return out


def _read_yaml_scalar(text: str, key: str) -> str | None:
    """Return the normalized scalar for `key` from `text`'s leading YAML fence, or ``None``."""

    if not text.startswith("---"):
        return None
    from agent_workflows import artifact_meta as _meta

    st = _meta.read_text(text)
    if key == "id":
        return st.id6 or None
    if key == "status":
        return st.legacy_raw_status
    if key == "set":
        return st.legacy_raw_set
    val = st.fields.get(key.lower().replace("-", "_"))
    return val or None if isinstance(val, str) else None


def _is_yaml_front_matter(text: str) -> bool:
    return bool(text and text.startswith("---"))


def _read_id(text: str) -> str | None:
    from agent_workflows import artifact_meta as _meta

    region = metadata_region(text)
    st = _meta.read_text(region)
    if not st.id6:
        return None
    # YAML fallback accepts any non-empty normalized lowercase id scalar;
    # bullet strict reader requires exact 6-char id6 matching the whole value.
    if _is_yaml_front_matter(region) and st.loose_id is None and "id" in st.fields:
        return st.id6
    if _core.ID6_RE.fullmatch(st.id6) and st.fields.get("id") == st.id6:
        return st.id6
    return None


def _read_status(text: str) -> str | None:
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import plans as _plans

    st = _meta.read_text(metadata_region(text))
    raw = st.legacy_raw_status
    if not raw:
        return None
    toks = raw.split()
    if len(toks) > 1:
        return _plans.normalize_status(toks[0])
    return toks[0]


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
# The permissive spelling is also the one the WRITER uses: `status_set`'s `_ID_RE`/`_STATUS_RE`, which is what
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
#
# THIS PAIR IS DELIBERATELY LEFT BULLET-ONLY, AND ITS OMISSION FROM THE YAML DIALECT IS A DECISION
# RATHER THAN AN OVERSIGHT (IPD `xo3244` E-03). The three INTERNAL readers above now fall back to the
# YAML dialect; these two do not. Two reasons. FIRST, no caller can produce the input: a host runner
# reads PLAN front matter, which is bullet-dialect by construction, so a YAML branch here would widen
# a surface nothing exercises. SECOND, and decisively, this is the ONE reader pair whose failure mode
# is documented as SILENTLY DEGRADING a runner to a directory-derived status, so its surface is kept
# as narrow as its callers need. If a driver ever has to read a YAML-fenced record, add the fallback
# HERE explicitly with its own evidence; do not infer it from the internal readers having one.
def read_front_matter_id(text: str) -> str | None:
    """Return the `- Id:` id6 from a record's METADATA REGION, or ``None``.

    Tolerates any whitespace after the leading dash (see the note above). For SELECTOR
    matching use the strict internal reader instead, so `aw find` behavior is unchanged.
    Bounded to `metadata_region`, so a QUOTED `- Id:` in a body is not read as a declaration.
    """
    from agent_workflows import artifact_meta as _meta

    return _meta.read_text(metadata_region(text)).loose_id


def read_front_matter_status(text: str) -> str | None:
    """Return the single-token `- Status:` value from a record's METADATA REGION, or ``None``.

    A multi-word status (e.g. ``EXECUTED (approved ...)``) yields ``None``, matching the
    internal reader's `(\\S+)` contract; only the leading whitespace tolerance differs.
    Bounded to `metadata_region`, like its `read_front_matter_id` twin.
    """
    from agent_workflows import artifact_meta as _meta

    return _meta.read_text(metadata_region(text)).loose_status


def read_front_matter_blocks_release(text: str) -> str | None:
    """Return the `- Blocks-Release:` value from a record's METADATA REGION, or ``None``.

    The value is a release id6 or the literal `next`. Note that `-` means ABSENT at every
    consumer. Bounded to `metadata_region`, like `read_front_matter_id` and
    `read_front_matter_status`, so a QUOTED `- Blocks-Release:` in a body is not read
    as a declaration.
    """
    from agent_workflows import artifact_meta as _meta

    return _meta.read_text(metadata_region(text)).loose_blocks_release


def _read_setid(text: str) -> str | None:
    from agent_workflows import artifact_meta as _meta

    return _meta.read_text(metadata_region(text)).legacy_raw_set


def _first_set_token(value: str) -> str | None:
    """The terse set-id: the first whitespace token before any '(' (mirrors plans_index)."""

    return value.split("(")[0].strip().split()[0] if value.strip() else None


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


def metadata_region(text: str) -> str:
    """Return the leading METADATA REGION of a record: where it DECLARES its own identity."""

    if not text:
        return text or ""
    m_open = _YAML_FENCE_OPEN_RE.match(text)
    if m_open is not None:
        pos = m_open.end()
        for line in text[pos:].splitlines(keepends=True):
            stripped = line.rstrip("\r\n")
            pos += len(line)
            if stripped.rstrip(" \t") == "---":
                return text[: pos - (len(line) - len(stripped))]
        return text  # fence unterminated within the input -> the region continues
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


# READ-ONLY SCAN SCOPE. `resolve` walks the records tree and reads every record header on EACH call.
# That is right for one lookup and badly wrong for a command that makes thousands: measured
# 2026-11-11, `aw partition -t plan` over the 209-plan metastore Set called `resolve` 1,451 times
# (once per dependency edge) and spent 530 of its 539 seconds re-walking and re-reading the same
# files (2.8 million reads, 25 million `lstat` calls). Inside `scan_once()`, `resolve` builds the
# candidate list and the header reads ONCE per (repo, record type, traversal settings) and reuses
# them. ONLY for commands that do not change records while the scope is open: a record written
# inside the scope is not seen by a later lookup in the same scope.
_SCAN_CACHE: Optional[
    Dict[
        Tuple[str, str, bool, Optional[int]],
        Tuple[List[Path], Optional[List[Tuple[Path, str]]]],
    ]
] = None
# Declared `- Id:` -> paths, built once per scan key inside `scan_once()` (lives and dies with it).
_SCAN_ID_INDEX: Dict[Tuple[str, str, bool, Optional[int]], Dict[str, List[Path]]] = {}
# Shared per-scope read-only cache for sibling modules (review_findings, check_engine) that run
# inside `scan_once()`. Cleared automatically on `drop_scan()` and when the outer scope exits.
_SCAN_EXTRAS: Optional[Dict[Any, Any]] = None


def current_scan_cache() -> Optional[Dict[Any, Any]]:
    """Return the active `scan_once()` read-only cache dict, or None outside a scope."""
    return _SCAN_EXTRAS


@contextlib.contextmanager
def scan_once():
    """Within this block, `resolve` reuses one directory walk and one metadata query per type.

    Use only around READ-ONLY work (see the note above). Nested scopes share the outer cache."""
    global _SCAN_CACHE, _SCAN_EXTRAS
    if _SCAN_CACHE is not None:
        yield
        return
    from agent_workflows import artifact_meta as _meta

    _SCAN_CACHE = {}
    _SCAN_ID_INDEX.clear()
    _SCAN_EXTRAS = {}
    try:
        with _meta.scan_once():
            yield
    finally:
        _SCAN_CACHE = None
        _SCAN_ID_INDEX.clear()
        _SCAN_EXTRAS = None


def drop_scan() -> None:
    """Forget what the open `scan_once()` scope has read, after a write inside it.

    The scope stays open; the next `resolve` walks and reads afresh. A no-op outside a scope."""
    if _SCAN_CACHE is not None:
        _SCAN_CACHE.clear()
    _SCAN_ID_INDEX.clear()
    if _SCAN_EXTRAS is not None:
        _SCAN_EXTRAS.clear()
    from agent_workflows import artifact_meta as _meta

    _meta.drop_scan_freshness()


def _scan_key(
    repo_root: Path, record_type: str
) -> Tuple[str, str, bool, Optional[int]]:
    return (str(Path(repo_root)), record_type, bool(_INCLUDE_IGNORED_DIRS), _MAX_DEPTH)


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
    from agent_workflows import research_contract as _rc

    if max_depth is None:
        max_depth = _MAX_DEPTH
    base_depth = len(base.parts)
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in layout.RECORD_SCAN_EXCLUDED_DIRS
            and (
                _INCLUDE_IGNORED_DIRS
                or (
                    d not in EXCLUDED_RECORD_DIRS
                    and not (
                        d.endswith(_rc.COMPANION_SUFFIX)
                        and _rc.companion_owner_stem(Path(dirpath) / d) is not None
                    )
                )
            )
        ]
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
        from agent_workflows.project_context import project_records_dir

        for base in (project_records_dir(repo_root), repo_root / ".agents"):
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
                    if any(ex in rel_parts for ex in EXCLUDED_RECORD_DIRS) or any(
                        ex in rel_parts for ex in layout.RECORD_SCAN_EXCLUDED_DIRS
                    ):
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


_META_TYPE_FOR_RECORD: Dict[str, str] = {
    "plans": "ipd",
    "specs": "spec",
    "prompts": "prompt",
    "research": "research",
    "backlog": "backlog",
    "walkthroughs": "walkthrough",
    "releases": "release",
}


def _cached_states_by_path(repo_root: Path, record_type: str) -> Dict[Path, Any]:
    """Query `artifact_meta` for cached states keyed by resolved Path."""
    if record_type == "reviews":
        return {}
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import project_context as _proj_ctx

    ctx = _proj_ctx.resolve_project_context(target_repo=str(repo_root))
    records_root = Path(ctx.logical_roots["records"])
    scan_repo = _meta._scan_repo_root(ctx, records_root)
    has_tree = records_root.is_dir() or (
        scan_repo is not None
        and (
            (scan_repo / ".aw" / "records").is_dir() or (scan_repo / ".agents").is_dir()
        )
    )
    if not has_tree:
        return {}
    state_root = Path(ctx.logical_roots["state"])
    if (
        not (state_root / "index.db").exists()
        and not (records_root / "meta").is_dir()
        and _meta._SCAN_ONCE_CONNS.get() is None
    ):
        # Without a persistent index.db, log-format meta/ tree, or outer scan_once() session,
        # calling _meta.query() under ephemeral_if_uninitialized() parses the entire multi-thousand
        # file corpus across all record types + reviews into a throwaway :memory: DB just to read
        # one record type. Returning {} lets resolve() use bounded header reads over this type's
        # candidate paths only.
        return {}
    filters: Dict[str, Any] = {"project_context": ctx}
    meta_t = _META_TYPE_FOR_RECORD.get(record_type)
    if meta_t is not None:
        filters["type"] = meta_t
    with _meta.ephemeral_if_uninitialized():
        res = _meta.query(**filters)
    by_path: Dict[Path, Any] = {}
    for st in res.rows:
        if not st.path:
            continue
        try:
            abs_p = _meta.source_path(st.path, records_root, scan_repo).resolve()
        except Exception:
            continue
        by_path[abs_p] = st
    return by_path


def _state_id_for_resolve(st: Any) -> Optional[str]:
    if not st or getattr(st, "id_derived", False):
        return None
    val = getattr(st, "id6", None)
    return val or None


def _state_set_for_resolve(st: Any) -> Optional[str]:
    if not st:
        return None
    raw = getattr(st, "legacy_raw_set", None)
    if raw is not None:
        return raw
    return getattr(st, "set_id", None)


def _state_matches_status(st: Any, tok: str, record_type: str) -> bool:
    if not st:
        return False
    raw = getattr(st, "legacy_raw_status", None)
    if not raw:
        return False
    toks = raw.strip().split()
    if not toks:
        return False
    if record_type == "plans":
        from agent_workflows import plans as _plans

        norm = _plans.normalize_status(toks[0])
        if norm != _plans.LEGACY_GROUP:
            return norm == tok
        if norm == tok:
            return True
        return len(toks) == 1 and toks[0] == tok
    return len(toks) == 1 and toks[0] == tok


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

    paths = None  # lazy: the single enumeration
    states = None  # lazy: (path, State) pairs derived from `paths` via artifact_meta

    cache_entry = (
        _SCAN_CACHE.get(_scan_key(repo_root, record_type))
        if _SCAN_CACHE is not None
        else None
    )
    if cache_entry is not None:
        paths, states = cache_entry[0], cache_entry[1]

    def _paths():
        """Candidate paths with NO file read at all - for the path/stem/substring rules."""
        nonlocal paths
        if paths is None:
            paths = list(_iter_paths(repo_root, record_type))
            if _SCAN_CACHE is not None:
                _SCAN_CACHE[_scan_key(repo_root, record_type)] = (paths, None)
        return paths

    def _states():
        """Candidates paired with `artifact_meta.State` for front-matter rules."""
        nonlocal states
        if states is None:
            from agent_workflows import artifact_meta as _meta

            cands = _paths()
            by_path = _cached_states_by_path(repo_root, record_type) if cands else {}
            out = []
            for p in cands:
                st = by_path.get(p)
                if st is None:
                    hdr = _read_header(p)
                    if hdr is not None:
                        st = _meta.read_text(metadata_region(hdr))
                if st is not None:
                    out.append((p, st))
            states = out
            if _SCAN_CACHE is not None:
                _SCAN_CACHE[_scan_key(repo_root, record_type)] = (_paths(), states)
        return states

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
            if _SCAN_CACHE is not None:
                key = _scan_key(repo_root, record_type)
                index = _SCAN_ID_INDEX.get(key)
                if index is None:
                    index = {}
                    for p, st in _states():
                        rid = _state_id_for_resolve(st)
                        if rid:
                            index.setdefault(rid, []).append(p)
                    _SCAN_ID_INDEX[key] = index
                return list(index.get(tok, []))
            return [p for p, st in _states() if _state_id_for_resolve(st) == tok]
        if kind == MATCH_SETID:
            return [p for p, st in _states() if _state_set_for_resolve(st) == tok]
        if kind == MATCH_STATUS:
            return [
                p for p, st in _states() if _state_matches_status(st, tok, record_type)
            ]
        # The filename-only rules read NO file content (E-05): they consult `_paths()`, never
        # `_states()`. Keep it that way - routing either one back through `_states()` silently
        # reintroduces metadata reads for filename matching.
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


def _declares_typed_subject(path: Path, id6: str) -> bool:
    """True iff the file names ``id6`` through a TYPED reference field in its metadata region."""

    if not id6 or not _core.ID6_RE.fullmatch(id6):
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    from agent_workflows import artifact_meta as _meta

    st = _meta.read_text(metadata_region(text))
    return any(
        st.fields.get(k) == id6
        for k in (
            "subject_id",
            "target_id",
            "references",
            "from_backlog",
            "from_spec",
            "reviewed_id",
        )
    )


# ----------------------------------------------------------------------------------------------
# MUTATING SELECTOR CONFINEMENT (IPD eby93o E-03)
#
# A type-scoped mutating verb (e.g. `aw rename specs <path>`) must not act on a file outside
# that type's records tree. Resolution precedence puts direct PATH first regardless of type,
# so `resolve` legitimately returns any existing file for readers (`aw find`, checkers, runners).
# `resolve_for_mutation` enforces tree containment on the returned paths before mutation.
#
# RECONCILIATION WITH SIBLING (F-14): `research_archive._resolve_research_for_mutation` confines
# to one tree by DENYING `MATCH_PATH` and DROPPING out-of-root paths, refusing only when all paths
# are dropped. Both behaviors are correct because they answer different questions: that helper
# filters a possibly-MULTI-member result (it accepts a setid multi-match, where dropping non-members
# is right), while this guard fires on an explicitly named foreign PATH, where the operator asked
# for one specific file with the wrong verb and refusing loudly naming the type and path is correct.
# Do NOT adopt deny-MATCH_PATH here: that would break legitimate same-type path selectors (E-04).
#
# FAIL-CLOSED ON EMPTY (OQ-02, F-15): When `record_dirs` returns [] for the requested type, the
# predicate MUST fail closed (refuse). `record_dirs` is queried for the REQUESTED type, so in a
# cross-type call the empty list belongs to the attacking type while the victim's tree is full;
# skipping on empty would admit the exact cross-type mutation this guard exists to prevent.
# ----------------------------------------------------------------------------------------------


def is_path_in_record_dirs(repo_root: Path, record_type: str, path: Path) -> bool:
    """Return True iff ``path`` lies inside any directory for ``record_type`` under ``repo_root``.

    Fails closed: returns False if ``record_dirs(repo_root, record_type)`` is empty.
    Reads no file content (purely path-based containment).
    """
    dirs = record_dirs(repo_root, record_type)
    if not dirs:
        return False
    try:
        rp = path.resolve()
    except OSError:
        return False
    for d in dirs:
        try:
            rd = d.resolve()
            if rp.is_relative_to(rd):
                return True
        except (ValueError, OSError):
            continue
    return False


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

    # Containment guard (IPD eby93o E-03): refuse any path outside the requested type's records tree.
    dirs = record_dirs(repo_root, record_type)
    for p in res.paths:
        if not dirs:
            return (
                [],
                f"{record_type} verb cannot act on {p}: it is not inside the {record_type} records tree "
                f"(no {record_type} records tree found)",
            )
        if not is_path_in_record_dirs(repo_root, record_type, p):
            return (
                [],
                f"{record_type} verb cannot act on {p}: it is not inside the {record_type} records tree",
            )

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

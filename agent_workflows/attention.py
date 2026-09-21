"""The read-only cross-tree attention view (Set attnview, Order 03).

`aw attention` scans the tracked `.agents/` trees on demand, validates each artifact against its tree
contract, maps each native status onto the five-value attention class, and renders the result to
STDOUT as a human board or versioned JSON. It writes NOTHING to disk and never touches git. `--check`
(and `--check --agent`) fail closed on any contract violation.

Stdlib-only, Python 3.9 (D46). Reuses `artifact_core` (scan, Drift, render, exit code) and consumes
the Order 01 contracts (`attention_contract`) and the Order 02 specs validator (`specs.validate_spec`).

Determinism (spec Section 8.5): full scan every run; repo-relative POSIX paths; sort by class order,
then normalized path, then id; UTF-8; LF; one final newline; fixed JSON key order/indent/separators;
no timestamps/mtime/locale; `last_history_at` parsed from history, never mtime.
"""

from __future__ import annotations

import functools
import json
import re
import sys
from pathlib import Path
from typing import Any, Collection, Dict, List, NamedTuple, Optional, Sequence, Tuple

from agent_workflows import artifact_core as core
from agent_workflows import artifact_naming as _naming
from agent_workflows import attention_contract as A
from agent_workflows import ipd_schema as _schema
from agent_workflows import lifecycle_style as LS
from agent_workflows import plans as plans_mod
from agent_workflows import research_contract
from agent_workflows import specs as specs_mod
from agent_workflows import term as T

# 3: items gained readiness + oqs + rqs (2 was priority + blocks_release).
# 4 (lanestrand-01 `pr5b0t` E-05): the payload gained the top-level `stranded_lanes` key. BUMPED
# rather than added silently, on this payload's OWN precedent: both earlier bumps were purely ADDITIVE
# too (items gained fields; nothing was removed or renamed), so "additive" has never been this
# repository's reason to skip a bump. The decisive argument is that a consumer must be able to tell
# whether `stranded_lanes` is ABSENT because this repository has no stranded lane or because the
# producer predates the key, and only the version distinguishes those. Every pre-existing key keeps its
# name, its position and its value.
SCHEMA_VERSION = 4
# MAPPING_VERSION is deliberately UNCHANGED at 1. It versions the native-status -> attention-class
# mapping, and no existing `(tree, native_status)` pair maps anywhere new: `attention_contract`'s new
# `lanes` fragment adds a SYNTHETIC tree whose states never previously had a class at all, and no
# scanned artifact's class changed. Bumping it would tell every consumer to re-derive a mapping that is
# byte-identical for every artifact they can see.
MAPPING_VERSION = 1

# attsel `fqnj8k` E-06: THE EXIT CODE FOR A SELECTOR THAT MATCHED NO ARTIFACT.
#
# THE DECISION, WITH THE REJECTED ALTERNATIVES NAMED, so a later reader sees this was decided rather
# than defaulted. `aw attention <selector>` used to print an empty view and exit 0 for a token that
# matched nothing, byte-identical to a token that matched and was then narrowed away downstream, so an
# operator could not tell a typo from a quiet repository and a machine consumer recorded a typo as a
# clean audit.
#
# CHOSEN: 2, with outcome `cannot-run` on the machine surfaces. FOLLOWING THE PRECEDENT spec `25kzda`
# (`Status: approved`) Section 2.3 sets: "Zero matches return exit 2", with the single Section 2.4a
# exemption for STATUS selectors because such a token is "a standing question about repository state
# rather than an assertion that a named item exists", closing "A misspelled id6 still exits 2; only
# the status selectors are exempt". That spec governs `aw <host> run` rather than this verb, so it is
# PRECEDENT and not binding contract; it is adopted because `aw runs` already implements exactly it for
# the identical condition (an unresolvable read-only target: `run_viewer.py`
# `emit_unresolvable_target_refusal`, exit 2, `cannot-run`, `unresolved_targets`).
#
# REJECTED, exit 1 folded into the drift/findings code: `agent_schema.validate_agent_record`'s parity
# rule makes `exit:1` incompatible with `cannot-run`, so this would force a `findings` outcome for a
# request that was never answered - the same greenwash the fix exists to remove - and it would be
# indistinguishable from a genuine contract violation.
#
# REJECTED, exit 0 with a message only, which is the live `aw find` convention (`aw find plans zzzzzz`
# prints `no matching plans` and exits 0): a script that greps for an id6 and gets exit 0 with empty
# output concludes "nothing to do", which is exactly the wrong conclusion, and this plan's execution
# contract mandates the fail-closed form. OQ-01 leaves the relaxation to the maintainer; it is one
# constant and its pinning tests.
#
# IT COMPOSES WITH DRIFT rather than masking it (F12). 2 dominates `core.drift_exit_code`'s 0/1, so a
# no-match on a drifty view can never be read as a clean view, and the drift findings are still carried
# in the record's diagnostics and in the human message, so neither code hides the other.
EXIT_UNRESOLVED_SELECTOR = 2


class Item(NamedTuple):
    id: str
    path: str  # repo-relative POSIX
    tree: str
    native_status: str
    attention_class: str
    gate: Optional[Dict[str, str]]
    last_history_at: Optional[str]
    # awdoctorfix Order 01: surface priority + release-blocker on the board. Optional + trailing so
    # the existing positional Item(...) constructions keep working; readers set them where they apply.
    priority: Optional[str] = None
    blocks_release: Optional[str] = None
    detail_kind: Optional[str] = None
    detail_text: Optional[str] = None
    readiness: Optional[str] = None
    oqs: int = 0
    rqs: int = 0
    # worksequence i6015i E-07: the artifact's DECLARED `Item-Dependencies` edges, in canonical token
    # form, so `aw next -o depth` can sequence prerequisites before dependents.
    #
    # WHY THE FIELD LIVES HERE rather than being looked up when sorting: `scan()` already holds each
    # artifact's full text (it reads it once and then discards it), whereas a sort-time lookup would
    # have to call `check_engine.build_dependency_index`, which re-reads EVERY artifact through
    # `status_set.inventory_all_artifacts`. That second full-tree pass is exactly what the
    # single-authority rule forbids (see `releases.py`: "a second scan could drift from the answer
    # `aw attention` and `aw doctor` give"), and it would be INVISIBLE in the output, so no assertion
    # on what the command prints could catch it. Extracting the edges during the one existing pass
    # keeps the order a pure function of the same scan result the view itself renders.
    #
    # Appended LAST with a default, matching the pattern `priority`/`blocks_release` used, so every
    # existing positional `Item(...)` construction (including the ones in the test suite and in
    # `releases.get_release_blockers`' callers) keeps working unchanged. `None` means "no
    # Item-Dependencies field present"; an empty tuple means the field was present and declared no
    # edges (`none`), a distinction `-o depth` does not need but which costs nothing to preserve.
    item_dependencies: Optional[Tuple[str, ...]] = None
    exec_progress: Optional[Tuple[int, int]] = None
    valid_progress: Optional[Tuple[int, int]] = None


_OQ_SECTION_RE = re.compile(
    r"^##\s+(?:[0-9]+\.\s*)?(?:Open|Resolved)\s+questions\b", re.IGNORECASE
)
_OQ_SECTION_SEARCH_RE = re.compile(
    r"(?m)^##\s+(?:[0-9]+\.\s*)?(?:Open|Resolved)\s+questions\b", re.IGNORECASE
)
_OQ_HEADING_RE = re.compile(
    r"^###\s+((?:OQ|RQ)-[0-9]+|(?:OQ|RQ)-[A-Za-z0-9_-]+):?\s*(.*)$", re.IGNORECASE
)
_OQ_STATUS_RE = re.compile(r"^-[ \t]*Status:[ \t]*(\S+)", re.IGNORECASE)


def count_question_stats(text: str) -> Tuple[int, int]:
    """Count (unresolved_oqs, resolved_rqs) in an artifact's '## Open questions' section."""
    if not text:
        return 0, 0
    m = _OQ_SECTION_SEARCH_RE.search(text)
    if not m:
        return 0, 0
    next_h2 = re.search(r"(?m)^##\s+", text[m.end() :])
    if next_h2:
        section_text = text[m.start() : m.end() + next_h2.start()]
    else:
        section_text = text[m.start() :]

    sec_lower = section_text.lower()
    if "oq-" not in sec_lower and "rq-" not in sec_lower:
        return 0, 0

    in_section = False
    unresolved_count = 0
    resolved_count = 0
    in_question_block = False
    is_resolved = False
    explicit_status = False

    def _flush_question():
        nonlocal \
            unresolved_count, \
            resolved_count, \
            in_question_block, \
            is_resolved, \
            explicit_status
        if in_question_block:
            if is_resolved:
                resolved_count += 1
            else:
                unresolved_count += 1
        in_question_block = False
        is_resolved = False
        explicit_status = False

    for line in section_text.splitlines():
        if line.startswith("## "):
            _flush_question()
            in_section = bool(_OQ_SECTION_RE.match(line.strip()))
            continue
        if not in_section:
            continue
        if line.startswith("### "):
            _flush_question()
            m_h = _OQ_HEADING_RE.match(line.strip())
            if m_h:
                in_question_block = True
                prefix = m_h.group(1).upper()
                rest = m_h.group(2)
                if prefix.startswith("RQ-") or re.search(
                    r"\bRESOLVED\b", rest, re.IGNORECASE
                ):
                    is_resolved = True
                else:
                    is_resolved = False
                explicit_status = False
            continue
        if in_question_block:
            m_s = _OQ_STATUS_RE.match(line.strip())
            if m_s and not explicit_status:
                status_val = m_s.group(1).lower().strip("[]().,")
                if status_val in ("resolved", "closed", "done", "answered"):
                    is_resolved = True
                elif status_val in ("open", "deferred", "pending", "unresolved"):
                    is_resolved = False
                explicit_status = True
            elif not explicit_status:
                if re.search(r"^-[ \t]*Blocking:.*\(resolved\)", line, re.IGNORECASE):
                    is_resolved = True
                elif re.search(
                    r"^-[ \t]*Resolution(?:\s+or\s+deferral\s+rationale)?:\s*RESOLVED\b",
                    line,
                    re.IGNORECASE,
                ):
                    is_resolved = True

    _flush_question()
    return unresolved_count, resolved_count


def read_readiness(text: str) -> Optional[str]:
    """The artifact's `- Readiness:` value normalized to the closed enum, or None.

    DELEGATES to `ipd_schema.read_readiness` rather than re-scanning, because that is the READ-path
    authority for this field and the enum (`go`/`go-pending-approval`/`no-go`) belongs to it. The
    four call sites here previously each ran their own `(\\S+)` scan, which stopped at the first
    space and so folded the workflow's documented multi-word spellings (`GO - PENDING HUMAN
    APPROVAL`, `go (pending human approval)`) down to a bare `go`. That is the one direction this
    field must never fail in: it renders and FILTERS as a clean `go` while the source says the plan
    still needs human approval. The schema reader returns None for anything out-of-vocabulary
    instead, which is the fail-closed answer the rest of the toolkit already relies on.

    Absent and unrecognized are deliberately the same answer (None), matching the schema reader; the
    board shows both as `-`. Pure.
    """
    return _schema.read_readiness(text)


def count_unresolved_open_questions(text: str) -> int:
    """Count open/unresolved questions in an artifact's '## Open questions' section."""
    oqs, _ = count_question_stats(text)
    return oqs


_EV_LEAF_RE = re.compile(r"^-\s*\[([ xX])\]\s*([EV])-[0-9]{2,}\b", re.MULTILINE)


def _extract_checklist_progress(
    text: str,
) -> Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
    """Extract (exec_progress, valid_progress) as ((checked, total), (checked, total)) for a plan.

    Returns (None, None) if no E or V items are present respectively.
    """
    if not text or ("E-" not in text and "V-" not in text):
        return None, None
    e_matches: List[str] = []
    v_matches: List[str] = []
    for mark, kind in _EV_LEAF_RE.findall(text):
        if kind == "E":
            e_matches.append(mark)
        else:
            v_matches.append(mark)

    exec_prog = (
        (sum(1 for m in e_matches if m in ("x", "X")), len(e_matches))
        if e_matches
        else None
    )
    valid_prog = (
        (sum(1 for m in v_matches if m in ("x", "X")), len(v_matches))
        if v_matches
        else None
    )
    return exec_prog, valid_prog


def count_resolved_questions(text: str) -> int:
    """Count resolved questions in an artifact's '## Open questions' section."""
    _, rqs = count_question_stats(text)
    return rqs


_FIELD_PATTERNS = (
    ("summary", re.compile(r"(?mi)^-\s*Summary:\s*(.+)$")),
    ("scope", re.compile(r"(?mi)^-\s*Scope:\s*(.+)$")),
    ("concern", re.compile(r"(?mi)^-\s*Concern:\s*(.+)$")),
    ("question", re.compile(r"(?mi)^-\s*Question:\s*(.+)$")),
    ("title", re.compile(r"(?mi)^-\s*Title:\s*(.+)$")),
)
_H1_RX = re.compile(r"(?m)^#\s+(?:[A-Za-z0-9_-]+:\s*)?(.+)$")

# The UNBULLETED (plain YAML) spelling of the same keys, for a doc whose front matter is real YAML
# rather than the `- Key: value` bullet list the plan/spec/backlog trees use (attcor `rkn8ya` E-10).
#
# THE RESEARCH CORPUS IS WHY: every pattern above requires the `-\s*` bullet, but research front
# matter is plain YAML. Measured on this tree, 110 research files carry an unbulleted `summary:` and
# ZERO carry `- Summary:`, so the field was NEVER read for that whole tree and `--details` fell through
# to the H1. The H1 fallback is usually adequate but NOT equivalent: `_H1_RX` strips a leading
# `Word:` prefix, turning `# Research: the design prompts...` into a mid-sentence fragment, and 4
# files have no H1 at all and so showed NO detail despite carrying a summary.
_UNBULLETED_FIELD_PATTERNS = tuple(
    (tag, re.compile(r"(?mi)^" + tag + r":[ \t]*(.+)$")) for tag, _rx in _FIELD_PATTERNS
)

# FRONT-MATTER SCOPED, deliberately. 55 files under `.aw/records/` carry an unbulleted `summary:`-like
# key in their BODY PROSE (a quoted example, a table cell, an instruction). Matching the whole document
# would surface that prose as the artifact's own summary, so the unbulleted form is read ONLY from a
# leading `---` fenced YAML block. A document with no front matter is unaffected.
_FRONTMATTER_RX = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)


def _frontmatter_block(text: str) -> str:
    """The raw YAML front-matter block (between the leading `---` fences), or `""` when absent."""

    m = _FRONTMATTER_RX.match(text)
    return m.group(1) if m else ""


def _extract_detail(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract (detail_kind, detail_text) using the fallback cascade:
    Summary -> Scope -> Concern -> Question -> Title -> H1 header.

    Each key is accepted in the `- Key: value` BULLET form anywhere in the document (the plan/spec/
    backlog shape) and, additionally, in the plain `key: value` UNBULLETED form inside a leading YAML
    front-matter block (the research shape). The CASCADE ORDER is unchanged, and the bulleted form
    WINS at each step, so no artifact that already reported a detail reports a different one.
    """
    fm = _frontmatter_block(text)
    for (tag, rx), (_utag, urx) in zip(_FIELD_PATTERNS, _UNBULLETED_FIELD_PATTERNS):
        cap = tag.capitalize() + ":"
        low = tag + ":"
        up = tag.upper() + ":"
        if cap in text or low in text or up in text:
            m = rx.search(text)
            if m:
                val = m.group(1).strip()
                if val:
                    return tag, val
            # The bulleted form is absent (or empty): try the unbulleted front-matter spelling.
            if fm:
                um = urx.search(fm)
                if um:
                    uval = um.group(1).strip()
                    if uval:
                        return tag, uval
    if "# " in text:
        m = _H1_RX.search(text)
        if m:
            val = m.group(1).strip()
            if val:
                return "title", val
    return None, None


def _rel_posix(repo_root: Path, p: Path) -> str:
    try:
        return p.relative_to(repo_root).as_posix()
    except ValueError:
        return p.resolve().relative_to(repo_root.resolve()).as_posix()


def _classify_tree(rel_posix: str) -> Optional[A.TreePolicy]:
    """Return the TreePolicy whose root is a path-prefix of the file, or None (unclassified)."""

    norm_rel = rel_posix
    if norm_rel.startswith(".aw/records/"):
        tail = norm_rel[len(".aw/records/") :]
        # Order 07 flattened the doc-family types out of docs/ in the .aw/ layout, but the
        # TreePolicy keys (and legacy .agents/) keep the docs/ grouping. Re-insert docs/ for those
        # types so the flat .aw/records/<type> classifies under the same policy as .agents/docs/<type>.
        _DOCS_FAMILY = (
            "specs",
            "research",
            "walkthroughs",
            "roadmaps",
            "prompt-library",
        )
        first = tail.split("/", 1)[0]
        if first in _DOCS_FAMILY:
            # prompt-library maps to the legacy docs/prompts policy key (renamed in Order 07).
            legacy_type = "prompts" if first == "prompt-library" else first
            tail = "docs/" + legacy_type + tail[len(first) :]
        norm_rel = ".agents/" + tail

    best: Optional[A.TreePolicy] = None
    for pol in A.TREE_POLICY:
        root = pol.root.replace("\\", "/")
        if norm_rel == root or norm_rel.startswith(root + "/"):
            # choose the longest matching root (specs under docs, etc.)
            if best is None or len(pol.root) > len(best.root):
                best = pol
    return best


def _history_section_lines(text: str) -> List[str]:
    if "## Workflow history" not in text:
        return []
    m = re.search(r"(?m)^## Workflow history[ \t]*$", text)
    if not m:
        return []
    start_pos = m.end()
    m_end = re.search(r"(?m)^## ", text[start_pos:])
    section = text[start_pos : start_pos + m_end.start()] if m_end else text[start_pos:]
    lines = section.splitlines()
    if lines and not lines[0].strip():
        lines = lines[1:]
    return lines


# worksequence i6015i E-07: the `- Item-Dependencies:` front-matter bullet. Only the bullet is matched
# here; the VALUE grammar is parsed by `ipd_schema.parse_item_dependencies`, the shipped authority for
# this field, rather than by a second regex that would drift from it.
_ITEM_DEPS_RE = re.compile(r"(?m)^-[ \t]*Item-Dependencies:[ \t]*(.+?)[ \t]*$")


def _extract_item_dependencies(text: str) -> Optional[Tuple[str, ...]]:
    """The artifact's declared `Item-Dependencies` edges in canonical token form, or None.

    Returns None when the field is ABSENT, and a (possibly empty) tuple when it is present. Reuses
    `ipd_schema.parse_item_dependencies` so the edge grammar, the `none`/`unresolved` sentinels, the
    accepted target types (`ipd`/`spec`/`backlog`) and the canonical token spelling all come from the
    one owning module. A malformed value yields an empty tuple rather than raising: this is a pure
    READ on a display/ordering path, and the fail-closed contract violation for a bad edge already
    belongs to `aw check`, which must stay the single authority for that finding. Pure.
    """
    if "Item-Dependencies:" not in text and "item-dependencies:" not in text:
        return None
    m = _ITEM_DEPS_RE.search(text)
    if m is None:
        return None
    edges, _ready, err = _schema.parse_item_dependencies(m.group(1))
    if err:
        return ()
    return tuple(e.canonical() for e in edges)


def _plans_id(text: str) -> Optional[str]:
    m = re.search(r"(?m)^-\s*Id:\s*(\S+)", text[:2048])
    if m:
        return m.group(1).strip()
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("- Id:"):
            return s[len("- Id:") :].strip()
    return None


_TREE_TO_SCAN_ROOTS: Dict[str, Tuple[str, ...]] = {
    "plans": (".aw/records/plans", ".agents/plans"),
    "specs": (".aw/records/specs", ".agents/docs/specs"),
    "research": (".aw/records/research", ".agents/docs/research"),
    "backlog": (".aw/records/backlog", ".agents/backlog"),
    "releases": (".aw/records/releases", ".agents/releases"),
    "walkthroughs": (".aw/records/walkthroughs", ".agents/docs/walkthroughs"),
    "roadmaps": (".aw/records/roadmaps", ".agents/docs/roadmaps"),
    "prompts": (
        ".aw/records/prompt-library",
        ".agents/docs/prompts",
        ".aw/records/prompts",
        ".agents/prompts",
    ),
    "prompt-library": (".aw/records/prompt-library", ".agents/docs/prompts"),
    "comms": (".aw/records/comms", ".agents/comms"),
}


def scan(
    repo_root: Path, type_filters: Optional[Collection[str]] = None
) -> Tuple[List[Item], List[core.Drift]]:
    """Full deterministic scan of the tracked trees. Returns (items, violations). Pure read."""

    items: List[Item] = []
    drift: List[core.Drift] = []
    seen_ids: Dict[str, str] = {}
    seen_paths: set = set()

    scan_roots = None
    if type_filters:
        collected = []
        for t in type_filters:
            if t in _TREE_TO_SCAN_ROOTS:
                collected.extend(_TREE_TO_SCAN_ROOTS[t])
            else:
                collected = None
                break
        if collected is not None and collected:
            scan_roots = tuple(dict.fromkeys(collected))

    scan_files = (
        core.iter_scan_files(repo_root, scan_roots=scan_roots)
        if scan_roots
        else core.iter_scan_files(repo_root)
    )

    for f in scan_files:
        rel = _rel_posix(repo_root, f)
        # only artifacts under an inventoried tree matter; the four root docs + READMEs are not artifacts
        pol = _classify_tree(rel)
        if pol is None:
            # a file under no inventoried tree, but only flag it if it is under .agents/ (not a root doc)
            if (
                rel.startswith(".agents/")
                and not rel.endswith("/README.md")
                and Path(rel).name != "README.md"
            ):
                drift.append(
                    core.Drift(
                        rel,
                        "attention.unclassified-tree",
                        "file under no inventoried tree",
                    )
                )
            continue
        if not pol.tracked:
            continue
        if A.is_nonartifact_name(Path(rel).name):
            continue

        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            drift.append(core.Drift(rel, "attention.unreadable", "cannot read/decode"))
            continue

        if rel in seen_paths:
            drift.append(
                core.Drift(rel, "attention.duplicate-path", "duplicate normalized path")
            )
            continue
        seen_paths.add(rel)

        rec, rec_drift = _record_for(pol.name, rel, f, text)
        drift.extend(rec_drift)
        if rec is None:
            continue

        # worksequence i6015i E-07: extract the declared dependency edges HERE, while `text` is still
        # in hand, so `-o depth` needs no second artifact-reading pass. Applied uniformly to every
        # tracked type rather than inside the five per-tree `_*_record` builders: the field's grammar is
        # type-agnostic (`ipd_schema.ITEM_DEP_TYPES` accepts `ipd`/`spec`/`backlog` TARGETS) and one
        # call site cannot drift from four others.
        deps = _extract_item_dependencies(text)
        if deps is not None:
            rec = rec._replace(item_dependencies=deps)

        if rec.id:
            if rec.id in seen_ids:
                drift.append(
                    core.Drift(
                        rel,
                        "attention.duplicate-id",
                        A.escape_detail(f"id {rec.id} also on {seen_ids[rec.id]}"),
                    )
                )
            else:
                seen_ids[rec.id] = rel
        items.append(rec)

    # setupmarker Order 01: the operational-action ledger was DELETED (it was redundant with backlog
    # and its eager mkdir made this read path stamp `.aw/state/` into every scanned repo - write-on-
    # read). "Setup pending" is now DERIVED read-only from the `.aw/setup-repo-needed.md` marker
    # (see `setup_needed`), not scanned as an action tree here.

    # IPD h40usm E-02: reclassify STALE research so finished-but-unpromoted `todo` no longer
    # masquerades as `ready`. The RUN/cited-by-executed signal is manifest-level + cross-tree, so it
    # cannot live in the status-only, pure/total `class_of`; instead we apply it here as a post-scan
    # pass keyed by research id6 (the lower-drift option per the IPD WIRING note + OQ-01). A RUN or
    # cited-by-executed `todo` doc is reclassed READY -> PARKED (dropped from the default actionable
    # board; child 01's `aw check`/`aw research index --check` owns the fail-closed stale-state drift,
    # so attention does NOT re-emit it). `active` is a genuine live state and is NOT touched; a
    # genuinely-unrun `todo` prompt stays READY (actionable). No new attention class is introduced.
    # (rstodo p3o9je: the hot state was renamed `intake` -> `todo`; native_status is normalized to the
    # canonical `todo` at the scanner, so a legacy `intake` doc is handled identically here.)
    items = _reclassify_stale_research(repo_root, items)

    # worksequence i6015i E-04: the default order is unchanged. `sort_items` with the default key
    # reproduces exactly the `(class order, path, id)` tuple this line always used, which is what makes
    # `aw next` byte-identical to the pre-rename `aw attention`.
    items = sort_items(items)
    drift.sort(key=lambda d: (d.location, d.rule))
    return items, drift


# --------------------------------------------------------------------------------------
# Ordering (worksequence i6015i, E-04 .. E-08)
# --------------------------------------------------------------------------------------

# The filename grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>`, from which `-o set` and `-o order` read.
#
# `set` and `order` are legitimately PARTIAL keys: a name that does not match sorts as ABSENT rather
# than raising. The non-matching population is the RESEARCH corpus, whose grammar is the shared
# clustered CORE followed by its own `.<model>.<kind>.md` facets (see `research_contract.parse_name`),
# plus genuinely grandfathered pre-cutover names.
#
# THE COMMENT THAT USED TO SIT HERE WAS WRONG ABOUT WHY, and attcor `rkn8ya` E-08 corrects it rather
# than preserving a misleading attribution. It blamed all 156 non-matching names on "grandfathered
# pre-cutover names"; re-measured on this tree, 103 of them were FULLY CONFORMANT modern names that
# this module's own regex rejected because it spelled the set id `[A-Za-z0-9]+`, excluding the HYPHEN
# that `artifact_naming.build_clustered_name` PRODUCES (it kebab-cases the set id) and that
# `artifact_naming._CLUSTERED_RE` accepts. Those 103 (88 plans, 15 backlog) all sorted as absent under
# `-o set` and `-o order`, so the defect was a second private copy of a shared grammar, not history.
#
# THE FIX IS DELEGATION to `artifact_naming`, the SINGLE naming authority, so a third copy of the
# grammar cannot drift from it again. NO REGEX IS WRITTEN IN THIS MODULE: the full-name reading uses
# `parse_clustered`, and the prefix reading uses `parse_clustered_prefix`, which is DEFINED IN THE
# AUTHORITY for this purpose. A prefix reading is needed at all because `parse_clustered` anchors at
# the tail with a CLOSED facet enum and therefore rejects a research name like
# `...-<id6>-<slug>.gpt5.survey.md` whose PREFIX is nonetheless perfectly parseable. (Re-encoding that
# prefix here would have re-created the very duplication this item removes, and
# `tests/test_naming_authority_single_source.py` correctly refuses it.)
#
# MEASURED AFTER THE FIX on this tree: 0 disagreements with `parse_clustered` across all 1148
# clustered-conformant items, and 127 items that previously sorted as absent now sort under their true
# set, with 0 items losing a key they previously had.

# `-o priority` ranks high > medium > low. DERIVED from the one shared vocabulary
# (`attention_contract.PRIORITY_ORDER`, itself aligned with `backlog.PRIORITIES` and
# `check_engine._PRIORITY_RANK`) rather than a second hardcoded rank table, which is the mistake
# `ipd_schema` recorded when a duplicated status copy desynced.
_PRIORITY_SORT_RANK = {name: i for i, name in enumerate(A.PRIORITY_ORDER)}
_READINESS_SORT_RANK = {
    name: i
    for i, name in enumerate(
        getattr(A, "READINESS_ORDER", ("go", "go-pending-approval", "no-go"))
    )
}
_RUN_SORT_RANK = {
    name: i
    for i, name in enumerate(
        getattr(
            A,
            "RUN_SORT_ORDER",
            ("running", "merging", "queued", "done", "blocked", "failed"),
        )
    )
}

# The sentinel for "this item has no value for the selected key". Sorting is done on a
# `(absent_flag, value, default_tail...)` tuple, where `absent_flag` is 1 for a missing value, so
# absent items land LAST under EVERY key without their value ever being compared (which also avoids
# comparing None with str on Python 3).
_ABSENT = 1
_PRESENT = 0


def _name_grammar_fields(path: str) -> Tuple[Optional[str], Optional[int]]:
    """(set_id, order) parsed from an artifact's FILENAME, or (None, None) when it does not match.

    DELEGATES to the single naming authority first (`artifact_naming.parse_clustered`), so `-o set`
    and `-o order` can never again disagree with the grammar that BUILDS these names (attcor
    `rkn8ya` E-08). Falls back to the authority's clustered PREFIX only for a name whose tail the
    authority's closed facet enum rejects but whose prefix is well-formed, which is the research
    corpus's `.<model>.<kind>.md` shape.
    """

    name = path.rsplit("/", 1)[-1]
    m = _naming.parse_clustered(name)
    if m is not None:
        try:
            return m.group("set"), int(m.group("nn"))
        except ValueError:  # pragma: no cover - the grammar already pins two digits
            return m.group("set"), None
    m = _naming.parse_clustered_prefix(name)
    if m is None:
        return None, None
    try:
        return m.group("set"), int(m.group("nn"))
    except ValueError:  # pragma: no cover - the grammar already pins two digits
        return m.group("set"), None


def dependency_depths(items: Sequence[Item]) -> Tuple[Dict[str, int], List[List[str]]]:
    """Longest declared prerequisite chain ending at each item, plus any cycles found.

    Returns ``(depth_by_id6, cycles)``. Depth 0 means the item declares no prerequisite that is
    itself present in the view, so roots sort first and a dependent always follows what it depends
    on: the ordering the work must actually be done in (spec 25kzda 5.4 rule 4, and the same
    direction `oc_runipd.queue_sort_key` puts `dependency_depth` first in).

    Type-agnostic BY CONSTRUCTION: the edges carry their own target type, and this view holds plans,
    specs, backlog items, research and releases together keyed by id6, so a plan declaring a
    `backlog` target orders against that backlog item without any per-type special case. It differs
    from the runner's `dependency_depth` in exactly one way, deliberately: the runner restricts edges
    to QUEUE MEMBERS (`edge.id6 not in by_id` is skipped) because its queue is homogeneous IPDs,
    whereas here every tracked artifact is in scope.

    Cycle-safe and non-recursive-on-the-caller's-behalf: a node already on the current path
    contributes 0 rather than recursing forever, so a hand-edited cyclic edge set cannot hang the
    view. Cycles are DETECTED and returned so the caller can REPORT them (E-08) instead of silently
    reordering around a real defect that `aw check` has its own rule for. Pure.
    """
    # Only edges whose target is IN THE VIEW can order the view; an edge to an artifact outside it
    # (or a typo'd id6) is a leaf and contributes no ordering, exactly as an out-of-queue edge does
    # for the runner.
    present: Dict[str, Item] = {it.id: it for it in items if it.id}
    edges_by_id: Dict[str, List[str]] = {}
    for it in items:
        if not it.id:
            continue
        targets: List[str] = []
        for token in it.item_dependencies or ():
            edge, err = _schema._parse_item_dependency_edge(token)
            if err or edge is None:
                continue
            if edge.id6 in present and edge.id6 != it.id:
                targets.append(edge.id6)
        edges_by_id[it.id] = sorted(set(targets))

    # Cycle detection is DELEGATED to the shipped pure helper rather than re-implemented here.
    cycles = _schema.item_dependency_cycles(edges_by_id)
    in_cycle = {node for cyc in cycles for node in cyc}

    depths: Dict[str, int] = {}

    def _depth(node: str, on_path: frozenset) -> int:
        if node in on_path:
            return 0
        cached = depths.get(node)
        if cached is not None:
            return cached
        best = 0
        for target in edges_by_id.get(node, ()):
            best = max(best, 1 + _depth(target, on_path | {node}))
        # Only memoize a value computed off the recursion path, so a cycle cannot poison the cache
        # for nodes reached through it.
        if not (on_path & in_cycle) and node not in in_cycle:
            depths[node] = best
        return best

    out: Dict[str, int] = {}
    for node in sorted(edges_by_id):
        out[node] = _depth(node, frozenset())
    return out, cycles


def _order_key(
    it: Item,
    order_by: str,
    depths: Optional[Dict[str, int]],
    repo_root: Optional[Path] = None,
    run_map: Optional[Dict[str, str]] = None,
) -> Tuple:
    """The PRIMARY sort component for one item under ``order_by``.

    Every branch returns ``(absent_flag, value)`` where ``absent_flag`` is `_ABSENT` for an item that
    carries no value for this key, which is what places it LAST (maintainer ruling: absent is never
    hidden and never defaulted, matching the `xprio` ruling that an absent Priority renders as
    UNPRIORITIZED rather than being defaulted to `medium`). Values are made directly comparable
    (ints/strs, never None), so no branch can raise a TypeError on a mixed comparison.
    """
    if order_by in ("runs", "run"):
        st = _item_run_status(it, run_map)
        if st and st != "-":
            rank = _RUN_SORT_RANK.get(st.lower())
            if rank is not None:
                return (_PRESENT, rank)
            return (_PRESENT, len(_RUN_SORT_RANK))
        return (_ABSENT, len(_RUN_SORT_RANK))
    if order_by == "priority":
        rank = _PRIORITY_SORT_RANK.get((it.priority or "").lower())
        # PRIORITY_ORDER is high-first, so its index is already the descending position.
        return (_PRESENT, rank) if rank is not None else (_ABSENT, 0)
    if order_by == "date":
        # Newest first: ISO dates sort lexicographically, so reverse the string order by negating
        # via a descending comparison on the inverted key. Using the raw string with a reversed
        # comparator would flip the whole tuple, so invert only this component.
        return (
            (_PRESENT, _invert_str(it.last_history_at))
            if it.last_history_at
            else (_ABSENT, "")
        )
    if order_by in ("set", "setid"):
        set_id, _order = _name_grammar_fields(it.path)
        return (_PRESENT, set_id) if set_id else (_ABSENT, "")
    if order_by == "order":
        _set_id, order = _name_grammar_fields(it.path)
        return (_PRESENT, order) if order is not None else (_ABSENT, 0)
    if order_by == "blocking":
        # Release blockers first, then everything else. `blocks_release` is the DECLARED gate field.
        #
        # attcor `rkn8ya` E-09: `"-"` means ABSENT, not "gated on a release named '-'". A bare
        # truthiness test sorted the literal string as PRESENT, and `-` (0x2D) collates below every
        # alphanumeric, so an item DECLARING ITSELF A NON-BLOCKER sorted ABOVE every real blocker.
        # This aligns the one reader of four that omitted the guard: `matches_blocking`,
        # `release_blockers`, `_resolve_release_version` and the render-time flag all exclude `"-"`.
        #
        # LATENT, recorded so nobody over-claims the impact: `releases.set_blocks_release_line`
        # REMOVES the line for value `-`, and 0 artifacts in this tree carry `Blocks-Release: -`, so
        # only a hand-edit produces the condition. It is a consistency fix, not an observed outage.
        blk = it.blocks_release
        return (_PRESENT, blk) if (blk and blk != "-") else (_ABSENT, "")
    if order_by == "depth":
        if depths is None:
            return (_ABSENT, 0)
        return (_PRESENT, depths.get(it.id, 0)) if it.id else (_ABSENT, 0)
    if order_by == "id6":
        return (_PRESENT, it.id) if it.id else (_ABSENT, "")
    if order_by == "path":
        return (_PRESENT, it.path) if it.path else (_ABSENT, "")
    if order_by == "file":
        return (_PRESENT, Path(it.path).name) if it.path else (_ABSENT, "")
    if order_by == "status":
        return (_PRESENT, it.native_status) if it.native_status else (_ABSENT, "")
    if order_by in ("tree", "type"):
        return (_PRESENT, it.tree) if it.tree else (_ABSENT, "")
    if order_by == "readiness":
        rank = _READINESS_SORT_RANK.get((it.readiness or "").lower())
        return (
            (_PRESENT, rank)
            if rank is not None
            else (_ABSENT, len(_READINESS_SORT_RANK))
        )
    if order_by == "oqs":
        oqs = getattr(it, "oqs", 0) or 0
        return (_PRESENT, -oqs) if oqs > 0 else (_ABSENT, 0)
    if order_by == "rqs":
        rqs = getattr(it, "rqs", 0) or 0
        return (_PRESENT, -rqs) if rqs > 0 else (_ABSENT, 0)
    if order_by in ("ctime", "mtime"):
        if repo_root is None:
            try:
                from agent_workflows.project_context import (
                    is_project_dir,
                    resolve_verb_repo_root,
                )

                cand = resolve_verb_repo_root(None)
                if is_project_dir(cand):
                    repo_root = cand
            except Exception:
                pass
        f = (repo_root / it.path) if repo_root else Path(it.path)
        try:
            st = f.stat()
            ts = st.st_ctime if order_by == "ctime" else st.st_mtime
            return (_PRESENT, -ts)
        except OSError:
            return (_ABSENT, 0.0)
    # `class` (the default) adds no primary component; the default tail alone decides.
    return ()


def _invert_str(value: str) -> Tuple[int, ...]:
    """Map a string to a key that sorts in DESCENDING order under an ascending sort.

    Used by `-o date` so the newest `last_history_at` comes first WITHOUT reversing the whole sort
    tuple (which would also reverse the default `(class, path, id)` tail and so break determinism
    expectations). Negating each code point is exact and locale-free, honoring this module's stated
    determinism contract (no locale, no timestamps).
    """
    return tuple(-ord(ch) for ch in value)


def sort_items(
    items: Sequence[Item],
    order_by: str = A.ORDER_CLASS,
    repo_root: Optional[Path] = None,
    run_map: Optional[Dict[str, str]] = None,
) -> List[Item]:
    """Return ``items`` ordered by ``order_by``. Never filters: the result is a PERMUTATION.

    The DEFAULT (`class`) reproduces the historical `(class order, path, id)` tuple exactly, byte for
    byte, because that order is a pinned contract (`xprio`) and not merely a default. Every other key
    prepends its own component and then FALLS THROUGH to that same tail, so every order is TOTAL and
    stable across runs, with no timestamps, mtime or locale involved.

    `-o depth` needs the whole item set to compute a graph, so the depths are computed ONCE here
    rather than per comparison. Cycles are reported through `sort_items_with_notices`; this function
    keeps the plain signature for callers that only want the order.
    """
    ordered, _notices = sort_items_with_notices(
        items, order_by, repo_root=repo_root, run_map=run_map
    )
    return ordered


def sort_items_with_notices(
    items: Sequence[Item],
    order_by: str = A.ORDER_CLASS,
    repo_root: Optional[Path] = None,
    run_map: Optional[Dict[str, str]] = None,
) -> Tuple[List[Item], List[str]]:
    """`sort_items` plus any human-facing notices the ordering produced (E-08).

    A notice is currently emitted only for a dependency CYCLE under `-o depth`. A cycle degrades to
    the default order for the affected nodes and is REPORTED rather than silently absorbed, because a
    view that quietly reorders around a cycle hides a defect `aw check` has a rule for. Notices are
    advisory and never change the exit code, which stays owned by the drift set.
    """
    keys = [k.strip() for k in order_by.split(",") if k.strip()]
    if not keys:
        keys = [A.ORDER_CLASS]

    for k in keys:
        if k not in A.ORDER_KEYS:
            # An out-of-vocabulary key cannot reach here through the CLI (argparse `choices` refuses it),
            # so this is a programming error rather than user input; fail loudly instead of silently
            # falling back to an order the caller did not ask for.
            raise ValueError(
                "unknown order key {0!r}; valid keys: {1}".format(
                    k, ", ".join(A.ORDER_KEYS)
                )
            )

    if any(k in ("runs", "run") for k in keys) and run_map is None:
        if repo_root is None:
            try:
                from agent_workflows.project_context import (
                    is_project_dir,
                    resolve_verb_repo_root,
                )

                cand = resolve_verb_repo_root(None)
                if is_project_dir(cand):
                    repo_root = cand
            except Exception:
                pass
        run_map = get_active_runs_map(repo_root) if repo_root else {}

    notices: List[str] = []
    depths: Optional[Dict[str, int]] = None
    if "depth" in keys:
        depths, cycles = dependency_depths(items)
        for cyc in cycles:
            notices.append(
                "dependency cycle: "
                + " -> ".join(cyc)
                + " (those items keep the default order; run `aw check plans` for the fail-closed finding)"
            )

    def key(it: Item) -> Tuple:
        return (
            tuple(_order_key(it, k, depths, repo_root, run_map) for k in keys),
            A.ATTENTION_CLASS_ORDER.index(it.attention_class),
            it.path,
            it.id,
        )

    return sorted(items, key=key), notices


def _reclassify_stale_research(repo_root: Path, items: List[Item]) -> List[Item]:
    """Return ``items`` with STALE research ``todo`` rows moved from READY to PARKED.

    A research ``todo`` doc is stale when its SET is a RUN prompt-set OR it is cited by an executed
    artifact (child 01's derivations). Such a doc is finished-but-unpromoted, not actionable, so it is
    reclassed to PARKED (hidden from the default board). A genuinely-unrun ``todo`` prompt keeps its
    READY class. Only ``todo`` is considered; ``active`` (a live state -> ACTIVE) is left untouched.
    Failure-isolated: any error in deriving the signal leaves the items unchanged (never breaks the
    view). ``class_of`` is not involved and stays status-only/total. (rstodo p3o9je: native_status is
    already normalized to canonical ``todo`` at the scanner, so a legacy ``intake`` doc is included.)
    """

    research_todo = [
        it for it in items if it.tree == "research" and it.native_status == "todo"
    ]
    if not research_todo:
        return items
    try:
        from agent_workflows import research_index as _ridx

        research_root = research_contract.resolve_research_root(repo_root)
        entries, _drift = _ridx._scan_docs(research_root)
        run_sets = _ridx.run_prompt_set_ids(entries)
        cited_exec = _ridx.cited_by_executed_ids(repo_root, research_root)
        by_id = {e.id6: e for e in entries}
    except Exception:
        return items

    out: List[Item] = []
    for it in items:
        if (
            it.tree == "research"
            and it.native_status == "todo"
            and it.attention_class == A.READY
        ):
            entry = by_id.get(it.id)
            stale = entry is not None and (
                entry.set_id in run_sets or it.id in cited_exec
            )
            if stale:
                out.append(it._replace(attention_class=A.PARKED))
                continue
        out.append(it)
    return out


def _record_for(
    tree: str, rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    if tree == "specs":
        return _spec_record(rel, path, text)
    if tree == "plans":
        return _plans_record(rel, path, text)
    if tree == "research":
        return _research_record(rel, path, text)
    if tree == "backlog":
        return _backlog_record(rel, path, text)
    if tree == "releases":
        return _release_record(rel, path, text)
    return None, []


def _release_record(
    rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    """Attention record for a release record (ship-gate anchor, awrelease). Reads `- Status:` +
    `- Id:` and maps via the releases CLASS_MAP (planned->ready, blocked->blocked, shipped->done)."""
    import re as _re

    drift: List[core.Drift] = []
    ms = _re.search(r"(?m)^- Status:\s*(\S+)\s*$", text)
    status = ms.group(1) if ms else None
    if status is None:
        drift.append(core.Drift(rel, "attention.missing-status", "no release Status"))
        return None, drift
    try:
        cls = A.class_of("releases", status)
    except A.UnknownNativeStatus:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                A.escape_detail(f"release status {status!r}"),
            )
        )
        return None, drift
    mid = _re.search(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$", text)
    lha = A.last_history_at(_history_section_lines(text))
    d_kind, d_text = _extract_detail(text)
    oqs, rqs = count_question_stats(text)
    return Item(
        mid.group(1) if mid else "",
        rel,
        "releases",
        status,
        cls,
        None,
        lha,
        detail_kind=d_kind,
        detail_text=d_text,
        oqs=oqs,
        rqs=rqs,
    ), drift


def _spec_record(
    rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    drift = specs_mod.validate_spec(path, text)
    lines = text.split("\n")
    status = specs_mod._read_status(lines)
    if status is None or status not in A.SPEC_STATUSES:
        return None, drift  # violations already recorded by validate_spec
    kind, ref, summary = specs_mod._read_gate(lines)
    gate = None
    if status == "deferred" and kind and ref:
        gate = {"kind": kind, "ref": ref}
        if summary:
            gate["summary"] = summary
    lha = A.last_history_at(_history_section_lines(text))
    # awdoctorfix Order 01: read Blocks-Release from the spec's front-matter so the board can surface it.
    br = specs_mod._read_blocks_release(lines)
    # xprio rp859c E-03: populate Item.priority from the spec's `- Priority:` line so the board LABELS
    # a spec's priority via the existing renderer (absent = None = no label). Shared sort key unchanged.
    pr = specs_mod._read_priority(lines)
    d_kind, d_text = _extract_detail(text)
    rd = read_readiness(text)
    oqs, rqs = count_question_stats(text)
    sid_m = re.search(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$", text)
    sid = sid_m.group(1) if sid_m else ""
    return Item(
        sid,
        rel,
        "specs",
        status,
        A.class_of("specs", status),
        gate,
        lha,
        blocks_release=br,
        priority=pr,
        detail_kind=d_kind,
        detail_text=d_text,
        readiness=rd,
        oqs=oqs,
        rqs=rqs,
    ), drift


_PLANS_DIR_PREFIXES = (".aw/records/plans/", ".agents/plans/")


def _plan_disposition_from_rel(rel: str) -> str:
    """The plan's lifecycle DISPOSITION (``executed``/``superseded``/...) from its repo-relative path.

    attcor `rkn8ya` E-05. Recognizes BOTH layouts: the modern `.aw/records/plans/<disp>/...` and the
    legacy `.agents/plans/<disp>/...`. Returns ``""`` when the path names no disposition directory
    (a plan sitting directly in the plans dir, or a path under neither prefix).

    THE FIRST COMPONENT UNDER THE PLANS DIR, deliberately, NOT the parent directory name: `aw archive
    plans` shards a terminal plan into ``<disposition>/YYYYMM/``, so a `parent.name` test would read
    ``202609`` and silently stop recognizing every sharded plan. This is the derivation
    `check_engine._plan_disposition` and `plans_index.scan_plans` already use, reused rather than
    invented a third time.
    """

    norm = rel.replace("\\", "/")
    for prefix in _PLANS_DIR_PREFIXES:
        if norm.startswith(prefix):
            tail = norm[len(prefix) :]
            return tail.split("/", 1)[0] if "/" in tail else ""
    return ""


def _plans_record(
    rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    drift: List[core.Drift] = []
    status = plans_mod.read_status(path, text=text)
    if status is None:
        drift.append(core.Drift(rel, "attention.missing-status", "no plan Status"))
        return None, drift
    if status not in plans_mod.RECOGNIZED:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                A.escape_detail(f"plan status {status!r}"),
            )
        )
        return None, drift
    # disposition vs terminal-status consistency (spec F3: "disposition-vs-terminal-status
    # disagreement" fails `--check` closed).
    #
    # attcor `rkn8ya` E-05: this check was DEAD under the modern layout. It tested only
    # `rel.startswith(".agents/plans/")`, so every `.aw/records/plans/<disp>/...` path yielded
    # `disp = ""` and the rule below could never fire; measured on this tree, all 700+ plans live
    # under `.aw/records/plans/`, so the rule fired for exactly zero of them.
    disp = _plan_disposition_from_rel(rel)
    if (
        disp in plans_mod.DIR_TERMINAL
        and plans_mod.DIR_TERMINAL[disp] != status
        and status in plans_mod.TERMINAL
    ):
        drift.append(
            core.Drift(
                rel,
                "attention.disposition-mismatch",
                A.escape_detail(f"dir {disp} vs status {status}"),
            )
        )
    pid = _plans_id(text)
    lha = A.last_history_at(_history_section_lines(text))
    # IPD 7mw7m5 E-02: populate Item.blocks_release for a release-blocking plan so it renders with
    # the `>` glyph / `[blocking]` label like specs/backlog blockers (the release_blockers SET scan
    # already re-reads the file, so set-membership does not depend on this; display parity does).
    br = None
    if "Blocks-Release:" in text:
        br_m = re.search(r"(?m)^- Blocks-Release:\s*(\S+)\s*$", text[:4096])
        if not br_m and len(text) > 4096:
            br_m = re.search(r"(?m)^- Blocks-Release:\s*(\S+)\s*$", text)
        if br_m:
            br = br_m.group(1)
    # xprio 1b45el E-03: populate Item.priority from the plan's `- Priority:` line so the board LABELS
    # a plan's priority via the existing type-agnostic renderer (absent = None = no label). This does
    # NOT alter the shared attention sort key (core), which excludes priority for all trees today.
    pr = None
    if "Priority:" in text:
        pr_m = re.search(r"(?m)^- Priority:[ \t]*(\S+)[ \t]*$", text[:4096])
        if not pr_m and len(text) > 4096:
            pr_m = re.search(r"(?m)^- Priority:[ \t]*(\S+)[ \t]*$", text)
        if pr_m:
            pr = pr_m.group(1)
    d_kind, d_text = _extract_detail(text)
    rd = read_readiness(text)
    oqs, rqs = count_question_stats(text)
    exec_prog, valid_prog = _extract_checklist_progress(text)
    return Item(
        pid or "",
        rel,
        "plans",
        status,
        A.class_of("plans", status),
        None,
        lha,
        blocks_release=br,
        priority=pr,
        detail_kind=d_kind,
        detail_text=d_text,
        readiness=rd,
        oqs=oqs,
        rqs=rqs,
        exec_progress=exec_prog,
        valid_progress=valid_prog,
    ), drift


def _research_record(
    rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    drift: List[core.Drift] = []
    data = research_contract.parse_frontmatter(text)
    if not data or "status" not in data:
        drift.append(
            core.Drift(
                rel, "attention.missing-status", "no research frontmatter status"
            )
        )
        return None, drift
    # rstodo p3o9je: normalize the RAW frontmatter status to canonical (a legacy `intake` -> `todo`)
    # BEFORE the STATUSES membership check, native_status storage, and class_of lookup, so an
    # unmigrated `intake` doc classifies exactly as `todo` (READY, stale-reclass, color) through the
    # migration window and never raises attention.unknown-status.
    raw_status = str(data["status"])
    norm = research_contract.normalize_status(raw_status)
    if not norm.ok:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                A.escape_detail(f"research status {raw_status!r}"),
            )
        )
        return None, drift
    status = norm.value or raw_status
    rid = str(data.get("id", "")) if data.get("id") else ""
    lha = A.last_history_at(_history_section_lines(text))
    # xprio 6vgd0k E-04: populate Item.priority from the doc's `priority:` frontmatter key so the
    # board LABELS a research doc's priority via the existing renderer (absent = None = no label).
    # Shared sort key unchanged.
    pr_val = data.get("priority")
    pr = str(pr_val) if pr_val not in (None, "") else None
    br_val = (
        data.get("blocks-release")
        or data.get("blocks_release")
        or data.get("Blocks-Release")
    )
    br = str(br_val).strip() if br_val not in (None, "") else None
    d_kind, d_text = _extract_detail(text)
    rd = read_readiness(text)
    oqs, rqs = count_question_stats(text)
    return Item(
        rid,
        rel,
        "research",
        status,
        A.class_of("research", status),
        None,
        lha,
        priority=pr,
        blocks_release=br,
        detail_kind=d_kind,
        detail_text=d_text,
        readiness=rd,
        oqs=oqs,
        rqs=rqs,
    ), drift


def _backlog_record(
    rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    """Attention record for a backlog item. A `blocked` item carries its typed gate so the board
    renders `[gate kind: ref]` and the JSON includes it (IPD crv40v PR-002)."""

    from agent_workflows import backlog as backlog_mod

    drift: List[core.Drift] = []
    item = backlog_mod.parse_item(text)
    status = item.status
    if status is None:
        drift.append(core.Drift(rel, "attention.missing-status", "no backlog Status"))
        return None, drift
    if status not in backlog_mod.STATUSES:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                A.escape_detail(f"backlog status {status!r}"),
            )
        )
        return None, drift
    gate = None
    if status == "blocked" and item.gate_kind and item.gate_ref:
        gate = {"kind": item.gate_kind, "ref": item.gate_ref}
    lha = A.last_history_at(_history_section_lines(text))
    d_kind, d_text = _extract_detail(text)
    rd = read_readiness(text)
    oqs, rqs = count_question_stats(text)
    return Item(
        item.id or "",
        rel,
        "backlog",
        status,
        A.class_of("backlog", status),
        gate,
        lha,
        priority=item.priority,
        blocks_release=item.blocks_release,
        detail_kind=d_kind,
        detail_text=d_text,
        readiness=rd,
        oqs=oqs,
        rqs=rqs,
    ), drift


# --------------------------------------------------------------------------------------
# Stranded lanes (lanestrand-01 `pr5b0t` E-04/E-05/E-06)
# --------------------------------------------------------------------------------------
#
# THE ONE CROSS-TREE VIEW COULD NOT SEE UNINTEGRATED WORK. Measured before this landed: `aw attention
# --check` exited 0 while dozens of `aw/lane/*` branches held commits that had never reached main, and
# plan `03ie04` was paid for TWICE ($16.59 then $32.83) because the first lane stranded silently.
#
# THE VERDICT COMES FROM THE RUN RECORD, NEVER FROM A FILESYSTEM WALK, and `SCAN_ROOTS` is deliberately
# UNCHANGED. `.aw/worktrees` and `.aw/records/runs` stay outside the scan set: a verdict derived from
# today's filesystem reports a RECOVERED run clean and rewrites history, which is what `xtklpd`'s
# review measured. So lanes join at RENDER time from the run records, not as scanned files.
#
# THE PREDICATE IS NOT DEFINED HERE. `runner_shared.classify_lane_integration` owns it (one reader; see
# its docstring for why `holds_work` alone cannot answer "did it land"), and this module only renders
# and gates on the result.

#: The stable rule id for a stranded lane, in the house `location<TAB>rule<TAB>detail` form (spec F4).
#: STABLE because tests and agent remediation key on it.
LANE_STRANDED_RULE = "attention.lane-stranded"

#: The stable rule id for a lane whose landing question could not be answered. Separate from the
#: stranded rule so a consumer can tell "provably unintegrated" from "unprovable", which are different
#: human actions even though both fail the gate.
LANE_UNKNOWN_RULE = "attention.lane-unknown"


def lane_drift_severity(lane_state: str) -> str:
    """The `Drift` severity for a lane state. Both reportable states FAIL the gate.

    FAIL CLOSED, on `nuanaw` ask 3 and on the spec's G3. `artifact_core.drift_exit_code` exempts
    exactly `info`, so an `info` severity would report the lane and still exit 0, which is the
    self-contradiction (`valid: true` beside lost work) this whole surface exists to remove. UNKNOWN
    fails too rather than warning: a landing question we cannot answer is not evidence the work landed.
    """
    return "error"


def stranded_lane_drift(repo_root: Path) -> List[core.Drift]:
    """Every stranded (or unprovable) lane, as `Drift` records. Read-only; never touches git state.

    WHY A `Drift` AND NOT AN `Item`, which is the whole implementation question for E-05/E-06 and is
    settled by MEASUREMENT rather than taste. `render_json` computes `valid` as `len(drift) == 0`, and
    every `--check` exit path returns `core.drift_exit_code(drift)`. So emitting a stranded lane as a
    non-`info` `Drift` makes the payload's honesty and the gate's exit code follow AUTOMATICALLY and by
    the SAME mechanism, with no second definition of validity; an `Item`-only design would leave
    `valid: true` and `--check` at 0 beside a stranded lane.

    NO ABSOLUTE PATH REACHES EITHER SURFACE. `location` is the lane BRANCH (a git ref such as
    `aw/lane/03ie04`, safe by construction) and the worktree is rendered repository-relative through
    `runner_shared.lane_worktree_display`, which returns None rather than an absolute path. The
    recorded `preserved_worktree` is an absolute home path in most run items, and `integration_detail`
    embeds an absolute repository path, so NEITHER is printed.

    Returns `[]` on any failure to read the run records, which is the honest answer for a repository
    that has never run a driver: absence of run records is not evidence of a stranded lane.
    """
    try:
        from agent_workflows import run_viewer
        from agent_workflows import runner_shared as rs
    except Exception:
        return []

    target_root = _resolve_runs_repo_root(repo_root)
    try:
        run_dirs = run_viewer.discover_run_dirs(target_root)
    except Exception:
        return []
    if not run_dirs:
        return []

    states: List[Dict] = []
    for run_dir in run_dirs:
        state_file = run_dir / "state.json"
        if not state_file.is_file():
            continue
        # A LIVE run's lanes must not fail the gate: a driver in progress legitimately owns them, and a
        # check that reds during every normal run is a check that gets bypassed. The lane classifier
        # ALSO excludes a live-owned lane on `owner_live`, so this is belt and braces on the cheaper
        # signal (`driver.lock` holder liveness, the same one `get_active_runs_map` consumes).
        try:
            if run_viewer.driver_holder_state(run_dir) == run_viewer.HOLDER_LIVE:
                continue
        except Exception:
            continue
        try:
            states.append(json.loads(state_file.read_text(encoding="utf-8")))
        except Exception:
            continue
    if not states:
        return []

    try:
        from agent_workflows import worktree_lease

        with worktree_lease.memoize_worktrees(target_root):
            records = rs.stranded_lane_records(target_root, states)
    except Exception:
        return []

    out: List[core.Drift] = []
    for rec in records:
        branch = str(rec.get("branch") or rec.get("lane_id") or "(unnamed lane)")
        state = str(rec.get("lane_state") or rs.LANE_UNKNOWN)
        rule = LANE_STRANDED_RULE if state == rs.LANE_STRANDED else LANE_UNKNOWN_RULE
        bits = ["{0} lane".format(state)]
        if rec.get("id6"):
            bits.append("plan {0}".format(rec["id6"]))
        if rec.get("commits_ahead"):
            bits.append("{0} commit(s) beyond base".format(rec["commits_ahead"]))
        if rec.get("dirty"):
            bits.append("uncommitted changes")
        if rec.get("integration_signal"):
            bits.append("integration_signal={0}".format(rec["integration_signal"]))
        display = rs.lane_worktree_display(target_root, rec.get("worktree"))
        if display:
            bits.append("worktree {0}".format(display))
        if rec.get("run_id"):
            # ONE ROW PER LANE, so the row must say how many runs touched it: the per-branch collapse in
            # `stranded_lane_records` replaced N identical-in-substance rows with one, and dropping the
            # count would lose the fact that the lane recurred rather than merely reformat it.
            try:
                run_count = int(rec.get("run_count") or 1)
            except (TypeError, ValueError):
                run_count = 1
            if run_count > 1:
                bits.append(
                    "newest run {0} of {1} runs".format(rec["run_id"], run_count)
                )
            else:
                bits.append("run {0}".format(rec["run_id"]))
        detail = "{0}: {1}. {2}".format(
            "; ".join(bits),
            rec.get("why") or "",
            lane_remedy_hint(str(rec["id6"]) if rec.get("id6") else None),
        )
        out.append(
            core.Drift(
                branch,
                rule,
                A.escape_detail(detail),
                severity=lane_drift_severity(state),
            )
        )
    out.sort(key=lambda d: (d.location, d.rule))
    return out


#: The symbol whose presence PROVES `aw <host> integrate` is really wired, probed by
#: :func:`lane_remedy_hint`. NAMED AS A CONSTANT so the probe is observable: the previous probe was a
#: bare `hasattr` against `cmd_integrate`, a name NOTHING ELSE IN THE REPOSITORY REFERENCES, so when the
#: verb shipped under a different name the conditional froze in its pre-`rl67b0` state and kept printing
#: "no `aw integrate` verb exists yet" for a verb that existed. That UNOBSERVABILITY was the defect, not
#: the wrong string, which is why a test pins this name (plan `0ta5vg` E-06).
LANE_INTEGRATE_PROBE_SYMBOL = "handle_integrate_command"


def lane_remedy_hint(id6: Optional[str] = None) -> str:
    """The remedy to print beside a stranded lane. An alarm with no route trains its own dismissal.

    NAMES ONLY A VERB THAT EXISTS AT RUNTIME, which is the rule that survived unchanged; what changed is
    that the probe now names a symbol that is really there. `rl67b0` shipped the verb as
    `handle_integrate_command` (the CLI forwards `aw oc integrate` as REMAINDER args rather than binding
    a `cmd_*` function), so the old `cmd_integrate` probe could never be True. Do not print a verb that
    does not exist, and do not probe a name nothing else references.

    HOST-NEUTRAL BY DEFAULT: both hosts carry the verb (`oc_runipd` and `agy_runipd` both define
    `handle_integrate_command`), so the hint names `aw oc integrate` as the concrete route rather than
    claiming only one host has it.

    ``id6`` is OPTIONAL so the no-argument call keeps working; when given, the hint names the concrete
    command instead of a `<id6>` placeholder the reader must substitute.
    """
    try:
        from agent_workflows import cli as _cli  # noqa: F401
    except Exception:
        return "Recover it by hand: inspect the branch, then merge it."
    integrate_exists = False
    try:
        from agent_workflows import oc_runipd as _oc

        integrate_exists = hasattr(_oc, LANE_INTEGRATE_PROBE_SYMBOL)
    except Exception:
        integrate_exists = False
    if integrate_exists:
        return "Recover it with `aw oc integrate {0}`.".format(id6 if id6 else "<id6>")
    return (
        "Recover it by hand: `git log main..<branch>` to see the work, then merge that branch "
        "(no `aw integrate` verb exists yet)."
    )


def render_stranded_lane_section(drift: List[core.Drift]) -> str:
    """The LOUD human section for stranded lanes, or `""` when none. One row per lane."""
    from agent_workflows import runner_shared as rs

    lanes = [d for d in drift if d.rule in (LANE_STRANDED_RULE, LANE_UNKNOWN_RULE)]
    if not lanes:
        return ""
    header = (
        "## {0} LANES ({1}): work that never reached the integration target\n".format(
            rs.LANE_STRANDED, len(lanes)
        )
    )
    body = "".join("- {0}: {1}\n".format(d.location, d.detail) for d in lanes)
    return header + body


# --------------------------------------------------------------------------------------
# Renderers (deterministic)
# --------------------------------------------------------------------------------------


def render_json(items: List[Item], drift: List[core.Drift]) -> str:
    obj = {
        "schema_version": SCHEMA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "valid": len(drift) == 0,
        "items": [
            {
                "id": it.id,
                "path": it.path,
                "tree": it.tree,
                "native_status": it.native_status,
                "attention_class": it.attention_class,
                "gate": it.gate,
                "last_history_at": it.last_history_at,
                "priority": it.priority,
                "blocks_release": it.blocks_release,
                "readiness": it.readiness,
                "oqs": it.oqs,
                "rqs": it.rqs,
                "detail_kind": it.detail_kind,
                "detail_text": it.detail_text,
            }
            for it in items
        ],
        "violations": [
            {"location": d.location, "rule": d.rule, "detail": d.detail} for d in drift
        ],
        # lanestrand-01 (`pr5b0t`) E-05: the machine-readable stranded-lane set. APPENDED, never a
        # repurposed key, so an existing consumer parsing this payload is byte-unchanged in every
        # pre-existing field and every pre-existing key keeps its position.
        #
        # DERIVED FROM `drift`, NOT RE-COMPUTED. That is what makes `valid` (computed as
        # `len(drift) == 0` above) unable to contradict this list by construction: a stranded lane is
        # in the payload if and only if it is in the drift set that decided `valid` and decides the
        # `--check` exit code. A second derivation here could disagree, and only one of them would be
        # wrong at a time.
        #
        # `location` is a git BRANCH and never a path, so nothing absolute can reach this payload.
        "stranded_lanes": [
            {"branch": d.location, "rule": d.rule, "detail": d.detail}
            for d in drift
            if d.rule in (LANE_STRANDED_RULE, LANE_UNKNOWN_RULE)
        ],
    }
    # canonical: fixed key order (insertion order above), 2-space indent, sorted item keys off, LF, final newline
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


# xterm-256 palette indices for the five ATTENTION CLASSES. This is NOT a lifecycle status table
# and it is deliberately RETAINED (plan `f9t5hz` E-02): its keys are the `A.*` cross-tree attention
# class constants, and spec `uonrjg` Section 3 lists "attention classes" as an explicit NON-GOAL,
# so R10.3's "local `_STATUS_COLOR_256` lifecycle tables MUST be removed" does not reach it. It
# colors the section HEADERS (`## ready (12)`) by class and nothing else.
#
# THE OBVIOUS CHECK ON THIS TABLE IS A TRAP, recorded because an agent reading only the keys draws
# the wrong conclusion. All five `A.*` constants are BARE STRINGS whose values (`'active'`,
# `'ready'`, `'blocked'`, `'done'`, `'parked'`) are ALSO native status words in several trees, so a
# "do the keys look like statuses?" test answers YES for all five and deletes a vocabulary the spec
# protects. Trace the keys to the `A.*` constants, never pattern-match them.
#
# NO LIFECYCLE SITE CONSULTS THIS TABLE ANY MORE (E-02). It used to sit as the second rung of every
# lifecycle fallback chain (`_STATUS_COLOR_256.get(status, _CLASS_COLOR_256.get(cls, 244))`), which
# was invisible while the two palettes agreed and became a silent re-introduction of the class
# palette into lifecycle rendering the moment they diverged - which spec Section 5 makes them do
# (`active` moves to 220, `blocked` to 208, `done` to 46). The shared resolver now owns every
# lifecycle color, and an unrecognized status resolves `unknown` with a diagnostic (R10.4) rather
# than borrowing a class color.
_CLASS_COLOR_256 = {
    A.ACTIVE: 39,  # bright azure
    A.READY: 40,  # green
    A.BLOCKED: 203,  # salmon/red
    A.DONE: 244,  # gray
    A.PARKED: 244,  # gray
}

#: Bold blue for the tree-name SEGMENT OF A PATH. This is the "existing independent convention"
#: spec `uonrjg` Section 11 item 5 exempts, and the exemption is scoped to a PATH: coloring one
#: directory segment inside `.aw/records/backlog/open/x.md` adds no width and identifies the tree
#: within a longer string. It is NOT a licence to color a bare artifact TYPE word in a row, which
#: Section 9.1 says does not inherit lifecycle color and criterion A10 tests for directly; see
#: `_render_item_row` / `_render_table_row`, where the type column is now plain (E-03).
_TREE_COLOR_256 = 33  # bold blue for the tree-name path segment

#: The `lifecycle_style` FAMILY for each attention tree. The names already coincide (both vocabularies
#: use `plans`/`specs`/`backlog`/`research`/`releases`), so this is an explicit identity map rather
#: than a translation: naming it makes the coincidence a CHECKED fact instead of an assumption, and
#: gives a tree that is not a lifecycle family somewhere to be absent from.
_LIFECYCLE_FAMILY_BY_TREE = {
    # The five TRACKED trees (`A.TRACKED_TREES`), i.e. every tree that actually builds an `Item`.
    "plans": LS.FAMILY_PLANS,
    "specs": LS.FAMILY_SPECS,
    "backlog": LS.FAMILY_BACKLOG,
    "research": LS.FAMILY_RESEARCH,
    "releases": LS.FAMILY_RELEASES,
    # Trees `TREE_POLICY` EXCLUDES today, mapped anyway so that if one is ever tracked it resolves
    # through the shared table rather than through this module's unknown branch. `walkthroughs` and
    # `roadmaps` are `lifecycle_style`'s NO-LIFECYCLE families and therefore resolve `none` (`·`),
    # which is the spec Section 6.7 answer and NOT the same thing as `unknown` (R10.4).
    "prompts": LS.FAMILY_PROMPTS,
    "walkthroughs": LS.FAMILY_WALKTHROUGHS,
    "roadmaps": LS.FAMILY_ROADMAPS,
}


def _resolve_item_lifecycle(tree: str, native_status: str) -> LS.Resolved:
    """Resolve one item's lifecycle presentation through the SHARED resolver (spec R10.3).

    THE ONE LIFECYCLE RESOLUTION PATH IN THIS MODULE. Every rendered status word, id6, date, SetID
    and Order number takes its color from the `Resolved` this returns, so Section 9.1's "the glyph,
    id6, and status word use the same lifecycle color and weight" holds by CONSTRUCTION rather than
    by three call sites agreeing on a lookup.

    A TREE THAT IS NOT A LIFECYCLE FAMILY RESOLVES `unknown`, NOT A BORROWED CLASS COLOR. R10.4 makes
    that distinction load-bearing, and `term.resolve_lifecycle` RAISES `UnknownFamily` for a family it
    has no policy for, which would be a crash in a read-only view. So an unmapped tree is translated
    into the `unknown` stage here (`?`, gray 244, plus the resolver's own diagnostic shape) instead of
    propagating: a view that cannot classify a row must say so, not fail.
    """

    family = _LIFECYCLE_FAMILY_BY_TREE.get(tree)
    if family is None:
        return LS.Resolved(
            stage=LS.UNKNOWN,
            style=LS.style_for(LS.UNKNOWN),
            family=tree,
            native_status=native_status or None,
            diagnostic="attention tree {0!r} is not a lifecycle family".format(tree),
        )
    return T.resolve_lifecycle(family, native_status)


_SINGULAR_TYPE = {
    "plans": "plan",
    "specs": "spec",
    "prompts": "prompt",
    "research": "research",
    "backlog": "backlog",
    "walkthroughs": "walkthrough",
    "roadmaps": "roadmap",
    "comms": "comms",
    "actions": "action",
}

TYPE_ALIASES: dict[str, str] = {
    "plan": "plans",
    "plans": "plans",
    "ipd": "plans",
    "spec": "specs",
    "specs": "specs",
    "backlog": "backlog",
    "bk": "backlog",
    "research": "research",
    "survey": "research",
    "findings": "research",
    "release": "releases",
    "releases": "releases",
    "roadmap": "roadmaps",
    "roadmaps": "roadmaps",
    "walkthrough": "walkthroughs",
    "walkthroughs": "walkthroughs",
    "walkthr": "walkthroughs",
    "prompt": "prompts",
    "prompts": "prompts",
    "prompt-library": "prompts",
    "comms": "comms",
    "actions": "actions",
}


def parse_type_filters(raw_types: Sequence[str] | None) -> set[str]:
    """Parse a sequence of type arguments (supporting comma-separated strings and repeated flags)
    into a set of normalized canonical tree names (e.g. 'plans', 'specs', 'backlog').
    """
    if not raw_types:
        return set()
    result: set[str] = set()
    for raw in raw_types:
        if not raw:
            continue
        parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
        for p in parts:
            canonical = TYPE_ALIASES.get(p, p)
            result.add(canonical)
    return result


def parse_filter_tokens(raw_values: Sequence[str] | None) -> set[str]:
    """Parse a sequence of filter arguments (supporting comma-separated strings and repeated flags)
    into a set of normalized lowercase tokens.
    """
    if not raw_values:
        return set()
    result: set[str] = set()
    for raw in raw_values:
        if not raw:
            continue
        parts = [p.strip().lower() for p in str(raw).split(",") if p.strip()]
        result.update(parts)
    return result


def parse_status_filters(raw_statuses: Sequence[str] | None) -> set[str]:
    """Parse status filter arguments, normalizing hyphens and underscores."""
    tokens = parse_filter_tokens(raw_statuses)
    result: set[str] = set()
    for t in tokens:
        result.add(t)
        if "_" in t:
            result.add(t.replace("_", "-"))
        elif "-" in t:
            result.add(t.replace("-", "_"))
    return result


# READ-SIDE priority aliases, normalized at the PARSE boundary only (attcor `rkn8ya` E-06).
#
# `--priority` carries no argparse `choices`, and `matches_priority` does exact membership, so
# `aw att --priority med` silently returned 0 items instead of erroring: a filter that answers
# "nothing matches" to a typo is worse than one that refuses. `med` is already accepted by
# `PRIORITY_RANK` in this same module and appears in the board's own table docstring, so accepting it
# here REMOVES an internal inconsistency rather than inventing a new vocabulary.
#
# NORMALIZED AT PARSE TIME, DELIBERATELY, so exactly ONE vocabulary survives downstream:
# `attention_contract.PRIORITY_ORDER` stays the single vocabulary and `_PRIORITY_SORT_RANK` stays
# DERIVED from it (the comment at its definition records that a hardcoded second copy is the mistake
# `ipd_schema` already made). Neither is touched.
#
# READ-SIDE ONLY: `aw ipd set` / `aw specs set` / `aw backlog set` keep their argparse `choices`, so
# `med` can never be WRITTEN into an artifact. The alias is a convenience for asking a question, not
# a second spelling of a stored value.
# EXACTLY ONE ENTRY, and no speculative additions: `med` is the alias this module already accepts
# elsewhere (`PRIORITY_RANK`), which is the whole justification for accepting it. Inventing further
# spellings (`hi`, `lo`) would create vocabulary this repository uses nowhere else.
_PRIORITY_FILTER_ALIASES = {"med": "medium"}


def parse_priority_filters(raw_priorities: Sequence[str] | None) -> set[str]:
    """Parse priority filter arguments, normalizing the read-side aliases (e.g. `med` -> `medium`)."""
    tokens = parse_filter_tokens(raw_priorities)
    return {_PRIORITY_FILTER_ALIASES.get(t, t) for t in tokens}


def parse_blocking_filters(raw_blocking: Sequence[str] | None) -> set[str]:
    """Parse blocking filter arguments."""
    return parse_filter_tokens(raw_blocking)


def parse_readiness_filters(raw_readiness: Sequence[str] | None) -> set[str]:
    """Parse readiness filter arguments, normalizing hyphens and underscores."""
    tokens = parse_filter_tokens(raw_readiness)
    result: set[str] = set()
    for t in tokens:
        result.add(t)
        if "_" in t:
            result.add(t.replace("_", "-"))
        elif "-" in t:
            result.add(t.replace("-", "_"))
    return result


_RUN_STATUS_ALIASES = {
    "executed": "done",
    "reviewed": "done",
    "substantially-complete": "done",
    "completed": "done",
    "failed-safely": "failed",
    "interrupted": "failed",
    "dependency-blocked": "blocked",
    "integration-blocked": "blocked",
    "merge-conflict": "blocked",
}


def parse_run_status_filters(raw_run_statuses: Sequence[str] | None) -> set[str]:
    """Parse run status filter arguments, normalizing hyphens, underscores, and synonyms."""
    tokens = parse_filter_tokens(raw_run_statuses)
    result: set[str] = set()
    for t in tokens:
        result.add(t)
        if "_" in t:
            result.add(t.replace("_", "-"))
        elif "-" in t:
            result.add(t.replace("-", "_"))
        t_norm = t.replace("_", "-")
        if t_norm in _RUN_STATUS_ALIASES:
            result.add(_RUN_STATUS_ALIASES[t_norm])
    return result


def matches_status(it: Item, status_filters: set[str]) -> bool:
    """Return True if item matches any of the given status filters."""
    if not status_filters:
        return True
    ns = (it.native_status or "").lower()
    ac = (it.attention_class or "").lower()
    candidates = {
        ns,
        ns.replace("_", "-"),
        ns.replace("-", "_"),
        ac,
        ac.replace("_", "-"),
        ac.replace("-", "_"),
    }
    return bool(candidates & status_filters)


def matches_priority(it: Item, priority_filters: set[str]) -> bool:
    """Return True if item matches any of the given priority filters."""
    if not priority_filters:
        return True
    p = (it.priority or "").lower()
    if not p or p == "-":
        return "-" in priority_filters or "none" in priority_filters
    return p in priority_filters


@functools.lru_cache(maxsize=32)
def _get_planned_release_info(repo_root: Optional[Path]) -> Tuple[str, str]:
    if not repo_root:
        return "", ""
    try:
        from agent_workflows import releases as _releases

        desc = _releases.describe_planned_release(repo_root)
        if desc:
            return (desc[0] or "").lower(), (desc[1] or "").lower()
    except (AttributeError, OSError, ValueError):
        pass
    return "", ""


def matches_blocking(
    it: Item, blocking_filters: set[str], repo_root: Path | None = None
) -> bool:
    """Return True if item matches any of the given blocking filters."""
    if not blocking_filters:
        return True
    is_blk = bool(it.blocks_release and it.blocks_release != "-")
    raw_blk = (it.blocks_release or "").lower()
    resolved_ver = (
        _resolve_release_version(repo_root, it.blocks_release).lower() if is_blk else ""
    )
    planned_id, planned_ver = _get_planned_release_info(repo_root)

    for tok in blocking_filters:
        if tok in ("true", "yes", "1", "any", "blocking"):
            if is_blk:
                return True
        elif tok in ("false", "no", "0", "none", "-", "non-blocking"):
            if not is_blk:
                return True
        elif is_blk:
            tok_clean = tok.lstrip("v")
            raw_clean = raw_blk.lstrip("v")
            res_clean = resolved_ver.lstrip("v")
            plan_clean = planned_ver.lstrip("v")

            if tok == "next":
                # attcor `rkn8ya` E-04: `next` RESOLVES against the PLANNED release; it used to
                # `return True` unconditionally, so `--blocking next` matched every gated item no
                # matter which release it named (a shipped or a past one included).
                #
                # `next` is the SYMBOL for "the single planned release", which is exactly what
                # `releases.resolve_blocks_release`/`describe_planned_release` mean by it, so the
                # correct predicate is "this item gates the planned release". The reasoning below for
                # a version/id6 token already did this; only the `next` branch bypassed it.
                #
                # WHEN THERE IS NO PLANNED RELEASE, `next` MATCHES NOTHING, and that is the honest
                # answer rather than a behavior-preserving dodge: `next` names a release record that
                # does not exist, so no item can gate it. (`--blocking any` remains the way to ask
                # "gated on anything at all".)
                if not (planned_id or plan_clean):
                    continue
                if raw_blk == "next":
                    return True
                if planned_id and raw_blk == planned_id:
                    return True
                if plan_clean and res_clean == plan_clean:
                    return True
                continue
            if tok in (raw_blk, resolved_ver) or tok_clean in (raw_clean, res_clean):
                return True
            if plan_clean and tok_clean == plan_clean:
                if raw_blk in ("next", planned_id) or raw_clean == plan_clean:
                    return True
            if planned_id and tok == planned_id:
                if raw_blk in ("next", planned_id) or raw_clean == plan_clean:
                    return True
    return False


def matches_readiness(it: Item, readiness_filters: set[str]) -> bool:
    """Return True if item matches any of the given readiness filters."""
    if not readiness_filters:
        return True
    r = (it.readiness or "").lower()
    if not r or r == "-":
        return "-" in readiness_filters or "none" in readiness_filters
    r_norm = r.replace("_", "-")
    for tok in readiness_filters:
        tok_norm = tok.replace("_", "-")
        if tok_norm in (r, r_norm):
            return True
    return False


def matches_run_status(
    it: Item, run_status_filters: set[str], run_map: Optional[Dict[str, str]]
) -> bool:
    """Return True if item matches any of the given run status filters."""
    if not run_status_filters:
        return True
    st = _item_run_status(it, run_map)
    st = (st or "").lower()
    has_run = bool(st and st != "-")
    if not has_run:
        return bool(run_status_filters & {"-", "none", "no", "false"})
    if "any" in run_status_filters:
        return True
    candidates = {
        st,
        st.replace("_", "-"),
        st.replace("-", "_"),
    }
    return bool(candidates & run_status_filters)


def _colorize_tree_segment(term: T.Term, path: str, tree: str) -> str:
    """Color the tree-name directory segment WITHIN ``path`` bold blue, in place.

    e.g. ``.agents/backlog/open/x.md`` with tree ``backlog`` colors just the ``backlog``
    segment (slashes stay uncolored), adding no width. If the tree name is not a distinct
    ``/tree/`` path segment (some logical trees live under a differently-named directory),
    the path is returned uncolored rather than mis-coloring a partial match.
    """
    seg = f"/{tree}/"
    idx = path.find(seg)
    if idx == -1:
        return path
    start = idx + 1  # first char of the tree name (after the leading slash)
    end = start + len(tree)
    return path[:start] + term.color256(tree, _TREE_COLOR_256, bold=True) + path[end:]


def setup_needed(repo_root: Path) -> bool:
    """setupmarker Order 01 (was awdoctor Order 02): True iff the per-repo reminder marker
    `.aw/setup-repo-needed.md` is present (written by `aw install`, cleared by the `/setup-repo`
    workflow's successful terminal pass or by the user deleting it; NOT by `aw setup`, which is the
    machine-wide install wizard and never touches the marker). DERIVED read-only from the marker;
    NEVER creates anything. Replaces the old open-`setup-repo`-action check (the ledger was
    deleted)."""
    try:
        return (Path(repo_root) / ".aw" / "setup-repo-needed.md").is_file()
    except Exception:
        return False


def release_blockers(items: List[Item], repo_root: Path) -> List[Item]:
    """awdoctor Order 02: items carrying a `- Blocks-Release: next|<id6>` field that are still LIVE.
    Reads the field from each item's file (the awrelease Set defines it). Returns the blocking items.

    Both TERMINAL classes are excluded, not just ``DONE``. A retired artifact keeps its
    ``Blocks-Release`` field on purpose, because the field records what the artifact was FOR and
    erasing it would falsify the record; but a superseded plan or a parked backlog item cannot gate a
    release, since nobody is going to do it. Skipping only ``DONE`` counted a plan retired to
    ``superseded/`` as an outstanding blocker, which is how a split plan kept appearing in the
    release-blocker list after its replacements were filed."""
    out: List[Item] = []
    for it in items:
        if it.attention_class in (A.DONE, A.PARKED):
            continue
        if it.blocks_release and it.blocks_release != "-":
            out.append(it)
    return out


_STEM_RE = re.compile(r"^(\d{8}-[a-z0-9-]+?-\d{2}-[0-9a-z]{6})")
_FACET_STRIP_RE = re.compile(r"(\.[a-z0-9-]+)*\.md$")


def _identity_stem(path: str) -> str:
    """awdoctorfix Order 02: the compact, tree-independent identity of a board line's file:
    `YYYYMMDD-<setid>-NN-<id6>` when the basename matches the clustering grammar, else the basename
    with its trailing `.md` / `.<type>.md` facet(s) stripped (e.g. `setup-repo-v1`)."""
    base = path.replace("\\", "/").rsplit("/", 1)[-1]
    m = _STEM_RE.match(base)
    if m:
        return m.group(1)
    return _FACET_STRIP_RE.sub("", base)


def _shared_gate_ref(items: Sequence["Item"], *, long: bool) -> str:
    """The ONE gate ref shared by every gated item in ``items``, or '' when there is no single one.

    THE FOLD DECISION, in one place, because the section header and the item rows must agree: the
    header hoists this ref only when it is shared, and each row suppresses its own gate suffix only
    when the header hoisted it. Deriving that twice is how the two drifted before, with the header
    folding while every row still repeated the ref, so the hoist added a line instead of removing
    noise.

    Returns '' when the group has no gate, only ONE gated item, several distinct refs, or a mix of
    gated and ungated items. Two of those bear explaining. A SINGLE item is not folded because the
    hoist trades one row suffix for one header line and saves nothing, while moving the ref away from
    the row it describes. The MIXED case is excluded because hoisting a ref into a header that also
    covers ungated rows would attribute a gate to items that do not have one.
    """
    gated = [it for it in items if it.gate]
    if len(gated) < 2 or len(gated) != len(items):
        return ""
    refs = {
        _gate_ref_display(A.escape_detail((it.gate or {}).get("ref", "")), long=long)
        for it in gated
    }
    refs.discard("")
    return next(iter(refs)) if len(refs) == 1 else ""


def _gate_ref_display(ref: str, *, long: bool) -> str:
    """A gate ref shortened for the compact board, or returned verbatim.

    The board's identity column already honors `--long` (compact `_identity_stem` by default, full
    path with `--long`), and the gate ref did NOT: it always printed the raw `Gate-Ref:` value, so a
    row showing a 30-char compact identity carried a 110-char repo-relative path for its gate. This
    applies the SAME rule to the ref so one flag governs both.

    ONLY a ref that is actually a path inside the records tree is compacted, which is why this is not
    just `_identity_stem`. A gate ref is a TYPED reference whose kind may be `todo`, `issue`, `date`,
    `decision`, or `external`, so most refs are not paths at all: `TODO.md` must stay `TODO.md` (a
    stem would render it as a bare `TODO`, naming a file that does not exist) and an issue reference
    or a date must survive byte-for-byte. The test is a directory separator, so only a genuinely
    nested path is shortened.
    """
    text = (ref or "").strip()
    if long or "/" not in text.replace("\\", "/"):
        return text
    return _identity_stem(text)


def _common_dir_prefix(paths: List[str]) -> str:
    """The common directory prefix (posix, trailing '/') shared by all paths, or '' if none.
    awdoctor Order 01: folded into a colored section header so per-item lines can be bare names."""
    if not paths:
        return ""
    import posixpath

    norm = [p.replace("\\", "/") for p in paths]
    dirs = [p.rsplit("/", 1)[0] if "/" in p else "" for p in norm]
    common = posixpath.commonpath(dirs) if all(dirs) else ""
    return (common + "/") if common else ""


# awdoctorfix Order 03: trees with no workflow-history lifecycle (research is commonly at todo with
# no history; actions carry status, not a history block) - a None last_history_at is NORMAL there, so
# suppress the `?` unknown-age marker rather than showing noise.
_HISTORYLESS_TREES = {"actions", "research"}


def _age_marker(last_history_at: Optional[str], tree: str = "") -> str:
    """awdoctor Order 01 + awdoctorfix Order 03: a compact staleness marker from last_history_at.
    '!' when older than ~30 days, '?' when unknown (None) EXCEPT on a history-less tree (returns ''),
    else '' (recent). Deterministic: compares ISO dates only."""
    if last_history_at is None:
        return "" if tree in _HISTORYLESS_TREES else "?"
    try:
        from datetime import date

        y, m, d = (int(x) for x in last_history_at.split("-")[:3])
        age_days = (date.today() - date(y, m, d)).days
        return "!" if age_days > 30 else ""
    except (ValueError, TypeError):
        return "?"


def _render_item_row(
    it: Item,
    cls: str,
    term: T.Term,
    colored: bool,
    long: bool,
    details: bool = False,
    gate_in_header: bool = False,
    runs_mode: bool = False,
    run_state: Optional[str] = None,
) -> str:
    """Render ONE board row for an item, in the compact columnar human form (colored) or the
    stable machine form (uncolored). Extracted so the release-blockers section renders items
    identically to the active/ready/blocked sections, not as raw paths.

    ``gate_in_header`` is True only when the caller ALREADY hoisted this group's single shared gate
    ref into the section header, in which case repeating it on every row is the noise the hoist
    exists to remove. It is passed explicitly rather than re-derived from ``cls`` because the two
    conditions are different: the hoist requires the whole group to share ONE ref, so a blocked group
    with several distinct refs is not folded and each row must still name its own gate.
    """
    status_word = it.native_status
    if colored:
        # THE SHARED RESOLVER, not a local table (spec `uonrjg` R10.3). The lifecycle marker, the
        # status word and (below) the identity columns all take their color and weight from this ONE
        # `Resolved`, which is what makes Section 9.1's "same lifecycle color and weight" structural.
        resolved = _resolve_item_lifecycle(it.tree, it.native_status)
        marker = term.format_lifecycle_marker(resolved, width=2)
        status_txt = term.style_lifecycle_text(status_word, resolved)
        # PADDED BY VISIBLE COLUMNS (Section 9.4), never by `len()` on styled text.
        status_padded = status_txt + (" " * max(0, 12 - T.visible_width(status_word)))
        age = _age_marker(it.last_history_at, it.tree)
        gate_glyph = "#" if it.gate else ""
        rb_glyph = ">" if it.blocks_release else ""
        blk = (age + gate_glyph + rb_glyph).strip()
        lead = f"{blk:<3}" if blk else "   "
        if long:
            path_txt = _colorize_tree_segment(term, it.path, it.tree)
            type_prefix = ""
        else:
            path_txt = _identity_stem(it.path)
            type_word = _SINGULAR_TYPE.get(it.tree, it.tree)
            # THE ARTIFACT TYPE CARRIES NO COLOR (criterion A10; Section 9.1 "The artifact type and
            # title do not inherit lifecycle color"). It used to be painted `_TREE_COLOR_256` bold,
            # and Section 11 item 5's "existing independent convention" exemption does NOT stretch to
            # cover it: that convention is for the tree SEGMENT OF A PATH (`_colorize_tree_segment`),
            # and a bare type word in a row is not a path. Coloring it made A10 untestable here.
            type_prefix = type_word + (" " * max(0, 10 - len(type_word))) + "  "
        inline_gate = ""
        if it.gate and not gate_in_header:
            g = it.gate
            ref_txt = _gate_ref_display(
                A.escape_detail(g.get("ref", "")), long=bool(long)
            )
            inline_gate = f"  [gate {g.get('kind')}: {ref_txt}]"
        run_txt = ""
        if runs_mode and run_state and run_state != "-":
            run_code = {
                "running": 51,
                "queued": 220,
                "merging": 201,
                "done": 40,
                "failed": 196,
                "blocked": 214,
            }.get(run_state, 244)
            run_txt = "  " + term.color256(f"[run:{run_state}]", run_code, bold=True)
        prio = ""
        if it.priority:
            pcode = {"high": 196, "medium": 214, "low": 244}.get(it.priority, 244)
            prio = "  " + term.color256(f"[{it.priority}]", pcode, bold=True)
        blocking = ""
        if it.blocks_release:
            blocking = "  " + term.color256("[blocking]", 196, bold=True)
        # The GLYPH IMMEDIATELY PRECEDES THE STATUS WORD (Section 9.1: "glyph MUST immediately
        # precede either id6 or status so its referent is obvious"), and it is padded by RENDERED
        # width by `format_lifecycle_marker`, so the two glyphs carrying U+FE0E (`⚠︎`, `↩︎`) occupy
        # the same column count as the single-codepoint ones.
        line = f"- {lead}{marker} {status_padded}  {type_prefix}{path_txt}{run_txt}{prio}{blocking}{inline_gate}"
        if details and it.detail_text:
            tag = it.detail_kind or "summary"
            tag_txt = term.color256(f"{tag}:", 244)
            detail_txt = term.color256(it.detail_text, 250)
            line += f"\n      {tag_txt} {detail_txt}"
        return line
    suffix = ""
    if it.gate:
        g = it.gate
        suffix = f"  [gate {g.get('kind')}: {A.escape_detail(g.get('ref', ''))}]"
    run_sfx = ""
    if runs_mode and run_state and run_state != "-":
        run_sfx = f"  [run: {run_state}]"
    line = f"- [{it.tree}] {it.path} ({status_word}){run_sfx}{suffix}"
    if details and it.detail_text:
        tag = it.detail_kind or "summary"
        line += f"\n      {tag}: {it.detail_text}"
    return line


@functools.lru_cache(maxsize=256)
def _resolve_release_version(repo_root: Optional[Path], val: Optional[str]) -> str:
    """Resolve a Blocks-Release value to a concrete release version string (e.g. '2.0.0'),
    or '-' if absent/None."""
    if not val or val == "-":
        return "-"
    if repo_root:
        try:
            from agent_workflows import releases as _releases

            p = _releases.resolve_release(repo_root, val)
            if p and p.is_file():
                m = _releases._VERSION_RE.search(p.read_text(encoding="utf-8"))
                if m:
                    return m.group(1)
            if val == "next":
                desc = _releases.describe_planned_release(repo_root)
                if desc and desc[1] and desc[1] != "?":
                    return desc[1]
            rec = _releases.get_release(repo_root, val)
            if rec and rec.version:
                return rec.version
        except Exception:
            pass
    return val


PRIORITY_RANK = {"": 0, "-": 0, "none": 0, "low": 1, "medium": 2, "med": 2, "high": 3}


_ID6_IN_NAME_RE = re.compile(r"-([0-9a-z]{6})-")
_IDENTITY_PARTS_RE = re.compile(
    r"^(\d{8})-([a-z0-9-]+?)-(\d{2})-([0-9a-z]{6})(?:-|\.|$)"
)
_LEGACY_SPEC_RE = re.compile(r"^(\d{8})-\d{4}-(\d{2})-([a-z0-9-]+)")


def extract_id6(it: Item) -> Optional[str]:
    """Extract id6 for an item, from it.id or filename."""
    if it.id and it.id != "-":
        return it.id
    _, _, _, id6 = _extract_identity_parts(it)
    if id6 and id6 != "-":
        return id6
    return None


def _extract_identity_parts(it: Item) -> Tuple[str, str, str, str]:
    """Extract (Date, SetID, Num, ID6) from an Item's path and metadata."""
    base = it.path.replace("\\", "/").rsplit("/", 1)[-1]
    m_leg = _LEGACY_SPEC_RE.match(base)
    if m_leg:
        return m_leg.group(1), m_leg.group(3), m_leg.group(2), it.id or "-"
    m = _IDENTITY_PARTS_RE.match(base)
    if m:
        return m.group(1), m.group(2), m.group(3), it.id or m.group(4)
    date = base[:8] if len(base) >= 8 and base[:8].isdigit() else "-"
    raw_stem = _FACET_STRIP_RE.sub("", base)
    set_id = raw_stem if raw_stem else "-"
    num = "-"
    id6 = it.id if it.id else "-"
    return date, set_id, num, id6


def _item_run_status(it: Item, run_map: Optional[Dict[str, str]]) -> Optional[str]:
    """Look up an item's run status in run_map using id, id6 stem, path, or filename."""
    if not run_map:
        return None
    _, _, _, it_id6 = _extract_identity_parts(it)
    for cand in (it.id, it_id6, it.path, Path(it.path).name):
        if cand and cand in run_map:
            return run_map[cand]
    return None


def _color_dep_id(dep: str, target: Optional[Item], term: T.Term, colored: bool) -> str:
    """Color a dependency id6 to match the lifecycle color of its TARGET's status.

    THIS IS A COMPACT id6 REFERENCE (spec Section 9.2): an id6 standing alone, carrying its
    artifact's lifecycle stage, and it takes the SAME treatment the target's own row gives its
    status word, through the shared resolver (R10.3).

    An UNMATCHED dependency stays neutral gray, and that is deliberately NOT the `unknown` stage:
    `unknown` means "this artifact has a lifecycle I could not read", whereas an unmatched id6 means
    no artifact was found at all, so there is no lifecycle to report and painting `?` here would
    claim there is.
    """
    if not colored:
        return dep
    if target is None:
        return term.color256(dep, 244)
    resolved = _resolve_item_lifecycle(target.tree, target.native_status)
    return term.style_lifecycle_text(dep, resolved)


def _extract_dependency_id6s(it: Item) -> List[str]:
    """Extract ordered unique dependency id6 strings for an item."""
    ids: List[str] = []
    seen: set = set()

    def _add(cand: str):
        if core.is_valid_id6(cand) and cand not in seen:
            seen.add(cand)
            ids.append(cand)

    if it.item_dependencies:
        for dep in it.item_dependencies:
            cand = dep.rsplit(":", 1)[-1].strip()
            _add(cand)
    if it.gate and isinstance(it.gate, dict):
        ref = str(it.gate.get("ref", "")).strip()
        if core.is_valid_id6(ref):
            _add(ref)
        else:
            m = _ID6_IN_NAME_RE.search(ref)
            if m:
                _add(m.group(1))

    return ids


def _resolve_runs_repo_root(repo_root: Path) -> Path:
    """Resolve the repository root that owns runs (handling git worktrees)."""
    from agent_workflows.runner_shared import state_root

    if state_root(repo_root).is_dir():
        return repo_root
    git_ref = repo_root / ".git"
    if git_ref.is_file():
        try:
            txt = git_ref.read_text(encoding="utf-8").strip()
            if txt.startswith("gitdir:"):
                gdir = Path(txt.split(":", 1)[1].strip()).resolve()
                candidate = gdir.parent.parent.parent
                if state_root(candidate).is_dir():
                    return candidate
        except Exception:
            pass
    if ".aw/worktrees" in str(repo_root.resolve()):
        for parent in repo_root.resolve().parents:
            if state_root(parent).is_dir():
                return parent
    return repo_root


def get_active_runs_map(repo_root: Path) -> Dict[str, str]:
    """Scan active runner sessions and return a mapping of id6/path to runner state.

    Only live runs (whose driver process currently holds driver.lock) are inspected.
    States are mapped to: 'running', 'queued', 'merging', 'done', 'failed', 'blocked'.
    """
    from agent_workflows import run_viewer

    run_map: Dict[str, str] = {}
    target_root = _resolve_runs_repo_root(repo_root)
    try:
        runs = run_viewer.discover_run_dirs(target_root)
    except Exception:
        return run_map

    live_runs = [
        r for r in runs if run_viewer.driver_holder_state(r) == run_viewer.HOLDER_LIVE
    ]
    if not live_runs:
        return run_map

    priority_order = {
        "running": 6,
        "merging": 5,
        "queued": 4,
        "done": 3,
        "blocked": 2,
        "failed": 1,
    }

    for run_dir in live_runs:
        state_file = run_dir / "state.json"
        if not state_file.is_file():
            continue
        try:
            state_data = json.loads(state_file.read_text(encoding="utf-8"))
            queue = state_data.get("queue") or []
            for item in queue:
                id6 = item.get("id6")
                cfg_file = item.get("configured_file")
                raw_st = (item.get("status") or "").lower()

                if raw_st == "running":
                    mapped = "running"
                elif raw_st == "merging":
                    mapped = "merging"
                elif raw_st == "queued":
                    mapped = "queued"
                elif raw_st in (
                    "executed",
                    "reviewed",
                    "substantially-complete",
                    "done",
                    "completed",
                ):
                    mapped = "done"
                elif raw_st in ("failed", "failed-safely", "interrupted"):
                    mapped = "failed"
                elif raw_st in (
                    "blocked",
                    "dependency-blocked",
                    "integration-blocked",
                    "merge-conflict",
                ):
                    mapped = "blocked"
                else:
                    mapped = raw_st[:7] if raw_st else "-"

                new_prio = priority_order.get(mapped, 0)

                keys_to_update = []
                if id6:
                    keys_to_update.append(id6)
                if cfg_file:
                    keys_to_update.append(cfg_file)
                    keys_to_update.append(Path(cfg_file).name)

                for k in keys_to_update:
                    curr = run_map.get(k)
                    curr_prio = priority_order.get(curr, 0) if curr else -1
                    if new_prio >= curr_prio:
                        run_map[k] = mapped
        except Exception:
            continue

    return run_map


# Status words whose 8-character TRUNCATION collides with another real status, mapped to a distinct
# 8-character abbreviation (attcor `rkn8ya` E-11a).
#
# THE COLLISION: `implementing` and `implemented` both slice to `implemen`, so the table could not
# distinguish ACTIVE work from FINISHED work. Color does distinguish them (`_resolve_item_lifecycle`
# gives them different lifecycle stages), but ONLY on a color TTY: `--no-color` and every piped or
# machine read saw one identical word for two opposite states.
#
# ABBREVIATED RATHER THAN WIDENED, deliberately. The Status column's width is pinned at 8 by the
# header (`"Status".ljust(8)`) and by an exact-line table snapshot test; widening it would shift every
# column in every row. Only the COLLIDING pair is remapped, so `not-exec`, `supersed`, `to-revie`,
# `reviewed`, `approved`, `executed`, `graduate` and every other truncation are byte-unchanged.
# The two abbreviations share the stem `implmnt` and differ in the FINAL LETTER, which carries the
# grammatical distinction the full words carry: `g` for the gerund (implementinG, in progress) and `d`
# for the past participle (implementeD, finished).
_STATUS_ABBREV = {
    "implementing": "implmntg",
    "implemented": "implmntd",
}


def _abbrev_status(native_status: str) -> str:
    """The <=8-character Status-column word for a native status, disambiguating 8-char collisions."""

    st = native_status or ""
    return _STATUS_ABBREV.get(st.lower(), st[:8])


# The readiness word that collides at the column's 9-character width (attcor `rkn8ya` E-11b).
# `go-pending-approval` sliced to `go-pendin`, indistinguishable from a cleared `go` to a reader and
# (before this fix) identically colored. The `?` marks the approval as still OUTSTANDING.
_READINESS_ABBREV = {"go-pending-approval": "go-pend?"}


def _abbrev_readiness(readiness: Optional[str]) -> str:
    """The <=9-character Readiness-column word, disambiguating the 9-char collision. `-` when absent."""

    rd = readiness or "-"
    return _READINESS_ABBREV.get(rd.lower(), rd[:9])


def _render_table_row(
    it: Item,
    term: T.Term,
    colored: bool,
    long: bool,
    details: bool = False,
    repo_root: Optional[Path] = None,
    gate_in_header: bool = False,
    set_w: int = 5,
    num_w: int = 2,
    oq_w: int = 3,
    exec_w: int = 4,
    valid_w: int = 5,
    id_map: Optional[Dict[str, Item]] = None,
    runs_mode: bool = False,
    run_state: Optional[str] = None,
) -> str:
    st_raw = _abbrev_status(it.native_status)
    # ONE resolution per row, from the shared resolver (R10.3). Computed even when `colored` is
    # False so the uncolored path takes the SAME glyph, which keeps the plain table a
    # character-for-character strip of the colored one (a property `test_attention` asserts).
    resolved = _resolve_item_lifecycle(it.tree, it.native_status)
    if colored:
        st_styled = term.style_lifecycle_text(st_raw, resolved)
    else:
        st_styled = st_raw
    # THE GLYPH LIVES INSIDE THE STATUS COLUMN, immediately preceding the status word (Section 9.1:
    # "glyph MUST immediately precede either id6 or status so its referent is obvious"). Folded into
    # the existing column rather than added as a new one so Section 12's "existing column order MUST
    # be preserved" holds literally: the column COUNT and their order are unchanged, and only the
    # Status column's width grows from 8 to 10. `format_lifecycle_marker` pads by RENDERED width, so
    # `⚠︎` (2 code points, 1 column) occupies the same 2 columns as `◕` (1 and 1).
    st_marker = term.format_lifecycle_marker(resolved, width=2, style=colored)
    st_col = st_marker + st_styled + (" " * (8 - T.visible_width(st_raw)))

    if runs_mode:
        run_raw = (run_state or "-")[:7]
        if colored:
            if run_raw == "-":
                run_styled = term.color256("-", 244)
            elif run_raw == "running":
                run_styled = term.color256(run_raw, 51, bold=True)
            elif run_raw == "queued":
                run_styled = term.color256(run_raw, 220, bold=False)
            elif run_raw == "merging":
                run_styled = term.color256(run_raw, 201, bold=True)
            elif run_raw == "done":
                run_styled = term.color256(run_raw, 40, bold=True)
            elif run_raw == "failed":
                run_styled = term.color256(run_raw, 196, bold=True)
            elif run_raw == "blocked":
                run_styled = term.color256(run_raw, 214, bold=False)
            else:
                run_styled = term.color256(run_raw, 244)
        else:
            run_styled = run_raw
        run_pad = " " * (7 - len(run_raw))
        run_col = f"{run_styled}{run_pad}"

    type_word = _SINGULAR_TYPE.get(it.tree, it.tree)
    tp_raw = type_word[:8]
    # THE TYPE COLUMN CARRIES NO COLOR (criterion A10). See `_render_item_row` for the full reasoning:
    # Section 9.1 says the artifact type does not inherit lifecycle color, and Section 11 item 5's
    # "existing independent convention" exemption covers `_TREE_COLOR_256` on a PATH SEGMENT, not a
    # bare type word in a row.
    tp_styled = tp_raw
    tp_col = tp_styled + (" " * (8 - len(tp_raw)))

    blk_ver = _resolve_release_version(repo_root, it.blocks_release)
    blk_raw = blk_ver[:6]
    left_pad = " " * (6 - len(blk_raw))
    if colored:
        if blk_raw != "-":
            blk_styled = term.color256(blk_raw, 196, bold=True)
        else:
            blk_styled = term.color256(blk_raw, 244)
    else:
        blk_styled = blk_raw
    blk_col = f"{left_pad}{blk_styled}"

    prio_raw = (it.priority or "-")[:8]
    if colored:
        if prio_raw != "-":
            pcode = {"high": 196, "medium": 214, "low": 244}.get(
                (it.priority or "").lower(), 244
            )
            prio_styled = term.color256(prio_raw, pcode, bold=True)
        else:
            prio_styled = term.color256(prio_raw, 244)
    else:
        prio_styled = prio_raw
    prio_col = prio_styled + (" " * (8 - len(prio_raw)))

    # attcor `rkn8ya` E-11b: the readiness cell, fixed in BOTH its text and its color.
    #
    # TEXT: `go-pending-approval` used to slice to `go-pendin`, which reads as a truncated `go`. It now
    # renders the distinct abbreviation `go-pend?`, whose trailing `?` says an approval is still
    # OUTSTANDING. The width stays 9 so no column moves.
    #
    # COLOR: the old code ran a SUBSTRING test over the 9-char slice (`"go" in lower and "no" not in
    # lower`), so `go-pendin` took 114 - the SAME green as a cleared `go`. An UNAPPROVED plan therefore
    # rendered as approved, which misreports an approval state and is the more serious half of this
    # fix. The colour now comes from the SHARED resolver (`lifecycle_style.resolve_readiness`), which
    # already maps the three readiness words to three DISTINCT stages (`go` -> ready,
    # `go-pending-approval` -> authority-queued, `no-go` -> blocked), so the distinction cannot be
    # re-lost by a heuristic and the readiness cell agrees with every other lifecycle colour in the row.
    rd_raw = _abbrev_readiness(it.readiness)
    if colored:
        if rd_raw != "-":
            rd_styled = term.style_lifecycle_text(
                rd_raw, LS.resolve_readiness(it.readiness)
            )
        else:
            rd_styled = term.color256(rd_raw, 244)
    else:
        rd_styled = rd_raw
    rd_col = rd_styled + (" " * (9 - T.visible_width(rd_raw)))

    oq_cnt = getattr(it, "oqs", 0) or 0
    rq_cnt = getattr(it, "rqs", 0) or 0
    tot_q = oq_cnt + rq_cnt
    if tot_q > 0:
        oq_raw = f"{oq_cnt}/{tot_q}"
        if colored:
            if oq_cnt == 0:
                oq_styled = term.color256(oq_raw, 40, bold=True)
            else:
                oq_styled = term.color256(oq_raw, 214, bold=True)
        else:
            oq_styled = oq_raw
    else:
        oq_raw = "-"
        oq_styled = term.color256("-", 244) if colored else "-"
    oq_left_pad = " " * max(0, oq_w - len(oq_raw))
    oq_col = f"{oq_left_pad}{oq_styled}"

    exec_prog = getattr(it, "exec_progress", None)
    if exec_prog and exec_prog[1] > 0:
        exec_raw = f"{exec_prog[0]}/{exec_prog[1]}"
        if colored:
            if exec_prog[0] == exec_prog[1]:
                exec_styled = term.color256(exec_raw, 40, bold=True)
            elif exec_prog[0] > 0:
                exec_styled = term.color256(exec_raw, 214, bold=True)
            else:
                exec_styled = term.color256(exec_raw, 244)
        else:
            exec_styled = exec_raw
    else:
        exec_raw = "-"
        exec_styled = term.color256("-", 244) if colored else "-"
    exec_left_pad = " " * max(0, exec_w - len(exec_raw))
    exec_col = f"{exec_left_pad}{exec_styled}"

    valid_prog = getattr(it, "valid_progress", None)
    if valid_prog and valid_prog[1] > 0:
        valid_raw = f"{valid_prog[0]}/{valid_prog[1]}"
        if colored:
            if valid_prog[0] == valid_prog[1]:
                valid_styled = term.color256(valid_raw, 40, bold=True)
            elif valid_prog[0] > 0:
                valid_styled = term.color256(valid_raw, 214, bold=True)
            else:
                valid_styled = term.color256(valid_raw, 244)
        else:
            valid_styled = valid_raw
    else:
        valid_raw = "-"
        valid_styled = term.color256("-", 244) if colored else "-"
    valid_left_pad = " " * max(0, valid_w - len(valid_raw))
    valid_col = f"{valid_left_pad}{valid_styled}"

    date, set_id, num, id6 = _extract_identity_parts(it)

    # THE FOUR IDENTITY COLUMNS TAKE THE SAME `resolved` AS THE STATUS WORD AND THE GLYPH, which is
    # what makes criterion A10's "glyph, id6, and status use the same resolved color and bold flag"
    # true by construction here: all three route through the one `style_lifecycle_text` call shape
    # with the one `Resolved`, so they cannot diverge.
    #
    # DATE, SetID AND N ARE KEPT ON THAT TREATMENT rather than being neutralized with the type column,
    # and the distinction is the spec's own. Section 9.1 and criterion A10 name the artifact TYPE,
    # TITLE and PATH as the cells that must NOT be lifecycle-colored, and these three are none of
    # those: they are FACETS OF THE ARTIFACT'S IDENTITY parsed out of the same filename the id6 comes
    # from (`_extract_identity_parts`), displayed as separate columns only because this table splits
    # the identity. Coloring them with the id6 is the "existing independent convention" Section 11
    # item 5 permits, it is a shipped contract (`tests/test_attention.py` asserts Date, SetID and ID6
    # all carry the status color), and Section 12 requires an existing stable contract be preserved
    # absent a separately reviewed interface change. The `-` sentinel stays neutral gray because an
    # absent facet has no lifecycle to report.
    date_raw = date[:8]
    if colored and date_raw == "-":
        date_styled = term.color256("-", 244)
    elif colored:
        date_styled = term.style_lifecycle_text(date_raw, resolved)
    else:
        date_styled = date_raw
    date_pad = " " * (8 - len(date_raw))
    date_col = f"{date_styled}{date_pad}"

    set_val = it.path if long else set_id
    if colored and long:
        # Under `--long` this column holds the PATH, which A10 says is not lifecycle-colored; the
        # tree SEGMENT keeps its own independent convention (Section 11 item 5).
        set_styled = _colorize_tree_segment(term, it.path, it.tree)
    elif colored and set_val == "-":
        set_styled = term.color256("-", 244)
    elif colored:
        set_styled = term.style_lifecycle_text(set_val, resolved)
    else:
        set_styled = set_val
    set_pad = " " * max(0, set_w - len(set_val))
    set_col = f"{set_styled}{set_pad}"

    num_raw = num[:num_w]
    if colored and num_raw == "-":
        num_styled = term.color256("-", 244)
    elif colored:
        num_styled = term.style_lifecycle_text(num_raw, resolved)
    else:
        num_styled = num_raw
    num_pad = " " * max(0, num_w - len(num_raw))
    num_col = f"{num_styled}{num_pad}"

    id6_raw = id6[:6]
    if colored and id6_raw == "-":
        id6_styled = term.color256("-", 244)
    elif colored:
        id6_styled = term.style_lifecycle_text(id6_raw, resolved)
    else:
        id6_styled = id6_raw
    id6_pad = " " * (6 - len(id6_raw))
    id6_col = f"{id6_styled}{id6_pad}"

    dep_ids = _extract_dependency_id6s(it)
    if dep_ids:
        deps_styled_parts = [
            _color_dep_id(dep, id_map.get(dep) if id_map else None, term, colored)
            for dep in dep_ids
        ]
        deps_col = ", ".join(deps_styled_parts)
    else:
        deps_col = term.color256("-", 244) if colored else "-"

    inline_gate = ""
    if it.gate and not gate_in_header:
        ref_txt = _gate_ref_display(
            A.escape_detail(it.gate.get("ref", "")), long=bool(long)
        )
        inline_gate = f"  [gate {it.gate.get('kind')}: {ref_txt}]"

    if runs_mode:
        row_line = (
            f"{st_col} {run_col} {tp_col} {blk_col} {prio_col} {rd_col} {oq_col} "
            f"{exec_col} {valid_col} {date_col} {set_col} {num_col} {id6_col} {deps_col}{inline_gate}"
        )
    else:
        row_line = (
            f"{st_col} {tp_col} {blk_col} {prio_col} {rd_col} {oq_col} "
            f"{exec_col} {valid_col} {date_col} {set_col} {num_col} {id6_col} {deps_col}{inline_gate}"
        )
    if details and it.detail_text:
        tag = it.detail_kind or "summary"
        tag_txt = term.color256(f"{tag}:", 244) if colored else f"{tag}:"
        detail_txt = term.color256(it.detail_text, 250) if colored else it.detail_text
        row_line += f"\n      {tag_txt} {detail_txt}"

    return row_line


def is_explicit_order(order_by: Optional[str]) -> bool:
    """Return True if ``order_by`` requests an explicit sort order (not None and not ORDER_CLASS)."""
    return bool(order_by and order_by != A.ORDER_CLASS)


def render_table(
    items: List[Item],
    drift: List[core.Drift],
    show_all: bool = False,
    term: Optional[T.Term] = None,
    long: bool = False,
    details: bool = False,
    repo_root: Optional[Path] = None,
    order_by: Optional[str] = None,
    legend: bool = True,
    id_map: Optional[Dict[str, Item]] = None,
    runs_mode: bool = False,
    run_map: Optional[Dict[str, str]] = None,
) -> str:
    """Render items in a compact columnar table for interactive/TTY viewing.

    Columns: Status (8), [Run (7)], Type (8), Blocks (6), Priority (8), Readiness (9), OQs (3), Exec (4), Valid (5), Date (8), SetID, N, ID6 (6), Deps.
    Sorted by Type, Blocking (non-blocking first), SetID, N, ID6, Priority (none first, then low, med, high), name.
    """
    if term is None:
        term = T.Term(color=True)
    colored = bool(getattr(term, "color", False))

    if repo_root is None:
        try:
            from agent_workflows.project_context import (
                is_project_dir,
                resolve_verb_repo_root,
            )

            cand = resolve_verb_repo_root(None)
            if is_project_dir(cand):
                repo_root = cand
        except Exception:
            pass

    if runs_mode and run_map is None and repo_root is not None:
        run_map = get_active_runs_map(repo_root)
    elif run_map is None:
        run_map = {}

    lines: List[str] = []
    if drift:
        lines.append(
            "VIEW INVALID: contract violations must be resolved before this board is authoritative."
        )
        for d in drift:
            lines.append(f"  ! {d.location}: {d.rule}: {d.detail}")
        lines.append("")

    if not show_all:
        visible = [it for it in items if it.attention_class not in (A.DONE, A.PARKED)]
    else:
        visible = list(items)

    if not visible:
        return "\n".join(lines).rstrip("\n") + "\n" if lines else ""

    if id_map is None:
        id_map = {it.id: it for it in items if it.id}

    if not is_explicit_order(order_by):

        def _sort_key(it: Item) -> Tuple:
            type_word = _SINGULAR_TYPE.get(it.tree, it.tree)
            blk_ver = _resolve_release_version(repo_root, it.blocks_release)
            is_blocking = 0 if (blk_ver == "-" or not it.blocks_release) else 1
            date, set_id, num, id6 = _extract_identity_parts(it)
            prio_rank = PRIORITY_RANK.get((it.priority or "").lower(), 0)
            name = _identity_stem(it.path)
            if num.isdigit():
                return (
                    type_word,
                    is_blocking,
                    0,
                    date,
                    set_id,
                    int(num),
                    id6 if id6 != "-" else (it.id or ""),
                    prio_rank,
                    name,
                    it.path,
                )
            return (
                type_word,
                is_blocking,
                1,
                prio_rank,
                name,
                it.path,
            )

        visible.sort(key=_sort_key)
    # The table is ONE flat list, not per-class sections, so there is no section header to hoist a
    # shared gate ref into. When every visible row is gated by the SAME ref, say it once above the
    # table and drop it from the rows; otherwise each row keeps its own (now `--long`-aware) ref.
    shared_gate = _shared_gate_ref(visible, long=long)
    if shared_gate:
        note = f"all {len(visible)} gated by {shared_gate}"
        lines.append(term.color256(note, 244) if colored else note)

    col_title = "Path" if long else "SetID"
    visible_set_vals = [
        it.path if long else _extract_identity_parts(it)[1] for it in visible
    ]
    set_w = max(len(col_title), max((len(s) for s in visible_set_vals), default=0))

    visible_num_lens = [len(_extract_identity_parts(it)[2]) for it in visible]
    num_w = max(len("N"), max(visible_num_lens, default=2), 2)

    visible_oq_lens = []
    visible_exec_lens = []
    visible_valid_lens = []
    for it in visible:
        oq_cnt = getattr(it, "oqs", 0) or 0
        rq_cnt = getattr(it, "rqs", 0) or 0
        tot_q = oq_cnt + rq_cnt
        if tot_q > 0:
            visible_oq_lens.append(len(f"{oq_cnt}/{tot_q}"))
        exec_prog = getattr(it, "exec_progress", None)
        if exec_prog and exec_prog[1] > 0:
            visible_exec_lens.append(len(f"{exec_prog[0]}/{exec_prog[1]}"))
        valid_prog = getattr(it, "valid_progress", None)
        if valid_prog and valid_prog[1] > 0:
            visible_valid_lens.append(len(f"{valid_prog[0]}/{valid_prog[1]}"))

    oq_w = max(len("OQs"), max(visible_oq_lens, default=1))
    exec_w = max(len("Exec"), max(visible_exec_lens, default=1))
    valid_w = max(len("Valid"), max(visible_valid_lens, default=1))

    # WIDENED FROM 8 TO 10 to match `_render_table_row`'s Status column, which now carries the
    # lifecycle glyph in its first two columns ahead of the status word. Two leading spaces rather
    # than a `ljust(10)` so the word `Status` still sits above the WORD it labels rather than above
    # the glyph. The column ORDER and COUNT are unchanged (Section 12).
    st_hdr = "  " + "Status".ljust(8)
    tp_hdr = "Type".ljust(8)
    blk_hdr = "Blocks"
    prio_hdr = "Priority"
    rd_hdr = "Readiness"
    oq_hdr = "OQs".rjust(oq_w)
    exec_hdr = "Exec".rjust(exec_w)
    valid_hdr = "Valid".rjust(valid_w)
    date_hdr = "Date".ljust(8)
    set_hdr = col_title.ljust(set_w)
    num_hdr = "N".ljust(num_w)
    id6_hdr = "ID6".ljust(6)

    if runs_mode:
        run_hdr = "Run".ljust(7)
        header = (
            f"{st_hdr} {run_hdr} {tp_hdr} {blk_hdr} {prio_hdr} {rd_hdr} {oq_hdr} "
            f"{exec_hdr} {valid_hdr} {date_hdr} {set_hdr} {num_hdr} {id6_hdr} Deps"
        )
    else:
        header = (
            f"{st_hdr} {tp_hdr} {blk_hdr} {prio_hdr} {rd_hdr} {oq_hdr} "
            f"{exec_hdr} {valid_hdr} {date_hdr} {set_hdr} {num_hdr} {id6_hdr} Deps"
        )
    lines.append(term.colorize(header, "bold") if colored else header)

    for it in visible:
        run_st = _item_run_status(it, run_map) if runs_mode else None
        lines.append(
            _render_table_row(
                it,
                term=term,
                colored=colored,
                long=long,
                details=details,
                repo_root=repo_root,
                gate_in_header=bool(shared_gate),
                set_w=set_w,
                num_w=num_w,
                oq_w=oq_w,
                exec_w=exec_w,
                valid_w=valid_w,
                id_map=id_map,
                runs_mode=runs_mode,
                run_state=run_st,
            )
        )

    if legend:
        oqs_lbl = term.colorize("OQs", "bold") if colored else "OQs"
        exec_lbl = term.colorize("Exec", "bold") if colored else "Exec"
        valid_lbl = term.colorize("Valid", "bold") if colored else "Valid"
        deps_lbl = term.colorize("Deps", "bold") if colored else "Deps"
        if runs_mode:
            run_lbl = term.colorize("Run", "bold") if colored else "Run"
            lines.append(
                f"{run_lbl} = Active runner state, {oqs_lbl} = Open Questions (open/total), {exec_lbl} = Executed items, "
                f"{valid_lbl} = Validated items, {deps_lbl} = Dependencies"
            )
        else:
            lines.append(
                f"{oqs_lbl} = Open Questions (open/total), {exec_lbl} = Executed items, "
                f"{valid_lbl} = Validated items, {deps_lbl} = Dependencies"
            )

    return "\n".join(lines).rstrip("\n") + "\n"


def render_board(
    items: List[Item],
    drift: List[core.Drift],
    show_all: bool = False,
    term: T.Term | None = None,
    long: bool = False,
    details: bool = False,
    legend: bool | None = None,
    repo_root: Path | None = None,
    order_by: Optional[str] = None,
    id_map: Optional[Dict[str, Item]] = None,
    runs_mode: bool = False,
    run_map: Optional[Dict[str, str]] = None,
) -> str:
    """Render the attention board.

    When ``term`` is colored (a real TTY / FORCE_COLOR), the human view renders the columnar
    table (Status, [Run], Type, Blocks, Priority, Readiness, OQs, Exec, Valid, Date, SetID, ID6, Deps). When color is OFF
    (piped / agent / NO_COLOR / no ``term``), it emits the stable machine-readable
    ``- [tree] path (status){gate}`` form so agents and grep keep a fixed, parseable shape. Under an
    explicit order, the non-colored board emits a single flat, globally-ordered list (sections are
    absent by design); under the default order, items are partitioned into attention class sections.
    """
    if term is None:
        term = T.Term(color=False)
    colored = bool(getattr(term, "color", False))
    if colored:
        return render_table(
            items,
            drift,
            show_all=show_all,
            term=term,
            long=long,
            details=details,
            repo_root=repo_root,
            order_by=order_by,
            legend=True if legend is None else legend,
            id_map=id_map,
            runs_mode=runs_mode,
            run_map=run_map,
        )
    if legend is None:
        legend = colored

    lines: List[str] = []
    if drift:
        lines.append(
            "VIEW INVALID: contract violations must be resolved before this board is authoritative."
        )
        for d in drift:
            lines.append(f"  ! {d.location}: {d.rule}: {d.detail}")
        lines.append("")

    if is_explicit_order(order_by):
        # Under an explicit order, emit ONE globally-ordered list instead of class-partitioned sections.
        # Items were already sorted upstream by cmd_attention; do not re-sort here.
        # Preserve the done/parked suppression unless show_all is True.
        if not show_all:
            visible = [
                it for it in items if it.attention_class not in (A.DONE, A.PARKED)
            ]
        else:
            visible = list(items)

        for it in visible:
            run_st = _item_run_status(it, run_map) if runs_mode else None
            lines.append(
                _render_item_row(
                    it,
                    it.attention_class,
                    term,
                    colored,
                    long,
                    details=details,
                    gate_in_header=False,
                    runs_mode=runs_mode,
                    run_state=run_st,
                )
            )
        return "\n".join(lines).rstrip("\n") + "\n" if lines else ""

    by_class: Dict[str, List[Item]] = {}
    for it in items:
        by_class.setdefault(it.attention_class, []).append(it)
    for cls in A.ATTENTION_CLASS_ORDER:
        group = by_class.get(cls, [])
        if not group:
            continue

        # Section header. In the colored human view, fold a shared gate artifact into the
        # header (e.g. "blocked (2) in TODO.md") instead of repeating it on every line.
        header_extra = ""
        shared_gate = ""
        if colored and cls == A.BLOCKED:
            shared_gate = _shared_gate_ref(group, long=long)
            if shared_gate:
                header_extra = f" in {shared_gate}"

        if cls in (A.DONE, A.PARKED) and not show_all:
            if not colored:
                lines.append(f"## {cls} ({len(group)}) [hidden; use --all]")
            continue

        # awdoctorfix Order 02: the colored default view shows a compact identity stem per item
        # (tree-independent), so no directory prefix is folded into the header. `--long` restores
        # full paths (rendered per-item below); either way the header carries no path prefix.
        header_title = f"{cls} ({len(group)}){header_extra}"
        if colored:
            code = _CLASS_COLOR_256.get(cls, 244)
            lines.append(term.color256(header_title, code, bold=True))
        else:
            lines.append(f"## {header_title}")

        for it in group:
            run_st = _item_run_status(it, run_map) if runs_mode else None
            lines.append(
                _render_item_row(
                    it,
                    cls,
                    term,
                    colored,
                    long,
                    details=details,
                    gate_in_header=bool(shared_gate),
                    runs_mode=runs_mode,
                    run_state=run_st,
                )
            )
    if colored and legend:
        lines.append(
            "legend: ! stale(>30d)  ? unknown-age  # blocked-by-gate  > release-blocker  [priority]"
        )
    return "\n".join(lines).rstrip("\n") + "\n" if lines else ""


# --------------------------------------------------------------------------------------
# CLI entrypoint
# --------------------------------------------------------------------------------------


def prune_drift_to_selection(
    drift: List[core.Drift],
    items: Sequence[Item],
    repo_root: Path,
    selected_trees: Optional[set[str]] = None,
) -> List[core.Drift]:
    """Narrow ``drift`` alongside a narrowed ``items`` set WITHOUT dropping a contract violation.

    THE ONE PRUNE, called from every filter site (attcor `rkn8ya` E-01). Three byte-identical copies
    of this five-line prune existed inline (the `--types` site, the selector site, and the combined
    status/priority/blocking/readiness/open-questions/run-status site); fixing one left two live, so
    the logic is defined once here.

    WHY A PLAIN `location in selected_item_paths` TEST IS WRONG, which is the bug this replaces. A
    file that FAILS TO PARSE yields drift and NO item: `_plans_record` returns ``(None, drift)`` and
    `scan` does ``if rec is None: continue`` AFTER extending drift. Its violation therefore matched
    no surviving item path and was silently DELETED by every narrowing, so `aw attention --check`
    exited 0 on a genuine violation under `-t plans`, under a selector, and under a status filter.
    That contradicts the spec's normative fail-closed rule (Section 8.6: `--check` "never silently
    skips a malformed included artifact").

    THE RETENTION RULE is by SELECTED TREE, not "retain everything". A drift record whose location
    lies under a tree the caller selected is retained even when it produced no item; drift from an
    unselected tree is still pruned, and a NON-PATH location (a stranded lane's git BRANCH) is still
    pruned under an explicit narrowing, preserving the deliberate suppression the lane join relies
    on. Retaining all drift unconditionally would resurrect stranded-lane rows under `--types`,
    contradicting spec F3a's normative exclusions.

    ``selected_trees`` is the ACTIVE `--types` filter, or ``None`` meaning EVERY TRACKED TREE. It is
    deliberately NOT derived from the surviving items' trees: a tree whose only offending file fails
    to parse contributes no item, so keying on the items would delete precisely the violation this
    function exists to keep. A selector or status narrowing states nothing about types, so under it
    every tracked tree stays selected and only the non-path (lane) locations are pruned.
    """

    if not drift:
        return drift

    selected_paths = {(repo_root / it.path).resolve() for it in items}
    trees = (
        set(selected_trees)
        if selected_trees
        else {pol.name for pol in A.TREE_POLICY if pol.tracked}
    )
    tree_roots: List[str] = []
    for pol in A.TREE_POLICY:
        if pol.name in trees:
            root = pol.root.replace("\\", "/").rstrip("/")
            tree_roots.append(root + "/")
            # The `.aw/` layout root for the same policy key: TREE_POLICY still spells the legacy
            # `.agents/` roots, and `_classify_tree` maps `.aw/records/<type>` onto them (re-inserting
            # the `docs/` grouping for the doc family). Derive both spellings so a modern-layout
            # location is recognized by the same membership test.
            legacy_prefix = ".agents/docs/"
            if root.startswith(legacy_prefix):
                tail = root[len(legacy_prefix) :]
                # `prompts` is the legacy key for the renamed `prompt-library` tree.
                modern = "prompt-library" if tail == "prompts" else tail
                tree_roots.append(f".aw/records/{modern}/")
            elif root.startswith(".agents/"):
                tree_roots.append(".aw/records/" + root[len(".agents/") :] + "/")

    def _keep(d: core.Drift) -> bool:
        loc = str(d.location).replace("\\", "/")
        try:
            if (repo_root / loc).resolve() in selected_paths:
                return True
        except (OSError, ValueError):
            pass
        # RETAINED: a violation from a SELECTED TREE whose file produced no item (unparseable,
        # missing status, unreadable). This is the fail-closed half.
        return any(loc.startswith(r) for r in tree_roots)

    return [d for d in drift if _keep(d)]


def filter_items_by_selectors(
    items: List[Item], selectors_list: Sequence[str], repo_root: Path
) -> List[Item]:
    """Filter scanned attention items by one or more selector tokens (id6, setid, path, tree, status, etc.)."""
    tokens = [str(t).strip() for t in selectors_list if str(t).strip()]
    if not tokens:
        return items

    from agent_workflows import selectors

    record_types = (
        "plans",
        "specs",
        "research",
        "backlog",
        "prompts",
        "walkthroughs",
        "roadmaps",
        "releases",
    )
    matched_paths: set = set()
    for tok in tokens:
        for rt in record_types:
            try:
                for p in selectors.resolve_selectors(repo_root, rt, [tok]):
                    matched_paths.add(p.resolve())
            except Exception:
                pass

    filtered: List[Item] = []
    for it in items:
        p_resolved = (repo_root / it.path).resolve()
        matches = False
        if p_resolved in matched_paths:
            matches = True
        else:
            for tok in tokens:
                tok_lower = tok.lower()
                if it.id and it.id.lower() == tok_lower:
                    matches = True
                    break
                if it.tree and it.tree.lower() == tok_lower:
                    matches = True
                    break
                if it.attention_class and it.attention_class.lower() == tok_lower:
                    matches = True
                    break
                if it.native_status and it.native_status.lower() == tok_lower:
                    matches = True
                    break
                if it.priority and it.priority.lower() == tok_lower:
                    matches = True
                    break
                if tok_lower in it.path.lower():
                    matches = True
                    break
        if matches:
            filtered.append(it)
    return filtered


def selector_vocabulary() -> frozenset:
    """The set of selector tokens that are a STANDING QUESTION about repository state.

    attsel `fqnj8k` E-08. A token in this set legitimately matches nothing (a repository may simply
    contain no `reusable` plan and no `releases` record), so a zero-match on it is a SUCCESSFUL answer
    and is exempt from the `EXIT_UNRESOLVED_SELECTOR` refusal. A token OUTSIDE it that matches nothing
    is an assertion that a named artifact exists, which is a refusal.

    THE DISTINCTION IS NOT INVENTED HERE. Spec `25kzda` Section 2.4a already draws it, for exactly this
    reason: an empty status-selector result "is a success, not an error ... because `reviews` is a
    standing question about repository state rather than an assertion that a named item exists. A
    misspelled id6 still exits 2; only the status selectors are exempt."

    DERIVED FROM THE CONTRACT SYMBOLS, NEVER A LITERAL LIST, which is the whole point: a tree, class,
    status or priority added to `attention_contract` (or to `backlog.PRIORITIES`) later joins this
    vocabulary automatically and so cannot silently become an "error" for an operator who asked a
    perfectly reasonable question about it.

    TWO SOURCES ARE INCLUDED THAT `TRACKED_TREES` AND `CLASS_MAPS` ALONE WOULD MISS, and each was
    found by MEASURING rather than by reading the enums, so neither is a guess:

    * TYPE NAMES THIS VERB ACCEPTS BUT DOES NOT SCAN. `TYPE_ALIASES` accepts `roadmaps`,
      `walkthroughs`, `prompts`, `comms` and `actions`, while `TRACKED_TREES` is five trees and the
      live scan yields four. So `aw att roadmaps` is a type question the CLI invites and the scanner
      can never answer with an item, and refusing it would call the operator wrong for using a name
      the verb's own `-t` flag documents. (The deeper gap - that `releases` records and every
      `roadmaps`/`walkthroughs` file are invisible to the view at all - is owned by approved plan
      `m867ox`, which declares `attention_contract.py`; this function deliberately does NOT edit that
      file and only stops those tokens being reported as typos.)
    * RUN-STATUS WORDS. `abandoned` reaches this verb through `--arcive-state`/`-as`, whose alias
      table is `_RUN_STATUS_ALIASES` and whose canonical values `matches_run_status` consumes. Asking
      "what is abandoned?" and hearing "nothing" is a successful answer, exactly like asking about an
      empty tree, so these join the vocabulary too. Sourced from the alias table and the `lanes`
      `CLASS_MAPS` fragment, never typed out here.
    """
    from agent_workflows import backlog as backlog_mod

    vocab: set = set()
    # Tree names (`-t`-style tokens used positionally): `specs`, `plans`, `research`, ...
    vocab |= {str(t).lower() for t in A.TRACKED_TREES}
    # Every type name the CLI accepts, INCLUDING the ones the scanner does not (see the docstring).
    vocab |= {str(k).lower() for k in TYPE_ALIASES}
    vocab |= {str(v).lower() for v in TYPE_ALIASES.values()}
    # Cross-tree attention classes: `ready`, `active`, `blocked`, `done`, `parked`.
    vocab |= {str(c).lower() for c in A.ATTENTION_CLASSES}
    # Every per-tree NATIVE status enum, read from the mapping that defines them.
    for _tree, class_map in A.CLASS_MAPS.items():
        vocab |= {str(s).lower() for s in class_map.keys()}
    # Priorities, whose owner is the backlog module.
    vocab |= {str(p).lower() for p in backlog_mod.PRIORITIES}
    # Run-status words, from the alias table this module already owns.
    vocab |= {str(k).lower() for k in _RUN_STATUS_ALIASES}
    vocab |= {str(v).lower() for v in _RUN_STATUS_ALIASES.values()}
    # The run-status words the runner writes that are not aliases (`abandoned` is the measured case).
    try:
        from agent_workflows import run_viewer as _run_viewer

        vocab.add(str(_run_viewer.ABANDONED).lower().rstrip("?"))
    except Exception:
        # A missing optional symbol must never make a legitimate question into an error, so the only
        # failure mode here is that ONE token loses its exemption, never a crash.
        pass
    return frozenset(vocab)


class SelectorMatchFacts(NamedTuple):
    """Per-token answers to "did this selector match anything, and is it even a valid selector?".

    attsel `fqnj8k` E-03. Two facts are kept SEPARATE because they are different messages and
    conflating them would trade one ambiguity for another (F3):

    * ``unmatched`` - the token is a well-formed selector that matched NO artifact in the unfiltered
      scan. This is the typo case.
    * ``invalid``  - resolving the token RAISED for every record type. `filter_items_by_selectors`
      swallows that in a bare `except Exception: pass`, so today a malformed selector is as silent as
      a merely-absent one. A token here is also in ``unmatched`` when it matched nothing, because a
      malformed token that somehow matched by path substring is still a match.
    """

    matched: Tuple[str, ...]
    unmatched: Tuple[str, ...]
    invalid: Tuple[str, ...]
    vocabulary: Tuple[str, ...]

    @property
    def refusable(self) -> Tuple[str, ...]:
        """The unmatched tokens that are NOT a standing vocabulary question, i.e. the refusals."""
        vocab = set(self.vocabulary)
        return tuple(t for t in self.unmatched if t.lower() not in vocab)


def selector_match_facts(
    items: List[Item],
    selectors_list: Sequence[str],
    repo_root: Path,
    drift: Optional[Sequence[core.Drift]] = None,
) -> SelectorMatchFacts:
    """Answer, PER TOKEN, whether it matched at least one artifact in the ``items`` given.

    attsel `fqnj8k` E-03.

    THE CALLER MUST PASS THE UNFILTERED SCAN, and this is the single most important property of this
    function. `run()` applies `--type` BEFORE the selector filter, so a token matching a backlog
    artifact under `-t plans` reaches the selector filter with its artifact already gone: a match fact
    computed from what the filter RECEIVED would report that token as a typo (measured at review: the
    same filter matches `sv0sf3` over the full 1063-item scan and 0 items over the `-t plans` 661-item
    scan). Reporting a FALSE no-match is a worse defect than the silence this fix removes, so the fact
    is pinned to the scan before any filter narrowed it.

    IT KEYS ON "MATCHED", NOT ON "RESOLVED" (F4). `filter_items_by_selectors`' last rung is a SUBSTRING
    test on `it.path`, so a token can legitimately match an artifact without resolving as any
    identifier; a no-match report keyed on the resolver alone would fire on every substring query. This
    function therefore re-uses the SAME matcher the view itself uses, one token at a time, so the two
    can never disagree about what a match is.

    A MALFORMED ARTIFACT YIELDS DRIFT AND NO ITEM, so ``drift`` must be passed or a token naming a real
    but unparseable file is reported as a typo. FOUND BY THIS PLAN'S OWN E-06 TEST rather than
    predicted: a plan carrying no `Status:` produces one `attention.missing-status` violation and ZERO
    items, so `aw att <its-id6>` saw an empty match set and refused, telling the operator their id6 does
    not exist when the file is sitting in `pending/` and is precisely what they need to go fix. That is
    the F4 false-no-match class arriving by a third route, and it is the worst instance of it, because
    the one artifact you most need to find is the broken one. A token matching a drift LOCATION
    therefore counts as MATCHED.

    `filter_items_by_selectors`' own signature, return value and behavior are UNTOUCHED: this is a
    separate pure function, not a mutation of that contract.
    """
    from agent_workflows import selectors

    tokens = [str(t).strip() for t in selectors_list if str(t).strip()]
    matched: List[str] = []
    unmatched: List[str] = []
    invalid: List[str] = []

    # The drift LOCATIONS, matched the same two ways the item rungs match: by resolved path and by
    # path substring. An id6 embedded in a filename is caught by the substring rung, which is what
    # makes `aw att bad001` find a plan too broken to have become an item.
    drift_locations = [str(d.location) for d in (drift or [])]

    record_types = (
        "plans",
        "specs",
        "research",
        "backlog",
        "prompts",
        "walkthroughs",
        "roadmaps",
        "releases",
    )
    for tok in tokens:
        # Ask the ONE matcher the view uses, for this token alone. Calling it per token is what turns
        # its set-valued answer into a per-token fact without duplicating any matching rung.
        hit = bool(filter_items_by_selectors(items, [tok], repo_root))
        if not hit and drift_locations:
            tok_lower = tok.lower()
            hit = any(tok_lower in loc.lower() for loc in drift_locations)
        if hit:
            matched.append(tok)
        else:
            unmatched.append(tok)
        # Independently: did the resolver raise for EVERY record type? That is the malformed-selector
        # fact, which the filter's bare `except Exception: pass` currently hides. Raising for every
        # type is the test, not raising for one: most tokens raise for the types they are not.
        raised_everywhere = True
        for rt in record_types:
            try:
                selectors.resolve_selectors(repo_root, rt, [tok])
                raised_everywhere = False
            except Exception:
                continue
        if raised_everywhere:
            invalid.append(tok)

    return SelectorMatchFacts(
        matched=tuple(matched),
        unmatched=tuple(unmatched),
        invalid=tuple(invalid),
        vocabulary=tuple(sorted(selector_vocabulary())),
    )


def format_unresolved_selector_message(
    facts: SelectorMatchFacts, *, term: Optional[T.Term] = None
) -> str:
    """The human report for selector tokens that matched no artifact.

    attsel `fqnj8k` E-04. REUSES `term.Term.format_empty_result`, the house empty-state primitive
    (`aw find` renders its own empty result with it), rather than inventing a second message shape the
    operator would have to learn. It renders the outcome line, an `Active filters:` block echoing the
    offending token(s), and a `Next` action.

    EACH UNMATCHED TOKEN IS NAMED INDIVIDUALLY, never collapsed into one message, because a
    multi-token invocation is exactly where a single typo hides.

    NO "DID YOU MEAN" GUESS. A wrong guess is worse than a clean negative and the operator knows what
    they typed; fuzzy matching is a separate feature with its own design question.
    """
    if term is None:
        term = T.Term(stream=sys.stderr, color=False)
    toks = facts.refusable
    noun = "selector" if len(toks) == 1 else "selectors"
    quoted = ", ".join(repr(t) for t in toks)
    summary = f"no artifact matched {noun} {quoted}"
    filters: List[Tuple[str, Any]] = [
        (f"unmatched {noun}", list(toks)),
        ("searched trees", ", ".join(sorted(str(t) for t in A.TRACKED_TREES))),
    ]
    if facts.matched:
        # Say which tokens DID match, so a mixed invocation reads as "these worked, that one did not".
        filters.append(("matched selectors", list(facts.matched)))
    if facts.invalid:
        # F3: "this token is not a valid selector at all" is a DIFFERENT message from "this valid
        # token matched nothing", and reporting only the second would trade one ambiguity for another.
        filters.append(("not a valid selector", list(facts.invalid)))
    return term.format_empty_result(
        summary,
        filters=filters,
        next_action=(
            "aw next",
            "show the whole board, then copy an id6 from it",
        ),
        status="fail",
    )


def unresolved_selector_agent_record(facts: SelectorMatchFacts) -> Dict[str, Any]:
    """The `aw.agent/v1` error record for selector tokens that matched no artifact.

    attsel `fqnj8k` E-05/E-09.

    SHAPED ON THE SHIPPED PRECEDENT, not invented. `aw runs <bogus>` already refuses an unresolvable
    read-only target with `kind:error, outcome:cannot-run, exit:2, verified:false, complete:false,
    findings:N, unresolved_targets:[...]` (`run_viewer.emit_unresolvable_target_refusal`), and that
    shape validates today. Copying it means one convention across the two verbs rather than a third.

    WHY `verified:false` AND `complete:false` ARE THE HONEST VALUES, and this is the half that matters
    most for automation. The old record said `outcome:clean, verified:true, complete:true, findings:0`
    for a token that matched nothing, so a consumer recorded a typo as a CLEAN AUDIT. Both booleans
    were false in substance: nothing was verified, and the answer is not complete, it is ABSENT.

    BOTH FIELD NAMES ARE EMITTED (decision D2). `unresolved_selectors` is this verb's own noun (its
    CLI positional is `selectors`), and `unresolved_targets` carries the identical list so a consumer
    already written against the `aw runs` precedent reads it unchanged. One extra key removes the only
    way a consumer could be surprised.

    NO SCHEMA BUMP IS NEEDED OR MADE. `render_json`'s `SCHEMA_VERSION` payload is not involved at all,
    because this refusal is emitted BEFORE the surface branches and so a no-match invocation never
    reaches `render_json` (decision D6).
    """
    from agent_workflows import agent_schema as _agent_schema

    toks = list(facts.refusable)
    noun = "selector" if len(toks) == 1 else "selectors"
    quoted = ", ".join(repr(t) for t in toks)
    record: Dict[str, Any] = {
        "schema": _agent_schema.SCHEMA_VERSION,
        "kind": "error",
        "cmd": "attention",
        "outcome": "cannot-run",
        "exit": EXIT_UNRESOLVED_SELECTOR,
        "verified": False,
        "complete": False,
        "findings": len(toks),
        "unresolved_selectors": toks,
        # D2: the precedent's own field name, same list, for a consumer written against `aw runs`.
        "unresolved_targets": toks,
        "error": (
            f"no artifact matched {noun} {quoted}; searched the tracked record trees "
            + ", ".join(sorted(str(t) for t in A.TRACKED_TREES))
        ),
        "next": "aw next",
    }
    if facts.matched:
        record["matched_selectors"] = list(facts.matched)
    if facts.invalid:
        # F3: kept distinct from merely-unmatched, since they are different messages.
        record["invalid_selectors"] = list(facts.invalid)
    # Fail closed on our OWN record rather than trusting it by eye (the plan forbids asserting schema
    # validity without the validator).
    _agent_schema.assert_valid_agent_record(record)
    return record


def _emit_unresolved_selector_refusal(
    facts: SelectorMatchFacts, *, args, ctx, repo_root: Path
) -> int:
    """Emit the no-match refusal on whichever surface is active, and return its exit code.

    attsel `fqnj8k` E-04/E-05/E-09/E-10. ONE function for all eight surfaces, because the defect it
    fixes was five surfaces having no report at all while two were thought to be the whole problem.

    THE CHANNEL IS PER SURFACE (decision D5), and the split is not cosmetic:

    * STDOUT for `--agent`, `--json`/`--format json` and `--check --agent`, because on those surfaces
      the record IS the payload and the consumer reads stdout.
    * STDERR for the human board, `--check`'s human path, and all three list modes. A list mode exists
      to be piped into another command, so a diagnostic on ITS stdout would corrupt the pipe; keeping
      stdout byte-identical there is a hard requirement, not a preference. This also matches the
      shipped `aw runs` refusal, which goes to stderr "so a refusal never lands in a report a caller
      is parsing on stdout".
    """
    if ctx.is_agent or ctx.is_json or getattr(args, "format", None) == "json":
        record = unresolved_selector_agent_record(facts)
        # `--json` (and `--format json`) pretty-print; `--agent` is one compact line. This mirrors how
        # `run_viewer.emit_unresolvable_target_refusal` chooses its indent.
        indent = 2 if (ctx.is_json or getattr(args, "format", None) == "json") else None
        sys.stdout.write(json.dumps(record, indent=indent, ensure_ascii=False) + "\n")
        return EXIT_UNRESOLVED_SELECTOR

    color = False if getattr(args, "no_color", False) else None
    term = T.Term(stream=sys.stderr, color=color)
    sys.stderr.write(format_unresolved_selector_message(facts, term=term) + "\n")
    return EXIT_UNRESOLVED_SELECTOR


def run(args) -> int:
    # Climb to the project root so `aw attention` works from any subdirectory; an explicit --dir is
    # honored verbatim (IPD awretrofit Order 06).
    from agent_workflows.project_context import (
        git_root_for_message,
        is_project_dir,
        no_project_message,
        resolve_verb_repo_root,
    )
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        Evidence,
        NextAction,
        select_output,
    )

    explicit_dir = getattr(args, "dir", None)
    repo_root = resolve_verb_repo_root(explicit_dir)
    check = getattr(args, "check", False)
    ctx = select_output(args)

    # No AW project at cwd or any ancestor (and none named via --dir): emit the verbose guidance
    # instead of a silent empty board. --check stays fail-closed-valid (nothing to violate).
    #
    # lanestrand-01 (`pr5b0t`) E-06: THE LANE CHECK DELIBERATELY DOES NOT APPLY ON THIS EARLY-RETURN
    # PATH, and the decision is recorded rather than left implicit. A directory that is not an AW
    # project has no `.aw/records/runs`, so there is no run record to read and therefore no lane a
    # driver of THIS toolkit could have stranded; running the probe would answer "no lanes" after doing
    # filesystem work, which is a slower way to reach the same 0. The honesty requirement is satisfied
    # because the branch's own precondition ("there is no project here") is what makes the empty answer
    # true, not an unexamined assumption: this is not the "prints a clean view without having looked"
    # case, since there is nothing in scope to look at.
    if not explicit_dir and not is_project_dir(repo_root):
        if check:
            if ctx.is_agent or ctx.is_json:
                res = CommandResult(
                    command="attention",
                    status="clean",
                    exit_code=0,
                    summary="the view is valid",
                    evidence=[
                        Evidence(
                            key="attention",
                            value={"items": 0, "drift": 0},
                            status="clean",
                        )
                    ],
                    data={"items": [], "drift": []},
                )
                return get_renderer(ctx).emit(res, ctx)
            sys.stdout.write("aw attention --check: the view is valid.\n")
            return 0
        if ctx.is_agent or ctx.is_json:
            # attcor `rkn8ya` E-12: EMIT the result. This `CommandResult` was built and then thrown
            # away - the `emit` call was missing - so `aw attention --agent` outside an AW project
            # wrote prose to STDERR and NOTHING to stdout, breaking the `aw.agent/v1` envelope
            # contract for a consumer that only reads stdout. The correct sibling is the `--check`
            # branch ten lines above, and the scan-error branch below also emits; this one path did
            # not. Reproduced before the fix: rc=3, stdout empty, stderr carrying the prose.
            #
            # AND THE SUMMARY IS SANITIZED. `no_project_message` interpolates the directory it
            # checked (`project_context.py`), so emitting it verbatim would write a machine-local
            # ABSOLUTE path into a machine payload, the same leak class as E-02 and forbidden by the
            # attention spec's Section 8.5. The human STDERR line keeps the full guidance (it names
            # the directory it checked, which is exactly what helps an operator standing in the wrong
            # one); the MACHINE summary states the condition and the remedies without the path.
            #
            # THE MACHINE SURFACE CARRIES EXIT 2, NOT 3, and the reason is a hard contract, recorded
            # here because the number differs from the human path's on purpose (decision D1).
            # `aw.agent/v1` admits ONLY 0/1/2 (`agent_schema.validate_agent_record`: "Field 'exit'
            # must be an integer in (0, 1, 2)"), and additionally requires an error-class record to
            # carry exit=2; `docs/cli-output-contract.md` Section 3 classifies precisely this case
            # ("Cannot-Run ... preventing domain inspection") as 2, and its exit-parity rule requires
            # the embedded `exit` to EQUAL the process exit code. An `exit_code=3` result therefore
            # cannot be emitted at all: it raises `ValueError` in the renderer before writing a byte,
            # which is why simply adding the missing `emit` call with 3 would reproduce the empty
            # stdout this fix removes. (The sibling `aw ipd board` had the identical defect and was
            # filed as backlog `5x195l`; nogitmsg `quqyc4` E-05 FIXED it the same way, so no site in
            # the package now builds an `exit_code=3` record. That property is pinned by
            # `tests/test_awretrofit_project_root_climb.py::NoProjectSubprocessMatrixTests`.)
            #
            # THE HUMAN PATH IS UNCHANGED at exit 3, so the shipped assertion in
            # `tests/test_awretrofit_project_root_climb.py` (rc 3, prose on stderr, empty stdout)
            # keeps passing and no operator-visible behavior regresses.
            #
            # nogitmsg `quqyc4` E-04 ADDS THE INSTALL OFFER AS STRUCTURED DATA, not only as prose:
            # when cwd IS inside a git repository, the record carries a `NextAction` so an automated
            # consumer can read the remedy from the `next` field instead of parsing the summary. The
            # command is `aw install .` and NOT `aw install <absolute root>` because the absolute form
            # is UNEMITTABLE: `agent_schema` refuses an absolute home path in ANY string field, so it
            # would raise in the renderer and reintroduce the very crash class this branch documents
            # (measured; decision 03-quqyc4-D2). `aw install` defaults to cwd, so `.` is literally
            # runnable. In a NON-git directory no action is attached and `next` stays null, because an
            # unconditional install suggestion would be wrong there.
            git_root = git_root_for_message(repo_root)
            res = CommandResult(
                command="attention",
                status="cannot-run",
                exit_code=2,
                summary=(
                    "no AW project found at the working directory or any ancestor; "
                    "cd into the repository or pass --dir <repo>"
                ),
                next_actions=(
                    [
                        NextAction(
                            command="aw install .",
                            description="install agent-workflows in this repo",
                        )
                    ]
                    if git_root is not None
                    else []
                ),
            )
            return get_renderer(ctx).emit(res, ctx)
        sys.stderr.write(no_project_message("attention", repo_root) + "\n")
        return 3

    type_filters = parse_type_filters(getattr(args, "types", None))

    try:
        items, drift = scan(repo_root, type_filters=type_filters)
    except (
        Exception
    ) as exc:  # a could-not-run condition (missing contract symbol, etc.)
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="attention",
                status="cannot-run",
                exit_code=2,
                summary=f"could not run: {exc}",
                diagnostics=[
                    Diagnostic(
                        location=str(repo_root),
                        rule="attention.scan_error",
                        detail=str(exc),
                        severity="error",
                    )
                ],
            )
            return get_renderer(ctx).emit(res, ctx)
        sys.stderr.write(f"aw attention: could not run: {exc}\n")
        return 2

    all_items_by_id = {it.id: it for it in items if it.id}

    # attsel `fqnj8k` E-03: HOLD THE UNNARROWED SCAN RESULT for the selector match facts. `items` and
    # `drift` are both rebound by the filters below, and the match fact must be answered against what
    # the scan actually found rather than against what a filter left. Captured here, immediately after
    # the ONE scan, so no filter can have touched it and no second scan is needed in the common case.
    unnarrowed_items = list(items)
    unnarrowed_drift = list(drift)

    # worksequence i6015i E-04/E-09: apply the requested ORDER to the items the ONE existing scan
    # produced. Read through `getattr` with the contract default, matching how every other option on
    # this path is read, so a narrower caller (a test harness, or an alias parser) still works.
    #
    # ORDERING IS APPLIED AFTER the filters below, deliberately: sorting first and filtering second
    # would give the same sequence but would sort rows that are about to be discarded. The set of items
    # is decided ONLY by the filters, never by the order, which is what makes "ordering never filters"
    # true by construction rather than by assertion.
    order_by = getattr(args, "order_by", None) or A.ORDER_CLASS
    order_notices: List[str] = []

    type_filters = parse_type_filters(getattr(args, "types", None))
    if type_filters:
        items = [it for it in items if it.tree in type_filters]
        # attcor `rkn8ya` E-01: prune through the ONE shared helper, which retains a violation from a
        # SELECTED TREE even when the offending file produced no item. `selected_trees` is the
        # REQUESTED filter, not the surviving items' trees: a tree whose every file fails to parse has
        # no surviving item, and keying on the items would delete exactly the violations that matter.
        drift = prune_drift_to_selection(
            drift, items, repo_root, selected_trees=type_filters
        )

    selectors_arg = getattr(args, "selectors", None) or []
    selector_facts: Optional[SelectorMatchFacts] = None
    if selectors_arg:
        # attsel `fqnj8k` E-03: THE MATCH FACT IS COMPUTED AGAINST THE UNFILTERED SCAN, and that is
        # the load-bearing detail of this whole fix.
        #
        # `--type` narrowed `items` fifteen lines above, so asking "did this token match?" of the list
        # the selector filter RECEIVES answers NO for a token whose artifact `--type` already removed.
        # Measured at review: the same filter matches `sv0sf3` over the full 1063-item scan and 0 items
        # over the `-t plans` 661-item scan, so `aw att sv0sf3 -t plans` would be reported as a TYPO.
        # Reporting a FALSE no-match is a WORSE defect than the silence this change removes, so the
        # fact is pinned to a scan that no filter has narrowed.
        #
        # A SECOND SCAN IS PAID ONLY WHEN `--type` COULD HAVE HIDDEN A MATCH. `scan()` itself honors
        # `type_filters`, so under `--type` even `unnarrowed_items` never saw the other trees and the
        # only way to know whether a token matches one of them is to scan them. Without `--type`,
        # `unnarrowed_items` IS the complete scan and re-scanning would buy nothing: a full scan of this
        # repository measures about 1.3s against about 0.65s narrowed, and paying that on every plain
        # `aw att <id6>` would be a user-perceptible slowdown for no change in output.
        fact_items = unnarrowed_items
        fact_drift = unnarrowed_drift
        if type_filters:
            try:
                fact_items, fact_drift = scan(repo_root)
            except Exception:
                # A scan that fails here must not break the view: fall back to the narrowed result,
                # which can only ever UNDER-report a match. Under-reporting means the refusal does not
                # fire, i.e. the pre-change behavior, never a false accusation.
                fact_items, fact_drift = unnarrowed_items, unnarrowed_drift
        selector_facts = selector_match_facts(
            fact_items, selectors_arg, repo_root, drift=fact_drift
        )
        items = filter_items_by_selectors(items, selectors_arg, repo_root)
        drift = prune_drift_to_selection(
            drift, items, repo_root, selected_trees=type_filters or None
        )

    # attsel `fqnj8k` E-04/E-05/E-06/E-09/E-10: THE REFUSAL, EVALUATED ONCE, BEFORE EVERY
    # SURFACE-SPECIFIC BRANCH.
    #
    # WHY HERE AND NOT IN THE RENDERERS (decision D4, answering OQ-02). `--check` returns before the
    # board is composed, and so do `-id`/`--paths`/`--filenames`; a message appended to the board
    # reaches NEITHER, which is precisely how five output surfaces stayed silent while the defect was
    # thought to be about two. Evaluating the ONE predicate here is what makes all eight surfaces agree
    # without eight copies of it.
    #
    # AND IT IS A SEPARATE CONDITION FROM DRIFT, deliberately. A `Drift` record is a repository-CONTRACT
    # finding about an artifact; an unmatched token is an OPERATOR INPUT error. Routing the refusal
    # through the drift set would get the `--check` behavior for free but would make `--json`'s `valid`
    # flag mean "you typed wrong", and would leave the maintainer unable to relax OQ-02 without
    # touching the drift path.
    if selector_facts is not None and selector_facts.refusable:
        return _emit_unresolved_selector_refusal(
            selector_facts, args=args, ctx=ctx, repo_root=repo_root
        )

    status_filters = parse_status_filters(getattr(args, "status", None))
    has_terminal_status = any(
        s
        in (
            "done",
            "parked",
            "superseded",
            "not-executed",
            "implemented",
            "shipped",
            "abandoned",
        )
        for s in status_filters
    )
    if status_filters:
        items = [it for it in items if matches_status(it, status_filters)]

    priority_filters = parse_priority_filters(getattr(args, "priority", None))
    if priority_filters:
        items = [it for it in items if matches_priority(it, priority_filters)]

    blocking_filters = parse_blocking_filters(getattr(args, "blocking", None))
    if blocking_filters:
        items = [
            it for it in items if matches_blocking(it, blocking_filters, repo_root)
        ]

    readiness_filters = parse_readiness_filters(getattr(args, "readiness", None))
    if readiness_filters:
        items = [it for it in items if matches_readiness(it, readiness_filters)]

    open_questions_filter = getattr(args, "open_questions", False)
    if open_questions_filter:
        # attcor `rkn8ya` E-07: the FILTER, and ONLY the filter. The second narrowing that used to sit
        # here (dropping DONE/PARKED when `--all`/a selector/a terminal status was absent) has moved
        # to where every other default-visibility decision is already made: the RENDER stage.
        #
        # WHY THE MOVE, in one measurement: `--priority high --format json` kept 90 `done` + 2
        # `parked` items while `--open-questions --format json` kept 0 of either, because this was the
        # ONE filter applying default visibility in the filter stage. The JSON and `--agent` renderers
        # deliberately apply NO visibility narrowing, so the payload silently disagreed with every
        # other filter's payload.
        #
        # IT ALSO POISONED `--check`: the shrunken item set shrank `selected_paths`, so a contract
        # violation on a `done` artifact carrying open questions was pruned out of the drift set and
        # `--check` exited 0 on it.
        #
        # THE DEFAULT HUMAN BOARD IS UNCHANGED, and that is by construction rather than by care: the
        # render stage recomputes the SAME predicate (`args.all or selectors or has_terminal_status`)
        # and passes it as `show_all`, which `render_board`/`render_table`/`--id6-only` already honor.
        items = [it for it in items if (getattr(it, "oqs", 0) or 0) > 0]

    active_flag = getattr(args, "active", False)
    not_active_flag = getattr(args, "not_active", False)

    if active_flag:
        run_status_filters = {"any"}
    elif not_active_flag:
        run_status_filters = {"-", "none", "no", "false"}
    else:
        raw_run_st = (
            getattr(args, "run_status", None)
            or getattr(args, "arcive_state", None)
            or getattr(args, "active_state", None)
        )
        run_status_filters = parse_run_status_filters(raw_run_st)

    has_terminal_run_status = any(
        s in ("done", "failed", "completed", "executed", "any")
        for s in run_status_filters
    )
    if has_terminal_run_status:
        has_terminal_status = True

    order_keys = [k.strip() for k in order_by.split(",") if k.strip()]
    runs_in_order = any(k in ("runs", "run") for k in order_keys)
    runs_arg = getattr(args, "runs", False)
    runs_needed = (
        bool(runs_arg)
        or bool(run_status_filters)
        or runs_in_order
        or active_flag
        or not_active_flag
    )

    run_map = get_active_runs_map(repo_root) if (runs_needed and repo_root) else {}

    if run_status_filters:
        items = [
            it for it in items if matches_run_status(it, run_status_filters, run_map)
        ]

    if (
        any(
            (
                status_filters,
                priority_filters,
                blocking_filters,
                readiness_filters,
                open_questions_filter,
                run_status_filters,
            )
        )
        and drift
    ):
        # attcor `rkn8ya` E-01, the third of the three formerly-duplicated prune sites. A status,
        # priority, blocking, readiness, open-questions or run-status narrowing says nothing about
        # TYPES, so the tree selection passed through is whatever `--types` asked for (or every
        # tracked tree), and a malformed artifact's violation survives instead of being deleted with
        # the item it never produced.
        drift = prune_drift_to_selection(
            drift, items, repo_root, selected_trees=type_filters or None
        )

    # lanestrand-01 (`pr5b0t`) E-04/E-05/E-06: JOIN THE STRANDED LANES AT RENDER TIME, after the
    # artifact filters and before anything consumes `drift`.
    #
    # AFTER THE FILTERS DELIBERATELY. Each filter above prunes `drift` down to the SELECTED artifact
    # paths, and a lane's `Drift` location is a git BRANCH that matches no path, so adding lanes before
    # the filters would have every filter silently delete them. Adding them here also means one thing
    # for both surfaces: `render_json` derives its `stranded_lanes` list from this same set, and
    # `core.drift_exit_code` reads it for the exit code, so the payload's `valid` flag and the gate can
    # never disagree.
    #
    # SUPPRESSED UNDER AN EXPLICIT NARROWING, matching what the filters above already do to artifact
    # drift: a user who asked for `--types specs` asked about specs, and a lane belongs to no tree they
    # selected. The DEFAULT invocation (what CI and an agent run) is the one that must fail closed, and
    # it does.
    if not type_filters and not selectors_arg:
        drift = drift + stranded_lane_drift(repo_root)
        drift.sort(key=lambda d: (d.location, d.rule))

    # Re-order the (possibly filtered) items. `scan()` already returned them in the default order, so
    # for `-o class` this is a no-op re-sort of an already-sorted list and the output is unchanged.
    if order_by != A.ORDER_CLASS:
        items, order_notices = sort_items_with_notices(
            items, order_by, repo_root=repo_root, run_map=run_map
        )

    fmt = getattr(args, "format", None)

    if check:
        exit_code = core.drift_exit_code(drift)
        status = "clean" if exit_code == 0 else "findings"
        summary = (
            f"{len(items)} items checked, 0 violations"
            if exit_code == 0
            else f"{len(drift)} finding(s) detected across {len(items)} items"
        )
        if ctx.is_agent or ctx.is_json:
            diagnostics = [
                Diagnostic(
                    location=d.location,
                    rule=d.rule,
                    detail=d.detail,
                    severity="error",
                )
                for d in drift
            ]
            evidence = [
                Evidence(
                    key="attention",
                    value={"items": len(items), "drift": len(drift)},
                    status=status,
                )
            ]
            res = CommandResult(
                command="attention",
                status=status,
                exit_code=exit_code,
                summary=summary,
                diagnostics=diagnostics,
                evidence=evidence,
                data={
                    "items": [it._asdict() for it in items],
                    "drift": [d._asdict() for d in drift],
                },
            )
            return get_renderer(ctx).emit(res, ctx)

        if drift:
            for d in drift:
                sys.stdout.write(f"{d.location}: {d.rule}: {d.detail}\n")
        else:
            sys.stdout.write("aw attention --check: the view is valid.\n")
        return exit_code

    id6_only = getattr(args, "id6_only", False)
    paths_only = getattr(args, "paths", False)
    filenames_only = getattr(args, "filenames", False)

    if id6_only or paths_only or filenames_only:
        show_all = (
            getattr(args, "all", False) or bool(selectors_arg) or has_terminal_status
        )
        if not show_all:
            visible = [
                it for it in items if it.attention_class not in (A.DONE, A.PARKED)
            ]
        else:
            visible = list(items)

        if id6_only:
            for it in visible:
                val = extract_id6(it)
                if val:
                    sys.stdout.write(f"{val}\n")
        elif paths_only:
            for it in visible:
                sys.stdout.write(f"{it.path}\n")
        elif filenames_only:
            for it in visible:
                name = Path(it.path).name
                sys.stdout.write(f"{name}\n")
        return core.drift_exit_code(drift)

    if ctx.is_agent:
        exit_code = core.drift_exit_code(drift)
        status = "clean" if exit_code == 0 else "findings"
        summary = f"{len(items)} attention item(s)"
        # worksequence i6015i E-08: an ordering notice must reach an AGENT too, not only the human
        # board, or `--agent -o depth` would silently absorb a cycle. Emitted as a WARNING diagnostic
        # so it is visible without affecting the exit code (which `core.drift_exit_code(drift)` above
        # has already decided from the drift set alone).
        notice_diagnostics = [
            Diagnostic(
                location=str(repo_root),
                rule="attention.order-notice",
                detail=notice,
                severity="warning",
            )
            for notice in order_notices
        ]
        diagnostics = notice_diagnostics + [
            Diagnostic(
                location=d.location,
                rule=d.rule,
                detail=d.detail,
                severity="error",
            )
            for d in drift
        ]
        evidence = [
            Evidence(
                key="attention",
                value={"items": len(items), "drift": len(drift)},
                status=status,
            )
        ]
        res = CommandResult(
            command="attention",
            status=status,
            exit_code=exit_code,
            summary=summary,
            diagnostics=diagnostics,
            evidence=evidence,
            data={
                "items": [it._asdict() for it in items],
                "drift": [d._asdict() for d in drift],
            },
        )
        return get_renderer(ctx).emit(res, ctx)

    if fmt == "json" or ctx.is_json:
        sys.stdout.write(render_json(items, drift))
    else:
        # Color only for a real TTY (should_color honors NO_COLOR/FORCE_COLOR/TERM/isatty);
        # --no-color forces plain, which also yields the machine-readable [tree] form.
        color = False if getattr(args, "no_color", False) else None
        term = T.Term(stream=sys.stdout, color=color)
        colored = bool(getattr(term, "color", False))
        long = getattr(args, "long", False)
        show_all = (
            getattr(args, "all", False) or bool(selectors_arg) or has_terminal_status
        )
        details = getattr(args, "details", False)
        runs_mode = runs_needed

        if not colored:
            if is_explicit_order(order_by):
                board = render_board(
                    items,
                    drift,
                    show_all=show_all,
                    term=term,
                    long=long,
                    details=details,
                    legend=False,
                    repo_root=repo_root,
                    order_by=order_by,
                    runs_mode=runs_mode,
                    run_map=run_map,
                )
            else:
                blockers = release_blockers(items, repo_root)
                blocker_keys = {it.path for it in blockers}
                main_items = [it for it in items if it.path not in blocker_keys]

                board = render_board(
                    main_items,
                    drift,
                    show_all=show_all,
                    term=term,
                    long=long,
                    details=details,
                    legend=False,
                    repo_root=repo_root,
                    order_by=order_by,
                    runs_mode=runs_mode,
                    run_map=run_map,
                )
                if blockers:
                    # Name the release the blockers gate (id6 + version), not just a count, so the
                    # planned release is visible during ordinary tool use - not only a hidden record.
                    try:
                        from agent_workflows import releases as _releases

                        _rel = _releases.describe_planned_release(repo_root)
                    except Exception:
                        _rel = None
                    _rel_label = f" for {_rel[1]} ({_rel[0]})" if _rel else ""
                    rel_header = f"release-blockers{_rel_label} ({len(blockers)})"
                    board += f"## {rel_header}\n"
                    # Render each blocker in the SAME compact columnar form as active/ready/blocked
                    # (not a raw absolute path), so the section reads consistently with the board.
                    for it in blockers:
                        run_st = _item_run_status(it, run_map) if runs_mode else None
                        board += (
                            _render_item_row(
                                it,
                                it.attention_class,
                                term,
                                colored,
                                long,
                                details=details,
                                runs_mode=runs_mode,
                                run_state=run_st,
                            )
                            + "\n"
                        )
        else:
            board = render_board(
                items,
                drift,
                show_all=show_all,
                term=term,
                long=long,
                details=details,
                legend=True,
                repo_root=repo_root,
                order_by=order_by,
                id_map=all_items_by_id,
                runs_mode=runs_mode,
                run_map=run_map,
            )
        # bklggrad orb9zb E-06: advisory release-gate warnings (human view only; NEVER affect the
        # exit code). Surfaces orphaned-live-blocker (an open blocking item already handed off to a
        # plan) with a de-gate/close hint.
        run_gate_warnings = not type_filters or "backlog" in type_filters
        gate_warnings = []
        if run_gate_warnings:
            try:
                from agent_workflows import check_engine as _ce

                gate_warnings = _ce.release_gate_warnings(repo_root)
                if selectors_arg and gate_warnings:
                    selected_paths = {(repo_root / it.path).resolve() for it in items}
                    gate_warnings = [
                        w
                        for w in gate_warnings
                        if (repo_root / w.location).resolve() in selected_paths
                    ]
            except Exception:
                gate_warnings = []
        if gate_warnings:
            gw_header = f"release-gate-warnings ({len(gate_warnings)})"
            if colored:
                board += term.color256(gw_header, 214, bold=True) + "\n"
            else:
                board += f"## {gw_header}\n"
            # Consistent identity-stem form + an indented, cut-and-paste Fix: line (the detail
            # carries a '\n    Fix: <cmd>' suffix). Uncolored/agent view keeps the full path.
            for w in gate_warnings:
                detail, _, fix = w.detail.partition("\n    Fix:")
                ident = (
                    _identity_stem(w.location) if colored and not long else w.location
                )
                board += f"- {ident}: {w.rule}: {detail}\n"
                if fix.strip():
                    board += f"    Fix: {fix.strip()}\n"

        # lanestrand-01 (`pr5b0t`) E-04: the LOUD stranded-lane section. It is deliberately DUPLICATED
        # information: the same lanes already appear in the board's `VIEW INVALID` violation block
        # (because they are `Drift` records, which is what makes `--check` fail), and this section
        # restates them under a heading naming the condition, with the remedy, so an operator reading a
        # long board cannot mistake unintegrated work for one more contract nit. NOT advisory, unlike
        # the two sections around it: these findings DO drive the exit code, through the drift set.
        lane_section = render_stranded_lane_section(drift)
        if lane_section:
            if colored:
                first, _, rest = lane_section.partition("\n")
                board += term.color256(first.lstrip("# "), 203, bold=True) + "\n" + rest
            else:
                board += lane_section

        # worksequence i6015i E-08: surface an ordering notice (currently a dependency cycle under
        # `-o depth`) VISIBLY rather than absorbing it. Advisory only: it never affects the exit code,
        # which stays owned by the drift set, because the fail-closed finding for a cyclic edge set
        # belongs to `aw check`, not to a display option.
        if order_notices:
            oc_header = f"order-notices ({len(order_notices)})"
            if colored:
                board += term.color256(oc_header, 214, bold=True) + "\n"
            else:
                board += f"## {oc_header}\n"
            for notice in order_notices:
                board += f"- {notice}\n"

        footer_lines: list[str] = []
        has_hidden = (
            any(it.attention_class in (A.DONE, A.PARKED) for it in items)
            and not show_all
        )
        needs_setup = setup_needed(repo_root)
        if needs_setup and has_hidden:
            footer_lines.append(
                "TODO: Run `/aw setup-repo` to set up this repo. Use `aw att --all` to see old stuff."
            )
        elif needs_setup:
            footer_lines.append("TODO: Run `/aw setup-repo` to set up this repo.")
        elif has_hidden and colored:
            footer_lines.append("Use `aw att --all` to see old stuff.")

        if footer_lines:
            board = board.rstrip("\n") + "\n" + "\n".join(footer_lines) + "\n"
        else:
            board = board.rstrip("\n") + "\n"
        sys.stdout.write(board)
    # a plain view still fails closed if invalid, so consumers cannot treat an invalid view as authoritative
    return core.drift_exit_code(drift)

"""Attention-visible backlog tier (spec 20260813-1833-01; IPD backlogtier-01/crv40v).

A lightweight, tracked `records`-class sub-tree of backlog items so COMMITTED work surfaces in
`aw attention` (which feeds `/whatnext`) while uncommitted "maybes" stay quiet. Closes the
false-comprehensiveness gap where committed work living only in free-prose `TODO.md` was invisible
to the attention view.

Layout (dual-path like plans: `.agents/backlog/` pre-migration, `.aw/records/backlog/` post):

    <backlog-root>/
      open/      committed, actionable now        (attention: ready)
      blocked/   committed but gated              (attention: blocked; requires a typed gate)
      parked/    uncommitted "maybes"             (attention: parked; hidden from the default board)
      done/      completed/closed                 (attention: done)

One item is one file with `- Field:` BULLET metadata (consistent with specs/plans, and so the
existing attention `Gate-Kind`/`Gate-Ref` grammar is reused verbatim), then a prose body.

The work-nature field is `- Work-Kind:` (wkindname Order 01 / 9trlc3). It was formerly spelled
`- Kind:`, which collided with four unrelated uses of that token (an IPD's structural kind, a research
document type, a comms message kind, and this module's own `- Gate-Kind:`). The legacy spelling is
still ACCEPTED on read via a deliberately retained dual-read window; only the canonical spelling is
ever WRITTEN. The field remains REQUIRED here (an absent value is `backlog.kind-invalid`), which is
deliberately asymmetric with plans and specs where it is optional: the Set unified the NAME, not the
requiredness.

    - Id: <id6>
    - Status: open | graduated | blocked | parked | done
    - Set: <terse-id>
    - Priority: high | medium | low
    - Work-Kind: bug | feature | chore | security | followup
    - Summary: <one line>
    - Gate-Kind: <artifact|decision|todo|issue|date|external>   # iff blocked
    - Gate-Ref: <ref>                                            # iff blocked

    ## Workflow history
    - YYYY-MM-DD <event> (<actor>): <one line>

    <free prose body>

Status is encoded BOTH by directory and by the `- Status:` bullet, and the two MUST agree.
`aw backlog new|set|check`: `new` creates a conformant item; `set` transitions status (moving the
file between the disposition dirs) and appends history; `check` validates the tree fail-closed with
the shared `Drift`/`--agent`/exit convention. Stdlib only; reuses `artifact_core` + `attention_contract`.

Both CLASSIFICATION fields (`- Priority:` and `- Work-Kind:`) are settable on an EXISTING item via
`aw backlog set --priority` / `--work-kind` (bklgkind b5sfwm), on both spellings of that verb, and the
write PERSISTS ON A NO-OP TRANSITION so a pure reclassification needs no status change. NEITHER FLAG
ACCEPTS THE `-` CLEARING SENTINEL, and the omission is deliberate rather than an oversight (OQ-02,
ruled 2026-09-10): both fields are REQUIRED here, so clearing one would leave an item `validate_item`
reports as `backlog.priority-invalid`/`backlog.kind-invalid` and `aw check backlog` exits nonzero on.
A required field may be RETARGETED, never emptied. The sibling `aw ipd set`/`aw specs set` flags do
still accept `-` because the field is optional on those record types today; that spelling is a known
loose end for `planprio` child `lkexaw`, which owns making both fields required on plans too, and is
not a precedent to copy back here.
"""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from agent_workflows import artifact_core as core
from agent_workflows import attention_contract as A
from agent_workflows import config as _config
from agent_workflows import lifecycle_dirs as _LD
from agent_workflows import record_placement as _rp

BACKLOG_ROOTS = (".agents/backlog", ".aw/records/backlog")
# bklgrad Order 01 (v58bvy) E-01: `graduated` sits between `open` and `done` and means the item's
# DESIGN work was handed off to artifacts (a plan/spec carrying `From-Backlog`) while its code is NOT
# yet written. Without it the lifecycle is effectively binary and an item whose spec + plans exist
# still reads `open` (indistinguishable from untouched work), with `done` the only alternative - a
# false claim of implementation that also drops any release gate. `graduated` is deliberately NOT a
# release-gate satisfier: `aw attention` maps it to `active` (not `done`), so a graduated blocker stays
# in the outstanding release-blocker set, and closing to `done` still requires the HANDOFF / SATISFIED
# / DE-GATED legitimacy fixes in `check_engine.evaluate_blocking_close`.
STATUS_DIRS = _LD.LIFECYCLE_SUBDIRS["backlog"]
STATUSES = frozenset(STATUS_DIRS)
PRIORITIES = frozenset(("high", "medium", "low"))
KINDS = frozenset(("bug", "feature", "chore", "security", "followup"))

# gatekinds kxawm4: the work-kinds whose items AUTOMATICALLY carry a release gate are configured
# per repository via `release_gate_work_kinds` in `.aw/config/project.json` (reading
# `config.release_gate_work_kinds`). `GATE_DEFAULT_KINDS` is retained as a deprecated alias of
# `config.RELEASE_GATE_WORK_KINDS_DEFAULT` (`bug` alone) so external callers do not break.
# The default remains `bug` alone: `security` is deliberately excluded by default because the maintainer
# measured agent security classifications in THIS repository to be overstated, so a default that the
# reference repo must immediately override is a bad default.
GATE_DEFAULT_KINDS = _config.RELEASE_GATE_WORK_KINDS_DEFAULT

# The statuses a NEW item may be born with that must NOT receive the defaulted gate. `done` because a
# gated closed item with no handoff/evidence/de-gate is a SHIPPED exit-blocking error
# (`check.blocking-item-closed-without-gate`), so defaulting there would manufacture the very
# violation this Set exists to eliminate; `parked` because a parked maybe is not live work (the
# attention view hides it), so gating a release on one asserts an obligation nobody has taken on.
_GATE_DEFAULT_SKIP_STATUSES = frozenset(("done", "parked"))

# Bullet-metadata field regexes (mirroring attention_contract's SPEC_STATUS_RE / GATE_*_RE style).
_ID_RE = re.compile(r"^- Id:[ \t]*(?P<value>\S+)[ \t]*$")
_STATUS_RE = re.compile(r"^- Status:[ \t]*(?P<value>\S+)[ \t]*$")
_SET_RE = re.compile(r"^- Set:[ \t]*(?P<value>\S+)[ \t]*$")
_PRIORITY_RE = re.compile(r"^- Priority:[ \t]*(?P<value>\S+)[ \t]*$")
# wkindname Order 01 (9trlc3) E-01: DUAL-READ window for the work-nature field. `- Work-Kind:` is the
# canonical on-disk spelling; `- Kind:` is the legacy one, still ACCEPTED so a partially migrated tree,
# a long-lived branch, or a stash never stops parsing. Both patterns are anchored on the FULL LINE and
# never on the bare token `Kind`, because this same module parses a DISTINCT `- Gate-Kind:` field
# (see `A.GATE_KIND_RE` below) that a substring-based match would silently capture or corrupt.
# The window is deliberately RETAINED after the corpus migration as cheap insurance; it is not dead code.
_WORK_KIND_RE = re.compile(r"^- Work-Kind:[ \t]*(?P<value>\S+)[ \t]*$")
_KIND_RE = re.compile(r"^- Kind:[ \t]*(?P<value>\S+)[ \t]*$")
_SUMMARY_RE = re.compile(r"^- Summary:[ \t]*(?P<value>.+?)[ \t]*$")
_BLOCKS_RELEASE_RE = re.compile(r"^- Blocks-Release:[ \t]*(?P<value>\S+)[ \t]*$")
_RELEASE_EXEMPT_KIND_RE = re.compile(
    r"^- Release-Exempt-Kind:[ \t]*(?P<value>\S+)[ \t]*$"
)
_RELEASE_EXEMPT_REF_RE = re.compile(
    r"^- Release-Exempt-Ref:[ \t]*(?P<value>.+?)[ \t]*$"
)
_CLOSE_EVIDENCE_RE = re.compile(r"^- Close-Evidence:[ \t]*(?P<value>.+?)[ \t]*$")
_TOP_KEY_RE = re.compile(r"^- ([A-Za-z0-9_-]+):(?:\s*(.*))?$")
_TEMPLATE_OWNED_KEYS = frozenset(
    (
        "Id",
        "Status",
        "Set",
        "Priority",
        "Work-Kind",
        "Kind",
        "Summary",
        "Gate-Kind",
        "Gate-Ref",
    )
)


class CandidateDuplicate:
    """A candidate duplicate backlog item identified by the near-duplicate guard."""

    __slots__ = ("id", "status", "summary", "path", "shared_tokens", "reason")

    def __init__(
        self,
        *,
        id: str,
        status: str,
        summary: str,
        path: Optional[str] = None,
        shared_tokens: Optional[set] = None,
        reason: Optional[str] = None,
    ) -> None:
        self.id = id
        self.status = status
        self.summary = summary
        self.path = path
        self.shared_tokens = shared_tokens or set()
        self.reason = reason or ""


#: Near-duplicate advisory detection limits and coverage (IPD fwgq2u / OQ-01 / E-02).
#: Follows aw graduation's advisory-not-refusal precedent (graduate jxxec8) of stating its own
#: detection limits in output so silence is never misread as proof of uniqueness.
BACKLOG_DUPLICATE_GUARD_LIMITS: Tuple[Tuple[str, str, str], ...] = (
    (
        "exact identifier and token overlap",
        "DETECTABLE",
        "items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported",
    ),
    (
        "paraphrased defect descriptions",
        "PARTLY DETECTABLE",
        "defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically",
    ),
    (
        "distinct issues referencing the same test or symbol",
        "NOT DETECTABLE",
        "items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required",
    ),
)

BACKLOG_DUPLICATE_GUARD_COVERAGE: str = (
    "Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), "
    "matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or "
    "using disjoint vocabulary are not indexed."
)

_DISTINCTIVE_TOKEN_RE = re.compile(
    r"\b(?:"
    r"test_[a-zA-Z0-9_]+"
    r"|Test[A-Za-z0-9]+"
    r"|[A-Z][A-Z0-9_]{2,}[A-Z0-9]"
    r"|[a-zA-Z0-9_]+\.py"
    r"|[a-z0-9]+(?:_[a-z0-9]+){2,}"
    r")\b"
)

_DISTINCTIVE_TOKEN_EXCLUSIONS = frozenset(
    {
        "OPEN",
        "DONE",
        "TODO",
        "GATE",
        "HTTP",
        "JSON",
        "HTML",
        "YAML",
        "JSONL",
        "HEAD",
        "SPEC",
        "TRUE",
        "FALSE",
        "WORK_KIND",
        "GATE_KIND",
        "GATE_REF",
        "BLOCKS_RELEASE",
        "SET",
        "STATUS",
        "PRIORITY",
        "SUMMARY",
        "ID",
    }
)


def extract_distinctive_tokens(text: str) -> set:
    """Extract distinctive identifiers (test functions, test classes, env vars, python files, multi-part symbols)."""
    found = set()
    for m in _DISTINCTIVE_TOKEN_RE.finditer(text):
        tok = m.group(0)
        if tok.isupper() and "_" not in tok:
            continue
        if tok in _DISTINCTIVE_TOKEN_EXCLUSIONS:
            continue
        found.add(tok)
    return found


def find_duplicate_candidates_in_items(
    items_data: List[Tuple[Path, BacklogItem, str]],
    summary: str,
    body: str = "",
) -> List[CandidateDuplicate]:
    """Scan existing backlog items for potential near-duplicates using distinctive token overlap.

    Advisory-only: never refuses, reports candidates across every status dir (open, graduated,
    blocked, parked, done).
    """
    in_sum_tokens = extract_distinctive_tokens(summary or "")
    in_all_tokens = extract_distinctive_tokens(f"{summary or ''} {body or ''}")
    if not in_all_tokens:
        return []

    candidates: List[CandidateDuplicate] = []
    for f, item, text in items_data:
        if not item.id:
            continue
        item_summary = item.summary or ""
        # 1. Shared distinctive token in summary (strongest signal)
        shared_sum = {tok for tok in in_sum_tokens if tok in item_summary}
        if shared_sum:
            candidates.append(
                CandidateDuplicate(
                    id=item.id,
                    status=item.status or "open",
                    summary=item_summary,
                    path=str(f),
                    shared_tokens=shared_sum,
                    reason="summary token overlap",
                )
            )
            continue
        # 2. Co-occurrence of >= 2 distinctive tokens in full text
        shared_all = {tok for tok in in_all_tokens if tok in text}
        if len(shared_all) >= 2:
            candidates.append(
                CandidateDuplicate(
                    id=item.id,
                    status=item.status or "open",
                    summary=item_summary,
                    path=str(f),
                    shared_tokens=shared_all,
                    reason="co-occurring tokens",
                )
            )
    return candidates


def find_duplicate_candidates(
    repo_root: Path,
    summary: str,
    body: str = "",
) -> List[CandidateDuplicate]:
    """Scan the repo's backlog items for potential duplicates of a proposed filing."""
    items_data: List[Tuple[Path, BacklogItem, str]] = []
    for f in _iter_items(repo_root):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        items_data.append((f, parse_item(text), text))
    return find_duplicate_candidates_in_items(items_data, summary=summary, body=body)


class BacklogItem:
    """Parsed backlog item fields (from the leading `- Field:` bullet block)."""

    __slots__ = (
        "blocks_release",
        "close_evidence",
        "gate_kind",
        "gate_ref",
        "id",
        "kind",
        "priority",
        "release_exempt_kind",
        "release_exempt_ref",
        "set",
        "status",
        "summary",
    )

    def __init__(self) -> None:
        self.id: Optional[str] = None
        self.status: Optional[str] = None
        self.set: Optional[str] = None
        self.priority: Optional[str] = None
        self.kind: Optional[str] = None
        self.summary: Optional[str] = None
        self.gate_kind: Optional[str] = None
        self.gate_ref: Optional[str] = None
        self.blocks_release: Optional[str] = None
        self.release_exempt_kind: Optional[str] = None
        self.release_exempt_ref: Optional[str] = None
        self.close_evidence: Optional[str] = None


def parse_item(text: str) -> BacklogItem:
    """Parse the leading bullet-metadata block. Missing fields stay None (validation reports them)."""

    item = BacklogItem()
    # E-01 dual-read: collect the two spellings separately so precedence is resolved ONCE, after the
    # scan, rather than depending on which line happened to come first in the file.
    work_kind = None
    legacy_kind = None
    for line in text.split("\n"):
        if line.startswith("## ") or (line and not line.startswith("- ")):
            # metadata block ends at the first non-bullet, non-blank line or the first H2
            if line.startswith("## "):
                break
            # a non-bullet content line: metadata block is over
            if line.strip() and not line.startswith("- "):
                break
        for attr, rx in (
            ("id", _ID_RE),
            ("status", _STATUS_RE),
            ("set", _SET_RE),
            ("priority", _PRIORITY_RE),
            ("summary", _SUMMARY_RE),
            ("blocks_release", _BLOCKS_RELEASE_RE),
            ("release_exempt_kind", _RELEASE_EXEMPT_KIND_RE),
            ("release_exempt_ref", _RELEASE_EXEMPT_REF_RE),
            ("close_evidence", _CLOSE_EVIDENCE_RE),
        ):
            m = rx.match(line)
            if m and getattr(item, attr) is None:
                setattr(item, attr, m.group("value"))
        # E-01 dual-read: match each spelling on its OWN full-line pattern. `- Gate-Kind:` cannot
        # satisfy either, which is the whole point of anchoring on the full line.
        mw = _WORK_KIND_RE.match(line)
        if mw and work_kind is None:
            work_kind = mw.group("value")
        mk_legacy = _KIND_RE.match(line)
        if mk_legacy and legacy_kind is None:
            legacy_kind = mk_legacy.group("value")
        mk = A.GATE_KIND_RE.match(line)
        if mk and item.gate_kind is None:
            item.gate_kind = mk.group("value")
        mr = A.GATE_REF_RE.match(line)
        if mr and item.gate_ref is None:
            item.gate_ref = mr.group("value")
    # E-01 precedence: the canonical spelling WINS when an item somehow carries both (e.g. a
    # half-merged branch). Absent both, `kind` stays None and validation reports it, unchanged.
    item.kind = work_kind if work_kind is not None else legacy_kind
    return item


def _dir_status(path: Path) -> Optional[str]:
    """The disposition-directory status for an item path (its parent dir name), or None."""

    parent = path.parent.name
    return parent if parent in STATUSES else None


def drift_location(path: Path) -> str:
    """The REPO-RELATIVE POSIX location to put in a Drift record for ``path``.

    Delegates to ``specs.drift_location`` so truncation at records segments
    (both canonical ``.aw/records/`` and legacy ``.agents/``) and fallback
    behavior remain defined in one place.
    """
    from agent_workflows import specs

    return specs.drift_location(path)


def validate_item(path: Path, text: str) -> List[core.Drift]:
    """Validate one backlog item fail-closed. Returns Drift records (empty == conformant)."""

    rel = drift_location(path)
    drift: List[core.Drift] = []
    item = parse_item(text)

    if not item.id or not core.is_valid_id6(item.id):
        drift.append(
            core.Drift(rel, "backlog.id-invalid", f"missing/invalid id6: {item.id!r}")
        )
    if item.status not in STATUSES:
        drift.append(
            core.Drift(
                rel,
                "backlog.status-invalid",
                f"status not in {sorted(STATUSES)}: {item.status!r}",
            )
        )
    else:
        d = _dir_status(path)
        if d is not None and d != item.status:
            drift.append(
                core.Drift(
                    rel,
                    "backlog.status-dir-mismatch",
                    f"status {item.status!r} != directory {d!r}",
                )
            )
    if item.priority not in PRIORITIES:
        drift.append(
            core.Drift(
                rel,
                "backlog.priority-invalid",
                f"priority not in {sorted(PRIORITIES)}: {item.priority!r}",
            )
        )
    if item.kind not in KINDS:
        drift.append(
            core.Drift(
                rel,
                "backlog.kind-invalid",
                f"kind not in {sorted(KINDS)}: {item.kind!r}",
            )
        )
    if not item.set:
        drift.append(core.Drift(rel, "backlog.set-missing", "missing - Set: bullet"))
    if not item.summary or not item.summary.strip():
        drift.append(
            core.Drift(rel, "backlog.summary-missing", "missing/empty - Summary:")
        )
    elif not A.is_safe_descriptive(item.summary):
        drift.append(
            core.Drift(
                rel,
                "backlog.summary-unsafe",
                "summary not a single bounded control-char-free line",
            )
        )

    # Gate present-and-valid IFF blocked; absent otherwise.
    has_gate = item.gate_kind is not None or item.gate_ref is not None
    if item.status == "blocked":
        if not item.gate_kind or not item.gate_ref:
            drift.append(
                core.Drift(
                    rel,
                    "backlog.gate-missing",
                    "blocked item requires - Gate-Kind: and - Gate-Ref:",
                )
            )
        else:
            if item.gate_kind not in A.GATE_KINDS:
                drift.append(
                    core.Drift(
                        rel,
                        "backlog.gate-kind-invalid",
                        f"Gate-Kind not in {sorted(A.GATE_KINDS)}: {item.gate_kind!r}",
                    )
                )
            elif not A.validate_gate_ref(item.gate_kind, item.gate_ref):
                drift.append(
                    core.Drift(
                        rel,
                        "backlog.gate-ref-invalid",
                        f"Gate-Ref invalid for kind {item.gate_kind!r}: {item.gate_ref!r}",
                    )
                )
    elif has_gate:
        drift.append(
            core.Drift(
                rel,
                "backlog.gate-unexpected",
                "gate fields present on a non-blocked item",
            )
        )

    # Release exemption validation (IPD ghna7l E-02).
    has_exempt_kind = item.release_exempt_kind is not None
    has_exempt_ref = item.release_exempt_ref is not None
    if has_exempt_kind != has_exempt_ref:
        drift.append(
            core.Drift(
                rel,
                "backlog.release-exempt-incomplete",
                "release exemption requires both - Release-Exempt-Kind: and - Release-Exempt-Ref:",
            )
        )
    elif has_exempt_kind and has_exempt_ref:
        if item.release_exempt_kind not in A.GATE_KINDS:
            drift.append(
                core.Drift(
                    rel,
                    "backlog.release-exempt-kind-invalid",
                    f"Release-Exempt-Kind not in {sorted(A.GATE_KINDS)}: {item.release_exempt_kind!r}",
                )
            )
        elif not A.validate_gate_ref(item.release_exempt_kind, item.release_exempt_ref):
            drift.append(
                core.Drift(
                    rel,
                    "backlog.release-exempt-ref-invalid",
                    f"Release-Exempt-Ref invalid for kind {item.release_exempt_kind!r}: {item.release_exempt_ref!r}",
                )
            )
        elif item.blocks_release and item.blocks_release != "-":
            drift.append(
                core.Drift(
                    rel,
                    "backlog.release-exempt-contradicts-gate",
                    f"item carries both a valid release exemption and - Blocks-Release: {item.blocks_release}",
                )
            )

    # gateatrest f7igdu E-02: validate close_evidence shape fail-closed
    if item.close_evidence is not None and not A.is_safe_descriptive(
        item.close_evidence
    ):
        drift.append(
            core.Drift(
                rel,
                "backlog.close-evidence-unsafe",
                "close evidence not a single bounded control-char-free line",
            )
        )

    return drift


def _iter_items(repo_root: Path) -> List[Path]:
    """Every backlog item file under either layout's status dirs (README excluded), sorted."""

    files: List[Path] = []
    for root_rel in BACKLOG_ROOTS:
        root = repo_root / root_rel
        for status in STATUS_DIRS:
            d = root / status
            if d.is_dir():
                for f in sorted(d.glob("*.md")):
                    if f.name != "README.md":
                        files.append(f)
    return sorted(set(files))


def existing_backlog_ids(repo_root: Path) -> set:
    """The set of `- Id:` id6 values across all backlog items (any status dir, either layout).

    Used by the `check.from-backlog-dangling` scan (bklggrad Order ku93tn) to confirm a plan's
    `From-Backlog` value resolves to a real backlog item."""

    ids: set = set()
    for f in _iter_items(Path(repo_root)):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        item = parse_item(text)
        if item.id:
            ids.add(item.id)
    return ids


# --------------------------------------------------------------------------------------
# CLI verbs: new | set | check
# --------------------------------------------------------------------------------------


def blocks_release_of_item(repo_root: Path, item_id6: Optional[str]) -> Optional[str]:
    """Return the `- Blocks-Release:` value of the backlog item with id6 `item_id6`, or None when the
    item does not exist or carries no gate.

    nobugship di08i9 E-03: the lookup the graduation inheritance needs, so a setter can carry an
    item's gate onto the plan or spec that graduated from it. Kept HERE, beside `existing_backlog_ids`
    and `_iter_items`, because the backlog module already owns reading a backlog item's metadata; a
    setter reaching into the backlog tree with its own regex would be a second reader of the same
    field."""

    if not item_id6 or item_id6 == "-":
        return None
    for f in _iter_items(Path(repo_root)):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        item = parse_item(text)
        if item.id == item_id6:
            return item.blocks_release
    return None


def find_item(repo_root: Path, item_id6: Optional[str]) -> Optional[BacklogItem]:
    """Return the parsed backlog item whose `- Id:` is `item_id6`, or None when there is none.

    planprio lkexaw: `aw ipd scaffold --from-backlog` reads the item's Priority, Work-Kind and
    Blocks-Release through this, so the backlog module stays the one reader of a backlog item's
    metadata (the same reason `blocks_release_of_item` lives here)."""

    if not item_id6:
        return None
    for f in _iter_items(Path(repo_root)):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        item = parse_item(text)
        if item.id == item_id6:
            return item
    return None


def decide_gate_default(
    repo_root: Path,
    *,
    kind: Optional[str],
    status: Optional[str],
    explicit_blocks_release: Optional[str],
    existing_blocks_release: Optional[str] = None,
    is_exempt: bool = False,
) -> Tuple[Optional[str], Optional[str]]:
    """Decide whether an item should have `- Blocks-Release:` DEFAULTED, and say why either way.

    nobugship di08i9 E-01/E-02 / relexempt ghna7l E-04. Returns `(value_to_apply, notice)`: `value_to_apply` is the gate to
    write (today always `next`) or None to write nothing, and `notice` is the human/agent-facing
    explanation, or None when no defaulting decision arose at all (so a non-bug item stays silent).

    THIS IS THE SINGLE AUTHORITY FOR THE DECISION, deliberately, because it is consumed from THREE
    call sites that must not drift: `run_new` (creation), `run_set` (the `--status` spelling of
    `aw backlog set`), and `status_set.apply_status_change` (the positional spelling). A default wired
    into one spelling of the setter and not the other would fire inconsistently, which is worse than
    not shipping it because it teaches a false expectation.

    FIVE CONDITIONS SHAPE IT AND EACH WAS MEASURED, NOT ASSUMED:

    1. ONLY work kinds configured in `release_gate_work_kinds` (defaulting to `bug` alone via
       `config.RELEASE_GATE_WORK_KINDS_DEFAULT`) are defaulted. The rule is "we don't ship known
       bugs"; `security` is deliberately excluded from the default because the maintainer measured
       agent security classifications in THIS repository to be overstated (parent OQ-01).
    2. FALL BACK TO UNGATED WHEN `next` DOES NOT RESOLVE; DO NOT REFUSE. A fresh `aw install` creates
       NO `.aw/records/releases/` directory, so "no planned release" is the NORMAL state of an adopter
       repo. Refusing made `aw backlog new --work-kind bug` fail outright there and broke 10 existing
       tests whose fixtures create no release record. This follows the maintainer's 2026-09-10 ruling
       on `y4adch` OQ-01: a bad/absent REPOSITORY state falls back and warns (blast radius is every
       caller), while a bad PER-INVOCATION value refuses (blast radius is the one caller who typed
       it). So the resolution check is a PREDICATE here, and the explicit-value refusal in `run_new`
       is untouched.
    3. SKIP `done` AND `parked`. `--status done --work-kind bug` is legal, and defaulting a gate onto
       it manufactures an item the SHIPPED exit-blocking checker rejects immediately
       (`check.blocking-item-closed-without-gate`, ERROR: a done item carrying a gate with no handoff,
       evidence, or de-gate; driven and reproduced). `parked` is skipped for the same reason the
       attention view hides a parked maybe: it is not live work, so gating a release on it asserts an
       obligation nobody has taken on.
    4. AN EXPLICIT VALUE ALWAYS WINS, INCLUDING `-`. A default is not a prohibition; an author may
       legitimately file an ungated bug, and an existing gate is never overwritten.
    5. A VALID RELEASE EXEMPTION SUPPRESSES THE DEFAULT (IPD ghna7l E-04). When an item carries or is
       being given a valid typed release exemption, no gate is defaulted, avoiding contradictory gate
       generation.
    """

    if is_exempt:
        return None, None
    if explicit_blocks_release is not None:
        return None, None
    gating_kinds = _config.release_gate_work_kinds(repo_root)
    if (kind or "") not in gating_kinds:
        return None, None
    if existing_blocks_release:
        return None, None
    kind_label = f"{kind} item" if kind else "item"
    if (status or "") in _GATE_DEFAULT_SKIP_STATUSES:
        return None, (
            f"not defaulting - Blocks-Release: on this {kind_label} because its status is {status!r}: "
            "a gated done item is rejected by check.blocking-item-closed-without-gate, and a "
            "parked maybe is not live work"
        )

    from agent_workflows import releases as _releases

    if _releases.resolve_release(Path(repo_root), "next") is None:
        return None, (
            f"not defaulting - Blocks-Release: on this {kind_label} because 'next' does not resolve to a "
            "single planned release record; file it ungated and set the gate with "
            "`aw backlog set --blocks-release next` once a planned release exists"
        )
    return "next", (
        f"defaulted - Blocks-Release: next on this {kind_label} (no --blocks-release given): every live "
        f"{kind_label} gates the next release; pass '--blocks-release -' to file an ungated {kind_label}"
    )


def _resolve_backlog_root(repo_root: Path) -> Path:
    """Prefer an existing `.aw/records/backlog`, else the pre-migration `.agents/backlog` default."""

    new = repo_root / ".aw" / "records" / "backlog"
    if new.exists():
        return new
    return repo_root / ".agents" / "backlog"


def _refuse_unsafe_descriptive(
    verb: str,
    flag: str,
    value: Optional[str],
    *,
    bound_length: bool = True,
) -> Optional[str]:
    """Judge one descriptive value against Section 8.8 output-safety.

    When bound_length is True, delegates the verdict to attention_contract.is_safe_descriptive.
    When bound_length is False (line-integrity mode), validates newlines/carriage returns
    and control characters without applying the length bound.
    Returns None if value is None or valid, else a refusal message naming verb, flag, and cause.
    """
    if value is None:
        return None
    if bound_length:
        if A.is_safe_descriptive(value):
            return None
        if "\n" in value or "\r" in value:
            return f"{verb}: {flag} must not contain embedded newlines"
        if A._CONTROL_CHAR_RE.search(value):
            return f"{verb}: {flag} must not contain control characters"
        if len(value) > A.MAX_DESCRIPTIVE_LEN:
            return (
                f"{verb}: {flag} exceeds maximum length of {A.MAX_DESCRIPTIVE_LEN} "
                f"characters ({len(value)} > {A.MAX_DESCRIPTIVE_LEN})"
            )
        return f"{verb}: {flag} is not a valid descriptive field"
    else:
        has_newline = "\n" in value or "\r" in value
        is_safe_line = (
            not has_newline
            and A.is_safe_descriptive(
                value.replace("\n", "").replace("\r", "")[: A.MAX_DESCRIPTIVE_LEN]
            )
            and not A._CONTROL_CHAR_RE.search(value)
        )
        if is_safe_line:
            return None
        if has_newline:
            return f"{verb}: {flag} must not contain embedded newlines"
        if A._CONTROL_CHAR_RE.search(value):
            return f"{verb}: {flag} must not contain control characters"
        return f"{verb}: {flag} is not a valid descriptive field"


def _render_item(
    item: BacklogItem,
    body: str,
    message: Optional[str] = None,
    *,
    source_text: Optional[str] = None,
) -> str:
    if source_text is None:
        lines = [
            f"- Id: {item.id}",
            f"- Status: {item.status}",
            f"- Set: {item.set}",
            f"- Priority: {item.priority}",
            # E-02: only the canonical spelling is ever WRITTEN (the legacy one stays readable).
            f"- Work-Kind: {item.kind}",
            f"- Summary: {item.summary}",
        ]
        if item.status == "blocked":
            lines.append(f"- Gate-Kind: {item.gate_kind}")
            lines.append(f"- Gate-Ref: {item.gate_ref}")
        today = datetime.date.today().isoformat()
        msg = (message or "").strip() or item.summary
        lines.append("")
        lines.append("## Workflow history")
        lines.append(f"- {today} created (aw backlog): {msg}")
        lines.append("")
        lines.append(body.rstrip() + "\n" if body.strip() else "")
        return "\n".join(lines).rstrip() + "\n"

    # rendrop 2yqt0a E-01 / E-07: walk source text to preserve unrecognized fields in original order,
    # and preserve header prose written between the leading bullets and ## Workflow history.
    if "\n## Workflow history" in source_text:
        pre_hist = source_text.split("\n## Workflow history", 1)[0]
    elif source_text.startswith("## Workflow history"):
        pre_hist = ""
    else:
        pre_hist = source_text

    source_lines = pre_hist.split("\n")
    last_bullet_idx = -1
    for i, line in enumerate(source_lines):
        if line.startswith("## ") or (line.strip() and not line.startswith("- ")):
            break
        if line.startswith("- "):
            last_bullet_idx = i

    bullet_lines = source_lines[: last_bullet_idx + 1] if last_bullet_idx >= 0 else []
    bullet_text = "\n".join(bullet_lines)
    header_prose = pre_hist[len(bullet_text) :]

    source_keys = set()
    for line in bullet_lines:
        m = _TOP_KEY_RE.match(line)
        if m:
            k = m.group(1)
            source_keys.add("Work-Kind" if k == "Kind" else k)

    emitted_keys = set()
    out_bullets: List[str] = []

    def _insert_absent_gate_fields():
        if item.status == "blocked":
            if "Gate-Kind" not in emitted_keys and "Gate-Kind" not in source_keys:
                out_bullets.append(f"- Gate-Kind: {item.gate_kind}")
                emitted_keys.add("Gate-Kind")
            if "Gate-Ref" not in emitted_keys and "Gate-Ref" not in source_keys:
                out_bullets.append(f"- Gate-Ref: {item.gate_ref}")
                emitted_keys.add("Gate-Ref")

    for line in bullet_lines:
        m = _TOP_KEY_RE.match(line)
        if not m:
            # Rule (3): An unparseable bullet is emitted verbatim, not dropped.
            out_bullets.append(line)
            continue

        raw_key = m.group(1)
        canon_key = "Work-Kind" if raw_key == "Kind" else raw_key

        # Rule (2): Gate-Summary dropped when not blocked, kept when blocked.
        if raw_key == "Gate-Summary" or A.GATE_SUMMARY_RE.match(line):
            if item.status == "blocked":
                out_bullets.append(line)
            continue

        if canon_key not in _TEMPLATE_OWNED_KEYS:
            # Non-template-owned field (e.g. Blocks-Release, Custom-Field, Graduated-To, etc.)
            out_bullets.append(line)
            continue

        # Template-owned field.
        # Rule (1): emit each template-owned key at most once.
        # Track emitted keys; the legacy - Kind: line is substituted in place ONLY when no
        # - Work-Kind: line was already emitted for it, and is otherwise DROPPED.
        if canon_key in emitted_keys:
            continue

        if canon_key == "Id":
            out_bullets.append(f"- Id: {item.id}")
            emitted_keys.add("Id")
        elif canon_key == "Status":
            out_bullets.append(f"- Status: {item.status}")
            emitted_keys.add("Status")
            _insert_absent_gate_fields()
        elif canon_key == "Set":
            out_bullets.append(f"- Set: {item.set}")
            emitted_keys.add("Set")
        elif canon_key == "Priority":
            out_bullets.append(f"- Priority: {item.priority}")
            emitted_keys.add("Priority")
        elif canon_key == "Work-Kind":
            out_bullets.append(f"- Work-Kind: {item.kind}")
            emitted_keys.add("Work-Kind")
        elif canon_key == "Summary":
            out_bullets.append(f"- Summary: {item.summary}")
            emitted_keys.add("Summary")
        elif canon_key == "Gate-Kind":
            if item.status == "blocked":
                out_bullets.append(f"- Gate-Kind: {item.gate_kind}")
                emitted_keys.add("Gate-Kind")
        elif canon_key == "Gate-Ref":
            if item.status == "blocked":
                out_bullets.append(f"- Gate-Ref: {item.gate_ref}")
                emitted_keys.add("Gate-Ref")

    # Template-owned lines absent from the source are inserted directly after - Status:
    # (gate fields) or in template order at the end of the block (anything else).
    for key in ("Id", "Status", "Set", "Priority", "Work-Kind", "Summary"):
        if key not in emitted_keys:
            if key == "Id":
                out_bullets.append(f"- Id: {item.id}")
            elif key == "Status":
                out_bullets.append(f"- Status: {item.status}")
                _insert_absent_gate_fields()
            elif key == "Set":
                out_bullets.append(f"- Set: {item.set}")
            elif key == "Priority":
                out_bullets.append(f"- Priority: {item.priority}")
            elif key == "Work-Kind":
                out_bullets.append(f"- Work-Kind: {item.kind}")
            elif key == "Summary":
                out_bullets.append(f"- Summary: {item.summary}")
            emitted_keys.add(key)

    if item.status == "blocked":
        if "Gate-Kind" not in emitted_keys:
            out_bullets.append(f"- Gate-Kind: {item.gate_kind}")
            emitted_keys.add("Gate-Kind")
        if "Gate-Ref" not in emitted_keys:
            out_bullets.append(f"- Gate-Ref: {item.gate_ref}")
            emitted_keys.add("Gate-Ref")

    rendered_bullets = "\n".join(out_bullets)
    if header_prose.strip():
        if not header_prose.startswith("\n"):
            header_prose = "\n\n" + header_prose.lstrip()
        rendered_head = rendered_bullets + header_prose
    else:
        rendered_head = rendered_bullets + "\n"

    lines = [rendered_head.rstrip()]
    today = datetime.date.today().isoformat()
    msg = (message or "").strip() or item.summary
    lines.append("")
    lines.append("## Workflow history")
    lines.append(f"- {today} created (aw backlog): {msg}")
    lines.append("")
    lines.append(body.rstrip() + "\n" if body.strip() else "")
    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------------------
# Release exemption line writers and validation (IPD ghna7l E-04)
# --------------------------------------------------------------------------------------

_RELEASE_EXEMPT_KIND_LINE_RE = re.compile(
    r"(?m)^- Release-Exempt-Kind:[ \t]*[^\n]*$\n?"
)
_RELEASE_EXEMPT_REF_LINE_RE = re.compile(r"(?m)^- Release-Exempt-Ref:[ \t]*[^\n]*$\n?")


def set_release_exempt_kind_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Release-Exempt-Kind:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
    (falling back to after `- Id:`, or leaving unchanged)."""
    text = _RELEASE_EXEMPT_KIND_LINE_RE.sub("", text)
    if value in (None, "-"):
        return text
    new_line = f"- Release-Exempt-Kind: {value}\n"
    for anchor in (r"(?m)^- Status:[^\n]*\n", r"(?m)^- Id:[^\n]*\n"):
        m = re.search(anchor, text)
        if m:
            i = m.end()
            return text[:i] + new_line + text[i:]
    return text


def set_release_exempt_ref_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Release-Exempt-Ref:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
    (falling back to after `- Id:`, or leaving unchanged)."""
    text = _RELEASE_EXEMPT_REF_LINE_RE.sub("", text)
    if value in (None, "-"):
        return text
    new_line = f"- Release-Exempt-Ref: {value}\n"
    for anchor in (r"(?m)^- Status:[^\n]*\n", r"(?m)^- Id:[^\n]*\n"):
        m = re.search(anchor, text)
        if m:
            i = m.end()
            return text[:i] + new_line + text[i:]
    return text


_CLOSE_EVIDENCE_LINE_RE = re.compile(r"(?m)^- Close-Evidence:[ \t]*[^\n]*$\n?")


def set_close_evidence_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Close-Evidence:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
    (falling back to after `- Id:`, or leaving unchanged)."""
    text = _CLOSE_EVIDENCE_LINE_RE.sub("", text)
    if value in (None, "-"):
        return text
    new_line = f"- Close-Evidence: {value}\n"
    for anchor in (r"(?m)^- Status:[^\n]*\n", r"(?m)^- Id:[^\n]*\n"):
        m = re.search(anchor, text)
        if m:
            i = m.end()
            return text[:i] + new_line + text[i:]
    return text


def validate_release_exempt_flags(
    verb: str, kind: Optional[str], ref: Optional[str]
) -> Optional[str]:
    """Validate release exemption flags at the point of typing.

    Enforces that both flags are provided together, kind is in GATE_KINDS, and ref is valid
    for that kind under validate_gate_ref. '-' for kind clears both bullets.
    Returns an error message string if invalid, or None if valid.
    """
    if kind is None and ref is None:
        return None
    if kind == "-":
        if ref is not None and ref != "-":
            return (
                f"{verb}: cannot specify a ref when clearing release exemption with '-'"
            )
        return None
    if kind is None or ref is None or ref == "-":
        return f"{verb}: release exemption requires both --release-exempt-kind and --release-exempt-ref"
    if kind not in A.GATE_KINDS:
        return f"{verb}: --release-exempt-kind must be one of {sorted(A.GATE_KINDS)}"
    if not A.validate_gate_ref(kind, ref):
        return f"{verb}: --release-exempt-ref is invalid for kind {kind!r}: {ref!r}"
    return None


def run_new(args) -> int:
    from agent_workflows.project_context import resolve_verb_repo_root

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    status = getattr(args, "status", None) or "open"
    if status not in STATUSES:
        sys.stderr.write(
            f"aw backlog new: --status must be one of {sorted(STATUSES)}\n"
        )
        return 2
    item = BacklogItem()
    existing_ids = set()
    existing_items_data: List[Tuple[Path, BacklogItem, str]] = []
    for f in _iter_items(repo_root):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        parsed = parse_item(text)
        if parsed.id:
            existing_ids.add(parsed.id)
        existing_items_data.append((f, parsed, text))
    # IPD sk7ggr E-01: mint against the REPOSITORY-WIDE id6 set (terminal artifacts included), not
    # just this tree's ids. The backlog set is unioned in, so this is strictly stronger than before.
    item.id = core.mint_id6(repo_root, existing_ids)
    item.status = status
    # setidlen x75obw E-06 (catalog I-17): the ONE shared setid-length guard, called BEFORE the
    # default is applied, so a supplied `--set` is judged and the id6 default (always 6 chars) is not.
    from agent_workflows import config as _config

    _setid_arg = getattr(args, "set", None)
    _setid_err, _setid_warn = _config.validate_setid_length_for_authoring(
        repo_root, _setid_arg, verb="aw backlog new"
    )
    if _setid_err:
        sys.stderr.write(f"{_setid_err}\n")
        return 2
    if _setid_warn:
        sys.stderr.write(f"note: {_setid_warn}\n")
    item.set = _setid_arg or item.id  # singleton set defaults to the id
    # E-02 / OQ-01: `--work-kind` is the preferred CLI spelling and `--kind` is KEPT as an accepted
    # alias, so no existing script, habit, or agent instruction breaks. The preferred spelling wins
    # when both are supplied. Both parse into distinct dests so "was it passed?" stays answerable.
    #
    # planprio lkexaw (maintainer ruling 2026-09-24): Priority and Work-Kind are DECIDED WHERE THE
    # WORK IS FIRST RECORDED, which for backlog-originated work is here. There is deliberately NO
    # default any more: the old silent `medium`/`chore` fallback wrote a value nobody chose, and a
    # plan graduating from the item then inherited that unchosen value as if it were a decision.
    item.priority = getattr(args, "priority", None)
    item.kind = getattr(args, "work_kind", None) or getattr(args, "kind", None)
    _missing = [
        flag
        for flag, value in (("--priority", item.priority), ("--work-kind", item.kind))
        if not value
    ]
    if _missing:
        sys.stderr.write(
            f"aw backlog new: {' and '.join(_missing)} required: decide the item's priority "
            f"({' | '.join(sorted(PRIORITIES))}) and work kind ({' | '.join(sorted(KINDS))}) "
            "when you file it; a plan graduated from this item inherits both\n"
        )
        return 2
    item.summary = (getattr(args, "summary", None) or "").strip()
    item.gate_kind = getattr(args, "gate_kind", None)
    item.gate_ref = getattr(args, "gate_ref", None)
    if item.priority not in PRIORITIES:
        sys.stderr.write(
            f"aw backlog new: --priority must be one of {sorted(PRIORITIES)}\n"
        )
        return 2
    if item.kind not in KINDS:
        sys.stderr.write(
            f"aw backlog new: --work-kind must be one of {sorted(KINDS)}\n"
        )
        return 2
    if not (item.summary or "").strip():
        sys.stderr.write("aw backlog new: --summary is required\n")
        return 2

    raw_summary = getattr(args, "summary", None)
    _summary_val = (
        raw_summary
        if (raw_summary and ("\n" in raw_summary or "\r" in raw_summary))
        else item.summary
    )
    _summary_err = _refuse_unsafe_descriptive(
        "aw backlog new", "--summary", _summary_val
    )
    if _summary_err:
        sys.stderr.write(f"{_summary_err}\n")
        return 2

    raw_gate_ref = getattr(args, "gate_ref", None)
    if raw_gate_ref is not None:
        _gr_err = _refuse_unsafe_descriptive(
            "aw backlog new", "--gate-ref", raw_gate_ref, bound_length=True
        )
        if _gr_err:
            sys.stderr.write(f"{_gr_err}\n")
            return 2

    if status == "blocked" and (not item.gate_kind or not item.gate_ref):
        sys.stderr.write(
            "aw backlog new: a blocked item requires --gate-kind and --gate-ref\n"
        )
        return 2

    rel_exempt_kind = getattr(args, "release_exempt_kind", None)
    rel_exempt_ref = getattr(args, "release_exempt_ref", None)
    _exempt_err = validate_release_exempt_flags(
        "aw backlog new", rel_exempt_kind, rel_exempt_ref
    )
    if _exempt_err:
        sys.stderr.write(f"{_exempt_err}\n")
        return 2

    is_exempt = bool(rel_exempt_kind and rel_exempt_kind != "-")
    if rel_exempt_kind and rel_exempt_kind != "-":
        item.release_exempt_kind = rel_exempt_kind
    if rel_exempt_ref and rel_exempt_ref != "-":
        item.release_exempt_ref = rel_exempt_ref

    br = getattr(args, "blocks_release", None)
    if br is not None and br != "-":
        from agent_workflows import releases as _releases

        if _releases.resolve_release(repo_root, br) is None:
            sys.stderr.write(
                f"aw backlog new: --blocks-release {br!r} does not resolve to a release record\n"
            )
            return 2
        item.blocks_release = br

    # nobugship di08i9 E-01: DEFAULT THE RELEASE GATE ON A BUG, through the ONE shared predicate so
    # creation and reclassification (E-02) cannot diverge. See `decide_gate_default` for the three
    # measured conditions (fall back rather than refuse, skip `done`/`parked`, keep the `-` escape).
    gate_default, gate_default_notice = decide_gate_default(
        repo_root,
        kind=item.kind,
        status=status,
        explicit_blocks_release=br,
        is_exempt=is_exempt,
    )
    if gate_default is not None:
        br = gate_default
        item.blocks_release = gate_default

    message = getattr(args, "message", None)
    if message is not None:
        _msg_err = _refuse_unsafe_descriptive(
            "aw backlog new", "--message", message, bound_length=False
        )
        if _msg_err:
            sys.stderr.write(f"{_msg_err}\n")
            return 2

    today = datetime.date.today().strftime("%Y%m%d")
    slug = (
        core.kebab(getattr(args, "slug", None) or item.summary or "item")[:50] or "item"
    )
    filename = f"{today}-{item.set}-01-{item.id}-{slug}.backlog.md"
    dest = (
        _resolve_backlog_root(repo_root)
        / _rp.target_subdir("backlog", status)
        / filename
    )
    body = getattr(args, "body", None) or ""
    rendered = _render_item(item, body, message=message)
    if br is not None:
        from agent_workflows import releases as _releases

        rendered = _releases.set_blocks_release_line(rendered, br)

    if rel_exempt_kind is not None or rel_exempt_ref is not None:
        if rel_exempt_kind == "-":
            rendered = set_release_exempt_kind_line(rendered, "-")
            rendered = set_release_exempt_ref_line(rendered, "-")
        else:
            if rel_exempt_ref is not None:
                rendered = set_release_exempt_ref_line(rendered, rel_exempt_ref)
            if rel_exempt_kind is not None:
                rendered = set_release_exempt_kind_line(rendered, rel_exempt_kind)

    # IPD fwgq2u E-02 / OQ-01: near-duplicate advisory guard. Reuses the existing_items_data walk
    # performed above rather than doing a second corpus pass (which would be 59t9x5 double-read in
    # miniature). Advisory-only: never refuses.
    candidates = find_duplicate_candidates_in_items(
        existing_items_data,
        summary=item.summary,
        body=body,
    )

    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        Evidence,
        select_output,
    )

    # nobugship di08i9 E-01 / OQ-01: ANNOUNCE THE DEFAULT ON BOTH OUTPUT SURFACES. A field the tool
    # wrote but the author did not type is exactly the hidden behavior that makes a later reader
    # distrust the record, and the maintainer's 2026-09-10 ruling on `y4adch` OQ-01 requires a VISIBLE
    # notice naming the field, the value applied, and why. The human `sys.stdout.write` alone does not
    # satisfy that here: the `--agent`/`--json` branches below RETURN before it, and a runner is the
    # most likely caller of this verb.
    #
    # THE CARRIER IS `data` PLUS AN `Evidence` RECEIPT, NOT AN `info` DIAGNOSTIC, and the choice is
    # deliberate. `CommandResult.to_agent_record` derives `findings` from `len(self.diagnostics)` and
    # `has_findings` returns True for any diagnostic regardless of severity, so an `info` diagnostic
    # would emit `findings: 1` on a successful create and teach every consumer that a normal filing
    # had something wrong with it. `data` carries the machine-readable fact into the full `--json`
    # representation, and `Evidence` is what survives into the COMPACT `--agent` JSONL record (where
    # `data` is not emitted), so between them the fact reaches both structured surfaces without
    # inflating a findings count.
    def _gate_notice_fields() -> tuple:
        if gate_default_notice is None:
            return {}, []
        gate_data = {
            "blocks_release": item.blocks_release,
            "blocks_release_defaulted": item.blocks_release is not None,
            "blocks_release_default_notice": gate_default_notice,
        }
        return gate_data, [
            Evidence(
                key="blocks-release-default",
                value=item.blocks_release or "none",
                status="verified",
                detail=gate_default_notice,
            )
        ]

    gate_data, gate_evidence = _gate_notice_fields()

    def _duplicate_notice_fields() -> tuple:
        cand_list = [
            {
                "id": c.id,
                "status": c.status,
                "summary": c.summary,
                "path": c.path,
                "shared_tokens": sorted(c.shared_tokens),
                "reason": c.reason,
            }
            for c in candidates
        ]
        limits_data = [
            {"case": case, "verdict": verdict, "why": why}
            for case, verdict, why in BACKLOG_DUPLICATE_GUARD_LIMITS
        ]
        dup_data = {
            "duplicate_candidates": cand_list,
            "duplicate_candidate_count": len(candidates),
            "duplicate_guard_advisory": True,
            "duplicate_guard_limits": limits_data,
            "duplicate_guard_coverage": BACKLOG_DUPLICATE_GUARD_COVERAGE,
        }
        dup_evidence = [
            Evidence(
                key="duplicate-candidates",
                value=len(candidates),
                status="verified",
                detail=f"{len(candidates)} candidate duplicate(s) detected",
            ),
            Evidence(
                key="duplicate-guard-coverage",
                value=BACKLOG_DUPLICATE_GUARD_COVERAGE,
                status="verified",
            ),
        ] + [
            Evidence(
                key=f"limit:{case}",
                value=verdict,
                status="verified",
                detail=why,
            )
            for case, verdict, why in BACKLOG_DUPLICATE_GUARD_LIMITS
        ]
        return dup_data, dup_evidence

    dup_data, dup_evidence = _duplicate_notice_fields()

    def _render_duplicate_advisory() -> str:
        lines = []
        if candidates:
            lines.append(
                "aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):"
            )
            for c in candidates:
                lines.append(f"  - {c.id} [{c.status}]: {c.summary}")
            lines.append(
                "  ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing."
            )
            lines.append("  What it can and cannot tell you:")
            for case, verdict, why in BACKLOG_DUPLICATE_GUARD_LIMITS:
                lines.append(f"    - {case}: {verdict} - {why}")
            lines.append(f"  {BACKLOG_DUPLICATE_GUARD_COVERAGE}")
        else:
            lines.append("aw backlog new: no duplicate candidates detected.")
            lines.append(
                "  ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new."
            )
            lines.append("  What it can and cannot tell you:")
            for case, verdict, why in BACKLOG_DUPLICATE_GUARD_LIMITS:
                lines.append(f"    - {case}: {verdict} - {why}")
            lines.append(f"  {BACKLOG_DUPLICATE_GUARD_COVERAGE}")
        return "\n".join(lines) + "\n"

    ctx = select_output(args)
    if not getattr(args, "apply", False):
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="backlog new",
                status="clean",
                exit_code=0,
                summary=f"would write {dest}",
                changes=[Change(path=str(dest), kind="create", applied=False)],
                data={"path": str(dest), "id": item.id, **gate_data, **dup_data},
                evidence=gate_evidence + dup_evidence,
                verified=True,
                complete=True,
            )
            return get_renderer(ctx).emit(res, ctx)
        if gate_default_notice:
            sys.stdout.write(f"aw backlog new: {gate_default_notice}\n")
        sys.stdout.write(_render_duplicate_advisory())
        sys.stdout.write(f"--- would write {dest} ---\n{rendered}")
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    core.atomic_write(dest, rendered)

    # plan `vhbvwz` E-04: REPORT a failed sidecar write instead of swallowing it in a bare
    # `except Exception: pass`. The inline `## Workflow history` record is already in `rendered` and
    # was written by the `atomic_write` directly above, so it is unaffected either way; the sidecar is
    # a machine-local activity log (OQ-01) and must never gate a durable write.
    if item.id:
        from agent_workflows import record_history as _rh

        _rh.append_advisory(
            repo_root,
            id6=item.id,
            tree="backlog",
            workflow="aw backlog new",
            actor="aw backlog",
            message=((message or "").strip() or item.summary).strip(),
            artifact=dest.name,
        )

    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="backlog new",
            status="clean",
            exit_code=0,
            summary=f"wrote {dest}",
            changes=[Change(path=str(dest), kind="create", applied=True)],
            data={"path": str(dest), "id": item.id, **gate_data, **dup_data},
            evidence=gate_evidence + dup_evidence,
            verified=True,
            complete=True,
        )
        return get_renderer(ctx).emit(res, ctx)

    if gate_default_notice:
        sys.stdout.write(f"aw backlog new: {gate_default_notice}\n")
    sys.stdout.write(_render_duplicate_advisory())
    sys.stdout.write(f"aw backlog new: wrote {dest}\n")
    return 0


def run_set(args) -> int:
    from agent_workflows.project_context import (
        is_project_dir,
        resolve_verb_repo_root,
    )

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    gate_dir_arg = getattr(args, "gate_dir", None)
    if gate_dir_arg is not None:
        gate_root = resolve_verb_repo_root(gate_dir_arg)
        if not is_project_dir(gate_root):
            sys.stderr.write(
                f"aw backlog set: --gate-dir '{gate_dir_arg}' is not an agent-workflows project root\n"
            )
            return 2
    else:
        gate_root = repo_root

    lane_carrier_ref = getattr(args, "lane_carrier_ref", None)
    lane_carrier_path = getattr(args, "lane_carrier_path", None)
    if lane_carrier_ref is not None and lane_carrier_path is None:
        sys.stderr.write(
            "aw backlog set: --lane-carrier-ref requires --lane-carrier-path\n"
        )
        return 2
    if lane_carrier_path is not None and lane_carrier_ref is None:
        sys.stderr.write(
            "aw backlog set: --lane-carrier-path requires --lane-carrier-ref\n"
        )
        return 2

    target = getattr(args, "path", None)
    new_status = getattr(args, "status", None)
    if not target or new_status not in STATUSES:
        sys.stderr.write(
            f"aw backlog set: --status must be one of {sorted(STATUSES)} and a path is required\n"
        )
        return 2
    # bklgkind b5sfwm E-03: validate the two CLASSIFICATION flags BEFORE resolving or writing
    # anything. Argparse `choices` already covers the CLI route, but this function is called directly
    # by tests and by other code, and the shared line writers deliberately do NOT enforce the enum
    # ("the ENUM check ... is enforced by `aw check` / validate_spec, not here"). Refusing here with
    # the same exit-2 shape `run_new` uses keeps a direct caller from producing an item that
    # `validate_item` rejects. NOTE `-` IS NOT ACCEPTED (OQ-02): both fields are REQUIRED on a backlog
    # item, so clearing one manufactures a `backlog.kind-invalid`/`backlog.priority-invalid` item.
    set_work_kind = getattr(args, "work_kind", None)
    set_priority = getattr(args, "priority", None)
    if set_work_kind is not None and set_work_kind not in KINDS:
        sys.stderr.write(
            f"aw backlog set: --work-kind must be one of {sorted(KINDS)}\n"
        )
        return 2
    if set_priority is not None and set_priority not in PRIORITIES:
        sys.stderr.write(
            f"aw backlog set: --priority must be one of {sorted(PRIORITIES)}\n"
        )
        return 2
    set_rel_exempt_kind = getattr(args, "release_exempt_kind", None)
    set_rel_exempt_ref = getattr(args, "release_exempt_ref", None)
    _exempt_err = validate_release_exempt_flags(
        "aw backlog set", set_rel_exempt_kind, set_rel_exempt_ref
    )
    if _exempt_err:
        sys.stderr.write(f"{_exempt_err}\n")
        return 2
    # setidhard bwgyum E-04: validate the FORWARD graduation link's value HERE, before anything is
    # resolved or written, in the same exit-2 shape the two flags above use. A setter that accepts a
    # typo writes a link `aw check` then reports as malformed, turning one clear refusal into a
    # confusing finding. The shape authority is the shared `plans.is_set_id_valid` (reached through
    # `releases.canonicalize_graduated_to`), never a second setid pattern. `-` clears, matching every
    # sibling link primitive.
    from agent_workflows import releases as _releases_gt_flag

    set_graduated_to, _gt_err = _releases_gt_flag.canonicalize_graduated_to(
        getattr(args, "graduated_to", None)
    )
    if _gt_err:
        sys.stderr.write(f"aw backlog set: {_gt_err}\n")
        return 2

    set_message = getattr(args, "message", None)
    if set_message is not None:
        _msg_err = _refuse_unsafe_descriptive(
            "aw backlog set", "--message", set_message, bound_length=False
        )
        if _msg_err:
            sys.stderr.write(f"{_msg_err}\n")
            return 2

    set_gate_ref = getattr(args, "gate_ref", None)
    if set_gate_ref is not None:
        _gr_err = _refuse_unsafe_descriptive(
            "aw backlog set", "--gate-ref", set_gate_ref, bound_length=True
        )
        if _gr_err:
            sys.stderr.write(f"{_gr_err}\n")
            return 2

    # IPD laykok E-03: close the path-only outlier - resolve via the ONE unified resolver so
    # `aw backlog set` now accepts an id6/setid/status/stem/substring, not just a literal path.
    from agent_workflows import selectors as _sel

    res = _sel.resolve(repo_root, "backlog", target)
    if res.rejected_kind is not None:
        sys.stderr.write(
            f"aw backlog set: this verb does not accept a {res.rejected_kind} selector: {target}\n"
        )
        return 2
    if not res.paths:
        sys.stderr.write(f"aw backlog set: no such item: {target}\n")
        return 2
    if len(res.paths) > 1:
        # Kind-aware ambiguity (E-07): a setid legitimately selects the whole Set; a unique-id
        # collision or a substring multi-match refuses with the candidate list unless --force.
        if res.kind == _sel.MATCH_SETID or (
            res.kind == _sel.MATCH_SUBSTRING and getattr(args, "force", False)
        ):
            pass  # act on all matches
        else:
            cand = "\n  ".join(str(p) for p in res.paths)
            overridable = (
                " (pass --force to act on all)"
                if res.kind == _sel.MATCH_SUBSTRING
                else ""
            )
            sys.stderr.write(
                f"aw backlog set: selector '{target}' is ambiguous ({res.kind}); "
                f"candidates{overridable}:\n  {cand}\n"
            )
            return 2
    # backlog set operates on a single item; when a setid/forced-substring yields many, act on the
    # first deterministically (backlog items are not grouped like plans, so multi is rare).
    src = res.paths[0]
    text = src.read_text(encoding="utf-8")
    item = parse_item(text)
    item.status = new_status
    if new_status == "blocked":
        gk = getattr(args, "gate_kind", None)
        gr = getattr(args, "gate_ref", None)
        if not gk or not gr:
            sys.stderr.write(
                "aw backlog set: moving to blocked requires --gate-kind and --gate-ref\n"
            )
            return 2
        item.gate_kind, item.gate_ref = gk, gr
    else:
        item.gate_kind = item.gate_ref = None

    # Rewrite metadata bullets in place; move file to the new status dir; append history.
    body = _strip_metadata_and_history(text)
    rendered = _render_item(item, body, source_text=text)
    # append a transition history record (in addition to the created line _render_item emits,
    # preserve prior history by re-emitting it):
    prior_status = parse_item(text).status
    label = new_status if prior_status != new_status else "same-status"
    rendered = _reattach_history(
        text,
        rendered,
        f"{new_status}",
        getattr(args, "message", "") or "",
        label=label,
    )

    # awrelease Order 02 / rendrop 2yqt0a E-02: set/clear the Blocks-Release gate field when requested
    # (a release id6, 'next', or '-' to clear). Absent the flag, an existing value is preserved in
    # place by _render_item.
    br = getattr(args, "blocks_release", None)
    if br is not None:
        from agent_workflows import releases as _releases

        rendered = _releases.set_blocks_release_line(rendered, br)

    # setidhard bwgyum / rendrop 2yqt0a E-02: apply explicit --graduated-to when given. Absent the
    # flag, an existing value is preserved in place by _render_item.
    if set_graduated_to is not None:
        from agent_workflows import releases as _releases_gt

        rendered = _releases_gt.set_graduated_to_line(rendered, set_graduated_to)

    if set_rel_exempt_kind is not None or set_rel_exempt_ref is not None:
        if set_rel_exempt_kind == "-":
            rendered = set_release_exempt_kind_line(rendered, "-")
            rendered = set_release_exempt_ref_line(rendered, "-")
        else:
            if set_rel_exempt_ref is not None:
                rendered = set_release_exempt_ref_line(rendered, set_rel_exempt_ref)
            if set_rel_exempt_kind is not None:
                rendered = set_release_exempt_kind_line(rendered, set_rel_exempt_kind)

    # bklgkind b5sfwm E-03/E-04: apply the two CLASSIFICATION fields. APPLIED AFTER THE RENDER,
    # THROUGH THE SHARED LINE WRITERS, exactly as `--blocks-release` above is, so `_render_item` stays
    # untouched and BOTH spellings of this verb funnel through ONE write mechanism: the positional
    # spelling reaches the same `releases.set_work_kind_line` / `set_priority_line` primitives via
    # `status_set.apply_status_change`. Writing to the parsed item before the render would fork the
    # mechanism and make the two spellings' output impossible to compare byte for byte.
    #
    # These writes are HOISTED OUT OF EVERY STATUS BRANCH and keyed only on flag presence, which IS
    # the "persists on a no-op transition" mechanism: a pure reclassification restates the item's
    # current status, changes no directory, and still rewrites the metadata line. The values were
    # validated at the top of this function, because these writers deliberately do not.
    #
    # THE ORDER OF THESE TWO WRITES IS DELIBERATE AND MATCHES `apply_status_change` (Priority first,
    # then Work-Kind). Both writers INSERT directly after `- Status:`, so whichever runs LAST ends up
    # the higher line; writing them in the other order would leave the two spellings of this one verb
    # emitting the same fields in a different order, which V-03 compares.
    if set_work_kind is not None or set_priority is not None:
        from agent_workflows import releases as _releases

        if set_priority is not None:
            rendered = _releases.set_priority_line(rendered, set_priority)
        if set_work_kind is not None:
            rendered = _releases.set_work_kind_line(rendered, set_work_kind)

    # nobugship di08i9 E-02 / gatefollows vsgd48 E-01: DEFAULT THE GATE ON RECLASSIFICATION AND ON
    # STATUS TRANSITIONS INTO A LIVE STATUS. The gate follows a work kind becoming `bug` AND follows
    # an ungated `bug` item transitioning into a live status (open, graduated, blocked). This is the
    # `--status` spelling of `aw backlog set`; the POSITIONAL spelling routes through
    # `status_set.apply_status_change`, which carries the SAME broadened call to the SAME shared predicate.
    # Both are required: `aw backlog set` forks on whether `--status` was passed, so a default wired into
    # one path would fire for one spelling and not the other.
    #
    # DOWNSTREAM WORKFLOW CONSEQUENCE (DISCLOSED, OQ-02): Gating an item at `graduated` changes what
    # a LATER close does. An ungated bug taken open -> graduated -> done closed silently before;
    # with the gate present at `graduated`, a later `set done` REFUSES with rc=1 under the shipped
    # close-legitimacy gate (evaluate_blocking_close below), demanding a handoff (--from-backlog),
    # evidence (--evidence), or an explicit de-gate (--blocks-release -). That refusal is intended
    # policy (AGENTS.md release-gates rule), but makes a previously-silent close interactive.
    #
    # DO NOT REMOVE A GATE WHEN A WORK KIND CHANGES AWAY FROM `bug`: a gate may have been set
    # deliberately for another reason, and silently clearing it would lose a decision. Hence the
    # predicate is consulted only for the kind the item is BECOMING, it never clears, and it declines
    # when the item already carries a gate (`existing_blocks_release`). Do not alter `decide_gate_default`
    # itself: its condition 3 already declines `done` and `parked`, so the broadened guard needs no
    # status allowlist of its own.
    if br is None:
        _rendered_item = parse_item(rendered)
        _is_exempt = bool(
            _rendered_item.release_exempt_kind
            and _rendered_item.release_exempt_ref
            and _rendered_item.release_exempt_kind != "-"
            and _rendered_item.release_exempt_ref != "-"
        )
        gate_default, gate_default_notice = decide_gate_default(
            repo_root,
            kind=set_work_kind or item.kind,
            status=new_status,
            explicit_blocks_release=None,
            existing_blocks_release=item.blocks_release,
            is_exempt=_is_exempt,
        )
        if gate_default is not None:
            from agent_workflows import releases as _releases

            rendered = _releases.set_blocks_release_line(rendered, gate_default)
        if gate_default_notice:
            sys.stdout.write(f"aw backlog set: {gate_default_notice}\n")

    # bklggrad orb9zb E-04 / gatedir 9vglxd E-04: release-gate close-legitimacy gate. `rendered` now
    # reflects the POST-mutation item (including any same-call `--blocks-release -` de-gate), so a
    # `done` + `--blocks-release -` in ONE call is honored via the DE-GATED path. The predicate is
    # the SINGLE shared authority (check_engine.evaluate_blocking_close) evaluated against `gate_root`
    # (defaulting to `repo_root`, but split when explicit `--gate-dir` is passed).
    # On an illegitimate blocking close we REFUSE and write nothing; blocking `-> parked` and
    # priority-demote-of-a-blocker WARN but proceed.
    from agent_workflows import check_engine as _ce

    verdict = _ce.evaluate_blocking_close(
        gate_root,
        src,
        new_status,
        evidence=getattr(args, "evidence", None),
        item_text=rendered,
        prior_priority=parse_item(text).priority,
        lane_carrier_ref=lane_carrier_ref,
        lane_carrier_path=lane_carrier_path,
    )
    if not verdict.legitimate and verdict.severity == "error":
        sys.stderr.write(f"aw backlog set: refused: {verdict.reason}.\n")
        for fix in verdict.fixes:
            sys.stderr.write(f"  - {fix}\n")
        return 1
    if verdict.severity == "warn":
        sys.stderr.write(f"aw backlog set: warning: {verdict.reason}.\n")

    # gateatrest f7igdu E-03: write the cited evidence durably on an evidence-satisfied close.
    # Keyed on verdict.path == "SATISFIED", never on args.evidence presence alone.
    if verdict.legitimate and verdict.path == "SATISFIED":
        accepted_evidence = (
            getattr(args, "evidence", None) or parse_item(rendered).close_evidence
        )
        if accepted_evidence:
            rendered = set_close_evidence_line(rendered, accepted_evidence)

    dest_dir = _resolve_backlog_root(repo_root) / _rp.target_subdir(
        "backlog", new_status
    )
    dest = dest_dir / src.name
    if getattr(args, "dry_run", False) or not getattr(args, "apply", True):
        sys.stdout.write(f"--- would move {src} -> {dest} (status {new_status}) ---\n")
        return 0
    # Append this transition to the GLOBAL sidecar as well (awhistory Order 02). The inline block now
    # keeps the FULL history (plan `vhbvwz` E-08 stopped slimming it), so this is an additional
    # machine-local activity-log entry rather than the only durable copy.
    #
    # plan `vhbvwz` E-04: a failure here is REPORTED, never swallowed, and it can never affect the
    # inline record, which `_reattach_history` has already assembled into `rendered` above and which is
    # written by the `atomic_write` below regardless of what this call returns.
    if item.id:
        from agent_workflows import record_history as _rh

        _rh.append_advisory(
            repo_root,
            id6=item.id,
            tree="backlog",
            workflow="aw backlog set",
            actor="aw backlog",
            message=(getattr(args, "message", "") or f"status -> {new_status}").strip(),
            artifact=src.name,
        )
    dest_dir.mkdir(parents=True, exist_ok=True)
    core.atomic_write(dest, rendered)
    if dest.resolve() != src.resolve():
        src.unlink()
    sys.stdout.write(f"aw backlog set: {src.name} -> {new_status}\n")
    return 0


def run_note(args) -> int:
    """`aw backlog note <selector> --message ...`: append a history record, changing NO status.

    plan `vhbvwz` E-05. The backlog verb set was `new`, `set`, `check` only, so ANNOTATING an item
    required a status-setting call - which is how BOTH defects this plan fixes were hit in the first
    place (a same-status `aw backlog set` used to discard the message outright, and it slimmed the
    item's history while doing it). `aw specs note` already existed and is the precedent copied here:
    same flag shape, same history-record behavior, no status change, no file move.

    DELIBERATELY NOT ROUTED THROUGH `run_set`. A note is not a transition: it must not consult the
    status vocabulary, must not touch the gate fields, must not re-render the metadata block, and must
    not invoke the release-gate close predicate. Writing the history record directly is both smaller
    and impossible to confuse with a transition, and it is exactly what `specs.run_note` does.
    """

    from agent_workflows.project_context import resolve_verb_repo_root

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    target = getattr(args, "path", None) or getattr(args, "selector", None)
    raw_message = getattr(args, "message", None)
    message = (raw_message or "").strip()
    if not target:
        sys.stderr.write(
            "aw backlog note: a selector (id6, filename, or path) is required\n"
        )
        return 2
    if not message:
        sys.stderr.write(
            "aw backlog note: --message is required (the note to record)\n"
        )
        return 2

    _msg_val = (
        raw_message
        if (raw_message and ("\n" in raw_message or "\r" in raw_message))
        else message
    )
    _msg_err = _refuse_unsafe_descriptive(
        "aw backlog note", "--message", _msg_val, bound_length=False
    )
    if _msg_err:
        sys.stderr.write(f"{_msg_err}\n")
        return 2

    # The ONE unified resolver, exactly as `run_set` uses: an id6, a filename, a stem, or a path.
    from agent_workflows import selectors as _sel

    res = _sel.resolve(repo_root, "backlog", target)
    if res.rejected_kind is not None:
        sys.stderr.write(
            f"aw backlog note: this verb does not accept a {res.rejected_kind} selector: {target}\n"
        )
        return 2
    if not res.paths:
        sys.stderr.write(f"aw backlog note: no such item: {target}\n")
        return 2
    if len(res.paths) > 1:
        cand = "\n  ".join(str(p) for p in res.paths)
        sys.stderr.write(
            f"aw backlog note: selector '{target}' is ambiguous ({res.kind}); candidates:\n  {cand}\n"
        )
        return 2

    src = res.paths[0]
    text = src.read_text(encoding="utf-8")
    item = parse_item(text)
    date = getattr(args, "date", None) or datetime.date.today().isoformat()
    record = f"- {date} note (aw backlog): {message}"

    # The sidecar remains a machine-local activity log and can never gate this write (E-04).
    if item.id:
        from agent_workflows import record_history as _rh

        _rh.append_advisory(
            repo_root,
            id6=item.id,
            tree="backlog",
            workflow="aw backlog note",
            actor="aw backlog",
            message=f"note: {message}",
            artifact=src.name,
        )

    # PREPEND under the existing heading (newest-first, matching every other writer). No status is
    # read or written, and the file is NOT moved, so the item's directory keeps agreeing with it.
    lines = text.split("\n")
    out: List[str] = []
    inserted = False
    for line in lines:
        out.append(line)
        if not inserted and line.strip() == "## Workflow history":
            out.append(record)
            inserted = True
    if not inserted:
        if out and out[-1].strip() != "":
            out.append("")
        out.append("## Workflow history")
        out.append(record)
    core.atomic_write(src, "\n".join(out).rstrip() + "\n")
    sys.stdout.write(f"aw backlog note: appended a history record to {src}\n")
    return 0


def _strip_metadata_and_history(text: str) -> str:
    """Return only the free prose body (after the `## Workflow history` section)."""

    parts = text.split("\n## Workflow history", 1)
    if len(parts) < 2:
        return ""
    after = parts[1]
    # body is whatever follows the history block (the next paragraph after the history bullets)
    out_lines: List[str] = []
    in_hist = True
    for line in after.split("\n")[1:]:
        if in_hist and (line.startswith("- ") or not line.strip()):
            continue
        in_hist = False
        out_lines.append(line)
    return "\n".join(out_lines).strip()


def _prior_history_records(text: str) -> List[str]:
    """The item's EXISTING inline history records, in file order (newest-first), or `[]`.

    BOUNDED EXACTLY AS `_strip_metadata_and_history` BOUNDS IT, and that is the whole subtlety. The
    history block ends at the first line that is neither blank nor a top-level `- ` bullet; everything
    after it is the PROSE BODY. Matching that same boundary is what keeps the two functions from
    disagreeing about which lines are records, because they partition the same file between them.

    THE BUG THIS SHAPE PREVENTS, measured on a real legacy item (`tk1gqo`) while implementing
    `vhbvwz` E-08. An earlier version scanned the whole post-heading region for `HISTORY_RECORD_RE`
    against `line.strip()`, so five INDENTED, PROSE-QUOTED example lines deep inside that item's body
    (it is a bug report whose text quotes history lines verbatim) matched as records and were
    re-emitted into the history block: 11 records became 17, and quoted examples were promoted into
    the item's own provenance. Hence two rules here: the block is BOUNDED as above, and a record must
    start at column zero (`ln.startswith("- ")`) so an indented quotation is never mistaken for one.
    """

    if "\n## Workflow history" not in text:
        return []
    after = text.split("\n## Workflow history", 1)[1]
    out: List[str] = []
    for ln in after.split("\n")[1:]:
        if not ln.strip():
            continue
        if not ln.startswith("- "):
            break  # the prose body begins here; everything beyond is not history
        if A.HISTORY_RECORD_RE.match(ln.strip()):
            out.append(ln.rstrip())
    return out


def _reattach_history(
    old_text: str,
    rendered: str,
    new_status: str,
    message: str,
    label: str = "set",
) -> str:
    """Prepend one transition record to the inline `## Workflow history`, PRESERVING prior records.

    NEWEST-FIRST, and prior records are KEPT (plan `vhbvwz` E-08). This function used to emit ONLY the
    new record, discarding every earlier one, per awhistory Order 02 / spec `20260818-1525-02` OQ-2,
    whose stated premise was that "the full chronological log lives in the global
    .aw/records/history.jsonl sidecar". That premise is false: `.aw/.gitignore` ignores the sidecar, so
    the slimmed records did not survive a clone and the item's provenance was destroyed for every
    reader but this machine. The maintainer ruled on 2026-09-10 (plan `vhbvwz` OQ-01) that inline
    history is the DURABLE home for backlog items and specs, matching plans; spec `20260818-1525-02`
    is amended in the same change.

    THE PRIOR RECORDS COME FROM `old_text`, NOT FROM `rendered`, AND THAT IS NOT INTERCHANGEABLE.
    `_strip_metadata_and_history` deliberately discards the history block, and `_render_item` then
    MINTS A FRESH `created` record stamped with TODAY's date, so `rendered`'s history section holds a
    synthetic line rather than the item's real past. Reading prior records from `rendered` therefore
    preserved a re-dated forgery of the oldest record and lost every other one (measured while
    implementing E-08: an item whose records were 2026-01-01 and 2026-01-02 came back with a single
    `created` line dated today). `old_text` is the file as it was on disk, so it is the only honest
    source. The re-minted `created` line is dropped for the same reason.

    THE LABEL PARAMETER (plan `jbipfa`, backlog `awqzuh`) allows the caller to specify the transition
    token (e.g. "graduated", "done", or "same-status"), aligning with `status_set.apply_status_change`
    which names the transition rather than writing an uninformative "set". The default "set" preserves
    the legacy record token for an unaware caller.

    THE SIDECAR IS STILL WRITTEN by the caller; it is a machine-local activity log, not the durable
    store, so it can never gate this write (see `record_history.append_advisory`).
    """

    today = datetime.date.today().isoformat()
    msg = message.strip() or f"status -> {new_status}"
    new_record = f"- {today} {label} (aw backlog): {msg}"
    # rebuild: metadata block from `rendered` up to its history header, then the NEW record followed by
    # every prior record from the FILE AS IT WAS (newest-first, matching status_set's plan writer),
    # then the prose body.
    head = rendered.split("\n## Workflow history", 1)[0]
    body = ""
    if "\n## Workflow history" in rendered:
        tail = rendered.split("\n## Workflow history", 1)[1]
        body_parts = tail.split("\n\n", 1)
        body = body_parts[1] if len(body_parts) > 1 else ""
    prior = _prior_history_records(old_text)
    hist_block = "\n".join([new_record] + prior)
    result = head + "\n## Workflow history\n" + hist_block
    if body.strip():
        result += "\n\n" + body.rstrip()
    return result.rstrip() + "\n"


def run_check(args) -> int:
    from agent_workflows.project_context import resolve_verb_repo_root
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        Evidence,
        select_output,
    )

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    drift: List[core.Drift] = []
    seen_ids: Dict[str, str] = {}
    items_count = 0
    for f in _iter_items(repo_root):
        items_count += 1
        text = f.read_text(encoding="utf-8")
        item_drift = validate_item(f, text)
        drift.extend(item_drift)
        pid = parse_item(text).id
        if pid and core.is_valid_id6(pid):
            loc = drift_location(f)
            if pid in seen_ids:
                drift.append(
                    core.Drift(
                        loc,
                        "backlog.id-duplicate",
                        f"id {pid} also in {seen_ids[pid]}",
                    )
                )
            else:
                seen_ids[pid] = loc

    ctx = select_output(args)
    if ctx.is_agent or ctx.is_json:
        exit_code = core.drift_exit_code(drift)
        status = "clean" if exit_code == 0 else "findings"
        summary = (
            f"{items_count} backlog items checked"
            if exit_code == 0
            else f"{len(drift)} finding(s) detected across {items_count} backlog items"
        )
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
                key="backlog",
                value={"checked": items_count, "violations": len(drift)},
                status=status,
            )
        ]
        res = CommandResult(
            command="backlog check",
            status=status,
            exit_code=exit_code,
            summary=summary,
            diagnostics=diagnostics,
            evidence=evidence,
            data={"checked": items_count, "violations": len(drift)},
        )
        return get_renderer(ctx).emit(res, ctx)

    # awcolor Order 01: color the HUMAN branch only (agent branch byte-for-byte unchanged).
    from agent_workflows import term as _term

    t = _term.Term(
        stream=sys.stdout, color=False if getattr(args, "no_color", False) else None
    )
    colored = getattr(t, "color", False)
    if drift:
        for d in drift:
            rule = t.color256(d.rule, 196, bold=True) if colored else d.rule
            sys.stdout.write(f"{d.location}: {rule}: {d.detail}\n")
        sys.stdout.write(f"aw backlog check: {len(drift)} violation(s).\n")
    else:
        msg = "aw backlog check: all backlog items conform."
        sys.stdout.write((t.color256(msg, 46, bold=True) if colored else msg) + "\n")
    return core.drift_exit_code(drift)

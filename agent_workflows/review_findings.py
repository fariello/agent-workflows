"""Typed, machine-readable plan-review findings (IPD revgate Order 01 / 15zvu6).

THE PROBLEM THIS SOLVES. A `/plan-review` classifies every finding with a Severity
(`BLOCKER|HIGH|MEDIUM|LOW`) and a Decision (`FIXED|DEFERRED|OPEN|REPLAN`), but those classifications
have historically survived only as PROSE: one summary line appended to the reviewed plan's
`## Workflow history`, plus the session transcript. Nothing deterministic could read them, which is
measurable: `BLOCKER`, `HIGH`, `Severity`, and `Remediation Risk` each appear ZERO times in
``ipd_lint.py`` and ``check_engine.py``. A `HIGH` finding left `OPEN` was therefore invisible to
every gate, check, and report in the repo.

This module is the DATA LAYER that fixes that, and NOTHING MORE. It defines the on-disk format, and
it parses and writes it. It deliberately gates nothing and blocks nothing: enforcement is the Order
02 sibling (`plqjt7`), the dependency cascade is Order 03 (`7nkcgp`), and making reviewers actually
EMIT the `## Decisions` section is Order 04 (`c621h9`). Landing the format on its own keeps it
verifiable in isolation.

LAYOUT. One file per reviewed plan, FLAT under ``.aw/records/reviews/``::

    .aw/records/reviews/YYYYMMDD-<setid>-NN-<id6>-<slug>.review.md

``<id6>`` is the REVIEWED PLAN's id6, not a fresh one (OQ-01, resolved during authoring). That is
the stable cross-tree join key the repo already uses for ``From-Backlog``, ``From-Spec``, and
``Item-Dependencies``, and it keeps working across a plan rename. The tree is FLAT on purpose: a
review does NOT move when its plan moves ``pending/`` -> ``executed/``, so ``aw ipd finalize`` stays
a single-file transaction rather than acquiring a second path to keep in sync.

ROUNDS. Plans are demonstrably re-reviewed (the corpus carries far more ``/plan-review`` history
lines than distinct reviewed plans), so one file holds repeated ``## Round <N>`` sections and
:meth:`ReviewDocument.current_findings` returns only the LAST round's rows. A gate must act on
current findings, or a `HIGH` that round 1 raised and round 2 fixed would block forever.

PARSER CONTRACT. Pure, stdlib-only, Python 3.9 compatible, and NEVER raises on malformed input: it
returns typed rows plus a list of :class:`Diagnostic`, mirroring the parse-then-diagnose split in
``ipd_lint`` (which parses open questions into plain dicts and diagnoses them in a separate pass).
A gate that crashes on a bad table is a gate that gets disabled, so a malformed row becomes a
diagnostic and the surrounding good rows still parse.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from agent_workflows import artifact_naming as _naming

# --------------------------------------------------------------------------------------
# The closed vocabularies. Sourced from the plan-review workflow's own classification
# (`.aw/system/workflows/plan-review/plan-review.md`), lowercased for comparison.
# --------------------------------------------------------------------------------------

#: Finding severities, ORDERED least-to-most severe. The order IS the comparison used by
#: :func:`is_gating`, so it must stay ascending.
SEVERITIES: Tuple[str, ...] = ("low", "medium", "high", "blocker")

#: What the reviewer decided to DO about a finding.
DECISIONS: Tuple[str, ...] = ("fixed", "deferred", "open", "replan")

#: Severity rank for threshold comparison (higher = more severe).
_SEVERITY_RANK: Dict[str, int] = {s: i for i, s in enumerate(SEVERITIES)}

#: The artifact-type facet a review file carries (registered in the CLOSED naming enum by E-01).
REVIEW_FACET = "review"

#: The record class the reviews tree is registered under (E-09), so callers resolve the directory
#: through `record_producers` rather than hardcoding a second path string.
REVIEW_RECORD_CLASS = "reviews"

# The findings-table columns, in order. These are exactly the columns `/plan-review` already emits in
# its required final report, so a reviewer transcribes rather than re-classifies. `Evidence` is
# included because the shipped workflow table has it (plan-review.md:461); dropping it would lose the
# `path:line` citation that makes a finding checkable.
FINDING_COLUMNS: Tuple[str, ...] = (
    "ID",
    "Severity",
    "Scope",
    "Area",
    "Evidence",
    "Finding",
    "Remediation Risk",
    "Decision",
    "Resolution",
)

# The `## Decisions` columns (E-08): a reviewer's SELF-RESOLVED judgement calls, recorded beside the
# findings they came from. Order 04 (`c621h9`) owns making reviewers populate this.
DECISION_COLUMNS: Tuple[str, ...] = (
    "ID",
    "Question",
    "Chosen",
    "Alternatives considered",
    "Basis",
    "Reversible",
)

H_FINDINGS = "Findings"
H_DECISIONS = "Decisions"

# --------------------------------------------------------------------------------------
# Diagnostics (the "never raise" half of the contract).
# --------------------------------------------------------------------------------------

D_MALFORMED_ROW = "REV-P001"
D_UNKNOWN_SEVERITY = "REV-P002"
D_UNKNOWN_DECISION = "REV-P003"
D_MISSING_META = "REV-M101"
D_NO_ROUNDS = "REV-R001"
D_DUPLICATE_ROUND = "REV-R002"
D_UNREADABLE = "REV-P004"


class Diagnostic(NamedTuple):
    """A parse/consistency complaint, tied to a 1-based line when one is known (0 otherwise).

    Mirrors ``ipd_lint.Diagnostic`` so the two surfaces render identically.
    """

    line: int
    code: str
    message: str

    def render(self, path: str) -> str:
        return f"{path}:{self.line} {self.code} {self.message}"


class Finding(NamedTuple):
    """One typed findings row.

    ``severity`` and ``decision`` are NORMALIZED to lowercase members of :data:`SEVERITIES` /
    :data:`DECISIONS` when recognized, and preserved verbatim (lowercased) when not, so an unknown
    value is visible to a caller AND reported as a diagnostic rather than silently coerced.
    """

    id: str
    severity: str
    scope: str
    area: str
    evidence: str
    finding: str
    remediation_risk: str
    decision: str
    resolution: str
    line: int = 0

    @property
    def severity_known(self) -> bool:
        return self.severity in _SEVERITY_RANK

    @property
    def decision_known(self) -> bool:
        return self.decision in DECISIONS

    @property
    def is_resolved(self) -> bool:
        """True iff the reviewer considers this finding CLOSED (`fixed`).

        `deferred`, `open`, and `replan` are all UNRESOLVED: a deferral is a deliberate decision not
        to fix, which is exactly the state Order 02 must be able to gate on.
        """
        return self.decision == "fixed"


class Decision(NamedTuple):
    """One typed `## Decisions` row: a judgement call the reviewer made on its own authority."""

    id: str
    question: str
    chosen: str
    alternatives: str
    basis: str
    reversible: str
    line: int = 0


class Round(NamedTuple):
    """One review round: its number, its findings, and its self-resolved decisions."""

    number: int
    findings: Tuple[Finding, ...]
    decisions: Tuple[Decision, ...]
    line: int = 0


class ReviewDocument(NamedTuple):
    """A parsed `.review.md`: metadata, every round in file order, and any diagnostics."""

    plan_id: str
    reviewed_at: str
    reviewer: str
    verdict: str
    rounds: Tuple[Round, ...]
    diagnostics: Tuple[Diagnostic, ...]
    path: Optional[Path] = None

    def current_round(self) -> Optional[Round]:
        """The LAST round in the file, or None when the document has no rounds.

        "Last in file order" is the definition of current (not max-by-number), so a hand-inserted
        out-of-order round cannot silently become authoritative; a non-ascending number is reported
        as a diagnostic instead.
        """
        return self.rounds[-1] if self.rounds else None

    def current_findings(self) -> Tuple[Finding, ...]:
        """Only the CURRENT round's findings.

        This is the accessor a gate must use: a finding superseded by a later round is NOT current,
        so a `HIGH` raised in round 1 and fixed in round 2 does not block anything.
        """
        cur = self.current_round()
        return cur.findings if cur is not None else ()

    def current_decisions(self) -> Tuple[Decision, ...]:
        """Only the CURRENT round's self-resolved decisions."""
        cur = self.current_round()
        return cur.decisions if cur is not None else ()

    def unresolved_findings(self) -> Tuple[Finding, ...]:
        """Current findings the reviewer did NOT mark `fixed`."""
        return tuple(f for f in self.current_findings() if not f.is_resolved)


# --------------------------------------------------------------------------------------
# Naming.
# --------------------------------------------------------------------------------------


def build_review_name(
    *, date: str, set_id: str, order: int, plan_id6: str, slug: str
) -> str:
    """Build the clustered review filename for a plan.

    Delegates to the single naming authority (:func:`artifact_naming.build_clustered_name`) rather
    than formatting a name here, so a review name cannot drift from the grammar every other artifact
    obeys. ``plan_id6`` is the REVIEWED PLAN's id6 (the join key), not a fresh identifier.
    """
    return _naming.build_clustered_name(
        date=date,
        set_id=set_id,
        order=order,
        id6=plan_id6,
        slug=slug,
        artifact_type=REVIEW_FACET,
    )


def parse_review_name(name: str) -> Optional[Dict[str, str]]:
    """Parse a review filename into its grammar parts, or None when it is not a review name.

    Returns None for a name whose facet is absent or is some other type, so a caller cannot mistake
    a plan for a review. The CLOSED facet enum means a dotted SLUG (``foo.bar``) is not mis-read as
    a facet.
    """
    m = _naming.parse_clustered(name)
    if m is None:
        return None
    parts = m.groupdict()
    if parts.get("type") != REVIEW_FACET:
        return None
    return {
        "date": parts["date"],
        "set": parts["set"],
        "nn": parts["nn"],
        "id6": parts["id6"],
        "slug": parts["slug"],
    }


def reviews_dir(repo_root) -> Path:
    """The CANONICAL WRITE destination for a repo's reviews, via the ONE record-path authority (E-09).

    Use this when creating a review. For READING, use :func:`review_dirs`, which additionally covers
    a bare/unregistered repo (see the note there).
    """
    try:
        from agent_workflows import record_producers as _rp

        return _rp.resolve_record_path(REVIEW_RECORD_CLASS, target_repo=str(repo_root))
    except Exception:
        return Path(repo_root) / ".aw" / "records" / REVIEW_RECORD_CLASS


def review_dirs(repo_root) -> List[Path]:
    """Every EXISTING directory to read reviews from, most-authoritative first.

    This is the ONE definition of reviews discovery in the codebase; ``check_engine`` delegates here
    rather than re-deriving it, so the check and the writer cannot disagree about where reviews live.

    It resolves through ``record_producers.resolve_record_read_paths`` (registered by E-09) AND then
    adds the literal in-repo ``.aw/records/reviews``. That second entry is NOT a redundant hardcoded
    path: for a repo with no project context the resolver legitimately returns a HOME-COMPANION
    location (``~/.aw/projects/<repo>-<hash>/records/reviews``), so without it a bare or
    not-yet-installed repo would silently enumerate ZERO reviews and the E-06 check would be
    vacuous. ``check_engine._type_dirs`` carries the identical fallback for the identical documented
    reason ("so a bare/unregistered repo resolves").
    """
    out: List[Path] = []
    seen = set()

    def _add(p: Path) -> None:
        if not p.is_dir():
            return
        try:
            key = str(p.resolve())
        except OSError:
            return
        if key not in seen:
            seen.add(key)
            out.append(p)

    try:
        from agent_workflows import record_producers as _rp

        for p in _rp.resolve_record_read_paths(
            REVIEW_RECORD_CLASS, target_repo=str(repo_root)
        ):
            _add(Path(p))
    except Exception:
        pass
    _add(Path(repo_root) / ".aw" / "records" / REVIEW_RECORD_CLASS)
    return out


# --------------------------------------------------------------------------------------
# WRITE.
# --------------------------------------------------------------------------------------


def _row(cells: Sequence[str]) -> str:
    # A cell containing a raw `|` would silently split into two columns, so escape it.
    safe = [str(c).replace("|", "\\|").replace("\n", " ").strip() for c in cells]
    return "| " + " | ".join(safe) + " |"


def _table(columns: Sequence[str], rows: Sequence[Sequence[str]]) -> List[str]:
    out = [_row(columns), _row(["-" * max(3, len(c)) for c in columns])]
    out.extend(_row(r) for r in rows)
    return out


def render_review(
    *,
    plan_id: str,
    reviewed_at: str,
    reviewer: str,
    verdict: str,
    rounds: Sequence[Round],
) -> str:
    """Render a complete `.review.md` body. Pure: builds a string, touches no disk."""
    lines: List[str] = [
        f"# Plan review findings: {plan_id}",
        "",
        f"- Plan-Id: {plan_id}",
        f"- Reviewed-At: {reviewed_at}",
        f"- Reviewer: {reviewer}",
        f"- Verdict: {verdict}",
        "",
    ]
    for rnd in rounds:
        lines.append(f"## Round {rnd.number}")
        lines.append("")
        lines.append(f"### {H_FINDINGS}")
        lines.append("")
        lines.extend(
            _table(
                FINDING_COLUMNS,
                [
                    (
                        f.id,
                        f.severity,
                        f.scope,
                        f.area,
                        f.evidence,
                        f.finding,
                        f.remediation_risk,
                        f.decision,
                        f.resolution,
                    )
                    for f in rnd.findings
                ],
            )
        )
        lines.append("")
        # The Decisions section is OPTIONAL (E-08): a review with no autonomous decisions is valid,
        # so an empty section is omitted rather than written as a header with an empty table.
        if rnd.decisions:
            lines.append(f"### {H_DECISIONS}")
            lines.append("")
            lines.extend(
                _table(
                    DECISION_COLUMNS,
                    [
                        (
                            d.id,
                            d.question,
                            d.chosen,
                            d.alternatives,
                            d.basis,
                            d.reversible,
                        )
                        for d in rnd.decisions
                    ],
                )
            )
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def write_review(path, **kwargs) -> Path:
    """Render and write a `.review.md`, creating the parent tree. Returns the written path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_review(**kwargs), encoding="utf-8")
    return p


# --------------------------------------------------------------------------------------
# PARSE.
# --------------------------------------------------------------------------------------

_META_RE = re.compile(r"^-\s*([A-Za-z][A-Za-z-]*):\s*(.*?)\s*$")
_ROUND_RE = re.compile(r"^##\s+Round\s+(\d+)\s*$", re.IGNORECASE)
_H3_RE = re.compile(r"^###\s+(.+?)\s*$")
_H2_RE = re.compile(r"^##\s+(.+?)\s*$")
_SEPARATOR_CELL_RE = re.compile(r"^:?-{3,}:?$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _split_row(line: str) -> List[str]:
    """Split a markdown table row into cells, honoring `\\|` escapes."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells: List[str] = []
    buf: List[str] = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            buf.append("|")
            i += 2
            continue
        if ch == "|":
            cells.append("".join(buf).strip())
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    return cells


def _is_separator(cells: Sequence[str]) -> bool:
    return bool(cells) and all(_SEPARATOR_CELL_RE.match(c or "") for c in cells)


def _is_header(cells: Sequence[str], columns: Sequence[str]) -> bool:
    if not cells:
        return False
    return cells[0].strip().lower() == columns[0].strip().lower()


def parse_review_text(text: str, path: Optional[Path] = None) -> ReviewDocument:
    """Parse a `.review.md` body into a :class:`ReviewDocument`.

    NEVER raises on malformed content. A row with the wrong cell count, an unrecognized severity, or
    an unrecognized decision produces a :class:`Diagnostic` while every well-formed row around it is
    still returned, so one bad row cannot blind a gate to the rest of the table.
    """
    diagnostics: List[Diagnostic] = []
    meta: Dict[str, str] = {}
    rounds: List[Round] = []

    cur_num: Optional[int] = None
    cur_line = 0
    cur_section = ""
    cur_findings: List[Finding] = []
    cur_decisions: List[Decision] = []
    seen_numbers: Dict[int, int] = {}
    in_fence = False

    def _flush() -> None:
        if cur_num is None:
            return
        rounds.append(
            Round(
                number=cur_num,
                findings=tuple(cur_findings),
                decisions=tuple(cur_decisions),
                line=cur_line,
            )
        )

    lines = text.splitlines()
    for idx, raw in enumerate(lines, start=1):
        if _FENCE_RE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        mr = _ROUND_RE.match(raw)
        if mr:
            _flush()
            cur_findings = []
            cur_decisions = []
            cur_section = ""
            cur_num = int(mr.group(1))
            cur_line = idx
            if cur_num in seen_numbers:
                diagnostics.append(
                    Diagnostic(
                        idx,
                        D_DUPLICATE_ROUND,
                        f"round {cur_num} appears more than once "
                        f"(first at line {seen_numbers[cur_num]}); "
                        "round numbers must be unique and ascending",
                    )
                )
            seen_numbers[cur_num] = idx
            continue

        mh3 = _H3_RE.match(raw)
        if mh3:
            cur_section = mh3.group(1).strip().lower()
            continue

        mh2 = _H2_RE.match(raw)
        if mh2:
            # Some other `##` section (not a Round): leaves any round context alone but ends the
            # current table context so a stray table below is not attributed to Findings.
            cur_section = ""
            continue

        if cur_num is None:
            mm = _META_RE.match(raw)
            if mm:
                meta[mm.group(1).strip().lower()] = mm.group(2).strip()
            continue

        if not raw.strip().startswith("|"):
            continue

        cells = _split_row(raw)
        if _is_separator(cells):
            continue

        if cur_section.startswith(H_FINDINGS.lower()):
            if _is_header(cells, FINDING_COLUMNS):
                continue
            if len(cells) != len(FINDING_COLUMNS):
                diagnostics.append(
                    Diagnostic(
                        idx,
                        D_MALFORMED_ROW,
                        f"findings row has {len(cells)} cells, expected "
                        f"{len(FINDING_COLUMNS)} ({', '.join(FINDING_COLUMNS)})",
                    )
                )
                continue
            sev = cells[1].strip().lower()
            dec = cells[7].strip().lower()
            fid = cells[0].strip()
            if sev not in _SEVERITY_RANK:
                diagnostics.append(
                    Diagnostic(
                        idx,
                        D_UNKNOWN_SEVERITY,
                        f"{fid or 'row'}: severity {cells[1].strip()!r} is not one of "
                        f"{'|'.join(SEVERITIES)}",
                    )
                )
            if dec not in DECISIONS:
                diagnostics.append(
                    Diagnostic(
                        idx,
                        D_UNKNOWN_DECISION,
                        f"{fid or 'row'}: decision {cells[7].strip()!r} is not one of "
                        f"{'|'.join(DECISIONS)}",
                    )
                )
            cur_findings.append(
                Finding(
                    id=fid,
                    severity=sev,
                    scope=cells[2],
                    area=cells[3],
                    evidence=cells[4],
                    finding=cells[5],
                    remediation_risk=cells[6],
                    decision=dec,
                    resolution=cells[8],
                    line=idx,
                )
            )
            continue

        if cur_section.startswith(H_DECISIONS.lower()):
            if _is_header(cells, DECISION_COLUMNS):
                continue
            if len(cells) != len(DECISION_COLUMNS):
                diagnostics.append(
                    Diagnostic(
                        idx,
                        D_MALFORMED_ROW,
                        f"decisions row has {len(cells)} cells, expected "
                        f"{len(DECISION_COLUMNS)} ({', '.join(DECISION_COLUMNS)})",
                    )
                )
                continue
            cur_decisions.append(
                Decision(
                    id=cells[0],
                    question=cells[1],
                    chosen=cells[2],
                    alternatives=cells[3],
                    basis=cells[4],
                    reversible=cells[5],
                    line=idx,
                )
            )
            continue

    _flush()

    for field in ("plan-id", "reviewed-at", "reviewer", "verdict"):
        if not meta.get(field):
            diagnostics.append(
                Diagnostic(0, D_MISSING_META, f"missing required `- {field}:` metadata")
            )
    if not rounds:
        diagnostics.append(
            Diagnostic(0, D_NO_ROUNDS, "no `## Round <N>` section found")
        )

    return ReviewDocument(
        plan_id=meta.get("plan-id", ""),
        reviewed_at=meta.get("reviewed-at", ""),
        reviewer=meta.get("reviewer", ""),
        verdict=meta.get("verdict", ""),
        rounds=tuple(rounds),
        diagnostics=tuple(diagnostics),
        path=path,
    )


def parse_review_file(path) -> ReviewDocument:
    """Read and parse a `.review.md`. An unreadable file yields a diagnostic, never an exception."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        return ReviewDocument(
            plan_id="",
            reviewed_at="",
            reviewer="",
            verdict="",
            rounds=(),
            diagnostics=(Diagnostic(0, D_UNREADABLE, f"cannot read: {exc}"),),
            path=p,
        )
    return parse_review_text(text, path=p)


def iter_review_files(repo_root):
    """Yield every `*.review.md` under the repo's reviews tree(s), sorted, de-duplicated.

    Discovery goes through :func:`review_dirs` (the record-path authority plus the documented
    bare-repo fallback), which is why E-06's check needs no path literal of its own.
    """
    seen = set()
    for base in review_dirs(repo_root):
        for p in sorted(base.rglob("*.review.md")):
            if p.name in ("README.md", "INDEX.md", "STATUS.md"):
                continue
            try:
                key = str(p.resolve())
            except OSError:
                continue
            if key in seen:
                continue
            seen.add(key)
            yield p


# --------------------------------------------------------------------------------------
# The shared gating comparison. Defined ONCE here so Order 02 and Order 03 cannot diverge.
# --------------------------------------------------------------------------------------


def is_gating(severity: str, threshold: str) -> bool:
    """True iff a finding of ``severity`` is at or above ``threshold`` and therefore gates.

    ``threshold`` of ``off`` disables gating entirely and always returns False. An unrecognized
    severity or threshold returns False (fail-open on GARBAGE only, never on a valid lower-severity
    finding), because a typo must not silently manufacture a block; the parser separately reports the
    unknown value as a diagnostic, so the bad data is still visible.
    """
    sev = (severity or "").strip().lower()
    thr = (threshold or "").strip().lower()
    if thr in ("off", ""):
        return False
    if sev not in _SEVERITY_RANK or thr not in _SEVERITY_RANK:
        return False
    return _SEVERITY_RANK[sev] >= _SEVERITY_RANK[thr]


# --------------------------------------------------------------------------------------
# The shared "does this plan's review block its dependents?" predicate (Order 03 / 7nkcgp).
#
# WHY IT LIVES HERE AND NOT IN A RUNNER. Order 03 must apply one identical rule on FOUR
# authority surfaces: `oc_runipd.dependency_status`, `agy_runipd.dependency_status`,
# `check_engine.evaluate_ipd_dependencies`, and `ipd_set_plan`'s Set compiler. Verified at
# execution time: NEITHER runner imports the other and neither imports any shared runner
# library, which is the exact duplication the in-flight `rununify` Set (orchestrator
# `5e4sb6`) exists to fix. Importing one runner from the other would create the first such
# coupling and collide with that extraction, so the predicate lands in THIS module, which
# already owns findings parsing and is already imported by `check_engine`.
#
# SCOPE LIMIT, stated plainly because it is easy to overread: this blocks on a RECORDED
# unresolved gating finding. A reviewer who records nothing is outside deterministic reach
# (the deliberate `absent -> silent` design of Order 02's E-07(a)), so the honest claim is
# "recorded unresolved gating findings now block dependents", NOT "unsound work cannot
# release dependents".
# --------------------------------------------------------------------------------------


class GatingBlock(NamedTuple):
    """Why a plan's review blocks its dependents: enough to name the ROOT CAUSE to an operator.

    ``kind`` is ``"finding"`` (a real unresolved gating row) or ``"malformed"`` (a review artifact
    that exists but cannot be parsed, so its findings cannot be checked). ``finding_id`` and
    ``severity`` are the empty string for the malformed case, where no row could be read.
    """

    plan_id6: str
    finding_id: str
    severity: str
    decision: str
    kind: str
    review_path: str
    detail: str

    def describe(self) -> str:
        """One operator-facing clause naming the blocking cause (never a bare 'not satisfied')."""
        if self.kind == "malformed":
            return "{0}: review artifact is malformed ({1})".format(
                self.plan_id6, self.detail
            )
        return "{0}: review finding {1} is {2}/{3} and unresolved".format(
            self.plan_id6, self.finding_id, self.severity, self.decision
        )


def plan_gating_blocks(
    repo_root, plan_id6: str, threshold: Optional[str] = None
) -> Tuple[GatingBlock, ...]:
    """Every recorded reason ``plan_id6``'s review blocks its dependents, in deterministic order.

    An EMPTY tuple means "nothing recorded blocks dependents", which is the answer for a plan with
    no review artifact at all. The three failure modes deliberately MIRROR Order 02's
    ``check_engine.evaluate_review_finding_escalation`` so the cascade and the escalation gate cannot
    disagree about what counts as blocking:

    (a) NO review artifact -> EMPTY (silent). Required for safety, not laziness: zero ``.review.md``
        files exist against 428 plans, so a fail-closed absent case would block the entire corpus.
    (b) Artifact PRESENT but malformed -> BLOCKING. A file that exists but cannot be trusted is an
        error, not an absence; treating it as an absence is the evasion path (a ``HGIH`` typo would
        otherwise slip past :func:`is_gating` silently).
    (c) Threshold ``off`` -> EMPTY, the gate is disabled entirely.

    Current-round semantics come from :meth:`ReviewDocument.current_findings`, so a finding raised in
    round 1 and fixed in round 2 never blocks. Only decisions OTHER than ``fixed`` block, matching
    :attr:`Finding.is_resolved`.

    Never raises: an unreadable tree or a missing config yields an empty tuple, because a crashing
    gate is a disabled gate.
    """
    root = Path(repo_root)
    if threshold is None:
        try:
            from agent_workflows import config as _cfg

            threshold = _cfg.findings_gate_threshold(root)
        except Exception:
            return ()
    thr = str(threshold).strip().lower()
    if thr in ("off", ""):
        return ()  # (c) disabled outright: do no work at all.

    wanted = (plan_id6 or "").strip()
    if not wanted:
        return ()

    out: List[GatingBlock] = []
    try:
        review_paths = sorted(iter_review_files(root), key=lambda p: str(p))
    except Exception:
        return ()
    for path in review_paths:
        doc = parse_review_file(path)
        if (doc.plan_id or "").strip() != wanted:
            continue
        if doc.diagnostics:
            # (b) present but unparseable -> block, and say which codes so the operator can repair it.
            codes = ", ".join(sorted({d.code for d in doc.diagnostics}))
            out.append(
                GatingBlock(
                    plan_id6=wanted,
                    finding_id="",
                    severity="",
                    decision="",
                    kind="malformed",
                    review_path=str(path),
                    detail=codes,
                )
            )
            continue
        for finding in doc.current_findings():
            if finding.is_resolved:
                continue
            if not is_gating(finding.severity, thr):
                continue
            out.append(
                GatingBlock(
                    plan_id6=wanted,
                    finding_id=finding.id,
                    severity=finding.severity,
                    decision=finding.decision,
                    kind="finding",
                    review_path=str(path),
                    detail="",
                )
            )
    return tuple(out)


def plan_blocks_dependents(
    repo_root, plan_id6: str, threshold: Optional[str] = None
) -> bool:
    """True iff ``plan_id6`` carries a recorded reason NOT to satisfy an ``executed:`` edge.

    The boolean convenience over :func:`plan_gating_blocks` for a caller that needs only the verdict.
    A caller that must TELL THE OPERATOR WHY should use :func:`plan_gating_blocks` instead; a block
    whose message does not name its cause is the failure mode this Set exists to remove.
    """
    return bool(plan_gating_blocks(repo_root, plan_id6, threshold))
